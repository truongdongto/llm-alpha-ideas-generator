import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
import random

from dsl.worldquant_alphas import WORLDQUANT_INSPIRED_ALPHAS
from llm_gen.prompt_builder import build_system_prompt, build_user_prompt


def _format_assistant_json(batch: list[dict]) -> str:
    return json.dumps(
        [{"expression": a["expression"], "rationale": a["rationales"][random.randint(0, 2)]} for a in batch],
        ensure_ascii=False,
    )

def build_sft_examples(seed: int = 0, min_batch: int = 1, max_batch: int = 3) -> list[dict]:
    rng = random.Random(seed)
    pool = WORLDQUANT_INSPIRED_ALPHAS.copy()
    rng.shuffle(pool)

    examples = []
    i = 0
    while i < len(pool):
        batch_size = rng.randint(min_batch, max_batch)
        batch = pool[i:i + batch_size]
        i += batch_size
        if not batch:
            break

        examples.append({
            "messages": [
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": build_user_prompt(rng.randint(3, 6))},
                {"role": "assistant", "content": _format_assistant_json(batch)},
            ]
        })
    return examples

def build_and_split_dataset(seed: int = 42, val_fraction: float = 0.15):
    """Build and split dataset for sft training."""
    examples = build_sft_examples(seed=seed)
    n_val = max(1, int(len(examples) * val_fraction))
    return examples[n_val:], examples[:n_val]  # train, val

if __name__ == "__main__":
    examples = build_sft_examples()
    ex = examples[0]['messages'][2]['content']
    print(ex)
    print(len(ex.split(' ')))