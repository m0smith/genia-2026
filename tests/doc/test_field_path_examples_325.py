from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

DOC_PATHS = [
    "GENIA_STATE.md",
    "GENIA_REPL_README.md",
    "README.md",
    "docs/cheatsheet/core.md",
    "docs/design/representation-system-and-format.md",
]

SLASH_PLACEHOLDER_RE = re.compile(
    r"\{[A-Za-z_][A-Za-z0-9_]*(?:/[A-Za-z_][A-Za-z0-9_]*)+(?:\.[A-Za-z_][A-Za-z0-9_]*)?\}"
)


def read_text(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def normalize(text: str) -> str:
    return " ".join(text.split())


def test_issue_325_representation_doc_uses_dot_field_path_examples() -> None:
    relpath = "docs/design/representation-system-and-format.md"
    text = normalize(read_text(relpath))

    required_excerpts = [
        "Field-path placeholders use dot-separated nested map lookup: `{user.name}`, `{user.address.city}`",
        'format("{user.name} lives in {user.address.city}", {user: {name: "Ada", address: {city: "Bountiful"}}})',
        '"Ada lives in Bountiful"',
        "Classification: Valid, covered by `spec/eval/format-field-path-multi-nested.yaml`.",
    ]

    missing = [excerpt for excerpt in required_excerpts if normalize(excerpt) not in text]
    assert missing == []


def test_issue_325_public_docs_do_not_use_slash_field_path_placeholders() -> None:
    offenders: dict[str, list[str]] = {}

    for relpath in DOC_PATHS:
        matches = sorted(set(SLASH_PLACEHOLDER_RE.findall(read_text(relpath))))
        if matches:
            offenders[relpath] = matches

    assert offenders == {}
