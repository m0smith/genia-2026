"""R28 E28-5 (issue #706): conformance matrix, `genia_run` parity, channels, failures, limits.

Matrix rows R1-R9, C1-C9, F1-F8, L1-L9, V1 in docs/mcp/conformance-matrix.md. These are
Python-host tests of the MCP adapter boundary over the launcher; they add no Genia semantics.
The parity oracle is direct command-source evaluation (`tests/fixtures/r28_mcp_conformance.py`,
matrix decision M4), never the CLI `-c` text stream; intentional differences (no `main`
dispatch, denied authority, envelope instead of raw text) are asserted as differences, not
normalized away. Namespace honesty: the whole corpus is run with the host's real namespace
behavior and with `unshare` simulated as denied.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.fixtures.r28_mcp_conformance import (
    AGGREGATE_LIMIT,
    CHANNEL_LIMIT,
    DOUBLING,
    NS_MODES,
    SOURCE_LIMIT,
    assert_closed_failure,
    assert_completed,
    direct_command_source,
    env_for,
    launcher_batch,
    run_sources,
    substituted_batch,
)
from tests.fixtures.r28_mcp_conformance import (
    CRASHING_WORKER,
    GARBAGE_WORKER,
    LEAKY_REPLY_WORKER,
    NONZERO_WORKER,
)
from tests.fixtures.r28_mcp_helpers import (
    GENIA_MAIN,
    REPO_ROOT,
    RUN_CHANNEL_LIMIT_MESSAGE,
    RUN_INTERNAL_MESSAGE,
    RUN_POLICY_MESSAGE,
    RUN_RUNTIME_MESSAGE,
    run_request,
    server_env,
    structured,
)

pytestmark = pytest.mark.unit


# --- V1 / R1-R8: the direct-host versus MCP parity corpus ---------------------------------------
#
# (id, class, source). Exact equality of rendered value, stdout and stderr with direct
# command-source evaluation is required for every row. Rows are deterministic ordinary
# computation: no callable values (ledger R28-H32), no randomness, no timing, no authority.

CORPUS = [
    # R1 literals
    ("int", "literal", "42"),
    ("negative", "literal", "-7"),
    ("decimal", "literal", "3.14"),
    ("string", "literal", '"hello"'),
    ("bool-true", "literal", "true"),
    ("bool-false", "literal", "false"),
    ("none-nil", "literal", 'none("nil")'),
    ("empty-list", "literal", "[]"),
    ("empty-map", "literal", "{}"),
    ("unicode-string", "literal", '"héllo 日本語 😀"'),
    ("escapes", "literal", '"line1\\nline2\\ttab"'),
    # R2 arithmetic and R8 exact numerics
    ("precedence", "arith", "1 + 2 * 3"),
    ("division", "arith", "7 / 2"),
    ("subtract", "arith", "10 - 20"),
    ("rational-sum", "exact", "1/3 + 1/6"),
    ("decimal-sum", "exact", "0.1 + 0.2"),
    ("beyond-r9-safe-integer", "exact", "9007199254740993"),
    ("beyond-r9-sum", "exact", "9007199254740993 + 2"),
    ("huge-integer", "exact", "123456789012345678901234567890"),
    ("huge-product", "exact", "123456789 * 987654321 * 123456789"),
    ("mixed-decimal", "arith", "2 * 3.5"),
    ("mod", "arith", "mod(17, 5)"),
    ("abs-min", "arith", "[abs(-5), min(3, 4)]"),
    ("float64", "exact", "float64(0.1) + float64(0.2)"),
    ("rational-ctor", "exact", "rational(1, 3)"),
    # R3 collections
    ("nested-list", "collection", "[1, [2, [3]]]"),
    ("map", "collection", "{a: 1, b: [1, 2]}"),
    ("map-put", "collection", 'map_put({a: 1}, "b", 2)'),
    ("length", "collection", "length([1, 2, 3])"),
    ("append", "collection", "append([1], [2])"),
    ("unicode-keys", "collection", '{"é": 1, "日本": [1, 2]}'),
    ("first-reverse", "collection", "[first([5, 6]), reverse([1, 2, 3])]"),
    ("string-ops", "collection", '[upper("é"), split("a,b,c", ",")]'),
    # R4 functions
    ("function", "function", "f(x) = x * 2\nf(21)"),
    ("factorial-25", "function", "fact(n) = (n) ? n == 0 -> 1 | (n) -> n * fact(n - 1)\nfact(25)"),
    ("fibonacci", "function", "fib(n) = (n) ? n < 2 -> n | (n) -> fib(n - 1) + fib(n - 2)\nfib(15)"),
    # R5 Outcome values
    ("some", "outcome", "some(1)"),
    ("err", "outcome", 'err("bad", {a: 1})'),
    ("or-else", "outcome", 'or_else(none("x"), 5)'),
    ("unwrap-or", "outcome", 'unwrap_or(5, none("x"))'),
    ("is-some", "outcome", "is_some?(some(1))"),
    (
        "validated-record-ok",
        "outcome",
        'validate_record({name: "a", age: 3}, {name: (r) -> validate_required("name", r), '
        'age: (r) -> validate_field("age", (v) -> v > 0, "positive", r)})',
    ),
    (
        "validated-record-missing-field",
        "outcome",
        'validate_record({name: "a"}, {name: (r) -> validate_required("name", r), '
        'age: (r) -> validate_required("age", r)})',
    ),
    # R6 Flow and pipelines
    ("pipeline-map-filter", "flow", "[1, 2, 3, 4] |> map((x) -> x * x) |> filter((x) -> x > 3)"),
    ("pipeline-sum", "flow", "[1, 2, 3] |> map((x) -> x * 2) |> sum"),
    ("pipeline-range", "flow", "range(1, 6) |> map((x) -> x * 2) |> collect"),
    ("pipeline-take", "flow", "[3, 1, 2] |> map((x) -> x + 1) |> take(2)"),
    ("pipeline-upper", "flow", '"a" |> upper'),
    ("flow-stdin-eof", "flow", "stdin |> lines |> collect"),
    ("flow-each-lazy", "flow", "[1, 2, 3] |> each(print)"),
    # R7 stdout/stderr composition
    ("stdout-lines", "output", 'print("a")\nprint("b")\n7'),
    ("stdout-stderr", "output", 'writeln(stdout, "x")\nwriteln(stderr, "y")\n1'),
    ("argv-empty", "authority-inert", "argv()"),
    # metaprogramming surface that stays available and pure
    ("quote", "meta", "quote(x + 1)"),
    ("eval-pure", "meta", "eval(quote(1 + 2), empty_env())"),
]
CORPUS_SOURCES = [source for _, _, source in CORPUS]
CORPUS_IDS = [name for name, _, _ in CORPUS]


def _mcp_triple(response):
    result = assert_completed(response)
    return result["value"]["rendered"], result["stdout"], result["stderr"]


@pytest.fixture(scope="module", params=NS_MODES)
def corpus_run(request):
    return request.param, run_sources(CORPUS_SOURCES, request.param)


@pytest.mark.parametrize("index", range(len(CORPUS)), ids=CORPUS_IDS)
def test_mcp_equals_direct_command_source_evaluation_exactly(corpus_run, index):
    mode, results = corpus_run
    response, envelope = results[index]
    assert envelope["status"] == "ok", (mode, CORPUS[index][0], envelope)
    assert _mcp_triple(response) == direct_command_source(CORPUS_SOURCES[index])


def test_the_corpus_covers_every_required_semantic_class():
    classes = {kind for _, kind, _ in CORPUS}
    assert {"literal", "arith", "collection", "function", "outcome", "flow", "exact", "output"} <= classes
    assert len(CORPUS) >= 50 and len(set(CORPUS_IDS)) == len(CORPUS_IDS)


def test_corpus_results_are_deterministic_across_calls_and_independent_launches():
    first = run_sources(CORPUS_SOURCES)
    second = run_sources(CORPUS_SOURCES + CORPUS_SOURCES)
    assert [e for _, e in first] == [e for _, e in second[: len(CORPUS)]]
    assert [e for _, e in first] == [e for _, e in second[len(CORPUS):]]  # also within one session


def test_no_state_carries_between_calls_in_one_session():
    sources = ["x = 41", "x", "f(n) = n", "f(1)", 'print("p")', "1"]
    results = run_sources(sources)
    envelopes = [e for _, e in results]
    assert envelopes[1]["status"] == "error" and envelopes[1]["error"]["kind"] == "runtime_error"
    assert envelopes[3]["status"] == "error"
    assert envelopes[5]["result"]["stdout"] == ""  # prior program output did not carry over


# --- intentional differences: policy restriction and entrypoint, never "semantic divergence" ------


def test_denied_authority_is_a_policy_restriction_not_a_semantic_difference(tmp_path):
    readable = tmp_path / "data.txt"
    readable.write_text("DIRECT-ONLY-CONTENT", encoding="utf-8")
    source = f'read_file("{readable}")'
    direct = direct_command_source(source)  # ordinary host execution has the authority
    assert direct[0] == '"DIRECT-ONLY-CONTENT"'
    ((response, envelope),) = run_sources([source])
    assert_closed_failure(response, "policy_denied", "policy", RUN_POLICY_MESSAGE)
    assert "DIRECT-ONLY-CONTENT" not in json.dumps(response)  # the file was never read


def test_main_is_not_dispatched_by_mcp_but_is_by_cli_command_mode():
    # Contract 2.5 versus STATE `-c` mode (ledger R28-H29): a documented adapter difference.
    source = 'main() = print("ran-main")\n7'
    library = direct_command_source(source)
    ((response, _),) = run_sources([source])
    assert _mcp_triple(response) == library == ("7", "", "")
    cli = subprocess.run(
        [sys.executable, "-c", GENIA_MAIN, "-c", source],
        capture_output=True,
        env=server_env(),
        cwd=str(REPO_ROOT),
        stdin=subprocess.DEVNULL,
        timeout=60,
        check=True,
    )
    assert b"ran-main" in cli.stdout  # direct CLI command mode dispatches `main`; MCP does not


# --- C1-C9: value / stdout / stderr / exit code stay separate; output is data ---------------------

JSONRPC_RESPONSE = '{"jsonrpc":"2.0","id":1,"result":{"tools":[]}}'
JSONRPC_REQUEST = '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"genia_run"}}'
CANCEL_LOOKALIKE = '{"jsonrpc":"2.0","method":"notifications/cancelled","params":{"requestId":1}}'


def _lit(text):
    """A Genia string literal for `text` (JSON string escapes are valid Genia escapes here)."""
    return json.dumps(text, ensure_ascii=False)


CHANNEL_CASES = {
    "value-only": ("1 + 1", ("2", "", "")),
    "stdout-only": ('print("only")', None),
    "stderr-only": ('writeln(stderr, "only")', None),
    "value+stdout": ('print("o")\n5', ("5", "o\n", "")),
    "value+stderr": ('writeln(stderr, "e")\n5', ("5", "", "e\n")),
    "all-three": ('print("o")\nwriteln(stderr, "e")\n5', ("5", "o\n", "e\n")),
    "stdout-json": ('print(' + _lit('{"a":[1,2,{"b":null}],"c":"d"}') + ")\n1", None),
    "jsonrpc-response-lookalike-same-id": (f"print({_lit(JSONRPC_RESPONSE)})\n1", None),
    "jsonrpc-request-lookalike": (f"print({_lit(JSONRPC_REQUEST)})\n1", None),
    "cancel-lookalike-on-stdout": (f"print({_lit(CANCEL_LOOKALIKE)})\n1", None),
    "cancel-lookalike-on-stderr": (f"writeln(stderr, {_lit(CANCEL_LOOKALIKE)})\n1", None),
    "method-names": (
        'print("initialize\\nserver/discover\\ntools/list\\nnotifications/cancelled\\n")\n1',
        None,
    ),
    "newline-heavy": ("write(stdout, " + _lit("\n" * 5000) + ")\n1", None),
    "crlf-and-cr": (f"write(stdout, {_lit(chr(13) + chr(10) + chr(13) + 'x' + chr(10))})\n1", None),
    "unicode-separators": (f"write(stdout, {_lit(chr(0x2028) + 'a' + chr(0x2029) + chr(0x85))})\n1", None),
    "control-chars": (f"write(stdout, {_lit(chr(0) + chr(27) + chr(7) + chr(127))})\n1", None),
    "unicode-both-channels": (
        f'write(stdout, {_lit("héllo 日本語 😀 a" + chr(0x301))})\n'
        f'write(stderr, {_lit("ключ 😀 ñ")})\n{_lit("é")}',
        None,
    ),
    "interleaved": ('print("1")\nwriteln(stderr, "2")\nprint("3")\n9', ("9", "1\n3\n", "2\n")),
}
CHANNEL_NAMES = sorted(CHANNEL_CASES)


@pytest.fixture(scope="module", params=NS_MODES)
def channel_run(request):
    sources = [CHANNEL_CASES[name][0] for name in CHANNEL_NAMES]
    messages = [run_request(source, i + 1) for i, source in enumerate(sources)]
    raw, out = launcher_batch(messages, request.param)
    return raw, out


@pytest.mark.parametrize("name", CHANNEL_NAMES)
def test_channels_are_separate_and_match_direct_evaluation(channel_run, name):
    _, out = channel_run
    source, expected = CHANNEL_CASES[name]
    response = out[CHANNEL_NAMES.index(name)]
    assert response["id"] == CHANNEL_NAMES.index(name) + 1
    triple = _mcp_triple(response)
    assert triple == direct_command_source(source)
    if expected is not None:
        assert triple == expected
    assert assert_completed(response)["exit_code"] == 0


def test_program_output_never_becomes_protocol_framing(channel_run):
    raw, out = channel_run
    # Exactly one newline-terminated frame per request, in order, nothing else on stdout.
    assert raw.count(b"\n") == len(CHANNEL_NAMES) == len(out)
    assert raw.endswith(b"\n")
    for index, frame in enumerate(raw[:-1].split(b"\n")):
        decoded = json.loads(frame.decode("utf-8"))
        assert decoded["id"] == index + 1 and decoded["jsonrpc"] == "2.0"
        assert set(decoded) == {"jsonrpc", "id", "result"}  # never a request, never an extra frame
        for control in ("\r", "\x00", "\x1b", "\x07"):
            assert control not in frame.decode("utf-8")  # C0 controls stay JSON-escaped (DEL and U+0085 are legal raw)
        # U+2028, U+2029 and U+0085 are legal raw in JSON strings and are not frame separators:
        # framing is `\n` only (contract 7.1); the official-client scenario proves a client copes.
    # The hostile output is present only as string data inside the matching response.
    hostile = out[CHANNEL_NAMES.index("cancel-lookalike-on-stdout")]
    assert CANCEL_LOOKALIKE in assert_completed(hostile)["stdout"]
    assert assert_completed(hostile)["value"]["rendered"] == "1"  # the run was not cancelled


def test_utf16_surrogate_escapes_are_a_documented_transcoding_limitation():
    # Matrix C10 (KNOWN LIMITATION, ledger R28-H40). Genia `\u` escapes can build strings that
    # hold UTF-16 surrogate code units, which are not Unicode scalar values. Direct evaluation
    # keeps them; the JSON boundary cannot represent a lone surrogate. MCP must fail closed
    # (fixed message, no partial data), and a valid pair becomes the real scalar value.
    pair, lone_value, lone_stdout, lone_stderr = run_sources(
        ['"\\ud83d\\ude00"', '"\\ud800"', 'write(stdout, "\\ud800")\n1', 'write(stderr, "\\udc00x")\n1']
    )
    assert pair[1]["result"]["value"]["rendered"] == '"\U0001f600"'  # merged to one scalar
    assert direct_command_source('"\\ud83d\\ude00"')[0] == '"\ud83d\ude00"'  # direct: two units
    for response, _ in (lone_value, lone_stdout, lone_stderr):
        assert_closed_failure(response, "internal_error", "adapter", RUN_INTERNAL_MESSAGE)


def test_session_stays_usable_after_hostile_output():
    hostile = f"print({_lit(JSONRPC_RESPONSE)})\nprint({_lit(CANCEL_LOOKALIKE)})\n1"
    results = run_sources([hostile, "2 + 2", hostile, "3 + 3"])
    assert [e["result"]["value"]["rendered"] for _, e in results] == ["1", "4", "1", "6"]


# --- F1-F8: every contracted failure class is the closed envelope --------------------------------

PARTIAL = 'print("PARTIAL-STDOUT")\nwriteln(stderr, "PARTIAL-STDERR")\n'

FAILURES = {
    "parse_error": (PARTIAL + "f(x) =", "parse_error", "parse", None),
    "policy_denied-file": (PARTIAL + 'read_file("/etc/hostname")', "policy_denied", "policy", RUN_POLICY_MESSAGE),
    "policy_denied-import": (PARTIAL + "import web\n1", "policy_denied", "policy", RUN_POLICY_MESSAGE),
    "policy_denied-shell": (PARTIAL + '"x" |> $(echo hi)', "policy_denied", "policy", RUN_POLICY_MESSAGE),
    "runtime_error-divide": (PARTIAL + "1 / 0", "runtime_error", "execution", RUN_RUNTIME_MESSAGE),
    "runtime_error-unbound": (PARTIAL + "undefined_SENTINEL_name", "runtime_error", "execution", RUN_RUNTIME_MESSAGE),
    "runtime_error-error": (PARTIAL + 'error("raised SENTINEL")', "runtime_error", "execution", RUN_RUNTIME_MESSAGE),
    "runtime_error-type": (PARTIAL + "1 |> 2", "runtime_error", "execution", RUN_RUNTIME_MESSAGE),
    "result_limit-stdout": (
        DOUBLING + 'print("PARTIAL-STDOUT")\nwriteln(stderr, "PARTIAL-STDERR")\nwrite(stdout, concat(dbl("x", 20), "y"))\n1',
        "result_limit", "adapter", RUN_CHANNEL_LIMIT_MESSAGE),
    "result_limit-value": (
        DOUBLING + PARTIAL + 'dbl("x", 20)', "result_limit", "adapter", RUN_CHANNEL_LIMIT_MESSAGE),
    "input_limit": ("= " * (SOURCE_LIMIT // 2 + 1), "input_limit", "protocol",
                    "Genia source exceeds the 262144-byte limit"),
}


@pytest.fixture(scope="module", params=NS_MODES)
def failure_run(request):
    names = sorted(FAILURES)
    results = run_sources([FAILURES[n][0] for n in names] + ["40 + 2"], request.param)
    return request.param, dict(zip(names, results)), results[-1]


@pytest.mark.parametrize("name", sorted(FAILURES))
def test_every_failure_class_is_the_closed_envelope_with_a_fixed_message(failure_run, name):
    mode, results, _ = failure_run
    _, kind, phase, message = FAILURES[name]
    response, envelope = results[name]
    if message is None:  # parse_error carries only a character offset
        import re

        message = envelope["error"]["message"]
        assert re.fullmatch(r"Genia source failed to parse( at character offset \d+)?", message)
    assert_closed_failure(response, kind, phase, message)
    text = json.dumps(response)
    for partial in ("PARTIAL-STDOUT", "PARTIAL-STDERR", "SENTINEL", "etc/hostname"):
        assert partial not in text, f"{partial!r} leaked in {name} ({mode})"


def test_the_server_keeps_serving_after_every_failure_class(failure_run):
    _, _, last = failure_run
    assert last[1]["result"]["value"]["rendered"] == "42"


@pytest.mark.parametrize(
    "worker, label",
    [
        (CRASHING_WORKER, "worker raised with a path and message"),
        (GARBAGE_WORKER, "worker wrote a traceback instead of a reply"),
        (NONZERO_WORKER, "worker replied then exited nonzero"),
    ],
    ids=["crash", "garbage", "nonzero-exit"],
)
def test_internal_error_is_fixed_and_leaks_nothing_of_the_worker(tmp_path, worker, label):
    raw, (response, after) = substituted_batch(tmp_path, worker, ["1", "2"])
    assert_closed_failure(response, "internal_error", "adapter", RUN_INTERNAL_MESSAGE)
    assert_closed_failure(after, "internal_error", "adapter", RUN_INTERNAL_MESSAGE)  # still serving
    assert b"SENTINEL" not in raw and b"/home/" not in raw


def test_a_reply_with_extra_fields_cannot_smuggle_text_through_the_closed_envelope(tmp_path):
    raw, (response,) = substituted_batch(tmp_path, LEAKY_REPLY_WORKER, ["1"])
    assert_closed_failure(response, "runtime_error", "execution", RUN_RUNTIME_MESSAGE)
    assert b"SENTINEL-DETAIL" not in raw


def test_every_failure_message_is_a_fixed_server_owned_string_within_the_diagnostic_bound():
    fixed = {RUN_POLICY_MESSAGE, RUN_RUNTIME_MESSAGE, RUN_INTERNAL_MESSAGE, RUN_CHANNEL_LIMIT_MESSAGE}
    assert all(len(m.encode("utf-8")) < 200 <= 65536 for m in fixed)  # contract 5: <= 65,536 bytes
    assert all(set(m) <= set(map(chr, range(32, 127))) for m in fixed)  # plain ASCII, no interpolation


# --- L1-L9: limits are UTF-8 byte sizes, enforced at the boundary ---------------------------------


def repeat_expr(char_literal, count):
    """A Genia expression for `count` copies of a one-character string (needs DOUBLING)."""
    if count == 0:
        return '""'
    parts = [f"dbl({char_literal}, {bit})" for bit in range(count.bit_length()) if count >> bit & 1]
    expression = parts[0]
    for part in parts[1:]:
        expression = f"concat({expression}, {part})"
    return expression


def _channel_program(channel, char, count, value="1"):
    return DOUBLING + f"write({channel}, {repeat_expr(_lit(char), count)})\n{value}"


def _value_program(char, count):
    return DOUBLING + repeat_expr(_lit(char), count)


def test_stdout_boundary_in_bytes_ascii_below_exact_above():
    below, exact, above = run_sources(
        [_channel_program("stdout", "x", n) for n in (CHANNEL_LIMIT - 1, CHANNEL_LIMIT, CHANNEL_LIMIT + 1)]
    )
    assert len(below[1]["result"]["stdout"]) == CHANNEL_LIMIT - 1
    assert len(exact[1]["result"]["stdout"]) == CHANNEL_LIMIT
    assert_closed_failure(above[0], "result_limit", "adapter", RUN_CHANNEL_LIMIT_MESSAGE)


def test_stderr_boundary_in_bytes_ascii_below_exact_above():
    below, exact, above = run_sources(
        [_channel_program("stderr", "x", n) for n in (CHANNEL_LIMIT - 1, CHANNEL_LIMIT, CHANNEL_LIMIT + 1)]
    )
    assert len(below[1]["result"]["stderr"]) == CHANNEL_LIMIT - 1
    assert len(exact[1]["result"]["stderr"]) == CHANNEL_LIMIT
    assert_closed_failure(above[0], "result_limit", "adapter", RUN_CHANNEL_LIMIT_MESSAGE)


@pytest.mark.parametrize("channel", ["stdout", "stderr"])
def test_channel_limit_counts_utf8_bytes_not_characters(channel):
    half = CHANNEL_LIMIT // 2  # 524,288 two-byte characters are exactly 1,048,576 bytes
    below, exact, above = run_sources(
        [_channel_program(channel, "é", n) for n in (half - 1, half, half + 1)]
    )
    assert below[1]["status"] == "ok" and exact[1]["status"] == "ok"
    assert len(exact[1]["result"][channel]) == half  # far fewer characters than the byte limit
    assert len(exact[1]["result"][channel].encode("utf-8")) == CHANNEL_LIMIT
    assert_closed_failure(above[0], "result_limit", "adapter", RUN_CHANNEL_LIMIT_MESSAGE)


def test_value_boundary_counts_the_rendered_quotes_in_bytes_ascii():
    # The rendered string carries two quote characters: 1,048,574 characters render to exactly
    # 1,048,576 bytes.
    below, exact, above = run_sources(
        [_value_program("x", n) for n in (CHANNEL_LIMIT - 3, CHANNEL_LIMIT - 2, CHANNEL_LIMIT - 1)]
    )
    assert len(below[1]["result"]["value"]["rendered"]) == CHANNEL_LIMIT - 1
    assert len(exact[1]["result"]["value"]["rendered"]) == CHANNEL_LIMIT
    assert_closed_failure(above[0], "result_limit", "adapter", RUN_CHANNEL_LIMIT_MESSAGE)


def test_value_boundary_counts_utf8_bytes_not_characters():
    # n two-byte characters + two quotes: 524,287 -> exactly 1,048,576 bytes.
    below, exact, above = run_sources(
        [_value_program("é", n) for n in (524286, 524287, 524288)]
    )
    rendered = exact[1]["result"]["value"]["rendered"]
    assert below[1]["status"] == "ok" and len(rendered.encode("utf-8")) == CHANNEL_LIMIT
    assert len(rendered) < CHANNEL_LIMIT // 2 + 3
    assert_closed_failure(above[0], "result_limit", "adapter", RUN_CHANNEL_LIMIT_MESSAGE)


def _source_of_bytes(total):
    """A valid program of exactly `total` UTF-8 bytes made of two-byte characters."""
    assert total >= 4 and total % 2 == 0
    return '"' + "é" * ((total - 2) // 2) + '"'


def test_source_limit_for_run_is_utf8_bytes_one_below_exact_one_above():
    below = _source_of_bytes(SOURCE_LIMIT - 2)
    exact = _source_of_bytes(SOURCE_LIMIT)
    above = '"' + "é" * ((SOURCE_LIMIT - 2) // 2) + 'x"'
    assert [len(s.encode("utf-8")) for s in (below, exact, above)] == [SOURCE_LIMIT - 2, SOURCE_LIMIT, SOURCE_LIMIT + 1]
    assert len(above) < SOURCE_LIMIT  # a character count would have accepted it
    r_below, r_exact, r_above = run_sources([below, exact, above])
    assert r_below[1]["status"] == "ok" and r_exact[1]["status"] == "ok"
    assert_closed_failure(r_above[0], "input_limit", "protocol", "Genia source exceeds the 262144-byte limit")


def _newline_program(stdout_newlines, stderr_newlines, stderr_x=0):
    stderr = repeat_expr('"\\n"', stderr_newlines)
    if stderr_x:
        stderr = f'concat({stderr}, "x")' if stderr_newlines else '"x"'
    return (
        DOUBLING
        + f"write(stdout, {repeat_expr(chr(34) + chr(92) + 'n' + chr(34), stdout_newlines)})\n"
        + f"write(stderr, {stderr})\n1"
    )


def test_aggregate_result_boundary_is_measured_on_the_encoded_envelope_bytes():
    # Calibrate the fixed overhead on this exact program shape, then land the encoded envelope
    # exactly one byte below, exactly on, and one byte above 3,276,800 bytes.
    a = CHANNEL_LIMIT  # stdout: 1,048,576 newlines, each escaped to two bytes
    calibration = run_sources([_newline_program(a, 1000)])[0][0]
    text = calibration["result"]["content"][0]["text"]
    overhead = len(text.encode("utf-8")) - 2 * a - 2 * 1000
    remaining = AGGREGATE_LIMIT - overhead - 2 * a  # bytes still available for stderr
    assert 0 < remaining <= 2 * CHANNEL_LIMIT
    # exact: `remaining` bytes of stderr = remaining//2 newlines (+ one "x" when odd)
    def program(extra):  # extra in {-1, 0, +1} bytes relative to the limit
        want = remaining + extra
        return _newline_program(a, want // 2, want % 2)

    below, exact, above = run_sources([program(-1), program(0), program(1)])
    sizes = [len(r[0]["result"]["content"][0]["text"].encode("utf-8")) for r in (below, exact)]
    assert sizes == [AGGREGATE_LIMIT - 1, AGGREGATE_LIMIT]
    assert below[1]["status"] == "ok" and exact[1]["status"] == "ok"
    assert_closed_failure(above[0], "result_limit", "adapter", "Result exceeds the 3276800-byte limit")


def test_runaway_output_is_stopped_at_the_limit_not_accumulated_until_the_deadline():
    import time

    flood = (
        'rand_flow(1) |> each((x) -> write(stdout, '
        '"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")) |> run'
    )
    started = time.monotonic()
    ((response, _),) = run_sources([flood])
    assert_closed_failure(response, "result_limit", "adapter", RUN_CHANNEL_LIMIT_MESSAGE)
    assert time.monotonic() - started < 4.5  # the limit, not the 5,000 ms deadline, ended it


def test_bounded_stream_never_retains_more_than_its_limit_and_discards_on_overflow():
    from hosts.python.mcp_worker import BoundedStream, ChannelLimitExceeded

    stream = BoundedStream(10_000)
    retained = 0
    with pytest.raises(ChannelLimitExceeded):
        for _ in range(100):
            stream.write("é" * 500)  # 1,000 bytes per write
            retained = max(retained, sum(len(p.encode("utf-8")) for p in stream._parts))
    assert retained <= 10_000  # enforcement happens before the limit is exceeded
    assert stream.overflowed and stream.getvalue() == ""  # partial data dropped immediately


def test_diagnostic_limit_does_not_apply_because_messages_are_fixed():
    # Matrix L6 (NOT APPLICABLE as a boundary): no failure message depends on input, so the
    # 65,536-byte diagnostic bound can never be approached; a huge hostile source yields the
    # same fixed-size message as a tiny one.
    big = "= " + "y" * 200000
    small = "= y"
    (b, _), (s, _) = [r for r in run_sources([big, small])]
    assert b["result"]["structuredContent"]["error"]["phase"] == "parse"
    assert len(json.dumps(b["result"]["structuredContent"]["error"]["message"])) < 100


def test_namespace_mode_does_not_change_limit_behavior():
    sources = [_channel_program("stdout", "x", CHANNEL_LIMIT), _channel_program("stdout", "x", CHANNEL_LIMIT + 1)]
    host = run_sources(sources, "host")
    denied = run_sources(sources, "denied")
    assert [e for _, e in host] == [e for _, e in denied]
    first = env_for("denied")["PATH"].split(os.pathsep)[0]  # the simulation is really in effect
    assert (Path(first) / "unshare").is_file()
    assert structured(host[0][0])[1]["status"] == "ok"
