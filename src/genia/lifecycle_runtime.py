"""R14 E14-1/E14-2/E14-3 lifecycle instance, scope, and element core.

Implements the portable entry/work/unwind algorithm and scope lifetime state
machine locked by the approved R14 contract
(``docs/design/r14-composable-lifecycle-contract.md``). The algorithm is
peer-list general from the start — it is the exact same algorithm reused,
unchanged, by vertical composition (``lifecycle_scope``/``lifecycle_child``,
issue #621), horizontal peer attachment breadth (issue #692), and each fresh
element scope of ``lifecycle_repeat`` (``run_lifecycle_element``, issue
#693). This module knows nothing about ``list``/``Flow``/iteration:
dispatching one ``run_lifecycle_element`` call per consumed element, eagerly
or lazily, is ``genia.builtins``'s ``lifecycle_repeat_fn``'s concern, not
this module's. It adds no ``lifecycle_config`` or HTTP behavior; those
remain later tickets (#694, #622-#628).
"""

from __future__ import annotations

from typing import Any, Callable

from .values import (
    GeniaMap,
    GeniaOptionErr,
    GeniaOptionSome,
    GeniaSymbol,
    make_none,
    symbol,
)

Invoke = Callable[[Any, list], Any]

_PEER_FIELDS = {"name", "enter", "exit"}
_ALIVE_LIFETIMES = ("entering", "active", "exiting")

_NO_PEER = make_none("lifecycle-no-peer")
_NO_RESULT = make_none("lifecycle-no-result")
_NO_FAILURE = make_none("lifecycle-no-failure")
_EXPIRED = "lifecycle-scope-expired"


class GeniaLifecycleScope:
    """Opaque per-scope-operation handle passed to enter/exit/work callables.

    Not source-constructible and not a public value category: it is obtained
    only as the argument passed into one ``lifecycle_scope``/``lifecycle_child``
    operation's own callables. Valid only while ``lifetime`` is one of
    ``entering``/``active``/``exiting``; any later use raises the same
    single-valid-lifetime ``RuntimeError`` family as an already-consumed Flow.
    """

    __slots__ = ("kind", "parent", "lifetime", "context")

    def __init__(self, kind: str, parent: "GeniaLifecycleScope | None"):
        self.kind = kind
        self.parent = parent
        self.lifetime = "created"
        self.context: dict[str, Any] = {}

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return f"<lifecycle-scope {self.kind} {self.lifetime}>"


def _require_live(handle: Any, operation: str) -> GeniaLifecycleScope:
    if not isinstance(handle, GeniaLifecycleScope):
        raise TypeError(
            f"{operation} expected a lifecycle scope handle, "
            f"received {type(handle).__name__}"
        )
    if handle.lifetime not in _ALIVE_LIFETIMES:
        raise RuntimeError(_EXPIRED)
    return handle


def _peer_name(peer: Any, operation: str) -> str:
    if not isinstance(peer, GeniaMap):
        raise TypeError(
            f"{operation} expected a lifecycle definition map, "
            f"received {type(peer).__name__}"
        )
    fields = {key for key, _value in peer.items() if isinstance(key, str)}
    if fields != _PEER_FIELDS:
        raise TypeError(
            f"{operation} expected a lifecycle definition with exactly "
            "'name', 'enter', and 'exit' fields"
        )
    name = peer.get("name")
    if not isinstance(name, GeniaSymbol) or name.name == "":
        raise TypeError(
            f"{operation} expected a non-empty peer name symbol, "
            f"received {type(name).__name__}"
        )
    return name.name


def _validate_peers(
    peers: Any, scope: GeniaLifecycleScope, operation: str
) -> list[tuple[str, GeniaMap]]:
    """Validate one scope operation's peer list before any ``enter`` runs.

    ``scope`` is the scope being entered, checked inclusive of itself: an
    element scope's reserved ``quote(element)``/``quote(index)`` context is
    pre-seeded into ``scope.context`` by its caller before this runs, so a
    peer name colliding with a reserved name is caught here as a
    self-collision, using the same walk that already climbs ``scope.parent``
    for ancestor non-shadowing. For a root/child scope, ``scope.context`` is
    always empty at this point, so checking it first is a no-op and this
    behaves exactly as before this scope-inclusive walk was introduced.
    """

    if not isinstance(peers, list):
        raise TypeError(
            f"{operation} expected a list of lifecycle definitions, "
            f"received {type(peers).__name__}"
        )
    validated: list[tuple[str, GeniaMap]] = []
    seen: set[str] = set()
    for peer in peers:
        name = _peer_name(peer, operation)
        if name in seen:
            raise TypeError(
                f"{operation} received duplicate peer name {name!r} in one peer list"
            )
        seen.add(name)
        ancestor: GeniaLifecycleScope | None = scope
        while ancestor is not None:
            if name in ancestor.context:
                raise TypeError(
                    f"{operation} peer name {name!r} shadows context already "
                    "exposed by this scope or an ancestor scope"
                )
            ancestor = ancestor.parent
        validated.append((name, peer))
    return validated


def _normalize_exception(error: Exception) -> tuple[str, GeniaMap]:
    reason = str(error) or "lifecycle-failure"
    return reason, GeniaMap()


def _outcome_context(context: Any, operation: str) -> GeniaMap:
    if context is None:
        return GeniaMap()
    if not isinstance(context, GeniaMap):
        raise TypeError(f"{operation} expected err(...) context to be a map")
    return context


def _failure_value(peer_name: str | None, phase: str, reason: str, context: GeniaMap) -> GeniaMap:
    peer_opt = GeniaOptionSome(symbol(peer_name)) if peer_name is not None else _NO_PEER
    return (
        GeniaMap()
        .put("peer", peer_opt)
        .put("phase", symbol(phase))
        .put("reason", reason)
        .put("context", context)
    )


def _primary_summary(primary: GeniaMap | None) -> GeniaMap:
    if primary is None:
        return (
            GeniaMap()
            .put("status", symbol("ok"))
            .put("phase", symbol("work"))
            .put("peer", _NO_PEER)
        )
    return (
        GeniaMap()
        .put("status", symbol("error"))
        .put("phase", primary.get("phase"))
        .put("peer", primary.get("peer"))
    )


_OPERATION_BY_KIND = {
    "root": "lifecycle_scope",
    "child": "lifecycle_child",
    "element": "lifecycle_repeat",
}


def _run_scope(
    kind: str,
    parent: GeniaLifecycleScope | None,
    peers: Any,
    work: Any,
    invoke: Invoke,
    *,
    preset_context: dict[str, Any] | None = None,
) -> GeniaMap:
    operation = _OPERATION_BY_KIND[kind]

    scope = GeniaLifecycleScope(kind, parent)
    if preset_context:
        scope.context.update(preset_context)

    validated_peers = _validate_peers(peers, scope, operation)

    scope.lifetime = "entering"

    entered: list[tuple[str, GeniaMap]] = []
    primary_failure: GeniaMap | None = None

    for name, peer in validated_peers:
        enter_fn = peer.get("enter")
        try:
            outcome = invoke(enter_fn, [scope])
        except Exception as error:  # noqa: BLE001 - normalized into the envelope
            reason, context = _normalize_exception(error)
            primary_failure = _failure_value(name, "enter", reason, context)
            break
        if isinstance(outcome, GeniaOptionSome):
            scope.context[name] = outcome.value
            entered.append((name, peer))
            continue
        if isinstance(outcome, GeniaOptionErr):
            context = _outcome_context(outcome.context, "lifecycle enter")
            primary_failure = _failure_value(name, "enter", outcome.reason, context)
            break
        raise TypeError(
            f"lifecycle enter for peer {name!r} must return some(...) or err(...), "
            f"received {type(outcome).__name__}"
        )

    result_value: Any = _NO_RESULT
    if primary_failure is None:
        scope.lifetime = "active"
        try:
            work_return = invoke(work, [scope])
        except Exception as error:  # noqa: BLE001
            reason, context = _normalize_exception(error)
            primary_failure = _failure_value(None, "work", reason, context)
        else:
            result_value = GeniaOptionSome(work_return)

    cleanup_failures: list[GeniaMap] = []
    if entered:
        scope.lifetime = "exiting"
        for name, peer in reversed(entered):
            exit_fn = peer.get("exit")
            summary = _primary_summary(primary_failure)
            failure: GeniaMap | None = None
            try:
                outcome = invoke(exit_fn, [scope, summary])
            except Exception as error:  # noqa: BLE001
                reason, context = _normalize_exception(error)
                failure = _failure_value(name, "exit", reason, context)
            else:
                if isinstance(outcome, GeniaOptionSome):
                    pass
                elif isinstance(outcome, GeniaOptionErr):
                    context = _outcome_context(outcome.context, "lifecycle exit")
                    failure = _failure_value(name, "exit", outcome.reason, context)
                else:
                    raise TypeError(
                        f"lifecycle exit for peer {name!r} must return some(...) or "
                        f"err(...), received {type(outcome).__name__}"
                    )
            if failure is not None:
                if primary_failure is None:
                    primary_failure = failure
                else:
                    cleanup_failures.append(failure)

    scope.lifetime = "completed" if primary_failure is None else "failed"

    if primary_failure is None:
        return (
            GeniaMap()
            .put("status", symbol("ok"))
            .put("state", symbol("completed"))
            .put("scope", symbol(kind))
            .put("phase", symbol("exit"))
            .put("peer", _NO_PEER)
            .put("result", result_value)
            .put("primary_failure", _NO_FAILURE)
            .put("cleanup_failures", cleanup_failures)
        )

    return (
        GeniaMap()
        .put("status", symbol("error"))
        .put("state", symbol("failed"))
        .put("scope", symbol(kind))
        .put("phase", primary_failure.get("phase"))
        .put("peer", primary_failure.get("peer"))
        .put("result", result_value)
        .put("primary_failure", primary_failure)
        .put("cleanup_failures", cleanup_failures)
    )


def run_lifecycle_scope(peers: Any, work: Any, invoke: Invoke) -> GeniaMap:
    """Run a fresh root execution scope: ``lifecycle_scope(peers, work)``."""

    return _run_scope("root", None, peers, work, invoke)


def run_lifecycle_child(parent_handle: Any, peers: Any, work: Any, invoke: Invoke) -> GeniaMap:
    """Run a child execution scope nested under an active parent handle.

    ``lifecycle_child(scope_handle, peers, work)`` may only be called while
    ``scope_handle``'s scope is ``active`` — i.e. synchronously from within
    that scope's own ``work`` callable. A handle that is alive but not
    ``active`` (mid ``entering``/``exiting``) is rejected with a distinct
    ``RuntimeError`` from the scope-expired identifier, since it is not
    expired, merely in the wrong phase for child creation; there is no
    asynchronous, stored-handle, or resumed-scope child creation path.
    """

    parent = _require_live(parent_handle, "lifecycle_child")
    if parent.lifetime != "active":
        raise RuntimeError(
            "lifecycle_child requires an active parent scope, "
            f"received lifetime {parent.lifetime!r}"
        )
    return _run_scope("child", parent, peers, work, invoke)


def run_lifecycle_element(
    peers: Any, element: Any, index: int, work: Any, invoke: Invoke
) -> GeniaMap:
    """Run one fresh element scope for ``lifecycle_repeat``'s caller.

    Reserved context ``quote(element)`` (the consumed ``element`` value) and
    ``quote(index)`` (its 1-based pull ordinal) are populated before any
    attached peer's own ``enter`` runs, readable by every peer and by
    ``work`` through the existing ``lifecycle_context`` accessor. A peer
    named ``element`` or ``index`` is construction-time misuse, rejected by
    the same non-shadowing mechanism ``_validate_peers`` already uses for
    ancestor context — see its docstring.

    An element scope has no R14 parent (``scope: quote(element)``, like a
    root scope): ``lifecycle_repeat`` itself has no lifecycle scope of its
    own, so each element scope is independent and never leaks context to
    another. This module has no knowledge of ``list``/``Flow``/iteration —
    dispatching one call of this function per consumed element, eagerly or
    lazily, is entirely genia.builtins's `lifecycle_repeat_fn`'s concern.
    """

    return _run_scope(
        "element",
        None,
        peers,
        work,
        invoke,
        preset_context={"element": element, "index": index},
    )


def lookup_lifecycle_context(handle: Any, name: Any) -> Any:
    """``lifecycle_context(scope_handle, name)``: inward-only context lookup.

    Checks the handle's own scope first, then its parent, then that parent's
    parent, up to the root, returning the first exposed value found. Never
    writes; only ``enter`` results populate context.
    """

    scope = _require_live(handle, "lifecycle_context")
    if not isinstance(name, GeniaSymbol) or name.name == "":
        raise TypeError(
            "lifecycle_context expected a non-empty context name symbol, "
            f"received {type(name).__name__}"
        )
    key = name.name
    cursor: GeniaLifecycleScope | None = scope
    while cursor is not None:
        if key in cursor.context:
            return GeniaOptionSome(cursor.context[key])
        cursor = cursor.parent
    return make_none("lifecycle-context-absent")
