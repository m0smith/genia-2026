# Chapter 05: Lists

## What list helpers are implemented today?

Genia ships a small list-focused stdlib in `std/prelude/list.genia`.

Core helpers include:

- `list`
- `first`
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
- `reduce`
- `map` and `filter` as stdlib functions
- `range` helpers for 1-, 2-, and 3-arity calls

### ⚠️ Partial

- list performance is currently interpreter-level; optimizations are selective and pattern-dependent

### ❌ Not implemented

- lazy sequences
- iterator protocol
- flow-aware list pipelines (backpressure/cancellation/multi-output stages)
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
