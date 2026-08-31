# `rand_flow`

**Category:** `random` &nbsp;|&nbsp; **Arity:** 1

```genia
rand_flow(seed)
```

Return a lazy seeded Flow of floats in `[0, 1)`.

The same seed produces the same bounded output in the Python reference host.
Use `take` or another limiter before `collect` or `run`.

---

_Source: `std/prelude/random.genia` &middot; category `random`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
