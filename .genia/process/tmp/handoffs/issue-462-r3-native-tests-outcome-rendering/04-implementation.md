# Genia Implementation Handoff — Issue #462

CHANGE NAME: issue #462 r3-native-tests-outcome-rendering
CHANGE SLUG: issue-462-r3-native-tests-outcome-rendering
ISSUE: 462
BRANCH: feature/issue-462-r3-native-tests-outcome-rendering
HANDOFF DIR: `.genia/process/tmp/handoffs/issue-462-r3-native-tests-outcome-rendering/`

## Starting Branch

```text
feature/issue-462-r3-native-tests-outcome-rendering
```

## Working Branch

```text
feature/issue-462-r3-native-tests-outcome-rendering
```

## Failing-Test Commit SHA Referenced

```text
9ac80c1ed23ffe246dfe1b6453e88750a67b3445
```

## Files Changed

```text
src/genia/builtins.py
tests/native/outcome_rendering.genia
.genia/process/tmp/handoffs/issue-462-r3-native-tests-outcome-rendering/04-implementation.md
```

## Root Cause

The failing native tests exposed that `display(none)` and `debug_repr(none)` were not receiving `none(...)` values. Normal direct-call none propagation short-circuited before the representation entry points executed.

That made native assertions such as:

```genia
assert_eq(display(none), "none(\"nil\")")
```

evaluate the first argument to a `none(...)` value instead of a string. The subsequent `assert_eq(...)` call then selected a host-backed assertion helper clause while the none-propagation detector tried to inspect that host-backed clause as though it were a Genia function body, producing:

```text
'_HostFunction' object has no attribute 'body'
```

This was not an Outcome constructor or rendering-string semantic defect. It was representation entry points missing the existing none-aware callable metadata they need to receive `none(...)` values directly.

During validation, one fixture expectation was also proven wrong against the approved contract and current representation behavior:

```genia
display(none("missing-key", {key: "name"}))
```

Current display rendering for map string values omits quotes, so the correct expected string is:

```text
none("missing-key", {key: name})
```

## Implementation Summary

In `src/genia/builtins.py`, marked the existing `display` and `debug_repr` host-backed entry point functions as none-aware:

```python
display_fn.__genia_handles_none__ = True
debug_repr_fn.__genia_handles_none__ = True
```

This lets the existing evaluator/callable dispatch deliver `none(...)` values to representation functions instead of short-circuiting them.

In `tests/native/outcome_rendering.genia`, corrected the one `display(none(..., context))` expected string to match current documented display behavior.

No Outcome constructors, Outcome value semantics, native test report semantics, parser, IR, evaluator architecture, or assertion helper behavior were changed.

## Commands Run And Results

Focused native Outcome wrapper:

```bash
uv run pytest -q tests/unit/test_outcome_native_tests.py -v
```

Observed:

```text
1 passed in 0.10s
```

Direct native test command:

```bash
uv run python -m genia.interpreter test tests/native/outcome_rendering.genia
```

Observed:

```text
total=6 passed=6 failed=0 errored=0
PASS some_values_render_deterministically
PASS some_with_context_renders_deterministically
PASS none_values_render_deterministically
PASS err_values_render_deterministically
PASS outcome_predicates_identify_some_and_none
PASS absence_helpers_expose_reason_and_context
total=6 passed=6 failed=0 errored=0
```

The command also emitted the existing Python runpy warning:

```text
<frozen runpy>:128: RuntimeWarning: 'genia.interpreter' found in sys.modules after import of package 'genia', but prior to execution of 'genia.interpreter'; this may result in unpredictable behaviour
```

Nearby native-test validation:

```bash
uv run pytest -q tests/unit/test_native_test_cli.py -v
uv run pytest -q tests/unit/test_interpreter_test_mode.py -v
uv run pytest -q tests/unit/test_native_test_runner.py -v
uv run pytest -q tests/unit/test_native_test_kernel.py -v
```

Observed:

```text
tests/unit/test_native_test_cli.py: 6 passed in 0.11s
tests/unit/test_interpreter_test_mode.py: 20 passed in 0.23s
tests/unit/test_native_test_runner.py: 26 passed in 0.31s
tests/unit/test_native_test_kernel.py: 6 passed in 0.11s
```

Outcome/Option helper validation:

```bash
uv run pytest -q tests/unit/test_option.py -v
```

Observed:

```text
30 passed in 0.91s
```

Additional representation entrypoint validation:

```bash
uv run pytest -q tests/unit/test_representation_entrypoints_185.py -v
```

Observed:

```text
4 passed in 0.07s
```

## Implementation Commit SHA

```text
pending
```

## Docs-Sync Notes For Next Phase

No user-facing docs were edited in this IMPLEMENTATION phase.

Later docs/audit phase should review whether coverage inventory wording needs a narrow update in:

- `GENIA_STATE.md`, especially native-test coverage inventory and Outcome/representation coverage notes
- `GENIA_REPL_README.md` only if native-test coverage inventory is mentioned there
- `README.md` only if native-test coverage inventory is mentioned there
- `docs/book/` only if behavior/docs inventory for Outcome rendering or native tests is updated there
- `docs/contract/semantic_facts.json` and `tests/doc/test_semantic_doc_sync.py` only if protected semantic facts need a coverage-inventory guard

Do not claim complete Outcome coverage. The fixture is narrow coverage for current constructor, rendering, predicate, and structured absence inspection behavior.

## Semantic Impact Confirmation

No Outcome semantics changed.

No native-test CLI/kernel/report semantics changed.

The implementation aligns `display(...)` and `debug_repr(...)` with existing documented representation behavior by allowing those representation entry points to receive `none(...)` values directly.
