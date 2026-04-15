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
import io
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from collections import deque
import queue
import random
import time
from urllib.parse import parse_qsl, urlsplit
import zipfile
from importlib import resources as importlib_resources
from pathlib import Path
import argparse
import re
import sys
import threading
from dataclasses import dataclass, field, fields, is_dataclass
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
ALWAYS_OPERATOR_DELIMITERS = frozenset({"+", "*", "/", "%", "=", "<", ">", "|", ",", ";", ":", "@", "(", ")", "{", "}", "[", "]"})
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
    ("AT", r"@"),
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
    ("AT", "@"),
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
class Annotation(Node):
    name: str
    value: Node
    span: SourceSpan | None = None


@dataclass
class AnnotatedNode(Node):
    annotations: list[Annotation]
    target: Node
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
class IrAnnotation(IrNode):
    """Lowered annotation payload for a bindable definition."""

    name: str
    value: IrNode
    span: SourceSpan | None = None


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
class IrOptionSome(IrNode):
    """Structured some value with explicit lowered inner value."""

    value: IrNode
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
class IrPipeline(IrNode):
    """Explicit pipeline source plus ordered stages for left-to-right evaluation."""

    source: IrNode
    stages: list[IrNode]
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
    annotations: list[IrAnnotation] = field(default_factory=list)
    span: SourceSpan | None = None


@dataclass
class IrFuncDef(IrNode):
    """Named function definition with lowered body."""

    name: str
    params: list[str]
    rest_param: str | None
    docstring: str | None
    body: IrNode
    annotations: list[IrAnnotation] = field(default_factory=list)
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


# Portable/shared Core IR node families produced by AST->IR lowering.
PORTABLE_CORE_IR_NODE_TYPES: tuple[type[IrNode], ...] = (
    IrAnnotation,
    IrLiteral,
    IrOptionNone,
    IrOptionSome,
    IrVar,
    IrQuote,
    IrDelay,
    IrQuasiQuote,
    IrUnquote,
    IrUnquoteSplicing,
    IrUnary,
    IrBinary,
    IrPipeline,
    IrCall,
    IrExprStmt,
    IrBlock,
    IrList,
    IrMap,
    IrSpread,
    IrCaseClause,
    IrCase,
    IrLambda,
    IrAssign,
    IrFuncDef,
    IrImport,
)

# Host-local post-lowering optimized nodes are intentionally outside the minimal portable contract.
HOST_LOCAL_POST_LOWERING_IR_NODE_TYPES: tuple[type[IrNode], ...] = (
    IrListTraversalLoop,
)


def iter_ir_nodes(root: IrNode | Iterable[IrNode]) -> Iterator[IrNode]:
    """Yield IR nodes in depth-first order for validation and tooling."""
    if isinstance(root, IrNode):
        stack: list[IrNode] = [root]
    else:
        stack = list(root)

    while stack:
        node = stack.pop()
        yield node

        children: list[IrNode] = []
        if isinstance(node, IrOptionNone):
            if node.reason is not None:
                children.append(node.reason)
            if node.context is not None:
                children.append(node.context)
        elif isinstance(node, IrOptionSome):
            children.append(node.value)
        elif isinstance(node, IrDelay):
            children.append(node.expr)
        elif isinstance(node, IrUnquote):
            children.append(node.expr)
        elif isinstance(node, IrUnquoteSplicing):
            children.append(node.expr)
        elif isinstance(node, IrUnary):
            children.append(node.expr)
        elif isinstance(node, IrBinary):
            children.extend([node.left, node.right])
        elif isinstance(node, IrPipeline):
            children.append(node.source)
            children.extend(node.stages)
        elif isinstance(node, IrCall):
            children.append(node.fn)
            children.extend(node.args)
        elif isinstance(node, IrExprStmt):
            children.append(node.expr)
        elif isinstance(node, IrBlock):
            children.extend(node.exprs)
        elif isinstance(node, IrList):
            children.extend(node.items)
        elif isinstance(node, IrMap):
            children.extend(value for _, value in node.items)
        elif isinstance(node, IrSpread):
            children.append(node.expr)
        elif isinstance(node, IrCaseClause):
            if node.guard is not None:
                children.append(node.guard)
            children.append(node.result)
        elif isinstance(node, IrCase):
            children.extend(node.clauses)
        elif isinstance(node, IrLambda):
            children.append(node.body)
        elif isinstance(node, IrAssign):
            children.extend(annotation.value for annotation in node.annotations)
            children.append(node.expr)
        elif isinstance(node, IrFuncDef):
            children.extend(annotation.value for annotation in node.annotations)
            children.append(node.body)
        elif isinstance(node, IrListTraversalLoop):
            children.extend([node.empty_clause, node.zero_clause])

        stack.extend(reversed(children))


def assert_portable_core_ir(nodes: Iterable[IrNode]) -> None:
    """Raise when host-local post-lowering IR appears in a portable/lowered program."""
    for node in iter_ir_nodes(nodes):
        if isinstance(node, HOST_LOCAL_POST_LOWERING_IR_NODE_TYPES):
            raise RuntimeError(
                "Portable Core IR validation failed: host-local post-lowering node "
                f"{type(node).__name__} appeared before host-local optimization."
            )


def lower_program(nodes: Iterable[Node]) -> list[IrNode]:
    return [lower_node(node) for node in nodes]


def _lower_annotations(annotations: list[Annotation]) -> list[IrAnnotation]:
    return [IrAnnotation(annotation.name, lower_node(annotation.value), span=annotation.span) for annotation in annotations]


def _map_literal_key_name(key: Node) -> str:
    if isinstance(key, Var):
        return key.name
    if isinstance(key, String):
        return key.value
    raise RuntimeError(f"Unsupported map literal key node: {key!r}")


def _flatten_pipeline_ast(node: Node) -> tuple[Node, list[Node]]:
    if isinstance(node, Binary) and node.op == "PIPE_FWD":
        source, stages = _flatten_pipeline_ast(node.left)
        return source, [*stages, node.right]
    return node, []


def lower_node(node: Node) -> IrNode:
    if isinstance(node, AnnotatedNode):
        lowered_annotations = _lower_annotations(node.annotations)
        target = node.target
        if isinstance(target, Assign):
            return IrAssign(target.name, lower_node(target.expr), annotations=lowered_annotations, span=node.span)
        if isinstance(target, FuncDef):
            return IrFuncDef(
                target.name,
                target.params,
                target.rest_param,
                target.docstring,
                lower_node(target.body),
                annotations=lowered_annotations,
                span=node.span,
            )
        raise RuntimeError(f"Annotated target is not bindable during lowering: {target!r}")
    if isinstance(node, ExprStmt):
        return IrExprStmt(lower_node(node.expr), span=node.span)
    if isinstance(node, Number):
        return IrLiteral(node.value, span=node.span)
    if isinstance(node, String):
        return IrLiteral(node.value, span=node.span)
    if isinstance(node, Boolean):
        return IrLiteral(node.value, span=node.span)
    if isinstance(node, Nil):
        return IrOptionNone(IrLiteral("nil", span=node.span), None, span=node.span)
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
            source, stages = _flatten_pipeline_ast(node)
            return IrPipeline(lower_node(source), [lower_node(stage) for stage in stages], span=node.span)
        return IrBinary(lower_node(node.left), node.op, lower_node(node.right), span=node.span)
    if isinstance(node, Call):
        if isinstance(node.fn, Var) and node.fn.name == "some" and len(node.args) == 1:
            return IrOptionSome(lower_node(node.args[0]), span=node.span)
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
            annotations=[],
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
        return IrPatNone(IrPatLiteral("nil"), None)
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
        result: Any = OPTION_NONE
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
        return OPTION_NONE
    if isinstance(node, NoneOption):
        reason = quote_node(node.reason) if node.reason is not None else "nil"
        context = quote_node(node.context) if node.context is not None else None
        return make_none(reason, context)
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
        result: Any = OPTION_NONE
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
        return OPTION_NONE
    if isinstance(pattern, NoneOption):
        reason = quote_pattern_node(pattern.reason) if pattern.reason is not None else "nil"
        context = quote_pattern_node(pattern.context) if pattern.context is not None else None
        return make_none(reason, context)
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
        result: Any = OPTION_NONE
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
    if value is None or _is_nil_none(value):
        return ()
    if isinstance(value, list):
        return tuple(value)
    if isinstance(value, GeniaPair):
        items: list[Any] = []
        current: Any = value
        while isinstance(current, GeniaPair):
            items.append(current.head)
            current = current.tail
        if current is not None and not _is_nil_none(current):
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
        result: Any = OPTION_NONE
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
            return OPTION_NONE
        if isinstance(current, NoneOption):
            reason = qq(current.reason, depth) if current.reason is not None else "nil"
            context = qq(current.context, depth) if current.context is not None else None
            return make_none(reason, context)
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
            and (
                (isinstance(clause.result, IrLiteral) and clause.result.value is None)
                or (
                    isinstance(clause.result, IrOptionNone)
                    and isinstance(clause.result.reason, IrLiteral)
                    and clause.result.reason.value == "nil"
                    and clause.result.context is None
                )
            )
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
        annotations=fn.annotations,
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
    if isinstance(node, IrPipeline):
        return recursive_call_count(node.source, fn_name) + sum(recursive_call_count(stage, fn_name) for stage in node.stages)
    if isinstance(node, IrOptionSome):
        return recursive_call_count(node.value, fn_name)
    if isinstance(node, IrOptionNone):
        return (
            recursive_call_count(node.reason, fn_name) if node.reason is not None else 0
        ) + (
            recursive_call_count(node.context, fn_name) if node.context is not None else 0
        )
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
                    return j < len(self.tokens) and self.tokens[j].kind in {"ASSIGN", "ARROW", "LBRACE"}
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

            if self.at("ASSIGN", "ARROW", "LBRACE"):
                return name, params, rest_param, name_token

            self.i = save
            return None
        except SyntaxError:
            self.i = save
            if self.function_header_has_body_starter(save):
                raise
            return None

    def parse_toplevel(self) -> Node:
        if self.at("AT"):
            annotations = self.parse_prefix_annotations()
            target = self.try_parse_bindable_toplevel()
            if target is None:
                bad = self.peek()
                raise SyntaxError(
                    "Prefix annotations must be followed by a top-level function definition "
                    f"or simple-name assignment, got {bad.text!r} ({bad.kind}) at {bad.pos}"
                )
            return AnnotatedNode(
                annotations,
                target,
                span=self.merge_spans(annotations[0].span, target.span),
            )

        import_stmt = self.try_parse_import_stmt()
        if import_stmt is not None:
            return import_stmt

        bindable = self.try_parse_bindable_toplevel()
        if bindable is not None:
            return bindable

        expr = self.parse_expr()
        if self.at("ASSIGN"):
            raise SyntaxError("Assignment target must be a simple name")
        return ExprStmt(expr, span=expr.span)

    def try_parse_import_stmt(self) -> ImportStmt | None:
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
        return None

    def try_parse_bindable_toplevel(self) -> Node | None:
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

            if self.at("ARROW"):
                self.eat("ARROW")
                self.skip_separators()
                body = self.parse_expr()
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
        return None

    def parse_prefix_annotations(self) -> list[Annotation]:
        annotations: list[Annotation] = []
        while self.at("AT"):
            start_tok = self.eat("AT")
            if not self.at("IDENT"):
                bad = self.peek()
                raise SyntaxError(f"Annotation expected a name identifier, got {bad.text!r} ({bad.kind}) at {bad.pos}")
            name_tok = self.eat("IDENT")
            if not self.at_expr_start():
                bad = self.peek()
                raise SyntaxError(f"Annotation @{name_tok.text} expected a value expression, got {bad.text!r} ({bad.kind}) at {bad.pos}")
            value = self.parse_expr()
            end_tok = self.peek(-1)
            annotations.append(
                Annotation(
                    name_tok.text,
                    value,
                    span=self.span_for_tokens(start_tok, end_tok),
                )
            )
            if not self.at("NEWLINE", "SEMI", "EOF"):
                bad = self.peek()
                raise SyntaxError(
                    f"Annotation @{name_tok.text} must end at a newline before its target, got {bad.text!r} ({bad.kind}) at {bad.pos}"
                )
            self.skip_separators()
        return annotations

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
        self.binding_metadata: dict[str, GeniaMap] = {}
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

    def set(
        self,
        name: str,
        value: Any,
        *,
        assignable: bool = True,
        metadata: GeniaMap | None = None,
        preserve_metadata: bool = False,
    ) -> None:
        self.values[name] = value
        if metadata is not None:
            self.binding_metadata[name] = metadata
        elif not preserve_metadata:
            self.binding_metadata.pop(name, None)
        if assignable:
            self.assignable.add(name)
        else:
            self.assignable.discard(name)

    def assign(self, name: str, value: Any, *, metadata: GeniaMap | None = None) -> None:
        target_env = self.find_assign_target(name)
        if target_env is None:
            self.set(name, value, assignable=True, metadata=metadata, preserve_metadata=metadata is None)
            return
        target_env.values[name] = value
        if metadata is not None:
            target_env.binding_metadata[name] = _merge_metadata_maps(target_env.binding_metadata.get(name), metadata)

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

    def define_function(self, fn: "GeniaFunction", *, metadata: GeniaMap | None = None) -> None:
        existing = self.values.get(fn.name)
        if existing is None:
            group = GeniaFunctionGroup(fn.name)
            if metadata is not None:
                group.merge_metadata(metadata)
            group.add_clause(fn)
            self.set(fn.name, group, assignable=True, metadata=group.metadata)
            return
        if not isinstance(existing, GeniaFunctionGroup):
            raise TypeError(f"Cannot define function {fn.name}/{fn.arity}: name already bound to non-function value")
        if metadata is not None:
            existing.merge_metadata(metadata)
            self.binding_metadata[fn.name] = existing.metadata
        existing.add_clause(fn)

    def get_metadata(self, name: str) -> "GeniaMap":
        if name in self.values:
            return self.binding_metadata.get(name, GeniaMap())
        if self.parent is not None:
            return self.parent.get_metadata(name)
        raise NameError(f"Undefined name: {name}")

    def merge_binding_metadata(self, name: str, metadata: "GeniaMap") -> None:
        env: Env = self
        while True:
            if name in env.values:
                merged = _merge_metadata_maps(env.binding_metadata.get(name), metadata)
                env.binding_metadata[name] = merged
                value = env.values[name]
                if isinstance(value, GeniaFunctionGroup):
                    value.metadata = merged
                return
            if env.parent is None:
                raise NameError(f"Undefined name: {name}")
            env = env.parent

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
        if module_name == "python" or module_name.startswith("python."):
            module_value = _build_python_host_module(root, module_name)
            root.loaded_modules[module_name] = module_value
            return module_value

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
    metadata: "GeniaMap" = field(default_factory=lambda: GeniaMap())

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

    def merge_metadata(self, metadata: "GeniaMap") -> None:
        self.metadata = _merge_metadata_maps(self.metadata, metadata)

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
_MAP_GET_MISSING = object()
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
    _STOP = object()

    def __init__(self, state_ref: GeniaRef):
        self._state_ref = state_ref
        self._condition = threading.Condition()
        self._failed = False
        self._stopped = False
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
            if kind == "cell_stop":
                first._stopped = True
                first._mailbox.put((first._generation, GeniaCell._STOP))
                continue
            raise RuntimeError(f"Unknown cell action kind: {kind}")

    def _run(self) -> None:
        while True:
            generation, update_fn = self._mailbox.get()
            if update_fn is GeniaCell._STOP:
                return
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
            if self._stopped:
                raise RuntimeError("Cell has been stopped")
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
            self._stopped = False
            self._error = None
            self._state_ref.set(value)
            self._condition.notify_all()
        if not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        return self

    def stop(self) -> None:
        with self._condition:
            if self._stopped or self._failed:
                return
            self._stopped = True
            generation = self._generation
        self._mailbox.put((generation, GeniaCell._STOP))

    def stopped(self) -> bool:
        with self._condition:
            return self._stopped

    def status(self) -> str:
        with self._condition:
            if self._failed:
                return "failed"
            if self._stopped:
                return "stopped"
            return "ready"

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
                if rest_name is not None or not _is_nil_none(current.tail):
                    raise TypeError("extend expected at most one final rest parameter")
                rest_value = _syntax_pair_nth(item, 1, "extend")
                if not isinstance(rest_value, GeniaSymbol):
                    raise TypeError("extend expected the rest parameter name to be a symbol")
                rest_name = rest_value.name
            else:
                raise TypeError("extend expected lambda parameter data")
            current = current.tail
        if not _is_nil_none(current):
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

    def get(self, key: Any, default: Any = _MAP_GET_MISSING) -> Any:
        frozen_key = _freeze_map_key(key)
        entry = self._entries.get(frozen_key)
        if entry is None:
            if default is not _MAP_GET_MISSING:
                return default
            return make_none("missing-key", GeniaMap().put("key", key))
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

    def items(self) -> list[tuple[Any, Any]]:
        return [(raw_key, raw_value) for raw_key, raw_value in self._entries.values()]

    def __repr__(self) -> str:
        return f"<map {len(self._entries)}>"


def _merge_metadata_maps(base: GeniaMap | None, override: GeniaMap | None) -> GeniaMap:
    result = base if base is not None else GeniaMap()
    if override is None:
        return result
    for key, value in override.items():
        result = result.put(key, value)
    return result


@dataclass(frozen=True)
class GeniaOptionNone:
    reason: Any = None
    context: Any = None

    @property
    def meta(self) -> "GeniaMap":
        metadata = GeniaMap().put("reason", self.reason)
        if self.context is not None:
            metadata = metadata.put("context", self.context)
        return metadata

    def __repr__(self) -> str:
        if self.reason is None:
            return 'none("nil")'
        if self.context is None:
            return f"none({self.reason!r})"
        return f"none({self.reason!r}, {self.context!r})"

def make_none(reason: Any = "nil", meta: Any = None) -> GeniaOptionNone:
    if reason is None:
        reason = "nil"
    if not isinstance(reason, str):
        raise TypeError(f"none reason expected string, received {_runtime_type_name(reason)}")
    if meta is not None and not isinstance(meta, GeniaMap):
        raise TypeError(f"none meta expected a map, received {_runtime_type_name(meta)}")
    return GeniaOptionNone(reason, meta)


def is_none(value: Any) -> bool:
    return isinstance(value, GeniaOptionNone)


def _is_nil_none(value: Any) -> bool:
    return is_none(value) and value.reason == "nil" and value.context is None


def _normalize_absence(value: Any) -> Any:
    if value is None:
        return OPTION_NONE
    return value


def _normalize_nil(value: Any) -> Any:
    return _normalize_absence(value)


OPTION_NONE = make_none("nil")
_RNG_MODULUS = 2**32
_RNG_MULTIPLIER = 1664525
_RNG_INCREMENT = 1013904223


@dataclass(frozen=True)
class GeniaOptionSome:
    value: Any

    def __repr__(self) -> str:
        return f"some({self.value!r})"


@dataclass(frozen=True)
class GeniaRng:
    state: int

    def __repr__(self) -> str:
        return "<rng>"


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


@dataclass(frozen=True)
class GeniaPythonHandle:
    kind: str
    value: Any

    def __repr__(self) -> str:
        return f"<python {self.kind}>"


def _genia_map_to_host_dict(value: GeniaMap) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for _, (raw_key, raw_value) in value._entries.items():
        host_key = _genia_map_key_to_host(raw_key)
        result[host_key] = _genia_to_python_host(raw_value)
    return result


def _genia_map_key_to_host(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, GeniaSymbol):
        return value.name
    if isinstance(value, list):
        return tuple(_genia_map_key_to_host(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_genia_map_key_to_host(item) for item in value)
    raise TypeError(f"python interop cannot convert map key type {_runtime_type_name(value)}")


def _genia_to_python_host(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if is_none(value):
        return None
    if isinstance(value, GeniaOptionSome):
        return _genia_to_python_host(value.value)
    if isinstance(value, list):
        return [_genia_to_python_host(item) for item in value]
    if isinstance(value, GeniaMap):
        return _genia_map_to_host_dict(value)
    if isinstance(value, GeniaPythonHandle):
        return value.value
    raise TypeError(f"python interop cannot convert {_runtime_type_name(value)} to a host value")


def _python_host_to_genia(value: Any) -> Any:
    if value is None:
        return OPTION_NONE
    if isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        return [_python_host_to_genia(item) for item in value]
    if isinstance(value, tuple):
        return [_python_host_to_genia(item) for item in value]
    if isinstance(value, dict):
        result = GeniaMap()
        for raw_key, raw_value in value.items():
            key = _python_host_map_key_to_genia(raw_key)
            result = result.put(key, _python_host_to_genia(raw_value))
        return result
    if isinstance(value, GeniaPythonHandle):
        return value
    return GeniaPythonHandle(type(value).__name__.lower(), value)


def _python_host_map_key_to_genia(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, tuple):
        return [_python_host_map_key_to_genia(item) for item in value]
    raise TypeError(f"python interop cannot convert host map key type {type(value).__name__}")


def _wrap_python_host_callable(
    module_name: str,
    export_name: str,
    fn: Callable[..., Any],
) -> Callable[..., Any]:
    def wrapped(*args: Any) -> Any:
        try:
            host_args = [_genia_to_python_host(arg) for arg in args]
            result = fn(*host_args)
        except (TypeError, ValueError, FileNotFoundError, OSError, PermissionError, RuntimeError):
            raise
        except Exception as exc:  # pragma: no cover - defensive bridge fallback
            raise RuntimeError(f"{module_name}/{export_name} raised {type(exc).__name__}: {exc}") from exc
        return _normalize_absence(_python_host_to_genia(result))

    return wrapped


def _mark_handles_none(fn: Callable[..., Any]) -> Callable[..., Any]:
    setattr(fn, "__genia_handles_none__", True)
    return fn


def _mark_handles_some(fn: Callable[..., Any]) -> Callable[..., Any]:
    setattr(fn, "__genia_handles_some__", True)
    return fn


_NONE_AWARE_PUBLIC_FUNCTIONS = frozenset(
    {
        "apply",
        "inspect",
        "trace",
        "tap",
        "some",
        "none?",
        "some?",
        "get",
        "get?",
        "map_some",
        "flat_map_some",
        "then_get",
        "then_first",
        "then_nth",
        "then_find",
        "or_else",
        "or_else_with",
        "unwrap_or",
        "absence_reason",
        "absence_context",
        "absence_meta",
        "is_some?",
        "is_none?",
        "cli_option",
        "cli_option_or",
        "map_put",
        "write",
        "writeln",
        "flush",
        "nil?",
        "cons",
        "car",
        "cdr",
        "pair?",
        "null?",
        "empty_env",
        "lookup",
        "define",
        "set",
        "extend",
        "eval",
        "self_evaluating?",
        "symbol_expr?",
        "tagged_list?",
        "quoted_expr?",
        "quasiquoted_expr?",
        "assignment_expr?",
        "lambda_expr?",
        "application_expr?",
        "block_expr?",
        "match_expr?",
        "text_of_quotation",
        "assignment_name",
        "assignment_value",
        "lambda_params",
        "lambda_body",
        "operator",
        "operands",
        "block_expressions",
        "match_branches",
        "branch_pattern",
        "branch_has_guard?",
        "branch_guard",
        "branch_body",
        "apply_dispatch",
        "_match_procedure?",
        "_match_expr",
        "_match_env",
        "_compound_procedure?",
        "_compound_params",
        "_compound_body",
        "_compound_env",
        "_apply_match_procedure",
        "_eval_match_branches",
        "_eval_match_branch",
        "_eval_match_branch_result",
        "_eval_guarded_branch",
        "eval_dispatch",
        "eval_assignment",
        "make_function",
        "make_matcher",
        "eval_operands",
        "eval_block",
        "eval_sequence",
        "tagged_list_impl",
        "syntax_expect_tagged",
        "syntax_pair_nth",
        "syntax_pair_nth_from",
        "syntax_pair_rest",
        "syntax_pair_rest_from",
        "syntax_expect_match_branch",
        "syntax_match_branch_size",
        "syntax_match_branch_size_checked",
        "syntax_proper_list_length",
        "branch_guard_from_size",
        "branch_body_from_size",
    }
)



_SOME_AWARE_PUBLIC_FUNCTIONS = _NONE_AWARE_PUBLIC_FUNCTIONS

def _pattern_explicitly_handles_none(pattern: IrPattern) -> bool:
    if isinstance(pattern, IrPatNone):
        return True
    if isinstance(pattern, IrPatTuple):
        return any(_pattern_explicitly_handles_none(item) for item in pattern.items)
    if isinstance(pattern, IrPatList):
        return any(_pattern_explicitly_handles_none(item) for item in pattern.items)
    if isinstance(pattern, IrPatMap):
        return any(_pattern_explicitly_handles_none(item) for _, item in pattern.items)
    if isinstance(pattern, IrPatSome):
        return _pattern_explicitly_handles_none(pattern.inner)
    return False


def _pattern_explicitly_handles_some(pattern: IrPattern) -> bool:
    if isinstance(pattern, IrPatSome):
        return True
    if isinstance(pattern, IrPatTuple):
        return any(_pattern_explicitly_handles_some(item) for item in pattern.items)
    if isinstance(pattern, IrPatList):
        return any(_pattern_explicitly_handles_some(item) for item in pattern.items)
    if isinstance(pattern, IrPatMap):
        return any(_pattern_explicitly_handles_some(item) for _, item in pattern.items)
    if isinstance(pattern, IrPatNone):
        if pattern.reason is not None and _pattern_explicitly_handles_some(pattern.reason):
            return True
        if pattern.context is not None and _pattern_explicitly_handles_some(pattern.context):
            return True
    return False


def _callable_case_explicitly_handles_none(body: IrNode) -> bool:
    if isinstance(body, IrCase):
        return any(
            _pattern_explicitly_handles_none(clause.pattern) or _pattern_explicitly_handles_some(clause.pattern)
            for clause in body.clauses
        )
    if isinstance(body, IrBlock) and body.exprs:
        return _callable_case_explicitly_handles_none(body.exprs[-1])
    return False


def _callable_case_explicitly_handles_some(body: IrNode) -> bool:
    if isinstance(body, IrCase):
        return any(_pattern_explicitly_handles_some(clause.pattern) for clause in body.clauses)
    if isinstance(body, IrBlock) and body.exprs:
        return _callable_case_explicitly_handles_some(body.exprs[-1])
    return False


def _body_delegates_to_option_aware(body: IrNode) -> bool:
    """Return True when the body's final expression delegates to a known Option-aware function."""
    if isinstance(body, IrCall) and isinstance(body.fn, IrVar):
        return body.fn.name in _NONE_AWARE_PUBLIC_FUNCTIONS
    if isinstance(body, IrBlock) and body.exprs:
        return _body_delegates_to_option_aware(body.exprs[-1])
    return False


def _function_explicitly_handles_none(fn: GeniaFunction) -> bool:
    return _callable_case_explicitly_handles_none(fn.body) or _body_delegates_to_option_aware(fn.body)


def _function_explicitly_handles_some(fn: GeniaFunction) -> bool:
    return _callable_case_explicitly_handles_some(fn.body) or _body_delegates_to_option_aware(fn.body)


def _callable_explicitly_handles_none(fn: Any, arity: int, callee_node: IrNode | None = None) -> bool:
    if getattr(fn, "__genia_handles_none__", False):
        return True
    if isinstance(fn, GeniaFunction):
        if fn.name in _NONE_AWARE_PUBLIC_FUNCTIONS:
            return True
        return _function_explicitly_handles_none(fn)
    if isinstance(fn, GeniaFunctionGroup):
        if fn.name in _NONE_AWARE_PUBLIC_FUNCTIONS:
            return True
        candidate = fn.get(arity)
        if candidate is not None:
            return _function_explicitly_handles_none(candidate)
        matches = [
            current
            for current in fn.values()
            if isinstance(current, GeniaFunction)
            and current.rest_param is not None
            and arity >= current.arity
        ]
        if len(matches) == 1:
            return _function_explicitly_handles_none(matches[0])
        if isinstance(callee_node, IrVar) and callee_node.name in {"map", "filter", "take", "scan"}:
            return True
        return False
    genia_body = getattr(fn, "__genia_body__", None)
    if genia_body is not None:
        return _callable_case_explicitly_handles_none(genia_body) or _body_delegates_to_option_aware(genia_body)
    return False


def _callable_explicitly_handles_some(fn: Any, arity: int, callee_node: IrNode | None = None) -> bool:
    if getattr(fn, "__genia_handles_some__", False):
        return True
    if isinstance(fn, GeniaFunction):
        if fn.name in _SOME_AWARE_PUBLIC_FUNCTIONS:
            return True
        return _function_explicitly_handles_some(fn)
    if isinstance(fn, GeniaFunctionGroup):
        if fn.name in _SOME_AWARE_PUBLIC_FUNCTIONS:
            return True
        candidate = fn.get(arity)
        if candidate is not None:
            return _function_explicitly_handles_some(candidate)
        matches = [
            current
            for current in fn.values()
            if isinstance(current, GeniaFunction)
            and current.rest_param is not None
            and arity >= current.arity
        ]
        if len(matches) == 1:
            return _function_explicitly_handles_some(matches[0])
        return False
    genia_body = getattr(fn, "__genia_body__", None)
    if genia_body is not None:
        return _callable_case_explicitly_handles_some(genia_body) or _body_delegates_to_option_aware(genia_body)
    return False


_SAFE_PYTHON_OPEN_MODES = frozenset({"r", "w", "a"})


def _python_open_impl(path: Any, mode: Any = "r") -> Any:
    if not isinstance(path, str):
        raise TypeError(f"python/open expected a string path, received {_runtime_type_name(path)}")
    if not isinstance(mode, str):
        raise TypeError(f"python/open expected a string mode, received {_runtime_type_name(mode)}")
    if mode not in _SAFE_PYTHON_OPEN_MODES:
        raise ValueError("python/open only allows text modes 'r', 'w', or 'a'")
    try:
        handle = open(path, mode, encoding="utf-8")
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise OSError(f"python/open could not open {path}: {exc}") from exc
    return GeniaPythonHandle("file", handle)


def _ensure_python_file(value: Any, name: str) -> io.TextIOBase:
    if isinstance(value, GeniaPythonHandle):
        value = value.value
    if not isinstance(value, io.TextIOBase):
        raise TypeError(f"{name} expected a python file handle, received {_runtime_type_name(value)}")
    return value


def _python_read_impl(handle: Any) -> str:
    file_handle = _ensure_python_file(handle, "python/read")
    return file_handle.read()


def _python_write_impl(handle: Any, text: Any) -> int:
    file_handle = _ensure_python_file(handle, "python/write")
    if not isinstance(text, str):
        raise TypeError(f"python/write expected a string as second argument, received {_runtime_type_name(text)}")
    return file_handle.write(text)


def _python_close_impl(handle: Any) -> Any:
    file_handle = _ensure_python_file(handle, "python/close")
    file_handle.close()
    return None


def _python_read_text_impl(path: Any) -> str:
    if not isinstance(path, str):
        raise TypeError(f"python/read_text expected a string path, received {_runtime_type_name(path)}")
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise OSError(f"python/read_text could not read {path}: {exc}") from exc


def _python_write_text_impl(path: Any, text: Any) -> int:
    if not isinstance(path, str):
        raise TypeError(f"python/write_text expected a string path, received {_runtime_type_name(path)}")
    if not isinstance(text, str):
        raise TypeError(f"python/write_text expected a string body, received {_runtime_type_name(text)}")
    try:
        return Path(path).write_text(text, encoding="utf-8")
    except OSError as exc:
        raise OSError(f"python/write_text could not write {path}: {exc}") from exc


def _python_len_impl(value: Any) -> int:
    return len(value)


def _python_str_impl(value: Any) -> str:
    return str(value)


def _python_json_loads_impl(text: Any) -> Any:
    if not isinstance(text, str):
        raise TypeError(f"python.json/loads expected a string, received {_runtime_type_name(text)}")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"python.json/loads invalid JSON: {exc.msg} at line {exc.lineno} column {exc.colno}"
        ) from exc


def _python_json_dumps_impl(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _build_python_host_module(root: "Env", module_name: str) -> ModuleValue:
    json_module = ModuleValue(
        "python.json",
        {
            "loads": _wrap_python_host_callable("python.json", "loads", _python_json_loads_impl),
            "dumps": _wrap_python_host_callable("python.json", "dumps", _python_json_dumps_impl),
        },
        "<python-host:python.json>",
    )
    root.loaded_modules.setdefault("python.json", json_module)

    root_module = ModuleValue(
        "python",
        {
            "json": json_module,
            "open": _wrap_python_host_callable("python", "open", _python_open_impl),
            "read": _wrap_python_host_callable("python", "read", _python_read_impl),
            "write": _wrap_python_host_callable("python", "write", _python_write_impl),
            "close": _wrap_python_host_callable("python", "close", _python_close_impl),
            "read_text": _wrap_python_host_callable("python", "read_text", _python_read_text_impl),
            "write_text": _wrap_python_host_callable("python", "write_text", _python_write_text_impl),
            "len": _wrap_python_host_callable("python", "len", _python_len_impl),
            "str": _wrap_python_host_callable("python", "str", _python_str_impl),
        },
        "<python-host:python>",
    )
    root.loaded_modules.setdefault("python", root_module)

    if module_name == "python":
        return root_module
    if module_name == "python.json":
        return json_module
    raise PermissionError(f"Host module not allowed: {module_name}")


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
    def __init__(
        self,
        iterator_factory: Callable[[], Iterable[Any]],
        *,
        label: str = "flow",
        close_on_early_termination: bool = True,
    ):
        self._iterator_factory = iterator_factory
        self._label = label
        self._consumed = False
        self._close_on_early_termination = close_on_early_termination

    def consume(self) -> Iterable[Any]:
        if self._consumed:
            raise RuntimeError("Flow has already been consumed")
        self._consumed = True
        produced = self._iterator_factory()
        try:
            return iter(produced)
        except TypeError:
            raise TypeError(f"Flow source {self._label} did not produce an iterable") from None

    def __repr__(self) -> str:
        state = "consumed" if self._consumed else "ready"
        return f"<flow {self._label} {state}>"

    @property
    def close_on_early_termination(self) -> bool:
        return self._close_on_early_termination


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
        result = OPTION_NONE
        for node in nodes:
            result = self.eval(node)
        return result

    def eval_annotations(self, annotations: list[IrAnnotation]) -> GeniaMap:
        metadata = GeniaMap()
        string_metadata_annotations = {
            "doc": "doc",
            "since": "since",
            "deprecated": "deprecated",
            "category": "category",
        }
        for annotation in annotations:
            value = self.eval(annotation.value)
            metadata_key = string_metadata_annotations.get(annotation.name)
            if metadata_key is not None:
                if not isinstance(value, str):
                    raise _annotation_metadata_error(annotation.name, value, "a string")
                metadata = metadata.put(metadata_key, value)
                continue
            if annotation.name == "meta":
                if not isinstance(value, GeniaMap):
                    raise _annotation_metadata_error("meta", value, "a map")
                metadata = _merge_metadata_maps(metadata, value)
                continue
            raise RuntimeError(
                "Unsupported annotation: "
                f"@{annotation.name}. Supported annotations: @doc, @meta, @since, @deprecated, @category"
            )
        return metadata

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
                return OPTION_NONE
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
                    return OPTION_NONE
                local = Env(self.env)
                for k, v in match_env.items():
                    local.set(k, v)
                return Evaluator(local, self.debug_hooks, self.debug_mode).eval_tail(body.empty_clause.result)

            if n_value == 0:
                match_env = self.match_pattern(body.zero_clause.pattern, current_args)
                if match_env is None:
                    return OPTION_NONE
                local = Env(self.env)
                for k, v in match_env.items():
                    local.set(k, v)
                return Evaluator(local, self.debug_hooks, self.debug_mode).eval_tail(body.zero_clause.result)

            if not isinstance(n_value, (int, float)):
                return OPTION_NONE
            if n_value < 0:
                return OPTION_NONE
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
            if clause.guard is not None and not truthy(Evaluator(local, self.debug_hooks, self.debug_mode).eval(clause.guard)):
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
        if isinstance(node, IrPipeline):
            return self.eval_pipeline(node, tail_position=True)
        if isinstance(node, IrBlock):
            local = Env(self.env)
            ev = Evaluator(local, self.debug_hooks, self.debug_mode)
            for expr in node.exprs[:-1]:
                ev.eval(expr)
            if not node.exprs:
                return OPTION_NONE
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

    def _pipeline_stage_name(self, node: IrNode) -> str | None:
        if isinstance(node, IrVar):
            return node.name
        if isinstance(node, IrCall) and isinstance(node.fn, IrVar):
            return node.fn.name
        return None

    def _render_pipeline_stage(self, node: IrNode) -> str:
        if isinstance(node, IrVar):
            return node.name
        if isinstance(node, IrLiteral):
            return format_debug(node.value)
        if isinstance(node, IrOptionSome):
            return f"some({self._render_pipeline_stage(node.value)})"
        if isinstance(node, IrOptionNone):
            if node.reason is None:
                return "none"
            reason_text = self._render_pipeline_stage(node.reason)
            if node.context is None:
                return f"none({reason_text})"
            return f"none({reason_text}, {self._render_pipeline_stage(node.context)})"
        if isinstance(node, IrList):
            item_texts: list[str] = []
            for item in node.items:
                if isinstance(item, IrSpread):
                    item_texts.append(f"..{self._render_pipeline_stage(item.expr)}")
                else:
                    item_texts.append(self._render_pipeline_stage(item))
            return f"[{', '.join(item_texts)}]"
        if isinstance(node, IrMap):
            entry_texts = [
                f"{key}: {self._render_pipeline_stage(value)}"
                for key, value in node.entries
            ]
            return f"{{{', '.join(entry_texts)}}}"
        if isinstance(node, IrUnary):
            op = "-" if node.op == "MINUS" else "!"
            return f"{op}{self._render_pipeline_stage(node.expr)}"
        if isinstance(node, IrBinary):
            op_map = {
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
            }
            op = op_map.get(node.op, node.op)
            return f"{self._render_pipeline_stage(node.left)} {op} {self._render_pipeline_stage(node.right)}"
        if isinstance(node, IrCall):
            fn_text = self._render_pipeline_stage(node.fn)
            arg_texts: list[str] = []
            for arg in node.args:
                if isinstance(arg, IrSpread):
                    arg_texts.append(f"..{self._render_pipeline_stage(arg.expr)}")
                else:
                    arg_texts.append(self._render_pipeline_stage(arg))
            return f"{fn_text}({', '.join(arg_texts)})"
        if isinstance(node, IrBlock):
            return "{ ... }"
        if isinstance(node, IrLambda):
            params = ", ".join(node.params)
            if node.rest_param is not None:
                params = f"{params}, ..{node.rest_param}" if params else f"..{node.rest_param}"
            return f"({params}) -> ..."
        if isinstance(node, IrQuote):
            return "quote(...)"
        if isinstance(node, IrQuasiQuote):
            return "quasiquote(...)"
        if isinstance(node, IrPipeline):
            stage_text = " |> ".join(self._render_pipeline_stage(stage) for stage in node.stages)
            return f"{self._render_pipeline_stage(node.source)} |> {stage_text}"
        return node.__class__.__name__

    def _pipeline_stage_mode(self, node: IrNode, stage_input: Any) -> str:
        stage_name = self._pipeline_stage_name(node)
        if stage_name in {"lines", "collect"}:
            return "Explicit bridge mode"
        if isinstance(stage_input, GeniaFlow):
            return "Flow mode"
        return "Value mode"

    def _format_pipeline_stage_span(self, node: IrNode) -> str | None:
        span = getattr(node, "span", None)
        if span is None:
            return None
        return f"{span.filename}:{span.line}"

    def _wrap_pipeline_stage_error(self, exc: Exception, stage_index: int, node: IrNode, stage_input: Any) -> Exception:
        message = str(exc)
        if message.startswith("pipeline stage ") and " failed in " in message:
            return exc
        if isinstance(exc, ValueError) and message.startswith("python.json/loads invalid JSON:"):
            return exc
        stage_text = self._render_pipeline_stage(node)
        mode_text = self._pipeline_stage_mode(node, stage_input)
        span_text = self._format_pipeline_stage_span(node)
        rendered = f"pipeline stage {stage_index + 1} failed in {mode_text} at {stage_text}"
        if span_text is not None:
            rendered += f" [{span_text}]"
        input_type = _runtime_type_name(stage_input)
        if isinstance(stage_input, GeniaOptionSome):
            rendered += f": pipeline value was {input_type} (auto-unwrapped)"
        elif isinstance(stage_input, GeniaOptionNone):
            rendered += f": pipeline value was {input_type}"
        else:
            rendered += f": stage received {input_type}"
        if message:
            rendered += f"; {message}"
        exc_type = exc.__class__
        try:
            return exc_type(rendered)
        except Exception:  # pragma: no cover - defensive fallback
            return RuntimeError(rendered)

    def eval_pipeline(self, node: IrPipeline, tail_position: bool) -> Any:
        stage_value = self.eval(node.source)
        for index, stage in enumerate(node.stages):
            if is_none(stage_value):
                return stage_value
            try:
                stage_value = self.eval_pipeline_stage(
                    stage,
                    stage_value,
                    tail_position=tail_position and index == len(node.stages) - 1,
                )
            except GeniaQuietBrokenPipe:
                raise
            except Exception as exc:  # noqa: BLE001
                raise self._wrap_pipeline_stage_error(exc, index, stage, stage_value) from exc
        return stage_value

    def eval_pipeline_stage(self, node: IrNode, stage_value: Any, *, tail_position: bool) -> Any:
        def invoke_with_pipeline_option_lifting(fn: Any, base_args: list[Any], callee_node: IrNode) -> Any:
            # Lift `some(x)` through ordinary stages while preserving explicit Option-aware call sites.
            if (
                isinstance(stage_value, GeniaOptionSome)
                and not _callable_explicitly_handles_some(fn, len(base_args) + 1, callee_node)
            ):
                result = self.invoke_callable(
                    fn,
                    [*base_args, stage_value.value],
                    tail_position=tail_position,
                    callee_node=callee_node,
                )
                if isinstance(result, (GeniaOptionSome, GeniaOptionNone)):
                    return result
                return GeniaOptionSome(result)
            return self.invoke_callable(
                fn,
                [*base_args, stage_value],
                tail_position=tail_position,
                callee_node=callee_node,
            )

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

            return invoke_with_pipeline_option_lifting(fn, args, node.fn)

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
        return invoke_with_pipeline_option_lifting(fn_value, [], node)

    def invoke_callable(
        self,
        fn: Any,
        args: list[Any],
        *,
        tail_position: bool,
        callee_node: IrNode | None = None,
        skip_none_propagation: bool = False,
    ) -> Any:
        if not skip_none_propagation:
            first_none = next((arg for arg in args if is_none(arg)), None)
            if first_none is not None and not _callable_explicitly_handles_none(fn, len(args), callee_node):
                return first_none

        if isinstance(fn, GeniaFunctionGroup):
            if isinstance(callee_node, IrVar) and len(args) == 2 and isinstance(args[1], GeniaFlow):
                if callee_node.name == "map":
                    mapper = args[0]
                    source = args[1]

                    def iterator() -> Iterable[Any]:
                        items = source.consume()
                        try:
                            for item in items:
                                yield self.invoke_callable(mapper, [item], tail_position=False)
                        finally:
                            if source.close_on_early_termination:
                                close = getattr(items, "close", None)
                                if callable(close):
                                    close()

                    return GeniaFlow(iterator, label="map", close_on_early_termination=source.close_on_early_termination)
                if callee_node.name == "filter":
                    predicate = args[0]
                    source = args[1]

                    def iterator() -> Iterable[Any]:
                        items = source.consume()
                        try:
                            for item in items:
                                if truthy(self.invoke_callable(predicate, [item], tail_position=False)):
                                    yield item
                        finally:
                            if source.close_on_early_termination:
                                close = getattr(items, "close", None)
                                if callable(close):
                                    close()

                    return GeniaFlow(
                        iterator,
                        label="filter",
                        close_on_early_termination=source.close_on_early_termination,
                    )
                if callee_node.name == "take":
                    count = args[0]
                    source = args[1]
                    if not isinstance(count, int) or isinstance(count, bool):
                        raise TypeError("take expected an integer count as first argument")

                    def iterator() -> Iterable[Any]:
                        if count <= 0:
                            return
                        remaining = count
                        items = source.consume()
                        upstream = iter(items)
                        try:
                            while remaining > 0:
                                try:
                                    item = next(upstream)
                                except StopIteration:
                                    return
                                yield item
                                remaining -= 1
                        finally:
                            if source.close_on_early_termination:
                                close = getattr(items, "close", None)
                                if callable(close):
                                    close()

                    return GeniaFlow(iterator, label="take", close_on_early_termination=source.close_on_early_termination)
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
            return _normalize_absence(target(*args))

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

        if not callable(fn):
            raise TypeError(f"pipeline stage expected a callable value, received {_runtime_type_name(fn)}")

        if tail_position:
            return TailCall(fn, tuple(args))
        return _normalize_absence(fn(*args))

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
            return make_none(reason, context)
        if isinstance(node, IrOptionSome):
            return GeniaOptionSome(self.eval(node.value))
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
            if is_none(value):
                return value
            if node.op == "MINUS":
                try:
                    return -value
                except TypeError:
                    return make_none("type-error", GeniaMap().put("source", "unary-minus").put("received", _runtime_type_name(value)))
            if node.op == "BANG":
                return not truthy(value)
            raise RuntimeError(f"Unknown unary operator {node.op}")
        if isinstance(node, IrPipeline):
            return self.eval_pipeline(node, tail_position=False)
        if isinstance(node, IrBinary):
            return self.eval_binary(node)
        if isinstance(node, IrCall):
            return self.eval_call(node, tail_position=False)

        if isinstance(node, IrBlock):
            local = Env(self.env)
            result = OPTION_NONE
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

            fn.__genia_body__ = body
            return fn

        if isinstance(node, IrAssign):
            value = self.eval(node.expr)
            self.env.assign(node.name, value)
            if node.annotations:
                metadata = self.eval_annotations(node.annotations)
                self.env.merge_binding_metadata(node.name, metadata)
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
            if node.annotations:
                metadata = self.eval_annotations(node.annotations)
                self.env.merge_binding_metadata(node.name, metadata)
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
        if node.op in {"EQEQ", "NE"}:
            right = self.eval(node.right)
            match node.op:
                case "EQEQ":
                    return left == right
                case "NE":
                    return left != right
        if is_none(left):
            return left
        if node.op == "AND":
            right = self.eval(node.right)
            if is_none(right):
                return right
            return left and right
        if node.op == "OR":
            right = self.eval(node.right)
            if is_none(right):
                return right
            return left or right
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
        if is_none(right):
            return right
        match node.op:
            case "PLUS":
                try:
                    return left + right
                except TypeError:
                    return make_none("type-error", GeniaMap().put("source", "+").put("left", _runtime_type_name(left)).put("right", _runtime_type_name(right)))
            case "MINUS":
                try:
                    return left - right
                except TypeError:
                    return make_none("type-error", GeniaMap().put("source", "-").put("left", _runtime_type_name(left)).put("right", _runtime_type_name(right)))
            case "STAR":
                try:
                    return left * right
                except TypeError:
                    return make_none("type-error", GeniaMap().put("source", "*").put("left", _runtime_type_name(left)).put("right", _runtime_type_name(right)))
            case "SLASH":
                try:
                    return left / right
                except TypeError:
                    return make_none("type-error", GeniaMap().put("source", "/").put("left", _runtime_type_name(left)).put("right", _runtime_type_name(right)))
            case "PERCENT":
                try:
                    return left % right
                except TypeError:
                    return make_none("type-error", GeniaMap().put("source", "%").put("left", _runtime_type_name(left)).put("right", _runtime_type_name(right)))
            case "LT":
                try:
                    return left < right
                except TypeError:
                    return make_none("type-error", GeniaMap().put("source", "<").put("left", _runtime_type_name(left)).put("right", _runtime_type_name(right)))
            case "LE":
                try:
                    return left <= right
                except TypeError:
                    return make_none("type-error", GeniaMap().put("source", "<=").put("left", _runtime_type_name(left)).put("right", _runtime_type_name(right)))
            case "GT":
                try:
                    return left > right
                except TypeError:
                    return make_none("type-error", GeniaMap().put("source", ">").put("left", _runtime_type_name(left)).put("right", _runtime_type_name(right)))
            case "GE":
                try:
                    return left >= right
                except TypeError:
                    return make_none("type-error", GeniaMap().put("source", ">=").put("left", _runtime_type_name(left)).put("right", _runtime_type_name(right)))
            case _:
                raise RuntimeError(f"Unknown binary operator {node.op}")


def truthy(value: Any) -> bool:
    if is_none(value):
        return False
    return bool(value)


def _runtime_type_name(value: Any) -> str:
    if value is None:
        return "none"
    if isinstance(value, GeniaOptionNone):
        return "none"
    if isinstance(value, GeniaOptionSome):
        return f"some({_runtime_type_name(value.value)})"
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
    if isinstance(value, GeniaRng):
        return "rng"
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
    if isinstance(value, GeniaPythonHandle):
        return "python_handle"
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


def _annotation_metadata_error(name: str, value: Any, expected: str) -> TypeError:
    return TypeError(f"@{name} annotation expected {expected}, received {_runtime_type_name(value)}")


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
    stdin_keys_provider: Optional[Callable[[], Iterable[str]]] = None,
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

    def _enable_virtual_terminal_processing_if_needed(sink: GeniaOutputSink) -> None:
        if os.name != "nt":
            return
        stream = getattr(sink, "_stream", None)
        if stream is None or not hasattr(stream, "isatty") or not stream.isatty():
            return
        fileno_fn = getattr(stream, "fileno", None)
        if not callable(fileno_fn):
            return
        try:
            fileno = fileno_fn()
        except (OSError, io.UnsupportedOperation, ValueError):
            return
        std_handle_map = {1: -11, 2: -12}
        std_handle = std_handle_map.get(fileno)
        if std_handle is None:
            return
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(std_handle)
            if handle in (0, -1):
                return
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)) == 0:
                return
            enable_virtual_terminal_processing = 0x0004
            if mode.value & enable_virtual_terminal_processing:
                return
            kernel32.SetConsoleMode(handle, mode.value | enable_virtual_terminal_processing)
        except Exception:
            return

    def _ensure_positive_int(value: Any, name: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} expected an integer, received {_runtime_type_name(value)}")
        if value < 1:
            raise ValueError(f"{name} expected a positive integer")
        return value

    def clear_screen_fn() -> None:
        _enable_virtual_terminal_processing_if_needed(stdout_sink)
        stdout_sink.write_text("\x1b[2J\x1b[H")
        stdout_sink.flush()
        return None

    def move_cursor_fn(x_value: Any, y_value: Any) -> None:
        x = _ensure_positive_int(x_value, "move_cursor")
        y = _ensure_positive_int(y_value, "move_cursor")
        _enable_virtual_terminal_processing_if_needed(stdout_sink)
        stdout_sink.write_text(f"\x1b[{y};{x}H")
        return None

    def render_grid_fn(grid_value: Any) -> Any:
        if not isinstance(grid_value, list):
            raise TypeError(f"render_grid expected a list, received {_runtime_type_name(grid_value)}")
        lines: list[str] = []
        for index, row in enumerate(grid_value):
            if isinstance(row, str):
                lines.append(row)
                continue
            if isinstance(row, list):
                lines.append("".join(format_display(cell) for cell in row))
                continue
            raise TypeError(
                "render_grid expected each row to be a string or list, "
                f"row {index} was {_runtime_type_name(row)}"
            )
        stdout_sink.write_text("\n".join(lines))
        return grid_value

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
                if _is_nil_none(pattern.tail):
                    return IrPatRest(None)
                rest_name = _syntax_pair_nth(pattern, 1, "_meta_match_pattern_env")
                if not isinstance(rest_name, GeniaSymbol):
                    raise TypeError("metacircular rest patterns require a symbol name")
                if not _is_nil_none(pattern.tail.tail):
                    raise TypeError("metacircular rest patterns accept at most one symbol name")
                return IrPatRest(rest_name.name)
            if _syntax_tagged_list(pattern, symbol("tuple")):
                items: list[IrPattern] = []
                current = pattern.tail
                while not _is_nil_none(current):
                    if not isinstance(current, GeniaPair):
                        raise TypeError("metacircular tuple patterns must be proper lists")
                    items.append(_meta_lower_quoted_pattern(current.head))
                    current = current.tail
                return IrPatTuple(items)
            if _syntax_tagged_list(pattern, symbol("glob")):
                glob_text = _syntax_pair_nth(pattern, 1, "_meta_match_pattern_env")
                if not isinstance(glob_text, str):
                    raise TypeError("metacircular glob patterns require a string")
                if not _is_nil_none(pattern.tail.tail):
                    raise TypeError("metacircular glob patterns accept exactly one string")
                return IrPatGlob(compile_glob_pattern(glob_text))
            if _syntax_tagged_list(pattern, symbol("some")):
                if _is_nil_none(pattern.tail) or not isinstance(pattern.tail, GeniaPair):
                    raise TypeError("metacircular some patterns require an inner pattern")
                if not _is_nil_none(pattern.tail.tail):
                    raise TypeError("metacircular some patterns accept exactly one inner pattern")
                return IrPatSome(_meta_lower_quoted_pattern(pattern.tail.head))
            items: list[IrPattern] = []
            current = pattern
            while not _is_nil_none(current):
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

    def _ensure_port_int(value: Any, name: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} expected an integer, received {_runtime_type_name(value)}")
        if value < 0 or value > 65535:
            raise ValueError(f"{name} expected an integer in [0, 65535]")
        return value

    def _ensure_optional_request_limit(value: Any, name: str) -> int | None:
        if value is _UNSET or value is None or _is_nil_none(value):
            return None
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} expected a positive integer, received {_runtime_type_name(value)}")
        if value < 1:
            raise ValueError(f"{name} expected a positive integer")
        return value

    def _ensure_zip_entry(value: Any, name: str) -> GeniaZipEntry:
        if not isinstance(value, GeniaZipEntry):
            raise TypeError(f"{name} expected a zip entry, received {_runtime_type_name(value)}")
        return value

    def _json_from_runtime(value: Any) -> Any:
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if is_none(value):
            return None
        if isinstance(value, list):
            return [_json_from_runtime(item) for item in value]
        if isinstance(value, GeniaMap):
            data: dict[str, Any] = {}
            for _, (original_key, original_value) in value._entries.items():
                if not isinstance(original_key, str):
                    raise TypeError("json_stringify expected object keys to be strings")
                data[original_key] = _json_from_runtime(original_value)
            return data
        raise TypeError(f"json_stringify expected a JSON-compatible value, got {type(value).__name__}")

    def _json_to_runtime(value: Any) -> Any:
        if value is None:
            return OPTION_NONE
        if isinstance(value, (bool, int, float, str)):
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
            return make_none("not-found", GeniaMap().put("needle", safe_needle))
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
            return make_none(
                "parse-error",
                GeniaMap()
                .put("source", "parse_int")
                .put("expected", "integer_string")
                .put("received", text)
                .put("base", base),
            )
        try:
            return GeniaOptionSome(int(stripped, base))
        except ValueError:
            return make_none(
                "parse-error",
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

    def stdin_keys_iterable() -> Iterable[str]:
        if stdin_keys_provider is not None:
            return stdin_keys_provider()

        def host_stdin_keys() -> Iterable[str]:
            if os.name == "nt":
                try:
                    import msvcrt
                except ImportError:
                    pass
                else:
                    while True:
                        key = msvcrt.getwch()
                        if key in ("\x00", "\xe0"):
                            key += msvcrt.getwch()
                        if key == "\r":
                            yield "\n"
                        else:
                            yield key
                    return

            stdin_stream = sys.stdin
            if not getattr(stdin_stream, "isatty", lambda: False)():
                while True:
                    chunk = stdin_stream.read(1)
                    if chunk == "":
                        return
                    yield chunk
                return

            try:
                import termios
                import tty
            except ImportError:
                while True:
                    chunk = stdin_stream.read(1)
                    if chunk == "":
                        return
                    yield chunk
                return

            try:
                fd = stdin_stream.fileno()
            except (AttributeError, io.UnsupportedOperation):
                while True:
                    chunk = stdin_stream.read(1)
                    if chunk == "":
                        return
                    yield chunk
                return

            import codecs

            previous_attrs = termios.tcgetattr(fd)
            decoder = codecs.getincrementaldecoder("utf-8")()
            try:
                tty.setraw(fd)
                while True:
                    raw_chunk = os.read(fd, 1)
                    if raw_chunk == b"":
                        remainder = decoder.decode(b"", final=True)
                        if remainder != "":
                            for ch in remainder:
                                yield ch
                        return
                    text = decoder.decode(raw_chunk, final=False)
                    if text != "":
                        for ch in text:
                            yield ch
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, previous_attrs)

        return host_stdin_keys()

    stdin_keys_flow = GeniaFlow(stdin_keys_iterable, label="stdin_keys", close_on_early_termination=True)

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

    def _maybe_close_iterable(iterable: Any) -> None:
        close = getattr(iterable, "close", None)
        if callable(close):
            close()

    class _FlowTeeState:
        def __init__(self, upstream: GeniaFlow):
            self._upstream = upstream
            self._iterator: Iterator[Any] | None = None
            self._upstream_done = False
            self._buffers = [deque(), deque()]
            self._closed_branches: set[int] = set()

        def _ensure_iterator(self) -> Iterator[Any] | None:
            if self._upstream_done:
                return None
            if self._iterator is None:
                self._iterator = iter(self._upstream.consume())
            return self._iterator

        def _fill_once(self) -> bool:
            iterator = self._ensure_iterator()
            if iterator is None:
                return False
            try:
                item = next(iterator)
            except StopIteration:
                self._upstream_done = True
                return False

            self._buffers[0].append(item)
            self._buffers[1].append(item)
            return True

        def next_item(self, branch_index: int) -> Any:
            while not self._buffers[branch_index]:
                if not self._fill_once():
                    raise StopIteration
            return self._buffers[branch_index].popleft()

        def close_branch(self, branch_index: int) -> None:
            self._closed_branches.add(branch_index)
            if len(self._closed_branches) != 2:
                return
            if self._iterator is not None and self._upstream.close_on_early_termination:
                _maybe_close_iterable(self._iterator)

    def lines_fn(source: Any) -> GeniaFlow:
        if isinstance(source, GeniaFlow):
            upstream = _ensure_flow(source, "lines")

            def iterator() -> Iterable[Any]:
                items = upstream.consume()
                try:
                    for item in items:
                        if not isinstance(item, str):
                            raise TypeError("lines expected string input items")
                        yield item
                finally:
                    if upstream.close_on_early_termination:
                        _maybe_close_iterable(items)

            return GeniaFlow(iterator, label="lines", close_on_early_termination=upstream.close_on_early_termination)

        if isinstance(source, GeniaStdinSource):
            return GeniaFlow(source.iter_lines, label="lines", close_on_early_termination=False)

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

    def tick_fn(*args: Any) -> GeniaFlow:
        if len(args) > 1:
            raise TypeError(f"tick expected 0 or 1 args, got {len(args)}")

        if len(args) == 0:
            limit = None
        else:
            limit_value = args[0]
            if not isinstance(limit_value, int) or isinstance(limit_value, bool):
                raise TypeError("tick expected an integer count")
            limit = limit_value

        def iterator() -> Iterable[int]:
            tick = 0
            if limit is None:
                while True:
                    yield tick
                    tick += 1
                return

            while tick < limit:
                yield tick
                tick += 1

        return GeniaFlow(iterator, label="tick")

    def tee_fn(source: Any) -> tuple[GeniaFlow, GeniaFlow]:
        upstream = _ensure_flow(source, "tee")
        state = _FlowTeeState(upstream)

        def branch_flow(branch_index: int) -> GeniaFlow:
            def iterator() -> Iterable[Any]:
                try:
                    while True:
                        try:
                            yield state.next_item(branch_index)
                        except StopIteration:
                            return
                finally:
                    state.close_branch(branch_index)

            return GeniaFlow(iterator, label=f"tee/{branch_index + 1}")

        return (branch_flow(0), branch_flow(1))

    def _split_flow_pair(value: Any, name: str) -> tuple[GeniaFlow, GeniaFlow]:
        if isinstance(value, (tuple, list)) and len(value) == 2:
            left = _ensure_flow(value[0], name)
            right = _ensure_flow(value[1], name)
            return left, right
        raise TypeError(f"{name} expected (flow1, flow2) pair or two flow arguments")

    def merge_flow_fn(*args: Any) -> GeniaFlow:
        if len(args) == 1:
            first_flow, second_flow = _split_flow_pair(args[0], "merge")
        elif len(args) == 2:
            first_flow = _ensure_flow(args[0], "merge")
            second_flow = _ensure_flow(args[1], "merge")
        else:
            raise TypeError(f"merge expected 1 or 2 args, got {len(args)}")

        def iterator() -> Iterable[Any]:
            first_items = iter(first_flow.consume())
            second_items: Iterator[Any] | None = None
            try:
                for item in first_items:
                    yield item

                second_items = iter(second_flow.consume())
                for item in second_items:
                    yield item
            finally:
                if first_flow.close_on_early_termination:
                    _maybe_close_iterable(first_items)
                if second_items is not None and second_flow.close_on_early_termination:
                    _maybe_close_iterable(second_items)

        return GeniaFlow(
            iterator,
            label="merge",
            close_on_early_termination=(
                first_flow.close_on_early_termination or second_flow.close_on_early_termination
            ),
        )

    def zip_flow_fn(*args: Any) -> GeniaFlow:
        if len(args) == 1:
            first_flow, second_flow = _split_flow_pair(args[0], "zip")
        elif len(args) == 2:
            first_flow = _ensure_flow(args[0], "zip")
            second_flow = _ensure_flow(args[1], "zip")
        else:
            raise TypeError(f"zip expected 1 or 2 args, got {len(args)}")

        def iterator() -> Iterable[Any]:
            first_items = iter(first_flow.consume())
            second_items = iter(second_flow.consume())
            try:
                while True:
                    try:
                        left = next(first_items)
                        right = next(second_items)
                    except StopIteration:
                        return
                    yield [left, right]
            finally:
                if first_flow.close_on_early_termination:
                    _maybe_close_iterable(first_items)
                if second_flow.close_on_early_termination:
                    _maybe_close_iterable(second_items)

        return GeniaFlow(
            iterator,
            label="zip",
            close_on_early_termination=(
                first_flow.close_on_early_termination or second_flow.close_on_early_termination
            ),
        )

    def map_flow_fn(fn_value: Any, source: Any) -> Any:
        mapper = _ensure_callable(fn_value, "map")
        if isinstance(source, GeniaFlow):
            upstream = source

            def iterator() -> Iterable[Any]:
                items = upstream.consume()
                try:
                    for item in items:
                        yield mapper(item)
                finally:
                    if upstream.close_on_early_termination:
                        _maybe_close_iterable(items)

            return GeniaFlow(iterator, label="map", close_on_early_termination=upstream.close_on_early_termination)
        if not isinstance(source, list):
            raise TypeError("map expected a flow or list")
        return [mapper(item) for item in source]

    def filter_flow_fn(predicate_value: Any, source: Any) -> Any:
        predicate = _ensure_callable(predicate_value, "filter")
        if isinstance(source, GeniaFlow):
            upstream = source

            def iterator() -> Iterable[Any]:
                items = upstream.consume()
                try:
                    for item in items:
                        if truthy(predicate(item)):
                            yield item
                finally:
                    if upstream.close_on_early_termination:
                        _maybe_close_iterable(items)

            return GeniaFlow(iterator, label="filter", close_on_early_termination=upstream.close_on_early_termination)
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
            try:
                while remaining > 0:
                    try:
                        item = next(items)
                    except StopIteration:
                        return
                    yield item
                    remaining -= 1
            finally:
                if upstream.close_on_early_termination:
                    _maybe_close_iterable(items)

        return GeniaFlow(iterator, label="take", close_on_early_termination=upstream.close_on_early_termination)

    def head_fn(*args: Any) -> GeniaFlow:
        if len(args) == 1:
            return take_fn(1, args[0])
        if len(args) == 2:
            return take_fn(args[0], args[1])
        raise TypeError(f"head expected 1 or 2 args, got {len(args)}")

    def scan_fn(step_value: Any, initial_state: Any, source: Any) -> GeniaFlow:
        step = _ensure_callable(step_value, "scan")
        upstream = _ensure_flow(source, "scan")

        def iterator() -> Iterable[Any]:
            state = initial_state
            items = upstream.consume()
            try:
                for item in items:
                    result = _invoke_from_builtin(step, [state, item])
                    if not isinstance(result, list) or len(result) != 2:
                        raise TypeError(
                            "scan expected step(state, item) to return [next_state, output], "
                            f"received {_runtime_type_name(result)}"
                        )
                    state = result[0]
                    yield result[1]
            finally:
                if upstream.close_on_early_termination:
                    _maybe_close_iterable(items)

        return GeniaFlow(iterator, label="scan", close_on_early_termination=upstream.close_on_early_termination)

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
            items = upstream.consume()
            try:
                for item in items:
                    result = _invoke_from_builtin(step, [item, current_ctx])
                    if not isinstance(result, GeniaMap):
                        raise RuntimeError("_rules_kernel expected a map result")

                    emitted = result.get("emit", [])
                    if not isinstance(emitted, list):
                        raise RuntimeError("_rules_kernel expected emit to be a list")

                    current_ctx = result.get("ctx", current_ctx)

                    for value in emitted:
                        yield value
            finally:
                if upstream.close_on_early_termination:
                    _maybe_close_iterable(items)

        return GeniaFlow(iterator, label="rules", close_on_early_termination=upstream.close_on_early_termination)

    def keep_some_else_fn(stage_value: Any, dead_value: Any, source: Any) -> GeniaFlow:
        stage = _ensure_callable(stage_value, "keep_some_else")
        dead_handler = _ensure_callable(dead_value, "keep_some_else")
        upstream = _ensure_flow(source, "keep_some_else")

        def iterator() -> Iterable[Any]:
            items = upstream.consume()
            try:
                for item in items:
                    result = _invoke_from_builtin(stage, [item])
                    if isinstance(result, GeniaOptionSome):
                        yield result.value
                        continue
                    if isinstance(result, GeniaOptionNone):
                        _invoke_from_builtin(dead_handler, [item])
                        continue
                    raise TypeError(
                        "keep_some_else expected stage(item) to return some(...) or none(...), "
                        f"received {_runtime_type_name(result)}"
                    )
            finally:
                if upstream.close_on_early_termination:
                    _maybe_close_iterable(items)

        return GeniaFlow(iterator, label="keep_some_else", close_on_early_termination=upstream.close_on_early_termination)

    def keep_some_fn(source: Any) -> GeniaFlow:
        upstream = _ensure_flow(source, "keep_some")

        def iterator() -> Iterable[Any]:
            items = upstream.consume()
            try:
                for item in items:
                    if isinstance(item, GeniaOptionSome):
                        yield item.value
                        continue
                    if isinstance(item, GeniaOptionNone):
                        continue
                    raise TypeError(
                        "keep_some expected items to be some(...) or none(...), "
                        f"received {_runtime_type_name(item)}"
                    )
            finally:
                if upstream.close_on_early_termination:
                    _maybe_close_iterable(items)

        return GeniaFlow(iterator, label="keep_some", close_on_early_termination=upstream.close_on_early_termination)

    def each_fn(fn_value: Any, source: Any) -> GeniaFlow:
        effect = _ensure_callable(fn_value, "each")
        upstream = _ensure_flow(source, "each")

        def iterator() -> Iterable[Any]:
            items = upstream.consume()
            try:
                for item in items:
                    effect(item)
                    yield item
            finally:
                if upstream.close_on_early_termination:
                    _maybe_close_iterable(items)

        return GeniaFlow(iterator, label="each", close_on_early_termination=upstream.close_on_early_termination)

    def collect_fn(source: Any) -> list[Any]:
        flow = _ensure_flow(source, "collect")
        items = flow.consume()
        try:
            return list(items)
        finally:
            if flow.close_on_early_termination:
                _maybe_close_iterable(items)

    def run_fn(source: Any) -> None:
        flow = _ensure_flow(source, "run")
        items = flow.consume()
        try:
            for _ in items:
                pass
        finally:
            if flow.close_on_early_termination:
                _maybe_close_iterable(items)
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

    def _metadata_doc(metadata: GeniaMap) -> str | None:
        doc_value = metadata.get("doc")
        return doc_value if isinstance(doc_value, str) else None

    def _metadata_summary_lines(metadata: GeniaMap) -> list[str]:
        labels = (
            ("category", "Category"),
            ("since", "Since"),
            ("deprecated", "Deprecated"),
        )
        lines: list[str] = []
        for key, label in labels:
            value = metadata.get(key)
            if isinstance(value, str):
                lines.append(f"{label}: {value}")
        return lines

    def _describe_function_group(group: GeniaFunctionGroup) -> str:
        shapes = _format_function_shapes(group)
        lines = [f"{group.name}/{shapes}"]
        span_text = _format_span(_group_span(group))
        if span_text is not None:
            lines.append(f"Defined at {span_text}")
        lines.append("")
        metadata_doc = _metadata_doc(group.metadata)
        effective_doc = group.docstring
        if effective_doc is None and metadata_doc is not None:
            effective_doc = metadata_doc
        if effective_doc is not None:
            lines.append(render_markdown_docstring(effective_doc))
        else:
            lines.append("No documentation available.")
        metadata_lines = _metadata_summary_lines(group.metadata)
        if metadata_lines:
            lines.append("")
            lines.extend(metadata_lines)
        return "\n".join(lines)

    def _describe_runtime_name(name: str, value: Any, metadata: GeniaMap | None = None) -> str:
        kind = "host-backed runtime function" if callable(value) else "named value"
        lines = [
            name,
            "",
            f"{name} is a {kind} in this phase.",
        ]
        if metadata is not None:
            doc_text = _metadata_doc(metadata)
            if doc_text is not None:
                lines.extend(["", render_markdown_docstring(doc_text)])
            metadata_lines = _metadata_summary_lines(metadata)
            if metadata_lines:
                lines.extend(["", *metadata_lines])
        lines.extend(
            [
                "",
                "Detailed docstrings are attached to public Genia/prelude functions instead of raw host bridge names.",
                'Use `help()` for the surface overview and `help("name")` for documented public helpers such as `get`, `map_put`, `ref_update`, `spawn`, `write`, `parse_int`, `match_branches`, `eval`, and `cell_send`.',
            ]
        )
        return "\n".join(lines)

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
            (
                "Flow",
                ("std/prelude/flow.genia",),
                ("lines", "scan", "keep_some_else", "rules", "each", "collect", "run"),
            ),
            (
                "Lists / fns / math",
                ("std/prelude/list.genia", "std/prelude/fn.genia", "std/prelude/math.genia"),
                ("list", "first", "nth", "map", "filter", "reduce", "apply", "compose", "inspect", "trace", "tap", "sum"),
            ),
            (
                "Option / string",
                ("std/prelude/option.genia", "std/prelude/string.genia"),
                (
                    "some",
                    "get",
                    "unwrap_or",
                    "absence_reason",
                    "absence_meta",
                    "parse_int",
                    "split",
                    "trim",
                    "join",
                    "map_some",
                    "then_get",
                ),
            ),
            ("Randomness", ("std/prelude/random.genia",), ("rng", "rand", "rand_int")),
            (
                "JSON",
                ("std/prelude/json.genia",),
                ("json_parse", "json_stringify", "json_pretty"),
            ),
            (
                "Web",
                ("std/prelude/web.genia",),
                ("serve_http", "get", "post", "route_request", "response", "json", "text", "ok", "ok_text", "bad_request", "not_found"),
            ),
            (
                "File / zip",
                ("std/prelude/file.genia",),
                ("read_file", "write_file", "zip_read", "zip_write"),
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
                "  `argv()` and values such as `stdin`, `stdin_keys`, `stdout`, `stderr`, `print`, `log`, `input`, `none`, `force`,",
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
                singleton = GeniaFunctionGroup(
                    target.name,
                    functions={target.arity: target},
                    docstring=target.docstring,
                    metadata=env.get_metadata(target.name),
                )
                _emit_help(_describe_function_group(singleton))
                return
            if original_name is not None:
                _emit_help(_describe_runtime_name(original_name, target, env.get_metadata(original_name)))
                return
            raise TypeError("help expected a function name or named function")

        _emit_help(_describe_help_overview())

    def doc_fn(*args: Any) -> Any:
        if len(args) != 1:
            raise TypeError(f"doc expected 1 arg, got {len(args)}")
        name = args[0]
        if not isinstance(name, str):
            raise TypeError(f"doc expected a string name, received {_runtime_type_name(name)}")
        try:
            env.get(name)
        except NameError:
            if env.try_autoload(name, 0):
                env.get(name)
            else:
                return make_none("missing-doc", GeniaMap().put("name", name))
        metadata = env.get_metadata(name)
        doc_text = _metadata_doc(metadata)
        if doc_text is not None:
            return doc_text
        target = env.get(name)
        if isinstance(target, GeniaFunctionGroup) and target.docstring is not None:
            return target.docstring
        return make_none("missing-doc", GeniaMap().put("name", name))

    def meta_fn(*args: Any) -> GeniaMap:
        if len(args) != 1:
            raise TypeError(f"meta expected 1 arg, got {len(args)}")
        name = args[0]
        if not isinstance(name, str):
            raise TypeError(f"meta expected a string name, received {_runtime_type_name(name)}")
        try:
            env.get(name)
        except NameError:
            if env.try_autoload(name, 0):
                env.get(name)
            else:
                raise
        return env.get_metadata(name)

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
        if _is_nil_none(value) or value is None:
            return OPTION_NONE
        if not isinstance(value, GeniaPair):
            raise TypeError("cdr expected a pair")
        return value.tail

    def pair_fn(value: Any) -> bool:
        return isinstance(value, GeniaPair)

    def null_fn(value: Any) -> bool:
        return value is None or _is_nil_none(value)

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

    def cell_stop_fn(cell_value: Any) -> None:
        cell = _ensure_cell(cell_value, "cell_stop")
        cell.stop()
        return None

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

    _ACTOR_EFFECT_ERROR = (
        'actor handler must return ["ok", new_state], '
        '["reply", new_state, response], or ["stop", reason, new_state], '
        "got: {value}"
    )

    def actor_validate_effect_fn(result: Any, cell: Any) -> Any:
        if isinstance(result, list):
            if len(result) == 2 and result[0] == "ok":
                return result[1]
            if len(result) == 3 and result[0] == "reply":
                return result[1]  # discard response for fire-and-forget
            if len(result) == 3 and result[0] == "stop":
                _stage_cell_action("cell_stop", cell, None)
                return result[2]
        raise TypeError(
            _ACTOR_EFFECT_ERROR.format(value=format_debug(result))
        )

    def actor_call_update_fn(handler: Any, msg: Any, reply_ref: Any, state: Any, cell: Any) -> Any:
        if not isinstance(reply_ref, GeniaRef):
            raise TypeError("_actor_call_update expected a ref for reply")
        try:
            ctx = GeniaMap({"reply_to": reply_ref})
            result = handler(state, msg, ctx)
            if isinstance(result, list):
                if len(result) == 3 and result[0] == "reply":
                    reply_ref.set(result[2])
                    return result[1]
                if len(result) == 2 and result[0] == "ok":
                    reply_ref.set(result[1])
                    return result[1]
                if len(result) == 3 and result[0] == "stop":
                    reply_ref.set(make_none("actor-stopped"))
                    _stage_cell_action("cell_stop", cell, None)
                    return result[2]
            raise TypeError(
                _ACTOR_EFFECT_ERROR.format(value=format_debug(result))
            )
        except BaseException:
            if not reply_ref.is_set():
                reply_ref.set(make_none("actor-error"))
            raise

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
        if spec is None or _is_nil_none(spec):
            flags = GeniaMap()
            options = GeniaMap()
            aliases = GeniaMap()
        else:
            if not isinstance(spec, GeniaMap):
                raise TypeError("cli_parse expected spec to be a map")

            flags_raw = spec.get("flags", None)
            options_raw = spec.get("options", None)
            aliases_raw = spec.get("aliases", None)

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
        return bool(genia_map.get(key, False))

    def cli_option_fn(opts: Any, name: Any) -> Any:
        genia_map = _ensure_map(opts, "cli_option")
        key = _ensure_string(name, "cli_option")
        return genia_map.get(key)

    def cli_option_or_fn(opts: Any, name: Any, default: Any) -> Any:
        genia_map = _ensure_map(opts, "cli_option_or")
        key = _ensure_string(name, "cli_option_or")
        value = genia_map.get(key, _UNSET)
        return default if value is _UNSET else value

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
        raise TypeError(f"unwrap_or expected an option value, received {_runtime_type_name(opt)}")

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
        raise TypeError(f"or_else expected an option value, received {_runtime_type_name(opt)}")

    def absence_reason_fn(value: Any) -> Any:
        if not isinstance(value, GeniaOptionNone):
            raise TypeError("absence_reason expected a none value")
        return GeniaOptionSome(value.reason)

    def absence_context_fn(value: Any) -> Any:
        if not isinstance(value, GeniaOptionNone):
            raise TypeError("absence_context expected a none value")
        if value.context is None:
            return OPTION_NONE
        return GeniaOptionSome(value.context)

    def absence_meta_fn(value: Any) -> Any:
        if not isinstance(value, GeniaOptionNone):
            raise TypeError("absence_meta expected a none value")
        return GeniaOptionSome(value.meta)

    def _invoke_from_builtin(proc: Any, args: list[Any]) -> Any:
        return Evaluator(env, env.debug_hooks, env.debug_mode).invoke_callable(
            proc,
            args,
            tail_position=False,
            callee_node=None,
        )

    def _invoke_raw_from_builtin(proc: Any, args: list[Any]) -> Any:
        """Like _invoke_from_builtin but skips none-propagation.
        Used by host-backed HOFs (map/filter/reduce) processing list elements."""
        return Evaluator(env, env.debug_hooks, env.debug_mode).invoke_callable(
            proc,
            args,
            tail_position=False,
            callee_node=None,
            skip_none_propagation=True,
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
            return make_none("missing-key", context)
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
        raise TypeError(f"map_some expected an option value, received {_runtime_type_name(opt)}")

    def flat_map_some_fn(proc: Any, opt: Any) -> Any:
        if isinstance(opt, GeniaOptionSome):
            result = _invoke_from_builtin(proc, [opt.value])
            if isinstance(result, (GeniaOptionSome, GeniaOptionNone)):
                return result
            raise TypeError(
                "flat_map_some expected function to return an option value, "
                f"received {_runtime_type_name(result)}"
            )
        if isinstance(opt, GeniaOptionNone):
            return opt
        raise TypeError(f"flat_map_some expected an option value, received {_runtime_type_name(opt)}")

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
                return make_none("empty-list")
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
                return make_none("index-out-of-bounds", context)
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
                return make_none("not-found", GeniaMap().put("needle", safe_needle))
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
        raise TypeError(f"or_else_with expected an option value, received {_runtime_type_name(opt)}")

    def reduce_fn(f: Any, acc: Any, xs: Any) -> Any:
        """Host-backed reduce that calls the callback via invoke_callable with
        skip_none_propagation, so that list elements which are none(...)
        are passed to the callback rather than short-circuiting it."""
        if not isinstance(xs, list):
            raise TypeError(f"reduce expected a list as third argument, received {_runtime_type_name(xs)}")
        result = acc
        for x in xs:
            result = _invoke_raw_from_builtin(f, [result, x])
        return result

    def map_fn(f: Any, xs: Any) -> Any:
        """Host-backed map that calls the callback via invoke_callable with
        skip_none_propagation, so that list elements which are none(...)
        are passed to the callback rather than short-circuiting it."""
        if not isinstance(xs, list):
            raise TypeError(f"map expected a list as second argument, received {_runtime_type_name(xs)}")
        return [_invoke_raw_from_builtin(f, [x]) for x in xs]

    def filter_fn(predicate: Any, xs: Any) -> Any:
        """Host-backed filter that calls the callback via invoke_callable with
        skip_none_propagation, so that list elements which are none(...)
        are passed to the callback rather than short-circuiting it."""
        if not isinstance(xs, list):
            raise TypeError(f"filter expected a list as second argument, received {_runtime_type_name(xs)}")
        return [x for x in xs if truthy(_invoke_raw_from_builtin(predicate, [x]))]

    def sum_fn(xs: Any) -> Any:
        if not isinstance(xs, list):
            raise TypeError(f"sum expected a list, received {_runtime_type_name(xs)}")
        total: int | float = 0
        for index, item in enumerate(xs, start=1):
            if not isinstance(item, (int, float)) or isinstance(item, bool):
                raise TypeError(
                    "sum expected a list of numbers; "
                    f"item {index} received {_runtime_type_name(item)}. "
                    "Use keep_some(...), keep_some_else(...), flat_map_some(...), or unwrap_or(...) before sum."
                )
            total += item
        return total

    for fn in (
        write_fn,
        writeln_fn,
        flush_fn,
        cli_spec_fn,
        some_fn,
        is_some_fn,
        is_none_fn,
        some_predicate_fn,
        none_predicate_fn,
        unwrap_or_fn,
        or_else_fn,
        or_else_with_fn,
        absence_reason_fn,
        absence_context_fn,
        absence_meta_fn,
        map_some_fn,
        flat_map_some_fn,
        cli_option_or_fn,
        map_put_fn,
        cons_fn,
        car_fn,
        cdr_fn,
        pair_fn,
        null_fn,
        meta_lookup_fn,
        meta_define_fn,
        meta_set_fn,
        meta_extend_fn,
        meta_host_apply_fn,
        meta_eval_error_fn,
        meta_match_pattern_env_fn,
        meta_match_error_fn,
        syntax_error_fn,
        syntax_self_evaluating_fn,
        syntax_symbol_expr_fn,
    ):
        _mark_handles_none(fn)
        _mark_handles_some(fn)

    def rand_fn(*args: Any) -> float:
        if len(args) != 0:
            raise TypeError(f"rand expected 0 args, got {len(args)}")
        return random.random()

    def rng_fn(seed: Any) -> GeniaRng:
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise TypeError("rng expected an integer seed")
        if seed < 0:
            raise ValueError("rng expected seed >= 0")
        return GeniaRng(seed % _RNG_MODULUS)

    def _ensure_rng(value: Any, name: str) -> GeniaRng:
        if not isinstance(value, GeniaRng):
            raise TypeError(f"{name} expected an rng state")
        return value

    def _ensure_rand_int_bound(n: Any) -> int:
        if not isinstance(n, int) or isinstance(n, bool):
            raise TypeError("rand_int expected a positive integer")
        if n <= 0:
            raise ValueError("rand_int expected n > 0")
        return n

    def _rng_next_state(state: int) -> int:
        return (_RNG_MULTIPLIER * state + _RNG_INCREMENT) % _RNG_MODULUS

    def seeded_rand_fn(rng_value: Any) -> list[Any]:
        rng_state = _ensure_rng(rng_value, "rand")
        next_state = _rng_next_state(rng_state.state)
        return [GeniaRng(next_state), next_state / _RNG_MODULUS]

    def rand_int_fn(n: Any) -> int:
        upper = _ensure_rand_int_bound(n)
        return random.randrange(upper)

    def seeded_rand_int_fn(rng_value: Any, n: Any) -> list[Any]:
        rng_state = _ensure_rng(rng_value, "rand_int")
        upper = _ensure_rand_int_bound(n)
        next_state = _rng_next_state(rng_state.state)
        return [GeniaRng(next_state), next_state % upper]

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
        if not isinstance(value, str):
            context = (
                GeniaMap()
                .put("source", "json_parse")
                .put("expected", "string")
                .put("received", _runtime_type_name(value))
            )
            return make_none("json-parse-error", context)

        text = value
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            context = (
                GeniaMap()
                .put("source", "json_parse")
                .put("message", exc.msg)
                .put("line", exc.lineno)
                .put("column", exc.colno)
            )
            return make_none("json-parse-error", context)
        return _json_to_runtime(parsed)

    def json_stringify_fn(value: Any) -> Any:
        try:
            return json.dumps(_json_from_runtime(value), indent=2, ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError) as exc:
            context = (
                GeniaMap()
                .put("source", "json_stringify")
                .put("message", str(exc))
                .put("received", _runtime_type_name(value))
            )
            return make_none("json-stringify-error", context)

    def _http_headers_to_runtime(headers: Iterable[tuple[str, str]]) -> GeniaMap:
        result = GeniaMap()
        for key, value in headers:
            result = result.put(key.lower(), value)
        return result

    def _http_query_to_runtime(query_text: str) -> GeniaMap:
        result = GeniaMap()
        for key, value in parse_qsl(query_text, keep_blank_values=True):
            result = result.put(key, value)
        return result

    def _http_request_map(request: BaseHTTPRequestHandler) -> GeniaMap:
        parsed_path = urlsplit(request.path)
        raw_body_bytes = b""
        content_length_text = request.headers.get("Content-Length")
        if content_length_text is not None:
            try:
                content_length = max(0, int(content_length_text))
            except ValueError:
                content_length = 0
            if content_length > 0:
                raw_body_bytes = request.rfile.read(content_length)

        raw_body = raw_body_bytes.decode("utf-8", errors="replace")
        content_type = request.headers.get("Content-Type", "")
        body: Any = raw_body
        if content_type.lower().startswith("application/json"):
            body = json_parse_fn(raw_body)

        client_host, client_port = request.client_address[:2]
        return (
            GeniaMap()
            .put("method", request.command.upper())
            .put("path", parsed_path.path or "/")
            .put("query", _http_query_to_runtime(parsed_path.query))
            .put("headers", _http_headers_to_runtime(request.headers.items()))
            .put("body", body)
            .put("raw_body", raw_body)
            .put("client", GeniaMap().put("host", client_host).put("port", client_port))
        )

    def _http_response_headers(value: Any) -> dict[str, str]:
        if value is None or _is_nil_none(value):
            return {}
        if not isinstance(value, GeniaMap):
            raise TypeError(
                "serve_http handler response.headers expected a map, "
                f"received {_runtime_type_name(value)}"
            )

        headers: dict[str, str] = {}
        for _, (raw_key, raw_value) in value._entries.items():
            if not isinstance(raw_key, str) or not isinstance(raw_value, str):
                raise TypeError("serve_http handler response.headers expected string keys and values")
            headers[raw_key] = raw_value
        return headers

    def _http_response_triplet(value: Any) -> tuple[int, dict[str, str], bytes]:
        if not isinstance(value, GeniaMap):
            raise TypeError(
                "serve_http handler must return a response map with status, headers, and body fields"
            )

        status = value.get("status", 200)
        if isinstance(status, bool) or not isinstance(status, int):
            raise TypeError(
                "serve_http handler response.status expected an integer, "
                f"received {_runtime_type_name(status)}"
            )
        if status < 100 or status > 999:
            raise ValueError("serve_http handler response.status expected an integer in [100, 999]")

        headers = _http_response_headers(value.get("headers", GeniaMap()))
        header_names = {name.lower() for name in headers}
        body = value.get("body", "")

        if body is None or is_none(body):
            payload = b""
            if "content-type" not in header_names:
                headers["content-type"] = "text/plain; charset=utf-8"
        elif isinstance(body, str):
            payload = body.encode("utf-8")
            if "content-type" not in header_names:
                headers["content-type"] = "text/plain; charset=utf-8"
        elif isinstance(body, GeniaBytes):
            payload = body.value
            if "content-type" not in header_names:
                headers["content-type"] = "application/octet-stream"
        else:
            raise TypeError(
                "serve_http handler response.body expected a string, bytes, or none, "
                f"received {_runtime_type_name(body)}"
            )

        if "content-length" not in header_names:
            headers["content-length"] = str(len(payload))
        return status, headers, payload

    def serve_http_fn(config_value: Any, handler: Any) -> GeniaMap:
        if not isinstance(config_value, GeniaMap):
            raise TypeError("serve_http expected config to be a map")
        if not callable(handler):
            raise TypeError("serve_http expected a handler function")

        host_value = config_value.get("host", "127.0.0.1")
        if not isinstance(host_value, str):
            raise TypeError(f"serve_http expected config.host to be a string, received {_runtime_type_name(host_value)}")

        port = _ensure_port_int(config_value.get("port", 8000), "serve_http config.port")
        max_requests = _ensure_optional_request_limit(
            config_value.get("max_requests", _UNSET),
            "serve_http config.max_requests",
        )

        class _GeniaHTTPServer(HTTPServer):
            allow_reuse_address = True

        class _GeniaRequestHandler(BaseHTTPRequestHandler):
            def _serve(self) -> None:
                try:
                    request_value = _http_request_map(self)
                    response_value = _invoke_from_builtin(handler, [request_value])
                    status, headers, payload = _http_response_triplet(response_value)
                except Exception as exc:  # pragma: no cover - exercised through HTTP 500 behavior
                    stderr_sink.write_text(f"serve_http handler error: {exc}\n")
                    status = 500
                    headers = {
                        "content-type": "text/plain; charset=utf-8",
                        "content-length": str(len(b"internal server error")),
                    }
                    payload = b"internal server error"

                self.send_response(status)
                for header_name, header_value in headers.items():
                    self.send_header(header_name, header_value)
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(payload)

            def do_GET(self) -> None:
                self._serve()

            def do_POST(self) -> None:
                self._serve()

            def do_PUT(self) -> None:
                self._serve()

            def do_DELETE(self) -> None:
                self._serve()

            def do_PATCH(self) -> None:
                self._serve()

            def do_OPTIONS(self) -> None:
                self._serve()

            def do_HEAD(self) -> None:
                self._serve()

            def log_message(self, format: str, *args: Any) -> None:
                return

        server = _GeniaHTTPServer((host_value, port), _GeniaRequestHandler)
        handled_requests = 0
        try:
            while max_requests is None or handled_requests < max_requests:
                server.handle_request()
                handled_requests += 1
        finally:
            server.server_close()

        bound_host, bound_port = server.server_address[:2]
        return GeniaMap().put("host", bound_host).put("port", bound_port).put("handled_requests", handled_requests)

    def read_file_fn(path: Any) -> Any:
        if not isinstance(path, str):
            context = (
                GeniaMap()
                .put("source", "read_file")
                .put("expected", "string_path")
                .put("received", _runtime_type_name(path))
            )
            return make_none("file-read-error", context)
        try:
            return Path(path).read_text(encoding="utf-8")
        except FileNotFoundError:
            context = GeniaMap().put("source", "read_file").put("path", path)
            return make_none("file-not-found", context)
        except OSError as exc:
            context = GeniaMap().put("source", "read_file").put("path", path).put("message", str(exc))
            return make_none("file-read-error", context)

    def write_file_fn(path: Any, text: Any) -> Any:
        if not isinstance(path, str):
            context = (
                GeniaMap()
                .put("source", "write_file")
                .put("expected", "string_path")
                .put("received", _runtime_type_name(path))
            )
            return make_none("file-write-error", context)
        if not isinstance(text, str):
            context = (
                GeniaMap()
                .put("source", "write_file")
                .put("path", path)
                .put("expected", "string_content")
                .put("received", _runtime_type_name(text))
            )
            return make_none("file-write-error", context)
        try:
            Path(path).write_text(text, encoding="utf-8")
            return path
        except OSError as exc:
            context = GeniaMap().put("source", "write_file").put("path", path).put("message", str(exc))
            return make_none("file-write-error", context)

    def zip_read_fn(path: Any) -> Any:
        if not isinstance(path, str):
            context = (
                GeniaMap()
                .put("source", "zip_read")
                .put("expected", "string_path")
                .put("received", _runtime_type_name(path))
            )
            return make_none("zip-read-error", context)
        if not Path(path).exists():
            context = GeniaMap().put("source", "zip_read").put("path", path)
            return make_none("file-not-found", context)

        def iterator() -> Iterable[Any]:
            with zipfile.ZipFile(path, "r") as archive:
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    yield [info.filename, GeniaBytes(archive.read(info.filename))]

        try:
            with zipfile.ZipFile(path, "r"):
                pass
        except zipfile.BadZipFile:
            context = GeniaMap().put("source", "zip_read").put("path", path)
            return make_none("zip-read-error", context)
        except OSError as exc:
            context = GeniaMap().put("source", "zip_read").put("path", path).put("message", str(exc))
            return make_none("zip-read-error", context)

        return GeniaFlow(iterator, label="zip_read")

    def _zip_item_to_entry(item: Any, index: int) -> Any:
        if isinstance(item, GeniaZipEntry):
            return item
        if not isinstance(item, list) or len(item) != 2:
            context = (
                GeniaMap()
                .put("source", "zip_write")
                .put("index", index)
                .put("expected", "[filename, content]")
                .put("received", _runtime_type_name(item))
            )
            return make_none("zip-write-error", context)

        name = item[0]
        content = item[1]
        if not isinstance(name, str):
            context = (
                GeniaMap()
                .put("source", "zip_write")
                .put("index", index)
                .put("expected", "string_filename")
                .put("received", _runtime_type_name(name))
            )
            return make_none("zip-write-error", context)
        if isinstance(content, str):
            content_bytes = GeniaBytes(content.encode("utf-8"))
        elif isinstance(content, GeniaBytes):
            content_bytes = content
        else:
            context = (
                GeniaMap()
                .put("source", "zip_write")
                .put("index", index)
                .put("filename", name)
                .put("expected", "bytes_or_string_content")
                .put("received", _runtime_type_name(content))
            )
            return make_none("zip-write-error", context)
        return GeniaZipEntry(name, content_bytes)

    def zip_write_flow_fn(path: Any, source: Any) -> Any:
        if not isinstance(path, str):
            context = (
                GeniaMap()
                .put("source", "zip_write")
                .put("expected", "string_path")
                .put("received", _runtime_type_name(path))
            )
            return make_none("zip-write-error", context)

        if isinstance(source, GeniaFlow):
            items = source.consume()
            close_items = source.close_on_early_termination
        elif isinstance(source, list):
            items = iter(source)
            close_items = False
        else:
            context = (
                GeniaMap()
                .put("source", "zip_write")
                .put("path", path)
                .put("expected", "flow_or_list")
                .put("received", _runtime_type_name(source))
            )
            return make_none("zip-write-error", context)

        try:
            try:
                with zipfile.ZipFile(path, "w") as archive:
                    for index, item in enumerate(items, start=1):
                        entry = _zip_item_to_entry(item, index)
                        if isinstance(entry, GeniaOptionNone):
                            return entry
                        archive.writestr(entry.name, entry.data.value)
                return path
            finally:
                if close_items:
                    _maybe_close_iterable(items)
        except OSError as exc:
            context = GeniaMap().put("source", "zip_write").put("path", path).put("message", str(exc))
            return make_none("zip-write-error", context)

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
    env.set("_clear_screen", clear_screen_fn)
    env.set("_move_cursor", move_cursor_fn)
    env.set("_render_grid", render_grid_fn)
    env.set("log", log)
    env.set("print", print_fn)
    env.set("input", input_fn)
    env.set("stdin", stdin_source)
    env.set("stdin_keys", stdin_keys_flow)
    env.set("_flow?", flow_predicate_fn)
    env.set("_lines", lines_fn)
    env.set("_tick", tick_fn)
    env.set("_tee", tee_fn)
    env.set("_merge", merge_flow_fn)
    env.set("_zip", zip_flow_fn)
    env.set("_scan", scan_fn)
    env.set("_keep_some", keep_some_fn)
    env.set("_keep_some_else", keep_some_else_fn)
    env.set("_each", each_fn)
    env.set("_rules_prepare", rules_prepare_fn)
    env.set("_rules_kernel", rules_kernel_fn)
    env.set("_rules_error", rules_error_fn)
    env.set("_flow_debug", flow_debug_fn)
    env.set("_run", run_fn)
    env.set("_collect", collect_fn)
    env.set("argv", argv_fn)
    env.set("help", help_fn)
    env.set("doc", doc_fn)
    env.set("meta", meta_fn)
    env.set("pi", math.pi)
    env.set("e", math.e)
    env.set("true", True)
    env.set("false", False)
    env.set("nil", OPTION_NONE)
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
    env.set("_absence_meta", absence_meta_fn)
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
    env.set("_cell_stop", cell_stop_fn)
    env.set("_spawn", spawn_fn)
    env.set("_send", send_fn)
    env.set("_process_alive?", process_alive_fn)
    env.set("_actor_validate_effect", actor_validate_effect_fn)
    env.set("_actor_call_update", actor_call_update_fn)
    env.set("_map_new", map_new_fn)
    env.set("_map_get", map_get_fn)
    env.set("_map_put", map_put_fn)
    env.set("_map_has?", map_has_fn)
    env.set("_map_remove", map_remove_fn)
    env.set("_map_count", map_count_fn)
    env.set("_rng", rng_fn)
    env.set("_rand", rand_fn)
    env.set("_rand_seeded", seeded_rand_fn)
    env.set("_rand_int", rand_int_fn)
    env.set("_rand_int_seeded", seeded_rand_int_fn)
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
    env.set("_read_file", read_file_fn)
    env.set("_write_file", write_file_fn)
    env.set("_json_parse", json_parse_fn)
    env.set("_json_stringify", json_stringify_fn)
    env.set("_serve_http", serve_http_fn)
    env.set("_zip_read", zip_read_fn)
    env.set("_zip_write", zip_write_flow_fn)
    env.set("zip_entries", zip_entries_fn)
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
    env.set("_sum", sum_fn)
    env.set("_reduce", reduce_fn)
    env.set("_map", map_fn)
    env.set("_filter", filter_fn)

    env.register_autoload("cli_parse", 1, "std/prelude/cli.genia")
    env.register_autoload("cli_parse", 2, "std/prelude/cli.genia")
    env.register_autoload("cli_flag?", 2, "std/prelude/cli.genia")
    env.register_autoload("cli_option", 2, "std/prelude/cli.genia")
    env.register_autoload("cli_option_or", 3, "std/prelude/cli.genia")
    env.register_autoload("lines", 1, "std/prelude/flow.genia")
    env.register_autoload("tick", 0, "std/prelude/flow.genia")
    env.register_autoload("tick", 1, "std/prelude/flow.genia")
    env.register_autoload("tee", 1, "std/prelude/flow.genia")
    env.register_autoload("merge", 1, "std/prelude/flow.genia")
    env.register_autoload("merge", 2, "std/prelude/flow.genia")
    env.register_autoload("zip", 1, "std/prelude/flow.genia")
    env.register_autoload("zip", 2, "std/prelude/flow.genia")
    env.register_autoload("scan", 2, "std/prelude/flow.genia")
    env.register_autoload("scan", 3, "std/prelude/flow.genia")
    env.register_autoload("keep_some", 1, "std/prelude/flow.genia")
    env.register_autoload("keep_some", 2, "std/prelude/flow.genia")
    env.register_autoload("keep_some_else", 2, "std/prelude/flow.genia")
    env.register_autoload("keep_some_else", 3, "std/prelude/flow.genia")
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
    env.register_autoload("inspect", 1, "std/prelude/fn.genia")
    env.register_autoload("trace", 2, "std/prelude/fn.genia")
    env.register_autoload("tap", 2, "std/prelude/fn.genia")
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
    env.register_autoload("rng", 1, "std/prelude/random.genia")
    env.register_autoload("rand", 0, "std/prelude/random.genia")
    env.register_autoload("rand", 1, "std/prelude/random.genia")
    env.register_autoload("rand_int", 1, "std/prelude/random.genia")
    env.register_autoload("rand_int", 2, "std/prelude/random.genia")
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
    env.register_autoload("clear_screen", 0, "std/prelude/io.genia")
    env.register_autoload("move_cursor", 2, "std/prelude/io.genia")
    env.register_autoload("render_grid", 1, "std/prelude/io.genia")
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
    env.register_autoload("absence_meta", 1, "std/prelude/option.genia")
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
    env.register_autoload("json_parse", 1, "std/prelude/json.genia")
    env.register_autoload("json_stringify", 1, "std/prelude/json.genia")
    env.register_autoload("json_pretty", 1, "std/prelude/json.genia")
    env.register_autoload("read_file", 1, "std/prelude/file.genia")
    env.register_autoload("write_file", 2, "std/prelude/file.genia")
    env.register_autoload("zip_read", 1, "std/prelude/file.genia")
    env.register_autoload("zip_write", 1, "std/prelude/file.genia")
    env.register_autoload("zip_write", 2, "std/prelude/file.genia")
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
    env.register_autoload("cell_stop", 1, "std/prelude/cell.genia")
    env.register_autoload("actor", 2, "std/prelude/actor.genia")
    env.register_autoload("actor_send", 2, "std/prelude/actor.genia")
    env.register_autoload("actor_call", 2, "std/prelude/actor.genia")
    env.register_autoload("actor_alive?", 1, "std/prelude/actor.genia")
    env.register_autoload("actor_stop", 1, "std/prelude/actor.genia")
    env.register_autoload("actor_restart", 2, "std/prelude/actor.genia")
    env.register_autoload("actor_state", 1, "std/prelude/actor.genia")
    env.register_autoload("actor_failed?", 1, "std/prelude/actor.genia")
    env.register_autoload("actor_error", 1, "std/prelude/actor.genia")
    env.register_autoload("actor_status", 1, "std/prelude/actor.genia")
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
    assert_portable_core_ir(ir_nodes)
    ir_nodes = optimize_program(ir_nodes, debug=os.getenv("GENIA_DEBUG_OPT", "") == "1")
    env.debug_hooks = effective_hooks
    env.debug_mode = effective_debug_mode
    result = Evaluator(env, debug_hooks=effective_hooks, debug_mode=effective_debug_mode).eval_program(ir_nodes)
    return _normalize_absence(result)


def _scan_pipe_mode_reserved_usage(node: Node, bound_names: set[str]) -> tuple[bool, bool]:
    """Return whether unbound stdin/run identifiers appear in a pipe stage expression."""
    if isinstance(node, Var):
        return node.name == "stdin" and node.name not in bound_names, node.name == "run" and node.name not in bound_names

    if isinstance(node, Lambda):
        nested_bound = set(bound_names)
        nested_bound.update(node.params)
        if node.rest_param is not None:
            nested_bound.add(node.rest_param)
        return _scan_pipe_mode_reserved_usage(node.body, nested_bound)

    if isinstance(node, Block):
        local_bound = set(bound_names)
        saw_stdin = False
        saw_run = False
        for expr in node.exprs:
            uses_stdin, uses_run = _scan_pipe_mode_reserved_usage(expr, local_bound)
            saw_stdin = saw_stdin or uses_stdin
            saw_run = saw_run or uses_run
            if isinstance(expr, Assign):
                local_bound.add(expr.name)
            if saw_stdin and saw_run:
                break
        return saw_stdin, saw_run

    if not is_dataclass(node):
        return False, False

    saw_stdin = False
    saw_run = False
    for node_field in fields(node):
        if node_field.name == "span":
            continue
        uses_stdin, uses_run = _scan_pipe_mode_reserved_usage_value(getattr(node, node_field.name), bound_names)
        saw_stdin = saw_stdin or uses_stdin
        saw_run = saw_run or uses_run
        if saw_stdin and saw_run:
            break
    return saw_stdin, saw_run


def _scan_pipe_mode_reserved_usage_value(value: Any, bound_names: set[str]) -> tuple[bool, bool]:
    if isinstance(value, Node):
        return _scan_pipe_mode_reserved_usage(value, bound_names)
    if isinstance(value, (list, tuple)):
        saw_stdin = False
        saw_run = False
        for item in value:
            uses_stdin, uses_run = _scan_pipe_mode_reserved_usage_value(item, bound_names)
            saw_stdin = saw_stdin or uses_stdin
            saw_run = saw_run or uses_run
            if saw_stdin and saw_run:
                break
        return saw_stdin, saw_run
    return False, False


def _validate_pipe_mode_expr(source: str) -> None:
    tokens = lex(source)
    parser = Parser(tokens, source=source, filename="<pipe>")
    ast_nodes = parser.parse_program()
    if len(ast_nodes) != 1 or not isinstance(ast_nodes[0], ExprStmt):
        raise ValueError("-p/--pipe expects a single stage expression")

    uses_stdin, uses_run = _scan_pipe_mode_reserved_usage(ast_nodes[0].expr, set())
    if uses_stdin:
        raise ValueError("-p/--pipe stage expression must omit stdin; it is added automatically")
    if uses_run:
        raise ValueError("-p/--pipe stage expression must omit run; it is added automatically")


def _wrap_pipe_mode_expr(source: str) -> str:
    _validate_pipe_mode_expr(source)
    return f"stdin |> lines |> {source} |> run"


def _extract_pipe_stage_name(message: str) -> str | None:
    """Extract the stage expression name from a pipeline error message."""
    match = re.search(r" at (.+?) \[", message)
    return match.group(1) if match else None


def _format_pipe_mode_error(exc: Exception) -> str:
    message = str(exc)
    if message == "-p/--pipe expects a single stage expression":
        return "Pipe mode expression must be a single stage expression, not a full program"
    if message == "-p/--pipe stage expression must omit stdin; it is added automatically":
        return "Do not use stdin in pipe mode; stdin is provided automatically"
    if message == "-p/--pipe stage expression must omit run; it is added automatically":
        return "Do not use run in pipe mode; run is implicit in pipe mode"
    if "Flow has already been consumed" in message:
        return "Flow values are single-use and cannot be reused after consumption"
    if "run expected a flow, received " in message:
        received = message.rsplit("received ", 1)[1]
        detail = f"Pipe mode stage must produce a flow; received {received}"
        if received in {"int", "float", "bool", "string", "list", "map"}:
            return f"{detail}. Use -c/--command when you want a final value such as `collect |> sum` or `collect |> count`."
        if received in {"some", "none"}:
            return (
                f"{detail}. Pipe mode expects a Flow stage, not a final Option value. "
                "Use keep_some(...), keep_some_else(...), per-item unwrap_or(...), or switch to -c/--command."
            )
        return detail
    if "stage received flow;" in message:
        stage_name = _extract_pipe_stage_name(message)
        # Per-item function receiving a flow directly (e.g. parse_int gets flow instead of string)
        if re.search(r"expected a (string|number|integer|bool), received flow\b", message):
            parts = [message]
            parts.append("Pipe mode passes a Flow through each stage, not one item at a time.")
            if stage_name:
                parts.append(f"Did you mean: map({stage_name}) or keep_some({stage_name})")
            else:
                parts.append("Wrap per-item functions with map(...) or keep_some(...).")
            return "\n".join(parts)
        # Reducer receiving a flow directly (e.g. sum expects a list)
        if "expected a list, received flow" in message:
            parts = [message]
            parts.append("Pipe mode passes a Flow, not a materialized list.")
            if stage_name:
                parts.append(f"Did you mean: collect |> {stage_name}")
            parts.append("Or use -c/--command for the full pipeline.")
            return "\n".join(parts)
        # Generic fallback for other flow-stage mismatches
        return (
            f"{message}. Pipe mode stages receive a Flow, not one row at a time. "
            "Use Flow stages such as map(...), filter(...), head(...), each(...), or keep_some(...); "
            "use -c/--command for reducers such as sum or count."
        )
    if "received some" in message:
        return (
            f"{message}. "
            "If this stage is intentionally Option-aware, keep explicit helpers such as flat_map_some(...), map_some(...), or then_* in place."
        )
    return message


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
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    terminator_index: int | None = None
    try:
        terminator_index = raw_argv.index("--")
    except ValueError:
        terminator_index = None

    parser = argparse.ArgumentParser(
        prog="genia",
        description="Genia CLI: file mode, command mode (-c), pipe mode (-p), or REPL.",
        epilog=(
            "Modes:\n"
            "  genia path/to/file.genia [args ...]\n"
            "  genia -c 'source' [args ...]\n"
            "  genia -p 'stage_expr' [args ...]\n"
            "  genia\n\n"
            "Pipe mode wraps as: stdin |> lines |> <stage_expr> |> run\n"
            "Use -- to stop option parsing and pass dash-prefixed literals as args/paths."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    command_group = parser.add_mutually_exclusive_group()
    command_group.add_argument("-c", "--command", help="Execute inline Genia source")
    command_group.add_argument("-p", "--pipe", help="Execute a pipe-mode stage expression")
    parser.add_argument("--debug-stdio", action="store_true", help="Run debug adapter over stdio for a program file")
    args, remaining_args = parser.parse_known_args(raw_argv)
    explicit_terminator_used = False
    if remaining_args and remaining_args[0] == "--":
        explicit_terminator_used = True
        remaining_args = remaining_args[1:]

    if args.command is None and args.pipe is None and remaining_args and remaining_args[0].startswith("-"):
        if not explicit_terminator_used and terminator_index is None:
            parser.error(
                "expected a source file path when not using -c/--command or -p/--pipe; "
                f"got option-like argument '{remaining_args[0]}'"
            )

    program_path: Optional[str] = None
    script_args: list[str] = []
    if args.command is not None or args.pipe is not None:
        script_args = remaining_args
    elif remaining_args:
        program_path = remaining_args[0]
        script_args = remaining_args[1:]

    if args.debug_stdio:
        if args.command is not None:
            parser.error("--debug-stdio cannot be used with --command")
        if args.pipe is not None:
            parser.error("--debug-stdio cannot be used with --pipe")
        if program_path is None:
            parser.error("--debug-stdio requires a program path")
        if script_args:
            parser.error("--debug-stdio accepts exactly one program path")
        if not Path(program_path).is_file():
            parser.error(f"--debug-stdio program path not found: {program_path}")
        return run_debug_stdio(program_path)

    def resolve_program_result(run_result: Any, env: Env) -> Any:
        main_group = env.values.get("main")
        if not isinstance(main_group, GeniaFunctionGroup):
            return run_result
        main_with_args = main_group.get(1)
        if main_with_args is not None:
            cli_args = env.get("argv")()
            return _normalize_absence(main_with_args(cli_args))
        main_without_args = main_group.get(0)
        if main_without_args is not None:
            return _normalize_absence(main_without_args())
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
            _emit_error(env, f"Error: {_format_pipe_mode_error(e)}")
            return 1

    if args.command is not None:
        env = make_global_env(cli_args=script_args)
        try:
            run_result = run_source(args.command, env, filename="<command>")
            result = resolve_program_result(run_result, env)
            if result is not None and not _is_nil_none(result):
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
            if result is not None and not _is_nil_none(result):
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
