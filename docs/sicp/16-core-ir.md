# 16. Core IR

## Cold Open

Surface syntax is flashy.
Runtimes prefer skeletons.

That is where Core IR comes in.

## What You'll Learn

- why Genia lowers AST shapes into a smaller internal representation
- what "portability boundary" means in practice
- how this helps future hosts stay honest

## Tiny Runnable Example

Prediction prompt: what value do we still get after the ordinary source is lowered behind the scenes?

```genia
inc(x) = x + 1
double(x) = x * 2

3 |> inc |> double
```

```text
8
```

## Why This Matters

You do not need to stare at IR every day.
You do need to know why a language implementation shrinks rich syntax into a simpler internal form.

## Core Concept

Core IR is the stripped skeleton.
It carries the important semantic bones without every bit of surface decoration.

## Visual / Mental Model

Think of surface syntax as a fully dressed person.
Core IR is the X-ray.

## Genia Implementation

- the parser lowers into a minimal Core IR before evaluation
- pipelines stay explicit in IR rather than becoming nested calls
- Option constructors are explicit in IR

## Common Mistakes

- teaching host-local optimized nodes as if they were the frozen shared contract
- treating IR as a user-facing language

## Failure Case

The existence of Core IR does not mean users should invent new source syntax and assume lowering will save it.

## Exercises

1. Prediction: why is an explicit pipeline node easier to port than a pile of nested calls?
2. Tiny build task: explain one Genia surface feature that benefits from explicit IR shape.
3. Rewrite for clarity: replace "internal magic" with "lowering to a smaller representation."

## Stretch Challenge

Sketch, in prose, how `some(1)` being explicit in IR could help another host.

## Reality Check

### ✅ Implemented

- AST-to-Core-IR lowering
- frozen minimal portability contract documentation

### ⚠️ Partial

- only the Python host is implemented today even though portability scaffolding exists

### ❌ Not Implemented

- multiple running hosts consuming the shared IR contract today

## Summary

Core IR is the reason the language can stay expressive on the surface while remaining small enough to port underneath.
