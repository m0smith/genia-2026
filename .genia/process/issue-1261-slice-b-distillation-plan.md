# #1261 Slice B: post-audit documentation distillation plan and closeout checklist

**Status: PLANNING ONLY.** Prepared in parallel with Codex's maintainability re-review of `6649d0b6`. Nothing here changes the implementation branch or any authoritative document, and no review or audit verdict is claimed. Apply it only after the independent re-review and truth audit establish the final behavior. Do not merge, close #1261/#1250, or begin Slice C.

Basis: `origin/claude/charming-gauss-dsstwt` at `6649d0b6` (code verified at `669e44d8`).

## 1. Budget

`GENIA_STATE.md` is **42,999 / 43,000** words by the gate's measure (`len(STATE.split())`, `tests/doc/test_state_distillation_gates.py`; `wc -w` reads 42,864 and is not the gate). Headroom is **1 word**: any truth correction from the audit must be paired with an equal reduction. Line budget (3,900) is not tight.

## 2. Findings (read-only audit of the current branch)

| ID | Where | Finding | Severity |
| --- | --- | --- | --- |
| D1 | `GENIA_STATE.md:747` | "C++ lacks `=:` (known gap `immutable_bindings`, genia-cpp#50)" misattributes ownership. The optional-capability gap is tracked at `genia-2026#1261` in `spec/known_host_gaps.json`; `genia-cpp#50` owns the required parser/lowering syntax obligation. | Medium: misleading C++ statement in the final authority. Fix is word-neutral. |
| D2 | `docs/strategy/release-roadmap.md:65` | "proposes, but does not implement, ... immutable lexical bindings" is obsolete for Python once Slice B is accepted; it still correctly excludes default-open and closed functions. | Medium: obsolete transitional claim. |
| D3 | `docs/host-interop/HOST_CAPABILITY_MATRIX.md` table | The matrix has rows for `open functions (R20)` and `multi-file eval` but **no `immutable_bindings` row**. Slice B appears only in a prose subsection. | Medium: omission, not a false claim. |
| D4 | `docs/architecture/core-ir-portability.md:188,209,222` | Heading "Model B Slice A declaration carriers (Partial)" now mixes Slice A carrier text with Slice B execution text. Two lines say "C++ ... not claimed (issue #1250 gap)" where the owner of the C++ syntax work is `genia-cpp#50`. | Low-Medium |
| D5 | `docs/host-interop/HOST_CAPABILITY_MATRIX.md:92-120` | Slice A C++ evidence (43 cases: 5 PASS / 38 UNSUPPORTED at ancestor contract `6402e668`) is retained correctly as non-current. The Slice B C++ observation (reviewer: 26/26 UNSUPPORTED, **not run by the implementer**) is not recorded; do not add a number the implementer cannot reproduce. | Low |
| D6 | `docs/book/03-functions.md:8-13` | Process vocabulary ("Slice A adds...", "Slice B executes...") in a user-facing chapter. | Low |
| D7 | `GENIA_RULES.md:5-15`, `GENIA_REPL_README.md:5-15`, `README.md:15-25` | The same ~10-line Model B paragraph is triplicated; `GENIA_STATE.md` section 3 already states it fully. Divergence risk (M3 was exactly this: three summaries drifting from STATE). | Medium: duplication. |
| D8 | `docs/cheatsheet/core.md:11-15`, `unix-power-mode.md:8-11`, book | Closed/pattern forms correctly marked "parse/lower only". No inaccuracy found; wording will need a second pass when Slices C-E land. | Info |
| D9 | `AGENTS.md` | Records R9-R28 status; no entry for the pre-R29 gate. Process-controlled file; any update is a separate maintainer decision. | Info |
| D10 | `docs/design/composability-matrix.md` | `=:` is not a Template/representation/matcher family member; the sync test covers builtin families only. No row required. | None |
| D11 | `docs/contract/semantic_facts.json:255,448`, `apps/mcp/mcp.genia`, `tests/data/mcp_language_profile.golden.json` | Consistent with STATE after `f3ced434` (checked by generator `--check` and the registry tests). | None |

No remaining discrepancy found between verified Slice B behavior and the four root documents other than D1 and D7. Entry-scope-only reservation (M3) is correctly stated in all of them at `6649d0b6`.

## 3. Distillation plan (apply after independent truth audit)

All edits keep semantics identical. Run `tests/doc`, `tests/unit/test_r28_mcp_language_*`, `tools/gen_mcp_language_profile.py --check`, the cheatsheet tests and `mkdocs build --strict` after each step. Delete `site/` after a strict build (the STATE-citation test scans it).

1. **D1 (word-neutral):** replace the STATE sentence with "C++ lacks `=:` (optional-capability gap `immutable_bindings`; syntax work: genia-cpp#50)." Re-check word count.
2. **D7 (−~230 words across the three roots, STATE untouched):** keep one canonical short paragraph in `GENIA_RULES.md` (invariants) and replace the README and REPL README copies with a 3-line summary plus a pointer to STATE section 3. Confirm no sync test pins the removed text before editing: `rg "Model B declarations" tests` currently finds no test dependency, but re-verify at apply time.
3. **STATE headroom (target ≥ 150 words so the audit can add truth without a new budget fight):** candidates measured at `6649d0b6`, in order of safety:
   - Section 9.50 evidence file list (about 45 words) and the "Release status" paragraph (about 44 words): both are evidence/history that `docs/releases/R28.md` and `R10-R14.md` already carry.
   - Slice A wire-shape prose in section 3 is already reduced to a pointer; no further cut.
   - Do **not** cut "Current consistency notes" (1,778 words) or other behavioral sections without a separate migration-map/crosswalk update; they are normative, not history.
   Any move to `docs/state-record/*` must regenerate the crosswalk (`tools/state_records.py`) and keep baseline identifiers (`test_every_baseline_identifier_is_in_state_or_a_state_record`).
4. **D2:** edit `release-roadmap.md:65`: immutable lexical bindings are implemented in Python (Slice B, `immutable_bindings`, C++ gap), default-open and closed functions remain proposed; STATE stays authoritative.
5. **D3:** add an `immutable_bindings` row to the capability table: Python Implemented; C++ Not Implemented (optional-capability gap `genia-2026#1261`; syntax `genia-cpp#50`); Notes cite `spec/*/model-b-b-*`.
6. **D4:** rename the Core IR section "Model B declaration carriers (Partial)", add a one-line per-carrier status (`IrImmutableBind` executes in Python; `IrPatternFuncDef`/`IrClosedFuncDef` parse/lower only) and make both C++ lines cite `genia-cpp#50`.
7. **D6:** in the book, describe features rather than slices once Slice B is accepted; revisit when C-E land.
8. **D5:** record the Slice B C++ observation only if the C++ maintainer or the audit reproduces it against a pinned binary at a current contract revision.

## 4. Ownership of deferred items (verified 2026-10-19/20)

| Item | Stated owner | Tracked as an issue? | Risk / action |
| --- | --- | --- | --- |
| M4 global-lock design | "#1261 design follow-up (Claude/m0smith)" | **No.** #1261 has no comments; the only record is PR #1262 text and `.genia/process`. | **New blocker for closeout:** once #1261 closes, the follow-up is orphaned. Open a tracked issue before #1261 closes. Draft below. |
| M6 / N5 documentation consumers | "next prelude/documentation-consumer implementer, m0smith integration, #1261/#1250" | **No** dedicated issue; closest existing tracker is #1101 (code documentation standard). | Same: open or attach to #1101 explicitly. Draft below. |
| Docker `r25-cell-nested-send-transaction` | genia-cpp#51 (opened by the maintainer per PR comment 6277840370) | Yes, in genia-cpp | I could **not** read genia-cpp#51: this session is scoped to `m0smith/genia-2026` only. Existence is taken from the maintainer's comment, not verified. Do not add the repository without being asked. |
| Slice B optional C++ gap | `genia-2026#1261` (`spec/known_host_gaps.json`) | Yes, but #1261 closes at merge | `known_host_gaps.json` requires a `genia-2026#` tracker; when #1261 closes, re-point it to a long-lived tracker or the parity gate may still pass but the reference becomes a closed issue. Decide with the maintainer. |
| C++ syntax (required obligation) | genia-cpp#50 under #1250 | Yes | No change. |

Draft issue text (not created; creating issues is the maintainer's call):

- *M4:* "Design: narrower synchronization domain for Env binding-policy writes." Context: process-wide `_BINDING_LOCK` serializes unrelated execution trees; measured +1% to +8% uncontended; contended cost unmeasured. Acceptance: proof of equivalence including routing, nearest-owner revalidation, all writers and lock ordering; a contended benchmark; race evidence; no per-Env lock without that proof.
- *N5:* "Characterize `=:`/closed declarations in maintained-code documentation checker and prelude documentation consumers before first shipped prelude adoption." Acceptance: `tools/code_documentation.py` explicit handling and tests; prelude/doc generator behavior for immutable and closed declarations.

## 5. Closeout checklist

- [ ] Codex maintainability re-review of `6649d0b6` (supersedes FAIL or lists blockers). *Not performed by the implementer.*
- [ ] Independent behavioral and documentation truth audit.
- [ ] Apply sections 3.1-3.8 in separate `distillation(...)` commit(s) after the audit; keep STATE ≤ 43,000 words; reconfirm all root documents say entry-scope-only reservation.
- [ ] Open or attach tracked issues for M4 and M6/N5 (section 4); decide the long-lived tracker for the optional C++ gap.
- [ ] genia-cpp#51 fixed in a separate, independently reviewed C++ change; deterministic paused-action coverage; `r25-cell-nested-send-transaction` returns `[1, 15, true]`; required Docker workflow green at the corrected reviewed head.
- [ ] Final-head CI green: Docs, Code documentation, LLM instructions, Host parity, main CI, Docker. Rerun local non-loopback (0 failed), loopback, shared R16 (901/901 expected), `mkdocs build --strict`, `tools/gen_mcp_language_profile.py --check`, `tools/gen_function_docs.py --check`, ruff and the code-documentation checker at that head.
- [ ] Maintainer merge decision. Keep #1261/#1250 open until then; no Slice C.

## 6. New blockers or risks found

1. **Orphaned follow-ups (closeout blocker):** M4 and M6/N5 have prose owners but no tracking issue; #1261 closing would drop them.
2. **Cannot verify genia-cpp#51 from this session** (repository outside session scope).
3. **D1 misattribution** in the final-authority document (word-neutral fix).
4. **Zero STATE headroom:** the audit cannot add a word without a paired cut.
5. Not a blocker but recorded: Slice B C++ behavior is unrun by the implementer; only the reviewer's 26 UNSUPPORTED observation exists.
