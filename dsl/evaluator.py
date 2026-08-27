"""
dsl/evaluator.py
================
Walks an AST (dsl/parser.py) and computes it against panel data
(dict[str, pd.DataFrame], date x ticker). Every function call dispatches
through dsl.operators.REGISTRY -- the operator set is exactly and only
what's declared there (operators.json's list), nothing more.
"""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from dsl.parser import Number, Field, FuncCall, BinOp, UnaryNeg, Ternary, parse_expression
from dsl.operators import REGISTRY


class AlphaEvaluationError(ValueError):
    pass


_COMPARISON_OPS = {">", "<", "==", ">=", "<=", "!="}


class Evaluator:
    def __init__(self, panel: dict[str, pd.DataFrame]):
        self.panel = panel
        self.ref = next(iter(panel.values()))  # reference shape/index for scalar broadcasting

    def eval(self, node) -> pd.DataFrame:
        if isinstance(node, Number):
            return pd.DataFrame(node.value, index=self.ref.index, columns=self.ref.columns)

        if isinstance(node, Field):
            if node.name in self.panel:
                return self.panel[node.name]
            lowered = node.name.lower()
            if lowered in self.panel:
                return self.panel[lowered]
            raise AlphaEvaluationError(
                f"Unknown field {node.name!r}. Available fields: {sorted(self.panel)}"
            )

        if isinstance(node, UnaryNeg):
            return -self.eval(node.operand)

        if isinstance(node, Ternary):
            cond = self.eval(node.cond)
            true_val = self.eval(node.true_val)
            false_val = self.eval(node.false_val)
            return true_val.where(cond != 0, false_val)

        if isinstance(node, BinOp):
            return self._eval_binop(node)

        if isinstance(node, FuncCall):
            return self._eval_func(node)

        raise AlphaEvaluationError(f"Unknown AST node type: {type(node)}")

    def _eval_binop(self, node: BinOp) -> pd.DataFrame:
        left = self.eval(node.left)
        right = self.eval(node.right)
        if node.op == "+": return left + right
        if node.op == "-": return left - right
        if node.op == "*": return left * right
        if node.op == "/": return left / right.replace(0, np.nan)
        if node.op == "||":
            return ((left != 0) | (right != 0)).astype(float)
        if node.op in _COMPARISON_OPS:
            result = {
                ">": left > right, "<": left < right, "==": left == right,
                ">=": left >= right, "<=": left <= right, "!=": left != right,
            }[node.op]
            return result.astype(float)
        raise AlphaEvaluationError(f"Unknown binary operator {node.op!r}")

    def _eval_func(self, node: FuncCall) -> pd.DataFrame:
        name = node.name.lower()
        spec = REGISTRY.get(name)
        if spec is None:
            import difflib
            suggestion = difflib.get_close_matches(name, REGISTRY.keys(), n=1)
            hint = f" Did you mean {suggestion[0]!r}?" if suggestion else ""
            raise AlphaEvaluationError(
                f"Unknown function {node.name!r}.{hint} Available functions: {sorted(REGISTRY)}"
            )

        n_required = len(spec.arg_types)
        n_max = n_required + (1 if spec.optional_arg_type else 0)
        if not (n_required <= len(node.args) <= n_max):
            expected = f"{n_required}" if n_required == n_max else f"{n_required} to {n_max}"
            raise AlphaEvaluationError(
                f"{name}() expects {expected} argument(s), got {len(node.args)}"
            )

        resolved = []
        for i, typ in enumerate(spec.arg_types):
            arg_node = node.args[i]
            resolved.append(self.eval(arg_node) if typ == "data" else self._require_number(arg_node, name, i + 1))

        if len(node.args) > n_required:
            resolved.append(self._require_number(node.args[n_required], name, n_required + 1))
        elif spec.optional_arg_type is not None:
            resolved.append(spec.optional_arg_default)

        return spec.fn(resolved)

    @staticmethod
    def _require_number(node, func: str, pos: int) -> float:
        if not isinstance(node, Number):
            raise AlphaEvaluationError(
                f"{func}(): argument {pos} must be a numeric literal, got {type(node).__name__}"
            )
        return node.value


def evaluate_expression(expr_str: str, panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    ast = parse_expression(expr_str)
    return Evaluator(panel).eval(ast)


if __name__ == "__main__":
    from data_layer import generate_synthetic_data

    panel = generate_synthetic_data(["AAA", "BBB", "CCC", "DDD"], n_days=60)
    if "industry" not in panel:
        groups = ["group_a", "group_b", "group_a", "group_b"]  # one per ticker, static over time
        panel["industry"] = pd.DataFrame(
            [groups] * len(panel["close"].index),
            index=panel["close"].index, columns=panel["close"].columns,
        )

    handwritten_expressions = [
        "close",
        "rank(close)",
        "delta(close, 5)",
        "correlation(volume, close, 10)",
        "covariance(volume, close, 10)",
        "scale(close)",
        "scale(close, 2)",
        "signedpower(close - open, 0.5)",
        "decay_linear(returns, 10)",
        "indneutralize(returns, industry)",
        "ts_min(close, 10)",
        "ts_max(close, 10)",
        "min(close, 10)",
        "max(close, 10)",
        "sum(volume, 5)",
        "product(close, 3)",
        "stddev(returns, 20)",
        "close > open ? 1 : -1",
        "(close > open) || (volume > 0)",
        "-rank(delta(close, 1))",
    ]
    for expr in handwritten_expressions:
        result = evaluate_expression(expr, panel)
        assert result.shape == panel["close"].shape, f"shape mismatch for {expr}"
        print(f"OK  {expr:45s} last_row={result.dropna(how='all').tail(1).values.tolist()}")