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
