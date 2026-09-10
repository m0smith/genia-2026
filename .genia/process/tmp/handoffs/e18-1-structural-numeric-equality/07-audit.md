# E18-1 Structural and Exact Numeric Equality — Audit

ISSUE: #791
BRANCH: `issue-791-structural-numeric-equality` (not `main`; matches change)

Audited skeptically: the implementation is assumed wrong until evidence shows
otherwise, and the implementer's expectations are not treated as evidence.

---

## 1. SUMMARY

Status: **[x] PASS** (after one finding was fixed inside this issue)

The landed relation matches the E18-1 contract, which itself only narrows the
approved R18 contract. No host-language equality decides Genia behavior on any
path this slice owns, no later-slice semantics were pre-implemented, and no
public surface, parser, AST, or Core IR node changed. One genuine coverage gap
(purity against lazy sources and Refs) was found and fixed before this verdict.

---

## 2. CORE CHECKS

### Contract ↔ implementation

Every row of the contract's numeric matrix was checked against the code path
that decides it, not against the tests:

- boolean/number separation: `genia_equal` tests `isinstance(..., bool)` **first**,
  before any `int` branch. Because this host makes `bool` a subclass of `int`,
  any other ordering would silently restore the coercion. Verified by reading
  the dispatch order, not by trusting the test.
- exact int/float bridge: `_int_equals_float` rejects non-finite, rejects
  non-integral via `float.is_integer()`, then compares `integer == int(number)`.
  The integer is never converted to a float. Confirmed against a value that
  would break a lossy implementation (`9007199254740993` vs
  `9007199254740992.0`) and against `10**400`, which would overflow a float
  conversion outright.
- signed zero / infinities: reached through IEEE float comparison after the NaN
  guard, which yields exactly the contracted results.
- NaN: guarded before float comparison, so it is unequal to everything including
  itself, and because structural containers recurse through `genia_equal` rather
  than host container comparison, the non-reflexivity now propagates. This was
  a real pre-R18 defect (host list/dataclass comparison tests element identity
  first), and it is now closed.

Structural kinds were checked one by one against the contract table. All E18-1
families are present. Maps are absent **correctly**: they are #792.

The contract's "inert closed ordinary data descriptors" have no branch. This is
not a gap: those descriptors (for example `http_operation`'s result) are ordinary
`GeniaMap` values in this host, not distinct classes, so their equality arrives
with #792. Verified by reading `src/genia/http_operation.py`, which returns a
`GeniaMap`.

### Design ↔ implementation

The design's ordered dispatch, per-kind field tables, transitional-branch
approach, and identity-only unclassified terminal are all implemented as
designed. The design's stated import direction (`equality.py → values.py`,
`sheet.py` only) holds; the model/retrieval/callable/lifecycle families are
matched by class name specifically to avoid an import cycle, as designed.

### Tests ↔ contract coverage

Contract invariants 1–10 were each traced to evidence:

| Invariant | Evidence |
|---|---|
| 1 `!=` is exact negation | shared spec `inequality-is-negation`; evaluator calls `genia_equal` once and negates |
| 2 reflexivity except NaN | `test_structural_values_are_reflexive_without_nan`, `test_nan_identity_does_not_imply_equality` |
| 3 symmetry | every numeric-matrix case asserts both directions |
| 4 determinism | `test_relation_is_deterministic` |
| 5 `true == 1` false | shared spec + unit matrix |
| 6 exact bridge | `test_int_float_bridge_is_exact_for_large_integers` |
| 7 purity | `test_equality_does_not_invoke_callables...`, plus the two tests added by this audit |
| 8 always a bool | `test_relation_always_returns_a_bool` |
| 9 no Core IR/parser change | `git diff --name-only main...HEAD` touches only `equality.py` and `evaluator.py` under `src/`; `ir.py`, `parser.py`, `lowering.py`, `ast_nodes.py`, `optimizer.py` and `hosts/` are untouched, and the `ir`/`parse` shared spec categories pass unchanged |
| 10 R17 unaffected | R17 integer and map-order shared specs pass unchanged; the bridge test uses R17-scale integers |

### Docs ↔ behavior

The new `GENIA_STATE.md` section was re-read against the implementation line by
line. It claims nothing not implemented, and it explicitly lists the families
that have *not* changed. Checked specifically that it does not describe R18 as
complete, does not describe map equality, protected equality, `assert_eq`, or
pattern behavior as changed, and does not introduce token syntax or storage
language.

### Scope

No scope expansion. No public function, builtin, operator, syntax, capability,
or spec category added. `spec/manifest.json` unchanged.

---

## 3. FINDINGS

### F1 — Purity was asserted only against callables (fixed in this issue)

The contract's purity clause forbids consuming a Seq/Flow and dereferencing a
Ref, but the committed tests only proved that nested callables are not invoked.
That is weaker than the contract. Absence of a bug is not evidence of a
guarantee.

Fixed by adding `test_equality_does_not_consume_a_flow_or_seq` (counts pulls
from a generator source and asserts zero, directly and through a List and an
Outcome, then confirms the Flow is still usable) and
`test_equality_does_not_dereference_a_ref` (two distinct Refs with equal
contents remain unequal). Both pass.

### F2 — Two existing tests changed; verified as corrections, not workarounds

`tests/unit/test_list_hofs_190.py::test_int_1_equals_true_in_genia` asserted
that a predicate returning `1` counts as boolean `true`. Its own comment stated
this held because "Python: 1 == True". That is precisely a test encoding
accidental host behavior. Its own class docstring states invariant F4 —
"predicate must return boolean true or false" — and its sibling cases assert
that a string or list return is excluded. The new result (`[]`) satisfies the
stated invariant and removes a contradiction between sibling tests. Recorded as
a deliberate correction, and the test was renamed and re-commented to say why.

`tests/spec/test_python_protocol_adapter_parity_762.py` is pure bookkeeping of
the shared-case count (644 → 651 for seven added cases; unsupported stays 18).
Verified that none of the seven added cases needs an unexpressible fixture: all
651 cases pass through both the in-process and subprocess protocol paths.

### F3 — Deliberately not raising on unclassified host objects

The design forbids a host-equality fallback but the contract also forbids adding
an error surface in this slice. The implementation resolves this with identity
comparison. This was challenged during audit: could identity silently hide real
host leakage? It could, so it is recorded as an explicit obligation for #797's
release audit to verify that no value reachable from Genia source lands in that
terminal. A test proves the terminal never consults host `__eq__`, using a host
object whose `__eq__` returns `True` for everything.

### F4 — Non-findings explicitly checked and cleared

- `_deferred_equal` asymmetry: checked. When exactly one operand is a deferred
  family the relation returns `false` before reaching it, so the relation stays
  symmetric.
- host `None` vs `none` Outcome: checked. `None` is classified explicitly and is
  never equal to a `none` Outcome; the Outcome branches run first.
- `GeniaFunction`/`GeniaFunctionGroup` are host dataclasses with generated
  structural equality. Confirmed they are in the deferred set, so #791 does not
  silently change function equality ahead of #793.
- `GeniaSheet` comparison never uses tuple `==`; every cell goes through
  `genia_equal`.

---

## 4. FUTURE-HOST CHECK

Could a C++ implementer reproduce E18-1 from the written contract plus the
shared specs, without reading Python source?

Yes for this slice. The numeric matrix, kind separation, structural field lists,
and purity rules are all written in
`docs/design/r18-portable-value-equality-contract.md` and in the issue contract,
and the seven `spec/eval/r18-equality-*.yaml` cases are executable evidence
covering boolean separation, the exact bridge (including a case that a lossy
implementation fails), signed zero, both infinities, NaN through containers,
kind separation, structural byte contents, and `!=` as exact negation.

The one host-specific element — testing booleans before integers — is a defence
against a Python accident, and the *rule* it implements is written host-neutrally.
A C++ host with a distinct `bool` type needs no such defence and would still pass
the specs.

Infinities and NaN are reachable from ordinary Genia source via float overflow,
so this evidence needs no host-only escape hatch.

---

## 5. VALIDATION

- new focused unit evidence: 46 passed
- new shared spec wiring: 8 passed
- full shared spec suite: `total=651 passed=651 failed=0 invalid=0`
- documentation tests: 205 passed
- full regression is re-run before the PR is considered ready (§6)

---

## 6. VERDICT

**PASS.**

Remaining work is correctly deferred and explicitly labelled: map equality and
legal keys (#792), identity/opaque-token/protected families (#793), the
remaining equality-like surfaces (#794), conformance hardening (#795), and
authoritative release truth (#796). This issue must not be read as completing
R18.
