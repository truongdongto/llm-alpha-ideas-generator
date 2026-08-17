"""
data_layer.py
=============
Responsibility: fetch raw OHLCV data and turn it into "panel" format,
which is the data structure the DSL evaluator consumes.

Panel format:
    A dict[str, pd.DataFrame] where each DataFrame has:
        index   = dates
        columns = tickers
        values  = the field's value (e.g. close price) for that ticker/date

This is the same shape WorldQuant BRAIN / most alpha research platforms use:
it makes cross-sectional operators (rank across tickers on a given date) and
time-series operators (rolling window down a column) both trivial to express
with pandas.

Two ways to get data:
    1. fetch_real_data(...)  -> uses yfinance, needs internet access to
       Yahoo Finance.
    2. generate_synthetic_data(...) -> pure numpy random walk, no internet
       needed. Use this to test the DSL parser/evaluator in isolation
       (e.g. in a sandboxed environment) before wiring up real data.

Both return the exact same panel dict shape, so everything downstream
(parser, evaluator, backtest engine) is agnostic to which one you used.
"""

from __future__ import annotations
import numpy as np
import pandas as pd

# Fields every alpha expression is allowed to reference.
BASE_FIELDS = ["open", "high", "low", "close", "volume"]
DERIVED_FIELDS = ["returns", "vwap", "adv20"]
ALL_FIELDS = BASE_FIELDS + DERIVED_FIELDS


def _add_derived_fields(panel: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Compute returns, vwap, adv20 from the base OHLCV panel."""
    close = panel["close"]
    volume = panel["volume"]
    high, low, open_ = panel["high"], panel["low"], panel["open"]

    panel["returns"] = close.pct_change()
    # crude vwap proxy since we don't have intraday data: typical price
    panel["vwap"] = (high + low + close) / 3.0
    # 20-day average daily volume, common normalizer in alpha expressions
    panel["adv20"] = volume.rolling(20, min_periods=1).mean()
    return panel


def fetch_real_data(
    tickers: list[str],
    start: str = "2018-01-01",
    end: str | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Fetch real OHLCV data via yfinance and reshape into panel format.
    """
    import yfinance as yf

    raw = yf.download(tickers, start=start, end=end, group_by="ticker",
                       auto_adjust=True, progress=False)

    panel: dict[str, pd.DataFrame] = {}
    for field in BASE_FIELDS:
        col_name = field.capitalize()
        if len(tickers) == 1:
            panel[field] = raw[[col_name]].rename(columns={col_name: tickers[0]})
        else:
            panel[field] = pd.concat(
                {t: raw[t][col_name] for t in tickers if t in raw.columns.levels[0]},
                axis=1,
            )

    return _add_derived_fields(panel)


def generate_synthetic_data(
    tickers: list[str],
    n_days: int = 500,
    seed: int = 42,
) -> dict[str, pd.DataFrame]:
    """
    Generate synthetic OHLCV panel data via geometric-brownian-motion-like
    random walks. No internet needed -- use this to test the DSL parser
    and evaluator end to end before hooking up real market data.

    NOTE: the synthetic prices have no real predictive structure, so any
    "alpha" you backtest against this data is meaningless for actual
    trading -- it only proves the pipeline is wired correctly.
    """
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2022-01-03", periods=n_days)

    close = pd.DataFrame(index=dates, columns=tickers, dtype=float)
    for t in tickers:
        drift = rng.normal(0.0002, 0.0001)
        vol = rng.uniform(0.01, 0.03)
        shocks = rng.normal(drift, vol, size=n_days)
        close[t] = 100 * np.exp(np.cumsum(shocks))

    # derive open/high/low from close with small random offsets
    noise = lambda scale: pd.DataFrame(
        rng.normal(1.0, scale, size=close.shape), index=dates, columns=tickers
    )
    jitter = lambda scale: pd.DataFrame(
        rng.uniform(0.0, scale, size=close.shape), index=dates, columns=tickers
    )
    open_ = close.shift(1).fillna(close.iloc[0]) * noise(0.003)
    # high/low are the max/min of open & close, nudged a bit further out
    # so high >= max(open, close) and low <= min(open, close) always hold.
    high = np.maximum(open_, close) * (1 + jitter(0.01))
    low = np.minimum(open_, close) * (1 - jitter(0.01))

    volume = pd.DataFrame(
        rng.integers(1_000_000, 20_000_000, size=close.shape),
        index=dates, columns=tickers,
    ).astype(float)

    panel = {"open": open_, "high": high, "low": low, "close": close, "volume": volume}
    return _add_derived_fields(panel)


def save_panel(panel: dict[str, pd.DataFrame], path: str) -> None:
    """Persist panel dict to a single Parquet file (long format)."""
    frames = []
    for field, df in panel.items():
        long = df.stack().rename(field).reset_index()
        long.columns = ["date", "ticker", field]
        frames.append(long.set_index(["date", "ticker"]))
    combined = pd.concat(frames, axis=1).reset_index()
    combined.to_parquet(path, index=False)


def load_panel(path: str) -> dict[str, pd.DataFrame]:
    """Load a Parquet file saved by save_panel back into panel dict format."""
    long = pd.read_parquet(path)
    fields = [c for c in long.columns if c not in ("date", "ticker")]
    panel = {}
    for field in fields:
        panel[field] = long.pivot(index="date", columns="ticker", values=field)
    return panel


if __name__ == "__main__":
    # quick smoke test
    tickers = ["AAA", "BBB", "CCC", "DDD"]
    panel = generate_synthetic_data(tickers, n_days=100)
    for field, df in panel.items():
        print(f"{field:10s} shape={df.shape}  sample_last_row=\n{df.tail(1)}\n")

    datas = fetch_real_data(tickers)
    print(datas)

    save_panel(panel, "/tmp/synthetic_panel.parquet")
    reloaded = load_panel("/tmp/synthetic_panel.parquet")
    assert set(reloaded.keys()) == set(panel.keys())
    assert np.allclose(reloaded["close"].values, panel["close"].values, equal_nan=True)
    print("save/load round-trip OK")