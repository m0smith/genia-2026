"""Genia callable runtime — issues #236, #237.

Defines callable value types (GeniaFunction, GeniaFunctionGroup, TailCall),
the TCO trampoline (eval_with_tco), none-awareness detection helpers, and
invoke_callable — the module-level dispatch entry point used by the evaluator.
"""
from __future__ import annotations

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
        IrListTraversalLoop,
        IrNode,
        IrVar,
    )
    from genia.pattern_match import (
        IrPatBind,
        IrPatRest,
        IrPatTuple,
        IrPattern,
        PatternOutcomeError,
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
    from genia.structural_key import clause_shape, collect_pattern_binders, open_dispatch_key, structural_key
else:
    from .ir import (
        IrBlock,
        IrCall,
        IrCase,
        IrListTraversalLoop,
        IrNode,
        IrVar,
    )
    from .pattern_match import (
        IrPatBind,
        IrPatRest,
        IrPatTuple,
        IrPattern,
        PatternOutcomeError,
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
    from .structural_key import clause_shape, collect_pattern_binders, open_dispatch_key, structural_key


# ---------------------------------------------------------------------------
# Debug hooks (moved from interpreter.py)
# ---------------------------------------------------------------------------

class DebugHooks:
    """No-op debugger observer interface; overrides receive live environments.

    The evaluator decides when hooks run. Callback failures propagate; these
    methods do not alter results themselves.
    """
    def before_node(self, node: IrNode, env: Env) -> None:  # noqa: ARG002
        """Observe the node/environment before evaluation; default does nothing."""
        pass

    def after_node(self, node: IrNode, env: Env, result: Any) -> None:  # noqa: ARG002
        """Observe the evaluated node result; default does nothing."""
        pass

    def on_function_enter(
        self,
        fn_name: str,
        args: tuple[Any, ...],
        env: Env,
        span: SourceSpan | None,
    ) -> None:  # noqa: ARG002
        """Observe a function frame after binding arguments; default does nothing."""
        pass

    def on_function_exit(
        self,
        fn_name: str,
        result: Any,
        env: Env,
        span: SourceSpan | None,
    ) -> None:  # noqa: ARG002
        """Observe successful body output, possibly TailCall; default does nothing."""
        pass


NOOP_DEBUG_HOOKS = DebugHooks()


def _maybe_close_iterable(iterable: Any) -> None:
    """Invoke a callable close attribute if present; lookup/close failures propagate."""
    close = getattr(iterable, "close", None)
    if callable(close):
        close()


def _finalize_iterable(iterable: Any, *, primary_error: bool) -> None:
    """Close the iterable, suppressing Exception only when a primary error exists.

    Otherwise cleanup failures propagate. BaseException is never suppressed.
    """
    if primary_error:
        try:
            _maybe_close_iterable(iterable)
        except Exception:
            pass
        return
    _maybe_close_iterable(iterable)


class _FusedStage:
    """Internal marker for supported fused map/filter stage descriptors."""
    pass


@dataclass(frozen=True)
class _MapStage(_FusedStage):
    """Immutable mapper descriptor; construction does not validate or invoke the callback."""
    mapper: Callable[[Any], Any]
    label = "map"


@dataclass(frozen=True)
class _FilterStage(_FusedStage):
    """Immutable predicate descriptor; truthy determines inclusion only when pulled."""
    predicate: Callable[[Any], Any]
    label = "filter"


def _preserve_fused_callback_error(exc: Exception) -> None:
    """Best-effort mutate an exception with the pipeline-preservation marker.

    Suppress Exception if setting the attribute fails; do not replace the error.
    """
    try:
        setattr(exc, "_genia_preserve_pipeline_error", True)
    except Exception:
        pass


class _FusedFlow(GeniaFlow):
    """Lazy single-use Flow applying ordered map/filter stages over one upstream.

    Construction does not consume source. The final stage supplies the label;
    upstream supplies early-close policy. Callers provide supported descriptors.
    """
    def __init__(self, upstream: GeniaFlow, stages: list[_FusedStage]):
        """Capture upstream and copy a nonempty stage list into a lazy Flow factory.

        Do not invoke callbacks or consume upstream here. Empty stages fail during
        label selection; upstream close policy is inherited.
        """
        self._upstream = upstream
        self._stages = list(stages)

        def _iterator() -> Any:
            """Consume upstream once and transform only demanded items in stage order.

            Map replaces current data; a false filter skips later stages for that item.
            Tag and re-raise callback Exceptions. Follow upstream close policy, preserving
            a primary Exception over cleanup Exception.
            """
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
    """Construct a lazy fused Flow, flattening an existing chain without consuming it.

    Copy stage order and reuse original upstream; do not mutate source.
    Underlying Flow single-use ownership still applies.
    """
    if isinstance(source, _FusedFlow):
        return _FusedFlow(source._upstream, source._stages + [stage])
    return _FusedFlow(source, [stage])


# ---------------------------------------------------------------------------
# Callable value types
# ---------------------------------------------------------------------------

def _record_shape(fn: Any) -> tuple[str, int]:
    """Shape of one group record: ``("fixed", n)`` or ``("varargs", minimum)``.

    Works for `GeniaFunction` records (identifier or pattern headers) and for
    host function records, which expose only `arity` and `rest_param`.
    """
    shape = getattr(fn, "shape", None)
    if shape is not None:
        return shape
    return ("varargs" if getattr(fn, "rest_param", None) is not None else "fixed", fn.arity)


def _is_pattern_record(fn: Any) -> bool:
    """True when `fn` is a pattern/guard-headed record that must be matched, not just bound."""
    return isinstance(fn, GeniaFunction) and (fn.pattern is not None or fn.guard is not None)


_CLAUSE_MISS = object()


def _run_pattern_record(
    record: "GeniaFunction",
    args: tuple[Any, ...],
    debug_hooks: DebugHooks = NOOP_DEBUG_HOOKS,
    debug_mode: bool = False,
) -> Any:
    """Match one pattern-headed record against `args` and run its body on a hit.

    The tuple pattern is matched once in the record's closure, the guard is evaluated
    once in a child frame holding the bindings, and the selected body runs in tail
    position (value or TailCall). A miss (pattern or false guard) returns `_CLAUSE_MISS`
    without running the body; a matcher Outcome is returned as the value. Matcher,
    guard and body failures propagate. Reuses the R20 unit matcher and clause invoker.
    """
    try:
        match = _first_unit_match([record], args, debug_hooks, debug_mode)
    except PatternOutcomeError as exc:
        return exc.outcome
    if match is None:
        return _CLAUSE_MISS
    return _invoke_open_clause(record, match[1], debug_hooks, debug_mode, args)


@dataclass
class GeniaFunctionGroup:
    """Mutable ordinary function container: ordered declaration records plus an arity index.

    `records` is the semantic store in declaration order (first match wins within a shape
    stratum). `functions` is a derived index keyed by required arity that holds the first
    record at that arity; it exists for legacy consumers and is never the record store.
    `owner` is the ``(module identity, defining name)`` provenance of the declaring
    binding, or None for host-created groups. Adding rejects duplicate clause keys and
    conflicting docs; metadata merges separately.
    """
    name: str
    functions: dict[int, "GeniaFunction"] = field(default_factory=dict)
    docstring: str | None = None
    metadata: GeniaMap = field(default_factory=lambda: GeniaMap())
    records: list["GeniaFunction"] = field(default_factory=list, repr=False)
    owner: tuple[str, str] | None = field(default=None, repr=False)
    _complex: bool = field(default=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Derive the record list from a supplied arity index when no records were given."""
        if self.functions and not self.records:
            self.records = list(self.functions.values())
        self._complex = any(_is_pattern_record(r) for r in self.records)

    def add_clause(self, fn: "GeniaFunction") -> None:
        """Reject a duplicate clause key, merge compatible documentation, then store the record.

        Two identifier-header clauses with the same key keep the legacy
        `Duplicate function definition` TypeError; a duplicate involving a pattern or
        guard header raises the R20 duplicate-clause diagnostic with both provenances.
        TypeError on conflicting docs leaves the new record unstored. Metadata is not
        merged here.
        """
        shape = _record_shape(fn)
        for existing in self.records:
            if _record_shape(existing) != shape:
                continue
            if _clause_key(existing) != _clause_key(fn):
                continue
            if _is_pattern_record(existing) or _is_pattern_record(fn):
                module_of = lambda record: record.closure.module_identity() if isinstance(record, GeniaFunction) else "<entry>"  # noqa: E731
                raise OpenFunctionDuplicateClauseError(
                    (module_of(fn), fn.name), "base", shape, getattr(existing, "span", None),
                    getattr(fn, "span", None), module_of(existing), module_of(fn),
                )
            raise TypeError(f"Duplicate function definition: {fn.name}/{fn.arity}")
        self._merge_docstring(fn.docstring)
        self.records.append(fn)
        if fn.arity in self.functions:
            self._complex = True
        else:
            self.functions[fn.arity] = fn
        if _is_pattern_record(fn):
            self._complex = True

    @property
    def is_simple(self) -> bool:
        """True while every record is an identifier header with a distinct required arity.

        Simple groups keep the exact legacy arity-table resolution and diagnostics.
        """
        return not self._complex

    def single_plain_record(self) -> "GeniaFunction | None":
        """The only record when the group is one identifier-header clause, else None.

        Consumers that need one exact signature (route, outbound HTTP, `@test`) use
        this instead of picking a representative from the arity index.
        """
        if len(self.records) == 1 and not _is_pattern_record(self.records[0]):
            return self.records[0]
        return None

    def _merge_docstring(self, candidate: str | None) -> None:
        """Ignore None, adopt first text, or require exact equality with existing text.

        Conflicting documentation raises TypeError without replacing existing text.
        """
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
        """Replace metadata with the governed merged map; merge errors propagate."""
        self.metadata = _merge_metadata_maps(self.metadata, metadata)

    def __iter__(self):
        """Iterate indexed arities in insertion order, not sorted order."""
        return iter(self.functions)

    def __getitem__(self, key: int) -> "GeniaFunction":
        """Return an arity-index entry or raise KeyError when absent."""
        return self.functions[key]

    def get(self, key: int) -> "GeniaFunction | None":
        """Return an arity-index entry or Python None when absent."""
        return self.functions.get(key)

    def values(self):
        """Return the live dictionary view of indexed function entries."""
        return self.functions.values()

    def sorted_arities(self) -> list[int]:
        """Return a fresh ascending list of indexed required arities."""
        return sorted(self.functions)

    def shapes(self) -> list[tuple[str, int]]:
        """Distinct clause shapes, fixed shapes first then varargs, each by ascending arity."""
        return sorted({_record_shape(r) for r in self.records})

    def stratum(self, arity: int, label: str | None = None, *, raise_missing: bool = True) -> list["GeniaFunction"] | None:
        """Records in the shape stratum selected by a call with `arity` arguments.

        Fixed `arity` records win outright (varargs never back them up); otherwise the
        varargs records whose minimum is at most `arity`, which must share one minimum.
        More than one eligible minimum raises the ordinary ambiguity TypeError; no
        eligible shape raises `No matching function` (or returns None when
        `raise_missing` is false). `label` names the callee in diagnostics.
        """
        fixed = [r for r in self.records if _record_shape(r) == ("fixed", arity)]
        if fixed:
            return fixed
        eligible = [
            r for r in self.records
            if _record_shape(r)[0] == "varargs" and _record_shape(r)[1] <= arity
        ]
        name = label if label is not None else self.name
        minima = sorted({_record_shape(r)[1] for r in eligible})
        if len(minima) > 1:
            candidates = ", ".join(f"{name}/{m}+" for m in minima)
            raise TypeError(f"Ambiguous function resolution: {name}/{arity}. Matching varargs: {candidates}")
        if eligible:
            return eligible
        if not raise_missing:
            return None
        raise TypeError(f"No matching function: {name}/{arity}. Available: {self._available_text(name)}")

    def _available_text(self, name: str) -> str:
        """The `Available:` list: arity-sorted for legacy-shaped groups, shape-sorted otherwise."""
        if self.is_simple:
            return ", ".join(f"{name}/{n}" for n in self.sorted_arities())
        return ", ".join(f"{name}/{n}{'+' if kind == 'varargs' else ''}" for kind, n in self.shapes())

    def _dispatch_once(
        self,
        args: tuple[Any, ...],
        debug_hooks: DebugHooks = NOOP_DEBUG_HOOKS,
        debug_mode: bool = False,
        label: str | None = None,
    ) -> Any:
        """Select one record for `args` and run it to a value or a deferred TailCall.

        Identifier-header records always match and are returned as a TailCall so the
        trampoline binds their header frame. Pattern records are matched (and guarded)
        once, in declaration order, within the shape stratum; a matcher Outcome is
        returned as the call's value, and exhausting the stratum is the terminal
        `No matching case` error. Header bodies are never run twice.
        """
        arity = len(args)
        stratum = self.stratum(arity, label)
        if __package__ in (None, ""):
            from genia.evaluator import _format_args_for_diagnostic
        else:
            from .evaluator import _format_args_for_diagnostic
        for record in stratum:
            if not _is_pattern_record(record):
                return TailCall(record, args)
            result = _run_pattern_record(record, args, debug_hooks, debug_mode)
            if result is not _CLAUSE_MISS:
                return result
        name = label if label is not None else self.name
        raise RuntimeError(
            f"No matching case for function {name}/{arity} with arguments {_format_args_for_diagnostic(args)}"
        )

    def __call__(self, *args: Any) -> Any:
        """Resolve and run the record for `args`.

        Simple groups invoke the exact-arity entry, else the sole eligible varargs entry;
        other groups dispatch through the shape stratum and first-match record selection.
        This direct host path does not apply invoke_callable None guards, autoloading
        or result normalization.
        """
        arity = len(args)
        if not self.is_simple:
            first = self.records[0]
            return eval_with_tco(
                self, args, getattr(first, "debug_hooks", NOOP_DEBUG_HOOKS), getattr(first, "debug_mode", False)
            )
        exact = self.get(arity)
        if exact is not None and exact.rest_param is None:
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


def _clause_key(fn: Any) -> Any:
    """Dispatch key of a group record (identifier headers derive theirs from params/rest)."""
    key = getattr(fn, "dispatch_key", None)
    if key is not None:
        return key
    return ("host", id(fn))


@dataclass
class GeniaFunction:
    """Ordinary function record: header, Core IR body and lexical closure.

    An identifier header (`pattern` None) binds `params`/`rest_param` and runs `body`
    in a fresh frame. A pattern header carries the full tuple `pattern` and optional
    `guard`; its `params` is empty, its `rest_param` is the final rest binder's name
    (empty string when the rest is unnamed) and its arity is the pattern's required
    count. Construction does not evaluate or validate the body. Calling uses the
    trampoline with stored debug/internal-access settings.
    """
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
    pattern: IrPattern | None = None
    guard: IrNode | None = None

    def __post_init__(self) -> None:
        """Compute the pattern-header shape once; the structural key is computed on demand."""
        self._shape = clause_shape(self.pattern) if self.pattern is not None else None
        self._dispatch_key: tuple | None = None

    @property
    def shape(self) -> tuple[str, int]:
        """``("fixed", n)`` or ``("varargs", minimum)`` for this record's header."""
        if self._shape is not None:
            return self._shape
        return ("varargs" if self.rest_param is not None else "fixed", len(self.params))

    @property
    def arity(self) -> int:
        """Return the required parameter count, excluding the rest parameter."""
        if self._shape is not None:
            return self._shape[1]
        return len(self.params)

    @property
    def dispatch_key(self) -> tuple:
        """The pure structural key of this header (shape, pattern, guard); computed once.

        An identifier header derives its key from the equivalent all-binder tuple
        pattern, so `f(x)` and `f(y)` collide while `f(x)` and `f(0)` do not.
        """
        if self._dispatch_key is None:
            pattern = self.pattern
            if pattern is None:
                items: list[Any] = [IrPatBind(name) for name in self.params]
                if self.rest_param is not None:
                    items.append(IrPatRest(self.rest_param))
                pattern = IrPatTuple(items)
            self._dispatch_key = open_dispatch_key(pattern, self.guard)
        return self._dispatch_key

    def __call__(self, *args: Any) -> Any:
        """Run the trampoline with stored debug settings; arity/body/hook failures propagate.

        Direct host invocation does not apply invoke_callable None argument guards.
        """
        return eval_with_tco(self, args, debug_hooks=self.debug_hooks, debug_mode=self.debug_mode)

    def __repr__(self) -> str:
        """Render function name/required arity and + for rest parameters, without evaluation."""
        if self.rest_param is None:
            return f"<function {self.name}/{self.arity}>"
        return f"<function {self.name}/{self.arity}+>"


@dataclass
class TailCall:
    """Deferred callee/argument tuple for the next trampoline iteration.

    Construction neither invokes nor validates the callee and transfers no
    resource ownership.
    """
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
    """Run `fn(*args)` to a final value in one flat tail-call loop.

    Inputs: any callable and its argument tuple; `debug_hooks`/`debug_mode`
    apply to `GeniaFunction` frames only.
    Output: the first non-`TailCall` result. A `TailCall` returned by a step
    replaces the current callee and arguments, so self and mutual tail
    recursion across ordinary functions, open interfaces, and linked views
    (R20 contract 5.1) use constant host stack.
    Failure: arity, dispatch, and body errors propagate unchanged.
    """
    current_fn = fn
    current_args = args

    while True:
        if isinstance(current_fn, GeniaFunctionGroup):
            result = current_fn._dispatch_once(current_args, debug_hooks, debug_mode)
        elif isinstance(current_fn, GeniaFunction) and (current_fn.pattern is not None or current_fn.guard is not None):
            if current_fn.rest_param is None:
                if len(current_args) != current_fn.arity:
                    raise TypeError(f"{current_fn.name} expected {current_fn.arity} args, got {len(current_args)}")
            elif len(current_args) < current_fn.arity:
                raise TypeError(f"{current_fn.name} expected at least {current_fn.arity} args, got {len(current_args)}")
            result = _run_pattern_record(current_fn, current_args, debug_hooks, debug_mode)
            if result is _CLAUSE_MISS:
                if __package__ in (None, ""):
                    from genia.evaluator import _format_args_for_diagnostic
                else:
                    from .evaluator import _format_args_for_diagnostic
                raise RuntimeError(
                    f"No matching case for function {current_fn.name}/{len(current_args)} "
                    f"with arguments {_format_args_for_diagnostic(current_args)}"
                )
        elif isinstance(current_fn, GeniaFunction):
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
        elif isinstance(current_fn, (GeniaOpenFunction, GeniaLinkedOpenFunction)):
            result = current_fn._dispatch_once(current_args)
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
    """An open interface was declared over a name that is already bound."""
    def __init__(self, interface_key: tuple[str, str], existing: str = "open interface"):
        """Store interface provenance and the redeclaration diagnostic; do not raise here.

        `existing` says what already holds the name: "open interface" (the
        default), "ordinary function", or "non-function value"; only the
        wording depends on it, the identity prefix is always the same."""
        module_id, name = interface_key
        phrase = {
            "open interface": "already declared open",
            "ordinary function": "already defined as an ordinary function",
        }.get(existing, "already bound to a non-function value")
        super().__init__(f"open-function-redeclaration: {name!r} is {phrase} in module {module_id!r}")
        self.interface_key = interface_key
        self.existing = existing


class FunctionDeclarationNotOwnerError(OpenFunctionError):
    """An ordinary declaration named a binding that refers to a group another binding owns."""
    def __init__(self, declared: str, shape: tuple[str, int], owner_module: str, owner_name: str, foreign: bool):
        """Build the path- and span-free diagnostic from names and the owner's canonical module identity.

        `shape` is the declared clause shape (rendered `n` or `n+`); `foreign` selects the
        owning-module wording over the same-scope wording. No value is rendered."""
        kind, count = shape
        label = f"{declared}/{count}{'+' if kind == 'varargs' else ''}"
        where = f"owned by module {owner_module!r}" if foreign else "declared by another binding in this scope"
        super().__init__(
            f"function-declaration-not-owner: cannot declare {label}: "
            f"{declared!r} refers to function {owner_name!r} {where}"
        )
        self.declared = declared
        self.owner_module = owner_module
        self.owner_name = owner_name
        self.foreign = foreign


class OpenFunctionTargetNotOpenError(OpenFunctionError):
    """An extension target is not an open interface."""
    def __init__(self, target: Any):
        """Retain target and render its repr in the diagnostic; construction does not raise."""
        super().__init__(f"open-function-target-not-open: {target!r} is not an open function interface")
        self.target = target


def _format_open_span(span: Optional[SourceSpan], module_identity: str = "<entry>") -> str:
    """Normalized, host-neutral span rendering (contract §8).

    The entry program keeps the source label it was given; a clause declared in
    an imported module renders as that module's identity, so a resolved
    filesystem path never appears. Never a raw host dataclass repr."""
    if span is None:
        return "<unknown>"
    if module_identity != "<entry>":
        return f"{module_identity}:{span.line}"
    return f"{span.filename}:{span.line}"


class OpenFunctionDuplicateClauseError(OpenFunctionError):
    """Two clauses in one unit share an alpha-normalized dispatch key."""
    def __init__(
        self,
        interface_key: tuple[str, str],
        unit_key: Any,
        shape: tuple,
        first_span: Any,
        duplicate_span: Any,
        first_module: str = "<entry>",
        duplicate_module: str = "<entry>",
    ):
        """Retain interface/unit/shape and both spans; render spans by source label or module identity.

        `first_module`/`duplicate_module` are the declaring module identities of
        the two clauses. Callers supply validated provenance and shape; do not
        inspect clause bodies."""
        module_id, name = interface_key
        super().__init__(
            "open-function-duplicate-clause: "
            f"{name} in unit {unit_key!r} has two clauses with an identical dispatch key "
            f"shape={shape!r} (first at {_format_open_span(first_span, first_module)}, "
            f"duplicate at {_format_open_span(duplicate_span, duplicate_module)})"
        )
        self.interface_key = interface_key
        self.unit_key = unit_key
        self.shape = shape
        self.first_span = first_span
        self.duplicate_span = duplicate_span


class OpenFunctionDuplicateSelectionError(OpenFunctionError):
    """The same contribution unit was selected twice for one interface."""
    def __init__(self, interface_key: tuple[str, str], unit_key: Any):
        """Retain interface/unit provenance and build the duplicate-selection diagnostic."""
        super().__init__(
            f"open-function-duplicate-selection: contribution {unit_key!r} is already selected for {interface_key!r}"
        )
        self.interface_key = interface_key
        self.unit_key = unit_key


class OpenFunctionIncompatibleContributionError(OpenFunctionError):
    """A selected contribution does not target the expected open interface."""
    def __init__(self, expected_interface_key: tuple[str, str], actual_target: Any):
        """Retain expected interface and actual target and format the incompatibility diagnostic."""
        super().__init__(
            "open-function-incompatible-contribution: "
            f"expected a contribution targeting {expected_interface_key!r}, got {actual_target!r}"
        )
        self.expected_interface_key = expected_interface_key
        self.actual_target = actual_target


class OpenFunctionVarargsAmbiguityError(OpenFunctionError):
    """Eligible clauses have more than one distinct varargs minimum."""
    def __init__(self, interface_key: tuple[str, str], call_arity: int, shapes: list, provenances: list):
        """Retain supplied shapes/provenances and render sorted copies for deterministic text.

        Inputs must be sortable; construction does not mutate their lists."""
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
    """More than one unit supplies a matching clause in the selected stratum."""
    def __init__(self, interface_key: tuple[str, str], call_arity: int, candidate_provenances: list):
        """Retain supplied candidate provenance; sort a copy for diagnostic rendering."""
        module_id, name = interface_key
        super().__init__(
            f"open-function-clause-ambiguity: {name}/{call_arity} matched clauses in more than one unit "
            f"{sorted(candidate_provenances)}"
        )
        self.interface_key = interface_key
        self.call_arity = call_arity
        self.candidate_provenances = candidate_provenances


class OpenFunctionNoMatchingFunctionError(OpenFunctionError):
    """No clause shape accepts the call argument count."""
    def __init__(self, interface_key: tuple[str, str], call_arity: int, available: Optional[list] = None):
        """Store interface/arity with the existing No matching function diagnostic family.

        `available` is the distinct clause shapes (`("fixed", n)` or
        `("varargs", n)`); when given they are listed in the ordinary-function
        format, fixed shapes first (`Available: f/1, f/2+`)."""
        module_id, name = interface_key
        text = f"No matching function: {name}/{call_arity}"
        if available:
            listed = ", ".join(
                f"{name}/{n}{'+' if kind == 'varargs' else ''}" for kind, n in sorted(available)
            )
            text += f". Available: {listed}"
        super().__init__(text)
        self.interface_key = interface_key
        self.call_arity = call_arity
        self.available = list(available or [])


class OpenFunctionNoMatchingCaseError(OpenFunctionError):
    """The selected shape stratum has no matching pattern/guard candidate."""
    def __init__(self, interface_key: tuple[str, str], call_arity: int, args: tuple[Any, ...]):
        """Store interface/arity and render args using governed evaluator diagnostics.

        Arguments are used for text, not retained as an exception attribute."""
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


_collect_pattern_binders = collect_pattern_binders
_structural_key = structural_key
_clause_shape = clause_shape
_open_dispatch_key = open_dispatch_key


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
        """Cache the duplicate-detection key without evaluating pattern, guard or body.

        Callers must keep pattern/guard consistent with this cached key afterward."""
        self.dispatch_key = _open_dispatch_key(self.pattern, self.guard)


def _check_no_duplicate_clauses(interface_key: tuple[str, str], unit_key: Any, records: list[OpenClauseRecord]) -> None:
    """Reject the first repeated cached dispatch key within one unit.

    Raise OpenFunctionDuplicateClauseError with both source spans; do not mutate
    records, compare bodies, or check duplicates across different units."""
    seen: dict[tuple, OpenClauseRecord] = {}
    for record in records:
        existing = seen.get(record.dispatch_key)
        if existing is not None:
            raise OpenFunctionDuplicateClauseError(
                interface_key,
                unit_key,
                record.dispatch_key[0],
                existing.span,
                record.span,
                existing.closure.module_identity(),
                record.closure.module_identity(),
            )
        seen[record.dispatch_key] = record


def _first_unit_match(
    records: list[Any],
    args: tuple[Any, ...],
    debug_hooks: DebugHooks = NOOP_DEBUG_HOOKS,
    debug_mode: bool = False,
) -> Optional[tuple[Any, dict]]:
    """Return the first matching record and bindings in supplied lexical order.

    Match in each record closure; evaluate a matched guard in a fresh child Env.
    False guards continue; return Python None on exhaustion. Never execute bodies.
    Matcher/guard failures propagate, including PatternOutcomeError."""
    if __package__ in (None, ""):
        from genia.evaluator import Evaluator
    else:
        from .evaluator import Evaluator
    for record in records:
        evaluator = Evaluator(record.closure, debug_hooks, debug_mode)
        match_env = evaluator.match_lambda_pattern(record.pattern, args)
        if match_env is None:
            continue
        if record.guard is not None:
            local = Env(record.closure)
            for k, v in match_env.items():
                local.set(k, v)
            if not truthy(Evaluator(local, debug_hooks, debug_mode).eval(record.guard)):
                continue
        return record, match_env
    return None


def _invoke_open_clause(
    record: Any,
    bindings: dict,
    debug_hooks: DebugHooks = NOOP_DEBUG_HOOKS,
    debug_mode: bool = False,
    args: Optional[tuple[Any, ...]] = None,
) -> Any:
    """Evaluate one selected body in tail position in a fresh child of its closure.

    Bind supplied matcher results locally; return value or TailCall unchanged.
    Body failures propagate. This helper neither selects clauses nor trampolines."""
    if __package__ in (None, ""):
        from genia.evaluator import Evaluator
    else:
        from .evaluator import Evaluator
    local = Env(record.closure)
    for k, v in bindings.items():
        local.set(k, v)
    if debug_mode and args is not None:
        debug_hooks.on_function_enter(record.name, args, local, record.span)
    result = Evaluator(local, debug_hooks, debug_mode).eval_tail(record.body)
    if debug_mode and args is not None:
        debug_hooks.on_function_exit(record.name, result, local, record.span)
    return result


def _dispatch_open(interface_key: tuple[str, str], participating_units: list[tuple[str, Any, list[OpenClauseRecord]]], args: tuple[Any, ...]) -> Any:
    """Select a shape, find one candidate per unit, then execute exactly one body.

    Fixed arity excludes varargs even when fixed patterns miss. Otherwise one
    eligible varargs minimum is required, with no largest-minimum preference.
    Preserve each unit's lexical first-match order; multiple matching units
    raise clause ambiguity, never resolved by specificity or selection order.

    Matchers and guards run before body selection. Convert PatternOutcomeError
    from unit matching to its Outcome; other matcher/guard/body errors propagate.
    No eligible shape raises NoMatchingFunction; no candidate raises NoMatchingCase.
    Return body value or TailCall, leaving trampoline execution to the caller.

    Callers supply compatible, unique units with construction-time duplicate
    checks already complete. Successful clause selection is order-independent;
    this helper does not promise guard effect or failure evaluation order.
    """
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
            raise OpenFunctionNoMatchingFunctionError(
                interface_key, n, sorted({r.dispatch_key[0] for _, r in all_entries})
            )
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
        """Validate same-unit duplicate keys at construction; no body execution.

        Target compatibility is checked by linking, not by this constructor."""
        _check_no_duplicate_clauses(self.target_interface_key, self.declaring_module_id, self.clauses)

    def __repr__(self) -> str:
        """Render module and target name without exposing or executing clause bodies."""
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
        """Reject duplicate base dispatch keys at construction, without invoking clauses."""
        _check_no_duplicate_clauses(self.interface_key, "base", self.clauses)

    @property
    def interface_key(self) -> tuple[str, str]:
        """Return canonical declaring-module/name provenance supplied by module construction."""
        return (self.module_id, self.name)

    def _dispatch_once(self, args: tuple[Any, ...]) -> Any:
        """Dispatch only base clauses once; return a value or deferred TailCall.

        Shape/pattern/ambiguity/body failures follow _dispatch_open; no trampoline here."""
        return _dispatch_open(self.interface_key, [("base", "base", self.clauses)], args)

    def __call__(self, *args: Any) -> Any:
        """Dispatch the base clauses for `args` and return the final value.

        Runs through the shared tail-call loop, so tail calls out of a
        selected clause (to this or any other callable) do not nest host
        frames. Dispatch failures use the open-function diagnostics.
        """
        return eval_with_tco(self, args)

    def __repr__(self) -> str:
        """Render the interface name without evaluating or exposing its clauses."""
        return f"<open function {self.name}>"


@dataclass
class GeniaLinkedOpenFunction:
    """R20 immutable linked view: one base GeniaOpenFunction plus an
    explicitly selected, order-irrelevant tuple of contribution units
    (contract §4.2, §4.3).

    LANGUAGE CONTRACT: selection is immutable from Genia source.
    PYTHON REFERENCE HOST: this dataclass is not frozen; module/linking code owns
    construction and validates targets/duplicate selections before dispatch.
    Do not mutate its base, units or referenced clause records afterward.
    """

    base: GeniaOpenFunction
    units: tuple[GeniaOpenContributionUnit, ...] = ()

    @property
    def interface_key(self) -> tuple[str, str]:
        """Return the base interface key; selection does not create a new provenance key."""
        return self.base.interface_key

    def _dispatch_once(self, args: tuple[Any, ...]) -> Any:
        """Dispatch base and explicitly selected units once, without mutating selection.

        Callers supply already-validated compatible, unique units. Return value or
        TailCall; shape/pattern/ambiguity/body failures follow _dispatch_open."""
        participating: list[tuple[str, Any, list[OpenClauseRecord]]] = [("base", "base", self.base.clauses)]
        for unit in self.units:
            participating.append(("contribution", unit.declaring_module_id, unit.clauses))
        return _dispatch_open(self.interface_key, participating, args)

    def __call__(self, *args: Any) -> Any:
        """Dispatch base plus selected contribution clauses for `args`.

        Returns the final value through the shared tail-call loop, so a tail
        call out of a selected clause does not nest host frames. The view
        stays immutable; dispatch failures use the open-function diagnostics.
        """
        return eval_with_tco(self, args)

    def __repr__(self) -> str:
        """Render base name and linked marker without invoking or listing contributions."""
        return f"<open function {self.base.name} (linked)>"


def _all_open_clause_records(fn: Any) -> list[OpenClauseRecord]:
    """Return a fresh list of record references: base first, then supplied unit order.

    Return an empty list for other values; do not select, sort, copy or mutate records."""
    if isinstance(fn, GeniaOpenFunction):
        return list(fn.clauses)
    if isinstance(fn, GeniaLinkedOpenFunction):
        records = list(fn.base.clauses)
        for unit in fn.units:
            records.extend(unit.clauses)
        return records
    return []


def _open_stratum_records(fn: Any, arity: int) -> list[OpenClauseRecord]:
    """Clause records of an open function or linked view in the shape stratum
    that a call with `arity` arguments selects (contract 5 step 1).

    Output: the fixed-`arity` records of the base and every selected unit, else
    every varargs record whose minimum is at most `arity` (all of them when the
    stratum is ambiguous, since dispatch reports that). Never raises.
    """
    records = _all_open_clause_records(fn)
    fixed = [r for r in records if r.dispatch_key[0] == ("fixed", arity)]
    if fixed:
        return fixed
    return [r for r in records if r.dispatch_key[0][0] == "varargs" and r.dispatch_key[0][1] <= arity]


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
    """Delegate None-awareness classification to the shared pattern matcher."""
    return pattern_explicitly_handles_none(pattern)


def _pattern_explicitly_handles_some(pattern: IrPattern) -> bool:
    """Delegate Some-awareness classification to the shared pattern matcher."""
    return pattern_explicitly_handles_some(pattern)


def _callable_case_explicitly_handles_none(body: IrNode) -> bool:
    """Recognize explicit None or Some handling in a final IrCase.

    For a block recurse only into its last expression; other forms return False.
    Do not evaluate guards or bodies.
    """
    if isinstance(body, IrCase):
        return any(
            _pattern_explicitly_handles_none(clause.pattern) or _pattern_explicitly_handles_some(clause.pattern)
            for clause in body.clauses
        )
    if isinstance(body, IrListTraversalLoop) and body.case is not None:
        return _callable_case_explicitly_handles_none(body.case)
    if isinstance(body, IrBlock) and body.exprs:
        return _callable_case_explicitly_handles_none(body.exprs[-1])
    return False


def _callable_case_explicitly_handles_some(body: IrNode) -> bool:
    """Recognize Some handling in a final IrCase or final block expression.

    Other forms return False; guards/bodies are not evaluated.
    """
    if isinstance(body, IrCase):
        return any(_pattern_explicitly_handles_some(clause.pattern) for clause in body.clauses)
    if isinstance(body, IrListTraversalLoop) and body.case is not None:
        return _callable_case_explicitly_handles_some(body.case)
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
    """Classify final case patterns or Option-aware delegation without invoking the function.

    Closure lookup does not autoload.
    """
    return _callable_case_explicitly_handles_none(fn.body) or _body_delegates_to_option_aware(fn.body, fn.closure)


def _function_explicitly_handles_some(fn: GeniaFunction) -> bool:
    """Classify Some case patterns or Option-aware delegation without invoking the function.

    Closure lookup does not autoload.
    """
    return _callable_case_explicitly_handles_some(fn.body) or _body_delegates_to_option_aware(fn.body, fn.closure)


def _stratum_resolvable(group: GeniaFunctionGroup, arity: int) -> bool:
    """Whether the shape stratum for `arity` is unambiguous; awareness checks never raise."""
    minima = {
        _record_shape(r)[1]
        for r in group.records
        if _record_shape(r)[0] == "varargs" and _record_shape(r)[1] <= arity
    }
    return len(minima) <= 1 or any(_record_shape(r) == ("fixed", arity) for r in group.records)


def _record_handles_none(record: Any) -> bool:
    """Whether one group record lets a `none` argument reach it (pattern, case body or delegation)."""
    if getattr(record, "__genia_handles_none__", False):
        return True
    if not isinstance(record, GeniaFunction):
        return False
    if _is_pattern_record(record):
        return (
            pattern_explicitly_handles_none(record.pattern)
            or pattern_explicitly_handles_some(record.pattern)
            or _callable_case_explicitly_handles_none(record.body)
            or _body_delegates_to_option_aware(record.body, record.closure)
        )
    return _function_explicitly_handles_none(record)


def _record_handles_some(record: Any) -> bool:
    """Whether one group record lets a `some(...)` argument reach it."""
    if getattr(record, "__genia_handles_some__", False):
        return True
    if not isinstance(record, GeniaFunction):
        return False
    if _is_pattern_record(record):
        return (
            pattern_explicitly_handles_some(record.pattern)
            or _callable_case_explicitly_handles_some(record.body)
            or _body_delegates_to_option_aware(record.body, record.closure)
        )
    return _function_explicitly_handles_some(record)


def _callable_explicitly_handles_none(fn: Any, arity: int, callee_node: Optional[IrNode] = None) -> bool:
    """Whether calling `fn` with `arity` arguments lets a `none` argument reach it.

    Output: True when the resolved callable explicitly handles none/some in a
    pattern, a case body, or by delegating to an Option-aware callee; False
    means `invoke_callable` returns the `none` unchanged. Ordinary groups are
    judged by the arity-resolved entry; open functions and linked views by the
    clauses of the selected shape stratum across all selected units (R20
    contract 5.2). Never raises or runs user code.
    """
    if getattr(fn, "__genia_handles_none__", False):
        return True
    if isinstance(fn, GeniaFunction):
        if fn.name in _NONE_AWARE_PUBLIC_FUNCTIONS:
            return True
        return _function_explicitly_handles_none(fn)
    if isinstance(fn, GeniaFunctionGroup):
        if fn.name in _NONE_AWARE_PUBLIC_FUNCTIONS:
            return True
        if not fn.is_simple:
            stratum = fn.stratum(arity, raise_missing=False) if _stratum_resolvable(fn, arity) else None
            if stratum:
                return any(_record_handles_none(record) for record in stratum)
            return isinstance(callee_node, IrVar) and callee_node.name in {"map", "filter", "take", "scan"}
        candidate = fn.get(arity)
        if candidate is not None and candidate.rest_param is None:
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
            pattern_explicitly_handles_none(record.pattern)
            or pattern_explicitly_handles_some(record.pattern)
            or _callable_case_explicitly_handles_none(record.body)
            or _body_delegates_to_option_aware(record.body, record.closure)
            for record in _open_stratum_records(fn, arity)
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
    """Whether calling `fn` with `arity` arguments lets a `some(...)` value reach it.

    Same resolution as `_callable_explicitly_handles_none`, but only `some`
    patterns, `some`-aware case bodies, and Option-aware delegation count; a
    False answer means the pipeline unwraps the `some` before the call.
    """
    if getattr(fn, "__genia_handles_some__", False):
        return True
    if isinstance(fn, GeniaFunction):
        if fn.name in _SOME_AWARE_PUBLIC_FUNCTIONS:
            return True
        return _function_explicitly_handles_some(fn)
    if isinstance(fn, GeniaFunctionGroup):
        if fn.name in _SOME_AWARE_PUBLIC_FUNCTIONS:
            return True
        if not fn.is_simple:
            stratum = fn.stratum(arity, raise_missing=False) if _stratum_resolvable(fn, arity) else None
            return bool(stratum) and any(_record_handles_some(record) for record in stratum)
        candidate = fn.get(arity)
        if candidate is not None and candidate.rest_param is None:
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
        return any(
            pattern_explicitly_handles_some(record.pattern)
            or _callable_case_explicitly_handles_some(record.body)
            or _body_delegates_to_option_aware(record.body, record.closure)
            for record in _open_stratum_records(fn, arity)
        )
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

    Unless propagation is skipped or the callee is absence-aware, return the
    first None Outcome argument unchanged before resolution. This helper does
    not unwrap Some arguments or implement pipeline-wide Err propagation.

    Groups recognize named Flow map/filter/take/drop adapters first, returning
    lazy Flows. Otherwise prefer exact arity then one eligible varargs entry;
    ambiguity raises TypeError. Consult autoload_resolver at most once for an
    unresolved IrVar callee; it must return a compatible group or None.

    Tail-position group calls defer only GeniaFunction targets; generic callable
    calls defer via TailCall. Non-tail function results normalize legacy absence.
    Map lookup/string-key projection return values/defaults immediately without
    tail deferral, require one or two arguments, and string projection requires
    GeniaMap. Noncallables raise TypeError; callback/body/resolver failures
    propagate. Arguments have already been evaluated.
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
                    """Consume source once and yield at most count items without an extra pull.

                    Nonpositive counts consume the Flow but pull no items. Follow source close
                    policy, preserving primary Exception over cleanup Exception.
                    """
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
                    """Consume source once, skip positive count items, then yield the remainder.

                    Nonpositive counts skip nothing. Follow source close policy, preserving
                    primary Exception over cleanup Exception.
                    """
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

        if not fn.is_simple:
            label = callee_node.name if isinstance(callee_node, IrVar) else fn.name
            if fn.stratum(arity, label, raise_missing=False) is None and autoload_resolver is not None and isinstance(callee_node, IrVar):
                resolved = autoload_resolver(callee_node.name, arity)
                if isinstance(resolved, GeniaFunctionGroup):
                    fn = resolved
            if not fn.is_simple:
                fn.stratum(arity, label)
                if tail_position:
                    return TailCall(fn, tuple(args))
                return _normalize_absence(fn(*args))

        def _resolve_target(functions: GeniaFunctionGroup, call_arity: int) -> Any:
            """Return exact arity or a sole eligible varargs entry; return None if absent.

            Multiple varargs raise TypeError with sorted candidates. No autoloading,
            invocation or mutation occurs.
            """
            exact = functions.get(call_arity)
            if exact is not None and exact.rest_param is None:
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
                callee = callee_node.name if isinstance(callee_node, IrVar) else functions.name
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
            callee = callee_node.name if isinstance(callee_node, IrVar) else fn.name
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
