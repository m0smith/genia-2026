# Seq and Flow Future Ideas

Status: **Parking lot / non-authoritative**

This note captures future ideas only. It does not define implemented Genia behavior.
If this conflicts with `GENIA_STATE.md`, `GENIA_STATE.md` wins.

## Core distinction

Preserve this mental model:

```text
Seq  = Genia semantic abstraction for ordered production
Flow = lazy, pull-based, usually single-use Seq implementation / transformation
List = eager, reusable Seq-compatible value
```

Do not define this as “everything secretly becomes Flow.”

## Why Seq matters

Seq exists to remove artificial cliffs between eager list pipelines and lazy Flow pipelines.

Candidate public contract:

```text
map     : Seq -> Seq
filter  : Seq -> Seq
take    : Seq -> Seq
drop    : Seq -> Seq
scan    : Seq -> Seq
each    : Seq -> Seq
collect : Seq -> List
run     : Seq -> none
reduce  : Seq -> value
```

## Resource vocabulary

Future docs may need clear terms:

```text
reusable Seq
single-use Seq
lazy source
eager source
consumed source
finalized source
owned source
borrowed source
```

This overlaps with Rust-friendly portability but should remain Genia-native.

## Expected behavior direction

Pipelines like this should eventually compose without a Flow/list cliff:

```genia
range(10)
  |> take(10)
  |> map((x) -> {a: x})
  |> map((x) -> format("number:{a}", x))
  |> each(print)
  |> run
```

Treat this as hypothetical unless already covered by current specs.

## Error wording direction

Prefer diagnostics like:

```text
each expected a Seq-compatible value, received <type>
```

over:

```text
each expected a Flow, received list
```

once the Seq contract is implemented.

## Laziness and finalization

Future contracts should preserve:

- bounded consumption
- early termination
- correct upstream finalization
- deterministic output order
- single-use enforcement for source-backed streams

## Non-goals

- no async streams yet
- no multi-port flows yet
- no Python generator exposure
- no Clojure-compatible full seq library
- no implicit conversion of arbitrary values to Seq
- no new syntax merely for Seq

## Promotion trigger

Promote this note when adding or tightening shared specs for Seq-compatible functions, especially `each`, `collect`, `run`, `reduce`, `map`, `filter`, `take`, `drop`, or `scan`.
