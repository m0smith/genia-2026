from pathlib import Path

from genia.ast_nodes import FuncDef
from genia.interpreter import (
    Assign,
    DebugHooks,
    IrFuncDef,
    Parser,
    SourceSpan,
    lex,
    lower_program,
)
from genia import make_global_env, run_source


class RecordingDebugHooks(DebugHooks):
    def __init__(self) -> None:
        self.before_calls: list[str] = []
        self.after_calls: list[str] = []
        self.function_enter: list[tuple[str, SourceSpan | None]] = []
        self.function_exit: list[tuple[str, SourceSpan | None]] = []
        self.seen_filenames: set[str] = set()

    def before_node(self, node, env) -> None:  # noqa: ANN001, ARG002
        self.before_calls.append(type(node).__name__)
        span = getattr(node, "span", None)
        if span is not None:
            self.seen_filenames.add(span.filename)

    def after_node(self, node, env, result) -> None:  # noqa: ANN001, ARG002
        self.after_calls.append(type(node).__name__)

    def on_function_enter(self, fn_name, args, env, span) -> None:  # noqa: ANN001, ARG002
        self.function_enter.append((fn_name, span))

    def on_function_exit(self, fn_name, result, env, span) -> None:  # noqa: ANN001, ARG002
        self.function_exit.append((fn_name, span))


def test_ast_nodes_include_source_spans_for_assignment_expression():
    src = "x = 1 + 2\n"
    ast = Parser(lex(src), source=src, filename="sample.genia").parse_program()

    assign = ast[0]
    assert isinstance(assign, Assign)
    assert assign.span is not None
    assert assign.span.filename == "sample.genia"
    assert (assign.span.line, assign.span.column) == (1, 1)
    assert assign.span.end_column >= assign.span.column

    binary = assign.expr
    assert binary.span is not None
    assert binary.span.filename == "sample.genia"


def test_spans_survive_lowering_for_function_defs():
    src = "f(x) = x + 1\n"
    ast = Parser(lex(src), source=src, filename="fn.genia").parse_program()
    assert isinstance(ast[0], FuncDef)
    assert ast[0].span is not None

    ir = lower_program(ast)
    assert isinstance(ir[0], IrFuncDef)
    assert ir[0].span is not None
    assert ir[0].span.filename == "fn.genia"


def test_debug_hooks_are_called_without_changing_semantics():
    hooks = RecordingDebugHooks()
    env = make_global_env([], debug_hooks=hooks, debug_mode=True)

    result = run_source("inc(x) = x + 1\ninc(41)\n", env, filename="hook.genia", debug_hooks=hooks, debug_mode=True)
    assert result == 42
    assert hooks.before_calls
    assert hooks.after_calls
    assert hooks.function_enter and hooks.function_enter[0][0] == "inc"
    assert hooks.function_exit and hooks.function_exit[0][0] == "inc"


def test_run_source_filename_is_used_in_spans():
    hooks = RecordingDebugHooks()
    env = make_global_env([], debug_hooks=hooks, debug_mode=True)

    run_source("x = 1 + 2\n", env, filename="sample.genia", debug_hooks=hooks, debug_mode=True)

    assert "sample.genia" in hooks.seen_filenames


def test_autoload_uses_real_file_path_for_span_filename(tmp_path: Path):
    prelude_file = tmp_path / "std" / "prelude" / "autoload_span.genia"
    prelude_file.parent.mkdir(parents=True)
    prelude_file.write_text("auto_const() = 7\n", encoding="utf-8")

    hooks = RecordingDebugHooks()
    env = make_global_env([], debug_hooks=hooks, debug_mode=True)
    env.register_autoload("auto_const", 0, str(prelude_file.resolve()))

    result = run_source("auto_const()\n", env, filename="main.genia", debug_hooks=hooks, debug_mode=True)

    assert result == 7
    assert str(prelude_file.resolve()) in hooks.seen_filenames


def test_default_runtime_behavior_unchanged_without_debug_hooks():
    env = make_global_env([])
    assert run_source("x = 1 + 2\nx * 10\n", env) == 30
