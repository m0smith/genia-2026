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
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

# Direct-script workflow entry and package-imported preparation tests share one helper.
if __package__:
    from . import build_backend
else:
    import build_backend

BASELINE = "0b25d2b45722f4397fd712f2f4b8eb3ea294f6e5"
CANDIDATE = "e3562f620020023ea39c44273068872d6bc73fe6"
R4 = "38eb980ee5fc95bdad45f197543861c2c2eb6046"
LOCK = "27ca5a9328ba8641ce18078782c7edecdc8a753aa6b4fd3ca57932a66d49f291"
HERE = Path(__file__).resolve().parent
REGISTRATION = json.loads((HERE / "registration.json").read_text())
INVENTORY = "tests/unit/test_model_b_slice_c_capability_evidence.py::test_every_slice_c_case_is_applicable_to_the_python_host"
SDK = "tests/unit/test_r28_mcp_architecture.py::test_no_mcp_sdk_import_or_dependency"
PROBE = "tests/unit/test_r28_mcp_conformance_lifecycle.py::test_a_discover_probe_launch_followed_by_a_session_launch_leaves_nothing_behind"
SIGNALS = (
    "tests/unit/test_r28_mcp_conformance_lifecycle.py::test_sighup_to_the_client_launched_process_stops_the_chain_and_cleans_up",
    "tests/unit/test_r28_mcp_stdio_lifecycle.py::test_a_signal_to_the_client_launched_process_stops_the_entire_chain_and_cleans_up[SIGTERM]",
    "tests/unit/test_r28_mcp_stdio_lifecycle.py::test_a_signal_to_the_client_launched_process_stops_the_entire_chain_and_cleans_up[SIGINT]",
)
TEARDOWN = (
    "tests/unit/test_r28_mcp_fixture_teardown.py::test_client_context_exception_reaps_its_command_and_descendants",
    "tests/unit/test_r28_mcp_fixture_teardown.py::test_context_exit_kills_and_reaps_a_sigterm_ignoring_direct_child",
)
IMAGE_KEYS = ("ImageOS", "ImageVersion", "RUNNER_OS", "RUNNER_ARCH")
RUN_KEYS = ("GITHUB_RUN_ID", "GITHUB_WORKFLOW_SHA", "GITHUB_RUN_ATTEMPT", "WORKFLOW_SHA")


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


# Independent approval must replace this sentinel in a separately reviewed change.
# The proposed fixture is deliberately unreachable from every acceptance caller.
APPROVED_DEPENDENCIES = None


def provision(root, sha, evidence, label):
    """Reject provisioning until independent approval registers immutable evidence.

    Baseline, candidate and scratch clones all enter here. No CLI/environment
    override can activate a proposal; historical LOCK/registration remain evidence.
    """
    if APPROVED_DEPENDENCIES is None:
        write_json(evidence / f"{label}-dependency-gate.json", {
            "outcome": "BLOCKED", "reason": "independent dependency baseline approval required",
        })
        raise RuntimeError("independent dependency baseline approval required")
    provision_locked(root, sha, evidence, label, *APPROVED_DEPENDENCIES)


def provision_locked(root, sha, evidence, label, fixture, expected):
    """Install one shared immutable lock and reject lock, declaration or freeze drift.

    Internal preparation seam: callers supply the fixture path and registered
    digest/pyproject/freeze values. Acceptance reaches it only through provision's
    approval gate. Save evidence before raising; never solve or overwrite an
    existing different lock. Locked sync validates freshness; hash checks before
    and after sync reject mutation. A separate hash-pinned build environment
    installs the real editable project without leaking backend packages into the
    target. Editable Genia's path is excluded from freeze.
    """
    clean(root, sha)
    started = time.monotonic()
    try:
        lock_bytes = fixture.read_bytes()
    except OSError as error:
        raise RuntimeError("missing dependency lock evidence") from error
    (evidence / f"{label}.lock").write_bytes(lock_bytes)
    digest = hashlib.sha256(lock_bytes).hexdigest()
    if digest != expected["lock_sha256"]:
        raise RuntimeError("dependency fixture lock digest mismatch")
    if hashlib.sha256((root / "pyproject.toml").read_bytes()).hexdigest() != expected["pyproject_sha256"]:
        raise RuntimeError("dependency declarations mismatch")
    target = root / "uv.lock"
    if target.is_symlink() or (target.exists() and target.read_bytes() != lock_bytes):
        raise RuntimeError("pre-existing dependency lock mismatch")
    inputs = build_backend.load_evidence()
    build_backend.check_runtime(root, evidence, label, command)
    target.write_bytes(lock_bytes)
    command(["uv", "--no-config", "sync", "--dev", "--locked", "--no-python-downloads",
             "--no-install-project", "--no-build", "--python", sys.executable], root, evidence, label + "-sync")
    build_backend.install_editable(root, evidence, label, command, inputs)
    after = target.read_bytes()
    (evidence / f"{label}-after-sync.lock").write_bytes(after)
    if hashlib.sha256(after).hexdigest() != digest:
        raise RuntimeError("dependency lock modified during sync")
    freeze = command(["uv", "--no-config", "--quiet", "pip", "freeze", "--python", str(root / ".venv/bin/python")], root, evidence, label + "-freeze").splitlines()
    actual = sorted(line.lower() for line in freeze if not line.startswith("-e "))
    write_json(evidence / f"{label}-freeze-diff.json", {
        "expected": expected["freeze"], "actual": actual,
        "missing": sorted(set(expected["freeze"]) - set(actual)),
        "extra": sorted(set(actual) - set(expected["freeze"])),
    })
    write_json(evidence / f"{label}-identity.json", {
        "sha": sha, "tree": git(root, "rev-parse", "HEAD^{tree}"),
        "lock_sha256": digest, "seconds": time.monotonic() - started,
        "non_editable_count": len(actual), "status": git(root, "status", "--porcelain"),
    })
    if actual != expected["freeze"]:
        raise RuntimeError("installed freeze drift from dependency evidence")
    clean(root, sha)


def registered_nodes():
    """Validate explicit node identities; list position never determines a gate."""
    original, focused = REGISTRATION["original"], REGISTRATION["focused"]
    if (len(original) != 22 or len(set(original)) != 22
            or len(focused) != 15 or len(set(focused)) != 15
            or not {INVENTORY, PROBE, *SIGNALS}.issubset(original)
            or not {INVENTORY, SDK, *TEARDOWN}.issubset(focused)):
        raise RuntimeError("registered gate identity/count drift")
    g0 = [*SIGNALS, *(n for n in original if n not in {INVENTORY, *SIGNALS}),
          *TEARDOWN, SDK]
    if len(g0) != 24 or len(set(g0)) != 24:
        raise RuntimeError("G0 identity/count drift")
    return {"original": original, "focused": focused, "g0": g0,
            "signals": list(SIGNALS), "teardown": list(TEARDOWN), "probe": PROBE}


def expected_defect(node):
    """Pin the approved mutant's traceback and minimum observed test duration."""
    if node == PROBE:
        return {"contains": ["a launch left processes behind"], "min_seconds": 55}
    if node == SIGNALS[0]:
        return {"contains": ["assert _wait_until(lambda: session.proc.poll() is not None)"],
                "min_seconds": 55}
    if node in SIGNALS[1:]:
        return {"contains": ["session.proc.wait(timeout=GRACE_S)",
                             "subprocess.TimeoutExpired", "timed out after 60 seconds"],
                "min_seconds": 55}
    raise RuntimeError("unregistered negative-control identity")


def check_results(xml, nodes, rc, seconds, defect):
    """Reject incomplete, skipped, unrelated or implausibly short mutant outcomes."""
    cases = ET.parse(xml).findall(".//testcase")
    ids = [case.attrib["classname"].replace(".", "/") + ".py::" + case.attrib["name"] for case in cases]
    counts = {"reported": len(cases), "fail": 0, "pass": 0}
    if sorted(ids) != sorted(nodes) or len(ids) != len(nodes):
        raise RuntimeError("incomplete or unexpected JUnit membership")
    for case in cases:
        if case.find("skipped") is not None or case.find("error") is not None:
            raise RuntimeError("skip/error is not acceptable evidence")
        failure = case.find("failure")
        counts["fail" if failure is not None else "pass"] += 1
        if defect is None:
            if failure is not None or rc != 0:
                raise RuntimeError("node failed")
        elif (rc != 1 or failure is None
              or not all(text in "".join(failure.itertext()) for text in defect["contains"])
              or min(seconds, float(case.attrib.get("time", "0"))) < defect["min_seconds"]):
            raise RuntimeError("mutant did not fail at the intended observation/duration")
    return counts


def run_nodes(root, nodes, evidence, label, *, workers=0, defect=None,
              classification="ACCEPTANCE"):
    """Invoke existing pytest IDs once, retaining raw facts before validating them.

    Mutant rc=1 stays a recorded failure; only the separate detector outcome is
    successful. Invalid XML, wrong identities, skips and unrelated failures abort.
    """
    xml = evidence / f"{label}.xml"
    argv = ["uv", "run", "--no-sync", "pytest", "-n", str(workers), "-v", "--tb=short",
            "--maxfail=1", f"--junitxml={xml}", *nodes]
    result = {"argv": argv, "cwd": str(root), "rc": None, "outcome": "FAIL",
              "classification": "MUTANT_DETECTION" if defect else classification,
              "expected_defect": defect}
    write_json(evidence / f"{label}-pre.json", context())
    start = time.monotonic()
    primary_error = None
    try:
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
            result["rc"] = proc.wait()
        result["seconds"] = time.monotonic() - start
        result["counts"] = check_results(xml, nodes, result["rc"], result["seconds"], defect)
        result["outcome"] = "EXPECTED_FAILURE_DETECTED" if defect else "PASS"
    except BaseException as error:
        primary_error = error
        result["error"] = str(error)
        raise
    finally:
        try:
            write_json(evidence / f"{label}-result.json", result)
            print(json.dumps({"label": label, **result}), flush=True)
        except Exception as cleanup_error:
            if primary_error is None:
                raise
            if hasattr(primary_error, "add_note"):
                primary_error.add_note(f"result capture failed: {cleanup_error}")
            print(f"result capture failed: {cleanup_error}", file=sys.stderr)


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


def negative_controls(baseline, work, evidence):
    """Require both reviewed mutants to fail at their exact registered observations."""
    root = scratch(baseline, work, evidence, "without-r4")
    run_nodes(root, [PROBE], evidence, "negative-r4", defect=expected_defect(PROBE))
    root = scratch(baseline, work, evidence, "without-forwarding")
    for index, node in enumerate(SIGNALS):
        run_nodes(root, [node], evidence, f"negative-signal-{index}",
                  defect=expected_defect(node))


def provenance(evidence):
    """Record allowlisted hosted provisioning, Python/uv, PID1 and cgroup evidence."""
    uv = Path(shutil.which("uv")).resolve()
    record = {
        "runner": {key: os.environ.get(key) for key in (
            "RUNNER_NAME", "RUNNER_OS", "RUNNER_ARCH", "ImageOS", "ImageVersion",
            "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_JOB", "GITHUB_WORKFLOW_REF", "GITHUB_WORKFLOW_SHA",
            "WORKFLOW_SHA", "ACCEPTANCE_ENVIRONMENT", "DISPATCH_MODE",
        )},
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        "kernel": platform.release(), "uid": os.getuid(),
        "python": sys.version, "executable": sys.executable, "platform": platform.platform(),
        "uv": str(uv), "uv_sha256": hashlib.sha256(uv.read_bytes()).hexdigest(),
        "home": os.environ["HOME"], "cache": os.environ["UV_CACHE_DIR"],
        "pid1": Path("/proc/1/cmdline").read_bytes().decode().replace("\0", " "),
        "cgroup": Path("/proc/self/cgroup").read_text(),
        "limits": Path("/proc/self/limits").read_text(),
        "context": context(),
    }
    write_json(evidence / "provenance.json", record)
    version = command(["uv", "--version"], evidence, evidence, "uv-version")
    record["uv_version"] = version
    write_json(evidence / "provenance.json", record)
    # Read only control files: no broad environment or credential dump.
    cgroup = Path("/sys/fs/cgroup") / Path("/proc/self/cgroup").read_text().strip().split("::", 1)[1].lstrip("/")
    values = {}
    while cgroup.is_relative_to("/sys/fs/cgroup"):
        values[str(cgroup)] = {name: (cgroup / name).read_text().strip()
                              for name in ("cpu.max", "memory.max") if (cgroup / name).exists()}
        cgroup = cgroup.parent
    write_json(evidence / "cgroup-limits.json", values)
    return record, values


def check_hosted(record, values):
    """Require SHA-bound attempt-1 authorization, provenance and non-root PID1 limits."""
    runner = record["runner"]
    for key in (*IMAGE_KEYS, *RUN_KEYS, "RUNNER_NAME", "GITHUB_JOB", "ACCEPTANCE_ENVIRONMENT"):
        if not runner.get(key):
            raise RuntimeError(f"missing hosted provisioning provenance: {key}")
    if (not re.fullmatch(r"[0-9a-f]{40}", runner["WORKFLOW_SHA"])
            or runner["WORKFLOW_SHA"] != runner["GITHUB_WORKFLOW_SHA"]
            or runner["GITHUB_RUN_ATTEMPT"] != "1"):
        raise RuntimeError("SHA-bound authorization or attempt-1 requirement failed")
    if os.getpid() != 1 or record["uid"] == 0:
        raise RuntimeError("hosted execution requires non-root non-reaping PID 1")
    if (sys.version_info[:3] != (3, 12, 14) or re.match(r"^uv 0\.13\.5(?:\s|$)", record["uv_version"]) is None
            or not record.get("boot_id") or not record.get("kernel")):
        raise RuntimeError("runtime/provisioning version drift")
    if not any(v.get("cpu.max") == "200000 100000" and v.get("memory.max") == "8589934592" for v in values.values()):
        raise RuntimeError("required cgroup envelope absent")


def verify_manifest(evidence):
    """Verify every retained file against the manifest; reject missing/extra files."""
    expected = json.loads((evidence / "manifest.json").read_text())
    actual = {str(p.relative_to(evidence)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(evidence.rglob("*")) if p.is_file() and p != evidence / "manifest.json"}
    if expected != actual:
        raise RuntimeError("artifact manifest mismatch")


def qualify_previous(evidence, current):
    """Require this job's successful G0 from a separate, already exited namespace."""
    verify_manifest(evidence)
    summary = json.loads((evidence / "summary.json").read_text())
    previous = json.loads((evidence / "provenance.json").read_text())
    if summary.get("stage") != "g0" or summary.get("outcome") != "PASS":
        raise RuntimeError("missing successful G0 prerequisite")
    if (previous["boot_id"] != current["boot_id"] or previous["kernel"] != current["kernel"]
            or previous["runner"] != current["runner"]):
        raise RuntimeError("G0 qualification does not describe this job/provisioning")


def independent_runners(upstream, current, evidence):
    """Compare G2 with both successful G1 VMs in the same recorded image class.

    Boot IDs establish distinct instances. Runner labels are compared/reported,
    not assumed globally unique. Image/kernel drift fails closed; this provides
    per-VM independence within one Ubuntu image class, not environment diversity.
    """
    records = []
    for name in ("A", "B"):
        root = upstream / f"issue-1250-serial-{name}-attempt-1"
        verify_manifest(root)
        index = json.loads((root / "artifact-index.json").read_text())
        if index.get("stage") != "serial" or index.get("outcome") != "PASS":
            raise RuntimeError("G2 requires two successful G1 artifacts")
        verify_manifest(root / "serial")
        serial = json.loads((root / "serial/summary.json").read_text())
        if serial.get("stage") != "serial" or serial.get("outcome") != "PASS":
            raise RuntimeError("G1 phase did not pass")
        previous = json.loads((root / "serial/provenance.json").read_text())
        qualify_previous(root / "g0", previous)
        if previous["runner"].get("ACCEPTANCE_ENVIRONMENT") != name:
            raise RuntimeError("G1 environment label mismatch")
        records.append(previous)
    comparisons = []
    for previous in records:
        if any(previous["runner"].get(k) != current["runner"].get(k) for k in (*RUN_KEYS, *IMAGE_KEYS)):
            raise RuntimeError("G1/G2 run, attempt, workflow or image provenance drift")
        if previous["kernel"] != current["kernel"]:
            raise RuntimeError("G1/G2 kernel drift")
        comparisons.append({"runner_name": previous["runner"]["RUNNER_NAME"],
                            "same_runner_label": previous["runner"]["RUNNER_NAME"] == current["runner"]["RUNNER_NAME"],
                            "boot_id": previous["boot_id"],
                            "image": {k: previous["runner"][k] for k in IMAGE_KEYS}})
    if current["runner"]["GITHUB_RUN_ATTEMPT"] != "1" or len({r["boot_id"] for r in [*records, current]}) != 3:
        raise RuntimeError("G1/G2 provisioning is not three independent attempt-1 VMs")
    write_json(evidence / "independence.json", {"g1": comparisons, "g2": current,
                                               "claim": "per-VM; one hosted Ubuntu image class"})


def manifest(evidence):
    """Write a complete content manifest and print its digest for external comparison."""
    write_json(evidence / "manifest.json", {
        str(p.relative_to(evidence)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(evidence.rglob("*")) if p.is_file() and p != evidence / "manifest.json"
    })
    digest = hashlib.sha256((evidence / "manifest.json").read_bytes()).hexdigest()
    print(f"manifest_sha256={digest} evidence={evidence}", flush=True)
    return digest


def finalize(evidence, roots, stage, primary_error):
    """Retain status/outcome on failure without masking the original exception.

    Metadata errors are reported separately. They fail an otherwise successful
    phase; when a primary exception exists it remains the propagated exception.
    """
    errors, statuses = [], {}
    for root in roots:
        try:
            statuses[str(root)] = {"sha": git(root, "rev-parse", "HEAD"),
                                   "status": git(root, "status", "--porcelain")}
        except Exception as error:
            statuses[str(root)] = {"error": str(error)}
            errors.append(str(error))
    try:
        write_json(evidence / "final-status.json", statuses)
        write_json(evidence / "summary.json", {
            "stage": stage, "outcome": "FAIL" if primary_error or errors else "PASS",
            "classification": "DIAGNOSTIC_ONLY" if stage in ("smoke", "negative-validation") else "ACCEPTANCE",
            "error": str(primary_error) if primary_error else None, "cleanup_errors": errors,
            "results": {p.name: json.loads(p.read_text()) for p in sorted(evidence.glob("*-result.json"))},
        })
        manifest(evidence)
    except Exception as error:
        errors.append(str(error))
    if errors:
        message = "evidence finalization errors: " + "; ".join(errors)
        print(message, file=sys.stderr, flush=True)
        if primary_error is not None:
            if hasattr(primary_error, "add_note"):
                primary_error.add_note(message)
        else:
            raise RuntimeError(message)


def report(argv):
    """Publish artifact-level outcomes/digest to logs and the Actions step summary."""
    parser = argparse.ArgumentParser(description=report.__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--stage", choices=("serial", "parallel", "smoke"), required=True)
    parser.add_argument("--command-outcome", required=True)
    args = parser.parse_args(argv)
    phases = ("smoke",) if args.stage == "smoke" else ("g0", args.stage)
    summaries = {stage: json.loads((args.evidence / stage / "summary.json").read_text())
                 if (args.evidence / stage / "summary.json").exists() else {"outcome": "NOT RUN"}
                 for stage in phases}
    index = {"stage": args.stage, "outcome": "PASS" if args.command_outcome == "success" and
             all(s["outcome"] == "PASS" for s in summaries.values()) else "FAIL",
             "classification": "DIAGNOSTIC_ONLY" if args.stage == "smoke" else "ACCEPTANCE",
             "phases": summaries}
    write_json(args.evidence / "artifact-index.json", index)
    digest = manifest(args.evidence)
    output = json.dumps(index, indent=2) + f"\nmanifest_sha256={digest}\n"
    print(output, flush=True)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a") as stream:
            stream.write("### #1250 " + index["classification"] + "\n```json\n" + output + "```\n")
    if os.environ.get("GITHUB_OUTPUT"):
        with Path(os.environ["GITHUB_OUTPUT"]).open("a") as stream:
            stream.write(f"manifest_digest={digest}\n")


def main(argv=None):
    """Run one namespace phase; smoke is baseline-only and never G0 evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("g0", "serial", "parallel", "smoke", "negative-validation"))
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--qualification", type=Path)
    parser.add_argument("--upstream", type=Path)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args(argv)
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    evidence = args.evidence.resolve() if args.evidence else work / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    os.environ["HOME"] = str(work / "home")
    os.environ["UV_CACHE_DIR"] = str(work / "uv-cache")
    Path(os.environ["HOME"]).mkdir(exist_ok=True)
    baseline = args.baseline.resolve()
    roots = [baseline]
    primary_error = None
    try:
        if os.getpid() != 1:
            raise RuntimeError("requires disposable non-reaping PID 1 namespace")
        record, values = provenance(evidence)
        if args.stage != "negative-validation":
            check_hosted(record, values)
            expected_mode = "smoke" if args.stage == "smoke" else "acceptance"
            if record["runner"].get("DISPATCH_MODE") != expected_mode:
                raise RuntimeError("dispatch mode authorization mismatch")
        nodes = registered_nodes()
        write_json(evidence / "registered.json", nodes)
        if args.stage in ("g0", "smoke", "negative-validation"):
            provision(baseline, BASELINE, evidence, "baseline")
            if args.stage == "smoke":
                if args.candidate is not None:
                    raise RuntimeError("smoke forbids candidate checkout/use")
                run_nodes(baseline, [PROBE], evidence, "smoke-probe", classification="DIAGNOSTIC_ONLY")
            else:
                run_nodes(baseline, [*SIGNALS, PROBE] if args.stage == "negative-validation" else nodes["g0"],
                          evidence, "g0-main", classification="DIAGNOSTIC_ONLY" if args.stage == "negative-validation" else "ACCEPTANCE")
                negative_controls(baseline, work, evidence)
            clean(baseline, BASELINE)
        else:
            if args.qualification is None or args.candidate is None:
                raise RuntimeError("candidate gate requires this job's G0 qualification")
            clean(baseline, BASELINE)
            qualify_previous(args.qualification, record)
            candidate = args.candidate.resolve()
            roots.append(candidate)
            clean(candidate, CANDIDATE)
            original = json.loads((candidate / ".genia/process/issue-1250-d2b-green-closeout-stop.json").read_text())["full_attempt"]["failed_nodes"]
            if original != nodes["original"]:
                raise RuntimeError("frozen candidate original-node identity drift")
            if args.stage == "parallel":
                if args.upstream is None:
                    raise RuntimeError("G2 requires both G1 artifacts")
                independent_runners(args.upstream, record, evidence)
            provision(candidate, CANDIDATE, evidence, "candidate")
            if args.stage == "serial":
                run_nodes(candidate, nodes["focused"], evidence, "g1-focused")
                run_nodes(candidate, original, evidence, "g1-original")
                run_nodes(candidate, list(TEARDOWN), evidence, "g1-teardown")
                for index, node in enumerate(SIGNALS):
                    for repetition in range(1, 4):
                        run_nodes(candidate, [node], evidence, f"g1-signal-{index}-{repetition}")
            else:
                run_nodes(candidate, [*original, *TEARDOWN], evidence, "g2-parallel", workers=2)
            clean(candidate, CANDIDATE)
    except BaseException as error:
        primary_error = error
        raise
    finally:
        finalize(evidence, roots, args.stage, primary_error)


if __name__ == "__main__":
    if sys.argv[1:2] == ["report"]:
        report(sys.argv[2:])
    else:
        main()
