# Issue #126 Preflight: Minimal Host Adapter Contract

=== GENIA PRE-FLIGHT ===

CHANGE NAME:
Define minimal host adapter contract (`run_case` interface)

Date: 2026-04-27

Parent epic:
#115 — Minimize Host Porting Surface via Prelude + IR + Capability Boundaries

## 0. Branch

- Starting branch: `main`
- Working branch: `issue-126-run-case-contract`
- Branch status: newly created locally from `main`
- Base observed locally: `1343b03`

## 1. Scope Lock

This preflight includes:

- minimal host adapter contract
- normalized `run_case` interface
- relationship to the current shared spec runner
- Python reference host alignment
- test harness integration boundaries

This preflight excludes:

- new language behavior
- new Genia syntax
- new host implementation
- broad spec runner rewrite
- Core IR redesign
- portability work beyond this contract
- implementing `run_case`
- renaming existing `exec_*` functions
- changing spec behavior

## 2. Source Of Truth

Authoritative sources, in repository order:

1. `GENIA_STATE.md` (final authority)
2. `GENIA_RULES.md`
3. `GENIA_REPL_README.md`
4. `README.md`
5. `spec/*`
6. `docs/host-interop/*`
7. `docs/architecture/*`
8. implementation (`src/*`, `hosts/*`)
9. `docs/process/run-change.md`

If these files conflict, `GENIA_STATE.md` wins. In particular, `GENIA_STATE.md` says Python is the only implemented host, active executable shared spec categories are `parse`, `ir`, `eval`, `cli`, `flow`, and `error`, and no generic multi-host runner exists today.

## 3. Current Behavior To Inspect

Current runner and host-adapter files that must shape later phases:

- `tools/spec_runner/executor.py`
  - Defines `ActualResult`.
  - Dispatches by category directly to parse, IR, CLI, Flow, or eval execution.
  - Applies category-local normalization for `stdout`, `stderr`, and CLI trailing-newline stripping.
  - Does not currently call `hosts/python/adapter.py::run_case`.
- `tools/spec_runner/loader.py`
  - Defines `LoadedSpec`.
  - Defines active categories: `eval`, `cli`, `ir`, `flow`, `error`, `parse`.
  - Validates one top-level YAML envelope and category-specific `input` / `expected` fields.
- `tools/spec_runner/comparator.py`
  - Compares `stdout`, `stderr`, and `exit_code` for eval/CLI/Flow/error.
  - Compares normalized portable IR for IR cases.
  - Compares normalized parse output for parse cases.
- `tools/spec_runner/runner.py`
  - Discovers specs, executes each independently, compares, and reports failures.
  - Treats execution exceptions as `runtime_crash`.
- `hosts/python/exec_cli.py`
  - Executes the Python interpreter as a subprocess for CLI file, command, and pipe modes.
  - Returns `stdout`, `stderr`, and `exit_code`.
- `hosts/python/exec_eval.py`
  - Executes command-source eval through a subprocess.
  - Returns `stdout`, `stderr`, and `exit_code`.
- `hosts/python/exec_flow.py`
  - Executes Flow specs through command-source eval, not CLI pipe mode.
  - Returns the same subprocess result shape as eval.
- `hosts/python/exec_ir.py`
  - Parses and lowers source, then normalizes portable Core IR.
  - Returns `{"ir": ...}`.
- `hosts/python/adapter.py`
  - Already contains a `run_case(case: SpecCase) -> SpecResult` scaffold.
  - This scaffold is not the path used by the current shared spec runner.
  - Later phases must decide whether to align, replace, or preserve this scaffold without claiming unimplemented multi-host behavior.
- `hosts/python/normalize.py`
  - Has a generic normalization helper, but current runner normalization is still mostly in `tools/spec_runner/executor.py`.

Spec cases to inspect in later phases:

- parse: `spec/parse/*.yaml`
- IR: `spec/ir/*.yaml`
- eval: `spec/eval/*.yaml`
- CLI: `spec/cli/*.yaml`
- flow: `spec/flow/*.yaml`
- error: `spec/error/*.yaml`

The old `spec/_holding/*` and `spec/flows/*` files are not active shared runner categories in the current `loader.py` category list.

## 4. Desired Contract Shape

Candidate interface only:

```text
run_case(case) -> normalized_result
```

Candidate `case` contents:

- identity: spec `name` and/or `id`
- category: one of `parse`, `ir`, `eval`, `cli`, `flow`, `error`
- input:
  - `source` for parse, IR, eval, Flow, and error
  - optional `stdin` for eval, Flow, error, and CLI
  - `file`, `command`, `argv`, and `debug_stdio` for CLI where applicable
- path or metadata for reporting only, if needed

Candidate `normalized_result` contents:

- for eval/CLI/Flow/error:
  - `stdout`
  - `stderr`
  - `exit_code`
- for IR:
  - normalized portable Core IR output
- for parse:
  - normalized parse result:
    - `kind: ok` plus normalized AST
    - `kind: error` plus error type and message
- optional execution-status metadata only if it does not change the compared contract

Errors should be represented without inventing new semantics:

- Current executable error specs assert only `stdout`, `stderr`, and `exit_code`.
- Current parse error specs assert exact error `type` and message substring.
- Structured phase/category/source-location fields remain contract concepts, but they are not machine-asserted by current error specs.
- Later phases must not add structured error assertions unless the spec phase explicitly defines them and aligns `GENIA_STATE.md`.

## 5. Contract vs Implementation

Portable contract:

- Defines the minimum host adapter entrypoint and result shape used by the shared spec harness.
- Must be category-aware but not category-redefining.
- Must preserve Core IR as the portability boundary.
- Must normalize host-native execution into the existing observable contract.

Python reference host today:

- Python is the only implemented host and semantic reference.
- Working runtime behavior lives mainly in `src/genia/`.
- `hosts/python/` contains adapter and normalization scaffolding plus category execution modules.
- The active runner currently dispatches directly through `tools/spec_runner/executor.py`, not through a single portable `run_case` adapter.

Spec runner expectations:

- Loader validates spec shape before execution.
- Comparator owns expected-vs-actual checks.
- Execution result must provide the exact fields each category compares today.
- Any `run_case` integration should be a narrow execution-boundary change, not a runner rewrite.

What must remain host-specific:

- subprocess invocation strategy
- parser/evaluator internals
- runtime object representations
- host capability implementations
- file layout and package bootstrapping
- host-local debugging metadata

Host-specific behavior must not redefine Genia language behavior.

## 6. Test Strategy For Later Phases

Later phases must follow failing tests first.

Adapter contract tests:

- prove a host adapter accepts a loaded spec-like case and returns the normalized category surface
- prove category dispatch does not mutate expected spec data
- prove unsupported categories fail explicitly

Python reference host tests:

- prove Python `run_case` delegates to the existing parse/IR/eval/CLI/Flow/error execution paths
- prove normalized stdout/stderr/exit-code behavior matches current runner behavior
- prove IR and parse result shapes remain compatible with the comparator

Spec runner integration tests:

- prove `tools/spec_runner` can route execution through the adapter contract
- prove existing active categories still discover, execute, compare, and report correctly
- prove CLI-specific normalization remains unchanged unless the spec phase explicitly changes it

Regression tests for existing specs:

- parse shared specs
- IR shared specs
- eval shared specs
- CLI shared specs
- Flow shared specs
- error shared specs

Do not write those tests during this preflight phase.

## 7. Docs Impact

Likely documentation impact in later docs phase:

- add or update a focused `docs/host-interop/` contract document for the minimal host adapter boundary
- possibly update `GENIA_STATE.md` if the public/shared contract changes
- possibly update `spec/manifest.json` if the host-test contract metadata changes
- possibly update `tools/spec_runner/README.md` if execution routing changes
- possibly update `README.md` or `GENIA_REPL_README.md` only if user-visible behavior changes

Docs must not over-document future hosts as implemented. Node.js, Java, Rust, Go, C++, browser-native, and other hosts remain planned/scaffolded only unless runnable implementations and tests exist.

## 8. Complexity Check

Classification: revealing structure, if kept narrow.

Justification:

- The current system already has category execution modules and normalized runner results.
- A minimal `run_case` contract can expose the existing boundary without adding language semantics.
- Complexity increases if the issue becomes a spec runner rewrite, a generic multi-host orchestration layer, or a structured error model expansion.

Drift risks:

- `hosts/python/adapter.py` already claims a `run_case` shape, but active runner code does not use it.
- Normalization currently exists in both runner code and host adapter scaffolding.
- `HOST_INTEROP.md` mentions a single `run_case` entrypoint, while `GENIA_STATE.md` still says no generic multi-host runner exists.
- CLI normalization differs from eval/Flow/error by stripping trailing newlines before comparison.
- Parse and IR result surfaces are not `stdout`/`stderr`/`exit_code` surfaces.

## 9. Philosophy Check

- preserve minimalism: YES, if the contract stays one small adapter boundary
- explicit behavior: YES, if each category's normalized result shape is written down
- Core IR as portability boundary: YES, IR cases must continue comparing portable Core IR only
- no host redefining language behavior: YES, adapters normalize and execute; they do not define semantics
- no hidden behavior: YES, if normalization rules remain visible in docs/spec runner tests

Notes:

- This issue should standardize the harness boundary, not expand the language.
- Prelude and Core IR remain the intended portability-reduction mechanisms.
- Host capability differences must stay explicit and labeled.

## 10. Prompt Plan

Use the full required pipeline, one prompt and one commit per phase:

1. preflight
2. spec
3. design
4. failing tests
5. implementation
6. docs sync
7. audit

Do not continue beyond preflight until explicitly prompted.

## 11. Final GO / NO-GO

Decision: GO for spec phase.

Blockers:

- None for spec phase.

Spec-phase cautions:

- Resolve the current `hosts/python/adapter.py` scaffold vs active `tools/spec_runner/executor.py` dispatch split.
- Define only the minimal shared adapter interface and result shape.
- Keep structured error expansion out of scope unless a later issue explicitly scopes it.
- Do not imply future hosts exist.

Recommended branch name:

- `issue-126-run-case-contract`

Recommended next prompt:

- `SPEC for #126`

Files likely touched in later phases:

- `GENIA_STATE.md`
- `docs/host-interop/HOST_INTEROP.md`
- possible new `docs/host-interop/HOST_ADAPTER_CONTRACT.md`
- `tools/spec_runner/README.md`
- `spec/manifest.json`
- `tools/spec_runner/executor.py`
- `tools/spec_runner/loader.py`
- `tools/spec_runner/comparator.py`
- `tools/spec_runner/runner.py`
- `hosts/python/adapter.py`
- `hosts/python/normalize.py`
- `hosts/python/exec_cli.py`
- `hosts/python/exec_eval.py`
- `hosts/python/exec_flow.py`
- `hosts/python/exec_ir.py`
- targeted tests under `tests/`
