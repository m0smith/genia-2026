"""
E16-4 (issue #761) contract revision pinning and current-main compatibility
classification tests.
"""
from __future__ import annotations

import re
import subprocess

import pytest

from tools.spec_runner.revision import (
    REPO_ROOT,
    RevisionResolutionError,
    check_revision,
    current_revision,
    is_locally_resolvable,
)

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def test_current_revision_returns_a_full_sha() -> None:
    revision = current_revision()
    assert _SHA_RE.match(revision)


def test_current_revision_matches_git_rev_parse_head() -> None:
    expected = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), capture_output=True, text=True, check=True
    ).stdout.strip()
    assert current_revision() == expected


def test_current_revision_raises_when_repo_root_is_not_a_git_repo(tmp_path) -> None:
    with pytest.raises(RevisionResolutionError):
        current_revision(repo_root=tmp_path)


def test_is_locally_resolvable_true_for_head() -> None:
    assert is_locally_resolvable(current_revision()) is True


def test_is_locally_resolvable_false_for_unknown_sha() -> None:
    assert is_locally_resolvable("0" * 40) is False


def test_check_revision_current_when_declared_equals_head() -> None:
    head = current_revision()
    result = check_revision(head)
    assert result.kind == "current"
    assert result.declared_revision == head
    assert result.current_revision == head


def test_check_revision_resolvable_ancestor_for_a_real_older_commit(tmp_path) -> None:
    """Uses a self-contained temp repo with a controlled two-commit history,
    rather than HEAD~1 on this checkout: CI checks out genia-2026 with
    --depth=1 (shallow clone), where HEAD~1 does not exist. A synthetic repo
    keeps this test correct regardless of the real checkout's clone depth."""

    def _git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=str(tmp_path), capture_output=True, text=True, check=True
        ).stdout.strip()

    _git("init", "-q")
    _git("config", "user.email", "test@example.com")
    _git("config", "user.name", "Test")
    (tmp_path / "a.txt").write_text("1")
    _git("add", "a.txt")
    _git("commit", "-q", "-m", "first")
    first_commit = _git("rev-parse", "HEAD")
    (tmp_path / "a.txt").write_text("2")
    _git("add", "a.txt")
    _git("commit", "-q", "-m", "second")
    second_commit = _git("rev-parse", "HEAD")

    result = check_revision(first_commit, repo_root=tmp_path)
    assert result.kind == "resolvable_ancestor"
    assert result.declared_revision == first_commit
    assert result.current_revision == second_commit


def test_check_revision_unresolvable_for_unknown_sha() -> None:
    result = check_revision("0" * 40)
    assert result.kind == "unresolvable"
