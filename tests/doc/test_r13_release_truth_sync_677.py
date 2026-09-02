from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "docs/releases/R13.md"


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _run_genia(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(Path(sys.executable).with_name("genia")), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_r13_status_remains_synchronized_after_release_truth_sync() -> None:
    required = {
        "AGENTS.md": "E13-7 release-example truth synchronization",
        "GENIA_STATE.md": "R13 E13-7/E13-8, issues #677/#678",
        "GENIA_RULES.md": "E13-7 changes no semantics",
        "README.md": "R13 E13-7",
        "GENIA_REPL_README.md": "E13-7 synchronizes runnable release examples",
        "docs/ai/LLM_CONTRACT.md": "E13-1 through E13-8 are complete",
        "docs/design/composability-matrix.md": "R13 public examples",
        "docs/design/r13-configuration-resolution-contract.md": (
            "E13-1 through E13-8 complete"
        ),
        "docs/releases/R13.md": "E13-1 through E13-8 delivered",
        "docs/releases/README.md": "E13-1 through E13-8 delivered",
        "docs/strategy/release-roadmap.md": (
            "E13-1 through E13-8 are complete"
        ),
        "docs/strategy/r13-configuration-resolution-ergonomics.md": (
            "E13-7 documentation and executable-example verification"
        ),
    }
    for path, expected in required.items():
        assert expected in _read(path), f"{path} must preserve synchronized R13 truth"

    release = RELEASE.read_text(encoding="utf-8")
    assert "Status: **Complete" in release
    assert "E13-1 through E13-8 delivered" in release
    assert "E13-7 and E13-8 remain gated" not in release


def test_r13_public_truth_keeps_maturity_portability_and_exclusions_explicit() -> None:
    release = RELEASE.read_text(encoding="utf-8").lower()
    for required in (
        "experimental",
        "portable ordinary",
        "python-host-only",
        "shared/multi-host conformance remains partial",
        "outcome",
        "immutable snapshot",
        "overrides > explicit arguments > environment > `.env`",
        "dot access",
        "ambient lookup",
        "lifecycle injection",
        "dependency injection",
        "interpolation",
        "profiles",
        "discovery",
        "refresh",
    ):
        assert required in release, f"R13 release truth is missing {required!r}"


def test_r13_semantic_fact_records_the_ordinary_composition_boundary() -> None:
    facts = json.loads(_read("docs/contract/semantic_facts.json"))
    fact = facts["r13_ordinary_composition_boundary"].lower()
    for required in (
        "ordinary callables",
        "explicit provider",
        "outcomes",
        "immutable snapshots",
        "callable template validation",
        "protected values",
        "python-host-only",
    ):
        assert required in fact


def test_r13_minimal_qualified_view_release_example_executes_exactly() -> None:
    source = (
        "provider = config_provider([{kind: quote(values), values: "
        '{SERVER_PORT: "8080", DB_PORT: "5432"}}]) |> unwrap_or(none)\n'
        'server = config_view(provider, "SERVER_")\n'
        'database = config_view(provider, "DB_")\n'
        '[server("PORT"), database("PORT")]'
    )
    result = _run_genia("-c", source)
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout == '[some("8080"), some("5432")]\n'


def test_r13_complete_validated_pipeline_release_example_executes_exactly() -> None:
    result = _run_genia("examples/r13_validated_pipeline_proving_case.genia")
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout == (
        "{server_port: some(8080), database_port: some(5432), metrics_port: "
        "some(9100), clean: [{id: 1, name: \"Ada\"}, {id: 2, name: \"Grace\"}], "
        "diagnostics: [{index: 1, kind: skipped, reason: \"blank_line\", context: "
        'none("nil")}, {index: 2, kind: error, reason: record_validation_failed, '
        "context: some({diagnostics: [{field: \"name\", status: error, reason: "
        '\"missing required field\", context: {field: \"name\", reason: '
        '\"missing required field\"}}]})}], credential: \"<protected>\", '
        "protected_match: true}\n"
    )
