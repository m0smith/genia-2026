# Native Test Assertion Library / Richer Test Ergonomics

Status: **Parking lot / non-authoritative**

This note captures future ideas only. It does not define implemented Genia behavior.
If this conflicts with `GENIA_STATE.md`, `GENIA_STATE.md` wins.

## Why this exists

Issue #431 added shared CLI coverage for passing, runtime-erroring, and discovery-error native test suite outcomes. The failing-suite case (`kind: fail`) was intentionally excluded because the current Genia-facing `--test` surface has no assertion helper or deterministic failure constructor — producing `NativeTestFailure` requires new implementation.

This note captures the deferred scope so it is not lost.

## Ideas to preserve

- Add the minimal deterministic failing outcome needed for shared CLI coverage first:
  - a single assertion helper or failure constructor that produces `kind: fail` through the `--test` surface
  - keep it narrow: one simple equality assertion is enough to unlock the shared CLI fixture
- After that baseline exists, consider richer test ergonomics:
  - equality assertions (`assert_eq(expected, actual)`)
  - expected-error assertions (`assert_raises(...)`)
  - grouped assertions within a single test body
  - better failure rendering (show expected vs actual in a readable diff-like format)
  - named test suites or module-level grouping

## What this should not become

- a full xUnit/RSpec/PyTest-style framework added in one large issue
- a new annotation-driven lifecycle (`@setup`, `@teardown`, `@test`) before the minimal assertion surface exists
- REPL-integrated test execution (separate concern)
- a change to the native test-runner kernel contract without first adding shared CLI coverage

## Related areas

- `spec/cli/README.md` — records the explicit exclusion of `native_test_runner_failing_suite_outcome` until a Genia-facing failure constructor is available
- issue #431 — added passing, error, and discovery-error shared CLI coverage
- issue #438 — exposed native test-runner outcomes through the CLI (`--test` mode)
- `src/genia/test_kernel.py` — current host-local native test kernel

## Promotion trigger

Promote this note into pre-flight when:

- a decision is made on the minimal assertion surface (function name, arity, failure contract)
- the shared CLI failing-suite fixture is ready to be written alongside the implementation
- scope is confirmed to exclude the richer ergonomics listed above (keep it one small issue at a time)

Keep out of issue #442 scope.
