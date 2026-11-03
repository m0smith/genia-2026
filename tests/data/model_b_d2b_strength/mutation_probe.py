"""Mutation discrimination through existing R16 execution/comparison; no source edits."""

import dataclasses
import json
import pathlib
import subprocess
import sys
from unittest.mock import patch
from tools.spec_runner.loader import load_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.comparator import compare_spec

M7 = """
from dataclasses import replace
from genia.evaluator import Evaluator
from genia.ir import IrOpenUse
original_eval = Evaluator._eval_impl
def fallback(self, node):
    if isinstance(node, IrOpenUse) and "." in node.target_module_alias:
        try:
            self.env.get(node.target_module_alias)
        except NameError:
            module_alias, target_name = node.target_module_alias.rsplit(".", 1)
            node = replace(node, target_module_alias=module_alias, target_name=target_name)
    return original_eval(self, node)
Evaluator._eval_impl = fallback
"""
M2 = """
from genia.ordinary_completion import _Projection
original_get = _Projection.__getattribute__
def wrong_channel(self, name):
    if name == "projected_doc":
        return original_get(self, "binding_metadata").get("doc", None)
    return original_get(self, name)
_Projection.__getattribute__ = wrong_channel
"""
root = pathlib.Path.cwd()
original_run = subprocess.run
records = []
for case_path, mutant in [
    ("spec/error/error-r20-use-dotted-from-not-rename.yaml", "M7"),
    ("spec/eval/model-b-link-projected-doc-not-binding-meta.yaml", "M2"),
]:
    spec = load_spec(root / case_path)
    for mode in ["control", mutant]:
        if mode == "M2" and sys.argv[1] == "red":
            continue  # ordinary activation rejects first; cannot discriminate reflection at RED
        launched = []

        def launch(command, **kwargs):
            """Inject a scratch in-memory mutant into the normal interpreter child."""
            command = list(command)
            assert pathlib.Path(command[1]).name == "interpreter.py", command
            if mode != "control":
                code = (
                    (M7 if mode == "M7" else M2)
                    + "\nimport runpy,sys\nsys.argv="
                    + repr([command[1]])
                    + "+sys.argv[1:]\nrunpy.run_path("
                    + repr(command[1])
                    + ',run_name="__main__")\n'
                )
                command = [command[0], "-c", code, *command[2:]]
            launched.append({"mode": mode, "in_memory_only": True, "timeout": 10})
            return original_run(command, timeout=10, **kwargs)

        with patch("hosts.python.exec_eval.subprocess.run", side_effect=launch):
            actual = execute_spec(spec)
        failures = compare_spec(spec, actual)
        record = {
            "case": spec.name,
            "mode": mode,
            "actual": dataclasses.asdict(actual),
            "comparison_failures": [dataclasses.asdict(f) for f in failures],
            "launch": launched,
        }
        records.append(record)
        print(spec.name, mode, record["actual"], "mismatches", len(failures), flush=True)
        should_pass = mode == "control" and not (sys.argv[1] == "red" and mutant == "M2")
        assert (not failures) == should_pass, record
payload = {
    "source_head": original_run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip(),
    "implementation": sys.argv[1],
    "r16_api": "load_spec / execute_spec / compare_spec; same interpreter subprocess",
    "mutant_M7": M7,
    "mutant_M2": M2,
    "records": records,
    "notes": "Mutants injected only in child process memory; no source file is edited. M2 on RED not run because activation masks doc routing.",
}
pathlib.Path("/workspace/work/d2b-strength-runs/" + sys.argv[1] + "-mutation.json").write_text(
    json.dumps(payload, indent=2) + "\n"
)
