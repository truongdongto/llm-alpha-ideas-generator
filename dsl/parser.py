"""
dsl/parser.py
=============
Responsibility: turn an alpha expression STRING (e.g.
    "rank(ts_delta(close, 5) / ts_std(returns, 20))"
) into an AST (Abstract Syntax Tree) of plain Python objects.

This module knows NOTHING about pandas/numpy or how to actually compute
anything -- it only knows grammar. That separation matters: it means an
LLM (in Module 3, later) only ever needs to produce a *string* in this
grammar, and this parser's job is just to validate that the string is
syntactically well-formed and turn it into a structure the evaluator
(dsl/evaluator.py) can walk.

Grammar supported:
    - arithmetic:      + - * /  and unary minus
    - numeric literals: 3, 5, 0.5, 20
    - identifiers (data fields): close, open, high, low, volume, returns, vwap, adv20
    - function calls:  name(arg1, arg2, ...)
    - parentheses for grouping

We use `lark` (an off-the-shelf parser library) to build the parse tree,
then walk it with a lark Transformer to produce our own lightweight AST
node classes (Number, Field, FuncCall, BinOp, UnaryNeg). Using our own
node classes (rather than passing lark's raw tree downstream) keeps the
evaluator decoupled from lark -- if we ever swap parser libraries, only
this file changes.
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
    args: tuple  # tuple of AST nodes


@dataclass(frozen=True)
class BinOp:
    op: str          # '+', '-', '*', '/'
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

    ?expr: expr "+" term   -> add
         | expr "-" term   -> sub
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

    args: expr ("," expr)*

    NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
    %import common.NUMBER
    %import common.WS
    %ignore WS
"""


@v_args(inline=True)
class _ASTBuilder(Transformer):
    """Walks the lark parse tree and builds our AST node classes."""

    def number(self, tok):
        return Number(float(tok))

    def field(self, name_tok):
        return Field(str(name_tok))

    def func_call(self, name_tok, args_list):
        # by the time this runs, the `args` rule has already been
        # transformed (bottom-up) into a plain Python list
        return FuncCall(str(name_tok), tuple(args_list))

    def args(self, *children):
        return list(children)

    def add(self, l, r):
        return BinOp("+", l, r)

    def sub(self, l, r):
        return BinOp("-", l, r)

    def mul(self, l, r):
        return BinOp("*", l, r)

    def div(self, l, r):
        return BinOp("/", l, r)

    def neg(self, operand):
        return UnaryNeg(operand)


_parser = Lark(_GRAMMAR, parser="lalr", transformer=None)
_builder = _ASTBuilder()


class AlphaExpressionSyntaxError(ValueError):
    """Raised when an expression string doesn't match the DSL grammar."""


def parse_expression(expr_str: str):
    """
    Parse an alpha expression string into an AST.

    Raises AlphaExpressionSyntaxError with a readable message if the
    string is not valid -- this is the boundary where malformed LLM
    output should get caught, before it ever touches real computation.
    """
    try:
        tree = _parser.parse(expr_str)
    except UnexpectedInput as e:
        raise AlphaExpressionSyntaxError(
            f"Could not parse expression {expr_str!r}: {e}"
        ) from e
    return _builder.transform(tree)


if __name__ == "__main__":
    examples = [
        "close",
        "rank(close)",
        "ts_delta(close, 5)",
        "rank(ts_delta(close, 5) / ts_std(returns, 20))",
        "-rank(close - open) * 2",
        "ts_corr(volume, close, 10) + 0.5",
    ]
    for e in examples:
        ast = parse_expression(e)
        print(f"{e!r:60s} -> {ast}")

    # a deliberately broken expression to confirm error handling works
    try:
        parse_expression("rank(open - (sum(vwap, 10) / 10)) * -1 * abs(rank(close - vwap))")
    except AlphaExpressionSyntaxError as e:
        print(f"\nExpected syntax error caught OK: {e}")