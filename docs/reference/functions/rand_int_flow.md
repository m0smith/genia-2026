# `rand_int_flow`

**Category:** `random` &nbsp;|&nbsp; **Arity:** 2

```genia
rand_int_flow(seed, n)
```

Return a lazy seeded Flow of integers in `[0, n)`.

## Arguments
- `seed`: non-negative integer seed
- `n`: positive exclusive upper bound

## Returns
- lazy seeded Flow of deterministic integers in `[0, n)`

## Notes
- the same seed and `n` produce the same bounded output in the Python reference host
- use `take` or another limiter before `collect` or `run`

---

_Source: `std/prelude/random.genia` &middot; category `random`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
