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
inc(x) = """
# inc

Increment a number by one.
""" x + 1
```

The string is metadata for the named function group, not a normal runtime expression.
Docstrings are rendered by `help(...)` as lightweight Markdown text.
Docstrings are allowed for **named functions only** (not lambdas).

You can inspect it with:

```genia
help("inc")
```

---

## Official Docstring Style Guide

Use this guide for new or updated public named functions.

### What a docstring is in Genia

* A string literal placed immediately after `=` in a named function definition.
* Attached as metadata for `help(...)`.
* Not evaluated as part of the function body expression.

### Where docstrings are allowed

* ✅ Named functions
* ❌ Lambdas

### Markdown support (implemented subset)

`help(...)` currently preserves and normalizes lightweight Markdown structure:

* Headings (`#`, `##`)
* Bullet lists (`-` or `*`)
* Inline code (`` `like_this` ``)
* Fenced code blocks (```genia ... ```)
* Paragraph spacing (extra blank lines are collapsed)

This is terminal-first formatting, not a full Markdown rendering engine.

### Canonical multi-clause rule

For a single named function group (same name across clauses):

* no docstrings → undocumented function
* one total docstring across clauses → documented function
* repeated identical docstrings across clauses → valid
* conflicting docstrings across clauses → runtime `TypeError`

### How `help` displays docstrings

`help("name")` prints:

1. function signature header (`name/shape`)
2. source location (`Defined at file:line`) when available
3. rendered docstring, or `No documentation available.`

---

## Official Templates

### Minimal template

```text
"""
One-line summary.
"""
```

### Standard template

```text
"""
# function-name

One-line summary.

Optional short description.

## Params

* `param`: description

## Returns

* description

## Examples

```genia
example() -> result
```

## Edge cases

* description

## Failure

* description
"""
```

Use these templates as the **content** of the string literal docstring.

---

## Usage Guidelines

### When to use minimal vs standard

* Use **minimal** for tiny helpers with obvious behavior.
* Use **standard** for most public stdlib-style functions.

### Keep docstrings concise

* Lead with one clear summary sentence.
* Add sections only when they improve understanding.

### Avoid redundant documentation

Avoid repeating things that are obvious from the function name/signature.

### Include examples for public functions

Most public functions should have at least one realistic example.

### Include edge/failure sections when behavior is non-trivial

Add `## Edge cases` and `## Failure` when:

* behavior depends on special inputs, or
* runtime errors are expected for invalid input.

### Avoid overdocumentation

If a section adds no new information, omit it.

---

## Real Examples (Valid Genia Syntax)

### 1) Simple function

```genia
inc(x) = "\"\"\"\n# inc\n\nIncrement `x` by one.\n\n## Params\n\n* `x`: number\n\n## Returns\n\n* number\n\n## Examples\n\n```genia\ninc(4) -> 5\n```\n\"\"\"" x + 1
```

### 2) Recursive function

```genia
fact(n) = "\"\"\"\n# fact\n\nCompute factorial recursively.\n\n## Params\n\n* `n`: non-negative integer\n\n## Returns\n\n* factorial of `n`\n\n## Examples\n\n```genia\nfact(5) -> 120\n```\n\n## Edge cases\n\n* `fact(0)` returns `1`\n\n## Failure\n\n* this version does not include an explicit negative-input guard\n\"\"\"" (
  0 -> 1 |
  n -> n * fact(n - 1)
)
```

### 3) Pattern-matching multi-clause function

All clauses must use the same canonical docstring text (or only one clause provides it):

```genia
sign(0) = "\"\"\"\n# sign\n\nClassify a number by sign.\n\"\"\"" 0
sign(n) = "\"\"\"\n# sign\n\nClassify a number by sign.\n\"\"\"" (
  n > 0 -> 1 |
  _ -> -1
)
```

### 4) Stdlib-style helper

```genia
sum(xs) = "\"\"\"\n# sum\n\nAdd all numbers in `xs`.\n\n## Params\n\n* `xs`: list of numbers\n\n## Returns\n\n* total as number\n\n## Examples\n\n```genia\nsum([1, 2, 3]) -> 6\nsum([]) -> 0\n```\n\"\"\"" (
  [] -> 0 |
  [x, ..rest] -> x + sum(rest)
)
```

---

## `help` Output Examples

### Documented function

Given:

```genia
inc(x) = "\"\"\"\n# inc\n\nIncrement `x` by one.\n\"\"\"" x + 1
help("inc")
```

Typical output:

```text
inc/1
Defined at demo.genia:1

# inc

Increment `x` by one.
```

### Undocumented function

Given:

```genia
plain(x) = x
help("plain")
```

Typical output:

```text
plain/1
Defined at demo.genia:1

No documentation available.
```

---

## Pipeline Operator (Phase 1)

Genia now supports a minimal pipeline operator for left-to-right function composition:

`left |> right`

Rewrite rules (implemented):

* `x |> f` becomes `f(x)`
* `x |> f(y)` becomes `f(y, x)` (the piped value is appended as the final argument)
* chaining is left-associative: `a |> f |> g` becomes `g(f(a))`

### Minimal example

```genia
inc(x) = x + 1
4 |> inc
```

Result:

```genia
5
```

### Edge case example

```genia
pair(a, b) = [a, b]
9 |> pair(1)
```

Result:

```genia
[1, 9]
```

Pipeline-friendly API design note:

- With current rewrite semantics (`x |> f(y)` => `f(y, x)`), functions that are commonly terminal pipeline steps often use destination/config args first.
- Example: `entries |> zip_write("out.zip")` calls `zip_write("out.zip", entries)` in this phase.

### Failure case example

```genia
1 |> 2
```

Expected behavior:

* runtime `TypeError` because `2` is not callable.

---

## Implementation Status

### ✅ Implemented

* Named function definitions
* Arity-based + varargs dispatch
* Runtime `main` entrypoint convention in file/`-c` modes:
  * `main/1` is preferred and called as `main(argv())`
  * fallback to `main/0` when `main/1` is absent
* Pipeline operator `|>` with expression-level call rewriting
* Named-function docstring metadata (`f(...) = "doc" ...`)
* `help(name)` output with:
  * signature header (`name/shape`)
  * source location when available
  * Markdown-aware docstring rendering (headings/lists/inline code/fenced code blocks)
  * undocumented fallback (`No documentation available.`)

### ⚠️ Partial

* Markdown rendering is intentionally minimal and terminal-first (no full Markdown engine, no syntax highlighting)
* Docstring parsing requires the docstring and body expression to be part of the same definition expression sequence (no dedicated block-doc syntax)
* Pipeline is only call composition, not a full flow runtime model
* `main` auto-invocation is only for file/`-c` execution modes (not REPL)

### ❌ Not implemented

* Lambda docstrings
* Separate docstring keywords or block syntax
* Dedicated CLI syntax (`$1`, `$2`, special argument keywords)
* Generalized flow semantics (lazy streams, multi-output stages, backpressure, cancellation)

---

## CLI Entrypoint with `main` (Runtime Convention)

`main` is just a normal function name with runtime convention behavior in file/`-c` execution.
No parser syntax is added.

### Minimal example

```genia
main(args) = length(args)
```

When run with two trailing args, this returns `2`.

### Edge case example

```genia
main() = "ok"
```

If `main/1` is absent, `main/0` is called automatically.

### Failure case example

```genia
main(args) = args
main() = "fallback"
```

`main/1` has precedence, so this returns the argv list rather than `"fallback"`.
