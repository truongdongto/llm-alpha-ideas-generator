import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
import random

from sft.worldquant_alphas import WORLDQUANT_INSPIRED_ALPHAS, THEMES
from llm_gen.prompt_builder import build_system_prompt

USER_TEMPLATES = [
    "Generate {n} new alpha expressions.",
    "Generate {n} new alpha expressions focusing on {theme}.",
    "Propose {n} alpha ideas related to {theme} signals.",
]


def _format_assistant_json(batch: list[dict]) -> str:
    return json.dumps(
        [{"expression": a["expression"], "rationales": a["rationales"]} for a in batch],
        ensure_ascii=False,
    )


def build_sft_examples(seed: int = 0, min_batch: int = 2, max_batch: int = 5) -> list[dict]:
    """Returns list of {"messages": [...]} chat examples."""
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

        template = rng.choice(USER_TEMPLATES)
        themes_in_batch = [a["theme"] for a in batch]
        dominant_theme = max(set(themes_in_batch), key=themes_in_batch.count)
        user_msg = template.format(n=len(batch), theme=dominant_theme)

        examples.append({
            "messages": [
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": _format_assistant_json(batch)},
            ]
        })
    return examples


if __name__ == "__main__":
    examples = build_sft_examples(seed=42)
    print(f"Built {len(examples)} SFT examples from {len(WORLDQUANT_INSPIRED_ALPHAS)} curated alphas")
    print(f"Themes: {THEMES}")
    print("\nSample example:")
    print(json.dumps(examples[0], ensure_ascii=False, indent=2))