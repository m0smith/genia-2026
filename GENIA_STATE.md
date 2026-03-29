# Genia — Current Language State (Main Branch)

> This document defines the **actual, enforced, and intended behavior** of Genia as it exists on the main branch.
>
> Audience:
>
> * AI agents (Codex, ChatGPT)
> * Language implementers
> * Contributors modifying parser, runtime, or syntax
>
> This is the **ground truth**, not a wishlist.

---

# 1. Language Identity

Genia is a:

* Functional-first language
* Expression-oriented language (everything evaluates to a value)
* Runtime-typed language
* Non-whitespace-sensitive language
* Minimal-core, composition-first language

Design priority:

> Reduce ambiguity for both humans and AI while keeping the implementation small.

---

# 2. Execution Model

* Programs are evaluated as expressions
* There are **no statements**
* Every construct returns a value
* Blocks evaluate sequentially and return the last expression

---

# 3. Function Model

## 3.1 Function Definitions

### Expression body

```
inc(x) = x + 1
```

### Case body

```
fact(n) =
  0 -> 1 |
  n -> n * fact(n - 1)
```

### Block body

```
fact(n) {
  log(n)
  0 -> 1 |
  n -> n * fact(n - 1)
}
```

---

## 3.2 Tuple Semantics (Critical)

All function arguments are treated as a **single tuple**.

```
f(x, y)
```

is equivalent to:

```
f((x, y))
```

Implications:

* Pattern matching always targets the full argument tuple
* Multi-argument functions are syntactic sugar

---

# 4. Pattern Matching

## 4.1 Case Structure

Each case:

```
pattern -> result
pattern ? guard -> result
```

Cases are separated by:

```
|
```

---

## 4.2 Evaluation Rules

* Cases are evaluated top-to-bottom
* Pattern must match first
* Guard (if present) must evaluate to true
* First matching case is selected

---

## 4.3 Examples

### Simple

```
fact(n) =
  n ? n <= 1 -> 1 |
  n -> n * fact(n - 1)
```

### Tuple matching

```
add(x, y) =
  (0, y) -> y |
  (x, 0) -> x |
  (x, y) -> x + y
```

### List destructuring

```
sum(list) =
  [] -> 0 |
  [head, ...tail] -> head + sum(tail)
```

---

# 5. Case Expression Placement (Strict)

Case expressions are **NOT general expressions**.

They are ONLY allowed in:

* Function bodies
* Final expression of a block

They are NOT allowed in:

* Subexpressions
* Function arguments
* Lists or maps
* Mid-block positions

---

# 6. Expression Model

## 6.1 Ordinary Expressions

Include:

* Literals
* Identifiers
* Function calls
* Arithmetic
* Comparisons
* Logical operations
* Pipelines
* Lambdas
* Blocks

---

## 6.2 Case Expressions

Separate grammar system.

Symbols reserved for case grammar:

* `->` (pattern mapping)
* `?` (guard)
* `|` (case separator)

These do NOT participate in normal operator precedence.

---

# 7. Operator Precedence (Ordinary Expressions)

From highest → lowest:

1. grouping (), literals, identifiers
2. function calls, indexing, member access
3. unary (-, !)
4. *, /, %
5. +, -
6. comparisons (<, <=, >, >=)
7. equality (==, !=)
8. logical AND (&&)
9. logical OR
10. pipeline

Constraints:

* Comparisons are non-associative
* Equality is non-associative

---

# 8. Lambda Semantics

Lambda form:

```
(x) -> x + 1
```

Important:

* Uses the same `->` symbol as case expressions
* Meaning is determined by context:

  * expression context → lambda
  * case context → pattern mapping

---

# 9. Blocks

```
{
  expr1
  expr2
  expr3
}
```

Rules:

* Expressions are separated by newlines
* Indentation is irrelevant
* Last expression is returned

Constraints:

* At most one case expression per block
* If present, it must be the final expression

---

# 10. Data Types

Core runtime types:

* Number
* String
* Boolean
* Nil
* List
* Map
* Function

---

# 11. Data Processing Model

Unified sequence abstraction.

Core operations:

* map
* filter
* reduce
* take

Example:

```
[1,2,3] |> map(x -> x * 2)
```

---

# 12. I/O Model

* stdin
* stdout
* stderr

Logging:

```
log("message")
```

---

# 13. Error Model (v0.1)

* Pattern match failure → runtime error
* No exception system in core

---

# 14. Structural Constraints (Non-Negotiable)

These must be preserved:

* Case expressions are NOT general expressions
* Pattern matching always targets full tuple
* No indentation-based parsing
* Minimal syntax is preferred over flexibility
* One clear way to express each concept

---

# 15. Known Gaps (Current State)

The following areas are incomplete or evolving:

* Standard library
* Module system
* Error handling model
* AWK-like streaming mode
* Optimization / IR layer
* Compiler backend

---

# 16. Design Philosophy (Enforcement Rules)

All new features must:

1. Reduce ambiguity
2. Keep grammar simple
3. Avoid overlapping concepts
4. Preserve separation of expression types
5. Favor composition over special cases

---

# 17. Mental Model for AI

Genia is best understood as:

* A pattern-matching function engine
* With expression evaluation
* And strict placement rules for control flow

---

# 18. Modification Checklist (For AI + Contributors)

Before implementing a change:

* Does this introduce parsing ambiguity?
* Does it blur case vs expression boundaries?
* Does it duplicate an existing mechanism?
* Can it be expressed via composition instead?

If YES → redesign

---

# END
