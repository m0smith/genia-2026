# Sheets Future Ideas

Status: **Parking lot / non-authoritative**

This note captures future ideas only. It does not define implemented Genia behavior.
If this conflicts with `GENIA_STATE.md`, `GENIA_STATE.md` wins.

## Current boundary

`GENIA_STATE.md` is the authority for implemented Sheet behavior.
Do not describe existing Sheet constructors or operations as hypothetical here.

## Outcome-aware columns

Future Sheet work may explore how Sheet values should interact with Outcome values:

- storing `some(...)`, `none(...)`, and `err(...)` as ordinary cell values
- explicit aggregation of missing or invalid cells
- report-friendly diagnostics for invalid rows or columns
- clear rules for operations that preserve, inspect, or summarize Outcome values

Open questions:

- Should any Sheet operation understand Outcome values directly?
- Which operations should aggregate diagnostics instead of short-circuiting?
- How should row, column, and field-path context appear in reports?

## Formula Plans

Future formula plans may include:

- explicit dependencies
- dependency sorting
- cycle detection
- pure derived columns
- Outcome propagation
- optional caching or materialization
- formula plans represented as ordinary Genia data

Avoid by default:

- A1 references
- mutable reactive cells
- hidden recalculation
- Excel-compatible formula language
- UI spreadsheet semantics

## Summaries And Inspection

Useful future areas:

- grouped summaries
- aggregate helpers for report output
- vectorized column expressions
- schema or shape inspection helpers
- preview helpers such as `head`, `schema`, or `describe`
- explicit conversion points between validation output and Sheet-shaped reports

## Design Influences

Borrow carefully from:

- APL: shape-first thinking
- Fortran: elemental functions, shape conformance, whole-array operations
- R: dataframe/tibble ergonomics, grouped summaries, pipe-friendly verbs
- Spreadsheets: approachable row/column mental model and formulas

Avoid:

- broad vector recycling
- implicit coercion soup
- NA / NaN / NULL confusion
- non-standard evaluation magic
- mutable dataframe expectations
- dense legacy syntax
- implicit typing
- global mutable numeric state

## Promotion trigger

Promote a future Sheet idea when it has a narrow contract, clear interaction with the
Outcome-aware validated data pipeline workflow, and a testable behavior boundary.
