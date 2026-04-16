# Genia Spec Runner (Phase 1)

## Running Shared Spec Cases
- Only Python host is supported in phase 1.
- Cases are loaded via `spec/manifest.json` (manifest-driven only).
- Run tests using `pytest` from the project root or `tools/spec_runner`.

## Test Integration
- Shared spec cases are exposed as additive pytest tests.
- Failures in shared spec cases surface as real pytest failures.

## Supported
- Categories: parse, lower, eval, cli, errors
- Normalization and error handling per shared contract

## Known Limitations
- Directory scanning for cases is NOT supported.
- Only Python host is implemented; others are scaffold-only.
- No multi-host or cross-runtime execution.
- Flows, async, and advanced IR are out of scope.

## Host-Local Boundaries
- All runner, adapter, and normalization logic is Python-only and not part of the shared contract.
- Only normalized outputs and error objects are compared to the shared contract.
