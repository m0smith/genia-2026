# E18-4 Reconcile Patterns, Assertions, and Equality-like Surfaces — Contract

ISSUE: #794
STATUS: contract

Narrows the approved parent contract to the E18-4 scope. Behavior only.

---

## 1. PURPOSE

Make "Genia has one equality relation" a property of the implementation rather
than only a statement in the contract, by requiring every remaining surface that
answers a semantic sameness question to give the same answer as `==`.

---

## 2. THE GOVERNING RULE

For any two Genia values `a` and `b`, every surface below answers exactly as
`a == b` does:

1. `==` and `!=` (`!=` is its negation)
2. a literal pattern with literal `a` tested against candidate `b`
3. a repeated pattern binding receiving `a` and `b` for the same name
4. `assert_eq(a, b)` — succeeds exactly when `a == b`
5. the meta-circular evaluator's `==` and `!=` operators
6. map lookup, presence, insertion, replacement, removal, and duplicate-key
   detection, for legal keys
7. Sheet column-name identity, for legal column names
8. recursive List, Pair, Outcome, and represented-value comparison
9. map equality

Items 6, 8, and 9 already hold after #791–#793 and are restated so the invariant
is complete and so a regression in them is a violation of *this* contract too.

No surface may consult a host-language equality, a host container's key rules, or
any separately defined relation to answer such a question.

---

## 3. BEHAVIOR — per surface

### Literal patterns

A literal pattern matches a candidate exactly when the literal and the candidate
are Genia-equal. A `1` literal does not match `true`. A `1` literal does match
`1.0`.

Pattern *mismatch* remains mismatch: a kind difference makes the clause not
match, and never raises.

### Duplicate pattern bindings

When one clause binds the same name more than once, the clause matches exactly
when every value bound to that name is Genia-equal to the others. A clause shaped
like `f(x, x)` accepts `(1, 1.0)` and rejects `(true, 1)`.

Merging bindings for *different* names is unaffected.

### `assert_eq`

`assert_eq(actual, expected)` succeeds exactly when `actual == expected`, and
otherwise fails through the existing failure path with its existing shape. R18
adds no deep-diff diagnostics and changes no message format.

`assert_eq` must never become a protected-payload oracle; comparing protected
carriers observes carrier identity only.

### Meta-circular evaluator operators

The meta-evaluator's `==` and `!=` denote the same relation as the language's own
`==` and `!=`. An expression evaluated through the meta-evaluator and the same
expression evaluated directly agree.

### Sheet column-name identity

Two Sheet column names denote the same column exactly when they are Genia-equal.
Column names that are not Genia-equal are distinct columns and must not be
rejected as duplicates.

The set of values legal as column names is not widened or narrowed by this
issue, and protected values remain rejected as column names.

### Identity-bearing values at these surfaces

Comparing identity-bearing values through any of these surfaces uses identity,
never invocation: a named pattern or Template value compared as a *value* is
never invoked, and a retrieval index handle compared through `==` yields a
boolean by identity rather than raising.

---

## 4. FAILURE

No new error surface, and no existing rejection is loosened except where the
rejection was itself a disagreement with `==`:

- Sheet duplicate-column rejection now triggers on Genia-equal names only. Names
  that merely collided under the old host-container relation are now accepted as
  distinct columns.
- Illegal Sheet column names and illegal map keys keep their existing rejections.

No diagnostic on any of these paths may contain a protected payload.

---

## 5. INVARIANTS

1. Every surface in §2 agrees with `==` for the same operands.
2. No surface consults host-language equality or host container key rules for a
   semantic question.
3. Literal-pattern and duplicate-binding mismatches remain mismatches, not errors.
4. `assert_eq` succeeds exactly when `==` is true, with its existing failure shape.
5. Meta-evaluated and directly evaluated equality agree.
6. Genia-equal Sheet column names are the same column; unequal ones are distinct.
7. No surface invokes a matcher, Template, or user function to decide equality.
8. No surface discloses a protected payload.
9. No new pattern syntax, public function, open-function semantics, or Core IR
   node is added.
10. R17 map order and the R18 relation itself are unchanged.

---

## 6. EXAMPLES

```genia
dup(a, b) =
  (x, x) -> "same" |
  (a, b) -> "diff"

dup(1, 1.0)     # "same"
dup(true, 1)    # "diff"
```

```genia
lit(v) =
  (1) -> "one" |
  (v) -> "other"

lit(1.0)    # "one"
lit(true)   # "other"
```

```genia
assert_eq(utf8_encode("hi"), utf8_encode("hi"))   # succeeds
assert_eq({"a": 1}, {"a": 1})                     # succeeds
assert_eq(true, 1)                                # fails
```

```genia
eval(quote(true == 1), empty_env())   # false, agreeing with true == 1
```

---

## 7. NON-GOALS

New pattern syntax; open functions or extensible dispatch; user-overloadable
equality; domain-specific equivalence predicates; deep-diff diagnostics; changes
to the relation itself; widening legal map keys or Sheet column names; C++ host.

---

## 8. DOC NOTES

`GENIA_STATE.md` must record that these surfaces now share one relation, and the
E18 not-yet-landed list becomes empty. Any documentation or example implying a
literal pattern matches across boolean/number kinds must be corrected. Mark as
**partial** until E18-6 consolidates release truth.

---

## 9. FINAL CHECK

Precise and testable; no implementation detail; no scope expansion; consistent
with `GENIA_STATE.md` as final authority.
