"""
Deterministic E16-1 protocol fixture adapter.

This is not a Genia host. It exists only to prove the E16-1 wire protocol's
mechanics and failure-taxonomy classification (issue #758) without depending
on any real host implementation. It reads exactly one request envelope from
stdin and, keyed off ``case_id``, deterministically produces one of the
behaviors the protocol contract must classify correctly: a valid ``ok``
response, a valid ``unsupported`` response, or one of several intentional
protocol violations (malformed JSON, wrong protocol version, mismatched
case_id/operation, invalid status, a missing/extra envelope key, a crash, a
hang, or leaked non-JSON output on its own stdout).

Run as: ``python -m tools.spec_runner.fixtures.protocol_fixture_adapter``
"""
from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

from tools.spec_runner.capabilities import known_capabilities
from tools.spec_runner.protocol import (
    build_capabilities_response,
    build_ok_response,
    build_unsupported_response,
    encode_response,
)

FIXTURE_CONTRACT_REVISION = "fixture-adapter-v1"


def _ok_result(operation: str, input_payload: dict[str, Any]) -> dict[str, Any]:
    if operation == "parse":
        return {"kind": "ok", "ast": {"type": "FixtureAst", "source": input_payload.get("source")}}
    if operation == "lower":
        return {"ir": {"type": "FixtureIr", "source": input_payload.get("source")}}
    # eval, cli
    return {"stdout": f"fixture-stdout:{input_payload.get('source', '')}\n", "stderr": "", "exit_code": 0}


def handle(request: dict[str, Any]) -> bytes | None:
    """Return the bytes to write to stdout, or None if the fixture should
    exit without writing a well-formed envelope (crash/hang cases handle
    their own process exit directly and never reach here)."""
    case_id = request["case_id"]
    operation = request["operation"]
    input_payload = request.get("input", {})

    if operation == "capabilities":
        # By default, deterministically declares every capability
        # genia-2026 currently defines as "supported" so requires-bearing
        # cases are never spuriously excluded merely because this is a
        # non-semantic fixture, not a real host. A test that needs to prove
        # a host with a *different* claimed set (E16-3, issue #760) may set
        # FIXTURE_CAPABILITIES_OVERRIDE to a JSON object mapping capability
        # name to status. contract_revision here is a fixture placeholder,
        # not a real pinned genia-2026 revision (that is E16-4, issue #761).
        override = os.environ.get("FIXTURE_CAPABILITIES_OVERRIDE")
        if override is not None:
            claimed = json.loads(override)
        else:
            claimed = {name: "supported" for name in sorted(known_capabilities())}
        return encode_response(
            build_capabilities_response(claimed, ["parse", "lower", "eval", "cli"], FIXTURE_CONTRACT_REVISION)
        )

    if case_id == "crash":
        sys.exit(3)

    if case_id == "hang":
        time.sleep(3600)
        return None  # pragma: no cover - unreachable under any real timeout

    if case_id == "unsupported":
        return encode_response(build_unsupported_response(case_id, operation, "fixture: operation not supported"))

    if case_id == "malformed-json":
        return b"this is not json\n"

    if case_id == "wrong-version":
        response = build_ok_response(case_id, operation, _ok_result(operation, input_payload))
        response["protocol_version"] = "99"
        return encode_response(response)

    if case_id == "wrong-case-id":
        response = build_ok_response(case_id, operation, _ok_result(operation, input_payload))
        response["case_id"] = "a-different-case-id"
        return encode_response(response)

    if case_id == "wrong-operation":
        response = build_ok_response(case_id, operation, _ok_result(operation, input_payload))
        other = next(op for op in ("parse", "lower", "eval", "cli") if op != operation)
        response["operation"] = other
        return encode_response(response)

    if case_id == "bad-status":
        response = build_ok_response(case_id, operation, _ok_result(operation, input_payload))
        response["status"] = "weird"
        return encode_response(response)

    if case_id == "missing-result":
        response = build_ok_response(case_id, operation, _ok_result(operation, input_payload))
        response["result"] = None
        return encode_response(response)

    if case_id == "extra-key":
        response = build_ok_response(case_id, operation, _ok_result(operation, input_payload))
        response["debug"] = "this key must not be here"
        return encode_response(response)

    if case_id == "stdout-leak":
        leaked = b"leaked evaluated-program output on the adapter's own stdout\n"
        envelope = encode_response(build_ok_response(case_id, operation, _ok_result(operation, input_payload)))
        return leaked + envelope

    # Default / "ok": round-trip the input deterministically.
    return encode_response(build_ok_response(case_id, operation, _ok_result(operation, input_payload)))


def main(argv: list[str] | None = None) -> int:
    raw = sys.stdin.buffer.read()
    request = json.loads(raw.decode("utf-8"))
    output = handle(request)
    if output is not None:
        sys.stdout.buffer.write(output)
        sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
