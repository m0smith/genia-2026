"""D1 RED: Python-private completion ownership and loader synchronization (#1250).

No portable linking claim. Real source modules are loaded before snapshot assertions.
The small accessor below binds a TEST-ONLY private inspection protocol: immutable
ModuleValue._ordinary_completions pairs; projection clauses/binding_metadata/
projected_doc/help_doc/help_metadata; clause.materialize() returns a fresh existing
GeniaFunction record. It is not a new language API or implementation. Equivalent
private layouts may adapt this accessor with independent review, not weaken oracles.
Missing projections intentionally fail; downstream mutation oracles are not claimed
executed until the implementation supplies that boundary. No skip/xfail/stub model.
"""

import pytest

from genia import make_global_env
from genia import environment as environments
from genia import ir
from genia.values import GeniaCell, GeniaMap, GeniaRef


def modules(tmp_path, files, root=None):
    """Write source fixtures and return the existing real loader and entry label."""
    for name, source in files.items():
        (tmp_path / (name + '.genia')).write_text(source, encoding='utf-8')
    return root or make_global_env([]), str(tmp_path / 'entry.genia')


def pairs(module):
    """Require the design's immutable private association boundary after real loading."""
    result = getattr(module, '_ordinary_completions', None)
    assert isinstance(result, tuple), 'D1: completed ModuleValue lacks immutable completion associations'
    assert all(isinstance(pair, tuple) and len(pair) == 2 for pair in result)
    return result


def projection(module, group):
    """Select by exact identity, never by equality, hash, name, or owner provenance."""
    selected = [value for original, value in pairs(module) if original is group]
    assert len(selected) == 1, 'D1: original exported callable must have exactly one projection'
    return selected[0]


def test_d1_01_cache_hit_reuses_one_original_projection(tmp_path):
    root, entry = modules(tmp_path, {'base': 'f(x) = 17\na = f'})
    first = root.load_module('base', entry)
    assert first is root.load_module('base', entry)
    group = first.get_export('f')
    assert first.get_export('a') is group and group(2) == 17
    snap = projection(first, group)
    assert len(pairs(first)) == 1
    assert projection(root.load_module('base', entry), group) is snap


def test_d1_02_detaches_record_body_parameters_and_execution_copies(tmp_path):
    root, entry = modules(tmp_path, {'base': 'f(x) = 17'})
    mod = root.load_module('base', entry)
    group = mod.get_export('f')
    assert group.records[0].params == ['x']
    assert group.records[0].body.value == {'kind': 'integer', 'digits': '17'}
    snap = projection(mod, group)
    assert isinstance(snap.clauses, tuple) and len(snap.clauses) == 1
    copied = snap.clauses[0].materialize()
    assert copied is not group.records[0] and copied.closure is group.records[0].closure
    assert copied.params == ['x'] and copied.body.value == {'kind': 'integer', 'digits': '17'}
    group.records[0].params[0] = 'changed'
    group.records[0].body.value['digits'] = '99'
    copied.params.append('leak')
    copied.body.value['digits'] = '1'
    fresh = snap.clauses[0].materialize()
    assert fresh.params == ['x'] and fresh.body.value == {'kind': 'integer', 'digits': '17'}
    assert fresh is not copied and fresh.body is not copied.body
    with pytest.raises((AttributeError, TypeError)):
        snap.clauses += (snap.clauses[0],)


def test_d1_02_grouped_header_arm_order_guard_and_provenance(tmp_path):
    root, entry = modules(tmp_path, {'base': 'f(x) = (0) -> x | (n) ? n > 0 -> n + x\nf(x,y) = x+y'})
    mod = root.load_module('base', entry)
    group = mod.get_export('f')
    assert group(3) == 6 and group(2, 3) == 5
    assert len(group.records[0].body.clauses) == 2
    assert group.records[0].body.clauses[1].guard is not None
    snap = projection(mod, group)
    assert len(snap.clauses) == 2
    assert [clause.shape for clause in snap.clauses] == [('fixed', 1), ('fixed', 2)]
    assert [clause.dispatch_key for clause in snap.clauses] == [record.dispatch_key for record in group.records]
    assert snap.clauses[0].declaration_ordinal < snap.clauses[1].declaration_ordinal
    assert len(snap.clauses[0].arm_ordinals) == 2
    assert snap.clauses[0].arm_ordinals[0] < snap.clauses[0].arm_ordinals[1]
    first = snap.clauses[0].materialize()
    second = snap.clauses[1].materialize()
    assert first.params == ['x'] and second.params == ['x', 'y']
    assert len(first.body.clauses) == 2
    assert first.body.clauses[1].guard is not None
    assert first.span == group.records[0].span and first.closure is group.records[0].closure
    first.body.clauses.reverse()
    group.records[0].body.clauses[1].guard = None
    group.records.reverse()
    assert snap.clauses[0].materialize().body.clauses[0].guard is None
    assert snap.clauses[0].materialize().body.clauses[1].guard is not None
    assert snap.clauses[0].materialize().params == ['x']


def test_d1_02_optimized_retained_case_is_detached_without_losing_arm_provenance(tmp_path):
    source = 'pick(n, xs) = (_, []) -> nil | (0, [x, .._]) -> x | (n, [_, ..rest]) -> pick(n - 1, rest)'
    root, entry = modules(tmp_path, {'base': source})
    mod = root.load_module('base', entry)
    group = mod.get_export('pick')
    assert isinstance(group.records[0].body, ir.IrListTraversalLoop)
    assert group(1, [7, 8]) == 8
    snap = projection(mod, group)
    copied = snap.clauses[0].materialize()
    assert isinstance(copied.body, ir.IrListTraversalLoop)
    assert len(copied.body.case.clauses) == 3
    assert copied.body.case is not group.records[0].body.case
    group.records[0].body.case.clauses.clear()
    copied.body.case.clauses.clear()
    assert len(snap.clauses[0].materialize().body.case.clauses) == 3


def test_d1_03_canonical_binding_doc_and_independent_inline_help_summary(tmp_path):
    source = '@doc "canonical"\nf(x)="inline" x\n@category "alias-category"\na=f'
    root, entry = modules(tmp_path, {'base': source})
    mod = root.load_module('base', entry)
    group = mod.get_export('f')
    assert group.records[0].closure.get_metadata('f').get('doc') == 'canonical'
    assert group.metadata.get('category') == 'alias-category'
    assert group.metadata.get('doc', None) is None and group.docstring == 'inline'
    snap = projection(mod, group)
    assert snap.binding_metadata.get('doc') == 'canonical'
    assert snap.binding_metadata.get('category', None) is None
    assert snap.projected_doc == 'canonical' and snap.help_doc == 'inline'
    assert snap.help_metadata.get('category') == 'alias-category'
    group.metadata._entries.clear()
    assert snap.help_metadata.get('category') == 'alias-category'


@pytest.mark.parametrize(('tail', 'doc', 'help_doc'), [
    ('g(x) = "H-inline" x\nf = g', 'original', 'original'),
    ('g(x) = "H-inline" x\n@doc "replacement"\nf = g', 'replacement', 'original'),
    ('import other as f', 'G-inline', 'original'),
    ('import other as f\nf = a', 'G-inline', 'original'),
    ('@doc "alias-help"\na = a', 'original', 'alias-help'),
    ('import other as f\n@doc "restored"\nf = a', 'restored', 'restored'),
])
def test_d1_03_05_b1_channels_after_replacement_import_restore(tmp_path, tail, doc, help_doc):
    source = '@doc "original"\nf(x) = "G-inline" x\na = f\n' + tail
    root, entry = modules(tmp_path, {'base': source, 'other': 'v = 1'})
    mod = root.load_module('base', entry)
    group = mod.get_export('a')
    assert group(4) == 4 and group.owner == ('base', 'f')
    # Source construction must complete before the expected missing-feature RED.
    snap = projection(mod, group)
    assert snap.projected_doc == doc and snap.help_doc == help_doc
    assert snap.binding_metadata.get('doc', None) == (None if doc == 'G-inline' else doc)
    old_map = snap.binding_metadata
    group.records[0].closure.merge_binding_metadata('a', GeniaMap().put('doc', 'after-completion'))
    assert snap.binding_metadata is old_map and snap.projected_doc == doc
    assert snap.help_doc == help_doc
    if doc != 'G-inline':
        # Deliberately mutate the original host container, not a language value.
        group.records[0].closure.binding_metadata['f']._entries.clear()
        assert snap.binding_metadata.get('doc') == doc


def test_d1_03_missing_doc_is_absence_not_rendered_or_replacement_inline(tmp_path):
    root, entry = modules(tmp_path, {'base': 'f(x)=x\na=f\ng(x)="H-inline" x\nf=g'})
    mod = root.load_module('base', entry)
    group = mod.get_export('a')
    assert group(7) == 7
    snap = projection(mod, group)
    assert snap.projected_doc is None and snap.help_doc is None


def test_d1_04_reexport_reuses_original_despite_later_help_changes(tmp_path):
    root, entry = modules(tmp_path, {
        'base': '@doc "base-doc"\nf(x)=x\na=f',
        'again': 'import base\n@doc "reexport-help"\na = base.a',
    })
    base = root.load_module('base', entry)
    group = base.get_export('a')
    again = root.load_module('again', entry)
    assert again.get_export('a') is group and group.metadata.get('doc') == 'reexport-help'
    snap = projection(base, group)
    assert projection(again, group) is snap
    assert snap.projected_doc == 'base-doc' and snap.help_doc == 'base-doc'


@pytest.mark.parametrize('failed', [False, True], ids=['never-directly-exported', 'failed-origin-retry'])
def test_d1_04_06_escaped_values_do_not_gain_completion_from_owner_text(tmp_path, failed):
    escaped = []
    root = make_global_env([])
    root.set_host('keep', escaped.append, visibility='runtime-public')
    source = 'f(x)=x\nkeep(f)\nf=7' + ('\n1/0' if failed else '')
    root, entry = modules(tmp_path, {'origin': source}, root)
    if failed:
        with pytest.raises(ZeroDivisionError):
            root.load_module('origin', entry)
        assert 'origin' not in root.loaded_modules and 'origin' not in root.loading_modules
        (tmp_path / 'origin.genia').write_text('f(x)=x+1', encoding='utf-8')
        retry = root.load_module('origin', entry)
        assert retry.get_export('f') is not escaped[0]
        assert retry.get_export('f').owner == escaped[0].owner
    else:
        root.load_module('origin', entry)
    old = escaped[0]
    assert old(4) == 4
    root.set_host('escaped', old, visibility='runtime-public')
    (tmp_path / 'again.genia').write_text('a=escaped', encoding='utf-8')
    again = root.load_module('again', entry)
    assert again.get_export('a') is old
    assert all(original is not old for original, _ in pairs(again))


def test_d1_01_cache_publication_already_contains_projection(tmp_path):
    class ObservedCache(dict):
        """Observe actual cache publication without implementing a snapshot or loader."""

        def __setitem__(self, name, value):
            if name == 'base':
                assert isinstance(getattr(value, '_ordinary_completions', None), tuple), 'D1: publishing incomplete module'
                assert len(value._ordinary_completions) == 1
            super().__setitem__(name, value)

    root, entry = modules(tmp_path, {'base': 'f(x)=x'})
    root.loaded_modules = ObservedCache(root.loaded_modules)
    root.load_module('base', entry)


def test_d1_01_cache_hit_synchronizes_with_completion_writer_lock(tmp_path):
    root, entry = modules(tmp_path, {'base': 'f(x)=x'})
    mod = root.load_module('base', entry)

    class ObservedCache(dict):
        """Check the accepted Python lock boundary deterministically, without sleeps."""

        def __contains__(self, key):
            if key == 'base':
                assert environments._BINDING_LOCK.locked(), 'D1: cache hit reads outside completion synchronization'
            return super().__contains__(key)

    root.loaded_modules = ObservedCache(root.loaded_modules)
    assert root.load_module('base', entry) is mod


def test_d1_06_publication_failure_discards_private_candidate_and_retry_is_fresh(tmp_path):
    seen = []

    class FailedPublication(RuntimeError):
        """Test-only injected failure at the existing cache publication assignment."""

    class FailingCache(dict):
        """Retain failed candidate to inspect leakage; raise before inserting it."""

        def __setitem__(self, key, value):
            if key == 'base':
                seen.append(value)
                raise FailedPublication('publication sentinel')
            super().__setitem__(key, value)

    root, entry = modules(tmp_path, {'dep': 'value=4', 'base': 'import dep\nf(x)=x'})
    root.loaded_modules = FailingCache(root.loaded_modules)
    with pytest.raises(FailedPublication, match='publication sentinel'):
        root.load_module('base', entry)
    assert 'base' not in root.loaded_modules and 'base' not in root.loading_modules
    dependency = root.loaded_modules['dep']
    root.loaded_modules = dict(root.loaded_modules)
    retry = root.load_module('base', entry)
    assert root.loaded_modules['dep'] is dependency
    assert seen[0].get_export('f') is not retry.get_export('f')
    assert projection(seen[0], seen[0].get_export('f')) is not projection(retry, retry.get_export('f'))


def test_d1_02_06_capture_does_not_execute_host_body_or_clone_closure_payload(tmp_path):
    calls = []
    root = make_global_env([])
    shared = GeniaRef(1)
    root.set_host('shared', shared, visibility='runtime-public')
    root.set_host('effect', lambda: calls.append('ran'), visibility='runtime-public')
    cell = GeniaCell(shared)
    root.set_host('shared_cell', cell, visibility='runtime-public')
    try:
        root, entry = modules(tmp_path, {'base': 'f() = effect()\nshell(x) = x |> $(cat)'}, root)
        mod = root.load_module('base', entry)
        assert calls == []
        group = mod.get_export('f')
        snap = projection(mod, group)
        assert snap.clauses[0].materialize().closure is group.records[0].closure
        assert snap.clauses[0].materialize().closure.get('shared') is shared
        assert snap.clauses[0].materialize().closure.get('shared_cell') is cell
        shared.set(9)
        assert snap.clauses[0].materialize().closure.get('shared').get() == 9
        assert cell._state_ref.get() == 9
        assert len(projection(mod, mod.get_export('shell')).clauses) == 1
        assert calls == []
    finally:
        cell.stop()
        cell._thread.join(timeout=2)
        assert not cell._thread.is_alive(), 'test Cell worker must be reclaimed even in RED'


def test_d1_06_module_value_construction_failure_control(tmp_path, monkeypatch):
    """Exercise the existing last preparation boundary; keep all old effects/dependencies."""
    seen = []
    root = make_global_env([])
    root.set_host('keep', seen.append, visibility='runtime-public')
    root, entry = modules(tmp_path, {'dep': 'v=1', 'base': 'import dep\nf(x)=x\nkeep(f)'}, root)
    original = environments.ModuleValue

    def broken(name, *args, **kwargs):
        """Raise before constructing the real completed value; implement no D1 machinery."""
        if name == 'base':
            raise MemoryError('construction sentinel')
        return original(name, *args, **kwargs)

    monkeypatch.setattr(environments, 'ModuleValue', broken)
    with pytest.raises(MemoryError, match='construction sentinel'):
        root.load_module('base', entry)
    assert 'base' not in root.loaded_modules and not root.loading_modules
    assert root.loaded_modules['dep'].get_export('v') == 1 and seen[0](4) == 4
    monkeypatch.setattr(environments, 'ModuleValue', original)
    retry = root.load_module('base', entry)
    assert retry.get_export('f') is not seen[0]


@pytest.mark.parametrize('source', ['import cycle', 'import other'])
def test_d1_07_cycle_control_preserves_error_and_cleans_loading_state(tmp_path, source):
    root, entry = modules(tmp_path, {'cycle': source, 'other': 'import cycle'})
    with pytest.raises(RuntimeError, match='Module import cycle detected while loading cycle'):
        root.load_module('cycle', entry)
    assert not root.loading_modules and 'cycle' not in root.loaded_modules


def test_d1_07_source_failure_control_preserves_prior_effect_and_dependency(tmp_path):
    values = []
    root = make_global_env([])
    root.set_host('effect', values.append, visibility='runtime-public')
    root, entry = modules(tmp_path, {'dep': 'v=4', 'base': 'import dep\neffect(3)\n1/0'}, root)
    with pytest.raises(ZeroDivisionError):
        root.load_module('base', entry)
    assert values == [3] and root.loaded_modules['dep'].get_export('v') == 4
    assert 'base' not in root.loaded_modules and not root.loading_modules


def test_d1_07_live_group_control_keeps_alias_and_binding_metadata(tmp_path):
    root, entry = modules(tmp_path, {'base': '@doc "original"\nf(x)=x\na=f\nf(x,y)=x+y'})
    mod = root.load_module('base', entry)
    group = mod.get_export('a')
    assert group is mod.get_export('f') and group(2, 3) == 5
    assert group.records[0].closure.get_metadata('f').get('doc') == 'original'
    assert group.records[0].closure.get_metadata('a').items() == []
