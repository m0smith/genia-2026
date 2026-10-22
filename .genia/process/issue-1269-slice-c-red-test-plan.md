# #1269 / #1250 — Model B Slice C RED test plan, host plan and documentation plan (revision 5)

**Revision 5 (documentation only):** the exact case IDs, oracle statuses, harness specification, R1 command/CI matrix, R3 GREEN gate, R4 diagnostic disposition, R5 manifest/documentation sequence and the recorded-not-approved G1 are in `issue-1269-slice-c-red-authorization-package.md`, which supersedes the inventory below wherever they differ; corrections are listed in its §8.4. C0 is merged (PR #1273).

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
