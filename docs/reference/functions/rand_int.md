# `rand_int`

**Category:** `random` &nbsp;|&nbsp; **Arity:** 1, 2

```genia
rand_int(n)
rand_int(rng_state, n)
```

Advance an explicit RNG state and return `[next_rng_state, int]`.

The integer is deterministic for a given seed and is always in `[0, n)`.

---

_Source: `std/prelude/random.genia` &middot; category `random`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
