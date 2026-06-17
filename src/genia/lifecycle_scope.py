"""Lifecycle scope tree data-shape validation for the Python reference host."""

from __future__ import annotations

from typing import Any

from .values import (
    GeniaMap,
    GeniaOptionNone,
    GeniaOptionSome,
    GeniaSymbol,
    _runtime_type_name,
)


_SCOPE_TREE = "scope_tree"
_SCOPE_NAMES = ("execution", "suite", "module", "test")
_SUPPORTED_SCOPES = ", ".join(_SCOPE_NAMES)
_EXPECTED_PARENTS = {
    "execution": None,
    "suite": "execution",
    "module": "suite",
    "test": "module",
}
_EXPECTED_CHILDREN = {
    "execution": ("suite",),
    "suite": ("module",),
    "module": ("test",),
    "test": (),
}


def validate_lifecycle_scope_tree(value: Any) -> None:
    """Validate lifecycle scope tree data without executing lifecycle behavior."""

    normalize_lifecycle_scope_tree(value)
    return None


def normalize_lifecycle_scope_tree(value: Any) -> GeniaMap:
    """Return a normalized lifecycle scope tree map or raise a deterministic error."""

    if not isinstance(value, GeniaMap):
        _fail(_SCOPE_TREE, "expected map", value)

    scopes = _required(value, "scopes", _SCOPE_TREE)
    if not isinstance(scopes, list):
        _fail(f"{_SCOPE_TREE}.scopes", "expected list", scopes)

    normalized_scopes: list[GeniaMap] = []
    scopes_by_name: dict[str, GeniaMap] = {}
    for index, scope in enumerate(scopes):
        normalized_scope = _normalize_scope(scope, index)
        name = normalized_scope.get("name")
        scope_name = name.name
        if scope_name in scopes_by_name:
            raise ValueError(
                f"invalid lifecycle scope tree at {_SCOPE_TREE}.scopes[{index}].name: "
                f"duplicate scope name {scope_name}"
            )
        scopes_by_name[scope_name] = normalized_scope
        normalized_scopes.append(normalized_scope)

    _validate_canonical_hierarchy(scopes_by_name)

    normalized = GeniaMap().put("scopes", normalized_scopes)
    for optional_field in ("description", "metadata"):
        if value.has(optional_field):
            optional_value = value.get(optional_field)
            _validate_optional_tree_field(optional_field, optional_value)
            normalized = normalized.put(optional_field, optional_value)
    return normalized


def _normalize_scope(value: Any, index: int) -> GeniaMap:
    path = f"{_SCOPE_TREE}.scopes[{index}]"
    if not isinstance(value, GeniaMap):
        _fail(path, "expected map", value)

    name = _required(value, "name", path)
    _require_identifier(name, f"{path}.name")
    if name.name not in _SCOPE_NAMES:
        raise ValueError(
            f"invalid lifecycle scope tree at {path}.name: unsupported scope {name.name}; "
            f"supported scopes: {_SUPPORTED_SCOPES}"
        )

    parent = _required(value, "parent", path)
    _require_parent(parent, f"{path}.parent")

    children = _required(value, "children", path)
    _require_children(children, f"{path}.children")

    normalized = GeniaMap().put("name", name).put("parent", parent).put("children", children)
    for optional_field in ("description", "metadata"):
        if value.has(optional_field):
            optional_value = value.get(optional_field)
            _validate_optional_scope_field(optional_field, optional_value, path)
            normalized = normalized.put(optional_field, optional_value)
    return normalized


def _validate_canonical_hierarchy(scopes_by_name: dict[str, GeniaMap]) -> None:
    for scope_name in _SCOPE_NAMES:
        if scope_name not in scopes_by_name:
            raise ValueError(
                f"invalid lifecycle scope tree at {_SCOPE_TREE}.scopes: "
                f"missing required scope {scope_name}"
            )

    for scope_name in _SCOPE_NAMES:
        scope = scopes_by_name[scope_name]
        parent = _parent_name(scope.get("parent"))
        expected_parent = _EXPECTED_PARENTS[scope_name]
        if parent != expected_parent:
            raise ValueError(
                f"invalid lifecycle scope tree at {_SCOPE_TREE}.scopes[{scope_name}].parent: "
                f"expected parent {_format_parent(expected_parent)}, got {_format_parent(parent)}"
            )

        children = tuple(child.name for child in scope.get("children"))
        expected_children = _EXPECTED_CHILDREN[scope_name]
        if children != expected_children:
            raise ValueError(
                f"invalid lifecycle scope tree at {_SCOPE_TREE}.scopes[{scope_name}].children: "
                f"expected children {_format_children(expected_children)}, got {_format_children(children)}"
            )


def _required(record: GeniaMap, field: str, path: str) -> Any:
    if not record.has(field):
        raise ValueError(
            f"invalid lifecycle scope tree at {path}.{field}: missing required field"
        )
    return record.get(field)


def _require_identifier(value: Any, path: str) -> None:
    if not isinstance(value, GeniaSymbol):
        _fail(path, "expected identifier", value)


def _require_parent(value: Any, path: str) -> None:
    if isinstance(value, GeniaOptionNone):
        return
    if isinstance(value, GeniaOptionSome) and isinstance(value.value, GeniaSymbol):
        return
    _fail(path, "expected none or some(identifier)", value)


def _require_children(value: Any, path: str) -> None:
    if not isinstance(value, list):
        _fail(path, "expected list", value)
    for index, child in enumerate(value):
        _require_identifier(child, f"{path}[{index}]")


def _validate_optional_tree_field(field: str, value: Any) -> None:
    path = f"{_SCOPE_TREE}.{field}"
    if field == "description" and not isinstance(value, str):
        _fail(path, "expected string", value)
    if field == "metadata" and not isinstance(value, GeniaMap):
        _fail(path, "expected map", value)


def _validate_optional_scope_field(field: str, value: Any, scope_path: str) -> None:
    path = f"{scope_path}.{field}"
    if field == "description" and not isinstance(value, str):
        _fail(path, "expected string", value)
    if field == "metadata" and not isinstance(value, GeniaMap):
        _fail(path, "expected map", value)


def _parent_name(value: GeniaOptionNone | GeniaOptionSome) -> str | None:
    if isinstance(value, GeniaOptionNone):
        return None
    return value.value.name


def _format_parent(parent: str | None) -> str:
    if parent is None:
        return "none"
    return parent


def _format_children(children: tuple[str, ...]) -> str:
    return "[" + ", ".join(children) + "]"


def _fail(path: str, expected: str, value: Any) -> None:
    actual = _lifecycle_type_name(value)
    raise ValueError(f"invalid lifecycle scope tree at {path}: {expected}, got {actual}")


def _lifecycle_type_name(value: Any) -> str:
    if isinstance(value, GeniaSymbol):
        return "symbol"
    return _runtime_type_name(value)
