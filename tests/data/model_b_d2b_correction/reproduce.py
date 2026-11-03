import os
import sys
import subprocess
import json
import pathlib
import xml.etree.ElementTree as ET

root = pathlib.Path(sys.argv[1])
label = sys.argv[2]
out = pathlib.Path("/workspace/work/d2b-correction-runs")
cases = sorted((root / "spec").glob("*/model-b-link-*.yaml")) + [
    root / "spec/error" / n
    for n in [
        "model-b-c-own-extend-ordinary-rejected.yaml",
        "model-b-c-own-use-ordinary-base-unchanged.yaml",
        "model-b-d1-preserve-ordinary-extension-rejection.yaml",
        "error-r20-cross-module-overlapping-unit-ambiguity.yaml",
    ]
]
nodes = [
    "tests/spec/test_model_b_d2b_red.py::test_d2b_shared_oracle[" + p.stem + "]" for p in cases
]
groups = [nodes[i : i + 10] for i in range(0, len(nodes), 10)] + [
    ["tests/unit/test_model_b_d2b_public.py"],
    [
        "tests/unit/test_model_b_d2a_link_core.py::test_d2a_09_public_use_over_explicit_bases_rejects_equal_keys_at_selection_d2b",
        "tests/unit/test_model_b_d2a_link_publish.py::test_d2a_10_ordinary_targets_become_explicit_source_targets_d2b",
        "tests/unit/test_model_b_slice_c_ownership.py::test_ordinary_group_accepts_explicit_extend_target_d2b",
        "tests/unit/test_r20_open_functions_cross_module.py::test_two_contributions_with_equal_key_are_rejected_at_selection",
    ],
]
env = dict(
    os.environ,
    UV_CACHE_DIR="/workspace/.cache/uv",
    UV_PROJECT_ENVIRONMENT="/workspace/work/slice-c-venv",
    PYTHONPATH=str(root / "src") + ":" + str(root),
)
records = []
runs = []
for i, g in enumerate(groups):
    xml = out / f"{label}-{i}.xml"
    log = out / f"{label}-{i}.log"
    cmd = [
        "uv",
        "run",
        "--no-sync",
        "pytest",
        "-q",
        "--maxfail=19",
        "--tb=short",
        "--junitxml=" + str(xml),
        *g,
    ]
    with log.open("w") as f:
        r = subprocess.run(cmd, cwd=root, env=env, stdout=f, stderr=subprocess.STDOUT)
    items = []
    for t in ET.parse(xml).iter("testcase"):
        failure = t.find("failure")
        error = t.find("error")
        skipped = t.find("skipped")
        items.append(
            {
                "name": t.attrib["name"],
                "class": t.get("classname"),
                "status": "fail"
                if failure is not None
                else "error"
                if error is not None
                else "skip"
                if skipped is not None
                else "pass",
                "failure": failure.get("message")
                if failure is not None
                else error.get("message")
                if error is not None
                else None,
            }
        )
    records.extend(items)
    runs.append(
        {"command": cmd, "returncode": r.returncode, "raw_log": log.read_text(), "cases": items}
    )
    print(label, i, r.returncode, log.read_text().splitlines()[-1], flush=True)
    if sum(x["status"] in ("fail", "error") for x in items) >= 19 or r.returncode not in (0, 1):
        raise SystemExit("STOP threshold or harness error")
payload = {
    "label": label,
    "source_head": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip(),
    "python": subprocess.check_output(
        ["uv", "run", "--no-sync", "python", "--version"], cwd=root, env=env, text=True
    ).strip(),
    "runs": runs,
    "cases": records,
    "counts": {
        s: sum(r["status"] == s for r in records) for s in ["pass", "fail", "error", "skip"]
    },
}
(out / (label + ".json")).write_text(json.dumps(payload, indent=2) + "\n")
print(payload["counts"], flush=True)
