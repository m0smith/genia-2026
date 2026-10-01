# Unified Function Model — Contract Gate Report

> **STATUS: PROPOSED / NON-AUTHORITATIVE — not adopted. `GENIA_STATE.md` remains final authority for implemented behavior.**
> This is an analysis-only gate investigation. It changes no runtime, parser, IR, or source-of-truth document, marks no roadmap work complete, and approves no syntax. Every claim about current behavior is either cited to a file/line on `main` at `495bffd` or was reproduced by a direct interpreter probe (Python reference host, `genia.interpreter.run_source` with real multi-file modules) during this investigation. Where evidence could not be obtained, it is marked **EVIDENCE GAP**.
>
> **Relevance re-check (2026-10-01):** `origin/main` has advanced 132 commits past `495bffd` (to `509ab5f`) since this report was produced. Every file this report cites — `src/genia/callable.py`, `evaluator.py`, `environment.py`, `parser.py`, `lowering.py`, `ir.py`, `optimizer.py`, `hosts/python/ir_normalize.py`, `hosts/python/parse_adapter.py`, `examples/ollama_chat.genia`, `tests/unit/test_r20_open_functions_cross_module.py`, `tests/unit/test_callable_runtime.py`, `docs/design/r20-open-functions-contract.md`, `docs/design/r20-open-functions-syntax-ir-design.md`, and `docs/analysis/r20-release-truth-audit.md` — has **zero diff** between `495bffd` and `509ab5f`. `AGENTS.md`, `GENIA_STATE.md`, `GENIA_RULES.md`, the release roadmap, the parking-lot doc, `docs/releases/R24.md`, `HOST_CAPABILITY_MATRIX.md`, and `spec/manifest.json` changed, but only to record R25/R26/R27 release completions (C++ stateful runtime/concurrency, C++ REPL/data bridges, C++ Flow/pipe mode) and a new **R26+ Change Pre-Flight Gate** process requirement (`AGENTS.md`); none of those edits touch R20, `open`/`extend`/`use`, or function-model content. Conclusion: **every finding and the final recommendation below are still current.** The one new fact to carry forward is procedural, not substantive: any future implementation slice from section 30 must now also complete the `GENIA Change Pre-Flight` issue template per `docs/process/run-change.md` before work begins. The two evidence gaps from the original investigation (the Codex audit's unreadable attachments on issue #1008, and the uninspected `genia-cpp` source) remain open and were not re-attempted in this re-check.

---

## 1. Executive conclusion

The hypothesis "ordinary functions and `open` functions should be one semantic kind, so `open` becomes unnecessary" **splits into two claims that must be judged separately**, and they get opposite verdicts.

1. **"There should be one Function kind."** This **survives**. Today's split is mostly an implementation artifact, and it has real bugs. Ordinary functions are an arity-keyed dict of single-body `GeniaFunction`s (`src/genia/callable.py:195-259`). Open functions are an ordered clause list behind a separate dispatcher (`src/genia/callable.py:596-641`). The two have diverged observably in six places (section 5). The open path also lacks features that ordinary functions have: mutual tail calls, per-arity none-awareness, docstrings/`@doc`, debug hooks, and Flow fusion. A single Function made of ordered Clauses, with one dispatch algorithm, explains both. The ordinary case is the one-unit, one-clause-per-shape special case of R20's §5 algorithm. The only exception is a dict-key artifact.

2. **"Therefore `open` is unnecessary."** This **does not survive**. In Genia today every top-level binding of a module is exported (`GENIA_RULES.md:313`; `src/genia/environment.py:257`), and no public/private marker exists (`GENIA_STATE.md:268`). That means Options A ("public implies targetable") and C ("anything resolvable is targetable") are the same rule: every top-level function of every module becomes a contribution target. The declaring author can no longer say "this is an extension point". The project has already recorded the opposite position: "keep ordinary functions closed by default … preserve the architectural meaning of `open`: the declaring API is intentionally an extension point" (`docs/strategy/roadmap/parking-lot.md:33-34`). R20 contract §2.2 and §12 say the same. Keeping an explicit marker is just `open` under its own name, so removing the keyword gains nothing.

**Single most important finding.** `open` currently does two unrelated jobs. It is the *only* way to write pattern-headed or repeated local clauses: ordinary `f(0) = 1` is a `SyntaxError` (probe `ord-pattern-header`). It is also the cross-module extensibility declaration. The one in-repo non-spec use (`examples/ollama_chat.genia:109-139`) uses `open` only for the first job, with no `extend` anywhere. The real simplification is to separate these jobs. Put clause structure in the unified Function. Keep `open` only as the declared-extensibility attribute that makes a Function a legal `extend` target.

**Confirmed R20 bugs.** These are independent of any redesign and should be repaired first as R20 follow-ups:
- alias/re-run contribution units are silently lost;
- the synthesized `__open_contribution__…` binding leaks through exports;
- mutual/cross-function tail calls through open functions overflow the stack at depth ~500, although `GENIA_STATE.md:3255` promises mutual TCO;
- grouped-header binders are dropped, so references silently fall through to outer or global names;
- open-function docstrings are unparseable, so `IrOpenFuncDef.docstring` is always `None`;
- contribution free names resolve dynamically to the entry program's root bindings. This last one is a pre-existing module-model defect that R20 inherits.

**Verdict: `PROCEED WITH NARROWER FORM`** (section 31):
- repair the bugs first;
- then contract a unified Function / Clause / ContributionUnit / FunctionView model in which `open` stays as declared extensibility;
- keep `extend`/`use` unchanged in meaning;
- treat any widening of ordinary-function surface syntax as its own later gate;
- reject a distinct "Function Template" abstraction.

---

## 2. Sources inspected

Source-of-truth documents (in precedence order):
- `AGENTS.md` (full)
- `GENIA_STATE.md` §4 (960-1027), §4.7 (1245-1378), §8 (3246-3273), module/function values (395-419), 268
- `GENIA_RULES.md` §8 (184-192), §8.2 (302-322), §8.2.2 (366-373), §8.5 (405-447)
- `README.md` (R20 section around 871-890)
- `GENIA_REPL_README.md` (grep only; no R20 content)

Strategy and process:
- `docs/strategy/release-roadmap.md` (55-79, 159-203)
- `docs/strategy/roadmap/parking-lot.md` (32-69, 85-88)
- `docs/strategy/roadmap/r35-r37.md` (R37), `r38.md`, `r41.md`
- `docs/process/run-change.md`
- `docs/ai/LLM_CONTRACT.md` (grep)
- `docs/strategy/killer-workflow.md` (priority framing only)

R20 material:
- `docs/design/r20-open-functions-contract.md` (full)
- `docs/design/r20-open-functions-syntax-ir-design.md` (full)
- `docs/design/r20-open-functions-preflight.md` (1-80)
- `docs/analysis/r20-release-truth-audit.md` (full)
- `docs/releases/R20.md` (grep)

Core IR and host material:
- `docs/architecture/core-ir-portability.md` (R20 rows)
- `docs/host-interop/HOST_PORTING_GUIDE.md:175-197`
- `docs/host-interop/HOST_CAPABILITY_MATRIX.md:66-67`
- `docs/releases/R24.md:40-80`
- `spec/manifest.json:84`

Implementation:
- `src/genia/callable.py` (195-341, 343-741, 855-1200)
- `src/genia/evaluator.py` (813-926, 1270-1283, 1390-1555)
- `src/genia/environment.py` (12-263)
- `src/genia/values.py:453-465`
- `src/genia/parser.py` (211-248, 380-675)
- `src/genia/lowering.py` (240-252, 340-392)
- `src/genia/ir.py` (181-284, 307+)
- `hosts/python/ir_normalize.py:251-276`, `hosts/python/parse_adapter.py:46-61`
- `src/genia/builtins.py:3247-3260, 3430-3474` (help/doc)
- `src/genia/optimizer.py:78-180`

Tests and specs:
- all 29 `spec/**/*r20*` files (enumerated)
- `spec/eval/r20-cross-module-lexical-visibility.yaml`, `spec/eval/r20-varargs-over-fixed-precedence.yaml`, `spec/eval/r20-gcd-grouped-clause-equivalent.yaml` (read)
- `tests/unit/test_r20_open_functions_cross_module.py`
- `tests/unit/test_callable_runtime.py:118-129`

Usage inventory:
- `examples/ollama_chat.genia:100-145`
- repo-wide grep for `open`/`extend`/`use` statements. Zero uses in `src/genia/std/prelude`.

Direct probes: about 70 scenarios, run through `run_source` with real temporary module files. They are referenced by name below, e.g. `[probe: alias-two-units]`.

**Codex audit — EVIDENCE GAP.** No audit on removing `open` or unifying the function model exists anywhere in the repository tree or git history. Issue #1008 ("Review for open functions", opened 2026-09-24) carries two attachments: `function-templates-architectural-investigation.md` and a ChatGPT transcript. Both are hosted as GitHub user-attachments that this session could not fetch (the proxy returned a repository-scope refusal). The audit's content was therefore **not read**. Each previously reported finding the task named was re-verified independently against `main` (sections 5, 6, 9, 10). None was accepted on authority.

**`m0smith/genia-cpp` — EVIDENCE GAP.** The C++ host source was not inspected. C++ statements rely only on `docs/releases/R24.md` and `HOST_CAPABILITY_MATRIX.md`.

---

## 3. Current implemented function model

**Documented truth**
- `GENIA_STATE.md:960-1019`: named functions are first-class. "Multiple definitions by arity shape are allowed". Varargs `f(a, ..rest)`. Exact fixed arity beats varargs. Multiple eligible varargs → `TypeError("Ambiguous function resolution")`.
- `GENIA_STATE.md:998`: one canonical docstring per group.
- `GENIA_STATE.md:999-1016`: annotations attach metadata to the binding.
- `GENIA_STATE.md:3252-3255`: proper TCO, self and mutual.
- `GENIA_RULES.md:184-192` repeats the resolution rules.

**Observed representation**
- **Group.** `Env.define_function` (`src/genia/environment.py:120-136`) creates or extends one mutable `GeniaFunctionGroup` (`callable.py:195-259`). The group is a `dict[int, GeniaFunction]` keyed by `len(params)`. Rest parameters are excluded from that key.
- **Duplicate.** A second definition with the same key raises `Duplicate function definition: f/n` (`callable.py:202-207`).
- **Entry.** Each entry is a `GeniaFunction` (`callable.py:262-285`): `params: list[str]`, `rest_param`, one `body`, `closure`, `span`.
- **No pattern headers.** Header items must be plain identifiers. `f(0) = 1` is `SyntaxError: Invalid function definition parameter token` `[probe: ord-pattern-header]`.
- **Grouped body.** The body may be an `IrCase` over the whole argument tuple, the "grouped" form `f(n) = (0) -> 1 | (n) -> …`. `eval_with_tco` first binds the header parameters positionally into a frame (`callable.py:314-318`). `eval_function_body` → `eval_case_expr` (`evaluator.py:813-834, 868-886`) then tests arms in lexical order, first match plus truthy guard wins. So arm bodies **see both header binders and arm binders** `[probe: ord-grouped-header-binder → [101, 2]]`.
- **Resolution.** `invoke_callable._resolve_target` (`callable.py:1131-1153`) and a duplicate `GeniaFunctionGroup.__call__` (`238-259`) try the exact key first, then the unique eligible varargs. A second eligible varargs → ambiguity.
- **Fixed plus same-minimum varargs.** Because the dict key ignores rest, `f(a,b)` plus `f(a,b,..r)` is rejected as duplicate `f/2` `[probe: ord-fixed+varargs-same-min]`. `f(a,b)` plus `f(a,..r)` is allowed.
- **No-match diagnostics.**
  - Pattern miss: `RuntimeError("No matching case for function f/1 with arguments [5]")`.
  - Arity miss: `TypeError("No matching function: f/2. Available: f/1")`.
- **None/Outcome.** Automatic none propagation is decided per resolved arity by inspecting the chosen entry's case arms for `none`/`some` patterns, or body delegation to a known option-aware callee (`callable.py:926-968`).
- **TCO.** Tail calls return `TailCall(GeniaFunction, args)`, trampolined in `eval_with_tco`. Mutual recursion works `[probe: ord-mutual-tco, depth 100001]`.
- **Closures and recursion.** The closure is the defining environment. Recursion is lexical name lookup at call time.
- **No local named functions.** Named function definitions are top-level only. `h(n) = …` inside a block is `SyntaxError: Assignment target must be a simple name` `[probe: ord-local-fn]`. Local callables are lambdas, which may carry a pattern (`evaluator.py:1390-1421`).
- **Extra machinery keyed on `GeniaFunctionGroup`:**
  - Flow fusion for `map`/`filter`/`take`/`drop` by callee name (`callable.py:1036-1127`);
  - autoload retry by `(name, arity)` (`1157-1162`);
  - debug hooks (`320, 331`);
  - `IrListTraversalLoop` optimization on `IrFuncDef` bodies (`optimizer.py:78-180`);
  - metadata/annotations including `@route`/`@test` (`evaluator.py:1439-1466`).
- **Identity.** Groups are identity-bearing under R18 `==` (preflight §2.1).

---

## 4. Current implemented open-function model

**Documented truth:** `GENIA_STATE.md:1245-1378`, `GENIA_RULES.md:405-447`, contract, and syntax/IR design.

**Observed implementation**

Parser:
- `try_parse_open_related_toplevel` (`parser.py:491-526`) recognizes top-level soft keywords `open`, `extend`, `use`.
- It also recognizes a bare `name(` when `name ∈ self._open_names`, a set that is per-parse and per-module.
- Clause parsing reuses `parse_lambda_parameter_pattern` (`567-614`).
- A grouped case body over a trivial header is **flattened** to one `CaseClause` per arm. The header pattern is discarded (`601-611`).
- Contiguous runs merge into one AST node (`_merge_open_toplevel`, `221-248`).
- `OpenFuncDef.docstring` is always `None` (`628`).

Lowering (`lowering.py:355-392`):
- `IrOpenFuncDef(name, clauses: list[IrCaseClause], docstring, annotations=[])`
- `IrOpenContribution(target_module_alias, target_name, clauses)`
- `IrOpenUse(local_name, target_module_alias, target_name, contribution_module_aliases)`
- Prefix annotations on these forms are rejected (`240-252`).

Evaluator (`evaluator.py:1497-1550`):
- **`IrOpenFuncDef`** raises redeclaration if the name is already bound in the module env, otherwise builds `GeniaOpenFunction(name, module_identity, [OpenClauseRecord…])`.
- **`IrOpenContribution`**:
  - resolves `alias.name` and requires a `GeniaOpenFunction`;
  - builds `GeniaOpenContributionUnit(target.interface_key, module_identity, clauses)`;
  - **binds it as an ordinary module binding** named `__open_contribution__{alias}__{name}` (`1525-1526`).
- **`IrOpenUse`** resolves the base, finds each contribution module's unit by scanning its exports for a unit with a matching `target_interface_key` and **returning the first match** (`1270-1283`). It rejects duplicate declaring-module ids, then binds `GeniaLinkedOpenFunction(base, units)`.

Runtime (`callable.py:343-741`):
- `OpenClauseRecord(pattern, guard, body, closure, span, dispatch_key)`.
- The dispatch key is shape plus alpha-normalized, span-free pattern/guard (`464-534`).
- Duplicates are detected at unit construction (`554-562, 654-655, 673-674`).
- `_dispatch_open` (`596-641`):
  - shape stratum: fixed-`n` first, else eligible varargs with a single distinct minimum;
  - per-unit first match;
  - more than one candidate → ambiguity;
  - no candidate → no-match-case.
- `GeniaOpenFunction.__call__` (`683-692`) and `GeniaLinkedOpenFunction.__call__` (`717-726`) loop only while `result.fn is self`. Any other `TailCall` is handed to `eval_with_tco` recursively.
- Interface identity is `(Env.module_identity(), name)`. That is `"<entry>"` for the entry program, otherwise the requested/cached module name (`environment.py:46-57, 245-248`).
- None-awareness for open callables is `any` clause of **any arity** having a `none`/`some` pattern (`callable.py:955-959, 998-999`). Body delegation is not considered.

Host capability:
- `open_functions` is an optional capability (`spec/manifest.json:84`).
- Python: Implemented.
- C++: "Implemented (local only)"; cross-module gated by `multi_file_eval` (`HOST_CAPABILITY_MATRIX.md:66`; `R24.md:51, 72`).

---

## 5. Verified semantic/implementation divergences

| # | Divergence | Ordinary (observed) | Open (observed) | Classification |
|---|---|---|---|---|
| D1 | Grouped-header binder visibility | Header params bound, visible in arm bodies (`callable.py:314-318`). `f(a,b) = (x,0) -> a+100 \| …` → `[101, 2]` | Header discarded at flatten (`parser.py:611`). Same source → `NameError: Undefined name: a`. With a global `a = 7` in scope it **silently returns 107** `[probe: open-grouped-header-binder(-global-capture)]` | **Bug** in R20. Contract §3.1 requires grouped/repeated equivalence, but the flatten changes the meaning of the grouped spelling relative to Genia's existing grouped-function semantics. It is masked by `spec/eval/r20-gcd-grouped-clause-equivalent.yaml`, whose arms rebind the same names. |
| D2 | Fixed arity `n` plus varargs minimum `n` | `Duplicate function definition: f/2` | Coexist; `f(1,2)` → fixed, `f(1,2,3)` → varargs. Pinned by `spec/eval/r20-varargs-over-fixed-precedence.yaml` | **Implementation artifact** on the ordinary side: the dict is keyed by `len(params)` (`callable.py:203`, preflight §2.1). No doc or test intends it. The only test (`test_callable_runtime.py:123-128`) covers a same-arity fixed duplicate. |
| D3 | Clause representation | One body per arity shape. Multi-alternative only through an `IrCase` body | Ordered flat `OpenClauseRecord` list, many per shape, plus a structural dispatch key | Intentional R20 generalization. The ordinary representation is an artifact of pre-R20 history. |
| D4 | Dispatch algorithm | Three copies: `GeniaFunctionGroup.__call__`, `invoke_callable._resolve_target`, plus `eval_case_expr` inside the body | `_dispatch_open` | Same stratum rule, different code. For one unit with one clause per shape, open ⊇ ordinary except D2. **Implementation artifact.** |
| D5 | Pattern-miss / arity-miss diagnostics | `RuntimeError("No matching case …")`; `TypeError("No matching function: f/2. Available: f/1")` | `OpenFunctionNoMatchingCaseError` (a `TypeError` subclass) with identical text; `No matching function: f/2` **without** `Available:` | **Unclear/minor.** The host exception class differs and the arity-miss text differs. Needs decision. |
| D6 | None-awareness | Per resolved arity, plus body-delegation detection (`callable.py:926-968`). `f(x)="ran"; f(a,b)=(some(y),z)->…` gives `f(none)` → `none` | Any clause of any arity. `f(none)` → `"ran"` when an unrelated arity-2 clause has `some(...)`. `open f(x) = unwrap_or(0, x)` gives `f(none)` → `none`, but ordinary gives `0` `[probes: *-none-prop-*, *-delegate-optaware]` | **Bug** (open side). R20 claims existing "automatic Outcome/`none` propagation are preserved" (`GENIA_STATE.md:1291-1293`). |
| D7 | Tail calls to another function | Trampolined; mutual recursion depth 100001 OK | `RecursionError` at depth **500** for open↔open and open↔ordinary mutual recursion `[probes: open-mutual-tco, open-self-tail-small, open-ord-cross-tail]` | **Bug** against `GENIA_STATE.md:3253-3255`. The R20 audit tested only self-recursion (`r20-release-truth-audit.md:126-129`). |
| D8 | Docstrings/metadata | Docstring after `=` and `@doc`/`@meta`/`@test`/`@route` supported | `open f(0) = """doc""" 1` treats the string as the **body**, so `f(0)` → the doc text and `doc("f")` → `none("missing-doc")`. `@doc` rejected (`lowering.py:246-252`). `IrOpenFuncDef.docstring` and `.annotations` are never populated | `@doc` rejection is a **disclosed limitation**. The docstring behavior is a **bug**, and `GENIA_STATE.md:1370-1372` ("beyond the optional docstring position") overclaims. |
| D9 | Debug hooks | Threaded | Not threaded | Disclosed limitation (`GENIA_STATE.md:1377-1378`). |
| D10 | Accidental repeated declaration | `f(n)=1` then `f(m)=2` → Duplicate `f/1` | Duplicate-dispatch-key error (alpha-normalized). But `open f(n)=1` followed by `f(0)=2` silently yields an unreachable clause | Intentional difference. Relevant to section 19. |

---

## 6. Bugs discovered or confirmed

All were reproduced on `main` at `495bffd`. "Redesign-independent" means the fix needs no unified model.

- **B1 — Contribution unit lost when one module extends one target through two aliases.** Confirmed. `import base; import base as b2; extend base.get("db",…); extend b2.get("cache",…)` then `use get from base with ext` → `get("cache",…)` is `No matching case`. The b2 unit is silently dropped `[probe: alias-two-units]`. Root cause and fix in section 9. Redesign-independent.
- **B2 — Non-contiguous `extend` runs for the same target silently overwrite.** New finding. `extend base.get("db",…)`, then an unrelated statement, then `extend base.get("cache",…)` → only `cache` survives. `db` → `No matching case` `[probe: noncontig-extend-*]`. The two runs produce two `IrOpenContribution` nodes with the same synthesized binding name, and `env.set` overwrites. The same run structure for `open` raises redeclaration, so the handling is **asymmetric**. Redesign-independent.
- **B3 — Rebinding an import alias makes a contribution to module A overwrite one to module B.** New finding. `import a as m; extend m.f(2)=…; import b as m; extend m.f(2)=…` → the unit for `a.f` is lost, and `use f from a with ext` → `incompatible-contribution` `[probe: alias-rebind-*]`. Same root cause as B2. Redesign-independent.
- **B4 — Contribution binding leaks through exports.** Confirmed. `ext.__open_contribution__base__get` is an ordinary readable export rendering `<open contribution ext -> get>`. Calling it raises `pipeline stage expected a callable value, received GeniaOpenContributionUnit`, which leaks a raw Python class name, the class of leak that R19/R23 diagnostics normalization forbids `[probe: leak-export*]`. See section 10.
- **B5 — Mutual/cross-function TCO broken for open functions and views.** New finding (D7). Root cause: `__call__` loops only on `result.fn is self` (`callable.py:689, 723`) and otherwise recurses into `eval_with_tco`, which calls the other open function's `__call__`, and so on. A base clause's recursive call inside a *view* also targets the base, not the view, so view recursion also nests. Redesign-independent. A single trampoline in a unified Function fixes it structurally.
- **B6 — Grouped-header binders dropped, with silent global capture** (D1). Redesign-*dependent* choice, see sections 8 and 29.
- **B7 — Open none-awareness is arity-insensitive and ignores delegation** (D6). Redesign-independent.
- **B8 — Open docstring unparseable** (D8); STATE overclaim.
- **B9 — Contribution free names resolve through the shared root/entry environment.** Pre-existing module-model defect. `load_module` builds `Env(root, rebind_parent=False)` (`environment.py:242`), and file/command mode runs the entry program *in* that root (`interpreter.py:622-640`). So any module reads the entry program's top-level bindings: a module `f() = zzz` returns `5` after the entry sets `zzz = 5` `[probe: module-sees-entry-binding]`. For R20, a contribution clause's free `walk` resolved to the entry program's current `walk` binding. After the entry reassigned `walk`, an already-captured view dispatched into the hijacking lambda `[probe: contrib-free-name-hijack → "ENTRY-HIJACK"]`. This contradicts R20 §2.2 ("closes over its own declaring module environment, not the importer's") and weakens every "module isolation" claim. It is **not** caused by R20. It is a module-model issue: `GENIA_STATE.md:977` only promises that module *assignment* does not rebind root.
- **B10 — Misleading diagnostics.**
  - Ordinary `f(n)=1` followed by `open f(0)=2` reports "already declared open" `[probe: ord-then-open]`.
  - `use f …` then ordinary `f(n)=99` reports "name already bound to non-function value" `[probe: use-then-ordinary-def]`.
  - Conversely, ordinary `f` then `use f` silently replaces the ordinary group `[probe: use-local-name-collision-with-ordinary]`.
- **Inconsistency flagged, not resolved.** `docs/design/r20-open-functions-contract.md:3` still reads "behavior not yet implemented", which is stale. Contract §4.2 says linking happens "before any ordinary top-level expression in that module can call the view", but `use` is evaluated sequentially: an earlier `get = (a,b,c) -> "local"` is observable before the `use` line `[probe: temporal-use → ['local','db:k']]`. No partially-linked view is exposed, so this is a wording/semantics mismatch, not a safety bug. It is marked unclear.

---

## 7. Proposed unified Function definition

**Function** — an identity-bearing, immutable, pattern-dispatched callable value, consisting of:

- `origin: FunctionOrigin` (section 9);
- `clauses`: an ordered sequence of Clauses, lexical order;
- `extensible: bool`, set only by an explicit declaration. Today that declaration is `open`. See section 10;
- interface metadata (doc/meta/annotations), owned by the declaration and never by clauses.

Calling a Function is the section 13 algorithm with exactly one unit, the Function's own clause sequence.

Ordinary functions are the case where every Clause has an all-identifier (optionally rest) pattern and no guard, and at most one Clause exists per shape. For those, dispatch reduces exactly to today's "exact fixed arity, else unique varargs" rule. The only exception is D2, which the unified model resolves in favour of R20 (fixed `n` and varargs-min `n` may coexist). That relaxes a restriction and breaks no existing program. The grouped form is the one place where the choice matters: see the Clause definition and the grouped-body decision in section 29, U1.

Explicitly **not** part of Function:
- no process registry;
- no mutable clause set (today's `GeniaFunctionGroup.add_clause` mutation happens only during module-top-level construction and becomes a build step);
- no code-as-data exposure.

**Function Templates are rejected.** A separate Function Template abstraction would do one of two things. It would rename open functions, since its only distinguishing content is "clauses that can be composed later", which ContributionUnit already is. Or it would expose clauses as first-class data, which needs executable IR values: code-as-data, and a second runtime category next to Function. Nothing in sections 7-13 needs one.

---

## 8. Proposed Clause definition

**Clause** — semantic fields:

| Field | Needed for | Participates in |
|---|---|---|
| argument pattern over the whole argument tuple (existing `IrPatTuple`, optional trailing `IrPatRest`) | matching | dispatch, duplicate key, shape derivation |
| optional guard (existing expression IR) | matching | dispatch, duplicate key |
| body | execution | not dispatch, not duplicate key |
| shape (`fixed n` / `varargs ≥ n`) | stratum | **derived** from the pattern, never stored (design §3), dispatch, diagnostics |
| lexical environment | execution | not portable data; the closure is established by the declaring module at build time |
| source span | provenance | diagnostics, help, debugging; excluded from duplicate key |
| lexical ordinal | first-match within a unit | dispatch order; **derived** from list index |

Not a Clause field:
- identity (Clauses are not independently identified);
- declaring module (structural: the containing unit's owner);
- metadata (owned by the Function).

The `IrCaseClause(pattern, guard, result, span)` node already has exactly these portable fields, so Clause needs **no new IR type**.

The one open semantic question is how an ordinary grouped body (`f(a, b) = (x, 0) -> a | …`) maps to Clauses. There are three options:
- **(G1) Do not flatten.** The grouped definition is one Clause with pattern `(a, b)` and an `IrCase` body. This preserves today's ordinary semantics exactly, including header binders, with zero new IR. But a miss inside the case body does not fall through to a later sibling Clause, so grouped ≠ repeated when the same shape has more than one Clause.
- **(G2) Flatten with header binders.** Each arm becomes a Clause whose pattern must *also* bind the header names positionally. Genia has no as-pattern (`pattern_match.py:155-240`), so this needs either a new pattern node or a clause-level `header_binders` field: new IR either way.
- **(G3) Flatten and forbid header-binder references**, rejecting at build time any arm body or guard that references a header name not rebound by the arm. This keeps R20's current flattening, turns B6's silent global capture into a deterministic error, and adds no IR. But existing *ordinary* grouped functions that read header names (legal today) could not use the flattened form.

**Recommendation:** G1 for ordinary grouped bodies, which is today's truth. Repair open's flatten to at least G3, so it never silently captures an outer name. Record the grouped-versus-repeated equivalence obligation (contract §3.1) as needing amendment (section 29, U1). Source AST and Core IR stay internal representations. Clauses are never runtime-visible data.

---

## 9. Function origin/identity contract

**FunctionOrigin** = (declaring module canonical identity, originally declared binding name). This is exactly R20's current interface key (`callable.py:676-678`; `environment.py:52-57`).

- **Where identity lives.** The origin is fixed at construction and carried by the value, not by the binding. That makes the answers below mechanical and matches R18's identity-bearing callable values.

| Question | Answer (observed today where applicable) |
|---|---|
| Aliasing (`import m as n`) | Preserves origin. The module cache is keyed by module name (`environment.py:230-231`); `iface.ping == iface2.ping` is true (R20 audit §3). |
| Importing | Preserves origin. |
| Re-exporting (`get = base.get` in module `re`) | Preserves origin. `extend re.get(…)` targets `('base','get')` and `use get from re with ext` works `[probe: reexport-extend, reexport-use-via-re]`. |
| Assigning to another local name | Preserves origin (same value). |
| Wrapping (`g = (a,b,c) -> f(a,b,c)`) | New callable, and not a Function with an origin: a lambda. Not a target. |
| Anonymous functions | No origin, so never contribution targets. |
| Local/nested functions | Named nested definitions do not exist (`[probe: ord-local-fn]`); nested `open` is rejected. No question arises. |
| Dynamically produced functions | Only lambdas can be produced dynamically, so no. |
| Observable to Genia code? | Only indirectly: `help`/diagnostic text and identity `==`. No accessor. **Keep it that way:** origin is semantic/runtime metadata, not a value. |
| Across hosts | Portable because both components are source-level strings. The entry program is `"<entry>"`. |
| R41 artifacts | Serializable as the pair. **Gap:** `IrOpenContribution` names the *alias*, which resolves through the module's `IrImport` table. An artifact must preserve imports to recover the canonical target. The contribution-unit *export* is not in IR at all (section 10). |
| Textually identical functions in two modules | Different origins. |
| Module relocation | Identity is the *requested module name*, not the path, so moving a file without renaming preserves identity. **Weakness (pre-existing, flagged in preflight §2.3):** two distinct files resolved under one name via requester-relative lookup collide in the cache, first loaded wins (`environment.py:209-231`). This is a module-identity issue, not a Function issue. |

**Alias bug root cause (B1).** The implementation keys contribution *storage* by alias spelling (`__open_contribution__{alias}__{name}`, `evaluator.py:1525`) but contribution *lookup* by origin (`_find_open_contribution_unit`, `1270-1283`), which returns `matches[0]`. Two aliases produce two units with the same origin: storage keeps both, lookup silently takes one. B2 and B3 are the mirror image: two different targets, or two runs, share one storage key.

Stable origin identity is *already* in place. The bug is that storage does not use it. The fix is redesign-independent: key a module's contribution table by target origin, and merge (or reject) all `extend` runs for one origin in a module, at build time, into one unit. This is a **bug repair**, not an argument for unified functions.

---

## 10. Visibility and extensibility decision

**Facts.** Every top-level binding is exported (`GENIA_RULES.md:313`; `environment.py:257`), including import aliases (`[probe: leak-import-reexport-base]`: `ext.base` is readable) and synthesized contribution bindings (B4). No privacy marker exists (`GENIA_STATE.md:268`). Underscore is not privacy (preflight §2.3). The module env is not even read-isolated from the entry program (B9).

| Criterion | (A) Public ⇒ targetable | (B) Explicit extensibility marker | (C) Any resolvable function targetable; safety from inert `extend` + explicit `use` |
|---|---|---|---|
| Surface | Removes `open` | Keeps one modifier (`open`) | Removes `open` |
| Accidental API exposure | Every top-level helper of every module becomes a target | None beyond what the author declares | Same as A |
| Encapsulation | Genia has no private, so A = C | Author controls it | None |
| Portability | Neutral | Neutral (one boolean in IR) | Neutral |
| Tooling | Cannot list extension points | Can list them | Cannot |
| Refactoring/library evolution | Adding a base clause can make any downstream `use` ambiguous (`[probe: ambiguous-base-overlap]`) for functions the author never offered; closed recursion means contributed clauses never reach internal helper calls (`[probe: recursion-base-helper-negative]`), so extending non-designed functions gives partial behavior | Coupling limited to declared points | Same as A |
| Deterministic identity | Same | Same | Same |
| Compatibility | Widening; no program breaks | None | Widening |
| Recreates `open`? | No, but only because nothing replaces it | **Yes: it *is* `open`** | No |

Option C is not *implicit extension*, because `use` is explicit. The consumer is not the party who needs protecting. The harm is to the **base author's evolution contract**: once any function can be targeted, every clause change is potentially a breaking change for unknown downstream views.

**Decision.** Retain (B), with `open` itself as the marker, redefined narrowly as "this Function's origin may be named by `extend`". It is not "this is a different kind of function" and not "this function may have pattern-headed clauses".

This keeps R20 §2.2 ("openness must be declared, never inferred") and the recorded project position (`parking-lot.md:33-34`). The marker has a compelling purpose beyond the old spelling: in a language where everything is exported, it is the *only* author-declared API-surface boundary. Revisit (A) only if Genia ever adds explicit export lists; that is parked module redesign.

---

## 11. ContributionUnit contract

- **Definition.** A ContributionUnit is an inert, non-callable, immutable value made of:
  - target FunctionOrigin;
  - declaring module identity;
  - ordered Clauses (lexical order) closing over the declaring module environment.
- **Uniqueness.** Exactly one unit per (declaring module, target origin). All `extend` statements in a module that resolve to one origin, through any alias and in any number of runs, form one unit in source order. Rejecting non-contiguous runs is the alternative if contiguity is a deliberate rule; section 29, U4.
- **Duplicates.** Duplicate dispatch keys within a unit fail at build time (contract §6, unchanged).
- **Target.** The target must be a Function whose origin is declared extensible (section 10). A FunctionView is not a target (`[probe: extend-view]` rejects it today; keep that).
- **Not a binding.** A unit is **never an ordinary module binding** (fixes B4). It lives in a per-module *contribution table* keyed by target origin. `use … with m` consults `m`'s table, never `m`'s namespace. The table is not reachable through `m.name`, not rendered, and not callable.
- **Discoverability.** `help`/diagnostics can list units by provenance. No Genia value exposes the table.
- **Portability.** Carried by `IrOpenContribution`. The table is a runtime derivation of those nodes, so no host side table is part of the contract.
- **Private state.** A unit may read its declaring module's bindings. It cannot read the target module's non-exported state, because none exists. Everything is exported and must be reached by qualified access, e.g. `base.secret` (`[probe: contrib-private-access, contrib-own-lexical]`). **B9 must be fixed** before "closes over its own declaring module" is true: free names must not fall through to the entry program.

---

## 12. FunctionView contract

- **Definition.** A FunctionView is the base Function plus a **set** of selected ContributionUnits, keyed by unit provenance. It is immutable. It is an ordinary callable value. It does not mutate the base (`[probe: nontransitive]`: `base.get` is unchanged after `c` links a view).
- **Identity.**
  - A view is a new identity-bearing value. `view == view` is true.
  - Two separately linked views with equal composition are **not** `==` (`[probe: view-eq → [False, False, True]]`). This matches R18 callable identity; do not add structural equality.
  - The view reports its base's origin for help and diagnostics, but it **is not** that origin.
- **Not a target or base.** A view is not an extension target and not a `use` base (`[probe: use-from-view]` rejects it; keep that). Composition is always "base + units" and never "view + units". This prevents order-dependent layering, which would reintroduce import-order semantics.
- **Rendering and metadata.**
  - Renders as today (`<open function get (linked)>`; see U7 for spelling).
  - `help` lists base first, then units by provenance (`builtins.py:3247-3260`).
  - `doc`/`meta` are the base's; units cannot supply metadata (contract §7.2).
- **Binding.** The view is bound under the target's name in the using module only. It is exported like any binding, but only as that module's own value, so it is non-transitive.

---

## 13. Exact dispatch algorithm

Given a callable `C` (a Function = one unit; or a View = base unit + selected units) and arguments of count `n`:

1. **Shape stratum.**
   - Let `F` be all Clauses, in all participating units, with fixed shape `n`.
   - If `F` is non-empty, the participating clauses are `F`.
   - Otherwise let `V` be the varargs Clauses with minimum ≤ `n`.
   - If `V` has more than one distinct minimum, raise `varargs-ambiguity(origin, n, shapes, provenances)`.
   - If `V` is empty, raise `no-matching-function(origin, n)`.
   - Otherwise the participating clauses are `V`.
2. **Unit-local first match.** For each unit independently, test its participating clauses in lexical order using existing `match_lambda_pattern` and guard semantics. The first success is that unit's candidate. A `PatternOutcomeError` returns its Outcome (existing behavior, `callable.py:627-630`).
3. **Across units.** Exactly one candidate → invoke it. More than one → `clause-ambiguity(origin, n, candidate provenances)`. None → `no-matching-case(origin, n, args)`.
4. **Invocation.** Bind the match environment over the clause closure and evaluate the body in tail position. A returned `TailCall` goes to **one shared trampoline** for all callables (fixes B5).

**None propagation** happens before step 1. Short-circuit unless some Clause *in the selected shape stratum* explicitly handles `none`/`some`, or its body delegates to an option-aware callee. This aligns open with ordinary (fixes B7). It needs the stratum computed first, which is a cheap, pure shape filter.

**Properties:**
- selection order never appears;
- lexical order matters only inside a unit;
- for an ordinary Function this is today's resolution, except D2;
- the base unit participates exactly like any other unit, so overlapping contributions are ambiguous (`[probe: ambiguous-base-overlap]`). This is preserved.

---

## 14. Recursion semantics

**Current (observed).**
- A base clause's `f` resolves lexically in the base module to the **base Function**, never a view. `base.start(-2)` fails even though the consumer's view handles negatives `[probe: recursion-base-helper-negative]`.
- A contribution's reference resolves lexically in the contributing module. If the name is unbound there, it falls through B9 to the *entry program's* binding, which may be the view or anything else `[probe: contrib-free-name-hijack]`.
- A contribution calling `base.f` gets the base `[probe: recursion-contrib-calls-base]`.

**Options**
1. **Closed/lexical recursion.**
   - Predictable.
   - Composition never changes the base's internal behavior, so "composition must not mutate the original" holds in the observable sense.
   - Module isolation holds once B9 is fixed.
   - No per-view re-closure.
   - Optimization stays local.
   - Debugging: a call's target is determined lexically.
   - **Cost:** an extended recursive interface (e.g. a structural walker over heterogeneous values) does not recurse through contributions. Users must pass the dispatcher explicitly.
2. **Open recursion through the view.**
   - Every clause needs an implicit "self" rebound per view.
   - That is either code-as-data (re-closing clauses per view) or a hidden dynamic parameter.
   - Composition changes base behavior: a base author's `start` helper would behave differently in each consumer.
   - It violates module isolation in spirit and makes actor/event reuse riskier (hidden late binding).
3. **Context-dependent resolution** (a view name in scope wins): this is today's accidental B9 behavior. Nondeterministic with respect to unrelated entry bindings. Reject.

**Recommendation:** (1), stated explicitly in the contract. Contributed clauses recurse lexically in their declaring module. The expressiveness cost is recorded as unresolved (U3), not solved by implicit late binding.

---

## 15. Alias/import/re-export semantics

- **Aliases and re-exports.** These resolve to the same origin (section 9). `extend` through any alias or re-export targets the origin. All `extend`s for one origin in one module are one unit (fixes B1-B3).
- **Duplicate selection.** `use f from X with m, m2` where `m` and `m2` alias one cached module → `duplicate-selection` (already correct, `[probe: dup-select-alias]`). Selecting through the same alias twice is also a duplicate.
- **Re-exported base.** `use get from re with ext`, where `re.get` is a re-export of `base.get`, links against the base origin (works today). A re-export of a *view* is not a valid `use` base (section 12).
- **Imports.** An import alone never selects (preserved, `[probe: nontransitive]`). Import order never affects dispatch (R20 spec `r20-cross-module-order-independence`).
- **Import aliases as exports.** Import aliases are exported bindings today (`ext.base`). This is a pre-existing module-model over-export of the same class as B4. It should be decided in the module model, not here (U6).

---

## 16. R20 semantic mapping

| Current R20 concept | Unified model | Preserved? | Special machinery remaining? |
|---|---|---|---|
| open interface | Function with `extensible` declared | Yes | One boolean |
| local/base clauses | Function.clauses | Yes | None |
| repeated local clauses | Clauses appended in source order | Yes (contiguity rule retained) | Parser run-merging (exists) |
| grouped clause | G1 or G3 (section 8) | **Partially:** §3.1 equivalence needs amendment under G1 | Decision U1 |
| contribution | Clauses in a ContributionUnit | Yes | Contribution table (replaces mangled binding) |
| contribution unit | ContributionUnit (one per module × origin) | Yes; fixes B1-B3 | None new |
| explicit selection | `use` | Yes | Same |
| linked view | FunctionView | Yes | Same |
| interface identity | FunctionOrigin | Yes | Same key |
| provenance | Clause span + unit declaring module + origin | Yes | Same |
| duplicate detection | Per-unit dispatch key | Yes | Same `_structural_key` (now also for ordinary functions) |
| ambiguity detection | §13 step 3 | Yes | Same |
| shape strata | §13 step 1 | Yes; ordinary gains D2 relaxation | Same |
| fixed-vs-varargs precedence | §13 step 1 | Yes | Same |
| lexical clause order | Within unit | Yes | Same |
| module ownership | Origin module owns base; unit owned by declaring module | Yes, **after B9 fix** | Module env isolation fix |
| imports | Inert | Yes | — |
| aliases | Origin-keyed | Yes, **fixed** | — |
| diagnostics | Same identities; possible rename of `open-function-*` prefix | Yes if names kept | See section 21 |
| immutable linking | View immutable; binding assignable like any binding | Yes | — |
| recursion | Closed/lexical, explicit | Yes, now contracted | — |
| help provenance | Same | Yes | — |
| TCO | Shared trampoline | **Improved** (B5) | — |
| none propagation | Per-stratum | **Improved** (B7) | — |

**What cannot be cleanly expressed:** exact grouped/repeated normalization under ordinary header-binder semantics without either new IR (G2) or giving up fall-through equivalence (G1). See section 29.

---

## 17. Core IR consequences

**Inventory:**
- `IrFuncDef(name, params, rest_param, docstring, body, annotations, span)` (`ir.py:220-229`);
- `IrOpenFuncDef(name, clauses, docstring, annotations, span)` (`251-260`);
- `IrOpenContribution(target_module_alias, target_name, clauses, span)` (`264-271`);
- `IrOpenUse(local_name, target_module_alias, target_name, contribution_module_aliases, span)` (`275-283`);
- `IrCaseClause(pattern, guard, result, span)` (`181-187`), reused.

Normalized shared IR emits all of these (`ir_normalize.py:251-276`). `IrOpenFuncDef.docstring` and `.annotations` are never populated by the parser (D8), so they are dead optional fields in normalized IR (`core-ir-portability.md:102-103`).

| Node | Classification | Reason |
|---|---|---|
| `IrFuncDef` | **KEEP (near-term) / UNCERTAIN (long-term)** | The R24 C++ host consumes it for every ordinary function case. Replacing it would invalidate pinned evidence (`R24.md:62-68`, `755/141/614`) and require a contract-revision bump. It is semantically expressible as an `IrOpenFuncDef` with one all-identifier Clause and an `IrCase` or plain body (G1). Hosts may lower it internally to the unified Function without changing portable IR. |
| `IrOpenFuncDef` | **GENERALIZE** | This becomes the general "Function with clauses" node, plus one explicit `extensible` field (or keep the node name and treat its presence as "extensible", which risks conflating the two roles again; U2). Populate or remove the dead `docstring`/`annotations`. |
| `IrOpenContribution` | **KEEP** | Correct shape. **Clarify** that the unit key is (declaring module, *resolved* target origin), not the alias. R41 must carry the import table needed to resolve it. |
| `IrOpenUse` | **KEEP** | Pure link instruction. Already minimal. |
| `IrCaseClause` | **KEEP** | Already the shared Clause representation for ordinary case arms, open clauses, and contribution clauses. **Yes: ordinary and contributed clauses already share one portable clause representation.** |

**Net effect.**
- The honest minimal outcome is **no IR reduction** in the near term: one node generalized, one field added, two dead fields resolved.
- A real reduction (removing `IrFuncDef`) is a **breaking portable-IR change** with R24 cost. It should be scheduled only with R41 (artifact format versioning) or another deliberate contract revision.
- The redesign **clarifies** IR more than it shrinks it. It does not require new IR concepts unless G2 is chosen.

---

## 18. Runtime consequences

Current named-callable runtime kinds:
- `GeniaFunctionGroup`, `GeniaFunction`
- `GeniaOpenFunction`, `GeniaLinkedOpenFunction`, `GeniaOpenContributionUnit`
- `OpenClauseRecord`
- plus lambdas (Python closures with `__genia_body__`) and `GeniaNamedPattern`

Proposed:
- `Function` (replaces Group and OpenFunction)
- `Clause` (replaces per-arity `GeniaFunction` and `OpenClauseRecord`)
- `ContributionUnit`
- `FunctionView`
- lambdas and named patterns unchanged

Machinery that is **coupled to `GeniaFunctionGroup` and must be moved, not deleted**:
- Flow fusion by callee name (`callable.py:1036-1127`);
- autoload retry (`1157-1162`);
- per-arity none detection (`926-1008`);
- `IrListTraversalLoop` optimization (`optimizer.py:78-180`, keyed on `IrFuncDef`);
- debug hooks (`callable.py:81-100, 319-332`);
- metadata merge (`environment.py:145-156`);
- `help`/`doc` (`builtins.py:3247-3474`).

That is roughly half the "simplification": complexity *moves* into Function. The genuine removals:
- two of three dispatch implementations;
- two runtime kinds;
- the special open `__call__` trampolines (fixing B5);
- the mangled contribution binding (fixing B4);
- the parallel none-detection branch (fixing B7).

---

## 19. Parser/syntax consequences

The syntax questions come after the semantics above. Test case:

```
get("mem", store, key) = ...
get("cache", cache, key) = ...
extend base.get("db", db, key) = ...
use get from base with db_ext
```

- **Semantics.** This is expressible *semantically* under the unified model. But without `open`, `extend base.get` would be accepted only under Option A/C, which section 10 rejects.
- **Local syntax.** Allowing pattern-headed and repeated clauses for non-extensible Functions (`f(0) = 1` without `open`) is a **separate surface decision** (U5).

What changes under U5 = yes:
- **Grouped syntax:** unchanged, G1.
- **Repeated declarations:** a contiguous run is one Function. A non-contiguous repeat is an error, matching today's open behavior (`[probe: open-noncontig]`), where ordinary functions today *allow* non-contiguous different-arity definitions.
- **Ordinary same-name definitions:** today `f(a)=…` and, anywhere later, `f(a,b)=…` form one arity group. A contiguity rule would **break** programs whose different-arity definitions are separated. So either contiguity is dropped for Functions (merging all same-name top-level definitions in a module, as ordinary functions do today) or ordinary functions keep non-contiguous accumulation. That is itself a semantic question (U4). R20's contiguity rule was a "deliberate minimality choice" (design §4), not a principled rule.
- **Accidental repeats:** an identical dispatch key is an error, as today. `f(n)=1` followed by `f(0)=2` would become a silently unreachable second clause. Today ordinary functions error. **U5 = yes therefore loses a diagnostic** unless unreachable-after-catch-all detection is added. This is the §14 hazard ("accidental repeated declaration silently becomes composition") in miniature. It is local, not cross-module.
- **Imports:** unaffected.
- **Local shadowing:** named local definitions do not exist, so unaffected.
- **Annotations:** the unified Function takes ordinary `@doc`/`@meta`. `open` declarations currently reject annotations, so this is a gain.

**Keyword:** `open` stays as a modifier meaning only "extensible".

---

## 20. Module-system consequences

- **Required regardless of the redesign:** a per-module contribution table (fixes B4) and origin-keyed unit storage (fixes B1-B3).
- **Required for R20's own contract to hold:** module environments must not read the entry program's bindings (B9). The current design makes `root` both the prelude/builtin scope and the entry program scope (`interpreter.py:622-640`; `environment.py:242`).
  - Fix direction: the entry program gets its own child environment.
  - This is module-model work affecting all modules, not just R20. It has compatibility risk: any module that accidentally depends on entry globals breaks. It needs its own gate.
- **Out of scope:** export lists, privacy, and import-alias export (U6).

---

## 21. Diagnostic/provenance consequences

- **Identities.** Keep the seven R20 identities. If `open` stays (section 10), the `open-function-` prefix remains accurate for extensibility-related errors:
  - `target-not-open`, `redeclaration`, `duplicate-selection`, `incompatible-contribution`.
  - Duplicate-clause and the two ambiguity diagnostics now apply to *all* Functions, so a neutral prefix (e.g. `function-duplicate-clause`) would be more accurate.
  - Renaming changes pinned stderr in `spec/error/error-r20-*.yaml` (6 files) and must be phased per AGENTS.md "RENAME SAFETY RULE".
- **Resolve D5:** one host exception class and one text for arity and pattern miss across all Functions. The ordinary text includes `Available:`, which is more useful.
- **Fix B10** messages.
- **Leaks:**
  - B4's raw class name `GeniaOpenContributionUnit` disappears once the unit is no longer a binding.
  - Span rendering currently prints absolute host paths (`[probe: open-dup-clause]`), contrary to contract §7.1/§8 "host paths may be shown only as separately classified host-local detail". **Flagged, not resolved:** the audit treated `filename:line` as sufficient.
- **Provenance:** unchanged (section 16).

---

## 22. Multi-host/C++ consequences

- **Python:** moderate refactor of the callable core (section 18). Highest-risk area: hot-path `invoke_callable` special cases.
- **C++ (EVIDENCE GAP: source not inspected).**
  - From docs: C++ declares `open_functions: supported` for local grouped/repeated clauses (`R24.md:51`) and implements ordinary functions within the R24 floor.
  - If portable IR is unchanged (section 17 "KEEP `IrFuncDef`"), C++ is unaffected by the unification itself.
  - It *is* affected by the semantic repairs: D2 relaxation, G3 rejection, D5 diagnostics, B5 TCO if its local open implementation shares Python's structure. Each repair needs shared specs, and the capability `open_functions` must remain the gate.
  - Removing `IrFuncDef`, or merging nodes, **would change R24 evidence**. It should wait for a versioned boundary (R41).
- **Shared specs:** new cases for D1/D2/D5/D6/D7, and B1-B3 (via `multi_file_eval`).
- **Capability:** no new capability. The work repairs and extends `open_functions` semantics.
- **Future hosts:** one dispatch algorithm instead of two is genuinely easier to port. That is the one clear multi-host win, and it is available without a portable-IR break, as hosts may internally lower `IrFuncDef` to the unified Function.

---

## 23. Value Template relationship

- **Value Template (R9/R15):** describes acceptable *values*. It is an ordinary callable with the Outcome protocol (`some`/`none`/`err`) and composes through `&`, `@?`/`@!`, and named patterns (`evaluator.py:1265-1306`).
- **Function:** describes executable behavior over *argument tuples*. Its result is arbitrary and not an Outcome protocol.

**Legitimately shared:**
- the pattern engine (`match_lambda_pattern`, named-pattern resolution, so a Template can be used *inside* a Clause pattern);
- ordinary callable invocation;
- lexical closures;
- the R9 philosophy of reusing callable/pattern machinery instead of a parallel matcher.

**Must remain distinct:**
- the Outcome protocol (a Function returning `none` is data, not "no match");
- composition operators (`&` combines matchers, not Functions);
- extensibility (Templates are not extension targets; R20 §12 non-goal);
- no-match semantics (Template → `none`/`err` value; Function → deterministic error).

The unified model **must not** make Functions Templates or vice versa.

---

## 24. Future actor/event relevance

Does Function/ContributionUnit/FunctionView remove the need for R37/R38 to invent another extensible-dispatch mechanism?

- **R37:** probably not needed. R37 selects events "with existing Genia pattern/value machinery" and observes subscriptions as Flows (`r35-r37.md:74-100`). That is Flow plus patterns, not extensible dispatch.
- **R38:** message handling is plausibly an ordinary Function over message patterns, so no new dispatch primitive is needed. But nothing requires cross-module contribution for actor behavior.
- **Providers/protocol implementations:** the natural consumer, e.g. `ollama_chat.genia`'s backend dispatch. Local-only open use proves *local* clauses suffice there today.

**Conclusion:** the model is a reasonable foundation but is **not justified by** future reuse. No kill-criterion credit is taken for it.

---

## 25. Compatibility/migration plan

**Under the recommended narrower form** (keep `open`), existing sources need no rewriting. Behavior changes are bug fixes, and each needs a shared spec:

| Change | Affected programs |
|---|---|
| D1/G3 | An `open` grouped body referencing a header name now errors instead of capturing a global. |
| D2 | Ordinary `f(a,b)` + `f(a,b,..r)` becomes legal (a widening). |
| D6/B7 | An `open` function receiving `none` with unrelated-arity `some` clauses now short-circuits. |
| D8 | `open f(0) = "…" body` string becomes a docstring. **This silently changes results:** today the string is the body. |
| B2/B3 | Non-contiguous `extend` runs now merge or error, where they silently overwrote. |
| D5 | Exception class/text alignment. |

**If `open` were removed** (the rejected hypothesis), `open f(…) = …` → `f(…) = …` is **not** always semantics-preserving:
- the repeated-clause parse depends on `_open_names` (`parser.py:521-524`);
- cross-module `extend` targets would lose their declared status, or become universally targetable;
- the pinned identities `open-function-target-not-open` / `redeclaration` lose meaning;
- none-propagation differences (D6) change results;
- C++ `open_functions` evidence changes.

**Quantified in-repo break under full removal:**
- 3 declarations in `examples/ollama_chat.genia`;
- about 3 README snippets;
- 29 R20 spec files, including 6 error specs with pinned text;
- `tests/unit/test_r20_open_functions_cross_module.py`;
- `GENIA_STATE.md` §4.7, `GENIA_RULES.md` §8.5, `docs/releases/R20.md`, `docs/host-interop/*`;
- the C++ R24 evidence row;
- zero prelude uses.

External user code: **unknown (evidence gap)**. Deprecation would need a soft-keyword alias period per AGENTS.md rename rules.

---

## 26. Complexity ledger

| Concern | Current | Proposed (narrow form) | Change |
|---|---|---|---|
| Runtime value kinds (named callables) | Group, Function, OpenFunction, LinkedOpenFunction, ContributionUnit (+ leaking binding), OpenClauseRecord | Function, Clause, ContributionUnit (not a binding), FunctionView | **Removes** (−2 kinds) |
| Dispatch implementations | 3 (`GeniaFunctionGroup.__call__`, `_resolve_target`, `_dispatch_open`) + `eval_case_expr` | 1 + `eval_case_expr` (for G1 bodies) | **Removes** |
| Trampolines | `eval_with_tco` + 2 bespoke open loops | 1 | **Removes** (and fixes B5) |
| None-awareness detection | 2 parallel branches | 1 per-stratum | **Removes** |
| IR nodes | `IrFuncDef`, `IrOpenFuncDef`, `IrOpenContribution`, `IrOpenUse` | Same 4 near-term; `IrOpenFuncDef` + `extensible` field | **Generalizes** (0 net); removal of `IrFuncDef` deferred and **breaking** |
| Parser concepts | FuncDef header (identifiers only) + open clause parser | Same two unless U5 = yes; then one clause parser + `open` modifier | **Renames/generalizes** |
| Evaluator branches | `IrFuncDef` + `IrOpenFuncDef` + contribution + use | Same count unless IR merges | **Moves** |
| Module machinery | Mangled export binding | Contribution table | **Moves** (slightly adds a concept, removes a leak) |
| Module isolation | Entry bindings leak into modules (B9) | Separate entry scope | **Adds** (a real fix, not simplification) |
| Metadata/provenance | Group metadata; open has none (D8) | One metadata path | **Removes** a gap |
| Host-coupled special cases (Flow fusion, autoload, optimizer, debug) | Keyed on Group/IrFuncDef | Keyed on Function | **Moves** |
| Host capabilities | `open_functions` | Same | None |
| Semantic specs | 29 R20 + ordinary cases | + about 10 repair cases | **Adds** evidence |
| Diagnostics | Divergent D5/B10 | Aligned | **Removes** divergence |

**Net:** genuine removal in dispatch, trampolines, runtime kinds, and none-detection. Moved complexity in host special cases. No near-term IR reduction. The hypothesis's headline gain, "remove `open`", contributes **nothing** to the removal column.

---

## 27. Alternatives considered

1. **Status quo + bug fixes only (B1-B10).** Cheapest. Keeps two dispatchers and two runtime kinds that have already diverged six ways. Acceptable fallback.
2. **Narrow unification: one Function kind; `open` retained as declared extensibility; no surface change (U5 deferred).** **Recommended.**
3. **Narrow unification + ordinary pattern-headed/repeated clauses (U5 = yes).** Plausible later step. Adds a second spelling (repeated clauses vs grouped `|`) for non-extensible Functions, loses the accidental-repeat diagnostic, and interacts with contiguity (U4). Needs its own gate under Core Surface Freeze.
4. **Full hypothesis: remove `open`; Option C.** Rejected (section 10): with everything exported, every function becomes an extension point.
5. **Remove `open`; Option A.** Identical to 4 in today's module model.
6. **Replace `open` with a different marker** (`@extensible`, `export open`, …). Rejected: renames `open`.
7. **Function Templates.** Rejected (section 7).
8. **Protocols/typeclasses.** Rejected (R20 §12 non-goal; parking lot).
9. **Explicit export lists, then Option A.** Only coherent path to removing `open`. Requires module-system redesign (parked). Out of scope.
10. **Open recursion views.** Rejected (section 14).

---

## 28. Kill-criteria evaluation

Evaluated for **(H)** the full hypothesis (remove `open`) and **(N)** the narrow form.

| Kill criterion | H | N |
|---|---|---|
| Merely renames open functions | Partly: cross-module half is `open` without its guard | No: removes dispatchers/kinds |
| Makes extension implicit | No (`use` explicit), but makes *extensibility* implicit | No |
| Introduces process-global mutation | No | No |
| Weakens deterministic dispatch | No | No (strengthens: B1-B3 fixed) |
| Weakens provenance | No | No |
| Weakens module isolation | Weakens encapsulation (every function targetable) | No (B9 fix strengthens it) |
| Makes ordinary function semantics more complicated | Yes (all functions gain extension-target status) | Slightly (D2 relaxation; one algorithm). Acceptable |
| Creates a second callable namespace | No | No (contribution table is not a namespace) |
| Requires public executable AST/IR | No | No |
| Increases Core IR complexity without compensation | No | No (0 net; clarifies) |
| Makes host implementation materially harder | Moderate | Low (no portable IR break near-term) |
| Relies primarily on speculative actors/events reuse | No | No |
| Cannot cleanly explain ordinary functions | Can | Can (G1) |
| Cannot preserve R20 contribution semantics | Preserves | Preserves (and repairs) |
| Requires marker that is `open` under another spelling without purpose | If a marker is kept: **yes → kill**. If not: triggers "extensibility promise" failure | Keeps `open` *itself* with a stated purpose → passes |

**H fails. N passes.**

---

## 29. Unresolved contract decisions

- **U1 — Grouped-body mapping:** G1 (no flatten), G2 (flatten plus header binders, new IR), or G3 (flatten, forbid header references). R20 contract §3.1 wording must be amended accordingly. Recommendation: G1 for ordinary, G3 minimum for open.
- **U2 — IR carrier for extensibility:** explicit field on a generalized node vs presence of `IrOpenFuncDef` vs a separate declaration node.
- **U3 — Recursion:** closed/lexical recursion confirmed as contract. Whether any explicit mechanism for recursing through a view is ever wanted (not implicit).
- **U4 — Contiguity:** keep R20's contiguous-run rule, adopt ordinary functions' non-contiguous accumulation, or unify on one. Also whether non-contiguous `extend` runs merge or error.
- **U5 — Surface:** may non-`open` Functions use pattern-headed/repeated clauses? Separate Core-Surface-Freeze gate. If yes: an unreachable-clause diagnostic policy.
- **U6 — Module model:** entry-scope isolation (B9), import aliases as exports, contribution-table visibility.
- **U7 — Diagnostics:** identity prefix rename policy; exception class and `Available:` text alignment (D5); host-path redaction in spans.
- **U8 — Stale docs:** `r20-open-functions-contract.md:3` status line; `GENIA_STATE.md:1370-1372` docstring claim; §4.2 "linked before any top-level expression" vs sequential `use`.
- **U9 — Evidence gaps:** Codex audit (issue #1008 attachments) unread; C++ open-function implementation uninspected.

---

## 30. Recommended implementation slices

Applies to the narrow form only. Each slice passes the normal preflight → contract → design → failing test → implementation → docs → audit gates (`docs/process/run-change.md`), **and** — per the R26+ Change Pre-Flight Gate added to `AGENTS.md` after this report was drafted — must first complete the `GENIA Change Pre-Flight` issue template (`.github/ISSUE_TEMPLATE/genia-change-preflight.md`) before implementation begins, since every slice below is a semantic/runtime/host-behavior change, not a typo fix. Classified as an **R20 follow-up** per the roadmap's "Promoted R20 follow-up" entry (`release-roadmap.md:63-66`). It is not a new release and not killer-workflow work.

1. **F1 — R20 bug repairs, no redesign.**
   - Origin-keyed contribution storage plus a contribution table that is not a binding (B1-B4).
   - Single trampoline for open functions and views (B5).
   - Per-stratum none-awareness (B7).
   - Grouped-flatten G3 rejection of header-name capture (B6).
   - Docstring parsing for `open` (B8).
   - Diagnostic fixes (B10).
   - Shared specs for each, cross-module ones via `multi_file_eval`.
2. **F2 — Module entry-scope isolation (B9).** Separate module-model gate, with compatibility survey.
3. **F3 — Contract: unified Function model.**
   - Sections 7-14 and 16 as contract text.
   - `open` = declared extensibility.
   - U1/U3/U4 resolved.
   - D2/D5 alignment.
   - No surface change.
4. **F4 — Python runtime unification.** Function/Clause/Unit/View kinds, one dispatcher. `IrFuncDef` lowered internally, with no portable IR change. Moved special cases (section 18).
5. **F5 — Shared evidence and C++ follow-up.** Requires inspecting genia-cpp.
6. **F6 — Optional, separate gate: U5 surface widening.**
7. **Deferred to R41 or a versioned IR revision:** merging `IrFuncDef` into the generalized node.

---

## 31. Final recommendation

**`PROCEED WITH NARROWER FORM`**

Why:

1. **The unified Function / Clause / ContributionUnit / FunctionView model is sound, and the split has real costs.**
   - Ordinary resolution is R20's §5 algorithm restricted to one unit (`callable.py:1131-1153` vs `596-641`). The only exception is a dict-key artifact (D2, `callable.py:203`).
   - The two paths have observably diverged in six ways: D1, D2, D5, D6, D7, D8.
   - The open path breaks documented guarantees: mutual TCO (`GENIA_STATE.md:3255` vs `RecursionError` at depth 500) and Outcome-propagation preservation (`GENIA_STATE.md:1291-1293` vs probe `open-none-prop-other-arity-some`).
   - One Function kind removes two dispatchers, two bespoke trampolines, and a parallel none-detection branch, and it needs no new portable IR (`IrCaseClause` already serves both, `lowering.py:383-391`).
2. **Removing `open` fails.**
   - Every top-level binding is exported (`GENIA_RULES.md:313`; `environment.py:257`) and no privacy exists (`GENIA_STATE.md:268`), so dropping the marker makes every function of every module an extension point.
   - That contradicts R20 §2.2/§12 and the recorded direction "keep ordinary functions closed by default … preserve the architectural meaning of `open`" (`parking-lot.md:33-34`).
   - Any replacement marker is `open` renamed (kill criterion).
   - `open` should be *narrowed*, not removed: today it wrongly doubles as the only pattern-headed-clause syntax, as the sole non-spec use shows (`examples/ollama_chat.genia:109-139`, no `extend`).
3. **Several defects exist regardless of design and should be fixed first:**
   - contribution units lost via aliases, non-contiguous runs, or alias rebinding (`evaluator.py:1525` vs `1270-1283`);
   - the leaking `__open_contribution__…` export;
   - broken open TCO (`callable.py:689, 723`);
   - silent global capture through dropped grouped-header binders (`parser.py:611`);
   - unparseable open docstrings (`parser.py:628`);
   - entry-program bindings visible to every module, which lets a contribution be hijacked (`environment.py:242`; `interpreter.py:622-640`).
4. **Not proven:** the reduction in Core IR (0 net near-term; removing `IrFuncDef` would break R24 pinned evidence). Also not established: C++ cost (source not inspected) and the content of the Codex audit (unreadable attachments). None of these reverses the verdict, but each bounds it. They are the reason the recommendation is the narrower form, not `PROCEED`.
