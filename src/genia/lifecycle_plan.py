"""Lifecycle plan data-shape validation for the Python reference host."""

from __future__ import annotations

from typing import Any

from .values import GeniaMap, GeniaSymbol, _runtime_type_name


_PLAN = "plan"


def validate_lifecycle_plan(value: Any) -> None:
    """Validate lifecycle plan data without executing lifecycle behavior."""

    normalize_lifecycle_plan(value)
    return None


def normalize_lifecycle_plan(value: Any) -> GeniaMap:
    """Return a normalized lifecycle plan map or raise a deterministic error."""

    if not isinstance(value, GeniaMap):
        _fail(_PLAN, "expected map", value)

    name = _required(value, "name", _PLAN)
    _require_identifier(name, f"{_PLAN}.name")

    phases = _required(value, "phases", _PLAN)
    if not isinstance(phases, list):
        _fail(f"{_PLAN}.phases", "expected list", phases)

    normalized_phases: list[GeniaMap] = []
    seen_phase_names: set[GeniaSymbol] = set()
    for index, phase in enumerate(phases):
        normalized_phase = _normalize_phase(phase, index, seen_phase_names)
        normalized_phases.append(normalized_phase)

    normalized = GeniaMap().put("name", name).put("phases", normalized_phases)
    for optional_field in ("description", "metadata"):
        if value.has(optional_field):
            optional_value = value.get(optional_field)
            _validate_optional_plan_field(optional_field, optional_value)
            normalized = normalized.put(optional_field, optional_value)
    if value.has("cleanup"):
        normalized = normalized.put(
            "cleanup",
            _normalize_cleanup_policy(value.get("cleanup")),
        )
    if value.has("failure_policy"):
        normalized = normalized.put(
            "failure_policy",
            _normalize_failure_policy(value.get("failure_policy")),
        )
    if value.has("result_policy"):
        normalized = normalized.put(
            "result_policy",
            _normalize_result_policy(value.get("result_policy")),
        )
    return normalized


def _normalize_phase(
    value: Any,
    index: int,
    seen_phase_names: set[GeniaSymbol],
) -> GeniaMap:
    path = f"{_PLAN}.phases[{index}]"
    if not isinstance(value, GeniaMap):
        _fail(path, "expected map", value)

    name = _required(value, "name", path)
    _require_identifier(name, f"{path}.name")
    if name in seen_phase_names:
        raise ValueError(
            f"invalid lifecycle plan at {path}.name: duplicate phase name {name}"
        )
    seen_phase_names.add(name)

    action = _required(value, "action", path)
    _require_identifier(action, f"{path}.action")

    normalized = GeniaMap().put("name", name).put("action", action)
    for optional_field in ("scope", "description", "metadata"):
        if value.has(optional_field):
            optional_value = value.get(optional_field)
            _validate_optional_phase_field(optional_field, optional_value, path)
            normalized = normalized.put(optional_field, optional_value)

    if value.has("always"):
        always = value.get("always")
        if not isinstance(always, bool):
            _fail(f"{path}.always", "expected boolean", always)
    else:
        always = False
    return normalized.put("always", always)


def _required(record: GeniaMap, field: str, path: str) -> Any:
    if not record.has(field):
        raise ValueError(
            f"invalid lifecycle plan at {path}.{field}: missing required field"
        )
    return record.get(field)


def _require_identifier(value: Any, path: str) -> None:
    if not isinstance(value, GeniaSymbol):
        _fail(path, "expected identifier", value)


def _validate_optional_plan_field(field: str, value: Any) -> None:
    path = f"{_PLAN}.{field}"
    if field == "description" and not isinstance(value, str):
        _fail(path, "expected string", value)
    if field == "metadata" and not isinstance(value, GeniaMap):
        _fail(path, "expected map", value)


def _validate_optional_phase_field(field: str, value: Any, phase_path: str) -> None:
    path = f"{phase_path}.{field}"
    if field == "scope":
        _require_identifier(value, path)
    if field == "description" and not isinstance(value, str):
        _fail(path, "expected string", value)
    if field == "metadata" and not isinstance(value, GeniaMap):
        _fail(path, "expected map", value)


def _normalize_cleanup_policy(value: Any) -> GeniaMap:
    path = f"{_PLAN}.cleanup"
    if not isinstance(value, GeniaMap):
        _fail(path, "expected map", value)

    normalized = (
        GeniaMap()
        .put("entered_scope_cleanup", True)
        .put("unentered_scope_cleanup", False)
        .put("nested_order", _symbol("inner_to_outer"))
        .put("same_scope_order", _symbol("reverse_source_order"))
        .put("continue_after_cleanup_failure", True)
        .put("record_multiple_failures", True)
    )

    allowed_fields = {
        "entered_scope_cleanup",
        "unentered_scope_cleanup",
        "nested_order",
        "same_scope_order",
        "continue_after_cleanup_failure",
        "record_multiple_failures",
    }
    _reject_unknown_policy_fields(value, allowed_fields, path, "cleanup policy")

    if value.has("entered_scope_cleanup"):
        entered_scope_cleanup = value.get("entered_scope_cleanup")
        _require_boolean(entered_scope_cleanup, f"{path}.entered_scope_cleanup")
        if entered_scope_cleanup is not True:
            raise ValueError(
                f"invalid lifecycle plan at {path}.entered_scope_cleanup: "
                "entered scopes must remain cleanup eligible"
            )

    if value.has("unentered_scope_cleanup"):
        unentered_scope_cleanup = value.get("unentered_scope_cleanup")
        _require_boolean(unentered_scope_cleanup, f"{path}.unentered_scope_cleanup")
        if unentered_scope_cleanup is not False:
            raise ValueError(
                f"invalid lifecycle plan at {path}.unentered_scope_cleanup: "
                "unentered scope cleanup is not supported"
            )

    if value.has("nested_order"):
        nested_order = value.get("nested_order")
        _require_policy_symbol(nested_order, f"{path}.nested_order")
        if nested_order != _symbol("inner_to_outer"):
            raise ValueError(
                f"invalid lifecycle plan at {path}.nested_order: "
                f"unsupported cleanup order {nested_order}"
            )
        normalized = normalized.put("nested_order", nested_order)

    if value.has("same_scope_order"):
        same_scope_order = value.get("same_scope_order")
        _require_policy_symbol(same_scope_order, f"{path}.same_scope_order")
        if same_scope_order not in {
            _symbol("reverse_source_order"),
            _symbol("registration_reverse_order"),
        }:
            raise ValueError(
                f"invalid lifecycle plan at {path}.same_scope_order: "
                f"unsupported cleanup order {same_scope_order}"
            )
        normalized = normalized.put("same_scope_order", same_scope_order)

    for field in ("continue_after_cleanup_failure", "record_multiple_failures"):
        if value.has(field):
            field_value = value.get(field)
            _require_boolean(field_value, f"{path}.{field}")
            if field_value is not True:
                raise ValueError(
                    f"invalid lifecycle plan at {path}.{field}: "
                    "cleanup failures must remain observable"
                )

    return normalized


def _normalize_failure_policy(value: Any) -> GeniaMap:
    path = f"{_PLAN}.failure_policy"
    if not isinstance(value, GeniaMap):
        _fail(path, "expected map", value)

    normalized = (
        GeniaMap()
        .put("primary_failure", _symbol("first_non_cleanup"))
        .put("cleanup_failure", _symbol("recorded_secondary"))
        .put("cleanup_only_status", _symbol("failed"))
        .put("normal_failure_continuation", _symbol("abort_to_cleanup"))
        .put("preserve_primary_failure", True)
        .put("preserve_cleanup_failures", True)
    )

    allowed_fields = {
        "primary_failure",
        "cleanup_failure",
        "cleanup_only_status",
        "normal_failure_continuation",
        "preserve_primary_failure",
        "preserve_cleanup_failures",
    }
    _reject_unknown_policy_fields(value, allowed_fields, path, "failure policy")

    if value.has("primary_failure"):
        primary_failure = value.get("primary_failure")
        _require_policy_symbol(primary_failure, f"{path}.primary_failure")
        if primary_failure != _symbol("first_non_cleanup"):
            _fail_unsupported_failure_policy(
                f"{path}.primary_failure",
                primary_failure,
            )

    if value.has("cleanup_failure"):
        cleanup_failure = value.get("cleanup_failure")
        _require_policy_symbol(cleanup_failure, f"{path}.cleanup_failure")
        if cleanup_failure == _symbol("overwrite_primary"):
            raise ValueError(
                f"invalid lifecycle plan at {path}.cleanup_failure: "
                "cleanup failure must not overwrite primary failure"
            )
        if cleanup_failure == _symbol("swallow"):
            raise ValueError(
                f"invalid lifecycle plan at {path}.cleanup_failure: "
                "cleanup failures must be preserved"
            )
        if cleanup_failure != _symbol("recorded_secondary"):
            _fail_unsupported_failure_policy(
                f"{path}.cleanup_failure",
                cleanup_failure,
            )

    if value.has("cleanup_only_status"):
        cleanup_only_status = value.get("cleanup_only_status")
        _require_policy_symbol(cleanup_only_status, f"{path}.cleanup_only_status")
        if cleanup_only_status != _symbol("failed"):
            _fail_unsupported_failure_policy(
                f"{path}.cleanup_only_status",
                cleanup_only_status,
            )

    if value.has("normal_failure_continuation"):
        normal_failure_continuation = value.get("normal_failure_continuation")
        _require_policy_symbol(
            normal_failure_continuation,
            f"{path}.normal_failure_continuation",
        )
        if normal_failure_continuation != _symbol("abort_to_cleanup"):
            _fail_unsupported_failure_policy(
                f"{path}.normal_failure_continuation",
                normal_failure_continuation,
            )

    if value.has("preserve_primary_failure"):
        preserve_primary_failure = value.get("preserve_primary_failure")
        _require_boolean(
            preserve_primary_failure,
            f"{path}.preserve_primary_failure",
        )
        if preserve_primary_failure is not True:
            raise ValueError(
                f"invalid lifecycle plan at {path}.preserve_primary_failure: "
                "primary failure must be preserved"
            )

    if value.has("preserve_cleanup_failures"):
        preserve_cleanup_failures = value.get("preserve_cleanup_failures")
        _require_boolean(
            preserve_cleanup_failures,
            f"{path}.preserve_cleanup_failures",
        )
        if preserve_cleanup_failures is not True:
            raise ValueError(
                f"invalid lifecycle plan at {path}.preserve_cleanup_failures: "
                "cleanup failures must be preserved"
            )

    return normalized


def _normalize_result_policy(value: Any) -> GeniaMap:
    path = f"{_PLAN}.result_policy"
    if not isinstance(value, GeniaMap):
        _fail(path, "expected map", value)

    normalized = (
        GeniaMap()
        .put("failure_order", _symbol("observed_order"))
        .put("include_phase", True)
        .put("include_scope", True)
        .put("include_role", True)
        .put("include_source_location", True)
    )

    allowed_fields = {
        "failure_order",
        "include_phase",
        "include_scope",
        "include_role",
        "include_source_location",
    }
    _reject_unknown_policy_fields(value, allowed_fields, path, "result policy")

    if value.has("failure_order"):
        failure_order = value.get("failure_order")
        _require_policy_symbol(failure_order, f"{path}.failure_order")
        if failure_order != _symbol("observed_order"):
            raise ValueError(
                f"invalid lifecycle plan at {path}.failure_order: "
                f"unsupported failure order {failure_order}"
            )

    for field in (
        "include_phase",
        "include_scope",
        "include_role",
        "include_source_location",
    ):
        if value.has(field):
            field_value = value.get(field)
            _require_boolean(field_value, f"{path}.{field}")

    return normalized


def _reject_unknown_policy_fields(
    record: GeniaMap,
    allowed_fields: set[str],
    path: str,
    policy_name: str,
) -> None:
    for key, _ in record.items():
        if key not in allowed_fields:
            raise ValueError(
                f"invalid lifecycle plan at {path}.{key}: "
                f"unsupported {policy_name} field"
            )


def _require_boolean(value: Any, path: str) -> None:
    if not isinstance(value, bool):
        _fail(path, "expected boolean", value)


def _require_policy_symbol(value: Any, path: str) -> None:
    if not isinstance(value, GeniaSymbol):
        _fail(path, "expected identifier", value)


def _fail_unsupported_failure_policy(path: str, value: GeniaSymbol) -> None:
    raise ValueError(
        f"invalid lifecycle plan at {path}: unsupported failure policy {value}"
    )


def _symbol(name: str) -> GeniaSymbol:
    return GeniaSymbol(name)


def _fail(path: str, expected: str, value: Any) -> None:
    actual = _lifecycle_type_name(value)
    raise ValueError(f"invalid lifecycle plan at {path}: {expected}, got {actual}")


def _lifecycle_type_name(value: Any) -> str:
    if isinstance(value, GeniaSymbol):
        return "symbol"
    return _runtime_type_name(value)
