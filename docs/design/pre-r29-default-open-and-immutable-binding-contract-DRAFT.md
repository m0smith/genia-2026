# #1249 — Function definitions and immutable bindings: semantic contract candidate

Status: **REVISE — independent review found 2 BLOCKERS and high-priority design gaps; PROPOSED, NOT APPROVED; non-authoritative**. This records the Contract-phase candidate, not implemented Genia behavior. `GENIA_STATE.md` remains final authority. Parent #1249; later phases #1250/#1251. Derived from merged pre-flight `docs/analysis/pre-r29-function-immutability-preflight-DRAFT.md`, R20 contract, and current STATE/RULES/REPL README/README.

## 1. Problem and goal

Today R20 requires explicit `open` to introduce an extensible interface, plain function syntax is closed by default, and `name = expr` creates or updates nearest lexical name. The user prefers `=:` for immutable binding, rejects `@closed`, and proposes open function declarations as the default. The chosen Model B permits third-party additive clause contributions to any exported open function, but never silent replacement of an equivalent clause and never automatic activation of imported contributions. Distinct overlapping clauses can make calls ambiguous, and this behavioral compatibility limit must be explicit. #1067 was scoped to preserving existing semantics; it did not approve this redesign.

## 2. Recorded extensibility decision: Model B — for contract review, not GO

**Maintainer direction (2026-10-16): choose Model B: exact duplicate protection with deterministic ambiguity detection.** Functions are open to extension by default, including cross-module contributions to exported open functions, and must not replace existing clause records by ordinary contribution. The current R20 shape-selection rules can nevertheless silently suppress a previous match; **the non-overwriting guarantee is NOT established until the cross-unit fixed/varargs conflict is resolved**. This supersedes the prior draft's Candidate B (local-only openness requiring separate opt-in authorization per exported function). The contract remains **PROPOSED / NOT APPROVED FOR IMPLEMENTATION** pending review of remaining details.

1. `name = expr`: retains existing nearest-lexical-binding assignment except that writing an immutable binding established by `=:` fails deterministically.
2. `name =: expr`: creates a **new immutable lexical name binding**, with single initialization and no subsequent reassignment of that binding, even via a nested closure. An explicit new local binding's shadowing behavior still needs a scope decision. This is **not** deep immutability of reachable objects.
3. `f(pattern) = expr`: declares an **open-by-default** function; adjacent clauses belong to one source-ordered base unit. When exported, the interface is eligible for third-party `extend` without any special opt-in declaration by its author. An ordinary import **does not** activate contributions.
4. `f(pattern) =: expr`: declares a **closed** function formed from its contiguous multi-clause declaration run. New clauses and cross-module extension of that function are prohibited after its initial group; mixing `=` and `=:` in one declaration group is invalid. The treatment of later same-name lexical rebinding is a separate binding-rule decision that must not undermine closed-function semantics.
5. **Proposed duplicate protection, pending portable-key repair:** a contribution with an identical **normalized structural dispatch key** to an existing base or included contribution clause is rejected, not substituted, even if the contributing module differs. Key equivalence requires a corrected host-neutral tagged representation, not the current Python structural key (which conflates `true` and `1`). Guards and free references are syntactic, not proof of matching equivalence. This *extends* current R20's build-time duplicate rejection, which is only within one unit; the changed cross-unit behavior needs explicit new shared evidence. No value or source-order "last-wins" rule.
6. **Distinct patterns may overlap; shape conflict policy remains a BLOCKER.** Unlike disjointness-only Model A, an extension with a distinct key is permitted to exist even when it could match arguments already matched by another clause. On invocation, use R20's fixed/varargs shape stratum and first-match-per-unit behavior; if multiple participating units supply candidates after shape selection, the call fails with deterministic ambiguity (rather than choosing the newest clause). No implicit specificity priority, override, or import-order preference.
7. **Selection remains explicit.** `extend base.f(pattern) = expr` still forms an inert contribution unit in the contributing module; `use f from base with contribution` selects units to form an immutable local linked view. Base module and unrelated consumers are unchanged. Contributions retain their own lexical closure and provenance. Merely importing a module never activates its extensions.
8. **Closed means no external extension.** `=:` is not a blanket permission for method replacement, and Model B does not introduce a privilege escalation or override authorization mechanism. Genuine intentional replacement is a later, separately gated proposal.
9. Preserve R20 function identity, origin/provenance, source-ordered base clauses, module-scoped linked views, Outcome propagation, TCO and diagnostic hygiene unless a later contract decision explicitly changes them. Avoid global mutable method tables and breaking portable Core IR consolidation.

### Duplicate versus overlap — essential distinction

A different-looking pattern is not necessarily disjoint: `f(0)` and `f(x)` both match input `0`; `f({status: "ready"})` and `f({status: s})` overlap on ready records. Model B intends not to prioritize structurally distinct overlaps, but **current R20 fixed-arity-over-varargs shape selection can silently suppress another unit before matching**. This must be prohibited or redesigned before approval.

An identical dispatch key is rejected in the *effective composed view*, including across different contributing units and between base and contributions. Whether duplicate keys are rejected at contribution declaration time versus link-time depends on whether the target's base unit is available and on module identity; the final contract must pin a deterministic check boundary. Two different units' duplicate clauses **must not** survive into a callable linked view. This is a deliberate divergence from the current R20 rule (cross-unit duplicate keys are presently call-time ambiguity, not build-time duplicate errors).

### Remaining review decisions (do not assume settled)

- **BLOCKER: cross-unit fixed/varargs conflicts:** proposed conservative resolution is reject a linked view when one participating unit contains fixed arity `n` and another contains eligible varargs minimum `m <= n`; seek explicit maintainer approval and account for presently valid linked views. No change to within-unit R20 rules by default.
- **HIGH: duplicate detection stage and key correctness:** proposed stage is atomic `use` link-time checking over the full participating selected set (plus existing unit-local construction checks); use host-neutral tagged literals (distinguish Boolean/Integer) and scope-aware binder normalization. Guard/free-name identity remains syntactic, not semantic equivalence.
- **Base unit versus contributed unit:** overlapping but different clauses in different units cause ambiguity; within one base/contribution unit existing R20 first-match order remains. Verify this is the intended meaning of "not overwritable" and document that new same-unit clauses can match earlier inputs without overriding earlier first-match choices.
- **Open function compatibility:** existing `open f(...)` spelling, ordinary-function parameter patterns and grouped clauses, and closed-source migration must be reconciled without silently changing dispatch.
- **HIGH: closed function name binding:** recommended `f(...) =:` constructs a closed callable and an immutable defining name in one validated maximal contiguous run; aliases cannot enable extension. Blank lines/comments do not end the run; interleaving statements or REPL submission boundaries do. Explicit approval remains required.
- **BLOCKER: all language-visible binding writers:** immutable binding must be protected from `=`, `use`, imports/aliases, function declarations, annotations and autoload publication, not just the lexical assignment path. Recommend reject known invalid writes before initializer effects, reject same-scope redeclaration, permit explicit lexical shadowing, keep parameters mutable, and keep referenced Ref/Cell capabilities mutable. Scope policy requires separate approval.
- **HIGH: ordinary-source compatibility:** preserve existing grouped-case header captures, inline docstrings, `@category`/`@test`/`@route` annotations, and alternative function declaration forms; do not blindly lower all ordinary functions as R20 `IrOpenFuncDef`.
- **HIGH: scope/portability:** locally executed named-function instances must not borrow top-level (module, exported name) identity; local callable instance identity and permitted export/extension targets require a precise rule. Specify source-vs-direct-IR agreement, bounded Core IR carriers, C++ supported behavior and issue-backed gaps. Nested functions, immutable shadowing, error stage/classes and module/entry separation (#1229/#1230) need explicit resolution.

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
- #1229 owns P2 execution closeout and #1230 owns compatibility fallback/retirement. **Independent review dated 2026-10-16 reports PR #1254 merged on `main`, removing the temporary fallback and strict switch.** Verify that observation against current `main` before final approval. Do not recreate the removed fallback, overwrite #1229/#1230 closure evidence or declare their tickets closed based on contract review. Current STATE still records runtime-owned entry write-through, so binding routing needs explicit coordination.
- Model B extensibility direction is recorded, but review and resolve §2 duplicate-detection stage, closed-function name binding, nested/local definition scope, immutable shadowing, parameter behavior, module-boundary effects and duplicate-definition diagnostics before recording GO.
- No #1250 implementation, red tests, or authoritative language-state edits until the pre-flight fields and contract decisions are formally accepted by maintainer.
- Once approved: #1250 phases design → failing shared tests → bounded Python/C++ implementation and host gaps → maintainability review; #1251 documentation truth → audit → distillation. Instructions for Codex must keep all four root docs, semantic registry/MCP profile, and release evidence up to date when behavior lands.
- R29 language-facing implementation is blocked until approved semantic prerequisite and integration gate; independent planning remains allowed; #1230 remains a second independent R29 gate.

## 7. Independent Codex review disposition — 2026-10-16

**Verdict: REVISE.** Reviewed current `main` at `e551021` and #1255 head `de68abba` with read-only runtime probes, not a complete regression. Source: maintainer-supplied independent Codex review (392 lines). Model B remains the selected *direction*, not an approved contract. Findings:

| Severity | Finding | Required contract response before GO |
| --- | --- | --- |
| BLOCKER | Cross-unit fixed-arity contributions displace varargs base behavior without ambiguity; even pattern misses may mask previously successful calls | Explicitly approve conservative link-time cross-unit fixed/varargs conflict rejection or alternate shape policy; add proof examples |
| HIGH | Current structural keys falsely collide for `true` and `1`; same-spelled free guard names may close over different environments | Portable tagged, binder-aware syntactic key; distinguish key equality from actual semantic overlap; prohibit guard execution in validation |
| BLOCKER | Current language-visible binding writers such as `use` can bypass lexical assignment protection | Define single immutable binding invariant across `=`, imports, `use`, declaration, annotations, autoload, REPL and initialization effects |
| HIGH | Closed clause group/immutable defining name/REPL semantics unclear | Define maximal contiguous clause group with atomic validation, immutable defining binding, aliases preserve callable closedness, REPL submission boundary |
| HIGH | Existing ordinary grouped functions and annotations break if blindly treated as R20 open functions | Compatibility inventory and explicit treatment of grouped header, metadata, inline docs and alternate declaration forms |
| HIGH | Local function factories cannot share top-level module/name identity | Bound local callable-instance identity, no external targeting unless explicitly supported, preserve re-export provenance |
| MEDIUM | Matcher/guard effects and Option/none propagation mean ambiguity is not complete observational determinism | Limit guarantee to chosen candidate/diagnostic after successful matching; keep established effects and propagation truth |
| HIGH | IR carrier and migration/conformance evidence must be approved before code | Shared source/direct-IR semantic contract, explicit Python/C++ supported cases and owned gaps |

**Recommended resolution rules for maintainer decision:** reject cross-unit fixed/varargs shape conflicts at link time; validate all cross-unit structural-key duplicates atomically when `use` forms the effective view; normalize literal keys with portable type tags and binders with lexical scope; reject any language-visible immutable write before executing its initializer; make `f(...)=:` bind a closed callable under an immutable defining name and end clause group at the next other statement/REPL submission. These are review recommendations, **not approved behavior**.

**Specific shared-spec examples to design before #1250:** base `f(..xs)` plus external fixed `f(x)` and `f(0)`; `true`/`1` literal key distinction; equal normalized cross-unit keys vs distinct overlapping guards; assignments through nested scopes/import/use/autoload and effectful initializers; closed factorial aliases/late clauses/mixed operators/REPL; ordinary grouped headers with `@category`, `@route`, and inline docs; direct IR vs parsed source; module aliases/re-exports/selected units; C++ optional capability reporting.

**Scope note:** review found PR #1254 merged fallback removal into main (`e551021`). This draft should not continue asserting the temporary fallback is still active; #1230 remains a separate closeout tracking item subject to verified GitHub state. Do not edit Claude's module-scope implementation or evidence.

**Current disposition: CONTRACT DRAFT / REVISE / NO-GO for implementation.** Resolve BLOCKER/HIGH findings, seek maintainer decisions, and commission a fresh independent semantic review before authorizing #1250.

## 8. Proposed resolution package for second review (NOT APPROVED)

This section is the **current, precise candidate** for resolving the Codex REVISE findings, and supersedes ambiguous earlier statements in this draft wherever they differ. Nothing here is implemented or accepted solely because it appears in the document. Explicit maintainer contract approval and fresh independent audit remain mandatory.

### 8.1 Open-by-default and linking

- Each **module-owned** ordinary named function declaration defines an open interface by default, without changing the ordinary body scope, accepted annotations, inline documentation, alternate body spellings or current lexical binding of its parameter names. This is observable openness of module-owned definitions, not an implicit conversion of every callable value (lambda, builtin, host callable or local factory) into a cross-module contribution target.
- Existing `open name(...)` is accepted as compatible explicit syntax during migration and has the same interface behavior; this design does not force historical R20 users to rewrite source.
- External `extend alias.name(...)` of an exported module-owned open interface is permitted without an author-side opt-in. Declaration is inert; only an explicit `use` selects contributions for a consumer-local linked view. Import alone neither selects clauses nor mutates any existing view.
- Closed callables created by `f(...)=:` cannot be `extend` targets under any alias. Plain assignment of an ordinary callable does not endow that callable with extendable interface ownership. A re-exported base interface preserves its original identity; linked-view values remain non-targetable until a separate explicit design decision.
- Within a unit, existing source-order first-match semantics remain. Across units there is no implicit priority, "last wins", specificity ranking or replacement permission.

### 8.2 Collision and shape validation (review approval required)

- A **dispatch key** is a host-neutral structural, source-syntactic identity for a clause's pattern, guard and shape, with type-tagged literal encodings (so Boolean `true` is not Integer `1`), binder-aware alpha-normalization, and explicit treatment of free names as *syntactic references*. Keys make **no assertion** that two distinct clauses have disjoint accepted inputs or that equal free-name syntax has equal captured values across modules. Never evaluate a guard, named matcher or clause body to compute keys.
- Reject duplicate keys within a base/contribution unit at construction as already required by R20. At `use` time, before a linked view is published, validate *all* selected base and contribution units together and reject **cross-unit duplicate keys** atomically with diagnostic provenance for both clauses. A contributor's inert declaration may exist even when selecting it would be invalid. Selection/order/alias changes must not change the rejection result.
- **Proposed conservative shape-coherence rule:** refuse to link a view containing a fixed arity `n` in one participating unit and a varargs minimum arity `m <= n` in a *different* participating unit. Reject before any call rather than allowing fixed-arity selection to suppress a base varargs handler. Preserve existing shape selection *within* one unit.
- For structurally distinct patterns with compatible shapes, link successfully even when their matches may overlap. During a call, choose the existing shape stratum and at most the first matching clause of each unit; if two or more units match, emit deterministic clause-ambiguity diagnostics, not a winner. A catch-all base clause can therefore make newly selected specializations ambiguous.
- This guarantees **no clause record is silently replaced or overwritten**, but not full observational preservation: guards or named matchers may perform effects or fail during candidate discovery, and adding an Option-aware clause may alter argument-propagation behavior as defined in R20. State the scope of determinism as *candidate selection and diagnostics after successful matching*, not guard-effect execution order.

### 8.3 Lexical immutability

- `name =: initializer` declares a *fresh* immutable binding in the current lexical scope; it cannot freeze or overwrite an already-defined same-scope name (including a parameter, import alias or builtin in that scope). A valid initializer executes exactly once.
- An explicit nested `name =:` declaration may shadow an outer binding by creating a distinct binding. Plain `name = value` retains existing nearest-binding resolution and **rejects assignment to the resolved immutable binding**, rather than implicitly shadowing it.
- Every language-visible operation that writes a binding must respect this invariant, including ordinary assignment, `use`, import aliases, named declarations and autoload/prelude publication. No operation may overwrite an existing immutable binding as an implementation shortcut. An invalid write whose target can be resolved before evaluating its initializer is rejected **before initializer evaluation and side effects**. A value's internal Ref/Cell or other permitted mutation capability is unaffected by the binding's immutability.
- Function parameters remain assignable under their current semantics unless individually declared otherwise in a separate proposal. Distinguish runtime-owned/entry prelude shadow/write-through from immutable user bindings; #1229/#1230 closeout determines the scope boundary, not this draft.

### 8.4 Closed declarations and lifetime

- A maximal consecutive run of clauses `f(pattern) =: expression` in one lexical declaration context creates **one closed callable** under **one immutable defining name**. Comments and blank lines do not break the run; any unrelated statement ends it. Validate the entire run before publishing its binding. A completed REPL submission terminates the run and cannot be reopened by a later submission.
- A mixed `=`/`=:` run is invalid; reintroducing `f` as another same-scope declaration after the group is sealed is invalid. A plain attempted rebinding of its immutable defining name is also invalid. Closedness belongs to the callable (aliases cannot extend it); binding immutability belongs to the defining lexical name (alias names keep their own assignment policy).
- Source-order matching, grouped patterns, recursion/TCO, annotations and doc metadata should retain currently accepted ordinary-function behavior. Do not import R20's stricter `open`-header-capture, `@doc`/`@meta`-only, or no-inline-doc rules automatically into ordinary declarations.
- **Local named functions:** preserve currently accepted lexical factories and distinct captured callable instances. Do not assign per-execution local closures the global module/export interface key and do not permit cross-module `extend` of such instances. The precise local clause accumulation policy and direct-IR carrier are design prerequisites, not inferred from top-level interface identity.

### 8.5 Portability, migration and evidence boundaries

- This is a **portable semantic change**, not a Python-only parser rewrite. The design phase must define source syntax, lowering, direct-IR validation, stable identity, immutable binding storage and normalized diagnostic identities *independently* of any host's implementation.
- The implementation phase cannot start until supported Python/C++ behavior is mapped to existing R16 shared specs and capability claims, with owned and removal-conditioned known gaps for unsupported host surfaces. No host may mask regressions in an already supported ordinary-function surface.
- Inventory existing ordinary grouped bodies, free header captures, alternate function syntaxes (`=`, `->`, block), `@category`/`@route`/`@test` and other annotations, inline docstrings, public prelude functions and autoload behavior. Preserve old accepted forms unless an explicitly approved breaking change records migration and shared cases.
- #1251 must audit cross-unit collision/shape behavior, `true` vs `1` matching-key agreement, all binding-writing operations, atomic closed groups, REPL boundaries, linked view aliasing, source/direct-IR conformance, Python/C++ host truth, plus synchronization of `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, semantic registry and generated MCP language profile **after verified implementation**.

### 8.6 Concrete approval checklist

| Decision | Candidate | Approval status |
| --- | --- | --- |
| Default cross-module eligibility | All exported module-owned ordinary open functions; explicit consumer `use` | Model B direction selected; exact contract not yet approved |
| Fixed/varargs cross-unit conflict | Reject at link-time for fixed n vs varargs m <= n in different units | **Awaiting explicit approval** |
| Cross-unit duplicate keys | Tagged portable structural key, reject atomically at link-time | **Awaiting explicit approval** |
| Guards/free variables | Syntactic key only, not semantic equivalence or disjointness proof | Awaiting explicit approval |
| Immutability enforcement | Every binding writer, reject known invalid writes before initializer | **Awaiting explicit approval** |
| `=:` closed function | Immutable defining name plus sealed multi-clause callable, one source/REPL group | Awaiting explicit approval |
| Existing ordinary syntax | Preserve grouped body/header bindings, annotations, documentation, alternate spellings | Awaiting compatibility evidence and approval |
| Local function identity | Distinct invocation-captured callable instances, no external extension target | Awaiting design proof |
| IR and multi-host evidence | Portable contract first, shared specs, exact host support/gaps; no IR-breaking shortcut | Awaiting design and evidence |

**Decision gate:** Independent review remains **REVISE**, and #1249 remains **NO-GO** for #1250 until all must-approve rows are reviewed, any disputed semantics receive an explicit maintainer decision, and a fresh independent contract review returns PASS. #1229/#1230 work and the independent R29 fallback closeout gate are not modified or subsumed.

## 9. Third-review candidate: observable decisions from second Codex REVISE (NOT APPROVED)

Independent second review of commit `3fa80b3` found the earlier shape-conflict and all-writer immutability invariants satisfactorily specified in the draft. It still returned **REVISE**, because observable binding placement, ordinary-open declaration accumulation, annotation evaluation, and nested named function syntax remained unclear. The following proposals explicitly fill those gaps, superseding §§8.1, 8.3, and 8.4 only where more specific. Maintainer acceptance and independent re-review are still required.

### 9.1 Immutable declarations and runtime-owned names

- `name =: initializer` declares in the **current lexical declaration scope**, *not* via the nearest-existing-binding `=` routing. An existing binding in that same declaration scope causes a duplicate-binding error before evaluating the initializer.
- **Conservative reserved-runtime-name exception:** in an entry program, names owned or reserved for runtime/prelude publication in parent runtime scope are not eligible for a new `=:` declaration in the entry scope, even when the prelude entry has not yet been lazily materialized. Reject them deterministically **before** evaluating an initializer. For example, `print =: 7` is rejected rather than freezing or replacing `print` in runtime scope or shadowing it in entry scope. This restriction does not prohibit ordinary nested `=:` shadowing of a non-reserved outer user binding.
- When `name` is a non-reserved name already declared in an outer lexical scope, explicit nested `name =:` creates a distinct local immutable binding, leaving the outer binding unchanged; plain `name = expr` still resolves the nearest existing binding and respects its immutability. Parameter bindings remain mutable.
- This **changes/adds observable entry declaration restrictions** and therefore requires explicit owner approval, exact identification of reserved runtime/prelude names (including unloaded names), and shared source/direct-IR evidence. Do not silently change existing `=` runtime-owned write-through routing, nor confuse #1229/#1230 scope closeout with approval of new `=:` semantics.

### 9.2 Ordinary open function base-unit lifetime and aliases

- Module-owned ordinary `f(...)` declarations of compatible clause shapes belong to **one base unit per function identity**, including **noncontiguous** declarations separated by ordinary statements. Clauses append in source execution order; repeated same-key clauses remain errors, and mixed closed/open declarations of the same binding remain invalid.
- During **declaration/initialization of the defining module or entry**, the base unit is an incrementally assembled, identity-bearing callable interface. Calls and aliases observe only clauses already published at the current execution point. A plain `a = f` binds the *same callable interface identity*, not a snapshot, so a later `f(x,y) = ...` makes the additional arity visible through `a`, preserving existing observable ordinary-function behavior.
- For the executable baseline `f(x)=x; a=f; f(x,y)=x+y; a(1,2)`, the result is `3`. Likewise `f(x)=x; unrelated=3; f(x,y)=x+y; f(1,2)` returns `3`. Prior calls made before later declarations are not retroactively changed.
- The module's base unit reaches its completed ordinary declaration state when the defining module's top-level evaluation finishes successfully; entry/REPL sessions may accept subsequent declarations according to existing session semantics, and earlier same-interface aliases continue observing additions. Exported module interfaces expose the completed base unit to external `extend`/consumer `use`.
- A consumer-local `use` creates one **immutable linked view of the selected clause set**, never a writable reference to a global contribution registry. Existing already-linked views are unaffected by later contributions, ordinary imports, or another module's future changes. This distinction between *local declaration-time accumulation* and *immutable linked views* is essential: the no-overwriting rule protects clause records and selected views, not the existence of later legitimate same-unit clause additions.
- Metadata and annotations preserve **existing ordinary function evaluation timing and documented ownership** for existing source forms. An interface's module-owned documentation/provenance identity is stable, but the exact metadata update rules for noncontiguous later ordinary declarations must be stated and conformance-tested against the existing ordinary-function baseline; do not apply the current R20 first-`open`-only metadata restriction blindly. **Review-required choice:** preserve existing ordinary later-annotation evaluation and metadata behavior for the initial transition; if this conflicts with immutable R20 interface metadata, use a documented compatibility rule rather than introducing silent changes.
- Do not expose a partially initialized imported module as a valid cross-module `extend` target or link a view before its own module initialization has completed. Implementation mechanisms can be settled during design; these execution observations are part of the contract.

### 9.3 Closed function annotations and atomic publication

- A maximal contiguous `f(...) =:` group is **structurally validated in full first** (shape, duplicate keys, mixed operators, permitted metadata and same-scope declaration collision). Structural failures publish no binding and evaluate no clause bodies or annotation expressions.
- On structural success, a **provisional self-referential closed callable binding** becomes visible *to that declaration's annotation expressions and recursive function bodies*. Evaluate existing permitted annotations in source order using that provisional binding; then atomically commit the finished **immutable defining name** and immutable closed callable metadata.
- **Annotation failure:** if any annotation expression raises or fails validation, withdraw the provisional name and publish **no completed lexical binding**. Side effects that actually occurred during annotation evaluation retain ordinary effects; rollback applies to *binding publication*, not arbitrary effects or external IO. The same declaration name may be retried by a later submission only under existing REPL/session error-recovery rules. No stale partial metadata survives.
- The proposed `@doc f(0); f(x) =: "self documentation"` may evaluate `f(0)` against the assembled provisional function before final publication, retaining self-reference ergonomics. An attempt to modify the provisional binding from an annotation must be rejected as a protected write. Clause bodies themselves are not evaluated merely to construct a definition, except when explicitly invoked by an annotation.
- Completing a REPL submission seals the closed clause group. A later submission cannot append to, reopen, or rebind its immutable defining name. Aliases never turn its closed callable into an externally extendable interface.

### 9.4 Nested named-function boundary

- This release **does not add nested named function declarations** of the form `make(k) = { f(x) = x + k; f }`. The currently rejected form remains rejected. Ordinary lexical factories returning lambdas remain supported unchanged; a lambda returned on each call captures its own environment and is not automatically eligible for module-owned `extend`/`use`.
- Local expression-level `name =: expr` immutable values are within scope, but do not implicitly authorize nested `f(...) =` or `f(...) =:` statement syntax. A future local-named-function feature requires its own explicit scope and identity contract.

### 9.5 Third-review acceptance examples and gating

| Proposed source situation | Exact proposed observation | Remaining approval/evidence |
| --- | --- | --- |
| Entry `print =: 7` | deterministic reserved-name declaration rejection before initializer | owner approval; runtime/prelude reservation registry boundary |
| Entry unloaded prelude name `name =: side_effect()` | same reserved-name rejection without evaluating initializer | evidence for lazy names |
| Nested ordinary `x =: 1` where outer user `x` exists | distinct local shadow; outer unchanged | lexical scope cases |
| `f(x)=x; a=f; f(x,y)=x+y; a(1,2)` | `3`; alias retains interface identity and sees later arity | source and direct-IR evidence |
| `f(x)=x; unrelated=3; f(x,y)=x+y; f(1,2)` | `3`; noncontiguous accumulation | grouped and annotation compatibility |
| A call to `a(1,2)` **before** second arity declaration | existing no-matching/arity behavior; no future clause visible | execution ordering |
| Existing ordinary later annotations | retain current timing and ownership; exact metadata rules to be derived before final approval | **open review item** |
| `@doc f(0); f(x) =: "self documentation"` | annotation sees provisional closed callable | annotation self-call and failure evidence |
| A closed declaration whose annotation fails | error and no completed function binding; effects already run persist | session and effect ordering |
| `make(k) = { f(x)=x+k; f }` | rejected, as at baseline | no accidental nested named-function expansion |

**Approval status:** This is a third-review **candidate only**, not an approved semantic choice or a merged language contract. The ordinary *later-declaration annotation/metadata* compatibility rule is still specifically flagged for verification against the current implementation and subsequent explicit wording. Do not begin #1250 tests/implementation, claim PASS, or merge #1255 as an approved contract until that rule and the other maintainer-visible choices are resolved and independent review returns PASS. #1251 must include every acceptance case above, alongside §8.5's shared-spec, host-truth, documentation and MCP language-profile synchronization obligations.
