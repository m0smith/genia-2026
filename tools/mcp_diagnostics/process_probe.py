"""Development diagnostic for governed-worker discovery by the lifecycle test helpers (ledger R28-H47).

The lifecycle conformance tests find the live worker through the process-inspection backend
(`/proc` on Linux, `ps`/`lsof` elsewhere). Run this where `wait_for_worker()` never sees a worker
(macOS) and send back the whole output:

    uv run --no-project --no-python-downloads python tools/mcp_diagnostics/process_probe.py

It starts the server exactly as the tests do, starts a long run, and prints for every process below
the launcher: the raw `ps` row without and with `-ww`, the argv the helpers parsed, whether they
recognise it as the governed worker, and its working directory; then a `VERDICT` line. It is a developer
tool: not imported by the server, no MCP behavior.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO_ROOT), str(REPO_ROOT / "src")]

from tests.fixtures import r28_mcp_helpers as h  # noqa: E402


def _raw_ps(pid, wide):
    """Return one raw `ps` row for a pid, optionally with wide argv output."""

    command = ["ps", "-o", "pid=,ppid=,lstart=,command=", "-p", str(pid)]
    if wide:
        command.insert(1, "-ww")
    done = subprocess.run(command, capture_output=True, text=True, check=False,
                          env={"LC_ALL": "C", "PATH": h._TOOL_PATH})
    return done.stdout.strip() or done.stderr.strip()


def main() -> int:
    """Run the diagnostic probe and report whether worker discovery succeeds."""

    report = {"backend": h.process_backend(), "sys.platform": sys.platform, "worker_rows": [], "governed_workers": []}
    with h.LauncherSession() as session:
        session.wait_ready()
        session.send(h.run_request("sleep(60000)", 1))
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline and not session.governed_workers():
            time.sleep(0.05)
        for pid in sorted(session.descendants()):
            identity = h.process_identity(pid)
            report["worker_rows"].append({
                "pid": pid,
                "raw_ps_default": _raw_ps(pid, False),
                "raw_ps_ww": _raw_ps(pid, True),
                "parsed_argv": h._cmdline(pid),
                "is_governed_worker": h.is_governed_worker(pid),
                "cwd": str(h.worker_workdir(identity)) if identity else None,
            })
        report["governed_workers"] = sorted(w[0] for w in session.governed_workers())
        report["launcher_pid"] = session.proc.pid
    found = bool(report["governed_workers"])
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    print("VERDICT", "OK: the helpers found the governed worker" if found else
          "FAIL: no process below the launcher was recognised as the governed worker; read parsed_argv and raw_ps_*")
    return 0 if found else 1


if __name__ == "__main__":
    os.environ.pop("GENIA_MCP_WORKER_DIAG", None)
    raise SystemExit(main())
