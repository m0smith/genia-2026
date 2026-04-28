# Audit: Prelude-safe callback invocation — `apply_raw`

Issue: #188
Phase: audit
Branch: issue-188-raw-callback-invocation-audit
Date: 2026-04-28

Preflight: `docs/architecture/issue-188-callbacks-preflight.md`
Spec: `docs/architecture/issue-188-callbacks-spec.md`
Design: `docs/architecture/issue-188-callbacks-design.md`

---

## 0. BRANCH CHECK

- Work was NOT done on `main` ✓
- Branches:
  - `issue-188-raw-callback-invocation-preflight` — preflight doc
  - `issue-188-raw-callback-invocation-spec` — spec + YAML cases + spec/eval/README.md
  - `issue-188-raw-callback-invocation-design` — design doc
  - `issue-188-raw-callback-invocation-test` — test file
  - `issue-188-raw-callback-invocation-impl` — implementation
  - `issue-188-raw-callback-invocation-docs` — doc sync
  - `issue-188-raw-callback-invocation-audit` — this phase
- Scope matches branch intent ✓
- No unrelated changes included ✓

---

## 3. AUDIT SUMMARY

Status: **PASS**

Summary: `apply_raw` is implemented exactly as specified. Two additions to `interpreter.py` — `apply_raw_fn` and `env.set("apply_raw", apply_raw_fn)` — expose the pre-existing `skip_none_propagation=True` mechanism under a clean public name. All 32 unit tests pass, all 144 spec runner cases pass (including 6 apply_raw-specific YAML cases), normal call semantics are unchanged, and documentation is truthful and internally consistent.

---

## 4. SPEC ↔ IMPLEMENTATION CHECK

| Spec invariant | Verified |
|---|---|
| ordinary-value-equivalence: `apply_raw(f, [x])` == `f(x)` when no none | ✓ (`test_named_function`, `test_lambda`, `test_multi_arg`) |
| raw-invocation: body executes with none arg | ✓ (`test_lambda_with_unwrap_or`, `test_multi_arg_none_in_second_position`) |
| no-implicit-coercion: identity returns none unchanged | ✓ (`test_identity_lambda_returns_none_unchanged`) |
| return-value-as-is: no re-wrapping | ✓ (`test_returns_plain_value_unchanged`) |
| exception-propagation: body errors surface | ✓ (`test_arity_mismatch_raises`, `test_undefined_name_inside_body_propagates`) |
| args-not-list → TypeError with correct message | ✓ (`test_string_as_args_raises_type_error`, message includes "received string") |
| proc-not-callable → dispatch error | ✓ (`test_int_proc_raises`) |
| zero-arg via empty list | ✓ (`test_zero_arg_lambda`, `test_zero_arg_named`) |
| normal-call-unchanged (regression) | ✓ (all `TestNormalCallUnchangedRegression` cases) |

## Mismatches: None

---

## 5. DESIGN ↔ IMPLEMENTATION CHECK

| Design requirement | Verified |
|---|---|
| `apply_raw_fn` defined inside `setup_env()` after `_invoke_raw_from_builtin` | ✓ (lines 6908–6919) |
| `env.set("apply_raw", apply_raw_fn)` registered | ✓ (line 7779) |
| Uses `Evaluator(env, env.debug_hooks, env.debug_mode).invoke_callable(...)` | ✓ |
| `skip_none_propagation=True` passed | ✓ |
| `tail_position=False`, `callee_node=None` | ✓ |
| `_runtime_type_name(args)` used in TypeError message | ✓ |
| Not added to `_NONE_AWARE_PUBLIC_FUNCTIONS` | ✓ |
| `_invoke_raw_from_builtin` unchanged | ✓ |
| No new IR nodes, no parser changes | ✓ |
| No changes to normal call semantics | ✓ |

## Mismatches: None

---

## 6. TEST VALIDITY

32 tests in 8 groups cover:

- Core behavior: ordinary args, named fn, lambda, multi-arg, string arg, list arg
- Zero-arg invocation: empty list
- None-arg body-execution: none in first, second, both positions; identity; `some?` predicate
- No implicit coercion: none reason preserved, some preserved, plain value unchanged
- Exception propagation: arity mismatch, undefined name
- args-not-list TypeError: string, int, bool, map; message content
- proc-not-callable: int, string
- Regression: normal call short-circuit unchanged for lambda, named fn, reduce, map, filter, none-aware builtins

All 32 pass. All assertions are specific (exact values, exact exception types and message patterns). No vague `assert True` or swallowed-error patterns.

## Missing / weak tests: None

## False confidence risks:

- `test_arity_mismatch_raises` uses a broad regex `[Nn]o.*match|[Uu]nmatched|[Dd]ispatch|[Aa]rity` — acceptable because the dispatch error format is internal and may vary across evolution; the test correctly asserts an exception is raised without overconstrained message matching.

---

## 7. TRUTHFULNESS REVIEW

Checked:

- **GENIA_STATE.md**: `apply_raw` listed under fn group with accurate description (language-contract, list required, registered directly). ✓
- **GENIA_RULES.md §9.6.4.1**: All behavioral claims are accurate against the implementation. The note that `apply_raw(f, none("x"))` short-circuits before `apply_raw` runs is correct (not in `_NONE_AWARE_PUBLIC_FUNCTIONS`). ✓
- **GENIA_REPL_README.md**: One-line entry under builtins is accurate. ✓
- **README.md**: Entry matches actual behavior. ✓
- **docs/host-interop/capabilities.md**: `fn.apply-raw` entry accurately documents name, surface, input/output, errors (including the three categories: non-list args, non-callable proc, body errors), portability as `language contract`. ✓

## Violations: None

---

## 8. CROSS-FILE CONSISTENCY

| Document | Consistent with implementation |
|---|---|
| GENIA_STATE.md | ✓ |
| GENIA_RULES.md | ✓ |
| GENIA_REPL_README.md | ✓ |
| README.md | ✓ |
| docs/host-interop/capabilities.md | ✓ |
| spec/eval/apply-raw-*.yaml (6 files) | ✓ — all pass spec runner |
| HOST_CAPABILITY_MATRIX.md | Not updated — correct; matrix tracks capability groups, not individual primitives; `apply_raw` is captured in `capabilities.md` which is the authoritative per-capability reference |

## Drift detected: None

Risk level: **Low**

---

## 9. PHILOSOPHY CHECK

- Preserves minimalism? **YES** — two lines of code, no new IR nodes, no parser changes
- Avoids hidden behavior? **YES** — `apply_raw` documents the bypass explicitly; normal calls unchanged
- Keeps semantics out of host? **YES** — mechanism (`skip_none_propagation`) pre-existed; this is public exposure only
- Aligns with pattern-matching-first? **YES** — no pattern machinery touched

## Violations: None

---

## 10. COMPLEXITY AUDIT

**Minimal and necessary**

`apply_raw_fn` is 8 lines: 1 guard + 7 for the `invoke_callable` call. All real logic pre-existed in `invoke_callable`. This change makes the pre-existing private mechanism publicly accessible without duplication.

## Anything removable: No

---

## 11. ISSUE LIST

None.

---

## 12. RECOMMENDED FIXES

None required. Potential future follow-up (not blocking):

1. Prelude extraction: rewrite `reduce`/`map`/`filter` in pure Genia using `apply_raw` (blocked on #188 landing — now unblocked). Tracked as a separate issue.
2. Docstring for `apply_raw` via prelude (optional, for `help("apply_raw")` teaching output).

---

## 14. VALIDATION

Evidence:

- `python -m pytest tests/test_apply_raw.py -v` → **32 passed, 0 failed** (all 32 test cases verified individually)
- `python -m tools.spec_runner` → **Summary: total=144 passed=144 failed=0 invalid=0** (includes 6 apply_raw YAML cases)
- `python -m pytest tests/ -q` → **full suite, exit code 0** (no regressions)
- Error message verified live: `apply_raw((x) -> x, "bad")` → `'apply_raw expected a list as second argument, received string'` ✓
- Error message verified live: `apply_raw((x) -> x, 99)` → `'apply_raw expected a list as second argument, received int'` ✓

---

## FINAL VERDICT

**Ready to merge: YES**

All invariants verified. No blocking issues. Cross-file consistency confirmed. No scope expansion. Two additions to one file; all behavior correct.
