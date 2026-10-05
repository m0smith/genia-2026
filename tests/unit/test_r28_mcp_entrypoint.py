"""R28 E28-6 (issue #707): the supported executable entrypoint and the packaging decision.

`scripts/genia-mcp` starts the same launcher the checked-in `.mcp.json` starts, from any working
directory, with no arguments. It is a thin shell wrapper: it adds no CLI command, no Genia
semantics, no authority, and no packaging claim (the wheel, the `genia` CLI, and
`pyproject.toml` are unchanged). Python-host / OS tests (subprocess, file modes).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tomllib

import pytest

from tests.fixtures.r28_mcp_helpers import (
    REPO_ROOT,
    RUN_TOOLS,
    client_environment,
    encode,
    frames,
    request,
    run_request,
)

pytestmark = pytest.mark.unit

SCRIPT = REPO_ROOT / "scripts" / "genia-mcp"


def _session(tmp_path, lines, args=()):
    return subprocess.run(
        [str(SCRIPT), *args],
        input=b"".join(encode(m) + b"\n" for m in lines),
        capture_output=True,
        cwd=str(tmp_path),  # deliberately not the repository root
        env=client_environment(),
        timeout=120,
    )


def _need_uv():
    import shutil

    if shutil.which("uv", path=client_environment().get("PATH")) is None:
        if os.environ.get("CI"):
            pytest.fail("uv is required")
        pytest.skip("uv is not on PATH here")


def test_the_entrypoint_is_an_executable_posix_shell_script():
    assert SCRIPT.is_file() and os.access(SCRIPT, os.X_OK)
    text = SCRIPT.read_text(encoding="utf-8")
    assert text.startswith("#!/bin/sh\n")
    assert "hosts/python/mcp_launch.py" in text


def test_the_entrypoint_adds_no_authority_secret_url_or_machine_detail():
    text = SCRIPT.read_text(encoding="utf-8")
    assert not re.search(r"https?://|token|secret|password|/home/|/Users/|HOME=|export ", text, re.I)
    assert "env " not in text and "eval " not in text


def test_the_entrypoint_works_from_any_working_directory(tmp_path):
    _need_uv()
    done = _session(tmp_path, [request("tools/list", 1), run_request("6 * 7", 2)])
    assert done.returncode == 0, done.stderr.decode()
    out = [json.loads(frame) for frame in frames(done.stdout)]
    assert [t["name"] for t in out[0]["result"]["tools"]] == list(RUN_TOOLS)
    assert out[1]["result"]["structuredContent"]["result"]["value"]["rendered"] == "42"
    assert done.stderr == b""  # stdout carries frames only; nothing leaks to stderr


def test_the_entrypoint_takes_no_arguments(tmp_path):
    done = _session(tmp_path, [], args=("--anything",))
    assert done.returncode == 2 and done.stdout == b""
    assert done.stderr.strip() == b"genia-mcp: takes no arguments"


def test_the_entrypoint_and_the_checked_in_configuration_start_the_same_launcher():
    config = json.loads((REPO_ROOT / ".mcp.json").read_text(encoding="utf-8"))
    args = config["mcpServers"]["genia"]["args"]
    assert args[-1] == "hosts/python/mcp_launch.py"
    assert "hosts/python/mcp_launch.py" in SCRIPT.read_text(encoding="utf-8")


def test_packaging_is_unchanged_no_new_cli_command_and_no_published_package_claim():
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["scripts"] == {"genia": "genia.interpreter:_main"}
    assert data["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == ["src/genia"]
    assert not (REPO_ROOT / "server.json").exists()  # no registry metadata for an unpublished package
    assert not (REPO_ROOT / "package.json").exists()
