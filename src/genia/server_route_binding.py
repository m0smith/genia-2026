"""Inert R8 route annotation discovery and R7 route assembly."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .callable import GeniaFunction, GeniaFunctionGroup
from .ir import IrFuncDef, IrNode
from .values import GeniaMap, _runtime_type_name


@dataclass(frozen=True)
class RouteDeclaration:
    name: str
    value: Any
    metadata: Mapping[str, Any] | GeniaMap
    target_kind: str
    source_identity: str
    source_index: int
    source_location: Any = None


@dataclass(frozen=True)
class RouteBinding:
    declaration_name: str
    method: str
    path: str
    handler: GeniaFunctionGroup
    source_identity: str
    source_index: int
    source_location: Any = None


@dataclass(frozen=True)
class RouteBindingDiagnostic:
    annotation_name: str
    declaration_name: str | None
    source_location: Any
    reason: str


@dataclass(frozen=True)
class RouteBindingResult:
    routes: list[RouteBinding]
    diagnostics: list[RouteBindingDiagnostic]


_ROUTE_KEYS = {"method", "path"}


def validate_route_descriptor(value: Any) -> GeniaMap:
    """Validate one closed inert route descriptor without normalizing it."""

    if not isinstance(value, GeniaMap):
        raise TypeError(
            "@route annotation expected a map, "
            f"received {_runtime_type_name(value)}"
        )
    keys = {key for key, _ in value.items() if isinstance(key, str)}
    if value.count() != 2 or keys != _ROUTE_KEYS:
        raise TypeError("@route descriptor expected exactly method and path fields")

    method = value.get("method")
    path = value.get("path")
    if not isinstance(method, str):
        raise TypeError(
            "@route descriptor method expected a string, "
            f"received {_runtime_type_name(method)}"
        )
    if not method:
        raise TypeError("@route descriptor method must not be empty")
    if not isinstance(path, str):
        raise TypeError(
            "@route descriptor path expected a string, "
            f"received {_runtime_type_name(path)}"
        )
    if not path:
        raise TypeError("@route descriptor path must not be empty")
    if not path.startswith("/"):
        raise TypeError("@route descriptor path must start with /")
    return value


def discover_route_bindings(
    declarations: list[RouteDeclaration],
    *,
    entry_source_identity: str,
) -> RouteBindingResult:
    """Discover validated entry-file routes without executing handlers."""

    candidates = sorted(
        (
            declaration
            for declaration in declarations
            if declaration.source_identity == entry_source_identity
            and _metadata_has(declaration.metadata, "route")
        ),
        key=lambda declaration: (declaration.source_index, declaration.name),
    )
    descriptor_diagnostics: list[RouteBindingDiagnostic] = []
    valid: list[RouteBinding] = []

    for candidate in candidates:
        if candidate.target_kind != "function":
            descriptor_diagnostics.append(
                _diagnostic(candidate, "@route annotation requires a top-level named function")
            )
            continue
        try:
            descriptor = validate_route_descriptor(_metadata_get(candidate.metadata, "route"))
        except TypeError as error:
            descriptor_diagnostics.append(_diagnostic(candidate, str(error)))
            continue
        if not _is_exact_one_argument_handler(candidate.value):
            descriptor_diagnostics.append(
                _diagnostic(
                    candidate,
                    "@route handler must expose exactly one fixed one-argument function arm",
                )
            )
            continue
        valid.append(
            RouteBinding(
                declaration_name=candidate.name,
                method=descriptor.get("method"),
                path=descriptor.get("path"),
                handler=candidate.value,
                source_identity=candidate.source_identity,
                source_index=candidate.source_index,
                source_location=candidate.source_location,
            )
        )

    by_key: dict[tuple[str, str], list[RouteBinding]] = {}
    for route in valid:
        by_key.setdefault((route.method, route.path), []).append(route)

    conflict_diagnostics: list[RouteBindingDiagnostic] = []
    for route in valid:
        if len(by_key[(route.method, route.path)]) < 2:
            continue
        conflict_diagnostics.append(
            RouteBindingDiagnostic(
                annotation_name="route",
                declaration_name=route.declaration_name,
                source_location=route.source_location,
                reason=f"conflicting @route {route.method} {route.path}",
            )
        )

    diagnostics = [*descriptor_diagnostics, *conflict_diagnostics]
    if diagnostics:
        return RouteBindingResult(routes=[], diagnostics=diagnostics)
    return RouteBindingResult(routes=valid, diagnostics=[])


def discover_entry_file_route_bindings(
    nodes: list[IrNode],
    env: Any,
    *,
    entry_source_identity: str,
) -> RouteBindingResult:
    """Discover route declarations owned by one evaluated entry-file IR list."""

    declarations: list[RouteDeclaration] = []
    for source_index, node in enumerate(nodes):
        if not isinstance(node, IrFuncDef):
            continue
        if not any(annotation.name == "route" for annotation in node.annotations):
            continue
        declarations.append(
            RouteDeclaration(
                name=node.name,
                value=env.get(node.name),
                metadata=env.get_metadata(node.name),
                target_kind="function",
                source_identity=entry_source_identity,
                source_index=source_index,
                source_location=node.span,
            )
        )
    return discover_route_bindings(
        declarations,
        entry_source_identity=entry_source_identity,
    )


def assemble_route_handler(
    result: RouteBindingResult,
    *,
    route: Callable[[str, str, Any], Any],
    route_request: Callable[[list[Any]], Any],
) -> Any:
    """Assemble accepted bindings solely through existing R7 operations."""

    if result.diagnostics:
        raise ValueError("cannot assemble routes with diagnostics")
    routes = [
        route(binding.method, binding.path, binding.handler)
        for binding in result.routes
    ]
    return route_request(routes)


def _is_exact_one_argument_handler(value: Any) -> bool:
    if not isinstance(value, GeniaFunctionGroup) or value.sorted_arities() != [1]:
        return False
    function = value.get(1)
    return isinstance(function, GeniaFunction) and function.rest_param is None


def _metadata_has(metadata: Mapping[str, Any] | GeniaMap, key: str) -> bool:
    return metadata.has(key) if isinstance(metadata, GeniaMap) else key in metadata


def _metadata_get(metadata: Mapping[str, Any] | GeniaMap, key: str) -> Any:
    return metadata.get(key)


def _diagnostic(
    declaration: RouteDeclaration,
    reason: str,
) -> RouteBindingDiagnostic:
    return RouteBindingDiagnostic(
        annotation_name="route",
        declaration_name=declaration.name,
        source_location=declaration.source_location,
        reason=reason,
    )
