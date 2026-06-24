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


def test_cleanup_normalizes_contract_safe_defaults_and_explicit_safe_values():
    empty_policy_plan = _record(
        name=symbol("test_lifecycle"),
        phases=[_phase("body", "lifecycle_run_body")],
        cleanup=_record(),
    )

    default_cleanup = _normalize(empty_policy_plan).get("cleanup")

    assert default_cleanup.get("entered_scope_cleanup") is True
    assert default_cleanup.get("unentered_scope_cleanup") is False
    assert default_cleanup.get("nested_order") == symbol("inner_to_outer")
    assert default_cleanup.get("same_scope_order") == symbol("reverse_source_order")
    assert default_cleanup.get("continue_after_cleanup_failure") is True
    assert default_cleanup.get("record_multiple_failures") is True

    explicit_policy_plan = _record(
        name=symbol("test_lifecycle"),
        phases=[_phase("body", "lifecycle_run_body")],
        cleanup=_record(
            entered_scope_cleanup=True,
            unentered_scope_cleanup=False,
            nested_order=symbol("inner_to_outer"),
            same_scope_order=symbol("registration_reverse_order"),
            continue_after_cleanup_failure=True,
            record_multiple_failures=True,
        ),
    )

    cleanup = _normalize(explicit_policy_plan).get("cleanup")

    assert cleanup.get("entered_scope_cleanup") is True
    assert cleanup.get("unentered_scope_cleanup") is False
    assert cleanup.get("nested_order") == symbol("inner_to_outer")
    assert cleanup.get("same_scope_order") == symbol("registration_reverse_order")
    assert cleanup.get("continue_after_cleanup_failure") is True
    assert cleanup.get("record_multiple_failures") is True


@pytest.mark.parametrize(
    ("cleanup", "expected_message"),
    [
        (
            _record(unentered_scope_cleanup=True),
            r"invalid lifecycle plan at plan\.cleanup\.unentered_scope_cleanup: unentered scope cleanup is not supported",
        ),
        (
            _record(nested_order=symbol("outer_to_inner")),
            r"invalid lifecycle plan at plan\.cleanup\.nested_order: unsupported cleanup order outer_to_inner",
        ),
        (
            _record(same_scope_order=symbol("source_order")),
            r"invalid lifecycle plan at plan\.cleanup\.same_scope_order: unsupported cleanup order source_order",
        ),
        (
            _record(entered_scope_cleanup=symbol("yes")),
            r"invalid lifecycle plan at plan\.cleanup\.entered_scope_cleanup: expected boolean, got symbol",
        ),
        (
            _record(entered_scope_cleanup=False),
            r"invalid lifecycle plan at plan\.cleanup\.entered_scope_cleanup: entered scopes must remain cleanup eligible",
        ),
    ],
)
def test_cleanup_rejects_unsafe_or_nonportable_policy_values(cleanup, expected_message):
    plan = _record(
        name=symbol("test_lifecycle"),
        phases=[_phase("body", "lifecycle_run_body")],
        cleanup=cleanup,
    )

    _assert_invalid(plan, expected_message)


def test_failure_policy_normalizes_contract_safe_defaults_and_explicit_safe_values():
    empty_policy_plan = _record(
        name=symbol("test_lifecycle"),
        phases=[_phase("body", "lifecycle_run_body")],
        failure_policy=_record(),
    )

    default_failure_policy = _normalize(empty_policy_plan).get("failure_policy")

    assert default_failure_policy.get("primary_failure") == symbol("first_non_cleanup")
    assert default_failure_policy.get("cleanup_failure") == symbol("recorded_secondary")
    assert default_failure_policy.get("cleanup_only_status") == symbol("failed")
    assert default_failure_policy.get("normal_failure_continuation") == symbol(
        "abort_to_cleanup"
    )
    assert default_failure_policy.get("preserve_primary_failure") is True
    assert default_failure_policy.get("preserve_cleanup_failures") is True

    explicit_policy_plan = _record(
        name=symbol("test_lifecycle"),
        phases=[_phase("body", "lifecycle_run_body")],
        failure_policy=_record(
            primary_failure=symbol("first_non_cleanup"),
            cleanup_failure=symbol("recorded_secondary"),
            cleanup_only_status=symbol("failed"),
            normal_failure_continuation=symbol("abort_to_cleanup"),
            preserve_primary_failure=True,
            preserve_cleanup_failures=True,
        ),
    )

    failure_policy = _normalize(explicit_policy_plan).get("failure_policy")

    assert failure_policy.get("primary_failure") == symbol("first_non_cleanup")
    assert failure_policy.get("cleanup_failure") == symbol("recorded_secondary")
    assert failure_policy.get("cleanup_only_status") == symbol("failed")
    assert failure_policy.get("normal_failure_continuation") == symbol(
        "abort_to_cleanup"
    )
    assert failure_policy.get("preserve_primary_failure") is True
    assert failure_policy.get("preserve_cleanup_failures") is True


@pytest.mark.parametrize(
    ("failure_policy", "expected_message"),
    [
        (
            _record(preserve_primary_failure=False),
            r"invalid lifecycle plan at plan\.failure_policy\.preserve_primary_failure: primary failure must be preserved",
        ),
        (
            _record(preserve_cleanup_failures=False),
            r"invalid lifecycle plan at plan\.failure_policy\.preserve_cleanup_failures: cleanup failures must be preserved",
        ),
        (
            _record(primary_failure=symbol("last_failure")),
            r"invalid lifecycle plan at plan\.failure_policy\.primary_failure: unsupported failure policy last_failure",
        ),
        (
            _record(cleanup_failure=symbol("overwrite_primary")),
            r"invalid lifecycle plan at plan\.failure_policy\.cleanup_failure: cleanup failure must not overwrite primary failure",
        ),
        (
            _record(normal_failure_continuation=symbol("continue_normal")),
            r"invalid lifecycle plan at plan\.failure_policy\.normal_failure_continuation: unsupported failure policy continue_normal",
        ),
        (
            _record(cleanup_failure=symbol("swallow")),
            r"invalid lifecycle plan at plan\.failure_policy\.cleanup_failure: cleanup failures must be preserved",
        ),
    ],
)
def test_failure_rejects_policies_that_drop_or_overwrite_failures(
    failure_policy,
    expected_message,
):
    plan = _record(
        name=symbol("test_lifecycle"),
        phases=[_phase("body", "lifecycle_run_body")],
        failure_policy=failure_policy,
    )

    _assert_invalid(plan, expected_message)


def test_result_policy_normalizes_deterministic_defaults_and_explicit_safe_values():
    empty_policy_plan = _record(
        name=symbol("test_lifecycle"),
        phases=[_phase("body", "lifecycle_run_body")],
        result_policy=_record(),
    )

    default_result_policy = _normalize(empty_policy_plan).get("result_policy")

    assert default_result_policy.get("failure_order") == symbol("observed_order")
    assert default_result_policy.get("include_phase") is True
    assert default_result_policy.get("include_scope") is True
    assert default_result_policy.get("include_role") is True
    assert default_result_policy.get("include_source_location") is True

    explicit_policy_plan = _record(
        name=symbol("test_lifecycle"),
        phases=[_phase("body", "lifecycle_run_body")],
        result_policy=_record(
            failure_order=symbol("observed_order"),
            include_phase=True,
            include_scope=True,
            include_role=True,
            include_source_location=True,
        ),
    )

    result_policy = _normalize(explicit_policy_plan).get("result_policy")

    assert result_policy.get("failure_order") == symbol("observed_order")
    assert result_policy.get("include_phase") is True
    assert result_policy.get("include_scope") is True
    assert result_policy.get("include_role") is True
    assert result_policy.get("include_source_location") is True


def test_result_policy_preserves_explicit_all_false_include_flags():
    plan = _record(
        name=symbol("test_lifecycle"),
        phases=[_phase("body", "lifecycle_run_body")],
        result_policy=_record(
            include_phase=False,
            include_scope=False,
            include_role=False,
            include_source_location=False,
        ),
    )

    result_policy = _normalize(plan).get("result_policy")

    assert result_policy.get("include_phase") is False
    assert result_policy.get("include_scope") is False
    assert result_policy.get("include_role") is False
    assert result_policy.get("include_source_location") is False


def test_result_policy_preserves_mixed_explicit_include_flags_independently():
    plan = _record(
        name=symbol("test_lifecycle"),
        phases=[_phase("body", "lifecycle_run_body")],
        result_policy=_record(
            include_phase=False,
            include_scope=True,
            include_role=False,
            include_source_location=True,
        ),
    )

    result_policy = _normalize(plan).get("result_policy")

    assert result_policy.get("include_phase") is False
    assert result_policy.get("include_scope") is True
    assert result_policy.get("include_role") is False
    assert result_policy.get("include_source_location") is True


def test_result_policy_defaults_omitted_include_flags_after_single_explicit_false():
    plan = _record(
        name=symbol("test_lifecycle"),
        phases=[_phase("body", "lifecycle_run_body")],
        result_policy=_record(include_phase=False),
    )

    result_policy = _normalize(plan).get("result_policy")

    assert result_policy.get("include_phase") is False
    assert result_policy.get("include_scope") is True
    assert result_policy.get("include_role") is True
    assert result_policy.get("include_source_location") is True


@pytest.mark.parametrize(
    ("result_policy", "expected_message"),
    [
        (
            _record(failure_order=symbol("cleanup_first")),
            r"invalid lifecycle plan at plan\.result_policy\.failure_order: unsupported failure order cleanup_first",
        ),
        (
            _record(include_phase=symbol("yes")),
            r"invalid lifecycle plan at plan\.result_policy\.include_phase: expected boolean, got symbol",
        ),
        (
            _record(include_scope=symbol("yes")),
            r"invalid lifecycle plan at plan\.result_policy\.include_scope: expected boolean, got symbol",
        ),
        (
            _record(include_role=symbol("yes")),
            r"invalid lifecycle plan at plan\.result_policy\.include_role: expected boolean, got symbol",
        ),
        (
            _record(include_source_location=symbol("yes")),
            r"invalid lifecycle plan at plan\.result_policy\.include_source_location: expected boolean, got symbol",
        ),
    ],
)
def test_result_rejects_unsupported_or_nonportable_policy_values(
    result_policy,
    expected_message,
):
    plan = _record(
        name=symbol("test_lifecycle"),
        phases=[_phase("body", "lifecycle_run_body")],
        result_policy=result_policy,
    )

    _assert_invalid(plan, expected_message)
