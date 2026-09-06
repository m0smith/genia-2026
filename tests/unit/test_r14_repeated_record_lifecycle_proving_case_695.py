"""Sidecar tests for the R14 E14-11 repeated record lifecycle proving case
(issue #695): examples/r14_repeated_record_lifecycle_proving_case.genia.

Proves, over the already-implemented E14-1 through E14-4 mechanism
(`lifecycle_scope`, `lifecycle_repeat`, `lifecycle_context`) with zero
runtime-code change, per
docs/design/r14-composable-lifecycle-contract.md's "Repeated record proof
(pressure test)" section:

- one outer pipeline/session scope wrapping fresh per-element scopes
- at least two peer LifecycleDefinitions per element, deterministic
  enter/work/reverse-unwind order
- record/fields/nr/nf-style values derived from the reserved
  quote(element)/quote(index) context as ordinary data, no new syntax
- an eager List source that never short-circuits on an individual element's
  data-level failure (err(...) as ordinary data) or genuine work-phase
  exception, with no cross-element context leakage
- a lazy Flow source bounded by `take`, proving no over-pull and that each
  yielded element is fully entered and unwound before the next pull
- explicit capture of survived data as ordinary values
"""

from __future__ import annotations

from pathlib import Path

from genia import make_global_env, run_source
from genia.utf8 import format_display

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/r14_repeated_record_lifecycle_proving_case.genia"


def _load():
    env = make_global_env()
    result = run_source(EXAMPLE.read_text(encoding="utf-8"), env, filename=str(EXAMPLE))
    return result


def _log_field(result, field):
    return [format_display(entry.get(field)) for entry in result.get("log")]


def test_example_file_exists():
    assert EXAMPLE.is_file()


def test_eager_statuses_show_no_short_circuit_on_failure():
    result = _load()
    summary = result.get("summary")
    statuses = [format_display(s) for s in summary.get("eager_statuses")]
    assert statuses == ["ok", "ok", "ok", "error", "ok"]


def test_malformed_field_count_is_ordinary_err_data_not_a_work_exception():
    result = _load()
    summary = result.get("summary")
    statuses = [format_display(s) for s in summary.get("eager_statuses")]
    # "bad" is element 3 (wrong field count): the failure is captured as
    # ordinary err(...) data inside .row, so the element's own
    # LifecycleResult still completes ok.
    assert statuses[2] == "ok"


def test_non_string_element_causes_a_genuine_work_phase_failure():
    result = _load()
    summary = result.get("summary")
    statuses = [format_display(s) for s in summary.get("eager_statuses")]
    # 999 is element 4: split() raises on a non-string element, producing a
    # genuine work-phase LifecycleResult failure, not ordinary err() data.
    assert statuses[3] == "error"


def test_survived_eager_excludes_malformed_and_failed_records_only():
    result = _load()
    summary = result.get("summary")
    survived = summary.get("survived_eager")
    names = [format_display(row.get("name")) for row in survived]
    assert names == ["Ada", "Grace", "Lin"]


def test_bounded_flow_pulls_exactly_two_and_survives_both():
    result = _load()
    summary = result.get("summary")
    assert summary.get("bounded_count") == 2
    survived = summary.get("survived_bounded")
    names = [format_display(row.get("name")) for row in survived]
    assert names == ["Amy", "Ben"]


def test_session_scope_wraps_the_entire_run():
    result = _load()
    peers = _log_field(result, "peer")
    phases = _log_field(result, "phase")
    assert (peers[0], phases[0]) == ("session", "enter")
    assert (peers[-1], phases[-1]) == ("session", "exit")


def test_two_peers_enter_work_unwind_in_deterministic_reverse_order():
    result = _load()
    peers = _log_field(result, "peer")
    phases = _log_field(result, "phase")
    # First element scope (right after the session's own enter).
    first_element = list(zip(peers[1:5], phases[1:5]))
    assert first_element == [
        ("record_context", "enter"),
        ("diagnostics", "enter"),
        ("diagnostics", "exit"),
        ("record_context", "exit"),
    ]


def test_element_index_is_scoped_per_repeat_call_with_no_cross_leakage():
    result = _load()
    peers = _log_field(result, "peer")
    phases = _log_field(result, "phase")
    indices = _log_field(result, "index")
    enter_indices = [
        idx
        for peer, phase, idx in zip(peers, phases, indices)
        if peer == "record_context" and phase == "enter"
    ]
    # Eager run: elements 1..5 in order, none skipped despite element 4's
    # work failure. Bounded run: an independent element index restarting at
    # 1..2 (no leakage from the eager run's own index/context).
    assert enter_indices == ["1", "2", "3", "4", "5", "1", "2"]


def test_failed_element_still_unwinds_both_peers_with_error_status():
    result = _load()
    peers = _log_field(result, "peer")
    phases = _log_field(result, "phase")
    indices = _log_field(result, "index")
    statuses = _log_field(result, "status")
    fourth_element_exits = [
        (peer, status)
        for peer, phase, idx, status in zip(peers, phases, indices, statuses)
        if idx == "4" and phase == "exit"
    ]
    assert ("diagnostics", "error") in fourth_element_exits
    assert ("record_context", "error") in fourth_element_exits
