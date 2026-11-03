"""Retain exact bounded selections without suppressing expected RED exits."""

from tests.spec.test_model_b_d2b_red import CASES
from pathlib import Path
import subprocess
import os
import json
import xml.etree.ElementTree as ET

nodes = [
    "tests/spec/test_model_b_d2b_red.py::test_d2b_shared_oracle[" + p.stem + "]" for p in CASES
]
selections = [nodes[i : i + 10] for i in range(0, len(nodes), 10)]
selections.append(
    [
        "tests/unit/test_model_b_d2b_public.py",
        "tests/unit/test_model_b_d2a_link_core.py::test_d2a_09_public_use_over_explicit_bases_rejects_equal_keys_at_selection_d2b",
        "tests/unit/test_model_b_d2a_link_publish.py::test_d2a_10_ordinary_targets_become_explicit_source_targets_d2b",
        "tests/unit/test_model_b_slice_c_ownership.py::test_ordinary_group_accepts_explicit_extend_target_d2b",
        "tests/unit/test_r20_open_functions_cross_module.py::test_two_contributions_with_equal_key_are_rejected_at_selection",
    ]
)
results = []
for i, selection in enumerate(selections):
    command = [
        "uv",
        "run",
        "--no-sync",
        "pytest",
        "-q",
        "--maxfail=19",
        "--tb=short",
        "--junitxml=work/d2b/final-" + str(i) + ".xml",
        *selection,
    ]
    with open("work/d2b/final-" + str(i) + ".log", "w") as log:
        r = subprocess.run(
            command,
            stdout=log,
            stderr=subprocess.STDOUT,
            env=dict(os.environ, UV_CACHE_DIR="/workspace/work/uv-cache"),
        )
    print(i, r.returncode, Path("work/d2b/final-" + str(i) + ".log").read_text().splitlines()[-1])
    for t in ET.parse("work/d2b/final-" + str(i) + ".xml").iter("testcase"):
        f = t.find("failure")
        results.append(
            {
                "selection": i,
                "name": t.get("name"),
                "class": t.get("classname"),
                "failure": None if f is None else f.get("message"),
            }
        )
Path("tests/data/model_b_d2b_red/results.json").write_text(
    json.dumps(
        {
            "baseline": "c377b971b42682207d194aefb0e5182650d4ac10",
            "cases": results,
            "commands": selections,
        },
        indent=2,
    )
    + "\n"
)
print("TOTAL", len(results), "FAILED", sum(r["failure"] is not None for r in results))
