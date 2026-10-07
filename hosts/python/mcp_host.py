"""In-process host bootstrap for the native Genia MCP server (R28 E28-2/E28-3, issues #703, #704).

Loads `apps/mcp/mcp.genia` and calls its `serve(revision, host)` function with the
host capabilities passed explicitly as an argument (never as ambient bindings),
following the `hosts/python/exec_ollama_chat.py` precedent (ledger R28-H20). The
capabilities provisioned are `parse` (`mcp_parse_capability.parse_source`) and `run`
(`mcp_run_capability.RunCapability`, E28-3). All
protocol, validation, dispatch, and result construction stay in `mcp.genia`.

Usage (started by `hosts/python/mcp_launch.py`):
    python -c "from hosts.python.mcp_host import main; ..." <mcp.genia path> <revision>
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
    """Unwind host execution on SIGTERM/SIGHUP with shell-style exit status.

    Raising SystemExit lets active supervisor finally blocks reap the worker and
    remove its directory; no cleanup is performed inside this signal handler.
    """
    raise SystemExit(128 + signum)


def main(argv: list[str] | None = None) -> int:
    """Load the native MCP server and serve with explicit parse/run capabilities.

    argv supplies exactly the server path and revision; wrong arity writes a fixed
    stderr diagnostic and returns 1. Installs termination handlers, consumes stdin
    through LineMux, and probes isolation before serving. Returns 0 when serve
    finishes; file, evaluation, initialization and signal exceptions propagate.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        sys.stderr.write("host bootstrap: expected <server path> <revision>\n")
        return 1
    server_path, revision = Path(args[0]), args[1]
    # The host owns raw stdin line multiplexing (not protocol work) so that a
    # cancellation notification can be observed while a run is in flight (ledger R28-H27).
    # SIGTERM and SIGHUP unwind like an exit so the supervisor's cleanup (kill and reap the worker
    # group, remove its temp directory) runs; without it the worker would be orphaned and its
    # private directory leaked (SIGHUP: ledger R28-H41, found by the E28-5 lifecycle matrix).
    # SIGINT already unwinds as KeyboardInterrupt.
    signal.signal(signal.SIGTERM, _terminate)
    signal.signal(signal.SIGHUP, _terminate)
    mux = LineMux(sys.stdin.fileno())
    env = make_global_env(cli_args=[], stdin_provider=mux.provider)
    run_source(server_path.read_text(encoding="utf-8"), env, filename=str(server_path))
    # Constructing the run capability determines its best-effort isolation profile (a
    # bounded one-time probe) here, before `serve` reads any request (ledger R28-H33).
    run_capability = RunCapability(mux)
    host = GeniaMap().put("parse", parse_source).put("run", run_capability.run)
    env.get("serve")(revision, host)
    return 0
