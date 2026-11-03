"""Python-host binding-lock scheduling proofs, not portable language authority.

The accepted shared cases own observable linking behavior. These tests exercise
actual concurrent source declarations and the private module-completion boundary.
"""

import threading
from unittest.mock import patch

import genia
from genia import callable as callables
from genia import environment as environments
from genia import ordinary_completion as completions
from tests.unit.model_b_d2a_support import base_world
from tests.unit.test_model_b_d2a_link_publish import CountingLock, bounded_process


def test_concurrent_ordinary_contributions_accumulate_without_lost_updates(tmp_path):
    """Pause the first locked build; a second source writer must acquire that same lock."""
    root, entry, module, group = base_world(tmp_path, "f(x,y)=x+y\n")
    genia.run_source("import base", root, filename=entry)

    def race():
        """Observe both lock boundaries without sleeps, in a deadlock-contained child."""
        built = threading.Event()
        release = threading.Event()
        attempted = threading.Event()
        errors = []
        units = []

        class ObservedLock(CountingLock):
            """Signal the competing acquisition before the existing bounded acquire."""

            def __enter__(self):
                """Expose the second writer's attempt even while the first holds ownership."""
                if threading.current_thread().name == "second-writer":
                    attempted.set()
                return super().__enter__()

        lock = ObservedLock()
        constructor = callables.GeniaOpenContributionUnit

        def construct(*args, **kwargs):
            """Require a held writer lock and pause before publishing the first built unit."""
            assert lock.owner == threading.get_ident()
            unit = constructor(*args, **kwargs)
            units.append(unit)
            if threading.current_thread().name == "first-writer":
                built.set()
                assert release.wait(2)
            return unit

        def writer(value):
            """Declare a real source contribution and retain thread exceptions for pytest."""
            try:
                genia.run_source(f"extend base.f({value})={value}", root, filename=entry)
            except BaseException as error:
                errors.append(error)

        with (
            patch.object(environments, "_BINDING_LOCK", lock),
            patch.object(callables, "GeniaOpenContributionUnit", construct),
        ):
            first = threading.Thread(target=writer, args=(0,), name="first-writer", daemon=True)
            second = threading.Thread(target=writer, args=(1,), name="second-writer", daemon=True)
            first.start()
            try:
                assert built.wait(2)
                second.start()
                assert attempted.wait(2)
                assert lock.owner == first.ident
            finally:
                release.set()
            first.join(2)
            second.join(2)
            assert not first.is_alive() and not second.is_alive() and not errors
        current = root.ordinary_contributions[id(group)]
        assert current.target is group and len(current.clauses) == 2
        assert len(units[0].clauses) == 1 and current is units[1]
        assert lock.holds == 2
        before = current
        with patch.object(environments, "_BINDING_LOCK", lock):
            try:
                genia.run_source("extend base.f(0)=99", root, filename=entry)
            except callables.OpenFunctionDuplicateClauseError:
                pass
            else:
                raise AssertionError("duplicate contribution unexpectedly published")
        assert root.ordinary_contributions[id(group)] is before

    bounded_process(race)


def test_ordinary_store_and_module_completion_share_the_writer_lock(tmp_path):
    """Real loader capture and each contribution build hold one shared binding lock."""
    root, entry, module, group = base_world(tmp_path, "f(x,y)=x+y\n")
    (tmp_path / "ext.genia").write_text(
        "import base\nextend base.f(0)=7\nmarker=0\nextend base.f(1)=8\n", encoding="utf-8"
    )
    lock = CountingLock()
    constructor = callables.GeniaOpenContributionUnit
    prepare = completions.prepare_module_completions
    units = []
    captured = []

    def construct(*args, **kwargs):
        """Observe a fully built replacement without lending its records to old units."""
        assert lock.owner == threading.get_ident()
        unit = constructor(*args, **kwargs)
        units.append(unit)
        return unit

    def capture(module_env, exports):
        """Prove loader capture is inside the same lock as accumulated-unit replacement."""
        if module_env.module_identity() == "ext":
            assert lock.owner == threading.get_ident()
            captured.append(module_env.ordinary_contributions[id(group)])
        return prepare(module_env, exports)

    with (
        patch.object(environments, "_BINDING_LOCK", lock),
        patch.object(callables, "GeniaOpenContributionUnit", construct),
        patch.object(completions, "prepare_module_completions", capture),
    ):
        result = root.load_module("ext", entry)
    assert len(units) == 2 and [len(unit.clauses) for unit in units] == [1, 2]
    assert captured == [units[1]]
    assert result._ordinary_contributions == (units[1],)
    assert result._ordinary_contributions[0].target is group
