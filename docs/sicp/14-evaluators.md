# 14. Evaluators

## Cold Open

At some point you stop asking, "What does this program do?"
and start asking, "How would I build the thing that makes programs do that?"

That is evaluator territory.

## What You'll Learn

- how Genia exposes a small metacircular helper surface
- what an environment value is
- why evaluator-building is partly about bookkeeping and partly about courage

## Tiny Runnable Example

Prediction prompt: can the evaluator layer really evaluate quoted code?

```genia
eval(quote(1 + 2), empty_env())
```
Classification: **Likely valid** (not directly tested)

```text
3
```

## Why This Matters

SICP becomes unforgettable when you realize the language can help explain itself.

## Core Concept

An evaluator needs:

- an expression
- an environment
- rules for what each shape means

## Visual / Mental Model

Think of the environment as labeled shelves and the evaluator as the librarian who knows how to use them.

## Genia Implementation

- `empty_env`, `lookup`, `define`, `set`, `extend`, and `eval` are implemented helpers
- metacircular environments are runtime capability values

## Common Mistakes

- mixing host evaluation ideas with Genia evaluator helpers
- assuming the metacircular layer replaces the ordinary runtime

## Failure Case

Evaluator helpers expect metacircular environment values in the right argument positions.
If you swap the order, Genia tells you.

## Exercises

1. Prediction: what does `lookup(env, quote(x))` return after one matching `define(...)`?
2. Tiny build task: create an env, define `x`, and look it up.
3. Rewrite for clarity: keep the quoted expression in its own binding before passing it to `eval`.

## Stretch Challenge

Explain how `quote(...)` and `eval(...)` form a loop without calling them "magic."

## Reality Check

### ✅ Implemented

- metacircular environment helpers
- evaluator helper surface

### ⚠️ Partial

- this is an educational layer, not a full second runtime architecture

### ❌ Not Implemented

- a separate production compiler pipeline replacing the current evaluator

## Summary

The evaluator chapters are where Genia lets you peek behind the curtain without pretending the curtain is gone.
