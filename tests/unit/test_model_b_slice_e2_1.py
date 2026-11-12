"""Python-private admission/lineage evidence; no source activation or portable claim.

The RED compatibility scaffold supplies only a descriptor/window when the seam is
absent, never admission. This lets RED observe real E1 dispatch rejection rather
than an import error. GREEN always exercises the production seams.
"""
from contextlib import contextmanager
from contextvars import copy_context
from types import SimpleNamespace
import threading

import pytest

import genia
from genia import callable as c
from genia.ir import IrVar
from genia.http_annotation_binding import resolve_http_annotation
from genia.test_cli import discover_annotated_test_units
from genia.test_kernel import TestUnit, run_test_unit
from genia.values import GeniaMap, GeniaFlow
from tests.unit.model_b_slice_e1_support import record, module_world, prepare_use


@contextmanager
def window(txn):
    """Use the production window; baseline scaffold grants no runtime authority."""
    helper = getattr(c, '_publication_window', None)
    if helper is not None:
        with helper(txn):
            yield
    else:
        txn.window_open = True
        try:
            yield
        finally:
            txn.window_open = False


def fixture(name='f', source='f(x) = x'):
    """Build guarded real records; attach the private transaction before exposure."""
    env = genia.make_global_env([])
    genia.run_source(source, env)
    group = c.GeniaClosedFunction._with_self_frame(name, env.get(name).records, env)
    descriptor = getattr(c, '_PublicationTransaction', None)
    txn = descriptor(group) if descriptor else SimpleNamespace(callable=group, window_open=False, closed=False)
    if descriptor is None:
        group._txn = txn
    group._state = 'initializing'
    env.assign(name, group)
    return env, group, txn


def refused(operation):
    """Require the exact publication failure class, never an arity/setup exception."""
    with pytest.raises(RuntimeError, match='closed-function-not-yet-published:'):
        operation()


def test_admitted_invocation_every_layer_and_bridge():
    env, group, txn = fixture()
    refused(lambda: group(7))
    with window(txn):
        assert group(7) == 7
        assert c.eval_with_tco(lambda: group._dispatch_once((8,)), ()) == 8
        assert group.records[0](9) == 9
        assert c.eval_with_tco(group.records[0], (10,)) == 10
        assert c.invoke_callable(group, [11], tail_position=False) == 11
        assert c.invoke_callable(group.records[0], [12], tail_position=False) == 12
        assert genia.run_source('[7] |> map(f)', env) == [7]
        assert genia.run_source('force(delay(f(13)))', env) == 13
        flow = GeniaFlow(lambda: iter([14]))
        env.set_host('input_flow', flow, visibility='entry-only')
        assert genia.run_source('input_flow |> map(f) |> collect', env) == [14]
    assert not txn.window_open
    refused(lambda: group(7))


def test_lineage_barrier_nested_windows_and_contexts():
    _, outer, txo = fixture()
    _, inner, txi = fixture('g', 'g(x) = x')
    with window(txo):
        assert outer(1) == 1
        refused(lambda: inner(1))
        with window(txi):
            assert outer(2) == inner(2) == 2
            ctx = copy_context()
            # A same-thread scheduler must explicitly enter the real barrier.
            with c._publication_barrier():
                ctx.run(lambda: refused(lambda: outer(3)))
                refused(lambda: inner(3))
            assert inner(4) == 4
        refused(lambda: inner(5))
        assert outer(5) == 5
        errors = []

        def other_thread():
            """A context copy conveys no thread-local authority."""
            try:
                ctx.run(lambda: refused(lambda: outer(6)))
            except BaseException as exc:
                errors.append(exc)

        thread = threading.Thread(target=other_thread)
        thread.start()
        thread.join(5)
        assert not thread.is_alive() and not errors
    ctx.run(lambda: refused(lambda: outer(7)))


def test_window_and_barrier_unwind_baseexception():
    _, group, txn = fixture()
    with pytest.raises(KeyboardInterrupt):
        with window(txn):
            with c._publication_barrier():
                refused(lambda: group(1))
                raise KeyboardInterrupt
    assert not txn.window_open
    with window(txn):
        assert group(2) == 2


@pytest.mark.parametrize('expression', ['doc("f")', 'meta("f")', 'help("f")', 'help(f)'])
def test_admitted_invocation_never_admits_reflection(expression):
    env, group, txn = fixture()
    with window(txn):
        assert group(1) == 1
        refused(lambda: genia.run_source(expression, env))
        refused(lambda: env.get('help')(group))


def test_admitted_does_not_admit_http_or_discovery():
    env, group, txn = fixture('f', 'f() = 1')
    env.binding_owner('f').binding_metadata['f'] = GeniaMap().put('test', 'private')
    with window(txn):
        assert group() == 1
        refused(lambda: resolve_http_annotation(group))
        refused(lambda: discover_annotated_test_units(env))


@pytest.mark.parametrize('operation', ['extend', 'use'])
def test_admitted_does_not_admit_link_targets(tmp_path, operation):
    root, entry, _, group = module_world(tmp_path, closed=True)
    descriptor = getattr(c, '_PublicationTransaction', None)
    txn = descriptor(group) if descriptor else SimpleNamespace(callable=group, window_open=False, closed=False)
    if descriptor is None:
        group._txn = txn
    group._state = 'initializing'
    root.assign('base', root.load_module('base', entry))
    if operation == 'use':
        prepare_use(root, entry, tmp_path, group)
    with window(txn):
        assert group(1) == 1
        source = 'extend base.f(x, y) = y' if operation == 'extend' else 'use f from base with ext'
        refused(lambda: genia.run_source(source, root, filename=entry))


@pytest.mark.parametrize('terminal', ['committed', 'failed'])
def test_n3_state_read_precedes_stable_descriptor_read(monkeypatch, terminal):
    _, group, txn = fixture()
    ready = threading.Event()
    resume = threading.Event()
    original = c.GeniaClosedFunction.__getattribute__
    reads = []
    failures = []

    def paused(self, name):
        """Pause only after the initializing state was read, before descriptor read."""
        value = original(self, name)
        if self is group and name == '_state':
            reads.append(value)
            ready.set()
            assert resume.wait(5)
        return value

    def reader():
        """Report any unexpected exception back to pytest's declaring thread."""
        try:
            refused(lambda: group(1))
        except BaseException as exc:
            failures.append(exc)

    monkeypatch.setattr(c.GeniaClosedFunction, '__getattribute__', paused)
    thread = threading.Thread(target=reader)
    thread.start()
    assert ready.wait(5)
    group._state = terminal
    assert group._txn is txn
    resume.set()
    thread.join(5)
    assert not thread.is_alive() and not failures
    assert reads == ['initializing']
    assert group._txn is txn


@pytest.mark.parametrize('raises', [False, True])
def test_real_native_boundary_hides_and_restores_window(raises):
    _, group, txn = fixture()
    seen = []

    def body():
        """Attempt a provisional call at the real native-test dispatch."""
        refused(lambda: group(1))
        seen.append('refused')
        if raises:
            raise ValueError('body failure')

    with window(txn):
        assert group(1) == 1
        result = run_test_unit(TestUnit('boundary', body))
        assert seen == ['refused']
        assert result['kind'] == ('error' if raises else 'pass')
        assert group(2) == 2


def test_extracted_record_state_precedes_none_and_missing_autoload_arity():
    env, group, _ = fixture()
    refused(lambda: c.invoke_callable(group.records[0], [genia.run_source('none("x")', env)], tail_position=False))
    genia.run_source('h(0) = 0', env)
    refused(lambda: c.invoke_callable(env.get('h'), [1, 2, 3], tail_position=False,
                                     callee_node=IrVar('h'), autoload_resolver=lambda *args: group))


def test_descriptor_single_assignment_and_committed_fast_path(monkeypatch):
    env = genia.make_global_env([])
    group = c.GeniaClosedFunction._with_self_frame('f', [record(env)], env)
    txn = c._PublicationTransaction(group)
    with pytest.raises(RuntimeError, match='fresh building callable'):
        c._PublicationTransaction(group)
    assert group._txn is txn
    group._state = 'committed'
    original = c.GeniaClosedFunction.__getattribute__

    def no_descriptor_read(self, name):
        """A committed invocation must never consult its descriptor or lineage."""
        assert name != '_txn'
        return original(self, name)

    monkeypatch.setattr(c.GeniaClosedFunction, '__getattribute__', no_descriptor_read)
    assert group(7) == 7
    group._check_use()


def test_nonroot_owner_and_debugger_self_scope():
    from genia.environment import Env
    root = genia.make_global_env([])
    module = Env(root)
    module.module_id = 'private-module'
    module._unit_scope = module
    group = c.GeniaClosedFunction._with_self_frame('f', [record(module)], module)
    group._state = 'committed'
    assert group.owner == ('private-module', 'f')
    frame = group.records[0].closure
    assert frame.parent is module and frame.parent is not root
    assert frame.unit_scope() is module
    scopes = []

    class Hooks(c.DebugHooks):
        """Observe actual debugger frames rather than a synthetic scope listing."""
        def on_function_enter(self, name, args, env, span):
            scopes.append(env)

    assert c.eval_with_tco(group.records[0], (7,), Hooks(), True) == 7
    assert scopes[0].parent is frame
    assert list(scopes[0].parent.inspection_bindings()) == ['f']
    assert scopes[0].parent.parent is module
