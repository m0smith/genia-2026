"""Genia callable runtime — issue #236.

Defines callable value types (GeniaFunction, GeniaFunctionGroup, TailCall),
the TCO trampoline (eval_with_tco), and none-awareness detection helpers.

Evaluator integration (invoke_callable, eval_call, eval_pipeline_stage) remains
in interpreter.py and is out of scope for this module.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

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
        pattern_explicitly_handles_none,
        pattern_explicitly_handles_some,
    )
    from genia.environment import Env
    from genia.values import GeniaMap, _merge_metadata_maps
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
        pattern_explicitly_handles_none,
        pattern_explicitly_handles_some,
    )
    from .environment import Env
    from .values import GeniaMap, _merge_metadata_maps
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
            frame = Env(current_fn.closure)
            for p, a in zip(current_fn.params, current_args):
                frame.set(p, a)
            if current_fn.rest_param is not None:
                frame.set(current_fn.rest_param, list(current_args[current_fn.arity:]))
            if debug_mode:
                debug_hooks.on_function_enter(current_fn.name, current_args, frame, current_fn.span)
            if __package__ in (None, ""):
                from genia.interpreter import Evaluator
            else:
                from .interpreter import Evaluator
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
# None-awareness detection
# ---------------------------------------------------------------------------

_NONE_AWARE_PUBLIC_FUNCTIONS = frozenset(
    {
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
    genia_body = getattr(fn, "__genia_body__", None)
    if genia_body is not None:
        genia_pattern = getattr(fn, "__genia_pattern__", None)
        return (
            (genia_pattern is not None and _pattern_explicitly_handles_some(genia_pattern))
            or _callable_case_explicitly_handles_some(genia_body)
            or _body_delegates_to_option_aware(genia_body)
        )
    return False
