# Chapter 02: Pattern Matching

## The Question

How does Genia choose which branch runs?

---

## The Smallest Example

```
head([1, 2, 3]) -> 1
```

This looks simple, but something important is happening:

Genia is not *checking conditions*.

It is **matching shapes**.

---

## Another Example

```
head([x, .._]) -> x
```

This says:

* If the input is a list
* With at least one element
* Bind the first element to `x`
* Ignore the rest

Then return `x`.

---

## What Is Really Happening

When a function is called, Genia:

1. Takes the input
2. Tries each pattern **in order**
3. Stops at the **first match**
4. Executes the corresponding result

There is no fallback logic beyond pattern matching.

Order matters.

---

## The Shape of the Rule

All pattern matching in Genia follows this structure:

```
pattern -> result
```

With multiple cases:

```
pattern1 -> result1 |
pattern2 -> result2 |
pattern3 -> result3
```

Evaluation is **top to bottom**.

---

## A Slightly Harder Example

```
nth(0, [x, .._]) -> x |
nth(n, [_, ..rest]) -> nth(n - 1, rest)
```

This defines `nth`:

* If index is `0`, return the first element
* Otherwise:

  * Skip the first element
  * Recurse with `n - 1`

No conditionals needed.

---

## A Failure Case

```
head([]) -> ?
```

There is no matching pattern.

Result:

👉 Runtime error

Genia does not silently fail or return null.

---

## A Subtle Edge Case

```
nth(0, []) -> ?
```

Even though `0` matches, the list pattern does not.

Patterns must match **completely**, not partially.

---

## Interpreter / Compiler View

Internally, pattern matching is likely implemented as:

* Sequential pattern checks
* Structural comparisons
* Variable binding environments

Potential optimizations:

* Pattern indexing
* Decision trees
* Match flattening

---

## Common Pitfall

**Forgetting order matters**

```
f(x) -> 1 |
f(0) -> 2
```

This will NEVER return `2`.

The first pattern always matches.

Correct version:

```
f(0) -> 2 |
f(x) -> 1
```

---

## Exercises

### 1. Easy

Write a function:

```
isEmpty([])
isEmpty([x, .._])
```

---

### 2. Medium

Write:

```
second([a, b, .._])
```

---

### 3. Tricky

Write `last` using pattern matching and recursion.

---

## Implementation Status

### ✅ Implemented

* Basic pattern matching
* Ordered evaluation
* List destructuring (`[x, ..rest]`)
* Variable binding
* Pattern guards (`pattern ? guard -> result`)

### ⚠️ Partial

* Error messages for failed matches may be minimal

### ❌ Missing

* Exhaustiveness checking
* Match optimizations (decision trees, indexing)

---

## Conditionals in Genia

Genia has no dedicated conditional keyword.

* Genia does **not** use `if` or `switch`
* All conditional logic is expressed via pattern matching
* Pattern matching is the only branching mechanism

---

## CLI parsing + pattern matching

Genia keeps CLI handling list-first:

- raw args: `argv()` (list of strings)
- parsed args: `cli_parse(args)` -> `[opts, positionals]`

You can parse flags/options first, then pattern match the remaining positional list.

### Minimal example

```genia
main(args) =
  run_parsed(cli_parse(args))

run_parsed(parsed) =
  ([opts, [input]]) -> [cli_flag?(opts, "pretty"), input] |
  ([opts, [input, output]]) -> [cli_flag?(opts, "pretty"), input, output] |
  _ -> "usage"
```

### Edge case example

Use `--` to stop option parsing:

```genia
cli_parse(["--pretty", "--", "--literal"])
```

Expected positional remainder includes `"--literal"`.

### Failure case example

```genia
cli_parse(["-ab"], map_put(map_new(), "options", ["a", "b"]))
```

Expected behavior:

- deterministic `ValueError` for ambiguous grouped short option parsing.

### CLI parsing status

### ✅ Implemented

* list-first raw args via `argv()`
* `cli_parse(args)` and minimal `cli_parse(args, spec)`
* helper readers: `cli_flag?`, `cli_option`, `cli_option_or`
* no parser changes required for CLI support

### ⚠️ Partial

* `spec` support is intentionally small: `flags`, `options`, `aliases`
* no advanced argparse-style validation/actions

### ❌ Missing

* `$1`, `$2`, `$NF`, `ARGV`, or any special positional-variable syntax
* shell tokenization/quoting logic (Genia operates on host-tokenized args)
* full argparse/subcommand system

---

## Notes for Contributors

* Pattern matching is the **core abstraction** of Genia
* Any feature that introduces branching should integrate with this model
* Avoid adding alternative conditional constructs
* Function docstrings are metadata only and must not change case/pattern semantics

---

## Generated Status

<!-- GENERATED:pattern-matching-status:start -->

Source: parser + runtime

* Pattern clauses supported: YES
* Ordered evaluation: YES
* List destructuring: YES
* Guards: YES
* Exhaustiveness checking: NO

<!-- GENERATED:pattern-matching-status:end -->
