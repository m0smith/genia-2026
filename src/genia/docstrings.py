from __future__ import annotations

import textwrap


def normalize_docstring(raw: str) -> str:
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    stripped = text.strip()
    if (stripped.startswith('"""') and stripped.endswith('"""')) or (
        stripped.startswith("'''") and stripped.endswith("'''")
    ):
        stripped = stripped[3:-3]
    dedented = textwrap.dedent(stripped)
    lines = dedented.split("\n")

    while lines and lines[0].strip() == "":
        lines.pop(0)
    while lines and lines[-1].strip() == "":
        lines.pop()

    out: list[str] = []
    blank_count = 0
    in_fence = False
    for line in lines:
        trimmed = line.rstrip() if not in_fence else line
        if trimmed.strip().startswith("```"):
            in_fence = not in_fence
            blank_count = 0
            out.append(trimmed)
            continue
        if trimmed.strip() == "":
            blank_count += 1
            if blank_count <= 1:
                out.append("")
            continue
        blank_count = 0
        out.append(trimmed)
    return "\n".join(out).strip()


def render_markdown_docstring(raw: str) -> str:
    return normalize_docstring(raw)
