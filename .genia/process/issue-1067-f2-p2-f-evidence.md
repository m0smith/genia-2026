# F2/P2-F evidence — integration, conformance and completion evidence (issue #1067, tracker #1229, retirement #1230)

Stacked on P2-E (PR #1241). **Baseline verified, not trusted:** the #1241 head on GitHub was `858fc6ad` although P2-E reported `7d696abf`. Cause: the P2-E follow-up commits
(`3a07a869`, `7d696abf`) were made on a detached HEAD, so `git push origin issue-1067-f2-p2-e-fallback` sent only the stale branch ref. I fast-forwarded the remote branch to
`7d696abf` (no overwrite, no discarded commit); #1241 now lists 3 commits and head `7d696abf`. Verified stack heads: P2-B `24cbe008` → P2-C `cb593207` → P2-D `b674674d` → P2-E `7d696abf`
(each an ancestor of the next). `origin/main` has since moved (`1261ae27`; stack merge base `b8168fd4`); nothing in this stack is merged. P2-F branch `issue-1067-f2-p2-f-integration`, head `cca8b7ed`.
Second record-keeping repair: `.genia/process/tmp/` is gitignored, so the P2-C/D/E maintainability records cited under `tmp/handoffs/` were never pushed; they are now committed as
`.genia/process/issue-1067-f2-p2-{c,d,e,f}-maintainability-review.md` and the evidence files point there.
Production code is unchanged in P2-F (`git diff --stat 7d696abf..HEAD -- src hosts tools apps` is empty).

## 1. Whole-stack verification (real host entry paths)

| Property | Evidence (all pass) |
|---|---|
| R, E, M physically distinct and registered | `test_combined_registered_execution_composes_every_approved_boundary`; P2-B `test_B1_A_*` |
| Runtime-owned declarations incl. unregistered helper `map_acc`; write-through; collisions | P2-B B2 cases (22); `test_B2_A_*` |
| 13 program sites and 31-site inventory | `test_B8_B_*` (13 host paths executed + construction guards + 31-site classification) |
| Reflection evaluation-bound; frame-first | shared specs `f2-module-reflection-*`, `f2-reflection-frame-parameter-*`; P2-B B5 (28) |
| `empty_env()` cannot see E implicitly | `test_B6_*`, `test_empty_env_base_hides_entry_names_from_entry_and_module_alike` |
| Consumers use right accessors | P2-B B9/B10/B12; real CLI file/command subprocess tests in `test_f2_p2_f_integration.py` |
| MCP prune precedes entry registration | `test_B7_B_worker_prunes_runtime_before_entry_registration`; `test_mcp_worker_path_prunes_before_entry_and_keeps_denied_names_denied` |
| Fallback reachable only from module identifier evaluation | P2-E eligibility tests; `test_B4_A_fallback_exclusions_*` (7); suite-wide measurement below |
| Strict denies with ordinary `NameError` (real CLI too) | `test_cli_file_mode_strict_denies_with_the_ordinary_name_error` |
| Events/warnings deduplicated, value-free | P2-E pair/warning tests; CLI test asserts one warning, no value or path |
Real entry paths run here: CLI file mode and command mode (subprocess, default and strict), native-test runner (`run_native_tests_from_file`), REPL (P2-B/P2-D actual-REPL cases), debug-stdio (P2-B B8 + debugger cases),
serve discovery (B12), MCP worker (`execute_source`) and the full MCP stdio/official-client acceptance (below).

## 2. Portable conformance review

Authority: `GENIA_STATE.md` states `doc("name")` semantics and, after this phase, one **language-level** bullet that `doc`/`meta`/`help` resolve `name` in the scope where the reflective identifier is evaluated (frame parameters first,
then the unit's own names and the runtime's; module code cannot name entry-program bindings); the approved contract §7.1/§16.2 (decision D1/P2R-2) is the supporting authority. Three portable observations were added using only existing infrastructure
(`spec/eval`, capabilities `multi_file_eval` and `doc_help`; no new capability, runner or protocol):
- `f2-module-reflection-resolves-in-module-scope` (module-own helper resolves; entry cannot see it) — `multi_file_eval`, `doc_help`
- `f2-module-reflection-cannot-name-entry-binding` (entry binding invisible to module reflection) — `multi_file_eval`, `doc_help`
- `f2-reflection-frame-parameter-precedes-runtime-name` (parameter named `map`) — `doc_help`
Result: Python 825/825 default and strict. Sensitivity: all three **fail on the pre-F2 `main` base (`b8168fd4`)** and pass on the stack. **Not portable and kept Python-only:** the temporary fallback, the strict switch, event sets, warnings, scope accessors,
sink/debug-state ownership, MCP pruning order (all Python-host mechanics; Python tests only).
**Python/C++ boundary statement:** the C++ host (`m0smith/genia-cpp`) was not run or inspected in this session. By recorded evidence it does not claim `doc_help` at its R24 floor (`docs/design/r24/capability-floor.json`) and declares
`multi_file_eval` unsupported (`spec/known_host_gaps.json`), so these cases are expected to report UNSUPPORTED there — never a pass. No C++ module, reflection-scope or fallback support is claimed, and no new known-host-gap entry was needed
(existing `multi_file_eval` gap covers the two module cases; the single-file case relies on the R24 floor record — to be confirmed by the next host-parity run).

## 3. #1230 executed strict-mode coverage inventory

Suite-wide measurement (throwaway plugin wrapping the fallback function, default mode, full non-loopback + loopback run on `7d696abf`, 6913 passed): **32 fallback reads in 12 tests, 13 distinct (module, name) pairs, every one in a
deliberate fallback test** (P2-B `test_B4_*`: 21 reads in 5 tests; P2-E `test_f2_p2_e_fallback.py`: 11 reads in 7 tests). Zero reads from any other test. The strict suite (below) is green. Execution table:

| Group | Files | Executed how | Registered E? | Strict | Event possible / observed |
|---|---|---|---|---|---|
| Packaged modules | `web`, `resource`, `execution` (`src/genia/std/prelude`) | imported from a registered entry: `test_repository_module_loads_from_a_registered_entry_without_fallback_events` (default and strict); also web/resource used by CLI, native, HTTP, resource suites | yes | yes and no | possible (module code) / **none observed**; top-level evaluation only, function bodies by their own suites |
| Example modules | `examples/ants`, `tic-tac-toe`, `r12_grounded_context_answer`, `ants_terminal`, `ants_actor` | same import test; plus existing example suites (tic-tac-toe native tests, R12 grounded proving) | yes | yes and no | possible / **none observed** (top level only for ants_terminal/ants_actor) |
| Prelude (24 files) | `src/genia/std/prelude/*.genia` | autoloaded into R by the whole suite | n/a (R code) | yes and no | **impossible by construction** (fallback requires a module unit) |
| MCP server program | `apps/mcp/mcp.genia` | MCP host/worker/stdio/official-client suites over a real registered E (launcher subprocess), 42-case acceptance run | yes | default and strict full suites | an entry program, not a module: not eligible; no warnings in suites that assert empty stderr |
| Example entry programs | remaining `examples/*.genia` | existing proving-case/cross-mode/native/serve suites where they exist; others are inspection-only here | partly | strict suite | entry programs are not eligible; **not individually executed unless a test above names them** |
| Fixtures | `tests/native/*.genia`, `tests/cases/**`, `spec/**` sources, tmp-written modules | native runner, spec runner (825 cases), unit suites | native: yes; spec runner: host adapter | yes and no | module fixtures exercised; only the deliberate tests read entry names |
**Limits (not claimed):** single-root harness tests cannot produce events; inspection-only files are listed as such; function bodies of repository modules are covered only where an existing test calls them; third-party reliance is unknown; the removal PR must
rerun this measurement on the merged tree. The first-on-`main` date is **not recorded** (stack unmerged).

## 4. #1220 acceptance review (recommend closure after maintainer review of the stack; not closed here)

| Criterion | Evidence | Status |
|---|---|---|
| Catalogue reads only runtime scope via `runtime_scope()` | `builtins.py` `_public_autoload_paths`/`_discover_public_family_names`; `test_B11_B_autoload_reads_use_runtime_or_reviewed_runtime_constructor` | proven |
| AST guard fails on implicit root reads; was red on P1 | `test_B11_B_catalogue_source_guard_rejects_implicit_root` (P2-B red evidence: failed at `builtins.py:3340/3378`; green since P2-D); mutation: catalogue read from E detected (3 failures) | proven |
| Real non-aliased R/E/M, empty-E control, identical `help()`, pruned R | `test_B11_A_help_overview_identical_from_R_E_M_and_pruned_R[False,True]`, `test_B11_A_wrong_catalogue_owner_empty_control_is_discriminating` | proven |
| Existing reflection/help/autoload/module/MCP suites pass | full default and strict runs (below) | proven |
| Independent verification, no leak beyond §16.2 | P2-D and P2-F independent truth audits | proven pending the final P2-F audit verdict |

## 5. #1221 acceptance review (recommend closure after maintainer review; not closed here)

| Criterion | Evidence | Status |
|---|---|---|
| Real separated scopes, not stubs | `separated_scopes` fixture self-checks (non-aliasing, disjoint bindings, empty E autoloads); host paths via `make_program_env`/CLI | proven |
| Each wrong-scope accessor detected | `test_B12_A_real_consumers_discriminate_wrong_accessors` (12 boundaries × 3 owners, equal-owner control) and the actual-REPL wrong-owner cases (3) — **plus eight author-run production mutations** each caught: sink→E (4 failures), catalogue→E (3), debugger→R (8), REPL→R (4), main dispatch→R (3), native discovery→R (10), reflection unbound (6), debug state on E (2) | proven; caveat: the serve wrong-owner variant accepts `NameError` (documented lookup-failure propagation) |
| Entry, runtime, module, REPL/debugger, restricted MCP visibility verified | B8–B12, `test_B7_*`, MCP security suites | proven |
| Existing P1 tests and applicable full regressions | below | proven |
| Evidence linked from #1067 | this record and the PR comments | pending posting |

## 6. #1238 disposition

| Item | Class | Disposition |
|---|---|---|
| N1 attempt-record semantics (`entry_declared_runtime_owned` records at attempt) | non-blocking P2-G documentation task | consumers (`:env`, discovery) filter on `name in runtime.values`, so a failed bind cannot surface a phantom binding; document the attempt semantics in P2-G; no correction needed |
| N2 duplicated ownership checks / per-operation autoload scan / cold manifest parse | deferred follow-up (owner: P3 or performance task) | no measured regression (fib(20) neutral); micro-optimisation not worth risk now |
| Reflection inside metacircular `eval` (`GeniaMetaEnv.lookup`) | deferred, **pinned** | reachable but conservative: resolves runtime names only, never entry names (no leak) and not `define`d names; the approved contract does not specify `eval` reflection; `test_reflection_inside_metacircular_eval_is_runtime_scoped_and_cannot_see_entry` pins it so a change is deliberate |
| Marker-check hot path (`type(value) is FunctionType` + `getattr`) | deferred | measured neutral; frozenset-membership alternative stays optional |
No semantic or security contract violation was found, so no failing test or fix was required in P2-F.

## 7. Regression evidence (commands: `uv run pytest -n auto -q -p no:cacheprovider --tb=line -m "not loopback"`, `... -m loopback`, `uv run python -m tools.spec_runner`; strict adds `GENIA_STRICT_MODULE_SCOPE=1`)

| Run | Result |
|---|---|
| Default, tree before the fixture fix | 6936 passed, 60 skipped, 0 failed; loopback 31; specs 825/825 |
| **Strict, same tree (initial failure preserved)** | **1 failed**, 6935 passed: `test_combined_registered_execution_composes_every_approved_boundary` relied on the fallback without clearing the switch (my new test); loopback 31; specs 825/825 |
| Fix | autouse default-mode fixture in `test_f2_p2_f_integration.py` (same pattern as the other fallback-exercising modules) |
| **Final default** (`b31ie5…` tree + docs) | **6936 passed, 60 skipped, 0 failed**, 416.6 s; loopback **31 passed**; specs **825/825** |
| **Final strict** | **6936 passed, 60 skipped, 0 failed**, 401.5 s; loopback **31 passed**; specs **825/825** |
| P2-B…P2-E counts re-derived | all 179 P2-B cases pass; P2-C 75, P2-D 87, P2-E 17 as assigned |
| VS Code extension (`npm ci` + `npm test` in a copy) | 4 passed (language indexer unit tests only; the debugger itself is covered by the Python debug-stdio suites) |
| Official MCP SDK client acceptance (`npm ci` in `tools/mcp_acceptance`, Node 22; stdio config/launch/lifecycle/official-client files, `-n0`) | **42 passed**, 81.8 s |
| ruff, maintained-code documentation (0 errors), generated function reference, prelude doc lint, MCP profile check, `tests/doc` | pass |
Not run: C++ host, VS Code launch/extension host tests beyond the unit tests, cross-host parity gate.

## 8. Reviews and remaining obligations

- Maintainability: recorded N/A for production code (no production change), with mutation evidence (`issue-1067-f2-p2-f-maintainability-review.md`).
- Independent truth audit: see PR.
- #1226: no meaningful new supporting computation beyond a throwaway pytest probe plugin (Python, pytest-specific, **D**), mutation worktree scripts (shell/Python, **D**), and routine greps; no Genia sketch, no candidate.
- **P2-G handoff:** final documentation synchronization of STATE/RULES/REPL README/README/architecture/contract status text; decide #1220/#1221 closure after maintainers review the merged stack; document N1 attempt semantics; refresh the #1230 measurement on the merged tree; update host-gap/capability docs only if the next host-parity run changes the C++ statement; final F2 completion audit.
