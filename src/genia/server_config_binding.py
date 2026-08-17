"""Inert R8 server configuration annotation discovery and bind-down."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .ir import IrAssign, IrNode
from .values import GeniaMap, _is_nil_none, _runtime_type_name


@dataclass(frozen=True)
class ServerConfigDeclaration:
    name: str
    metadata: Mapping[str, Any] | GeniaMap
    target_kind: str
    source_identity: str
    source_index: int
    source_location: Any = None


@dataclass(frozen=True)
class ServerConfigBinding:
    declaration_name: str
    config: GeniaMap
    source_identity: str
    source_index: int
    source_location: Any = None


@dataclass(frozen=True)
class ServerConfigBindingDiagnostic:
    annotation_name: str
    declaration_name: str | None
    source_location: Any
    reason: str


@dataclass(frozen=True)
class ServerConfigBindingResult:
    binding: ServerConfigBinding | None
    diagnostics: list[ServerConfigBindingDiagnostic]


_SERVER_KEYS = {"host", "port", "max_requests"}


def validate_server_descriptor(value: Any) -> GeniaMap:
    """Validate and normalize one closed inert server descriptor."""

    if not isinstance(value, GeniaMap):
        raise TypeError(
            "@server annotation expected a map, "
            f"received {_runtime_type_name(value)}"
        )

    for key, _ in value.items():  # noqa: PERF102 - GeniaMap exposes ordered items, not keys
        if not isinstance(key, str) or key not in _SERVER_KEYS:
            raise TypeError(f"@server descriptor has unknown field: {key}")

    host = value.get("host", "127.0.0.1")
    if not isinstance(host, str):
        raise TypeError(
            "@server descriptor host expected a string, "
            f"received {_runtime_type_name(host)}"
        )

    port = value.get("port", 8000)
    if isinstance(port, bool) or not isinstance(port, int):
        raise TypeError(
            "@server descriptor port expected an integer, "
            f"received {_runtime_type_name(port)}"
        )
    if port < 0 or port > 65535:
        raise ValueError("@server descriptor port expected an integer in [0, 65535]")

    normalized = GeniaMap().put("host", host).put("port", port)
    if value.has("max_requests"):
        max_requests = value.get("max_requests")
        if max_requests is not None and not _is_nil_none(max_requests):
            if isinstance(max_requests, bool) or not isinstance(max_requests, int):
                raise TypeError(
                    "@server descriptor max_requests expected a positive integer, "
                    f"received {_runtime_type_name(max_requests)}"
                )
            if max_requests < 1:
                raise ValueError("@server descriptor max_requests expected a positive integer")
            normalized = normalized.put("max_requests", max_requests)
    return normalized


def discover_server_config_binding(
    declarations: list[ServerConfigDeclaration],
    *,
    entry_source_identity: str,
) -> ServerConfigBindingResult:
    """Discover exactly one validated entry-file server descriptor."""

    candidates = sorted(
        (
            declaration
            for declaration in declarations
            if declaration.source_identity == entry_source_identity
            and _metadata_has(declaration.metadata, "server")
        ),
        key=lambda declaration: (declaration.source_index, declaration.name),
    )
    if not candidates:
        return ServerConfigBindingResult(
            binding=None,
            diagnostics=[
                ServerConfigBindingDiagnostic(
                    annotation_name="server",
                    declaration_name=None,
                    source_location=None,
                    reason="required @server descriptor not found in entry file",
                )
            ],
        )

    diagnostics: list[ServerConfigBindingDiagnostic] = []
    valid: list[ServerConfigBinding] = []
    for candidate in candidates:
        if candidate.target_kind != "assignment":
            diagnostics.append(
                _diagnostic(candidate, "@server annotation requires a top-level assignment")
            )
            continue
        try:
            config = validate_server_descriptor(_metadata_get(candidate.metadata, "server"))
        except (TypeError, ValueError) as error:
            diagnostics.append(_diagnostic(candidate, str(error)))
            continue
        valid.append(
            ServerConfigBinding(
                declaration_name=candidate.name,
                config=config,
                source_identity=candidate.source_identity,
                source_index=candidate.source_index,
                source_location=candidate.source_location,
            )
        )

    if len(valid) > 1:
        diagnostics.extend(
            ServerConfigBindingDiagnostic(
                annotation_name="server",
                declaration_name=binding.declaration_name,
                source_location=binding.source_location,
                reason="multiple @server descriptors in entry file",
            )
            for binding in valid
        )

    if diagnostics:
        return ServerConfigBindingResult(binding=None, diagnostics=diagnostics)
    if not valid:
        return ServerConfigBindingResult(binding=None, diagnostics=[])
    return ServerConfigBindingResult(binding=valid[0], diagnostics=[])


def discover_entry_file_server_config_binding(
    nodes: list[IrNode],
    env: Any,
    *,
    entry_source_identity: str,
) -> ServerConfigBindingResult:
    """Discover canonical server metadata owned by evaluated entry-file assignments."""

    declarations: list[ServerConfigDeclaration] = []
    for source_index, node in enumerate(nodes):
        if not isinstance(node, IrAssign):
            continue
        if not any(annotation.name == "server" for annotation in node.annotations):
            continue
        declarations.append(
            ServerConfigDeclaration(
                name=node.name,
                metadata=env.get_metadata(node.name),
                target_kind="assignment",
                source_identity=entry_source_identity,
                source_index=source_index,
                source_location=node.span,
            )
        )
    return discover_server_config_binding(
        declarations,
        entry_source_identity=entry_source_identity,
    )


def bind_server_config(
    result: ServerConfigBindingResult,
    handler: Any,
    *,
    serve_http: Callable[[GeniaMap, Any], Any],
) -> Any:
    """Pass accepted configuration solely to the existing serving operation."""

    if result.diagnostics or result.binding is None:
        raise ValueError("cannot bind server config with diagnostics")
    return serve_http(result.binding.config, handler)


def _metadata_has(metadata: Mapping[str, Any] | GeniaMap, key: str) -> bool:
    return metadata.has(key) if isinstance(metadata, GeniaMap) else key in metadata


def _metadata_get(metadata: Mapping[str, Any] | GeniaMap, key: str) -> Any:
    return metadata.get(key)


def _diagnostic(
    declaration: ServerConfigDeclaration,
    reason: str,
) -> ServerConfigBindingDiagnostic:
    return ServerConfigBindingDiagnostic(
        annotation_name="server",
        declaration_name=declaration.name,
        source_location=declaration.source_location,
        reason=reason,
    )
