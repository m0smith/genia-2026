# 18. Machines and Compilation

## Cold Open

At the end of SICP, the story zooms out.
Not just "What does this function do?"
But "What kind of machine could carry this whole language?"

## What You'll Learn

- what parts of Genia's implementation story are real today
- where compilation and multi-host work are still scaffolding
- how to talk about future machines without pretending they already exist

## Tiny Runnable Example

Prediction prompt: what does the current machine still do with an ordinary expression pipeline?

```genia
inc(x) = x + 1

41 |> inc
```

```text
42
```

## Why This Matters

Implementation chapters keep language design honest.
They remind you that semantics eventually need a machine-shaped home.

## Core Concept

Today Genia is primarily an interpreted Python reference host with Core IR lowering and portability scaffolding around it.

## Visual / Mental Model

Imagine a workshop bench.
One working machine sits in the middle.
Around it are labeled parts and blueprints for future machines.

## Genia Implementation

- Python is the implemented reference host
- docs and manifests for future hosts exist
- Core IR and shared spec scaffolding define the intended portability path

## Common Mistakes

- speaking about planned hosts as if they are already implemented
- teaching documentation scaffolding as completed runtime support

## Failure Case

The repository contains future-host scaffolding, not a finished compiled multi-host ecosystem.
This chapter must say that plainly.

## Exercises

1. Prediction: which is implemented today, Python host or Rust host?
2. Rewrite for clarity: distinguish "documented portability path" from "running host."
3. Tiny build task: summarize the current host status in two sentences.

## Stretch Challenge

Explain why a shared Core IR contract matters before multiple hosts fully exist.

## Reality Check

### ✅ Implemented

- Python reference host
- Core IR lowering
- portability documentation and manifest scaffolding

### ⚠️ Partial

- shared multi-host infrastructure is scaffolded, not fully running

### ❌ Not Implemented

- compiled native host pipeline as a finished supported workflow
- multiple implemented hosts in this repository today

## Summary

This is the honest ending:
Genia already has a real machine, and it also has carefully labeled blueprints for the machines that may come next.
