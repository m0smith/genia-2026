"""Read-only mandatory qualification for future #1250 dependency approval validation.

No baseline activation, acceptance runner or CI dispatch. A reviewer must anchor
the expected artifact digest and environment class independently. Evidence is
self-attested packaging provenance, not independent approval or hosted CI proof.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import uuid

if __package__:
    from . import build_backend
else:
    import build_backend

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROPOSAL = HERE / "registration-proposal.json"
NODE = "tests/unit/test_issue_1250_build_backend.py::test_real_cold_baseline_and_candidate_provisioning"
COMMANDS = ("uv-version", "sync", "build-venv", "build-install", "build-editable",
            "project-install", "editable-metadata", "freeze", "installed-project", "editable-record")


def sha256(path):
    """Digest one evidence/source file without normalization."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources():
    """Bind qualification to all current #1250 tooling and preparation test bytes."""
    files = sorted(HERE.glob("*.py")) + sorted((ROOT / "tests/unit").glob("test_issue_1250*.py"))
    files += sorted((ROOT / ".github/workflows").glob("issue-1250*.yml"))
    files += [HERE / "hosted-policy.json", HERE / "hosted-receipt.pending.json"]
    return {str(path.relative_to(ROOT)): sha256(path) for path in files}


def inputs():
    """Verify the inactive registration's immutable data and return its exact identity."""
    registration = json.loads(PROPOSAL.read_text())
    build, _ = build_backend.load_evidence()
    runtime = json.loads((HERE / "dependencies/proposed-2026-11-08/proposal.json").read_text())
    if (any(registration["runtime"][key] != runtime[key] for key in ("lock_sha256", "pyproject_sha256", "freeze"))
            or len(runtime["freeze"]) != 42 or runtime["freeze"] != sorted(set(runtime["freeze"]))):
        raise RuntimeError("registration proposal runtime freeze mismatch")
    if (sha256(HERE / registration["runtime"]["lock_file"]) != registration["runtime"]["lock_sha256"]
            or sha256(HERE / registration["build"]["evidence_file"]) != registration["build"]["evidence_sha256"]
            or sha256(HERE / registration["build"]["requirements_file"]) != registration["build"]["requirements_sha256"]
            or sorted(f"{p['name']}=={p['version']}" for p in build["packages"]) != registration["build"]["inventory"]):
        raise RuntimeError("registration proposal dependency identity mismatch")
    return {"registration_sha256": sha256(PROPOSAL), "runtime": registration["runtime"],
            "build": registration["build"], "scope": registration["scope"], "subjects": registration["subjects"]}


def manifest(root):
    """Write a complete artifact manifest; never include its own bytes."""
    values = {str(p.relative_to(root)): sha256(p) for p in sorted(root.rglob("*"))
              if p.is_file() and p != root / "manifest.json"}
    (root / "manifest.json").write_text(json.dumps(values, indent=2) + "\n")


def environment():
    """Record actual runtime/platform and allowlisted hosted provenance without secrets."""
    uv = Path(shutil.which("uv")).resolve()
    os_release = platform.freedesktop_os_release()
    hosted = {key: os.environ.get(key) for key in (
        "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_SHA", "GITHUB_WORKFLOW_REF",
        "GITHUB_WORKFLOW_SHA", "GITHUB_REPOSITORY", "RUNNER_OS", "RUNNER_ARCH", "ImageOS", "ImageVersion")}
    context = "local-" + os_release["ID"] + "-" + os_release["VERSION_ID"]
    if os.environ.get("GITHUB_ACTIONS") == "true":
        if (not all(hosted.values()) or hosted["GITHUB_RUN_ATTEMPT"] != "1"
                or os_release["ID"] != "ubuntu" or os_release["VERSION_ID"] != "24.04"
                or hosted["RUNNER_OS"] != "Linux" or hosted["ImageOS"] != "ubuntu24"):
            raise RuntimeError("unsupported hosted qualification provenance")
        context = "github-hosted-ubuntu-24.04"
    return {"environment_class": context, "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(), "python_executable": sys.executable,
            "python_sha256": sha256(Path(sys.executable).resolve()), "uv_path": str(uv),
            "uv_version": subprocess.check_output([str(uv), "--no-config", "--version"], text=True).strip(),
            "uv_sha256": sha256(uv), "system": platform.system(), "machine": platform.machine(),
            "os_release": {k: os_release[k] for k in ("ID", "VERSION_ID")}, "hosted": hosted}


@contextmanager
def capture(root):
    """Retain non-skipped real integration outcomes, current inputs/source and logs.

    Called only inside the explicitly selected preparation integration test.
    Existing evidence is never overwritten. Exceptions remain failures and are
    re-raised; neither collection nor read-only validation activates a baseline.
    """
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise RuntimeError("qualification output must be a fresh empty directory")
    record = {"classification": "DEPENDENCY_PREPARATION", "outcome": "FAIL", "skipped": 0,
              "node": NODE, "run_id": str(uuid.uuid4()), "sources": sources(), "inputs": inputs(),
              "environment": environment(), "started_utc": datetime.now(timezone.utc).isoformat()}
    log = root / "execution.log"
    log.write_text("BEGIN explicit real cold-cache packaging integration\n")
    try:
        yield record
        record["outcome"] = "PASS"
    except BaseException as error:
        record["error"] = str(error)
        raise
    finally:
        record["finished_utc"] = datetime.now(timezone.utc).isoformat()
        with log.open("a") as stream:
            stream.write(record["outcome"] + " real integration; see per-subject commands and assertions\n")
        (root / "integration.json").write_text(json.dumps(record, indent=2) + "\n")
        manifest(root)
        if record["outcome"] == "PASS":
            try:
                # Local schema/integrity validation is not independent approval.
                _validate_contents(root, sha256(root / "manifest.json"),
                                      record["environment"]["environment_class"])
            except BaseException as error:
                record.update(outcome="FAIL", error=str(error))
                (root / "integration.json").write_text(json.dumps(record, indent=2) + "\n")
                with log.open("a") as stream:
                    stream.write("FAIL qualification bundle validation\n")
                manifest(root)
                raise


def _validate_contents(root, expected_manifest_sha256, expected_environment, *, now=None):
    """Reject absent, modified, stale, skipped, wrong-source or failed qualification.

    The caller must supply an independently approved manifest digest and intended
    environment class. Validating local evidence as local never qualifies hosted
    activation. A 24-hour maximum age and exact current source/input identities
    require a fresh run after any relevant code, tests or proposal change.
    """
    try:
        if not re.fullmatch(r"[0-9a-f]{64}", expected_manifest_sha256 or ""):
            raise ValueError("independently approved manifest digest required")
        if sha256(root / "manifest.json") != expected_manifest_sha256:
            raise ValueError("qualification manifest digest mismatch")
        paths = list(root.rglob("*"))
        if any(p.is_symlink() for p in paths):
            raise ValueError("qualification symlinks forbidden")
        actual = {str(p.relative_to(root)): sha256(p) for p in paths if p.is_file() and p != root / "manifest.json"}
        if json.loads((root / "manifest.json").read_text()) != actual:
            raise ValueError("qualification artifact manifest mismatch")
        record = json.loads((root / "integration.json").read_text())
        expected = inputs()
        if (record["outcome"] != "PASS" or record["skipped"] != 0 or record["node"] != NODE
                or record["classification"] != "DEPENDENCY_PREPARATION"
                or record["sources"] != sources() or record["inputs"] != expected):
            raise ValueError("missing successful non-skipped exact-source/input qualification")
        current = now or datetime.now(timezone.utc)
        started = datetime.fromisoformat(record["started_utc"])
        finished = datetime.fromisoformat(record["finished_utc"])
        if not (current - timedelta(hours=24) <= started <= finished <= current + timedelta(minutes=5)):
            raise ValueError("stale or invalid qualification timestamp")
        env = record["environment"]
        if env["environment_class"] != expected_environment:
            raise ValueError("qualification environment class mismatch")
        for key in ("python_implementation", "python_version", "system", "machine", "uv_sha256"):
            if env[key] != expected["scope"][key]:
                raise ValueError("qualification toolchain/platform mismatch")
        if not re.match(r"^uv 0\.13\.5(?:\s|$)", env["uv_version"]):
            raise ValueError("qualification uv version mismatch")
        if expected_environment == "github-hosted-ubuntu-24.04":
            hosted = env["hosted"]
            if (not all(hosted.values()) or hosted["GITHUB_RUN_ATTEMPT"] != "1"
                    or env["os_release"] != {"ID": "ubuntu", "VERSION_ID": "24.04"}
                    or hosted["RUNNER_OS"] != "Linux" or hosted["ImageOS"] != "ubuntu24"):
                raise ValueError("hosted qualification provenance missing")
        if "PASS real integration" not in (root / "execution.log").read_text():
            raise ValueError("qualification execution log missing")
        caches = []
        for label, identity in expected["subjects"].items():
            subject = root / label
            def load(suffix):
                """Read one retained subject evidence record; missing data rejects."""
                return json.loads((subject / f"{label}-{suffix}.json").read_text())
            cold, observed = load("cold-start"), load("identity")
            if (cold["run_id"] != record["run_id"] or not cold["cache_absent"] or not cold["venv_absent"]
                    or cold["sha"] != identity["sha"] or observed["sha"] != identity["sha"]
                    or observed["tree"] != identity["tree"] or observed["status"] != ""
                    or observed["lock_sha256"] != expected["runtime"]["lock_sha256"]
                    or observed["non_editable_count"] != 42):
                raise ValueError("subject cold-start/identity mismatch")
            caches.append(cold["cache"])
            freeze, inventory = load("freeze-diff"), load("build-inventory")
            if (freeze["expected"] != expected["runtime"]["freeze"] or freeze["actual"] != freeze["expected"]
                    or freeze["missing"] or freeze["extra"] or inventory["actual"] != expected["build"]["inventory"]
                    or not re.fullmatch(r"[0-9a-f]{64}", inventory["wheel_sha256"])):
                raise ValueError("baseline/candidate dependency or inventory mismatch")
            for stage in COMMANDS:
                if load(stage)["rc"] != 0 or not (subject / f"{label}-{stage}.log").is_file():
                    raise ValueError("qualification command failed or missing")
            if (str(Path(cold["subject_root"]) / "src/genia") not in (subject / f"{label}-installed-project.log").read_text()
                    or '"editable": true' not in (subject / f"{label}-editable-metadata.log").read_text()
                    or "editable RECORD verified" not in (subject / f"{label}-editable-record.log").read_text()):
                raise ValueError("real editable installation/RECORD proof missing")
        if len(set(caches)) != 2 or any(not cache for cache in caches):
            raise ValueError("subjects did not use separate cold caches")
        return record
    except (OSError, KeyError, ValueError, TypeError, AttributeError) as error:
        raise RuntimeError("dependency qualification rejected: " + str(error)) from error


def require_qualification(root, expected_manifest_sha256, expected_environment, *, now=None, hosted_snapshot=None):
    """Validate local contents; hosted qualification additionally requires independent API proof.

    Artifact environment variables, candidate manifests and arbitrary paths never
    grant hosted trust. Collection uses content checks only and cannot issue the
    transient snapshot capability created by the independent retrieval process.
    """
    if expected_environment == "github-hosted-ubuntu-24.04":
        from tools.issue_1250.hosted_trust import check_snapshot
        check_snapshot(hosted_snapshot, root, expected_manifest_sha256)
    return _validate_contents(root, expected_manifest_sha256, expected_environment, now=now)


def main(argv=None):
    """Explicit future read-only approval validation; never activate or run acceptance."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--environment-class", required=True)
    args = parser.parse_args(argv)
    require_qualification(args.evidence, args.manifest_sha256, args.environment_class)
    print("DEPENDENCY_QUALIFICATION_VERIFIED; no activation or acceptance authorized")


if __name__ == "__main__":
    main()
