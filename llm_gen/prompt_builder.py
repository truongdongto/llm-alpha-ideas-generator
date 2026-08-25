"""
llm_gen/prompt_builder.py
==========================
Builds the system + user prompt. Operator list is pulled directly from
dsl.operators.REGISTRY (name + description + arg signature), so the
prompt can never drift from what the DSL actually supports.
"""
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
sys.path.append(str(Path(__file__).parent.parent))

from dsl.operators import REGISTRY
from data_layer import ALL_FIELDS

SYSTEM_PROMPT_TEMPLATE = """You are a quantitative researcher generating alpha factor expressions \
for equity trading, following WorldQuant BRAIN's alpha expression language.

An "alpha" is a formula computed on daily cross-sectional market data that produces a \
numeric score per stock per day; stocks with higher scores are expected to have higher \
forward returns than stocks with lower scores.

AVAILABLE DATA FIELDS (each is a date x ticker matrix):
{fields}

AVAILABLE OPERATORS:
{operators}

RULES:
- Only use the fields and operators listed above.
- Positional args marked (int) must be plain numeric literals (e.g. the "d" in ts_mean(x, d)).
- Keyword args must use the exact names shown, e.g. rank(x, rate=2), add(x, y, filter=true).
- Comparisons (x > y, x == y, etc.) and add/subtract/multiply/max/min accept 2+ inputs.
- Prefer expressions with a clear economic rationale over arbitrary formulas.
- Prefer NEW, DIVERSE ideas over sign-flips or trivial rescalings of alphas already tried.

OUTPUT FORMAT:
Respond with ONLY a JSON array, no other text:
[{{"expression": "rank(ts_delta(close, 5))", "rationale": "short-term momentum"}}, ...]
"""

USER_PROMPT_TEMPLATE = """Generate {n} new alpha expressions.

{feedback_section}
Respond with the JSON array only.
"""


def _format_operator_line(name: str) -> str:
    spec = REGISTRY[name]
    if spec.arg_types is not None:
        arg_str = ", ".join(spec.arg_types)
    else:
        arg_str = f"data, data, ... (min {spec.min_args})"
    kwarg_str = ""
    if spec.kwargs:
        kwarg_str = ", " + ", ".join(f"{k}={v}" for k, v in spec.kwargs.items())
    return f"  - {name}({arg_str}{kwarg_str}): {spec.description}"


def build_system_prompt() -> str:
    op_lines = "\n".join(_format_operator_line(name) for name in sorted(REGISTRY))
    field_lines = "\n".join(f"  - {f}" for f in sorted(ALL_FIELDS))
    return SYSTEM_PROMPT_TEMPLATE.format(fields=field_lines, operators=op_lines)


def build_feedback_section(
    leaderboard: pd.DataFrame,
    top_k: int = 5,
    recent_invalid_k: int = 5,
) -> str:
    """
    Summarize the research done so far into a short text block the LLM
    can condition on. Pulled from the running leaderboard maintained by
    orchestrate.py.

    Two things the LLM gets shown:
      - the TOP performing valid alphas so far (to build on / diversify from)
      - the MOST RECENT invalid/malformed attempts (to stop repeating
        syntax mistakes -- this materially improves valid-output rate
        in practice)
    """
    if leaderboard.empty:
        return "No alphas have been tried yet. This is the first round.\n"

    valid_mask = leaderboard["valid"].astype(bool)
    valid = leaderboard[valid_mask].sort_values("reward", ascending=False)
    invalid = leaderboard[~valid_mask].tail(recent_invalid_k)

    lines = []
    if len(valid) > 0:
        lines.append(f"TOP {min(top_k, len(valid))} ALPHAS SO FAR (higher reward = better):")
        for _, row in valid.head(top_k).iterrows():
            lines.append(
                f'  - "{row["expression"]}" | reward={row["reward"]:.3f} '
                f'| mean_ic={row["mean_ic"]:.4f} | turnover={row["turnover"]:.2f}'
            )
    else:
        lines.append("No valid alphas found yet -- prioritize getting the SYNTAX right first.")

    if len(invalid) > 0:
        lines.append(f"\nRECENT INVALID ATTEMPTS (do not repeat these mistakes):")
        for _, row in invalid.iterrows():
            lines.append(f'  - "{row["expression"]}" -> {row["error"]}')

    lines.append(
        "\nGenerate ideas that are DIFFERENT from the top alphas above (avoid high "
        "correlation / sign-flip duplicates) while still being syntactically valid."
    )
    return "\n".join(lines) + "\n"


def build_user_prompt(n: int, leaderboard: pd.DataFrame, top_k: int = 5) -> str:
    feedback = build_feedback_section(leaderboard, top_k=top_k)
    return USER_PROMPT_TEMPLATE.format(n=n, feedback_section=feedback)


if __name__ == "__main__":
    print(build_system_prompt())
    print("-" * 60)
    empty_leaderboard = pd.DataFrame(columns=["expression", "valid", "reward", "mean_ic", "turnover", "error"])
    print(build_user_prompt(5, empty_leaderboard))