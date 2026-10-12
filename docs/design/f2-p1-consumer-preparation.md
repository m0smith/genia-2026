# F2 P1 — Module/entry scope consumer preparation

Status: **PROPOSED DESIGN — review required; no implementation authorization.**
Tracking: [issue #1067](https://github.com/m0smith/genia-2026/issues/1067).
[P0](f2-module-entry-scope-isolation-contract.md) defines the proposed future
boundary. `GENIA_STATE.md` remains final authority for implemented behavior.
This design neither amends P0 nor claims its behavior is available.

## 1. Baseline and scope

Inspected Python baseline: `b22027bedb0f233222218b4a8772a0a242fe32d5`, equal to
fetched `origin/main` on 2026-10-12. P0 merged in #1204 at `7dc781d`; the
independent prelude-local repair merged in #1206 at `b22027b`.
`tests/native/prelude_local_binding_isolation.genia` protects that repair.
P0's historical write-defect description is therefore not current behavior.
F1 is complete; F3–F5 stay paused. No P1 design PR was found in the GitHub
search or latest issue comments before this branch was created.

**LANGUAGE CONTRACT:** P1 adds no syntax, dispatch rule, reflective authority,
assignment rule, Core IR node or module-isolation behavior. Future behavior
remains governed by P0 and the decisions identified below.

**PYTHON REFERENCE HOST:** P1 prepares host consumers while runtime R and entry
E are still the same Env. Modules remain children of that root. New accessors
must initially select exactly the environments consumers use today. A method
called “unit scope” cannot be substituted for debugger root access yet:
module frames currently expose root globals, not their module's globals.

The roadmap schedules this unnumbered R20 follow-up after R28 and before R29.
This is correctness infrastructure for ordinary pipeline composition, not a
new release or extension of R28. The earlier survey's test counts are issue
evidence, not fresh validation of this design or proof about third-party code.

## 2. Smallest scope-access model

Retain `Env.root()` as the structural root operation. Introduce explicit
host accessors with the following proposed responsibilities; names here are
design candidates, not existing APIs:

| Accessor | Intended responsibility | P1 mapping | Later mapping |
|---|---|---|---|
| `runtime_scope()` | Autoloads, module cache, trusted internal bindings, debug runtime state | `root()` | R |
| `entry_scope()` | The execution's entry top level, for host consumers only | root for executions created by the host | E |
| `unit_scope()` | Declaring top level of the lexical frame | existing module Env for M; root for entry/prelude | M, E or R |
| `inspection_globals_scope()` | Preserve debugger's phase-dependent view | `root()` for every frame | `unit_scope()` when D3 is activated |

Use an inherited top-level-unit reference on Env, set explicitly by module
construction, and an execution entry reference owned by the runtime root.
Ordinary block/function frames inherit the declaring-unit reference from their
lexical parent, never from the caller. Module construction must set its own
reference before evaluation; prelude evaluation identifies R. Do not infer unit
ownership from filenames or `module_id`: an inherited canonical identity is
useful for provenance but does not identify the top-level Env object.

P1 can register the existing root as entry without allocating a child. Keep
`make_global_env()` and `run_source(source, env)` return/caller behavior intact:
the latter also evaluates module and prelude code, so it must not unconditionally
register each supplied environment as the execution's entry. Host execution
construction is the registration boundary. Standalone Env-based unit tests
need a documented root default for entry access; no caller-created Env is
silently replaced. Future P2 entry construction is a separate gate.

Prefer references on the existing Env over a new execution manager, mutable
global “current scope”, or a mirrored dictionary. Accessors return the owning
Env; bindings and metadata stay paired there. Keep lexical reads/assignment
unchanged in P1. Entry access is not a language builtin and must not be used
inside module lookup, reflection or closure resolution as an authority bypass.

`inspection_globals_scope()` is a host migration seam, not a user mode or a
permanent compatibility option. P2 changes its mapping once, after baseline
regressions exist. It can then become a direct unit-access alias or be removed.
This explicitly reconciles P0 §10's consumer preparation with P0 §8's eventual
unit view: adopting the eventual module-debugger view in P1 would change output.

## 3. Consumer inventory

Locations below refer to baseline function names; line numbers may move.
“Same” means P1 can preserve today's observations with the stated mapping.
“Deferred” means activating the desired behavior must wait for P2/P3.

| Consumer and source | Current root dependency/behavior | Eventual scope | Smallest P1 adaptation | Regression evidence needed | P1 behavior / P2 dependency | Portability |
|---|---|---|---|---|---|---|
| `interpreter.py`: `main`, `repl`, `run_debug_stdio`, `_run_serve_file` | Each builds one global Env and evaluates entry source there; serve bypasses `run_source` | E for entry evaluation | Register existing root as entry; pass explicit entry handle through orchestration | File/command/pipe/test/serve/debug/REPL mode selection; repeated submissions | Same; P2 alone allocates E | Python wiring; existing shared CLI/REPL contracts remain |
| `interpreter.py`: `run_source` | Evaluates in supplied Env; writes debug settings and temporarily enables trusted access | Supplied lexical scope; execution state on R | Preserve evaluation target; distinguish runtime debug ownership without widening trusted access | Module/autoload execution, repeated runs, restoration after exception, debug autoload stop | Same; P2 callers supply E/M/R | No new IR or public return shape |
| `interpreter.py`: `_resolve_program_result` | Reads `env.values['main']`; prefers ordinary `main/1` to `/0`; gets `argv` lexically | Own E binding for main; runtime-public argv via E lookup | Read entry's own values; keep `.get(1)`/`.get(0)` selection | `test_cli_args.py` main/argv cases, absent main, runtime/module main exclusion later | Same; P2 main must not come from R/M | Shared CLI under `cli_file_mode`/`cli_command_mode`; no separate main capability |
| `test_cli.py`: `discover_annotated_test_units`, `discover_test_units` | Scans supplied Env own values/metadata; registrations stored in `_native_test_units` there | E own bindings and registrar list | Access E once for values, metadata and registrations together | Legacy/annotated order, duplicate names, invalid metadata, parameterized/nonfunction discovery errors, imported tests excluded | Same; P2 list and fixtures move together | Python native-test tooling; no C++ test-mode claim |
| `test_cli.py`: `make_test_env` | Fixture loop and `test` registrar installed in root | E, entry-only | Classified host-install API records class but writes same Env in P1 | Every supplied fixture named/classified; registrar identity/order; fixture collision behavior | Same; P2 moves entry-only injections, module fixture access requires explicit arguments | Host injection policy, no new language API |
| `interpreter.py`: `repl` `:env` | Sorted own root values, including builtins and autoloaded bindings | E own values | Read entry accessor, still root; keep rendering/order | Pin user and runtime bindings, autoload appearance, persistent session, scripted input/no prompts | Same; P2 adopts D3 and updates expectations/docs | Colon command is Python host-local |
| `debug_controller.py`: `_variables`, `ensure_root_frame` | Globals always `frame.env.root().values`; locals own frame; root frame also forced to root | Globals declaring unit; root logical frame E | Use inspection compatibility accessor for globals and explicit entry for root frame; retain locals | Existing entry-frame test plus module frame, module lambda/open contribution, nested block, prelude/autoload; no extra values exposed | Same; P2 switches globals to unit after tests pin current module-root view | Debug protocol is host tooling |
| `builtins.py`: `doc_fn`, `meta_fn`, `help_fn` | Closures capture root Env; string lookup and metadata there; help output uses captured stdout sink | Lexical evaluation scope per D1 | Factor scope-parameterized reflection helpers, invoke with same root; keep callable object/metadata behavior | Root lookup/missing names/autoload/metadata, help target callable and help overview, indirect calls | Same preparation; D1 binding activation deferred | Shared `doc_help`; future C++ unsupported |
| `environment.py`: `register_autoload`, `try_autoload`, `get`; `builtins.py` help catalogue | Tables/file sets on root; autoload evaluates into root and closes over root | R | Replace runtime ownership references only; preserve loading order and deduplication | Bundled/absolute path loads, cycle/error cleanup, plain-value lookup, arity retry, prelude local guard | Same; P2 must never evaluate prelude into E | Runtime owner is host detail; prelude observations portable where supported |
| `environment.py`: `load_module`, `resolve_module_source` | Root cache; modules `Env(root, rebind_parent=False)`; own values become exports | Cache R; evaluation M under R | Identify runtime owner and register module unit; retain parent and lookup today | Alias cache identity, sibling/nested imports, cycles, exports, requester-relative resolution, packaged trust | Same; P2 root stops containing entry definitions | Existing `multi_file_eval`; C++ unsupported |
| `environment.py`: `get`, `get_metadata`, `assign`, `find_assign_target`, `define_function`, `merge_binding_metadata` | Reads/metadata traverse parents; assignment traverses until boundary; definitions modify own group | Lexical chain; later E/M/R boundaries | Leave algorithms unchanged; document accessor ownership separately | Assignment/closure capture, metadata precedence, duplicate arity, nonassignable names | Same; P2 compatibility writes and P3 shadowing need separate designs | Language behavior; future shared evidence required |
| `evaluator.py`: `eval`, `eval_call`, `eval_pipeline_stage`, `invoke_callable`, annotation and open/use/extend evaluation | Several direct `env.get` paths and arity-autoload callback; definitions own Env; closures capture it | Lexical scope; unit for declaration ownership | No new shadow/reflective lookup rule in P1; identify all identifier paths for later hook | Direct/indirect/pipeline/tail calls, annotations, open closures/contributions, Outcome and Flow adapters | Same; P2 D1 hook must cover fast paths as well as plain `IrVar` | Existing IR unchanged |
| `callable.py`: `eval_with_tco`, `_closure_lookup`, `_callable_explicitly_handles_none/some`, `invoke_callable` | Fresh frames under captured closure; awareness helper manually walks `values`, without autoload; group dispatch/autoload differs from host direct call | Declaring lexical chain | Inherit unit reference in new frames; leave awareness and selection untouched | Mutual TCO, per-stratum Outcome behavior, helper delegation, lazy callback scope | Same; P3 overlay lookup must also address awareness, not just calls | Shared open/Outcome/TCO boundaries; C++ gaps retained |
| `server_route_binding.py`, `server_config_binding.py`, `server_cors_binding.py`: `discover_entry_file_*`; interpreter serve orchestration | Entry IR restricts declarations; supplied env resolves value/metadata; handler/transport references captured | E discovery; lexical handler closures; R capabilities | Pass entry accessor with existing entry IR; keep source identity and discovery order | Route/server/CORS validation, imported annotations inert, main not dispatched, outgoing annotations/send call remains explicit | Same; P2 must not scan R/M or auto-execute annotations | Python HTTP host surface; C++ unsupported |
| `interpreter.py`: `_emit_error`, `_emit_result`; `test_cli.py`: `_write_stdout`, `_write_stderr` | Error/test reporting uses own `env.values` sinks; ordinary result uses lexical get | Host diagnostic sink R; result retains existing lexical sink behavior unless separately gated | Explicit runtime accessor for direct sink reads, keep captured sinks and lexical result reads | Custom stdout/stderr, rebound/invalid sink, broken pipe, native report ordering, debug output events | Same; P2 direct E dictionary reads would miss sinks | Host IO; no new sink authority |
| `builtins.py`: `make_global_env` and helpers; `environment.py`: `set_internal` | Host bindings/capability closures installed in root; trusted internals guarded separately | R for public runtime; E for per-program injection | Record visibility at host installation, without changing assignable/trust/metadata or lazy acquisition | Enumeration/class check, optional constructor paths, no acquisition/import activation, protected carrier/sink rules | Same; P2 placement consumes classification | R10 authority unchanged; placement is not privilege minting |
| `host_bridge.py`: `_build_python_host_module`; Env host-module branch | Host module built using root argument/cache, not entry; no ordinary Genia module Env | R host capability ownership | Keep runtime argument explicit; no reclassification of host modules as E | Allowlist/handle rejection/normalization, host-module cache | Same; no new fallback in host bridge | Python-only allowlisted bridge |
| `hosts/python/mcp_worker_profile.py`: `prune_environment`; `hosts/python/mcp_worker.py` execution | Removes disallowed own bindings and root autoloads before evaluation | Filter R before E construction | Use runtime accessor for both tables; retain allowlist policy and metadata removal | MCP denied names/autoloads/imports, resource/output limits, fresh worker environment | Same; P2 must not prune only empty E | Defense in depth, not sandbox; no MCP surface change |
| `tools/gen_function_docs.py`: `collect`; `tools/lint_doc.py`: public/autoload collection | Fresh global root autoload catalogue, lookup of prelude metadata | R | Runtime accessor, never entry accessor | Generator `--check`, linter coverage, host builtin registry | Same; no user-binding catalogue | Tooling only |
| `hosts/python/exec_model_fixture.py`, `exec_r12_grounded_fixture.py`, `exec_r25_concurrency_fixture.py` | Explicit fixture/provider/authority/helper injection via `env.set` | Declared per adapter, see §4 | Classify each installation, retain actual root placement in P1 | Existing shared fixture executions; protected sentinel non-leakage; module callback use | Same; P2 class determines placement | Test adapters, not public capabilities |
| Python harnesses: `tests/unit/test_modules_phase1.py` | Direct alias/entry `env.values` reads; root cache identity; injected module counter | E for program values, R for cache/counter capability | Change only entry inspections to entry accessor; classify counter runtime-public | Alias cache assertions, immutable exports, module assignment boundary | Same; P2 raw entry reads otherwise fail | Python internals, shared module twins where observable |
| Other Python harnesses (below) | Mixed runtime presence/absence assertions and injected program fixtures | Depends on assertion purpose | Keep runtime assertions on R; program inspections on E; injection explicit | Existing model/retrieval, Seq, MCP policy and authority tests | Same; no blanket search/replace | Host internals plus existing native/shared evidence |

Additional harness files found with direct `env.values`/`root()` inspection:
`test_r11_model_fixture.py`, `test_r12_embedding_fixture.py`,
`test_r12_indexing_fixture.py`, `test_r12_retrieval_fixture.py`,
`test_r12_reranking_fixture.py`, `test_flow_adjacent_186.py`,
`test_seq_as_seq_boundary_306.py`, `test_host_builtin_docs.py`,
`test_execution_process_genia_surface_absent.py`, `test_r28_mcp_launcher.py`,
`test_r28_mcp_run_worker.py`, and `test_r28_mcp_conformance_security.py`, all under
`tests/unit/`. Presence/absence checks about builtins/autoloads remain runtime
checks. A source-under-test inspection becomes an entry check. Dynamic host
fixtures throughout IO/configuration/model/retrieval/lifecycle tests need
classification, even when they do not directly inspect dictionaries.

Inventory discovery used repository searches for `.root(`, `env.values`,
`env.set(`, `set_internal`, `make_global_env`, debug globals and direct name
resolution, followed by reading the listed consumers. This is source inspection,
not a fresh dynamic free-name survey. Later P1 review must repeat the searches
against its baseline and account for new consumers individually.

## 4. Host injection classification

P1 needs a host-only installation helper accepting an explicit visibility
argument. It records class and installs in the same legacy environment. Do not
change `Env.set` into a classification requirement: evaluator definitions,
parameters and lexical assignment also use it and are not host injection.
Do not use underscore spelling to decide visibility or trust.

| Injection point | Names/capability | Proposed class and rationale |
|---|---|---|
| `builtins.make_global_env` ordinary registration | 241 fresh root names: 92 without leading underscore, 149 with it | runtime-public; this denotes placement, not public API stability |
| `environment.set_internal` registration | `_evolve`, `_as_seq`, `_seq_transform`, `_ensure_seq_compatible`, `_seq_reduce`, `_scan`, `_each`, `_run`, `_collect` | runtime-public ownership, with current trusted-code access restriction retained |
| `register_autoload` calls in builtins | 234 `(name, arity)` registrations | runtime-public; prelude files still evaluated only in R |
| Sink/argument installation | `stdout`, `stderr`, `argv` and captured output writer | runtime-public; preserve constructor-provided sink identity |
| Input callbacks | `stdin`, `stdin_keys`, `input`; constructor `stdin_data`, `stdin_provider`, `stdin_keys_provider` | runtime-public; providers are captured Python callbacks, not additional Genia bindings |
| Configuration callbacks | `environment_snapshot_provider`, `dotenv_snapshot_provider` captured by provider constructors | runtime-public capability closure; no ambient acquisition added |
| Debug constructor state | `debug_hooks`, `debug_mode` fields, output handler | runtime state, not lexical bindings; record separately rather than inventing two names |
| `test_cli.make_test_env` fixture loop | Each actual supplied fixture name | entry-only; preserve fixture collision/order behavior until P2 |
| `test_cli.make_test_env` registrar/list | `test`, `_native_test_units` host attribute | entry-only binding and entry-owned list; no exported registrar added |
| `exec_model_fixture.py` | `model_provider_fixture`, `model_credential_fixture`, `model_authority_fixture` | entry-only: program consumes these explicitly; module must receive arguments |
| `exec_r12_grounded_fixture.py` | Five provider fixture names plus purpose-derived credential/authority fixture names | entry-only: grounded module receives supplied model call/values explicitly |
| `exec_r25_concurrency_fixture.py` | `_r25_await_idle` | entry-only: explicit test synchronization, not a production builtin |
| `test_modules_phase1.py` injected `counter` | Callback intentionally used in imported module | runtime-public: explicit test-host capability decision, not accidental fixture visibility |
| Other Python harness injection loops/calls | Per-run paths, records, protected credentials, authorities and provider objects | entry-only by intended program use; any module-visible exception must be named and justified individually |

Counts above were re-enumerated by constructing a fresh `make_global_env([])`
without evaluating a program. That read-only probe matched P0's counts. P1's
TEST/implementation slices must commit the sorted name/arity enumeration and
classification evidence; this design does not freeze counts as a runtime rule.
Check set equality between installed names and classified names, trusted internal
names and their classifications, and autoload keys and their classifications.
Exercise optional constructor paths and dynamic adapter/fixture installation.
An expected-name snapshot must require review when a name appears; a blanket
“every current dictionary key is public” assertion would miss unreviewed additions.
The helper rejects missing/invalid class on host installation. Preserve raw
`Env.set` for language bindings, but require each maintained host installation
site to use the helper; source review/guard must catch a new raw host injection.

Classification checks belong to P1. Moving bindings belongs to P2. Installing
a protected credential or authority in R does not create declassification power
or weaken R10 sinks. Provider construction/acquisition remains explicit.

## 5. D2b: shape shadowing analysis

Recommendation: **per-shape visibility for ordinary function groups**, with an
explicit ordinary-storage refinement reviewed before P3. Do not apply group
merging to arbitrary callable values, open interfaces or linked views.

Current mechanics matter:

- `Env.define_function` checks only own `values`; it creates or modifies an
  ordinary group there. It does not merge with a parent group.
- `GeniaFunctionGroup.functions` is keyed by integer required arity, not
  `(fixed/varargs, n)`. `add_clause` rejects two entries with the same required
  arity even if one is fixed and the other has rest parameters.
- Direct group calls and `invoke_callable` prefer an exact dictionary entry,
  otherwise the sole eligible rest entry. Exact lookup can itself return a
  rest entry with that minimum. Distinct eligible rest minima are ambiguous;
  there is no largest-minimum preference.
- Identifier lookup returns one first-class value before argument dispatch.
  A call-site-only fallback would make `f(args)` differ from `g = f; g(args)`.
  Arity-autoload retry exists for named calls, not arbitrary aliases.
- Open dispatch has true fixed/varargs shapes, ordered strata, provenance,
  identity and explicit linking. It is not an ordinary group dictionary.

The following are **design scenarios, not runnable examples or new implemented
claims**. Results describe the candidate P3 policies; current behavior is noted.

| Collision/scenario | Current shared root | Per-name hiding in P3 | Per-shape ordinary view in P3 | Compatibility consequence |
|---|---|---|---|---|
| E `rows/0`, R `rows/1` | New arity merges into runtime group | `/1` disappears to entry | Both visible to entry, R `/1` unchanged | Per-shape retains the valid cross-arity call |
| E fixed `f/1`, R fixed `f/1` | Duplicate if R group loaded; autoload timing can defer error | E replaces name | E `/1` replaces R `/1` for entry | Intentional P3 collision correction, needs announcement |
| E fixed `/1`, R fixed `/2` | Both can coexist | `/2` lost | Both available | No regression for distinct arities |
| E rest minimum 1, R rest minimum 2 | Coexist; call arity ≥2 ambiguous | Only E eligible | Both eligible; keep ambiguity | No scope-based/largest-minimum preference |
| E fixed `/2`, R rest minimum 1 | Exact `/2` wins; other eligible calls use rest | Runtime rest lost | Exact wins; rest remains for other arities | Preserve fixed-first behavior |
| E fixed `/1`, R rest minimum 1 (or converse) | Same integer slot rejected | E replaces whole name | True shape union would introduce a previously rejected coexistence | Requires explicit refinement; cannot silently use dictionary update |
| E value, lambda, Template, map or linked view named `f` | Assignment replaces whole binding | Whole binding shadowed | Whole binding shadowed | Arity merging is not a general callable composition operation |
| E ordinary group, R non-group callable/value | Definition currently rejects loaded non-group | New E group hides R | New E group hides R; no inherited shapes | P3 D2 behavior, not implicit callable conversion |
| E ordinary name, R open interface/view | Ordinary definition currently rejects loaded interface/view | E hides R | E hides R as whole binding, if D2 approves; no clause union | R20 identity/contribution ownership stays intact |
| Same E group redeclared at same required arity | Duplicate | Duplicate | Duplicate | No widening of ordinary local clauses |
| E shadows a not-yet-loaded prelude name | Load can later collide, including other names in same file | E blocks runtime name | R loads separately; E shapes overlay R shapes | Autoload order/file side effects need explicit evidence |

The narrower alternative is **per required-arity slot**, matching today's
ordinary group storage. Entry slot `n` would replace runtime slot `n` whether
fixed or rest. It avoids changing the storage model, but can hide an inherited
varargs tail when E defines a fixed entry at the same minimum. That is a real
difference from P0's “same shape” language and needs a deliberate amendment.
Per-name hiding is simpler but loses the `rows` case; reject it unless the
maintainer deliberately accepts that break.

Preferred refinement for review: retain same-required-arity rejection *within*
each ordinary group, and permit distinct fixed/rest shapes from E and R in the
entry-visible view, with true fixed-first selection and existing rest ambiguity.
This permits a cross-scope combination the shared-root model rejects today;
it is an additional P3 compatibility decision, not just an implementation detail.
If that widening is rejected, approve the slot alternative explicitly instead.
P1 does neither and therefore does not depend technically on this refinement.
The latest issue closeout still requires a maintainer ruling before P1 execution.

A future view must preserve source closures, Outcome-awareness selection,
TCO, named Flow adapters, indirect/higher-order invocation, rendering and
reflection, and runtime immutability. Avoid copying R clauses into E's mutable
declaration group. A stable entry-owned view over separate groups is a candidate,
but its identity, live additions during a REPL, metadata/docstring ownership and
lazy autoload discovery require a focused P3 design and shared evidence.
Recommend E-owned binding metadata when E exists, and unchanged metadata on
R's original value; do not synthesize annotation merges silently. Pure inherited
lookup must return the original R value. No view is implemented in P1.

## 6. Reflection mechanism

Recommendation: **evaluation-bound callable values using existing lexical Env
capture**, activated in P2 after behavior-preserving preparation in P1.

Factor current render/lookup logic into helpers accepting a lookup Env and
unchanged runtime catalogue/output dependencies. In P1 the existing builtin
closures call those helpers with the captured root. Do not wrap values or
switch module lookup context yet: module-own `doc` would immediately change
results even while E and R still coincide.

For P2, mark only the original runtime reflective targets as scope-bindable.
At identifier evaluation, resolve the lexical binding normally, then bind a
marked target to the actual evaluating Env. This is value-based marking, not
a special case for the strings `doc`, `meta`, `help`: a user rebinding one of
those names must keep its ordinary value. Already-bound callables must be
returned unchanged through aliases, parameters, maps, modules or higher-order
calls. Passing one between units is the explicit grant D1 already authorizes.

Cover `Evaluator.eval`'s `IrVar` path, direct `eval_call`, both pipeline name
paths, and autoload retries. They currently do not all use `eval(IrVar)`.
Prefer one internal identifier-resolution helper shared by those paths.
Do not put binding into ordinary `Env.get` used by host inspection or into
invocation: those are not necessarily identifier evaluation.

| Approach | Assessment |
|---|---|
| Bound callable capturing lexical Env | Matches D1 for direct, indirect, lazy/higher-order and cross-unit calls; existing invocation accepts Python callables; no Core IR change needed |
| Invocation context parameter/context variable | Identifies caller/invoker rather than evaluation scope; `map(doc, names)` and explicitly passed callable lose authority unless value also captures scope; larger plumbing without benefit |
| One reflection closure installed per unit | Captures top level, misses function/block lexical frames and passed-callable provenance; requires many bindings and changes export/injection surfaces |
| Source rewrite into lambdas or new IR node | Could encode capture but adds lowering/serialization obligations where ordinary runtime callable capture suffices; reject without demonstrated necessity and separate contract gate |

Cache by (lexical Env, original reflective target) to preserve repeated-read
callable identity in the same scope. Store cache with that Env rather than a
runtime cache strongly retaining every completed call frame. Existing closure
cycles remain subject to normal Python collection; a deliberately retained
bound callable legitimately retains its lexical frame. Stable same-scope
identity and different-scope identity need explicit P2 evidence against R18.
Transferred wrappers retain their exact object identity. A closure captures
the live environment, not a snapshot: later lexical rebinding is visible, as
with existing functions. It captures a function/block Env, not only unit Env.

Host direct retrieval through `env.get('doc')` remains a root-bound callable
unless the host explicitly requests a scope-bound value. Maintain current
metadata, arity/misuse diagnostics and absence-awareness markers through the
wrapper. `help()` still uses runtime catalogue and captured stdout; string
targets use bound lexical lookup. Callable-target help retains current rendering
and target ownership rules; do not add an annotation/identity model through
this refactor. Reflection never uses the module-to-entry fallback, including
metadata lookup. A wrapper explicitly supplied by entry code is the only such
authority path D1 allows.

No IR change is presently necessary: `IrVar` still means evaluate a lexical
name; an ordinary runtime callable carries its environment. A future host can
implement the same portable semantics with its own closure value. C++ currently
declares `doc_help` and `multi_file_eval` unsupported; this design claims no
cross-host implementation. If a later design cannot represent bound callable
capture without new IR, stop for a separate contract gate before tests/code.

## 7. Fallback removal policy

P0 §11.4 currently uses “the release following the release that ships P2”.
The follow-up has no numbered release, making that deadline ambiguous. No
fallback is implemented now and this design does not amend §11.4.

| Deadline | Strength | Failure mode |
|---|---|---|
| Calendar only | Enforceable even if releases stop | Date alone cannot prove strict-mode readiness; rushed removal or repeated extensions |
| Release only | Fits release acceptance | Unnumbered P2 and delayed releases can leave fallback indefinitely |
| Hybrid (recommended) | Objective evidence plus milestone and time bound | Requires explicit ownership, dated exposure start and a release gate |

Proposed amendment for maintainer approval before P2:

1. Preserve every P0 §11.4 evidence criterion. Record P1 completion, strict
   zero-event evidence for both full-suite partitions and repository-owned
   programs/modules/fixtures, shared/native isolation cases, one STATE marker,
   one removable code path, and explicit third-party uncertainty.
2. Name an owner and removal tracking issue when P2 is authorized. Record the
   UTC date warning-enabled P2 first becomes publicly available and compute a
   maximum **60-calendar-day** exposure window from that date. Sixty days is a
   proposed policy duration, not an existing promise or invented release date.
3. Require P3 removal before R29 implementation begins, consistent with the
   current follow-up scheduling, or by the end of that 60-day window, whichever
   comes first. If the milestone is too soon to provide meaningful exposure,
   review scheduling explicitly; do not waive evidence or claim a warning
   window occurred merely because code merged.
4. Strict-mode CI starts with P2. Add a host/process deadline check in P2's
   own TEST/implementation phases; it fails once the dated maximum expires.
   R29's intake references the removal issue as a blocker. The check must not
   alter runtime lookup based on today's date.
5. If readiness/exposure is insufficient at either limit, block progression
   and require an explicit recorded amendment naming owner, reason, remaining
   evidence and a new absolute deadline/milestone. No automatic extension,
   automatic unsafe deletion, or permanent public switch.

“Every repository-owned program” is not established by a passing pytest count:
P2 needs an execution manifest covering apps/examples and fixture-backed
programs with deterministic offline adapters where needed. Unexecuted paths
and programs requiring unavailable external services must be listed and
resolved, not silently called zero-event evidence. Static free-name review
supplements executions but does not establish dynamic-path absence.

Warn/count distinct (declaring module, name) pairs without values, paths or raw
host exceptions. Include contribution closures and nested frames, not just
module top-level evaluation. Reflective lookup, writes and exports never use
fallback. Registry placement and strict-switch spelling remain P2 design work;
do not force Python temporary compatibility into a C++-scoped gap schema.

## 8. Implementation decomposition and verification

These are proposed work slices, not new tickets or permission to execute them.
Each needs explicit phase authorization; TEST precedes implementation and the
implementation commit references its failing-test SHA. Characterization tests
pinning current output may pass initially; new accessor/classification API
tests must fail before their implementation.

| Slice | Deliverable | Dependencies | Focused verification |
|---|---|---|---|
| P1-A | Characterize REPL `:env` and entry/module debugger views; preserve current globals leakage in baseline assertions | Approved P1 test phase | Scripted REPL without prompts; entry/module/prelude/nested/contribution frames; globals vs locals |
| P1-B | Add runtime/entry/unit accessors, unit inheritance and inspection compatibility seam; register current root as entry | A evidence, approved design/TEST | Accessor ownership on root/module/function/block; no new child entry; metadata/bindings identity; reused Env |
| P1-C | Re-point CLI, native discovery/registrar state and serve orchestration | B | Existing CLI main/argv/mode tests, native discovery errors/order, imported annotations inert, server and outbound regressions |
| P1-D | Re-point REPL/debugger through behavior-preserving inspection accessors | A/B | Exact baseline observations, autoload stops, logical frame mapping and breakpoint/step behavior |
| P1-E | Classify builtin/internal/autoload/adapter/fixture host installations; commit enumeration and fail on unclassified injection | B for naming/placement API | Constructor variants, per-run fixtures, raw-host-injection guard, module counter, protected sentinel checks |
| P1-F | Factor reflection helpers with explicit lookup Env but root-bound existing callables; keep catalogue/IO on R | Reflection mechanism reviewed | Existing doc/meta/help and open annotation tests; indirect invocation and callable identity unchanged |
| P1-G | Update Python program inspections, runtime tooling and MCP runtime pruning; finish residual consumer search | B, coordinate E | Alias/export tests, generated-doc check/lint, MCP worker profile/security, fixture adapters |
| P1-H | Integrated regression and skeptical phase closeout | C–G | Both full partitions, targeted shared cases, documentary truth, no scope activation or changed diagnostics |

After B, C/D/F can run independently subject to shared-file ownership:
C and D both touch `interpreter.py`, so assign that file to one integration
owner or serialize those edits. E and F both touch `builtins.py`; serialize
their commits or partition reviewed hunks. G's runtime tooling can run
independently of host-fixture migration; harness injections overlap E and need
one owner. Parallel agents are useful only after design approval and explicit
slice delegation, not during this planning assignment.

Focused suites include `tests/unit/test_cli_args.py`,
`test_interpreter_test_mode.py`, `test_debug_stdio.py`, `test_modules_phase1.py`,
existing doc/meta/help and R20 tests, server/HTTP tests, MCP worker/profile tests,
and the native prelude guard. Use the repository's existing modules rather
than inventing duplicate semantic tests that mirror implementation.

P1 shared-spec obligation: preserve existing observations under existing
capabilities; add no isolation expectations yet. Run relevant CLI/REPL,
multi-file, reflection and open-function cases through R16. C++ must retain
supported-case results and unsupported classifications; no new capability or
host-parity claim follows from a Python accessor change. P2/P3 portable
changes need shared cases before implementation, including module entry misses,
import-order independence, declaring contribution closure, D1 transfer and
shadowing matrices. Pure debugger/host API checks belong in Python tests.

Full Python regression is the union of:

```text
uv run pytest -n auto -q -m "not loopback"
uv run pytest -n auto -q -m loopback
```

Preserve source documentation on substantial changed helpers. Generated
reference regeneration is needed only if governed public metadata changes;
P1 should not change it. No book, cheatsheet, STATE or MCP fact should claim
isolation after P1. Later observable changes update STATE and relevant book
chapters, review core/unix cheatsheets with their sidecars and required tests,
and synchronize RULES/REPL/README, semantic guards and applicable MCP facts.
P1's consumer API architecture may be documented as implemented only after
its own verification; do not duplicate proposed semantics into truth docs.

## 9. Risks and review decisions

Principal risks are incorrectly redirecting runtime consumers to E; silently
changing module-debugger/reflection output in P1; missing direct identifier or
Outcome-awareness fast paths; moving fixture capabilities without explicit
module arguments; treating runtime-public placement as trust; changing alias
identity, autoload timing or varargs selection through naive dictionary union;
and relying on survey counts instead of fresh acceptance evidence.

P2 additionally needs a design for preserving legacy entry collisions and
rebinding while E/R are distinct: own definitions, prelude file loading,
assignability, metadata merges, entry alias visibility and R20 ownership must
all be covered. An entry accessor alone cannot provide that compatibility.
The prelude repair is a guard, not a reason to declare P2 structurally proven.

Maintainer decisions requested by this design:

1. D2 finality and D2b's ordinary-only shape policy, including whether the
   fixed/rest same-minimum cross-scope combination is allowed or whether the
   narrower required-arity-slot policy should amend P0 instead.
2. Approve evaluation-bound reflective callables without Core IR changes;
   retain root-bound behavior through P1 and activate D1 in P2. Confirm stable
   same-Env caching and the identity evidence required before activation.
3. Amend the fallback deadline to evidence plus the pre-R29/60-day hybrid
   policy, or choose a different explicit duration/milestone before P2.

D1, D3, D4, the three-scope direction and the merged prelude repair are already
settled. This note presents recommendations for review; it does not mark the
open choices approved. P1 execution still requires explicit approval. P2/P3
and F3–F5 remain outside this assignment.
