"""
Eval execution for Genia Python host adapter.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def run_eval_subprocess(
    source: str, stdin: str | None, fixtures: tuple[str, ...] = (),
    module_entry: str | None = None,
    module_files: tuple[tuple[str, str], ...] = (),
) -> dict[str, object]:
    interpreter_path = REPO_ROOT / "src" / "genia" / "interpreter.py"
    env = dict(os.environ)
    pythonpath = str(REPO_ROOT / "src")
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        pythonpath if not existing_pythonpath else os.pathsep.join([pythonpath, existing_pythonpath])
    )
    command = [sys.executable, str(interpreter_path), "-c", source]
    if fixtures:
        fixture_modules = {
            ("r11_model",): "hosts.python.exec_model_fixture",
            ("r12_grounded",): "hosts.python.exec_r12_grounded_fixture",
        }
        if fixtures not in fixture_modules:
            raise ValueError(f"unsupported eval fixtures: {fixtures!r}")
        command = [sys.executable, "-m", fixture_modules[fixtures], source]
        env["PYTHONPATH"] = os.pathsep.join(
            [str(REPO_ROOT), env["PYTHONPATH"]]
        )
    if module_entry is not None:
        if fixtures:
            raise ValueError("module fixtures cannot be combined with injected fixtures")
        with tempfile.TemporaryDirectory(prefix="genia-spec-") as directory:
            root = Path(directory)
            for logical_path, contents in module_files:
                target = root / logical_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(contents, encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(interpreter_path), str(root / module_entry)],
                cwd=str(root), input=stdin if stdin is not None else None,
                capture_output=True, text=True, encoding="utf-8", env=env,
            )
    else:
        completed = subprocess.run(
            command, cwd=str(REPO_ROOT), input=stdin if stdin is not None else None,
            capture_output=True, text=True, encoding="utf-8", env=env,
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
