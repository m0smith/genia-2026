"""Manual-only hosted packaging collection support; no activation or acceptance.

Bootstrap only immutable official toolchain archives, run exactly the mandatory
cold-cache preparation node, retain command/JUnit/source identity and failures.
This producer cannot mint independently verified provenance or approval receipts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET

from . import approval_validation as qualification

ROOT = qualification.ROOT
POLICY = Path(__file__).with_name("hosted-policy.json")


def guard(environment):
    """Require exact-source attempt-1 authorized manual dispatch on supported hosted OS."""
    sha = environment.get("REQUESTED_SHA", "")
    import re

    if (
        environment.get("GITHUB_EVENT_NAME") != "workflow_dispatch"
        or environment.get("GITHUB_REPOSITORY") != "m0smith/genia-2026"
        or environment.get("AUTHORIZED") != "true"
        or environment.get("GITHUB_RUN_ATTEMPT") != "1"
        or not re.fullmatch(r"[0-9a-f]{40}", sha)
        or environment.get("GITHUB_SHA") != sha
        or environment.get("GITHUB_WORKFLOW_SHA") != sha
        or environment.get("RUNNER_OS") != "Linux"
        or environment.get("RUNNER_ARCH") != "X64"
        or environment.get("ImageOS") != "ubuntu24"
    ):
        raise RuntimeError("hosted collection dispatch is not exact-source authorized attempt 1")
    return sha


def bootstrap_python(work):
    """Install the hash-pinned official Ubuntu CPython build into a new private cache.

    The official distribution/installer is trusted only after its recorded release
    asset digest matches. No hosted/toolchain execution occurs during preparation.
    Never fall back to a pre-existing mutable runner Python on installation error.
    """
    policy = json.loads(POLICY.read_text())
    work.mkdir(parents=True, exist_ok=False)
    archive = work / "python.tar.gz"
    with urllib.request.urlopen(policy["python"]["url"], timeout=60) as response:
        content = response.read(110 * 1024**2 + 1)
    if (
        len(content) > 110 * 1024**2
        or hashlib.sha256(content).hexdigest() != policy["python"]["sha256"]
    ):
        raise RuntimeError("pinned CPython distribution digest mismatch")
    archive.write_bytes(content)
    unpacked, cache = work / "official-distribution", work / "private-tool-cache"
    unpacked.mkdir()
    # Qualification ZIPs never use tar; this is a separate hash-trusted official installer.
    subprocess.run(["tar", "-xzf", str(archive), "-C", str(unpacked)], check=True)
    environment = {
        **os.environ,
        "AGENT_TOOLSDIRECTORY": str(cache),
        "RUNNER_TOOL_CACHE": str(cache),
    }
    subprocess.run(["bash", "setup.sh"], cwd=unpacked, env=environment, check=True)
    installed = cache / "Python/3.12.14/x64"
    python = installed / "bin/python"
    environment["LD_LIBRARY_PATH"] = str(installed / "lib")
    version = subprocess.check_output(
        [str(python), "-c", "import platform; print(platform.python_version())"],
        env=environment,
        text=True,
    ).strip()
    if version != policy["python"]["version"]:
        raise RuntimeError("installed CPython version drift")
    with Path(os.environ["GITHUB_PATH"]).open("a") as stream:
        stream.write(str(installed / "bin") + "\n")
    with Path(os.environ["GITHUB_ENV"]).open("a") as stream:
        stream.write("LD_LIBRARY_PATH=" + str(installed / "lib") + "\n")
    print("Pinned CPython installed; version " + version)


def bootstrap_uv(work):
    """Install only the direct hash-pinned uv wheel into the private approved Python."""
    policy = json.loads(POLICY.read_text())
    if sys.version_info[:3] != (3, 12, 14):
        raise RuntimeError("uv bootstrap requires the pinned CPython 3.12.14 first")
    requirements = work / "uv-requirements.txt"
    requirements.write_text(
        f"uv @ {policy['uv']['url']} --hash=sha256:{policy['uv']['wheel_sha256']}\n"
    )
    subprocess.run([sys.executable, "-m", "ensurepip", "--upgrade"], check=True)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "--isolated",
            "--disable-pip-version-check",
            "install",
            "--no-deps",
            "--no-index",
            "--require-hashes",
            "-r",
            str(requirements),
        ],
        check=True,
    )
    binary = Path(shutil.which("uv")).resolve()
    if qualification.sha256(binary) != policy["uv"]["binary_sha256"]:
        raise RuntimeError("installed uv binary digest mismatch")
    print("Pinned uv binary verified")


def collect(work):
    """Execute only real cold-cache packaging, retaining exact source and JUnit outcomes."""
    sha = guard(os.environ)
    if work.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("qualification work must be outside candidate checkout")
    work.mkdir(parents=True, exist_ok=True)
    output, runner, cache = work / "qualification", work / "test-runner", work / "runner-cache"
    if any(path.exists() for path in (output, runner, cache, work / "pytest-tmp")):
        raise RuntimeError("hosted collection requires fresh output/environments/caches")

    def git(*args):
        """Read exact local checkout identity without mutating the source tree."""
        return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()

    if git("rev-parse", "HEAD") != sha or git("status", "--porcelain"):
        raise RuntimeError("hosted checkout source/status mismatch")
    source = {
        "commit_sha": sha,
        "tree_sha": git("rev-parse", "HEAD^{tree}"),
        "workflow_sha256": qualification.sha256(
            ROOT / ".github/workflows/issue-1250-qualification.yml"
        ),
    }
    lock = ROOT / "uv.lock"
    expected = qualification.inputs()
    lock.write_bytes((ROOT / "tools/issue_1250" / expected["runtime"]["lock_file"]).read_bytes())
    clean_env = {
        key: value
        for key, value in os.environ.items()
        if key
        not in {
            "GH_TOKEN",
            "GITHUB_TOKEN",
            "ACTIONS_RUNTIME_TOKEN",
            "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
        }
    }
    clean_env["UV_CACHE_DIR"] = str(cache)
    with (work / "bootstrap-runner.log").open("w") as log:
        subprocess.run(
            [
                "uv",
                "--no-config",
                "sync",
                "--dev",
                "--locked",
                "--no-build",
                "--no-install-project",
                "--python",
                sys.executable,
            ],
            cwd=ROOT,
            env={**clean_env, "UV_PROJECT_ENVIRONMENT": str(runner)},
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    environment = {
        **clean_env,
        "ISSUE1250_BUILD_INTEGRATION": "1",
        "ISSUE1250_BUILD_EVIDENCE": str(output),
    }
    argv = [
        "uv",
        "--no-config",
        "run",
        "--no-project",
        "--no-sync",
        "--python",
        str(runner / "bin/python"),
        "pytest",
        "-n",
        "0",
        "-q",
        "--basetemp=" + str(work / "pytest-tmp"),
        "--junitxml=" + str(work / "junit.xml"),
        qualification.NODE,
    ]
    with (work / "pytest.log").open("w") as log:
        result = subprocess.run(
            argv, cwd=ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT, check=False
        )
    output.mkdir(exist_ok=True)
    for name in ("pytest.log", "junit.xml"):
        if (work / name).exists():
            shutil.copyfile(work / name, output / name)
    (output / "source-identity.json").write_text(json.dumps(source, indent=2) + "\n")
    passed = result.returncode == 0
    try:
        cases = ET.parse(output / "junit.xml").findall(".//testcase")
        passed = (
            passed and len(cases) == 1 and cases[0].get("name") == qualification.NODE.split("::")[1]
        )
        passed = passed and all(
            cases[0].find(tag) is None for tag in ("failure", "error", "skipped")
        )
    except (OSError, ET.ParseError, IndexError):
        passed = False
    (output / "collection-result.json").write_text(
        json.dumps(
            {
                "outcome": "PASS" if passed else "FAIL",
                "rc": result.returncode if not passed else 0,
                "test_node": qualification.NODE,
                "argv": argv,
                "source": source,
            },
            indent=2,
        )
        + "\n"
    )
    qualification.manifest(output)
    if not passed or git("rev-parse", "HEAD") != sha or git("status", "--porcelain"):
        raise RuntimeError("mandatory real hosted packaging collection failed")


def publish(work, step_outcome):
    """Finalize artifacts even on failure; never turn a failed collection into PASS."""
    output = work / "qualification"
    output.mkdir(parents=True, exist_ok=True)
    for name, source in (
        ("bootstrap.log", work / "bootstrap-runner.log"),
        ("dispatch.json", work / "diagnostics/dispatch.json"),
    ):
        if source.exists():
            shutil.copyfile(source, output / name)
    for name in ("bootstrap.log", "uv-bootstrap.log"):
        source = work / "diagnostics" / name
        if source.exists():
            # Toolchain failures remain diagnostic; the Actions run cannot qualify.
            shutil.copyfile(source, output / name)
    result = output / "collection-result.json"
    if step_outcome != "success" or not result.exists():
        result.write_text(
            json.dumps(
                {"outcome": "FAIL", "rc": 1, "reason": "collection did not complete successfully"}
            )
            + "\n"
        )
    qualification.manifest(output)
    print("qualification_manifest_sha256=" + qualification.sha256(output / "manifest.json"))


def main(argv=None):
    """Workflow-only bootstrap/collect/publish commands; no dispatch or activation API."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("bootstrap-python", "bootstrap-uv", "collect", "publish"))
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--step-outcome", default="failure")
    args = parser.parse_args(argv)
    if args.mode == "bootstrap-python":
        bootstrap_python(args.work)
    elif args.mode == "bootstrap-uv":
        bootstrap_uv(args.work)
    elif args.mode == "collect":
        collect(args.work)
    else:
        publish(args.work, args.step_outcome)


if __name__ == "__main__":
    main()
