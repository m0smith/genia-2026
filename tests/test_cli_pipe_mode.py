"""Comprehensive CLI pipe mode tests.

Tests exercise the CLI entrypoint (_main) to pin down all pipe mode
behavior: validation, error messages, broken pipe handling, and
stderr robustness.
"""

import io
import sys

import pytest

from genia import make_global_env
from genia.interpreter import _main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class CountingStdin:
    """Simulated stdin that records how many lines were read."""

    def __init__(self, lines: list[str]):
        self._lines = list(lines)
        self.reads = 0
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._index >= len(self._lines):
            raise StopIteration
        self.reads += 1
        value = self._lines[self._index]
        self._index += 1
        return value


class InfiniteCountingStdin:
    """Stdin that yields the same line forever (for broken-pipe tests)."""

    def __init__(self, line: str):
        self._line = line
        self.reads = 0

    def __iter__(self):
        return self

    def __next__(self):
        self.reads += 1
        return self._line


class BrokenStream:
    """A stream that raises BrokenPipeError on any write or flush."""

    def write(self, text: str) -> int:
        raise BrokenPipeError()

    def flush(self) -> None:
        raise BrokenPipeError()


# ===========================================================================
# 1) Explicit stdin rejection
# ===========================================================================

class TestExplicitStdinRejection:
    def test_bare_stdin_in_pipe_mode(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n"]))

        exit_code = _main(["-p", "stdin |> lines"])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert captured.out == ""
        assert "stdin is provided automatically" in captured.err

    def test_stdin_piped_further(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n"]))

        exit_code = _main(["-p", "stdin |> lines |> each(print)"])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "stdin is provided automatically" in captured.err

    def test_lambda_param_named_stdin_is_allowed(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n", "b\n"]))

        exit_code = _main(["-p", "map((stdin) -> stdin) |> each(print)"])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert captured.out == "a\nb\n"
        assert captured.err == ""


# ===========================================================================
# 2) Explicit run rejection
# ===========================================================================

class TestExplicitRunRejection:
    def test_trailing_run(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n"]))

        exit_code = _main(["-p", "each(print) |> run"])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert captured.out == ""
        assert "run is implicit in pipe mode" in captured.err

    def test_standalone_run(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n"]))

        exit_code = _main(["-p", "run"])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "run is implicit in pipe mode" in captured.err

    def test_lambda_param_named_run_is_allowed(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n", "b\n"]))

        exit_code = _main(["-p", "map((run) -> run) |> each(print)"])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert captured.out == "a\nb\n"


# ===========================================================================
# 3) Non-flow final result
# ===========================================================================

class TestNonFlowFinalResult:
    def test_collect_produces_list_not_flow(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n", "b\n"]))

        exit_code = _main(["-p", "collect"])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert captured.out == ""
        assert "Pipe mode stage must produce a flow" in captured.err
        assert "received list" in captured.err
        assert "-c/--command" in captured.err

    def test_count_produces_int_not_flow(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n", "b\n"]))

        exit_code = _main(["-p", "collect |> count"])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "Pipe mode stage must produce a flow" in captured.err
        assert "received int" in captured.err


# ===========================================================================
# 4) Whole-flow vs per-item misuse
# ===========================================================================

class TestPerItemMisuse:
    def test_parse_int_receives_flow(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["42\n"]))

        exit_code = _main(["-p", "parse_int"])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert captured.out == ""
        # Must mention received type
        assert "received flow" in captured.err
        # Must suggest correct pipeline usage
        assert "map(parse_int)" in captured.err
        assert "keep_some(parse_int)" in captured.err

    def test_trim_receives_flow(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["  hello  \n"]))

        exit_code = _main(["-p", "trim"])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "received flow" in captured.err
        assert "map(trim)" in captured.err
        assert "keep_some(trim)" in captured.err

    def test_error_includes_stage_name(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["42\n"]))

        exit_code = _main(["-p", "parse_int"])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "parse_int" in captured.err
        assert "Pipe mode passes a Flow" in captured.err


# ===========================================================================
# 5) Reducer misuse
# ===========================================================================

class TestReducerMisuse:
    def test_sum_receives_flow(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["10\n", "20\n"]))

        exit_code = _main(["-p", "sum"])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert captured.out == ""
        # Must mention type mismatch
        assert "sum expected a list" in captured.err
        assert "received flow" in captured.err
        # Must suggest alternatives
        assert "collect |> sum" in captured.err
        assert "-c/--command" in captured.err

    def test_count_receives_flow(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n", "b\n"]))

        exit_code = _main(["-p", "count"])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "received flow" in captured.err
        assert "-c/--command" in captured.err


# ===========================================================================
# 6) Broken pipe on stdout
# ===========================================================================

class TestBrokenPipeStdout:
    def test_broken_stdout_exits_cleanly(self, monkeypatch):
        stderr = io.StringIO()
        monkeypatch.setattr("sys.stdin", InfiniteCountingStdin("hello\n"))
        monkeypatch.setattr("sys.stdout", BrokenStream())
        monkeypatch.setattr("sys.stderr", stderr)

        exit_code = _main(["-p", "each(print)"])

        assert exit_code == 0
        assert stderr.getvalue() == ""

    def test_broken_stdout_with_head_exits_cleanly(self, monkeypatch):
        stderr = io.StringIO()
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n", "b\n", "c\n"]))
        monkeypatch.setattr("sys.stdout", BrokenStream())
        monkeypatch.setattr("sys.stderr", stderr)

        exit_code = _main(["-p", "head(1) |> each(print)"])

        assert exit_code == 0
        assert stderr.getvalue() == ""

    def test_no_python_traceback_on_broken_pipe(self, monkeypatch):
        stderr = io.StringIO()
        monkeypatch.setattr("sys.stdin", InfiniteCountingStdin("hello\n"))
        monkeypatch.setattr("sys.stdout", BrokenStream())
        monkeypatch.setattr("sys.stderr", stderr)

        exit_code = _main(["-p", "each(print)"])

        assert exit_code == 0
        # No Python traceback or internal error
        assert "Traceback" not in stderr.getvalue()
        assert "BrokenPipeError" not in stderr.getvalue()


# ===========================================================================
# 7) Broken pipe with flow pipeline
# ===========================================================================

class TestBrokenPipeFlowPipeline:
    def test_map_then_print_with_broken_pipe(self, monkeypatch):
        stderr = io.StringIO()
        monkeypatch.setattr("sys.stdin", InfiniteCountingStdin("hello\n"))
        monkeypatch.setattr("sys.stdout", BrokenStream())
        monkeypatch.setattr("sys.stderr", stderr)

        exit_code = _main(["-p", "map(trim) |> each(print)"])

        assert exit_code == 0
        assert stderr.getvalue() == ""

    def test_stdin_stops_pulling_after_broken_pipe(self, monkeypatch):
        stderr = io.StringIO()
        stdin = InfiniteCountingStdin("hello\n")
        monkeypatch.setattr("sys.stdin", stdin)
        monkeypatch.setattr("sys.stdout", BrokenStream())
        monkeypatch.setattr("sys.stderr", stderr)

        exit_code = _main(["-p", "each(print)"])

        assert exit_code == 0
        # Should stop after first write attempt
        assert stdin.reads == 1

    def test_no_extra_output_after_broken_pipe(self, monkeypatch):
        stderr = io.StringIO()
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n", "b\n", "c\n"]))
        monkeypatch.setattr("sys.stdout", BrokenStream())
        monkeypatch.setattr("sys.stderr", stderr)

        exit_code = _main(["-p", "each(print)"])

        assert exit_code == 0
        # No error or extra output
        assert stderr.getvalue() == ""


# ===========================================================================
# 8) stderr robustness
# ===========================================================================

class TestStderrRobustness:
    def test_broken_stderr_does_not_crash_on_error_report(self, monkeypatch):
        """If stderr is broken while reporting a pipe mode error, process
        should still exit cleanly without a Python traceback."""
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n"]))
        monkeypatch.setattr("sys.stdout", io.StringIO())
        monkeypatch.setattr("sys.stderr", BrokenStream())

        # Use an expression that triggers a pipe mode error
        exit_code = _main(["-p", "collect"])

        # Should not crash; exit 1 for the error
        assert exit_code == 1

    def test_broken_stderr_with_log_in_flow_no_crash(self, monkeypatch):
        """log() writes to stderr via a sink with swallow_broken_pipe=True.
        If stderr is broken, the flow should still terminate cleanly."""
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n", "b\n"]))
        monkeypatch.setattr("sys.stdout", io.StringIO())
        monkeypatch.setattr("sys.stderr", BrokenStream())

        exit_code = _main(["-p", "map((x) -> { log(x); x }) |> each(print)"])

        assert exit_code == 0


# ===========================================================================
# Happy paths (regression guards)
# ===========================================================================

class TestPipeModeHappyPath:
    def test_pipe_mode_bypasses_main_dispatch(self, monkeypatch, capsys):
        original_make_global_env = make_global_env

        def make_env_with_failing_main(*args, **kwargs):
            env = original_make_global_env(*args, **kwargs)

            def should_not_run():
                raise AssertionError("pipe mode should not dispatch main")

            env.set("main", should_not_run)
            return env

        monkeypatch.setattr("genia.interpreter.make_global_env", make_env_with_failing_main)
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n", "b\n"]))

        exit_code = _main(["-p", "each(print)"])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert captured.out == "a\nb\n"
        assert captured.err == ""

    def test_simple_each_print(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n", "b\n"]))

        exit_code = _main(["-p", "each(print)"])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert captured.out == "a\nb\n"
        assert captured.err == ""

    def test_map_trim_filter_each_print(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["  a  \n", "\n", "  b  \n"]))

        exit_code = _main(["-p", 'map(trim) |> filter((x) -> x != "") |> each(print)'])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert captured.out == "a\nb\n"
        assert captured.err == ""

    def test_head_limits_output(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n", "b\n", "c\n"]))

        exit_code = _main(["-p", "head(1) |> each(print)"])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert captured.out == "a\n"
        assert captured.err == ""

    def test_empty_stdin_completes_cleanly(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin([]))

        exit_code = _main(["-p", "each(print)"])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert captured.out == ""
        assert captured.err == ""

    def test_long_flag_works(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["x\n"]))

        exit_code = _main(["--pipe", "each(print)"])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert captured.out == "x\n"

    def test_pipe_mode_with_cli_args(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin([]))

        exit_code = _main(["-p", "each(print)", "--", "--flag", "value"])
        captured = capsys.readouterr()

        assert exit_code == 0


# ===========================================================================
# Full program rejection
# ===========================================================================

class TestFullProgramRejection:
    def test_assignment_then_expr_is_rejected(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n"]))

        exit_code = _main(["-p", "x = 1\nx"])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "single stage expression" in captured.err

    def test_multiple_expressions_are_rejected(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n"]))

        exit_code = _main(["-p", "each(print)\neach(print)"])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "single stage expression" in captured.err


# ===========================================================================
# Error message quality
# ===========================================================================

class TestErrorMessageQuality:
    def test_errors_are_genia_facing_no_python_internals(self, monkeypatch, capsys):
        """Pipe mode errors must not expose Python internals."""
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n"]))

        _main(["-p", "parse_int"])
        captured = capsys.readouterr()

        assert "TypeError" not in captured.err
        assert "Traceback" not in captured.err
        assert "File \"" not in captured.err

    def test_non_callable_stage_has_clear_message(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n"]))

        exit_code = _main(["-p", "1 + 2"])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "expected a callable value" in captured.err
        assert "received int" in captured.err
        assert "Pipe mode stages receive a Flow" in captured.err

    def test_flow_reuse_has_clear_message(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", CountingStdin(["a\n"]))

        exit_code = _main(["-p", '((flow) -> { x = flow |> head(1); x |> collect; x })'])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "single-use" in captured.err
        assert "cannot be reused" in captured.err
