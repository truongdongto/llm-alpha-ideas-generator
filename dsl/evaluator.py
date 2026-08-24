"""
dsl/evaluator.py
================
This is where the alpha operators live. Two families:

  Cross-sectional operators (operate ACROSS tickers, on a single date):
      rank(x)      -> percentile rank of x among all tickers, per date
      zscore(x)    -> (x - mean) / std across tickers, per date
      scale(x)     -> x scaled so sum(|x|) == 1 across tickers, per date

  Time-series operators (operate DOWN the date axis, per ticker):
      ts_delta(x, n)   -> x - x shifted n days back
      ts_mean(x, n)    -> rolling mean over n days
      ts_std(x, n)     -> rolling std over n days
      ts_rank(x, n)    -> rolling percentile rank of the latest value in
                          its trailing n-day window
      ts_corr(x, y, n) -> rolling correlation between two fields over n days
      decay_linear(x,n)-> weighted moving average with linearly decaying
                          weights (most recent day weighted highest) --
                          a very common "smoothing" operator in alpha research

  Elementwise:
      log(x), abs(x), sign(x)
"""

from __future__ import annotations
import numpy as np
import pandas as pd

from .parser import Number, Field, FuncCall, BinOp, UnaryNeg, parse_expression


class AlphaEvaluationError(ValueError):
    """Raised for semantic errors: unknown field, wrong arg count, etc."""

    
# ---------------------------------------------------------------------------
# Operator implementations
# ---------------------------------------------------------------------------

def _rank(x: pd.DataFrame) -> pd.DataFrame:
    return x.rank(axis=1, pct=True)


def _zscore(x: pd.DataFrame) -> pd.DataFrame:
    mean = x.mean(axis=1)
    std = x.std(axis=1)
    return x.sub(mean, axis=0).div(std.replace(0, np.nan), axis=0)


def _scale(x: pd.DataFrame) -> pd.DataFrame:
    denom = x.abs().sum(axis=1).replace(0, np.nan)
    return x.div(denom, axis=0)


def _ts_delta(x: pd.DataFrame, n: float) -> pd.DataFrame:
    return x - x.shift(int(n))


def _ts_mean(x: pd.DataFrame, n: float) -> pd.DataFrame:
    return x.rolling(int(n), min_periods=1).mean()


def _ts_std(x: pd.DataFrame, n: float) -> pd.DataFrame:
    return x.rolling(int(n), min_periods=2).std()


def _ts_rank(x: pd.DataFrame, n: float) -> pd.DataFrame:
    n = int(n)
    # percentile rank of the LAST value within its trailing n-day window,
    # computed independently per ticker column
    def _roll_rank(s: pd.Series) -> pd.Series:
        return s.rolling(n, min_periods=2).apply(
            lambda w: pd.Series(w).rank(pct=True).iloc[-1], raw=False
        )
    return x.apply(_roll_rank, axis=0)


def _ts_corr(x: pd.DataFrame, y: pd.DataFrame, n: float) -> pd.DataFrame:
    n = int(n)
    return x.rolling(n, min_periods=2).corr(y)


def _decay_linear(x: pd.DataFrame, n: float) -> pd.DataFrame:
    n = int(n)
    weights = np.arange(1, n + 1, dtype=float)  # oldest->smallest, newest->largest
    weights /= weights.sum()

    def _weighted(s: pd.Series) -> pd.Series:
        return s.rolling(n, min_periods=1).apply(
            lambda w: np.dot(w, weights[-len(w):]) / weights[-len(w):].sum(),
            raw=True,
        )
    return x.apply(_weighted, axis=0)


_CROSS_SECTIONAL_UNARY = {"rank": _rank, "zscore": _zscore, "scale": _scale}
_TS_UNARY = {"ts_delta": _ts_delta, "ts_mean": _ts_mean, "ts_std": _ts_std,
             "ts_rank": _ts_rank, "decay_linear": _decay_linear}
_ELEMENTWISE_UNARY = {"log": lambda x: np.log(x.clip(lower=1e-12)),
                       "abs": lambda x: x.abs(),
                       "sign": lambda x: np.sign(x)}
_TS_BINARY = {"ts_corr": _ts_corr}


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

class Evaluator:
    """
    Evaluates an AST against a fixed panel dataset.

    Usage:
        panel = {"close": df_close, "volume": df_volume, ...}
        ev = Evaluator(panel)
        result_df = ev.eval(parse_expression("rank(ts_delta(close, 5))"))
    """

    def __init__(self, panel: dict[str, pd.DataFrame]):
        self.panel = panel
        # all field DataFrames share the same index/columns; use one as reference
        self._ref = next(iter(panel.values()))

    def eval(self, node) -> pd.DataFrame:
        if isinstance(node, Number):
            # broadcast a scalar into a full DataFrame so it composes with
            # binary ops the same way a field does
            return pd.DataFrame(node.value, index=self._ref.index, columns=self._ref.columns)

        if isinstance(node, Field):
            if node.name not in self.panel:
                raise AlphaEvaluationError(
                    f"Unknown field {node.name!r}. Available fields: {sorted(self.panel)}"
                )
            return self.panel[node.name]

        if isinstance(node, UnaryNeg):
            return -self.eval(node.operand)

        if isinstance(node, BinOp):
            left = self.eval(node.left)
            right = self.eval(node.right)
            if node.op == "+":
                return left + right
            if node.op == "-":
                return left - right
            if node.op == "*":
                return left * right
            if node.op == "/":
                return left / right.replace(0, np.nan)
            raise AlphaEvaluationError(f"Unknown binary operator {node.op!r}")

        if isinstance(node, FuncCall):
            return self._eval_func(node)

        raise AlphaEvaluationError(f"Unknown AST node type: {type(node)}")

    def _eval_func(self, node: FuncCall) -> pd.DataFrame:
        name, args = node.name, node.args

        if name in _CROSS_SECTIONAL_UNARY:
            self._check_arity(name, args, 1)
            return _CROSS_SECTIONAL_UNARY[name](self.eval(args[0]))

        if name in _ELEMENTWISE_UNARY:
            self._check_arity(name, args, 1)
            return _ELEMENTWISE_UNARY[name](self.eval(args[0]))

        if name in _TS_UNARY:
            self._check_arity(name, args, 2)
            x = self.eval(args[0])
            n = self._require_number(args[1], func=name, pos=2)
            return _TS_UNARY[name](x, n)

        if name in _TS_BINARY:
            self._check_arity(name, args, 3)
            x = self.eval(args[0])
            y = self.eval(args[1])
            n = self._require_number(args[2], func=name, pos=3)
            return _TS_BINARY[name](x, y, n)

        raise AlphaEvaluationError(
            f"Unknown function {name!r}. Available functions: "
            f"{sorted(list(_CROSS_SECTIONAL_UNARY) + list(_ELEMENTWISE_UNARY) + list(_TS_UNARY) + list(_TS_BINARY))}"
        )

    @staticmethod
    def _check_arity(name: str, args: tuple, expected: int) -> None:
        if len(args) != expected:
            raise AlphaEvaluationError(
                f"{name}() expects {expected} argument(s), got {len(args)}"
            )

    @staticmethod
    def _require_number(node, func: str, pos: int) -> float:
        if not isinstance(node, Number):
            raise AlphaEvaluationError(
                f"{func}(): argument {pos} must be a numeric literal (window size), "
                f"got {type(node).__name__}"
            )
        return node.value


def evaluate_expression(expr_str: str, panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Convenience one-shot: parse + evaluate a string against panel data."""
    ast = parse_expression(expr_str)
    return Evaluator(panel).eval(ast)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from data_layer import generate_synthetic_data

    panel = generate_synthetic_data(["AAA", "BBB", "CCC", "DDD"], n_days=60)

    handwritten_expressions = [
        "close",
        "rank(close)",
        "ts_delta(close, 5)",
        "ts_mean(close, 10)",
        "rank(ts_delta(close, 5) / ts_std(returns, 20))",
        "decay_linear(returns, 5)",
        "ts_corr(volume, close, 10)",
        "zscore(volume) - zscore(adv20)",
        "-rank(close - open) * 2",
        "log(volume)",
    ]

    for expr in handwritten_expressions:
        result = evaluate_expression(expr, panel)
        assert result.shape == panel["close"].shape, f"shape mismatch for {expr}"
        last_valid = result.dropna(how="all").tail(1)
        print(f"OK  {expr:55s} last_row=\n{last_valid}\n")

    # semantic error cases -- should raise cleanly, not crash with a traceback
    for bad_expr in ["unknown_field + 1", "rank(close, 5)", "ts_delta(close, returns)"]:
        try:
            evaluate_expression(bad_expr, panel)
            print(f"FAIL should have raised for: {bad_expr}")
        except AlphaEvaluationError as e:
            print(f"OK  correctly rejected {bad_expr!r}: {e}")