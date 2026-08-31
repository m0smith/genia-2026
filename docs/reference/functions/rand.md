# `rand`

**Category:** `random` &nbsp;|&nbsp; **Arity:** 0, 1

```genia
rand()
rand(rng_state)
```

Advance an explicit RNG state and return `[next_rng_state, float]`.

## Arguments
- `rng_state`: explicit RNG state

## Returns
- `[next_rng_state, float]`, with a deterministic float in `[0, 1)`

## Errors
- raises a type error when `rng_state` is not an RNG state

---

_Source: `std/prelude/random.genia` &middot; category `random`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
