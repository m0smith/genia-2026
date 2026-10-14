# F2 P2 pre-flight — physical scope separation (issue #1067)

Phase: **preflight only.** No runtime, test, STATE, contract, or spec change is
made by this record. `GENIA_STATE.md` remains final authority and describes
single-root behavior; the F2 contract (`docs/design/f2-module-entry-scope-isolation-contract.md`)
and P1 design (`docs/design/f2-p1-consumer-preparation.md`) remain **PROPOSED**.
Tracking: [#1067](https://github.com/m0smith/genia-2026/issues/1067), carry-forward
obligations [#1220](https://github.com/m0smith/genia-2026/issues/1220) and
[#1221](https://github.com/m0smith/genia-2026/issues/1221).

P2-0 rulings (proposed): `.genia/process/issue-1067-f2-p2-0-decisions.md`.

**Verdict: CONDITIONAL GO** — for the contract-clarification slice (P2-0) and the
characterization slice (P2-A) only. **NO-GO** for any slice that moves bindings
or allocates a distinct entry scope until the P2-0 rulings in §J exist.

## A. Current baseline (verified in code, not from PR text)

- `origin/main` = `c4cecd1` (PR #1222). #1219 merged as `10ed362`; P1-H record
  `.genia/process/issue-1067-f2-p1-h-integration.md` exists; #1220/#1221 are
  recorded as P2 completion obligations in both that record and contract §10
  (commit `ec5e060`). #1067, #1220, #1221 are open.
- Topology today: `make_global_env()` returns one parentless `Env`; every entry
  program (file, `-c`, pipe, test, REPL, debug, serve, MCP worker, `hosts/python/exec_*`
  adapters) runs directly in it; module Envs are `Env(root, rebind_parent=False)`
  (`environment.py:366`); prelude autoloads evaluate into and close over it
  (`environment.py:310`).
- All four P1 accessors exist (`environment.py:96-122`) and every one resolves
  to the root except `unit_scope()`, which returns the declaring module Env via
  an inherited `_unit_scope` reference (set at `:53`, replaced for modules at `:367`).
  `set_host*`/`register_host_autoload` record `runtime-public`/`entry-only` classes
  in side dictionaries on the Env but **install in the same Env** (`:159-197`).
- P1 consumers confirmed re-pointed: CLI `main` (`interpreter.py:499`), serve
  (`:549`), native-test discovery/registrar list (`test_cli.py:87,102,180`),
  debugger root frame (`debug_controller.py:290`), debugger globals and REPL
  `:env` via `inspection_globals_scope()` (`debug_controller.py:244`,
  `interpreter.py:383`), MCP prune (`mcp_worker_profile.py:144`), doc tooling
  (`tools/gen_function_docs.py:110`, `tools/lint_doc.py:536,556`).
- Empirical probe (throwaway, not committed): with `R = make_global_env([])` and a
  plain `E = Env(R)` running the entry, today's code gives: entry `first(x)=x` and
  `map(...)=...` land in **E and shadow**; entry `rows()=1` creates an E-only group
  that **hides R's other arities**; `log = 5` **rebinds R** (E stays empty);
  `help("x")`/`doc("zzz")` for an entry-defined name **miss** (reflection closures
  capture R); `E.entry_scope()` and `E.runtime_scope()` both return R. So a naive
  child scope is *not* the contract's P2 (it is partly P3), see §B and §J.

## B. Target scope model (what is approved vs unresolved)

Grounded in contract §4–§9 and P1 design §2. "Approved" = contract §14 "approved";
everything else is unresolved and is listed in §J.

| Question | Answer | Status |
|---|---|---|
| 1. Parent graph | R (parentless; builtins, prelude, `runtime-public`, module cache, autoload tables, debug state). E = child of R. Each M = child of R (never of E or another M). Prelude closes over R | Approved (§4.2) |
| 2. Ownership | Builtins/internal/autoload/sinks/`argv`/providers → R. Program top level, import aliases, `entry-only` injections (test fixtures, `test` registrar, `exec_*` fixtures) → E. Module top level, aliases, `open_contributions` → M | Approved (§4.2, §6) |
| 3. Lookup | E: E→R(+autoload). M: M→R(+autoload). R: R(+autoload). Fixed lexical, never caller-dependent. Existing `Env.get` order (chain → internal → autoload → NameError) is already the right insertion order for the P2 fallback (just before `NameError`) | Approved; fallback placement is a pre-flight recommendation |
| 4. Writes | Assignment and definition from prelude/module code never reach E. **Entry assignment/definition of a name that exists in R** is the open question below | Partly approved (§4.4); collision rows unresolved |
| 5. Top-level entry definitions | E, except names bound in (or autoload-registered to) R, whose P2 behavior is "unchanged" (§9.1 table) | **Unresolved mechanism** |
| 6. Module isolation | M sees M, aliases, R. P2 adds a temporary read-only E fallback with a once-per-(module,name) stderr warning and a host-local strict switch | Approved (§5, §11); registry/switch/deadline unresolved |
| 7. Host-owned functions | Capture R; reach E only through values the entry passes. `set_host(..., visibility=…)` becomes the single routing point (`entry-only`→E, `runtime-public`→R) | Recommended; routing site is new |
| 8. Reflection/help | D1: resolve in the scope where the identifier is **evaluated**; catalogue/autoload/stdout stay on R. P1-F factored `_help_in_scope`, `doc_fn`, `meta_fn` with a lookup Env but still bind R | D1 approved; evaluation-bound mechanism is a P1-design *recommendation*, not ruled |
| 9. Same name in R and E | P2: **unchanged** observable collision/rebinding behavior (§9.1). P3: shadow in E (D2, D2b) | Approved as a table; mechanism unresolved |
| 10. Backward compatible | Everything in the §9.1 "P2" column, `:env` output *for the entry* (D3 narrows it), debugger entry-frame view, all CLI/exit/stdout behavior, `make_global_env()`+`run_source(src, env)` for callers that supply their own root | Approved |
| 11. Observable change | (a) module reads of E names still work **with a warning** (stderr only); (b) prelude can no longer write E; (c) `:env`/debugger `globals` narrow to the unit (D3); (d) reflection resolves per D1 (e.g. `doc("own_helper")` in a module now works) | Approved (§7.2, §8, §10) |
| 12. MCP workers | Prune **R** (bindings and autoloads) before any E exists; E starts empty and receives no `runtime-public`/`entry-only` host binding; `policy_violation` static layer unchanged; defense in depth, not a sandbox | Recommended; fail-closed tests required (§E) |

**Not P2** (do not pull forward): shadowing in E (D2/D2b), `NameError` for module
reads, fallback removal, export/privacy, C++ module system.

## C. Migration inventory (classification of every direct-root dependency)

Disposition: **R** = correct/retain, **M** = must migrate in P2, **P3** = later,
**?** = needs a contract decision. `root()` replacement is decided per ownership,
never blanket. Under the planned graph R is the structural root, so
`self.root()` *inside `Env`* already equals R for every Env (E, M, frames).

| Site | Dependency | Disp. | Note |
|---|---|---|---|
| `environment.py:130-133` `get` | internal values + autoload via `root()` | R | Correct (runtime-owned). Fallback hook goes here |
| `:157` `set_internal`; `:276` `register_autoload`; `:287` `try_autoload` (evaluates into root) | runtime tables | R | Autoload must keep defining into R; add test that it never defines into E |
| `:353-387` `load_module` | cache, `loading_modules`, parent=root | R | M stays child of R; alias bound by the importing scope (`evaluator.py:1499`) |
| `:98` `runtime_scope` / `:106` `entry_scope` / `:122` `inspection_globals_scope` | accessor mapping | M | The three one-line remaps are the P2 flip. `entry_scope` needs a registered E; default stays R for caller-created roots |
| `:159-197` `set_host*`, `register_host_autoload` | classes recorded, installed in self | M | Route by class; today they are metadata-only |
| `:219-250` `define_function`; `evaluator.py:1503` open redeclaration check | own-`values` only | ? | Source of the `rows`/`first` collision rows; see §J-1 |
| `:199-217` `assign`/`find_assign_target` | walks parents if `rebind_parent` | R | E with `rebind_parent=True` reproduces "rebinds R" for assignment; module Envs stay `False` |
| `environment.py:259-273` `merge_binding_metadata`, `get_metadata` | parent walk | R | Metadata follows the binding's owning Env; add collision-row metadata test |
| `builtins.py:3340`, `:3378` (#1220) | `env.root().autoloads` in help catalogue | M (see §G) | `env` there is captured R, so the migration is **behavior-neutral** under the approved graph; closing #1220 needs a test/guard decision (§G) |
| `builtins.py` `doc_fn`/`meta_fn`/`help_fn` (`help_fn` `:3490`, `_help_in_scope` `:3448`, `doc_fn` `:3531`, `meta_fn` `:3565`) | R-bound lookup Env | M (D1) | Entry names currently invisible to `doc`/`help` once E exists (probe). Must bind evaluation scope or entry reflection regresses |
| `builtins.py:394-` `_make_meta_env` (`Env(env, rebind_parent=False)`) | metacircular base env is a child of R, so it currently also sees entry names | ? | Incidental visibility; decide keep (E fallback-like) or restrict; needs a characterization test first |
| `builtins.py:~5884-6107` `make_global_env` host installs | runtime-public by P1-E | R | Keep in R; `trusted_autoloads.update` at `:6518` is R state |
| `interpreter.py:336` `_emit_error`; `test_cli.py:283,292` `_write_stdout/_write_stderr` | `env.values.get("stderr"/"stdout")` on the supplied Env | M | P1 design §3 prescribed a runtime accessor; code still reads the supplied Env's own dict. If handed E, custom sinks are silently skipped for `sys.stderr`. Not yet shown which Env each caller passes — verify in P2-A |
| `interpreter.py:200-217` `run_source` | writes `debug_hooks`/`debug_mode`/`internal_access` on the supplied Env | M | Debug state is runtime-owned; E would get its own copy while R's stays at constructor values. Decide owner = R |
| `interpreter.py:338-` `_emit_result` | `env.get("stdout")` lexical | R | Correct from E |
| `interpreter.py:383` REPL `:env` | `inspection_globals_scope()` | M (D3) | Remap to unit/E; entry-only listing; existing characterization test updates |
| `interpreter.py:499` `_resolve_program_result` | `entry_scope().values["main"]` | R | Correct once `entry_scope()` returns E |
| `interpreter.py:549` serve; `server_*_binding.py` | entry IR + `entry_env` | R | Correct once E; annotations must not scan R/M |
| `interpreter.py:354,419,540,631,644,659`; `test_cli.py:86`; `hosts/python/{exec_model_fixture,exec_ollama_chat,exec_r12_grounded_fixture,exec_r25_concurrency_fixture,mcp_host,mcp_worker}.py` | the **construction sites** (13) that create the one env | M | Each must create/register E and run source in it. This is where separation actually becomes real |
| `test_cli.py:102,180-182` | entry values scan | R | Correct once E; `make_test_env` fixtures/registrar → E via `set_host(entry-only)` |
| `debug_controller.py:244` globals; `:246` locals; `:290` root frame; `:214-221` `_frame_for_env` | globals/frames | M / R | Globals remap to `unit_scope()` (D3). `_frame_for_env` falls back to `frames[0]` for Envs under R (prelude frames); verify it still lands on E |
| `hosts/python/mcp_worker_profile.py:144-152` `prune_environment`; `mcp_worker.py:225-241` | prunes runtime values/autoloads, then evaluates in same env | M | Prune R, then create E; no E binding may re-introduce a denied name |
| `tools/gen_function_docs.py:110`; `tools/lint_doc.py:536,556` | fresh-env catalogue | R | Must stay `runtime_scope()`; never entry |
| `host_bridge.py:417-453` | `root.loaded_modules` | R | Module cache is R |
| `callable.py:1127-1134` `_closure_lookup` (awareness), manual `.values` walk | no autoload, no fallback | ? | Awareness of a callable resolved via fallback differs from call-time; characterize (R20/Outcome awareness) |
| `builtins.py:535,886,4217,4227,4267,5939,5970` (`Evaluator(env, env.debug_hooks, env.debug_mode)` on captured R); `environment.py:368-369` (module copies `root.debug_hooks`) | debug state read from R | M | `run_source` writes hooks only on the Env it is given (`interpreter.py:210-211`); running in E would leave R's hooks no-op, losing stepping inside HOF callbacks and modules. Rule: R owns debug state |
| `test_cli.py:318-324` (`getattr(env, "_native_test_units")` on the constructed env) vs `:87` (`setattr` on `entry_scope()`) | legacy test list read/written on different Envs | M | Once E≠R legacy `test(...)` locations are silently dropped; the construction helper must register E before `:87`, and `:322` must use `entry_scope()` |
| `server_{config,cors,route}_binding.py` (~`:223/187/217`) | parent-walking `get_metadata` | R | Correct under any write-through; verify in T3 |
| Prelude top-level helpers with no autoload registration (e.g. `map_acc`, `filter_acc`, `reverse_acc`, `nth_impl`, `take_acc`, `range_acc` in `std/prelude/list.genia`) | name not in R and not autoload-registered until the file loads | ? | Defeats a rule keyed on "bound in R or autoload-registered" (§J-1) |
| Tests: 171 files call `make_global_env`; 5 inspect `env.values`; none call `.root()` | harnesses | see §E | Caller-created roots keep entry==root; **most of the suite will not exercise separation** unless P2 says so |
| Fallback, shadowing, `NameError`, fallback removal, D2b | — | P3 | Out of P2 |

## D. Risk register (ranked)

Each: current → target → failure mode → mitigation → verification.

1. **Collision rows cannot be "unchanged" by structure alone** (`define_function`/open
   redeclaration check own `values`). Current: entry definition in the shared root
   merges with R's group, errors on duplicate arity, and is seen by prelude. Target
   (§9.1 P2): unchanged. Failure: child E silently becomes P3 shadowing (probe:
   `first`, `map`, `rows`) and hides R's other arities. Mitigation: explicit
   write-through rule (§J-1). Verify: four pinned collision rows, red first. Note the rule is order-dependent (whether a name is already bound depends on load timing) and also governs `IrOpenFuncDef` (`evaluator.py:1503`).
2. **Reflection regresses for entry names once E exists** (probe). Mitigation: D1
   evaluation-bound activation, covering `IrVar`, direct `eval_call`, both pipeline
   name paths and autoload retry (P1 design §6), with value-based marking so user
   rebinding of `doc` keeps its value. Verify: entry/module/prelude/indirect
   (`map(doc, names)`)/transferred/alias cases; callable-identity and R18 evidence.
3. **Suite coverage illusion.** 171 test files use `run_source(src, make_global_env())`
   (entry==root default) and will stay green without exercising E≠R. Mitigation:
   host-entry-point-level separated tests plus a parametrized separated mode for
   the P1-listed families (§E, #1221). Verify: each boundary has a test that fails
   under the wrong accessor.
4. **Host construction sites missed** (13 sites; fixtures installed after
   `make_global_env`). Failure: an adapter runs in R, silently keeping the leak, or
   installs a fixture in R. Mitigation: one construction helper, grep guard (like
   P1-E's raw-injection guard) that fails on `make_global_env(` followed by direct
   program evaluation outside the helper.
5. **MCP pruning applied to the wrong scope or after E creation.** Failure: E
   receives/keeps a denied name or an unpruned autoload. Mitigation: prune R before
   E; E has no host bindings; assert `E.parent is R`, denied names undefined from
   E, `help()` catalogue pruned. Verify: existing `test_r28_mcp_*` + new separated
   tests; fail-closed on registry change.
6. **Fallback incompleteness.** Reads reaching E through paths other than `Env.get`
   (`_closure_lookup`, direct `values` reads at `evaluator.py:1503`) or writes/reflection/exports
   accidentally using it (§11.2.3). Mitigation: one named code path in `Env.get`'s miss
   branch; dedupe on R; reported against the **declaring** module (`unit_scope().module_id`);
   no value/path/exception text. Verify: contribution closures, nested frames, lazy
   Flow callbacks, transitive imports; warning content test.
7. **Debug/runtime state split** (`run_source` writes hooks on the supplied Env;
   `_frame_for_env` falls back to `frames[0]`). Mitigation: R owns debug state;
   characterize breakpoint/step across E, M, prelude frames before the flip.
8. **Hidden E visibility through the metacircular base env** (`_make_meta_env`).
   Decide before flip (§J-4); characterize first.
9. **Protected values / R10.** Placing a binding in R or E must not create
   declassification authority or leak via `:env`/debugger `globals`. Mitigation:
   existing sentinel-proof patterns re-run against separated scopes; `entry-only`
   fixtures stay out of R.
10. **STATE size.** `GENIA_STATE.md` is 42,865 words against a 43,000 limit
    (135-word margin, per the P1-H record). P2 docs must be net-small or trim.
11. **Circular imports / import-order.** Module is a sibling child of R; cycle
    detection unchanged. Verify transitive and aliased imports and
    entry-bound-before/after import give the same result (with warning).
12. **Premature P3.** Any E shadowing, `NameError`, or D2b work leaking into P2.
    Mitigation: scope lock in the P2 issue; P3 criteria §11.4 untouched.

## E. Test plan

Execution: `uv run pytest -n auto -q -m "not loopback"` and `-m loopback`; focused
`uv run pytest tests/unit/test_scope_*.py tests/unit/test_inspection_consumers_p1_d.py tests/unit/test_repl_env_characterization.py tests/unit/test_debug_stdio.py tests/unit/test_cli_args.py tests/unit/test_interpreter_test_mode.py tests/unit/test_modules_phase1.py`;
shared: `uv run python -m tools.spec_runner`; native: the existing native-test runner
(`tests/native/prelude_local_binding_isolation.genia`). Python-host tests carry the
"Python internals/host tooling" docstring per AGENTS.md; portable observations go to
shared/native specs.

**Layers**

1. *Characterization (pass today; P2-A).* Pin before any flip: the four §9 collision
   rows; module read of an entry name (before/after `import`); contribution closure
   with entry-defined helper; entry-name `doc`/`help`/`meta` and module-own `doc`;
   metacircular base env visibility of an entry name; custom `stdout`/`stderr` sink
   routing for error/test output (which Env callers pass); debug hooks across
   entry/module/prelude frames; MCP pruned catalogue; `:env` module/entry listing.
2. *Failing P2 tests (red first, P2-B).* Use a plain two-Env fixture (`R=make_global_env`,
   `E=Env(R)` run the entry in `E`) which already fails today for the intended
   reason because `entry_scope()` returns R.
3. *Regression (must stay green).* CLI/REPL/debugger/modules/reflection/config/
   autoload/Flow/lifecycle/MCP suites; `spec_runner` 822/822 baseline.
4. *Shared conformance.* See below.

| ID | Behavior | Old behavior that must fail | Source files | Location | Cross-host | Expected red diagnostic |
|---|---|---|---|---|---|---|
| T1 | `main/1`→`main/0`, `argv` dispatch from E; module/R `main` never entry | `_resolve_program_result(_, E)` reads R (no `main`) → result printed, not dispatched | `interpreter.py:499` | `tests/unit/test_f2_p2_separated_entry.py` | shared CLI cases unchanged | `assert … == 'out'`, got `<function main/0>` |
| T2 | Native-test discovery scans E; `@test` in modules excluded; fixtures/`test` registrar `entry-only` in E | `discover_test_units(E)` scans R: `test(...)` registrar entries (list on R) are still found, `@test`-annotated entry functions are missed | `test_cli.py:87,102,180,322` | same | Python tooling only | annotated-test count mismatch (not `total=0`) |
| T3 | Serve discovery from E; annotations in modules inert | discovery reads R | `interpreter.py:549`, `server_*_binding.py` | same (loopback marker where sockets) | Python HTTP host | "no route/server declared" |
| T4 | REPL `:env` lists E's own bindings only (D3), session persists | lists R builtins | `interpreter.py:383` | update `test_repl_env_characterization.py` | colon command host-local | extra builtin names present |
| T5 | Debugger `locals`=frame, `globals`=declaring unit (E or M); prelude frame resolves | globals = R for module frames | `debug_controller.py:244,290,215` | `test_debug_stdio.py` additions | host protocol | module frame globals list builtins |
| T6 | `gen_function_docs.collect`/`lint_doc` use `runtime_scope()`. These tools build fresh roots (entry==root default), so a wrong-accessor red needs an explicitly separated E in the test; otherwise T6 is guard-only (§J-6) | red only with an explicit E | `tools/*` | `tests/unit/test_scope_consumers_*.py` | tooling | "autoloads empty" |
| T7 | Module M→R only; entry name read works **with one stderr warning** per (module,name); strict switch fails; contribution clause reported against declaring module; import order independent | module reads E silently / no warning, no switch | `environment.py:get`, new fallback path | `tests/unit/test_f2_p2_module_fallback.py` + native cases | Python-only fallback; shared §5 cases are P3 | `warning absent` / `NameError` mismatch |
| T8 | D1 reflection: entry→E then R; module→M then R; prelude→R; `map(doc,names)` binds E; transferred callable keeps scope; user-rebound `doc` unchanged | `doc("zzz")` in E misses entry name after flip | `builtins.py` reflection, `evaluator.py` identifier paths | `test_f2_p1_reflection_scope.py` + new | `doc_help` shared cases unchanged; C++ unsupported | `none('missing-doc')` instead of metadata |
| T9 | MCP: R pruned before E; `mcp_worker.py:241` runs source in **E, not R**; no installs after `prune_environment` (`:232`); E empty; denied names undefined; catalogue/help pruned; allowed run unchanged. Limits to state, not overclaim: `prune_environment` never prunes `internal_values`, and allowed autoloads can re-add unlisted helper names into R (only static `policy_violation` covers that) | prune only an empty E / ordering regression | `mcp_worker_profile.py`, `mcp_worker.py` | `test_r28_mcp_*` + new unit | none | denied name resolves |
| T10 | Four collision rows preserved (definition vs unloaded prelude name; extend loaded group; value rebinding of R name; unloaded-prelude value) | child-E shadowing/hiding (probe) | `environment.py:define_function`, `evaluator.py:1503` | `test_f2_p2_collisions.py` | portable P3 shadowing matrix deferred | `ArityError` on `rows/1`; `first` resolves to entry in prelude |
| T11 | Sink/diagnostic routing: custom stdout/stderr via R, test/err output ordering | `env.values.get("stderr")` on E → `sys.stderr` fallback | `interpreter.py:336`, `test_cli.py:283,292` | same | host IO | text on process stderr, not sink |
| T12 | Host injection routing by class; unclassified rejected | installed in same Env | `environment.py:set_host*` | extend `test_scope_accessors_p1_b.py` | host policy | value found in wrong Env |
| T13 | Debug state ownership (R): hooks reach HOF callbacks (`builtins.py:535,886,4217…`), modules (`environment.py:368`) and autoload frames | hooks on E only; R no-op | `interpreter.py:200-217` | new unit | host | hooks absent in prelude frame |
| T14 | Metacircular `eval` base env visibility per §J-4 | n/a (decision) | `builtins.py:394` | native + unit | `eval` shared cases unchanged | NameError / unexpected value |
| T15 | Prelude cannot write E; autoload defines only into R | n/a post-flip | `environment.py:try_autoload` | native `prelude_local_binding_isolation.genia` run under separated mode | portable | entry binding changed |
| T16 | R10 protected sentinels: no leak via `:env`, debugger globals, warnings, reflection | n/a | configuration/lifecycle | `test_declassification.py` patterns | Python | sentinel in output |
| T17 | Wrong-accessor matrix: every consumer in §C has one test that fails if given the other of `runtime_scope()`/`entry_scope()`/`unit_scope()` | stub-based (#1221) | all | `tests/unit/test_f2_p2_wrong_accessor.py` | n/a | named boundary mismatch |

Shared-spec decision: P2 introduces **no new module-isolation expectation**, because
the fallback keeps module reads working. Contract §12 makes §7.1 (D1) portable, so
D1 evaluation-scope cases (entry/module/prelude/indirect/transferred) are a portable
obligation to express as shared specs under `doc_help` + `multi_file_eval`, alongside
other observations invariant across P1→P2→P3 (declaring-module closure with a
module-defined helper, prelude non-write). `NameError`/shadowing cases
are P3 shared work (gate P2→P3, §11.4.3). Capability vocabulary stays
`multi_file_eval`/`doc_help`; no new capability.

Host test: contract §12 states C++ rejects `import`, declares `multi_file_eval`
unsupported, and has a single environment. This repository does not itself state
`doc_help` is unsupported in C++ (the P1-H record says C++ parity was not run);
verify against `spec/manifest.json`/the R16 runner in P2-F rather than assume. **Not
re-verified against `genia-cpp` HEAD in this pre-flight** (outside repository scope);
P2-F must re-run `tools.spec_runner` to show no change in supported/unsupported
classification. No C++ change or host-gap entry is required by P2.

## F. Slice plan

Reuse #1067 (parent), #1220, #1221. Open only the two issues the contract already
requires: a P2 tracking issue (scope lock + checklist below) and the §11.5
fallback-removal issue. Slices are PRs checked off in the P2 issue, not new issues.

| Slice | Purpose / deliverable | Depends | Files | Invariants | Red tests | Gate / evidence | Parallel |
|---|---|---|---|---|---|---|---|
| **P2-0** | Contract clarification (docs only): rulings in §J; names the construction helper/registration API, fallback registry, strict-switch spelling, deadline, #1220 reclassification, defined completion | this pre-flight | `docs/design/f2-…contract.md` (amend), P2 + fallback issues | no behavior | none | Maintainer approval recorded on #1067 | ‖ P2-A |
| **P2-A** | Characterization tests (green today) for §E layer 1 | — | `tests/unit/*`, `tests/native/*` | no source change | none (pass) | all pin current behavior | ‖ P2-0 |
| **P2-B** | Failing separated-scope tests T1-T5, T7-T13, T15-T17 | P2-0, P2-A | `tests/unit/test_f2_p2_*.py` | no source change | all, red for intended reason | red SHA recorded | after 0/A |
| **P2-C** | Topology: construction helper + 13 sites, `entry_scope`/`runtime_scope` remap, `set_host` routing, write-through rule, `run_source` debug ownership | P2-B | `environment.py`, `interpreter.py`, `test_cli.py`, `hosts/python/*` | prelude closes over R; M child of R; collisions unchanged | T1-T3, T10-T13 green | sequential (owns `environment.py`) | no |
| **P2-D** | Consumer flip + reflection: REPL/debugger D3, D1 activation, runtime sink reads, `.root()` removal in `builtins.py` (#1220) | P2-C | `builtins.py`, `evaluator.py`, `callable.py`, `interpreter.py`, `debug_controller.py` | D1; entry compat | T4, T5, T8, T14 | #1220 evidence | ‖ P2-E (serialize `interpreter.py` hunks) |
| **P2-E** | Fallback: `Env.get` miss path, dedupe, warning text, strict switch, registry/marker; repository-program manifest and deadline check only if P2-0 keeps them in scope (P1 design §7 proposal, beyond contract §11 minimum) | P2-C and P2-D's `environment.py` hunks (serialize) | `environment.py`, new small module, CI config | reads only; no values/paths | T7 | strict CI zero events | after P2-D `environment.py` hunks; otherwise ‖ |
| **P2-F** | Integration: real separated coverage of every boundary (#1221), MCP T9, both full partitions, `spec_runner`, doc tooling | P2-D, P2-E | tests | — | T9, T17 | **#1221 gate**; full green | no |
| **P2-G** | Docs + audit + distillation: STATE (net-small), RULES, REPL README, README, host-interop, cheatsheet only if example changes, semantic facts, MCP profile impact answer, composability-matrix test | P2-F | docs | STATE ≤43,000 words | doc-sync tests | skeptical audit | no |

P2 is **not complete** until #1220 and #1221 each carry linked verification (or an
approved reclassification) in #1067; code merge alone does not close P2.

## G. Deferred audit findings — state and required fixes

**#1220 (open).** `builtins.py:3340,3378` read `env.root().autoloads` inside
`make_global_env`, where `env` is R itself. Under the approved graph (R is the
parentless root; E and M are children), `root()` and `runtime_scope()` coincide for
every Env, so the migration is correct and **behavior-neutral**; a test cannot go red
on the *accessor choice* unless some Env's `runtime_scope()` differs from `root()`,
which the approved topology never produces. Wrong choices *are* testable once E exists:
using `entry_scope()`/`unit_scope()` for the catalogue sees an empty one. P2 must therefore (i) replace both sites
with `runtime_scope()`; (ii) add behavioral tests with E≠R proving the help overview
and families are built from R's catalogue (entry-defined names never appear;
MCP-pruned R shows the pruned catalogue; help output unchanged); (iii) add a source
guard (as P1-E did for raw host injection) that fails on `.root()` calls outside
`environment.py` and on `.autoloads` reads through anything but `runtime_scope()`,
which **does** fail against the current code (`builtins.py:3340,3378`). Criterion 2 of #1220
("fail against old direct-root implementation") is met only through (iii), plus
entry/unit-misuse tests for (ii); recorded as
reclassification request in §J-5. Do not close on (i) alone.

**#1221 (open).** Stub tests (`test_scope_consumers_p1_g.py`, `test_inspection_consumers_p1_d.py`,
P1-C) prove accessor *intent* only. P2-B/F must supply T1-T5, T9, T11, T17 against
real `R`/`E`/`M` Envs, including a runtime/entry collision, forbidden cross-scope
visibility, and a wrong-accessor variant per boundary. Keep the P1 stubs as
characterization. Evidence to link on #1067: test names, red SHA, green SHA,
full-partition results.

## H. Documentation impact

During this pre-flight: **only this record** is added (`.genia/process/`, not `docs/`).
No STATE/RULES/README/contract/spec edits; P1 "not implemented" statements stay true.
When P2 lands, same-change updates (AGENTS non-negotiable rule): `GENIA_STATE.md`
(scope model, host classes, consumer contexts, fallback only under the single
`TEMPORARY COMPATIBILITY FALLBACK` marker), `GENIA_RULES.md` §8.2/§8.3,
`GENIA_REPL_README.md` (`:env`, labeled `PYTHON REFERENCE HOST`), `README.md` if a
module-scope statement is user visible, R20 contract §2.2 cross-reference,
`docs/host-interop/*`, `docs/contract/semantic_facts.json` guarded facts and
`tests/doc/test_semantic_doc_sync.py`, MCP language-profile impact question
(answer recorded; contract defers a profile fact to P3), composability-matrix test
(`tests/doc/test_composability_matrix_sync.py` if reflection family text changes),
generated function docs only if public `@doc` changes. STATE margin is 135 words.

## I. Independent review

Read-only reviewer (separate agent, no edits) challenged the first draft against the
code. Findings and disposition:

| # | Finding | Disposition |
|---|---|---|
| H1 | Write-through rule incomplete (unregistered prelude helpers; contradiction with §9.1 row 4; order-dependence; `IrOpenFuncDef`) | Verified (`map_acc` unregistered). Added to §C, risk 1, §J-1; contract conflict stated |
| H2 | Debug-state consumers missing | Added to §C and T13 |
| H3 | Native-test list read/write on different Envs (`test_cli.py:322` vs `:87`) | Verified; added to §C and T2 |
| H4 | T6/T17 impossible under entry==root default | T6 reworded (explicit E or guard-only) |
| M5 | #1220 claim overstated | §G reworded; guard scope widened to `.autoloads`; tests-`.root()` claim corrected |
| M6 | T2 red diagnostic wrong | Corrected |
| M7 | MCP gaps (E vs R execution, `internal_values`, allowed autoloads) | T9 extended with explicit limits |
| M8 | C++ `doc_help` attribution; D1 portable | Corrected in §E |
| L9 | Citation errors | Corrected where verified |
| L10 | P2-E scope/parallelism; §J-4 restrict is a behavior change | Serialized `environment.py`; labeled |

No finding was rejected. The reviewer judged the probe claims plausible and confirmed
the 13 construction sites. No premature P3 work was found.

## J. Open decisions and verdict

Rulings needed in P2-0 (none may be assumed):

1. **Write-through rule for the §9.1 P2 column.** A child E does not preserve P2
   behavior (probe). Candidate (recommended): during P2 an entry definition/assignment
   whose name is bound in R **or autoload-registered** writes through to R exactly as
   today; all other names go to E; removed in P3, when D2/D2b shadowing replaces it.
   Gaps found in review that P2-0 must close: (a) prelude files define top-level helpers
with no autoload registration (`map_acc`, `filter_acc`, …), so the rule must be keyed
on a static manifest of every top-level name in every autoload file, or accept a
visible change; (b) contract §9.1 row 4 ("prelude write into an entry binding: removed")
cannot hold for R-named entry bindings that live in R under write-through — check the
16 §2.1 names against R/autoload; (c) routing is load-order dependent and must also
cover `IrOpenFuncDef`. Consequences to rule on: such names are absent from E's `:env`/test discovery;
   module/prelude see them (today's behavior). Alternative: amend §9.1 to start shadowing
   at P2 (rejected here: contradicts the approved table).
2. **Reflection in P2.** Activate D1 evaluation-bound reflective values in P2
   (P1 design recommendation; not recorded as ruled), or a documented interim.
3. **Fallback mechanics:** registry location (contract notes `spec/known_host_gaps.json`
   is C++-scoped), strict-switch spelling, deadline unit (releases vs the P1 design's
   hybrid 60-day proposal), and who owns the removal issue. Contract §14 open question 4
   and P1 design §7 are unratified in #1067.
4. **Metacircular base env** visibility of E names (§C, T14). Restricting it is a P2 behavior change (hides E names from `eval`) and must be labeled so.
5. **#1220 reclassification** (accessor test infeasible; guard-based criterion).
6. **Construction API:** name/shape of the single helper that registers E on R
   (default: caller-created roots keep entry==root, per P1 design §2), and whether a
   suite-wide separated mode is required beyond host entry points.
7. D2b is **not** a P2 blocker; only P3 depends on it.

**Verdict: CONDITIONAL GO.** Prerequisites: P2-0 rulings 1-6 recorded on #1067;
P2 tracking and fallback-removal issues opened; P2-A characterization merged.
Recommended first slice: **P2-0 ‖ P2-A** (both behavior-neutral). No P2 failing
test or implementation should start before those, and nothing here authorizes P3.
