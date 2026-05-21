# Genia Killer Workflow — Strategy Guide

Status: **Strategy / prioritization guide.**
This document does not define implemented Genia language behavior.
If anything here conflicts with `GENIA_STATE.md`, `GENIA_STATE.md` wins.

---

## First Killer Workflow

Genia's first killer workflow is **Outcome-aware validated data pipelines.**

Core promise:

```
messy records in → clear pipelines → validated shaped output / reports + useful diagnostics
```

## Practical Workflow Shape

1. Read messy records from files or stdin
2. Parse structured data such as CSV, JSON, or JSONL
3. Transform records through clear pipelines
4. Validate with Outcome-aware rules
5. Reshape valid records into Sheets or reportable structures
6. Emit clean output plus useful diagnostics

## North-Star Example

> **Not a current behavior contract.** Illustrative only.

```
stdin
|> lines
|> map(parse_csv_row)
|> keep_some(validate_record)
|> map(reshape_for_report)
|> each(print)
```

Current implemented building blocks include `lines`, `map`, `keep_some`, `each`, `print`,
Outcome constructors `some`/`none`/`err`, and Sheet values. Pipeline composition is implemented.
The complete workflow above depends on `parse_csv_row` and `validate_record` being defined by the caller.

## Near-Term Preferred Alignment Areas

Changes that strengthen one or more of these areas are preferred:

- **Flow / Seq** — lazy pull-based ordered processing
- **Outcome** — `some`, `none`, `err` value-level presence/absence/failure
- **Record parsing** — CSV, JSON, JSONL, field extraction from messy input
- **Validation** — Outcome-aware rule application to records
- **Diagnostics** — surfacing which records failed, why, and how
- **Sheets** — immutable columnar output for reportable structures
- **CLI-native data processing** — pipe-mode, file-mode, stdout/stderr discipline
- **Value templates** — when they support validation, contracts, or shapes for record data

## Defer / Parking-Lot Areas

Unless explicitly approved, route proposals in these areas to parking lot:

- actors / process-level concurrency
- browser UI / playground
- lifecycle machinery
- ants / teaching demos
- multi-host expansion beyond what the killer workflow needs
- broad runtime architecture not needed for Outcome-aware data pipelines

See `docs/parking-lot/README.md` for the parking-lot process.

## Using This Document

Agents and contributors should read this document before proposing or implementing new work.

Ask: **Does this change help Genia become excellent at Outcome-aware validated data pipelines?**

- If yes: proceed through the normal phase pipeline.
- If indirectly: document how.
- If no: park it unless explicitly approved.

This document is a compass, not a language contract. It does not add to, remove from,
or override anything in `GENIA_STATE.md`.
