"""R28 E28-4 (issue #705): the official MCP client SDK uses the configured server end to end.

Runs the pinned harness in tools/mcp_acceptance/ (official TypeScript client SDK v2) against the
command read from the checked-in `.mcp.json`. Needs Node and the locked dependencies
(`npm ci` in the harness directory). Skipped locally when they are absent unless
GENIA_REQUIRE_MCP_CLIENT=1 (set by the dedicated CI job), where absence is a failure.
Expected to fail until E28-4 lands (red phase).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess

import pytest

from tests.fixtures.r28_mcp_helpers import ACCEPTANCE_HARNESS_DIR, MCP_CONFIG_PATH, RUN_TOOLS

pytestmark = pytest.mark.unit

REQUIRED_STEPS = [
    "discover",
    "tools",
    "capabilities",
    "parse_invalid",
    "parse_valid",
    "run",
    "framing",
    "authority",
]


def _harness_ready():
    required = os.environ.get("GENIA_REQUIRE_MCP_CLIENT") == "1"
    installed = (ACCEPTANCE_HARNESS_DIR / "node_modules" / "@modelcontextprotocol" / "client").is_dir()
    if shutil.which("node") is None or not installed:
        message = "Node or the locked harness dependencies are not installed (npm ci)"
        if required:
            pytest.fail(message)
        pytest.skip(message)


def test_the_harness_is_a_small_pinned_lockfile_project():
    package = ACCEPTANCE_HARNESS_DIR / "package.json"
    assert package.is_file(), "E28-4 not implemented: tools/mcp_acceptance/package.json missing"
    data = json.loads(package.read_text(encoding="utf-8"))
    assert data.get("private") is True and data.get("type") == "module"
    assert data["dependencies"] == {"@modelcontextprotocol/client": "2.2.0"}  # exact, no range
    assert (ACCEPTANCE_HARNESS_DIR / "package-lock.json").is_file()
    assert (ACCEPTANCE_HARNESS_DIR / "acceptance.mjs").is_file()
    assert not (ACCEPTANCE_HARNESS_DIR / "node_modules").is_symlink()


def test_the_harness_reads_the_launch_command_from_the_checked_in_configuration():
    script = (ACCEPTANCE_HARNESS_DIR / "acceptance.mjs").read_text(encoding="utf-8")
    assert ".mcp.json" in script and "mcpServers" in script
    assert "versionNegotiation" not in script or "auto" in script  # modern negotiation, not legacy
    assert MCP_CONFIG_PATH.is_file()


def test_the_official_client_completes_the_acceptance_scenario():
    _harness_ready()
    done = subprocess.run(
        ["node", "acceptance.mjs"],
        cwd=str(ACCEPTANCE_HARNESS_DIR),
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    report = json.loads(done.stdout.strip().splitlines()[-1])
    assert report["ok"] is True
    assert report["client"]["package"] == "@modelcontextprotocol/client"
    assert report["client"]["version"] == "2.2.0"
    assert report["negotiation"] in ("auto", "pin")
    assert report["tools"] == list(RUN_TOOLS)
    assert [step["name"] for step in report["steps"]] == REQUIRED_STEPS
    assert all(step["ok"] for step in report["steps"]), report["steps"]
    run_step = next(step for step in report["steps"] if step["name"] == "run")
    assert run_step["detail"]["rendered"] == "42"
    assert run_step["detail"]["stdout"] == "to-stdout\n"
    assert run_step["detail"]["stderr"] == "to-stderr\n"
    assert run_step["detail"]["exit_code"] == 0
