# === GENIA IMPLEMENTATION ===

CHANGE NAME: issue #470 r3-follow-up-malformed-test-annotation-edge-cases
CHANGE SLUG: issue-470-r3-follow-up-malformed-test-annotation-edge-cases
ISSUE: #470
TYPE: feature
BRANCH: feature/issue-470-r3-follow-up-malformed-test-annotation-edge-cases

GENIA_STATE.md is final authority.

HARD STOP OBSERVED:
- IMPLEMENTATION phase only.
- No tests were added or changed in this phase.
- No contract or design changes were made.
- No docs-sync work was performed.
- No parser, lexer, Core IR, prelude, assertion helper, report formatter, host adapter, lifecycle behavior, or shared spec fixture changes were made.
- The only documentation-style change is this IMPLEMENTATION handoff.

---

## 0. BRANCH CHECK

Required branch:

```text
feature/issue-470-r3-follow-up-malformed-test-annotation-edge-cases
```

Result:
- Starting branch: `feature/issue-470-r3-follow-up-malformed-test-annotation-edge-cases`
- Working branch: `feature/issue-470-r3-follow-up-malformed-test-annotation-edge-cases`
- Branch already existed: YES
- Current branch matched required branch before edits: YES
- Stopped on main: NO
- Merge/rebase performed: NO

---

## 1. FAILING TEST COMMIT REFERENCED

```text
cd2a407772a81d7241c6a6751bcf6aed4360bea0
```

Short form from prompt:

```text
cd2a407 test(native-tests): cover malformed test annotation edge cases issue #470
```

---

## 2. FILES CHANGED

- `src/genia/test_cli.py`
- `.genia/process/tmp/handoffs/issue-470-r3-follow-up-malformed-test-annotation-edge-cases/04-implementation.md`

No test files were changed in this phase.

---

## 3. IMPLEMENTATION SUMMARY

Changed native-test duplicate-name validation so `TestUnit` values that already carry `metadata["discovery_error"]` are not treated as valid duplicate-name participants.

Added a private helper:

```text
_has_discovery_error(test_unit)
```

`validate_unique_test_names(...)` now lets malformed annotated discovery-error units pass through unchanged while still preserving the existing duplicate-name behavior for valid explicit/annotated native-test duplicates.

---

## 4. EXACT BUG FIXED

Before this implementation, this source:

```genia
test("bad_duplicate", () -> assert_true(true))

@test ""
bad_duplicate() = assert_true(true)
```

reported:

```text
ERROR bad_duplicate phase=discovery reason=duplicate native test name: bad_duplicate
```

That replaced the malformed annotation's own discovery error.

After this implementation, the explicit test remains runnable and the malformed annotated declaration reports:

```text
ERROR bad_duplicate phase=discovery reason=@test description must be a non-empty string
```

Valid duplicate native-test names still report:

```text
duplicate native test name: same_name
```

---

## 5. COMMANDS RUN

Focused implementation check:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_cli.py -v
```

Observed result:

```text
14 passed
```

Nearby native-test regression coverage:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_runner.py -v
```

Observed result:

```text
26 passed
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_kernel.py -v
```

Observed result:

```text
6 passed
```

`tests/unit/test_interpreter_test_mode.py` was not run because this implementation did not affect interpreter routing or CLI mode dispatch.

---

## 6. IMPLEMENTATION COMMIT SHA

```text
317c6f906405c42547a07d67905104e06ede9385
```

---

## 7. FOLLOW-UP CONCERNS

None discovered in this phase.
