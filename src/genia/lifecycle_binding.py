"""Internal lifecycle annotation binding helpers for the Python reference host."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .callable import GeniaFunction, GeniaFunctionGroup
from .values import _runtime_type_name


@dataclass(frozen=True)
class LifecycleAnnotationBinding:
    phase: str
    annotation_name: str
    filters: Mapping[str, Any]
    ordering: str = "source_order"
    required: bool = False
    participant_kind: str = "callable"
    failure_policy: str = "diagnostic"


@dataclass(frozen=True)
class AnnotationInfo:
    name: str
    metadata: Mapping[str, Any]
    source_location: Any = None


@dataclass(frozen=True)
class AnnotationCandidate:
    name: str
    value: Any
    annotations: list[AnnotationInfo]
    source_location: Any = None
    source_identity: str = ""
    source_index: int = 0


@dataclass(frozen=True)
class LifecycleParticipant:
    declaration_name: str
    value: Any
    annotation: AnnotationInfo
    phase: str
    binding: LifecycleAnnotationBinding
    order_key: tuple[Any, ...]
    source_location: Any = None


@dataclass(frozen=True)
class LifecycleBindingDiagnostic:
    phase: str
    annotation_name: str
    declaration_name: str | None
    source_location: Any
    reason: str


@dataclass(frozen=True)
class LifecycleBindingResult:
    phase: str
    binding: LifecycleAnnotationBinding
    participants: list[LifecycleParticipant]
    diagnostics: list[LifecycleBindingDiagnostic]


_SUPPORTED_ORDERINGS = (
    "source_order",
    "reverse_source_order",
    "stable_name_order",
)
_SUPPORTED_ORDERING_SET = set(_SUPPORTED_ORDERINGS)


def discover_lifecycle_participants(
    binding: LifecycleAnnotationBinding,
    candidates: list[AnnotationCandidate],
) -> LifecycleBindingResult:
    ordering = _validate_ordering(binding.ordering)

    participants: list[LifecycleParticipant] = []
    diagnostics: list[LifecycleBindingDiagnostic] = []
    seen_declarations: set[str] = set()

    for candidate in candidates:
        matching_annotations = [
            annotation
            for annotation in candidate.annotations
            if _annotation_matches(binding, annotation)
        ]
        if not matching_annotations:
            continue

        if not _participant_kind_matches(binding, candidate):
            diagnostics.append(
                _diagnostic(
                    binding,
                    candidate,
                    (
                        f"lifecycle participant {candidate.name} "
                        f"for @{binding.annotation_name} expected callable, "
                        f"got {_runtime_type_name(candidate.value)}"
                    ),
                )
            )
            continue

        for annotation in matching_annotations:
            if candidate.name in seen_declarations:
                diagnostics.append(
                    _diagnostic(
                        binding,
                        candidate,
                        (
                            "duplicate lifecycle participant selected "
                            f"for @{binding.annotation_name}: {candidate.name}"
                        ),
                    )
                )
                continue
            seen_declarations.add(candidate.name)
            participants.append(
                LifecycleParticipant(
                    declaration_name=candidate.name,
                    value=candidate.value,
                    annotation=annotation,
                    phase=binding.phase,
                    binding=binding,
                    order_key=_order_key(ordering, candidate),
                    source_location=candidate.source_location,
                )
            )

    participants = sorted(participants, key=lambda participant: participant.order_key)
    if binding.required and not participants:
        diagnostics.append(
            LifecycleBindingDiagnostic(
                phase=binding.phase,
                annotation_name=binding.annotation_name,
                declaration_name=None,
                source_location=None,
                reason=(
                    "required lifecycle annotation binding found no candidates "
                    f"for @{binding.annotation_name}"
                ),
            )
        )

    return LifecycleBindingResult(
        phase=binding.phase,
        binding=binding,
        participants=participants,
        diagnostics=diagnostics,
    )


def _annotation_matches(
    binding: LifecycleAnnotationBinding,
    annotation: AnnotationInfo,
) -> bool:
    if annotation.name != binding.annotation_name:
        return False
    for key, expected in binding.filters.items():
        if key not in annotation.metadata:
            return False
        if annotation.metadata[key] != expected:
            return False
    return True


def _participant_kind_matches(
    binding: LifecycleAnnotationBinding,
    candidate: AnnotationCandidate,
) -> bool:
    if binding.participant_kind == "callable":
        return _is_lifecycle_callable_participant(candidate.value)
    return True


def _is_lifecycle_callable_participant(value: Any) -> bool:
    return isinstance(value, (GeniaFunctionGroup, GeniaFunction)) or callable(value)


def _validate_ordering(ordering: Any) -> str:
    if not isinstance(ordering, str):
        raise ValueError(
            "invalid lifecycle annotation binding at binding.ordering: "
            f"expected ordering identifier, got {_runtime_type_name(ordering)}"
        )
    if ordering not in _SUPPORTED_ORDERING_SET:
        raise ValueError(
            "invalid lifecycle annotation binding at binding.ordering: "
            f"unsupported ordering {ordering}"
        )
    return ordering


def _order_key(
    ordering: str,
    candidate: AnnotationCandidate,
) -> tuple[Any, ...]:
    source_identity = candidate.source_identity
    source_index = candidate.source_index
    name = candidate.name
    if ordering == "source_order":
        return (source_identity, source_index, name)
    if ordering == "reverse_source_order":
        return (source_identity, -source_index, name)
    return (name, source_identity, source_index)


def _diagnostic(
    binding: LifecycleAnnotationBinding,
    candidate: AnnotationCandidate,
    reason: str,
) -> LifecycleBindingDiagnostic:
    return LifecycleBindingDiagnostic(
        phase=binding.phase,
        annotation_name=binding.annotation_name,
        declaration_name=candidate.name,
        source_location=candidate.source_location,
        reason=reason,
    )
