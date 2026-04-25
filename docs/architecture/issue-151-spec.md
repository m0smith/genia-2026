# Issue #151 Spec — Preflight-Locked, No-Behavior Change

## 1. Purpose

This spec defines the behavior contract for issue #151 exactly as locked by the preflight phase:

- this phase introduces **no Genia language/runtime/CLI/flow semantic changes**
- this phase introduces **no implementation behavior changes**
- this phase defines only the process-facing contract that later phases must follow

If later prompts introduce behavior updates, they must be specified in a new spec revision before any implementation work.

## 2. Scope (from preflight)

### Included

- writing a spec artifact for issue #151
- preserving the preflight scope lock
- defining testable invariants for “no behavior change”

### Excluded

- parser/runtime/interpreter changes
- standard-library changes
- host-adapter changes
- shared-spec runner changes
- test-suite behavior changes
- docs-sync changes that claim new implemented behavior

## 3. Behavior definition

Issue #151, in this phase, defines a **null semantic delta**:

- Inputs: unchanged
- Outputs: unchanged
- Error surfaces: unchanged
- State transitions: unchanged

Observable behavior for all currently implemented categories (`parse`, `ir`, `eval`, `cli`, `flow`, `error`) remains exactly as already documented in `GENIA_STATE.md`.

## 4. Semantics

### Evaluation behavior

- program evaluation semantics are unchanged
- expression parsing/evaluation boundaries are unchanged
- flow orchestration semantics are unchanged

### Matching behavior

- pattern-matching forms and constraints are unchanged

### Error behavior

- existing normalized error surface remains unchanged

### Edge cases

- no new edge-case semantics are added in this issue phase

## 5. Failure behavior

Failure for this issue phase is defined as **scope drift**. A failure occurs if any change in this phase:

- alters observable runtime behavior
- alters portable contract claims
- alters shared-spec expectations/results
- claims features not implemented

What must not happen on failure:

- no silent semantic expansion
- no undocumented behavior changes
- no host-only behavior promoted to portable contract

## 6. Invariants

The following truths must hold:

1. `GENIA_STATE.md` remains the final authority for implemented behavior.
2. This issue phase does not modify language/runtime/CLI/flow semantics.
3. Later phases may not exceed this scope without an explicit spec update.
4. Documentation must not claim behavior beyond implemented and tested surfaces.

## 7. Examples

### Minimal

- Existing programs continue to parse and evaluate exactly as before.
- Existing shared spec cases continue to represent the same contract categories.

### Real

- Any subsequent commit in this issue that changes user-visible behavior without first revising this spec is non-compliant.

## 8. Non-goals

- adding new syntax
- changing current CLI modes or dispatch rules
- expanding flow semantics
- broadening cross-host guarantees
- introducing implementation details/design decisions in this phase

## 9. Implementation boundary

This spec is contract-level and process-level only:

- portable semantics are unchanged
- no Python-specific mechanism is assumed or required
- no host-internal structure is standardized here

## 10. Documentation requirements

For this issue phase:

- `GENIA_STATE.md`: no behavior wording changes required
- `GENIA_RULES.md`: no invariant wording changes required
- `GENIA_REPL_README.md` / `README.md`: no behavior wording changes required
- maturity labels remain unchanged because no behavior is added

## 11. Complexity check

- [x] Minimal
- [x] Necessary
- [ ] Overly complex

Explanation:

This spec intentionally minimizes risk by freezing scope to a no-behavior-change contract until a later prompt explicitly expands scope.

## 12. Final check

- No implementation details included
- No scope expansion beyond preflight
- Consistent with `GENIA_STATE.md` authority model
- Behavior is precise and testable via “no semantic delta” invariants
