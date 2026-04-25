# Issue #149 Design — Pattern Matching Shared Spec Coverage

## 1. Design summary

- Keep the shared-spec architecture unchanged: one YAML case per file in existing category directories.
- Add a compact set of shared cases for pattern behavior in `spec/eval/` and `spec/error/` only.
- Reuse existing runner loading, execution, and normalized comparison surfaces (`stdout`, `stderr`, `exit_code`) with no schema changes.
- Update runner tests only where discovery/inventory assertions must include new case files.
- Do not change parser/runtime semantics, host contract semantics, or CLI/flow behavior as part of this issue.

## 2. Scope lock (from spec)

Included:

- shared executable coverage for already-implemented pattern behavior
- deterministic success-path proofs in `eval`
- deterministic stable failure proofs in `error`
- minimal test plumbing changes only if required for case discovery/execution assertions

Excluded:

- any new pattern semantics or syntax
- parser/runtime refactor
- category redesign
- shared-runner schema redesign
- non-Python host behavior

## 3. Architecture overview

This issue stays in the **Docs / Tests / Specs zone**.

Current execution path remains unchanged:

1. shared YAML files under `spec/eval/` and `spec/error/` are discovered by existing runner logic
2. category executors run source through current Python reference host pathways
3. runner compares normalized observable surfaces only
4. test modules validate discovery and execution behavior for the case inventory

No new runtime pathways are introduced.

## 4. File / module changes

### New files (design phase)

- `docs/architecture/issue-149-pattern-matching-shared-specs-design.md` (this file)

### Planned spec files (test/implementation phases)

`spec/eval/` planned additions:

- `pattern-first-match-wins.yaml`
- `pattern-literal-int.yaml`
- `pattern-literal-string.yaml`
- `pattern-wildcard.yaml`
- `pattern-variable-binding.yaml`
- `pattern-list-exact.yaml`
- `pattern-list-exact-miss.yaml`
- `pattern-list-empty.yaml`
- `pattern-tuple-multiarg.yaml`
- `pattern-map-partial.yaml`
- `pattern-map-key-binding.yaml`
- `pattern-map-shorthand.yaml`
- `pattern-option-some.yaml`
- `pattern-option-none.yaml`
- `pattern-option-none-context.yaml`
- `pattern-option-none-reason.yaml`
- `pattern-guard-pass.yaml`
- `pattern-guard-skip.yaml`
- `pattern-glob-star.yaml`
- `pattern-glob-non-string.yaml`

`spec/error/` planned additions:

- `error-pattern-miss.yaml`
- `error-pattern-guard-all-fail.yaml`
- `error-pattern-glob-malformed.yaml`

### Expected modified tests (later phases, if needed)

- `tests/test_spec_ir_runner_blackbox.py`
- `tests/test_cli_shared_spec_runner.py` (only if shared inventory assertions there require updates)

### Expected docs sync surfaces (later phase)

- `GENIA_STATE.md`
- `GENIA_REPL_README.md`
- `README.md`
- `spec/eval/README.md`
- `spec/error/README.md`
- `tools/spec_runner/README.md`

## 5. Data shapes

No new data shape is introduced.

All new cases must use existing shared spec schema used by `eval` and `error` categories:

- `name: <string>`
- `category: <eval|error>`
- `input:` with existing source fields
- `expected:`
  - `stdout: <string>`
  - `stderr: <string>`
  - `exit_code: <int>`

No additional fields, annotations, or per-case custom comparators are added.

## 6. Interface / control-flow design

No interpreter interface changes are designed.

Runner control flow remains:

1. discover case files by category
2. execute category-specific path
3. normalize outputs with existing rules
4. compare against `expected`
5. report pass/fail

Design constraints:

- each case should prove one contract fact where practical
- case assertions should avoid host internals
- error cases should use stable documented diagnostics only

## 7. Error-handling design

Error-case design is constrained to currently documented stable surfaces:

- match miss behavior
- guard all fail behavior
- malformed glob behavior

Not allowed in this issue:

- traceback-shape assertions
- unstable wording assertions
- undocumented parser/runtime failure variants

If a diagnostic is not stable, the case should be dropped rather than widening the contract.

## 8. Integration points

Integration remains inside existing boundaries:

- case files under `spec/eval/` and `spec/error/`
- existing `tools/spec_runner` loaders/executors
- existing shared runner blackbox tests

No language-runtime integration changes are in scope.

## 9. Test-phase input

The next **test** phase should add failing tests/cases first.

Target invariants to encode:

- deterministic first-match behavior
- deterministic literal/collection/map/option pattern outcomes
- deterministic guard pass/skip outcomes
- deterministic normalized pattern failures in `error`

Test strategy notes:

- keep cases deterministic and minimal
- prefer exact expected surfaces over broad assertions
- update inventory assertions only where necessary

## 10. Docs impact (later docs phase)

Docs updates should only reflect landed executable coverage.

Required tone:

- coverage expansion for existing behavior
- no claim of semantic expansion
- no implication of non-Python host readiness

## 11. Constraints

Must:

- preserve existing schema and runner behavior
- preserve category boundaries
- preserve semantics as-is

Must not:

- redesign runner
- introduce parser/runtime changes
- add cross-category coupling

## 12. Complexity check

Assessment:

- Minimal: Yes
- Necessary: Yes
- Over-engineered: No

Reason:

- this design reuses existing architecture and limits change to case inventory plus minimal inventory-test/doc synchronization
