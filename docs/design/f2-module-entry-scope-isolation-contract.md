# F2 Module and Entry-Program Scope Isolation Contract (P0)

Status: **PROPOSED CONTRACT (P0) — no behavior in this document is implemented.**
`GENIA_STATE.md` remains final authority for implemented behavior and is not
changed by this document. Until an implementation phase lands, STATE describes
what the Python reference host actually does, including the behavior this
contract proposes to correct. This document defines required semantics and a
phased migration; it contains no tests, adds no syntax, and changes no Core IR.

**Implementation status (P2-G):** §16 and amendments A1–A3 were approved by the maintainer on #1067 ([comment](https://github.com/m0smith/genia-2026/issues/1067#issuecomment-6171848719)) and are implemented in the Python reference host by the stacked PRs #1235 (tests), #1239, #1240, #1241 and #1242, which are not on `main` until the stack merges. P3 (shadowing, `NameError` for module reads, fallback and write-through removal) and C++ module support are not implemented. `GENIA_STATE.md` section 9 is the implemented-truth statement.

**P2-0 amendment (approved; was PROPOSED):** §16 resolves
the six P2 pre-flight decisions (P2R-1 through P2R-6) and the statements in
§4.2, §4.4, §6.1, §8, §9.1, §10, §11, §12 and §13 below are read together with
it. Nothing in §16 is implemented; P2-B failing tests must not start until the
rulings are approved.

Tracking: `m0smith/genia-2026#1067` (R20 follow-up F2). Survey evidence:
issue #1067 comments "F2 survey — module entry-scope isolation" and "F2 survey
addendum". Origin: defect B9 of
`docs/analysis/unified-function-model-contract-gate-DRAFT.md` (proposed,
non-authoritative input).

## 1. Purpose and boundary

R20 contract §2.2 requires a contribution clause to close over "its own
declaring module environment, not the importer's environment". The Python
reference host does not honor that for free names, because one environment is
both the runtime scope (builtins, prelude, host bindings, module cache) and the
entry program's top-level scope, and every module environment is a child of it.

This contract defines:

1. three scopes — runtime, entry, module — with ownership, parentage, lookup
   order, and lifetime (§4);
2. module isolation, including R20 contributions and import-order
   independence (§5);
3. the visibility class of every host-injected binding (§6);
4. the lookup context of reflective names and of every consumer that today
   treats the root as "the program" (§7, §8);
5. how entry-program names that collide with runtime or prelude names are
   treated, split into definition collisions and value rebinding (§9);
6. the migration phases and their gates (§10);
7. the temporary compatibility fallback, its measurement, and its removal (§11);
8. the portability boundary and the documentation obligations (§12, §13).

It does not add a package system, import syntax, export lists, privacy markers,
selective imports, or import-alias rules (those remain separate gates).

## 2. Current behavior (non-normative record)

Recorded so that the proposal is checked against what exists. Each row cites
the authoritative statement or the code site; the survey's reproductions are in
the issue comments above.

| Fact | Where |
|---|---|
| Module evaluation uses its own module environment; module top-level assignment does not rebind names in the importing root environment | `GENIA_STATE.md` §4 (module evaluation bullet); `GENIA_RULES.md` §8.3 |
| Lexical assignment does not protect builtin/root names from rebinding inside the same root environment; this is "real current behavior" | `GENIA_STATE.md`, "Current consistency notes" |
| Every top-level module binding is exported; imports bind only the module value; loads are cached by module name | `GENIA_RULES.md` §8.2 |
| A contribution clause closes over its declaring module environment, not the importer's | `docs/design/r20-open-functions-contract.md` §2.2 |
| `make_global_env()` returns one parentless `Env` holding builtins, host sinks, `argv`, autoload tables, and the module cache | `src/genia/builtins.py` |
| File, command, pipe, native-test, and REPL programs run directly in that environment | `src/genia/interpreter.py` |
| A module environment is `Env(root, rebind_parent=False)`; its exports are its own `values` | `src/genia/environment.py` (`load_module`) |
| Free-name lookup walks `parent` links, so module code reaches the entry program's bindings | `Env.get` |
| Prelude definitions are autoloaded into, and close over, the root | `Env.try_autoload` |
| `doc`, `meta`, `help` are closures over the root and resolve string names there | `src/genia/builtins.py` |
| CLI `main` is read from the root's `values` | `src/genia/interpreter.py` (`_resolve_program_result`) |
| Native-test discovery scans the root's `values` and `binding_metadata`; fixtures and the `test` registrar are bound in the root | `src/genia/test_cli.py` |
| REPL `:env` lists every root binding, builtins included | `src/genia/interpreter.py`; documented in `GENIA_REPL_README.md` "REPL commands" |
| Debugger globals are `frame.env.root().values` | `src/genia/debug_controller.py` |

### 2.1 Observed defects

1. **Module-to-entry read leak.** With entry `zzz = 5` and module `f() = zzz`,
   `m.f()` returns `5`. A contribution whose module does not define `helper`
   resolves the entry program's `helper`. A module's top-level `y = zzz + 1`
   succeeds or raises `NameError` depending on whether the entry defined `zzz`
   before or after `import m`.
2. **Runtime-to-entry write leak.** A prelude function's *local* assignment
   rebinds a same-spelled entry top-level name, because assignment updates the
   nearest existing binding in a chain that reaches the entry's bindings.
   Calling the prelude's `actor_call` (which assigns `reply = ref()`) replaces a
   user's top-level `reply`. Sixteen locally assigned names across twelve
   prelude functions are exposed. Module code cannot do this (module
   environments do not rebind their parent).

Both follow from the same structure: the runtime and the entry program share
one scope.

Status note (P2 reconciliation): the specific prelude local-assignment instances
of item 2 were repaired independently by #1205/#1206 and are no longer
reproducible on `main`; item 2 is retained as the historical record of why the
structural write-isolation guarantee of §4.4 is still owed by P2. Item 1 is
unchanged.

## 3. Evidence and its limits

Facts from the F2 survey, recorded as input and not as obligations:

- Repository-imported modules (`web`, `resource`, and the example modules
  `ants`, `ants_terminal`, `ants_actor`, `tic-tac-toe`,
  `r12_grounded_context_answer`) and all prelude files have zero free names
  that resolve outside the module, its imports, builtins, and prelude.
- Across the instrumented regression, module code read an entry-defined name
  zero times. The one recorded read was a name the Python test harness injected
  into the root before running a module (a host-injected binding).
- Running the entry program in a child environment, with `doc`/`meta`/`help`
  redirected to it, removed the leak: 5,234 non-loopback and 31 of 31 loopback
  tests passed, and 46 tests failed, all in host code that reads the root as
  "the program's bindings" (native-test discovery, CLI `main` dispatch,
  debugger variables, Python-harness environment inspection).
- The C++ host has no module system (§12).

Limits, stated so they are not read as proof of safety:

- **Third-party Genia programs are unknown, not zero risk.** Repository tests
  cannot show that no external program relies on a module reading an entry
  binding. A dependent program fails with `NameError` at call time, not at
  import. Every removal decision in §11 must carry this uncertainty explicitly.
- Instrumentation covers executed paths only. Examples and applications that
  the suite does not execute were checked by static free-name analysis, which
  is conservative in one direction (it cannot prove a dynamically computed name
  safe).

## 4. Scopes

### 4.1 Terms

- **Runtime scope (R)** — owns language builtins, the prelude (autoloaded),
  host-injected bindings classified `runtime-public` (§6), and per-execution
  runtime state: module cache, autoload tables, debug settings.
- **Entry scope (E)** — the top-level scope of the single entry program: a
  file, a `-c` command, a pipe-stage program, a native-test file, or one REPL
  session.
- **Module scope (M)** — the top-level scope of one loaded Genia module.
- **Free name** — an identifier read that is not bound by a pattern, a
  parameter, or an enclosing lexical frame inside the reading function.
- **Reflective lookup** — resolving a name supplied as a string value at run
  time (`doc`, `meta`, `help`).
- **Unit** — E for entry code, M for module code.

### 4.2 Ownership, parentage, resolution, lifetime

| | Runtime R | Entry E | Module M |
|---|---|---|---|
| Created by | the host, once per execution | the host, once per entry-program execution; one per REPL session | the first successful `import` of a canonical module name in that execution |
| Parent | none | R | R (never E, never another M) |
| Contains | builtins, prelude, `runtime-public` host bindings, module cache, autoload tables | the entry program's top-level bindings, its import aliases, `entry-only` host bindings | the module's top-level bindings (its exports), its import aliases, its R20 contribution table |
| Free-name lookup | R, then autoload | E, then R | M, then R |
| Lifetime | the execution | the entry-program execution or REPL session | the execution (cached; evaluated once) |
| Portable identity | none | `<entry>` (R20 §2.1) | canonical module name (R20 §2.1) |

During P2 the "Contains" row for E is qualified by §16.1: names in the
runtime-owned set are bound in R even when the entry program declares them.

The lookup chain is fixed and lexical. It is never conditional on who imported
a module or who called a function. Autoload is attempted at R after a chain
miss and always defines into R.

### 4.3 Closures

A function closes over the scope in which it is defined: a function defined in
E closes over E, in M over M, and a prelude function over R. A prelude function
therefore cannot observe — and cannot assign to — entry or module bindings.
This is a consequence of the structure, not an additional rule.

### 4.4 Definition and assignment (writes)

- A definition or assignment executed in a unit binds in that unit's own scope
  chain as lexical assignment already specifies, **but the chain never contains
  another unit's scope**. An assignment from prelude or module code never finds
  an entry binding. This subsumes the runtime-to-entry write leak (§2.1).
- "Entry binding" in this contract means a binding resident in E. Under the P2
  compatibility rule (§16.1) a binding for a runtime-owned name is resident in R
  even when the entry program declared it, so it is not an entry binding for
  the purposes of this subsection or §9.1.
- Module top-level assignment never writes E or R (already true; unchanged).
- What an entry assignment or definition does when the name exists in R is a
  separate question, decided in §9.

### 4.5 Imports and the module cache

`import m` binds the module value to its alias in the importing scope (E or M).
A module imported by another module is a sibling child of R, not a child of the
importer: it cannot read the importer's bindings or aliases, and the importer
reaches it only through its alias. The cache is per execution and keyed by
canonical module name (unchanged). Cycle detection and the resolution order of
`GENIA_RULES.md` §8.2 are unchanged.

## 5. Module isolation

1. A module's free-name lookup resolves through its own scope, its explicitly
   bound import aliases, and R. It never consults E.
2. R20 base-unit clauses, contribution clauses, and linked views resolve free
   names through their **declaring** module's chain (M, then R). A contribution
   is never resolved through the importer's, the base module's, or the entry
   program's scope.
3. Execution order of the entry program does not change what a module
   resolves: a name the entry binds before `import m` is as invisible to `m` as
   one it binds afterwards.
4. Module top-level evaluation is independent of entry bindings, so import order
   cannot change a module's result.
5. State reaches a module from the entry program only through values the entry
   passes explicitly (arguments, closures, module values, `runtime-public` host
   capabilities). There is no ambient path.

The principle behind all five: **a module must not acquire authority over
entry-program bindings merely because of the environment in which it runs.**
Exceptions are explicit and justified by compatibility evidence; the only one
this contract allows is the temporary fallback of §11.

## 6. Host-injected bindings

A host-injected binding is any binding the host (not Genia source) places in a
scope: standard sinks, `argv`, stdin and key providers, environment and
`.env` snapshot providers, configuration and provider constructors, debug
hooks, native-test fixtures, and the `test` registrar.

### 6.1 Visibility classes

Every host-injected binding has exactly one declared class:

| Class | Bound in | Visible to |
|---|---|---|
| `runtime-public` | R | E, every M, and prelude |
| `entry-only` | E | entry-program code (and functions defined in E) |

An `entry-only` binding is resident in E, so a module read of it is a fallback
event during P2 (§11) and a `NameError` after P3.

There is no class granting visibility to a selected module in this contract.
A module receives a host capability from R or by explicit argument passing.

### 6.2 Rules

- An unclassified host-injected binding is a contract or host-integration
  defect. It is not public by default and not entry-only by default; it must be
  classified before it ships.
- Ordinary language-level host capabilities (builtin functions, sinks, `argv`)
  are `runtime-public`. Per-run, program-specific injections — native-test
  fixtures and the `test` registrar — are `entry-only`.
- Declaring a binding `runtime-public` is a capability decision. It is reviewed
  against R10 protected-value and the execution-realization guardrails; placing
  a capability in R does not make it a declassification authority.
- Fixtures bound `entry-only` are not visible in modules; a module under test
  receives needed values by ordinary argument passing.

### 6.3 Inventory

The inventory is individual per injection point; the builtin family is
enumerated mechanically rather than by hand. P1 must commit the enumeration as
the evidence that every name is classified, and a regression check that fails
on an unclassified name.

Observed at the commit this contract was drafted against, using a fresh
`make_global_env([])`:

| Injection point | Names | Proposed class |
|---|---|---|
| Builtin installation in `make_global_env` | 241 root bindings: 92 without a leading underscore and 149 underscore-prefixed internal helpers | `runtime-public` |
| Trusted internal values (`set_internal`, `internal_values`) | 9 | `runtime-public` and visible only to trusted (packaged) code, as today |
| Prelude autoload table | 234 autoload entries | `runtime-public` (defined into R on demand) |
| Standard sinks and input | `stdout`, `stderr`, `stdin`, `argv` | `runtime-public` |
| Native-test fixture bindings (`test_cli.py`, `env.set(name, value)`) | the names supplied per run | `entry-only` |
| Native-test registrar (`test_cli.py`, `env.set("test", ...)`) | `test` | `entry-only` |
| Python test-harness injection of arbitrary names before `run_source` | per test | not a language surface; a harness that injects a name into R declares it `runtime-public`, one that injects into E declares it `entry-only` |

The count of underscore-prefixed helpers is informative. This contract does not
make them part of the language surface; classification of a helper as
`runtime-public` does not promise it to programs.

## 7. Reflective lookup

`doc`, `meta`, and `help` resolve a name supplied as a string value.

### 7.1 Rule (decision D1)

A reflective builtin resolves its name in the lexical scope **in which the
builtin's identifier is evaluated**, using that scope's normal chain (E, then R
for entry code; M, then R for module code). The scope is fixed when the
identifier is evaluated, not when the resulting callable is invoked.

Consequences, each a requirement:

- An imported callable that calls `doc("x")` in its own body resolves `x` in
  its own module chain (M, then R). The importer's entry bindings are not
  consulted, whoever called the function.
- Entry code calling `doc("x")` resolves `x` in E, then R.
- A prelude function calling `help` resolves in R.
- Indirect use is preserved: `map(doc, names)` written in entry code resolves
  in E, because the identifier `doc` was evaluated in E, even though the call
  is made by prelude code.
- A reflective builtin passed explicitly to another unit carries the scope in
  which it was evaluated. Passing it is an explicit grant, consistent with §5 item 5.
- Reflective lookup is not a back door: it cannot name an entry binding from
  module code unless the entry program handed the module a reflective callable
  bound to E.

### 7.2 Notes

- The mechanism (how a builtin learns the scope of its evaluation) is a design
  question for P1 and is intentionally not specified here.
- Today `doc("own_helper")` called from module code cannot resolve the
  module's own helper, because resolution happens in the root. The rule above
  makes that work; this is the one place where the contract improves, not just
  restricts, observable behavior, and it must be called out in the P1/P2 docs.
- `help()` with no argument and the prelude autoload path do not name a binding
  and are unaffected.

## 8. Program-scope consumers

"Unit scope" means the top-level scope of the program unit the code belongs to.
Each consumer below must resolve in the stated context.

| Consumer | Required lookup context |
|---|---|
| Evaluator free-name read | the chain in §4.2 |
| `doc`, `meta`, `help` | §7 (scope where the identifier is evaluated) |
| Prelude autoload | defines into R only |
| CLI `main` and `argv` dispatch | E only. A module's `main`, and any R binding named `main`, are never the program entry point |
| Native-test discovery (`@test` annotations and `test(...)` registrations) | E only (entry-declared runtime-owned names included, §16.1.4): annotated functions bound in E plus registrations made through the `entry-only` registrar. Test functions in imported modules are not discovered (unchanged) |
| Native-test fixtures | bound `entry-only` in E |
| Serve-mode annotation discovery (`@route`, `@server`, `@cors`, `@get`, `@post` binding) | E only (entry-declared runtime-owned names included, §16.1.4). Annotations in modules do not self-register (unchanged) |
| REPL evaluation | E for the whole session |
| REPL `:env` (decision D3) | E's own bindings (unit scope). Runtime bindings are not listed |
| Debugger variables (decision D3) | `locals` = the frame's own bindings; `globals` = the top-level scope of the frame's declaring unit (E or M), not R |
| Module export surface (`mod.name`) | M's own bindings only, never R or E (unchanged) |
| Python-harness inspection of an execution's bindings | a harness that needs the program's bindings reads E through the program-scope accessor, not R |
| Serve program `web` alias and entry-declared handlers | E through the entry accessor; `_emit_error` through the runtime accessor |
| Host diagnostic and test-report sinks (`stdout`/`stderr` direct reads) | R, through the runtime accessor (§16.6) |
| Debug hooks and mode | owned by R; written and read through the runtime accessor (§16.6) |
| Metacircular `empty_env()` base scope | R only (§16.4) |

### 8.1 Regression coverage before isolation

`:env` has no test today (the survey found none), and the debugger variable
view is covered for an entry frame only
(`tests/unit/test_debug_stdio.py::test_stack_trace_and_scopes_variables`: `locals`
holds the frame's parameter, `globals` lists the entry's functions) with no
module-frame case. CLI `main` dispatch and native-test discovery are covered
by existing tests that failed under the survey's isolation experiment, which
shows they are sensitive to this change. The following are required **before**
any phase that separates E from R (§10):

1. A test pinning the current output of `:env`, including that it lists user
   bindings and runtime bindings under the single-root structure.
2. Debugger tests for a *module* frame's `locals` and `globals`, alongside the
   existing entry-frame test, so D3 can be checked for both unit kinds.
3. Retention of the existing CLI `main`/`argv` and native-test discovery tests
   (including `@test` discovery-error cases) as the acceptance set that must
   pass unchanged after re-pointing.

These are written in P1's TEST phase against the *existing* behavior, then
re-pointed. They are not part of this contract's PR.

## 9. Entry names that collide with runtime or prelude names

Two different things must not be conflated.

- **Definition collision** — the entry program defines a function or value whose
  name is bound in R, or is a not-yet-loaded prelude name. Today the entry and
  the prelude share one scope, so the entry's definition occupies the same
  binding the prelude would define, or the prelude's later definition collides
  with it (for example an entry `first/1` makes a later prelude load fail with
  "Duplicate function definition").
- **Value rebinding** — an assignment in entry code rebinds a name bound in R
  (STATE "Current consistency notes": assignment does not protect
  builtin/root names from rebinding).

### 9.0 Observed collisions (survey evidence)

Method: an instrumented run of the non-loopback regression (5,280 tests, all
passing; the MCP subprocess tests are excluded because they cannot be affected
in-process). A name is a *runtime name* if it was bound in the root before the
entry program first ran, and an *unloaded prelude name* if it is in the
autoload table and not yet bound. An entry program touching its own names is
not a collision.

| Category | Observed |
|---|---|
| Definition: entry defines a function with the name of a not-yet-loaded prelude function | 111 definitions, 36 distinct names, 77 tests (arity 0: 5, arity 1: 81, arity 2: 17, arity 3: 8). Names include `inc`, `map`, `filter`, `reduce`, `sum`, `first`, `length`, `append`, `reverse`, `take`, `drop` |
| Definition: entry adds a clause to an existing runtime function group | 5 definitions, 1 name (`rows`, a new arity 0 added to the existing group), 5 tests; none repeated an existing arity |
| Value: entry assigns a non-function value to an unloaded prelude name | 22 records (14 maps, 6 linked open views, 2 lambdas) |
| Value rebinding: entry assignment rebinds a name bound in the runtime before the entry ran | 70 records, 5 names (`e`, `index`, `log`, `meta`, `rows`), 58 tests |

Observations:

1. Every one of these programs passes today. None was a duplicate-definition
   failure; that error needs a same-arity collision at prelude load, which the
   suite does not exercise.
2. The only module-or-prelude read of an entry-touched name observed anywhere
   in the suite is the runtime-to-entry write defect of §2.1 item 2. No module or
   prelude read of a *rebound* runtime name or of an *extended* runtime group
   was observed.
3. The rebound names (`log`, `index`, `meta`, `e`, `rows`) look like ordinary
   identifiers reused as variables. Today such an assignment replaces the
   builtin for every module and prelude function in the execution; nothing in
   the evidence shows a program doing it on purpose to change what modules see.
4. Entry code resolves E before R, so an entry binding shadowing R gives entry
   code the same result it gets today. A shadowing semantic could change an
   observed result in exactly three ways: a module or prelude read of the name
   (none observed); an entry that extends a runtime function group with a new
   arity and then calls the runtime's other arities (the `rows` case: the
   entry only ever calls its own arity-0 clause, but nothing prevents the
   other); and a program that rebinds a builtin on purpose (none
   distinguishable in the evidence).
5. Limits: this is repository evidence. It does not show the absence of
   third-party reliance.


### 9.1 Requirement and decision D2

The direction is that an entry program may define or assign a name that exists
in R **without modifying R**: the entry's binding lives in E and shadows R for
entry code only. Modules and prelude continue to see R's binding.

The observable change from today's shared-root behavior is confined to one
phase, chosen so that module isolation (§5) and entry shadowing are separate
compatibility decisions:

| Behavior | P1 | P2 | P3 |
|---|---|---|---|
| Module free-name reads of entry names | unchanged | work, with a fallback warning (§11) | `NameError` |
| Entry definition of a name bound in R | unchanged | **unchanged**: the existing collision behavior, including duplicate-definition errors, is preserved | shadows in E; R untouched |
| Entry value rebinding of a name bound in R | unchanged | **unchanged**: rebinds R as today | shadows in E; R untouched |
| Prelude/runtime write into an E-resident entry binding (§2.1 item 2) | unchanged | removed (prelude closes over R, cannot reach E) | removed |

The mechanism by which P2 preserves rows 2 and 3 while E is a distinct scope is
the runtime-owned name write-through rule of §16.1; it is a Python-host
compatibility mechanism that P3 replaces with shadowing. D2b is not needed to
specify or implement P2 and remains a P3 dependency (§16.7).

P2 deliberately preserves today's collision errors and rebinding so that the
introduction of separate scopes is not itself a visible change for entry code,
and so that the P2 warning stream measures only module reads. P3 introduces
shadowing and must announce the change in STATE, because a program that
rebinds a builtin on purpose to change what modules or the prelude see will
change behavior.

**Group shadowing (D2b).** A function name is a group of arity shapes, and
today an entry that defines a new arity of a runtime name merges into the
runtime's group. For D2 to leave entry-visible behavior unchanged, shadowing of
a function name must be **per arity shape**: an entry clause shadows the
runtime's clause of the same shape in E, and the runtime's other shapes remain
visible to entry code, without R being modified. Name-level hiding (the entry's
group replaces the runtime's group wholesale) would silently remove the
runtime's other arities from entry code and is rejected unless a maintainer
chooses it deliberately. This adds a lookup rule (merge E's and R's groups per
shape at call resolution) that the design phase must specify.

**Disposition:** D2 is *provisionally* approved. The evidence in §9.0 supports
shadowing at P3 for entry-visible results, but D2b adds a rule that was not in
the original decision, and the evidence is repository-only. It is not finally
approved until D2b and the open questions in §14 are reviewed.

## 10. Migration phases

Each phase passes the repository's pre-flight, contract, design, failing-test,
implementation, documentation, and audit gates. None is authorized by this
document.

| Phase | Content | Observable change |
|---|---|---|
| P0 | This contract | none |
| P1 | Introduce a program-scope accessor and re-point each §8 consumer to it while the single root still holds both scopes. Add the §8.1 regression tests first. Classify every injection (§6.3) | none intended |
| P2 | Create distinct R and E scopes; modules remain children of R. Install the §11 fallback. Prelude closes over R. Apply the §16 rulings (runtime-owned write-through, evaluation-bound reflection, runtime-based `eval` base) | module reads of E-resident entry names still work and warn; prelude can no longer write E-resident names; `:env` and debugger `globals` narrow to the unit (D3); `entry-only` fixtures and the `test` registrar are invisible to prelude and modules; module-called and frame-local `doc`/`meta`/`help` resolve in the evaluating chain (§16.2); `empty_env()` no longer exposes E-resident names (§16.4) |
| P3 | Remove the fallback; strict isolation; apply D2 shadowing | module reads of entry names raise `NameError`; entry definitions and rebinding no longer touch R |

Gates:

- **P0 → P1:** this contract reviewed and approved.
- **P1 → P2:** every §8 consumer resolves in its required context under the
  single root; the §8.1 tests exist and pass; every injection is classified.
- **P2 → P3:** the §11.4 removal criteria are met.

P2 completion also requires two open P1 audit follow-ups (both Low, neither
blocked P1-H): #1220 (reflection/help ownership of the autoload catalogue and
direct-root access; acceptance criteria revised in §16.5) and #1221 (P1-C/D/G
accessor tests are stub-based; add real separated-scope coverage that fails for
each wrong-scope accessor use, per §16.6). P2 is not complete until both carry
verification evidence linked from #1067, or an approved reclassification.

F3–F5 of the unified-function-model draft remain paused throughout.

## 11. Compatibility fallback (temporary)

### 11.1 Status

The fallback is a **temporary compatibility mechanism of the Python reference
host**. It is not language semantics, is not part of the portable contract, is
not specified for any other host, and must not be described in user-facing
chapters as a feature. It exists only so that P2 can ship without silently
breaking programs — including third-party programs — that depend on a module
reading an entry binding.

### 11.2 Trigger and resolution order

During P2, and only then:

1. A free-name read in module code follows the chain of §4.2 (M, then R,
   including autoload).
2. Only if that fails to bind the name, and the name is bound in E (E-resident;
   a runtime-owned name is never E-resident, §16.1), the read resolves to E's binding. The resolved value is exactly what the pre-P2
   behavior would have produced.
3. The fallback applies to reads only. It never applies to writes, to
   reflective lookup (§7), or to export access.
4. The fallback applies identically to R20 contribution clauses and is reported
   against their **declaring** module.
5. The fallback applies only when the reading frame's declaring unit is a module.
   Prelude and other R-closure code, the metacircular evaluator (§16.4), and host
   accessors never receive it (§16.3).

### 11.3 Diagnostic and measurement

- Each fallback resolution emits one warning per distinct (canonical module
  identity, name) per execution on the host's diagnostic channel (stderr in the
  CLI modes). It does not change stdout, the exit status, or the resolved value.
- The warning names the canonical module identity and the free name, states
  that the name was resolved from the entry program, and states that the
  behavior is temporary and will become a `NameError`. It does not contain the
  bound value, a filesystem path, or host exception text (R19/R23 diagnostic
  rules). It is host-local diagnostic detail, not a portable error identity.
- A host-local strict switch makes the same run treat a fallback event as a
  failure, so a program, test run, or CI job can prove it triggers none. Its
  spelling and effect are fixed by §16.3; it is not a language-visible surface.
- Usage is measured as the count of distinct fallback events, with the
  (module, name) pairs, per run. The repository's own CI runs under the strict
  switch.

### 11.4 Removal criterion

The fallback is removed (P3) only when **all** hold:

1. P1 is complete.
2. Under the strict switch, the full regression (both `loopback` partitions)
   and every repository-owned module and program (`src/genia/std`, `apps/`,
   `examples/`, test fixtures) produce zero fallback events.
3. Shared or native evidence for §5 exists and passes.
4. `GENIA_STATE.md` documents the fallback only under a single marker line
   `TEMPORARY COMPATIBILITY FALLBACK`, and the fallback is one named code path
   so removal is a deletion rather than a redesign.
5. The removal decision records, in the PR, that repository tests do not
   establish the absence of third-party reliance, and what exposure window the
   P2 warning stream provided before removal.

Independently of the above, the deadline is the hybrid of §16.3.5 (a dated
maximum exposure window and a milestone), which replaces the earlier
release-relative wording because the follow-up has no release number. Missing
the deadline requires an explicit recorded decision that names a new absolute
date. The fallback may not be extended by inaction, and it may not become a
permanent configuration option.

### 11.5 Tracking and responsibility

- A GitHub issue is opened when P2 is authorized. It carries §11.4 as a
  checklist and is referenced by the STATE marker and by the warning text.
- The fallback is recorded as a temporary host gap with a reference issue,
  reason, affected host (Python), affected area (module name resolution), and
  removal condition (§11.4). The record is the removal issue plus the STATE
  marker defined in item 4 of the §16.3 ruling; `spec/known_host_gaps.json` is not used, because its schema
  is scoped to optional capabilities the C++ host does not declare.
- The author of P3 is responsible for removing the code path and the marker,
  updating the documents in §13, and closing the migration issue; P3 is not
  complete while the marker or the code path exists.

## 12. Portability

- **Portable (language contract):** §4 (scopes and the lookup chain), §5
  (module isolation), §7.1 (reflective lookup is scoped to where the identifier
  is evaluated), and §9.1's final state (entry bindings shadow, never mutate,
  the runtime).
- **Python reference host only:** the §16.1 runtime-owned write-through rule and
  manifest, the §16.6 construction API and test modes, §6 visibility classes as implemented through
  the Python host's injection API, §8 consumers that are host surfaces (REPL
  `:env`, debugger, CLI dispatch, native-test discovery), and the entire §11
  fallback. Documents citing these must carry the `LANGUAGE CONTRACT:` and
  `PYTHON REFERENCE HOST:` labels where applicable.
- **C++ host (`m0smith/genia-cpp`):** not affected now and no parity is
  claimed. Module `import` is rejected by its parser and reported unsupported,
  the optional capability `multi_file_eval` is declared `unsupported`, and the
  host has a single environment. There is therefore nothing to isolate, and no
  known-host-gap entry is created by this contract. The evidence for this is
  the declared capability set and the parser, not `spec/known_host_gaps.json`.
- **Future C++ obligation:** a C++ module system, when implemented, must satisfy
  §4 and §5 from its first release. It must not copy the Python fallback.
- **Shared evidence:** the existing `multi_file_eval` capability is the
  candidate vehicle for §5. The TEST phase decides applicability before any
  cross-host conformance is claimed.

## 13. Documentation synchronization obligations (future)

No document other than this one and its index entry changes in P0. Each phase
that lands behavior keeps the following current in the same change:

| Document | Obligation |
|---|---|
| `GENIA_STATE.md` | the implemented scope model, the host injection classes, the consumers' contexts, and, under the single marker, the fallback while it exists |
| `GENIA_RULES.md` | §8.2 and §8.3 invariants (module lookup, assignment, collisions) |
| `GENIA_REPL_README.md` | `:env` and debugger-adjacent REPL behavior, labeled `PYTHON REFERENCE HOST` |
| `README.md` | any user-visible module-scope statement |
| `docs/design/r20-open-functions-contract.md` | §2.2 cross-reference to the module-scope contract |
| `docs/host-interop/*` | host binding visibility classes and the C++ boundary |
| `docs/cheatsheet/*`, `docs/book/*` | only if an implemented example changes |
| `spec/*` and semantic-documentation guardrails | shared evidence for §5, and any protected fact added to `docs/contract/semantic_facts.json` |
| MCP language profile registry | revisit at P3: module isolation may merit a profile fact with a STATE anchor. P2 answer to record in its pre-flight: the P2 observable changes (§10) are host/module-visibility details; a profile fact is added only if STATE gains a module-isolation anchor |
| `docs/design/composability-matrix.md` and `tests/doc/test_composability_matrix_sync.py` | review the reflection (`doc`/`meta`/`help`) rows when §16.2 lands; run the sync test |
| `docs/book/*` (eval/metacircular chapter) | review and update if §16.4 changes an implemented example, with the cheatsheet sidecar tests when a cheatsheet example changes |

Authoritative language facts stay centralized in STATE; other documents refer to
it rather than restating the semantics.

## 14. Decisions and open questions

| ID | Decision | State |
|---|---|---|
| D1 | Reflective lookup resolves in the scope where the identifier is evaluated (§7) | approved |
| D2 | Entry definitions and rebinding shadow in E and never mutate R; P2 preserves today's collision behavior, P3 introduces shadowing (§9) | provisional; evidence in §9.0 |
| D2b | Shadowing of a function name is per arity shape, so an entry that extends a runtime group still sees the runtime's other shapes (§9.1) | proposed; needs review |
| D3 | `:env` and debugger globals show the current unit's top-level bindings; regression tests precede isolation (§8, §8.1) | approved |
| D4 | Every host-injected binding carries an explicit class, `runtime-public` or `entry-only`; unclassified is a defect (§6) | approved with the refinement that the inventory is enumerated and enforced |

P2-0 rulings P2R-1 through P2R-6 are in §16 (PROPOSED). They settle the P2
mechanism questions below only where §16 says so; D2 finality, D2b, and the
open questions that §16.7 lists as P3 dependencies remain unresolved.

Open questions returned for review (this document does not decide them):

1. **D2 finality and D2b.** Whether the evidence in §9.0 is sufficient to
   approve shadowing at P3, in particular for deliberate rebinding of builtins,
   and whether shadowing is per arity shape (D2b, recommended) or per name.
2. **Prelude helper locals.** The runtime-to-entry write leak (§2.1 item 2) exists
   today and is independent of any phase. Whether to repair it earlier as its
   own slice (rename or restructure the exposed locals) or let P2 remove it
   structurally is a scheduling decision for maintainers.
3. **Reflective-builtin mechanism.** How a builtin learns its evaluation scope
   (§7.2) is a P1 design question that may constrain Core IR or evaluator
   structure; if it requires a Core IR change, that change needs its own
   contract.
4. **Fallback deadline unit.** Proposed resolution in §16.3.5 (hybrid dated
   window plus milestone); pending approval.

## 15. Non-goals and non-changes

- No module privacy, export lists, selective imports, or import-alias export
  rules.
- No change to Core IR, the parser, lowering, the module cache key, import cycle
  detection, host modules (`python`, `python.json`), or autoload
  deduplication.
- No change to R10 protected-value behavior.
- No new user-visible builtin, annotation, CLI flag, or syntax.
- No C++ obligation now (§12).
- No implementation, test, or specification change in this PR.

## 16. P2-0 rulings (approved on #1067; implemented on the stacked P2 branches)

Status: **APPROVED** (historical wording follows: written while PROPOSED). These rulings resolve the six decisions left by the F2 P2
pre-flight. They are contract text only: no behavior below is implemented,
`GENIA_STATE.md` is unchanged, and no P2 test or code may start until the
maintainer approves §16.1, §16.2, §16.4 and §16.3.5 (the rulings that carry an
observable-behavior choice; §16.7 lists them). Identifiers `P2R-n` avoid the
unrelated D1–D4 labels of §14. Everything in this section that concerns
write-through, the runtime-owned manifest, the fallback, construction, or test
modes is **PYTHON REFERENCE HOST** behavior; the scope model it protects
(§4, §5, §7.1) is **LANGUAGE CONTRACT**.

Baseline facts the rulings rest on (verified against `origin/main` at `95c5bfb`):

- A distinct child entry scope is not P2: with `E = Env(R)`, an entry `first/1`
  or `map/1` lands in E and shadows R, an entry `rows/0` creates an E-only group
  that hides R's other arities, `log = 5` rebinds R, and `entry_scope()` still
  returns R. Shadowing is P3 behavior (§9.1).
- R holds 241 builtin bindings. The autoloaded prelude files declare about 320 distinct top-level
  names (functions and assignments), but only 217 distinct names are autoload-registered;
  about 103 declared names in 13 files (for example `map_acc`, `filter_acc`, `abs_impl`,
  `list?`, `map?`, `get_or`, `make_function`) are not registered. The autoload
  registry therefore cannot identify the names the runtime owns.
- With the entry program in the shared root, an entry `first/1` or `map_acc/3`
  already breaks the prelude's `map` (an entry-to-prelude hijack). Preserving the
  shared-root outcome for those names is what §9.1 "unchanged" means in P2.

### 16.1 P2R-1 — Runtime-owned names, collisions, write-through

**16.1.1 Runtime-owned set.** A name is *runtime-owned* at the moment of an
entry top-level binding operation if any of the following holds:

1. it is a key of R's bindings or of R's trusted internal bindings (builtins and
   `runtime-public` host injections that survive any MCP pruning);
2. it is an autoload-registered name in R;
3. it is a top-level declared name (function, named pattern, or assignment) in
   any prelude file that is an autoload target, registered or not. Files that
   are only importable as packaged modules (`web.genia`, `resource.genia`,
   `execution.genia`) are excluded; the manifest names its source files
   explicitly and a test fails if an autoload target is missing from it.

Clause 3 is a static **runtime-owned name manifest**. It is derived mechanically
from the prelude sources (by parse of top-level declarations, not by autoload
registration, and without evaluating prelude files at environment construction),
is R-owned state, and is protected by a drift test that fails when a top-level
prelude declaration is absent from it or when it fails to include every
autoload-registered name. The autoload registry is never the sole authority for
ownership. Packaged modules are modules, not runtime-owned names: an entry
assignment such as `ok_text = web.ok_text` binds in E. The manifest is not shrunk by MCP pruning (pruning removes bindings and
autoloads from R; it does not change what the prelude declares).

**16.1.2 Routing rule (P2 only).** Every top-level binding operation of the
entry unit — the IR forms `IrFuncDef`, `IrAssign`, `IrNamedPatternDef`,
`IrImport` alias, `IrOpenFuncDef`, the local name bound by `IrOpenUse`, and
annotation metadata merges — whose name is runtime-owned binds in R, with exactly the
semantics the single-root host has today, including: merging into an existing
function group, the duplicate-arity error, the non-function/open-interface
conflict `TypeError`, assignment through the existing assignability rule, and
the later prelude-load collision. Any other entry top-level operation binds in E.
Function-local and inner-frame operations follow the ordinary lexical chain
(frame, E, R); E is created with parent rebinding enabled so an inner-frame
assignment to an existing R binding rebinds R as today.

`IrOpenContribution` binds no name; the entry unit's contribution table lives in
E. The redeclaration check for open declarations tests the routed scope.

**16.1.3 What does not write through.** Prelude and R-closure code never reaches
E. Module environments never write through: a module top-level definition of a
runtime-owned name stays module-local, as today. No other name class writes
through; the set is closed and enumerable.

**16.1.4 Entry-declared visibility.** E records which runtime-owned names the
entry unit itself declared. Host consumers of the entry unit (CLI `main`
dispatch, native-test discovery including annotation metadata, serve annotation
discovery, `:env`, debugger `globals` for entry frames) observe those names through E's view, bound to R's binding,
and observe no other R binding. The mechanism is a design-phase matter.

**16.1.5 Ownership table.**

| Declaration | Resident in | Notes |
|---|---|---|
| Builtins, `runtime-public` host bindings, prelude (loaded or not), autoload tables, module cache, debug state | R | unchanged |
| Entry top-level, name not runtime-owned (including its import aliases); `entry-only` host injections | E | invisible to prelude; module reads are fallback events (§11) |
| Entry top-level, name runtime-owned | R (E records entry-declared, §16.1.4) | P2 compatibility; replaced by shadowing in P3 |
| Module top-level, aliases, contributions | M | unchanged |

**16.1.6 Ordering and arity.** R is complete (builtins, `runtime-public`
injections, MCP pruning) before E is registered; a `runtime-public` binding,
autoload registration or trusted internal installed in R after E is registered
is a host-integration defect (it could turn an E-resident name into a runtime-owned
one). An `entry-only` injection of a runtime-owned name raises. Because
runtime-owned writes land in R's single binding, every distinct arity and every
duplicate-arity outcome is the single-root outcome; no per-arity merge exists in
P2 and D2b is not required.

**16.1.7 Diagnostics and compatibility.** No new warning, error text or
exception class is introduced by write-through; its residual effect (an entry
declaration of a runtime-owned name remains visible to modules and the prelude,
and a prelude helper name can still be hijacked) is the §9.1 "unchanged" P2
behavior and is removed in P3. The `internal_values` hijack (an entry
declaration of a trusted internal name shadowing it for trusted code) is
likewise unchanged in P2 and is a P3 hardening item.

**16.1.8 Required proof (future, red first).** (a) the four collision rows of
§9.0 behave identically with E registered (entry definition vs unloaded prelude
name, extension of a loaded group, value rebinding of a loaded name, value
assignment to an unloaded prelude name) including an unregistered helper such
as `map_acc`; (b) a non-runtime-owned entry name is absent from R and invisible
to prelude code; (c) the manifest drift test; (d) each §8 entry consumer sees
entry-declared runtime-owned names; (e) `E.parent is R` and
`entry_scope() is not runtime_scope()`. Python unit tests (host mechanism);
collision and isolation observations that are portable are shared specs only
when the capability vocabulary already covers them.

### 16.2 P2R-2 — Reflection and help lookup

`doc`, `meta` and `help` activate §7.1 in P2 as evaluation-bound values over
existing lexical capture (the mechanism recommended in the P1 design §6; if the
design phase finds Core IR is required, it stops for a separate contract).

| Operation | Lookup scope | Metadata | Autoload | Catalogue / sink |
|---|---|---|---|---|
| Entry code | the evaluating frame, then E, then R | binding's owning scope along that chain | defines into R | R |
| Module code | the evaluating frame, then M, then R | same, along the M chain | defines into R | R |
| Prelude / R-closure code | the evaluating frame, then R | R | defines into R | R |
| Host direct `env.get("doc")` | R-bound value | R | R | R |
| Callable passed to another unit | the scope where the identifier was evaluated | as evaluated | R | R |

Runtime-owned names declared by the entry resolve in R (§16.1) and are found by
every row. The fallback (§11) never applies to reflection or metadata. The help
overview and families are always built from R's catalogue and written to R's
captured sink, regardless of the evaluating scope; a restricted (MCP-pruned) R
therefore shows the pruned catalogue from any scope and reflection can name only
what the evaluating chain can see.

Observable changes, to be announced in STATE: (1) a module's `doc("own_helper")`
now resolves (§7.2); (2) a module's `doc`/`meta`/`help` of an E-resident entry
name no longer resolves, whereas it does today because the root is shared; there
is no fallback for it; (3) lookup starts at the evaluating frame, so a local or
parameter binding named like the target now takes precedence (`describe(map) =
doc("map")` documents the parameter's value, not the prelude function). Entry
top-level reflection is otherwise unchanged. Value-based marking,
callable-identity stability and `map(doc, names)` binding the evaluating scope
are design requirements already stated in the P1 design §6.

Proof (future): entry, module, prelude, indirect (`map(doc, names)`),
transferred, alias and user-rebound-`doc` cases; a module attempting to name an
E-resident entry binding; MCP-pruned catalogue from E. Evaluation-scope cases are
portable and belong in shared specs (`doc_help` with `multi_file_eval`); host
retrieval and catalogue-ownership cases are Python unit tests.

### 16.3 P2R-3 — Compatibility fallback and strict switch

1. **Needed.** Yes. The fallback is retained as §11 specifies because
   third-party reliance on module-to-entry reads is unknown, and its cost is one
   named code path in the name-miss branch of `Env.get`.
2. **Eligibility is structural, not registered.** A read resolves through the
   fallback only if (a) the reading frame's declaring unit is a module (including
   R20 contribution clauses, reported against the declaring module); (b) the
   M-then-R chain including autoload and trusted internals has missed; (c) the
   name is E-resident; and (d) the read is an identifier evaluation of a free
   name by the evaluator. Condition (d) makes the fallback opt-in per call site:
   reflection, the metacircular evaluator and host `Env.get` calls never request it. No allowlist or manifest of eligible programs exists.
   Events are recorded as the per-execution set of (canonical module identity,
   name) pairs held on R, which also drives warning deduplication.
3. **Strict switch.** The environment variable `GENIA_STRICT_MODULE_SCOPE=1`
   (the repository already uses environment variables for host-local switches, for
   example `GENIA_DEBUG_OPT`), read once when R is constructed. No CLI flag, API
   keyword or language surface is added. Under strict mode a would-be fallback
   read raises the ordinary `Undefined name` `NameError`, adding no new failure
   mode. Strict mode does not detect module or prelude reads of entry-declared
   runtime-owned bindings (they are R-resident); the P2→P3 gate therefore also
   requires measuring those reads before shadowing is introduced (§16.7).
   The default during P2 is off (fallback with warning).
4. **Marker and recording.** The code path is one named function carrying the
   literal marker `TEMPORARY COMPATIBILITY FALLBACK`, which also appears once in
   `GENIA_STATE.md`. The temporary-gap record is the removal issue plus that
   marker; `spec/known_host_gaps.json` is not used (its schema is C++/capability
   scoped). The removal issue is opened when P2 is authorized and is cited by the
   warning text.
5. **Removal and deadline (hybrid).** Removal conditions are §11.4 unchanged.
   The deadline is the earlier of (a) 60 calendar days after the UTC date on which
   warning-enabled P2 is first on `main`, recorded in the removal issue and
   STATE marker, and (b) the start of R29 implementation, with the P1 design §7
   caveat: if (b) leaves too little exposure, scheduling is reviewed explicitly and
   no evidence criterion is waived. Missing a limit requires a recorded decision
   with owner, reason, remaining evidence and a new absolute date. There is no
   automated date-expiry check and no repository-program execution manifest;
   the removal PR carries a table of repository programs/modules/fixtures run under
   strict mode, states which suites ran through the construction helper (single-root
   tests cannot produce events), and lists any that could not be run. The R29 milestone
   is the first merged PR or issue label that starts R29 implementation, recorded in
   the removal issue.
6. **Masking prevention.** The repository CI runs the full regression with strict
   mode on, so any unintended module read of an E name fails; the tests that
   intentionally exercise the fallback clear the variable explicitly and are the
   only fallback-event sources. Further tests (including reflection called from a module frame) prove the
   fallback never serves writes, reflection, exports, prelude or R-closure reads, `empty_env()` lookups
   (§16.4), or runtime-owned names (which are never E-resident), and that
   warnings contain no value, path or exception text.

### 16.4 P2R-4 — Metacircular `eval` base environment

Today `empty_env()` creates a child of R, so it also sees whatever the entry
program bound, and a module calling `eval(expr, empty_env())` reads entry
bindings. `empty_env()` takes no caller scope, so the only base that does not
give module code entry authority (§5, principle sentence) is R. Ruling: the base
of `empty_env()` is a child of R and never of E; there is no fallback for it.
State reaches an evaluation explicitly through `define`/`extend`; runtime-owned
names (including entry-declared ones, which live in R) remain visible. This is an
observable P2 change for entry programs that evaluate quoted code naming an
E-resident entry function; it must be announced in STATE and the eval book
chapter, and the migration is to `define` the name explicitly. Alternative
(not recommended without separate approval): make `empty_env` evaluation-bound
like §16.2, which extends the D1 mechanism to a further builtin and needs its own
design review. Repository evidence: the metacircular unit tests pass with the
entry in a child scope; no repository spec evaluates quoted code naming an
entry-defined name; third-party reliance is unknown, as in §3.
Proof (future): a module and an entry program each attempt to evaluate an
E-resident name through `empty_env()` (must raise `NameError`); explicit
`define` works; runtime names resolve; evaluation of an entry-declared
runtime-owned name works.

### 16.5 P2R-5 — #1220 reclassification

`builtins.py` reads `env.root().autoloads` inside `make_global_env`, where `env`
is the runtime scope being built and closes into the help helpers. Under the
approved graph R is the parentless root, so `root()` and `runtime_scope()` are
the same object for every Env, and the reads are correct. They cannot be shown
wrong by a test on the accessor spelling alone. The actual risk is different:
when P2-D threads a lookup scope into the reflection helpers, a catalogue read
from the lookup scope's own `autoloads` (which is empty for E and M) silently
empties `help()`. Ruling: the requirement is correct scope behavior, not a
particular refactor.

Revised #1220 acceptance criteria (replace criteria 1–2; keep 3–5):

1. The help catalogue (`_public_autoload_paths`, `_discover_public_family_names`)
   reads only the runtime scope through `runtime_scope()`; behavior-neutral.
2. An AST source guard fails on `.root()` calls outside `environment.py` and on
   `.autoloads` reads whose receiver is not a `runtime_scope()` result, with an
   explicit reviewed allowlist for receivers that are the runtime scope by
   construction (for example the constructor's own `env`); it fails on the current
   `.root()` reads, giving the red phase for the accessor.
3. Behavioral tests with real, non-aliased R, E and M (setup asserts
   `E.autoloads == {}` while R's is non-empty as a control): `help()` output is
   identical when evaluated from E, from M, and from R; an entry- or
   module-defined name never appears in a family; a pruned R shows the pruned
   catalogue from E.
4. Existing reflection/help, autoload, module and MCP security suites pass.
5. Independent verification that no scope leak or semantics change exists beyond
   §16.2, with evidence linked from #1067.

`.root()` is not prohibited inside `environment.py` (structural root operation).

### 16.6 P2R-6 — Entry registration, construction, test coverage

1. **Registration API.** `make_global_env()` still returns R and callers that
   supply their own root keep `entry_scope() is runtime_scope()`. A host-only
   operation on R, `create_entry_scope()`, allocates E as a child of R with
   parent rebinding enabled and its own unit identity, registers it as the
   execution's entry, and returns it; a second call on the same R raises. After
   registration `entry_scope()` returns E from any Env of the execution,
   `runtime_scope()` returns R, `unit_scope()` returns E for entry frames and M
   for module frames, and `inspection_globals_scope()` returns the unit scope.
   `set_host(..., visibility=...)` routes by class from any Env of the execution:
   `runtime-public` into R, `entry-only` into E. On a root with no registered
   entry, `entry-only` installs into R (entry is the root), preserving the existing
   single-root harnesses; the construction helper rejects an `entry-only` install made
   after R is complete but before `create_entry_scope()` returns. Module environments stay children of R built by
   `load_module`.
2. **One construction helper.** The Python host provides one helper that builds R,
   applies pre-registration host work (runtime-public installs, MCP pruning),
   registers E, and returns both scopes. Every program-construction site uses it;
   a source guard fails on a program evaluated outside it. `run_source` never
   registers E and keeps evaluating in the scope supplied.
3. **Evaluation scope of hosts.** `make_test_env` returns the entry scope (or both
   scopes) so that native-test identification (`identify_tests`) and the runner
   evaluate in E; the serve path reads the `web` alias and entry declarations from E.
   The construction-site guard matches any evaluator entry point
   (`run_source`, `Evaluator(...).eval_program`), not only `run_source`.

   **Runtime-owned reads and writes by hosts.** Direct reads of `stdout`/`stderr`
   sinks (`_emit_error`, native-test report writers) go through the runtime
   accessor; debug hooks and mode are written to and read from R so stepping
   reaches higher-order callbacks, modules and prelude frames; the native-test
   registration list is written and read on the same scope (E).
4. **Construction sites (13) and disposition.**

| Site | Role | Disposition |
|---|---|---|
| `interpreter.py` `repl` | REPL session | one E per session, persists |
| `interpreter.py` `run_debug_stdio` | debugger | root frame is E |
| `interpreter.py` `_run_serve_file` | serve | discovery on E |
| `interpreter.py` `_run_execution_mode` (pipe, command, file: 3 sites) | CLI modes | entry runs in E |
| `test_cli.py` `make_test_env` (consumed by `native_test_runner`) | native tests | fixtures and registrar `entry-only` into E; returns E |
| `hosts/python/exec_model_fixture.py`, `exec_r12_grounded_fixture.py`, `exec_r25_concurrency_fixture.py` | conformance adapters | fixtures `entry-only` into E |
| `hosts/python/exec_ollama_chat.py` | offline adapter | entry runs in E |
| `hosts/python/mcp_worker.py` | MCP worker | prune R, then register E; E starts empty; no host binding added after pruning |
| `hosts/python/mcp_host.py` | MCP server program | server program runs in E; `serve` read from E; the separate run capability keeps its own worker process |

Not program sites and unchanged: `builtins.py` R creation, `load_module` module
Env, the metacircular base (§16.4), evaluator/callable frames, and the two
catalogue-only tools (`gen_function_docs.py`, `lint_doc.py`), which stay on
`runtime_scope()`.
5. **Test coverage.** A suite-wide separated mode is not required: 171 test files
   run source in a caller-created root and would still pass without exercising
   separation, and five harnesses read root values by design. Instead (a) every
   boundary in the #1221 list is covered through the real host entry points, and
   (b) a shared test fixture builds a real R and E and itself fails if
   `entry_scope() is runtime_scope()` or if R and E binding sets overlap, so a
   single-root test cannot count; (c) each boundary test has a wrong-accessor
   variant that fails when handed the other of `runtime_scope()`, `entry_scope()`
   or `unit_scope()`. Native-test and portable observations that are invariant
   across P1/P2/P3 go in shared specs or native tests; accessor, host and sink
   mechanics are Python unit tests, labeled as such.

### 16.7 Phase boundary, dependencies and gate

- **Settled for P2 by this section (once approved):** runtime-owned write-through,
  evaluation-bound reflection, the fallback and strict switch, the `eval` base,
  the construction API, and the #1220/#1221 completion criteria.
- **P2→P3 gate additions:** measure module and prelude reads of entry-written
  R bindings (a counter or diagnostic) before shadowing is introduced; give R a
  module identity distinct from E's `<entry>` identity if open-interface keys,
  fallback reports or debugger attribution need it (design question); decide the
  Option-awareness walk (`_closure_lookup`) for callables resolved only through
  the fallback (deferred, unchanged in P2).
- **MCP note:** pruned builtin names stop being runtime-owned while pruned prelude
  names stay owned (the manifest is not shrunk); neither lets write-through recreate
  a denied binding in R, which a test must assert.
- **Deferred to P3, unchanged:** D2/D2b finality and any shadowing, `NameError`
  for module reads, removal of the fallback and the write-through rule, the
  `internal_values` hardening, export/privacy, C++ module system. P2 needs no
  interim semantic rule from these; P2→P3 requires them to be ruled on first.
- **Approval items:** §16.1 (including the choice to preserve collisions for
  unregistered prelude helper names; the alternative of shadowing helper names in
  P2 contradicts the §9.1 table and is not adopted), §16.2 (including the
  module-reflection change), §16.3.5 (deadline), §16.4 (the `empty_env` change).
- **Recommended slice order:** P2-A characterization (parallel with approval) →
  P2-B failing tests → P2-C topology and construction helper → P2-D consumer flip,
  reflection, `eval` base → P2-E fallback and strict switch (serialize the
  `environment.py` hunks) → P2-F integration and the #1220/#1221 evidence → P2-G
  documentation, semantic facts and audit. Each documentation slice updates
  STATE, RULES, the REPL README, host-interop and the book/cheatsheets with
  their sidecar tests in the same change as the behavior.

### 16.8 P2 reconciliation with P2-A evidence and amendments (A1–A3 approved)

Status: **APPROVED** (historical wording follows: written while PROPOSED); A2 supersedes the 60-day/R29 "earlier of" deadline wording of §11.4 and §16.3.5. §16.1–§16.7 above are unchanged. This
subsection records how the P2-A characterization
(`.genia/process/issue-1067-f2-p2-a-characterization.md`, PR #1228) relates to
§16 and the amendments the maintainer is asked to approve together with the six
rulings. The approval record is
`.genia/process/issue-1067-f2-p2-approval-gate.md`. An amendment takes effect
only when approved on #1067; until then §16.1–§16.7 stand as written.

**Reconciliation result.** No P2-A observation contradicts a P2R ruling. The
observations that the rulings rest on were reproduced against real
environments: `map_acc` is unregistered and installed into R by the list-file
load (P2R-1 manifest need); a child scope shadows or hides runtime groups
instead of writing through (P2R-1 premise); string `doc`/`meta`/`help` capture R
even in a module (P2R-2 observable change 1); `empty_env()` is a non-rebinding
child of R that reads live entry names (P2R-4 observable change); error and
test sinks ignore a sink bound on an inherited scope (P2R-6); plain-child `main`
is ignored by the entry accessor (P2R-6). Three items are P2-A *limits*, not
conflicts: root and runtime accessors coincide, so #1220 cannot be proven by
accessor spelling alone (P2R-5); manifest counts (about 320 / 217 / 103) were
not independently re-derived in P2-A and are re-derived by the P2-B drift test;
MCP pruning was characterized on a root and a plain child, not on a worker E.

**A1 (modifies §16.7, P2→P3 gate): measurable retirement gate for the
entry-to-prelude interference.** The residual risk of §16.1.7 (an entry
declaration of a runtime-owned name stays visible to modules and the prelude,
including hijack of an unregistered helper such as `map_acc`, and
`internal_values` shadowing) is a **P3 obligation**. P3 may not remove
write-through or introduce shadowing until all hold: (a) the entry-declared
runtime-owned name list of §16.1.4 is measured per run, by class (public
registered, unregistered helper, builtin), for CI and the repository-owned
programs, and its non-empty members each have a recorded disposition;
(b) module and prelude reads of entry-written R bindings are counted (§16.7
first bullet) with the counts recorded in the fallback removal issue;
(c) the currently characterized hijack behaviors (entry `first/1`, `map_acc/3`
breaking the prelude `map`) are pinned by a test so P3 changes them
deliberately; (d) D2/D2b are ruled. No per-arity shadowing is introduced in P2.

**A2 (modifies §16.3.5 and the final paragraph of §11.4): fallback deadline.**
Replace "the earlier of (a) 60 calendar days … and (b) the start of R29
implementation" with an evidence-gated policy: the removal criteria of §11.4
are the only removal condition; the start of R29 implementation is a hard gate
(R29 intake references the removal issue as a blocker and may not start with
the fallback present unless a recorded revised decision names owner, reason,
remaining evidence and a new absolute date); 60 calendar days after the UTC
date warning-enabled P2 is first on `main` is a **review checkpoint**, not a
removal trigger — at the checkpoint the removal issue must show either readiness
or a visible blocker / recorded revised decision. Sixty days is not claimed to
guarantee a sufficient exposure window. No silent extension, no automatic
removal, no date-expiry runtime check, no permanent switch. The removal PR
records the exposure window that actually occurred.

**A3 (clarifies §16.6.4): inventory scope.** The 13 program-construction sites
are migrated to the construction helper. The broader P2-A inventory (13 program
+ 3 tooling + 15 direct `Env` allocations = 31) is classified as: 13 program
sites migrate; 3 tooling calls stay on `runtime_scope()`; of the 15 direct
allocations, 1 is R creation, 1 is the module Env, 1 is the metacircular base
(P2R-4), 1 is a metacircular pattern child, and 11 are evaluator/callable
frames that inherit their parent's scope and are not construction sites.
Legacy single-root harnesses (caller-created roots where entry is root) remain
intentional and are not counted as separation evidence (§16.6.5).
