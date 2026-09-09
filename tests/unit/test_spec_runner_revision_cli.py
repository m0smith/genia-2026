"""
E16-4 (issue #761) end-to-end proof that `tools.spec_runner.runner`
classifies a host's declared contract_revision and reports pinned vs.
current-main-compatibility evidence, or stops deterministically on an
unresolvable revision, without ever rewriting the host's declared claim.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tools.spec_runner import runner
from tools.spec_runner.loader import LoadedSpec
from tools.spec_runner.revision import REPO_ROOT, current_revision

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


def test_declared_revision_matching_current_reports_pinned(monkeypatch, capsys) -> None:
    monkeypatch.setattr(runner, "discover_specs", _one_pass_spec)
    exit_code = runner.main(["--host", FIXTURE_ADAPTER_COMMAND])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert f"Revision: pinned conformance for {current_revision()}" in out


def test_declared_ancestor_revision_reports_current_main_compatibility_only(monkeypatch, capsys) -> None:
    monkeypatch.setattr(runner, "discover_specs", _one_pass_spec)
    parent = subprocess.run(
        ["git", "rev-parse", "HEAD~1"], cwd=str(REPO_ROOT), capture_output=True, text=True, check=True
    ).stdout.strip()
    monkeypatch.setenv("FIXTURE_CONTRACT_REVISION_OVERRIDE", parent)

    exit_code = runner.main(["--host", FIXTURE_ADAPTER_COMMAND])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "Revision: current-main compatibility only" in out
    assert parent in out
    assert current_revision() in out
    # The host's own declared claim is never rewritten by the runner.
    assert "Revision: pinned conformance for" not in out


def test_unresolvable_declared_revision_stops_before_any_case_runs(monkeypatch, capsys) -> None:
    ran_any_case = False

    def _fail_if_called():  # pragma: no cover - only invoked on regression
        nonlocal ran_any_case
        ran_any_case = True
        return _one_pass_spec()

    monkeypatch.setattr(runner, "discover_specs", _fail_if_called)
    monkeypatch.setenv("FIXTURE_CONTRACT_REVISION_OVERRIDE", "0" * 40)

    exit_code = runner.main(["--host", FIXTURE_ADAPTER_COMMAND])
    out = capsys.readouterr().out

    assert exit_code == 1
    assert "UNRESOLVABLE host-declared contract_revision" in out
    assert "0" * 40 in out
    assert ran_any_case is False
    assert "Summary:" not in out
