import importlib.resources as resources
import io

from genia import make_global_env, run_source
from genia.interpreter import _load_source_from_path, _main


def test_packaged_stdlib_resource_is_discoverable_and_readable():
    resource = resources.files("genia").joinpath("std/prelude/list.genia")

    assert resource.is_file()
    text = resource.read_text(encoding="utf-8")
    assert "list(..xs)" in text
    assert "head(xs)" in text


def test_runtime_can_load_known_stdlib_file_through_resource_loader(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    env = make_global_env([])

    result = run_source("import math\n[math/pi, math/inc(2)]", env, filename="<command>")

    assert result[0] == 3.141592653589793
    assert result[1] == 3


def test_internal_loader_reads_packaged_stdlib_source():
    source, filename = _load_source_from_path("std/prelude/list.genia")

    assert "append(xs, ys)" in source
    assert "src/genia/std/prelude/list.genia" in filename or "genia/std/prelude/list.genia" in filename


def test_command_mode_flow_with_piped_stdin_head_regression(monkeypatch):
    stdout = io.StringIO()
    stderr = io.StringIO()
    stdin = io.StringIO("a\nb\nc\n")

    monkeypatch.setattr("sys.stdin", stdin)
    monkeypatch.setattr("sys.stdout", stdout)
    monkeypatch.setattr("sys.stderr", stderr)

    exit_code = _main(["-c", 'stdin |> lines |> head(1) |> each(print) |> run'])

    assert exit_code == 0
    assert stdout.getvalue() == "a\n"
    assert stderr.getvalue() == ""
