# #1269 / #1250 — Model B Slice C pre-flight (default-open ordinary functions and pattern/guard-headed functions)

**Status: PRE-FLIGHT ONLY. No RED, no GREEN, no production, test, spec, manifest or implemented-truth change accompanies this document.**
**Gate: implementer recommendation = CONDITIONAL GO (see §12). This is *not* the independent gate; a separate reviewer must return GO before any RED commit.**

| Item | Value |
| --- | --- |
| Tracking issue | [#1269](https://github.com/m0smith/genia-2026/issues/1269) (child of [#1250](https://github.com/m0smith/genia-2026/issues/1250)) |
| Base | `main` at `6d50a36d23cc4b894f0456ee502deb5d7796e99b` (merge of PR #1262, Slice B) |
| Prior slices | A: PR #1260 (parser/Core IR); B: [#1261](https://github.com/m0smith/genia-2026/issues/1261) / PR #1262 (immutable bindings) |
| Authority | Contract #1255 (`docs/design/pre-r29-default-open-and-immutable-binding-contract-DRAFT.md`, maintainer-approved 2026-10-16); design #1259 (`...-design.md`, incl. §13 corrections); implemented truth = `GENIA_STATE.md` |
| Companion | `issue-1269-slice-c-red-test-plan.md` (RED inventory, host plan, documentation plan) |
| Roles | Implementer/pre-flight owner: Claude. Independent reviewer: **not yet assigned**. Integration owner: m0smith. Nothing here is reviewer approval. |

Evidence rules used below: "**observed**" = I ran the probe on the Python host at the base SHA; "**read**" = read from source/docs; "**to verify**" = not yet executed and must be characterized in the RED baseline before being asserted.

---

## 1. Authoritative state (Step 1)

Read in order: `AGENTS.md`, `GENIA_STATE.md` (§3 Model B block, §4, §4.7), `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, `docs/process/run-change.md`, `docs/process/00-preflight.md`, `docs/process/extensions/portability-analysis.md`, `docs/ai/LLM_CONTRACT.md`, the contract, the design, merged Slice A/B code and shared specs, and issues #1250/#1261.

### 1.1 What `main` actually implements (read + observed)

- Slice A: `=:`, atomic closed groups and ordinary pattern/guard headers **parse and lower** to `IrImmutableBind`, `IrClosedFuncDef`, `IrPatternFuncDef` (`src/genia/ir.py:304-331`, `lowering.py:246-250`); `assert_portable_core_ir` validates them (`ir.py` ~463-495). Pattern headers reject `->`/grouped bodies at parse time; their post-`=` string is a body, never documentation (STATE §3).
- Slice B: `IrImmutableBind` executes (`evaluator.py:_eval_immutable_bind`), Env-owned binding policy, optional capability `immutable_bindings` (Python supported, C++ listed gap → #1261 / genia-cpp#50).
- **Slice C territory is a single explicit stub**: `evaluator.py:1362-1367` raises `model-b-not-implemented: declaration evaluation is not available` for `IrPatternFuncDef` and `IrClosedFuncDef`. Same stub guards route/server/CORS discovery (`server_route_binding.py:206-214`, `server_cors_binding.py:177-185`, `server_config_binding.py:213-221`).
- **Ordinary functions already accumulate live and noncontiguously** (observed): `f(x)=x; a=f; f(x,y)=x+y; a(1,2)` → `3`. `GeniaFunctionGroup` (`callable.py:238`) is a **dict keyed by required arity**; `add_clause` raises `Duplicate function definition: f/N` on any second clause with the same required arity.
- Explicit R20 `open` is a separate construction (`GeniaOpenFunction`, `OpenClauseRecord`, `_dispatch_open`, `_first_unit_match`, `callable.py:619-960`); `open` after an ordinary same-name function → `open-function-redeclaration` (observed); a bare clause after an `open` run has ended → `open-function-redeclaration … already declared open` (observed).

### 1.2 Historical/superseded text that must not be mistaken for current gates

| Source | Stale statement | Current truth |
| --- | --- | --- |
| Design §11 and header | "CONDITIONAL GO ONLY … A red-test gate remains closed until build CI passes" | Slice A and B have since merged; §11's "exact next bounded task" was Slice A and is spent. |
| Design §2 | "Inspection baseline `95213d1`" | `main` is `6d50a36`. |
| Design §3.3 vs §13.2 | §3.3: "Reserve `0.2.0`… C must make the semantic version transition explicit"; §9 row C repeats it. §13.2 says "Do not unilaterally require Core IR 0.2.0". | §13 states it supersedes conflicting earlier wording. Manifest `core_ir_version` is still `0.1.0` (read). **Open decision D6** (recommendation: no bump in C). |
| Design §9 row C | "module completion projections available for D" listed under C | Recommend moving the frozen-projection work to D (§3.3, D7). |
| Design §3.2 | optional `pattern`/`guard` on `IrFuncDef` | Superseded by §13.2 `IrPatternFuncDef`; implemented that way in Slice A. |
| Contract header | "NOT IMPLEMENTED" | True for D/E and for C; no longer true for `=:` (Slice B). STATE is authoritative. |
| #1261 body | Unchecked acceptance boxes, "GO before RED", "Excluded: Slice C" | PR #1262 merged; #1261 remains open only administratively. None of its gates apply to C. |
| #1250 body | "Status: Proposal; not implemented", broad "Scope includes" | Parent tracker; split into slices; do not close. |

No stale document is edited by this PR (documentation-only, process evidence only).

---

## 2. Pre-flight template (docs/process/00-preflight.md)

**CHANGE NAME:** Model B Slice C — default-open ordinary function execution and pattern/guard-headed ordinary functions
**CHANGE SLUG:** `issue-1269-model-b-slice-c`

**0. BRANCH.** Required: YES. The repository convention is `issue-<number>-<short-name>` (`docs/process/run-change.md`). For this *pre-flight-only* PR the harness-designated branch `claude/nice-brahmagupta-1e17ws` (cut from `main@6d50a36`) is used instead; the implementation branch should be `issue-1269-model-b-slice-c` per convention and is **not created yet**. Base: `main`. One branch per change.

**1. SCOPE LOCK.**
Includes — (a) executable ordinary pattern/guard-headed clauses (`IrPatternFuncDef` outside `IrClosedFuncDef`); (b) ordinary groups become ordered clause groups with portable typed structural duplicate keys, same-arity distinct patterns, same-required-arity fixed/varargs coexistence, noncontiguous declaration and live aliases; (c) header-frame/guard scope and single candidate-discovery evaluation; (d) declaration ownership/interface provenance on the group and the no-append-through-foreign-binding rule; (e) metadata-channel preservation for the ordinary path; (f) optional capability `default_open_functions`; (g) shared R16 + host-local RED/GREEN for the above.
Excludes — Slice D (cross-module `extend`/`use` on ordinary exports, linked views, cross-unit duplicate/fixed-varargs/ambiguity checks, frozen completion metadata snapshots); Slice E (`IrClosedFuncDef` execution, publication state machine, provisional self-identity); C++ implementation; Core IR/manifest version bump (pending D6); #1257 write-through retirement; #1268 and other maintenance; nested named declarations; `@closed`; any new runner/protocol/capability *framework*.

**2. SOURCE OF TRUTH.** `GENIA_STATE.md` → `GENIA_RULES.md` → `GENIA_REPL_README.md` → `README.md` → `spec/*` → `docs/host-interop/*` → `docs/architecture/*`. Additional: contract #1255, design #1259, `docs/design/r20-open-functions-{contract,syntax-ir-design}.md`, `docs/architecture/core-ir-portability.md`, `docs/architecture/executable-semantic-conformance.md`.

**3. FEATURE MATURITY.** Partial (Python reference host only after GREEN). Doc wording: "Python executes ordinary pattern/guard-headed and noncontiguous same-arity-distinct clauses; cross-module extension and closed functions remain unimplemented; C++ not claimed." Nothing is documented as implemented before executable evidence.

**3a. Portability Analysis** — §8 below (seven fields).

**4. CONTRACT vs IMPLEMENTATION.** Portable contract: contract §§2.1–2.3, 3, 5.1–5.2, 6.1 (as scoped in §3/§4 below). Python today: §1.1. Not implemented: everything in §3.1 "in scope" plus D/E.

**5. TEST STRATEGY.** Companion file. Core invariants: no previously valid program changes meaning except the enumerated, approved deltas (§6); every new error/success is pinned by a shared spec or declared host-local; no existing ordinary/R20 spec is weakened or reclassified unsupported.

**6. EXAMPLES.**
Minimal:
```genia
fact(0) = 1
fact(n) ? n > 0 = n * fact(n - 1)
fact(5)        # 120 (target; today: model-b-not-implemented)
```
Real (header capture preserved, noncontiguous accumulation):
```genia
area(x) = (0) -> 0 | (n) -> n * x
describe(none) = "absent"
describe([a, ..rest]) ? a > 0 = "positive-head"
describe(_) = "other"
```

**7. COMPLEXITY CHECK.** Revealing structure. It removes the special status of `open` for local dispatch rather than adding a second dispatcher: reuse R20 `_dispatch_open`/`_first_unit_match`/`eval_with_tco`; add owner/provenance to an existing object (design §1.3).

**8. CROSS-FILE IMPACT.** Likely: `src/genia/callable.py`, `evaluator.py` (IrFuncDef/IrPatternFuncDef branches), `environment.py` (`define_function`, ownership), `builtins.py` (help/doc/meta/reflection), `http_annotation_binding.py`, `server_route_binding.py`, `lifecycle_binding.py`, `test_cli.py`, `interpreter.py` (main group), `values.py`/`equality.py` (rendering/identity), `optimizer.py` (verify no function-body/declaration reordering), `spec/*`, `spec/manifest.json`, `spec/known_host_gaps.json`, `hosts/python/*` (capability claim), tests. Risk of drift: **High** (callable core; many arity-dict consumers; documentation surfaces).
MCP language-knowledge impact: **Affected.** `idioms.clauses` currently states that executable clause dispatch needs explicit `open` and that pattern/guard headers reject evaluation; `supported_forms`/examples may change. Update STATE, the `mcp_language_profile` registry in `docs/contract/semantic_facts.json`, and regenerate `apps/mcp/mcp.genia` via `tools/gen_mcp_language_profile.py` — **only after** verified GREEN. Not regenerated now.

**9. DOC DISTILLATION CHECK.** Creates process artifacts: YES → Doc Distillation required at the end of the implementation PR. Adds docs/design or docs/architecture files: NO (these files live in `.genia/process/`, process evidence, not authoritative semantics). Doc drift risk: **High**.

**10. PHILOSOPHY CHECK.** Preserves minimalism: YES (reuses dispatcher; no `@closed`). Avoids hidden behavior: YES *provided* D1/D5 are decided explicitly rather than inherited silently. Keeps semantics out of host: YES (portable keys, shared specs). Pattern-matching-first: YES.

**KILLER WORKFLOW ALIGNMENT.** Indirectly. Pattern-headed clauses let record-parsing/validation stages dispatch on `some`/`none`/`err` and record shapes without the `open` ceremony, supporting Outcome-aware validated pipelines (Outcome, validation, diagnostics). Required non-regression: `docs/strategy/killer-workflow.md` pipeline specs.

**11. PROMPT PLAN.** Preflight (this) → independent review/GO → decisions D1–D7 → RED (shared + host-local, separate commit) → GREEN → maintainability review → docs sync → skeptic audit → distillation → final-head CI. No contract/design re-run is needed unless a decision below changes approved semantics (then back to #1249).

**12. HOST PARITY / CONFORMANCE.** Affected hosts: Python (implement), C++ (honest gap). Changes portable semantics: **YES**. Spec/conformance tests: RED plan. Python updated: after GO. C++ updated: **no**; optional `default_open_functions` unsupported + issue-backed `spec/known_host_gaps.json` entry added with the RED commit. Cross-host behavior verified: not claimed. Can one host merge before the other: YES with the gap entry (the capability is optional, as in Slice B). Temporary compatibility note: C++ pattern-header parsing is already UNSUPPORTED (Slice A, genia-cpp#50); C++ ordinary functions continue to behave as today.

---

## 3. Slice C boundary (Step 2)

### 3.1 Behavior in scope (exact)

1. **Ordinary functions open by default (local).** A named ordinary function declared with `=`/`->`/block remains one live identity-bearing group. Later same-scope declarations of the same name append in execution order, noncontiguously, and aliases bound before an append observe it. A clause is not visible before its declaration executes. *Most of this is today's behavior; Slice C turns it into a contract-backed, evidenced guarantee (regression-guard specs) and extends it to pattern clauses.*
2. **Executable pattern/guard headers.** `IrPatternFuncDef` (one full tuple pattern, optional `? guard`, `=` body) installs a clause into the same group. The header frame is the pattern's bindings; the guard sees them; the body sees them; match-local bindings shadow outer names (design §13.4).
3. **Multiple clauses, order, dispatch.** Within the group: shape stratum first (fixed arity `n` if any fixed clause of arity `n` exists, else eligible varargs with a single distinct minimum), then first matching clause in declaration order. Fixed stratum does **not** fall through to varargs on pattern miss.
4. **Ambiguity.** Within one unit there is no clause ambiguity (first match wins). Varargs ambiguity (more than one distinct eligible minimum) is retained. **Clause ambiguity requires more than one participating unit and therefore cannot occur in Slice C.**
5. **Duplicate keys.** Rejected at declaration (before the clause becomes visible) using the portable typed, scope-aware structural key (design §5.4/§13.4). Bodies and closures are excluded; nothing is evaluated.
6. **Noncontiguous declarations; arity; varargs.** Preserved; same-required-arity fixed + varargs now coexist.
7. **Explicit R20 `open`.** Unchanged construction, syntax, contiguity, metadata policy and diagnostics (one approved exception: key encoding, D4).
8. **Closures, recursion, identity.** Each clause captures its declaring environment; recursion/TCO via the existing trampoline; re-evaluation of a declaration in a fresh scope creates a fresh group identity; aliases preserve R18 callable equality.
9. **Guard scope/side effects.** Candidate discovery evaluates matchers/guards once, in declaration order, stopping at the first match; the retained bindings are reused by the body (no second evaluation). Failures/effects of guards are not rolled back.
10. **Metadata.** Three channels preserved (binding annotations, inline docs, shared help) with annotation publication per contract §5.2 (install clause first, validate annotations in order, stop at first failure, attach once).
11. **Immutable-binding interaction (Slice B).** A function declaration (legacy or pattern-headed) cannot overwrite an immutable binding or be declared over one; `x =: …` cannot be declared over an existing function name; checks run before annotations and before clause installation.

### 3.2 Explicitly excluded

Slice D and E items listed in §2.1; closed `f(...)=:` (stays `model-b-not-implemented`, including a pattern child *inside* a closed group); `extend`/`use` targeting of ordinary groups (stays `open-function-target-not-open` / current behavior); changes to `GeniaOpenFunction`/`GeniaLinkedOpenFunction` semantics.

### 3.3 Prerequisite vs deferred module-contribution aspects (dependency analysis for D/E)

| Contract aspect | Needed for coherent *local* default-open? | Decision |
| --- | --- | --- |
| Interface provenance `(canonical module identity, defining name)` recorded on the ordinary group | Yes — needed so the no-append-through-foreign-binding rule can be decided and so D has a stable provenance. Cheap and local. | **C** |
| Declaration ownership (append only through the declaring scope's own binding) | Yes — see D5; it is where default-open first changes valid programs (cross-module append via alias is currently *possible*, §6 B4). | **C** |
| Frozen exported projection at module completion (clauses + three metadata observations) | No consumer exists until `use` can link an ordinary base. Untestable in C without inventing a consumer. | **D** (design §9 row C lists it under C — flagged D7) |
| `extend` of an ordinary export; `use` over an ordinary base; linked-view construction | No | **D** |
| Cross-unit duplicate / fixed-vs-varargs conflict / clause ambiguity | No (single unit) | **D** |
| Portable structural key walker | Yes (within-group duplicate detection) | **C**; D reuses it unchanged |
| Re-export provenance retention | Only the field; semantics are exercised by `extend`/`use` | field in **C**, behavior **D** |
| Selection/import non-activation | Unchanged behavior | regression guard in **C** |

**Conclusion:** Slice C is implementable coherently without any portion of Slice D, *provided* provenance + ownership are in C and the frozen projection is deferred. Dependency on **Slice E: none** (closed groups stay unimplemented). **Dependency report:** if the reviewer rejects D7, C must additionally freeze a read-only projection at `Env.load_module` completion; that is the only identified cross-slice coupling and would add ~one module-load hook and its tests.

---

## 4. Contract-to-implementation traceability

| Contract / design | Requirement | Implementation surface (read) | RED family (companion) |
| --- | --- | --- | --- |
| C §2.1 | Module-owned ordinary named function is open by default; explicit `open` unchanged | `callable.GeniaFunctionGroup` (+ owner/provenance), `environment.define_function`, `evaluator` IrFuncDef/IrPatternFuncDef branches | C-OPEN, C-R20 |
| C §2.1 | Lambdas/builtins/host callables/factory instances get **no** interface identity | `callable.py`, `builtins.py:_host_function_group` (host groups) | C-IDENT |
| C §2.2 | Noncontiguous accumulation; alias sees later arities; no early visibility | `define_function` (existing) | C-ACC |
| C §2.2 | Preserve header captures, `=`/`->`/block, inline docs, `@category/@route/@test`, annotation timing; **do not lower via `IrOpenFuncDef`** | evaluator IrFuncDef branch; `open_header_capture.py` not applied to ordinary | C-META, C-HDR |
| C §2.2 | Nested named declarations remain unsupported; lambda factories distinct | parser (existing) | C-IDENT |
| C §2.3 | Duplicate key within a unit rejected at construction; typed literals; alpha normalization; no evaluation | new portable key walker replacing `_open_dispatch_key`/`_structural_key` | C-KEY |
| C §2.3 | Within-unit R20 shape precedence preserved; first match wins | `_dispatch_open` reuse | C-DISP |
| C §2.3 | Cross-unit rules | — | **Deferred to D** |
| C §3 / design §4 | Immutable bindings not overwritten by named declarations; checks before effects | `Env._reject_immutable_write` (Slice B) | C-IMM |
| C §5.1 | Three metadata channels for ordinary functions | `Env.merge_binding_metadata`, `GeniaFunctionGroup.merge_metadata/_merge_docstring`, `builtins` doc/meta/help | C-META |
| C §5.2 | Install clause, then ordered annotation validation, atomic attach | evaluator IrFuncDef branch (`eval_annotations`) | C-ANN |
| C §5.3 | Linked-view metadata | — | **Deferred to D** |
| C §6.1(2) | Core IR carriers host-neutral, no opportunistic rewrite | existing Slice A carriers; no new node | C-IR |
| C §6.1(3-5) | Shared R16 cases; capability reuse; host truth | `spec/`, manifest, `known_host_gaps.json` | all |
| D §13.4 | Header frame once per call; match-local shadows header; guard evaluated once; preserve legacy ordinary error identities; new `open-function-*` for new cross-unit errors | record adapter over `OpenClauseRecord` + header frame | C-HDR, C-ERR |
| D §13.3 | Optional capability `default_open_functions`; C++ unsupported with owned gap | manifest + known gaps | host plan |
| D §13.5 | Inventory `iter_ir_nodes`, optimizers, `server_route_binding`, native test discovery, `tools/code_documentation.py` | listed in §5 | C-IR, C-CONSUMER |

---

## 5. Parser / Core IR / runtime impact

**Parser.** No change expected: Slice A already parses pattern headers into `PatternFuncDef` (`parser.py:502`) and rejects `->`/grouped bodies/`->` after pattern headers. Legacy identifier headers keep `FuncDef`. *Verification item:* confirm that every `ParseError` that today blocks a would-be-valid ordinary clause form is intentional (e.g. `f((a, b)) = a` → "Invalid pattern token '(' (LPAREN)" observed; supported literal/list/map/`some`/`err`/named forms are those of the Slice A `model-b-a-pattern-*` cases) — no parser edits in C.

**Core IR.** No new node families, no new fields. `IrPatternFuncDef` outside a closed group becomes executable. `IrClosedFuncDef` children are never independently evaluated (E). Wire shapes and the byte-stable legacy `IrFuncDef` snapshot are unchanged. Core IR version label: **D6**. `iter_ir_nodes`, `assert_portable_core_ir`, optimizer and `_MINIMAL_PORTABLE_NODE_FAMILIES` already include the Slice A carriers (read); the RED plan adds a traversal/optimizer non-reordering regression.

**Runtime (Python).**
- `GeniaFunctionGroup` can no longer be only `dict[arity → GeniaFunction]`: distinct same-shape patterns need an ordered record list. Proposed (implementation choice, not contract): keep `functions` as a *derived index for legacy identifier-header fixed clauses* so existing consumers keep working, and add an ordered `records` list plus owner/provenance.
- Clause records reuse `OpenClauseRecord` extended with the ordinary header frame (design §5.2), dispatch via `_dispatch_open` machinery; `GeniaFunctionGroup.__call__`, `invoke_callable._resolve_target`, `_callable_explicitly_handles_none/some`, `_body_delegates_to_option_aware`, help/doc rendering and `sorted_arities()` consumers must all agree (§6 B5/B11, D1, D3).
- Evaluator: the `IrFuncDef` branch gains ownership + key validation; a new `IrPatternFuncDef` branch (non-closed) shares the same publication/annotation path; closed-group stub unchanged.
- Environment: `define_function` already runs the immutable check, group lookup and mutation in one `_BINDING_LOCK` critical section (read, `environment.py:~640-675`); the key check must join that critical section.

---

## 6. Observed baseline and breaking-change / migration assessment

### 6.1 Observed baseline (Python host @ `6d50a36`)

| # | Program | Today |
| --- | --- | --- |
| P1 | `f(x)=x; a=f; f(x,y)=x+y; a(1,2)` | `3` |
| P2 | `f(0)=1; f(n)=n; f(0)` | `Error: model-b-not-implemented: declaration evaluation is not available` |
| P3 | `f(x)=1; f(y)=2` | `Duplicate function definition: f/1` |
| P4 | `f(a)=1; f(a, ..r)=2` | `Duplicate function definition: f/1` |
| P5 | `f(a,..r)="min1"; f(a,b,..s)="min2"; f(1,2)` | **`"min2"`** (ordinary: exact-arity key wins; sole-varargs rule) |
| P6 | same under `open f(...)…` | `open-function-varargs-ambiguity: f/2 …` |
| P7 | `f(a,..r); f(a,b,..s); f(1,2,3)` | `Ambiguous function resolution: f/3. Matching varargs: f/1+, f/2+` |
| P8 | `f(a)=1; f(1,2)` | `No matching function: f/2. Available: f/1` |
| P9 | `f(x)=x; f(none("r"))` | `none("r")` (automatic `none` propagation) |
| P10 | `f(x)=x; a=f; a(x,y)=x+y; f(1,2)` | **`3`** — declaring through an alias appends to the aliased group |
| P11 | module `lib`: `g(x)=x`; consumer: `import lib; h = lib.g; h(x,y)=x+y; lib.g(1,2)` | **`3`** — a consumer extends another module's ordinary function through an alias |
| P12 | `map(a,b,c)="mine"` at entry (prelude name `map`) | defines in runtime scope R via entry write-through; `map(1,2,3)` → `"mine"`, `map(inc,[1,2])` still `[2,3]` |
| P13 | `open f(true)=1; f(1)=2` and `open f(1)=1; f(1.0)=2` | both `open-function-duplicate-clause` (Python `True == 1` / `1 == 1.0` collision) |
| P14 | `f(x)=x; open f(0)=1` | `open-function-redeclaration … already defined as an ordinary function` |
| P15 | `open f(0)=1; g(x)=x; f(n)=n` | `open-function-redeclaration … already declared open` |
| P16 | `open gcd(a,0)=a; gcd(a,b)=gcd(b,a%b); gcd(48,18)` | `6` |
| P17 | `f(x) ? x > 0 -> 1` | parse error "pattern/guard function headers cannot use ->" |
| P18 | `print(a,b,c)="mine"` | `Cannot define function print/3: name already bound to non-function value` |

Corpus check (observed, scripted parse of every `*.genia` in the repo): 183 files, 5 unparseable (not examined individually; expected negative fixtures — **to verify**), 1,252 same-name function groups, **0 groups with two or more varargs clauses**, 0 pattern-header clauses. Scope limit: top-level `.genia` files only; Python test sources with inline Genia are not covered and must be scanned in RED baseline.

### 6.2 Does default-open change the meaning of previously valid programs?

Mostly **no**: B1–B3, B6 convert former *errors* into valid programs. **Three exceptions need explicit decisions** because they turn a valid program into an error or a different result:

| ID | Change | Direction | Affected programs | Handling |
| --- | --- | --- | --- | --- |
| **B5 / D1** | Dispatch regime for varargs: ordinary resolver picks the **exact-arity key** even when it is a varargs function (P5 → `"min2"`); R20 stratum rule raises varargs ambiguity (P6). Unifying ordinary groups on `_dispatch_open` changes P5 from a result to an error. | valid → error | any ordinary group with ≥2 varargs clauses with different minima called at an arity equal to the larger minimum | **Decision D1.** Corpus: 0 such groups in `.genia` files. |
| **B4 / D5** | Declaring `h(...) = …` where `h` is an alias of another group (same scope or imported from another module) currently appends to the *aliased* group (P10, P11). Design §4 says "Never append through an arbitrary callable alias or imported binding". P11 is an **implicit cross-module modification**, which #1250 non-goals forbid. | valid → error (proposed) | programs relying on alias-append | **Decision D5**: error identity and same-scope-alias treatment are unspecified by contract. |
| **B10 / D2** | Entry-scope ordinary declarations on runtime-owned (prelude) names write through to runtime scope R (P12). With default-open + pattern clauses, a user catch-all/pattern clause can be appended to a prelude-owned group and become reachable for runtime-internal callers. | no change in routing; **risk amplification** | user code defining a prelude name | **Decision D2.** #1229/#1230/#1257 own write-through retirement; C must not change routing silently. |

Other deltas:

| ID | Change | Direction | Handling |
| --- | --- | --- | --- |
| B1 | Pattern/guard-headed ordinary clauses execute | error → valid | New behavior; `model-b-not-implemented` retained only inside closed groups. |
| B2 | Same required arity, distinct keys (e.g. `f(0)`, `f(n)`) | error → valid | Legacy id `Duplicate function definition: f/N` retained for identical keys involving only legacy clauses (D3). |
| B3 | Fixed + varargs with the same required arity (P4) | error → valid | Document (design §13.4). Fixed stratum does not fall through to varargs on pattern miss. |
| B6 | Explicit R20 duplicate relation: `true` vs `1`, and `1` vs `1.0` (observed, P13) become distinct keys | error → valid (R20) | Design §13.4 approved delta; **D4** asks to confirm it lands in C (key walker is shared). |
| B7 | New error categories | new | D3. |
| B8 | A later clause shadowed by an earlier catch-all is silently unreachable | n/a | No warning is introduced (no invented semantics); documented in user docs. |
| B9 | `extend`/`use` against ordinary exports | unchanged in C | D. |
| B11 | Consumers keyed on `sorted_arities()`/`.functions` (`@route` requires `[1]`, HTTP annotations `[0]`, `main`, `@test`, lifecycle, `help`) | none for legacy-only groups | **D3b**: behavior for groups that contain pattern clauses (see §11). |
| B12 | Core IR label | none proposed | D6. |

### 6.3 R20 backward-compatibility matrix

| Explicit R20 surface | Slice C effect | Evidence |
| --- | --- | --- |
| `open f(...) = …` + contiguous bare clauses (P16) | unchanged | existing `r20-*` specs + `tests/unit/test_r20_*` must pass unmodified |
| grouped-body flattening into per-arm clauses, header-capture rejection (`open-function-header-capture`) | unchanged (ordinary path never applies `open_header_capture`) | `r20-open-grouped-header-*` specs; new C-HDR contrast cases |
| interface-owned metadata, `@doc/@meta` only, others rejected | unchanged | `r20-open-*metadata*` specs |
| `open` after ordinary / bare clause after ended run → `open-function-redeclaration` (P14, P15) | unchanged | new characterization specs (C-R20) |
| Duplicate-key diagnostics (`open-function-duplicate-clause`) | same category; key relation changes for `true`/`1`, `1`/`1.0` (B6) | C-KEY |
| `extend`/`use`, order independence, consumer non-transitivity, linked-view metadata | unchanged | all `r20-cross-module-*` specs (D) |
| `use` over an ordinary function replaces it undiagnosed | unchanged | characterization |
| Automatic `none`/`some` propagation over the shape stratum | unchanged for R20; extended to ordinary pattern groups (B5 family) | `r20-option-*` twins `model-b-c-option-*` |
| Tail calls (`r20-open-ordinary-mutual-tail-call`) | unchanged | existing + C twins |

---

## 7. Concurrency, reentrancy, shared mutable environment

- **Install atomicity.** Key validation and group mutation must stay inside the existing `_BINDING_LOCK` critical section of `define_function`; a racing declaration of the same key must fail exactly once and never publish a duplicate. Host-local deterministic test with barriers (as `test_model_b_slice_b_races.py`), no sleeps.
- **Dispatch vs. concurrent append.** A call must operate on a snapshot of the clause list taken at dispatch start (copy-on-write tuple), so a concurrent append (other thread/process) cannot be observed mid-iteration and a call cannot see a "future" clause. Aliases still see appends made *before* the call starts.
- **Reentrant guards/matchers.** A guard or named matcher may call the same function (recursion) or declare nothing (named nested declarations are unsupported). Candidate discovery must not hold the binding lock while running user code (Slice B rule: lock never held across user code).
- **Meta-circular writers** (`_meta_define`, `_meta_set`) must route through the same checked path (Slice B inventory); the RED plan re-asserts it for ordinary/pattern clauses.
- **No admission/state machine** is needed (that is E).

## 8. Seven-field portability analysis (docs/process/extensions/portability-analysis.md)

1. **Portability zone.** Portable language semantics (shared R16 behavior) for default-open local ordinary function groups and ordinary pattern/guard headers; plus **Python-host-only** implementation details (group record layout, lock, trampoline integration). `GENIA_STATE.md` is authoritative only after GREEN.
2. **Core IR impact.** Node families touched: `IrFuncDef` (evaluation/ownership semantics only; wire shape unchanged), `IrPatternFuncDef` (becomes executable when not inside a group), `IrClosedFuncDef` (unchanged: still rejected), `IrAnnotation` (publication timing for pattern clauses), pattern families `IrPat*` (key walker). No new nodes, no new fields. `IrOpenFuncDef/IrOpenContribution/IrOpenUse` unchanged except the shared key encoding (D4). Version label: D6.
3. **Capability categories affected.** Required: `core_ir_eval`, `doc_help` (regression guard), `parser`/`ast_lowering` (unchanged; Slice A cases must still pass). Optional: **new `default_open_functions`** (independently claimable surface per design §13.3); existing `open_functions` (regression only; not re-labelled), `repl` (persistent group growth), `multi_file_eval` (provenance/non-activation guards only). No other new capability; no `closed_functions` yet (E).
4. **Shared spec impact.** New `spec/eval`, `spec/error`, `spec/cli` (REPL) cases `model-b-c-*`; existing `spec/ir/model-b-a-*` untouched. Regression-guard cases for behavior that already works carry **no** `requires`; only new behavior is gated by `default_open_functions`. Multi-file cases use `requires: [default_open_functions, multi_file_eval]` where a module boundary is observable. See companion plan.
5. **Python reference-host impact.** `callable.py`, `evaluator.py`, `environment.py`, reflection (`builtins.py`), consumers of arity-keyed groups, `hosts/python/protocol_adapter.py` (auto-claims manifest names — **the manifest entry must be added in the same commit that makes the cases pass, or the claim is false**, per Slice B precedent where it was provisional between RED and GREEN), tests.
6. **Host adapter impact.** Python adapter: capability claim only (no protocol change; R16 protocol v1 and `contract_revision` pinning unchanged). C++ adapter: advertise `default_open_functions` **unsupported**; gap entry; no adapter change in this repo.
7. **Future host impact.** Node/Java/Rust/Go are planned only; no invented hosts. Any future host implements from the contract + shared cases without reading Python source; the portable key encoding (typed tags, binder-slot normalization, no `repr`/host equality) is the part most likely to leak host semantics and is therefore specified by value in the RED cases (C-KEY).

## 9. Host capability plan (Python / C++) and known-gap accounting

- **Python.** Claims `default_open_functions` = supported only when every `requires: [default_open_functions]` case passes at the GREEN head. No case is classified unsupported to pass; zero failures plus honest unsupported counts are both reported.
- **C++ (bounded production host, `m0smith/genia-cpp`, read-only here).** Not implemented here. Facts: C++ lacks pattern-header parsing (Slice A: 27–38 `model-b-a-*` cases UNSUPPORTED, genia-cpp#50), lacks `=:`, and `multi_file_eval` is already a listed gap. Add with the RED commit a `spec/known_host_gaps.json` entry for optional capability `default_open_functions`: `tracking_issue: m0smith/genia-2026#1269` (the parity gate requires a `genia-2026#` reference, as for `immutable_bindings`), `affected_host: cpp`, exact affected case IDs, reason, removal condition (genia-cpp declares it supported and the gate reports PARITY_OK). **Process gap to close:** a genia-cpp child issue for execution parity should be opened by the integration owner; this session's GitHub scope is `m0smith/genia-2026` only, so none is created here.
- **Existing C++ explicit-R20 duplicate-clause discrepancy** (design §13.3) is a separate pre-existing item: it must not be counted as Model B conformance nor hidden inside this gap entry.
- **Required capabilities** (`parser`, `ast_lowering`, `core_ir_eval`, `doc_help`) are not eligible for optional-gap entries; no new *required* case may be added that C++ cannot run without a documented process decision (the RED plan keeps all new eval/error cases optional-gated).
- Direct-IR twins are host-local (R16 `eval` accepts source only).

## 10. Security, diagnostics, MCP, documentation, rollback

- **Security/diagnostics.** (a) D5 closes an existing cross-module mutation path (P11) — a security-relevant ownership boundary; its error must not leak other-module paths or captured values (render canonical module identity / existing `<entry>` label only). (b) `No matching case … with arguments [...]` already uses `format_debug`; RED must assert protected (R10) sentinels do not appear in pattern-group diagnostics. (c) D2 amplification: prelude-name write-through lets user pattern clauses reach runtime-internal callers; not widened silently. (d) Key walker rejects malformed structures deterministically (no `repr` fallback). (e) No diagnostics include filesystem paths or object addresses.
- **MCP.** Affected as in §2.8; held until GREEN. `genia_language_profile` must keep telling clients that explicit `open` still works and that `extend`/`use` and closed functions are not available.
- **Documentation plan.** Companion file §4. No authoritative document is changed by this PR.
- **Rollback/failure containment.** Slice C changes are confined to the ordinary group record, key walker and two evaluator branches. Rollback = revert the implementation PR together with the `default_open_functions` manifest/gap entries and docs; no persisted state; Slice D must not start before C's identity/provenance fields are final (design §9: C and D roll back together once views ship). Failure containment inside a run: a rejected declaration installs nothing (duplicate/ownership/immutable checks precede clause publication; annotation failure leaves the already-installed clause, per contract §5.2). Earlier effects are not rolled back.

## 11. Outstanding semantic decisions (not mine to invent)

| ID | Decision needed | Why unresolved | Implementer recommendation |
| --- | --- | --- | --- |
| **D1** | Dispatch regime for ordinary groups: unify on R20 shape-stratum (changes P5 from `"min2"` to varargs-ambiguity error) vs keep the legacy exact-key/sole-varargs resolver for legacy-only groups vs a hybrid. | Contract §2.2 says "currently accepted ordinary behavior"; §2.3 says "within-unit R20 shape precedence is preserved"; design §13.4 only lists the *same-required-arity* delta. P5 is not documented as an approved delta. | Unify on the stratum rule (one dispatcher, design §1.3/§5.2) **and** record P5 as an explicit approved breaking delta (corpus evidence: 0 occurrences in `.genia` files), preserving the legacy `Ambiguous function resolution` text where legacy-only groups hit ambiguity (P7). If maintainer refuses any valid→error delta: hybrid (legacy resolver iff group has no pattern clause) with a documented two-regime caveat. |
| **D2** | Entry-scope ordinary/pattern declarations on runtime-owned (prelude) names: keep write-through (P12) or reject pattern-headed clauses there (mirrors Slice B `=:` reserved-name rule)? | Contract: "does not change #1229/#1230 scope behavior". | Keep routing exactly as today (no new semantics); add characterization + a negative regression that prelude-internal callers are not redirected for *existing* clauses; flag residual amplification for #1257. Reviewer may instead choose rejection. |
| **D3** | Error identities for **new** in-group failures: duplicate key involving a pattern clause; no matching shape; no matching case; plus (D3b) how arity-keyed consumers (`@route`, HTTP annotations, `main`, `@test`, lifecycle, `help`) treat groups that contain pattern clauses. | Design §13.4 fixes only legacy-preservation and new *cross-unit* ids. | Duplicates: legacy `Duplicate function definition: f/N` for legacy-only keys, `open-function-duplicate-clause` otherwise; shape/case: existing `No matching function…`/`open-function-no-matching-case`. D3b: `sorted_arities()` returns the distinct required arities of all records; consumers continue to require their exact arity set; pattern-headed `@route` handlers dispatch through the group. Requires explicit confirmation. |
| **D4** | Land the portable key walker (replacing `_open_dispatch_key`) in C, thereby changing explicit-R20 duplicate relation for `true`/`1`, `1`/`1.0` (B6)? | Approved in design §13.4 as a delta but not scheduled to a slice; a second key service is forbidden. | Yes, in C; log the delta; characterize current R20 behavior first (P13 observed both collisions). |
| **D5** | Declaration through (a) an alias in the same scope and (b) an imported binding: error identity, and whether (a) keeps historical append (P10) or is rejected. | Contract §2.2 is silent; design §4 table says "never append through an arbitrary callable alias or imported binding". | Reject (b) with a normalized ownership error (closes P11). Treat (a) as reject too, for one rule ("a declaration appends only to the group its own binding owns"), recorded as a breaking delta; if maintainer wants (a) preserved, keep P10 and test it. |
| **D6** | Core IR/manifest version label in C (design §3.3/§9 vs §13.2). | Internal contradiction. | No bump in C (§13 supersedes); revisit at integration (#1251). |
| **D7** | Whether frozen module-completion projections belong to C (design §9 row C) or D. | Row C lists them; no consumer exists in C. | Defer to D (§3.3). |

None of D1–D7 requires editing the approved contract *except* if the maintainer judges D1/D5 to be semantic changes rather than implementation choices — in that case they return to #1249 first (stop condition, design §11).

## 12. Gate recommendation

- **Implementer recommendation: CONDITIONAL GO** to proceed to RED *after* (i) independent review of this pre-flight returns GO, (ii) D1, D3, D5 are decided (D2, D4, D6, D7 may be accepted as recommended), and (iii) the RED baseline characterizes the remaining "to verify" items (the 5 unparseable corpus files; inline Genia in Python tests).
- **NO-GO triggers:** a reviewer finding that C requires frozen projections or any `extend`/`use` change; or that D1/D5 are unapproved semantic changes (→ #1249).
- **Not self-certified.** Reviewer approval, if any, is recorded separately by the independent reviewer; nothing in this file claims it.
- Stop point reached: no RED/GREEN, no merge, #1250/#1261 untouched except a tracking comment on #1250.
