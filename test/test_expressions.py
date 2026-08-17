"""
test_manual_expressions.py
===========================
Validates the DSL parser + evaluator against a TINY, hand-crafted dataset
where we can compute the expected result by hand (or with plain pandas
one-liners we trust) and assert equality. This is stronger than the shape
checks in dsl/evaluator.py's __main__ block -- it actually proves the
operators compute the RIGHT NUMBERS, not just the right shape.

Rationale: this is the checkpoint before Module 2 (backtest engine). If
the evaluator has a subtle bug (e.g. off-by-one in a rolling window, or
rank direction reversed), every alpha backtested downstream would be
silently wrong. Better to catch it here with 3 tickers / 5 days by hand
than 3 months from now looking at a suspicious IC.
"""

import numpy as np
import pandas as pd

from dsl.evaluator import evaluate_expression, AlphaEvaluationError
from dsl.parser import parse_expression, AlphaExpressionSyntaxError

# ---------------------------------------------------------------------------
# Tiny deterministic panel: 3 tickers, 5 days, hand-pickable numbers
# ---------------------------------------------------------------------------
dates = pd.bdate_range("2024-01-01", periods=5)
tickers = ["AAA", "BBB", "CCC"]

close = pd.DataFrame(
    {
        "AAA": [10, 11, 12, 11, 13],
        "BBB": [20, 19, 21, 22, 20],
        "CCC": [ 5,  5,  6,  7,  8],
    },
    index=dates, dtype=float,
)
volume = pd.DataFrame(
    {
        "AAA": [100, 150, 120, 130, 140],
        "BBB": [200, 210, 190, 220, 230],
        "CCC": [ 50,  60,  55,  65,  70],
    },
    index=dates, dtype=float,
)
open_ = close.shift(1).fillna(close.iloc[0])
returns = close.pct_change()

panel = {
    "close": close,
    "open": open_,
    "volume": volume,
    "returns": returns,
    "high": close,   # not used in these tests, placeholder
    "low": close,
    "vwap": close,
    "adv20": volume.rolling(20, min_periods=1).mean(),
}

failures = []


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    if not condition:
        failures.append(label)
    print(f"[{status}] {label}")


# ---------------------------------------------------------------------------
# 1. Field lookup is a plain passthrough
# ---------------------------------------------------------------------------
result = evaluate_expression("close", panel)
check("field passthrough: close == raw close data", result.equals(close))

# ---------------------------------------------------------------------------
# 2. rank(): cross-sectional percentile rank on the LAST day
#    2024-01-05 close: AAA=13, BBB=20, CCC=8  -> order CCC < AAA < BBB
#    pct rank (pandas default, ties->average, ascending): CCC=1/3, AAA=2/3, BBB=3/3
# ---------------------------------------------------------------------------
result = evaluate_expression("rank(close)", panel)
last_row = result.iloc[-1]
check("rank(close) last day: CCC lowest -> rank 1/3",
      np.isclose(last_row["CCC"], 1/3))
check("rank(close) last day: AAA middle -> rank 2/3",
      np.isclose(last_row["AAA"], 2/3))
check("rank(close) last day: BBB highest -> rank 3/3",
      np.isclose(last_row["BBB"], 1.0))

# ---------------------------------------------------------------------------
# 3. ts_delta(x, n): x - x shifted n days
#    AAA close: [10, 11, 12, 11, 13] -> ts_delta(close, 2) on day5 = 13 - 12 = 1
# ---------------------------------------------------------------------------
result = evaluate_expression("ts_delta(close, 2)", panel)
check("ts_delta(close, 2) AAA last day == 13 - 12 == 1",
      np.isclose(result["AAA"].iloc[-1], 1.0))
check("ts_delta(close, 2) BBB last day == 20 - 21 == -1",
      np.isclose(result["BBB"].iloc[-1], -1.0))

# ---------------------------------------------------------------------------
# 4. ts_mean(x, n): rolling mean
#    CCC close: [5, 5, 6, 7, 8] -> ts_mean(close, 3) on last day = mean(6,7,8) = 7
# ---------------------------------------------------------------------------
result = evaluate_expression("ts_mean(close, 3)", panel)
check("ts_mean(close, 3) CCC last day == mean(6,7,8) == 7",
      np.isclose(result["CCC"].iloc[-1], 7.0))

# ---------------------------------------------------------------------------
# 5. Arithmetic composition: (close - open) should be 0 on day 1 (open==close by construction)
#    and match manual diff on later days
# ---------------------------------------------------------------------------
result = evaluate_expression("close - open", panel)
check("close - open == 0 on day 1 (open seeded from close)",
      np.isclose(result["AAA"].iloc[0], 0.0))
check("close - open AAA day2 == 11 - 10 == 1",
      np.isclose(result["AAA"].iloc[1], 1.0))

# ---------------------------------------------------------------------------
# 6. Unary negation + scalar multiply
# ---------------------------------------------------------------------------
result = evaluate_expression("-close * 2", panel)
check("-close * 2 AAA day1 == -20", np.isclose(result["AAA"].iloc[0], -20.0))

# ---------------------------------------------------------------------------
# 7. log()
# ---------------------------------------------------------------------------
result = evaluate_expression("log(close)", panel)
check("log(close) AAA day1 == log(10)", np.isclose(result["AAA"].iloc[0], np.log(10)))

# ---------------------------------------------------------------------------
# 8. ts_corr(x, y, n): sanity check it's bounded in [-1, 1] and matches
#    pandas' own rolling corr computed independently
# ---------------------------------------------------------------------------
result = evaluate_expression("ts_corr(volume, close, 4)", panel)
expected_aaa = volume["AAA"].rolling(4, min_periods=2).corr(close["AAA"])
check("ts_corr(volume, close, 4) matches pandas rolling corr (AAA)",
      np.allclose(result["AAA"].dropna(), expected_aaa.dropna()))

# ---------------------------------------------------------------------------
# 9. Nested / composed expression from the earlier deep-dive example
# ---------------------------------------------------------------------------
result = evaluate_expression("rank(ts_delta(close, 1) / ts_std(returns, 3))", panel)
check("composed expression produces correct shape", result.shape == close.shape)
check("composed expression is a valid rank (values in [0,1] where defined)",
      result.dropna().le(1.0).all().all() and result.dropna().ge(0.0).all().all())

# ---------------------------------------------------------------------------
# 10. Error handling: syntax errors and semantic errors should raise our
#     custom exceptions, not generic tracebacks
# ---------------------------------------------------------------------------
try:
    parse_expression("rank(close +)")
    check("malformed syntax should raise", False)
except AlphaExpressionSyntaxError:
    check("malformed syntax raises AlphaExpressionSyntaxError", True)

try:
    evaluate_expression("nonexistent_field", panel)
    check("unknown field should raise", False)
except AlphaEvaluationError:
    check("unknown field raises AlphaEvaluationError", True)

try:
    evaluate_expression("ts_mean(close, close)", panel)
    check("non-numeric window arg should raise", False)
except AlphaEvaluationError:
    check("non-numeric window arg raises AlphaEvaluationError", True)


# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
if failures:
    print(f"{len(failures)} CHECK(S) FAILED:")
    for f in failures:
        print(f"  - {f}")
    raise SystemExit(1)
else:
    print("ALL CHECKS PASSED")