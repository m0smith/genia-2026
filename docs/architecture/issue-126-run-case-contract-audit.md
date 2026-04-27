# === GENIA AUDIT / TRUTH REVIEW ===

CHANGE NAME: Define minimal host adapter contract (`run_case` interface)

---

## 0. BRANCH CHECK

- Branch: `issue-126-run-case-contract` — NOT `main`. ✓
- Branch name matches change. ✓
- Scope matches branch intent: adapter contract alignment only. ✓
- No unrelated changes included. ✓

### Violations: None

---

## 3. AUDIT SUMMARY

Status: **[x] PASS**

Summary: All six pipeline phases completed correctly. `run_case` accepts `LoadedSpec` and returns `ActualResult` with correct per-category normalization. The executor delegates cleanly. Docs are accurate. 1472/1472 pytest, 138/138 shared spec runner.

---

## 4. SPEC ↔ IMPLEMENTATION CHECK

**Input contract (spec §4):**

| Spec requirement | Implementation | Status |
|-----------------|----------------|--------|
| Accepts `name`, `category`, `source`, `stdin`, `file`, `command`, `argv`, `debug_stdio` | `run_case(spec: LoadedSpec)` — `LoadedSpec` carries all fields | ✓ |
| Must not inspect `expected_*` fields | No `expected_*` access in `adapter.py` | ✓ |
| Must not mutate input | No mutation | ✓ |
| Unsupported category raises immediately | `raise ValueError(f"Unknown spec case category: {spec.category}")` | ✓ |

**Output contract (spec §5.1):**

| Category | Required fields | Actual return | Status |
|----------|----------------|---------------|--------|
| eval, flow, error | `stdout`, `stderr`, `exit_code`, no strip | `ActualResult(stdout=normalize_text(...), ...)` | ✓ |
| cli | `stdout`, `stderr`, `exit_code`, trailing newlines stripped | `ActualResult(stdout=strip_trailing_newlines(normalize_text(...)), ...)` | ✓ |
| ir | `ir` field | `ActualResult(ir=result["ir"])` | ✓ |
| parse | `parse` dict | `ActualResult(parse=result)` | ✓ |

**Normalization rules (spec §5.2):**

| Rule | Implementation | Status |
|------|----------------|--------|
| Line-ending normalization all text fields | `normalize_text` in `normalize.py`: `\r\n→\n`, `\r→\n` | ✓ |
| CLI trailing-newline strip after normalization | `strip_trailing_newlines(normalize_text(...))` — order is correct | ✓ |
| eval/flow/error must NOT strip trailing newlines | Only `normalize_text`, no strip call | ✓ |
| IR normalization owned by `exec_ir` | `exec_ir` result passed through as-is | ✓ |
| Parse normalization owned by parse path | `parse_and_normalize` result passed through as-is | ✓ |

**Error category (spec §5.3):**
Uses `run_eval_subprocess` (eval path). Returns `stdout`, `stderr`, `exit_code` with line-ending normalization only. ✓

**Invariants (spec §6):**

| # | Invariant | Status |
|---|-----------|--------|
| 1 | Adapter does not inspect `expected_*` | ✓ |
| 2 | Adapter does not mutate input | ✓ |
| 3 | Unsupported categories raise immediately | ✓ (raises `ValueError`) |
| 4 | CLI strip occurs after line-ending normalization | ✓ (order verified in code) |
| 5 | IR/parse shapes compatible with `comparator.py` | ✓ (138/138 spec cases pass) |
| 6 | eval/flow/error do not strip trailing newlines | ✓ |
| 7 | Host-specific internals stay internal | ✓ (`SimpleNamespace` for `exec_ir` is internal adapter detail) |

### Mismatches: None

---

## 5. DESIGN ↔ IMPLEMENTATION CHECK

| Design decision | Implementation | Status |
|----------------|----------------|--------|
| Strategy: replace scaffold entirely | `SpecCase` and `SpecResult` removed | ✓ |
| `run_case` accepts `LoadedSpec`, returns `ActualResult` | Signature matches | ✓ |
| `normalize.py`: remove `normalize_result`, `_normalize_value`; add `normalize_text`, `strip_trailing_newlines` | Done | ✓ |
| `executor.py`: `execute_spec` delegates to `run_case` via local import | `from hosts.python.adapter import run_case` inside function body | ✓ |
| `ActualResult` stays in `executor.py` | Still defined there | ✓ |
| `loader.py`, `comparator.py`, `runner.py` not changed | Confirmed by `git diff` | ✓ |
| Circular import resolved with local import | Local import inside `execute_spec` body | ✓ |

**Behavior change vs old executor.py:** The old `executor.py` had an implicit fallthrough — unknown categories silently ran as eval. The new `adapter.py` raises `ValueError` for unknown categories. This is the correct change per spec invariant §6.3 and matches the loader's own category validation.

### Mismatches: None

---

## 6. TEST VALIDITY

**Coverage against spec §9 ("For the test phase"):**

| Spec-required test | Test in `test_adapter_contract.py` | Status |
|--------------------|-----------------------------------|--------|
| eval returns stdout/stderr/exit_code, no strip | `test_run_case_eval_no_trailing_newline_strip`, `test_run_case_eval_fields` | ✓ |
| cli strips trailing newlines | `test_run_case_cli_strips_trailing_newlines` | ✓ |
| ir returns ir field | `test_run_case_ir_provides_ir_field` | ✓ |
| parse returns parse field (kind: ok) | `test_run_case_parse_ok_provides_parse_field` | ✓ |
| parse returns parse field (kind: error) | `test_run_case_parse_error_provides_parse_field` | ✓ |
| error uses eval path, returns stdout/stderr/exit_code | `test_run_case_error_uses_eval_path_no_strip` | ✓ |
| flow returns stdout/stderr/exit_code, no strip | `test_run_case_flow_no_trailing_newline_strip` | ✓ |
| unsupported category raises | `test_run_case_unsupported_category_raises` | ✓ |
| cli CRLF normalized before stripping | `test_run_case_cli_crlf_normalized_then_stripped` | ✓ |

**Return-type tests (ActualResult, not dict):**  Each category has a `test_run_case_<cat>_returns_actual_result` test. ✓

**Spec observable cases (spec §7) coverage:**

All 9 observable cases from the spec have corresponding test coverage. ✓

**Regression coverage:**  
Existing 138 shared spec cases (eval/ir/cli/flow/error/parse) all pass through `execute_spec → run_case`. ✓

**Mock target correctness:**  
Tests patch at `hosts.python.adapter.<function>` — correct for post-implementation. Before implementation, these patches raised `AttributeError` (confirming the tests were genuinely failing). ✓

### Missing / weak tests: None blocking.

### False confidence risks: None. Mocks return realistic shapes; `isinstance(result, ActualResult)` checks prevent dict false-positives.

---

## 7. TRUTHFULNESS REVIEW

**`HOST_INTEROP.md`:**
- No longer claims `run_case(case: SpecCase) -> SpecResult`. ✓
- Documents correct input fields, per-category output fields, normalization rules. ✓
- CLI trailing-newline rule explicitly called out. ✓
- "Unsupported categories raise an error immediately" documented. ✓

**`GENIA_STATE.md`:**
- `hosts/python/` no longer described as "documentation/adaptation scaffold only". ✓
- `run_case` named as canonical wired entrypoint. ✓
- Does not imply multi-host support. ✓

**`tools/spec_runner/README.md`:**
- Notes `execute_spec` delegates to `adapter.py::run_case`. ✓

**Remaining `SpecCase`/`SpecResult` references in repo:**
- `docs/architecture/issue-126-run-case-contract-spec.md` — historical "Scaffold path" description. Correct context, not authoritative. ✓
- `docs/architecture/issue-126-run-case-contract-design.md` — lists what was removed. Correct. ✓
- `docs/architecture/issue-126-run-case-contract-preflight.md` — historical scaffold note. ✓
- `docs/architecture/issue-152-spec-system-doc-sync-design.md` — frozen past design doc quoting old `HOST_INTEROP.md` text. Stale but non-authoritative. Does not affect runtime or tests. ✓

No authoritative doc (`GENIA_STATE.md`, `GENIA_RULES.md`, `README.md`, `GENIA_REPL_README.md`, `HOST_INTEROP.md`) contains stale `SpecCase`/`SpecResult` claims. ✓

### Violations: None

---

## 8. CROSS-FILE CONSISTENCY

| Source | Claim | Aligned | Notes |
|--------|-------|---------|-------|
| `HOST_INTEROP.md` | `run_case(spec: LoadedSpec) -> ActualResult` | ✓ | Matches implementation |
| `HOST_INTEROP.md` | CLI strips trailing newlines; eval/flow/error do not | ✓ | Matches `adapter.py` |
| `GENIA_STATE.md` | `hosts/python/adapter.py::run_case` is canonical entrypoint | ✓ | Matches implementation |
| `GENIA_STATE.md` | No generic multi-host runner | ✓ | Unchanged, still true |
| `spec_runner/README.md` | `execute_spec` delegates to `adapter.py::run_case` | ✓ | Matches `executor.py` |
| `GENIA_RULES.md` | No changes needed | ✓ | No adapter contract rules in rules doc |
| `README.md` | No changes needed | ✓ | No `SpecCase`/`SpecResult` references |

### Drift detected: None

Risk level: **[x] Low**

---

## 9. PHILOSOPHY CHECK

- Preserve minimalism? **YES** — thin wrapper in `executor.py`; dispatch logic consolidated in one place.
- Avoid hidden behavior? **YES** — normalization rules explicit; unknown categories raise immediately.
- Keep semantics out of host? **YES** — adapter normalizes and dispatches; does not define language semantics.
- Align with pattern-matching-first? **YES (N/A)** — not a language behavior change.

### Violations: None

---

## 10. COMPLEXITY AUDIT

**[x] Minimal and necessary**

### Justification:
- `adapter.py` is now 52 lines vs 69 before. Simpler.
- `normalize.py` is 11 lines vs 30 before. Simpler.
- `executor.py` is 19 lines vs 62 before. Simpler.
- No new abstractions. No feature creep. Scope held exactly.

### Anything removable: Nothing.

---

## 11. ISSUE LIST

No critical, major, or blocking issues found.

**Minor (non-blocking):**
- `docs/architecture/issue-152-spec-system-doc-sync-design.md` contains a frozen historical quote of the old `HOST_INTEROP.md` `run_case(case: SpecCase) -> SpecResult` text. This is a past-issue pipeline artifact, frozen in time. Not authoritative, not read by tests, does not affect runtime. No fix required.

---

## 12. RECOMMENDED FIXES (ORDERED)

None required. All issues are non-blocking.

---

## 14. VALIDATION

**Tests executed:**
```
pytest: 1472 passed in 125.97s
```

**Spec runner:**
```
Summary: total=138 passed=138 failed=0 invalid=0
```

**Import chain verified:**
```
imports OK
run_case params: ['spec']
run_case return annotation: <class 'tools.spec_runner.executor.ActualResult'>
```

**Unknown category raises:**
```
OK: raises ValueError: Unknown spec case category: unknown
```

**Stale symbol scan:**  
No `SpecCase`, `SpecResult`, or `normalize_result` references in any authoritative doc or active source file.

---

## FINAL VERDICT

**Ready to merge? YES**

- No blocking issues.
- All tests pass.
- All spec cases pass.
- Docs aligned with implementation.
- Scope held exactly.
