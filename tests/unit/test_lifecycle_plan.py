import importlib

import pytest

from genia.values import GeniaMap, symbol


def _lifecycle_plan_module():
    return importlib.import_module("genia.lifecycle_plan")


def _record(**fields):
    record = GeniaMap()
    for key, value in fields.items():
        record = record.put(key, value)
    return record


def _phase(name, action, **fields):
    return _record(name=symbol(name), action=symbol(action), **fields)


def _normalize(plan):
    return _lifecycle_plan_module().normalize_lifecycle_plan(plan)


def _assert_invalid(plan, expected_message):
    lifecycle_plan = _lifecycle_plan_module()
    with pytest.raises(ValueError, match=expected_message):
        lifecycle_plan.normalize_lifecycle_plan(plan)


def test_normalize_accepts_valid_lifecycle_plan_shape_and_defaults_always():
    plan = _record(
        name=symbol("command_mode"),
        phases=[
            _phase(
                "init_context",
                "lifecycle_init_context",
                scope=symbol("execution"),
            ),
            _phase(
                "load_command_source",
                "lifecycle_load_command_source",
                scope=symbol("source"),
            ),
            _phase(
                "finalize",
                "lifecycle_finalize_context",
                scope=symbol("execution"),
                always=True,
            ),
        ],
    )

    normalized = _normalize(plan)

    assert normalized.get("name") == symbol("command_mode")
    phases = normalized.get("phases")
    assert [phase.get("name") for phase in phases] == [
        symbol("init_context"),
        symbol("load_command_source"),
        symbol("finalize"),
    ]
    assert [phase.get("action") for phase in phases] == [
        symbol("lifecycle_init_context"),
        symbol("lifecycle_load_command_source"),
        symbol("lifecycle_finalize_context"),
    ]
    assert [phase.get("scope") for phase in phases] == [
        symbol("execution"),
        symbol("source"),
        symbol("execution"),
    ]
    assert [phase.get("always") for phase in phases] == [False, False, True]


def test_normalize_preserves_phase_order_exactly_as_declared():
    plan = _record(
        name=symbol("pipe_mode"),
        phases=[
            _phase("consume_pipeline", "lifecycle_consume_pipeline"),
            _phase("bind_stdin_source", "lifecycle_bind_stdin_source"),
            _phase("init_context", "lifecycle_init_context"),
        ],
    )

    normalized = _normalize(plan)

    assert [phase.get("name") for phase in normalized.get("phases")] == [
        symbol("consume_pipeline"),
        symbol("bind_stdin_source"),
        symbol("init_context"),
    ]


def test_validate_accepts_minimal_plan_and_phase_without_execution():
    calls = []

    def action_that_must_not_be_called():
        calls.append("called")

    plan = _record(
        name=symbol("file_mode"),
        phases=[
            _record(
                name=symbol("load_file_source"),
                action=symbol("lifecycle_load_file_source"),
                metadata=_record(host_callable=action_that_must_not_be_called),
            )
        ],
    )

    lifecycle_plan = _lifecycle_plan_module()

    assert lifecycle_plan.validate_lifecycle_plan(plan) is None
    assert calls == []


@pytest.mark.parametrize(
    ("plan", "expected_message"),
    [
        ([], r"invalid lifecycle plan at plan: expected map, got list"),
        (_record(phases=[]), r"invalid lifecycle plan at plan\.name: missing required field"),
        (
            _record(name=symbol("command_mode")),
            r"invalid lifecycle plan at plan\.phases: missing required field",
        ),
        (
            _record(name=symbol("command_mode"), phases=symbol("not_a_list")),
            r"invalid lifecycle plan at plan\.phases: expected list, got symbol",
        ),
    ],
)
def test_rejects_invalid_plan_shape_with_path_diagnostics(plan, expected_message):
    _assert_invalid(plan, expected_message)


@pytest.mark.parametrize(
    ("phase", "expected_message"),
    [
        (symbol("not_a_phase_record"), r"invalid lifecycle plan at plan\.phases\[0\]: expected map, got symbol"),
        (
            _record(action=symbol("lifecycle_init_context")),
            r"invalid lifecycle plan at plan\.phases\[0\]\.name: missing required field",
        ),
        (
            _record(name=symbol("init_context")),
            r"invalid lifecycle plan at plan\.phases\[0\]\.action: missing required field",
        ),
        (
            _phase("init_context", "lifecycle_init_context", always=symbol("yes")),
            r"invalid lifecycle plan at plan\.phases\[0\]\.always: expected boolean, got symbol",
        ),
    ],
)
def test_rejects_invalid_phase_shape_with_path_diagnostics(phase, expected_message):
    plan = _record(name=symbol("command_mode"), phases=[phase])

    _assert_invalid(plan, expected_message)


def test_rejects_duplicate_phase_names_with_deterministic_diagnostic():
    plan = _record(
        name=symbol("command_mode"),
        phases=[
            _phase("finalize", "lifecycle_finalize_source"),
            _phase("finalize", "lifecycle_finalize_context"),
        ],
    )

    _assert_invalid(
        plan,
        r"invalid lifecycle plan at plan\.phases\[1\]\.name: duplicate phase name finalize",
    )


def test_rejects_callable_phase_action_as_nonportable_behavior():
    def host_callable():
        raise AssertionError("lifecycle validation must not call phase actions")

    plan = _record(
        name=symbol("command_mode"),
        phases=[
            _record(
                name=symbol("init_context"),
                action=host_callable,
                scope=symbol("execution"),
            )
        ],
    )

    _assert_invalid(
        plan,
        r"invalid lifecycle plan at plan\.phases\[0\]\.action: expected identifier, got function",
    )
