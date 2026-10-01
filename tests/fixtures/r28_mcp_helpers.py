"""Shared harness for the R28 E28-1 native Genia MCP skeleton tests.

The harness speaks raw newline-delimited JSON-RPC (MCP 2026-07-28 stdio) to the
native ``apps/mcp/mcp.genia`` program started by the ordinary Genia CLI. It
contains no MCP application logic: it builds requests, runs the server, and
splits stdout on ``\\n`` only (never ``str.splitlines``, which also splits on
U+2028/U+2029 and would mask a framing defect).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_PATH = REPO_ROOT / "apps" / "mcp" / "mcp.genia"
LAUNCHER_PATH = REPO_ROOT / "hosts" / "python" / "mcp_launch.py"

GENIA_MAIN = "from genia.interpreter import _main; raise SystemExit(_main())"

REVISION = "0123456789abcdef0123456789abcdef01234567"
OTHER_REVISION = "fedcba9876543210fedcba9876543210fedcba98"

PROTOCOL_VERSION = "2026-07-28"
META_VERSION = "io.modelcontextprotocol/protocolVersion"
META_CAPABILITIES = "io.modelcontextprotocol/clientCapabilities"
META_CLIENT_INFO = "io.modelcontextprotocol/clientInfo"
META_SERVER_INFO = "io.modelcontextprotocol/serverInfo"


def good_meta(**extra):
    meta = {META_VERSION: PROTOCOL_VERSION, META_CAPABILITIES: {}}
    meta.update(extra)
    return meta


def request(method, req_id=1, params=None, *, meta=True):
    """Build one JSON-RPC request object (per-request ``_meta`` by default)."""
    body = dict(params or {})
    if meta is True:
        body["_meta"] = good_meta()
    elif meta is not False:
        body["_meta"] = meta
    return {"jsonrpc": "2.0", "id": req_id, "method": method, "params": body}


def notification(method, params=None):
    message = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        message["params"] = params
    return message


def encode(message, *, ensure_ascii=True) -> bytes:
    return json.dumps(message, ensure_ascii=ensure_ascii, separators=(",", ":")).encode("utf-8")


def server_env(extra=None):
    env = dict(os.environ)
    src = str(REPO_ROOT / "src")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src if not existing else os.pathsep.join([src, existing])
    env.update(extra or {})
    return env


def server_command(args):
    assert SERVER_PATH.is_file(), (
        "E28-1 not implemented: apps/mcp/mcp.genia does not exist "
        "(native Genia MCP server expected at this path)"
    )
    # Same invocation as hosts/python/exec_cli.py (`-m genia.interpreter` would emit
    # a runpy RuntimeWarning on stderr, which must stay free of protocol noise).
    return [sys.executable, "-c", GENIA_MAIN, str(SERVER_PATH), *args]


def run_raw(lines, *, args=(REVISION,), cwd=None, env=None, timeout=60):
    """Run the server directly (no launcher) with raw byte lines on stdin."""
    stdin = b"".join(line + b"\n" for line in lines)
    return subprocess.run(
        server_command(list(args)),
        input=stdin,
        capture_output=True,
        cwd=str(cwd) if cwd else str(REPO_ROOT),
        env=env if env is not None else server_env(),
        timeout=timeout,
    )


def run_messages(messages, **kwargs):
    return run_raw([encode(m) for m in messages], **kwargs)


def frames(stdout: bytes):
    """Split stdout into protocol frames on newline only."""
    assert stdout == b"" or stdout.endswith(b"\n"), "last frame not newline-terminated"
    if stdout == b"":
        return []
    return stdout[:-1].split(b"\n")


def responses(completed):
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    decoded = []
    for frame in frames(completed.stdout):
        assert frame != b"", "empty protocol line on stdout"
        decoded.append(json.loads(frame.decode("utf-8")))
    return decoded


def call(message, **kwargs):
    """Send one request, return its single decoded response."""
    out = responses(run_messages([message], **kwargs))
    assert len(out) == 1, out
    return out[0]


@lru_cache(maxsize=None)
def _cached(key):
    kind, payload = key
    message = json.loads(payload)
    return call(message)


def cached_call(message):
    return _cached(("call", json.dumps(message, sort_keys=True)))


def expected_capabilities(revision=REVISION, tools=("genia_capabilities",)):
    return {
        "server": {"name": "genia-mcp", "contract": "genia.mcp.v1"},
        "mcp": {"protocol_version": PROTOCOL_VERSION, "transport": "stdio"},
        "genia": {
            "host": "python-reference",
            "contract_revision": revision,
            "portable_mcp_implementation": False,
        },
        "tools": list(tools),
        "execution_profile": {
            "name": "source-only-isolated-v1",
            "source_max_bytes": 262144,
            "timeout_ms": 5000,
            "stdout_max_bytes": 1048576,
            "stderr_max_bytes": 1048576,
            "value_max_bytes": 1048576,
            "diagnostic_max_bytes": 65536,
            "filesystem": False,
            "environment": False,
            "configuration": False,
            "secrets": False,
            "network": False,
        },
    }


def expected_envelope(revision=REVISION, tools=("genia_capabilities",)):
    return {
        "schema_version": "genia.mcp.v1",
        "status": "ok",
        "result": expected_capabilities(revision, tools),
        "error": None,
    }


FIXED_MESSAGES = {
    -32700: "Parse error",
    -32600: "Invalid request",
    -32601: "Method not found",
    -32602: "Invalid params",
    -32022: "Unsupported protocol version",
}
UNKNOWN_TOOL_MESSAGE = "Unknown tool"


def assert_protocol_error(response, code, *, req_id=..., message=None, data=None):
    """Assert a verified 2026-07-28 JSON-RPC error response shape."""
    assert response["jsonrpc"] == "2.0"
    assert "result" not in response
    if req_id is ...:
        pass
    elif req_id is None:
        assert "id" not in response, response
    else:
        assert response["id"] == req_id
        assert type(response["id"]) is type(req_id)
    error = response["error"]
    assert type(error["code"]) is int and error["code"] == code
    assert error["message"] == (message or FIXED_MESSAGES[code])
    if data is None:
        assert set(error) == {"code", "message"}, error
    else:
        assert set(error) == {"code", "message", "data"}, error
        assert error["data"] == data


# --- E28-2: launcher mode (host provisions the parse capability) -------------

PARSE_TOOLS = ("genia_capabilities", "genia_parse")
CAPABILITY_PATH = REPO_ROOT / "hosts" / "python" / "mcp_parse_capability.py"
HOST_BOOTSTRAP_PATH = REPO_ROOT / "hosts" / "python" / "mcp_host.py"


def repository_revision() -> str:
    done = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout.strip()


def run_launcher_raw(lines, *, timeout=120):
    """Run the server through the host launcher (parse capability provisioned)."""
    assert HOST_BOOTSTRAP_PATH.is_file(), (
        "E28-2 not implemented: hosts/python/mcp_host.py does not exist"
    )
    stdin = b"".join(line + b"\n" for line in lines)
    return subprocess.run(
        [sys.executable, "-m", "hosts.python.mcp_launch"],
        input=stdin,
        capture_output=True,
        cwd=str(REPO_ROOT),
        env=server_env(),
        timeout=timeout,
    )


def launcher_call(message, **kwargs):
    out = responses(run_launcher_raw([encode(message)], **kwargs))
    assert len(out) == 1, out
    return out[0]


def parse_request(source, req_id=1, **extra_arguments):
    arguments = {"source": source}
    arguments.update(extra_arguments)
    return request("tools/call", req_id, {"name": "genia_parse", "arguments": arguments})


def error_envelope(kind, phase, message):
    return {
        "schema_version": "genia.mcp.v1",
        "status": "error",
        "result": None,
        "error": {"kind": kind, "message": message, "phase": phase},
    }
