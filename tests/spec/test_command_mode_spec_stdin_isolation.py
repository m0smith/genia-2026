from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

from hosts.python import exec_cli as exec_cli_module
from hosts.python.exec_cli import exec_cli
from tools.spec_runner.loader import load_spec


REPO = Path(__file__).resolve().parents[2]
CLI_DIR = REPO / "spec" / "cli"


def test_command_mode_collect_sum_closes_ambient_stdin(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(argv: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append({"argv": argv, **kwargs})
        return SimpleNamespace(stdout="0\n", stderr="", returncode=0)

    monkeypatch.setattr(exec_cli_module.subprocess, "run", fake_run)
    spec = load_spec(CLI_DIR / "command_mode_collect_sum.yaml")

    result = exec_cli(spec)

    assert result == {"stdout": "0\n", "stderr": "", "exit_code": 0}
    assert calls[0]["argv"][3:] == ["-c", spec.command]
    assert calls[0]["input"] is None
    assert calls[0]["stdin"] == subprocess.DEVNULL
