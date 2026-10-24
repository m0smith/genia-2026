"""Shared helpers for the Slice C host-local tests (issue #1269).

PYTHON REFERENCE HOST ONLY: these helpers evaluate source through the Python
interpreter in-process or through the Python CLI entry point. They never
define portable semantics; portable observations live in the shared
``spec/{eval,error,cli}/model-b-c-*.yaml`` cases.
"""

from __future__ import annotations

import dataclasses
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


# --- inspection boundaries (B0 amendment, issue #1269; package section 3, A2/A3) ------------------
#
# The approved design replaces the pure dispatch-key walker and lets the optimizer's retained arm
# structure move onto the declaration record. These helpers are the single place where host-local
# tests reach those internals, so a signature/location change at GREEN is a one-line edit here and
# never an edit to an assertion. Behavior today is byte-for-byte what the tests called directly.


def dispatch_key(pattern: Any, guard: Any) -> tuple:
    """Pure structural key of one clause header (pattern + guard); raises on unsupported input."""
    from genia.callable import _open_dispatch_key

    return _open_dispatch_key(pattern, guard)


def structural_key(node: Any, scope: dict) -> Any:
    """Pure structural key of one IR node under an explicit binder scope."""
    from genia.callable import _structural_key

    return _structural_key(node, scope)


def build_clause_record(clause: Any, env: Any) -> Any:
    """Construct the open-clause record for a lowered clause without evaluating anything."""
    from genia.callable import OpenClauseRecord

    return OpenClauseRecord(clause.pattern, clause.guard, clause.result, env, clause.span)


def reachable_case_clauses(root: Any) -> list[Any]:
    """Every ``IrCaseClause`` reachable from `root`, depth-first in field order, once each.

    Retention boundary (A3): the obligation is that all original arms stay reachable and equal from
    the optimized program. If GREEN keeps the arms on a declaration record rather than in the IR
    tree, extend *this* walker to read that record; the retention assertions do not change.
    """
    from genia import ir

    found: list[Any] = []
    seen: set[int] = set()

    def visit(node: Any) -> None:
        if isinstance(node, (list, tuple)):
            for item in node:
                visit(item)
            return
        if not dataclasses.is_dataclass(node) or isinstance(node, type) or id(node) in seen:
            return
        seen.add(id(node))
        if isinstance(node, ir.IrCaseClause):
            found.append(node)
        for field in dataclasses.fields(node):
            visit(getattr(node, field.name))

    visit(root)
    return found
