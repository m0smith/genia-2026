"""Host-local #1250 CI guard/evidence tests; no portable Genia semantics or acceptance credit.

Remove with the temporary workflow after #1250's acceptance decision is recorded.
All tests are offline; no hosted dispatch, acceptance subprocess or real timer wait.
"""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

import pytest
import yaml

from tools.issue_1250 import run as gate

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/issue-1250-acceptance.yml"
SHA = "a" * 40
REAL_INSTALL_EDITABLE = gate.build_backend.install_editable


def record(label="G2", boot="g2", mode="acceptance"):
    """Return minimal valid, public hosted evidence with an intentionally reusable runner label."""
    return {
        "runner": {"ImageOS": "ubuntu24", "ImageVersion": "20261107.1",
                   "RUNNER_OS": "Linux", "RUNNER_ARCH": "X64", "RUNNER_NAME": "same-label",
                   "GITHUB_RUN_ID": "123", "GITHUB_RUN_ATTEMPT": "1",
                   "GITHUB_WORKFLOW_SHA": SHA, "WORKFLOW_SHA": SHA,
                   "GITHUB_JOB": "parallel" if label == "G2" else "serial",
                   "ACCEPTANCE_ENVIRONMENT": label, "DISPATCH_MODE": mode},
        "boot_id": boot, "kernel": "test-kernel", "uid": 1000,
        "uv_version": "uv 0.13.5 (test build)",
    }


def phase(root, stage, provenance):
    """Create a self-consistent phase artifact; tests then corrupt its specific invariants."""
    root.mkdir(parents=True)
    gate.write_json(root / "provenance.json", provenance)
    gate.write_json(root / "summary.json", {"stage": stage, "outcome": "PASS"})
    gate.manifest(root)


@pytest.fixture
def upstream(tmp_path):
    """Two successful G1 artifacts on separate VMs, including same-job G0 qualification."""
    for name in ("A", "B"):
        root = tmp_path / f"issue-1250-serial-{name}-attempt-1"
        previous = record(name, name)
        phase(root / "g0", "g0", previous)
        phase(root / "serial", "serial", previous)
        gate.write_json(root / "artifact-index.json", {"stage": "serial", "outcome": "PASS"})
        gate.manifest(root)
    return tmp_path


def test_three_vm_independence_compares_labels_and_image(upstream, tmp_path):
    gate.independent_runners(upstream, record(), tmp_path)
    comparisons = json.loads((tmp_path / "independence.json").read_text())
    assert all(r["same_runner_label"] for r in comparisons["g1"])
    assert {r["boot_id"] for r in comparisons["g1"]} == {"A", "B"}


@pytest.mark.parametrize("change", ["g2-is-a", "duplicate-g1", "image", "kernel", "attempt", "sha", "g1-fail", "tamper"])
def test_independence_rejects_reused_vm_drift_and_invalid_artifacts(upstream, tmp_path, change):
    current = record()
    root = upstream / "issue-1250-serial-B-attempt-1"
    if change == "g2-is-a":
        current["boot_id"] = "A"
    elif change in ("image", "attempt", "sha"):
        key = {"image": "ImageVersion", "attempt": "GITHUB_RUN_ATTEMPT", "sha": "WORKFLOW_SHA"}[change]
        current["runner"][key] = "wrong"
    elif change == "kernel":
        current["kernel"] = "different"
    elif change == "duplicate-g1":
        previous = record("B", "A")
        for stage in ("g0", "serial"):
            gate.write_json(root / stage / "provenance.json", previous)
            gate.manifest(root / stage)
        gate.manifest(root)
    elif change == "g1-fail":
        gate.write_json(root / "serial/summary.json", {"stage": "serial", "outcome": "FAIL"})
        gate.manifest(root / "serial")
        gate.manifest(root)
    else:
        (root / "unexpected.txt").write_text("not in manifest")
    with pytest.raises(RuntimeError):
        gate.independent_runners(upstream, current, tmp_path)


@pytest.mark.parametrize("change", [None, "sha", "attempt", "root", "image-missing", "quota", "python"])
def test_hosted_requirements(monkeypatch, change):
    """Require hosted version/identity/attempt/uid/quota facts independent of test Python."""
    monkeypatch.setattr(gate.sys, "version_info", (3, 12, 14) if change != "python" else (3, 14, 0))
    current = record()
    values = {"cgroup": {"cpu.max": "200000 100000", "memory.max": "8589934592"}}
    monkeypatch.setattr(gate.os, "getpid", lambda: 1)
    if change == "sha":
        current["runner"]["WORKFLOW_SHA"] = "b" * 40
    elif change == "attempt":
        current["runner"]["GITHUB_RUN_ATTEMPT"] = "2"
    elif change == "root":
        current["uid"] = 0
    elif change == "image-missing":
        del current["runner"]["ImageVersion"]
    elif change == "quota":
        values["cgroup"]["memory.max"] = "max"
    if change:
        with pytest.raises(RuntimeError):
            gate.check_hosted(current, values)
    else:
        gate.check_hosted(current, values)


@pytest.mark.parametrize("change", [None, "short-wall", "short-test", "missing-wait", "wrong-timeout", "wrong-exit", "skip", "error", "wrong-node"])
def test_signal_mutant_requires_traceback_elapsed_and_identity(tmp_path, change):
    node = gate.SIGNALS[1]
    defect = gate.expected_defect(node)
    text = "\n".join(defect["contains"])
    rc, wall, duration = 1, 60.5, "60.0"
    if change == "short-wall":
        wall = 1
    elif change == "short-test":
        duration = "1"
    elif change == "missing-wait":
        text = text.replace("session.proc.wait(timeout=GRACE_S)", "session.wait_ready()")
    elif change == "wrong-timeout":
        text = text.replace("60 seconds", "30 seconds")
    elif change == "wrong-exit":
        rc = 2
    name = node.split("::")[1] if change != "wrong-node" else "wrong"
    root = ET.Element("testsuites")
    case = ET.SubElement(ET.SubElement(root, "testsuite"), "testcase",
                         classname="tests.unit.test_r28_mcp_stdio_lifecycle", name=name, time=duration)
    ET.SubElement(case, "skipped" if change == "skip" else "error" if change == "error" else "failure").text = text
    xml = tmp_path / "result.xml"
    ET.ElementTree(root).write(xml)
    if change:
        with pytest.raises(RuntimeError):
            gate.check_results(xml, [node], rc, wall, defect)
    else:
        assert gate.check_results(xml, [node], rc, wall, defect) == {"reported": 1, "fail": 1, "pass": 0}


def test_registration_is_order_independent_and_identity_strict(monkeypatch):
    registration = deepcopy(gate.REGISTRATION)
    registration["original"].reverse()
    registration["focused"].reverse()
    monkeypatch.setattr(gate, "REGISTRATION", registration)
    assert gate.INVENTORY not in gate.registered_nodes()["g0"]
    assert gate.SDK in gate.registered_nodes()["g0"]
    registration["original"][registration["original"].index(gate.INVENTORY)] = "wrong inventory"
    with pytest.raises(RuntimeError, match="identity"):
        gate.registered_nodes()


def test_cleanup_preserves_primary_exception(tmp_path):
    primary = ValueError("original failure")
    gate.finalize(tmp_path, [tmp_path / "missing-checkout"], "g0", primary)
    if hasattr(primary, "add_note"):
        assert "evidence finalization errors" in primary.__notes__[0]
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["outcome"] == "FAIL" and summary["error"] == "original failure"
    gate.verify_manifest(tmp_path)


def test_smoke_only_provisions_baseline_and_runs_probe(monkeypatch, tmp_path):
    monkeypatch.setattr(gate.sys, "version_info", (3, 12, 14))
    current = record("smoke", "smoke-boot", "smoke")
    calls = []
    monkeypatch.setattr(gate.os, "getpid", lambda: 1)
    monkeypatch.setattr(gate, "provenance", lambda evidence: (current, {"test": {"cpu.max": "200000 100000", "memory.max": "8589934592"}}))
    monkeypatch.setattr(gate, "provision", lambda root, sha, evidence, label: calls.append(("provision", sha)))
    monkeypatch.setattr(gate, "run_nodes", lambda root, nodes, evidence, label, **kw: calls.append(("nodes", nodes, kw)))
    monkeypatch.setattr(gate, "clean", lambda *args: None)
    monkeypatch.setattr(gate, "git", lambda *args: gate.BASELINE)
    gate.main(["smoke", "--baseline", str(tmp_path / "baseline"), "--work", str(tmp_path / "smoke")])
    assert calls == [("provision", gate.BASELINE), ("nodes", [gate.PROBE], {"classification": "DIAGNOSTIC_ONLY"})]
    summary = json.loads((tmp_path / "smoke/evidence/summary.json").read_text())
    assert summary["classification"] == "DIAGNOSTIC_ONLY" and summary["outcome"] == "PASS"


@pytest.mark.parametrize("change", [None, "sha", "malformed", "attempt", "auth", "ref", "repo", "event", "mode"])
def test_first_dispatch_step_fails_loudly_before_checkout(tmp_path, change):
    workflow = yaml.load(WORKFLOW.read_text(), Loader=yaml.BaseLoader)
    script = workflow["jobs"]["smoke"]["steps"][0]["run"]
    env = {**os.environ, "RUNNER_TEMP": str(tmp_path), "GITHUB_EVENT_NAME": "workflow_dispatch",
           "GITHUB_REPOSITORY": "m0smith/genia-2026", "GITHUB_REF": "refs/heads/issue-1250-acceptance-infrastructure",
           "GITHUB_SHA": SHA, "GITHUB_WORKFLOW_SHA": SHA, "GITHUB_RUN_ATTEMPT": "1",
           "AUTHORIZED": "true", "REQUESTED_SHA": SHA, "REQUESTED_MODE": "smoke",
           "STAGE": "smoke", "ENVIRONMENT": "smoke"}
    if change:
        key = {"sha": "GITHUB_SHA", "malformed": "REQUESTED_SHA", "attempt": "GITHUB_RUN_ATTEMPT",
               "auth": "AUTHORIZED", "ref": "GITHUB_REF", "repo": "GITHUB_REPOSITORY",
               "event": "GITHUB_EVENT_NAME", "mode": "REQUESTED_MODE"}[change]
        env[key] = "wrong"
    result = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True)
    assert (result.returncode == 0) is (change is None)
    dispatch = json.loads((tmp_path / "issue-1250-smoke-smoke/evidence/dispatch.json").read_text())
    assert dispatch["outcome"] == ("PASS" if change is None else "FAIL")


def test_workflow_dispatch_permissions_dependencies_and_privileged_paths():
    workflow = yaml.load(WORKFLOW.read_text(), Loader=yaml.BaseLoader)
    assert set(workflow["on"]) == {"workflow_dispatch"}
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["jobs"]["parallel"]["needs"] == "serial"
    for job in workflow["jobs"].values():
        assert 0 < int(job["timeout-minutes"]) <= 45
        assert job["steps"][0]["name"].startswith("Fail loudly")
        body = next(s["run"] for s in job["steps"] if s.get("id") == "gate")
        assert "/usr/bin/sudo /usr/bin/systemd-run" in body
        assert "/usr/bin/unshare" in body and "/usr/bin/setpriv" in body
        assert 'run_namespace smoke' in body
    candidate = next(s for s in workflow["jobs"]["smoke"]["steps"] if s["name"].startswith("Checkout frozen candidate"))
    assert candidate["if"] == "env.STAGE != 'smoke'"


@pytest.mark.parametrize("command_outcome", ["success", "failure", "skipped"])
def test_artifact_report_prints_digests_and_keeps_smoke_diagnostic(tmp_path, monkeypatch, capsys, command_outcome):
    phase(tmp_path / "smoke", "smoke", record(mode="smoke"))
    output, summary = tmp_path.parent / "outputs", tmp_path.parent / "step-summary"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    gate.report(["--evidence", str(tmp_path), "--stage", "smoke", "--command-outcome", command_outcome])
    index = json.loads((tmp_path / "artifact-index.json").read_text())
    assert index["outcome"] == ("PASS" if command_outcome == "success" else "FAIL")
    assert index["classification"] == "DIAGNOSTIC_ONLY"
    assert "manifest_sha256=" in capsys.readouterr().out
    assert output.read_text().startswith("manifest_digest=")
    assert "DIAGNOSTIC_ONLY" in summary.read_text()
    gate.verify_manifest(tmp_path)


def test_absent_phase_is_not_run_and_cannot_report_pass(tmp_path):
    gate.report(["--evidence", str(tmp_path), "--stage", "serial", "--command-outcome", "success"])
    index = json.loads((tmp_path / "artifact-index.json").read_text())
    assert index["outcome"] == "FAIL"
    assert all(phase["outcome"] == "NOT RUN" for phase in index["phases"].values())


@pytest.fixture
def locked_subject(tmp_path, monkeypatch):
    """Real throwaway git subject and fake uv; never installs or runs acceptance."""
    root, evidence, binary = (tmp_path / name for name in ("subject", "evidence", "bin"))
    for path in (root, evidence, binary):
        path.mkdir()
    (root / ".gitignore").write_text("uv.lock\n")
    (root / "pyproject.toml").write_text("[project]\nname='unit-subject'\n")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Unit", "-c", "user.email=unit@example.invalid",
                    "commit", "-qm", "fixture"], check=True)
    fixture = tmp_path / "acceptance.lock"
    fixture.write_text("immutable unit lock\n")
    expected = {"lock_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
                "pyproject_sha256": hashlib.sha256((root / "pyproject.toml").read_bytes()).hexdigest(),
                "freeze": ["example==1"]}
    executable = binary / "uv"
    executable.write_text("#!/usr/bin/env python3\n" +
        "import json, os, sys\nfrom pathlib import Path\n" +
        "with Path(os.environ['FAKE_CALLS']).open('a') as out: out.write(json.dumps(sys.argv[1:])+'\\n')\n" +
        "if 'sync' in sys.argv[1:]:\n" +
        "    if os.environ.get('FAKE_REWRITE'): Path('uv.lock').write_text('changed')\n" +
        "    sys.exit(int(os.environ.get('FAKE_SYNC_RC', '0')))\n" +
        "elif 'freeze' in sys.argv[1:]: print(os.environ.get('FAKE_FREEZE', 'example==1'))\n" +
        "else: sys.exit('unexpected resolution/acceptance command')\n")
    executable.chmod(0o755)
    monkeypatch.setattr(gate.build_backend, "check_runtime", lambda *args: None)
    monkeypatch.setattr(gate.build_backend, "install_editable", lambda *args: None)
    monkeypatch.setenv("PATH", str(binary) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("FAKE_CALLS", str(tmp_path / "calls"))
    return root, gate.git(root, "rev-parse", "HEAD"), evidence, fixture, expected


@pytest.mark.parametrize("change", [None, "missing", "tamper", "existing", "symlink", "declarations",
                                  "freeze-version", "freeze-missing", "freeze-extra", "freeze-backend", "sync", "rewrite", "dirty"])
def test_shared_locked_provisioning_fails_closed(locked_subject, monkeypatch, change):
    root, sha, evidence, fixture, expected = locked_subject
    if change == "missing":
        fixture.unlink()
    elif change == "tamper":
        fixture.write_text(fixture.read_text() + "x")
    elif change == "existing":
        (root / "uv.lock").write_text("different")
    elif change == "symlink":
        (root / "uv.lock").symlink_to(fixture)
    elif change == "declarations":
        expected["pyproject_sha256"] = "0" * 64
    elif change and change.startswith("freeze-"):
        monkeypatch.setenv("FAKE_FREEZE", {"freeze-version": "example==2", "freeze-missing": "",
                                         "freeze-extra": "example==1\nextra==1",
                                         "freeze-backend": "example==1\nhatchling==1.33.0"}[change])
    elif change == "sync":
        monkeypatch.setenv("FAKE_SYNC_RC", "1")
    elif change == "rewrite":
        monkeypatch.setenv("FAKE_REWRITE", "1")
    elif change == "dirty":
        (root / "untracked").touch()
    if change:
        with pytest.raises(RuntimeError):
            gate.provision_locked(root, sha, evidence, "unit", fixture, expected)
    else:
        gate.provision_locked(root, sha, evidence, "unit", fixture, expected)
        gate.clean(root, sha)
        assert (root / "uv.lock").read_bytes() == fixture.read_bytes()
    calls_path = root.parent / "calls"
    calls = [json.loads(x) for x in calls_path.read_text().splitlines()] if calls_path.exists() else []
    assert all(call[0] != "lock" for call in calls)
    if calls:
        assert calls[0][:7] == ["--no-config", "sync", "--dev", "--locked", "--no-python-downloads", "--no-install-project", "--no-build"]
    if change in {"missing", "tamper", "existing", "symlink", "declarations", "dirty"}:
        assert not calls
    if calls and any("freeze" in call for call in calls):
        freeze_call = next(call for call in calls if "freeze" in call)
        assert freeze_call[-2:] == ["--python", str(root / ".venv/bin/python")]
    if change and change.startswith("freeze-"):
        assert json.loads((evidence / "unit-freeze-diff.json").read_text())["actual"] != expected["freeze"]


def test_proposal_is_pinned_and_cannot_activate_acceptance(locked_subject):
    root, sha, evidence, _, _ = locked_subject
    proposal = ROOT / "tools/issue_1250/dependencies/proposed-2026-11-08"
    expected = json.loads((proposal / "proposal.json").read_text())
    assert expected["status"] == "PROPOSED_NOT_APPROVED"
    assert hashlib.sha256((proposal / "acceptance.lock").read_bytes()).hexdigest() == expected["lock_sha256"]
    assert gate.LOCK == "27ca5a9328ba8641ce18078782c7edecdc8a753aa6b4fd3ca57932a66d49f291"
    assert len(gate.REGISTRATION["freeze"]) == 42
    assert "pymdown-extensions==12.3" in gate.REGISTRATION["freeze"]
    assert len(gate.REGISTRATION["original"]) == 22
    assert gate.APPROVED_DEPENDENCIES is None
    with pytest.raises(RuntimeError, match="independent dependency baseline approval"):
        gate.provision(root, sha, evidence, "unit")
    assert json.loads((evidence / "unit-dependency-gate.json").read_text())["outcome"] == "BLOCKED"
    assert not (root / "uv.lock").exists()


def test_missing_build_evidence_stops_provisioning_and_records_failure(locked_subject, monkeypatch):
    root, sha, evidence, fixture, expected = locked_subject

    def missing():
        """Represent absent registered build evidence before any installer command."""
        raise RuntimeError("missing build evidence")

    monkeypatch.setattr(gate.build_backend, "load_evidence", missing)
    with pytest.raises(RuntimeError, match="missing build evidence") as caught:
        gate.provision_locked(root, sha, evidence, "unit", fixture, expected)
    gate.finalize(evidence, [root], "smoke", caught.value)
    assert json.loads((evidence / "summary.json").read_text())["outcome"] == "FAIL"
    assert not (root.parent / "calls").exists()


@pytest.mark.parametrize("failure", ["build-editable", "project-install"])
def test_actual_provision_wrapper_propagates_backend_and_install_failures(locked_subject, monkeypatch, failure):
    """Exercise wrapper -> locked helper -> real build coordinator with injected IO failure."""
    root, sha, evidence, fixture, expected = locked_subject
    monkeypatch.setattr(gate, "APPROVED_DEPENDENCIES", (fixture, expected))
    monkeypatch.setattr(gate.build_backend, "install_editable", REAL_INSTALL_EDITABLE)

    def command(argv, cwd, output, label):
        """Model installer subprocess failures while retaining the real error contract."""
        rc = 1 if label.endswith(failure) else 0
        gate.write_json(output / (label + ".json"), {"argv": argv, "rc": rc})
        (output / (label + ".log")).write_text("injected unit failure" if rc else "unit setup")
        if rc:
            raise RuntimeError(label + " failed; see retained log")
        if label.endswith("build-editable"):
            wheel = Path(argv[-2]) / "genia-0.1.14-py3-none-any.whl"
            wheel.write_bytes(b"unit editable wheel")
            Path(argv[-1]).write_text(json.dumps({"wheel": wheel.name,
                "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest()}))
        return ""

    monkeypatch.setattr(gate, "command", command)
    with pytest.raises(RuntimeError, match=failure) as caught:
        gate.provision(root, sha, evidence, "wrapper")
    gate.finalize(evidence, [root], "smoke", caught.value)
    assert json.loads((evidence / "summary.json").read_text())["outcome"] == "FAIL"
    assert json.loads((evidence / ("wrapper-" + failure + ".json")).read_text())["rc"] == 1
    assert not list(evidence.glob("*-build-env-*"))
