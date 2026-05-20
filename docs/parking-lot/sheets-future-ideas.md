# Sheets Future Ideas

Status: **Parking lot / non-authoritative**

This note captures future ideas only. It does not define implemented Genia behavior.
If this conflicts with `GENIA_STATE.md`, `GENIA_STATE.md` wins.

## Current direction to preserve

The preferred direction is:

```text
Sheet = immutable, columnar, named-column value with aligned rows
```

Start small. Avoid Excel-like cell mutation and hidden recalculation until much later, if ever.

## Design influences

Useful influences:

- APL: shape-first thinking
- Fortran: elemental functions, shape conformance, whole-array operations
- R: dataframe/tibble ergonomics, grouped summaries, pipe-friendly verbs
- Spreadsheets: approachable row/column mental model and formulas

## Candidate early operations

```text
sheet(...)
shape(sheet)
columns(sheet)
rows(sheet)
select(sheet, columns)
where(sheet, predicate)
derive(sheet, column, function)
collect(sheet)
```

Possible pipe style:

```genia
people
  |> where(row -> row.age >= 18)
  |> derive(quote(age_next), row -> row.age + 1)
  |> select([quote(name), quote(age_next)])
```

Treat this as hypothetical until implemented and tested.

## Outcome-aware cells and columns

Future Sheet values should interact cleanly with Outcome:

```text
some(value)        present usable value
none(context?)     missing/absent value
err(reason, ctx?)  recoverable invalid value
```

Open question:

- Should columns contain Outcome values directly?
- Should Sheet operations propagate Outcome automatically?
- Which operations short-circuit on `err`, and which aggregate/report errors?

## Formula plans later

Future formula plans may include:

- explicit dependencies
- dependency sorting
- cycle detection
- pure derived columns
- Outcome propagation
- optional caching/materialization

Avoid for early phase:

- A1 references
- mutable reactive cells
- hidden recalculation
- Excel-compatible formula language
- UI spreadsheet semantics

## Safe R ideas

Borrow:

- columnar mental model
- pipe-friendly verbs
- grouped summaries
- vectorized column expressions
- interactive inspection helpers like `head`, `schema`, `describe`

Avoid:

- broad vector recycling
- implicit coercion soup
- NA / NaN / NULL confusion
- non-standard evaluation magic
- mutable dataframe expectations

## Safe Fortran/APL ideas

Borrow:

- scalar lifting over shaped values
- shape conformance
- elemental/pure formulas
- whole-column expressions
- independence guarantees for derived columns

Avoid:

- dense legacy syntax
- implicit typing
- global mutable numeric state

## Promotion trigger

Promote this note when implementing the first minimal Sheet contract:

```text
immutable Sheets
named aligned columns
row count / shape checks
select / where / derive
basic tests and docs sync
```
