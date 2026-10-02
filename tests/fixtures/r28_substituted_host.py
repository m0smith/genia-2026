"""Test-only host bootstrap with a substituted governed worker (R28 E28-5, issue #706).

Mirrors `hosts/python/mcp_host.main` exactly except that the supervisor is constructed with a
caller-supplied worker command (the supervisor's own `worker_argv` seam, the one its unit
tests use). It lets wire-level tests drive the real native server and supervisor with a
crashing, garbage-emitting, or protected-value-bearing worker without editing or weakening
any production module. Usage: `python -c "from tests.fixtures.r28_substituted_host import
main; raise SystemExit(main())" <server path> <revision> <worker script>`.
"""

from __future__ import annotations

import signal
import sys
from pathlib import Path

from genia import make_global_env, run_source
from genia.values import GeniaMap
from hosts.python.mcp_parse_capability import parse_source
from hosts.python.mcp_run_capability import RunCapability
from hosts.python.mcp_stdin import LineMux


def _terminate(signum, _frame):
    raise SystemExit(128 + signum)


def main() -> int:
    server_path, revision, worker = sys.argv[1], sys.argv[2], sys.argv[3]
    signal.signal(signal.SIGTERM, _terminate)
    signal.signal(signal.SIGHUP, _terminate)
    mux = LineMux(sys.stdin.fileno())
    env = make_global_env(cli_args=[], stdin_provider=mux.provider)
    run_source(Path(server_path).read_text(encoding="utf-8"), env, filename=server_path)
    capability = RunCapability(mux, worker_argv=[sys.executable, "-B", worker], isolated=False)
    host = GeniaMap().put("parse", parse_source).put("run", capability.run)
    env.get("serve")(revision, host)
    return 0
