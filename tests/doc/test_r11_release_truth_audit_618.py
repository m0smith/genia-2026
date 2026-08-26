from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_r11_release_completion_is_synchronized_after_e11_8() -> None:
    required = {
        "AGENTS.md": "R11 — AI Composition is complete",
        "GENIA_STATE.md": "R11 E11-1 through E11-8",
        "GENIA_RULES.md": "R11 E11-1 through E11-8",
        "GENIA_REPL_README.md": "R11 E11-1 through E11-8",
        "README.md": "R11 E11-1 through E11-8",
        "docs/ai/LLM_CONTRACT.md": "R11 — AI Composition is complete",
        "docs/design/README.md": "E11-1 through E11-8 are complete",
        "docs/design/r11-ai-composition-contract.md": "E11-1 through E11-8 complete",
        "docs/releases/R11.md": "Status: **Complete",
        "docs/releases/README.md": "COMPLETE; E11-1 through E11-8 delivered",
        "docs/strategy/killer-workflow.md": "R11** is complete",
        "docs/strategy/release-roadmap.md": "Release R11 — AI Composition ✓ COMPLETE",
    }
    for path, expected in required.items():
        assert expected in _read(path), f"{path} must record completed R11 truth"


def test_r11_completion_does_not_overstate_maturity_or_scope() -> None:
    combined = "\n".join(
        _read(path)
        for path in (
            "GENIA_STATE.md",
            "README.md",
            "docs/ai/LLM_CONTRACT.md",
            "docs/releases/R11.md",
            "docs/strategy/release-roadmap.md",
        )
    ).lower()
    for required in (
        "experimental",
        "python-host-only",
        "partial",
        "tools",
        "agents",
        "streaming",
        "retrieval",
        "r12",
    ):
        assert required in combined

    release = _read("docs/releases/R11.md").lower()
    assert "does not claim r11 completion" not in release
    assert "e11-8 remains" not in release


def test_r11_completion_keeps_the_single_public_ai_surface() -> None:
    state = _read("GENIA_STATE.md")
    rules = _read("GENIA_RULES.md")
    release = _read("docs/releases/R11.md")
    assert "`model(provider, config, credential, authority)` is the sole public AI entry point" in state
    assert "`model(provider, config, credential, authority)` is an ordinary call" in rules
    assert "one Experimental public entry point, `model/4`" in release
