# Issue #149 Spec — Pattern Matching Shared Spec Coverage

## 1. Scope

This issue defines a shared-semantic coverage expansion for already-implemented pattern matching behavior.

Included in this phase:

- executable shared spec cases proving existing pattern-match behavior across currently active shared categories where pattern behavior is observable
- coverage for deterministic success behavior in `eval`
- coverage for deterministic normalized failure behavior in `error` where diagnostics are already documented and stable
- runner/test updates only if strictly required to execute the added shared cases

Excluded from this phase:

- new pattern syntax
- new pattern semantics
- parser redesign
- runtime redesign
- host-specific behavioral expansion
- non-Python host implementation work
- broad refactors unrelated to shared pattern coverage

This issue is coverage expansion for existing behavior, not a language feature change.

## 2. Portable observable contract

The contract to prove in this issue is limited to observable behavior already defined in authoritative docs and existing runtime behavior:

- first-match-wins behavior for pattern branches
- deterministic matching behavior for already-implemented pattern families currently exposed in shared surfaces:
  - literals
  - wildcard and variable binding
  - list/tuple patterns supported today
  - map/key matching forms supported today
  - option patterns (`some(...)` / `none`) supported today
- deterministic guard behavior where already implemented (`when` pass/fail style behavior)
- deterministic normalized failure surfaces for documented mismatch/error categories already eligible for shared error assertions

This contract does not prove parser internals, VM/interpreter internals, host object shapes, or traceback details.

## 3. Category boundaries

Shared case placement for this issue must keep category boundaries explicit:

- `eval`
  - success-path pattern semantics and deterministic evaluated output
- `error`
  - stable, documented, normalized failure behavior tied to pattern matching

Boundary rules:

- do not move success-path behavior into `error`
- do not assert unstable wording in `error`
- do not add pattern coverage to unrelated categories unless the behavior is category-specific and already documented

## 4. Behavior inventory to prove

The later test/implementation phases should add a minimal, high-signal inventory that proves the current contract.

Required success behavior groups (`eval`):

1. first-match selection
2. literal match for string/integer forms already implemented
3. wildcard and variable binding behavior
4. list/tuple exact/shape behavior already implemented
5. map/key partial and shorthand behavior already implemented
6. option pattern behavior for `some(...)` and `none`
7. guard pass and guard skip behavior

Required failure behavior groups (`error`):

1. deterministic match-miss surface where currently documented
2. deterministic guard-all-fail or equivalent documented failure surface
3. deterministic malformed-glob (or equivalent pattern syntax failure) only if wording/shape is already stable for shared assertion

Inventory size guidance:

- prefer a compact case set with one contract fact per case where practical
- avoid duplicated proof across cases
- avoid speculative or host-leaky assertions

## 5. Failure behavior constraints

Failure coverage in this issue is intentionally narrow.

Include only failures that are already:

- implemented
- documented
- stable enough for shared normalized assertion

Do not include:

- traceback shape assertions
- undocumented parser/runtime error variants
- future-looking diagnostics
- wording that is not yet stable in truth docs

## 6. Core invariants

All shared cases added for this issue must preserve:

- no new semantics
- deterministic observable outputs
- explicit category boundary (`eval` vs `error`)
- assertions only on normalized shared surfaces (`stdout`, `stderr`, `exit_code`)
- no host-internal leakage
- no implied guarantees beyond covered cases

## 7. Minimal example families

Minimal candidate families (subject to exact syntax/runtime confirmation in later phases):

- first match:
  - `match 1 { 1 => "ok" _ => "no" }`
- literal and wildcard:
  - `match "a" { "a" => 1 _ => 0 }`
- option:
  - `match some(1) { some(x) => x none => 0 }`
- guard behavior:
  - branch with guard pass and guard skip variants

Failure family candidates:

- pattern miss producing documented normalized failure
- malformed glob form producing documented normalized parse/pattern failure

## 8. Non-goals

Out of scope for this issue:

- introducing new pattern forms
- changing guard semantics
- changing option semantics
- changing pipeline/flow semantics
- changing CLI mode behavior
- proving non-Python hosts
- redesigning shared runner schema

## 9. Implementation boundary

This spec is behavior-only.

- It defines what must be proved by executable shared cases.
- It does not prescribe interpreter internals.
- It does not authorize semantic expansion.

Any runner/test changes in later phases must remain minimal and strictly supportive of executing covered cases.

## 10. Documentation truth requirements

Later docs-sync work must keep truth surfaces aligned with landed executable coverage:

- describe this issue as coverage expansion for existing behavior
- do not claim new pattern language capabilities
- do not imply non-Python host support
- keep category boundaries and guarantees explicit

Potential docs surfaces to sync later if inventory/status wording changes:

- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
- `README.md`
- `spec/eval/README.md`
- `spec/error/README.md`
- `tools/spec_runner/README.md`

## 11. Complexity check

Assessment:

- Minimal: Yes
- Necessary: Yes
- Overly complex: No

Reason:

- this issue strengthens regression proof for current pattern behavior without changing semantics or architecture

## 12. Acceptance criteria for later phases

Issue #149 is complete only when all of the following are true:

- executable shared cases prove the approved pattern success/failure inventory within `eval` and `error`
- added cases validate only already-implemented behavior
- any runner/test updates are minimal and only support case execution
- no new language/runtime semantics are introduced
- docs are synchronized to exact landed coverage and no further

## Spec decision summary

This issue defines a narrow, implementation-ready contract for shared pattern coverage:

- prove existing deterministic pattern success behavior
- prove existing deterministic normalized failure behavior
- keep `eval`/`error` boundaries explicit
- avoid semantic expansion
- align docs later to exactly what executable cases prove
