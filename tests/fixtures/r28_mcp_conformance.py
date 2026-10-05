"""Shared helpers for the R28 E28-5 conformance and parity matrix tests (issue #706).

Everything here drives the *existing* surfaces (the launcher, the supervisor seam, the
official-client harness). It contains no MCP application logic and no production behavior.

Direct-host oracle (matrix decision M4): command-source evaluation through the same library
call the worker makes (`run_source(source, env, filename="<command>")`, value rendered by the
canonical debug renderer, program output captured separately), in an *unrestricted* default
global environment. It is not the CLI `-c` mode, which dispatches `main` and prints one text
stream (ledger R28-H29).
"""

from __future__ import annotations

import io
import json
import os
import sys
import textwrap
from functools import lru_cache

from tests.fixtures.r28_mcp_helpers import (
    REPO_ROOT,
    compat_handshake,
    compat_parse,
    compat_run,
    denied_namespace_path,
    encode,
    frames,
    parse_request,
    run_request,
    server_env,
    structured,
)

NS_MODES = ("host", "denied")  # "host": whatever this host really does; "denied": simulated

SOURCE_LIMIT = 262144
CHANNEL_LIMIT = 1048576
AGGREGATE_LIMIT = 3276800

# Genia: a string of exactly 2**n characters (doubling), for exact-limit programs.
DOUBLING = 'dbl(s, n) =\n  (s, n) ? n == 0 -> s |\n  (s, n) -> dbl(concat(s, s), n - 1)\n'

# Substrings that must never appear anywhere in a failure response (contract 2.2, 6).
HOST_LEAK_MARKERS = (
    "Traceback",
    'File "',
    ".py",
    "hosts/python",
    "hosts.python",
    "src/genia",
    "SyntaxError",
    "RuntimeError",
    "TypeError",
    "ValueError",
    "ZeroDivision",
    "PermissionError",
    "Exception",
    "GeniaFunction",
    "make_global_env",
    "0x",
    "/home/",
    "/tmp/",
    "/proc",
    str(REPO_ROOT),
)


def env_for(mode: str) -> dict:
    """The server environment for a namespace mode (`host` or simulated `denied`)."""
    env = server_env()
    if mode == "denied":
        env["PATH"] = denied_namespace_path(os.environ.get("PATH", ""))
    return env


def launcher_batch(messages, mode="host", timeout=600):
    """Send all `messages` to one launcher session; return (raw stdout, decoded responses)."""
    from tests.fixtures.r28_mcp_helpers import run_launcher_raw

    done = run_launcher_raw([encode(m) for m in messages], timeout=timeout, env=env_for(mode))
    assert done.returncode == 0, done.stderr.decode("utf-8", "replace")
    decoded = []
    for frame in frames(done.stdout):
        assert frame != b"", "empty protocol line on stdout"
        decoded.append(json.loads(frame.decode("utf-8")))
    return done.stdout, decoded


ERAS = ("modern", "compat")  # the two supported MCP protocol eras (amendment A5)
COMPAT_RESULT_KEYS = {"content", "structuredContent", "isError"}


def structured_era(response, era="modern"):
    """(CallToolResult, envelope) after checking the wire shape of the given protocol era."""
    if era == "modern":
        return structured(response)
    assert set(response) == {"jsonrpc", "id", "result"}, response
    result = response["result"]
    assert set(result) == COMPAT_RESULT_KEYS, sorted(result)  # no resultType, ttlMs, cacheScope, _meta
    (item,) = result["content"]
    assert item["type"] == "text" and "\n" not in item["text"]
    assert json.loads(item["text"]) == result["structuredContent"]
    envelope = result["structuredContent"]
    assert result["isError"] is (envelope["status"] == "error")
    return result, envelope


def era_batch(messages, era="modern", mode="host", timeout=600):
    """Send `messages` in one session; the compatibility era completes the handshake first.

    Returns (raw stdout, responses) with the handshake's own response checked and removed.
    """
    if era == "modern":
        return launcher_batch(messages, mode, timeout)
    raw, out = launcher_batch([*compat_handshake(), *messages], mode, timeout)
    assert out[0]["id"] == "init" and "error" not in out[0], out[0]
    assert out[0]["result"]["protocolVersion"] == "2025-11-25"
    return raw, out[1:]


def run_sources(sources, mode="host", timeout=600, era="modern"):
    """`genia_run` each source in one session; return [(raw response, envelope), ...]."""
    build = run_request if era == "modern" else compat_run
    messages = [build(source, index + 1) for index, source in enumerate(sources)]
    _, out = era_batch(messages, era, mode, timeout)
    assert [r["id"] for r in out] == list(range(1, len(sources) + 1))
    return [(r, structured_era(r, era)[1]) for r in out]


def parse_sources(sources, mode="host", timeout=600, era="modern"):
    build = parse_request if era == "modern" else compat_parse
    messages = [build(source, index + 1) for index, source in enumerate(sources)]
    _, out = era_batch(messages, era, mode, timeout)
    assert [r["id"] for r in out] == list(range(1, len(sources) + 1))
    return [(r, structured_era(r, era)[1]) for r in out]


@lru_cache(maxsize=None)
def cached_run(source, mode="host"):
    ((raw, envelope),) = run_sources([source], mode)
    return raw, envelope


# --- the direct-host oracle ----------------------------------------------------------------


def direct_command_source(source):
    """(rendered value, stdout, stderr) of direct command-source evaluation, or raises."""
    import genia
    import genia.interpreter  # noqa: F401 - registers the interpreter runtime
    from genia.utf8 import format_debug

    out, err = io.StringIO(), io.StringIO()
    env = genia.make_global_env(
        cli_args=[],
        stdin_provider=lambda: iter(()),
        stdout_stream=out,
        stderr_stream=err,
        environment_snapshot_provider=dict,
    )
    value = genia.run_source(source, env, filename="<command>")
    return format_debug(value), out.getvalue(), err.getvalue()


# --- shape checks --------------------------------------------------------------------------

ENVELOPE_KEYS = {"schema_version", "status", "result", "error"}
ERROR_KEYS = {"kind", "message", "phase"}
RESULT_KEYS = {"kind", "value", "stdout", "stderr", "exit_code"}
CALL_RESULT_KEYS = {"resultType", "content", "structuredContent", "isError", "_meta"}


def assert_wire_result(response, era="modern"):
    """The CallToolResult wire shape (contract 2.2 / A1, or A5.5 for the compatibility era)."""
    assert set(response) == {"jsonrpc", "id", "result"}
    expected = CALL_RESULT_KEYS if era == "modern" else COMPAT_RESULT_KEYS
    assert set(response["result"]) == expected, sorted(response["result"])
    return structured_era(response, era)[1]


def assert_closed_failure(response, kind, phase, message, era="modern"):
    """A failure is exactly the closed envelope: no result, no partial data, a fixed message."""
    envelope = assert_wire_result(response, era)
    assert set(envelope) == ENVELOPE_KEYS
    assert envelope["schema_version"] == "genia.mcp.v1"
    assert envelope["status"] == "error"
    assert envelope["result"] is None  # no partial stdout/stderr/value/AST
    assert set(envelope["error"]) == ERROR_KEYS
    assert envelope["error"] == {"kind": kind, "phase": phase, "message": message}
    assert response["result"]["isError"] is True
    text = json.dumps(response, ensure_ascii=False)
    for marker in HOST_LEAK_MARKERS:
        assert marker not in text, f"host detail {marker!r} crossed the boundary"
    return envelope


def assert_completed(response, era="modern"):
    envelope = assert_wire_result(response, era)
    assert set(envelope) == ENVELOPE_KEYS
    assert envelope["status"] == "ok" and envelope["error"] is None
    assert set(envelope["result"]) == RESULT_KEYS
    assert set(envelope["result"]["value"]) == {"rendered"}
    assert envelope["result"]["kind"] == "completed" and envelope["result"]["exit_code"] == 0
    assert response["result"]["isError"] is False
    return envelope["result"]


# --- a launcher whose worker is substituted (the supervisor's own seam) -----------------------

_HOST_CODE = "from tests.fixtures.r28_substituted_host import main; raise SystemExit(main())"

SENTINEL = "SENTINEL-ZQ9-7731-PROTECTED"

# The real worker with one extra binding: a protected carrier holding SENTINEL. MCP provisions
# no provider, so this is the only way a carrier can reach a program; it exercises the real
# native server, supervisor, policy, and renderer over a value the contract says must never
# cross (contract 6). Nothing in the production worker is weakened or edited.
PROTECTED_WORKER = f"""
import hosts.python.mcp_worker as worker
from genia.values import GeniaConfigProvider, GeniaSymbol

provider = GeniaConfigProvider(({{"K": "{SENTINEL}"}},))
original = worker.prune_environment


def inject(env):
    original(env)
    env.set("CARRIER", provider.protect("{SENTINEL}", GeniaSymbol("api")))


worker.prune_environment = inject
raise SystemExit(worker.main())
"""

CRASHING_WORKER = """
import sys
sys.stdin.buffer.read()
sys.stderr.buffer.write(b"GENIA-WORKER-READY\\n")
sys.stderr.buffer.flush()
raise RuntimeError("SENTINEL-WORKER-CRASH /home/secret/path")
"""

GARBAGE_WORKER = """
import sys
sys.stdin.buffer.read()
sys.stderr.buffer.write(b"GENIA-WORKER-READY\\n")
sys.stderr.buffer.flush()
sys.stdout.write("Traceback (most recent call last): SENTINEL-GARBAGE\\n")
"""

NONZERO_WORKER = """
import sys
sys.stdin.buffer.read()
sys.stderr.buffer.write(b"GENIA-WORKER-READY\\n")
sys.stderr.buffer.flush()
sys.stdout.write('{"status": "completed", "value": "1", "stdout": "", "stderr": ""}\\n')
sys.stdout.flush()
sys.exit(3)
"""

LEAKY_REPLY_WORKER = """
import sys
sys.stdin.buffer.read()
sys.stderr.buffer.write(b"GENIA-WORKER-READY\\n")
sys.stderr.buffer.flush()
sys.stdout.write('{"status": "runtime_error", "detail": "SENTINEL-DETAIL /home/x"}\\n')
"""


def substituted_session(tmp_path, worker_source, name="worker.py"):
    """A launcher-equivalent session running `worker_source` as the governed worker."""
    from tests.fixtures.r28_mcp_helpers import LauncherSession, SERVER_PATH, repository_revision

    worker = tmp_path / name
    worker.write_text(textwrap.dedent(worker_source), encoding="utf-8")
    return LauncherSession(
        command=[
            sys.executable,
            "-c",
            _HOST_CODE,
            str(SERVER_PATH),
            repository_revision(),
            str(worker),
        ],
        cwd=REPO_ROOT,
        env=server_env(),
    )


def substituted_batch(tmp_path, worker_source, sources, timeout=120):
    """Run `sources` (genia_run) against a substituted worker; return raw frames and envelopes."""
    with substituted_session(tmp_path, worker_source) as session:
        session.wait_ready()
        responses = []
        for index, source in enumerate(sources):
            session.send(run_request(source, index + 1))
            responses.append(session.read(timeout))
        raw = session.raw_stdout
    return raw, responses

