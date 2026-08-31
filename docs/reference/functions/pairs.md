# `pairs`

**Category:** `map` &nbsp;|&nbsp; **Arity:** 2

```genia
pairs(xs, ys)
```

Zip two lists into a list of `[x, y]` pairs, bounded by the shorter input.

## Arguments
- `xs`: the first list; supplies the `x` of each pair
- `ys`: the second list; supplies the `y` of each pair

## Returns
- a list of `[x, y]` pairs, one per index up to the length of the shorter list
- `[]` when either list is empty

## Errors
- rejects an argument that is not a list

## Examples
```genia
pairs([1, 2], [3, 4])  # => [[1, 3], [2, 4]]
pairs([1], [10, 20])   # => [[1, 10]]
pairs([], [1, 2])      # => []
```

---

_Source: `std/prelude/map.genia` &middot; category `map`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
