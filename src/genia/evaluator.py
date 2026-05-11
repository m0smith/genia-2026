"""Evaluator core: Evaluator class and tightly coupled helpers.

Extracted for issue #243. No logic changes.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional

if __package__ in (None, ""):
    import sys
    from pathlib import Path
    _src_root = Path(__file__).resolve().parents[1]
    if str(_src_root) not in sys.path:
        sys.path.insert(0, str(_src_root))
    from genia.utf8 import format_debug, format_display
    from genia.environment import Env
    from genia.errors import GeniaQuietBrokenPipe
    from genia.ast_nodes import (
        Assign, Binary, Block, Boolean, Call, CaseClause, CaseExpr, Delay,
        GlobPattern, Lambda, ListLiteral, ListPattern, MapLiteral, MapPattern,
        Nil, Node, NoneOption, Number, QuasiQuote, Quote, RestPattern,
        SomePattern, Spread, String, SymbolLiteral, TuplePattern, Unary,
        Unquote, UnquoteSplicing, Var, WildcardPattern,
    )
    from genia.ir import (
        IrAnnotation, IrAssign, IrBinary, IrBlock, IrCall, IrCase, IrDelay,
        IrExprStmt, IrFuncDef, IrImport, IrLambda, IrList, IrListTraversalLoop,
        IrLiteral, IrMap, IrNode, IrOptionNone, IrOptionSome, IrPipeline,
        IrQuote, IrQuasiQuote, IrShellStage, IrSpread, IrUnary, IrUnquote,
        IrUnquoteSplicing, IrVar,
    )
    from genia.pattern_match import (
        IrPatBind, IrPatGlob, IrPatList, IrPatLiteral, IrPatMap, IrPatNone,
        IrPatRest, IrPatSome, IrPatTuple, IrPatWildcard, IrPattern,
        compile_glob_pattern, match_lambda_pattern, match_pattern,
        match_pattern_atom,
    )
    from genia.values import (
        OPTION_NONE, _is_nil_none, _merge_metadata_maps, _runtime_type_name, GeniaFlow, GeniaMap, GeniaOptionNone,
        GeniaOptionSome, GeniaPair, GeniaSymbol, ModuleValue, is_none,
        make_none, symbol, truthy,
    )
    from genia.callable import (
        DebugHooks, NOOP_DEBUG_HOOKS, GeniaFunction, invoke_callable as _invoke_callable,
        _callable_explicitly_handles_some,
    )
    from genia.lowering import lower_node, _lambda_pattern_is_simple_parameter_shape
else:
    from .utf8 import format_debug, format_display
    from .environment import Env
    from .errors import GeniaQuietBrokenPipe
    from .ast_nodes import (
        Assign, Binary, Block, Boolean, Call, CaseClause, CaseExpr, Delay,
        GlobPattern, Lambda, ListLiteral, ListPattern, MapLiteral, MapPattern,
        Nil, Node, NoneOption, Number, QuasiQuote, Quote, RestPattern,
        SomePattern, Spread, String, SymbolLiteral, TuplePattern, Unary,
        Unquote, UnquoteSplicing, Var, WildcardPattern,
    )
    from .ir import (
        IrAnnotation, IrAssign, IrBinary, IrBlock, IrCall, IrCase, IrDelay,
        IrExprStmt, IrFuncDef, IrImport, IrLambda, IrList, IrListTraversalLoop,
        IrLiteral, IrMap, IrNode, IrOptionNone, IrOptionSome, IrPipeline,
        IrQuote, IrQuasiQuote, IrShellStage, IrSpread, IrUnary, IrUnquote,
        IrUnquoteSplicing, IrVar,
    )
    from .pattern_match import (
        IrPatBind, IrPatGlob, IrPatList, IrPatLiteral, IrPatMap, IrPatNone,
        IrPatRest, IrPatSome, IrPatTuple, IrPatWildcard, IrPattern,
        compile_glob_pattern, match_lambda_pattern, match_pattern,
        match_pattern_atom,
    )
    from .values import (
        OPTION_NONE, _is_nil_none, _merge_metadata_maps, _runtime_type_name, GeniaFlow, GeniaMap, GeniaOptionNone,
        GeniaOptionSome, GeniaPair, GeniaSymbol, ModuleValue, is_none,
        make_none, symbol, truthy,
    )
    from .callable import (
        DebugHooks, NOOP_DEBUG_HOOKS, GeniaFunction, invoke_callable as _invoke_callable,
        _callable_explicitly_handles_some,
    )
    from .lowering import lower_node, _lambda_pattern_is_simple_parameter_shape

QUOTE_OPERATOR_SYMBOLS = {
    "PLUS": "+",
    "MINUS": "-",
    "STAR": "*",
    "SLASH": "/",
    "PERCENT": "%",
    "LT": "<",
    "LE": "<=",
    "GT": ">",
    "GE": ">=",
    "EQEQ": "==",
    "NE": "!=",
    "AND": "&&",
    "OR": "||",
    "PIPE_FWD": "|>",
    "BANG": "!",
}


def quote_node(node: Node) -> Any:
    def quoted_list(items: list[Any]) -> Any:
        result: Any = OPTION_NONE
        for item in reversed(items):
            result = GeniaPair(item, result)
        return result

    if isinstance(node, Number):
        return node.value
    if isinstance(node, String):
        return node.value
    if isinstance(node, Boolean):
        return node.value
    if isinstance(node, Nil):
        return OPTION_NONE
    if isinstance(node, NoneOption):
        reason = quote_node(node.reason) if node.reason is not None else "nil"
        context = quote_node(node.context) if node.context is not None else None
        return make_none(reason, context)
    if isinstance(node, SymbolLiteral):
        return symbol(node.name)
    if isinstance(node, Var):
        return symbol(node.name)
    if isinstance(node, Quote):
        return quoted_list([symbol("quote"), quote_node(node.expr)])
    if isinstance(node, Delay):
        return quoted_list([symbol("delay"), quote_node(node.expr)])
    if isinstance(node, QuasiQuote):
        return quoted_list([symbol("quasiquote"), quote_node(node.expr)])
    if isinstance(node, Unquote):
        return quoted_list([symbol("unquote"), quote_node(node.expr)])
    if isinstance(node, UnquoteSplicing):
        return quoted_list([symbol("unquote_splicing"), quote_node(node.expr)])
    if isinstance(node, Unary):
        return quoted_list([symbol("app"), symbol(QUOTE_OPERATOR_SYMBOLS[node.op]), quote_node(node.expr)])
    if isinstance(node, Binary):
        return quoted_list([symbol("app"), symbol(QUOTE_OPERATOR_SYMBOLS[node.op]), quote_node(node.left), quote_node(node.right)])
    if isinstance(node, Call):
        return quoted_list([symbol("app"), quote_node(node.fn), *(quote_node(arg) for arg in node.args)])
    if isinstance(node, Block):
        return quoted_list([symbol("block"), *(quote_node(expr) for expr in node.exprs)])
    if isinstance(node, ListLiteral):
        return quoted_list([quote_node(item) for item in node.items])
    if isinstance(node, MapLiteral):
        result = GeniaMap()
        for key, value in node.items:
            result = result.put(quote_node(key), quote_node(value))
        return result
    if isinstance(node, Assign):
        return quoted_list([symbol("assign"), symbol(node.name), quote_node(node.expr)])
    if isinstance(node, Spread):
        return quoted_list([symbol("spread"), quote_node(node.expr)])
    if isinstance(node, Lambda):
        header = quote_lambda_header(node)
        return quoted_list([symbol("lambda"), header, quote_node(node.body)])
    if isinstance(node, CaseExpr):
        return quoted_list([symbol("match"), *(quote_case_clause(clause, quote_node) for clause in node.clauses)])
    raise TypeError(f"quote does not support node type {type(node).__name__}")


def quote_pattern_node(pattern: Node) -> Any:
    def quoted_list(items: list[Any]) -> Any:
        result: Any = OPTION_NONE
        for item in reversed(items):
            result = GeniaPair(item, result)
        return result

    if isinstance(pattern, Number):
        return pattern.value
    if isinstance(pattern, String):
        return pattern.value
    if isinstance(pattern, Boolean):
        return pattern.value
    if isinstance(pattern, Nil):
        return OPTION_NONE
    if isinstance(pattern, NoneOption):
        reason = quote_pattern_node(pattern.reason) if pattern.reason is not None else "nil"
        context = quote_pattern_node(pattern.context) if pattern.context is not None else None
        return make_none(reason, context)
    if isinstance(pattern, SymbolLiteral):
        return symbol(pattern.name)
    if isinstance(pattern, Var):
        return symbol(pattern.name)
    if isinstance(pattern, WildcardPattern):
        return symbol("_")
    if isinstance(pattern, RestPattern):
        if pattern.name is None:
            return quoted_list([symbol("rest")])
        return quoted_list([symbol("rest"), symbol(pattern.name)])
    if isinstance(pattern, TuplePattern):
        return quoted_list([symbol("tuple"), *(quote_pattern_node(item) for item in pattern.items)])
    if isinstance(pattern, ListPattern):
        return quoted_list([quote_pattern_node(item) for item in pattern.items])
    if isinstance(pattern, MapPattern):
        result = GeniaMap()
        for key, value in pattern.items:
            result = result.put(key, quote_pattern_node(value))
        return result
    if isinstance(pattern, GlobPattern):
        return quoted_list([symbol("glob"), pattern.pattern])
    if isinstance(pattern, SomePattern):
        return quoted_list([symbol("some"), quote_pattern_node(pattern.inner)])
    raise TypeError(f"quote does not support pattern type {type(pattern).__name__}")


def quote_lambda_header(node: Lambda) -> Any:
    def quoted_list(items: list[Any]) -> Any:
        result: Any = OPTION_NONE
        for item in reversed(items):
            result = GeniaPair(item, result)
        return result

    if node.pattern is not None and not _lambda_pattern_is_simple_parameter_shape(
        node.pattern,
        node.params,
        node.rest_param,
    ):
        return quote_pattern_node(node.pattern)

    params = [symbol(name) for name in node.params]
    if node.rest_param is None:
        return quoted_list(params)
    return quoted_list([*params, quoted_list([symbol("rest"), symbol(node.rest_param)])])


def quote_case_clause(
    clause: CaseClause,
    quote_expr: Callable[[Node], Any],
) -> Any:
    def quoted_list(items: list[Any]) -> Any:
        result: Any = OPTION_NONE
        for item in reversed(items):
            result = GeniaPair(item, result)
        return result

    if clause.guard is None:
        return quoted_list([symbol("clause"), quote_pattern_node(clause.pattern), quote_expr(clause.result)])
    return quoted_list([symbol("clause"), quote_pattern_node(clause.pattern), quote_expr(clause.guard), quote_expr(clause.result)])


@dataclass(frozen=True)
class _QuasiquoteSplice:
    items: tuple[Any, ...]


def _quasiquote_splice_items(value: Any) -> tuple[Any, ...]:
    if value is None or _is_nil_none(value):
        return ()
    if isinstance(value, list):
        return tuple(value)
    if isinstance(value, GeniaPair):
        items: list[Any] = []
        current: Any = value
        while isinstance(current, GeniaPair):
            items.append(current.head)
            current = current.tail
        if current is not None and not _is_nil_none(current):
            raise TypeError("unquote_splicing expected a list or nil-terminated pair chain")
        return tuple(items)
    raise TypeError("unquote_splicing expected a list or nil-terminated pair chain")


def quasiquote_node(
    node: Node,
    env: "Env",
    debug_hooks: "DebugHooks | None" = None,
    debug_mode: bool = False,
) -> Any:
    effective_debug_hooks = debug_hooks or NOOP_DEBUG_HOOKS

    def quoted_list(items: list[Any]) -> Any:
        result: Any = OPTION_NONE
        for item in reversed(items):
            result = GeniaPair(item, result)
        return result

    def eval_unquoted(expr: Node) -> Any:
        return Evaluator(env, effective_debug_hooks, debug_mode).eval(lower_node(expr))

    def qq(current: Node, depth: int, *, list_context: bool = False) -> Any:
        if isinstance(current, Number):
            return current.value
        if isinstance(current, String):
            return current.value
        if isinstance(current, Boolean):
            return current.value
        if isinstance(current, Nil):
            return OPTION_NONE
        if isinstance(current, NoneOption):
            reason = qq(current.reason, depth) if current.reason is not None else "nil"
            context = qq(current.context, depth) if current.context is not None else None
            return make_none(reason, context)
        if isinstance(current, Var):
            return symbol(current.name)
        if isinstance(current, SymbolLiteral):
            return symbol(current.name)
        if isinstance(current, Quote):
            return quoted_list([symbol("quote"), quote_node(current.expr)])
        if isinstance(current, Delay):
            return quoted_list([symbol("delay"), qq(current.expr, depth)])
        if isinstance(current, QuasiQuote):
            return quoted_list([symbol("quasiquote"), qq(current.expr, depth + 1)])
        if isinstance(current, Unquote):
            if depth == 1:
                return eval_unquoted(current.expr)
            return quoted_list([symbol("unquote"), qq(current.expr, depth - 1)])
        if isinstance(current, UnquoteSplicing):
            if depth == 1:
                if not list_context:
                    raise RuntimeError("unquote_splicing(...) is only valid in quasiquote list context")
                return _QuasiquoteSplice(_quasiquote_splice_items(eval_unquoted(current.expr)))
            return quoted_list([symbol("unquote_splicing"), qq(current.expr, depth - 1)])
        if isinstance(current, Unary):
            return quoted_list([symbol("app"), symbol(QUOTE_OPERATOR_SYMBOLS[current.op]), qq(current.expr, depth)])
        if isinstance(current, Binary):
            return quoted_list([symbol("app"), symbol(QUOTE_OPERATOR_SYMBOLS[current.op]), qq(current.left, depth), qq(current.right, depth)])
        if isinstance(current, Call):
            return quoted_list([symbol("app"), qq(current.fn, depth), *(qq(arg, depth) for arg in current.args)])
        if isinstance(current, Block):
            return quoted_list([symbol("block"), *(qq(expr, depth) for expr in current.exprs)])
        if isinstance(current, ListLiteral):
            items: list[Any] = []
            for item in current.items:
                if isinstance(item, UnquoteSplicing):
                    resolved = qq(item, depth, list_context=True)
                    if isinstance(resolved, _QuasiquoteSplice):
                        items.extend(resolved.items)
                    else:
                        items.append(resolved)
                    continue
                if isinstance(item, Spread):
                    items.append(quoted_list([symbol("spread"), qq(item.expr, depth)]))
                    continue
                resolved = qq(item, depth)
                if isinstance(resolved, _QuasiquoteSplice):
                    raise RuntimeError("unquote_splicing(...) is only valid in quasiquote list context")
                items.append(resolved)
            return quoted_list(items)
        if isinstance(current, MapLiteral):
            result = GeniaMap()
            for key, value in current.items:
                quoted_value = qq(value, depth)
                if isinstance(quoted_value, _QuasiquoteSplice):
                    raise RuntimeError("unquote_splicing(...) is only valid in quasiquote list context")
                result = result.put(qq(key, depth), quoted_value)
            return result
        if isinstance(current, Assign):
            return quoted_list([symbol("assign"), symbol(current.name), qq(current.expr, depth)])
        if isinstance(current, Spread):
            return quoted_list([symbol("spread"), qq(current.expr, depth)])
        if isinstance(current, Lambda):
            header = quote_lambda_header(current)
            return quoted_list([symbol("lambda"), header, qq(current.body, depth)])
        if isinstance(current, CaseExpr):
            return quoted_list([symbol("match"), *(quote_case_clause(clause, lambda expr: qq(expr, depth)) for clause in current.clauses)])
        raise TypeError(f"quasiquote does not support node type {type(current).__name__}")

    return qq(node, 1)


def _annotation_metadata_error(name: str, value: Any, expected: str) -> TypeError:
    return TypeError(f"@{name} annotation expected {expected}, received {_runtime_type_name(value)}")


def _syntax_tagged_list(value: Any, tag: Any) -> bool:
    return isinstance(value, GeniaPair) and value.head == tag


def _syntax_pair_nth(value: Any, index: int, name: str) -> Any:
    current = value
    for _ in range(index):
        if not isinstance(current, GeniaPair):
            raise TypeError(f"{name} expected the quoted form to have enough parts")
        current = current.tail
    if not isinstance(current, GeniaPair):
        raise TypeError(f"{name} expected the quoted form to have enough parts")
    return current.head


def _meta_lower_quoted_pattern(pattern: Any) -> IrPattern:
    if pattern is None or isinstance(pattern, (bool, int, float, str)):
        return IrPatLiteral(pattern)
    if isinstance(pattern, GeniaOptionNone):
        reason = _meta_lower_quoted_pattern(pattern.reason) if pattern.reason is not None else None
        context = _meta_lower_quoted_pattern(pattern.context) if pattern.context is not None else None
        return IrPatNone(reason, context)
    if isinstance(pattern, GeniaSymbol):
        if pattern.name == "_":
            return IrPatWildcard()
        return IrPatBind(pattern.name)
    if isinstance(pattern, GeniaMap):
        items: list[tuple[str, IrPattern]] = []
        for _, (original_key, original_value) in pattern._entries.items():
            if not isinstance(original_key, str):
                raise TypeError("metacircular quoted map patterns require string keys")
            items.append((original_key, _meta_lower_quoted_pattern(original_value)))
        return IrPatMap(items)
    if isinstance(pattern, GeniaPair):
        if _syntax_tagged_list(pattern, symbol("rest")):
            if _is_nil_none(pattern.tail):
                return IrPatRest(None)
            rest_name = _syntax_pair_nth(pattern, 1, "_meta_match_pattern_env")
            if not isinstance(rest_name, GeniaSymbol):
                raise TypeError("metacircular rest patterns require a symbol name")
            if not _is_nil_none(pattern.tail.tail):
                raise TypeError("metacircular rest patterns accept at most one symbol name")
            return IrPatRest(rest_name.name)
        if _syntax_tagged_list(pattern, symbol("tuple")):
            items: list[IrPattern] = []
            current = pattern.tail
            while not _is_nil_none(current):
                if not isinstance(current, GeniaPair):
                    raise TypeError("metacircular tuple patterns must be proper lists")
                items.append(_meta_lower_quoted_pattern(current.head))
                current = current.tail
            return IrPatTuple(items)
        if _syntax_tagged_list(pattern, symbol("glob")):
            glob_text = _syntax_pair_nth(pattern, 1, "_meta_match_pattern_env")
            if not isinstance(glob_text, str):
                raise TypeError("metacircular glob patterns require a string")
            if not _is_nil_none(pattern.tail.tail):
                raise TypeError("metacircular glob patterns accept exactly one string")
            return IrPatGlob(compile_glob_pattern(glob_text))
        if _syntax_tagged_list(pattern, symbol("some")):
            if _is_nil_none(pattern.tail) or not isinstance(pattern.tail, GeniaPair):
                raise TypeError("metacircular some patterns require an inner pattern")
            if not _is_nil_none(pattern.tail.tail):
                raise TypeError("metacircular some patterns accept exactly one inner pattern")
            return IrPatSome(_meta_lower_quoted_pattern(pattern.tail.head))
        items: list[IrPattern] = []
        current = pattern
        while not _is_nil_none(current):
            if not isinstance(current, GeniaPair):
                raise TypeError("metacircular list patterns must be proper lists")
            items.append(_meta_lower_quoted_pattern(current.head))
            current = current.tail
        return IrPatList(items)
    raise TypeError(f"metacircular quoted match pattern is unsupported: {format_debug(pattern)}")


def _syntax_reserved_tag_name(value: Any) -> str | None:
    if isinstance(value, GeniaSymbol):
        if value.name in {
            "quote",
            "quasiquote",
            "app",
            "assign",
            "lambda",
            "block",
            "match",
            "delay",
            "unquote",
            "unquote_splicing",
            "spread",
            "clause",
            "tuple",
            "rest",
            "glob",
            "some",
        }:
            return value.name
    return None


# -----------------------------
# Runtime
# -----------------------------


class GeniaPromise:
    def __init__(
        self,
        expr: IrNode,
        env: "Env",
        debug_hooks: DebugHooks = NOOP_DEBUG_HOOKS,
        debug_mode: bool = False,
    ):
        self._expr = expr
        self._env = env
        self._debug_hooks = debug_hooks
        self._debug_mode = debug_mode
        self._forced = False
        self._forcing = False
        self._value: Any = None

    def force(self) -> Any:
        if self._forced:
            return self._value
        if self._forcing:
            raise RuntimeError("Promise is already being forced")
        self._forcing = True
        try:
            value = Evaluator(self._env, self._debug_hooks, self._debug_mode).eval(self._expr)
        except Exception:
            self._forcing = False
            raise
        self._value = value
        self._forced = True
        self._forcing = False
        return value

    def status(self) -> str:
        if self._forcing:
            return "forcing"
        if self._forced:
            return "forced"
        return "delayed"

    def __repr__(self) -> str:
        return f"<promise {self.status()}>"

    def __str__(self) -> str:
        return repr(self)


class GeniaMetaEnv:
    def __init__(self, env: Env):
        self._env = env

    @property
    def env(self) -> Env:
        return self._env

    def lookup(self, name: str) -> Any:
        try:
            return self._env.get(name)
        except NameError:
            if self._env.try_autoload(name, 0):
                return self._env.get(name)
            raise

    def define(self, name: str, value: Any) -> "GeniaMetaEnv":
        self._env.set(name, value)
        return self

    def assign(self, name: str, value: Any) -> Any:
        self._env.assign(name, value)
        return value

    def extend(self, params: Any, args: list[Any]) -> "GeniaMetaEnv":
        if _syntax_tagged_list(params, symbol("tuple")):
            bindings = Evaluator(self._env).match_pattern(_meta_lower_quoted_pattern(params), tuple(args))
            if bindings is None:
                raise RuntimeError(f"metacircular match failed for lambda parameters with args {format_debug(args)}")
            child = Env(self._env)
            for name, value in bindings.items():
                child.set(name, value)
            return GeniaMetaEnv(child)

        required, rest = self._parse_params(params)
        if rest is None:
            if len(args) != len(required):
                raise TypeError(f"extend expected {len(required)} args, got {len(args)}")
        elif len(args) < len(required):
            raise TypeError(f"extend expected at least {len(required)} args, got {len(args)}")

        child = Env(self._env)
        for index, name in enumerate(required):
            child.set(name, args[index])
        if rest is not None:
            child.set(rest, args[len(required):])
        return GeniaMetaEnv(child)

    def _parse_params(self, params: Any) -> tuple[list[str], str | None]:
        required: list[str] = []
        rest_name: str | None = None
        current = params
        while isinstance(current, GeniaPair):
            item = current.head
            if isinstance(item, GeniaSymbol):
                if rest_name is not None:
                    raise TypeError("extend expected rest parameter to be final")
                required.append(item.name)
            elif _syntax_tagged_list(item, symbol("rest")):
                if rest_name is not None or not _is_nil_none(current.tail):
                    raise TypeError("extend expected at most one final rest parameter")
                rest_value = _syntax_pair_nth(item, 1, "extend")
                if not isinstance(rest_value, GeniaSymbol):
                    raise TypeError("extend expected the rest parameter name to be a symbol")
                rest_name = rest_value.name
            else:
                raise TypeError("extend expected lambda parameter data")
            current = current.tail
        if not _is_nil_none(current):
            raise TypeError("extend expected lambda parameter data")
        return required, rest_name

    def __repr__(self) -> str:
        return "<meta-env>"


class Evaluator:
    def __init__(self, env: Env, debug_hooks: DebugHooks = NOOP_DEBUG_HOOKS, debug_mode: bool = False):
        self.env = env
        self.debug_hooks = debug_hooks
        self.debug_mode = debug_mode

    def eval_program(self, nodes: Iterable[IrNode]) -> Any:
        result = OPTION_NONE
        for node in nodes:
            result = self.eval(node)
        return result

    def eval_annotations(self, annotations: list[IrAnnotation]) -> GeniaMap:
        metadata = GeniaMap()
        string_metadata_annotations = {
            "doc": "doc",
            "since": "since",
            "deprecated": "deprecated",
            "category": "category",
        }
        for annotation in annotations:
            value = self.eval(annotation.value)
            metadata_key = string_metadata_annotations.get(annotation.name)
            if metadata_key is not None:
                if not isinstance(value, str):
                    raise _annotation_metadata_error(annotation.name, value, "a string")
                metadata = metadata.put(metadata_key, value)
                continue
            if annotation.name == "meta":
                if not isinstance(value, GeniaMap):
                    raise _annotation_metadata_error("meta", value, "a map")
                metadata = _merge_metadata_maps(metadata, value)
                continue
            raise RuntimeError(
                "Unsupported annotation: "
                f"@{annotation.name}. Supported annotations: @doc, @meta, @since, @deprecated, @category"
            )
        return metadata

    def eval_function_body(
        self,
        params: list[str],
        args: tuple[Any, ...],
        body: IrNode,
        fn_name: str | None = None,
    ) -> Any:
        if isinstance(body, IrListTraversalLoop):
            return self.eval_list_traversal_loop(params, args, body)
        if isinstance(body, IrCase):
            return self.eval_case_expr(args, body, fn_name)
        if isinstance(body, IrBlock):
            # If the final expr is a case expr, it matches against function args.
            for expr in body.exprs[:-1]:
                self.eval(expr)
            if not body.exprs:
                return OPTION_NONE
            last = body.exprs[-1]
            if isinstance(last, IrCase):
                return self.eval_case_expr(args, last, fn_name)
            return self.eval_tail(last)
        return self.eval_tail(body)

    def eval_list_traversal_loop(self, params: list[str], args: tuple[Any, ...], body: IrListTraversalLoop) -> Any:
        values = dict(zip(params, args))
        n_value = values.get(body.counter_var)
        xs_value = values.get(body.list_var)

        while True:
            current_args = (n_value, xs_value)
            if not isinstance(xs_value, list) or len(xs_value) == 0:
                match_env = self.match_pattern(body.empty_clause.pattern, current_args)
                if match_env is None:
                    return OPTION_NONE
                local = Env(self.env)
                for k, v in match_env.items():
                    local.set(k, v)
                return Evaluator(local, self.debug_hooks, self.debug_mode).eval_tail(body.empty_clause.result)

            if n_value == 0:
                match_env = self.match_pattern(body.zero_clause.pattern, current_args)
                if match_env is None:
                    return OPTION_NONE
                local = Env(self.env)
                for k, v in match_env.items():
                    local.set(k, v)
                return Evaluator(local, self.debug_hooks, self.debug_mode).eval_tail(body.zero_clause.result)

            if not isinstance(n_value, (int, float)):
                return OPTION_NONE
            if n_value < 0:
                return OPTION_NONE
            n_value = n_value - body.step_size
            xs_value = xs_value[body.step_size:]

    def eval_case_expr(self, args: tuple[Any, ...], case_expr: IrCase, fn_name: str | None = None) -> Any:
        for clause in case_expr.clauses:
            match_env = self.match_pattern(clause.pattern, args)
            if match_env is None:
                continue
            local = Env(self.env)
            for k, v in match_env.items():
                local.set(k, v)
            if clause.guard is not None and not truthy(Evaluator(local, self.debug_hooks, self.debug_mode).eval(clause.guard)):
                continue
            return Evaluator(local, self.debug_hooks, self.debug_mode).eval_tail(clause.result)
        if fn_name is not None:
            raise RuntimeError(
                f"No matching case for function {fn_name}/{len(args)} with arguments {args!r}"
            )
        raise RuntimeError(f"No matching case for arguments {args!r}")

    def eval_tail(self, node: IrNode) -> Any:
        if isinstance(node, IrCall):
            return self.eval_call(node, tail_position=True)
        if isinstance(node, IrPipeline):
            return self.eval_pipeline(node, tail_position=True)
        if isinstance(node, IrBlock):
            local = Env(self.env)
            ev = Evaluator(local, self.debug_hooks, self.debug_mode)
            for expr in node.exprs[:-1]:
                ev.eval(expr)
            if not node.exprs:
                return OPTION_NONE
            return ev.eval_tail(node.exprs[-1])
        return self.eval(node)

    def eval_call(self, node: IrCall, tail_position: bool) -> Any:
        args: list[Any] = []
        for arg_node in node.args:
            if isinstance(arg_node, IrSpread):
                value = self.eval(arg_node.expr)
                if not isinstance(value, list):
                    raise TypeError("Cannot spread non-list into function arguments")
                args.extend(value)
            else:
                args.append(self.eval(arg_node))

        if isinstance(node.fn, IrVar):
            name = node.fn.name
            try:
                fn = self.env.get(name)
            except NameError:
                if self.env.try_autoload(name, len(args)):
                    fn = self.env.get(name)
                else:
                    raise
        else:
            fn = self.eval(node.fn)

        return self.invoke_callable(fn, args, tail_position=tail_position, callee_node=node.fn)

    def _pipeline_stage_name(self, node: IrNode) -> str | None:
        if isinstance(node, IrShellStage):
            return f"$({node.command})"
        if isinstance(node, IrVar):
            return node.name
        if isinstance(node, IrCall) and isinstance(node.fn, IrVar):
            return node.fn.name
        return None

    def _render_pipeline_stage(self, node: IrNode) -> str:
        if isinstance(node, IrVar):
            return node.name
        if isinstance(node, IrLiteral):
            return format_debug(node.value)
        if isinstance(node, IrOptionSome):
            return f"some({self._render_pipeline_stage(node.value)})"
        if isinstance(node, IrOptionNone):
            if node.reason is None:
                return "none"
            reason_text = self._render_pipeline_stage(node.reason)
            if node.context is None:
                return f"none({reason_text})"
            return f"none({reason_text}, {self._render_pipeline_stage(node.context)})"
        if isinstance(node, IrList):
            item_texts: list[str] = []
            for item in node.items:
                if isinstance(item, IrSpread):
                    item_texts.append(f"..{self._render_pipeline_stage(item.expr)}")
                else:
                    item_texts.append(self._render_pipeline_stage(item))
            return f"[{', '.join(item_texts)}]"
        if isinstance(node, IrMap):
            entry_texts = [
                f"{key}: {self._render_pipeline_stage(value)}"
                for key, value in node.entries
            ]
            return f"{{{', '.join(entry_texts)}}}"
        if isinstance(node, IrUnary):
            op = "-" if node.op == "MINUS" else "!"
            return f"{op}{self._render_pipeline_stage(node.expr)}"
        if isinstance(node, IrBinary):
            op_map = {
                "PLUS": "+",
                "MINUS": "-",
                "STAR": "*",
                "SLASH": "/",
                "PERCENT": "%",
                "LT": "<",
                "LE": "<=",
                "GT": ">",
                "GE": ">=",
                "EQEQ": "==",
                "NE": "!=",
                "AND": "&&",
                "OR": "||",
                "PIPE_FWD": "|>",
            }
            op = op_map.get(node.op, node.op)
            return f"{self._render_pipeline_stage(node.left)} {op} {self._render_pipeline_stage(node.right)}"
        if isinstance(node, IrCall):
            fn_text = self._render_pipeline_stage(node.fn)
            arg_texts: list[str] = []
            for arg in node.args:
                if isinstance(arg, IrSpread):
                    arg_texts.append(f"..{self._render_pipeline_stage(arg.expr)}")
                else:
                    arg_texts.append(self._render_pipeline_stage(arg))
            return f"{fn_text}({', '.join(arg_texts)})"
        if isinstance(node, IrBlock):
            return "{ ... }"
        if isinstance(node, IrLambda):
            params = ", ".join(node.params)
            if node.rest_param is not None:
                params = f"{params}, ..{node.rest_param}" if params else f"..{node.rest_param}"
            return f"({params}) -> ..."
        if isinstance(node, IrQuote):
            return "quote(...)"
        if isinstance(node, IrQuasiQuote):
            return "quasiquote(...)"
        if isinstance(node, IrShellStage):
            return f"$({node.command})"
        if isinstance(node, IrPipeline):
            stage_text = " |> ".join(self._render_pipeline_stage(stage) for stage in node.stages)
            return f"{self._render_pipeline_stage(node.source)} |> {stage_text}"
        return node.__class__.__name__

    def _pipeline_stage_mode(self, node: IrNode, stage_input: Any) -> str:
        stage_name = self._pipeline_stage_name(node)
        if stage_name == "lines" or (stage_name == "collect" and isinstance(stage_input, GeniaFlow)):
            return "Explicit bridge mode"
        if isinstance(stage_input, GeniaFlow):
            return "Flow mode"
        return "Value mode"

    def _format_pipeline_stage_span(self, node: IrNode) -> str | None:
        span = getattr(node, "span", None)
        if span is None:
            return None
        return f"{span.filename}:{span.line}"

    def _wrap_pipeline_stage_error(self, exc: Exception, stage_index: int, node: IrNode, stage_input: Any) -> Exception:
        if getattr(exc, "_genia_preserve_pipeline_error", False):
            return exc
        message = str(exc)
        if message.startswith("pipeline stage ") and " failed in " in message:
            return exc
        if isinstance(exc, ValueError) and message.startswith("python.json/loads invalid JSON:"):
            return exc
        stage_text = self._render_pipeline_stage(node)
        mode_text = self._pipeline_stage_mode(node, stage_input)
        span_text = self._format_pipeline_stage_span(node)
        rendered = f"pipeline stage {stage_index + 1} failed in {mode_text} at {stage_text}"
        if span_text is not None:
            rendered += f" [{span_text}]"
        input_type = _runtime_type_name(stage_input)
        if isinstance(stage_input, GeniaOptionSome):
            rendered += f": pipeline value was {input_type} (auto-unwrapped)"
        elif isinstance(stage_input, GeniaOptionNone):
            rendered += f": pipeline value was {input_type}"
        else:
            rendered += f": stage received {input_type}"
        if message:
            rendered += f"; {message}"
        exc_type = exc.__class__
        try:
            return exc_type(rendered)
        except Exception:  # pragma: no cover - defensive fallback
            return RuntimeError(rendered)

    def eval_pipeline(self, node: IrPipeline, tail_position: bool) -> Any:
        stage_value = self.eval(node.source)
        for index, stage in enumerate(node.stages):
            if is_none(stage_value):
                return stage_value
            try:
                stage_value = self.eval_pipeline_stage(
                    stage,
                    stage_value,
                    tail_position=tail_position and index == len(node.stages) - 1,
                )
            except GeniaQuietBrokenPipe:
                raise
            except Exception as exc:  # noqa: BLE001
                raise self._wrap_pipeline_stage_error(exc, index, stage, stage_value) from exc
        return stage_value

    def eval_pipeline_stage(self, node: IrNode, stage_value: Any, *, tail_position: bool) -> Any:
        if isinstance(node, IrShellStage):
            return self._eval_shell_stage(node, stage_value)

        def invoke_with_pipeline_option_lifting(fn: Any, base_args: list[Any], callee_node: IrNode) -> Any:
            # Lift `some(x)` through ordinary stages while preserving explicit Option-aware call sites.
            if (
                isinstance(stage_value, GeniaOptionSome)
                and not _callable_explicitly_handles_some(fn, len(base_args) + 1, callee_node)
            ):
                result = self.invoke_callable(
                    fn,
                    [*base_args, stage_value.value],
                    tail_position=tail_position,
                    callee_node=callee_node,
                )
                if isinstance(result, (GeniaOptionSome, GeniaOptionNone)):
                    return result
                if isinstance(result, GeniaFlow):
                    return result
                return GeniaOptionSome(result)
            return self.invoke_callable(
                fn,
                [*base_args, stage_value],
                tail_position=tail_position,
                callee_node=callee_node,
            )

        if isinstance(node, IrCall):
            args: list[Any] = []
            for arg_node in node.args:
                if isinstance(arg_node, IrSpread):
                    value = self.eval(arg_node.expr)
                    if not isinstance(value, list):
                        raise TypeError("Cannot spread non-list into function arguments")
                    args.extend(value)
                else:
                    args.append(self.eval(arg_node))

            if isinstance(node.fn, IrVar):
                name = node.fn.name
                try:
                    fn = self.env.get(name)
                except NameError:
                    if self.env.try_autoload(name, len(args) + 1):
                        fn = self.env.get(name)
                    else:
                        raise
            else:
                fn = self.eval(node.fn)

            return invoke_with_pipeline_option_lifting(fn, args, node.fn)

        if isinstance(node, IrVar):
            try:
                fn_value = self.env.get(node.name)
            except NameError:
                if self.env.try_autoload(node.name, 1):
                    fn_value = self.env.get(node.name)
                else:
                    raise
        else:
            fn_value = self.eval(node)
        return invoke_with_pipeline_option_lifting(fn_value, [], node)

    def _shell_stage_input_to_bytes(self, value: Any) -> bytes:
        if isinstance(value, str):
            return value.encode("utf-8")
        if isinstance(value, bool):
            return format_display(value).encode("utf-8")
        if isinstance(value, (int, float)):
            return format_display(value).encode("utf-8")
        if isinstance(value, list):
            return "\n".join(format_display(item) for item in value).encode("utf-8")
        if isinstance(value, GeniaFlow):
            items = value.consume()
            return "\n".join(format_display(item) for item in items).encode("utf-8")
        raise TypeError(f"shell stage: cannot convert {type(value).__name__} to stdin bytes")

    def _eval_shell_stage(self, node: IrShellStage, stage_value: Any) -> Any:
        # Option lifting: unwrap some, propagate none
        unwrapped = stage_value
        was_some = False
        if isinstance(stage_value, GeniaOptionNone):
            return stage_value
        if isinstance(stage_value, GeniaOptionSome):
            unwrapped = stage_value.value
            was_some = True

        stdin_bytes = self._shell_stage_input_to_bytes(unwrapped)
        try:
            result = subprocess.run(
                node.command,
                shell=True,
                input=stdin_bytes,
                capture_output=True,
            )
        except Exception as exc:
            raise RuntimeError(f"shell stage: failed to execute: {node.command}") from exc

        if result.returncode != 0:
            raise RuntimeError(
                f"shell stage: command failed (exit {result.returncode}): {node.command}"
            )

        stdout_text = result.stdout.decode("utf-8", errors="replace")
        if stdout_text.endswith("\n"):
            stdout_text = stdout_text[:-1]

        if stdout_text == "":
            out: Any = make_none("empty-shell-output")
        else:
            out = stdout_text

        if was_some and not isinstance(out, (GeniaOptionSome, GeniaOptionNone)):
            out = GeniaOptionSome(out)
        return out

    def invoke_callable(
        self,
        fn: Any,
        args: list[Any],
        *,
        tail_position: bool,
        callee_node: IrNode | None = None,
        skip_none_propagation: bool = False,
    ) -> Any:
        def _autoload(name: str, arity: int) -> Any:
            if self.env.try_autoload(name, arity):
                return self.env.get(name)
            return None

        return _invoke_callable(
            fn,
            args,
            tail_position=tail_position,
            callee_node=callee_node,
            skip_none_propagation=skip_none_propagation,
            autoload_resolver=_autoload,
        )

    def match_pattern(self, pattern: IrPattern, args: tuple[Any, ...]) -> Optional[dict[str, Any]]:
        return match_pattern(pattern, args)

    def match_lambda_pattern(self, pattern: IrPattern, args: tuple[Any, ...]) -> Optional[dict[str, Any]]:
        return match_lambda_pattern(pattern, args)

    def match_pattern_atom(self, pattern: IrPattern, arg: Any) -> Optional[dict[str, Any]]:
        return match_pattern_atom(pattern, arg)

    def eval(self, node: IrNode) -> Any:
        if self.debug_mode:
            self.debug_hooks.before_node(node, self.env)
        result = self._eval_impl(node)
        if self.debug_mode:
            self.debug_hooks.after_node(node, self.env, result)
        return result

    def _eval_impl(self, node: IrNode) -> Any:
        if isinstance(node, IrShellStage):
            raise SyntaxError("shell stage $(...) is only valid as a pipeline stage")
        if isinstance(node, IrExprStmt):
            return self.eval(node.expr)
        if isinstance(node, IrLiteral):
            return node.value
        if isinstance(node, IrOptionNone):
            reason = self.eval(node.reason) if node.reason is not None else None
            context = self.eval(node.context) if node.context is not None else None
            return make_none(reason, context)
        if isinstance(node, IrOptionSome):
            return GeniaOptionSome(self.eval(node.value))
        if isinstance(node, IrList):
            result: list[Any] = []
            for item in node.items:
                if isinstance(item, IrSpread):
                    value = self.eval(item.expr)
                    if not isinstance(value, list):
                        raise TypeError("Cannot spread non-list")
                    result.extend(value)
                else:
                    result.append(self.eval(item))
            return result
        if isinstance(node, IrMap):
            result = GeniaMap()
            for key, value_node in node.items:
                result = result.put(key, self.eval(value_node))
            return result
        if isinstance(node, IrQuote):
            return quote_node(node.expr)
        if isinstance(node, IrQuasiQuote):
            return quasiquote_node(node.expr, self.env, self.debug_hooks, self.debug_mode)
        if isinstance(node, IrDelay):
            return GeniaPromise(node.expr, self.env, self.debug_hooks, self.debug_mode)
        if isinstance(node, IrUnquote):
            raise RuntimeError("unquote(...) is only valid inside quasiquote")
        if isinstance(node, IrUnquoteSplicing):
            raise RuntimeError("unquote_splicing(...) is only valid inside quasiquote")
        if isinstance(node, IrVar):
            try:
                return self.env.get(node.name)
            except NameError:
                if self.env.try_autoload(node.name, 0):
                    return self.env.get(node.name)
                raise
        if isinstance(node, IrUnary):
            value = self.eval(node.expr)
            if is_none(value):
                return value
            if node.op == "MINUS":
                try:
                    return -value
                except TypeError:
                    return make_none("type-error", GeniaMap().put("source", "unary-minus").put("received", _runtime_type_name(value)))
            if node.op == "BANG":
                return not truthy(value)
            raise RuntimeError(f"Unknown unary operator {node.op}")
        if isinstance(node, IrPipeline):
            return self.eval_pipeline(node, tail_position=False)
        if isinstance(node, IrBinary):
            return self.eval_binary(node)
        if isinstance(node, IrCall):
            return self.eval_call(node, tail_position=False)

        if isinstance(node, IrBlock):
            local = Env(self.env)
            result = OPTION_NONE
            ev = Evaluator(local, self.debug_hooks, self.debug_mode)
            for expr in node.exprs:
                result = ev.eval(expr)
            return result
        if isinstance(node, IrLambda):
            params = node.params
            rest_param = node.rest_param
            pattern = node.pattern
            body = node.body
            closure = self.env
            internal_access = self.env.internal_access

            def fn(*args):
                frame = Env(closure, internal_access=internal_access)
                if pattern is None:
                    if rest_param is None:
                        if len(args) != len(params):
                            raise TypeError(f"lambda expected {len(params)} args, got {len(args)}")
                    elif len(args) < len(params):
                        raise TypeError(f"lambda expected at least {len(params)} args, got {len(args)}")
                    for p, a in zip(params, args):
                        frame.set(p, a)
                    if rest_param is not None:
                        frame.set(rest_param, list(args[len(params):]))
                else:
                    match_env = Evaluator(closure, self.debug_hooks, self.debug_mode).match_lambda_pattern(pattern, args)
                    if match_env is None:
                        raise RuntimeError(f"No matching case for arguments {args!r}")
                    for name, value in match_env.items():
                        frame.set(name, value)
                return Evaluator(frame, self.debug_hooks, self.debug_mode).eval(body)

            fn.__genia_body__ = body
            if pattern is not None:
                fn.__genia_pattern__ = pattern
            return fn

        if isinstance(node, IrAssign):
            value = self.eval(node.expr)
            self.env.assign(node.name, value)
            if node.annotations:
                metadata = self.eval_annotations(node.annotations)
                self.env.merge_binding_metadata(node.name, metadata)
            return value

        if isinstance(node, IrFuncDef):
            fn = GeniaFunction(
                node.name,
                node.params,
                node.rest_param,
                node.docstring,
                node.body,
                self.env,
                span=node.span,
                debug_hooks=self.debug_hooks,
                debug_mode=self.debug_mode,
                internal_access=self.env.internal_access,
            )
            self.env.define_function(fn)
            if node.annotations:
                metadata = self.eval_annotations(node.annotations)
                self.env.merge_binding_metadata(node.name, metadata)
            return fn
        if isinstance(node, IrImport):
            requester = node.span.filename if node.span is not None else None
            module_value = self.env.load_module(node.module_name, requester)
            self.env.set(node.alias, module_value)
            return module_value
        if isinstance(node, IrCase):
            raise RuntimeError("Standalone case expressions are only valid as function bodies or final block expressions")
        if isinstance(node, IrListTraversalLoop):
            raise RuntimeError("Optimized list traversal nodes are only valid as function bodies")
        raise RuntimeError(f"Unknown node: {node!r}")

    def eval_binary(self, node: IrBinary) -> Any:
        left = self.eval(node.left)
        if node.op in {"EQEQ", "NE"}:
            right = self.eval(node.right)
            match node.op:
                case "EQEQ":
                    return left == right
                case "NE":
                    return left != right
        if is_none(left):
            return left
        if node.op == "AND":
            right = self.eval(node.right)
            if is_none(right):
                return right
            return left and right
        if node.op == "OR":
            right = self.eval(node.right)
            if is_none(right):
                return right
            return left or right
        if node.op == "SLASH" and isinstance(left, (GeniaMap, ModuleValue)):
            if isinstance(node.right, IrVar):
                key_name = node.right.name
                if isinstance(left, GeniaMap):
                    return left.get(key_name)
                return left.get_export(key_name)
            if isinstance(node.right, IrCall) and isinstance(node.right.fn, IrVar):
                key_name = node.right.fn.name
                if isinstance(left, GeniaMap):
                    callee = left.get(key_name)
                else:
                    callee = left.get_export(key_name)
                args: list[Any] = []
                for arg_node in node.right.args:
                    if isinstance(arg_node, IrSpread):
                        value = self.eval(arg_node.expr)
                        if not isinstance(value, list):
                            raise TypeError("Cannot spread non-list into function arguments")
                        args.extend(value)
                    else:
                        args.append(self.eval(arg_node))
                return self.invoke_callable(callee, args, tail_position=False, callee_node=node.right.fn)
            raise TypeError("named accessor '/' requires a bare identifier on the right-hand side")
        try:
            right = self.eval(node.right)
        except NameError:
            if node.op == "SLASH" and isinstance(node.right, IrVar):
                raise TypeError("named accessor '/' is only supported for map and module values") from None
            raise
        if is_none(right):
            return right
        match node.op:
            case "PLUS":
                try:
                    return left + right
                except TypeError:
                    return make_none("type-error", GeniaMap().put("source", "+").put("left", _runtime_type_name(left)).put("right", _runtime_type_name(right)))
            case "MINUS":
                try:
                    return left - right
                except TypeError:
                    return make_none("type-error", GeniaMap().put("source", "-").put("left", _runtime_type_name(left)).put("right", _runtime_type_name(right)))
            case "STAR":
                try:
                    return left * right
                except TypeError:
                    return make_none("type-error", GeniaMap().put("source", "*").put("left", _runtime_type_name(left)).put("right", _runtime_type_name(right)))
            case "SLASH":
                try:
                    return left / right
                except TypeError:
                    return make_none("type-error", GeniaMap().put("source", "/").put("left", _runtime_type_name(left)).put("right", _runtime_type_name(right)))
            case "PERCENT":
                try:
                    return left % right
                except TypeError:
                    return make_none("type-error", GeniaMap().put("source", "%").put("left", _runtime_type_name(left)).put("right", _runtime_type_name(right)))
            case "LT":
                try:
                    return left < right
                except TypeError:
                    return make_none("type-error", GeniaMap().put("source", "<").put("left", _runtime_type_name(left)).put("right", _runtime_type_name(right)))
            case "LE":
                try:
                    return left <= right
                except TypeError:
                    return make_none("type-error", GeniaMap().put("source", "<=").put("left", _runtime_type_name(left)).put("right", _runtime_type_name(right)))
            case "GT":
                try:
                    return left > right
                except TypeError:
                    return make_none("type-error", GeniaMap().put("source", ">").put("left", _runtime_type_name(left)).put("right", _runtime_type_name(right)))
            case "GE":
                try:
                    return left >= right
                except TypeError:
                    return make_none("type-error", GeniaMap().put("source", ">=").put("left", _runtime_type_name(left)).put("right", _runtime_type_name(right)))
            case _:
                raise RuntimeError(f"Unknown binary operator {node.op}")
