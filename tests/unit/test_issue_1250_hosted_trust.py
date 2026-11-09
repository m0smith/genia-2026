"""Mocked GitHub provenance and independent receipt tests; never hosted verification."""

import base64
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib
import json

import pytest


def trust():
    """Load the new trust interface lazily for bounded preimplementation RED."""
    return importlib.import_module("tools.issue_1250.hosted_trust")


class FakeAPI:
    """Return deep copies of authoritative-API-shaped fixtures, no network credentials."""
    def __init__(self, values):
        self.values = values
        self.calls = []

    def json(self, path):
        """Retain requested read endpoints and reject any unexpected lookup."""
        self.calls.append(path)
        return deepcopy(self.values[path])


@pytest.fixture
def hosted():
    now = datetime.now(timezone.utc)
    sha, tree = "a" * 40, "b" * 40
    workflow = b"name: issue-1250 test fixture\n"
    expected = {"repository": "m0smith/genia-2026", "workflow_id": 5,
        "workflow_path": ".github/workflows/issue-1250-qualification.yml", "workflow_sha": sha,
        "workflow_sha256": hashlib.sha256(workflow).hexdigest(), "commit_sha": sha, "tree_sha": tree,
        "run_id": 41, "attempt": 1, "artifact_id": 7, "artifact_name": "issue-1250-qualification-41-1",
        "artifact_sha256": "c" * 64, "manifest_sha256": "d" * 64,
        "proposal_sha256": "e" * 64, "build_evidence_sha256": "f" * 64, "require_attestation": False}
    prefix = "/repos/m0smith/genia-2026"
    run = {"id": 41, "run_attempt": 1, "repository": {"id": 99, "full_name": expected["repository"]},
        "head_repository": {"id": 99, "full_name": expected["repository"]}, "head_sha": sha,
        "workflow_id": 5, "path": expected["workflow_path"], "event": "workflow_dispatch",
        "status": "completed", "conclusion": "success", "actor": {"login": "collector"},
        "triggering_actor": {"login": "collector"},
        "run_started_at": (now - timedelta(minutes=5)).isoformat(), "updated_at": (now - timedelta(minutes=1)).isoformat()}
    artifact = {"id": 7, "name": expected["artifact_name"], "expired": False, "size_in_bytes": 100,
        "digest": "sha256:" + expected["artifact_sha256"], "created_at": (now - timedelta(minutes=2)).isoformat(),
        "workflow_run": {"id": 41, "repository_id": 99, "head_repository_id": 99, "head_sha": sha}}
    job = {"id": 17, "name": "Cold dependency qualification", "run_id": 41, "head_sha": sha,
        "status": "completed", "conclusion": "success", "runner_id": 123, "runner_name": "GitHub Actions 123",
        "runner_group_name": "GitHub Actions", "labels": ["ubuntu-24.04"],
        "steps": [{"name": "Mandatory real cold-cache integration", "status": "completed", "conclusion": "success"}]}
    values = {prefix: {"id": 99, "full_name": expected["repository"]},
        prefix + "/actions/runs/41": run,
        prefix + "/actions/runs/41/attempts/1": deepcopy(run),
        prefix + "/actions/workflows/5": {"id": 5, "path": expected["workflow_path"], "state": "active"},
        prefix + "/commits/" + sha: {"sha": sha, "commit": {"tree": {"sha": tree}}, "author": {"login": "source-author"}},
        prefix + "/contents/" + expected["workflow_path"] + "?ref=" + sha: {
            "type": "file", "encoding": "base64", "content": base64.b64encode(workflow).decode(),
            "sha": hashlib.sha1(b"blob " + str(len(workflow)).encode() + b"\0" + workflow).hexdigest()},
        prefix + "/actions/runs/41/attempts/1/jobs?per_page=100": {"total_count": 1, "jobs": [job]},
        prefix + "/actions/runs/41/artifacts?per_page=100": {"total_count": 1, "artifacts": [artifact]}}
    return expected, FakeAPI(values), now


def test_authoritative_metadata_binds_exact_manual_run(hosted):
    expected, api, now = hosted
    proof = trust().verify_metadata(api, expected, now=now)
    assert proof["commit_sha"] == expected["commit_sha"]
    assert proof["tree_sha"] == expected["tree_sha"]
    assert proof["artifact_sha256"] == expected["artifact_sha256"]


@pytest.mark.parametrize("change", ["repository", "workflow", "workflow-bytes", "commit", "tree", "run", "attempt",
    "failed", "incomplete", "nonmanual", "fork", "artifact-id", "artifact-name", "artifact-digest", "no-digest",
    "expired", "stale", "ambiguous", "wrong-artifact-run", "job-failure", "skipped-test", "self-hosted", "attestation-required", "api-error"])
def test_wrong_or_insufficient_api_provenance_fails_closed(hosted, change):
    expected, api, now = hosted
    p = "/repos/m0smith/genia-2026"
    run = api.values[p + "/actions/runs/41/attempts/1"]
    artifact = api.values[p + "/actions/runs/41/artifacts?per_page=100"]["artifacts"][0]
    job = api.values[p + "/actions/runs/41/attempts/1/jobs?per_page=100"]["jobs"][0]
    if change == "repository": api.values[p]["full_name"] = "attacker/repo"
    elif change == "workflow": run["workflow_id"] = 6
    elif change == "workflow-bytes": expected["workflow_sha256"] = "0" * 64
    elif change == "commit": run["head_sha"] = "0" * 40
    elif change == "tree": api.values[p + "/commits/" + expected["commit_sha"]]["commit"]["tree"]["sha"] = "0" * 40
    elif change == "run": run["id"] = 42
    elif change == "attempt": run["run_attempt"] = 2
    elif change == "failed": run["conclusion"] = "failure"
    elif change == "incomplete": run["status"] = "in_progress"
    elif change == "nonmanual": run["event"] = "pull_request"
    elif change == "fork": run["head_repository"]["id"] = 100
    elif change == "artifact-id": artifact["id"] = 8
    elif change == "artifact-name": artifact["name"] = "other"
    elif change == "artifact-digest": artifact["digest"] = "sha256:" + "0" * 64
    elif change == "no-digest": artifact.pop("digest")
    elif change == "expired": artifact["expired"] = True
    elif change == "stale": artifact["created_at"] = (now - timedelta(days=2)).isoformat()
    elif change == "ambiguous":
        api.values[p + "/actions/runs/41/artifacts?per_page=100"]["artifacts"].append(deepcopy(artifact))
        api.values[p + "/actions/runs/41/artifacts?per_page=100"]["total_count"] = 2
    elif change == "wrong-artifact-run": artifact["workflow_run"]["id"] = 42
    elif change == "job-failure": job["conclusion"] = "failure"
    elif change == "skipped-test": job["steps"][0]["conclusion"] = "skipped"
    elif change == "self-hosted": job["labels"].append("self-hosted")
    elif change == "attestation-required": expected["require_attestation"] = True
    elif change == "api-error": api.values.clear()
    with pytest.raises(RuntimeError, match="hosted provenance rejected"):
        trust().verify_metadata(api, expected, now=now)


def test_independent_receipt_requires_api_approval_of_canonical_payload(hosted):
    expected, api, now = hosted
    module = trust()
    proof = module.verify_metadata(api, expected, now=now)
    receipt = {**expected, "status": "APPROVED", "scope": "dependency-baseline-activation",
               "reviewer": "independent-reviewer", "expires_utc": (now + timedelta(hours=1)).isoformat(),
               "review": {"pull_number": 1318, "id": 88}}
    api.values["/repos/m0smith/genia-2026/pulls/1318/reviews/88"] = {
        "id": 88, "state": "APPROVED", "commit_id": expected["commit_sha"],
        "user": {"login": "independent-reviewer"}, "submitted_at": now.isoformat(),
        "body": "ISSUE1250-APPROVAL sha256:" + module.receipt_digest(receipt)}
    assert module.verify_receipt(api, receipt, proof, {"independent-reviewer"}, now=now)["status"] == "APPROVED"


@pytest.mark.parametrize("change", ["missing", "pending", "self-issued", "unknown-reviewer", "wrong-commit", "wrong-tree",
    "wrong-artifact", "wrong-manifest", "expired", "bad-reference", "comment-only", "bad-marker", "api-error"])
def test_untrusted_receipts_never_authorize(hosted, change):
    expected, api, now = hosted
    module = trust()
    proof = module.verify_metadata(api, expected, now=now)
    receipt = {**expected, "status": "APPROVED", "scope": "dependency-baseline-activation",
               "reviewer": "independent-reviewer", "expires_utc": (now + timedelta(hours=1)).isoformat(),
               "review": {"pull_number": 1318, "id": 88}}
    review = {"id": 88, "state": "APPROVED", "commit_id": expected["commit_sha"],
              "user": {"login": "independent-reviewer"}, "submitted_at": now.isoformat(), "body": ""}
    if change == "missing": receipt = None
    elif change == "pending": receipt["status"] = "PENDING"
    elif change == "self-issued": receipt["reviewer"] = review["user"]["login"] = "collector"
    elif change == "unknown-reviewer": receipt["reviewer"] = review["user"]["login"] = "stranger"
    elif change == "wrong-commit": receipt["commit_sha"] = "0" * 40
    elif change == "wrong-tree": receipt["tree_sha"] = "0" * 40
    elif change == "wrong-artifact": receipt["artifact_id"] = 8
    elif change == "wrong-manifest": receipt["manifest_sha256"] = "0" * 64
    elif change == "expired": receipt["expires_utc"] = (now - timedelta(hours=1)).isoformat()
    elif change == "bad-reference": receipt["review"]["pull_number"] = 1
    elif change == "comment-only": review["state"] = "COMMENTED"
    review["body"] = "ISSUE1250-APPROVAL sha256:" + module.receipt_digest(receipt or {})
    if change == "bad-marker": review["body"] = "APPROVED (unbound)"
    if change != "api-error": api.values["/repos/m0smith/genia-2026/pulls/1318/reviews/88"] = review
    with pytest.raises(RuntimeError, match="approval receipt rejected"):
        module.verify_receipt(api, receipt, proof, {"independent-reviewer", "collector"}, now=now)
