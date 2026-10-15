"""Python-only F2/P2 pre-merge correction regressions (issue #1067, tracker #1229, debt #1238, retirement #1230).

Covers Python-host internals only: the entry-declaration record on `Env`, the per-execution
fallback event accounting under host-thread concurrency, and fallback state for caller-created
registered runtimes. None of this is portable language behavior, so there is no shared-spec twin.

- R01: `entry_declared_runtime_owned` records successful declarations only.
- R15: one warning per canonical (module, name) pair per execution under concurrent readers.
- R16: `create_entry_scope()` leaves a caller-created runtime with working fallback accounting.
"""

import threading

import pytest

import genia
from genia import make_program_env, run_source
from genia.environment import Env
from genia.module_fallback import temporary_compatibility_fallback_read
from tests.unit.f2_p2_support import register_entry, separated_scopes


@pytest.fixture(autouse=True)
def _default_mode(monkeypatch):
    """Fallback accounting is a default-mode behavior; strict-capture tests set the switch themselves."""
    monkeypatch.delenv("GENIA_STRICT_MODULE_SCOPE", raising=False)


def _program_with_list_prelude():
    """Return a program environment whose list prelude is loaded, so `first` and `length` are bound runtime names.

    Failure cases below need an existing runtime-owned binding to collide with.
    """
    entry = make_program_env([])
    run_source("length([1])", entry)  # loads the list prelude so `first` is a bound runtime name
    return entry


# ---------------------------------------------------------------- R01 -------------------------


@pytest.mark.parametrize(
    "source,error,name",
    [
        ("first(x) = x", TypeError, "first"),
        ("open log(x) = x", Exception, "log"),
    ],
)
def test_r01_failed_declaration_of_existing_runtime_name_is_not_recorded(source, error, name):
    entry = _program_with_list_prelude()
    runtime = entry.runtime_scope()
    before = runtime.values[name]
    with pytest.raises(error):
        run_source(source, entry)
    assert name not in entry.entry_declared_runtime_owned
    assert name not in entry.inspection_bindings()
    assert entry.binding_owner(name) is None
    assert runtime.values[name] is before


def test_r01_failed_assignment_and_failed_function_clause_are_not_recorded(tmp_path):
    def prepare(runtime):
        """Pre-registration host setup: a non-assignable and an ordinary non-function runtime binding."""
        runtime.set("fixed_value", 1, assignable=False)
        runtime.set("plain_value", 2)

    s = separated_scopes(tmp_path, prepare=prepare)
    entry = s.entry
    with pytest.raises(NameError):
        run_source("fixed_value = 5", entry)
    with pytest.raises(TypeError):
        run_source("plain_value(x) = x", entry)
    assert entry.entry_declared_runtime_owned == set()
    assert "fixed_value" not in entry.inspection_bindings()
    assert "plain_value" not in entry.inspection_bindings()
    assert s.runtime.values["fixed_value"] == 1 and s.runtime.values["plain_value"] == 2


def test_r01_failed_declaration_retains_its_original_error_text():
    entry = _program_with_list_prelude()
    with pytest.raises(TypeError) as first:
        run_source("first(x) = x", entry)
    again = _program_with_list_prelude()
    with pytest.raises(TypeError) as second:
        run_source("first(x) = x", again)
    assert str(first.value) == str(second.value) != ""


@pytest.mark.parametrize(
    "source,name",
    [
        ("first = 1", "first"),
        ("first(a, b, c, d, e) = 1", "first"),
        ("open_probe_free = 1\nmap_acc(a, b, c, d) = 1", "map_acc"),
    ],
)
def test_r01_successful_declaration_is_recorded_and_visible(source, name):
    entry = _program_with_list_prelude()
    run_source(source, entry)
    assert name in entry.entry_declared_runtime_owned
    assert name in entry.inspection_bindings()
    assert entry.binding_owner(name) is entry.runtime_scope()


def test_r01_nested_successful_declaration_survives_a_later_failed_one():
    entry = _program_with_list_prelude()
    with pytest.raises(TypeError):
        run_source("map_acc(a, b, c, d) = 1\nfirst(x) = x", entry)
    assert "map_acc" in entry.entry_declared_runtime_owned
    assert "first" not in entry.entry_declared_runtime_owned


@pytest.mark.parametrize("source", ["read_file = 1", "read_file(x) = x", "open read_file(x) = x"])
def test_r01_mcp_denied_name_cannot_be_declared_restored_or_recorded(tmp_path, source):
    from hosts.python.mcp_worker_profile import prune_environment

    s = separated_scopes(tmp_path, prune=prune_environment)
    assert "read_file" not in s.runtime.values
    with pytest.raises(ValueError, match="restricted execution"):
        run_source(source, s.entry)
    assert "read_file" not in s.runtime.values and "read_file" not in s.entry.values
    assert "read_file" not in s.entry.entry_declared_runtime_owned
    assert "read_file" not in s.entry.inspection_bindings()


# ---------------------------------------------------------------- R15 -------------------------


def _worker_module(tmp_path):
    """Build an entry program with a real module `race` and three spawned Process workers.

    `p` and `q` run `race.worker` (an eligible fallback read of entry name `entry_secret`, the same pair);
    `r` runs `race.other` (a distinct pair, `entry_other`). Returns the entry env; messages are sent by the caller.
    """
    (tmp_path / "race.genia").write_text("worker(msg) = entry_secret\nother(msg) = entry_other\n", encoding="utf-8")
    entry = make_program_env([])
    genia.run_source(
        "entry_secret = 42\nentry_other = 7\nimport race\n"
        "p = spawn(race.worker)\nq = spawn(race.worker)\nr = spawn(race.other)",
        entry,
        filename=str(tmp_path / "entry.genia"),
    )
    return entry


class _PausingEvents(set):
    """Event set that holds each membership test at a barrier, forcing the legal racy schedule.

    A reader that tests membership and records separately lets every paused reader see "unseen".
    A correct atomic claim keeps test and add in one critical section, so the second reader cannot
    reach the barrier until the first has recorded; the barrier then times out and is tolerated.
    """

    def __init__(self, parties):
        """Create an empty set whose membership tests rendezvous at a `parties`-way barrier."""
        super().__init__()
        self.barrier = threading.Barrier(parties)
        self.hits = 0

    def __contains__(self, item):
        """Answer membership first, then pause up to 1s at the barrier (tolerating a broken one) to force overlap."""
        seen = super().__contains__(item)  # the answer is fixed before the pause
        self.hits += 1
        try:
            self.barrier.wait(timeout=1)
        except threading.BrokenBarrierError:
            pass
        return seen


def test_r15_same_pair_from_concurrent_process_workers_warns_once(tmp_path, capsys):
    entry = _worker_module(tmp_path)
    runtime = entry.runtime_scope()
    runtime.fallback_events = _PausingEvents(2)
    genia.run_source("send(p, 1)\nsend(q, 2)", entry)
    entry.get("p")._r25_wait_idle()
    entry.get("q")._r25_wait_idle()
    err = capsys.readouterr().err
    assert set(runtime.fallback_events) == {("race", "entry_secret")}
    assert runtime.fallback_events.hits >= 2  # both workers really reached the membership step
    assert err.count("module 'race' resolved entry-program name 'entry_secret'") == 1
    assert not entry.get("p").failed() and not entry.get("q").failed()


def test_r15_claim_is_atomic_for_many_threads_on_one_pair():
    runtime = Env()
    runtime.init_fallback_state(strict_module_scope=False)
    winners = []
    start = threading.Barrier(8)

    def contend():
        """Wait for all threads, then claim the one shared pair, counting a win only when the claim returns True."""
        start.wait()
        if runtime.claim_fallback_event(("m", "n")):
            winners.append(1)

    threads = [threading.Thread(target=contend) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(winners) == 1 and runtime.fallback_events == {("m", "n")}


def test_r15_distinct_pairs_each_warn_once_and_single_thread_is_unchanged(tmp_path, capsys):
    entry = _worker_module(tmp_path)
    genia.run_source("send(p, 1)\nsend(r, 2)\nsend(p, 3)", entry)
    entry.get("p")._r25_wait_idle()
    entry.get("r")._r25_wait_idle()
    err = capsys.readouterr().err
    assert entry.runtime_scope().fallback_events == {("race", "entry_secret"), ("race", "entry_other")}
    assert err.count("entry_secret") == 1 and err.count("entry_other") == 1


def test_r15_executions_do_not_share_claims_or_locks(tmp_path):
    a, b = Env(), Env()
    a.init_fallback_state(strict_module_scope=False)
    b.init_fallback_state(strict_module_scope=False)
    assert a.claim_fallback_event(("m", "n")) is True
    assert b.claim_fallback_event(("m", "n")) is True
    assert a.claim_fallback_event(("m", "n")) is False
    assert a._fallback_lock is not b._fallback_lock


def test_r15_warning_io_is_outside_the_claim_critical_section(tmp_path):
    """A sink that re-enters the claim path would deadlock if IO ran under the guard."""
    s = separated_scopes(tmp_path)
    runtime = s.runtime
    reentered = []

    class ReenteringSink:
        """Warning sink that claims another pair from inside `write_text`, probing for I/O under the lock."""

        def write_text(self, text):
            """Record the result of a nested claim; it would deadlock if the caller still held the claim lock."""
            reentered.append(runtime.claim_fallback_event(("other", "pair")))

    runtime.values["stderr"] = ReenteringSink()
    s.load("worker() = entry_marker", name="reenter_module")
    s.entry.set("entry_marker", 1)
    worker = threading.Thread(target=lambda: run_source("reenter_module.worker()", s.entry))
    worker.start()
    worker.join(timeout=5)
    assert not worker.is_alive(), "warning IO ran inside the synchronization critical section"
    assert reentered == [True]


# ---------------------------------------------------------------- R16 -------------------------


def _manual_runtime():
    """Hand-build registered runtime R, entry E (with `shared = 42`) and module frame M named `manual`.

    Mirrors what the module loader sets up without using `make_global_env`, so fallback state comes only from
    `create_entry_scope()`. Returns `(R, E, M)`.
    """
    r = Env()
    e = r.create_entry_scope()
    e.set("shared", 42)
    m = Env(r)
    m._unit_scope = m
    m.module_id = "manual"
    return r, e, m


def test_r16_manually_registered_runtime_records_and_warns_for_eligible_fallback(capsys, monkeypatch):
    monkeypatch.delenv("GENIA_STRICT_MODULE_SCOPE", raising=False)
    r, _e, m = _manual_runtime()
    assert r.fallback_events == set()
    assert genia.run_source("shared", m) == 42
    assert r.fallback_events == {("manual", "shared")}
    assert capsys.readouterr().err.count("module 'manual' resolved entry-program name 'shared'") == 1


def test_r16_manually_registered_runtime_captures_strict_mode_at_registration(monkeypatch):
    monkeypatch.setenv("GENIA_STRICT_MODULE_SCOPE", "1")
    r, _e, m = _manual_runtime()
    monkeypatch.delenv("GENIA_STRICT_MODULE_SCOPE")  # later changes must not affect this execution
    assert r.strict_module_scope is True
    with pytest.raises(NameError):
        genia.run_source("shared", m)
    assert r.fallback_events == set()


def test_r16_two_registered_runtimes_have_isolated_event_state(monkeypatch):
    monkeypatch.delenv("GENIA_STRICT_MODULE_SCOPE", raising=False)
    r1, _e1, m1 = _manual_runtime()
    r2, _e2, _m2 = _manual_runtime()
    genia.run_source("shared", m1)
    assert r1.fallback_events == {("manual", "shared")} and r2.fallback_events == set()
    assert r1.fallback_events is not r2.fallback_events


def test_r16_factory_built_runtime_state_is_not_reinitialised(monkeypatch):
    monkeypatch.setenv("GENIA_STRICT_MODULE_SCOPE", "1")
    runtime = genia.make_global_env([])
    events, lock = runtime.fallback_events, runtime._fallback_lock
    monkeypatch.delenv("GENIA_STRICT_MODULE_SCOPE")
    register_entry(runtime)
    assert runtime.strict_module_scope is True
    assert runtime.fallback_events is events and runtime._fallback_lock is lock


def test_r16_unregistered_single_root_has_no_fallback_and_no_state():
    legacy_root = Env()
    legacy_root.set("x", 1)
    child = Env(legacy_root)
    child._unit_scope = child
    child.module_id = "legacy"
    assert genia.run_source("x", child) == 1  # ordinary parent lookup, no fallback involved
    assert legacy_root.fallback_events is None


def test_r16_missing_event_state_fails_closed_rather_than_skipping_diagnostics():
    r, e, m = _manual_runtime()
    r.fallback_events = None  # simulate an inconsistent registered runtime
    assert temporary_compatibility_fallback_read(m, "shared") == (False, None)
