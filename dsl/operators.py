"""
dsl/operators.py
=================
Operator registry STRICTLY limited to operators.json (the "101 Formulaic
Alphas" paper's own operator table). Every entry here corresponds to
exactly one row in that file -- nothing added, nothing from the broader
WorldQuant BRAIN platform operator set carried over.

Naming/semantics notes (paper's own conventions, not WQ platform's):
  - min(x,d) / max(x,d) are TIME-SERIES min/max (aliases of ts_min/ts_max),
    NOT an n-ary "smallest of several values" function.
  - sum(x,d), product(x,d), stddev(x,d) have no "ts_" prefix in the paper,
    despite being time-series operators -- kept as bare names to match.
  - scale(x, a) takes an OPTIONAL second positional arg (default a=1),
    not a keyword argument.
  - No add()/subtract()/multiply()/divide() functions exist in this set --
    arithmetic is only available via the raw +, -, *, / symbols (handled
    in the evaluator directly, not through this registry).
  - No kwargs anywhere in this operator set, so OperatorSpec carries none.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class OperatorSpec:
    fn: Callable
    arg_types: tuple            # e.g. ("data",) or ("data", "int")
    optional_arg_type: str | None = None     # at most one optional trailing positional arg
    optional_arg_default: float | None = None
    kwargs: dict = None          # unused in this operator set; kept only so external
                                  # code that introspects OperatorSpec.kwargs (e.g. a
                                  # prompt builder) doesn't break on a missing attribute
    description: str = ""

    def __post_init__(self):
        if self.kwargs is None:
            object.__setattr__(self, "kwargs", {})


# ---------------------------------------------------------------------------
# Elementwise
# ---------------------------------------------------------------------------

def _abs(a): return a[0].abs()
def _log(a): return np.log(a[0].clip(lower=1e-12))
def _sign(a): return np.sign(a[0])


# ---------------------------------------------------------------------------
# Cross-sectional
# ---------------------------------------------------------------------------

def _rank(a): return a[0].rank(axis=1, pct=True)


def _scale(a):
    x, target = a[0], a[1]
    denom = x.abs().sum(axis=1).replace(0, np.nan)
    return x.div(denom, axis=0) * target


# ---------------------------------------------------------------------------
# Time-series
# ---------------------------------------------------------------------------

def _delay(a): return a[0].shift(int(a[1]))
def _delta(a): return a[0] - a[0].shift(int(a[1]))
def _sum(a): return a[0].rolling(int(a[1]), min_periods=1).sum()
def _product(a): return a[0].rolling(int(a[1]), min_periods=1).apply(np.prod, raw=True)
def _stddev(a): return a[0].rolling(int(a[1]), min_periods=2).std()
def _ts_min(a): return a[0].rolling(int(a[1]), min_periods=1).min()
def _ts_max(a): return a[0].rolling(int(a[1]), min_periods=1).max()


def _ts_rank(a):
    n = int(a[1])
    def _roll_rank(s: pd.Series) -> pd.Series:
        return s.rolling(n, min_periods=2).apply(
            lambda w: pd.Series(w).rank(pct=True).iloc[-1], raw=False
        )
    return a[0].apply(_roll_rank, axis=0)


def _ts_arg_extreme(a, use_max: bool):
    # "which day ts_max/ts_min occurred on", counted as days SINCE that day
    # (0 = today). The paper doesn't pin down the exact indexing convention;
    # this matches the common WorldQuant-platform interpretation.
    n = int(a[1])
    fn = np.nanargmax if use_max else np.nanargmin
    def f(w):
        if np.all(np.isnan(w)):
            return np.nan
        return len(w) - 1 - fn(w)
    def _roll(s: pd.Series) -> pd.Series:
        return s.rolling(n, min_periods=1).apply(f, raw=True)
    return a[0].apply(_roll, axis=0)

def _ts_argmax(a): return _ts_arg_extreme(a, use_max=True)
def _ts_argmin(a): return _ts_arg_extreme(a, use_max=False)


def _correlation(a):
    n = int(a[2])
    return a[0].rolling(n, min_periods=2).corr(a[1])


def _covariance(a):
    n = int(a[2])
    return a[0].rolling(n, min_periods=2).cov(a[1])


def _signedpower(a):
    return np.sign(a[0]) * (a[0].abs() ** a[1])


def _decay_linear(a):
    # Paper says weights "d, d-1, ..., 1" without specifying which end of
    # the window each applies to. This follows the common WorldQuant-platform
    # convention: the MOST RECENT day gets the largest weight (d), the
    # oldest day in the window gets the smallest (1).
    n = int(a[1])
    weights = np.arange(1, n + 1, dtype=float)  # oldest -> 1, most recent -> d
    weights /= weights.sum()
    def _weighted(s: pd.Series) -> pd.Series:
        return s.rolling(n, min_periods=1).apply(
            lambda w: np.dot(w, weights[-len(w):]) / weights[-len(w):].sum(), raw=True
        )
    return a[0].apply(_weighted, axis=0)


# ---------------------------------------------------------------------------
# Group (indneutralize)
# ---------------------------------------------------------------------------

def _indneutralize(a):
    x, group = a
    df = pd.DataFrame({"x": x.stack(), "g": group.stack()})
    df["date"] = df.index.get_level_values(0)
    grp_mean = df.groupby(["date", "g"])["x"].transform("mean")
    return (df["x"] - grp_mean).unstack()


# ---------------------------------------------------------------------------
# Registry -- one entry per row in operators.json
# ---------------------------------------------------------------------------

REGISTRY: dict[str, OperatorSpec] = {
    "abs": OperatorSpec(_abs, ("data",), description="Absolute value."),
    "log": OperatorSpec(_log, ("data",), description="Natural logarithm."),
    "sign": OperatorSpec(_sign, ("data",), description="+1/-1/0 sign of input."),

    "rank": OperatorSpec(_rank, ("data",), description="Cross-sectional rank."),
    "scale": OperatorSpec(_scale, ("data",), optional_arg_type="float", optional_arg_default=1.0,
                           description="Rescale x so sum(abs(x)) == a (default a=1)."),

    "delay": OperatorSpec(_delay, ("data", "int"), description="Value of x d days ago."),
    "delta": OperatorSpec(_delta, ("data", "int"), description="Today's x minus x d days ago."),
    "correlation": OperatorSpec(_correlation, ("data", "data", "int"),
                                 description="Time-serial correlation of x and y over the past d days."),
    "covariance": OperatorSpec(_covariance, ("data", "data", "int"),
                                description="Time-serial covariance of x and y over the past d days."),
    "signedpower": OperatorSpec(_signedpower, ("data", "data"), description="x^a, preserving the sign of x."),
    "decay_linear": OperatorSpec(_decay_linear, ("data", "int"),
                                  description="Weighted moving average over d days with linearly decaying weights."),
    "indneutralize": OperatorSpec(_indneutralize, ("data", "data"),
                                   description="x cross-sectionally demeaned within each group g."),

    "ts_min": OperatorSpec(_ts_min, ("data", "int"), description="Time-series min over the past d days."),
    "ts_max": OperatorSpec(_ts_max, ("data", "int"), description="Time-series max over the past d days."),
    "ts_argmax": OperatorSpec(_ts_argmax, ("data", "int"), description="Which day ts_max(x,d) occurred on."),
    "ts_argmin": OperatorSpec(_ts_argmin, ("data", "int"), description="Which day ts_min(x,d) occurred on."),
    "ts_rank": OperatorSpec(_ts_rank, ("data", "int"), description="Time-series rank over the past d days."),

    # bare-name aliases, exactly as documented in operators.json
    "min": OperatorSpec(_ts_min, ("data", "int"), description="Alias of ts_min(x, d)."),
    "max": OperatorSpec(_ts_max, ("data", "int"), description="Alias of ts_max(x, d)."),
    "sum": OperatorSpec(_sum, ("data", "int"), description="Time-series sum over the past d days."),
    "product": OperatorSpec(_product, ("data", "int"), description="Time-series product over the past d days."),
    "stddev": OperatorSpec(_stddev, ("data", "int"), description="Moving time-series standard deviation over d days."),
}