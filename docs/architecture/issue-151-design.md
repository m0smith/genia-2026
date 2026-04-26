# Issue #151 Design

CHANGE NAME:
Add stdlib contract shared specs

Phase: design

Issue: #151

Parent: #116

## 1. Purpose

Translate `docs/architecture/issue-151-spec.md` into an implementation-ready plan for later phases.

This design covers where the failing tests, executable shared specs, and docs-sync edits should land. It does not add those files or change behavior in the design phase.

## 2. Scope Lock

This design follows the spec phase exactly:

- use existing shared spec categories only: `eval` and `flow` for new cases
- do not add a new `stdlib` spec category
- do not change parser, evaluator, Flow runtime, CLI behavior, host adapters, or stdlib implementation
- do not redesign existing diagnostics
- preserve existing stdlib-adjacent shared specs
- keep `GENIA_STATE.md` as final authority

If later work discovers that a listed expected result is not implemented, stop and resolve truth against `GENIA_STATE.md` before changing implementation or docs.

## 3. Architecture Overview

Primary zone:

- Docs / Tests / Examples, specifically executable shared spec files under `spec/` and shared-spec runner tests under `tests/`

No intended change:

- Language Contract semantics
- Core IR portability boundary
- Python runtime implementation
- Host adapter behavior
- CLI mode semantics

Data flow after implementation:

1. `tools.spec_runner.loader.discover_specs()` discovers new YAML files under `spec/eval/` and `spec/flow/`.
2. `tools.spec_runner.executor.execute_spec()` executes each case through the existing eval or flow category path.
3. `tools.spec_runner.comparator.compare_spec()` compares `stdout`, `stderr`, and `exit_code`.
4. Runner tests assert discovery and selected fixture execution.

## 4. File Plan

Design phase changes:

- Modify `docs/architecture/issue-151-design.md` only.

Later TEST phase should modify:

- `tests/test_spec_ir_runner_blackbox.py`

Later IMPLEMENTATION phase should add:

- `spec/eval/stdlib-map-list-basic.yaml`
- `spec/eval/stdlib-map-list-empty.yaml`
- `spec/eval/stdlib-filter-list-basic.yaml`
- `spec/eval/stdlib-filter-list-no-match.yaml`
- `spec/eval/stdlib-first-list-some.yaml`
- `spec/eval/stdlib-first-list-empty.yaml`
- `spec/eval/stdlib-last-list-some.yaml`
- `spec/eval/stdlib-last-list-empty.yaml`
- `spec/eval/stdlib-nth-list-some.yaml`
- `spec/eval/stdlib-nth-list-out-of-bounds.yaml`
- `spec/eval/stdlib-map-option-elements.yaml`
- `spec/eval/stdlib-filter-option-elements.yaml`
- `spec/flow/flow-map-basic.yaml`
- `spec/flow/flow-filter-basic.yaml`
- `spec/flow/flow-map-filter-chain.yaml`

Later DOCS phase should consider modifying:

- `GENIA_STATE.md`
- `README.md`
- `spec/README.md`
- `spec/eval/README.md`
- `spec/flow/README.md`
- `GENIA_RULES.md` only for stale shared-spec status wording identified in preflight, if kept in #151 docs scope

No later phase should modify runtime files for this issue unless a prior phase is explicitly revised.

## 5. Spec File Shape

Each new eval spec should use the existing shared YAML envelope:

```yaml
name: stdlib-map-list-basic
category: eval
input:
  source: |
    [1, 2, 3] |> map((x) -> x + 1)
expected:
  stdout: "[2, 3, 4]\n"
  stderr: ""
  exit_code: 0
```

Each new flow spec should use the existing shared YAML envelope:

```yaml
name: flow-map-basic
category: flow
input:
  source: |
    stdin |> lines |> map(upper) |> collect
  stdin: |
    a
    b
expected:
  stdout: "[\"A\", \"B\"]\n"
  stderr: ""
  exit_code: 0
```

Naming rules:

- filenames must match the spec names with `.yaml`
- eval stdlib value cases use the `stdlib-` prefix
- flow cases use the existing `flow-` prefix
- names should be added verbatim to runner tests

## 6. Test Design

The TEST phase must commit failing tests before any spec YAML files are added.

Primary test file:

- `tests/test_spec_ir_runner_blackbox.py`

Required discovery assertions:

- Add all new eval names to `test_discover_specs_includes_eval_cases`.
- Add all new flow names to `test_discover_specs_includes_flow_cases`.

Required fixture execution assertions:

- Add all new eval filenames to the `test_eval_spec_fixture` parametrization.
- Add all new flow filenames to the `test_flow_spec_fixture` parametrization.

Expected failure mode in TEST phase:

- discovery assertions fail because YAML files do not yet exist
- fixture parametrization may fail at `load_spec(...)` because files do not yet exist

Do not change loader, executor, or comparator tests unless the failing tests reveal that the existing shared spec system cannot handle already-supported category shapes.

## 7. Implementation Design

The IMPLEMENTATION phase for this issue is spec-file implementation only.

Implementation steps:

1. Add the 12 eval YAML files listed in this design.
2. Add the 3 flow YAML files listed in this design.
3. Keep each case deterministic and minimal.
4. Use only behavior already documented in `GENIA_STATE.md` / `GENIA_RULES.md`.
5. Run targeted shared-spec runner tests.

No Python runtime or stdlib code should change if current implementation matches the spec.

If an executable spec fails because behavior differs from the spec:

- stop
- compare against `GENIA_STATE.md`
- if `GENIA_STATE.md` supports the spec, open a separate implementation/fix path only after explicit prompt
- if `GENIA_STATE.md` contradicts the spec, revise the spec in a new spec phase before continuing

## 8. Documentation Design

The DOCS phase should update docs only after the YAML specs exist and pass.

Doc wording should say focused shared stdlib coverage was added, not full stdlib conformance.

Recommended doc updates:

- `GENIA_STATE.md`: add the new focused stdlib eval/flow coverage to current shared spec inventory.
- `README.md`: update shared spec status summaries so they mention focused core stdlib shared coverage where appropriate.
- `spec/README.md`: mention focused stdlib value/Flow coverage under eval/flow inventory if the document keeps inventory detail.
- `spec/eval/README.md`: add list stdlib helper coverage to eval inventory.
- `spec/flow/README.md`: add direct Flow `map`/`filter` coverage to first-wave Flow inventory.
- `GENIA_RULES.md`: correct stale "only eval, ir, cli active" wording if this docs phase includes shared-spec status sync.

Docs must not:

- claim every stdlib helper has shared spec coverage
- claim non-Python hosts are implemented
- promote host-local implementation details into language behavior
- remove partial/experimental maturity labels

## 9. Error Handling Design

No new error behavior is designed for #151.

Existing misuse specs remain authoritative for this recovery slice:

- `first-on-flow-type-error`
- `reduce-on-flow-type-error`
- `each-on-list-type-error`
- `count-as-pipe-stage-type-error`

Do not add new error cases unless a later spec revision explicitly lists them.

## 10. Verification Plan

Later phases should run, at minimum:

```bash
PYTHONPATH=src pytest -q tests/test_spec_ir_runner_blackbox.py
```

If docs are changed in the DOCS phase, also run the repository's semantic/doc sync tests appropriate to the touched files.

If the full shared spec runner is used, use the existing project-approved command pattern for `tools.spec_runner`.

## 11. Risk And Mitigation

Risk: expected output formatting differs from direct command output.

- Mitigation: use existing shared spec runner normalization and exact outputs from the spec phase.

Risk: Flow `stdin` block formatting introduces an extra blank line.

- Mitigation: keep flow stdin fixtures minimal and compare through the runner in implementation phase.

Risk: docs overstate coverage.

- Mitigation: use "focused core stdlib shared coverage" and keep full-conformance claims out.

Risk: TEST phase accidentally adds YAML fixtures.

- Mitigation: TEST phase should edit only runner assertions and commit failing tests.

## 12. Phase Boundaries

Design phase:

- update this artifact only

TEST phase:

- add failing runner assertions only

IMPLEMENTATION phase:

- add executable YAML shared specs only, unless explicitly re-scoped

DOCS phase:

- update truth-aligned shared-spec coverage docs after specs pass

AUDIT phase:

- verify phase trail, docs/spec/test alignment, and no runtime drift

## 13. Final Check

- Design maps exactly to the committed spec artifact.
- No new behavior is invented.
- No implementation files are changed in this phase.
- No tests are changed in this phase.
- Later phases have a concrete file and verification plan.

