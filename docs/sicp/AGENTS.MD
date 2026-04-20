# SICP with Genia Agent Contract

This file defines how contributors must build and maintain `docs/sicp/`.

`docs/sicp/` is an executable learning surface, not a loose notes folder.
It must stay aligned with:

- `AGENTS.md`
- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
- `README.md`
- `docs/ai/LLM_CONTRACT.md`

If these disagree about implemented behavior, `GENIA_STATE.md` is the final authority.

## What To Write vs How To Write

- `OUTLINE.md` is the source of truth for WHAT to write.
- `WRITING_GUIDE.md` is the source of truth for HOW to write.
- This file defines workflow, validation, and truthfulness rules for maintaining the SICP learning system.

Do not improvise a different chapter set.
Do not write in a different teaching style.

## Non-Negotiable Truthfulness Rules

- Teach only implemented Genia behavior as implemented.
- If a concept is scaffolded, partial, experimental, or missing, label it clearly.
- Never present planned behavior as current behavior.
- Prefer references to canonical docs over restating semantics from memory.

Every chapter must include a `Reality Check` section with:

- `### ✅ Implemented`
- `### ⚠️ Partial`
- `### ❌ Not Implemented`

## Required Reading Before Editing

Read these first:

1. `AGENTS.md`
2. `GENIA_STATE.md`
3. `GENIA_RULES.md`
4. `GENIA_REPL_README.md`
5. `README.md`
6. `docs/ai/LLM_CONTRACT.md`
7. `docs/sicp/AGENTS.MD`
8. `docs/sicp/OUTLINE.md`
9. `docs/sicp/WRITING_GUIDE.md`

Then read any chapter files you plan to change.

## Chapter Set And Index Discipline

- Keep `docs/sicp/index.md` aligned with the actual chapter files that exist.
- Keep chapter ordering aligned with `OUTLINE.md`.
- If a chapter is added, removed, or renamed, update both `index.md` and `OUTLINE.md` together.

## Runnable Fence Contract

The test suite depends on this exact policy.

### Runnable Genia examples

A runnable Genia example must:

- use a `genia` code fence
- contain real executable Genia source
- be self-contained
- be immediately followed by a non-Genia expected-output block

Required shape:

````md
```genia
square(x) = x * x

square(5)
```

```text
25
```
````

Rules:

- the expected-output block must be the next code block
- expected output normally uses `text`
- expected output must match actual runtime output exactly
- each runnable block runs in a fresh environment during validation

### Non-runnable Genia examples

Use a `genia` fence only when the snippet is Genia-shaped.
If it is illustrative only, mark the line immediately above the fence with one of:

- `**Illustrative** — not runnable`

These blocks are skipped by the validator.

### Non-Genia content

Do not use `genia` for:

- shell commands
- expected output
- markdown templates
- JSON
- pseudocode in another language
- AST or IR sketches that are explanatory text

Use the correct fence such as `bash`, `text`, `json`, or `md`.

## Workflow

When editing `docs/sicp/`:

1. read the authority docs first
2. verify the target concept is actually implemented
3. follow the chapter template in `OUTLINE.md`
4. follow the pedagogy rules in `WRITING_GUIDE.md`
5. update `index.md` if chapter inventory changed
6. run `pytest tests/test_sicp_code_blocks.py`

If code or language semantics change in the repository, SICP chapters that teach that behavior must be updated in the same change.

## Sync Responsibility

Keep the SICP docs synchronized with:

- top-level repository instructions
- source-of-truth runtime docs
- executable examples and tests

If you discover drift in:

- `README.md`
- `GENIA_REPL_README.md`
- `AGENTS.md`

and that drift would mis-teach the same behavior covered in SICP, correct it as part of the same work when practical.
