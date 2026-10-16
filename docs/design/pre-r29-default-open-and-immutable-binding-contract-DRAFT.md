# #1249 — Function definitions and immutable bindings: semantic contract candidate

Status: **PROPOSED, NOT APPROVED; non-authoritative**. This records the Contract-phase candidate, not implemented Genia behavior. `GENIA_STATE.md` remains final authority. Parent #1249; later phases #1250/#1251. Derived from merged pre-flight `docs/analysis/pre-r29-function-immutability-preflight-DRAFT.md`, R20 contract, and current STATE/RULES/REPL README/README.

## 1. Problem and goal

Today R20 requires explicit `open` to introduce an extensible interface, plain function syntax is closed by default, and `name = expr` creates or updates nearest lexical name. The user prefers `=:` for immutable binding, rejects `@closed`, and proposes open function declarations as the default. The design must not silently grant third parties the right to change imported functions. #1067 was scoped to preserving existing semantics; it did not approve this redesign.

## 2. Proposed decision — for maintainer review, not GO

**Candidate B: default-open local clause model with explicit cross-module authority.**

1. `name = expr`: unchanged lexical assignment semantics, except that assignment targeting an existing immutable binding fails deterministically. Does not silently rebind a function via a function-clause declaration.
2. `name =: expr`: creates a **new immutable lexical binding in the current scope**, not a freeze operation on an existing one. The initializer is evaluated once on declaration; any later assignment to that exact binding fails. This does not promise deep immutability of value graphs. Shadowing rules must be explicit and must not undermine current module ownership.
3. `f(pattern) = expr`: defines an **open-by-default local function clause run**. Adjacent clauses for the same declared function form one ordered unit. *Local openness does not itself authorize foreign extension*. R20 unit-local first-match and ambiguity semantics remain the baseline. Plain-identifier ordinary declarations, pattern-headed declarations, grouped-body syntax and nested scope behavior require an explicit compatibility decision before GO.
4. `f(pattern) =: expr`: defines a **closed multi-clause declaration group**. The contiguous group is one atomic definition, then further clauses and `extend` attempts are rejected. Mixing `=` and `=:` in a single group is rejected before execution. A closed function's name should also be immutable **only if** that lexical behavior is explicitly approved; the two concepts must not be accidentally conflated.
5. Cross-module contribution remains a separate authorized action, with no implicit selection on import. Current `extend` and `use` must either retain a positive opt-in target declaration or use a similarly explicit authority mechanism. **Open by default for local clauses must not mean exported functions are automatically extension-capable**. Do not invent a global mutable method table.
6. Preserve existing R20 provenance, stable identity, clause ordering, guards, shape stratum, explicit selected contribution sets, duplicate and ambiguity rejection, Outcome propagation, TCO and import inertness except for separately approved compatibility changes.

**Unresolved design fork requiring approval:** What exact source declaration makes an exported default-open local function eligible for cross-module `extend`? Preferred conservative option is to retain `open f(...)=...` temporarily as the *cross-module authorization marker* while allowing `f(...)=...` to be locally open. This is *not* `@closed`, and the `open` keyword has a narrower purpose. Alternative: a separate export/extension permission, but that expands scope into module syntax. Do not remove `open` until a concrete alternative is approved.

## 3. Semantic decision table (candidate / expected tests)

| Source / situation | Proposed outcome | Open question |
| --- | --- | --- |
| `x =: 1; x = 2` in same lexical binding | error, no write | exact error stage/class |
| `x =: 1; x =: 2` same scope | duplicate declaration error | duplicate diagnostic identity |
| outer `x =: 1`; nested `x =: 2` | lexical shadow only if new local declaration is permitted | shadowing policy vs #1229/#1230 |
| outer `x =: 1`; nested `x = 2` | reject nearest-immutable write, no implicit shadow | stage/class |
| `f(0) = 1; f(n) = 2` contiguous | one local open function with source-order clauses | prevent overlap incompatibility with old ordinary function path |
| `f(0) =: 1; f(n) =: 2` contiguous | one sealed group after construction | first declaration time/atomicity |
| `f(0) = 1; f(n) =: 2` | reject mixed group | parse vs lowering error |
| `f(0) =: 1; unrelated = 3; f(n) =: 2` | reject late clause, not reopen | treatment of a new scoped binding |
| imported `module.f` with no explicit cross-module authority | foreign `extend` rejected | exact authorization mechanism |
| imported authorized `module.f` + matching `extend` + `use` | existing R20 selected-view rules | how local default-open interfaces are represented |
| plain `f = other_callable` | ordinary name assignment; not clause extension | compatibility with callable rebinding |
| `f(pattern) = body` nested in function/block | no new nested-open semantics without separate approval | likely keep current nested restrictions |

All entries remain proposals until contract approval. Clauses marked `=:` are *not* claimed executable in today's runtime.

## 4. Compatibility matrix / migration budget

- **High risk:** existing ordinary function source that shares repeated names or grouped case bodies; parser currently reserves pattern headers for explicit `open`. Inventory and representative tests required before default-open changes.
- **High risk:** `IrFuncDef` and `IrOpenFuncDef` portability/lowering; do not break Core IR versioning opportunistically (R41 or explicit versioned gate).
- **High risk:** module exports, imported values, explicit `extend`/`use` and `use` replacing an ordinary function (currently undiagnosed): ensure no silent privilege expansion.
- **Medium risk:** lexical assignments, parameters, REPL persistence, closures and debugger/inspection behavior; #1229 and #1230 are evolving module/entry scope evidence.
- **Medium risk:** R29–R31 higher-order pipeline helpers, prelude and documentation/MCP language profile; R33 tooling and R41 artifact freezing magnify delayed-change cost.
- **Unmeasured:** count and location of affected declarations in src/std/apps/examples/spec. Do not estimate migration effort numerically until inventory is executed.

## 5. PORTABILITY ANALYSIS (seven explicit fields; contract-phase intake)

1. **Observable semantic boundary:** source parsing, lexical assignment/declaration, function clause grouping/dispatch, module extension authority, diagnostics, REPL persistence. Authority remains STATE/RULES until implementation lands.
2. **Portable representation/Core IR:** existing `IrAssign`, `IrFuncDef`, `IrOpenFuncDef`, `IrOpenContribution`, `IrOpenUse` supply baseline; immutability and default-local-open indicators require a design-proven carrier. No breaking IR rewrite or host-derived semantics.
3. **Shared executable evidence:** propose capability-scoped shared spec YAML for immutable assignment, function declaration/dispatch, authorized/unselected cross-module extension, parity of errors and source grouping; tests originate in #1250 after contract approval.
4. **Capability applicability:** inspect existing `spec/manifest.json` `open_functions` and multi-file capabilities and reuse where accurate; do not invent a capability/runner merely for convenience. Differentiate existing ordinary function/assignment surface from optional extension surface.
5. **Host claims:** Python full reference host currently implements R20; C++ is bounded R27 and reports specific unsupported cases. #1250 must verify actual capabilities and update host matrix/spec gating with measured evidence; no parity claim yet.
6. **Host-gap policy:** portable changes must have Python and C++ shared evidence or explicit issue-backed `spec/known_host_gaps.json` entry naming host, affected cases, reason and removal condition before claiming merge-ready compatibility. Do not mask gaps as successful tests.
7. **Truth/documentation synchronization:** after verified implementation #1251 updates GENIA_STATE.md, GENIA_RULES.md, GENIA_REPL_README.md, README.md, spec metadata, host capability docs, reference examples and `docs/contract/semantic_facts.json` MCP language-profile registry plus generator/check. Planning draft does not update implemented truth.

**Executable semantic conformance obligation:** Reuse R16 shared spec runner and host protocol; record concrete spec case IDs and capability selection in #1250. Cross-module tests require existing multi-file mechanism. Neither Python nor C++ runtime implementation may be the source of portable semantics.

## 6. Process, dependencies, and explicit no-go

- #1253 analysis is merged; roadmap gate PR #1252 may be merged separately.
- #1229 owns P2 execution closeout and #1230 owns compatibility fallback/retirement. Do not edit their runtime scope files or decide their acceptance here. Refresh module/entry-scope baseline before finalizing this contract.
- Review and resolve §2 extension-authority fork, closed function binding semantics, nested/local definition scope, parameter immutability and duplicate-definition diagnostics before recording GO.
- No #1250 implementation, red tests, or authoritative language-state edits until the pre-flight fields and contract decisions are formally accepted by maintainer.
- Once approved: #1250 phases design → failing shared tests → bounded Python/C++ implementation and host gaps → maintainability review; #1251 documentation truth → audit → distillation. Instructions for Codex must keep all four root docs, semantic registry/MCP profile, and release evidence up to date when behavior lands.
- R29 language-facing implementation is blocked until approved semantic prerequisite and integration gate; independent planning remains allowed; #1230 remains a second independent R29 gate.

**Current disposition: CONTRACT DRAFT / NO-GO for implementation.**
