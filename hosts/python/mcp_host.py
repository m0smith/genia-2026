"""In-process host bootstrap for the native Genia MCP server (R28 E28-2, issue #703).

Loads `apps/mcp/mcp.genia` and calls its `serve(revision, host)` function with the
host capabilities passed explicitly as an argument (never as ambient bindings),
following the `hosts/python/exec_ollama_chat.py` precedent (ledger R28-H20). The only
capability provisioned is `parse` (`mcp_parse_capability.parse_source`). All
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


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        sys.stderr.write("host bootstrap: expected <server path> <revision>\n")
        return 1
    server_path, revision = Path(args[0]), args[1]
    env = make_global_env(cli_args=[])
    run_source(server_path.read_text(encoding="utf-8"), env, filename=str(server_path))
    host = GeniaMap().put("parse", parse_source)
    env.get("serve")(revision, host)
    return 0
