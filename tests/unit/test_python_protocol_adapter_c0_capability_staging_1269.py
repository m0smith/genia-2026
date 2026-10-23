"""
Slice C / C0 (issue #1269, parent #1250) capability-staging regression tests
for hosts/python/protocol_adapter.py::_VOCABULARY_ONLY_CAPABILITIES.

PYTHON REFERENCE HOST: protocol-adapter capability advertisement only. At the
Slice C RED phase the production override stages exactly `default_open_functions`
as `unsupported`; that makes no claim that any default-open behavior is
implemented. Temporary test staging is the union of the production override and
the staged names (never a replacement), `PRE_C0_CAPABILITY_MAP` stays frozen
history, and the GREEN commit removes the production staging (issue #1269,
package section R6.5).
"""
from __future__ import annotations

import json
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
REPO_ROOT = Path(__file__).resolve().parents[2]

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


# Slice C RED phase (issue #1269): the manifest gains `default_open_functions`
# and the production override stages it, so the advertised map is the frozen
# pre-C0 map plus that one name reported `unsupported`. GREEN adds
# GREEN_CAPABILITY_MAP (the same name `supported`) and PHASE_OVERRIDE becomes
# frozenset(); RED_CAPABILITY_MAP is then retained as history.
RED_CAPABILITY_MAP = {**PRE_C0_CAPABILITY_MAP, "default_open_functions": "unsupported"}
PHASE_OVERRIDE = frozenset({"default_open_functions"})
PHASE_MAP = RED_CAPABILITY_MAP


def _stage(monkeypatch: pytest.MonkeyPatch, *names: str) -> None:
    """Stage names by union with the production override read at test time."""
    monkeypatch.setattr(
        adapter,
        "_VOCABULARY_ONLY_CAPABILITIES",
        adapter._VOCABULARY_ONLY_CAPABILITIES | frozenset(names),
    )


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


def test_override_matches_the_phase_and_is_immutable() -> None:
    assert adapter._VOCABULARY_ONLY_CAPABILITIES == PHASE_OVERRIDE
    assert isinstance(adapter._VOCABULARY_ONLY_CAPABILITIES, frozenset)


def test_phase_capability_map_equals_the_expected_map_and_keeps_history_unchanged() -> None:
    claimed = _python_claimed_capabilities()
    assert claimed == PHASE_MAP
    assert {k: v for k, v in claimed.items() if k != "default_open_functions"} == PRE_C0_CAPABILITY_MAP


def test_empty_override_keeps_open_functions_and_multi_file_eval_supported() -> None:
    claimed = _python_claimed_capabilities()
    assert claimed["open_functions"] == "supported"
    assert claimed["multi_file_eval"] == "supported"


def test_default_open_functions_is_vocabulary_only_and_unsupported_at_red() -> None:
    manifest = json.loads((REPO_ROOT / "spec" / "manifest.json").read_text(encoding="utf-8"))
    assert "default_open_functions" in known_capabilities()
    assert "default_open_functions" in manifest["optional_capabilities"]
    assert "default_open_functions" not in manifest["required_capabilities"]
    assert "default_open_functions" in adapter._VOCABULARY_ONLY_CAPABILITIES
    assert _python_claimed_capabilities()["default_open_functions"] == "unsupported"


# --- C0-B: vocabulary-only staging -----------------------------------------------------------------


def test_staged_known_capability_is_reported_unsupported_and_others_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stage(monkeypatch, "refs")
    claimed = _python_claimed_capabilities()
    assert claimed["refs"] == "unsupported"
    expected = dict(PHASE_MAP, refs="unsupported")
    assert claimed == expected


def test_staging_overrides_the_partial_status_too(monkeypatch: pytest.MonkeyPatch) -> None:
    _stage(monkeypatch, "shared_spec_runner")
    assert _python_claimed_capabilities()["shared_spec_runner"] == "unsupported"


def test_staging_an_unknown_name_is_rejected_not_added(monkeypatch: pytest.MonkeyPatch) -> None:
    _stage(monkeypatch, "not-a-real-capability")
    with pytest.raises(ValueError, match="not-a-real-capability"):
        _python_claimed_capabilities()


# --- C0-C: external-host gate reports unsupported without invoking the adapter ------------------


def test_staged_capability_case_is_unsupported_without_invoking_the_host(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _stage(monkeypatch, "refs")
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


def test_default_open_functions_case_is_unsupported_without_invoking_the_host(tmp_path: Path) -> None:
    marker = tmp_path / "host-was-invoked"
    host = tmp_path / "host.py"
    host.write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('invoked')\nraise SystemExit(1)\n",
        encoding="utf-8",
    )

    result = execute_spec_via_host(
        _gated_spec("default_open_functions"),
        [sys.executable, str(host)],
        timeout=5.0,
        host_capabilities=_python_claimed_capabilities(),
    )

    assert result.kind == "unsupported"
    assert "default_open_functions" in result.reason
    assert not marker.exists()


def test_ungated_case_is_not_affected_by_staging(monkeypatch: pytest.MonkeyPatch) -> None:
    _stage(monkeypatch, "refs")
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
    _stage(monkeypatch, "refs", "repl")
    claimed = _python_claimed_capabilities()
    assert set(claimed) == known_capabilities()
    assert set(claimed.values()) <= CAPABILITY_STATUSES
