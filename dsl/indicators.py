"""
dsl/indicators.py
===================
Standard technical indicators, registered as DSL operators so they can be
composed inside alpha expressions (e.g. rank(rsi(close, 14) - 50)).

All are computed per-ticker (columns), independently -- i.e. these are
ordinary time-series operators just like ts_mean/ts_std_dev, applied
column-wise via DataFrame.apply. Standard textbook formulas (Wilder's
smoothing for RSI/ATR/ADX, EMA-based MACD) are used; where a formula has
multiple common conventions, the choice is noted in the description.
"""

from __future__ import annotations
import numpy as np
import pandas as pd

from dsl.operators import OperatorSpec


def _ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False, min_periods=1).mean()


def _wilder_smooth(s: pd.Series, period: int) -> pd.Series:
    return s.ewm(alpha=1 / period, adjust=False, min_periods=1).mean()


# ---------------------------------------------------------------------------
# Moving averages
# ---------------------------------------------------------------------------

def _sma(a, kw):
    return a[0].rolling(int(a[1]), min_periods=1).mean()

def _ema_op(a, kw):
    n = int(a[1])
    return a[0].apply(lambda col: _ema(col, n), axis=0)


# ---------------------------------------------------------------------------
# RSI (Wilder's original formula)
# ---------------------------------------------------------------------------

def _rsi_col(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = _wilder_smooth(gain, period)
    avg_loss = _wilder_smooth(loss, period)
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def _rsi(a, kw):
    return a[0].apply(lambda col: _rsi_col(col, int(a[1])), axis=0)


# ---------------------------------------------------------------------------
# MACD (line, signal, histogram)
# ---------------------------------------------------------------------------

def _macd_line(a, kw):
    x, fast, slow = a[0], int(a[1]), int(a[2])
    return x.apply(lambda col: _ema(col, fast) - _ema(col, slow), axis=0)

def _macd_signal(a, kw):
    x, fast, slow, signal = a[0], int(a[1]), int(a[2]), int(a[3])
    line = x.apply(lambda col: _ema(col, fast) - _ema(col, slow), axis=0)
    return line.apply(lambda col: _ema(col, signal), axis=0)

def _macd_hist(a, kw):
    x, fast, slow, signal = a[0], int(a[1]), int(a[2]), int(a[3])
    line = x.apply(lambda col: _ema(col, fast) - _ema(col, slow), axis=0)
    sig = line.apply(lambda col: _ema(col, signal), axis=0)
    return line - sig


# ---------------------------------------------------------------------------
# Bollinger Bands
# ---------------------------------------------------------------------------

def _bollinger_mid(a, kw):
    return a[0].rolling(int(a[1]), min_periods=1).mean()

def _bollinger_upper(a, kw):
    n = int(a[1])
    mid = a[0].rolling(n, min_periods=1).mean()
    std = a[0].rolling(n, min_periods=2).std()
    return mid + kw["num_std"] * std

def _bollinger_lower(a, kw):
    n = int(a[1])
    mid = a[0].rolling(n, min_periods=1).mean()
    std = a[0].rolling(n, min_periods=2).std()
    return mid - kw["num_std"] * std

def _bollinger_width(a, kw):
    n = int(a[1])
    mid = a[0].rolling(n, min_periods=1).mean().replace(0, np.nan)
    std = a[0].rolling(n, min_periods=2).std()
    return (2 * kw["num_std"] * std) / mid


# ---------------------------------------------------------------------------
# ATR (Wilder's Average True Range)
# ---------------------------------------------------------------------------

def _true_range(high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    prev_close = close.shift(1)
    tr1 = high - low
    # tr2/tr3 are NaN on day 1 (no prev_close yet); np.maximum would
    # propagate that NaN instead of falling back to tr1, so mask with -inf
    # (never wins the max, never poisons it) to match the standard
    # convention where day-1 true range is just high-low.
    tr2 = (high - prev_close).abs().fillna(-np.inf)
    tr3 = (low - prev_close).abs().fillna(-np.inf)
    return np.maximum(np.maximum(tr1, tr2), tr3)

def _atr(a, kw):
    high, low, close, period = a[0], a[1], a[2], int(a[3])
    tr = _true_range(high, low, close)
    return tr.apply(lambda col: _wilder_smooth(col, period), axis=0)


# ---------------------------------------------------------------------------
# Stochastic Oscillator (%K, %D)
# ---------------------------------------------------------------------------

def _stoch_k(a, kw):
    high, low, close, period = a[0], a[1], a[2], int(a[3])
    lowest = low.rolling(period, min_periods=1).min()
    highest = high.rolling(period, min_periods=1).max()
    return 100 * (close - lowest) / (highest - lowest).replace(0, np.nan)

def _stoch_d(a, kw):
    k = _stoch_k(a, kw)
    return k.rolling(int(kw["smooth"]), min_periods=1).mean()


# ---------------------------------------------------------------------------
# Williams %R
# ---------------------------------------------------------------------------

def _williams_r(a, kw):
    high, low, close, period = a[0], a[1], a[2], int(a[3])
    highest = high.rolling(period, min_periods=1).max()
    lowest = low.rolling(period, min_periods=1).min()
    return -100 * (highest - close) / (highest - lowest).replace(0, np.nan)


# ---------------------------------------------------------------------------
# CCI (Commodity Channel Index)
# ---------------------------------------------------------------------------

def _cci(a, kw):
    high, low, close, period = a[0], a[1], a[2], int(a[3])
    typical = (high + low + close) / 3
    sma = typical.rolling(period, min_periods=1).mean()
    mad = typical.rolling(period, min_periods=1).apply(lambda w: np.mean(np.abs(w - w.mean())), raw=True)
    return (typical - sma) / (0.015 * mad.replace(0, np.nan))


# ---------------------------------------------------------------------------
# OBV (On-Balance Volume)
# ---------------------------------------------------------------------------

def _obv(a, kw):
    close, volume = a
    direction = np.sign(close.diff().fillna(0))
    return (direction * volume).cumsum()


# ---------------------------------------------------------------------------
# ADX (Average Directional Index, Wilder's formula)
# ---------------------------------------------------------------------------

def _adx_col(high, low, close, period):
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_dm = pd.Series(plus_dm, index=high.index)
    minus_dm = pd.Series(minus_dm, index=high.index)

    tr = _true_range(high.to_frame(), low.to_frame(), close.to_frame()).iloc[:, 0]
    atr = _wilder_smooth(tr, period)
    plus_di = 100 * _wilder_smooth(plus_dm, period) / atr.replace(0, np.nan)
    minus_di = 100 * _wilder_smooth(minus_dm, period) / atr.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return _wilder_smooth(dx, period)

def _adx(a, kw):
    high, low, close, period = a[0], a[1], a[2], int(a[3])
    out = pd.DataFrame(index=high.index, columns=high.columns, dtype=float)
    for col in high.columns:
        out[col] = _adx_col(high[col], low[col], close[col], period)
    return out


# ---------------------------------------------------------------------------
# Ichimoku Cloud
# ---------------------------------------------------------------------------

def _ichimoku_line(high, low, period):
    return (high.rolling(period, min_periods=1).max() + low.rolling(period, min_periods=1).min()) / 2

def _ichimoku_tenkan(a, kw):  # conversion line, default period 9
    return _ichimoku_line(a[0], a[1], int(a[2]))

def _ichimoku_kijun(a, kw):  # base line, default period 26
    return _ichimoku_line(a[0], a[1], int(a[2]))

def _ichimoku_senkou_a(a, kw):  # leading span A: avg(tenkan, kijun)
    high, low, tenkan_period, kijun_period = a[0], a[1], int(a[2]), int(a[3])
    tenkan = _ichimoku_line(high, low, tenkan_period)
    kijun = _ichimoku_line(high, low, kijun_period)
    return (tenkan + kijun) / 2

def _ichimoku_senkou_b(a, kw):  # leading span B, default period 52
    return _ichimoku_line(a[0], a[1], int(a[2]))

def _ichimoku_chikou(a, kw):  # lagging span: close shifted back `period` days
    return a[0].shift(-int(a[1]))


INDICATOR_REGISTRY: dict[str, OperatorSpec] = {
    "sma": OperatorSpec(_sma, ("data", "int"), description="Simple moving average over d days."),
    "ema": OperatorSpec(_ema_op, ("data", "int"), description="Exponential moving average, span=d."),
    "rsi": OperatorSpec(_rsi, ("data", "int"), description="Relative Strength Index (Wilder's smoothing), 0-100."),
    "macd_line": OperatorSpec(_macd_line, ("data", "int", "int"),
                               description="macd_line(x, fast, slow): EMA(fast) - EMA(slow)."),
    "macd_signal": OperatorSpec(_macd_signal, ("data", "int", "int", "int"),
                                 description="macd_signal(x, fast, slow, signal): EMA(signal) of the MACD line."),
    "macd_hist": OperatorSpec(_macd_hist, ("data", "int", "int", "int"),
                               description="macd_hist(x, fast, slow, signal): MACD line minus its signal line."),
    "bollinger_mid": OperatorSpec(_bollinger_mid, ("data", "int"), description="Bollinger middle band: SMA(x, d)."),
    "bollinger_upper": OperatorSpec(_bollinger_upper, ("data", "int"), kwargs={"num_std": 2.0},
                                     description="Bollinger upper band: SMA + num_std * rolling std."),
    "bollinger_lower": OperatorSpec(_bollinger_lower, ("data", "int"), kwargs={"num_std": 2.0},
                                     description="Bollinger lower band: SMA - num_std * rolling std."),
    "bollinger_width": OperatorSpec(_bollinger_width, ("data", "int"), kwargs={"num_std": 2.0},
                                     description="Bollinger band width normalized by the middle band."),
    "atr": OperatorSpec(_atr, ("data", "data", "data", "int"),
                         description="atr(high, low, close, d): Wilder's Average True Range."),
    "stoch_k": OperatorSpec(_stoch_k, ("data", "data", "data", "int"),
                             description="stoch_k(high, low, close, d): Stochastic %K, 0-100."),
    "stoch_d": OperatorSpec(_stoch_d, ("data", "data", "data", "int"), kwargs={"smooth": 3.0},
                             description="stoch_d(high, low, close, d): SMA(%K, smooth) -- the %D signal line."),
    "williams_r": OperatorSpec(_williams_r, ("data", "data", "data", "int"),
                                description="williams_r(high, low, close, d): Williams %R, -100 to 0."),
    "cci": OperatorSpec(_cci, ("data", "data", "data", "int"),
                         description="cci(high, low, close, d): Commodity Channel Index."),
    "obv": OperatorSpec(_obv, ("data", "data"), description="obv(close, volume): On-Balance Volume (cumulative)."),
    "adx": OperatorSpec(_adx, ("data", "data", "data", "int"),
                         description="adx(high, low, close, d): Average Directional Index (trend strength, Wilder's)."),
    "ichimoku_tenkan": OperatorSpec(_ichimoku_tenkan, ("data", "data", "int"),
                                     description="ichimoku_tenkan(high, low, d): Conversion line, typically d=9."),
    "ichimoku_kijun": OperatorSpec(_ichimoku_kijun, ("data", "data", "int"),
                                    description="ichimoku_kijun(high, low, d): Base line, typically d=26."),
    "ichimoku_senkou_a": OperatorSpec(_ichimoku_senkou_a, ("data", "data", "int", "int"),
                                       description="ichimoku_senkou_a(high, low, tenkan_d, kijun_d): Leading span A "
                                                    "(NOTE: not shifted forward 26 days as platforms typically plot it)."),
    "ichimoku_senkou_b": OperatorSpec(_ichimoku_senkou_b, ("data", "data", "int"),
                                       description="ichimoku_senkou_b(high, low, d): Leading span B, typically d=52."),
    "ichimoku_chikou": OperatorSpec(_ichimoku_chikou, ("data", "int"),
                                     description="ichimoku_chikou(close, d): Lagging span, typically d=26. CAUTION: "
                                                  "this looks BACKWARD (shift(-d) moves future data into the past "
                                                  "index) -- do not use as a live predictive signal without care, "
                                                  "it is a charting convention, not a forecast."),
}