# 06. Symbolic Data

## Cold Open

What if the program itself became data you could carry around?
Not the result.
The code shape.

That is where SICP gets weird in a good way.

## What You'll Learn

- how `quote(...)` turns syntax into data
- how `quasiquote(...)` lets you splice in real values
- why symbols are not the same thing as strings

## Tiny Runnable Example

Prediction prompt: what does the interpreter hand back here?

```genia
quote([a, b, c])
```
Classification: **Likely valid** (not directly tested)

```text
(a b c)
```

## Why This Matters

Once code can become data, you can inspect it, transform it, and eventually evaluate it again.

## Core Concept

`quote(...)` says, "Do not run this. Package it."
`quasiquote(...)` says, "Package it, but let me sneak a few live values inside."

## Visual / Mental Model

Think of `quote(...)` as putting syntax in amber.
`quasiquote(...)` is amber with a tiny hatch for selected live pieces.

## Genia Implementation

- `quote(...)` is implemented
- `quasiquote(...)`, `unquote(...)`, and list-context `unquote_splicing(...)` are implemented
- quoted identifiers become symbols

## Common Mistakes

- expecting quoted code to run
- assuming symbols are strings

## Failure Case

`unquote(...)` outside a surrounding quasiquote is a runtime error.
So is splicing where list context does not exist.

## Exercises

1. Prediction: what does `quasiquote([a, unquote(1 + 2), c])` return?
2. Fix the bug: move `unquote(...)` into a real `quasiquote(...)`.
3. Tiny build task: quote a map with one identifier key and one string key.

## Stretch Challenge

Write a quoted expression, then use a helper from the syntax layer to inspect one piece of it.

## Reality Check

### ✅ Implemented

- `quote(...)`
- `quasiquote(...)`
- `unquote(...)`
- list-context `unquote_splicing(...)`

### ⚠️ Partial

- this is still a small programs-as-data surface, not a full macro system

### ❌ Not Implemented

- quote sugar such as `'x`
- macros

## Summary

Symbolic data is where Genia stops being only a language you use and starts becoming a language you can examine.
