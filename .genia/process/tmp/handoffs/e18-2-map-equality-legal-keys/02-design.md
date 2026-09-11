# E18-2 Map Equality, Legal Keys, and Key Equivalence — Design

ISSUE: #792
STATUS: design

Translates the E18-2 contract into implementation structure. Adds no behavior.

---

## 0. BRANCH CHECK

`issue-792-map-equality-legal-keys`; pre-flight and contract exist on it.

---

## 1. PURPOSE

Replace the host dictionary's implicit key relation with one canonical key
identity owned by the equality boundary, and add the map branch to the canonical
relation, so map equality and key identity become two views of the same rule.

---

## 2. ARCHITECTURE

### 2.1 One canonicalizer, owned by the equality boundary

`src/genia/equality.py` gains:

```text
canonical_map_key(value) -> hashable internal identity   (raises on illegal keys)
```

This is internal. It is not a public hash API and is not reachable from Genia
source. It is the *only* place that decides key legality and key identity.

### 2.2 Canonical identities are kind-tagged

Every identity is a tuple whose first element tags the Genia semantic kind, so no
host coercion can merge two kinds:

| Key | Canonical identity |
|---|---|
| boolean | `("bool", True/False)` |
| integer | `("num", exact int)` |
| float, finite and integral | `("num", exact int)` |
| float, finite and non-integral | `("float", value)` |
| float, infinite | `("float", value)` — deterministic by sign |
| float NaN | **rejected** |
| string | `("string", value)` |
| symbol | `("symbol", name)` |
| Pair | `("pair", ck(head), ck(tail))` |
| List | `("list", (ck(item), …))` |
| represented | `("represented", facet, ck(carried))` |
| anything else | **rejected** |

Why this is exactly `==` on legal keys:

- booleans get their own tag, so `true` can never meet `1` — the current defect
- an integer and an exactly-equal integral float both reduce to the same exact
  integer, which is the contract's int/float bridge, and it is exact because the
  float is converted upward, never the integer downward
- `0.0` and `-0.0` are both integral and reduce to `0`, so they collapse as
  required
- two equal floats always have the same integrality, so they always take the same
  tag; non-integral finite floats and infinities keep exact float identity, whose
  host comparison for non-NaN floats is exactly IEEE equality, which is the
  contract
- strings and symbols have distinct tags
- Pair/List/represented recurse, so nested legality and nested identity are both
  inherited

### 2.3 NaN rejection is structural

NaN is rejected at the point it is encountered, so a NaN anywhere inside a List,
Pair, or represented carried value at any depth rejects the whole key by ordinary
recursion. No separate "contains NaN" scan is needed, which means the rule cannot
drift out of step with the identity rule.

### 2.4 Host-internal accommodations are preserved, not promoted

`_freeze_map_key` currently also accepts host `None` and host tuples. The
approved contract says these are "not authority to introduce a new public
tuple/null key kind".

They are therefore kept working, with their own tags (`("host-none",)`,
`("host-tuple", …)`), and are documented as host-internal accommodations rather
than public key families. Removing them is a behavior change this issue's
contract does not authorize; promoting them to documented key kinds is one the
parent contract forbids. Keeping them inert satisfies both.

### 2.5 `GeniaMap` integration

`values.py::_freeze_map_key` becomes a thin delegation to
`canonical_map_key`. `GeniaMap.get`, `put`, `has`, and `remove` continue to call
`_freeze_map_key` and therefore all route through the one canonicalizer without
individual changes. Map literal duplicate-key association already goes through
`put`, so it is covered by construction rather than by a parallel code path.

Because rejection happens inside `_freeze_map_key`, an illegal key is rejected on
lookup and presence as well as on insertion, as the contract requires.

Import direction: `equality.py` imports `values.py`, so `values.py` must not
import `equality.py` at module scope. `_freeze_map_key` uses a function-local
import with a module-level cache after first use. The E18-0 design explicitly
anticipated this ("using a function-local import if required").

R17 order is stored by the insertion order of `self._entries`, which is untouched
by this change. Only *which* canonical identity a key maps to changes, so order
maintenance is unaffected.

### 2.6 Map equality in the canonical relation

`GeniaMap` moves out of E18-1's transitional branch into its own branch:

```text
len(left._entries) != len(right._entries)  -> False
for canonical_key, (_, left_value) in left._entries.items():
    entry = right._entries.get(canonical_key, MISSING)
    if entry is MISSING: return False
    if not genia_equal(left_value, entry[1]): return False
return True
```

Lookup by canonical identity is exactly "the other map has an equal key",
because canonical identity *is* key equality. Iterating one side and looking up
the other ignores order by construction, and the length check makes the
one-directional scan sufficient.

Mapped values use the full relation, so any Genia value may be a value, and a map
holding NaN as a value is correctly non-reflexive.

### 2.7 Deliberately **not** adding `GeniaMap.__eq__`

Considered and rejected for this issue.

Adding it would make internal host `==` on maps structural too, which sounds
desirable, but it forces a choice between `__hash__ = None` (breaking any
internal use of a map in a host set/dict, and maps are currently identity-hashable)
and an inconsistent eq/hash pair, which is its own hazard.

E18-1 set the precedent: byte values gained structural Genia equality without
gaining a host `__eq__`. The canonical relation lives in `equality.py`; host
`==` on a runtime object is an implementation-local comparison, not a Genia
semantic path.

Recorded as an explicit obligation: **#794's inventory sweep and #797's audit
must confirm no semantic site decides map sameness with host `==`.**

---

## 3. FILE PLAN

Modified:
- `src/genia/equality.py` — add `canonical_map_key`, add the map branch, remove
  `GeniaMap` from the transitional set
- `src/genia/values.py` — `_freeze_map_key` delegates to the canonicalizer
- `GENIA_STATE.md` — resolve the R17 open question; drop maps from E18-1's
  not-yet-landed list

New:
- `spec/eval/r18-map-*.yaml`, `spec/error/r18-map-key-*.yaml`
- `tests/unit/test_r18_map_equality_legal_keys_792.py`
- shared-spec wiring test

Removed: none.

---

## 4. TEST PLAN INPUT

Invariants to test: contract §8 items 1–11.

Specific targets:
- equal-content maps with different insertion histories compare equal, while
  `map_keys` still reports their differing R17 orders in the same program
- `true`/`1` and `false`/`0` are distinct entries; `1`/`1.0` and `0.0`/`-0.0` are one entry
- replacement through a cross-kind equal key preserves R17 position
- removal and re-insertion still append
- NaN key rejected on put, get, has, and remove
- nested NaN inside List, Pair, and represented keys rejected
- every non-keyable family still rejected, including protected values
- map equality with nested maps, and with NaN as a value
- no internal canonical form appears in any rejection message

Regression risks: R17 order damage; the two-argument `map_get` default path;
map patterns; `json_encode` object-member ordering; anything relying on
`_entries` keys.

---

## 5. COMPLEXITY CHECK

- [ ] Minimal
- [x] Necessary
- [ ] Over-engineered

One canonicalizer plus one branch. No registry, no public hashing, no second
relation.

---

## 6. FINAL CHECK

- matches contract exactly: YES
- no behavior added by design: YES
- R17 order preserved by construction: YES
- no public surface, hash API, or Core IR change: YES
- no later-slice semantics implemented: YES (protected keys stay rejected exactly
  as they already are; #793 changes protected *equality*, not keyability)

**GO for the E18-2 failing-test phase.**
