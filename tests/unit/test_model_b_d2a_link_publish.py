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
from tests.unit.model_b_d2a_support import base_world, contributor, frozen, linking, no_runtime_calls

F5 = "f(a1, a2, a3, a4, a5) = 0\n"


def observation(value, seen=None):
    """Detach fixture-owned structure while retaining identities; never clone an Env/handle."""
    from genia.values import GeniaMap, ModuleValue
    from collections.abc import Mapping

    if value is None or type(value) in (str, int, bool, float):
        return value
    seen = set() if seen is None else seen
    if id(value) in seen:
        return ('reference', id(value))
    seen.add(id(value))
    if isinstance(value, GeniaMap):
        return ('map', id(value), observation(value._entries, seen))
    if isinstance(value, Mapping):
        return ('dict', id(value), tuple((observation(k, seen), observation(v, seen))
                                        for k, v in value.items()))
    if isinstance(value, (tuple, list)):
        return (type(value).__name__, None if isinstance(value, tuple) else id(value),
                tuple(observation(v, seen) for v in value))
    if isinstance(value, (set, frozenset)):
        return ('set', frozenset(value))
    if isinstance(value, (callables.GeniaFunction, callables.OpenClauseRecord)):
        return ('record', id(value), id(value.closure), tuple(value.params) if hasattr(value, 'params') else None,
                observation(value.body, seen), observation(value.pattern, seen),
                observation(value.guard, seen), observation(value.span, seen), value.dispatch_key)
    if isinstance(value, ModuleValue):
        return ('module', id(value), observation(value.exports, seen), observation(value.contributions, seen),
                id(value._ordinary_completions), observation(value._ordinary_completions, seen),
                id(value._ordinary_contributions), observation(value._ordinary_contributions, seen))
    if isinstance(value, callables.GeniaFunctionGroup):
        return ('group', id(value), observation(value.records, seen), observation(value.functions, seen),
                observation(value.metadata, seen), value.docstring)
    if dataclasses.is_dataclass(value):
        # Only explicit, fixture-owned IR/projection/view dataclasses reach here.
        return (type(value).__name__, id(value), tuple((f.name, observation(getattr(value, f.name), seen))
                                                     for f in dataclasses.fields(value)))
    return ('opaque', id(value))


def snapshot(root, module):
    """Capture binding/immutability, caches, both contribution stores and prior-view contents."""
    return observation((root.values, root.binding_metadata, root.assignable,
                        root.immutable_names(), root.loaded_modules, root.loading_modules,
                        root.open_contributions, root.ordinary_contributions, module))


def two_views(tmp_path):
    """Build the shared fixture world plus one valid contributor unit `good` for f/1."""
    root, entry, module, group = base_world(tmp_path, F5)
    good = contributor(root, entry, tmp_path, "good", group, ["f(0) = 1"])
    return root, entry, module, group, good


# --- D2a-07: atomicity ---------------------------------------------------------------------


class InjectedFault(Exception):
    """Distinct harness exception, never an accepted production diagnostic."""


def traced_build(fl, base, units, stop=None):
    """Fault at a numbered Python line in the real builder, including every scan iteration.

    The successful trace determines sites dynamically; no future helper names or
    implementation lines are frozen. Restores any pre-existing tracer on failure.
    """
    import sys

    events = []
    old = sys.gettrace()

    def trace(frame, event, arg):
        """Raise the injected fault on the `stop`-th executed builder source line."""
        if event == 'line' and frame.f_code.co_filename == fl.__file__:
            events.append((frame.f_code.co_name, frame.f_lineno))
            if len(events) == stop:
                raise InjectedFault('builder line fault')
        return trace

    try:
        sys.settrace(trace)
        result = fl.link_view(base, units)
        return result, events
    finally:
        sys.settrace(old)


def test_d2a_07_every_executed_resolution_and_scan_line_is_atomic_and_retryable(tmp_path):
    root, entry, module, group, good = two_views(tmp_path)
    other = contributor(root, entry, tmp_path, 'other', group, ['f(1)=2', 'f(2,3)=4'])
    fl = linking()
    base = frozen(module, group)
    prior = fl.link_view(base, [good])
    root.publish_view('v', prior)
    _, sites = traced_build(fl, base, [other, good])
    assert sites and any(name == 'plan_link' for name, line in sites)
    # Each occurrence matters: repeating the same line in a scan is a new fault site.
    for stop in range(1, len(sites) + 1):
        before = snapshot(root, module)
        with pytest.raises(InjectedFault, match='builder line fault'):
            candidate, _ = traced_build(fl, base, [other, good], stop)
            root.publish_view('v', candidate)
        assert snapshot(root, module) == before
        assert root.get('v') is prior and prior(0) == 1
        retry = fl.link_view(base, [other, good])
        root.publish_view('v', retry)
        assert root.get('v') is retry and retry(1) == 2
        root.publish_view('v', prior)


def test_d2a_07_sort_and_actual_view_constructor_faults_are_atomic_and_retryable(tmp_path, monkeypatch):
    import builtins
    import sys

    root, entry, module, group, good = two_views(tmp_path)
    fl = linking()
    base = frozen(module, group)
    prior = fl.link_view(base, [good])
    root.publish_view('v', prior)
    before = snapshot(root, module)
    sort_hits = []
    previous = sys.getprofile()

    def profile(frame, event, function):
        """Fault the first sort entered from the linking module, recording the hit."""
        if event == 'c_call' and frame.f_code.co_filename == fl.__file__:
            if function is builtins.sorted or getattr(function, '__name__', '') == 'sort':
                sort_hits.append(True)
                raise InjectedFault('sort fault')

    try:
        sys.setprofile(profile)
        with pytest.raises(InjectedFault, match='sort fault'):
            root.publish_view('v', fl.link_view(base, [good]))
    finally:
        sys.setprofile(previous)
    assert sort_hits and snapshot(root, module) == before
    root.publish_view('v', fl.link_view(base, [good]))
    root.publish_view('v', prior)
    constructor_hits = []
    constructor = callables.GeniaLinkedOpenFunction.__init__

    def broken_constructor(self, *args, **kwargs):
        """Run real construction then fail before a constructed value can escape."""
        constructor(self, *args, **kwargs)
        constructor_hits.append(self)
        raise InjectedFault('constructor fault')

    with monkeypatch.context() as patch:
        patch.setattr(callables.GeniaLinkedOpenFunction, '__init__', broken_constructor)
        with pytest.raises(InjectedFault, match='constructor fault'):
            root.publish_view('v', fl.link_view(base, [good]))
    assert len(constructor_hits) == 1 and snapshot(root, module) == before
    root.publish_view('v', fl.link_view(base, [good]))
    assert root.get('v')(0) == 1


def test_d2a_07_semantic_resolution_and_scan_errors_leave_all_state_unchanged(tmp_path):
    root, entry, module, group, good = two_views(tmp_path)
    fl = linking()
    twin = contributor(root, entry, tmp_path, 'twin', group, ['f(0)=9'])
    duplicate = callables.GeniaOpenContributionUnit(group.owner, 'good', list(good.clauses), target=group)
    base = frozen(module, group)
    prior = fl.link_view(base, [good])
    root.publish_view('v', prior)
    before = snapshot(root, module)
    for units, error in [([good, duplicate], callables.OpenFunctionDuplicateSelectionError),
                         ([good, twin], callables.OpenFunctionCrossUnitDuplicateClauseError)]:
        with pytest.raises(error):
            root.publish_view('v', fl.link_view(base, units))
        assert snapshot(root, module) == before and root.get('v') is prior
        root.publish_view('v', fl.link_view(base, [good]))
        root.publish_view('v', prior)


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
    """Bounded lock wrapper: reject same-thread re-entry before trying to acquire."""

    def __init__(self):
        """Start unowned with zero recorded holds."""
        self._lock = threading.Lock()
        self.owner = None
        self.holds = 0
        self.max_depth = 0

    def __enter__(self):
        """Acquire with a 2 s bound, rejecting same-thread re-entry; count the hold."""
        if self.owner == threading.get_ident():
            raise AssertionError('nested binding lock acquisition')
        if not self._lock.acquire(timeout=2):
            raise AssertionError('binding lock acquisition timed out')
        self.owner = threading.get_ident()
        self.holds += 1
        self.max_depth = 1
        return self

    def __exit__(self, *exc):
        """Release the lock and propagate any exception unchanged."""
        self.owner = None
        self._lock.release()
        return False


def bounded_process(action, timeout=12):
    """Contain thread deadlocks in a disposable process and always reap that process.

    Python/Linux harness only: fork preserves the prepared real loader fixtures.
    Any assertion/exception is returned to pytest; timeout terminates the child,
    including its daemon threads, instead of hanging the suite.
    """
    import multiprocessing
    import traceback

    context = multiprocessing.get_context('fork')
    receiving, sending = context.Pipe(duplex=False)

    def child():
        """Run `action` in the forked child and report its traceback (or None) to the parent."""
        try:
            action()
        except BaseException:
            sending.send(traceback.format_exc())
        else:
            sending.send(None)
        finally:
            sending.close()

    process = context.Process(target=child, daemon=True)
    process.start()
    sending.close()
    try:
        assert receiving.poll(timeout), 'race worker exceeded bounded deadline'
        failure = receiving.recv()
        assert failure is None, failure
        process.join(timeout=2)
        assert not process.is_alive() and process.exitcode == 0
    finally:
        receiving.close()
        if process.is_alive():
            process.terminate()
            process.join(timeout=2)
        if process.is_alive():
            process.kill()
            process.join(timeout=2)
        assert not process.is_alive(), 'race worker could not be reaped'


def test_d2a_08_builder_takes_no_lock_and_publication_takes_exactly_one_hold(tmp_path, monkeypatch):
    from genia import builtins as genia_builtins

    root, entry, module, group, good = two_views(tmp_path)
    base = frozen(module, group)
    fl = linking()
    counter = CountingLock()
    monkeypatch.setattr(environments, '_BINDING_LOCK', counter)

    def forbidden(*args, **kwargs):
        """Fail if the pure builder performs a lookup or rendering call."""
        raise AssertionError('pure builder called Env.get or renderer')

    with monkeypatch.context() as patch, no_runtime_calls():
        patch.setattr(environments.Env, 'get', forbidden)
        patch.setattr(genia_builtins, 'format_display', forbidden)
        patch.setattr(genia_builtins, 'format_debug', forbidden)
        view = fl.link_view(base, [good])
    assert counter.holds == 0
    root.publish_view('v', view)
    assert counter.holds == 1 and counter.max_depth == 1
    assert root.get('v') is view


def test_d2a_08_concurrent_publication_is_observed_before_and_after_each_write(tmp_path):
    import queue

    root, entry, module, group, good = two_views(tmp_path)
    other = contributor(root, entry, tmp_path, 'other', group, ['f(1)=2'])
    candidates = [linking().link_view(frozen(module, group), [unit]) for unit in (good, other)]
    root.publish_view('v', candidates[0])
    signatures = {id(view): observation(view) for view in candidates}

    def race():
        """Run two barrier-started publishers while a reader observes each checked write."""
        start = threading.Barrier(3, timeout=2)
        messages = queue.Queue()
        errors = []
        original = environments.Env._write_binding
        observations = []

        def checked_write(env, name, value, *args, **kwargs):
            """Wrap the real checked write, pausing for reader acknowledgement before and after it."""
            if env is root and name == 'v':
                for phase in ('before', 'after'):
                    if phase == 'after':
                        original(env, name, value, *args, **kwargs)
                    acknowledged = threading.Event()
                    messages.put((phase, acknowledged))
                    assert acknowledged.wait(2), 'reader failed to acknowledge publication boundary'
            else:
                original(env, name, value, *args, **kwargs)

        def writer(view):
            """Publish `view` eight times after the start barrier, collecting any failure."""
            try:
                start.wait()
                for _ in range(8):
                    root.publish_view('v', view)
            except BaseException as error:
                errors.append(error)

        environments.Env._write_binding = checked_write
        threads = [threading.Thread(target=writer, args=(view,), daemon=True) for view in candidates]
        try:
            for thread in threads:
                thread.start()
            start.wait()
            for _ in range(32):
                phase, acknowledged = messages.get(timeout=3)
                try:
                    current = root.get('v')
                    assert id(current) in signatures
                    assert observation(current) == signatures[id(current)]
                    assert current(0 if current is candidates[0] else 1) in (1, 2)
                    observations.append((phase, id(current)))
                finally:
                    acknowledged.set()
            for thread in threads:
                thread.join(timeout=2)
            assert not any(t.is_alive() for t in threads) and not errors
            assert len(observations) == 32
            assert {identity for phase, identity in observations if phase == 'after'} == set(signatures)
        finally:
            environments.Env._write_binding = original

    bounded_process(race)


def test_d2a_08_module_load_overlaps_publication_and_both_finish(tmp_path):
    root, entry, module, group, good = two_views(tmp_path)
    view = linking().link_view(frozen(module, group), [good])

    def race():
        """Publish while a module initializer is blocked, then let both finish."""
        entered = threading.Event()
        published = threading.Event()
        errors = []

        def pause_load():
            """Signal module initialization is running and wait for publication to complete."""
            entered.set()
            assert published.wait(3), 'publication blocked behind module initialization'
            assert root.get('v') is view and view(0) == 1

        root.set_host('pause_load', pause_load, visibility='runtime-public')
        (tmp_path / 'late.genia').write_text('pause_load()\nlate(x)=x\n', encoding='utf-8')

        def load():
            """Load the blocked module in a thread, collecting any failure."""
            try:
                root.load_module('late', entry)
            except BaseException as error:
                errors.append(error)

        thread = threading.Thread(target=load, daemon=True)
        thread.start()
        assert entered.wait(3), 'load never reached synchronized initialization point'
        try:
            assert 'late' in root.loading_modules and 'late' not in root.loaded_modules
            root.publish_view('v', view)
            assert root.get('v') is view and view(0) == 1
        finally:
            published.set()
        thread.join(timeout=3)
        assert not thread.is_alive() and not errors
        assert 'late' in root.loaded_modules and root.get('v') is view

    bounded_process(race)


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
    names = genia.run_source('import base\nbase.f(3)', root, filename=entry)
    assert names == 3  # plain ordinary use of the exported function is unchanged
    assert not any("link" in key.lower() and "view" in key.lower() for key in root.values)


def test_d2a_10_private_tables_are_absent_from_source_access_reflection_and_equality(tmp_path):
    root, entry, module, group = base_world(tmp_path, 'f(x)=x\n')
    unit = callables.GeniaOpenContributionUnit(group.owner, 'ext', [], target=group)
    augmented = dataclasses.replace(module, _ordinary_contributions=(unit,))
    assert augmented == module
    root.set_host('inspected', augmented, visibility='runtime-public')
    for name in ('_ordinary_completions', '_ordinary_contributions', 'link_view', 'FrozenOrdinaryBase'):
        with pytest.raises(NameError):
            genia.run_source('inspected.' + name, root, filename=entry)
    rendered = genia.run_source('[display(inspected), debug_repr(inspected)]', root, filename=entry)
    assert all('_ordinary' not in text and 'FrozenOrdinaryBase' not in text for text in rendered)
