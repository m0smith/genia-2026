"""Focused invariants for E15-2 (#729) default_field that shared eval specs can't express."""

from genia import make_global_env, run_source
from genia.values import GeniaMap, GeniaOptionSome


def _run(source: str):
    return run_source(source, make_global_env([]), filename="<test>")


def test_zero_default_success_preserves_original_subject_identity():
    result = _run(
        "Person = exact_shape({name: refinement((x) -> x != \"\")})\n"
        "record = {name: \"Ada\"}\n"
        "[Person(record), record]"
    )
    assert isinstance(result, list)
    outcome, record = result
    assert isinstance(outcome, GeniaOptionSome)
    assert outcome.value is record


def test_missing_field_default_inserted_returns_new_map_not_original():
    result = _run(
        "Person = exact_shape({name: refinement((x) -> x != \"\"), age: default_field(0, refinement((x) -> x >= 0))})\n"
        "record = {name: \"Ada\"}\n"
        "[Person(record), record]"
    )
    outcome, record = result
    assert isinstance(outcome, GeniaOptionSome)
    assert outcome.value is not record
    assert outcome.value.get("age") == 0
    assert outcome.value.get("name") == "Ada"
    assert not record.has("age")


def test_default_value_itself_validated_and_failure_propagates():
    result = _run(
        "Person = exact_shape({age: default_field(-1, refinement((x) -> x >= 0))})\n"
        "Person({})"
    )
    from genia.values import GeniaOptionNone

    assert isinstance(result, GeniaOptionNone)
    assert result.reason == "refinement-mismatch"


def test_represented_default_never_appears_in_description():
    result = _run(
        "Person = exact_shape({meta: default_field(represent(\"json\", {a: 1}), refinement((x) -> true))})\n"
        "template_description(Person)"
    )
    assert isinstance(result, GeniaOptionSome)
    description = result.value
    assert isinstance(description, GeniaMap)
    fields = description.get("fields")
    field_desc = fields.get("meta")
    rendered = repr(field_desc.get("has_default"))
    assert "json" not in rendered
    assert field_desc.get("has_default") is True
