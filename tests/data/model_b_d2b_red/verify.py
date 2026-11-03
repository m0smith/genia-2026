"""Focused RED evidence capture using existing pytest/R16 APIs; not a new runner."""

from pathlib import Path
import json
import os
import subprocess
from tools.spec_runner.loader import load_spec
from tools.spec_runner.protocol import fetch_capabilities
from tools.spec_runner.host_executor import execute_spec_via_host

cases = sorted(Path("spec").glob("*/model-b-link-*.yaml"))
cap = fetch_capabilities(["/workspace/genia-cpp/build/genia-adapter"], timeout=10)
assert cap.kind == "ok", cap
out = []
for p in cases:
    spec = load_spec(p)
    result = execute_spec_via_host(
        spec,
        ["/workspace/genia-cpp/build/genia-adapter"],
        timeout=10,
        host_capabilities=cap.result["capabilities"],
    )
    out.append({"case": spec.name, "kind": result.kind, "reason": result.reason})
assert all(x["kind"] == "unsupported" for x in out), out
Path("tests/data/model_b_d2b_red/cpp_evidence.json").write_text(
    json.dumps(
        {
            "source_pin": "fef41e58dcd3b80aaedcac98c92943fcfbfd1945",
            "capabilities": cap.result,
            "cases": out,
        },
        indent=2,
    )
    + "\n"
)
print("CPP", len(out), "UNSUPPORTED; 0 PASS; 0 failure classes")
# Bound each pytest selection below the twenty-failure STOP threshold.
env = dict(os.environ, UV_CACHE_DIR="/workspace/work/uv-cache")
for start in range(0, len(cases), 10):
    nodes = [
        "tests/spec/test_model_b_d2b_red.py::test_d2b_shared_oracle[" + p.stem + "]"
        for p in cases[start : start + 10]
    ]
    cmd = [
        "uv",
        "run",
        "--no-sync",
        "pytest",
        "-q",
        "--maxfail=19",
        "--tb=short",
        "--junitxml=work/d2b/shared-" + str(start) + ".xml",
        *nodes,
    ]
    with open("work/d2b/shared-" + str(start) + ".log", "w") as log:
        r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, env=env)
    print(
        start,
        r.returncode,
        Path("work/d2b/shared-" + str(start) + ".log").read_text().splitlines()[-1],
    )
