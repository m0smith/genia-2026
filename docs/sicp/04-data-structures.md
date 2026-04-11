# 04. Data Structures

## Cold Open

One value is easy.
Ten values are annoying.
A nested value that mixes names, lists, and optional pieces is where real programs begin.

## What You'll Learn

- how Genia represents lists and maps
- how nested structure changes the way you think
- how absence can show up inside structure, not just around it

## Tiny Runnable Example

Prediction prompt: what shape comes back here?

```genia
person = {name: "Ada", pets: ["ant", "bee"]}

[person/name, nth(1, person/pets)]
```

```text
["Ada", some("bee")]
```

## Why This Matters

Programs stop being "do math" very quickly.
They become "walk this structure and find the piece you need."

## Core Concept

Lists preserve order.
Maps name parts.
Nesting lets you build stories instead of flat scraps.

## Visual / Mental Model

Think of a nested map as a backpack with labeled pockets.
Lists are the ordered items stuffed inside those pockets.

## Genia Implementation

- list literals are implemented
- map literals are implemented
- slash access on maps is implemented
- maybe-aware helpers such as `nth` are implemented

## Common Mistakes

- expecting every lookup to succeed
- forgetting that `nth` returns an Option value

**Illustrative sketch — not runnable**
```genia
order = {
  user: {name: "Ari"},
  items: [...],
  payment: ...
}
```

## Failure Case

Going past the end of a list does not quietly invent a value.
It returns structured absence such as `none("index-out-of-bounds", ...)`.

## Exercises

1. Prediction: what does `nth(0, ["a", "b"])` return?
2. Fix the bug: replace a raw out-of-range assumption with `unwrap_or`.
3. Tiny build task: create a nested map with a `name` and `scores`.

## Stretch Challenge

Model a tiny game save as one nested map and one list.

## Reality Check

### ✅ Implemented

- lists
- maps
- nesting
- slash map access

### ⚠️ Partial

- map values are persistent and opaque at runtime; this chapter teaches use, not internal representation

### ❌ Not Implemented

- general mutable object fields
- arbitrary member-access syntax

## Summary

Once you can see a program as structure plus traversal, Genia starts feeling much less mysterious.
