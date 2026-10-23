"""Shared helpers for the Slice C host-local tests (issue #1269).

PYTHON REFERENCE HOST ONLY: these helpers evaluate source through the Python
interpreter in-process or through the Python CLI entry point. They never
define portable semantics; portable observations live in the shared
``spec/{eval,error,cli}/model-b-c-*.yaml`` cases.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import genia

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"


@dataclass(frozen=True)
class Outcome:
    """Result of evaluating one program: a value, or the raised exception."""

    value: Any = None
    error: BaseException | None = None
    printed: tuple[str, ...] = ()

    @property
    def error_class(self) -> str | None:
        return None if self.error is None else type(self.error).__name__

    @property
    def message(self) -> str | None:
        return None if self.error is None else str(self.error)


def fresh_env() -> tuple[Any, list[str]]:
    """Return a fresh global environment and the list collecting `print` output."""
    printed: list[str] = []
    return genia.make_global_env([], output_handler=printed.append), printed


def outcome(source: str, *, filename: str = "<command>", env: Any = None) -> Outcome:
    """Evaluate `source` once and capture either its value or its exception."""
    printed: list[str]
    if env is None:
        env, printed = fresh_env()
    else:
        printed = []
    try:
        value = genia.run_source(source, env, filename=filename)
    except Exception as error:  # noqa: BLE001 - the test inspects the exact class
        return Outcome(error=error, printed=tuple(printed))
    return Outcome(value=value, printed=tuple(printed))


def cli(*args: str, stdin: str = "", cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run the Python CLI entry point (`genia.interpreter._main`) in a subprocess."""
    env = dict(os.environ)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(SRC) if not existing else os.pathsep.join([str(SRC), existing])
    return subprocess.run(
        [sys.executable, "-c", "from genia.interpreter import _main; raise SystemExit(_main())", *args],
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(cwd or REPO_ROOT),
        timeout=60,
        check=False,
    )
