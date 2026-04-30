"""
Eval execution for Genia Python host adapter.
"""

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def run_eval_subprocess(source: str, stdin: str | None) -> dict[str, object]:
    interpreter_path = REPO_ROOT / "src" / "genia" / "interpreter.py"
    env = dict(os.environ)
    pythonpath = str(REPO_ROOT / "src")
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        pythonpath if not existing_pythonpath else os.pathsep.join([pythonpath, existing_pythonpath])
    )
    completed = subprocess.run(
        [sys.executable, str(interpreter_path), "-c", source],
        cwd=str(REPO_ROOT),
        input=stdin if stdin is not None else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    return {
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "exit_code": completed.returncode,
    }


def exec_eval(case) -> dict:
    if isinstance(case.input, str):
        source = case.input
    elif isinstance(case.input, dict):
        source = case.input.get("source")
        if not isinstance(source, str):
            raise TypeError("eval case input.source must be a string")
    else:
        raise TypeError("eval case input must be a string or mapping")
    stdin = case.stdin if isinstance(case.stdin, str) else None
    return run_eval_subprocess(source, stdin)
