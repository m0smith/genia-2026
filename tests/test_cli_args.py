import pytest

from genia.interpreter import _main


class CountingStdin:
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


def test_command_flag_executes_source_and_prints_result(capsys):
    exit_code = _main(["-c", "[1,2,3] |> count"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "3"


def test_command_mode_treats_non_option_trailing_tokens_as_cli_args(capsys):
    exit_code = _main(["-c", "main(args) = args", "examples/ants.genia"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == '["examples/ants.genia"]'


def test_command_flag_rejects_debug_stdio_combination():
    with pytest.raises(SystemExit):
        _main(["--debug-stdio", "-c", "1 + 1"])


def test_debug_stdio_rejects_pipe_mode_combination(capsys):
    with pytest.raises(SystemExit) as exc_info:
        _main(["--debug-stdio", "-p", "each(print)"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert "--debug-stdio cannot be used with --pipe" in captured.err


def test_debug_stdio_rejects_extra_trailing_args(tmp_path, capsys):
    program = tmp_path / "debug_target.genia"
    program.write_text("1 + 2", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        _main(["--debug-stdio", str(program), "extra"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert "--debug-stdio accepts exactly one program path" in captured.err


def test_debug_stdio_reports_missing_program_path_cleanly(capsys):
    with pytest.raises(SystemExit) as exc_info:
        _main(["--debug-stdio", "--", "--pretty"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert "--debug-stdio program path not found: --pretty" in captured.err


def test_file_mode_passes_remaining_cli_args_into_argv(tmp_path, capsys):
    program = tmp_path / "argv_echo.genia"
    program.write_text("argv()", encoding="utf-8")
    exit_code = _main([str(program), "--pretty", "in.txt"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == '["--pretty", "in.txt"]'


def test_command_mode_invokes_main_1_with_empty_cli_args(capsys):
    exit_code = _main(["-c", "main(args) = length(args)"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "0"


def test_command_mode_passes_bare_cli_args_into_main_1(capsys):
    exit_code = _main(["-c", "main(args) = args", "a"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == '["a"]'


def test_command_mode_passes_option_like_cli_args_into_main_1(capsys):
    exit_code = _main(["-c", "main(args) = args", "--pretty", "in.txt"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == '["--pretty", "in.txt"]'


def test_command_mode_treats_args_after_terminator_as_plain_args(capsys):
    exit_code = _main(["-c", "main(args) = args", "--", "--pretty", "in.txt"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == '["--pretty", "in.txt"]'


def test_command_mode_invokes_main_0_when_main_1_missing(capsys):
    exit_code = _main(["-c", "main() = 42"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "42"


def test_command_mode_prefers_main_1_over_main_0(capsys):
    source = """
main() = 10
main(args) = length(args)
"""
    exit_code = _main(["-c", source])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "0"


def test_command_mode_without_main_preserves_existing_behavior(capsys):
    exit_code = _main(["-c", "1 + 2"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "3"


def test_command_mode_without_main_ignores_trailing_cli_args(capsys):
    exit_code = _main(["-c", "1 + 2", "--pretty", "in.txt"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "3"


def test_file_mode_invokes_main_1_with_cli_args(tmp_path, capsys):
    program = tmp_path / "main_argv.genia"
    program.write_text("main(args) = length(args)", encoding="utf-8")
    exit_code = _main([str(program), "in.txt", "out.txt"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "2"


def test_file_mode_invokes_main_0_when_main_1_missing(tmp_path, capsys):
    program = tmp_path / "main_zero.genia"
    program.write_text("main() = 7", encoding="utf-8")
    exit_code = _main([str(program)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "7"


def test_pipe_mode_wraps_stage_expression_and_prints_first_line(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin(["a\n", "b\n", "c\n"]))

    exit_code = _main(["-p", "head(1) |> each(print)"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "a\n"
    assert captured.err == ""


def test_pipe_mode_each_print_happy_path(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin(["a\n", "b\n"]))

    exit_code = _main(["-p", "each(print)"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "a\nb\n"
    assert captured.err == ""


def test_pipe_long_flag_matches_short_flag(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin(["x\n", "y\n"]))

    exit_code = _main(["--pipe", "take(1) |> each(print)"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "x\n"
    assert captured.err == ""


def test_pipe_mode_with_no_stdin_is_normal_completion(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin([]))

    exit_code = _main(["-p", "head(1) |> each(print)"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""


def test_pipe_mode_with_one_input_line_is_clean(monkeypatch, capsys):
    stdin = CountingStdin(["solo\n"])
    monkeypatch.setattr("sys.stdin", stdin)

    exit_code = _main(["-p", "head(1) |> each(print)"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "solo\n"
    assert captured.err == ""
    assert stdin.reads == 1


def test_pipe_mode_preserves_early_termination(monkeypatch, capsys):
    stdin = CountingStdin(["a\n", "b\n", "c\n"])
    monkeypatch.setattr("sys.stdin", stdin)

    exit_code = _main(["-p", "head(1) |> each(print)"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "a\n"
    assert captured.err == ""
    assert stdin.reads == 1


def test_pipe_mode_rejects_explicit_run(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin(["a\n"]))

    exit_code = _main(["-p", "head(1) |> each(print) |> run"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() == "Error: Do not use run in pipe mode; pipe mode runs the flow automatically"


def test_pipe_mode_allows_lambda_param_named_run(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin(["a\n", "b\n"]))

    exit_code = _main(["-p", "map((run) -> run) |> each(print)"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "a\nb\n"
    assert captured.err == ""


def test_pipe_mode_rejects_explicit_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin(["a\n"]))

    exit_code = _main(["-p", "stdin |> lines |> head(1) |> each(print)"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() == "Error: Do not use stdin in pipe mode; stdin is provided automatically"


def test_pipe_mode_allows_lambda_param_named_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin(["a\n", "b\n"]))

    exit_code = _main(["-p", "map((stdin) -> stdin) |> each(print)"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "a\nb\n"
    assert captured.err == ""


def test_file_mode_rejects_option_like_program_path(capsys):
    with pytest.raises(SystemExit) as exc_info:
        _main(["--pretty", "in.txt"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert "expected a source file path" in captured.err
    assert "-c/--command" in captured.err


def test_file_mode_accepts_dash_prefixed_program_path_after_terminator(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    program = tmp_path / "-dash-script.genia"
    program.write_text("1 + 2", encoding="utf-8")

    exit_code = _main(["--", "-dash-script.genia"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == "3"
    assert captured.err == ""


def test_pipe_mode_rejects_full_programs_with_clear_error(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin(["a\n"]))

    exit_code = _main(["-p", "x = 1\nx"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() == "Error: Pipe mode expression must be a single stage expression, not a full program"


def test_pipe_mode_rejects_stage_expressions_that_do_not_produce_a_flow(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin(["a\n", "b\n"]))

    exit_code = _main(["-p", "collect"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() == "Error: Pipe mode stage expression must produce a flow for the automatic final run; received list"


def test_pipe_mode_invalid_non_callable_stage_is_reported_cleanly(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin(["a\n"]))

    exit_code = _main(["-p", "1 + 2"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert (
        captured.err.strip()
        == "Error: pipeline stage 2 failed in Flow mode at 1 + 2 [<pipe>:1]: stage received flow; pipeline stage expected a callable value, received int"
    )


def test_pipe_mode_some_mismatch_points_toward_explicit_helpers(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin(["42\n"]))

    exit_code = _main(["-p", 'map((x) -> some(x)) |> each(parse_int)'])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "parse_int expected a string, received some" in captured.err
    assert "Pipelines preserve explicit some(...)" in captured.err


def test_pipe_mode_flow_reuse_error_is_translated_cleanly(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin(["a\n", "b\n"]))

    exit_code = _main(
        [
            "-p",
            '((flow) -> { x = flow |> head(1); x |> collect; x })',
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.err.strip() == "Error: Flow values are single-use and cannot be reused after consumption"


def test_pipe_mode_realistic_unix_like_smoke(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin(["  a  \n", "\n", " b \n"]))

    exit_code = _main(["-p", 'map(trim) |> filter((x) -> x != "") |> each(print)'])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "a\nb\n"
    assert captured.err == ""


def test_pipe_mode_treats_args_after_terminator_as_plain_args(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin([]))

    exit_code = _main(["-p", "each(print)", "--", "--pretty", "in.txt"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
