"""RED-A seam proposal only; Python-private lifecycle, not portability evidence.

Proposed production seam (NOT implemented by this test):
    genia.closed_publication._run_publication(txn, evaluate_annotations)
        -> txn.callable
The fresh building descriptor already owns a validated whole group and its
reserved self frame. T0/T1/T2/T3 preparation belongs to the caller. The driver
owns T4-T7 and invokes evaluate_annotations(self_frame) once inside its T5
window, outside the binding lock. The callback owns ordered annotation
evaluation/folding and returns the final private GeniaMap. Scope/name/group
are derived from the stable descriptor, never supplied twice.

Contract section 4 and Slice E design sections 3-4/6/10 govern the oracles.
AttributeError at the proposed entry is the authorized RED-A seam-absence
gate ONLY. Callback/terminal assertions below are intended behavioral oracles,
not observed RED-B failures. No C/F/K sequence, fake driver, state stores or
slot manipulation is supplied by fixtures. Fault/race coverage awaits RED-B.
Public source/direct-IR activation remains E2.4.
"""

import pytest

import genia
from genia import callable as c
from genia import closed_publication as publication
from genia import environment as e
from genia import ir
from genia.evaluator import Evaluator
from genia.values import GeniaMap
from tests.unit.model_b_slice_e1_support import record


def fresh_transaction():
    """Use actual E1/E2 constructors without publishing or setting any state."""
    outer = e.Env()
    outer.set_host('f', 41, visibility='runtime-public',
                   metadata=GeniaMap().put('doc', 'outer'))
    declaring = e.Env(outer, rebind_parent=False)
    group = c.GeniaClosedFunction._with_self_frame('f', [record(declaring)], declaring)
    txn = publication._PublicationTransaction(group)
    assert txn.declaring_scope is declaring
    assert txn.self_frame.parent is declaring
    assert group._state == 'building'
    assert not txn.closed and not txn.window_open
    return outer, declaring, group, txn


def assert_closed_transaction(txn):
    """Require real terminal cleanup even when neither scope has a slot left."""
    assert txn.callable._txn is txn
    assert txn.closed and not txn.window_open
    assert txn not in e._OPEN_TRANSACTIONS
    assert not publication._publication_admitted(txn)
    for scope in (txn.declaring_scope, txn.self_frame):
        assert not (scope._provisional_slots or {})


def test_red_a_success_installs_both_terminal_bindings_and_metadata():
    """Design T5/C1-C6: return callable and keep tables valid after K1/K2."""
    outer, declaring, group, txn = fresh_transaction()
    metadata = GeniaMap().put('doc', 'published').put('category', 'test')
    calls = []
    immutable_self_names = txn.self_frame._immutable

    def annotations(frame):
        """Observe real admission; return metadata without implementing publication."""
        calls.append(frame)
        assert frame is txn.self_frame
        assert group._state == 'initializing'
        assert txn.window_open and publication._publication_admitted(txn)
        assert txn in e._OPEN_TRANSACTIONS
        assert declaring.get('f') is frame.get('f') is group
        assert group(7) == 7
        assert 'f' not in declaring.values and 'f' not in frame.values
        assert 'f' not in declaring.binding_metadata and 'f' not in frame.binding_metadata
        with pytest.raises(RuntimeError, match='^closed-function-not-yet-published: f is not yet published$'):
            frame.get_metadata('f')
        return metadata

    result = publication._run_publication(txn, annotations)

    assert result is group and calls == [txn.self_frame]
    assert group._state == 'committed'
    assert dict(group.metadata.items()) == dict(metadata.items())
    assert_closed_transaction(txn)
    assert txn.self_frame._immutable is immutable_self_names
    for scope in (declaring, txn.self_frame):
        assert scope.values['f'] is scope.get('f') is group
        assert dict(scope.binding_metadata['f'].items()) == dict(metadata.items())
        assert dict(scope.get_metadata('f').items()) == dict(metadata.items())
        assert 'f' in scope.immutable_names()
        with pytest.raises(e.ImmutableBindingError):
            scope.assign('f', 99)
        with pytest.raises(e.ImmutableBindingError):
            scope.merge_binding_metadata('f', GeniaMap().put('doc', 'bad'))
    assert outer.get('f') == 41
    assert outer.get_metadata('f').get('doc') == 'outer'
    assert group(8) == 8


@pytest.mark.parametrize('error_type', [ValueError, KeyboardInterrupt])
def test_red_a_annotation_failure_preserves_exception_and_allows_name_reuse(error_type):
    """Design T7/F1-F3: effects persist, self stays failed, declaring name is free."""
    outer, declaring, group, txn = fresh_transaction()
    fault = error_type('annotation stopped')
    escaped = []
    prior_names = declaring.immutable_names()
    immutable_self_names = txn.self_frame._immutable

    def annotations(frame):
        """Escape the admitted value then raise the exact annotation exception."""
        assert frame is txn.self_frame
        assert txn.window_open and group._state == 'initializing'
        escaped.append(frame.get('f'))
        raise fault

    # Resolve outside pytest.raises: AttributeError must remain seam-absence,
    # never accidentally satisfy the intended annotation-failure oracle.
    driver = publication._run_publication
    with pytest.raises(error_type) as caught:
        driver(txn, annotations)

    assert caught.value is fault
    assert escaped == [group]
    assert group._state == 'failed'
    assert dict(group.metadata.items()) == {}
    assert_closed_transaction(txn)
    assert 'f' not in declaring.values and 'f' not in declaring.binding_metadata
    assert declaring.immutable_names() == prior_names
    assert declaring.get('f') == 41
    assert txn.self_frame.values['f'] is txn.self_frame.get('f') is group
    assert txn.self_frame._immutable is immutable_self_names
    with pytest.raises(RuntimeError, match='^closed-function-failed-publication: closed function failed publication$'):
        group(7)
    with pytest.raises(e.ImmutableBindingError):
        txn.self_frame.merge_binding_metadata('f', GeniaMap().put('doc', 'bad'))
    assert outer.get_metadata('f').get('doc') == 'outer'
    replacement = object()
    declaring.commit_immutable_declaration(declaring.prepare_immutable_declaration('f'), replacement)
    assert declaring.get('f') is replacement
    assert txn.self_frame.get('f') is group and group._state == 'failed'


@pytest.mark.parametrize('entry', ['source', 'direct_ir'])
def test_public_closed_execution_remains_rejected(entry):
    """Preserve the E2.4 gate, independently of the proposed private seam."""
    scope = genia.make_global_env([])
    effects = []
    scope.set_host('effect', lambda: effects.append('ran'), visibility='entry-only')
    with pytest.raises(RuntimeError, match='^model-b-not-implemented: declaration evaluation is not available$'):
        if entry == 'source':
            genia.run_source('f(x) =: effect()', scope)
        else:
            Evaluator(scope).eval(ir.IrClosedFuncDef('f', [
                ir.IrFuncDef('f', ['x'], None, None, ir.IrCall(ir.IrVar('effect'), [])),
            ]))
    assert effects == []
    assert 'f' not in scope.values
