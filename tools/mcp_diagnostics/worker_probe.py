"""Development diagnostic for the governed run-tool worker path (ledger R28-H47).

Run on the machine where the run tool returns `internal_error` (for example macOS):

    uv run --no-project --no-python-downloads python tools/mcp_diagnostics/worker_probe.py

It prints one JSON report and a final `VERDICT` line. It reproduces the *production* path (the
supervisor's exact environment, working directory, session, and worker command) and adds only
what the production path hides: the worker's stderr and exit status, the outcome of every
process limit the worker applies, and the platform facilities the test helpers rely on.

It is a developer tool: nothing here is imported by the MCP server, it adds no MCP behavior, and
the MCP client still receives only the sanitized `internal_error`.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO_ROOT), str(REPO_ROOT / "src")]

from hosts.python import mcp_run_capability as supervisor  # noqa: E402
from hosts.python import mcp_worker as worker  # noqa: E402

LIMIT_CODE = r"""
import json, resource, sys
plan = json.loads(sys.argv[1])
out = {}
for name, soft, hard in plan:
    const = getattr(resource, name, None)
    if const is None:
        out[name] = {"status": "no-such-resource"}
        continue
    before = resource.getrlimit(const)
    try:
        resource.setrlimit(const, (soft, hard))
        out[name] = {"status": "ok", "before": before, "after": resource.getrlimit(const)}
    except BaseException as exc:
        out[name] = {"status": "FAILED", "before": before, "error": type(exc).__name__,
                     "errno": getattr(exc, "errno", None), "message": str(exc)}
print(json.dumps(out))
"""


def _run(argv, *, env=None, cwd=None, stdin_data=b"", timeout=60, new_session=True):
    try:
        done = subprocess.run(
            argv,
            input=stdin_data,
            capture_output=True,
            env=env,
            cwd=cwd,
            timeout=timeout,
            start_new_session=new_session,
            close_fds=True,
            check=False,
        )
    except BaseException as exc:  # noqa: BLE001
        return {"launch_error": f"{type(exc).__name__}: {exc}"}
    return {
        "returncode": done.returncode,
        "stdout": done.stdout.decode("utf-8", "replace")[:2000],
        "stderr": done.stderr.decode("utf-8", "replace")[:4000],
    }


def platform_facts() -> dict:
    return {
        "sys.platform": sys.platform,
        "platform": platform.platform(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "has_proc": Path("/proc").is_dir(),
        "ps": shutil.which("ps"),
        "lsof": shutil.which("lsof"),
        "unshare": shutil.which("unshare"),
    }


def limit_probe() -> dict:
    """Each limit the worker applies, individually, in a throwaway process (own failure each)."""
    plan = [
        ["RLIMIT_FSIZE", 0, 0],
        ["RLIMIT_CORE", 0, 0],
        ["RLIMIT_CPU", worker.CPU_SECONDS, worker.CPU_SECONDS],
        ["RLIMIT_NOFILE", worker.OPEN_FILES, worker.OPEN_FILES],
        ["RLIMIT_AS", worker.ADDRESS_SPACE_BYTES, worker.ADDRESS_SPACE_BYTES],
    ]
    result = {}
    for item in plan:  # one process per limit so an earlier failure cannot mask a later one
        report = _run([sys.executable, "-S", "-c", LIMIT_CODE, json.dumps([item])])
        try:
            result.update(json.loads(report["stdout"]))
        except (KeyError, ValueError):
            result[item[0]] = report
    return result


def production_path(source: str) -> dict:
    """Exactly what `RunCapability._run` does, plus the worker's stderr (normally discarded)."""
    workdir = tempfile.mkdtemp(prefix="genia-probe-")
    try:
        env = supervisor._worker_environment()
        env["GENIA_MCP_WORKER_DIAG"] = "1"  # the only addition: names an internal failure on stderr
        report = _run(
            supervisor.worker_command(supervisor.DEFAULT_WORKER_ARGV, False),
            env=env,
            cwd=workdir,
            stdin_data=source.encode("utf-8"),
        )
        report["env_keys"] = sorted(env)
        return report
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def supervised(source: str) -> str:
    return supervisor.RunCapability(isolated=False).run(source, lambda _line: False)


def helper_facilities() -> dict:
    facts = {}
    for name, argv in (("ps", ["ps", "-axo", "pid=,ppid=,command="]), ("lsof", ["lsof", "-v"])):
        report = _run(argv, timeout=15)
        facts[name] = {"returncode": report.get("returncode"), "error": report.get("launch_error")}
    return facts


def verdict(report: dict) -> str:
    failed = [n for n, r in report["limits"].items() if r.get("status") == "FAILED"]
    worker_diag = report["worker_stderr_diag"]
    if report["supervised_reply"].startswith('{"status": "completed"'):
        return "OK: the production path completes `1 + 2`; no failure to localize"
    if failed:
        return f"FAIL: process limit(s) rejected by this OS: {', '.join(failed)}; worker diag: {worker_diag or 'none'}"
    return f"FAIL: no limit rejected; first signal: {worker_diag or report['worker']}"


def main() -> int:
    report: dict = {"platform": platform_facts(), "limits": limit_probe()}
    report["worker"] = production_path("1 + 2")
    stderr = report["worker"].get("stderr", "")
    report["worker_stderr_diag"] = [line for line in stderr.splitlines() if "GENIA-WORKER-DIAG" in line]
    report["supervised_reply"] = supervised("1 + 2")
    report["helpers"] = helper_facilities()
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    print("VERDICT", verdict(report))
    return 0 if report["supervised_reply"].startswith('{"status": "completed"') else 1


if __name__ == "__main__":
    os.environ.pop("GENIA_MCP_WORKER_DIAG", None)
    raise SystemExit(main())
