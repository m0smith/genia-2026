from __future__ import annotations

import bisect
from typing import Optional
from .numeric_source import classify_numeric_literal
from .ast_nodes import (
    AnnotatedNode,
    Annotation,
    Assign,
    Binary,
    Block,
    Boolean,
    Call,
    CaseClause,
    CaseExpr,
    Delay,
    ErrPattern,
    ExprStmt,
    FuncDef,
    GlobPattern,
    ImportStmt,
    Lambda,
    ListLiteral,
    ListPattern,
    MapLiteral,
    MapPattern,
    NamedPatternDef,
    NamedPatternUse,
    Nil,
    Node,
    NoneOption,
    Number,
    OpenExtendDef,
    OpenFuncDef,
    OpenUseDef,
    QuasiQuote,
    Quote,
    RestPattern,
    ShellStage,
    SomePattern,
    Spread,
    String,
    TuplePattern,
    Unary,
    Unquote,
    UnquoteSplicing,
    Var,
    WildcardPattern,
)
from .lexer import Token, SourceSpan, parse_string_literal, parse_glob_literal

PRECEDENCE = {
    "PIPE_FWD": 5,
    "OR": 10,
    "AT_CHECK": 15,
    "AT_ASSERT": 15,
    "AND": 20,
    "AMP": 25,
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


def _number_node(tok, span) -> Number:
    """Build a Number AST node with R21 E21-1 source classification metadata.

    `value` preserves the existing evaluator-facing int/float construction
    (unchanged R21 evaluator/runtime boundary); the new source_kind/digits/
    coefficient/exponent fields carry the pure lexical classification from
    classify_numeric_literal for E21-2 to consume later.
    """
    source = classify_numeric_literal(tok.text)
    if source.kind == "integer":
        return Number(int(tok.text), span=span, source_kind="integer", digits=source.digits)
    return Number(
        float(tok.text),
        span=span,
        source_kind="decimal",
        coefficient=source.coefficient,
        exponent=source.exponent,
    )


class Parser:
    def __init__(self, tokens: list[Token], source: str = "", filename: str = "<memory>"):
        self.tokens = tokens
        self.source = source
        self.filename = filename
        self.i = 0
        # R20 open functions: names declared `open` earlier in this module's
        # top-level clause run, so a later bare pattern-headed clause with
        # the same name is recognized as a repeated clause rather than an
        # ordinary function header (openness is declared, never inferred).
        self._open_names: set[str] = set()
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
