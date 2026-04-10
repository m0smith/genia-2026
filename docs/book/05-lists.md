# Chapter 05: Lists

## What list helpers are implemented today?

Genia currently has two list-like data families:

- ordinary list values such as `[1, 2, 3]`
- pair-built lists such as `cons(1, cons(2, nil))`

These are distinct in the current runtime.

- ordinary list literals stay ordinary list values
- quoted lists use pair chains ending in `nil`
- `pair?([1, 2])` is `false`

Genia ships a small list-focused stdlib in bundled `src/genia/std/prelude/list.genia` source.

The runtime loads this bundled prelude through package resources, so the same list stdlib works in both repo execution and installed-package/tool execution.

Core helpers include:

- `list`
- `first`
- `last`
- `find_opt`
- `nth`
- `take`
- `drop`
- `range`
- compatibility aliases:
  - `first_opt`
  - `nth_opt`
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

Each public helper includes a Markdown docstring readable through `help("name")`.

Current compatibility note:

- `first`, `last`, and `nth` are canonical maybe-returning list access helpers
- `first_opt` and `nth_opt` remain compatibility aliases
- `find_opt` is the canonical maybe-returning predicate-search helper for lists
- string `find` is a separate canonical maybe-returning string-search builtin
- new examples should prefer `first` / `last` / `nth` over `first_opt` / `nth_opt`

---

## Pairs and pair-built lists

Pairs are the SICP-style list substrate in current Genia.

Available primitives:

- `cons`
- `car`
- `cdr`
- `pair?`
- `null?`

### Minimal example

```genia
xs = cons(1, cons(2, cons(3, nil)))
[car(xs), car(cdr(xs))]
```

Expected result:

```genia
[1, 2]
```

### Edge case example

```genia
[pair?(cons(1, nil)), null?(nil), pair?([1, 2])]
```

Expected result:

```genia
[true, true, false]
```

### Failure case example

```genia
cdr(42)
```

Expected behavior:

- raises `TypeError` because `cdr` expects a pair

Current note:

- pair-built lists end in `nil`
- ordinary list helpers such as `map`, `filter`, `take`, and `drop` still operate on ordinary list values in this phase
- quoted list syntax uses pair chains, which makes `quote([a, b, c])` produce symbolic pair data

---

## Delayed pair tails

Promises make stream-like pair structures possible without using Flow.

### Status

✅ Implemented

- promises can appear in pair tails
- `force(cdr(pair))` works
- successful forcing is memoized

⚠️ Partial

- there is no full stream stdlib in this phase
- forcing is explicit; tails are not forced automatically

❌ Missing

- lazy list literals
- stream-specific pattern matching

### Minimal example

```genia
stream_head(s) = car(s)
stream_tail(s) = force(cdr(s))

s = cons(1, delay(cons(2, nil)))
[stream_head(s), car(stream_tail(s))]
```

Expected result:

```genia
[1, 2]
```

### Edge case example

```genia
ones() = cons(1, delay(ones()))
s = ones()
[car(s), car(force(cdr(s))), car(force(cdr(force(cdr(s)))))]
```

Expected result:

```genia
[1, 1, 1]
```

### Failure case example

```genia
force(cdr(cons(1, 2)))
```

Expected result:

```genia
2
```

This is not an error because `force(x)` returns non-promise values unchanged.

---

## Canonical maybe-returning list access

Genia now has a canonical maybe-returning list access surface for maybe-results.

Implemented helpers:

- `first(list)`
- `first_opt(list)` (compatibility alias)
- `last(list)`
- `nth(index, list)`
- `nth_opt(index, list)` (compatibility alias)
- `find_opt(predicate, list)`
- explicit chaining helpers over canonical access:
  - `then_first(target)`
  - `then_nth(index, target)`

These return `none...` for empty/no-match/out-of-range and `some(value)` for present results, including present legacy-`nil` values.
In current runtime output, legacy `nil` normalizes to `none("nil")`, so a present `nil` element appears as `some(none("nil"))`.

Current structured absence reasons in this layer:

- `first([])` and `last([])` -> `none("empty-list")`
- `find_opt(pred, xs)` with no match -> `none("no-match")`
- `nth(i, xs)` out of range -> `none("index-out-of-bounds", { index: i, length: n })`

### Minimal example

```genia
unwrap_or(0, first([1, 2, 3]))
```

Expected result:

```genia
1
```

### Edge case example

```genia
pick(opt) =
  some(x) -> x |
  none("empty-list") -> "empty" |
  none(_) -> "missing"

[pick(first([nil])), pick(last([])), pick(find_opt((x) -> none?(x), [1, nil, 2])), absence_reason(nth(9, [1, 2]))]
```

Expected result:

```text
[none("nil"), "empty", none("nil"), some("index-out-of-bounds")]
```

Rendered absence values keep their structure visible in tooling:

```genia
[first([]), nth(9, [1, 2])]
```

Expected rendered result:

```text
[none("empty-list"), none("index-out-of-bounds", {index: 9, length: 2})]
```

### Failure case example

```genia
find_opt(42, [1, 2, 3])
```

Expected behavior:

- runtime failure because `find_opt` expects a callable predicate

Naming note:

- new `?`-suffixed APIs are boolean-returning
- canonical maybe-returning helpers therefore do not use `?`
- `get?` remains the current compatibility exception from the earlier Option phase
- compatibility aliases retained in this phase:
  - `first_opt` -> `first`
  - `nth_opt` -> `nth`
- list predicate search remains canonically named `find_opt` in this phase

Maybe-flow note:

- list helpers often act as the first maybe-aware step in an Option-aware pipeline
- example:
  ```genia
  unwrap_or(0, fields("a b c d 5 x") |> nth(5) |> flat_map_some(parse_int))
  ```
- this works because `nth` returns `some("5")`, pipelines preserve that explicit Option, and `flat_map_some(parse_int)` applies `parse_int` to the wrapped value
- direct chaining also composes with list results:
  ```genia
  data = { items: [{ name: "A" }, { name: "B" }] }
  unwrap_or("?", data |> get("items") |> then_nth(0) |> then_get("name"))
  ```
- and:
  ```genia
  data = { users: [] }
  result = data |> get("users") |> then_first() |> then_get("email")
  [absence_reason(result), is_none?(result)]
  ```
- explicit helpers such as `then_first` and `then_nth` are the canonical bridge when a prior stage has already produced an explicit Option value

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

This works through the pipeline stage-call rule `x |> f(y)` → `f(y, x)`.

### Failure case example

```genia
map((x) -> x + 1, 123)
```

Expected behavior:

- runtime match failure, because `reduce` expects list-pattern-compatible input.

---

## CLI args as lists (implemented)

Genia exposes raw CLI args with host-backed `argv()`, and that value is just a list of strings.
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

Current note:

- `argv()` is the raw host-backed capability boundary
- public CLI parsing helpers such as `cli_parse` live in prelude/Genia code in this phase

---

## `nth`, `take`, and `drop`

### Minimal example

```genia
unwrap_or("?", nth(1, ["a", "b", "c"]))
take(2, [1, 2, 3, 4]) -> [1, 2]
drop(2, [1, 2, 3, 4]) -> [3, 4]
```

### Edge case example

```genia
[nth(9, [1, 2]), take(0, [1, 2]), drop(0, [1, 2])]
```

Expected result:

```text
[none("index-out-of-bounds", {index: 9, length: 2}), [], [1, 2]]
```

The important modern style point:

```genia
unwrap_or("missing", nth(9, [1, 2]))
```

Expected result:

```text
"missing"
```

Compatibility lookup forms still exist elsewhere in Genia, but `nth` is not one of them.

### Failure case example

```genia
nth(1, 42)
```

Expected behavior:

- runtime match failure (second argument is not a list).

Another failure case:

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
- canonical maybe-returning list/search helpers: `first`, `last`, `nth`, `find_opt`
- compatibility aliases: `first_opt`, `nth_opt`
- docs-deprecated lookup forms such as `map_get`, slash access, and callable map/string lookup are covered in Chapter 01 and are not the preferred list/search style
- `reduce`
- `map` and `filter` as stdlib functions
- `range` helpers for 1-, 2-, and 3-arity calls

### ⚠️ Partial

- list performance is currently interpreter-level; optimizations are selective and pattern-dependent
- pipelines lift ordinary stages over `some(...)`, while explicit helpers still provide predictable Option control for list/search chains

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
  |> map((e) -> e ? entry_json(e) -> entry_name(e) | _ -> none)
```

Expected behavior:

- preserves list ordering
- emits `none("nil")` for non-JSON entries

### Failure case example

```genia
zip_entries("missing.zip")
```

Expected behavior:

- raises clear file error for unreadable/missing archive path
