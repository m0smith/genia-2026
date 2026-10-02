"""R28 E28-3 (issue #704): `genia_run` over the native Genia MCP server.

Pinned to docs/design/r28-e28-3-genia-run-design.md and contract §2.5, §4, §5, §6
with Clarification A4 (§17). `genia_run` is provisioned only by the host launcher;
plain CLI mode keeps the E28-1 surface. Expected to fail until the E28-3
implementation lands (failing-test phase).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time

import pytest

from tests.fixtures.r28_mcp_helpers import (
    GENIA_MAIN,
    REPO_ROOT,
    RUN_CANCELLED_MESSAGE,
    RUN_CHANNEL_LIMIT_MESSAGE,
    RUN_INTERNAL_MESSAGE,
    RUN_POLICY_MESSAGE,
    RUN_RUNTIME_MESSAGE,
    RUN_TIMEOUT_MESSAGE,
    RUN_TOOLS,
    UNKNOWN_TOOL_MESSAGE,
    LauncherSession,
    assert_protocol_error,
    call,
    cancel_notification,
    completed_envelope,
    encode,
    error_envelope,
    expected_envelope,
    frames,
    launcher_call,
    parse_request,
    pid_alive,
    repository_revision,
    request,
    responses,
    run_launcher_raw,
    run_request,
    server_env,
    structured,
)

pytestmark = pytest.mark.unit

SOURCE_LIMIT = 262144
CHANNEL_LIMIT = 1048576
RUN_DESCRIPTOR_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["source"],
    "properties": {"source": {"type": "string", "maxLength": SOURCE_LIMIT}},
}
INPUT_LIMIT = error_envelope(
    "input_limit", "protocol", "Genia source exceeds the 262144-byte limit"
)
AGGREGATE_LIMIT = error_envelope(
    "result_limit", "adapter", "Result exceeds the 3276800-byte limit"
)
CHANNEL_LIMIT_ENVELOPE = error_envelope("result_limit", "adapter", RUN_CHANNEL_LIMIT_MESSAGE)
POLICY_DENIED = error_envelope("policy_denied", "policy", RUN_POLICY_MESSAGE)
RUNTIME_ERROR = error_envelope("runtime_error", "execution", RUN_RUNTIME_MESSAGE)
TIMEOUT = error_envelope("timeout", "execution", RUN_TIMEOUT_MESSAGE)
CANCELLED = error_envelope("cancelled", "execution", RUN_CANCELLED_MESSAGE)
INTERNAL = error_envelope("internal_error", "adapter", RUN_INTERNAL_MESSAGE)

# Genia: a string of exactly 2**n characters (doubling), for exact-limit tests.
DOUBLING = 'dbl(s, n) =\n  (s, n) ? n == 0 -> s |\n  (s, n) -> dbl(concat(s, s), n - 1)\n'


def _run(source, req_id=1, **kwargs):
    return structured(launcher_call(run_request(source, req_id), **kwargs))


# --- surface -------------------------------------------------------------------


def test_cli_mode_without_capabilities_does_not_advertise_or_serve_run():
    listed = call(request("tools/list", 1))["result"]["tools"]
    assert [tool["name"] for tool in listed] == ["genia_capabilities"]
    response = call(run_request("1 + 2", 2))
    assert_protocol_error(response, -32602, req_id=2, message=UNKNOWN_TOOL_MESSAGE)


def test_launcher_mode_discovery_is_exactly_the_three_v1_tools_with_closed_schemas():
    listed = launcher_call(request("tools/list", 1))["result"]["tools"]
    assert [tool["name"] for tool in listed] == list(RUN_TOOLS)
    descriptor = listed[2]
    assert set(descriptor) == {"name", "description", "inputSchema"}
    assert isinstance(descriptor["description"], str) and descriptor["description"]
    assert descriptor["inputSchema"] == RUN_DESCRIPTOR_SCHEMA


def test_capabilities_report_exactly_the_advertised_tools():
    response = launcher_call(request("tools/call", 1, {"name": "genia_capabilities"}))
    _, envelope = structured(response)
    assert envelope == expected_envelope(repository_revision(), tools=RUN_TOOLS)


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"source": 1},
        {"source": None},
        {"source": ["1"]},
        {"source": "1", "mode": "file"},
        {"source": "1", "argv": []},
        {"source": "1", "stdin": ""},
        {"source": "1", "timeout_ms": 1},
        {"source": "1", "filename": "x.genia"},
        {"source": "1", "env": {}},
    ],
)
def test_run_is_source_only_and_arguments_are_closed(arguments):
    message = request("tools/call", 3, {"name": "genia_run", "arguments": arguments})
    assert_protocol_error(launcher_call(message), -32602, req_id=3)


# --- completed results: channels and parity -------------------------------------


def test_completed_shape_for_a_pure_expression():
    result, envelope = _run("1 + 2")
    assert result["isError"] is False
    assert envelope == completed_envelope("3")


def test_value_stdout_and_stderr_are_distinct_channels():
    source = 'print("to-out")\nwriteln(stderr, "to-err")\n42'
    _, envelope = _run(source)
    assert envelope == completed_envelope("42", stdout="to-out\n", stderr="to-err\n")


def test_none_nil_is_a_present_rendered_value():
    from genia.utf8 import format_debug

    _, envelope = _run('none("nil")')
    assert envelope["status"] == "ok"
    rendered = envelope["result"]["value"]["rendered"]
    assert isinstance(rendered, str) and rendered != ""
    # The canonical debug renderer, not a new serialization.
    assert rendered == format_debug(_direct_value('none("nil")'))


def _direct_value(source):
    import genia.interpreter  # noqa: F401 - registers the interpreter runtime
    from genia import make_global_env, run_source

    env = make_global_env(cli_args=[])
    return run_source(source, env, filename="<command>")


def _command_mode(source):
    """Direct approved host execution: ordinary `genia -c` (the parity oracle)."""
    done = subprocess.run(
        [sys.executable, "-c", GENIA_MAIN, "-c", source],
        capture_output=True,
        env=server_env(),
        cwd=str(REPO_ROOT),
        stdin=subprocess.DEVNULL,
        timeout=60,
    )
    assert done.returncode == 0, done.stderr
    return done.stdout.decode("utf-8")


PARITY_SOURCES = [
    "1 + 2",
    '"hi"',
    "[1, 2, 3]",
    "{a: 1, b: [1, 2]}",
    "1.5 + 2",
    "[1, 2, 3] |> map((x) -> x * 2)",
    "some(1)",
    'err("bad", {a: 1})',
    "f(x) = x * 2\nf(21)",
    'print("a")\nprint("b")\n7',
    'validate_record({name: "a", age: 3}, {name: (r) -> validate_required("name", r), age: (r) -> validate_field("age", (v) -> v > 0, "positive", r)})',
    'validate_record({name: "a"}, {name: (r) -> validate_required("name", r), age: (r) -> validate_required("age", r)})',
]


@pytest.mark.parametrize("source", PARITY_SOURCES)
def test_run_matches_direct_command_mode_execution(source):
    expected = _command_mode(source)
    _, envelope = _run(source)
    assert envelope["status"] == "ok"
    result = envelope["result"]
    assert result["kind"] == "completed" and result["exit_code"] == 0
    assert result["stderr"] == ""
    # `genia -c` prints program output then the canonical debug rendering of the value.
    assert expected == result["stdout"] + result["value"]["rendered"] + "\n"


def test_validated_pipeline_outcome_is_deterministic_and_structured():
    source = PARITY_SOURCES[-2]
    first = _run(source)[1]
    second = _run(source)[1]
    assert first == second
    assert first["status"] == "ok" and "name" in first["result"]["value"]["rendered"]


def test_command_source_semantics_do_not_dispatch_main():
    # Contract §2.5: no implicit entrypoint (ledger R28-H29; STATE's -c mode differs).
    _, envelope = _run('main() = print("ran")\n1')
    assert envelope == completed_envelope("1")


# --- framing isolation ------------------------------------------------------------


def test_program_output_cannot_corrupt_protocol_framing():
    hostile = 'print("a")\nprint("}{\\"jsonrpc\\": \\"2.0\\", \\"id\\": 99}")\nprint("b\\u2028c")\n1'
    out = run_launcher_raw([encode(run_request(hostile, 1)), encode(request("tools/list", 2))])
    lines = frames(out.stdout)
    assert len(lines) == 2  # exactly one frame per request
    decoded = [json.loads(line) for line in lines]
    assert [d["id"] for d in decoded] == [1, 2]
    envelope = decoded[0]["result"]["structuredContent"]
    assert envelope["status"] == "ok"
    assert '{"jsonrpc"' in envelope["result"]["stdout"]  # data, not a frame


# --- fresh worker ------------------------------------------------------------------


def test_each_call_starts_from_a_fresh_runtime():
    messages = [run_request("x = 41\nx", 1), run_request("x", 2), run_request("x = 41\nx", 3)]
    out = responses(run_launcher_raw([encode(m) for m in messages]))
    envelopes = [structured(o)[1] for o in out]
    assert envelopes[0] == completed_envelope("41")
    assert envelopes[1] == RUNTIME_ERROR  # nothing carried over from call 1
    assert envelopes[2] == envelopes[0]


def test_run_is_deterministic_and_stateless_across_identical_calls():
    out = responses(run_launcher_raw([encode(run_request("[1, 2, 3]", i)) for i in (1, 2)]))
    assert out[0]["result"] == out[1]["result"]


# --- policy: prohibited authority is denied -----------------------------------------

MARKER = "MARKER_PATH"
DENIED_SOURCES = {
    "file read": 'read_file("/etc/hostname")',
    "file write": 'write_file("MARKER_PATH", "x")',
    "zip": 'zip_read("/tmp/x.zip")',
    "resource": '_resource_read_text("/etc/hostname")',
    "import web": "import web\n1",
    "import execution": "import execution\n1",
    "import file": "import file\n1",
    "import any module": "import list\n1",
    "shell stage": '"x" |> $(echo hi)',
    "shell stage side effect": '"x" |> $(touch MARKER_PATH)',
    "configuration": 'config_get("HOME")',
    "secret": 'secret_get("API_KEY")',
    "declassification": "declassify",
    "model": "model",
    "http": 'http_operation("GET", "http://127.0.0.1:1/", "/", {}, {}, "")',
    "input": 'input("prompt")',
    "terminal keys": "stdin_keys",
}


def _fill_marker(source, marker):
    return source.replace(MARKER, str(marker))


@pytest.mark.parametrize("name", sorted(DENIED_SOURCES))
def test_prohibited_authority_is_policy_denied_without_effect(name, tmp_path):
    marker = tmp_path / "marker"
    source = _fill_marker(DENIED_SOURCES[name], marker)
    # The source must be valid Genia: denial must come from policy, not parsing.
    parsed = launcher_call(parse_request(source, 1))
    assert structured(parsed)[1]["status"] == "ok", name
    result, envelope = _run(source)
    assert envelope == POLICY_DENIED, name
    assert result["isError"] is True
    assert not marker.exists(), "prohibited operation had an effect"


def test_denial_leaks_neither_source_nor_authority_detail():
    result, envelope = _run('read_file("/etc/SENTINEL-SECRET-PATH")')
    text = json.dumps(result)
    assert "SENTINEL-SECRET-PATH" not in text and "read_file" not in text


def test_ordinary_computation_with_pure_prelude_is_allowed():
    _, envelope = _run('upper("abc")')
    assert envelope == completed_envelope('"ABC"')


# --- failures: fixed messages, no partial data --------------------------------------


def test_runtime_error_is_normalized_without_source_or_diagnostic_text():
    result, envelope = _run('print("partial")\nundefined_SENTINEL_name + 1')
    assert envelope == RUNTIME_ERROR
    text = json.dumps(result)
    assert "SENTINEL" not in text and "partial" not in text  # no partial stdout either


def test_parse_error_carries_only_an_offset():
    result, envelope = _run("f(x) = x | SENTINEL_TOKEN_QQQ =")
    assert envelope["status"] == "error"
    assert envelope["error"]["kind"] == "parse_error" and envelope["error"]["phase"] == "parse"
    assert re.fullmatch(
        r"Genia source failed to parse( at character offset \d+)?",
        envelope["error"]["message"],
    )
    assert "SENTINEL" not in json.dumps(result)


# --- limits -------------------------------------------------------------------------


def test_source_over_the_limit_is_input_limit_and_never_reaches_a_worker():
    source = "= " * (SOURCE_LIMIT // 2 + 1)
    assert len(source.encode()) == SOURCE_LIMIT + 2
    _, envelope = _run(source)
    assert envelope == INPUT_LIMIT


def test_source_at_the_limit_runs():
    source = "1 " + " " * (SOURCE_LIMIT - 2)
    assert len(source.encode()) == SOURCE_LIMIT
    _, envelope = _run(source)
    assert envelope == completed_envelope("1")


def test_stdout_at_the_limit_succeeds_and_one_byte_over_is_result_limit():
    ok = DOUBLING + 'write(stdout, dbl("x", 20))\n1'
    over = DOUBLING + 'write(stdout, concat(dbl("x", 20), "y"))\n1'
    out = responses(run_launcher_raw([encode(run_request(ok, 1)), encode(run_request(over, 2))], timeout=300))
    first, second = (structured(o)[1] for o in out)
    assert first["status"] == "ok" and len(first["result"]["stdout"]) == CHANNEL_LIMIT
    assert second == CHANNEL_LIMIT_ENVELOPE


def test_stderr_over_the_limit_is_result_limit_with_no_partial_data():
    over = DOUBLING + 'write(stderr, concat(dbl("x", 20), "y"))\nwrite(stdout, "partial")\n1'
    result, envelope = _run(over, timeout=300)
    assert envelope == CHANNEL_LIMIT_ENVELOPE
    assert "partial" not in json.dumps(result)


def test_value_over_the_limit_is_result_limit():
    over = DOUBLING + 'dbl("x", 20)'  # rendered with quotes: 2**20 + 2 bytes
    _, envelope = _run(over, timeout=300)
    assert envelope == CHANNEL_LIMIT_ENVELOPE


def test_combined_channels_over_the_aggregate_limit_are_result_limit():
    # Each channel is exactly at its own limit but the encoded envelope exceeds 3,276,800.
    source = DOUBLING + 'write(stdout, dbl("\\n", 20))\nwrite(stderr, dbl("\\n", 20))\n1'
    _, envelope = _run(source, timeout=300)
    assert envelope == AGGREGATE_LIMIT


# --- deadline -----------------------------------------------------------------------

LOOP = "loop(n) = loop(n + 1)\nloop(0)"


@pytest.mark.parametrize(
    "source",
    [LOOP, "sleep(60000)"],
    ids=["busy-loop", "sleep"],
)
def test_deadline_returns_timeout_and_reaps_the_worker(source):
    with LauncherSession() as session:
        started = time.monotonic()
        session.send(run_request(source, 1))
        time.sleep(1.0)
        workers = session.workers()
        assert workers, "no worker process observed during the call"
        response = session.read(timeout=30)
        elapsed = time.monotonic() - started
        _, envelope = structured(response)
        assert envelope == TIMEOUT
        assert 4.5 <= elapsed <= 10, elapsed
        assert not any(pid_alive(pid) for pid in workers), "worker survived the deadline"


# --- cancellation -------------------------------------------------------------------


def test_cancel_queued_with_the_request_cancels_and_reaps():
    with LauncherSession() as session:
        session.send(run_request(LOOP, 7))
        session.send(cancel_notification(7))
        started = time.monotonic()
        response = session.read(timeout=30)
        assert response["id"] == 7
        assert structured(response)[1] == CANCELLED
        assert time.monotonic() - started < 4.5  # well before the 5000 ms deadline
        time.sleep(0.5)
        assert session.workers() == set()
        # The server is still alive and answers the next request.
        session.send(run_request("1 + 1", 8))
        assert structured(session.read())[1] == completed_envelope("2")


def test_cancel_arriving_mid_run_cancels_and_reaps():
    with LauncherSession() as session:
        session.send(run_request(LOOP, 11))
        time.sleep(1.0)
        workers = session.workers()
        assert workers
        started = time.monotonic()
        session.send(cancel_notification(11))
        response = session.read(timeout=30)
        assert structured(response)[1] == CANCELLED
        assert time.monotonic() - started < 3
        assert not any(pid_alive(pid) for pid in workers)


def test_cancel_for_another_request_id_is_ignored():
    with LauncherSession() as session:
        session.send(run_request("sleep(1500)\n5", 21))
        session.send(cancel_notification(999))
        assert structured(session.read(timeout=30))[1] == completed_envelope("5")


def test_cancel_after_completion_is_ignored_and_the_server_continues():
    with LauncherSession() as session:
        session.send(run_request("1", 31))
        assert structured(session.read())[1] == completed_envelope("1")
        session.send(cancel_notification(31))
        session.send(run_request("2", 32))
        response = session.read()
        assert response["id"] == 32 and structured(response)[1] == completed_envelope("2")


def test_other_requests_during_a_run_are_answered_in_order_after_it():
    with LauncherSession() as session:
        session.send(run_request(LOOP, 41))
        session.send(request("tools/list", 42))
        time.sleep(0.5)
        session.send(cancel_notification(41))
        first = session.read(timeout=30)
        second = session.read(timeout=30)
        assert [first["id"], second["id"]] == [41, 42]
        assert structured(first)[1] == CANCELLED
        assert [t["name"] for t in second["result"]["tools"]] == list(RUN_TOOLS)


def test_cancelled_envelope_carries_no_partial_data():
    with LauncherSession() as session:
        session.send(run_request('print("partial-out")\n' + LOOP, 51))
        time.sleep(1.0)
        session.send(cancel_notification(51))
        result = session.read(timeout=30)
        assert "partial-out" not in json.dumps(result)
        assert structured(result)[1] == CANCELLED


# --- the launcher is still the only host entry --------------------------------------


def test_run_source_with_malformed_json_is_still_a_protocol_parse_error():
    # Clarification A2 is unchanged by E28-3.
    out = run_launcher_raw([b'{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"genia_run","arguments":{"source":"\\ud800"}}}'])
    (frame,) = frames(out.stdout)
    decoded = json.loads(frame)
    assert decoded["error"]["code"] == -32700 and "id" not in decoded
