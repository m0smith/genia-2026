# #1269 / #1250 — Model B Slice C RED test plan, host plan and documentation plan

**Status: PLAN ONLY — no test, spec, manifest or production file is added by this document.** Everything here is authorized only after an independent GO on `issue-1269-slice-c-preflight.md` and resolution of its decisions D1/D3/D5. Expected outputs marked `[D#]` depend on that decision; literal diagnostic text for *new* failures is not contract-fixed and must be locked in the RED commit.

Conventions (reused, none new): shared cases are `spec/{eval,error,cli}/model-b-c-*.yaml` loaded by the existing R16 runner; **regression guards carry no `requires`** (they must pass today and after — they exist to prove no previously valid program changed meaning, and must never be gated away); only genuinely new behavior carries `requires: [default_open_functions]` (+ `multi_file_eval` / `repl` where those surfaces are observed). Host-local tests live in `tests/unit/test_model_b_slice_c*.py` (direct Core IR, locks, reflection consumers). Native tests alone are not evidence for C++.

## 1. RED baseline protocol (before writing any case)

1. Record `main` SHA, `python -m tools.spec_runner` counts (Slice B recorded 874 passed / 0 failed / 0 invalid before its additions; re-measure), and focused suites: `tests/unit/test_function_resolution_precedence.py`, `test_callable_runtime.py`, `test_lexical_assignment.py`, `test_r20_open_functions_*.py`, `test_model_b_slice_{a,b}.py`, `tests/spec/test_r20_open_functions_shared_specs.py`, F2 isolation, REPL characterization.
2. Characterize the "to verify" items: the 5 unparseable corpus files; inline Genia in Python test sources (scan for groups with ≥2 varargs minima and for alias-declaration, P5/P10/P11 of the pre-flight).
3. Commit the RED as a separate commit; expected failures listed with exact messages; the implementation commit must cite the RED SHA.
4. `spec/manifest.json`: add optional capability `default_open_functions` **in the RED commit** (needed for the cases to load) and mark it provisional exactly as Slice B did, because `hosts/python/protocol_adapter.py::_python_claimed_capabilities` auto-claims manifest names; the claim is true only at the GREEN head. Add the C++ `spec/known_host_gaps.json` entry in the same commit (tracking `m0smith/genia-2026#1269`, exact case list).

## 2. Shared R16 inventory

Legend — **G** regression guard (passes today, no `requires`); **R** RED (fails today); category in brackets.

### C-OPEN — default-open local accumulation
| ID | Program / observation | Expected | Kind |
| --- | --- | --- | --- |
| model-b-c-acc-noncontiguous-arities | `f(x)=x; g(y)=y; f(x,y)=x+y` calls | `1`, `3` | G [eval] |
| model-b-c-acc-alias-sees-later-arity | P1 | `3` | G |
| model-b-c-acc-call-before-later-clause | `f(x)=x; f(1,2)` before `f(x,y)` declared → `No matching function: f/2. Available: f/1`; after declaration succeeds | exact | G [error]+[eval] |
| model-b-c-acc-pattern-after-plain | `f(x, y)=…; f(0, y)=…` then call | pattern clause installs, order = declaration order | R |
| model-b-c-acc-noncontiguous-pattern | pattern clauses separated by unrelated statements | all visible after execution, none before | R |
| model-b-c-acc-lambda-factory-distinct | `mk(k) = (x) -> x + k` instances | distinct, equal only to themselves; not extendable | G |
| model-b-c-acc-redeclare-fresh-scope | declaration inside a lambda body evaluated twice | fresh group each time (identity not shared) | R/to-verify by parse (nested named declarations are unsupported → assert existing rejection) |

### C-PAT — pattern/guard headers execute
| ID | Observation | Expected |
| --- | --- | --- |
| model-b-c-pat-literal-base-case | `fact(0)=1; fact(n)=n*fact(n-1); fact(5)` | `120` (R) |
| model-b-c-pat-guard-selects | `f(x) ? x > 0 = "pos"; f(x) = "other"` | order + guard (R) |
| model-b-c-pat-guard-sees-header-binding | guard references pattern binders; body does too | (R) |
| model-b-c-pat-match-local-shadows-outer | pattern binder shadows module-level name | (R) |
| model-b-c-pat-list-map-some-err-named | one case per pattern family: list/rest, map, `some(x)`, `err(r,c)`, named matcher, wildcard | (R) one file each |
| model-b-c-pat-string-body-is-body | `f("a") = "doc-like"` returns that string; `doc("f")` unchanged | (R) |
| model-b-c-pat-first-match-wins | two overlapping clauses → first | (R) |
| model-b-c-pat-unreachable-later-clause | catch-all first, specific second → specific never runs, no diagnostic | (R) |
| model-b-c-pat-fixed-miss-no-varargs-fallthrough | `f(0)=…; f(n, ..r)=…; f(5)` | `No matching case` family `[D3]` — documents R20 stratum rule |

### C-KEY — duplicate keys (portable relation; no evaluation)
| ID | Observation | Expected |
| --- | --- | --- |
| model-b-c-key-alpha-equivalent-dup | `f([a,b]) = …; f([c,d]) = …` | duplicate-clause error `[D3]`, nothing evaluated (R) |
| model-b-c-key-guard-alpha-dup | same pattern, guards alpha-equal | duplicate (R) |
| model-b-c-key-guard-differs-ok | same pattern, different guard | both install (R) |
| model-b-c-key-true-vs-one | `f(true)=…; f(1)=…` | both install; calls route correctly (R, delta B6) |
| model-b-c-key-one-vs-one-point-zero | `f(1)=…; f(1.0)=…` | both install (R, delta B6) |
| model-b-c-key-free-name-syntactic | guards `x > limit` vs `x > cap` with different free names | distinct keys (R) |
| model-b-c-key-shadowed-binder | nested lambda/case in guard shadowing a pattern binder | alpha-equal only when binder structure equal (R) |
| model-b-c-key-no-effects | guard/matcher/body side effects absent while duplicate is rejected (sentinel via Ref) | no effect (R) |
| model-b-c-key-legacy-dup-id | P3 | `Duplicate function definition: f/1` unchanged (G) |
| model-b-c-key-explicit-open-dup-unchanged | explicit `open` duplicates (existing `error-r20-local-duplicate-clause`) | unchanged (G); plus `true`/`1`, `1`/`1.0` become distinct under D4 (R, `requires: open_functions, default_open_functions`) |
| model-b-c-key-numeric-spellings-same-binary64 | `0.1` vs `0.10` | same key (R) |

### C-DISP — shape strata, varargs, ambiguity
| ID | Observation | Expected |
| --- | --- | --- |
| model-b-c-disp-fixed-and-varargs-same-required-arity | P4 then `f(1)`, `f(1,2)` | `1` fixed, varargs (R, delta B3) |
| model-b-c-disp-fixed-over-varargs | existing precedence (`test_exact_fixed_arity_preferred_over_varargs`) as shared twin | G |
| model-b-c-disp-varargs-ambiguity-legacy-id | P7 | `Ambiguous function resolution…` (G) |
| model-b-c-disp-varargs-exact-key-shadow | **P5** | `"min2"` today → `[D1]` (guard if hybrid; error + approved-delta note if unified). This case is the explicit breaking-change tripwire |
| model-b-c-disp-no-matching-function | P8 | legacy text (G) |
| model-b-c-disp-no-matching-case | shape ok, no pattern matches | `[D3]` (R); arguments rendered via `format_debug` |
| model-b-c-disp-no-clause-ambiguity-in-one-unit | overlapping clauses never produce `open-function-clause-ambiguity` in Slice C | first-match (R) |

### C-HDR — header frame, grouped bodies, side-effect order
| ID | Observation | Expected |
| --- | --- | --- |
| model-b-c-hdr-grouped-body-captures-header | `area(x) = (0)->0 \| (n)->n*x` | existing behavior (G); contrast with explicit-open rejection `open-function-header-capture` (G, existing) |
| model-b-c-hdr-guard-evaluated-once | guard increments a Ref; one call | counter = 1 for matched clause, no re-evaluation at invocation (R) |
| model-b-c-hdr-guard-order | earlier clause's guard effect precedes later clause's; later guard not run after a match | exact Ref log (R) |
| model-b-c-hdr-guard-error-propagates | guard raises | error propagates, later clauses not tried, no partial binding (R) |
| model-b-c-hdr-matcher-outcome | named matcher returning `none`/`err` | existing PatternOutcome behavior (R for pattern group; G for legacy `pattern` use) |
| model-b-c-hdr-closure-capture | clause captures declaring scope | (R) |
| model-b-c-hdr-recursion-tco | deep self and mutual tail recursion across pattern clauses (e.g. `r20-open-ordinary-mutual-tail-call` twin) | constant stack (R) |

### C-OPT — Outcome/Option awareness
`model-b-c-option-none-pattern-in-stratum-dispatches`, `-other-arity-clause-not-aware`, `-delegation-to-aware-callee`, `-err-pipeline-value-short-circuits`: twins of the four `r20-option-*` specs for ordinary pattern groups (R); plus P9 `f(x)=x; f(none("r"))` (G) and a pipeline `|>` lift case (G). Killer-workflow validated-pipeline specs must stay green unmodified.

### C-R20 — explicit `open` compatibility (all G, no `requires` beyond `open_functions`)
`model-b-c-r20-open-then-bare-clause-run`, `-open-after-ordinary-redeclaration` (P14), `-bare-after-ended-run` (P15), `-gcd-unchanged` (P16), `-grouped-header-capture-rejected`, `-metadata-doc-meta-only`, `-use-replaces-ordinary` (characterization). These re-state, as `model-b-c-*`, behavior already covered by `r20-*` so the compatibility claim of Slice C is checkable in one grep; the original `r20-*` specs remain **unmodified**.

### C-OWN — ownership / provenance / declaration targets
| ID | Observation | Expected |
| --- | --- | --- |
| model-b-c-own-declare-through-alias-same-scope | P10 | `[D5]` |
| model-b-c-own-declare-through-imported-alias | P11 (`multi_file_eval`) | `[D5]` error naming canonical module identity, no path/address; base module's `g` unchanged (R) |
| model-b-c-own-import-alone-inert | importing a module never changes the importer's/other module's dispatch | G |
| model-b-c-own-extend-target-ordinary-unchanged | `extend` on ordinary export → `open-function-target-not-open` | G (D owns the change) |
| model-b-c-own-use-ordinary-base-unchanged | `use` over ordinary base → current behavior | G |
| model-b-c-own-lambda-builtin-not-interface | lambda/builtin/host alias declaration target | no interface identity; `[D5]` |
| model-b-c-own-module-cannot-see-entry-binding | F2 topology unchanged | G (existing `f2-*` specs also unmodified) |
| model-b-c-own-entry-prelude-name | P12 | `[D2]` characterization |
| model-b-c-own-same-name-two-modules | two modules each define `f(0)`/`f(n)`: independent groups | R (`multi_file_eval`) |

### C-IMM — Slice B interaction
`x =: 1; x(a)=a` fails before clause install (R); `f(a)=a; f =: 1` fails (G); `x =: 1; x(0)=1` (pattern) fails (R); declaration over import alias / parameter name per Slice B policy (G/R); `f(x)=x` where `f` is a parameter in function scope — existing behavior characterization (G); meta-circular `_meta_define` cannot append to an immutable-owned name (host-local).

### C-META — three metadata channels, annotations, docs
`@doc` on later clause merges onto binding (G); newer key overwrites, unmentioned retained (G); unannotated alias gets no copy (G); inline docstring shared across legacy clauses and visible through alias (G); conflicting inline docstring fails **before** installing the new clause (G); pattern clause string-body is not documentation (R); `help(name)` lists every record deterministically including pattern clauses with provenance, no host objects (R); `doc(name)`/`meta(name)`/`help(name)` for groups with pattern clauses (R); `@category/@route/@test/@doc` accepted on pattern clauses where legal on legacy (R); `@route`/HTTP/lifecycle binding with pattern clause per `[D3b]` (R, host-local + shared where expressible).

### C-ANN — annotation publication (contract §5.2)
Install-then-annotate: annotation raising on clause 2 leaves clause 2 callable and clause-1 metadata unchanged (G for legacy via characterization; R for pattern); first failing annotation stops later annotations (effect log via Ref); effects of executed annotations persist; no partial metadata map visible (R).

### C-ERR — diagnostics and leakage
Protected (R10) sentinel in args never appears in no-matching-case/duplicate/ownership diagnostics (R); no filesystem path or `0x…` address in any new diagnostic (R); error category normalization table for new ids (error category, R19-style) `[D3]`; ownership error provenance names canonical module identity or `<entry>` only.

### C-MODE — mode equivalence and REPL
`cli` cases: file / `-c` / import / piped; REPL: group grows across completed submissions (`f(x)=x` then `f(0,y)=y`), a failed declaration (duplicate/immutable) leaves the group unchanged and the name usable, incomplete multi-line input stays incomplete (`requires: repl` only where the existing CLI REPL cases already do). Command-mode `genia_run` MCP-equivalent source cases via `eval`.

### C-IR — carriers and traversal (host-local plus existing shared `ir` cases)
Existing `spec/ir/model-b-a-*` byte-stable (G); `IrPatternFuncDef` evaluated directly produces the same observable as its source (host-local twin of every R eval case that is source-expressible); direct-IR malformed pattern node rejected (existing Slice A tests stay); closed-group child `IrPatternFuncDef` still `model-b-not-implemented` and **not** installed (G, regression for E boundary); optimizer never reorders/merges declarations (`test_model_b_optimizer_regression.py` extended); `iter_ir_nodes` reaches pattern bodies/guards.

## 3. Host-local Python test inventory (`tests/unit/test_model_b_slice_c.py`, `..._races.py`)

1. Group record API: ordered records, derived arity index consistency for legacy-only groups, owner/provenance field, snapshot-on-dispatch.
2. Key walker unit tests as pure functions over lowered IR: tag distinctness, binder-slot normalization, free names, quasiquote depth, malformed structure rejected deterministically, **no `repr`/host equality fallback** (property: key equality ⇔ documented relation for a table of pairs).
3. Locks/races: two threads declaring the same key → exactly one wins; declare vs. dispatch snapshot; guard reentry does not hold `_BINDING_LOCK`; barrier coordination, no sleeps.
4. Consumers of arity-keyed groups: `server_route_binding`, `http_annotation_binding`, `lifecycle_binding`, `test_cli`, `interpreter` main-group lookup, `builtins` help/doc/meta, `values`/`equality` rendering and identity — each with (a) unchanged behavior on legacy-only groups, (b) `[D3b]` behavior on groups containing pattern clauses.
5. Autoload/prelude: a prelude file defining pattern clauses loads identically with and without autoload (twin of `test_autoload_resolution_matches_non_autoload`); P12 characterization.
6. Reflection: `doc/meta/help` scope-bound lookups (F2) unchanged.
7. Error-class identity: legacy `TypeError` texts for P3/P7/P8 byte-identical (existing tests unmodified).
8. Direct-IR vs source equivalence for every R eval case that is source-expressible.

## 4. Expected RED outcome and capability requirements

- Expected: every **R** shared case fails today, almost all with `model-b-not-implemented: declaration evaluation is not available` (pattern-headed cases) or `Duplicate function definition` (same-arity cases) or accepted-but-wrong output (D5 cases); every **G** case passes today and must stay passing; host-local R tests fail on missing API. Record counts as `selected/passed/failed/invalid` like the Slice B RED note.
- Capability requirements: `default_open_functions` for all R cases; `+ multi_file_eval` for module-boundary cases; `+ open_functions` for explicit-R20 delta cases; `+ repl` only for REPL cases that already gate on it. G cases: none. Required capabilities (`parser`, `ast_lowering`, `core_ir_eval`, `doc_help`) are never relaxed.
- **Non-negotiables:** no existing spec edited to weaken or re-tag; no genuine failure classified `unsupported`; C++ "unsupported" is reported as unsupported, never as PASS; a RED case that cannot be written without a new semantic choice stops the phase and goes to #1249.

## 5. Implementation surfaces mapped to RED families

| Surface | Families |
| --- | --- |
| `callable.py` group record + key walker + dispatch adapter | C-KEY, C-DISP, C-HDR, C-OPT |
| `evaluator.py` IrFuncDef / IrPatternFuncDef branches | C-PAT, C-ANN, C-IMM, C-IR |
| `environment.py` `define_function`, ownership, lock | C-OWN, C-IMM, races |
| `builtins.py` help/doc/meta; `values.py`/`equality.py` | C-META, C-ERR |
| arity-keyed consumers | C-META (D3b), host-local §3.4 |
| `spec/manifest.json`, `known_host_gaps.json`, `hosts/python/protocol_adapter.py` | capability/gap accounting |

## 6. Documentation and architecture plan (applies only after verified GREEN)

Process/conformance history stays in `.genia/process/` and `docs/releases`-style evidence; authoritative semantic files describe behavior only.

| File | Change after GREEN | Must remain true until then |
| --- | --- | --- |
| `GENIA_STATE.md` | §3 Model B block: ordinary pattern/guard headers execute (Python); retire "Default-open dispatch… unimplemented" for the local part only, keep "linking and closed publication remain unimplemented"; §4: multi-clause ordinary dispatch, duplicate-key and ownership rules, B-deltas; §4.7: note explicit `open` unchanged and still the only form for cross-module `extend`/`use`; §MCP paragraph (`idioms.clauses`) ; anchors in `state:open-functions`/`state:syntax-forms` preserved for registry checks; distill to keep word budget | currently says pattern headers fail with `model-b-not-implemented` — stays true |
| `GENIA_RULES.md` | "Model B declarations: partial support" block updated in the same way; invariants for ownership/dispatch | same |
| `GENIA_REPL_README.md` | same block; REPL group-growth/failed-declaration behavior | same |
| `README.md` | same block | same |
| `docs/architecture/core-ir-portability.md` | note `IrPatternFuncDef` is evaluable outside closed groups; version label per D6 | no new node |
| `docs/architecture/executable-semantic-conformance.md`, `docs/host-interop/HOST_CAPABILITY_MATRIX.md`, `HOST_PORTING_GUIDE.md`, `capabilities.md` | add `default_open_functions` row (Python supported, C++ unsupported/gap #1269) | do not claim C++ |
| `docs/design/pre-r29-…-contract-DRAFT.md`, `-design.md` | status lines only (implemented slices); no semantic rewrite; remain historical | approved semantics unchanged |
| `docs/design/r20-open-functions-*.md` | cross-reference only | historical |
| `docs/contract/semantic_facts.json` (`mcp_language_profile`) | update `clauses` idiom and discovery/gap facts, evidence fragments, anchors | tests `test_state_anchors_and_registry_sync.py`, `test_semantic_doc_sync.py` |
| `apps/mcp/mcp.genia` | regenerate with `tools/gen_mcp_language_profile.py`, run its check; golden/probe evidence refreshed | not regenerated before GREEN |
| `docs/book/*`, `docs/cheatsheet/*` (core, unix-power-mode) | pattern-clause examples with classification; cheatsheet sidecar validation if runnable examples change | |
| `docs/ai/LLM_CONTRACT.md` | MCP `genia_language_profile` sentence mentions "multi-clause functions with a literal first parameter need `open`" — update after GREEN | |
| `tools/code_documentation.py` / maintained-code docs | new/changed public and internal callables documented per `docs/contract/code-documentation.md` | |

Banned certainty phrases (`all examples`, `complete coverage`, `fully aligned`, `no drift`) are not to be used; examples carry classification; Python-only behavior is labelled.

## 7. Process after GO

RED commit (+ evidence note) → GREEN commit(s) → maintainability review (`docs/process/code-maintainability-review.md`, inspecting the diff and call sites) → docs commit → independent skeptic audit → distillation → final-head CI (both loopback partitions) → maintainer merge. The temporary #1226 dogfooding observation applies to the eventual substantial task (not to this docs-only pre-flight).
