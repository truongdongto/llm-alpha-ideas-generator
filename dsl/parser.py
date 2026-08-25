"""
dsl/parser.py
=============
Grammar extended to match WorldQuant BRAIN's expression syntax:
  - keyword args:      rank(x, rate=2), scale(x, scale=1, longscale=1)
  - comparison ops:    x < y, x >= y, x == y  (return 1.0/0.0)
  - boolean literals:  true / false (used as kwarg values, e.g. filter=true)
  - n-ary functions:   add(x, y, z), max(x, y, z, ...)

Grammar precedence (loosest to tightest): comparison > +/- > * / > unary neg.
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
class Boolean:
    value: bool


@dataclass(frozen=True)
class Field:
    name: str


@dataclass(frozen=True)
class FuncCall:
    name: str
    pos_args: tuple            # positional AST nodes
    kwargs: dict                # name -> Number | Boolean AST node


@dataclass(frozen=True)
class BinOp:
    op: str          # + - * / < <= > >= == !=
    left: object
    right: object


@dataclass(frozen=True)
class UnaryNeg:
    operand: object


# ---------------------------------------------------------------------------
# Grammar
# ---------------------------------------------------------------------------

_GRAMMAR = r"""
    ?start: expr

    ?expr: comparison "?" expr ":" expr -> ternary
         | comparison

    ?comparison: comparison "<"  add_expr -> lt
               | comparison "<=" add_expr -> le
               | comparison ">"  add_expr -> gt
               | comparison ">=" add_expr -> ge
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
         | TRUE                    -> true_lit
         | FALSE                   -> false_lit
         | NAME "(" args ")"       -> func_call
         | NAME                    -> field
         | "(" expr ")"

    args: (arg ("," arg)*)?
    ?arg: NAME "=" value  -> kwarg
        | expr            -> posarg
    ?value: NUMBER -> number
          | TRUE -> true_lit
          | FALSE -> false_lit

    NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
    TRUE.2: "true"
    FALSE.2: "false"
    %import common.NUMBER
    %import common.WS
    %ignore WS
"""


@v_args(inline=True)
class _ASTBuilder(Transformer):
    def number(self, tok):
        return Number(float(tok))

    def true_lit(self, tok=None):
        return Boolean(True)

    def false_lit(self, tok=None):
        return Boolean(False)

    def field(self, name_tok):
        return Field(str(name_tok))

    def posarg(self, node):
        return ("pos", node)

    def kwarg(self, name_tok, value_node):
        return ("kw", str(name_tok), value_node)

    def args(self, *items):
        return list(items)

    def func_call(self, name_tok, args_list):
        pos_args = tuple(item[1] for item in args_list if item[0] == "pos")
        kwargs = {item[1]: item[2] for item in args_list if item[0] == "kw"}
        return FuncCall(str(name_tok), pos_args, kwargs)

    def add(self, l, r): return BinOp("+", l, r)
    def sub(self, l, r): return BinOp("-", l, r)
    def mul(self, l, r): return BinOp("*", l, r)
    def div(self, l, r): return BinOp("/", l, r)
    def lt(self, l, r): return BinOp("<", l, r)
    def le(self, l, r): return BinOp("<=", l, r)
    def gt(self, l, r): return BinOp(">", l, r)
    def ge(self, l, r): return BinOp(">=", l, r)
    def eq(self, l, r): return BinOp("==", l, r)
    def ne(self, l, r): return BinOp("!=", l, r)
    def neg(self, operand): return UnaryNeg(operand)

    def ternary(self, cond, true_val, false_val):
        # "cond ? a : b" is sugar for if_else(cond, a, b) -- reuse the same
        # FuncCall representation so no new evaluator logic is needed.
        return FuncCall("if_else", (cond, true_val, false_val), {})


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
        "rank(close, rate=2)",
        "add(close, open, filter=true)",
        "scale(close, scale=1, longscale=2, shortscale=1)",
        "if_else(close > open, 1, -1)",
        "and(close > open, volume > adv20)",
        "ts_backfill(close, lookback=20, k=1)",
        "winsorize(returns, std=3)",
        "close != open",
        "not(close < open)",
    ]
    for e in examples:
        ast = parse_expression(e)
        print(f"{e!r:55s} -> {ast}")

    try:
        parse_expression("rank(close, unknown_kwarg_syntax=)")
    except AlphaExpressionSyntaxError as e:
        print(f"\nExpected syntax error caught OK: {e}")