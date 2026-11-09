"""Host-local packaging guards for #1250; no Genia semantics or acceptance credit.

The real provisioning integration is opt-in because it downloads pinned wheels
into disposable caches. It never activates the approval sentinel or runs gates.
"""

import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from tools.issue_1250 import run as gate
from tools.issue_1250 import approval_validation

ROOT = Path(__file__).resolve().parents[2]
PROPOSAL = ROOT / "tools/issue_1250/dependencies/proposed-2026-11-08"


def backend():
    """Delay loading the new interface so preimplementation RED stays bounded."""
    return importlib.import_module("tools.issue_1250.build_backend")


@pytest.mark.parametrize("file", ["build-evidence.json", "build-requirements.txt"])
@pytest.mark.parametrize("change", ["missing", "tamper"])
def test_backend_evidence_missing_or_modified_fails_before_install(tmp_path, monkeypatch, file, change):
    module = backend()
    for source in module.INPUTS.iterdir():
        if source.is_file():
            (tmp_path / source.name).write_bytes(source.read_bytes())
    monkeypatch.setattr(module, "INPUTS", tmp_path)
    if change == "missing":
        (tmp_path / file).unlink()
    else:
        with (tmp_path / file).open("ab") as out:
            out.write(b"x")
    with pytest.raises(RuntimeError, match="build evidence"):
        module.load_evidence()


@pytest.mark.parametrize("change", ["missing", "version", "extra"])
def test_real_backend_inventory_rejects_absence_version_and_extra(tmp_path, change):
    """Run the real isolated checker against an empty uv-created environment."""
    module = backend()
    manifest, _ = module.load_evidence()
    venv = tmp_path / "build"
    subprocess.run(["uv", "venv", "--no-python-downloads", "--python", sys.executable, str(venv)], check=True)
    purelib = subprocess.check_output([str(venv / "bin/python"), "-I", "-c",
                                       "import sysconfig; print(sysconfig.get_path('purelib'))"], text=True).strip()
    # Synthetic installed METADATA distinguishes exact version checks from absence.
    for package in manifest["packages"]:
        name, version = package["name"], package["version"]
        if change == "missing" and name == "hatchling":
            continue
        if change == "version" and name == "hatchling":
            version = "0.0.0"
        info = Path(purelib) / (name.replace("-", "_") + "-" + version + ".dist-info")
        info.mkdir()
        (info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n")
    if change == "extra":
        info = Path(purelib) / "unregistered-1.dist-info"
        info.mkdir()
        (info / "METADATA").write_text("Metadata-Version: 2.1\nName: unregistered\nVersion: 1\n")
    expected = tmp_path / "inputs.json"
    expected.write_text(json.dumps(manifest))
    result = subprocess.run([str(venv / "bin/python"), "-I", str(module.BUILDER),
                             "inspect", str(expected), str(tmp_path / "inventory.json")],
                            capture_output=True, text=True)
    assert result.returncode != 0
    assert "build distribution drift" in result.stderr
    actual = json.loads((tmp_path / "inventory.json").read_text())["actual"]
    if change == "missing":
        assert not any(line.startswith("hatchling==") for line in actual)
    elif change == "version":
        assert "hatchling==0.0.0" in actual
    else:
        assert "unregistered==1" in actual


def test_provision_handoff_uses_one_fixture_for_both_subjects(monkeypatch, tmp_path):
    sentinel = (tmp_path / "acceptance.lock", {"registered": "unit test only"})
    calls = []
    monkeypatch.setattr(gate, "APPROVED_DEPENDENCIES", sentinel)
    monkeypatch.setattr(gate, "provision_locked", lambda *args: calls.append(args))
    for label, sha in (("baseline", gate.BASELINE), ("candidate", gate.CANDIDATE)):
        gate.provision(tmp_path / label, sha, tmp_path, label)
    assert [call[-2:] for call in calls] == [sentinel, sentinel]
    assert [call[1] for call in calls] == [gate.BASELINE, gate.CANDIDATE]


def test_failed_provisioning_cannot_finalize_as_pass(tmp_path):
    error = RuntimeError("build backend missing")
    gate.finalize(tmp_path, [], "smoke", error)
    assert json.loads((tmp_path / "summary.json").read_text())["outcome"] == "FAIL"


@pytest.mark.skipif(os.environ.get("ISSUE1250_BUILD_INTEGRATION") != "1",
                    reason="explicit pinned-download preparation integration only")
def test_real_cold_baseline_and_candidate_provisioning(tmp_path, monkeypatch):
    """Build/install both frozen projects and verify exact build and target inventories.

    Calls only the internal preparation seam. No acceptance nodes, main(),
    activation or PID/signal tests. Each subject gets an empty private uv cache.
    """
    module = backend()
    fixture = PROPOSAL / "acceptance.lock"
    expected = json.loads((PROPOSAL / "proposal.json").read_text())
    build_inputs, _ = module.load_evidence()
    evidence_root = Path(os.environ.get("ISSUE1250_BUILD_EVIDENCE", tmp_path / "evidence"))
    evidence_root.mkdir(parents=True, exist_ok=True)
    with approval_validation.capture(evidence_root) as qualification:
        inventories = []
        for label, sha in (("baseline", gate.BASELINE), ("candidate", gate.CANDIDATE)):
            root, evidence = tmp_path / label, evidence_root / label
            evidence.mkdir()
            subprocess.run(["git", "clone", "--shared", "--no-checkout", str(ROOT), str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "checkout", "--detach", sha], check=True)
            cache = tmp_path / (label + "-cold-cache")
            monkeypatch.setenv("UV_CACHE_DIR", str(cache))
            assert not cache.exists() and not (root / ".venv").exists()
            gate.write_json(evidence / f"{label}-cold-start.json", {
                "run_id": qualification["run_id"], "sha": sha, "cache": str(cache),
                "subject_root": str(root), "cache_absent": not cache.exists(),
                "venv_absent": not (root / ".venv").exists(),
            })
            gate.provision_locked(root, sha, evidence, label, fixture, expected)
            assert hashlib.sha256((root / "uv.lock").read_bytes()).hexdigest() == expected["lock_sha256"]
            assert json.loads((evidence / f"{label}-freeze-diff.json").read_text())["actual"] == expected["freeze"]
            inventory = json.loads((evidence / f"{label}-build-inventory.json").read_text())
            inventories.append(inventory["actual"])
            assert inventory["actual"] == sorted(f"{p['name']}=={p['version']}" for p in build_inputs["packages"])
            python = root / ".venv/bin/python"
            installed = gate.command([str(python), "-I", "-c",
                "import genia, importlib.metadata as m; "
                "print(list(genia.__path__)); print(m.distribution('genia').read_text('direct_url.json'))"],
                tmp_path, evidence, label + "-installed-project")
            assert str(root / "src/genia") in installed
            assert '"editable": true' in installed
            assert (root / ".venv/bin/genia").is_file()
            # Frontend metadata must agree with installed RECORD, not just freeze.
            gate.command([str(python), "-I", "-c",
                "import base64,csv,hashlib; from importlib import metadata; "
                "d=metadata.distribution('genia'); "
                "r=next(d.locate_file(f) for f in d.files if str(f).endswith('.dist-info/RECORD')); "
                "p=r.parent/'direct_url.json'; "
                "row=next(x for x in csv.reader(r.open()) if x[0].endswith('/direct_url.json')); "
                "assert row[1]=='sha256='+base64.urlsafe_b64encode(hashlib.sha256(p.read_bytes()).digest()).rstrip(b'=').decode(); "
                "assert int(row[2])==len(p.read_bytes()); print('editable RECORD verified')"],
                tmp_path, evidence, label + "-editable-record")
            assert not list(evidence.glob("*-build-env-*"))
            gate.clean(root, sha)
            gate.manifest(evidence)
        assert inventories[0] == inventories[1]



@pytest.mark.parametrize("override", ["UV_INDEX_URL", "PIP_INDEX_URL", "UV_NO_VERIFY_HASHES", "UV_PROJECT_ENVIRONMENT"])
def test_dependency_configuration_override_fails_before_command(monkeypatch, tmp_path, override):
    module = backend()
    monkeypatch.setenv(override, "unregistered")
    calls = []
    with pytest.raises(RuntimeError, match="unregistered dependency configuration"):
        module.check_runtime(tmp_path, tmp_path, "unit", lambda *args: calls.append(args))
    assert calls == []


def test_incorrect_uv_version_is_rejected(tmp_path):
    with pytest.raises(RuntimeError, match="requires uv 0.13.5"):
        backend().check_runtime(tmp_path, tmp_path, "unit", lambda *args: "uv 0.13.6")


def test_build_installs_only_hashed_direct_requirements_and_local_editable(tmp_path):
    """Capture acquisition flags; fake the backend output only for command inspection."""
    module = backend()
    inputs = module.load_evidence()
    calls = []

    def command(argv, root, evidence, label):
        """Emulate the built wheel/report; never download or execute a resolver."""
        calls.append(argv)
        if label.endswith("build-editable"):
            output = Path(argv[-2])
            wheel = output / "genia-0.1.14-py3-none-any.whl"
            wheel.write_bytes(b"unit wheel")
            Path(argv[-1]).write_text(json.dumps({"wheel": wheel.name,
                "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest()}))
        return ""

    module.install_editable(tmp_path, tmp_path, "unit", command, inputs)
    pip_calls = [args for args in calls if "install" in args]
    assert len(pip_calls) == 2
    assert all("--no-deps" in args and "--no-index" in args for args in pip_calls)
    assert "--require-hashes" in pip_calls[0] and "--only-binary" in pip_calls[0]
    assert all("--no-build-isolation" not in args and "lock" not in args for args in calls)
    assert not list(tmp_path.glob("*-build-env-*"))
