"""
llm_gen/prompt_builder.py
==========================
Builds the system + user prompt sent to the LLM each round.
"""
from __future__ import annotations

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import pandas as pd
from dsl.evaluator import (
    _CROSS_SECTIONAL_UNARY, _TS_UNARY, _ELEMENTWISE_UNARY, _TS_BINARY,
)
from data_layer import ALL_FIELDS

SYSTEM_PROMPT_TEMPLATE = """You are a quantitative researcher generating alpha expressions \
for equity trading, in the style of WorldQuant BRAIN's alpha expression language.

An "alpha" is a formula computed on daily cross-sectional market data that produces a \
numeric score per stock per day; stocks with higher scores are expected to have higher \
forward returns than stocks with lower scores.

AVAILABLE DATA FIELDS (each is a date x ticker matrix):
{fields}

AVAILABLE OPERATORS:
Cross-sectional (operate across all tickers on one date):
{cross_sectional_ops}
Time-series (operate across the date axis, per ticker):
{ts_ops}
Elementwise:
{elementwise_ops}

RULES:
- Every expression must be syntactically valid: only the fields and operators listed above, \
standard arithmetic (+ - * /), and numeric literals for window sizes.
- Time-series operator window arguments (the "n" in ts_mean(x, n)) must be plain numbers, \
not expressions.
- Prefer expressions with a clear economic rationale (momentum, mean-reversion, volume/price \
divergence, volatility, liquidity, etc.) over arbitrary formulas.
- Prefer NEW, DIVERSE ideas over ones that are just sign-flips or trivial rescalings of alphas \
already tried (see feedback below).

OUTPUT FORMAT:
Respond with ONLY a JSON array, no other text, in this exact shape:
[{{"expression": "rank(ts_delta(close, 5))", "rationale": "short-term momentum"}}, ...]
"""

USER_PROMPT_TEMPLATE = """Generate {n} new alpha expressions.

{feedback_section}
Respond with the JSON array only.
"""


def _format_ops(names: list[str]) -> str:
    return "\n".join(f"  - {name}" for name in sorted(names))


def build_system_prompt() -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(
        fields=_format_ops(ALL_FIELDS),
        cross_sectional_ops=_format_ops(list(_CROSS_SECTIONAL_UNARY)),
        ts_ops=_format_ops(list(_TS_UNARY) + list(_TS_BINARY)),
        elementwise_ops=_format_ops(list(_ELEMENTWISE_UNARY)),
    )


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