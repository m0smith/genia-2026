# === GENIA CONTRACT ===

CHANGE NAME:
issue #510 r5-native-test-boundary

CHANGE SLUG:
issue-510-r5-native-test-boundary

Issue: #510
Type: contract
Release classification: R5 — Native Test Expansion / Pytest Migration Wave 1
Branch: `contract/issue-510-r5-native-test-boundary`
Handoff directory: `.genia/process/tmp/handoffs/issue-510-r5-native-test-boundary/`

Source pre-flight: `00-preflight.md` (present, GO for CONTRACT phase).

`GENIA_STATE.md` is the final authority. If anything below conflicts with `GENIA_STATE.md`, `GENIA_STATE.md` wins and this contract must be corrected, not the state.

This is a contract/docs boundary change. It defines a placement boundary; it does **not** add, remove, or change any executable behavior.

---

## 0. BRANCH CHECK

- Must NOT be on `main`: confirmed — working branch is `contract/issue-510-r5-native-test-boundary`.
- Must match pre-flight branch: confirmed — matches `00-preflight.md` expected branch.
- Working tree: clean except untracked `.claude/settings.local.json` (unrelated tooling file; not part of this change).
- No branch switch, merge, or rebase performed.

---

## 1. PURPOSE

Define the authoritative boundary between **Genia-native tests** and **Python pytest / shared semantic specs**, so that future R5 test placement and migration decisions are unambiguous.

The contract answers one question precisely: *given a behavior to protect with a test, where does that test belong?*

It introduces no new test mechanism, no new annotation, no new runner behavior, and no change to discovery, execution, reporting, or diagnostics. It is a placement contract over the test surfaces that already exist per `GENIA_STATE.md` sections 9, 9.1, 9.1.1, 9.2, and 9.6.

---

## 2. SCOPE (FROM PRE-FLIGHT)

Included:

- A normative definition of which behaviors **belong in Genia-native tests**.
- A normative definition of which behaviors **stay in Python pytest**.
- A normative statement that **shared semantic specs remain authoritative** for portable observable CLI/eval/flow/error/parse/IR behavior where covered.
- An explicit statement that native tests **complement** pytest and shared specs and replace neither.
- An explicit Python-reference-host and Experimental maturity framing for native tests.

Excluded:

- No implementation, no test migration, no new native-test behavior.
- No parser, lexer, IR, lowering, host adapter, CLI harness, spec runner, prelude, or runtime changes.
- No setup/teardown, fixtures, parameterization, property tests, snapshot tests, parallel execution, filtering, broad directory discovery, or multi-host execution.
- No R4 lifecycle-execution work; existing inert R4 lifecycle facts (section 9.6) constrain wording only.
- No broad pytest migration plan or migration matrix.

---

## 3. BEHAVIOR

This contract defines a **classification rule**, not runtime behavior. There are no new inputs, outputs, or state changes in the executable system.

Inputs (to the classification rule, applied by a maintainer or agent):

- A behavior or surface to be protected by a test.

Outputs (of the classification rule):

- A placement decision: **native test**, **pytest**, or **shared semantic spec**.

State changes:

- None in the runtime. The only artifacts changed by adopting this contract are documentation and the placement of future tests, handled in later phases.

### 3.1 Native test placement (belongs in Genia-native tests)

A behavior belongs in a Genia-native test when it is **Genia-facing** — expressible and verifiable in Genia source from the Genia user's perspective. This includes:

- Outcome constructor / representation / predicate / inspection behavior (`some`, `none`, `err`, `display`, `debug_repr`, `some?`, `none?`, `absence_reason`, `absence_context`).
- Validation helper behavior (`validate_record`, `validate_each`, `collect_validated`, and related Outcome-aware rules).
- Flow / Seq behavior that is visible at the Genia source level.
- Sheet helper behavior visible at the Genia source level.
- Record-parsing helpers usable from Genia source (e.g. `parse_jsonl_record`).
- Prelude utilities and user-facing examples intended to demonstrate the killer workflow.

Native tests are authored with the existing `test(name, body)` form or `@test "description"` annotated zero-argument functions, run through the existing native test kernel, and report the existing normalized `PASS` / `FAIL` / `ERROR` outcomes (per `GENIA_STATE.md` 9.1, 9.2). This contract adds nothing to that mechanism.

### 3.2 Pytest placement (stays in Python pytest)

A behavior stays in Python pytest when it is an **implementation or host-internal** surface not expressible as Genia-level source behavior. This includes:

- Parser / lexer / AST shape and Core IR normalization.
- Host adapter plumbing and Python-specific exception/normalization behavior.
- CLI harness internals and the spec runner implementation itself.
- Native test stack internals (the kernel, the CLI/test-mode layer, discovery/duplicate-name machinery, and the inert R4 lifecycle descriptor/validation path) as Python units — e.g. the existing `tests/unit/test_native_test_kernel.py` and `tests/unit/test_native_test_cli.py`.

### 3.3 Shared semantic spec placement (stays authoritative where covered)

Shared semantic specs remain authoritative for **portable observable behavior** — CLI `stdout` / `stderr` / `exit_code`, eval, flow, error, parse, and IR behavior — wherever they already provide coverage, including the selected native test-runner passing, runtime-erroring, and discovery-error suite outcomes already in shared CLI coverage (`GENIA_STATE.md` line 133). Portable observable behavior must not be moved out of shared specs into native tests.

---

## 4. SEMANTICS

Evaluation behavior: unchanged. This contract triggers no evaluation. `@test` annotations remain inert outside native test mode; the kernel and CLI layers behave exactly as documented in `GENIA_STATE.md` 9.1–9.2.

Classification (the only "matching" behavior this contract introduces) resolves by the perspective of the behavior under test:

- Genia-facing / user-visible source behavior → native test (3.1).
- Python/host/parser/IR/runner internal behavior → pytest (3.2).
- Portable observable CLI/eval/flow/error/parse/IR behavior with existing shared coverage → shared semantic spec (3.3).

Edge cases:

- A behavior with both a Genia-facing surface and a host-internal surface is split: the Genia-facing assertion goes to a native test, the internal assertion stays in pytest. It is not duplicated wholesale.
- A behavior that is observable at the CLI **and** already covered by a shared spec stays in the shared spec; a native test is not added to re-assert the same observable outcome.
- Native-test stack behavior (kernel/CLI/discovery/lifecycle descriptor) is host-internal (3.2) even though it concerns testing, because it asserts Python implementation rather than Genia source behavior.

Error behavior: none introduced. No new diagnostics, exit codes, or report formats. Existing native-test discovery errors, duplicate-name errors, metadata-validation errors, and exit codes (`0` / `1` / `2`) are unchanged.

---

## 5. FAILURE

What causes a violation of this contract (in later phases or future work):

- Placing a test that asserts Python/parser/IR/host internals into a Genia-native test.
- Removing or bypassing a shared semantic spec for portable observable behavior in favor of a native test.
- Documentation that claims native tests are stable/complete, replace pytest, or support unimplemented features (setup/teardown, fixtures, parameterization, snapshots, property tests, parallelism, filtering, multi-host).

Resulting error:

- This is a contract/docs boundary, so violations surface as review/audit findings and (where guardrail tests exist) as failing doc/semantic-sync tests — not as new runtime errors.

What does NOT happen:

- No runtime error path changes.
- No change to native-test discovery, execution, reporting, exit codes, or diagnostics.
- No test is migrated, added, or deleted by this contract itself.

---

## 6. INVARIANTS

- Native tests cover only Genia-facing behavior verifiable in Genia source.
- Python host/parser/IR/runner/CLI-harness internals stay in pytest.
- Shared semantic specs remain authoritative for portable observable behavior they already cover.
- Native tests complement pytest and shared specs; they replace neither.
- Native-test support remains Experimental and Python-reference-host only.
- No observable test behavior (discovery, execution, reporting, diagnostics, exit codes) changes under this contract.
- The native-test mechanism described in `GENIA_STATE.md` 9.1–9.2 and the inert R4 lifecycle facts in 9.6 are unchanged.
- The contract claims no unimplemented native-test feature.

---

## 7. EXAMPLES

Minimal:

- Native test: a `@test "..."` zero-argument function asserting `assert_eq(display(some(1)), "...")` — Genia-facing Outcome behavior.
- Pytest: a Python unit asserting the native test kernel normalizes a raised exception into an `error` result dict — host-internal.

Real (all already present in the repo per `GENIA_STATE.md`):

- Native test: `tests/native/outcome_rendering.genia` (validated by `tests/unit/test_outcome_native_tests.py`) and `tests/native/r1_validated_pipeline.genia` — Genia-facing helper/pipeline behavior. Correctly native.
- Native test example: `examples/r3_validated_pipeline_native_tests.genia` — Genia-facing validated-pipeline surface. Correctly native.
- Pytest: `tests/unit/test_native_test_kernel.py`, `tests/unit/test_native_test_cli.py` — native-test stack internals. Correctly pytest.
- Shared spec: selected native test-runner passing / runtime-erroring / discovery-error suite outcomes in shared CLI coverage. Correctly shared.

No new runnable examples are added in this phase.

---

## 8. NON-GOALS

Explicitly NOT included:

- Full or partial pytest-to-native migration execution.
- A migration matrix or per-test migration plan.
- Multi-host native-test execution.
- Setup/teardown execution; `@setup` / `@teardown` annotations.
- General fixture system; parameterized, snapshot, or property tests.
- Parallel native-test execution; test filtering; broad directory discovery.
- Native tests for parser / IR / host-adapter internals.
- Native tests as a replacement for shared semantic specs.
- Any R4 lifecycle-execution behavior.

---

## 9. DOC NOTES

- `GENIA_STATE.md` should describe this as an R5 **native-test / pytest / shared-spec placement boundary**, layered on top of the existing native-test facts in sections 9, 9.1, 9.1.1, 9.2, and 9.6 — not as a new capability.
- Maturity: **Experimental**, Python reference host only.
- Wording must state that native tests complement pytest and shared specs and must avoid any implication of completeness, pytest replacement, multi-host support, or unimplemented lifecycle/fixture/parameterization/snapshot/property/parallel features.
- The boundary description must keep portable native-test guidance separate from Python reference-host implementation detail.

---

## 10. FINAL CHECK

- Precise and testable: YES — placement is decided by a stated rule with worked, repo-present examples.
- No implementation details / no new behavior: YES — defines placement only.
- No scope expansion beyond pre-flight: YES — matches `00-preflight.md` scope lock and non-goals.
- Consistent with `GENIA_STATE.md`: YES — references and preserves sections 9, 9.1, 9.1.1, 9.2, 9.6; introduces no conflicting claim.
- Killer-workflow alignment: indirect — protects Genia-facing Outcome / validation / Flow-Seq / Sheets / diagnostics surfaces with correctly-placed native tests without adding pipeline features.

Ready to proceed to DESIGN phase.
