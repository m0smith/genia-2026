# Genia `@doc` Style Guide

This file is the single source of truth for `@doc` formatting in Genia.

## 1. Purpose

`@doc` is structured documentation metadata for top-level bindings.

- It is not a comment.
- It is not executable code.
- It should stay concise enough that the function body remains easy to scan in source.

Use `@doc` to describe the public contract a reader should understand at the binding site.

## 2. Supported Format

Single-line:

```genia
@doc "Adds one to x."
```

Multiline:

```genia
@doc """
Adds one to x.

Returns:
- some(value) when present
- none("...") when missing
"""
```

## 3. Markdown Support (Strict Subset)

Allowed:

- paragraphs
- blank lines
- `-` bullet lists
- inline code
- fenced code blocks
- `*italic*`
- `**bold**`
- simple headings such as `## Arguments`, `## Returns`, `## Errors`, `## Notes`, and `## Examples`

Disallowed:

- HTML
- tables
- images
- complex nesting
- arbitrary Markdown extensions

Genia renders `@doc` as terminal-first lightweight Markdown, not as a full Markdown engine.

## 4. Required Structure Rules

- The first line must be a short summary sentence.
- Describe behavior, not implementation details.
- Mention `none(...)` or other failure behavior when it matters to callers.
- Mention Flow/lazy semantics when the binding is lazy, pull-based, single-use, or otherwise stream-sensitive.

## 5. Standard Sections

Only these section headers are allowed:

- `## Arguments`
  - Describe the caller-visible meaning of inputs.
- `## Returns`
  - Describe success results and `none(...)` behavior when relevant.
- `## Errors`
  - Describe clear runtime error cases or invalid-input behavior.
- `## Notes`
  - Capture short contract caveats such as laziness, single-use Flow behavior, or compatibility notes.
- `## Examples`
  - Show small realistic call shapes.

Omit sections that add no value.

## 6. Examples (Good vs Bad)

Good: short doc

```genia
@doc "Adds one to x."
inc(x) -> x + 1
```

Good: structured doc

```genia
@doc """
Return the user name for `record`.

## Arguments
- `record`: map-like user record

## Returns
- string name when present
- none("missing-key", ...) when the nested key is missing
"""
user_name(record) -> record |> get("user") |> then_get("name")
```

Good: pipeline / Option-aware doc

```genia
@doc """
Parse integer rows from `flow`.

## Returns
- Flow of parsed integers
- bad rows are dropped through `keep_some`

## Notes
- Flow stays lazy and single-use
"""
parsed_rows(flow) -> flow |> keep_some(parse_int)
```

Bad: long rambling prose

```genia
@doc """
This function is intended to be used in a variety of circumstances and has
many interesting implementation details that are helpful to understand before
reading the body.
"""
f(x) -> ...
```

Bad: leading filler

```genia
@doc "This function adds one to x."
inc(x) -> x + 1
```

Bad: implementation detail

```genia
@doc "Uses a recursive helper and two temporary maps internally."
f(x) -> ...
```

Bad: missing failure behavior

```genia
@doc """
Return the first item in `xs`.
"""
first(xs) -> ...
```

## 7. When To Use `@doc`

Use `@doc` for:

- public functions
- important top-level bindings that benefit from discovery/help output

Do not use `@doc` for:

- trivial helpers whose names already explain the contract
- local variables

## 8. Style Principles

- Write contracts, not essays.
- Optimize for scanning.
- Docs must not obscure the function body.
- If the name explains it, keep doc minimal.

## 9. Automated Linter (`tools/lint_doc.py`)

A deterministic linter validates `@doc` content against the rules in this guide.

### Usage

```bash
# Lint a single doc string
python tools/lint_doc.py "Adds one to x."

# Lint all @doc strings in a file
python tools/lint_doc.py --file src/genia/std/prelude/core.genia

# Scan an entire directory recursively
python tools/lint_doc.py --scan-dir src/genia/std/prelude

# Machine-readable JSON output (works with any mode)
python tools/lint_doc.py --json --file src/genia/std/prelude/core.genia
python tools/lint_doc.py --json --scan-dir src/genia/std/prelude
```

Human-readable output shows file path, line number, binding name (when detected), and rule ID:

```
core.genia:12:2 (my_func): [warning] DOC002: Summary line should end with '.', '!', or '?'.
```

`--json` output returns structured findings for tooling integration.
`--scan-dir` prints a summary with file/error/warning counts to stderr.

### Programmatic API

```python
from lint_doc import lint_doc

findings = lint_doc(doc_text)
for f in findings:
    print(f)  # [error] DOC001: @doc must begin with a non-empty summary line.
```

### Implemented Rules (Phase 1)

| ID | Severity | Rule |
|---|---|---|
| DOC001 | error | Summary required — first non-empty line must exist |
| DOC002 | warning | Summary shape — must end with `.`/`!`/`?`, must not start with `This function`, `This method`, or `Function to` |
| DOC003 | error | Allowed sections only — `## Arguments`, `## Returns`, `## Errors`, `## Notes`, `## Examples` |
| DOC004 | error | No HTML — raw HTML tags forbidden (except inside fenced code blocks) |
| DOC005 | error | No tables — pipe-table markdown forbidden (except inside fenced code blocks) |
| DOC006 | warning | Behavior mention — `none(`, `flow`, `lazy` should appear in prose, not only inside example fences |
| DOC007 | error | Fence sanity — fences must be balanced; `## Examples` fences accept only `genia`, `text`, or empty language tag |

### What the Linter Does NOT Check

- Semantic quality, readability scoring, or NLP analysis
- Whether every public function has a `@doc` (no public/private marker exists yet)
- Cross-reference between `@doc` content and actual function signatures
- Whether described behavior matches runtime behavior
- Spelling or grammar beyond the mechanical rules above

## 10. Validation

Automated tests enforce synchronization between this style guide, the book, and cheatsheets:

```bash
pytest tests/test_doc_style_sync.py -v
```

What is validated:

- This file retains its required sections (`## 1. Purpose` through `## 8. Style Principles`) and good/bad examples
- The linter's allowed section headers, discouraged prefixes, and disallowed Markdown match this guide
- `docs/cheatsheet/core.md` and `docs/cheatsheet/quick-reference.md` have `@doc Quick Reference` sections linking back here
- `docs/book/03-functions.md` has a `Documenting Functions` section whose Markdown subset and allowed headers are consistent with this guide
- Prelude `.genia` files pass the doc linter (no errors) when `@doc` annotations are present

What is NOT validated:

- Whether every public function has a `@doc`
- Semantic correctness of doc content
- Runnable example execution (covered by cheatsheet sidecar tests separately)
