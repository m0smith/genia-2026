# SICP with Genia — Writing Guide

## Purpose

This document defines **HOW to write the book**.

- OUTLINE.md defines WHAT to write
- This document defines HOW to write it well
- AGENTS.md enforces rules

---

## Core Style: Reptile Brain Learning

The brain learns best when:
- it is curious
- it is slightly confused
- it predicts before seeing answers
- it sees patterns repeatedly

Your job is to **engage the reader’s survival brain**, not just their logic.

---

## Writing Rules

### 1. Start With Tension

Never start with definitions.

BAD:
> A function is...

GOOD:
> You wrote a program that works… until it doesn’t scale.

---

### 2. Force Prediction

Before showing results, ask:

- “What do you think this returns?”
- “Which one is faster?”
- “Will this crash?”

---

### 3. Use Tiny Steps

Break concepts into:
- 1 idea
- 1 example
- 1 takeaway

---

### 4. Show Failure First

Teach through mistakes:

- wrong implementation
- unexpected behavior
- edge cases

---

### 5. Use Visual Mental Models

Repeat consistent metaphors:

| Concept        | Metaphor              |
|----------------|----------------------|
| pipeline       | conveyor belt        |
| pattern match  | lock and key         |
| none           | broken track         |
| recursion      | stack of plates      |
| tail call      | reusing same plate   |
| IR             | stripped skeleton    |

---

### 6. Avoid Abstract Language

BAD:
> This demonstrates abstraction.

GOOD:
> You just stopped copying code three times.

---

### 7. Keep Energy High

- short paragraphs
- varied sentence length
- occasional humor
- conversational tone

---

## Exercises

Each section should include:

### Types of Exercises

1. Prediction
2. Fix the bug
3. Fill in the blank
4. Rewrite for clarity
5. Small build task

---

## Code Block Rules

### Runnable Genia Code

Use:

```genia
[1,2,3] |> map(inc)
Expected Output

Use a separate block:

[2, 3, 4]
Rules
Every runnable example MUST have output
Output MUST match exactly
Non-runnable examples MUST be clearly labeled
Reality Check Section (MANDATORY)

Every chapter MUST include:

✅ Implemented in Genia
⚠️ Partial support
❌ Not implemented

This prevents misleading readers.

Tone Guidelines

You are:

a mentor, not a lecturer
a guide, not a textbook
slightly playful, never silly
clear, never condescending
Anti-Patterns (DO NOT DO)

❌ Long walls of text
❌ Abstract definitions first
❌ No examples
❌ No exercises
❌ Teaching unimplemented features
❌ Overly academic tone

Golden Rule

If a tired student can:

read it
understand it
try it
succeed

Then you wrote it correctly.

If not, simplify.