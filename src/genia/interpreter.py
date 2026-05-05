#!/usr/bin/env python3
"""
Minimal Genia REPL / interpreter prototype.

Implemented subset:
- numbers, booleans, nil, strings
- arithmetic: + - * / %
- comparison: < <= > >= == !=
- variables and function calls
- function definitions: name(args) = expr
- function definitions with blocks: name(args) { ... }
- case expressions in function bodies and as final expression in blocks
- pattern matching against the full argument tuple
- single-argument pattern shorthand: 0 -> 1 is treated like (0) -> 1
- guards: pattern ? condition -> result
- blocks with newline or ; expression separators
- builtins: log(...), print(...), input(prompt), help()
"""
from __future__ import annotations

import os
from pathlib import Path
import argparse
import sys
from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any, Optional

if __package__ in (None, ""):
    _src_root = Path(__file__).resolve().parents[1]
    if str(_src_root) not in sys.path:
        sys.path.insert(0, str(_src_root))
    from genia.utf8 import (
        format_debug,
    )
    from genia.lexer import lex
    from genia.parser import Parser
    from genia.environment import Env

    from genia.errors import GeniaQuietBrokenPipe, _format_pipe_mode_error
    from genia.ast_nodes import (
        Assign,
        Block,
        ExprStmt,
        Lambda,
        ListPattern,
        MapPattern,
        Node,
        NoneOption,
        RestPattern,
        SomePattern,
        TuplePattern,
        Var,
    )
    from genia.ir import (
        HOST_LOCAL_POST_LOWERING_IR_NODE_TYPES as HOST_LOCAL_POST_LOWERING_IR_NODE_TYPES,
        PORTABLE_CORE_IR_NODE_TYPES as PORTABLE_CORE_IR_NODE_TYPES,
        assert_portable_core_ir,
        iter_ir_nodes as iter_ir_nodes,
    )
    from genia.values import (
        _is_nil_none,
        _normalize_absence,
        GeniaOutputSink,
    )
    from genia.optimizer import (
        optimize_program as optimize_program,
    )
    from genia.lowering import (
        lower_program as lower_program,
        lower_node as lower_node,
        lower_pattern as lower_pattern,
    )
    from genia.callable import (
        DebugHooks as DebugHooks,
        NOOP_DEBUG_HOOKS as NOOP_DEBUG_HOOKS,
        GeniaFunction as GeniaFunction,
        GeniaFunctionGroup as GeniaFunctionGroup,
        TailCall as TailCall,
        eval_with_tco as eval_with_tco,
    )
else:
    from .environment import Env
    from .errors import GeniaQuietBrokenPipe, _format_pipe_mode_error
    from .ast_nodes import (
        Assign,
        Block,
        ExprStmt,
        Lambda,
        ListPattern,
        MapPattern,
        Node,
        NoneOption,
        RestPattern,
        SomePattern,
        TuplePattern,
        Var,
    )
    from .ir import (
        HOST_LOCAL_POST_LOWERING_IR_NODE_TYPES as HOST_LOCAL_POST_LOWERING_IR_NODE_TYPES,
        PORTABLE_CORE_IR_NODE_TYPES as PORTABLE_CORE_IR_NODE_TYPES,
        assert_portable_core_ir,
        iter_ir_nodes as iter_ir_nodes,
    )
    from .utf8 import (
        format_debug,
    )
    from .values import (
        _is_nil_none,
        _normalize_absence,
        GeniaOutputSink,
    )
    from .lexer import lex
    from .parser import Parser
    from .optimizer import (
        optimize_program as optimize_program,
    )
    from .lowering import (
        lower_program as lower_program,
        lower_node as lower_node,
        lower_pattern as lower_pattern,
    )
    from .callable import (
        DebugHooks as DebugHooks,
        NOOP_DEBUG_HOOKS as NOOP_DEBUG_HOOKS,
        GeniaFunction as GeniaFunction,
        GeniaFunctionGroup as GeniaFunctionGroup,
        TailCall as TailCall,
        eval_with_tco as eval_with_tco,
    )

if __package__ in (None, ""):
    from genia.builtins import make_global_env
    from genia.evaluator import Evaluator, GeniaPromise, GeniaMetaEnv
    from genia.lexer import SourceSpan
    from genia.values import (
        OPTION_NONE,
        GeniaBytes,
        GeniaFlow,
        GeniaOptionNone,
        GeniaOptionSome,
        GeniaRef,
        GeniaZipEntry,
        truthy,
    )
    from genia.host_bridge import (
        BASE_DIR,
        _load_source_from_path,
        _resolve_packaged_module,
        _build_python_host_module,
        _genia_to_python_host,
        _python_host_to_genia,
    )
    from genia.pattern_match import (
        IrPatBind,
        IrPatGlob,
        IrPatList,
        IrPatLiteral,
        IrPatMap,
        IrPatNone,
        IrPatRest,
        IrPatSome,
        IrPatTuple,
        IrPatWildcard,
        IrPattern,
    )
else:
    from .builtins import make_global_env as make_global_env
    from .evaluator import Evaluator as Evaluator, GeniaPromise as GeniaPromise, GeniaMetaEnv as GeniaMetaEnv
    from .lexer import SourceSpan as SourceSpan
    from .values import (
        OPTION_NONE as OPTION_NONE,
        GeniaBytes as GeniaBytes,
        GeniaFlow as GeniaFlow,
        GeniaOptionNone as GeniaOptionNone,
        GeniaOptionSome as GeniaOptionSome,
        GeniaRef as GeniaRef,
        GeniaZipEntry as GeniaZipEntry,
        truthy as truthy,
    )
    from .host_bridge import (
        BASE_DIR as BASE_DIR,
        _load_source_from_path as _load_source_from_path,
        _resolve_packaged_module as _resolve_packaged_module,
        _build_python_host_module as _build_python_host_module,
        _genia_to_python_host as _genia_to_python_host,
        _python_host_to_genia as _python_host_to_genia,
    )
    from .pattern_match import (
        IrPatBind as IrPatBind,
        IrPatGlob as IrPatGlob,
        IrPatList as IrPatList,
        IrPatLiteral as IrPatLiteral,
        IrPatMap as IrPatMap,
        IrPatNone as IrPatNone,
        IrPatRest as IrPatRest,
        IrPatSome as IrPatSome,
        IrPatTuple as IrPatTuple,
        IrPatWildcard as IrPatWildcard,
        IrPattern as IrPattern,
    )

    def actor_validate_effect_fn(result: Any, cell: Any) -> Any:
        if isinstance(result, list):
            if len(result) == 2 and result[0] == "ok":
                return result[1]
            if len(result) == 3 and result[0] == "reply":
                return result[1]  # discard response for fire-and-forget
            if len(result) == 3 and result[0] == "stop":
                _stage_cell_action("cell_stop", cell, None)
                return result[2]
        raise TypeError(
            _ACTOR_EFFECT_ERROR.format(value=format_debug(result))
        )

    def actor_call_update_fn(handler: Any, msg: Any, reply_ref: Any, state: Any, cell: Any) -> Any:
        if not isinstance(reply_ref, GeniaRef):
            raise TypeError("_actor_call_update expected a ref for reply")
        try:
            ctx = GeniaMap({"reply_to": reply_ref})
            result = handler(state, msg, ctx)
            if isinstance(result, list):
                if len(result) == 3 and result[0] == "reply":
                    reply_ref.set(result[2])
                    return result[1]
                if len(result) == 2 and result[0] == "ok":
                    reply_ref.set(result[1])
                    return result[1]
                if len(result) == 3 and result[0] == "stop":
                    reply_ref.set(make_none("actor-stopped"))
                    _stage_cell_action("cell_stop", cell, None)
                    return result[2]
            raise TypeError(
                _ACTOR_EFFECT_ERROR.format(value=format_debug(result))
            )
        except BaseException:
            if not reply_ref.is_set():
                reply_ref.set(make_none("actor-error"))
            raise

    def _ensure_map(value: Any, name: str) -> GeniaMap:
        if not isinstance(value, GeniaMap):
            raise TypeError(f"{name} expected a map as first argument, received {_runtime_type_name(value)}")
        return value

    def _ensure_list_of_strings(value: Any, name: str) -> list[str]:
        if not isinstance(value, list):
            raise TypeError(f"{name} expected a list of strings, received {_runtime_type_name(value)}")
        if not all(isinstance(item, str) for item in value):
            raise TypeError(f"{name} expected a list of strings, received list")
        return value

    def _map_from_string_names(names: list[str]) -> GeniaMap:
        result = GeniaMap()
        for name in names:
            result = result.put(name, True)
        return result

    def cli_spec_fn(spec: Any) -> GeniaMap:
        if spec is None or _is_nil_none(spec):
            flags = GeniaMap()
            options = GeniaMap()
            aliases = GeniaMap()
        else:
            if not isinstance(spec, GeniaMap):
                raise TypeError("cli_parse expected spec to be a map")

            flags_raw = spec.get("flags", None)
            options_raw = spec.get("options", None)
            aliases_raw = spec.get("aliases", None)

            flags_list = _ensure_list_of_strings(flags_raw, "cli_parse spec.flags") if flags_raw is not None else []
            options_list = _ensure_list_of_strings(options_raw, "cli_parse spec.options") if options_raw is not None else []
            flags = _map_from_string_names(flags_list)
            options = _map_from_string_names(options_list)
            aliases = GeniaMap()

            if aliases_raw is not None:
                if not isinstance(aliases_raw, GeniaMap):
                    raise TypeError("cli_parse spec.aliases expected a map")
                for _, (raw_key, raw_value) in aliases_raw._entries.items():
                    if not isinstance(raw_key, str) or not isinstance(raw_value, str):
                        raise TypeError("cli_parse spec.aliases expected string keys and values")
                    aliases = aliases.put(raw_key, raw_value)

        return GeniaMap().put("flags", flags).put("options", options).put("aliases", aliases)

    def cli_chars_fn(value: Any) -> list[str]:
        if not isinstance(value, str):
            raise TypeError("cli_parse expected a list of strings")
        return list(value)

    def cli_type_error_fn(message: Any) -> Any:
        raise TypeError(_ensure_string(message, "cli_parse"))

    def cli_value_error_fn(message: Any) -> Any:
        raise ValueError(_ensure_string(message, "cli_parse"))

    def cli_flag_fn(opts: Any, name: Any) -> bool:
        genia_map = _ensure_map(opts, "cli_flag?")
        key = _ensure_string(name, "cli_flag?")
        return bool(genia_map.get(key, False))

    def cli_option_fn(opts: Any, name: Any) -> Any:
        genia_map = _ensure_map(opts, "cli_option")
        key = _ensure_string(name, "cli_option")
        return genia_map.get(key)

    def cli_option_or_fn(opts: Any, name: Any, default: Any) -> Any:
        genia_map = _ensure_map(opts, "cli_option_or")
        key = _ensure_string(name, "cli_option_or")
        value = genia_map.get(key, _UNSET)
        return default if value is _UNSET else value

    def map_new_fn(*args: Any) -> GeniaMap:
        if len(args) != 0:
            raise TypeError(f"map_new expected 0 args, got {len(args)}")
        return GeniaMap()

    def map_get_fn(map_value: Any, key: Any) -> Any:
        genia_map = _ensure_map(map_value, "map_get")
        return genia_map.get(key)

    def map_put_fn(map_value: Any, key: Any, value: Any) -> GeniaMap:
        genia_map = _ensure_map(map_value, "map_put")
        return genia_map.put(key, value)

    def map_has_fn(map_value: Any, key: Any) -> bool:
        genia_map = _ensure_map(map_value, "map_has?")
        return genia_map.has(key)

    def map_remove_fn(map_value: Any, key: Any) -> GeniaMap:
        genia_map = _ensure_map(map_value, "map_remove")
        return genia_map.remove(key)

    def map_count_fn(map_value: Any) -> int:
        genia_map = _ensure_map(map_value, "map_count")
        return genia_map.count()

    def map_items_fn(map_value: Any) -> int:
        genia_map = _ensure_map(map_value, "map_items")
        return genia_map.items()

    def pairs_error_fn(position: Any, value: Any) -> Any:
        if position == "first":
            raise TypeError(f"pairs expected a list as first argument, received {_runtime_type_name(value)}")
        if position == "second":
            raise TypeError(f"pairs expected a list as second argument, received {_runtime_type_name(value)}")
        raise TypeError("pairs internal error expected argument position 'first' or 'second'")

    def some_fn(value: Any) -> GeniaOptionSome:
        return GeniaOptionSome(value)

    def is_some_fn(value: Any) -> bool:
        return isinstance(value, GeniaOptionSome)

    def is_none_fn(value: Any) -> bool:
        return isinstance(value, GeniaOptionNone)

    def unwrap_or_fn(default: Any, opt: Any) -> Any:
        if isinstance(opt, GeniaOptionSome):
            return opt.value
        if isinstance(opt, GeniaOptionNone):
            return default
        raise TypeError(f"unwrap_or expected an option value, received {_runtime_type_name(opt)}")

    def some_predicate_fn(value: Any) -> bool:
        return is_some_fn(value)

    def none_predicate_fn(value: Any) -> bool:
        return is_none_fn(value)

    def _resolve_option_and_other(first: Any, second: Any) -> tuple[Any, Any]:
        if isinstance(first, (GeniaOptionSome, GeniaOptionNone)):
            return first, second
        if isinstance(second, (GeniaOptionSome, GeniaOptionNone)):
            return second, first
        return first, second

    def or_else_fn(first: Any, second: Any) -> Any:
        opt, fallback = _resolve_option_and_other(first, second)
        if isinstance(opt, GeniaOptionSome):
            return opt.value
        if isinstance(opt, GeniaOptionNone):
            return fallback
        raise TypeError(f"or_else expected an option value, received {_runtime_type_name(opt)}")

    def absence_reason_fn(value: Any) -> Any:
        if not isinstance(value, GeniaOptionNone):
            raise TypeError("absence_reason expected a none value")
        return GeniaOptionSome(value.reason)

    def absence_context_fn(value: Any) -> Any:
        if not isinstance(value, GeniaOptionNone):
            raise TypeError("absence_context expected a none value")
        if value.context is None:
            return OPTION_NONE
        return GeniaOptionSome(value.context)

    def absence_meta_fn(value: Any) -> Any:
        if not isinstance(value, GeniaOptionNone):
            raise TypeError("absence_meta expected a none value")
        return GeniaOptionSome(value.meta)

    def _invoke_from_builtin(proc: Any, args: list[Any]) -> Any:
        return Evaluator(env, env.debug_hooks, env.debug_mode).invoke_callable(
            proc,
            args,
            tail_position=False,
            callee_node=None,
        )

    def _invoke_raw_from_builtin(proc: Any, args: list[Any]) -> Any:
        """Like _invoke_from_builtin but skips none-propagation.
        Used by host-backed HOFs (map/filter/reduce) processing list elements."""
        return Evaluator(env, env.debug_hooks, env.debug_mode).invoke_callable(
            proc,
            args,
            tail_position=False,
            callee_node=None,
            skip_none_propagation=True,
        )

    def apply_raw_fn(proc: Any, args: Any) -> Any:
        if not isinstance(args, list):
            raise TypeError(
                f"apply_raw expected a list as second argument, received {_runtime_type_name(args)}"
            )
        return Evaluator(env, env.debug_hooks, env.debug_mode).invoke_callable(
            proc,
            args,
            tail_position=False,
            callee_node=None,
            skip_none_propagation=True,
        )

    def _get_option_impl(name: str, key: Any, target: Any) -> Any:
        if isinstance(target, GeniaOptionNone):
            return target
        if isinstance(target, GeniaOptionSome):
            return _get_option_impl(name, key, target.value)
        if isinstance(target, GeniaMap):
            if target.has(key):
                return GeniaOptionSome(target.get(key))
            context = GeniaMap().put("key", key)
            return make_none("missing-key", context)
        raise TypeError(f"{name} expected a map, some(map), or none target; received {_runtime_type_name(target)}")

    def get_fn(key: Any, target: Any) -> Any:
        return _get_option_impl("get", key, target)

    def get_option_fn(key: Any, target: Any) -> Any:
        return _get_option_impl("get?", key, target)

    def map_some_fn(proc: Any, opt: Any) -> Any:
        if isinstance(opt, GeniaOptionSome):
            return GeniaOptionSome(_invoke_from_builtin(proc, [opt.value]))
        if isinstance(opt, GeniaOptionNone):
            return opt
        raise TypeError(f"map_some expected an option value, received {_runtime_type_name(opt)}")

    def flat_map_some_fn(proc: Any, opt: Any) -> Any:
        if isinstance(opt, GeniaOptionSome):
            result = _invoke_from_builtin(proc, [opt.value])
            if isinstance(result, (GeniaOptionSome, GeniaOptionNone)):
                return result
            raise TypeError(
                "flat_map_some expected function to return an option value, "
                f"received {_runtime_type_name(result)}"
            )
        if isinstance(opt, GeniaOptionNone):
            return opt
        raise TypeError(f"flat_map_some expected an option value, received {_runtime_type_name(opt)}")

    def _looks_like_get_target(value: Any) -> bool:
        return isinstance(value, (GeniaOptionSome, GeniaOptionNone, GeniaMap))

    def _looks_like_list_target(value: Any) -> bool:
        return isinstance(value, (GeniaOptionSome, GeniaOptionNone, list))

    def _looks_like_find_target(value: Any) -> bool:
        return isinstance(value, (GeniaOptionSome, GeniaOptionNone, str))

    def _resolve_chain_binary_args(
        name: str,
        first: Any,
        second: Any,
        target_predicate: Callable[[Any], bool],
    ) -> tuple[Any, Any]:
        first_is_target = target_predicate(first)
        second_is_target = target_predicate(second)
        if first_is_target and not second_is_target:
            return first, second
        if second_is_target and not first_is_target:
            return second, first
        return second, first

    def then_get_fn(first: Any, second: Any) -> Any:
        target, key = _resolve_chain_binary_args("then_get", first, second, _looks_like_get_target)
        return _get_option_impl("then_get", key, target)

    def _first_option_impl(target: Any) -> Any:
        if isinstance(target, GeniaOptionNone):
            return target
        if isinstance(target, GeniaOptionSome):
            return _first_option_impl(target.value)
        if isinstance(target, list):
            if len(target) == 0:
                return make_none("empty-list")
            return GeniaOptionSome(target[0])
        raise TypeError(f"then_first expected a list, some(list), or none target; received {_runtime_type_name(target)}")

    def then_first_fn(target: Any) -> Any:
        return _first_option_impl(target)

    def _nth_option_impl(index: Any, target: Any) -> Any:
        if not isinstance(index, int) or isinstance(index, bool):
            raise TypeError("then_nth expected an integer index")
        if isinstance(target, GeniaOptionNone):
            return target
        if isinstance(target, GeniaOptionSome):
            return _nth_option_impl(index, target.value)
        if isinstance(target, list):
            size = len(target)
            if index < 0 or index >= size:
                context = GeniaMap().put("index", index).put("length", size)
                return make_none("index-out-of-bounds", context)
            return GeniaOptionSome(target[index])
        raise TypeError(f"then_nth expected a list, some(list), or none target; received {_runtime_type_name(target)}")

    def then_nth_fn(first: Any, second: Any) -> Any:
        target, index = _resolve_chain_binary_args("then_nth", first, second, _looks_like_list_target)
        return _nth_option_impl(index, target)

    def _find_option_impl(needle: Any, target: Any) -> Any:
        safe_needle = _ensure_string(needle, "then_find")
        if isinstance(target, GeniaOptionNone):
            return target
        if isinstance(target, GeniaOptionSome):
            return _find_option_impl(safe_needle, target.value)
        if isinstance(target, str):
            idx = target.find(safe_needle)
            if idx < 0:
                return make_none("not-found", GeniaMap().put("needle", safe_needle))
            return GeniaOptionSome(idx)
        raise TypeError(f"then_find expected a string, some(string), or none target; received {_runtime_type_name(target)}")

    def then_find_fn(first: Any, second: Any) -> Any:
        if isinstance(first, (GeniaOptionSome, GeniaOptionNone)):
            target, needle = first, second
        elif isinstance(second, (GeniaOptionSome, GeniaOptionNone)):
            target, needle = second, first
        elif isinstance(second, str):
            target, needle = second, first
        else:
            target, needle = first, second
        return _find_option_impl(needle, target)

    def or_else_with_fn(first: Any, second: Any) -> Any:
        opt, thunk = _resolve_option_and_other(first, second)
        if isinstance(opt, GeniaOptionSome):
            return opt.value
        if isinstance(opt, GeniaOptionNone):
            return _invoke_from_builtin(thunk, [])
        raise TypeError(f"or_else_with expected an option value, received {_runtime_type_name(opt)}")

    def reduce_error_fn(xs: Any) -> Any:
        raise TypeError(f"reduce expected a list as third argument, received {_runtime_type_name(xs)}")

    def sum_fn(xs: Any) -> Any:
        if not isinstance(xs, list):
            raise TypeError(f"sum expected a list, received {_runtime_type_name(xs)}")
        total: int | float = 0
        for index, item in enumerate(xs, start=1):
            if not isinstance(item, (int, float)) or isinstance(item, bool):
                raise TypeError(
                    "sum expected a list of numbers; "
                    f"item {index} received {_runtime_type_name(item)}. "
                    "Use keep_some(...), keep_some_else(...), flat_map_some(...), or unwrap_or(...) before sum."
                )
            total += item
        return total

    for fn in (
        write_fn,
        writeln_fn,
        flush_fn,
        cli_spec_fn,
        some_fn,
        is_some_fn,
        is_none_fn,
        some_predicate_fn,
        none_predicate_fn,
        unwrap_or_fn,
        or_else_fn,
        or_else_with_fn,
        absence_reason_fn,
        absence_context_fn,
        absence_meta_fn,
        map_some_fn,
        flat_map_some_fn,
        cli_option_or_fn,
        map_put_fn,
        cons_fn,
        car_fn,
        cdr_fn,
        pair_fn,
        null_fn,
        meta_lookup_fn,
        meta_define_fn,
        meta_set_fn,
        meta_extend_fn,
        meta_host_apply_fn,
        meta_eval_error_fn,
        meta_match_pattern_env_fn,
        meta_match_error_fn,
        syntax_error_fn,
        syntax_self_evaluating_fn,
        syntax_symbol_expr_fn,
    ):
        _mark_handles_none(fn)
        _mark_handles_some(fn)

    def rand_fn(*args: Any) -> float:
        if len(args) != 0:
            raise TypeError(f"rand expected 0 args, got {len(args)}")
        return random.random()

    def rng_fn(seed: Any) -> GeniaRng:
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise TypeError("rng expected an integer seed")
        if seed < 0:
            raise ValueError("rng expected seed >= 0")
        return GeniaRng(seed % _RNG_MODULUS)

    def _ensure_rng(value: Any, name: str) -> GeniaRng:
        if not isinstance(value, GeniaRng):
            raise TypeError(f"{name} expected an rng state")
        return value

    def _ensure_rand_int_bound(n: Any) -> int:
        if not isinstance(n, int) or isinstance(n, bool):
            raise TypeError("rand_int expected a positive integer")
        if n <= 0:
            raise ValueError("rand_int expected n > 0")
        return n

    def _rng_next_state(state: int) -> int:
        return (_RNG_MULTIPLIER * state + _RNG_INCREMENT) % _RNG_MODULUS

    def seeded_rand_fn(rng_value: Any) -> list[Any]:
        rng_state = _ensure_rng(rng_value, "rand")
        next_state = _rng_next_state(rng_state.state)
        return [GeniaRng(next_state), next_state / _RNG_MODULUS]

    def rand_int_fn(n: Any) -> int:
        upper = _ensure_rand_int_bound(n)
        return random.randrange(upper)

    def seeded_rand_int_fn(rng_value: Any, n: Any) -> list[Any]:
        rng_state = _ensure_rng(rng_value, "rand_int")
        upper = _ensure_rand_int_bound(n)
        next_state = _rng_next_state(rng_state.state)
        return [GeniaRng(next_state), next_state % upper]

    def sleep_fn(ms: Any) -> None:
        if not isinstance(ms, (int, float)) or isinstance(ms, bool):
            raise TypeError("sleep expected a non-negative number")
        if ms < 0:
            raise ValueError("sleep expected ms >= 0")
        time.sleep(ms / 1000.0)
        return None

    def every_fn(ms: Any) -> GeniaFlow:
        if not isinstance(ms, (int, float)) or isinstance(ms, bool):
            raise TypeError("every expected a non-negative number")
        if ms < 0:
            raise ValueError("every expected ms >= 0")

        def iterator():
            while True:
                time.sleep(ms / 1000.0)
                yield make_none("tick")

        return GeniaFlow(iterator, label=f"every({ms})")

    def utf8_encode_fn(value: Any) -> GeniaBytes:
        text = _ensure_string(value, "utf8_encode")
        return GeniaBytes(text.encode("utf-8"))

    def utf8_decode_fn(value: Any) -> str:
        encoded = _ensure_bytes(value, "utf8_decode")
        try:
            return encoded.value.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"utf8_decode invalid UTF-8: {exc}") from exc

    def json_parse_fn(value: Any) -> Any:
        if not isinstance(value, str):
            context = (
                GeniaMap()
                .put("source", "json_parse")
                .put("expected", "string")
                .put("received", _runtime_type_name(value))
            )
            return make_none("json-parse-error", context)

        text = value
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            context = (
                GeniaMap()
                .put("source", "json_parse")
                .put("message", exc.msg)
                .put("line", exc.lineno)
                .put("column", exc.colno)
            )
            return make_none("json-parse-error", context)
        return _json_to_runtime(parsed)

    def json_stringify_fn(value: Any) -> Any:
        try:
            return json.dumps(_json_from_runtime(value), indent=2, ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError) as exc:
            context = (
                GeniaMap()
                .put("source", "json_stringify")
                .put("message", str(exc))
                .put("received", _runtime_type_name(value))
            )
            return make_none("json-stringify-error", context)

    def _http_headers_to_runtime(headers: Iterable[tuple[str, str]]) -> GeniaMap:
        result = GeniaMap()
        for key, value in headers:
            result = result.put(key.lower(), value)
        return result

    def _http_query_to_runtime(query_text: str) -> GeniaMap:
        result = GeniaMap()
        for key, value in parse_qsl(query_text, keep_blank_values=True):
            result = result.put(key, value)
        return result

    def _http_request_map(request: BaseHTTPRequestHandler) -> GeniaMap:
        parsed_path = urlsplit(request.path)
        raw_body_bytes = b""
        content_length_text = request.headers.get("Content-Length")
        if content_length_text is not None:
            try:
                content_length = max(0, int(content_length_text))
            except ValueError:
                content_length = 0
            if content_length > 0:
                raw_body_bytes = request.rfile.read(content_length)

        raw_body = raw_body_bytes.decode("utf-8", errors="replace")
        content_type = request.headers.get("Content-Type", "")
        body: Any = raw_body
        if content_type.lower().startswith("application/json"):
            body = json_parse_fn(raw_body)

        client_host, client_port = request.client_address[:2]
        return (
            GeniaMap()
            .put("method", request.command.upper())
            .put("path", parsed_path.path or "/")
            .put("query", _http_query_to_runtime(parsed_path.query))
            .put("headers", _http_headers_to_runtime(request.headers.items()))
            .put("body", body)
            .put("raw_body", raw_body)
            .put("client", GeniaMap().put("host", client_host).put("port", client_port))
        )

    def _http_response_headers(value: Any) -> dict[str, str]:
        if value is None or _is_nil_none(value):
            return {}
        if not isinstance(value, GeniaMap):
            raise TypeError(
                "serve_http handler response.headers expected a map, "
                f"received {_runtime_type_name(value)}"
            )

        headers: dict[str, str] = {}
        for _, (raw_key, raw_value) in value._entries.items():
            if not isinstance(raw_key, str) or not isinstance(raw_value, str):
                raise TypeError("serve_http handler response.headers expected string keys and values")
            headers[raw_key] = raw_value
        return headers

    def _http_response_triplet(value: Any) -> tuple[int, dict[str, str], bytes]:
        if not isinstance(value, GeniaMap):
            raise TypeError(
                "serve_http handler must return a response map with status, headers, and body fields"
            )

        status = value.get("status", 200)
        if isinstance(status, bool) or not isinstance(status, int):
            raise TypeError(
                "serve_http handler response.status expected an integer, "
                f"received {_runtime_type_name(status)}"
            )
        if status < 100 or status > 999:
            raise ValueError("serve_http handler response.status expected an integer in [100, 999]")

        headers = _http_response_headers(value.get("headers", GeniaMap()))
        header_names = {name.lower() for name in headers}
        body = value.get("body", "")

        if body is None or is_none(body):
            payload = b""
            if "content-type" not in header_names:
                headers["content-type"] = "text/plain; charset=utf-8"
        elif isinstance(body, str):
            payload = body.encode("utf-8")
            if "content-type" not in header_names:
                headers["content-type"] = "text/plain; charset=utf-8"
        elif isinstance(body, GeniaBytes):
            payload = body.value
            if "content-type" not in header_names:
                headers["content-type"] = "application/octet-stream"
        else:
            raise TypeError(
                "serve_http handler response.body expected a string, bytes, or none, "
                f"received {_runtime_type_name(body)}"
            )

        if "content-length" not in header_names:
            headers["content-length"] = str(len(payload))
        return status, headers, payload

    def serve_http_fn(config_value: Any, handler: Any) -> GeniaMap:
        if not isinstance(config_value, GeniaMap):
            raise TypeError("serve_http expected config to be a map")
        if not callable(handler):
            raise TypeError("serve_http expected a handler function")

        host_value = config_value.get("host", "127.0.0.1")
        if not isinstance(host_value, str):
            raise TypeError(f"serve_http expected config.host to be a string, received {_runtime_type_name(host_value)}")

        port = _ensure_port_int(config_value.get("port", 8000), "serve_http config.port")
        max_requests = _ensure_optional_request_limit(
            config_value.get("max_requests", _UNSET),
            "serve_http config.max_requests",
        )

        class _GeniaHTTPServer(HTTPServer):
            allow_reuse_address = True

        class _GeniaRequestHandler(BaseHTTPRequestHandler):
            def _serve(self) -> None:
                try:
                    request_value = _http_request_map(self)
                    response_value = _invoke_from_builtin(handler, [request_value])
                    status, headers, payload = _http_response_triplet(response_value)
                except Exception as exc:  # pragma: no cover - exercised through HTTP 500 behavior
                    stderr_sink.write_text(f"serve_http handler error: {exc}\n")
                    status = 500
                    headers = {
                        "content-type": "text/plain; charset=utf-8",
                        "content-length": str(len(b"internal server error")),
                    }
                    payload = b"internal server error"

                self.send_response(status)
                for header_name, header_value in headers.items():
                    self.send_header(header_name, header_value)
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(payload)

            def do_GET(self) -> None:
                self._serve()

            def do_POST(self) -> None:
                self._serve()

            def do_PUT(self) -> None:
                self._serve()

            def do_DELETE(self) -> None:
                self._serve()

            def do_PATCH(self) -> None:
                self._serve()

            def do_OPTIONS(self) -> None:
                self._serve()

            def do_HEAD(self) -> None:
                self._serve()

            def log_message(self, format: str, *args: Any) -> None:
                return

        server = _GeniaHTTPServer((host_value, port), _GeniaRequestHandler)
        handled_requests = 0
        try:
            while max_requests is None or handled_requests < max_requests:
                server.handle_request()
                handled_requests += 1
        finally:
            server.server_close()

        bound_host, bound_port = server.server_address[:2]
        return GeniaMap().put("host", bound_host).put("port", bound_port).put("handled_requests", handled_requests)

    def read_file_fn(path: Any) -> Any:
        if not isinstance(path, str):
            context = (
                GeniaMap()
                .put("source", "read_file")
                .put("expected", "string_path")
                .put("received", _runtime_type_name(path))
            )
            return make_none("file-read-error", context)
        try:
            return Path(path).read_text(encoding="utf-8")
        except FileNotFoundError:
            context = GeniaMap().put("source", "read_file").put("path", path)
            return make_none("file-not-found", context)
        except OSError as exc:
            context = GeniaMap().put("source", "read_file").put("path", path).put("message", str(exc))
            return make_none("file-read-error", context)

    def write_file_fn(path: Any, text: Any) -> Any:
        if not isinstance(path, str):
            context = (
                GeniaMap()
                .put("source", "write_file")
                .put("expected", "string_path")
                .put("received", _runtime_type_name(path))
            )
            return make_none("file-write-error", context)
        if not isinstance(text, str):
            context = (
                GeniaMap()
                .put("source", "write_file")
                .put("path", path)
                .put("expected", "string_content")
                .put("received", _runtime_type_name(text))
            )
            return make_none("file-write-error", context)
        try:
            Path(path).write_text(text, encoding="utf-8")
            return path
        except OSError as exc:
            context = GeniaMap().put("source", "write_file").put("path", path).put("message", str(exc))
            return make_none("file-write-error", context)

    def zip_read_fn(path: Any) -> Any:
        if not isinstance(path, str):
            context = (
                GeniaMap()
                .put("source", "zip_read")
                .put("expected", "string_path")
                .put("received", _runtime_type_name(path))
            )
            return make_none("zip-read-error", context)
        if not Path(path).exists():
            context = GeniaMap().put("source", "zip_read").put("path", path)
            return make_none("file-not-found", context)

        def iterator() -> Iterable[Any]:
            with zipfile.ZipFile(path, "r") as archive:
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    yield [info.filename, GeniaBytes(archive.read(info.filename))]

        try:
            with zipfile.ZipFile(path, "r"):
                pass
        except zipfile.BadZipFile:
            context = GeniaMap().put("source", "zip_read").put("path", path)
            return make_none("zip-read-error", context)
        except OSError as exc:
            context = GeniaMap().put("source", "zip_read").put("path", path).put("message", str(exc))
            return make_none("zip-read-error", context)

        return GeniaFlow(iterator, label="zip_read")

    def _zip_item_to_entry(item: Any, index: int) -> Any:
        if isinstance(item, GeniaZipEntry):
            return item
        if not isinstance(item, list) or len(item) != 2:
            context = (
                GeniaMap()
                .put("source", "zip_write")
                .put("index", index)
                .put("expected", "[filename, content]")
                .put("received", _runtime_type_name(item))
            )
            return make_none("zip-write-error", context)

        name = item[0]
        content = item[1]
        if not isinstance(name, str):
            context = (
                GeniaMap()
                .put("source", "zip_write")
                .put("index", index)
                .put("expected", "string_filename")
                .put("received", _runtime_type_name(name))
            )
            return make_none("zip-write-error", context)
        if isinstance(content, str):
            content_bytes = GeniaBytes(content.encode("utf-8"))
        elif isinstance(content, GeniaBytes):
            content_bytes = content
        else:
            context = (
                GeniaMap()
                .put("source", "zip_write")
                .put("index", index)
                .put("filename", name)
                .put("expected", "bytes_or_string_content")
                .put("received", _runtime_type_name(content))
            )
            return make_none("zip-write-error", context)
        return GeniaZipEntry(name, content_bytes)

    def zip_write_flow_fn(path: Any, source: Any) -> Any:
        if not isinstance(path, str):
            context = (
                GeniaMap()
                .put("source", "zip_write")
                .put("expected", "string_path")
                .put("received", _runtime_type_name(path))
            )
            return make_none("zip-write-error", context)

        if isinstance(source, GeniaFlow):
            items = source.consume()
            close_items = source.close_on_early_termination
        elif isinstance(source, list):
            items = iter(source)
            close_items = False
        else:
            context = (
                GeniaMap()
                .put("source", "zip_write")
                .put("path", path)
                .put("expected", "flow_or_list")
                .put("received", _runtime_type_name(source))
            )
            return make_none("zip-write-error", context)

        try:
            try:
                with zipfile.ZipFile(path, "w") as archive:
                    for index, item in enumerate(items, start=1):
                        entry = _zip_item_to_entry(item, index)
                        if isinstance(entry, GeniaOptionNone):
                            return entry
                        archive.writestr(entry.name, entry.data.value)
                return path
            finally:
                if close_items:
                    _maybe_close_iterable(items)
        except OSError as exc:
            context = GeniaMap().put("source", "zip_write").put("path", path).put("message", str(exc))
            return make_none("zip-write-error", context)

    def zip_entries_fn(path: Any) -> list[GeniaZipEntry]:
        zip_path = _ensure_string(path, "zip_entries")
        try:
            with zipfile.ZipFile(zip_path, "r") as archive:
                entries: list[GeniaZipEntry] = []
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    entries.append(GeniaZipEntry(info.filename, GeniaBytes(archive.read(info.filename))))
                return entries
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"zip_entries could not read zip file: {zip_path}") from exc
        except zipfile.BadZipFile as exc:
            raise ValueError(f"zip_entries invalid zip archive: {zip_path}") from exc
        except OSError as exc:
            raise OSError(f"zip_entries could not read zip file: {zip_path}") from exc

    def entry_name_fn(entry: Any) -> str:
        return _ensure_zip_entry(entry, "entry_name").name

    def entry_bytes_fn(entry: Any) -> GeniaBytes:
        return _ensure_zip_entry(entry, "entry_bytes").data

    def set_entry_bytes_fn(entry: Any, new_bytes: Any) -> GeniaZipEntry:
        zip_entry = _ensure_zip_entry(entry, "set_entry_bytes")
        data = _ensure_bytes(new_bytes, "set_entry_bytes")
        return GeniaZipEntry(zip_entry.name, data)

    def update_entry_bytes_fn(entry: Any, updater: Any) -> GeniaZipEntry:
        zip_entry = _ensure_zip_entry(entry, "update_entry_bytes")
        if not callable(updater):
            raise TypeError("update_entry_bytes expected a function as second argument")
        next_data = updater(zip_entry.data)
        if not isinstance(next_data, GeniaBytes):
            raise TypeError("update_entry_bytes updater must return bytes")
        return GeniaZipEntry(zip_entry.name, next_data)

    def entry_json_fn(entry: Any) -> bool:
        zip_entry = _ensure_zip_entry(entry, "entry_json")
        return zip_entry.name.lower().endswith(".json")

    def zip_write_fn(first: Any, second: Any) -> str:
        if isinstance(first, str) and isinstance(second, list):
            out_path = first
            entries = second
        elif isinstance(first, list) and isinstance(second, str):
            entries = first
            out_path = second
        else:
            raise TypeError("zip_write expected (entries, path) or (path, entries)")

        for item in entries:
            if not isinstance(item, GeniaZipEntry):
                raise TypeError("zip_write expected a list of zip entries")

        try:
            with zipfile.ZipFile(out_path, "w") as archive:
                for item in entries:
                    archive.writestr(item.name, item.data.value)
        except OSError as exc:
            raise OSError(f"zip_write could not write zip file: {out_path}") from exc
        return out_path

    env.set("stdout", stdout_sink)
    env.set("stderr", stderr_sink)
    env.set("_write", write_fn)
    env.set("_writeln", writeln_fn)
    env.set("_flush", flush_fn)
    env.set("_clear_screen", clear_screen_fn)
    env.set("_move_cursor", move_cursor_fn)
    env.set("_render_grid", render_grid_fn)
    env.set("log", log)
    env.set("print", print_fn)
    env.set("display", display_fn)
    env.set("debug_repr", debug_repr_fn)
    env.set("input", input_fn)
    env.set("stdin", stdin_source)
    env.set("stdin_keys", stdin_keys_flow)
    env.set("_flow?", flow_predicate_fn)
    env.set("_lines", lines_fn)
    env.set("_evolve", tick_fn)
    env.set("_tee", tee_fn)
    env.set("_merge", merge_flow_fn)
    env.set("_zip", zip_flow_fn)
    env.set("_scan", scan_fn)
    env.set("_keep_some", keep_some_fn)
    env.set("_keep_some_else", keep_some_else_fn)
    env.set("_each", each_fn)
    env.set("_rules_prepare", rules_prepare_fn)
    env.set("_rules_kernel", rules_kernel_fn)
    env.set("_rules_error", rules_error_fn)
    env.set("_flow_debug", flow_debug_fn)
    env.set("_run", run_fn)
    env.set("_collect", collect_fn)
    env.set("argv", argv_fn)
    env.set("help", help_fn)
    env.set("doc", doc_fn)
    env.set("meta", meta_fn)
    env.set("pi", math.pi)
    env.set("e", math.e)
    env.set("true", True)
    env.set("false", False)
    env.set("nil", OPTION_NONE)
    env.set("none", OPTION_NONE)
    env.set("_some", some_fn)
    env.set("_none?", none_predicate_fn)
    env.set("_some?", some_predicate_fn)
    env.set("_get", get_fn)
    env.set("_get?", get_option_fn)
    env.set("_map_some", map_some_fn)
    env.set("_flat_map_some", flat_map_some_fn)
    env.set("_then_get", then_get_fn)
    env.set("_then_first", then_first_fn)
    env.set("_then_nth", then_nth_fn)
    env.set("_then_find", then_find_fn)
    env.set("_or_else", or_else_fn)
    env.set("_or_else_with", or_else_with_fn)
    env.set("_unwrap_or", unwrap_or_fn)
    env.set("_absence_reason", absence_reason_fn)
    env.set("_absence_context", absence_context_fn)
    env.set("_absence_meta", absence_meta_fn)
    env.set("_is_some?", is_some_fn)
    env.set("_is_none?", is_none_fn)
    env.set("force", force_fn)
    env.set("_meta_empty_env", meta_empty_env_fn)
    env.set("_meta_lookup", meta_lookup_fn)
    env.set("_meta_define", meta_define_fn)
    env.set("_meta_set", meta_set_fn)
    env.set("_meta_extend", meta_extend_fn)
    env.set("_meta_host_apply", meta_host_apply_fn)
    env.set("_meta_eval_error", meta_eval_error_fn)
    env.set("_meta_match_pattern_env", meta_match_pattern_env_fn)
    env.set("_meta_match_error", meta_match_error_fn)
    env.set("_syntax_error", syntax_error_fn)
    env.set("_syntax_self_evaluating", syntax_self_evaluating_fn)
    env.set("_syntax_symbol_expr", syntax_symbol_expr_fn)
    env.set("cons", cons_fn)
    env.set("car", car_fn)
    env.set("cdr", cdr_fn)
    env.set("pair?", pair_fn)
    env.set("null?", null_fn)
    env.set("_ref", ref_fn)
    env.set("_ref_get", ref_get_fn)
    env.set("_ref_set", ref_set_fn)
    env.set("_ref_is_set", ref_is_set_fn)
    env.set("_ref_update", ref_update_fn)
    env.set("_cell_new", cell_new_fn)
    env.set("_cell_with_state", cell_with_state_fn)
    env.set("_cell_send", cell_send_fn)
    env.set("_cell_get", cell_get_fn)
    env.set("_cell_failed?", cell_failed_fn)
    env.set("_cell_error", cell_error_fn)
    env.set("_restart_cell", restart_cell_fn)
    env.set("_cell_status", cell_status_fn)
    env.set("_cell_alive?", cell_alive_fn)
    env.set("_cell_stop", cell_stop_fn)
    env.set("_spawn", spawn_fn)
    env.set("_send", send_fn)
    env.set("_process_alive?", process_alive_fn)
    env.set("_process_failed?", process_failed_fn)
    env.set("_process_error", process_error_fn)
    env.set("_actor_validate_effect", actor_validate_effect_fn)
    env.set("_actor_call_update", actor_call_update_fn)
    env.set("_map_new", map_new_fn)
    env.set("_map_get", map_get_fn)
    env.set("_map_put", map_put_fn)
    env.set("_map_has?", map_has_fn)
    env.set("_map_remove", map_remove_fn)
    env.set("_map_count", map_count_fn)
    env.set("_map_items", map_items_fn)
    env.set("_pairs_error", pairs_error_fn)
    env.set("_rng", rng_fn)
    env.set("_rand", rand_fn)
    env.set("_rand_seeded", seeded_rand_fn)
    env.set("_rand_int", rand_int_fn)
    env.set("_rand_int_seeded", seeded_rand_int_fn)
    env.set("sleep", sleep_fn)
    env.set("every", every_fn)
    env.set("_byte_length", byte_length_fn)
    env.set("_is_empty", is_empty_fn)
    env.set("_concat", concat_fn)
    env.set("_contains", contains_fn)
    env.set("_starts_with", starts_with_fn)
    env.set("_ends_with", ends_with_fn)
    env.set("_find", find_fn)
    env.set("_split", split_fn)
    env.set("_split_whitespace", split_whitespace_fn)
    env.set("_join", join_fn)
    env.set("_trim", trim_fn)
    env.set("_trim_start", trim_start_fn)
    env.set("_trim_end", trim_end_fn)
    env.set("_lower", lower_fn)
    env.set("_upper", upper_fn)
    env.set("_parse_int", parse_int_fn)
    env.set("utf8_decode", utf8_decode_fn)
    env.set("utf8_encode", utf8_encode_fn)
    env.set("_read_file", read_file_fn)
    env.set("_write_file", write_file_fn)
    env.set("_json_parse", json_parse_fn)
    env.set("_json_stringify", json_stringify_fn)
    env.set("_serve_http", serve_http_fn)
    env.set("_zip_read", zip_read_fn)
    env.set("_zip_write", zip_write_flow_fn)
    env.set("zip_entries", zip_entries_fn)
    env.set("entry_name", entry_name_fn)
    env.set("entry_bytes", entry_bytes_fn)
    env.set("set_entry_bytes", set_entry_bytes_fn)
    env.set("update_entry_bytes", update_entry_bytes_fn)
    env.set("entry_json", entry_json_fn)
    env.set("_cli_spec", cli_spec_fn)
    env.set("_cli_chars", cli_chars_fn)
    env.set("_cli_type_error", cli_type_error_fn)
    env.set("_cli_value_error", cli_value_error_fn)
    env.set("_cli_flag?", cli_flag_fn)
    env.set("_cli_option", cli_option_fn)
    env.set("_cli_option_or", cli_option_or_fn)
    env.set("_sum", sum_fn)
    env.set("_reduce_error", reduce_error_fn)
    env.set("apply_raw", apply_raw_fn)

    env.register_autoload("cli_parse", 1, "std/prelude/cli.genia")
    env.register_autoload("cli_parse", 2, "std/prelude/cli.genia")
    env.register_autoload("cli_flag?", 2, "std/prelude/cli.genia")
    env.register_autoload("cli_option", 2, "std/prelude/cli.genia")
    env.register_autoload("cli_option_or", 3, "std/prelude/cli.genia")
    env.register_autoload("lines", 1, "std/prelude/flow.genia")
    env.register_autoload("evolve", 0, "std/prelude/flow.genia")
    env.register_autoload("evolve", 1, "std/prelude/flow.genia")
    env.register_autoload("tee", 1, "std/prelude/flow.genia")
    env.register_autoload("merge", 1, "std/prelude/flow.genia")
    env.register_autoload("merge", 2, "std/prelude/flow.genia")
    env.register_autoload("zip", 1, "std/prelude/flow.genia")
    env.register_autoload("zip", 2, "std/prelude/flow.genia")
    env.register_autoload("scan", 2, "std/prelude/flow.genia")
    env.register_autoload("scan", 3, "std/prelude/flow.genia")
    env.register_autoload("keep_some", 1, "std/prelude/flow.genia")
    env.register_autoload("keep_some", 2, "std/prelude/flow.genia")
    env.register_autoload("keep_some_else", 2, "std/prelude/flow.genia")
    env.register_autoload("keep_some_else", 3, "std/prelude/flow.genia")
    env.register_autoload("rules", 0, "std/prelude/flow.genia")
    env.register_autoload("refine", 0, "std/prelude/flow.genia")
    env.register_autoload("each", 2, "std/prelude/flow.genia")
    env.register_autoload("collect", 1, "std/prelude/flow.genia")
    env.register_autoload("run", 1, "std/prelude/flow.genia")
    env.register_autoload("list", 0, "std/prelude/list.genia")
    env.register_autoload("first", 1, "std/prelude/list.genia")
    env.register_autoload("first_opt", 1, "std/prelude/list.genia")
    env.register_autoload("last", 1, "std/prelude/list.genia")
    env.register_autoload("find_opt", 2, "std/prelude/list.genia")
    env.register_autoload("rest", 1, "std/prelude/list.genia")
    env.register_autoload("empty?", 1, "std/prelude/list.genia")
    env.register_autoload("nil?", 1, "std/prelude/list.genia")
    env.register_autoload("append", 2, "std/prelude/list.genia")
    env.register_autoload("length", 1, "std/prelude/list.genia")
    env.register_autoload("reverse", 1, "std/prelude/list.genia")
    env.register_autoload("reduce", 3, "std/prelude/list.genia")
    env.register_autoload("map", 2, "std/prelude/list.genia")
    env.register_autoload("filter", 2, "std/prelude/list.genia")
    env.register_autoload("count", 1, "std/prelude/list.genia")
    env.register_autoload("any?", 2, "std/prelude/list.genia")
    env.register_autoload("nth", 2, "std/prelude/list.genia")
    env.register_autoload("nth_opt", 2, "std/prelude/list.genia")
    env.register_autoload("take", 2, "std/prelude/list.genia")
    env.register_autoload("head", 1, "std/prelude/list.genia")
    env.register_autoload("head", 2, "std/prelude/list.genia")
    env.register_autoload("drop", 2, "std/prelude/list.genia")
    env.register_autoload("range", 1, "std/prelude/list.genia")
    env.register_autoload("range", 2, "std/prelude/list.genia")
    env.register_autoload("range", 3, "std/prelude/list.genia")
    env.register_autoload("apply", 2, "std/prelude/fn.genia")
    env.register_autoload("compose", 1, "std/prelude/fn.genia")
    env.register_autoload("inspect", 1, "std/prelude/fn.genia")
    env.register_autoload("trace", 2, "std/prelude/fn.genia")
    env.register_autoload("tap", 2, "std/prelude/fn.genia")
    env.register_autoload("rule_skip", 0, "std/prelude/flow.genia")
    env.register_autoload("step_skip", 0, "std/prelude/flow.genia")
    env.register_autoload("rule_emit", 1, "std/prelude/flow.genia")
    env.register_autoload("step_emit", 1, "std/prelude/flow.genia")
    env.register_autoload("rule_emit_many", 1, "std/prelude/flow.genia")
    env.register_autoload("step_emit_many", 1, "std/prelude/flow.genia")
    env.register_autoload("rule_set", 1, "std/prelude/flow.genia")
    env.register_autoload("step_set", 1, "std/prelude/flow.genia")
    env.register_autoload("rule_ctx", 1, "std/prelude/flow.genia")
    env.register_autoload("step_ctx", 1, "std/prelude/flow.genia")
    env.register_autoload("rule_halt", 0, "std/prelude/flow.genia")
    env.register_autoload("step_halt", 0, "std/prelude/flow.genia")
    env.register_autoload("rule_step", 3, "std/prelude/flow.genia")
    env.register_autoload("step_step", 3, "std/prelude/flow.genia")
    env.register_autoload("map_new", 0, "std/prelude/map.genia")
    env.register_autoload("map_get", 2, "std/prelude/map.genia")
    env.register_autoload("map_put", 3, "std/prelude/map.genia")
    env.register_autoload("map_has?", 2, "std/prelude/map.genia")
    env.register_autoload("map_remove", 2, "std/prelude/map.genia")
    env.register_autoload("map_count", 1, "std/prelude/map.genia")
    env.register_autoload("map_items", 1, "std/prelude/map.genia")
    env.register_autoload("map_item_key", 1, "std/prelude/map.genia")
    env.register_autoload("map_item_value", 1, "std/prelude/map.genia")
    env.register_autoload("map_keys", 1, "std/prelude/map.genia")
    env.register_autoload("map_values", 1, "std/prelude/map.genia")
    env.register_autoload("pairs", 2, "std/prelude/map.genia")
    env.register_autoload("rng", 1, "std/prelude/random.genia")
    env.register_autoload("rand", 0, "std/prelude/random.genia")
    env.register_autoload("rand", 1, "std/prelude/random.genia")
    env.register_autoload("rand_int", 1, "std/prelude/random.genia")
    env.register_autoload("rand_int", 2, "std/prelude/random.genia")
    env.register_autoload("ref", 0, "std/prelude/ref.genia")
    env.register_autoload("ref", 1, "std/prelude/ref.genia")
    env.register_autoload("ref_get", 1, "std/prelude/ref.genia")
    env.register_autoload("ref_set", 2, "std/prelude/ref.genia")
    env.register_autoload("ref_is_set", 1, "std/prelude/ref.genia")
    env.register_autoload("ref_update", 2, "std/prelude/ref.genia")
    env.register_autoload("spawn", 1, "std/prelude/process.genia")
    env.register_autoload("send", 2, "std/prelude/process.genia")
    env.register_autoload("process_alive?", 1, "std/prelude/process.genia")
    env.register_autoload("write", 2, "std/prelude/io.genia")
    env.register_autoload("writeln", 2, "std/prelude/io.genia")
    env.register_autoload("flush", 1, "std/prelude/io.genia")
    env.register_autoload("clear_screen", 0, "std/prelude/io.genia")
    env.register_autoload("move_cursor", 2, "std/prelude/io.genia")
    env.register_autoload("render_grid", 1, "std/prelude/io.genia")
    env.register_autoload("some", 1, "std/prelude/option.genia")
    env.register_autoload("none?", 1, "std/prelude/option.genia")
    env.register_autoload("some?", 1, "std/prelude/option.genia")
    env.register_autoload("get", 2, "std/prelude/option.genia")
    env.register_autoload("get?", 2, "std/prelude/option.genia")
    env.register_autoload("map_some", 2, "std/prelude/option.genia")
    env.register_autoload("flat_map_some", 2, "std/prelude/option.genia")
    env.register_autoload("then_get", 2, "std/prelude/option.genia")
    env.register_autoload("then_first", 1, "std/prelude/option.genia")
    env.register_autoload("then_nth", 2, "std/prelude/option.genia")
    env.register_autoload("then_find", 2, "std/prelude/option.genia")
    env.register_autoload("or_else", 2, "std/prelude/option.genia")
    env.register_autoload("or_else_with", 2, "std/prelude/option.genia")
    env.register_autoload("unwrap_or", 2, "std/prelude/option.genia")
    env.register_autoload("absence_reason", 1, "std/prelude/option.genia")
    env.register_autoload("absence_context", 1, "std/prelude/option.genia")
    env.register_autoload("absence_meta", 1, "std/prelude/option.genia")
    env.register_autoload("is_some?", 1, "std/prelude/option.genia")
    env.register_autoload("is_none?", 1, "std/prelude/option.genia")
    env.register_autoload("byte_length", 1, "std/prelude/string.genia")
    env.register_autoload("is_empty", 1, "std/prelude/string.genia")
    env.register_autoload("concat", 2, "std/prelude/string.genia")
    env.register_autoload("contains", 2, "std/prelude/string.genia")
    env.register_autoload("starts_with", 2, "std/prelude/string.genia")
    env.register_autoload("ends_with", 2, "std/prelude/string.genia")
    env.register_autoload("find", 2, "std/prelude/string.genia")
    env.register_autoload("split", 2, "std/prelude/string.genia")
    env.register_autoload("split_whitespace", 1, "std/prelude/string.genia")
    env.register_autoload("join", 2, "std/prelude/string.genia")
    env.register_autoload("trim", 1, "std/prelude/string.genia")
    env.register_autoload("trim_start", 1, "std/prelude/string.genia")
    env.register_autoload("trim_end", 1, "std/prelude/string.genia")
    env.register_autoload("lower", 1, "std/prelude/string.genia")
    env.register_autoload("upper", 1, "std/prelude/string.genia")
    env.register_autoload("parse_int", 1, "std/prelude/string.genia")
    env.register_autoload("parse_int", 2, "std/prelude/string.genia")
    env.register_autoload("json_parse", 1, "std/prelude/json.genia")
    env.register_autoload("json_stringify", 1, "std/prelude/json.genia")
    env.register_autoload("json_pretty", 1, "std/prelude/json.genia")
    env.register_autoload("read_file", 1, "std/prelude/file.genia")
    env.register_autoload("write_file", 2, "std/prelude/file.genia")
    env.register_autoload("zip_read", 1, "std/prelude/file.genia")
    env.register_autoload("zip_write", 1, "std/prelude/file.genia")
    env.register_autoload("zip_write", 2, "std/prelude/file.genia")
    env.register_autoload("stream_cons", 2, "std/prelude/stream.genia")
    env.register_autoload("stream_head", 1, "std/prelude/stream.genia")
    env.register_autoload("stream_tail", 1, "std/prelude/stream.genia")
    env.register_autoload("stream_map", 2, "std/prelude/stream.genia")
    env.register_autoload("stream_take", 2, "std/prelude/stream.genia")
    env.register_autoload("stream_filter", 2, "std/prelude/stream.genia")
    env.register_autoload("self_evaluating?", 1, "std/prelude/syntax.genia")
    env.register_autoload("symbol_expr?", 1, "std/prelude/syntax.genia")
    env.register_autoload("tagged_list?", 2, "std/prelude/syntax.genia")
    env.register_autoload("quoted_expr?", 1, "std/prelude/syntax.genia")
    env.register_autoload("quasiquoted_expr?", 1, "std/prelude/syntax.genia")
    env.register_autoload("assignment_expr?", 1, "std/prelude/syntax.genia")
    env.register_autoload("lambda_expr?", 1, "std/prelude/syntax.genia")
    env.register_autoload("application_expr?", 1, "std/prelude/syntax.genia")
    env.register_autoload("block_expr?", 1, "std/prelude/syntax.genia")
    env.register_autoload("match_expr?", 1, "std/prelude/syntax.genia")
    env.register_autoload("text_of_quotation", 1, "std/prelude/syntax.genia")
    env.register_autoload("assignment_name", 1, "std/prelude/syntax.genia")
    env.register_autoload("assignment_value", 1, "std/prelude/syntax.genia")
    env.register_autoload("lambda_params", 1, "std/prelude/syntax.genia")
    env.register_autoload("lambda_body", 1, "std/prelude/syntax.genia")
    env.register_autoload("operator", 1, "std/prelude/syntax.genia")
    env.register_autoload("operands", 1, "std/prelude/syntax.genia")
    env.register_autoload("block_expressions", 1, "std/prelude/syntax.genia")
    env.register_autoload("match_branches", 1, "std/prelude/syntax.genia")
    env.register_autoload("branch_pattern", 1, "std/prelude/syntax.genia")
    env.register_autoload("branch_has_guard?", 1, "std/prelude/syntax.genia")
    env.register_autoload("branch_guard", 1, "std/prelude/syntax.genia")
    env.register_autoload("branch_body", 1, "std/prelude/syntax.genia")
    env.register_autoload("empty_env", 0, "std/prelude/eval.genia")
    env.register_autoload("lookup", 2, "std/prelude/eval.genia")
    env.register_autoload("define", 3, "std/prelude/eval.genia")
    env.register_autoload("set", 3, "std/prelude/eval.genia")
    env.register_autoload("extend", 3, "std/prelude/eval.genia")
    env.register_autoload("eval", 2, "std/prelude/eval.genia")

    env.register_autoload("inc", 1, "std/prelude/math.genia")
    env.register_autoload("dec", 1, "std/prelude/math.genia")
    env.register_autoload("mod", 2, "std/prelude/math.genia")
    env.register_autoload("abs", 1, "std/prelude/math.genia")
    env.register_autoload("min", 2, "std/prelude/math.genia")
    env.register_autoload("max", 2, "std/prelude/math.genia")
    env.register_autoload("sum", 1, "std/prelude/math.genia")
    env.register_autoload("awkify", 2, "std/prelude/awk.genia")
    env.register_autoload("awk_filter", 2, "std/prelude/awk.genia")
    env.register_autoload("awk_map", 2, "std/prelude/awk.genia")
    env.register_autoload("awk_count", 2, "std/prelude/awk.genia")
    env.register_autoload("fields", 1, "std/prelude/awk.genia")
    env.register_autoload("cell", 1, "std/prelude/cell.genia")
    env.register_autoload("cell_with_state", 1, "std/prelude/cell.genia")
    env.register_autoload("cell_send", 2, "std/prelude/cell.genia")
    env.register_autoload("cell_get", 1, "std/prelude/cell.genia")
    env.register_autoload("cell_state", 1, "std/prelude/cell.genia")
    env.register_autoload("cell_failed?", 1, "std/prelude/cell.genia")
    env.register_autoload("cell_error", 1, "std/prelude/cell.genia")
    env.register_autoload("restart_cell", 2, "std/prelude/cell.genia")
    env.register_autoload("cell_status", 1, "std/prelude/cell.genia")
    env.register_autoload("cell_alive?", 1, "std/prelude/cell.genia")
    env.register_autoload("cell_stop", 1, "std/prelude/cell.genia")
    env.register_autoload("actor", 2, "std/prelude/actor.genia")
    env.register_autoload("actor_send", 2, "std/prelude/actor.genia")
    env.register_autoload("actor_call", 2, "std/prelude/actor.genia")
    env.register_autoload("actor_alive?", 1, "std/prelude/actor.genia")
    env.register_autoload("actor_stop", 1, "std/prelude/actor.genia")
    env.register_autoload("actor_restart", 2, "std/prelude/actor.genia")
    env.register_autoload("actor_state", 1, "std/prelude/actor.genia")
    env.register_autoload("actor_failed?", 1, "std/prelude/actor.genia")
    env.register_autoload("actor_error", 1, "std/prelude/actor.genia")
    env.register_autoload("actor_status", 1, "std/prelude/actor.genia")
    return env


def is_complete(source: str) -> bool:
    brace = paren = bracket = 0
    in_str: Optional[str] = None
    esc = False
    for ch in source:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
            continue
        if ch in ('"', "'"):
            in_str = ch
        elif ch == '{':
            brace += 1
        elif ch == '}':
            brace -= 1
        elif ch == '(':
            paren += 1
        elif ch == ')':
            paren -= 1
        elif ch == '[':
            bracket += 1
        elif ch == ']':
            bracket -= 1
    if in_str or brace > 0 or paren > 0 or bracket > 0:
        return False
    # If the last nonblank line ends with =, |, -> or ?, keep reading.
    lines = [ln.rstrip() for ln in source.splitlines() if ln.strip()]
    if not lines:
        return True
    last = lines[-1].rstrip()
    return not (last.endswith("=") or last.endswith("|") or last.endswith("->") or last.endswith("?"))


def run_source(
    source: str,
    env: Env,
    *,
    filename: str = "<memory>",
    debug_hooks: DebugHooks | None = None,
    debug_mode: bool = False,
) -> Any:
    effective_hooks = debug_hooks or env.debug_hooks or NOOP_DEBUG_HOOKS
    effective_debug_mode = debug_mode or env.debug_mode
    tokens = lex(source)
    parser = Parser(tokens, source=source, filename=filename)
    ast_nodes = parser.parse_program()
    ir_nodes = lower_program(ast_nodes)
    assert_portable_core_ir(ir_nodes)
    ir_nodes = optimize_program(ir_nodes, debug=os.getenv("GENIA_DEBUG_OPT", "") == "1")
    env.debug_hooks = effective_hooks
    env.debug_mode = effective_debug_mode
    result = Evaluator(env, debug_hooks=effective_hooks, debug_mode=effective_debug_mode).eval_program(ir_nodes)
    return _normalize_absence(result)


def _scan_pipe_mode_reserved_usage(node: Node, bound_names: set[str]) -> tuple[bool, bool]:
    """Return whether unbound stdin/run identifiers appear in a pipe stage expression."""
    if isinstance(node, Var):
        return node.name == "stdin" and node.name not in bound_names, node.name == "run" and node.name not in bound_names

    if isinstance(node, Lambda):
        nested_bound = set(bound_names)
        if node.pattern is not None:
            nested_bound.update(_pattern_bound_names(node.pattern))
        else:
            nested_bound.update(node.params)
            if node.rest_param is not None:
                nested_bound.add(node.rest_param)
        return _scan_pipe_mode_reserved_usage(node.body, nested_bound)

    if isinstance(node, Block):
        local_bound = set(bound_names)
        saw_stdin = False
        saw_run = False
        for expr in node.exprs:
            uses_stdin, uses_run = _scan_pipe_mode_reserved_usage(expr, local_bound)
            saw_stdin = saw_stdin or uses_stdin
            saw_run = saw_run or uses_run
            if isinstance(expr, Assign):
                local_bound.add(expr.name)
            if saw_stdin and saw_run:
                break
        return saw_stdin, saw_run

    if not is_dataclass(node):
        return False, False

    saw_stdin = False
    saw_run = False
    for node_field in fields(node):
        if node_field.name == "span":
            continue
        uses_stdin, uses_run = _scan_pipe_mode_reserved_usage_value(getattr(node, node_field.name), bound_names)
        saw_stdin = saw_stdin or uses_stdin
        saw_run = saw_run or uses_run
        if saw_stdin and saw_run:
            break
    return saw_stdin, saw_run


def _pattern_bound_names(pattern: Node) -> set[str]:
    if isinstance(pattern, Var):
        return {pattern.name}
    if isinstance(pattern, RestPattern):
        return {pattern.name} if pattern.name is not None else set()
    if isinstance(pattern, SomePattern):
        return _pattern_bound_names(pattern.inner)
    if isinstance(pattern, NoneOption):
        names: set[str] = set()
        if pattern.reason is not None:
            names.update(_pattern_bound_names(pattern.reason))
        if pattern.context is not None:
            names.update(_pattern_bound_names(pattern.context))
        return names
    if isinstance(pattern, (TuplePattern, ListPattern)):
        names: set[str] = set()
        for item in pattern.items:
            names.update(_pattern_bound_names(item))
        return names
    if isinstance(pattern, MapPattern):
        names: set[str] = set()
        for _, value in pattern.items:
            names.update(_pattern_bound_names(value))
        return names
    return set()


def _scan_pipe_mode_reserved_usage_value(value: Any, bound_names: set[str]) -> tuple[bool, bool]:
    if isinstance(value, Node):
        return _scan_pipe_mode_reserved_usage(value, bound_names)
    if isinstance(value, (list, tuple)):
        saw_stdin = False
        saw_run = False
        for item in value:
            uses_stdin, uses_run = _scan_pipe_mode_reserved_usage_value(item, bound_names)
            saw_stdin = saw_stdin or uses_stdin
            saw_run = saw_run or uses_run
            if saw_stdin and saw_run:
                break
        return saw_stdin, saw_run
    return False, False


def _validate_pipe_mode_expr(source: str) -> None:
    tokens = lex(source)
    parser = Parser(tokens, source=source, filename="<pipe>")
    ast_nodes = parser.parse_program()
    if len(ast_nodes) != 1 or not isinstance(ast_nodes[0], ExprStmt):
        raise ValueError("-p/--pipe expects a single stage expression")

    uses_stdin, uses_run = _scan_pipe_mode_reserved_usage(ast_nodes[0].expr, set())
    if uses_stdin:
        raise ValueError("-p/--pipe stage expression must omit stdin; it is added automatically")
    if uses_run:
        raise ValueError("-p/--pipe stage expression must omit run; it is added automatically")


def _wrap_pipe_mode_expr(source: str) -> str:
    _validate_pipe_mode_expr(source)
    return f"stdin |> lines |> {source} |> run"


def _emit_result(env: Env, value: Any) -> None:
    sink = env.get("stdout")
    if not isinstance(sink, GeniaOutputSink):
        raise RuntimeError("stdout sink is not configured")
    sink.write_text(format_debug(value) + "\n")


def _emit_error(env: Env, message: str) -> None:
    sink = env.values.get("stderr")
    if isinstance(sink, GeniaOutputSink):
        sink.write_text(message + "\n")
    else:
        try:
            sys.stderr.write(message + "\n")
            sys.stderr.flush()
        except BrokenPipeError:
            return


def repl() -> None:
    env = make_global_env([])
    try:
        env.get("_writeln")(env.get("stdout"), "Genia prototype REPL. Type :help for examples, :quit to exit.")
    except GeniaQuietBrokenPipe:
        return
    buf = ""
    while True:
        try:
            prompt = "... " if buf else ">>> "
            line = input(prompt)
        except EOFError:
            try:
                env.get("_writeln")(env.get("stdout"), "")
            except GeniaQuietBrokenPipe:
                return
            break
        if not buf and line.strip() == ":quit":
            break
        if not buf and line.strip() == ":help":
            env.get("help")()
            continue
        if not buf and line.strip() == ":env":
            for k in sorted(env.values):
                env.get("_writeln")(env.get("stdout"), f"{k} = {format_debug(env.values[k])}")
            continue
        buf += line + "\n"
        if not is_complete(buf):
            continue
        source = buf
        buf = ""
        if not source.strip():
            continue
        try:
            result = run_source(source, env)
            if result is not None:
                _emit_result(env, result)
        except GeniaQuietBrokenPipe:
            return
        except Exception as e:  # noqa: BLE001
            _emit_error(env, f"Error: {e}")


def run_debug_stdio(
    program_path: str,
    *,
    command_stream: Any = None,
    event_stream: Any = None,
    error_stream: Any = None,
) -> int:
    from .debug_controller import StdioDebugSession

    command_stream = command_stream or sys.stdin
    event_stream = event_stream or sys.stdout
    error_stream = error_stream or sys.stderr
    resolved_path = str(Path(program_path).resolve())
    source = Path(program_path).read_text(encoding="utf-8")
    session = StdioDebugSession(command_stream, event_stream, filename=resolved_path)
    env = make_global_env(
        debug_hooks=session,
        debug_mode=True,
        output_handler=session.emit_stdout_output,
        stderr_stream=error_stream,
    )
    session.ensure_root_frame(env)
    return session.run(lambda: run_source(source, env, filename=resolved_path, debug_hooks=session, debug_mode=True), error_stream=error_stream)


@dataclass
class ExecutionMode:
    kind: str
    source: str | None = None
    program_path: str | None = None
    script_args: list[str] = field(default_factory=list)


def _select_execution_mode(
    args: argparse.Namespace,
    remaining_args: list[str],
    *,
    explicit_terminator_used: bool,
    terminator_index: int | None,
    parser: argparse.ArgumentParser,
) -> ExecutionMode:
    if args.command is None and args.pipe is None and remaining_args and remaining_args[0].startswith("-"):
        if not explicit_terminator_used and terminator_index is None:
            parser.error(
                "expected a source file path when not using -c/--command or -p/--pipe; "
                f"got option-like argument '{remaining_args[0]}'"
            )

    program_path: Optional[str] = None
    script_args: list[str] = []
    if args.command is not None or args.pipe is not None:
        script_args = remaining_args
    elif remaining_args:
        program_path = remaining_args[0]
        script_args = remaining_args[1:]

    if args.debug_stdio:
        if args.command is not None:
            parser.error("--debug-stdio cannot be used with --command")
        if args.pipe is not None:
            parser.error("--debug-stdio cannot be used with --pipe")
        if program_path is None:
            parser.error("--debug-stdio requires a program path")
        if script_args:
            parser.error("--debug-stdio accepts exactly one program path")
        if not Path(program_path).is_file():
            parser.error(f"--debug-stdio program path not found: {program_path}")
        return ExecutionMode(kind="debug_stdio", program_path=program_path)

    if args.pipe is not None:
        return ExecutionMode(kind="pipe", source=args.pipe, script_args=script_args)
    if args.command is not None:
        return ExecutionMode(kind="command", source=args.command, script_args=script_args)
    if program_path is not None:
        return ExecutionMode(kind="file", program_path=program_path, script_args=script_args)
    return ExecutionMode(kind="repl")


def _resolve_program_result(run_result: Any, env: Env) -> Any:
    main_group = env.values.get("main")
    if not isinstance(main_group, GeniaFunctionGroup):
        return run_result
    main_with_args = main_group.get(1)
    if main_with_args is not None:
        cli_args = env.get("argv")()
        return _normalize_absence(main_with_args(cli_args))
    main_without_args = main_group.get(0)
    if main_without_args is not None:
        return _normalize_absence(main_without_args())
    return run_result


def _run_execution_mode(mode: ExecutionMode) -> int:
    if mode.kind == "debug_stdio":
        assert mode.program_path is not None
        return run_debug_stdio(mode.program_path)

    if mode.kind == "pipe":
        assert mode.source is not None
        env = make_global_env(cli_args=mode.script_args)
        try:
            wrapped_source = _wrap_pipe_mode_expr(mode.source)
            run_source(wrapped_source, env, filename="<pipe>")
            return 0
        except GeniaQuietBrokenPipe:
            return 0
        except Exception as e:  # noqa: BLE001
            _emit_error(env, f"Error: {_format_pipe_mode_error(e)}")
            return 1

    if mode.kind == "command":
        assert mode.source is not None
        env = make_global_env(cli_args=mode.script_args)
        try:
            run_result = run_source(mode.source, env, filename="<command>")
            result = _resolve_program_result(run_result, env)
            if result is not None and not _is_nil_none(result):
                _emit_result(env, result)
            return 0
        except GeniaQuietBrokenPipe:
            return 0
        except Exception as e:  # noqa: BLE001
            _emit_error(env, f"Error: {e}")
            return 1

    if mode.kind == "file":
        assert mode.program_path is not None
        env = make_global_env(cli_args=mode.script_args)
        try:
            with open(mode.program_path, "r", encoding="utf-8") as f:
                run_result = run_source(f.read(), env, filename=str(Path(mode.program_path).resolve()))
            result = _resolve_program_result(run_result, env)
            if result is not None and not _is_nil_none(result):
                _emit_result(env, result)
            return 0
        except GeniaQuietBrokenPipe:
            return 0
        except Exception as e:  # noqa: BLE001
            _emit_error(env, f"Error: {e}")
            return 1

    if mode.kind == "repl":
        repl()
        return 0

    raise AssertionError(f"unknown execution mode: {mode.kind}")


def _main(argv: Optional[list[str]] = None) -> int:
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    terminator_index: int | None = None
    try:
        terminator_index = raw_argv.index("--")
    except ValueError:
        terminator_index = None

    parser = argparse.ArgumentParser(
        prog="genia",
        description="Genia CLI: file mode, command mode (-c), pipe mode (-p), or REPL.",
        epilog=(
            "Modes:\n"
            "  genia path/to/file.genia [args ...]\n"
            "  genia -c 'source' [args ...]\n"
            "  genia -p 'stage_expr' [args ...]\n"
            "  genia\n\n"
            "Pipe mode wraps as: stdin |> lines |> <stage_expr> |> run\n"
            "Use -- to stop option parsing and pass dash-prefixed literals as args/paths."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-V", "--version", action="store_true", help="Show Genia version and exit")
    command_group = parser.add_mutually_exclusive_group()
    command_group.add_argument("-c", "--command", help="Execute inline Genia source")
    command_group.add_argument("-p", "--pipe", help="Execute a pipe-mode stage expression")
    parser.add_argument("--debug-stdio", action="store_true", help="Run debug adapter over stdio for a program file")
    args, remaining_args = parser.parse_known_args(raw_argv)
    if getattr(args, "version", False):
        import importlib.metadata
        try:
            version = importlib.metadata.version("genia")
        except Exception:
            version = "unknown"
        print(f"genia {version}")
        return 0
    explicit_terminator_used = False
    if remaining_args and remaining_args[0] == "--":
        explicit_terminator_used = True
        remaining_args = remaining_args[1:]

    mode = _select_execution_mode(
        args,
        remaining_args,
        explicit_terminator_used=explicit_terminator_used,
        terminator_index=terminator_index,
        parser=parser,
    )
    return _run_execution_mode(mode)


if __name__ == "__main__":
    raise SystemExit(_main())
