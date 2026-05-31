"""
CLI simulation execution for Genia Python host adapter.
"""

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def exec_cli(spec) -> dict:
    env = dict(os.environ)
    pythonpath = str(REPO_ROOT / "src")
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        pythonpath if not existing_pythonpath else os.pathsep.join([pythonpath, existing_pythonpath])
    )

    file = getattr(spec, "file", None)
    command = getattr(spec, "command", None)
    test = getattr(spec, "test", None)
    stdin_text = getattr(spec, "stdin", "")
    debug_stdio = getattr(spec, "debug_stdio", False)
    trailing_args = getattr(spec, "argv", [])

    argv = [
        sys.executable,
        "-c",
        "from genia.interpreter import _main; raise SystemExit(_main())",
    ]
    if debug_stdio:
        argv.append("--debug-stdio")

    if test and not file and not command and stdin_text == "" and not trailing_args:
        argv.extend(["--test", test])
        stdin = None

    elif file and not command and not test:
        argv.append(file)
        if trailing_args:
            argv.extend(trailing_args)
        stdin = None

    elif command and not file and not test and stdin_text == "":
        argv.extend(["-c", command])
        if trailing_args:
            argv.extend(trailing_args)
        stdin = None

    elif command and not file and not test:
        argv.extend(["-p", command])
        stdin = stdin_text

    else:
        raise ValueError(
            "Invalid CLI spec: file mode requires file only; "
            "command mode requires command with stdin unset; "
            "pipe mode requires command and may include stdin; "
            "test mode requires test only."
        )

    completed = subprocess.run(
        argv,
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
