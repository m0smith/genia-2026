# Genia Parking Lot

Status: **Non-authoritative future idea capture**

This directory is for ideas that may influence future Genia design, but **nothing here defines implemented Genia behavior**.

If anything in this directory conflicts with `GENIA_STATE.md`, then `GENIA_STATE.md` wins.

## Killer Workflow Alignment

Ideas that do not support Genia's first killer workflow — Outcome-aware validated data pipelines —
should be parked here unless explicitly approved.

Read `docs/strategy/killer-workflow.md` for the full list of preferred alignment areas
and the areas that belong in parking lot by default.

## Purpose

Use this directory to capture:

- future design ideas
- language influences worth revisiting
- possible host/runtime directions
- postponed scope from completed issues
- ideas that are useful but not ready for pre-flight
- ideas that do not align with the current killer workflow

## Non-authoritative rule

Parking-lot notes must not be treated as:

- current behavior
- language contract
- implementation instruction
- source-of-truth documentation
- runnable examples unless explicitly marked as hypothetical

## Promotion path

Ideas should move through the normal Genia process before implementation:

```text
Parking Lot
  -> Pre-flight
  -> Contract
  -> Design
  -> Failing Tests
  -> Implementation
  -> Docs Sync
  -> Audit / Truth Review
```

## Suggested file header

Use this header for new notes:

```md
# <Idea Title>

Status: Parking lot / non-authoritative

This note captures future ideas only. It does not define implemented Genia behavior.
If this conflicts with GENIA_STATE.md, GENIA_STATE.md wins.
```

## Suggested organization

Start with one note per idea family:

- `rust-friendly-portability.md`
- `sheets-future-ideas.md`
- `lifecycle-future-ideas.md`
- `seq-flow-future-ideas.md`

Keep notes short enough to be useful. If a note becomes implementation-ready, promote it into a normal issue and pre-flight artifact instead of expanding it forever.
