# E18-1 Structural and Exact Numeric Equality — Test Phase

ISSUE: #791
STATUS: failing tests/specs written and proven failing before implementation

---

## Added evidence

Shared, host-neutral (portable evidence a future host consumes):

- `spec/eval/r18-equality-boolean-number-separation.yaml`
- `spec/eval/r18-equality-exact-int-float-bridge.yaml`
- `spec/eval/r18-equality-signed-zero-and-infinities.yaml`
- `spec/eval/r18-equality-nan-non-reflexive.yaml`
- `spec/eval/r18-equality-kind-separation.yaml`
- `spec/eval/r18-equality-structural-contents.yaml`
- `spec/eval/r18-equality-inequality-is-negation.yaml`
- `tests/spec/test_r18_equality_shared_specs_791.py` (runner wiring)

Focused, host-local (kinds awkward to build from source, plus relation properties):

- `tests/unit/test_r18_structural_numeric_equality_791.py`

---

## Proof that the new cases fail for the intended semantic reason

### Shared specs

`uv run pytest -q tests/spec/test_r18_equality_shared_specs_791.py`
→ **4 failed, 4 passed**

Failing, each with the exact contradiction named:

| Spec | Expected | Actual (pre-implementation) | Semantic reason |
|---|---|---|---|
| `boolean-number-separation` | `[false, false, false, false, true, true, false]` | `[true, true, true, true, true, true, false]` | host treats booleans as a numeric subtype |
| `nan-non-reflexive` | `[false, …, false, true]` | `[false, false, false, true, true, true, true, true]` | host container comparison tests element identity before element equality, so a NaN-bearing value compares equal to itself |
| `structural-contents` | `[true, false, true, true, true, false, true, true]` | `[false, false, false, false, true, false, true, true]` | byte values have no host equality, so equal byte values compare by allocation identity |
| `inequality-is-negation` | `[true, true, false, true, true, true, true, false, true]` | `[false, false, false, true, true, true, false, true, true]` | `!=` inherits the same host defects as `==` |

Passing before implementation (kept deliberately as portable conformance
evidence, not as failing evidence): `exact-int-float-bridge`,
`signed-zero-and-infinities`, `kind-separation`. The Python reference host
already agrees with the contract on these, but a naive future host would not —
for example a host that decides the int/float bridge by converting an
arbitrary-precision integer to a float would fail `exact-int-float-bridge`. They
are recorded here so the audit does not mistake them for untested claims.

### Focused unit tests

`uv run pytest -q tests/unit/test_r18_structural_numeric_equality_791.py`
→ **collection error**: `ModuleNotFoundError: No module named 'genia.equality'`.

A bare collection error is weak evidence on its own, so the semantic
contradiction was measured directly against the relation in force today
(host equality, which is what the evaluator currently returns):

```
MISMATCH  true == 1                        host=True   contract=False
MISMATCH  false == 0                       host=True   contract=False
MISMATCH  true == 1.0                      host=True   contract=False
MISMATCH  [nan] == [nan]                   host=True   contract=False
MISMATCH  some(nan) == some(nan)           host=True   contract=False
MISMATCH  bytes hi == bytes hi             host=False  contract=True
MISMATCH  zip entry == zip entry           host=False  contract=True
MISMATCH  format == format                 host=False  contract=True
MISMATCH  [True] == [1]                    host=True   contract=False
ok        sheet == sheet(int/float)        host=True   contract=True

9 of 10 contract cases contradicted by the current host relation
```

So the unit-level assertions fail for genuine semantic reasons, not merely
because a module is missing.

---

## Unrelated pre-existing failures

The `main` baseline at `5c00e76` is **2 failed, 3997 passed** for
`-m "not loopback"` and **26 passed** for `-m loopback`. Both failures are
`tests/unit/test_native_test_runner.py` unreadable-file cases that fail because
this environment runs as root, so `chmod 000` does not restrict access. They are
not caused by this branch and are not treated as this issue's evidence.

---

## Not yet covered here (by design)

Map equality (#792), identity/opaque-token/protected families (#793),
`assert_eq`/literal-pattern/duplicate-binding reconciliation (#794), and
multi-host conformance hardening (#795) are out of this slice's scope. The
transitional branches for those families preserve today's behavior, so no
existing test for them should change in this issue.
