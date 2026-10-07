# Tooling and examples record

> **Non-authoritative provenance record.** This file preserves, verbatim and unedited, text that was displaced
> from `GENIA_STATE.md` during the #1099 distillation. It is audit material, not part of the truth hierarchy:
> it does not define Genia behavior, and `GENIA_STATE.md` governs. Start with the release, design, and reference
> documents; open this file only to see the exact displaced wording.
>
> Baseline: `GENIA_STATE.md` at `d401f322c692e8c3620509854065692c2605c61a`. Scope: Documentation-publishing and `@doc` tooling sections (0.2-0.4) and the example-demo catalogue (section 11).
> Ledger: `docs/analysis/state-distillation-migration-map.json`.

## B020: baseline lines 354-386

Moved from GENIA_STATE.md@d401f322, lines 354-386 (ledger row B020, moved, sha256 69d19a7d6540e9b9)

~~~~~markdown
## 0.2) Repository documentation publishing workflow
Implemented today:

- repository docs are staged into a temporary MkDocs input tree by `tools/stage_docs_for_mkdocs.py`
- the published docs site uses MkDocs with the Material theme
- published sections include:
  - `README.md` as the homepage
  - `GENIA_STATE.md`
  - `GENIA_RULES.md`
  - `GENIA_REPL_README.md`
  - `docs/cheatsheet/*`
  - public-facing host interop docs under `docs/host-interop/`
  - per-release runnable examples under `docs/releases/` (see `docs/releases/README.md`)
  - `docs/strategy/release-roadmap.md`, staged individually as `strategy/release-roadmap.md` with a top-level Roadmap navigation entry; it remains non-authoritative planning guidance and no other `docs/strategy/*` file is published
- GitHub Actions docs workflow behavior is:
  - on pull requests: stage, validate, and build docs without deployment
  - on pushes to `main`: stage, validate, build, and deploy to GitHub Pages
  - after a successful Pages deployment, publish the generated Function Reference mirror to the GitHub Wiki only when the optional `WIKI_TOKEN` repository secret is configured
  - when `WIKI_TOKEN` is absent, skip all Wiki-specific setup and publishing steps without failing the Pages deployment
- docs validation in this phase includes:
  - strict MkDocs builds
  - semantic doc sync tests for protected cross-doc semantic facts
    - the protected facts surface is intentionally small and lives in `docs/contract/semantic_facts.json`
    - validation covers both public docs and LLM-instruction surfaces
  - cheatsheet validation tests
  - core documentation truthfulness and synchronization tests

Clarifications:

- the staging tree is a build artifact only; source-of-truth docs remain in their existing repository locations
- source annotations and the host documentation registry consumed by `tools/gen_function_docs.py` remain authoritative for both `docs/reference/**` and the generated Wiki mirror; generated pages must not be edited by hand
- the docs workflow is repository tooling, not part of the Genia language/runtime semantics

~~~~~

## B021: baseline lines 387-425

Moved from GENIA_STATE.md@d401f322, lines 387-425 (ledger row B021, moved, sha256 dceda65441ea1950)

~~~~~markdown
## 0.3) `@doc` linter (`tools/lint_doc.py`)

Implemented today:

- deterministic linter for `@doc` content strings
- located at `tools/lint_doc.py`; tests at `tests/test_lint_doc.py`
- accepts a raw `@doc` text string via the `lint_doc()` API or CLI
- returns structured `LintFinding` values with `rule_id`, `severity`, `message`, and optional `line`
- CLI modes:
  - inline: `python tools/lint_doc.py "doc string"`
  - file: `python tools/lint_doc.py --file path.genia`
- directory scan: `python tools/lint_doc.py --scan-dir dir/`
  - all modes support `--json` for machine-readable output
- `--require-coverage` derives the public surface from registered prelude autoloads
  plus the canonical non-internal Python-host builtin registry
- DOC008 requires canonical documentation for every derived public binding;
  DOC009 requires its category; registry entries with `stability: "internal"`
  are excluded
- file/scan modes extract binding names and include them in output
- `--scan-dir` prints a summary (files scanned, doc count, error/warning counts) to stderr

Implemented lint rules (phase 1):

| Rule | ID | Severity | Description |
|---|---|---|---|
| Summary required | DOC001 | error | Every `@doc` must have a non-empty first line |
| Summary shape | DOC002 | warning | Summary should end with `.`/`!`/`?` and avoid boilerplate prefixes |
| Allowed sections | DOC003 | error | Only `## Arguments`, `## Returns`, `## Errors`, `## Notes`, `## Examples` |
| No HTML | DOC004 | error | Raw HTML tags forbidden outside fences |
| No tables | DOC005 | error | Pipe-table markdown forbidden outside fences |
| Behavior mention | DOC006 | warning | `none(`, `flow`, `lazy` should appear in prose, not only in fences |
| Fence sanity | DOC007 | error | Fences must be balanced; `## Examples` fences allow only `genia`, `text`, or empty lang |

Not implemented yet:

- semantic NLP scoring or readability metrics
- public/private marker enforcement (no such marker exists in the language yet)
- cross-reference validation between `@doc` content and function signatures

~~~~~

## B022: baseline lines 426-445

Moved from GENIA_STATE.md@d401f322, lines 426-445 (ledger row B022, moved, sha256 b52a4e5b953ade6a)

~~~~~markdown
## 0.4) `@doc` style synchronization tests (`tests/test_doc_style_sync.py`)

Implemented today:

- style guide structure test: validates `docs/style/doc-style.md` has required sections, good/bad examples, and well-formed genia fences
- cheatsheet sync test: validates `docs/cheatsheet/core.md` and `docs/cheatsheet/quick-reference.md` have `@doc Quick Reference` sections with case markers linking back to the style guide
- linter-style guide alignment test: validates that the linter's `ALLOWED_SECTION_HEADERS`, `DISCOURAGED_PREFIXES`, and disallowed Markdown match the style guide
- prelude doc lint sweep: scans all `src/genia/std/prelude/*.genia` files for `@doc` strings and runs the linter over them

Not implemented yet:

- CI-gate enforcement (tests exist but are not yet wired into a required CI check)
- runnable example execution within the style guide itself (cheatsheet sidecar tests cover runnable examples separately)

Clarifications:

- these are repository tooling tests, not part of the Genia language/runtime semantics
- the linter is repository tooling, not part of the Genia language/runtime semantics
- rules are intentionally conservative and deterministic

~~~~~

## B309: baseline lines 6594-6607

Moved from GENIA_STATE.md@d401f322, lines 6594-6607 (ledger row B309, moved, sha256 9abf5a645b7005ec)

~~~~~markdown
## 11) Example demos shipped in-repo

Per-release curated runnable examples (one or more small examples per
release for its headline behavior) are published at `docs/releases/` —
see `docs/releases/README.md`.

- `examples/tic-tac-toe.genia`: canonical Format + Seq-compatible style example — two-player console tic-tac-toe using `Format`/`format(...)` for board rendering and list-side sequence helpers for data-driven winner detection
- `examples/ants.genia`: canonical pure deterministic ants colony simulation demo with optional CLI seed for reproducible runs
- `examples/ants_terminal.genia`: blocking terminal developer UI over the same colony simulation with CLI-configurable seed, ant count, step count, delay, world size, and pure/actor mode selection
- `examples/ants_actor.genia`: actor/coordinator version of the ants simulation — same colony rules, different execution structure
- `examples/ants_web.genia`: browser visualization over the same ants simulation using the current blocking HTTP helper, JSON endpoints, and a Canvas renderer in plain browser JavaScript
- `examples/validated_pipeline_demo.genia`: experimental first demo milestone for the Outcome-aware validated data pipeline direction — a file-mode demo covered by shared CLI spec `spec/cli/validated-data-pipeline-demo.yaml`; reads JSONL records from `examples/data/validated_pipeline_demo.jsonl`, validates each record using existing `parse_jsonl_record`, `validate_each`, `validate_record`, and `collect_validated` helpers, and emits clean records plus diagnostics; demonstrates the intended Outcome-aware validated data pipeline direction; does not add new helper/runtime semantics; Experimental
- `examples/r3_validated_pipeline_native_tests.genia`: R3 native-test example for the validated-pipeline surface — runnable through the native test runner (`genia test examples/r3_validated_pipeline_native_tests.genia`); covers Outcome-boundary preservation through `validate_each`, direct `validate_each(...) |> collect_validated(...)` composition, and a JSONL-style pipeline with clean/diagnostic observability; uses existing `test(name, body)` native-test syntax and existing validation/Outcome helpers; validated by `tests/unit/test_r3_validated_pipeline_native_test_examples.py`; this is selected native coverage only, not complete validated-pipeline coverage; Experimental
- `examples/mcp/validated_records.genia` and `examples/mcp/validated_records_broken.genia`: the R28 MCP demo — an Outcome-aware validated record pipeline (`validate_record`, `validate_each`, `collect_validated`) and the same program with one deliberate syntax error, used to show `genia_parse` diagnostics; both are ordinary Genia that runs unchanged through the Genia MCP server's `genia_run` (walkthrough `docs/mcp/demo.md`; R28 is not complete)
~~~~~

## B310: baseline lines 6608-6621

Moved from GENIA_STATE.md@d401f322, lines 6608-6621 (ledger row B310, moved, sha256 3f0c9b4398b64acb)

~~~~~markdown
- `examples/ollama_chat.genia`: Experimental application composition over existing R9/R10/R13/R14/R20 behavior — named `Ollama` and `Groq` Value Templates select independent open-function clauses for backend profile, inert request operation, and response-content extraction while generic code owns configuration precedence, immutable conversation state, HTTP status/JSON normalization, and complete Outcome continuation; local Ollama runs directly through `genia`, while Groq currently uses `hosts/python/exec_ollama_chat.py` to construct a provider-matched `chat_outbound` declassification authority for the existing protected HTTP sink; `GROQ_AUTHORIZATION` is the complete protected header value, including `Bearer `, because pure Genia cannot concatenate an ordinary prefix with a protected carrier; the launcher is Python reference-host realization, not portable language behavior or final launcher architecture; it does not add Ollama/Groq to R11 `model/4`, add language/Core IR semantics, weaken secret protection, or imply future-host networking; portable behavior and the Python protected-sink boundary are validated by `tests/native/ollama_chat_example.genia` and `tests/unit/test_ollama_chat_example.py`; Experimental

`examples/ants.genia` intentionally uses only currently implemented features:

- ordinary persistent maps/lists for explicit world, cell, and ant state
- world-owned active food/pheromone position lists plus food/pheromone totals for compact evaporation and summary calculation
- explicit seeded randomness via `rng(seed)` plus `rand_int(rng_state, n)` for reproducible weighted movement choice
- world-owned RNG threading through `step(world) -> world2`
- recursive stepping over ants and simulation ticks
- `sleep` for blocking frame delay
- text rendering via `print`

Implemented colony behavior in this phase:

~~~~~

## B311: baseline lines 6622-6635

Moved from GENIA_STATE.md@d401f322, lines 6622-6635 (ledger row B311, moved, sha256 961ef9afa57e6b57)

~~~~~markdown
- nest/home region tracking
- food pickup with decremented food quantity
- return-to-nest delivery with delivered-food counting
- pheromone deposit on return paths
- pheromone evaporation each evolve
- direction-aware candidate moves with weighted seeded choice

It is intentionally pure and explicit. It is **not** actor-based, does **not** add a scheduler, and does **not** introduce hidden mutable runtime state or new language syntax.
This is the canonical simulation teaching pattern in this phase: ordinary world value, deterministic `step(world) -> world2`, seeded RNG threaded through the world, and rendering from snapshots in outer shells.

`examples/ants_terminal.genia` intentionally stays within the same current runtime surface:

- imports and renders the same pure colony simulation helpers from `examples/ants.genia`
- sequential multi-ant stepping with the same nest/food/pheromone/weighted-movement semantics as the tested ants helpers
~~~~~

## B312: baseline lines 6636-6649

Moved from GENIA_STATE.md@d401f322, lines 6636-6649 (ledger row B312, moved, sha256 d76e6f3b33d5dd8e)

~~~~~markdown
- terminal rendering via `clear_screen()`, `move_cursor(x, y)`, and `render_grid(grid)`
- CLI configuration via `main(argv())` plus `cli_parse`
- explicit seeded randomness via `rng(seed)` plus `rand_int(rng_state, n)` for reproducible setup and movement
- visible text UI for development/teaching:
  - deterministic rendering priority: carrying ant `H`, ant `a`, nest `N`, food `*`, pheromone heat `#`/`+`/`:`, empty `.`
  - stats panel with mode, seed, evolve, remaining steps, ant/carrying counts, delivered food, remaining food, pheromone total, active trail count, and delay
  - CLI flags: `--seed`, `--ants`, `--steps`, `--delay`, `--size`, and `--mode pure|actor`
- pure mode steps the imported pure `ants.step(world)` model
- actor mode uses a coordinator actor session from `examples/ants_actor.genia` so the same terminal UI can compare the actor/coordinator execution structure

It is still a blocking terminal demo. It does **not** use `stdin_keys`, does **not** introduce a real-time event loop, does **not** provide pause/step/quit key controls, and does **not** add new language/runtime features. Same seed plus same config gives the same progression for a given mode.

`examples/ants_actor.genia` demonstrates actor-based concurrency using the same colony rules from `examples/ants.genia`:

~~~~~

## B313: baseline lines 6650-6663

Moved from GENIA_STATE.md@d401f322, lines 6650-6663 (ledger row B313, moved, sha256 d309965a134090ba)

~~~~~markdown
- coordinator actor owns the authoritative world state
- ant workers request sense data via `actor_call` and submit move intents back to the coordinator
- explicit coordinator-driven evolve loop for deterministic reproducibility
- reusable actor session helpers for the terminal UI: `actor_session`, `actor_session_world`, `actor_session_step`, and `actor_session_stop`
- imports and reuses the pure scoring/movement logic from `ants.genia` via `import ants`
- per-ant RNG splitting via `rng(seed)` / `rand_int` for seeded randomness
- string-tagged messages: `["sense", ant_id]`, `["move_intent", ant_id, move]`, `["evolve"]`, `["snapshot"]`, `["stop"]`

It is a teaching architecture layer — same colony behavior, different execution structure. It does **not** add new language syntax, does **not** introduce a scheduler, and does **not** require selective receive or timeouts.

`examples/ants_web.genia` is an application/demo layer over the existing HTTP surface:

- serves `GET /`, `GET /app.js`, and `GET /style.css` as static browser assets
- serves `GET /state` as a JSON-friendly snapshot with evolve, seed, mode, world size, ant positions/carrying status, nest cells, food cells, pheromone cells, delivered food, remaining food, and small stats
~~~~~

## B314: baseline lines 6664-6671

Moved from GENIA_STATE.md@d401f322, lines 6664-6671 (ledger row B314, moved, sha256 fbe20e3827f75ff9)

~~~~~markdown
- accepts `POST /reset` with JSON config (`seed`, `ants`, `size`, `delay`, `mode`) and `POST /step` to advance one evolve
- keeps one explicit server-memory session in a `ref`
- pure mode reuses `ants_terminal.start_session` over the pure `ants.step(world)` model
- actor mode reuses the coordinator session from `examples/ants_actor.genia`
- the browser uses Canvas drawing and client-side repeated `/step` calls for run/pause controls

It is a viewer over the current simulation/session logic. It does **not** implement browser-native Genia execution, a browser playground runtime, WebSockets, SSE, a generalized event loop, or a new server framework. Terminal ants remains the developer UI.

~~~~~
