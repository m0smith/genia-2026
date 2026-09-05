"""Focused tests for the R14 E14-3 ``lifecycle_repeat`` builtin (issue #693):
eager (List) and lazy (Flow) dispatch, reserved ``element``/``index``
context, deterministic per-element peer ordering, and early-termination
cleanup, per docs/design/r14-composable-lifecycle-contract.md's "Repeated
element-scoped execution" section.

These tests exercise ``lifecycle_repeat`` through real Genia source via
``run_source``, using the same ``GeniaFlow``-fixture style already
established by ``tests/unit/test_flow_phase1.py`` (a Python-side pull/close
counter injected as a host function), since the Flow-vs-List dispatch lives
in ``genia.builtins``, not ``genia.lifecycle_runtime``. See
``tests/unit/test_lifecycle_runtime.py`` for the Flow-free
``run_lifecycle_element`` core tests.
"""

from __future__ import annotations

import pytest

from genia import make_global_env, run_source
from genia.interpreter import GeniaFlow
from genia.values import GeniaOptionErr, GeniaOptionNone


class _CountingCloser:
    """Iterator counting pulls/closes, to prove no-over-pull and close-once."""

    def __init__(self, state, *, limit=1000):
        self._state = state
        self._limit = limit
        self._next = 0
        self._closed = False

    def __iter__(self):
        return self

    def __next__(self):
        if self._next >= self._limit:
            raise StopIteration
        value = self._next
        self._next += 1
        self._state["pulled"] += 1
        return value

    def close(self):
        if self._closed:
            return
        self._closed = True
        self._state["closed"] += 1


def _counting_env(*, limit=1000):
    env = make_global_env()
    state = {"pulled": 0, "closed": 0}

    def ticks():
        return GeniaFlow(lambda: _CountingCloser(state, limit=limit), label="ticks")

    env.set("ticks", ticks)
    return env, state


def _values_flow_env(values):
    env = make_global_env()

    def numbers():
        return GeniaFlow(lambda: iter(values), label="numbers")

    env.set("numbers", numbers)
    return env


# --- eager (List) dispatch ---------------------------------------------


def test_lifecycle_repeat_eager_list_every_element_gets_its_own_element_scope():
    env = make_global_env()
    src = """
    peers = [{name: quote(cfg), enter: (h) -> some("ctx"), exit: (h, s) -> some("nil")}]
    work(h) = [
      unwrap_or(none, lifecycle_context(h, quote(element))),
      unwrap_or(none, lifecycle_context(h, quote(index)))
    ]
    results = lifecycle_repeat(peers, ["x", "y", "z"], work)
    [
      length(results),
      results |> map((r) -> r.scope == quote(element)),
      results |> map((r) -> r.status == quote(ok)),
      results |> map((r) -> unwrap_or(none, r.result))
    ]
    """
    count, all_element_scope, all_ok, elements = run_source(src, env)

    assert count == 3
    assert all_element_scope == [True, True, True]
    assert all_ok == [True, True, True]
    assert elements == [["x", 1], ["y", 2], ["z", 3]]


def test_lifecycle_repeat_eager_list_individual_failure_does_not_skip_other_elements():
    env = make_global_env()
    src = """
    maybe_fail(idx) =
      2 -> 1 / 0 |
      _ -> "fine"
    work(h) = maybe_fail(unwrap_or(0, lifecycle_context(h, quote(index))))
    results = lifecycle_repeat([], [10, 20, 30], work)
    results |> map((r) -> r.status == quote(ok))
    """
    statuses = run_source(src, env)

    assert statuses == [True, False, True]


def test_lifecycle_repeat_eager_list_two_peers_enter_work_unwind_order_per_element():
    env = make_global_env()
    src = """
    calls = ref([])
    push(tag) = ref_set(calls, ref_get(calls) + [tag])
    peers = [
      {name: quote(a), enter: (h) -> { push("A.enter") some("a") }, exit: (h, s) -> { push("A.exit") some("nil") }},
      {name: quote(b), enter: (h) -> { push("B.enter") some("b") }, exit: (h, s) -> { push("B.exit") some("nil") }}
    ]
    work(h) = push("work")
    lifecycle_repeat(peers, [10, 20], work)
    ref_get(calls)
    """
    calls = run_source(src, env)

    assert calls == [
        "A.enter", "B.enter", "work", "B.exit", "A.exit",
        "A.enter", "B.enter", "work", "B.exit", "A.exit",
    ]


def test_lifecycle_repeat_peer_named_element_is_rejected_before_any_enter():
    env = make_global_env()
    src = """
    calls = ref([])
    push(tag) = ref_set(calls, ref_get(calls) + [tag])
    peers = [{name: quote(element), enter: (h) -> { push("entered") some("bad") }, exit: (h, s) -> some("nil")}]
    lifecycle_repeat(peers, [1, 2], (h) -> "unreachable")
    """
    with pytest.raises(TypeError):
        run_source(src, env)


def test_lifecycle_repeat_peer_named_index_is_rejected_before_any_enter():
    env = make_global_env()
    src = """
    peers = [{name: quote(index), enter: (h) -> some("bad"), exit: (h, s) -> some("nil")}]
    lifecycle_repeat(peers, [1, 2], (h) -> "unreachable")
    """
    with pytest.raises(TypeError):
        run_source(src, env)


def test_lifecycle_repeat_no_cross_element_context_leakage():
    env = make_global_env()
    src = """
    label_for(idx) =
      1 -> some("first-only") |
      _ -> some("later")
    peers = [{
      name: quote(seen_by),
      enter: (h) -> label_for(unwrap_or(0, lifecycle_context(h, quote(index)))),
      exit: (h, s) -> some("nil")
    }]
    work(h) = unwrap_or(none, lifecycle_context(h, quote(seen_by)))
    results = lifecycle_repeat(peers, [10, 20], work)
    results |> map((r) -> unwrap_or(none, r.result))
    """
    values = run_source(src, env)

    assert values == ["first-only", "later"]


def test_lifecycle_repeat_element_work_returning_option_or_outcome_is_ordinary_result():
    env = make_global_env()
    src = """
    work(h) =
      1 -> none |
      idx -> err("bad-row", {index: idx})
    results = lifecycle_repeat([], [1, 2], (h) -> work(unwrap_or(0, lifecycle_context(h, quote(index)))))
    [
      results |> map((r) -> r.status == quote(ok)),
      results |> map((r) -> unwrap_or("MISSING", r.result))
    ]
    """
    statuses, results = run_source(src, env)

    assert statuses == [True, True]
    assert isinstance(results[0], GeniaOptionNone)
    assert isinstance(results[1], GeniaOptionErr)
    assert results[1].reason == "bad-row"


def test_lifecycle_repeat_empty_list_returns_empty_list():
    env = make_global_env()
    src = 'lifecycle_repeat([], [], (h) -> "unreachable")'

    assert run_source(src, env) == []


def test_lifecycle_repeat_malformed_source_raises_seq_compatible_error():
    env = make_global_env()
    src = 'lifecycle_repeat([], "not-a-seq", (h) -> "unreachable")'

    with pytest.raises(TypeError):
        run_source(src, env)


# --- lazy (Flow) dispatch -----------------------------------------------


def test_lifecycle_repeat_over_flow_returns_a_flow_not_a_list():
    env, state = _counting_env()
    src = """
    flow_of_results = lifecycle_repeat([], ticks(), (h) -> "touched")
    _flow?(flow_of_results)
    """
    is_flow = run_source(src, env)

    assert is_flow is True
    assert state["pulled"] == 0


def test_lifecycle_repeat_lazy_flow_defers_all_work_until_pulled():
    env, state = _counting_env()
    src = """
    lifecycle_repeat([], ticks(), (h) -> "touched")
    "constructed"
    """
    run_source(src, env)

    assert state["pulled"] == 0
    assert state["closed"] == 0


def test_lifecycle_repeat_lazy_flow_pulls_exactly_n_elements_for_take_n():
    env, state = _counting_env()
    src = """
    results = lifecycle_repeat([], ticks(), (h) -> "touched") |> take(3) |> collect
    [length(results), results |> map((r) -> r.scope == quote(element))]
    """
    count, all_element_scope = run_source(src, env)

    assert count == 3
    assert all_element_scope == [True, True, True]
    assert state["pulled"] == 3
    assert state["closed"] == 1


def test_lifecycle_repeat_lazy_flow_index_is_pull_ordinal():
    env = _values_flow_env(["p", "q", "r"])
    src = """
    work(h) = unwrap_or(0, lifecycle_context(h, quote(index)))
    results = lifecycle_repeat([], numbers(), work) |> collect
    results |> map((r) -> unwrap_or(none, r.result))
    """
    indices = run_source(src, env)

    assert indices == [1, 2, 3]


def test_lifecycle_repeat_lazy_flow_two_peers_per_element_close_before_next_pull():
    env = _values_flow_env([10, 20])
    src = """
    calls = ref([])
    push(tag) = ref_set(calls, ref_get(calls) + [tag])
    peers = [
      {name: quote(a), enter: (h) -> { push("A.enter") some("a") }, exit: (h, s) -> { push("A.exit") some("nil") }},
      {name: quote(b), enter: (h) -> { push("B.enter") some("b") }, exit: (h, s) -> { push("B.exit") some("nil") }}
    ]
    work(h) = push("work")
    lifecycle_repeat(peers, numbers(), work) |> collect
    ref_get(calls)
    """
    calls = run_source(src, env)

    assert calls == [
        "A.enter", "B.enter", "work", "B.exit", "A.exit",
        "A.enter", "B.enter", "work", "B.exit", "A.exit",
    ]


def test_lifecycle_repeat_lazy_flow_empty_source_yields_nothing():
    env = _values_flow_env([])
    src = 'lifecycle_repeat([], numbers(), (h) -> "unreachable") |> collect'

    assert run_source(src, env) == []
