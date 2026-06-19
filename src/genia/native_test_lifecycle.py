"""Native test lifecycle contract consumer.

This module describes the existing native test path as inert R4 lifecycle
plan/scope data. It does not execute lifecycle phases or change native test
behavior.
"""

from __future__ import annotations

from .lifecycle_plan import normalize_lifecycle_plan
from .lifecycle_scope import normalize_lifecycle_scope_tree
from .values import GeniaMap, GeniaOptionSome, OPTION_NONE, symbol


def _record(**fields: object) -> GeniaMap:
    record = GeniaMap()
    for key, value in fields.items():
        record = record.put(key, value)
    return record


def _phase(name: str, action: str) -> GeniaMap:
    return _record(name=symbol(name), action=symbol(action))


def _scope(name: str, parent: object, children: list[str]) -> GeniaMap:
    return _record(
        name=symbol(name),
        parent=parent,
        children=[symbol(child) for child in children],
    )


def native_test_lifecycle_plan() -> GeniaMap:
    """Return inert lifecycle plan data for the current native test path."""

    return _record(
        name=symbol("native_test_lifecycle"),
        phases=[
            _phase("discover", "discover_tests"),
            _phase("run", "run_tests"),
            _phase("report", "report_results"),
        ],
    )


def native_test_lifecycle_scope_tree() -> GeniaMap:
    """Return inert lifecycle scope-tree data for the native test path."""

    return _record(
        scopes=[
            _scope("execution", OPTION_NONE, ["suite"]),
            _scope("suite", GeniaOptionSome(symbol("execution")), ["module"]),
            _scope("module", GeniaOptionSome(symbol("suite")), ["test"]),
            _scope("test", GeniaOptionSome(symbol("module")), []),
        ],
    )


def validate_native_test_lifecycle() -> GeniaMap:
    """Validate and return normalized native-test lifecycle descriptor data."""

    plan = normalize_lifecycle_plan(native_test_lifecycle_plan())
    scope_tree = normalize_lifecycle_scope_tree(native_test_lifecycle_scope_tree())
    return _record(plan=plan, scope_tree=scope_tree)
