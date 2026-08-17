"""Inert R8 CORS annotation discovery and R7 CORS bind-down."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .cors_policy import resolve_cors_policy
from .ir import IrAssign, IrNode
from .values import GeniaMap


@dataclass(frozen=True)
class CorsDeclaration:
    name: str
    metadata: Mapping[str, Any] | GeniaMap
    target_kind: str
    source_identity: str
    source_index: int
    source_location: Any = None


@dataclass(frozen=True)
class CorsBinding:
    declaration_name: str
    policy: GeniaMap
    source_identity: str
    source_index: int
    source_location: Any = None


@dataclass(frozen=True)
class CorsBindingDiagnostic:
    annotation_name: str
    declaration_name: str | None
    source_location: Any
    reason: str


@dataclass(frozen=True)
class CorsBindingResult:
    binding: CorsBinding | None
    diagnostics: list[CorsBindingDiagnostic]


def validate_cors_descriptor(value: Any) -> GeniaMap:
    """Validate one closed inert descriptor through the R7 policy contract."""

    resolve_cors_policy(value)
    return value


def discover_cors_binding(
    declarations: list[CorsDeclaration],
    *,
    entry_source_identity: str,
    server_declaration_name: str,
    server_source_index: int,
) -> CorsBindingResult:
    """Discover the optional entry-file CORS descriptor for one server owner."""

    candidates = sorted(
        (
            declaration
            for declaration in declarations
            if declaration.source_identity == entry_source_identity
            and _metadata_has(declaration.metadata, "cors")
        ),
        key=lambda declaration: (declaration.source_index, declaration.name),
    )
    diagnostics: list[CorsBindingDiagnostic] = []
    valid: list[CorsBinding] = []
    for candidate in candidates:
        if candidate.target_kind != "assignment":
            diagnostics.append(
                _diagnostic(candidate, "@cors annotation requires a top-level assignment")
            )
            continue
        try:
            policy = validate_cors_descriptor(_metadata_get(candidate.metadata, "cors"))
        except TypeError as error:
            diagnostics.append(_diagnostic(candidate, str(error)))
            continue
        valid.append(
            CorsBinding(
                declaration_name=candidate.name,
                policy=policy,
                source_identity=candidate.source_identity,
                source_index=candidate.source_index,
                source_location=candidate.source_location,
            )
        )

    if len(valid) > 1:
        diagnostics.extend(
            CorsBindingDiagnostic(
                annotation_name="cors",
                declaration_name=binding.declaration_name,
                source_location=binding.source_location,
                reason="multiple @cors descriptors in entry file",
            )
            for binding in valid
        )
    elif len(valid) == 1 and (
        valid[0].declaration_name != server_declaration_name
        or valid[0].source_index != server_source_index
    ):
        diagnostics.append(
            CorsBindingDiagnostic(
                annotation_name="cors",
                declaration_name=valid[0].declaration_name,
                source_location=valid[0].source_location,
                reason=(
                    "@cors descriptor must be attached to @server owner "
                    f"{server_declaration_name}"
                ),
            )
        )

    if diagnostics:
        return CorsBindingResult(binding=None, diagnostics=diagnostics)
    if not valid:
        return CorsBindingResult(binding=None, diagnostics=[])
    return CorsBindingResult(binding=valid[0], diagnostics=[])


def discover_entry_file_cors_binding(
    nodes: list[IrNode],
    env: Any,
    *,
    entry_source_identity: str,
    server_declaration_name: str,
    server_source_index: int,
) -> CorsBindingResult:
    """Discover canonical CORS metadata owned by entry-file assignments."""

    declarations: list[CorsDeclaration] = []
    for source_index, node in enumerate(nodes):
        if not isinstance(node, IrAssign):
            continue
        if not any(annotation.name == "cors" for annotation in node.annotations):
            continue
        declarations.append(
            CorsDeclaration(
                name=node.name,
                metadata=env.get_metadata(node.name),
                target_kind="assignment",
                source_identity=entry_source_identity,
                source_index=source_index,
                source_location=node.span,
            )
        )
    return discover_cors_binding(
        declarations,
        entry_source_identity=entry_source_identity,
        server_declaration_name=server_declaration_name,
        server_source_index=server_source_index,
    )


def bind_cors(
    result: CorsBindingResult,
    handler: Any,
    *,
    cors: Callable[[GeniaMap, Any], Any],
) -> Any:
    """Optionally wrap an accepted handler solely through the R7 operation."""

    if result.diagnostics:
        raise ValueError("cannot bind CORS with diagnostics")
    if result.binding is None:
        return handler
    return cors(result.binding.policy, handler)


def _metadata_has(metadata: Mapping[str, Any] | GeniaMap, key: str) -> bool:
    return metadata.has(key) if isinstance(metadata, GeniaMap) else key in metadata


def _metadata_get(metadata: Mapping[str, Any] | GeniaMap, key: str) -> Any:
    return metadata.get(key)


def _diagnostic(declaration: CorsDeclaration, reason: str) -> CorsBindingDiagnostic:
    return CorsBindingDiagnostic(
        annotation_name="cors",
        declaration_name=declaration.name,
        source_location=declaration.source_location,
        reason=reason,
    )
