from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_r12_release_completion_is_synchronized_after_e12_9() -> None:
    required = {
        "AGENTS.md": "R12 — Retrieval & Grounding is complete",
        "GENIA_STATE.md": "R12 is release-complete through E12-9",
        "GENIA_RULES.md": "R12 is release-complete",
        "GENIA_REPL_README.md": "E12-9 completes audit/distillation",
        "README.md": "truth audit makes R12",
        "docs/ai/LLM_CONTRACT.md": "R9, R10, R11, R12, and R13 Complete",
        "docs/design/composability-matrix.md": "release-complete R12 boundary",
        "docs/design/r12-retrieval-grounding-contract.md": "E12-1 through E12-9 complete",
        "docs/releases/R12.md": "Status: **Complete",
        "docs/releases/README.md": "COMPLETE; E12-1 through E12-9 delivered",
        "docs/strategy/killer-workflow.md": "R12** is complete through E12-9",
        "docs/strategy/release-roadmap.md": "Release R12 — Retrieval & Grounding ✓ COMPLETE",
    }
    for path, expected in required.items():
        assert expected in _read(path), f"{path} must record completed R12 truth"


def test_r12_completion_does_not_overstate_maturity_portability_or_scope() -> None:
    combined = "\n".join(
        _read(path)
        for path in (
            "GENIA_STATE.md",
            "README.md",
            "docs/ai/LLM_CONTRACT.md",
            "docs/releases/R12.md",
            "docs/strategy/release-roadmap.md",
        )
    ).lower()
    for required in (
        "experimental",
        "python",
        "partial",
        "hidden query embedding",
        "persistence",
        "citation rendering",
        "provider registry",
        "streaming",
        "retry",
        "agents",
    ):
        assert required in combined

    release = _read("docs/releases/R12.md")
    assert "E12-9 remains separately gated" not in release
    assert "Status: **Active" not in release


def test_r12_completion_preserves_the_approved_composition_boundary() -> None:
    state = _read("GENIA_STATE.md")
    rules = _read("GENIA_RULES.md")
    release = _read("docs/releases/R12.md")
    assert "explicit query embedding" in state
    assert "opaque backend-native scores" in rules
    assert "unchanged R11 `model/4`" in release
    for purpose in ("embed_call", "index_call", "retrieve_call", "rerank_call"):
        assert f"`quote({purpose})`" in release
