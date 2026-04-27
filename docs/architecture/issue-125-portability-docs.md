# Issue #125 Docs Phase — Require Portability Analysis in Pre-Flight

**Phase:** docs
**Branch:** `issue-125-portability-preflight`
**Issue:** #125 — Require portability analysis in pre-flight for all features
**Scope:** Process/documentation only. No runtime behavior changes.

---

## 1. Scope

Update only docs that need to change per the spec and implementation. Do not touch docs that
describe language behavior, runtime behavior, or host capabilities — none of those changed.

---

## 2. Cross-File Consistency Check

### Core docs — no change required

| File | Status | Reason |
|---|---|---|
| `GENIA_STATE.md` | No change | No language behavior or host capability changed |
| `GENIA_RULES.md` | No change | No semantics, pattern behavior, or evaluation rules changed |
| `README.md` | No change | Already references `docs/process/run-change.md` and `docs/process/llm-prompts.md` as required reading; user-facing behavior unchanged |
| `GENIA_REPL_README.md` | No change | Describes REPL behavior only |
| `AGENTS.md` | No change | Already states Core IR as portability boundary and the one-zone-per-change rule; phase pipeline listing is unchanged; process sub-structure is delegated to `docs/process/` |

### Process docs — already updated by implementation phase

| File | Change | Verified |
|---|---|---|
| `docs/process/00-preflight.md` | Section `3a. PORTABILITY ANALYSIS` inserted between section 3 and section 4 | YES — confirmed at line 121 |
| `docs/process/run-change.md` | Step 2 expanded with portability analysis requirement note | YES — confirmed at lines 7–9 |
| `docs/process/llm-prompts.md` | `## Preflight Phase` section appended with all seven field names and rules | YES — confirmed at line 55 |

### Host-interop and architecture docs — no change required

`docs/host-interop/*` and `docs/architecture/*` describe host contract behavior and Core IR
portability. None of that changed in this issue.

---

## 3. Internal Consistency Verification

### Field names match across all three docs

`docs/process/00-preflight.md` section 3a field labels:

1. `Portability zone:`
2. `Core IR impact:`
3. `Capability categories affected:`
4. `Shared spec impact:`
5. `Python reference host impact:`
6. `Host adapter impact:`
7. `Future host impact:`

`docs/process/llm-prompts.md` Preflight Phase field list: same seven names in the same order. ✓

`docs/process/run-change.md` references "section 3a" — matching the label in `00-preflight.md`. ✓

### Valid-value lists match

`Portability zone` valid values in `00-preflight.md`:
`language contract, Core IR, prelude, Python reference host, host adapter, shared spec, docs/tests only`

`Portability zone` valid values in `llm-prompts.md`:
`language contract, Core IR, prelude, Python reference host, host adapter, shared spec, docs/tests only` ✓

### Section numbering is consistent

Sections 4–10 in `00-preflight.md` are undisturbed. `3a` appears between 3 and 4 as specified. ✓

### No cross-doc references to preflight template structure exist outside the three target files

`grep` for `00-preflight` and `pre-flight template` across `docs/` (excluding issue-125 docs and
the three target files) returned no results. No stale external references to update. ✓

---

## 4. Truthfulness Check

The three updated process docs:

- Do NOT claim future hosts (Node.js, Java, Rust, Go, C++) are implemented — the valid-value
  guidance in `00-preflight.md` and the rules in `llm-prompts.md` explicitly prohibit such claims.
- Do NOT imply that portability analysis is a completed multi-host validation — it is a required
  planning discipline for future changes.
- DO accurately describe the current state: Python is the only implemented host; Core IR is the
  portability boundary; spec categories are parse, ir, eval, cli, flow, error.
- DO use language consistent with `GENIA_STATE.md`: "Python reference host", "planned future hosts",
  "not implemented".

---

## 5. Test Result

```
python -m pytest tests/test_semantic_doc_sync.py -q
52 passed in 0.18s
```

Unchanged from baseline. No regressions introduced by the three process doc edits.

---

## 6. Change Summary

**Files updated by implementation phase (confirmed):**

- `docs/process/00-preflight.md` — +74 lines (section 3a block)
- `docs/process/run-change.md` — +3 lines (step 2 sub-bullets)
- `docs/process/llm-prompts.md` — +24 lines, -1 line (Preflight Phase section)

**Files that required no docs-phase edits:**

- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `README.md`
- `GENIA_REPL_README.md`
- `AGENTS.md`
- All `docs/host-interop/*`
- All `docs/architecture/*` (other than the issue-125 phase docs on this branch)

**No examples added or removed** — this is a process-only change with no user-facing language examples.

---

## 7. Complexity Check

Minimal and clear. Three small additions to three existing process docs. No core language docs
touched. No host-interop docs touched. No examples changed.

---

## 8. Final Check

- All docs match implementation: YES
- `GENIA_STATE.md` is accurate and complete: YES — unchanged; no language behavior changed
- Examples are correct: N/A — no examples added
- No speculative content: YES — all guidance is grounded in current implemented state
- Ready for audit: YES
