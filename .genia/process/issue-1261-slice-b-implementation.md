# #1261 Slice B implementation and verification evidence

Commits (oldest first): pre-flight `b809a9ce`; RED `0469396b`; GREEN `5d16b712`; fix `b4299e46`; docs `f3ced434`. This evidence file is committed after them.

## Regression on `f3ced434`

| Run | Result |
| --- | --- |
| `uv run pytest -n auto -q -m "not loopback"` | 7082 passed, 60 skipped, 1 failed (669s). The failure, `test_state_distillation_gates::test_every_cited_state_section_number_resolves...`, was an environment artifact: my `mkdocs build --strict` left an ignored `site/` tree that the test scans. After `rm -rf site`, the module passes (9 passed). No code or test change. |
| `uv run pytest -n auto -q -m loopback` | 31 passed (local loopback sockets were permitted). |
| `uv run python -m tools.spec_runner` | total=900 passed=900 failed=0 invalid=0 (baseline 874 + 26 new). |
| `uv run ruff check .` | pass |
| `tools/gen_mcp_language_profile.py --check`, `tools/gen_function_docs.py --check` | pass |
| `mkdocs build --strict` (after `stage_docs_for_mkdocs.py`) | pass |
| `python -m tools.code_documentation --base-ref origin/main` | 0 errors; 2801 legacy gaps (2 baseline entries removed, none added) |

Earlier run on GREEN `5d16b712` found 3 real failures (2 host-parity-gate, 1 harness-injection lint), fixed in `b4299e46`; the code-documentation checker found 14 undocumented bindings, also fixed there.

## Claim verification

- `immutable_bindings` (Python): the adapter auto-claims manifest names; the claim became true at GREEN (26/26 shared cases pass, 25 gated by it). The manifest entry was added in RED, so RED-to-GREEN HEAD states carried a provisional claim, as recorded in the RED evidence.
- C++ gap: `spec/known_host_gaps.json` entry `immutable_bindings`. The parity gate requires a `genia-2026#` tracking issue, so `tracking_issue` is `m0smith/genia-2026#1261`, with `genia-cpp#50` named in reason and removal condition. No C++ binary was run in this change; no C++ parity is claimed.
- Centralized writes (all in `src/genia/environment.py`): `set`, `assign`/`find_assign_target`, `define_function`, `merge_binding_metadata`, `set_host` (via `set`), and `commit_immutable_declaration` all consult `_immutable`. Evaluator pre-checks: `IrAssign` (before RHS), `IrImport`, `IrOpenFuncDef`, `IrOpenUse`. Named pattern and metacircular `define`/`assign` are covered through `set`/`assign` (host-local tests). Unchecked by design: trusted bootstrap writers (`set_internal`, builtins install, `mcp_worker_profile` pruning `del runtime.values[...]`).
- Lock scope: one module-level non-reentrant `threading.Lock` (`_BINDING_LOCK`), held only around the check-and-write in `set`/`assign` and in prepare/commit; never across initializer, RHS or annotation evaluation. Nothing under it calls another locking method. `test_binding_lock_is_released_after_every_rejection` and 200-iteration `test_commit_versus_racing_assign_never_loses_the_immutable_value` cover leak and race.
- Reentrancy: an initializer that writes the target name through `assign`/`set` makes the later commit fail ("already bound"); the write stands and nothing is rolled back (`test_reentrant_write_during_initializer_fails_commit_without_rollback`).
- Perf: recursion benchmark `fib(21)`, best of 3: baseline 1.215-1.233s vs 1.216-1.377s with the change (noisy; at most about 8-12% worst observed).

## Decisions and known limits

- Reserved-name rejection applies to the entry scope and the unregistered single-root harness only, not to module or nested scopes (design text: "Entry reserved-name check").
- Diagnostic wording is implementer-chosen (contract fixes none); asserted by the shared specs.
- Annotations on `=:` attach after commit with `target_kind="assignment"`; a failing annotation leaves the committed binding (non-transactional, like ordinary assignment).
- Unannotated `=:` is an ordinary statement for route/server/CORS discovery; `=:` annotated `@route`/`@server`/`@cors` is rejected.
- Not done (out of scope): Slices C-E, C++ implementation, N4/N6 debt, module-scope reserved names.
- STATE word budget: stayed within 43000 by distilling Slice A wire detail (now cites `core-ir-portability.md`) and R28 grounded-example prose.
