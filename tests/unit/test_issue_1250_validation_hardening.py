"""Deterministic host-local packaging negatives; no acceptance or semantic oracles."""

import base64
import csv
import hashlib
from pathlib import Path
from types import SimpleNamespace
import sys
import zipfile

import pytest

from tools.issue_1250 import build_backend, editable_builder as frontend


@pytest.fixture
def installed_record(tmp_path, monkeypatch):
    """Minimal installed distribution with real file hashes and RECORD self-row."""
    environment = tmp_path / "venv"
    info = environment / "lib/python3.12/site-packages/genia-0.1.14.dist-info"
    info.mkdir(parents=True)
    data = info / "METADATA"
    data.write_bytes(b"Name: genia\nVersion: 0.1.14\n")
    record = info / "RECORD"
    digest = base64.urlsafe_b64encode(hashlib.sha256(data.read_bytes()).digest()).rstrip(b"=").decode()
    record.write_text(f"{info.name}/METADATA,sha256={digest},{data.stat().st_size}\n{info.name}/RECORD,,\n")
    distribution = SimpleNamespace(files=[Path(info.name) / "RECORD"],
                                   locate_file=lambda path: info.parent / path)
    monkeypatch.setattr(frontend.metadata, "distribution", lambda name: distribution)
    monkeypatch.setattr(sys, "prefix", str(environment))
    return record, distribution


@pytest.mark.parametrize("change", ["missing", "malformed", "empty", "duplicate", "bad-hash", "bad-size", "escape", "ambiguous"])
def test_record_corruption_rejected_before_frontend_mutation(installed_record, tmp_path, change):
    record, distribution = installed_record
    original = record.read_text()
    if change == "missing":
        record.unlink()
    elif change == "malformed":
        record.write_text('"unterminated\n')
    elif change == "empty":
        record.write_text("")
    elif change == "duplicate":
        record.write_text(original + original.splitlines()[0] + "\n")
    elif change == "bad-hash":
        record.write_text(original.replace("sha256=", "sha256=INVALID"))
    elif change == "bad-size":
        rows = list(csv.reader(original.splitlines()))
        rows[0][2] = "9999"
        with record.open("w", newline="") as out:
            csv.writer(out).writerows(rows)
    elif change == "escape":
        record.write_text(original + "../../../../../outside,sha256=x,1\n")
    elif change == "ambiguous":
        distribution.files.append(Path("other.dist-info/RECORD"))
    with pytest.raises(RuntimeError, match="RECORD"):
        frontend.record_editable(tmp_path.resolve())
    assert not (record.parent / "direct_url.json").exists()


def test_record_verifier_rejects_changed_editable_metadata(installed_record, tmp_path):
    record, _ = installed_record
    frontend.record_editable(tmp_path.resolve())
    (record.parent / "direct_url.json").write_text("modified")
    with pytest.raises(RuntimeError, match="RECORD"):
        frontend.verify_record(record)


@pytest.mark.parametrize("change", ["dynamic-missing", "dynamic-version", "dynamic-url", "build-failure",
                                  "backend-path-list", "backend-path-string", "backend-path-empty"])
def test_actual_frontend_build_negatives(tmp_path, monkeypatch, change):
    """Inject a backend, then exercise real requirement/backend-path/build branches."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(frontend, "inspect_environment", lambda *args: ["hatchling==1.33.0"])
    versions = {"hatchling": "1.33.0", "editables": "0.6"}

    def version(name):
        """Model only the declared pinned build inventory."""
        if name not in versions:
            raise frontend.metadata.PackageNotFoundError(name)
        return versions[name]

    monkeypatch.setattr(frontend.metadata, "version", version)
    dynamic = {"dynamic-missing": ["unregistered>=1"], "dynamic-version": ["editables>=999"],
               "dynamic-url": ["editables @ https://example.invalid/unapproved.whl"]}.get(change, [])

    def failing_build(*args):
        """A real backend exception must propagate, never produce a successful wheel."""
        raise RuntimeError("injected build_editable failure")

    monkeypatch.setitem(sys.modules, "hatchling", SimpleNamespace(build=SimpleNamespace(
        get_requires_for_build_editable=lambda *args: dynamic, build_editable=failing_build)))
    text = '[build-system]\nrequires=["hatchling"]\nbuild-backend="hatchling.build"\n'
    if change.startswith("backend-path"):
        text += 'backend-path=' + {"backend-path-list": '["../escape"]', "backend-path-string": '"bad"',
                                   "backend-path-empty": '[]'}[change] + '\n'
    (tmp_path / "pyproject.toml").write_text(text)
    with pytest.raises(RuntimeError):
        frontend.build({}, tmp_path, tmp_path / "wheel", tmp_path / "report.json")
    assert not (tmp_path / "wheel").exists()


@pytest.mark.parametrize("kind,value", [("python", (3, 12, 13)), ("implementation", "PyPy"),
                                        ("system", "Darwin"), ("machine", "aarch64")])
def test_unsupported_toolchain_fails_before_uv(tmp_path, monkeypatch, kind, value):
    if kind == "python":
        monkeypatch.setattr(build_backend.sys, "version_info", value)
    else:
        attr = {"implementation": "python_implementation", "system": "system", "machine": "machine"}[kind]
        monkeypatch.setattr(build_backend.platform, attr, lambda: value)
    calls = []
    with pytest.raises(RuntimeError, match="CPython 3.12.14 Linux x86_64"):
        build_backend.check_runtime(tmp_path, tmp_path, "unit", lambda *args: calls.append(args))
    assert calls == []


def test_editable_wheel_modified_after_build_is_rejected(tmp_path):
    inputs = build_backend.load_evidence()
    calls = []

    def command(argv, root, evidence, label):
        """Retain an expected hash, then simulate postverification wheel corruption."""
        calls.append(label)
        if label.endswith("build-editable"):
            import json
            wheel = Path(argv[-2]) / "genia-0.1.14-py3-none-any.whl"
            wheel.write_bytes(b"modified wheel")
            Path(argv[-1]).write_text(json.dumps({"wheel": wheel.name,
                "wheel_sha256": hashlib.sha256(b"original wheel").hexdigest()}))
        return ""

    with pytest.raises(RuntimeError, match="wheel modified"):
        build_backend.install_editable(tmp_path, tmp_path, "unit", command, inputs)
    assert "unit-project-install" not in calls
    assert not list(tmp_path.glob("*-build-env-*"))


@pytest.mark.parametrize("corruption", ["wrong-hash", "changed-bytes"])
def test_real_uv_rejects_corrupt_hash_pinned_backend_wheel(tmp_path, corruption):
    """Use real uv on a local wheel and empty venv; no network/index or mocks."""
    import subprocess
    wheel = tmp_path / "unit_backend-1-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as out:
        out.writestr("unit_backend.py", "value = 1\n")
        out.writestr("unit_backend-1.dist-info/METADATA", "Metadata-Version: 2.1\nName: unit-backend\nVersion: 1\n")
        out.writestr("unit_backend-1.dist-info/WHEEL", "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n")
        out.writestr("unit_backend-1.dist-info/RECORD", "")
    expected = hashlib.sha256(wheel.read_bytes()).hexdigest()
    if corruption == "wrong-hash":
        expected = "0" * 64
    else:
        with wheel.open("ab") as stream:
            stream.write(b"changed after registration")
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(f"unit-backend @ {wheel.as_uri()} --hash=sha256:{expected}\n")
    environment = tmp_path / "empty"
    subprocess.run(["uv", "--no-config", "venv", "--no-python-downloads", "--python", sys.executable,
                    str(environment)], check=True, capture_output=True)
    result = subprocess.run(["uv", "--no-config", "--no-cache", "pip", "install", "--python",
                             str(environment / "bin/python"), "--no-deps", "--no-index",
                             "--require-hashes", "-r", str(requirements)], capture_output=True, text=True)
    assert result.returncode != 0
    assert "hash mismatch" in (result.stdout + result.stderr).lower()
