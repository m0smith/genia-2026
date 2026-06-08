# Genia TEST Handoff — Issue #460

CHANGE NAME: issue #460 r3-implementation-annotation-native-tests  
CHANGE SLUG: issue-460-r3-implementation-annotation-native-tests  
TYPE: feature  
ISSUE: 460  
BRANCH: feature/issue-460-r3-implementation-annotation-native-tests  
HANDOFF DIR: `.genia/process/tmp/handoffs/issue-460-r3-implementation-annotation-native-tests/`

---

## 1. Branch

- starting branch: `feature/issue-460-r3-implementation-annotation-native-tests`
- working branch: `feature/issue-460-r3-implementation-annotation-native-tests`
- branch status: already existed
- main branch work: no
- merge/rebase performed: no

Note: the prompt asked to read `docs/process/03-test.md`, but this branch contains `docs/process/04-test.md` as the failing-test phase prompt. I read `docs/process/04-test.md` and kept this handoff at the prompt-requested path, `03-test.md`.

---

## 2. Files Changed

- `tests/unit/test_interpreter_test_mode.py`

No implementation files were modified.

---

## 3. Tests Added

Added native test-mode coverage for:

- duplicate native-test names across `test(name, body)` and `@test` annotated functions
- `@test` applied to a non-function declaration
- unsupported `@setup` annotation rejection, proving setup lifecycle behavior was not introduced
- `@doc` metadata preservation when a function also carries `@test`

---

## 4. Exact Behavior Covered

The tests assert:

- duplicate explicit/annotated native-test names are discovery errors and do not report passing duplicate tests
- annotated non-function declarations report an existing native-test discovery error
- unsupported lifecycle annotations are rejected as unsupported annotations rather than executed as setup hooks
- existing `@doc` metadata remains available inside an annotated native-test function
- existing pass/fail/error behavior for already-covered annotated tests remains unchanged through the surrounding suite

---

## 5. Commands Run

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_interpreter_test_mode.py -v
```

Observed result:

```text
1 failed, 18 passed
```

Expected failing test:

```text
tests/unit/test_interpreter_test_mode.py::test_test_mode_reports_duplicate_legacy_and_annotated_names_as_discovery_error
```

Failure evidence:

```text
assert exit_code == 1
E       assert 0 == 1
```

Interpretation:

- current implementation runs both duplicate-named tests successfully
- approved contract requires duplicate native-test names to be a discovery error

Additional nearby validation:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_cli.py -v
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_runner.py -v
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_kernel.py -v
```

Observed results:

```text
tests/unit/test_native_test_cli.py: 6 passed
tests/unit/test_native_test_runner.py: 26 passed
tests/unit/test_native_test_kernel.py: 6 passed
```

---

## 6. Expected Failing Evidence

The failing test is intentional for the TEST phase.

It proves the missing implementation behavior:

- collect names from explicit native-test registrations and annotated native-test discovery
- reject duplicate names before reporting a successful suite
- surface the duplicate as a discovery error

---

## 7. Implementation-Phase Notes

Implementation should remain narrow:

- add duplicate-name validation after merging explicit registrations and annotated test units
- preserve explicit tests first, annotated tests second
- return/report duplicate names through the existing discovery-error mechanism
- do not add setup/teardown lifecycle behavior
- do not change assertion helper semantics
- do not change parser syntax

The currently expected duplicate error text in the failing test is:

```text
duplicate native test name: duplicate
```

---

## 8. Phase Confirmation

- failing tests added: yes
- implementation performed: no
- runtime/parser/IR semantics changed: no
- docs sync beyond TEST handoff: no
- shared CLI spec fixtures changed: no

---

## 9. Commit

Failing-test commit SHA:

```text
PENDING
```
