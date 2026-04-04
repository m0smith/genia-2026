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
    assert "omit run" in captured.err


def test_pipe_mode_rejects_explicit_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin(["a\n"]))

    exit_code = _main(["-p", "stdin |> lines |> head(1) |> each(print)"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "omit stdin" in captured.err


def test_pipe_mode_realistic_unix_like_smoke(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin(["  a  \n", "\n", " b \n"]))

    exit_code = _main(["-p", 'map(trim) |> filter((x) -> x != "") |> each(print)'])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "a\nb\n"
    assert captured.err == ""
