# Pipeline / Option redesign

## Old behavior

- `|>` was pure call rewriting.
- `record |> get("user") |> then_get("name")` worked because helper functions such as `then_get`, `then_nth`, and `map_some` propagated `none(...)`.
- `parse_int("12x")` raised instead of returning structured absence.

## New behavior

- `|>` is now an Option-aware pipeline stage form.
- If a stage input or result is `some(x)`, the next stage receives `x`.
- If a stage input or result is `none(...)`, remaining stages do not execute and that same `none(...)` is returned.
- `parse_int` now returns `some(int)` on success and `none(parse_failed, context)` for ordinary parse failure.

## Why

- The old helper-first style made simple pipelines verbose and easy to get wrong.
- Automatic Option propagation makes canonical maybe-returning helpers compose directly.
- Structured absence now travels through pipelines without turning normal missing-data cases into exceptions.

## Write code like this now

Old:

```genia
record |> get("user") |> then_get("name") |> or_else("unknown")
```

New:

```genia
unwrap_or("unknown", record |> get("user") |> get("name"))
```

Old:

```genia
nth(5, fields(row)) |> map_some(parse_int) |> unwrap_or(0)
```

New:

```genia
unwrap_or(0, fields(row) |> nth(5) |> parse_int)
```

## Flow relationship

- Flow remains explicit.
- `lines`, `collect`, `run`, and other Flow helpers still define when values cross between ordinary values and Flow values.
- Option-aware pipelines do not create implicit Value↔Flow conversion.
