"""R20 contract section 3.3: header-name capture check for grouped open clauses.

In `open f(h1, ..., hn) = (p1, ...) -> r1 | ...` the plain-identifier header
names are not bindings; each arm is an independent clause. An arm guard or
result that refers freely to a header name its own pattern does not bind would
silently resolve to an outer or global binding of that name, so the parser
rejects the program with `open-function-header-capture` before anything runs.

The scope rules are the portable ones recorded in
docs/design/r20-open-functions-syntax-ir-design.md section 4.1: a lambda's
parameter names, a nested case arm's pattern names, and an earlier assignment
in the same block shadow a header name; quoted data is not a reference.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Iterable, Optional

from .ast_nodes import (
    Assign,
    Binary,
    Block,
    CaseClause,
    CaseExpr,
    ErrPattern,
    Lambda,
    ListPattern,
    MapLiteral,
    MapPattern,
    NamedPatternUse,
    Node,
    Quote,
    QuasiQuote,
    RestPattern,
    SomePattern,
    TuplePattern,
    Unquote,
    UnquoteSplicing,
    Var,
)


def pattern_binders(pattern: Optional[Node]) -> set[str]:
    """Names that `pattern` binds at any depth.

    Identifier patterns (`Var`) and named rest patterns bind; wildcards,
    literals, and an unnamed rest bind nothing. Pure; never raises.
    """
    names: set[str] = set()
    if pattern is None:
        return names
    if isinstance(pattern, Var):
        names.add(pattern.name)
    elif isinstance(pattern, RestPattern):
        if pattern.name:
            names.add(pattern.name)
    elif isinstance(pattern, (TuplePattern, ListPattern)):
        for item in pattern.items:
            names |= pattern_binders(item)
    elif isinstance(pattern, MapPattern):
        for _key, value in pattern.items:
            names |= pattern_binders(value)
    elif isinstance(pattern, SomePattern):
        names |= pattern_binders(pattern.inner) | pattern_binders(pattern.context)
    elif isinstance(pattern, ErrPattern):
        names |= pattern_binders(pattern.reason) | pattern_binders(pattern.context)
    elif isinstance(pattern, NamedPatternUse):
        names |= pattern_binders(pattern.inner)
    return names


def _children(node: Node) -> Iterable[Node]:
    """Direct child nodes of `node` (fields holding a node, or lists/tuples of them)."""
    if not is_dataclass(node):
        return
    for f in fields(node):
        value = getattr(node, f.name)
        stack = [value]
        while stack:
            current = stack.pop()
            if isinstance(current, Node):
                yield current
            elif isinstance(current, (list, tuple)):
                stack.extend(current)


def first_free_reference(node: Optional[Node], watched: set[str], bound: frozenset[str]) -> Optional[Var]:
    """The first reference, in source order, to a name in `watched` that no
    binder inside `node` shadows, or None.

    `bound` holds names already introduced by enclosing binders within the
    arm. Pure; never raises.
    """
    if node is None:
        return None
    if isinstance(node, Var):
        return node if node.name in watched and node.name not in bound else None
    if isinstance(node, Quote):
        return None
    if isinstance(node, QuasiQuote):
        return _first_unquoted_reference(node.expr, watched, bound)
    if isinstance(node, Binary):
        found = first_free_reference(node.left, watched, bound)
        if found is None and not node.named_access:
            found = first_free_reference(node.right, watched, bound)
        return found
    if isinstance(node, Block):
        scope = set(bound)
        for expr in node.exprs:
            found = first_free_reference(expr, watched, frozenset(scope))
            if found is not None:
                return found
            if isinstance(expr, Assign):
                scope.add(expr.name)
        return None
    if isinstance(node, Lambda):
        scope = set(bound) | set(node.params)
        if node.rest_param:
            scope.add(node.rest_param)
        scope |= pattern_binders(node.pattern)
        return first_free_reference(node.body, watched, frozenset(scope))
    if isinstance(node, CaseExpr):
        for clause in node.clauses:
            found = _first_in_clause(clause, watched, bound)
            if found is not None:
                return found
        return None
    if isinstance(node, MapLiteral):
        for _key, value in node.items:
            found = first_free_reference(value, watched, bound)
            if found is not None:
                return found
        return None
    for child in _children(node):
        found = first_free_reference(child, watched, bound)
        if found is not None:
            return found
    return None


def _first_in_clause(clause: CaseClause, watched: set[str], bound: frozenset[str]) -> Optional[Var]:
    """First free reference in a case arm's guard then result, with the arm's own pattern names in scope."""
    scope = frozenset(set(bound) | pattern_binders(clause.pattern))
    found = first_free_reference(clause.guard, watched, scope)
    if found is None:
        found = first_free_reference(clause.result, watched, scope)
    return found


def _first_unquoted_reference(node: Node, watched: set[str], bound: frozenset[str]) -> Optional[Var]:
    """First free reference inside the unquoted parts of a quasiquote; the quoted skeleton is data."""
    if isinstance(node, (Unquote, UnquoteSplicing)):
        return first_free_reference(node.expr, watched, bound)
    for child in _children(node):
        found = _first_unquoted_reference(child, watched, bound)
        if found is not None:
            return found
    return None


def header_names(header: TuplePattern) -> list[str]:
    """Plain-identifier and named-rest names of a trivial grouped-clause header, in order."""
    names: list[str] = []
    for item in header.items:
        if isinstance(item, Var):
            names.append(item.name)
        elif isinstance(item, RestPattern) and item.name:
            names.append(item.name)
    return names


def find_header_capture(header: TuplePattern, arms: list[CaseClause]) -> Optional[tuple[str, Optional[Node]]]:
    """The first `(name, reference node)` that a grouped clause must be rejected for, or None.

    For each arm, the watched names are the header names its own pattern does
    not bind; the arm's guard then result are searched in source order.
    """
    header_name_list = header_names(header)
    if not header_name_list:
        return None
    for arm in arms:
        watched = set(header_name_list) - pattern_binders(arm.pattern)
        if not watched:
            continue
        found = first_free_reference(arm.guard, watched, frozenset())
        if found is None:
            found = first_free_reference(arm.result, watched, frozenset())
        if found is not None:
            return found.name, found
    return None
