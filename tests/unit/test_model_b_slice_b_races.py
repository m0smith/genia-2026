"""Deterministic writer-race regressions for Model B Slice B (#1261, review findings M1/M2).

Each test pauses one writer at a named point using a patched hook, runs the
competing writer, and then asserts the final state is a legal serialization:
exactly one of the two writers may win, never both. Every wait is bounded, so a
correct implementation (where the paused writer holds the binding lock and the
competitor blocks) still terminates. PYTHON REFERENCE HOST ONLY: these exercise
private Env APIs and are not portable source observations.
"""
import threading

import pytest

import genia
from genia import ir
from genia.environment import Env, ImmutableBindingError
from genia.evaluator import Evaluator
from genia.values import GeniaMap

WAIT = 5.0  # upper bound for any single wait; never reached on a passing run
SETTLE = 0.5  # how long to let a competitor try to proceed while a writer is paused


def fresh_entry():
    """Return a registered entry scope over a fresh runtime."""
    runtime = genia.make_global_env([])
    return runtime.create_entry_scope() if runtime._entry is None else runtime._entry


def run_in_thread(target):
    """Start `target` on a daemon thread and return (thread, outcome-dict)."""
    outcome = {}

    def body():
        try:
            outcome["result"] = target()
        except BaseException as error:  # noqa: BLE001 - recorded for assertions
            outcome["error"] = error

    thread = threading.Thread(target=body, daemon=True)
    thread.start()
    return thread, outcome


def test_m1_function_writer_cannot_extend_group_after_name_becomes_immutable(monkeypatch):
    """Pause a function declaration after its immutability check, then commit `x` immutable."""
    env = fresh_entry()
    genia.run_source("g(a) = a", env)
    group = env.get("g")
    clauses_before = len(group.clauses) if hasattr(group, "clauses") else None

    paused, release = threading.Event(), threading.Event()
    original = Env._reject_immutable_write

    def pausing(self, name, verb):
        original(self, name, verb)
        if name == "x" and threading.current_thread().name == "m1-writer":
            paused.set()
            release.wait(WAIT)

    monkeypatch.setattr(Env, "_reject_immutable_write", pausing)

    node = ir.IrFuncDef("x", ["a", "b"], None, None, ir.IrVar("a"))
    outcome = {}

    def write():
        try:
            outcome["result"] = Evaluator(env).eval(node)
        except BaseException as error:  # noqa: BLE001
            outcome["error"] = error

    writer = threading.Thread(target=write, name="m1-writer", daemon=True)
    writer.start()
    assert paused.wait(WAIT), "function writer never reached its immutability check"

    def commit():
        ticket = env.prepare_immutable_declaration("x")
        env.commit_immutable_declaration(ticket, group)

    committer, commit_outcome = run_in_thread(commit)
    committer.join(SETTLE)  # a correct implementation blocks here until the writer releases
    release.set()
    writer.join(WAIT)
    committer.join(WAIT)
    assert not writer.is_alive() and not committer.is_alive()

    writer_won = "error" not in outcome
    commit_won = "error" not in commit_outcome
    assert writer_won != commit_won, (outcome, commit_outcome)  # exactly one serialization is legal
    if commit_won:
        assert isinstance(outcome["error"], ImmutableBindingError)
        assert "x" in env.immutable_names()
        if clauses_before is not None:
            assert len(group.clauses) == clauses_before  # no unauthorized clause on the shared group
    else:
        assert isinstance(commit_outcome["error"], ImmutableBindingError)
        assert "x" not in env.immutable_names()


class PausingAssignable(set):
    """Pauses the commit between value publication and policy publication."""

    def __init__(self, paused, release):
        super().__init__()
        self.paused, self.release = paused, release

    def discard(self, name):
        super().discard(name)
        if name == "x":
            self.paused.set()
            self.release.wait(WAIT)


def test_m2_metadata_writer_cannot_land_in_the_partial_publication_window():
    """Pause the commit after `values[x]` exists but before `x` is marked immutable."""
    env = fresh_entry()
    paused, release = threading.Event(), threading.Event()
    env.assignable = PausingAssignable(paused, release)

    def commit():
        env.commit_immutable_declaration(env.prepare_immutable_declaration("x"), 1)

    committer, commit_outcome = run_in_thread(commit)
    assert paused.wait(WAIT), "commit never reached its partial-publication point"
    assert "x" in env.values  # the window is real: value published, policy not yet

    late = GeniaMap().put("doc", "unauthorized late metadata")
    meta_writer, meta_outcome = run_in_thread(lambda: env.merge_binding_metadata("x", late))
    meta_writer.join(SETTLE)  # a correct implementation blocks here until the commit completes
    release.set()
    committer.join(WAIT)
    meta_writer.join(WAIT)
    assert not committer.is_alive() and not meta_writer.is_alive()

    assert "error" not in commit_outcome, commit_outcome
    assert "x" in env.immutable_names()
    assert isinstance(meta_outcome.get("error"), ImmutableBindingError), meta_outcome
    assert env.get_metadata("x").get("doc") != "unauthorized late metadata"


def test_m2_declaration_owned_metadata_still_attaches_after_commit():
    """The authorized initial attachment through the declaration ticket is preserved."""
    env = fresh_entry()
    ticket = env.prepare_immutable_declaration("x")
    env.commit_immutable_declaration(ticket, 1)
    env.merge_binding_metadata("x", GeniaMap().put("doc", "declared"), declaration=ticket)
    assert env.get_metadata("x").get("doc") == "declared"
    with pytest.raises(ImmutableBindingError):
        env.merge_binding_metadata("x", GeniaMap().put("doc", "late"))
    assert env.get_metadata("x").get("doc") == "declared"
