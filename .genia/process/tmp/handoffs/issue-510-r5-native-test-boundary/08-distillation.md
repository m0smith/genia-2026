# === GENIA DISTILLATION ===

CHANGE NAME:
issue #510 r5-native-test-boundary

CHANGE SLUG:
issue-510-r5-native-test-boundary

Issue: #510
Type: contract
Release classification: R5 — Native Test Expansion / Pytest Migration Wave 1
Branch: `contract/issue-510-r5-native-test-boundary`
Handoff directory: `.genia/process/tmp/handoffs/issue-510-r5-native-test-boundary/`

`GENIA_STATE.md` is final authority.

---

## 0. BRANCH CHECK

- Not on `main`: confirmed — `contract/issue-510-r5-native-test-boundary`.
- Matches pre-flight branch: confirmed.
- No merge/rebase/switch.

---

## 1. EXTRACTED DURABLE CONTENT

The only durable, canonical artifact produced by this change is the **native-test / pytest / shared-spec placement boundary**. It is already written, in canonical form, in `GENIA_STATE.md`:

Invariants (durable):
- Native tests complement pytest and shared semantic specs; they do not replace either.
- Genia-native tests are for Genia-facing behavior verifiable in Genia source (Outcome helpers, validation helpers, Flow/Seq visible behavior, Sheet helpers, user-facing examples, prelude/source-level behavior).
- Python pytest is the home for parser, lexer, AST, Core IR, host/runtime internals, host adapter behavior, CLI harness internals, spec runner internals, Python-specific exception/normalization behavior, and native-test stack internals.
- Shared semantic specs remain authoritative for covered portable observable CLI/eval/flow/error/parse/IR behavior and must not be displaced by native tests.

Maturity (durable):
- Experimental, Python reference host.

Tested limitations (durable):
- setup/teardown execution, fixtures, parameterized tests, snapshots, property tests, parallelism, filtering, broad discovery, and multi-host execution are not implemented.

Everything else across the handoffs is phase/process text (planning, branch checks, validation logs, scope-lock restatements) and is intentionally discarded — not migrated into docs.

---

## 2. DESTINATION FOR EACH ITEM

- Placement boundary invariants + maturity + limitations → `GENIA_STATE.md`, section `### Native test / pytest / shared-spec placement boundary (Python reference host, Experimental)` (already present, ~line 2261). No further edit required.
- Wording guardrail → `tests/doc/test_semantic_doc_sync.py::test_native_test_placement_boundary_stays_explicit_in_state` (already present). Durable; keeps the section from drifting.
- No content maps to `GENIA_RULES.md` (no semantics changed), `README.md`, `GENIA_REPL_README.md`, or `docs/design/*`. The roadmap (`docs/strategy/release-roadmap.md` R5) already carries an aligned planning-level description and needs no change.

No new doc categories created.

---

## 3. FILES UPDATED

- None in this phase. Durable content was already canonicalized during IMPLEMENTATION; DISTILLATION confirms it and adds nothing.

---

## 4. CONSISTENCY CHECK

- `GENIA_STATE.md` ↔ `GENIA_RULES.md` ↔ `README.md` ↔ `GENIA_REPL_README.md` ↔ `docs/architecture/*` ↔ `docs/strategy/release-roadmap.md` ↔ examples: aligned (verified in DOC SYNC and AUDIT). No contradictions. No doc implies native tests replace pytest/shared specs or claims unsupported features as implemented.

---

## 5. CLEANUP

Process-artifact containment:
- The handoff directory `.genia/process/tmp/handoffs/issue-510-r5-native-test-boundary/` is matched by `.gitignore` line 83 (`.genia/process/tmp/`) and is currently untracked.
- No change-specific handoff/process content leaked into `docs/`. (A grep of `docs/` for handoff terms matched only the legitimate, durable process templates under `docs/process/*`, e.g. `00-preflight.md`, `05-doc.md`; these are canonical process docs, not change artifacts.)

Handoff directory status:
- **Safe to delete.** All durable content has been extracted/confirmed into `GENIA_STATE.md` and the guardrail test; the handoff files hold only process state.
- Repo-convention caveat: prior changes (e.g. `issue-450-*`, `issue-451-*`, `issue-452-*`) have their handoff files **tracked in git** despite the ignore rule, which means the established convention is to `git add -f` the handoff directory at commit time rather than delete it. Follow whichever the maintainer prefers — both are valid given the above. If retaining, force-add at the commit step; if not, the directory can be removed.
- Handoff files were not migrated into `docs/`.

---

## 6. COMPLEXITY CHECK

- [x] Minimal and clear
- [ ] Slightly expanded but justified
- [ ] Too verbose

Durable content was already in the single authoritative location; distillation is confirmation plus cleanup guidance only.

---

## 7. OUTPUT SUMMARY

1. Extracted durable content: the native-test / pytest / shared-spec placement boundary — invariants, Experimental / Python-reference-host maturity, and the list of unsupported features.
2. Destination: `GENIA_STATE.md` boundary section (already present) + the doc-sync guardrail test (already present).
3. Files updated this phase: none.
4. Handoff directory: safe to delete (or `git add -f` per the existing repo convention for prior issues).
5. Discarded content worth noting: all phase logs, branch checks, validation transcripts, and scope-lock restatements — intentionally not preserved, per distillation rules.

---

## 8. NOTES FOR THE COMMIT STEP (outside distillation scope)

- The change is still uncommitted (`GENIA_STATE.md`, `tests/doc/test_semantic_doc_sync.py`). Per AGENTS.md, commit with phase-appropriate prefixes; the failing-test commit should precede implementation and the implementation commit should reference that SHA.
- A stale `.git/index.lock` is present in this environment and could not be removed by this read-only session (`Operation not permitted`); it may need clearing before the next git write/commit.
- `.claude/settings.local.json` is unrelated local tooling and should not be committed as part of this change.

DISTILLATION complete. End of pipeline (DOC SYNC → AUDIT → DISTILLATION done; no commit performed, per phase rules).
