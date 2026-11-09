"""Host-local future-qualification contract tests; synthetic fixtures grant no approval."""

from datetime import datetime, timedelta, timezone
import importlib
import json

import pytest


def validator():
    """Load the preparation verifier lazily to retain bounded missing-interface RED."""
    return importlib.import_module("tools.issue_1250.approval_validation")


@pytest.fixture
def qualification(tmp_path):
    """Synthetic complete bundle; only verifies validator logic, never real execution."""
    module = validator()
    expected = module.inputs()
    now = datetime.now(timezone.utc)
    record = {"classification": "DEPENDENCY_PREPARATION", "outcome": "PASS", "skipped": 0,
              "node": module.NODE, "run_id": "unit-only", "sources": module.sources(),
              "inputs": expected, "environment": module.environment(),
              "started_utc": (now - timedelta(seconds=5)).isoformat(), "finished_utc": now.isoformat()}
    (tmp_path / "integration.json").write_text(json.dumps(record))
    (tmp_path / "execution.log").write_text("PASS real integration (synthetic unit fixture)\n")
    for label, subject in expected["subjects"].items():
        root = tmp_path / label
        root.mkdir()
        values = {"cold-start": {"run_id": "unit-only", "cache_absent": True, "venv_absent": True,
                    "sha": subject["sha"], "cache": str(tmp_path / (label + "-cache")),
                    "subject_root": str(tmp_path / (label + "-subject"))},
                  "identity": {**subject, "status": "", "lock_sha256": expected["runtime"]["lock_sha256"],
                               "non_editable_count": 42},
                  "freeze-diff": {"actual": expected["runtime"]["freeze"], "expected": expected["runtime"]["freeze"],
                                  "missing": [], "extra": []},
                  "build-inventory": {"actual": expected["build"]["inventory"], "wheel_sha256": "a" * 64}}
        for name, value in values.items():
            (root / f"{label}-{name}.json").write_text(json.dumps(value))
        for stage in module.COMMANDS:
            (root / f"{label}-{stage}.json").write_text(json.dumps({"argv": ["unit-only"], "rc": 0}))
            (root / f"{label}-{stage}.log").write_text("synthetic retained command\n")
        (root / f"{label}-installed-project.log").write_text(str(tmp_path / (label + "-subject") / "src/genia"))
        (root / f"{label}-editable-metadata.log").write_text('{"editable": true}')
        (root / f"{label}-editable-record.log").write_text("editable RECORD verified")
    module.manifest(tmp_path)
    return module, tmp_path, record["environment"]["environment_class"], now


def change_json(path, update):
    """Alter a fixture while tests rebuild the outer integrity manifest independently."""
    value = json.loads(path.read_text())
    update(value)
    path.write_text(json.dumps(value))


def test_complete_current_local_qualification_passes_only_as_local(qualification):
    module, root, context, now = qualification
    assert module.require_qualification(root, module.sha256(root / "manifest.json"), context, now=now)["outcome"] == "PASS"
    with pytest.raises(RuntimeError, match="environment class"):
        module.require_qualification(root, module.sha256(root / "manifest.json"), "github-hosted-ubuntu-24.04", now=now)


@pytest.mark.parametrize("change", ["missing-integration", "missing-log", "missing-command", "failed", "skipped",
    "stale", "future", "source", "inputs", "freeze", "inventory", "subject", "shared-cache", "warm-cache",
    "existing-venv", "python", "uv", "platform", "provenance", "record", "command-failure", "wheel-hash", "manifest", "unanchored"])
def test_future_approval_requires_complete_fresh_success(qualification, change):
    module, root, context, now = qualification
    report = root / "integration.json"
    candidate = root / "candidate"
    if change.startswith("missing-"):
        {"missing-integration": report, "missing-log": root / "execution.log",
         "missing-command": candidate / "candidate-sync.log"}[change].unlink()
    elif change == "failed":
        change_json(report, lambda x: x.update(outcome="FAIL"))
    elif change == "skipped":
        change_json(report, lambda x: x.update(skipped=1))
    elif change in {"stale", "future"}:
        instant = now + timedelta(days=-2 if change == "stale" else 1)
        change_json(report, lambda x: x.update(started_utc=instant.isoformat(), finished_utc=instant.isoformat()))
    elif change == "source":
        change_json(report, lambda x: x["sources"].update(unreviewed="0" * 64))
    elif change == "inputs":
        change_json(report, lambda x: x["inputs"]["runtime"].update(lock_sha256="0" * 64))
    elif change == "freeze":
        change_json(candidate / "candidate-freeze-diff.json", lambda x: x["actual"].append("hatchling==1.33.0"))
    elif change == "inventory":
        change_json(candidate / "candidate-build-inventory.json", lambda x: x["actual"].append("unexpected==1"))
    elif change == "subject":
        change_json(candidate / "candidate-identity.json", lambda x: x.update(sha="b" * 40))
    elif change in {"shared-cache", "warm-cache", "existing-venv"}:
        data = json.loads((root / "baseline/baseline-cold-start.json").read_text())
        update = {"shared-cache": {"cache": data["cache"]}, "warm-cache": {"cache_absent": False},
                  "existing-venv": {"venv_absent": False}}[change]
        change_json(candidate / "candidate-cold-start.json", lambda x: x.update(update))
    elif change in {"python", "uv", "platform", "provenance"}:
        update = {"python": {"python_version": "3.12.13"}, "uv": {"uv_version": "uv 0.13.6"},
                  "platform": {"system": "Darwin"}, "provenance": {"uv_sha256": "0" * 64}}[change]
        change_json(report, lambda x: x["environment"].update(update))
    elif change == "record":
        (candidate / "candidate-editable-record.log").write_text("not verified")
    elif change == "command-failure":
        change_json(candidate / "candidate-project-install.json", lambda x: x.update(rc=1))
    elif change == "wheel-hash":
        change_json(candidate / "candidate-build-inventory.json", lambda x: x.update(wheel_sha256="bad"))
    module.manifest(root)
    digest = module.sha256(root / "manifest.json")
    if change == "manifest":
        (root / "unregistered").touch()
    elif change == "unanchored":
        digest = ""
    with pytest.raises(RuntimeError, match="qualification rejected"):
        module.require_qualification(root, digest, context, now=now)


def test_missing_bundle_rejected_without_execution(tmp_path):
    with pytest.raises(RuntimeError, match="qualification rejected"):
        validator().require_qualification(tmp_path / "missing", "0" * 64, "github-hosted-ubuntu-24.04")


def test_registration_proposal_is_exact_and_inactive():
    from tools.issue_1250 import run as gate
    module = validator()
    proposed = json.loads(module.PROPOSAL.read_text())
    assert proposed["status"] == "PROPOSED_NOT_APPROVED"
    assert len(proposed["runtime"]["freeze"]) == 42
    assert "pymdown-extensions==13.0" in proposed["runtime"]["freeze"]
    assert "pymdown-extensions==12.3" in gate.REGISTRATION["freeze"]
    assert gate.APPROVED_DEPENDENCIES is None
    assert len(proposed["build"]["inventory"]) == 7
    assert module.inputs()["scope"] == proposed["scope"]


def test_capture_records_real_failure_and_preserves_exception(tmp_path):
    module = validator()
    with pytest.raises(ValueError, match="injected integration failure"):
        with module.capture(tmp_path):
            raise ValueError("injected integration failure")
    assert json.loads((tmp_path / "integration.json").read_text())["outcome"] == "FAIL"
    assert (tmp_path / "manifest.json").is_file()


def test_incomplete_capture_cannot_self_report_pass(tmp_path):
    module = validator()
    with pytest.raises(RuntimeError, match="qualification rejected"):
        with module.capture(tmp_path):
            pass  # No real subjects/commands: a successful body alone cannot qualify.
    assert json.loads((tmp_path / "integration.json").read_text())["outcome"] == "FAIL"
