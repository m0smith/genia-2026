from __future__ import annotations

from dataclasses import dataclass

from .loader import LoadedSpec


@dataclass(frozen=True)
class ActualResult:
    stdout: str | None = None
    stderr: str | None = None
    exit_code: int | None = None
    ir: object | None = None
    parse: object | None = None


def execute_spec(spec: LoadedSpec) -> ActualResult:
    from hosts.python.adapter import run_case
    return run_case(spec)
