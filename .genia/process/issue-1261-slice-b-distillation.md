# #1261 Slice B post-audit distillation (evidence record)

Phase: distillation. Base: `7583f69c641d9c0c1f4419a6d0abd256fc16305f` (independent truth re-audit PASS reported by the maintainer; not self-certified here). Documentation commit: `ae76c7ce`.

## Extracted durable content and destination
| Content | Destination |
| --- | --- |
| Python executes `name =: expr`; closed/pattern declarations parse/lower only (`model-b-not-implemented`); default-open, linking, closed publication unimplemented | already in STATE §3, RULES, REPL README, README, cheatsheets (verified, unchanged) |
| C++ gap tracked at genia-2026#1261, parser/lowering genia-cpp#50 | STATE §3 (one-line precision), host matrix |
| Slice A/B labels and handoff pointers removed | book `03-functions.md`, `core-ir-portability.md`, `HOST_CAPABILITY_MATRIX.md` |

## Files updated
`GENIA_STATE.md` (net -3 whitespace tokens; 42996 `split()` words, limit 43000), `docs/book/03-functions.md`, `docs/architecture/core-ir-portability.md`, `docs/host-interop/HOST_CAPABILITY_MATRIX.md`.
Verified without change: GENIA_RULES, GENIA_REPL_README, README, core/unix-power-mode cheatsheets, `semantic_facts.json`, generated `apps/mcp/mcp.genia`, LLM contract, design doc (non-authoritative, left as history).

## Not changed / still owned
M4 (process-wide lock), M6/N5 (checker characterization before first prelude adoption), race-test hardening (`group.functions`, timed joins): #1261. genia-cpp#51 (Cell staged-send quiescence race) is a separate required correction; no waiver. No host parity claimed.

## Verification (local, Python 3.12)
- tests/doc + doc-style + 5 cheatsheet modules + R28 registry/profile: 614 passed, 35 skipped
- `gen_mcp_language_profile.py --check`, `gen_function_docs.py --check`, `lint_doc.py --require-coverage`: pass
- code-documentation vs origin/main: 9636 records / 2801 legacy gaps / 1 exclusion / 0 errors; `test_code_documentation.py` 26 passed
- `mkdocs build --strict`: pass (generated `site/` removed; it trips a STATE-citation gate otherwise)
- Not run locally: full regression, Docker/C++ workflow, final-head CI.

Handoff directory `.genia/process/tmp/handoffs/issue-1250-slice-a` is Slice A evidence; not touched.
