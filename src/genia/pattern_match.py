"""Pattern matching engine for the Python reference host."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .values import GeniaMap, GeniaOptionNone, GeniaOptionSome


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

    matcher: CompiledGlobPattern


@dataclass
class IrPatSome(IrPattern):
    """Option constructor pattern that matches `some(value)` values."""

    inner: IrPattern


@dataclass
class IrPatNone(IrPattern):
    """Option none-family pattern with optional reason and context matching."""

    reason: IrPattern | None = None
    context: IrPattern | None = None


def _merge_bindings(target: dict[str, Any], source: dict[str, Any]) -> bool:
    for key, value in source.items():
        if key in target and target[key] != value:
            return False
        target[key] = value
    return True


def match_pattern(pattern: IrPattern, args: tuple[Any, ...]) -> Optional[dict[str, Any]]:
    # Pattern matching targets the full argument tuple.
    if isinstance(pattern, IrPatTuple):
        if len(pattern.items) != len(args):
            return None
        env: dict[str, Any] = {}
        for pat, arg in zip(pattern.items, args):
            sub = match_pattern_atom(pat, arg)
            if sub is None or not _merge_bindings(env, sub):
                return None
        return env
    if len(args) != 1:
        return None
    return match_pattern_atom(pattern, args[0])


def match_lambda_pattern(pattern: IrPattern, args: tuple[Any, ...]) -> Optional[dict[str, Any]]:
    if not isinstance(pattern, IrPatTuple):
        return match_pattern(pattern, args)

    rest_index = None
    for index, item in enumerate(pattern.items):
        if isinstance(item, IrPatRest):
            rest_index = index
            break

    if rest_index is None:
        return match_pattern(pattern, args)

    if rest_index != len(pattern.items) - 1:
        return None
    prefix = pattern.items[:rest_index]
    if len(args) < len(prefix):
        return None

    env: dict[str, Any] = {}
    for pat, arg in zip(prefix, args[:len(prefix)]):
        sub = match_pattern_atom(pat, arg)
        if sub is None or not _merge_bindings(env, sub):
            return None

    rest_pat = pattern.items[rest_index]
    sub = match_pattern_atom(rest_pat, list(args[len(prefix):]))
    if sub is None or not _merge_bindings(env, sub):
        return None
    return env


def match_pattern_atom(pattern: IrPattern, arg: Any) -> Optional[dict[str, Any]]:
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
            reason_bindings = match_pattern_atom(pattern.reason, arg.reason)
            if reason_bindings is None:
                return None
            env.update(reason_bindings)
        if pattern.context is not None:
            context_bindings = match_pattern_atom(pattern.context, arg.context)
            if context_bindings is None or not _merge_bindings(env, context_bindings):
                return None
        return env
    if isinstance(pattern, IrPatSome):
        if not isinstance(arg, GeniaOptionSome):
            return None
        return match_pattern_atom(pattern.inner, arg.value)
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
                sub = match_pattern_atom(pat, item)
                if sub is None or not _merge_bindings(env, sub):
                    return None
            return env

        prefix = pattern.items[:rest_index]
        rest_pat = pattern.items[rest_index]

        if len(arg) < len(prefix):
            return None

        env: dict[str, Any] = {}
        for pat, item in zip(prefix, arg[:len(prefix)]):
            sub = match_pattern_atom(pat, item)
            if sub is None or not _merge_bindings(env, sub):
                return None

        sub = match_pattern_atom(rest_pat, arg[len(prefix):])
        if sub is None or not _merge_bindings(env, sub):
            return None
        return env
    if isinstance(pattern, IrPatMap):
        if not isinstance(arg, GeniaMap):
            return None
        env: dict[str, Any] = {}
        for key, value_pattern in pattern.items:
            if not arg.has(key):
                return None
            value = arg.get(key)
            sub = match_pattern_atom(value_pattern, value)
            if sub is None or not _merge_bindings(env, sub):
                return None
        return env
    raise RuntimeError(f"Unsupported pattern: {pattern!r}")


def pattern_explicitly_handles_none(pattern: IrPattern) -> bool:
    if isinstance(pattern, IrPatNone):
        return True
    if isinstance(pattern, IrPatTuple):
        return any(pattern_explicitly_handles_none(item) for item in pattern.items)
    if isinstance(pattern, IrPatList):
        return any(pattern_explicitly_handles_none(item) for item in pattern.items)
    if isinstance(pattern, IrPatMap):
        return any(pattern_explicitly_handles_none(item) for _, item in pattern.items)
    if isinstance(pattern, IrPatSome):
        return pattern_explicitly_handles_none(pattern.inner)
    return False


def pattern_explicitly_handles_some(pattern: IrPattern) -> bool:
    if isinstance(pattern, IrPatSome):
        return True
    if isinstance(pattern, IrPatTuple):
        return any(pattern_explicitly_handles_some(item) for item in pattern.items)
    if isinstance(pattern, IrPatList):
        return any(pattern_explicitly_handles_some(item) for item in pattern.items)
    if isinstance(pattern, IrPatMap):
        return any(pattern_explicitly_handles_some(item) for _, item in pattern.items)
    if isinstance(pattern, IrPatNone):
        if pattern.reason is not None and pattern_explicitly_handles_some(pattern.reason):
            return True
        if pattern.context is not None and pattern_explicitly_handles_some(pattern.context):
            return True
    return False
