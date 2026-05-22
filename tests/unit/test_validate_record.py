import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug


def _run(src: str):
    env = make_global_env([])
    return run_source(src, env)


def test_validate_record_required_fields_present_returns_clean_record():
    src = """
    required_name(record) = validate_required("name", record) |> then_get("name")
    required_age(record) = validate_required("age", record) |> then_get("age")

    validate_record(
      {name: "Ada", age: 36},
      {name: required_name, age: required_age}
    )
    """

    assert format_debug(_run(src)) == 'some({name: "Ada", age: 36})'


def test_validate_record_optional_missing_fields_are_omitted_from_clean_record():
    src = """
    required_name(record) = validate_required("name", record) |> then_get("name")
    optional_email(record) = validate_optional("email", record)

    validate_record(
      {name: "Ada"},
      {name: required_name, email: optional_email}
    )
    """

    assert format_debug(_run(src)) == 'some({name: "Ada"})'


def test_validate_record_missing_required_field_returns_field_diagnostics():
    src = """
    required_name(record) = validate_required("name", record) |> then_get("name")
    required_age(record) = validate_required("age", record) |> then_get("age")

    validate_record(
      {name: "Ada"},
      {name: required_name, age: required_age}
    )
    """

    assert format_debug(_run(src)) == (
        'err(record_validation_failed, {diagnostics: ['
        '{field: "age", status: error, reason: "missing required field", '
        'context: {field: "age", reason: "missing required field"}}]})'
    )


def test_validate_record_aggregates_multiple_field_errors():
    src = """
    required_name(record) = validate_required("name", record) |> then_get("name")
    required_age(record) = validate_required("age", record) |> then_get("age")

    validate_record(
      {row: 7},
      {name: required_name, age: required_age}
    )
    """

    assert format_debug(_run(src)) == (
        'err(record_validation_failed, {diagnostics: ['
        '{field: "name", status: error, reason: "missing required field", '
        'context: {row: 7, field: "name", reason: "missing required field"}}, '
        '{field: "age", status: error, reason: "missing required field", '
        'context: {row: 7, field: "age", reason: "missing required field"}}]})'
    )


def test_validate_record_supports_existing_nested_field_paths():
    src = """
    required_patient_id(record) = validate_required("patient.id", record)
    required_patient_age(record) = validate_required("patient.age", record)

    validate_record(
      {patient: {id: "p-1", age: 36}},
      {"patient.id": required_patient_id, "patient.age": required_patient_age}
    )
    """

    assert format_debug(_run(src)) == 'some({patient.id: "p-1", patient.age: 36})'


def test_validate_record_three_arg_preserves_caller_context():
    src = """
    required_name(record) = validate_required("name", record) |> then_get("name")
    required_age(record) = validate_required("age", record) |> then_get("age")

    validate_record(
      {name: "Ada"},
      {name: required_name, age: required_age},
      {source: "import-7", row: 4}
    )
    """

    assert format_debug(_run(src)) == (
        'err(record_validation_failed, {source: "import-7", row: 4, diagnostics: ['
        '{field: "age", status: error, reason: "missing required field", '
        'context: {field: "age", reason: "missing required field"}}]})'
    )


def test_validate_record_three_arg_success_preserves_caller_context():
    src = """
    required_name(record) = validate_required("name", record) |> then_get("name")
    validate_record({name: "Ada"}, {name: required_name}, {source: "batch-1"})
    """

    assert format_debug(_run(src)) == 'some({name: "Ada"}, {source: "batch-1"})'


def test_validate_record_rejects_non_record_input_as_runtime_misuse():
    src = """
    valid(_record) = some(1)
    validate_record([1, 2, 3], {field: valid})
    """

    with pytest.raises(TypeError, match="validate_record expected a record map"):
        _run(src)


def test_validate_record_rejects_non_map_validator_spec_as_runtime_misuse():
    with pytest.raises(TypeError, match="validate_record expected validators to be a map"):
        _run("validate_record({name: \"Ada\"}, [1, 2, 3])")


def test_validate_record_rejects_non_callable_validator_value_as_runtime_misuse():
    with pytest.raises(TypeError, match="validate_record expected validator for field"):
        _run("validate_record({name: \"Ada\"}, {name: 7})")


def test_validate_record_rejects_non_outcome_validator_result_as_runtime_misuse():
    src = """
    invalid(record) = record
    validate_record({name: "Ada"}, {name: invalid})
    """

    with pytest.raises(TypeError, match="validate_record validator for field .* must return an Outcome"):
        _run(src)
