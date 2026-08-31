# `map_some`

**Category:** `option` &nbsp;|&nbsp; **Arity:** 2

```genia
map_some(f, opt)
```

Apply `f` to the inner value of `some(value)`, returning `some(result)`.

## Arguments
- `f`: function applied to the unwrapped inner value; called only for `some(value)`
- `opt`: the Option to transform

## Returns
- `some(f(value))` when `opt` is `some(value)`
- the incoming `none(...)` unchanged when `opt` is `none(...)`

## Errors
- raises when `opt` is not an Option value

## Examples

    "42" |> parse_int |> map_some((n) -> n * 2)

yields `some(84)`, and a parse failure yields `none("parse-error", ...)`.

---

_Source: `std/prelude/option.genia` &middot; category `option`. Generated from canonical metadata by `tools/gen_function_docs.py`._

[<- Back to the Function Reference](../index.md)
