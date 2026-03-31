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
