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

## Outcome-Aware Conditional Flow Termination

Roadmap decision for planned R11:

- do not introduce a special-purpose `take_some_while` helper
- prefer ordinary `take_while(some?)` if the desired operation can be expressed through
  general `take_while` semantics
- keep input production separate from conversation-state evolution

`take_while` is not currently an implemented Genia Flow helper. Before promotion, its
general semantics require design and focused tests, including whether the terminating
item is emitted, how Outcome values remain observable, and how bounded consumption
finalizes an upstream Flow. The R11 roadmap records this as a planned semantic gap; it
does not authorize implementation.

Current `evolve(init, step)` remains unchanged: it emits `init` and repeatedly applies
`step(previous_value)`. For state driven by an input Flow, current
`scan(step, initial_state, source)` is the closer existing composition shape. Neither
helper should be overloaded merely to make a conversation example shorter.

A future conceptual termination stage, subject to the general `take_while` design, is:

```text
outcome_flow
  |> take_while(some?)
```

This decision does not define current `evolve`, `scan`, Flow, Outcome, or `take_while`
behavior.

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
