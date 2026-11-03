"""D2a RED: completion lookup, frozen base, link validation and canonical order (#1250).

Acceptance IDs D2a-01..05 and D2a-09 of docs/design/pre-r29-model-b-d2-linking-design.md
section 9.1. PYTHON REFERENCE HOST ONLY; no shared spec; no public surface. The private
protocol is documented in tests/unit/model_b_d2a_support.py. All D2a seams are absent
today, so these tests fail by design. Error texts are the section 6.1 frozen forms.
"""

import itertools

import pytest

import genia
from genia import callable as callables
from genia.callable import OpenFunctionDuplicateSelectionError, OpenFunctionError
from tests.unit.model_b_d2a_support import (
    base_world, completion_for, contributor, explicit_unit, frozen, linking, world, no_runtime_calls,
)

F5 = "f(a1, a2, a3, a4, a5) = 0\n"


# --- D2a-01: typed completion lookup (exact identity) ------------------------------------


def test_d2a_01_direct_alias_replaced_slot_and_reexport_share_one_projection(tmp_path):
    root, entry, base, _ = base_world(tmp_path, "f(x) = x\na = f\nf = 3\n")
    # B1 replaced slot: `f` now holds 3, but the exported alias is still the original G.
    group = base.get_export("a")
    assert base.get_export("f") == 3 and group.name == "f" and group.owner == ("base", "f")
    snapshot = completion_for(base, group)
    assert snapshot is not None and completion_for(base, base.get_export("a")) is snapshot
    (tmp_path / "relay.genia").write_text("import base\nh = base.a\n", encoding="utf-8")
    relay = root.load_module("relay", entry)
    assert relay.get_export("h") is group
    assert completion_for(relay, group) is snapshot  # re-export reaches the origin witness
    assert completion_for(base, group) is snapshot


def test_d2a_01_direct_export_without_slot_replacement(tmp_path):
    root, entry, base, group = base_world(tmp_path, "f(x) = x\n")
    snapshot = completion_for(base, group)
    assert snapshot is not None and snapshot.original is group


def test_d2a_01_no_authority_for_non_ordinary_or_uncompleted_values(tmp_path):
    root, entry, base, group = base_world(
        tmp_path, "f(x) = x\nlam = (x) -> x\nalias = lam\nopen o(1) = 1\n",
    )
    linked = linking().link_view(frozen(base, group), [])
    assert completion_for(base, base.get_export("lam")) is None
    assert completion_for(base, base.get_export("alias")) is None  # local alias of a lambda
    assert completion_for(base, base.get_export("o")) is None  # closed/explicit callable
    assert completion_for(base, root.get("map")) is None  # builtin / prelude callable
    assert completion_for(base, lambda *args: 0) is None  # host callable
    assert completion_for(base, linked) is None  # a view never carries authority
    # An entry-scope ordinary function was never published by the module loader.
    local = genia.run_source("g(x) = x\ng", root, filename="<command>")
    assert completion_for(base, local) is None
    # A same-spelling group from a different module is a different G (name never matches).
    (tmp_path / "other.genia").write_text("f(x) = x\n", encoding="utf-8")
    other = root.load_module("other", entry)
    assert completion_for(base, other.get_export("f")) is None
    assert completion_for(other, group) is None


# --- D2a-02: FrozenOrdinaryBase fidelity -----------------------------------------------


def test_d2a_02_frozen_base_copies_clauses_keys_and_provenance(tmp_path):
    source = "offset = 10\nf(x) = x + offset\nf(x, y) = x + y\nf(0, y, z) = z\n"
    root, entry, base, group = base_world(tmp_path, source)
    projection = completion_for(base, group)
    view_base = frozen(base, group)
    assert view_base.group is group and view_base.projection is projection
    assert (view_base.name, view_base.module_id) == ("f", "base")
    assert view_base.interface_key == projection.provenance == ("base", "f")
    assert isinstance(view_base.clauses, tuple) and len(view_base.clauses) == len(projection.clauses) == 3
    assert view_base.span == projection.clauses[0]._record.span
    for copy, clause, original in zip(view_base.clauses, projection.clauses, group.records):
        assert copy.dispatch_key == clause.dispatch_key  # tested D1-key/copy-key invariant
        assert copy.span == original.span and copy.closure is original.closure
        assert copy is not original and copy.body is not original.body
        assert copy is not clause._record


def test_d2a_02_later_changes_do_not_alter_the_frozen_base(tmp_path):
    root, entry, base, group = base_world(tmp_path, "f(x) = 17\nlater = f\n")
    first = frozen(base, group)
    group.records[0].params[0] = "changed"
    group.records[0].body.value["digits"] = "99"
    group.records.append(group.records[0])
    assert first.clauses[0].params == ["x"]
    assert first.clauses[0].body.value == {"kind": "integer", "digits": "17"}
    assert len(first.clauses) == 1
    second = frozen(base, group)
    assert second.clauses[0].params == ["x"]
    assert second.clauses[0] is not first.clauses[0]  # views from one base may not share copies
    first.clauses[0].body.value["digits"] = "1"
    assert second.clauses[0].body.value == {"kind": "integer", "digits": "17"}
    with pytest.raises((AttributeError, TypeError)):
        first.clauses += (first.clauses[0],)


# --- D2a-03: equal dispatch-key detection ------------------------------------------------


def test_d2a_03_alpha_equivalent_base_vs_contributor_is_cross_unit_duplicate(tmp_path):
    root, entry, base, group = base_world(tmp_path, "f(x) = x\n")
    ext = contributor(root, entry, tmp_path, "ext", group, ["f(y) = 1"])
    fl = linking()
    with pytest.raises(callables.OpenFunctionCrossUnitDuplicateClauseError) as caught:
        fl.plan_link(frozen(base, group), [ext])
    assert isinstance(caught.value, OpenFunctionError) and isinstance(caught.value, TypeError)
    assert str(caught.value) == (
        "open-function-cross-unit-duplicate-clause: f has an identical dispatch key in units "
        "base[base] and 'ext' shape=('fixed', 1) (first at base:1, duplicate at ext:2)"
    )
    assert caught.value.interface_key == ("base", "f")
    assert (caught.value.first_unit, caught.value.second_unit) == ("base", "ext")
    assert caught.value.shape == ("fixed", 1)


def test_d2a_03_contributor_vs_contributor_and_literal_distinctions(tmp_path):
    root, entry, base, group = base_world(tmp_path, F5)
    fl = linking()
    one = contributor(root, entry, tmp_path, "one", group, ["f(0) = 1"])
    two = contributor(root, entry, tmp_path, "two", group, ["f(0) = 2"])
    with pytest.raises(callables.OpenFunctionCrossUnitDuplicateClauseError) as caught:
        fl.plan_link(frozen(base, group), [one, two])
    assert str(caught.value) == (
        "open-function-cross-unit-duplicate-clause: f has an identical dispatch key in units "
        "'one' and 'two' shape=('fixed', 1) (first at one:2, duplicate at two:2)"
    )
    # true vs 1 and 1 vs 1.0 are distinct keys (proved here, not assumed).
    tru = contributor(root, entry, tmp_path, "tru", group, ["f(true) = 1"])
    uno = contributor(root, entry, tmp_path, "uno", group, ["f(1) = 2"])
    flt = contributor(root, entry, tmp_path, "flt", group, ["f(1.0) = 3"])
    assert len(fl.plan_link(frozen(base, group), [tru, uno, flt])) == 3


def test_d2a_03_guard_alpha_equivalence_and_free_name_distinction(tmp_path):
    root, entry, base, group = base_world(tmp_path, F5)
    fl = linking()
    alpha = contributor(root, entry, tmp_path, "alpha", group, ["f(a, b) ? a > b = 1"])
    beta = contributor(root, entry, tmp_path, "beta", group, ["f(c, d) ? c > d = 2"])
    with pytest.raises(callables.OpenFunctionCrossUnitDuplicateClauseError):
        fl.plan_link(frozen(base, group), [alpha, beta])
    free_p = contributor(root, entry, tmp_path, "free_p", group, ["f(a) ? a > p = 1"])
    free_q = contributor(root, entry, tmp_path, "free_q", group, ["f(a) ? a > q = 2"])
    assert len(fl.plan_link(frozen(base, group), [free_p, free_q])) == 2
    other_guard = contributor(root, entry, tmp_path, "other_guard", group, ["f(a, b) ? a < b = 3"])
    assert len(fl.plan_link(frozen(base, group), [alpha, other_guard])) == 2


def test_d2a_03_planning_runs_no_matcher_guard_body_or_callback(tmp_path):
    root, entry, base, group = base_world(tmp_path, F5)
    calls = []
    root.set_host("probe", lambda *args: calls.append(args) or True, visibility="runtime-public")
    one = contributor(root, entry, tmp_path, "one", group, ["f(a) ? probe(a) = probe(a)"])
    two = contributor(root, entry, tmp_path, "two", group, ["f(b) ? probe(b) = probe(b)"])
    fl = linking()
    with pytest.raises(callables.OpenFunctionCrossUnitDuplicateClauseError):
        fl.plan_link(frozen(base, group), [one, two])
    fine = contributor(root, entry, tmp_path, "fine", group, ["f(a) ? probe(a) = probe(a)", "f(0) = probe(0)"])
    fl.link_view(frozen(base, group), [fine])
    assert calls == []


# --- D2a-04: fixed n vs varargs m <= n ----------------------------------------------------


SHAPE_CONFLICT = (
    "open-function-shape-conflict: f: fixed/1 in unit base[base] (at base:1) conflicts with "
    "varargs/1+ in unit 'ext' (at ext:2); a fixed-arity clause conflicts with a varargs clause "
    "of another unit whose minimum arity is not greater"
)


def test_d2a_04_fixed_vs_varargs_with_disjoint_patterns_is_rejected(tmp_path):
    root, entry, base, group = base_world(tmp_path, "f(x) = x\n")
    ext = contributor(root, entry, tmp_path, "ext", group, ["f(x, ..r) = 1"])
    with pytest.raises(callables.OpenFunctionShapeConflictError) as caught:
        linking().plan_link(frozen(base, group), [ext])
    assert str(caught.value) == SHAPE_CONFLICT
    assert isinstance(caught.value, OpenFunctionError)
    assert (caught.value.first_unit, caught.value.second_unit) == ("base", "ext")
    assert (caught.value.first_shape, caught.value.second_shape) == (("fixed", 1), ("varargs", 1))
    # Disjoint patterns still conflict: shape, not pattern overlap, is the criterion.
    root2, entry2, base2, group2 = base_world(tmp_path / "second", "f(0) = 0\n")
    ext2 = contributor(root2, entry2, tmp_path / "second", "ext", group2, ["f(1, ..r) = 1"])
    with pytest.raises(callables.OpenFunctionShapeConflictError):
        linking().plan_link(frozen(base2, group2), [ext2])


def test_d2a_04_accepted_shape_combinations(tmp_path):
    fl = linking()
    root, entry, base, group = base_world(tmp_path, "f(a) = a\n")
    # varargs minimum greater than the fixed arity, and a same-unit fixed+varargs mix.
    mix = contributor(root, entry, tmp_path, "mix", group, ["f(a, b, c) = 1", "f(a, b, ..r) = 2"])
    assert len(fl.plan_link(frozen(base, group), [mix])) == 1
    # varargs vs varargs across units is left to runtime varargs ambiguity.
    root2, entry2, base2, group2 = base_world(tmp_path / "v", "f(a, ..r) = a\n")
    more = contributor(root2, entry2, tmp_path / "v", "more", group2, ["f(a, b, ..r) = 2"])
    same_min = contributor(root2, entry2, tmp_path / "v", "same_min", group2, ["f(0, ..r) = 3"])
    assert len(fl.plan_link(frozen(base2, group2), [more, same_min])) == 2


# --- D2a-05: canonical order -------------------------------------------------------------


def test_d2a_05_every_with_order_gives_the_same_view_sorted_by_module_id(tmp_path):
    root, entry, base, group = base_world(tmp_path, F5)
    units = [
        contributor(root, entry, tmp_path, name, group, [f"f({index}) = {index}"])
        for index, name in enumerate(["Beta", "alpha", "_under", "zeta"])
    ]
    fl = linking()
    expected = ["Beta", "_under", "alpha", "zeta"]  # Python str order, no case folding
    seen = set()
    for order in itertools.permutations(units):
        view = fl.link_view(frozen(base, group), list(order))
        assert isinstance(view.units, tuple)
        assert [unit.declaring_module_id for unit in view.units] == expected
        seen.add(tuple(unit.declaring_module_id for unit in view.units))
    assert len(seen) == 1


def test_d2a_05_conflict_report_is_independent_of_with_order(tmp_path):
    root, entry, base, group = base_world(tmp_path, F5)
    units = [
        contributor(root, entry, tmp_path, name, group, [f"f({tag}) = 1"])
        for name, tag in [("zeta", "y"), ("alpha", "x"), ("mid", "z")]
    ]
    fl = linking()
    messages = set()
    for order in itertools.permutations(units):
        with pytest.raises(callables.OpenFunctionCrossUnitDuplicateClauseError) as caught:
            fl.link_view(frozen(base, group), list(order))
        messages.add(str(caught.value))
    assert messages == {
        "open-function-cross-unit-duplicate-clause: f has an identical dispatch key in units "
        "'alpha' and 'mid' shape=('fixed', 1) (first at alpha:2, duplicate at mid:2)"
    }


def test_d2a_05_duplicate_selection_is_raised_before_link_validation(tmp_path):
    root, entry, base, group = base_world(tmp_path, F5)
    first = contributor(root, entry, tmp_path, "ext", group, ["f(x) = 1"])
    again = callables.GeniaOpenContributionUnit(group.owner, "ext", list(first.clauses), target=group)
    clash = contributor(root, entry, tmp_path, "clash", group, ["f(y) = 2"])  # conflicts with ext
    with pytest.raises(OpenFunctionDuplicateSelectionError):
        linking().link_view(frozen(base, group), [first, clash, again])


# --- D2a-09: explicit bases use the same validator; legacy public path untouched ---------


EXPLICIT_FILES = {
    "ebase": 'open get("mem", k) = 1\n',
    "e1": 'import ebase\nextend ebase.get("db", key) = 2\n',
    "e2": 'import ebase\nextend ebase.get("db", key) = 3\n',
}


def test_d2a_09_explicit_base_gains_cross_unit_validation_in_the_private_validator(tmp_path):
    root, entry = world(tmp_path, EXPLICIT_FILES)
    ebase = root.load_module("ebase", entry).get_export("get")
    key = ebase.interface_key
    units = [explicit_unit(root.load_module(name, entry), key) for name in ("e1", "e2")]
    with pytest.raises(callables.OpenFunctionCrossUnitDuplicateClauseError) as caught:
        linking().link_view(ebase, units)
    assert str(caught.value) == (
        "open-function-cross-unit-duplicate-clause: get has an identical dispatch key in units "
        "'e1' and 'e2' shape=('fixed', 2) (first at e1:2, duplicate at e2:2)"
    )
    ok = linking().link_view(ebase, units[:1])
    assert ok.base is ebase and ok("mem", "x") == 1


def test_d2a_09_public_use_over_explicit_bases_rejects_equal_keys_at_selection_d2b(tmp_path):
    root, entry = world(tmp_path, EXPLICIT_FILES)
    program = "import ebase\nimport e1\nimport e2\nuse get from ebase with e1, e2\n0"
    with pytest.raises(callables.OpenFunctionCrossUnitDuplicateClauseError) as caught:
        genia.run_source(program, root, filename=entry)
    assert "open-function-cross-unit-duplicate-clause: get has an identical dispatch key" in str(
        caught.value
    )


@pytest.mark.parametrize('fail_origin', [False, True], ids=['unfinished', 'failed-and-retried'])
def test_d2a_01_unfinished_or_failed_origin_never_confers_authority(tmp_path, fail_origin):
    root, entry = world(tmp_path, {'origin': 'f(x)=x\nretain(f)\n' + ('1/0\n' if fail_origin else ''),
                                   'relay': 'a=escaped\n'})
    seen = []

    def retain(group):
        """Export an escaped identity while its declaring module is still loading."""
        root.set_host('escaped', group, visibility='runtime-public')
        relay = root.load_module('relay', entry)
        assert 'origin' not in root.loaded_modules
        assert completion_for(relay, group) is None
        seen.append((group, relay))

    root.set_host('retain', retain, visibility='runtime-public')
    if fail_origin:
        with pytest.raises(ZeroDivisionError):
            root.load_module('origin', entry)
        assert 'origin' not in root.loaded_modules and 'origin' not in root.loading_modules
        old, relay = seen[0]
        assert completion_for(relay, old) is None
        (tmp_path / 'origin.genia').write_text('f(x)=x+1\n', encoding='utf-8')
        retry = root.load_module('origin', entry)
        assert completion_for(retry, old) is None
        assert completion_for(retry, retry.get_export('f')) is not None
    else:
        origin = root.load_module('origin', entry)
        group, relay = seen[0]
        assert completion_for(origin, group) is not None
        # An unfinished re-export did not retroactively acquire a witness.
        assert completion_for(relay, group) is None


def test_d2a_02_ref_cell_and_runtime_literal_identity_survive_view_materialization(tmp_path):
    from genia import ir
    from genia.values import GeniaCell, GeniaRef

    ref = GeniaRef(1)
    cell = GeniaCell(ref)
    payload = [ref, cell]
    root = genia.make_global_env([])
    root.set_host('shared', ref, visibility='runtime-public')
    root.set_host('shared_cell', cell, visibility='runtime-public')

    def literalize(group):
        """Host-only literal fixture, installed before successful module completion."""
        group.records[0].body = ir.IrLiteral(payload)

    root.set_host('literalize', literalize, visibility='runtime-public')
    try:
        root, entry, module, group = base_world(tmp_path, 'f()=0\nliteralize(f)\n', root=root)
        base = frozen(module, group)
        assert base.clauses[0].closure is group.records[0].closure
        assert base.clauses[0].closure.get('shared') is ref
        assert base.clauses[0].closure.get('shared_cell') is cell
        assert base.clauses[0].body.value is payload
        view = linking().link_view(base, [])
        root.publish_view('v', view)
        result = genia.run_source('v()', root, filename=entry)
        assert result is payload and result[0] is ref and result[1] is cell
        ref.set(9)
        assert genia.run_source('v()', root)[0].get() == 9
        assert cell._state_ref.get() == 9
    finally:
        cell.stop()
        cell._thread.join(timeout=2)
        assert not cell._thread.is_alive()


def test_d2a_02_later_slot_alias_and_help_metadata_do_not_rewrite_completion(tmp_path):
    from genia.values import GeniaMap

    root, entry, module, group = base_world(
        tmp_path, '@doc "original"\nf(x)=17\na=f\n')
    first = frozen(module, group)
    p = first.projection
    before = (tuple(p.binding_metadata.items()), p.projected_doc,
              p.help_doc, tuple(p.help_metadata.items()))
    closure = group.records[0].closure
    closure.assign('f', 99)
    closure.merge_binding_metadata('a', GeniaMap().put('doc', 'alias-after'))
    closure.merge_binding_metadata('f', GeniaMap().put('doc', 'slot-after'))
    group.metadata = group.metadata.put('doc', 'help-after')
    group.docstring = 'inline-after'
    second = frozen(module, group)
    assert second.projection is p
    assert (tuple(p.binding_metadata.items()), p.projected_doc,
            p.help_doc, tuple(p.help_metadata.items())) == before
    assert p.projected_doc == 'original'
    assert linking().link_view(first, [])(3) == linking().link_view(second, [])(3) == 17
    with pytest.raises((TypeError, AttributeError)):
        p.binding_metadata._entries['doc'] = 'mutated'


NESTED_KEYS = [
    ('f(a) ? ((a) -> a)(1) > 0 = 1', 'f(b) ? ((b) -> b)(1) > 0 = 2', True),
    ('f(a) ? ((p) -> p)(a) > 0 = 1', 'f(a) ? ((p) -> a)(a) > 0 = 2', False),
    ('f(x) ? {local =: x; ((y) -> local + y)(1) > 0} = 1',
     'f(a) ? {bound =: a; ((z) -> bound + z)(1) > 0} = 2', True),
    ('f(x) ? {local =: x; ((y) -> outside + y)(1) > 0} = 1',
     'f(a) ? {bound =: a; ((z) -> another + z)(1) > 0} = 2', False),
]


@pytest.mark.parametrize('left,right,duplicate', NESTED_KEYS)
def test_d2a_03_nested_guard_lambda_shadowing_and_free_names(tmp_path, left, right, duplicate):
    root, entry, module, group = base_world(tmp_path, F5)
    units = [contributor(root, entry, tmp_path, name, group, [source])
             for name, source in [('alpha', left), ('beta', right)]]
    if duplicate:
        with pytest.raises(callables.OpenFunctionCrossUnitDuplicateClauseError):
            linking().plan_link(frozen(module, group), units)
    else:
        assert len(linking().plan_link(frozen(module, group), units)) == 2


def test_d2a_03_build_never_calls_matcher_guard_body_get_or_renderer(tmp_path, monkeypatch):
    from genia import builtins as genia_builtins
    from genia.environment import Env

    effects = []
    root = genia.make_global_env([])
    root.set_host('probe', lambda value: effects.append(value) or True, visibility='runtime-public')
    root, entry, module, group = base_world(
        tmp_path, 'pattern Watch(v)=probe(v)\nf(Watch(v)) ? probe(v) = probe(v)\n', root=root)
    unit = contributor(root, entry, tmp_path, 'ext', group, ['f(a,b)=probe(a)'])
    base = frozen(module, group)

    def forbidden(*args, **kwargs):
        """Any runtime lookup/rendering during pure link construction is a test failure."""
        raise AssertionError('link builder invoked lookup or renderer')

    with monkeypatch.context() as patch, no_runtime_calls():
        patch.setattr(Env, 'get', forbidden)
        patch.setattr(genia_builtins, 'format_display', forbidden)
        patch.setattr(genia_builtins, 'format_debug', forbidden)
        linking().plan_link(base, [unit])
        linking().link_view(base, [unit])
    assert effects == []


def test_d2a_04_varargs_base_fixed_contributor_reverses_shape_payload_and_spans(tmp_path):
    root, entry, module, group = base_world(tmp_path, 'f(0,..r)=0\n')
    unit = contributor(root, entry, tmp_path, 'ext', group, ['f(1)=1'])
    with pytest.raises(callables.OpenFunctionShapeConflictError) as caught:
        linking().plan_link(frozen(module, group), [unit])
    error = caught.value
    assert error.interface_key == ('base', 'f')
    assert (error.first_shape, error.second_shape) == (('varargs', 1), ('fixed', 1))
    assert error.first_span == group.records[0].span
    assert error.second_span == unit.clauses[0].span
    assert str(error) == (
        "open-function-shape-conflict: f: varargs/1+ in unit base[base] (at base:1) conflicts with "
        "fixed/1 in unit 'ext' (at ext:2); a fixed-arity clause conflicts with a varargs clause "
        "of another unit whose minimum arity is not greater")


def test_d2a_05_import_order_and_selection_order_have_same_dispatch_and_conflicts(tmp_path):
    observations = []
    for number, order in enumerate(itertools.permutations(['alpha', 'beta', 'zeta'])):
        directory = tmp_path / str(number)
        root, entry, module, group = base_world(directory, F5)
        # Preload modules in each permutation before harvesting their units.
        for name, source in [('alpha','f(0)=10'), ('beta','f(1)=20'), ('zeta','f(x)=30')]:
            (directory / (name + '.genia')).write_text('import iface\nextend iface.' + source + '\n')
        for name in order:
            root.load_module(name, entry)
        units = [callables.GeniaOpenContributionUnit(group.owner, name,
                  list(root.loaded_modules[name].contributions[('iface','f')].clauses), target=group)
                 for name in reversed(order)]
        view = linking().link_view(frozen(module, group), [u for u in units if u.declaring_module_id != 'zeta'])
        assert view(0) == 10 and view(1) == 20
        observations.append(tuple(u.declaring_module_id for u in view.units))
        # alpha/beta are distinct, so add a genuine equal-key partner for zeta.
        twin = contributor(root, entry, directory, 'twin', group, ['f(y)=99'])
        with pytest.raises(callables.OpenFunctionCrossUnitDuplicateClauseError) as caught:
            linking().link_view(frozen(module, group), units + [twin])
        observations.append(str(caught.value))
    assert len(set(observations[::2])) == len(set(observations[1::2])) == 1


def test_d2a_05_first_pair_precedes_later_duplicate_and_equal_key_precedes_shape(tmp_path):
    # base/alpha shape conflict precedes a later alpha/beta duplicate.
    root, entry, module, group = base_world(tmp_path, 'f(0)=0\n')
    alpha = contributor(root, entry, tmp_path, 'alpha', group, ['f(1,..r)=1'])
    beta = contributor(root, entry, tmp_path, 'beta', group, ['f(1,..s)=2'])
    for order in ([beta,alpha], [alpha,beta]):
        with pytest.raises(callables.OpenFunctionShapeConflictError) as caught:
            linking().link_view(frozen(module, group), order)
        assert (caught.value.first_unit, caught.value.second_unit) == ('base','alpha')
        assert caught.value.first_span == group.records[0].span
        assert caught.value.second_span == alpha.clauses[0].span
    # Equal keys in a pair are diagnosed before a conflicting later record.
    root, entry, module, group = base_world(tmp_path / 'equal', 'f(x)=x\n')
    unit = contributor(root, entry, tmp_path / 'equal', 'ext', group, ['f(y)=1','f(z,..r)=2'])
    with pytest.raises(callables.OpenFunctionCrossUnitDuplicateClauseError) as caught:
        linking().link_view(frozen(module, group), [unit])
    assert caught.value.first_span == group.records[0].span
    assert caught.value.duplicate_span == unit.clauses[0].span


def test_d2a_02_later_contribution_list_and_store_changes_do_not_retroactively_change_view(tmp_path):
    root, entry, module, group = base_world(tmp_path, F5)
    unit = contributor(root, entry, tmp_path, 'ext', group, ['f(0)=1'])
    later = contributor(root, entry, tmp_path, 'later', group, ['f(1)=2'])
    view = linking().link_view(frozen(module, group), [unit])
    root.publish_view('v', view)
    assert genia.run_source('v(0)', root, filename=entry) == 1
    unit.clauses.extend(later.clauses)
    root.ordinary_contributions[id(group)] = later  # host-only store fixture; evaluator stays inert
    assert genia.run_source('v(0)', root, filename=entry) == 1
    with pytest.raises(callables.OpenFunctionNoMatchingCaseError):
        genia.run_source('v(1)', root, filename=entry)
    newer = linking().link_view(frozen(module, group), [later])
    root.publish_view('newer', newer)
    assert genia.run_source('newer(1)', root, filename=entry) == 2
