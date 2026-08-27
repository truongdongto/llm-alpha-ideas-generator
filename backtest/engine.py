"""
backtest/engine.py
===================
Responsibility: take a computed alpha SIGNAL (a date x ticker DataFrame,
as produced by dsl.evaluator) and evaluate whether it has genuine
predictive power over future returns. This is the module that turns
"a formula the LLM wrote" into "a number telling you if it's any good".

Core metrics, all standard in quant alpha research:

  IC (Information Coefficient)
      Spearman rank correlation, computed PER DATE, between the signal
      and the forward return. A time series of daily IC values.
      -> mean_ic close to 0 = no predictive power
      -> mean_ic > 0.02-0.03 with a stable sign is considered interesting
         in real (noisy) equity data; this is a LOW bar on purpose,
         real alphas are weak signals averaged over many bets.

  IC decay
      Same computation repeated at multiple forward horizons (1, 5, 10,
      20 days) to see how quickly the signal's predictive power fades.

  Quantile returns
      Bucket the cross-section into N quantiles by signal value each day,
      average the forward return within each bucket. A genuinely useful
      alpha should show a roughly MONOTONIC relationship between quantile
      rank and average forward return -- and the top-minus-bottom
      ("long-short") spread is the return you'd have captured trading it.

  Turnover
      How much the implied portfolio weights change day to day. High
      turnover means high transaction costs eat into any edge. Computed
      by converting the raw signal into rank-demeaned, unit-gross weights
      first (a standard "signal -> portfolio" step), then summing the
      day-over-day absolute weight change.

  Alpha correlation
      Cross-sectional correlation between two DIFFERENT alpha signals,
      averaged over time. Used later to filter out alphas that are just
      redundant restatements of ones you already have (BRAIN and most
      research platforms penalize this heavily).

VECTORIZATION NOTE:
    IC is Spearman correlation, which is just Pearson correlation
    computed on RANKS. Rather than looping over dates and calling
    scipy.stats.spearmanr() date-by-date (slow once you have thousands
    of dates x hundreds of tickers x hundreds of candidate alphas), we
    rank each row (cross-sectionally, axis=1) and compute the row-wise
    Pearson correlation directly with pandas broadcasting. This computes
    IC for ALL dates in one shot with no Python-level loop.
"""

from __future__ import annotations
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Forward returns
# ---------------------------------------------------------------------------

def forward_returns(close: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """
    Return realized from t to t+horizon, indexed at t.
    """
    return close.shift(-horizon) / close - 1.0


# ---------------------------------------------------------------------------
# IC (Information Coefficient)
# ---------------------------------------------------------------------------

def compute_ic_series(
    signal: pd.DataFrame,
    fwd_ret: pd.DataFrame,
    method: str = "spearman",
    min_valid: int = 3,
) -> pd.Series:
    """
    Cross-sectional IC per date, fully vectorized (no per-date loop).

    method="spearman" (default): rank both signal and forward return
        cross-sectionally per date, then compute row-wise Pearson corr
        on the ranks -- this IS Spearman correlation.
    method="pearson": skip the ranking step, correlate raw values.

    Returns a pd.Series indexed by date. Dates with fewer than
    `min_valid` non-NaN ticker pairs are NaN (not enough cross-section
    to compute a meaningful correlation).
    """
    # mask so a ticker is used only where BOTH signal and fwd_ret exist --
    # ranking must see the identical set of ticker on both sides
    valid = signal.notna() & fwd_ret.notna()
    x = signal.where(valid)
    y = fwd_ret.where(valid)

    if method == "spearman":
        x = x.rank(axis=1)
        y = y.rank(axis=1)
    elif method != "pearson":
        raise ValueError(f"Unknown method {method!r}, expected 'spearman' or 'pearson'")

    n_valid = valid.sum(axis=1)

    mean_x = x.mean(axis=1)
    mean_y = y.mean(axis=1)
    dx = x.sub(mean_x, axis=0)
    dy = y.sub(mean_y, axis=0)

    cov = (dx * dy).mean(axis=1)
    std_x = dx.pow(2).mean(axis=1).pow(0.5)
    std_y = dy.pow(2).mean(axis=1).pow(0.5)

    with np.errstate(invalid="ignore", divide="ignore"):
        ic = cov / (std_x * std_y)

    ic = ic.where(n_valid >= min_valid)
    return ic


def ic_summary(ic_series: pd.Series) -> dict:
    """
    Collapse a daily IC series into the handful of numbers people
    actually look at when screening an alpha.
    """
    clean = ic_series.dropna()
    n = len(clean)
    if n == 0:
        return {"mean_ic": np.nan, "std_ic": np.nan, "ic_ir": np.nan,
                "hit_rate": np.nan, "n_days": 0}
    mean_ic = clean.mean()
    std_ic = clean.std()
    return {
        "mean_ic": mean_ic,
        "std_ic": std_ic,
        # IC Information Ratio: signal-to-noise of the daily IC itself.
        # Higher = more CONSISTENT predictive power, not just occasionally lucky.
        "ic_ir": mean_ic / std_ic if std_ic > 0 else np.nan,
        # fraction of days IC had the same sign as the overall mean
        "hit_rate": (np.sign(clean) == np.sign(mean_ic)).mean(),
        "n_days": n,
    }


def ic_decay(
    signal: pd.DataFrame,
    close: pd.DataFrame,
    horizons: tuple[int, ...] = (1, 5, 10, 20),
    method: str = "spearman",
) -> pd.DataFrame:
    """
    Run compute_ic_series + ic_summary at multiple forward horizons.
    Returns a DataFrame indexed by horizon with columns
    [mean_ic, std_ic, ic_ir, hit_rate, n_days].
    """
    rows = {}
    for h in horizons:
        fwd = forward_returns(close, h)
        ic = compute_ic_series(signal, fwd, method=method)
        rows[h] = ic_summary(ic)
    return pd.DataFrame(rows).T.rename_axis("horizon")


# ---------------------------------------------------------------------------
# Quantile returns
# ---------------------------------------------------------------------------

def quantile_bucket(signal: pd.DataFrame, n_quantiles: int = 5) -> pd.DataFrame:
    """
    Assign each (date, ticker) to a quantile bucket 1..n_quantiles based
    on the signal's cross-sectional percentile rank that day. Fully
    vectorized: uses percentile rank + ceil, no pd.qcut-per-row loop.
    """
    pct_rank = signal.rank(axis=1, pct=True)  # in (0, 1], NaN preserved
    bucket = np.ceil(pct_rank * n_quantiles)
    bucket = bucket.clip(upper=n_quantiles)
    return bucket


def compute_quantile_daily_returns(
    signal: pd.DataFrame,
    fwd_ret: pd.DataFrame,
    n_quantiles: int = 5,
) -> pd.DataFrame:
    """
    For each date, the average forward return of tickers in each quantile.
    Returns a DataFrame: index=date, columns=1..n_quantiles.
    """
    bucket = quantile_bucket(signal, n_quantiles)
    out = {}
    for q in range(1, n_quantiles + 1):
        mask = bucket == q
        out[q] = fwd_ret.where(mask).mean(axis=1)
    return pd.DataFrame(out)


def quantile_summary(daily_q_returns: pd.DataFrame) -> dict:
    """
    Collapse daily quantile returns into: per-quantile mean return, and
    the long-short (top quantile minus bottom quantile) spread with a
    t-stat (mean / (std / sqrt(n)) across days) to gauge significance.
    """
    n_quantiles = daily_q_returns.shape[1]
    mean_by_q = daily_q_returns.mean(axis=0)

    long_short_daily = daily_q_returns[n_quantiles] - daily_q_returns[1]
    ls_clean = long_short_daily.dropna()
    ls_mean = ls_clean.mean()
    ls_std = ls_clean.std()
    ls_tstat = ls_mean / (ls_std / np.sqrt(len(ls_clean))) if len(ls_clean) > 1 and ls_std > 0 else np.nan

    return {
        "mean_return_by_quantile": mean_by_q,
        "long_short_mean": ls_mean,
        "long_short_tstat": ls_tstat,
        "n_days": len(ls_clean),
        "monotonic": mean_by_q.is_monotonic_increasing or mean_by_q.is_monotonic_decreasing,
    }


# ---------------------------------------------------------------------------
# Turnover
# ---------------------------------------------------------------------------

def signal_to_weights(signal: pd.DataFrame) -> pd.DataFrame:
    """
    Convert a raw alpha signal into normalized portfolio weights:
    rank-demean cross-sectionally (so it's long the top half, short the
    bottom half), then scale so gross exposure (sum of |weight|) == 1
    each day. This is the standard "signal -> tradeable weights" step.
    """
    demeaned = signal.rank(axis=1, pct=True) - 0.5
    denom = demeaned.abs().sum(axis=1).replace(0, np.nan)
    return demeaned.div(denom, axis=0)


def compute_turnover(signal: pd.DataFrame) -> float:
    """
    Average daily turnover = mean over dates of sum_ticker |w_t - w_{t-1}|.
    A value of e.g. 0.4 means ~40% of gross exposure gets traded each day
    on average -- useful for a rough sense of transaction-cost drag.
    """
    weights = signal_to_weights(signal)
    daily_turnover = weights.diff().abs().sum(axis=1)
    return daily_turnover.iloc[1:].mean()  # drop first day (all-NaN diff)


# ---------------------------------------------------------------------------
# Alpha-vs-alpha correlation (for diversity filtering, used in Module 5)
# ---------------------------------------------------------------------------

def alpha_correlation(signal_a: pd.DataFrame, signal_b: pd.DataFrame) -> float:
    """
    Average cross-sectional correlation between two alpha signals over
    time -- a proxy for how redundant they are. Close to 1.0 (or -1.0)
    means they're basically the same bet; close to 0 means diversifying.
    Uses the same vectorized rank-correlation machinery as compute_ic_series.
    """
    ic_like = compute_ic_series(signal_a, signal_b, method="spearman")
    return ic_like.mean()


# ---------------------------------------------------------------------------
# High-level orchestrator
# ---------------------------------------------------------------------------

def backtest_alpha(
    signal: pd.DataFrame,
    close: pd.DataFrame,
    horizons: tuple[int, ...] = (1, 5, 10, 20),
    n_quantiles: int = 5,
) -> dict:
    """
    Run the full evaluation suite on one alpha signal and return a single
    dict summarizing it -- this is what Module 5 (the generate-test loop)
    will call once per LLM-generated expression.
    """
    ic_decay_table = ic_decay(signal, close, horizons=horizons)

    fwd1 = forward_returns(close, horizons[0])
    daily_q = compute_quantile_daily_returns(signal, fwd1, n_quantiles=n_quantiles)
    q_summary = quantile_summary(daily_q)

    turnover = compute_turnover(signal)

    return {
        "ic_decay": ic_decay_table,
        "primary_horizon_ic": ic_decay_table.loc[horizons[0]].to_dict(),
        "quantile_summary": q_summary,
        "turnover": turnover,
    }