from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def _function_body(source: str, name: str) -> str:
    marker = f"    def {name}"
    start = source.index(marker)
    next_def = source.find("\n    def ", start + len(marker))
    if next_def == -1:
        return source[start:]
    return source[start:next_def]


def test_rules_kernel_does_not_default_rule_result_fields_in_host() -> None:
    """Issue #121 keeps rule result defaulting in the portable Flow layer."""

    source = (REPO / "src/genia/builtins.py").read_text(encoding="utf-8")
    body = _function_body(source, "rules_kernel_fn")

    assert '.get("emit", [])' not in body
    assert '.get("ctx", current_ctx)' not in body
