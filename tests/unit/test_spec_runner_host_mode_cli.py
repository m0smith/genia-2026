"""
E16-2 (issue #759) end-to-end proof that ``tools.spec_runner.runner.main``
can drive an external adapter command through ``--host``, with the same
CLI/reporting surface, transport isolation, and deterministic taxonomy
exercised through a monkeypatched, crafted spec list against the
deterministic E16-1 fixture adapter. The default in-process path
(no ``--host``) is asserted unchanged.
"""
from __future__ import annotations

import shlex
import sys
from pathlib import Path

from tools.spec_runner import runner
from tools.spec_runner.loader import InvalidSpec, LoadedSpec

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ADAPTER_COMMAND = shlex.join(
    [sys.executable, "-m", "tools.spec_runner.fixtures.protocol_fixture_adapter"]
)


def _spec(
    name: str,
    *,
    expected_stdout: str,
    expected_stderr: str = "",
    expected_exit_code: int = 0,
    source: str = "hello",
) -> LoadedSpec:
    return LoadedSpec(
        name=name,
        category="eval",
        source=source,
        stdin="",
        expected_stdout=expected_stdout,
        expected_stderr=expected_stderr,
        expected_exit_code=expected_exit_code,
        expected_ir=None,
        path=Path("spec/eval") / f"{name}.yaml",
    )


def _crafted_specs() -> tuple[list[LoadedSpec], list[InvalidSpec]]:
    return (
        [
            _spec("ok", expected_stdout="fixture-stdout:hello\n"),
            _spec("ok-but-wrong-expectation", expected_stdout="nope\n"),
            _spec("unsupported", expected_stdout=""),
            _spec("stdout-leak", expected_stdout=""),
            _spec("crash", expected_stdout=""),
            _spec("hang", expected_stdout=""),
        ],
        [],
    )


def test_host_mode_reports_every_taxonomy_outcome_and_exits_nonzero(monkeypatch, capsys) -> None:
    monkeypatch.setattr(runner, "discover_specs", _crafted_specs)

    exit_code = runner.main(["--host", FIXTURE_ADAPTER_COMMAND, "--host-timeout", "0.5"])

    out = capsys.readouterr().out
    assert exit_code == 1  # protocol_error/crash/timeout present

    assert "Summary: total=6 passed=1 failed=1 unsupported=1 protocol_error=1 crash=1 timeout=1 invalid=0" in out
    per_case_lines = out.split("Summary:")[0]
    # A pass is only ever counted, never printed as its own per-case line.
    assert not any(line.startswith("PASS ") for line in per_case_lines.splitlines())
    assert "FAIL eval ok-but-wrong-expectation" in out
    assert "UNSUPPORTED eval unsupported" in out
    assert "PROTOCOL_ERROR eval stdout-leak" in out
    assert "CRASH eval crash" in out
    assert "TIMEOUT eval hang" in out


def test_host_mode_all_pass_exits_zero(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        runner,
        "discover_specs",
        lambda: ([_spec("ok", expected_stdout="fixture-stdout:hello\n")], []),
    )

    exit_code = runner.main(["--host", FIXTURE_ADAPTER_COMMAND])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Summary: total=1 passed=1 failed=0 unsupported=0 protocol_error=0 crash=0 timeout=0 invalid=0" in out


def test_default_mode_is_unchanged_without_host_flag(monkeypatch, capsys) -> None:
    """Proves the existing in-process path is untouched by this slice: a
    spec whose ``source`` triggers a genuine Python eval failure still goes
    through the normal in-process comparator/report_failure path, not the
    host-mode taxonomy reporter."""
    monkeypatch.setattr(
        runner,
        "discover_specs",
        lambda: ([_spec("real-eval", source="1", expected_stdout="1\n")], []),
    )

    exit_code = runner.main([])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Summary: total=1 passed=1 failed=0 invalid=0" in out
    assert "unsupported=" not in out
