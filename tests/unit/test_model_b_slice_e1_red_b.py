"""Python-host E1 behavioral RED against real GREEN-A closed values (#1250).

Sealing, alias metadata, opaque rendering and D2b exclusion reach existing real
operations. Every owner-sensitive fixture has a valid declaration owner and an
ordinary control. The sole test named missing_seam diagnoses absent lifecycle
state separately: no arbitrary `_state` assignment or fake transaction is used.

State-specific failed/initializing invocation, reflection, failed rendering and
transport-then-invoke oracles are deferred until that real interface exists.
Active annotation lineage, discovery and atomic publication remain E2.
"""

import pytest

import genia
from genia import callable as callables
from genia.equality import genia_equal
from genia.ordinary_completion import completion_for
from genia.utf8 import format_debug, format_display
from genia.values import (
    GeniaCell, GeniaMap, GeniaOptionSome, GeniaProtected, GeniaRef, GeniaSymbol,
)
from tests.unit.model_b_slice_e1_support import bound_group, module_world, prepare_use, record


@pytest.mark.parametrize("path", ["direct", "defining-name", "restored-name"])
def test_ordinary_append_control_reaches_mutation(path):
    scope, group = bound_group(closed=False)
    if path == "restored-name":
        saved = GeniaRef()
        saved.set(group)
        scope.assign("f", 7)
        scope.assign("f", saved.get())
    if path == "direct":
        group.add_clause(record(scope, params=("x", "y")))
    else:
        genia.run_source("f(x, y) = y", scope)
    assert scope.get("f") is group and group.sorted_arities() == [1, 2]


@pytest.mark.parametrize("path", ["direct", "defining-name", "restored-name"])
def test_closed_append_is_rejected_by_value(path):
    scope, group = bound_group(closed=True)
    if path == "restored-name":
        saved = GeniaRef()
        saved.set(group)
        scope.assign("f", 7)
        scope.assign("f", saved.get())
    assert group.owner == (scope.module_identity(), "f")
    with pytest.raises((TypeError, RuntimeError), match="closed-function-not-extensible") as caught:
        if path == "direct":
            group.add_clause(record(scope, params=("x", "y")))
        else:
            genia.run_source("f(x, y) = y", scope)
    assert str(caught.value) == (
        "closed-function-not-extensible: cannot declare f/2: f refers to a closed function"
    )
    assert scope.get("f") is group and group.sorted_arities() == [1]


def test_alias_control_reports_ordinary_ownership_not_closedness():
    scope, group = bound_group(closed=False)
    genia.run_source("a = f", scope)
    assert scope.get("a") is group and group.owner == (scope.module_identity(), "f")
    with pytest.raises(TypeError, match="function-declaration-not-owner"):
        genia.run_source("a(x, y) = y", scope)


def test_closed_alias_append_reports_closedness_before_owner_mismatch():
    scope, group = bound_group(closed=True)
    genia.run_source("a = f", scope)
    assert scope.get("a") is group and group.owner == (scope.module_identity(), "f")
    with pytest.raises((TypeError, RuntimeError), match="closed-function-not-extensible") as caught:
        genia.run_source("a(x, y) = y", scope)
    assert str(caught.value) == (
        "closed-function-not-extensible: cannot declare a/2: a refers to a closed function"
    )


def test_ordinary_metadata_control_reaches_mutation():
    _, group = bound_group(closed=False)
    group.merge_metadata(GeniaMap().put("doc", "updated"))
    assert group.metadata.get("doc") == "updated"


def test_closed_callable_metadata_cannot_be_merged_after_construction():
    _, group = bound_group(closed=True)
    before = group.metadata
    # The contract requires rejection; no new literal/class is invented for this method.
    with pytest.raises((TypeError, RuntimeError)):
        group.merge_metadata(GeniaMap().put("doc", "updated"))
    assert group.metadata is before


def test_ordinary_alias_annotations_preserve_existing_shared_help_behavior():
    scope, group = bound_group(closed=False)
    genia.run_source('@meta({test: "alias-test", route: "data-only"})\na = f', scope)
    assert scope.get_metadata("a").get("test") == "alias-test"
    assert group.metadata.get("test") == "alias-test"
    assert scope.get_metadata("f").has("test") is False


def test_closed_alias_annotations_change_binding_metadata_only():
    scope, group = bound_group(closed=True)
    before = group.metadata
    genia.run_source('@meta({test: "alias-test", route: "data-only"})\na = f', scope)
    assert scope.get("a") is group
    assert scope.get_metadata("a").get("test") == "alias-test"
    assert scope.get_metadata("a").get("route") == "data-only"
    assert scope.get_metadata("f").has("test") is False
    assert group.metadata is before  # keys are allowed, but the value's metadata is sealed


@pytest.mark.parametrize("export", ["direct", "alias", "reexport"])
def test_ordinary_capture_control_is_eligible(tmp_path, export):
    _, _, module, group = module_world(tmp_path, closed=False, export=export)
    assert completion_for(module, group) is not None


@pytest.mark.parametrize("export", ["direct", "alias", "reexport"])
def test_closed_values_never_gain_ordinary_completion(tmp_path, export):
    _, _, control, ordinary = module_world(tmp_path / "control", closed=False, export=export)
    assert completion_for(control, ordinary) is not None
    _, _, module, group = module_world(tmp_path / "closed", closed=True, export=export)
    scope = group.records[0].closure.unit_scope()
    assert group.owner == (scope.module_identity(), "f")
    assert completion_for(module, group) is None


@pytest.mark.parametrize("operation", ["extend", "use"])
def test_ordinary_link_target_control_is_eligible(tmp_path, operation):
    root, entry, _, group = module_world(tmp_path, closed=False)
    genia.run_source("import base", root, filename=entry)
    if operation == "use":
        prepare_use(root, entry, tmp_path, group)
    source = "extend base.f(x, y) = y" if operation == "extend" else "use f from base with ext"
    genia.run_source(source, root, filename=entry)
    if operation == "use":
        assert genia.run_source("f(7)", root, filename=entry) == 7
        assert genia.run_source("f(7, 8)", root, filename=entry) == 8


@pytest.mark.parametrize("operation", ["extend", "use"])
def test_closed_target_is_not_linkable(tmp_path, operation):
    root, entry, _, group = module_world(tmp_path, closed=True)
    assert group.owner == (group.records[0].closure.module_identity(), "f")
    genia.run_source("import base", root, filename=entry)
    if operation == "use":
        prepare_use(root, entry, tmp_path, group)
    source = "extend base.f(x, y) = y" if operation == "extend" else "use f from base with ext"
    # Lifecycle state is not yet constructible. Require rejection, accepting only
    # approved target/state errors; exact state-error precedence is deferred.
    with pytest.raises(
        (TypeError, RuntimeError),
        match="open-function-target-not-open|closed-function-not-yet-published|closed-function-failed-publication",
    ):
        genia.run_source(source, root, filename=entry)


@pytest.mark.parametrize("render", [repr, str, format_debug, format_display], ids=["repr", "str", "debug", "display"])
def test_constructed_closed_value_renders_opaquely(render):
    _, group = bound_group(closed=True)
    # Both initializing and committed non-failed renderings have this marker.
    # No lifecycle state is fabricated or claimed here.
    assert render(group) == "<closed-function f>"


@pytest.mark.parametrize("render", [format_debug, format_display], ids=["debug", "display"])
def test_nested_closed_rendering_hides_source_metadata_and_protected_capture(render):
    scope, group = bound_group(closed=True, source='f(x) = "SOURCE_SENTINEL" x')
    protected = GeniaProtected("PROTECTED_PAYLOAD_SENTINEL", object(), GeniaSymbol("test-only"))
    scope.set_host("captured", protected, visibility="entry-only")
    group.metadata = GeniaMap().put("doc", "METADATA_SENTINEL")  # synthetic host-owned fixture data
    nested = [group, GeniaMap().put("target", group), GeniaOptionSome(group)]
    text = render(nested)
    assert not any(s in text for s in ("SOURCE_SENTINEL", "METADATA_SENTINEL", "PROTECTED_PAYLOAD_SENTINEL"))
    assert text.count("<closed-function f>") == 3


def test_transport_and_language_identity_do_not_invoke_a_closed_value():
    scope, group = bound_group(closed=True, source="f(x) = transport_tripwire()")
    calls = []

    def tripwire():
        """Record an actual body execution; transport must never call this."""
        calls.append("invoked")
        return 1

    scope.set_host("transport_tripwire", tripwire, visibility="runtime-public")
    other = callables.GeniaClosedFunction._from_records("f", group.records)
    other.owner = group.owner
    ref = GeniaRef()
    ref.set(group)
    cell = GeniaCell(ref)
    try:
        scope.assign("a", ref.get())
        assert scope.get("a") is group and cell.get() is group
        assert [group][0] is group and GeniaMap().put("g", group).get("g") is group
        assert GeniaOptionSome(group).value is group
        assert genia_equal(group, group) and not genia_equal(group, other)
        assert calls == []
    finally:
        cell.stop()
        cell._r25_wait_idle()


def test_missing_seam_lifecycle_state_is_classified_separately():
    """Interface diagnosis only; not claimed as invocation/reflection behavioral RED."""
    _, group = bound_group(closed=True)
    state = getattr(group, "_state", None)
    assert state in {"building", "initializing", "committed", "failed"}, (
        "MISSING INTERNAL SEAM: real closed group has no lifecycle state; "
        "state-specific invocation, failed rendering and reflection oracles are deferred"
    )
