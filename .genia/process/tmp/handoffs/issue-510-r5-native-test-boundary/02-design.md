# === GENIA DESIGN ===

CHANGE NAME:
issue #510 r5-native-test-boundary

CHANGE SLUG:
issue-510-r5-native-test-boundary

Issue: #510
Type: contract
Release classification: R5 — Native Test Expansion / Pytest Migration Wave 1
Branch: `contract/issue-510-r5-native-test-boundary`
Handoff directory: `.genia/process/tmp/handoffs/issue-510-r5-native-test-boundary/`

Sources read: `00-preflight.md`, `01-contract.md` (both present).

`GENIA_STATE.md` is the final authority. This design organizes a documentation/placement boundary. It introduces no code and no behavior.

---

## 0. BRANCH CHECK

- Must NOT be on `main`: confirmed — `contract/issue-510-r5-native-test-boundary`.
- Matches pre-flight/contract branch: confirmed.
- No switch, merge, or rebase.

---

## 1. PURPOSE

Translate the contract's placement rule into a concrete documentation structure and the guardrails that protect it. This is structure, not new behavior: it says *where the boundary is written down* and *how it is kept honest*, given that no runtime or test mechanism changes.

---

## 2. SCOPE LOCK

Contract includes:

- Documented placement rule: native test vs pytest vs shared semantic spec.
- "Complement, not replace" statement.
- Experimental / Python-reference-host framing.

Contract excludes:

- Any test migration, new native-test behavior, or runtime/parser/IR/host/CLI-harness/spec-runner/prelude change.
- Lifecycle execution, fixtures, parameterization, snapshots, property tests, parallelism, filtering, broad discovery, multi-host.
- A migration matrix or per-test migration plan.

Do not expand scope. This design adds documentation and (optionally) doc-guardrail tests only.

---

## 3. ARCHITECTURE

Where this fits:

- The boundary is **documentation that sits above an unchanged native-test stack**. The stack already has four layers per `GENIA_STATE.md` 9.x: kernel core (`src/genia/test_kernel.py`), assertion helpers, CLI/test-mode layer (`src/genia/test_cli.py`), and the inert R4 lifecycle descriptor/validation path. None of these layers are touched.

Affected components:

- `GENIA_STATE.md` native-test sections (9, 9.1, 9.1.1, 9.2, 9.6) — gain a placement-boundary subsection.
- Public testing guidance docs (README / testing docs / docs book section, if a current one exists and is incomplete or misleading on this point).
- Optionally, doc-sync / semantic guardrail tests if any contract sentence becomes protected semantic text.

Data flow:

- None at runtime. The "flow" is editorial: contract wording → `GENIA_STATE.md` subsection → any downstream doc references → optional guardrail test asserting the wording stays present/consistent.

Integration points:

- The boundary subsection must cross-reference, not duplicate, the existing native-test facts already in `GENIA_STATE.md`.

---

## 4. FILE PLAN

New files:

- None required. (A dedicated `docs/contract/` note is possible but unnecessary; prefer extending `GENIA_STATE.md`. Do not add a new doc file unless the DOCS phase finds existing files cannot host the boundary cleanly.)

Modified files (later phases — DOCS, and TEST only if a protected fact is introduced):

- `GENIA_STATE.md` — add an R5 native-test/pytest/shared-spec **placement boundary** subsection adjacent to sections 9.2 / 9.6; keep it descriptive and maturity-labeled.
- `docs/strategy/release-roadmap.md` — only if R5 positioning needs a one-line clarification; not required by the contract.
- README or testing docs — only if current public native-test guidance is incomplete or misleading about the boundary.
- `docs/contract/semantic_facts.json` — only if a sentence becomes a protected semantic fact.
- `tests/doc/test_semantic_doc_sync.py` — only if semantic-sync guardrails need to cover a new protected fact.

Removed files:

- None.

---

## 5. DATA / INTERFACE DESIGN

No runtime data shapes, value templates, variants, functions, classes, or interfaces change.

The only "interface" introduced is an **editorial classification table** to live in the `GENIA_STATE.md` boundary subsection. Proposed shape (three columns, descriptive only):

- *Surface* — the behavior under test (e.g. "Outcome `display` rendering", "kernel exception→error normalization", "native `--test` suite exit code").
- *Placement* — `native test` | `pytest` | `shared spec`.
- *Rationale* — Genia-facing source behavior | host/implementation internal | portable observable with existing shared coverage.

Seed rows come directly from contract §7 (all already present in the repo): `tests/native/outcome_rendering.genia`, `tests/native/r1_validated_pipeline.genia`, `examples/r3_validated_pipeline_native_tests.genia` → native; `tests/unit/test_native_test_kernel.py`, `tests/unit/test_native_test_cli.py` → pytest; selected native test-runner suite outcomes → shared spec.

No implementation logic. The table documents existing, correctly-placed artifacts; it is not a migration worklist.

---

## 6. CONTROL / ERROR FLOW

Execution flow: none — nothing executes as a result of this change.

Decision structure (the documented placement rule, restating contract §4 for design clarity):

1. Is the behavior expressible/verifiable in Genia source from the user's perspective? → native test.
2. Else, is it Python/parser/IR/host/runner/CLI-harness internal? → pytest.
3. Is it portable observable CLI/eval/flow/error/parse/IR behavior already covered by a shared spec? → shared spec (and do not duplicate it as a native test).
4. Mixed surface → split: Genia-facing assertion native, internal assertion pytest; do not duplicate wholesale.

Where errors are detected:

- Editorially, in review/audit: a misplaced test or an over-claiming sentence is a finding.
- Mechanically, only if a guardrail/doc-sync test exists for a protected sentence; then drift fails that test. No new runtime error path.

Boundaries that enforce correctness:

- The contract invariants (§6) are the acceptance gate for DOCS/AUDIT.
- `GENIA_STATE.md` remains the final authority; the boundary subsection must not contradict 9.x.

Must match contract failure behavior: confirmed — no runtime errors introduced; violations are review/guardrail findings only.

---

## 7. TEST PLAN INPUT

Invariants to test (DOCS/TEST phase, doc-level only):

- Boundary subsection exists in `GENIA_STATE.md` and labels native tests Experimental / Python reference host.
- Wording states native tests complement (do not replace) pytest and shared specs.
- No claim of unimplemented features (setup/teardown, fixtures, parameterization, snapshots, property tests, parallelism, filtering, multi-host).

Edge cases:

- Mixed-surface behavior described as "split", not "duplicate".
- Shared-spec-covered observable behavior not redirected to native tests.

Regression risks:

- Drift between the boundary subsection and existing 9.x native-test facts.
- A future reader treating the placement table as a migration mandate.

Test files / locations:

- `tests/doc/test_semantic_doc_sync.py` — only if a sentence becomes a protected semantic fact.
- No new `tests/unit/*` or `tests/native/*` — this change adds no behavior to assert.
- No new shared spec cases.

---

## 8. DOC IMPACT

- `GENIA_STATE.md` — REQUIRED in DOCS phase: add the placement-boundary subsection near 9.2/9.6.
- `GENIA_RULES.md` — not needed.
- `GENIA_REPL_README.md` — not needed.
- `README.md` — only if current native-test guidance is incomplete/misleading on placement.
- `docs/book` / testing docs — update only an existing native-test/testing section if present; do not create new structure speculatively.
- `docs/strategy/release-roadmap.md` — optional one-line R5 clarification.

---

## 9. COMPLEXITY CHECK

- [x] Minimal
- [ ] Necessary
- [ ] Over-engineered

Explanation: the design adds one documentation subsection (plus an optional descriptive table and optional guardrail) over an unchanged stack. It reveals existing structure and reduces placement ambiguity without adding surface area — consistent with the pre-flight "Revealing structure" classification.

---

## 10. FINAL CHECK

- Matches contract exactly: YES — organizes the §3/§4 placement rule and §6 invariants; adds nothing beyond.
- No new behavior: YES — documentation/guardrail only; native-test stack untouched.
- No host-specific assumptions: YES — boundary is portable; Python reference-host detail is kept explicitly separate, per contract §9.
- Ready for implementation: YES — but note this issue is expected to be docs/contract-only; the IMPLEMENTATION phase is likely a no-op unless the issue body requires behavior changes.

---

OUTPUT: design complete. Recommended next phase: TEST (doc-guardrail only if a protected fact is introduced) → DOCS sync of `GENIA_STATE.md`.
