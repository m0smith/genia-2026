# E18-2 Map Equality, Legal Keys, and Key Equivalence — Test Phase

ISSUE: #792
STATUS: failing evidence written and proven failing before implementation

---

## Added evidence

Shared, host-neutral:

- `spec/eval/r18-map-structural-equality.yaml`
- `spec/eval/r18-map-key-equivalence-is-equality.yaml`
- `spec/eval/r18-map-equal-keys-share-every-operation.yaml`
- `spec/error/r18-map-key-nan-rejected.yaml`
- `spec/error/r18-map-key-nested-nan-rejected.yaml`
- `spec/error/r18-map-key-nan-rejected-on-lookup.yaml`
- `tests/spec/test_r18_map_equality_shared_specs_792.py`

Focused:

- `tests/unit/test_r18_map_equality_legal_keys_792.py`

---

## Proof the new cases fail for the intended semantic reason

`uv run pytest -q tests/spec/test_r18_map_equality_shared_specs_792.py`
→ **5 failed, 2 passed**

| Spec | Expected | Actual | Semantic reason |
|---|---|---|---|
| `map-structural-equality` | `[true, true, true, false, false, true, true, true]` | `[true, false, false, false, false, false, false, false]` | maps have no structural equality at all; only a map compared with itself is equal, and even two empty maps are unequal |
| `map-key-equivalence-is-equality` | `[2, "bool", "int", 2, …]` | `[1, "int", "int", 1, …]` | the host dictionary decides key identity, so `true` and `1` collapse into one entry and the boolean's value is lost |
| `map-key-nan-rejected` | stderr + exit 1 | `{nan: "value"}`, exit 0 | NaN is accepted as a key |
| `map-key-nested-nan-rejected` | stderr + exit 1 | `{[1, [2, nan]]: "value"}`, exit 0 | a NaN nested inside a List key is accepted |
| `map-key-nan-rejected-on-lookup` | stderr + exit 1 | `false`, exit 0 | a NaN lookup silently reports absence instead of rejecting |

Passing before implementation, kept as portable conformance evidence:
`map-equal-keys-share-every-operation`. The Python host already collapses `1`
and `1.0` correctly and already maintains R17 order correctly; a host that did
not collapse cross-kind numeric keys would fail this case. It also pins R17 order
behavior so the key-identity change cannot silently damage it.

`uv run pytest -q tests/unit/test_r18_map_equality_legal_keys_792.py`
→ collection error: `cannot import name 'canonical_map_key'`. The canonicalizer
does not exist yet; the semantic contradictions it asserts are the ones measured
above through the shared specs.

---

## Behavior measured and deliberately pinned, not changed

Replacing an entry through an equal cross-kind key keeps the replaced entry's
R17 position but retains the *replacing* key's representation, so after
associating `1` then `1.0` the key reported by `map_keys` is `1.0`.

Neither R17 nor R18 specifies which representation survives: R17 contracts the
key's position, R18 contracts which keys collide. This is therefore existing
unspecified behavior, and E18-2 must not change it opportunistically. It is
asserted in `r18-map-equal-keys-share-every-operation.yaml` so it is pinned
rather than left to drift.

---

## Unrelated pre-existing failures

Baseline on `main` @ `82fd58a`: `-m "not loopback"` 2 failed / 4051 passed
(the two root/`chmod 000` native-test-runner cases), `-m loopback` 26 passed,
shared spec suite 651/651.
