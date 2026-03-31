import pytest

from genia.interpreter import _main


def test_command_flag_executes_source_and_prints_result(capsys):
    exit_code = _main(["-c", "[1,2,3] |> count"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "3"


def test_command_flag_rejects_program_path_combination():
    with pytest.raises(SystemExit):
        _main(["examples/ants.genia", "-c", "1 + 1"])


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
