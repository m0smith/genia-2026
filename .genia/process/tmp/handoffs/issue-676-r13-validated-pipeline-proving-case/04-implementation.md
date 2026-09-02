# Implementation — issue #676 R13 validated-pipeline proving case

## Summary

Added the application-owned offline R13 proving example, deterministic `.env` fixture, native Genia proof, and shared CLI/eval/Flow/error observations. No production runtime file changed. The example composes the implemented conventional provider, three qualified `PORT` views, explicit conversion, callable Template validation, record collection/diagnostics, and an existing R10 authorized protected boundary.

## Files changed

- Added `examples/r13_validated_pipeline_proving_case.genia` and `.env` fixture.
- Added `tests/native/r13_validated_pipeline_proving_case.genia`.
- Added four issue-scoped shared YAML cases under `spec/{cli,eval,flow,error}`.
- Corrected the focused Python test's expected injected `.env` path from absolute to the exact explicit relative descriptor path.
- No files removed; no `src/` files modified.

## Validation

- `uv run pytest -q tests/unit/test_r13_validated_pipeline_proving_case_676.py tests/spec/test_r13_validated_pipeline_shared_specs_676.py tests/unit/test_r13_cross_mode_hardening_675.py tests/unit/test_configuration_standard.py`
- Result: 27 passed.
- `uv run python -m genia.interpreter examples/r13_validated_pipeline_proving_case.genia`
- Result: successful deterministic safe map with `some(8080)`, `some(5432)`, `some(9100)`, two clean records, two ordered diagnostics, credential `"<protected>"`, and `protected_match: true`.

## Complexity

Minimal and direct. All additions are proving fixtures over existing behavior.

## Blockers/ambiguities

None.

## Audit/test follow-up

Run the focused suite, documentation synchronization tests, composability review/test, and both full regression partitions. Confirm sentinel absence, one successful audit/declassification/outbound attempt, zero mismatch/direct-protected attempts, and no production semantic diff.
