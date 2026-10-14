# F2/P2-D evidence — scope consumer migration (issue #1067, tracker #1229)

Stacked on P2-C (PR #1239, head `cb593207a635fe46ffa26cc10387aee6b2cac442`) which is stacked on P2-B (PR #1235, red-test SHA
`163f5160f6486cb56fc78211edd0afc261a13c18`). Branch `issue-1067-f2-p2-d-consumers`. **Not releasable alone**: the P2-E module
fallback is not delivered; do not merge the stack to `main` before P2-E/F/G. #1067, #1220, #1221, #1229, #1230, #1238 stay open.
Final implementation/documentation head: `2e813704` (a later commit adds only this record and the review handoff under `.genia/`).

## Baseline reproduced before changes

`P2-C 75/75 green; P2-D 37 red (+50 already green); P2-E 13 red (+4 green)` (per-test mapping from the P2-B evidence table).
The 37 red P2-D cases by test function: reflection (B5_A binding identity ×4, scope-bound identity ×3; B5_B parameter-first ×3,
module-evaluation binding ×4, module-local ×3, native twins ×2) = 19; B6_A `eval` ×1; B9_A runtime-owned annotation ×1; B10_A debug hooks ×1;
B10_B REPL ×1; B11_B guards ×2; B12_A wrong-accessor ×9 and REPL wrong-owner ×3. 13 P2-E: B4_A events ×1, exclusions ×7; B4_B distinct pairs ×1,
warn-once ×3, strict capture ×1.

## What P2-D delivers (Python reference host)

- **Scope-bound reflection (§16.2).** `Evaluator._resolve_identifier` is the single identifier-resolution helper for variable reads, call
  targets and both pipeline stage paths. A runtime `doc`/`meta`/`help` (value-marked via `Env.SCOPE_BINDER_ATTR`, never by name) is returned bound to
  the evaluating Env and cached per Env (stable identity per scope; different scope, different object). Already-bound callables, aliases and user
  rebindings are returned unchanged; host `Env.get` still returns the raw root-bound callable; the help catalogue and sink stay runtime-owned.
- **`eval` (§16.4).** No code change: `empty_env()` was already based on R, so after P2-C topology E-resident names are not implicitly visible
  (tests added for entry and module; `define` supplies values). One P2-B test line was repaired (below).
- **Consumers (§16.6).** REPL `:env`, debugger globals, CLI `main` dispatch and native-test discovery use the entry scope plus its declared
  runtime-owned names (`Env.inspection_bindings`, `Env.binding_owner`); `run_source`/debug state live on R once E is registered
  (`Env.debug_state_scope`). Serve discovery needed no change (chain lookup already finds write-through names).
- **#1220.** The two catalogue reads use `runtime_scope()`; AST guards (B11_B) pass; help identical from R/E/M and pruned R (B11_A).
- **#1221.** Real non-aliased R/E/M positives and wrong-accessor negatives for main, native, serve, debugger (entry/module), sinks, generator, linter,
  reflection, MCP prune, and the actual REPL: all pass. These are evidence, not closure: #1221/#1220 stay open for review.

## Results

| Selection | Result |
|---|---|
| P2-B suite + P2-C + P2-D supplemental | P2-C 75/75, **P2-D 87/87 assigned cases green**, P2-E 13 red + 4 green; supplemental `test_f2_p2_c_topology.py` 8, `test_f2_p2_d_consumers.py` 9 |
| Final non-loopback (`-n auto -m "not loopback"`, final tree) | **13 failed**, 6885 passed, 60 skipped, 429.6 s; every failure is a P2-E case (`test_B4_*`), none other |
| Loopback | 31 passed |
| Shared specs (`python -m tools.spec_runner`) | **822/822** (the three R20 reflection specs and the parity count recovered) |
| Earlier full run on `7b61b42e` (preserved) | 14 failed = 13 P2-E + `[module-main]`, a deterministic regression from my `_resolve_program_result` re-resolving the entry scope (masked a wrong accessor); fixed by the non-re-resolving `binding_owner`, then re-run clean |
| ruff, maintained-code documentation (0 errors, baseline 2827→2822), generated function reference, prelude doc lint, MCP profile `--check`, `tests/doc` (395 passed, 35 skipped) | pass |

Not run: Node/VS Code, official-SDK job, C++ parity.

## Test changes (before/after)

Existing assertions changed because the approved behavior changed, each with an inline reason: debugger globals are unit-scoped
(`test_debug_stdio.py`, 4 cases; entry shows E, module shows M, prelude shows R; runtime/entry cross-visibility removed); REPL `:env` lists entry
bindings only (`test_repl_env_characterization.py` 2, P2-A 1); module string reflection resolves the module's own name (P2-A 3); host-direct module lookup of an
entry-only fixture raises NameError (P2-A native); raw runtime reflective alias binds at identifier evaluation while an already-bound value keeps its scope
(`test_f2_p1_reflection_scope.py`, 3, now with a positive grant control). Edits to Codex's red tests (reviewed): serve wrong-accessor accepts `NameError` (message
asserted) or `AssertionError` because discovery documents that lookup failures propagate; REPL instrument ignores module-load `run_source` calls; B6_A replaces
`eval(quote(map((x) -> x + 1, [41])), empty_env())`, which the metacircular evaluator cannot parse on P1 either, with `inc(41)`.

## MCP security (no redesign)

`mcp_worker.execute_source` still prunes R via `prepare=` before E is registered; no host or envelope file changed. Denied names stay denied, write-through cannot recreate
them (P2-C tests), help catalogue respects pruning from E (B11_A pruned), reflection from E/M resolves only inside its scope chain. The 10 protected-value
conformance cases and the compat/lifecycle suites pass in the final run.

## Reviews

- Maintainability: **PASS WITH NON-BLOCKING FINDINGS** (`.genia/process/tmp/handoffs/f2-p2-d/maintainability-review.md`); fixes 1, 3, 4, t1 applied.
- Independent truth audit (read-only): **PASS WITH FINDINGS**, no blocking. Findings: reflective call inside metacircular `eval` resolves through `GeniaMetaEnv.lookup` to the raw R-bound
  callable (conservative, cannot leak E; tracked in #1238); debugger redaction rests on `repr` of protected values (covered by `test_B10_A_protected_entry_values_are_redacted_in_globals_and_diagnostics`).

## Remaining

P2-E: 13 `test_B4_*` cases (fallback, strict switch, event set, warning dedupe, exclusions, strict CI). #1238: N1 attempt-record semantics, N2 cost/duplication, plus the
metacircular reflection corner and the frozenset-membership alternative. #1220/#1221/#1230 await their review gates; documentation is partial by design.

## #1226 dogfooding

Supporting computation this task: the table-to-slice classifier (Python, same as P2-C) and two Python timing scripts (`timeit`, `perf_counter`). Classification **D** for the classifier
(already observed in P2-C; not re-counted) and **D** for the timing scripts: STATE documents no wall-clock primitive (`sleep` only), so a Genia benchmark of the Python host is not possible —
a deliberate scope boundary, not a gap request. No Genia sketch was run; **no new candidate**. Review/experiment cost not measured.
