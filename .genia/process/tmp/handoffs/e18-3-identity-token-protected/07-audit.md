# E18-3 Identity, Opaque Token, and Protected Equality — Audit

ISSUE: #793
BRANCH: `issue-793-identity-token-protected-equality` (not `main`; matches change)

Audited skeptically, and treated as a **security review**, not only a correctness
review. The implementer's expectations are not evidence.

---

## 1. SUMMARY

Status: **[x] PASS**

The protected-payload oracle is closed at the type level as well as at the
language level, so it is closed for paths #794 has not reached yet. The three
non-structural families are classified explicitly, and the relation now has no
host-equality delegation anywhere. Two structural risks introduced by this
slice's design were probed directly and found clean.

---

## 2. SECURITY REVIEW

### The oracle is closed, and closed at the right layer

Measured before this slice, from ordinary source with no declassification
authority: two independently acquired carriers holding the same secret compared
**equal**, and the leak travelled through Lists, Outcomes, `err` context, map
values, and nested containers, alternating exactly with payload equality.

After this slice every one of those observables answers `false` for both the
equal-payload pair and the different-payload pair. The tests assert
*indistinguishability* rather than a particular value, which is the stronger
property: an observable that returns `false` for both is correct; one that can
tell the pairs apart is an oracle even when each answer looks reasonable.

The decisive design point was challenged: *is removing `GeniaProtected.__eq__`
redundant once the equality boundary handles carriers?* No. Verified directly
that `assert_eq` — which still compares with host `!=` until #794 — is already
non-oracular because of the type-level change:

```
host != on equal payloads  : True
host != on diff payloads   : True
indistinguishable          : True
```

Had the fix lived only in the equality boundary, `assert_eq` would have remained
a payload oracle for the whole interval between #793 and #794. Removing it from
the type makes the guarantee a property of the type rather than of every
caller's discipline.

### Other leak surfaces checked

- rendering: `format_display` and `format_debug` disclose no payload through any
  of ten container shapes
- map-key rejection: message contains no payload
- hashing: carriers remain unhashable, so they cannot enter a host set or dict —
  itself an equality-shaped oracle, and consistent with being illegal map keys
- declassification: comparing carriers consults no authority (spy asserts zero
  calls)
- end-to-end: the exact pre-R18 oracle source now returns
  `[True, False, False, False, False]`

### Residual

Equality still reveals **carrier identity** — that two names denote the same
carrier. That is explicitly permitted by the contract and is not a payload leak.

---

## 3. CORE CHECKS

### Two risks this slice's own design introduced, probed directly

**R1 — the `callable()` catch-all could misclassify a structural value.**
`_is_identity_bearing` ends with `callable(value)`, and the three families are
checked *before* the structural branches. If any structural runtime type defined
`__call__`, it would be silently reclassified as identity-bearing and stop
comparing by contents. Probed every structural kind:

```
callable structural values (would be misclassified): []
```

Clean today. Recorded as a standing constraint: **a future structural Genia value
must not be callable**, or it must be excluded from this check explicitly. Handed
to #797.

**R2 — the token probe calls `getattr` on every operand of every comparison.**
If a runtime class defined a dynamic `__getattr__`, that lookup could execute
code and break equality purity. Scanned every class in `values.py`; none defines
`__getattr__`. Clean.

### Contract ↔ implementation

- identity: `left is right`, with no field access anywhere on the path. Verified
  that `ModuleValue`'s host dataclass equality — which compares its whole export
  table — is overridden, and that a named pattern's matcher is never invoked.
- tokens: equal iff all three identities are equal, each compared with
  `genia_equal` rather than host equality. Confirmed by a test that the exact
  int/float bridge and boolean/number separation both apply *inside* a token
  identity, which proves the components really do go through the canonical
  relation.
- non-overloadability: a fixture token that also offers an `__eq__` returning
  `True` for everything is compared correctly as unequal, proving the engine
  reads the token's data and ignores its behavior.
- ordering: protected is checked first, then tokens, then identity, all before
  any structural branch, so recursion cannot reach inside any of them.

### Scaffold removal

`_deferred_equal` and `_is_deferred` are gone, asserted by a test rather than by
inspection. The relation now has no host-equality delegation on any path.

### Superseded prior expectations — verified as corrections, not workarounds

Four places asserted the pre-R18 payload-comparing behavior:

1. `spec/eval/protected-secret-acquisition-and-matching.yaml`
2. `tests/unit/test_protected_configuration.py` (its name literally described
   equality as including the payload)
3. `tests/unit/test_configuration_views.py`
4. `tests/unit/test_lifecycle_config.py`

Checked against the truth hierarchy rather than simply overwritten: `spec/*`
ranks below `GENIA_STATE.md`; the approved R18 contract defines
carrier-identity-only equality; #793's scope states it outright. `GENIA_STATE.md`
and the spec were updated in the same change, so no authoritative source is left
contradicting another.

For (3) and (4) the tests had a legitimate intent — proving a view acquires the
same secret as a direct acquisition — that `==` can only serve if equality
compares payloads. That intent is now established through the **authorized
declassification boundary**, which is both correct and a better test: it proves
provider and purpose match too. Weakening the assertions to `!=` alone would have
lost real coverage.

---

## 4. FUTURE-HOST CHECK

Could a C++ implementer reproduce E18-3 from the written contract plus shared
specs, without reading Python source?

For identity and protected: yes. `r18-protected-equality-is-carrier-identity` and
`r18-protected-non-interference-through-containers` fail any host that compares
payloads, at every container shape, and `r18-identity-bearing-equality` fails a
host whose runtime values carry structural equality.

For opaque tokens: there is deliberately **no** shared spec, because R18 exposes
no way to mint or observe a token from source. A shared case would have to invent
the public surface this release excludes. The family is specified in prose —
three immutable identities established at mint time, compared as data, no issuer
contact, no comparator — which is enough for a future host to implement it when a
token type is introduced. Recorded so #795 does not mistake the absence for a
coverage gap and #797 does not mistake it for an untested claim.

The security property a future host most needs is stated as a prohibition, not an
implementation: protected equality must never compare payloads.

---

## 5. VALIDATION

- focused + shared 793 evidence: 60 passed
- protected/declassification/sink/lifecycle suites: 45 passed
- full shared spec suite: `total=660 passed=660 failed=0 invalid=0`
- documentation tests: 205 passed
- full regression re-run green before the PR is considered ready

---

## 6. VERDICT

**PASS**, with two standing constraints handed to #797: a future structural Genia
value must not be callable (R1), and no semantic site may decide map sameness
with host `==` (carried from #792).
