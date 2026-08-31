# `rng`

**Category:** `random` &nbsp;|&nbsp; **Arity:** 1

```genia
rng(seed)
```

Create an explicit deterministic RNG state from `seed`.

## Arguments
- `seed`: non-negative integer seed

## Returns
- explicit deterministic RNG state

## Errors
- raises a type or value error when `seed` is not a non-negative integer

## Notes
- use this when you want reproducible random sequences in tests or demos

---

_Source: `std/prelude/random.genia` &middot; category `random`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
