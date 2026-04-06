from __future__ import annotations

from dataclasses import dataclass
import io
from pathlib import Path
import re

import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug


NON_RUNNABLE_MARKERS = {
    "**Example only — not runnable**",
    "**Illustrative sketch — not runnable**",
    "**Conceptual example — not directly runnable**",
}
OUTPUT_FENCE_TYPES = {"text"}
FENCE_RE = re.compile(r"^```([A-Za-z0-9_-]*)\s*$")


@dataclass(frozen=True)
class MarkdownBlock:
    index: int
    lang: str
    content: str
    start_line: int
    end_line: int
    preceding_line: str


def is_non_runnable_marker(line: str) -> bool:
    return line.strip() in NON_RUNNABLE_MARKERS


def collect_markdown_code_blocks(path: Path) -> list[MarkdownBlock]:
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks: list[MarkdownBlock] = []
    index = 0
    i = 0
    while i < len(lines):
        match = FENCE_RE.match(lines[i])
        if match is None:
            i += 1
            continue
        lang = match.group(1)
        start_line = i + 1
        preceding_line = lines[i - 1] if i > 0 else ""
        j = i + 1
        content_lines: list[str] = []
        while j < len(lines) and lines[j].strip() != "```":
            content_lines.append(lines[j])
            j += 1
        if j >= len(lines):
            raise AssertionError(f"{path}: unclosed code fence starting at line {start_line}")
        blocks.append(
            MarkdownBlock(
                index=index,
                lang=lang,
                content="\n".join(content_lines),
                start_line=start_line,
                end_line=j + 1,
                preceding_line=preceding_line,
            )
        )
        index += 1
        i = j + 1
    return blocks


def normalize_output(text: str) -> str:
    return text.replace("\r\n", "\n").rstrip()


def run_genia_snippet(source: str, env, stdout: io.StringIO, stderr: io.StringIO) -> str:
    stdout.seek(0)
    stdout.truncate(0)
    stderr.seek(0)
    stderr.truncate(0)
    try:
        result = run_source(source, env, filename="<sicp-doc>")
        if result is not None:
            stdout.write(format_debug(result) + "\n")
    except Exception as exc:  # noqa: BLE001
        stderr.write(f"Error: {exc}\n")
    return normalize_output(stdout.getvalue() + stderr.getvalue())


def validate_sicp_chapter(path: Path) -> list[MarkdownBlock]:
    blocks = collect_markdown_code_blocks(path)
    runnable_blocks: list[MarkdownBlock] = []

    for i, block in enumerate(blocks):
        if block.lang != "genia":
            continue
        if is_non_runnable_marker(block.preceding_line):
            continue

        if i + 1 >= len(blocks):
            raise AssertionError(
                f"{path}:{block.start_line}: runnable genia block #{block.index} is missing an adjacent expected-output block"
            )

        output_block = blocks[i + 1]
        if output_block.lang not in OUTPUT_FENCE_TYPES:
            raise AssertionError(
                f"{path}:{block.start_line}: runnable genia block #{block.index} must be followed by a {sorted(OUTPUT_FENCE_TYPES)!r} block, got '{output_block.lang or '<blank>'}'"
            )

        stdout = io.StringIO()
        stderr = io.StringIO()
        env = make_global_env(stdout_stream=stdout, stderr_stream=stderr)
        actual = run_genia_snippet(block.content, env, stdout, stderr)
        expected = normalize_output(output_block.content)
        if actual != expected:
            raise AssertionError(
                f"{path}:{block.start_line}: output mismatch for runnable genia block #{block.index}\n"
                f"Expected:\n{expected}\n"
                f"Actual:\n{actual}"
            )
        runnable_blocks.append(block)

    return runnable_blocks


def test_is_non_runnable_marker_accepts_supported_labels():
    for marker in NON_RUNNABLE_MARKERS:
        assert is_non_runnable_marker(marker)


def test_validate_sicp_chapter_accepts_valid_runnable_pair(tmp_path: Path):
    chapter = tmp_path / "chapter.md"
    chapter.write_text(
        """# Demo

```genia
1 + 2
```

```text
3
```
""",
        encoding="utf-8",
    )

    blocks = validate_sicp_chapter(chapter)

    assert len(blocks) == 1


def test_validate_sicp_chapter_skips_marked_non_runnable_block(tmp_path: Path):
    chapter = tmp_path / "chapter.md"
    chapter.write_text(
        """# Demo

**Conceptual example — not directly runnable**
```genia
fact(n, acc) = ...
```

```genia
1 + 2
```

```text
3
```
""",
        encoding="utf-8",
    )

    blocks = validate_sicp_chapter(chapter)

    assert len(blocks) == 1


def test_validate_sicp_chapter_fails_when_output_block_is_missing(tmp_path: Path):
    chapter = tmp_path / "chapter.md"
    chapter.write_text(
        """# Demo

```genia
1 + 2
```
""",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError, match="missing an adjacent expected-output block"):
        validate_sicp_chapter(chapter)


def test_validate_sicp_chapter_fails_when_next_block_is_genia(tmp_path: Path):
    chapter = tmp_path / "chapter.md"
    chapter.write_text(
        """# Demo

```genia
1 + 2
```

```genia
3
```
""",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError, match="must be followed by"):
        validate_sicp_chapter(chapter)


def test_validate_sicp_chapter_fails_on_output_mismatch(tmp_path: Path):
    chapter = tmp_path / "chapter.md"
    chapter.write_text(
        """# Demo

```genia
1 + 2
```

```text
99
```
""",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError, match="output mismatch"):
        validate_sicp_chapter(chapter)


def test_validate_sicp_chapter_supports_multiple_runnable_blocks(tmp_path: Path):
    chapter = tmp_path / "chapter.md"
    chapter.write_text(
        """# Demo

```genia
square(x) = x * x

square(5)
```

```text
25
```

```genia
square(x) = x * x

square(9)
```

```text
81
```
""",
        encoding="utf-8",
    )

    blocks = validate_sicp_chapter(chapter)

    assert len(blocks) == 2


def test_validate_sicp_chapter_handles_mixed_runnable_and_non_runnable_blocks(tmp_path: Path):
    chapter = tmp_path / "chapter.md"
    chapter.write_text(
        """# Demo

```genia
inc(x) = x + 1

inc(4)
```

```text
5
```

**Example only — not runnable**
```genia
inc(x) = ...
```

```genia
inc(x) = x + 1

inc(10)
```

```text
11
```
""",
        encoding="utf-8",
    )

    blocks = validate_sicp_chapter(chapter)

    assert len(blocks) == 2


@pytest.mark.parametrize(
    "path",
    sorted(
        p
        for p in Path("docs/sicp").iterdir()
        if p.is_file() and p.suffix.lower() == ".md" and p.name != "AGENTS.MD"
    ),
)
def test_sicp_chapters_have_valid_and_executable_genia_blocks(path: Path):
    validate_sicp_chapter(path)
