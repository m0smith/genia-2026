# #1261 / #1250 — Model B Slice B pre-flight (immutable lexical bindings)

**Status:** scoped pre-flight / RED authorization candidate; **no executable Slice B implementation or review verdict claimed**.
**Classification:** pre-R29 semantic foundation, parent #1250. Dependency: merged Slice A #1260, approved contract #1255, approved design #1259. C++ Slice A host work: `m0smith/genia-cpp#50`.
**Owner:** m0smith (integration); implementer/reviewer must be distinguished.
**Authority read before planning:** `AGENTS.md`, `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, `docs/strategy/killer-workflow.md`, `docs/strategy/release-roadmap.md`, `docs/process/run-change.md`, contract and design. The latter are *future approved semantics*, not claims that B is implemented.

## Problem and exact intended behavior

Slice A recognizes `x =: expr` and lowers `IrImmutableBind`, but the Python evaluator deliberately reports `model-b-not-implemented`. Slice B implements **only** `IrImmutableBind` execution and language-visible *binding* immutability.

The approved semantics:
1. `x =: init` declares a fresh immutable name **in its current lexical declaration scope**, evaluates the initializer exactly once only after already-detectable collisions/reserved-name checks, and commits once.
2. An existing local variable, parameter, imported alias or previous same-scope `=:` blocks a new `=:`, even when currently mutable. Explicit nested lexical declaration may shadow an outer nonreserved user binding.
3. `x = value` retains nearest-binding resolution; if that target is immutable, reject **before RHS effects**, not by silently shadowing or searching past it. Respect the existing R/E/M and `rebind_parent` owner boundaries and runtime-owned entry write-through policy until separately approved changes.
4. Runtime-owned/reserved names (including as-yet-unloaded prelude names) reject entry-scope `=:` before initializer; this must not depend on lazy autoload state.
5. Enforce via a centralized environment binding-policy / checked prepare-and-commit mechanism, not only `IrImmutableBind` evaluator branch. Inventory all language-visible writes: `Env.set`, `assign`, `find_assign_target`, function declaration, imports and aliases, R20 `use`, metadata/annotations, autoload/prelude, module exports. Operation type/ownership matter; attaching metadata *as part of the same declaration* is not a later unauthorized write.
6. Preparation is checked against concurrent writers and revalidated after initializer side effects; no rollback of effects already executed before a later collision. Binding immutability is **shallow**: Ref/Cell internal mutation remains allowed, while rebinding the name is rejected.
7. Named functions, pattern ordinary functions and closed `=:` functions remain `model-b-not-implemented` where Slice A deliberately rejects them. Do not implement C/D/E.

## Portability analysis (seven fields, scoped to contract-approved semantics)

1. **Portable observable / authority:** current-scope fresh immutable lexical declaration, earliest-invalid-target failure ordering, nearest-target reassignment rejection, reserved prelude names, explicit lexical shadowing, shallow Ref/Cell identity. Contract #1255 §3; `GENIA_STATE.md` is only authority for *currently implemented* behavior.
2. **Boundary and representation:** existing `IrImmutableBind(name, expr, annotations, span)` portable carrier from Slice A, lexical owner policy in `Env`, no new Core IR version. Preserve R/E/M and legacy `IrAssign` wire snapshots. Host-local direct-IR validation tests supplement shared source/eval tests.
3. **Executable shared specs:** RED shared R16 `eval` success/failure cases for immutability, earliest-error effect ordering, duplicate declarations, local/parent scoping, parameter/import/function-name conflicts, reserved/lazy prelude names, explicit nested shadow, module separation, annotations, Ref/Cell mutation and REPL persistence. Use already-supported R16 mechanisms; host-local tests for concurrent racing commits and bypassed writer entry points.
4. **Applicability:** re-evaluate optional independently claimable `immutable_bindings` support in `spec/manifest.json` only when Python implementation and conformance evidence exist. Do not prematurely claim optional features because `hosts/python/protocol_adapter.py:_python_claimed_capabilities` currently auto-claims manifest-supported names. Known C++ gaps may be listed only when compliant with `spec/known_host_gaps.json` optional-capability rules, with issue, removal criteria and exact cases.
5. **Host impact:** Python reference host is first implementation. C++ is bounded, not advertised as supporting `=:` syntax or execution; required parser/lowering debt is `m0smith/genia-cpp#50`. C++ Slice B semantics need explicit evidence or owned honest optional gap, without calling UNSUPPORTED parity.
6. **Implemented truth synchronization:** after verified GREEN, update `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, `docs/contract/semantic_facts.json`, generated `apps/mcp/mcp.genia` through `tools/gen_mcp_language_profile.py`, Core IR/host matrix, maintained book/cheatsheets where applicable. Preserve STATE's current word budget by proper distillation and preserve R28 release history.
7. **No new mechanisms:** reuse existing R16 runner, protocol, manifest, Core IR, environment and doc-sync guardrails. No second parser/dispatcher, external conformance system, broad version bump or undocumented import/module authority.

## Tests and RED plan

- Establish merged Slice A baseline (including the 874-case R16 suite), focused Env/scopes/prelude/autoload/import/module/R20/Ref/Cell tests; record exact command and SHA.
- Write shared failing `eval` specs and unit tests covering each valid and invalid state transition, especially `print =: side_effect()` rejected before initializer, pre-existing mutable duplicate rejected, `x =: init; x = side_effect()` rejected before RHS, nested shadowing, alias/prelude/import writers and lazy reserves.
- Host-local concurrency tests verify racing `prepare_write`/commit cannot both publish, using bounded deterministic coordination rather than sleeps. Reentrant initializer may mutate the candidate scope; commit must revalidate. Capture effects honestly, with no invented transaction rollback.
- Test shallow immutability with existing Ref/Cell operations, and no admission of closed callable self-frame rules (Slice E).
- Characterize N5 `environment._declared_prelude_names` and `tools/code_documentation.py` AST handling before any runtime-reserved name claim; don't allow silent skip of new declarations.
- Characterize N8 evaluation staging: earlier statements may have effects before reaching an unsupported declaration; Slice B only guarantees target-specific before-initializer/before-RHS rejection where target invalidity is known.
- Keep all RED code in tests/specs, commit expected failing evidence separately before editing production.

## Implementation shape and risk

Prefer one Env-owned binding-policy record alongside value+metadata, with write kind, policy and owner resolution; owner-local check and atomic recheck/commit against races. Explicitly compare `Env.set`/ `assign` and all call sites before choosing the minimal API. Preserve mutable ordinary assignment, aliases, closure captures, parameter mutability, existing R20 `use`, import/export and runtime-owned write-through.
**High-risk areas:** lazy prelude reserved manifest completeness (N5), module and entry write resolution (#1229/#1230), metadata attachments, reentrant initializer collision, racy commits, generated MCP capabilities, direct-IR bypass, old R20 imports/linked views. Do not reinterpret historical dotted `=` targets as property writes.

## Required phase gates and stop conditions

**Gate status now:** Slice A merged; contract/design approved. Slice B has not begun RED/implementation. This pre-flight authorizes no implementation by itself until the implementation executor confirms missing ambiguities are resolved and records GO. If the approved contract and current `Env` topology conflict, stop and raise an issue before tests.

Sequence: baseline → committed RED tests → minimal GREEN implementation → verification → independent maintainability review → docs + semantic facts/MCP sync → independent behavioral/truth audit → doc distillation → final-head CI → maintainer merge.
One executor may combine RED/GREEN in one session while keeping separate commits and evidence. No self-merge. Keep #1250 open.

**Do not implement:** Slice C default-open function dispatch, D linking, E closed function publication/provisional self-identity, any unapproved runtime-owned shadow policy or blanket immutable parameter defaults.

## Outcome / acceptance

A narrow Slice B PR whose RED SHA predates implementation; supported Python eval cases pass, old R20/ordinary/entry/module/prelude/Flow cases stay stable, host/capability claims are honest, required docs reflect verified behavior, review/audit PASS, and no B–E boundary drift. Record unresolved C++ and N4/N6 debt with owners.
