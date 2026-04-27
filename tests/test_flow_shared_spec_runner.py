from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import hosts.python.exec_flow as exec_flow_module
from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import ActualResult, execute_spec
from tools.spec_runner.loader import LoadedSpec, load_spec


REPO = Path(__file__).resolve().parents[1]
FLOW_DIR = REPO / "spec" / "flow"


def _write_flow_spec(tmp_path: Path, name: str, source: str) -> Path:
    path = tmp_path / f"{name}.yaml"
    path.write_text(
        "\n".join(
            [
                f"name: {name}",
                "category: flow",
                "input:",
                "  source: |",
                *(f"    {line}" for line in source.splitlines()),
                "expected:",
                '  stdout: ""',
                '  stderr: ""',
                "  exit_code: 0",
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_flow_loader_preserves_eval_like_fields() -> None:
    spec = load_spec(FLOW_DIR / "stdin-lines-collect-basic.yaml")

    assert spec.category == "flow"
    assert spec.source == "stdin |> lines |> collect\n"
    assert spec.stdin == "a\nb\n"
    assert spec.expected_stdout == '["a", "b"]\n'
    assert spec.expected_stderr == ""
    assert spec.expected_exit_code == 0


def test_flow_loader_rejects_unconsumed_flow_case(tmp_path: Path) -> None:
    spec_path = _write_flow_spec(tmp_path, "bad-flow-no-terminal", "stdin |> lines |> take(2)")

    with pytest.raises(ValueError, match="must explicitly consume the flow with collect or run"):
        load_spec(spec_path)


def test_execute_spec_normalizes_flow_line_endings_like_eval(monkeypatch) -> None:
    def fake_exec_flow(_spec: LoadedSpec) -> dict[str, object]:
        return {"stdout": "a\r\nb\n", "stderr": "err\r\n", "exit_code": 0}

    monkeypatch.setattr("hosts.python.adapter.exec_flow", fake_exec_flow)
    spec = load_spec(FLOW_DIR / "stdin-lines-collect-basic.yaml")

    actual = execute_spec(spec)

    assert actual == ActualResult(stdout="a\nb\n", stderr="err\n", exit_code=0)


def test_exec_flow_delegates_to_command_source_subprocess_without_wrapping(monkeypatch) -> None:
    calls: list[tuple[str, str | None]] = []

    def fake_run_eval_subprocess(source: str, stdin: str | None) -> dict[str, object]:
        calls.append((source, stdin))
        return {"stdout": "", "stderr": "", "exit_code": 0}

    monkeypatch.setattr(exec_flow_module, "run_eval_subprocess", fake_run_eval_subprocess)
    case = SimpleNamespace(source="stdin |> lines |> collect", stdin="a\nb\n")

    actual = exec_flow_module.exec_flow(case)

    assert actual == {"stdout": "", "stderr": "", "exit_code": 0}
    assert calls == [("stdin |> lines |> collect", "a\nb\n")]


def test_compare_spec_reports_flow_observable_mismatch() -> None:
    spec = load_spec(FLOW_DIR / "rules-identity-stage.yaml")
    actual = ActualResult(stdout="wrong", stderr="", exit_code=0)

    failures = compare_spec(spec, actual)

    assert [(failure.field, failure.expected, failure.actual) for failure in failures] == [
        ("stdout", '["a", "b"]\n', "wrong")
    ]
