"""Focused tests for the R14 E14-1 lifecycle instance/scope core (issue #621).

Exercises the entry/work/unwind algorithm, the scope lifetime state machine,
and vertical (parent/child) composition locked by
docs/design/r14-composable-lifecycle-contract.md, against
``genia.lifecycle_runtime`` directly with a trivial injected invoker — the
same dependency-injection style already used by
``tests/unit/test_server_lifecycle.py``.
"""

from __future__ import annotations

import pytest

from genia.lifecycle_runtime import (
    lookup_lifecycle_context,
    run_lifecycle_child,
    run_lifecycle_scope,
)
from genia.values import GeniaMap, GeniaOptionErr, GeniaOptionNone, GeniaOptionSome, symbol


def _invoke(fn, args):
    return fn(*args)


def _peer(name, enter, exit_):
    return GeniaMap().put("name", symbol(name)).put("enter", enter).put("exit", exit_)


def _ok_enter(value="ctx", calls=None, tag=None):
    def enter(handle):
        if calls is not None:
            calls.append(f"{tag}.enter")
        return GeniaOptionSome(value)

    return enter


def _ok_exit(calls=None, tag=None):
    def exit_(handle, summary):
        if calls is not None:
            calls.append(f"{tag}.exit")
        return GeniaOptionSome("nil")

    return exit_


def _err_enter(reason="enter-fail", calls=None, tag=None):
    def enter(handle):
        if calls is not None:
            calls.append(f"{tag}.enter")
        return GeniaOptionErr(reason, GeniaMap())

    return enter


def _err_exit(reason="exit-fail", calls=None, tag=None):
    def exit_(handle, summary):
        if calls is not None:
            calls.append(f"{tag}.exit")
        return GeniaOptionErr(reason, GeniaMap())

    return exit_


def _failure(result, key):
    return result.get("primary_failure").get(key)


# --- success paths -----------------------------------------------------


def test_zero_peers_success_carries_work_result():
    result = run_lifecycle_scope([], lambda handle: 42, _invoke)

    assert result.get("status") == symbol("ok")
    assert result.get("state") == symbol("completed")
    assert result.get("scope") == symbol("root")
    assert result.get("phase") == symbol("exit")
    assert isinstance(result.get("peer"), GeniaOptionNone)
    assert result.get("result") == GeniaOptionSome(42)
    assert isinstance(result.get("primary_failure"), GeniaOptionNone)
    assert result.get("cleanup_failures") == []


def test_single_peer_enters_works_and_exits_in_order():
    calls: list[str] = []
    peers = [_peer("a", _ok_enter(calls=calls, tag="A"), _ok_exit(calls=calls, tag="A"))]

    def work(handle):
        calls.append("work")
        return "done"

    result = run_lifecycle_scope(peers, work, _invoke)

    assert calls == ["A.enter", "work", "A.exit"]
    assert result.get("status") == symbol("ok")
    assert result.get("result") == GeniaOptionSome("done")


def test_two_peers_reverse_unwind_order():
    calls: list[str] = []
    peers = [
        _peer("a", _ok_enter(calls=calls, tag="A"), _ok_exit(calls=calls, tag="A")),
        _peer("b", _ok_enter(calls=calls, tag="B"), _ok_exit(calls=calls, tag="B")),
    ]

    def work(handle):
        calls.append("work")

    run_lifecycle_scope(peers, work, _invoke)

    assert calls == ["A.enter", "B.enter", "work", "B.exit", "A.exit"]


# --- enter failures ------------------------------------------------------


def test_enter_failure_on_first_peer_skips_unwind_entirely():
    calls: list[str] = []
    peers = [_peer("a", _err_enter("boom", calls=calls, tag="A"), _ok_exit(calls=calls, tag="A"))]

    result = run_lifecycle_scope(peers, lambda handle: pytest.fail("work must not run"), _invoke)

    assert calls == ["A.enter"]
    assert result.get("status") == symbol("error")
    assert result.get("state") == symbol("failed")
    assert result.get("phase") == symbol("enter")
    assert _failure(result, "peer") == GeniaOptionSome(symbol("a"))
    assert _failure(result, "reason") == "boom"
    assert result.get("cleanup_failures") == []
    assert result.get("result") == GeniaOptionNone("lifecycle-no-result")


def test_enter_failure_on_second_peer_unwinds_only_the_first():
    calls: list[str] = []
    peers = [
        _peer("a", _ok_enter(calls=calls, tag="A"), _ok_exit(calls=calls, tag="A")),
        _peer("b", _err_enter("nope", calls=calls, tag="B"), _ok_exit(calls=calls, tag="B")),
    ]

    result = run_lifecycle_scope(peers, lambda handle: pytest.fail("work must not run"), _invoke)

    assert calls == ["A.enter", "B.enter", "A.exit"]
    assert _failure(result, "peer") == GeniaOptionSome(symbol("b"))
    assert _failure(result, "reason") == "nope"
    assert result.get("cleanup_failures") == []


def test_enter_failure_cleanup_failure_is_appended_not_promoted():
    peers = [
        _peer("a", _ok_enter(), _err_exit("a-exit-broke")),
        _peer("b", _err_enter("b-enter-broke"), _ok_exit()),
    ]

    result = run_lifecycle_scope(peers, lambda handle: pytest.fail("work must not run"), _invoke)

    assert _failure(result, "peer") == GeniaOptionSome(symbol("b"))
    assert _failure(result, "reason") == "b-enter-broke"
    cleanup = result.get("cleanup_failures")
    assert len(cleanup) == 1
    assert cleanup[0].get("peer") == GeniaOptionSome(symbol("a"))
    assert cleanup[0].get("reason") == "a-exit-broke"


# --- work failures ---------------------------------------------------------


def test_work_raising_unwinds_all_entered_peers_and_is_primary():
    calls: list[str] = []
    peers = [_peer("a", _ok_enter(calls=calls, tag="A"), _ok_exit(calls=calls, tag="A"))]

    def work(handle):
        raise RuntimeError("boom")

    result = run_lifecycle_scope(peers, work, _invoke)

    assert calls == ["A.enter", "A.exit"]
    assert result.get("status") == symbol("error")
    assert result.get("phase") == symbol("work")
    assert isinstance(_failure(result, "peer"), GeniaOptionNone)
    assert _failure(result, "reason") == "boom"
    assert result.get("result") == GeniaOptionNone("lifecycle-no-result")


# --- exit failures -----------------------------------------------------


def test_single_exit_failure_is_promoted_and_result_is_still_carried():
    peers = [_peer("a", _ok_enter(), _err_exit("a-broke"))]

    result = run_lifecycle_scope(peers, lambda handle: "value", _invoke)

    assert result.get("status") == symbol("error")
    assert result.get("phase") == symbol("exit")
    assert _failure(result, "peer") == GeniaOptionSome(symbol("a"))
    assert _failure(result, "reason") == "a-broke"
    # D1: work succeeded, so its return value is still carried even though
    # the scope's overall outcome is failed due to a later exit failure.
    assert result.get("result") == GeniaOptionSome("value")
    assert result.get("cleanup_failures") == []


def test_two_exit_failures_first_encountered_in_unwind_is_promoted():
    peers = [
        _peer("a", _ok_enter(), _err_exit("a-broke")),
        _peer("b", _ok_enter(), _err_exit("b-broke")),
    ]

    result = run_lifecycle_scope(peers, lambda handle: None, _invoke)

    # Reverse unwind order visits B first, so B's failure is promoted and
    # A's is a cleanup failure.
    assert _failure(result, "peer") == GeniaOptionSome(symbol("b"))
    assert _failure(result, "reason") == "b-broke"
    cleanup = result.get("cleanup_failures")
    assert len(cleanup) == 1
    assert cleanup[0].get("peer") == GeniaOptionSome(symbol("a"))
    assert cleanup[0].get("reason") == "a-broke"


def test_every_entered_peer_exit_runs_exactly_once_despite_earlier_exit_failure():
    calls: list[str] = []
    peers = [
        _peer("a", _ok_enter(calls=calls, tag="A"), _ok_exit(calls=calls, tag="A")),
        _peer("b", _ok_enter(calls=calls, tag="B"), _err_exit("boom", calls=calls, tag="B")),
    ]

    run_lifecycle_scope(peers, lambda handle: None, _invoke)

    assert calls == ["A.enter", "B.enter", "B.exit", "A.exit"]


# --- vertical composition (parent/child/grandchild) ------------------------


def test_child_creation_during_enter_phase_is_rejected_but_distinct_from_expired():
    attempts: dict[str, object] = {}

    def enter(handle):
        try:
            run_lifecycle_child(handle, [], lambda h: None, _invoke)
        except RuntimeError as error:
            attempts["raised"] = True
            attempts["message"] = str(error)
        else:
            attempts["raised"] = False
        return GeniaOptionSome("v")

    peers = [_peer("a", enter, _ok_exit())]

    result = run_lifecycle_scope(peers, lambda handle: None, _invoke)

    # D3: a handle mid-"entering" is still alive (not scope-expired) but is
    # not "active", so lifecycle_child must still reject it, with a distinct
    # message from the scope-expired identifier.
    assert attempts["raised"] is True
    assert "lifecycle-scope-expired" not in attempts["message"]
    assert result.get("status") == symbol("ok")


def test_child_completes_and_returns_result_to_parent_without_raising():
    def work(handle):
        child_result = run_lifecycle_child(handle, [], lambda h: "child-value", _invoke)
        return child_result

    result = run_lifecycle_scope([], work, _invoke)

    child_result = result.get("result").value
    assert child_result.get("status") == symbol("ok")
    assert child_result.get("scope") == symbol("child")
    assert child_result.get("result") == GeniaOptionSome("child-value")


def test_child_failure_does_not_implicitly_fail_parent():
    def child_work(handle):
        raise RuntimeError("child broke")

    def work(handle):
        child_result = run_lifecycle_child(handle, [], child_work, _invoke)
        assert child_result.get("status") == symbol("error")
        return "parent survived"

    result = run_lifecycle_scope([], work, _invoke)

    assert result.get("status") == symbol("ok")
    assert result.get("result") == GeniaOptionSome("parent survived")


def test_grandchild_nesting_two_levels_beyond_parent():
    def work(handle):
        def child_work(child_handle):
            grandchild = run_lifecycle_child(child_handle, [], lambda gh: "leaf", _invoke)
            return grandchild.get("result").value

        child_result = run_lifecycle_child(handle, [], child_work, _invoke)
        return child_result.get("result").value

    result = run_lifecycle_scope([], work, _invoke)

    assert result.get("result") == GeniaOptionSome("leaf")


def test_context_read_through_from_child_to_parent():
    def enter(handle):
        return GeniaOptionSome("parent-value")

    peers = [_peer("cfg", enter, _ok_exit())]

    def work(handle):
        def child_work(child_handle):
            return lookup_lifecycle_context(child_handle, symbol("cfg"))

        child_result = run_lifecycle_child(handle, [], child_work, _invoke)
        return child_result.get("result").value

    result = run_lifecycle_scope(peers, work, _invoke)

    assert result.get("result") == GeniaOptionSome(GeniaOptionSome("parent-value"))


def test_context_lookup_absent_name_returns_none():
    def work(handle):
        return lookup_lifecycle_context(handle, symbol("missing"))

    result = run_lifecycle_scope([], work, _invoke)

    assert result.get("result") == GeniaOptionSome(GeniaOptionNone("lifecycle-context-absent"))


def test_context_not_visible_to_an_earlier_peer_only_to_later_ones_and_work():
    seen_by_a = {}

    def enter_a(handle):
        seen_by_a["b"] = lookup_lifecycle_context(handle, symbol("b"))
        return GeniaOptionSome("a-value")

    def enter_b(handle):
        return GeniaOptionSome("b-value")

    peers = [_peer("a", enter_a, _ok_exit()), _peer("b", enter_b, _ok_exit())]

    def work(handle):
        return lookup_lifecycle_context(handle, symbol("b"))

    result = run_lifecycle_scope(peers, work, _invoke)

    assert isinstance(seen_by_a["b"], GeniaOptionNone)
    assert result.get("result") == GeniaOptionSome(GeniaOptionSome("b-value"))


# --- non-shadowing / construction-time misuse -----------------------------


def test_duplicate_peer_name_in_one_list_is_rejected_before_any_enter():
    calls: list[str] = []
    peers = [
        _peer("x", _ok_enter(calls=calls, tag="X1"), _ok_exit()),
        _peer("x", _ok_enter(calls=calls, tag="X2"), _ok_exit()),
    ]

    with pytest.raises(TypeError):
        run_lifecycle_scope(peers, lambda handle: None, _invoke)
    assert calls == []


def test_child_peer_name_cannot_shadow_ancestor_context():
    peers = [_peer("x", _ok_enter(), _ok_exit())]

    def work(handle):
        child_peers = [_peer("x", _ok_enter(), _ok_exit())]
        run_lifecycle_child(handle, child_peers, lambda h: None, _invoke)
        return "unreachable"

    # The shadowing TypeError is raised synchronously inside the parent's own
    # `work` callable, so — exactly like any other exception a work callable
    # raises — it is normalized into the *parent's own* work-phase primary
    # failure rather than escaping as a raw Python exception (matching "the
    # only way work causes a lifecycle failure is by raising").
    result = run_lifecycle_scope(peers, work, _invoke)

    assert result.get("status") == symbol("error")
    assert result.get("phase") == symbol("work")
    assert "shadows context" in _failure(result, "reason")


# --- misuse / malformed shapes ---------------------------------------------


def test_peer_missing_required_field_is_rejected():
    malformed = GeniaMap().put("name", symbol("x")).put("enter", _ok_enter())

    with pytest.raises(TypeError):
        run_lifecycle_scope([malformed], lambda handle: None, _invoke)


def test_enter_must_return_some_or_err():
    def bad_enter(handle):
        return "not-an-outcome"

    peers = [_peer("x", bad_enter, _ok_exit())]

    with pytest.raises(TypeError):
        run_lifecycle_scope(peers, lambda handle: None, _invoke)


def test_exit_must_return_some_or_err():
    def bad_exit(handle, summary):
        return "not-an-outcome"

    peers = [_peer("x", _ok_enter(), bad_exit)]

    with pytest.raises(TypeError):
        run_lifecycle_scope(peers, lambda handle: None, _invoke)


def test_err_context_must_be_a_map_when_present():
    def enter_bad_context(handle):
        return GeniaOptionErr("boom", "not-a-map")

    peers = [_peer("x", enter_bad_context, _ok_exit())]

    with pytest.raises(TypeError):
        run_lifecycle_scope(peers, lambda handle: None, _invoke)


# --- scope-expired handle misuse -------------------------------------------


def test_stale_handle_after_completion_raises_on_context_lookup():
    captured = {}

    def work(handle):
        captured["handle"] = handle
        return "ok"

    run_lifecycle_scope([], work, _invoke)

    with pytest.raises(RuntimeError, match="lifecycle-scope-expired"):
        lookup_lifecycle_context(captured["handle"], symbol("anything"))


def test_stale_handle_after_completion_cannot_create_a_child():
    captured = {}

    def work(handle):
        captured["handle"] = handle
        return "ok"

    run_lifecycle_scope([], work, _invoke)

    with pytest.raises(RuntimeError):
        run_lifecycle_child(captured["handle"], [], lambda h: None, _invoke)
