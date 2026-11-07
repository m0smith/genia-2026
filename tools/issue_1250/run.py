"""Temporary #1250 G0–G2 orchestration; existing pytest nodes remain the oracle.

Run as PID 1 in a disposable Linux PID/mount namespace. Only direct subprocesses
are waited for: adopted zombies deliberately remain observable until namespace
exit. Subjects are separate frozen checkouts; mutations occur only in scratch
clones. Any unexpected exit, count, skip, drift or failure aborts advancement.
No network credentials, full environment dumps, G3–G5 or dispatch operations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

BASELINE = "0b25d2b45722f4397fd712f2f4b8eb3ea294f6e5"
CANDIDATE = "e3562f620020023ea39c44273068872d6bc73fe6"
R4 = "38eb980ee5fc95bdad45f197543861c2c2eb6046"
LOCK = "27ca5a9328ba8641ce18078782c7edecdc8a753aa6b4fd3ca57932a66d49f291"
HERE = Path(__file__).resolve().parent
REGISTRATION = json.loads((HERE / "registration.json").read_text())
TEARDOWN = [n for n in REGISTRATION["focused"] if "test_r28_mcp_fixture_teardown.py::" in n]


def write_json(path, value):
    """Write public, explicitly selected evidence as readable JSON."""
    path.write_text(json.dumps(value, indent=2) + "\n")


def command(argv, cwd, evidence, label):
    """Run one preparation command, retaining argv, output and exit before raising."""
    result = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, check=False)
    (evidence / f"{label}.log").write_text(result.stdout)
    write_json(evidence / f"{label}.json", {"argv": argv, "cwd": str(cwd), "rc": result.returncode})
    print(f"{label}: rc={result.returncode}", flush=True)
    if result.returncode:
        raise RuntimeError(f"{label} failed; see retained log")
    return result.stdout.strip()


def git(root, *args):
    """Read a frozen checkout's identity/content; do not mutate its tracked files."""
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def clean(root, sha):
    """Reject wrong subject SHA or any tracked/untracked checkout drift."""
    if git(root, "rev-parse", "HEAD") != sha or git(root, "status", "--porcelain"):
        raise RuntimeError(f"subject identity/status drift: {root}")


def context():
    """Passively capture ancestor/descendant process identities and signal masks.

    Record executable basenames rather than arbitrary argv/environment contents.
    /proc races are expected; no signal, ptrace, subreaper or process mutation.
    """
    table = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry / "stat").read_text().rsplit(")", 1)[1].split()
            status = dict(line.split(":", 1) for line in (entry / "status").read_text().splitlines())
            table[int(entry.name)] = {
                "ppid": int(fields[1]), "pgid": int(fields[2]), "sid": int(fields[3]),
                "tty": int(fields[4]), "start": fields[19],
                **{k: status[k].strip() for k in ("Name", "State", "SigBlk", "SigIgn", "SigCgt", "SigPnd", "ShdPnd")},
            }
        except (OSError, ProcessLookupError, KeyError):
            continue
    # The namespace contains only this gate and its children; all entries are relevant.
    return table


def provision(root, sha, evidence, label):
    """Solve locally, sync locked, and fail on historical dependency/lock drift."""
    clean(root, sha)
    started = time.monotonic()
    command(["uv", "lock", "--no-python-downloads", "--python", sys.executable], root, evidence, label + "-lock")
    lock_bytes = (root / "uv.lock").read_bytes()
    (evidence / f"{label}.lock").write_bytes(lock_bytes)
    digest = hashlib.sha256(lock_bytes).hexdigest()
    command(["uv", "sync", "--dev", "--locked", "--no-python-downloads", "--python", sys.executable], root, evidence, label + "-sync")
    freeze = command(["uv", "pip", "freeze"], root, evidence, label + "-freeze").splitlines()
    actual = sorted(line.lower() for line in freeze if not line.startswith("-e "))
    write_json(evidence / f"{label}-identity.json", {
        "sha": sha, "tree": git(root, "rev-parse", "HEAD^{tree}"),
        "lock_sha256": digest, "seconds": time.monotonic() - started,
        "non_editable_count": len(actual), "status": git(root, "status", "--porcelain"),
    })
    if digest != LOCK or actual != REGISTRATION["freeze"]:
        raise RuntimeError("lock/freeze drift from approved evidence")
    clean(root, sha)


def run_nodes(root, nodes, evidence, label, *, workers=0, defect=None):
    """Invoke exact IDs once; require exact JUnit membership and expected outcomes.

    A negative control succeeds only for rc=1 and the specific assertion/timeout
    at every selected node; collection errors, unrelated failures and skips fail.
    Logs/context/results are written before checking the exit or XML.
    """
    xml = evidence / f"{label}.xml"
    argv = ["uv", "run", "--no-sync", "pytest", "-n", str(workers), "-v", "--tb=short",
            "--maxfail=1", f"--junitxml={xml}", *nodes]
    write_json(evidence / f"{label}-pre.json", context())
    start = time.monotonic()
    with (evidence / f"{label}.log").open("w") as log, (evidence / f"{label}-process.jsonl").open("w") as trace:
        proc = subprocess.Popen(argv, cwd=root, stdout=log, stderr=subprocess.STDOUT)
        last = None
        while True:
            snapshot = context()
            if snapshot != last:
                trace.write(json.dumps({"seconds": time.monotonic() - start, "processes": snapshot}) + "\n")
                trace.flush()
                last = snapshot
            if proc.poll() is not None:
                break
            time.sleep(0.1)
        rc = proc.wait()
    write_json(evidence / f"{label}-result.json", {
        "argv": argv, "cwd": str(root), "rc": rc, "seconds": time.monotonic() - start,
        "expected_defect": defect,
    })
    print(f"{label}: rc={rc}; log={evidence / (label + '.log')}", flush=True)
    cases = ET.parse(xml).findall(".//testcase")
    ids = [case.attrib["classname"].replace(".", "/") + ".py::" + case.attrib["name"] for case in cases]
    if sorted(ids) != sorted(nodes) or len(ids) != len(nodes):
        raise RuntimeError(f"{label}: incomplete or unexpected JUnit membership")
    for case in cases:
        if case.find("skipped") is not None or case.find("error") is not None:
            raise RuntimeError(f"{label}: skip/error is not acceptable evidence")
        failure = case.find("failure")
        if defect is None:
            if failure is not None or rc != 0:
                raise RuntimeError(f"{label}: acceptance node failed")
        elif rc != 1 or failure is None or defect not in "".join(failure.itertext()):
            raise RuntimeError(f"{label}: mutant did not fail at the intended observation")


def scratch(baseline, work, evidence, kind):
    """Create a disposable baseline clone and apply only the approved mutant."""
    root = work / kind
    command(["git", "clone", "--shared", "--no-checkout", str(baseline), str(root)], work, evidence, kind + "-clone")
    command(["git", "checkout", "--detach", BASELINE], root, evidence, kind + "-checkout")
    provision(root, BASELINE, evidence, kind)
    if kind == "without-r4":
        patch = subprocess.check_output(["git", "-C", str(baseline), "show", R4, "--format=", "--", "tests/fixtures/r28_mcp_helpers.py"])
        patch_path = evidence / "r4-original.patch"
        patch_path.write_bytes(patch)
        command(["git", "apply", "--reverse", "--check", str(patch_path)], root, evidence, kind + "-check")
        command(["git", "apply", "--reverse", str(patch_path)], root, evidence, kind + "-apply")
    else:
        path = root / "hosts/python/mcp_launch.py"
        before = path.read_text()
        target = "            child.send_signal(signum)"
        if before.count(target) != 1:
            raise RuntimeError("signal-forwarding mutant target drift")
        path.write_text(before.replace(target, "            pass  # scratch negative control: do not forward"))
    diff = git(root, "diff", "--no-ext-diff")
    (evidence / f"{kind}.patch").write_text(diff + "\n")
    expected = "tests/fixtures/r28_mcp_helpers.py" if kind == "without-r4" else "hosts/python/mcp_launch.py"
    if git(root, "diff", "--name-only") != expected or not diff:
        raise RuntimeError("mutant escaped its approved scratch path")
    return root


def negative_controls(baseline, work, evidence, signals, probe):
    """Require both reviewed mutants to fail existing tests at their intended defect."""
    root = scratch(baseline, work, evidence, "without-r4")
    run_nodes(root, [probe], evidence, "negative-r4", defect="a launch left processes behind")
    root = scratch(baseline, work, evidence, "without-forwarding")
    for index, node in enumerate(signals):
        # Each mutant node is an independent command so every signal must be detected.
        defect = "assert _wait_until(lambda: session.proc.poll() is not None)" if index == 0 else "subprocess.TimeoutExpired"
        run_nodes(root, [node], evidence, f"negative-signal-{index}", defect=defect)


def provenance(evidence):
    """Record allowlisted hosted provisioning, Python/uv, PID1 and cgroup evidence."""
    uv = Path(shutil.which("uv")).resolve()
    write_json(evidence / "provenance.json", {
        "runner": {key: os.environ.get(key) for key in (
            "RUNNER_NAME", "RUNNER_OS", "RUNNER_ARCH", "ImageOS", "ImageVersion",
            "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_JOB", "GITHUB_WORKFLOW_REF", "GITHUB_WORKFLOW_SHA",
        )},
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        "python": sys.version, "executable": sys.executable, "platform": platform.platform(),
        "uv": str(uv), "uv_sha256": hashlib.sha256(uv.read_bytes()).hexdigest(),
        "home": os.environ["HOME"], "cache": os.environ["UV_CACHE_DIR"],
        "pid1": Path("/proc/1/cmdline").read_bytes().decode().replace("\0", " "),
        "cgroup": Path("/proc/self/cgroup").read_text(),
        "limits": Path("/proc/self/limits").read_text(),
        "context": context(),
    })
    command(["uv", "--version"], evidence, evidence, "uv-version")
    # Read only control files: no broad environment or credential dump.
    cgroup = Path("/sys/fs/cgroup") / Path("/proc/self/cgroup").read_text().strip().split("::", 1)[1].lstrip("/")
    values = {}
    while cgroup.is_relative_to("/sys/fs/cgroup"):
        values[str(cgroup)] = {name: (cgroup / name).read_text().strip()
                              for name in ("cpu.max", "memory.max") if (cgroup / name).exists()}
        cgroup = cgroup.parent
    write_json(evidence / "cgroup-limits.json", values)
    return values


def main():
    """Run G0 then the requested bounded gate; write manifest even on failure.

    negative-validation is local infrastructure validation only: positive controls
    followed by both mutants, never candidate acceptance. Hosted modes require
    provisioning identity and the approved 2-CPU / 8-GiB cgroup envelope.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("serial", "parallel", "negative-validation"))
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    evidence = work / "evidence"
    evidence.mkdir(exist_ok=True)
    os.environ["HOME"] = str(work / "home")
    os.environ["UV_CACHE_DIR"] = str(work / "uv-cache")
    Path(os.environ["HOME"]).mkdir(exist_ok=True)
    try:
        if os.getpid() != 1:
            raise RuntimeError("requires disposable non-reaping PID 1 namespace")
        values = provenance(evidence)
        if args.stage != "negative-validation":
            for key in ("RUNNER_NAME", "ImageOS", "ImageVersion", "GITHUB_WORKFLOW_SHA"):
                if not os.environ.get(key):
                    raise RuntimeError(f"missing hosted provisioning provenance: {key}")
            if not any(v.get("cpu.max") == "200000 100000" and v.get("memory.max") == "8589934592" for v in values.values()):
                raise RuntimeError("required cgroup envelope absent")
        baseline, candidate = args.baseline.resolve(), args.candidate.resolve()
        if args.stage != "negative-validation":
            clean(candidate, CANDIDATE)
        original = json.loads((candidate / ".genia/process/issue-1250-d2b-green-closeout-stop.json").read_text())["full_attempt"]["failed_nodes"]
        if len(original) != 22 or len(set(original)) != 22:
            raise RuntimeError("frozen original-node registration drift")
        signals = [n for n in original if "test_sighup_" in n or "test_a_signal_to_" in n]
        probe = next(n for n in original if "test_a_discover_probe_" in n)
        g0 = signals + [n for n in original[1:] if n not in signals] + TEARDOWN + [REGISTRATION["focused"][-1]]
        if len(signals) != 3 or len(g0) != 24 or len(TEARDOWN) != 2 or len(REGISTRATION["focused"]) != 15:
            raise RuntimeError("registered gate count drift")
        write_json(evidence / "registered.json", {"original": original, "focused": REGISTRATION["focused"], "g0": g0, "signals": signals, "teardown": TEARDOWN})
        provision(baseline, BASELINE, evidence, "baseline")
        run_nodes(baseline, signals + [probe] if args.stage == "negative-validation" else g0, evidence, "g0-main")
        negative_controls(baseline, work, evidence, signals, probe)
        clean(baseline, BASELINE)
        if args.stage != "negative-validation":
            provision(candidate, CANDIDATE, evidence, "candidate")
            if args.stage == "serial":
                run_nodes(candidate, REGISTRATION["focused"], evidence, "g1-focused")
                run_nodes(candidate, original, evidence, "g1-original")
                run_nodes(candidate, TEARDOWN, evidence, "g1-teardown")
                for index, node in enumerate(signals):
                    for repetition in range(1, 4):
                        run_nodes(candidate, [node], evidence, f"g1-signal-{index}-{repetition}")
            else:
                run_nodes(candidate, original + TEARDOWN, evidence, "g2-parallel", workers=2)
            clean(candidate, CANDIDATE)
    finally:
        # Preserve subject status even when a test/preparation command aborts.
        write_json(evidence / "final-status.json", {
            str(root): {"sha": git(root, "rev-parse", "HEAD"),
                        "status": git(root, "status", "--porcelain")}
            for root in (args.baseline.resolve(), args.candidate.resolve())
        })
        write_json(evidence / "manifest.json", {
            str(p.relative_to(evidence)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(evidence.rglob("*")) if p.is_file() and p.name != "manifest.json"
        })


if __name__ == "__main__":
    main()
