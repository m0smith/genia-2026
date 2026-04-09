from __future__ import annotations

import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
STAGING_ROOT = REPO_ROOT / ".tmp" / "mkdocs-docs"
ROOT_DOCS = [
    "README.md",
    "GENIA_STATE.md",
    "GENIA_RULES.md",
    "GENIA_REPL_README.md",
]
DOC_DIRS = [
    "docs/architecture",
    "docs/book",
    "docs/cheatsheet",
    "docs/host-interop",
]
README_LINK_REWRITES = {
    "(docs/architecture/": "(architecture/",
    "(docs/book/": "(book/",
    "(docs/cheatsheet/": "(cheatsheet/",
    "(docs/host-interop/": "(host-interop/",
}


def reset_staging_dir() -> None:
    if STAGING_ROOT.exists():
        shutil.rmtree(STAGING_ROOT)
    STAGING_ROOT.mkdir(parents=True)


def stage_root_doc(filename: str) -> None:
    source = REPO_ROOT / filename
    target_name = "index.md" if filename == "README.md" else filename
    target = STAGING_ROOT / target_name
    text = source.read_text(encoding="utf-8")
    if filename == "README.md":
        for old, new in README_LINK_REWRITES.items():
            text = text.replace(old, new)
    target.write_text(text, encoding="utf-8")


def stage_doc_tree(directory: str) -> None:
    source_root = REPO_ROOT / directory
    target_root = STAGING_ROOT / source_root.name
    for source in source_root.rglob("*.md"):
        if source.name == "CHAPTER_TEMPLATE.md":
            continue
        relative_path = source.relative_to(source_root)
        target = target_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def main() -> None:
    reset_staging_dir()
    for filename in ROOT_DOCS:
        stage_root_doc(filename)
    for directory in DOC_DIRS:
        stage_doc_tree(directory)
    print(f"Staged docs for MkDocs in {STAGING_ROOT}")


if __name__ == "__main__":
    main()
