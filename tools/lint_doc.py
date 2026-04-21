#!/usr/bin/env python3
"""Deterministic linter for Genia @doc content.

Usage:
    python tools/lint_doc.py "doc string here"
    python tools/lint_doc.py --file path/to/file.genia
    python tools/lint_doc.py --scan-dir src/genia/std/prelude
    python tools/lint_doc.py --json --file path/to/file.genia

Checks only rules that can be verified reliably without NLP.
See docs/style/doc-style.md for the full style guide.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class LintFinding:
    rule_id: str
    severity: Severity
    message: str
    line: Optional[int] = None  # 1-based line within the doc string

    def __str__(self) -> str:
        loc = f"line {self.line}: " if self.line is not None else ""
        return f"[{self.severity.value}] {self.rule_id}: {loc}{self.message}"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALLOWED_SECTION_HEADERS = frozenset({
    "## Arguments",
    "## Returns",
    "## Errors",
    "## Notes",
    "## Examples",
})

DISCOURAGED_PREFIXES = [
    "this function",
    "this method",
    "function to",
]

ALLOWED_FENCE_LANGS = frozenset({"genia", "text", ""})

BEHAVIOR_TOKENS = ["none(", "flow", "lazy"]

HTML_TAG_RE = re.compile(r"</?[a-zA-Z][a-zA-Z0-9]*(?:\s[^>]*)?>")
PIPE_TABLE_RE = re.compile(r"^\s*\|.*\|.*\|\s*$")
SECTION_HEADER_RE = re.compile(r"^##\s+\S")
FENCE_RE = re.compile(r"^(`{3,})(.*)?$")


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

@dataclass
class ParsedDoc:
    """Lightweight parsed representation of a @doc string."""
    raw: str
    lines: List[str] = field(default_factory=list)
    summary_line_idx: Optional[int] = None  # index into self.lines
    summary_text: str = ""
    sections: List[str] = field(default_factory=list)  # header lines found
    section_line_indices: List[int] = field(default_factory=list)
    fences: List[dict] = field(default_factory=list)  # {open_idx, close_idx?, lang}


def parse_doc(text: str) -> ParsedDoc:
    """Parse a @doc string into a lightweight structure for lint rules."""
    doc = ParsedDoc(raw=text)
    doc.lines = text.split("\n")

    # Find summary: first non-empty line
    for i, line in enumerate(doc.lines):
        stripped = line.strip()
        if stripped:
            doc.summary_line_idx = i
            doc.summary_text = stripped
            break

    # Find section headers and fences
    in_fence = False
    fence_backtick_len = 0

    for i, line in enumerate(doc.lines):
        stripped = line.strip()
        m = FENCE_RE.match(stripped)
        if m:
            backticks = m.group(1)
            lang = (m.group(2) or "").strip()
            if not in_fence:
                in_fence = True
                fence_backtick_len = len(backticks)
                doc.fences.append({"open_idx": i, "close_idx": None, "lang": lang})
            elif len(backticks) >= fence_backtick_len and not lang:
                # closing fence
                in_fence = False
                doc.fences[-1]["close_idx"] = i
                fence_backtick_len = 0
            continue

        if not in_fence and SECTION_HEADER_RE.match(stripped):
            doc.sections.append(stripped)
            doc.section_line_indices.append(i)

    return doc


# ---------------------------------------------------------------------------
# Individual lint rules
# ---------------------------------------------------------------------------

def rule_summary_required(doc: ParsedDoc) -> List[LintFinding]:
    """DOC001: Every @doc must begin with a non-empty summary line."""
    if doc.summary_line_idx is None:
        return [LintFinding(
            rule_id="DOC001",
            severity=Severity.ERROR,
            message="@doc must begin with a non-empty summary line.",
        )]
    return []


def rule_summary_shape(doc: ParsedDoc) -> List[LintFinding]:
    """DOC002: Summary line should end with punctuation and avoid boilerplate."""
    findings: List[LintFinding] = []
    if not doc.summary_text:
        return findings

    # Check trailing punctuation
    if doc.summary_text[-1] not in ".!?":
        findings.append(LintFinding(
            rule_id="DOC002",
            severity=Severity.WARNING,
            message="Summary line should end with '.', '!', or '?'.",
            line=(doc.summary_line_idx or 0) + 1,
        ))

    # Check discouraged prefixes
    lower = doc.summary_text.lower()
    for prefix in DISCOURAGED_PREFIXES:
        if lower.startswith(prefix):
            findings.append(LintFinding(
                rule_id="DOC002",
                severity=Severity.WARNING,
                message=f"Summary should not start with '{prefix}'.",
                line=(doc.summary_line_idx or 0) + 1,
            ))
            break

    return findings


def rule_allowed_sections(doc: ParsedDoc) -> List[LintFinding]:
    """DOC003: Only allowed section headers may appear."""
    findings: List[LintFinding] = []
    for header, idx in zip(doc.sections, doc.section_line_indices):
        if header not in ALLOWED_SECTION_HEADERS:
            findings.append(LintFinding(
                rule_id="DOC003",
                severity=Severity.ERROR,
                message=f"Disallowed section header: '{header}'. "
                        f"Allowed: {', '.join(sorted(ALLOWED_SECTION_HEADERS))}",
                line=idx + 1,
            ))
    return findings


def rule_no_html(doc: ParsedDoc) -> List[LintFinding]:
    """DOC004: No raw HTML tags in @doc content."""
    findings: List[LintFinding] = []
    in_fence = False
    fence_backtick_len = 0

    for i, line in enumerate(doc.lines):
        stripped = line.strip()
        m = FENCE_RE.match(stripped)
        if m:
            backticks = m.group(1)
            lang = (m.group(2) or "").strip()
            if not in_fence:
                in_fence = True
                fence_backtick_len = len(backticks)
            elif len(backticks) >= fence_backtick_len and not lang:
                in_fence = False
                fence_backtick_len = 0
            continue

        if not in_fence and HTML_TAG_RE.search(line):
            findings.append(LintFinding(
                rule_id="DOC004",
                severity=Severity.ERROR,
                message="Raw HTML tags are not allowed in @doc content.",
                line=i + 1,
            ))
    return findings


def rule_no_tables(doc: ParsedDoc) -> List[LintFinding]:
    """DOC005: No markdown pipe-tables in @doc content."""
    findings: List[LintFinding] = []
    in_fence = False
    fence_backtick_len = 0

    for i, line in enumerate(doc.lines):
        stripped = line.strip()
        m = FENCE_RE.match(stripped)
        if m:
            backticks = m.group(1)
            lang = (m.group(2) or "").strip()
            if not in_fence:
                in_fence = True
                fence_backtick_len = len(backticks)
            elif len(backticks) >= fence_backtick_len and not lang:
                in_fence = False
                fence_backtick_len = 0
            continue

        if not in_fence and PIPE_TABLE_RE.match(line):
            findings.append(LintFinding(
                rule_id="DOC005",
                severity=Severity.ERROR,
                message="Markdown tables (pipe syntax) are not allowed in @doc content.",
                line=i + 1,
            ))
    return findings


def rule_behavior_mention(doc: ParsedDoc) -> List[LintFinding]:
    """DOC006: Important behavior tokens should appear outside example fences."""
    # Collect which behavior tokens appear anywhere in the doc
    lower_full = doc.raw.lower()
    relevant_tokens = [t for t in BEHAVIOR_TOKENS if t in lower_full]
    if not relevant_tokens:
        return []

    # Build set of lines that are inside fences
    fenced_lines: set = set()
    for fence in doc.fences:
        start = fence["open_idx"]
        end = fence["close_idx"] if fence["close_idx"] is not None else len(doc.lines) - 1
        for li in range(start, end + 1):
            fenced_lines.add(li)

    # Check if each token appears in non-fenced content
    findings: List[LintFinding] = []
    for token in relevant_tokens:
        found_outside = False
        for i, line in enumerate(doc.lines):
            if i in fenced_lines:
                continue
            if token in line.lower():
                found_outside = True
                break
        if not found_outside:
            findings.append(LintFinding(
                rule_id="DOC006",
                severity=Severity.WARNING,
                message=f"Behavior token '{token}' appears only inside an example fence. "
                        f"Mention it in prose or a section too.",
            ))
    return findings


def rule_examples_fence_sanity(doc: ParsedDoc) -> List[LintFinding]:
    """DOC007: Fenced code blocks must be balanced with allowed language tags."""
    findings: List[LintFinding] = []

    # Check for unbalanced fences
    for fence in doc.fences:
        if fence["close_idx"] is None:
            findings.append(LintFinding(
                rule_id="DOC007",
                severity=Severity.ERROR,
                message="Unclosed fenced code block.",
                line=fence["open_idx"] + 1,
            ))

    # Check language tags in ## Examples section fences
    # Find the line index where ## Examples starts
    examples_start = None
    next_section_start = None
    for header, idx in zip(doc.sections, doc.section_line_indices):
        if header == "## Examples":
            examples_start = idx
        elif examples_start is not None and next_section_start is None:
            next_section_start = idx

    if examples_start is not None:
        examples_end = next_section_start if next_section_start is not None else len(doc.lines)
        for fence in doc.fences:
            open_idx = fence["open_idx"]
            if examples_start < open_idx < examples_end:
                lang = fence["lang"]
                if lang not in ALLOWED_FENCE_LANGS:
                    findings.append(LintFinding(
                        rule_id="DOC007",
                        severity=Severity.ERROR,
                        message=f"Fence language '{lang}' is not allowed in ## Examples. "
                                f"Allowed: {', '.join(repr(lang_name) for lang_name in sorted(ALLOWED_FENCE_LANGS))}",
                        line=open_idx + 1,
                    ))

    return findings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

ALL_RULES = [
    rule_summary_required,
    rule_summary_shape,
    rule_allowed_sections,
    rule_no_html,
    rule_no_tables,
    rule_behavior_mention,
    rule_examples_fence_sanity,
]


def lint_doc(text: str) -> List[LintFinding]:
    """Lint a @doc string and return all findings."""
    doc = parse_doc(text)
    findings: List[LintFinding] = []
    for rule_fn in ALL_RULES:
        findings.extend(rule_fn(doc))
    return findings


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

# Pattern to extract @doc strings and the following binding name
_TRIPLE_DOC_RE = re.compile(r'@doc\s+"""(.*?)"""', re.DOTALL)
_SINGLE_DOC_RE = re.compile(r'@doc\s+"([^"]*)"')
_BINDING_NAME_RE = re.compile(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*[\(=]')


def _extract_docs_from_file(path: str) -> List[dict]:
    """Extract @doc strings from a .genia file.

    Returns list of dicts with keys: line, text, binding (binding may be None).
    """
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    docs: List[dict] = []
    matched_spans: List[tuple] = []

    def _find_binding(end_offset: int) -> Optional[str]:
        """Look for the binding name after the @doc string ends."""
        line_idx = content[:end_offset].count("\n")
        # Search the next few lines for a binding
        for i in range(line_idx, min(line_idx + 5, len(lines))):
            m = _BINDING_NAME_RE.match(lines[i])
            if m:
                return m.group(1)
        return None

    # Triple-quoted docs first (greedy match takes priority)
    for m in _TRIPLE_DOC_RE.finditer(content):
        line_num = content[:m.start()].count("\n") + 1
        binding = _find_binding(m.end())
        docs.append({"line": line_num, "text": m.group(1), "binding": binding})
        matched_spans.append((m.start(), m.end()))

    # Single-quoted docs, skipping any that overlap with triple-quoted matches
    for m in _SINGLE_DOC_RE.finditer(content):
        if any(s <= m.start() < e for s, e in matched_spans):
            continue
        line_num = content[:m.start()].count("\n") + 1
        binding = _find_binding(m.end())
        docs.append({"line": line_num, "text": m.group(1), "binding": binding})
    return docs


def _finding_to_dict(f: LintFinding) -> dict:
    """Convert a LintFinding to a JSON-serializable dict."""
    d: dict = {"rule_id": f.rule_id, "severity": f.severity.value, "message": f.message}
    if f.line is not None:
        d["line"] = f.line
    return d


def _format_finding_human(path: str, file_line: int, binding: Optional[str],
                          f: LintFinding) -> str:
    """Format a finding for human-readable output."""
    loc = f":{f.line}" if f.line else ""
    name = f" ({binding})" if binding else ""
    return f"{path}:{file_line}{loc}{name}: {f}"


def _scan_dir(dirpath: str, json_mode: bool) -> int:
    """Scan all .genia files in a directory and report findings."""
    import glob
    import json

    pattern = os.path.join(dirpath, "**", "*.genia")
    files = sorted(glob.glob(pattern, recursive=True))
    if not files:
        print(f"No .genia files found in {dirpath}", file=sys.stderr)
        return 0

    all_results: List[dict] = []
    error_count = 0
    warning_count = 0
    files_with_errors: List[str] = []

    for filepath in files:
        docs = _extract_docs_from_file(filepath)
        for doc_entry in docs:
            findings = lint_doc(doc_entry["text"])
            if findings:
                errors = [f for f in findings if f.severity == Severity.ERROR]
                warnings = [f for f in findings if f.severity == Severity.WARNING]
                error_count += len(errors)
                warning_count += len(warnings)
                if errors:
                    files_with_errors.append(filepath)

                if json_mode:
                    all_results.append({
                        "file": filepath,
                        "doc_line": doc_entry["line"],
                        "binding": doc_entry["binding"],
                        "findings": [_finding_to_dict(f) for f in findings],
                    })
                else:
                    for f in findings:
                        print(_format_finding_human(
                            filepath, doc_entry["line"], doc_entry["binding"], f))

    if json_mode:
        json.dump({
            "files_scanned": len(files),
            "errors": error_count,
            "warnings": warning_count,
            "results": all_results,
        }, sys.stdout, indent=2)
        print()
    else:
        # Summary line
        total_docs = sum(len(_extract_docs_from_file(f)) for f in files)
        print("\n--- Scan summary ---", file=sys.stderr)
        print(f"Files scanned: {len(files)}", file=sys.stderr)
        print(f"@doc strings found: {total_docs}", file=sys.stderr)
        print(f"Errors: {error_count}  Warnings: {warning_count}", file=sys.stderr)
        if files_with_errors:
            print(f"Files with errors: {', '.join(sorted(set(files_with_errors)))}",
                  file=sys.stderr)

    return 1 if error_count > 0 else 0


def main(argv: Optional[List[str]] = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print(
            "Usage:\n"
            "  lint_doc.py DOC_STRING\n"
            "  lint_doc.py --file FILE [--json]\n"
            "  lint_doc.py --scan-dir DIR [--json]\n",
            file=sys.stderr,
        )
        return 1

    json_mode = "--json" in args
    args = [a for a in args if a != "--json"]

    if args[0] == "--scan-dir":
        if len(args) < 2:
            print("Missing directory path after --scan-dir", file=sys.stderr)
            return 1
        return _scan_dir(args[1], json_mode)

    if args[0] == "--file":
        if len(args) < 2:
            print("Missing file path after --file", file=sys.stderr)
            return 1
        import json as json_mod

        docs = _extract_docs_from_file(args[1])
        exit_code = 0
        json_results: List[dict] = []

        for doc_entry in docs:
            findings = lint_doc(doc_entry["text"])
            if json_mode:
                if findings:
                    json_results.append({
                        "file": args[1],
                        "doc_line": doc_entry["line"],
                        "binding": doc_entry["binding"],
                        "findings": [_finding_to_dict(f) for f in findings],
                    })
            else:
                for f in findings:
                    print(_format_finding_human(
                        args[1], doc_entry["line"], doc_entry["binding"], f))
            if any(f.severity == Severity.ERROR for f in findings):
                exit_code = 1

        if json_mode:
            json_mod.dump(json_results, sys.stdout, indent=2)
            print()
        elif not docs:
            print("No @doc strings found.", file=sys.stderr)
        return exit_code
    else:
        text = args[0]
        findings = lint_doc(text)
        if json_mode:
            import json as json_mod
            json_mod.dump([_finding_to_dict(f) for f in findings], sys.stdout, indent=2)
            print()
        else:
            for f in findings:
                print(f)
        return 1 if any(f.severity == Severity.ERROR for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
