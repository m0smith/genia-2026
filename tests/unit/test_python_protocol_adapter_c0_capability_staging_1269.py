"""
Slice C / C0 (issue #1269, parent #1250) capability-staging regression tests
for hosts/python/protocol_adapter.py::_VOCABULARY_ONLY_CAPABILITIES.

PYTHON REFERENCE HOST: protocol-adapter capability advertisement only. The
override is empty in production; these tests never stage `default_open_functions`
and make no claim that any default-open behavior is implemented.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

import hosts.python.protocol_adapter as adapter
from hosts.python.protocol_adapter import _python_claimed_capabilities
from tools.spec_runner.capabilities import case_is_applicable, known_capabilities
from tools.spec_runner.host_executor import execute_spec_via_host
from tools.spec_runner.loader import LoadedSpec
from tools.spec_runner.protocol import CAPABILITY_STATUSES

# Capability map advertised by the unmodified adapter on main@6d50a36, captured
# by running `_python_claimed_capabilities()` before the C0 change (not derived
# from the code under test).
PRE_C0_CAPABILITY_MAP = {
    "allowlisted_host_interop": "supported",
    "ast_lowering": "supported",
    "bytes_utf8": "supported",
    "cell_primitives": "supported",
    "cli_command_mode": "supported",
    "cli_file_mode": "supported",
    "cli_pipe_mode": "supported",
    "configuration_dotenv_snapshot": "supported",
    "configuration_environment_snapshot": "supported",
    "core_ir_eval": "supported",
    "debugger_stdio": "supported",
    "doc_help": "supported",
    "embedding_deterministic_fixture": "supported",
    "execution_process": "supported",
    "flow_phase_1": "supported",
    "http_outbound_transport": "supported",
    "http_server": "supported",
    "immutable_bindings": "supported",
    "indexing_deterministic_fixture": "supported",
    "json_compat": "supported",
    "json_strict": "supported",
    "model_deterministic_fixture": "supported",
    "model_gemini_rest": "supported",
    "multi_file_eval": "supported",
    "open_functions": "supported",
    "parser": "supported",
    "prelude_autoload": "supported",
    "process_primitives": "supported",
    "refs": "supported",
    "repl": "supported",
    "reranking_deterministic_fixture": "supported",
    "resource_io": "supported",
    "retrieval_deterministic_fixture": "supported",
    "shared_spec_runner": "partial",
    "shell_stage": "supported",
}


def _gated_spec(*requires: str) -> LoadedSpec:
    """Build an in-memory eval spec with the requested capability requirements.

    The fixture supplies one deterministic expected result for exercising the
    external-host applicability gate without adding a shared-spec YAML file.
    """
    return LoadedSpec(
        name="c0-gated",
        category="eval",
        source="1",
        stdin="",
        expected_stdout="1\n",
        expected_stderr="",
        expected_exit_code=0,
        expected_ir=None,
        path=Path("spec/eval/c0-gated.yaml"),
        requires=tuple(requires),
    )


# --- C0-A: empty override compatibility ----------------------------------------------------------


def test_override_is_empty_and_immutable_in_production() -> None:
    assert adapter._VOCABULARY_ONLY_CAPABILITIES == frozenset()
    assert isinstance(adapter._VOCABULARY_ONLY_CAPABILITIES, frozenset)


def test_empty_override_capability_map_equals_pre_c0_baseline_exactly() -> None:
    assert _python_claimed_capabilities() == PRE_C0_CAPABILITY_MAP


def test_empty_override_keeps_open_functions_and_multi_file_eval_supported() -> None:
    claimed = _python_claimed_capabilities()
    assert claimed["open_functions"] == "supported"
    assert claimed["multi_file_eval"] == "supported"


def test_default_open_functions_is_not_in_the_vocabulary_or_the_override() -> None:
    assert "default_open_functions" not in known_capabilities()
    assert "default_open_functions" not in adapter._VOCABULARY_ONLY_CAPABILITIES
    assert "default_open_functions" not in _python_claimed_capabilities()


# --- C0-B: vocabulary-only staging -----------------------------------------------------------------


def test_staged_known_capability_is_reported_unsupported_and_others_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(adapter, "_VOCABULARY_ONLY_CAPABILITIES", frozenset({"refs"}))
    claimed = _python_claimed_capabilities()
    assert claimed["refs"] == "unsupported"
    expected = dict(PRE_C0_CAPABILITY_MAP, refs="unsupported")
    assert claimed == expected


def test_staging_overrides_the_partial_status_too(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adapter, "_VOCABULARY_ONLY_CAPABILITIES", frozenset({"shared_spec_runner"}))
    assert _python_claimed_capabilities()["shared_spec_runner"] == "unsupported"


def test_staging_an_unknown_name_is_rejected_not_added(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adapter, "_VOCABULARY_ONLY_CAPABILITIES", frozenset({"not-a-real-capability"}))
    with pytest.raises(ValueError, match="not-a-real-capability"):
        _python_claimed_capabilities()


# --- C0-C: external-host gate reports unsupported without invoking the adapter ------------------


def test_staged_capability_case_is_unsupported_without_invoking_the_host(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(adapter, "_VOCABULARY_ONLY_CAPABILITIES", frozenset({"refs"}))
    marker = tmp_path / "host-was-invoked"
    host = tmp_path / "host.py"
    host.write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('invoked')\nraise SystemExit(1)\n",
        encoding="utf-8",
    )

    result = execute_spec_via_host(
        _gated_spec("refs"),
        [sys.executable, str(host)],
        timeout=5.0,
        host_capabilities=_python_claimed_capabilities(),
    )

    # `unsupported` is distinct from a failure/crash/protocol_error/timeout
    # (the host would have produced one of those had it been invoked).
    assert result.kind == "unsupported"
    assert "refs" in result.reason
    assert not marker.exists()


def test_ungated_case_is_not_affected_by_staging(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adapter, "_VOCABULARY_ONLY_CAPABILITIES", frozenset({"refs"}))
    result = execute_spec_via_host(
        _gated_spec(),
        [sys.executable, "-m", "hosts.python.protocol_adapter"],
        timeout=30.0,
        host_capabilities=_python_claimed_capabilities(),
    )
    assert result.kind == "pass"


def test_empty_override_leaves_existing_r20_capability_gating_unchanged() -> None:
    claimed = _python_claimed_capabilities()
    for name in ("open_functions", "multi_file_eval"):
        assert case_is_applicable((name,), claimed) == (True, None)


# --- C0-D: complete vocabulary and permitted statuses ----------------------------------------------


def test_claimed_names_equal_known_vocabulary_with_and_without_staging(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert set(_python_claimed_capabilities()) == known_capabilities()
    monkeypatch.setattr(adapter, "_VOCABULARY_ONLY_CAPABILITIES", frozenset({"refs", "repl"}))
    claimed = _python_claimed_capabilities()
    assert set(claimed) == known_capabilities()
    assert set(claimed.values()) <= CAPABILITY_STATUSES
