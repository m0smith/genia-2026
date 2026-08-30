from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "docs/releases/R12.md"


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _run_genia(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(Path(sys.executable).with_name("genia")), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_r12_status_remains_synchronized_after_release_completion() -> None:
    required = {
        "AGENTS.md": "E12-8 release-example truth synchronization",
        "GENIA_STATE.md": "R12 E12-8, issue #650",
        "README.md": "R12 E12-8",
        "GENIA_REPL_README.md": "E12-8 synchronizes runnable release examples",
        "docs/ai/LLM_CONTRACT.md": "R9, R10, R11, and R12 Complete",
        "docs/design/composability-matrix.md": "release-complete R12 boundary",
        "docs/design/r12-retrieval-grounding-contract.md": "E12-1 through E12-9 complete",
        "docs/releases/R12.md": "E12-1 through E12-9 delivered",
        "docs/releases/README.md": "E12-1 through E12-9 delivered",
        "docs/strategy/release-roadmap.md": "E12-1 through E12-9 complete",
    }
    for path, expected in required.items():
        assert expected in _read(path), f"{path} must preserve synchronized R12 truth"

    release = RELEASE.read_text(encoding="utf-8")
    assert "Status: **Complete" in release
    assert "E12-9 remains separately gated" not in release


def test_r12_public_truth_keeps_maturity_portability_and_exclusions_explicit() -> None:
    release = RELEASE.read_text(encoding="utf-8").lower()
    for required in (
        "experimental",
        "portable",
        "python-host-only",
        "ordinary values",
        "outcome",
        "backend-native",
        "citation rendering",
        "hidden query embedding",
        "persistence",
        "retry",
        "streaming",
        "agents",
        "provider registry",
        "rag",
    ):
        assert required in release, f"R12 release truth is missing {required!r}"


def test_r12_semantic_fact_records_the_ordinary_composition_boundary() -> None:
    facts = json.loads(_read("docs/contract/semantic_facts.json"))
    fact = facts["r12_ordinary_composition_boundary"].lower()
    for required in (
        "ordinary values",
        "outcomes",
        "exact provenance",
        "explicit query embedding",
        "opaque index handle",
        "backend-native scores",
        "unchanged model/4",
        "python-host-only",
    ):
        assert required in fact


def test_r12_local_chunk_release_example_executes_exactly() -> None:
    source = (
        'doc = {id: "doc-1", text: "A😀éZ", '
        'meta: represent("json", {source: "fixture"})}\n'
        "chunk((_text) -> [{offset: 1, length: 2}], doc) "
        "|> unwrap_or([]) |> map((item) -> [item.text, item.source])"
    )
    result = _run_genia("-c", source)
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout == '[["😀é", {doc_id: "doc-1", offset: 1, length: 2}]]\n'


def test_r12_complete_grounded_release_example_executes_exactly() -> None:
    result = _run(
        "-m",
        "hosts.python.exec_r12_grounded_fixture",
        "--file",
        "examples/r12_cross_mode_grounded_proving.genia",
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout == (
        '{answer: {kind: text, text: "Ada wrote notes."}, sources: '
        '[{doc_id: "doc-ada", offset: 0, length: 16}], evidence: '
        '[{chunk: {text: "Ada wrote notes.", source: {doc_id: "doc-ada", '
        "offset: 0, length: 16}, meta: <represented>}, score: 1.0}]}\n"
    )
