# `flat_map_some`

**Category:** `option` &nbsp;|&nbsp; **Arity:** 2

```genia
flat_map_some(f, opt)
```

Apply the Option-returning function `f` to the inner value of `some(value)`.

## Arguments
- `f`: function applied to the unwrapped inner value; must itself return an Option, and is called only for `some(value)`
- `opt`: the Option to chain from

## Returns
- the Option returned by `f(value)` when `opt` is `some(value)`
- the incoming `none(...)` unchanged when `opt` is `none(...)`

## Errors
- raises when `opt` is not an Option value
- raises when `f` returns a non-Option value

## Examples

    "42" |> parse_int |> flat_map_some(validate_positive)

where `validate_positive` returns `some(n)` or `none("negative", ...)`.

---

_Source: `std/prelude/option.genia` &middot; category `option`. Generated from `@doc`/`@meta` by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
