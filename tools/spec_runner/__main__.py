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


def _strip_issue_838_filter_args(argv: list[str]) -> list[str]:
    """Temporary branch-only shim for the issue #838 implementation runner.

    The generic runner does not currently expose category/name filtering. The
    temporary workflow only needs a successful full shared-spec pass before it
    commits the already-approved N-1 implementation, so discard those two
    harness-only filters and run the complete suite. Remove this shim before
    PR #839 leaves draft status.
    """
    result: list[str] = []
    index = 0
    while index < len(argv):
        if argv[index] in {"--category", "--name-prefix"}:
            index += 2
            continue
        result.append(argv[index])
        index += 1
    return result


_bootstrap_repo_pythonpath()

from .runner import main  # noqa: E402


raise SystemExit(main(_strip_issue_838_filter_args(sys.argv[1:])))
