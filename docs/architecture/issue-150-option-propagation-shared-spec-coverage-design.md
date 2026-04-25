# Issue #150 Design — Option Propagation Shared Spec Coverage

## 1. Design summary

- Keep the current shared-spec architecture unchanged: one YAML case per file under existing active category directories.
- Add a minimal set of executable shared cases proving already-implemented Option propagation behavior.
- Keep category boundaries explicit:
  - `eval` for direct Option/pipeline behavior
  - `flow` for direct Flow-source Option filtering/propagation behavior
  - `cli` only when mode-wrapper behavior is needed to prove the same documented contract
- Reuse current runner loading and comparison surfaces exactly (`stdout`, `stderr`, `exit_code`).
- Avoid schema changes, runner redesign, parser/runtime behavior changes, and stdlib surface changes.

## 2. Scope lock (from spec)

This design implements only the approved spec contract for Issue #150:

Included:

- executable shared coverage for existing `some(...)` / `none(...)` behavior
- executable shared coverage for existing Option propagation through documented pipeline/Flow/helper paths
- optional CLI-category additions only where needed to prove existing mode-observable behavior
- runner/test updates only if necessary for case execution/discovery

Excluded:

- any new language semantics
- parser syntax changes
- runtime semantic changes
- new stdlib APIs or helper semantics
- non-Python host behavior

## 3. Architecture overview

This work lives entirely in the **Docs/Tests/Specs zone** (plus optional spec-runner tests if needed).

Flow of data for this issue remains unchanged:

1. YAML case files under `spec/<category>/` are discovered by the shared runner.
2. Cases execute through existing host adapter paths for each category.
3. Runner compares normalized observable surfaces only.
4. Test modules validate discovery/execution expectations for the case inventory.

No new runtime pathways are introduced.

## 4. File / module changes

## New files

- `docs/architecture/issue-150-option-propagation-shared-spec-coverage-design.md` (this design doc)
- planned shared case files (test phase):
  - `spec/eval/option-some-render-basic.yaml`
  - `spec/eval/option-none-render-basic.yaml`
  - `spec/eval/pipeline-option-some-lift.yaml`
  - `spec/eval/pipeline-option-none-short-circuit.yaml`
  - `spec/flow/flow-keep-some-parse-int.yaml`
- optional shared case files only if contract proof requires mode-specific behavior:
  - `spec/cli/command-mode-option-propagation.yaml`
  - `spec/cli/pipe-mode-option-flow-propagation.yaml`

## Modified files (expected in later phases)

- `tests/test_spec_ir_runner_blackbox.py` (case inventory/discovery assertions)
- `tests/test_cli_shared_spec_runner.py` (only if new CLI cases are added)
- optionally docs truth surfaces in docs phase if inventory/status wording needs synchronization:
  - `GENIA_STATE.md`
  - `GENIA_REPL_README.md`
  - `README.md`
  - `spec/eval/README.md`
  - `spec/flow/README.md`
  - `spec/cli/README.md`
  - `tools/spec_runner/README.md`

## Removed files

- none

## 5. Data shapes

No new schema is introduced.

All new shared cases must use existing category envelopes.

### Eval/Flow/CLI case shape (existing)

- `name: <string>`
- `category: <eval|flow|cli>`
- `input:`
  - `source` or category-appropriate existing fields (e.g., CLI `command` / `file`)
  - optional deterministic `stdin`
  - optional existing `argv` where already used
- `expected:`
  - `stdout: <string>`
  - `stderr: <string>`
  - `exit_code: <int>`

Normalization and assertion behavior remains current runner behavior only.

## 6. Function / interface design

No new runtime/prelude functions are designed.

Interfaces touched are existing tooling/testing interfaces only:

- shared case discovery in existing runner/test helpers
- existing category executors for `eval`, `flow`, `cli`

Potential test-level interface touchpoints (if needed):

- case filename allowlists / snapshot expectations in blackbox tests
- discovery count/ordering expectations in CLI shared runner tests

No external interface changes.

## 7. Control flow design

Execution flow for new cases follows existing paths:

1. Runner discovers YAML files by category.
2. For each new case:
   - loads `input`
   - executes through category executor
   - normalizes newline surfaces
   - compares exact expected surfaces
3. Aggregated pass/fail reporting remains unchanged.

Decision points for case placement:

- If behavior is ordinary Option/pipeline semantics without mode wrapping → `eval`.
- If behavior requires direct Flow-source semantics (`stdin |> lines`) without CLI mode wrapper → `flow`.
- If behavior is specifically about command/pipe mode wrapper effect on observable Option propagation → `cli`.

## 8. Error handling design

No new error model is added.

Design constraints:

- failure cases only assert currently documented, stable error surfaces
- assertions remain on `stdout`/`stderr`/`exit_code` only
- no traceback-shape or host-internal assertions

Boundary enforcement:

- unstable or undocumented diagnostics are not added to shared coverage in this issue
- if wording stability is uncertain for a candidate failure case, drop it from shared cases

## 9. Integration points

Integration remains with existing modules only:

- `spec/<category>/` case inventories
- `tools/spec_runner` category execution paths
- existing Python host adapter execution for active categories
- shared-runner test modules under `tests/`

No changes to interpreter architecture or prelude loading are part of this design.

## 10. Test design input (for next phase)

The **test phase** must add failing shared cases first (before any implementation fix), using the approved inventory.

Primary invariants to encode as failing/passing shared assertions:

- deterministic direct rendering for `some(...)` and `none`
- deterministic `some(...)` lift behavior through ordinary stages
- deterministic `none(...)` short-circuit behavior
- deterministic Option filtering through existing Flow helper paths
- no silent Option-structure loss at observable boundary

Edge-case selection rules:

- keep cases deterministic and minimal
- one contract fact per case where practical
- avoid overlap between `eval` and `cli` unless mode distinction is the point

Runner-test updates:

- update only if discovery assertions require the new filenames
- avoid adding new runner features in this issue

## 11. Doc impact (later docs phase)

Potential docs updates depend on actual landed case inventory:

- coverage inventory wording in `GENIA_STATE.md`
- matching summary wording in `README.md` and `GENIA_REPL_README.md`
- category README inventory notes in `spec/*/README.md`
- runner docs in `tools/spec_runner/README.md`

Docs updates must remain strictly factual to what executable cases actually cover.

## 12. Constraints

Must:

- follow existing shared-spec file patterns
- preserve minimal, deterministic observable assertions
- keep semantics and host contract unchanged
- keep category boundaries explicit

Must not:

- introduce new concepts beyond spec scope
- depend on Python-specific leakage
- redesign runner schema or execution model
- change language/runtime behavior

## 13. Complexity check

Assessment:

- Minimal: Yes
- Necessary: Yes
- Over-engineered: No

Reason:

- this design reuses existing infrastructure and adds only case inventory plus minimal test bookkeeping
- it strengthens regression proof for already-implemented behavior without architecture churn

## 14. Final check

- Matches approved Issue #150 spec scope.
- Introduces no new behavior.
- Provides concrete file plan and placement rules for test/implementation phases.
- Keeps shared contract assertions portable and observable.
- Ready for failing-tests phase.
