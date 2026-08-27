"""
dsl/parser.py
=============
Grammar strictly limited to the operator set in operators.json (the
original "101 Formulaic Alphas" paper notation). No keyword arguments,
no boolean/string literals -- none of the allowed operators need them.

Supported surface syntax:
  - arithmetic:    + - * /  (and unary minus)
  - comparisons:   > < == >= <= !=
  - logical OR:    ||        (no && or ! in this operator set)
  - ternary:       x ? y : z
  - function calls with purely positional arguments: name(a, b, ...)

Precedence (loosest to tightest): ternary > || > comparison > +/- > * / > unary neg.
"""

from __future__ import annotations
from dataclasses import dataclass
from lark import Lark, Transformer, v_args, UnexpectedInput


# ---------------------------------------------------------------------------
# AST node types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Number:
    value: float


@dataclass(frozen=True)
class Field:
    name: str


@dataclass(frozen=True)
class FuncCall:
    name: str
    args: tuple  # positional AST nodes only -- this operator set has no kwargs


@dataclass(frozen=True)
class BinOp:
    op: str          # + - * / > < == ||
    left: object
    right: object


@dataclass(frozen=True)
class UnaryNeg:
    operand: object


@dataclass(frozen=True)
class Ternary:
    cond: object
    true_val: object
    false_val: object


# ---------------------------------------------------------------------------
# Grammar
# ---------------------------------------------------------------------------

_GRAMMAR = r"""
    ?start: expr

    ?expr: logical_or "?" expr ":" expr -> ternary
         | logical_or

    ?logical_or: logical_or "||" comparison -> or_op
               | comparison

    ?comparison: comparison ">"  add_expr -> gt
               | comparison "<"  add_expr -> lt
               | comparison ">=" add_expr -> ge
               | comparison "<=" add_expr -> le
               | comparison "==" add_expr -> eq
               | comparison "!=" add_expr -> ne
               | add_expr

    ?add_expr: add_expr "+" term -> add
             | add_expr "-" term -> sub
             | term

    ?term: term "*" factor -> mul
         | term "/" factor -> div
         | factor

    ?factor: "-" factor    -> neg
           | atom

    ?atom: NUMBER                  -> number
         | NAME "(" args ")"       -> func_call
         | NAME                    -> field
         | "(" expr ")"

    args: (expr ("," expr)*)?

    NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
    %import common.NUMBER
    %import common.WS
    %ignore WS
"""


@v_args(inline=True)
class _ASTBuilder(Transformer):
    def number(self, tok):
        return Number(float(tok))

    def field(self, name_tok):
        return Field(str(name_tok))

    def args(self, *items):
        return list(items)

    def func_call(self, name_tok, args_list):
        return FuncCall(str(name_tok), tuple(args_list))

    def add(self, l, r): return BinOp("+", l, r)
    def sub(self, l, r): return BinOp("-", l, r)
    def mul(self, l, r): return BinOp("*", l, r)
    def div(self, l, r): return BinOp("/", l, r)
    def gt(self, l, r): return BinOp(">", l, r)
    def lt(self, l, r): return BinOp("<", l, r)
    def ge(self, l, r): return BinOp(">=", l, r)
    def le(self, l, r): return BinOp("<=", l, r)
    def eq(self, l, r): return BinOp("==", l, r)
    def ne(self, l, r): return BinOp("!=", l, r)
    def or_op(self, l, r): return BinOp("||", l, r)
    def neg(self, operand): return UnaryNeg(operand)

    def ternary(self, cond, true_val, false_val):
        return Ternary(cond, true_val, false_val)


_parser = Lark(_GRAMMAR, parser="lalr")
_builder = _ASTBuilder()


class AlphaExpressionSyntaxError(ValueError):
    pass


def parse_expression(expr_str: str):
    try:
        tree = _parser.parse(expr_str)
    except UnexpectedInput as e:
        raise AlphaExpressionSyntaxError(f"Could not parse expression {expr_str!r}: {e}") from e
    return _builder.transform(tree)


if __name__ == "__main__":
    examples = [
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
        "((-1 * ts_rank(correlation(low, delay(close, 2), 5), 2)) * rank(correlation(low, volume, 5)))",
    ]
    for e in examples:
        ast = parse_expression(e)
        print(f"{e!r:45s} -> {ast}")

    try:
        parse_expression("rank(close, )")
    except AlphaExpressionSyntaxError as e:
        print(f"\nExpected syntax error caught OK: {e}")