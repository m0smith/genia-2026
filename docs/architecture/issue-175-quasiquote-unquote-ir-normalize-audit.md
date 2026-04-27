# Audit: issue #175 — Fix quasiquote+unquote normalization in spec/ir shared runner

**Date:** 2026-04-26
**Branch:** `issue-175-quasiquote-unquote-ir-normalize`
**Verdict:** PASS

## Scope

Issue #175: `_normalize_quoted_syntax` in `hosts/python/ir_normalize.py` did not handle
`Unquote` or `UnquoteSplicing` parser AST nodes inside quasiquote bodies, causing a `TypeError`
crash when normalizing any `spec/ir` case containing `quasiquote([..., unquote(x)])`.

---

## Checklist

### Tests

| Test | Result |
|---|---|
| `test_ir_spec_fixture[quasiquote-unquote-var.yaml]` | PASS |
| `test_ir_spec_fixture[quasiquote-unquote-splicing-var.yaml]` | PASS |
| `test_discover_specs_includes_ir_cases` (includes new names) | PASS |
| All `test_ir_spec_fixture` cases (7 total) | PASS |
| `tests/test_quasiquote.py` (13 eval tests) | PASS |
| Full suite | **1460 / 1460 PASS** |

### Spec cases

| Case | Before fix | After fix |
|---|---|---|
| `quasiquote-unquote-var.yaml` | FAIL (`TypeError: unsupported quoted syntax Unquote`) | PASS |
| `quasiquote-unquote-splicing-var.yaml` | FAIL (`TypeError: unsupported quoted syntax UnquoteSplicing`) | PASS |
| All 20 pre-existing `spec/ir/` cases | PASS (no regression) | PASS |

### Implementation scope

| Check | Result |
|---|---|
| Only `hosts/python/ir_normalize.py` changed in production code | PASS |
| `src/genia/interpreter.py` untouched (evaluator, parser AST, lowering unchanged) | PASS |
| No new IR node types introduced | PASS |
| No new parser AST types introduced | PASS |
| No new language syntax | PASS |
| No evaluator behavior change | PASS |
| Change is exactly 2 import names + 2 × 4-line branches (12 lines) | PASS |
| `_normalize_ir_node` for top-level `IrUnquote`/`IrUnquoteSplicing` unchanged | PASS |
| Inner `expr` recurses via `_normalize_quoted_syntax` (not `_normalize_ir_node`) | PASS |

### Documentation

| Check | Result |
|---|---|
| `Known Normalization Limitations` section removed from `core-ir-portability.md` | PASS |
| No stale limitation text remains in `core-ir-portability.md` | PASS |
| `GENIA_STATE.md` IR stability bullet updated to include quasiquote+unquote coverage | PASS |
| No stale limitation text found in `docs/design/` or other docs | PASS |

### Phase discipline

| Phase | Commit | Check |
|---|---|---|
| spec | `b12e0aa` | Spec doc only; no YAML, no code |
| design | `0c35956` | Design doc only; no YAML, no code |
| test | `36e9003` | YAML + test registration only; failing before impl |
| implementation | `9d8c6c9` | Code only; references failing-test commit `36e9003` |
| docs | `bec4510` | Docs only; no code change |

---

## Notes

- The limitation was already documented in `core-ir-portability.md` before this issue. This fix
  closes the gap and removes the documentation of it.
- `tests/test_quasiquote.py` eval tests were unaffected throughout: the fix is in the IR
  normalizer path, not the evaluator.
- The inner `expr` of `Unquote`/`UnquoteSplicing` is still parser AST inside a quasiquote body,
  so recursion correctly stays within `_normalize_quoted_syntax`. This invariant is confirmed by
  the passing spec cases and is documented in the design doc.
- Compound inner expressions (e.g., `unquote(x + 1)`) remain out of scope and would still raise
  the existing `TypeError` fallback. That gap is separate and not part of this issue.
