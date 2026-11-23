"""Python-host design 10.3 evidence completing E2-L1/L2/L5/L10/L11/L12 (#1250 E2.4).

PYTHON REFERENCE HOST internals: threading, lock/lineage mechanics and fault
injection against the real private `_run_publication` driver. Portable behavior
lives in shared specs; nothing here claims a portable concurrency guarantee.

Every pause is a delegating wrapper around an operation the production driver
performs (a table store, an `Env` helper, `__setattr__` on the callable, the
staging function). A wrapper never performs, skips or reorders a lifecycle step;
it only runs a non-owner observer thread to completion while the owner is held
at the chosen point. Observers read through the real lookup/introspection entry
points. Single-fault model only: no multi-fault or persistent-OOM claim.
"""

from contextlib import contextmanager, redirect_stdout
import inspect
import io
import sys
import threading
import time

import pytest

import genia
from genia import callable as c
from genia import closed_publication as p
from genia import environment as e
from genia.values import GeniaMap
from tests.unit.test_model_b_slice_e2_3_red_b import (
    FAILED, NOT_READY, SingleFault, join_observer, patch_operation, terminal, world,
    window_transaction,
)

FINAL = GeniaMap().put('doc', 'final')


# ---------------------------------------------------------------------------
# Delegating wrappers (real operation always runs; pause only brackets it)
# ---------------------------------------------------------------------------

def wrap_operation(monkeypatch, owner, name, selected, before=None, after=None):
    """Bracket an existing operation without altering its arguments or result."""
    original = getattr(owner, name)
    signature = inspect.signature(original)

    def delegated(*args, **kwargs):
        """Run `before`, the real operation, then `after` for selected calls only."""
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        chosen = selected(bound.arguments)
        if chosen and before:
            before()
        result = original(*args, **kwargs)
        if chosen and after:
            after()
        return result

    monkeypatch.setattr(owner, name, delegated)


class Table(dict):
    """Real dict that brackets stores of one key; all other behavior is inherited."""

    def __init__(self, contents, key, before, after):
        """Copy existing contents only; hooks are zero-argument callables."""
        super().__init__(contents)
        self._key, self._before, self._after = key, before, after

    def __setitem__(self, key, value):
        """Bracket the real insertion of the selected key."""
        chosen = key == self._key
        if chosen and self._before:
            self._before()
        super().__setitem__(key, value)
        if chosen and self._after:
            self._after()


class Slots(dict):
    """Real slot table that brackets the owner thread's C1 lookup once armed."""

    def __init__(self, contents, owner, state):
        """`state` is a mutable dict: armed flag and the two hooks."""
        super().__init__(contents)
        self._owner, self._state = owner, state

    def get(self, key, default=None):
        """Bracket the first owner-thread lookup after annotations returned."""
        state = self._state
        chosen = (state['armed'] and threading.current_thread() is self._owner
                  and key == 'f')
        if chosen:
            state['armed'] = False
            if state['before']:
                state['before']()
        result = super().get(key, default)
        if chosen and state['after']:
            state['after']()
        return result


CHECKPOINTS = ['C1', 'C2', 'C2b', 'C3', 'C4-metadata', 'C4-immutable', 'C4-binding',
               'C5-metadata', 'C5-binding', 'K1', 'K2', 'K3', 'K4']
# Positions strictly before the C3 store show the unpublished function.
UNPUBLISHED = {('C1', 'before'), ('C1', 'after'), ('C2', 'before'), ('C2', 'after'),
               ('C2b', 'before'), ('C2b', 'after'), ('C3', 'before')}


def install_checkpoint(monkeypatch, txn, checkpoint, position, hit):
    """Return a `prepare(frame)` callback wiring one real step to `hit`."""
    group, scope, frame = txn.callable, txn.declaring_scope, txn.self_frame
    before = hit if position == 'before' else None
    after = hit if position == 'after' else None
    state = {'armed': False, 'before': before, 'after': after}
    owner = threading.current_thread()
    original_set = c.GeniaClosedFunction.__setattr__
    original_env_set = e.Env.__setattr__

    def arm():
        """Last step of T5: only now may the owner's lookups count as C1."""
        state['armed'] = True

    def prepare(live_frame):
        """Install table replacements that need T4 to have run (slot table)."""
        if checkpoint == 'C1':
            assert scope._provisional_slots and 'f' in scope._provisional_slots
            scope._provisional_slots = Slots(scope._provisional_slots, owner, state)
        return arm

    if checkpoint == 'C2':
        def store(candidate, name, value):
            """Bracket the real C2 metadata store."""
            chosen = candidate is group and name == 'metadata'
            if chosen and before:
                before()
            original_set(candidate, name, value)
            if chosen and after:
                after()
        monkeypatch.setattr(c.GeniaClosedFunction, '__setattr__', store)
    elif checkpoint == 'C3':
        def store(candidate, name, value):
            """Bracket the real linearization store."""
            chosen = candidate is group and name == '_state' and value == 'committed'
            if chosen and before:
                before()
            original_set(candidate, name, value)
            if chosen and after:
                after()
        monkeypatch.setattr(c.GeniaClosedFunction, '__setattr__', store)
    elif checkpoint == 'C2b':
        wrap_operation(monkeypatch, p, '_stage_immutable_names',
                       lambda bound: bound['scope'] is scope and bound['name'] == 'f',
                       before, after)
    elif checkpoint == 'C4-immutable':
        def env_store(self, name, value):
            """Bracket the real declaring-scope immutable-set store."""
            chosen = self is scope and name == '_immutable'
            if chosen and before:
                before()
            original_env_set(self, name, value)
            if chosen and after:
                after()
        monkeypatch.setattr(e.Env, '__setattr__', env_store)
    elif checkpoint in ('C4-metadata', 'C4-binding', 'C5-metadata', 'C5-binding'):
        target = scope if checkpoint.startswith('C4') else frame
        attribute = 'binding_metadata' if checkpoint.endswith('metadata') else 'values'
        monkeypatch.setattr(target, attribute,
                            Table(getattr(target, attribute), 'f', before, after))
    elif checkpoint in ('K1', 'K2'):
        target = scope if checkpoint == 'K1' else frame
        wrap_operation(monkeypatch, e.Env, '_remove_provisional_slot',
                       lambda bound: bound['self'] is target and bound['txn'] is txn,
                       before, after)
    elif checkpoint == 'K3':
        wrap_operation(monkeypatch, e, '_unregister_open_transaction',
                       lambda bound: bound['txn'] is txn, before, after)
    elif checkpoint == 'K4':
        wrap_operation(monkeypatch, p._PublicationTransaction, '__setattr__',
                       lambda bound: bound['self'] is txn and bound['name'] == 'closed'
                       and bound['value'] is True, before, after)
    elif checkpoint != 'C1':
        raise AssertionError(checkpoint)
    return prepare


# ---------------------------------------------------------------------------
# Non-owner observations (every entry the design lists for E2-L1)
# ---------------------------------------------------------------------------

def normalize(value, group):
    """Make observations comparable: identity of the group, maps as dicts."""
    if value is group:
        return '<group>'
    if isinstance(value, GeniaMap):
        return dict(value.items())
    if isinstance(value, (int, str, bool, type(None))):
        return value
    return repr(value)  # e.g. the none("missing-doc", ...) value of an alias


def capture(group, operation):
    """Outcome of one observation: ('ok', value) or ('err', exact message)."""
    try:
        return ('ok', normalize(operation(), group))
    except BaseException as exc:  # an unexpected type must show up in the compare
        return ('err', f'{type(exc).__name__}: {exc}')


def printed(source, scope):
    """Run introspection source in `scope`, returning its stdout and value."""
    sink = io.StringIO()
    with redirect_stdout(sink):
        genia.run_source(source, scope)
    return sink.getvalue()


def lookups(group, scope, frame):
    """Observation table taken on a non-owner thread, never touching the lock."""
    decl = e.Env(scope)
    selfscope = e.Env(frame)
    table = {
        'decl_get': lambda: scope.get('f'),
        'decl_metadata': lambda: scope.get_metadata('f'),
        'self_get': lambda: frame.get('f'),
        'self_metadata': lambda: frame.get_metadata('f'),
        'doc_decl': lambda: genia.run_source('doc("f")', decl),
        'meta_decl': lambda: genia.run_source('meta("f")', decl),
        'help_decl': lambda: printed('help("f")', decl),
        'doc_self': lambda: genia.run_source('doc("f")', selfscope),
        'meta_self': lambda: genia.run_source('meta("f")', selfscope),
        'help_self': lambda: printed('help("f")', selfscope),
        'doc_ref': lambda: genia.run_source('doc("esc")', decl),
        'meta_ref': lambda: genia.run_source('meta("esc")', decl),
        'help_ref': lambda: printed('help("esc")', decl),
        'help_value': lambda: printed('help(esc)', decl),
    }
    return {key: capture(group, operation) for key, operation in table.items()}


class CallObserver:
    """Start a real call on a second thread and record its guard decision.

    A call after C3 also binds parameters under the binding lock, which the
    paused owner holds, so completion is awaited only after the owner finishes.
    The deterministic event is the guard's own decision, recorded by a wrapper
    that delegates to the real `_check_invocation`.
    """

    def __init__(self, monkeypatch, group):
        """Install the delegating decision recorder once per test."""
        self.group, self.decisions, self.workers = group, {}, []
        original = c.GeniaClosedFunction._check_invocation
        observer = self

        def check(candidate):
            """Record the real guard's decision for the observer thread only."""
            name = threading.current_thread().name
            if candidate is group and name.startswith('l1-call'):
                try:
                    original(candidate)
                except BaseException as exc:
                    observer.decisions[name] = ('err', str(exc))
                    observer.events[name].set()
                    raise
                observer.decisions[name] = ('ok', None)
                observer.events[name].set()
                return
            return original(candidate)

        self.events = {}
        monkeypatch.setattr(c.GeniaClosedFunction, '_check_invocation', check)

    def start(self, label):
        """Begin the call; return its guard decision (never its final result)."""
        name = f'l1-call-{label}'
        self.events[name] = threading.Event()
        results = {}

        def run():
            """The observed call: guard first, ordinary invocation afterwards."""
            try:
                results['value'] = self.group(7)
            except BaseException as exc:
                results['error'] = exc

        worker = threading.Thread(target=run, name=name, daemon=True)
        self.workers.append((worker, results))
        worker.start()
        assert self.events[name].wait(5), 'guard decision never reached'
        return self.decisions[name]

    def finish(self):
        """After the owner released the lock, collect every call's final outcome."""
        outcomes = []
        for worker, results in self.workers:
            worker.join(5)
            assert not worker.is_alive(), 'call stayed blocked after owner exit'
            outcomes.append(('err', str(results['error'])) if 'error' in results
                            else ('ok', results['value']))
        return outcomes


def expected_unpublished(baseline):
    """Everything a non-owner may see before C3: the outer binding, or NOT_READY."""
    refused = ('err', f'RuntimeError: {NOT_READY}')
    return {
        'decl_get': ('ok', 41),
        'decl_metadata': ('ok', {'doc': 'outer'}),
        'self_get': refused, 'self_metadata': refused,
        'doc_decl': baseline['doc_decl'], 'meta_decl': baseline['meta_decl'],
        'help_decl': baseline['help_decl'],
        'doc_self': refused, 'meta_self': refused, 'help_self': refused,
        'doc_ref': refused, 'meta_ref': refused, 'help_ref': refused,
        'help_value': refused,
    }


def expected_published(reference):
    """From C3 on: the committed callable with its final metadata, everywhere."""
    final = ('ok', {'doc': 'final'})
    return {
        'decl_get': ('ok', '<group>'), 'decl_metadata': final,
        'self_get': ('ok', '<group>'), 'self_metadata': final,
        'doc_decl': ('ok', 'final'), 'meta_decl': final,
        'help_decl': reference['help_decl'],
        'doc_self': ('ok', 'final'), 'meta_self': final,
        'help_self': reference['help_self'],
        # An alias name answers from its own binding-owned metadata (design 4.5/7.3),
        # not the callable's; it is unchanged by publication. Pinned in the caller.
        'doc_ref': reference['doc_ref'], 'meta_ref': reference['meta_ref'],
        'help_ref': reference['help_ref'], 'help_value': reference['help_value'],
    }


@pytest.mark.parametrize('position', ['before', 'after'])
@pytest.mark.parametrize('checkpoint', CHECKPOINTS)
def test_l1_second_thread_sees_one_state_at_every_checkpoint(monkeypatch, checkpoint, position):
    """Design 10.3 E2-L1: paused at each real step, never a mixture.

    A non-owner thread (no admission, no lock) calls through an escaped reference,
    reads doc/meta/help (by name in the declaring scope and through the self
    frame, and through the reference), and looks up the name and its metadata in
    both scopes. Each pause must be wholly unpublished (before the real C3 store)
    or wholly published (from it on).
    """
    txn = world()
    group, scope, frame = txn.callable, txn.declaring_scope, txn.self_frame
    baseline = lookups(group, scope, frame)  # the world before any declaration
    observed = []
    calls = CallObserver(monkeypatch, group)

    def hit():
        """Owner paused at the selected step: observe from other threads."""
        expectation = ('unpublished' if (checkpoint, position) in UNPUBLISHED
                       else 'published')
        assert group._state == ('initializing' if expectation == 'unpublished'
                                else 'committed')
        decision = calls.start(f'{checkpoint}-{position}')
        assert decision == (('err', NOT_READY) if expectation == 'unpublished'
                            else ('ok', None))
        observed.append((expectation, join_observer(lambda: lookups(group, scope, frame))))

    prepare = install_checkpoint(monkeypatch, txn, checkpoint, position, hit)

    def annotations(live_frame):
        """Escape the real admitted reference as an ordinary annotation effect."""
        scope.set('esc', live_frame.get('f'))
        arm = prepare(live_frame)
        arm()
        return FINAL

    assert p._run_publication(txn, annotations) is group
    assert len(observed) == 1, 'the selected real step was never reached exactly once'
    terminal(txn, 'committed', FINAL)
    expectation, actual = observed[0]
    reference = lookups(group, scope, frame)
    assert reference['meta_ref'] == ('ok', {})  # alias metadata stays binding-owned
    assert reference['help_ref'] == reference['help_value']
    wanted = (expected_unpublished(baseline) if expectation == 'unpublished'
              else expected_published(reference))
    assert actual == wanted
    assert calls.finish() == [
        ('err', NOT_READY) if expectation == 'unpublished' else ('ok', 7)]


# ---------------------------------------------------------------------------
# E2-L2 gaps: a fault at P1 (state still `building`) and at C1
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('error_type', [MemoryError, KeyboardInterrupt])
@pytest.mark.parametrize('after', [False, True])
def test_l2_p1_fault_discards_never_reachable_callable(monkeypatch, error_type, after):
    """P1 (design 4.4): the callable was never reachable; close routine only."""
    txn = world()
    scope, group = txn.declaring_scope, txn.callable
    fault = SingleFault(after, error_type('P1 name recheck'))
    patch_operation(monkeypatch, e.Env, '_check_declaration',
                    lambda bound: bound['self'] is scope and bound['name'] == 'f', fault)
    with pytest.raises(error_type) as caught:
        p._run_publication(txn, lambda frame: pytest.fail('annotation ran after a P1 fault'))
    assert caught.value is fault.error and fault.hits == 1
    assert group._state == 'building' and txn.closed and not txn.window_open
    assert txn not in e._OPEN_TRANSACTIONS
    for owner_scope in (scope, txn.self_frame):
        assert 'f' not in (owner_scope._provisional_slots or {})
    assert 'f' not in scope.values and 'f' not in scope.binding_metadata
    assert 'f' not in scope.immutable_names()
    assert scope.get('f') == 41  # outer binding untouched; the name is reusable
    ticket = scope.prepare_immutable_declaration('f')
    scope.commit_immutable_declaration(ticket, 5)
    assert scope.get('f') == 5


@pytest.mark.parametrize('error_type', [MemoryError, KeyboardInterrupt])
@pytest.mark.parametrize('after', [False, True])
def test_l2_c1_fault_enters_failure_protocol(monkeypatch, error_type, after):
    """C1 (design 4.4): state is `initializing`, nothing visible was written: T7."""
    txn = world()
    group, scope = txn.callable, txn.declaring_scope
    fault = SingleFault(after, error_type('C1 revalidation'))
    state = {'armed': False, 'before': None, 'after': None}

    def inject():
        """Raise the single fault around the real C1 slot lookup."""
        fault.run(lambda: None)

    state['after' if after else 'before'] = inject
    # SingleFault.run(after=True) performs `operation()` then raises, so the
    # hook alone is the injection point whichever side it brackets.
    fault_after = SingleFault(False, fault.error)
    state['before'] = state['after'] = None
    state['after' if after else 'before'] = lambda: fault_after.run(lambda: None)

    def annotations(frame):
        """Install the bracket on the real slot table, armed at the end of T5."""
        scope._provisional_slots = Slots(scope._provisional_slots,
                                         threading.current_thread(), state)
        state['armed'] = True
        return FINAL

    with pytest.raises(error_type) as caught:
        p._run_publication(txn, annotations)
    assert caught.value is fault.error and fault_after.hits == 1
    assert group.metadata != FINAL or group._state == 'failed'
    terminal(txn, 'failed')


# ---------------------------------------------------------------------------
# E2-L10 (N1): interleaved publications and a writer holding the lock
# ---------------------------------------------------------------------------

def wait_until_blocked_on_binding_lock(thread, timeout=5):
    """Poll the other thread's innermost line until it waits for the binding lock."""
    import linecache
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        frame = sys._current_frames().get(thread.ident)
        if frame is not None:
            text = linecache.getline(frame.f_code.co_filename, frame.f_lineno)
            if '_BINDING_LOCK' in text:
                return
        time.sleep(0.001)
    raise AssertionError('thread never reached its binding-lock acquisition')


@pytest.mark.parametrize('first', ['f', 'h'])
def test_l10_n1_two_publications_interleave_in_both_orders(monkeypatch, first):
    """Two owners meet after T5; the second computes C2b from the first's result.

    The first owner is held after its own real C2b (lock held) until the second
    owner is observed blocked on that lock. If C2b were staged outside the lock
    or from a stale set, one name would be lost from the immutable set.
    """
    owners = {'f': world(), }
    owners['h'] = world(name='h', declaring=owners['f'].declaring_scope)
    scope = owners['f'].declaring_scope
    second = 'h' if first == 'f' else 'f'
    rendezvous = threading.Barrier(2)
    first_holds_lock = threading.Event()
    results, errors, threads = {}, [], {}
    original_stage = p._stage_immutable_names
    staged = {}

    def stage(held_scope, name):
        """Delegate the real C2b; hold the first owner here, lock still held."""
        before = held_scope._immutable
        result = original_stage(held_scope, name)
        staged[name] = (before, result)
        if name == first:
            first_holds_lock.set()
            wait_until_blocked_on_binding_lock(threads[second])
        return result

    monkeypatch.setattr(p, '_stage_immutable_names', stage)

    def run(name):
        """One owner's declaration, on its own thread."""
        def annotations(frame):
            """Both reservations coexist; the second waits for the first's lock."""
            rendezvous.wait(5)
            if name == second:
                assert first_holds_lock.wait(5)
            return GeniaMap().put('doc', name)
        try:
            results[name] = p._run_publication(owners[name], annotations)
        except BaseException as exc:
            errors.append(exc)

    for name in (first, second):
        threads[name] = threading.Thread(target=run, args=(name,), daemon=True)
    for thread in threads.values():
        thread.start()
    for thread in threads.values():
        thread.join(10)
        assert not thread.is_alive()
    assert not errors, errors
    assert staged[first][0] == frozenset()
    assert staged[second][0] == frozenset({first}), 'second C2b must read the current set'
    assert staged[second][1] == frozenset({'f', 'h'})
    assert scope.immutable_names() == frozenset({'f', 'h'})
    for name in ('f', 'h'):
        assert results[name] is owners[name].callable
        terminal(owners[name], 'committed', GeniaMap().put('doc', name))
        with pytest.raises(e.ImmutableBindingError):
            scope.assign(name, 9)
    assert not e._OPEN_TRANSACTIONS


def test_l10_n1_immutable_commit_while_owner_waits_for_lock(monkeypatch):
    """Writer g holds the lock when f arrives at T6; f waits, then commits correctly."""
    txn = world()
    scope, group = txn.declaring_scope, txn.callable
    owner = threading.current_thread()
    writer_in_lock = threading.Event()
    original_window = p._publication_window
    original_set = e.Env.__setattr__
    writer_state = {}

    def env_store(self, name, value):
        """Hold the writer inside its critical section until f is observed waiting."""
        if (self is scope and name == '_immutable'
                and threading.current_thread() is writer_state.get('thread')):
            writer_in_lock.set()
            wait_until_blocked_on_binding_lock(owner)
            writer_state['owner_waited'] = True
        original_set(self, name, value)

    monkeypatch.setattr(e.Env, '__setattr__', env_store)

    @contextmanager
    def window(*args, **kwargs):
        """After real window exit, let a writer take the lock before T6 does."""
        candidate = window_transaction(original_window, args, kwargs)
        with original_window(*args, **kwargs):
            yield
        if candidate is txn:
            def writer():
                """Ordinary checked immutable declaration of g."""
                ticket = scope.prepare_immutable_declaration('g')
                scope.commit_immutable_declaration(ticket, 3)

            thread = threading.Thread(target=writer, daemon=True)
            writer_state['thread'] = thread
            thread.start()
            assert writer_in_lock.wait(5)

    monkeypatch.setattr(p, '_publication_window', window)
    assert p._run_publication(txn, lambda frame: FINAL) is group
    writer_state['thread'].join(5)
    assert writer_state.get('owner_waited'), 'f never waited behind the writer'
    terminal(txn, 'committed', FINAL)
    assert scope.immutable_names() == frozenset({'f', 'g'})
    for name in ('f', 'g'):
        with pytest.raises(e.ImmutableBindingError):
            scope.assign(name, 9)
    assert scope.get('g') == 3


# ---------------------------------------------------------------------------
# E2-L11 (N2): an aborted T4, caused by an ordinary error, plus one close fault
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('step', ['K1', 'K2', 'K3'])
def test_l11_n2_aborted_t4_close_fault_keeps_live_owner(monkeypatch, step):
    """A loses the name to live B (ordinary error at P1); one fault hits A's close.

    The abort is not a protocol fault: the single injected fault is the only one.
    A never owned a slot or a set entry, so B's reservations must survive every
    repeated K step, and B must still publish.
    """
    live = world()
    scope = live.declaring_scope
    aborted = world(declaring=scope)  # same scope, same name f
    fault = SingleFault(True, KeyboardInterrupt('A close'))
    if step == 'K3':
        patch_operation(monkeypatch, e, '_unregister_open_transaction',
                        lambda bound: bound['txn'] is aborted, fault)
    else:
        target = scope if step == 'K1' else aborted.self_frame
        patch_operation(monkeypatch, e.Env, '_remove_provisional_slot',
                        lambda bound: bound['self'] is target and bound['txn'] is aborted,
                        fault)

    def live_annotations(frame):
        """While B is live, A's declaration is rejected and A's cleanup is faulted."""
        assert live in e._OPEN_TRANSACTIONS
        with pytest.raises(e.ImmutableBindingError):
            p._run_publication(aborted, lambda inner: pytest.fail('A annotation ran'))
        assert fault.hits == 1
        assert aborted.closed and aborted not in e._OPEN_TRANSACTIONS
        assert aborted.callable._state == 'building'
        assert 'f' not in (aborted.self_frame._provisional_slots or {})
        assert scope._provisional_slots['f'].transaction is live
        assert frame._provisional_slots['f'].transaction is live
        assert live in e._OPEN_TRANSACTIONS and not live.closed
        assert frame.get('f') is scope.get('f') is live.callable  # guarded, not fast path
        assert scope.root().get('f') == 41
        with pytest.raises(e.ImmutableBindingError):
            scope.assign('f', 9)
        return FINAL

    assert p._run_publication(live, live_annotations) is live.callable
    terminal(live, 'committed', FINAL)
    assert not e._OPEN_TRANSACTIONS


# ---------------------------------------------------------------------------
# E2-L12 (N3): paused use/metadata/introspection reads keep their snapshot
# ---------------------------------------------------------------------------

READ_ENTRIES = {
    'declaring_metadata': (lambda t, d, f: lambda: t.declaring_scope.get_metadata('f'),
                           ('ok', {'doc': 'outer'})),
    'self_metadata': (lambda t, d, f: lambda: t.self_frame.get_metadata('f'),
                      ('err', f'RuntimeError: {NOT_READY}')),
    'doc_ref': (lambda t, d, f: lambda: genia.run_source('doc("esc")', d),
                ('err', f'RuntimeError: {NOT_READY}')),
    'meta_ref': (lambda t, d, f: lambda: genia.run_source('meta("esc")', d),
                 ('err', f'RuntimeError: {NOT_READY}')),
    'help_ref': (lambda t, d, f: lambda: printed('help("esc")', d),
                 ('err', f'RuntimeError: {NOT_READY}')),
    'help_value': (lambda t, d, f: lambda: printed('help(esc)', d),
                   ('err', f'RuntimeError: {NOT_READY}')),
}


@pytest.mark.parametrize('outcome', ['committed', 'failed'])
@pytest.mark.parametrize('entry', sorted(READ_ENTRIES))
def test_l12_n3_paused_reads_of_metadata_and_introspection(monkeypatch, outcome, entry):
    """Pause after the decision state read (`initializing`); the owner then ends.

    The paused reader's answer is decided by the snapshot, with no other exception,
    `_txn` is the same object, and a following access gives the terminal result.
    """
    txn = world()
    group, scope = txn.callable, txn.declaring_scope
    make, wanted = READ_ENTRIES[entry]
    decl = e.Env(scope)
    original = c.GeniaClosedFunction.__getattribute__
    paused, resume = threading.Event(), threading.Event()
    workers, snapshots, observations = [], [], []
    annotation_error = ValueError('annotation')

    def getattribute(candidate, name):
        """Pause the reader thread right after it read `initializing`."""
        value = original(candidate, name)
        if (candidate is group and name == '_state' and workers
                and threading.current_thread() is workers[0] and value == 'initializing'
                and not paused.is_set()):
            snapshots.append(value)
            paused.set()
            assert resume.wait(5), 'owner did not reach a terminal state'
        return value

    monkeypatch.setattr(c.GeniaClosedFunction, '__getattribute__', getattribute)
    descriptor = {}

    def reader():
        """Run the selected read once; keep its exact outcome."""
        observations.append(capture(group, make(txn, decl, None)))

    def annotations(frame):
        """Start the reader inside a real window; let the owner finish afterwards."""
        scope.set('esc', frame.get('f'))
        descriptor['txn'] = group._txn
        worker = threading.Thread(target=reader, daemon=True)
        workers.append(worker)
        worker.start()
        assert paused.wait(5), 'reader never read the initializing state'
        if outcome == 'failed':
            raise annotation_error
        return FINAL

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
    assert snapshots == ['initializing']
    assert observations == [wanted], 'the paused read must keep its snapshot answer'
    assert group._txn is txn is descriptor['txn']
    again = capture(group, make(txn, decl, None))  # before `terminal` reuses the name
    # A following access gives the terminal behavior, not the snapshot answer.
    if entry in ('declaring_metadata', 'self_metadata'):
        if outcome == 'committed':
            assert again == ('ok', {'doc': 'final'})
        elif entry == 'declaring_metadata':
            assert again == ('ok', {'doc': 'outer'})  # as if never declared
        else:
            # Raw self-frame metadata after failure is not specified beyond the
            # callable's own guards (see `terminal`); only the stale answer is wrong.
            assert again != wanted
    elif outcome == 'failed':
        assert again == ('err', f'RuntimeError: {FAILED}')
    else:
        assert again != wanted and again[0] == 'ok'  # alias-owned metadata/help text
    terminal(txn, outcome, FINAL)


# ---------------------------------------------------------------------------
# E2-L5: real serve_http dispatch on the declaring thread (design 6.4)
# ---------------------------------------------------------------------------

@pytest.mark.loopback
def test_l5_real_serve_http_request_cannot_use_provisional_callable():
    """A handler reached through a real socket request is refused at its dispatch.

    The annotation stores the admitted callable and runs the real `serve_http` on
    the declaring thread; the request handler runs on that same thread inside the
    still-open window, yet the host's dispatch barrier hides the transaction.
    """
    from urllib.request import urlopen
    from tests.fixtures.loopback import free_port

    txn = world()
    group, scope = txn.callable, txn.declaring_scope
    port, owner = free_port(), threading.current_thread()
    stash, seen, response = [], {}, {}

    def handler(request):
        """Reads the stash like the design's Ref example and tries to call it."""
        seen['thread'] = threading.current_thread()
        seen['refused'] = capture(group, lambda: stash[0](1))
        return GeniaMap().put('status', 200).put('body', 'ok')

    def client():
        """One real request, retried until the listener exists."""
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                with urlopen(f'http://127.0.0.1:{port}/', timeout=5) as reply:
                    response['status'], response['body'] = reply.status, reply.read()
                return
            except OSError:
                time.sleep(0.01)

    def annotations(frame):
        """Window open: serve exactly one real request, then still be admitted."""
        stash.append(frame.get('f'))
        assert group(1) == 1
        thread = threading.Thread(target=client, daemon=True)
        thread.start()
        result = scope.get('_serve_http')(
            GeniaMap().put('port', port).put('max_requests', 1), handler)
        thread.join(5)
        seen['served'] = result
        assert group(2) == 2  # barrier unwound: authority is back
        return FINAL

    assert p._run_publication(txn, annotations) is group
    assert seen['thread'] is owner, 'serve_http dispatches on the declaring thread'
    assert seen['refused'] == ('err', f'RuntimeError: {NOT_READY}')
    assert response == {'status': 200, 'body': b'ok'}
    terminal(txn, 'committed', FINAL)
