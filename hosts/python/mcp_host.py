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

import sys
from pathlib import Path

from genia import make_global_env, run_source
from genia.values import GeniaMap
from hosts.python.mcp_parse_capability import parse_source
from hosts.python.mcp_run_capability import RunCapability
from hosts.python.mcp_stdin import LineMux


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        sys.stderr.write("host bootstrap: expected <server path> <revision>\n")
        return 1
    server_path, revision = Path(args[0]), args[1]
    # The host owns raw stdin line multiplexing (not protocol work) so that a
    # cancellation notification can be observed while a run is in flight (ledger R28-H27).
    mux = LineMux(sys.stdin.fileno())
    env = make_global_env(cli_args=[], stdin_provider=mux.provider)
    run_source(server_path.read_text(encoding="utf-8"), env, filename=str(server_path))
    # Constructing the run capability determines its best-effort isolation profile (a
    # bounded one-time probe) here, before `serve` reads any request (ledger R28-H33).
    run_capability = RunCapability(mux)
    host = GeniaMap().put("parse", parse_source).put("run", run_capability.run)
    env.get("serve")(revision, host)
    return 0
