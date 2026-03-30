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

---

## `map` and `filter` (reduce-driven)

`map` and `filter` are implemented in stdlib using `reduce` and `reverse`.

This keeps the implementation minimal and takes advantage of existing tail-recursive accumulation behavior already used by `reduce`.

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

### Failure case example

```genia
map((x) -> x + 1, 123)
```

Expected behavior:

- runtime match failure, because `map` delegates to list-pattern-based `reduce` and non-list input cannot match those list cases.

---

## Implementation status

### ✅ Implemented

- list literals and list spread
- list-pattern matching with rest patterns
- recursive list helpers in stdlib
- `reduce`
- `map` and `filter` as reduce-based stdlib functions

### ⚠️ Partial

- list performance is currently interpreter-level; optimizations are selective and pattern-dependent

### ❌ Not implemented

- lazy sequences
- iterator protocol
- built-in map/filter syntax (helpers exist only as stdlib functions)
