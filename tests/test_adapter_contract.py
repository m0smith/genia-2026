"""
Failing tests for the run_case adapter contract — issue #126.

Target interface (post-implementation):
    run_case(spec: LoadedSpec) -> ActualResult

All tests in this file MUST fail before implementation and pass after.

Failure modes before implementation:
- eval/error tests: AttributeError — hosts.python.adapter.run_eval_subprocess not yet imported
- parse tests: AttributeError — hosts.python.adapter.parse_and_normalize not yet imported
- ir/cli/flow return-type tests: isinstance(result, ActualResult) fails — old code returns dict
- unsupported-category test: passes both before and after (contract already correct)
"""
import pytest
from pathlib import Path
from unittest.mock import patch

from tools.spec_runner.loader import LoadedSpec
from tools.spec_runner.executor import ActualResult
from hosts.python.adapter import run_case


def _spec(category, source="x", **kwargs):
    defaults = dict(
        name="test",
        category=category,
        source=source,
        stdin="",
        expected_stdout=None,
        expected_stderr=None,
        expected_exit_code=None,
        expected_ir=None,
        path=Path("/fake/test.yaml"),
        command=None,
        file=None,
        argv=[],
        debug_stdio=False,
    )
    defaults.update(kwargs)
    return LoadedSpec(**defaults)


# ---------------------------------------------------------------------------
# eval
# ---------------------------------------------------------------------------

def test_run_case_eval_returns_actual_result():
    with patch("hosts.python.adapter.run_eval_subprocess") as m:
        m.return_value = {"stdout": "hello\n", "stderr": "", "exit_code": 0}
        result = run_case(_spec("eval", source="print('hello')"))
    assert isinstance(result, ActualResult)


def test_run_case_eval_fields():
    with patch("hosts.python.adapter.run_eval_subprocess") as m:
        m.return_value = {"stdout": "hello\n", "stderr": "", "exit_code": 0}
        result = run_case(_spec("eval", source="print('hello')"))
    assert result.stdout == "hello\n"
    assert result.stderr == ""
    assert result.exit_code == 0


def test_run_case_eval_no_trailing_newline_strip():
    with patch("hosts.python.adapter.run_eval_subprocess") as m:
        m.return_value = {"stdout": "hello\n", "stderr": "warn\n", "exit_code": 0}
        result = run_case(_spec("eval", source="print('hello')"))
    assert result.stdout == "hello\n", "eval must not strip trailing newlines from stdout"
    assert result.stderr == "warn\n", "eval must not strip trailing newlines from stderr"


# ---------------------------------------------------------------------------
# error (uses eval path)
# ---------------------------------------------------------------------------

def test_run_case_error_returns_actual_result():
    with patch("hosts.python.adapter.run_eval_subprocess") as m:
        m.return_value = {"stdout": "", "stderr": "ZeroDivisionError\n", "exit_code": 1}
        result = run_case(_spec("error", source="1/0"))
    assert isinstance(result, ActualResult)


def test_run_case_error_uses_eval_path_no_strip():
    with patch("hosts.python.adapter.run_eval_subprocess") as m:
        m.return_value = {"stdout": "", "stderr": "err\n", "exit_code": 1}
        result = run_case(_spec("error", source="1/0"))
    assert result.stderr == "err\n", "error must not strip trailing newlines from stderr"
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------

def test_run_case_cli_returns_actual_result():
    with patch("hosts.python.adapter.exec_cli") as m:
        m.return_value = {"stdout": "hello\n", "stderr": "", "exit_code": 0}
        result = run_case(_spec("cli", source="print('hello')", command="print('hello')", stdin="", argv=[]))
    assert isinstance(result, ActualResult)


def test_run_case_cli_strips_trailing_newlines():
    with patch("hosts.python.adapter.exec_cli") as m:
        m.return_value = {"stdout": "hello\n\n", "stderr": "\n", "exit_code": 0}
        result = run_case(_spec("cli", source="print('hello')", command="print('hello')", stdin="", argv=[]))
    assert result.stdout == "hello", "cli must strip trailing newlines from stdout"
    assert result.stderr == "", "cli must strip trailing newlines from stderr"


def test_run_case_cli_crlf_normalized_then_stripped():
    with patch("hosts.python.adapter.exec_cli") as m:
        m.return_value = {"stdout": "hello\r\n", "stderr": "warn\r\n", "exit_code": 0}
        result = run_case(_spec("cli", source="print('hello')", command="print('hello')", stdin="", argv=[]))
    assert result.stdout == "hello", "cli must normalize CRLF then strip trailing newlines"
    assert result.stderr == "warn", "cli must normalize CRLF then strip trailing newlines from stderr"


# ---------------------------------------------------------------------------
# flow
# ---------------------------------------------------------------------------

def test_run_case_flow_returns_actual_result():
    with patch("hosts.python.adapter.exec_flow") as m:
        m.return_value = {"stdout": "line\n", "stderr": "", "exit_code": 0}
        result = run_case(_spec("flow", source="stdin |> lines |> each(print) |> run"))
    assert isinstance(result, ActualResult)


def test_run_case_flow_no_trailing_newline_strip():
    with patch("hosts.python.adapter.exec_flow") as m:
        m.return_value = {"stdout": "line\n", "stderr": "warn\n", "exit_code": 0}
        result = run_case(_spec("flow", source="stdin |> lines |> each(print) |> run"))
    assert result.stdout == "line\n", "flow must not strip trailing newlines from stdout"
    assert result.stderr == "warn\n", "flow must not strip trailing newlines from stderr"
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# ir
# ---------------------------------------------------------------------------

def test_run_case_ir_returns_actual_result():
    ir_val = [{"kind": "Int", "value": 1}]
    with patch("hosts.python.adapter.exec_ir") as m:
        m.return_value = {"ir": ir_val}
        result = run_case(_spec("ir", source="1"))
    assert isinstance(result, ActualResult)


def test_run_case_ir_provides_ir_field():
    ir_val = [{"kind": "Int", "value": 1}]
    with patch("hosts.python.adapter.exec_ir") as m:
        m.return_value = {"ir": ir_val}
        result = run_case(_spec("ir", source="1"))
    assert result.ir == ir_val
    assert result.stdout is None
    assert result.stderr is None


# ---------------------------------------------------------------------------
# parse
# ---------------------------------------------------------------------------

def test_run_case_parse_ok_returns_actual_result():
    parse_val = {"kind": "ok", "ast": {"type": "Int", "value": 1}}
    with patch("hosts.python.adapter.parse_and_normalize") as m:
        m.return_value = parse_val
        result = run_case(_spec("parse", source="1"))
    assert isinstance(result, ActualResult)


def test_run_case_parse_ok_provides_parse_field():
    parse_val = {"kind": "ok", "ast": {"type": "Int", "value": 1}}
    with patch("hosts.python.adapter.parse_and_normalize") as m:
        m.return_value = parse_val
        result = run_case(_spec("parse", source="1"))
    assert result.parse == parse_val
    assert result.stdout is None


def test_run_case_parse_error_provides_parse_field():
    parse_val = {"kind": "error", "type": "ParseError", "message": "unexpected EOF"}
    with patch("hosts.python.adapter.parse_and_normalize") as m:
        m.return_value = parse_val
        result = run_case(_spec("parse", source="("))
    assert isinstance(result, ActualResult)
    assert result.parse["kind"] == "error"
    assert result.parse["type"] == "ParseError"
    assert isinstance(result.parse["message"], str)


# ---------------------------------------------------------------------------
# unsupported category
# ---------------------------------------------------------------------------

def test_run_case_unsupported_category_raises():
    with pytest.raises((ValueError, KeyError, TypeError)):
        run_case(_spec("unknown_category"))


# ---------------------------------------------------------------------------
# adapter must not inspect expected fields
# ---------------------------------------------------------------------------

def test_run_case_does_not_require_expected_fields():
    with patch("hosts.python.adapter.run_eval_subprocess") as m:
        m.return_value = {"stdout": "2\n", "stderr": "", "exit_code": 0}
        result = run_case(_spec("eval", source="1+1"))
    assert result.exit_code == 0
