from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_r13_release_completion_is_synchronized_after_e13_8() -> None:
    required = {
        "AGENTS.md": "R13 — Configuration Resolution Ergonomics is complete",
        "GENIA_STATE.md": "R13 is release-complete through E13-8",
        "GENIA_RULES.md": "R13 is release-complete",
        "GENIA_REPL_README.md": "E13-8 completes audit/distillation",
        "README.md": "truth audit makes R13 release-complete",
        "docs/ai/LLM_CONTRACT.md": "R9, R10, R11, R12, and R13 Complete",
        "docs/design/composability-matrix.md": "release-complete R13 boundary",
        "docs/design/r13-configuration-resolution-contract.md": (
            "E13-1 through E13-8 complete"
        ),
        "docs/releases/R13.md": "Status: **Complete",
        "docs/releases/README.md": "COMPLETE; E13-1 through E13-8 delivered",
        "docs/strategy/killer-workflow.md": "R13** is complete through E13-8",
        "docs/strategy/release-roadmap.md": (
            "Release R13 — Configuration Resolution Ergonomics ✓ COMPLETE"
        ),
    }
    for path, expected in required.items():
        assert expected in _read(path), f"{path} must record completed R13 truth"


def test_r13_completion_does_not_overstate_maturity_portability_or_scope() -> None:
    combined = "\n".join(
        _read(path)
        for path in (
            "GENIA_STATE.md",
            "README.md",
            "docs/ai/LLM_CONTRACT.md",
            "docs/releases/R13.md",
            "docs/strategy/release-roadmap.md",
        )
    ).lower()
    for required in (
        "experimental",
        "python",
        "partial",
        "dot access",
        "ambient lookup",
        "lifecycle injection",
        "dependency injection",
        "interpolation",
        "profiles",
        "discovery",
        "refresh",
    ):
        assert required in combined

    release = _read("docs/releases/R13.md")
    assert "E13-8 remains separately gated" not in release
    assert "Status: **Active" not in release


def test_r13_completion_preserves_r10_and_the_approved_composition_boundary() -> None:
    state = _read("GENIA_STATE.md")
    rules = _read("GENIA_RULES.md")
    release = _read("docs/releases/R13.md")
    assert "overrides > explicit arguments > environment > `.env`" in release
    assert "immutable snapshot" in state
    assert "one existing `config_get` or `secret_get`, and returns its exact Outcome" in rules
    assert "protected" in state.lower()
    contract = _read("docs/design/r13-configuration-resolution-contract.md")
    assert "No new syntax" in contract
    assert "Core IR node" in contract
