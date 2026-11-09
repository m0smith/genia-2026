"""Independent read-only GitHub provenance and approval checks for #1250.

Run this reviewed verifier in the trusted controller before any subject process.
Reviewer authority comes from main policy pinned by the dispatch, not artifacts.
GitHub HTTPS/API metadata and server ZIP digest are the default trust root;
required attestations fail closed until a cryptographic verifier is implemented.
Nothing here dispatches, installs, changes registration or activates a baseline.
"""

from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from . import approval_validation as qualification
from . import hosted_archive

REPOSITORY = "m0smith/genia-2026"
WORKFLOW_PATH = ".github/workflows/issue-1250-qualification.yml"
AUTH_FIELDS = (
    "repository",
    "workflow_id",
    "workflow_path",
    "workflow_sha",
    "workflow_sha256",
    "commit_sha",
    "tree_sha",
    "run_id",
    "attempt",
    "artifact_id",
    "artifact_name",
    "artifact_sha256",
    "manifest_sha256",
    "proposal_sha256",
    "build_evidence_sha256",
    "runtime_lock_sha256",
    "build_requirements_sha256",
    "require_attestation",
)
_VERIFIED = object()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Prevent automatic forwarding of GitHub API Authorization to storage hosts."""

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        """Return no redirect request; the caller handles an authenticated 302 safely."""
        return None


class GitHubReadOnly:
    """Bounded GET-only API client; tokens are never logged, serialized or forwarded."""

    def __init__(self, token):
        """Bind an operator-configured read-only token to a non-redirecting GET client."""
        if not token or "\n" in token:
            raise RuntimeError("explicit read-only GitHub credential required")
        self._token = token
        self._opener = urllib.request.build_opener(NoRedirect())

    def close(self):
        """Drop all credential-bearing client references before subject execution."""
        self._token = None
        self._opener = None

    def _get(self, path, limit):
        """Read fixed-repository API bytes with no redirects or unbounded responses."""
        if not path.startswith("/repos/" + REPOSITORY + "/") and path != "/repos/" + REPOSITORY:
            raise RuntimeError("unregistered GitHub API path")
        if self._token is None or self._opener is None:
            raise RuntimeError("GitHub client is closed")
        request = urllib.request.Request(
            "https://api.github.com" + path,
            headers={
                "Authorization": "Bearer " + self._token,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "issue-1250-independent-verifier",
            },
        )
        with self._opener.open(request, timeout=30) as response:
            data = response.read(limit + 1)
        if len(data) > limit:
            raise RuntimeError("GitHub response size limit exceeded")
        return data

    def json(self, path):
        """Read bounded authoritative JSON; redact transport errors and signed URLs."""
        try:
            return json.loads(self._get(path, 2 * 1024**2))
        except Exception:
            raise RuntimeError("GitHub metadata read failed") from None

    def download(self, path, limit=32 * 1024**2):
        """Download only an explicit artifact endpoint, stripping auth on storage GET."""
        if not re.fullmatch(r"/repos/m0smith/genia-2026/actions/artifacts/[1-9][0-9]*/zip", path):
            raise RuntimeError("unregistered artifact download endpoint")
        try:
            try:
                return self._get(path, limit)
            except urllib.error.HTTPError as redirect:
                if redirect.code != 302:
                    raise RuntimeError("artifact API failed") from None
                location = redirect.headers["Location"]
            parsed = urllib.parse.urlsplit(location)
            if (
                parsed.scheme != "https"
                or parsed.username
                or parsed.password
                or parsed.port not in {None, 443}
                or not parsed.hostname
                or not (
                    parsed.hostname.endswith(".blob.core.windows.net")
                    or parsed.hostname.endswith(".actions.githubusercontent.com")
                )
                or parsed.fragment
            ):
                raise RuntimeError("untrusted artifact redirect")
            # New request has no token; further redirects are forbidden.
            with self._opener.open(urllib.request.Request(location), timeout=30) as response:
                data = response.read(limit + 1)
            if len(data) > limit:
                raise RuntimeError("artifact download size limit exceeded")
            return data
        except Exception:
            raise RuntimeError("GitHub artifact download failed") from None


def verify_metadata(api, expected, *, now=None):
    """Bind an explicit authorized tuple to GitHub's repo/run/job/artifact metadata.

    Only a completed successful attempt-1 manual run of the reviewed workflow at
    the exact source revision is accepted. No branch-name or environment claim
    replaces these checks. Artifact ambiguity, missing digest or API errors reject.
    """
    try:
        current = now or datetime.now(timezone.utc)
        if set(expected) != set(AUTH_FIELDS):
            raise ValueError("strict external authorization fields required")
        if expected["repository"] != REPOSITORY or expected["workflow_path"] != WORKFLOW_PATH:
            raise ValueError("wrong repository/workflow authorization")
        for field in ("workflow_id", "run_id", "attempt", "artifact_id"):
            if type(expected[field]) is not int or expected[field] <= 0:
                raise ValueError("invalid authorized numeric identity")
        for field in ("commit_sha", "tree_sha", "workflow_sha"):
            if not re.fullmatch(r"[0-9a-f]{40}", expected[field]):
                raise ValueError("immutable source/workflow identity required")
        for field in (
            "workflow_sha256",
            "artifact_sha256",
            "manifest_sha256",
            "proposal_sha256",
            "build_evidence_sha256",
            "runtime_lock_sha256",
            "build_requirements_sha256",
        ):
            if not re.fullmatch(r"[0-9a-f]{64}", expected[field]):
                raise ValueError("explicit reviewed digest required")
        if expected["attempt"] != 1 or expected["workflow_sha"] != expected["commit_sha"]:
            raise ValueError("only exact-source attempt-1 workflow supported")
        if expected["require_attestation"] is not False:
            raise ValueError("required cryptographic attestation verification is unsupported; stop")
        p = "/repos/" + REPOSITORY
        repo = api.json(p)
        latest = api.json(f"{p}/actions/runs/{expected['run_id']}")
        run = api.json(f"{p}/actions/runs/{expected['run_id']}/attempts/{expected['attempt']}")
        workflow = api.json(f"{p}/actions/workflows/{expected['workflow_id']}")
        commit = api.json(f"{p}/commits/{expected['commit_sha']}")
        definition = api.json(f"{p}/contents/{WORKFLOW_PATH}?ref={expected['workflow_sha']}")
        if (
            repo["full_name"] != REPOSITORY
            or workflow["id"] != expected["workflow_id"]
            or workflow["path"] != WORKFLOW_PATH
            or workflow["state"] != "active"
            or commit["sha"] != expected["commit_sha"]
            or commit["commit"]["tree"]["sha"] != expected["tree_sha"]
        ):
            raise ValueError("repository/workflow/commit metadata mismatch")
        for observed in (latest, run):
            if (
                observed["id"] != expected["run_id"]
                or observed["run_attempt"] != expected["attempt"]
                or observed["head_sha"] != expected["commit_sha"]
                or observed["workflow_id"] != workflow["id"]
                or observed["path"].split("@")[0] != WORKFLOW_PATH
                or observed["event"] != "workflow_dispatch"
                or observed.get("referenced_workflows")
                or observed["status"] != "completed"
                or observed["conclusion"] != "success"
                or observed["repository"]["id"] != repo["id"]
                or observed["repository"]["full_name"] != REPOSITORY
                or observed["head_repository"]["id"] != repo["id"]
                or observed["head_repository"]["full_name"] != REPOSITORY
            ):
                raise ValueError("wrong/incomplete/failed manual run or attempt")
        raw = base64.b64decode("".join(definition["content"].split()), validate=True)
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if (
            definition["type"] != "file"
            or definition["encoding"] != "base64"
            or definition["sha"] != blob
            or hashlib.sha256(raw).hexdigest() != expected["workflow_sha256"]
        ):
            raise ValueError("immutable workflow bytes mismatch")
        jobs = api.json(
            f"{p}/actions/runs/{expected['run_id']}/attempts/{expected['attempt']}/jobs?per_page=100"
        )
        if jobs["total_count"] != 1 or len(jobs["jobs"]) != 1:
            raise ValueError("ambiguous qualification job")
        job = jobs["jobs"][0]
        mandatory = [
            s for s in job["steps"] if s["name"] == "Mandatory real cold-cache integration"
        ]
        if (
            job["name"] != "Cold dependency qualification"
            or job["run_id"] != expected["run_id"]
            or job["head_sha"] != expected["commit_sha"]
            or job["status"] != "completed"
            or job["conclusion"] != "success"
            or "ubuntu-24.04" not in job["labels"]
            or "self-hosted" in job["labels"]
            or job["runner_group_name"] != "GitHub Actions"
            or not job["runner_id"]
            or not job["runner_name"]
            or len(mandatory) != 1
            or mandatory[0]["status"] != "completed"
            or mandatory[0]["conclusion"] != "success"
        ):
            raise ValueError("hosted runner or mandatory integration step not verified")
        listing = api.json(f"{p}/actions/runs/{expected['run_id']}/artifacts?per_page=100")
        if listing["total_count"] != 1 or len(listing["artifacts"]) != 1:
            raise ValueError("ambiguous or missing qualification artifact")
        artifact = listing["artifacts"][0]
        origin = artifact["workflow_run"]
        if (
            artifact["id"] != expected["artifact_id"]
            or artifact["name"] != expected["artifact_name"]
            or artifact["name"]
            != f"issue-1250-qualification-{expected['run_id']}-{expected['attempt']}"
            or artifact["expired"] is not False
            or not 0 < artifact["size_in_bytes"] <= 32 * 1024**2
            or artifact["digest"] != "sha256:" + expected["artifact_sha256"]
            or origin["id"] != expected["run_id"]
            or origin["head_sha"] != expected["commit_sha"]
            or origin["repository_id"] != repo["id"]
            or origin["head_repository_id"] != repo["id"]
        ):
            raise ValueError("artifact identity/digest/origin mismatch")
        created = datetime.fromisoformat(artifact["created_at"].replace("Z", "+00:00"))
        started = datetime.fromisoformat(run["run_started_at"].replace("Z", "+00:00"))
        completed = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
        if not (
            current - timedelta(hours=24)
            <= started
            <= created
            <= completed + timedelta(minutes=5)
            <= current + timedelta(minutes=5)
        ):
            raise ValueError("stale or inconsistent API provenance")
        return {
            **{key: expected[key] for key in AUTH_FIELDS},
            "repository_id": repo["id"],
            "artifact_size": artifact["size_in_bytes"],
            "collectors": [run["actor"]["login"], run["triggering_actor"]["login"]],
            "source_author": (commit.get("author") or {}).get("login"),
            "collector_ids": [numeric_id(run["actor"]), numeric_id(run["triggering_actor"])],
            "completed_utc": run["updated_at"],
            "runner_id": job["runner_id"],
            "runner_name": job["runner_name"],
            "api_verified": True,
        }
    except Exception as error:
        raise RuntimeError("hosted provenance rejected: " + str(error)) from None


BASE_SHA = "9f96c6d9369bc29b87d6f63a97b3f7ce89bb7e05"
POLICY_PATH = "tools/issue_1250/reviewer-policy.json"
ACCEPTANCE_PATH = ".github/workflows/issue-1250-acceptance.yml"


def numeric_id(value):
    """Reject missing, ambiguous or boolean GitHub numeric account identities."""
    identity = value["id"]
    if type(identity) is not int or identity <= 0:
        raise ValueError("unambiguous numeric GitHub user ID required")
    return identity


@dataclass(frozen=True)
class VerifiedPolicy:
    """Process-local policy proof bound to main bytes and this dispatch/source."""

    reviewer_ids: frozenset
    excluded_ids: frozenset
    digest: str
    commit_sha: str
    run_id: int
    _seal: object


def policy_bytes(api, digest):
    """Fetch only main's exact pinned policy bytes, verifying the Git blob too."""
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("independently supplied policy SHA-256 required")
    definition = api.json(f"/repos/{REPOSITORY}/contents/{POLICY_PATH}?ref=main")
    raw = base64.b64decode("".join(definition["content"].split()), validate=True)
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if (definition["type"] != "file" or definition["encoding"] != "base64"
            or definition["sha"] != blob or hashlib.sha256(raw).hexdigest() != digest):
        raise ValueError("main policy bytes changed or mismatched")
    return json.loads(raw)


def verify_authority(api, digest, run_id, commit_sha):
    """Authenticate main policy, dispatch maintainer and complete base..S accounts.

    Compare pagination is bounded to 1000 commits. All pages must agree on the
    total and base; missing/unmapped authors or committers reject, never omit an
    identity. Enrollment attestation covers co-author trailers and independence.
    """
    try:
        policy = policy_bytes(api, digest)
        if (set(policy) != {"schema", "repository", "base_sha", "maintainers", "reviewers"}
                or policy["schema"] != 1 or policy["repository"] != REPOSITORY
                or policy["base_sha"] != BASE_SHA):
            raise ValueError("invalid main policy contract")
        maintainers = [numeric_id(v) for v in policy["maintainers"]]
        reviewers = [numeric_id(v) for v in policy["reviewers"]]
        if (not maintainers or not reviewers or len(maintainers) != len(set(maintainers))
                or len(reviewers) != len(set(reviewers))):
            raise ValueError("missing or duplicate enrolled identities")
        for member in [*policy["maintainers"], *policy["reviewers"]]:
            if not isinstance(member["login"], str) or not member["login"]:
                raise ValueError("enrollment login required for audit")
        for reviewer in policy["reviewers"]:
            if (reviewer["enrolled_by"] not in maintainers
                    or reviewer["independence_attested"] is not True
                    or not re.fullmatch(r"https://github.com/m0smith/genia-2026/issues/1250#issuecomment-[1-9][0-9]*", reviewer["authorization"])):
                raise ValueError("owner enrollment attestation required")
            if datetime.fromisoformat(reviewer["enrolled_utc"].replace("Z", "+00:00")).tzinfo is None:
                raise ValueError("timezone-aware enrollment date required")
        if type(run_id) is not int or run_id <= 0 or not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
            raise ValueError("explicit acceptance run/source required")
        p = "/repos/" + REPOSITORY
        dispatch = api.json(f"{p}/actions/runs/{run_id}")
        if (dispatch["id"] != run_id or dispatch["run_attempt"] != 1
                or dispatch["event"] != "workflow_dispatch" or dispatch["head_sha"] != commit_sha
                or dispatch["path"] != ACCEPTANCE_PATH or dispatch.get("referenced_workflows")
                or dispatch["repository"]["full_name"] != REPOSITORY
                or dispatch["head_repository"]["full_name"] != REPOSITORY
                or numeric_id(dispatch["actor"]) not in maintainers
                or numeric_id(dispatch["triggering_actor"]) not in maintainers):
            raise ValueError("acceptance dispatch is not enrolled exact-source attempt 1")
        pr = api.json(f"{p}/pulls/1318")
        if (pr["base"]["sha"] != BASE_SHA
                or pr["base"]["ref"] != "issue-1250-acceptance-infrastructure"
                or pr["head"]["sha"] != commit_sha
                or pr["base"]["repo"]["full_name"] != REPOSITORY
                or pr["head"]["repo"]["full_name"] != REPOSITORY):
            raise ValueError("PR base or candidate changed")
        excluded = {numeric_id(dispatch["actor"]), numeric_id(dispatch["triggering_actor"])}
        commits, total = [], None
        for page in range(1, 11):
            comparison = api.json(f"{p}/compare/{BASE_SHA}...{commit_sha}?per_page=100&page={page}")
            count = comparison["total_commits"]
            if (type(count) is not int or not 0 < count <= 1000
                    or (total is not None and count != total)
                    or comparison["status"] != "ahead" or comparison["behind_by"] != 0
                    or comparison["ahead_by"] != count
                    or comparison["base_commit"]["sha"] != BASE_SHA
                    or comparison["merge_base_commit"]["sha"] != BASE_SHA):
                raise ValueError("ambiguous or divergent contributor range")
            total = count
            batch = comparison["commits"]
            if len(batch) != min(100, total - len(commits)):
                raise ValueError("truncated contributor listing")
            for commit in batch:
                if not re.fullmatch(r"[0-9a-f]{40}", commit["sha"]):
                    raise ValueError("ambiguous contributor commit")
                excluded.update((numeric_id(commit["author"]), numeric_id(commit["committer"])))
            commits.extend(c["sha"] for c in batch)
            if len(commits) == total:
                break
        if len(set(commits)) != total or commits[-1] != commit_sha:
            raise ValueError("incomplete or duplicate contributor listing")
        return VerifiedPolicy(frozenset(reviewers), frozenset(excluded), digest, commit_sha, run_id, _VERIFIED)
    except Exception:
        raise RuntimeError("reviewer authority rejected: policy, dispatch or contributor verification failed") from None


def receipt_digest(receipt):
    """Hash the canonical approval payload excluding the later-assigned review reference."""
    payload = {key: value for key, value in receipt.items() if key != "review"}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def verify_receipt(api, receipt, proof, reviewers, *, now=None):
    """Require an independent allowlisted API approval binding the exact receipt payload.

    Review identity/authority is external policy. Collector/source-author approvals,
    candidate status flags, preparation COMMENT reviews and unbound prose reject.
    This returns verified data only and never activates or installs anything.
    """
    try:
        current = now or datetime.now(timezone.utc)
        metadata = verify_metadata(api, {key: proof[key] for key in AUTH_FIELDS}, now=current)
        if (
            not isinstance(receipt, dict)
            or receipt["status"] != "APPROVED"
            or receipt["scope"] != "dependency-baseline-activation"
        ):
            raise ValueError("explicit independent approval required")
        if any(receipt[key] != metadata[key] for key in AUTH_FIELDS):
            raise ValueError("receipt source/workflow/run/artifact/dependency mismatch")
        if set(receipt) != set(AUTH_FIELDS) | {
            "status",
            "scope",
            "reviewer",
            "expires_utc",
            "review",
        }:
            raise ValueError("strict approval receipt fields required")
        reviewer = receipt["reviewer"]
        if (
            not isinstance(reviewers, VerifiedPolicy)
            or reviewers._seal is not _VERIFIED
            or reviewers.commit_sha != metadata["commit_sha"]
            or type(reviewer) is not int
            or reviewer not in reviewers.reviewer_ids
            or reviewer in reviewers.excluded_ids
            or reviewer in metadata["collector_ids"]
        ):
            raise ValueError("self-issued or unauthorized approval receipt")
        reference = receipt["review"]
        if (
            reference["pull_number"] != 1318
            or type(reference["id"]) is not int
            or reference["id"] <= 0
        ):
            raise ValueError("invalid independent approval reference")
        review = api.json(f"/repos/{REPOSITORY}/pulls/1318/reviews/{reference['id']}")
        marker = "ISSUE1250-APPROVAL sha256:" + receipt_digest(receipt)
        if (
            review["id"] != reference["id"]
            or review["state"] != "APPROVED"
            or review["commit_id"] != metadata["commit_sha"]
            or numeric_id(review["user"]) != reviewer
            or marker not in review["body"].splitlines()
        ):
            raise ValueError("independent review did not approve this exact payload/source")
        expires = datetime.fromisoformat(receipt["expires_utc"].replace("Z", "+00:00"))
        submitted = datetime.fromisoformat(review["submitted_at"].replace("Z", "+00:00"))
        completed = datetime.fromisoformat(metadata["completed_utc"].replace("Z", "+00:00"))
        if not (
            completed <= submitted <= current + timedelta(minutes=5)
            and current < expires <= completed + timedelta(hours=24)
        ):
            raise ValueError("stale/invalid independent approval receipt")
        return dict(receipt)
    except Exception as error:
        raise RuntimeError("approval receipt rejected: " + str(error)) from None


@dataclass(frozen=True)
class VerifiedSnapshot:
    """Transient verifier-issued capability, never deserialized from an artifact/JSON flag."""

    root: Path
    proof: dict
    device: int
    inode: int
    _seal: object


def check_snapshot(snapshot, root, manifest_sha256):
    """Reject arbitrary paths/forged hosted claims without a live verified snapshot handle."""
    if (
        not isinstance(snapshot, VerifiedSnapshot)
        or snapshot._seal is not _VERIFIED
        or snapshot.root != root.resolve()
        or snapshot.proof["manifest_sha256"] != manifest_sha256
        or (root.stat().st_dev, root.stat().st_ino) != (snapshot.device, snapshot.inode)
        or any(p.stat().st_mode & 0o222 for p in [root, *root.rglob("*")])
    ):
        raise RuntimeError(
            "dependency qualification rejected: environment class requires independent API-verified read-only hosted snapshot"
        )


def retrieve(api, expected, destination, diagnostics, *, now=None):
    """Verify one authorized run/artifact and safely publish a read-only qualification.

    No artifact is executed. API proof, digest, archive policy, exact source/input
    fingerprints, JUnit and complete hosted outcome must all hold. Failure retains
    only redacted diagnostics and never leaves a trusted partial destination.
    """
    published = False
    if (
        diagnostics.exists()
        or diagnostics.is_symlink()
        or diagnostics.resolve().is_relative_to(qualification.ROOT.resolve())
    ):
        raise RuntimeError(
            "fresh independent diagnostic location required; previous evidence preserved"
        )
    diagnostics.mkdir(parents=True, exist_ok=False)
    result = {"outcome": "FAIL", "classification": "HOSTED_EVIDENCE_VERIFICATION"}
    try:
        if destination.resolve().is_relative_to(qualification.ROOT.resolve()):
            raise ValueError("evidence destination must be outside candidate/source checkout")
        proof = verify_metadata(api, expected, now=now)
        result["api_metadata"] = proof
        data = api.download(f"/repos/{REPOSITORY}/actions/artifacts/{expected['artifact_id']}/zip")
        result["download_sha256"] = hashlib.sha256(data).hexdigest()
        result["download_size"] = len(data)
        if (
            len(data) != proof["artifact_size"]
            or hashlib.sha256(data).hexdigest() != proof["artifact_sha256"]
        ):
            raise ValueError("downloaded archive digest mismatch")
        hosted_archive.extract_snapshot(data, destination, expected["manifest_sha256"])
        published = True
        record = qualification._validate_contents(
            destination, expected["manifest_sha256"], "github-hosted-ubuntu-24.04", now=now
        )
        source = json.loads((destination / "source-identity.json").read_text())
        outcome = json.loads((destination / "collection-result.json").read_text())
        if (
            source["commit_sha"] != proof["commit_sha"]
            or source["tree_sha"] != proof["tree_sha"]
            or source["workflow_sha256"] != proof["workflow_sha256"]
            or proof["workflow_sha256"] != qualification.sources()[WORKFLOW_PATH]
            or outcome["rc"] != 0
            or outcome["outcome"] != "PASS"
            or outcome["test_node"] != qualification.NODE
            or record["inputs"]["registration_sha256"] != proof["proposal_sha256"]
            or record["inputs"]["build"]["evidence_sha256"] != proof["build_evidence_sha256"]
            or record["inputs"]["runtime"]["lock_sha256"] != proof["runtime_lock_sha256"]
            or record["inputs"]["build"]["requirements_sha256"]
            != proof["build_requirements_sha256"]
        ):
            raise ValueError("artifact source/input/integration mismatch")
        hosted = record["environment"]["hosted"]
        if (
            hosted["GITHUB_REPOSITORY"] != REPOSITORY
            or hosted["GITHUB_RUN_ID"] != str(proof["run_id"])
            or hosted["GITHUB_RUN_ATTEMPT"] != str(proof["attempt"])
            or hosted["GITHUB_SHA"] != proof["commit_sha"]
            or hosted["GITHUB_WORKFLOW_SHA"] != proof["workflow_sha"]
            or hosted["RUNNER_ARCH"] != "X64"
        ):
            raise ValueError("forged hosted environment identity")
        cases = ET.parse(destination / "junit.xml").findall(".//testcase")
        if (
            len(cases) != 1
            or cases[0].get("name") != qualification.NODE.split("::")[1]
            or cases[0].get("classname") != "tests.unit.test_issue_1250_build_backend"
            or any(cases[0].find(name) is not None for name in ("failure", "error", "skipped"))
        ):
            raise ValueError("mandatory real integration did not execute successfully")
        stat = destination.stat()
        result["outcome"] = "VERIFIED_NOT_APPROVED"
        return VerifiedSnapshot(destination.resolve(), proof, stat.st_dev, stat.st_ino, _VERIFIED)
    except Exception as error:
        result["error"] = str(error)
        if published:
            discard_snapshot(destination)
        raise RuntimeError("hosted qualification retrieval rejected: " + str(error)) from None
    finally:
        (diagnostics / "verification.json").write_text(json.dumps(result, indent=2) + "\n")


def discard_snapshot(root):
    """Remove only a snapshot owned by this verifier after validation failure."""
    import shutil

    for path in [root, *root.rglob("*")]:
        path.chmod(0o700 if path.is_dir() else 0o600)
    shutil.rmtree(root)


def checkout_identity():
    """Read the exact staged verifier/activation checkout identity without mutation."""

    def git(*args):
        """Read immutable Git identity or current status from the trusted checkout."""
        return subprocess.check_output(
            ["git", "-C", str(qualification.ROOT), *args], text=True
        ).strip()

    return {
        "commit_sha": git("rev-parse", "HEAD"),
        "tree_sha": git("rev-parse", "HEAD^{tree}"),
        "status": git("status", "--porcelain"),
    }


def require_approved_snapshot(api, receipt, snapshot, reviewers, *, now=None):
    """Future staged activation boundary: require both complete API proof and external approval.

    Returns verified receipt data to the same-process controller only. The
    checked-in sentinel stays None; no serialized receipt grants a capability.
    """
    local = checkout_identity()
    if (
        local["commit_sha"] != snapshot.proof["commit_sha"]
        or local["tree_sha"] != snapshot.proof["tree_sha"]
        or local["status"]
    ):
        raise RuntimeError(
            "exact clean staged source required for approval; changed code must requalify"
        )
    qualification.require_qualification(
        snapshot.root,
        snapshot.proof["manifest_sha256"],
        "github-hosted-ubuntu-24.04",
        now=now,
        hosted_snapshot=snapshot,
    )
    return verify_receipt(api, receipt, snapshot.proof, reviewers, now=now)


def main(argv=None):
    """Explicit future retrieval; requires external authorization, never dispatch/activation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--diagnostics", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--policy-sha256")
    parser.add_argument("--acceptance-run-id", type=int)
    args = parser.parse_args(argv)
    if args.authorization.resolve().is_relative_to(qualification.ROOT.resolve()):
        raise RuntimeError("authorization must be supplied outside candidate checkout")
    expected = json.loads(args.authorization.read_text())
    api = GitHubReadOnly(os.environ.get("GH_TOKEN"))
    try:
        snapshot = retrieve(api, expected, args.destination, args.diagnostics)
        if args.receipt:
            result = {"outcome": "FAIL", "classification": "APPROVAL_VERIFICATION_NOT_ACTIVATION"}
            try:
                policy = verify_authority(api, args.policy_sha256, args.acceptance_run_id, expected["commit_sha"])
                require_approved_snapshot(api, json.loads(args.receipt.read_text()), snapshot, policy)
                result["outcome"] = "APPROVAL_VERIFIED_NOT_ACTIVATED"
            finally:
                (args.diagnostics / "approval-verification.json").write_text(json.dumps(result, indent=2) + "\n")
        print("HOSTED_EVIDENCE_VERIFIED; no activation/acceptance authorized")
    finally:
        api.close()



if __name__ == "__main__":
    main()
