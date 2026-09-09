"""
E16-7 (issue #764) end-to-end proof that `tools.spec_runner.runner` writes
a deterministic evidence document when `--evidence` is given, using the
deterministic E16-1 fixture adapter.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.spec_runner import runner
from tools.spec_runner.loader import LoadedSpec

FIXTURE_ADAPTER_COMMAND = f"{sys.executable} -m tools.spec_runner.fixtures.protocol_fixture_adapter"


def _one_pass_spec() -> tuple[list[LoadedSpec], list]:
    return (
        [
            LoadedSpec(
                name="ok",
                category="eval",
                source="hello",
                stdin="",
                expected_stdout="fixture-stdout:hello\n",
                expected_stderr="",
                expected_exit_code=0,
                expected_ir=None,
                path=Path("spec/eval/ok.yaml"),
            )
        ],
        [],
    )


def test_evidence_is_written_and_matches_the_run(monkeypatch, capsys, tmp_path) -> None:
    monkeypatch.setattr(runner, "discover_specs", _one_pass_spec)
    evidence_path = tmp_path / "evidence.json"

    exit_code = runner.main(["--host", FIXTURE_ADAPTER_COMMAND, "--evidence", str(evidence_path)])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert f"Evidence written: {evidence_path}" in out

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["protocol_version"] == "1"
    assert evidence["total_cases"] == 1
    assert evidence["applicable_cases"] == 1
    assert evidence["counts"] == {
        "pass": 1,
        "fail": 0,
        "unsupported": 0,
        "protocol_error": 0,
        "crash": 0,
        "timeout": 0,
        "invalid": 0,
    }
    assert evidence["contract_revision"]["declared"]
    assert evidence["contract_revision"]["classification"] in ("current", "resolvable_ancestor")
    assert "parser" in evidence["capabilities"]


def test_evidence_is_not_written_without_the_flag(monkeypatch, capsys, tmp_path) -> None:
    monkeypatch.setattr(runner, "discover_specs", _one_pass_spec)
    exit_code = runner.main(["--host", FIXTURE_ADAPTER_COMMAND])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Evidence written" not in out


def test_repeated_runs_over_the_same_deterministic_inputs_produce_identical_evidence(
    monkeypatch, capsys, tmp_path
) -> None:
    monkeypatch.setattr(runner, "discover_specs", _one_pass_spec)
    path_a = tmp_path / "a.json"
    path_b = tmp_path / "b.json"

    runner.main(["--host", FIXTURE_ADAPTER_COMMAND, "--evidence", str(path_a)])
    capsys.readouterr()
    runner.main(["--host", FIXTURE_ADAPTER_COMMAND, "--evidence", str(path_b)])
    capsys.readouterr()

    assert path_a.read_text(encoding="utf-8") == path_b.read_text(encoding="utf-8")


def test_evidence_never_written_when_revision_is_unresolvable(monkeypatch, capsys, tmp_path) -> None:
    monkeypatch.setattr(runner, "discover_specs", _one_pass_spec)
    monkeypatch.setenv("FIXTURE_CONTRACT_REVISION_OVERRIDE", "0" * 40)
    evidence_path = tmp_path / "evidence.json"

    exit_code = runner.main(["--host", FIXTURE_ADAPTER_COMMAND, "--evidence", str(evidence_path)])

    assert exit_code == 1
    assert not evidence_path.exists()
