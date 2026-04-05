# Chapter 05: Lists

## What list helpers are implemented today?

Genia ships a small list-focused stdlib in bundled `std/prelude/list.genia` source.

The runtime loads this bundled prelude through package resources, so the same list stdlib works in both repo execution and installed-package/tool execution.

Core helpers include:

- `list`
- `first`
- `first_opt`
- `last`
- `find_opt`
- `rest`
- `empty?`
- `nil?`
- `append`
- `length`
- `reverse`
- `reduce`
- `map`
- `filter`
- `count`
- `any?`
- `nth`
- `take`
- `drop`
- `range`

Each public helper includes a Markdown docstring readable through `help("name")`.

Current compatibility note:

- `first` remains the legacy non-empty extractor
- `first_opt`, `last`, and `find_opt` are the Option-returning maybe-helpers for lists
- string `find` remains a separate builtin and still returns index-or-`nil`

---

## Option-returning list helpers

Genia now has explicit Option-returning list helpers for maybe-results.

Implemented helpers:

- `first_opt(list)`
- `last(list)`
- `find_opt(predicate, list)`

These return `none` for empty/no-match and `some(value)` for present results, including `some(nil)`.

### Minimal example

```genia
unwrap_or(0, first_opt([1, 2, 3]))
```

Expected result:

```genia
1
```

### Edge case example

```genia
pick(opt) =
  some(x) -> x |
  none -> "missing"

[pick(first_opt([nil])), pick(last([])), pick(find_opt((x) -> x == nil, [1, nil, 2]))]
```

Expected result:

```genia
[nil, "missing", nil]
```

### Failure case example

```genia
find_opt(42, [1, 2, 3])
```

Expected behavior:

- runtime failure because `find_opt` expects a callable predicate

Naming note:

- new `?`-suffixed APIs are boolean-returning
- these maybe-returning helpers therefore do not use `?`
- `get?` remains the current compatibility exception from the earlier Option phase

---

## `map` and `filter` (reduce-driven)

`map` and `filter` are implemented in stdlib using `reduce`.

### Minimal example

```genia
map((x) -> x + 1, [1, 2, 3])
```

Expected result:

```genia
[2, 3, 4]
```

### Edge case example

```genia
filter((x) -> x % 2 == 0, [1, 2, 3, 4, 5])
```

Expected result:

```genia
[2, 4]
```

Order is preserved in output.

Pipeline form (Phase 1):

```genia
[1, 2, 3] |> map(inc)
```

This works through the pipeline rewrite rule `x |> f(y)` → `f(y, x)`.

### Failure case example

```genia
map((x) -> x + 1, 123)
```

Expected behavior:

- runtime match failure, because `reduce` expects list-pattern-compatible input.

---

## CLI args as lists (implemented)

Genia exposes raw CLI args with `argv()`, and that value is just a list of strings.
This means optional positional arguments can use ordinary list patterns.

### Minimal example

```genia
main(args) =
  ([input]) -> ["one", input] |
  ([input, output]) -> ["two", input, output] |
  _ -> "usage"

main(argv())
```

### Edge case example

```genia
main(args) =
  [] -> "no args" |
  [first, ..rest] -> [first, length(rest)]
```

This stays pure list matching with no special CLI variable syntax.

### Failure case example

```genia
cli_parse(1)
```

Expected behavior:

- raises `TypeError` (`cli_parse expected a list of strings`)

---

## `nth`, `take`, and `drop`

### Minimal example

```genia
nth(1, ["a", "b", "c"]) -> "b"
take(2, [1, 2, 3, 4]) -> [1, 2]
drop(2, [1, 2, 3, 4]) -> [3, 4]
```

### Edge case example

```genia
nth(9, [1, 2]) -> nil
take(0, [1, 2]) -> []
drop(0, [1, 2]) -> [1, 2]
```

### Failure case example

```genia
take(2, 42)
```

Expected behavior:

- runtime match failure (second argument is not a list).

---

## `range`

`range` is a recursive stdlib helper that builds numeric lists.

Implemented arities:

- `range(stop)` → delegates to `range(0, stop - 1, 1)`
- `range(start, stop)` → delegates to `range(start, stop, 1)`
- `range(start, stop, step)` → inclusive stop model with explicit step control

### Minimal example

```genia
range(5)
```

Expected result:

```genia
[0, 1, 2, 3, 4]
```

### Edge case example

```genia
range(5, 1, -2)
```

Expected result:

```genia
[5, 3, 1]
```

### Failure case example

```genia
range(1, 5, 0)
```

Expected behavior:

- returns `[]` to avoid non-terminating recursion when step is zero.

---

## Implementation status

### ✅ Implemented

- list literals and list spread
- list-pattern matching with rest patterns
- recursive list helpers in stdlib
- Option-returning list helpers: `first_opt`, `last`, `find_opt`
- `reduce`
- `map` and `filter` as stdlib functions
- `range` helpers for 1-, 2-, and 3-arity calls

### ⚠️ Partial

- list performance is currently interpreter-level; optimizations are selective and pattern-dependent
- maybe-result behavior is still mixed: `first_opt`, `last`, and `find_opt` return Option values, while `nth` still returns `nil` for out-of-range and legacy `first` still expects a non-empty list

### ❌ Not implemented

- lazy sequences
- iterator protocol
- advanced flow/list interop (multi-output stages, async backpressure/cancellation controls)
- built-in map/filter syntax (helpers exist only as stdlib functions)

---

## List-based archive pipelines (Phase 1 bridge)

`zip_entries(path)` currently returns a **list**, so existing list helpers (`map`, `filter`, `count`) work directly.

### Minimal example

```genia
zip_entries("in.zip")
  |> map(entry_name)
```

Expected result:

- list of entry names in archive order

### Edge case example

```genia
zip_entries("in.zip")
  |> map((e) -> e ? entry_json(e) -> entry_name(e) | _ -> nil)
```

Expected behavior:

- preserves list ordering
- emits `nil` for non-JSON entries

### Failure case example

```genia
zip_entries("missing.zip")
```

Expected behavior:

- raises clear file error for unreadable/missing archive path
