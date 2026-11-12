"""Python-private E1 lifecycle consumers, not source/publication or portability proof.

Controlled `_state` stores exercise real GREEN-B1 values, never a fake callable.
Live synchronous annotation admission, transactions, slots and lineage are E2
(design 10.1/11). E1 must fail closed in their absence. The self-frame builder
interface test is separately identified; remaining REDs exercise existing paths.
"""

from dataclasses import replace

import pytest

import genia
from genia import callable as c
from genia.environment import ImmutableBindingError
from genia.equality import genia_equal
from genia.http_annotation_binding import resolve_http_annotation
from genia.test_cli import discover_annotated_test_units
from genia.utf8 import format_debug, format_display
from genia.values import GeniaFlow, GeniaMap, GeniaNamedPattern, GeniaOptionSome, GeniaProtected, GeniaRef, GeniaSymbol
from tests.unit.model_b_slice_e1_support import bound_group, module_world, prepare_use, record


ERRORS = {
    "building": "closed-function-not-yet-published: f is not yet published",
    "initializing": "closed-function-not-yet-published: f is not yet published",
    "failed": "closed-function-failed-publication: closed function failed publication",
}


def fixture(state, source="f(x) = tripwire(x)"):
    """Expose an actual private group in a controlled state, retaining real dispatch."""
    env, group = bound_group(closed=True, source=source)
    effects = []

    def tripwire(x):
        """Distinguish successful dispatch from a lifecycle rejection."""
        effects.append(x)
        return x

    env.set_host("tripwire", tripwire, visibility="runtime-public")
    group._state = state
    return env, group, effects


@pytest.mark.parametrize("state", ["building", "initializing", "failed", "committed"])
@pytest.mark.parametrize("entry", ["host", "invoke", "tail", "dispatch", "apply_raw", "callback", "matcher"])
def test_invocation_state_matrix(state, entry):
    env, group, effects = fixture(state, "f(x) = some(tripwire(x))" if entry == "matcher" else "f(x) = tripwire(x)")
    if entry == "matcher":
        env.set_host("P", GeniaNamedPattern("P", group), visibility="entry-only")
        genia.run_source("g(P(x)) = x", env)
    operations = {
        "host": lambda: group(7),
        "invoke": lambda: c.invoke_callable(group, [7], tail_position=False),
        "tail": lambda: c.eval_with_tco(group, (7,)),
        "dispatch": lambda: c.eval_with_tco(lambda: c.TailCall(group, (7,)), ()),
        "apply_raw": lambda: genia.run_source("apply_raw(f, [7])", env),
        "callback": lambda: genia.run_source("[7] |> map(f)", env),
        "matcher": lambda: genia.run_source("g(7)", env),
    }
    if state == "committed":
        result = operations[entry]()
        assert result == ([7] if entry == "callback" else 7)
        assert effects == [7]
    else:
        with pytest.raises(RuntimeError) as error:
            operations[entry]()
        assert str(error.value).endswith(ERRORS[state])
        if entry == "callback":
            assert str(error.value).startswith("pipeline stage 1 failed")
        assert effects == []


@pytest.mark.parametrize("state", ["initializing", "failed"])
@pytest.mark.parametrize("arguments", ['[none("fixture")]', '[err("reason")]', "[]", "[1, 2]"])
def test_state_precedes_none_err_and_wrong_arity(state, arguments):
    env, _, effects = fixture(state)
    with pytest.raises(RuntimeError) as error:
        genia.run_source(f"apply_raw(f, {arguments})", env)
    assert str(error.value) == ERRORS[state]
    assert effects == []


def test_invoke_none_precedes_neither_state_nor_autoload():
    env, group, effects = fixture("failed")
    calls = []
    with pytest.raises(RuntimeError, match="^closed-function-failed-publication:"):
        c.invoke_callable(group, [genia.run_source('none("fixture")', env)], tail_position=True,
                          autoload_resolver=lambda *args: calls.append(args))
    assert calls == effects == []


def test_failed_pattern_guard_is_never_evaluated():
    env, _, effects = fixture("failed", "f(x) ? tripwire(x) = x")
    with pytest.raises(RuntimeError) as error:
        genia.run_source("f(7)", env)
    assert str(error.value) == ERRORS["failed"]
    assert effects == []


@pytest.mark.parametrize("state", ["initializing", "failed", "committed"])
@pytest.mark.parametrize("expression", ['doc("a")', 'meta("a")', 'help("a")', "help(a)"])
def test_reflection_checks_value_before_binding_metadata(state, expression, capsys):
    env, group, effects = fixture(state)
    group.metadata = GeniaMap().put("doc", "callable-doc")
    genia.run_source('@doc "alias-doc"\na = f', env)
    assert group.metadata.get("doc") == "callable-doc"
    if state == "committed":
        value = genia.run_source(expression, env)
        if expression.startswith("doc"):
            assert value == "alias-doc"
        elif expression.startswith("meta"):
            assert value.get("doc") == "alias-doc"
        else:
            output = capsys.readouterr().out
            assert "callable-doc" in output and "alias-doc" not in output
    else:
        with pytest.raises(RuntimeError) as error:
            genia.run_source(expression, env)
        assert str(error.value) == ERRORS[state]
        assert "alias-doc" not in capsys.readouterr().out
    assert effects == []


@pytest.mark.parametrize("state", ["initializing", "failed", "committed"])
@pytest.mark.parametrize("operation", ["extend", "use"])
def test_link_targets_have_exact_state_precedence(tmp_path, state, operation):
    root, entry, _, group = module_world(tmp_path, closed=True)
    group._state = state
    genia.run_source("import base", root, filename=entry)
    if operation == "use":
        prepare_use(root, entry, tmp_path, group)
    source = "extend base.f(x, y) = y" if operation == "extend" else "use f from base with ext"
    with pytest.raises((TypeError, RuntimeError)) as error:
        genia.run_source(source, root, filename=entry)
    expected = ("open-function-target-not-open: 'base.f' is not an open function interface"
                if state == "committed" else ERRORS[state])
    assert str(error.value) == expected


@pytest.mark.parametrize("state", ["initializing", "failed", "committed"])
def test_http_exclusion_runs_after_state_check(state):
    _, group, effects = fixture(state)
    group.metadata = GeniaMap().put("http_annotation", GeniaMap())
    with pytest.raises((TypeError, RuntimeError)) as error:
        resolve_http_annotation(group)
    expected = ("send_annotated expected a function annotated with @get or @post"
                if state == "committed" else ERRORS[state])
    assert str(error.value) == expected
    assert effects == []


@pytest.mark.parametrize("state", ["initializing", "failed", "committed"])
def test_native_discovery_checks_state_and_schedules_group(state):
    env, group, effects = fixture(state, "f() = tripwire(7)")
    genia.run_source('@test("private fixture")\na = f', env)
    if state == "committed":
        units = discover_annotated_test_units(env)
        assert len(units) == 1 and units[0].body is group
    else:
        with pytest.raises(RuntimeError) as error:
            discover_annotated_test_units(env)
        assert str(error.value) == ERRORS[state]
    assert effects == []


@pytest.mark.parametrize("render", [repr, str, format_debug, format_display])
def test_failed_render_transport_and_identity(render):
    env, group, effects = fixture("failed")
    protected = GeniaProtected("SECRET_SENTINEL", object(), GeniaSymbol("fixture"))
    env.set_host("captured", protected, visibility="entry-only")
    group.metadata = GeniaMap().put("doc", "METADATA_SENTINEL")
    ref = GeniaRef()
    ref.set(group)
    env.assign("a", ref.get())
    assert env.get("a") is group and genia_equal(group, ref.get())
    text = render([group, GeniaMap().put("f", group), GeniaOptionSome(group)])
    assert text.count("<closed-function failed>") == (2 if render in (repr, str) else 3)
    assert not any(word in text for word in ("METADATA_SENTINEL", "SECRET_SENTINEL", "tripwire"))
    assert render(group) == "<closed-function failed>"
    assert effects == []


def test_failed_pipeline_skips_and_unpulled_flow_do_not_invoke():
    env, _, effects = fixture("failed")
    result = genia.run_source('none("upstream") |> f', env)
    assert result.reason == "upstream"
    env.set_host("source", GeniaFlow(lambda: iter([7])), visibility="entry-only")
    flow = genia.run_source("source |> map(f)", env)
    assert effects == []
    with pytest.raises(RuntimeError, match="closed-function-failed-publication"):
        list(flow.consume())
    assert effects == []


def test_apply_raw_argument_validation_still_precedes_invocation():
    env, _, effects = fixture("failed")
    with pytest.raises(TypeError, match="apply_raw expected a list"):
        genia.run_source('apply_raw(f, "bad")', env)
    assert effects == []


def test_varargs_direct_host_diagnostic_uses_group_name():
    env, group, _ = fixture("failed")
    attempted = replace(record(env, name="other"), rest_param="rest")
    with pytest.raises(TypeError) as error:
        group.add_clause(attempted)
    assert str(error.value) == (
        "closed-function-not-extensible: cannot declare f/1+: f refers to a closed function"
    )


def test_immutable_defining_name_precedes_closedness_and_rhs():
    env, group, effects = fixture("committed")
    env.assign("f", 0)
    ticket = env.prepare_immutable_declaration("locked")
    env.commit_immutable_declaration(ticket, group)
    with pytest.raises(ImmutableBindingError, match="Cannot rebind immutable binding: locked"):
        genia.run_source("locked(x, y) = y", env)
    with pytest.raises(ImmutableBindingError, match="Cannot assign to immutable binding: locked"):
        genia.run_source("locked = tripwire(9)", env)
    assert env.get("locked") is group and effects == []


def test_private_self_frame_builder_and_extracted_record_guard():
    """Interface + behavior: guarded copies must not mutate GREEN-A's shared records.

    This one test diagnoses an absent builder separately from behavioral REDs.
    Construction-only `_from_records` identity guarantees remain unchanged.
    """
    env, ordinary = bound_group(closed=False, source="f(x) = x")
    original = ordinary.get(1)
    group = c.GeniaClosedFunction._with_self_frame("f", ordinary.records, env)
    guarded = group.get(1)
    assert guarded is not original and original.closure is env
    frame = guarded.closure
    assert frame.parent is env and frame.get("f") is group
    assert frame.immutable_names() == frozenset({"f"})
    assert frame.module_identity() == env.module_identity()
    assert frame.unit_scope() is env.unit_scope()
    assert env.get("f") is ordinary
    for state in ("initializing", "failed"):
        group._state = state
        for invoke in (lambda: guarded(7), lambda: c.eval_with_tco(guarded, (7,))):
            with pytest.raises(RuntimeError) as error:
                invoke()
            assert str(error.value) == ERRORS[state]
    group._state = "committed"
    assert guarded(7) == c.eval_with_tco(guarded, (7,)) == 7
    with pytest.raises(ImmutableBindingError):
        frame.assign("f", 9)
    # This name is private; parent publication and E2 transactions are absent.
    assert env.get("f") is ordinary


@pytest.mark.parametrize("source, expected", [
    ("f(f) = { f = f + 1; f }", 8),
    ("f([f]) = { f = f + 1; f }", 8),
    ("f(x) = { outer = x; outer }", 7),
])
def test_self_frame_preserves_local_shadowing_and_other_name_writes(source, expected):
    """Builder-interface extension: lexical semantics use the ordinary evaluator."""
    env, ordinary = bound_group(closed=False, source="outer = 0\n" + source)
    group = c.GeniaClosedFunction._with_self_frame("f", ordinary.records, env)
    group._state = "committed"
    assert group([7] if "[f]" in source else 7) == expected
    assert env.get("outer") == (7 if "outer = x" in source else 0)
    assert env.get("f") is ordinary


def test_self_identity_survives_parent_reuse_and_failed_value_is_not_revived():
    """Builder-interface extension: a body-created lambda keeps the private self frame."""
    env, ordinary = bound_group(closed=False, source="f(x) = [(y) -> f(y)]")
    group = c.GeniaClosedFunction._with_self_frame("f", ordinary.records, env)
    group._state = "committed"
    escaped = group(7)[0]
    env.assign("f", 99)
    group._state = "failed"  # controlled host fixture, not a publication transition
    with pytest.raises(RuntimeError) as error:
        escaped(7)
    assert str(error.value) == ERRORS["failed"]
    assert env.get("f") == 99


def test_unshadowed_self_assignment_is_rejected_before_rhs():
    env, ordinary = bound_group(closed=False, source="f(x) = { f = missing_rhs(); x }")
    group = c.GeniaClosedFunction._with_self_frame("f", ordinary.records, env)
    group._state = "committed"
    with pytest.raises(ImmutableBindingError, match="Cannot assign to immutable binding: f"):
        group(7)


def test_autoload_replacement_checks_closed_state_before_selecting_a_record():
    """An ordinary unresolved arity must not bypass the replacement value's guard."""
    env, failed, effects = fixture("failed")
    ordinary = c.GeniaFunctionGroup("g")
    ordinary.add_clause(record(env, name="g", params=("x", "y")))
    from genia.ir import IrVar
    with pytest.raises(RuntimeError) as error:
        c.invoke_callable(ordinary, [7], tail_position=False, callee_node=IrVar("g"),
                          autoload_resolver=lambda name, arity: failed)
    assert str(error.value) == ERRORS["failed"]
    assert effects == []
