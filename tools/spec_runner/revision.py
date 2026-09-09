"""
E16-4 contract revision resolution (issue #761).

Answers exactly two questions, using local git history only -- this module
never fetches from a remote, and never auto-upgrades or rewrites a host's
declared revision:

1. what is the exact genia-2026 revision this runner is currently checked
   out at?
2. does a host-declared revision resolve to a commit this local history
   already has, and if so, is it the revision currently checked out (a
   genuine pinned-conformance run) or a different, older commit (meaning
   this run's evidence can only honestly speak to current-main
   compatibility, not to pinned conformance for that declared revision)?

Real, separately-checked-out pinned-conformance evidence for an older
revision is an external-host-CI concern (E16-7, issue #764): that CI pins
its own genia-2026 checkout. This module only classifies what one local run
against the currently checked-out tree can honestly claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

REPO_ROOT = Path(__file__).resolve().parents[2]

REVISION_CHECK_KINDS = ("current", "resolvable_ancestor", "unresolvable")


class RevisionResolutionError(ValueError):
    """The runner's own current revision could not be determined."""


def current_revision(repo_root: Path = REPO_ROOT) -> str:
    """The exact git commit SHA this runner is currently checked out at."""
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RevisionResolutionError(
            "could not resolve the current genia-2026 revision via `git rev-parse HEAD`"
        )
    return completed.stdout.strip()


def is_locally_resolvable(revision: str, repo_root: Path = REPO_ROOT) -> bool:
    """True if ``revision`` names a commit this local git history already
    has. Never fetches from a remote; a revision this checkout has never
    seen is simply unresolvable, not an error to retry."""
    completed = subprocess.run(
        ["git", "cat-file", "-e", f"{revision}^{{commit}}"],
        cwd=str(repo_root),
        capture_output=True,
    )
    return completed.returncode == 0


@dataclass(frozen=True)
class RevisionCheck:
    """The E16-4 classification of one host-declared revision against the
    revision this runner is actually checked out at right now."""

    kind: str
    declared_revision: str
    current_revision: str

    def __post_init__(self) -> None:
        if self.kind not in REVISION_CHECK_KINDS:
            raise ValueError(f"invalid RevisionCheck kind: {self.kind!r}")


def check_revision(declared_revision: str, repo_root: Path = REPO_ROOT) -> RevisionCheck:
    """Classify a host's declared ``contract_revision``.

    - ``"current"``: the declared revision is exactly the revision this
      runner is checked out at. This run's pass/fail evidence is honest
      pinned-conformance evidence for that declared revision.
    - ``"resolvable_ancestor"``: the declared revision is a real, locally
      known commit, but not the one currently checked out. This run tested
      the host against a *different* spec/ tree than it declared; its
      evidence can only honestly be reported as current-main compatibility
      for the host, not as pinned conformance for its declared revision.
    - ``"unresolvable"``: the declared revision names no commit this local
      history has. Neither pinned-conformance nor current-main-compatibility
      evidence can be honestly attributed to it.
    """
    current = current_revision(repo_root)
    if declared_revision == current:
        return RevisionCheck(kind="current", declared_revision=declared_revision, current_revision=current)
    if is_locally_resolvable(declared_revision, repo_root):
        return RevisionCheck(
            kind="resolvable_ancestor", declared_revision=declared_revision, current_revision=current
        )
    return RevisionCheck(kind="unresolvable", declared_revision=declared_revision, current_revision=current)
