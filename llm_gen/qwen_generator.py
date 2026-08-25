"""
llm_gen/qwen_generator.py
============================
Real AlphaIdeaGenerator backed by a local Qwen2.5-Instruct model via HF transformers.

Model choice: Qwen2.5-7B-Instruct (or Qwen2.5-Coder-7B-Instruct, which
tends to follow strict output-format instructions like "JSON array only"
more reliably since it's code/structure-trained) is a reasonable default
-- swap `model_name` for a smaller Qwen2.5-1.5B/3B-Instruct variant if
you don't have a GPU with enough VRAM for the 7B model.
"""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from llm_gen.base import AlphaIdeaGenerator, AlphaIdea, parse_llm_output
from llm_gen.prompt_builder import build_system_prompt


class QwenAlphaGenerator(AlphaIdeaGenerator):
    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-Coder-3B-Instruct",
        max_new_tokens: int = 2048,
        temperature: float = 0.8,
        top_p: float = 0.9,
        dtype: torch.dtype = torch.bfloat16,
    ):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, dtype=dtype, device_map=self.device,
        )
        self.model.eval()

        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.system_prompt = build_system_prompt()

    def _build_chat_messages(self, n: int, feedback_context: str) -> list[dict]:
        from llm_gen.prompt_builder import build_user_prompt
        return [
            {"role": "system", "content": self.system_prompt},
            # feedback_context here is actually the leaderboard-derived
            # user prompt built by orchestrate.py's caller -- see
            # generate() below for how this gets threaded through.
            {"role": "user", "content": feedback_context},
        ]

    @torch.no_grad()
    def generate(self, n: int, feedback_context: str) -> list[AlphaIdea]:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": feedback_context},
        ]
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
        )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        output_ids = self.model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            do_sample=True,
            temperature=self.temperature,
            top_p=self.top_p,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        # slice off the prompt tokens, keep only the newly generated completion
        completion_ids = output_ids[0][inputs["input_ids"].shape[1]:]
        raw_text = self.tokenizer.decode(completion_ids, skip_special_tokens=True)

        ideas = parse_llm_output(raw_text)
        if not ideas:
            # empty/malformed batch is a normal (if undesirable) outcome --
            # the orchestration loop's leaderboard + feedback mechanism is
            # exactly what should teach the model to stop doing this, not
            # an exception here.
            print(f"[AlphaGenerator] WARNING: could not parse any ideas from output:\n{raw_text[:300]}")
        return ideas[:n]


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from data_layer import generate_synthetic_data
    from orchestrate import AlphaResearchLoop

    panel = generate_synthetic_data([f"T{i:02d}" for i in range(20)], n_days=300)
    generator = QwenAlphaGenerator(model_name="Qwen/Qwen2.5-Coder-3B-Instruct")
    loop = AlphaResearchLoop(generator=generator, panel=panel, n_rounds=5, ideas_per_round=8)
    leaderboard = loop.run()
    print(leaderboard.head(10))