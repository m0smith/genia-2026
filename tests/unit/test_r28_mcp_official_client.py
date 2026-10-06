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
    "schemas",
    "capabilities",
    "parse_invalid",
    "parse_valid",
    "parse_repair_run",
    "run",
    "run_failing",
    "framing",
    "authority",
    "sequential",
    "cancel",
    "disconnect",
    "relaunch",
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
    assert "GENIA_ACCEPT_NEGOTIATION" in script  # every negotiation path is selectable
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
    assert report["negotiation"] == "auto" and report["negotiated_protocol_version"] == "2026-07-28"
    assert report["tools"] == list(RUN_TOOLS)
    assert [step["name"] for step in report["steps"]] == REQUIRED_STEPS
    assert all(step["ok"] for step in report["steps"]), report["steps"]
    run_step = next(step for step in report["steps"] if step["name"] == "run")
    assert run_step["detail"]["rendered"] == "42"
    assert run_step["detail"]["stdout"] == "to-stdout\n"
    assert run_step["detail"]["stderr"] == "to-stderr\n"
    assert run_step["detail"]["exit_code"] == 0


@pytest.mark.parametrize("path,version", [("legacy", "2025-11-25"), ("sdk-default", "2025-11-25"), ("pin", "2026-07-28")])
def test_the_official_client_completes_the_scenario_on_every_negotiation_path(path, version):
    # Amendment A5: the same scenario (discovery, parse, run, channels, failures, cancel, disconnect,
    # relaunch) passes whichever era the client negotiates; only the wire shape differs.
    _harness_ready()
    done = subprocess.run(
        ["node", "acceptance.mjs"],
        cwd=str(ACCEPTANCE_HARNESS_DIR),
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
        env={**os.environ, "GENIA_ACCEPT_NEGOTIATION": path},
    )
    assert done.returncode == 0, done.stdout + done.stderr
    report = json.loads(done.stdout.strip().splitlines()[-1])
    assert report["ok"] is True and report["negotiation"] == path
    assert report["negotiated_protocol_version"] == version
    assert report["tools"] == list(RUN_TOOLS)
    assert all(step["ok"] for step in report["steps"]), report["steps"]


def test_the_official_client_matrix_covers_cancel_disconnect_and_relaunch():
    # E28-5 (matrix O1-O12): the extra end-to-end rows run inside the same harness and the same CI
    # job; the details below must be real observations, not vacuous passes.
    _harness_ready()
    done = subprocess.run(
        ["node", "acceptance.mjs"],
        cwd=str(ACCEPTANCE_HARNESS_DIR),
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    report = json.loads(done.stdout.strip().splitlines()[-1])
    details = {step["name"]: step["detail"] for step in report["steps"]}
    assert details["cancel"]["elapsed_ms"] < 5000  # cancelled well inside the 5,000 ms deadline
    assert details["disconnect"]["checked"] is True and details["disconnect"]["processes"] >= 2
    assert details["relaunch"]["clean_shutdown"] is True
    assert set(details["authority"].values()) == {"policy_denied"} and len(details["authority"]) >= 8
    assert details["sequential"]["calls"] == 12
    assert not (ACCEPTANCE_HARNESS_DIR.parent.parent / "genia-acceptance-must-not-exist").exists()


def test_version_negotiation_evidence_for_ledger_h36():
    # R28-H36 / amendment A5: the SDK default (`legacy`, `initialize` for 2025-11-25), `auto`, and a
    # pinned 2026-07-28 all connect and list exactly the three tools; each records its negotiated era.
    _harness_ready()
    done = subprocess.run(
        ["node", "negotiation.mjs"],
        cwd=str(ACCEPTANCE_HARNESS_DIR),
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    report = json.loads(done.stdout.strip().splitlines()[-1])
    by_label = {r["label"]: r for r in report["results"]}
    assert report["client_version"] == "2.2.0"
    expected = {"sdk-default": "2025-11-25", "legacy": "2025-11-25", "auto": "2026-07-28", "pin": "2026-07-28"}
    for label, version in expected.items():
        assert by_label[label]["connected"] is True and by_label[label]["tools"] == list(RUN_TOOLS), label
        assert by_label[label]["negotiated_protocol_version"] == version, label
