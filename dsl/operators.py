"""
dsl/operators.py
=================
Registry of supported operators, modeled on WorldQuant BRAIN's operator
set (see wq_operators.json). Each entry is an OperatorSpec: how many/what
type of positional args it takes, what keyword args (with defaults) it
accepts, and the actual pandas implementation.

This is the single source of truth for what the DSL supports -- the
evaluator dispatches through this registry generically (no per-operator
hardcoded branches), and the prompt builder introspects it directly so
the LLM's system prompt can never drift from what actually runs.

NOT IMPLEMENTED (need capabilities this system doesn't have yet -- see
checklist in the accompanying response for why):
  group_* (need an industry/sector grouping field), bucket, densify,
  vec_avg, vec_sum (need vector-valued fields), trade_when, hump (need
  cross-day state), ts_regression (multi-output), quantile, ts_quantile
  (need distribution functions), kth_element, last_diff_value,
  days_from_last_change (niche time-series lookups).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class OperatorSpec:
    fn: Callable
    arg_types: tuple | None = None   # fixed arity: tuple of 'data'/'int'. None = variadic (all 'data').
    min_args: int = 2                # only used when arg_types is None (variadic)
    kwargs: dict = field(default_factory=dict)   # name -> default (bool/float)
    description: str = ""


def _bool_to_float(df: pd.DataFrame) -> pd.DataFrame:
    return df.astype(float)


# ---------------------------------------------------------------------------
# Elementwise
# ---------------------------------------------------------------------------

def _abs(a, kw): return a[0].abs()
def _log(a, kw): return np.log(a[0].clip(lower=1e-12))
def _sign(a, kw): return np.sign(a[0])
def _sqrt(a, kw): return a[0].clip(lower=0) ** 0.5
def _inverse(a, kw): return 1.0 / a[0].replace(0, np.nan)
def _reverse(a, kw): return -a[0]
def _is_nan(a, kw): return _bool_to_float(a[0].isna())
def _power(a, kw): return a[0] ** a[1]
def _signed_power(a, kw): return np.sign(a[0]) * (a[0].abs() ** a[1])


# ---------------------------------------------------------------------------
# N-ary arithmetic (variadic)
# ---------------------------------------------------------------------------

def _add(a, kw):
    dfs = [d.fillna(0) for d in a] if kw["filter"] else a
    out = dfs[0]
    for d in dfs[1:]:
        out = out + d
    return out


def _subtract(a, kw):
    dfs = [d.fillna(0) for d in a] if kw["filter"] else a
    out = dfs[0]
    for d in dfs[1:]:
        out = out - d
    return out


def _multiply(a, kw):
    dfs = [d.fillna(0) for d in a] if kw["filter"] else a
    out = dfs[0]
    for d in dfs[1:]:
        out = out * d
    return out


def _divide(a, kw): return a[0] / a[1].replace(0, np.nan)
def _max_op(a, kw):
    out = a[0]
    for d in a[1:]:
        out = np.maximum(out, d)
    return out
def _min_op(a, kw):
    out = a[0]
    for d in a[1:]:
        out = np.minimum(out, d)
    return out


# ---------------------------------------------------------------------------
# Logical (1/0 convention, matching WQ)
# ---------------------------------------------------------------------------

def _and(a, kw): return _bool_to_float((a[0] != 0) & (a[1] != 0))
def _or(a, kw): return _bool_to_float((a[0] != 0) | (a[1] != 0))
def _not(a, kw): return _bool_to_float(a[0] == 0)
def _if_else(a, kw): return a[1].where(a[0] != 0, a[2])


# ---------------------------------------------------------------------------
# Cross-sectional
# ---------------------------------------------------------------------------

def _rank(a, kw):
    # NOTE: WQ's `rate` kwarg (tie/smoothing behavior) is accepted for
    # compatibility but not functionally implemented -- undocumented
    # exact semantics. Plain percentile rank always used.
    return a[0].rank(axis=1, pct=True)


def _zscore(a, kw):
    x = a[0]
    mean, std = x.mean(axis=1), x.std(axis=1)
    return x.sub(mean, axis=0).div(std.replace(0, np.nan), axis=0)


def _scale(a, kw):
    x = a[0]
    scale, longscale, shortscale = kw["scale"], kw["longscale"], kw["shortscale"]
    if longscale == 1 and shortscale == 1:
        # simple case: no long/short split requested
        denom = x.abs().sum(axis=1).replace(0, np.nan)
        return x.div(denom, axis=0) * scale
    pos = x.where(x > 0)
    neg = x.where(x < 0)
    pos_scaled = pos.div(pos.abs().sum(axis=1).replace(0, np.nan), axis=0) * longscale
    neg_scaled = neg.div(neg.abs().sum(axis=1).replace(0, np.nan), axis=0) * shortscale
    return pos_scaled.fillna(0) + neg_scaled.fillna(0)


def _normalize(a, kw):
    x = a[0]
    out = x.sub(x.mean(axis=1), axis=0)
    if kw["useStd"]:
        out = out.div(x.std(axis=1).replace(0, np.nan), axis=0)
    if kw["limit"] and kw["limit"] > 0:
        out = out.clip(lower=-kw["limit"], upper=kw["limit"])
    return out


def _winsorize(a, kw):
    x = a[0]
    mean, std = x.mean(axis=1), x.std(axis=1)
    lower = mean - kw["std"] * std
    upper = mean + kw["std"] * std
    return x.clip(lower=lower, upper=upper, axis=0)


# ---------------------------------------------------------------------------
# Time-series
# ---------------------------------------------------------------------------

def _ts_delay(a, kw): return a[0].shift(int(a[1]))
def _ts_delta(a, kw): return a[0] - a[0].shift(int(a[1]))
def _ts_mean(a, kw): return a[0].rolling(int(a[1]), min_periods=1).mean()
def _ts_sum(a, kw): return a[0].rolling(int(a[1]), min_periods=1).sum()
def _ts_product(a, kw):
    n = int(a[1])
    return a[0].rolling(n, min_periods=1).apply(np.prod, raw=True)
def _ts_std_dev(a, kw): return a[0].rolling(int(a[1]), min_periods=2).std()
def _ts_av_diff(a, kw): return a[0] - a[0].rolling(int(a[1]), min_periods=1).mean()


def _ts_zscore(a, kw):
    n = int(a[1])
    mean = a[0].rolling(n, min_periods=1).mean()
    std = a[0].rolling(n, min_periods=2).std()
    return (a[0] - mean) / std.replace(0, np.nan)


def _ts_rank(a, kw):
    n = int(a[1])
    def _roll_rank(s: pd.Series) -> pd.Series:
        return s.rolling(n, min_periods=2).apply(
            lambda w: pd.Series(w).rank(pct=True).iloc[-1], raw=False
        )
    return a[0].apply(_roll_rank, axis=0) + kw["constant"]


def _ts_corr(a, kw):
    n = int(a[2])
    return a[0].rolling(n, min_periods=2).corr(a[1])


def _ts_covariance(a, kw):
    # WQ signature is ts_covariance(y, x, d) -- args[0]=y, args[1]=x
    n = int(a[2])
    return a[0].rolling(n, min_periods=2).cov(a[1])


def _ts_decay_linear(a, kw):
    # NOTE: `dense` kwarg (NaN-handling mode) accepted but not
    # functionally different -- always treats missing values as 0 weight.
    n = int(a[1])
    weights = np.arange(1, n + 1, dtype=float)
    weights /= weights.sum()
    def _weighted(s: pd.Series) -> pd.Series:
        return s.rolling(n, min_periods=1).apply(
            lambda w: np.dot(w, weights[-len(w):]) / weights[-len(w):].sum(), raw=True
        )
    return a[0].apply(_weighted, axis=0)


def _ts_arg_extreme(a, kw, use_max: bool):
    n = int(a[1])
    fn = np.nanargmax if use_max else np.nanargmin
    def f(w):
        if np.all(np.isnan(w)):
            return np.nan
        return len(w) - 1 - fn(w)
    def _roll(s: pd.Series) -> pd.Series:
        return s.rolling(n, min_periods=1).apply(f, raw=True)
    return a[0].apply(_roll, axis=0)

def _ts_arg_max(a, kw): return _ts_arg_extreme(a, kw, use_max=True)
def _ts_arg_min(a, kw): return _ts_arg_extreme(a, kw, use_max=False)


def _ts_scale(a, kw):
    n = int(a[1])
    rmin = a[0].rolling(n, min_periods=1).min()
    rmax = a[0].rolling(n, min_periods=1).max()
    return (a[0] - rmin) / (rmax - rmin).replace(0, np.nan) + kw["constant"]


def _ts_step(a, kw, evaluator):
    n = a[0]  # literal number, 'int' arg_type
    ref = evaluator.ref
    counter = np.arange(1, len(ref.index) + 1) * n
    return pd.DataFrame(
        np.tile(counter.reshape(-1, 1), (1, len(ref.columns))),
        index=ref.index, columns=ref.columns,
    )


def _ts_count_nans(a, kw):
    n = int(a[1])
    return a[0].isna().rolling(n, min_periods=1).sum()


def _ts_backfill(a, kw):
    # NOTE: `k` (k-th most recent valid value) simplified to always k=1
    # (most recent valid value within the lookback window).
    return a[0].ffill(limit=int(kw["lookback"]))


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

REGISTRY: dict[str, OperatorSpec] = {
    # elementwise
    "abs": OperatorSpec(_abs, ("data",), description="Absolute value."),
    "log": OperatorSpec(_log, ("data",), description="Natural logarithm."),
    "sign": OperatorSpec(_sign, ("data",), description="+1/-1/0 sign of input."),
    "sqrt": OperatorSpec(_sqrt, ("data",), description="Non-negative square root."),
    "inverse": OperatorSpec(_inverse, ("data",), description="1 / x."),
    "reverse": OperatorSpec(_reverse, ("data",), description="Negation: -x."),
    "is_nan": OperatorSpec(_is_nan, ("data",), description="1 if x is NaN else 0."),
    "power": OperatorSpec(_power, ("data", "data"), description="x raised to power y."),
    "signed_power": OperatorSpec(_signed_power, ("data", "data"),
                                  description="x^y, preserving the sign of x."),

    # n-ary arithmetic
    "add": OperatorSpec(_add, None, min_args=2, kwargs={"filter": False},
                         description="Sum of 2+ inputs. filter=true treats NaN as 0."),
    "subtract": OperatorSpec(_subtract, None, min_args=2, kwargs={"filter": False},
                              description="Left-to-right subtraction of 2+ inputs."),
    "multiply": OperatorSpec(_multiply, None, min_args=2, kwargs={"filter": False},
                              description="Product of 2+ inputs. filter=true treats NaN as 0."),
    "divide": OperatorSpec(_divide, ("data", "data"), description="x / y."),
    "max": OperatorSpec(_max_op, None, min_args=2, description="Elementwise max of 2+ inputs."),
    "min": OperatorSpec(_min_op, None, min_args=2, description="Elementwise min of 2+ inputs."),

    # logical
    "and": OperatorSpec(_and, ("data", "data"), description="1 if both inputs nonzero, else 0."),
    "or": OperatorSpec(_or, ("data", "data"), description="1 if either input nonzero, else 0."),
    "not": OperatorSpec(_not, ("data",), description="Logical negation: 1 if x==0 else 0."),
    "if_else": OperatorSpec(_if_else, ("data", "data", "data"),
                             description="if_else(cond, a, b): a where cond!=0, else b."),

    # cross-sectional
    "rank": OperatorSpec(_rank, ("data",), kwargs={"rate": 2},
                          description="Cross-sectional percentile rank in [0,1]."),
    "zscore": OperatorSpec(_zscore, ("data",), description="Cross-sectional z-score."),
    "scale": OperatorSpec(_scale, ("data",), kwargs={"scale": 1.0, "longscale": 1.0, "shortscale": 1.0},
                           description="Scale so sum(|x|) == scale (or long/short book sizes separately)."),
    "normalize": OperatorSpec(_normalize, ("data",), kwargs={"useStd": False, "limit": 0.0},
                               description="Subtract cross-sectional mean; optionally divide by std and clip."),
    "winsorize": OperatorSpec(_winsorize, ("data",), kwargs={"std": 4.0},
                               description="Clip to mean +/- std*stdev cross-sectionally."),

    # time-series
    "ts_delay": OperatorSpec(_ts_delay, ("data", "int"), description="Value of x from d days ago."),
    "ts_delta": OperatorSpec(_ts_delta, ("data", "int"), description="x - ts_delay(x, d)."),
    "ts_mean": OperatorSpec(_ts_mean, ("data", "int"), description="Rolling mean over d days."),
    "ts_sum": OperatorSpec(_ts_sum, ("data", "int"), description="Rolling sum over d days."),
    "ts_product": OperatorSpec(_ts_product, ("data", "int"), description="Rolling product over d days."),
    "ts_std_dev": OperatorSpec(_ts_std_dev, ("data", "int"), description="Rolling standard deviation over d days."),
    "ts_av_diff": OperatorSpec(_ts_av_diff, ("data", "int"), description="x - ts_mean(x, d)."),
    "ts_zscore": OperatorSpec(_ts_zscore, ("data", "int"),
                               description="(x - ts_mean(x,d)) / ts_std_dev(x,d): time-series z-score."),
    "ts_rank": OperatorSpec(_ts_rank, ("data", "int"), kwargs={"constant": 0.0},
                             description="Rolling percentile rank of the latest value within its d-day window."),
    "ts_corr": OperatorSpec(_ts_corr, ("data", "data", "int"), description="Rolling Pearson correlation over d days."),
    "ts_covariance": OperatorSpec(_ts_covariance, ("data", "data", "int"),
                                   description="ts_covariance(y, x, d): rolling covariance over d days."),
    "ts_decay_linear": OperatorSpec(_ts_decay_linear, ("data", "int"), kwargs={"dense": False},
                                     description="Linearly-decayed weighted moving average over d days."),
    "ts_arg_max": OperatorSpec(_ts_arg_max, ("data", "int"),
                                description="Days since the max value within the last d days (0 = today)."),
    "ts_arg_min": OperatorSpec(_ts_arg_min, ("data", "int"),
                                description="Days since the min value within the last d days (0 = today)."),
    "ts_scale": OperatorSpec(_ts_scale, ("data", "int"), kwargs={"constant": 0.0},
                              description="Min-max scale x to [0,1] within its trailing d-day window."),
    "ts_count_nans": OperatorSpec(_ts_count_nans, ("data", "int"), description="Count of NaN values over the last d days."),
    "ts_backfill": OperatorSpec(_ts_backfill, ("data",), kwargs={"lookback": 5.0, "k": 1.0},
                                 description="Forward-fill NaN with the most recent valid value within `lookback` days."),
    "ts_step": OperatorSpec(None, ("int",), description="Counter of days, incrementing by n each day."),  # special-cased (needs evaluator ref)
}

# Common alternate spellings seen in academic/paper notation (e.g. the "101
# Formulaic Alphas" paper) that don't match our canonical registry names.
# Resolved case-insensitively: "Ts_ArgMax" and "ts_argmax" both map here.
ALIASES: dict[str, str] = {
    "stddev": "ts_std_dev",
    "std": "ts_std_dev",
    "delta": "ts_delta",
    "delay": "ts_delay",
    "correlation": "ts_corr",
    "covariance": "ts_covariance",
    "decay_linear": "ts_decay_linear",
    "signedpower": "signed_power",
    "ts_argmax": "ts_arg_max",
    "ts_argmin": "ts_arg_min",
    "argmax": "ts_arg_max",
    "argmin": "ts_arg_min",
    "sum": "ts_sum",
    "product": "ts_product",
    "mean": "ts_mean",
    "rank_": "rank",
}