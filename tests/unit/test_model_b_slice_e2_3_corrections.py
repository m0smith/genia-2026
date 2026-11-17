"""Python-private C2b/F3/F5 observations for the authorized corrective slice.

Faults select the real named pre-C3 staging operation, not an immutable-table
store or frozenset operator. Setup uses only approved construction primitives.
F5 runs in a child process so a cleanup defect cannot poison later tests.
Persistent-fault progress and public closed-source activation are not claimed.
"""

from contextlib import contextmanager
import subprocess
import sys
import textwrap

import pytest

import genia
from genia import closed_publication as p
from genia import environment as e
from genia.utf8 import format_debug, format_display
from genia.values import GeniaMap
from tests.unit.test_model_b_slice_e2_3_red_b import FAILED, join_observer, terminal, world


def exercise_c2b_fault(monkeypatch, error_type, after, competing):
    """Inject once before/after actual local staging and assert owner invariants."""
    original_stage = p._stage_immutable_names
    txn = world()
    scope, group = txn.declaring_scope, txn.callable
    sentinel = 'private-metadata-must-not-escape'
    metadata = GeniaMap().put('doc', sentinel)
    error = error_type('C2b allocation')
    snapshots, calls = [], []
    other = world(name='h', declaring=scope) if competing == 'live_owner' else None

    def stage(held_scope, name):
        """Delegate the real C2b operation; only this owner's attempt is faulted."""
        if held_scope is not scope or name != 'f':
            return original_stage(held_scope, name)
        assert not calls, 'more than one staging attempt after a precommit fault'
        calls.append(name)
        assert e._BINDING_LOCK.locked()
        assert group._state == 'initializing' and not txn.window_open
        assert txn in e._OPEN_TRANSACTIONS
        assert 'f' not in scope.values and 'f' not in scope.binding_metadata
        assert group.metadata is metadata  # actual C2 preceded C2b
        snapshots.append(scope._immutable)
        if after:
            staged = original_stage(held_scope, name)
            assert staged == snapshots[0] | {'f'}
            assert scope._immutable is snapshots[0]  # local allocation, no C4 store
        raise error

    monkeypatch.setattr(p, '_stage_immutable_names', stage)
    if competing == 'immutable_writer':
        original_window = p._publication_window

        @contextmanager
        def window(candidate):
            """Let a real same-scope writer commit after T5, before T6 locks."""
            with original_window(candidate):
                yield
            if candidate is txn:
                def writer():
                    """Commit g through the ordinary checked immutable writer."""
                    ticket = scope.prepare_immutable_declaration('g')
                    scope.commit_immutable_declaration(ticket, 3)
                    return True
                assert join_observer(writer)

        monkeypatch.setattr(p, '_publication_window', window)

    def annotations(frame):
        """Escape the genuine provisional identity as an allowed annotation effect."""
        scope.set('escaped', frame.get('f'))
        return metadata

    def fail_owner():
        """Require exact error and no declaring publication before testing reuse."""
        with pytest.raises(error_type) as caught:
            p._run_publication(txn, annotations)
        assert caught.value is error and calls == ['f']
        assert group._state == 'failed' and group._txn is txn
        assert scope._immutable is snapshots[0]
        assert 'f' not in scope.values and 'f' not in scope.binding_metadata
        assert txn.self_frame.get('f') is group
        assert scope.get('escaped') is group
        if competing == 'immutable_writer':
            assert scope.get('g') == 3 and 'g' in scope.immutable_names()
            with pytest.raises(e.ImmutableBindingError):
                scope.assign('g', 9)
        terminal(txn, 'failed')  # includes cleanup, failed identity and real name reuse

    if other is None:
        fail_owner()
    else:
        def other_annotations(frame):
            """Hold another live owner while f fails its allocation stage."""
            fail_owner()
            assert other in e._OPEN_TRANSACTIONS and not other.closed
            assert scope._provisional_slots['h'].transaction is other
            assert frame._provisional_slots['h'].transaction is other
            assert scope.get('h') is frame.get('h') is other.callable
            with pytest.raises(e.ImmutableBindingError):
                scope.assign('h', 9)
            return GeniaMap()

        assert p._run_publication(other, other_annotations) is other.callable
        terminal(other, 'committed', GeniaMap())
    return txn, sentinel


@pytest.mark.parametrize('error_type', [MemoryError, KeyboardInterrupt])
@pytest.mark.parametrize('after', [False, True])
@pytest.mark.parametrize('competing', ['none', 'immutable_writer', 'live_owner'])
def test_c2b_precommit_fault_and_n1_owner_isolation(monkeypatch, error_type, after, competing):
    """L2/T7 and N1: failed f never loses g immutability or another live owner."""
    exercise_c2b_fault(monkeypatch, error_type, after, competing)


def test_f3_failed_group_keeps_metadata_inaccessible(monkeypatch, capsys):
    """C2 metadata may remain private after C2b failure; all public use rejects."""
    txn, sentinel = exercise_c2b_fault(monkeypatch, MemoryError, True, 'none')
    group, scope = txn.callable, txn.declaring_scope
    assert group.metadata.get('doc') == sentinel  # observe, do not erase private data
    for expression in ('doc("escaped")', 'meta("escaped")', 'help("escaped")', 'help(escaped)'):
        with pytest.raises(RuntimeError) as caught:
            genia.run_source(expression, scope)
        assert str(caught.value) == FAILED
        assert sentinel not in str(caught.value)
    for rendered in (repr(group), format_debug([group]), format_display([group])):
        assert sentinel not in rendered
    captured = capsys.readouterr()
    assert sentinel not in captured.out + captured.err


def test_f5_interrupted_failure_lock_acquire_still_cleans_owner():
    """One T7 acquire interrupt must not strand a live owner; isolated if broken."""
    script = textwrap.dedent('''
        from genia import closed_publication as p, environment as e
        from tests.unit.test_model_b_slice_e2_3_red_b import terminal, world
        txn = world()
        original = e._BINDING_LOCK
        annotation_error = ValueError('ordinary annotation failure')
        interrupt = KeyboardInterrupt('T7 lock acquisition')
        class Lock:
            armed = False
            fired = False
            def __enter__(self):
                if self.armed and not self.fired:
                    self.fired = True
                    raise interrupt
                return original.__enter__()
            def __exit__(self, *exc):
                return original.__exit__(*exc)
            def locked(self):
                return original.locked()
        observed = Lock()
        e._BINDING_LOCK = observed
        def annotations(frame):
            observed.armed = True
            raise annotation_error
        try:
            p._run_publication(txn, annotations)
        except (ValueError, KeyboardInterrupt) as caught:
            assert caught is annotation_error or caught is interrupt
        else:
            raise AssertionError('annotation failure was suppressed')
        assert observed.fired
        terminal(txn, 'failed')
    ''')
    result = subprocess.run([sys.executable, '-c', script], capture_output=True,
                            text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
