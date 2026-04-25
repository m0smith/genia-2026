# Issue #151 Preflight

CHANGE NAME: issue-151-scope-lock

---

## 0. BRANCH

Branch required:
YES

Branch type:
[x] feature
[ ] fix
[ ] refactor
[ ] docs
[ ] exp

Branch slug: issue-151-scope-lock

Expected branch: feature/issue-151-scope-lock

Base branch:
main

Rules:
- No work begins on `main`
- Branch must be created before Spec
- One branch per change

---

## 1. SCOPE LOCK

### Change includes:
- Preflight-only scope lock for issue #151.
- Reading and aligning against authoritative docs before spec/design/test/implementation.
- Recording required workflow and phase boundaries for follow-up prompts.

### Change does NOT include:
- Any language/runtime/CLI/flow semantic changes.
- Any implementation edits.
- Any test additions/changes.
- Any docs sync beyond this preflight artifact.

---

## 2. SOURCE OF TRUTH

Authoritative files:
- `GENIA_STATE.md` (final authority)
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
- `README.md`
- `AGENTS.md`

### Additional relevant:
- `docs/process/00-preflight.md`
- `docs/process/run-change.md`
- `docs/process/branch-workflow.md`

### Notes:
- Scope/details for issue #151 are not described in-repo at time of preflight; no behavior assumptions are made.

---

## 3. FEATURE MATURITY

Stage:
[ ] Experimental
[x] Partial
[ ] Stable

### How this must be described in docs:
- Preflight only. No behavior claims are introduced.

---

## 4. CONTRACT vs IMPLEMENTATION

### Contract (portable semantics):
- No contract change in preflight.

### Implementation (Python today):
- No implementation change in preflight.

### Not implemented:
- Any issue #151 behavior scope until explicitly defined by the issue/spec phase.

---

## 5. TEST STRATEGY

### Core invariants:
- Do not change behavior during preflight.
- Preserve phase isolation.

### Expected behaviors:
- Repository state remains behaviorally unchanged.

### Failure cases:
- Scope drift into spec/design/test/implementation during preflight.

### How this will be tested:
- No runtime/spec execution in this phase.
- Validate only that this preflight artifact is committed.

---

## 6. EXAMPLES

### Minimal example:
- N/A (preflight-only)

### Real example (if applicable):
- N/A (preflight-only)

---

## 7. COMPLEXITY CHECK

Is this:
[ ] Adding complexity
[x] Revealing structure

### Justification:
- Captures constraints and phase discipline without changing semantics.

---

## 8. CROSS-FILE IMPACT

### Files that must change:
- `docs/architecture/issue-151-preflight.md`

Risk of drift:
[x] Low
[ ] Medium
[ ] High

---

## 9. PHILOSOPHY CHECK

Does this:
- preserve minimalism? YES
- avoid hidden behavior? YES
- keep semantics out of host? YES
- align with pattern-matching-first? YES

### Notes:
- No semantic surface touched.

---

## 10. PROMPT PLAN

Will use full pipeline?
YES

Steps:
- Preflight
- Spec
- Design
- Test
- Implementation
- Docs
- Audit

---

## FINAL GO / NO-GO

Ready to proceed?
YES (for next prompt/phase only)
