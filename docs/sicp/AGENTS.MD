# Codex Prompt: Write Genia SICP Book in Head First Learning Style

## Objective

Write the Genia SICP book content in the **Head First learning style**, optimized for:

* engagement
* retention
* intuitive understanding
* “reptile brain” attention capture

This is NOT a traditional textbook.

This is an **interactive, brain-aware learning experience**.

---

## Required Reading (MANDATORY)

Before writing, you MUST understand:

* `AGENTS.md`
* `GENIA_STATE.md`
* `GENIA_RULES.md`
* existing `docs/sicp/*` chapters

And you MUST follow the **Head First design philosophy**, which includes:

* conversational tone
* visual thinking
* puzzles and interaction
* humor and surprise
* multiple learning modalities

Head First books intentionally use:

* stories
* jokes
* puzzles
* diagrams
* questions
* unusual layouts

to activate different parts of the brain and improve learning. ([Wikipedia][1])

---

## Cognitive Design Principles (CRITICAL)

You MUST incorporate these in every section:

### 1. Engage the “reptile brain”

The human brain prioritizes:

* novelty
* emotion
* surprise
* relevance

This is sometimes referred to as the “reptilian brain,” which responds to instinct and attention triggers. ([Alsi][2])

So:

* Avoid long dry explanations
* Break patterns frequently
* Use unexpected phrasing, humor, or contrast

---

### 2. Make the reader DO something

Every section must include at least one:

* question
* prediction
* mini-exercise
* “what do you think happens?” moment

---

### 3. Use conversation, not lecture

Bad:

> “A function is a mapping from inputs to outputs.”

Good:

> “What do you think this does?”

---

### 4. Chunk aggressively

* Small sections
* Short paragraphs
* Lots of whitespace
* One idea at a time

---

### 5. Use multiple representations

For the same idea, include:

* code
* explanation
* analogy
* visual structure (ASCII if needed)

---

### 6. Repeat—but differently

Reinforce key ideas using:

* slightly different examples
* different wording
* different contexts

---

## Required Structural Elements

Every section MUST include MOST of the following:

### 🧠 “Your Brain on Genia”

Explain what the reader is *feeling confused about*

### 🤔 “Think About It”

Ask a question BEFORE explaining

### 💡 “Aha!”

Explain the concept simply after tension is built

### 🧪 “Try This”

Small interactive code snippet

### ⚠️ “Common Trap”

Highlight a mistake

### 🔁 “Let’s Rewrite That”

Show improvement/refactor

### 🧩 “Puzzle”

Short challenge

---

## Tone Guidelines

* Conversational
* Slightly playful
* Occasionally humorous
* Directly address the reader (“you”)
* Avoid academic tone

---

## Example Transformation

### ❌ Traditional

```text
A recursive function calls itself.
```

### ✅ Head First Style

```text
Wait.

Did that function just… call itself?

Yes. It did.

And that’s not a bug—it’s the entire point.
```

---

## Code Presentation Rules

* Keep examples small
* Build complexity gradually
* Always explain *why*, not just *what*

---

## Genia-Specific Rules

### 1. NEVER introduce `if`

Genia uses pattern matching only.

### 2. Always use real Genia syntax

No pseudocode unless explicitly labeled.

### 3. Stay consistent with current implementation

Do not describe features that are not implemented.

---

## Output Requirements

When writing a chapter:

* Place in: `docs/sicp/01-...`, `02-...`, etc.
* Use Markdown
* Include section headers
* Include all interactive elements
* Include code blocks with `genia` language tag

---

## Example Section Skeleton

````md
## 1.1 What Is a Computation?

🤔 Think About It  
What does this do?

```genia
1 + 2 * 3
````

Pause. Don’t scroll.

...

💡 Aha!
Genia evaluates expressions by...

🧠 Your Brain on Genia
You might be thinking...

🧪 Try This
Change the numbers...

⚠️ Common Trap
Most people assume...

```

---

## Anti-Patterns (DO NOT DO)

- Long walls of text
- Formal academic tone
- Explaining everything before engaging the reader
- No interaction
- No humor
- Purely linear explanation

---

## Quality Bar

The chapter is correct ONLY if:

- it feels interactive
- it pulls the reader forward
- it forces thinking
- it is fun to read
- it still teaches accurately

---

## Final Instruction

Rewrite or generate content so that:

> The reader cannot passively consume it.

They must:
- think
- predict
- interact
- engage

---

## Standard Repository Reminder

- Keep docs aligned with implementation
- Update examples if behavior changes
- Mark sections:
  - ✅ implemented
  - ⚠️ partial
  - ❌ future

---

## Philosophy Reminder

This is not just documentation.

This is:

> **A guided experience of discovering computation.**
```

[1]: https://en.wikipedia.org/wiki/Head_First_%28book_series%29?utm_source=chatgpt.com "Head First (book series)"
[2]: https://www.alsi.net/Learning/Styles.htm?utm_source=chatgpt.com "Learning With Style - Active Learning Systems, Inc."
