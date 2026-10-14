# F2/P2-B implementation brief — failing tests only (issue #1067, tracker #1229)

**Do not start until the maintainer has approved contract §16 and A1–A3 on #1067** (see
`issue-1067-f2-p2-approval-gate.md`). Phase: `test`. Commit prefix
`test(scope): … issue #1067`. **No production file changes** (`src/`, `hosts/`, `tools/`,
`apps/`, workflows). No docs claim P2 behavior. Stop after committing the red tests; P2-C
must cite the red commit SHA.

## Rules for every red test

- Fails against current `main` (P1) for the reason stated in the table; run once and record
  the actual failure message in the P2-B evidence record `.genia/process/issue-1067-f2-p2-b-red-evidence.md`.
- Two red classes, labeled in the test id/docstring and enumerated in the evidence record:
  - **B (behavioral):** drives a real, existing entry point (subprocess/`_run_execution_mode`,
    `make_test_env` + runner, `mcp_worker.execute_source`, REPL, serve discovery, `run_source`
    on a caller root) and fails by assertion on observable behavior. Preferred.
  - **A (API-absence):** needs `create_entry_scope()`/the construction helper/the runtime-owned
    manifest, which do not exist yet; fails with the distinct, intentional marker
    `P2-C API missing` raised by the shared fixture (never a bare `AttributeError`, never a
    collection error). A-class tests exist only for accessor mechanics (Python-only).
- Tests that would pass against P1 for a trivial reason (alias R=E) are forbidden: the shared
  fixture asserts non-aliasing (see group 12) so a single-root run cannot count.
- Do not use `xfail`/skip to hide reds; the red commit is allowed to fail CI on its own branch
  only, and the PR description states that. Do not weaken or delete P2-A characterization tests;
  those that encode P1 shared-root facts are marked in the evidence record as "expected to flip in P2-D"
  with the flip reason.
- Portability: **shared-spec candidates** are listed per group; confirm capability vocabulary
  (`doc_help`, `multi_file_eval`, `open_functions` exist today; no new capability may be invented
  in this slice). Everything else is Python-only and labeled so in the module docstring (AGENTS
  portable-behavior placement rule). Native `.genia` tests are Python-host-only and are not portability proof.
- File placement: new modules `tests/unit/test_f2_p2_b_*.py` (one per group cluster), fixture
  helper `tests/unit/f2_p2_support.py`, native tests under `tests/native/`, candidate specs listed
  under `spec/` **as proposed names only** (spec files are written in P2-F when behavior exists;
  P2-B adds only specs that already fail meaningfully on P1, e.g. module `doc("own_helper")`).

## Shared fixture (`f2_p2_support.py`)

`separated_scopes()` builds R with the production host path, then `create_entry_scope()`;
returns R, E and a module loader producing a real M. Self-checks (each its own test): `E is not R`,
`E.parent is R`, `R.entry_scope() is E`, `R.runtime_scope() is R`, `E.runtime_scope() is R`,
`unit_scope()` is E for entry frames and M for module frames, binding sets of R and E disjoint at
setup, `E.autoloads == {}` while R's is non-empty. `wrong_accessor(boundary)` parametrizes the
variant each boundary test must also run (hands the consumer R where E is required and vice versa)
and asserts the test **fails** for the wrong accessor (mutation-style proof, implemented by
injecting the wrong accessor through the consumer's seam, not by editing production code).

## Red-test plan (12 groups)

| # | Group | Representative red tests | Fails on P1 because | Class | Portable? |
|---|---|---|---|---|---|
| 1 | Distinct runtime/entry registration (T-D6a, T-D1e) | `create_entry_scope()` returns child with rebind-parent and own unit id; second call raises; `entry_scope()` is E from R/E/M; `set_host` routes `runtime-public`→R, `entry-only`→E; `entry-only` on an unregistered root installs into R; `entry-only` of a runtime-owned name raises | API absent; accessors alias R | A | Python-only |
| 2 | Runtime-owned collisions incl. `map_acc` (T-D1a, T-D1c) | four §9.0 collision rows identical with E registered for `first`, `map`, `map_acc`, `rows/0`+`rows/1`, `log = 5`; distinct arities merge; duplicate-arity error text identical; manifest drift test: every top-level declaration of every autoload-target prelude file (assignments included, `web`/`resource`/`execution` excluded) is in the manifest, manifest ⊇ autoload names, manifest not shrunk by pruning; `map_acc` is owned but not catalogued | child-E probe shadows/hides; registry-only derivation misses ~103 names | A (collisions), B (drift test reads prelude sources, fails because manifest missing) | Python-only |
| 3 | Prelude access to entry-only bindings (T-D1b) | non-runtime-owned entry name `zzz` is absent from R and unreadable by prelude/R-closure code; entry-declared runtime-owned name lands in R and `E` records it; prelude local assignment never reaches E (regression from #1205) | shared root exposes `zzz` | A+B (native twin: prelude function referencing a free entry name raises `Undefined name`) | native twin candidate; Python mechanics |
| 4 | Module isolation and fallback eligibility (T-D3) | module function, module top-level (import-time), contribution closure reads of an E-resident name: with `GENIA_STRICT_MODULE_SCOPE=1` → `Undefined name` `NameError` (also at import, loading guard cleared); default → value + exactly one warning per distinct (module identity, name), none on repeat; warning has no value/path/exception text; event set is readable per run; no fallback for writes, `doc`/`meta`/`help`, exports, prelude code, `empty_env()` lookups, or runtime-owned names | P1 returns the entry value, ignores the variable, emits no warning, has no event set | B via subprocess/`run_source` on a real entry+module (strict-mode tests fail with "returned 5, expected NameError"); event-set accessor tests A | strict-mode `NameError` shape is P3-portable, **not** P2; P2 is Python-only host-local |
| 5 | Scope-bound reflection (T-D2) | `doc`/`meta`/`help` from entry, module, prelude, indirect `map(doc, names)`, transferred callable, alias, user-rebound `doc`; function-local binding named like target wins; module reflection of an E-resident entry name stops resolving (no fallback); module `doc("own_helper")` resolves; host `env.get("doc")` is R-bound; help overview identical from any scope | module string reflection uses R; no frame-first lookup | B (module own-helper and local-wins fail by assertion on real modules) | **shared-spec candidates:** module `doc("own_helper")` (`doc_help`+`multi_file_eval`), local-binding-wins (`doc_help`); catalogue/sink ownership Python-only |
| 6 | Metacircular `eval` isolation (T-D4) | `eval(quote(f(1)), empty_env())` with entry-owned `f` → `NameError` from entry and from a module; after `define` works; runtime-owned (`map`) works; entry-declared runtime-owned name works; module-owned name unreachable from entry's base; base is child of R only | `empty_env()` reads live entry names | B | single-file entry case = shared-spec candidate if an `eval` capability exists, else Python-only |
| 7 | MCP pruning and forbidden reintroduction (T-D6d) | `mcp_worker.execute_source` prunes R, then registers E, E starts empty; denied binding names undefined and **not recreated by write-through** (entry defining a denied builtin name that is not prelude-owned stays in E and is not visible to R; a pruned-but-prelude-owned name stays manifest-owned yet pruned binding is not resurrected); allowed program runs unchanged; no host binding installed after pruning; pruned catalogue from E | no E exists; prune acts on shared root | A+B (security) | Python-only (security) |
| 8 | Entry construction and execution modes (T-D6b) | AST/source guard: no program evaluated outside the construction helper (matches `run_source` **and** `Evaluator(...).eval_program`); each of the 13 sites (repl, debug_stdio, serve, pipe, command, file, make_test_env, 3 fixtures, ollama, mcp_worker, mcp_host) yields `entry_scope() is not runtime_scope()`; `run_source` never registers E; REPL keeps one E per session; CLI `main` dispatch finds `main` in E | raw `make_global_env` sites | A+B (CLI subprocess `main` dispatch fails only once E physical — keep as flip target) | Python-only |
| 9 | Native-test registration | `make_test_env` returns E (or both); fixtures `entry-only` into E; registration list written/read on E; `identify_tests` and the runner evaluate in E; imported module `@test` excluded; legacy single-root registrar still works | fixtures/list on R | A+B | native test twin for isolation; runner mechanics Python-only |
| 10 | Debugger and REPL visibility (T-D6c) | `:env` lists entry-declared names incl. recorded runtime-owned ones and not R bindings; debugger `globals` for entry frames show E view, module frames show M view; debug hooks/mode written and read on R (stepping reaches callbacks, modules, prelude frames); protected payloads stay redacted | all scopes alias R | A+B | Python-only |
| 11 | #1220 help catalogue ownership (T-D5) | runtime accessor exists for catalogue ownership; AST guard fails on `.root()` outside `environment.py` and `.autoloads` receivers not from `runtime_scope()` (reviewed allowlist, fails on current `builtins.py` reads); with real R/E/M and control `E.autoloads == {}`: `help()` identical from E, M, R; entry/module names never in families; pruned R shows pruned catalogue from E; wrong-accessor variant (catalogue read from lookup scope) empties `help()` and fails the test | guard fails on current reads; E/M catalogue reads via lookup scope not yet testable | A (guard is B and fails by assertion on current source) | Python-only |
| 12 | #1221 non-aliased fixtures and wrong-accessor variants | one test per boundary × accessor in {runtime, entry, unit}: CLI `main`, native discovery, serve annotation discovery + `web` alias, REPL `:env`, debugger globals, sinks (`_emit_error`, `_write_stdout/_write_stderr`), reflection/tooling (`gen_function_docs`, `lint_doc` stay on runtime), MCP pruning; fixture self-checks (group 1 list); a single-root run is rejected by the fixture | stubs only; accessors alias R | A | Python-only |

Sink/debug specifics (inside groups 8–10): sinks read through the runtime accessor from R even when
E lacks them (P2-A shows P1 falls back to process streams for an inherited child sink); debug
hooks/mode on R; native-test list on E.

## Evidence record contents (`…-p2-b-red-evidence.md`)

Test count per group and class (A/B); for each red test the first failure line on P1; the list of
P2-A tests expected to flip; the shared-spec candidates deferred to P2-F with their intended
capability; confirmation that `git diff origin/main --stat` shows only `tests/**`, `spec/**` (only
specs that fail meaningfully on P1) and `.genia/process/**`; commands run; full-suite pass/fail
unaffected outside the new red files (run both partitions; disclose pre-existing load-sensitive
failures as P2-A did).

## Validation before the P2-B PR

`uv run ruff check .`; `uv run python -m tools.code_documentation --base-ref origin/main` (new test
helpers need documentation); the new modules run and fail as recorded; both regression partitions run
with the new reds isolated and counted; doc/semantic sync tests unaffected (no authority doc edits).
MCP language-knowledge impact: none for this slice.

## Hand-off to P2-C

P2-C starts from the red SHA, implements `create_entry_scope()`, construction helper, manifest and
write-through, `set_host` routing, and turns groups 1–3 and the construction half of 8–9 green.
Groups 4–7, 10–12 are completed by P2-D/P2-E. A red test may only be edited with a recorded reason
(wrong expectation vs contract §16), never to make it pass.
