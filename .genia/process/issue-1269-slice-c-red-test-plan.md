# #1269 / #1250 — Model B Slice C RED test plan, host plan and documentation plan (revision 6)

**Revision 6 (documentation only):** the executable inventory is **§R6 at the end of this file** (116 shared cases with source, category, requirements, expected stdout/stderr/exit, baseline, oracle status and C++ row; host-local items HL-15…HL-24; reconciliation with the 127 ids below). Sections 2 and 3 below keep their rationale but are superseded wherever a row differs. **Revision 5 (documentation only):** the exact case IDs, oracle statuses, harness specification, R1 command/CI matrix, R3 GREEN gate, R4 diagnostic disposition, R5 manifest/documentation sequence and the recorded-not-approved G1 are in `issue-1269-slice-c-red-authorization-package.md`, which supersedes the inventory below wherever they differ; corrections are listed in its §8.4. C0 is merged (PR #1273).

**Status: PLAN ONLY — no test, spec, manifest, adapter or production file is added by this document. RED is NO-GO** until the gate in `issue-1269-slice-c-preflight.md` §12 is cleared. Revision 4 (from head `abd10bdb`) applies Codex's verification (`6324998154`), the integration reconciliation (`6325204788`) and the coordination comment (`6326404613`): the temporary `main` compatibility boundary and stop conditions (new family **C-MAIN**), D8 mandatory arm-information retention with forward/reverse/terminal-miss/legacy-duplicate oracles, corrected C0 capability-evidence terminology, and the verified D3b consumer facts. D1, the numeric structural-key rule, D3, D5, D6, D7 and the D8 interpretation are not reopened; C1–C8 obligations and all R20 coverage are retained. D8 is **verified as a contract interpretation**, so the `PENDING D8 VERIFICATION` labels are retired. Literal strings for new diagnostics are RED oracles byte-characterized against the observed baseline before being locked (maintainer directive); none is locked by this plan. **A case that would need an unapproved choice is a stop condition (SC-*), never an invented expectation.**

Conventions (reused, nothing new): shared cases are `spec/{eval,error,cli}/model-b-c-*.yaml` run by the existing R16 runner. **Old behavior keeps its original applicability** — a regression twin for behavior that needed `open_functions`, `multi_file_eval`, `repl`, `refs`, `flow_phase_1` or `immutable_bindings` keeps exactly that `requires`; behavior that was ungated stays ungated. Only genuinely new behavior is gated by `default_open_functions` (plus the concern-specific capabilities it uses). Required capabilities (`parser`, `ast_lowering`, `core_ir_eval`, `doc_help`) are never relaxed. Historical `r20-*` specs and `tests/unit/test_r20_*` are **not duplicated, renamed or edited**; where they already cover behavior this plan cites them and adds only the missing counterexamples.

Expected-output notation: `out:` = stdout, `err:` = stderr line (exact text, `Error: ` prefix, exit 1). Strings for **new** failures are the pinned proposals of preflight D3; literal text is locked in the RED commit after the maintainer confirms D3/D3b/D5/D8.

## 1. RED baseline protocol and capability staging (C3, C8)

1. Record `main` SHA and `python -m tools.spec_runner` counts (measured 901 passed / 0 failed / 0 invalid on `main@79c073b`), plus the focused suites: `test_function_resolution_precedence.py`, `test_callable_runtime.py`, `test_lexical_assignment.py`, `test_r20_open_functions_*.py`, `test_model_b_slice_{a,b,b_races}.py`, `test_model_b_optimizer_regression.py`, `tests/spec/test_r20_open_functions_shared_specs.py`, F2 isolation, REPL characterization, `tests/doc`.
2. Characterize the **to verify** items: the 5 unparseable corpus files; inline Genia in Python tests (groups with ≥2 varargs minima, alias declarations); whether any existing R20 spec/test expects `true`/`1` or `1`/`1.0` to be duplicates; exact current diagnostics of each arity-keyed consumer for a wrong-shape handler; exact `Available:` rendering for varargs shapes in `No matching function`.
3. **C0 — IMPLEMENTED AND MERGED (PR #1273; independent review PASS; accepted).** Historical design text follows: it was a separate reviewed commit before RED — evidence plumbing that prevents a false capability claim (preflight §9.1): an adapter claim-status override set `_VOCABULARY_ONLY_CAPABILITIES` (initially empty; empty ⇒ advertised map exactly unchanged) reports listed names `unsupported`; `test_python_claimed_capabilities_covers_the_full_vocabulary` keeps `set(claimed) == known_capabilities()` and gains a vocabulary-only-is-`unsupported` assertion. No protocol, runner or manifest-format change; this does not mean a contract SHA stays frozen across commits.
4. **RED commit:** `spec/manifest.json` gains `default_open_functions` **and** the name is added to the override set (Python then reports `unsupported`); `spec/known_host_gaps.json` gains the C++ entry (tracking `m0smith/genia-2026#1269`, exact case IDs); gated cases are added. **Terminology:** under *external-host* execution (`--host`) gated cases are reported **`unsupported`** before invocation — not "skipped", not passing evidence; an all-`unsupported` green exit proves no new conformance. A *pytest skip* is a different test-framework event and is not used for this. The default *in-process* run (`python -m tools.spec_runner`, no `--host`) does **not** apply the external-host gate and would execute and fail the gated cases; the RED baseline records which runs CI requires (preflight U7) and neither hides nor reclassifies them. RED failures are produced by `tests/spec/test_model_b_slice_c_red.py`, a direct host-local runner over the **same YAML**, the existing `execute_spec`/`run_case` and the existing `compare_spec`, with ordinary assertions, auto-collected, selecting every intended case (including ungated P5 and the ungated C-MAIN guards), retaining actual errors/output, never converting a failure into skip/xfail/`unsupported`, and with no second evaluator or expected-output store. It fails with recorded messages. Ungated/old-capability guards run normally and must pass. Counts are reported as failed / passed / invalid / unsupported separately; non-vacuous selected-case counts are asserted.
5. **GREEN commit:** remove the name from the override set in the same commit that makes the gated cases pass, so `supported` is true when claimed; GREEN cites the RED SHA; delete the override if empty (or keep the small generic set with coverage); convert the harness to a thin ordinary shared-case wrapper. The Slice B provisional-claim precedent is acknowledged and not repeated. Old tests and capabilities are neither re-tagged nor downgraded.
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
| model-b-c-open-lambda-factory-distinct | **corrected source** `mk(k) { g = (x) -> x + k; g }`; `a = mk(1)`, `b = mk(2)`; `[a(1), b(1), a == a, a == b]` (the original `mk(k) = (x) -> x + k` is a grouped-body arm, not a lambda — observed `mk(1)` → `2`) | `out: [2, 3, true, false]` (observed) | G |
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
| model-b-c-disp-p5-migration-fixed-clause | add exact `f(a, b)="exact2"` | `f(1,2)` → `"exact2"` (documented migration fix); **R-gated, not G**: today this program fails with `Duplicate function definition: f/2` (fixed+rest at the same required arity) |
| model-b-c-disp-p5-migration-drop-lower | only `f(a, b, ..s)` | `f(1,2)` → `"min2"` |
| model-b-c-disp-p7-same-arity-ambiguity | `f(a,..r); f(a,b,..s); f(1,2,3)` | `err: Ambiguous function resolution: f/3. Matching varargs: f/1+, f/2+` (G) |
| model-b-c-disp-fixed-over-varargs | `pick(a,b)="exact"; pick(a,..rest)="varargs"; pick(1,2)` / `(1,2,3)` | `"exact"` / `"varargs"` (G; existing `test_function_resolution_precedence.py` stays) |
| model-b-c-disp-fixed-and-varargs-same-arity | `f(a)=1; f(a,..r)=2; [f(1), f(1,2)]` | `out: [1, 2]` (P4, error→valid), R-gated |
| model-b-c-disp-no-matching-function | P8 | `err: No matching function: f/2. Available: f/1` byte-identical (G) |
| model-b-c-disp-no-matching-function-new-group | `f(x)=1; f(x,y)=2; f(x,..r)=3; f()` | `err: No matching function: f/0. Available: f/1, f/2, f/1+` (R-gated; baseline today `Duplicate function definition: f/1`; the `open` twin already yields this exact text; renderer = `OpenFunctionNoMatchingFunctionError`, re-characterized byte-for-byte before locking) |
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
| model-b-c-optim-keys-retained | host-local, **mandatory (D8)**: the original grouped-body arm keys, ordinals and provenance of the optimized declaration are retained or losslessly derivable from the unoptimized semantic structure and **equal** the unoptimized ones — including the recursive arm that `optimize_nth_style_recursion` does not keep in `IrListTraversalLoop`; deriving them from the optimized node alone must fail this case; `IrListTraversalLoop` never serialized as portable IR |
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

### C-CONSUMER — special consumers (D3b APPROVED; facts independently verified)
Legacy-only groups: **identical** behavior to today for every consumer (G, byte-for-byte, including `@test`'s existing absence of a rest-parameter check). Consumers are **not** treated uniformly: route and outbound HTTP annotations require fixed signatures with **no rest parameter**; `@test` and `main` have different established arity behavior; lifecycle binding has no signature gate; `help`/`doc`/`meta` are introspection. **No blanket rejection merely because a callable has pattern clauses** — a rejection exists only where the consumer's existing predicate is an exact single fixed record. No representative record is ever chosen.
| Consumer | Case | Expected |
| --- | --- | --- |
| `@route` (fixed arity 1, `rest_param is None`) | handler `h(req) = …` legacy | accepted (G) |
| `@route` | handler with a pattern clause `h({path: p}) = p`; handler `h(r)=…; h(r,..x)=…` (fixed+rest same minimum); handler `h(r, ..x)` alone | discovery diagnostic `@route handler must expose exactly one fixed one-argument function arm` for the first two (R-gated); the third is unchanged (already rejected today, G) |
| HTTP annotations (`@get`/`@post`, `send_annotated`; fixed arity 0, no rest) | zero-arg legacy accepted (G); pattern-bearing or `f(); f(..r)` mixed | `TypeError: send_annotated expected a fixed zero-argument function` (R-gated, host-local) |
| `@test` (arity set `[0]`; **no** rest check) | legacy `f()` accepted (G); legacy `f(..r)` exactly as today (G); group with a pattern record, or a fixed+rest pair | discovery unit `@test functions must take zero arguments`; test body not run, no representative `get(0)` (R-gated) |
| `main` (file/command entry; no mismatch diagnostic exists) | see **C-MAIN** — temporary compatibility boundary (preflight §2.5.1), stop conditions SC-MAIN-1…5 | |
| lifecycle participants (**no signature gate**; accepts function/group/callable) | legacy group; pattern-bearing group; fixed+rest group | **no new binding-time rejection**; all bind; invocation uses ordinary Slice C dispatch with the lifecycle's exact argument count (e.g. a pattern-bearing participant matched/missed exactly like a direct call; miss identity = case-miss `RuntimeError`). Baseline-characterized for legacy (G); pattern groups R-gated. **U3 resolved** |
| `help` / `doc` / `meta` | legacy-only group | byte-identical output (G) |
| `help` / `doc` / `meta` | group with pattern records / fixed+rest pair | **still work (usable, not rejected)**; `help` lists records in declaration order deterministically (shape, guard present/absent), no host objects, no captured values, no extra provenance; `doc`/`meta` follow the three-channel rules (R-gated) |
| negatives for the exact-single-record consumers | fixed+rest same-minimum group `f(x)=…; f(x,..r)=…` (reports `sorted_arities() == [1]`) | rejected by route/HTTP/`@test` where their contract is exact-one-record, proving arity-set inspection alone is insufficient; `main` per SC-MAIN-4 (stop condition) |
Host-local tests inspect each consumer predicate directly (no server/network); a table of `(group shape → accepted?)` per consumer is asserted — with the lifecycle and `help`/`doc`/`meta` columns asserting *accepted/usable* so a blanket rejection fails — and a grep-level test ensures no consumer calls `get(n)` on a group with more than one record without a cardinality check.

### C-MAIN — temporary `main` compatibility boundary (U2; preflight §2.5.1; architecture in #1271, not Slice C)
Each case below fixes **what executes, what does not execute, the returned value and the absence of unintended side effects.** Cases are CLI-shaped like `spec/cli/file_mode_main_argv` (sibling `.genia` file plus YAML) unless marked host-local. Expected stdout is shown one line per `/`. The pattern in each R-gated program **matches the supplied argv**, so a selector that did pattern-based discovery would visibly run the clause body (making the case non-vacuous).

Guards — baseline-observed, ungated, original applicability, must stay passing through every refactor:
| ID | Program | argv | Expected | Proves |
| --- | --- | --- | --- | --- |
| model-b-c-main-legacy-main1-preferred (M1) | `main(args) = { print("main1"); 11 }`; `main() = { print("main0"); 10 }`; `print("top")`; `42` | `[]` | `top` / `main1` / `11`; exit 0 | `main/1` wins; `main/0` does **not** run; result replaces `42` |
| model-b-c-main-legacy-main0-fallback (M2) | `main() = { print("main0"); 10 }`; `print("top")`; `42` | `[]` | `top` / `main0` / `10` | `main/0` fallback |
| model-b-c-main-legacy-rest-main-selected (M3) | `main(a, ..r) = { print("mainrest"); 12 }`; `print("top")`; `42` | `[]` | `top` / `mainrest` / `12` | **legacy rest-parameter `main` is still selected** (the derived legacy index must keep it keyed at its required arity) |
| model-b-c-main-no-qualifying (M4) | `main(a, b) = { print("main2"); 12 }`; `print("top")`; `42` | `[]` | `top` / `42`; no `main2` | no `main/1`/`main/0` → source result retained, **no diagnostic** |
| model-b-c-main-command-mode (M5) | `-c 'main(a) = { print("cmdmain"); a }` newline `print("top")'` | `["x", "y"]` | `top` / `cmdmain` / `["x", "y"]` | command mode uses the same selector |
| model-b-c-main-repl-never-selects (M6) | REPL submission `main() = { print("ran"); 1 }` | — | transcript shows `<function main/0>` and **no** `ran`; `requires: repl` | REPL activation unchanged (exact transcript framing characterized in the baseline) |
| existing `file_mode_main_argv`, `pipe_mode_bypass_main` | unmodified | | per YAML | pipe bypass and file `main(argv())` unchanged |

New behavior — **R-gated** (`default_open_functions`; today they fail with `model-b-not-implemented: declaration evaluation is not available`, M7):
| ID | Program | argv | Expected | Proves |
| --- | --- | --- | --- | --- |
| model-b-c-main-pattern-not-selected | `print("top")`; `main(["--x"]) = { print("pattern-main"); 1 }`; `42` | `["--x"]` | `top` / `42`; exit 0; **no** `pattern-main`; returned value `42`, not `1` | executes: top-level statements only; does not execute: the clause body; returned value: source result |
| model-b-c-main-pattern-guard-not-evaluated | `ping() = { print("guard-ran"); true }`; `main(args) ? ping() = { print("body"); 1 }`; `print("top")`; `42` | `["a"]` | `top` / `42`; no `guard-ran`, no `body` | no guard is evaluated to choose an entry (rule 2) |
| model-b-c-main-wildcard-not-selected | `main(_) = { print("wild"); 7 }`; `print("top")`; `42` | `[]` | `top` / `42`; no `wild` | wildcard header is pattern-bearing (M7 classification) |
| model-b-c-main-multi-pattern-group-not-selected | `main(["a"]) = { print("A"); 1 }`; `main(["b"]) = { print("B"); 2 }`; `print("top")`; `42` | `["a"]` | `top` / `42`; no `A`, no `B` | no representative clause of a pure-pattern group is picked |
| model-b-c-main-pattern-command-mode | `-c` with the single-pattern program | `["x", "y"]`, pattern `main(["x", "y"])` | source result only, no body output | same boundary in command mode |
| model-b-c-main-explicit-call-dispatches | `main(["--x"]) = { print("pattern-main"); 1 }`; `print(main(["--x"]))`; `42` | `["--x"]` | `pattern-main` / `1` / `42` — `pattern-main` **exactly once** | explicit direct call uses ordinary dispatch (rule 7); the entry convention neither re-runs nor suppresses it |
| model-b-c-main-explicit-call-miss | `main(["--x"]) = 1`; `main(["--y"])` | `[]` | `RuntimeError` `No matching case for function main/1 with arguments …`, exit 1; full argument rendering characterized in the baseline (U4) | ordinary case-miss identity, not a new `main` diagnostic |
| model-b-c-main-test-mode-unchanged | `--test` file with a `@test` function and a pattern-bearing `main` | | the `@test` runs; `main` produces no output (legacy-`main` twin characterized in the baseline, G) | test activation unchanged (rule 6) |
| host-local structural | `_resolve_program_result` is reached only from the `command` and `file` branches; no pattern/guard evaluation occurs in it; no new error category named for `main` exists | | | rules 2, 4, 6 |

**Stop conditions — deliberately NOT cases (no expectation manufactured). Revision 5: the integration owner's *recommended* G1 invariant (package §7, not yet approved) would turn these into reserved `model-b-c-main-g1-*` GREEN-entry cases; until the maintainer approves G1 they remain stop conditions:**
| ID | Mixed shape | Why stopped |
| --- | --- | --- |
| SC-MAIN-1 | legacy `main()` + pattern record(s) of another arity | per-arity-key vs whole-group readings diverge; neither approved |
| SC-MAIN-2 | legacy `main/1` + pattern record(s) of another arity | same |
| SC-MAIN-3 | legacy `main/1` and a pattern arity-1 record (either order) | direct selection bypasses declaration order; dispatch is pattern-based discovery (rule 2) |
| SC-MAIN-4 | fixed+rest same minimum | any pick is a representative record (rule 5) |
| SC-MAIN-5 | legacy rest `main(a, ..r)` + pattern arity-1 record | as SC-MAIN-3 |
The harness must not contain an "any outcome", skipped or xfail placeholder for these. If the integration owner wants them covered, a maintainer disposition (or #1271's gates) comes first; the RED phase then stops per the design §11 stop condition rather than choosing.

### C-D8 — grouped-body declaration identity (Option A; **verified as a contract interpretation by Codex `6324998154`**; preflight §2.6)
Local duplicate detection uses **declaration-level keys** for ordinary grouped-body declarations. Original grouped-body arm keys, ordinals and necessary provenance **MUST** be retained or remain losslessly derivable from the unoptimized semantic structure. Existing explicit R20 `open` grouped-arm flattening is **unchanged** (cited, not duplicated). Expected outputs below are recommendations from the verified interpretation; they are characterized in the RED baseline (the pattern-header forms fail today with `model-b-not-implemented`) and locked in the RED commit.
| ID | Source | Expected |
| --- | --- | --- |
| model-b-c-d8-forward-collision | `describe(x) = (0) -> "zero" \| (n) -> "other"`; `describe(0) = "ZERO"`; `[describe(0), describe(7)]` | both install, **no arm-duplicate error**; `out: ["zero", "other"]` (earlier all-bind header wins and its body selects an arm; later `describe(0)` unreachable, B8). R-gated |
| model-b-c-d8-reverse-collision | `f(0) = "clause"`; `f(x) = (0) -> "arm" \| (n) -> n`; `[f(0), f(5)]` | installs; `out: ["clause", 5]`. Local arm-key checking would reject — that outcome fails the case. R-gated |
| model-b-c-d8-terminal-grouped-miss | `f(x) = (0 -> x)`; `f(y) ? y > 5 = "later"`; `f(9)` | `err: No matching case for function f/1 with arguments [9]` (`RuntimeError`); returning `"later"` fails the case — the selected grouped body's miss is terminal. R-gated |
| model-b-c-d8-earlier-pattern-miss-continues | `f(0) = "zero"`; `f(x) = (1) -> "one"`; `f(5)` | the earlier pattern header misses and the next declaration is tried; its grouped body then misses terminally: `err: No matching case for function f/1 with arguments [5]` (invariant 2: only an earlier *pattern-header* miss continues). R-gated |
| model-b-c-d8-legacy-identical-header-dup | `describe(x) = (0) -> "zero" \| (n) -> "other"`; `describe(y) = "later"` | `err: Duplicate function definition: describe/1` — identical all-bind declaration key; legacy identity preserved byte for byte (G, ungated) |
| model-b-c-d8-grouped-decl-one-key | `f(a) = (0) -> "z" \| (n) -> n + a`; `f(a, b) = a + b`; `[f(0), f(3), f(1, 2)]` | installs; `out: ["z", 6, 3]` (G for the legacy portion, ungated) |
| model-b-c-d8-prefix-and-capture | block-prefix program (P19) and header-capture grouped program inside a multi-record group | prefix once per call, before the guard; header capture preserved; arm bindings shadow headers; guards/matchers once per attempted match; only the selected result executes; executed effects persist on failure (G for legacy, unchanged) |
| model-b-c-d8-optimizer-equivalence | `pick(n, xs)` recursion (C-OPTIM) inside a group that also has a pattern clause, plus a **later** declaration | source = unoptimized Core = optimized: values, errors, effects, order and duplicate decisions (including the later declaration after an optimized one) identical |
| model-b-c-d8-r20-flattening-unchanged | `open f(x) = (0) -> 1 \| (n) -> 2`; `f(0) = 3` | still rejected as an explicit-open duplicate (existing `r20-*` behavior; cited from the existing specs, not copied). Option A applied to `open` fails this case |
| host-local `d8-arms-retained-not-checked` | inspect the declaration record: one declaration key; **original arm keys/ordinals/provenance present or losslessly derivable from the unoptimized structure** (also after the optimizer rewrote the body); Slice C duplicate checks consult only the declaration key; no user code ran while computing keys | |
Retained arm keys are evidence for Slice D, not permission to treat body alternatives as independent linked-view candidates; no D linking oracle is locked here.

### C-IMM — Slice B interaction
`x =: 1` then `x(a)=a` and `x(0)=1`: both fail before any clause installs (`err: Cannot rebind immutable binding: x`; exact text from Slice B specs); `f(a)=a; f =: 1` fails (`Cannot declare immutable binding f: name is already bound in this scope`); declaration over an import alias or parameter name per Slice B policy; `_meta_define` cannot append to an immutable-owned name (host-local).

### C-META — three metadata channels (contract §5.1)
G (ungated, baseline already true — verify and keep): binding `@doc` merges onto the declaring binding across later clauses; newer key overwrites, unmentioned keys retained; an unannotated alias gets no copy; inline docstring shared across legacy clauses and visible through an alias; conflicting inline docstring on a valid added arity fails **before** installation (prior callable and doc unchanged; identical docs accepted); reviewer-observed trio: `@doc "canonical"` + inline `"inline"` + alias-only `@category "alias-category"` → `doc("f") == "canonical"`, `doc("a") == "inline"`, alias metadata contains the category, `help("f")` renders `inline` plus the alias category (a single unified map would fail this). R-gated: pattern clauses accept the annotations legal on legacy clauses; `help(name)` for a group with pattern records lists records in declaration order deterministically without host objects; `help` for legacy-only groups is **unchanged** (not authority to change all ordinary help output).

### C-ANN — annotation publication (contract §5.2, C6)
Separate cases, each with an explicit pre/post observation: (1) later annotation suppressed: `@doc 7` on a valid new arity → first failure stops, a later annotation expression (effect-logged via `Ref`) never runs; (2) retained old metadata: earlier successfully attached metadata unchanged and no partial map; (3) installed clause visible: after the failed declaration the new clause is callable through an **earlier alias**; (4) conflicting inline doc fails before install; (5) effects of already executed annotation expressions persist; (6) REPL recovery: the failure leaves the session usable and the group unchanged except the installed clause. Observed note: `@doc 7` currently raises `@doc annotation expected a string, received int` (exact text re-confirmed in the baseline; clause-installed-after-failure behavior is a baseline characterization, G for legacy, R-gated for pattern clauses).

### C-ERR — diagnostics and leakage
Protected (R10) sentinel as an argument never appears in no-matching-case/duplicate/ownership diagnostics; no `0x…` address in any new diagnostic. **Path policy (R4, revision 5):** the existing R20 duplicate-clause renderer is preserved for pattern-clause duplicates, including its file-mode entry label (the host-resolved path; shared oracles use the `<command>` label, file mode is pinned host-locally); the no-path rule applies to the new ownership / foreign-alias diagnostics (canonical module identity or `<entry>` only) and designated sanitized surfaces — see the package §5. File-mode duplicate oracles stay unlocked until the design-text clarification (package §5.5) is confirmed.

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
8. Optimizer on/off equivalence (C-OPTIM), including retention of original arm information (D8 invariant 4).
9. C-MAIN structural checks and consumer acceptance table (lifecycle and `help`/`doc`/`meta` accept pattern groups).
10. Capability evidence (only if C0 is authorized): exact-unchanged advertised map for the empty prerequisite; vocabulary-only name reports `unsupported`; external-host path reports `unsupported` without invoking the adapter; direct same-YAML comparator failure surfaces as a failure; unchanged old requirements; non-vacuous selected-case counts.

## 4. Expected RED outcome and capability requirements

- Every **R** case fails today with a recorded message (mostly `model-b-not-implemented: declaration evaluation is not available`, `Duplicate function definition`, or accepted-but-wrong output for P5/P10/P11); every **G** case passes today and must stay passing; record `selected/passed/failed/invalid` counts like the Slice B RED note and keep `unsupported` counts separate (an `unsupported` case is never passing evidence; a pytest skip is a separate event and is also reported separately).
- Requirements: R-gated cases `default_open_functions` (+ `multi_file_eval` for module cases, `open_functions` for explicit-R20 delta cases, `repl`, `refs`, `immutable_bindings` as used). G cases: original requirements. The P5 tripwire is ungated because it changes ungated ordinary behavior; it is run by the RED harness directly and by the normal runner after GREEN.
- **Stop conditions are not cases:** SC-MAIN-1…5 are recorded in C-MAIN and produce no test, placeholder, skip or xfail.
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
| `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md` | the "Model B declarations: partial support" block updated identically; REPL group-growth and failed-declaration behavior; **file/command entry-selection caveat**: only legacy-style `main` is auto-selected, a pattern-bearing `main` is not (temporary compatibility boundary pending the host-selected application lifecycle, [#1271](https://github.com/m0smith/genia-2026/issues/1271)); explicit calls dispatch normally | same |
| `docs/architecture/core-ir-portability.md` | `IrPatternFuncDef` evaluable outside closed groups; label stays `0.1.0` | no new node |
| `docs/architecture/executable-semantic-conformance.md`, `docs/host-interop/HOST_CAPABILITY_MATRIX.md`, `HOST_PORTING_GUIDE.md`, `capabilities.md` and any other affected host documentation | `default_open_functions` row (Python supported, C++ unsupported/gap #1269); C0 staging described as evidence process using the `unsupported` / pytest-skip / in-process distinctions, not semantics | do not claim C++ |
| `docs/design/pre-r29-…-contract-DRAFT.md`, `…-design.md` | status lines only; no semantic rewrite | approved semantics unchanged |
| `docs/contract/semantic_facts.json` (`mcp_language_profile`), `apps/mcp/mcp.genia` | update `clauses` idiom and discovery facts (including that pattern-bearing `main` is not an auto-selected entry point): ordinary pattern/multi-clause execution; **ordinary-base linking and closed functions unavailable; explicit R20 `open`/`extend`/`use` still implemented**; regenerate with `tools/gen_mcp_language_profile.py`; run its check, `test_state_anchors_and_registry_sync.py`, `test_semantic_doc_sync.py` | not regenerated before GREEN |
| `docs/ai/LLM_CONTRACT.md` | revise the "literal first parameter needs `open`" sentence; carry the `main` entry caveat | |
| `docs/book/*`, `docs/cheatsheet/*` | classified pattern-clause examples; sidecar validation if runnable examples change | |
| maintained-code docs / `tools/code_documentation.py` | new and changed callables documented per `docs/contract/code-documentation.md` | |

Banned certainty phrases are not used; examples carry classification; Python-only behavior is labelled.

## 7. Process after GO

C0 (reviewed) → RED commit + evidence note → GREEN → maintainability review (`docs/process/code-maintainability-review.md`, over the diff and call sites) → docs commit → independent skeptic audit → distillation → final-head CI (both loopback partitions) → maintainer merge. The temporary #1226 dogfooding observation applies to the eventual substantial task, not to this docs-only revision.

---

## R6. Revision-6 executable inventory (supersedes the id lists, sources and expectations in §2 and §3 above)

**DOCUMENTATION ONLY. No YAML, harness, manifest, test or runtime file is created by this section. RED is NOT authorized.** The prose rationale in §1–§6 above (C1–C8, D1/D3/D3b/D5/D8 traceability, family descriptions, documentation plan) is retained; where a row in §2 or §3 differs from this section, this section governs. Decisions this section depends on are listed in the decision register of `issue-1269-slice-c-red-authorization-package.md` §R6.0 and are **PROPOSED**, not approved.

### R6.A Legend and conventions

- **Kind:** **G** guard — passes on `main@79c073b` today with its original applicability and must stay green; **R** ungated RED tripwire — fails today, no new capability; **RG** gated RED — fails today, `requires` includes `default_open_functions` (+ concern-specific capabilities). `RG*` rows are gated under the recommended O-1 Option C and ungated (keeping their other requirements) under Option A.
- **Oracle:** *observed* — the expected value equals what the Python host printed for the program on `main@79c073b` (guards) or for the explicit-open **twin** of the same clauses (RED cases whose default-open behavior is by contract the same); *contract-derived* — no observable twin exists (noncontiguous clauses, typed numeric keys, header-frame rules) and the value follows the approved contract/design rule cited; *L* — renderer text observed on the twin, byte-locked at the RED baseline; *PROPOSED text* — the current runtime cannot emit it, so nothing is "observed"; the candidate text is the pre-flight D3 proposal and needs maintainer approval.
- **Categories:** `eval` (final value printed with a trailing newline), `error` (stdout empty, exit 1, `Error: …` on stderr), `cli` (file / `-c` / `--test` through the CLI path; runner strips trailing newlines from both streams). Cases that print before failing are `eval`, not `error`. Source locations in shared oracles are `<command>:N` (N = 1-based line of the submitted source).
- **One-shot constraint:** evaluation stops at the first failure, so no shared case observes state *after* a failure; effects before the failure are observed through stdout (`print`), not through `Ref` logs. Observations after a failure are host-local (HL-16…HL-19, HL-24).
- **No new syntax or mechanism:** every source uses constructs implemented on `main@79c073b` (named patterns, `@doc`/`@category`/`@since` prefix annotations, inline docstrings `f(x) = "doc" body`, block bodies). Nothing is invented for exception capture.
- **C++ column** is the pinned adapter `genia-cpp@44456baea06b4bb7bdf727e39939dd7150261ee6`: *PASS/FAIL/UNSUPPORTED (adapter)* were **executed** on the exact source shown; *UNSUPPORTED (existing capability gate)* is the runner's pre-invocation classification (observed for `immutable_bindings`, `multi_file_eval`, `doc_help`); *UNSUPPORTED (capability `default_open_functions` undeclared)* is **inferred** (the name is not in C++'s claims and does not exist in the manifest yet); `unsupported` is never PASS. "as specified" means the program ends in a declaration or uses a construct C++ lacks; some such programs execute and disagree when extended (see the ledger in the package §R6.2).
- The `model-b-c-` prefix is part of every id; `.yaml` stem = id; sibling `.genia` files hold CLI file sources.

### R6.B Inventory arithmetic (Option C recommended; inferred, not executed)

| Family | N | G | R | RG |
| --- | ---: | ---: | ---: | ---: |
| open | 7 | 5 | 0 | 2 |
| pat | 14 | 0 | 0 | 14 |
| key | 16 | 0 | 0 | 16 |
| disp | 12 | 5 | 1 | 6 |
| hdr | 9 | 4 | 0 | 5 |
| optim | 2 | 1 | 0 | 1 |
| opt | 6 | 2 | 0 | 4 |
| own | 13 | 7 | 0 | 6 |
| d8 | 7 | 3 | 0 | 4 |
| imm | 3 | 2 | 0 | 1 |
| meta | 7 | 6 | 0 | 1 |
| ann | 3 | 2 | 0 | 1 |
| stage | 1 | 1 | 0 | 0 |
| mode | 3 | 0 | 0 | 3 |
| main | 13 | 5 | 0 | 8 |
| **total** | **116** | **43** | **1** | **72** |

(`RG` includes the four `RG*` ownership rows, which are `own-local-alias-rejected`, `own-local-alias-varargs`, `own-alias-annotation-not-evaluated`, `own-imported-alias-rejected`.) Totals, RED/GREEN projections and workflow behavior: package §R6.3.

### R6.C Reconciliation with the revision-5 inventory (128 rows: 127 created + 1 blocked)

| Disposition | Revision-5 ids | Revision 6 |
| --- | --- | --- |
| **Excluded (O-4)** | `key-repeated-binders-distinct` | not created |
| **Moved to host-local (9, absent from the shared list)** | `open-persistent-env`, `own-local-alias-state-after-rejection`, `own-local-alias-owner-still-extendable`, `own-imported-alias-owner-unchanged`, `ann-repl-recovery`, `mode-repl-failed-declaration-leaves-group`, `main-repl-never-selects`, `key-legacy-dup-id`, `key-rest-binders-legacy-duplicate` | HL-15…HL-22 |
| **Moved to host-local after re-sourcing (5)** | `own-lambda-nonfunction-unchanged`, `own-builtin-nonfunction-unchanged`, `d8-legacy-identical-header-dup`, `ann-old-metadata-retained`, `ann-installed-clause-visible-via-alias` | HL-18, HL-21, HL-22 |
| **Replaced** | `key-named-matcher` → `key-named-matcher-distinct`, `key-named-matcher-same-dup`; `key-quote-unquote` → `key-quote-names-are-data` (active-unquote half open); `mode-file-command-import-equivalence` → `mode-file-pattern-program`, `mode-command-pattern-program`, `mode-import-pattern-program`; `own-explicit-open-unchanged` → `own-explicit-open-alias-unchanged` | counted in the 116 |
| **Unchanged ids** | all others | 116 − 7 replacement ids = 109 ids carried over unchanged |

127 − 9 − 5 + 1 + 2 = **116**. Source corrections made while pinning programs: `optim-collection-recursion` uses `0` instead of `nil` (orthogonal to the optimizer; C++ does not recognise `nil`, and the replacement lets the optimizer property be observed on C++); `meta-inline-doc-*` use the real inline-docstring syntax (`f(x) = "doc" body`), because the revision-5 programs never produced a documentation string; `hdr-guard-evaluated-once`, `hdr-guard-order`, `key-no-effects`, `own-alias-annotation-not-evaluated` observe effects with `print` instead of a `Ref` log; `key-named-matcher*`, `pat-named-matcher` use `pattern Name(v) = some(v)` per STATE.

### R6.D Shared inventory — 116 cases

##### `model-b-c-open-noncontiguous-arities`
- category `eval` · ungated guard · requires `(none)` · trace C-OPEN, contract 2.2
- source:
  ```
  f(x) = x
  g(y) = y
  f(x, y) = x + y
  [f(1), f(1, 2)]
  ```
- expected: stdout="[1, 3]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="[1, 3]\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-open-alias-sees-later-arity`
- category `eval` · ungated guard · requires `(none)` · trace contract 2.2
- source:
  ```
  f(x) = x
  a = f
  z = 0
  f(x, y) = x + y
  a(1, 2)
  ```
- expected: stdout="3\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="3\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-open-immutable-alias-stays-live`
- category `eval` · ungated guard · requires `immutable_bindings` · trace Slice B interaction
- source:
  ```
  f(x) = x
  a =: f
  f(x, y) = x + y
  a(1, 2)
  ```
- expected: stdout="3\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="3\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (existing capability gate: immutable_bindings)

##### `model-b-c-open-call-before-later-clause`
- category `error` · ungated guard · requires `(none)` · trace contract 2.2 (call before later arity)
- source:
  ```
  f(x) = x
  f(1, 2)
  ```
- expected: stdout="" stderr="Error: No matching function: f/2. Available: f/1\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: No matching function: f/2. Available: f/1\n" exit=1
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-open-pattern-after-plain`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C-PAT first match; D3
- source:
  ```
  f(x) = x
  f(0) = 9
  [f(0), f(1)]
  ```
- expected: stdout="[0, 1]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-open-noncontiguous-pattern`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace contract 2.2 noncontiguous accumulation
- source:
  ```
  f(0) = "a"
  g(y) = y
  print(f(0))
  f(1) = "b"
  [f(0), f(1)]
  ```
- expected: stdout="a\n[\"a\", \"b\"]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: contract-derived
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)
- note: explicit-open twin is invalid by design (open requires contiguous clauses), so the oracle is contract-derived

##### `model-b-c-open-lambda-factory-distinct`
- category `eval` · ungated guard · requires `(none)` · trace contract 2.2 lexical factories
- source:
  ```
  mk(k) {
    g = (x) -> x + k
    g
  }
  a = mk(1)
  b = mk(2)
  [a(1), b(1), a == a, a == b]
  ```
- expected: stdout="[2, 3, true, false]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="[2, 3, true, false]\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-pat-literal-base-case`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C-PAT; design 13.1
- source:
  ```
  fact(0) = 1
  fact(n) = n * fact(n - 1)
  fact(5)
  ```
- expected: stdout="120\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-pat-guard-selects`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C-PAT; design 13.1
- source:
  ```
  f(x) ? x > 0 = "pos"
  f(x) = "other"
  [f(1), f(-1)]
  ```
- expected: stdout="[\"pos\", \"other\"]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-pat-guard-sees-header-binding`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C-PAT; design 13.1
- source:
  ```
  f([a, b]) ? a < b = a + b
  f([a, b]) = a * b
  [f([1, 2]), f([3, 2])]
  ```
- expected: stdout="[3, 6]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-pat-match-local-shadows-outer`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C-PAT; design 13.1
- source:
  ```
  v = 99
  f([v]) = v
  f([1])
  ```
- expected: stdout="1\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-pat-list-rest`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C-PAT; design 13.1
- source:
  ```
  f([x, ..xs]) = xs
  f([1, 2, 3])
  ```
- expected: stdout="[2, 3]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-pat-map`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C-PAT; design 13.1
- source:
  ```
  f({key: x}) = x
  f({key: 5})
  ```
- expected: stdout="5\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-pat-some`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C-PAT; design 13.1
- source:
  ```
  f(some(x)) = x
  f(some(3))
  ```
- expected: stdout="3\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-pat-err`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C-PAT; design 13.1
- source:
  ```
  f(err(r, c)) = r
  f(err("bad", "ctx"))
  ```
- expected: stdout="\"bad\"\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-pat-wildcard`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C-PAT; design 13.1
- source:
  ```
  f(_) = 1
  f(7)
  ```
- expected: stdout="1\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred); informational, if executed: matches

##### `model-b-c-pat-first-match-wins`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C-PAT; design 13.1
- source:
  ```
  f(x) = 1
  f(0) = 2
  f(0)
  ```
- expected: stdout="1\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-pat-fixed-miss-no-varargs-fallthrough`
- category `error` · gated by `default_open_functions` · requires `default_open_functions` · trace D1/D3 strata
- source:
  ```
  f(0) = 1
  f(n, ..r) = 2
  f(5)
  ```
- expected: stdout="" stderr="Error: No matching case for function f/1 with arguments [5]\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-pat-fixed-miss-two-args-varargs`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C-PAT; design 13.1
- source:
  ```
  f(0) = 1
  f(n, ..r) = 2
  f(9, 8)
  ```
- expected: stdout="2\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-pat-named-matcher`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C-PAT
- source:
  ```
  pattern Id(v) = some(v)
  f(Id(x)) = x
  f(3)
  ```
- expected: stdout="3\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)
- note: named-pattern syntax per STATE named reusable patterns

##### `model-b-c-pat-string-body-is-body`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C-PAT; design 13.1
- source:
  ```
  f("a") = "doc-like"
  [f("a"), doc("f")]
  ```
- expected: stdout="[\"doc-like\", none(\"missing-doc\", {name: \"f\"})]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)
- note: doc() of an undocumented pattern group is not derivable from any authority; observed on open twin

##### `model-b-c-key-true-vs-one`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace D3 typed keys (pre-flight 2.2)
- source:
  ```
  f(true) = 1
  f(1) = 2
  [f(true), f(1)]
  ```
- expected: stdout="[1, 2]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-key-one-vs-one-point-zero`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace D3 typed keys; runtime numeric equality
- source:
  ```
  f(1) = 10
  f(1.0) = 20
  [f(1), f(1.0)]
  ```
- expected: stdout="[10, 10]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-key-same-binary64-dup`
- category `error` · gated by `default_open_functions` · requires `default_open_functions` · trace D3 duplicate; R20 renderer
- source:
  ```
  f(1.0) = 1
  f(1.00000000000000001) = 2
  ```
- expected: stdout="" stderr="Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: L: wording observed on the explicit-open twin; byte-lock at RED baseline
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-key-spelling-dup`
- category `error` · gated by `default_open_functions` · requires `default_open_functions` · trace D3
- source:
  ```
  f(0.1) = 1
  f(0.10) = 2
  ```
- expected: stdout="" stderr="Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: L: wording observed on the explicit-open twin; byte-lock at RED baseline
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-key-alpha-equivalent-dup`
- category `error` · gated by `default_open_functions` · requires `default_open_functions` · trace D3
- source:
  ```
  f([a, b]) = 1
  f([c, d]) = 2
  ```
- expected: stdout="" stderr="Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: L: wording observed on the explicit-open twin; byte-lock at RED baseline
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-key-guard-alpha-dup`
- category `error` · gated by `default_open_functions` · requires `default_open_functions` · trace D3
- source:
  ```
  f(x) ? x > 0 = 1
  f(y) ? y > 0 = 2
  ```
- expected: stdout="" stderr="Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: L: wording observed on the explicit-open twin; byte-lock at RED baseline
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-key-guard-differs-ok`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace D3
- source:
  ```
  f(x) ? x > 0 = 1
  f(x) ? x < 0 = 2
  [f(1), f(-1)]
  ```
- expected: stdout="[1, 2]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-key-free-name-syntactic`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace D3 free names are syntactic
- source:
  ```
  limit = 1
  cap = 1
  f(x) ? x > limit = "limit"
  f(x) ? x > cap = "cap"
  f(5)
  ```
- expected: stdout="\"limit\"\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-key-lambda-shadow-dup`
- category `error` · gated by `default_open_functions` · requires `default_open_functions` · trace D3 alpha normalization
- source:
  ```
  f(x) ? ((a) -> a)(x) > 0 = 1
  f(y) ? ((b) -> b)(y) > 0 = 2
  ```
- expected: stdout="<open function f>\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: L: wording observed on the explicit-open twin; byte-lock at RED baseline
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-key-lambda-shadow-outer-slot-distinct`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace D3 nested-shadow row of pre-flight 2.2 table
- source:
  ```
  f(x) ? ((x) -> x)(1) > 0 = 1
  f(x) ? x > 0 = 2
  f(5)
  ```
- expected: stdout="1\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: contract-derived
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)
- note: both clauses must install (no duplicate error); selected clause is the first

##### `model-b-c-key-quote-names-are-data`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace D3 quoted names are data
- source:
  ```
  f(x) ? x == quote(p) = "p"
  f(x) ? x == quote(q) = "q"
  [f(quote(p)), f(quote(q))]
  ```
- expected: stdout="[\"p\", \"q\"]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: contract-derived
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)
- note: replaces key-quote-unquote (quoted half only); active-unquote half is PENDING: no pinned guard-position unquote program, see decision register

##### `model-b-c-key-named-matcher-distinct`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace D3 distinct matcher references
- source:
  ```
  pattern P(v) = some(v)
  pattern Q(v) = some(v)
  f(P(x)) = "p"
  f(Q(x)) = "q"
  f(1)
  ```
- expected: stdout="\"p\"\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-key-named-matcher-same-dup`
- category `error` · gated by `default_open_functions` · requires `default_open_functions` · trace D3 same matcher reference duplicates
- source:
  ```
  pattern P(v) = some(v)
  f(P(x)) = 1
  f(P(y)) = 2
  ```
- expected: stdout="" stderr="Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:2, duplicate at <command>:3)\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: L: wording observed on the explicit-open twin; byte-lock at RED baseline
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)
- note: NEW id: splits the former key-named-matcher aggregate

##### `model-b-c-key-no-effects`
- category `error` · gated by `default_open_functions` · requires `default_open_functions` · trace D3 no effects at key time
- source:
  ```
  trace() = { print("effect"); true }
  f(x) ? trace() = { print("body"); 1 }
  f(y) ? trace() = { print("body2"); 2 }
  ```
- expected: stdout="" stderr="Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:2, duplicate at <command>:3)\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: L: wording observed on the explicit-open twin; byte-lock at RED baseline
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)
- note: stdout must stay empty: replaces the Ref log (one-shot eval stops at the first failure)

##### `model-b-c-key-r20-delta-true-one`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions, open_functions` · trace D3; approved R20 acceptance change
- source:
  ```
  open f(true) = 1
  f(1) = 2
  [f(true), f(1)]
  ```
- expected: stdout="[1, 2]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)\n" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred); informational, if executed: DIFFERS ("[1, 1]\n")

##### `model-b-c-key-r20-delta-one-float`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions, open_functions` · trace D3; approved R20 acceptance change
- source:
  ```
  open f(1) = 1
  f(1.0) = 2
  f(1.0)
  ```
- expected: stdout="1\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)\n" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred); informational, if executed: matches

##### `model-b-c-disp-p5-varargs-minima-ambiguity`
- category `error` · ungated RED tripwire (P5) · requires `(none)` · trace D1; RULES.md:205
- source:
  ```
  f(a, ..r) = "min1"
  f(a, b, ..s) = "min2"
  f(1, 2)
  ```
- expected: stdout="" stderr="Error: Ambiguous function resolution: f/2. Matching varargs: f/1+, f/2+\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="\"min2\"\n" stderr="" exit=0
- RED: fails (expected RED) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)
- note: ungated tripwire

##### `model-b-c-disp-p5-migration-fixed-clause`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace D1 migration fix
- source:
  ```
  f(a, ..r) = "min1"
  f(a, b, ..s) = "min2"
  f(a, b) = "exact2"
  f(1, 2)
  ```
- expected: stdout="\"exact2\"\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: Duplicate function definition: f/2\n" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-disp-p5-migration-drop-lower`
- category `eval` · ungated guard · requires `(none)` · trace D1 migration
- source:
  ```
  f(a, b, ..s) = "min2"
  f(1, 2)
  ```
- expected: stdout="\"min2\"\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="\"min2\"\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-disp-p7-same-arity-ambiguity`
- category `error` · ungated guard · requires `(none)` · trace D1 unchanged P7
- source:
  ```
  f(a, ..r) = "min1"
  f(a, b, ..s) = "min2"
  f(1, 2, 3)
  ```
- expected: stdout="" stderr="Error: Ambiguous function resolution: f/3. Matching varargs: f/1+, f/2+\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: Ambiguous function resolution: f/3. Matching varargs: f/1+, f/2+\n" exit=1
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-disp-fixed-over-varargs`
- category `eval` · ungated guard · requires `(none)` · trace RULES.md:204
- source:
  ```
  pick(a, b) = "exact"
  pick(a, ..rest) = "varargs"
  [pick(1, 2), pick(1, 2, 3)]
  ```
- expected: stdout="[\"exact\", \"varargs\"]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="[\"exact\", \"varargs\"]\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-disp-fixed-and-varargs-same-arity`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace D1 P4
- source:
  ```
  f(a) = 1
  f(a, ..r) = 2
  [f(1), f(1, 2)]
  ```
- expected: stdout="[1, 2]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: Duplicate function definition: f/1\n" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-disp-no-matching-function`
- category `error` · ungated guard · requires `(none)` · trace P8 unchanged
- source:
  ```
  f(a) = 1
  f(1, 2)
  ```
- expected: stdout="" stderr="Error: No matching function: f/2. Available: f/1\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: No matching function: f/2. Available: f/1\n" exit=1
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-disp-no-matching-function-new-group`
- category `error` · gated by `default_open_functions` · requires `default_open_functions` · trace D1/D3 renderer reuse
- source:
  ```
  f(x) = 1
  f(x, y) = 2
  f(x, ..r) = 3
  f()
  ```
- expected: stdout="" stderr="Error: No matching function: f/0. Available: f/1, f/2, f/1+\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: Duplicate function definition: f/1\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-disp-duplicate-pattern-header`
- category `error` · gated by `default_open_functions` · requires `default_open_functions` · trace D3
- source:
  ```
  f([a, b]) = 1
  f([c, d]) = 2
  ```
- expected: stdout="" stderr="Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: L: wording observed on the explicit-open twin; byte-lock at RED baseline
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-disp-case-miss-identity`
- category `error` · ungated guard · requires `(none)` · trace P20 unchanged
- source:
  ```
  f(x) = (0 -> x)
  f(1)
  ```
- expected: stdout="" stderr="Error: No matching case for function f/1 with arguments [1]\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: No matching case for function f/1 with arguments [1]\n" exit=1
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-disp-case-miss-pattern-group`
- category `error` · gated by `default_open_functions` · requires `default_open_functions` · trace D3 case-miss class
- source:
  ```
  f(0) = 1
  f(5)
  ```
- expected: stdout="" stderr="Error: No matching case for function f/1 with arguments [5]\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-disp-no-clause-ambiguity-single-unit`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace D3 single-unit first match
- source:
  ```
  f([x, ..r]) = "list"
  f(x) = "any"
  [f([1]), f(2)]
  ```
- expected: stdout="[\"list\", \"any\"]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-hdr-block-prefix-once`
- category `eval` · ungated guard · requires `(none)` · trace C1 P19
- source:
  ```
  f(x) { print("prefix"); k = x + 1; n ? n < k -> x | _ -> 0 }
  f(2)
  ```
- expected: stdout="prefix\n2\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="prefix\n2\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-hdr-block-prefix-miss`
- category `eval` · ungated guard · requires `(none)` · trace C1
- source:
  ```
  f(x) { print("prefix"); k = x + 1; n ? n < 0 -> x }
  f(2)
  ```
- expected: stdout="prefix\n" stderr="Error: No matching case for function f/1 with arguments [2]\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="prefix\n" stderr="Error: No matching case for function f/1 with arguments [2]\n" exit=1
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-hdr-block-prefix-multi-call`
- category `eval` · ungated guard · requires `(none)` · trace C1
- source:
  ```
  f(x) { print("prefix"); k = x + 1; n ? n < k -> x | _ -> 0 }
  [f(1), f(2)]
  ```
- expected: stdout="prefix\nprefix\n[1, 2]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="prefix\nprefix\n[1, 2]\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-hdr-grouped-body-captures-header`
- category `eval` · ungated guard · requires `(none)` · trace C1; contract 2.2 header captures
- source:
  ```
  f(x) = (0) -> x | (n) -> n + x
  [f(0), f(5)]
  ```
- expected: stdout="[0, 10]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="[0, 10]\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): **FAIL** ["", "Error: Undefined name: x\n", 1]

##### `model-b-c-hdr-guard-evaluated-once`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C1 once-only guard
- source:
  ```
  check(x) = { print("guard"); true }
  f(x) ? check(x) = x
  f(7)
  ```
- expected: stdout="guard\n7\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)
- note: print log replaces the Ref counter; no refs capability needed

##### `model-b-c-hdr-guard-order`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C1 source-order guards
- source:
  ```
  t(s, r) = { print(s); r }
  f(x) ? t("a", false) = 1
  f(x) ? t("b", true) = 2
  f(x) ? t("c", true) = 3
  f(0)
  ```
- expected: stdout="a\nb\n2\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-hdr-guard-error`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C1/C6 guard error propagates
- source:
  ```
  t(s, r) = { print(s); r }
  f(x) ? t("a", false) = 1
  f(x) ? undefined_guard(x) = 2
  f(x) ? t("c", true) = 3
  f(0)
  ```
- expected: stdout="a\n" stderr="Error: Undefined name: undefined_guard\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)
- note: stdout `a` then error; `c` never printed; one-shot so no partial-binding observation (host-local HL)

##### `model-b-c-hdr-matcher-outcome`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C1 matcher err is not a miss
- source:
  ```
  pattern M(v) = err("bad", v)
  f(M(x)) = 1
  f(y) = 2
  f(3)
  ```
- expected: stdout="err(\"bad\", 3)\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-hdr-recursion-tco`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C1; twin of r20-open-ordinary-mutual-tail-call
- source:
  ```
  count(0) = "done"
  count(n) = step(n - 1)
  step(n) = count(n)
  count(20000)
  ```
- expected: stdout="\"done\"\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-optim-collection-recursion`
- category `eval` · ungated guard · requires `(none)` · trace C2
- source:
  ```
  pick(n, xs) = (_, []) -> 0 | (0, [x, .._]) -> x | (n, [_, ..rest]) -> pick(n - 1, rest)
  pick(1, [5, 6])
  ```
- expected: stdout="6\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="6\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): **PASS**
- note: `nil` of the revision-5 plan source replaced by `0`: orthogonal to the optimizer, and C++ does not recognise `nil` (C++ ledger)

##### `model-b-c-optim-late-declaration`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C2/D8 optimized declaration then later pattern clause of another arity
- source:
  ```
  pick(n, xs) = (_, []) -> 0 | (0, [x, .._]) -> x | (n, [_, ..rest]) -> pick(n - 1, rest)
  pick(0) = "zero"
  [pick(1, [5, 6]), pick(0)]
  ```
- expected: stdout="[6, \"zero\"]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-opt-none-pattern-in-group-dispatches`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C-OPT; r20-option twin
- source:
  ```
  f(none) = "was-none"
  f(v) = v
  [f(none), f(3)]
  ```
- expected: stdout="[\"was-none\", 3]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-opt-other-arity-clause-not-aware`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C-OPT; r20-option twin
- source:
  ```
  f(0) = "zero"
  f(a, b) = (some(y), z) -> y
  f(x) = "ran"
  [f(none) == none]
  ```
- expected: stdout="[true]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-opt-delegation-to-aware-callee`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C-OPT; r20-option twin
- source:
  ```
  f(1) = "one"
  f(x) = unwrap_or(0, x)
  [f(none)]
  ```
- expected: stdout="[0]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-opt-err-pipeline-value-short-circuits`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace C-OPT; r20-option twin
- source:
  ```
  f(1) = "one"
  f(x) = x + 1
  [err("e") |> f]
  ```
- expected: stdout="[err(\"e\")]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: observed on explicit-open twin + contract
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-opt-plain-identity-none`
- category `eval` · ungated guard · requires `(none)` · trace P9
- source:
  ```
  f(x) = x
  f(none("r"))
  ```
- expected: stdout="none(\"r\")\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="none(\"r\")\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): **PASS**

##### `model-b-c-opt-pipe-lift`
- category `eval` · ungated guard · requires `(none)` · trace existing pipeline lift
- source:
  ```
  inc(x) = x + 1
  some(1) |> inc
  ```
- expected: stdout="some(2)\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="some(2)\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)
- note: oracle observed: `some(2)`

##### `model-b-c-own-alias-call-live`
- category `eval` · ungated guard · requires `(none)` · trace P1
- source:
  ```
  f(x) = x
  a = f
  f(x, y) = x + y
  a(1, 2)
  ```
- expected: stdout="3\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="3\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-own-immutable-alias-live`
- category `eval` · ungated guard · requires `immutable_bindings` · trace Slice B
- source:
  ```
  f(x) = x
  a =: f
  f(x, y) = x + y
  a(1, 2)
  ```
- expected: stdout="3\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="3\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (existing capability gate: immutable_bindings)

##### `model-b-c-own-local-alias-rejected`
- category `error` · new-capability-gated under Option C (recommended); ungated (keeping other requirements) under Option A · requires `default_open_functions` · trace D5 (P10)
- source:
  ```
  f(x) = x
  a = f
  a(x, y) = x + y
  ```
- expected: stdout="" stderr="Error: function-declaration-not-owner: cannot declare a/2: 'a' refers to function 'f' declared by another binding in this scope\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="<function a/2>\n" stderr="" exit=0
- RED: fails (expected RED) · oracle: PROPOSED text (pre-flight D3); not observable on the current runtime; maintainer approval required
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)
- note: ungated under O-1 Option A; gated under Option C (recommended)

##### `model-b-c-own-local-alias-pattern-clause`
- category `error` · gated by `default_open_functions` · requires `default_open_functions` · trace D5; pattern header is new syntax
- source:
  ```
  f(x) = x
  a = f
  a(0, y) = y
  ```
- expected: stdout="" stderr="Error: function-declaration-not-owner: cannot declare a/2: 'a' refers to function 'f' declared by another binding in this scope\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: PROPOSED text (pre-flight D3); not observable on the current runtime; maintainer approval required
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-own-local-alias-varargs`
- category `error` · new-capability-gated under Option C (recommended); ungated (keeping other requirements) under Option A · requires `default_open_functions` · trace D5; ownership check precedes the legacy duplicate check
- source:
  ```
  f(x) = x
  a = f
  a(x, ..r) = x
  ```
- expected: stdout="" stderr="Error: function-declaration-not-owner: cannot declare a/1+: 'a' refers to function 'f' declared by another binding in this scope\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: Duplicate function definition: a/1\n" exit=1
- RED: fails (expected RED) · oracle: PROPOSED text (pre-flight D3); not observable on the current runtime; maintainer approval required
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)
- note: ungated under O-1 Option A; gated under Option C

##### `model-b-c-own-alias-annotation-not-evaluated`
- category `error` · new-capability-gated under Option C (recommended); ungated (keeping other requirements) under Option A · requires `default_open_functions` · trace D5/C6 rejection precedes annotation evaluation
- source:
  ```
  f(x) = x
  a = f
  @doc (print("annotation-ran"))
  a(x, y) = x + y
  ```
- expected: stdout="" stderr="Error: function-declaration-not-owner: cannot declare a/2: 'a' refers to function 'f' declared by another binding in this scope\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="annotation-ran\n<function a/2>\n" stderr="" exit=0
- RED: fails (expected RED) · oracle: PROPOSED text (pre-flight D3); not observable on the current runtime; maintainer approval required
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)
- note: stdout must be empty; replaces the Ref log. ungated under Option A

##### `model-b-c-own-imported-alias-rejected`
- category `error` · new-capability-gated under Option C (recommended); ungated (keeping other requirements) under Option A · requires `default_open_functions, multi_file_eval` · trace D5 (P11)
- modules (entry `main.genia`):
  ```
  // lib.genia
  g(x) = x
  ```
  ```
  // main.genia
  import lib
  h = lib.g
  h(x, y) = x + y
  ```
- expected: stdout="" stderr="Error: function-declaration-not-owner: cannot declare h/2: 'h' refers to function 'g' owned by module 'lib'\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="<function h/2>\n" stderr="" exit=0
- RED: fails (expected RED) · oracle: PROPOSED text (pre-flight D3); not observable on the current runtime; maintainer approval required
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)
- note: ungated (keeping multi_file_eval) under Option A

##### `model-b-c-own-explicit-open-alias-unchanged`
- category `error` · ungated guard · requires `open_functions` · trace D5; R20 contract (view/interface named, not 'non-function')
- source:
  ```
  open f(x) = x
  a = f
  a(x, y) = x + y
  ```
- expected: stdout="" stderr="Error: Cannot define function a/2: name is bound to an open function interface or linked view, which an ordinary definition cannot replace\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: Cannot define function a/2: name is bound to an open function interface or linked view, which an ordinary definition cannot replace\n" exit=1
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)
- note: O-5 replacement of own-explicit-open-unchanged (same slot)

##### `model-b-c-own-import-inert`
- category `eval` · ungated guard · requires `multi_file_eval` · trace D5 import never alters dispatch
- modules (entry `main.genia`):
  ```
  // lib.genia
  g(x) = x
  ```
  ```
  // main.genia
  import lib
  g(x, y) = x + y
  [g(1, 2), lib.g(1)]
  ```
- expected: stdout="[3, 1]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="[3, 1]\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (existing capability gate: multi_file_eval)

##### `model-b-c-own-extend-ordinary-rejected`
- category `error` · ungated guard · requires `multi_file_eval, open_functions` · trace D5
- modules (entry `main.genia`):
  ```
  // base.genia
  f(x) = x
  ```
  ```
  // main.genia
  import base
  extend base.f(0) = 0
  ```
- expected: stdout="" stderr="Error: open-function-target-not-open: 'base.f' is not an open function interface\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: open-function-target-not-open: 'base.f' is not an open function interface\n" exit=1
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (existing capability gate: multi_file_eval)

##### `model-b-c-own-use-ordinary-base-unchanged`
- category `error` · ungated guard · requires `multi_file_eval, open_functions` · trace D5
- modules (entry `main.genia`):
  ```
  // base.genia
  f(x) = x
  ```
  ```
  // ext.genia
  import base
  value = 1
  ```
  ```
  // main.genia
  import base
  import ext
  use f from base with ext
  ```
- expected: stdout="" stderr="Error: open-function-target-not-open: 'base.f' is not an open function interface\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: open-function-target-not-open: 'base.f' is not an open function interface\n" exit=1
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (existing capability gate: multi_file_eval)

##### `model-b-c-own-two-modules-independent`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions, multi_file_eval` · trace D5 independent groups
- modules (entry `main.genia`):
  ```
  // m1.genia
  f(0) = "m1-zero"
  f(n) = "m1-other"
  ```
  ```
  // m2.genia
  f(0) = "m2-zero"
  f(n) = "m2-other"
  ```
  ```
  // main.genia
  import m1
  import m2
  [m1.f(0), m1.f(3), m2.f(0), m2.f(3)]
  ```
- expected: stdout="[\"m1-zero\", \"m1-other\", \"m2-zero\", \"m2-other\"]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-own-entry-prelude-name`
- category `eval` · ungated guard · requires `(none)` · trace D2/P12 characterization
- source:
  ```
  map(a, b, c) = "mine"
  [map(1, 2, 3), map((x) -> x + 1, [1, 2])]
  ```
- expected: stdout="[\"mine\", [2, 3]]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="[\"mine\", [2, 3]]\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)
- note: host-specific internals (write-through) are HL-5; this observable stays shared

##### `model-b-c-d8-forward-collision`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace D8
- source:
  ```
  describe(x) = (0) -> "zero" | (n) -> "other"
  describe(0) = "ZERO"
  [describe(0), describe(7)]
  ```
- expected: stdout="[\"zero\", \"other\"]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-d8-reverse-collision`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions` · trace D8
- source:
  ```
  f(0) = "clause"
  f(x) = (0) -> "arm" | (n) -> n
  [f(0), f(5)]
  ```
- expected: stdout="[\"clause\", 5]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-d8-terminal-grouped-miss`
- category `error` · gated by `default_open_functions` · requires `default_open_functions` · trace D8 terminal miss
- source:
  ```
  f(x) = (0 -> x)
  f(y) ? y > 5 = "later"
  f(9)
  ```
- expected: stdout="" stderr="Error: No matching case for function f/1 with arguments [9]\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-d8-earlier-pattern-miss-continues`
- category `error` · gated by `default_open_functions` · requires `default_open_functions` · trace D8 invariant 2
- source:
  ```
  f(0) = "zero"
  f(x) = (1) -> "one"
  f(5)
  ```
- expected: stdout="" stderr="Error: No matching case for function f/1 with arguments [5]\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-d8-grouped-decl-one-key`
- category `eval` · ungated guard · requires `(none)` · trace D8
- source:
  ```
  f(a) = (0) -> "z" | (n) -> n + a
  f(a, b) = a + b
  [f(0), f(3), f(1, 2)]
  ```
- expected: stdout="[\"z\", 6, 3]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="[\"z\", 6, 3]\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-d8-prefix-and-capture`
- category `eval` · ungated guard · requires `(none)` · trace D8/C1
- source:
  ```
  f(x) { print("prefix"); k = x + 1; n ? n < k -> x | _ -> 0 }
  g(a) = (0) -> a | (n) -> n + a
  [f(1), g(0), g(2)]
  ```
- expected: stdout="prefix\n[1, 0, 4]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="prefix\n[1, 0, 4]\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-d8-r20-flattening-unchanged`
- category `error` · ungated guard · requires `open_functions` · trace D8 explicit-open unchanged
- source:
  ```
  open f(x) = (0) -> 1 | (n) -> 2
  f(0) = 3
  ```
- expected: stdout="" stderr="Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)\n" exit=1
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)
- note: source chosen by the revision-6 author; the package gives only the outcome

##### `model-b-c-imm-rebind-as-function`
- category `error` · ungated guard · requires `immutable_bindings` · trace Slice B
- source:
  ```
  x =: 1
  x(a) = a
  ```
- expected: stdout="" stderr="Error: Cannot rebind immutable binding: x\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: Cannot rebind immutable binding: x\n" exit=1
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (existing capability gate: immutable_bindings)

##### `model-b-c-imm-rebind-as-pattern-function`
- category `error` · gated by `default_open_functions` · requires `default_open_functions, immutable_bindings` · trace Slice B x D3
- source:
  ```
  x =: 1
  x(0) = 1
  ```
- expected: stdout="" stderr="Error: Cannot rebind immutable binding: x\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-imm-declare-after-function`
- category `error` · ungated guard · requires `immutable_bindings` · trace Slice B
- source:
  ```
  f(a) = a
  f =: 1
  ```
- expected: stdout="" stderr="Error: Cannot declare immutable binding f: name is already bound in this scope\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: Cannot declare immutable binding f: name is already bound in this scope\n" exit=1
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (existing capability gate: immutable_bindings)

##### `model-b-c-meta-binding-doc-merge`
- category `eval` · ungated guard · requires `doc_help` · trace contract 5.1
- source:
  ```
  @doc "one"
  @category "c1"
  f(x) = x
  @doc "two"
  f(x, y) = x + y
  [doc("f"), meta("f")]
  ```
- expected: stdout="[\"two\", {doc: \"two\", category: \"c1\"}]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="[\"two\", {doc: \"two\", category: \"c1\"}]\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (existing capability gate: doc_help)

##### `model-b-c-meta-newer-key-overwrites`
- category `eval` · ungated guard · requires `doc_help` · trace contract 5.1
- source:
  ```
  @doc "one"
  f(x) = x
  @doc "two"
  f(x, y) = x + y
  doc("f")
  ```
- expected: stdout="\"two\"\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="\"two\"\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (existing capability gate: doc_help)

##### `model-b-c-meta-alias-no-copy`
- category `eval` · ungated guard · requires `doc_help` · trace contract 5.1
- source:
  ```
  @doc "one"
  f(x) = x
  a = f
  f(x, y) = x + y
  [doc("a"), meta("a")]
  ```
- expected: stdout="[none(\"missing-doc\", {name: \"a\"}), {}]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="[none(\"missing-doc\", {name: \"a\"}), {}]\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (existing capability gate: doc_help)

##### `model-b-c-meta-inline-doc-shared-via-alias`
- category `eval` · ungated guard · requires `doc_help` · trace contract 5.1 (inline doc syntax: `f(x) = "doc" body`)
- source:
  ```
  f(x) = "d1" x
  a = f
  f(x, y) = "d1" x + y
  [doc("f"), doc("a"), a(1, 2)]
  ```
- expected: stdout="[\"d1\", \"d1\", 3]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="[\"d1\", \"d1\", 3]\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (existing capability gate: doc_help)

##### `model-b-c-meta-conflicting-inline-doc-before-install`
- category `error` · ungated guard · requires `doc_help` · trace contract 5.1/5.2
- source:
  ```
  f(x) = "d1" x
  f(x, y) = "d2" x + y
  ```
- expected: stdout="" stderr="Error: Conflicting docstrings for function f: got 'd2', expected 'd1'\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: Conflicting docstrings for function f: got 'd2', expected 'd1'\n" exit=1
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (existing capability gate: doc_help)

##### `model-b-c-meta-three-channel-trio`
- category `eval` · ungated guard · requires `doc_help` · trace contract 5.1 reviewer trio
- source:
  ```
  @doc "canonical"
  f(x) = "inline" x
  @category "alias-category"
  a = f
  [doc("f"), doc("a"), meta("a")]
  ```
- expected: stdout="[\"canonical\", \"inline\", {category: \"alias-category\"}]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="[\"canonical\", \"inline\", {category: \"alias-category\"}]\n" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (existing capability gate: doc_help)

##### `model-b-c-meta-pattern-clause-annotations`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions, doc_help` · trace contract 5.1; observed legacy twin `@doc "zero"\nf(x) = 1`
- source:
  ```
  @doc "zero"
  f(0) = 1
  f(x) = x
  doc("f")
  ```
- expected: stdout="\"zero\"\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: contract-derived
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)
- note: open twin may reject annotations (R20 restriction): then the oracle is CD from the legacy-clause behaviour

##### `model-b-c-ann-later-annotation-suppressed`
- category `error` · ungated guard · requires `doc_help` · trace contract 5.2 / C6
- source:
  ```
  f(x) = x
  @doc 7
  @category (print("later"))
  f(x, y) = x
  ```
- expected: stdout="" stderr="Error: @doc annotation expected a string, received int\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: @doc annotation expected a string, received int\n" exit=1
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (existing capability gate: doc_help)

##### `model-b-c-ann-prior-effects-persist`
- category `eval` · ungated guard · requires `doc_help` · trace contract 5.2 / C6
- source:
  ```
  @since (print("first"))
  @doc 7
  f(x) = x
  ```
- expected: stdout="first\n" stderr="Error: @doc annotation expected a string, received int\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="first\n" stderr="Error: @doc annotation expected a string, received int\n" exit=1
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (existing capability gate: doc_help)

##### `model-b-c-ann-pattern-clause-variants`
- category `error` · gated by `default_open_functions` · requires `default_open_functions, doc_help` · trace contract 5.2 for pattern clauses
- source:
  ```
  f(x) = x
  @doc 7
  f(0) = 1
  ```
- expected: stdout="" stderr="Error: @doc annotation expected a string, received int\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: contract-derived
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-stage-closed-rejected`
- category `eval` · ungated guard · requires `(none)` · trace C8
- source:
  ```
  print("before")
  f(0) =: { print("child"); 0 }
  ```
- expected: stdout="before\n" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="before\n" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-mode-file-pattern-program`
- category `cli` · gated by `default_open_functions` · requires `default_open_functions` · trace C-MODE file mode
- CLI file mode, argv `[]`; source:
  ```
  f(0) = "zero"
  f(n) = "other"
  print([f(0), f(1)])
  ```
- expected: stdout="[\"zero\", \"other\"]" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)
- note: stdout for cli is trailing-newline stripped by the runner

##### `model-b-c-mode-command-pattern-program`
- category `cli` · gated by `default_open_functions` · requires `default_open_functions` · trace C-MODE -c mode
- CLI `-c` command mode, argv `[]`; source:
  ```
  f(0) = "zero"
  f(n) = "other"
  print([f(0), f(1)])
  ```
- expected: stdout="[\"zero\", \"other\"]" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-mode-import-pattern-program`
- category `eval` · gated by `default_open_functions` · requires `default_open_functions, multi_file_eval` · trace C-MODE import
- modules (entry `main.genia`):
  ```
  // lib.genia
  f(0) = "zero"
  f(n) = "other"
  ```
  ```
  // main.genia
  import lib
  [lib.f(0), lib.f(1)]
  ```
- expected: stdout="[\"zero\", \"other\"]\n" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available\n" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-main-legacy-main1-preferred`
- category `cli` · ungated guard · requires `(none)` · trace C-MAIN
- CLI file mode, argv `[]`; source:
  ```
  main(args) = { print("main1"); 11 }
  main() = { print("main0"); 10 }
  print("top")
  42
  ```
- expected: stdout="top\nmain1\n11" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="top\nmain1\n11" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-main-legacy-main0-fallback`
- category `cli` · ungated guard · requires `(none)` · trace C-MAIN
- CLI file mode, argv `[]`; source:
  ```
  main() = { print("main0"); 10 }
  print("top")
  42
  ```
- expected: stdout="top\nmain0\n10" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="top\nmain0\n10" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-main-legacy-rest-main-selected`
- category `cli` · ungated guard · requires `(none)` · trace C-MAIN
- CLI file mode, argv `[]`; source:
  ```
  main(a, ..r) = { print("mainrest"); 12 }
  print("top")
  42
  ```
- expected: stdout="top\nmainrest\n12" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="top\nmainrest\n12" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-main-no-qualifying`
- category `cli` · ungated guard · requires `(none)` · trace C-MAIN
- CLI file mode, argv `[]`; source:
  ```
  main(a, b) = { print("main2"); 12 }
  print("top")
  42
  ```
- expected: stdout="top\n42" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="top\n42" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-main-command-mode`
- category `cli` · ungated guard · requires `(none)` · trace C-MAIN
- CLI `-c` command mode, argv `["x", "y"]`; source:
  ```
  main(a) = { print("cmdmain"); a }
  print("top")
  ```
- expected: stdout="top\ncmdmain\n[\"x\", \"y\"]" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="top\ncmdmain\n[\"x\", \"y\"]" stderr="" exit=0
- RED: passes (guard; must stay green) · oracle: observed (Python baseline main@79c073b)
- C++ (pinned `44456ba`): UNSUPPORTED (adapter, as specified)

##### `model-b-c-main-pattern-not-selected`
- category `cli` · gated by `default_open_functions` · requires `default_open_functions` · trace C-MAIN
- CLI file mode, argv `["--x"]`; source:
  ```
  print("top")
  main(["--x"]) = { print("pattern-main"); 1 }
  42
  ```
- expected: stdout="top\n42" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="top" stderr="Error: model-b-not-implemented: declaration evaluation is not available" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-main-pattern-guard-not-evaluated`
- category `cli` · gated by `default_open_functions` · requires `default_open_functions` · trace C-MAIN
- CLI file mode, argv `["a"]`; source:
  ```
  ping() = { print("guard-ran"); true }
  main(args) ? ping() = { print("body"); 1 }
  print("top")
  42
  ```
- expected: stdout="top\n42" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-main-wildcard-not-selected`
- category `cli` · gated by `default_open_functions` · requires `default_open_functions` · trace C-MAIN
- CLI file mode, argv `[]`; source:
  ```
  main(_) = { print("wild"); 7 }
  print("top")
  42
  ```
- expected: stdout="top\n42" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-main-multi-pattern-group-not-selected`
- category `cli` · gated by `default_open_functions` · requires `default_open_functions` · trace C-MAIN
- CLI file mode, argv `["a"]`; source:
  ```
  main(["a"]) = { print("A"); 1 }
  main(["b"]) = { print("B"); 2 }
  print("top")
  42
  ```
- expected: stdout="top\n42" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-main-pattern-command-mode`
- category `cli` · gated by `default_open_functions` · requires `default_open_functions` · trace C-MAIN
- CLI `-c` command mode, argv `["x", "y"]`; source:
  ```
  main(["x", "y"]) = { print("body"); 1 }
  print("top")
  42
  ```
- expected: stdout="top\n42" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-main-explicit-call-dispatches`
- category `cli` · gated by `default_open_functions` · requires `default_open_functions` · trace C-MAIN
- CLI file mode, argv `["--x"]`; source:
  ```
  main(["--x"]) = { print("pattern-main"); 1 }
  print(main(["--x"]))
  42
  ```
- expected: stdout="pattern-main\n1\n42" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available" exit=1
- RED: fails (expected RED) · oracle: contract-derived (RED author confirms at baseline)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-main-explicit-call-miss`
- category `cli` · gated by `default_open_functions` · requires `default_open_functions` · trace C-MAIN
- CLI file mode, argv `[]`; source:
  ```
  main(["--x"]) = 1
  main(["--y"])
  ```
- expected: stdout="" stderr="Error: No matching case for function main/1 with arguments [[\"--y\"]]" exit=1
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available" exit=1
- RED: fails (expected RED) · oracle: L: wording observed on the explicit-open twin; byte-lock at RED baseline
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)

##### `model-b-c-main-test-mode-unchanged`
- category `cli` · gated by `default_open_functions` · requires `default_open_functions` · trace C-MAIN rule 6
- CLI `--test` file mode, argv `[]`; source:
  ```
  test("passes", () -> none)
  main(["x"]) = { print("main-ran"); 0 }
  ```
- expected: stdout="total=1 passed=1 failed=0 errored=0\nPASS passes\ntotal=1 passed=1 failed=0 errored=0" stderr="" exit=0
- baseline (observed, Python main@79c073b, gate bypassed): stdout="" stderr="Error: model-b-not-implemented: declaration evaluation is not available" exit=1
- RED: fails (expected RED) · oracle: observed on legacy-`main` twin (same program with an identifier header)
- C++ (pinned `44456ba`): UNSUPPORTED (capability `default_open_functions` undeclared by C++; inferred)
- note: oracle observed on the legacy-`main` twin (`main(args) = ...`) at RED baseline

### R6.E Host-local inventory (HL-1…HL-14 unchanged from the package §3.4; HL-15…HL-24 new)

Module docstrings must say they cover Python internals or Python-specific representation (AGENTS "Portable-behavior test placement"). Native Genia tests are an alternative where the behavior is Genia-facing but not yet portable.

| ID | Subject | Moved case ids / purpose | Why not a shared case | Shared observable twin |
| --- | --- | --- | --- | --- |
| HL-15 | persistent REPL environment: group grows across submissions; `f(0, 5)` → `5` | `open-persistent-env` | needs successive submissions; the REPL echoes host function representations (observed `<function f/1>` and `GeniaFunctionGroup(name='f', …)`), which no authority specifies (`<function` appears in no root document) | `open-noncontiguous-arities`, `open-pattern-after-plain` |
| HL-16 | Python `Env`: after the ownership rejection `f` and `a` are unchanged, `f(1, 2)` still has no arity-2 clause, and a later legitimate `f(x, y) = x + y` makes `a(1, 2)` = `3` | `own-local-alias-state-after-rejection`, `own-local-alias-owner-still-extendable` | observation after a failure | `own-local-alias-rejected` |
| HL-17 | Python module loader: after the foreign-alias rejection `lib.g(1, 2)` still reports no arity-2 clause and `lib.g(1)` → `1` | `own-imported-alias-owner-unchanged` | observation after a failure | `own-imported-alias-rejected` |
| HL-18 | Python `Env`: after a failed `@doc 7` the earlier metadata is retained, the new clause is installed and visible through an earlier alias | `ann-old-metadata-retained`, `ann-installed-clause-visible-via-alias` | observation after a failure | `ann-later-annotation-suppressed`, `ann-prior-effects-persist` |
| HL-19 | REPL recovery: a failed annotation or declaration leaves the session usable and the group unchanged except the installed clause. Framing: annotation and target in **one** submission (observed: `@doc 7; f(x, y) = x + y` raises `@doc annotation expected a string, received int` and installs `f/2`; a separate-line framing fails with a prefix-annotation error). `requires` n/a (host-local) | `ann-repl-recovery`, `mode-repl-failed-declaration-leaves-group` | REPL transcript echoes host values | one-shot error cases above |
| HL-20 | REPL submission of `main() = …` shows no `main` output; plus HL-9 structural | `main-repl-never-selects` | transcript is a host representation | none |
| HL-21 | legacy duplicate wording (`Duplicate function definition: f/1`, `describe/1`) after the refactor; existing `test_f2_p2_a_characterization.py` / `test_f2_p2_b_registration.py` stay unmodified | `key-legacy-dup-id`, `key-rest-binders-legacy-duplicate`, `d8-legacy-identical-header-dup` | wording appears in no root document or spec (R6-D3) | none |
| HL-22 | declaration over a lambda / builtin binding keeps `Cannot define function g/2: name already bound to non-function value` | `own-lambda-nonfunction-unchanged`, `own-builtin-nonfunction-unchanged` | wording unspecified (R6-D3) | none |
| HL-23 | migration companions (before/after) for every changed outcome of old syntax: P5, alias declaration, annotated alias declaration, imported-alias declaration, alias-varargs; the existing `test_function_resolution_precedence.py` expectations are updated at GREEN | O-1 rows 1–5 | records the documented break, independent of the applicability option | the shared RED cases |
| HL-24 | guard error: no partial binding and no later guard evaluated after `hdr-guard-error`'s failure | post-state of `hdr-guard-error` | observation after a failure | `hdr-guard-error` (stdout/stderr part) |

### R6.F Excluded, half-open and reserved items

- `key-repeated-binders-distinct` — excluded (O-4); no approved non-linear-pattern semantics.
- Active `unquote` half of the quote/unquote counterexample — no pinned guard-position program; only `key-quote-names-are-data` is included (R6-D9).
- `model-b-c-main-g1-*` — six reserved ids (package §R6.8); none is created before G1 approval.
- Stop conditions SC-MAIN-1…5 in C-MAIN remain stop conditions, not cases (six reserved ids are their GREEN-entry form).

### R6.G Traceability retained

C1 → `hdr-*`, `d8-prefix-and-capture`, `hdr-grouped-body-captures-header`; C2 → `optim-*`, HL-8; C3/C8 → package §R6.4–R6.5, `stage-closed-rejected`; C4 → `key-*`; C5 → `own-*`, HL-4, HL-10; C6 → `ann-*`, HL-3, HL-18, HL-24; C7 → `disp-p5-*`, HL-23. D1 → `disp-*`; D3 → `key-*`, `disp-duplicate-pattern-header`; D3b → HL-4 (route/HTTP/`@test`/lifecycle/introspection predicates asserted independently, never blanket rejection); D5 → `own-*`; D8 → `d8-*`, HL-8. Optimized output equality alone does not prove arm/provenance retention (HL-8 asserts retention).
