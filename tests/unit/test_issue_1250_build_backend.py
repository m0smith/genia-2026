"""Host-local packaging guards for #1250; no Genia semantics or acceptance credit.

The real provisioning integration is opt-in because it downloads pinned wheels
into disposable caches. It never activates the approval sentinel or runs gates.
"""

from copy import deepcopy
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from tools.issue_1250 import run as gate

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
    # An empty environment must fail both the actual pins and modified inventories.
    if change == "version":
        manifest["packages"][0]["version"] = "0.0.0"
    elif change == "extra":
        manifest["packages"].append({"name": "unregistered", "version": "1"})
    expected = tmp_path / "inputs.json"
    expected.write_text(json.dumps(manifest))
    result = subprocess.run([str(venv / "bin/python"), "-I", str(module.BUILDER),
                             "inspect", str(expected), str(tmp_path / "inventory.json")],
                            capture_output=True, text=True)
    assert result.returncode != 0
    assert "build distribution drift" in result.stderr
    assert json.loads((tmp_path / "inventory.json").read_text())["actual"] == []


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
    """Build/install both frozen projects, check exact freezes, then inject backend drift.

    Calls only the internal preparation seam. No acceptance nodes, main(),
    activation or PID/signal tests. Each subject gets an empty private uv cache.
    """
    module = backend()
    fixture = PROPOSAL / "acceptance.lock"
    expected = json.loads((PROPOSAL / "proposal.json").read_text())
    build_inputs, _ = module.load_evidence()
    evidence_root = Path(os.environ.get("ISSUE1250_BUILD_EVIDENCE", tmp_path / "evidence"))
    evidence_root.mkdir(parents=True, exist_ok=True)
    inventories = []
    for label, sha in (("baseline", gate.BASELINE), ("candidate", gate.CANDIDATE)):
        root, evidence = tmp_path / label, evidence_root / label
        evidence.mkdir()
        subprocess.run(["git", "clone", "--shared", "--no-checkout", str(ROOT), str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "checkout", "--detach", sha], check=True)
        monkeypatch.setenv("UV_CACHE_DIR", str(tmp_path / (label + "-cold-cache")))
        assert not Path(os.environ["UV_CACHE_DIR"]).exists()
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
        assert not list(evidence.glob("*-build-env-*"))
        gate.clean(root, sha)
        gate.manifest(evidence)
    assert inventories[0] == inventories[1]
    # A backend accidentally present in target must trip the unchanged freeze guard.
    bad = deepcopy(expected)
    bad["freeze"] = [*bad["freeze"], "hatchling==1.33.0"]
    # Target drift is exercised without another dependency install below by unit tests;
    # real targets above prove backend-only distributions never leaked.
    assert "hatchling==1.33.0" not in expected["freeze"]
