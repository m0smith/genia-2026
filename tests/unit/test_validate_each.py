import pytest

from genia import make_global_env, run_source
from genia.interpreter import GeniaFlow
from genia.utf8 import format_debug
from genia.values import GeniaOptionSome


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


def test_validate_each_preserves_upstream_err_without_calling_validator():
    env = make_global_env([])

    def fail_if_called(value):
        raise AssertionError(f"validator should not receive upstream err: {value!r}")

    env.set("fail_if_called", fail_if_called)

    result = run_source(
        """
        validate_each([
          err("invalid json", {line: 2, raw: "{bad}"})
        ], fail_if_called)
        """,
        env,
    )

    assert format_debug(result) == '[err("invalid json", {line: 2, raw: "{bad}"})]'


def test_validate_each_preserves_upstream_none_without_calling_validator():
    env = make_global_env([])

    def fail_if_called(value):
        raise AssertionError(f"validator should not receive upstream none: {value!r}")

    env.set("fail_if_called", fail_if_called)

    result = run_source(
        """
        validate_each([
          none("blank line", {line: 3, raw: ""})
        ], fail_if_called)
        """,
        env,
    )

    assert format_debug(result) == '[none("blank line", {line: 3, raw: ""})]'


def test_validate_each_unwraps_upstream_some_before_validation():
    src = """
    validator(record) = (
      ({id: 1}) -> some({id: record("id"), checked: true}) |
      (_) -> err(quote(validator_received_wrapper), {received: display(record)})
    )

    validate_each([
      some({id: 1})
    ], validator)
    """

    assert format_debug(_run(src)) == "[some({id: 1, checked: true})]"


def test_validate_each_preserves_mixed_upstream_outcome_order():
    src = """
    validator(record) = (
      ({id: id}) -> some({id: id, valid: true}) |
      (_) -> err(quote(validator_received_wrapper), {received: display(record)})
    )

    validate_each([
      some({id: 1}),
      err("invalid json", {line: 2}),
      none("blank line", {line: 3}),
      some({id: 4})
    ], validator)
    """

    assert format_debug(_run(src)) == (
        '[some({id: 1, valid: true}), '
        'err("invalid json", {line: 2}), '
        'none("blank line", {line: 3}), '
        'some({id: 4, valid: true})]'
    )


def test_validate_each_plain_record_validation_still_works():
    src = """
    validator(record) = (
      ({id: id}) -> some({id: id, valid: true}) |
      (_) -> err(quote(invalid_record), {received: display(record)})
    )

    validate_each([{id: 7}], validator)
    """

    assert format_debug(_run(src)) == "[some({id: 7, valid: true})]"


def test_validate_each_rejects_non_callable_validator():
    with pytest.raises(TypeError, match="validate_each expected validator to be callable"):
        _run("validate_each([{id: 1}], 7)")


def test_validate_each_rejects_non_list_non_flow_source():
    with pytest.raises(TypeError, match="validate_each expected a list or Flow source"):
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


def test_validate_each_flow_returns_flow_and_preserves_ordered_outcomes():
    src = """
    next(n) = n + 1
    validator(n) = some(n * 10)

    source = evolve(1, next) |> take(3)
    validate_each(source, validator)
    """

    result = _run(src)

    assert isinstance(result, GeniaFlow)
    assert format_debug(list(result.consume())) == "[some(10), some(20), some(30)]"


def test_validate_each_flow_preserves_some_none_and_err_outcomes():
    src = """
    next(n) = n + 1
    validator(n) = (
      0 -> some({id: n}) |
      1 -> none("inactive", {id: n}) |
      2 -> err(quote(invalid_record), {id: n})
    )

    source = evolve(0, next) |> take(3)
    collect(validate_each(source, validator))
    """

    assert format_debug(_run(src)) == (
        '[some({id: 0}), '
        'none("inactive", {id: 1}), '
        "err(invalid_record, {id: 2})]"
    )


def test_validate_each_flow_composes_with_collect_validated():
    src = """
    next(n) = n + 1
    validator(n) = (
      0 -> some({id: n}) |
      1 -> none("inactive", {id: n}) |
      2 -> err(quote(invalid_record), {id: n})
    )

    source = evolve(0, next) |> take(3)
    collect_validated(validate_each(source, validator))
    """

    assert format_debug(_run(src)) == (
        "{clean: [{id: 0}], diagnostics: ["
        '{index: 1, kind: skipped, reason: "inactive", context: some({id: 1})}, '
        "{index: 2, kind: error, reason: invalid_record, context: some({id: 2})}]}"
    )


def test_validate_each_flow_is_lazy_until_consumed():
    env = make_global_env([])
    state = {"pulled": 0, "validated": 0}

    def counted_source():
        def iterator():
            for value in [1, 2, 3]:
                state["pulled"] += 1
                yield value

        return GeniaFlow(iterator, label="counted")

    def validator(value):
        state["validated"] += 1
        return GeniaOptionSome(value * 10)

    env.set("counted_source", counted_source)
    env.set("validator", validator)

    result = run_source("validate_each(counted_source(), validator)", env)

    assert isinstance(result, GeniaFlow)
    assert state == {"pulled": 0, "validated": 0}

    items = iter(result.consume())
    assert format_debug(next(items)) == "some(10)"
    assert state == {"pulled": 1, "validated": 1}

    assert format_debug(list(items)) == "[some(20), some(30)]"
    assert state == {"pulled": 3, "validated": 3}


def test_validate_each_flow_non_outcome_validator_result_fails_when_consumed():
    env = make_global_env([])
    state = {"validated": 0}

    def counted_source():
        return GeniaFlow(lambda: iter([1]), label="counted")

    def invalid(value):
        state["validated"] += 1
        return value

    env.set("counted_source", counted_source)
    env.set("invalid", invalid)

    result = run_source("validate_each(counted_source(), invalid)", env)

    assert isinstance(result, GeniaFlow)
    assert state == {"validated": 0}
    with pytest.raises(TypeError, match="validate_each validator must return an Outcome"):
        list(result.consume())
    assert state == {"validated": 1}


def test_validate_each_flow_output_is_single_use():
    src = """
    next(n) = n + 1
    validator(n) = some(n)

    source = evolve(1, next) |> take(2)
    validate_each(source, validator)
    """

    result = _run(src)

    assert isinstance(result, GeniaFlow)
    assert format_debug(list(result.consume())) == "[some(1), some(2)]"
    with pytest.raises(RuntimeError, match="Flow has already been consumed"):
        list(result.consume())
