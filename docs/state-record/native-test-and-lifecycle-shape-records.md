# Native test and lifecycle data-shape record

> **Non-authoritative provenance record.** This file preserves, verbatim and unedited, text that was displaced
> from `GENIA_STATE.md` during the #1099 distillation. It is audit material, not part of the truth hierarchy:
> it does not define Genia behavior, and `GENIA_STATE.md` governs. Start with the release, design, and reference
> documents; open this file only to see the exact displaced wording.
>
> Baseline: `GENIA_STATE.md` at `d401f322c692e8c3620509854065692c2605c61a`. Scope: Pre-condensation text of STATE sections 9.1-9.6.
> Ledger: `docs/analysis/state-distillation-migration-map.json`.

## B172: baseline lines 3530-3561

Moved from GENIA_STATE.md@d401f322, lines 3530-3561 (ledger row B172, retained-condensed, sha256 40fe937d997d41b9)

~~~~~markdown
## 9.1) Native test kernel core (Python reference host, Experimental)

LANGUAGE CONTRACT:
- Native test kernel core provides normalized pass/fail/error result dictionaries and suite dictionaries.
- It normalizes `TestUnit` execution into one of three stable result kinds: `pass`, `fail`, or `error`.
- It aggregates suite results and maps suite results to kernel-level exit codes.
- `TestResult` is distinct from Outcome (`some`/`none`/`err`); there is no automatic mapping between them.
- Exit code `0` means all executed tests passed or the suite was empty; exit code `1` means at least one test failed or errored.
- Native test metadata keys and values must be strings. Non-string metadata is reported as a deterministic discovery error before test body execution. Diagnostics use deterministic Genia runtime type names and include existing `TestUnit.location` when available.

PYTHON REFERENCE HOST:
- Implemented as `src/genia/test_kernel.py` in the Python reference host.
- Provides: `NativeTestFailure`, `TestUnit`, `run_test_unit`, `run_test_suite`, `aggregate_results`, `suite_exit_code`.
- `TestUnit` is a frozen dataclass with `name` (required non-empty string), `body` (required callable), and optional `location` and `metadata`. When `metadata` is present, all keys and values must be strings; non-string metadata is a discovery error.
- `run_test_unit(test_unit)` validates metadata before executing the body, catches `NativeTestFailure` as a `fail` result, and catches other exceptions as `error` results. Non-string metadata keys are reported as discovery errors with reason `invalid native test metadata key: expected string, received <type>`; non-string metadata values are reported as discovery errors with reason `invalid native test metadata value for key '<key>': expected string, received <type>`. Diagnostics use Genia runtime type names; existing `TestUnit.location` is appended when available. Invalid metadata must not cause the test body to execute.
- `run_test_suite(test_units)` runs each unit in given order and aggregates results via `aggregate_results`.
- Normalized `TestResult` dictionaries contain stable keys: `kind`, `name`, `phase`, `reason`, `expected`, `actual`, `stdout`, `stderr`, `diagnostics`.
- `stdout` and `stderr` are stable empty strings in this phase; capture is not implemented.
- `TestSuiteResult` dictionaries contain: `total`, `passed`, `failed`, `errored`, `results`.
- `results` preserves input order exactly.
- Validated by `tests/unit/test_native_test_kernel.py` (10 tests, Python reference host only).

Not implemented in this phase:
- `skip` result kind
- `duration` field
- shared spec-runner integration
- host adapter for Genia runtime callables
- parser/lexer/evaluator/Core IR changes
- broad assertion framework, lifecycle hooks, lifecycle annotations (such as `@setup`/`@teardown`), or fixtures; only the minimal helpers `assert_true` and `assert_eq` are implemented; `@test` annotation discovery is handled by the CLI/test-mode layer, not the kernel
- stdout/stderr capture (fields are present but always empty strings)
- multi-host test execution

~~~~~

## B173: baseline lines 3562-3604

Moved from GENIA_STATE.md@d401f322, lines 3562-3604 (ledger row B173, retained-condensed, sha256 f493d3c8e3bcde79)

~~~~~markdown
## 9.1.1) Native test assertion helpers (Python reference host, Experimental)

PYTHON REFERENCE HOST:
- The Python reference host provides minimal native-test assertion helpers: `assert_true(value)` and `assert_eq(actual, expected)`.
- Implemented as builtins registered directly in the global environment via `src/genia/builtins.py`.
- This is not a full assertion framework. This is the minimal native-test helper surface.

`assert_true(value)`:
- passes when `value` is truthy according to current runtime truthiness
- returns `none` on success
- prints nothing on success
- raises `NativeTestFailure` on assertion failure
- inside native test mode, a failing `assert_true` is reported as a test `FAIL` outcome, not an `ERROR` outcome

`assert_eq(actual, expected)`:
- passes exactly when `actual == expected` under the one Genia equality relation (R18 E18-4); see "Portable value equality" above
- compares Outcome values directly, including `none(...)`
- returns `none` on success
- prints nothing on success
- preserves useful actual/expected diagnostics on failure
- raises `NativeTestFailure` on assertion failure
- inside native test mode, a failing `assert_eq` is reported as a test `FAIL` outcome, not an `ERROR` outcome

Assertion failure behavior:
- Inside native test mode, failing helpers are reported as test FAIL outcomes rather than evaluation ERROR outcomes.
- Incorrect helper arity remains an evaluation ERROR.
- Later tests in the same suite continue running after an assertion failure.

Not implemented in this phase:
- `assert_false`, `assert_ne`, `assert_raises`, custom assertion messages, snapshot testing, property testing, soft assertions, or matcher DSLs
- broader cross-host implementation beyond the bounded C++ R24 host
- assertion lifecycle hooks, grouping, or count tracking

A Genia-native fixture now covers the R1 validated pipeline path. Validated by `tests/unit/test_r1_validated_pipeline_native_tests.py` (1 test, Python reference host only); the fixture is `tests/native/r1_validated_pipeline.genia`. Validated pipeline behavior is covered by a native test fixture using `parse_jsonl_record`, `validate_each`, `validate_record`, `collect_validated`, and `assert_eq`.

A Genia-native fixture now covers selected Outcome constructor, representation, predicate, and structured absence inspection behavior. Validated by `tests/unit/test_outcome_native_tests.py` (7 tests, Python reference host only); the fixture is `tests/native/outcome_rendering.genia`. The fixture uses `@test` annotated zero-argument functions and `assert_eq` to cover selected current behavior for `some(...)`, `none(...)`, `err(...)`, `display(...)`, `debug_repr(...)`, `some?`, `none?`, `absence_reason`, `absence_context`, and `absence_meta`. This is selected native coverage only; it does not change Outcome semantics or native-test report semantics.

A Genia-native fixture covers selected validation-helper behavior for the R3 validated-pipeline surface, including required/field/optional/record validation, `validate_each` Outcome-boundary behavior, and `collect_validated` aggregation. Validated by `tests/unit/test_r3_validation_helpers_native_tests.py` (1 test, Python reference host only); the fixture is `tests/native/r3_validation_helpers.genia`. This is selected native coverage only and does not change validation, Outcome, Flow, or native-test semantics.

A Genia-native fixture covers selected Flow/Seq visible behavior, including direct Flow `map`, `filter`, and `scan` results, list-side `collect` reuse, and list-side `run` terminal behavior returning `none`. Validated by `tests/unit/test_flow_seq_native_tests.py` (1 test, Python reference host only); the fixture is `tests/native/flow_seq_behavior.genia`. This is selected native coverage only and does not change Flow, Seq, assertion, or native-test semantics.

A runnable native-test example file is now available for the R3 validated-pipeline surface. The example is `examples/r3_validated_pipeline_native_tests.genia`, validated by `tests/unit/test_r3_validated_pipeline_native_test_examples.py` (1 test, Python reference host only). It covers Outcome-boundary preservation through `validate_each` (upstream `some(...)`, `none(...)`, and `err(...)` items pass through without invoking the validator), direct `validate_each(...) |> collect_validated(...)` composition, and a JSONL-style pipeline demonstrating clean/diagnostic observability. The example uses existing `test(name, body)` native-test authoring, existing validation helpers, and existing Outcome semantics only. This is selected native coverage only; it does not imply complete validated-pipeline coverage, advanced Flow behavior beyond what is already stated above, or new language/runtime/CLI/lifecycle behavior.

~~~~~

## B174: baseline lines 3605-3626

Moved from GENIA_STATE.md@d401f322, lines 3605-3626 (ledger row B174, retained-condensed, sha256 e96fbd2b117d4210)

~~~~~markdown
## 9.2) Native test CLI (Python reference host, Experimental)

Status: Experimental, Python reference host.

`genia --test <file>` runs native test units registered through the test-mode-only `test(name, body)` helper and `@test` annotated zero-argument functions discovered after evaluation, and reports the existing normalized native test runner outcomes. The CLI prints suite counts before and after per-result lines, reports `PASS`, `FAIL`, and `ERROR` results, and exits `0` when no failures/errors occur, `1` when failures or normalized test errors occur, and `2` for invalid CLI invocation.

`genia test <file>` routes through `src/genia/test_cli.py::run_native_tests_from_file`, sharing the same report format as `genia --test <file>`. It validates and parses the file, discovers test units through the existing test-mode-only `test(name, body)` registration path and appends `@test` annotated zero-argument functions discovered after evaluation, runs the discovered units through the native test kernel, prints a summary line (`total=<t> passed=<p> failed=<f> errored=<e>`) before and after per-result lines, and exits `0` when all discovered tests pass, `1` when any test fails/errors, and `2` for invalid CLI invocation.

Native tests may be authored with the legacy `test(name, body)` call form. Native tests may also be authored as `@test "description"` annotated zero-argument functions. The `@test "description"` annotation carries the human-readable description; the function name is the test identifier. Annotated native tests are discovered only in native test mode. `@test` marks functions for discovery; it does not execute by itself. Annotated tests use the same native test kernel as legacy tests. Assertion failures are `FAIL`; unexpected runtime exceptions are `ERROR`; malformed annotated declarations are discovery `ERROR`: empty `@test` description, `@test` on a non-function binding, and `@test` on a parameterized function are each reported with distinct discovery error reasons; a malformed annotated declaration keeps its own discovery error reason and is not overridden by duplicate-name detection. Duplicate native-test names among valid annotated and explicit units are discovery errors; the discovery reason begins with `duplicate native test name: <name>` followed by deterministic `occurrence N: <location>` lines for each conflicting definition, where location is derived from existing `TestUnit.location` metadata when available or `<unknown>` when not. Lifecycle hooks are not implemented. Setup/teardown, fixtures, parameterized tests, filtering, parallel native tests, and broad lifecycle semantics are not implemented.

PYTHON REFERENCE HOST:
- Implemented as `src/genia/test_cli.py` in the Python reference host.
- The `genia test <file>` entry point is implemented as `src/genia/test_cli.py::run_native_tests_from_file` and routed by `src/genia/interpreter.py`.
- Test mode registers a test-mode-only `test(name, body)` helper that appends `TestUnit` values to a private list; malformed units are normalized as discovery errors by the existing kernel.
- `--test` is mutually exclusive with `-c`/`--command`, `-p`/`--pipe`, and `--debug-stdio`.
- Invalid combinations such as `--debug-stdio --test` are rejected with exit code `2`.
- Report format: a summary line `total=<t> passed=<p> failed=<f> errored=<e>` appears both before and after per-result lines.
- Per-result lines: `PASS <name>`, `FAIL <name> phase=<phase> reason=<reason>` (with `expected=<expected> actual=<actual>` when present), `ERROR <name-or-unnamed> phase=<phase> reason=<reason>`.
- Validated by `tests/unit/test_native_test_cli.py` (17 tests) and `tests/unit/test_interpreter_test_mode.py` (20 tests), Python reference host only.

`@test "description"` annotation-driven native test discovery is implemented; annotated zero-argument functions are discovered after legacy `test(name, body)` registrations and run through the same native test kernel. Duplicate test names across explicit and annotated tests are discovery errors. This does not add setup/teardown lifecycle hooks, `@setup` or `@teardown` annotations, filtering, parallel execution, JSON/JUnit/TAP output, or multi-host test execution.

~~~~~

## B175: baseline lines 3627-3660

Moved from GENIA_STATE.md@d401f322, lines 3627-3660 (ledger row B175, retained-condensed, sha256 ee6c478730465a89)

~~~~~markdown
## 9.3) Lifecycle plan data-shape support (Python reference host, Experimental)

Status: Experimental, Python reference host only. Implemented in issue #449; root policy validation extended in issue #451.

LANGUAGE CONTRACT:
- A lifecycle plan is ordinary data: a map with a required `name` identifier and a required `phases` list of phase maps.
- A lifecycle phase is a map with a required `name` identifier and a required `action` identifier. Optional fields are `scope` (portable scope label), `always` (boolean), `description` (string), and `metadata` (map).
- Phase order is list order; no implicit ordering or reordering is added.
- `action` is a portable identifier (a quoted symbol), not a callable or host hook; it does not execute by existing in a plan.
- `always`, if present, must be a boolean; it normalizes to `false` when absent.
- Optional root policy maps are supported for portable data validation only: `cleanup`, `failure_policy`, and `result_policy`.
- Root policy maps normalize contract-safe defaults and reject unsupported, unsafe, or nonportable policy values. Cleanup validation preserves cleanup eligibility for entered scopes, rejects cleanup for unentered scopes, keeps cleanup failures observable, and permits only supported cleanup ordering labels. Failure policy validation preserves primary failures and cleanup failures and rejects policies that overwrite or swallow cleanup failures. Result policy validation fixes `failure_order` to the deterministic `observed_order` label and validates the observability include flags (`include_phase`, `include_scope`, `include_role`, `include_source_location`) as booleans, preserving each explicit accepted value in the normalized output and defaulting omitted flags to `true`.
- A valid plan must not contain duplicate phase `name` values within one plan.
- Lifecycle plans are inert data: constructing, importing, or validating a plan does not execute lifecycle behavior.

PYTHON REFERENCE HOST:
- `validate_lifecycle_plan(value) -> None` validates the shape without executing lifecycle behavior; raises `ValueError` with a deterministic path-based diagnostic on invalid input.
- `normalize_lifecycle_plan(value) -> GeniaMap` validates and returns a normalized plan map with `always` defaulted to `false` on phases where absent; raises `ValueError` on invalid input.
- Identifier fields (`name`, `action`, `scope`) must be `GeniaSymbol` values (produced by `quote(...)` in Genia surface code).
- Callable values as `action` fields are rejected as nonportable behavior.
- Implemented in `src/genia/lifecycle_plan.py`.
- Validated by `tests/unit/test_lifecycle_plan.py` (35 tests), Python reference host only.

Explicit limitations:
- No lifecycle runner behavior is implemented.
- No phase execution is implemented.
- No cleanup execution behavior is implemented.
- No action resolution or registry is implemented.
- No execution-mode lifecycle dispatch is implemented.
- No annotation-driven phase discovery (`@setup`, `@teardown`) is implemented.
- No module, server, actor, notebook, or browser lifecycle support is implemented.
- No portable multi-host lifecycle runner behavior is implemented.
- This is Python reference-host internal utility code; no public Genia prelude API was added in this phase.

~~~~~

## B176: baseline lines 3661-3699

Moved from GENIA_STATE.md@d401f322, lines 3661-3699 (ledger row B176, retained-condensed, sha256 a6fddd2de38fa843)

~~~~~markdown
## 9.4) Lifecycle scope tree data-shape support (Python reference host, Experimental)

Status: Experimental, Python reference host only. Implemented in issue #450.

LANGUAGE CONTRACT:
- A lifecycle scope tree is ordinary data: a map with a required `scopes` list of scope maps.
- Each scope is a map with a required `name` identifier, a required `parent` (either `none` for the root scope or `some(identifier)` for non-root scopes), and a required `children` list of identifiers.
- The first-pass R4 scope vocabulary is exactly four names: `execution`, `suite`, `module`, `test`.
- The canonical first-pass hierarchy is `execution -> suite -> module -> test`.
- Canonical parent/child relationships are deterministic:
  - `execution`: parent `none`, children `[suite]`
  - `suite`: parent `some(execution)`, children `[module]`
  - `module`: parent `some(suite)`, children `[test]`
  - `test`: parent `some(module)`, children `[]`
- Duplicate scope names are rejected.
- Unsupported scope names (including server, actor, plugin, request, browser, notebook) are rejected.
- Optional `description` (string) and `metadata` (map) fields are preserved as inert data and are not executed.
- Lifecycle scope tree data is inert: constructing, importing, or validating a scope tree does not execute lifecycle behavior.

PYTHON REFERENCE HOST:
- `validate_lifecycle_scope_tree(value) -> None` validates the shape without executing lifecycle behavior; raises `ValueError` with a deterministic path-based diagnostic on invalid input.
- `normalize_lifecycle_scope_tree(value) -> GeniaMap` validates and returns a normalized scope tree map; raises `ValueError` on invalid input.
- Identifier fields (`name`, `parent` inner value, and `children` entries) must be `GeniaSymbol` values (produced by `quote(...)` in Genia surface code).
- Input order of scope records is preserved by normalization; no implicit reordering occurs.
- Callable values stored in optional `metadata` fields are not invoked during validation or normalization.
- Implemented in `src/genia/lifecycle_scope.py`.
- Validated by `tests/unit/test_lifecycle_scope.py` (13 tests), Python reference host only.

Explicit limitations:
- No lifecycle runner behavior is implemented.
- No lifecycle phase execution is implemented.
- No setup/teardown behavior is implemented.
- No annotation discovery or annotation execution is implemented.
- No cleanup execution behavior is implemented.
- No execution-mode lifecycle dispatch is implemented.
- No server, actor, plugin, browser, notebook, HTTP, command, file, pipe, REPL, source, or flow lifecycle scopes are implemented.
- No changes were made to parser, lexer, Core IR, evaluator, prelude, CLI, native test runner, runtime execution paths, or shared semantic specs.
- This is Python reference-host internal utility code; no public Genia prelude API was added in this phase.

~~~~~

## B177: baseline lines 3700-3730

Moved from GENIA_STATE.md@d401f322, lines 3700-3730 (ledger row B177, retained-condensed, sha256 eb1b35544108ba97)

~~~~~markdown
## 9.5) Lifecycle annotation binding helper (Python reference host, Experimental)

Status: Experimental, Python reference host only. Implemented in issue #452; ordering-rule contract hardened in issue #453.

LANGUAGE CONTRACT:
- Lifecycle annotation binding treats annotations as candidate markers for lifecycle phases; annotations do not execute themselves.
- A lifecycle annotation binding selects candidates by annotation name, exact metadata filters, participant kind, and deterministic ordering.
- Supported first-pass ordering labels are `source_order`, `reverse_source_order`, and `stable_name_order`.
- Omitted annotation binding ordering defaults to `source_order`.
- Ordering metadata is normalized and preserved in the binding result data. Ordering metadata is inert: it does not execute annotated declarations, introduce lifecycle phase execution, introduce setup/teardown behavior, or introduce dependency or priority ordering.
- Invalid ordering values fail validation with a deterministic diagnostic. Unsupported ordering labels and non-string ordering values are both rejected; the diagnostic names the `binding.ordering` field, and for non-string values it names the runtime type. Ordering validation does not invoke participant or ordering values.
- Required bindings report a deterministic diagnostic when no participants match; optional bindings may produce an empty participant list without diagnostics.
- Selecting the same declaration more than once for one binding produces a deterministic diagnostic and includes that declaration at most once.
- Binding results are discovery data only. Selecting a participant does not invoke it, activate a phase, execute setup/teardown behavior, or change ordinary evaluation.

PYTHON REFERENCE HOST:
- Implemented as `src/genia/lifecycle_binding.py`.
- Provides internal dataclasses and `discover_lifecycle_participants(...)` for phase-owned annotation binding discovery.
- The helper supports annotation-name matching, exact metadata filtering, callable participant validation, deterministic ordering, duplicate diagnostics, required-binding diagnostics, and binding results without executing participant values.
- `LifecycleAnnotationBinding.ordering` defaults to `source_order` when omitted. Ordering values are validated through a centralized `_validate_ordering(...)` check that rejects non-string values and unsupported labels with deterministic `binding.ordering` diagnostics; the ordering value is preserved in the normalized binding result data.
- Validated by `tests/unit/test_lifecycle_binding.py` (17 tests), Python reference host only.

Explicit limitations:
- No lifecycle runner behavior is implemented.
- No lifecycle phase execution is implemented.
- No setup/teardown behavior is implemented.
- No `@setup` or `@teardown` annotations are implemented.
- No parser, lexer, Core IR, evaluator, CLI, native test behavior, prelude, public builtin, runtime execution path, or shared semantic spec behavior changed.
- No public Genia lifecycle annotation binding API was added.
- Native test discovery remains owned by the existing native test CLI/test-mode layer; it was not refactored to use this helper in this phase.

~~~~~

## B178: baseline lines 3731-3767

Moved from GENIA_STATE.md@d401f322, lines 3731-3767 (ledger row B178, retained-condensed, sha256 474cc3c11304dcfe)

~~~~~markdown
## 9.6) Native test lifecycle contract consumer (Python reference host, Experimental)

Status: Experimental, Python reference host only, internal/inert lifecycle contract consumer. Implemented in issue #454.

The Python reference host native test path is the first implemented consumer of the inert R4 lifecycle contract. It describes and validates the existing native test lifecycle shape as inert lifecycle plan/scope data. Observable native-test behavior is unchanged.

LANGUAGE CONTRACT:
- The native test path is described as an inert lifecycle plan with the phase shape `discover -> run -> report`.
- The native test path is described as an inert lifecycle scope tree with the canonical hierarchy `execution -> suite -> module -> test`.
- The descriptor is internal/inert data: constructing or validating it does not execute lifecycle behavior and does not change native-test behavior.
- Descriptor validation is silent during native test execution; it produces no user-visible output unless the static internal descriptor is malformed.

PYTHON REFERENCE HOST:
- Implemented in `src/genia/native_test_lifecycle.py` with:
  - `native_test_lifecycle_plan()` — returns inert lifecycle plan data for the native test path.
  - `native_test_lifecycle_scope_tree()` — returns inert lifecycle scope-tree data for the native test path.
  - `validate_native_test_lifecycle()` — validates and returns normalized plan/scope data using the existing lifecycle helpers (`normalize_lifecycle_plan`, `normalize_lifecycle_scope_tree`).
- The descriptor reuses the existing inert lifecycle plan/scope validators (sections 9.3 and 9.4); it does not duplicate or loosen validation logic.
- Dependency direction is `native_test_lifecycle.py -> lifecycle_plan.py / lifecycle_scope.py`; the lifecycle helpers do not depend on native-test modules.
- `validate_native_test_lifecycle()` is integrated into `src/genia/test_cli.py` on the native test file execution path as a silent, behavior-neutral validation call.
- Validated by `tests/unit/test_native_test_lifecycle_consumer.py` (9 tests), Python reference host only.

Explicit limitations:
- No lifecycle runner is implemented.
- No lifecycle phase execution is implemented.
- No setup execution is implemented.
- No teardown execution is implemented.
- No `@setup` or `@teardown` annotations are implemented.
- No generalized annotation execution is implemented.
- No lifecycle action registry or action resolution is implemented.
- No public Genia prelude lifecycle API was added.
- No parser, lexer, Core IR, or evaluator semantic changes were made.
- Native-test discovery is not routed through lifecycle binding; `@test` discovery is unchanged and `discover_lifecycle_participants(...)` is not used.
- No execution-mode lifecycle dispatch is implemented.
- The native-test consumer adds no server, actor, plugin, YAML, browser, notebook, or data-workflow lifecycle. The separate focused R8 server lifecycle core is described in section 9.7; no multi-host lifecycle is implemented.
- No changes to native-test CLI output or native-test exit codes were made.

~~~~~
