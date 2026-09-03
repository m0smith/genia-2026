import importlib

import pytest

from genia import make_global_env, run_source
from genia.values import GeniaMap, GeniaOptionErr, GeniaOptionNone, GeniaOptionSome, symbol


RESULT_KEYS = [
    "status",
    "state",
    "scope",
    "phase",
    "peer",
    "result",
    "primary_failure",
    "cleanup_failures",
]


def _runtime():
    return importlib.import_module("genia.lifecycle_runtime")


def _record(**fields):
    value = GeniaMap()
    for key, item in fields.items():
        value = value.put(key, item)
    return value


def _peer(name, enter, exit):
    return _record(name=symbol(name), enter=enter, exit=exit)


def _invoke(fn, args):
    return fn(*args)


def _keys(value):
    return [key for key, _item in value.items()]


def _run_root(peers, work):
    return _runtime().run_lifecycle_scope(peers, work, invoke=_invoke)


def _run_child(parent, peers, work):
    return _runtime().run_lifecycle_child(parent, peers, work, invoke=_invoke)


def test_empty_root_scope_returns_exact_completed_result():
    result = _run_root([], lambda _scope: 42)

    assert _keys(result) == RESULT_KEYS
    assert result.get("status") == symbol("ok")
    assert result.get("state") == symbol("completed")
    assert result.get("scope") == symbol("root")
    assert result.get("phase") == symbol("exit")
    assert result.get("peer") == GeniaOptionNone("lifecycle-no-peer")
    assert result.get("result") == GeniaOptionSome(42)
    assert result.get("primary_failure") == GeniaOptionNone("lifecycle-no-failure")
    assert result.get("cleanup_failures") == []


def test_work_outcome_is_ordinary_result_data():
    work_value = GeniaOptionErr(symbol("application-error"), _record(row=3))

    result = _run_root([], lambda _scope: work_value)

    assert result.get("status") == symbol("ok")
    assert result.get("result") == GeniaOptionSome(work_value)


def test_parent_child_context_is_inherited_and_child_finishes_before_parent():
    calls = []

    parent = _peer(
        "request",
        lambda _scope: calls.append("parent.enter") or GeniaOptionSome(_record(id="r-1")),
        lambda _scope, _summary: calls.append("parent.exit") or GeniaOptionSome("nil"),
    )
    child = _peer(
        "operation",
        lambda _scope: calls.append("child.enter") or GeniaOptionSome("op"),
        lambda _scope, _summary: calls.append("child.exit") or GeniaOptionSome("nil"),
    )

    def parent_work(parent_scope):
        calls.append("parent.work.before")

        def child_work(child_scope):
            calls.append("child.work")
            return _runtime().lifecycle_context(child_scope, symbol("request"))

        child_result = _run_child(parent_scope, [child], child_work)
        calls.append("parent.work.after")
        return child_result

    result = _run_root([parent], parent_work)
    child_result = result.get("result").value

    assert calls == [
        "parent.enter",
        "parent.work.before",
        "child.enter",
        "child.work",
        "child.exit",
        "parent.work.after",
        "parent.exit",
    ]
    assert child_result.get("scope") == symbol("child")
    assert child_result.get("status") == symbol("ok")
    inherited = child_result.get("result").value
    assert isinstance(inherited, GeniaOptionSome)
    assert inherited.value.get("id") == "r-1"


def test_child_failure_is_contained_and_parent_completes():
    def parent_work(parent_scope):
        return _run_child(parent_scope, [], lambda _child: (_ for _ in ()).throw(RuntimeError("child failed")))

    parent_result = _run_root([], parent_work)
    child_result = parent_result.get("result").value

    assert parent_result.get("status") == symbol("ok")
    assert child_result.get("status") == symbol("error")
    assert child_result.get("phase") == symbol("work")
    assert child_result.get("primary_failure").get("reason") == "child failed"


def test_child_failure_propagation_requires_parent_to_raise():
    def parent_work(parent_scope):
        child = _run_child(parent_scope, [], lambda _child: (_ for _ in ()).throw(RuntimeError("child failed")))
        if child.get("status") == symbol("error"):
            raise RuntimeError("parent chose propagation")
        return child

    result = _run_root([], parent_work)

    assert result.get("status") == symbol("error")
    assert result.get("phase") == symbol("work")
    assert result.get("primary_failure").get("reason") == "parent chose propagation"


def test_nested_grandchild_reads_nearest_ancestor_context():
    root_peer = _peer("root_context", lambda _scope: GeniaOptionSome("root"), lambda *_: GeniaOptionSome("nil"))
    child_peer = _peer("child_context", lambda _scope: GeniaOptionSome("child"), lambda *_: GeniaOptionSome("nil"))

    def root_work(root_scope):
        return _run_child(
            root_scope,
            [child_peer],
            lambda child_scope: _run_child(
                child_scope,
                [],
                lambda grandchild: [
                    _runtime().lifecycle_context(grandchild, symbol("root_context")),
                    _runtime().lifecycle_context(grandchild, symbol("child_context")),
                ],
            ),
        )

    result = _run_root([root_peer], root_work)
    grandchild = result.get("result").value.get("result").value

    assert grandchild.get("scope") == symbol("child")
    assert grandchild.get("result") == GeniaOptionSome([GeniaOptionSome("root"), GeniaOptionSome("child")])


def test_context_absence_is_none_and_expired_handle_fails_loudly():
    captured = []
    result = _run_root([], lambda scope: captured.append(scope) or _runtime().lifecycle_context(scope, symbol("missing")))

    assert result.get("result") == GeniaOptionSome(GeniaOptionNone("lifecycle-context-absent"))
    with pytest.raises(RuntimeError, match="lifecycle-scope-expired"):
        _runtime().lifecycle_context(captured[0], symbol("missing"))


def test_partial_entry_skips_failed_peer_and_work_then_unwinds_entered_only():
    calls = []
    first = _peer(
        "first",
        lambda _scope: calls.append("first.enter") or GeniaOptionSome("one"),
        lambda _scope, summary: calls.append(("first.exit", summary)) or GeniaOptionSome("nil"),
    )
    second = _peer(
        "second",
        lambda _scope: calls.append("second.enter") or GeniaOptionErr("enter failed", _record(step=2)),
        lambda *_: calls.append("second.exit") or GeniaOptionSome("nil"),
    )
    third = _peer(
        "third",
        lambda _scope: calls.append("third.enter") or GeniaOptionSome("three"),
        lambda *_: calls.append("third.exit") or GeniaOptionSome("nil"),
    )

    result = _run_root([first, second, third], lambda _scope: calls.append("work"))

    assert [call if isinstance(call, str) else call[0] for call in calls] == [
        "first.enter",
        "second.enter",
        "first.exit",
    ]
    assert result.get("phase") == symbol("enter")
    assert result.get("peer") == GeniaOptionSome(symbol("second"))
    assert result.get("result") == GeniaOptionNone("lifecycle-no-result")
    primary = result.get("primary_failure")
    assert primary.get("reason") == "enter failed"
    assert primary.get("context").get("step") == 2


def test_reverse_unwind_promotes_first_exit_failure_and_records_later_failures():
    calls = []

    def peer(name):
        return _peer(
            name,
            lambda _scope, name=name: calls.append(f"{name}.enter") or GeniaOptionSome(name),
            lambda _scope, _summary, name=name: calls.append(f"{name}.exit")
            or GeniaOptionErr(f"{name} exit failed", _record(name=name)),
        )

    result = _run_root([peer("a"), peer("b")], lambda _scope: calls.append("work") or "done")

    assert calls == ["a.enter", "b.enter", "work", "b.exit", "a.exit"]
    assert result.get("phase") == symbol("exit")
    assert result.get("peer") == GeniaOptionSome(symbol("b"))
    assert result.get("result") == GeniaOptionSome("done")
    assert result.get("primary_failure").get("reason") == "b exit failed"
    assert [failure.get("reason") for failure in result.get("cleanup_failures")] == ["a exit failed"]


def test_work_failure_stays_primary_when_cleanup_also_fails():
    peer = _peer(
        "cleanup",
        lambda _scope: GeniaOptionSome("owned"),
        lambda _scope, summary: GeniaOptionErr("cleanup failed", summary),
    )

    result = _run_root([peer], lambda _scope: (_ for _ in ()).throw(ValueError("work failed")))

    assert result.get("primary_failure").get("reason") == "work failed"
    assert result.get("primary_failure").get("phase") == symbol("work")
    assert [failure.get("reason") for failure in result.get("cleanup_failures")] == ["cleanup failed"]


@pytest.mark.parametrize(
    ("peers", "message"),
    [
        ("not-a-list", "lifecycle_scope expected peers to be a list"),
        ([_record(name=symbol("x"), enter=lambda _: GeniaOptionSome(1))], "closed lifecycle definition"),
        ([_peer("x", lambda _: GeniaOptionSome(1), lambda *_: GeniaOptionSome("nil")), _peer("x", lambda _: GeniaOptionSome(2), lambda *_: GeniaOptionSome("nil"))], "duplicate lifecycle peer name"),
    ],
)
def test_invalid_definitions_fail_before_any_entry(peers, message):
    with pytest.raises((TypeError, ValueError), match=message):
        _run_root(peers, lambda _scope: "work")


def test_child_cannot_shadow_ancestor_context():
    parent = _peer("shared", lambda _scope: GeniaOptionSome("parent"), lambda *_: GeniaOptionSome("nil"))
    child = _peer("shared", lambda _scope: GeniaOptionSome("child"), lambda *_: GeniaOptionSome("nil"))

    result = _run_root([parent], lambda parent_scope: _run_child(parent_scope, [child], lambda _scope: "work"))

    assert result.get("status") == symbol("error")
    assert result.get("phase") == symbol("work")
    assert "ancestor lifecycle context" in result.get("primary_failure").get("reason")


def test_child_requires_parent_active_work_and_rejects_expired_handle():
    captured = []
    _run_root([], lambda scope: captured.append(scope) or "done")

    with pytest.raises(RuntimeError, match="lifecycle-scope-expired"):
        _run_child(captured[0], [], lambda _scope: "never")


def test_invalid_callback_outcomes_are_lifecycle_failures_and_cleanup_continues():
    calls = []
    invalid_enter = _peer("bad", lambda _scope: "not-outcome", lambda *_: calls.append("bad.exit"))

    enter_result = _run_root([invalid_enter], lambda _scope: calls.append("work"))

    assert enter_result.get("status") == symbol("error")
    assert enter_result.get("phase") == symbol("enter")
    assert "must return some(...) or err(...)" in enter_result.get("primary_failure").get("reason")
    assert calls == []

    invalid_exit = _peer(
        "bad",
        lambda _scope: GeniaOptionSome("owned"),
        lambda *_: calls.append("bad.exit") or "not-outcome",
    )
    exit_result = _run_root([invalid_exit], lambda _scope: "done")
    assert exit_result.get("phase") == symbol("exit")
    assert "must return" in exit_result.get("primary_failure").get("reason")
    assert "err(...)" in exit_result.get("primary_failure").get("reason")
    assert calls == ["bad.exit"]


def test_public_builtins_execute_ordinary_genia_call_forms():
    source = """
peer = {
  name: quote(request),
  enter: (_) -> some({id: "r-1"}),
  exit: (_, _) -> some("nil")
}

lifecycle_scope([peer], (parent) ->
  lifecycle_child(parent, [], (child) -> lifecycle_context(child, quote(request)))
)
"""

    result = run_source(source, make_global_env([]))
    child_result = result.get("result").value

    assert result.get("status") == symbol("ok")
    assert child_result.get("status") == symbol("ok")
    inherited = child_result.get("result").value
    assert isinstance(inherited, GeniaOptionSome)
    assert inherited.value.get("id") == "r-1"


def test_scope_handle_debug_representation_is_opaque():
    result = run_source(
        "lifecycle_scope([], (scope) -> debug_repr(scope))",
        make_global_env([]),
    )

    rendered = result.get("result").value
    assert rendered == "<execution-scope>"
    assert "parent" not in rendered
    assert "context" not in rendered
