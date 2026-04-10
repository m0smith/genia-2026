import io


from genia import make_global_env, run_source
from genia.interpreter import _main, repl
from genia.utf8 import format_debug


class RecordingStream:
    def __init__(self):
        self.parts: list[str] = []
        self.flush_count = 0

    def write(self, text: str) -> int:
        self.parts.append(text)
        return len(text)

    def flush(self) -> None:
        self.flush_count += 1

    def getvalue(self) -> str:
        return "".join(self.parts)


class BrokenStdout:
    def write(self, text: str) -> int:
        raise BrokenPipeError()

    def flush(self) -> None:
        raise BrokenPipeError()


class InfiniteCountingStdin:
    def __init__(self, line: str):
        self._line = line
        self.reads = 0

    def __iter__(self):
        return self

    def __next__(self):
        self.reads += 1
        return self._line


def test_print_writes_only_to_stdout():
    stdout = io.StringIO()
    stderr = io.StringIO()
    env = make_global_env(stdout_stream=stdout, stderr_stream=stderr)

    assert run_source('print("hi")', env) == "hi"
    assert stdout.getvalue() == "hi\n"
    assert stderr.getvalue() == ""


def test_log_writes_only_to_stderr():
    stdout = io.StringIO()
    stderr = io.StringIO()
    env = make_global_env(stdout_stream=stdout, stderr_stream=stderr)

    assert run_source('log("oops")', env) == "oops"
    assert stdout.getvalue() == ""
    assert stderr.getvalue() == "oops\n"


def test_write_and_writeln_to_stdout():
    stdout = io.StringIO()
    stderr = io.StringIO()
    env = make_global_env(stdout_stream=stdout, stderr_stream=stderr)

    run_source('write(stdout, "a")\nwriteln(stdout, "b")', env)
    assert stdout.getvalue() == "ab\n"
    assert stderr.getvalue() == ""


def test_io_public_wrappers_work_as_function_values():
    stdout = io.StringIO()
    stderr = io.StringIO()
    env = make_global_env(stdout_stream=stdout, stderr_stream=stderr)

    assert run_source('apply(write, [stdout, "a"])\napply(writeln, [stdout, "b"])', env) == "b"
    assert stdout.getvalue() == "ab\n"
    assert stderr.getvalue() == ""


def test_terminal_helpers_write_expected_escape_sequences():
    stdout = RecordingStream()
    stderr = RecordingStream()
    env = make_global_env(stdout_stream=stdout, stderr_stream=stderr)

    assert format_debug(run_source("clear_screen()\nmove_cursor(4, 2)", env)) == 'none("nil")'
    assert stdout.getvalue() == "\x1b[2J\x1b[H\x1b[2;4H"
    assert stdout.flush_count == 1
    assert stderr.getvalue() == ""


def test_render_grid_writes_rows_to_stdout():
    stdout = io.StringIO()
    stderr = io.StringIO()
    env = make_global_env(stdout_stream=stdout, stderr_stream=stderr)

    result = run_source('render_grid(["abc", ["d", "e", "f"], [1, 2, 3]])', env)

    assert result == ["abc", ["d", "e", "f"], [1, 2, 3]]
    assert stdout.getvalue() == "abc\ndef\n123"
    assert stderr.getvalue() == ""


def test_flush_succeeds_for_stdout_and_stderr():
    stdout = RecordingStream()
    stderr = RecordingStream()
    env = make_global_env(stdout_stream=stdout, stderr_stream=stderr)

    assert format_debug(run_source("flush(stdout)\nflush(stderr)", env)) == 'none("nil")'
    assert stdout.flush_count == 1
    assert stderr.flush_count == 1


def test_output_sinks_exist_as_runtime_values():
    env = make_global_env(stdout_stream=io.StringIO(), stderr_stream=io.StringIO())

    assert repr(run_source("stdout", env)) == "<stdout>"
    assert repr(run_source("stderr", env)) == "<stderr>"


def test_uncaught_runtime_error_renders_to_stderr_in_command_mode(capsys):
    exit_code = _main(["-c", "unknown_name"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Error: Undefined name: unknown_name" in captured.err


def test_file_mode_diagnostics_go_to_stderr(tmp_path, capsys):
    program = tmp_path / "bad.genia"
    program.write_text("unknown_name\n", encoding="utf-8")

    exit_code = _main([str(program)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Error: Undefined name: unknown_name" in captured.err


def test_repl_result_output_goes_to_stdout(monkeypatch):
    prompts: list[str] = []
    inputs = iter(["1 + 2", ":quit"])
    stdout = io.StringIO()
    stderr = io.StringIO()

    def fake_input(prompt: str = "") -> str:
        prompts.append(prompt)
        return next(inputs)

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr("sys.stdout", stdout)
    monkeypatch.setattr("sys.stderr", stderr)

    repl()

    assert prompts == [">>> ", ">>> "]
    assert "Genia prototype REPL" in stdout.getvalue()
    assert "3\n" in stdout.getvalue()
    assert stderr.getvalue() == ""


def test_repl_errors_go_to_stderr(monkeypatch):
    inputs = iter(["unknown_name", ":quit"])
    stdout = io.StringIO()
    stderr = io.StringIO()

    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.setattr("sys.stdout", stdout)
    monkeypatch.setattr("sys.stderr", stderr)

    repl()

    assert "Error: Undefined name: unknown_name" in stderr.getvalue()
    assert "Genia prototype REPL" in stdout.getvalue()


def test_broken_pipe_on_stdout_path_is_quiet(monkeypatch):
    stderr = io.StringIO()

    monkeypatch.setattr("sys.stdout", BrokenStdout())
    monkeypatch.setattr("sys.stderr", stderr)

    exit_code = _main(["-c", 'print("hi")\nnil'])

    assert exit_code == 0
    assert stderr.getvalue() == ""


def test_broken_pipe_on_flow_output_is_quiet_and_stops_after_first_pull(monkeypatch):
    stderr = io.StringIO()
    stdin = InfiniteCountingStdin("hello\n")

    monkeypatch.setattr("sys.stdin", stdin)
    monkeypatch.setattr("sys.stdout", BrokenStdout())
    monkeypatch.setattr("sys.stderr", stderr)

    exit_code = _main(["-p", "each(print)"])

    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert stdin.reads == 1


def test_flow_output_to_stdout_respects_take():
    stdout = io.StringIO()
    stderr = io.StringIO()
    env = make_global_env(stdin_data=["a", "b", "c"], stdout_stream=stdout, stderr_stream=stderr)

    result = run_source("stdin |> lines |> take(2) |> each(print) |> run", env)

    assert format_debug(result) == 'none("nil")'
    assert stdout.getvalue() == "a\nb\n"
    assert stderr.getvalue() == ""


def test_injected_test_streams_work_for_stdout_and_stderr():
    stdout = RecordingStream()
    stderr = RecordingStream()
    env = make_global_env(stdout_stream=stdout, stderr_stream=stderr)

    run_source('print("ok")\nlog("warn")', env)

    assert stdout.getvalue() == "ok\n"
    assert stderr.getvalue() == "warn\n"


def test_input_remains_independent_of_stdin(monkeypatch):
    stdout = io.StringIO()
    stderr = io.StringIO()
    env = make_global_env(stdin_data=["streamed"], stdout_stream=stdout, stderr_stream=stderr)

    monkeypatch.setattr("builtins.input", lambda prompt="": "typed")

    assert run_source('input("Prompt: ")', env) == "typed"
    assert run_source("stdin()", env) == ["streamed"]
