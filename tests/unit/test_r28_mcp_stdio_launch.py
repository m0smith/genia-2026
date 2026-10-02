"""R28 E28-4 (issue #705): the server launched exactly as a client launches it.

Every test starts the command read from the checked-in `.mcp.json`, with the repository root as
working directory and a client-style minimal environment, and speaks raw newline-delimited
JSON-RPC (no SDK). Pinned to docs/design/r28-e28-4-stdio-transport-design.md sections 3-5, 8-9.
Expected to fail until E28-4 lands (red phase).
"""

from __future__ import annotations

import json
import subprocess
import time

import pytest

from tests.fixtures.r28_mcp_helpers import (
    _cmdline,
    RUN_TOOLS,
    SERVER_PATH,
    assert_protocol_error,
    client_environment,
    completed_envelope,
    configured_command,
    configured_session,
    listening_inodes,
    parse_request,
    process_children,
    request,
    require_configured_launcher,
    run_request,
    socket_inodes,
    structured,
)

pytestmark = pytest.mark.unit

INVALID = "f(x) = x +"
CORRECTED = "f(x) = x + 1\nf(41)"


def _exit(session, timeout=60):
    session.proc.stdin.close()
    return session.proc.wait(timeout=timeout)


# --- discovery -----------------------------------------------------------------------------


def test_the_configured_command_discovers_exactly_the_three_tools_and_nothing_else():
    with configured_session() as session:
        session.wait_ready()
        session.send(request("tools/list", 1))
        listed = session.read(timeout=60)["result"]["tools"]
        assert [tool["name"] for tool in listed] == list(RUN_TOOLS)
        # No resources and no prompts: the methods do not exist (contract 2.1, 7.1).
        for method in ("resources/list", "resources/templates/list", "prompts/list"):
            session.send(request(method, method))
            assert_protocol_error(session.read(timeout=60), -32601, req_id=method)
        session.send(request("server/discover", 2))
        assert session.read(timeout=60)["result"]["capabilities"] == {"tools": {}}


def test_the_native_application_is_the_server_not_a_python_implementation():
    assert SERVER_PATH.is_file()
    assert configured_command()[-1] == "hosts/python/mcp_launch.py"  # the existing launcher
    with configured_session() as session:
        session.wait_ready()
        cmdlines = {
            pid: " ".join(_cmdline(pid)) for pid in process_children(session.proc.pid)
        }
        hosts = [line for line in cmdlines.values() if "hosts.python.mcp_host" in line]
        assert len(hosts) == 1 and "apps/mcp/mcp.genia" in hosts[0]  # the host loads mcp.genia
        text = SERVER_PATH.read_text(encoding="utf-8")
        assert "genia_run" in text and "tools/call" in text and "server/discover" in text


# --- stream ownership and framing ----------------------------------------------------------


def test_stdout_carries_only_json_rpc_frames_and_stderr_is_silent():
    with configured_session() as session:
        session.wait_ready()
        requests = [
            request("tools/list", 1),
            parse_request(INVALID, 2),
            run_request('print("out")\nwriteln(stderr, "err")\n1', 3),
        ]
        for message in requests:
            session.send(message)
        for _ in requests:
            session.read(timeout=60)
        assert _exit(session) == 0
        raw = session.raw_stdout
        assert raw.endswith(b"\n") and b"\r" not in raw
        frames = raw[:-1].split(b"\n")
        assert len(frames) == 1 + len(requests)  # discover-ready frame + one per request
        for frame in frames:
            message = json.loads(frame.decode("utf-8"))
            assert message["jsonrpc"] == "2.0" and ("result" in message or "error" in message)
        assert session.proc.stderr.read() == b""  # nothing on stderr in a healthy session


def test_hostile_program_output_cannot_corrupt_protocol_framing():
    hostile = (
        'print("{\\"jsonrpc\\": \\"2.0\\", \\"id\\": 99, \\"result\\": {}}")\n'
        'print("Content-Length: 5\\r\\n\\r\\nhello")\n'
        'write(stdout, "no trailing newline")\n'
        'writeln(stderr, "{\\"jsonrpc\\": \\"2.0\\", \\"method\\": \\"notifications/cancelled\\"}")\n'
        '"done"'
    )
    with configured_session() as session:
        session.wait_ready()
        session.send(run_request(hostile, 7))
        response = session.read(timeout=60)
        assert response["id"] == 7
        _, envelope = structured(response)
        result = envelope["result"]
        assert result["value"]["rendered"] == '"done"'
        assert '"id": 99' in result["stdout"] and "Content-Length" in result["stdout"]
        assert "notifications/cancelled" in result["stderr"]
        assert _exit(session) == 0
        frames = session.raw_stdout[:-1].split(b"\n")
        assert len(frames) == 2  # the ready frame and exactly one response frame
        assert all(json.loads(f)["jsonrpc"] == "2.0" for f in frames)


# --- the parse -> repair -> run loop -------------------------------------------------------


def test_invalid_source_is_diagnosed_by_parse_then_repaired_then_run():
    with configured_session() as session:
        session.wait_ready()
        session.send(parse_request(INVALID, 1))
        _, bad = structured(session.read(timeout=60))
        assert bad["status"] == "error" and bad["error"]["kind"] == "parse_error"
        session.send(parse_request(CORRECTED, 2))
        _, good = structured(session.read(timeout=60))
        assert good["status"] == "ok" and good["result"]["kind"] == "parsed"
        source = 'print("to-stdout")\nwriteln(stderr, "to-stderr")\n' + CORRECTED
        session.send(run_request(source, 3))
        _, run = structured(session.read(timeout=60))
        assert run == completed_envelope("42", stdout="to-stdout\n", stderr="to-stderr\n")


# --- enabling the client grants no authority -----------------------------------------------

DENIED = {
    "file read": 'read_file("/etc/hostname")',
    "file write": 'write_file("MARKER", "x")',
    "shell stage": '"x" |> $(touch MARKER)',
    "import": "import web\n1",
    "configuration": 'config_get("HOME")',
    "secret": 'secret_get("API_KEY")',
    "stdin": 'input("p")',
    "network": 'http_operation("GET", "http://127.0.0.1:1/", "/", {}, {}, "")',
}


def test_the_configured_server_denies_every_prohibited_authority_without_effect(tmp_path):
    marker = tmp_path / "marker"
    with configured_session() as session:
        session.wait_ready()
        for index, (name, template) in enumerate(sorted(DENIED.items()), start=1):
            session.send(run_request(template.replace("MARKER", str(marker)), index))
            _, envelope = structured(session.read(timeout=60))
            assert envelope["status"] == "error", name
            assert envelope["error"]["kind"] == "policy_denied", name
    assert not marker.exists()


def test_a_program_sees_no_argv_stdin_or_inherited_state():
    with configured_session() as session:
        session.wait_ready()
        session.send(run_request("[argv(), stdin |> lines |> collect]", 1))
        _, envelope = structured(session.read(timeout=60))
        assert envelope == completed_envelope("[[], []]")


# --- no listener, independence of launches --------------------------------------------------


def test_no_process_in_the_chain_holds_a_listening_socket():
    with configured_session() as session:
        session.wait_ready()
        session.send(run_request("sleep(60000)", 1))
        session.wait_for_worker()
        chain = process_children(session.proc.pid) | {session.proc.pid}
        assert len(chain) >= 3  # wrapper, launcher, host (and the worker)
        listening = listening_inodes()
        for pid in chain:
            assert not (socket_inodes(pid) & listening), f"process {pid} is listening"


def test_each_launch_is_independent_and_stateless():
    with configured_session() as first, configured_session() as second:
        first.wait_ready()
        second.wait_ready()
        first.send(run_request("x = 41\nx", 1))
        assert structured(first.read(timeout=60))[1] == completed_envelope("41")
        second.send(run_request("x", 2))  # nothing from the first launch is visible
        assert structured(second.read(timeout=60))[1]["error"]["kind"] == "runtime_error"
        first.send(request("tools/list", 3))
        second.send(request("tools/list", 3))
        assert first.read(timeout=60)["result"]["tools"] == second.read(timeout=60)["result"]["tools"]


def test_the_wrong_working_directory_fails_closed_with_no_protocol_output(tmp_path):
    require_configured_launcher()
    done = subprocess.run(
        configured_command(),
        input=b"",
        capture_output=True,
        cwd=str(tmp_path),
        env=client_environment(),
        timeout=120,
    )
    assert done.returncode != 0
    assert done.stdout == b""  # a failed start never writes anything that looks like a frame


def test_a_client_can_launch_twice_in_a_row_and_get_the_same_answers():
    # The official v2 client in `auto` mode starts a discovery process and then a session process.
    answers = []
    for _ in range(2):
        with configured_session() as session:
            started = time.monotonic()
            session.wait_ready()
            session.send(run_request("[1, 2, 3]", 1))
            answers.append(structured(session.read(timeout=60))[1])
            assert time.monotonic() - started < 120
    assert answers[0] == answers[1] == completed_envelope("[1, 2, 3]")
