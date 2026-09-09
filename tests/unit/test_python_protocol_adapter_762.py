"""
E16-5 (issue #762) unit tests for hosts/python/protocol_adapter.py: request
-> LoadedSpec-shape translation, result -> wire-envelope translation, and
the capabilities declaration, all without spawning a subprocess.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from hosts.python.protocol_adapter import (
    _python_claimed_capabilities,
    _result_for_operation,
    _spec_for_operation,
    handle,
)
from tools.spec_runner.capabilities import known_capabilities
from tools.spec_runner.executor import ActualResult
from tools.spec_runner.protocol import build_request, run_adapter_request

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_ADAPTER_COMMAND = [sys.executable, "-m", "hosts.python.protocol_adapter"]


# --- _spec_for_operation: inverse of host_executor.build_host_request -----------------------------


def test_spec_for_operation_parse() -> None:
    spec = _spec_for_operation("parse", {"source": "1 + 1"})
    assert spec.category == "parse"
    assert spec.source == "1 + 1"


def test_spec_for_operation_lower() -> None:
    spec = _spec_for_operation("lower", {"source": "1 + 1"})
    assert spec.category == "ir"
    assert spec.source == "1 + 1"


def test_spec_for_operation_eval() -> None:
    spec = _spec_for_operation("eval", {"source": "1", "stdin": "a\n", "argv": None})
    assert spec.category == "eval"
    assert spec.source == "1"
    assert spec.stdin == "a\n"
    assert spec.fixtures == ()


def test_spec_for_operation_cli_file_mode() -> None:
    spec = _spec_for_operation("cli", {"argv": ["path.genia", "x"], "stdin": None})
    assert spec.file == "path.genia"
    assert spec.argv == ["x"]
    assert spec.command is None
    assert spec.test is None
    assert spec.stdin == ""


def test_spec_for_operation_cli_command_mode() -> None:
    spec = _spec_for_operation("cli", {"argv": ["-c", "1 + 1", "x"], "stdin": None})
    assert spec.command == "1 + 1"
    assert spec.argv == ["x"]
    assert spec.file is None
    assert spec.stdin == ""


def test_spec_for_operation_cli_pipe_mode() -> None:
    spec = _spec_for_operation("cli", {"argv": ["-p", "stdin |> lines"], "stdin": "a\nb\n"})
    assert spec.command == "stdin |> lines"
    assert spec.stdin == "a\nb\n"
    assert spec.argv == []


def test_spec_for_operation_cli_test_mode() -> None:
    spec = _spec_for_operation("cli", {"argv": ["--test", "my-suite"], "stdin": None})
    assert spec.test == "my-suite"
    assert spec.file is None
    assert spec.command is None


# --- _result_for_operation --------------------------------------------------------------------


def test_result_for_operation_parse() -> None:
    actual = ActualResult(parse={"kind": "ok", "ast": {}})
    assert _result_for_operation("parse", actual) == {"kind": "ok", "ast": {}}


def test_result_for_operation_lower() -> None:
    actual = ActualResult(ir={"n": 1})
    assert _result_for_operation("lower", actual) == {"ir": {"n": 1}}


def test_result_for_operation_eval() -> None:
    actual = ActualResult(stdout="1\n", stderr="", exit_code=0)
    assert _result_for_operation("eval", actual) == {"stdout": "1\n", "stderr": "", "exit_code": 0}


# --- capabilities declaration ------------------------------------------------------------------


def test_python_claimed_capabilities_covers_the_full_vocabulary() -> None:
    claimed = _python_claimed_capabilities()
    assert set(claimed) == set(known_capabilities())
    assert claimed["shared_spec_runner"] == "partial"
    assert claimed["parser"] == "supported"


# --- handle(): direct in-process call, no subprocess -----------------------------------------


def test_handle_eval_ok() -> None:
    request = build_request("c1", "eval", {"source": "1 + 1", "stdin": None, "argv": None})
    response = json.loads(handle(request))
    assert response["status"] == "ok"
    assert response["result"]["stdout"] == "2\n"
    assert response["result"]["exit_code"] == 0


def test_handle_parse_ok() -> None:
    request = build_request("c1", "parse", {"source": "1"})
    response = json.loads(handle(request))
    assert response["status"] == "ok"
    assert response["result"]["kind"] == "ok"


# --- end-to-end through the real subprocess -----------------------------------------------------


def test_protocol_adapter_subprocess_eval_round_trip() -> None:
    request = build_request("c1", "eval", {"source": "1 + 1", "stdin": None, "argv": None})
    outcome = run_adapter_request(PROTOCOL_ADAPTER_COMMAND, request, timeout=15.0, cwd=str(REPO_ROOT))
    assert outcome.kind == "ok"
    assert outcome.result == {"stdout": "2\n", "stderr": "", "exit_code": 0}


def test_protocol_adapter_subprocess_evaluated_stdout_isolated_from_transport() -> None:
    """The evaluated program's own print() output must never corrupt the
    adapter's own stdout transport channel -- it must arrive only inside
    result.stdout, and the envelope must still parse as exactly one JSON
    object."""
    request = build_request(
        "c1", "eval", {"source": 'print("not json {{{"); 1', "stdin": None, "argv": None}
    )
    outcome = run_adapter_request(PROTOCOL_ADAPTER_COMMAND, request, timeout=15.0, cwd=str(REPO_ROOT))
    assert outcome.kind == "ok"
    assert outcome.result["stdout"] == "not json {{{\n1\n"


def test_protocol_adapter_subprocess_capabilities() -> None:
    request = build_request("__capabilities__", "capabilities", {})
    outcome = run_adapter_request(PROTOCOL_ADAPTER_COMMAND, request, timeout=15.0, cwd=str(REPO_ROOT))
    assert outcome.kind == "ok"
    assert outcome.result["capabilities"]["parser"] == "supported"
    assert outcome.result["operations"] == ["parse", "lower", "eval", "cli"]
