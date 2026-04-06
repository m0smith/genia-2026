# Codex Prompt: Write and Revise the Genia SICP Book in Head First Style

## Objective

Write and revise the Genia SICP book in `docs/sicp/` using a **Head First–style learning design** that is:

* engaging
* interactive
* memorable
* brain-aware
* accurate to the current Genia implementation

This is **not** a traditional textbook.
It is a **high-engagement learning experience** designed to make the reader think, predict, laugh a little, and remember.

At the same time, it must remain **strictly truthful** to the current Genia implementation and repository documentation.

---

## Required Reading (MANDATORY)

Before making any changes, you MUST read:

* `AGENTS.md`
* `docs/sicp/AGENTS.MD`
* `GENIA_STATE.md`
* `GENIA_RULES.md`
* `GENIA_REPL_README.md`
* relevant existing `docs/sicp/*` chapter files

Treat these as authoritative.

### Source-of-truth rule

If these disagree:

* `GENIA_STATE.md` is the final authority for what is actually implemented
* `GENIA_RULES.md` is the authority for language semantics
* `docs/sicp/*` must be updated to match reality

Do not document imagined or planned behavior as if it already exists.

---

## Core Writing Style

Write in a **Head First–style** learning voice.

That means the chapter must feel:

* conversational
* energetic
* interactive
* slightly playful
* easy to skim
* easy to remember

### Required cognitive style

Every major section should actively engage the reader using most of these:

* **Think About It**
* **Your Brain on Genia**
* **Aha!**
* **Try This**
* **Common Trap**
* **Let’s Rewrite That**
* **Puzzle**
* **Mini challenge**
* **Prediction prompt**

Do not write long dry walls of text.

Do not sound like a formal language specification unless the section is explicitly a reference note.

---

## Non-Negotiable Truthfulness Rules

You MUST follow the repository documentation discipline.

### Never do these:

* Document a feature as implemented unless it is actually implemented
* Use syntax that does not work
* Hand-wave over real limitations
* Present future work as current behavior

### Every chapter or major feature section must clearly label:

* ✅ Implemented
* ⚠️ Partial
* ❌ Future / not implemented

### Every feature explanation should include:

* a minimal example
* an edge case example
* a failure case example, where relevant

---

## Genia-Specific Language Rules

### 1. Never introduce `if`

Genia uses pattern matching as its conditional model.

Do not write:

* `if`
* `switch`
* ternary
* fake pseudocode conditionals pretending to be Genia

### 2. Use real Genia syntax

Use actual Genia syntax that matches the current implementation.

### 3. Keep examples aligned with reality

All Genia examples must reflect real parser/runtime behavior.

### 4. Do not use ```genia for non-Genia code

If a code block is not Genia, use the correct fence, such as:

* `text`
* `python`
* `json`
* `md`
* `bash`

Never use ```genia for prose, pseudocode, JSON, markdown examples, shell snippets, or other languages.

---

## Code Fence Policy (CRITICAL)

This section is mandatory.

The automated SICP book test suite depends on this format.

### A. Runnable Genia blocks

A runnable Genia example must:

* use ` ```genia `
* be valid Genia source intended to execute
* be immediately followed by an expected-output block
* use a different fence type for the expected output

The required pattern is:

````md
```genia
square(x) = x * x

square(5)
```

```text
25
```
````

Strict rule:

* the expected-output block must be the **next code block**
* the expected-output block must use a non-Genia fence type
* the standard fence type is `text`

The test harness matches runnable `genia` blocks to the immediately following output block.

Execution model for the test suite:

* each runnable block is executed in a fresh Genia environment
* runnable blocks should therefore be self-contained
* non-runnable marked blocks are skipped entirely

### B. Non-runnable Genia blocks

Sometimes a chapter needs a Genia-shaped example that is:

* partial
* schematic
* intentionally incomplete
* illustrative only

These may still use ` ```genia `, but only if they are visibly marked on the line immediately above the block.

Accepted markers:

* **Example only — not runnable**
* **Illustrative sketch — not runnable**
* **Conceptual example — not directly runnable**

Example:

````md
**Conceptual example — not directly runnable**
```genia
fact(n, acc) = ...
```
````

These blocks are skipped by the automated test suite.

### C. Non-Genia blocks

If the content is not Genia, it must not use ` ```genia `.

Use the correct fence type instead, such as:

* `text`
* `python`
* `json`
* `md`
* `bash`

Examples:

* output samples → `text`
* AST/IR shapes that are explanatory rather than runnable Genia → `text`
* shell commands → `bash`
* Python snippets → `python`

### D. Output blocks

Expected output blocks must:

* use a non-Genia fence type
* normally use ` ```text `
* contain the expected rendered output only
* immediately follow the runnable `genia` block as the next code block

The test suite normalizes newline style and trims trailing whitespace, but it does not ignore real output differences.

### E. Invalid patterns that should fail

This is invalid because the runnable `genia` block is not followed by a non-Genia output block:

````md
```genia
1 + 2
```

```genia
3
```
````

This is also invalid because a runnable `genia` block has no adjacent expected-output block at all:

````md
```genia
1 + 2
```
````

---

## Testability Expectations

Genia blocks in the SICP book are executable learning artifacts.

When writing or revising a chapter:

* prefer runnable examples over decorative examples
* keep runnable examples small and self-contained
* pair runnable `genia` blocks with adjacent `text` output blocks
* avoid fake examples that cannot be validated
* mark illustrative-only Genia snippets explicitly as not runnable

If you add runnable examples, assume the automated test suite will execute them.

---

## Structural Requirements for Each Chapter

Each chapter should generally include:

1. **A strong opening hook**

   * surprise
   * curiosity
   * tension
   * a concrete question

2. **Short sections with whitespace**

   * no giant walls of text
   * one idea at a time

3. **Interactive learning moments**

   * prediction questions
   * fill-in-the-blank thinking
   * “what happens next?” prompts
   * tiny exercises

4. **Code + explanation + analogy**

   * not just code
   * not just prose

5. **A summary section**

   * key ideas
   * what the reader should now believe / understand

6. **Exercises**

   * a few basic
   * at least one that requires thinking, not just copying

7. **Solutions section**

   * when appropriate, either in the same chapter or a companion section/file

8. **Status markers**

   * ✅ implemented
   * ⚠️ partial
   * ❌ future

---

## Preferred Section Components

Use many of these throughout a chapter:

### Think About It

Ask the reader to predict before explaining.

### Your Brain on Genia

Name the confusion the reader is probably feeling.

### Aha!

Resolve the tension simply and clearly.

### Try This

Give a tiny runnable example.

### Common Trap

Show a likely mistake.

### Let’s Rewrite That

Show a cleaner or more idiomatic version.

### Puzzle

Add a small challenge that makes the reader stop and think.

---

## Tone Guidelines

Use:

* direct address (“you”)
* short paragraphs
* occasional humor
* high clarity
* concrete examples

Avoid:

* academic stiffness
* long abstract exposition
* needless jargon
* “spec voice” except where explicitly needed

---

## Output and File Placement

Write chapters into files such as:

* `docs/sicp/01-...`
* `docs/sicp/02-...`

When revising an existing chapter:

* preserve useful material
* improve structure and engagement
* keep it aligned with real implementation
* update status markers if needed

---

## Documentation Synchronization Rules

If a chapter change reveals a mismatch with implementation or repo docs, update the relevant files too.

When behavior or feature coverage changes, update as needed:

* `GENIA_STATE.md`
* `GENIA_RULES.md`
* `GENIA_REPL_README.md`
* relevant `docs/sicp/*`

Do not let the book drift away from the language.

---

## Anti-Patterns (STRICTLY FORBIDDEN)

Do NOT:

* invent unsupported syntax
* use `if` in Genia examples
* write long passive textbook prose
* use ```genia for non-Genia content
* include non-runnable `genia` blocks without a visible warning label
* describe future work as already implemented
* leave feature status ambiguous

---

## Quality Bar

A chapter is only acceptable if it is:

* accurate
* engaging
* interactive
* skimmable
* implementation-faithful
* clearly labeled where behavior is partial
* disciplined about code fences and runnable examples

The reader should not be able to just glaze over and passively consume it.

They should have to:

* think
* predict
* try
* compare
* notice

---

## Example Code Fence Policy

### Runnable Genia example

```genia
square(x) = x * x

square(5)
```

### Non-runnable Genia example

**Illustrative sketch — not runnable**

```genia
eval(expr, env) = ...
```

### Non-Genia output block

```text
25
```

---

## Final Instruction

Write the Genia SICP book so that:

* the reader’s attention stays engaged
* learning feels active
* examples are trustworthy
* code fences are used correctly
* runnable vs non-runnable Genia blocks are clearly distinguished
* the book remains synchronized with the real language

After writing or revising:

* verify syntax examples carefully
* verify status labels
* verify code fence correctness
* verify that non-runnable `genia` blocks are clearly marked
