# E18-2 Map Equality, Legal Keys, and Key Equivalence — Audit

ISSUE: #792
BRANCH: `issue-792-map-equality-legal-keys` (not `main`; matches change)

Audited skeptically. The implementer's expectations are not evidence.

---

## 1. SUMMARY

Status: **[x] PASS**

Map equality and map key identity are now two views of one relation owned by one
canonicalizer. The full regression shows no behavioral fallout beyond the
intended change. One genuine defect was found **outside** this issue's scope — a
second, independent key relation for Sheet column names — and is recorded as a
named obligation for #794 rather than silently fixed here.

---

## 2. CORE CHECKS

### Contract ↔ implementation

Each required key-equivalence row was checked against the canonicalizer's code
path, not against the tests:

- `true`/`1`: booleans are tagged `("bool", …)` before the `int` branch is
  reachable, so they cannot meet `("num", …)`. Verified by dispatch order.
- `1`/`1.0`: the integral-float branch returns `("num", int(value))`, converting
  the **float** upward. Checked explicitly that no path narrows an integer to a
  float, which is what keeps the R17 arbitrary-precision guarantee. Confirmed
  against `9007199254740993` vs `9007199254740992.0`, which stay two keys.
- `0.0`/`-0.0`: both integral, both reduce to `0`. Collapse is by construction.
- infinities: not finite, so they keep exact float identity and stay distinct by
  sign.
- strings vs symbols: distinct tags.
- Pair/List/represented: recurse, so nested legality and nested identity are one
  rule rather than two.

Challenged and confirmed: *could two equal floats ever take different tags?*
No — equality of two non-NaN floats implies equal mathematical value, which
implies equal integrality, which implies the same tag. So the tagging cannot
split an equal pair.

Challenged and confirmed: *is the one-directional scan in `_map_equal` enough?*
Yes. Canonical identities are unique dict keys, and the length check plus a
successful lookup of every left key in right forces a bijection.

### Legality boundary

NaN rejection is inside the canonicalizer, and every `GeniaMap` operation
(`get`, `put`, `has`, `remove`) calls `_freeze_map_key` first. So "illegal
everywhere, not only on insertion" holds structurally rather than by four
separate checks. Directly tested for all four operations.

Nested NaN rejects through ordinary recursion, so the rejection rule cannot drift
out of step with the identity rule. Tested at depth in Lists, Pairs, and
represented keys.

### R17 preservation

This was the highest-risk area, so it was tested rather than reasoned about:
append-on-new-key, replacement-preserves-position, replacement through an equal
*cross-kind* key preserves position, removal preserves remaining order,
remove-then-reinsert appends, and persistence (operations do not mutate the
source). All pass. The shared spec
`r18-map-equal-keys-share-every-operation.yaml` asserts the same rules through
ordinary source.

Additionally, the full regression contains the pre-existing R17 map-order shared
specs; they pass unchanged.

### Docs ↔ behavior

The resolved R17 "open question" was the one real documentation contradiction and
is fixed. The key-family wording no longer reads as if host tuple keys were a
public Genia key kind, which implements the parent contract's explicit
instruction.

### Scope

No public function, syntax, hash API, capability, or Core IR node added. Map
patterns were checked and need no change: `IrPatMap` matches via `arg.has(key)`
and `arg.get(key)`, so it already routes through the one canonicalizer.

---

## 3. FINDINGS

### F1 — A second key relation exists for Sheet column names (out of scope; handed to #794)

`src/genia/sheet.py::_freeze_column_name` is an independent, hand-rolled key
identity relation with exactly the defects R18 exists to remove: it returns raw
host values for booleans, integers, floats, and strings, so the host dictionary
decides column-name identity.

Measured on this branch:

```
sheet([[true, [1]], [1, [2]]])
→ Error: sheet expected unique column names
```

Under the canonical relation `true != 1`, so those are two distinct column names
and the Sheet should be accepted. This is a live disagreement between a
key-like surface and `==`.

**Not fixed here.** #792's approved scope is map equality, legal keys, and key
equivalence. Sheet column-name identity is an equality-like surface, which is
explicitly #794's scope ("other approved equality-like surfaces found by
inventory"). Fixing it here would be scope expansion; ignoring it would let a
known host-defined relation survive the release.

**Recorded as a required item for #794**, and for #797 to verify.

### F2 — `GeniaMap` still has no host `__eq__` (deliberate; obligation carried forward)

Internal host `==` on two maps remains identity. The design records why
(`__hash__ = None` would break internal identity-hashing of maps; an inconsistent
eq/hash pair is its own hazard) and follows E18-1's precedent that the canonical
relation lives in `equality.py`.

The residual risk is that some *semantic* site compares maps with host `==` and
therefore gets identity instead of the relation. This audit did not find one, but
absence of a find is not proof. Carried forward as an explicit obligation for
#794's inventory sweep and #797's audit.

### F3 — Host tuple/`None` key accommodations retained

Challenged: should these be removed? No. The parent contract says they are "not
authority to introduce a new public tuple/null key kind" — it does not authorize
removing them, and removing them would be an unrequested behavior change.
Retained with their own tags, and the documentation no longer presents them as
public key families. Correct handling of an explicit contract instruction.

### F4 — Non-findings checked and cleared

- duplicate canonical keys within one map: impossible, dict keys are unique
- `json_encode` object-member ordering: reads raw keys from entry values, not
  canonical identities; unaffected and its specs pass
- map display/formatting (`utf8._format_map`): reads raw keys, display only
- `map_get`'s two-argument default path: still routes through the canonicalizer
  before consulting storage, so an illegal key is rejected rather than silently
  returning the default
- protected key rejection: tested that the message contains no payload

---

## 4. FUTURE-HOST CHECK

Could a C++ implementer reproduce E18-2 from the written contract plus shared
specs, without reading Python source? Yes.

The critical portability hazard is that a host will reach for its own hash-map
key equality, which typically merges `true` with `1` and accepts NaN. The shared
cases make both failures visible:
`r18-map-key-equivalence-is-equality.yaml` fails a host that merges kinds, and
the three `r18-map-key-*-rejected` error cases fail a host that accepts NaN on
insertion, at depth, or on lookup. `r18-map-structural-equality.yaml` fails a
host that compares maps by allocation identity, and
`r18-map-equal-keys-share-every-operation.yaml` pins R17 order alongside key
collapse so a host cannot satisfy one by breaking the other.

The canonical identity *representation* is deliberately internal and is not
specified to hosts; only the observable relation is. A host may use any internal
representation that reproduces it.

---

## 5. VALIDATION

- focused unit + shared spec wiring: 57 passed
- full shared spec suite: `total=657 passed=657 failed=0 invalid=0`
- documentation tests: 205 passed
- full regression `-m "not loopback"`: 3 failed / 4107 passed, where the only
  non-baseline failure was the protocol parity spec **count** (651→657), now
  updated; the other two are the pre-existing root/`chmod 000` cases measured on
  `main` before this branch
- full regression is re-run green before the PR is considered ready

---

## 6. VERDICT

**PASS**, with one named out-of-scope defect (F1) handed to #794 and one
obligation (F2) carried to #794/#797.
