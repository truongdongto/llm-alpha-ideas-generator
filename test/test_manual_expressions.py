"""
test_manual_expressions.py
===========================
Hand-computed checks for every new/changed operator, on a tiny
deterministic 3-ticker/5-day panel where expected values are computed
independently (numpy one-liners we trust, or by hand).
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd

from dsl.evaluator import evaluate_expression, AlphaEvaluationError
from dsl.parser import parse_expression, AlphaExpressionSyntaxError

dates = pd.bdate_range("2024-01-01", periods=5)
tickers = ["AAA", "BBB", "CCC"]

close = pd.DataFrame({"AAA": [10, 11, 12, 11, 13], "BBB": [20, 19, 21, 22, 20], "CCC": [5, 5, 6, 7, 8]},
                      index=dates, dtype=float)
volume = pd.DataFrame({"AAA": [100, 150, 120, 130, 140], "BBB": [200, 210, 190, 220, 230], "CCC": [50, 60, 55, 65, 70]},
                       index=dates, dtype=float)
high = close + 1
low = close - 1
open_ = close.shift(1).fillna(close.iloc[0])
returns = close.pct_change()

panel = {"close": close, "open": open_, "high": high, "low": low, "volume": volume,
         "returns": returns, "vwap": close, "adv20": volume.rolling(20, min_periods=1).mean()}

failures = []


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    if not condition:
        failures.append(label)
    print(f"[{status}] {label}")


ev = lambda e: evaluate_expression(e, panel)

# --- elementwise ---
check("abs(-5)-style: abs(open-close) AAA day2 == |10-11| == 1", np.isclose(ev("abs(open - close)")["AAA"].iloc[1], 1.0))
check("sqrt(close) AAA day1 == sqrt(10)", np.isclose(ev("sqrt(close)")["AAA"].iloc[0], np.sqrt(10)))
check("inverse(close) AAA day1 == 1/10", np.isclose(ev("inverse(close)")["AAA"].iloc[0], 0.1))
check("reverse(close) AAA day1 == -10", np.isclose(ev("reverse(close)")["AAA"].iloc[0], -10.0))
check("power(close, 2) AAA day1 == 100", np.isclose(ev("power(close, 2)")["AAA"].iloc[0], 100.0))
check("signed_power(close - open, 2) AAA day2 == sign(1)*1^2 == 1",
      np.isclose(ev("signed_power(close - open, 2)")["AAA"].iloc[1], 1.0))
check("is_nan: no NaN in close -> all 0", (ev("is_nan(close)") == 0).all().all())

# --- n-ary arithmetic ---
check("add(close, open, volume) AAA day1 == 10+10+100 == 120",
      np.isclose(ev("add(close, open, volume)")["AAA"].iloc[0], 120.0))
check("subtract(close, open, 1) AAA day2 == 11-10-1 == 0",
      np.isclose(ev("subtract(close, open, 1)")["AAA"].iloc[1], 0.0))
check("multiply(close, 2, 3) AAA day1 == 10*2*3 == 60",
      np.isclose(ev("multiply(close, 2, 3)")["AAA"].iloc[0], 60.0))
check("divide(close, 2) AAA day1 == 5", np.isclose(ev("divide(close, 2)")["AAA"].iloc[0], 5.0))
check("max(close, 15) AAA day1 == max(10,15) == 15", np.isclose(ev("max(close, 15)")["AAA"].iloc[0], 15.0))
check("min(close, 15) AAA day1 == min(10,15) == 10", np.isclose(ev("min(close, 15)")["AAA"].iloc[0], 10.0))

# add(x, y, filter=true) treats NaN as 0 before summing
panel_nan = dict(panel)
close_with_nan = close.copy()
close_with_nan.iloc[0, 0] = np.nan
panel_nan["close"] = close_with_nan
result_filter = evaluate_expression("add(close, 5, filter=true)", panel_nan)
check("add(..., filter=true) treats NaN as 0: NaN+5 == 5", np.isclose(result_filter["AAA"].iloc[0], 5.0))

# --- logical / comparison ---
check("close > open AAA day2 (11>10) == 1.0", np.isclose(ev("close > open")["AAA"].iloc[1], 1.0))
check("close > open AAA day1 (10>10 False) == 0.0", np.isclose(ev("close > open")["AAA"].iloc[0], 0.0))
check("close != open AAA day1 (10!=10 False) == 0.0", np.isclose(ev("close != open")["AAA"].iloc[0], 0.0))
check("and(close > open, volume > 0) AAA day2 == 1 (both true)",
      np.isclose(ev("and(close > open, volume > 0)")["AAA"].iloc[1], 1.0))
check("or(close < open, volume > 0) AAA day1 == 1 (volume>0 true)",
      np.isclose(ev("or(close < open, volume > 0)")["AAA"].iloc[0], 1.0))
check("not(close > open) AAA day1 == 1 (close>open is false)",
      np.isclose(ev("not(close > open)")["AAA"].iloc[0], 1.0))
check("if_else(close > open, 1, -1) AAA day2 == 1 (condition true)",
      np.isclose(ev("if_else(close > open, 1, -1)")["AAA"].iloc[1], 1.0))
check("if_else(close > open, 1, -1) AAA day1 == -1 (condition false)",
      np.isclose(ev("if_else(close > open, 1, -1)")["AAA"].iloc[0], -1.0))

# --- cross-sectional ---
result = ev("rank(close)")
check("rank(close) last day: CCC=8 lowest -> 1/3", np.isclose(result["CCC"].iloc[-1], 1/3))
check("rank(close) last day: BBB=20 highest -> 3/3", np.isclose(result["BBB"].iloc[-1], 1.0))

result = ev("scale(close)")
check("scale(close) (default): sum(|weights|) == 1 each day",
      np.allclose(result.abs().sum(axis=1).dropna(), 1.0))

result = ev("normalize(close, useStd=true)")
check("normalize(close, useStd=true): cross-sectional mean ~ 0 each day",
      np.allclose(result.mean(axis=1).dropna(), 0.0, atol=1e-8))

result = ev("winsorize(close, std=1)")
mean_last, std_last = close.iloc[-1].mean(), close.iloc[-1].std()
check("winsorize clips values beyond mean +/- 1*std on last day",
      result.iloc[-1].max() <= mean_last + 1 * std_last + 1e-8)

# --- time-series ---
check("ts_delay(close, 2) AAA last day == close 2 days ago == 12", np.isclose(ev("ts_delay(close, 2)")["AAA"].iloc[-1], 12.0))
check("ts_delta(close, 2) AAA last day == 13-12 == 1", np.isclose(ev("ts_delta(close, 2)")["AAA"].iloc[-1], 1.0))
check("ts_sum(close, 3) CCC last day == 6+7+8 == 21", np.isclose(ev("ts_sum(close, 3)")["CCC"].iloc[-1], 21.0))
check("ts_product(close, 2) AAA last day == 11*13 == 143", np.isclose(ev("ts_product(close, 2)")["AAA"].iloc[-1], 143.0))
check("ts_mean(close, 3) CCC last day == mean(6,7,8) == 7", np.isclose(ev("ts_mean(close, 3)")["CCC"].iloc[-1], 7.0))

expected_std = close["CCC"].iloc[2:5].std()
check("ts_std_dev(close, 3) CCC last day matches pandas .std()",
      np.isclose(ev("ts_std_dev(close, 3)")["CCC"].iloc[-1], expected_std))

expected_zscore = (close["CCC"].iloc[-1] - close["CCC"].iloc[2:5].mean()) / expected_std
check("ts_zscore(close, 3) CCC last day matches manual (x - mean)/std",
      np.isclose(ev("ts_zscore(close, 3)")["CCC"].iloc[-1], expected_zscore))

# ts_arg_max/min: AAA close=[10,11,12,11,13], last 3 days window=[12,11,13] -> max=13 at offset 0 (today)
check("ts_arg_max(close, 3) AAA last day == 0 (today is the max in the window)",
      np.isclose(ev("ts_arg_max(close, 3)")["AAA"].iloc[-1], 0.0))
# BBB close=[20,19,21,22,20], last 3 days=[21,22,20] -> min=20 at offset 0 (today)
check("ts_arg_min(close, 3) BBB last day == 0 (today is the min in the window)",
      np.isclose(ev("ts_arg_min(close, 3)")["BBB"].iloc[-1], 0.0))

# ts_scale: CCC last 3 days=[6,7,8] -> (8-6)/(8-6) == 1.0 (today is the window max)
check("ts_scale(close, 3) CCC last day == 1.0 (today is window max)",
      np.isclose(ev("ts_scale(close, 3)")["CCC"].iloc[-1], 1.0))

check("ts_step(1) is the same value across all tickers on a given day",
      ev("ts_step(1)").iloc[-1].nunique() == 1)
check("ts_step(1) last day == 5 (5th business day)", np.isclose(ev("ts_step(1)")["AAA"].iloc[-1], 5.0))

# ts_covariance(y, x, d) matches pandas rolling cov
expected_cov = volume["AAA"].rolling(4, min_periods=2).cov(close["AAA"])
check("ts_covariance(volume, close, 4) matches pandas rolling .cov()",
      np.allclose(ev("ts_covariance(volume, close, 4)")["AAA"].dropna(), expected_cov.dropna()))

# ts_backfill
close_gap = close.copy()
close_gap.iloc[1, 0] = np.nan  # AAA day2 missing
panel_gap = dict(panel)
panel_gap["close"] = close_gap
result = evaluate_expression("ts_backfill(close, lookback=5)", panel_gap)
check("ts_backfill fills the gap with the last valid value (10)", np.isclose(result["AAA"].iloc[1], 10.0))

check("ts_count_nans(close, 5) AAA counts exactly 1 NaN after the gap",
      evaluate_expression("ts_count_nans(close, 5)", panel_gap)["AAA"].iloc[-1] == 1)

# --- error handling ---
try:
    ev("rank(close, bogus_kwarg=1)")
    check("unknown kwarg should raise", False)
except AlphaEvaluationError:
    check("unknown kwarg raises AlphaEvaluationError", True)

try:
    ev("add(close)")
    check("variadic op below min_args should raise", False)
except AlphaEvaluationError:
    check("add() with only 1 arg raises AlphaEvaluationError (needs >=2)", True)

try:
    parse_expression("rank(close, filter=)")
    check("malformed kwarg syntax should raise", False)
except AlphaExpressionSyntaxError:
    check("malformed kwarg syntax raises AlphaExpressionSyntaxError", True)

print("\n" + "=" * 60)
if failures:
    print(f"{len(failures)} CHECK(S) FAILED:")
    for f in failures:
        print(f"  - {f}")
    raise SystemExit(1)
else:
    print("ALL CHECKS PASSED")