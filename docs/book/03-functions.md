# Chapter 03: Functions

## The Smallest Example

```genia
inc(x) = x + 1
```

Named functions are values and dispatch by name + arity shape.

---

## Function Docstrings (Implemented)

A named function may include a leading docstring string literal after `=`:

```genia
inc(x) = "Increment a number by one." x + 1
```

The string is metadata for the named function group, not a normal runtime expression.

You can inspect it with:

```genia
help("inc")
```

---

## Edge Case Example

Multiple clauses can share one canonical docstring:

```genia
echo() = "Return value unchanged." nil
echo(x) = "Return value unchanged." x
```

This is valid (same docstring text).

---

## Failure Case Example

Conflicting docstrings across clauses raise a clear error:

```genia
echo() = "First doc." nil
echo(x) = "Second doc." x
```

Expected behavior: runtime `TypeError` for conflicting function docstrings.

---

## Implementation Status

### ✅ Implemented

* Named function definitions
* Arity-based + varargs dispatch
* Named-function docstring metadata (`f(...) = "doc" ...`)
* `help(name)` metadata output (name, arities, docstring when present, source when available)

### ⚠️ Partial

* Docstring parsing currently requires the docstring and body expression to be part of the same definition expression sequence (no dedicated block-doc syntax)

### ❌ Not implemented

* Lambda docstrings
* Separate docstring keywords or block syntax
