"""
test_backtest_engine.py
========================
Validates backtest/engine.py two ways:

1. CROSS-CHECK vs a trusted (but slow) ground truth: compute IC with a
   plain Python loop over dates calling scipy.stats.spearmanr, and assert
   our vectorized compute_ic_series() matches it. This proves the
   vectorization didn't change the math.

2. KNOWN-ANSWER tests: build a synthetic dataset where we control the
   data-generating process ourselves, so we KNOW in advance what the
   "correct" answer should look like:
     - a signal that's constructed to genuinely predict forward returns
       must show high positive mean IC and a monotonic quantile spread
     - a signal built from independent random noise must show mean IC
       close to 0
     - turnover of a constant (unchanging) signal must be 0
     - a signal correlated with itself must give alpha_correlation == 1.0

This is the same principle as the roadmap note for Module 4: validate
against a KNOWN alpha before trusting the engine on LLM-generated ones.
"""

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from backtest.engine import (
    forward_returns, compute_ic_series, ic_summary, ic_decay,
    compute_quantile_daily_returns, quantile_summary,
    signal_to_weights, compute_turnover, alpha_correlation, backtest_alpha,
)

failures = []


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    if not condition:
        failures.append(label)
    print(f"[{status}] {label}")


# ---------------------------------------------------------------------------
# Part 1: cross-check vectorized IC vs scipy loop-based ground truth
# ---------------------------------------------------------------------------
rng = np.random.default_rng(7)
dates = pd.bdate_range("2023-01-02", periods=80)
tickers = [f"T{i:02d}" for i in range(15)]

signal = pd.DataFrame(rng.standard_normal((80, 15)), index=dates, columns=tickers)
fwd_ret = pd.DataFrame(rng.standard_normal((80, 15)) * 0.02, index=dates, columns=tickers)
# sprinkle in some NaNs to make sure the masking logic is exercised too
mask_nan = rng.random((80, 15)) < 0.05
signal = signal.mask(mask_nan)

vectorized_ic = compute_ic_series(signal, fwd_ret, method="spearman")

ground_truth = {}
for d in dates:
    x = signal.loc[d]
    y = fwd_ret.loc[d]
    valid = x.notna() & y.notna()
    if valid.sum() < 3:
        ground_truth[d] = np.nan
        continue
    corr, _ = spearmanr(x[valid], y[valid])
    ground_truth[d] = corr
ground_truth = pd.Series(ground_truth)

check(
    "vectorized IC matches scipy.stats.spearmanr loop (all dates)",
    np.allclose(vectorized_ic.dropna(), ground_truth.dropna(), atol=1e-8),
)

# ---------------------------------------------------------------------------
# Part 2: known-answer test with an injected predictive relationship
#
# Construct returns as: return[t] = 0.8 * zscore(factor[t-1]) + small noise
# so `factor` (lagged) should have HIGH IC predicting forward_returns(1),
# while an unrelated random field should have ~0 IC.
# ---------------------------------------------------------------------------
rng2 = np.random.default_rng(123)
n_days, n_tickers = 250, 25
dates2 = pd.bdate_range("2022-01-03", periods=n_days)
tick2 = [f"S{i:02d}" for i in range(n_tickers)]

factor = pd.DataFrame(rng2.standard_normal((n_days, n_tickers)), index=dates2, columns=tick2)
factor_z = factor.sub(factor.mean(axis=1), axis=0).div(factor.std(axis=1), axis=0)

noise = pd.DataFrame(rng2.standard_normal((n_days, n_tickers)), index=dates2, columns=tick2)
# return realized ON day t is driven by factor known at t-1 (this is what
# makes it a legitimately laggable predictive signal, not lookahead)
daily_log_ret = 0.03 * factor_z.shift(1).fillna(0.0) + 0.01 * noise
close = 100 * np.exp(daily_log_ret.cumsum())

unrelated_field = pd.DataFrame(rng2.standard_normal((n_days, n_tickers)), index=dates2, columns=tick2)

fwd1 = forward_returns(close, 1)

# the "oracle" signal: factor_z evaluated at t predicts fwd1 at t (return t->t+1)
oracle_ic = compute_ic_series(factor_z, fwd1)
oracle_summary = ic_summary(oracle_ic)
check(
    f"oracle signal (factor_z) has strong positive mean IC (got {oracle_summary['mean_ic']:.3f})",
    oracle_summary["mean_ic"] > 0.3,
)
check(
    f"oracle signal has reasonably high hit rate (got {oracle_summary['hit_rate']:.2f})",
    oracle_summary["hit_rate"] > 0.7,
)

unrelated_ic = compute_ic_series(unrelated_field, fwd1)
unrelated_summary = ic_summary(unrelated_ic)
check(
    f"unrelated random field has mean IC close to 0 (got {unrelated_summary['mean_ic']:.3f})",
    abs(unrelated_summary["mean_ic"]) < 0.15,
)

# quantile returns for the oracle signal should be monotonic and show a
# clear positive long-short spread
daily_q = compute_quantile_daily_returns(factor_z, fwd1, n_quantiles=5)
q_summary = quantile_summary(daily_q)
check(
    f"oracle signal quantile returns are monotonic (got means={q_summary['mean_return_by_quantile'].round(4).to_dict()})",
    q_summary["monotonic"],
)
check(
    f"oracle signal long-short spread is positive and significant (mean={q_summary['long_short_mean']:.4f}, t={q_summary['long_short_tstat']:.2f})",
    q_summary["long_short_mean"] > 0 and q_summary["long_short_tstat"] > 2,
)

# ---------------------------------------------------------------------------
# Part 3: turnover sanity checks
# ---------------------------------------------------------------------------
constant_signal = pd.DataFrame(
    np.tile(np.arange(n_tickers), (n_days, 1)), index=dates2, columns=tick2, dtype=float
)
check(
    "turnover of an unchanging signal is (approximately) 0",
    np.isclose(compute_turnover(constant_signal), 0.0, atol=1e-8),
)

alternating_signal = pd.DataFrame(
    rng2.standard_normal((n_days, n_tickers)), index=dates2, columns=tick2
)
check(
    "turnover of a freshly-random-each-day signal is meaningfully > 0",
    compute_turnover(alternating_signal) > 0.1,
)

# ---------------------------------------------------------------------------
# Part 4: alpha-vs-alpha correlation sanity checks
# ---------------------------------------------------------------------------
check(
    "alpha_correlation(x, x) == 1.0 (self-correlation)",
    np.isclose(alpha_correlation(factor_z, factor_z), 1.0, atol=1e-8),
)
check(
    "alpha_correlation(x, -x) == -1.0 (perfectly inverse)",
    np.isclose(alpha_correlation(factor_z, -factor_z), -1.0, atol=1e-8),
)
check(
    "alpha_correlation(oracle, unrelated) is close to 0",
    abs(alpha_correlation(factor_z, unrelated_field)) < 0.15,
)

# ---------------------------------------------------------------------------
# Part 5: end-to-end orchestrator smoke test
# ---------------------------------------------------------------------------
result = backtest_alpha(factor_z, close, horizons=(1, 5, 10, 20), n_quantiles=5)
check("backtest_alpha() returns ic_decay table with all 4 horizons",
      list(result["ic_decay"].index) == [1, 5, 10, 20])
check("backtest_alpha() primary_horizon_ic mean_ic matches standalone computation",
      np.isclose(result["primary_horizon_ic"]["mean_ic"], oracle_summary["mean_ic"], atol=1e-8))
check("backtest_alpha() includes turnover as a finite number",
      np.isfinite(result["turnover"]))

print("\nIC decay table for the oracle signal (should decay toward 0 as horizon grows):")
print(result["ic_decay"][["mean_ic", "ic_ir", "n_days"]])


# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
if failures:
    print(f"{len(failures)} CHECK(S) FAILED:")
    for f in failures:
        print(f"  - {f}")
    raise SystemExit(1)
else:
    print("ALL CHECKS PASSED")