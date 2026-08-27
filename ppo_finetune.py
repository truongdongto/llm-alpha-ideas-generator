"""
ppo_finetune.py
================
PPO fine-tuning stage, using the backtest engine as the reward signal so the model 
learns to prefer alphas with real predictive power, not just syntactically valid ones.
"""

from __future__ import annotations
from pathlib import Path
import inspect
import os
import sys
sys.path.append(str(Path(__file__).parent.parent))

# Must be set before importing torch to take effect.
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import random
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from trl import PPOConfig, PPOTrainer, AutoModelForCausalLMWithValueHead


from dsl.evaluator import evaluate_expression, AlphaEvaluationError
from dsl.parser import AlphaExpressionSyntaxError
from backtest.engine import backtest_alpha, alpha_correlation
from llm_gen.base import parse_llm_output
from llm_gen.prompt_builder import build_system_prompt
from llm_gen.reward import compute_reward, DEFAULT_WEIGHTS
from data_layer import fetch_real_data
from dsl.worldquant_alphas import THEMES


# ---------------------------------------------------------------------------
# Data: train / validation split by time (walk-forward). Reward during
# training only ever sees train_panel; val_panel is used solely to monitor
# for overfitting, never to compute gradients.
# ---------------------------------------------------------------------------

def split_panel_by_time(panel: dict, train_frac: float = 0.7) -> tuple[dict, dict]:
    n = len(panel["close"].index)
    cutoff = int(n * train_frac)
    train_panel = {k: v.iloc[:cutoff] for k, v in panel.items()}
    val_panel = {k: v.iloc[cutoff:] for k, v in panel.items()}
    return train_panel, val_panel


# ---------------------------------------------------------------------------
# Prompt sampling -- reuses the SAME templates/themes as the SFT dataset
# builder, so PPO's prompt distribution matches what the model was already
# taught to respond to, rather than introducing a new unseen format.
# ---------------------------------------------------------------------------

def sample_prompt(rng: random.Random) -> str:
    user_template = [
        """generate {n} alpha expression relating to {theme} concept""",
        """create {n} alpha formula associated with {theme}""",
        """generate {n} alpha idea linked with {theme}""",
    ]
    template = rng.choice(user_template)
    theme = rng.choice(THEMES)
    return template.format(n=1, theme=theme)


def build_chat_prompt(tokenizer, user_message: str) -> str:
    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": user_message},
    ]
    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


# ---------------------------------------------------------------------------
# Reward: parse -> evaluate -> backtest -> diversity-aware compute_reward.
# Same compute_reward() used by orchestrate.py's in-context loop, so PPO
# optimizes exactly the metric alphas get screened by everywhere else.
# ---------------------------------------------------------------------------

POOL_ACCEPT_REWARD = 0.3
POOL_MAX_SIZE = 30


def compute_ppo_reward(completion: str, panel: dict, accepted_pool: dict) -> tuple[float, str | None, float | None]:
    """Returns (reward, expression | None, mean_ic | None)."""
    ideas = parse_llm_output(completion)
    if not ideas:
        return compute_reward(None, None, 0.0, valid=False), None, None
    expression = ideas[0].expression  # asked for n=1; ignore any extras if the model over-produces

    try:
        signal = evaluate_expression(expression, panel)
    except (AlphaExpressionSyntaxError, AlphaEvaluationError):
        return compute_reward(None, None, 0.0, valid=False), expression, None
    except Exception:  # noqa: BLE001 -- never let one bad completion crash training
        return compute_reward(None, None, 0.0, valid=False), expression, None

    result = backtest_alpha(signal, panel["close"], horizons=(1,), n_quantiles=5)
    mean_ic = result["primary_horizon_ic"]["mean_ic"]

    diversity = 0.0
    if accepted_pool:
        diversity = max(abs(alpha_correlation(signal, other)) for other in accepted_pool.values())

    reward = compute_reward(
        mean_ic=mean_ic, turnover=result["turnover"],
        diversity_max_corr=diversity, valid=True, weights=DEFAULT_WEIGHTS,
    )

    if reward >= POOL_ACCEPT_REWARD:
        accepted_pool[expression] = signal
        if len(accepted_pool) > POOL_MAX_SIZE:
            accepted_pool.pop(next(iter(accepted_pool)))  # drop oldest; cheap bound, not reward-ranked

    return reward, expression, mean_ic


def check_validation_ic(accepted_pool: dict, val_panel: dict) -> float | None:
    """Re-backtest the pool's expressions on the held-out window; returns
    the best validation |mean_ic| found, or None if the pool is empty."""
    if not accepted_pool:
        return None
    best = None
    for expr in list(accepted_pool):
        try:
            signal = evaluate_expression(expr, val_panel)
            result = backtest_alpha(signal, val_panel["close"], horizons=(1,), n_quantiles=5)
            ic = abs(result["primary_horizon_ic"]["mean_ic"])
            if best is None or ic > best:
                best = ic
        except (AlphaExpressionSyntaxError, AlphaEvaluationError, Exception):
            continue
    return best


# ---------------------------------------------------------------------------
# Main training loop
# ---------------------------------------------------------------------------

def main(
    model_name: str = "Qwen/Qwen3-4B-Instruct-2507",
    lora_path: str = "/kaggle/input/models/truongdongto/sft-checkpoint/transformers/default/1/sft-checkpoint",
    n_steps: int = 300,
    batch_size: int = 1,
    mini_batch_size: int = 1,
    gradient_accumulation_steps: int = 1,
    learning_rate: float = 1.0e-5,
    val_check_every: int = 25,
    checkpoint_every: int = 50,
    output_dir: str = "./ppo-checkpoint",
    seed: int = 0,
):
    print("Loading model for PPO training ...\n")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    rng = random.Random(seed)

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    base_model = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.bfloat16, device_map=device)
    model = PeftModel.from_pretrained(base_model, lora_path, is_trainable=True)

    policy_model = AutoModelForCausalLMWithValueHead.from_pretrained(model, dtype=torch.bfloat16, device_map=device)
    pretrained = getattr(policy_model, "pretrained_model", policy_model)
    if hasattr(pretrained, "gradient_checkpointing_enable"):
        pretrained.gradient_checkpointing_enable()
    if hasattr(pretrained, "enable_input_require_grads"):
        pretrained.enable_input_require_grads()
    pretrained.config.use_cache = False
    print(f"Loaded policy model.\n")

    ppo_kwargs = dict(
        learning_rate=learning_rate,
        batch_size=batch_size,
        mini_batch_size=mini_batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        ppo_epochs=2,
        optimize_device_cache=True,
        gradient_checkpointing=True,
    )
    ppo_params = inspect.signature(PPOConfig.__init__).parameters
    ppo_config = PPOConfig(**{k: v for k, v in ppo_kwargs.items() if k in ppo_params})
    ppo_trainer = PPOTrainer(
        config=ppo_config,
        model=policy_model,
        ref_model=None,
        tokenizer=tokenizer,
    )

    full_panel = fetch_real_data(tickers=["NFLX", "MS", "DELL", "ARM", "SHEL", "IBM"], end="2025-12-12")
    train_panel, val_panel = split_panel_by_time(full_panel, train_frac=0.7)
    print("Fetched and splitted data successfully.\n")

    accepted_pool: dict = {}

    generation_kwargs = {
        "min_length": -1,
        "top_p": 0.9,
        "temperature": 0.9,
        "do_sample": True,
        "pad_token_id": tokenizer.eos_token_id,
        "max_new_tokens": 64,
    }

    print("PPO training ...\n")
    for step in range(n_steps):
        user_messages = [sample_prompt(rng) for _ in range(batch_size)]
        chat_prompts = [build_chat_prompt(tokenizer, m) for m in user_messages]
        query_tensors = [tokenizer(p, return_tensors="pt").input_ids[0].to(device) for p in chat_prompts]

        response_tensors = ppo_trainer.generate(query_tensors, return_prompt=False, **generation_kwargs)
        completions = [tokenizer.decode(r, skip_special_tokens=True) for r in response_tensors]

        rewards, expressions, n_valid = [], [], 0
        for completion in completions:
            r, expr, mean_ic = compute_ppo_reward(completion, train_panel, accepted_pool)
            rewards.append(torch.tensor(r, dtype=torch.bfloat16))
            expressions.append(expr)
            if mean_ic is not None:
                n_valid += 1

        stats = ppo_trainer.step(query_tensors, response_tensors, rewards)

        mean_reward = torch.stack(rewards).mean().item()
        valid_rate = n_valid / batch_size
        print(f"[step {step+1}/{n_steps}] mean_reward={mean_reward:.3f}  valid_rate={valid_rate:.2f}  "
              f"pool_size={len(accepted_pool)}  kl={stats.get('objective/kl', float('nan')):.4f}")

        if (step + 1) % val_check_every == 0:
            val_ic = check_validation_ic(accepted_pool, val_panel)
            if val_ic is not None:
                print(f"  [validation] best pool |mean_ic| on held-out window: {val_ic:.4f} "
                      f"(compare against training reward trend -- a growing gap signals overfitting)")

        if (step + 1) % checkpoint_every == 0:
            ppo_trainer.save_pretrained(f"{output_dir}/step_{step+1}")

    ppo_trainer.save_pretrained(output_dir)
    print(f"\nTraining complete. Final checkpoint saved to {output_dir}")
    print(f"Final accepted pool: {len(accepted_pool)} expressions")


if __name__ == "__main__":
    main()