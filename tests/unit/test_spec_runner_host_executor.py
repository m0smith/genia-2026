"""
E16-2 (issue #759) generic external-host execution path tests.

Proves that tools/spec_runner/host_executor.py can drive the deterministic
E16-1 fixture adapter (not a Genia host) through the generic protocol and
produce every outcome in the taxonomy, without any fixture/C++-specific
knowledge leaking into the module under test.
"""
from __future__ import annotations

import sys
from pathlib import Path

from tools.spec_runner.host_executor import build_host_request, execute_spec_via_host
from tools.spec_runner.loader import LoadedSpec

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ADAPTER_COMMAND = [sys.executable, "-m", "tools.spec_runner.fixtures.protocol_fixture_adapter"]


def _spec(
    name: str,
    category: str = "eval",
    *,
    source: str = "hello",
    expected_stdout: str | None = None,
    expected_stderr: str | None = None,
    expected_exit_code: int | None = None,
    expected_ir=None,
    expected_parse=None,
    fixtures: tuple[str, ...] = (),
    debug_stdio: bool = False,
    file: str | None = None,
    command: str | None = None,
    test: str | None = None,
    argv: list[str] | None = None,
) -> LoadedSpec:
    return LoadedSpec(
        name=name,
        category=category,
        source=source,
        stdin="",
        expected_stdout=expected_stdout,
        expected_stderr=expected_stderr,
        expected_exit_code=expected_exit_code,
        expected_ir=expected_ir,
        path=Path("spec") / category / f"{name}.yaml",
        file=file,
        command=command,
        test=test,
        argv=argv or [],
        debug_stdio=debug_stdio,
        expected_parse=expected_parse,
        fixtures=fixtures,
    )


# --- build_host_request: category -> operation / input mapping -----------------------------------


def test_build_host_request_maps_ir_category_to_lower_operation() -> None:
    request = build_host_request(_spec("ok", category="ir", source="1 + 1"))
    assert request["operation"] == "lower"
    assert request["input"] == {"source": "1 + 1"}


def test_build_host_request_maps_flow_and_error_categories_to_eval_operation() -> None:
    for category in ("flow", "error", "eval"):
        request = build_host_request(_spec("ok", category=category, source="1 + 1"))
        assert request["operation"] == "eval"
        assert request["input"] == {"source": "1 + 1", "stdin": None, "argv": None}


def test_build_host_request_cli_file_mode_argv() -> None:
    spec = _spec("ok", category="cli", source="path/to/file.genia", file="path/to/file.genia", argv=["x"])
    request = build_host_request(spec)
    assert request["operation"] == "cli"
    assert request["input"] == {"argv": ["path/to/file.genia", "x"], "stdin": None}


def test_build_host_request_cli_command_mode_argv() -> None:
    spec = _spec("ok", category="cli", source="-c form", command="1 + 1")
    request = build_host_request(spec)
    assert request["input"] == {"argv": ["-c", "1 + 1"], "stdin": None}


def test_build_host_request_cli_pipe_mode_argv() -> None:
    spec = LoadedSpec(
        name="ok",
        category="cli",
        source="stdin |> lines |> each(print)",
        stdin="a\nb\n",
        expected_stdout=None,
        expected_stderr=None,
        expected_exit_code=None,
        expected_ir=None,
        path=Path("spec/cli/ok.yaml"),
        command="stdin |> lines |> each(print)",
        argv=[],
    )
    request = build_host_request(spec)
    assert request["input"] == {"argv": ["-p", "stdin |> lines |> each(print)"], "stdin": "a\nb\n"}


def test_build_host_request_returns_none_for_fixture_bearing_case() -> None:
    spec = _spec("ok", fixtures=("r11_model",))
    assert build_host_request(spec) is None


def test_build_host_request_returns_none_for_debug_stdio_case() -> None:
    spec = _spec("ok", category="cli", command="1 + 1", debug_stdio=True)
    assert build_host_request(spec) is None


# --- execute_spec_via_host: full taxonomy through the deterministic fixture adapter ---------------


def test_execute_spec_via_host_pass() -> None:
    spec = _spec("ok", expected_stdout="fixture-stdout:hello\n", expected_stderr="", expected_exit_code=0)
    result = execute_spec_via_host(spec, FIXTURE_ADAPTER_COMMAND, timeout=5.0)
    assert result.kind == "pass"
    assert result.failures == ()


def test_execute_spec_via_host_fail() -> None:
    spec = _spec("ok", expected_stdout="something else entirely\n", expected_stderr="", expected_exit_code=0)
    result = execute_spec_via_host(spec, FIXTURE_ADAPTER_COMMAND, timeout=5.0)
    assert result.kind == "fail"
    assert len(result.failures) == 1
    assert result.failures[0].field == "stdout"


def test_execute_spec_via_host_unsupported_from_adapter() -> None:
    spec = _spec("unsupported")
    result = execute_spec_via_host(spec, FIXTURE_ADAPTER_COMMAND, timeout=5.0)
    assert result.kind == "unsupported"
    assert result.reason == "fixture: operation not supported"


def test_execute_spec_via_host_unsupported_local_capability() -> None:
    spec = _spec("ok", fixtures=("r12_grounded",))
    result = execute_spec_via_host(spec, FIXTURE_ADAPTER_COMMAND, timeout=5.0)
    assert result.kind == "unsupported"
    assert "expressible over the generic" in result.reason


def test_execute_spec_via_host_protocol_error() -> None:
    spec = _spec("stdout-leak")
    result = execute_spec_via_host(spec, FIXTURE_ADAPTER_COMMAND, timeout=5.0)
    assert result.kind == "protocol_error"


def test_execute_spec_via_host_crash() -> None:
    spec = _spec("crash")
    result = execute_spec_via_host(spec, FIXTURE_ADAPTER_COMMAND, timeout=5.0)
    assert result.kind == "crash"


def test_execute_spec_via_host_timeout() -> None:
    spec = _spec("hang")
    result = execute_spec_via_host(spec, FIXTURE_ADAPTER_COMMAND, timeout=0.5)
    assert result.kind == "timeout"


def test_execute_spec_via_host_parse_category_pass() -> None:
    spec = _spec(
        "ok",
        category="parse",
        source="x",
        expected_parse={"kind": "ok", "ast": {"type": "FixtureAst", "source": "x"}},
    )
    result = execute_spec_via_host(spec, FIXTURE_ADAPTER_COMMAND, timeout=5.0)
    assert result.kind == "pass"


def test_execute_spec_via_host_ir_category_pass() -> None:
    spec = _spec(
        "ok",
        category="ir",
        source="x",
        expected_ir={"type": "FixtureIr", "source": "x"},
    )
    result = execute_spec_via_host(spec, FIXTURE_ADAPTER_COMMAND, timeout=5.0)
    assert result.kind == "pass"
