"""Frozen ordinary views and pure validation for explicitly selected D2b linking.

Completion witnesses own the syntax. Each view receives detached invocation copies
and captures selected unit clause lists. No matcher, guard, body, lookup or renderer
runs while planning. Publication is a separate Env checked write after construction.
"""
from dataclasses import dataclass
from typing import Any

from .ordinary_completion import _Projection
from .callable import (
    GeniaFunction, GeniaOpenContributionUnit, GeniaLinkedOpenFunction,
    OpenFunctionDuplicateSelectionError, OpenFunctionCrossUnitDuplicateClauseError,
    OpenFunctionShapeConflictError,
)


@dataclass(frozen=True, eq=False)
class FrozenOrdinaryBase:
    """View-owned invocation syntax with original G/closure/runtime-handle identity.

    The projection remains authoritative; mutable invocation copies are never lent
    back to the witness or another view. This type is not exposed to Genia code.
    """
    group: Any
    interface_key: tuple[str, str]
    name: str
    module_id: str
    clauses: tuple[GeniaFunction, ...]
    span: Any
    projection: _Projection

    @classmethod
    def from_projection(cls, projection: _Projection) -> 'FrozenOrdinaryBase':
        """Materialize detached records and eagerly verify their keys before escape."""
        clauses = tuple(clause.materialize() for clause in projection.clauses)
        for copy, clause in zip(clauses, projection.clauses):
            if copy.dispatch_key != clause.dispatch_key:
                raise TypeError('ordinary completion key mismatch')
        module_id, name = projection.provenance
        return cls(projection.original, projection.provenance, name, module_id,
                   clauses, clauses[0].span if clauses else None, projection)


def plan_link(base: Any, units: Any) -> tuple:
    """Validate canonical cross-unit keys/shapes, returning the sorted selection.

    Duplicate selection wins first. Scan unit pairs then lexical clause ordinals;
    equal keys win over shape conflict. Read cached keys only, without user code
    or Env access. Same-unit and varargs/varargs combinations remain unchanged.
    """
    selected = tuple(units)
    seen = set()
    for unit in selected:
        if unit.declaring_module_id in seen:
            raise OpenFunctionDuplicateSelectionError(base.interface_key, unit.declaring_module_id)
        seen.add(unit.declaring_module_id)
    ordered = tuple(sorted(selected, key=lambda unit: unit.declaring_module_id))
    if isinstance(base, FrozenOrdinaryBase):
        base_keys = tuple(clause.dispatch_key for clause in base.projection.clauses)
    else:
        base_keys = tuple(record.dispatch_key for record in base.clauses)
    participants = [('base', f'base[{base.module_id}]', base.clauses, base_keys)]
    participants.extend((u.declaring_module_id, repr(u.declaring_module_id), u.clauses,
                         tuple(r.dispatch_key for r in u.clauses)) for u in ordered)
    for i, (first, first_label, records, keys) in enumerate(participants):
        for second, second_label, other_records, other_keys in participants[i + 1:]:
            for record, key in zip(records, keys):
                for other, other_key in zip(other_records, other_keys):
                    modules = (record.closure.module_identity(), other.closure.module_identity())
                    if key == other_key:
                        raise OpenFunctionCrossUnitDuplicateClauseError(
                            base.interface_key, first, second, key[0], record.span, other.span,
                            *modules, first_label, second_label)
                    shape, other_shape = key[0], other_key[0]
                    if shape[0] != other_shape[0]:
                        fixed, varargs = (shape, other_shape) if shape[0] == 'fixed' else (other_shape, shape)
                        if varargs[1] <= fixed[1]:
                            raise OpenFunctionShapeConflictError(
                                base.interface_key, first, second, shape, other_shape,
                                record.span, other.span, *modules, first_label, second_label)
    return ordered


def link_view(base: Any, units: Any) -> GeniaLinkedOpenFunction:
    """Build a validated frozen selection without publication, effects or locking.

    Fallible key reads and unit-list capture finish before constructing the value;
    callers may publish only the returned complete view through Env.publish_view.
    """
    ordered = plan_link(base, units)
    for record in base.clauses:
        record.dispatch_key
    copies = tuple(GeniaOpenContributionUnit(u.target_interface_key, u.declaring_module_id,
                                           tuple(u.clauses), target=u.target) for u in ordered)
    return GeniaLinkedOpenFunction(base, copies)
