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

## Release Positioning

**R1** proved the killer-workflow foundation end-to-end:

```
messy records in → clear pipelines → Outcome-aware validation → clean records + diagnostics out
```

R1 is complete.

**R2** protects and exercises the R1 surface through native Genia tests.
R2 is complete.

**R3** expanded native Genia test coverage over Genia-facing behavior.
R3 delivered `@test "description"` annotation-driven native test discovery, native test coverage for validation helpers, Outcome constructors/rendering, JSONL helpers, and pipeline examples.
R3 is complete.

**R4** extracts the proven test lifecycle shape into a portable lifecycle contract.
R4 is complete.

**R5** moves appropriate Genia-facing tests into Genia-native tests.
R5 is complete.

**R6** hardens the data workflow with CSV, Sheets, report output, and richer diagnostics.
R6 is complete.

**R7** improves web-serving ergonomics as explicitly approved infrastructure work.
R7 is complete. It does not replace the validated-data-pipeline product north star, and it is not a general web framework, browser-native runtime, or plugin system.

**R8** completed the explicitly approved server-execution-mode infrastructure work.

**R9** completed the value-template and representation work that supports the
validated-data-pipeline direction. **R10** is complete: its approved
configuration/protected-value contract and E10-1 provider/ordinary acquisition,
E10-2 defaults/conversion/Template validation, E10-3 protected-carrier/matching, E10-4 protected-sink safety, E10-5 explicit declassification, E10-6 cross-mode hardening, E10-7 composed validated-pipeline proof, and E10-8 release truth audit are complete. Later work still requires the repository's contract, design, test,
implementation, documentation, and audit gates.

**R11** is complete through E11-8. Its Experimental ordinary model callable,
R9-structured output, R10 credential boundary, application-owned Flow/`scan`
conversation composition, and validated-pipeline proving case are implemented;
E11-7 synchronizes runnable release examples and implemented truth without adding
runtime behavior; E11-8 completes the release truth audit and distillation without
adding runtime behavior.

**R12** is complete through E12-9. E12-1 through E12-7 implement and prove the
Experimental ordinary retrieval/grounding composition used by the validated
grounded pipeline; E12-8 synchronizes runnable examples and implemented truth
without runtime behavior; E12-9 completes the release truth audit and
distillation without runtime behavior.

**R13** is complete through E13-8. E13-1 through E13-6 implement and prove the
Experimental explicit configuration-resolution composition used by validated
pipelines; E13-7 synchronizes runnable examples and implemented truth without
runtime behavior; E13-8 completes the release truth audit and distillation
without runtime behavior.

**R14** is in progress through E14-2. It is explicitly approved lifecycle
infrastructure with a direct record-pipeline proving path: multiple lifecycle
concerns may surround each consumed element while existing Flow/Seq and Outcome
transformations remain authoritative. E14-0 through E14-2 (issues #620, #621,
#692) implement and prove the Experimental parent/child instance/scope core
and its horizontal peer-attachment breadth; E14-3 and later slices —
repeated element-scoped execution, provider binding, and the outbound HTTP
application-integration proof — remain planned, not implemented.

## Using This Document

Agents and contributors should read this document before proposing or implementing new work.

Ask: **Does this change help Genia become excellent at Outcome-aware validated data pipelines?**

- If yes: proceed through the normal phase pipeline.
- If indirectly: document how.
- If no: park it unless explicitly approved.

This document is a compass, not a language contract. It does not add to, remove from,
or override anything in `GENIA_STATE.md`.
