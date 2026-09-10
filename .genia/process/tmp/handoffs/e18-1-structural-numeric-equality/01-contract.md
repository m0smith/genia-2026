# E18-1 Structural and Exact Numeric Equality — Contract

ISSUE: #791
PARENT: #789
STATUS: contract

This contract **narrows** the already-approved parent contract
`docs/design/r18-portable-value-equality-contract.md` to the E18-1 slice. It does
not redefine R18. Where this document and the approved R18 contract could be read
differently, the approved R18 contract governs.

Contract defines behavior only. No tests and no implementation appear here.

---

## 0. BRANCH CHECK

Branch: `issue-791-structural-numeric-equality` (matches pre-flight). Not `main`.

---

## 1. PURPOSE

Genia has exactly one semantic equality relation. This slice makes that relation
real for structural values and numbers in the Python reference host, replacing
delegation to the host language's equality rules.

---

## 2. SCOPE (FROM PRE-FLIGHT)

Included: the E18-1 structural subset, the exact numeric matrix, and the single
`==`/`!=` evaluator dispatch point.

Excluded: maps (#792); identity-bearing, opaque-token, protected carriers (#793);
`assert_eq`, literal patterns, duplicate bindings and the wider inventory (#794);
conformance hardening (#795); authoritative documentation (#796).

---

## 3. BEHAVIOR

### 3.1 The relation

Genia equality is a binary relation over two already-present Genia values
producing a boolean.

`a == b` denotes it. `a != b` denotes exactly its logical negation: for all
operand pairs, `(a != b)` is `true` if and only if `(a == b)` is `false`.

`==` is not user-overloadable. No Genia-visible function, Template, matcher, or
provider can supply, replace, extend, or intercept it. This slice adds no public
function, builtin, operator, or import entry.

### 3.2 Kind separation

Two values of different Genia semantic kinds are unequal. The sole cross-kind
exception in all of R18 is the integer/float numeric bridge in §4.

Kind difference produces `false`. It is not an error.

Named consequences:

- symbol `quote(x)` is not string `"x"`
- a represented value is not its unrepresented carried value
- a List is not a Pair
- a boolean is not an integer and is not a float
- an Outcome is not its carried contents

### 3.3 Structural equality (E18-1 subset)

A structural value compares recursively by its **named semantic contents**. The
comparison names each semantic field explicitly. Adding a host-language field to
a runtime representation must not change Genia equality.

Covered by this slice:

| Kind | Equal when |
|---|---|
| boolean | same truth value |
| integer | §4 |
| float | §4 |
| string | same code-point sequence |
| symbol | same symbol name |
| List | same length and equal corresponding elements, in order |
| Pair | equal heads and equal tails |
| `some` | both `some`, equal carried values, equal contexts |
| `none` | both `none`, equal reasons, equal contexts |
| `err` | both `err`, equal reasons, equal contexts |
| represented value | equal facet identity and equal carried value |
| RNG state | equal deterministic state |
| Format | equal template/tag/composition structure |
| bytes | equal byte sequence |
| ZIP entry | equal name and equal byte contents |
| Sheet | equal ordered semantic columns and equal cell values |
| inert closed data descriptor | equal contract-defined immutable fields |

Outcome constructors are never equal across constructor kinds merely because
their contents resemble one another.

Representation layers remain ordered; nesting order and duplicate layers
participate in equality.

Recursion into these contents uses this same relation, not host equality.

### 3.4 Terminal leaves

A value belonging to a family owned by a later slice — maps, identity-bearing
runtime values, opaque semantic tokens, protected carriers — may appear nested
inside a structural value. Equality never follows runtime state behind such a
value. The semantics of comparing those values are established by #792 and #793;
this slice neither defines nor changes them.

### 3.5 Purity

Equality is a pure observation over data already present on the operands. It
must not:

- perform IO or network access
- acquire configuration, secrets, or resources
- declassify protected values
- invoke functions, Templates, matchers, models, providers, token issuers, or
  any user-supplied callback
- consume or advance a Seq or Flow
- dereference a Ref
- inspect Cell, Process, provider, or handle state
- mutate either operand or any reachable runtime state

Equality of a value with itself performs no work that observation of the value
would not already permit.

### 3.6 No host-equality fallback

The relation dispatches on an explicit list of Genia semantic kinds. It has no
final "otherwise, use the host language's equality" branch for unrecognized host
objects. A host object arriving at this boundary is host leakage or misuse and is
governed by existing host-leakage rules; it does not thereby make the host
language's equality part of Genia.

---

## 4. SEMANTICS — numeric equality

Booleans are a distinct semantic kind and never participate in numeric equality.
This holds regardless of any host language in which booleans are represented as
integers.

| Left | Right | Result |
|---|---|---|
| `1` | `1` | true |
| `1` | `2` | false |
| `1` | `1.0` | true |
| `1` | `1.5` | false |
| `true` | `1` | **false** |
| `true` | `true` | true |
| `false` | `0` | **false** |
| `false` | `false` | true |
| `true` | `false` | false |
| `0.0` | `-0.0` | true |
| `+inf` | `+inf` | true |
| `-inf` | `-inf` | true |
| `+inf` | `-inf` | false |
| `NaN` | `NaN` | false |
| `NaN` | any value, including itself | false |

Integer/integer: equal exact mathematical integers.

Float/float: equal mathematical values, with `0.0` and `-0.0` equal, matching
infinities equal, and NaN unequal to everything including itself.

Integer/float bridge: an integer equals a float if and only if the float is
finite, integral, and its exact mathematical value equals the integer. The
comparison is exact in both directions. A conforming host must not decide this by
converting an arbitrary-precision integer into a host floating-point value, nor
by converting a float into an integer with rounding or truncation.

R17 arbitrary-precision integer semantics are unchanged and are not narrowed. A
large integer beyond floating-point precision compares correctly against a float
rather than collapsing to it.

R18 defines no approximate equality and no ordering.

---

## 5. FAILURE

This slice introduces no new error surface.

- kind mismatch → `false`
- NaN comparison → `false`
- no operand is rejected by `==`/`!=` for being of an unusual family

Map-key legality failures are #792. Existing unrelated runtime errors are
unchanged.

No protected payload, opaque-token internal, or referenced runtime state may
appear in any diagnostic produced along an equality path.

---

## 6. INVARIANTS

1. `(a != b)` is exactly `!(a == b)` for all operand pairs.
2. Every structural value covered by §3.3 is reflexive with itself, except where
   it contains NaN in an equality-relevant position.
3. Equality is symmetric: `a == b` and `b == a` agree.
4. Equality is deterministic: repeated comparison of unchanged operands agrees.
5. `true == 1` is `false` and `false == 0` is `false`.
6. `1 == 1.0` is `true`; a large integer not exactly representable as a float is
   not equal to a nearby float.
7. Equality performs no IO, no user code execution, and no state observation
   beyond already-present value contents.
8. Equality never returns a non-boolean.
9. No Core IR, AST, parser, or public language surface changes.
10. R17 integer and map-order semantics are unaffected by this slice.

---

## 7. EXAMPLES

Minimal:

```genia
1 == 1.0        # true
true == 1       # false
false == 0      # false
0.0 == -0.0     # true
1 == 1.5        # false
```

Real:

```genia
[1, 2, 3] == [1, 2.0, 3]           # true
some([1]) == some([1])             # true
some(1) == err(1)                  # false
quote(status) == "status"          # false
err("bad", {"line": 3}) == err("bad", {"line": 3})   # governed by #792 for the map value
```

The last example's map-valued context is deliberately named as a boundary: its
outcome is fixed by #792, not by this slice.

---

## 8. NON-GOALS

- user-overloadable equality, equality protocols, or typeclasses
- approximate float comparison
- total ordering or comparison operators other than `==`/`!=`
- public hashing surface
- deep-diff or structural-difference diagnostics
- map equality or map-key relation
- identity-bearing, opaque-token, or protected-carrier semantics
- token-domain or minting syntax/APIs
- storage or `Revision` implementation
- C++ host implementation
- any new public Genia function or syntax

---

## 9. DOC NOTES

`GENIA_STATE.md` gains no R18 release-truth section in this issue; #796 owns
authoritative R18 wording. This issue must only ensure that no source-of-truth
document is left directly contradicting the behavior it lands — specifically, no
authoritative document may continue to state or exemplify that a boolean equals a
number.

Mark as: **partial** (E18-1 slice of an in-progress release).

---

## 10. FINAL CHECK

- precise and testable: YES
- no implementation details: YES (implementation structure is the design phase)
- no scope expansion beyond #791 and the approved R18 contract: YES
- consistent with `GENIA_STATE.md` as final authority: YES — this contract
  describes behavior to implement, not behavior already implemented
