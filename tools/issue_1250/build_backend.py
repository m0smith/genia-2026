"""Pinned isolated PEP 660 provisioning for #1250's unapproved dependency proposal.

The project backend contract stays unchanged. Only these hash-registered wheels
are installed into a temporary build venv; target installation never resolves
build dependencies. No approval, acceptance, dispatch or semantic behavior here.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import re
import sys
import tempfile

INPUTS = Path(__file__).resolve().parent / "dependencies/proposed-build-2026-11-08"
BUILDER = Path(__file__).resolve().with_name("editable_builder.py")
EVIDENCE_SHA256 = "e1fae82b5e5358d7db86ede48903cda603eea0d26050de6827cf850e21a65404"
REQUIREMENTS_SHA256 = "96a6b7b227b6d8603b786f7dfdb2a825a915fbe910b3b59674b29b4490baab18"


def load_evidence():
    """Read literal hash-registered build inputs, rejecting absence or modification."""
    values = []
    for name, digest in (("build-evidence.json", EVIDENCE_SHA256),
                         ("build-requirements.txt", REQUIREMENTS_SHA256)):
        try:
            content = (INPUTS / name).read_bytes()
        except OSError as error:
            raise RuntimeError(f"missing build evidence: {name}") from error
        if hashlib.sha256(content).hexdigest() != digest:
            raise RuntimeError(f"modified build evidence: {name}")
        values.append(content)
    return json.loads(values[0]), values[1]


def check_runtime(root, evidence, label, command):
    """Enforce the evidenced Python/Linux/uv scope and reject config overrides."""
    if (platform.python_implementation() != "CPython" or sys.version_info[:3] != (3, 12, 14) or platform.system() != "Linux"
            or platform.machine() != "x86_64"):
        raise RuntimeError("dependency provisioning requires CPython 3.12.14 Linux x86_64")
    overrides = sorted(k for k in os.environ if k.startswith(("UV_", "PIP_")) and k not in {"UV_CACHE_DIR", "UV_RUN_RECURSION_DEPTH"})
    if overrides:
        raise RuntimeError("unregistered dependency configuration: " + ", ".join(overrides))
    version = command(["uv", "--no-config", "--version"], root, evidence, label + "-uv-version")
    if not re.match(r"^uv 0\.13\.5(?:\s|$)", version):
        raise RuntimeError("dependency provisioning requires uv 0.13.5")


def install_editable(root, evidence, label, command, inputs):
    """Build in a fresh isolated pinned venv and install the real editable wheel.

    Commands/outputs, expected inputs, complete build inventory and wheel digest
    survive temporary-venv cleanup on success or error. uv installs direct pinned
    wheels with hashes and no dependencies/index; no backend package enters the
    target. The PEP 660 frontend records PEP 610 editable source metadata after
    wheel installation. Any missing/drifting backend or install failure raises.
    """
    manifest, requirements = inputs
    inputs_file = evidence / f"{label}-build-inputs.json"
    inputs_file.write_text(json.dumps(manifest, indent=2) + "\n")
    requirements_file = evidence / f"{label}-build-requirements.txt"
    requirements_file.write_bytes(requirements)
    with tempfile.TemporaryDirectory(prefix=label + "-build-env-", dir=evidence) as temporary:
        work = Path(temporary)
        build_python = work / "venv/bin/python"
        wheel_dir = work / "wheel"
        wheel_dir.mkdir()
        command(["uv", "--no-config", "venv", "--no-python-downloads", "--python", sys.executable,
                 str(work / "venv")], root, evidence, label + "-build-venv")
        command(["uv", "--no-config", "pip", "install", "--python", str(build_python),
                 "--no-deps", "--require-hashes", "--no-index", "--only-binary", ":all:",
                 "-r", str(requirements_file)], root, evidence, label + "-build-install")
        inventory = evidence / f"{label}-build-inventory.json"
        command([str(build_python), "-I", str(BUILDER), "build", str(inputs_file),
                 str(root), str(wheel_dir), str(inventory)], root, evidence, label + "-build-editable")
        built = json.loads(inventory.read_text())
        filename = built["wheel"]
        if Path(filename).name != filename:
            raise RuntimeError("editable wheel path escaped build directory")
        wheel = wheel_dir / filename
        if hashlib.sha256(wheel.read_bytes()).hexdigest() != built["wheel_sha256"]:
            raise RuntimeError("editable wheel modified after build")
        target_python = root / ".venv/bin/python"
        wheel_requirements = evidence / f"{label}-project-requirements.txt"
        wheel_requirements.write_text(f"genia @ {wheel.as_uri()} --hash=sha256:{built['wheel_sha256']}\n")
        command(["uv", "--no-config", "pip", "install", "--python", str(target_python),
                 "--no-deps", "--no-index", "--require-hashes", "--reinstall", "-r", str(wheel_requirements)],
                root, evidence, label + "-project-install")
        command([str(target_python), "-I", str(BUILDER), "record", str(root)],
                root, evidence, label + "-editable-metadata")
