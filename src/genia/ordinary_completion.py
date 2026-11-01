"""Private D1 completion ownership; no linking, reflection API or wire format.

The loader calls preparation under its binding lock after successful module
evaluation. Copies execute no user code and retain closure/runtime-value identity.
"""

from dataclasses import dataclass, field, fields, is_dataclass
from types import MappingProxyType
from typing import Any

from . import ast_nodes, ir, pattern_match
from .callable import GeniaFunction, GeniaFunctionGroup
from .lexer import SourceSpan
from .values import GeniaMap


def _copy_syntax(value: Any) -> Any:
    """Detach known syntax containers without cloning closures or runtime handles.

    Only repository AST/IR/pattern dataclasses and source spans are constructed;
    arbitrary dataclasses, conversion hooks and deepcopy protocols are untouched.
    Literal numeric payload dictionaries are syntax; opaque language values remain
    shared. No portable-IR validator is used, so host-only bodies remain valid.
    """
    if isinstance(value, ir.IrLiteral):
        # Numeric source payloads are syntax. Other literal values belong to the
        # language runtime, including mutable handles or host-injected lists.
        payload = value.value
        if type(payload) is dict and payload.get('kind') in {'integer', 'decimal', 'float64', 'rational'}:
            payload = _copy_syntax(payload)
        return ir.IrLiteral(payload, span=_copy_syntax(value.span))
    if type(value) is list:
        return [_copy_syntax(item) for item in value]
    if type(value) is tuple:
        return tuple(_copy_syntax(item) for item in value)
    if type(value) is dict:
        return {key: _copy_syntax(item) for key, item in value.items()}
    if is_dataclass(value) and (
        isinstance(value, (ast_nodes.Node, ir.IrNode, pattern_match.IrPattern, SourceSpan))
        or type(value).__module__ == pattern_match.__name__
    ):
        return type(value)(**{part.name: _copy_syntax(getattr(value, part.name)) for part in fields(value)})
    return value


def _copy_record(record: GeniaFunction) -> GeniaFunction:
    """Make an existing invocation record with detached syntax and shared closure/hooks."""
    return GeniaFunction(
        record.name, list(record.params), record.rest_param, record.docstring,
        _copy_syntax(record.body), record.closure, span=_copy_syntax(record.span),
        debug_hooks=record.debug_hooks, debug_mode=record.debug_mode,
        internal_access=record.internal_access, pattern=_copy_syntax(record.pattern),
        guard=_copy_syntax(record.guard),
    )


class _Metadata(GeniaMap):
    """Persistent-map compatible metadata with a read-only owned host table."""

    def __init__(self, source: GeniaMap):
        """Copy only the metadata table; language payloads retain shallow identity."""
        object.__setattr__(self, '_entries', MappingProxyType(dict(source._entries)))

    def __setattr__(self, name: str, value: Any) -> None:
        """Reject reassignment of the snapshot table; persistent put/remove stay functional."""
        raise AttributeError('completed metadata is read-only')


def _doc(metadata: GeniaMap) -> str | None:
    """Select a string doc without rendering, autoload or language invocation."""
    value = metadata.get('doc', None)
    return value if isinstance(value, str) else None


@dataclass(frozen=True, eq=False)
class _Clause:
    """Immutable logical descriptor owning private detached existing-IR syntax."""

    shape: tuple
    dispatch_key: tuple
    declaration_ordinal: int
    arm_ordinals: tuple[int, ...]
    provenance: tuple
    _record: GeniaFunction = field(repr=False)

    def materialize(self) -> GeniaFunction:
        """Return a fresh invocation copy; never lend the authoritative syntax tree."""
        return _copy_record(self._record)


@dataclass(frozen=True, eq=False)
class _Projection:
    """Original completion facts, separate from the mutable ordinary callable."""

    original: GeniaFunctionGroup = field(repr=False)
    provenance: tuple[str, str]
    clauses: tuple[_Clause, ...]
    binding_metadata: GeniaMap
    projected_doc: str | None
    help_doc: str | None
    help_metadata: GeniaMap


def _capture(group: GeniaFunctionGroup, module_env: Any) -> _Projection:
    """Capture one original G using its local defining slot, not its current value.

    Called with the writer lock held. Construction can raise; no live object is
    modified or published. Closures, Ref/Cell values and prior effects stay live.
    """
    binding = _Metadata(module_env.binding_metadata.get(group.owner[1], GeniaMap()))
    help_map = _Metadata(group.metadata)
    clauses = []
    for ordinal, record in enumerate(group.records):
        owned = _copy_record(record)
        case = owned.body.case if isinstance(owned.body, ir.IrListTraversalLoop) else owned.body
        arms = tuple(range(len(case.clauses))) if isinstance(case, ir.IrCase) else ()
        clauses.append(_Clause(
            owned.shape, owned.dispatch_key, ordinal, arms,
            (*group.owner, ordinal, owned.span), owned,
        ))
    binding_doc = _doc(binding)
    help_doc = _doc(help_map)
    return _Projection(
        group, group.owner, tuple(clauses), binding,
        binding_doc if binding_doc is not None else group.docstring,
        help_doc if help_doc is not None else group.docstring, help_map,
    )


def prepare_module_completions(module_env: Any, exports: dict) -> tuple:
    """Build private exact-identity associations before the loader publishes a cache entry.

    Only a group actually declared in this module attempt is captured. Re-exports
    require a prior exact-G completion witness; missing/failed origins and old
    escaped identities remain normal exports with no projection or new error.
    No alias hashing/equality, global registry, view construction or user code.
    """
    associations = []
    seen = set()
    for value in exports.values():
        if not isinstance(value, GeniaFunctionGroup) or id(value) in seen or value.owner is None:
            continue
        seen.add(id(value))
        original = (
            value.owner[0] == module_env.module_identity() and value.records
            and all(record.closure.unit_scope() is module_env for record in value.records)
        )
        if original:
            associations.append((value, _capture(value, module_env)))
            continue
        origin = module_env.root().loaded_modules.get(value.owner[0])
        if origin is not None:
            for group, projection in origin._ordinary_completions:
                if group is value:
                    associations.append((value, projection))
                    break
    return tuple(associations)
