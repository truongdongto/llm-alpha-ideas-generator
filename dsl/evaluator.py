"""
dsl/evaluator.py
================
Walks an AST (dsl/parser.py) and computes it against panel data
(dict[str, pd.DataFrame], date x ticker). Function calls are dispatched
generically through dsl.operators.REGISTRY -- adding a new operator only
requires adding one entry there, not touching this file.
"""

from __future__ import annotations
import difflib
import numpy as np
import pandas as pd

from dsl.parser import Number, Boolean, Field, FuncCall, BinOp, UnaryNeg, parse_expression
from dsl.operators import REGISTRY, ALIASES


class AlphaEvaluationError(ValueError):
    pass


_COMPARISON_OPS = {"<", "<=", ">", ">=", "==", "!="}


class Evaluator:
    def __init__(self, panel: dict[str, pd.DataFrame]):
        self.panel = panel
        self.ref = next(iter(panel.values()))  # reference shape/index for scalars

    def eval(self, node) -> pd.DataFrame:
        if isinstance(node, Number):
            return pd.DataFrame(node.value, index=self.ref.index, columns=self.ref.columns)

        if isinstance(node, Boolean):
            return pd.DataFrame(float(node.value), index=self.ref.index, columns=self.ref.columns)

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
        if node.op in _COMPARISON_OPS:
            result = {
                "<": left < right, "<=": left <= right,
                ">": left > right, ">=": left >= right,
                "==": left == right, "!=": left != right,
            }[node.op]
            return result.astype(float)
        raise AlphaEvaluationError(f"Unknown binary operator {node.op!r}")

    def _eval_func(self, node: FuncCall) -> pd.DataFrame:
        raw_name = node.name
        name = ALIASES.get(raw_name.lower(), raw_name.lower())
        spec = REGISTRY.get(name)
        if spec is None:
            suggestion = difflib.get_close_matches(name, REGISTRY.keys(), n=1)
            hint = f" Did you mean {suggestion[0]!r}?" if suggestion else ""
            raise AlphaEvaluationError(
                f"Unknown function {raw_name!r}.{hint} Available functions: {sorted(REGISTRY)}"
            )

        # resolve positional args
        if spec.arg_types is not None:
            if len(node.pos_args) != len(spec.arg_types):
                raise AlphaEvaluationError(
                    f"{name}() expects {len(spec.arg_types)} positional arg(s), got {len(node.pos_args)}"
                )
            resolved = [
                self.eval(arg_node) if typ == "data" else self._require_number(arg_node, name, i + 1)
                for i, (typ, arg_node) in enumerate(zip(spec.arg_types, node.pos_args))
            ]
        else:
            if len(node.pos_args) < spec.min_args:
                raise AlphaEvaluationError(
                    f"{name}() expects at least {spec.min_args} arg(s), got {len(node.pos_args)}"
                )
            resolved = [self.eval(arg_node) for arg_node in node.pos_args]

        # resolve keyword args
        unknown_kwargs = set(node.kwargs) - set(spec.kwargs)
        if unknown_kwargs:
            raise AlphaEvaluationError(
                f"{name}() got unknown keyword argument(s) {sorted(unknown_kwargs)}. "
                f"Allowed: {sorted(spec.kwargs)}"
            )
        resolved_kwargs = {}
        for key, default in spec.kwargs.items():
            if key in node.kwargs:
                resolved_kwargs[key] = self._literal_value(node.kwargs[key], name, key)
            else:
                resolved_kwargs[key] = default

        if name == "ts_step":  # only operator needing the evaluator's reference shape
            from dsl.operators import _ts_step
            return _ts_step(resolved, resolved_kwargs, self)

        return spec.fn(resolved, resolved_kwargs)

    @staticmethod
    def _require_number(node, func: str, pos: int) -> float:
        if not isinstance(node, Number):
            raise AlphaEvaluationError(
                f"{func}(): argument {pos} must be a numeric literal, got {type(node).__name__}"
            )
        return node.value

    @staticmethod
    def _literal_value(node, func: str, key: str):
        if isinstance(node, Number):
            return node.value
        if isinstance(node, Boolean):
            return node.value
        raise AlphaEvaluationError(
            f"{func}(): keyword argument {key!r} must be a literal number or boolean, "
            f"got {type(node).__name__}"
        )


def evaluate_expression(expr_str: str, panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    ast = parse_expression(expr_str)
    return Evaluator(panel).eval(ast)


if __name__ == "__main__":
    from data_layer import generate_synthetic_data

    panel = generate_synthetic_data(["AAA", "BBB", "CCC", "DDD"], n_days=60)

    handwritten_expressions = [
        "close",
        "rank(close)",
        "add(close, open, volume, filter=true)",
        "if_else(close > open, 1, -1)",
        "and(close > open, volume > adv20)",
        "winsorize(returns, std=3)",
        "ts_delay(close, 5)",
        "ts_zscore(close, 10)",
        "ts_arg_max(close, 10)",
        "ts_scale(close, 10, constant=0)",
        "ts_step(1)",
        "ts_backfill(close, lookback=10)",
        "scale(close, scale=1, longscale=2, shortscale=1)",
        "power(close, 2)",
        "signed_power(close - open, 0.5)",
    ]
    for expr in handwritten_expressions:
        result = evaluate_expression(expr, panel)
        assert result.shape == panel["close"].shape, f"shape mismatch for {expr}"
        print(f"OK  {expr:50s} last_row={result.dropna(how='all').tail(1).values.tolist()}")