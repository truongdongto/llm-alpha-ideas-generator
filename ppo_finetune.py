"""
ppo_finetune.py
================
RL fine-tuning of the Qwen policy using PPO (via the `trl` library), so
the model learns -- through actual gradient updates, not just in-context
prompting -- to propose alpha expressions that score well on the
backtest engine's reward.

*** NOT EXECUTABLE IN THIS SANDBOX ***
Same constraint as llm_gen/qwen_generator.py: no huggingface.co access
and no GPU here. This file is syntax-checked (py_compile) only. Run it
on your own machine with:
    pip install torch transformers trl peft accelerate
    # a CUDA GPU with >=16GB VRAM is realistic for a 7B model with PEFT/LoRA;
    # for less VRAM, use Qwen2.5-1.5B-Instruct or Qwen2.5-3B-Instruct instead.

DESIGN NOTES (why this looks the way it does):

1. One idea per completion, not a JSON batch.
   The in-context loop (orchestrate.py) asks for N ideas per LLM call
   because that's efficient for API-based/inference-only usage. PPO
   needs one scalar reward per (query, response) pair, so here each
   training example asks for exactly ONE alpha expression -- this
   removes any ambiguity about which part of a multi-idea completion a
   given reward should attribute to.

2. Reward = the SAME compute_reward() used everywhere else.
   The whole point of building llm_gen/reward.py as a standalone,
   pure function was so the metric used to rank alphas on the
   leaderboard is EXACTLY the metric the policy gets optimized against.
   If these two diverged, PPO could learn to game a proxy reward that
   doesn't match what you actually screen alphas by.

3. No diversity penalty during PPO (diversity_max_corr is fixed at 0
   here), unlike orchestrate.py's in-context loop. Diversity-vs-pool is
   a moving target across a training run (the "pool" would have to be
   the policy's own recent outputs, updated online) -- a reasonable
   extension, but left out here to keep the core PPO loop legible. See
   the TODO in `compute_ppo_reward` for how you'd wire it in.

4. LoRA/PEFT is recommended but not hardwired in -- see `use_lora` flag.
   Full fine-tuning of a 7B model's value head + policy is expensive;
   LoRA cuts trainable parameters dramatically with little quality loss
   for this kind of narrow, structured-output task.
"""

from __future__ import annotations
import torch
from transformers import AutoTokenizer
from trl import PPOConfig, PPOTrainer, AutoModelForCausalLMWithValueHead

from dsl.evaluator import evaluate_expression, AlphaEvaluationError
from dsl.parser import AlphaExpressionSyntaxError
from backtest.engine import backtest_alpha
from llm_gen.base import parse_single_llm_output
from llm_gen.prompt_builder import build_system_prompt
from llm_gen.reward import compute_reward, DEFAULT_WEIGHTS
from data_layer import generate_synthetic_data  # swap for fetch_real_data(...) for real training


SINGLE_IDEA_USER_PROMPT = (
    "Generate exactly 1 new alpha expression. Respond with a single JSON object only, "
    'in this exact shape: {"expression": "...", "rationale": "..."}'
)


def compute_ppo_reward(expression: str | None, panel: dict) -> float:
    """
    Same logic as orchestrate.py's _evaluate_one_idea, collapsed to a
    single scalar for PPO. Returns compute_reward()'s invalid_penalty
    for anything that fails to parse or evaluate -- including a
    completely unparseable completion (expression=None).

    TODO (extension): thread in a running `accepted_pool` here (e.g. a
    module-level dict updated every N steps with the best expressions
    seen so far) and pass a real diversity_max_corr, exactly like
    orchestrate.AlphaResearchLoop._diversity_max_corr does, if you want
    PPO to also learn to avoid redundant alphas rather than just strong
    ones.
    """
    if not expression:
        return compute_reward(None, None, 0.0, valid=False)

    try:
        signal = evaluate_expression(expression, panel)
    except (AlphaExpressionSyntaxError, AlphaEvaluationError):
        return compute_reward(None, None, 0.0, valid=False)
    except Exception:
        return compute_reward(None, None, 0.0, valid=False)

    result = backtest_alpha(signal, panel["close"], horizons=(1,), n_quantiles=5)
    mean_ic = result["primary_horizon_ic"]["mean_ic"]
    return compute_reward(
        mean_ic=mean_ic, turnover=result["turnover"],
        diversity_max_corr=0.0,  # see TODO above
        valid=True, weights=DEFAULT_WEIGHTS,
    )


def main(
    model_name: str = "Qwen/Qwen2.5-7B-Instruct",
    n_steps: int = 200,
    batch_size: int = 8,
    learning_rate: float = 1.4e-5,
    use_lora: bool = True,
    output_dir: str = "./qwen-alpha-ppo-checkpoint",
):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    peft_config = None
    if use_lora:
        from peft import LoraConfig
        peft_config = LoraConfig(
            r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
            task_type="CAUSAL_LM",
        )

    # AutoModelForCausalLMWithValueHead wraps the base causal LM with an
    # extra scalar "value head" PPO needs to estimate expected future reward
    policy_model = AutoModelForCausalLMWithValueHead.from_pretrained(
        model_name, peft_config=peft_config, torch_dtype=torch.bfloat16,
    ).to(device)

    ppo_config = PPOConfig(
        model_name=model_name,
        learning_rate=learning_rate,
        batch_size=batch_size,
        mini_batch_size=max(1, batch_size // 2),
    )
    ppo_trainer = PPOTrainer(ppo_config, policy_model, ref_model=None, tokenizer=tokenizer)

    # NOTE: swap generate_synthetic_data(...) for fetch_real_data(tickers, ...)
    # to train against real market data instead of synthetic random walks.
    panel = generate_synthetic_data([f"T{i:02d}" for i in range(30)], n_days=400)

    system_prompt = build_system_prompt()
    chat_prompt = tokenizer.apply_chat_template(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": SINGLE_IDEA_USER_PROMPT},
        ],
        tokenize=False, add_generation_prompt=True,
    )
    query_tensor = tokenizer(chat_prompt, return_tensors="pt").input_ids[0].to(device)

    generation_kwargs = {
        "min_length": -1,
        "top_p": 0.9,
        "temperature": 0.9,      # relatively high: PPO needs sampling diversity
        "do_sample": True,
        "pad_token_id": tokenizer.eos_token_id,
        "max_new_tokens": 200,   # a single expression is short; no need for 1024 tokens
    }

    for step in range(n_steps):
        # every training example in this simple loop reuses the same
        # static prompt -- diversity comes from sampling temperature, not
        # from varying the prompt. A fancier version could rotate through
        # several prompt variants (different economic-rationale hints) per batch.
        query_tensors = [query_tensor for _ in range(batch_size)]

        response_tensors = ppo_trainer.generate(
            query_tensors, return_prompt=False, **generation_kwargs,
        )
        completions = [tokenizer.decode(r, skip_special_tokens=True) for r in response_tensors]

        rewards = []
        for completion in completions:
            idea = parse_single_llm_output(completion)
            expr = idea.expression if idea else None
            r = compute_ppo_reward(expr, panel)
            rewards.append(torch.tensor(r, dtype=torch.float32))

        stats = ppo_trainer.step(query_tensors, response_tensors, rewards)

        mean_reward = torch.stack(rewards).mean().item()
        print(f"[step {step+1}/{n_steps}] mean_reward={mean_reward:.3f}  "
              f"kl={stats.get('objective/kl', float('nan')):.4f}")

        if (step + 1) % 50 == 0:
            ppo_trainer.save_pretrained(f"{output_dir}/step_{step+1}")

    ppo_trainer.save_pretrained(output_dir)
    print(f"Training complete. Final checkpoint saved to {output_dir}")


if __name__ == "__main__":
    main()