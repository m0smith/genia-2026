"""Python-private slot/reservation tests; terminal stores are controlled fixtures.

No T4/C/F/K protocol or source activation is exercised. Baseline scaffolding
installs only slot data, never lookup/admission/writer behavior, so RED diagnoses
missing guards rather than a missing import or invalid callable.
"""
import ast
from contextlib import contextmanager, nullcontext
import inspect
import textwrap
import threading
from types import SimpleNamespace

import pytest

import genia
from genia import callable as c
from genia import environment as e
from genia.closed_publication import _PublicationTransaction, _publication_window, _publication_barrier
from genia.values import GeniaMap
from tests.unit.model_b_slice_e1_support import record


@contextmanager
def reserved(name='f', *, outer=41, source='f(x) = x', declaring=None):
    """Build genuine guarded records and install private data under the binding lock."""
    root = genia.make_global_env([]) if declaring is None else declaring.root()
    if declaring is None:
        root.set_host(name, outer, visibility='runtime-public', metadata=GeniaMap().put('doc', 'outer'))
        declaring = e.Env(root, rebind_parent=False)
        declaring._unit_scope = declaring
        declaring.module_id = 'slot-module'
    scratch = e.Env(declaring)
    genia.run_source(source, scratch)
    group = c.GeniaClosedFunction._with_self_frame(name, scratch.get(name).records, declaring)
    frame = group.records[0].closure
    txn = _PublicationTransaction(group)
    group._state = 'initializing'
    register = getattr(e, '_register_open_transaction', None)
    with e._BINDING_LOCK:
        if register:
            register(txn)
            declaring._install_provisional_slot(name, txn, strict=False)
            frame._install_provisional_slot(name, txn, strict=True)
        else:
            for env, strict in [(declaring, False), (frame, True)]:
                env._provisional_slots = {name: SimpleNamespace(transaction=txn, strict=strict)}
    try:
        yield root, declaring, frame, group, txn
    finally:
        with e._BINDING_LOCK:
            if register:
                declaring._remove_provisional_slot(name, txn)
                frame._remove_provisional_slot(name, txn)
                e._unregister_open_transaction(txn)
            else:
                declaring._provisional_slots.clear()
                frame._provisional_slots.clear()


def unpublished(operation):
    """Require the lifecycle diagnostic, not a fixture/arity failure."""
    with pytest.raises(RuntimeError, match='^closed-function-not-yet-published: f is not yet published$'):
        operation()


def test_declaring_fallthrough_strict_self_and_admitted_helper():
    with reserved() as (root, declaring, frame, group, txn):
        genia.run_source('helper() = f', declaring)
        assert declaring.get('f') == 41
        unpublished(lambda: frame.get('f'))
        assert declaring.get('helper')() == 41
        with _publication_window(txn):
            assert declaring.get('helper')() is group
            assert frame.get('f') is group
            assert group(7) == 7
            with _publication_barrier():
                assert declaring.get('f') == 41
                unpublished(lambda: frame.get('f'))
        assert root.get('f') == 41


def test_escaped_closure_cannot_obtain_provisional_name():
    with reserved(source='f(x) = [(y) -> f]') as (_, declaring, frame, group, txn):
        with _publication_window(txn):
            escaped = group(0)[0]
            assert escaped(1) is group
        unpublished(lambda: escaped(1))
        declaring.set('other', 3)
        assert frame.get('other') == 3


@pytest.mark.parametrize('state', ['initializing', 'committed', 'failed'])
@pytest.mark.parametrize('admitted', [False, True])
def test_lookup_and_metadata_state_table(state, admitted):
    with reserved() as (_, declaring, frame, group, txn):
        group.metadata = GeniaMap().put('doc', 'final')
        group._state = state  # fixture only: no actual publication or failure
        with _publication_window(txn):
            with (nullcontext() if admitted else _publication_barrier()):
                for env in [declaring, frame]:
                    if state == 'committed':
                        assert env.get('f') is group
                        assert env.get_metadata('f') is group.metadata
                    elif state == 'failed':
                        assert env.get('f') is group if env is frame else env.get('f') == 41
                        if env is frame:
                            with pytest.raises(RuntimeError, match='closed-function-failed-publication:'):
                                env.get_metadata('f')
                        else:
                            assert env.get_metadata('f').get('doc') == 'outer'
                    elif admitted:
                        assert env.get('f') is group
                        unpublished(lambda: env.get_metadata('f'))
                    elif env is frame:
                        unpublished(lambda: env.get('f'))
                        unpublished(lambda: env.get_metadata('f'))
                    else:
                        assert env.get('f') == 41
                        assert env.get_metadata('f').get('doc') == 'outer'


@pytest.mark.parametrize('writer', [
    'check_assign', 'find_assign', 'write', 'set', 'assign', 'function', 'view',
    'declaration', 'commit', 'metadata', 'metadata_ticket', 'import', 'use', 'open',
])
@pytest.mark.parametrize('target', ['declaring', 'self'])
def test_every_writer_rejects_live_reservation(tmp_path, writer, target):
    with reserved() as (root, declaring, frame, group, txn):
        env = {'declaring': declaring, 'self': frame, 'child': e.Env(frame)}[target]
        metadata = GeniaMap().put('doc', 'bad')
        ticket = e.DeclarationTicket(env, 'f')
        ticket.committed = writer == 'metadata_ticket'
        path = tmp_path / 'lazy.genia'
        path.write_text('f = 99', encoding='utf-8')
        root.register_host_autoload('f', 0, str(path), visibility='runtime-public')
        def operation():
            """Invoke the actual writer, taking the lock for lock-owned private seams."""
            if writer == 'check_assign':
                env.check_assign_target('f')
            elif writer == 'find_assign':
                with e._BINDING_LOCK:
                    env.find_assign_target('f')
            elif writer == 'write':
                with e._BINDING_LOCK:
                    env._write_binding('f', 99, True, None, False)
            elif writer == 'set':
                env.set_host('f', 99, visibility='entry-only')
            elif writer == 'assign':
                env.assign('f', 99)
            elif writer == 'function':
                env.define_function(record(env))
            elif writer == 'view':
                env.publish_view('f', object())
            elif writer == 'declaration':
                env.prepare_immutable_declaration('f')
            elif writer == 'commit':
                env.commit_immutable_declaration(ticket, 99)
            elif writer.startswith('metadata'):
                env.merge_binding_metadata('f', metadata, declaration=ticket if writer.endswith('ticket') else None)
            else:
                source = {'import': 'import missing as f', 'use': 'use f from missing with ext',
                          'open': 'open f(x) = x', 'autoload': 'f = 99'}[writer]
                genia.run_source(source, env)
        with pytest.raises(e.ImmutableBindingError, match='immutable binding'):
            operation()
        assert root.get('f') == 41
        assert 'f' not in declaring.values
        assert list(group.metadata.items()) == []


def test_rejection_before_rhs_and_import_link_effects(monkeypatch):
    with reserved() as (_, declaring, _, _, _):
        effects = []
        declaring.set('effect', lambda: effects.append(1))
        for source in ['f = effect()', 'f =: effect()', 'import absent as f', 'use f from absent with ext']:
            with pytest.raises(e.ImmutableBindingError):
                genia.run_source(source, declaring)
        assert effects == []


def test_builder_reserves_without_ordinary_self_binding():
    env = e.Env()
    group = c.GeniaClosedFunction._with_self_frame('f', [record(env)], env)
    frame = group.records[0].closure
    assert frame.values == {}
    assert frame.immutable_names() == frozenset({'f'})
    assert frame.parent is env and frame.unit_scope() is env.unit_scope()
    with pytest.raises(e.ImmutableBindingError):
        frame.assign('f', 1)


def test_transaction_identity_and_ownership_across_threads():
    with reserved() as (_, da, fa, _, ta), reserved() as (_, db, fb, gb, tb):
        assert ta is not tb and ta != tb
        assert {ta, tb} <= e._OPEN_TRANSACTIONS
        ready = threading.Barrier(2)
        errors = []
        def remove_a():
            """Repeat owner-only primitive removals while B is held open."""
            try:
                ready.wait(5)
                with e._BINDING_LOCK:
                    assert not db._remove_provisional_slot('f', ta)
                    assert not fb._remove_provisional_slot('f', ta)
                    da._remove_provisional_slot('f', ta)
                    with pytest.raises(RuntimeError, match='live slots'):
                        e._unregister_open_transaction(ta)
                    fa._remove_provisional_slot('f', ta)
                    e._unregister_open_transaction(ta)
                    e._unregister_open_transaction(ta)
            except BaseException as exc:
                errors.append(exc)
            finally:
                ready.wait(5)
        worker = threading.Thread(target=remove_a)
        worker.start()
        ready.wait(5)
        ready.wait(5)
        worker.join(5)
        assert not worker.is_alive() and errors == []
        assert ta not in e._OPEN_TRANSACTIONS and tb in e._OPEN_TRANSACTIONS
        with _publication_window(tb):
            assert db.get('f') is fb.get('f') is gb
        with pytest.raises(e.ImmutableBindingError):
            db.assign('f', 9)


def test_empty_set_fast_paths_are_unchanged_and_do_not_consult_slots(monkeypatch):
    assert not e._OPEN_TRANSACTIONS
    root, child = e.Env(), None
    root.set_host('x', 7, visibility='runtime-public')
    child = e.Env(root)
    def forbidden(*args):
        """The empty-set branch must not perform slot or admission work."""
        pytest.fail('guarded lookup on empty set')
    monkeypatch.setattr(e.Env, '_get_guarded', forbidden)
    assert child.get('x') == 7
    assert isinstance(child.get_metadata('x'), GeniaMap)
    for method in [e.Env.get, e.Env.get_metadata]:
        tree = ast.parse(textwrap.dedent(inspect.getsource(method)))
        # One guard followed by the original ordinary lookup, with no helper call
        # in the ordinary branch (the baseline source is independently compared).
        guard = next(node for node in tree.body[0].body if isinstance(node, ast.If))
        assert ast.unparse(guard.test) == '_OPEN_TRANSACTIONS'


@pytest.mark.parametrize('terminal', ['committed', 'failed'])
@pytest.mark.parametrize('strict', [False, True])
def test_n3_one_state_read_survives_descriptor_race(monkeypatch, terminal, strict):
    with reserved() as (_, declaring, frame, group, txn):
        ready, resume = threading.Event(), threading.Event()
        original = c.GeniaClosedFunction.__getattribute__
        reads, outcomes = [], []
        def paused(self, name):
            """Pause the reader after its sole state read and before descriptor access."""
            value = original(self, name)
            if self is group and name == '_state' and threading.current_thread() is worker:
                reads.append(value)
                ready.set()
                assert resume.wait(5)
            return value
        monkeypatch.setattr(c.GeniaClosedFunction, '__getattribute__', paused)
        def lookup():
            """A non-owner must decide from its initializing snapshot."""
            try:
                outcomes.append((frame if strict else declaring).get('f'))
            except BaseException as exc:
                outcomes.append(exc)
        worker = threading.Thread(target=lookup)
        worker.start()
        try:
            assert ready.wait(5)
            with e._BINDING_LOCK:
                group._state = terminal
            resume.set()
            worker.join(5)
        finally:
            resume.set()
            worker.join(5)
        assert reads == ['initializing']
        if strict:
            assert isinstance(outcomes[0], RuntimeError)
            assert str(outcomes[0]).startswith('closed-function-not-yet-published:')
        else:
            assert outcomes == [41]
        assert group._txn is txn
        assert (frame.get('f') is group) if terminal == 'committed' or strict else declaring.get('f') == 41


def test_autoload_publication_honors_runtime_slot(tmp_path):
    root = e.Env()
    path = tmp_path / 'lazy.genia'
    path.write_text('f = 99', encoding='utf-8')
    with reserved(declaring=root):
        root.register_host_autoload('f', 0, str(path), visibility='runtime-public')
        with pytest.raises(e.ImmutableBindingError):
            root.try_autoload('f', 0)
        assert 'f' not in root.values
        assert not root.loaded_files and not root.loading_files


@pytest.mark.parametrize('writer', ['check_assign_target', 'find_assign_target', 'assign', 'merge_binding_metadata'])
def test_nearest_reservation_is_never_redirected(writer):
    with reserved() as (root, _, frame, _, _):
        child = e.Env(frame)
        with pytest.raises(e.ImmutableBindingError):
            if writer == 'find_assign_target':
                with e._BINDING_LOCK:
                    child.find_assign_target('f')
            elif writer == 'assign':
                child.assign('f', 99)
            elif writer == 'merge_binding_metadata':
                child.merge_binding_metadata('f', GeniaMap())
            else:
                child.check_assign_target('f')
        assert root.get('f') == 41
