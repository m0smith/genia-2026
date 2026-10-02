"""R28 E28-5 (issue #706): conformance matrix, authority denial, protected values, renderer.

Matrix rows A1-A22, S1-S10, Z1 in docs/mcp/conformance-matrix.md. Python-host security-boundary
tests (policy, restricted runtime, supervisor, wire); they add no Genia semantics and weaken
nothing. The layers are different claims and are asserted separately:

* static policy: the raw parser AST is rejected before anything runs (`policy_denied`);
* unavailable binding: the default-deny pruned environment lacks the name (runtime failure);
* runtime stub: process creation, sockets, and module loading are stubbed in the worker;
* host/OS defense in depth: rlimits and an optional network namespace (cited, not re-proved
  here; the namespace is never the security contract).

Namespace honesty: the wire matrix runs with the host's real namespace behavior and with
`unshare` simulated as denied; the outcome must be identical.
"""

from __future__ import annotations

import importlib
import json

import pytest

from hosts.python.mcp_worker_profile import (
    ALLOWED_AUTOLOADS,
    ALLOWED_BINDINGS,
    DENIED_AUTOLOADS,
    DENIED_BINDINGS,
    DENIED_NAMES,
    policy_violation,
    prune_environment,
)
from tests.fixtures.r28_mcp_conformance import (
    DOUBLING,
    NS_MODES,
    PROTECTED_WORKER,
    SENTINEL,
    assert_closed_failure,
    assert_completed,
    run_sources,
    substituted_session,
)
from tests.fixtures.r28_mcp_helpers import (
    RUN_CANCELLED_MESSAGE,
    RUN_CHANNEL_LIMIT_MESSAGE,
    RUN_POLICY_MESSAGE,
    RUN_RUNTIME_MESSAGE,
    RUN_TIMEOUT_MESSAGE,
    cancel_notification,
    listening_inodes,
    run_request,
    structured,
)

pytestmark = pytest.mark.unit

MARKER = "MARKER_PATH"


def _worker():
    return importlib.import_module("hosts.python.mcp_worker")


def _raw_ast(source):
    from genia.interpreter import Parser, lex

    return Parser(lex(source), source=source, filename="<t>").parse_program()


# --- A: the authority-denial matrix --------------------------------------------------------------
#
# authority -> sources that attempt it. Every source must be valid Genia (so denial is the
# policy's, not the parser's). `MARKER_PATH` is replaced by a path that must stay untouched.

AUTHORITY = {
    "A1-filesystem-read": [
        'read_file("/etc/hostname")',
        '_read_file("/etc/hostname")',
        'zip_read("/tmp/x.zip")',
        '_zip_read("/tmp/x.zip")',
        '_resource_read_text("/etc/hostname")',
        '_resource_read_bytes("/etc/hostname")',
        '_resource_discover("/")',
        "_resource_capabilities",
    ],
    "A2-filesystem-write": [
        'write_file("MARKER_PATH", "x")',
        '_write_file("MARKER_PATH", "x")',
        'zip_write("MARKER_PATH")',
        '_resource_write_text("MARKER_PATH", "x")',
        '_resource_write_bytes("MARKER_PATH", "x")',
        '_resource_copy("a", "MARKER_PATH")',
        '_resource_delete("MARKER_PATH")',
    ],
    "A3-environment": ["config_standard", 'config_get("HOME")', 'config_get_or("PATH", "")', "config_args"],
    "A4-configuration": [
        'config_get("K")',
        "config_provider",
        'config_view(config_provider)',
        "lifecycle_config",
        "config_standard",
    ],
    "A5-secret": ['secret_get("K")', 'secret_get_or("K", 1)', "secret_view"],
    "A6-declassification": ["declassify", "declassify(1, 2)"],
    "A7-network-http": [
        'http_operation("GET", "http://127.0.0.1:1/", "/", {}, {}, "")',
        '_http_send("GET")',
        "import web\n1",
    ],
    "A8-server-listener": ['_serve_http(1)', "_cors", "import server\n1"],
    "A10-shell-stage": ['"x" |> $(touch MARKER_PATH)', '"x" |> $(echo hi)', "$(touch MARKER_PATH)"],
    "A11-external-process": ['_execution_process("echo")', "import execution\n1"],
    "A12-import": ["import web\n1", "import execution\n1", "import file\n1", "import list\n1", "import not_a_module\n1"],
    "A15-stdin-terminal": ['input("prompt")', "stdin_keys"],
    "A17-model-provider": ["model", 'model("p", "m", "x", {})'],
    "A18-retrieval-provider": ["embed", "retrieve", "rerank"],
    "A19-indirection": ["eval(quote(read_file), empty_env())", "eval(quote(declassify), empty_env())"],
    "A20-indirect-spawn": ['spawn(() -> write_file("MARKER_PATH", "x"))'],
}
CASES = [(authority, source) for authority, sources in AUTHORITY.items() for source in sources]
CASE_IDS = [f"{authority}:{source[:28]!r}" for authority, source in CASES]


def _filled(source, tmp_path):
    return source.replace(MARKER, str(tmp_path / "marker"))


@pytest.mark.parametrize("mode", NS_MODES)
def test_static_policy_denies_every_authority_at_the_wire(mode, tmp_path):
    sources = [_filled(source, tmp_path) for _, source in CASES]
    results = run_sources(sources, mode)
    assert not (tmp_path / "marker").exists(), "a prohibited operation had an effect"
    for (authority, source), (response, _) in zip(CASES, results):
        assert_closed_failure(response, "policy_denied", "policy", RUN_POLICY_MESSAGE)
    # denial never echoes source, name, or path
    text = json.dumps([r for r, _ in results])
    for fragment in ("read_file", "/etc/hostname", "secret_get", "MARKER", str(tmp_path)):
        assert fragment not in text


@pytest.mark.parametrize("authority, source", CASES, ids=CASE_IDS)
def test_static_policy_rejects_the_raw_ast_before_any_evaluation(authority, source, tmp_path):
    assert policy_violation(_raw_ast(_filled(source, tmp_path))) is True


@pytest.mark.parametrize("authority, source", CASES, ids=CASE_IDS)
def test_runtime_layer_alone_still_denies_when_policy_is_disabled(authority, source, tmp_path):
    reply = _worker().execute_source(_filled(source, tmp_path), enforce_policy=False)
    # Fails closed: never an effect, no detail. `import` and shell stages are stopped by the
    # runtime stubs; named authority by the pruned environment. An in-language `spawn` runs the
    # attempt asynchronously, so the *spawning* program completes while the attempt itself fails
    # inside the spawned process (the marker proves it had no effect).
    if source.startswith("spawn("):
        assert reply["status"] == "completed"
    else:
        assert set(reply) == {"status"} and reply["status"] in {"runtime_error", "policy_denied"}, reply
    assert not (tmp_path / "marker").exists()


def test_every_denied_binding_and_autoload_is_unavailable_after_pruning():
    import genia
    import genia.interpreter  # noqa: F401

    env = genia.make_global_env(cli_args=[])
    prune_environment(env)
    present = set(env.values) | {name for name, _ in env.root().autoloads}
    assert present <= ALLOWED_BINDINGS | {name for name, _ in ALLOWED_AUTOLOADS}
    assert not (set(DENIED_BINDINGS) & present)
    assert not ({name for name, _ in DENIED_AUTOLOADS} & present)


def test_every_denied_name_is_rejected_statically_and_unbound_at_runtime():
    assert DENIED_NAMES  # the complete default-deny list, not a hand-picked sample
    for name in sorted(DENIED_NAMES):
        assert policy_violation(_raw_ast(name)) is True, name
        reply = _worker().execute_source(name, enforce_policy=False)
        assert reply["status"] in {"runtime_error", "policy_denied"} and set(reply) == {"status"}, name


def test_any_reference_to_a_denied_name_is_rejected_even_for_a_user_definition():
    assert policy_violation(_raw_ast("read_file(x) = x\nread_file(1)")) is True  # conservative
    # A bare definition references nothing and grants nothing, so it is not rejected.
    assert policy_violation(_raw_ast("read_file(x) = x\n1")) is False


@pytest.mark.parametrize(
    "source",
    ["lookup(\"read_file\", empty_env())", "socket", 'connect("127.0.0.1", 1)', "load(\"a\")"],
)
def test_authority_with_no_genia_binding_at_all_is_unavailable_not_stubbed(source):
    # Sockets and `load` have no Genia surface: the program cannot even name them. (The Python
    # socket stub is a runtime backstop under policy and pruning; see
    # test_r28_mcp_run_worker.py::test_runtime_stubs_deny_process_creation_and_sockets_*.)
    ((response, _),) = run_sources([source])
    assert_closed_failure(response, "runtime_error", "execution", RUN_RUNTIME_MESSAGE)


def test_inert_bindings_are_available_but_grant_nothing():
    # A13/A14/A16: `stdin` is an immediate-EOF source and `argv()` is empty: inert, not denied.
    results = run_sources(["stdin |> lines |> collect", "argv()", "[stdin |> lines |> collect, argv()]"])
    assert [assert_completed(r)["value"]["rendered"] for r, _ in results] == ["[]", "[]", "[[], []]"]


def test_annotation_forms_are_inert_and_open_no_listener():
    before = listening_inodes()
    sources = ['@get("/x")\nh() = 1\n7', '@cors("*")\nh() = 1\n7']
    results = run_sources(sources)
    for response, _ in results:  # unbound annotation machinery: fails closed
        assert_closed_failure(response, "runtime_error", "execution", RUN_RUNTIME_MESSAGE)
    assert listening_inodes() <= before  # no listener appeared (matrix A8)


def test_ordinary_genia_concurrency_is_not_host_process_authority():
    # `spawn` is an in-language Process (a worker-local thread); process creation is stubbed.
    ((response, _),) = run_sources(["spawn(() -> 1 + 1) |> process_alive?"])
    assert assert_completed(response)["value"]["rendered"] in {"true", "false"}


def test_authority_outcomes_are_identical_with_the_namespace_granted_or_denied(tmp_path):
    sources = [_filled(source, tmp_path) for _, source in CASES[:12]]
    host = run_sources(sources, "host")
    denied = run_sources(sources, "denied")
    assert [e for _, e in host] == [e for _, e in denied]


# --- S: protected values never cross the boundary ----------------------------------------------
#
# MCP provisions no provider, so a protected carrier can only be reached by host injection.
# `CARRIER` is bound by a test-only worker wrapper (tests/fixtures/r28_mcp_conformance.py) around
# the unmodified production worker; everything else is the real native server and supervisor.

LEAK_FRAGMENTS = ("SENTINEL", "ZQ9", "7731", SENTINEL)

PROTECTED_PROGRAMS = {
    # final rendered value
    "S1-bare-value": "CARRIER",
    "S1-in-list": "[CARRIER]",
    "S1-in-map": "{k: CARRIER}",
    "S1-nested": "[[[{a: some(CARRIER)}]]]",
    "S1-lazy-collect": "[1, 2] |> map((x) -> CARRIER) |> collect",
    "S1-lazy-flow-unforced": "[1] |> map((x) -> CARRIER)",
    "S1-after-output": 'print("before")\nCARRIER',
    # Outcome values
    "S9-some": "some(CARRIER)",
    "S9-err-context": 'err("x", {c: CARRIER})',
    "S9-err-bare": 'err("x", CARRIER)',
    "S9-or-else": 'or_else(none("x"), CARRIER)',
    "S9-unwrap-or": 'unwrap_or(CARRIER, none("x"))',
    # stdout / stderr
    "S2-print": "print(CARRIER)",
    "S2-write": "write(stdout, CARRIER)",
    "S2-print-list": "print([CARRIER])",
    "S2-print-display": "print(display(CARRIER))",
    "S2-print-debug": "print(debug_repr(CARRIER))",
    "S2-log": "log(CARRIER)",
    "S3-stderr": "writeln(stderr, CARRIER)",
    "S3-stderr-display": "writeln(stderr, display(CARRIER))",
    # debug / display rendering
    "S7-display": "display(CARRIER)",
    "S7-debug-repr": "debug_repr(CARRIER)",
    "S7-debug-list": "debug_repr([CARRIER, {k: CARRIER}])",
    "S7-inspect": "inspect(CARRIER)",
    "S7-format": 'format("{}", CARRIER)',
    "S7-string-ops": "[concat(\"a\", CARRIER)]",
    # JSON encoding
    "S8-json-encode": "json_encode(CARRIER)",
    "S8-json-encode-nested": "json_encode({a: [CARRIER]})",
    "S8-json-stringify": "json_stringify({a: CARRIER})",
    "S8-json-pretty": "json_pretty([CARRIER])",
    # exception normalization (error messages, runtime failures)
    "S5-error": "error(CARRIER)",
    "S5-error-concat": 'error("bad " + CARRIER)',
    "S5-type-error": "1 + CARRIER",
    "S5-call": "CARRIER(1)",
    "S5-assert": "assert_eq(CARRIER, 1)",
    "S5-after-touch-div": "x = CARRIER\n1 / 0",
    "S5-after-touch-unbound": "x = CARRIER\nundefined_name_QQ",
    "S5-upper": "upper(CARRIER)",
    # declassification and representation attempts
    "S6-declassify": "declassify(CARRIER, 1)",
    "S6-strip": "strip_representation(CARRIER)",
    "S6-represent": 'represent(CARRIER, "x")',
    # carrier-derived observations that are not the secret
    "S6-equality-oracle": 'CARRIER == "' + SENTINEL + '"',
    "S6-identity": "CARRIER == CARRIER",
    # further observation paths found while auditing (E28-5 skeptical pass)
    "S7-trace": "trace(CARRIER, 1)",
    "S7-tap": "tap(CARRIER, print)",
    "S7-help": "help(CARRIER)",
    "S7-meta": "meta(CARRIER)",
    "S7-map-display": "[CARRIER] |> map(display) |> collect",
    "S8-render-csv": "render_csv([[CARRIER]])",
    "S8-utf8-encode": "utf8_encode(CARRIER)",
    "S9-validate-required": 'validate_required("a", {a: CARRIER})',
    "S9-ref": "ref(CARRIER) |> ref_get",
    "S9-cell": "cell(CARRIER) |> cell_get",
    "S9-process": "spawn(() -> CARRIER) |> process_alive?",
    "S9-actor": "actor(CARRIER, (s, m) -> s)",
    "S2-flow-each-print": "[CARRIER] |> each(print)",
    "S5-assert-true": "assert_true(false, CARRIER)",
    # source echo on every failure class: the sentinel is *in the source text*
    "S4-source-in-parse-error": '"' + SENTINEL + '" +',
    "S4-source-in-policy-denial": 'read_file("' + SENTINEL + '")',
    "S4-source-in-runtime-error": 'undefined_' + "SENTINEL_ZQ9_7731" + "(1)",
    "S4-source-in-value": '"' + SENTINEL + '"',
}


@pytest.fixture(scope="module")
def protected_run(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("protected")
    names = sorted(PROTECTED_PROGRAMS)
    with substituted_session(tmp_path, PROTECTED_WORKER) as session:
        session.wait_ready()
        out = {}
        for index, name in enumerate(names):
            session.send(run_request(PROTECTED_PROGRAMS[name], index + 1))
            out[name] = session.read(120)
        raw = session.raw_stdout
    return raw, out


def test_the_substituted_worker_really_carries_a_protected_value(protected_run):
    # Guard against a vacuous matrix: the carrier exists and is observably protected, and the
    # control programs that merely mention the sentinel as *source text* do round-trip it.
    _, out = protected_run
    assert assert_completed(out["S7-display"])["value"]["rendered"] == '"<protected>"'
    assert assert_completed(out["S6-identity"])["value"]["rendered"] == "true"
    assert_closed_failure(out["S1-bare-value"], "policy_denied", "policy", RUN_POLICY_MESSAGE)
    assert SENTINEL in assert_completed(out["S4-source-in-value"])["value"]["rendered"]  # control


@pytest.mark.parametrize("name", sorted(PROTECTED_PROGRAMS))
def test_no_protected_fragment_appears_anywhere_in_the_response(protected_run, name):
    _, out = protected_run
    text = json.dumps(out[name], ensure_ascii=False)
    if name == "S4-source-in-value":
        # The only program that legitimately returns the sentinel is the one that *wrote* it as an
        # ordinary string in its own source: that is program data, not a protected value.
        assert SENTINEL in text
        return
    for fragment in LEAK_FRAGMENTS:
        assert fragment not in text, f"{fragment!r} crossed the boundary in {name}"


def test_no_protected_fragment_appears_in_the_raw_stdout_bytes_of_the_whole_session(protected_run):
    raw, out = protected_run
    # Only the control program (which wrote the sentinel as an ordinary string in its own source)
    # may carry it; every other response is clean.
    assert raw.count(SENTINEL.encode()) >= 1  # the control is really in the stream
    leaky = {n for n, r in out.items() if SENTINEL in json.dumps(r, ensure_ascii=False)}
    assert leaky == {"S4-source-in-value"}


def test_protected_results_are_fixed_envelopes_with_no_partial_data(protected_run):
    _, out = protected_run
    for name in ("S1-bare-value", "S1-in-list", "S1-in-map", "S1-nested", "S1-lazy-collect", "S9-some",
                 "S9-err-context", "S9-err-bare", "S9-or-else", "S9-unwrap-or", "S1-after-output"):
        assert_closed_failure(out[name], "policy_denied", "policy", RUN_POLICY_MESSAGE)
        assert "before" not in json.dumps(out[name])  # earlier program output dropped too
    for name in ("S2-print", "S2-write", "S2-print-list", "S3-stderr", "S5-error", "S5-error-concat",
                 "S5-call", "S5-assert", "S5-after-touch-div", "S5-after-touch-unbound", "S5-upper",
                 "S2-log", "S7-format", "S7-string-ops", "S6-declassify"):
        status = structured(out[name])[1]["status"]
        assert status == "error", name
    for name in ("S2-print", "S2-write", "S2-print-list", "S3-stderr", "S5-error", "S5-call"):
        assert_closed_failure(out[name], "runtime_error", "execution", RUN_RUNTIME_MESSAGE)
    assert_closed_failure(out["S6-declassify"], "policy_denied", "policy", RUN_POLICY_MESSAGE)


def test_serializers_refuse_a_protected_value_with_a_fixed_outcome(protected_run):
    _, out = protected_run
    for name in ("S8-json-encode", "S8-json-encode-nested", "S8-json-stringify", "S8-json-pretty"):
        rendered = assert_completed(out[name])["value"]["rendered"]
        assert "protected-value" in rendered, name  # the existing R10 refusal Outcome, redacted


def test_declassification_and_representation_attempts_do_not_reveal_anything(protected_run):
    _, out = protected_run
    for name in ("S6-strip", "S6-represent"):
        assert SENTINEL not in json.dumps(out[name])
    # Equality against the literal secret text is not an oracle: carriers compare by identity.
    assert assert_completed(out["S6-equality-oracle"])["value"]["rendered"] == "false"


def test_protected_value_on_the_timeout_path_leaks_nothing(tmp_path):
    with substituted_session(tmp_path, PROTECTED_WORKER) as session:
        session.wait_ready()
        session.send(run_request("x = display(CARRIER)\nloop(n) = loop(n + 1)\nloop(0)", 1))
        response = session.read(60)
        raw = session.raw_stdout
    assert_closed_failure(response, "timeout", "execution", RUN_TIMEOUT_MESSAGE)
    assert not any(f.encode() in raw for f in LEAK_FRAGMENTS)


def test_protected_value_on_the_cancellation_path_leaks_nothing(tmp_path):
    with substituted_session(tmp_path, PROTECTED_WORKER) as session:
        session.wait_ready()
        session.send(run_request("x = display(CARRIER)\nloop(n) = loop(n + 1)\nloop(0)", 1))
        session.send(cancel_notification(1))
        response = session.read(60)
        raw = session.raw_stdout
    assert_closed_failure(response, "cancelled", "execution", RUN_CANCELLED_MESSAGE)
    assert not any(f.encode() in raw for f in LEAK_FRAGMENTS)


def test_protected_value_on_the_result_limit_path_leaks_nothing(tmp_path):
    source = DOUBLING + 'x = display(CARRIER)\nwrite(stdout, concat(dbl("x", 20), "y"))\n1'
    with substituted_session(tmp_path, PROTECTED_WORKER) as session:
        session.wait_ready()
        session.send(run_request(source, 1))
        response = session.read(120)
        raw = session.raw_stdout
    assert_closed_failure(response, "result_limit", "adapter", RUN_CHANNEL_LIMIT_MESSAGE)
    assert not any(f.encode() in raw for f in LEAK_FRAGMENTS)


def test_protected_value_on_the_aggregate_limit_path_leaks_nothing(tmp_path):
    source = (
        DOUBLING + 'x = display(CARRIER)\nwrite(stdout, dbl("\\n", 20))\nwrite(stderr, dbl("\\n", 20))\n1'
    )
    with substituted_session(tmp_path, PROTECTED_WORKER) as session:
        session.wait_ready()
        session.send(run_request(source, 1))
        response = session.read(120)
        raw = session.raw_stdout
    assert structured(response)[1]["error"]["kind"] == "result_limit"
    assert not any(f.encode() in raw for f in LEAK_FRAGMENTS)


def test_protected_value_in_the_worker_build_reply_is_denied_with_no_partial_fields():
    from genia.values import GeniaConfigProvider, GeniaSymbol

    carrier = GeniaConfigProvider(({"K": SENTINEL},)).protect(SENTINEL, GeniaSymbol("api"))
    from genia.values import GeniaMap

    for value in (carrier, [carrier], GeniaMap().put("k", [carrier]), (carrier,)):
        reply = _worker().build_reply(value, "out", "err")
        assert reply == {"status": "policy_denied"}


# --- Z1 (H32): the debug renderer exposes host representations of callable values ---------------


def test_callable_renderings_are_host_representations_and_never_carry_a_protected_value(tmp_path):
    # Ledger R28-H32 evidence. The canonical debug renderer shows Python-level text for callable
    # values. It cannot expose a captured protected value (a closure's environment is not
    # rendered), it does not affect any deterministic corpus row (the corpus excludes callables),
    # and it is exactly what ordinary command-mode evaluation prints.
    programs = {
        "builtin": "print",
        "user-function": "f(x) = x\nf",
        "closure-over-carrier": "(x) -> CARRIER",
        "named-over-carrier": "g() = CARRIER\ng",
        "partial": "add(a, b) = a + b\nadd",
    }
    names = sorted(programs)
    with substituted_session(tmp_path, PROTECTED_WORKER) as session:
        session.wait_ready()
        out = {}
        for index, name in enumerate(names):
            session.send(run_request(programs[name], index + 1))
            out[name] = session.read(60)
        raw = session.raw_stdout
    assert not any(f.encode() in raw for f in LEAK_FRAGMENTS)
    rendered = {name: assert_completed(out[name])["value"]["rendered"] for name in names}
    assert rendered["builtin"].startswith("<function ") and " at 0x" in rendered["builtin"]
    for name in ("user-function", "closure-over-carrier", "named-over-carrier", "partial"):
        assert "Genia" in rendered[name] or rendered[name].startswith("<function")
    assert "<protected>" not in rendered["closure-over-carrier"]
    # `GeniaFunctionGroup(...)` and addresses are host text: pinned as a limitation, not parity.


def test_callable_rendering_is_host_text_and_equals_ordinary_command_mode_shape():
    from tests.fixtures.r28_mcp_conformance import direct_command_source

    ((response, _),) = run_sources(["print"])
    rendered = assert_completed(response)["value"]["rendered"]
    direct = direct_command_source("print")[0]
    # Same shape (address text may differ between processes), same renderer, same host text.
    assert rendered.split(" at 0x")[0] == direct.split(" at 0x")[0]
