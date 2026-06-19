import importlib
from collections.abc import Callable

from genia.lifecycle_plan import normalize_lifecycle_plan, validate_lifecycle_plan
from genia.lifecycle_scope import (
    normalize_lifecycle_scope_tree,
    validate_lifecycle_scope_tree,
)
from genia.values import GeniaMap, GeniaOptionSome, OPTION_NONE, symbol


def _native_test_lifecycle_module():
    return importlib.import_module("genia.native_test_lifecycle")


def _plan():
    return _native_test_lifecycle_module().native_test_lifecycle_plan()


def _scope_tree():
    return _native_test_lifecycle_module().native_test_lifecycle_scope_tree()


def _phase_names(plan):
    return [phase.get("name") for phase in plan.get("phases")]


def _scope_names(scope_tree):
    return [scope.get("name") for scope in scope_tree.get("scopes")]


def _parent_name(parent):
    if parent == OPTION_NONE:
        return None
    if isinstance(parent, GeniaOptionSome):
        return parent.value
    raise AssertionError(f"unexpected parent value: {parent!r}")


def test_native_test_lifecycle_plan_returns_plan_shaped_inert_data():
    plan = _plan()

    assert isinstance(plan, GeniaMap)
    assert plan.get("name") == symbol("native_test_lifecycle")
    assert isinstance(plan.get("phases"), list)
    assert all(isinstance(phase, GeniaMap) for phase in plan.get("phases"))
    assert all(
        not isinstance(phase.get("action"), Callable)
        for phase in plan.get("phases")
    )


def test_native_test_lifecycle_plan_validates_through_existing_plan_helpers():
    plan = _plan()

    assert validate_lifecycle_plan(plan) is None
    normalized = normalize_lifecycle_plan(plan)

    assert isinstance(normalized, GeniaMap)
    assert _phase_names(normalized) == [
        symbol("discover"),
        symbol("run"),
        symbol("report"),
    ]


def test_native_test_lifecycle_plan_phase_names_are_exactly_discover_run_report():
    normalized = normalize_lifecycle_plan(_plan())

    assert _phase_names(normalized) == [
        symbol("discover"),
        symbol("run"),
        symbol("report"),
    ]


def test_native_test_lifecycle_scope_tree_returns_scope_tree_shaped_inert_data():
    scope_tree = _scope_tree()

    assert isinstance(scope_tree, GeniaMap)
    assert isinstance(scope_tree.get("scopes"), list)
    assert all(isinstance(scope, GeniaMap) for scope in scope_tree.get("scopes"))
    assert all(
        not isinstance(scope.get("metadata"), Callable)
        for scope in scope_tree.get("scopes")
    )


def test_native_test_lifecycle_scope_tree_validates_through_existing_scope_helpers():
    scope_tree = _scope_tree()

    assert validate_lifecycle_scope_tree(scope_tree) is None
    normalized = normalize_lifecycle_scope_tree(scope_tree)

    assert isinstance(normalized, GeniaMap)
    assert _scope_names(normalized) == [
        symbol("execution"),
        symbol("suite"),
        symbol("module"),
        symbol("test"),
    ]


def test_native_test_lifecycle_scope_hierarchy_is_exactly_execution_suite_module_test():
    normalized = normalize_lifecycle_scope_tree(_scope_tree())
    scopes_by_name = {scope.get("name"): scope for scope in normalized.get("scopes")}

    assert _parent_name(scopes_by_name[symbol("execution")].get("parent")) is None
    assert _parent_name(scopes_by_name[symbol("suite")].get("parent")) == symbol(
        "execution"
    )
    assert _parent_name(scopes_by_name[symbol("module")].get("parent")) == symbol(
        "suite"
    )
    assert _parent_name(scopes_by_name[symbol("test")].get("parent")) == symbol(
        "module"
    )
    assert scopes_by_name[symbol("execution")].get("children") == [symbol("suite")]
    assert scopes_by_name[symbol("suite")].get("children") == [symbol("module")]
    assert scopes_by_name[symbol("module")].get("children") == [symbol("test")]
    assert scopes_by_name[symbol("test")].get("children") == []


def test_validate_native_test_lifecycle_returns_validated_plan_and_scope_tree():
    validated = _native_test_lifecycle_module().validate_native_test_lifecycle()

    assert isinstance(validated, GeniaMap)
    assert validated.has("plan")
    assert validated.has("scope_tree")
    assert _phase_names(validated.get("plan")) == [
        symbol("discover"),
        symbol("run"),
        symbol("report"),
    ]
    assert _scope_names(validated.get("scope_tree")) == [
        symbol("execution"),
        symbol("suite"),
        symbol("module"),
        symbol("test"),
    ]


def test_native_test_lifecycle_descriptor_actions_are_identifiers_not_callables():
    normalized = normalize_lifecycle_plan(_plan())

    assert [phase.get("action") for phase in normalized.get("phases")] == [
        symbol("discover_tests"),
        symbol("run_tests"),
        symbol("report_results"),
    ]
    assert all(
        not isinstance(phase.get("action"), Callable)
        for phase in normalized.get("phases")
    )


def test_native_test_lifecycle_descriptor_does_not_expose_phase_execution_api():
    lifecycle = _native_test_lifecycle_module()

    assert not hasattr(lifecycle, "run_lifecycle_phase")
    assert not hasattr(lifecycle, "execute_lifecycle_plan")
    assert not hasattr(lifecycle, "discover_lifecycle_participants")
