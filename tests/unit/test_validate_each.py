import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug


def _run(src: str):
    env = make_global_env([])
    return run_source(src, env)


def test_validate_each_returns_one_outcome_per_list_item():
    src = """
    valid(record) = some(record)

    validate_each([
      {id: 1, name: "Ada"},
      {id: 2, name: "Linus"},
      {id: 3, name: "Grace"}
    ], valid)
    """

    result = _run(src)

    assert isinstance(result, list)
    assert len(result) == 3
    assert format_debug(result) == (
        '[some({id: 1, name: "Ada"}), '
        'some({id: 2, name: "Linus"}), '
        'some({id: 3, name: "Grace"})]'
    )


def test_validate_each_preserves_err_outcomes():
    src = """
    validator(record) = (
      ({id: 1}) -> some(record) |
      ({id: 2}) -> err(quote(invalid_record), {id: record("id")})
    )

    validate_each([{id: 1}, {id: 2}, {id: 1}], validator)
    """

    assert format_debug(_run(src)) == (
        "[some({id: 1}), "
        "err(invalid_record, {id: 2}), "
        "some({id: 1})]"
    )


def test_validate_each_preserves_none_outcomes():
    src = """
    validator(record) = (
      ({active: true}) -> some(record) |
      ({active: false}) -> none("inactive", {id: record("id")})
    )

    validate_each([
      {id: 1, active: true},
      {id: 2, active: false},
      {id: 3, active: true}
    ], validator)
    """

    assert format_debug(_run(src)) == (
        '[some({id: 1, active: true}), '
        'none("inactive", {id: 2}), '
        'some({id: 3, active: true})]'
    )


def test_validate_each_rejects_non_callable_validator():
    with pytest.raises(TypeError, match="validate_each expected validator to be callable"):
        _run("validate_each([{id: 1}], 7)")


def test_validate_each_rejects_non_list_source():
    with pytest.raises(TypeError, match="validate_each expected a list source"):
        _run("validate_each({a: 1}, (record) -> some(record))")


def test_validate_each_rejects_non_outcome_validator_result():
    src = """
    invalid(record) = record("id") == 1
    validate_each([{id: 1}], invalid)
    """

    with pytest.raises(TypeError, match="validate_each validator must return an Outcome"):
        _run(src)


def test_validate_each_composes_with_collect_validated():
    src = """
    validator(record) = (
      ({id: 1}) -> some(record) |
      ({id: 2}) -> none("inactive", {id: record("id")}) |
      ({id: 3}) -> err(quote(invalid_record), {id: record("id")})
    )

    collect_validated(validate_each([{id: 1}, {id: 2}, {id: 3}], validator))
    """

    assert format_debug(_run(src)) == (
        "{clean: [{id: 1}], diagnostics: ["
        '{index: 1, kind: skipped, reason: "inactive", context: some({id: 2})}, '
        "{index: 2, kind: error, reason: invalid_record, context: some({id: 3})}]}"
    )


def test_validate_each_composes_with_validate_record():
    src = """
    required_name(record) = validate_required("name", record) |> then_get("name")
    person(record) = validate_record(record, {name: required_name})

    validate_each([{name: "Ada"}, {row: 2}, {name: "Grace"}], person)
    """

    assert format_debug(_run(src)) == (
        '[some({name: "Ada"}), '
        'err(record_validation_failed, {diagnostics: ['
        '{field: "name", status: error, reason: "missing required field", '
        'context: {row: 2, field: "name", reason: "missing required field"}}]}), '
        'some({name: "Grace"})]'
    )
