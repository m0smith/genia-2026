# SICP with Genia — Writing Guide

## Purpose

This document defines HOW to write the SICP-with-Genia chapters well.

- `OUTLINE.md` defines WHAT chapters exist
- this file defines HOW those chapters should feel
- `AGENTS.MD` defines the maintenance contract

## Core Style: Reptile-Brain Learning

Write for a tired, curious reader whose attention must be earned.

That means:

- tension before theory
- prediction before explanation
- tiny wins before abstraction
- repetition with variation
- concrete examples before formal terms

## Teaching Moves To Use Repeatedly

Favor these moves in every chapter:

- `Think About It`
- `Prediction Prompt`
- `Aha!`
- `Common Trap`
- `Try This`
- `Mini challenge`
- `Reality Check`

Not every label must appear every time, but the chapter should clearly use that rhythm.

## Start With Tension

Bad opening:

```text
A function is a reusable abstraction.
```

Better opening:

```text
You copied the same calculation three times, changed one copy, and now the results disagree.
```

## Force Prediction

Before showing output, ask a small question such as:

- What do you think this returns?
- Which branch matches first?
- Does this produce a value or a `none(...)`?

Prediction makes the later explanation stick.

## Use Tiny Steps

Break ideas into:

- one idea
- one example
- one takeaway

Avoid giant explanation dumps.

## Show Failure, Not Just Success

Readers trust a chapter more when it admits where the walls are.

Include:

- a wrong version
- an edge case
- a failure mode

## Mental Models To Reuse

Keep these metaphors stable:

| Concept | Metaphor |
| --- | --- |
| pipeline | conveyor belt |
| pattern match | lock and key |
| `none(...)` | broken track |
| recursion | stack of plates |
| tail call | reusing the same plate |
| Core IR | stripped skeleton |

## Tone

Write like:

- a mentor, not a lecturer
- a guide, not a spec document
- lightly playful, never goofy
- clear, never condescending

Use short paragraphs.
Keep energy high.
Let the reader breathe.

## Runnable Example Rules

Runnable Genia examples use a `genia` fence and must be followed immediately by a non-Genia output fence.

Correct pattern:

````md
```genia
1 + 2
```

```text
3
```
````

Illustrative-only Genia snippets must be marked on the line immediately above the fence with one of the approved labels from `AGENTS.MD`.

## Exercises

Each chapter should include a small mix of:

1. prediction
2. fix-the-bug
3. fill-in-the-blank
4. rewrite-for-clarity
5. tiny build task

Keep exercises short enough that a reader can try one right away.

## Reality Check

Every chapter must include:

- `### ✅ Implemented`
- `### ⚠️ Partial`
- `### ❌ Not Implemented`

This section prevents wishful teaching.

## Anti-Patterns

Do not write:

- long walls of text
- abstract definitions first
- untested runnable examples
- unmarked non-runnable Genia snippets
- speculative features presented as current
- dry academic ports of SICP phrasing

## Golden Rule

If a reader can:

- read it quickly
- predict something
- run something
- get a small win

then the chapter is doing its job.
