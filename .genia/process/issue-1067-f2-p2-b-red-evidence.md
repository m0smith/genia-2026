# F2/P2-B expected-red evidence — #1067 / #1229

**EXPECTED RED — P2-B test-first gate.** Python-host test work only. No production, authoritative-document, workflow, spec, or host-capability change; P2-C has not begun.

## Authorization and baseline

- Maintainer approval: [D1–D6 with A1–A3](https://github.com/m0smith/genia-2026/issues/1067#issuecomment-6171848719). The approval supersedes the stale pending-status wording in the merged planning records; it does not claim implementation.
- Latest fetched baseline at start: `b8168fd4f056904b50a3bb5e2b999d2baeb1f5fb`.
- Verified merged prerequisites: #1227 (`7b02512b587f29609e3f86448dac0bf9215eed0f`), #1228 (`7b3b5243e7bef5b280fcca7703d8ec8660dd45c7`), #1231 (`b8168fd4f056904b50a3bb5e2b999d2baeb1f5fb`).
- Branch: `issue-1067-f2-p2-b-red-tests`; isolated worktree: `/tmp/genia-f2-p2-b`.
- Final red-test commit: `163f5160f6486cb56fc78211edd0afc261a13c18`. All implementation slices must cite this SHA; later evidence-only commits do not change the test target. Initial suite commit was `02439632e6af9554f53275b5e8d720b7097da7b8`; the final test-only follow-up permits the approved physical E allocation in the inventory and broadens catalogue guards across production Python. These repairs correct latent test guard expectations, not the P2 contract.
- Inputs: latest AGENTS; implemented STATE/RULES/REPL README/README surfaces; approved F2 contract §16/A1–A3; P2-0 decisions, P2-A characterization, approval gate and P2-B brief; process/run-change and code-documentation instructions; open #1220/#1221/#1229/#1230.
- MCP language-knowledge impact: **none in P2-B**, because no implemented behavior or profile fact changes. Python internals/host compatibility are the target; no C++ parity claim or new capability vocabulary is introduced.

## Final red matrix

All 179 new pytest cases fail on P1: A = explicit approved-API absence; B = observable behavior/source assertions. Zero collection errors, skips, xfails, accidental exception failures, or unexpected passes. The two native cases are included through their two pytest wrappers, not counted again.

| Test group | Contract reference | A / B failures | Actual failure | Expected P2 behavior | Green-making slice |
|---|---|---:|---|---|---|
| B1 | §16.6.1, §16.1.6 | 19 / 0 | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | Distinct registered R/E, exactly-once registration and host-class ownership | P2-C |
| B2 | §16.1.1–8, §16.8 A1 | 22 / 0 | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | Complete declaration-derived ownership; P1 collision/write-through diagnostics preserved; pruning never grants authority | P2-C |
| B3 | §16.1.3/7/8(b), §4.3–4.4 | 2 / 1 | Failed: DID NOT RAISE <class 'NameError'> | R closures cannot reach E; R-resident entry-declared runtime-owned names remain the P2 compatibility exception | P2-C |
| B4 | §16.3.2–6, §11, A2 | 8 / 9 | Failed: DID NOT RAISE <class 'NameError'> | Only module evaluator free reads fall back; strict switch captured once; pair-deduped warnings/events; no data leakage | P2-E |
| B5 | §16.2, §7.1, P1 design §6 | 10 / 15 | AssertionError: assert none('missing-doc', <map 1>) == 'module documentation' | Evaluation-bound reflection, frame-first binding metadata, explicit callable grants, stable identity and value-based rebinding | P2-D |
| B6 | §16.4 | 1 / 2 | Failed: DID NOT RAISE <class 'NameError'> | empty_env uses R only; explicit define admits E values; runtime-owned names remain available | P2-D |
| B7 | §16.6.2–3, §16.7 MCP note | 2 / 1 | assert (<genia.environment.Env object at 0x107238aa0> is not <genia.environment.Env object at 0x107238aa0>) | Prune R before empty E; denied builtin/prelude names never regain R authority | P2-C/P2-D |
| B8 | §16.6.2–4, §16.8 A3, §16.1.4 | 1 / 28 | AssertionError: repl: program still evaluated in shared R=E | All 13 program sites register E; all 31 baseline sites classified; direct native evaluator protected; serve sees entry declarations | P2-C/P2-D |
| B9 | §8, §16.6.3, §16.1.4 | 1 / 6 | assert (<genia.environment.Env object at 0x1071fab70> is not <genia.environment.Env object at 0x1071fab70>) | Fixtures/registrar/list reside in E; discovery/runner select E and include entry-declared runtime-owned tests | P2-C/P2-D |
| B10 | §8, §16.6.1/3/5, R10 | 2 / 5 | AssertionError: assert [] == ['message\n'] | Unit inspection, runtime sinks/debug hooks, local frames and protected redaction | P2-D |
| B11 | §16.5.1–3 (#1220) | 3 / 2 | AssertionError: §16.5 runtime accessor required: src/genia/builtins.py:3340:root, src/genia/builtins.py:3378:root | Source guard and real R/E/M catalogue ownership, identical/pruned help, empty-E catalogue mutation | P2-D |
| B12 | §16.6.5 (#1221) | 39 / 0 | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | Positive real consumers plus wrong-owner accessor mutations over distinct R/E/M; actual REPL sessions | P2-D |

A-class totals are initial failure classes, not claims that registration alone makes every case green. The same marker intentionally gates genuine separated integration cases completed by P2-D/E. Missing measurement after registration uses the explicit `P2-C API missing` convention with P2-E identified as responsible.

## Test design and boundaries

- `separated_scopes` constructs R through production, registers through `create_entry_scope`, rejects aliasing/overlapping setup bindings, and imports a real sibling M. It does not simulate P2 by relabeling `Env(R)`.
- Source parsing in the manifest drift test derives every top-level assignment/function/named pattern in every actual autoload target. It includes `pi` and `map_acc`, excludes packaged-only `web`/`resource`/`execution`, and proves routing without prescribing a new public manifest accessor. Registry-only implementations fail unregistered declarations. An entry-only `read_file` injection must still be rejected after pruning; `secret_get` is no longer runtime-owned and may be entry-only without recreating R authority.
- The 31-site guard classifies 13 program + 3 tooling + 15 direct allocations by AST owner, including qualified factories; it rejects unknown constructors and permits only one new helper owning R construction plus registration. The 18 non-program dispositions are explicitly enumerated in the guard. No line-number freeze or demand to allocate E for frames/tools.
- B12 parametrizes each consumer over R/E/M. The matching owner is a positive control; the other owners must fail the identical observation after accessor injection. The real REPL variant wraps actual evaluation before :env, avoiding an obsolete factory mock. Help has a separate empty-E catalogue mutation. Initial API absence prevents dynamically executing these positives/mutations today; static review is not implementation proof.
- Reflection keeps binding-owned doc/meta separate from callable-target help metadata. An unannotated parameter has missing doc/empty metadata, while callable-valued help can retain the target metadata. Native twins pin module-local lookup and parameter precedence.
- Five additional binding-form snippets (pattern, import alias, open, use with a real contribution, metadata) were executed against caller-created P1 roots as syntax/compatibility controls: 5 passed. These controls prove syntax only, not separation. A malformed initial use snippet was repaired before the red commit.
- Security: worker pruning precedes registration; denied runtime bindings/autoloads cannot be restored by name ownership. Protected globals and output diagnostics retain sentinel-free rendering. No real provider/network/credential is required by any new test.

## Compatibility and P3 retirement

P2-A remains unchanged (42/42 passed independently; also included in the 523-case green focused selection). Legacy caller-created roots keep R=E; plain children remain unregistered. Tests asserting those facts are not separation evidence and do not automatically flip in P2-D.

Approved differences from P2-A when exercised through registered host construction:
- Module free reads gain bounded fallback warnings; strict reads become ordinary NameError, including import-time and contribution reads. Shared-root characterization remains valid on caller-created roots.
- Module-own doc/meta/help improves; module reflection cannot name E; reflection starts at the evaluating frame. Existing P1 helper factoring tests retain historical root behavior until their separately documented consumer flip.
- empty_env loses implicit E-resident access; define supplies values explicitly. Runtime names remain visible.
- make_test_env, actual CLI/REPL construction, debugger module globals and inherited sink consumers change ownership. P2-A native fixture visibility/REPL runtime listing/module-root globals/inherited sink fallback observations are expected to change only on the newly migrated host paths.

Exact P2-A targets for the later documentation/consumer flip (all names are in `tests/unit/test_f2_p2_a_characterization.py`; no characterization is rewritten in P2-B):

| Target | P2-D/E disposition |
|---|---|
| `test_module_direct_binding_and_metadata_exist_but_string_reflection_uses_root[doc/meta/help]` | Module-source reflection resolves its own probe; replace the missing-doc/meta/string-help observation when implementation lands, even for caller-created roots. Host direct `scope.get(reflection)` remains R-bound. |
| `test_debugger_real_module_and_prelude_frames_show_root_globals_and_local_parameters` | Module-frame globals become M; prelude globals become R; entry globals become the recorded E view. Local parameter assertions remain. |
| `test_error_and_test_output_use_supplied_env_local_sink_then_system_fallback[_emit_error/_write_stderr/_write_stdout]` | Inherited child sinks are now read through R rather than ignored; supplied sink/process-fallback distinction changes. |
| `test_repl_real_shared_root_lists_entry_runtime_autoload_and_redacts_protection` | Real REPL construction registers E; remove runtime/autoload listing expectations and preserve protected redaction. |
| `test_native_discovery_real_root_includes_entry_tests_excludes_module_tests` | make_test_env returns E. Host direct module get cannot reach fixture_marker, while explicit eligible identifier fallback is separately tested. Discovery/registration identity and imported-test exclusion stay. |
| `test_cli_actual_entry_main_dispatch_uses_shared_root[command/file]` | Its exact result remains valid after E construction; output alone never established shared-root identity. Rename/reclassify its scope commentary in P2-D, do not weaken dispatch assertions. |
| `test_protected_entry_binding_is_visible_to_module_inspection_but_payload_is_redacted` | This caller-created root deliberately stays shared, so host module get can remain valid; module debugger globals are M and must lose the entry marker. Redaction remains mandatory. |
| `test_module_free_name_reads_live_shared_entry_root_without_warning`, contribution/import-time/shared-root eval/serve/collision/plain-child cases | These explicitly construct caller-owned R and remain legacy evidence. They do not test a registered E and do not automatically flip. The new host-constructed B tests pin the approved changes. |

A1 retirement obligations remain open for P3: measure entry-declared runtime-owned names per run by public registered / unregistered helper / builtin class; record every non-empty member disposition; count module/prelude reads of entry-written R bindings; record counts in #1230; rule D2/D2b before shadowing or removing write-through. The first/map_acc hijacks are pinned intentionally. No P3 semantics or measurement implementation is added here.

A2 is evidence-gated: R29 start is a hard gate and 60 days is a review checkpoint, with explicit recorded decisions for extensions. No date-expiry behavior is tested or implemented in this phase.

## Verification

Commands run from `/tmp/genia-f2-p2-b` use this exact prefix to reuse the locked repository environment without changing production files:

```sh
UV_CACHE_DIR=/tmp/uv-cache UV_PROJECT_ENVIRONMENT=/Users/m0smith/projects/genia-2026/.venv uv run --no-sync
```

| Command after prefix | Result |
|---|---|
| `pytest -q tests/unit/test_f2_p2_b_*.py --tb=short --junitxml=/tmp/p2-b-red.xml` | 179 failed in 4.84s; exit 1 expected; zero errors/skips |
| `pytest -q tests/unit/test_f2_p2_a_characterization.py` (independent reviewer) | 42 passed in 4.71s |
| Focused 18-module command below | 523 passed in 480.96s |
| `pytest -n auto -q -m loopback` (initial sandbox run) | 29 failed / 2 passed: denied socket binds; not runtime regression evidence |
| Same loopback command with socket permission | 31 passed in 38.01s |
| `ruff check .` | passed |
| `python -m tools.code_documentation --base-ref origin/main` | 9450 records / 2840 legacy gaps / 1 classified exclusion / 0 errors |
| `python tools/gen_function_docs.py --check` | up to date |
| `python tools/lint_doc.py --scan-dir src/genia/std/prelude --require-coverage` | 24 files / 286 @doc strings / 0 errors or warnings |
| `python tools/gen_mcp_language_profile.py --check` | passed |
| `git diff --check` (no uv prefix) | clean |

Focused selection:

```sh
pytest -q tests/unit/test_f2_p2_a_characterization.py tests/unit/test_scope_accessors_p1_b.py tests/unit/test_host_binding_classification_p1_e.py tests/unit/test_f2_p1_reflection_scope.py tests/unit/test_entry_consumers_p1_c.py tests/unit/test_inspection_consumers_p1_d.py tests/unit/test_scope_consumers_p1_g.py tests/unit/test_repl_env_characterization.py tests/unit/test_modules_phase1.py tests/unit/test_autoload.py tests/unit/test_function_docstrings.py tests/unit/test_metacircular_eval.py tests/unit/test_debug_stdio.py tests/unit/test_cli_args.py tests/unit/test_interpreter_test_mode.py tests/unit/test_r28_mcp_run_worker.py tests/unit/test_r28_mcp_conformance_security.py tests/unit/test_protected_configuration.py
```

Full non-loopback command (intentional reds segregated; no existing tests suppressed):

```sh
pytest -n auto -q -m 'not loopback' --ignore=tests/unit/test_f2_p2_b_registration.py --ignore=tests/unit/test_f2_p2_b_behavior.py --ignore=tests/unit/test_f2_p2_b_hosts.py --ignore=tests/unit/test_f2_p2_b_boundaries.py --ignore=tests/unit/test_f2_p2_b_manifest.py
```

Full non-loopback completed: **6616 passed / 71 skipped / 75 failed** in 1294.21s. Intentional red modules were excluded explicitly; no existing selection was suppressed. The sandbox blocked `ps` process snapshots and launcher/cache access, and this fresh worktree lacked the ignored `uv.lock` required by one existing launcher fixture. The failures are preserved below; this is not a clean full run.

For validation only, copied the existing ignored development lock with `cp /Users/m0smith/projects/genia-2026/uv.lock /tmp/genia-f2-p2-b/uv.lock`. It remains ignored and is not part of the PR. All 75 failed cases were rerun serially with process/cache permission and unchanged deadlines: **75 passed in 176.04s** (exit 0). Remaining unexplained existing-test failures: **0**. This establishes passing observations for the full unchanged selection across the original run and permitted retries; it does not turn the original parallel run into a clean all-green run. The initial diagnostics and passing retry are consistent with environment/load effects (inference), with no evidence of a scope regression.

`python -m tools.spec_runner`: **total=822 passed=822 failed=0 invalid=0** (exit 0). No shared spec was added or changed.

## Independent skeptical audit

**PASS — independent read-only reviewer `/root/skeptical_review`.** Reviewed §16/A1–A3, brief, all modules, fixture, discriminator seams, manifest/autoload distinction, security, reflection and P3 boundaries. Independently executed P2-A (42 passed) and red modules (179 intentional failures in the final snapshot). Blocking findings repaired: REPL mutation omission, catalogue allowlist false positives, incomplete 31-site classification, parameter-metadata overclaims, and latent use syntax. No production edit was recommended or made.

Final guard follow-up was separately reviewed: inventory permits exactly one new E allocation; catalogue guards scan production Python under src/hosts/tools/apps and report only the two existing builtins.py reads. Independent targeted rerun: 2 intentional source-guard reds, no allowlist false positives.

Review limitation: API-dependent positive/mutation paths are statically reviewed now and must actually execute in P2-C/D/E; this phase proves meaningful initial reds, not correctness of absent implementation.

## Coverage exclusions and implementation handoff

- No topology implementation, fallback implementation, strict CI job, P3 shadowing/finality, export/privacy changes or C++ module implementation.
- No official-SDK/VS Code/Node acceptance or live Ollama/Gemini/HTTP run. Host entry tests script only protocol/terminal/network edges and execute real environment construction/evaluation.
- Portable shared-spec candidates deferred to P2-F under existing `doc_help`/`multi_file_eval`: module-own doc/meta/help, local-binding-first reflection and explicit reflective callable grants. The two native twins are Python-only evidence. `open_functions` exists; no standalone metacircular-eval capability is invented. Host fallback/switch/pruning/accessors are not promoted to portable semantics.
- Manifest storage and event-measurement names remain design choices; tests observe routing and use a narrow host-only event adapter. Any adjustment to that adapter must be recorded against §16, without weakening assertions.
- P2-C begins only after red evidence is reviewed and cites `163f5160f6486cb56fc78211edd0afc261a13c18`. Implement topology/one helper/manifest/write-through/host routing, preserving A1 compatibility. P2-D migrates consumers/reflection/eval/debug/sinks/MCP. P2-E implements only the approved temporary fallback, strict capture, safe warnings/events. Assignments: **P2-C 75 / P2-D 87 / P2-E 17**; every individual assignment is in the appendix. Counts describe green-making responsibility, not phase completion.
- Future implementation prompts must require same-slice authoritative STATE/RULES/REPL/README and relevant book/cheatsheet-sidecar updates, explicit host capability/gap review, semantic_facts and MCP language-profile impact (regenerate if affected), composition-boundary review and generated references where public metadata changes. Documentation must describe only behavior actually implemented and verified.
- #1067/#1220/#1221/#1229/#1230 remain open. No merge is performed. Evidence-only follow-up commit and published PR are delivery metadata; P2-C is not authorized by publishing this PR.

## Per-case red diagnostics and green-making slices

Test identifiers include parameter values. First actual failure lines are recorded verbatim apart from Markdown escaping. Contract references/expected behavior are in the group matrix and each test docstring/code; no collection/import failure is counted.

| Test id | Class | Actual first failure | Green-making slice |
|---|---|---|---|
| `tests/unit/test_f2_p2_b_behavior.py::test_B4_B_strict_module_read_rejects_entry_binding[call]` | B | Failed: DID NOT RAISE <class 'NameError'> | P2-E |
| `tests/unit/test_f2_p2_b_behavior.py::test_B4_B_strict_module_read_rejects_entry_binding[top_level]` | B | Failed: DID NOT RAISE <class 'NameError'> | P2-E |
| `tests/unit/test_f2_p2_b_behavior.py::test_B4_B_strict_module_read_rejects_entry_binding[contribution]` | B | Failed: DID NOT RAISE <class 'NameError'> | P2-E |
| `tests/unit/test_f2_p2_b_behavior.py::test_B4_B_fallback_warns_once_per_module_name_pair[call]` | B | AssertionError: P2-E warning absent/undedupe: '' | P2-E |
| `tests/unit/test_f2_p2_b_behavior.py::test_B4_B_fallback_warns_once_per_module_name_pair[top_level]` | B | AssertionError: P2-E warning absent/undedupe: '' | P2-E |
| `tests/unit/test_f2_p2_b_behavior.py::test_B4_B_fallback_warns_once_per_module_name_pair[contribution]` | B | AssertionError: P2-E warning absent/undedupe: '' | P2-E |
| `tests/unit/test_f2_p2_b_behavior.py::test_B4_B_distinct_pairs_warn_independently` | B | AssertionError: assert 0 == 4 | P2-E |
| `tests/unit/test_f2_p2_b_behavior.py::test_B4_B_host_get_never_uses_fallback` | B | Failed: DID NOT RAISE <class 'NameError'> | P2-E |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_B_module_local_reflection_resolves_actual_owner[doc]` | B | AssertionError: assert none('missing-doc', <map 1>) == 'module documentation' | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_B_module_local_reflection_resolves_actual_owner[meta]` | B | AssertionError: assert none('missing-meta', <map 1>) is <map 1> | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_B_module_local_reflection_resolves_actual_owner[help]` | B | assert 'module documentation' in 'No public helper or runtime name found: own_helper\n\nUse \`help()\` for the public surface overview.\n\`doc("name")\` returns none("missing-doc", {name: name}) when a bound name has no doc metadata.\n' | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_B_module_reflection_never_falls_back_to_entry[doc]` | B | AssertionError: module reflection exposed E metadata | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_B_module_reflection_never_falls_back_to_entry[meta]` | B | AssertionError: module reflection exposed E metadata | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_B_module_reflection_never_falls_back_to_entry[help]` | B | AssertionError: assert 'No public helper or runtime name found: entry_subject' in 'entry_subject/1\nDefined at <memory>:1\n\nENTRY_DOCUMENTATION_SENTINEL\n' | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_B_frame_parameter_takes_precedence[doc]` | B | AssertionError: parameter has no binding @doc; do not use R map metadata | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_B_frame_parameter_takes_precedence[meta]` | B | AssertionError: parameter binding has no metadata; do not use R map metadata | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_B_frame_parameter_takes_precedence[help]` | B | AssertionError: assert 'parameter documentation' in 'map/2\nDefined at /private/tmp/genia-f2-p2-b/src/genia/std/prelude/list.genia:130\n\nApply a function to every list element.\n\nCategory: list\n' | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_B_module_evaluation_binding_survives_indirection[indirect]` | B | AssertionError: assert [none('missing-doc', <map 1>)] == ['module documentation'] | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_B_module_evaluation_binding_survives_indirection[alias]` | B | AssertionError: assert none('missing-doc', <map 1>) == 'module documentation' | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_B_module_evaluation_binding_survives_indirection[transfer]` | B | AssertionError: assert none('missing-doc', <map 1>) == 'module documentation' | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_B_module_evaluation_binding_survives_indirection[higher_order]` | B | AssertionError: assert none('missing-doc', <map 1>) == 'module documentation' | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B6_B_empty_env_does_not_implicitly_expose_entry[False]` | B | Failed: DID NOT RAISE <class 'NameError'> | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B6_B_empty_env_does_not_implicitly_expose_entry[True]` | B | Failed: DID NOT RAISE <class 'NameError'> | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B3_B_runtime_closure_cannot_read_entry_binding` | B | Failed: DID NOT RAISE <class 'NameError'> | P2-C |
| `tests/unit/test_f2_p2_b_behavior.py::test_B6_A_explicit_define_and_runtime_names_keep_working` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_B_native_reflection_twin[module_reflection_owns_its_lookup]` | B | AssertionError: total=2 passed=0 failed=2 errored=0 | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_B_native_reflection_twin[frame_parameter_precedes_runtime_name]` | B | AssertionError: total=2 passed=0 failed=2 errored=0 | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_A_reflection_binding_identity_and_explicit_grants[entry]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_A_reflection_binding_identity_and_explicit_grants[entry_alias]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_A_reflection_binding_identity_and_explicit_grants[entry_indirect]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_A_reflection_binding_identity_and_explicit_grants[transfer_to_module]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_A_reflection_binding_identity_and_explicit_grants[user_rebound]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_A_reflection_binding_identity_and_explicit_grants[host_direct]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_A_reflection_binding_identity_and_explicit_grants[prelude]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B4_B_strict_switch_is_captured_once_at_runtime_construction` | B | AssertionError: assert 'TEMPORARY COMPATIBILITY FALLBACK' in '' | P2-E |
| `tests/unit/test_f2_p2_b_behavior.py::test_B4_A_event_measurement_is_deduplicated_and_execution_local` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-E |
| `tests/unit/test_f2_p2_b_behavior.py::test_B4_A_fallback_exclusions_preserve_scope_and_emit_no_events[write]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-E |
| `tests/unit/test_f2_p2_b_behavior.py::test_B4_A_fallback_exclusions_preserve_scope_and_emit_no_events[export]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-E |
| `tests/unit/test_f2_p2_b_behavior.py::test_B4_A_fallback_exclusions_preserve_scope_and_emit_no_events[reflection]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-E |
| `tests/unit/test_f2_p2_b_behavior.py::test_B4_A_fallback_exclusions_preserve_scope_and_emit_no_events[runtime_owned]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-E |
| `tests/unit/test_f2_p2_b_behavior.py::test_B4_A_fallback_exclusions_preserve_scope_and_emit_no_events[local]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-E |
| `tests/unit/test_f2_p2_b_behavior.py::test_B4_A_fallback_exclusions_preserve_scope_and_emit_no_events[eval]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-E |
| `tests/unit/test_f2_p2_b_behavior.py::test_B4_A_fallback_exclusions_preserve_scope_and_emit_no_events[host_get]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-E |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_A_scope_bound_callable_identity_is_stable[doc]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_A_scope_bound_callable_identity_is_stable[meta]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_behavior.py::test_B5_A_scope_bound_callable_identity_is_stable[help]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B11_B_catalogue_source_guard_rejects_implicit_root` | B | AssertionError: §16.5 runtime accessor required: src/genia/builtins.py:3340:root, src/genia/builtins.py:3378:root | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B11_B_autoload_reads_use_runtime_or_reviewed_runtime_constructor` | B | AssertionError: §16.5 catalogue must use R: src/genia/builtins.py:3340:env.root().autoloads, src/genia/builtins.py:3378:env.root().autoloads | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B11_A_help_overview_identical_from_R_E_M_and_pruned_R[False]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B11_A_help_overview_identical_from_R_E_M_and_pruned_R[True]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B11_A_wrong_catalogue_owner_empty_control_is_discriminating` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[runtime-main]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[runtime-native]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[runtime-serve]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[runtime-debug_entry]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[runtime-debug_module]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[runtime-error_sink]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[runtime-stdout_sink]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[runtime-stderr_sink]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[runtime-generator]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[runtime-linter]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[runtime-reflection]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[runtime-mcp_prune]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[entry-main]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[entry-native]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[entry-serve]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[entry-debug_entry]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[entry-debug_module]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[entry-error_sink]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[entry-stdout_sink]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[entry-stderr_sink]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[entry-generator]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[entry-linter]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[entry-reflection]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[entry-mcp_prune]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[module-main]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[module-native]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[module-serve]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[module-debug_entry]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[module-debug_module]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[module-error_sink]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[module-stdout_sink]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[module-stderr_sink]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[module-generator]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[module-linter]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[module-reflection]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_real_consumers_discriminate_wrong_accessors[module-mcp_prune]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_actual_repl_discriminates_wrong_inspection_owner[runtime]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_actual_repl_discriminates_wrong_inspection_owner[entry]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_boundaries.py::test_B12_A_actual_repl_discriminates_wrong_inspection_owner[module]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_hosts.py::test_B8_B_all_13_program_construction_paths_register_entry[repl]` | B | AssertionError: repl: program still evaluated in shared R=E | P2-C |
| `tests/unit/test_f2_p2_b_hosts.py::test_B8_B_all_13_program_construction_paths_register_entry[debug_stdio]` | B | AssertionError: debug_stdio: program still evaluated in shared R=E | P2-C |
| `tests/unit/test_f2_p2_b_hosts.py::test_B8_B_all_13_program_construction_paths_register_entry[serve]` | B | AssertionError: construction site serve did not execute a program | P2-C |
| `tests/unit/test_f2_p2_b_hosts.py::test_B8_B_all_13_program_construction_paths_register_entry[pipe]` | B | AssertionError: assert 1 == 0 | P2-C |
| `tests/unit/test_f2_p2_b_hosts.py::test_B8_B_all_13_program_construction_paths_register_entry[command]` | B | AssertionError: command: program still evaluated in shared R=E | P2-C |
| `tests/unit/test_f2_p2_b_hosts.py::test_B8_B_all_13_program_construction_paths_register_entry[file]` | B | AssertionError: file: program still evaluated in shared R=E | P2-C |
| `tests/unit/test_f2_p2_b_hosts.py::test_B8_B_all_13_program_construction_paths_register_entry[native]` | B | AssertionError: native: program still evaluated in shared R=E | P2-C |
| `tests/unit/test_f2_p2_b_hosts.py::test_B8_B_all_13_program_construction_paths_register_entry[model_fixture]` | B | AssertionError: model_fixture: program still evaluated in shared R=E | P2-C |
| `tests/unit/test_f2_p2_b_hosts.py::test_B8_B_all_13_program_construction_paths_register_entry[grounded_fixture]` | B | AssertionError: grounded_fixture: program still evaluated in shared R=E | P2-C |
| `tests/unit/test_f2_p2_b_hosts.py::test_B8_B_all_13_program_construction_paths_register_entry[concurrency_fixture]` | B | AssertionError: concurrency_fixture: program still evaluated in shared R=E | P2-C |
| `tests/unit/test_f2_p2_b_hosts.py::test_B8_B_all_13_program_construction_paths_register_entry[ollama]` | B | AssertionError: ollama: program still evaluated in shared R=E | P2-C |
| `tests/unit/test_f2_p2_b_hosts.py::test_B8_B_all_13_program_construction_paths_register_entry[mcp_worker]` | B | AssertionError: mcp_worker: program still evaluated in shared R=E | P2-D |
| `tests/unit/test_f2_p2_b_hosts.py::test_B8_B_all_13_program_construction_paths_register_entry[mcp_host]` | B | AssertionError: mcp_host: program still evaluated in shared R=E | P2-D |
| `tests/unit/test_f2_p2_b_hosts.py::test_B9_B_native_registration_discovery_and_execution_are_entry_owned[owner]` | B | assert (<genia.environment.Env object at 0x1071fab70> is not <genia.environment.Env object at 0x1071fab70>) | P2-C |
| `tests/unit/test_f2_p2_b_hosts.py::test_B9_B_native_registration_discovery_and_execution_are_entry_owned[fixtures]` | B | AssertionError: assert ('fixture_marker' in {'Format': <function make_global_env.<locals>.format_constructor at 0x10705b4c0>, '__r18_conformance_test_only_nan': n...e_context_fn at 0x107206200>, '_absence_meta': <function make_global_env.<locals>.absence_meta_fn at 0x1072071a0>, ...} and 'fixture_marker' not in {'Format': <function make_global_env.<locals>.format_constructor at 0x10705b4c0>, '__r18_conformance_test_only_nan': n...e_context_fn at 0x107206200>, '_absence_meta': <function make_global_env.<locals>.absence_meta_fn at 0x1072071a0>, ...}) | P2-C |
| `tests/unit/test_f2_p2_b_hosts.py::test_B9_B_native_registration_discovery_and_execution_are_entry_owned[registrar]` | B | AssertionError: assert ('test' in {'Format': <function make_global_env.<locals>.format_constructor at 0x1070dd1c0>, '__r18_conformance_test_only_nan': n...e_context_fn at 0x107208e00>, '_absence_meta': <function make_global_env.<locals>.absence_meta_fn at 0x107208400>, ...} and 'test' not in {'Format': <function make_global_env.<locals>.format_constructor at 0x1070dd1c0>, '__r18_conformance_test_only_nan': n...e_context_fn at 0x107208e00>, '_absence_meta': <function make_global_env.<locals>.absence_meta_fn at 0x107208400>, ...}) | P2-C |
| `tests/unit/test_f2_p2_b_hosts.py::test_B9_B_native_registration_discovery_and_execution_are_entry_owned[list]` | B | AssertionError: assert not True | P2-C |
| `tests/unit/test_f2_p2_b_hosts.py::test_B9_B_native_registration_discovery_and_execution_are_entry_owned[discovery]` | B | AssertionError: assert 'entry_test' not in {'Format': <function make_global_env.<locals>.format_constructor at 0x10704efc0>, '__r18_conformance_test_only_nan': n...e_context_fn at 0x107204fe0>, '_absence_meta': <function make_global_env.<locals>.absence_meta_fn at 0x107204f40>, ...} | P2-D |
| `tests/unit/test_f2_p2_b_hosts.py::test_B9_B_native_registration_discovery_and_execution_are_entry_owned[runner]` | B | assert <genia.environment.Env object at 0x1073cd490> is not <genia.environment.Env object at 0x1073cd490> | P2-D |
| `tests/unit/test_f2_p2_b_hosts.py::test_B7_B_worker_prunes_runtime_before_entry_registration` | B | assert (<genia.environment.Env object at 0x107238aa0> is not <genia.environment.Env object at 0x107238aa0>) | P2-D |
| `tests/unit/test_f2_p2_b_hosts.py::test_B7_A_denied_names_do_not_regain_runtime_authority[secret_get]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_hosts.py::test_B7_A_denied_names_do_not_regain_runtime_authority[read_file]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_hosts.py::test_B10_B_host_sinks_read_runtime_even_from_child[_emit_error]` | B | AssertionError: assert [] == ['message\n'] | P2-D |
| `tests/unit/test_f2_p2_b_hosts.py::test_B10_B_host_sinks_read_runtime_even_from_child[_write_stdout]` | B | AssertionError: assert [] == ['message'] | P2-D |
| `tests/unit/test_f2_p2_b_hosts.py::test_B10_B_host_sinks_read_runtime_even_from_child[_write_stderr]` | B | AssertionError: assert [] == ['message\n'] | P2-D |
| `tests/unit/test_f2_p2_b_hosts.py::test_B10_B_repl_inspection_excludes_runtime_and_preserves_entry` | B | AssertionError: assert ('stdout = ' not in '17\n5\n2\nF...107060d60>\n' | P2-D |
| `tests/unit/test_f2_p2_b_hosts.py::test_B10_B_debugger_module_globals_use_module_unit` | B | AssertionError: debugger globals selected R instead of M | P2-D |
| `tests/unit/test_f2_p2_b_hosts.py::test_B10_A_debug_hooks_owned_by_runtime_reach_module_and_callbacks` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_hosts.py::test_B9_A_runtime_owned_entry_annotation_is_discovered_and_executed` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_hosts.py::test_B8_A_serve_discovery_includes_entry_declared_runtime_owned_handler` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_hosts.py::test_B10_A_protected_entry_values_are_redacted_in_globals_and_diagnostics` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-D |
| `tests/unit/test_f2_p2_b_manifest.py::test_B2_A_every_prelude_declaration_routes_to_runtime_without_eager_load` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_manifest.py::test_B8_B_program_constructor_guard_no_raw_runtime_factory[src/genia/interpreter.py-repl-0]` | B | AssertionError: §16.6.2 src/genia/interpreter.py:repl site 0: raw R constructor before program evaluation | P2-C |
| `tests/unit/test_f2_p2_b_manifest.py::test_B8_B_program_constructor_guard_no_raw_runtime_factory[src/genia/interpreter.py-run_debug_stdio-0]` | B | AssertionError: §16.6.2 src/genia/interpreter.py:run_debug_stdio site 0: raw R constructor before program evaluation | P2-C |
| `tests/unit/test_f2_p2_b_manifest.py::test_B8_B_program_constructor_guard_no_raw_runtime_factory[src/genia/interpreter.py-_run_serve_file-0]` | B | AssertionError: §16.6.2 src/genia/interpreter.py:_run_serve_file site 0: raw R constructor before program evaluation | P2-C |
| `tests/unit/test_f2_p2_b_manifest.py::test_B8_B_program_constructor_guard_no_raw_runtime_factory[src/genia/interpreter.py-_run_execution_mode-0]` | B | AssertionError: §16.6.2 src/genia/interpreter.py:_run_execution_mode site 0: raw R constructor before program evaluation | P2-C |
| `tests/unit/test_f2_p2_b_manifest.py::test_B8_B_program_constructor_guard_no_raw_runtime_factory[src/genia/interpreter.py-_run_execution_mode-1]` | B | AssertionError: §16.6.2 src/genia/interpreter.py:_run_execution_mode site 1: raw R constructor before program evaluation | P2-C |
| `tests/unit/test_f2_p2_b_manifest.py::test_B8_B_program_constructor_guard_no_raw_runtime_factory[src/genia/interpreter.py-_run_execution_mode-2]` | B | AssertionError: §16.6.2 src/genia/interpreter.py:_run_execution_mode site 2: raw R constructor before program evaluation | P2-C |
| `tests/unit/test_f2_p2_b_manifest.py::test_B8_B_program_constructor_guard_no_raw_runtime_factory[src/genia/test_cli.py-make_test_env-0]` | B | AssertionError: §16.6.2 src/genia/test_cli.py:make_test_env site 0: raw R constructor before program evaluation | P2-C |
| `tests/unit/test_f2_p2_b_manifest.py::test_B8_B_program_constructor_guard_no_raw_runtime_factory[hosts/python/exec_model_fixture.py-_build_env-0]` | B | AssertionError: §16.6.2 hosts/python/exec_model_fixture.py:_build_env site 0: raw R constructor before program evaluation | P2-C |
| `tests/unit/test_f2_p2_b_manifest.py::test_B8_B_program_constructor_guard_no_raw_runtime_factory[hosts/python/exec_r12_grounded_fixture.py-_build_env-0]` | B | AssertionError: §16.6.2 hosts/python/exec_r12_grounded_fixture.py:_build_env site 0: raw R constructor before program evaluation | P2-C |
| `tests/unit/test_f2_p2_b_manifest.py::test_B8_B_program_constructor_guard_no_raw_runtime_factory[hosts/python/exec_r25_concurrency_fixture.py-_build_env-0]` | B | AssertionError: §16.6.2 hosts/python/exec_r25_concurrency_fixture.py:_build_env site 0: raw R constructor before program evaluation | P2-C |
| `tests/unit/test_f2_p2_b_manifest.py::test_B8_B_program_constructor_guard_no_raw_runtime_factory[hosts/python/exec_ollama_chat.py-main-0]` | B | AssertionError: §16.6.2 hosts/python/exec_ollama_chat.py:main site 0: raw R constructor before program evaluation | P2-C |
| `tests/unit/test_f2_p2_b_manifest.py::test_B8_B_program_constructor_guard_no_raw_runtime_factory[hosts/python/mcp_worker.py-execute_source-0]` | B | AssertionError: §16.6.2 hosts/python/mcp_worker.py:execute_source site 0: raw R constructor before program evaluation | P2-C |
| `tests/unit/test_f2_p2_b_manifest.py::test_B8_B_program_constructor_guard_no_raw_runtime_factory[hosts/python/mcp_host.py-main-0]` | B | AssertionError: §16.6.2 hosts/python/mcp_host.py:main site 0: raw R constructor before program evaluation | P2-C |
| `tests/unit/test_f2_p2_b_manifest.py::test_B8_B_program_evaluator_paths_have_registered_entry_guard` | B | assert (<genia.environment.Env object at 0x107067800> is <genia.environment.Env object at 0x107067800> and <genia.environment.Env object at 0x107067800> is not <genia.environment.Env object at 0x107067800>) | P2-D |
| `tests/unit/test_f2_p2_b_manifest.py::test_B8_B_31_site_inventory_classifies_all_raw_program_constructors` | B | AssertionError: A3 unclassified ownership/construction paths: {('src/genia/interpreter.py', 'repl', 'make_global_env'): 1, ('src/genia/interpreter.py', 'run_debug_stdio', 'make_global_env'): 1, ('src/genia/interpreter.py', '_run_serve_file', 'make_global_env'): 1, ('src/genia/interpreter.py', '_run_execution_mode', 'make_global_env'): 3, ('src/genia/test_cli.py', 'make_test_env', 'make_global_env'): 1, ('hosts/python/exec_model_fixture.py', '_build_env', 'make_global_env'): 1, ('hosts/python/exec_ollama_chat.py', 'main', 'make_global_env'): 1, ('hosts/python/exec_r12_grounded_fixture.py', '_build_env', 'make_global_env'): 1, ('hosts/python/exec_r25_concurrency_fixture.py', '_build_env', 'make_global_env'): 1, ('hosts/python/mcp_host.py', 'main', 'make_global_env'): 1, ('hosts/python/mcp_worker.py', 'execute_source', 'make_global_env'): 1} | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B1_A_registered_scope_invariant[distinct]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B1_A_registered_scope_invariant[parent]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B1_A_registered_scope_invariant[registration]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B1_A_registered_scope_invariant[runtime]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B1_A_registered_scope_invariant[entry_frame]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B1_A_registered_scope_invariant[module_frame]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B1_A_registered_scope_invariant[disjoint]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B1_A_registered_scope_invariant[autoloads]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B1_A_registered_scope_invariant[identity]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B1_A_registered_scope_invariant[inspection]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B1_A_second_registration_rejected` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B1_A_entry_host_class_routes_from_any_scope[runtime]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B1_A_entry_host_class_routes_from_any_scope[entry]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B1_A_entry_host_class_routes_from_any_scope[module]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B1_A_late_runtime_install_and_owned_entry_injection_rejected[public]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B1_A_late_runtime_install_and_owned_entry_injection_rejected[internal]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B1_A_late_runtime_install_and_owned_entry_injection_rejected[autoload]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B1_A_late_runtime_install_and_owned_entry_injection_rejected[owned_entry]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_duplicate_collisions_keep_single_root_diagnostic[False-first-x-x-first(41)-41]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_duplicate_collisions_keep_single_root_diagnostic[False-map-f, xs-xs-map((x) -> x, [41])-result1]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_duplicate_collisions_keep_single_root_diagnostic[False-map_acc-f, xs, acc-acc-map_acc((x) -> x, [], [41])-result2]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_duplicate_collisions_keep_single_root_diagnostic[True-first-x-x-first(41)-41]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_duplicate_collisions_keep_single_root_diagnostic[True-map-f, xs-xs-map((x) -> x, [41])-result1]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_duplicate_collisions_keep_single_root_diagnostic[True-map_acc-f, xs, acc-acc-map_acc((x) -> x, [], [41])-result2]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_distinct_arities_merge_in_runtime[rows-rows() = 71-[rows(), rows(sheet([["a", [1]]]))]-expected0]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_distinct_arities_merge_in_runtime[first-first(x,y) = y-[first([3]) \|> unwrap_or(0), first(1,42)]-expected1]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_assignment_write_through_loaded_and_unloaded[log-True]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_assignment_write_through_loaded_and_unloaded[first-True]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_assignment_write_through_loaded_and_unloaded[first-False]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_assignment_write_through_loaded_and_unloaded[map_acc-False]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_host_owned_write_through_and_entry_only_name` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_prelude_hijack_is_pinned_for_P3_retirement[first-first(x) = x]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_prelude_hijack_is_pinned_for_P3_retirement[map_acc-map_acc(f,xs,acc) = acc]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B3_A_runtime_closure_cannot_read_or_write_entry_only` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B3_A_runtime_owned_entry_declaration_remains_visible_to_R` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_manifest_ownership_survives_pruning_without_conveying_authority` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_all_entry_binding_forms_route_runtime_owned_names[pattern]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_all_entry_binding_forms_route_runtime_owned_names[import]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_all_entry_binding_forms_route_runtime_owned_names[open]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_all_entry_binding_forms_route_runtime_owned_names[use]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B2_A_all_entry_binding_forms_route_runtime_owned_names[metadata]` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |
| `tests/unit/test_f2_p2_b_registration.py::test_B1_A_registration_must_be_owned_by_runtime` | A | Failed: P2-C API missing: Env.create_entry_scope() (§16.6.1) | P2-C |

## Full-regression initial failures and exact permitted retry

Initial failures (no changed deadlines): 9 compatibility conformance; 23 conformance lifecycle; 1 runaway-output conformance; 1 entrypoint; 8 portability; 9 supervisor; 6 MCP run; 1 stdio config; 10 stdio launch; 7 stdio lifecycle = 75. Representative diagnostics: `PermissionError: [Errno 1] Operation not permitted: 'ps'`, `server closed stdout before the expected frame`, `Failed to initialize cache at /Users/m0smith/.cache/uv`, and missing `/private/tmp/genia-f2-p2-b/uv.lock`. A serial permitted retry distinguishes these environmental failures from test changes; the initial failed run is not erased by retry.

Exact failed-node selection (same environment prefix as above, run with process/cache permission; output redirected to `/tmp/p2-b-regression-retry.log`):

```sh
pytest -q \
  'tests/unit/test_r28_mcp_compat_conformance.py::test_cancellation_mid_run_returns_no_partial_data_and_reaps_the_worker_in_the_compat_era[denied]' \
  'tests/unit/test_r28_mcp_compat_conformance.py::test_a_cancel_queued_with_its_request_wins_in_the_compat_era' \
  'tests/unit/test_r28_mcp_compat_conformance.py::test_timeout_is_the_same_closed_failure_and_the_session_survives_in_the_compat_era[denied]' \
  'tests/unit/test_r28_mcp_compat_conformance.py::test_sigterm_mid_run_in_a_compat_session_reaps_the_worker[denied]' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_a_cancel_that_does_not_name_the_running_request_is_ignored[string-id-for-an-integer-request-]' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_a_cancel_that_does_not_name_the_running_request_is_ignored[missing-requestId-]' \
  'tests/unit/test_r28_mcp_compat_conformance.py::test_cancellation_mid_run_returns_no_partial_data_and_reaps_the_worker_in_the_compat_era[host]' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_a_cancel_that_does_not_name_the_running_request_is_ignored[null-requestId-]' \
  'tests/unit/test_r28_mcp_compat_conformance.py::test_sigterm_mid_run_in_a_compat_session_reaps_the_worker[host]' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_a_cancel_that_does_not_name_the_running_request_is_ignored[no-params-]' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_a_cancel_that_does_not_name_the_running_request_is_ignored[cancel-sent-as-a-request-]' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_duplicate_cancellations_cancel_exactly_once_and_never_a_later_request' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_cancel_queued_with_the_request_wins_and_the_worker_is_reaped[host]' \
  'tests/unit/test_r28_mcp_compat_conformance.py::test_timeout_is_the_same_closed_failure_and_the_session_survives_in_the_compat_era[host]' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_cancel_during_evaluation_returns_no_partial_data_and_removes_the_workdir[host]' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_cancel_queued_with_the_request_wins_and_the_worker_is_reaped[denied]' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_cancel_during_evaluation_returns_no_partial_data_and_removes_the_workdir[denied]' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_cancellation_near_successful_completion_yields_exactly_one_whole_terminal_state' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_cancellation_near_the_deadline_yields_exactly_one_terminal_state' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_a_cancel_that_does_not_name_the_running_request_is_ignored[wrong-request-id-]' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_timeout_is_fixed_closed_partial_free_and_the_next_request_still_works[denied]' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_timeout_is_fixed_closed_partial_free_and_the_next_request_still_works[host]' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_sighup_to_the_client_launched_process_stops_the_chain_and_cleans_up' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_a_discover_probe_launch_followed_by_a_session_launch_leaves_nothing_behind' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_other_unbounded_programs_are_bounded_by_the_same_fixed_deadline[unbounded-flow-without-output]' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_other_unbounded_programs_are_bounded_by_the_same_fixed_deadline[long-sleep]' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_overflow_kills_the_worker_and_removes_its_private_directory' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_no_worker_remains_after_a_mixed_session_of_every_terminal_state' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_sigterm_to_the_host_mid_run_reaps_the_worker_and_removes_its_directory[host]' \
  'tests/unit/test_r28_mcp_conformance_lifecycle.py::test_sigterm_to_the_host_mid_run_reaps_the_worker_and_removes_its_directory[denied]' \
  'tests/unit/test_r28_mcp_compat_conformance.py::test_a_client_disconnect_after_initialize_leaves_nothing_behind' \
  'tests/unit/test_r28_mcp_compat_conformance.py::test_repeated_connections_each_start_new_and_are_independent' \
  'tests/unit/test_r28_mcp_conformance_run.py::test_runaway_output_is_stopped_at_the_limit_not_accumulated_until_the_deadline' \
  'tests/unit/test_r28_mcp_entrypoint.py::test_the_entrypoint_works_from_any_working_directory' \
  'tests/unit/test_r28_mcp_portability.py::test_the_backend_counts_an_unreaped_zombie_as_alive[ps]' \
  'tests/unit/test_r28_mcp_portability.py::test_the_backend_sees_descendants_their_command_lines_and_identities[ps]' \
  'tests/unit/test_r28_mcp_portability.py::test_the_ps_backend_asks_for_untruncated_command_lines' \
  'tests/unit/test_r28_mcp_portability.py::test_the_ps_backend_sees_a_long_command_line_in_full' \
  'tests/unit/test_r28_mcp_portability.py::test_the_backend_finds_the_governed_worker_of_a_live_session_and_proves_cleanup[ps]' \
  'tests/unit/test_r28_mcp_portability.py::test_the_process_probe_reports_how_this_platform_shows_the_governed_worker' \
  'tests/unit/test_r28_mcp_portability.py::test_the_backend_reads_a_processs_working_directory[ps]' \
  'tests/unit/test_r28_mcp_portability.py::test_the_backend_sees_no_listener_for_the_launcher_chain[ps]' \
  'tests/unit/test_r28_mcp_run_supervisor.py::test_each_call_is_a_fresh_process_in_its_own_process_group' \
  'tests/unit/test_r28_mcp_run.py::test_cancel_queued_with_the_request_cancels_without_a_surviving_worker' \
  'tests/unit/test_r28_mcp_run.py::test_other_requests_during_a_run_are_answered_in_order_after_it' \
  'tests/unit/test_r28_mcp_run.py::test_deadline_returns_timeout_and_reaps_the_worker[busy-loop]' \
  'tests/unit/test_r28_mcp_run_supervisor.py::test_deadline_is_measured_from_readiness_not_from_spawn' \
  'tests/unit/test_r28_mcp_run.py::test_deadline_returns_timeout_and_reaps_the_worker[sleep]' \
  'tests/unit/test_r28_mcp_run_supervisor.py::test_worker_that_never_becomes_ready_is_internal_error_after_the_startup_limit' \
  'tests/unit/test_r28_mcp_run_supervisor.py::test_worker_children_die_with_the_worker[plain]' \
  'tests/unit/test_r28_mcp_run_supervisor.py::test_cancel_line_arriving_mid_run_cancels_and_other_lines_are_preserved' \
  'tests/unit/test_r28_mcp_run.py::test_cancel_immediately_after_worker_creation_cancels_and_reaps' \
  'tests/unit/test_r28_mcp_run_supervisor.py::test_strict_reap_check_sees_an_unreaped_zombie' \
  'tests/unit/test_r28_mcp_run.py::test_cancelled_envelope_carries_no_partial_data' \
  'tests/unit/test_r28_mcp_run_supervisor.py::test_deadline_returns_timeout_and_reaps_the_worker' \
  'tests/unit/test_r28_mcp_run_supervisor.py::test_cancel_during_bootstrap_cancels_and_reaps' \
  'tests/unit/test_r28_mcp_run_supervisor.py::test_cancel_line_already_queued_with_the_request_cancels' \
  'tests/unit/test_r28_mcp_stdio_config.py::test_no_python_mcp_sdk_is_a_dependency' \
  'tests/unit/test_r28_mcp_stdio_launch.py::test_the_configured_command_discovers_exactly_the_three_tools_and_nothing_else' \
  'tests/unit/test_r28_mcp_stdio_launch.py::test_stdout_carries_only_json_rpc_frames_and_stderr_is_silent' \
  'tests/unit/test_r28_mcp_stdio_launch.py::test_the_native_application_is_the_server_not_a_python_implementation' \
  'tests/unit/test_r28_mcp_stdio_launch.py::test_the_configured_server_denies_every_prohibited_authority_without_effect' \
  'tests/unit/test_r28_mcp_stdio_launch.py::test_no_process_in_the_chain_holds_a_listening_socket' \
  'tests/unit/test_r28_mcp_stdio_launch.py::test_invalid_source_is_diagnosed_by_parse_then_repaired_then_run' \
  'tests/unit/test_r28_mcp_stdio_launch.py::test_hostile_program_output_cannot_corrupt_protocol_framing' \
  'tests/unit/test_r28_mcp_stdio_launch.py::test_a_program_sees_no_argv_stdin_or_inherited_state' \
  'tests/unit/test_r28_mcp_stdio_launch.py::test_each_launch_is_independent_and_stateless' \
  'tests/unit/test_r28_mcp_stdio_launch.py::test_a_client_can_launch_twice_in_a_row_and_get_the_same_answers' \
  'tests/unit/test_r28_mcp_stdio_lifecycle.py::test_cancellation_still_reaps_the_worker_through_the_wrapper_chain' \
  'tests/unit/test_r28_mcp_stdio_lifecycle.py::test_closing_stdin_mid_run_lets_the_run_finish_then_exits' \
  'tests/unit/test_r28_mcp_stdio_lifecycle.py::test_a_signal_to_the_client_launched_process_stops_the_entire_chain_and_cleans_up[SIGTERM]' \
  'tests/unit/test_r28_mcp_stdio_lifecycle.py::test_a_signal_to_the_client_launched_process_stops_the_entire_chain_and_cleans_up[SIGINT]' \
  'tests/unit/test_r28_mcp_stdio_lifecycle.py::test_sigterm_to_the_host_reaps_the_worker_and_removes_its_directory' \
  'tests/unit/test_r28_mcp_stdio_lifecycle.py::test_a_client_that_closes_both_streams_mid_run_leaves_no_survivors' \
  'tests/unit/test_r28_mcp_stdio_lifecycle.py::test_closing_stdin_while_idle_exits_cleanly_and_leaves_nothing' > /tmp/p2-b-regression-retry.log 2>&1
```
