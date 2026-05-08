#!/usr/bin/env python3
"""
CLI/REPL orchestration facade for the Genia Python reference host.

Entry points: run_source, _main, repl, run_debug_stdio.
Re-exports selected symbols from genia.builtins, genia.evaluator,
genia.callable, genia.values, genia.lexer, genia.parser, genia.lowering,
genia.optimizer, genia.ast_nodes, and genia.host_bridge for backward
compatibility with callers written before the module split (#210 series).
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
        assert_portable_core_ir,
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
        assert_portable_core_ir,
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
        GeniaFlow,
        GeniaOptionNone,
        GeniaOptionSome,
        truthy,
    )
    from genia.host_bridge import (
        BASE_DIR,
        _load_source_from_path,
        _build_python_host_module,
        _genia_to_python_host,
        _python_host_to_genia,
        _resolve_packaged_module,
    )
else:
    from .builtins import make_global_env as make_global_env
    from .evaluator import Evaluator as Evaluator, GeniaPromise as GeniaPromise, GeniaMetaEnv as GeniaMetaEnv
    from .lexer import SourceSpan as SourceSpan
    from .values import (
        OPTION_NONE as OPTION_NONE,
        GeniaFlow as GeniaFlow,
        GeniaOptionNone as GeniaOptionNone,
        GeniaOptionSome as GeniaOptionSome,
        truthy as truthy,
    )
    from .host_bridge import (
        BASE_DIR as BASE_DIR,
        _load_source_from_path as _load_source_from_path,
        _build_python_host_module as _build_python_host_module,
        _genia_to_python_host as _genia_to_python_host,
        _python_host_to_genia as _python_host_to_genia,
        _resolve_packaged_module as _resolve_packaged_module,
    )

# ---------------------------------------------------------------------------
# CLI/REPL orchestration
# ---------------------------------------------------------------------------

def _is_std_prelude_filename(filename: str) -> bool:
    normalized = filename.replace("\\", "/")
    return "/std/prelude/" in normalized or normalized.startswith("std/prelude/")


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
    previous_internal_access = env.internal_access
    env.internal_access = previous_internal_access or _is_std_prelude_filename(filename)
    try:
        result = Evaluator(env, debug_hooks=effective_hooks, debug_mode=effective_debug_mode).eval_program(ir_nodes)
    finally:
        env.internal_access = previous_internal_access
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
    return f"stdin |> lines |> {source} |> _pipe_run"


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
