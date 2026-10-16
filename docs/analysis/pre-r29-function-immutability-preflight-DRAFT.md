# #1249 — Function openness and immutable binding: independent pre-flight draft

Status: **PROPOSED / ANALYSIS ONLY — NO GO DECISION, NO APPROVED SEMANTICS.** Prepared independently of ongoing #1229/#1230 scope work. `GENIA_STATE.md` is authoritative for implemented behavior. This file does not authorize tests, code or changes to language-reference documentation.

## 1. Placement and dependency

Unnumbered semantic foundation follow-up after completed R20/#1067 work and before new R29 language-facing implementation. Parent planning: #1249, with conditional downstream #1250 implementation and #1251 integration/audit. Roadmap plan is PR #1252 (not assumed merged).

Parallel lane: Claude is handling #1229 post-merge verification and #1230's module-scope compatibility fallback. **Do not touch** their working branches, environment/module-scope runtime code, module-scope compatibility contracts, closeout evidence or fallback-removal decisions in this lane. Capture dependencies; rebase only after those changes stabilize. #1230 remains a separate R29 hard gate.

## 2. Baseline: implemented, not proposed

- `name = expression` assigns in lexical scope, creating a current-scope binding if no reachable binding exists and otherwise updating the nearest existing lexical binding. Parameters are assignable.
- R20's `open f(pattern) = body` explicitly introduces an open interface; contiguous repeated `f(pattern) = body` clauses add local clauses. Cross-module contribution uses explicit `extend` and selected `use` semantics. R20's ordering, provenance, ambiguity, identity, and view rules must be preserved unless a separate explicit decision changes them.
- The R20/#1067 follow-up **rejected removal of explicit `open`** under its then-authorized scope, citing implicit cross-module extension risk under current export/module boundaries; its historical conclusions must not be rewritten.
- No `=:` operator or default-open function definition is implemented.

References: `GENIA_STATE.md` lexical assignment and §4.7; `GENIA_RULES.md` §8.5; `GENIA_REPL_README.md` lexical assignment; `README.md`; `docs/design/r20-open-functions-contract.md`; #1067; `docs/strategy/roadmap/sequence.md`.

## 3. User intent and candidate syntax

The user's design intent is **immutable name binding** for `=:`; a `@closed` annotation is explicitly unwanted. Candidate expressions (not executable behavior):

```genia
limit =: 3                    // immutable lexical binding
counter = 0                   // existing assignment behavior
counter = 1

describe(0) = "zero"         // proposed open-by-default definition
describe(n) = "number"

factorial(0) =: 1             // proposed closed-function clause run
factorial(n) =: n * factorial(n - 1)
```

Do **not** prematurely infer that an immutable name entails deep immutability of referenced objects. Distinguish immutable lexical binding from closed callable extension policy; the latter needs explicit definition-lifetime/grouping semantics.

## 4. Questions requiring contract decisions before GO

| Decision | Risk / required counterexample |
| --- | --- |
| Does `f(args) = ...` imply openness only for local clause runs, or cross-module extensibility? | Imported function must never become an unauthorized global extension target. |
| Which constructs count as function definitions rather than rebinding of an ordinary callable name? | `f = other`, `f(x) = body`, `f(x) =: body`, and first/repeated clauses cannot silently collide. |
| Is `name =: expr` a new binding only, or can it freeze an existing name? | Reassignment, duplicate same-scope binding, parameter mutation, closure capture, shadowing and builtins need deterministic outcomes. |
| What makes a contiguous group of `f(pattern) =: body` clauses one immutable closed definition? | Second clause must not fail as an attempted rebinding; intervening statements must have specified consequences. |
| What is exported and who can `extend`/`use` it? | Local/default openness must not grant importers mutation or unselected dispatch contributions. |
| Does source compatibility require migration/shims? | Ordinary function declarations, previously illegal patterns, explicit `open`, named values, and existing R20 modules all need inventories. |
| How is this represented and tested across hosts? | Avoid silent Core IR incompatibilities (R41 boundary); establish Python and C++ capability differences by evidence. |
| Which changes are prerequisites for R29? | Block only semantically affected R29 implementation; unrelated planning/docs-debt may proceed. |

## 5. Safety-first option comparison (decision pending)

**Option A — single-axis syntax (proposed intent):** `=` means open function clauses or mutable name assignment; `=:` means closed function clauses or immutable binding. Simplicity is attractive, but it conflates *reassignable lexical name*, *modifiable clause collection*, and *cross-module contribution authority*. A contract must disentangle them and show that it preserves the R20 authority boundary.

**Option B — default local open, explicit cross-module authorization:** ordinary `f(...) = ...` may accept additional local clauses; cross-module contribution requires a separate explicit declaration/permission even if local definitions are open by default. This best protects the extension boundary, but requires evaluating whether it meets the intended “open by default” ergonomics and whether extra declaration syntax is acceptable.

**Option C — retain current `open` for cross-module extensibility, add only `=:` immutable binding:** smaller compatibility surface, but does *not* satisfy the stated full open-by-default goal. Keep as fallback, not an assumed outcome.

No option is approved. Prefer minimal surface and explicit module authority; do not change existing dispatch ranking as a side effect.

## 6. Evidence / test matrix for contract phase (not test files yet)

- Lexical: top-level/local immutable creation; repeated declaration/reassignment failure; closure references; nested shadow; assignment through enclosing scopes; parameter reassignment behavior; builtins/root names.
- Function: ordinary single/multi-clause syntax; closed contiguous multi-clause grouping; post-group extension prohibition; mixed `=` / `=:` rejection; recursion/TCO; guards, wildcard and destructuring; diagnostics and introspection.
- Modules: declaration/export vs importing; `extend`/`use` selection; aliases/rebindings; modules' own local contributions; unselected external contributions; no implicit global registry; source and execution isolation.
- Portability: source AST/Core IR parse/lowering round trip where supported; external host protocol shared-spec cases; Python-C++ supported surface matrix; MCP language-profile truth and generated reference drift.

## 7. Interfaces with ongoing Claude work

**#1229:** currently owns evidence for separated module/entry runtime scopes. Contract design may describe logical lexical environments but may not prescribe a competing runtime scope implementation while #1229 is closing.

**#1230:** currently owns temporary module-to-entry read fallback and R29 removal/exception gate. Avoid sharing its files, branch or tests. Resolve function openness in the *intended* isolated module model; measure compatibility fallback interactions only after Claude's work is settled. No assumption that #1230 is closed or has passed.

**#1250:** blocked until #1249 has a recorded approved contract/GO decision; no early parser or evaluator writes.

**#1251:** blocked until semantics have actually landed; must synchronize `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, semantic registry/MCP profile and affected reference/tests with actual implementation only.

## 8. Provisional gate

**Decision: REVIEW / NOT YET GO.** The contract needs an explicit ruling on cross-module extension authority and lexical binding/rebinding interactions. Do not start #1250 yet.

## 9. Next bounded task

Produce a source-and-example-backed language contract decision matrix, with positive/negative cases, explicit exported-function policy, migration inventory, host/IR impact, and a concrete recommendation for user approval. After #1229/#1230 converge, refresh module boundary facts before final acceptance. Keep implementation truth docs current only when behavior is merged.
