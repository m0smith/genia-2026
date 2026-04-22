#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CANONICAL_FILES = [
    ROOT / "AGENTS.md",
    ROOT / "GENIA_STATE.md",
    ROOT / "GENIA_RULES.md",
    ROOT / "docs/ai/LLM_CONTRACT.md",
]

OPTIONAL_LLM_FILES = [
    ROOT / ".github/copilot-instructions.md",
]

OPTIONAL_LLM_GLOBS = [
    ".github/instructions/**/*.md",
    ".github/instructions/**/*.instructions.md",
    ".github/agents/**/*.md",
    ".github/agents/**/*.agent.md",
]

REQUIRED_REFERENCES = [
    "GENIA_STATE.md",
    "GENIA_RULES.md",
    "AGENTS.md",
    "docs/ai/LLM_CONTRACT.md",
]

# These phrases are dangerous because they create competing constitutions.
FORBIDDEN_PATTERNS = [
    re.compile(r"\bthis file is the source of truth\b", re.IGNORECASE),
    re.compile(r"\bthis file defines language semantics\b", re.IGNORECASE),
    re.compile(r"\bcopilot instructions take precedence\b", re.IGNORECASE),
    re.compile(r"\btool-specific instructions take precedence\b", re.IGNORECASE),
    re.compile(r"\bAGENTS\.md is the final authority\b", re.IGNORECASE),
    re.compile(r"\bLLM_CONTRACT\.md is the final authority\b", re.IGNORECASE),
    re.compile(r"\bsemantics are defined here\b", re.IGNORECASE),
]

# In lower-level files, these topics should normally be referenced, not redefined at length.
PROTECTED_TOPIC_PATTERNS = [
    re.compile(r"\boption\b", re.IGNORECASE),
    re.compile(r"\bsome\s*/\s*none\b", re.IGNORECASE),
    re.compile(r"\bsome\b", re.IGNORECASE),
    re.compile(r"\bnone\b", re.IGNORECASE),
    re.compile(r"\bpipeline\b", re.IGNORECASE),
    re.compile(r"\|\>"),
    re.compile(r"\bpattern matching\b", re.IGNORECASE),
    re.compile(r"\bhost portability\b", re.IGNORECASE),
    re.compile(r"\bcore ir\b", re.IGNORECASE),
]

MAX_PROTECTED_TOPIC_HITS_IN_TOOL_FILE = 6

DOC_REMINDER_PATTERNS = [
    re.compile(r"update documentation", re.IGNORECASE),
    re.compile(r"update docs", re.IGNORECASE),
]

TEST_REMINDER_PATTERNS = [
    re.compile(r"\btests\b", re.IGNORECASE),
    re.compile(r"update .*tests", re.IGNORECASE),
    re.compile(r"add .*tests", re.IGNORECASE),
]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def gather_tool_specific_files() -> list[Path]:
    files: list[Path] = []
    for path in OPTIONAL_LLM_FILES:
        if path.exists():
            files.append(path)
    for pattern in OPTIONAL_LLM_GLOBS:
        files.extend(sorted(ROOT.glob(pattern)))
    deduped = []
    seen = set()
    for path in files:
        if path.is_file() and path not in seen:
            seen.add(path)
            deduped.append(path)
    return deduped


def validate_canonical_files(errors: list[str]) -> None:
    for path in CANONICAL_FILES:
        if not path.exists():
            errors.append(f"Missing canonical file: {rel(path)}")


def validate_contract_alignment(errors: list[str]) -> None:
    agents = ROOT / "AGENTS.md"
    contract = ROOT / "docs/ai/LLM_CONTRACT.md"

    if not agents.exists() or not contract.exists():
        return

    agents_text = read_text(agents)
    contract_text = read_text(contract)

    if "GENIA_STATE.md is the final authority" not in agents_text and "GENIA_STATE.md` is the final authority" not in agents_text:
        errors.append(
            "AGENTS.md no longer appears to declare GENIA_STATE.md as final authority."
        )

    if "GENIA_STATE.md" not in contract_text or "final authority" not in contract_text.lower():
        errors.append(
            "docs/ai/LLM_CONTRACT.md must state that GENIA_STATE.md is the final authority for implemented behavior."
        )

    if "tool-specific instruction files" not in contract_text.lower() or "must not redefine" not in contract_text.lower():
        errors.append(
            "docs/ai/LLM_CONTRACT.md must state that tool-specific instruction files must not redefine semantics."
        )


def validate_tool_file(path: Path, errors: list[str]) -> None:
    text = read_text(path)

    for reference in REQUIRED_REFERENCES:
        if reference not in text:
            errors.append(f"{rel(path)} is missing required reference: {reference}")

    for pattern in FORBIDDEN_PATTERNS:
        if pattern.search(text):
            errors.append(
                f"{rel(path)} contains forbidden authority/semantics claim matching: {pattern.pattern}"
            )

    protected_hits = sum(1 for pattern in PROTECTED_TOPIC_PATTERNS if pattern.search(text))
    if protected_hits > MAX_PROTECTED_TOPIC_HITS_IN_TOOL_FILE:
        errors.append(
            f"{rel(path)} appears to duplicate protected semantic content instead of referencing canonical docs."
        )

    if not any(pattern.search(text) for pattern in DOC_REMINDER_PATTERNS):
        errors.append(
            f"{rel(path)} should remind agents to update documentation with behavior/code changes."
        )

    if not any(pattern.search(text) for pattern in TEST_REMINDER_PATTERNS):
        errors.append(
            f"{rel(path)} should remind agents to update or add tests."
        )


def main() -> int:
    errors: list[str] = []

    validate_canonical_files(errors)
    validate_contract_alignment(errors)

    tool_files = gather_tool_specific_files()
    if not tool_files:
        errors.append(
            "No tool-specific LLM instruction files were found under .github/. Add at least .github/copilot-instructions.md."
        )

    for path in tool_files:
        validate_tool_file(path, errors)

    if errors:
        print("LLM instruction validation failed:\n", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("LLM instruction validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
