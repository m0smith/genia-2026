# Issue #127 Audit — Create template repo for new Genia hosts

**Phase:** audit
**Branch:** `issue-127-host-template`
**Issue:** #127 — Create template repo for new Genia hosts
**Failing-test commit:** `dd2ce42`
**Implementation commit:** `0d6deb9`

---

## 0. Branch Check

- Work done on `issue-127-host-template`, NOT on `main` ✓
- Branch name matches pre-flight ✓
- All 5 phase commits are correctly prefixed: `spec`, `design`, `test`, `feat`, `docs` ✓
- No unrelated files changed ✓

**Violations:** None.

---

## 3. Audit Summary

**Status: PASS WITH ISSUES**

Implementation is correct and complete. All 43 structural invariant tests pass. Full suite (1542 tests) passes. Shared spec runner (138 cases) passes. One minor process gap: the preflight document was delivered as conversation output but not committed to the repo. Fixed in this audit commit.

---

## 4. Spec ↔ Implementation Check

### §4.1 `hosts/template/AGENTS.md`

| Requirement | Status |
|---|---|
| Contains `scaffolded, not implemented` | ✓ (inv 1) |
| Contains required reading list | ✓ |
| States directory is a template | ✓ ("This directory is a template") |
| References `HOST_PORTING_GUIDE.md` | ✓ |
| Contains no runtime code | ✓ |

### §4.2 `hosts/template/README.md`

| Requirement | Status |
|---|---|
| Contains `scaffolded, not implemented` | ✓ (inv 2) |
| All 10 required section headings present | ✓ (parametrized tests) |
| References `HOST_PORTING_GUIDE.md` | ✓ (inv 3) |
| References `HOST_CAPABILITY_MATRIX.md` | ✓ (inv 4) |
| No capability claimed as Implemented | ✓ |

Note: spec lists 11 required headings (including `# <Host Name> Host`) but the test suite covers the 10 `##`-level section headings. The top-level heading is present in the file. Non-blocking.

### §4.3 `hosts/template/CAPABILITY_STATUS.md`

| Requirement | Status |
|---|---|
| References `capabilities.md` | ✓ (inv 6) |
| No plain `Implemented` status | ✓ (inv 5) |
| No invented names | ✓ (inv 7) |
| Complete: all 29 registry names present | ✓ (verified by audit script: 29/29 match) |
| Footer present | ✓ |

### §4.4 `hosts/template/adapter_stub.md`

| Requirement | Status |
|---|---|
| Contains `run_case` | ✓ (inv 8) |
| References `HOST_INTEROP.md` | ✓ (inv 9) |
| Documents LoadedSpec input fields | ✓ (all 7 fields present) |
| Documents ActualResult output fields | ✓ (stdout, stderr, exit_code) |
| TODO stubs for all 6 categories | ✓ (parametrized tests) |
| References `tools/spec_runner/executor.py::execute_spec` | ✓ |

### §4.5 `hosts/template/ci_stub.md`

| Requirement | Status |
|---|---|
| Notes CI is host-language-specific | ✓ |
| Required shared spec runner job | ✓ (`python -m tools.spec_runner`) |
| Required host-local test job | ✓ |
| TODO for setup steps | ✓ |
| References `HOST_PORTING_GUIDE.md §Test Checklist` | ✓ |
| No working GitHub Actions YAML | ✓ (markdown only) |

### §4.6 `hosts/template/EXAMPLE.md`

| Requirement | Status |
|---|---|
| All 7 step headings present | ✓ (parametrized tests) |
| References `HOST_PORTING_GUIDE.md` | ✓ (inv 10) |
| References `HOST_CAPABILITY_MATRIX.md` | ✓ (inv 10) |
| Closing note re: `GENIA_STATE.md` | ✓ |
| No invented language features | ✓ |

### §2 Pointer requirements

| Requirement | Status |
|---|---|
| `HOST_PORTING_GUIDE.md` references `hosts/template/` | ✓ (inv 11) |
| All 5 planned-host READMEs reference `hosts/template/` | ✓ (inv 12) |
| `HOST_CAPABILITY_MATRIX.md` has no Template row | ✓ (inv 13) |
| `GENIA_STATE.md` unchanged | ✓ (inv 14) |
| `hosts/README.md` Target Layout updated | ✓ (docs phase) |

**Mismatches:** None.

---

## 5. Design ↔ Implementation Check

| Design item | Status |
|---|---|
| 6 new template files created | ✓ |
| 1 new test file created | ✓ |
| `HOST_PORTING_GUIDE.md` pointer added | ✓ |
| 5 planned-host README pointers added | ✓ |
| `hosts/README.md` updated | ✓ (docs phase) |
| No changes to `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md` | ✓ |
| No changes to `spec/`, `src/genia/`, `tools/`, `hosts/python/` | ✓ |
| Tests use `pathlib.Path` only, no Genia runtime imports | ✓ |
| Capability names sourced dynamically from `capabilities.md` in test | ✓ |
| Implementation order: tests first (failing), then files, then pointers | ✓ |

**Mismatches:** None.

---

## 6. Test Validity

### Coverage against spec invariants

All 14 spec §5 invariants are covered by named tests. ✓

### Additional regression tests

- 10 parametrized README heading checks ✓
- 1 `CAPABILITY_STATUS.md` footer check ✓
- 6 parametrized adapter_stub category checks ✓
- 7 parametrized EXAMPLE.md step checks ✓
- 5 parametrized planned-host README pointer checks ✓

### Completeness gap (non-blocking)

The test `test_capability_status_no_invented_names` verifies no invented names but does **not** verify completeness (that all 29 registry names are present in the status file). The audit script confirms completeness: 29/29 match. This is acceptable — the invariant as written in spec §5 is "no invented names," not "all names present." A future host implementer could add a new registry name without the test catching its absence in existing templates. This is a documentation/tooling concern, not a correctness failure today.

### False confidence risks

None identified. All tests assert concrete string content, not vague success. Tests would fail on regression.

---

## 7. Truthfulness Review

- All template files carry `scaffolded, not implemented` status ✓
- No capability claimed as Implemented ✓
- `CAPABILITY_STATUS.md` footer explicitly warns against premature Implemented labels ✓
- `EXAMPLE.md` closing note states not to update `GENIA_STATE.md` unless shared behavior changes ✓
- `adapter_stub.md` points to the reference implementation in `hosts/python/` for comparison ✓
- No examples purport to be runnable code (all stubs are in Markdown prose, not fenced Genia blocks) ✓
- `hosts/README.md` Target Layout note correctly labels the template as "not a host itself" ✓

**Violations:** None.

---

## 8. Cross-File Consistency

| File | State |
|---|---|
| `GENIA_STATE.md` | Unchanged; anchor string present ✓ |
| `GENIA_RULES.md` | Unchanged ✓ |
| `GENIA_REPL_README.md` | Unchanged ✓ |
| `README.md` | Unchanged ✓ |
| `HOST_CAPABILITY_MATRIX.md` | Unchanged; no Template row ✓ |
| `HOST_PORTING_GUIDE.md` | Pointer added only ✓ |
| `hosts/README.md` | Target Layout updated; Host Status table unchanged ✓ |
| `hosts/{node,go,java,rust,cpp}/README.md` | Pointer section added only ✓ |
| `spec/manifest.json` | Unchanged ✓ |

**Drift detected:** None.
**Risk level:** Low.

---

## 9. Philosophy Check

- Preserves minimalism: **YES** — 6 Markdown files, 6 pointer edits, 1 test file; no runtime code
- Avoids hidden behavior: **YES** — all scaffold; nothing executes
- Keeps semantics out of host: **YES** — no language semantics involved
- Aligns with pattern-matching-first: **N/A** — infrastructure change, not a language feature

**Violations:** None.

---

## 10. Complexity Audit

**[x] Minimal and necessary**

6 Markdown files map directly to the 6 deliverables listed in the issue. The test file covers exactly the spec invariants, no more. Pointer edits are the minimum required to make the template discoverable from existing docs.

**Anything removable:** No. Each file serves a distinct purpose specified by the issue.

---

## 11. Issue List

### Minor — No committed preflight document

- **Severity:** Minor
- **File:** `docs/architecture/` (missing `issue-127-host-template-preflight.md`)
- **Problem:** The preflight was delivered as conversation output following the established pattern from issues #125, #126, etc., but was not committed to the repo. Other issues have a `docs/architecture/issue-NNN-*-preflight.md` file.
- **Why it matters:** Breaks the paper-trail pattern; future auditors cannot find the preflight reasoning in the repo.
- **Minimal fix:** Commit `docs/architecture/issue-127-host-template-preflight.md` in this audit commit.
- **Status:** Fixed in this audit commit. ✓

---

## 12. Recommended Fixes (Ordered)

1. ~~Commit missing preflight document~~ — **Done in this audit commit.**

No further fixes required.

---

## 14. Validation Evidence

```
tests/test_host_template_structure.py    43 passed
tests/test_portability_contract_sync.py  8 passed
tests/test_host_boundary_labels.py      20 passed
tests/test_semantic_doc_sync.py         64 passed
Full pytest suite                     1542 passed
python -m tools.spec_runner              138 passed / 0 failed
```

Capability completeness check (audit script):
```
capabilities.md names:        29
CAPABILITY_STATUS.md rows:    29
Missing from status:          none
Invented (not in registry):   none
```

---

## Final Verdict

**Ready to merge: YES**

All spec invariants implemented and tested. No runtime behavior changed. No language semantics affected. No truth-hierarchy docs falsely updated. One minor process gap (missing preflight doc) fixed in this commit. Full suite and shared spec runner clean.
