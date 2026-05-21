import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug


def _run(src: str):
    env = make_global_env([])
    return run_source(src, env)


def test_validate_optional_missing_field_returns_structured_none():
    result = _run('validate_optional("nickname", {name: "Ada"})')

    assert format_debug(result) == 'none({field: "nickname", reason: missing_optional_field})'


def test_validate_optional_present_field_without_validator_returns_some_with_context():
    result = _run('validate_optional("nickname", {nickname: "Countess"})')

    assert format_debug(result) == 'some("Countess", {field: "nickname"})'


def test_validate_optional_preserves_validator_some_outcome():
    src = """
    valid(value) = some(value + 1, {source: quote(validator)})
    validate_optional("age", {age: 41}, valid)
    """

    assert format_debug(_run(src)) == "some(42, {source: validator})"


def test_validate_optional_preserves_validator_err_outcome():
    src = """
    invalid(value) = err(quote(bad_age), {actual: value})
    validate_optional("age", {age: "old"}, invalid)
    """

    assert format_debug(_run(src)) == 'err(bad_age, {actual: "old"})'


def test_validate_optional_validator_none_becomes_err_for_present_field():
    src = """
    ambiguous(value) = none("blank", {actual: value})
    validate_optional("nickname", {nickname: ""}, ambiguous)
    """

    assert (
        format_debug(_run(src))
        == 'err(optional_field_validator_returned_none, {field: "nickname", validator_result: none("blank", {actual: ""})})'
    )


def test_validate_optional_treats_falsey_values_as_present():
    src = """
    [
      validate_optional("flag", {flag: false}),
      validate_optional("count", {count: 0}),
      validate_optional("text", {text: ""}),
      validate_optional("items", {items: []}),
      validate_optional("meta", {meta: {}}),
      validate_optional("maybe", {maybe: none("nil")}),
      validate_optional("problem", {problem: err(quote(bad))})
    ]
    """

    assert format_debug(_run(src)) == (
        '[some(false, {field: "flag"}), '
        'some(0, {field: "count"}), '
        'some("", {field: "text"}), '
        'some([], {field: "items"}), '
        'some({}, {field: "meta"}), '
        'some(none("nil"), {field: "maybe"}), '
        'some(err(bad), {field: "problem"})]'
    )


def test_validate_optional_rejects_non_map_record():
    with pytest.raises(TypeError, match="validate_optional expected a record map"):
        _run('validate_optional("age", [1, 2, 3])')


def test_validate_optional_rejects_non_callable_validator():
    with pytest.raises(TypeError, match="validate_optional expected validator to be callable"):
        _run('validate_optional("age", {age: 42}, 7)')


def test_validate_optional_rejects_validator_returning_non_outcome():
    src = """
    invalid(value) = value
    validate_optional("age", {age: 42}, invalid)
    """

    with pytest.raises(TypeError, match="validate_optional validator must return an Outcome"):
        _run(src)


def test_validate_optional_wrong_arity_is_runtime_misuse():
    with pytest.raises(TypeError, match="validate_optional"):
        _run('validate_optional("age")')


def test_validate_required_missing_field_behavior_remains_unchanged():
    result = _run('validate_required("age", {row: 2, name: "Linus"})')

    assert (
        format_debug(result)
        == 'err("missing required field", {row: 2, field: "age", reason: "missing required field"})'
    )


def test_validate_field_flat_diagnostic_behavior_remains_unchanged():
    result = _run(
        'validate_field("age", (value) -> value == 37, "age must equal 37", {row: 3, age: "old"})'
    )

    assert (
        format_debug(result)
        == 'err("invalid field", {row: 3, field: "age", expected: "age must equal 37", actual: "old", reason: "invalid field"})'
    )


def test_validate_field_preserves_one_level_nested_path():
    result = _run(
        'validate_field("patient.name", (value) -> value != "", "name required", {patient: {name: ""}})'
    )

    assert (
        format_debug(result)
        == 'err("invalid field", {field: "patient.name", expected: "name required", actual: "", reason: "invalid field"})'
    )


def test_validate_field_preserves_two_level_nested_path():
    result = _run(
        'validate_field("patient.address.zip", (value) -> value == "02139", "valid zip", {patient: {address: {zip: "bad"}}})'
    )

    assert (
        format_debug(result)
        == 'err("invalid field", {field: "patient.address.zip", expected: "valid zip", actual: "bad", reason: "invalid field"})'
    )


def test_validate_record_multiple_nested_failures_keep_distinct_paths():
    src = """
    collect_validated([
      validate_field("patient.name", (value) -> value != "", "name required", {patient: {name: ""}}),
      validate_field("patient.birth_date", (value) -> value != "", "birth date required", {patient: {birth_date: ""}}),
      validate_field("patient.address.zip", (value) -> value == "02139", "valid zip", {patient: {address: {zip: "bad"}}})
    ])
    """

    assert format_debug(_run(src)) == (
        '{clean: [], diagnostics: ['
        '{index: 0, kind: error, reason: "invalid field", context: some({field: "patient.name", expected: "name required", actual: "", reason: "invalid field"})}, '
        '{index: 1, kind: error, reason: "invalid field", context: some({field: "patient.birth_date", expected: "birth date required", actual: "", reason: "invalid field"})}, '
        '{index: 2, kind: error, reason: "invalid field", context: some({field: "patient.address.zip", expected: "valid zip", actual: "bad", reason: "invalid field"})}]}'
    )


def test_validate_required_missing_nested_field_uses_full_path():
    result = _run('validate_required("patient.address.zip", {patient: {address: {city: "Cambridge"}}})')

    assert (
        format_debug(result)
        == 'err("missing required field", {field: "patient.address.zip", reason: "missing required field"})'
    )


def test_validate_optional_missing_nested_field_uses_full_path():
    result = _run('validate_optional("patient.nickname", {patient: {name: "Ada"}})')

    assert format_debug(result) == 'none({field: "patient.nickname", reason: missing_optional_field})'


def test_validate_optional_nested_present_without_validator_uses_full_path():
    result = _run('validate_optional("patient.name", {patient: {name: "Ada"}})')

    assert format_debug(result) == 'some("Ada", {field: "patient.name"})'


def test_validate_optional_nested_validator_err_uses_full_path_when_context_has_field():
    src = """
    invalid(value) = err(quote(bad_name), {field: "name", actual: value})
    validate_optional("patient.name", {patient: {name: ""}}, invalid)
    """

    assert format_debug(_run(src)) == 'err(bad_name, {field: "patient.name", actual: ""})'


def test_validate_optional_nested_validator_none_uses_full_path():
    src = """
    ambiguous(value) = none("blank", {actual: value})
    validate_optional("patient.nickname", {patient: {nickname: ""}}, ambiguous)
    """

    assert (
        format_debug(_run(src))
        == 'err(optional_field_validator_returned_none, {field: "patient.nickname", validator_result: none("blank", {actual: ""})})'
    )


def test_collect_validated_behavior_remains_unchanged():
    src = """
    collect_validated([
      some({id: 1}),
      none("inactive", {id: 2}),
      err("bad", {id: 3})
    ])
    """

    assert format_debug(_run(src)) == (
        '{clean: [{id: 1}], diagnostics: ['
        '{index: 1, kind: skipped, reason: "inactive", context: some({id: 2})}, '
        '{index: 2, kind: error, reason: "bad", context: some({id: 3})}]}'
    )
