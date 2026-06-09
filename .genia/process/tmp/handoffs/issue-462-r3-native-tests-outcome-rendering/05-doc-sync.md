# Genia Doc-Sync Handoff — Issue #462

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

## Implementation Commit SHA Referenced

```text
b7dec20737325648b022f45e5c76bed9651e475b
```

## Files Changed

```text
GENIA_STATE.md
GENIA_RULES.md
GENIA_REPL_README.md
README.md
.genia/process/tmp/handoffs/issue-462-r3-native-tests-outcome-rendering/05-doc-sync.md
```

## Docs Updated

Updated `GENIA_STATE.md`:

- recorded that `display(value)` and `debug_repr(value)` render Outcome values directly, including `none(...)`, and that this is representation behavior only
- corrected the stale `display(none("missing-key", {key: "name"}))` example to the current display string `none("missing-key", {key: name})`
- added a narrow native coverage inventory entry for `tests/native/outcome_rendering.genia` and `tests/unit/test_outcome_native_tests.py`

Updated `GENIA_RULES.md`:

- added the representation invariant that `display(value)` and `debug_repr(value)` must render Outcome values directly rather than being bypassed by ordinary none propagation

Updated `GENIA_REPL_README.md`:

- mirrored the concise current behavior note for `display(value)` and `debug_repr(value)` rendering Outcome values directly

Updated `README.md`:

- clarified the representation entrypoint summary to include direct Outcome rendering, including `none(...)`
- added a selected native coverage inventory line for `tests/native/outcome_rendering.genia`

No changes were made to `docs/contract/semantic_facts.json` or `tests/doc/test_semantic_doc_sync.py`. The protected semantic facts surface is intentionally small and does not currently track representation entrypoints or native fixture inventory.

No `docs/book` files were updated because `docs/book/` is not present in this repo state.

## Why Each Doc Change Was Necessary

`GENIA_STATE.md` is final authority and needed to reflect the implemented representation-entrypoint behavior from commit `b7dec20737325648b022f45e5c76bed9651e475b`. It also had one stale display example that contradicted current display rendering for map string values.

`GENIA_RULES.md` needed the matching invariant so future changes preserve `display(...)` and `debug_repr(...)` as representation entrypoints that receive Outcome values directly.

`GENIA_REPL_README.md` and `README.md` already summarize the representation entrypoint surface, so they needed the same narrow current-behavior clarification.

`GENIA_STATE.md` and `README.md` already track selected test/coverage surfaces, so they received precise native fixture inventory wording. The wording is intentionally limited to selected coverage and does not claim complete Outcome coverage.

## Commands Run And Results

Doc guard:

```bash
uv run pytest -q tests/doc/test_semantic_doc_sync.py -v
```

Observed:

```text
85 passed in 0.36s
```

Focused behavior checks:

```bash
uv run pytest -q tests/unit/test_outcome_native_tests.py -v
```

Observed:

```text
1 passed in 0.08s
```

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

The direct native command also emitted the existing Python runpy warning:

```text
<frozen runpy>:128: RuntimeWarning: 'genia.interpreter' found in sys.modules after import of package 'genia', but prior to execution of 'genia.interpreter'; this may result in unpredictable behaviour
```

```bash
uv run pytest -q tests/unit/test_representation_entrypoints_185.py -v
```

Observed:

```text
4 passed in 0.08s
```

## Docs Commit SHA

```text
pending
```

## Audit Notes For Next Phase

Audit should verify that the docs do not overclaim Outcome coverage and that no user-facing docs imply a change to Outcome constructor semantics, native-test report semantics, parser behavior, IR behavior, evaluator architecture, or assertion helper behavior.

Audit may also note that the implementation handoff's embedded implementation commit field says `pending`; the actual implementation commit referenced by this doc-sync phase is `b7dec20737325648b022f45e5c76bed9651e475b`.
