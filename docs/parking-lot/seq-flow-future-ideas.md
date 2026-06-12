# Seq and Flow Future Ideas

Status: **Parking lot / non-authoritative**

This note captures future ideas only. It does not define implemented Genia behavior.
If this conflicts with `GENIA_STATE.md`, `GENIA_STATE.md` wins.

## Current boundary

`GENIA_STATE.md` is the authority for implemented Seq-compatible and Flow behavior.
Do not use this note to redefine which helpers currently accept lists or Flow values.

Useful future docs should preserve the semantic distinction between:

- Seq compatibility as an ordered-production category
- Flow as a lazy, pull-based, single-use runtime value
- List as an eager, reusable value
- source values that produce ordered items
- terminal consumers that materialize, reduce, or run ordered items

## Ownership Vocabulary

Future docs may need clearer terms for source ownership and consumption:

- reusable source
- single-use source
- lazy source
- eager source
- consumed source
- finalized source
- owned source
- borrowed source

This may help portability work, but should remain Genia-native terminology rather than
importing another language's ownership model wholesale.

## Resource And Finalization Terminology

Future contracts may need tighter wording for:

- bounded consumption
- early termination
- upstream finalization
- deterministic output order
- source-backed single-use enforcement
- terminal consumers versus transforming stages

These notes should become authoritative only through `GENIA_STATE.md`, focused specs,
and tests.

## Future Tightening Areas

Possible future work:

- clearer diagnostic wording for Seq-compatible misuse
- more shared specs for bounded pulling and finalization behavior
- explicit documentation for reusable versus single-use sources
- tighter distinction between host implementation iterators and public Genia values
- more precise guidance for terminal consumers such as materialization, reduction, and
  effectful traversal

## Non-goals

- no async streams yet
- no multi-port flows yet
- no Python generator exposure as a public Genia value
- no Clojure-compatible full seq library
- no implicit conversion of arbitrary values to Seq
- no new syntax merely for Seq or Flow

## Promotion trigger

Promote one future Seq/Flow item when it tightens the current contract with focused
specs and does not imply behavior beyond what has been implemented and verified.
