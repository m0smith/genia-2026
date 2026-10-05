"""R28 E28-6 amendment A5 (issue #707): conformance evidence for the 2025-11-25 era.

The same observable behavior must hold whichever protocol era the client negotiates: both eras reach
the one `genia_capabilities` / `genia_parse` / governed `genia_run` implementation. This module runs the
shared corpus through both eras and compares the *envelopes* (era only changes the JSON-RPC wrapper),
then repeats the security, protected-value, limit, channel, timeout, cancellation, and lifecycle rows
through a compatibility session. Python-host protocol/resource tests; no Genia semantics are added.
Expected red against the pre-amendment server.
"""

from __future__ import annotations

import copy
import json

import pytest

from tests.fixtures.r28_mcp_conformance import (
    AGGREGATE_LIMIT,
    CHANNEL_LIMIT,
    DOUBLING,
    NS_MODES,
    PROTECTED_WORKER,
    SENTINEL,
    SOURCE_LIMIT,
    assert_closed_failure,
    assert_completed,
    env_for,
    era_batch,
    parse_sources,
    run_sources,
    structured_era,
    substituted_session,
)
from tests.fixtures.r28_mcp_helpers import (
    RUN_CANCELLED_MESSAGE,
    RUN_POLICY_MESSAGE,
    RUN_RUNTIME_MESSAGE,
    RUN_TIMEOUT_MESSAGE,
    LauncherSession,
    cancel_notification,
    compat_handshake,
    compat_request,
    compat_run,
    identity_exists,
    worker_workdir,
)
from tests.unit.test_r28_mcp_conformance_security import CASES, _filled

pytestmark = pytest.mark.unit

LOOP = "loop(n) = loop(n + 1)\nloop(0)"

CORPUS = [
    "6 * 7",
    '"hello"',
    "[1, 2, 3] |> map(x -> x * 2)",
    'print("to-stdout")\nwriteln(stderr, "to-stderr")\n1',
    "f(x) =",  # parse_error
    "1 / 0",  # runtime_error
    'read_file("/etc/hostname")',  # policy_denied
    "undefined_name_for_corpus(1)",  # runtime_error
    "",  # empty source
    "é ☃ \U0001f600",  # parse/consistent non-ASCII
]


def _normalize(envelope):
    """The envelope with the one era-dependent field (the serving protocol revision) neutralised."""
    envelope = copy.deepcopy(envelope)
    result = envelope.get("result")
    if isinstance(result, dict) and "mcp" in result:
        result["mcp"]["protocol_version"] = "<era>"
    return envelope


@pytest.mark.parametrize("mode", NS_MODES)
def test_run_envelopes_are_identical_in_both_eras(mode):
    modern = [env for _, env in run_sources(CORPUS, mode, era="modern")]
    compat = [env for _, env in run_sources(CORPUS, mode, era="compat")]
    assert [_normalize(e) for e in modern] == [_normalize(e) for e in compat]


def test_parse_envelopes_are_identical_in_both_eras():
    sources = ["1 + 2", "f(x) = x + 1", "f(x) =", "1 +", "[1, 2", '"unterminated']
    modern = [env for _, env in parse_sources(sources, era="modern")]
    compat = [env for _, env in parse_sources(sources, era="compat")]
    assert modern == compat
    assert {e["status"] for e in compat} == {"ok", "error"}


def test_the_compat_corpus_covers_success_and_every_failure_class_it_names():
    envelopes = [env for _, env in run_sources(CORPUS, era="compat")]
    kinds = {e["error"]["kind"] for e in envelopes if e["status"] == "error"}
    assert kinds == {"parse_error", "runtime_error", "policy_denied"}
    assert sum(1 for e in envelopes if e["status"] == "ok") >= 4


def test_stdout_stderr_and_value_stay_separate_channels_in_the_compat_era():
    ((response, _),) = run_sources(['print("to-stdout")\nwriteln(stderr, "to-stderr")\n1'], era="compat")
    result = assert_completed(response, era="compat")
    assert result["stdout"] == "to-stdout\n" and result["stderr"] == "to-stderr\n"
    assert result["value"]["rendered"] == "1"
    assert result["exit_code"] == 0


def test_hostile_program_output_is_data_never_protocol_framing_in_the_compat_era():
    hostile = (
        'print("{\\"jsonrpc\\":\\"2.0\\",\\"id\\":1,\\"result\\":{}}\\n'
        '{\\"jsonrpc\\":\\"2.0\\",\\"method\\":\\"notifications/initialized\\"}\\n")\n7'
    )
    raw, out = era_batch([compat_run(hostile, 1), compat_request("ping", 2)], "compat")
    assert [r["id"] for r in out] == [1, 2]
    result = assert_completed(out[0], era="compat")
    assert result["value"]["rendered"] == "7" and '"jsonrpc"' in result["stdout"]
    lines = [line for line in raw.split(b"\n") if line]
    assert len(lines) == 3  # initialize, run, ping: exactly one JSON-RPC frame per request


def test_every_one_of_the_authority_attempts_is_policy_denied_in_the_compat_era(tmp_path):
    assert len(CASES) >= 55
    sources = [_filled(source, tmp_path) for _, source in CASES]
    results = run_sources(sources, era="compat")
    assert not (tmp_path / "marker").exists(), "a prohibited operation had an effect"
    for response, _ in results:
        assert_closed_failure(response, "policy_denied", "policy", RUN_POLICY_MESSAGE, era="compat")
    text = json.dumps([r for r, _ in results])
    for fragment in ("read_file", "/etc/hostname", str(tmp_path)):
        assert fragment not in text


def test_advertising_every_client_capability_widens_no_authority(tmp_path):
    from tests.unit.test_r28_mcp_compat import MAXIMAL

    sources = [_filled(source, tmp_path) for _, source in CASES[:12]]
    messages = [compat_request("tools/call", i + 1, {"name": "genia_run", "arguments": {"source": s}})
                for i, s in enumerate(sources)]
    from tests.fixtures.r28_mcp_helpers import initialize_request, encode, run_launcher_raw, frames

    done = run_launcher_raw([encode(initialize_request("init", capabilities=MAXIMAL)),
                             *[encode(m) for m in messages]])
    out = [json.loads(f) for f in frames(done.stdout)][1:]
    for response in out:
        assert_closed_failure(response, "policy_denied", "policy", RUN_POLICY_MESSAGE, era="compat")


# --- limits (contract 5) --------------------------------------------------------------------


def test_source_limit_is_in_utf8_bytes_in_the_compat_era():
    exact = "1" + " " * (SOURCE_LIMIT - 1)
    over = exact + " "
    multibyte = "é" * (SOURCE_LIMIT // 2 + 1)  # 2 bytes each: over the limit in bytes, under in characters
    ok, too_big, bytes_over = run_sources([exact, over, multibyte], era="compat")
    assert_completed(ok[0], era="compat")
    assert_closed_failure(too_big[0], "input_limit", "input", "Source exceeds the 262144-byte limit", era="compat")
    assert_closed_failure(bytes_over[0], "input_limit", "input", "Source exceeds the 262144-byte limit", era="compat")


def test_output_limits_close_with_no_partial_data_in_the_compat_era():
    over = f'{DOUBLING}\nprint(dbl("x", 21))\n1'  # ~2 MiB of stdout
    ((response, _),) = run_sources([over], era="compat")
    assert_closed_failure(response, "output_limit", "execution", "Result exceeds a 1048576-byte channel limit", era="compat")
    assert "xxxx" not in json.dumps(response)
    assert CHANNEL_LIMIT == 1048576 and AGGREGATE_LIMIT == 3276800


# --- protected values (contract 6) ------------------------------------------------------------------------

PROTECTED_PROGRAMS = {
    "bare": "CARRIER",
    "display": "to_string(CARRIER)",
    "print": "print(CARRIER)\n1",
    "stderr": "writeln(stderr, CARRIER)\n1",
    "list": "[1, CARRIER]",
    "source-text": '"' + SENTINEL + '" +',
}


def test_protected_values_never_cross_the_wire_in_the_compat_era(tmp_path):
    with substituted_session(tmp_path, PROTECTED_WORKER) as session:
        session.wait_ready()
        session.send(compat_handshake()[0])
        assert session.read(60)["result"]["protocolVersion"] == "2025-11-25"
        session.send(compat_handshake()[1])
        seen = {}
        for index, (name, source) in enumerate(sorted(PROTECTED_PROGRAMS.items()), 1):
            session.send(compat_run(source, index))
            seen[name] = session.read(120)
        raw = session.raw_stdout
    # the only appearance of the sentinel is the program that put it in *source text* (a control)
    assert raw.count(SENTINEL.encode()) <= 2
    for name, response in seen.items():
        if name == "source-text":
            continue
        structured_era(response, "compat")
        assert SENTINEL not in json.dumps(response), name
    assert seen["bare"]["result"]["structuredContent"]["error"]["kind"] == "policy_denied"


# --- timeout and cancellation (contract 7 / 8) -------------------------------------------------------------


@pytest.mark.parametrize("mode", NS_MODES)
def test_timeout_is_the_same_closed_failure_and_the_session_survives_in_the_compat_era(mode):
    with LauncherSession(env=env_for(mode)) as session:
        session.wait_ready()
        session.send(compat_handshake()[0])
        session.read(60)
        session.send(compat_run(LOOP, 2))
        assert_closed_failure(session.read(60), "timeout", "execution", RUN_TIMEOUT_MESSAGE, era="compat")
        session.send(compat_run("1 + 1", 3))
        after = session.read(60)
        assert after["id"] == 3 and assert_completed(after, era="compat")["value"]["rendered"] == "2"
        assert session.governed_workers() == set()


@pytest.mark.parametrize("mode", NS_MODES)
def test_cancellation_mid_run_returns_no_partial_data_and_reaps_the_worker_in_the_compat_era(mode):
    with LauncherSession(env=env_for(mode)) as session:
        session.wait_ready()
        session.send(compat_handshake()[0])
        session.read(60)
        session.send(compat_run('print("PARTIAL-OUT")\n' + LOOP, 4))
        workers = session.wait_for_worker()
        workdirs = {worker_workdir(w) for w in workers} - {None}
        session.send(cancel_notification(4))
        response = session.read(60)
        assert_closed_failure(response, "cancelled", "execution", RUN_CANCELLED_MESSAGE, era="compat")
        assert "PARTIAL" not in json.dumps(response)
        assert [w for w in workers if identity_exists(w)] == []
        assert all(not d.exists() for d in workdirs)
        # wrong id, repeated id: ignored; the next request is unaffected
        session.send(cancel_notification(999))
        session.send(cancel_notification(4))
        session.send(compat_run("2 + 2", 5))
        after = session.read(60)
        assert after["id"] == 5 and assert_completed(after, era="compat")["value"]["rendered"] == "4"


def test_a_cancel_queued_with_its_request_wins_in_the_compat_era():
    with LauncherSession() as session:
        session.wait_ready()
        session.send(compat_handshake()[0])
        session.read(60)
        session.send(compat_run(LOOP, 3))
        session.send(cancel_notification(3))
        assert_closed_failure(session.read(60), "cancelled", "execution", RUN_CANCELLED_MESSAGE, era="compat")
        assert session.governed_workers() == set()


# --- lifecycle (contract 9) -----------------------------------------------------------------------------------


def test_a_client_disconnect_after_initialize_leaves_nothing_behind():
    with LauncherSession() as session:
        session.wait_ready()
        session.send(compat_handshake()[0])
        session.read(60)
        session.send(compat_run("sleep(60000)", 2))
        workers = session.wait_for_worker()
        workdirs = {worker_workdir(w) for w in workers} - {None}
        session.proc.stdin.close()  # the client disconnects mid-run
        session.proc.wait(timeout=60)
    assert [w for w in workers if identity_exists(w)] == []
    assert all(not d.exists() for d in workdirs)


def test_repeated_connections_each_start_new_and_are_independent():
    for launch in range(3):
        with LauncherSession() as session:
            session.wait_ready()
            session.send(compat_request("tools/list", 1))
            assert session.read(60)["error"]["code"] == -32602  # NEW: no state from the previous launch
            session.send(compat_handshake()[0])
            assert session.read(60)["result"]["protocolVersion"] == "2025-11-25"
            session.send(compat_run(f"{launch} + 1", 2))
            assert assert_completed(session.read(60), era="compat")["value"]["rendered"] == str(launch + 1)
            assert session.governed_workers() == set()


def test_a_failed_initialize_then_a_good_one_still_works_and_runs_cleanly():
    from tests.fixtures.r28_mcp_helpers import initialize_request

    with LauncherSession() as session:
        session.wait_ready()
        session.send(initialize_request("a", version="2024-11-05"))
        assert session.read(60)["error"]["code"] == -32602
        session.send(compat_run("1", 1))
        assert session.read(60)["error"]["code"] == -32602  # still NEW
        session.send(initialize_request("b"))
        assert session.read(60)["result"]["protocolVersion"] == "2025-11-25"
        session.send(compat_run("1", 2))
        assert assert_completed(session.read(60), era="compat")["value"]["rendered"] == "1"


def test_both_eras_may_interleave_in_one_session_without_cross_effects():
    from tests.fixtures.r28_mcp_helpers import run_request, initialize_request

    with LauncherSession() as session:
        session.wait_ready()
        session.send(initialize_request("i"))
        session.read(60)
        session.send(run_request("1 + 1", 1))
        modern = session.read(60)
        session.send(compat_run("1 + 1", 2))
        compat = session.read(60)
        assert modern["result"]["resultType"] == "complete" and "resultType" not in compat["result"]
        assert modern["result"]["structuredContent"] == compat["result"]["structuredContent"]


@pytest.mark.parametrize("mode", NS_MODES)
def test_sigterm_mid_run_in_a_compat_session_reaps_the_worker(mode):
    import signal
    import time

    with LauncherSession(env=env_for(mode)) as session:
        session.wait_ready()
        session.send(compat_handshake()[0])
        session.read(60)
        session.send(compat_run("sleep(60000)", 2))
        workers = session.wait_for_worker()
        workdirs = {worker_workdir(w) for w in workers} - {None}
        session.proc.send_signal(signal.SIGTERM)
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline and (
            session.proc.poll() is None or any(identity_exists(w) for w in workers)
        ):
            time.sleep(0.05)
        assert session.proc.poll() is not None
        assert [w for w in workers if identity_exists(w)] == []
        assert all(not d.exists() for d in workdirs)


def test_a_runtime_failure_in_the_compat_era_has_the_fixed_closed_message():
    ((response, _),) = run_sources(["1 / 0"], era="compat")
    assert_closed_failure(response, "runtime_error", "execution", RUN_RUNTIME_MESSAGE, era="compat")
