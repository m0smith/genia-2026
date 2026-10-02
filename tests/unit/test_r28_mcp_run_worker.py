"""R28 E28-3 (issue #704): the disposable worker, policy, and restricted runtime.

Pinned to docs/design/r28-e28-3-genia-run-design.md §4.5 and Clarification A4:
policy inspection runs in the worker over the raw parser AST, and the restricted
Genia environment is a default-deny classification. Expected to fail until E28-3 lands.
"""

from __future__ import annotations

import importlib
import json
import subprocess
import sys

import pytest

from tests.fixtures.r28_mcp_helpers import (
    REPO_ROOT,
    WORKER_PATH,
    WORKER_PROFILE_PATH,
    server_env,
)

pytestmark = pytest.mark.unit


def _worker():
    assert WORKER_PATH.is_file(), "E28-3 not implemented: hosts/python/mcp_worker.py missing"
    return importlib.import_module("hosts.python.mcp_worker")


def _profile():
    assert WORKER_PROFILE_PATH.is_file(), (
        "E28-3 not implemented: hosts/python/mcp_worker_profile.py missing"
    )
    return importlib.import_module("hosts.python.mcp_worker_profile")


def _fresh_env():
    import genia.interpreter  # noqa: F401 - registers the interpreter runtime
    from genia import make_global_env

    return make_global_env(cli_args=[])


# --- reply shapes -------------------------------------------------------------------


def test_completed_reply_has_exactly_value_stdout_stderr():
    reply = _worker().execute_source('print("o")\nwriteln(stderr, "e")\n1 + 2')
    assert reply == {"status": "completed", "value": "3", "stdout": "o\n", "stderr": "e\n"}


def test_parse_error_reply_carries_only_the_offset():
    reply = _worker().execute_source("f(x) = x | SENTINEL =")
    assert set(reply) == {"status", "offset"} and reply["status"] == "parse_error"
    assert isinstance(reply["offset"], int)


def test_runtime_error_reply_has_no_diagnostic_text():
    reply = _worker().execute_source('print("partial")\nundefined_SENTINEL_name')
    assert reply == {"status": "runtime_error"}


def test_main_is_not_dispatched():
    reply = _worker().execute_source('main() = print("ran")\n1')
    assert reply == {"status": "completed", "value": "1", "stdout": "", "stderr": ""}


def test_stdin_is_immediate_eof_and_argv_is_empty():
    reply = _worker().execute_source("[argv(), stdin |> lines |> collect]")
    assert reply["status"] == "completed" and reply["value"] == "[[], []]"


def test_state_does_not_carry_between_calls():
    worker = _worker()
    assert worker.execute_source("x = 1\nx")["status"] == "completed"
    assert worker.execute_source("x") == {"status": "runtime_error"}


# --- layered denial: policy AND restricted runtime ------------------------------------

DENIED = {
    "read_file": 'read_file("/etc/hostname")',
    "write_file": 'write_file("{marker}", "x")',
    "zip_write": 'zip_write("{marker}", [])',
    "resource": '_resource_write_text("{marker}", "x")',
    "http": '_http_send',
    "serve": "_serve_http",
    "config": 'config_get("HOME")',
    "secret": 'secret_get("K")',
    "declassify": "declassify",
    "model": "model",
    "input": 'input("p")',
    "stdin_keys": "stdin_keys",
    "import_web": "import web\n1",
    "import_execution": "import execution\n1",
    "import_file": "import file\n1",
    "shell": '"x" |> $(touch {marker})',
}


@pytest.mark.parametrize("name", sorted(DENIED))
def test_policy_layer_denies_before_anything_runs(name, tmp_path):
    marker = tmp_path / "m"
    reply = _worker().execute_source(DENIED[name].format(marker=marker))
    assert reply == {"status": "policy_denied"}
    assert not marker.exists()


@pytest.mark.parametrize("name", sorted(DENIED))
def test_restricted_runtime_denies_even_with_policy_disabled(name, tmp_path):
    marker = tmp_path / "m"
    reply = _worker().execute_source(
        DENIED[name].format(marker=marker), enforce_policy=False
    )
    # Fails closed: never completed, never an effect, no detail.
    assert reply["status"] in {"runtime_error", "policy_denied"}, reply
    assert set(reply) == {"status"}
    assert not marker.exists()


def test_indirection_cannot_reach_prohibited_authority():
    source = 'f = eval(quote(read_file), empty_env())\nf'
    reply = _worker().execute_source(source, enforce_policy=False)
    assert reply["status"] in {"runtime_error", "policy_denied"}


# --- classification is exhaustive (default deny) ----------------------------------------


def test_every_binding_and_autoload_is_explicitly_classified():
    profile = _profile()
    env = _fresh_env()
    names = set(env.values)
    assert names <= (profile.ALLOWED_BINDINGS | profile.DENIED_BINDINGS), sorted(
        names - profile.ALLOWED_BINDINGS - profile.DENIED_BINDINGS
    )
    autoloads = set(env.root().autoloads)
    assert autoloads <= (profile.ALLOWED_AUTOLOADS | profile.DENIED_AUTOLOADS), sorted(
        autoloads - profile.ALLOWED_AUTOLOADS - profile.DENIED_AUTOLOADS
    )
    assert not (profile.ALLOWED_BINDINGS & profile.DENIED_BINDINGS)
    assert not (profile.ALLOWED_AUTOLOADS & profile.DENIED_AUTOLOADS)


def test_classification_names_exist_today():
    # A stale entry would hide a removed binding; keep the lists honest.
    profile = _profile()
    env = _fresh_env()
    assert profile.DENIED_BINDINGS <= set(env.values)
    assert profile.ALLOWED_BINDINGS <= set(env.values)


def test_pruned_environment_keeps_only_allowed_names():
    profile = _profile()
    env = _fresh_env()
    profile.prune_environment(env)
    assert set(env.values) <= profile.ALLOWED_BINDINGS
    assert set(env.root().autoloads) <= profile.ALLOWED_AUTOLOADS
    for denied in ("read_file", "_read_file", "write_file", "config_get", "secret_get",
                   "_http_send", "_execution_process", "input", "stdin_keys"):
        assert denied not in env.values
    assert ("read_file", 1) not in env.root().autoloads
    # Ordinary pure prelude behavior still works.
    assert env.get("stdout") is not None


def test_authority_bindings_are_classified_as_denied():
    denied = _profile().DENIED_BINDINGS
    for name in ("_read_file", "_write_file", "_http_send", "_serve_http", "_zip_read",
                 "_zip_write", "_resource_read_text", "_resource_write_text",
                 "_execution_process", "config_get", "secret_get", "declassify", "model",
                 "embed", "retrieve", "input", "stdin_keys"):
        assert name in denied, name


# --- policy over the raw AST ---------------------------------------------------------------


def test_policy_inspects_the_raw_ast_not_the_normalized_surface():
    profile = _profile()
    from hosts.python.parse_adapter import parse_and_normalize
    from src.genia.interpreter import Parser, lex

    source = 'read_file("x")'
    # The normalized surface cannot see the callee (ledger R28-H23/H25)...
    assert parse_and_normalize(source)["ast"] == {"kind": "Call"}
    # ...but policy over the raw parser AST can.
    nodes = Parser(lex(source), source=source, filename="<t>").parse_program()
    assert profile.policy_violation(nodes) is True
    ok = Parser(lex("1 + 2"), source="1 + 2", filename="<t>").parse_program()
    assert profile.policy_violation(ok) is False


def test_policy_denies_imports_and_shell_stages_structurally():
    profile = _profile()
    from src.genia.interpreter import Parser, lex

    for source in ("import web\n1", '"x" |> $(echo hi)'):
        nodes = Parser(lex(source), source=source, filename="<t>").parse_program()
        assert profile.policy_violation(nodes) is True, source


# --- result handling inside the worker -----------------------------------------------------


def test_protected_carrier_in_the_result_is_policy_denied_with_no_partial_fields():
    from genia.values import GeniaProtected, GeniaSymbol

    carrier = GeniaProtected("SECRET-VALUE", object(), GeniaSymbol("purpose"))
    reply = _worker().build_reply(carrier, "out", "err")
    assert reply == {"status": "policy_denied"}
    assert "SECRET" not in json.dumps(reply)


def test_channel_overflow_is_result_limit_even_if_the_program_swallows_it():
    big = 'dbl(s, n) =\n  (s, n) ? n == 0 -> s |\n  (s, n) -> dbl(concat(s, s), n - 1)\n'
    source = big + 'write(stdout, concat(dbl("x", 20), "y"))\n1'
    assert _worker().execute_source(source) == {"status": "result_limit"}


def test_rendered_value_over_the_limit_is_result_limit():
    big = 'dbl(s, n) =\n  (s, n) ? n == 0 -> s |\n  (s, n) -> dbl(concat(s, s), n - 1)\n'
    assert _worker().execute_source(big + 'dbl("x", 20)') == {"status": "result_limit"}


def test_reply_is_one_ascii_json_line_from_the_worker_process():
    done = subprocess.run(
        [sys.executable, "-B", "-m", "hosts.python.mcp_worker"],
        input='print("héllo  ")\n"é"'.encode("utf-8"),
        capture_output=True,
        cwd=str(REPO_ROOT),
        env=server_env({"PYTHONPATH": f"{REPO_ROOT}:{REPO_ROOT / 'src'}"}),
        timeout=60,
    )
    assert done.returncode == 0, done.stderr
    line = done.stdout
    assert line.endswith(b"\n") and line.count(b"\n") == 1
    line.decode("ascii")  # escaped, never raw non-ASCII
    reply = json.loads(line)
    assert reply["status"] == "completed" and reply["stdout"].startswith("héllo")


def test_worker_applies_process_limits():
    code = (
        "import resource\n"
        "from hosts.python import mcp_worker as w\n"
        "w.apply_limits()\n"
        "print(resource.getrlimit(resource.RLIMIT_FSIZE)[0], "
        "resource.getrlimit(resource.RLIMIT_CORE)[0], "
        "resource.getrlimit(resource.RLIMIT_AS)[0] > 0)\n"
    )
    done = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env=server_env({"PYTHONPATH": f"{REPO_ROOT}:{REPO_ROOT / 'src'}"}),
        timeout=60,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.split() == ["0", "0", "True"]


def test_runtime_process_creation_is_stubbed_even_without_policy(tmp_path):
    marker = tmp_path / "shell-marker"
    reply = _worker().execute_source(
        f'"x" |> $(touch {marker})', enforce_policy=False
    )
    assert reply["status"] in {"runtime_error", "policy_denied"}
    assert not marker.exists()
