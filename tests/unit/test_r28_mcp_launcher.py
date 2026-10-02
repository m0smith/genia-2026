"""R28 E28-1 (issue #702): build/launch identity boundary tests.

``contract_revision`` is server-owned build/launch metadata supplied through a
narrow host boundary (``hosts/python/mcp_launch.py``) as an inert 40-lowercase-hex
value. The native ``mcp.genia`` constructs the capability result; the host must
not. See docs/design/r28-e28-1-native-mcp-skeleton-design.md section 8, row 5.

Expected to fail until the launcher and ``mcp.genia`` exist (failing-test phase).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from tests.fixtures.r28_mcp_helpers import (
    LAUNCHER_PATH,
    REPO_ROOT,
    REVISION,
    SERVER_PATH,
    encode,
    expected_envelope,
    frames,
    request,
    server_env,
)

pytestmark = pytest.mark.unit

HEX40 = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_ENV_KEYS = {
    "PATH",
    "PYTHONPATH",
    "PYTHONIOENCODING",
    "PYTHONUTF8",
    "LANG",
    "LC_ALL",
    "SYSTEMROOT",
    "LD_LIBRARY_PATH",
    "DYLD_LIBRARY_PATH",
}


def _launcher():
    assert LAUNCHER_PATH.is_file(), (
        "E28-1 not implemented: hosts/python/mcp_launch.py does not exist"
    )
    import importlib

    return importlib.import_module("hosts.python.mcp_launch")


def _git(repo: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
        GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid",
    )
    done = subprocess.run(
        ["git", *args], cwd=repo, env=env, capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def _make_repo(path: Path) -> str:
    path.mkdir()
    _git(path, "init", "-q")
    (path / "a.txt").write_text("one\n")
    _git(path, "add", "a.txt")
    _git(path, "commit", "-q", "-m", "c1")
    return _git(path, "rev-parse", "HEAD")


def test_revision_is_exactly_40_lowercase_hex(tmp_path):
    launcher = _launcher()
    head = _make_repo(tmp_path / "r")
    revision = launcher.resolve_contract_revision(tmp_path / "r")
    assert HEX40.fullmatch(revision)
    assert revision == head


def test_revision_propagation_is_deterministic(tmp_path):
    launcher = _launcher()
    _make_repo(tmp_path / "r")
    values = {launcher.resolve_contract_revision(tmp_path / "r") for _ in range(5)}
    assert len(values) == 1


def test_dirty_workspace_is_never_described(tmp_path):
    launcher = _launcher()
    repo = tmp_path / "r"
    head = _make_repo(repo)
    (repo / "a.txt").write_text("modified\n")  # tracked change
    (repo / "untracked.txt").write_text("x\n")  # untracked file
    revision = launcher.resolve_contract_revision(repo)
    assert revision == head  # no "-dirty", no suffix, no extra state
    assert HEX40.fullmatch(revision)


def test_ambient_git_environment_cannot_redirect_resolution(tmp_path, monkeypatch):
    launcher = _launcher()
    head = _make_repo(tmp_path / "r")
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "nonexistent"))
    monkeypatch.setenv("GIT_WORK_TREE", str(tmp_path))
    monkeypatch.setenv("GIT_INDEX_FILE", str(tmp_path / "idx"))
    assert launcher.resolve_contract_revision(tmp_path / "r") == head


def test_default_resolution_is_module_relative_not_caller_cwd(tmp_path, monkeypatch):
    launcher = _launcher()
    expected = _git(REPO_ROOT, "rev-parse", "HEAD")
    monkeypatch.chdir(tmp_path)  # caller cwd elsewhere
    assert launcher.resolve_contract_revision() == expected


def test_unresolvable_revision_fails_closed_without_leaking_paths(tmp_path):
    launcher = _launcher()
    not_a_repo = tmp_path / "plain"
    not_a_repo.mkdir()
    with pytest.raises(launcher.McpLaunchError) as excinfo:
        launcher.resolve_contract_revision(not_a_repo)
    text = str(excinfo.value)
    assert str(tmp_path) not in text and "Traceback" not in text and "fatal:" not in text


@pytest.mark.parametrize(
    "bad",
    ["", "x" * 40, REVISION.upper(), REVISION[:39], REVISION + "0", REVISION + "-dirty"],
)
def test_command_builder_rejects_non_inert_revisions(bad):
    launcher = _launcher()
    with pytest.raises(launcher.McpLaunchError):
        launcher.build_server_command(bad)


def test_command_starts_the_native_server_with_only_the_revision():
    launcher = _launcher()
    command = launcher.build_server_command(REVISION, python=sys.executable)
    assert command[0] == sys.executable
    # E28-2: the child runs the in-process host bootstrap, which provisions the
    # parse capability explicitly (design §3.2).
    assert command[1] == "-c" and "hosts.python.mcp_host" in command[2]
    assert "-m" not in command
    assert Path(command[3]) == SERVER_PATH
    assert command[4:] == [REVISION]  # no other datum crosses the boundary


def test_server_environment_is_a_fixed_allowlist(monkeypatch):
    launcher = _launcher()
    monkeypatch.setenv("SECRET_TOKEN_SENTINEL", "s3cr3t")
    monkeypatch.setenv("GENIA_ANYTHING", "1")
    monkeypatch.setenv("HOME", "/home/sentinel")
    env = launcher.server_environment(dict(os.environ))
    assert set(env) <= ALLOWED_ENV_KEYS
    assert "SECRET_TOKEN_SENTINEL" not in env and "HOME" not in env
    assert all("s3cr3t" not in value for value in env.values())


def test_server_environment_keeps_the_dynamic_loader_path(monkeypatch):
    # A shared-library Python (for example actions/setup-python on a self-hosted
    # runner) cannot start without its loader path: it is launch plumbing only.
    launcher = _launcher()
    monkeypatch.setenv("LD_LIBRARY_PATH", "/opt/python/lib")
    monkeypatch.setenv("DYLD_LIBRARY_PATH", "/opt/python/lib")
    env = launcher.server_environment(dict(os.environ))
    assert env["LD_LIBRARY_PATH"] == "/opt/python/lib"
    assert env["DYLD_LIBRARY_PATH"] == "/opt/python/lib"


def test_launcher_end_to_end_reports_the_repository_revision():
    _launcher()
    expected = _git(REPO_ROOT, "rev-parse", "HEAD")
    completed = subprocess.run(
        [sys.executable, "-m", "hosts.python.mcp_launch"],
        input=encode(request("tools/call", 1, {"name": "genia_capabilities"})) + b"\n",
        capture_output=True,
        cwd=str(REPO_ROOT),
        env=server_env(),
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    (frame,) = frames(completed.stdout)
    message = json.loads(frame.decode("utf-8"))
    assert message["result"]["structuredContent"] == expected_envelope(
        expected, tools=("genia_capabilities", "genia_parse", "genia_run")
    )
    assert completed.stderr == b""


def test_launcher_startup_failure_writes_nothing_to_stdout(tmp_path):
    launcher = _launcher()
    not_a_repo = tmp_path / "plain"
    not_a_repo.mkdir()
    with pytest.raises(launcher.McpLaunchError):
        launcher.build_server_command(launcher.resolve_contract_revision(not_a_repo))
