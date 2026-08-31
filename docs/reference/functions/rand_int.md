# `rand_int`

**Category:** `random` &nbsp;|&nbsp; **Arity:** 1, 2

```genia
rand_int(n)
rand_int(rng_state, n)
```

Advance an explicit RNG state and return `[next_rng_state, int]`.

## Arguments
- `rng_state`: explicit RNG state
- `n`: positive exclusive upper bound

## Returns
- `[next_rng_state, int]`, with a deterministic integer in `[0, n)`

## Errors
- raises a type error when `rng_state` is not an RNG state
- raises a type or value error when `n` is not a positive integer

---

_Source: `std/prelude/random.genia` &middot; category `random`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
