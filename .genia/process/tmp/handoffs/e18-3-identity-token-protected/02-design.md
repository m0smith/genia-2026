# E18-3 Identity, Opaque Token, and Protected Equality — Design

ISSUE: #793
STATUS: design

Translates the E18-3 contract into implementation structure. Adds no behavior.

---

## 1. PURPOSE

Replace the last transitional branch with three real families, and remove the
host-level protected-payload oracle so the security boundary does not depend on
every caller remembering to use the language relation.

---

## 2. ARCHITECTURE

### 2.1 Ordering inside `genia_equal`

The three families are checked **before** any structural branch, because the
whole point is that structural recursion must never reach their contents:

1. protected carriers
2. opaque semantic tokens
3. identity-bearing values

Each is terminal. A structural container holding one of them recurses into the
container and then stops at the leaf.

Protected carriers are checked first so that no other branch — present or
future — can observe a carrier before the identity-only rule applies.

### 2.2 Protected carriers

Language-level: two carriers are equal exactly when `left is right`.

Host-level: **`GeniaProtected.__eq__` is removed.** This is a defence in depth
required by the contract, not a redundancy:

- `assert_eq` currently compares with host `!=` and would otherwise remain a
  payload oracle until #794 lands
- any present or future internal host comparison, deduplication, membership test,
  or accidental `==` would otherwise be an oracle
- the removal is what makes the guarantee a property of the *type* rather than a
  property of every caller's discipline

With `__eq__` removed the class inherits identity equality, which is exactly the
contract. `__hash__ = None` is deliberately **kept**: protected carriers must
stay unhashable so they cannot be placed in a host set or dict, which would be
another equality-shaped oracle. Unhashability is also consistent with their being
illegal map keys.

`_declassify_with` is untouched: authorized declassification is the only
supported path to the payload and this slice does not change it.

### 2.3 Opaque semantic tokens

R18 adds no public token class, value, or minting API. What it adds is the
**adapter shape** the equality engine will use when a token type eventually
exists.

A value participates in this family by exposing an immutable triple of hidden
equality identities. The engine reads that triple and compares the three parts.
It never calls a comparator, method, issuer, or provider supplied by the token —
the token supplies **data**, not behavior. That distinction is what keeps `==`
non-overloadable while leaving the family open to future domains.

Two tokens are equal exactly when domain, provenance, and semantic identities are
all equal. Each part is compared by the canonical relation, so the comparison is
itself portable rather than delegating to host equality.

A token is never equal to a non-token, and tokens of different domains are never
equal (which falls out of comparing the domain identity first).

No token type exists in `src/`. The architecture is exercised by a **test-only**
fixture, as the parent contract permits ("A private test fixture may exercise
this architecture if needed, but it must not become source-visible language
behavior"). Nothing in the Genia surface can create or observe a token in R18.

### 2.4 Identity-bearing values

An explicit family list — the same one E18-1 deferred — compared with
`left is right`.

This deliberately overrides host dataclass equality, which today compares fields
for `ModuleValue`, `GeniaPythonHandle`, `GeniaNamedPattern`, `GeniaFunction`, and
`GeniaFunctionGroup`. `ModuleValue`'s generated equality compares its entire
export table, which is exactly the "equivalent visible state implies equality"
error the contract forbids.

Detection reuses E18-1's approach: `isinstance` for classes importable without a
cycle, and class-name matching for the model/retrieval/callable/lifecycle layers.

Plain callables (host functions, lambdas) are included, so a callable reaching
the relation is classified deliberately rather than falling through to the
unclassified terminal.

### 2.5 Removing the transitional scaffold

`_DEFERRED_TO_IDENTITY_SLICE`, `_DEFERRED_TO_IDENTITY_SLICE_BY_NAME`,
`_is_deferred`, and `_deferred_equal` are deleted. After this slice the relation
has no transitional branch and no host-equality delegation anywhere.

The unclassified identity terminal from E18-1 remains, but after this slice
nothing reachable from Genia source should land in it — #797 verifies that.

---

## 3. FILE PLAN

Modified:
- `src/genia/equality.py` — three family branches; transitional scaffold removed
- `src/genia/values.py` — remove `GeniaProtected.__eq__`, keep `__hash__ = None`
- `GENIA_STATE.md` — correct the protected-equality line; update the deferred list

New:
- `spec/eval/r18-identity-*.yaml`, `spec/eval/r18-protected-*.yaml`
- `tests/unit/test_r18_identity_token_protected_793.py`
- shared-spec wiring test

---

## 4. TEST PLAN INPUT

Contract invariants 1–11.

Security testing is **adversarial**: for each observable listed in contract §5,
attempt to extract payload information and assert failure. Uses the established
sentinel-proof pattern — put a unique sentinel string in the payload, then assert
the sentinel appears in no output, message, or encoding, and that no observable
distinguishes equal-payload carriers from different-payload ones.

The decisive test: build two carriers with **equal** payloads and two with
**different** payloads, then assert every observable behaves identically across
both pairs. Equality that merely returns `false` for both is correct; equality
that returns `true` for the equal-payload pair is the oracle.

Also test: identity aliases vs independently constructed equivalents for Refs,
Cells, modules, function groups, and named patterns; that a module's exports are
not compared; token triple equality and difference in each of the three
components; that a token comparison invokes nothing.

Regression risks: tests that compared modules or function groups with `==`
expecting field equality; `contains_protected` (uses `isinstance`, unaffected);
anything placing a protected value in a host container.

---

## 5. COMPLEXITY CHECK

- [ ] Minimal
- [x] Necessary
- [ ] Over-engineered

Three branches plus one deletion. The token adapter is the smallest thing that
makes the fourth family real without inventing public API.

---

## 6. FINAL CHECK

- matches contract exactly: YES
- no behavior added by design: YES
- no public token surface, storage, or syntax: YES
- no user-overloadable equality: YES — tokens supply data, never comparators
- protected payload unreachable without declassification: YES
- no Core IR or parser change: YES

**GO for the E18-3 failing-test phase.**
