"""
Python Host Adapter for Genia Shared Spec Contract

Implements: run_case(spec: LoadedSpec) -> ActualResult
"""
from types import SimpleNamespace

from hosts.python import parse_and_normalize
from hosts.python.exec_eval import run_eval_subprocess
from hosts.python.exec_ir import exec_ir
from hosts.python.exec_cli import exec_cli
from hosts.python.exec_flow import exec_flow
from hosts.python.normalize import normalize_text, strip_trailing_newlines

from tools.spec_runner.loader import LoadedSpec
from tools.spec_runner.executor import ActualResult


def run_case(spec: LoadedSpec) -> ActualResult:
    if spec.category == "parse":
        result = parse_and_normalize(spec.source)
        return ActualResult(parse=result)

    if spec.category == "ir":
        result = exec_ir(SimpleNamespace(input={"source": spec.source}, stdin=None))
        return ActualResult(ir=result["ir"])

    if spec.category == "cli":
        result = exec_cli(spec)
        return ActualResult(
            stdout=strip_trailing_newlines(normalize_text(result["stdout"])),
            stderr=strip_trailing_newlines(normalize_text(result["stderr"])),
            exit_code=result["exit_code"],
        )

    if spec.category == "flow":
        result = exec_flow(spec)
        return ActualResult(
            stdout=normalize_text(result["stdout"]),
            stderr=normalize_text(result["stderr"]),
            exit_code=result["exit_code"],
        )

    if spec.category in ("eval", "error"):
        result = run_eval_subprocess(spec.source, spec.stdin or None)
        return ActualResult(
            stdout=normalize_text(result["stdout"]),
            stderr=normalize_text(result["stderr"]),
            exit_code=result["exit_code"],
        )

    raise ValueError(f"Unknown spec case category: {spec.category}")
