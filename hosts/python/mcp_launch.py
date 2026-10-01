"""Narrow host launcher for the native Genia MCP server (R28 E28-1, issue #702).

This module is build/launch identity plumbing only. It resolves the repository
revision (``contract_revision``), validates it as an inert 40-lowercase-hex value,
and starts ``apps/mcp/mcp.genia`` on the Python reference host (through the
in-process host bootstrap, ``hosts/python/mcp_host.py``) with a fixed environment
allowlist and that single program argument. It contains no MCP
protocol, validation, dispatch, policy, capability, or JSON construction: all of
that lives in ``mcp.genia`` (docs/analysis/r28-host-dependency-inventory.md,
R28-H10).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_PATH = REPO_ROOT / "apps" / "mcp" / "mcp.genia"

# The child runs the in-process host bootstrap, which loads mcp.genia and provisions
# the parse capability as an explicit argument (R28 E28-2). `-c` rather than `-m`
# keeps the runpy RuntimeWarning off stderr, which must stay free of protocol noise.
_GENIA_MAIN = "from hosts.python.mcp_host import main; raise SystemExit(main())"
_REVISION = re.compile(r"[0-9a-f]{40}")
# Launch plumbing only: interpreter lookup, text encoding, and the dynamic loader
# path a shared-library Python needs to start (for example actions/setup-python).
_ENV_ALLOWLIST = (
    "PATH",
    "LD_LIBRARY_PATH",
    "DYLD_LIBRARY_PATH",
    "PYTHONIOENCODING",
    "PYTHONUTF8",
    "LANG",
    "LC_ALL",
    "SYSTEMROOT",
)


class McpLaunchError(RuntimeError):
    """Fixed-message launch failure; never carries paths or raw host text."""


def _valid_revision(value: str) -> bool:
    return _REVISION.fullmatch(value) is not None


def resolve_contract_revision(repo_root: Path | None = None) -> str:
    """Return the repository HEAD commit as 40 lowercase hex, nothing else.

    Workspace state (modified/untracked files) is never described, and ambient
    ``GIT_*`` variables cannot redirect the lookup.
    """
    root = Path(repo_root) if repo_root is not None else REPO_ROOT
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    try:
        done = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=str(root),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        raise McpLaunchError("unable to determine the repository revision") from None
    revision = done.stdout.strip()
    if done.returncode != 0 or not _valid_revision(revision):
        raise McpLaunchError("unable to determine the repository revision")
    return revision


def build_server_command(revision: str, python: str = sys.executable) -> list[str]:
    """Return the argv that starts ``mcp.genia`` with only the revision datum."""
    if not _valid_revision(revision):
        raise McpLaunchError("contract revision must be 40 lowercase hex digits")
    return [python, "-c", _GENIA_MAIN, str(SERVER_PATH), revision]


def server_environment(base: Mapping[str, str]) -> dict[str, str]:
    """Return the fixed launch environment: an allowlist, nothing user-defined."""
    env = {key: base[key] for key in _ENV_ALLOWLIST if key in base}
    src = str(REPO_ROOT / "src")
    existing = base.get("PYTHONPATH")
    env["PYTHONPATH"] = src if not existing else os.pathsep.join([src, existing])
    env.setdefault("PYTHONUTF8", "1")
    return env


def main() -> int:
    try:
        command = build_server_command(resolve_contract_revision())
    except McpLaunchError as error:
        sys.stderr.write(f"launcher: {error}\n")
        return 1
    return subprocess.run(
        command, env=server_environment(os.environ), cwd=str(REPO_ROOT), check=False
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
