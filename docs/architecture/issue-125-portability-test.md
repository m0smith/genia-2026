# Issue #125 Test Phase — Require Portability Analysis in Pre-Flight

**Phase:** test
**Branch:** `issue-125-portability-preflight`
**Issue:** #125 — Require portability analysis in pre-flight for all features
**Scope:** Process/documentation only. No runtime behavior changes.

---

## 1. Scope

Test only what the spec defines. The spec (section 8 — Validation) explicitly determined:

> No machine-asserted test change required for this issue. `tests/test_semantic_doc_sync.py`
> covers protected semantic facts in `docs/contract/semantic_facts.json`. The pre-flight
> template (`docs/process/00-preflight.md`) is not currently a source of machine-asserted
> facts. Adding test coverage for the template structure is out of scope for this issue.

No new test functions are added in this phase. The test phase fulfils the pipeline requirement
by:

1. Recording the decision and its justification.
2. Establishing the pre-implementation baseline (all existing tests pass).
3. Documenting the manual review invariants that serve as the validation mechanism.
4. Specifying what the full suite must confirm after implementation.

---

## 2. Pre-Implementation Baseline

**Command run:**

```
python -m pytest tests/test_semantic_doc_sync.py -q
```

**Result:**

```
....................................................                     [100%]
52 passed in 0.19s
```

All 52 existing semantic doc sync tests pass before any file in this issue is edited. This is
the baseline. Implementation must not cause any of these 52 tests to fail.

**Portability section absent from template (confirmed):**

```
grep -n "3a\|PORTABILITY\|portability" docs/process/00-preflight.md
(no output)
```

This confirms the implementation has not yet been applied and the tests are being run against
the pre-change state, as required by AGENTS.md.

---

## 3. Why No New Failing Tests

The spec decision is grounded in the following:

- `tests/test_semantic_doc_sync.py` guards semantic facts held in
  `docs/contract/semantic_facts.json`. Those facts describe language contract and host
  contract behavior.
- Process document structure (e.g., which sections a template contains) is not a semantic
  fact. It is workflow discipline.
- The portability analysis requirement is enforced by human/agent review at the spec step,
  not by the language runtime or the shared spec runner.
- Adding machine-asserted tests for template structure would require extending the scope of
  `test_semantic_doc_sync.py` beyond its current semantic-facts mandate, which is a separate
  issue.

Tension with AGENTS.md:

AGENTS.md states: "The `test` phase must commit failing tests before implementation." The
spec for this issue explicitly excluded machine-asserted tests. When the spec and the
general pipeline rule conflict, the spec is the higher authority for this issue because it
was explicitly decided after examining the current test infrastructure. This test-phase
document commits that decision on the record before implementation proceeds.

---

## 4. Manual Review Invariants (from Spec, section 9)

These invariants replace machine assertions as the validation mechanism. They must be
checked by the agent or human during the audit phase:

1. `docs/process/00-preflight.md` contains a section labeled `3a. PORTABILITY ANALYSIS`.
2. That section contains all seven field labels:
   - `Portability zone:`
   - `Core IR impact:`
   - `Capability categories affected:`
   - `Shared spec impact:`
   - `Python reference host impact:`
   - `Host adapter impact:`
   - `Future host impact:`
3. Each field label has guidance text (definition and/or valid values).
4. The section contains a minimal process-change example.
5. The section does not claim unimplemented hosts are implemented.
6. `docs/process/run-change.md` step 2 contains text about PORTABILITY ANALYSIS being
   required before the spec step.
7. `docs/process/llm-prompts.md` contains a `## Preflight Phase` section listing all seven
   field names.

Prohibited strings (must not appear in any portability-analysis guidance text):

- `"TBD"` as a valid field answer
- `"to be determined"` as a valid field answer
- Any statement claiming Node.js, Java, Rust, Go, or C++ hosts are implemented

---

## 5. Post-Implementation Verification Plan

After the implementation phase edits the three files, run:

```
python -m pytest tests/test_semantic_doc_sync.py -q
```

Expected result: 52 passed (same baseline). Zero regressions.

Also verify manually:

- Open `docs/process/00-preflight.md` and confirm section `3a. PORTABILITY ANALYSIS` is
  present between section 3 and section 4.
- Open `docs/process/run-change.md` and confirm the portability requirement note appears
  under step 2.
- Open `docs/process/llm-prompts.md` and confirm the `## Preflight Phase` section and field
  list are present.

---

## 6. Complexity Check

Minimal and sufficient.

No new test code is added. The baseline is established. The manual review invariants are
documented. The post-implementation check is specified. This is the correct and honest scope
for a process-only change where the spec explicitly excluded machine-asserted tests.

---

## 7. Final Check

- Tests cover spec-defined behavior: YES — manual review invariants map 1:1 to spec section 9.
- Tests cover failure behavior: YES — prohibited strings are documented.
- Tests cover edge cases: N/A — process doc, not runtime behavior.
- Results are real, not assumed: YES — baseline run confirmed 52 passed.
- Ready for implementation phase: YES.
