"""Genia callable runtime — issues #236, #237.

Defines callable value types (GeniaFunction, GeniaFunctionGroup, TailCall),
the TCO trampoline (eval_with_tco), none-awareness detection helpers, and
invoke_callable — the module-level dispatch entry point used by the evaluator.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

if __package__ in (None, ""):
    import sys
    from pathlib import Path
    _src_root = Path(__file__).resolve().parents[1]
    if str(_src_root) not in sys.path:
        sys.path.insert(0, str(_src_root))
    from genia.ir import (
        IrBlock,
        IrCall,
        IrCase,
        IrNode,
        IrVar,
    )
    from genia.pattern_match import (
        IrPattern,
        PatternOutcomeError,
        match_lambda_pattern,
        pattern_explicitly_handles_none,
        pattern_explicitly_handles_some,
    )
    from genia.environment import Env
    from genia.values import (
        GeniaFlow,
        GeniaMap,
        _merge_metadata_maps,
        _normalize_absence,
        _runtime_type_name,
        is_none,
        truthy,
    )
    from genia.lexer import SourceSpan
else:
    from .ir import (
        IrBlock,
        IrCall,
        IrCase,
        IrNode,
        IrVar,
    )
    from .pattern_match import (
        IrPattern,
        PatternOutcomeError,
        match_lambda_pattern,
        pattern_explicitly_handles_none,
        pattern_explicitly_handles_some,
    )
    from .environment import Env
    from .values import (
        GeniaFlow,
        GeniaMap,
        _merge_metadata_maps,
        _normalize_absence,
        _runtime_type_name,
        is_none,
        truthy,
    )
    from .lexer import SourceSpan


# ---------------------------------------------------------------------------
# Debug hooks (moved from interpreter.py)
# ---------------------------------------------------------------------------

class DebugHooks:
    def before_node(self, node: IrNode, env: Env) -> None:  # noqa: ARG002
        pass

    def after_node(self, node: IrNode, env: Env, result: Any) -> None:  # noqa: ARG002
        pass

    def on_function_enter(
        self,
        fn_name: str,
        args: tuple[Any, ...],
        env: Env,
        span: SourceSpan | None,
    ) -> None:  # noqa: ARG002
        pass

    def on_function_exit(
        self,
        fn_name: str,
        result: Any,
        env: Env,
        span: SourceSpan | None,
    ) -> None:  # noqa: ARG002
        pass


NOOP_DEBUG_HOOKS = DebugHooks()


def _maybe_close_iterable(iterable: Any) -> None:
    close = getattr(iterable, "close", None)
    if callable(close):
        close()


def _finalize_iterable(iterable: Any, *, primary_error: bool) -> None:
    if primary_error:
        try:
            _maybe_close_iterable(iterable)
        except Exception:
            pass
        return
    _maybe_close_iterable(iterable)


class _FusedStage:
    pass


@dataclass(frozen=True)
class _MapStage(_FusedStage):
    mapper: Callable[[Any], Any]
    label = "map"


@dataclass(frozen=True)
class _FilterStage(_FusedStage):
    predicate: Callable[[Any], Any]
    label = "filter"


def _preserve_fused_callback_error(exc: Exception) -> None:
    try:
        setattr(exc, "_genia_preserve_pipeline_error", True)
    except Exception:
        pass


class _FusedFlow(GeniaFlow):
    def __init__(self, upstream: GeniaFlow, stages: list[_FusedStage]):
        self._upstream = upstream
        self._stages = list(stages)

        def _iterator() -> Any:
            items = upstream.consume()
            primary_error = False
            try:
                for item in items:
                    current = item
                    keep = True
                    for stage in self._stages:
                        if isinstance(stage, _MapStage):
                            try:
                                current = stage.mapper(current)
                            except Exception as exc:
                                _preserve_fused_callback_error(exc)
                                raise
                        elif isinstance(stage, _FilterStage):
                            try:
                                keep = truthy(stage.predicate(current))
                            except Exception as exc:
                                _preserve_fused_callback_error(exc)
                                raise
                            if not keep:
                                break
                    if keep:
                        yield current
            except Exception:
                primary_error = True
                raise
            finally:
                if upstream.close_on_early_termination:
                    _finalize_iterable(items, primary_error=primary_error)

        super().__init__(
            _iterator,
            label=self._stages[-1].label,
            close_on_early_termination=upstream.close_on_early_termination,
        )


def _append_fused_stage(source: GeniaFlow, stage: _FusedStage) -> _FusedFlow:
    if isinstance(source, _FusedFlow):
        return _FusedFlow(source._upstream, source._stages + [stage])
    return _FusedFlow(source, [stage])


# ---------------------------------------------------------------------------
# Callable value types
# ---------------------------------------------------------------------------

@dataclass
class GeniaFunctionGroup:
    name: str
    functions: dict[int, "GeniaFunction"] = field(default_factory=dict)
    docstring: str | None = None
    metadata: GeniaMap = field(default_factory=lambda: GeniaMap())

    def add_clause(self, fn: "GeniaFunction") -> None:
        existing = self.functions.get(fn.arity)
        if existing is not None:
            raise TypeError(f"Duplicate function definition: {fn.name}/{fn.arity}")
        self._merge_docstring(fn.docstring)
        self.functions[fn.arity] = fn

    def _merge_docstring(self, candidate: str | None) -> None:
        if candidate is None:
            return
        if self.docstring is None:
            self.docstring = candidate
            return
        if self.docstring != candidate:
            raise TypeError(
                f"Conflicting docstrings for function {self.name}: got {candidate!r}, expected {self.docstring!r}"
            )

    def merge_metadata(self, metadata: GeniaMap) -> None:
        self.metadata = _merge_metadata_maps(self.metadata, metadata)

    def __iter__(self):
        return iter(self.functions)

    def __getitem__(self, key: int) -> "GeniaFunction":
        return self.functions[key]

    def get(self, key: int) -> "GeniaFunction | None":
        return self.functions.get(key)

    def values(self):
        return self.functions.values()

    def sorted_arities(self) -> list[int]:
        return sorted(self.functions)

    def __call__(self, *args: Any) -> Any:
        arity = len(args)
        exact = self.get(arity)
        if exact is not None:
            return exact(*args)
        vararg_matches = [
            candidate
            for candidate in self.values()
            if isinstance(candidate, GeniaFunction)
            and candidate.rest_param is not None
            and arity >= candidate.arity
        ]
        if len(vararg_matches) == 1:
            return vararg_matches[0](*args)
        if len(vararg_matches) > 1:
            candidates = ", ".join(
                f"{self.name}/{candidate.arity}+"
                for candidate in sorted(vararg_matches, key=lambda fn: fn.arity)
            )
            raise TypeError(f"Ambiguous function resolution: {self.name}/{arity}. Matching varargs: {candidates}")
        available = ", ".join(f"{self.name}/{n}" for n in self.sorted_arities())
        raise TypeError(f"No matching function: {self.name}/{arity}. Available: {available}")


@dataclass
class GeniaFunction:
    name: str
    params: list[str]
    rest_param: str | None
    docstring: str | None
    body: IrNode
    closure: Env
    span: SourceSpan | None = None
    debug_hooks: DebugHooks = field(default_factory=lambda: NOOP_DEBUG_HOOKS)
    debug_mode: bool = False
    internal_access: bool = False

    @property
    def arity(self) -> int:
        return len(self.params)

    def __call__(self, *args: Any) -> Any:
        return eval_with_tco(self, args, debug_hooks=self.debug_hooks, debug_mode=self.debug_mode)

    def __repr__(self) -> str:
        if self.rest_param is None:
            return f"<function {self.name}/{self.arity}>"
        return f"<function {self.name}/{self.arity}+>"


@dataclass
class TailCall:
    fn: Any
    args: tuple[Any, ...]


# ---------------------------------------------------------------------------
# TCO trampoline
# ---------------------------------------------------------------------------

def eval_with_tco(
    fn: Any,
    args: tuple[Any, ...],
    debug_hooks: DebugHooks = NOOP_DEBUG_HOOKS,
    debug_mode: bool = False,
) -> Any:
    current_fn = fn
    current_args = args

    while True:
        if isinstance(current_fn, GeniaFunction):
            if current_fn.rest_param is None:
                if len(current_args) != current_fn.arity:
                    raise TypeError(f"{current_fn.name} expected {current_fn.arity} args, got {len(current_args)}")
            elif len(current_args) < current_fn.arity:
                raise TypeError(f"{current_fn.name} expected at least {current_fn.arity} args, got {len(current_args)}")
            frame = Env(current_fn.closure, internal_access=current_fn.internal_access)
            for p, a in zip(current_fn.params, current_args):
                frame.set(p, a)
            if current_fn.rest_param is not None:
                frame.set(current_fn.rest_param, list(current_args[current_fn.arity:]))
            if debug_mode:
                debug_hooks.on_function_enter(current_fn.name, current_args, frame, current_fn.span)
            if __package__ in (None, ""):
                from genia.evaluator import Evaluator
            else:
                from .evaluator import Evaluator
            result = Evaluator(frame, debug_hooks=debug_hooks, debug_mode=debug_mode).eval_function_body(
                current_fn.params,
                current_args,
                current_fn.body,
                current_fn.name,
            )
            if debug_mode:
                debug_hooks.on_function_exit(current_fn.name, result, frame, current_fn.span)
        else:
            result = current_fn(*current_args)

        if isinstance(result, TailCall):
            current_fn = result.fn
            current_args = result.args
            continue
        return result


# ---------------------------------------------------------------------------
# R20 open functions and extensible pattern dispatch
#
# Core IR reuses IrCaseClause/IrPattern verbatim (see
# docs/design/r20-open-functions-syntax-ir-design.md); this section is the
# runtime dispatch algorithm required by
# docs/design/r20-open-functions-contract.md sections 5 (dispatch), 6
# (duplicates), and 4.3 (import-order independence). No process-global
# mutable dispatch table exists: every value below is constructed once, at
# module-load time, from Core IR already produced by lowering.
# ---------------------------------------------------------------------------


class OpenFunctionError(TypeError):
    """Base class for every R20 portable diagnostic identity (contract §8)."""


class OpenFunctionRedeclarationError(OpenFunctionError):
    def __init__(self, interface_key: tuple[str, str]):
        module_id, name = interface_key
        super().__init__(
            f"open-function-redeclaration: {name!r} is already declared open in module {module_id!r}"
        )
        self.interface_key = interface_key


class OpenFunctionTargetNotOpenError(OpenFunctionError):
    def __init__(self, target: Any):
        super().__init__(f"open-function-target-not-open: {target!r} is not an open function interface")
        self.target = target


def _format_open_span(span: Optional[SourceSpan]) -> str:
    """Normalized, host-neutral span rendering (contract §8): a Genia
    source label and line, never a raw host dataclass repr."""
    if span is None:
        return "<unknown>"
    return f"{span.filename}:{span.line}"


class OpenFunctionDuplicateClauseError(OpenFunctionError):
    def __init__(self, interface_key: tuple[str, str], unit_key: Any, shape: tuple, first_span: Any, duplicate_span: Any):
        module_id, name = interface_key
        super().__init__(
            "open-function-duplicate-clause: "
            f"{name} in unit {unit_key!r} has two clauses with an identical dispatch key "
            f"shape={shape!r} (first at {_format_open_span(first_span)}, duplicate at {_format_open_span(duplicate_span)})"
        )
        self.interface_key = interface_key
        self.unit_key = unit_key
        self.shape = shape
        self.first_span = first_span
        self.duplicate_span = duplicate_span


class OpenFunctionDuplicateSelectionError(OpenFunctionError):
    def __init__(self, interface_key: tuple[str, str], unit_key: Any):
        super().__init__(
            f"open-function-duplicate-selection: contribution {unit_key!r} is already selected for {interface_key!r}"
        )
        self.interface_key = interface_key
        self.unit_key = unit_key


class OpenFunctionIncompatibleContributionError(OpenFunctionError):
    def __init__(self, expected_interface_key: tuple[str, str], actual_target: Any):
        super().__init__(
            "open-function-incompatible-contribution: "
            f"expected a contribution targeting {expected_interface_key!r}, got {actual_target!r}"
        )
        self.expected_interface_key = expected_interface_key
        self.actual_target = actual_target


class OpenFunctionVarargsAmbiguityError(OpenFunctionError):
    def __init__(self, interface_key: tuple[str, str], call_arity: int, shapes: list, provenances: list):
        module_id, name = interface_key
        super().__init__(
            f"open-function-varargs-ambiguity: {name}/{call_arity} matches more than one varargs shape "
            f"{sorted(shapes)} contributed by {sorted(provenances)}"
        )
        self.interface_key = interface_key
        self.call_arity = call_arity
        self.shapes = shapes
        self.provenances = provenances


class OpenFunctionClauseAmbiguityError(OpenFunctionError):
    def __init__(self, interface_key: tuple[str, str], call_arity: int, candidate_provenances: list):
        module_id, name = interface_key
        super().__init__(
            f"open-function-clause-ambiguity: {name}/{call_arity} matched clauses in more than one unit "
            f"{sorted(candidate_provenances)}"
        )
        self.interface_key = interface_key
        self.call_arity = call_arity
        self.candidate_provenances = candidate_provenances


class OpenFunctionNoMatchingFunctionError(OpenFunctionError):
    def __init__(self, interface_key: tuple[str, str], call_arity: int):
        module_id, name = interface_key
        super().__init__(f"No matching function: {name}/{call_arity}")
        self.interface_key = interface_key
        self.call_arity = call_arity


class OpenFunctionNoMatchingCaseError(OpenFunctionError):
    def __init__(self, interface_key: tuple[str, str], call_arity: int, args: tuple[Any, ...]):
        module_id, name = interface_key
        if __package__ in (None, ""):
            from genia.evaluator import _format_args_for_diagnostic
        else:
            from .evaluator import _format_args_for_diagnostic
        super().__init__(
            f"No matching case for function {name}/{call_arity} with arguments {_format_args_for_diagnostic(args)}"
        )
        self.interface_key = interface_key
        self.call_arity = call_arity


def _collect_pattern_binders(node: Any, order: list[str]) -> None:
    """Depth-first collection of every IrPatBind/named IrPatRest binder in
    first-occurrence order, walking dataclass fields generically so R20 adds
    no second pattern-traversal mechanism."""
    if node is None:
        return
    if isinstance(node, (list, tuple)):
        for item in node:
            _collect_pattern_binders(item, order)
        return
    if not dataclasses.is_dataclass(node):
        return
    cls_name = type(node).__name__
    if cls_name == "IrPatBind":
        if node.name not in order:
            order.append(node.name)
        return
    if cls_name == "IrPatRest":
        if node.name is not None and node.name not in order:
            order.append(node.name)
        return
    for f in dataclasses.fields(node):
        if f.name == "span":
            continue
        _collect_pattern_binders(getattr(node, f.name), order)


def _structural_key(node: Any, binder_index: dict[str, int]) -> Any:
    """Structural, span-free, alpha-normalized key for a pattern or guard
    node (contract §6). Bound-variable references are renamed to their
    first-occurrence ordinal so binder spelling never affects duplicate
    detection; free references keep their name."""
    if node is None:
        return None
    if isinstance(node, (str, int, float, bool)):
        return node
    if isinstance(node, (list, tuple)):
        return tuple(_structural_key(item, binder_index) for item in node)
    if not dataclasses.is_dataclass(node):
        return repr(node)
    cls_name = type(node).__name__
    if cls_name == "IrVar" and node.name in binder_index:
        return ("BINDREF", binder_index[node.name])
    if cls_name == "IrPatBind" and node.name in binder_index:
        return ("BIND", binder_index[node.name])
    if cls_name == "IrPatRest" and node.name is not None and node.name in binder_index:
        return ("RESTBIND", binder_index[node.name])
    parts: list[Any] = [cls_name]
    for f in dataclasses.fields(node):
        if f.name == "span":
            continue
        parts.append(_structural_key(getattr(node, f.name), binder_index))
    return tuple(parts)


def _clause_shape(pattern: IrPattern) -> tuple[str, int]:
    items = getattr(pattern, "items", None)
    if items and type(items[-1]).__name__ == "IrPatRest":
        return ("varargs", len(items) - 1)
    return ("fixed", len(items) if items is not None else 0)


def _open_dispatch_key(pattern: IrPattern, guard: Optional[IrNode]) -> tuple:
    order: list[str] = []
    _collect_pattern_binders(pattern, order)
    binder_index = {name: i for i, name in enumerate(order)}
    return (
        _clause_shape(pattern),
        _structural_key(pattern, binder_index),
        _structural_key(guard, binder_index) if guard is not None else None,
    )


@dataclass
class OpenClauseRecord:
    """One clause's pattern/guard/body/closure/provenance (contract §7.1).
    Lexical ordinal within its unit is this record's list index — no
    separate ordinal field is stored (design doc §3)."""

    pattern: IrPattern
    guard: Optional[IrNode]
    body: IrNode
    closure: Env
    span: Optional[SourceSpan]
    dispatch_key: tuple = field(init=False)

    def __post_init__(self) -> None:
        self.dispatch_key = _open_dispatch_key(self.pattern, self.guard)


def _check_no_duplicate_clauses(interface_key: tuple[str, str], unit_key: Any, records: list[OpenClauseRecord]) -> None:
    seen: dict[tuple, OpenClauseRecord] = {}
    for record in records:
        existing = seen.get(record.dispatch_key)
        if existing is not None:
            raise OpenFunctionDuplicateClauseError(
                interface_key, unit_key, record.dispatch_key[0], existing.span, record.span
            )
        seen[record.dispatch_key] = record


def _first_unit_match(records: list[OpenClauseRecord], args: tuple[Any, ...]) -> Optional[tuple[OpenClauseRecord, dict]]:
    if __package__ in (None, ""):
        from genia.evaluator import Evaluator
    else:
        from .evaluator import Evaluator
    for record in records:
        evaluator = Evaluator(record.closure)
        match_env = evaluator.match_lambda_pattern(record.pattern, args)
        if match_env is None:
            continue
        if record.guard is not None:
            local = Env(record.closure)
            for k, v in match_env.items():
                local.set(k, v)
            if not truthy(Evaluator(local).eval(record.guard)):
                continue
        return record, match_env
    return None


def _invoke_open_clause(record: OpenClauseRecord, bindings: dict) -> Any:
    if __package__ in (None, ""):
        from genia.evaluator import Evaluator
    else:
        from .evaluator import Evaluator
    local = Env(record.closure)
    for k, v in bindings.items():
        local.set(k, v)
    return Evaluator(local).eval_tail(record.body)


def _dispatch_open(interface_key: tuple[str, str], participating_units: list[tuple[str, Any, list[OpenClauseRecord]]], args: tuple[Any, ...]) -> Any:
    """The contract §5 dispatch algorithm: shape stratum, then unit-local
    first match, then across-unit exactly-one-candidate selection. Import
    order and contribution-selection order never appear in this function —
    only `participating_units` order (irrelevant to the result) and each
    unit's own clause order (relevant, per unit, per contract §4.3)."""
    n = len(args)
    all_entries: list[tuple[int, OpenClauseRecord]] = []
    for unit_index, (_role, _unit_key, records) in enumerate(participating_units):
        for record in records:
            all_entries.append((unit_index, record))

    fixed_matches = [(ui, r) for ui, r in all_entries if r.dispatch_key[0] == ("fixed", n)]
    if fixed_matches:
        participating_entries = fixed_matches
    else:
        varargs_eligible = [
            (ui, r) for ui, r in all_entries if r.dispatch_key[0][0] == "varargs" and r.dispatch_key[0][1] <= n
        ]
        minimums = sorted({r.dispatch_key[0][1] for _, r in varargs_eligible})
        if len(minimums) > 1:
            shapes = sorted({r.dispatch_key[0] for _, r in varargs_eligible})
            provenances = sorted({str(participating_units[ui][1]) for ui, _ in varargs_eligible})
            raise OpenFunctionVarargsAmbiguityError(interface_key, n, shapes, provenances)
        if not varargs_eligible:
            raise OpenFunctionNoMatchingFunctionError(interface_key, n)
        participating_entries = varargs_eligible

    candidates: list[tuple[int, Any, tuple[OpenClauseRecord, dict]]] = []
    for unit_index, (_role, unit_key, _records) in enumerate(participating_units):
        unit_records = [r for ui, r in participating_entries if ui == unit_index]
        try:
            match = _first_unit_match(unit_records, args)
        except PatternOutcomeError as exc:
            return exc.outcome
        if match is not None:
            candidates.append((unit_index, unit_key, match))

    if not candidates:
        raise OpenFunctionNoMatchingCaseError(interface_key, n, args)
    if len(candidates) > 1:
        provenances = sorted(str(unit_key) for _, unit_key, _ in candidates)
        raise OpenFunctionClauseAmbiguityError(interface_key, n, provenances)

    _, _unit_key, (record, bindings) = candidates[0]
    return _invoke_open_clause(record, bindings)


@dataclass
class GeniaOpenContributionUnit:
    """One contributing module's ordered clause set targeting one open
    interface (contract §4.1). Never callable by itself; only participates
    once explicitly selected into a GeniaLinkedOpenFunction."""

    target_interface_key: tuple[str, str]
    declaring_module_id: str
    clauses: list[OpenClauseRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        _check_no_duplicate_clauses(self.target_interface_key, self.declaring_module_id, self.clauses)

    def __repr__(self) -> str:
        return f"<open contribution {self.declaring_module_id} -> {self.target_interface_key[1]}>"


@dataclass
class GeniaOpenFunction:
    """R20 open interface — an identity-bearing ordinary callable whose base
    unit is this module's own ordered clauses (contract §2, §3)."""

    name: str
    module_id: str
    clauses: list[OpenClauseRecord] = field(default_factory=list)
    docstring: Optional[str] = None
    metadata: GeniaMap = field(default_factory=lambda: GeniaMap())
    span: Optional[SourceSpan] = None

    def __post_init__(self) -> None:
        _check_no_duplicate_clauses(self.interface_key, "base", self.clauses)

    @property
    def interface_key(self) -> tuple[str, str]:
        return (self.module_id, self.name)

    def _dispatch_once(self, args: tuple[Any, ...]) -> Any:
        return _dispatch_open(self.interface_key, [("base", "base", self.clauses)], args)

    def __call__(self, *args: Any) -> Any:
        current_args = args
        while True:
            result = self._dispatch_once(current_args)
            if not isinstance(result, TailCall):
                return result
            if result.fn is self:
                current_args = result.args
                continue
            return eval_with_tco(result.fn, result.args)

    def __repr__(self) -> str:
        return f"<open function {self.name}>"


@dataclass
class GeniaLinkedOpenFunction:
    """R20 immutable linked view: one base GeniaOpenFunction plus an
    explicitly selected, order-irrelevant tuple of contribution units
    (contract §4.2, §4.3)."""

    base: GeniaOpenFunction
    units: tuple[GeniaOpenContributionUnit, ...] = ()

    @property
    def interface_key(self) -> tuple[str, str]:
        return self.base.interface_key

    def _dispatch_once(self, args: tuple[Any, ...]) -> Any:
        participating: list[tuple[str, Any, list[OpenClauseRecord]]] = [("base", "base", self.base.clauses)]
        for unit in self.units:
            participating.append(("contribution", unit.declaring_module_id, unit.clauses))
        return _dispatch_open(self.interface_key, participating, args)

    def __call__(self, *args: Any) -> Any:
        current_args = args
        while True:
            result = self._dispatch_once(current_args)
            if not isinstance(result, TailCall):
                return result
            if result.fn is self:
                current_args = result.args
                continue
            return eval_with_tco(result.fn, result.args)

    def __repr__(self) -> str:
        return f"<open function {self.base.name} (linked)>"


def _all_open_clause_records(fn: Any) -> list[OpenClauseRecord]:
    if isinstance(fn, GeniaOpenFunction):
        return list(fn.clauses)
    if isinstance(fn, GeniaLinkedOpenFunction):
        records = list(fn.base.clauses)
        for unit in fn.units:
            records.extend(unit.clauses)
        return records
    return []


# ---------------------------------------------------------------------------
# None-awareness detection
# ---------------------------------------------------------------------------

_NONE_AWARE_PUBLIC_FUNCTIONS = frozenset(
    {
        "reduce",
        "apply",
        "inspect",
        "trace",
        "tap",
        "some",
        "none?",
        "some?",
        "get",
        "get?",
        "map_some",
        "flat_map_some",
        "then_get",
        "then_first",
        "then_nth",
        "then_find",
        "or_else",
        "or_else_with",
        "unwrap_or",
        "absence_reason",
        "absence_context",
        "absence_meta",
        "is_some?",
        "is_none?",
        "cli_option",
        "cli_option_or",
        "map_put",
        "diagnostic_error",
        "diagnostic_skipped",
        "write",
        "writeln",
        "flush",
        "nil?",
        "cons",
        "car",
        "cdr",
        "pair?",
        "null?",
        "empty_env",
        "lookup",
        "define",
        "set",
        "extend",
        "eval",
        "self_evaluating?",
        "symbol_expr?",
        "tagged_list?",
        "quoted_expr?",
        "quasiquoted_expr?",
        "assignment_expr?",
        "lambda_expr?",
        "application_expr?",
        "block_expr?",
        "match_expr?",
        "text_of_quotation",
        "assignment_name",
        "assignment_value",
        "lambda_params",
        "lambda_body",
        "operator",
        "operands",
        "block_expressions",
        "match_branches",
        "branch_pattern",
        "branch_has_guard?",
        "branch_guard",
        "branch_body",
        "apply_dispatch",
        "_match_procedure?",
        "_match_expr",
        "_match_env",
        "_compound_procedure?",
        "_compound_params",
        "_compound_body",
        "_compound_env",
        "_apply_match_procedure",
        "_eval_match_branches",
        "_eval_match_branch",
        "_eval_match_branch_result",
        "_eval_guarded_branch",
        "eval_dispatch",
        "eval_assignment",
        "make_function",
        "make_matcher",
        "eval_operands",
        "eval_block",
        "eval_sequence",
        "tagged_list_impl",
        "syntax_expect_tagged",
        "syntax_pair_nth",
        "syntax_pair_nth_from",
        "syntax_pair_rest",
        "syntax_pair_rest_from",
        "syntax_expect_match_branch",
        "syntax_match_branch_size",
        "syntax_match_branch_size_checked",
        "syntax_proper_list_length",
        "branch_guard_from_size",
        "branch_body_from_size",
    }
)


_SOME_AWARE_PUBLIC_FUNCTIONS = _NONE_AWARE_PUBLIC_FUNCTIONS


def _pattern_explicitly_handles_none(pattern: IrPattern) -> bool:
    return pattern_explicitly_handles_none(pattern)


def _pattern_explicitly_handles_some(pattern: IrPattern) -> bool:
    return pattern_explicitly_handles_some(pattern)


def _callable_case_explicitly_handles_none(body: IrNode) -> bool:
    if isinstance(body, IrCase):
        return any(
            _pattern_explicitly_handles_none(clause.pattern) or _pattern_explicitly_handles_some(clause.pattern)
            for clause in body.clauses
        )
    if isinstance(body, IrBlock) and body.exprs:
        return _callable_case_explicitly_handles_none(body.exprs[-1])
    return False


def _callable_case_explicitly_handles_some(body: IrNode) -> bool:
    if isinstance(body, IrCase):
        return any(_pattern_explicitly_handles_some(clause.pattern) for clause in body.clauses)
    if isinstance(body, IrBlock) and body.exprs:
        return _callable_case_explicitly_handles_some(body.exprs[-1])
    return False


def _closure_lookup(env: Env, name: str) -> Any:
    """Walk the closure chain without triggering autoloads."""
    current: Optional[Env] = env
    while current is not None:
        val = current.values.get(name)
        if val is not None:
            return val
        current = current.parent
    return None


def _body_delegates_to_option_aware(body: IrNode, closure: Optional[Env] = None) -> bool:
    """Return True when the body's final expression delegates to a known Option-aware function.

    When a closure is supplied the lookup extends to Python-native callables that carry
    ``__genia_handles_none__`` or ``__genia_handles_some__``, so public Genia wrappers
    (e.g. ``none?(v) = _none?(v)``) are classified correctly without requiring their
    names to appear in ``_NONE_AWARE_PUBLIC_FUNCTIONS``.
    """
    if isinstance(body, IrCall) and isinstance(body.fn, IrVar):
        name = body.fn.name
        if name in _NONE_AWARE_PUBLIC_FUNCTIONS:
            return True
        if closure is not None:
            callee = _closure_lookup(closure, name)
            if callee is not None and (
                getattr(callee, "__genia_handles_none__", False)
                or getattr(callee, "__genia_handles_some__", False)
            ):
                return True
        return False
    if isinstance(body, IrBlock) and body.exprs:
        return _body_delegates_to_option_aware(body.exprs[-1], closure)
    return False


def _function_explicitly_handles_none(fn: GeniaFunction) -> bool:
    return _callable_case_explicitly_handles_none(fn.body) or _body_delegates_to_option_aware(fn.body, fn.closure)


def _function_explicitly_handles_some(fn: GeniaFunction) -> bool:
    return _callable_case_explicitly_handles_some(fn.body) or _body_delegates_to_option_aware(fn.body, fn.closure)


def _callable_explicitly_handles_none(fn: Any, arity: int, callee_node: Optional[IrNode] = None) -> bool:
    if getattr(fn, "__genia_handles_none__", False):
        return True
    if isinstance(fn, GeniaFunction):
        if fn.name in _NONE_AWARE_PUBLIC_FUNCTIONS:
            return True
        return _function_explicitly_handles_none(fn)
    if isinstance(fn, GeniaFunctionGroup):
        if fn.name in _NONE_AWARE_PUBLIC_FUNCTIONS:
            return True
        candidate = fn.get(arity)
        if candidate is not None:
            if getattr(candidate, "__genia_handles_none__", False):
                return True
            if not isinstance(candidate, GeniaFunction):
                return False
            return _function_explicitly_handles_none(candidate)
        matches = [
            current
            for current in fn.values()
            if isinstance(current, GeniaFunction)
            and current.rest_param is not None
            and arity >= current.arity
        ]
        if len(matches) == 1:
            return _function_explicitly_handles_none(matches[0])
        if isinstance(callee_node, IrVar) and callee_node.name in {"map", "filter", "take", "scan"}:
            return True
        return False
    if isinstance(fn, (GeniaOpenFunction, GeniaLinkedOpenFunction)):
        return any(
            pattern_explicitly_handles_none(record.pattern) or pattern_explicitly_handles_some(record.pattern)
            for record in _all_open_clause_records(fn)
        )
    genia_body = getattr(fn, "__genia_body__", None)
    if genia_body is not None:
        genia_pattern = getattr(fn, "__genia_pattern__", None)
        return (
            (genia_pattern is not None and _pattern_explicitly_handles_none(genia_pattern))
            or _callable_case_explicitly_handles_none(genia_body)
            or _body_delegates_to_option_aware(genia_body)
        )
    return False


def _callable_explicitly_handles_some(fn: Any, arity: int, callee_node: Optional[IrNode] = None) -> bool:
    if getattr(fn, "__genia_handles_some__", False):
        return True
    if isinstance(fn, GeniaFunction):
        if fn.name in _SOME_AWARE_PUBLIC_FUNCTIONS:
            return True
        return _function_explicitly_handles_some(fn)
    if isinstance(fn, GeniaFunctionGroup):
        if fn.name in _SOME_AWARE_PUBLIC_FUNCTIONS:
            return True
        candidate = fn.get(arity)
        if candidate is not None:
            if getattr(candidate, "__genia_handles_some__", False):
                return True
            if not isinstance(candidate, GeniaFunction):
                return False
            return _function_explicitly_handles_some(candidate)
        matches = [
            current
            for current in fn.values()
            if isinstance(current, GeniaFunction)
            and current.rest_param is not None
            and arity >= current.arity
        ]
        if len(matches) == 1:
            return _function_explicitly_handles_some(matches[0])
        return False
    if isinstance(fn, (GeniaOpenFunction, GeniaLinkedOpenFunction)):
        return any(pattern_explicitly_handles_some(record.pattern) for record in _all_open_clause_records(fn))
    genia_body = getattr(fn, "__genia_body__", None)
    if genia_body is not None:
        genia_pattern = getattr(fn, "__genia_pattern__", None)
        return (
            (genia_pattern is not None and _pattern_explicitly_handles_some(genia_pattern))
            or _callable_case_explicitly_handles_some(genia_body)
            or _body_delegates_to_option_aware(genia_body)
        )
    return False


# ---------------------------------------------------------------------------
# Module-level invocation dispatcher — issue #237
# ---------------------------------------------------------------------------

def invoke_callable(
    fn: Any,
    args: list[Any],
    *,
    tail_position: bool,
    callee_node: Optional[IrNode] = None,
    skip_none_propagation: bool = False,
    autoload_resolver: Optional[Callable[[str, int], Any]] = None,
) -> Any:
    """Dispatch a Genia callable value with evaluated args.

    Dispatch order: none-guard → GeniaFunctionGroup → GeniaMap → str → callable.
    Returns TailCall when tail_position=True for GeniaFunctionGroup and plain-callable
    paths. The autoload_resolver callback is consulted at most once for
    GeniaFunctionGroup when arity resolution initially fails.
    """
    if not skip_none_propagation:
        first_none = next((arg for arg in args if is_none(arg)), None)
        if first_none is not None and not _callable_explicitly_handles_none(fn, len(args), callee_node):
            return first_none

    if isinstance(fn, GeniaFunctionGroup):
        if isinstance(callee_node, IrVar) and len(args) >= 1 and isinstance(args[-1], GeniaFlow):
            if callee_node.name == "map" and len(args) == 2:
                mapper = args[0]
                source = args[1]
                return _append_fused_stage(
                    source,
                    _MapStage(
                        lambda item: invoke_callable(
                            mapper,
                            [item],
                            tail_position=False,
                            autoload_resolver=autoload_resolver,
                        )
                    ),
                )

            if callee_node.name == "filter" and len(args) == 2:
                predicate = args[0]
                source = args[1]
                return _append_fused_stage(
                    source,
                    _FilterStage(
                        lambda item: invoke_callable(
                            predicate,
                            [item],
                            tail_position=False,
                            autoload_resolver=autoload_resolver,
                        )
                    ),
                )

            if callee_node.name == "take" and len(args) == 2:
                count = args[0]
                source = args[1]
                if not isinstance(count, int) or isinstance(count, bool):
                    raise TypeError("take expected an integer count as first argument")

                def _take_iterator() -> Any:
                    items = source.consume()
                    if count <= 0:
                        if source.close_on_early_termination:
                            _finalize_iterable(items, primary_error=False)
                        return
                    remaining = count
                    upstream = iter(items)
                    primary_error = False
                    try:
                        while remaining > 0:
                            try:
                                item = next(upstream)
                            except StopIteration:
                                return
                            yield item
                            remaining -= 1
                    except Exception:
                        primary_error = True
                        raise
                    finally:
                        if source.close_on_early_termination:
                            _finalize_iterable(items, primary_error=primary_error)

                return GeniaFlow(_take_iterator, label="take", close_on_early_termination=source.close_on_early_termination)

            if callee_node.name == "drop" and len(args) == 2:
                count = args[0]
                source = args[1]
                if not isinstance(count, int) or isinstance(count, bool):
                    raise TypeError("drop expected an integer count as first argument")

                def _drop_iterator() -> Any:
                    items = source.consume()
                    upstream = iter(items)
                    primary_error = False
                    try:
                        remaining = count
                        while remaining > 0:
                            try:
                                next(upstream)
                            except StopIteration:
                                return
                            remaining -= 1
                        for item in upstream:
                            yield item
                    except Exception:
                        primary_error = True
                        raise
                    finally:
                        if source.close_on_early_termination:
                            _finalize_iterable(items, primary_error=primary_error)

                return GeniaFlow(_drop_iterator, label="drop", close_on_early_termination=source.close_on_early_termination)

        arity = len(args)

        def _resolve_target(functions: GeniaFunctionGroup, call_arity: int) -> Any:
            exact = functions.get(call_arity)
            if exact is not None:
                return exact
            vararg_matches = [
                candidate
                for candidate in functions.values()
                if isinstance(candidate, GeniaFunction)
                and candidate.rest_param is not None
                and call_arity >= candidate.arity
            ]
            if len(vararg_matches) == 1:
                return vararg_matches[0]
            if len(vararg_matches) > 1:
                callee = callee_node.name if isinstance(callee_node, IrVar) else "function"
                candidates = ", ".join(
                    f"{callee}/{candidate.arity}+"
                    for candidate in sorted(vararg_matches, key=lambda f: f.arity)
                )
                raise TypeError(
                    f"Ambiguous function resolution: {callee}/{call_arity}. Matching varargs: {candidates}"
                )
            return None

        target = _resolve_target(fn, arity)

        if target is None and autoload_resolver is not None and isinstance(callee_node, IrVar):
            resolved = autoload_resolver(callee_node.name, arity)
            if resolved is not None:
                fn = resolved
                if isinstance(fn, GeniaFunctionGroup):
                    target = _resolve_target(fn, arity)

        if target is None:
            callee = callee_node.name if isinstance(callee_node, IrVar) else "function"
            available = ", ".join(f"{callee}/{n}" for n in fn.sorted_arities())
            raise TypeError(f"No matching function: {callee}/{arity}. Available: {available}")

        if isinstance(target, GeniaFunction) and tail_position:
            return TailCall(target, tuple(args))
        return _normalize_absence(target(*args))

    if isinstance(fn, GeniaMap):
        arg_count = len(args)
        if arg_count == 1:
            return fn.get(args[0])
        if arg_count == 2:
            key = args[0]
            if fn.has(key):
                return fn.get(key)
            return args[1]
        raise TypeError(f"map callable expected 1 or 2 args, got {arg_count}")

    if isinstance(fn, str):
        arg_count = len(args)
        if arg_count not in (1, 2):
            raise TypeError(f"string projector expected 1 or 2 args, got {arg_count}")
        target_map = args[0]
        if not isinstance(target_map, GeniaMap):
            raise TypeError("string projector expected a map-like target as first argument")
        if arg_count == 2 and not target_map.has(fn):
            return args[1]
        return target_map.get(fn)

    if not callable(fn):
        raise TypeError(f"pipeline stage expected a callable value, received {_runtime_type_name(fn)}")

    if tail_position:
        return TailCall(fn, tuple(args))
    return _normalize_absence(fn(*args))
