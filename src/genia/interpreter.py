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
import bisect
import json
import queue
import random
import time
import zipfile
from pathlib import Path
import argparse
import re
import sys
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Optional

if __package__ in (None, ""):
    _src_root = Path(__file__).resolve().parents[1]
    if str(_src_root) not in sys.path:
        sys.path.insert(0, str(_src_root))
    from genia.utf8 import (
        format_debug,
        format_display,
        utf8_byte_length,
    )
    from genia.docstrings import render_markdown_docstring
else:
    from .docstrings import render_markdown_docstring
    from .utf8 import (
        format_debug,
        format_display,
        utf8_byte_length,
    )

BASE_DIR = Path(__file__).resolve().parents[2] if "__file__" in globals() else Path.cwd()


# -----------------------------
# Lexer
# -----------------------------

# Single source of truth for symbol/operator policy:
# - These characters are always token delimiters/operators in Genia.
# - Clojure-style symbol punctuation that we allow in names is listed below.
# - `name?` and `name!` are ordinary identifiers (no special lexer semantics).
# - `/` is reserved for division and is not allowed inside identifier names.
ALWAYS_OPERATOR_DELIMITERS = frozenset({"+", "*", "/", "%", "=", "<", ">", "|", ",", ";", "(", ")", "{", "}", "[", "]"})
ALLOWED_SYMBOL_PUNCTUATION = frozenset({"_", "?", "!", ".", ":", "$", "-"})
IDENT_START_RE = re.compile(r"[A-Za-z_$]")
IDENT_BODY_RE = re.compile(r"[A-Za-z0-9]")

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
    ("PIPE_FWD", r"\|>"),
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
    ("PIPE_FWD", "|>"),
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
def _is_identifier_start(ch: str) -> bool:
    if ch == "$":
        return True
    return bool(IDENT_START_RE.fullmatch(ch))


def _is_identifier_part(ch: str) -> bool:
    if IDENT_BODY_RE.fullmatch(ch):
        return True
    if ch in ALWAYS_OPERATOR_DELIMITERS:
        return False
    return ch in ALLOWED_SYMBOL_PUNCTUATION


@dataclass
class Token:
    kind: str
    text: str
    pos: int


@dataclass(frozen=True)
class SourceSpan:
    filename: str
    line: int
    column: int
    end_line: int
    end_column: int


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

        if source.startswith('glob"', pos):
            literal_start = pos + 4
            i = literal_start + 1
            while i < length:
                if source[i] == "\\":
                    i += 2
                    continue
                if source[i] == '"':
                    text = source[pos:i + 1]
                    tokens.append(Token("GLOB", text, pos))
                    pos = i + 1
                    break
                i += 1
            else:
                raise SyntaxError(f"Unterminated glob pattern literal at {pos}")
            continue

        if ch in "\"'":
            if source.startswith(ch * 3, pos):
                delim = ch * 3
                i = pos + 3
                while i < length:
                    if source.startswith(delim, i):
                        text = source[pos:i + 3]
                        tokens.append(Token("STRING", text, pos))
                        pos = i + 3
                        break
                    if source[i] == "\\":
                        i += 2
                        continue
                    i += 1
                else:
                    raise SyntaxError(f"Unterminated triple-quoted string at {pos}")
            else:
                string_match = STRING_RE.match(source, pos)
                if string_match is None:
                    raise SyntaxError(f"Unexpected character {ch!r} at {pos}")
                text = string_match.group()
                tokens.append(Token("STRING", text, pos))
                pos += len(text)
            continue

        if _is_identifier_start(ch):
            ident_start = pos
            pos += 1
            while pos < length and _is_identifier_part(source[pos]):
                if source[pos] == "-" and pos + 1 < length and source[pos + 1] == ">":
                    break
                pos += 1
            tokens.append(Token("IDENT", source[ident_start:pos], ident_start))
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
        raise SyntaxError(f"Unexpected character {source[pos]!r} at {pos}")

    tokens.append(Token("EOF", "", len(source)))
    return tokens


def parse_string_literal(text: str) -> str:
    if text.startswith('"""') and text.endswith('"""') and len(text) >= 6:
        quote = '"'
        content = text[3:-3]
    elif text.startswith("'''") and text.endswith("'''") and len(text) >= 6:
        quote = "'"
        content = text[3:-3]
    elif len(text) >= 2 and text[0] in "\"'" and text[-1] == text[0]:
        quote = text[0]
        content = text[1:-1]
    else:
        raise SyntaxError(f"Invalid string literal: {text!r}")
    out: list[str] = []
    i = 0
    while i < len(content):
        ch = content[i]
        if ch != "\\":
            out.append(ch)
            i += 1
            continue

        i += 1
        if i >= len(content):
            raise SyntaxError("Trailing backslash in string literal")
        esc = content[i]
        i += 1

        if esc == "n":
            out.append("\n")
        elif esc == "r":
            out.append("\r")
        elif esc == "t":
            out.append("\t")
        elif esc == "\\":
            out.append("\\")
        elif esc == "\"":
            out.append("\"")
        elif esc == "'":
            out.append("'")
        elif esc == "u":
            if i + 4 > len(content):
                raise SyntaxError("Invalid \\u escape in string literal")
            hex_part = content[i:i + 4]
            if not re.fullmatch(r"[0-9A-Fa-f]{4}", hex_part):
                raise SyntaxError("Invalid \\u escape in string literal")
            out.append(chr(int(hex_part, 16)))
            i += 4
        elif esc == quote:
            out.append(quote)
        else:
            raise SyntaxError(f"Unsupported escape sequence: \\{esc}")
    return "".join(out)


def parse_glob_literal(text: str) -> str:
    if not (text.startswith('glob"') and text.endswith('"') and len(text) >= 6):
        raise SyntaxError(f"Invalid glob literal: {text!r}")
    content = text[5:-1]
    out: list[str] = []
    i = 0
    while i < len(content):
        ch = content[i]
        if ch != "\\":
            out.append(ch)
            i += 1
            continue
        i += 1
        if i >= len(content):
            raise SyntaxError("Invalid glob literal: trailing backslash")
        esc = content[i]
        i += 1
        if esc in {"*", "?", "[", "]", "\\"}:
            out.append("\\" + esc)
            continue
        raise SyntaxError(f"Invalid glob literal escape: \\{esc}")
    return "".join(out)


@dataclass(frozen=True)
class GlobClassEntry:
    start: str
    end: str


@dataclass(frozen=True)
class GlobToken:
    kind: str
    value: Any = None


@dataclass(frozen=True)
class CompiledGlobPattern:
    source: str
    tokens: tuple[GlobToken, ...]


def compile_glob_pattern(text: str) -> CompiledGlobPattern:
    tokens: list[GlobToken] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\":
            if i + 1 >= len(text):
                raise SyntaxError("Invalid glob pattern: trailing backslash")
            tokens.append(GlobToken("LITERAL", text[i + 1]))
            i += 2
            continue
        if ch == "*":
            if not tokens or tokens[-1].kind != "STAR":
                tokens.append(GlobToken("STAR"))
            i += 1
            continue
        if ch == "?":
            tokens.append(GlobToken("ANY_ONE"))
            i += 1
            continue
        if ch == "[":
            token, i = _parse_glob_class(text, i)
            tokens.append(token)
            continue
        tokens.append(GlobToken("LITERAL", ch))
        i += 1
    return CompiledGlobPattern(source=text, tokens=tuple(tokens))


def _parse_glob_class(text: str, start_idx: int) -> tuple[GlobToken, int]:
    i = start_idx + 1
    if i >= len(text):
        raise SyntaxError("Invalid glob pattern: unterminated character class")
    negated = False
    if text[i] == "!":
        negated = True
        i += 1
    entries: list[GlobClassEntry] = []
    saw_entry = False
    pending_literal: str | None = None

    while i < len(text):
        ch = text[i]
        if ch == "]":
            if pending_literal is not None:
                entries.append(GlobClassEntry(pending_literal, pending_literal))
                pending_literal = None
                saw_entry = True
            if not saw_entry:
                raise SyntaxError("Invalid glob pattern: empty character class")
            return GlobToken("CLASS", (negated, tuple(entries))), i + 1

        if ch == "\\":
            if i + 1 >= len(text):
                raise SyntaxError("Invalid glob pattern: trailing backslash in character class")
            literal = text[i + 1]
            i += 2
        else:
            literal = ch
            i += 1

        if pending_literal is None:
            pending_literal = literal
            continue

        if literal == "-" and i < len(text) and text[i] != "]":
            if text[i] == "\\":
                if i + 1 >= len(text):
                    raise SyntaxError("Invalid glob pattern: trailing backslash in range")
                range_end = text[i + 1]
                i += 2
            else:
                range_end = text[i]
                i += 1
            if ord(pending_literal) > ord(range_end):
                raise SyntaxError("Invalid glob pattern: descending character range")
            entries.append(GlobClassEntry(pending_literal, range_end))
            pending_literal = None
            saw_entry = True
            continue

        entries.append(GlobClassEntry(pending_literal, pending_literal))
        pending_literal = literal
        saw_entry = True

    raise SyntaxError("Invalid glob pattern: unterminated character class")


def glob_match(compiled: CompiledGlobPattern, value: str) -> bool:
    tokens = compiled.tokens
    memo: dict[tuple[int, int], bool] = {}

    def go(tok_i: int, str_i: int) -> bool:
        key = (tok_i, str_i)
        if key in memo:
            return memo[key]
        if tok_i == len(tokens):
            memo[key] = str_i == len(value)
            return memo[key]
        token = tokens[tok_i]
        if token.kind == "STAR":
            memo[key] = go(tok_i + 1, str_i) or (str_i < len(value) and go(tok_i, str_i + 1))
            return memo[key]
        if str_i >= len(value):
            memo[key] = False
            return False
        ch = value[str_i]
        if token.kind == "LITERAL":
            memo[key] = ch == token.value and go(tok_i + 1, str_i + 1)
            return memo[key]
        if token.kind == "ANY_ONE":
            memo[key] = go(tok_i + 1, str_i + 1)
            return memo[key]
        if token.kind == "CLASS":
            negated, entries = token.value
            in_class = any(entry.start <= ch <= entry.end for entry in entries)
            if negated:
                in_class = not in_class
            memo[key] = in_class and go(tok_i + 1, str_i + 1)
            return memo[key]
        raise RuntimeError(f"Unsupported compiled glob token: {token.kind}")

    return go(0, 0)


# -----------------------------
# AST
# -----------------------------

class Node:
    pass


@dataclass
class Number(Node):
    value: int | float
    span: SourceSpan | None = None


@dataclass
class String(Node):
    value: str
    span: SourceSpan | None = None


@dataclass
class Boolean(Node):
    value: bool
    span: SourceSpan | None = None


@dataclass
class Nil(Node):
    span: SourceSpan | None = None


@dataclass
class Var(Node):
    name: str
    span: SourceSpan | None = None


@dataclass
class Unary(Node):
    op: str
    expr: Node
    span: SourceSpan | None = None


@dataclass
class Binary(Node):
    left: Node
    op: str
    right: Node
    span: SourceSpan | None = None


@dataclass
class Call(Node):
    fn: Node
    args: list[Node]
    span: SourceSpan | None = None


@dataclass
class ExprStmt(Node):
    expr: Node
    span: SourceSpan | None = None


@dataclass
class Block(Node):
    exprs: list[Node]
    span: SourceSpan | None = None


@dataclass
class ListLiteral(Node):
    items: list[Node]
    span: SourceSpan | None = None


@dataclass
class Spread(Node):
    expr: Node
    span: SourceSpan | None = None


@dataclass
class ListPattern(Node):
    items: list[Node]
    span: SourceSpan | None = None


@dataclass
class GlobPattern(Node):
    pattern: str
    span: SourceSpan | None = None


@dataclass
class WildcardPattern(Node):
    span: SourceSpan | None = None


@dataclass
class RestPattern(Node):
    name: str | None
    span: SourceSpan | None = None


@dataclass
class TuplePattern(Node):
    items: list[Node]
    span: SourceSpan | None = None


@dataclass
class CaseClause(Node):
    pattern: Node
    guard: Optional[Node]
    result: Node
    span: SourceSpan | None = None


@dataclass
class CaseExpr(Node):
    clauses: list[CaseClause]
    span: SourceSpan | None = None


@dataclass
class Lambda(Node):
    params: list[str]
    rest_param: str | None
    body: Node
    span: SourceSpan | None = None


@dataclass
class Assign(Node):
    name: str
    expr: Node
    span: SourceSpan | None = None


@dataclass
class FuncDef(Node):
    name: str
    params: list[str]
    rest_param: str | None
    docstring: str | None
    body: Node
    span: SourceSpan | None = None


# -----------------------------
# Tiny IR
# -----------------------------

class IrNode:
    """Base type for lowered Genia IR nodes."""


@dataclass
class IrLiteral(IrNode):
    """Normalized constant value (number/string/bool/nil)."""

    value: Any
    span: SourceSpan | None = None


@dataclass
class IrVar(IrNode):
    """Variable read by name (kept explicit for analysis and rewriting)."""

    name: str
    span: SourceSpan | None = None


@dataclass
class IrUnary(IrNode):
    """Unary operator application."""

    op: str
    expr: IrNode
    span: SourceSpan | None = None


@dataclass
class IrBinary(IrNode):
    """Binary operator application with explicit operands."""

    left: IrNode
    op: str
    right: IrNode
    span: SourceSpan | None = None


@dataclass
class IrCall(IrNode):
    """Function call where callee and args are already lowered."""

    fn: IrNode
    args: list[IrNode]
    span: SourceSpan | None = None


@dataclass
class IrExprStmt(IrNode):
    """Top-level expression statement (keeps source ordering explicit)."""

    expr: IrNode
    span: SourceSpan | None = None


@dataclass
class IrBlock(IrNode):
    """Sequential expression block."""

    exprs: list[IrNode]
    span: SourceSpan | None = None


@dataclass
class IrList(IrNode):
    """List literal with lowered items."""

    items: list[IrNode]
    span: SourceSpan | None = None


@dataclass
class IrSpread(IrNode):
    """List spread element in expression contexts (list literals and call args)."""

    expr: IrNode
    span: SourceSpan | None = None


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
class IrPatGlob(IrPattern):
    """Whole-string glob pattern matcher."""

    matcher: "CompiledGlobPattern"


@dataclass
class IrCaseClause(IrNode):
    """Single case arm with optional guard."""

    pattern: IrPattern
    guard: Optional[IrNode]
    result: IrNode
    span: SourceSpan | None = None


@dataclass
class IrCase(IrNode):
    """Case dispatch is explicit so optimization passes can inspect patterns."""

    clauses: list[IrCaseClause]
    span: SourceSpan | None = None


@dataclass
class IrLambda(IrNode):
    """Lambda expression with params and lowered body."""

    params: list[str]
    rest_param: str | None
    body: IrNode
    span: SourceSpan | None = None


@dataclass
class IrAssign(IrNode):
    """Top-level assignment side effect."""

    name: str
    expr: IrNode
    span: SourceSpan | None = None


@dataclass
class IrFuncDef(IrNode):
    """Named function definition with lowered body."""

    name: str
    params: list[str]
    rest_param: str | None
    docstring: str | None
    body: IrNode
    span: SourceSpan | None = None


@dataclass
class IrListTraversalLoop(IrNode):
    """Optimized loop-like form for nth-style list traversal recursion."""

    counter_var: str
    list_var: str
    step_size: int
    empty_clause: IrCaseClause
    zero_clause: IrCaseClause
    span: SourceSpan | None = None


def lower_program(nodes: Iterable[Node]) -> list[IrNode]:
    return [lower_node(node) for node in nodes]


def lower_node(node: Node) -> IrNode:
    if isinstance(node, ExprStmt):
        return IrExprStmt(lower_node(node.expr), span=node.span)
    if isinstance(node, Number):
        return IrLiteral(node.value, span=node.span)
    if isinstance(node, String):
        return IrLiteral(node.value, span=node.span)
    if isinstance(node, Boolean):
        return IrLiteral(node.value, span=node.span)
    if isinstance(node, Nil):
        return IrLiteral(None, span=node.span)
    if isinstance(node, Var):
        return IrVar(node.name, span=node.span)
    if isinstance(node, Unary):
        return IrUnary(node.op, lower_node(node.expr), span=node.span)
    if isinstance(node, Binary):
        if node.op == "PIPE_FWD":
            lowered_left = lower_node(node.left)
            lowered_right = lower_node(node.right)
            if isinstance(lowered_right, IrCall):
                return IrCall(lowered_right.fn, [*lowered_right.args, lowered_left], span=node.span)
            return IrCall(lowered_right, [lowered_left], span=node.span)
        return IrBinary(lower_node(node.left), node.op, lower_node(node.right), span=node.span)
    if isinstance(node, Call):
        return IrCall(lower_node(node.fn), [lower_node(arg) for arg in node.args], span=node.span)
    if isinstance(node, Block):
        return IrBlock([lower_node(expr) for expr in node.exprs], span=node.span)
    if isinstance(node, ListLiteral):
        return IrList([lower_node(item) for item in node.items], span=node.span)
    if isinstance(node, Spread):
        return IrSpread(lower_node(node.expr), span=node.span)
    if isinstance(node, CaseExpr):
        return IrCase(
            [
                IrCaseClause(
                    lower_pattern(clause.pattern),
                    lower_node(clause.guard) if clause.guard is not None else None,
                    lower_node(clause.result),
                    span=clause.span,
                )
                for clause in node.clauses
            ],
            span=node.span,
        )
    if isinstance(node, Lambda):
        return IrLambda(node.params, node.rest_param, lower_node(node.body), span=node.span)
    if isinstance(node, Assign):
        return IrAssign(node.name, lower_node(node.expr), span=node.span)
    if isinstance(node, FuncDef):
        return IrFuncDef(
            node.name,
            node.params,
            node.rest_param,
            node.docstring,
            lower_node(node.body),
            span=node.span,
        )
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
    if isinstance(pattern, GlobPattern):
        return IrPatGlob(compile_glob_pattern(pattern.pattern))
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
    if fn.rest_param is not None or len(fn.params) != 2 or not isinstance(fn.body, IrCase):
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
        fn.rest_param,
        fn.docstring,
        IrListTraversalLoop(
            counter_var=fn.params[0],
            list_var=fn.params[1],
            step_size=1,
            empty_clause=empty_clause,
            zero_clause=zero_clause,
            span=fn.span,
        ),
        span=fn.span,
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
    "PIPE_FWD": 5,
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

RESERVED_LITERAL_IDENTIFIERS = frozenset({"true", "false", "nil"})


class Parser:
    def __init__(self, tokens: list[Token], source: str = "", filename: str = "<memory>"):
        self.tokens = tokens
        self.source = source
        self.filename = filename
        self.i = 0
        self._line_starts = [0]
        for idx, ch in enumerate(source):
            if ch == "\n":
                self._line_starts.append(idx + 1)

    def _line_col(self, pos: int) -> tuple[int, int]:
        line_idx = bisect.bisect_right(self._line_starts, pos) - 1
        line_start = self._line_starts[line_idx]
        return line_idx + 1, pos - line_start + 1

    def span_for_tokens(self, start_tok: Token, end_tok: Token) -> SourceSpan:
        end_pos = end_tok.pos + max(len(end_tok.text) - 1, 0)
        line, col = self._line_col(start_tok.pos)
        end_line, end_col = self._line_col(end_pos)
        return SourceSpan(self.filename, line, col, end_line, end_col)

    def merge_spans(self, start: SourceSpan | None, end: SourceSpan | None) -> SourceSpan | None:
        if start is None:
            return end
        if end is None:
            return start
        return SourceSpan(start.filename, start.line, start.column, end.end_line, end.end_column)

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

    def skip_newlines(self) -> None:
        while self.at("NEWLINE"):
            self.i += 1

    def validate_parameter_name(self, tok: Token, *, context: str, allow_wildcard: bool = False) -> str:
        name = tok.text
        if name in RESERVED_LITERAL_IDENTIFIERS:
            raise SyntaxError(f"{context} cannot use reserved literal {name!r} as a parameter at {tok.pos}")
        if name == "_" and not allow_wildcard:
            raise SyntaxError(f"{context} cannot use '_' as a parameter name at {tok.pos}")
        return name

    def function_header_has_body_starter(self, start_index: int) -> bool:
        j = start_index + 1
        if j >= len(self.tokens) or self.tokens[j].kind != "LPAREN":
            return False
        depth = 0
        while j < len(self.tokens):
            kind = self.tokens[j].kind
            if kind == "LPAREN":
                depth += 1
            elif kind == "RPAREN":
                depth -= 1
                if depth == 0:
                    j += 1
                    while j < len(self.tokens) and self.tokens[j].kind == "NEWLINE":
                        j += 1
                    return j < len(self.tokens) and self.tokens[j].kind in {"ASSIGN", "LBRACE"}
            elif kind == "EOF":
                return False
            j += 1
        return False

    def parenthesized_intro_has_arrow(self, start_index: int) -> bool:
        if start_index >= len(self.tokens) or self.tokens[start_index].kind != "LPAREN":
            return False
        j = start_index
        depth = 0
        while j < len(self.tokens):
            kind = self.tokens[j].kind
            if kind == "LPAREN":
                depth += 1
            elif kind == "RPAREN":
                depth -= 1
                if depth == 0:
                    j += 1
                    while j < len(self.tokens) and self.tokens[j].kind == "NEWLINE":
                        j += 1
                    return j < len(self.tokens) and self.tokens[j].kind == "ARROW"
            elif kind == "EOF":
                return False
            j += 1
        return False

    def parse_program(self) -> list[Node]:
        out: list[Node] = []
        self.skip_separators()
        while not self.at("EOF"):
            out.append(self.parse_toplevel())
            self.skip_separators()
        return out

    def parse_parameter_list(
        self,
        *,
        context: str,
        allow_wildcard: bool = False,
    ) -> tuple[list[str], str | None]:
        params: list[str] = []
        rest_param: str | None = None
        if self.at("RPAREN"):
            return params, rest_param
        while True:
            if self.at("DOTDOT"):
                dotdot = self.eat("DOTDOT")
                if rest_param is not None:
                    raise SyntaxError(f"{context} can only have one rest parameter at {dotdot.pos}")
                if not self.at("IDENT"):
                    bad = self.peek()
                    raise SyntaxError(f"Invalid {context.lower()} rest parameter token {bad.text!r} ({bad.kind}) at {bad.pos}")
                rest_tok = self.eat("IDENT")
                rest_param = self.validate_parameter_name(rest_tok, context=context, allow_wildcard=allow_wildcard)
                self.skip_newlines()
                if self.at("COMMA"):
                    comma = self.eat("COMMA")
                    raise SyntaxError(f"{context} rest parameter must be final at {comma.pos}")
                break

            if not self.at("IDENT"):
                bad = self.peek()
                raise SyntaxError(f"Invalid {context.lower()} parameter token {bad.text!r} ({bad.kind}) at {bad.pos}")
            param_tok = self.eat("IDENT")
            params.append(self.validate_parameter_name(param_tok, context=context, allow_wildcard=allow_wildcard))
            if not self.maybe("COMMA"):
                break
            self.skip_newlines()
            if self.at("RPAREN"):
                break
            self.skip_newlines()
        return params, rest_param

    def try_parse_function_header(self) -> tuple[str, list[str], str | None, Token] | None:
        if not (self.at("IDENT") and self.peek(1).kind == "LPAREN"):
            return None

        save = self.i
        try:
            name_token = self.eat("IDENT")
            name = name_token.text
            self.eat("LPAREN")
            self.skip_newlines()
            params, rest_param = self.parse_parameter_list(context="Function definition")
            self.eat("RPAREN")
            self.skip_newlines()

            if self.at("ASSIGN", "LBRACE"):
                return name, params, rest_param, name_token

            self.i = save
            return None
        except SyntaxError:
            self.i = save
            if self.function_header_has_body_starter(save):
                raise
            return None

    def parse_toplevel(self) -> Node:
        header = self.try_parse_function_header()
        if header is not None:
            name, params, rest_param, name_tok = header

            if self.at("ASSIGN"):
                self.eat("ASSIGN")
                self.skip_separators()
                docstring: str | None = None
                if self.at("STRING"):
                    save = self.i
                    candidate = parse_string_literal(self.eat("STRING").text)
                    if self.at_expr_start():
                        docstring = candidate
                    else:
                        self.i = save
                body = self.parse_function_body_after_intro(len(params))
                return FuncDef(
                    name,
                    params,
                    rest_param,
                    docstring,
                    body,
                    span=self.merge_spans(self.span_for_tokens(name_tok, name_tok), body.span),
                )

            if self.at("LBRACE"):
                body = self.parse_block(allow_final_case=True)
                return FuncDef(
                    name,
                    params,
                    rest_param,
                    None,
                    body,
                    span=self.merge_spans(self.span_for_tokens(name_tok, name_tok), body.span),
                )

            raise SyntaxError("Internal parser error: expected function body")

        if self.at("IDENT") and self.peek(1).kind == "ASSIGN":
            name_tok = self.eat("IDENT")
            name = name_tok.text
            self.eat("ASSIGN")
            self.skip_separators()
            expr = self.parse_expr()
            return Assign(name, expr, span=self.merge_spans(self.span_for_tokens(name_tok, name_tok), expr.span))

        expr = self.parse_expr()
        return ExprStmt(expr, span=expr.span)

    def at_expr_start(self) -> bool:
        return self.at("NUMBER", "STRING", "IDENT", "MINUS", "BANG", "LPAREN", "LBRACK", "LBRACE")

    def leading_parenthesized_item_count_before_arrow(self) -> int | None:
        if not self.at("LPAREN"):
            return None
        j = self.i + 1
        nested_depth = 0
        item_count = 0
        in_item = False
        opening_kinds = {"LPAREN", "LBRACK", "LBRACE"}
        matching_close = {"LPAREN": "RPAREN", "LBRACK": "RBRACK", "LBRACE": "RBRACE"}
        close_stack: list[str] = []
        while j < len(self.tokens):
            tok = self.tokens[j]
            kind = tok.kind
            if nested_depth == 0 and kind == "RPAREN":
                if in_item:
                    item_count += 1
                j += 1
                while j < len(self.tokens) and self.tokens[j].kind == "NEWLINE":
                    j += 1
                if j >= len(self.tokens) or self.tokens[j].kind != "ARROW":
                    return None
                return item_count
            if kind == "EOF":
                return None
            if nested_depth == 0 and kind == "NEWLINE":
                j += 1
                continue
            if nested_depth == 0 and kind == "COMMA":
                if in_item:
                    item_count += 1
                    in_item = False
                j += 1
                continue

            in_item = True
            if kind in opening_kinds:
                close_stack.append(matching_close[kind])
                nested_depth += 1
            elif close_stack and kind == close_stack[-1]:
                close_stack.pop()
                nested_depth -= 1
            j += 1
        return None

    def parse_function_body_after_intro(self, param_count: int) -> Node:
        if self.looks_like_case_start():
            leading_tuple_arity = self.leading_parenthesized_item_count_before_arrow()
            if leading_tuple_arity is not None and leading_tuple_arity != param_count:
                return self.parse_expr()
            return self.parse_case_expr(single_param_shorthand_ok=True)
        return self.parse_expr()

    def parse_block(self, allow_final_case: bool) -> Block:
        start = self.eat("LBRACE")
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
        end = self.eat("RBRACE")
        return Block(exprs, span=self.span_for_tokens(start, end))

    def looks_like_case_start(self) -> bool:
        # single param shorthand cases: 0 ->, name ->, [x, y] ->, name ? ... ->
        # tuple case: ( ... ) ->
        # We only detect enough for v0.1.
        if self.at("NUMBER", "STRING", "IDENT", "GLOB"):
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
        return CaseExpr(clauses, span=self.merge_spans(clauses[0].span, clauses[-1].span))

    def parse_case_clause(self, single_param_shorthand_ok: bool) -> CaseClause:
        pattern = self.parse_pattern(single_param_shorthand_ok)
        guard = None
        if self.maybe("QMARK"):
            guard = self.parse_expr()
        self.eat("ARROW")
        result = self.parse_expr()
        return CaseClause(pattern, guard, result, span=self.merge_spans(pattern.span, result.span))

    def parse_pattern(self, single_param_shorthand_ok: bool) -> Node:
        if self.at("LPAREN"):
            start = self.eat("LPAREN")
            items: list[Node] = []
            if not self.at("RPAREN"):
                while True:
                    items.append(self.parse_pattern_atom())
                    if not self.maybe("COMMA"):
                        break
            end = self.eat("RPAREN")
            return TuplePattern(items, span=self.span_for_tokens(start, end))
        atom = self.parse_pattern_atom()
        if single_param_shorthand_ok:
            return atom
        return TuplePattern([atom], span=atom.span)

    def parse_pattern_atom(self) -> Node:
        tok = self.peek()
        if tok.kind == "NUMBER":
            self.i += 1
            return Number(float(tok.text) if "." in tok.text else int(tok.text), span=self.span_for_tokens(tok, tok))
        if tok.kind == "STRING":
            self.i += 1
            return String(parse_string_literal(tok.text), span=self.span_for_tokens(tok, tok))
        if tok.kind == "GLOB":
            self.i += 1
            return GlobPattern(parse_glob_literal(tok.text), span=self.span_for_tokens(tok, tok))
        if tok.kind == "DOTDOT":
            self.i += 1
            if self.at("IDENT"):
                name = self.eat("IDENT").text
                if name == "_":
                    return RestPattern(None, span=self.span_for_tokens(tok, tok))
                return RestPattern(name, span=self.span_for_tokens(tok, tok))
            return RestPattern(None, span=self.span_for_tokens(tok, tok))
        if tok.kind == "IDENT":
            self.i += 1
            if tok.text == "true":
                return Boolean(True, span=self.span_for_tokens(tok, tok))
            if tok.text == "false":
                return Boolean(False, span=self.span_for_tokens(tok, tok))
            if tok.text == "nil":
                return Nil(span=self.span_for_tokens(tok, tok))
            if tok.text == "_":
                return WildcardPattern(span=self.span_for_tokens(tok, tok))
            return Var(tok.text, span=self.span_for_tokens(tok, tok))
        if tok.kind == "LBRACK":
            start = self.eat("LBRACK")
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
            end = self.eat("RBRACK")
            return ListPattern(items, span=self.span_for_tokens(start, end))
        raise SyntaxError(f"Invalid pattern token {tok.text!r} ({tok.kind}) at {tok.pos}")

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
            left = Binary(left, op, right, span=self.merge_spans(left.span, right.span))
        return left

    def parse_prefix(self) -> Node:
        tok = self.peek()
        if tok.kind == "NUMBER":
            self.i += 1
            return Number(float(tok.text) if "." in tok.text else int(tok.text), span=self.span_for_tokens(tok, tok))
        if tok.kind == "STRING":
            self.i += 1
            return String(parse_string_literal(tok.text), span=self.span_for_tokens(tok, tok))
        if tok.kind == "IDENT":
            self.i += 1
            if tok.text == "true":
                return Boolean(True, span=self.span_for_tokens(tok, tok))
            if tok.text == "false":
                return Boolean(False, span=self.span_for_tokens(tok, tok))
            if tok.text == "nil":
                return Nil(span=self.span_for_tokens(tok, tok))
            return Var(tok.text, span=self.span_for_tokens(tok, tok))
        if tok.kind in ("MINUS", "BANG"):
            self.i += 1
            expr = self.parse_expr(70)
            return Unary(tok.kind, expr, span=self.merge_spans(self.span_for_tokens(tok, tok), expr.span))
        if tok.kind == "LPAREN":
            save = self.i
            start = self.peek()
            try:
                self.i += 1
                self.skip_newlines()
                params, rest_param = self.parse_parameter_list(context="Lambda", allow_wildcard=True)
                self.eat("RPAREN")
                self.skip_newlines()
                if self.at("ARROW"):
                    self.eat("ARROW")
                    body = self.parse_expr()
                    return Lambda(params, rest_param, body, span=self.merge_spans(self.span_for_tokens(start, start), body.span))
                self.i = save
            except SyntaxError:
                self.i = save
                if self.parenthesized_intro_has_arrow(save):
                    raise

            self.i += 1
            self.skip_newlines()
            expr = self.parse_expr()
            self.skip_newlines()
            self.eat("RPAREN")
            return expr
        if tok.kind == "LBRACK":
            return self.parse_list_literal()
        if tok.kind == "LBRACE":
            return self.parse_block(allow_final_case=False)
        raise SyntaxError(f"Unexpected token {tok.text!r} ({tok.kind}) at {tok.pos}")

    def parse_list_literal(self) -> ListLiteral:
        start = self.eat("LBRACK")
        self.skip_newlines()
        items: list[Node] = []
        self.skip_separators()
        if not self.at("RBRACK"):
            while True:
                if self.at("DOTDOT"):
                    dotdot = self.eat("DOTDOT")
                    expr = self.parse_expr()
                    items.append(Spread(expr, span=self.merge_spans(self.span_for_tokens(dotdot, dotdot), expr.span)))
                else:
                    items.append(self.parse_expr())
                self.skip_separators()
                if not self.maybe("COMMA"):
                    break
                self.skip_newlines()
                if self.at("RBRACK"):
                    break
                self.skip_newlines()
        self.skip_newlines()
        end = self.eat("RBRACK")
        return ListLiteral(items, span=self.span_for_tokens(start, end))

    def finish_call(self, fn: Node) -> Node:
        self.eat("LPAREN")
        self.skip_newlines()
        args: list[Node] = []
        self.skip_separators()
        if not self.at("RPAREN"):
            while True:
                if self.at("DOTDOT"):
                    dotdot = self.eat("DOTDOT")
                    expr = self.parse_expr()
                    args.append(Spread(expr, span=self.merge_spans(self.span_for_tokens(dotdot, dotdot), expr.span)))
                else:
                    args.append(self.parse_expr())
                self.skip_separators()
                if not self.maybe("COMMA"):
                    break
                self.skip_newlines()
                if self.at("RPAREN"):
                    break
                self.skip_newlines()
        self.skip_newlines()
        end = self.eat("RPAREN")
        return Call(fn, args, span=self.merge_spans(fn.span, self.span_for_tokens(end, end)))


# -----------------------------
# Runtime
# -----------------------------

class DebugHooks:
    def before_node(self, node: IrNode, env: "Env") -> None:  # noqa: ARG002
        pass

    def after_node(self, node: IrNode, env: "Env", result: Any) -> None:  # noqa: ARG002
        pass

    def on_function_enter(
        self,
        fn_name: str,
        args: tuple[Any, ...],
        env: "Env",
        span: SourceSpan | None,
    ) -> None:  # noqa: ARG002
        pass

    def on_function_exit(
        self,
        fn_name: str,
        result: Any,
        env: "Env",
        span: SourceSpan | None,
    ) -> None:  # noqa: ARG002
        pass


NOOP_DEBUG_HOOKS = DebugHooks()


class Env:
    def __init__(self, parent: Optional["Env"] = None):
        self.parent = parent
        self.values: dict[str, Any] = {}
        self.autoloads: dict[tuple[str, int], str] = {}
        self.loaded_files: set[str] = set()
        self.loading_files: set[str] = set()
        self.debug_hooks: DebugHooks = NOOP_DEBUG_HOOKS
        self.debug_mode: bool = False

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
            group = GeniaFunctionGroup(fn.name)
            group.add_clause(fn)
            self.values[fn.name] = group
            return
        if not isinstance(existing, GeniaFunctionGroup):
            raise TypeError(f"Cannot define function {fn.name}/{fn.arity}: name already bound to non-function value")
        existing.add_clause(fn)

    def register_autoload(self, name: str, arity: int, path: str) -> None:
        root = self.root()
        root.autoloads[(name, arity)] = path

    def try_autoload(self, name: str, arity: int) -> bool:
        root = self.root()
        path = root.autoloads.get((name, arity))
        if path is None:
            for (autoload_name, _), candidate_path in root.autoloads.items():
                if autoload_name == name:
                    path = candidate_path
                    break
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
            run_source(source, root, filename=key, debug_hooks=root.debug_hooks, debug_mode=root.debug_mode)
            root.loaded_files.add(key)
            return True
        finally:
            root.loading_files.remove(key)


@dataclass
class GeniaFunctionGroup:
    name: str
    functions: dict[int, "GeniaFunction"] = field(default_factory=dict)
    docstring: str | None = None

    def add_clause(self, fn: "GeniaFunction") -> None:
        existing = self.functions.get(fn.arity)
        if existing is not None:
            raise TypeError(f"Duplicate function definition: {fn.name}/{fn.arity}")
        self._merge_docstring(fn.docstring)
        self.functions[fn.arity] = fn

    def _merge_docstring(self, candidate: str | None) -> None:
        if candidate is None:
            return
        if self.docstring is None:
            self.docstring = candidate
            return
        if self.docstring != candidate:
            raise TypeError(
                f"Conflicting docstrings for function {self.name}: got {candidate!r}, expected {self.docstring!r}"
            )

    def __iter__(self):
        return iter(self.functions)

    def __getitem__(self, key: int) -> "GeniaFunction":
        return self.functions[key]

    def get(self, key: int) -> "GeniaFunction | None":
        return self.functions.get(key)

    def values(self):
        return self.functions.values()

    def sorted_arities(self) -> list[int]:
        return sorted(self.functions)



@dataclass
class GeniaFunction:
    name: str
    params: list[str]
    rest_param: str | None
    docstring: str | None
    body: IrNode
    closure: Env
    span: SourceSpan | None = None
    debug_hooks: DebugHooks = NOOP_DEBUG_HOOKS
    debug_mode: bool = False

    @property
    def arity(self) -> int:
        return len(self.params)

    def __call__(self, *args: Any) -> Any:
        return eval_with_tco(self, args, debug_hooks=self.debug_hooks, debug_mode=self.debug_mode)

    def __repr__(self) -> str:
        if self.rest_param is None:
            return f"<function {self.name}/{self.arity}>"
        return f"<function {self.name}/{self.arity}+>"


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

    def is_set(self) -> bool:
        with self._condition:
            return self._is_set

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


def _freeze_map_key(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        return ("list", tuple(_freeze_map_key(item) for item in value))
    if isinstance(value, tuple):
        return ("tuple", tuple(_freeze_map_key(item) for item in value))
    raise TypeError(f"map key type is not supported: {type(value).__name__}")


class GeniaMap:
    def __init__(self, entries: dict[Any, tuple[Any, Any]] | None = None):
        self._entries = {} if entries is None else entries

    def get(self, key: Any) -> Any:
        frozen_key = _freeze_map_key(key)
        entry = self._entries.get(frozen_key)
        if entry is None:
            return None
        return entry[1]

    def put(self, key: Any, value: Any) -> "GeniaMap":
        frozen_key = _freeze_map_key(key)
        next_entries = dict(self._entries)
        next_entries[frozen_key] = (key, value)
        return GeniaMap(next_entries)

    def has(self, key: Any) -> bool:
        frozen_key = _freeze_map_key(key)
        return frozen_key in self._entries

    def remove(self, key: Any) -> "GeniaMap":
        frozen_key = _freeze_map_key(key)
        if frozen_key not in self._entries:
            return self
        next_entries = dict(self._entries)
        del next_entries[frozen_key]
        return GeniaMap(next_entries)

    def count(self) -> int:
        return len(self._entries)

    def __repr__(self) -> str:
        return f"<map {len(self._entries)}>"


class GeniaProcess:
    def __init__(self, handler: Callable[[Any], Any]):
        self._handler = handler
        self._mailbox: queue.Queue[Any] = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while True:
            message = self._mailbox.get()
            self._handler(message)

    def send(self, message: Any) -> None:
        self._mailbox.put(message)

    def is_alive(self) -> bool:
        return self._thread.is_alive()

    def __repr__(self) -> str:
        status = "alive" if self.is_alive() else "dead"
        return f"<process {status}>"


class GeniaBytes:
    def __init__(self, value: bytes):
        self.value = value

    def __repr__(self) -> str:
        return f"<bytes {len(self.value)}>"


class GeniaZipEntry:
    def __init__(self, name: str, data: GeniaBytes):
        self.name = name
        self.data = data

    def __repr__(self) -> str:
        return f"<zip-entry {self.name!r} {len(self.data.value)}>"


def eval_with_tco(
    fn: Any,
    args: tuple[Any, ...],
    debug_hooks: DebugHooks = NOOP_DEBUG_HOOKS,
    debug_mode: bool = False,
) -> Any:
    current_fn = fn
    current_args = args

    while True:
        if isinstance(current_fn, GeniaFunction):
            if current_fn.rest_param is None:
                if len(current_args) != current_fn.arity:
                    raise TypeError(f"{current_fn.name} expected {current_fn.arity} args, got {len(current_args)}")
            elif len(current_args) < current_fn.arity:
                raise TypeError(f"{current_fn.name} expected at least {current_fn.arity} args, got {len(current_args)}")
            frame = Env(current_fn.closure)
            for p, a in zip(current_fn.params, current_args):
                frame.set(p, a)
            if current_fn.rest_param is not None:
                frame.set(current_fn.rest_param, list(current_args[current_fn.arity:]))
            if debug_mode:
                debug_hooks.on_function_enter(current_fn.name, current_args, frame, current_fn.span)
            result = Evaluator(frame, debug_hooks=debug_hooks, debug_mode=debug_mode).eval_function_body(
                current_fn.params,
                current_args,
                current_fn.body,
                current_fn.name,
            )
            if debug_mode:
                debug_hooks.on_function_exit(current_fn.name, result, frame, current_fn.span)
        else:
            result = current_fn(*current_args)

        if isinstance(result, TailCall):
            current_fn = result.fn
            current_args = result.args
            continue
        return result


class Evaluator:
    def __init__(self, env: Env, debug_hooks: DebugHooks = NOOP_DEBUG_HOOKS, debug_mode: bool = False):
        self.env = env
        self.debug_hooks = debug_hooks
        self.debug_mode = debug_mode

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
                return Evaluator(local, self.debug_hooks, self.debug_mode).eval_tail(body.empty_clause.result)

            if n_value == 0:
                match_env = self.match_pattern(body.zero_clause.pattern, current_args)
                if match_env is None:
                    return None
                local = Env(self.env)
                for k, v in match_env.items():
                    local.set(k, v)
                return Evaluator(local, self.debug_hooks, self.debug_mode).eval_tail(body.zero_clause.result)

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
            if clause.guard is not None and not Evaluator(local, self.debug_hooks, self.debug_mode).eval(clause.guard):
                continue
            return Evaluator(local, self.debug_hooks, self.debug_mode).eval_tail(clause.result)
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
            ev = Evaluator(local, self.debug_hooks, self.debug_mode)
            for expr in node.exprs[:-1]:
                ev.eval(expr)
            if not node.exprs:
                return None
            return ev.eval_tail(node.exprs[-1])
        return self.eval(node)

    def eval_call(self, node: IrCall, tail_position: bool) -> Any:
        args: list[Any] = []
        for arg_node in node.args:
            if isinstance(arg_node, IrSpread):
                value = self.eval(arg_node.expr)
                if not isinstance(value, list):
                    raise TypeError("Cannot spread non-list into function arguments")
                args.extend(value)
            else:
                args.append(self.eval(arg_node))

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

        return self.invoke_callable(fn, args, tail_position=tail_position, callee_node=node.fn)

    def invoke_callable(
        self,
        fn: Any,
        args: list[Any],
        *,
        tail_position: bool,
        callee_node: IrNode | None = None,
    ) -> Any:

        if isinstance(fn, GeniaFunctionGroup):
            arity = len(args)

            def resolve_target(functions: GeniaFunctionGroup, call_arity: int) -> Any | None:
                exact = functions.get(call_arity)
                if exact is not None:
                    return exact

                vararg_matches = [
                    candidate
                    for candidate in functions.values()
                    if isinstance(candidate, GeniaFunction)
                    and candidate.rest_param is not None
                    and call_arity >= candidate.arity
                ]
                if len(vararg_matches) == 1:
                    return vararg_matches[0]
                if len(vararg_matches) > 1:
                    callee = callee_node.name if isinstance(callee_node, IrVar) else "function"
                    candidates = ", ".join(
                        f"{callee}/{candidate.arity}+"
                        for candidate in sorted(vararg_matches, key=lambda f: f.arity)
                    )
                    raise TypeError(
                        f"Ambiguous function resolution: {callee}/{call_arity}. Matching varargs: {candidates}"
                    )
                return None

            target = resolve_target(fn, arity)

            if target is None and isinstance(callee_node, IrVar):
                if self.env.try_autoload(callee_node.name, arity):
                    fn = self.env.get(callee_node.name)
                    if isinstance(fn, GeniaFunctionGroup):
                        target = resolve_target(fn, arity)

            if target is None:
                callee = callee_node.name if isinstance(callee_node, IrVar) else "function"
                available = ", ".join(f"{callee}/{n}" for n in fn.sorted_arities())
                raise TypeError(f"No matching function: {callee}/{arity}. Available: {available}")
            if tail_position and not self.debug_mode:
                return TailCall(target, tuple(args))
            return target(*args)

        if tail_position and not self.debug_mode:
            return TailCall(fn, tuple(args))
        return fn(*args)

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
        if isinstance(pattern, IrPatGlob):
            if not isinstance(arg, str):
                return None
            return {} if glob_match(pattern.matcher, arg) else None
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
        if self.debug_mode:
            self.debug_hooks.before_node(node, self.env)
        result = self._eval_impl(node)
        if self.debug_mode:
            self.debug_hooks.after_node(node, self.env, result)
        return result

    def _eval_impl(self, node: IrNode) -> Any:
        if isinstance(node, IrExprStmt):
            return self.eval(node.expr)
        if isinstance(node, IrLiteral):
            return node.value
        if isinstance(node, IrList):
            result: list[Any] = []
            for item in node.items:
                if isinstance(item, IrSpread):
                    value = self.eval(item.expr)
                    if not isinstance(value, list):
                        raise TypeError("Cannot spread non-list")
                    result.extend(value)
                else:
                    result.append(self.eval(item))
            return result
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
            ev = Evaluator(local, self.debug_hooks, self.debug_mode)
            for expr in node.exprs:
                result = ev.eval(expr)
            return result
        if isinstance(node, IrLambda):
            params = node.params
            rest_param = node.rest_param
            body = node.body
            closure = self.env

            def fn(*args):
                if rest_param is None:
                    if len(args) != len(params):
                        raise TypeError(f"lambda expected {len(params)} args, got {len(args)}")
                elif len(args) < len(params):
                    raise TypeError(f"lambda expected at least {len(params)} args, got {len(args)}")
                frame = Env(closure)
                for p, a in zip(params, args):
                    frame.set(p, a)
                if rest_param is not None:
                    frame.set(rest_param, list(args[len(params):]))
                return Evaluator(frame, self.debug_hooks, self.debug_mode).eval(body)

            return fn

        if isinstance(node, IrAssign):
            value = self.eval(node.expr)
            self.env.set(node.name, value)
            return value

        if isinstance(node, IrFuncDef):
            fn = GeniaFunction(
                node.name,
                node.params,
                node.rest_param,
                node.docstring,
                node.body,
                self.env,
                span=node.span,
                debug_hooks=self.debug_hooks,
                debug_mode=self.debug_mode,
            )
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
    cli_args: Optional[list[str]] = None,
    debug_hooks: DebugHooks | None = None,
    debug_mode: bool = False,
    output_handler: Optional[Callable[[str], None]] = None,
) -> Env:
    env = Env()
    env.debug_hooks = debug_hooks or NOOP_DEBUG_HOOKS
    env.debug_mode = debug_mode

    def log(*args: Any) -> Any:
        output = " ".join(format_display(arg) for arg in args) + "\n"
        if output_handler is None:
            print(output, end="")
        else:
            output_handler(output)
        return args[-1] if args else None

    def print_fn(*args: Any) -> Any:
        output = " ".join(format_display(arg) for arg in args) + "\n"
        if output_handler is None:
            print(output, end="")
        else:
            output_handler(output)
        return args[-1] if args else None

    def _ensure_string(value: Any, name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{name} expected a string")
        return value

    def _ensure_bytes(value: Any, name: str) -> GeniaBytes:
        if not isinstance(value, GeniaBytes):
            raise TypeError(f"{name} expected bytes")
        return value

    def _ensure_zip_entry(value: Any, name: str) -> GeniaZipEntry:
        if not isinstance(value, GeniaZipEntry):
            raise TypeError(f"{name} expected a zip entry")
        return value

    def _json_from_runtime(value: Any) -> Any:
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, list):
            return [_json_from_runtime(item) for item in value]
        if isinstance(value, GeniaMap):
            data: dict[str, Any] = {}
            for _, (original_key, original_value) in value._entries.items():
                if not isinstance(original_key, str):
                    raise TypeError("json_pretty expected object keys to be strings")
                data[original_key] = _json_from_runtime(original_value)
            return data
        raise TypeError(f"json_pretty expected a JSON-compatible value, got {type(value).__name__}")

    def _json_to_runtime(value: Any) -> Any:
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, list):
            return [_json_to_runtime(item) for item in value]
        if isinstance(value, dict):
            result = GeniaMap()
            for k, v in value.items():
                result = result.put(k, _json_to_runtime(v))
            return result
        raise TypeError(f"json_parse produced unsupported host value: {type(value).__name__}")

    def byte_length_fn(value: Any) -> int:
        return utf8_byte_length(_ensure_string(value, "byte_length"))

    def is_empty_fn(value: Any) -> bool:
        return _ensure_string(value, "is_empty") == ""

    def concat_fn(left: Any, right: Any) -> str:
        return _ensure_string(left, "concat") + _ensure_string(right, "concat")

    def contains_fn(haystack: Any, needle: Any) -> bool:
        return _ensure_string(needle, "contains") in _ensure_string(haystack, "contains")

    def starts_with_fn(value: Any, prefix: Any) -> bool:
        return _ensure_string(value, "starts_with").startswith(_ensure_string(prefix, "starts_with"))

    def ends_with_fn(value: Any, suffix: Any) -> bool:
        return _ensure_string(value, "ends_with").endswith(_ensure_string(suffix, "ends_with"))

    def find_fn(value: Any, needle: Any) -> int | None:
        idx = _ensure_string(value, "find").find(_ensure_string(needle, "find"))
        return None if idx < 0 else idx

    def split_fn(value: Any, sep: Any) -> list[str]:
        parts = _ensure_string(value, "split").split(_ensure_string(sep, "split"))
        if parts and parts[0] == "":
            parts = parts[1:]
        if parts and parts[-1] == "":
            parts = parts[:-1]
        return parts

    def split_whitespace_fn(value: Any) -> list[str]:
        return _ensure_string(value, "split_whitespace").split()

    def join_fn(sep: Any, xs: Any) -> str:
        separator = _ensure_string(sep, "join")
        if not isinstance(xs, list):
            raise TypeError("join expected a list as second argument")
        if not all(isinstance(item, str) for item in xs):
            raise TypeError("join expected a list of strings")
        return separator.join(xs)

    def trim_fn(value: Any) -> str:
        return _ensure_string(value, "trim").strip()

    def trim_start_fn(value: Any) -> str:
        return _ensure_string(value, "trim_start").lstrip()

    def trim_end_fn(value: Any) -> str:
        return _ensure_string(value, "trim_end").rstrip()

    def lower_fn(value: Any) -> str:
        return _ensure_string(value, "lower").lower()

    def upper_fn(value: Any) -> str:
        return _ensure_string(value, "upper").upper()

    def input_fn(prompt: str = "") -> str:
        return input(prompt)

    argv_cache = list(cli_args or [])

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

    def argv_fn() -> list[str]:
        return list(argv_cache)

    def _emit_help(text: str) -> None:
        output = text + "\n"
        if output_handler is None:
            print(output, end="")
        else:
            output_handler(output)

    def _format_span(span: SourceSpan | None) -> str | None:
        if span is None:
            return None
        return f"{span.filename}:{span.line}"

    def _format_function_shapes(group: GeniaFunctionGroup) -> str:
        shapes: list[str] = []
        for arity in group.sorted_arities():
            fn_value = group.get(arity)
            if fn_value is None:
                continue
            suffix = "+" if fn_value.rest_param is not None else ""
            shapes.append(f"{arity}{suffix}")
        return ", ".join(shapes) if shapes else "unknown"

    def _group_span(group: GeniaFunctionGroup) -> SourceSpan | None:
        spans = [fn.span for fn in group.values() if isinstance(fn, GeniaFunction) and fn.span is not None]
        if not spans:
            return None
        return min(spans, key=lambda s: (s.line, s.column, s.end_line, s.end_column))

    def _describe_function_group(group: GeniaFunctionGroup) -> str:
        shapes = _format_function_shapes(group)
        lines = [f"{group.name}/{shapes}"]
        span_text = _format_span(_group_span(group))
        if span_text is not None:
            lines.append(f"Defined at {span_text}")
        lines.append("")
        if group.docstring is not None:
            lines.append(render_markdown_docstring(group.docstring))
        else:
            lines.append("No documentation available.")
        return "\n".join(lines)

    def help_fn(*args: Any) -> None:
        if len(args) > 1:
            raise TypeError(f"help expected 0 or 1 args, got {len(args)}")
        if len(args) == 1:
            target = args[0]
            if isinstance(target, str):
                target = env.get(target)
            if isinstance(target, GeniaFunctionGroup):
                _emit_help(_describe_function_group(target))
                return
            if isinstance(target, GeniaFunction):
                singleton = GeniaFunctionGroup(target.name, functions={target.arity: target}, docstring=target.docstring)
                _emit_help(_describe_function_group(singleton))
                return
            raise TypeError("help expected a function name or named function")

        _emit_help(
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
  print(argv())
  count([1, 2, 3])
  print([1, 2, 3])

  inbox = ref([])
  p = spawn((msg) -> ref_update(inbox, (xs) -> append(xs, [msg])))
  send(p, "hello")
  process_alive?(p)

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
  help(name)   show metadata for a named function

CLI builtins (list-first):
  argv()                     trailing command-line args as [string]
  cli_parse(args)            [opts_map, positionals]
  cli_parse(args, spec)      same with minimal spec map (flags/options/aliases)
  cli_flag?(opts, name)      boolean option check
  cli_option(opts, name)     option value or nil
  cli_option_or(opts, name, default)

Concurrency builtins (host-backed):
  spawn(handler)          create a process with a mailbox
  send(process, message)  enqueue a message for that process
  process_alive?(process) check whether process worker thread is alive

Persistent map builtins (phase 1, host-backed opaque wrapper):
  map_new()
  map_get(map, key)
  map_put(map, key, value)
  map_has?(map, key)
  map_remove(map, key)
  map_count(map)

Simulation primitives (host-backed builtins):
  rand()                float in [0, 1)
  rand_int(n)           integer in [0, n), n must be a positive integer
  sleep(ms)             block for ms milliseconds

Bytes / JSON / ZIP builtins (host-backed runtime bridge):
  utf8_encode(string)        bytes wrapper
  utf8_decode(bytes)         string
  json_parse(string)         runtime value (objects become map values)
  json_pretty(value)         stable pretty JSON string
  zip_entries(path)          list of zip entries
  zip_write(entries, path)   writes zip and returns path
  entry_name(entry)
  entry_bytes(entry)
  set_entry_bytes(entry, bytes)
  update_entry_bytes(entry, updater)
  entry_json(entry)
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

    def ref_is_set_fn(ref_value: Any) -> bool:
        if not isinstance(ref_value, GeniaRef):
            raise TypeError("ref_is_set expected a ref")
        return ref_value.is_set()

    def ref_update_fn(ref_value: Any, updater: Any) -> Any:
        if not isinstance(ref_value, GeniaRef):
            raise TypeError("ref_update expected a ref as first argument")
        if not callable(updater):
            raise TypeError("ref_update expected a function as second argument")
        return ref_value.update(updater)

    def spawn_fn(handler: Any) -> GeniaProcess:
        if not callable(handler):
            raise TypeError("spawn expected a function")
        return GeniaProcess(handler)

    def send_fn(process: Any, message: Any) -> None:
        if not isinstance(process, GeniaProcess):
            raise TypeError("send expected a process as first argument")
        process.send(message)
        return None

    def process_alive_fn(process: Any) -> bool:
        if not isinstance(process, GeniaProcess):
            raise TypeError("process_alive? expected a process")
        return process.is_alive()

    def _ensure_map(value: Any, name: str) -> GeniaMap:
        if not isinstance(value, GeniaMap):
            raise TypeError(f"{name} expected a map as first argument")
        return value

    def _ensure_list_of_strings(value: Any, name: str) -> list[str]:
        if not isinstance(value, list):
            raise TypeError(f"{name} expected a list of strings")
        if not all(isinstance(item, str) for item in value):
            raise TypeError(f"{name} expected a list of strings")
        return value

    def _parse_cli_spec(spec: Any) -> tuple[set[str], set[str], dict[str, str]]:
        if spec is None:
            return set(), set(), {}
        if not isinstance(spec, GeniaMap):
            raise TypeError("cli_parse expected spec to be a map")

        flags_raw = spec.get("flags")
        options_raw = spec.get("options")
        aliases_raw = spec.get("aliases")

        flags = set(_ensure_list_of_strings(flags_raw, "cli_parse spec.flags")) if flags_raw is not None else set()
        options = set(_ensure_list_of_strings(options_raw, "cli_parse spec.options")) if options_raw is not None else set()
        aliases: dict[str, str] = {}

        if aliases_raw is not None:
            if not isinstance(aliases_raw, GeniaMap):
                raise TypeError("cli_parse spec.aliases expected a map")
            for _, (raw_key, raw_value) in aliases_raw._entries.items():
                if not isinstance(raw_key, str) or not isinstance(raw_value, str):
                    raise TypeError("cli_parse spec.aliases expected string keys and values")
                aliases[raw_key] = raw_value

        return flags, options, aliases

    def _cli_option_like(token: str) -> bool:
        return token != "-" and token.startswith("-")

    def _cli_put(opts: GeniaMap, name: str, value: Any) -> GeniaMap:
        if name == "":
            raise ValueError("cli_parse encountered an empty option name")
        return opts.put(name, value)

    def cli_parse_fn(*args: Any) -> list[Any]:
        if len(args) == 1:
            raw_args = _ensure_list_of_strings(args[0], "cli_parse")
            flags, options, aliases = set(), set(), {}
        elif len(args) == 2:
            raw_args = _ensure_list_of_strings(args[0], "cli_parse")
            flags, options, aliases = _parse_cli_spec(args[1])
        else:
            raise TypeError(f"cli_parse expected 1 or 2 args, got {len(args)}")

        opts = GeniaMap()
        positionals: list[str] = []
        parsing_options = True
        i = 0

        while i < len(raw_args):
            token = raw_args[i]

            if not parsing_options:
                positionals.append(token)
                i += 1
                continue

            if token == "--":
                parsing_options = False
                i += 1
                continue

            if token.startswith("--") and len(token) > 2:
                body = token[2:]
                if "=" in body:
                    name, value = body.split("=", 1)
                    name = aliases.get(name, name)
                    opts = _cli_put(opts, name, value)
                    i += 1
                    continue

                name = aliases.get(body, body)
                uses_explicit_option = name in options
                has_value = i + 1 < len(raw_args)
                next_token = raw_args[i + 1] if has_value else None
                should_consume_next = has_value and (uses_explicit_option or (name not in flags and not _cli_option_like(next_token)))
                if should_consume_next:
                    opts = _cli_put(opts, name, next_token)
                    i += 2
                    continue
                opts = _cli_put(opts, name, True)
                i += 1
                continue

            if token.startswith("-") and token != "-" and len(token) > 1:
                body = token[1:]
                if len(body) == 1:
                    name = aliases.get(body, body)
                    uses_explicit_option = name in options
                    has_value = i + 1 < len(raw_args)
                    next_token = raw_args[i + 1] if has_value else None
                    should_consume_next = has_value and (uses_explicit_option or (name not in flags and not _cli_option_like(next_token)))
                    if should_consume_next:
                        opts = _cli_put(opts, name, next_token)
                        i += 2
                        continue
                    opts = _cli_put(opts, name, True)
                    i += 1
                    continue

                if options:
                    option_chars = [ch for ch in body if aliases.get(ch, ch) in options]
                    if len(option_chars) > 1:
                        raise ValueError(f"cli_parse ambiguous short option group: -{body}")
                    if len(option_chars) == 1:
                        option_char = option_chars[0]
                        option_idx = body.index(option_char)
                        if option_idx != 0:
                            raise ValueError(f"cli_parse ambiguous short option group: -{body}")
                        name = aliases.get(option_char, option_char)
                        inline_value = body[1:]
                        if inline_value != "":
                            opts = _cli_put(opts, name, inline_value)
                            i += 1
                            continue
                        if i + 1 >= len(raw_args):
                            raise ValueError(f"cli_parse missing value for -{option_char}")
                        opts = _cli_put(opts, name, raw_args[i + 1])
                        i += 2
                        continue

                for ch in body:
                    name = aliases.get(ch, ch)
                    opts = _cli_put(opts, name, True)
                i += 1
                continue

            positionals.append(token)
            i += 1

        return [opts, positionals]

    def cli_flag_fn(opts: Any, name: Any) -> bool:
        genia_map = _ensure_map(opts, "cli_flag?")
        key = _ensure_string(name, "cli_flag?")
        return bool(genia_map.get(key))

    def cli_option_fn(opts: Any, name: Any) -> Any:
        genia_map = _ensure_map(opts, "cli_option")
        key = _ensure_string(name, "cli_option")
        return genia_map.get(key)

    def cli_option_or_fn(opts: Any, name: Any, default: Any) -> Any:
        genia_map = _ensure_map(opts, "cli_option_or")
        key = _ensure_string(name, "cli_option_or")
        value = genia_map.get(key)
        return default if value is None else value

    def map_new_fn(*args: Any) -> GeniaMap:
        if len(args) != 0:
            raise TypeError(f"map_new expected 0 args, got {len(args)}")
        return GeniaMap()

    def map_get_fn(map_value: Any, key: Any) -> Any:
        genia_map = _ensure_map(map_value, "map_get")
        return genia_map.get(key)

    def map_put_fn(map_value: Any, key: Any, value: Any) -> GeniaMap:
        genia_map = _ensure_map(map_value, "map_put")
        return genia_map.put(key, value)

    def map_has_fn(map_value: Any, key: Any) -> bool:
        genia_map = _ensure_map(map_value, "map_has?")
        return genia_map.has(key)

    def map_remove_fn(map_value: Any, key: Any) -> GeniaMap:
        genia_map = _ensure_map(map_value, "map_remove")
        return genia_map.remove(key)

    def map_count_fn(map_value: Any) -> int:
        genia_map = _ensure_map(map_value, "map_count")
        return genia_map.count()

    def rand_fn(*args: Any) -> float:
        if len(args) != 0:
            raise TypeError(f"rand expected 0 args, got {len(args)}")
        return random.random()

    def rand_int_fn(n: Any) -> int:
        if not isinstance(n, int) or isinstance(n, bool):
            raise TypeError("rand_int expected a positive integer")
        if n <= 0:
            raise ValueError("rand_int expected n > 0")
        return random.randrange(n)

    def sleep_fn(ms: Any) -> None:
        if not isinstance(ms, (int, float)) or isinstance(ms, bool):
            raise TypeError("sleep expected a non-negative number")
        if ms < 0:
            raise ValueError("sleep expected ms >= 0")
        time.sleep(ms / 1000.0)
        return None

    def utf8_encode_fn(value: Any) -> GeniaBytes:
        text = _ensure_string(value, "utf8_encode")
        return GeniaBytes(text.encode("utf-8"))

    def utf8_decode_fn(value: Any) -> str:
        encoded = _ensure_bytes(value, "utf8_decode")
        try:
            return encoded.value.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"utf8_decode invalid UTF-8: {exc}") from exc

    def json_parse_fn(value: Any) -> Any:
        text = _ensure_string(value, "json_parse")
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"json_parse invalid JSON: {exc.msg} at line {exc.lineno} column {exc.colno}") from exc
        return _json_to_runtime(parsed)

    def json_pretty_fn(value: Any) -> str:
        return json.dumps(_json_from_runtime(value), indent=2, ensure_ascii=False, sort_keys=True)

    def zip_entries_fn(path: Any) -> list[GeniaZipEntry]:
        zip_path = _ensure_string(path, "zip_entries")
        try:
            with zipfile.ZipFile(zip_path, "r") as archive:
                entries: list[GeniaZipEntry] = []
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    entries.append(GeniaZipEntry(info.filename, GeniaBytes(archive.read(info.filename))))
                return entries
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"zip_entries could not read zip file: {zip_path}") from exc
        except zipfile.BadZipFile as exc:
            raise ValueError(f"zip_entries invalid zip archive: {zip_path}") from exc
        except OSError as exc:
            raise OSError(f"zip_entries could not read zip file: {zip_path}") from exc

    def entry_name_fn(entry: Any) -> str:
        return _ensure_zip_entry(entry, "entry_name").name

    def entry_bytes_fn(entry: Any) -> GeniaBytes:
        return _ensure_zip_entry(entry, "entry_bytes").data

    def set_entry_bytes_fn(entry: Any, new_bytes: Any) -> GeniaZipEntry:
        zip_entry = _ensure_zip_entry(entry, "set_entry_bytes")
        data = _ensure_bytes(new_bytes, "set_entry_bytes")
        return GeniaZipEntry(zip_entry.name, data)

    def update_entry_bytes_fn(entry: Any, updater: Any) -> GeniaZipEntry:
        zip_entry = _ensure_zip_entry(entry, "update_entry_bytes")
        if not callable(updater):
            raise TypeError("update_entry_bytes expected a function as second argument")
        next_data = updater(zip_entry.data)
        if not isinstance(next_data, GeniaBytes):
            raise TypeError("update_entry_bytes updater must return bytes")
        return GeniaZipEntry(zip_entry.name, next_data)

    def entry_json_fn(entry: Any) -> bool:
        zip_entry = _ensure_zip_entry(entry, "entry_json")
        return zip_entry.name.lower().endswith(".json")

    def zip_write_fn(first: Any, second: Any) -> str:
        if isinstance(first, str) and isinstance(second, list):
            out_path = first
            entries = second
        elif isinstance(first, list) and isinstance(second, str):
            entries = first
            out_path = second
        else:
            raise TypeError("zip_write expected (entries, path) or (path, entries)")

        for item in entries:
            if not isinstance(item, GeniaZipEntry):
                raise TypeError("zip_write expected a list of zip entries")

        try:
            with zipfile.ZipFile(out_path, "w") as archive:
                for item in entries:
                    archive.writestr(item.name, item.data.value)
        except OSError as exc:
            raise OSError(f"zip_write could not write zip file: {out_path}") from exc
        return out_path

    env.set("log", log)
    env.set("print", print_fn)
    env.set("input", input_fn)
    env.set("stdin", stdin_fn)
    env.set("argv", argv_fn)
    env.set("help", help_fn)
    env.set("pi", math.pi)
    env.set("e", math.e)
    env.set("true", True)
    env.set("false", False)
    env.set("nil", None)
    env.set("ref", ref_fn)
    env.set("ref_get", ref_get_fn)
    env.set("ref_set", ref_set_fn)
    env.set("ref_is_set", ref_is_set_fn)
    env.set("ref_update", ref_update_fn)
    env.set("spawn", spawn_fn)
    env.set("send", send_fn)
    env.set("process_alive?", process_alive_fn)
    env.set("map_new", map_new_fn)
    env.set("map_get", map_get_fn)
    env.set("map_put", map_put_fn)
    env.set("map_has?", map_has_fn)
    env.set("map_remove", map_remove_fn)
    env.set("map_count", map_count_fn)
    env.set("rand", rand_fn)
    env.set("rand_int", rand_int_fn)
    env.set("sleep", sleep_fn)
    env.set("byte_length", byte_length_fn)
    env.set("is_empty", is_empty_fn)
    env.set("concat", concat_fn)
    env.set("contains", contains_fn)
    env.set("starts_with", starts_with_fn)
    env.set("ends_with", ends_with_fn)
    env.set("find", find_fn)
    env.set("split", split_fn)
    env.set("split_whitespace", split_whitespace_fn)
    env.set("join", join_fn)
    env.set("trim", trim_fn)
    env.set("trim_start", trim_start_fn)
    env.set("trim_end", trim_end_fn)
    env.set("lower", lower_fn)
    env.set("upper", upper_fn)
    env.set("utf8_decode", utf8_decode_fn)
    env.set("utf8_encode", utf8_encode_fn)
    env.set("json_parse", json_parse_fn)
    env.set("json_pretty", json_pretty_fn)
    env.set("zip_entries", zip_entries_fn)
    env.set("zip_write", zip_write_fn)
    env.set("entry_name", entry_name_fn)
    env.set("entry_bytes", entry_bytes_fn)
    env.set("set_entry_bytes", set_entry_bytes_fn)
    env.set("update_entry_bytes", update_entry_bytes_fn)
    env.set("entry_json", entry_json_fn)
    env.set("cli_parse", cli_parse_fn)
    env.set("cli_flag?", cli_flag_fn)
    env.set("cli_option", cli_option_fn)
    env.set("cli_option_or", cli_option_or_fn)

    env.register_autoload("list", 0, "std/prelude/list.genia")
    env.register_autoload("first", 1, "std/prelude/list.genia")
    env.register_autoload("rest", 1, "std/prelude/list.genia")
    env.register_autoload("empty?", 1, "std/prelude/list.genia")
    env.register_autoload("nil?", 1, "std/prelude/list.genia")
    env.register_autoload("append", 2, "std/prelude/list.genia")
    env.register_autoload("length", 1, "std/prelude/list.genia")
    env.register_autoload("reverse", 1, "std/prelude/list.genia")
    env.register_autoload("reduce", 3, "std/prelude/list.genia")
    env.register_autoload("map", 2, "std/prelude/list.genia")
    env.register_autoload("filter", 2, "std/prelude/list.genia")
    env.register_autoload("count", 1, "std/prelude/list.genia")
    env.register_autoload("any?", 2, "std/prelude/list.genia")
    env.register_autoload("nth", 2, "std/prelude/list.genia")
    env.register_autoload("take", 2, "std/prelude/list.genia")
    env.register_autoload("drop", 2, "std/prelude/list.genia")
    env.register_autoload("range", 1, "std/prelude/list.genia")
    env.register_autoload("range", 2, "std/prelude/list.genia")
    env.register_autoload("range", 3, "std/prelude/list.genia")
    env.register_autoload("apply", 2, "std/prelude/fn.genia")
    env.register_autoload("compose", 1, "std/prelude/fn.genia")

    env.register_autoload("inc", 1, "std/prelude/math.genia")
    env.register_autoload("dec", 1, "std/prelude/math.genia")
    env.register_autoload("mod", 2, "std/prelude/math.genia")
    env.register_autoload("abs", 1, "std/prelude/math.genia")
    env.register_autoload("min", 2, "std/prelude/math.genia")
    env.register_autoload("max", 2, "std/prelude/math.genia")
    env.register_autoload("sum", 1, "std/prelude/math.genia")
    env.register_autoload("awkify", 2, "std/prelude/awk.genia")
    env.register_autoload("awk_filter", 2, "std/prelude/awk.genia")
    env.register_autoload("awk_map", 2, "std/prelude/awk.genia")
    env.register_autoload("awk_count", 2, "std/prelude/awk.genia")
    env.register_autoload("fields", 1, "std/prelude/awk.genia")
    env.register_autoload("agent", 1, "std/prelude/agent.genia")
    env.register_autoload("agent_send", 2, "std/prelude/agent.genia")
    env.register_autoload("agent_get", 1, "std/prelude/agent.genia")
    env.register_autoload("agent_state", 1, "std/prelude/agent.genia")
    env.register_autoload("agent_alive?", 1, "std/prelude/agent.genia")
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


def run_source(
    source: str,
    env: Env,
    *,
    filename: str = "<memory>",
    debug_hooks: DebugHooks | None = None,
    debug_mode: bool = False,
) -> Any:
    effective_hooks = debug_hooks or env.debug_hooks or NOOP_DEBUG_HOOKS
    effective_debug_mode = debug_mode or env.debug_mode
    tokens = lex(source)
    parser = Parser(tokens, source=source, filename=filename)
    ast_nodes = parser.parse_program()
    ir_nodes = lower_program(ast_nodes)
    ir_nodes = optimize_program(ir_nodes, debug=os.getenv("GENIA_DEBUG_OPT", "") == "1")
    env.debug_hooks = effective_hooks
    env.debug_mode = effective_debug_mode
    return Evaluator(env, debug_hooks=effective_hooks, debug_mode=effective_debug_mode).eval_program(ir_nodes)


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
                print(f"{k} = {format_debug(env.values[k])}")
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
                print(format_debug(result))
        except Exception as e:  # noqa: BLE001
            print(f"Error: {e}", file=sys.stderr)


def run_debug_stdio(
    program_path: str,
    *,
    command_stream: Any = None,
    event_stream: Any = None,
    error_stream: Any = None,
) -> int:
    from .debug_controller import StdioDebugSession

    command_stream = command_stream or sys.stdin
    event_stream = event_stream or sys.stdout
    error_stream = error_stream or sys.stderr
    resolved_path = str(Path(program_path).resolve())
    source = Path(program_path).read_text(encoding="utf-8")
    session = StdioDebugSession(command_stream, event_stream, filename=resolved_path)
    env = make_global_env(debug_hooks=session, debug_mode=True, output_handler=session.emit_stdout_output)
    session.ensure_root_frame(env)
    return session.run(lambda: run_source(source, env, filename=resolved_path, debug_hooks=session, debug_mode=True), error_stream=error_stream)


def _main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="genia.interpreter")
    parser.add_argument("-c", "--command")
    parser.add_argument("--debug-stdio", action="store_true")
    args, remaining_args = parser.parse_known_args(argv)

    program_path: Optional[str] = None
    script_args: list[str] = []
    if args.command is not None:
        script_args = remaining_args
    elif remaining_args:
        program_path = remaining_args[0]
        script_args = remaining_args[1:]

    if args.debug_stdio:
        if program_path is None:
            parser.error("--debug-stdio requires a program path")
        if args.command is not None:
            parser.error("--debug-stdio cannot be used with --command")
        return run_debug_stdio(program_path)

    def resolve_program_result(run_result: Any, env: Env) -> Any:
        main_group = env.values.get("main")
        if not isinstance(main_group, GeniaFunctionGroup):
            return run_result
        main_with_args = main_group.get(1)
        if main_with_args is not None:
            cli_args = env.get("argv")()
            return main_with_args(cli_args)
        main_without_args = main_group.get(0)
        if main_without_args is not None:
            return main_without_args()
        return run_result

    if args.command is not None:
        env = make_global_env(cli_args=script_args)
        run_result = run_source(args.command, env, filename="<command>")
        result = resolve_program_result(run_result, env)
        if result is not None:
            print(format_debug(result))
        return 0
    if program_path is not None:
        env = make_global_env(cli_args=script_args)
        with open(program_path, "r", encoding="utf-8") as f:
            run_result = run_source(f.read(), env, filename=str(Path(program_path).resolve()))
        result = resolve_program_result(run_result, env)
        if result is not None:
            print(format_debug(result))
        return 0

    repl()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
