"""R28 E28-4 (issue #705): the checked-in, credential-free stdio client configuration.

Pinned to docs/design/r28-e28-4-stdio-transport-design.md sections 1, 3, 8 and contract
sections 7, 9.3, 12.1. Static checks only; the launch behavior is in
test_r28_mcp_stdio_launch.py. Expected to fail until E28-4 lands (red phase).
"""

from __future__ import annotations

import json
import re

import pytest

from tests.fixtures.r28_mcp_helpers import (
    MCP_CONFIG_PATH,
    MCP_SERVER_NAME,
    REPO_ROOT,
    STDIO_GUIDE_PATH,
    VSCODE_MCP_CONFIG_PATH,
    configured_command,
    load_mcp_config,
)

pytestmark = pytest.mark.unit

EXPECTED_COMMAND = [
    "uv",
    "run",
    "--no-project",
    "--no-python-downloads",
    "python",
    "hosts/python/mcp_launch.py",
]


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


# --- the one portable configuration --------------------------------------------------------


def test_one_repository_root_portable_configuration_exists():
    assert MCP_CONFIG_PATH.is_file(), "E28-4 not implemented: .mcp.json missing"
    config = load_mcp_config()
    assert set(config) == {"mcpServers"}  # the portable format's only top-level key
    assert list(config["mcpServers"]) == [MCP_SERVER_NAME]


def test_the_vscode_specific_file_is_not_duplicated():
    # Contract 12.1: do not duplicate; .vscode/mcp.json only if verified to be necessary.
    assert MCP_CONFIG_PATH.is_file(), "E28-4 not implemented: .mcp.json missing"
    assert not VSCODE_MCP_CONFIG_PATH.exists()
    for other in (".cursor/mcp.json", ".mcp/config.json", "mcp.json", ".github/mcp.json"):
        assert not (REPO_ROOT / other).exists(), other


def test_the_server_entry_is_exactly_the_documented_stdio_command():
    entry = load_mcp_config()["mcpServers"][MCP_SERVER_NAME]
    assert set(entry) == {"type", "command", "args"}
    assert entry["type"] == "stdio"
    assert configured_command() == EXPECTED_COMMAND


def test_the_configured_script_is_a_repository_relative_existing_file():
    script = configured_command()[-1]
    assert not script.startswith(("/", "~")) and ":" not in script and "\\" not in script
    assert (REPO_ROOT / script).is_file()


# --- credential-free, machine-independent ------------------------------------------------


def test_the_configuration_carries_no_environment_input_url_or_working_directory():
    entry = load_mcp_config()["mcpServers"][MCP_SERVER_NAME]
    for forbidden in ("env", "envFile", "inputs", "cwd", "url", "headers", "oauth", "sandbox"):
        assert forbidden not in entry and forbidden not in load_mcp_config(), forbidden


def test_the_configuration_contains_no_secret_absolute_path_or_machine_detail():
    import getpass
    import os

    text = MCP_CONFIG_PATH.read_text(encoding="utf-8")
    values = list(_strings(load_mcp_config()))
    assert not re.search(r"(?i)token|secret|password|api[_-]?key|bearer|credential", text)
    assert not any(v.startswith(("/", "~")) or re.match(r"^[A-Za-z]:[\\\\/]", v) for v in values)
    assert not any("${" in v or "$(" in v for v in values)  # no variable or shell expansion
    for private in {getpass.getuser(), os.path.expanduser("~"), str(REPO_ROOT)} - {"", "/", "root"}:
        assert private not in text, "machine-specific value in the checked-in configuration"
    assert text.endswith("\n") and "\t" not in text


def test_the_configuration_enables_no_http_transport():
    config = load_mcp_config()
    values = [v.lower() for v in _strings(config)]
    assert not any(v.startswith(("http:", "https:")) for v in values)
    assert all(v not in {"http", "sse", "streamable-http", "streamablehttp"} for v in values)


def test_the_launch_flags_forbid_ambient_acquisition():
    args = configured_command()
    assert "--no-project" in args  # no project sync, no environment creation, no network
    assert "--no-python-downloads" in args  # never fetch an interpreter at launch
    assert args[0] == "uv"
    assert "sh" not in args and "-c" not in args and "bash" not in args  # no shell


# --- HTTP stays deferred (static guard; green before and after) ----------------------------

LISTENER_PATTERNS = (
    r"\bhttp\.server\b",
    r"\bsocketserver\b",
    r"\bimport\s+asyncio\b",
    r"\baiohttp\b",
    r"\buvicorn\b",
    r"\bfastapi\b",
    r"\bflask\b",
    r"\bStreamable[Hh][Tt][Tt][Pp]\b",
    r"\.listen\(",
    r"\bbind\(",
)


def test_no_mcp_host_module_or_the_native_app_can_open_a_listener():
    paths = sorted((REPO_ROOT / "hosts" / "python").glob("mcp_*.py")) + [
        REPO_ROOT / "apps" / "mcp" / "mcp.genia"
    ]
    assert len(paths) >= 6
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for pattern in LISTENER_PATTERNS:
            if path.name == "mcp_worker.py" and pattern in (r"\.listen\(", r"\bbind\("):
                continue  # the worker's runtime *stubs* name socket methods in order to deny them
            assert not re.search(pattern, text), f"{path.name} matches {pattern}"


def test_no_python_mcp_sdk_is_a_dependency():
    for name in ("pyproject.toml", "uv.lock"):
        text = (REPO_ROOT / name).read_text(encoding="utf-8").lower()
        assert not re.search(r'(^|[\s"\'])mcp([>=<~!\s"\'\[]|$)', text), name
        assert "modelcontextprotocol" not in text, name


# --- developer documentation matches the configuration -------------------------------------


def test_the_stdio_guide_exists_and_quotes_the_exact_configured_command():
    assert STDIO_GUIDE_PATH.is_file(), "E28-4 not implemented: docs/mcp/stdio-development.md missing"
    text = STDIO_GUIDE_PATH.read_text(encoding="utf-8")
    assert " ".join(EXPECTED_COMMAND) in text
    assert ".mcp.json" in text


def test_the_stdio_guide_states_scope_and_limits_without_overclaiming():
    assert STDIO_GUIDE_PATH.is_file(), "E28-4 not implemented"
    text = STDIO_GUIDE_PATH.read_text(encoding="utf-8").lower()
    for required in (
        "exactly four",
        "genia_capabilities",
        "genia_parse",
        "genia_run",
        "streamable http is deferred",
        "not a security sandbox",
        "initialize",  # the legacy-handshake limitation
        "uv",
        "git",
        "posix",
        "not claim",  # what is deliberately not claimed
    ):
        assert required in text, f"guide must mention {required!r}"
    for overclaim in ("production-ready", "multi-tenant safe", "vs code acceptance passed"):
        assert overclaim not in text


def test_the_configuration_is_valid_json_with_stable_formatting():
    raw = MCP_CONFIG_PATH.read_text(encoding="utf-8")
    assert json.dumps(json.loads(raw), indent=2) + "\n" == raw
