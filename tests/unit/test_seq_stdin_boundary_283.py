"""Contract tests for issue #283 stdin/Seq boundary.

Raw stdin is a host input capability. It must enter ordered Flow processing
through ``lines`` before Seq-compatible terminals consume it.
"""

import pytest

from genia import make_global_env, run_source
from genia.interpreter import _main
from genia.utf8 import format_debug


def test_stdin_lines_collect_is_the_command_mode_bridge():
    env = make_global_env(stdin_data=["a", "b"])

    assert run_source("stdin |> lines |> collect", env) == ["a", "b"]


def test_stdin_lines_each_run_is_the_effect_bridge(capsys):
    env = make_global_env(stdin_data=["a", "b"])

    result = run_source("stdin |> lines |> each(print) |> run", env)
    captured = capsys.readouterr()

    assert format_debug(result) == 'none("nil")'
    assert captured.out == "a\nb\n"
    assert captured.err == ""


@pytest.mark.parametrize(
    ("source", "helper"),
    [
        ("stdin |> collect", "collect"),
        ("stdin |> run", "run"),
        ("stdin |> each(print) |> run", "each"),
    ],
)
def test_raw_stdin_is_not_directly_seq_compatible(source, helper):
    env = make_global_env(stdin_data=["a", "b"])

    with pytest.raises(
        TypeError,
        match=(
            rf"{helper} expected a Seq-compatible value "
            r"\(list or Flow\); received stdin\. "
            r"Use stdin \|> lines to adapt stdin into a Flow\."
        ),
    ):
        run_source(source, env)


def test_pipe_mode_still_injects_stdin_lines(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", iter(["a\n", "b\n"]))

    exit_code = _main(["-p", "each(print)"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "a\nb\n"
    assert captured.err == ""


def test_pipe_mode_still_rejects_explicit_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", iter(["a\n"]))

    exit_code = _main(["-p", "stdin |> lines |> each(print)"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "stdin is provided automatically" in captured.err
