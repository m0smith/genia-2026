"""Python-host D2b publication/metadata/TCO seams, complementary to shared R16 cases."""

import pytest
import genia
from genia import callable as callables
from genia.environment import Env, ImmutableBindingError
from tests.unit.model_b_d2a_support import base_world, frozen, linking
from tests.unit.test_model_b_d2a_link_publish import snapshot, bounded_process


def public_world(tmp_path):
    """Load real ordinary target/contribution fixtures; import is not selection."""
    root, entry, module, group = base_world(tmp_path, "f(x,y)=x+y\n")
    (tmp_path / "ext.genia").write_text("import base\nextend base.f(0)=7\n")
    genia.run_source("import base\nimport ext", root, filename=entry)
    return root, entry, module, group


def test_public_atomic_checked_writer_failure_and_retry(tmp_path, monkeypatch):
    """Injected writer failure preserves prior binding/tables; retry publishes a full view."""
    root, entry, module, group = public_world(tmp_path)
    root.set_host("f", 99, visibility="runtime-public")
    before = snapshot(root, module)
    original = Env._write_binding

    def fail(env, name, *args, **kwargs):
        """Fault the checked publication before any real mutation."""
        if env is root and name == "f":
            raise RuntimeError("writer sentinel")
        return original(env, name, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Env, "_write_binding", fail)
        with pytest.raises(RuntimeError, match="writer sentinel"):
            genia.run_source("use f from base with ext", root, filename=entry)
    assert snapshot(root, module) == before
    assert genia.run_source("use f from base with ext\nf(0)", root, filename=entry) == 7


def test_public_failed_selection_preserves_previous_view(tmp_path):
    """A duplicate selection cannot replace an already published view."""
    root, entry, module, group = public_world(tmp_path)
    genia.run_source("use f from base with ext", root, filename=entry)
    prior = root.get("f")
    before = snapshot(root, module)
    with pytest.raises(callables.OpenFunctionDuplicateSelectionError):
        genia.run_source("use f from base with ext,ext", root, filename=entry)
    assert root.get("f") is prior and snapshot(root, module) == before and prior(0) == 7


def test_public_view_nonretroactive_after_more_contributions(tmp_path):
    """An entry unit accumulates new records without modifying an earlier view."""
    root, entry, module, group = public_world(tmp_path)
    genia.run_source("use f from base with ext", root, filename=entry)
    old = root.get("f")
    (tmp_path / "extra.genia").write_text("import base\nextend base.f(1)=8\n")
    genia.run_source("import extra\nuse f from base with ext,extra", root, filename=entry)
    assert root.get("f")(1) == 8 and old(0) == 7
    with pytest.raises(callables.OpenFunctionNoMatchingCaseError):
        old(1)


@pytest.mark.parametrize("channel", ["doc", "meta", "help"])
def test_frozen_three_channel_reflection_even_before_public_activation(tmp_path, channel, capsys):
    """D2b reflection must use the three distinct D1 channels, ignoring alias overlays."""
    root, entry, module, group = base_world(
        tmp_path, '@doc "canonical"\nf(x)="inline" x\n@category "alias-category"\na=f\n'
    )
    view = linking().link_view(frozen(module, group), [])
    root.publish_view("v", view)
    genia.run_source('@doc "overlay"\ng=v', root, filename=entry)
    if channel == "doc":
        assert genia.run_source('doc("g")', root) == "canonical"
    elif channel == "meta":
        meta = genia.run_source('meta("g")', root)
        assert meta.get("doc") == "canonical" and meta.get("category", None) is None
    else:
        genia.run_source("help(g)", root)
        output = capsys.readouterr().out
        assert "f (linked ordinary function view)" in output
        assert "inline" in output and "alias-category" in output and "  1. base:1" in output
        assert "base:2" not in output
        assert str(tmp_path) not in output and "overlay" not in output


def test_public_self_tco_uses_published_view(tmp_path):
    """Source-selected view recurses through its defining closure without host stack growth."""
    root, entry, module, group = base_world(
        tmp_path, "f(n,acc)=(0,a)->a | (k,a)->walk(k - 1, a + 1)\nwalk=f\n"
    )
    (tmp_path / "ext.genia").write_text("import base\nextend base.f()=0\n")
    genia.run_source("import base\nimport ext\nuse f from base with ext", root, filename=entry)
    group.records[0].closure.publish_view("walk", root.get("f"))
    assert genia.run_source("f(60000,0)", root, filename=entry) == 60000


def test_public_publication_overlaps_real_module_load(tmp_path):
    """Use executes while another loader is paused; process containment bounds deadlocks."""
    import threading

    root, entry, module, group = public_world(tmp_path)

    def race():
        """Hold user initialization outside the binding lock while public selection runs."""
        entered = threading.Event()
        done = threading.Event()
        errors = []

        def pause():
            """Wait for selection to complete during module evaluation."""
            entered.set()
            assert done.wait(3)

        root.set_host("pause", pause, visibility="runtime-public")
        (tmp_path / "late.genia").write_text("pause()\nf(x)=x\n")

        def load():
            """Collect loader failures for the supervising process."""
            try:
                root.load_module("late", entry)
            except BaseException as e:
                errors.append(e)

        thread = threading.Thread(target=load, daemon=True)
        thread.start()
        assert entered.wait(3)
        try:
            assert genia.run_source("use f from base with ext\nf(0)", root, filename=entry) == 7
        finally:
            done.set()
        thread.join(3)
        assert not thread.is_alive() and not errors

    bounded_process(race)


def test_public_use_cannot_replace_immutable_name(tmp_path):
    """Immutable-name precheck wins without replacing state or running a view."""
    root, entry, module, group = public_world(tmp_path)
    genia.run_source("f =: 99", root, filename=entry)
    before = snapshot(root, module)
    with pytest.raises(ImmutableBindingError):
        genia.run_source("use f from base with ext", root, filename=entry)
    assert root.get("f") == 99 and snapshot(root, module) == before


def test_escaped_failed_origin_has_no_public_extension_authority(tmp_path):
    """Same-spelling escaped G from a failed attempt never gains a completion witness."""
    root = genia.make_global_env([])
    entry = str(tmp_path / "main.genia")
    escaped = []
    root.set_host("retain", escaped.append, visibility="runtime-public")
    (tmp_path / "origin.genia").write_text("f(x)=x\nretain(f)\n1/0\n")
    with pytest.raises(ZeroDivisionError):
        root.load_module("origin", entry)
    root.set_host("escaped", escaped[0], visibility="runtime-public")
    (tmp_path / "relay.genia").write_text("f=escaped\n")
    with pytest.raises(callables.OpenFunctionTargetNotOpenError):
        genia.run_source("import relay\nextend relay.f(0)=1", root, filename=entry)
    assert "origin" not in root.loaded_modules


def test_public_use_holds_writer_lock_once(tmp_path, monkeypatch):
    """Source resolution/build precede one checked publication hold."""
    from genia import environment as environments
    from tests.unit.test_model_b_d2a_link_publish import CountingLock

    root, entry, module, group = public_world(tmp_path)
    lock = CountingLock()
    monkeypatch.setattr(environments, "_BINDING_LOCK", lock)
    genia.run_source("use f from base with ext", root, filename=entry)
    assert lock.holds == 1
    assert root.get("f")(0) == 7


def test_two_public_use_writers_are_observed_during_publication(tmp_path):
    """Observe real source selections at checked-writer boundaries in a bounded worker."""
    import queue
    import threading

    root, entry, module, group = public_world(tmp_path)
    (tmp_path / "extra.genia").write_text("import base\nextend base.f(1)=8\n")
    genia.run_source("import extra\nuse f from base with ext", root, filename=entry)

    def race():
        """Synchronize two source writers and acknowledge every complete candidate."""
        barrier = threading.Barrier(3, timeout=3)
        messages = queue.Queue()
        errors = []
        original = Env._write_binding

        def observe(env, name, value, *args, **kwargs):
            """Pause before and after the real checked write, under its actual lock."""
            if env is root and name == "f":
                for phase in ("before", "after"):
                    if phase == "after":
                        original(env, name, value, *args, **kwargs)
                    acknowledged = threading.Event()
                    messages.put(acknowledged)
                    assert acknowledged.wait(3)
            else:
                original(env, name, value, *args, **kwargs)

        def writer(unit):
            """Run independent parser/evaluator requests selecting one contribution."""
            try:
                barrier.wait()
                for _ in range(4):
                    genia.run_source("use f from base with " + unit, root, filename=entry)
            except BaseException as error:
                errors.append(error)

        Env._write_binding = observe
        threads = [
            threading.Thread(target=writer, args=(unit,), daemon=True) for unit in ("ext", "extra")
        ]
        try:
            for thread in threads:
                thread.start()
            barrier.wait()
            for _ in range(16):
                ack = messages.get(timeout=3)
                try:
                    current = root.get("f")
                    assert isinstance(current, callables.GeniaLinkedOpenFunction)
                    assert current.base.group is group
                    selected = [u.declaring_module_id for u in current.units]
                    assert selected in (["ext"], ["extra"])
                    assert current(0 if selected == ["ext"] else 1) == (
                        7 if selected == ["ext"] else 8
                    )
                finally:
                    ack.set()
            for thread in threads:
                thread.join(timeout=3)
            assert not errors and not any(t.is_alive() for t in threads)
        finally:
            Env._write_binding = original

    bounded_process(race)


def test_public_views_keep_completed_base_after_live_group_mutation(tmp_path):
    """Both old and later selections use the original completion, while live calls can change."""
    from genia.ir import IrLiteral

    root, entry, module, group = public_world(tmp_path)
    genia.run_source("use f from base with ext", root, filename=entry)
    assert genia.run_source("f(1,2)", root, filename=entry) == 3
    old = root.get("f")
    group.records[0].body = IrLiteral(999)
    assert group(1, 2) == 999
    genia.run_source("use f from base with ext", root, filename=entry)
    new = root.get("f")
    assert old is not new
    assert [old(1, 2), new(1, 2)] == [3, 3]


@pytest.mark.parametrize(
    ("source", "present", "absent"),
    [
        ('x=1\n@doc "canonical"\nf(x)=x\n', "  1. base:2", "base:3"),
        ("x=1\nf(x)=x\n", "  1. base:2", "base:1"),
    ],
    ids=["annotation-start-after-prefix", "unannotated-head"],
)
def test_frozen_help_preserves_original_span_start(tmp_path, capsys, source, present, absent):
    """Discriminate annotation-inclusive D1 spans from shifted/head-only rendering."""
    root, entry, module, group = base_world(tmp_path, source)
    root.publish_view("v", linking().link_view(frozen(module, group), []))
    genia.run_source("help(v)", root, filename=entry)
    output = capsys.readouterr().out
    assert present in output and absent not in output
    assert str(tmp_path) not in output


def test_public_use_preserves_literal_dotted_module_alias(tmp_path):
    """A dotted import alias remains one Env name, never a rename-on-use expression."""
    root, entry, module, group = public_world(tmp_path)
    genia.run_source("import base as a.b\nuse f from a.b with ext", root, filename=entry)
    assert root.get("a.b") is module
    view = root.get("f")
    assert view.base.group is group
    assert view(0) == 7 and view(1, 2) == 3
