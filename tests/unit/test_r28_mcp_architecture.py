"""R28 E28-1 (issue #702): native-Genia ownership and Python-drift tests.

Evidence that the MCP application lives in ``apps/mcp/mcp.genia`` and that Python
owns none of: tool dispatch, MCP application policy, request validation,
capability result construction, or result-envelope construction. The host may
supply only the build/launch ``contract_revision``.

Behavioral evidence is preferred (differential runs, no-authority runs); the AST
scans are a drift tripwire for future moves of application logic into Python, not
a substitute for behavior. Expected to fail until ``mcp.genia`` exists.
"""

from __future__ import annotations

import ast
import os
import re
import tempfile
from pathlib import Path

import pytest

from tests.fixtures.r28_mcp_helpers import (
    LAUNCHER_PATH,
    OTHER_REVISION,
    REPO_ROOT,
    REVISION,
    SERVER_PATH,
    request,
    run_messages,
)

pytestmark = pytest.mark.unit

# Literals that define the MCP application. They must live in mcp.genia only.
APPLICATION_LITERALS = (
    "genia_capabilities",
    "genia_parse",
    "genia_run",
    "genia.mcp.v1",
    "source-only-isolated-v1",
    "server/discover",
    "tools/list",
    "tools/call",
    "resultType",
    "structuredContent",
    "io.modelcontextprotocol",
    "genia-mcp",
    "2026-07-28",
)

PYTHON_ROOTS = ("src", "hosts", "apps", "tools", "scripts")

SESSION = [
    request("server/discover", 1),
    request("tools/list", 2),
    request("tools/call", 3, {"name": "genia_capabilities"}),
    request("tools/call", 4, {"name": "genia_parse"}),
    request("tools/call", 5, {"name": "genia_capabilities", "arguments": {"x": 1}}),
    request("initialize", 6),
    request("tools/list", 7, meta={"io.modelcontextprotocol/protocolVersion": "1900-01-01",
                                   "io.modelcontextprotocol/clientCapabilities": {}}),
]


def _python_sources():
    for root in PYTHON_ROOTS:
        base = REPO_ROOT / root
        if base.is_dir():
            yield from (p for p in base.rglob("*.py") if ".venv" not in p.parts)


def _string_constants(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.value


# --- positive: the native program owns the application -----------------------


def test_native_server_program_exists_and_is_genia_source():
    assert SERVER_PATH.is_file(), "E28-1 not implemented: apps/mcp/mcp.genia missing"
    assert SERVER_PATH.suffix == ".genia"
    assert SERVER_PATH.stat().st_size > 0


def test_native_program_owns_every_application_literal_it_must_own():
    assert SERVER_PATH.is_file(), "E28-1 not implemented: apps/mcp/mcp.genia missing"
    source = SERVER_PATH.read_text(encoding="utf-8")
    for literal in (
        "genia_capabilities",
        "genia.mcp.v1",
        "source-only-isolated-v1",
        "server/discover",
        "tools/list",
        "tools/call",
        "resultType",
        "structuredContent",
        "genia-mcp",
        "2026-07-28",
        "io.modelcontextprotocol/protocolVersion",
        # E28-2: the parse tool's descriptor, limits, and envelopes are native too.
        "genia_parse",
        "input_limit",
        "result_limit",
        "parse_error",
        "Genia source failed to parse",
    ):
        assert literal in source, f"mcp.genia must own literal {literal!r}"


def test_intermediate_surface_does_not_advertise_later_tickets_in_source_policy():
    # Through E28-2 the server may implement genia_parse but not genia_run, which
    # E28-3 adds with its own evidence.
    assert SERVER_PATH.is_file(), "E28-1 not implemented: apps/mcp/mcp.genia missing"
    source = SERVER_PATH.read_text(encoding="utf-8")
    assert "genia_run" not in source


# --- negative: Python owns no application logic -------------------------------


def test_no_python_module_defines_mcp_application_literals():
    offenders = []
    for path in _python_sources():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for value in _string_constants(tree):
            for literal in APPLICATION_LITERALS:
                if literal in value:
                    offenders.append((str(path.relative_to(REPO_ROOT)), literal))
    assert offenders == [], (
        "MCP application literals must live only in apps/mcp/mcp.genia: " f"{offenders}"
    )


def test_no_mcp_sdk_import_or_dependency():
    banned = {"mcp", "fastmcp", "modelcontextprotocol"}
    offenders = []
    for path in _python_sources():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names = [node.module.split(".")[0]]
            if banned.intersection(names):
                offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == []
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert not re.search(r"(?im)^\s*[\"']?(mcp|fastmcp)\b", pyproject)
    lock = REPO_ROOT / "uv.lock"
    if lock.exists():
        assert 'name = "mcp"' not in lock.read_text(encoding="utf-8")


def test_launcher_is_a_narrow_host_shim_with_no_json_or_protocol_code():
    assert LAUNCHER_PATH.is_file(), "E28-1 not implemented: hosts/python/mcp_launch.py missing"
    tree = ast.parse(LAUNCHER_PATH.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module.split(".")[0])
    allowed = {"__future__", "collections", "os", "pathlib", "re", "subprocess", "sys", "typing"}
    assert imported <= allowed, f"launcher imports beyond the narrow allowlist: {imported - allowed}"
    assert "json" not in imported  # the host never constructs JSON responses


# --- behavioral: host supplies only the revision ------------------------------


def _session_bytes(revision):
    completed = run_messages(SESSION, args=(revision,))
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    return completed.stdout


def test_changing_only_the_host_revision_changes_only_revision_bytes():
    a = _session_bytes(REVISION)
    b = _session_bytes(OTHER_REVISION)
    assert a != b  # the revision really is reported...
    # ...and is the ONLY thing the host controls: substituting it makes the
    # entire session output byte-identical, so no Python path shaped any other
    # field of discovery, list, capability, error, or framing output.
    assert a.replace(REVISION.encode(), OTHER_REVISION.encode()) == b


def test_output_is_identical_with_empty_cwd_and_minimal_environment():
    baseline = _session_bytes(REVISION)
    with tempfile.TemporaryDirectory() as empty:
        minimal = {
            "PATH": "/usr/bin:/bin",
            "PYTHONPATH": str(REPO_ROOT / "src"),
            "PYTHONIOENCODING": "utf-8",
        }
        # Loader paths are launch plumbing for a shared-library Python (for
        # example actions/setup-python on a self-hosted runner), not user state.
        for key in ("LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH"):
            if key in os.environ:
                minimal[key] = os.environ[key]
        completed = run_messages(SESSION, cwd=Path(empty), env=minimal)
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    assert completed.stdout == baseline  # no cwd/environment/workspace dependence


def test_native_program_requests_no_filesystem_network_process_or_config_authority():
    assert SERVER_PATH.is_file(), "E28-1 not implemented: apps/mcp/mcp.genia missing"
    source = SERVER_PATH.read_text(encoding="utf-8")
    imports = re.findall(r"(?m)^\s*import\s+([A-Za-z_][\w.]*)", source)
    assert imports == [], f"mcp.genia must import no modules in E28-1: {imports}"
    for token in (
        "read_file",
        "write_file",
        "zip_read",
        "execution.process",
        "web.",
        "http_send",
        "secret_get",
        "config_get",
        "spawn(",
    ):
        assert token not in source, f"mcp.genia must not reference {token!r}"


def test_no_python_specific_text_crosses_the_mcp_boundary():
    # Closed values only: no tracebacks, class names, paths, or reprs.
    out = _session_bytes(REVISION).decode("utf-8")
    for leak in ("Traceback", "python", "Python", ".py", "<class", "0x"):
        assert leak not in out.replace("python-reference", "")
