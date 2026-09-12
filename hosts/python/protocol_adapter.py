"""
E16-5 Python reference host, speaking the E16-1 subprocess protocol
(issue #762).

Wraps the existing in-process adapter (``hosts/python/adapter.py::
run_case``), translating between the E16-1 wire envelope and the existing
``LoadedSpec``-shaped in-process contract. This module must not
reimplement or alter any Python evaluation semantics -- it only translates
transport, exactly like ``hosts/python/adapter.py`` already does for the
in-process path.

Run as: ``python -m hosts.python.protocol_adapter``
"""
from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any

from hosts.python.adapter import run_case
from tools.spec_runner.capabilities import known_capabilities
from tools.spec_runner.protocol import (
    build_capabilities_response,
    build_ok_response,
    decode_request,
    encode_response,
)
from tools.spec_runner.revision import current_revision

# shared_spec_runner is documented as Partial in
# docs/host-interop/HOST_CAPABILITY_MATRIX.md (active coverage exists, but
# is not yet complete across every category/case). Every other known
# capability is Implemented or Python-host-only for the Python reference
# host by construction.
_PARTIAL_CAPABILITIES = frozenset({"shared_spec_runner"})


def _python_claimed_capabilities() -> dict[str, str]:
    return {
        name: ("partial" if name in _PARTIAL_CAPABILITIES else "supported")
        for name in sorted(known_capabilities())
    }


def _spec_for_operation(operation: str, input_payload: dict[str, Any]) -> SimpleNamespace:
    """Reconstruct the LoadedSpec-shaped object hosts/python/adapter.py::
    run_case expects, from one E16-1 wire request. This is the exact
    inverse of tools/spec_runner/host_executor.py::build_host_request's
    mapping, so a request built by the generic runner round-trips."""
    if operation == "parse":
        return SimpleNamespace(category="parse", source=input_payload["source"])
    if operation == "lower":
        return SimpleNamespace(category="ir", source=input_payload["source"])
    if operation == "eval":
        modules = input_payload.get("modules")
        module_files = () if modules is None else tuple(
            (item["path"], item["source"]) for item in modules["files"]
        )
        return SimpleNamespace(
            category="eval",
            source=input_payload["source"],
            stdin=input_payload.get("stdin") or "",
            fixtures=(),
            module_entry=None if modules is None else modules["entry"],
            module_files=module_files,
        )
    if operation == "cli":
        argv = list(input_payload["argv"])
        stdin = input_payload.get("stdin") or ""
        if not argv:
            raise ValueError("cli input.argv must be non-empty")
        if argv[0] == "--test":
            return SimpleNamespace(
                category="cli", file=None, command=None, test=argv[1],
                stdin="", debug_stdio=False, argv=[], fixtures=(),
            )
        if argv[0] == "-c":
            return SimpleNamespace(
                category="cli", file=None, command=argv[1], test=None,
                stdin="", debug_stdio=False, argv=argv[2:], fixtures=(),
            )
        if argv[0] == "-p":
            return SimpleNamespace(
                category="cli", file=None, command=argv[1], test=None,
                stdin=stdin, debug_stdio=False, argv=[], fixtures=(),
            )
        return SimpleNamespace(
            category="cli", file=argv[0], command=None, test=None,
            stdin="", debug_stdio=False, argv=argv[1:], fixtures=(),
        )
    raise ValueError(f"unsupported operation: {operation!r}")


def _result_for_operation(operation: str, actual: Any) -> dict[str, Any]:
    if operation == "parse":
        return actual.parse
    if operation == "lower":
        return {"ir": actual.ir}
    return {"stdout": actual.stdout, "stderr": actual.stderr, "exit_code": actual.exit_code}


def handle(request: dict[str, Any]) -> bytes:
    operation = request["operation"]
    case_id = request["case_id"]
    input_payload = request.get("input", {})

    if operation == "capabilities":
        return encode_response(
            build_capabilities_response(
                _python_claimed_capabilities(),
                ["parse", "lower", "eval", "cli"],
                current_revision(),
            )
        )

    spec = _spec_for_operation(operation, input_payload)
    actual = run_case(spec)
    result = _result_for_operation(operation, actual)
    return encode_response(build_ok_response(case_id, operation, result))


def main(argv: list[str] | None = None) -> int:
    raw = sys.stdin.buffer.read()
    request = decode_request(raw)
    sys.stdout.buffer.write(handle(request))
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
