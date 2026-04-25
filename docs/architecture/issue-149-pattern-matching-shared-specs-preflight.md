# Issue #149 Preflight — Pattern Matching Shared Spec Coverage

CHANGE NAME: pattern-matching-shared-spec-coverage

## 0. BRANCH

Branch required:
YES

Branch type:
- [x] feature
- [ ] fix
- [ ] refactor
- [ ] docs
- [ ] exp

Branch slug: issue-149-pattern-matching-shared-specs

Expected branch: feature/issue-149-pattern-matching-shared-specs

Base branch:
main

Rules acknowledged:

- No work begins on `main`
- Branch must be created before Spec
- One branch per change

## 1. SCOPE LOCK

### Change includes

- defining the issue scope as **shared-spec coverage expansion** for already-implemented pattern matching behavior
- adding or adjusting shared cases only in active spec categories where pattern behavior is currently observable (`eval`, `error`)
- keeping assertions limited to normalized shared surfaces (`stdout`, `stderr`, `exit_code`)
- syncing any affected documentation/testing inventory in later phases

### Change does NOT include

- introducing new pattern syntax or new semantics
- redesigning parser/runtime behavior
- changing host-specific internals
- non-Python host implementation work
- broad refactors unrelated to pattern shared-spec coverage

## 2. SOURCE OF TRUTH

Authoritative files:

- `GENIA_STATE.md` (final authority)
- `GENIA_RULES.md`
- `README.md`
- `AGENTS.md`

### Additional relevant

- `GENIA_REPL_README.md`
- `spec/eval/*`
- `spec/error/*`
- `tests/test_spec_ir_runner_blackbox.py`

### Notes

- If there is any conflict, `GENIA_STATE.md` wins.
- This issue must prove existing behavior; it must not define new language behavior.

## 3. FEATURE MATURITY

Stage:
- [ ] Experimental
- [x] Partial
- [ ] Stable

### How this must be described in docs

Pattern matching shared coverage should be described as **expanded executable proof of existing behavior** and not as a new feature rollout.

## 4. CONTRACT vs IMPLEMENTATION

### Contract (portable semantics)

- deterministic first-match behavior
- deterministic literal/list/tuple/map/option/wildcard pattern matching outcomes where already implemented
- deterministic normalized failure surfaces for documented mismatch/guard/glob errors

### Implementation (Python today)

- Python reference host executes the current shared cases through the existing runner

### Not implemented

- non-Python host conformance for this coverage surface
- any semantics not already defined in `GENIA_STATE.md`

## 5. TEST STRATEGY

### Core invariants

- no new semantics introduced
- category boundaries remain explicit
- deterministic outputs only

### Expected behaviors

- pattern success cases in eval surface
- documented pattern failures in error surface

### Failure cases

- match miss behavior
- guard rejection behavior
- malformed glob behavior (where documented and stable)

### How this will be tested

- shared YAML cases under `spec/eval` and `spec/error`
- shared runner/test suite assertions for discovery and execution paths

## 6. EXAMPLES

### Minimal example

- `match 1 { 1 => "ok" _ => "no" }`

### Real example (if applicable)

- `match some(41) { some(x) => x + 1 none => 0 }`

## 7. COMPLEXITY CHECK

Is this:
- [ ] Adding complexity
- [x] Revealing structure

### Justification

This issue should make existing pattern semantics more explicit through executable shared proofs without expanding semantics.

## 8. CROSS-FILE IMPACT

### Files that must change

- `docs/architecture/issue-149-pattern-matching-shared-specs-preflight.md`
- (later phases only) relevant files in `spec/eval/*`, `spec/error/*`, and related shared-runner tests/docs as needed

Risk of drift:
- [x] Low
- [ ] Medium
- [ ] High

## 9. PHILOSOPHY CHECK

Does this:

- preserve minimalism? YES
- avoid hidden behavior? YES
- keep semantics out of host? YES
- align with pattern-matching-first? YES

### Notes

Coverage should stay small, deterministic, and contract-oriented.

## 10. PROMPT PLAN

Will use full pipeline?
YES

Steps:

- Spec
- Design
- Test
- Implementation
- Docs
- Audit

## FINAL GO / NO-GO

Ready to proceed?
YES

### If NO, what is missing

N/A
