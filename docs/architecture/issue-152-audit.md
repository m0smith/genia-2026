# Issue #152 — Spec-System Doc Sync: Audit

**Phase:** audit
**Branch:** issue-152-spec-system-doc-sync
**Issue:** #152 — Subtask for #116: Sync spec-system documentation with current shared spec reality

---

## Verification Checklist

| Check | Result |
|---|---|
| `uv run pytest tests/test_semantic_doc_sync.py` — all 48 tests pass | PASS |
| `uv run pytest -q --maxfail=5` — full suite | PASS (1398 passed) |
| `uv run python -m tools.spec_runner` | PASS (91 passed) |
| `grep "does not yet execute parse" GENIA_STATE.md` — no output | PASS |
| `grep "does not yet provide implemented shared case coverage for parse" HOST_INTEROP.md` — no output | PASS |
| `grep "only the eval category is active" quick-reference.md unix-power-mode.md` — no output | PASS |
| `head -3 docs/architecture/spec-phase-1-design.md` — shows SUPERSEDED | PASS |
| `spec/errors/README.md` scaffold-only label intact | PASS |
| `spec/flows/README.md` scaffold-only label intact | PASS |
| `spec/parser/README.md` scaffold-only label intact | PASS |
| `spec/pattern/README.md` scaffold-only label intact | PASS |

---

## Drift Items Resolved

| # | File | Stale claim | Resolution |
|---|---|---|---|
| 1 | `GENIA_STATE.md` lines 173–174 | Omitted `spec/parse/`; falsely claimed runner does not yet execute parse | Replaced: added `spec/parse/` to directory list; replaced false denial with accurate initial-coverage qualifier |
| 2 | `docs/host-interop/HOST_INTEROP.md` line 102 | "This runner does not yet provide implemented shared case coverage for parse" | Replaced: added parse to runner description, comparison-fields list (`parse: normalized AST …`), and execution note |
| 3 | `docs/cheatsheet/quick-reference.md` line 1 | "only the eval category is active … other categories are scaffold-only" | Replaced: six-category header listing eval, ir, cli, flow, error, parse |
| 4 | `docs/cheatsheet/unix-power-mode.md` line 1 | Same as #3 | Same replacement |
| 5 | `docs/architecture/spec-phase-1-design.md` | Design artifact using `spec/errors/`, `spec/flows/`, `spec/parser/`; marked IR/parse/flow/runner as Phase 2+ | Prepended SUPERSEDED notice; body preserved as historical record |

---

## Scope Invariants Confirmed

- No runtime behavior was changed.
- No spec case files were added, removed, or modified.
- No new language semantics were introduced.
- `GENIA_STATE.md` §0 authoritative sections (lines 18–19, 54–55, 64–65, 154) were not touched.
- Scaffold-only directories (`spec/errors/`, `spec/flows/`, `spec/parser/`, `spec/pattern/`) remain correctly labeled and unchanged.
- `docs/contract/semantic_facts.json` unchanged — no new semantic facts required.
- CI workflow unchanged.

---

## Commit Trail

| Commit | Phase | Description |
|---|---|---|
| preflight | preflight | Pre-flight analysis and branch creation |
| `9c92a9a` | spec | Spec document — exact required/forbidden phrases and guard assertion wording |
| `cfbddbc` | design | Design document — exact replacement text for each file |
| `11f9b61` | test | Failing guard assertions added to `tests/test_semantic_doc_sync.py` |
| `4959fb4` | docs | Five documentation corrections applied; orphaned assertion restored |

---

## No-Delta Confirmation

No unresolved drift items remain for this issue. All five stale claims are corrected, all five guards pass, and no new stale language was introduced by the corrections.

**GENIA_STATE.md is the final authority for implemented behavior. All other docs/specs must align with this contract.**
