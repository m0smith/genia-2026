#!/usr/bin/env python3
"""
Minimal Genia REPL / interpreter prototype.

Need to implement soon:
And I would say this requires:

- list values
- list patterns
- wildcard _
- rest pattern ..
- recursion

Implemented subset:
- numbers, booleans, nil, strings
- arithmetic: + - * / %
- comparison: < <= > >= == !=
- variables and function calls
- function definitions: name(args) = expr
- function definitions with blocks: name(args) { ... }
- case expressions in function bodies and as final expression in blocks
- pattern matching against the full argument tuple
- single-argument pattern shorthand: 0 -> 1 is treated like (0) -> 1
- guards: pattern ? condition -> result
- blocks with newline or ; expression separators
- builtins: log(...), print(...), input(prompt), help()

Not yet implemented:
- lambdas
- lists/maps/destructuring beyond tuple-parameter patterns
- pipelines
- member access / indexing
- modules
"""
from __future__ import annotations

import math
import os
from pathlib import Path
import re
import sys
import threading
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional

BASE_DIR = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()


# -----------------------------
# Lexer
# -----------------------------

TOKEN_SPEC = [
    ("NUMBER", r"\d+(?:\.\d+)?"),
    ("STRING", r'"([^"\\]|\\.)*"|\'([^\'\\]|\\.)*\''),
    ("ARROW", r"->"),
    ("EQEQ", r"=="),
    ("NE", r"!="),
    ("LE", r"<="),
    ("GE", r">="),
    ("AND", r"&&"),
    ("OR", r"\|\|"),
    ("ASSIGN", r"="),
    ("LT", r"<"),
    ("GT", r">"),
    ("PLUS", r"\+"),
    ("MINUS", r"-"),
    ("STAR", r"\*"),
    ("SLASH", r"/"),
    ("PERCENT", r"%"),
    ("BANG", r"!"),
    ("QMARK", r"\?"),
    ("PIPE", r"\|"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("LBRACE", r"\{"),
    ("RBRACE", r"\}"),
    ("LBRACK", r"\["),
    ("RBRACK", r"\]"),
    ("DOTDOT", r"\.\."),
    ("COMMA", r","),
    ("SEMI", r";"),
    ("COMMENT", r"#[^\n]*"),
    ("NEWLINE", r"\n"),
    ("SKIP", r"[ \t\r]+"),
]
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
STRING_RE = re.compile(r'"([^"\\]|\\.)*"|\'([^\'\\]|\\.)*\'')
PUNCTUATION_TOKENS = [
    ("ARROW", "->"),
    ("EQEQ", "=="),
    ("NE", "!="),
    ("LE", "<="),
    ("GE", ">="),
    ("AND", "&&"),
    ("OR", "||"),
    ("DOTDOT", ".."),
    ("ASSIGN", "="),
    ("LT", "<"),
    ("GT", ">"),
    ("PLUS", "+"),
    ("MINUS", "-"),
    ("STAR", "*"),
    ("SLASH", "/"),
    ("PERCENT", "%"),
    ("BANG", "!"),
    ("QMARK", "?"),
    ("PIPE", "|"),
    ("LPAREN", "("),
    ("RPAREN", ")"),
    ("LBRACE", "{"),
    ("RBRACE", "}"),
    ("LBRACK", "["),
    ("RBRACK", "]"),
    ("COMMA", ","),
    ("SEMI", ";"),
]
TOKEN_BOUNDARIES = [text for _, text in PUNCTUATION_TOKENS] + ["#"]
IDENT_TOKEN_BOUNDARIES = [boundary for boundary in TOKEN_BOUNDARIES if boundary != "?"]


def _starts_token_boundary(source: str, pos: int, *, for_identifier: bool = False) -> bool:
    boundaries = IDENT_TOKEN_BOUNDARIES if for_identifier else TOKEN_BOUNDARIES
    return any(source.startswith(boundary, pos) for boundary in boundaries)


@dataclass
class Token:
    kind: str
    text: str
    pos: int


def lex(source: str) -> list[Token]:
    tokens: list[Token] = []
    pos = 0
    length = len(source)

    while pos < length:
        ch = source[pos]

        if ch in " \t\r":
            pos += 1
            continue
        if ch == "\n":
            tokens.append(Token("NEWLINE", ch, pos))
            pos += 1
            continue
        if ch == "#":
            while pos < length and source[pos] != "\n":
                pos += 1
            continue

        number_match = NUMBER_RE.match(source, pos)
        if number_match is not None:
            text = number_match.group()
            tokens.append(Token("NUMBER", text, pos))
            pos += len(text)
            continue

        if ch in "\"'":
            string_match = STRING_RE.match(source, pos)
            if string_match is None:
                raise SyntaxError(f"Unexpected character {ch!r} at {pos}")
            text = string_match.group()
            tokens.append(Token("STRING", text, pos))
            pos += len(text)
            continue

        matched_punctuation = False
        for kind, text in PUNCTUATION_TOKENS:
            if source.startswith(text, pos):
                tokens.append(Token(kind, text, pos))
                pos += len(text)
                matched_punctuation = True
                break
        if matched_punctuation:
            continue

        ident_start = pos
        while pos < length and not source[pos].isspace() and not _starts_token_boundary(source, pos, for_identifier=True):
            pos += 1
        if pos > ident_start:
            tokens.append(Token("IDENT", source[ident_start:pos], ident_start))
            continue
        raise SyntaxError(f"Unexpected character {source[pos]!r} at {pos}")

    tokens.append(Token("EOF", "", len(source)))
    return tokens


# -----------------------------
# AST
# -----------------------------

class Node:
    pass


@dataclass
class Number(Node):
    value: int | float


@dataclass
class String(Node):
    value: str


@dataclass
class Boolean(Node):
    value: bool


@dataclass
class Nil(Node):
    pass


@dataclass
class Var(Node):
    name: str


@dataclass
class Unary(Node):
    op: str
    expr: Node


@dataclass
class Binary(Node):
    left: Node
    op: str
    right: Node


@dataclass
class Call(Node):
    fn: Node
    args: list[Node]


@dataclass
class ExprStmt(Node):
    expr: Node


@dataclass
class Block(Node):
    exprs: list[Node]


@dataclass
class ListLiteral(Node):
    items: list[Node]


@dataclass
class ListPattern(Node):
    items: list[Node]


@dataclass
class WildcardPattern(Node):
    pass


@dataclass
class RestPattern(Node):
    name: str | None


@dataclass
class TuplePattern(Node):
    items: list[Node]


@dataclass
class CaseClause(Node):
    pattern: Node
    guard: Optional[Node]
    result: Node


@dataclass
class CaseExpr(Node):
    clauses: list[CaseClause]


@dataclass
class Lambda(Node):
    params: list[str]
    body: Node


@dataclass
class Assign(Node):
    name: str
    expr: Node


@dataclass
class FuncDef(Node):
    name: str
    params: list[str]
    body: Node


# -----------------------------
# Tiny IR
# -----------------------------

class IrNode:
    """Base type for lowered Genia IR nodes."""


@dataclass
class IrLiteral(IrNode):
    """Normalized constant value (number/string/bool/nil)."""

    value: Any


@dataclass
class IrVar(IrNode):
    """Variable read by name (kept explicit for analysis and rewriting)."""

    name: str


@dataclass
class IrUnary(IrNode):
    """Unary operator application."""

    op: str
    expr: IrNode


@dataclass
class IrBinary(IrNode):
    """Binary operator application with explicit operands."""

    left: IrNode
    op: str
    right: IrNode


@dataclass
class IrCall(IrNode):
    """Function call where callee and args are already lowered."""

    fn: IrNode
    args: list[IrNode]


@dataclass
class IrExprStmt(IrNode):
    """Top-level expression statement (keeps source ordering explicit)."""

    expr: IrNode


@dataclass
class IrBlock(IrNode):
    """Sequential expression block."""

    exprs: list[IrNode]


@dataclass
class IrList(IrNode):
    """List literal with lowered items."""

    items: list[IrNode]


class IrPattern:
    """Base type for case patterns in IR."""


@dataclass
class IrPatLiteral(IrPattern):
    """Literal pattern used in case matching."""

    value: Any


@dataclass
class IrPatBind(IrPattern):
    """Pattern variable binding."""

    name: str


@dataclass
class IrPatWildcard(IrPattern):
    """Wildcard pattern (_) that matches without binding."""

    pass


@dataclass
class IrPatRest(IrPattern):
    """List-rest pattern (.. or ..name)."""

    name: str | None


@dataclass
class IrPatTuple(IrPattern):
    """Tuple argument-pattern shape for function dispatch."""

    items: list[IrPattern]


@dataclass
class IrPatList(IrPattern):
    """List structural pattern with optional rest."""

    items: list[IrPattern]


@dataclass
class IrCaseClause(IrNode):
    """Single case arm with optional guard."""

    pattern: IrPattern
    guard: Optional[IrNode]
    result: IrNode


@dataclass
class IrCase(IrNode):
    """Case dispatch is explicit so optimization passes can inspect patterns."""

    clauses: list[IrCaseClause]


@dataclass
class IrLambda(IrNode):
    """Lambda expression with params and lowered body."""

    params: list[str]
    body: IrNode


@dataclass
class IrAssign(IrNode):
    """Top-level assignment side effect."""

    name: str
    expr: IrNode


@dataclass
class IrFuncDef(IrNode):
    """Named function definition with lowered body."""

    name: str
    params: list[str]
    body: IrNode


@dataclass
class IrListTraversalLoop(IrNode):
    """Optimized loop-like form for nth-style list traversal recursion."""

    counter_var: str
    list_var: str
    step_size: int
    empty_clause: IrCaseClause
    zero_clause: IrCaseClause


def lower_program(nodes: Iterable[Node]) -> list[IrNode]:
    return [lower_node(node) for node in nodes]


def lower_node(node: Node) -> IrNode:
    if isinstance(node, ExprStmt):
        return IrExprStmt(lower_node(node.expr))
    if isinstance(node, Number):
        return IrLiteral(node.value)
    if isinstance(node, String):
        return IrLiteral(node.value)
    if isinstance(node, Boolean):
        return IrLiteral(node.value)
    if isinstance(node, Nil):
        return IrLiteral(None)
    if isinstance(node, Var):
        return IrVar(node.name)
    if isinstance(node, Unary):
        return IrUnary(node.op, lower_node(node.expr))
    if isinstance(node, Binary):
        return IrBinary(lower_node(node.left), node.op, lower_node(node.right))
    if isinstance(node, Call):
        return IrCall(lower_node(node.fn), [lower_node(arg) for arg in node.args])
    if isinstance(node, Block):
        return IrBlock([lower_node(expr) for expr in node.exprs])
    if isinstance(node, ListLiteral):
        return IrList([lower_node(item) for item in node.items])
    if isinstance(node, CaseExpr):
        return IrCase(
            [
                IrCaseClause(
                    lower_pattern(clause.pattern),
                    lower_node(clause.guard) if clause.guard is not None else None,
                    lower_node(clause.result),
                )
                for clause in node.clauses
            ]
        )
    if isinstance(node, Lambda):
        return IrLambda(node.params, lower_node(node.body))
    if isinstance(node, Assign):
        return IrAssign(node.name, lower_node(node.expr))
    if isinstance(node, FuncDef):
        return IrFuncDef(node.name, node.params, lower_node(node.body))
    raise RuntimeError(f"Unknown AST node during lowering: {node!r}")


def lower_pattern(pattern: Node) -> IrPattern:
    if isinstance(pattern, Number):
        return IrPatLiteral(pattern.value)
    if isinstance(pattern, String):
        return IrPatLiteral(pattern.value)
    if isinstance(pattern, Boolean):
        return IrPatLiteral(pattern.value)
    if isinstance(pattern, Nil):
        return IrPatLiteral(None)
    if isinstance(pattern, WildcardPattern):
        return IrPatWildcard()
    if isinstance(pattern, RestPattern):
        return IrPatRest(pattern.name)
    if isinstance(pattern, Var):
        return IrPatBind(pattern.name)
    if isinstance(pattern, TuplePattern):
        return IrPatTuple([lower_pattern(item) for item in pattern.items])
    if isinstance(pattern, ListPattern):
        return IrPatList([lower_pattern(item) for item in pattern.items])
    raise RuntimeError(f"Unknown pattern during lowering: {pattern!r}")


def optimize_program(ir_nodes: Iterable[IrNode], *, debug: bool = False) -> list[IrNode]:
    optimized: list[IrNode] = []
    for node in ir_nodes:
        if isinstance(node, IrFuncDef):
            rewritten = optimize_nth_style_recursion(node)
            if rewritten is not node and debug:
                print(f"Applied list traversal optimization to function {node.name}/{len(node.params)}")
            optimized.append(rewritten)
        else:
            optimized.append(node)
    return optimized


def optimize_nth_style_recursion(fn: IrFuncDef) -> IrFuncDef:
    if len(fn.params) != 2 or not isinstance(fn.body, IrCase):
        return fn
    case = fn.body
    if any(clause.guard is not None for clause in case.clauses):
        return fn

    empty_clause: IrCaseClause | None = None
    zero_clause: IrCaseClause | None = None
    recur_clause: IrCaseClause | None = None

    for clause in case.clauses:
        if recursive_call_count(clause.result, fn.name) > 1:
            return fn
        tuple_pat = clause.pattern
        if not isinstance(tuple_pat, IrPatTuple) or len(tuple_pat.items) != 2:
            continue
        n_pat, xs_pat = tuple_pat.items
        if (
            isinstance(xs_pat, IrPatList)
            and len(xs_pat.items) == 0
            and isinstance(clause.result, IrLiteral)
            and clause.result.value is None
            and empty_clause is None
        ):
            empty_clause = clause
            continue
        if (
            isinstance(n_pat, IrPatLiteral)
            and n_pat.value == 0
            and isinstance(xs_pat, IrPatList)
            and len(xs_pat.items) == 2
            and isinstance(xs_pat.items[0], IrPatBind)
            and isinstance(xs_pat.items[1], IrPatRest)
            and isinstance(clause.result, IrVar)
            and clause.result.name == xs_pat.items[0].name
            and zero_clause is None
        ):
            zero_clause = clause
            continue
        if recur_clause is None and is_tail_recursive_step(clause, fn.name):
            recur_clause = clause
            n_bind = n_pat if isinstance(n_pat, IrPatBind) else None
            rest_pat = xs_pat.items[1] if isinstance(xs_pat, IrPatList) and len(xs_pat.items) == 2 else None
            if n_bind is None or not isinstance(rest_pat, IrPatRest) or rest_pat.name is None:
                return fn
            continue
        if recursive_call_count(clause.result, fn.name) > 0:
            return fn

    if empty_clause is None or zero_clause is None or recur_clause is None:
        return fn
    recur_pat = recur_clause.pattern
    assert isinstance(recur_pat, IrPatTuple)
    recur_n_pat, recur_xs_pat = recur_pat.items
    if not (isinstance(recur_n_pat, IrPatBind) and isinstance(recur_xs_pat, IrPatList)):
        return fn
    if len(recur_xs_pat.items) != 2 or not isinstance(recur_xs_pat.items[1], IrPatRest):
        return fn
    rest_name = recur_xs_pat.items[1].name
    if rest_name is None:
        return fn
    recur_result = recur_clause.result
    if not isinstance(recur_result, IrCall) or not isinstance(recur_result.fn, IrVar) or recur_result.fn.name != fn.name:
        return fn
    if len(recur_result.args) != 2:
        return fn
    n_arg, xs_arg = recur_result.args
    if not (
        isinstance(n_arg, IrBinary)
        and n_arg.op == "MINUS"
        and isinstance(n_arg.left, IrVar)
        and n_arg.left.name == recur_n_pat.name
        and isinstance(n_arg.right, IrLiteral)
        and n_arg.right.value == 1
    ):
        return fn
    if not (isinstance(xs_arg, IrVar) and xs_arg.name == rest_name):
        return fn

    return IrFuncDef(
        fn.name,
        fn.params,
        IrListTraversalLoop(
            counter_var=fn.params[0],
            list_var=fn.params[1],
            step_size=1,
            empty_clause=empty_clause,
            zero_clause=zero_clause,
        ),
    )


def is_tail_recursive_step(clause: IrCaseClause, fn_name: str) -> bool:
    tuple_pat = clause.pattern
    if not isinstance(tuple_pat, IrPatTuple) or len(tuple_pat.items) != 2:
        return False
    _, xs_pat = tuple_pat.items
    if not (isinstance(xs_pat, IrPatList) and len(xs_pat.items) == 2 and isinstance(xs_pat.items[1], IrPatRest)):
        return False
    result = clause.result
    if not isinstance(result, IrCall):
        return False
    if not isinstance(result.fn, IrVar) or result.fn.name != fn_name:
        return False
    return recursive_call_count(result, fn_name) == 1


def recursive_call_count(node: IrNode, fn_name: str) -> int:
    if isinstance(node, IrCall):
        own = 1 if isinstance(node.fn, IrVar) and node.fn.name == fn_name else 0
        return own + recursive_call_count(node.fn, fn_name) + sum(recursive_call_count(arg, fn_name) for arg in node.args)
    if isinstance(node, IrUnary):
        return recursive_call_count(node.expr, fn_name)
    if isinstance(node, IrBinary):
        return recursive_call_count(node.left, fn_name) + recursive_call_count(node.right, fn_name)
    if isinstance(node, IrBlock):
        return sum(recursive_call_count(expr, fn_name) for expr in node.exprs)
    if isinstance(node, IrExprStmt):
        return recursive_call_count(node.expr, fn_name)
    if isinstance(node, IrCase):
        return sum(recursive_call_count(clause.result, fn_name) for clause in node.clauses)
    if isinstance(node, IrAssign):
        return recursive_call_count(node.expr, fn_name)
    if isinstance(node, IrLambda):
        return recursive_call_count(node.body, fn_name)
    return 0


# -----------------------------
# Parser
# -----------------------------

PRECEDENCE = {
    "OR": 10,
    "AND": 20,
    "EQEQ": 30,
    "NE": 30,
    "LT": 40,
    "LE": 40,
    "GT": 40,
    "GE": 40,
    "PLUS": 50,
    "MINUS": 50,
    "STAR": 60,
    "SLASH": 60,
    "PERCENT": 60,
}


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.i = 0

    def peek(self, offset: int = 0) -> Token:
        return self.tokens[self.i + offset]

    def at(self, *kinds: str) -> bool:
        return self.peek().kind in kinds

    def eat(self, kind: str) -> Token:
        tok = self.peek()
        if tok.kind != kind:
            raise SyntaxError(f"Expected {kind}, got {tok.kind} at {tok.pos}")
        self.i += 1
        return tok

    def maybe(self, kind: str) -> Optional[Token]:
        if self.at(kind):
            return self.eat(kind)
        return None

    def skip_separators(self) -> None:
        while self.at("NEWLINE", "SEMI"):
            self.i += 1

    def parse_program(self) -> list[Node]:
        out: list[Node] = []
        self.skip_separators()
        while not self.at("EOF"):
            out.append(self.parse_toplevel())
            self.skip_separators()
        return out

    def try_parse_function_header(self) -> tuple[str, list[str]] | None:
        if not (self.at("IDENT") and self.peek(1).kind == "LPAREN"):
            return None

        save = self.i
        try:
            name = self.eat("IDENT").text
            self.eat("LPAREN")
            params: list[str] = []
            if not self.at("RPAREN"):
                while True:
                    params.append(self.eat("IDENT").text)
                    if not self.maybe("COMMA"):
                        break
            self.eat("RPAREN")

            if self.at("ASSIGN", "LBRACE"):
                return name, params

            self.i = save
            return None
        except SyntaxError:
            self.i = save
            return None

    def parse_toplevel(self) -> Node:
        header = self.try_parse_function_header()
        if header is not None:
            name, params = header

            if self.at("ASSIGN"):
                self.eat("ASSIGN")
                self.skip_separators()
                body = self.parse_function_body_after_intro()
                return FuncDef(name, params, body)

            if self.at("LBRACE"):
                body = self.parse_block(allow_final_case=True)
                return FuncDef(name, params, body)

            raise SyntaxError("Internal parser error: expected function body")

        if self.at("IDENT") and self.peek(1).kind == "ASSIGN":
            name = self.eat("IDENT").text
            self.eat("ASSIGN")
            self.skip_separators()
            expr = self.parse_expr()
            return Assign(name, expr)

        expr = self.parse_expr()
        return ExprStmt(expr)

    def parse_function_body_after_intro(self) -> Node:
        if self.looks_like_case_start():
            return self.parse_case_expr(single_param_shorthand_ok=True)
        return self.parse_expr()

    def parse_block(self, allow_final_case: bool) -> Block:
        self.eat("LBRACE")
        exprs: list[Node] = []
        self.skip_separators()
        while not self.at("RBRACE"):
            if allow_final_case and self.looks_like_case_start():
                case_expr = self.parse_case_expr(single_param_shorthand_ok=True)
                exprs.append(case_expr)
                self.skip_separators()
                if not self.at("RBRACE"):
                    raise SyntaxError("Case expression must be final in a block")
                break
            exprs.append(self.parse_expr())
            self.skip_separators()
        self.eat("RBRACE")
        return Block(exprs)

    def looks_like_case_start(self) -> bool:
        # single param shorthand cases: 0 ->, name ->, [x, y] ->, name ? ... ->
        # tuple case: ( ... ) ->
        # We only detect enough for v0.1.
        if self.at("NUMBER", "STRING", "IDENT"):
            j = self.i + 1
            while self.tokens[j].kind == "NEWLINE":
                j += 1
            if self.tokens[j].kind in {"ARROW", "QMARK"}:
                return True
        if self.at("LPAREN", "LBRACK"):
            open_kind = self.peek().kind
            close_kind = "RPAREN" if open_kind == "LPAREN" else "RBRACK"
            depth = 0
            j = self.i
            while True:
                tok = self.tokens[j]
                if tok.kind == open_kind:
                    depth += 1
                elif tok.kind == close_kind:
                    depth -= 1
                    if depth == 0:
                        j += 1
                        while self.tokens[j].kind == "NEWLINE":
                            j += 1
                        return self.tokens[j].kind in {"ARROW", "QMARK"}
                elif tok.kind == "EOF":
                    return False
                j += 1
        return False

    def parse_case_expr(self, single_param_shorthand_ok: bool) -> CaseExpr:
        clauses = [self.parse_case_clause(single_param_shorthand_ok)]
        while self.maybe("PIPE"):
            self.skip_separators()
            clauses.append(self.parse_case_clause(single_param_shorthand_ok))
        return CaseExpr(clauses)

    def parse_case_clause(self, single_param_shorthand_ok: bool) -> CaseClause:
        pattern = self.parse_pattern(single_param_shorthand_ok)
        guard = None
        if self.maybe("QMARK"):
            guard = self.parse_expr()
        self.eat("ARROW")
        result = self.parse_expr()
        return CaseClause(pattern, guard, result)

    def parse_pattern(self, single_param_shorthand_ok: bool) -> Node:
        if self.at("LPAREN"):
            self.eat("LPAREN")
            items: list[Node] = []
            if not self.at("RPAREN"):
                while True:
                    items.append(self.parse_pattern_atom())
                    if not self.maybe("COMMA"):
                        break
            self.eat("RPAREN")
            return TuplePattern(items)
        atom = self.parse_pattern_atom()
        if single_param_shorthand_ok:
            return atom
        return TuplePattern([atom])

    def parse_pattern_atom(self) -> Node:
        tok = self.peek()
        if tok.kind == "NUMBER":
            self.i += 1
            return Number(float(tok.text) if "." in tok.text else int(tok.text))
        if tok.kind == "STRING":
            self.i += 1
            return String(eval(tok.text))
        if tok.kind == "DOTDOT":
            self.i += 1
            if self.at("IDENT"):
                name = self.eat("IDENT").text
                if name == "_":
                    return RestPattern(None)
                return RestPattern(name)
            return RestPattern(None)
        if tok.kind == "IDENT":
            self.i += 1
            if tok.text == "true":
                return Boolean(True)
            if tok.text == "false":
                return Boolean(False)
            if tok.text == "nil":
                return Nil()
            if tok.text == "_":
                return WildcardPattern()
            return Var(tok.text)
        if tok.kind == "LBRACK":
            self.i += 1
            items: list[Node] = []
            saw_rest = False
            if not self.at("RBRACK"):
                while True:
                    item = self.parse_pattern_atom()
                    if saw_rest:
                        raise SyntaxError("..rest must be the final item in a list pattern")
                    items.append(item)
                    if isinstance(item, RestPattern):
                        saw_rest = True
                    if not self.maybe("COMMA"):
                        break
            self.eat("RBRACK")
            return ListPattern(items)
        raise SyntaxError(f"Invalid pattern at {tok.pos}")

    def parse_expr(self, min_prec: int = 0) -> Node:
        left = self.parse_prefix()
        while True:
            tok = self.peek()
            if tok.kind == "LPAREN":
                left = self.finish_call(left)
                continue
            prec = PRECEDENCE.get(tok.kind)
            if prec is None or prec < min_prec:
                break
            op = tok.kind
            self.i += 1
            right = self.parse_expr(prec + 1)
            left = Binary(left, op, right)
        return left

    def parse_prefix(self) -> Node:
        tok = self.peek()
        if tok.kind == "NUMBER":
            self.i += 1
            return Number(float(tok.text) if "." in tok.text else int(tok.text))
        if tok.kind == "STRING":
            self.i += 1
            return String(eval(tok.text))
        if tok.kind == "IDENT":
            self.i += 1
            if tok.text == "true":
                return Boolean(True)
            if tok.text == "false":
                return Boolean(False)
            if tok.text == "nil":
                return Nil()
            return Var(tok.text)
        if tok.kind in ("MINUS", "BANG"):
            self.i += 1
            return Unary(tok.kind, self.parse_expr(70))
        if tok.kind == "LPAREN":
            save = self.i
            try:
                self.i += 1
                params: list[str] = []
                if not self.at("RPAREN"):
                    while True:
                        params.append(self.eat("IDENT").text)
                        if not self.maybe("COMMA"):
                            break
                self.eat("RPAREN")
                if self.at("ARROW"):
                    self.eat("ARROW")
                    body = self.parse_expr()
                    return Lambda(params, body)
                self.i = save
            except SyntaxError:
                self.i = save

            self.i += 1
            expr = self.parse_expr()
            self.eat("RPAREN")
            return expr
        if tok.kind == "LBRACK":
            return self.parse_list_literal()
        if tok.kind == "LBRACE":
            return self.parse_block(allow_final_case=False)
        raise SyntaxError(f"Unexpected token {tok.kind} at {tok.pos}")

    def parse_list_literal(self) -> ListLiteral:
        self.eat("LBRACK")
        items: list[Node] = []
        if not self.at("RBRACK"):
            while True:
                items.append(self.parse_expr())
                if not self.maybe("COMMA"):
                    break
        self.eat("RBRACK")
        return ListLiteral(items)

    def finish_call(self, fn: Node) -> Node:
        self.eat("LPAREN")
        args: list[Node] = []
        if not self.at("RPAREN"):
            while True:
                args.append(self.parse_expr())
                if not self.maybe("COMMA"):
                    break
        self.eat("RPAREN")
        return Call(fn, args)


# -----------------------------
# Runtime
# -----------------------------

class Env:
    def __init__(self, parent: Optional["Env"] = None):
        self.parent = parent
        self.values: dict[str, Any] = {}
        self.autoloads: dict[tuple[str, int], str] = {}
        self.loaded_files: set[str] = set()
        self.loading_files: set[str] = set()

    def root(self) -> "Env":
        env = self
        while env.parent is not None:
            env = env.parent
        return env

    def get(self, name: str) -> Any:
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise NameError(f"Undefined name: {name}")

    def set(self, name: str, value: Any) -> None:
        self.values[name] = value

    def define_function(self, fn: "GeniaFunction") -> None:
        existing = self.values.get(fn.name)
        if existing is None:
            self.values[fn.name] = {fn.arity: fn}
            return
        if not isinstance(existing, dict) or not all(isinstance(k, int) for k in existing):
            raise TypeError(f"Cannot define function {fn.name}/{fn.arity}: name already bound to non-function value")
        if fn.arity in existing:
            raise TypeError(f"Duplicate function definition: {fn.name}/{fn.arity}")
        existing[fn.arity] = fn

    def register_autoload(self, name: str, arity: int, path: str) -> None:
        root = self.root()
        root.autoloads[(name, arity)] = path

    def try_autoload(self, name: str, arity: int) -> bool:
        root = self.root()
        path = root.autoloads.get((name, arity))
        if path is None:
            return False

        full_path = (BASE_DIR / path).resolve()
        key = str(full_path)

        if key in root.loaded_files:
            return True

        if key in root.loading_files:
            raise RuntimeError(f"Autoload cycle detected while loading {full_path}")

        root.loading_files.add(key)
        try:
            source = full_path.read_text(encoding="utf-8")
            run_source(source, root)
            root.loaded_files.add(key)
            return True
        finally:
            root.loading_files.remove(key)


@dataclass
class GeniaFunction:
    name: str
    params: list[str]
    body: IrNode
    closure: Env

    @property
    def arity(self) -> int:
        return len(self.params)

    def __call__(self, *args: Any) -> Any:
        return eval_with_tco(self, args)

    def __repr__(self) -> str:
        return f"<function {self.name}/{self.arity}>"


@dataclass
class TailCall:
    fn: Any
    args: tuple[Any, ...]


_UNSET = object()


class GeniaRef:
    def __init__(self, initial: Any = _UNSET):
        self._condition = threading.Condition()
        self._value = initial
        self._is_set = initial is not _UNSET

    def get(self) -> Any:
        with self._condition:
            while not self._is_set:
                self._condition.wait()
            return self._value

    def set(self, value: Any) -> Any:
        with self._condition:
            self._value = value
            self._is_set = True
            self._condition.notify_all()
            return value

    def update(self, fn: Any) -> Any:
        with self._condition:
            while not self._is_set:
                self._condition.wait()
            self._value = fn(self._value)
            self._condition.notify_all()
            return self._value

    def __repr__(self) -> str:
        with self._condition:
            if self._is_set:
                return f"<ref {self._value!r}>"
            return "<ref <unset>>"


def eval_with_tco(fn: Any, args: tuple[Any, ...]) -> Any:
    current_fn = fn
    current_args = args

    while True:
        if isinstance(current_fn, GeniaFunction):
            if len(current_args) != current_fn.arity:
                raise TypeError(f"{current_fn.name} expected {current_fn.arity} args, got {len(current_args)}")
            frame = Env(current_fn.closure)
            for p, a in zip(current_fn.params, current_args):
                frame.set(p, a)
            result = Evaluator(frame).eval_function_body(
                current_fn.params,
                current_args,
                current_fn.body,
                current_fn.name,
            )
        else:
            result = current_fn(*current_args)

        if isinstance(result, TailCall):
            current_fn = result.fn
            current_args = result.args
            continue
        return result


class Evaluator:
    def __init__(self, env: Env):
        self.env = env

    def eval_program(self, nodes: Iterable[IrNode]) -> Any:
        result = None
        for node in nodes:
            result = self.eval(node)
        return result

    def eval_function_body(
        self,
        params: list[str],
        args: tuple[Any, ...],
        body: IrNode,
        fn_name: str | None = None,
    ) -> Any:
        if isinstance(body, IrListTraversalLoop):
            return self.eval_list_traversal_loop(params, args, body)
        if isinstance(body, IrCase):
            return self.eval_case_expr(args, body, fn_name)
        if isinstance(body, IrBlock):
            # If the final expr is a case expr, it matches against function args.
            for expr in body.exprs[:-1]:
                self.eval(expr)
            if not body.exprs:
                return None
            last = body.exprs[-1]
            if isinstance(last, IrCase):
                return self.eval_case_expr(args, last, fn_name)
            return self.eval_tail(last)
        return self.eval_tail(body)

    def eval_list_traversal_loop(self, params: list[str], args: tuple[Any, ...], body: IrListTraversalLoop) -> Any:
        values = dict(zip(params, args))
        n_value = values.get(body.counter_var)
        xs_value = values.get(body.list_var)

        while True:
            current_args = (n_value, xs_value)
            if not isinstance(xs_value, list) or len(xs_value) == 0:
                match_env = self.match_pattern(body.empty_clause.pattern, current_args)
                if match_env is None:
                    return None
                local = Env(self.env)
                for k, v in match_env.items():
                    local.set(k, v)
                return Evaluator(local).eval_tail(body.empty_clause.result)

            if n_value == 0:
                match_env = self.match_pattern(body.zero_clause.pattern, current_args)
                if match_env is None:
                    return None
                local = Env(self.env)
                for k, v in match_env.items():
                    local.set(k, v)
                return Evaluator(local).eval_tail(body.zero_clause.result)

            if not isinstance(n_value, (int, float)):
                return None
            if n_value < 0:
                return None
            n_value = n_value - body.step_size
            xs_value = xs_value[body.step_size:]

    def eval_case_expr(self, args: tuple[Any, ...], case_expr: IrCase, fn_name: str | None = None) -> Any:
        for clause in case_expr.clauses:
            match_env = self.match_pattern(clause.pattern, args)
            if match_env is None:
                continue
            local = Env(self.env)
            for k, v in match_env.items():
                local.set(k, v)
            if clause.guard is not None and not Evaluator(local).eval(clause.guard):
                continue
            return Evaluator(local).eval_tail(clause.result)
        if fn_name is not None:
            raise RuntimeError(
                f"No matching case for function {fn_name}/{len(args)} with arguments {args!r}"
            )
        raise RuntimeError(f"No matching case for arguments {args!r}")

    def eval_tail(self, node: IrNode) -> Any:
        if isinstance(node, IrCall):
            return self.eval_call(node, tail_position=True)
        if isinstance(node, IrBlock):
            local = Env(self.env)
            ev = Evaluator(local)
            for expr in node.exprs[:-1]:
                ev.eval(expr)
            if not node.exprs:
                return None
            return ev.eval_tail(node.exprs[-1])
        return self.eval(node)

    def eval_call(self, node: IrCall, tail_position: bool) -> Any:
        args = [self.eval(a) for a in node.args]

        if isinstance(node.fn, IrVar):
            name = node.fn.name
            try:
                fn = self.env.get(name)
            except NameError:
                if self.env.try_autoload(name, len(args)):
                    fn = self.env.get(name)
                else:
                    raise
        else:
            fn = self.eval(node.fn)

        if isinstance(fn, dict) and all(isinstance(k, int) for k in fn):
            arity = len(args)
            target = fn.get(arity)

            if target is None and isinstance(node.fn, IrVar):
                if self.env.try_autoload(node.fn.name, arity):
                    fn = self.env.get(node.fn.name)
                    if isinstance(fn, dict) and all(isinstance(k, int) for k in fn):
                        target = fn.get(arity)

            if target is None:
                callee = node.fn.name if isinstance(node.fn, IrVar) else "function"
                available = ", ".join(f"{callee}/{n}" for n in sorted(fn))
                raise TypeError(f"No matching function: {callee}/{arity}. Available: {available}")
            return TailCall(target, tuple(args)) if tail_position else target(*args)

        return TailCall(fn, tuple(args)) if tail_position else fn(*args)

    def match_pattern(self, pattern: IrPattern, args: tuple[Any, ...]) -> Optional[dict[str, Any]]:
        # full parameter tuple matching
        if isinstance(pattern, IrPatTuple):
            if len(pattern.items) != len(args):
                return None
            env: dict[str, Any] = {}
            for pat, arg in zip(pattern.items, args):
                sub = self.match_pattern_atom(pat, arg)
                if sub is None:
                    return None
                for k, v in sub.items():
                    if k in env and env[k] != v:
                        return None
                    env[k] = v
            return env
        # single-parameter shorthand
        if len(args) != 1:
            return None
        return self.match_pattern_atom(pattern, args[0])

    def match_pattern_atom(self, pattern: IrPattern, arg: Any) -> Optional[dict[str, Any]]:
        if isinstance(pattern, IrPatLiteral):
            return {} if pattern.value == arg else None
        if isinstance(pattern, IrPatWildcard):
            return {}
        if isinstance(pattern, IrPatRest):
            return {pattern.name: arg} if pattern.name is not None else {}
        if isinstance(pattern, IrPatBind):
            return {pattern.name: arg}
        if isinstance(pattern, IrPatList):
            if not isinstance(arg, list):
                return None

            rest_index = None
            for i, pat in enumerate(pattern.items):
                if isinstance(pat, IrPatRest):
                    rest_index = i
                    break

            if rest_index is None:
                if len(pattern.items) != len(arg):
                    return None
                env: dict[str, Any] = {}
                for pat, item in zip(pattern.items, arg):
                    sub = self.match_pattern_atom(pat, item)
                    if sub is None:
                        return None
                    for k, v in sub.items():
                        if k in env and env[k] != v:
                            return None
                        env[k] = v
                return env

            prefix = pattern.items[:rest_index]
            rest_pat = pattern.items[rest_index]

            if len(arg) < len(prefix):
                return None

            env: dict[str, Any] = {}
            for pat, item in zip(prefix, arg[:len(prefix)]):
                sub = self.match_pattern_atom(pat, item)
                if sub is None:
                    return None
                for k, v in sub.items():
                    if k in env and env[k] != v:
                        return None
                    env[k] = v

            sub = self.match_pattern_atom(rest_pat, arg[len(prefix):])
            if sub is None:
                return None
            for k, v in sub.items():
                if k in env and env[k] != v:
                    return None
                env[k] = v
            return env
        raise RuntimeError(f"Unsupported pattern: {pattern!r}")

    def eval(self, node: IrNode) -> Any:
        if isinstance(node, IrExprStmt):
            return self.eval(node.expr)
        if isinstance(node, IrLiteral):
            return node.value
        if isinstance(node, IrList):
            return [self.eval(item) for item in node.items]
        if isinstance(node, IrVar):
            return self.env.get(node.name)
        if isinstance(node, IrUnary):
            value = self.eval(node.expr)
            if node.op == "MINUS":
                return -value
            if node.op == "BANG":
                return not truthy(value)
            raise RuntimeError(f"Unknown unary operator {node.op}")
        if isinstance(node, IrBinary):
            return self.eval_binary(node)
        if isinstance(node, IrCall):
            return self.eval_call(node, tail_position=False)

        if isinstance(node, IrBlock):
            local = Env(self.env)
            result = None
            ev = Evaluator(local)
            for expr in node.exprs:
                result = ev.eval(expr)
            return result
        if isinstance(node, IrLambda):
            params = node.params
            body = node.body
            closure = self.env

            def fn(*args):
                if len(args) != len(params):
                    raise TypeError(f"lambda expected {len(params)} args, got {len(args)}")
                frame = Env(closure)
                for p, a in zip(params, args):
                    frame.set(p, a)
                return Evaluator(frame).eval(body)

            return fn

        if isinstance(node, IrAssign):
            value = self.eval(node.expr)
            self.env.set(node.name, value)
            return value

        if isinstance(node, IrFuncDef):
            fn = GeniaFunction(node.name, node.params, node.body, self.env)
            self.env.define_function(fn)
            return fn
        if isinstance(node, IrCase):
            raise RuntimeError("Standalone case expressions are only valid as function bodies or final block expressions")
        if isinstance(node, IrListTraversalLoop):
            raise RuntimeError("Optimized list traversal nodes are only valid as function bodies")
        raise RuntimeError(f"Unknown node: {node!r}")

    def eval_binary(self, node: IrBinary) -> Any:
        left = self.eval(node.left)
        if node.op == "AND":
            return left and self.eval(node.right)
        if node.op == "OR":
            return left or self.eval(node.right)
        right = self.eval(node.right)
        match node.op:
            case "PLUS":
                return left + right
            case "MINUS":
                return left - right
            case "STAR":
                return left * right
            case "SLASH":
                return left / right
            case "PERCENT":
                return left % right
            case "LT":
                return left < right
            case "LE":
                return left <= right
            case "GT":
                return left > right
            case "GE":
                return left >= right
            case "EQEQ":
                return left == right
            case "NE":
                return left != right
            case _:
                raise RuntimeError(f"Unknown binary operator {node.op}")


def truthy(value: Any) -> bool:
    return bool(value)


# -----------------------------
# Builtins / REPL
# -----------------------------

def make_global_env(
    stdin_data: Optional[list[str]] = None,
    stdin_provider: Optional[Callable[[], list[str]]] = None,
) -> Env:
    env = Env()

    def log(*args: Any) -> Any:
        print(*args)
        return args[-1] if args else None

    def print_fn(*args: Any) -> Any:
        print(*args)
        return args[-1] if args else None

    def input_fn(prompt: str = "") -> str:
        return input(prompt)

    stdin_cache: Optional[list[str]] = None

    def stdin_fn() -> list[str]:
        nonlocal stdin_cache
        if stdin_cache is None:
            if stdin_provider is not None:
                stdin_cache = stdin_provider()
            elif stdin_data is not None:
                stdin_cache = stdin_data
            else:
                stdin_cache = sys.stdin.read().splitlines()
        return stdin_cache

    def help_fn() -> None:
        print(
            """
Genia prototype help
--------------------
Examples:
  1 + 2 * 3
  square(x) = x * x
  square(5)

  fact(n) =
    0 -> 1 |
    n -> n * fact(n - 1)

  fact2(n) {
    log(n)
    0 -> 1 |
    n -> n * fact2(n - 1)
  }

  add() = 0

  add(x, y) =
    (0, y) -> y |
    (x, 0) -> x |
    (x, y) -> x + y

  print(stdin())
  count([1, 2, 3])
  print([1, 2, 3])

  first_pair(xs) =
    [a, b] -> a + b

  describe(xs) =
    [] -> "empty" |
    [x] -> "one" |
    [x, y] -> "two"

Commands:
  :quit   exit
  :env    show defined names
  :help   show this help
""".strip()
        )

    def ref_fn(*args: Any) -> GeniaRef:
        if len(args) == 0:
            return GeniaRef()
        if len(args) == 1:
            return GeniaRef(args[0])
        raise TypeError(f"ref expected 0 or 1 args, got {len(args)}")

    def ref_get_fn(ref_value: Any) -> Any:
        if not isinstance(ref_value, GeniaRef):
            raise TypeError("ref_get expected a ref")
        return ref_value.get()

    def ref_set_fn(ref_value: Any, value: Any) -> Any:
        if not isinstance(ref_value, GeniaRef):
            raise TypeError("ref_set expected a ref as first argument")
        return ref_value.set(value)

    def ref_update_fn(ref_value: Any, updater: Any) -> Any:
        if not isinstance(ref_value, GeniaRef):
            raise TypeError("ref_update expected a ref as first argument")
        if not callable(updater):
            raise TypeError("ref_update expected a function as second argument")
        return ref_value.update(updater)

    env.set("log", log)
    env.set("print", print_fn)
    env.set("input", input_fn)
    env.set("stdin", stdin_fn)
    env.set("help", help_fn)
    env.set("pi", math.pi)
    env.set("e", math.e)
    env.set("true", True)
    env.set("false", False)
    env.set("nil", None)
    env.set("ref", ref_fn)
    env.set("ref_get", ref_get_fn)
    env.set("ref_set", ref_set_fn)
    env.set("ref_update", ref_update_fn)

    env.register_autoload("reduce", 3, "std/prelude/list.genia")
    env.register_autoload("count", 1, "std/prelude/list.genia")
    env.register_autoload("any?", 2, "std/prelude/list.genia")
    env.register_autoload("nth", 2, "std/prelude/list.genia")
    env.register_autoload("take", 2, "std/prelude/list.genia")
    env.register_autoload("drop", 2, "std/prelude/list.genia")
    env.register_autoload("sum", 1, "std/prelude/math.genia")
    return env


def is_complete(source: str) -> bool:
    brace = paren = bracket = 0
    in_str: Optional[str] = None
    esc = False
    for ch in source:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
            continue
        if ch in ('"', "'"):
            in_str = ch
        elif ch == '{':
            brace += 1
        elif ch == '}':
            brace -= 1
        elif ch == '(':
            paren += 1
        elif ch == ')':
            paren -= 1
        elif ch == '[':
            bracket += 1
        elif ch == ']':
            bracket -= 1
    if in_str or brace > 0 or paren > 0 or bracket > 0:
        return False
    # If the last nonblank line ends with =, |, -> or ?, keep reading.
    lines = [ln.rstrip() for ln in source.splitlines() if ln.strip()]
    if not lines:
        return True
    last = lines[-1].rstrip()
    return not (last.endswith("=") or last.endswith("|") or last.endswith("->") or last.endswith("?"))


def run_source(source: str, env: Env) -> Any:
    tokens = lex(source)
    parser = Parser(tokens)
    ast_nodes = parser.parse_program()
    ir_nodes = lower_program(ast_nodes)
    ir_nodes = optimize_program(ir_nodes, debug=os.getenv("GENIA_DEBUG_OPT", "") == "1")
    return Evaluator(env).eval_program(ir_nodes)


def repl() -> None:
    env = make_global_env([])
    print("Genia prototype REPL. Type :help for examples, :quit to exit.")
    buf = ""
    while True:
        try:
            prompt = "... " if buf else ">>> "
            line = input(prompt)
        except EOFError:
            print()
            break
        if not buf and line.strip() == ":quit":
            break
        if not buf and line.strip() == ":help":
            env.get("help")()
            continue
        if not buf and line.strip() == ":env":
            for k in sorted(env.values):
                print(f"{k} = {env.values[k]!r}")
            continue
        buf += line + "\n"
        if not is_complete(buf):
            continue
        source = buf
        buf = ""
        if not source.strip():
            continue
        try:
            result = run_source(source, env)
            if result is not None:
                print(repr(result))
        except Exception as e:  # noqa: BLE001
            print(f"Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        env = make_global_env()
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            result = run_source(f.read(), env)
        if result is not None:
            print(repr(result))
    else:
        repl()
