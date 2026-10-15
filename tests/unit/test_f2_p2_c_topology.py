"""Python-only F2/P2-C topology tests (contract 16.1, 16.6; issue #1067, tracker #1229).

Supplements the P2-B red suite with checks the P2-B cases do not make directly:
immutable class-level state defaults, registration isolation between runtimes,
construction-helper ordering, manifest stability under pruning, and the pruned-name
rejection. Python host internals only; none of this is portable language behavior.
"""

import pytest

from genia import make_global_env, make_program_env, run_source
from genia.environment import Env, runtime_owned_manifest
from hosts.python.mcp_worker_profile import prune_environment


def test_ordinary_frames_share_no_registration_state():
    """Class-level defaults are immutable; only R and E carry topology instance state."""
    runtime = make_global_env([])
    entry = runtime.create_entry_scope()
    frame = Env(entry)
    assert frame._entry is None and frame._is_entry is False
    assert frame.entry_declared_runtime_owned is None
    assert isinstance(Env.prelude_paths, frozenset)
    assert "entry_declared_runtime_owned" not in vars(frame) and "_entry" not in vars(frame)
    assert vars(entry)["entry_declared_runtime_owned"] is not None
    assert entry.entry_declared_runtime_owned is not runtime.entry_declared_runtime_owned


def test_registrations_are_isolated_between_runtimes():
    """Registering E on one runtime never changes another runtime's entry or records."""
    first, second = make_global_env([]), make_global_env([])
    first_entry = first.create_entry_scope()
    assert second.entry_scope() is second
    second_entry = second.create_entry_scope()
    run_source("log = 5", first_entry)
    assert first_entry.entry_declared_runtime_owned == {"log"}
    assert second_entry.entry_declared_runtime_owned == set()
    assert second.values["log"] != 5


def test_entry_declared_runtime_owned_records_only_runtime_owned_names():
    """16.1.4: E records entry-declared runtime-owned names, not ordinary entry names."""
    entry = make_program_env([])
    run_source("map_acc(f, xs, acc) = acc\nlog = 5\nzzz = 1", entry)
    assert entry.entry_declared_runtime_owned == {"map_acc", "log"}
    assert "zzz" in entry.values and "zzz" not in entry.runtime_scope().values


def test_helper_runs_prepare_on_runtime_before_registration():
    """16.6.2: pre-registration host work sees an unregistered R and no E."""
    seen = []

    def prepare(runtime):
        """Record the registration state visible to pre-registration host work."""
        seen.append((runtime.parent, runtime._entry, runtime.entry_scope() is runtime))

    entry = make_program_env([], prepare=prepare)
    assert seen == [(None, None, True)]
    assert entry.runtime_scope()._entry is entry


def test_helper_rejects_entry_only_injection_before_registration():
    """16.6.1: an entry-only install made before E exists is rejected, not placed in R."""

    def prepare(runtime):
        """Install an entry-only binding too early."""
        runtime.set_host("too_early", 1, visibility="entry-only")

    with pytest.raises(ValueError, match="after entry registration"):
        make_program_env([], prepare=prepare)


def test_manifest_snapshot_survives_pruning_and_denied_name_is_rejected():
    """16.1.1/16.7: pruning never shrinks the manifest nor lets write-through recreate a denied name."""
    runtime = make_global_env([])
    before = runtime.prelude_paths
    manifest = runtime_owned_manifest(before)
    prune_environment(runtime)
    assert runtime.prelude_paths == before
    assert runtime_owned_manifest(runtime.prelude_paths) == manifest
    entry = runtime.create_entry_scope()
    assert runtime.is_runtime_owned("read_file") and runtime.is_runtime_owned("map_acc")
    with pytest.raises(ValueError) as failure:
        run_source('read_file(path) = "SENTINEL-DENIED-VALUE"', entry)
    assert "SENTINEL-DENIED-VALUE" not in str(failure.value)
    assert "read_file" not in runtime.values and "read_file" not in entry.values
    run_source("map_acc(f, xs, acc) = acc", entry)  # still-reachable prelude file: write-through
    assert "map_acc" in runtime.values


def test_caller_created_root_keeps_single_root_behavior():
    """Legacy harness: no registration, entry is the root, both host classes install in place."""
    root = make_global_env([])
    assert root.entry_scope() is root and root.inspection_globals_scope() is root
    root.set_host("fixture", 1, visibility="entry-only")
    root.set_host("capability", 2, visibility="runtime-public")
    assert root.values["fixture"] == 1 and root.values["capability"] == 2
    run_source("first_user = 3", root)
    assert root.values["first_user"] == 3


def test_open_function_declaration_over_runtime_owned_name_reports_redeclaration():
    """The routed home scope is consulted, so an open declaration cannot silently replace R's group."""
    entry = make_program_env([])
    entry.runtime_scope().get("first")
    with pytest.raises(Exception) as failure:
        run_source('open first("x", y) = y', entry)
    assert "first" in str(failure.value)
    assert "first" not in entry.values
