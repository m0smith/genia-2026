# Genia — Compiler & Language Invariants (DO NOT BREAK)

> This document defines **non-negotiable invariants** for the Genia language.
>
> Audience:
>
> * AI agents (Codex, ChatGPT)
> * Parser / compiler implementers
> * Contributors modifying syntax or semantics
>
> If a change violates any rule in this document, it MUST be rejected or redesigned.

---

# 1. Core Principle

Genia prioritizes:

> **Clarity over flexibility**

and

> **Unambiguous parsing over expressive shortcuts**

---

# 2. Expression vs Case Separation (CRITICAL)

## RULE 1

Case expressions are NOT ordinary expressions.

They exist in a separate grammar layer.

## MUST NOT

* Treat `->` as a general infix operator
* Allow `|` outside case expressions
* Allow `?` outside case guard context

## CONSEQUENCE

Parser must:

* Detect case context explicitly
* Never attempt to interpret case syntax inside expression parsing

---

# 3. Case Expression Placement (HARD RULE)

## RULE 2

Case expressions are ONLY allowed in:

* Function bodies
* Final position in a block

## MUST NOT

* Appear in subexpressions
* Appear as function arguments
* Appear inside lists or maps
* Appear before other expressions in a block

## CONSEQUENCE

Parser MUST reject:

```
x + (0 -> 1 | n -> n)
```

```
f(0 -> 1 | n -> n)
```

```
{
  0 -> 1 |
  n -> n
  log(x)
}
```

---

# 4. Single Case Expression Per Block

## RULE 3

A block may contain:

* zero or more ordinary expressions
* at most ONE case expression

If present:

* it MUST be the final expression

---

# 5. Tuple Matching Model (CRITICAL)

## RULE 4

All pattern matching operates on the FULL argument tuple.

Even for:

```
f(x)
```

Matching target is:

```
(x)
```

## MUST NOT

* Match partial arguments implicitly
* Introduce alternative matching targets

---

# 6. Lambda vs Case Arrow Disambiguation

## RULE 5

`->` has TWO meanings, resolved by context ONLY:

* Expression context → lambda
* Case context → pattern mapping

## MUST NOT

* Use precedence to resolve ambiguity
* Allow mixed interpretation in the same parse position

## CONSEQUENCE

Parser must decide BEFORE parsing `->`:

* Are we in expression mode?
* Or case mode?

---

# 7. Block Semantics

## RULE 6

Blocks:

* Are NOT indentation-sensitive
* Use newlines as expression separators
* Return the last expression

## MUST NOT

* Use indentation for structure
* Require semicolons

---

# 8. Operator Simplicity

## RULE 7

Operators must remain simple and predictable.

## MUST NOT

* Introduce new operators that overlap existing meaning
* Reuse symbols already assigned to case grammar

---

# 9. Non-Associative Comparisons

## RULE 8

These are invalid unless explicitly supported later:

```
a < b < c
```

```
a == b == c
```

Parser must reject them.

---

# 10. Minimal Core Guarantee

## RULE 9

The core language must remain minimal.

## MUST NOT

* Add features that duplicate existing capability
* Add alternate syntax for the same concept

---

# 11. No Hidden Semantics

## RULE 10

All behavior must be explicit in syntax.

## MUST NOT

* Introduce implicit conversions that affect control flow
* Introduce hidden evaluation rules

---

# 12. Error Model (v0.1 Constraint)

## RULE 11

Pattern match failure MUST produce a runtime error.

## MUST NOT

* Silently continue
* Fall through to undefined behavior

---

# 13. Grammar Simplicity Constraint

## RULE 12

Grammar must remain:

* Layered (expression vs case)
* Predictable
* Small

## MUST NOT

* Merge case grammar into expression grammar
* Create ambiguous productions

---

# 14. AI Interpretability Constraint

## RULE 13

The language must remain easy for LLMs to reason about.

## MUST NOT

* Introduce syntax requiring global inference
* Introduce context-sensitive ambiguity

---

# 15. Feature Acceptance Test

Before accepting any feature, it MUST pass:

1. Does this reduce ambiguity?
2. Does this simplify parsing?
3. Does this preserve grammar separation?
4. Can this be expressed via composition instead?

If ANY answer is "no" → reject or redesign

---

# 16. Parser Enforcement Requirements

The parser MUST:

* Reject invalid case placement
* Reject ambiguous constructs
* Enforce tuple matching rules
* Distinguish lambda vs case early

---

# 17. Final Principle

> If a feature makes the language harder to explain in one paragraph, it does not belong in the core.

---

# END
