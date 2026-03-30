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
inc(x) = "# inc\n\nIncrement a number by one." x + 1
```

The string is metadata for the named function group, not a normal runtime expression.
Docstrings are rendered by `help(...)` as lightweight Markdown text.

You can inspect it with:

```genia
help("inc")
```

### Recommended docstring shape

Use short Markdown sections when they add value:

```genia
sum(xs) = "# sum\n\nAdd all numbers in `xs`.\n\n## Params\n\n* `xs`: list of numbers\n\n## Examples\n\n```genia\nsum([1, 2, 3]) -> 6\n```" 0
```

---

## Edge Case Example

Multiple clauses can share one canonical docstring:

```genia
echo() = "# echo\n\nReturn value unchanged." nil
echo(x) = "# echo\n\nReturn value unchanged." x
```

This is valid (same docstring text).

---

## Failure Case Example

Conflicting docstrings across clauses raise a clear error:

```genia
echo() = "first doc" nil
echo(x) = "second doc" x
```

Expected behavior: runtime `TypeError` for conflicting function docstrings.

---

## Implementation Status

### ✅ Implemented

* Named function definitions
* Arity-based + varargs dispatch
* Named-function docstring metadata (`f(...) = "doc" ...`)
* `help(name)` output with:
  * signature header (`name/shape`)
  * source location when available
  * Markdown-aware docstring rendering (headings/lists/inline code/fenced code blocks)
  * undocumented fallback (`No documentation available.`)

### ⚠️ Partial

* Markdown rendering is intentionally minimal and terminal-first (no full Markdown engine, no syntax highlighting)
* Docstring parsing requires the docstring and body expression to be part of the same definition expression sequence (no dedicated block-doc syntax)

### ❌ Not implemented

* Lambda docstrings
* Separate docstring keywords or block syntax
