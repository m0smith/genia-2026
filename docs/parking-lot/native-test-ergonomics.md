# Native Test Ergonomics Future Ideas

Status: **Parking lot / non-authoritative**

This note captures future ideas only. It does not define implemented Genia behavior.
If this conflicts with `GENIA_STATE.md`, `GENIA_STATE.md` wins.

## Current boundary

`GENIA_STATE.md` is the authority for implemented native-test behavior.
The current Python reference host already has minimal assertion helpers and normalized
native-test failure reporting. Do not use this parking-lot note as evidence that
`assert_true`, `assert_eq`, or `NativeTestFailure` are missing.

## Ideas to preserve

Future assertion ergonomics may include:

- custom assertion messages
- `assert_false` / `assert_ne`
- `assert_raises(...)` or an equivalent expected-error helper
- grouped assertions within one test body
- soft assertions or assertion count reporting
- clearer diff-style rendering for large expected/actual values
- named suites or module-level grouping
- property testing
- snapshot testing
- richer filtering/report output such as JSON, JUnit, or TAP

## Non-goals

- no full xUnit/RSpec/PyTest-style framework in one large issue
- no lifecycle hooks or setup/teardown behavior from this parking-lot note
- no parser, runtime, or kernel behavior change without the normal Genia phase process
- no claim that any future helper exists until `GENIA_STATE.md` and tests say so

## Promotion trigger

Promote one narrow item at a time when there is a concrete failing test or user-facing
reporting gap that the existing minimal assertion surface does not cover.
