# 15. Language Variations

## Cold Open

SICP loves to ask, "What if the language worked a little differently?"
That question is exciting.
It is also dangerous if you blur it with what Genia actually does today.

## What You'll Learn

- which parts of Genia behavior are fixed today
- where explicit variation already exists
- how to talk about future language experiments without teaching them as current

## Tiny Runnable Example

Prediction prompt: what does explicit delayed evaluation look like in current Genia?

```genia
p = delay(1 + 2)

force(p)
```
Classification: **Likely valid** (not directly tested)

```text
3
```

## Why This Matters

Language design is easier to understand when you can compare "the current rule" with "a possible different rule."

## Core Concept

A variation is only useful if you can first state the baseline clearly.
Genia today is mostly strict by default, with explicit delayed computation where needed.

## Visual / Mental Model

Think of the current language as the house you actually live in.
Variations are blueprints on the table, not rooms you can already walk into.

## Genia Implementation

- ordinary evaluation rules are implemented
- explicit delay/force is implemented
- alternative evaluation strategies are mainly conceptual in this phase

## Common Mistakes

- talking about imagined language extensions as if they already ship
- using the word "variation" to smuggle in unimplemented syntax

## Failure Case

Do not document alternative conditionals, macros, or evaluation rules as current Genia just because they make the chapter narrative exciting.

## Exercises

1. Prediction: what changes if you remove `delay(...)` from the runnable example?
2. Rewrite for clarity: describe one current Genia rule and one conceptual variation.
3. Tiny build task: wrap a computation in `delay(...)` and then `force(...)`.

## Stretch Challenge

Write one paragraph that distinguishes implemented behavior from a possible future experiment.

## Reality Check

### ✅ Implemented

- current strict-by-default evaluation
- explicit `delay(...)` / `force(...)`

### ⚠️ Partial

- the chapter talks about language variation mostly as a design lens, not as a large implemented feature set

### ❌ Not Implemented

- multiple selectable evaluation strategies
- user-defined syntax extensions

## Summary

This chapter is a reminder to separate design imagination from actual runtime truth.
