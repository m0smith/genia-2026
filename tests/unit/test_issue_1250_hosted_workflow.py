"""Static/manual workflow and mocked transport tests; no hosted collection or CI."""

import io
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/issue-1250-qualification.yml"


def workflow():
    """Read literal workflow keys without YAML 1.1 interpreting `on` as boolean."""
    return yaml.load(WORKFLOW.read_text(), Loader=yaml.BaseLoader)


def test_collection_workflow_is_manual_minimal_pinned_and_bounded():
    value = workflow()
    assert set(value["on"]) == {"workflow_dispatch"}
    assert value["permissions"] == {"contents": "read"}
    assert value["concurrency"]["cancel-in-progress"] == "false"
    job = value["jobs"]["qualification"]
    assert job["runs-on"] == "ubuntu-24.04" and int(job["timeout-minutes"]) == 25
    actions = [step for step in job["steps"] if "uses" in step]
    assert len(actions) == 2
    assert all(re.fullmatch(r"actions/[a-z-]+@[0-9a-f]{40}", step["uses"]) for step in actions)
    assert actions[0]["with"]["persist-credentials"] == "false"
    assert actions[1]["with"]["retention-days"] == "30" and actions[1]["if"] == "always()"
    mandatory = next(step for step in job["steps"] if step["name"] == "Mandatory real cold-cache integration")
    assert "if" not in mandatory and "hosted_collection collect" in mandatory["run"]
    assert "run.py" not in str(job) and "workflow_run" not in value["on"]


@pytest.mark.parametrize("change", [None, "repo", "event", "sha", "workflow-sha", "attempt", "authorization"])
def test_precheckout_guard_never_runs_collection(tmp_path, change):
    env = {**os.environ, "RUNNER_TEMP": str(tmp_path), "GITHUB_REPOSITORY": "m0smith/genia-2026",
           "GITHUB_EVENT_NAME": "workflow_dispatch", "REQUESTED_SHA": "a" * 40,
           "GITHUB_SHA": "a" * 40, "GITHUB_WORKFLOW_SHA": "a" * 40,
           "GITHUB_RUN_ATTEMPT": "1", "AUTHORIZED": "true"}
    if change:
        key = {"repo": "GITHUB_REPOSITORY", "event": "GITHUB_EVENT_NAME", "sha": "GITHUB_SHA",
               "workflow-sha": "GITHUB_WORKFLOW_SHA", "attempt": "GITHUB_RUN_ATTEMPT",
               "authorization": "AUTHORIZED"}[change]
        env[key] = "wrong"
    script = workflow()["jobs"]["qualification"]["steps"][0]["run"]
    result = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True)
    assert (result.returncode == 0) is (change is None)
    record = json.loads((tmp_path / "issue1250-hosted/diagnostics/dispatch.json").read_text())
    assert record["outcome"] == ("PASS" if change is None else "FAIL")
    assert not (tmp_path / "issue1250-hosted/qualification").exists()


def test_python_archive_corruption_stops_before_install(tmp_path, monkeypatch):
    from tools.issue_1250 import hosted_collection
    monkeypatch.setattr(hosted_collection.urllib.request, "urlopen", lambda *args, **kwargs: io.BytesIO(b"corrupted"))
    calls = []
    monkeypatch.setattr(hosted_collection.subprocess, "run", lambda *args, **kwargs: calls.append(args))
    with pytest.raises(RuntimeError, match="CPython distribution digest"):
        hosted_collection.bootstrap_python(tmp_path / "python")
    assert calls == []


def test_failed_collection_cannot_publish_pass(tmp_path):
    from tools.issue_1250 import hosted_collection
    output = tmp_path / "qualification"
    output.mkdir()
    (output / "collection-result.json").write_text('{"outcome":"PASS","rc":0}')
    hosted_collection.publish(tmp_path, "failure")
    assert json.loads((output / "collection-result.json").read_text())["outcome"] == "FAIL"
    assert (output / "manifest.json").is_file()


@pytest.mark.parametrize("trusted", [True, False])
def test_api_token_never_forwarded_to_artifact_storage(monkeypatch, trusted):
    from tools.issue_1250 import hosted_trust
    calls = []
    location = "https://production.blob.core.windows.net/artifact?sig=private" if trusted else "https://evil.invalid/artifact"

    class Opener:
        """In-memory 302 transport; no network traffic or real credentials."""
        def open(self, request, timeout):
            """Assert the API request uses auth and the storage request has none."""
            calls.append(request)
            if len(calls) == 1:
                assert request.get_header("Authorization") == "Bearer UNIT-SECRET"
                raise urllib.error.HTTPError(request.full_url, 302, "redirect", {"Location": location}, None)
            assert request.get_header("Authorization") is None
            return io.BytesIO(b"unit artifact")

    client = hosted_trust.GitHubReadOnly("UNIT-SECRET")
    client._opener = Opener()
    if trusted:
        assert client.download("/repos/m0smith/genia-2026/actions/artifacts/7/zip") == b"unit artifact"
        assert len(calls) == 2
    else:
        with pytest.raises(RuntimeError, match="download failed") as caught:
            client.download("/repos/m0smith/genia-2026/actions/artifacts/7/zip")
        assert len(calls) == 1 and "private" not in str(caught.value)


def test_candidate_authorization_file_cannot_start_retrieval(tmp_path, monkeypatch):
    from tools.issue_1250 import hosted_trust
    calls = []
    monkeypatch.setattr(hosted_trust, "GitHubReadOnly", lambda *args: calls.append(args))
    with pytest.raises(RuntimeError, match="outside candidate"):
        hosted_trust.main(["--authorization", str(ROOT / "tools/issue_1250/registration-proposal.json"),
                           "--destination", str(tmp_path / "evidence"), "--diagnostics", str(tmp_path / "diagnostics")])
    assert calls == []
