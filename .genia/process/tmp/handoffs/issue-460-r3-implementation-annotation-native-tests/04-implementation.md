# Genia Implementation Handoff — Issue #460

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

---

## 2. Failing-Test Commit

```text
ff9e0ccff60cafa753d29f20f084a6b188fe4769
```

---

## 3. Files Changed

- `src/genia/test_cli.py`
- `.genia/process/tmp/handoffs/issue-460-r3-implementation-annotation-native-tests/04-implementation.md`

---

## 4. Implementation Summary

Added duplicate-name validation at the native test discovery merge point.

`discover_test_units(env)` now combines:

- explicit `test(name, body)` registrations
- `@test` annotated function test units

Then it calls `validate_unique_test_names(...)` before returning the final list to the existing native-test kernel.

When a duplicate non-empty string test name is found, discovery returns one existing-style discovery-error `TestUnit` with:

```text
duplicate native test name: <name>
```

No new native-test execution path was introduced.

---

## 5. Exact Behavior Fixed

Fixed:

- duplicate names across explicit native-test registrations and annotated native-test discovery no longer produce a successful suite
- the duplicate is surfaced through the existing discovery-error mechanism
- the failing TEST-phase case now passes:

```text
tests/unit/test_interpreter_test_mode.py::test_test_mode_reports_duplicate_legacy_and_annotated_names_as_discovery_error
```

---

## 6. Behavior Preserved

Preserved:

- explicit tests are collected before annotated tests
- annotated tests still run through the existing native-test kernel
- passing annotated tests still report pass outcomes
- assertion helper failures still report fail outcomes
- runtime errors still report error outcomes
- malformed annotated declarations still report discovery errors
- `@test` remains inert outside native-test runner discovery
- native-test report formatting remains unchanged

---

## 7. Behavior Not Implemented

Not implemented:

- setup/teardown lifecycle behavior
- annotation-driven lifecycle phases
- parser syntax changes
- Core IR changes
- assertion helper semantic changes
- custom `@test` names, tags, filters, skip, payload options, or priority
- imported-module or nested/local test discovery
- generalized annotation discovery
- CLI redesign
- docs sync beyond this implementation handoff

---

## 8. Commands Run

Baseline before implementation:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_interpreter_test_mode.py -v
```

Observed:

```text
1 failed, 18 passed
```

The failure was the expected TEST-phase duplicate-name failure:

```text
assert exit_code == 1
E       assert 0 == 1
```

Validation after implementation:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_interpreter_test_mode.py -v
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_cli.py -v
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_runner.py -v
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_kernel.py -v
```

Observed:

```text
tests/unit/test_interpreter_test_mode.py: 19 passed
tests/unit/test_native_test_cli.py: 6 passed
tests/unit/test_native_test_runner.py: 26 passed
tests/unit/test_native_test_kernel.py: 6 passed
```

---

## 9. Docs Sync

Docs sync is required next if the branch process continues to DOC/AUDIT phases.

No user-facing docs sync was performed in this implementation phase.

---

## 10. Phase Confirmation

- setup/teardown lifecycle behavior added: no
- parser syntax added: no
- assertion helper semantics changed: no
- docs sync performed beyond this implementation handoff: no
- implementation was minimal and local: yes

---

## 11. Implementation Commit

Implementation commit SHA:

```text
2167d04c36c1270020566a829a7e17f8a5e85b83
```

---

## 12. Final Git Status

```text
clean after implementation commit 2167d04c36c1270020566a829a7e17f8a5e85b83
```
