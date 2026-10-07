#!/usr/bin/env python3
"""Baseline inventory of GENIA_STATE.md for the #1099 distillation (PR B, phase 4a).

Pure measurement: it never edits STATE. Output is deterministic JSON consumed by the
migration ledger guard (tests/doc/test_state_migration_map.py) and the preservation gates.

  python tools/state_inventory.py headings      # section inventory (JSON)
  python tools/state_inventory.py identifiers   # sorted distinct backtick identifiers (JSON)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STATE = REPO / "GENIA_STATE.md"
HEADING_RE = re.compile(r"^(#{1,6}) (.+?)\s*$")
NUMBER_RE = re.compile(r"^(\d+(?:\.\d+)*)\)")
ANCHOR_RE = re.compile(r"^<!-- anchor: (state:[a-z0-9-]+) -->$")


def _scan(text: str):
    lines = text.split("\n")
    out = []
    fence = False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            fence = not fence
            continue
        if not fence:
            m = HEADING_RE.match(line)
            if m:
                out.append((i, len(m.group(1)), m.group(2)))
    return lines, out


def headings(text: str) -> list[dict]:
    lines, found = _scan(text)
    rows = []
    for n, (i, level, title) in enumerate(found):
        end = len(lines)
        for j, lvl in [(j, l) for j, l, _ in found[n + 1 :]]:
            if lvl <= level:
                end = j
                break
        own_end = found[n + 1][0] if n + 1 < len(found) else len(lines)  # up to the next heading of any level
        body = "\n".join(lines[i:own_end])
        span = "\n".join(lines[i:end])
        anchor = None
        for line in lines[i + 1 : i + 4]:
            m = ANCHOR_RE.match(line)
            if m:
                anchor = m.group(1)
        number = NUMBER_RE.match(title)
        rows.append(
            {
                "id": f"H{n + 1:03d}",
                "line": i + 1,
                "level": level,
                "heading": title,
                "number": number.group(1) if number else None,
                "anchor": anchor,
                "span_lines": end - i,
                "span_words": len(span.split()),
                "own_lines": own_end - i,
                "own_words": len(body.split()),
                "issue_refs": len(re.findall(r"#\d{3,4}", span)),
                "ticket_tags": len(re.findall(r"\bE\d+-\d+\b", span)),
            }
        )
    return rows


def blocks(text: str, min_lines: int = 14, split_over: int = 70) -> list[dict]:
    """Partition every line of STATE into rows: one per heading, or sub-blocks for long sections.

    A row covers [start, end] (1-based, inclusive). Rows are contiguous and non-overlapping, so
    the ledger accounts for every line. A long section is split at top-level bullets/paragraphs,
    merging pieces smaller than ``min_lines``.
    """
    lines, found = _scan(text)
    starts = [0] + [i for i, _, _ in found if i > 0]
    starts = sorted(set(starts))
    rows = []
    for a, b in zip(starts, starts[1:] + [len(lines)]):
        if b - a <= split_over:
            rows.append((a, b))
            continue
        cuts = [a]
        fence = False
        for i in range(a + 1, b):
            line = lines[i]
            if line.startswith("```"):
                fence = not fence
            if fence:
                continue
            if line.startswith("- ") or (line and line[0] not in " -<`" and lines[i - 1] == ""):
                cuts.append(i)
        merged = []
        cur = cuts[0]
        for c in cuts[1:]:
            if c - cur >= min_lines:
                merged.append((cur, c))
                cur = c
        merged.append((cur, b))
        rows.extend(merged)
    out = []
    for n, (a, b) in enumerate(rows):
        seg = "\n".join(lines[a:b])
        title = next((l for l in lines[a:b] if l.strip() and not l.startswith("<!--")), "").strip()
        out.append(
            {
                "id": f"B{n + 1:03d}",
                "start": a + 1,
                "end": b,
                "title": title[:110],
                "lines": b - a,
                "words": len(seg.split()),
                "issue_refs": len(re.findall(r"#\d{3,4}", seg)),
                "ticket_tags": len(re.findall(r"\bE\d+-\d+\b", seg)),
                "identifiers": sorted(set(re.findall(r"`([^`\n]+)`", seg))),
            }
        )
    return out


def identifiers(text: str) -> list[str]:
    return sorted(set(re.findall(r"`([^`\n]+)`", text)))


def main(argv: list[str]) -> int:
    text = STATE.read_text(encoding="utf-8")
    if argv[:1] == ["headings"]:
        print(json.dumps(headings(text), indent=1, ensure_ascii=False))
    elif argv[:1] == ["blocks"]:
        print(json.dumps(blocks(text), indent=1, ensure_ascii=False))
    elif argv[:1] == ["identifiers"]:
        print(json.dumps(identifiers(text), indent=0, ensure_ascii=False))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
