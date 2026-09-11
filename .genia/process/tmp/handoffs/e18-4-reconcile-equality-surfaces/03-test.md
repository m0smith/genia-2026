# E18-4 Reconcile Patterns, Assertions, and Equality-like Surfaces — Test Phase

ISSUE: #794
STATUS: failing evidence written and proven failing before implementation

---

## Added evidence

Shared:
- `spec/eval/r18-surface-agreement-across-equality-like-paths.yaml`
- `spec/eval/r18-surface-assert-eq-uses-one-relation.yaml`
- `spec/eval/r18-surface-sheet-column-identity.yaml`
- `spec/error/r18-surface-assert-eq-rejects-cross-kind.yaml`
- `tests/spec/test_r18_surface_reconciliation_shared_specs_794.py`

Focused:
- `tests/unit/test_r18_equality_surface_reconciliation_794.py`

---

## Proof the new cases fail for the intended semantic reason

### Shared specs — 4 failed, 0 passed

The cross-surface agreement case is the important one:

```
expected [[true, false, false], [true, false, false], [true, false, false], [true, false, false], true,  true,  true ]
actual   [[true, false, false], [true, true,  false], [true, true,  false], [true, true,  false], false, false, false]
```

Row 1 is `==`, already correct after #791. Rows 2, 3 and 4 are duplicate
bindings, literal patterns and the meta-evaluator, and each reports the `true`/`1`
pair as equal. The final three booleans — "does this surface's row equal the `==`
row?" — are all `false`, which is the divergence stated as a single fact.

The other three: `assert_eq` on equal byte values raised a failure; the Sheet
with `true` and `1` column names was rejected as having duplicate names; and
`assert_eq(true, 1)` exited 0 instead of failing.

### Focused tests — 9 failed, 15 passed

| Failure | Semantic reason |
|---|---|
| agreement on `true`/`1` and `false`/`0` | duplicate binding and meta-evaluator both use host equality |
| agreement on the map pair | duplicate binding compares maps with host `==`, which is identity |
| literal patterns | a `1` literal matches `true` |
| `assert_eq` | accepts `true`/`1`; rejects equal byte values and equal-content maps |
| meta-evaluator `!=` | disagrees with `!=` |
| Sheet distinct columns | `true` and `1` collide |
| NaN column name | accepted, though a non-reflexive name cannot denote a stable column |
| literal mismatch shape | a `1` literal wrongly matched `true` |

15 tests already pass and are kept as regression protection: `==`/`!=` agreement
itself, composite operands through `==`, Sheet duplicate rejection for genuinely
equal names, the protected column-name rejection message, matcher values compared
without invocation, `assert_eq` not being a protected oracle, and index handles
comparing by identity.

---

## Test-design correction made during this phase

The first draft ran list, Outcome, and map operands through the meta-circular
evaluator. That failed with "metacircular eval does not support expression",
which is an unsupported-syntax error, not an equality divergence — invalid
evidence.

The operand table was therefore split: `SCALAR_OPERAND_PAIRS` covers the forms
the meta-evaluator supports and is run through all four surfaces, while
`COMPOSITE_OPERAND_PAIRS` covers lists, Outcomes, symbols, and maps through `==`,
duplicate bindings, and `!=`. Recorded because the correction is the reason the
remaining failures are all genuine.

---

## Unrelated pre-existing failures

Baseline on `main` @ `925a548`: `-m "not loopback"` 2 failed / 4168 passed,
`-m loopback` 26 passed, shared specs 660/660, `ruff` clean.
