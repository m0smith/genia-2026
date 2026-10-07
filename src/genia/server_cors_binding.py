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
    """Candidate annotation metadata with entry-file identity and source ordering.

    The caller supplies evaluated metadata and target kind; discovery validates
    them without executing the declaration. Frozen fields retain references to
    metadata and source location rather than making deep immutable copies.
    """

    name: str
    metadata: Mapping[str, Any] | GeniaMap
    target_kind: str
    source_identity: str
    source_index: int
    source_location: Any = None


@dataclass(frozen=True)
class CorsBinding:
    """Accepted CORS policy and assignment provenance for server-owner matching.

    Validation retains the input policy map; wrapping begins only in bind_cors.
    Frozen fields do not deeply freeze referenced policy or location values.
    """

    declaration_name: str
    policy: GeniaMap
    source_identity: str
    source_index: int
    source_location: Any = None


@dataclass(frozen=True)
class CorsBindingDiagnostic:
    """Annotation failure carrying declaration identity and optional source location.

    Discovery collects these records instead of binding invalid candidates.
    """

    annotation_name: str
    declaration_name: str | None
    source_location: Any
    reason: str


@dataclass(frozen=True)
class CorsBindingResult:
    """Optional accepted policy or diagnostics preventing handler wrapping.

    No binding and no diagnostics means CORS is absent; bind_cors then returns
    the original handler. The diagnostics list remains mutable.
    """

    binding: CorsBinding | None
    diagnostics: list[CorsBindingDiagnostic]


def validate_cors_descriptor(value: Any) -> GeniaMap:
    """Validate via resolve_cors_policy and return the original map unchanged.

    R7 policy validation errors propagate; the resolved policy object is not
    retained and no handler is wrapped during descriptor validation.
    """

    resolve_cors_policy(value)
    return value


def discover_cors_binding(
    declarations: list[CorsDeclaration],
    *,
    entry_source_identity: str,
    server_declaration_name: str,
    server_source_index: int,
) -> CorsBindingResult:
    """Validate optional entry-file CORS assignments in source-index/name order.

    Ignore other sources; catch descriptor TypeError as diagnostic reasons.
    Reject multiple valid policies, or one whose name/index differs from the
    selected server owner. Any diagnostic suppresses the binding; no candidates
    yields absence without diagnostics. Discovery never wraps the handler.
    """

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
    """Read evaluated CORS metadata from annotated top-level IrAssign nodes.

    The caller supplies the entry-file-only IR list and evaluated environment;
    candidates receive its source identity and enumerated indices. Environment
    lookup failures propagate. Delegate policy/owner validation to discovery
    without evaluating assignments or wrapping handlers.
    """

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
    """Return the original handler on absence, or call injected cors once.

    Diagnostics raise ValueError before wrapping. An accepted policy and handler
    pass unchanged to the callback; return its result and propagate its effects
    or exceptions. This function does not itself activate a server.
    """

    if result.diagnostics:
        raise ValueError("cannot bind CORS with diagnostics")
    if result.binding is None:
        return handler
    return cors(result.binding.policy, handler)


def _metadata_has(metadata: Mapping[str, Any] | GeniaMap, key: str) -> bool:
    """Check key presence in either evaluated Genia metadata or a host mapping."""

    return metadata.has(key) if isinstance(metadata, GeniaMap) else key in metadata


def _metadata_get(metadata: Mapping[str, Any] | GeniaMap, key: str) -> Any:
    """Read an annotation payload; a missing key follows the mapping get behavior."""

    return metadata.get(key)


def _diagnostic(declaration: CorsDeclaration, reason: str) -> CorsBindingDiagnostic:
    """Associate a validation reason with the candidate name and source location."""

    return CorsBindingDiagnostic(
        annotation_name="cors",
        declaration_name=declaration.name,
        source_location=declaration.source_location,
        reason=reason,
    )
