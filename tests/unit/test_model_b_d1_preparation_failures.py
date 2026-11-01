"""Python-internal D1 faults at actual preparation boundaries, not portable linking.

Each injected exception must occur before publication, preserve old effects and
dependencies, release the writer lock and loading sentinel, and allow fresh retry.
These supplement the accepted RED oracles without changing them.
"""

import pytest

from genia import make_global_env
from genia import environment, ir, ordinary_completion
from genia.values import GeniaMap
from tests.unit.test_model_b_d1_completion import modules, projection


@pytest.mark.parametrize('stage', ['binding-map', 'help-map', 'clause-copy', 'projection'])
def test_real_preparation_fault_discards_private_state_and_keeps_old_values(tmp_path, monkeypatch, stage):
    """Fail once at real construction, then remove the fault and explicitly retry."""
    escaped = []
    root = make_global_env([])
    root.set_host('keep', escaped.append, visibility='runtime-public')
    root, entry = modules(tmp_path, {
        'dep': 'v=1', 'base': 'import dep\nf(x)=x\nkeep(f)',
    }, root)
    calls = []
    target = {'binding-map': '_Metadata', 'help-map': '_Metadata',
              'clause-copy': '_copy_record', 'projection': '_Projection'}[stage]
    original = getattr(ordinary_completion, target)

    def injected(*args, **kwargs):
        """Raise at the selected real construction call, with no alternate implementation."""
        calls.append(stage)
        if len(calls) == (2 if stage == 'help-map' else 1):
            raise MemoryError(stage)
        return original(*args, **kwargs)

    monkeypatch.setattr(ordinary_completion, target, injected)
    with pytest.raises(MemoryError, match=stage):
        root.load_module('base', entry)
    assert calls and len(escaped) == 1 and escaped[0](7) == 7
    assert 'base' not in root.loaded_modules and not root.loading_modules
    assert not environment._BINDING_LOCK.locked()
    assert root.loaded_modules['dep'].get_export('v') == 1
    assert not hasattr(escaped[0], '_ordinary_completions')
    dependency = root.loaded_modules['dep']
    monkeypatch.setattr(ordinary_completion, target, original)
    retry = root.load_module('base', entry)
    assert root.loaded_modules['dep'] is dependency
    assert retry.get_export('f') is not escaped[0]
    assert projection(retry, retry.get_export('f')).original is retry.get_export('f')


def test_completed_metadata_is_read_only_and_runtime_payload_remains_shared(tmp_path):
    """Neither metadata table mutation nor rebinding can corrupt the owned projection."""
    root, entry = modules(tmp_path, {'base': '@doc "canonical"\nf(x)=x'})
    mod = root.load_module('base', entry)
    snap = projection(mod, mod.get_export('f'))
    with pytest.raises(TypeError):
        snap.binding_metadata._entries['bad'] = ('bad', 1)
    with pytest.raises(AttributeError):
        snap.binding_metadata._entries = {}
    assert snap.binding_metadata.put('doc', 'new').get('doc') == 'new'
    assert snap.binding_metadata.get('doc') == 'canonical'
    assert isinstance(snap.binding_metadata, GeniaMap)


def test_literal_runtime_value_is_not_confused_with_numeric_syntax_payload():
    """Detach tagged numeric syntax, but preserve a runtime literal's list identity."""
    payload = [GeniaMap().put('value', 1)]
    literal = ir.IrLiteral(payload)
    detached = ordinary_completion._copy_syntax(literal)
    assert detached is not literal and detached.value is payload
    numeric = ir.IrLiteral({'kind': 'integer', 'digits': '17'})
    copied_numeric = ordinary_completion._copy_syntax(numeric)
    numeric.value['digits'] = '99'
    assert copied_numeric.value == {'kind': 'integer', 'digits': '17'}


@pytest.mark.parametrize('kind', [[], {}], ids=['list-kind', 'map-kind'])
def test_opaque_literal_kind_is_not_hashed(kind):
    """Unhashable runtime payloads are not misclassified as numeric source syntax."""
    payload = {'kind': kind}
    assert ordinary_completion._copy_syntax(ir.IrLiteral(payload)).value is payload


def test_literal_kind_never_invokes_user_hash_or_equality():
    """A string subclass tag cannot execute host hooks during capture under the lock."""
    class HostileKind(str):
        """A runtime value masquerading as a numeric tag, with forbidden conversions."""

        def __hash__(self):
            """Signal an incorrect classification before any callback can re-enter the loader."""
            raise AssertionError('kind hash hook executed')

        def __eq__(self, other):
            """Signal an incorrect user-value comparison during syntax classification."""
            raise AssertionError('kind equality hook executed')

    payload = {'kind': HostileKind('integer')}
    assert ordinary_completion._copy_syntax(ir.IrLiteral(payload)).value is payload
