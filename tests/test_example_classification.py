from __future__ import annotations

from pathlib import Path
import sys

import pytest

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from docs_truth_utils import (
    CLASSIFICATION_RE,
    REPO,
    display_path,
    iter_example_docs,
    iter_primary_example_fences,
)


def assert_example_classifications_present(path: Path) -> None:
    violations: list[str] = []
    for fence in iter_primary_example_fences(path):
        location = f"{display_path(path)}:{fence.closing_line}"
        if fence.classification_line is None:
            violations.append(f"{location}: missing classification after '{fence.heading}'")
            continue
        if CLASSIFICATION_RE.match(fence.classification_line) is None:
            violations.append(
                f"{location}: invalid classification vocabulary after '{fence.heading}': "
                f"{fence.classification_line}"
            )
    assert not violations, "\n".join(violations)


@pytest.mark.parametrize("path", iter_example_docs(), ids=lambda p: str(p.relative_to(REPO)))
def test_example_sections_use_supported_classification_labels(path: Path) -> None:
    assert_example_classifications_present(path)


def test_example_classification_helper_rejects_missing_label(tmp_path: Path) -> None:
    chapter = tmp_path / "chapter.md"
    chapter.write_text(
        """# Demo

## Minimal example

```genia
1 + 2
```
""",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError, match="missing classification"):
        assert_example_classifications_present(chapter)


def test_example_classification_helper_rejects_invalid_vocabulary(tmp_path: Path) -> None:
    chapter = tmp_path / "chapter.md"
    chapter.write_text(
        """# Demo

## Minimal example

```genia
1 + 2
```
Classification: **Runnable**
""",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError, match="invalid classification vocabulary"):
        assert_example_classifications_present(chapter)
