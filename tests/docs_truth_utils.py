from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


REPO = Path(__file__).resolve().parent.parent
ROOT_DOC_FILES = [
    "AGENTS.md",
    "GENIA_REPL_README.md",
    "GENIA_RULES.md",
    "GENIA_STATE.md",
    "README.md",
]
DOC_SURFACE_DIRS = [
    "docs/book",
    "docs/cheatsheet",
    "docs/host-interop",
    "docs/sicp",
]
ALLOWED_CLASSIFICATIONS = {"Valid", "Likely valid", "Illustrative", "Invalid"}
CLASSIFICATION_RE = re.compile(
    r"^Classification:\s+(?:\*\*)?(Valid|Likely valid|Illustrative|Invalid)(?:\*\*)?(?:\b.*)?$"
)
FENCE_RE = re.compile(r"^```([A-Za-z0-9_-]*)\s*$")
HEADING_RE = re.compile(r"^(#{2,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class ExampleFence:
    path: Path
    heading: str
    opening_line: int
    closing_line: int
    classification_line: str | None
    classification_line_number: int | None


def read_text(relpath: str | Path) -> str:
    return (REPO / relpath).read_text(encoding="utf-8")


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def iter_markdown_files() -> list[Path]:
    files = [REPO / relpath for relpath in ROOT_DOC_FILES]
    for rel_dir in DOC_SURFACE_DIRS:
        files.extend(sorted((REPO / rel_dir).rglob("*.md")))
    return sorted(set(files))


def iter_example_docs() -> list[Path]:
    files: list[Path] = []
    for rel_dir in ["docs/book", "docs/cheatsheet", "docs/sicp"]:
        files.extend(sorted((REPO / rel_dir).rglob("*.md")))
    return files


def strip_fenced_code(text: str) -> str:
    lines = text.splitlines()
    stripped: list[str] = []
    in_fence = False
    for line in lines:
        if FENCE_RE.match(line):
            in_fence = not in_fence
            stripped.append("")
            continue
        stripped.append("" if in_fence else line)
    return "\n".join(stripped)


def _is_example_heading(title: str) -> bool:
    lowered = title.strip().lower()
    if "example" not in lowered:
        return False
    excluded = (
        "example rules",
        "examples",
        "stdlib/examples",
    )
    return not any(marker in lowered for marker in excluded)


def iter_primary_example_fences(path: Path) -> list[ExampleFence]:
    lines = path.read_text(encoding="utf-8").splitlines()
    fences: list[ExampleFence] = []

    for index, line in enumerate(lines):
        match = HEADING_RE.match(line.strip())
        if match is None:
            continue
        title = match.group(2)
        if not _is_example_heading(title):
            continue

        level = len(match.group(1))
        section_end = len(lines)
        for next_index in range(index + 1, len(lines)):
            next_match = HEADING_RE.match(lines[next_index].strip())
            if next_match and len(next_match.group(1)) <= level:
                section_end = next_index
                break

        opening_line = None
        closing_line = None
        lang = ""
        for block_index in range(index + 1, section_end):
            block_match = FENCE_RE.match(lines[block_index])
            if block_match is None:
                continue
            lang = block_match.group(1)
            inner = block_index + 1
            while inner < section_end and lines[inner].strip() != "```":
                inner += 1
            if inner >= section_end:
                raise AssertionError(f"{path}:{block_index + 1}: unclosed code fence in example section")
            if lang != "text":
                opening_line = block_index + 1
                closing_line = inner + 1
                break

        if opening_line is None or closing_line is None:
            continue

        classification_line = None
        classification_line_number = None
        probe_index = closing_line
        while probe_index < section_end:
            probe = lines[probe_index].strip()
            if not probe:
                probe_index += 1
                continue
            if probe.startswith("<!--"):
                probe_index += 1
                continue
            if probe.startswith("Classification:"):
                classification_line = probe
                classification_line_number = probe_index + 1
            break

        fences.append(
            ExampleFence(
                path=path,
                heading=title,
                opening_line=opening_line,
                closing_line=closing_line,
                classification_line=classification_line,
                classification_line_number=classification_line_number,
            )
        )

    return fences
