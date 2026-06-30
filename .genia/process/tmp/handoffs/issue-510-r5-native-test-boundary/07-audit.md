# === GENIA AUDIT ===

CHANGE NAME:
issue #510 r5-native-test-boundary

CHANGE SLUG:
issue-510-r5-native-test-boundary

Issue: #510
Type: contract
Release classification: R5 — Native Test Expansion / Pytest Migration Wave 1
Branch: `contract/issue-510-r5-native-test-boundary`
Handoff directory: `.genia/process/tmp/handoffs/issue-510-r5-native-test-boundary/`

`GENIA_STATE.md` is final authority. Audited assuming the change is wrong until proven correct.

---

## 0. BRANCH CHECK

- Not on `main`: confirmed — `contract/issue-510-r5-native-test-boundary`.
- Branch matches the change across all handoffs: confirmed.
- Unrelated changes: only untracked `.claude/settings.local.json` (local tooling, not part of this change). The two tracked modifications (`GENIA_STATE.md`, `tests/doc/test_semantic_doc_sync.py`) are exactly the change surface. No stray edits.
- Note: the change is uncommitted; there are zero commits on the branch vs `main`. Commits were deferred by each phase prompt (see §7).

---

## 1. SUMMARY

Status:

- [x] PASS
- [ ] PASS WITH ISSUES
- [ ] FAIL

The change adds one authoritative `GENIA_STATE.md` subsection documenting the R5 native-test / pytest / shared-spec placement boundary, plus one doc-guardrail test that protects its required wording. It introduces no runtime, native-test, parser, IR, CLI, prelude, host-adapter, spec-runner, or shared-spec behavior, and matches the contract and design exactly. Two minor, non-blocking notes are recorded below.

---

## 2. CORE CHECKS

Contract ↔ Implementation: MATCH.
- Contract §3/§4 placement rule (Genia-facing → native; host/internal → pytest; portable observable covered → shared spec; complement-not-replace; Experimental / Python reference host) is reproduced precisely in the new `GENIA_STATE.md` section (lines ~2261–2281).
- Contract §8 non-goals (setup/teardown, fixtures, parameterization, snapshots, property tests, parallelism, filtering, broad discovery, multi-host) are all present as explicit "not implemented" lines.

Design ↔ Implementation: MATCH.
- Design called for a descriptive, maturity-labeled boundary subsection adjacent to the existing native-test sections. Implementation placed it immediately after "Native test layer boundaries" and before "## 9.1) Native test kernel core" — an adjacent, sensible location consistent with the design's "near §9.2 / §9.6" intent.
- Design marked the placement table and the doc guardrail as optional. The table was not added (acceptable). The guardrail was added in the TEST phase and made green in IMPLEMENTATION (the test-first flow). No deviation of substance.

Tests ↔ Contract: COVERED.
- `test_native_test_placement_boundary_stays_explicit_in_state` asserts concrete required wording: complement / do-not-replace phrasing, Genia-facing placement, the pytest-home surfaces (parser, Core IR, host adapter, CLI harness, spec runner), shared-spec authority, Experimental + Python reference host, and a per-feature "not implemented / no <feature>" check for every unsupported feature. This maps 1:1 to the contract invariants for a docs-only change.

Docs ↔ behavior: TRUTHFUL.
- The section documents placement guidance only and changes no behavior. Every claim is maturity-labeled and consistent with the surrounding §9.x native-test facts.

No scope expansion: CONFIRMED. Diff is limited to the `GENIA_STATE.md` subsection and the one guardrail test.

Edge cases: the contract's "mixed surface → split, not duplicate" and "covered observable behavior stays in shared specs" rules are represented in the section's pytest-home and shared-spec paragraphs.

Mismatches: none material (see §7 minor notes).

---

## 3. TEST QUALITY

- Covers core behavior: YES — asserts the boundary section exists and contains each required clause.
- Covers failure case: YES — TEST-phase handoff recorded the expected red (`1 failed`, marker absent) before implementation; the marker-find assertion fails if the section is removed or renamed.
- Asserts concrete results: YES — exact normalized substrings, not vague presence checks.
- Fails on regression: YES — removing any required clause or any unsupported-feature disclaimer fails the test.

Gaps / risks: low. The guardrail is wording-based (appropriate for a docs boundary). It does not, and need not, assert runtime behavior because none changed.

---

## 4. DOC TRUTH

- Reflects implemented behavior only: YES — it is a placement/guidance boundary over the already-implemented native-test stack; it claims no new capability.
- Partial features marked: YES — labeled Experimental, Python reference host.
- Avoids implying future capability: YES — unsupported features are each explicitly "not implemented".
- Examples: none added; none rely on unimplemented features.

Violations: none.

---

## 5. CONSISTENCY

Cross-doc alignment verified in DOC SYNC and re-confirmed here:
- `GENIA_STATE.md` (authoritative section) — source of truth.
- `docs/strategy/release-roadmap.md` R5 section — same split; consistent (planning doc).
- `README.md`, `GENIA_REPL_README.md`, `GENIA_RULES.md`, `docs/architecture/*`, `docs/parking-lot/native-test-ergonomics.md` — consistent; either describe the same split or point to `GENIA_STATE.md`; none imply native tests replace pytest; none claim unsupported features as implemented.

Drift: none found.

Risk level:
- [x] Low
- [ ] Medium
- [ ] High

---

## 6. COMPLEXITY

- [x] Minimal and necessary
- [ ] Slightly complex but justified
- [ ] Over-engineered

One documentation subsection plus one guardrail test. Reveals existing structure; adds no surface area.

---

## 7. ISSUES

Issue 1 — process/commit hygiene
- Severity: [x] Minor
- File(s): branch state (no commits).
- Problem: The full change is uncommitted; AGENTS.md expects phase commits with prefixes (`test(...)`, `feat`/`docs(...)`, etc.), the failing-test commit before implementation, and the implementation commit referencing the failing-test SHA. None exist yet.
- Why it matters: phase-commit traceability is part of the repo's workflow discipline.
- Minimal fix: handle at the explicit commit step (out of scope for DOC SYNC / AUDIT / DISTILLATION, which the phase prompts instructed not to commit). Not a correctness blocker.

Issue 2 — cosmetic wording (do not "fix" casually)
- Severity: [x] Minor
- File(s): `GENIA_STATE.md` (new section), line ~2273: "setup/teardown execution and setup/teardown are not implemented".
- Problem: reads slightly redundant.
- Why it matters / caution: the phrasing is load-bearing for the guardrail, which looks for the substring "setup/teardown are not implemented" (or "is not implemented" / "no setup/teardown"). Tightening to "setup/teardown execution is not implemented" would break that exact-substring check. Leave as-is, or change the doc and the guardrail together in a future change.
- Minimal fix: none recommended now.

---

## 8. RECOMMENDED FIXES

1. None blocking. Proceed to DISTILLATION, then to the commit step where the phase-commit prefixes and failing-test → implementation SHA linkage should be established.

---

## 9. VALIDATION

- Tests executed: YES.
  - `PYTHONPATH=src python3 -m pytest -q tests/doc/test_semantic_doc_sync.py` → `86 passed`.
  - `PYTHONPATH=src python3 -m pytest -q tests/doc/test_semantic_doc_sync.py tests/unit/test_native_test_kernel.py tests/unit/test_native_test_cli.py tests/unit/test_outcome_native_tests.py` → `116 passed`.
  - Includes `test_native_test_placement_boundary_stays_explicit_in_state` (green).
- Results observed: YES (above).
- Examples verified: N/A (no examples added/changed).
- Docs checked against behavior: YES (DOC SYNC sweep + diff review).
- Caveat: the canonical `uv run pytest` command could not provision the pinned interpreter offline in this environment; ran with system `python3` (3.10) + `PYTHONPATH=src`. The doc-sync/native-test suites are interpreter-agnostic, so results are trustworthy; a maintainer should re-run the canonical `uv` command in a networked environment before merge.

---

## KILLER WORKFLOW DRIFT CHECK

- Stayed aligned: YES — indirectly strengthens Outcome-aware validated data pipelines by clarifying that Genia-facing Outcome/validation/Flow-Seq/Sheet/diagnostics behavior is the home for native tests.
- General-purpose machinery added: NO.
- Premature actors/UI/lifecycle/multi-host/demo work: NO — the section explicitly disclaims lifecycle execution and multi-host.
- Docs imply strategy is implemented behavior: NO — strategy/roadmap remain labeled as planning; the boundary is maturity-labeled.

---

## FINAL VERDICT

Ready to merge? YES — pending the standard commit step (phase-prefixed commits, failing-test → implementation SHA linkage) and a final canonical `uv run pytest` confirmation in a networked environment. No correctness, scope, or truth blockers.
