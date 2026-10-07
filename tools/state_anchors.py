"""Semantic anchor parsing for GENIA_STATE.md (#1099).

An anchor is one line ``<!-- anchor: state:<name> -->`` placed immediately after a ``##`` or
``###`` heading (blank lines allowed). Its span runs from that heading to the line before the next
heading of the same or higher level, so a ``##`` span includes its ``###`` children. Anchors
identify sections independently of heading numbers or titles.

This module only parses text; it never defines or changes language semantics.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

MARKER_RE = re.compile(r"^<!-- anchor: (?P<name>\S+) -->$")
NAME_RE = re.compile(r"^state:[a-z0-9]+(?:-[a-z0-9]+)*$")
HEADING_RE = re.compile(r"^(?P<hashes>#{1,6}) (?P<title>.+?)\s*$")
SECTION_NUMBER_RE = re.compile(r"^## (?P<number>\d+(?:\.\d+)*)\)")


@dataclass(frozen=True)
class Anchor:
    name: str
    heading: str
    level: int
    start: int  # index of the heading line
    end: int  # exclusive index of the first line after the span
    section_number: str | None  # number of the enclosing (or own) ``##`` heading


def _lines(text: str) -> list[str]:
    return text.split("\n")


def _headings(lines: list[str]) -> list[tuple[int, int]]:
    """(line index, level) for every heading outside fenced code blocks."""
    found: list[tuple[int, int]] = []
    in_fence = False
    for index, line in enumerate(lines):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_RE.match(line)
        if match:
            found.append((index, len(match.group("hashes"))))
    return found


def _markers(lines: list[str]) -> list[tuple[int, str]]:
    found = []
    in_fence = False
    for index, line in enumerate(lines):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = MARKER_RE.match(line)
        if match:
            found.append((index, match.group("name")))
    return found


def _heading_before_marker(lines: list[str], marker_index: int, heading_lines: dict[int, int]) -> int | None:
    index = marker_index - 1
    while index >= 0 and lines[index].strip() == "":
        index -= 1
    return index if index in heading_lines else None


def parse_anchors(text: str) -> dict[str, Anchor]:
    """Map anchor name -> Anchor. A duplicate name keeps its first occurrence (see problems)."""
    lines = _lines(text)
    headings = _headings(lines)
    heading_levels = dict(headings)
    result: dict[str, Anchor] = {}
    for marker_index, name in _markers(lines):
        heading_index = _heading_before_marker(lines, marker_index, heading_levels)
        if heading_index is None or name in result:
            continue
        level = heading_levels[heading_index]
        end = len(lines)
        for index, other_level in headings:
            if index > heading_index and other_level <= level:
                end = index
                break
        result[name] = Anchor(
            name=name,
            heading=lines[heading_index],
            level=level,
            start=heading_index,
            end=end,
            section_number=_enclosing_section_number(lines, headings, heading_index),
        )
    return result


def _enclosing_section_number(lines: list[str], headings: list[tuple[int, int]], heading_index: int) -> str | None:
    for index, level in reversed([h for h in headings if h[0] <= heading_index]):
        if level == 2:
            match = SECTION_NUMBER_RE.match(lines[index])
            return match.group("number") if match else None
        if level == 1:
            return None
    return None


def span_text(text: str, anchor: Anchor) -> str:
    return "\n".join(_lines(text)[anchor.start : anchor.end])


def find_anchor_problems(text: str) -> list[str]:
    lines = _lines(text)
    heading_levels = dict(_headings(lines))
    problems: list[str] = []
    seen: set[str] = set()
    for marker_index, name in _markers(lines):
        if not NAME_RE.match(name):
            problems.append(f"line {marker_index + 1}: malformed anchor name {name!r}")
        if name in seen:
            problems.append(f"line {marker_index + 1}: duplicate anchor {name!r}")
        seen.add(name)
        heading_index = _heading_before_marker(lines, marker_index, heading_levels)
        if heading_index is None:
            problems.append(f"line {marker_index + 1}: anchor {name!r} must directly follow a heading")
        elif heading_levels[heading_index] not in (2, 3):
            problems.append(f"line {marker_index + 1}: anchor {name!r} must follow a ## or ### heading")
    return problems
