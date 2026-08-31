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
- On the **public surface** (names exported by autoloaded prelude modules, plus non-`internal` host builtins), `## Arguments` and `## Returns` are **required** for any function that takes arguments or returns a value.
- `none(...)` / absence behavior **must** be stated whenever the function can produce it (this is the single most common real omission — e.g. `first`).
- Trivial, name-explains-it helpers may remain single-line (see §7); everything else uses the structured form.

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
| DOC008 | error* | Coverage — every public binding must carry a `@doc` (`*` enforced only in `--require-coverage` mode) |
| DOC009 | error* | Category — every public `@doc` must be paired with `@category` (`*` enforced only in `--require-coverage` mode) |

### What the Linter Does NOT Check

- Semantic quality, readability scoring, or NLP analysis
- Whether prose reads well (coverage — every public binding having a `@doc` and `@category` — is now checked by DOC008/DOC009 in `--require-coverage` mode)
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
- core `@doc` surfaces remain consistent with this guide
- Prelude `.genia` files pass the doc linter (no errors) when `@doc` annotations are present

What is NOT validated:

- Semantic correctness of doc *content* (public-binding coverage is enforced by DOC008/DOC009 — see §11–§12)
- Semantic correctness of doc content
- Runnable example execution (covered by cheatsheet sidecar tests separately)

## 11. Function Metadata (`@meta` family)

`@doc` describes the contract; the metadata annotations classify the binding so it can
be grouped, badged, versioned, and cross-linked in generated docs and in `help()`.
These annotations are already parsed by the language (`@doc`, `@meta`, `@since`,
`@deprecated`, `@category`) and surfaced by `help()` / `doc("name")`.

### Canonical keys

- `@category "<family>"` — **required on the public surface.** The family the function
  belongs to (`list`, `map`, `math`, `flow`, `string`, `option`, `io`, …). Drives index
  grouping and the page breadcrumb.
- `@since "<release>"` — release the function was introduced (e.g. `"R3"`). Renders a
  "Since" badge.
- `@deprecated "<guidance>"` — present only when retiring; the string names the
  replacement. Renders a deprecation banner and moves the function to a deprecated list.
- `@meta {stability: "<level>"}` — `stable` (default), `experimental`, or `internal`.
  `internal` bindings are resolvable but excluded from the generated reference.
- `@meta {see_also: ["name", ...]}` — related function names; rendered as cross-links.

### Canonical shape

```genia
@doc """
Return the first element as an absence-aware Option.

## Arguments
- `xs`: list value

## Returns
- `some(value)` for the first element
- `none("empty-list")` for `[]`
"""
@category "list"
@since "R3"
first(xs) = ...
```

Ordering convention: `@doc` first, then `@category`, then `@since` / `@deprecated`, then
any `@meta {...}`. Keep metadata to the keys above; unknown keys are ignored by the
generator and should be avoided.

## 12. Documentation Coverage (DOC008 / DOC009)

The public surface must be fully documented. Two coverage rules run over the source in
`--require-coverage` mode (used by CI); they operate at the *binding* level, not on the
`@doc` string, so ordinary `lint_doc(text)` behavior is unchanged.

- **DOC008 (error):** every public binding must carry a `@doc`. "Public" = a name
  exported by an autoloaded prelude module, or a non-`internal` host builtin once the
  host doc registry lands. Internal helpers (e.g. `*_impl`) and names marked
  `stability: "internal"` are exempt.
- **DOC009 (error):** every public `@doc` must be paired with `@category`.

### Usage

```bash
# Coverage sweep over the prelude (fails on any undocumented / uncategorized public name)
python tools/lint_doc.py --scan-dir src/genia/std/prelude --require-coverage
```

Rollout is phased: coverage is enforced on the prelude surface first; host builtins join
the gate when their doc registry is added.
