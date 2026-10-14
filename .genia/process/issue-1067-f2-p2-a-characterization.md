# F2/P2-A current-behavior characterization — #1067

Scope: Python-host tests and evidence only. P2-B/P2-C, physical scope separation,
contract rulings, shared specs and production code are outside this change.
Characterization is evidence of compatibility, not portable semantic authority.
STATE remains final authority. MCP language-knowledge impact: none; no behavior,
public surface or language-profile fact changes. C++ is unaffected.

## Baseline and isolation

Fetched `origin/main`; PR #1223 is merged at
`95c5bfbea97219ced9068196ef113cf532cdf281` (2026-10-14).
Branch: `issue-1067-f2-p2-a-characterization`; worktree: `/tmp/genia-p2-a`.
The tested production tree is exactly that baseline. Only the new Python test
module and this record change. #1067, #1220 and #1221 remain open.
Claude's P2-0 worktree/branch and the F2 contract were not edited.

Inputs: repository AGENTS instructions; STATE §4/§7/§9/§9.49; RULES §8.2–8.3;
REPL commands; README module surface; F2 P0 contract; P2 pre-flight;
P1-H integration/audit carry-forward; process/run-change and maintained-code
documentation policies; issues #1067/#1220/#1221 and PR #1223.
The F2 contract still labels itself PROPOSED and explicitly grants no implemented
behavior; its accepted decisions and unresolved P2-0 choices must not be inferred
to be runtime facts.

## Current graph

`R = make_global_env(...)`: parentless runtime **and entry** environment.
Entry and prelude definitions close over R. `runtime_scope`, `entry_scope` and
`inspection_globals_scope` all return R. `unit_scope` returns R for entry/prelude.
Each loaded module M is a real `Env(R, rebind_parent=False)`, owns its bindings,
metadata and contribution table, and sets `unit_scope` to M. Module frames and
blocks inherit that unit. Inspection globals still return R even from M.
Module cache, autoload catalogue/file sets and internal values belong to R.

Ordinary lexical children are distinct existing Envs, not registered P2 entries.
Parameters bind locally; returned callbacks retain their defining frame after
return and ignore later rebinding of a shadowed root name. Assignment walks to
the nearest assignable binding until a `rebind_parent=False` boundary; definitions
consult the defining Env's own values. Lookup order is lexical values, guarded
root internals, root autoload, then `Undefined name: <name>`.
Existing P1-B tests cover nested blocks/lambdas, module aliases, sibling imports,
owner identities and live metadata/cache identity.

## Collision and reflection observations

All named tests below are in `tests/unit/test_f2_p2_a_characterization.py`.

| Current observation | Executable evidence |
|---|---|
| Entry first/1 and map/2 succeed before list autoload; a later length call fails with the exact duplicate name/arity | `test_entry_definition_before_list_autoload_succeeds_then_poison_load` |
| After loading list prelude, duplicate first/1, map/2 or map_acc/3 fails, retaining group and existing arm identity | `test_entry_duplicate_shape_after_autoload_fails_without_replacing_group` |
| map_acc is neither initially bound nor autoload-registered; list-file loading installs it into R | same collision tests; `test_unregistered_helper_missing_before_autoload_then_directly_visible_but_not_catalogued` |
| rows/0 joins host rows/1 in the same group; host arm and binding metadata survive; both arities evaluate | `test_rows_zero_arity_joins_existing_host_group_and_preserves_one_arity` |
| first/2 joins an already-loaded first/1, retaining its original arm | `test_new_arity_merges_with_loaded_prelude_without_changing_existing_arm` |
| log = 5 replaces the callable in R; invocation reports the current callable misuse diagnostic | `test_assignment_replaces_runtime_visible_callable_in_shared_root` |
| Plain child first/map/rows definitions shadow the parent group; child rows/0 hides rows/1 and yields exact arity miss | `test_plain_child_definitions_shadow_parent_group_instead_of_write_through` |
| Entry doc/meta/help find shared-root names and preserve identity | `test_shared_root_entry_reflection_preserves_metadata_and_callable_identity` |
| Module own probe has direct value/metadata lookup, but doc/meta/help string lookup still uses captured R; help(probe) sees the function's documentation | `test_module_direct_binding_and_metadata_exist_but_string_reflection_uses_root` |
| map reflection triggers root autoload; map_acc is subsequently visible but undocumented, with empty metadata, and absent from help() catalogue | `test_unregistered_helper_missing_before_autoload_then_directly_visible_but_not_catalogued` |

Failure after a partly completed autoload is not transactional: tests assert that
the original colliding group survives and the loading guard clears, but do not
claim rollback of earlier definitions. P1-F real-Env tests additionally establish
that reflection aliases/transferred callables retain root binding and explicit
private lookup helpers do not change public callable identity.

## Module compatibility and metacircular eval

`test_module_free_name_reads_live_shared_entry_root_without_warning` covers entry
definition before and after import: a module function reads the root's latest
value with no compatibility warning. `test_top_level_module_read_depends_on_entry_definition_before_import`
records the stricter top-level case: import fails when the name is absent, clears
the loading guard, then succeeds after definition. Its captured assignment stays
at the import-time value after later entry rebinding.
`test_module_local_names_and_writes_are_distinct_from_root_and_sibling` proves
identical names in two modules remain separately owned and cannot rebind R.
`test_contribution_closure_keeps_module_owner_but_reads_entry_helper_through_root`
reproduces the R20 free-helper dependency through a real imported contribution.

`test_metacircular_empty_environment_reads_live_entry_root_but_owns_writes`
proves that empty_env is a non-rebinding child of captured R, so eval currently
reads live entry names through R while assignments remain in the metacircular
environment. Restricting those reads during P2 would be an observable change.

## Consumer coverage and limits

| Consumer | Real current-behavior evidence | What it does not prove |
|---|---|---|
| CLI file/command | New subprocess test runs the installed console entry's `_main`, invokes main(args), and checks exact stdout/empty stderr | Output alone does not prove root identity; that comes from P1-B and construction inspection |
| Native tests | Real make_test_env, injected fixture, legacy registration, entry @test and imported @test; modules still read entry-only fixture | No separated E ownership or forbidden module visibility |
| Serve | Real parsed/lowered entry IR, evaluated descriptors, imported module metadata, and config/route discovery | No listener launch in the new test; existing P1-C orchestration uses a stub to record supplied Env, existing server regression covers activation |
| REPL | Actual repl construction, evaluation and :env rendering; only terminal input scripted; entry/runtime/autoload listed, protected payload redacted | Unit-only future view |
| Debugger | Real hooks retain module/prelude frames; actual initial-frame and globals/locals rendering | New test is inspection, not a complete stepping protocol test; existing debug-stdio suite supplies protocol coverage |
| Module inspection | Actual module globals view is R; module marker absent, entry marker visible | Proposed D3 module-only globals |
| Documentation generator/linter | Actual collect and runtime-public name helpers inspect real catalogue, map documented, map_acc absent | Wrong-accessor discrimination where R=E |
| MCP | Real pruned R through root and plain child inputs, denied bindings/autoload, guarded actual internal binding, trusted autoload, help catalogue and AST policy | Child is not a worker E; no new E construction; existing worker/security suites cover actual execute_source/subprocess boundaries |
| Error/test sinks | Actual _emit_error/_write_stderr/_write_stdout use root local sink, but ignore inherited child sink and fall back to sys streams | Does not prescribe future sink routing |

P1-C/D/G stubs are retained: they prove that consumers call the accessor, not that
P2 topology works. None of this record treats shared R=E tests as separation proof.

## Environment-construction inventory

Reproduced with `rg -n 'make_global_env\(|\bEnv\(' src hosts tools`, checked with
Python AST calls and enclosing-function identification. At baseline: **13 program
construction call sites**, **3 tooling construction calls**, **15 direct Env
allocation sites** (31 calls total; definitions/docstrings excluded). No additional
program construction site beyond the pre-flight's 13 was found.

R/E/I in the accessor column mean runtime/entry/inspection accessor used by the
associated path, not necessarily on the allocation line. `none` means creation
or evaluation remains direct. Every listed fresh make_global_env result shares
entry with root today; descendants share runtime root but are separate objects.

| Site at baseline | Creation and intended owner | Accessors in path | P2 impact | Existing/new evidence |
|---|---|---|---|---|
| interpreter.py:354 repl | fresh R=E, persistent REPL | I | create/register E; inspection view | repl_env_characterization; new real REPL |
| interpreter.py:419 run_debug_stdio | fresh R=E with hooks/output | E/I in debugger | E and runtime debug ownership | debug_stdio; new real frames |
| interpreter.py:540 _run_serve_file | fresh R=E | E | entry construction | entry_consumers_p1_c; server binding suites; new descriptors |
| interpreter.py:631 _run_execution_mode pipe | fresh R=E | none | entry construction | cli_args; shared pipe cases |
| interpreter.py:644 _run_execution_mode command | fresh R=E | E for main | entry construction | cli_args; new command subprocess |
| interpreter.py:659 _run_execution_mode file | fresh R=E | E for main | entry construction | cli_args; new file subprocess |
| test_cli.py:86 make_test_env | fresh R=E; entry-only fixtures/registrar | E list/discovery | E construction and list reader | interpreter_test_mode; host_binding_classification; new discovery |
| exec_model_fixture.py:33 _build_env | fresh R=E; classified entry fixtures | none | E construction/injection placement | host_binding_classification; model fixture specs |
| exec_r12_grounded_fixture.py:38 _build_env | fresh R=E; classified entry fixtures | none | E construction/injection placement | host_binding_classification; grounded specs |
| exec_r25_concurrency_fixture.py:15 _build_env | fresh R=E; entry fixture | none | E construction/injection placement | host_binding_classification; concurrency specs |
| exec_ollama_chat.py:20 main | fresh R=E and explicit CLI args | none | E construction | adapter classification guard; no live-provider run in P2-A |
| mcp_host.py:58 main | fresh R=E for trusted MCP server source | none | E construction/launcher injection | r28_mcp_entrypoint/stdio launch suites |
| mcp_worker.py:225 execute_source | fresh R=E, empty stdin, bounded sinks; prune then run | R via prune | prune R before E; no reinjection | r28_mcp_run_worker/conformance_security; new prune/catalogue |
| gen_function_docs.py:110 collect | fresh runtime catalogue | R | retain runtime-only | scope_consumers_p1_g; new real tooling |
| lint_doc.py:536 _runtime_public_names | fresh runtime catalogue | R | retain runtime-only | same |
| lint_doc.py:556 _runtime_public_prelude_names | fresh runtime catalogue | R | retain runtime-only | same |
| builtins.py:317 make_global_env | Env(), parentless R=E | R for internal classification | factory default compatibility | scope_accessors_p1_b; host_binding_classification |
| builtins.py:395 _make_meta_env | Env(captured R, rebind_parent=False) | none | D4: E visibility must be decided | metacircular_eval; new live-root/read-local-write |
| builtins.py:615 meta_match_pattern_env_fn | Env(meta_env.env), lexical match result | none | inherited graph | metacircular_eval/pattern tests |
| environment.py:366 load_module | Env(R, rebind_parent=False), M owns unit | R/unit setup | parent remains R, fallback later | scope_accessors; modules_phase1; new module/contribution |
| callable.py:408 eval_with_tco | Env(function closure), local call frame | none | closure's owner | scope_accessors; new captured callback/frame |
| callable.py:756 _first_unit_match | Env(contribution closure), candidate frame | none | declaring M parent chain | r20_open_functions_cross_module; new contribution |
| callable.py:774 _invoke_open_clause | Env(clause closure), invocation frame | none | declaring closure parent chain | same |
| evaluator.py:573,585 GeniaMetaEnv.extend | Env(meta env), pattern/parameter child (2 sites) | none | inherited graph | metacircular_eval |
| evaluator.py:853,862 eval_list_traversal_loop | Env(current), selected match frame (2 sites) | none | inherited graph | optimized-list regression; scope_accessors prelude evidence |
| evaluator.py:882 eval_case_expr | Env(current), selected case frame | none | inherited graph | case/pattern regression |
| evaluator.py:900 eval_tail | Env(current), tail block | none | inherited unit/lookup | scope_accessors; tail-call regression |
| evaluator.py:1389 _eval_impl | Env(current), ordinary block | none | inherited unit/lookup | scope_accessors real nested blocks |
| evaluator.py:1404 lambda fn | Env(captured closure), parameter frame | none | inherited unit/lookup | scope_accessors; new returned callback |

Transitive subprocess adapters exec_eval/exec_ir/exec_cli/exec_flow do not directly
allocate an Env. `make_global_env` does not allocate E; P1 classes remain placement
bookkeeping. The inventory is a baseline record, not a brittle source-lock test.

## Security baseline

Real pruning removes unknown/denied ordinary bindings and non-allowed autoload
keys from R and removes denied binding metadata/trusted-autoload keys. It leaves
plain-child own values alone. Internal values are a separate guarded table:
ordinary child lookup cannot see actual `_evolve`, a trusted child can, and an
allowed trusted prelude executes after pruning. No privilege is minted or granted
by entry-only classification. Root help reads the pruned runtime autoload table.
Help's static scaffold still describes a generic host bridge; a missing-name note
is not access to the denied binding. No assertion treats catalogue prose as a
capability grant. Module globals and REPL list protected entry bindings today,
but their payload sentinels stay absent from rendered output and misuse diagnostics.
This is regression evidence, not a sandbox claim.

## P2-0 handoff and future red targets

| Decision | Evidence / required ruling | P2-B target after ruling |
|---|---|---|
| D1 collisions/write-through | first/map/map_acc before/after load, rows group merge, assignment replacement; plain child shadows rather than reproducing root | Explicit R/E collisions, hidden unregistered prelude helpers, arity misses, metadata ownership; do not simply run entry in Env(R) |
| D2 reflection | String doc/meta/help captures R even when called in real M; function-valued help differs | Entry/module/prelude, alias/HOF/transfer reflection and callable identity with E distinct |
| D3 fallback | Real module free reads see live R without warning; top-level import timing and contribution helper read reproduce leak | Module fallback/warning deduplication/strict mode and non-writing fallback, after approved mechanism/deadline |
| D4 metacircular eval | empty_env sees live root entry bindings; local assignments do not write R | Explicit preservation or approved changed visibility when E is distinct |
| D5 #1220 | Existing root and runtime accessors coincide; pruned-root catalogue is observable | Ownership guard plus E-vs-R catalogue misuse test; a behavioral root-vs-runtime discrimination is infeasible under approved graph |
| D6 registration/testing | Plain child main ignored; shared-root native discovery and fixtures work; local sink access falls back for a child | Real construction helper across 13 sites; entry registration/legacy list; sinks/debug state; wrong-accessor tests per boundary |

Contract discrepancies are recorded, not resolved: §2.1's historical prelude
local-assignment defect was independently repaired by #1205/#1206 and is already
identified in #1067/P1 history; P2 still owes structural write isolation.
The P2 pre-flight's proposed write-through rule does not account for unregistered
helpers without an explicit manifest or accepted compatibility change.
#1220 and #1221 cannot be closed by this characterization: real registered E does
not exist. No new failing P2 tests or topology implementation were started.
Any later implementation prompt must require same-change authoritative STATE,
relevant book/cheatsheet and other affected documentation updates when behavior
lands, including the MCP language-knowledge impact assessment.

## Independent test-quality review

Separate read-only reviewer checked the request, new tests and complementary
P1/REPL/security suites. No blocking quality findings. Recommendations repaired:
exact duplicate-definition arities; precise CLI identity claim; explicit serve
discovery-versus-orchestration limitation. Follow-up review verified the inventory
and found a weak contribution ownership assertion; repaired by checking the real
clause closure's distinct module identity, parent and unit accessor. Final focused
suite rerun passed after that repair. Reviewer could not execute uv because
its default cache was restricted; parent run supplies executable results.
Only terminal input is stubbed in the new REPL test; no accessor or lookup is
mocked. P1 stubs remain useful but limited. Evidence is against current behavior,
not a specification that these compatibility accidents must persist forever.

## Verification

Results below are recorded after command completion; Python 3.12.9 locally,
CI uses Python 3.14. Node/VS Code, mandatory official-SDK acceptance and C++ parity
are not claimed as locally validated. Full Python selection uses both partitions;
pre-existing skips remain skips, not coverage credit.

All commands run in `/tmp/genia-p2-a` with the locked uv development environment.

| Command | Result |
|---|---|
| `uv run pytest -q tests/unit/test_f2_p2_a_characterization.py` | 42 passed after final ownership assertion repair |
| `uv run pytest -q tests/unit/test_f2_p2_a_characterization.py tests/unit/test_scope_accessors_p1_b.py tests/unit/test_f2_p1_reflection_scope.py tests/unit/test_entry_consumers_p1_c.py tests/unit/test_inspection_consumers_p1_d.py tests/unit/test_scope_consumers_p1_g.py tests/unit/test_repl_env_characterization.py` | 85 passed |
| `uv run pytest -q tests/unit/test_f2_p2_a_characterization.py tests/unit/test_host_binding_classification_p1_e.py` | 60 passed after classifying root host injections |
| `uv run pytest -q tests/doc/test_semantic_doc_sync.py tests/doc/test_state_anchors_and_registry_sync.py tests/doc/test_composability_matrix_sync.py tests/unit/test_code_documentation.py tests/unit/test_doc_style_sync.py` | 307 passed, 34 existing skips |
| `uv run pytest -n auto -q -m loopback` | 31 passed |
| `uv run python -m tools.spec_runner` | total 822, passed 822, failed 0, invalid 0 |
| `uv run pytest -q tests/unit/test_prelude_local_binding_isolation.py` | 12 passed; existing native prelude isolation fixture remains green |
| `uv run ruff check .` | passed |
| `uv run python -m tools.code_documentation --base-ref origin/main` | 9362 records, 2840 legacy gaps, 1 classified exclusion, 0 errors |
| `uv run python tools/gen_function_docs.py --check` | function reference up to date |
| `uv run python tools/lint_doc.py --scan-dir src/genia/std/prelude --require-coverage` | 24 files, 286 @doc strings, 0 errors/warnings |
| `uv run python tools/gen_mcp_language_profile.py --check` | passed |
| `git diff --check` | passed |

The broader focused run used:

```sh
uv run pytest -q tests/unit/test_f2_p2_a_characterization.py tests/unit/test_scope_accessors_p1_b.py tests/unit/test_host_binding_classification_p1_e.py tests/unit/test_f2_p1_reflection_scope.py tests/unit/test_entry_consumers_p1_c.py tests/unit/test_inspection_consumers_p1_d.py tests/unit/test_scope_consumers_p1_g.py tests/unit/test_repl_env_characterization.py tests/unit/test_modules_phase1.py tests/unit/test_autoload.py tests/unit/test_function_docstrings.py tests/unit/test_metacircular_eval.py tests/unit/test_debug_stdio.py tests/unit/test_cli_args.py tests/unit/test_interpreter_test_mode.py tests/unit/test_r28_mcp_run_worker.py tests/unit/test_r28_mcp_conformance_security.py tests/unit/test_protected_configuration.py
```

It collected the 40-case intermediate new suite: 520 passed / 1 failed, the
P1-E harness classification guard rejecting two unclassified root injections in
the new tests. Repaired by using `set_host(runtime-public)` and
`register_host_autoload(runtime-public)`; the final 42 cases plus that guard's
entire module passed (60). No guard, visibility rule or runtime implementation
was weakened. The additional 2 module/contribution tests and final assertion
repairs were checked in the final standalone and focused commands above.

Full regression command: `uv run pytest -n auto -q -m 'not loopback'`.
Result: **6679 passed, 71 skipped, 4 failed** in 1245.85 seconds. It collected the
35-case intermediate new suite before the final 7 cases were added; final 42-case
and focused reruns above cover the completed new file. The 71 existing skips are
not coverage credit; no skip was added or changed by P2-A. This was a completed
full selection, not a clean all-green full run of the final tree.

Failures:

1. `test_host_binding_classification_p1_e.py::test_harness_injection_sites_have_explicit_classes`:
   the two new unclassified root injections, repaired as recorded above.
2. `test_r28_mcp_conformance_lifecycle.py::test_overflow_kills_the_worker_and_removes_its_private_directory`:
   received `timeout` instead of `result_limit` under parallel load.
3. `test_r28_mcp_conformance_run.py::test_runaway_output_is_stopped_at_the_limit_not_accumulated_until_the_deadline`:
   output-limit closed-failure envelope assertion failed during the same run.
4. `test_spec_runner_host_mode_cli.py::test_host_mode_reports_every_taxonomy_outcome_and_exits_nonzero`:
   0.5-second fixture deadline produced `passed=0 failed=0 unsupported=1
   protocol_error=0 crash=1 timeout=4` instead of one of each taxonomy outcome.

Rechecked with the exact command:

```sh
uv run pytest -q tests/unit/test_host_binding_classification_p1_e.py::test_harness_injection_sites_have_explicit_classes tests/unit/test_r28_mcp_conformance_lifecycle.py::test_overflow_kills_the_worker_and_removes_its_private_directory tests/unit/test_r28_mcp_conformance_run.py::test_runaway_output_is_stopped_at_the_limit_not_accumulated_until_the_deadline tests/unit/test_spec_runner_host_mode_cli.py::test_host_mode_reports_every_taxonomy_outcome_and_exits_nonzero
```

**4 passed in 6.84 seconds.** Runtime, existing tests and deadlines were unchanged.
The three existing-test failures are consistent with parallel load sensitivity
(inference from the failure diagnostics and passing unloaded retry), not evidence
of a scope behavior change. They remain disclosed; retry does not erase the full
run's failures. Loopback's 31 passing cases and the completed non-loopback run
together cover the full selection. No Node/VS Code or mandatory official-SDK job
was separately run; no C++ validation is claimed.

Delivery is a test-phase commit and focused PR against main on the branch above;
the PR/head SHA and issue handoff link are reported in GitHub and the final
delivery report. No merge or issue closure is authorized by this record.
