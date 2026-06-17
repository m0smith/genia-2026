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


def _fail(path: str, expected: str, value: Any) -> None:
    actual = _lifecycle_type_name(value)
    raise ValueError(f"invalid lifecycle plan at {path}: {expected}, got {actual}")


def _lifecycle_type_name(value: Any) -> str:
    if isinstance(value, GeniaSymbol):
        return "symbol"
    return _runtime_type_name(value)
