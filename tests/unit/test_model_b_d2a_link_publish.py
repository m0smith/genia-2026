"""D2a RED: atomic publication, lock discipline and non-activation (#1250).

Acceptance IDs D2a-07, D2a-08, D2a-10 (design sections 2, 5, 9.1). PYTHON REFERENCE HOST
ONLY. D2a-10 contains existing-behavior guards (they pass today and must keep passing)
plus assertions on the inert private fields (RED until D2a adds them).
"""

import dataclasses
import threading

import pytest

import genia
from genia import callable as callables
from genia import environment as environments
from genia.callable import OpenFunctionTargetNotOpenError
from genia.environment import ImmutableBindingError
from tests.unit.f2_p2_support import separated_scopes
from tests.unit.model_b_d2a_support import base_world, contributor, frozen, linking

F5 = "f(a1, a2, a3, a4, a5) = 0\n"


def snapshot(root, module):
    """Observable state a failed link must leave untouched."""
    return (
        dict(root.values), dict(root.binding_metadata), set(root.assignable),
        dict(root.loaded_modules), module._ordinary_completions, dict(root.open_contributions),
    )


def two_views(tmp_path):
    root, entry, module, group = base_world(tmp_path, F5)
    good = contributor(root, entry, tmp_path, "good", group, ["f(0) = 1"])
    return root, entry, module, group, good


# --- D2a-07: atomicity ---------------------------------------------------------------------


def test_d2a_07_failed_link_at_each_stage_publishes_nothing_and_retry_succeeds(tmp_path):
    root, entry, module, group, good = two_views(tmp_path)
    fl = linking()
    prior = fl.link_view(frozen(module, group), [good])
    root.publish_view("v", prior)
    before = snapshot(root, module)
    clash = contributor(root, entry, tmp_path, "clash", group, ["f(z) = 9", "f(1, y) = 3"])
    twin = contributor(root, entry, tmp_path, "twin", group, ["f(w) = 8"])
    dup = callables.GeniaOpenContributionUnit(group.owner, "good", list(good.clauses), target=group)

    class BadKey(callables.OpenClauseRecord):
        """A record whose cached key cannot be read; surfaces at view build, never at dispatch."""
        dispatch_key = property(lambda self: (_ for _ in ()).throw(TypeError("malformed key")))

    broken_clause = BadKey.__new__(BadKey)
    broken = callables.GeniaOpenContributionUnit(group.owner, "broken", [], target=group)
    broken.clauses.append(broken_clause)
    for units, error in [
        ([good, dup], callables.OpenFunctionDuplicateSelectionError),   # resolution stage
        ([clash, twin], callables.OpenFunctionCrossUnitDuplicateClauseError),  # scan stage
        ([broken], TypeError),                                          # view-build stage
    ]:
        with pytest.raises(error):
            root.publish_view("v", fl.link_view(frozen(module, group), units))
        assert snapshot(root, module) == before
        assert root.get("v") is prior
    retry = fl.link_view(frozen(module, group), [good, twin])
    root.publish_view("v", retry)
    assert root.get("v") is retry and retry is not prior


def test_d2a_07_immutable_name_collision_raises_through_the_checked_writer(tmp_path):
    root, entry, module, group, good = two_views(tmp_path)
    genia.run_source("pinned =: 5", root, filename="<command>")
    before = snapshot(root, module)
    view = linking().link_view(frozen(module, group), [good])
    with pytest.raises(ImmutableBindingError):
        root.publish_view("pinned", view)
    assert snapshot(root, module) == before and root.get("pinned") == 5


def test_d2a_07_runtime_owned_name_routes_to_the_runtime_scope_and_pruned_name_fails(tmp_path):
    from hosts.python.mcp_worker_profile import prune_environment

    scopes = separated_scopes(tmp_path / "ok")
    root, entry, module, group = base_world(tmp_path / "base", F5)
    view = linking().link_view(frozen(module, group), [])
    scopes.entry.publish_view("map", view)  # runtime-owned name: bound in R exactly like Env.set
    assert scopes.runtime.values["map"] is view
    assert "map" in scopes.entry.entry_declared_runtime_owned
    scopes.entry.publish_view("local_view", view)
    assert scopes.entry.values["local_view"] is view
    pruned = separated_scopes(tmp_path / "pruned", prune=prune_environment)
    with pytest.raises(ValueError):
        pruned.entry.publish_view("read_file", view)
    assert "read_file" not in pruned.runtime.values and "read_file" not in pruned.entry.values


# --- D2a-08: lock discipline ---------------------------------------------------------------


class CountingLock:
    """Non-reentrant lock wrapper: records holds and rejects nested acquisition."""

    def __init__(self):
        self._lock = threading.Lock()
        self.holds = 0
        self.depth = 0
        self.max_depth = 0

    def __enter__(self):
        self._lock.acquire()
        self.holds += 1
        self.depth += 1
        self.max_depth = max(self.max_depth, self.depth)
        return self

    def __exit__(self, *exc):
        self.depth -= 1
        self._lock.release()
        return False


def test_d2a_08_builder_takes_no_lock_and_publication_takes_exactly_one_hold(tmp_path, monkeypatch):
    root, entry, module, group, good = two_views(tmp_path)
    base = frozen(module, group)
    counter = CountingLock()
    monkeypatch.setattr(environments, "_BINDING_LOCK", counter)
    fl = linking()
    view = fl.link_view(base, [good])
    assert counter.holds == 0  # plan, sort and build are pure: no lock, no Env.get
    root.publish_view("v", view)
    assert counter.holds == 1 and counter.max_depth == 1  # single hold, never re-entrant
    assert root.get("v") is view


def test_d2a_08_concurrent_publication_never_exposes_a_half_built_view(tmp_path):
    root, entry, module, group, good = two_views(tmp_path)
    fl = linking()
    other = contributor(root, entry, tmp_path, "other", group, ["f(1) = 2"])
    candidates = [fl.link_view(frozen(module, group), [good]), fl.link_view(frozen(module, group), [other])]
    barrier = threading.Barrier(2)
    errors = []

    def publish(view):
        try:
            barrier.wait(timeout=10)
            for _ in range(200):
                root.publish_view("v", view)
        except BaseException as error:  # noqa: BLE001 - reported to the main thread
            errors.append(error)

    threads = [threading.Thread(target=publish, args=(view,)) for view in candidates]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert not any(thread.is_alive() for thread in threads) and errors == []
    final = root.get("v")
    assert any(final is view for view in candidates)
    assert [unit.declaring_module_id for unit in final.units] in (["good"], ["other"])


def test_d2a_08_module_load_racing_publication_does_not_deadlock(tmp_path):
    root, entry, module, group, good = two_views(tmp_path)
    (tmp_path / "late.genia").write_text("late(x) = x\n", encoding="utf-8")
    view = linking().link_view(frozen(module, group), [good])
    errors = []

    def load():
        try:
            root.load_module("late", entry)
        except BaseException as error:  # noqa: BLE001
            errors.append(error)

    def publish():
        try:
            for _ in range(100):
                root.publish_view("v", view)
        except BaseException as error:  # noqa: BLE001
            errors.append(error)

    threads = [threading.Thread(target=load), threading.Thread(target=publish)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert not any(thread.is_alive() for thread in threads) and errors == []
    assert root.get("v") is view and "late" in root.loaded_modules


# --- D2a-10: non-activation ----------------------------------------------------------------


def test_d2a_10_ordinary_targets_are_still_rejected_from_source(tmp_path):
    root, entry, module, group = base_world(tmp_path, "f(x) = x\n")
    (tmp_path / "ext.genia").write_text("import base\nextend base.f(0, 1) = 1\n", encoding="utf-8")
    with pytest.raises(OpenFunctionTargetNotOpenError) as caught:
        root.load_module("ext", entry)
    assert "open-function-target-not-open" in str(caught.value)
    with pytest.raises(OpenFunctionTargetNotOpenError):
        genia.run_source("import base\nuse f from base with base", root, filename=entry)


def test_d2a_10_inert_private_fields_exist_and_stay_empty_without_activation(tmp_path):
    root, entry, module, group = base_world(tmp_path, "f(x) = x\n")
    assert root.ordinary_contributions == {}
    assert module._ordinary_contributions == () and isinstance(module._ordinary_contributions, tuple)
    field = {item.name: item for item in dataclasses.fields(callables.GeniaOpenContributionUnit)}["target"]
    assert field.default is None and field.compare is False and field.repr is False
    unit = callables.GeniaOpenContributionUnit(("base", "f"), "ext", [], target=group)
    assert unit.target is group
    assert unit == callables.GeniaOpenContributionUnit(("base", "f"), "ext", [])  # target never compared
    assert "GeniaFunctionGroup" not in repr(unit) and repr(unit) == "<open contribution ext -> f>"


def test_d2a_10_no_export_equality_or_reflection_exposes_private_machinery(tmp_path):
    root, entry, module, group = base_world(tmp_path, "f(x) = x\n")
    assert not any(name.startswith("_ordinary") for name in module.exports)
    assert "ordinary" not in repr(module).lower()
    fields = {item.name: item for item in dataclasses.fields(type(module))}
    for private in ("_ordinary_completions", "_ordinary_contributions"):
        assert fields[private].compare is False and fields[private].repr is False
    fl = linking()
    assert not hasattr(fl, "__all__") or "link_view" not in getattr(fl, "__all__", ())
    names = genia.run_source('import base\nbase.f(3)', root, filename=entry)
    assert names == 3  # plain ordinary use of the exported function is unchanged
    assert not any("link" in key.lower() and "view" in key.lower() for key in root.values)
