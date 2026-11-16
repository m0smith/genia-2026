"""Python-host RED-B oracles; execution is blocked at the deliberate scaffold.

Contract section 4; Slice E design sections 4/6/10.3. Real E1/E2 builders and
the production _run_publication entry are used throughout. Instrumentation
only delegates existing operations, observes them or raises one fault; it
never supplies lifecycle transitions. No multi-fault/persistent-OOM claim.
T0-T3, public activation and shared portability evidence are out of scope.

Coverage limits: step-local C1/C2b and a real HTTP dispatch are not claimed.
Those need a separately reviewed reachable operation/fixture, not invented
hooks. C2/C3/P3/K4 use existing attribute stores; C4/C5 use actual table writes;
P2/P4/P5/K1-K3 use existing private primitive boundaries. No production edits.
"""

import ast
from contextlib import contextmanager
import inspect
import textwrap
import threading

import pytest

import genia
from genia import callable as c
from genia import closed_publication as p
from genia import environment as e
from genia.values import GeniaMap
from tests.unit.model_b_slice_e1_support import record


NOT_READY = 'closed-function-not-yet-published: f is not yet published'
FAILED = 'closed-function-failed-publication: closed function failed publication'


def world(name='f', declaring=None):
    """Build only T3 data, without any lifecycle stores or slot installation."""
    if declaring is None:
        root = genia.make_global_env([])
        root.set_host(name, 41, visibility='runtime-public',
                      metadata=GeniaMap().put('doc', 'outer'))
        declaring = e.Env(root, rebind_parent=False)
    group = c.GeniaClosedFunction._with_self_frame(name, [record(declaring, name)], declaring)
    txn = p._PublicationTransaction(group)
    assert group._state == 'building' and not txn.closed and not txn.window_open
    assert txn.self_frame.parent is declaring
    return txn


def terminal(txn, state, metadata=None):
    """Assert final tables after both owner slots have actually disappeared."""
    group, declaring, frame = txn.callable, txn.declaring_scope, txn.self_frame
    name = group.name
    assert group._state == state and group._txn is txn
    assert txn.closed and not txn.window_open and txn not in e._OPEN_TRANSACTIONS
    for scope in (declaring, frame):
        assert name not in (scope._provisional_slots or {})
    assert frame.values[name] is frame.get(name) is group
    assert frame.immutable_names() == frozenset({name})
    if state == 'committed':
        assert declaring.values[name] is declaring.get(name) is group
        assert name in declaring.immutable_names()
        for observed in (group.metadata, declaring.get_metadata(name), frame.get_metadata(name)):
            assert dict(observed.items()) == dict(metadata.items())
        assert group(7) == 7
    else:
        assert name not in declaring.values and name not in declaring.binding_metadata
        assert name not in declaring.immutable_names()
        # Failed callable metadata is inaccessible; do not prescribe erasure of
        # a private C2 store when the single fault occurred after its effect.
        with pytest.raises(RuntimeError, match=f'^{FAILED}$'):
            group._check_use()
        with pytest.raises(RuntimeError, match=f'^{FAILED}$'):
            group(7)
        with pytest.raises(RuntimeError, match=f'^{FAILED}$'):
            frame.get_metadata(name)
        with pytest.raises(e.ImmutableBindingError):
            frame.merge_binding_metadata(name, GeniaMap().put('doc', 'bad'))
        ticket = declaring.prepare_immutable_declaration(name)
        declaring.commit_immutable_declaration(ticket, 99)
        assert declaring.get(name) == 99 and frame.get(name) is group


def join_observer(operation):
    """Run a true non-owner and propagate its exception instead of losing it."""
    results, errors = [], []

    def observe():
        """Capture the exact outcome from the foreign thread."""
        try:
            results.append(operation())
        except BaseException as exc:
            errors.append(exc)

    worker = threading.Thread(target=observe, daemon=True)
    worker.start()
    worker.join(5)
    assert not worker.is_alive(), 'reader blocked on a lock held by the owner'
    if errors:
        raise errors[0]
    return results[0]


def require_unpublished(operation):
    """Pin complete existing diagnostic identity, not only exception class."""
    with pytest.raises(RuntimeError) as caught:
        operation()
    assert str(caught.value) == NOT_READY


def test_l1_l4_l9_initializing_visibility_writers_and_unlocked_body():
    """Non-owner refuses use, owner resolves self; every user callback is unlocked."""
    txn = world()
    group, scope, frame = txn.callable, txn.declaring_scope, txn.self_frame
    metadata = GeniaMap().put('doc', 'final')
    effects = []

    def check_lock():
        """Acquire nonblocking so a regression fails without deadlocking pytest."""
        acquired = e._BINDING_LOCK.acquire(False)
        assert acquired, 'binding lock held while running user code'
        e._BINDING_LOCK.release()
        return 7

    scope.set_host('body_probe', check_lock, visibility='entry-only')
    # Use a real body that calls the probe, not a monkeypatched dispatcher.
    scratch = e.Env(scope)
    genia.run_source('f(x) = body_probe()', scratch)
    group = c.GeniaClosedFunction._with_self_frame('f', scratch.get('f').records, scope)
    txn = p._PublicationTransaction(group)
    frame = txn.self_frame
    scope.set_host('effect', lambda: effects.append('rhs'), visibility='entry-only')

    def annotations(self_frame):
        """Exercise admission and code execution while the real driver owns T5."""
        assert self_frame is frame and check_lock() == 7
        assert group(0) == 7
        assert scope.get('f') is frame.get('f') is group

        def external():
            """Read and attempt writes on a non-admitted foreign thread."""
            assert scope.get('f') == 41
            assert scope.get_metadata('f').get('doc') == 'outer'
            for operation in (lambda: group(0), group._check_use,
                              lambda: frame.get('f'), lambda: frame.get_metadata('f')):
                require_unpublished(operation)
            for target in (scope, frame, e.Env(frame)):
                with pytest.raises(e.ImmutableBindingError):
                    genia.run_source('f = effect()', target)
            return True

        assert join_observer(external)
        assert effects == []
        return metadata

    assert p._run_publication(txn, annotations) is group
    terminal(txn, 'committed', metadata)


@pytest.mark.parametrize('error_type', [ValueError, KeyboardInterrupt])
def test_l2_t5_effects_and_baseexception_identity(error_type):
    """One annotation error leaves its escaped reference failed and name reusable."""
    txn = world()
    error, effects = error_type('annotation'), []

    def annotations(frame):
        """Retain a real admitted reference as a persistent annotation effect."""
        effects.append(frame.get('f'))
        raise error

    with pytest.raises(error_type) as caught:
        p._run_publication(txn, annotations)
    assert caught.value is error and effects == [txn.callable]
    terminal(txn, 'failed')


class SingleFault:
    """One fault total, raised before or after a delegated production effect."""

    def __init__(self, after, error=None):
        """Keep fault identity and trigger count outside lifecycle data."""
        self.after, self.error, self.hits = after, error or MemoryError('single fault'), 0

    def run(self, operation):
        """Retry calls pass through after the one injected exception."""
        if self.hits:
            return operation()
        self.hits += 1
        if not self.after:
            raise self.error
        operation()
        raise self.error


@pytest.mark.parametrize('step', ['register', 'declaring_slot', 'self_slot'])
@pytest.mark.parametrize('after', [False, True])
def test_l2_t4_primitive_faults(monkeypatch, step, after):
    """P2/P4/P5 single faults discard/fail and remove only this transaction."""
    txn, fault = world(), SingleFault(after, KeyboardInterrupt('T4 interrupt'))
    if step == 'register':
        original = e._register_open_transaction

        def register(candidate):
            """Delegate the exact registry effect once, then inject."""
            return fault.run(lambda: original(candidate)) if candidate is txn else original(candidate)

        monkeypatch.setattr(e, '_register_open_transaction', register)
    else:
        original = e.Env._install_provisional_slot
        target = txn.self_frame if step == 'self_slot' else txn.declaring_scope

        def install(scope, name, candidate, *, strict):
            """Instrument an actual slot insertion without installing a fake slot."""
            def operation():
                """Call through unchanged to the real installer."""
                return original(scope, name, candidate, strict=strict)
            return fault.run(operation) if scope is target and candidate is txn else operation()

        monkeypatch.setattr(e.Env, '_install_provisional_slot', install)
    with pytest.raises(KeyboardInterrupt) as caught:
        p._run_publication(txn, lambda frame: GeniaMap())
    assert caught.value is fault.error and fault.hits == 1
    assert txn.closed and txn not in e._OPEN_TRANSACTIONS
    assert not txn.window_open
    for scope in (txn.declaring_scope, txn.self_frame):
        assert 'f' not in (scope._provisional_slots or {})
    assert 'f' not in txn.declaring_scope.values
    if step == 'register':
        assert txn.callable._state == 'building'
    else:
        terminal(txn, 'failed')


@pytest.mark.parametrize('field,value,state', [
    ('_state', 'initializing', 'failed'),
    ('metadata', None, 'failed'),
    ('_state', 'committed', 'committed'),
])
@pytest.mark.parametrize('after', [False, True])
def test_l2_l3_state_and_metadata_store_faults(monkeypatch, field, value, state, after):
    """P3/C2/C3: inspect real state at interrupted C3; committed never fails."""
    txn, fault = world(), SingleFault(after)
    group = txn.callable
    metadata, states = GeniaMap().put('doc', 'final'), []
    original = c.GeniaClosedFunction.__setattr__

    def store(candidate, name, held):
        """Delegate every actual store, injecting only at the selected one."""
        def operation():
            """Record actual lifecycle writes, never create one."""
            original(candidate, name, held)
            if candidate is group and name == '_state':
                states.append(held)
        if candidate is group and name == field and (field == 'metadata' or held == value):
            return fault.run(operation)
        return operation()

    monkeypatch.setattr(c.GeniaClosedFunction, '__setattr__', store)
    with pytest.raises(MemoryError) as caught:
        p._run_publication(txn, lambda frame: metadata)
    assert caught.value is fault.error and fault.hits == 1
    expected = state if field != '_state' or value != 'committed' or after else 'failed'
    if field == '_state' and value == 'initializing' and not after:
        assert group._state == 'building'  # discarded before reachability
        assert txn.closed and txn not in e._OPEN_TRANSACTIONS
        assert not txn.window_open and 'f' not in txn.declaring_scope.values
        for scope in (txn.declaring_scope, txn.self_frame):
            assert 'f' not in (scope._provisional_slots or {})
    else:
        terminal(txn, expected, metadata)
    if 'committed' in states:
        assert 'failed' not in states[states.index('committed') + 1:]


@pytest.mark.parametrize('which', ['declaring_metadata', 'declaring_values', 'self_metadata', 'self_values'])
@pytest.mark.parametrize('after', [False, True])
def test_l2a_c4_c5_allocation_rolls_forward_under_same_lock(monkeypatch, which, after):
    """Actual dictionary insertions before/after effect; one MemoryError only."""
    txn, fault = world(), SingleFault(after)
    scope = txn.self_frame if which.startswith('self') else txn.declaring_scope
    attribute = 'binding_metadata' if which.endswith('metadata') else 'values'
    metadata = GeniaMap().put('doc', 'final')
    lock_observations = []
    real_lock = e._BINDING_LOCK

    class LockObserver:
        """Delegate the original lock, counting real hold boundaries only."""

        def __init__(self):
            self.generation = 0

        def __enter__(self):
            self.acquire()
            return self

        def __exit__(self, *exc):
            self.release()

        def acquire(self, *args, **kwargs):
            """Count only a successful acquisition of the original lock."""
            acquired = real_lock.acquire(*args, **kwargs)
            if acquired:
                self.generation += 1
            return acquired

        def release(self):
            """Release exactly the original binding lock."""
            real_lock.release()

        def locked(self):
            return real_lock.locked()

    observed_lock = LockObserver()
    monkeypatch.setattr(e, '_BINDING_LOCK', observed_lock)

    class Writes(dict):
        """Delegate actual dict writes, including simulated allocating insertions."""

        def __setitem__(self, key, value):
            """Observe continuous owner lock and invoke one allocation fault."""
            if key == 'f':
                assert txn.callable._state == 'committed'
                assert real_lock.locked()
                lock_observations.append(observed_lock.generation)
                return fault.run(lambda: super(Writes, self).__setitem__(key, value))
            return super().__setitem__(key, value)

    monkeypatch.setattr(scope, attribute, Writes(getattr(scope, attribute)))
    with pytest.raises(MemoryError) as caught:
        p._run_publication(txn, lambda frame: metadata)
    assert caught.value is fault.error and fault.hits == 1
    assert len(lock_observations) >= 2 and len(set(lock_observations)) == 1
    terminal(txn, 'committed', metadata)


@pytest.mark.parametrize('step', ['K1', 'K2', 'K3', 'K4'])
def test_l2_cleanup_after_effect_is_idempotent(monkeypatch, step):
    """Repeat owner cleanup after a single interrupt, with terminal tables intact."""
    txn, fault = world(), SingleFault(True, KeyboardInterrupt('cleanup'))
    metadata = GeniaMap().put('doc', 'final')
    if step in ('K1', 'K2'):
        original = e.Env._remove_provisional_slot
        target = txn.declaring_scope if step == 'K1' else txn.self_frame

        def remove(scope, name, candidate):
            """Delegate conditional owner removal before raising once."""
            def operation():
                """Call through unchanged to the real remover."""
                return original(scope, name, candidate)
            return fault.run(operation) if scope is target and candidate is txn else operation()

        monkeypatch.setattr(e.Env, '_remove_provisional_slot', remove)
    elif step == 'K3':
        original = e._unregister_open_transaction

        def unregister(candidate):
            """Delegate registry discard before raising once."""
            return fault.run(lambda: original(candidate)) if candidate is txn else original(candidate)

        monkeypatch.setattr(e, '_unregister_open_transaction', unregister)
    else:
        original = p._PublicationTransaction.__setattr__

        def close(candidate, name, value):
            """Observe the real K4 write, never close the descriptor ourselves."""
            def operation():
                """Perform only the actual descriptor write being instrumented."""
                return original(candidate, name, value)
            return fault.run(operation) if candidate is txn and name == 'closed' and value else operation()

        monkeypatch.setattr(p._PublicationTransaction, '__setattr__', close)
    with pytest.raises(KeyboardInterrupt) as caught:
        p._run_publication(txn, lambda frame: metadata)
    assert caught.value is fault.error and fault.hits == 1
    terminal(txn, 'committed', metadata)


def test_l10_n1_same_scope_immutable_writer_after_t5(monkeypatch):
    """Pause actual window exit, then commit another immutable on a real thread."""
    txn, metadata = world(), GeniaMap().put('doc', 'final')
    original = p._publication_window

    @contextmanager
    def window(candidate):
        """Delegate admission/revocation, with an interleaving after real T5."""
        with original(candidate):
            yield
        if candidate is txn:
            def writer():
                """A genuine same-scope writer commits while owner is between locks."""
                ticket = txn.declaring_scope.prepare_immutable_declaration('g')
                txn.declaring_scope.commit_immutable_declaration(ticket, 3)
                return True
            assert join_observer(writer)

    monkeypatch.setattr(p, '_publication_window', window)
    assert p._run_publication(txn, lambda frame: metadata) is txn.callable
    terminal(txn, 'committed', metadata)
    for name in ('f', 'g'):
        with pytest.raises(e.ImmutableBindingError):
            txn.declaring_scope.assign(name, 9)


def test_l6_nested_transaction_through_real_module_load(tmp_path):
    """A synchronous module bridge retains outer lineage around inner publication."""
    outer, inner = world(), world(name='h')
    root = outer.declaring_scope.root()
    metadata = GeniaMap().put('doc', 'final')

    def inner_annotations(frame):
        """Both genuine windows coexist; inner exit must retain outer authority."""
        assert p._publication_admitted(outer) and p._publication_admitted(inner)
        assert frame.get('h') is inner.callable
        return metadata

    def load_inner():
        """Host bridge invokes the actual inner entry during module initialization."""
        return p._run_publication(inner, inner_annotations)

    root.set_host('load_inner', load_inner, visibility='runtime-public')
    (tmp_path / 'nested.genia').write_text('h = load_inner()\n', encoding='utf-8')

    def outer_annotations(frame):
        """Load the real module, then verify the surviving outer window."""
        module = frame.load_module('nested', str(tmp_path / 'entry.genia'))
        assert module.get_export('h') is inner.callable
        assert p._publication_admitted(outer) and not p._publication_admitted(inner)
        return metadata

    assert p._run_publication(outer, outer_annotations) is outer.callable
    terminal(inner, 'committed', metadata)
    terminal(outer, 'committed', metadata)


@pytest.mark.parametrize('cleanup_step', ['K1', 'K2', 'K3'])
def test_l11_n2_owner_cleanup_fault_keeps_other_transaction_live(monkeypatch, cleanup_step):
    """A single cleanup fault in inner A cannot remove outer B's reservations."""
    active, closing = world(), world(name='h')
    fault, metadata = SingleFault(True, KeyboardInterrupt('A cleanup')), GeniaMap()
    if cleanup_step == 'K3':
        original = e._unregister_open_transaction

        def unregister(candidate):
            """Discard only the real closing owner, then interrupt once."""
            return fault.run(lambda: original(candidate)) if candidate is closing else original(candidate)

        monkeypatch.setattr(e, '_unregister_open_transaction', unregister)
    else:
        original = e.Env._remove_provisional_slot
        target = closing.declaring_scope if cleanup_step == 'K1' else closing.self_frame

        def remove(scope, name, candidate):
            """Delegate the actual owner-specific conditional removal."""
            def operation():
                """Call the existing owner-conditional removal unchanged."""
                return original(scope, name, candidate)
            return fault.run(operation) if candidate is closing and scope is target else operation()

        monkeypatch.setattr(e.Env, '_remove_provisional_slot', remove)

    def annotations(frame):
        """Run A while B is live, inspecting B only after A has exited."""
        with pytest.raises(KeyboardInterrupt) as caught:
            p._run_publication(closing, lambda inner: metadata)
        assert caught.value is fault.error and fault.hits == 1
        terminal(closing, 'committed', metadata)
        assert active in e._OPEN_TRANSACTIONS and not active.closed
        assert active.declaring_scope._provisional_slots['f'].transaction is active
        assert frame._provisional_slots['f'].transaction is active
        assert frame.get('f') is active.declaring_scope.get('f') is active.callable
        with pytest.raises(e.ImmutableBindingError):
            active.declaring_scope.assign('f', 9)
        return metadata

    assert p._run_publication(active, annotations) is active.callable
    terminal(active, 'committed', metadata)


@pytest.mark.parametrize('outcome', ['committed', 'failed'])
@pytest.mark.parametrize('entry', ['invocation', 'declaring', 'self'])
def test_l12_n3_paused_state_read_retains_descriptor(monkeypatch, outcome, entry):
    """Pause a real reader after initializing read while owner reaches terminal."""
    txn = world()
    group, metadata = txn.callable, GeniaMap().put('doc', 'final')
    original = c.GeniaClosedFunction.__getattribute__
    paused, resume = threading.Event(), threading.Event()
    workers, reads, observations = [], [], []
    annotation_error = ValueError('annotation')

    def getattribute(candidate, name):
        """Return actual state snapshot after owner finishes; never change state."""
        value = original(candidate, name)
        if (candidate is group and name == '_state' and workers
                and threading.current_thread() is workers[0]):
            reads.append(value)
            if value == 'initializing':
                paused.set()
                assert resume.wait(5), 'owner did not complete publication/failure'
        return value

    monkeypatch.setattr(c.GeniaClosedFunction, '__getattribute__', getattribute)

    def reader():
        """Keep the original snapshot outcome, including exact diagnostic."""
        try:
            operation = {'invocation': lambda: group(7),
                         'declaring': lambda: txn.declaring_scope.get('f'),
                         'self': lambda: txn.self_frame.get('f')}[entry]
            observations.append(operation())
        except BaseException as exc:
            observations.append(exc)

    def annotations(frame):
        """Start reader only in a genuine window, then let owner run to terminal."""
        worker = threading.Thread(target=reader, daemon=True)
        workers.append(worker)
        worker.start()
        assert paused.wait(5), 'reader never reached initializing state'
        if outcome == 'failed':
            raise annotation_error
        return metadata

    try:
        if outcome == 'failed':
            with pytest.raises(ValueError) as caught:
                p._run_publication(txn, annotations)
            assert caught.value is annotation_error
        else:
            assert p._run_publication(txn, annotations) is group
    finally:
        resume.set()
        for worker in workers:
            worker.join(5)
            assert not worker.is_alive()
    assert reads == ['initializing'] and group._txn is txn
    if entry == 'declaring':
        assert observations == [41]
    else:
        assert len(observations) == 1 and isinstance(observations[0], RuntimeError)
        assert str(observations[0]) == NOT_READY
    terminal(txn, outcome, metadata)


@pytest.mark.parametrize('after', [False, True])
def test_l1_c3_synchronized_reader_sees_one_complete_state(monkeypatch, after):
    """Observe on a foreign thread immediately before/after actual C3 store."""
    txn, metadata = world(), GeniaMap().put('doc', 'final')
    group = txn.callable
    original = c.GeniaClosedFunction.__setattr__
    seen = []

    def observe():
        """Do not acquire owner lock; all reads must agree at this pause."""
        if after:
            assert group(7) == 7
            group._check_use()
            for scope in (txn.declaring_scope, txn.self_frame):
                assert scope.get('f') is group
                assert dict(scope.get_metadata('f').items()) == dict(metadata.items())
        else:
            require_unpublished(lambda: group(7))
            require_unpublished(group._check_use)
            require_unpublished(lambda: txn.self_frame.get('f'))
            assert txn.declaring_scope.get('f') == 41
        seen.append('after' if after else 'before')
        return True

    def store(candidate, name, value):
        """Wrap the real linearization store with a joined non-owner observer."""
        selected = candidate is group and name == '_state' and value == 'committed'
        if selected and not after:
            assert join_observer(observe)
        original(candidate, name, value)
        if selected and after:
            assert join_observer(observe)

    monkeypatch.setattr(c.GeniaClosedFunction, '__setattr__', store)
    assert p._run_publication(txn, lambda frame: metadata) is group
    assert seen == ['after' if after else 'before']
    terminal(txn, 'committed', metadata)


def test_l8_empty_set_lookup_keeps_existing_structural_fast_path(monkeypatch):
    """The no-transaction control is structural, never a timing assertion."""
    assert not e._OPEN_TRANSACTIONS

    def forbidden(*args, **kwargs):
        """Fail if ordinary reads consult guarded transaction machinery."""
        pytest.fail('guarded lookup while no transaction is open')

    monkeypatch.setattr(e.Env, '_get_guarded', forbidden)
    scope = e.Env()
    scope.set_host('x', 7, visibility='runtime-public', metadata=GeniaMap().put('doc', 'x'))
    assert scope.get('x') == 7 and scope.get_metadata('x').get('doc') == 'x'
    for method in (e.Env.get, e.Env.get_metadata):
        tree = ast.parse(textwrap.dedent(inspect.getsource(method)))
        guard = next(node for node in tree.body[0].body if isinstance(node, ast.If))
        assert ast.unparse(guard.test) == '_OPEN_TRANSACTIONS'
