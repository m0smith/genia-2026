# Failing tests — issue #676 R13 validated-pipeline proving case

## Test plan

- Add focused Python tests for artifact inventory, deterministic source acquisition, safe top-level results, exact configuration failure Outcomes, authorized one-attempt dispatch, mismatch fail-closed behavior, protected direct-host rejection, and native execution.
- Add a shared-spec inventory/runner test requiring CLI, eval, Flow, and error cases.
- Cover contract invariants without modifying production implementation.

## Files changed

- `tests/unit/test_r13_validated_pipeline_proving_case_676.py`
- `tests/spec/test_r13_validated_pipeline_shared_specs_676.py`

## Command run

`uv run pytest -q tests/unit/test_r13_validated_pipeline_proving_case_676.py tests/spec/test_r13_validated_pipeline_shared_specs_676.py`

## Failing evidence

10 expected failures. The required example, `.env` fixture, native fixture, and four shared YAML cases do not exist. All behavioral tests therefore fail at the missing example boundary, the native runner returns file error exit code 2, and both shared inventory/execution tests fail on missing YAML.

These failures correctly define the absent E13-6 proving artifacts; they do not indicate a contract/design ambiguity or an existing-runtime defect.

## Ambiguities/blockers

None. Implementation should add only the designed executable artifacts and make these observations pass; no `src/` change is authorized.
