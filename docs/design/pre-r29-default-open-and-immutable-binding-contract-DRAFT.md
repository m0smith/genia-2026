# #1249 — Function definitions and immutable bindings: semantic contract candidate

Status: **PROPOSED, NOT APPROVED; non-authoritative**. This records the Contract-phase candidate, not implemented Genia behavior. `GENIA_STATE.md` remains final authority. Parent #1249; later phases #1250/#1251. Derived from merged pre-flight `docs/analysis/pre-r29-function-immutability-preflight-DRAFT.md`, R20 contract, and current STATE/RULES/REPL README/README.

## 1. Problem and goal

Today R20 requires explicit `open` to introduce an extensible interface, plain function syntax is closed by default, and `name = expr` creates or updates nearest lexical name. The user prefers `=:` for immutable binding, rejects `@closed`, and proposes open function declarations as the default. The chosen Model B permits third-party additive clause contributions to any exported open function, but never silent replacement of an equivalent clause and never automatic activation of imported contributions. Distinct overlapping clauses can make calls ambiguous, and this behavioral compatibility limit must be explicit. #1067 was scoped to preserving existing semantics; it did not approve this redesign.

## 2. Recorded extensibility decision: Model B — for contract review, not GO

**Maintainer direction (2026-10-16): choose Model B: exact duplicate protection with deterministic ambiguity detection.** Functions are open to extension by default, including cross-module contributions to exported open functions, and are **not overwritable by ordinary contribution**. This supersedes the prior draft's Candidate B (local-only openness requiring separate opt-in authorization per exported function). The contract remains **PROPOSED / NOT APPROVED FOR IMPLEMENTATION** pending review of remaining details.

1. `name = expr`: retains existing nearest-lexical-binding assignment except that writing an immutable binding established by `=:` fails deterministically.
2. `name =: expr`: creates a **new immutable lexical name binding**, with single initialization and no subsequent reassignment of that binding, even via a nested closure. An explicit new local binding's shadowing behavior still needs a scope decision. This is **not** deep immutability of reachable objects.
3. `f(pattern) = expr`: declares an **open-by-default** function; adjacent clauses belong to one source-ordered base unit. When exported, the interface is eligible for third-party `extend` without any special opt-in declaration by its author. An ordinary import **does not** activate contributions.
4. `f(pattern) =: expr`: declares a **closed** function formed from its contiguous multi-clause declaration run. New clauses and cross-module extension of that function are prohibited after its initial group; mixing `=` and `=:` in one declaration group is invalid. The treatment of later same-name lexical rebinding is a separate binding-rule decision that must not undermine closed-function semantics.
5. **No overwriting:** a contribution with an identical **normalized structural dispatch key** to an existing base or included contribution clause is rejected, not substituted, even if the contributing module differs. Key equivalence follows R20's span-free alpha-normalized dispatch identity (including guard structure). This *extends* current R20's build-time duplicate rejection, which is only within one unit; the changed cross-unit behavior needs explicit new shared evidence. No value or source-order "last-wins" rule.
6. **Distinct patterns may overlap.** Unlike disjointness-only Model A, an extension with a distinct key is permitted to exist even when it could match arguments already matched by another clause. On invocation, use R20's fixed/varargs shape stratum and first-match-per-unit behavior; if multiple participating units supply candidates, the call fails with deterministic ambiguity (rather than choosing the newest clause). No implicit specificity priority, override, or import-order preference.
7. **Selection remains explicit.** `extend base.f(pattern) = expr` still forms an inert contribution unit in the contributing module; `use f from base with contribution` selects units to form an immutable local linked view. Base module and unrelated consumers are unchanged. Contributions retain their own lexical closure and provenance. Merely importing a module never activates its extensions.
8. **Closed means no external extension.** `=:` is not a blanket permission for method replacement, and Model B does not introduce a privilege escalation or override authorization mechanism. Genuine intentional replacement is a later, separately gated proposal.
9. Preserve R20 function identity, origin/provenance, source-ordered base clauses, module-scoped linked views, Outcome propagation, TCO and diagnostic hygiene unless a later contract decision explicitly changes them. Avoid global mutable method tables and breaking portable Core IR consolidation.

### Duplicate versus overlap — essential distinction

A different-looking pattern is not necessarily disjoint: `f(0)` and `f(x)` both match input `0`; `f({status: "ready"})` and `f({status: s})` overlap on ready records. Model B permits the structurally distinct clause but **never silently prioritizes it over an already matching clause from another unit**.

An identical dispatch key is rejected in the *effective composed view*, including across different contributing units and between base and contributions. Whether duplicate keys are rejected at contribution declaration time versus link-time depends on whether the target's base unit is available and on module identity; the final contract must pin a deterministic check boundary. Two different units' duplicate clauses **must not** survive into a callable linked view. This is a deliberate divergence from the current R20 rule (cross-unit duplicate keys are presently call-time ambiguity, not build-time duplicate errors).

### Remaining review decisions (do not assume settled)

- **Duplicate detection stage:** validation at `extend` declaration, at `use` linked-view construction, or both where possible; deterministic error identity and diagnostic provenance.
- **Base unit versus contributed unit:** overlapping but different clauses in different units cause ambiguity; within one base/contribution unit existing R20 first-match order remains. Verify this is the intended meaning of "not overwritable" and document that new same-unit clauses can match earlier inputs without overriding earlier first-match choices.
- **Open function compatibility:** existing `open f(...)` spelling, ordinary-function parameter patterns and grouped clauses, and closed-source migration must be reconciled without silently changing dispatch.
- **Closed function name binding:** ensure that `f(...) =:` prohibits extension even if the callable is aliased; decide whether same-name lexical rebinding is separately prohibited.
- **Scope/portability:** nested functions, immutable shadowing and error stage/classes, runtime module/entry separation (#1229/#1230), `IrFuncDef` versus `IrOpenFuncDef`, Python/C++ capabilities and shared specs.

## 3. Semantic decision table (Model B candidate / expected tests)

| Source / situation | Proposed outcome | Open contract detail |
| --- | --- | --- |
| `x =: 1; x = 2` in same lexical binding | immutable write error; no write | error stage/class |
| `x =: 1; x =: 2` same lexical scope | duplicate immutable declaration error | diagnostic identity |
| outer `x =: 1`; nested `x =: 2` | explicit local shadow, if allowed | decide scope rule vs #1229/#1230 |
| outer `x =: 1`; nested `x = 2` | reject nearest immutable write | stage/class |
| `f(0) = 1; f(n) = 2` contiguous | one open base unit; source-order matching | compatibility with ordinary grouped function |
| `f(0) =: 1; f(n) =: 2` contiguous | closed multi-clause initial group | finalize grouping/atomicity |
| `f(0) = 1; f(n) =: 2` same run | reject mixed open/closed group | parse/lowering policy |
| `f(0) =: 1; unrelated = 3; f(n) =: 2` | reject late closed extension | treatment of redeclaration |
| `base.f(0) = ...` and external `extend base.f(0) = ...` | exact duplicate rejected in composed view, no replacement | detection stage/diagnostics |
| `base.f(0) = ...` and external `extend base.f(x) = ...` | distinct pattern permitted; on a call with 0, ambiguity if both units match | normalize key and ambiguity |
| exported open `base.f`, external `extend base.f(1)=...` | permitted without owner opt-in; inert until explicit `use` | extension authorization by openness |
| ordinary `import` of base and contribution | no activation; base's behavior unchanged | import inertness |
| `use f from base with contrib` | linked view includes selected clauses only, with deterministic collision policy | duplicate check |
| `extend base.closed(...)` where base defines `=:` | reject; no linkable contribution | stable closed identity |
| `f = other_callable` | lexical assignment, not clause replacement | collision/rebinding policy |
| nested `f(pattern) = body` | no newly approved nested-open semantics | explicit restriction unless approved |

All source examples involving `=:` or default-open functions are **proposed**, not executable behavior in current Genia.

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
3. **Shared executable evidence:** propose capability-scoped shared spec YAML for immutable assignment, function declaration/dispatch, default-eligible/unselected cross-module extension and cross-unit duplicate-versus-overlap distinction, parity of errors and source grouping; tests originate in #1250 after contract approval.
4. **Capability applicability:** inspect existing `spec/manifest.json` `open_functions` and multi-file capabilities and reuse where accurate; do not invent a capability/runner merely for convenience. Differentiate existing ordinary function/assignment surface from optional extension surface.
5. **Host claims:** Python full reference host currently implements R20; C++ is bounded R27 and reports specific unsupported cases. #1250 must verify actual capabilities and update host matrix/spec gating with measured evidence; no parity claim yet.
6. **Host-gap policy:** portable changes must have Python and C++ shared evidence or explicit issue-backed `spec/known_host_gaps.json` entry naming host, affected cases, reason and removal condition before claiming merge-ready compatibility. Do not mask gaps as successful tests.
7. **Truth/documentation synchronization:** after verified implementation #1251 updates GENIA_STATE.md, GENIA_RULES.md, GENIA_REPL_README.md, README.md, spec metadata, host capability docs, reference examples and `docs/contract/semantic_facts.json` MCP language-profile registry plus generator/check. Planning draft does not update implemented truth.

**Executable semantic conformance obligation:** Reuse R16 shared spec runner and host protocol; record concrete spec case IDs and capability selection in #1250. Cross-module tests require existing multi-file mechanism. Neither Python nor C++ runtime implementation may be the source of portable semantics.

## 6. Process, dependencies, and explicit no-go

- #1253 analysis is merged; roadmap gate PR #1252 may be merged separately.
- #1229 owns P2 execution closeout and #1230 owns compatibility fallback/retirement. Do not edit their runtime scope files or decide their acceptance here. Refresh module/entry-scope baseline before finalizing this contract.
- Model B extensibility direction is recorded, but review and resolve §2 duplicate-detection stage, closed-function name binding, nested/local definition scope, immutable shadowing, parameter behavior, module-boundary effects and duplicate-definition diagnostics before recording GO.
- No #1250 implementation, red tests, or authoritative language-state edits until the pre-flight fields and contract decisions are formally accepted by maintainer.
- Once approved: #1250 phases design → failing shared tests → bounded Python/C++ implementation and host gaps → maintainability review; #1251 documentation truth → audit → distillation. Instructions for Codex must keep all four root docs, semantic registry/MCP profile, and release evidence up to date when behavior lands.
- R29 language-facing implementation is blocked until approved semantic prerequisite and integration gate; independent planning remains allowed; #1230 remains a second independent R29 gate.

**Current disposition: CONTRACT DRAFT / NO-GO for implementation.**
