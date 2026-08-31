# Proposal — Genia Function Documentation Standard & Generated Reference

Status: **DIRECTION APPROVED** (see §7 for decisions)
Author: (drafted with Claude)
Scope: standardize how every out-of-the-box function is documented, then generate an
alphabetical function reference with one page per function, and keep it maintained
automatically.

---

## 1. TL;DR

You were right: a standard already exists, and it is not being followed.

This proposal does four things:

1. Confirms and consolidates the standard you already have (`docs/style/doc-style.md`
   + the `@meta` annotation family) into **one** authoritative contract.
2. Upgrades three rules that are the reason it drifts: **coverage is mandatory**,
   **built-ins get doc parity**, and **the source annotations are the single source of
   truth** for all generated docs.
3. Generates an **alphabetical function reference** and a **per-function page** directly
   from `@doc` / `@meta` in the source — no hand-maintained duplicate.
4. Wires generation + linting into CI and `AGENTS.md` so it cannot silently rot again.

Two decisions need your call before build; see §7.

---

## 2. What already exists (the standard you have)

The machinery is real and mostly good. Nothing here is greenfield.

* **Style guide:** `docs/style/doc-style.md` — "single source of truth for `@doc`
  formatting." Defines the summary-first rule, the allowed Markdown subset, and the
  five allowed section headers: `## Arguments`, `## Returns`, `## Errors`, `## Notes`,
  `## Examples`.
* **Linter:** `tools/lint_doc.py` — rules `DOC001`–`DOC007` (summary present, summary
  punctuation / no boilerplate, only-allowed headers, no HTML, no pipe tables, behavior
  tokens outside fences, balanced fences). Has `--file`, `--scan-dir`, and `--json`.
* **Annotations the language already parses:** `@doc`, `@meta`, `@since`, `@deprecated`,
  `@category` (plus `@test`, `@route`, `@server`, `@cors`). Confirmed in
  `src/genia/evaluator.py` (the supported-annotations error message) and
  `tests/unit/test_annotation_metadata.py` / `test_prefix_annotations.py`.
* **Runtime surface:** `help()` renders `@doc` + a metadata summary (Category / Since /
  Deprecated) via `env.get_metadata(name)`, and `doc("name")` returns the doc metadata
  or `none("missing-doc", {name})`. See `src/genia/builtins.py`.
* **Instruction hook:** `AGENTS.md` already has a `## @doc Style Validation Rule`
  section tying the style guide to the cheatsheets and book.

So the contract, the annotations, the linter, and the runtime `help`/`doc` surface are
all in place today.

---

## 3. Why it isn't being followed (evidence from the tree)

* **Structure adoption is ~1/3.** 259 `@doc` bindings live across 23 prelude files,
  but only **8** files use the structured `## Arguments` / `## Returns` sections
  (`actor, awk, eval, list, stream, syntax, validation, web`). `list.genia` is exemplary;
  `math.genia` is mostly bare one-liners. Same standard, wildly different output.
* **Metadata adoption is zero.** `@category` / `@since` / `@deprecated` / `@meta` are
  supported and surfaced by `help()`, yet **no prelude file uses them**. Every function
  is uncategorized and unversioned, so an alphabetical index cannot group or badge them.
* **Built-ins are undocumented by design.** There are ~**215** host builtins registered
  via `env.set(...)` in `builtins.py`. The help system *explicitly* punts on them:
  `help("print")` shows "a generic note instead of a second host-side docs registry."
  There is no doc source for the entire host surface, so any generator would emit a hole
  exactly where beginners look first (`print`, `map_put`, `parse_int`, `argv`, …).
* **The linter is opt-in, not enforced.** `AGENTS.md` requires prelude `@doc` strings to
  pass the linter *"when present."* Nothing fails CI when a public function has **no**
  `@doc` at all — `DOC001` only fires once a `@doc` exists. Coverage is unmeasured.
* **No reference exists.** `mkdocs.yml` has State/Rules/REPL/Cheatsheets/Design but no
  per-function reference and no alphabetical index.

Net: the standard is sound; enforcement and coverage are the gap, and built-ins are a
structural blind spot.

---

## 4. The proposed standard (v2)

Keep everything in `doc-style.md`. Add/upgrade the following. This becomes the amended
`docs/style/doc-style.md` on approval.

### 4.1 Source annotations are the single source of truth

All human-facing function documentation lives in `@doc` + `@meta` at the binding site.
The reference site, the alphabetical index, `help()`, and `doc()` are all **projections**
of these annotations. No function doc is written directly into a Markdown page; pages are
generated (§5). This is the rule that stops drift.

### 4.2 `@doc` structure (tightened)

* First line: one-sentence summary, ends with `.`/`!`/`?`, no filler ("This function…").
  *(existing DOC001/DOC002)*
* **Non-trivial functions MUST include `## Arguments` and `## Returns`.** Add `## Errors`
  when it can fail or reject input, `## Notes` for laziness/single-use/Flow or
  compatibility caveats, and `## Examples` for anything non-obvious. Trivial,
  name-explains-it helpers may stay single-line (existing rule 7 preserved).
* Absence/`none(...)` behavior must be stated whenever a function can return it
  (promotes the guide's current "mention when it matters" to a hard rule for the public
  surface — this is the most common real omission, e.g. `first`).

### 4.3 `@meta` becomes required on the public surface

Adopt the already-supported annotations as a required, canonical block:

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

Canonical metadata keys (all optional except `category`):

| Key          | Meaning                                          | Drives in the reference          |
|--------------|--------------------------------------------------|----------------------------------|
| `category`   | family/grouping (`list`, `map`, `math`, `flow`…) | index grouping + page breadcrumb |
| `since`      | release/version introduced (`"R3"`)              | "Since" badge                    |
| `deprecated` | replacement guidance if retiring                 | "Deprecated" banner              |
| `stability`  | `stable` / `experimental` / `internal`           | stability badge; hide `internal` |
| `see_also`   | related function names                           | cross-links between pages        |

(`category`, `since`, `deprecated` already render in `help()`; `stability`/`see_also`
are new and additive.) A new linter rule enforces presence of `category` on public names.

### 4.4 Built-in doc parity (closes the 215-function hole)

Built-ins must carry the **same** `@doc` + `@meta` shape as prelude functions so a
reader cannot tell "who implemented it" from the docs. Recommended mechanism (final
implementation is part of the build task, but the standard fixes the *shape*):

* A single machine-readable **host doc registry** — one entry per public builtin with
  `doc`, `category`, `since`, `stability`, `see_also` — attached to the binding via the
  existing `env.assign(..., metadata=...)` path so `help()` / `doc()` light up for
  builtins too, and validated by the **same** `lint_doc.py`.
* Builtins deliberately *not* meant for direct use (internal bridges) are marked
  `stability: "internal"` and excluded from the reference (but still resolvable).

This makes "all built-in and prelude functions and anything else out of the box"
a single uniform corpus.

### 4.5 Coverage is mandatory and measured

New linter rule **`DOC008` (error): every public name must have a `@doc`.** "Public"
= names exported by autoloaded prelude modules + registry builtins not marked
`internal`. New rule **`DOC009` (warning→error): public `@doc` must declare
`@category`.** Coverage becomes a number CI can gate on, so a new undocumented function
fails the build instead of quietly shipping.

---

## 5. The generated reference (index + per-function "wiki" pages)

Generated by a new `tools/gen_function_docs.py` that boots the Genia environment,
enumerates the public surface (prelude autoloads + non-internal registry builtins),
pulls each function's `doc()` + metadata, and emits:

* **Alphabetical index** — every out-of-the-box function A→Z, with signature/arities,
  one-line summary, category, and stability/since badges, linking to each page. A
  secondary by-category view is cheap to emit from the same data.
* **One page per function** ("wiki page") — name, arities/shapes, full rendered `@doc`
  (Arguments/Returns/Errors/Notes/Examples), metadata badges, `see_also` cross-links,
  and a "defined at" source link.

Everything is derived from source, so the pages are always truthful and never
hand-edited. Location depends on decision (A) in §7.

---

## 6. Keeping it maintained automatically

1. **Generator is the only writer.** Pages are build output, checked in for GitHub
   Pages but never edited by hand.
2. **CI staleness gate.** A CI step runs the generator and `git diff --exit-code` on the
   generated tree — if a function's `@doc`/`@meta` changed and the reference wasn't
   regenerated, the build fails. Same pattern the repo already uses for cheatsheet
   case-tables.
3. **Lint gate promoted to required.** `tools/lint_doc.py --scan-dir` (prelude + builtin
   registry) runs in CI as an **error** gate, including the new `DOC008`/`DOC009`
   coverage rules.
4. **`AGENTS.md` codifies it.** Extend the existing `## @doc Style Validation Rule`
   section: annotations are the source of truth; new/changed public functions require
   `@doc` + `@category`; regenerate the reference in the same change; CI enforces both.
   This is the "update the project instructions" piece.

---

## 7. Decisions I need from you

**(A) Where do the per-function "wiki" pages live?**

* **Recommended — mkdocs site** (`docs/reference/functions/<name>.md` + `docs/reference/index.md`,
  added to `mkdocs.yml` nav). Reuses your existing GitHub Pages build, can be enforced by
  CI, and lives in-repo with the source.
* **GitHub Wiki** (the literal wiki.git). Familiar "wiki" UX but a separate repo, harder
  to gate in CI and to keep in lockstep with source.
* (We can also mirror mkdocs → GitHub Wiki if you want both.)

**(B) Built-in docs — now or phased?**

* **Recommended — build the host doc registry now** so the reference is complete on day
  one (no "documented in a later phase" holes for `print`, `map_put`, etc.).
* **Phase it** — ship prelude coverage first, backfill builtins next. Faster first cut,
  temporary holes.

Once you pick, I'll finalize the amended `doc-style.md`, then move to backfilling docs,
the generator, and the CI wiring (tasks 2–4).

---

## 7a. Decisions (locked)

* **(A) Wiki location → Both.** mkdocs pages under `docs/reference/functions/<name>.md`
  (+ `docs/reference/index.md`) are the generated source of truth; a mirror step also
  publishes them into the GitHub Wiki so both surfaces exist and stay identical.
* **(B) Built-ins → Phased, prelude first.** Ship full prelude coverage + the generated
  reference now; the `internal`-aware host doc registry for the ~215 builtins lands as a
  fast-follow. Until then the reference lists built-ins as "documentation pending" rather
  than omitting them, so the hole is visible and tracked, and `DOC008` coverage is
  enforced on the prelude surface first (builtins added to the gate when their registry
  lands).

Build order from here: (1) amend `docs/style/doc-style.md` to v2, (2) backfill prelude
`@doc`/`@meta` to pass the linter + new coverage rules, (3) `tools/gen_function_docs.py`
→ mkdocs index + per-function pages + Wiki mirror, (4) CI gates + `AGENTS.md`.

---

## Progress log

**Step 1 — standard (DONE).** `docs/style/doc-style.md` amended to v2: `## Arguments`/`## Returns`
now required on the public surface; new §11 (Function Metadata / `@meta` family) and §12
(Documentation Coverage, DOC008/DOC009). Sync test `tests/unit/test_doc_style_sync.py` still
passes (19/19).

**Step 1 — linter (DONE).** `tools/lint_doc.py` gains DOC008 (public binding missing `@doc`)
and DOC009 (public `@doc` missing `@category`) as a binding-level coverage pass behind
`--require-coverage`, plus `--public-names <file>` to scope coverage to the true exported
surface. `lint_doc(text)` / DOC001–007 unchanged. Fixed the identifier regex to accept
`?`/`!`-suffixed names (predicates like `empty?`) and made the scanner skip lines inside
`@doc` bodies and fenced code.

**Step 2 — prelude backfill (DONE for coverage).** Added `@category` to **all 217** public
prelude functions (derived from each function's autoload module). Verified against the
runtime: 217/217 now report a `category`, and `lint_doc --scan-dir src/genia/std/prelude
--require-coverage --public-names …` reports **0 errors, 0 warnings**. Full unit suite:
**2685 passed** (one unrelated pre-existing py3.10 f-string collection error in
`test_r12_grounded_composition.py` was skipped, not caused by this change).

*Optional follow-up (not required by the standard):* structural enrichment of one-line
`@doc`s into `## Arguments`/`## Returns` for the ~15 modules that are still summary-only.
Allowed to stay one-line for trivial helpers, so this is a quality pass, not a gate.

**Next:** Step 3 — `tools/gen_function_docs.py` → alphabetical index + per-function pages
(mkdocs) + Wiki mirror; Step 4 — CI gates + `AGENTS.md`.

**Follow-up enrichment (DONE).** Converted thin one-line `@doc`s into the structured
form for 40 non-trivial functions across the four core modules: `map` (6), `string` (5),
`option` (15), `flow` (14). Trivial helpers were intentionally left as concise one-liners
per §7. Whole prelude still lints clean (0 errors / 0 warnings) and loads (217/217).

**Step 3 — generated reference (DONE).** `tools/gen_function_docs.py` boots the runtime,
reads each public function's `@doc`/`@category`/arities/source, and emits:
`docs/reference/index.md` (alphabetical A-Z table + by-category view) and
`docs/reference/functions/<slug>.md` (one page per function, 217 pages). It also manages a
generated nav block in `mkdocs.yml` and writes a flat GitHub Wiki mirror to `.tmp/wiki/`.
`tools/stage_docs_for_mkdocs.py` now stages `docs/reference`, and `mkdocs build --strict`
passes with all 217 pages wired into nav and no broken links. `tools/publish_wiki.sh`
regenerates and pushes the wiki mirror. `--check` mode reports staleness for CI.

**Still open:** Step 4 — add generation + `--check` staleness gate + `--require-coverage`
to CI (`.github/workflows/docs.yml` / `ci.yml`) and codify the workflow in `AGENTS.md`.
