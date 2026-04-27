from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import tools.spec_runner.runner as runner_module

from hosts.python import exec_cli as exec_cli_module
from hosts.python.exec_cli import exec_cli
from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import ActualResult, execute_spec
from tools.spec_runner.loader import LoadedSpec, discover_specs, load_spec
from tools.spec_runner.runner import main as run_spec_suite


REPO = Path(__file__).resolve().parents[1]
CLI_DIR = REPO / "spec" / "cli"


def _loaded_cli_spec(
    *,
    name: str = "case",
    file: str | None = None,
    command: str | None = None,
    stdin: str = "",
    argv: list[str] | None = None,
    debug_stdio: bool = False,
    expected_stdout: str = "",
    expected_stderr: str = "",
    expected_exit_code: int = 0,
) -> LoadedSpec:
    source = file if file is not None else command
    assert source is not None
    return LoadedSpec(
        name=name,
        category="cli",
        source=source,
        stdin=stdin,
        expected_stdout=expected_stdout,
        expected_stderr=expected_stderr,
        expected_exit_code=expected_exit_code,
        expected_ir=None,
        path=CLI_DIR / f"{name}.yaml",
        description="test",
        file=file,
        command=command,
        argv=[] if argv is None else argv,
        debug_stdio=debug_stdio,
        spec_id=name,
    )


def _write_cli_spec(tmp_path: Path, name: str, input_lines: list[str]) -> Path:
    path = tmp_path / f"{name}.yaml"
    path.write_text(
        "\n".join(
            [
                f"name: {name}",
                f"id: {name}",
                "category: cli",
                "description: temporary cli spec",
                "input:",
                *input_lines,
                "expected:",
                '  stdout: ""',
                '  stderr: ""',
                "  exit_code: 0",
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_discover_specs_includes_cli_cases_without_invalid_specs() -> None:
    specs, invalid_specs = discover_specs()

    assert invalid_specs == []
    cli_names = {spec.name for spec in specs if spec.category == "cli"}
    assert {
        "file_mode_basic",
        "file_mode_argv",
        "file_mode_main_argv",
        "command_mode_basic",
        "command_mode_argv",
        "command_mode_collect_sum",
        "pipe_mode_basic",
        "pipe_mode_map_parse_int",
        "pipe_mode_bare_parse_int_error",
        "pipe_mode_sum_error",
        "pipe_mode_collect_error",
        "pipe_mode_explicit_run_error",
    }.issubset(cli_names)


def test_cli_loader_preserves_flattened_cli_fields() -> None:
    spec = load_spec(CLI_DIR / "command_mode_argv.yaml")

    assert spec.category == "cli"
    assert spec.source == "print argv()"
    assert spec.file is None
    assert spec.command == "print argv()"
    assert spec.stdin == ""
    assert spec.argv == ["a", "b"]
    assert spec.debug_stdio is False
    assert spec.expected_stdout == '["a", "b"]'
    assert spec.expected_stderr == ""
    assert spec.expected_exit_code == 0


def test_cli_loader_rejects_multiple_modes(tmp_path: Path) -> None:
    spec_path = _write_cli_spec(
        tmp_path,
        "bad_cli_modes",
        [
            '  source: "bad.genia"',
            '  file: "bad.genia"',
            '  command: "print 1"',
            '  stdin: ""',
            "  argv: []",
            "  debug_stdio: false",
        ],
    )

    with pytest.raises(ValueError, match="file mode requires input.file only"):
        load_spec(spec_path)


def test_cli_loader_rejects_missing_command_and_file(tmp_path: Path) -> None:
    spec_path = _write_cli_spec(
        tmp_path,
        "missing_cli_mode",
        [
            '  source: ""',
            "  file: null",
            "  command: null",
            '  stdin: ""',
            "  argv: []",
            "  debug_stdio: false",
        ],
    )

    with pytest.raises(ValueError, match="provide input.file or input.command"):
        load_spec(spec_path)


def test_exec_cli_file_mode_executes_file_and_passes_argv() -> None:
    spec = load_spec(CLI_DIR / "file_mode_argv.yaml")

    actual = exec_cli(spec)

    assert actual == {
        "stdout": '["foo", "bar"]\n',
        "stderr": "",
        "exit_code": 0,
    }


def test_exec_cli_file_mode_does_not_insert_terminator_for_plain_argv(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(argv: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append({"argv": argv, **kwargs})
        return SimpleNamespace(stdout="ok\n", stderr="", returncode=0)

    monkeypatch.setattr(exec_cli_module.subprocess, "run", fake_run)
    spec = _loaded_cli_spec(file="script.genia", argv=["foo", "bar"])

    exec_cli(spec)

    assert calls[0]["argv"][2:] == ["script.genia", "foo", "bar"]


def test_exec_cli_file_mode_passes_option_like_argv_without_inserting_terminator(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(argv: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append({"argv": argv, **kwargs})
        return SimpleNamespace(stdout="ok\n", stderr="", returncode=0)

    monkeypatch.setattr(exec_cli_module.subprocess, "run", fake_run)
    spec = _loaded_cli_spec(file="script.genia", argv=["--pretty"])

    exec_cli(spec)

    assert calls[0]["argv"][2:] == ["script.genia", "--pretty"]


def test_exec_cli_command_mode_executes_command_and_passes_argv() -> None:
    spec = load_spec(CLI_DIR / "command_mode_argv.yaml")

    actual = exec_cli(spec)

    assert actual == {
        "stdout": '["a", "b"]\n',
        "stderr": "",
        "exit_code": 0,
    }


def test_exec_cli_command_mode_passes_trailing_args_without_inserted_terminator(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(argv: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append({"argv": argv, **kwargs})
        return SimpleNamespace(stdout="ok\n", stderr="", returncode=0)

    monkeypatch.setattr(exec_cli_module.subprocess, "run", fake_run)
    spec = _loaded_cli_spec(command="print 1", stdin="", argv=["--pretty"])

    actual = exec_cli(spec)

    assert actual["stdout"] == "ok\n"
    assert calls[0]["argv"][2:] == ["-c", "print 1", "--pretty"]
    assert calls[0]["input"] is None


def test_exec_cli_pipe_mode_executes_command_with_piped_stdin() -> None:
    spec = load_spec(CLI_DIR / "pipe_mode_basic.yaml")

    actual = exec_cli(spec)

    assert actual == {
        "stdout": "alpha\nbeta\n",
        "stderr": "",
        "exit_code": 0,
    }


def test_exec_cli_pipe_mode_rejects_explicit_run_stdin() -> None:
    spec = _loaded_cli_spec(command="run(stdin)", stdin="x\n", expected_exit_code=1)

    actual = exec_cli(spec)

    assert actual["stdout"] == ""
    assert "stdin is provided automatically" in actual["stderr"]
    assert actual["exit_code"] == 1


def test_exec_cli_pipe_mode_requires_command() -> None:
    spec = SimpleNamespace(
        file=None,
        command=None,
        stdin="x\n",
        argv=[],
        debug_stdio=False,
    )

    with pytest.raises(ValueError, match="pipe mode requires command"):
        exec_cli(spec)


def test_exec_cli_uses_subprocess_without_shell_piping(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(argv: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append({"argv": argv, **kwargs})
        return SimpleNamespace(stdout="", stderr="", returncode=0)

    monkeypatch.setattr(exec_cli_module.subprocess, "run", fake_run)
    spec = _loaded_cli_spec(command="each(print)", stdin="x\n")

    exec_cli(spec)

    assert calls[0]["argv"][2:] == ["-p", "each(print)"]
    assert calls[0]["input"] == "x\n"
    assert calls[0].get("shell") is None
    assert not any("|" in part for part in calls[0]["argv"])
    assert "echo" not in calls[0]["argv"]


def test_execute_spec_normalizes_cli_line_endings_and_trailing_newlines(monkeypatch) -> None:
    def fake_exec_cli(_spec: LoadedSpec) -> dict[str, object]:
        return {"stdout": "a\r\nb\n\n", "stderr": "err\r\n\n", "exit_code": 0}

    monkeypatch.setattr("hosts.python.adapter.exec_cli", fake_exec_cli)
    spec = _loaded_cli_spec(command="print 1")

    actual = execute_spec(spec)

    assert actual == ActualResult(stdout="a\nb", stderr="err", exit_code=0)


def test_execute_spec_preserves_internal_cli_whitespace(monkeypatch) -> None:
    def fake_exec_cli(_spec: LoadedSpec) -> dict[str, object]:
        return {"stdout": "a  b\tc\n", "stderr": "x  y\n", "exit_code": 0}

    monkeypatch.setattr("hosts.python.adapter.exec_cli", fake_exec_cli)
    spec = _loaded_cli_spec(command="print 1")

    actual = execute_spec(spec)

    assert actual.stdout == "a  b\tc"
    assert actual.stderr == "x  y"


def test_cli_spec_fixture_executes_and_compares_expected_observables() -> None:
    spec = load_spec(CLI_DIR / "pipe_mode_argv_empty.yaml")

    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert actual.stdout == "[]"
    assert actual.stderr == ""
    assert actual.exit_code == 0
    assert failures == []


@pytest.mark.parametrize(
    "fname",
    [
        "file_mode_main_argv.yaml",
        "command_mode_collect_sum.yaml",
        "pipe_mode_map_parse_int.yaml",
        "pipe_mode_bare_parse_int_error.yaml",
        "pipe_mode_sum_error.yaml",
        "pipe_mode_collect_error.yaml",
    ],
)
def test_new_cli_spec_fixtures_execute_and_compare(fname: str) -> None:
    spec = load_spec(CLI_DIR / fname)

    actual = execute_spec(spec)
    failures = compare_spec(spec, actual)

    assert actual.ir is None
    assert failures == []


def test_compare_spec_reports_cli_observable_mismatch() -> None:
    spec = load_spec(CLI_DIR / "command_mode_basic.yaml")
    actual = ActualResult(stdout="wrong", stderr="", exit_code=0)

    failures = compare_spec(spec, actual)

    assert [(failure.field, failure.expected, failure.actual) for failure in failures] == [
        ("stdout", "123", "wrong")
    ]


def test_spec_runner_integration_includes_cli_without_invalid_specs(capsys) -> None:
    exit_code = run_spec_suite()
    captured = capsys.readouterr()

    specs, invalid_specs = discover_specs()
    cli_count = sum(1 for spec in specs if spec.category == "cli")
    assert cli_count > 0
    assert invalid_specs == []
    assert exit_code == 0
    assert "invalid=0" in captured.out
    assert f"total={len(specs)}" in captured.out


def test_spec_runner_verbose_reports_spec_start_and_elapsed(capsys, monkeypatch) -> None:
    spec = _loaded_cli_spec(name="verbose_case", command="print 1")

    monkeypatch.setattr(runner_module, "discover_specs", lambda: ([spec], []))
    monkeypatch.setattr(
        runner_module,
        "execute_spec",
        lambda _spec: ActualResult(stdout="", stderr="", exit_code=0),
    )

    exit_code = runner_module.main(["--verbose"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "verbose_case\n" in captured.out
    assert "verbose_case\t" in captured.out
    assert "Summary: total=1 passed=1 failed=0 invalid=0" in captured.out


def test_eval_and_ir_specs_still_execute_unchanged() -> None:
    eval_spec = load_spec(REPO / "spec" / "eval" / "arithmetic-basic.yaml")
    ir_spec = load_spec(REPO / "spec" / "ir" / "pipeline-explicit.yaml")

    eval_actual = execute_spec(eval_spec)
    ir_actual = execute_spec(ir_spec)

    assert compare_spec(eval_spec, eval_actual) == []
    assert compare_spec(ir_spec, ir_actual) == []
