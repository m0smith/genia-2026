from __future__ import annotations

from pathlib import Path
import sys


def _bootstrap_repo_pythonpath() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    src_path = repo_root / "src"

    for candidate in (repo_root, src_path):
        candidate_str = str(candidate)
        if candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)


_bootstrap_repo_pythonpath()

from .runner import main


raise SystemExit(main())
