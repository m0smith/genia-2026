# `rand`

**Category:** `random` &nbsp;|&nbsp; **Arity:** 0, 1

```genia
rand()
rand(rng_state)
```

Advance an explicit RNG state and return `[next_rng_state, float]`.

The float is deterministic for a given seed and is always in `[0, 1)`.

---

_Source: `std/prelude/random.genia` &middot; category `random`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
