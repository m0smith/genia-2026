# Note: Examples in this chapter are validated by the Semantic Spec System where covered. Currently, only the eval category is active for executable shared spec files; other categories are scaffold-only. See GENIA_STATE.md for authoritative status.
# Chapter 02: Pattern Matching

## The Question

How does Genia choose which branch runs?

---

## The Smallest Example

```
head([1, 2, 3]) -> 1
```
Classification: **Likely valid** (not directly tested)

This looks simple, but something important is happening:

Genia is not *checking conditions*.

It is **matching shapes**.

---

## Another Example

```
head([x, .._]) -> x
```
Classification: **Likely valid** (not directly tested)

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

nth(0, [x, .._]) -> x |
nth(n, [_, ..rest]) -> nth(n - 1, rest)
## A Slightly Harder Example

```
nth(0, [x, .._]) -> x |
nth(n, [_, ..rest]) -> nth(n - 1, rest)
```
Classification: **Likely valid** (not directly tested)

This defines `nth`:

* If index is `0`, return the first element
* Otherwise:

  * Skip the first element
  * Recurse with `n - 1`

No conditionals needed.

---

## Map patterns (implemented)

Map patterns match required keys in persistent map values.

### Minimal example

```genia
greet(person) =
  ({ name }) -> "Hello " + name
```
Classification: **Likely valid** (not directly tested)

`{ name }` is shorthand for `{ name: name }`.

### Edge case example

```genia
describe(person) =
  ({ "name": name, age: years, city, }) -> [name, years, city]
```
Classification: **Likely valid** (not directly tested)

Map patterns are partial by default: extra keys are allowed.  
All listed keys must be present.

### Failure case example

```genia
bad(person) =
  ({ "name" }) -> person
```
Classification: **Likely valid** (not directly tested)

Expected behavior: syntax error (shorthand is only allowed for identifier keys; string keys must use `:`).

---

## Multiline list patterns (implemented)

List pattern shapes can span lines inside `[...]`.

### Minimal example

```genia
first3(xs) =
  [
    a, b, c,
    .._
  ] -> [a, b, c]
```
Classification: **Likely valid** (not directly tested)

### Edge case example

```genia
head_or_none(xs) =
  [
    x,
    .._
  ] -> x |
  [] -> "none"
```
Classification: **Likely valid** (not directly tested)

### Failure case example

```genia
bad(xs) =
  [
    a,
    ..rest,
    b
  ] -> a
```
Classification: **Likely valid** (not directly tested)

Expected behavior: parse error (`..rest must be the final item in a list pattern`).

---

## Glob String Patterns (Phase 1)

Genia supports a minimal glob pattern form in pattern position:

```
glob"..."
```

This is still pattern matching (not regex, not captures).

### Minimal example

```genia
kind(name) =
  glob"*.md" -> "markdown" |
  _ -> "other"
```
Classification: **Likely valid** (not directly tested)

### Edge case example

```genia
kind(s) =
  glob"" -> "empty" |
  glob"*" -> "any" |
  _ -> "fallback"
```
Classification: **Likely valid** (not directly tested)

- `glob""` matches only `""`
- `glob"*"` matches every string, including `""`

### Failure case example

Malformed classes fail deterministically:

```genia
bad(s) =
  glob"[a-z" -> "nope" |
  _ -> "ok"
```
Classification: **Likely valid** (not directly tested)

Expected behavior: syntax error for unterminated character class.

Supported glob features in this phase:

- `*` (zero or more chars)
- `?` (exactly one char)
- class: `[abc]`
- range: `[a-z]`
- negated class: `[!abc]`
- escapes: `\*`, `\?`, `\[`, `\]`, `\\`

Not part of this phase:

- regex
- extglob
- captures/destructuring

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

## Interpreter / Compiler View (Implemented)

Current runtime behavior is implemented as:

* Parsed case/function patterns lower into explicit Core IR pattern nodes.
* Matching runs sequentially, top-to-bottom.
* Structural comparison + variable-binding environments are used at runtime.
* Duplicate bindings (like `[x, x]`) require equal values at match time.

Current optimization scope:

* A narrow recognized recursion shape (nth-style list traversal) may lower further to a specialized loop IR node.

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

## Pattern matching with Option values (phase 1)

Option values can be matched directly with literal and constructor patterns.

Legacy surface `nil` is still accepted, but it immediately normalizes to `none("nil")`.
Pattern matching therefore sees one absence family at runtime.

Modern Genia code usually gets these Option values from canonical helpers such as:

- `get`
- `first`
- `last`
- `nth`
- string `find`
- `find_opt`

Current scope:

- Option constructors are supported in pattern matching (`some(pattern)`)
- structured absence patterns are supported (`none(reason)`, `none(reason, context)`)
- this does not imply general ADT constructor-pattern support in this phase

### Minimal example

```genia
fallback(opt) =
  none -> "missing" |
  some(_) -> "present"
```
Classification: **Likely valid** (not directly tested)

`none` is a literal pattern and matches only the Option none value, not `nil`.

In current runtime terms, that means it matches normalized absence values such as:

- `none("nil")`
- `none("empty-list")`
- `none("missing-key", {...})`

### Edge case example

```genia
pick_name(opt) =
  none("empty-list") -> "empty" |
  some({name}) -> name |
  some(_) -> "unknown"

pick_name(last([]))
```
Classification: **Likely valid** (not directly tested)

Constructor-pattern matching composes with existing map/list patterns.

### Failure case example

```genia
bad(opt) =
  none(a, b, c) -> a
```
Classification: **Likely valid** (not directly tested)

Expected behavior:

- syntax error (`none(...)` pattern accepts at most reason and context)

### Implementation status

### ✅ Implemented

- literal matching on `none`
- structured matching on `none(reason)` and `none(reason, context)`
- constructor matching on `some(pattern)`
- Option-returning helpers such as `first`, `last`, `nth`, string `find`, and `find_opt` can be matched the same way as `get`
- guard-friendly Option checks (`is_some?`, `is_none?`, `some?`, `none?`) remain available

### ⚠️ Partial

- `some(pattern)` supports exactly one inner pattern
- `none(reason)` and `none(reason, context)` match structured absence, but this is still limited to the Option family rather than general constructor-pattern matching
- no general `value ? ...` expression form exists; Option matching still happens through ordinary function/case-pattern positions

### ❌ Not implemented

- multi-argument option constructor patterns beyond current Option forms (`some(a, b)`, `none(a, b, c)`)

---

## Implementation Status

### ✅ Implemented

* Basic pattern matching
* Ordered evaluation
* List destructuring (`[x, ..rest]`)
* Map destructuring (`{name}`, `{name: n}`, mixed forms)
* Variable binding
* Pattern guards (`pattern ? guard -> result`)
* Glob string patterns (`glob"..."`) with whole-string matching only
* Glob class/range/negated-class matching and minimal escapes

### ⚠️ Partial

* Error messages for failed matches may be minimal
* Glob parsing is intentionally small (no regex/extglob/capture syntax)

### ❌ Missing

* Exhaustiveness checking
* Match optimizations (decision trees, indexing)
* Regex patterns, extglob operators, or capture extraction in glob patterns

---

## Conditionals in Genia

Genia has no dedicated conditional keyword.

* Genia does **not** use `if` or `switch`
* All conditional logic is expressed via pattern matching
* Pattern matching is the only branching mechanism

---

## CLI parsing + pattern matching

Genia keeps CLI handling list-first:

- raw args: `argv()` (host-backed list of strings)
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
Classification: **Likely valid** (not directly tested)

### Edge case example

Use `--` to stop option parsing:

```genia
cli_parse(["--pretty", "--", "--literal"])
```
Classification: **Likely valid** (not directly tested)

Expected positional remainder includes `"--literal"`.

### Failure case example

```genia
cli_parse(["-ab"], map_put(map_new(), "options", ["a", "b"]))
```
Classification: **Likely valid** (not directly tested)

Expected behavior:

- deterministic `ValueError` for ambiguous grouped short option parsing.

### CLI parsing status

### ✅ Implemented

* list-first raw args via `argv()`
* prelude-backed `cli_parse(args)` and minimal `cli_parse(args, spec)`
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
* Glob string patterns: YES
* Guards: YES
* Exhaustiveness checking: NO

<!-- GENERATED:pattern-matching-status:end -->
