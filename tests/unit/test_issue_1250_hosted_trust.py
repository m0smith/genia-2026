"""Mocked GitHub provenance and independent receipt tests; never hosted verification."""

import base64
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib
import json
from pathlib import Path
import zipfile
import io

import pytest


def trust():
    """Load the new trust interface lazily for bounded preimplementation RED."""
    return importlib.import_module("tools.issue_1250.hosted_trust")


def synthetic_policy(expected, reviewers):
    """Model a separately verified policy for focused legacy receipt/snapshot tests.

    Main-policy authentication and complete contributor checks are exercised by
    test_issue_1250_controller; these existing tests retain their original oracles.
    """
    module = trust()
    return module.VerifiedPolicy(frozenset(reviewers), frozenset({10, 30, 31}),
                                 "d" * 64, expected["commit_sha"], 55, module._VERIFIED)


class FakeAPI:
    """Return deep copies of authoritative-API-shaped fixtures, no network credentials."""

    def __init__(self, values):
        """Initialize isolated response fixtures and an empty read-call ledger."""
        self.values = values
        self.calls = []

    def json(self, path):
        """Retain requested read endpoints and reject any unexpected lookup."""
        self.calls.append(path)
        return deepcopy(self.values[path])


@pytest.fixture
def hosted():
    """Create synthetic exact-source successful API metadata; no real run is referenced."""
    now = datetime.now(timezone.utc)
    sha, tree = "a" * 40, "b" * 40
    workflow = (
        Path(__file__).resolve().parents[2] / ".github/workflows/issue-1250-qualification.yml"
    ).read_bytes()
    expected = {
        "repository": "m0smith/genia-2026",
        "workflow_id": 5,
        "workflow_path": ".github/workflows/issue-1250-qualification.yml",
        "workflow_sha": sha,
        "workflow_sha256": hashlib.sha256(workflow).hexdigest(),
        "commit_sha": sha,
        "tree_sha": tree,
        "run_id": 41,
        "attempt": 1,
        "artifact_id": 7,
        "artifact_name": "issue-1250-qualification-41-1",
        "artifact_sha256": "c" * 64,
        "manifest_sha256": "d" * 64,
        "proposal_sha256": "e" * 64,
        "build_evidence_sha256": "f" * 64,
        "require_attestation": False,
    }
    from tools.issue_1250 import approval_validation

    pinned = approval_validation.inputs()
    expected["proposal_sha256"] = pinned["registration_sha256"]
    expected["build_evidence_sha256"] = pinned["build"]["evidence_sha256"]
    expected["runtime_lock_sha256"] = pinned["runtime"]["lock_sha256"]
    expected["build_requirements_sha256"] = pinned["build"]["requirements_sha256"]
    prefix = "/repos/m0smith/genia-2026"
    run = {
        "id": 41,
        "run_attempt": 1,
        "repository": {"id": 99, "full_name": expected["repository"]},
        "head_repository": {"id": 99, "full_name": expected["repository"]},
        "head_sha": sha,
        "workflow_id": 5,
        "path": expected["workflow_path"],
        "event": "workflow_dispatch",
        "status": "completed",
        "conclusion": "success",
        "actor": {"login": "collector", "id": 40},
        "triggering_actor": {"login": "collector", "id": 41},
        "run_started_at": (now - timedelta(minutes=5)).isoformat(),
        "updated_at": (now - timedelta(minutes=1)).isoformat(),
    }
    artifact = {
        "id": 7,
        "name": expected["artifact_name"],
        "expired": False,
        "size_in_bytes": 100,
        "digest": "sha256:" + expected["artifact_sha256"],
        "created_at": (now - timedelta(minutes=2)).isoformat(),
        "workflow_run": {"id": 41, "repository_id": 99, "head_repository_id": 99, "head_sha": sha},
    }
    job = {
        "id": 17,
        "name": "Cold dependency qualification",
        "run_id": 41,
        "head_sha": sha,
        "status": "completed",
        "conclusion": "success",
        "runner_id": 123,
        "runner_name": "GitHub Actions 123",
        "runner_group_name": "GitHub Actions",
        "labels": ["ubuntu-24.04"],
        "steps": [
            {
                "name": "Mandatory real cold-cache integration",
                "status": "completed",
                "conclusion": "success",
            }
        ],
    }
    values = {
        prefix: {"id": 99, "full_name": expected["repository"]},
        prefix + "/actions/runs/41": run,
        prefix + "/actions/runs/41/attempts/1": deepcopy(run),
        prefix + "/actions/workflows/5": {
            "id": 5,
            "path": expected["workflow_path"],
            "state": "active",
        },
        prefix + "/commits/" + sha: {
            "sha": sha,
            "commit": {"tree": {"sha": tree}},
            "author": {"login": "source-author"},
        },
        prefix + "/contents/" + expected["workflow_path"] + "?ref=" + sha: {
            "type": "file",
            "encoding": "base64",
            "content": base64.b64encode(workflow).decode(),
            "sha": hashlib.sha1(
                b"blob " + str(len(workflow)).encode() + b"\0" + workflow
            ).hexdigest(),
        },
        prefix + "/actions/runs/41/attempts/1/jobs?per_page=100": {"total_count": 1, "jobs": [job]},
        prefix + "/actions/runs/41/artifacts?per_page=100": {
            "total_count": 1,
            "artifacts": [artifact],
        },
    }
    return expected, FakeAPI(values), now


def test_authoritative_metadata_binds_exact_manual_run(hosted):
    expected, api, now = hosted
    proof = trust().verify_metadata(api, expected, now=now)
    assert proof["commit_sha"] == expected["commit_sha"]
    assert proof["tree_sha"] == expected["tree_sha"]
    assert proof["artifact_sha256"] == expected["artifact_sha256"]


@pytest.mark.parametrize(
    "change",
    [
        "repository",
        "workflow",
        "workflow-bytes",
        "commit",
        "tree",
        "run",
        "attempt",
        "failed",
        "incomplete",
        "nonmanual",
        "reusable-workflow",
        "fork",
        "artifact-id",
        "artifact-name",
        "artifact-digest",
        "no-digest",
        "expired",
        "stale",
        "ambiguous",
        "wrong-artifact-run",
        "job-failure",
        "skipped-test",
        "self-hosted",
        "attestation-required",
        "api-error",
    ],
)
def test_wrong_or_insufficient_api_provenance_fails_closed(hosted, change):
    expected, api, now = hosted
    p = "/repos/m0smith/genia-2026"
    run = api.values[p + "/actions/runs/41/attempts/1"]
    artifact = api.values[p + "/actions/runs/41/artifacts?per_page=100"]["artifacts"][0]
    job = api.values[p + "/actions/runs/41/attempts/1/jobs?per_page=100"]["jobs"][0]
    if change == "repository":
        api.values[p]["full_name"] = "attacker/repo"
    elif change == "workflow":
        run["workflow_id"] = 6
    elif change == "workflow-bytes":
        expected["workflow_sha256"] = "0" * 64
    elif change == "commit":
        run["head_sha"] = "0" * 40
    elif change == "tree":
        api.values[p + "/commits/" + expected["commit_sha"]]["commit"]["tree"]["sha"] = "0" * 40
    elif change == "run":
        run["id"] = 42
    elif change == "attempt":
        run["run_attempt"] = 2
    elif change == "failed":
        run["conclusion"] = "failure"
    elif change == "incomplete":
        run["status"] = "in_progress"
    elif change == "nonmanual":
        run["event"] = "pull_request"
    elif change == "reusable-workflow":
        run["referenced_workflows"] = [{"sha": "0" * 40}]
    elif change == "fork":
        run["head_repository"]["id"] = 100
    elif change == "artifact-id":
        artifact["id"] = 8
    elif change == "artifact-name":
        artifact["name"] = "other"
    elif change == "artifact-digest":
        artifact["digest"] = "sha256:" + "0" * 64
    elif change == "no-digest":
        artifact.pop("digest")
    elif change == "expired":
        artifact["expired"] = True
    elif change == "stale":
        artifact["created_at"] = (now - timedelta(days=2)).isoformat()
    elif change == "ambiguous":
        api.values[p + "/actions/runs/41/artifacts?per_page=100"]["artifacts"].append(
            deepcopy(artifact)
        )
        api.values[p + "/actions/runs/41/artifacts?per_page=100"]["total_count"] = 2
    elif change == "wrong-artifact-run":
        artifact["workflow_run"]["id"] = 42
    elif change == "job-failure":
        job["conclusion"] = "failure"
    elif change == "skipped-test":
        job["steps"][0]["conclusion"] = "skipped"
    elif change == "self-hosted":
        job["labels"].append("self-hosted")
    elif change == "attestation-required":
        expected["require_attestation"] = True
    elif change == "api-error":
        api.values.clear()
    with pytest.raises(RuntimeError, match="hosted provenance rejected"):
        trust().verify_metadata(api, expected, now=now)


def test_independent_receipt_requires_api_approval_of_canonical_payload(hosted):
    expected, api, now = hosted
    module = trust()
    proof = module.verify_metadata(api, expected, now=now)
    receipt = {
        **expected,
        "status": "APPROVED",
        "scope": "dependency-baseline-activation",
        "reviewer": 20,
        "expires_utc": (now + timedelta(hours=1)).isoformat(),
        "review": {"pull_number": 1318, "id": 88},
    }
    api.values["/repos/m0smith/genia-2026/pulls/1318/reviews/88"] = {
        "id": 88,
        "state": "APPROVED",
        "commit_id": expected["commit_sha"],
        "user": {"login": "independent-reviewer", "id": 20},
        "submitted_at": now.isoformat(),
        "body": "ISSUE1250-APPROVAL sha256:" + module.receipt_digest(receipt),
    }
    assert (
        module.verify_receipt(api, receipt, proof, synthetic_policy(expected, {20}), now=now)["status"]
        == "APPROVED"
    )


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "pending",
        "self-issued",
        "unknown-reviewer",
        "wrong-commit",
        "wrong-tree",
        "wrong-artifact",
        "wrong-manifest",
        "expired",
        "bad-reference",
        "comment-only",
        "bad-marker",
        "api-error",
    ],
)
def test_untrusted_receipts_never_authorize(hosted, change):
    expected, api, now = hosted
    module = trust()
    proof = module.verify_metadata(api, expected, now=now)
    receipt = {
        **expected,
        "status": "APPROVED",
        "scope": "dependency-baseline-activation",
        "reviewer": 20,
        "expires_utc": (now + timedelta(hours=1)).isoformat(),
        "review": {"pull_number": 1318, "id": 88},
    }
    review = {
        "id": 88,
        "state": "APPROVED",
        "commit_id": expected["commit_sha"],
        "user": {"login": "independent-reviewer", "id": 20},
        "submitted_at": now.isoformat(),
        "body": "",
    }
    if change == "missing":
        receipt = None
    elif change == "pending":
        receipt["status"] = "PENDING"
    elif change == "self-issued":
        receipt["reviewer"] = review["user"]["id"] = 40
    elif change == "unknown-reviewer":
        receipt["reviewer"] = review["user"]["id"] = 999
    elif change == "wrong-commit":
        receipt["commit_sha"] = "0" * 40
    elif change == "wrong-tree":
        receipt["tree_sha"] = "0" * 40
    elif change == "wrong-artifact":
        receipt["artifact_id"] = 8
    elif change == "wrong-manifest":
        receipt["manifest_sha256"] = "0" * 64
    elif change == "expired":
        receipt["expires_utc"] = (now - timedelta(hours=1)).isoformat()
    elif change == "bad-reference":
        receipt["review"]["pull_number"] = 1
    elif change == "comment-only":
        review["state"] = "COMMENTED"
    review["body"] = "ISSUE1250-APPROVAL sha256:" + module.receipt_digest(receipt or {})
    if change == "bad-marker":
        review["body"] = "APPROVED (unbound)"
    if change != "api-error":
        api.values["/repos/m0smith/genia-2026/pulls/1318/reviews/88"] = review
    with pytest.raises(RuntimeError, match="approval receipt rejected"):
        module.verify_receipt(api, receipt, proof, synthetic_policy(expected, {20, 40}), now=now)


@pytest.fixture
def downloadable(hosted, tmp_path):
    """Complete synthetic hosted ZIP plus mocked API; not actual hosted execution."""
    from tests.unit import test_issue_1250_approval_validation as local

    fixture = tmp_path / "fixture"
    fixture.mkdir()
    module, root, _, _ = local.qualification.__wrapped__(fixture)
    expected, api, now = hosted
    report = json.loads((root / "integration.json").read_text())
    report["environment"].update(
        environment_class="github-hosted-ubuntu-24.04",
        os_release={"ID": "ubuntu", "VERSION_ID": "24.04"},
        hosted={
            "GITHUB_REPOSITORY": expected["repository"],
            "GITHUB_RUN_ID": "41",
            "GITHUB_RUN_ATTEMPT": "1",
            "GITHUB_SHA": expected["commit_sha"],
            "GITHUB_WORKFLOW_SHA": expected["workflow_sha"],
            "GITHUB_WORKFLOW_REF": expected["repository"]
            + "/"
            + expected["workflow_path"]
            + "@refs/heads/staged",
            "RUNNER_OS": "Linux",
            "RUNNER_ARCH": "X64",
            "ImageOS": "ubuntu24",
            "ImageVersion": "unit-fixture",
        },
    )
    (root / "integration.json").write_text(json.dumps(report))
    (root / "source-identity.json").write_text(
        json.dumps({k: expected[k] for k in ("commit_sha", "tree_sha", "workflow_sha256")})
    )
    (root / "collection-result.json").write_text(
        json.dumps({"rc": 0, "outcome": "PASS", "test_node": module.NODE})
    )
    (root / "junit.xml").write_text(
        '<testsuites><testsuite><testcase classname="tests.unit.test_issue_1250_build_backend" name="test_real_cold_baseline_and_candidate_provisioning"/></testsuite></testsuites>'
    )

    def seal():
        """Reseal synthetic altered content to test semantic verification past integrity checks."""
        module.manifest(root)
        expected["manifest_sha256"] = module.sha256(root / "manifest.json")
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
            for file in root.rglob("*"):
                if file.is_file():
                    archive.writestr(str(file.relative_to(root)), file.read_bytes())
        data = stream.getvalue()
        expected["artifact_sha256"] = hashlib.sha256(data).hexdigest()
        artifact = api.values["/repos/m0smith/genia-2026/actions/runs/41/artifacts?per_page=100"][
            "artifacts"
        ][0]
        artifact.update(digest="sha256:" + expected["artifact_sha256"], size_in_bytes=len(data))
        api.download = lambda path: data
        return data

    seal()
    yield expected, api, now, root, seal
    # The verifier returns immutable owned snapshots; allow pytest cleanup afterwards.
    for path in [tmp_path, *tmp_path.rglob("*")]:
        if not path.is_symlink():
            path.chmod(0o700 if path.is_dir() else 0o600)


def test_mocked_retrieval_checks_complete_hosted_binding(downloadable, tmp_path):
    expected, api, now, _, _ = downloadable
    module = trust()
    snapshot = module.retrieve(
        api, expected, tmp_path / "verified", tmp_path / "diagnostics", now=now
    )
    from tools.issue_1250 import approval_validation

    assert (
        approval_validation.require_qualification(
            snapshot.root,
            expected["manifest_sha256"],
            "github-hosted-ubuntu-24.04",
            now=now,
            hosted_snapshot=snapshot,
        )["outcome"]
        == "PASS"
    )
    assert (
        json.loads((tmp_path / "diagnostics/verification.json").read_text())["outcome"]
        == "VERIFIED_NOT_APPROVED"
    )


@pytest.mark.parametrize(
    "change",
    [
        "download-digest",
        "download-size",
        "source",
        "forged-env",
        "forged-sha",
        "forged-workflow-sha",
        "missing-junit",
        "skipped-junit",
        "failed-outcome",
        "source-fingerprint",
    ],
)
def test_retrieval_rejects_and_removes_untrusted_evidence(downloadable, tmp_path, change):
    expected, api, now, root, seal = downloadable
    if change == "download-digest":
        api.download = lambda path: b"corrupted"
    elif change == "download-size":
        api.values["/repos/m0smith/genia-2026/actions/runs/41/artifacts?per_page=100"]["artifacts"][
            0
        ]["size_in_bytes"] += 1
    else:
        if change == "source":
            value = json.loads((root / "source-identity.json").read_text())
            value["commit_sha"] = "0" * 40
            (root / "source-identity.json").write_text(json.dumps(value))
        elif change in {"forged-env", "forged-sha", "forged-workflow-sha", "source-fingerprint"}:
            value = json.loads((root / "integration.json").read_text())
            if change in {"forged-env", "forged-sha", "forged-workflow-sha"}:
                key = {
                    "forged-env": "GITHUB_RUN_ID",
                    "forged-sha": "GITHUB_SHA",
                    "forged-workflow-sha": "GITHUB_WORKFLOW_SHA",
                }[change]
                value["environment"]["hosted"][key] = "0" * 40
            else:
                value["sources"]["tools/issue_1250/run.py"] = "0" * 64
            (root / "integration.json").write_text(json.dumps(value))
        elif change == "missing-junit":
            (root / "junit.xml").unlink()
        elif change == "skipped-junit":
            (root / "junit.xml").write_text(
                '<testsuites><testcase name="test_real_cold_baseline_and_candidate_provisioning"><skipped/></testcase></testsuites>'
            )
        elif change == "failed-outcome":
            (root / "collection-result.json").write_text('{"rc":1,"outcome":"FAIL"}')
        seal()
    with pytest.raises(RuntimeError, match="retrieval rejected"):
        trust().retrieve(api, expected, tmp_path / "verified", tmp_path / "diagnostics", now=now)
    assert not (tmp_path / "verified").exists()
    assert json.loads((tmp_path / "diagnostics/verification.json").read_text())["outcome"] == "FAIL"


def test_forged_hosted_json_cannot_mint_independent_proof(downloadable):
    expected, _, now, root, _ = downloadable
    from tools.issue_1250 import approval_validation

    with pytest.raises(RuntimeError, match="API-verified"):
        approval_validation.require_qualification(
            root, expected["manifest_sha256"], "github-hosted-ubuntu-24.04", now=now
        )


def test_full_mocked_snapshot_approval_does_not_activate(downloadable, tmp_path, monkeypatch):
    expected, api, now, _, _ = downloadable
    module = trust()
    snapshot = module.retrieve(
        api, expected, tmp_path / "verified", tmp_path / "diagnostics", now=now
    )
    receipt = {
        **expected,
        "status": "APPROVED",
        "scope": "dependency-baseline-activation",
        "reviewer": 20,
        "expires_utc": (now + timedelta(hours=1)).isoformat(),
        "review": {"pull_number": 1318, "id": 88},
    }
    api.values["/repos/m0smith/genia-2026/pulls/1318/reviews/88"] = {
        "id": 88,
        "state": "APPROVED",
        "commit_id": expected["commit_sha"],
        "user": {"login": "independent-reviewer", "id": 20},
        "submitted_at": now.isoformat(),
        "body": "ISSUE1250-APPROVAL sha256:" + module.receipt_digest(receipt),
    }
    monkeypatch.setattr(
        module,
        "checkout_identity",
        lambda: {
            "commit_sha": expected["commit_sha"],
            "tree_sha": expected["tree_sha"],
            "status": "",
        },
    )
    assert (
        module.require_approved_snapshot(api, receipt, snapshot, synthetic_policy(expected, {20}), now=now)[
            "status"
        ]
        == "APPROVED"
    )
    from tools.issue_1250 import run

    assert run.APPROVED_DEPENDENCIES is None


def test_previous_diagnostics_are_never_overwritten(hosted, tmp_path):
    expected, api, now = hosted
    diagnostics = tmp_path / "diagnostics"
    diagnostics.mkdir()
    (diagnostics / "verification.json").write_text("previous failure")
    with pytest.raises(RuntimeError, match="previous evidence preserved"):
        trust().retrieve(api, expected, tmp_path / "verified", diagnostics, now=now)
    assert (diagnostics / "verification.json").read_text() == "previous failure"
    assert api.calls == [] and not (tmp_path / "verified").exists()


@pytest.mark.parametrize("change", ["commit_sha", "tree_sha", "status"])
def test_changed_staged_source_cannot_use_prior_approval(
    downloadable, tmp_path, monkeypatch, change
):
    expected, api, now, _, _ = downloadable
    module = trust()
    snapshot = module.retrieve(
        api, expected, tmp_path / "verified", tmp_path / "diagnostics", now=now
    )
    identity = {
        "commit_sha": expected["commit_sha"],
        "tree_sha": expected["tree_sha"],
        "status": "",
    }
    identity[change] = "changed"
    monkeypatch.setattr(module, "checkout_identity", lambda: identity)
    with pytest.raises(RuntimeError, match="changed code must requalify"):
        module.require_approved_snapshot(api, None, snapshot, synthetic_policy(expected, {20}), now=now)
