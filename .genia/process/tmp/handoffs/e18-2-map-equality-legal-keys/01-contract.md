# E18-2 Map Equality, Legal Keys, and Key Equivalence — Contract

ISSUE: #792
STATUS: contract

Narrows the approved parent contract
`docs/design/r18-portable-value-equality-contract.md` to the E18-2 scope. Where
the two could be read differently, the approved R18 contract governs.

Behavior only. No tests, no implementation.

---

## 0. BRANCH CHECK

Branch `issue-792-map-equality-legal-keys`, not `main`, matches pre-flight.

---

## 1. PURPOSE

Make map equality and map-key identity two consequences of the one Genia
equality relation, instead of properties supplied by a host container.

---

## 2. SCOPE

Included: map equality; the legal-key family; key reflexivity and NaN rejection;
one key relation across every map operation; preservation of R17 order.

Excluded: R17 order redesign; new keyable families; opaque tokens as keys; public
hash API; identity/token/protected equality (#793); `assert_eq`/patterns (#794).

---

## 3. BEHAVIOR — map equality

Map equality is equality of **mappings**, not of insertion history.

Two maps are equal exactly when:

1. they contain the same number of mappings, and
2. every mapping in one has a key in the other that is Genia-equal, whose mapped
   value is Genia-equal.

Consequences:

- two maps with the same mappings are equal even when their R17 iteration orders
  differ
- maps are compared by content, never by runtime allocation identity
- mapped **values** are compared with the full Genia relation, so a map is not
  restricted to legal-key values: any Genia value may be a value

A map may contain NaN as a **value**. Such a map is therefore not reflexive,
because NaN is not reflexive. R18 requires reflexivity of legal map *keys*, not
of every Genia value. `{"a": nan} == {"a": nan}` is `false`, and that is correct,
not a defect.

Maps are unequal to values of every other kind.

---

## 4. BEHAVIOR — legal map keys

A key is legal exactly when it belongs to one of:

- booleans
- integers
- floats that are not NaN, including infinities
- strings
- symbols
- Pairs whose head and tail are recursively legal
- Lists whose elements are recursively legal
- represented values whose carried value is recursively legal

Every legal key satisfies `k == k`.

Nothing else is a legal key. In particular the following are **not** made keyable
by R18: maps, Outcomes, functions, Templates and named patterns, providers,
declassification authorities, protected carriers, Refs, Cells, Processes, Seqs,
Flows, modules, runtime handles, Sheets, Formats, byte values, ZIP entries, RNG
states, and opaque semantic tokens.

NaN is illegal as a key. Any otherwise-legal structural key containing NaN in an
equality-relevant position — inside a List, a Pair, or a represented value's
carried value, at any depth — is likewise illegal.

R18 adds no public hashing surface. Internal canonicalization is private.

---

## 5. BEHAVIOR — key equivalence

For legal keys, key identity is exactly Genia `==`:

```text
a == b
  => same lookup entry
  => same presence answer
  => same replacement target
  => same removal target
  => same duplicate-key identity in a map literal
```

Equal legal keys are interchangeable in every map operation. Unequal legal keys
are never collapsed by host container coercion.

Required, and each is a direct consequence of the R18 numeric matrix:

| Keys | Same entry? |
|---|---|
| `1` and `1.0` | yes |
| `0.0` and `-0.0` | yes |
| `true` and `1` | **no** |
| `false` and `0` | **no** |
| `true` and `true` | yes |
| `"1"` and `1` | no |
| `quote(a)` and `"a"` | no |

Equal legal keys must receive identical internal key treatment, so no map
operation can distinguish them.

---

## 6. BEHAVIOR — R17 preservation

R17 map order semantics are unchanged by this issue:

- a newly associated key is appended to the end of the current order
- replacing an existing key's value preserves that key's position
- removal preserves the relative order of remaining keys
- removing then re-inserting a key appends it at the current end
- `map_items`, `map_keys`, `map_values` expose that deterministic order
- map literals associate left to right; a repeated key keeps the position of its
  first association while the last value wins

Order is a separate observable from equality. Two equal maps may expose different
orders. Changing key identity changes *which* keys collide, not how order is
maintained: when `1` then `1.0` are associated, that is one key that keeps the
first position and takes the second value, exactly as R17 replacement specifies.

---

## 7. FAILURE

Illegal keys are rejected deterministically at the existing map-key misuse
boundary, before any storage is consulted. This applies uniformly to lookup,
presence, insertion, and removal — an illegal key is illegal everywhere, not only
on insertion.

Rejection is deterministic: the same illegal key is always rejected, never
sometimes accepted because of a host identity shortcut.

No diagnostic on an equality or key path may contain a protected payload, an
opaque-token internal, or an internal canonical key form.

Existing rejection behavior for already-illegal families is preserved. R18 does
not redesign diagnostic text; R19 owns diagnostic hardening.

---

## 8. INVARIANTS

1. Map equality is symmetric, deterministic, and independent of insertion order.
2. Two maps with equal mappings are equal; two maps differing in any mapping are
   unequal.
3. A map is equal to no value of another kind.
4. Every legal key is reflexive.
5. `a == b` for legal keys implies the same entry for lookup, presence,
   replacement, removal, and duplicate detection.
6. Unequal legal keys always denote different entries.
7. NaN, and any structural key containing NaN, is never a legal key.
8. The legal-key family is exactly the list in §4 — no wider, no narrower.
9. R17 order semantics are unchanged.
10. Map equality and key canonicalization are pure, and neither invokes user code
    nor declassifies anything.
11. No public function, syntax, hash API, or Core IR node is added.

---

## 9. EXAMPLES

```genia
{"a": 1} == {"a": 1}          # true
{"a": 1, "b": 2} == {"b": 2, "a": 1}   # true, orders differ
{"a": 1} == {"a": 2}          # false
{"a": 1} == {"a": 1, "b": 2}  # false
{} == {}                      # true
```

```genia
m = map_put(map_put(map_new(), true, "bool"), 1, "int")
map_count(m)        # 2
map_get(m, true)    # "bool"
map_get(m, 1)       # "int"
```

```genia
n = map_put(map_put(map_new(), 1, "first"), 1.0, "second")
map_count(n)        # 1
map_get(n, 1)       # "second"
map_keys(n)         # [1]  first association keeps its position
```

---

## 10. NON-GOALS

R17 order redesign; new keyable families; opaque tokens as keys; public hashing;
deep diff; ordering of maps; identity/token/protected equality; pattern and
assertion reconciliation; token or storage APIs; C++ host.

---

## 11. DOC NOTES

`GENIA_STATE.md` must be updated by this issue in two places: the R17 section's
"current limitation/open question" about map equality is resolved and must no
longer be stated as open, and the E18-1 section's list of not-yet-landed families
must drop maps. Mark as **partial** — R18 completes at E18-6/E18-7.

---

## 12. FINAL CHECK

Precise and testable; no implementation detail; no scope expansion; consistent
with `GENIA_STATE.md` as final authority for what is implemented today.
