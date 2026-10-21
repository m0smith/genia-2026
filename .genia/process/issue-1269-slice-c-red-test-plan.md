# #1269 / #1250 — Model B Slice C RED test plan, host plan and documentation plan (revision 3)

**Status: PLAN ONLY — no test, spec, manifest, adapter or production file is added by this document. RED is NO-GO** until the gate in `issue-1269-slice-c-preflight.md` §12 is cleared. Revision 3 (from reviewed head `db30181f`) keeps revision 2's D1, numeric-key and C1–C8 content and adds the maintainer's **D5, D3, D3b** approvals and **D8 Option A (pending Codex verification)** — preflight §2.3–2.6 and §11. **Every case labelled `PENDING D8 VERIFICATION` is not a locked oracle.** Literal strings for new diagnostics are RED oracles that are byte-characterized against the observed baseline before being locked (maintainer directive); none is locked by this plan.

Conventions (reused, nothing new): shared cases are `spec/{eval,error,cli}/model-b-c-*.yaml` run by the existing R16 runner. **Old behavior keeps its original applicability** — a regression twin for behavior that needed `open_functions`, `multi_file_eval`, `repl`, `refs`, `flow_phase_1` or `immutable_bindings` keeps exactly that `requires`; behavior that was ungated stays ungated. Only genuinely new behavior is gated by `default_open_functions` (plus the concern-specific capabilities it uses). Required capabilities (`parser`, `ast_lowering`, `core_ir_eval`, `doc_help`) are never relaxed. Historical `r20-*` specs and `tests/unit/test_r20_*` are **not duplicated, renamed or edited**; where they already cover behavior this plan cites them and adds only the missing counterexamples.

Expected-output notation: `out:` = stdout, `err:` = stderr line (exact text, `Error: ` prefix, exit 1). Strings for **new** failures are the pinned proposals of preflight D3; literal text is locked in the RED commit after the maintainer confirms D3/D3b/D5/D8.

## 1. RED baseline protocol and capability staging (C3, C8)

1. Record `main` SHA and `python -m tools.spec_runner` counts (Slice B recorded 874 passed / 0 failed / 0 invalid; re-measure), plus the focused suites: `test_function_resolution_precedence.py`, `test_callable_runtime.py`, `test_lexical_assignment.py`, `test_r20_open_functions_*.py`, `test_model_b_slice_{a,b,b_races}.py`, `test_model_b_optimizer_regression.py`, `tests/spec/test_r20_open_functions_shared_specs.py`, F2 isolation, REPL characterization, `tests/doc`.
2. Characterize the **to verify** items: the 5 unparseable corpus files; inline Genia in Python tests (groups with ≥2 varargs minima, alias declarations); whether any existing R20 spec/test expects `true`/`1` or `1`/`1.0` to be duplicates; exact current diagnostics of each arity-keyed consumer for a wrong-shape handler; exact `Available:` rendering for varargs shapes in `No matching function`.
3. **C0 — DESIGN-ONLY at this revision (integration-owner conditional sign-off for design; no code authorized; Codex checking for false claims, hidden failures and applicability changes).** If authorized later it is a separate reviewed commit before RED — evidence plumbing that prevents a false capability claim (preflight §9.1): adapter constant `_VOCABULARY_ONLY_CAPABILITIES` reports listed names `unsupported`; `test_python_claimed_capabilities_covers_the_full_vocabulary` keeps `set(claimed) == known_capabilities()` and gains a vocabulary-only-is-unsupported assertion. No protocol/runner/manifest-format change.
4. **RED commit:** `spec/manifest.json` gains `default_open_functions` **and** the name is added to `_VOCABULARY_ONLY_CAPABILITIES` (Python reports `unsupported`, honestly); `spec/known_host_gaps.json` gains the C++ entry (tracking `m0smith/genia-2026#1269`, exact case IDs); gated cases are added. Under the normal runner gated cases are **not applicable** to Python (skipped/unsupported counts, never counted as pass or fail). RED failures are produced by `tests/spec/test_model_b_slice_c_red.py`, which loads the gated cases and runs them through `hosts/python/adapter.run_case` directly (capability gating bypassed, documented, RED-only); it fails with recorded messages. Ungated/old-capability guards run normally and must pass.
5. **GREEN commit:** remove the name from `_VOCABULARY_ONLY_CAPABILITIES` in the same commit that makes the cases pass, so `supported` is true when claimed. The Slice B provisional-claim precedent is acknowledged and not repeated.
6. RED is a separate commit; GREEN cites its SHA. A case that cannot be written without a new semantic choice stops the phase and returns to #1249.

## 2. Shared R16 inventory with executable oracles

Legend: **G** = guard, passes today (original applicability, unchanged) · **R** = RED, fails today · **R-gated** = R and `requires: default_open_functions` (+ listed). "Today" for R cases is the recorded failure.

### C-OPEN — accumulation (contract §2.2)
| ID | Source | Expected | Kind / requires |
| --- | --- | --- | --- |
| model-b-c-open-noncontiguous-arities | `f(x)=x`, `g(y)=y`, `f(x,y)=x+y`, `[f(1), f(1,2)]` | `out: [1, 3]` | G, none |
| model-b-c-open-alias-sees-later-arity | `f(x)=x; a=f; z=0; f(x,y)=x+y; a(1,2)` | `out: 3` | G |
| model-b-c-open-immutable-alias-stays-live | `f(x)=x; a =: f; f(x,y)=x+y; a(1,2)` | `out: 3` (immutable alias does not freeze accumulation; **to verify** baseline) | G, `immutable_bindings` |
| model-b-c-open-call-before-later-clause | `f(x)=x`, `f(1,2)` | `err: No matching function: f/2. Available: f/1` | G (error) |
| model-b-c-open-pattern-after-plain | `f(x)=x; f(0)=9; [f(0), f(1)]` | `out: [0, 1]` — earlier catch-all wins (first match); install succeeds (distinct keys) | R-gated |
| model-b-c-open-noncontiguous-pattern | pattern clauses separated by `g(y)=y` and a `print`; call after all, and a call between them | call between sees only earlier clauses; after sees all | R-gated |
| model-b-c-open-lambda-factory-distinct | `mk(k) = (x) -> x + k`; two instances | distinct callables, each equal only to itself; no interface identity | G |
| model-b-c-open-persistent-env | REPL: `f(x)=x` then `f(0, y)=y` then `f(0, 5)` | `5`; group grew across submissions | R-gated + `repl` |

### C-PAT — pattern/guard headers execute (grammar per design §13.1)
| ID | Source | Expected |
| --- | --- | --- |
| model-b-c-pat-literal-base-case | `fact(0)=1; fact(n)=n*fact(n - 1); fact(5)` | `out: 120` |
| model-b-c-pat-guard-selects | `f(x) ? x > 0 = "pos"; f(x) = "other"; [f(1), f(-1)]` | `out: ["pos", "other"]` |
| model-b-c-pat-guard-sees-header-binding | guard and body both reference pattern binders | value computed from both |
| model-b-c-pat-match-local-shadows-outer | module-level `v = 99`, clause `f([v]) = v` | `f([1])` → `1` |
| model-b-c-pat-{list-rest,map,some,err,named,wildcard} | one case per family (`f([x, ..xs])`, `f({key: x})`, `f(some(x))`, `f(err(r, c))`, `f(P(x))`, `f(_)`) | results per pattern |
| model-b-c-pat-string-body-is-body | `f("a") = "doc-like"`; `[f("a"), doc("f")]` | body returned; `doc` shows no documentation (post-`=` string is never documentation) |
| model-b-c-pat-first-match-wins | `f(x)=1; f(0)=2; f(0)` | `out: 1` (no specificity) |
| model-b-c-pat-fixed-miss-no-varargs-fallthrough | `f(0)=1; f(n, ..r)=2; f(5)` | `err: No matching case for function f/1 with arguments [5]` exit 1; `f(9, 8)` → `2` |

All R-gated.

### C-KEY — typed structural keys (preflight §2.2, approved)
Installation **and dispatch** observations (C4):
| ID | Source | Expected |
| --- | --- | --- |
| model-b-c-key-true-vs-one | `f(true)=1; f(1)=2; [f(true), f(1)]` | `out: [1, 2]` (both install; runtime: `true` does not match numeric `1`) |
| model-b-c-key-one-vs-one-point-zero | `f(1)=10; f(1.0)=20; [f(1), f(1.0)]` | both install; `out: [10, 10]` (runtime literal `1` matches `1.0`, first match wins — P21) |
| model-b-c-key-same-binary64-dup | `f(1.0)=1; f(1.00000000000000001)=2` | `err: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)` |
| model-b-c-key-spelling-dup | `f(0.1)=1; f(0.10)=2` | same duplicate error |
| model-b-c-key-alpha-equivalent-dup | `f([a,b])=1; f([c,d])=2` | duplicate error (lines 1/2) |
| model-b-c-key-guard-alpha-dup / -guard-differs-ok | same pattern; alpha-equal guards → dup; different guards → both install | |
| model-b-c-key-free-name-syntactic | guards `x > limit` vs `x > cap` | distinct keys; both install even if `limit == cap` at runtime |
| model-b-c-key-lambda-shadow | `f(x) ? ((a)->a)(x) > 0 = 1; f(y) ? ((b)->b)(y) > 0 = 2` | duplicate; a variant where an inner binder shadows an outer pattern binder is **not** collapsed with one referencing the outer slot |
| model-b-c-key-quote-unquote | clauses whose guards differ only inside quoted vs unquoted names | quoted names are data (not renamed); active unquote at depth participates |
| model-b-c-key-repeated-rest-binders | `f(x, x)` vs `f(a, b)`; `f(x, ..r)` vs `f(y, ..s)` | repeated binder differs from distinct binders; rest binders alpha-normalize |
| model-b-c-key-named-matcher | `f(P(x))=1; f(Q(x))=2` vs same matcher twice | distinct references distinct; same reference duplicate |
| model-b-c-key-no-effects | guard/matcher/body effects logged to a `Ref`; rejected duplicate | log empty |
| model-b-c-key-legacy-dup-id | P3 | `err: Duplicate function definition: f/1` (G) |
| model-b-c-key-r20-delta-true-one | `open f(true)=1` / `f(1)=2` / `[f(true), f(1)]` | `out: [1, 2]` — **approved R20 acceptance change** (today: duplicate error, P13). `requires: open_functions` + `default_open_functions`. |
| model-b-c-key-r20-delta-one-float | `open f(1)=1` / `f(1.0)=2` | installs; `f(1.0)` → `1` |
| error-r20-local-duplicate-clause (existing) | unchanged | must still pass unmodified |

### C-DISP — D1 and strata (approved)
| ID | Source | Expected |
| --- | --- | --- |
| **model-b-c-disp-p5-varargs-minima-ambiguity** | `f(a, ..r)="min1"; f(a, b, ..s)="min2"; f(1, 2)` | `err: Ambiguous function resolution: f/2. Matching varargs: f/1+, f/2+` exit 1 (today: `"min2"`). **Approved breaking change.** Ungated (it changes ungated ordinary behavior); RED fails today; run directly by the RED harness, by the normal runner after GREEN |
| model-b-c-disp-p5-migration-fixed-clause | add exact `f(a, b)="exact2"` | `f(1,2)` → `"exact2"` (documented migration fix) |
| model-b-c-disp-p5-migration-drop-lower | only `f(a, b, ..s)` | `f(1,2)` → `"min2"` |
| model-b-c-disp-p7-same-arity-ambiguity | `f(a,..r); f(a,b,..s); f(1,2,3)` | `err: Ambiguous function resolution: f/3. Matching varargs: f/1+, f/2+` (G) |
| model-b-c-disp-fixed-over-varargs | `pick(a,b)="exact"; pick(a,..rest)="varargs"; pick(1,2)` / `(1,2,3)` | `"exact"` / `"varargs"` (G; existing `test_function_resolution_precedence.py` stays) |
| model-b-c-disp-fixed-and-varargs-same-arity | `f(a)=1; f(a,..r)=2; [f(1), f(1,2)]` | `out: [1, 2]` (P4, error→valid), R-gated |
| model-b-c-disp-no-matching-function | P8 | `err: No matching function: f/2. Available: f/1` byte-identical (G) |
| model-b-c-disp-no-matching-function-new-group | `f(x)=1; f(x,y)=2; f(x,..r)=3; f()` | `err: No matching function: f/0. Available: f/1, f/2, f/1+` (R-gated; renderer = `OpenFunctionNoMatchingFunctionError`, re-characterized byte-for-byte before locking) |
| model-b-c-disp-duplicate-pattern-header | `f([a,b])=1; f([c,d])=2` | `err: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)` (R-gated; class `OpenFunctionDuplicateClauseError`) |
| model-b-c-disp-distinct-failure-classes | one program per class (duplicate / shape miss / case miss / varargs ambiguity / ownership) | host-local assertion of the five distinct exception classes: `TypeError`+legacy text, `OpenFunctionDuplicateClauseError`, `TypeError` shape-miss, `RuntimeError` case-miss, `TypeError` ambiguity, `FunctionDeclarationNotOwnerError` — they must not collapse into one another |
| model-b-c-disp-case-miss-identity | `f(x) = (0 -> x); f(1)` | `err: No matching case for function f/1 with arguments [1]`; exception class `RuntimeError` (G, P20); same class and text for a **pattern group** miss `f(0)=1; f(5)` → `err: No matching case for function f/1 with arguments [5]` (R-gated) |
| model-b-c-disp-no-clause-ambiguity-single-unit | overlapping clauses | first match; never `open-function-clause-ambiguity` (R-gated) |
| model-b-c-disp-explicit-open-varargs-ambiguity | existing `error-r20-varargs-ambiguity` | unchanged (G, `open_functions`) |

### C-HDR — frames, block prefix, side-effect order (C1)
| ID | Source | Expected |
| --- | --- | --- |
| **model-b-c-hdr-block-prefix-once** | `f(x) { print("prefix"); k = x + 1; n ? n < k -> x \| _ -> 0 }` then `f(2)` | `out: prefix\n2` — prefix once, before guard, `k` visible to the guard (G, P19; must stay green through the refactor) |
| model-b-c-hdr-block-prefix-miss | same shape with all arms missing | prefix printed once, then the ordinary case-miss error; no rollback of the print |
| model-b-c-hdr-block-prefix-multi-call | two calls | prefix printed once per call, not per arm |
| model-b-c-hdr-grouped-body-captures-header | `f(x) = (0) -> x \| (n) -> n + x` | header binding visible in arms (G); contrast `open` rejection `open-function-header-capture` (existing G) |
| model-b-c-hdr-guard-evaluated-once | guard increments a `Ref`; one call | counter `1`; body does not re-evaluate (R-gated, `refs`) |
| model-b-c-hdr-guard-order | clause 1 guard logs "a" and fails, clause 2 guard logs "b" and passes, clause 3 would log "c" | log `a,b` |
| model-b-c-hdr-guard-error | guard raises | error propagates, later guards not run, no partial binding |
| model-b-c-hdr-matcher-outcome | named matcher returning `none`/`err` | existing pattern-outcome behavior; matcher `err` is not a miss |
| model-b-c-hdr-recursion-tco | deep self and mutual tail recursion across pattern clauses (twin of `r20-open-ordinary-mutual-tail-call`) | constant stack, correct result |

### C-OPTIM — optimizer retention (C2)
| ID | Observation |
| --- | --- |
| model-b-c-optim-collection-recursion | `pick(n, xs) = (_, []) -> nil \| (0, [x, .._]) -> x \| (n, [_, ..rest]) -> pick(n - 1, rest)`: results identical with the optimizer on and off (`pick(1, [5, 6])` → `6`); host-local run both ways |
| model-b-c-optim-late-declaration | optimized declaration followed later by another clause of a different shape: both visible; duplicate decision identical optimized/unoptimized |
| model-b-c-optim-keys-retained | host-local: logical keys and ordered arm records for the optimized declaration equal the unoptimized ones; `IrListTraversalLoop` never serialized as portable IR |
| existing | `model-b-a-recursion-in-list`, `-in-map`, `test_model_b_optimizer_regression.py` stay green unmodified |

### C-OPT — Outcome/Option awareness
Ordinary pattern-group twins of the four `r20-option-*` specs (`none-pattern-in-stratum-dispatches`, `other-arity-clause-not-aware`, `delegation-to-aware-callee`, `err-pipeline-value-short-circuits`) — R-gated; P9 `f(x)=x; f(none("r"))` → `none("r")` (G); `|>` lift case (G); unrelated or later-declared clauses cannot confer awareness at an earlier call. Validated-pipeline/killer-workflow specs unmodified.

### C-OWN — ownership (D5 APPROVED; exact texts are RED oracles locked after baseline characterization)
Every rejection case also asserts the **state after rejection**: nothing installed, owner group unchanged, alias binding unchanged, rejected declaration's annotation expressions **not evaluated** (effect log via `Ref` empty), metadata of both names unchanged, a later legitimate owner declaration still works.
| ID | Source | Expected |
| --- | --- | --- |
| model-b-c-own-alias-call-live | P1 | `out: 3` (G) |
| model-b-c-own-immutable-alias-live | `f(x)=x; a =: f; f(x,y)=x+y; a(1,2)` | `out: 3` (G, `immutable_bindings`) |
| **model-b-c-own-local-alias-rejected** | `f(x) = x`<br>`a = f`<br>`a(x, y) = x + y` | `err: function-declaration-not-owner: cannot declare a/2: 'a' refers to function 'f' declared by another binding in this scope`; then (separate case, same prefix) `f(1)`→`1`, `a(1)`→`1`, `f(1, 2)`→`No matching function: f/2. Available: f/1`; then `f(x, y) = x + y; a(1, 2)`→`3` (R-gated; today the declaration succeeds, P10) |
| model-b-c-own-local-alias-pattern-clause | `a(0, y) = y` through the alias | same category and message with `a/2` (R-gated) |
| model-b-c-own-local-alias-varargs | `a(x, ..r) = x` | `… cannot declare a/1+: …` (R-gated) |
| model-b-c-own-alias-annotation-not-evaluated | `@doc (log_effect())` on the rejected declaration | rejection first; effect log empty (R-gated, `refs`) |
| **model-b-c-own-imported-alias-rejected** | module `lib`: `g(x) = x`; entry: `import lib`, `h = lib.g`, `h(x, y) = x + y` | `err: function-declaration-not-owner: cannot declare h/2: 'h' refers to function 'g' owned by module 'lib'`; `lib.g(1, 2)` still `No matching function: g/2. Available: g/1`; `lib.g(1)` → `1` (R-gated, `multi_file_eval`; today `3`, P11) |
| model-b-c-own-diagnostic-safety | both rejections above | message contains no filesystem path, `0x…` address, source span or captured/protected value (R10 sentinel as an argument default is absent); module rendered by canonical identity only (host-local + shared substring checks) |
| model-b-c-own-lambda-builtin-host-unchanged | `g = (x) -> x; g(a, b) = 1`; `p = print; p(a, b) = 1` | existing `Cannot define function g/2: name already bound to non-function value` etc. **unchanged** — D5 does not re-label non-group bindings (G) |
| model-b-c-own-explicit-open-unchanged | declaring over an open interface/view | existing `Cannot define function … open function interface or linked view` (G) |
| model-b-c-own-import-inert | importing a module never changes dispatch elsewhere | G, `multi_file_eval` |
| model-b-c-own-extend-ordinary-rejected | `extend base.f(0)=…` where `base.f` is ordinary | `open-function-target-not-open` unchanged (G, `multi_file_eval`+`open_functions`) |
| model-b-c-own-use-ordinary-base-unchanged | `use f from base with c` over an ordinary base | current behavior characterized, unchanged (G) |
| model-b-c-own-explicit-open-link-unchanged | existing `r20-cross-module-*` fixture | still green (G; cited, not copied) |
| model-b-c-own-two-modules-independent | two modules each define `f(0)`/`f(n)` | independent groups |
| model-b-c-own-entry-prelude-name | P12 | characterization: routing unchanged; existing prelude clauses not redirected for internal callers (D2) |
| model-b-c-own-module-cannot-see-entry | F2 topology | G (existing `f2-*` unmodified) |
| host-local | direct `Env.define_function` owner checks (owner = `(module identity, name)` provenance, not `callable(value)`); ordinary group with provenance is **not** accepted by `IrOpenContribution`/`IrOpenUse` target checks via `isinstance` or duck typing |

### C-CONSUMER — special consumers (D3b APPROVED)
Legacy-only groups: **identical** behavior to today for every consumer (G, byte-for-byte, including `@test`'s existing absence of a rest-parameter check). New groups use each consumer's **existing** mismatch behavior; no representative record is ever chosen.
| Consumer | Case | Expected |
| --- | --- | --- |
| `@route` | `@route(...)` handler `h(req) = …` legacy | accepted (G) |
| `@route` | handler with a pattern clause `h({path: p}) = p`; handler `h(r)=…; h(r,..x)=…` (fixed+rest same minimum); handler `h(r, ..x)` alone | route discovery diagnostic `@route handler must expose exactly one fixed one-argument function arm` for the first two (R-gated); the third is unchanged (already rejected today, G) |
| HTTP annotations (`@get`/`@post`, `send_annotated`) | zero-arg legacy accepted (G); pattern-bearing or `f(); f(..r)` mixed | `TypeError: send_annotated expected a fixed zero-argument function` (R-gated, host-local) |
| `@test` | legacy `f()` accepted (G); legacy `f(..r)` as today (G); group with a pattern record, or a fixed+rest pair | discovery unit `@test functions must take zero arguments`; test body not run, no representative `get(0)` (R-gated) |
| `main` | legacy `main/0`, `main/1` selected as today (G); pattern-bearing `main`, or `main(a); main(a,..r)` | **not selected**, program result returned, no error (existing "no qualifying main" behavior; uncertainty U2) (R-gated) |
| lifecycle participants | legacy and pattern-bearing groups | no binding-time rejection (no signature gate exists today); dispatch via the unified resolver; baseline-characterized (uncertainty U3) |
| `help` / `doc` / `meta` | legacy-only group | byte-identical output (G) |
| `help` / `doc` / `meta` | group with pattern records / fixed+rest pair | **still work**; `help` lists records in declaration order deterministically (shape, guard present/absent), no host objects, no captured values, no extra provenance; `doc`/`meta` follow the three-channel rules (R-gated) |
| negatives for all | fixed+rest same-minimum group `f(x)=…; f(x,..r)=…` (reports `sorted_arities() == [1]`) | rejected by route/HTTP/test/main where their contract is exact-one-record, proving arity-set inspection alone is insufficient |
Host-local tests inspect each consumer predicate directly (no server/network); a table of `(group shape → accepted?)` per consumer is asserted, and a grep-level test ensures no consumer calls `get(n)` on a group with more than one record without a cardinality check.

### C-D8 — grouped-body declaration identity (**PENDING D8 VERIFICATION — expected outputs below are Option A and are NOT locked until Codex confirms contract/design consistency; a "conflict" verdict changes only these rows**)
| ID | Source | Expected under Option A |
| --- | --- | --- |
| model-b-c-d8-grouped-decl-one-key | `f(a) = (0) -> "z" \| (n) -> n + a` then `f(a, b) = a + b`; `[f(0), f(3), f(1, 2)]` | installs; `out: ["z", 6, 3]` (grouped case behaves as today; G for the legacy portion, ungated) |
| model-b-c-d8-arm-vs-later-clause-no-dup | `f(x) = (0) -> "arm" \| (n) -> n`; `f(0) = "clause"`; `f(0)` | **no duplicate error** (distinct declaration-level keys); `out: "arm"` (header catch-all matches first; later clause unreachable, B8) — PENDING D8 VERIFICATION (design §3.2 tension) |
| model-b-c-d8-clause-before-grouped | `f(0) = "clause"`; `f(x) = (0) -> "arm" \| (n) -> n`; `[f(0), f(5)]` | installs; `out: ["clause", 5]` — PENDING D8 VERIFICATION |
| model-b-c-d8-case-miss-no-fallthrough | `f(x) = (0 -> x)`; `f(y) ? y > 5 = "later"`; `f(9)` | `err: No matching case for function f/1 with arguments [9]` — the grouped declaration's header matched first, so its miss does not reach the later clause — PENDING D8 VERIFICATION |
| model-b-c-d8-legacy-dup-unchanged | `f(a) = (0) -> 1 \| (n) -> 2`; `f(b) = 3` | `err: Duplicate function definition: f/1` (same declaration-level key; preserved; G) |
| model-b-c-d8-prefix-and-capture | block-prefix program (P19) and header-capture grouped program inside a multi-record group | prefix once per call, header capture preserved (G for legacy, unchanged) |
| model-b-c-d8-optimizer-equivalence | `pick(n, xs)` recursion (C-OPTIM) inside a group that also has a pattern clause | optimized == unoptimized; derived arm info retained, same declaration key |
| host-local `d8-derived-arms-retained-not-checked` | inspect the record: declaration key present; derived arm keys/ordinals retained; Slice C duplicate check consults only the declaration key | PENDING D8 VERIFICATION |
If Codex reports a conflict with design §3.2, the alternative (arm keys participate: `model-b-c-d8-arm-vs-later-clause-no-dup` becomes the `open-function-duplicate-clause` error) goes to the maintainer; this plan does not choose it.

### C-IMM — Slice B interaction
`x =: 1` then `x(a)=a` and `x(0)=1`: both fail before any clause installs (`err: Cannot rebind immutable binding: x`; exact text from Slice B specs); `f(a)=a; f =: 1` fails (`Cannot declare immutable binding f: name is already bound in this scope`); declaration over an import alias or parameter name per Slice B policy; `_meta_define` cannot append to an immutable-owned name (host-local).

### C-META — three metadata channels (contract §5.1)
G (ungated, baseline already true — verify and keep): binding `@doc` merges onto the declaring binding across later clauses; newer key overwrites, unmentioned keys retained; an unannotated alias gets no copy; inline docstring shared across legacy clauses and visible through an alias; conflicting inline docstring on a valid added arity fails **before** installation (prior callable and doc unchanged; identical docs accepted); reviewer-observed trio: `@doc "canonical"` + inline `"inline"` + alias-only `@category "alias-category"` → `doc("f") == "canonical"`, `doc("a") == "inline"`, alias metadata contains the category, `help("f")` renders `inline` plus the alias category (a single unified map would fail this). R-gated: pattern clauses accept the annotations legal on legacy clauses; `help(name)` for a group with pattern records lists records in declaration order deterministically without host objects; `help` for legacy-only groups is **unchanged** (not authority to change all ordinary help output).

### C-ANN — annotation publication (contract §5.2, C6)
Separate cases, each with an explicit pre/post observation: (1) later annotation suppressed: `@doc 7` on a valid new arity → first failure stops, a later annotation expression (effect-logged via `Ref`) never runs; (2) retained old metadata: earlier successfully attached metadata unchanged and no partial map; (3) installed clause visible: after the failed declaration the new clause is callable through an **earlier alias**; (4) conflicting inline doc fails before install; (5) effects of already executed annotation expressions persist; (6) REPL recovery: the failure leaves the session usable and the group unchanged except the installed clause. Observed note: `@doc 7` currently raises `@doc annotation expected a string, received int` (exact text re-confirmed in the baseline; clause-installed-after-failure behavior is a baseline characterization, G for legacy, R-gated for pattern clauses).

### C-ERR — diagnostics and leakage
Protected (R10) sentinel as an argument never appears in no-matching-case/duplicate/ownership diagnostics; no filesystem path or `0x…` address in any new diagnostic; ownership diagnostics name only the canonical module identity or `<entry>`.

### C-MODE — mode equivalence and REPL
File / `-c` / import / piped equivalents; REPL group growth; a failed declaration (duplicate, immutable, ownership) leaves the group unchanged and the name usable; incomplete multi-line input stays incomplete. `requires: repl` exactly where existing CLI REPL cases require it.

### C-STAGE — E and D boundary negatives (C8)
| ID | Source | Expected |
| --- | --- | --- |
| model-b-c-stage-closed-rejected | `print("before"); f(0) =: { print("child"); 0 }` | `out: before`, `err: Error: model-b-not-implemented: declaration evaluation is not available`; `child` never printed; no provisional binding (`f` undefined afterwards); no partial closed clause installed (G for rejection; stays after `IrPatternFuncDef` becomes executable) |
| model-b-c-stage-closed-pattern-child | direct closed group whose child is `IrPatternFuncDef` (host-local) | child not installed independently; same rejection |
| model-b-c-stage-mixed-operators | `f(x)=x; f(y)=:y` contiguous | parse error before execution (Slice A pins stay) |
| model-b-c-stage-ordinary-target | covered in C-OWN | D owns the change |

### C-IR — carriers and traversal
Existing `spec/ir/model-b-a-*` byte-stable (G); host-local direct-IR twins of every R eval case that is source-expressible; malformed direct `IrPatternFuncDef` rejected (existing); `iter_ir_nodes` reaches pattern bodies/guards; optimizer never reorders/merges declarations or annotations.

## 3. Host-local Python test inventory (`tests/unit/test_model_b_slice_c*.py`)

1. Group record API: ordered records, derived arity index consistent for legacy-only groups, owner/provenance field.
2. Key walker as a pure function over lowered IR against the §2.2 table and C-KEY rows; **no `repr`/host equality fallback**; malformed structure rejected deterministically.
3. Writer atomicity and reentrancy (C6), barriers and bounded joins, both orderings: two threads declaring the same key → one wins; declaration racing `=:`/rebind of the name → no bypass; annotation or guard callback that reenters evaluation and adds a declaration or changes a binding → no deadlock, no partial publication, no dictionary-iteration failure, selected clause's bindings unaffected; user code never runs under `_BINDING_LOCK`. **Not asserted:** a stronger in-flight snapshot guarantee or rollback of effects (not approved).
4. Arity-keyed consumers (C-CONSUMER).
5. Autoload/prelude twin of `test_autoload_resolution_matches_non_autoload` with pattern clauses; P12 characterization.
6. Exception-class identity for P3/P7/P8/P20 (existing tests unmodified).
7. Source ↔ direct-IR equivalence for every source-expressible R case.
8. Optimizer on/off equivalence (C-OPTIM).

## 4. Expected RED outcome and capability requirements

- Every **R** case fails today with a recorded message (mostly `model-b-not-implemented: declaration evaluation is not available`, `Duplicate function definition`, or accepted-but-wrong output for P5/P10/P11); every **G** case passes today and must stay passing; record `selected/passed/failed/invalid` counts like the Slice B RED note and keep unsupported counts separate.
- Requirements: R-gated cases `default_open_functions` (+ `multi_file_eval` for module cases, `open_functions` for explicit-R20 delta cases, `repl`, `refs`, `immutable_bindings` as used). G cases: original requirements. The P5 tripwire is ungated because it changes ungated ordinary behavior; it is run by the RED harness directly and by the normal runner after GREEN.
- **Non-negotiables:** no existing spec edited, weakened or re-tagged; no genuine failure classified `unsupported`; C++ "unsupported" is never reported as PASS; the pre-existing C++ R20 duplicate-clause discrepancy is not hidden inside the Model B gap entry.

## 5. Implementation surfaces mapped to RED families

| Surface | Families |
| --- | --- |
| `callable.py` group records, key walker, dispatch adapter | C-KEY, C-DISP, C-HDR, C-OPT |
| `evaluator.py` `IrFuncDef`/`IrPatternFuncDef` branches, body preparation | C-PAT, C-HDR, C-ANN, C-IMM, C-IR |
| `optimizer.py` / `interpreter.py` optimize boundary | C-OPTIM |
| `environment.py` `define_function`, ownership, lock | C-OWN, C-IMM, writer atomicity |
| `builtins.py`, `values.py`, `equality.py`, consumer modules | C-META, C-CONSUMER, C-ERR |
| manifest, known gaps, `hosts/python/protocol_adapter.py` | §1 staging, C++ gap |

## 6. Documentation and architecture plan (only after verified GREEN)

Process/conformance history stays in `.genia/process/` and release evidence; authoritative semantic files describe behavior only, and the **local partial boundary**, never completed Model B.

| File | Change after GREEN | True until then |
| --- | --- | --- |
| `GENIA_STATE.md` | §3: ordinary pattern/guard headers execute (Python); local default-open ordinary groups, typed duplicate keys, ownership rule; retire "Default-open dispatch … unimplemented" for the local part only, keep "linking and closed publication remain unimplemented"; §4: unified shape-stratum dispatch and the **P5 migration note**; §4.7: explicit `open`/`extend`/`use` unchanged and still the only cross-module extension; `idioms.clauses` paragraph; word budget by distillation; anchors preserved | pattern headers fail with `model-b-not-implemented` |
| `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md` | the "Model B declarations: partial support" block updated identically; REPL group-growth and failed-declaration behavior | same |
| `docs/architecture/core-ir-portability.md` | `IrPatternFuncDef` evaluable outside closed groups; label stays `0.1.0` | no new node |
| `docs/architecture/executable-semantic-conformance.md`, `docs/host-interop/HOST_CAPABILITY_MATRIX.md`, `HOST_PORTING_GUIDE.md`, `capabilities.md` | `default_open_functions` row (Python supported, C++ unsupported/gap #1269); C0 staging described as evidence process, not semantics | do not claim C++ |
| `docs/design/pre-r29-…-contract-DRAFT.md`, `…-design.md` | status lines only; no semantic rewrite | approved semantics unchanged |
| `docs/contract/semantic_facts.json` (`mcp_language_profile`), `apps/mcp/mcp.genia` | update `clauses` idiom and discovery facts: ordinary pattern/multi-clause execution; **ordinary-base linking and closed functions unavailable; explicit R20 `open`/`extend`/`use` still implemented**; regenerate with `tools/gen_mcp_language_profile.py`; run its check, `test_state_anchors_and_registry_sync.py`, `test_semantic_doc_sync.py` | not regenerated before GREEN |
| `docs/ai/LLM_CONTRACT.md` | revise the "literal first parameter needs `open`" sentence | |
| `docs/book/*`, `docs/cheatsheet/*` | classified pattern-clause examples; sidecar validation if runnable examples change | |
| maintained-code docs / `tools/code_documentation.py` | new and changed callables documented per `docs/contract/code-documentation.md` | |

Banned certainty phrases are not used; examples carry classification; Python-only behavior is labelled.

## 7. Process after GO

C0 (reviewed) → RED commit + evidence note → GREEN → maintainability review (`docs/process/code-maintainability-review.md`, over the diff and call sites) → docs commit → independent skeptic audit → distillation → final-head CI (both loopback partitions) → maintainer merge. The temporary #1226 dogfooding observation applies to the eventual substantial task, not to this docs-only revision.
