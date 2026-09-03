"""Explicit root/child lifecycle execution scopes for the Python reference host."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .values import (
    GeniaMap,
    GeniaOptionErr,
    GeniaOptionSome,
    GeniaSymbol,
    make_none,
    symbol,
)


Invoke = Callable[[Any, list[Any]], Any]
CallableCheck = Callable[[Any], bool]

_LIVE_STATES = frozenset({"entering", "active", "exiting"})
_DEFINITION_FIELDS = frozenset({"name", "enter", "exit"})


def _record(**fields: Any) -> GeniaMap:
    result = GeniaMap()
    for name, value in fields.items():
        result = result.put(name, value)
    return result


@dataclass
class _LifecycleInstance:
    name: GeniaSymbol
    enter: Any
    exit: Any
    entered: bool = False


class ExecutionScope:
    """Opaque handle for one synchronous lifecycle scope."""

    __slots__ = ("_parent", "_kind", "_state", "_contexts", "_instances", "_in_work")

    def __init__(self, parent: ExecutionScope | None, kind: str):
        self._parent = parent
        self._kind = kind
        self._state = "created"
        self._contexts: dict[str, Any] = {}
        self._instances: list[_LifecycleInstance] = []
        self._in_work = False

    def __repr__(self) -> str:
        return "<execution-scope>"


def run_lifecycle_scope(
    peers: Any,
    work: Any,
    *,
    invoke: Invoke,
    is_callable: CallableCheck = callable,
) -> GeniaMap:
    """Run one root execution scope."""

    return _run_scope(None, "root", peers, work, invoke=invoke, is_callable=is_callable)


def run_lifecycle_child(
    parent: Any,
    peers: Any,
    work: Any,
    *,
    invoke: Invoke,
    is_callable: CallableCheck = callable,
) -> GeniaMap:
    """Run one synchronous child of an active parent scope."""

    parent_scope = _require_scope(parent)
    _require_live(parent_scope)
    if parent_scope._state != "active" or not parent_scope._in_work:
        raise RuntimeError("lifecycle_child requires an active parent work scope")
    return _run_scope(parent_scope, "child", peers, work, invoke=invoke, is_callable=is_callable)


def lifecycle_context(scope: Any, name: Any) -> Any:
    """Read the nearest inward-visible lifecycle context."""

    current = _require_scope(scope)
    _require_live(current)
    if not isinstance(name, GeniaSymbol):
        raise TypeError("lifecycle_context expected name to be a symbol")
    while current is not None:
        if name.name in current._contexts:
            return GeniaOptionSome(current._contexts[name.name])
        current = current._parent
    return make_none("lifecycle-context-absent")


def _run_scope(
    parent: ExecutionScope | None,
    kind: str,
    peers: Any,
    work: Any,
    *,
    invoke: Invoke,
    is_callable: CallableCheck,
) -> GeniaMap:
    instances = _validate_inputs(parent, peers, work, is_callable=is_callable)
    scope = ExecutionScope(parent, kind)
    scope._instances = instances
    primary: GeniaMap | None = None
    cleanup_failures: list[GeniaMap] = []
    result_value: Any = make_none("lifecycle-no-result")
    work_returned = False

    try:
        scope._state = "entering"
        for instance in instances:
            try:
                outcome = invoke(instance.enter, [scope])
            except Exception as error:
                primary = _exception_failure(error, instance.name, "enter")
                break
            if isinstance(outcome, GeniaOptionErr):
                primary = _outcome_failure(outcome, instance.name, "enter")
                break
            if not isinstance(outcome, GeniaOptionSome):
                primary = _message_failure(
                    instance.name,
                    "enter",
                    "lifecycle enter must return some(...) or err(...)",
                )
                break
            instance.entered = True
            scope._contexts[instance.name.name] = outcome.value

        if primary is None:
            scope._state = "active"
            scope._in_work = True
            try:
                result_value = invoke(work, [scope])
                work_returned = True
            except Exception as error:
                primary = _exception_failure(error, None, "work")
            finally:
                scope._in_work = False

        entered = [instance for instance in instances if instance.entered]
        if entered:
            scope._state = "exiting"
        elif primary is None:
            scope._state = "exiting"

        for instance in reversed(entered):
            summary = _primary_summary(primary)
            try:
                outcome = invoke(instance.exit, [scope, summary])
            except Exception as error:
                failure = _exception_failure(error, instance.name, "exit")
            else:
                if isinstance(outcome, GeniaOptionErr):
                    failure = _outcome_failure(outcome, instance.name, "exit")
                elif isinstance(outcome, GeniaOptionSome) and outcome.value == "nil":
                    failure = None
                else:
                    failure = _message_failure(
                        instance.name,
                        "exit",
                        'lifecycle exit must return some("nil") or err(...)',
                    )
            if failure is not None:
                if primary is None:
                    primary = failure
                else:
                    cleanup_failures.append(failure)

        scope._state = "completed" if primary is None else "failed"
        return _result(scope, primary, cleanup_failures, result_value, work_returned)
    finally:
        if scope._state not in {"completed", "failed"}:
            scope._state = "failed"
        scope._in_work = False


def _validate_inputs(
    parent: ExecutionScope | None,
    peers: Any,
    work: Any,
    *,
    is_callable: CallableCheck,
) -> list[_LifecycleInstance]:
    if not isinstance(peers, list):
        raise TypeError("lifecycle_scope expected peers to be a list")
    if not is_callable(work):
        raise TypeError("lifecycle scope expected work to be callable")

    ancestor_names: set[str] = set()
    current = parent
    while current is not None:
        ancestor_names.update(current._contexts)
        current = current._parent

    names: set[str] = set()
    instances: list[_LifecycleInstance] = []
    for index, peer in enumerate(peers):
        if not isinstance(peer, GeniaMap):
            raise TypeError(f"lifecycle peer {index} expected a closed lifecycle definition")
        raw_fields = [key for key, _value in peer.items()]
        if not all(isinstance(key, str) for key in raw_fields) or set(raw_fields) != _DEFINITION_FIELDS:
            raise TypeError(f"lifecycle peer {index} expected a closed lifecycle definition")
        name = peer.get("name")
        enter = peer.get("enter")
        exit = peer.get("exit")
        if not isinstance(name, GeniaSymbol):
            raise TypeError(f"lifecycle peer {index} name expected a symbol")
        if not is_callable(enter) or not is_callable(exit):
            raise TypeError(f"lifecycle peer {index} enter and exit must be callable")
        if name.name in names:
            raise ValueError(f"duplicate lifecycle peer name: {name.name}")
        if name.name in ancestor_names:
            raise ValueError(f"lifecycle peer name collides with ancestor lifecycle context: {name.name}")
        names.add(name.name)
        instances.append(_LifecycleInstance(name, enter, exit))
    return instances


def _require_scope(value: Any) -> ExecutionScope:
    if not isinstance(value, ExecutionScope):
        raise TypeError("expected an execution scope handle")
    return value


def _require_live(scope: ExecutionScope) -> None:
    if scope._state not in _LIVE_STATES:
        raise RuntimeError("lifecycle-scope-expired")


def _failure(peer: GeniaSymbol | None, phase: str, reason: str, context: GeniaMap) -> GeniaMap:
    return _record(
        peer=GeniaOptionSome(peer) if peer is not None else make_none("lifecycle-no-peer"),
        phase=symbol(phase),
        reason=reason,
        context=context,
    )


def _message_failure(peer: GeniaSymbol | None, phase: str, reason: str) -> GeniaMap:
    return _failure(peer, phase, reason, GeniaMap())


def _outcome_failure(outcome: GeniaOptionErr, peer: GeniaSymbol, phase: str) -> GeniaMap:
    reason = outcome.reason if isinstance(outcome.reason, str) else str(outcome.reason)
    context = outcome.context if isinstance(outcome.context, GeniaMap) else GeniaMap()
    return _failure(peer, phase, reason, context)


def _exception_failure(error: Exception, peer: GeniaSymbol | None, phase: str) -> GeniaMap:
    supplied_reason = getattr(error, "reason", None)
    reason = supplied_reason if isinstance(supplied_reason, str) else str(error)
    if not reason:
        reason = "lifecycle callback failed"
    supplied_context = getattr(error, "context", None)
    context = supplied_context if isinstance(supplied_context, GeniaMap) else GeniaMap()
    return _failure(peer, phase, reason, context)


def _primary_summary(primary: GeniaMap | None) -> GeniaMap:
    if primary is None:
        return _record(
            status=symbol("ok"),
            phase=symbol("exit"),
            peer=make_none("lifecycle-no-peer"),
        )
    return _record(
        status=symbol("error"),
        phase=primary.get("phase"),
        peer=primary.get("peer"),
    )


def _result(
    scope: ExecutionScope,
    primary: GeniaMap | None,
    cleanup_failures: list[GeniaMap],
    result_value: Any,
    work_returned: bool,
) -> GeniaMap:
    if primary is None:
        phase = symbol("exit")
        peer = make_none("lifecycle-no-peer")
        primary_value: Any = make_none("lifecycle-no-failure")
    else:
        phase = primary.get("phase")
        peer = primary.get("peer")
        primary_value = primary
    return _record(
        status=symbol("ok" if primary is None else "error"),
        state=symbol("completed" if primary is None else "failed"),
        scope=symbol(scope._kind),
        phase=phase,
        peer=peer,
        result=GeniaOptionSome(result_value) if work_returned else make_none("lifecycle-no-result"),
        primary_failure=primary_value,
        cleanup_failures=cleanup_failures,
    )
