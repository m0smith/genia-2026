# E18-3 Identity, Opaque Token, and Protected Equality — Test Phase

ISSUE: #793
STATUS: failing evidence written and proven failing before implementation

---

## Added evidence

Shared, host-neutral:

- `spec/eval/r18-protected-equality-is-carrier-identity.yaml`
- `spec/eval/r18-protected-non-interference-through-containers.yaml`
- `spec/eval/r18-identity-bearing-equality.yaml`
- `tests/spec/test_r18_identity_protected_shared_specs_793.py`

Focused:

- `tests/unit/test_r18_identity_token_protected_793.py`

Opaque semantic tokens get **no** shared spec by design: R18 exposes no way to
mint or observe a token from Genia source, so shared cases would have to invent
the public surface this release explicitly excludes. The family is covered by
focused tests against the internal adapter instead.

---

## Proof the new cases fail for the intended semantic reason

### Shared specs — 2 failed, 1 passed

`r18-protected-equality-is-carrier-identity`
expected `[true, true, false, false, false, false, true, true]`,
actual `[true, true, true, true, false, false, false, true]`.
Two independently acquired carriers holding the same secret compared **equal**,
and `!=` agreed.

`r18-protected-non-interference-through-containers`
expected all `false` except the identity case,
actual `[true, false, true, false, true, false, true, false, true, true]`.

That alternating pattern is the finding: the cases alternate equal-payload,
different-payload, at every nesting — bare List, Outcome, `err` context, map
value, nested List — and the result alternates with them. Ordinary structural
recursion reached the carrier and compared payloads at **every** level.

`r18-identity-bearing-equality` passes before implementation and is kept as
portable conformance evidence. Refs and lambdas are plain host classes, so this
host already compares them by identity; a host whose runtime values carry
structural equality would fail it.

### Focused tests — 31 failed, 25 passed

Failure groups and their semantic reasons:

| Group | Reason |
|---|---|
| `test_equality_cannot_distinguish_equal_from_different_payloads` (all 10 wrappers) | payload comparison leaks through every container shape |
| `test_inequality_cannot_distinguish_...` (all 10) | `!=` inherits the same leak |
| `test_independently_acquired_carriers_with_equal_payloads_are_unequal` | carriers compare by payload, not identity |
| `test_host_equality_on_the_carrier_type_is_not_a_payload_oracle` | `GeniaProtected.__eq__` compares the payload directly |
| `test_protected_oracle_is_closed_from_ordinary_source` | end-to-end oracle reachable from real source |
| `test_modules_compare_by_identity_...`, `test_python_handles_...`, `test_named_patterns_...` | host dataclass equality compares fields, including a module's whole export table |
| all token tests | the opaque-token family has no implementation at all |
| `test_the_relation_has_no_transitional_branch_left` | the E18-1 scaffold is still present |

25 tests already pass: carrier self-equality, carrier-vs-payload inequality,
unhashability, rendering non-disclosure (already guaranteed by R10/R14 work),
Ref/Cell identity, and callable identity. These are kept so the implementation
cannot regress guarantees that already hold.

---

## Test design note

The adversarial pattern used throughout is to build one carrier pair with
**equal** payloads and one with **different** payloads, then require every
observable to answer identically for both. This is stronger than asserting a
particular return value: an observable that returns `false` for both is correct,
while one that can tell the pairs apart is an oracle even if each individual
answer looks reasonable.

---

## Unrelated pre-existing failures

Baseline on `main` @ `7552a98`: `-m "not loopback"` 2 failed / 4108 passed (the
root/`chmod 000` native-test-runner cases), `-m loopback` 26 passed, shared
specs 657/657.
