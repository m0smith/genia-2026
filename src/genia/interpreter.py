#!/usr/bin/env python3
"""
Minimal Genia REPL / interpreter prototype.

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
from importlib import resources as importlib_resources
from pathlib import Path
import argparse
import re
import sys
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Iterator, Optional

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


def _stdlib_resource(relative_path: str):
    if not relative_path.startswith("std/"):
        return None
    try:
        resource = importlib_resources.files("genia").joinpath(relative_path)
    except ModuleNotFoundError:
        return None
    return resource if resource.is_file() else None


def _load_source_from_path(path: str) -> tuple[str, str]:
    resource = _stdlib_resource(path)
    if resource is not None:
        source = resource.read_text(encoding="utf-8")
        with importlib_resources.as_file(resource) as resolved_resource_path:
            return source, str(resolved_resource_path)

    file_path = Path(path)
    candidates: list[Path] = []
    if file_path.is_absolute():
        candidates.append(file_path)
    else:
        candidates.append((BASE_DIR / path).resolve())
        candidates.append(file_path.resolve())
    for candidate in candidates:
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8"), str(candidate.resolve())
    raise FileNotFoundError(path)


def _resolve_packaged_module(module_name: str) -> tuple[str, str] | None:
    resource = _stdlib_resource(f"std/prelude/{module_name}.genia")
    if resource is None:
        return None
    source = resource.read_text(encoding="utf-8")
    with importlib_resources.as_file(resource) as resolved_resource_path:
        return source, str(resolved_resource_path)


# -----------------------------
# Lexer
# -----------------------------

# Single source of truth for symbol/operator policy:
# - These characters are always token delimiters/operators in Genia.
# - Clojure-style symbol punctuation that we allow in names is listed below.
# - `name?` and `name!` are ordinary identifiers (no special lexer semantics).
# - `/` is reserved for division and is not allowed inside identifier names.
ALWAYS_OPERATOR_DELIMITERS = frozenset({"+", "*", "/", "%", "=", "<", ">", "|", ",", ";", ":", "(", ")", "{", "}", "[", "]"})
ALLOWED_SYMBOL_PUNCTUATION = frozenset({"_", "?", "!", ".", "$", "-"})
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
    ("COLON", r":"),
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
    ("COLON", ":"),
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
class NoneOption(Node):
    reason: Node | None = None
    context: Node | None = None
    span: SourceSpan | None = None


@dataclass
class SymbolLiteral(Node):
    name: str
    span: SourceSpan | None = None


@dataclass
class Var(Node):
    name: str
    span: SourceSpan | None = None


@dataclass
class Quote(Node):
    expr: Node
    span: SourceSpan | None = None


@dataclass
class Delay(Node):
    expr: Node
    span: SourceSpan | None = None


@dataclass
class QuasiQuote(Node):
    expr: Node
    span: SourceSpan | None = None


@dataclass
class Unquote(Node):
    expr: Node
    span: SourceSpan | None = None


@dataclass
class UnquoteSplicing(Node):
    expr: Node
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
class MapLiteral(Node):
    items: list[tuple[Node, Node]]
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
class MapPattern(Node):
    items: list[tuple[str, Node]]
    span: SourceSpan | None = None


@dataclass
class SomePattern(Node):
    inner: Node
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


@dataclass
class ImportStmt(Node):
    module_name: str
    alias: str
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
class IrOptionNone(IrNode):
    """Structured none value with optional quoted reason and evaluated context."""

    reason: IrNode | None = None
    context: IrNode | None = None
    span: SourceSpan | None = None


@dataclass
class IrVar(IrNode):
    """Variable read by name (kept explicit for analysis and rewriting)."""

    name: str
    span: SourceSpan | None = None


@dataclass
class IrQuote(IrNode):
    """Quoted source expression preserved for syntax-to-data conversion."""

    expr: Node
    span: SourceSpan | None = None


@dataclass
class IrDelay(IrNode):
    """Delayed expression preserved for promise creation."""

    expr: IrNode
    span: SourceSpan | None = None


@dataclass
class IrQuasiQuote(IrNode):
    """Quasiquoted source expression preserved for syntax-to-data conversion."""

    expr: Node
    span: SourceSpan | None = None


@dataclass
class IrUnquote(IrNode):
    """Unquote special form; only valid during quasiquote processing."""

    expr: IrNode
    span: SourceSpan | None = None


@dataclass
class IrUnquoteSplicing(IrNode):
    """Unquote-splicing special form; only valid during quasiquote list processing."""

    expr: IrNode
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
class IrPipe(IrNode):
    """Pipeline stage application with Option-aware short-circuit semantics."""

    left: IrNode
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
class IrMap(IrNode):
    """Map literal with lowered values and normalized string keys."""

    items: list[tuple[str, IrNode]]
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
class IrPatMap(IrPattern):
    """Map pattern that requires listed string keys to exist."""

    items: list[tuple[str, IrPattern]]


@dataclass
class IrPatGlob(IrPattern):
    """Whole-string glob pattern matcher."""

    matcher: "CompiledGlobPattern"


@dataclass
class IrPatSome(IrPattern):
    """Option constructor pattern that matches `some(value)` values."""

    inner: IrPattern


@dataclass
class IrPatNone(IrPattern):
    """Option none-family pattern with optional reason and context matching."""

    reason: IrPattern | None = None
    context: IrPattern | None = None


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
class IrImport(IrNode):
    module_name: str
    alias: str
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


def _map_literal_key_name(key: Node) -> str:
    if isinstance(key, Var):
        return key.name
    if isinstance(key, String):
        return key.value
    raise RuntimeError(f"Unsupported map literal key node: {key!r}")


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
    if isinstance(node, NoneOption):
        reason = IrQuote(node.reason, span=node.reason.span) if node.reason is not None else None
        context = lower_node(node.context) if node.context is not None else None
        return IrOptionNone(reason, context, span=node.span)
    if isinstance(node, SymbolLiteral):
        return IrLiteral(symbol(node.name), span=node.span)
    if isinstance(node, Var):
        return IrVar(node.name, span=node.span)
    if isinstance(node, Quote):
        return IrQuote(node.expr, span=node.span)
    if isinstance(node, Delay):
        return IrDelay(lower_node(node.expr), span=node.span)
    if isinstance(node, QuasiQuote):
        return IrQuasiQuote(node.expr, span=node.span)
    if isinstance(node, Unquote):
        return IrUnquote(lower_node(node.expr), span=node.span)
    if isinstance(node, UnquoteSplicing):
        return IrUnquoteSplicing(lower_node(node.expr), span=node.span)
    if isinstance(node, Unary):
        return IrUnary(node.op, lower_node(node.expr), span=node.span)
    if isinstance(node, Binary):
        if node.op == "PIPE_FWD":
            return IrPipe(lower_node(node.left), lower_node(node.right), span=node.span)
        return IrBinary(lower_node(node.left), node.op, lower_node(node.right), span=node.span)
    if isinstance(node, Call):
        return IrCall(lower_node(node.fn), [lower_node(arg) for arg in node.args], span=node.span)
    if isinstance(node, Block):
        return IrBlock([lower_node(expr) for expr in node.exprs], span=node.span)
    if isinstance(node, ListLiteral):
        return IrList([lower_node(item) for item in node.items], span=node.span)
    if isinstance(node, MapLiteral):
        return IrMap([(_map_literal_key_name(key), lower_node(value)) for key, value in node.items], span=node.span)
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
    if isinstance(node, ImportStmt):
        return IrImport(node.module_name, node.alias, span=node.span)
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
    if isinstance(pattern, NoneOption):
        return IrPatNone(
            lower_pattern(pattern.reason) if pattern.reason is not None else None,
            lower_pattern(pattern.context) if pattern.context is not None else None,
        )
    if isinstance(pattern, SymbolLiteral):
        return IrPatLiteral(symbol(pattern.name))
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
    if isinstance(pattern, MapPattern):
        return IrPatMap([(key, lower_pattern(value)) for key, value in pattern.items])
    if isinstance(pattern, GlobPattern):
        return IrPatGlob(compile_glob_pattern(pattern.pattern))
    if isinstance(pattern, SomePattern):
        return IrPatSome(lower_pattern(pattern.inner))
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


QUOTE_OPERATOR_SYMBOLS = {
    "PLUS": "+",
    "MINUS": "-",
    "STAR": "*",
    "SLASH": "/",
    "PERCENT": "%",
    "LT": "<",
    "LE": "<=",
    "GT": ">",
    "GE": ">=",
    "EQEQ": "==",
    "NE": "!=",
    "AND": "&&",
    "OR": "||",
    "PIPE_FWD": "|>",
    "BANG": "!",
}


def quote_node(node: Node) -> Any:
    def quoted_list(items: list[Any]) -> Any:
        result: Any = None
        for item in reversed(items):
            result = GeniaPair(item, result)
        return result

    if isinstance(node, Number):
        return node.value
    if isinstance(node, String):
        return node.value
    if isinstance(node, Boolean):
        return node.value
    if isinstance(node, Nil):
        return None
    if isinstance(node, NoneOption):
        return GeniaOptionNone(
            quote_node(node.reason) if node.reason is not None else None,
            quote_node(node.context) if node.context is not None else None,
        )
    if isinstance(node, SymbolLiteral):
        return symbol(node.name)
    if isinstance(node, Var):
        return symbol(node.name)
    if isinstance(node, Quote):
        return quoted_list([symbol("quote"), quote_node(node.expr)])
    if isinstance(node, Delay):
        return quoted_list([symbol("delay"), quote_node(node.expr)])
    if isinstance(node, QuasiQuote):
        return quoted_list([symbol("quasiquote"), quote_node(node.expr)])
    if isinstance(node, Unquote):
        return quoted_list([symbol("unquote"), quote_node(node.expr)])
    if isinstance(node, UnquoteSplicing):
        return quoted_list([symbol("unquote_splicing"), quote_node(node.expr)])
    if isinstance(node, Unary):
        return quoted_list([symbol("app"), symbol(QUOTE_OPERATOR_SYMBOLS[node.op]), quote_node(node.expr)])
    if isinstance(node, Binary):
        return quoted_list([symbol("app"), symbol(QUOTE_OPERATOR_SYMBOLS[node.op]), quote_node(node.left), quote_node(node.right)])
    if isinstance(node, Call):
        return quoted_list([symbol("app"), quote_node(node.fn), *(quote_node(arg) for arg in node.args)])
    if isinstance(node, Block):
        return quoted_list([symbol("block"), *(quote_node(expr) for expr in node.exprs)])
    if isinstance(node, ListLiteral):
        return quoted_list([quote_node(item) for item in node.items])
    if isinstance(node, MapLiteral):
        result = GeniaMap()
        for key, value in node.items:
            result = result.put(quote_node(key), quote_node(value))
        return result
    if isinstance(node, Assign):
        return quoted_list([symbol("assign"), symbol(node.name), quote_node(node.expr)])
    if isinstance(node, Spread):
        return quoted_list([symbol("spread"), quote_node(node.expr)])
    if isinstance(node, Lambda):
        params = [symbol(name) for name in node.params]
        if node.rest_param is None:
            header: Any = quoted_list(params)
        else:
            header = quoted_list([*params, quoted_list([symbol("rest"), symbol(node.rest_param)])])
        return quoted_list([symbol("lambda"), header, quote_node(node.body)])
    if isinstance(node, CaseExpr):
        return quoted_list([symbol("match"), *(quote_case_clause(clause, quote_node) for clause in node.clauses)])
    raise TypeError(f"quote does not support node type {type(node).__name__}")


def quote_pattern_node(pattern: Node) -> Any:
    def quoted_list(items: list[Any]) -> Any:
        result: Any = None
        for item in reversed(items):
            result = GeniaPair(item, result)
        return result

    if isinstance(pattern, Number):
        return pattern.value
    if isinstance(pattern, String):
        return pattern.value
    if isinstance(pattern, Boolean):
        return pattern.value
    if isinstance(pattern, Nil):
        return None
    if isinstance(pattern, NoneOption):
        return GeniaOptionNone(
            quote_pattern_node(pattern.reason) if pattern.reason is not None else None,
            quote_pattern_node(pattern.context) if pattern.context is not None else None,
        )
    if isinstance(pattern, SymbolLiteral):
        return symbol(pattern.name)
    if isinstance(pattern, Var):
        return symbol(pattern.name)
    if isinstance(pattern, WildcardPattern):
        return symbol("_")
    if isinstance(pattern, RestPattern):
        if pattern.name is None:
            return quoted_list([symbol("rest")])
        return quoted_list([symbol("rest"), symbol(pattern.name)])
    if isinstance(pattern, TuplePattern):
        return quoted_list([symbol("tuple"), *(quote_pattern_node(item) for item in pattern.items)])
    if isinstance(pattern, ListPattern):
        return quoted_list([quote_pattern_node(item) for item in pattern.items])
    if isinstance(pattern, MapPattern):
        result = GeniaMap()
        for key, value in pattern.items:
            result = result.put(key, quote_pattern_node(value))
        return result
    if isinstance(pattern, GlobPattern):
        return quoted_list([symbol("glob"), pattern.pattern])
    if isinstance(pattern, SomePattern):
        return quoted_list([symbol("some"), quote_pattern_node(pattern.inner)])
    raise TypeError(f"quote does not support pattern type {type(pattern).__name__}")


def quote_case_clause(
    clause: CaseClause,
    quote_expr: Callable[[Node], Any],
) -> Any:
    def quoted_list(items: list[Any]) -> Any:
        result: Any = None
        for item in reversed(items):
            result = GeniaPair(item, result)
        return result

    if clause.guard is None:
        return quoted_list([symbol("clause"), quote_pattern_node(clause.pattern), quote_expr(clause.result)])
    return quoted_list([symbol("clause"), quote_pattern_node(clause.pattern), quote_expr(clause.guard), quote_expr(clause.result)])


@dataclass(frozen=True)
class _QuasiquoteSplice:
    items: tuple[Any, ...]


def _quasiquote_splice_items(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, list):
        return tuple(value)
    if isinstance(value, GeniaPair):
        items: list[Any] = []
        current: Any = value
        while isinstance(current, GeniaPair):
            items.append(current.head)
            current = current.tail
        if current is not None:
            raise TypeError("unquote_splicing expected a list or nil-terminated pair chain")
        return tuple(items)
    raise TypeError("unquote_splicing expected a list or nil-terminated pair chain")


def quasiquote_node(
    node: Node,
    env: "Env",
    debug_hooks: "DebugHooks | None" = None,
    debug_mode: bool = False,
) -> Any:
    effective_debug_hooks = debug_hooks or NOOP_DEBUG_HOOKS

    def quoted_list(items: list[Any]) -> Any:
        result: Any = None
        for item in reversed(items):
            result = GeniaPair(item, result)
        return result

    def eval_unquoted(expr: Node) -> Any:
        return Evaluator(env, effective_debug_hooks, debug_mode).eval(lower_node(expr))

    def qq(current: Node, depth: int, *, list_context: bool = False) -> Any:
        if isinstance(current, Number):
            return current.value
        if isinstance(current, String):
            return current.value
        if isinstance(current, Boolean):
            return current.value
        if isinstance(current, Nil):
            return None
        if isinstance(current, NoneOption):
            return GeniaOptionNone(
                qq(current.reason, depth) if current.reason is not None else None,
                qq(current.context, depth) if current.context is not None else None,
            )
        if isinstance(current, Var):
            return symbol(current.name)
        if isinstance(current, SymbolLiteral):
            return symbol(current.name)
        if isinstance(current, Quote):
            return quoted_list([symbol("quote"), quote_node(current.expr)])
        if isinstance(current, Delay):
            return quoted_list([symbol("delay"), qq(current.expr, depth)])
        if isinstance(current, QuasiQuote):
            return quoted_list([symbol("quasiquote"), qq(current.expr, depth + 1)])
        if isinstance(current, Unquote):
            if depth == 1:
                return eval_unquoted(current.expr)
            return quoted_list([symbol("unquote"), qq(current.expr, depth - 1)])
        if isinstance(current, UnquoteSplicing):
            if depth == 1:
                if not list_context:
                    raise RuntimeError("unquote_splicing(...) is only valid in quasiquote list context")
                return _QuasiquoteSplice(_quasiquote_splice_items(eval_unquoted(current.expr)))
            return quoted_list([symbol("unquote_splicing"), qq(current.expr, depth - 1)])
        if isinstance(current, Unary):
            return quoted_list([symbol("app"), symbol(QUOTE_OPERATOR_SYMBOLS[current.op]), qq(current.expr, depth)])
        if isinstance(current, Binary):
            return quoted_list([symbol("app"), symbol(QUOTE_OPERATOR_SYMBOLS[current.op]), qq(current.left, depth), qq(current.right, depth)])
        if isinstance(current, Call):
            return quoted_list([symbol("app"), qq(current.fn, depth), *(qq(arg, depth) for arg in current.args)])
        if isinstance(current, Block):
            return quoted_list([symbol("block"), *(qq(expr, depth) for expr in current.exprs)])
        if isinstance(current, ListLiteral):
            items: list[Any] = []
            for item in current.items:
                if isinstance(item, UnquoteSplicing):
                    resolved = qq(item, depth, list_context=True)
                    if isinstance(resolved, _QuasiquoteSplice):
                        items.extend(resolved.items)
                    else:
                        items.append(resolved)
                    continue
                if isinstance(item, Spread):
                    items.append(quoted_list([symbol("spread"), qq(item.expr, depth)]))
                    continue
                resolved = qq(item, depth)
                if isinstance(resolved, _QuasiquoteSplice):
                    raise RuntimeError("unquote_splicing(...) is only valid in quasiquote list context")
                items.append(resolved)
            return quoted_list(items)
        if isinstance(current, MapLiteral):
            result = GeniaMap()
            for key, value in current.items:
                quoted_value = qq(value, depth)
                if isinstance(quoted_value, _QuasiquoteSplice):
                    raise RuntimeError("unquote_splicing(...) is only valid in quasiquote list context")
                result = result.put(qq(key, depth), quoted_value)
            return result
        if isinstance(current, Assign):
            return quoted_list([symbol("assign"), symbol(current.name), qq(current.expr, depth)])
        if isinstance(current, Spread):
            return quoted_list([symbol("spread"), qq(current.expr, depth)])
        if isinstance(current, Lambda):
            params = [symbol(name) for name in current.params]
            if current.rest_param is None:
                header: Any = quoted_list(params)
            else:
                header = quoted_list([*params, quoted_list([symbol("rest"), symbol(current.rest_param)])])
            return quoted_list([symbol("lambda"), header, qq(current.body, depth)])
        if isinstance(current, CaseExpr):
            return quoted_list([symbol("match"), *(quote_case_clause(clause, lambda expr: qq(expr, depth)) for clause in current.clauses)])
        raise TypeError(f"quasiquote does not support node type {type(current).__name__}")

    return qq(node, 1)


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
    if isinstance(node, IrPipe):
        return recursive_call_count(node.left, fn_name) + recursive_call_count(node.right, fn_name)
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

RESERVED_LITERAL_IDENTIFIERS = frozenset({"true", "false", "nil", "none"})


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

    def next_non_newline_token(self) -> Token:
        j = self.i
        while self.tokens[j].kind == "NEWLINE":
            j += 1
        return self.tokens[j]

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
        if self.at("IDENT") and self.peek().text == "import":
            import_tok = self.eat("IDENT")
            self.skip_newlines()
            if not self.at("IDENT"):
                bad = self.peek()
                raise SyntaxError(f"import expected a module name identifier, got {bad.text!r} ({bad.kind}) at {bad.pos}")
            module_tok = self.eat("IDENT")
            module_name = module_tok.text
            alias = module_name
            end_tok = module_tok
            self.skip_newlines()
            if self.at("IDENT") and self.peek().text == "as":
                self.eat("IDENT")
                self.skip_newlines()
                if not self.at("IDENT"):
                    bad = self.peek()
                    raise SyntaxError(f"import as expected an alias identifier, got {bad.text!r} ({bad.kind}) at {bad.pos}")
                end_tok = self.eat("IDENT")
                alias = end_tok.text
            return ImportStmt(module_name, alias, span=self.span_for_tokens(import_tok, end_tok))

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

        assign = self.try_parse_name_assignment()
        if assign is not None:
            return assign

        expr = self.parse_expr()
        if self.at("ASSIGN"):
            raise SyntaxError("Assignment target must be a simple name")
        return ExprStmt(expr, span=expr.span)

    def try_parse_name_assignment(self) -> Assign | None:
        if not (self.at("IDENT") and self.peek(1).kind == "ASSIGN"):
            return None
        name_tok = self.eat("IDENT")
        name = name_tok.text
        self.eat("ASSIGN")
        self.skip_separators()
        expr = self.parse_expr()
        return Assign(name, expr, span=self.merge_spans(self.span_for_tokens(name_tok, name_tok), expr.span))

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
        parenthesized_case = self.try_parse_parenthesized_case_expr(param_count)
        if parenthesized_case is not None:
            return parenthesized_case
        if self.looks_like_case_start():
            leading_tuple_arity = self.leading_parenthesized_item_count_before_arrow()
            if leading_tuple_arity is not None and leading_tuple_arity != param_count:
                return self.parse_expr()
            return self.parse_case_expr(single_param_shorthand_ok=True)
        return self.parse_expr()

    def try_parse_parenthesized_case_expr(self, param_count: int) -> Node | None:
        if not self.at("LPAREN"):
            return None
        save = self.i
        try:
            self.eat("LPAREN")
            self.skip_separators()
            if not self.looks_like_case_start():
                self.i = save
                return None
            leading_tuple_arity = self.leading_parenthesized_item_count_before_arrow()
            if leading_tuple_arity is not None and leading_tuple_arity != param_count:
                self.i = save
                return None
            case_expr = self.parse_case_expr(single_param_shorthand_ok=True)
            self.skip_separators()
            self.eat("RPAREN")
            return case_expr
        except SyntaxError:
            self.i = save
            return None

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
            assign = self.try_parse_name_assignment()
            if assign is not None:
                exprs.append(assign)
            else:
                expr = self.parse_expr()
                if self.at("ASSIGN"):
                    raise SyntaxError("Assignment target must be a simple name")
                exprs.append(expr)
            self.skip_separators()
        end = self.eat("RBRACE")
        return Block(exprs, span=self.span_for_tokens(start, end))

    def looks_like_case_start(self) -> bool:
        # single param shorthand cases: 0 ->, name ->, [x, y] ->, name ? ... ->
        # tuple case: ( ... ) ->
        # We only detect enough for v0.1.
        if self.at("IDENT") and self.peek(1).kind == "LPAREN":
            depth = 0
            j = self.i + 1
            while True:
                tok = self.tokens[j]
                if tok.kind == "LPAREN":
                    depth += 1
                elif tok.kind == "RPAREN":
                    depth -= 1
                    if depth == 0:
                        j += 1
                        while self.tokens[j].kind == "NEWLINE":
                            j += 1
                        return self.tokens[j].kind in {"ARROW", "QMARK"}
                elif tok.kind == "EOF":
                    return False
                j += 1
        if self.at("NUMBER", "STRING", "IDENT", "GLOB"):
            j = self.i + 1
            while self.tokens[j].kind == "NEWLINE":
                j += 1
            if self.tokens[j].kind in {"ARROW", "QMARK"}:
                return True
        if self.at("LPAREN", "LBRACK", "LBRACE"):
            open_kind = self.peek().kind
            close_kind = {"LPAREN": "RPAREN", "LBRACK": "RBRACK", "LBRACE": "RBRACE"}[open_kind]
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
            if tok.text == "none":
                if self.at("LPAREN"):
                    return self.finish_none_pattern(tok)
                return NoneOption(span=self.span_for_tokens(tok, tok))
            if tok.text == "some" and self.at("LPAREN"):
                start = self.eat("LPAREN")
                self.skip_newlines()
                inner = self.parse_pattern_atom()
                self.skip_newlines()
                if self.at("COMMA"):
                    comma = self.eat("COMMA")
                    raise SyntaxError(f"some(...) pattern expects exactly one inner pattern at {comma.pos}")
                end = self.eat("RPAREN")
                return SomePattern(inner, span=self.span_for_tokens(tok, end))
            if tok.text == "_":
                return WildcardPattern(span=self.span_for_tokens(tok, tok))
            return Var(tok.text, span=self.span_for_tokens(tok, tok))
        if tok.kind == "LBRACK":
            start = self.eat("LBRACK")
            items: list[Node] = []
            saw_rest = False
            self.skip_newlines()
            if not self.at("RBRACK"):
                while True:
                    item = self.parse_pattern_atom()
                    if saw_rest:
                        raise SyntaxError("..rest must be the final item in a list pattern")
                    items.append(item)
                    if isinstance(item, RestPattern):
                        saw_rest = True
                    self.skip_newlines()
                    if not self.maybe("COMMA"):
                        break
                    self.skip_newlines()
            end = self.eat("RBRACK")
            return ListPattern(items, span=self.span_for_tokens(start, end))
        if tok.kind == "LBRACE":
            return self.parse_map_pattern()
        raise SyntaxError(f"Invalid pattern token {tok.text!r} ({tok.kind}) at {tok.pos}")

    def parse_none_reason_pattern_atom(self) -> Node:
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
            if tok.text == "none":
                return NoneOption(span=self.span_for_tokens(tok, tok))
            if tok.text == "_":
                return WildcardPattern(span=self.span_for_tokens(tok, tok))
            return SymbolLiteral(tok.text, span=self.span_for_tokens(tok, tok))
        raise SyntaxError(f"none(...) reason pattern expects a literal, symbol label, or _ at {tok.pos}")

    def finish_none_pattern(self, none_tok: Token) -> Node:
        self.eat("LPAREN")
        self.skip_newlines()
        if self.at("RPAREN"):
            raise SyntaxError(f"none(...) pattern expects 1 or 2 inner patterns at {self.peek().pos}")
        reason = self.parse_none_reason_pattern_atom()
        self.skip_newlines()
        context: Node | None = None
        if self.at("COMMA"):
            self.eat("COMMA")
            self.skip_newlines()
            context = self.parse_pattern_atom()
            self.skip_newlines()
            if self.at("COMMA"):
                comma = self.eat("COMMA")
                raise SyntaxError(f"none(...) pattern expects at most 2 inner patterns at {comma.pos}")
        end = self.eat("RPAREN")
        return NoneOption(reason, context, span=self.span_for_tokens(none_tok, end))

    def finish_none_expr(self, none_tok: Token) -> Node:
        self.eat("LPAREN")
        self.skip_newlines()
        if self.at("RPAREN"):
            raise SyntaxError(f"none(...) expects 1 or 2 arguments at {self.peek().pos}")
        reason = self.parse_expr()
        self.skip_newlines()
        context: Node | None = None
        if self.at("COMMA"):
            self.eat("COMMA")
            self.skip_newlines()
            context = self.parse_expr()
            self.skip_newlines()
            if self.at("COMMA"):
                comma = self.eat("COMMA")
                raise SyntaxError(f"none(...) expects at most 2 arguments at {comma.pos}")
        end = self.eat("RPAREN")
        return NoneOption(reason, context, span=self.span_for_tokens(none_tok, end))

    def parse_expr(self, min_prec: int = 0) -> Node:
        left = self.parse_prefix()
        while True:
            tok = self.peek()
            if tok.kind == "NEWLINE":
                next_tok = self.next_non_newline_token()
                if next_tok.kind == "PIPE_FWD":
                    self.skip_newlines()
                    tok = self.peek()
                else:
                    break
            if tok.kind == "LPAREN":
                left = self.finish_call(left)
                continue
            prec = PRECEDENCE.get(tok.kind)
            if prec is None or prec < min_prec:
                break
            op = tok.kind
            self.i += 1
            if op == "PIPE_FWD":
                self.skip_newlines()
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
            if tok.text == "none":
                if self.at("LPAREN"):
                    return self.finish_none_expr(tok)
                return NoneOption(span=self.span_for_tokens(tok, tok))
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
            return self.parse_brace_expr()
        raise SyntaxError(f"Unexpected token {tok.text!r} ({tok.kind}) at {tok.pos}")

    def parse_brace_expr(self) -> Node:
        save = self.i
        try:
            return self.parse_map_literal()
        except SyntaxError:
            self.i = save
            return self.parse_block(allow_final_case=False)

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

    def parse_map_literal_key(self) -> Node:
        if self.at("IDENT"):
            tok = self.eat("IDENT")
            return Var(tok.text, span=self.span_for_tokens(tok, tok))
        if self.at("STRING"):
            tok = self.eat("STRING")
            return String(parse_string_literal(tok.text), span=self.span_for_tokens(tok, tok))
        tok = self.peek()
        raise SyntaxError(f"Invalid map key token {tok.text!r} ({tok.kind}) at {tok.pos}")

    def parse_map_literal(self) -> MapLiteral:
        start = self.eat("LBRACE")
        self.skip_newlines()
        items: list[tuple[Node, Node]] = []
        if not self.at("RBRACE"):
            while True:
                key = self.parse_map_literal_key()
                self.skip_newlines()
                self.eat("COLON")
                self.skip_newlines()
                value = self.parse_expr()
                items.append((key, value))
                self.skip_separators()
                if not self.maybe("COMMA"):
                    break
                self.skip_newlines()
                if self.at("RBRACE"):
                    break
                self.skip_newlines()
        self.skip_newlines()
        end = self.eat("RBRACE")
        return MapLiteral(items, span=self.span_for_tokens(start, end))

    def parse_map_pattern(self) -> MapPattern:
        start = self.eat("LBRACE")
        self.skip_newlines()
        items: list[tuple[str, Node]] = []
        if not self.at("RBRACE"):
            while True:
                if self.at("IDENT"):
                    key_tok = self.eat("IDENT")
                    key = key_tok.text
                    if self.maybe("COLON"):
                        self.skip_newlines()
                        value_pattern = self.parse_pattern_atom()
                    else:
                        value_pattern = Var(key, span=self.span_for_tokens(key_tok, key_tok))
                    items.append((key, value_pattern))
                elif self.at("STRING"):
                    key_tok = self.eat("STRING")
                    key = parse_string_literal(key_tok.text)
                    if not self.maybe("COLON"):
                        raise SyntaxError(f"Map pattern shorthand is only allowed for identifier keys at {key_tok.pos}")
                    self.skip_newlines()
                    value_pattern = self.parse_pattern_atom()
                    items.append((key, value_pattern))
                else:
                    bad = self.peek()
                    raise SyntaxError(f"Invalid map pattern key token {bad.text!r} ({bad.kind}) at {bad.pos}")

                self.skip_newlines()
                if not self.maybe("COMMA"):
                    break
                self.skip_newlines()
                if self.at("RBRACE"):
                    break
                self.skip_newlines()
        end = self.eat("RBRACE")
        return MapPattern(items, span=self.span_for_tokens(start, end))

    def parse_quoted_form(self) -> Node:
        assign = self.try_parse_name_assignment()
        if assign is not None:
            return assign
        if not self.at("LPAREN") and self.looks_like_case_start():
            return self.parse_case_expr(single_param_shorthand_ok=True)
        expr = self.parse_expr()
        if self.at("ASSIGN"):
            raise SyntaxError("Assignment target must be a simple name")
        return expr

    def finish_call(self, fn: Node) -> Node:
        self.eat("LPAREN")
        self.skip_newlines()
        if isinstance(fn, Var) and fn.name in {"quote", "quasiquote"}:
            if self.at("RPAREN"):
                raise SyntaxError(f"{fn.name}(...) expects exactly one argument")
            expr = self.parse_quoted_form()
            self.skip_separators()
            if self.maybe("COMMA"):
                raise SyntaxError(f"{fn.name}(...) expects exactly one argument")
            self.skip_newlines()
            end = self.eat("RPAREN")
            if isinstance(fn, Var) and fn.name == "quote":
                return Quote(expr, span=self.merge_spans(fn.span, self.span_for_tokens(end, end)))
            return QuasiQuote(expr, span=self.merge_spans(fn.span, self.span_for_tokens(end, end)))
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
        if isinstance(fn, Var) and fn.name == "delay":
            if len(args) != 1:
                raise SyntaxError("delay(...) expects exactly one argument")
            if isinstance(args[0], Spread):
                raise SyntaxError("delay(...) does not accept spread arguments")
            return Delay(args[0], span=self.merge_spans(fn.span, self.span_for_tokens(end, end)))
        if isinstance(fn, Var) and fn.name == "unquote":
            if len(args) != 1:
                raise SyntaxError("unquote(...) expects exactly one argument")
            if isinstance(args[0], Spread):
                raise SyntaxError("unquote(...) does not accept spread arguments")
            return Unquote(args[0], span=self.merge_spans(fn.span, self.span_for_tokens(end, end)))
        if isinstance(fn, Var) and fn.name == "unquote_splicing":
            if len(args) != 1:
                raise SyntaxError("unquote_splicing(...) expects exactly one argument")
            if isinstance(args[0], Spread):
                raise SyntaxError("unquote_splicing(...) does not accept spread arguments")
            return UnquoteSplicing(args[0], span=self.merge_spans(fn.span, self.span_for_tokens(end, end)))
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
    def __init__(self, parent: Optional["Env"] = None, *, rebind_parent: bool | None = None):
        self.parent = parent
        self.values: dict[str, Any] = {}
        self.assignable: set[str] = set()
        self.rebind_parent = (parent is not None) if rebind_parent is None else rebind_parent
        self.autoloads: dict[tuple[str, int], str] = {}
        self.loaded_files: set[str] = set()
        self.loading_files: set[str] = set()
        self.loaded_modules: dict[str, "ModuleValue"] = {}
        self.loading_modules: set[str] = set()
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
        if self.try_autoload(name, 0) and name in self.values:
            return self.values[name]
        raise NameError(f"Undefined name: {name}")

    def set(self, name: str, value: Any, *, assignable: bool = True) -> None:
        self.values[name] = value
        if assignable:
            self.assignable.add(name)
        else:
            self.assignable.discard(name)

    def assign(self, name: str, value: Any) -> None:
        target_env = self.find_assign_target(name)
        if target_env is None:
            self.set(name, value, assignable=True)
            return
        target_env.values[name] = value

    def find_assign_target(self, name: str) -> Optional["Env"]:
        env: Env = self
        while True:
            if name in env.values:
                if name in env.assignable:
                    return env
                raise NameError(f"Cannot assign to non-assignable name: {name}")
            if env.parent is None or not env.rebind_parent:
                return None
            env = env.parent

    def define_function(self, fn: "GeniaFunction") -> None:
        existing = self.values.get(fn.name)
        if existing is None:
            group = GeniaFunctionGroup(fn.name)
            group.add_clause(fn)
            self.set(fn.name, group, assignable=True)
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

        source, key = _load_source_from_path(path)

        if key in root.loaded_files:
            return True

        if key in root.loading_files:
            raise RuntimeError(f"Autoload cycle detected while loading {key}")

        root.loading_files.add(key)
        try:
            run_source(source, root, filename=key, debug_hooks=root.debug_hooks, debug_mode=root.debug_mode)
            root.loaded_files.add(key)
            return True
        finally:
            root.loading_files.remove(key)

    def resolve_module_source(self, module_name: str, requester_filename: str | None = None) -> tuple[str, str]:
        candidates: list[Path] = []
        if requester_filename and requester_filename not in {"<memory>", "<command>"}:
            requester = Path(requester_filename)
            candidates.append((requester.parent / f"{module_name}.genia").resolve())
        candidates.append((BASE_DIR / f"{module_name}.genia").resolve())
        for path in candidates:
            if path.is_file():
                return path.read_text(encoding="utf-8"), str(path)
        packaged = _resolve_packaged_module(module_name)
        if packaged is not None:
            return packaged
        raise FileNotFoundError(f"Module not found: {module_name}")

    def load_module(self, module_name: str, requester_filename: str | None = None) -> "ModuleValue":
        root = self.root()
        if module_name in root.loaded_modules:
            return root.loaded_modules[module_name]
        if module_name in root.loading_modules:
            raise RuntimeError(f"Module import cycle detected while loading {module_name}")

        source, key = root.resolve_module_source(module_name, requester_filename)
        root.loading_modules.add(module_name)
        try:
            module_env = Env(root, rebind_parent=False)
            module_env.debug_hooks = root.debug_hooks
            module_env.debug_mode = root.debug_mode
            run_source(source, module_env, filename=key, debug_hooks=root.debug_hooks, debug_mode=root.debug_mode)
            exports = dict(module_env.values)
            module_value = ModuleValue(module_name, exports, key)
            root.loaded_modules[module_name] = module_value
            return module_value
        finally:
            root.loading_modules.remove(module_name)


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

    def __call__(self, *args: Any) -> Any:
        arity = len(args)
        exact = self.get(arity)
        if exact is not None:
            return exact(*args)
        vararg_matches = [
            candidate
            for candidate in self.values()
            if isinstance(candidate, GeniaFunction)
            and candidate.rest_param is not None
            and arity >= candidate.arity
        ]
        if len(vararg_matches) == 1:
            return vararg_matches[0](*args)
        if len(vararg_matches) > 1:
            candidates = ", ".join(
                f"{self.name}/{candidate.arity}+"
                for candidate in sorted(vararg_matches, key=lambda fn: fn.arity)
            )
            raise TypeError(f"Ambiguous function resolution: {self.name}/{arity}. Matching varargs: {candidates}")
        available = ", ".join(f"{self.name}/{n}" for n in self.sorted_arities())
        raise TypeError(f"No matching function: {self.name}/{arity}. Available: {available}")



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
_CELL_TX = threading.local()


def _cell_tx_stack() -> list[list[tuple[str, Any, Any]]]:
    stack = getattr(_CELL_TX, "stack", None)
    if stack is None:
        stack = []
        _CELL_TX.stack = stack
    return stack


def _push_cell_tx() -> list[tuple[str, Any, Any]]:
    actions: list[tuple[str, Any, Any]] = []
    _cell_tx_stack().append(actions)
    return actions


def _pop_cell_tx() -> list[tuple[str, Any, Any]]:
    stack = _cell_tx_stack()
    if not stack:
        return []
    actions = stack.pop()
    if not stack:
        try:
            delattr(_CELL_TX, "stack")
        except AttributeError:
            pass
    return actions


def _stage_cell_action(kind: str, first: Any, second: Any) -> bool:
    stack = getattr(_CELL_TX, "stack", None)
    if not stack:
        return False
    stack[-1].append((kind, first, second))
    return True


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


class GeniaCell:
    def __init__(self, state_ref: GeniaRef):
        self._state_ref = state_ref
        self._condition = threading.Condition()
        self._failed = False
        self._error: str | None = None
        self._generation = 0
        self._mailbox: queue.Queue[tuple[int, Any]] = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _error_text(self, exc: BaseException) -> str:
        message = str(exc).strip()
        name = type(exc).__name__
        return f"{name}: {message}" if message else name

    def _commit_actions(self, actions: list[tuple[str, Any, Any]]) -> None:
        for kind, first, second in actions:
            if kind == "cell_send":
                first.send(second)
                continue
            if kind == "process_send":
                first.send(second)
                continue
            raise RuntimeError(f"Unknown cell action kind: {kind}")

    def _run(self) -> None:
        while True:
            generation, update_fn = self._mailbox.get()
            with self._condition:
                if generation != self._generation or self._failed:
                    continue

            try:
                _push_cell_tx()
                try:
                    current_state = self._state_ref.get()
                    next_state = update_fn(current_state)
                finally:
                    actions = _pop_cell_tx()

                with self._condition:
                    if generation != self._generation or self._failed:
                        continue
                    self._commit_actions(actions)
                    self._state_ref.set(next_state)
            except Exception as exc:
                with self._condition:
                    if generation != self._generation:
                        continue
                    self._failed = True
                    self._error = self._error_text(exc)
                    self._condition.notify_all()

    def send(self, update_fn: Any) -> None:
        with self._condition:
            if self._failed:
                raise RuntimeError(f"Cell has failed: {self._error}")
            generation = self._generation
        self._mailbox.put((generation, update_fn))

    def get(self) -> Any:
        with self._condition:
            if self._failed:
                raise RuntimeError(f"Cell has failed: {self._error}")
        return self._state_ref.get()

    def failed(self) -> bool:
        with self._condition:
            return self._failed

    def error_option(self) -> Any:
        with self._condition:
            if self._failed and self._error is not None:
                return GeniaOptionSome(self._error)
            return OPTION_NONE

    def restart(self, value: Any) -> "GeniaCell":
        with self._condition:
            self._generation += 1
            self._failed = False
            self._error = None
            self._state_ref.set(value)
            self._condition.notify_all()
        return self

    def status(self) -> str:
        with self._condition:
            return "failed" if self._failed else "ready"

    def is_alive(self) -> bool:
        return self._thread.is_alive()

    def __repr__(self) -> str:
        return f"<cell {self.status()}>"


@dataclass(frozen=True)
class GeniaSymbol:
    name: str

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class GeniaPair:
    head: Any
    tail: Any

    def __repr__(self) -> str:
        return f"Pair({self.head!r}, {self.tail!r})"


class GeniaPromise:
    def __init__(
        self,
        expr: IrNode,
        env: "Env",
        debug_hooks: DebugHooks = NOOP_DEBUG_HOOKS,
        debug_mode: bool = False,
    ):
        self._expr = expr
        self._env = env
        self._debug_hooks = debug_hooks
        self._debug_mode = debug_mode
        self._forced = False
        self._forcing = False
        self._value: Any = None

    def force(self) -> Any:
        if self._forced:
            return self._value
        if self._forcing:
            raise RuntimeError("Promise is already being forced")
        self._forcing = True
        try:
            value = Evaluator(self._env, self._debug_hooks, self._debug_mode).eval(self._expr)
        except Exception:
            self._forcing = False
            raise
        self._value = value
        self._forced = True
        self._forcing = False
        return value

    def status(self) -> str:
        if self._forcing:
            return "forcing"
        if self._forced:
            return "forced"
        return "delayed"

    def __repr__(self) -> str:
        return f"<promise {self.status()}>"

    def __str__(self) -> str:
        return repr(self)


class GeniaMetaEnv:
    def __init__(self, env: Env):
        self._env = env

    @property
    def env(self) -> Env:
        return self._env

    def lookup(self, name: str) -> Any:
        try:
            return self._env.get(name)
        except NameError:
            if self._env.try_autoload(name, 0):
                return self._env.get(name)
            raise

    def define(self, name: str, value: Any) -> "GeniaMetaEnv":
        self._env.set(name, value)
        return self

    def assign(self, name: str, value: Any) -> Any:
        self._env.assign(name, value)
        return value

    def extend(self, params: Any, args: list[Any]) -> "GeniaMetaEnv":
        required, rest = self._parse_params(params)
        if rest is None:
            if len(args) != len(required):
                raise TypeError(f"extend expected {len(required)} args, got {len(args)}")
        elif len(args) < len(required):
            raise TypeError(f"extend expected at least {len(required)} args, got {len(args)}")

        child = Env(self._env)
        for index, name in enumerate(required):
            child.set(name, args[index])
        if rest is not None:
            child.set(rest, args[len(required):])
        return GeniaMetaEnv(child)

    def _parse_params(self, params: Any) -> tuple[list[str], str | None]:
        required: list[str] = []
        rest_name: str | None = None
        current = params
        while isinstance(current, GeniaPair):
            item = current.head
            if isinstance(item, GeniaSymbol):
                if rest_name is not None:
                    raise TypeError("extend expected rest parameter to be final")
                required.append(item.name)
            elif _syntax_tagged_list(item, symbol("rest")):
                if rest_name is not None or current.tail is not None:
                    raise TypeError("extend expected at most one final rest parameter")
                rest_value = _syntax_pair_nth(item, 1, "extend")
                if not isinstance(rest_value, GeniaSymbol):
                    raise TypeError("extend expected the rest parameter name to be a symbol")
                rest_name = rest_value.name
            else:
                raise TypeError("extend expected lambda parameter data")
            current = current.tail
        if current is not None:
            raise TypeError("extend expected lambda parameter data")
        return required, rest_name

    def __repr__(self) -> str:
        return "<meta-env>"


_SYMBOL_INTERN_TABLE: dict[str, GeniaSymbol] = {}


def symbol(name: str) -> GeniaSymbol:
    existing = _SYMBOL_INTERN_TABLE.get(name)
    if existing is not None:
        return existing
    created = GeniaSymbol(name)
    _SYMBOL_INTERN_TABLE[name] = created
    return created


def _freeze_map_key(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, GeniaSymbol):
        return ("symbol", value.name)
    if isinstance(value, GeniaPair):
        return ("pair", _freeze_map_key(value.head), _freeze_map_key(value.tail))
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


@dataclass(frozen=True)
class GeniaOptionNone:
    reason: Any = None
    context: Any = None

    def __repr__(self) -> str:
        if self.reason is None and self.context is None:
            return "none"
        if self.context is None:
            return f"none({self.reason!r})"
        return f"none({self.reason!r}, {self.context!r})"


OPTION_NONE = GeniaOptionNone()


@dataclass(frozen=True)
class GeniaOptionSome:
    value: Any

    def __repr__(self) -> str:
        return f"some({self.value!r})"


@dataclass(frozen=True)
class ModuleValue:
    name: str
    exports: dict[str, Any]
    path: str

    def get_export(self, export_name: str) -> Any:
        if export_name not in self.exports:
            raise NameError(f"Module {self.name} has no export named {export_name}")
        return self.exports[export_name]

    def __repr__(self) -> str:
        return f"<module {self.name}>"


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


class GeniaQuietBrokenPipe(Exception):
    pass


class GeniaFlow:
    def __init__(self, iterator_factory: Callable[[], Iterable[Any]], *, label: str = "flow"):
        self._iterator_factory = iterator_factory
        self._label = label
        self._consumed = False

    def consume(self) -> Iterable[Any]:
        if self._consumed:
            raise RuntimeError("Flow has already been consumed")
        self._consumed = True
        return self._iterator_factory()

    def __repr__(self) -> str:
        state = "consumed" if self._consumed else "ready"
        return f"<flow {self._label} {state}>"


class GeniaOutputSink:
    def __init__(
        self,
        name: str,
        *,
        stream: Any | None = None,
        writer: Callable[[str], Any] | None = None,
        swallow_broken_pipe: bool = False,
    ):
        self.name = name
        self._stream = stream
        self._writer = writer
        self._swallow_broken_pipe = swallow_broken_pipe

    def write_text(self, text: str) -> None:
        try:
            if self._writer is not None:
                self._writer(text)
            elif self._stream is not None:
                self._stream.write(text)
            else:
                raise RuntimeError(f"{self.name} sink is not configured")
        except BrokenPipeError:
            if self._swallow_broken_pipe:
                return
            raise GeniaQuietBrokenPipe() from None

    def flush(self) -> None:
        try:
            if self._stream is not None and hasattr(self._stream, "flush"):
                self._stream.flush()
        except BrokenPipeError:
            if self._swallow_broken_pipe:
                return
            raise GeniaQuietBrokenPipe() from None

    def __repr__(self) -> str:
        return f"<{self.name}>"


class GeniaStdinSource:
    def __init__(self, iterator_factory: Callable[[], Iterable[str]]):
        self._iterator_factory = iterator_factory
        self._iterator: Iterator[str] | None = None
        self._cache: list[str] = []
        self._exhausted = False

    def _ensure_iterator(self) -> Iterator[str] | None:
        if self._exhausted:
            return None
        if self._iterator is None:
            self._iterator = iter(self._iterator_factory())
        return self._iterator

    def iter_lines(self) -> Iterable[str]:
        while True:
            iterator = self._ensure_iterator()
            if iterator is None:
                return
            try:
                item = next(iterator)
            except StopIteration:
                self._iterator = None
                self._exhausted = True
                return
            if not isinstance(item, str):
                raise TypeError("stdin expected string input items")
            normalized = item.rstrip("\r\n")
            self._cache.append(normalized)
            yield normalized

    def materialize(self) -> list[str]:
        if not self._exhausted:
            for _ in self.iter_lines():
                pass
        return list(self._cache)

    def __call__(self) -> list[str]:
        return self.materialize()

    def __repr__(self) -> str:
        state = "exhausted" if self._exhausted else "ready"
        return f"<stdin-source {state}>"


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
        if isinstance(node, IrPipe):
            return self.eval_pipe(node, tail_position=True)
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

    def eval_pipe(self, node: IrPipe, tail_position: bool) -> Any:
        stage_value = self.eval(node.left)
        if isinstance(stage_value, GeniaOptionNone):
            return stage_value
        if isinstance(stage_value, GeniaOptionSome):
            stage_value = stage_value.value
        return self.eval_pipe_stage(node.right, stage_value, tail_position=tail_position)

    def eval_pipe_stage(self, node: IrNode, stage_value: Any, *, tail_position: bool) -> Any:
        if isinstance(node, IrCall):
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
                    if self.env.try_autoload(name, len(args) + 1):
                        fn = self.env.get(name)
                    else:
                        raise
            else:
                fn = self.eval(node.fn)

            return self.invoke_callable(fn, [*args, stage_value], tail_position=tail_position, callee_node=node.fn)

        if isinstance(node, IrVar):
            try:
                fn_value = self.env.get(node.name)
            except NameError:
                if self.env.try_autoload(node.name, 1):
                    fn_value = self.env.get(node.name)
                else:
                    raise
        else:
            fn_value = self.eval(node)
        return self.invoke_callable(fn_value, [stage_value], tail_position=tail_position, callee_node=node)

    def invoke_callable(
        self,
        fn: Any,
        args: list[Any],
        *,
        tail_position: bool,
        callee_node: IrNode | None = None,
    ) -> Any:

        if isinstance(fn, GeniaFunctionGroup):
            if isinstance(callee_node, IrVar) and len(args) == 2 and isinstance(args[1], GeniaFlow):
                if callee_node.name == "map":
                    mapper = args[0]
                    source = args[1]

                    def iterator() -> Iterable[Any]:
                        for item in source.consume():
                            yield self.invoke_callable(mapper, [item], tail_position=False)

                    return GeniaFlow(iterator, label="map")
                if callee_node.name == "filter":
                    predicate = args[0]
                    source = args[1]

                    def iterator() -> Iterable[Any]:
                        for item in source.consume():
                            if self.invoke_callable(predicate, [item], tail_position=False):
                                yield item

                    return GeniaFlow(iterator, label="filter")
                if callee_node.name == "take":
                    count = args[0]
                    source = args[1]
                    if not isinstance(count, int) or isinstance(count, bool):
                        raise TypeError("take expected an integer count as first argument")

                    def iterator() -> Iterable[Any]:
                        if count <= 0:
                            return
                        remaining = count
                        upstream = iter(source.consume())
                        while remaining > 0:
                            try:
                                item = next(upstream)
                            except StopIteration:
                                return
                            yield item
                            remaining -= 1

                    return GeniaFlow(iterator, label="take")
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
            if tail_position:
                return TailCall(target, tuple(args))
            return target(*args)

        if isinstance(fn, GeniaMap):
            arg_count = len(args)
            if arg_count == 1:
                return fn.get(args[0])
            if arg_count == 2:
                key = args[0]
                if fn.has(key):
                    return fn.get(key)
                return args[1]
            raise TypeError(f"map callable expected 1 or 2 args, got {arg_count}")

        if isinstance(fn, str):
            arg_count = len(args)
            if arg_count not in (1, 2):
                raise TypeError(f"string projector expected 1 or 2 args, got {arg_count}")
            target = args[0]
            if not isinstance(target, GeniaMap):
                raise TypeError("string projector expected a map-like target as first argument")
            if arg_count == 2 and not target.has(fn):
                return args[1]
            return target.get(fn)

        if tail_position:
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
        if isinstance(pattern, IrPatNone):
            if not isinstance(arg, GeniaOptionNone):
                return None
            env: dict[str, Any] = {}
            if pattern.reason is not None:
                reason_bindings = self.match_pattern_atom(pattern.reason, arg.reason)
                if reason_bindings is None:
                    return None
                env.update(reason_bindings)
            if pattern.context is not None:
                context_bindings = self.match_pattern_atom(pattern.context, arg.context)
                if context_bindings is None:
                    return None
                for k, v in context_bindings.items():
                    if k in env and env[k] != v:
                        return None
                    env[k] = v
            return env
        if isinstance(pattern, IrPatSome):
            if not isinstance(arg, GeniaOptionSome):
                return None
            return self.match_pattern_atom(pattern.inner, arg.value)
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
        if isinstance(pattern, IrPatMap):
            if not isinstance(arg, GeniaMap):
                return None
            env: dict[str, Any] = {}
            for key, value_pattern in pattern.items:
                if not arg.has(key):
                    return None
                value = arg.get(key)
                sub = self.match_pattern_atom(value_pattern, value)
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
        if isinstance(node, IrOptionNone):
            reason = self.eval(node.reason) if node.reason is not None else None
            context = self.eval(node.context) if node.context is not None else None
            if reason is None and context is None:
                return OPTION_NONE
            return GeniaOptionNone(reason, context)
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
        if isinstance(node, IrMap):
            result = GeniaMap()
            for key, value_node in node.items:
                result = result.put(key, self.eval(value_node))
            return result
        if isinstance(node, IrQuote):
            return quote_node(node.expr)
        if isinstance(node, IrQuasiQuote):
            return quasiquote_node(node.expr, self.env, self.debug_hooks, self.debug_mode)
        if isinstance(node, IrDelay):
            return GeniaPromise(node.expr, self.env, self.debug_hooks, self.debug_mode)
        if isinstance(node, IrUnquote):
            raise RuntimeError("unquote(...) is only valid inside quasiquote")
        if isinstance(node, IrUnquoteSplicing):
            raise RuntimeError("unquote_splicing(...) is only valid inside quasiquote")
        if isinstance(node, IrVar):
            try:
                return self.env.get(node.name)
            except NameError:
                if self.env.try_autoload(node.name, 0):
                    return self.env.get(node.name)
                raise
        if isinstance(node, IrUnary):
            value = self.eval(node.expr)
            if node.op == "MINUS":
                return -value
            if node.op == "BANG":
                return not truthy(value)
            raise RuntimeError(f"Unknown unary operator {node.op}")
        if isinstance(node, IrPipe):
            return self.eval_pipe(node, tail_position=False)
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
            self.env.assign(node.name, value)
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
        if isinstance(node, IrImport):
            requester = node.span.filename if node.span is not None else None
            module_value = self.env.load_module(node.module_name, requester)
            self.env.set(node.alias, module_value)
            return module_value
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
        if node.op == "SLASH" and isinstance(left, (GeniaMap, ModuleValue)):
            if isinstance(node.right, IrVar):
                key_name = node.right.name
                if isinstance(left, GeniaMap):
                    return left.get(key_name)
                return left.get_export(key_name)
            if isinstance(node.right, IrCall) and isinstance(node.right.fn, IrVar):
                key_name = node.right.fn.name
                if isinstance(left, GeniaMap):
                    callee = left.get(key_name)
                else:
                    callee = left.get_export(key_name)
                args: list[Any] = []
                for arg_node in node.right.args:
                    if isinstance(arg_node, IrSpread):
                        value = self.eval(arg_node.expr)
                        if not isinstance(value, list):
                            raise TypeError("Cannot spread non-list into function arguments")
                        args.extend(value)
                    else:
                        args.append(self.eval(arg_node))
                return self.invoke_callable(callee, args, tail_position=False, callee_node=node.right.fn)
            raise TypeError("named accessor '/' requires a bare identifier on the right-hand side")
        try:
            right = self.eval(node.right)
        except NameError:
            if node.op == "SLASH" and isinstance(node.right, IrVar):
                raise TypeError("named accessor '/' is only supported for map and module values") from None
            raise
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


def _runtime_type_name(value: Any) -> str:
    if value is None:
        return "nil"
    if isinstance(value, GeniaOptionNone):
        return "none"
    if isinstance(value, GeniaOptionSome):
        return "some"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    if isinstance(value, GeniaMap):
        return "map"
    if isinstance(value, GeniaFlow):
        return "flow"
    if isinstance(value, GeniaRef):
        return "ref"
    if isinstance(value, GeniaProcess):
        return "process"
    if isinstance(value, GeniaOutputSink):
        return "sink"
    if isinstance(value, GeniaBytes):
        return "bytes"
    if isinstance(value, GeniaZipEntry):
        return "zip_entry"
    if isinstance(value, GeniaPair):
        return "pair"
    if isinstance(value, GeniaMetaEnv):
        return "meta_env"
    if isinstance(value, GeniaPromise):
        return "promise"
    if isinstance(value, GeniaFunctionGroup):
        return "function"
    if callable(value):
        return "function"
    return type(value).__name__


def _syntax_tagged_list(value: Any, tag: Any) -> bool:
    return isinstance(value, GeniaPair) and value.head == tag


def _syntax_pair_nth(value: Any, index: int, name: str) -> Any:
    current = value
    for _ in range(index):
        if not isinstance(current, GeniaPair):
            raise TypeError(f"{name} expected the quoted form to have enough parts")
        current = current.tail
    if not isinstance(current, GeniaPair):
        raise TypeError(f"{name} expected the quoted form to have enough parts")
    return current.head


def _syntax_reserved_tag_name(value: Any) -> str | None:
    if isinstance(value, GeniaSymbol):
        if value.name in {
            "quote",
            "quasiquote",
            "app",
            "assign",
            "lambda",
            "block",
            "match",
            "delay",
            "unquote",
            "unquote_splicing",
            "spread",
            "clause",
            "tuple",
            "rest",
            "glob",
            "some",
        }:
            return value.name
    return None


# -----------------------------
# Builtins / REPL
# -----------------------------

def make_global_env(
    stdin_data: Optional[list[str]] = None,
    stdin_provider: Optional[Callable[[], Iterable[str]]] = None,
    cli_args: Optional[list[str]] = None,
    debug_hooks: DebugHooks | None = None,
    debug_mode: bool = False,
    stdout_stream: Any = None,
    stderr_stream: Any = None,
    output_handler: Optional[Callable[[str], None]] = None,
) -> Env:
    env = Env()
    env.debug_hooks = debug_hooks or NOOP_DEBUG_HOOKS
    env.debug_mode = debug_mode

    stdout_sink = GeniaOutputSink(
        "stdout",
        stream=stdout_stream if stdout_stream is not None else sys.stdout,
        writer=output_handler,
    )
    stderr_sink = GeniaOutputSink(
        "stderr",
        stream=stderr_stream if stderr_stream is not None else sys.stderr,
        swallow_broken_pipe=True,
    )

    def _ensure_sink(value: Any, name: str) -> GeniaOutputSink:
        if not isinstance(value, GeniaOutputSink):
            raise TypeError(f"{name} expected a sink")
        return value

    def _ensure_meta_env(value: Any, name: str) -> GeniaMetaEnv:
        if not isinstance(value, GeniaMetaEnv):
            raise TypeError(f"{name} expected a metacircular environment")
        return value

    def _meta_symbol_name(value: Any, name: str) -> str:
        if isinstance(value, GeniaSymbol):
            return value.name
        if isinstance(value, str):
            return value
        raise TypeError(f"{name} expected a symbol or string name")

    def _meta_operator_add(left: Any, right: Any) -> Any:
        return left + right

    def _meta_operator_sub(*args: Any) -> Any:
        if len(args) == 1:
            return -args[0]
        if len(args) == 2:
            return args[0] - args[1]
        raise TypeError(f"- expected 1 or 2 args, got {len(args)}")

    def _meta_operator_mul(left: Any, right: Any) -> Any:
        return left * right

    def _meta_operator_div(left: Any, right: Any) -> Any:
        return left / right

    def _meta_operator_mod(left: Any, right: Any) -> Any:
        return left % right

    def _meta_operator_lt(left: Any, right: Any) -> Any:
        return left < right

    def _meta_operator_le(left: Any, right: Any) -> Any:
        return left <= right

    def _meta_operator_gt(left: Any, right: Any) -> Any:
        return left > right

    def _meta_operator_ge(left: Any, right: Any) -> Any:
        return left >= right

    def _meta_operator_eq(left: Any, right: Any) -> Any:
        return left == right

    def _meta_operator_ne(left: Any, right: Any) -> Any:
        return left != right

    def _meta_operator_not(value: Any) -> Any:
        return not value

    def _make_meta_env() -> GeniaMetaEnv:
        base = Env(env, rebind_parent=False)
        for name, operator in {
            "+": _meta_operator_add,
            "-": _meta_operator_sub,
            "*": _meta_operator_mul,
            "/": _meta_operator_div,
            "%": _meta_operator_mod,
            "<": _meta_operator_lt,
            "<=": _meta_operator_le,
            ">": _meta_operator_gt,
            ">=": _meta_operator_ge,
            "==": _meta_operator_eq,
            "!=": _meta_operator_ne,
            "!": _meta_operator_not,
        }.items():
            base.set(name, operator, assignable=False)
        return GeniaMetaEnv(base)

    def _sink_write_display(sink: GeniaOutputSink, value: Any, *, newline: bool) -> Any:
        text = format_display(value)
        if newline:
            text += "\n"
        sink.write_text(text)
        return value

    def write_fn(sink_value: Any, value: Any) -> Any:
        sink = _ensure_sink(sink_value, "write")
        return _sink_write_display(sink, value, newline=False)

    def writeln_fn(sink_value: Any, value: Any) -> Any:
        sink = _ensure_sink(sink_value, "writeln")
        return _sink_write_display(sink, value, newline=True)

    def flush_fn(sink_value: Any) -> None:
        sink = _ensure_sink(sink_value, "flush")
        sink.flush()
        return None

    def meta_empty_env_fn() -> GeniaMetaEnv:
        return _make_meta_env()

    def meta_lookup_fn(meta_env_value: Any, name_value: Any) -> Any:
        meta_env = _ensure_meta_env(meta_env_value, "lookup")
        return meta_env.lookup(_meta_symbol_name(name_value, "lookup"))

    def meta_define_fn(meta_env_value: Any, name_value: Any, value: Any) -> GeniaMetaEnv:
        meta_env = _ensure_meta_env(meta_env_value, "define")
        meta_env.define(_meta_symbol_name(name_value, "define"), value)
        return meta_env

    def meta_set_fn(meta_env_value: Any, name_value: Any, value: Any) -> Any:
        meta_env = _ensure_meta_env(meta_env_value, "set")
        return meta_env.assign(_meta_symbol_name(name_value, "set"), value)

    def meta_extend_fn(meta_env_value: Any, params: Any, args: Any) -> GeniaMetaEnv:
        meta_env = _ensure_meta_env(meta_env_value, "extend")
        if not isinstance(args, list):
            raise TypeError("extend expected a list of argument values")
        return meta_env.extend(params, args)

    def meta_host_apply_fn(proc: Any, args: Any) -> Any:
        if not isinstance(args, list):
            raise TypeError("apply expected a list of positional arguments")
        return Evaluator(env, env.debug_hooks, env.debug_mode).invoke_callable(
            proc,
            args,
            tail_position=False,
            callee_node=None,
        )

    def meta_eval_error_fn(expr: Any) -> Any:
        raise RuntimeError(f"metacircular eval does not support expression: {format_debug(expr)}")

    def _meta_lower_quoted_pattern(pattern: Any) -> IrPattern:
        if pattern is None or isinstance(pattern, (bool, int, float, str)):
            return IrPatLiteral(pattern)
        if isinstance(pattern, GeniaOptionNone):
            reason = _meta_lower_quoted_pattern(pattern.reason) if pattern.reason is not None else None
            context = _meta_lower_quoted_pattern(pattern.context) if pattern.context is not None else None
            return IrPatNone(reason, context)
        if isinstance(pattern, GeniaSymbol):
            if pattern.name == "_":
                return IrPatWildcard()
            return IrPatBind(pattern.name)
        if isinstance(pattern, GeniaMap):
            items: list[tuple[str, IrPattern]] = []
            for _, (original_key, original_value) in pattern._entries.items():
                if not isinstance(original_key, str):
                    raise TypeError("metacircular quoted map patterns require string keys")
                items.append((original_key, _meta_lower_quoted_pattern(original_value)))
            return IrPatMap(items)
        if isinstance(pattern, GeniaPair):
            if _syntax_tagged_list(pattern, symbol("rest")):
                if pattern.tail is None:
                    return IrPatRest(None)
                rest_name = _syntax_pair_nth(pattern, 1, "_meta_match_pattern_env")
                if not isinstance(rest_name, GeniaSymbol):
                    raise TypeError("metacircular rest patterns require a symbol name")
                if pattern.tail.tail is not None:
                    raise TypeError("metacircular rest patterns accept at most one symbol name")
                return IrPatRest(rest_name.name)
            if _syntax_tagged_list(pattern, symbol("tuple")):
                items: list[IrPattern] = []
                current = pattern.tail
                while current is not None:
                    if not isinstance(current, GeniaPair):
                        raise TypeError("metacircular tuple patterns must be proper lists")
                    items.append(_meta_lower_quoted_pattern(current.head))
                    current = current.tail
                return IrPatTuple(items)
            if _syntax_tagged_list(pattern, symbol("glob")):
                glob_text = _syntax_pair_nth(pattern, 1, "_meta_match_pattern_env")
                if not isinstance(glob_text, str):
                    raise TypeError("metacircular glob patterns require a string")
                if pattern.tail.tail is not None:
                    raise TypeError("metacircular glob patterns accept exactly one string")
                return IrPatGlob(compile_glob_pattern(glob_text))
            if _syntax_tagged_list(pattern, symbol("some")):
                if pattern.tail is None or not isinstance(pattern.tail, GeniaPair):
                    raise TypeError("metacircular some patterns require an inner pattern")
                if pattern.tail.tail is not None:
                    raise TypeError("metacircular some patterns accept exactly one inner pattern")
                return IrPatSome(_meta_lower_quoted_pattern(pattern.tail.head))
            items: list[IrPattern] = []
            current = pattern
            while current is not None:
                if not isinstance(current, GeniaPair):
                    raise TypeError("metacircular list patterns must be proper lists")
                items.append(_meta_lower_quoted_pattern(current.head))
                current = current.tail
            return IrPatList(items)
        raise TypeError(f"metacircular quoted match pattern is unsupported: {format_debug(pattern)}")

    def meta_match_pattern_env_fn(meta_env_value: Any, pattern: Any, args: Any) -> Any:
        meta_env = _ensure_meta_env(meta_env_value, "_meta_match_pattern_env")
        if not isinstance(args, list):
            raise TypeError("_meta_match_pattern_env expected a list of argument values")
        bindings = Evaluator(meta_env.env, env.debug_hooks, env.debug_mode).match_pattern(
            _meta_lower_quoted_pattern(pattern),
            tuple(args),
        )
        if bindings is None:
            return OPTION_NONE
        child = Env(meta_env.env)
        for name, value in bindings.items():
            child.set(name, value)
        return GeniaOptionSome(GeniaMetaEnv(child))

    def meta_match_error_fn(expr: Any, args: Any) -> Any:
        raise RuntimeError(
            f"metacircular match failed for {format_debug(expr)} with args {format_debug(args)}"
        )

    def log(*args: Any) -> Any:
        output = " ".join(format_display(arg) for arg in args)
        stderr_sink.write_text(output + "\n")
        return args[-1] if args else None

    def print_fn(*args: Any) -> Any:
        output = " ".join(format_display(arg) for arg in args)
        stdout_sink.write_text(output + "\n")
        return args[-1] if args else None

    def _ensure_string(value: Any, name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{name} expected a string, received {_runtime_type_name(value)}")
        return value

    def _ensure_bytes(value: Any, name: str) -> GeniaBytes:
        if not isinstance(value, GeniaBytes):
            raise TypeError(f"{name} expected bytes, received {_runtime_type_name(value)}")
        return value

    def _ensure_zip_entry(value: Any, name: str) -> GeniaZipEntry:
        if not isinstance(value, GeniaZipEntry):
            raise TypeError(f"{name} expected a zip entry, received {_runtime_type_name(value)}")
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

    def find_fn(value: Any, needle: Any) -> Any:
        safe_value = _ensure_string(value, "find")
        safe_needle = _ensure_string(needle, "find")
        idx = safe_value.find(safe_needle)
        if idx < 0:
            return GeniaOptionNone(symbol("not_found"), GeniaMap().put("needle", safe_needle))
        return GeniaOptionSome(idx)

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
            raise TypeError(f"join expected a list as second argument, received {_runtime_type_name(xs)}")
        if not all(isinstance(item, str) for item in xs):
            raise TypeError("join expected a list of strings, received list")
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

    def parse_int_fn(*args: Any) -> Any:
        if len(args) not in (1, 2):
            raise TypeError(f"parse_int expected 1 or 2 args, got {len(args)}")
        text = _ensure_string(args[0], "parse_int")
        base = 10
        if len(args) == 2:
            base = args[1]
            if not isinstance(base, int) or isinstance(base, bool):
                raise TypeError("parse_int expected an integer base")
            if base < 2 or base > 36:
                raise ValueError("parse_int expected base in 2..36")

        stripped = text.strip()
        if stripped == "":
            return GeniaOptionNone(
                symbol("parse_failed"),
                GeniaMap()
                .put("source", "parse_int")
                .put("expected", "integer_string")
                .put("received", text)
                .put("base", base),
            )
        try:
            return GeniaOptionSome(int(stripped, base))
        except ValueError:
            return GeniaOptionNone(
                symbol("parse_failed"),
                GeniaMap()
                .put("source", "parse_int")
                .put("expected", "integer_string")
                .put("received", text)
                .put("base", base),
            )

    def input_fn(prompt: str = "") -> str:
        return input(prompt)

    argv_cache = list(cli_args or [])

    def stdin_iterable() -> Iterable[str]:
        if stdin_provider is not None:
            return stdin_provider()
        if stdin_data is not None:
            return iter(stdin_data)

        def host_stdin_lines() -> Iterable[str]:
            for line in sys.stdin:
                yield line

        return host_stdin_lines()

    stdin_source = GeniaStdinSource(stdin_iterable)
    setattr(stdin_source, "_genia_stdin_source", True)

    def argv_fn() -> list[str]:
        return list(argv_cache)

    def _ensure_flow(value: Any, name: str) -> GeniaFlow:
        if not isinstance(value, GeniaFlow):
            raise TypeError(f"{name} expected a flow, received {_runtime_type_name(value)}")
        return value

    def flow_predicate_fn(value: Any) -> bool:
        return isinstance(value, GeniaFlow)

    def _ensure_callable(value: Any, name: str) -> Callable[..., Any]:
        if not callable(value):
            raise TypeError(f"{name} expected a function, received {_runtime_type_name(value)}")
        return value

    def lines_fn(source: Any) -> GeniaFlow:
        if isinstance(source, GeniaFlow):
            upstream = _ensure_flow(source, "lines")

            def iterator() -> Iterable[Any]:
                for item in upstream.consume():
                    if not isinstance(item, str):
                        raise TypeError("lines expected string input items")
                    yield item

            return GeniaFlow(iterator, label="lines")

        if isinstance(source, GeniaStdinSource):
            return GeniaFlow(source.iter_lines, label="lines")

        if callable(source):
            raw_lines = source()
        else:
            raw_lines = source

        if not isinstance(raw_lines, list):
            raise TypeError("lines expected stdin source, flow, or list of strings")
        if not all(isinstance(item, str) for item in raw_lines):
            raise TypeError("lines expected a list of strings")

        def iterator() -> Iterable[str]:
            for item in raw_lines:
                yield item

        return GeniaFlow(iterator, label="lines")

    def map_flow_fn(fn_value: Any, source: Any) -> Any:
        mapper = _ensure_callable(fn_value, "map")
        if isinstance(source, GeniaFlow):
            upstream = source

            def iterator() -> Iterable[Any]:
                for item in upstream.consume():
                    yield mapper(item)

            return GeniaFlow(iterator, label="map")
        if not isinstance(source, list):
            raise TypeError("map expected a flow or list")
        return [mapper(item) for item in source]

    def filter_flow_fn(predicate_value: Any, source: Any) -> Any:
        predicate = _ensure_callable(predicate_value, "filter")
        if isinstance(source, GeniaFlow):
            upstream = source

            def iterator() -> Iterable[Any]:
                for item in upstream.consume():
                    if predicate(item):
                        yield item

            return GeniaFlow(iterator, label="filter")
        if not isinstance(source, list):
            raise TypeError("filter expected a flow or list")
        return [item for item in source if predicate(item)]

    def take_fn(n: Any, source: Any) -> GeniaFlow:
        if not isinstance(n, int) or isinstance(n, bool):
            raise TypeError("take expected an integer count as first argument")
        upstream = _ensure_flow(source, "take")

        def iterator() -> Iterable[Any]:
            if n <= 0:
                return
            remaining = n
            items = iter(upstream.consume())
            while remaining > 0:
                try:
                    item = next(items)
                except StopIteration:
                    return
                yield item
                remaining -= 1

        return GeniaFlow(iterator, label="take")

    def head_fn(*args: Any) -> GeniaFlow:
        if len(args) == 1:
            return take_fn(1, args[0])
        if len(args) == 2:
            return take_fn(args[0], args[1])
        raise TypeError(f"head expected 1 or 2 args, got {len(args)}")

    def _ensure_rule_values(rule_values: list[Any]) -> list[Any]:
        for index, rule_value in enumerate(rule_values, start=1):
            if not callable(rule_value):
                raise TypeError(f"rules expected rule {index} to be a function")
        return rule_values

    def rules_prepare_fn(rule_values: Any) -> list[Any]:
        if not isinstance(rule_values, list):
            raise TypeError("rules expected an internal list of rule functions")
        return list(_ensure_rule_values(list(rule_values)))

    def rules_error_fn(rule_index: Any, detail: Any) -> Any:
        if not isinstance(rule_index, int) or isinstance(rule_index, bool):
            raise TypeError("_rules_error expected an integer rule index")
        raise RuntimeError(f"invalid-rules-result: rule {rule_index} {_ensure_string(detail, '_rules_error')}")

    def flow_debug_fn(value: Any) -> str:
        return format_debug(value)

    def rules_kernel_fn(step_value: Any, source: Any) -> GeniaFlow:
        step = _ensure_callable(step_value, "rules")
        upstream = _ensure_flow(source, "rules")

        def iterator() -> Iterable[Any]:
            current_ctx: Any = GeniaMap()
            for item in upstream.consume():
                result = _invoke_from_builtin(step, [item, current_ctx])
                if not isinstance(result, GeniaMap):
                    raise RuntimeError("_rules_kernel expected a map result")

                emitted = result.get("emit")
                if not isinstance(emitted, list):
                    raise RuntimeError("_rules_kernel expected emit to be a list")

                current_ctx = result.get("ctx")

                for value in emitted:
                    yield value

        return GeniaFlow(iterator, label="rules")

    def each_fn(fn_value: Any, source: Any) -> GeniaFlow:
        effect = _ensure_callable(fn_value, "each")
        upstream = _ensure_flow(source, "each")

        def iterator() -> Iterable[Any]:
            for item in upstream.consume():
                effect(item)
                yield item

        return GeniaFlow(iterator, label="each")

    def collect_fn(source: Any) -> list[Any]:
        flow = _ensure_flow(source, "collect")
        return list(flow.consume())

    def run_fn(source: Any) -> None:
        flow = _ensure_flow(source, "run")
        for _ in flow.consume():
            pass
        return None

    def _emit_help(text: str) -> None:
        stdout_sink.write_text(text + "\n")

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

    def _describe_runtime_name(name: str, value: Any) -> str:
        kind = "host-backed runtime function" if callable(value) else "host-backed runtime value"
        return "\n".join(
            [
                name,
                "",
                f"{name} is a {kind} in this phase.",
                "Detailed docstrings are attached to public Genia/prelude functions instead of raw host bridge names.",
                'Use `help()` for the surface overview and `help("name")` for documented public helpers such as `get`, `map_put`, `ref_update`, `spawn`, `write`, `parse_int`, `match_branches`, `eval`, and `cell_send`.',
            ]
        )

    def _discover_public_family_names(paths: tuple[str, ...], preferred: tuple[str, ...]) -> list[str]:
        discovered: list[str] = []
        seen: set[str] = set()
        for (name, _), path in env.root().autoloads.items():
            if path not in paths or name in seen:
                continue
            seen.add(name)
            discovered.append(name)

        if not discovered:
            return []

        ordered = [name for name in preferred if name in seen]
        extras = [name for name in discovered if name not in ordered]
        return [*ordered, *extras]

    def _help_public_families() -> list[tuple[str, list[str]]]:
        specs = [
            ("CLI", ("std/prelude/cli.genia",), ("cli_parse", "cli_flag?", "cli_option", "cli_option_or")),
            ("Flow", ("std/prelude/flow.genia",), ("lines", "rules", "each", "collect", "run")),
            (
                "Lists / fns / math",
                ("std/prelude/list.genia", "std/prelude/fn.genia", "std/prelude/math.genia"),
                ("list", "first", "nth", "map", "filter", "reduce", "apply", "compose", "sum"),
            ),
            (
                "Option / string",
                ("std/prelude/option.genia", "std/prelude/string.genia"),
                ("some", "get", "unwrap_or", "absence_reason", "parse_int", "split", "trim", "join", "map_some", "then_get"),
            ),
            (
                "Map / ref / process / sinks",
                ("std/prelude/map.genia", "std/prelude/ref.genia", "std/prelude/process.genia", "std/prelude/io.genia"),
                ("map_put", "map_has?", "ref_update", "spawn", "send", "write", "writeln", "flush"),
            ),
            (
                "Streams / cells / rule helpers",
                ("std/prelude/stream.genia", "std/prelude/cell.genia", "std/prelude/fn.genia"),
                ("stream_cons", "stream_map", "stream_take", "cell", "cell_send", "cell_error", "rule_emit", "rule_step"),
            ),
            (
                "Syntax / eval",
                ("std/prelude/syntax.genia", "std/prelude/eval.genia"),
                ("match_branches", "branch_guard", "empty_env", "eval"),
            ),
            ("AWK-style helpers", ("std/prelude/awk.genia",), ("fields", "awkify", "awk_filter", "awk_map", "awk_count")),
        ]
        families: list[tuple[str, list[str]]] = []
        for label, paths, preferred in specs:
            names = _discover_public_family_names(paths, preferred)
            if names:
                families.append((label, names))
        return families

    def _describe_help_overview() -> str:
        lines = [
            "Genia prototype help",
            "--------------------",
            "Examples:",
            "  1 + 2 * 3",
            '  person = { name: "Maya" }',
            '  unwrap_or("unknown", person |> get("name"))',
            "  [1, 2, 3] |> map((x) -> x + 1)",
            '  unwrap_or(0, "42" |> parse_int)',
            "  quote([a, b, c])",
            '  help("get")',
            '  help("map_put")',
            '  help("spawn")',
            '  help("eval")',
            "",
            "Commands:",
            "  :quit   exit",
            "  :env    show defined names",
            "  :help   show this help",
            "  help(name)   show docs for a public helper or a note for a runtime name",
            "",
            "Public stdlib model:",
            "  Most user-facing helpers live in autoloaded prelude modules.",
            '  `help("name")` autoloads a documented public helper and renders its Markdown docstring.',
            "  Public family samples below are derived from registered prelude autoloads.",
            '  Example: `unwrap_or("?", record |> get("user") |> get("name"))` is preferred over helper-heavy safe-chaining and legacy lookup forms.',
            "",
            "Public prelude families discovered from autoload registrations:",
        ]
        for label, names in _help_public_families():
            lines.append(f"  {label}:")
            lines.append(f"    {', '.join(names)}")
        lines.extend(
            [
                "",
                "Intentional host bridge:",
                "  Raw host-backed names stay small and capability-oriented.",
                "  `argv()` and values such as `stdin`, `stdout`, `stderr`, `print`, `log`, `input`, `none`, `force`,",
                "  pair helpers, simulation primitives, and utf8/json/zip bridges remain host-backed in this phase.",
                '  `help("print")` and similar raw bridge names show a small generic note instead of a second host-side docs registry.',
            ]
        )
        return "\n".join(lines)

    def help_fn(*args: Any) -> None:
        if len(args) > 1:
            raise TypeError(f"help expected 0 or 1 args, got {len(args)}")
        if len(args) == 1:
            target = args[0]
            original_name: str | None = target if isinstance(target, str) else None
            if isinstance(target, str):
                try:
                    target = env.get(target)
                except NameError:
                    if env.try_autoload(target, 0):
                        target = env.get(target)
                    else:
                        raise
            if isinstance(target, GeniaFunctionGroup):
                _emit_help(_describe_function_group(target))
                return
            if isinstance(target, GeniaFunction):
                singleton = GeniaFunctionGroup(target.name, functions={target.arity: target}, docstring=target.docstring)
                _emit_help(_describe_function_group(singleton))
                return
            if original_name is not None:
                _emit_help(_describe_runtime_name(original_name, target))
                return
            raise TypeError("help expected a function name or named function")

        _emit_help(_describe_help_overview())

    def ref_fn(*args: Any) -> GeniaRef:
        if len(args) == 0:
            return GeniaRef()
        if len(args) == 1:
            return GeniaRef(args[0])
        raise TypeError(f"ref expected 0 or 1 args, got {len(args)}")

    def force_fn(value: Any) -> Any:
        if isinstance(value, GeniaPromise):
            return value.force()
        return value

    def syntax_self_evaluating_fn(expr: Any) -> bool:
        if expr is None or isinstance(expr, GeniaOptionNone):
            return True
        if isinstance(expr, bool):
            return True
        if isinstance(expr, (int, float)) and not isinstance(expr, bool):
            return True
        if isinstance(expr, str):
            return True
        return False

    def syntax_symbol_expr_fn(expr: Any) -> bool:
        return isinstance(expr, GeniaSymbol)

    def syntax_error_fn(message: Any) -> Any:
        raise TypeError(_ensure_string(message, "_syntax_error"))

    def cons_fn(head: Any, tail: Any) -> GeniaPair:
        return GeniaPair(head, tail)

    def car_fn(value: Any) -> Any:
        if not isinstance(value, GeniaPair):
            raise TypeError("car expected a pair")
        return value.head

    def cdr_fn(value: Any) -> Any:
        if not isinstance(value, GeniaPair):
            raise TypeError("cdr expected a pair")
        return value.tail

    def pair_fn(value: Any) -> bool:
        return isinstance(value, GeniaPair)

    def null_fn(value: Any) -> bool:
        return value is None

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

    def _ensure_cell(cell_value: Any, name: str) -> GeniaCell:
        if not isinstance(cell_value, GeniaCell):
            raise TypeError(f"{name} expected a cell as first argument")
        return cell_value

    def cell_new_fn(initial: Any) -> GeniaCell:
        return GeniaCell(GeniaRef(initial))

    def cell_with_state_fn(state_ref: Any) -> GeniaCell:
        if not isinstance(state_ref, GeniaRef):
            raise TypeError("cell_with_state expected a ref")
        return GeniaCell(state_ref)

    def cell_send_fn(cell_value: Any, update_fn: Any) -> None:
        cell = _ensure_cell(cell_value, "cell_send")
        if not callable(update_fn):
            raise TypeError("cell_send expected a function as second argument")
        if _stage_cell_action("cell_send", cell, update_fn):
            return None
        cell.send(update_fn)
        return None

    def cell_get_fn(cell_value: Any) -> Any:
        cell = _ensure_cell(cell_value, "cell_get")
        return cell.get()

    def cell_failed_fn(cell_value: Any) -> bool:
        cell = _ensure_cell(cell_value, "cell_failed?")
        return cell.failed()

    def cell_error_fn(cell_value: Any) -> Any:
        cell = _ensure_cell(cell_value, "cell_error")
        return cell.error_option()

    def restart_cell_fn(cell_value: Any, new_state: Any) -> Any:
        cell = _ensure_cell(cell_value, "restart_cell")
        return cell.restart(new_state)

    def cell_status_fn(cell_value: Any) -> str:
        cell = _ensure_cell(cell_value, "cell_status")
        return cell.status()

    def cell_alive_fn(cell_value: Any) -> bool:
        cell = _ensure_cell(cell_value, "cell_alive?")
        return cell.is_alive()

    def spawn_fn(handler: Any) -> GeniaProcess:
        if not callable(handler):
            raise TypeError("spawn expected a function")
        return GeniaProcess(handler)

    def send_fn(process: Any, message: Any) -> None:
        if not isinstance(process, GeniaProcess):
            raise TypeError("send expected a process as first argument")
        if _stage_cell_action("process_send", process, message):
            return None
        process.send(message)
        return None

    def process_alive_fn(process: Any) -> bool:
        if not isinstance(process, GeniaProcess):
            raise TypeError("process_alive? expected a process")
        return process.is_alive()

    def _ensure_map(value: Any, name: str) -> GeniaMap:
        if not isinstance(value, GeniaMap):
            raise TypeError(f"{name} expected a map as first argument, received {_runtime_type_name(value)}")
        return value

    def _ensure_list_of_strings(value: Any, name: str) -> list[str]:
        if not isinstance(value, list):
            raise TypeError(f"{name} expected a list of strings, received {_runtime_type_name(value)}")
        if not all(isinstance(item, str) for item in value):
            raise TypeError(f"{name} expected a list of strings, received list")
        return value

    def _map_from_string_names(names: list[str]) -> GeniaMap:
        result = GeniaMap()
        for name in names:
            result = result.put(name, True)
        return result

    def cli_spec_fn(spec: Any) -> GeniaMap:
        if spec is None:
            flags = GeniaMap()
            options = GeniaMap()
            aliases = GeniaMap()
        else:
            if not isinstance(spec, GeniaMap):
                raise TypeError("cli_parse expected spec to be a map")

            flags_raw = spec.get("flags")
            options_raw = spec.get("options")
            aliases_raw = spec.get("aliases")

            flags_list = _ensure_list_of_strings(flags_raw, "cli_parse spec.flags") if flags_raw is not None else []
            options_list = _ensure_list_of_strings(options_raw, "cli_parse spec.options") if options_raw is not None else []
            flags = _map_from_string_names(flags_list)
            options = _map_from_string_names(options_list)
            aliases = GeniaMap()

            if aliases_raw is not None:
                if not isinstance(aliases_raw, GeniaMap):
                    raise TypeError("cli_parse spec.aliases expected a map")
                for _, (raw_key, raw_value) in aliases_raw._entries.items():
                    if not isinstance(raw_key, str) or not isinstance(raw_value, str):
                        raise TypeError("cli_parse spec.aliases expected string keys and values")
                    aliases = aliases.put(raw_key, raw_value)

        return GeniaMap().put("flags", flags).put("options", options).put("aliases", aliases)

    def cli_chars_fn(value: Any) -> list[str]:
        if not isinstance(value, str):
            raise TypeError("cli_parse expected a list of strings")
        return list(value)

    def cli_type_error_fn(message: Any) -> Any:
        raise TypeError(_ensure_string(message, "cli_parse"))

    def cli_value_error_fn(message: Any) -> Any:
        raise ValueError(_ensure_string(message, "cli_parse"))

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

    def some_fn(value: Any) -> GeniaOptionSome:
        return GeniaOptionSome(value)

    def is_some_fn(value: Any) -> bool:
        return isinstance(value, GeniaOptionSome)

    def is_none_fn(value: Any) -> bool:
        return isinstance(value, GeniaOptionNone)

    def unwrap_or_fn(default: Any, opt: Any) -> Any:
        if isinstance(opt, GeniaOptionSome):
            return opt.value
        if isinstance(opt, GeniaOptionNone):
            return default
        raise TypeError("unwrap_or expected an option value")

    def some_predicate_fn(value: Any) -> bool:
        return is_some_fn(value)

    def none_predicate_fn(value: Any) -> bool:
        return is_none_fn(value)

    def _resolve_option_and_other(first: Any, second: Any) -> tuple[Any, Any]:
        if isinstance(first, (GeniaOptionSome, GeniaOptionNone)):
            return first, second
        if isinstance(second, (GeniaOptionSome, GeniaOptionNone)):
            return second, first
        return first, second

    def or_else_fn(first: Any, second: Any) -> Any:
        opt, fallback = _resolve_option_and_other(first, second)
        if isinstance(opt, GeniaOptionSome):
            return opt.value
        if isinstance(opt, GeniaOptionNone):
            return fallback
        raise TypeError("or_else expected an option value")

    def absence_reason_fn(value: Any) -> Any:
        if not isinstance(value, GeniaOptionNone):
            raise TypeError("absence_reason expected a none value")
        if value.reason is None:
            return OPTION_NONE
        return GeniaOptionSome(value.reason)

    def absence_context_fn(value: Any) -> Any:
        if not isinstance(value, GeniaOptionNone):
            raise TypeError("absence_context expected a none value")
        if value.context is None:
            return OPTION_NONE
        return GeniaOptionSome(value.context)

    def _invoke_from_builtin(proc: Any, args: list[Any]) -> Any:
        return Evaluator(env, env.debug_hooks, env.debug_mode).invoke_callable(
            proc,
            args,
            tail_position=False,
            callee_node=None,
        )

    def _get_option_impl(name: str, key: Any, target: Any) -> Any:
        if isinstance(target, GeniaOptionNone):
            return target
        if isinstance(target, GeniaOptionSome):
            return _get_option_impl(name, key, target.value)
        if isinstance(target, GeniaMap):
            if target.has(key):
                return GeniaOptionSome(target.get(key))
            context = GeniaMap().put("key", key)
            return GeniaOptionNone(symbol("missing_key"), context)
        raise TypeError(f"{name} expected a map, some(map), or none target; received {_runtime_type_name(target)}")

    def get_fn(key: Any, target: Any) -> Any:
        return _get_option_impl("get", key, target)

    def get_option_fn(key: Any, target: Any) -> Any:
        return _get_option_impl("get?", key, target)

    def map_some_fn(proc: Any, opt: Any) -> Any:
        if isinstance(opt, GeniaOptionSome):
            return GeniaOptionSome(_invoke_from_builtin(proc, [opt.value]))
        if isinstance(opt, GeniaOptionNone):
            return opt
        raise TypeError("map_some expected an option value")

    def flat_map_some_fn(proc: Any, opt: Any) -> Any:
        if isinstance(opt, GeniaOptionSome):
            result = _invoke_from_builtin(proc, [opt.value])
            if isinstance(result, (GeniaOptionSome, GeniaOptionNone)):
                return result
            raise TypeError("flat_map_some expected function to return an option value")
        if isinstance(opt, GeniaOptionNone):
            return opt
        raise TypeError("flat_map_some expected an option value")

    def _looks_like_get_target(value: Any) -> bool:
        return isinstance(value, (GeniaOptionSome, GeniaOptionNone, GeniaMap))

    def _looks_like_list_target(value: Any) -> bool:
        return isinstance(value, (GeniaOptionSome, GeniaOptionNone, list))

    def _looks_like_find_target(value: Any) -> bool:
        return isinstance(value, (GeniaOptionSome, GeniaOptionNone, str))

    def _resolve_chain_binary_args(
        name: str,
        first: Any,
        second: Any,
        target_predicate: Callable[[Any], bool],
    ) -> tuple[Any, Any]:
        first_is_target = target_predicate(first)
        second_is_target = target_predicate(second)
        if first_is_target and not second_is_target:
            return first, second
        if second_is_target and not first_is_target:
            return second, first
        return second, first

    def then_get_fn(first: Any, second: Any) -> Any:
        target, key = _resolve_chain_binary_args("then_get", first, second, _looks_like_get_target)
        return _get_option_impl("then_get", key, target)

    def _first_option_impl(target: Any) -> Any:
        if isinstance(target, GeniaOptionNone):
            return target
        if isinstance(target, GeniaOptionSome):
            return _first_option_impl(target.value)
        if isinstance(target, list):
            if len(target) == 0:
                return GeniaOptionNone(symbol("empty_list"))
            return GeniaOptionSome(target[0])
        raise TypeError(f"then_first expected a list, some(list), or none target; received {_runtime_type_name(target)}")

    def then_first_fn(target: Any) -> Any:
        return _first_option_impl(target)

    def _nth_option_impl(index: Any, target: Any) -> Any:
        if not isinstance(index, int) or isinstance(index, bool):
            raise TypeError("then_nth expected an integer index")
        if isinstance(target, GeniaOptionNone):
            return target
        if isinstance(target, GeniaOptionSome):
            return _nth_option_impl(index, target.value)
        if isinstance(target, list):
            size = len(target)
            if index < 0 or index >= size:
                context = GeniaMap().put("index", index).put("length", size)
                return GeniaOptionNone(symbol("index_out_of_bounds"), context)
            return GeniaOptionSome(target[index])
        raise TypeError(f"then_nth expected a list, some(list), or none target; received {_runtime_type_name(target)}")

    def then_nth_fn(first: Any, second: Any) -> Any:
        target, index = _resolve_chain_binary_args("then_nth", first, second, _looks_like_list_target)
        return _nth_option_impl(index, target)

    def _find_option_impl(needle: Any, target: Any) -> Any:
        safe_needle = _ensure_string(needle, "then_find")
        if isinstance(target, GeniaOptionNone):
            return target
        if isinstance(target, GeniaOptionSome):
            return _find_option_impl(safe_needle, target.value)
        if isinstance(target, str):
            idx = target.find(safe_needle)
            if idx < 0:
                return GeniaOptionNone(symbol("not_found"), GeniaMap().put("needle", safe_needle))
            return GeniaOptionSome(idx)
        raise TypeError(f"then_find expected a string, some(string), or none target; received {_runtime_type_name(target)}")

    def then_find_fn(first: Any, second: Any) -> Any:
        if isinstance(first, (GeniaOptionSome, GeniaOptionNone)):
            target, needle = first, second
        elif isinstance(second, (GeniaOptionSome, GeniaOptionNone)):
            target, needle = second, first
        elif isinstance(second, str):
            target, needle = second, first
        else:
            target, needle = first, second
        return _find_option_impl(needle, target)

    def or_else_with_fn(first: Any, second: Any) -> Any:
        opt, thunk = _resolve_option_and_other(first, second)
        if isinstance(opt, GeniaOptionSome):
            return opt.value
        if isinstance(opt, GeniaOptionNone):
            return _invoke_from_builtin(thunk, [])
        raise TypeError("or_else_with expected an option value")

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

    env.set("stdout", stdout_sink)
    env.set("stderr", stderr_sink)
    env.set("_write", write_fn)
    env.set("_writeln", writeln_fn)
    env.set("_flush", flush_fn)
    env.set("log", log)
    env.set("print", print_fn)
    env.set("input", input_fn)
    env.set("stdin", stdin_source)
    env.set("_flow?", flow_predicate_fn)
    env.set("_lines", lines_fn)
    env.set("_each", each_fn)
    env.set("_rules_prepare", rules_prepare_fn)
    env.set("_rules_kernel", rules_kernel_fn)
    env.set("_rules_error", rules_error_fn)
    env.set("_flow_debug", flow_debug_fn)
    env.set("_run", run_fn)
    env.set("_collect", collect_fn)
    env.set("argv", argv_fn)
    env.set("help", help_fn)
    env.set("pi", math.pi)
    env.set("e", math.e)
    env.set("true", True)
    env.set("false", False)
    env.set("nil", None)
    env.set("none", OPTION_NONE)
    env.set("_some", some_fn)
    env.set("_none?", none_predicate_fn)
    env.set("_some?", some_predicate_fn)
    env.set("_get", get_fn)
    env.set("_get?", get_option_fn)
    env.set("_map_some", map_some_fn)
    env.set("_flat_map_some", flat_map_some_fn)
    env.set("_then_get", then_get_fn)
    env.set("_then_first", then_first_fn)
    env.set("_then_nth", then_nth_fn)
    env.set("_then_find", then_find_fn)
    env.set("_or_else", or_else_fn)
    env.set("_or_else_with", or_else_with_fn)
    env.set("_unwrap_or", unwrap_or_fn)
    env.set("_absence_reason", absence_reason_fn)
    env.set("_absence_context", absence_context_fn)
    env.set("_is_some?", is_some_fn)
    env.set("_is_none?", is_none_fn)
    env.set("force", force_fn)
    env.set("_meta_empty_env", meta_empty_env_fn)
    env.set("_meta_lookup", meta_lookup_fn)
    env.set("_meta_define", meta_define_fn)
    env.set("_meta_set", meta_set_fn)
    env.set("_meta_extend", meta_extend_fn)
    env.set("_meta_host_apply", meta_host_apply_fn)
    env.set("_meta_eval_error", meta_eval_error_fn)
    env.set("_meta_match_pattern_env", meta_match_pattern_env_fn)
    env.set("_meta_match_error", meta_match_error_fn)
    env.set("_syntax_error", syntax_error_fn)
    env.set("_syntax_self_evaluating", syntax_self_evaluating_fn)
    env.set("_syntax_symbol_expr", syntax_symbol_expr_fn)
    env.set("cons", cons_fn)
    env.set("car", car_fn)
    env.set("cdr", cdr_fn)
    env.set("pair?", pair_fn)
    env.set("null?", null_fn)
    env.set("_ref", ref_fn)
    env.set("_ref_get", ref_get_fn)
    env.set("_ref_set", ref_set_fn)
    env.set("_ref_is_set", ref_is_set_fn)
    env.set("_ref_update", ref_update_fn)
    env.set("_cell_new", cell_new_fn)
    env.set("_cell_with_state", cell_with_state_fn)
    env.set("_cell_send", cell_send_fn)
    env.set("_cell_get", cell_get_fn)
    env.set("_cell_failed?", cell_failed_fn)
    env.set("_cell_error", cell_error_fn)
    env.set("_restart_cell", restart_cell_fn)
    env.set("_cell_status", cell_status_fn)
    env.set("_cell_alive?", cell_alive_fn)
    env.set("_spawn", spawn_fn)
    env.set("_send", send_fn)
    env.set("_process_alive?", process_alive_fn)
    env.set("_map_new", map_new_fn)
    env.set("_map_get", map_get_fn)
    env.set("_map_put", map_put_fn)
    env.set("_map_has?", map_has_fn)
    env.set("_map_remove", map_remove_fn)
    env.set("_map_count", map_count_fn)
    env.set("rand", rand_fn)
    env.set("rand_int", rand_int_fn)
    env.set("sleep", sleep_fn)
    env.set("_byte_length", byte_length_fn)
    env.set("_is_empty", is_empty_fn)
    env.set("_concat", concat_fn)
    env.set("_contains", contains_fn)
    env.set("_starts_with", starts_with_fn)
    env.set("_ends_with", ends_with_fn)
    env.set("_find", find_fn)
    env.set("_split", split_fn)
    env.set("_split_whitespace", split_whitespace_fn)
    env.set("_join", join_fn)
    env.set("_trim", trim_fn)
    env.set("_trim_start", trim_start_fn)
    env.set("_trim_end", trim_end_fn)
    env.set("_lower", lower_fn)
    env.set("_upper", upper_fn)
    env.set("_parse_int", parse_int_fn)
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
    env.set("_cli_spec", cli_spec_fn)
    env.set("_cli_chars", cli_chars_fn)
    env.set("_cli_type_error", cli_type_error_fn)
    env.set("_cli_value_error", cli_value_error_fn)
    env.set("_cli_flag?", cli_flag_fn)
    env.set("_cli_option", cli_option_fn)
    env.set("_cli_option_or", cli_option_or_fn)

    env.register_autoload("cli_parse", 1, "std/prelude/cli.genia")
    env.register_autoload("cli_parse", 2, "std/prelude/cli.genia")
    env.register_autoload("cli_flag?", 2, "std/prelude/cli.genia")
    env.register_autoload("cli_option", 2, "std/prelude/cli.genia")
    env.register_autoload("cli_option_or", 3, "std/prelude/cli.genia")
    env.register_autoload("lines", 1, "std/prelude/flow.genia")
    env.register_autoload("rules", 0, "std/prelude/flow.genia")
    env.register_autoload("each", 2, "std/prelude/flow.genia")
    env.register_autoload("collect", 1, "std/prelude/flow.genia")
    env.register_autoload("run", 1, "std/prelude/flow.genia")
    env.register_autoload("list", 0, "std/prelude/list.genia")
    env.register_autoload("first", 1, "std/prelude/list.genia")
    env.register_autoload("first_opt", 1, "std/prelude/list.genia")
    env.register_autoload("last", 1, "std/prelude/list.genia")
    env.register_autoload("find_opt", 2, "std/prelude/list.genia")
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
    env.register_autoload("nth_opt", 2, "std/prelude/list.genia")
    env.register_autoload("take", 2, "std/prelude/list.genia")
    env.register_autoload("head", 1, "std/prelude/list.genia")
    env.register_autoload("head", 2, "std/prelude/list.genia")
    env.register_autoload("drop", 2, "std/prelude/list.genia")
    env.register_autoload("range", 1, "std/prelude/list.genia")
    env.register_autoload("range", 2, "std/prelude/list.genia")
    env.register_autoload("range", 3, "std/prelude/list.genia")
    env.register_autoload("apply", 2, "std/prelude/fn.genia")
    env.register_autoload("compose", 1, "std/prelude/fn.genia")
    env.register_autoload("rule_skip", 0, "std/prelude/fn.genia")
    env.register_autoload("rule_emit", 1, "std/prelude/fn.genia")
    env.register_autoload("rule_emit_many", 1, "std/prelude/fn.genia")
    env.register_autoload("rule_set", 1, "std/prelude/fn.genia")
    env.register_autoload("rule_ctx", 1, "std/prelude/fn.genia")
    env.register_autoload("rule_halt", 0, "std/prelude/fn.genia")
    env.register_autoload("rule_step", 3, "std/prelude/fn.genia")
    env.register_autoload("map_new", 0, "std/prelude/map.genia")
    env.register_autoload("map_get", 2, "std/prelude/map.genia")
    env.register_autoload("map_put", 3, "std/prelude/map.genia")
    env.register_autoload("map_has?", 2, "std/prelude/map.genia")
    env.register_autoload("map_remove", 2, "std/prelude/map.genia")
    env.register_autoload("map_count", 1, "std/prelude/map.genia")
    env.register_autoload("ref", 0, "std/prelude/ref.genia")
    env.register_autoload("ref", 1, "std/prelude/ref.genia")
    env.register_autoload("ref_get", 1, "std/prelude/ref.genia")
    env.register_autoload("ref_set", 2, "std/prelude/ref.genia")
    env.register_autoload("ref_is_set", 1, "std/prelude/ref.genia")
    env.register_autoload("ref_update", 2, "std/prelude/ref.genia")
    env.register_autoload("spawn", 1, "std/prelude/process.genia")
    env.register_autoload("send", 2, "std/prelude/process.genia")
    env.register_autoload("process_alive?", 1, "std/prelude/process.genia")
    env.register_autoload("write", 2, "std/prelude/io.genia")
    env.register_autoload("writeln", 2, "std/prelude/io.genia")
    env.register_autoload("flush", 1, "std/prelude/io.genia")
    env.register_autoload("some", 1, "std/prelude/option.genia")
    env.register_autoload("none?", 1, "std/prelude/option.genia")
    env.register_autoload("some?", 1, "std/prelude/option.genia")
    env.register_autoload("get", 2, "std/prelude/option.genia")
    env.register_autoload("get?", 2, "std/prelude/option.genia")
    env.register_autoload("map_some", 2, "std/prelude/option.genia")
    env.register_autoload("flat_map_some", 2, "std/prelude/option.genia")
    env.register_autoload("then_get", 2, "std/prelude/option.genia")
    env.register_autoload("then_first", 1, "std/prelude/option.genia")
    env.register_autoload("then_nth", 2, "std/prelude/option.genia")
    env.register_autoload("then_find", 2, "std/prelude/option.genia")
    env.register_autoload("or_else", 2, "std/prelude/option.genia")
    env.register_autoload("or_else_with", 2, "std/prelude/option.genia")
    env.register_autoload("unwrap_or", 2, "std/prelude/option.genia")
    env.register_autoload("absence_reason", 1, "std/prelude/option.genia")
    env.register_autoload("absence_context", 1, "std/prelude/option.genia")
    env.register_autoload("is_some?", 1, "std/prelude/option.genia")
    env.register_autoload("is_none?", 1, "std/prelude/option.genia")
    env.register_autoload("byte_length", 1, "std/prelude/string.genia")
    env.register_autoload("is_empty", 1, "std/prelude/string.genia")
    env.register_autoload("concat", 2, "std/prelude/string.genia")
    env.register_autoload("contains", 2, "std/prelude/string.genia")
    env.register_autoload("starts_with", 2, "std/prelude/string.genia")
    env.register_autoload("ends_with", 2, "std/prelude/string.genia")
    env.register_autoload("find", 2, "std/prelude/string.genia")
    env.register_autoload("split", 2, "std/prelude/string.genia")
    env.register_autoload("split_whitespace", 1, "std/prelude/string.genia")
    env.register_autoload("join", 2, "std/prelude/string.genia")
    env.register_autoload("trim", 1, "std/prelude/string.genia")
    env.register_autoload("trim_start", 1, "std/prelude/string.genia")
    env.register_autoload("trim_end", 1, "std/prelude/string.genia")
    env.register_autoload("lower", 1, "std/prelude/string.genia")
    env.register_autoload("upper", 1, "std/prelude/string.genia")
    env.register_autoload("parse_int", 1, "std/prelude/string.genia")
    env.register_autoload("parse_int", 2, "std/prelude/string.genia")
    env.register_autoload("stream_cons", 2, "std/prelude/stream.genia")
    env.register_autoload("stream_head", 1, "std/prelude/stream.genia")
    env.register_autoload("stream_tail", 1, "std/prelude/stream.genia")
    env.register_autoload("stream_map", 2, "std/prelude/stream.genia")
    env.register_autoload("stream_take", 2, "std/prelude/stream.genia")
    env.register_autoload("stream_filter", 2, "std/prelude/stream.genia")
    env.register_autoload("self_evaluating?", 1, "std/prelude/syntax.genia")
    env.register_autoload("symbol_expr?", 1, "std/prelude/syntax.genia")
    env.register_autoload("tagged_list?", 2, "std/prelude/syntax.genia")
    env.register_autoload("quoted_expr?", 1, "std/prelude/syntax.genia")
    env.register_autoload("quasiquoted_expr?", 1, "std/prelude/syntax.genia")
    env.register_autoload("assignment_expr?", 1, "std/prelude/syntax.genia")
    env.register_autoload("lambda_expr?", 1, "std/prelude/syntax.genia")
    env.register_autoload("application_expr?", 1, "std/prelude/syntax.genia")
    env.register_autoload("block_expr?", 1, "std/prelude/syntax.genia")
    env.register_autoload("match_expr?", 1, "std/prelude/syntax.genia")
    env.register_autoload("text_of_quotation", 1, "std/prelude/syntax.genia")
    env.register_autoload("assignment_name", 1, "std/prelude/syntax.genia")
    env.register_autoload("assignment_value", 1, "std/prelude/syntax.genia")
    env.register_autoload("lambda_params", 1, "std/prelude/syntax.genia")
    env.register_autoload("lambda_body", 1, "std/prelude/syntax.genia")
    env.register_autoload("operator", 1, "std/prelude/syntax.genia")
    env.register_autoload("operands", 1, "std/prelude/syntax.genia")
    env.register_autoload("block_expressions", 1, "std/prelude/syntax.genia")
    env.register_autoload("match_branches", 1, "std/prelude/syntax.genia")
    env.register_autoload("branch_pattern", 1, "std/prelude/syntax.genia")
    env.register_autoload("branch_has_guard?", 1, "std/prelude/syntax.genia")
    env.register_autoload("branch_guard", 1, "std/prelude/syntax.genia")
    env.register_autoload("branch_body", 1, "std/prelude/syntax.genia")
    env.register_autoload("empty_env", 0, "std/prelude/eval.genia")
    env.register_autoload("lookup", 2, "std/prelude/eval.genia")
    env.register_autoload("define", 3, "std/prelude/eval.genia")
    env.register_autoload("set", 3, "std/prelude/eval.genia")
    env.register_autoload("extend", 3, "std/prelude/eval.genia")
    env.register_autoload("eval", 2, "std/prelude/eval.genia")

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
    env.register_autoload("cell", 1, "std/prelude/cell.genia")
    env.register_autoload("cell_with_state", 1, "std/prelude/cell.genia")
    env.register_autoload("cell_send", 2, "std/prelude/cell.genia")
    env.register_autoload("cell_get", 1, "std/prelude/cell.genia")
    env.register_autoload("cell_state", 1, "std/prelude/cell.genia")
    env.register_autoload("cell_failed?", 1, "std/prelude/cell.genia")
    env.register_autoload("cell_error", 1, "std/prelude/cell.genia")
    env.register_autoload("restart_cell", 2, "std/prelude/cell.genia")
    env.register_autoload("cell_status", 1, "std/prelude/cell.genia")
    env.register_autoload("cell_alive?", 1, "std/prelude/cell.genia")
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


def _validate_pipe_mode_expr(source: str) -> None:
    tokens = lex(source)
    parser = Parser(tokens, source=source, filename="<pipe>")
    ast_nodes = parser.parse_program()
    if len(ast_nodes) != 1 or not isinstance(ast_nodes[0], ExprStmt):
        raise ValueError("-p/--pipe expects a single stage expression")

    for token in tokens:
        if token.kind != "IDENT":
            continue
        if token.text == "stdin":
            raise ValueError("-p/--pipe stage expression must omit stdin; it is added automatically")
        if token.text == "run":
            raise ValueError("-p/--pipe stage expression must omit run; it is added automatically")


def _wrap_pipe_mode_expr(source: str) -> str:
    _validate_pipe_mode_expr(source)
    return f"stdin |> lines |> {source} |> run"


def _emit_result(env: Env, value: Any) -> None:
    sink = env.get("stdout")
    if not isinstance(sink, GeniaOutputSink):
        raise RuntimeError("stdout sink is not configured")
    sink.write_text(format_debug(value) + "\n")


def _emit_error(env: Env, message: str) -> None:
    sink = env.values.get("stderr")
    if isinstance(sink, GeniaOutputSink):
        sink.write_text(message + "\n")
    else:
        try:
            sys.stderr.write(message + "\n")
            sys.stderr.flush()
        except BrokenPipeError:
            return


def repl() -> None:
    env = make_global_env([])
    try:
        env.get("_writeln")(env.get("stdout"), "Genia prototype REPL. Type :help for examples, :quit to exit.")
    except GeniaQuietBrokenPipe:
        return
    buf = ""
    while True:
        try:
            prompt = "... " if buf else ">>> "
            line = input(prompt)
        except EOFError:
            try:
                env.get("_writeln")(env.get("stdout"), "")
            except GeniaQuietBrokenPipe:
                return
            break
        if not buf and line.strip() == ":quit":
            break
        if not buf and line.strip() == ":help":
            env.get("help")()
            continue
        if not buf and line.strip() == ":env":
            for k in sorted(env.values):
                env.get("_writeln")(env.get("stdout"), f"{k} = {format_debug(env.values[k])}")
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
                _emit_result(env, result)
        except GeniaQuietBrokenPipe:
            return
        except Exception as e:  # noqa: BLE001
            _emit_error(env, f"Error: {e}")


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
    env = make_global_env(
        debug_hooks=session,
        debug_mode=True,
        output_handler=session.emit_stdout_output,
        stderr_stream=error_stream,
    )
    session.ensure_root_frame(env)
    return session.run(lambda: run_source(source, env, filename=resolved_path, debug_hooks=session, debug_mode=True), error_stream=error_stream)


def _main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="genia.interpreter")
    command_group = parser.add_mutually_exclusive_group()
    command_group.add_argument("-c", "--command")
    command_group.add_argument("-p", "--pipe")
    parser.add_argument("--debug-stdio", action="store_true")
    args, remaining_args = parser.parse_known_args(argv)

    program_path: Optional[str] = None
    script_args: list[str] = []
    if args.command is not None or args.pipe is not None:
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

    if args.pipe is not None:
        env = make_global_env(cli_args=script_args)
        try:
            wrapped_source = _wrap_pipe_mode_expr(args.pipe)
            run_source(wrapped_source, env, filename="<pipe>")
            return 0
        except GeniaQuietBrokenPipe:
            return 0
        except Exception as e:  # noqa: BLE001
            _emit_error(env, f"Error: {e}")
            return 1

    if args.command is not None:
        env = make_global_env(cli_args=script_args)
        try:
            run_result = run_source(args.command, env, filename="<command>")
            result = resolve_program_result(run_result, env)
            if result is not None:
                _emit_result(env, result)
            return 0
        except GeniaQuietBrokenPipe:
            return 0
        except Exception as e:  # noqa: BLE001
            _emit_error(env, f"Error: {e}")
            return 1
    if program_path is not None:
        env = make_global_env(cli_args=script_args)
        try:
            with open(program_path, "r", encoding="utf-8") as f:
                run_result = run_source(f.read(), env, filename=str(Path(program_path).resolve()))
            result = resolve_program_result(run_result, env)
            if result is not None:
                _emit_result(env, result)
            return 0
        except GeniaQuietBrokenPipe:
            return 0
        except Exception as e:  # noqa: BLE001
            _emit_error(env, f"Error: {e}")
            return 1

    repl()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
