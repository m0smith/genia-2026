# Issue #150 Spec — Option Propagation Shared Spec Coverage

## 1. Scope

This issue defines a shared-semantic coverage expansion for already-implemented Option propagation behavior.

Included in this phase:

- executable shared spec cases proving existing `some(...)` / `none(...)` behavior
- coverage across relevant active categories where this behavior is already observable:
  - `eval`
  - `flow`
  - `cli` only where needed to prove existing pipe/command observable behavior
- coverage for existing option-aware stdlib helpers only where already implemented and documented
- runner/test updates only if required to execute the new shared cases

Excluded from this phase:

- new language semantics
- new parser syntax
- new pipeline semantics
- new Flow semantics
- new stdlib functions
- host-surface expansion
- non-Python hosts
- broad refactors

This issue is coverage expansion for existing contract behavior, not a feature change.

## 2. Portable observable contract

The shared contract to prove in this issue is limited to observable behavior already documented in `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, and `README.md`:

- direct Option surface rendering is deterministic for `some(...)` and `none(...)`
- pipeline Option propagation behaves as currently documented:
  - `none(...)` short-circuits remaining stages and returns unchanged
  - `some(x)` lifts through ordinary stages by passing `x`
  - lifted stage results preserve explicit Option results and wrap non-Option lifted results as documented
- existing option-aware Flow helpers preserve current behavior where already documented (for example `keep_some` / `keep_some_else` usage paths)
- observable outputs are asserted only through normalized shared surfaces (`stdout`, `stderr`, `exit_code`)

This contract does not prove internals such as host object layouts, Python traceback structure, parser internals, or prelude file organization.

## 3. Category placement boundaries

To avoid semantic drift, the shared cases for this issue must obey category boundaries:

- `eval`
  - use for direct language/pipeline/Option propagation behavior not tied to CLI mode wrapping
- `flow`
  - use for direct Flow-source behavior (`stdin |> lines |> ...`) where Option-aware Flow helpers are the behavior under test
- `cli`
  - use only when Option propagation proof requires mode-specific wrapper behavior (`-c` / `-p`) already in current shared contract

Boundary rules:

- do not move ordinary pipeline semantics into `cli` unless mode behavior is part of the assertion
- do not test pipe-mode wrapper mechanics in `flow`; that belongs to `cli`
- do not add error-category cases unless the failure surface is already documented and stable for shared assertion

## 4. Behavior inventory to prove

The implementation/test phases should add a minimal, behavior-oriented inventory proving the current contract.

Required behavior groups:

1. Direct Option rendering in eval surface
   - deterministic success output for `some(...)`
   - deterministic success output for `none` / `none(...)` forms already documented

2. Pipeline Option propagation in eval surface
   - `some(...)` propagation through at least one ordinary stage path
   - `none(...)` short-circuit of downstream stages
   - no silent loss of Option structure at final observable boundary

3. Option-aware helper propagation in existing stdlib paths
   - list/value pipeline behavior using already-implemented helpers (`map`, `keep_some`, `keep_some_else`, `flat_map_some`, `unwrap_or`, or equivalent already-documented helpers)
   - choose only helpers whose behavior is already stable and documented

4. Flow-oriented Option behavior
   - at least one deterministic Flow case showing Option filtering/propagation via already-implemented helpers
   - behavior must stay in first-wave Flow contract boundaries

5. CLI coverage only if needed
   - add/adjust `cli` cases only where existing `-c` or `-p` observable behavior is necessary to prove Option propagation contract consistency

Inventory size guidance:

- prefer a small set of high-signal cases over broad matrix expansion
- each case should prove one contract fact clearly
- avoid duplicated proofs across categories

## 5. Failure behavior coverage

Failure coverage in this issue is narrow and contract-driven.

Include only failures that are already documented/stable and directly tied to Option propagation or Option-aware helper usage.

Do not include:

- new diagnostics
- Python traceback-shape assertions
- undocumented misuse variants
- speculative option-error semantics

If a failure case is added, shared assertions must remain limited to documented observable surfaces (`stdout`, `stderr`, `exit_code`) with current normalization rules.

## 6. Core invariants

All shared cases added for this issue must preserve these invariants:

- no new semantics are introduced
- compared behavior is observable and deterministic
- category boundaries remain explicit (`eval` vs `flow` vs `cli`)
- Option propagation behavior matches current documented contract exactly
- cases remain independent and reproducible
- shared assertions do not depend on host-specific leakage
- uncovered Option behavior remains unguaranteed

## 7. Minimal example families

Minimal candidate families (subject to syntax/runtime confirmation in later phases):

- direct value rendering:
  - `some(1)`
  - `none`
- basic Option filtering pipeline:
  - `[some(1), none, some(2)] |> keep_some |> each(print)`

Real pipeline/flow families:

- `stdin |> lines |> map(parse_int) |> keep_some |> each(print)`
- equivalent deterministic command-mode flow-to-value examples using already-documented helpers

Examples in later phases must be validated against current syntax and current runtime behavior before they are committed as executable cases.

## 8. Non-goals

Out of scope for this issue:

- introducing any new Option constructor/destructor semantics
- changing pipeline lifting rules
- changing Flow orchestration semantics
- adding or renaming stdlib APIs
- parser changes for new surface forms
- proving non-Python hosts
- making Option behavior claims not backed by executable shared cases

## 9. Implementation boundary

This spec is behavior-only.

- it defines what must be proved by executable shared cases
- it does not prescribe interpreter internals or runner internals
- it remains portable at the contract level even though only Python is currently implemented

Later implementation work may touch runner or tests only where required to execute the defined shared proofs.

## 10. Documentation truth requirements

Later docs-sync phase must ensure repository truth surfaces describe this issue accurately and narrowly:

- describe this as shared coverage expansion for existing behavior
- do not claim new Option semantics
- do not imply broader Flow/pipeline guarantees than covered cases prove
- do not imply non-Python host implementation

Potential truth surfaces requiring synchronization if coverage inventory materially expands:

- `GENIA_STATE.md`
- `GENIA_REPL_README.md`
- `README.md`
- `spec/*` category READMEs
- `tools/spec_runner/README.md`

These edits belong to later phases unless a direct contradiction must be corrected immediately.

## 11. Complexity check

Assessment:

- Minimal: Yes
- Necessary: Yes
- Overly complex: No

Reason:

- this issue reveals and hardens existing behavior by executable proof
- it avoids semantic expansion while reducing regression risk in visible Option propagation paths

## 12. Acceptance criteria for later phases

Issue #150 is complete only when all of the following are true:

- executable shared cases prove existing Option propagation behavior across relevant active categories
- cases cover direct Option rendering plus propagation through supported pipeline/flow/helper paths already implemented
- any CLI additions are strictly contract-necessary
- runner/test changes (if any) are minimal and only support case execution/assertion
- no new language/runtime semantics are introduced
- docs are synchronized to the exact implemented coverage and no further

## Spec decision summary

This issue defines a narrow, implementation-ready contract for shared Option propagation coverage:

- prove existing `some(...)` / `none(...)` observable behavior
- prove existing pipeline/Flow propagation behavior where already implemented
- prove only already-documented option-aware stdlib behavior
- keep category boundaries explicit
- avoid semantic expansion

The next Design phase must map this contract into concrete case inventory and file placement without changing semantics.
