# E18-2 Map Equality, Legal Keys, and Key Equivalence — Pre-flight

ISSUE: #792
PARENT: #789
BLOCKED BY: #790 (merged, PR #805) and #791 (merged, PR #806)
STATUS: pre-flight

---

## 0. BRANCH

Branch required: YES
Branch slug: `map-equality-legal-keys`
Expected branch: `issue-792-map-equality-legal-keys`
Base branch: `main` @ `82fd58a` (contains merged E18-1)

---

## 1. SCOPE LOCK

### Includes

- structural map equality: equality of mappings, independent of R17 insertion
  and iteration order
- one legal-key relation identical to public `==` for lookup, presence,
  insertion/replacement, removal, and duplicate-key detection
- legal-key reflexivity, and therefore deterministic rejection of NaN and of any
  otherwise-keyable structural key containing NaN in an equality-relevant position
- kind-tagged internal key canonicalization so host container coercion can no
  longer merge unequal keys (notably `true` and `1`)
- moving `GeniaMap` out of E18-1's transitional branch into the canonical relation
- shared failing specs/tests before implementation

### Excludes

- any change to R17 deterministic iteration/accessor order
- new keyable families beyond the approved R18 legal-key list
- making opaque semantic tokens legal keys
- public hash API
- identity-bearing, opaque-token, and protected-carrier equality — #793
  (protected values remain rejected as keys, which is existing behavior, not new
  #793 semantics)
- `assert_eq`, literal patterns, duplicate bindings — #794
- token/storage/C++ implementation

---

## 2. SOURCE OF TRUTH

Authoritative: `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`,
`README.md`, `AGENTS.md`.

Additional relevant: `docs/design/r18-portable-value-equality-contract.md`
(sections "Map equality", "Legal map keys and key equivalence", "Map-key
canonicalization", "GeniaMap integration"); the E18-0 design; the merged E18-1
handoffs; `GENIA_STATE.md`'s R17 ordered-map section.

Note: `GENIA_STATE.md`'s R17 section currently records as a "current
limitation/open question" that separately constructed equal-content maps compare
by host-object identity. This issue resolves that limitation, so that text must
be updated by this issue rather than left contradicting landed behavior.

---

## 3. FEATURE MATURITY

Stage: [x] Partial (E18-2 slice; R18 completes at E18-6/E18-7)

---

## 3a. Portability Analysis

All seven fields resolved; no `TBD`.

1. **Portability zone** — *language semantics (portable contract)*. Map equality
   and the legal-key relation are host-independent. The current reliance on a
   host dictionary's own key coercion is host leakage being removed.

2. **Core IR impact** — `none`. No new or changed `Ir*` node family. `IrMap` and
   the map pattern families are unchanged in shape. Map literal duplicate-key
   association changes which entries collide, but that is runtime semantics on an
   unchanged node. No parser, AST, or lowering change.

3. **Capability categories affected** — `none`. Key canonicalization and map
   equality are pure: no IO, no acquisition, no provider or user callback, no
   Flow/Seq consumption. `spec/manifest.json` capability lists are unchanged.

4. **Shared spec impact** — new executable cases under `spec/eval/`
   (map equality, key equivalence, R17 order preservation) and under
   `spec/error/` (deterministic illegal-key rejection). No new spec category or
   envelope field.

5. **Python reference host impact** — `src/genia/equality.py` gains the map
   branch and the internal legal-key canonicalizer; `src/genia/values.py`'s
   `_freeze_map_key` is replaced by/delegated to that canonicalizer and
   `GeniaMap` operations route through it. No public Genia function, builtin, or
   syntax is added. Observable changes: equal-content maps now compare equal;
   `true` and `1` become distinct keys; NaN and NaN-containing keys are rejected.

6. **Host adapter impact** — `none`. `hosts/python/adapter.py` and
   `protocol_adapter.py` are unchanged.

7. **Future host impact** — required and positive. A future host must not reuse
   its own hash-map key equality (which would typically merge `true`/`1` or
   accept NaN). The written contract plus the new shared cases specify the
   relation without reference to Python. No C++ implementation is added.

---

## 4. CONTRACT vs IMPLEMENTATION

Portable contract (approved by E18-0, implemented here):
- map equality is equality of mappings; equal-content maps are equal regardless
  of insertion history, while R17 iteration order is untouched
- for legal keys, key identity is exactly `==`
- every legal key is reflexive; NaN and NaN-containing keys are therefore illegal
- the legal-key families are exactly booleans, integers, non-NaN floats
  (including infinities), strings, symbols, and recursively legal Pairs, Lists,
  and represented values

Python implementation today (measured on this base):
- `GeniaMap` has no host equality, so `{"a":1} == {"a":1}` is `false`
- `_freeze_map_key` returns raw host values for `bool`/`int`/`float`/`str`, so
  the host dictionary decides key identity: `true` and `1` collapse into one key
  (measured: count 1, `map_get(m, true)` returns the integer's value)
- NaN is accepted as a key and appears to work only because host dictionary
  lookup shortcuts on object identity (measured: count 1, `map_has?` true)
- `1` vs `1.0` and `0.0` vs `-0.0` already collapse, which is correct
- unsupported keys already raise `TypeError("map key type is not supported: X")`,
  and protected values, declassification authorities, and index handles already
  have their own rejection messages

Host-only accommodations present today: `_freeze_map_key` accepts host `None`
and host tuples. The approved contract says these are not authority to introduce
public null/tuple key kinds. They stay host-internal and are neither promoted nor
documented as public key families.

---

## 5. TEST STRATEGY

Core invariants:
- equal-content maps are equal irrespective of insertion history
- R17 order semantics are bit-for-bit unchanged
- `a == b` implies same lookup/replacement/removal/duplicate-key entry
- `true`/`1` and `false`/`0` are distinct keys; `1`/`1.0` and `0.0`/`-0.0` are the same key
- NaN and nested-NaN keys are rejected deterministically
- no protected payload or internal canonical form appears in a diagnostic

Test approach: shared `spec/eval` and `spec/error` cases for source-reachable
behavior; focused pytest for the canonicalizer and for R17 order regression.
Failing evidence committed before implementation.

Baseline: `main` @ `82fd58a` — `-m "not loopback"` 2 failed / 4051 passed (the
two pre-existing root/`chmod 000` native-test-runner cases), `-m loopback` 26
passed, shared spec suite 651/651.

---

## 6. EXAMPLES

Minimal:
```genia
{"a": 1} == {"a": 1}                       # true
map_count(map_put(map_put(map_new(), true, "b"), 1, "i"))   # 2
```

Real:
```genia
a = map_put(map_put(map_new(), "x", 1), "y", 2)
b = map_put(map_put(map_new(), "y", 2), "x", 1)
a == b            # true
map_keys(a)       # ["x", "y"]   R17 order unchanged
map_keys(b)       # ["y", "x"]
```

---

## 7. COMPLEXITY CHECK

[x] Revealing structure

Map key identity is already a relation; today it is silently supplied by a host
dictionary. Naming it and making it agree with `==` removes hidden behavior and
one whole class of cross-host divergence.

---

## 8. CROSS-FILE IMPACT

Files likely to change: `src/genia/equality.py`, `src/genia/values.py`
(`_freeze_map_key`, `GeniaMap`), new shared specs, new focused tests,
`GENIA_STATE.md` (the R17 open-question text and the E18-1 section's deferred
list), plus existing tests that encoded host key coercion.

Risk of drift: [x] High — map behavior spans literals, accessors, patterns, and
host storage. Mitigated by one canonicalizer, by explicit R17 order regression
tests, and by measuring the baseline before changing anything.

---

## 9. DOC DISTILLATION CHECK

Creates process artifacts? YES → distillation runs; release-wide distillation is
#797. Adds `docs/design`/`docs/architecture` files? NO.
Doc drift risk: [x] Medium — the R17 "map equality unresolved" note must be
corrected in this issue.

---

## 10. PHILOSOPHY CHECK

- preserves minimalism? YES — no public surface added
- avoids hidden behavior? YES — this removes a hidden host relation
- keeps semantics out of host? YES
- aligns with pattern-matching-first? YES — map patterns match by content, and
  content is now defined by one relation

---

## KILLER WORKFLOW ALIGNMENT

[x] Yes. Validated data pipelines key, group, deduplicate, and compare records
by map content constantly. Equal-content maps comparing unequal, and `true`
silently overwriting the entry for `1`, are direct correctness hazards for record
parsing, validation, and diagnostics.

---

## 11. PROMPT PLAN

Preflight → Contract → Design → Test (failing) → Implementation → Docs → Audit →
Distillation.

---

## FINAL GO / NO-GO

Ready to proceed? **YES**. Both blockers (#790, #791) are merged.
