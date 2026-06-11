# Genia TEST / Failing Tests - Issue #465

CHANGE NAME: issue #465 r3-native-tests-validated-pipeline-examples  
CHANGE SLUG: issue-465-r3-native-tests-validated-pipeline-examples  
TYPE: feature  
ISSUE: 465  
BRANCH: feature/issue-465-r3-native-tests-validated-pipeline-examples

## Scope tested

Added failing Python test coverage for the planned R3 native-test validated-pipeline example file:

```text
examples/r3_validated_pipeline_native_tests.genia
```

The focused test expects the future example to run through the existing native-test runner and report three passing native tests that prove:

- upstream `some(...)`, `none(...)`, and `err(...)` Outcome boundaries stay observable;
- `validate_each(...)` output feeds `collect_validated(...)` directly;
- a small JSONL-style validated pipeline keeps clean records and diagnostics visible through the native-test report path.

## Files changed

- `tests/unit/test_r3_validated_pipeline_native_test_examples.py`
- `.genia/process/tmp/handoffs/issue-465-r3-native-tests-validated-pipeline-examples/03-failing-tests.md`

## Commands run

```bash
uv run pytest -q tests/unit/test_r3_validated_pipeline_native_test_examples.py -v
```

## Failing output summary

The focused test fails before implementation as intended:

```text
tests/unit/test_r3_validated_pipeline_native_test_examples.py F          [100%]
E       assert 2 == 0
FAILED tests/unit/test_r3_validated_pipeline_native_test_examples.py::test_r3_validated_pipeline_native_test_examples_pass
1 failed
```

The failure is narrow: the test expects native-test execution of `examples/r3_validated_pipeline_native_tests.genia` to exit `0`, but current execution exits `2` before the example exists.

## Failing-test commit SHA

Final SHA is reported after the commit is created. The SHA cannot be embedded in this same committed file without changing the commit identity.

## Implementation note

No implementation changes were made. No `.genia` example file, runtime behavior, parser behavior, validation helper behavior, docs, or CLI/native-test runner behavior was changed in this TEST phase.
