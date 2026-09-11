# E18-3 Identity, Opaque Token, and Protected Equality — Contract

ISSUE: #793
STATUS: contract

Narrows the approved parent contract to the E18-3 scope. Where the two could be
read differently, the approved R18 contract governs. Behavior only.

---

## 0. BRANCH CHECK

`issue-793-identity-token-protected-equality`, not `main`, matches pre-flight.

---

## 1. PURPOSE

Complete the four-family equality model by defining the three families that must
**not** be compared by contents: identity-bearing runtime values, opaque semantic
tokens, and protected carriers.

---

## 2. BEHAVIOR — identity-bearing runtime values

An identity-bearing value compares only by logical runtime entity identity.

Two such values are equal exactly when they denote the same runtime entity.
Equivalent visible state, configuration, or construction arguments never imply
equality.

The family is:

- functions, function groups, and host/native callables
- named pattern and Template matcher values
- model callables and model/embed/index/retrieve/rerank providers
- retrieval index handles
- modules
- Refs, Cells, Processes
- Seq and Flow values
- promises and meta-environments
- configuration providers and declassification authorities
- host/Python handles, IO source and sink handles
- lifecycle values denoting executable or runtime behavior

Equality never dereferences, invokes, advances, or inspects the referenced
entity. In particular it never reads a Ref's contents, a Cell's or Process's
state, a Seq's or Flow's elements, a provider's configuration, a module's
exports, or a closure's captured environment.

A future live Store, execution, actor, job, or subscription handle belongs to
this family by default, unless a later approved contract deliberately classifies
it as an opaque semantic token.

Identity-bearing values are terminal: when one is reached inside a structural
value, comparison stops there.

Identity-bearing values are not legal map keys. R18 does not change that.

---

## 3. BEHAVIOR — opaque semantic tokens

An opaque semantic token represents an immutable semantic fact whose equality is
meaningful but whose representation is not public.

Every token carries three hidden equality components, established before any
comparison occurs:

1. **domain identity** — which token domain the token belongs to
2. **provenance identity** — the issuing authority or origin the token is
   compatible with
3. **semantic identity** — the immutable opaque fact the token denotes

Two tokens are equal exactly when all three components are equal. A token is
never equal to a value of any other kind, including a token of a different
domain.

Comparison reads only those already-present components. It must not:

- contact or call an issuer, provider, or authority
- perform IO, parsing, ordering, or any user-defined computation
- execute a comparator supplied by the token, its domain, or user code
- expose any of the three components to Genia source

Token equality never fails because an issuer is unavailable: the identities
already exist on the token.

This family is deliberately **closed to comparator extension and open to domain
extension**. A future built-in token kind, or a future user-defined token domain,
participates by establishing the three identities at mint time. It may not
register comparator code, supply an equality method, or overload `==`. That is
what keeps one equality relation while leaving the family extensible.

R18 adds **no** public token-domain declaration, token minting API, token value,
or syntax, and implements no storage or `Revision`. A storage `Revision` is a
motivating future example of this family, not a special equality rule and not
something this release implements.

Opaque semantic tokens are **not** legal map keys in R18.

---

## 4. BEHAVIOR — protected carriers

A protected carrier compares by **carrier identity only**.

- a carrier is equal to itself, and to any alias naming the same carrier
- two independently acquired carriers are unequal, even when they come from the
  same provider and purpose and carry equal payloads
- a carrier is never equal to its payload, nor to a value of any other kind

Ordinary equality never compares protected payloads. Comparing payloads requires
first passing the existing explicit authorized declassification boundary; after
declassification the result is an ordinary value compared by ordinary rules.

Protected carriers are terminal inside structural values and are not legal map
keys.

---

## 5. BEHAVIOR — protected non-interference (security boundary)

Code that lacks matching declassification authority must not be able to derive
any information about a protected payload — including whether two payloads are
equal — through any of:

- `==` or `!=`
- recursive structural comparison at any depth
- Lists, Pairs, Outcomes, represented values, or maps containing carriers
- map keys, duplicate-key detection, or internal key canonicalization
- hashing or any internal canonical form
- ordering
- literal pattern matching or duplicate pattern bindings
- assertions
- serialization, including JSON encoding
- display, debug, or diagnostic rendering
- exception and rejection messages

The equality result **may** reveal carrier identity — that two names refer to the
same carrier. It must **not** reveal whether two independently acquired carriers
hold equal payloads.

No diagnostic produced on an equality, key, or rejection path may contain a
protected payload.

Because an accidental internal host comparison would defeat this boundary
regardless of what the language-level relation does, the host must not retain a
payload-comparing equality on the protected carrier type itself.

---

## 6. FAILURE

No new error surface. Cross-kind and cross-family comparisons yield `false`.

Existing rejection behavior is preserved: protected carriers, declassification
authorities, and runtime handles remain illegal map keys with their existing
messages, and those messages disclose no payload.

---

## 7. INVARIANTS

1. Identity-bearing values are equal exactly when they denote the same entity.
2. Equality never dereferences, invokes, advances, or inspects a referenced
   runtime entity.
3. Two tokens are equal exactly when domain, provenance, and semantic identities
   are all equal.
4. Token comparison contacts no issuer and runs no user-supplied comparator.
5. A protected carrier is equal only to itself or an alias of the same carrier.
6. No observable behavior discloses whether two independently acquired carriers
   hold equal payloads.
7. No diagnostic contains a protected payload or a token's hidden components.
8. Opaque tokens and protected carriers are not legal map keys.
9. Equality remains pure, total, and boolean-valued.
10. No public function, syntax, token API, storage implementation, or Core IR
    node is added.
11. `==` remains non-overloadable; no value supplies its own comparator.

---

## 8. EXAMPLES

```genia
r = ref(1)
s = r
r == s            # true, same runtime entity
r == ref(1)       # false, equal contents are not equality
```

```genia
a1 = secret_get(provider, "A", quote(use))
a2 = secret_get(provider, "A", quote(use))
b  = secret_get(provider, "B", quote(use))   # same payload as A

a1 == a1          # true
a1 == a2          # false, independently acquired
a1 == b           # false, and this must not disclose that the payloads match
[a1] == [b]       # false
```

---

## 9. NON-GOALS

Public token syntax, minting APIs, or token values; storage/`Revision`;
opaque tokens as map keys; user-defined comparators or equality overloading;
declassification changes; diagnostic redesign (R19); `assert_eq`/pattern
reconciliation (#794); C++ host.

---

## 10. DOC NOTES

`GENIA_STATE.md` must be corrected by this issue: its statement that protected
equality includes carried-value equality becomes false. The E18-1/E18-2 deferred
list must also drop the identity, token, and protected families.

Documentation must describe the opaque-token family as a contract/design property
with **no** implemented source-level feature — no token can be created or
observed from Genia source in R18.

Mark as **partial**; R18 completes at E18-6/E18-7.

---

## 11. FINAL CHECK

Precise and testable; no implementation detail; no scope expansion; consistent
with `GENIA_STATE.md` as final authority for currently implemented behavior.
