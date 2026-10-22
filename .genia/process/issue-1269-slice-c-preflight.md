# #1269 / #1250 — Model B Slice C pre-flight, revision 5 (default-open ordinary functions and pattern/guard-headed functions)

**Status: PRE-FLIGHT ONLY. No RED, no GREEN, no production, test, spec, manifest or implemented-truth change accompanies this document.**
**Gate: NO-GO for RED remains in effect (revision 5 adds only the R1–R5 package; C0 has since merged via #1273).** Revision 4 is a documentation-only final-delta revision on top of revision 3 (`abd10bdb`). It applies Codex's independent verification (`6324998154`), the integration reconciliation (`6325204788`) and the Slice C coordination comment (`6326404613`). It is not a GO, does not self-certify any review, and does not authorize C0, RED, GREEN, manifest edits or merge.

| Item | Value |
| --- | --- |
| Tracking issue | [#1269](https://github.com/m0smith/genia-2026/issues/1269) (child of [#1250](https://github.com/m0smith/genia-2026/issues/1250)) |
| Base | `main` at `6d50a36d23cc4b894f0456ee502deb5d7796e99b` (Slice B merge) |
| Revision | 4 (starts from head `abd10bdb1aaf81147ae094063599020bb4dcd95a`, re-verified as the PR head before editing; `origin/main` still `6d50a36d23cc4b894f0456ee502deb5d7796e99b`, no intervening commits on the branch or on `main`). Revisions 1–3 are preserved in git history only. |
| Authority | Contract #1255 (maintainer-approved 2026-10-16); design #1259 incl. §13 and the final #1259 review pins; implemented truth = `GENIA_STATE.md` |
| Companion | `issue-1269-slice-c-red-test-plan.md` (revision 5); `issue-1269-slice-c-red-authorization-package.md` (R1–R5, G1 recorded) |
| Maintainer decisions recorded | **D1 approved** (PR #1270 comment 6321690337). **Numeric structural-key rule approved** (comment 6321761534). **D5, D3, D3b approved; D8 Option A approved as the desired approach, subject to Codex contract/design verification** (comment 6322649763). **C0: integration-owner design-only conditional sign-off** (comment 6322246286; code not authorized). **Codex independent verification: D8 Option A PASS as a contract interpretation, C0 PASS for design, pre-flight REVISE for bounded items** (comment 6324998154); **integration reconciliation: narrow REVISE** (6325204788); **`main` temporary compatibility boundary directed** (6326404613; architecture in [#1271](https://github.com/m0smith/genia-2026/issues/1271), not part of Slice C). Each approval is scoped to what it says (§2). |
| Roles | Implementer/pre-flight owner: Claude. Independent reviewer: Codex (exact-head final-delta review of revision 4 requested). Integration owner: m0smith. |

Evidence vocabulary: **observed** = I ran it on the Python host at the base SHA; **read** = from source/docs; **reviewer-observed** = reported by Codex in its review, not re-run by me; **to verify** = must be characterized in the RED baseline before being asserted.

## 0. Revision log

**Revision 5 — RED-preparation package, documentation only.** Accepted pre-flight (revision 4, `585f6aa`) is not reopened. Changes: C0 is **implemented, independently reviewed and merged** (PR #1273; `_VOCABULARY_ONLY_CAPABILITIES` is empty in production) — §9.1, §11 and §12 updated; stale facts corrected (RED plan header, the Slice B "874" count now measured **901**, the lambda-factory program, migration/new-group baselines); U7 is resolved by the R1 matrix; the RED-entry conditions R1–R5 and the recorded-not-approved G1 live in `issue-1269-slice-c-red-authorization-package.md`. `origin/main` is `79c073b` (adds only C0 and the #1271/#1272 lifecycle drafts, none touching Slice C). **Nothing here authorizes RED or GREEN.**

**Revision 4 (this file) — final pre-flight corrections, documentation only.** Authority re-check at the start of this revision: PR head is still `abd10bdb`; `origin/main` is still `6d50a36d`; `AGENTS.md` and the root authorities are unchanged on `main`. Changes:

| ID | Correction | Where |
| --- | --- | --- |
| **U2** | Pattern-bearing `main` is a **temporary compatibility boundary**, not a language design. The legacy selector is unchanged (`main/1` with `argv()`, else `main/0`, else the source result); no pattern-based discovery, no new diagnostic, no representative clause; pipe/REPL/test/serve untouched; explicit direct calls use ordinary Slice C dispatch. Mixed legacy/pattern declarations are characterized, and the cases whose expectation would need an unapproved choice are recorded as **stop conditions**. Host-selected lifecycle is #1271. | §2.5.1, §6.2 B11, §11 |
| **D8** | "Arm keys may be retained" replaced by a **MUST retain, or remain losslessly derivable from the unoptimized semantic structure** obligation. Local duplicate detection uses declaration-level keys for ordinary grouped bodies; explicit R20 `open` grouped-arm flattening is unchanged. Forward and reverse collisions, a terminal grouped miss and a legacy identical-header duplicate added. "Same-arity clauses install" qualified by declaration-key equality. D8 Option A is **verified as a contract interpretation** (Codex), so the `PENDING D8 VERIFICATION` labels are retired; the five invariants are mandatory. | §2.6, §5.3 |
| **C0** | Capability-evidence terminology: external-host runs report gated cases as `unsupported`; a pytest skip is a different event; unsupported is never passing evidence; the in-process runner path is named and does not apply the gate; the direct RED harness uses the same YAML and existing comparator without hiding failures; a contract SHA is not frozen across commits. C0 stays design-approved but **not implementation-authorized**. | §9.1 |
| **D3b** | Consumer facts re-stated from the independent verification: route and outbound HTTP annotations require fixed signatures with no rest parameter; `@test` and `main` have different arity behavior; lifecycle has no signature gate and ordinary callable groups remain callable; `help`/`doc`/`meta` remain usable for pattern groups. No blanket rejection merely because a callable has pattern clauses. | §2.5 |
| U-register | U1, U3, U6 resolved; U2 dispositioned (boundary + stop conditions). | §11 |

Nothing in D1, the numeric structural-key rule, D3, D5, D6, D7 or the D8 interpretation is reopened. C1–C8 implementation obligations and all original R20 conformance coverage are retained. Slice D (ordinary-base linking) and Slice E (closed publication) stay deferred.

**Revision 3:** D5 → §2.3 and §11; D3 → §2.4; D3b → §2.5 (and correction of §5.4); D8 → §2.6 (**pending Codex verification**); C0 re-stated as design-only (§9.1). Authority re-check: `origin/main` is still `6d50a36d23cc4b894f0456ee502deb5d7796e99b` (identical to the base), so none of `AGENTS.md`, `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, `docs/ai/LLM_CONTRACT.md`, `docs/process/run-change.md` or the contract/design has changed since they were read; the PR #1270 discussion (comments `6321690337`, `6321761534`, `6322246286`, `6322649763`, review `5603138617`) was re-read in full. Revision 2 corrections C1–C8 are retained unchanged.

**Revision 2 — findings C1–C8 and decisions**

| ID | Finding / decision | Disposition in this revision |
| --- | --- | --- |
| C1 | Header-frame adaptation must preserve ordinary block-prefix execution | §5.2, §6.1 P19, RED plan C-HDR |
| C2 | Optimizer rewrites ordinary `IrCase` to `IrListTraversalLoop` before declaration evaluation | §5.3, RED plan C-OPTIM |
| C3 | Manifest vocabulary auto-claims Python support; RED-time claim contradiction | §9.1 (staging mechanism **C0**), RED plan §1 |
| C4 | Local numeric key semantics needed in C; acknowledgement | §2.2 (approved), §6.3, RED plan C-KEY |
| C5 | Ownership/consumer inspection incl. fixed+rest same-minimum | §5.4, §11 D3b, RED plan C-OWN/C-CONSUMER |
| C6 | Publication/reentrancy atomicity without locking user code; no invented snapshot policy | §7 |
| C7 | D1 compatibility break pinned with error identity and migration | §2.1, §6.2, RED plan C-DISP |
| C8 | Old-spec requirements preserved; MCP wording; decisions before GO | §10, §12, RED plan §2/C-R20 |

---

## 1. Authoritative state

Read, in order: `AGENTS.md`, `GENIA_STATE.md` (§3, §4, §4.7), `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, `docs/process/run-change.md`, `docs/process/00-preflight.md`, `docs/process/extensions/portability-analysis.md`, `docs/ai/LLM_CONTRACT.md`, the contract, the design, merged Slice A/B code and specs, #1250/#1261/#1269, and PR #1270 review threads.

### 1.1 What `main` implements (read + observed)

- Slice A: `=:`, atomic closed groups and ordinary pattern/guard headers parse and lower to `IrImmutableBind`, `IrClosedFuncDef`, `IrPatternFuncDef` (`ir.py:304-331`, `lowering.py:246-250`, `parser.py:502`). Pattern headers reject `->` and grouped bodies; their post-`=` string is a body.
- Slice B: `IrImmutableBind` executes under an Env-owned policy; optional capability `immutable_bindings` (C++ listed gap → #1261 / genia-cpp#50).
- The Slice C stub is one line: `evaluator.py:1362-1367` raises `model-b-not-implemented: declaration evaluation is not available` for `IrPatternFuncDef` and `IrClosedFuncDef` (also route/server/CORS discovery guards).
- Ordinary functions already accumulate live and noncontiguously (observed P1). `GeniaFunctionGroup` (`callable.py:238`) is a `dict[arity → GeniaFunction]`; `add_clause` rejects a second clause with the same required arity.
- Explicit R20 `open` is a separate construction (`GeniaOpenFunction`, `OpenClauseRecord`, `_dispatch_open`, `_first_unit_match`).

### 1.2 Historical or superseded text — do not treat as current gates

| Source | Stale statement | Current truth |
| --- | --- | --- |
| Design §11 and header | "CONDITIONAL GO ONLY…" for Slice A tests | Slices A and B merged. |
| Design §2 | baseline `95213d1` | `main` is `6d50a36`. |
| Design §3.3 / §9 row C | "Reserve Core IR `0.2.0`; C must make the transition explicit" | **Superseded by §13.2** ("do not unilaterally require 0.2.0"); manifest stays `0.1.0`. Resolved, not an open decision (D6). |
| Design §9 row C | module-completion projections under C | Deferred to D (D7 accepted by integration and Codex). |
| Design §3.2 | optional `pattern`/`guard` on `IrFuncDef` | Superseded by §13.2 `IrPatternFuncDef`. |
| Contract header | "NOT IMPLEMENTED" | Partly stale (`=:` is implemented); STATE is authoritative. |
| #1261 body | "GO before RED", unchecked boxes | PR #1262 merged; not Slice C gates. |
| Revision 1 of this file | "CONDITIONAL GO", "GO then decisions" ordering | Superseded: **decisions precede GO** (§12). |

---

## 2. Maintainer decisions incorporated

### 2.1 D1 — unified Model B shape-stratum varargs dispatch (APPROVED 2026-10-21)

Scope of approval: D1 and its P5 consequence **only**. It does not approve diagnostics beyond what is pinned below, aliases, or anything in D/E, and it does not start RED.

**Acknowledged breaking change (P5).**
```genia
f(a, ..r) = "min1"
f(a, b, ..s) = "min2"
f(1, 2)
```
- Current Python ordinary dispatch (observed): `"min2"` (the exact-arity key holds a varargs clause and wins).
- Approved Slice C behavior: shape-stratum selection. No fixed clause of arity 2 exists; eligible varargs minima are `{1, 2}` (more than one distinct minimum) → **ambiguity error**. The largest minimum is never chosen. No hybrid or legacy fallback exists; the resolver does not depend on whether a group contains pattern clauses.
- **Error identity (selected, contract-consistent):** ordinary groups keep the existing legacy ordinary identity for this failure class — `TypeError: Ambiguous function resolution: f/2. Matching varargs: f/1+, f/2+` (the text P7 already produces for the non-exact-arity case; design §13.4 "preserve legacy ordinary error identities for … ambiguous … failures"). Explicit `open` keeps `open-function-varargs-ambiguity`. The two spellings are therefore intentionally different by construction path, as they are today.
- **Migration note (to appear in STATE/RULES/README at GREEN):** a group with two or more varargs clauses of different minimum arity that is called at an arity equal to the larger minimum used to select the larger-minimum clause and now raises. Fix: remove the lower-minimum clause, or add an exact fixed clause of that arity. Corpus evidence (limited): 0 such groups among 1,252 groups in 183 repo `.genia` files; inline Genia in Python test sources is **to verify**. Zero occurrences is evidence of low impact, not of approval (C7).
- **Executable oracle:** RED case `model-b-c-disp-p5-varargs-minima-ambiguity` (error spec) plus the migration-contrast cases in the companion plan. It is a RED/new-behavior case, **not** a regression guard that must pass today.
- Unchanged by D1: exact fixed arity beats varargs (`pick(a,b)` vs `pick(a,..rest)`, existing `test_function_resolution_precedence.py`), P7 same-arity-3 ambiguity, P8 no-matching-function text.

### 2.2 Numeric structural-key rule (APPROVED 2026-10-21)

Approved rule (verbatim intent): **Boolean, integer and floating keys carry separate tags; floating spellings that lower to the same binary64 value are duplicate keys.** The approval includes the compatibility consequences, among them a historical explicit-R20 key-acceptance change. It satisfies the maintainer-acknowledgement condition retained by the final #1259 review (design §13.4).

| Pair (as two local clauses) | Key relation | Observed today (explicit `open`, host-equality keys) | Slice C behavior |
| --- | --- | --- | --- |
| `true` vs `1` | distinct | duplicate-clause rejected (P13) | both install |
| `1` vs `1.0` | distinct (integer tag ≠ float tag) | duplicate-clause rejected (P13) | both install |
| `0.1` vs `0.10` | same key | duplicate (observed) | duplicate (unchanged outcome, now by typed binary64 key) |
| `1.0` vs `1.00000000000000001` | same key (identical binary64 after lowering) | duplicate (observed) | duplicate |
| `1` vs `2` | distinct | installs | installs |

- Keys are **syntactic**: key equality is not runtime matching equality. Observed: a literal `1` pattern *matches* the value `1.0` at runtime (`((1) -> "int-clause" | _ -> "other")` over `[1, 1.0, true]` → `int-clause, int-clause, other`). So with clauses `f(1)=10; f(1.0)=20`, both install; `f(1.0)` dispatches by first-match order (expected `10`, because clause 1's literal matches), `f(true)` does not match either numeric clause. Dispatch is first-match, never specificity. The expected dispatch results are re-confirmed in the RED baseline (C4 requires installation **and dispatch** observations).
- **Compatibility consequence (explicit):** shared key helper replaces `_open_dispatch_key`/`_structural_key` (`callable.py:646-700`), so explicit-R20 `open f(true)=…; f(1)=…` and `open f(1)=…; f(1.0)=…` change from rejection to acceptance. Same-binary64 spellings remain duplicates. Existing `r20-*` shared specs and `tests/unit/test_r20_open_functions_*` do not contain these pairs as expectations (**to verify** in the RED baseline); if any does, it is reported, not edited.
- Key encoding rules (design §5.4): explicit type tags; no `repr`, host class names or flat binder dictionary; binder depth/slot normalization; free names and named-matcher references stay syntactic; quote/unquote at appropriate depth; rest binders participate; deterministic rejection of malformed structure.

### 2.3 D5 — declaration ownership (APPROVED 2026-10-21, comment 6322649763)

**Rule.** Only the binding that owns a function group may append clauses to it. A same-scope alias and an imported/foreign alias can **call** the live function but cannot **declare** into it. Callable identity is unchanged (aliases stay equal and live); an immutable alias (`a =: f`) does not freeze the mutable group (`f` keeps accumulating; `a` observes it). Ownership is the group's recorded provenance `(canonical module identity, defining name)` compared with the declaring scope's module identity and the declared name; it is not inferred from `callable(value)`.

**Scope of the rule.** It applies when the declared name is currently bound to an *ordinary function group* whose provenance differs from the declaration's own `(module identity, name)`. Unchanged and not covered: names bound to lambdas, builtins/host callables or other values (existing `Cannot define function N/A: name already bound to non-function value`, P18), explicit `open` interfaces/views (`Cannot define function … open function interface or linked view`), immutable bindings (Slice B messages), and runtime-owned entry write-through (D2).

**One stable proposed category, `function-declaration-not-owner`**, with two safe, deterministic messages. Proposed class `FunctionDeclarationNotOwnerError(TypeError)` placed beside the `OpenFunctionError` family in `callable.py`, so it follows the existing infrastructure: `TypeError` subclass, message prefix = normalized category, error-spec `notes: error_phase: eval`, `error_category: FunctionDeclarationNotOwnerError`. The shape suffix is `N` for a fixed shape and `N+` for a varargs shape.

| Case | Source | Exact output (stdout empty before the failing statement; exit 1) |
| --- | --- | --- |
| Local alias | `f(x) = x`<br>`a = f`<br>`a(x, y) = x + y` | `Error: function-declaration-not-owner: cannot declare a/2: 'a' refers to function 'f' declared by another binding in this scope` |
| Imported alias | module `lib`: `g(x) = x`; entry: `import lib`<br>`h = lib.g`<br>`h(x, y) = x + y` | `Error: function-declaration-not-owner: cannot declare h/2: 'h' refers to function 'g' owned by module 'lib'` |
| Pattern clause through alias | `a(0, y) = y` (pattern header, same alias) | `Error: function-declaration-not-owner: cannot declare a/2: 'a' refers to function 'f' declared by another binding in this scope` |
| Varargs shape | `a(x, ..r) = x` | `… cannot declare a/1+: …` |

Messages contain only the declared name/shape, the owner's defining name and the canonical module identity (the cached module name, never a filesystem path); no source spans, addresses, captured values or protected values. Literal text is a **proposal pinned for the RED oracle**; it is locked only after the RED baseline characterizes the surrounding infrastructure (`Env.define_function` message conventions) and Codex confirms it.

**State after rejection (all observable, all RED assertions).** Nothing is installed; the owner group keeps exactly its prior clauses (`f(1)` → `1`, `a(1)` → `1`, `f(1, 2)` → `No matching function: f/2. Available: f/1`); the alias binding is unchanged; annotation expressions attached to the rejected declaration are **not evaluated** (rejection precedes annotations); binding metadata of `f` and `a` is unchanged; a later *legitimate* declaration `f(x, y) = x + y` still succeeds and `a(1, 2)` then returns `3`; for the imported case `lib.g(1, 2)` still fails with the arity-miss text and the importer's other bindings are unchanged. The rejection is a statement-level error: statements already executed keep their effects.

**Migration (valid → error, approved):** P10 (`a(x,y)=…` through a same-scope alias) and P11 (cross-module append through an alias) no longer succeed. Migration note for the docs at GREEN: declare through the owning name (`f(x, y) = …`); to change another module's function use explicit R20 `open`/`extend`/`use` or edit the owning module. P11 was an implicit cross-module modification, which #1250 forbids.

### 2.4 D3 — diagnostics (APPROVED 2026-10-21): preserve legacy, normalized duplicate for new pattern cases

Principle: **legacy ordinary class, category and byte-identical text are preserved** wherever a legacy program already produced the failure; the normalized `open-function-duplicate-clause` diagnostic is used only for **new** pattern-header duplicate cases; no new legacy-style error is invented for implementation convenience. Literal strings below are RED oracles proposed from the observed baseline and existing infrastructure; the maintainer directed that they be **pinned against the observed baseline during RED**, so each is re-characterized (byte-for-byte) before being locked.

| Failure | Class / category | Exact output | Basis |
| --- | --- | --- | --- |
| **Duplicate declaration, legacy-only** (same required arity, both plain identifier headers; P3) | `TypeError`, `Duplicate function definition` | `Error: Duplicate function definition: f/1` | preserved (observed) |
| **Duplicate declaration involving a pattern/guard clause** (new surface) | `OpenFunctionDuplicateClauseError(TypeError)`, `open-function-duplicate-clause` | `Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)` | existing class and renderer `_format_open_span`; unit label `base` = the group's single unit; imported-module clauses render `module-identity:line`, entry clauses keep the entry source label as given (existing R20 behavior; no host path resolution) |
| **Argument-count / shape mismatch** (no clause of an eligible shape; P8) | `TypeError`, `No matching function` | legacy-only group: `Error: No matching function: f/2. Available: f/1` (byte-identical). Group containing a pattern record or a fixed+rest pair: same prefix with the existing R20 renderer: distinct shapes sorted, fixed shapes first, `+` for varargs. Pinned example: `f(x)=1; f(x,y)=2; f(x,..r)=3; f()` → `Error: No matching function: f/0. Available: f/1, f/2, f/1+` | legacy preserved; new-group listing reuses `OpenFunctionNoMatchingFunctionError` formatting |
| **Valid shape, no matching pattern** (P20) | `RuntimeError`, `No matching case` | `Error: No matching case for function f/1 with arguments [5]` | preserved class and text for ordinary groups **including pattern groups** (not the R20 `TypeError` subclass); arguments via `format_debug` (protected values masked) |
| **Varargs ambiguity** (P5, P7) | `TypeError`, `Ambiguous function resolution` | `Error: Ambiguous function resolution: f/2. Matching varargs: f/1+, f/2+` | preserved legacy identity for ordinary groups (D1); explicit `open` keeps `open-function-varargs-ambiguity` |
| **Invalid declaration ownership** | `FunctionDeclarationNotOwnerError(TypeError)`, `function-declaration-not-owner` | §2.3 | new, D5 |

Note on the shape-mismatch listing for new groups: the legacy-only format (`f/N` per required arity, no `+`) cannot describe a group with several records per arity, so groups containing a pattern record or a fixed+rest pair use the existing `OpenFunctionNoMatchingFunctionError` rendering (`callable.py:580-598`, read: `sorted(available)` over `(kind, n)` tuples, `+` for varargs). The pinned example above is derived from that code and is re-characterized byte-for-byte in the RED baseline before being locked.

Other observable identities unchanged: immutable-binding messages (Slice B), `open-function-redeclaration`, `open-function-target-not-open`, `open-function-header-capture`.

### 2.5 D3b — special consumers (APPROVED 2026-10-21): conservative boundary

Rule: **legacy-only groups behave exactly as today.** A group that contains any pattern-headed record, or a fixed+rest pair at the same required minimum (constructible only after Slice C, previously a duplicate error), is **not admissible** to a consumer **whose existing signature contract requires exactly one fixed handler record** (`@route`, outbound HTTP annotations, `@test`) and cannot establish that from an arity set. The consumer never picks a representative record. Existing rejection mechanisms and texts are used; no new consumer message is introduced. A more flexible acceptance policy would be a separate design.

**Independently verified consumer facts (Codex `6324998154`; preserved here and not to be flattened into one rule):**
- `@route` handlers and outbound HTTP annotations require **fixed signatures with no rest parameter** (`rest_param is None`).
- `@test` and `main` have **different established arity behavior** from the route/HTTP pair: neither checks for a rest parameter today (`@test` requires `get(0)` with arity set `[0]`; `main` tries `get(1)` then `get(0)` and never diagnoses a mismatch). Their legacy behavior is preserved as is.
- **Lifecycle binding has no new signature gate.** Ordinary callable groups remain callable.
- **`help`, `doc` and `meta` remain usable** for the new pattern groups.
- **No blanket rejection.** Pattern clauses are never rejected merely because they are pattern clauses. Rejection applies only where an existing exact-single-record signature contract is the consumer's established predicate.

| Consumer (source) | Existing predicate (read) | Existing mismatch output | Slice C rule for pattern-bearing or fixed+rest-mixed groups |
| --- | --- | --- | --- |
| `@route` handler (`server_route_binding.py:261`) | `sorted_arities() == [1]`, `get(1)` is a `GeniaFunction`, `rest_param is None` | discovery diagnostic `@route handler must expose exactly one fixed one-argument function arm` | same diagnostic; admissible only if the group is exactly one legacy fixed arity-1 record |
| HTTP annotation (`http_annotation_binding.py:55-78`) | `sorted_arities() == [0]`, `get(0)` fixed (no rest) | `TypeError: send_annotated expected a fixed zero-argument function` | same error; admissible only if exactly one legacy fixed arity-0 record |
| `@test` (`test_cli.py:189-200`) | `get(0)` exists and `sorted_arities() == [0]` (**does not** check `rest_param`) | discovery unit `@test functions must take zero arguments` | same unit text; legacy-only behavior (including today's no-rest-check) unchanged; a group with a pattern record or a fixed+rest pair is rejected rather than choosing `get(0)` |
| `main` (`interpreter.py:513-529`, `_resolve_program_result`) | `main_group.get(1)` then `get(0)` by arity key (a legacy rest-parameter `main(a, ..r)` is stored at key 1 and **is** selected today — observed §2.5.1); absence returns the program result silently (**no mismatch diagnostic exists**) | none | **Temporary compatibility boundary — see §2.5.1.** Legacy-only groups: unchanged. Pattern-bearing `main` is not auto-selected by the legacy selector; no new diagnostic; no representative clause. |
| Lifecycle participants (`lifecycle_binding.py:199`) | accepts any `GeniaFunctionGroup`/`GeniaFunction`/callable; **no signature gate** | none | **Resolved (was U3).** No new binding-time signature rejection. Ordinary callable groups, including groups with pattern records, remain callable and use ordinary Slice C dispatch at invocation with the lifecycle's own argument count. Nothing to reject because the existing contract has no signature to violate. |
| `help` / `doc` / `meta` | introspection, not invocation | — | **continue to work for pattern groups.** Legacy-only rendering byte-identical. New groups: deterministic declaration-order listing of records (shape, optional guard presence, declaration order), no host objects, no source spans beyond what legacy `help` already shows, no captured values. |

**Correction to revision 2 (§5.4):** revision 2 asserted a "varargs-accepting `[1]` rule" for these consumers. That was wrong for `@route` and HTTP annotations (both require `rest_param is None`); only `@test` and `main` accept a rest parameter today. The corrected table above is authoritative. The fixed+rest same-minimum group `f(x)=…; f(x,..r)=…` reports `sorted_arities() == [1]` and would pass the *arity* check, which is exactly why record-cardinality checks are required.

### 2.5.1 U2 — `main` entry selection: temporary Slice C compatibility boundary (DIRECTED 2026-10-21, comment 6326404613)

**This is a temporary compatibility boundary, not the long-term language design.** The long-term direction is [#1271](https://github.com/m0smith/genia-2026/issues/1271): the host-selected Genia Application Lifecycle will invoke an ordinary Genia `main` as the default lifecycle's conventional work entry (not special parser syntax; no new source-visible API in its initial design; it must preserve file/command `main/1` > `main/0` > source-result fallback, explicit serve/pipe/test modes, inert imports, Outcome distinctions and R14 cleanup rules). #1271 needs its own contract and design gates, is **not** part of Slice C, is **not** implemented, and does **not** block Slice C. Nothing below approves or pre-empts it.

**Observed baseline of the legacy selector (Python @ `6d50a36`, scripted file/`-c` runs; `argv` as given).** `_resolve_program_result` (`interpreter.py:513`) is called only from the `command` (`-c`) and `file` branches (`interpreter.py:671`, `:687`; read). It looks up `main` in the entry scope and, if it is a `GeniaFunctionGroup`, tries `group.get(1)` then `group.get(0)` by arity key, else returns the program result.

| # | Program (file mode unless noted) | Output (stdout) | Reading |
| --- | --- | --- | --- |
| M1 | `main(args) = { print("main1"); 11 }`; `main() = { print("main0"); 10 }`; `print("top")`; `42` | `top` / `main1` / `11` | `main/1` is preferred; `main/0` is not run; the `main` result replaces `42` |
| M2 | `main()` only | `top` / `main0` / `10` | `main/0` fallback |
| M3 | `main(a, ..r) = { print("mainrest"); 12 }` | `top` / `mainrest` / `12` | a **legacy rest-parameter** `main` stored at key 1 **is** selected today; "exact `main/1`" in legacy terms is *the record stored at arity key 1* |
| M4 | `main(a, b) = …`; `print("top")`; `42` | `top` / `42` | no `main/1` or `main/0` → source result retained, no diagnostic |
| M5 | `-c 'main(a) = { print("cmdmain"); a }\nprint("top")' x y` | `top` / `cmdmain` / `["x", "y"]` | command mode uses the same selector, with trailing args as `argv()` |
| M6 | REPL submission `main() = { print("ran"); 1 }` | `<function main/0>` (no `ran`) | the REPL never calls the selector |
| M7 | `main(_) = { print("wild"); 7 }` | `Error: model-b-not-implemented: declaration evaluation is not available` | a wildcard header is **pattern-headed** (not a legacy identifier header) |
| existing | `spec/cli/file_mode_main_argv`, `spec/cli/pipe_mode_bypass_main` | per their YAML | pipe mode bypasses `main` dispatch |

**Boundary rules.**
1. **Selection convention unchanged.** File/command mode selects `main/1` (called with `argv()`), otherwise `main/0`, otherwise retains the source result. M1–M5 stay byte-identical, including M3 (legacy rest-parameter `main` keeps being selected).
2. **No pattern-based entry-point discovery in Slice C.** The selector does not match `argv()` against patterns, does not evaluate guards to choose an entry, and does not try clause records in turn.
3. **A pattern-bearing `main` is not automatically selected by the current legacy selector.** "Pattern-bearing" includes wildcard-headed clauses (M7).
4. **No new special diagnostic.** Non-selection is silent, like M4; no `main-*` error category is introduced.
5. **No representative clause.** The selector never picks one record of a multi-record group to stand in for the group.
6. **Pipe, REPL, test and serve activation are unchanged** (pipe bypass, M6, native `@test` discovery, `serve`).
7. **Explicit direct calls use ordinary Slice C dispatch.** A program that calls `main(["--x"])` itself dispatches through the pattern group exactly like any other function (shape stratum, first match, case-miss identity). Calling it explicitly neither selects nor suppresses the entry convention.
8. **Mixed declarations** are characterized in the table below. Only the pure cases are determinable without a new choice; the others are **stop conditions**.

**Group classes and dispositions.**

| Class | Shape of the `main` group | Disposition |
| --- | --- | --- |
| **L** legacy-only | every record a legacy identifier-header record (including rest-parameter records) | **unchanged** (rule 1); guard cases, ungated, original applicability |
| **P** pure pattern | every record pattern-headed (e.g. `main(["--x"])`, `main(x) ? x == [] = …`, `main(_)`) | **not selected**; source result returned; no clause body, guard or matcher of the group executes at entry; nothing printed by the group; exit status as for the source result (determinable; R-gated, §2 C-MAIN in the plan) |
| **X** explicit call | any group, called explicitly by program text | ordinary dispatch (rule 7) |
| **M** mixed | at least one legacy record and at least one pattern record, or a fixed+rest pair at the same required minimum | see stop conditions |

**Stop conditions (SC-MAIN) — no expectation is manufactured.** The cases below are *constructible only after Slice C* (before it, such groups are `model-b-not-implemented` or a duplicate-definition error), so no legacy behavior exists to preserve. Their behavior depends on a choice no approval makes:

| ID | Mixed shape | Divergent readings (none approved) | Why this is a stop |
| --- | --- | --- | --- |
| SC-MAIN-1 | legacy `main()` + pattern record(s) of any other arity | (S) per-arity-key: `main/0` still runs; (G) whole-group: nothing is selected | rule 3 says "pattern-bearing `main`"; whether one pattern record disables an otherwise legacy `main/0` is not stated |
| SC-MAIN-2 | legacy `main/1` + pattern record(s) of another arity | (S) `main/1` selected with `argv()`, pattern record not executed; (G) not selected | same |
| SC-MAIN-3 | legacy `main/1` and a pattern `main` record of arity 1 (either order) | (G) not selected; (S-direct) call the legacy record, skipping a pattern record declared earlier; (S-dispatch) dispatch by declaration order | selecting the legacy record directly would silently bypass first-match order; dispatching is the pattern-based entry that rule 2 excludes |
| SC-MAIN-4 | fixed+rest same minimum (`main(a)`; `main(a, ..r)`) | any choice picks a representative record | rule 5 |
| SC-MAIN-5 | legacy rest `main(a, ..r)` + pattern arity-1 record | as SC-MAIN-3 | same |

Resolution, if ever needed, belongs to a maintainer decision or to #1271's contract and design (host-selected lifecycle), **not** to Slice C. The recorded reading (G) is the one consistent with the D3b table in revision 3 ("pattern-bearing or fixed+rest-mixed group … not selected") and (S) is the one consistent with the literal phrase "exact-arity selector"; both are recorded so the conflict is visible, and **neither is chosen here**. RED must not contain an expectation for SC-MAIN-1…5; if the integration owner wants them covered before GREEN, they need an explicit disposition first. They must not be represented by a vacuous or "any outcome" case.

**Documentation obligation at GREEN.** `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md` and `README.md` must carry a caveat that file/command entry selection only considers legacy-style `main` and that pattern-bearing `main` is not auto-selected, and must say the convention is the current temporary behavior pending the application lifecycle (#1271). The MCP language profile text must not imply that a pattern-bearing `main` is an entry point.

### 2.6 D8 — grouped-body clause identity (Option A APPROVED; **VERIFIED as a contract interpretation by Codex, `6324998154`**, subject to the mandatory invariants below)

Maintainer condition (comment 6322649763) was Codex confirmation of consistency with the approved contract/design. Codex returned **PASS as a contract interpretation** and the integration owner agreed (`6325204788`): no Model B contract amendment is required. The conflict reading of design §3.2 is therefore withdrawn. Do not claim that design §13 explicitly settled the local-versus-cross-unit boundary: **neither §3.2 nor §13 specifies it**; Option A supplies it, consistently with contract §2.2/§2.3 and design §§3.2/5.2.

**Rule.**
- A legacy identifier-header declaration (`f(a, b) = <expr | block | grouped case>`) contributes **one declaration-level structural key**: `(shape, all-bind header pattern, no guard)`. **Local duplicate detection uses declaration-level keys for ordinary grouped-body declarations.**
- **Mandatory retention (corrects revision 3's "arm keys may be retained").** The original grouped-body arm keys, ordinals and the necessary provenance (header/body pairing, declaration ordinal, arm ordinal) **MUST be retained, or must remain losslessly derivable from the unoptimized semantic structure**, to satisfy design §§3.2/5.2. They are not exposed and Slice C's local duplicate check does not consult them; they exist for Slice D's cross-unit validation. Deriving them only *after* optimization is insufficient (§5.3).
- **Explicit R20 `open` grouped-arm flattening is unchanged.** Contract §§3.1/3.3 and STATE §4.7 require explicit-open grouped arms to flatten, so `open f(x)=(0)->1 | (n)->2; f(0)=3` still rejects the duplicate zero arm (reviewer-observed). Applying Option A to `open` would violate that contract; Option A is ordinary-declaration behavior only.
- Unchanged: first-match order; header capture and header-frame visibility; block-prefix effects (once per call); a selected grouped body's **case miss never falls through** to a later ordinary declaration; optimized/unoptimized equivalence; declaration order.

**Mandatory invariants (Codex).**
1. One local declaration record/key for a legacy identifier header. No user matcher, guard, prefix or body executes while computing keys. Internal arm order, keys and provenance are preserved separately.
2. Shape selection precedes declaration selection. A selected grouped body's miss is terminal for that invocation (no later ordinary clause, no varargs rescue). An *earlier pattern-header* miss may continue to the next declaration.
3. Build the positional header frame once. Execute a block prefix once before final-case matching and retain that prepared environment as the parent of arm locals. Arm bindings shadow headers. Matchers and guards run once per attempted match; only the selected result executes. Already-executed effects are preserved on failure.
4. Capture semantic information **before** optimization, retain a lossless original representation, or decline the rewrite. `optimize_nth_style_recursion` (`optimizer.py:75`) replaces `IrCase` with `IrListTraversalLoop`, retaining the empty/zero arms but not the recursive arm (reviewer-observed). No new portable IR field is necessary.
5. Source, unoptimized Core and optimized execution must agree on values, errors, effects, ordering and duplicate decisions, including a later declaration after an optimized one.

**Oracles (expected outputs are recommendations from the verified interpretation; none was executed as Slice C evidence, because the baseline rejects pattern-header declarations with `model-b-not-implemented`).**

| Case | Source | Expected |
| --- | --- | --- |
| Forward collision | `describe(x) = (0) -> "zero" \| (n) -> "other"`<br>`describe(0) = "ZERO"`<br>`[describe(0), describe(7)]` | both declarations install, **no arm-duplicate error**; `["zero", "other"]`. Keys: all-bind header vs literal-zero header (distinct). The earlier header wins; its body selects an arm; the later `describe(0)` is unreachable (B8) |
| Reverse collision | `f(0) = "clause"`<br>`f(x) = (0) -> "arm" \| (n) -> n`<br>`[f(0), f(5)]` | installs; `["clause", 5]`. Local arm-key checking would wrongly reject; declaration keys differ and first-match order is preserved |
| Terminal grouped miss | `f(x) = (0 -> x)`<br>`f(y) ? y > 5 = "later"`<br>`f(9)` | `RuntimeError: No matching case for function f/1 with arguments [9]`. Returning `"later"` disproves the implementation of Option A |
| Legacy identical-header duplicate | `describe(x) = (0) -> "zero" \| (n) -> "other"`<br>`describe(y) = "later"` | the all-bind header key is identical → legacy `TypeError: Duplicate function definition: describe/1`, preserved byte for byte |

**Qualification of "same-arity clauses install" (corrects revision 3).** A same-arity clause installs **unless its declaration-level structural key equals an existing key** — identical all-bind headers (`describe(x)` / `describe(y)`), identical pattern/guard keys under the typed numeric rule (§2.2). Revision 3's sentence "a catch-all-header grouped declaration followed by any same-arity clause installs" was wrong for a later plain identifier header and is withdrawn. Compatibility consequences: no previously valid program changes; a pattern clause *before* a grouped declaration is reachable first, and a call it misses reaches the grouped declaration's header, whose case may then miss with no fall-through.

**Slice D boundary.** Retained arm keys are *evidence*, not permission to turn body alternatives into independent linked-view candidates. Slice D must reconcile its atomic cross-unit equal-key/shape rules with ordinary preparation and miss semantics. This revision does not lock new D linking oracles.

---

## 3. Pre-flight template (docs/process/00-preflight.md)

**CHANGE NAME:** Model B Slice C — default-open ordinary function execution and pattern/guard-headed ordinary functions
**CHANGE SLUG:** `issue-1269-model-b-slice-c`

**0. BRANCH.** Required: YES. Convention is `issue-<number>-<short-name>`; this documentation-only PR uses the harness-designated `claude/nice-brahmagupta-1e17ws`. The implementation branch (`issue-1269-model-b-slice-c`) does not exist yet. Base `main`.

**1. SCOPE LOCK.** Includes — executable ordinary `IrPatternFuncDef` outside a closed group; ordered clause groups with approved typed keys; same-arity distinct patterns and same-required-arity fixed+varargs coexistence; unified shape-stratum dispatch (D1); prepared block/header frames; declaration ownership and provenance; ordinary metadata channels and annotation publication; optional capability `default_open_functions` with the staging in §9.1; shared R16 + host-local RED/GREEN.
Excludes — Slice D: cross-module `extend`/`use` of **ordinary** exports, ordinary-base linked views, cross-unit duplicate/fixed-varargs/ambiguity validation, module-completion frozen projections. Slice E: `IrClosedFuncDef` execution, closed publication state machine, provisional self-identity, failed-callable semantics. C++ implementation. Core IR version bump. #1257 write-through retirement; #1268 and other maintenance. Nested named declarations; `@closed`; any new runner/protocol/capability framework. **Explicit R20 `open`/`extend`/`use` remain implemented and unchanged.**

**2. SOURCE OF TRUTH.** `GENIA_STATE.md` → `GENIA_RULES.md` → `GENIA_REPL_README.md` → `README.md` → `spec/*` → `docs/host-interop/*` → `docs/architecture/*`. Additional: contract, design, R20 contract/syntax-IR design, `docs/architecture/core-ir-portability.md`, `executable-semantic-conformance.md`.

**3. FEATURE MATURITY.** Partial (Python only after GREEN). Doc wording at GREEN: "Python executes ordinary pattern/guard-headed clauses and local default-open ordinary groups; ordinary-base `extend`/`use` linking and closed functions remain unimplemented; explicit R20 linking is unchanged; C++ not claimed." Nothing is documented as implemented earlier.

**3a. Portability Analysis** — §8.

**4. CONTRACT vs IMPLEMENTATION.** Portable contract: §§2.1–2.3, 3, 5.1–5.2, 6.1 as staged in §4. Python today: §1.1. Not implemented: all Slice C items, D, E.

**5. TEST STRATEGY.** Companion plan. Invariant: no previously valid program changes meaning except the enumerated, maintainer-approved deltas (§6.2).

**6. EXAMPLES.** Minimal: `fact(0) = 1` / `fact(n) ? n > 0 = n * fact(n - 1)` / `fact(5)` → `120` (target; today `model-b-not-implemented`). Real: noncontiguous clauses with `some`/`none`/`err` patterns for record-parsing stages.

**7. COMPLEXITY CHECK.** Revealing structure — reuse of R20 shape selection, per-unit matching and the shared trampoline; no second dispatcher.

**8. CROSS-FILE IMPACT.** `callable.py`, `evaluator.py`, `environment.py`, `optimizer.py` (C2), `interpreter.py` (optimize boundary, main group), `builtins.py` (help/doc/meta), `http_annotation_binding.py`, `server_route_binding.py`, `lifecycle_binding.py`, `test_cli.py`, `values.py`/`equality.py`, `spec/*`, `hosts/python/protocol_adapter.py`, tests. Drift risk: **High**.
MCP language-knowledge impact: **Affected** — see §10; update STATE, the `mcp_language_profile` registry and regenerate `apps/mcp/mcp.genia` **only after** verified GREEN.

**9. DOC DISTILLATION CHECK.** Creates process artifacts: YES → Doc Distillation at the end of the implementation PR. Adds docs/design or docs/architecture files: NO. Drift risk: High.

**10. PHILOSOPHY CHECK.** Minimalism YES; hidden behavior avoided YES (every valid→error delta is enumerated and approved; D8 Option A is verified as a contract interpretation; the temporary `main` boundary is documented, and its mixed cases are stop conditions rather than invented behavior); semantics out of host YES; pattern-matching-first YES.

**KILLER WORKFLOW ALIGNMENT.** Indirectly (Outcome, validation, record parsing). Validated-pipeline and Outcome specs must stay unmodified and green.

**11. PROMPT PLAN.** Preflight (this, rev. 4) → decisions resolved (§11) → independent Codex re-review → integration GO/NO-GO → **C0** evidence-plumbing prerequisite (§9.1) → RED → GREEN → maintainability review → docs → skeptic audit → distillation → final-head CI.

**12. HOST PARITY / CONFORMANCE.** Affected hosts: Python (implement), C++ (gap). Portable semantics: YES. Python/C++ updated: Python only after GO. Cross-host behavior verified: not claimed. Can one host merge first: YES (optional capability, honest gap entry). C++ pattern-header parsing is already UNSUPPORTED (Slice A, genia-cpp#50).

---

## 4. Slice C boundary (staged local C / D-linked / E-closed)

### 4.1 In scope (exact)

1. **Local default-open ordinary group.** A named ordinary function (`=`, `->`, block) is one live identity-bearing group; later same-owner declarations append in execution order, noncontiguously and across REPL submissions; aliases bound earlier observe appends made before the call; no clause is visible before its declaration executes.
2. **Executable pattern/guard headers.** `IrPatternFuncDef` outside `IrClosedFuncDef` installs into the same group. Header frame, guard and body scope per §5.2.
3. **Dispatch (D1 approved).** Shape stratum first: fixed arity `n` if any fixed clause of arity `n` exists, else eligible varargs; more than one distinct eligible minimum → ambiguity (legacy ordinary identity, §2.1). Fixed stratum does not fall through to varargs on pattern miss. Within the single unit, first matching clause wins. **Clause ambiguity cannot occur in C** (needs more than one unit).
4. **Duplicate keys** (§2.2, approved) rejected at declaration, before the clause is visible, with nothing evaluated.
5. **Ownership/provenance.** The group records `(canonical module identity, defining name)`. A declaration appends only through the binding that owns the group (§5.4, D5).
6. **Metadata** channels and annotation publication per contract §5.1–5.2.
7. **Slice B interaction.** Declarations cannot overwrite immutable bindings and `=:` cannot be declared over an existing function name; checks precede clause installation and annotations.

### 4.2 Excluded, with executable negative evidence required

- `IrClosedFuncDef` (including a pattern child inside it): still `model-b-not-implemented`, **no child annotation, guard or body evaluates, no provisional binding, no partial clause installed**.
- Ordinary export as `extend`/`use` target: still rejected (`open-function-target-not-open` / current `use` behavior). Recording provenance on an ordinary group must not make `isinstance` or duck-typed target checks accept it.
- Plain `import` never activates contributions. No module-completion projection, no linked-view introspection precedence, no cross-unit rules.
- Explicit R20 linked views, metadata policy and `extend`/`use` behavior: unchanged, **still reported implemented**.

### 4.3 Dependency analysis for D/E

| Aspect | Needed for local C? | Decision |
| --- | --- | --- |
| Provenance field on the ordinary group | Yes (ownership decision, stable key for D) | C |
| Declaration ownership (no append through foreign/alias bindings) | Yes | C |
| Typed structural key walker | Yes (local duplicates); reused unchanged by D | C |
| Frozen completion projection (clauses + three metadata observations) | No consumer in C | **D** (accepted deferral, D7) |
| `extend` of ordinary export; `use`; linked views; cross-unit duplicates, fixed/varargs conflicts, clause ambiguity | No | **D** |
| Closed publication, provisional frames, failed-callable reflection | No | **E** |

Smallest-alternative fallback (Codex §C): if C cannot keep these exclusions, retain the current module/linker and closed-node rejection untouched and add only local construction and dispatch adapters with a distinct ordinary-source policy/provenance marker. Do not broaden C to share a base class or target check.

---

## 5. Contract traceability and runtime impact

### 5.1 Traceability

| Contract / design | Requirement | Surface (read) | RED family |
| --- | --- | --- | --- |
| C §2.1 | Module-owned ordinary function open by default; explicit `open` unchanged | `GeniaFunctionGroup` (+owner), `Env.define_function`, evaluator branches | C-OPEN, C-R20 |
| C §2.1 | Lambdas/builtins/host callables get no interface identity | `callable.py`, `builtins._host_function_group` | C-OWN |
| C §2.2 | Accumulation, live alias, no early visibility | `define_function` | C-OPEN |
| C §2.2 | Preserve header captures, spellings, inline docs, annotation timing; do not lower via `IrOpenFuncDef` | evaluator `IrFuncDef`, block/case body evaluation (`eval_function_body`) | C-HDR, C-META |
| C §2.3 | Typed duplicate keys at construction | key walker replacing `_open_dispatch_key` | C-KEY |
| C §2.3 | Within-unit shape precedence, first match | `_dispatch_open` reuse | C-DISP |
| C §3 | Immutable bindings respected | `Env._reject_immutable_write` | C-IMM |
| C §5.1/5.2 | Three metadata channels; install then annotate | evaluator, `merge_binding_metadata`, builtins | C-META, C-ANN |
| D §13.4 | Header frame once per call; match-local shadows header; guard once; legacy error identities | record adapter | C-HDR, C-ERR |
| D §13.3 | Optional capability; C++ unsupported with owned gap | manifest, known gaps | §9 |
| D §13.5 | Inventory `iter_ir_nodes`, optimizer, route binding, native tests, code-doc tooling | listed in §8.5 | C-IR, C-CONSUMER |
| C §2.3 cross-unit; C §5.3 | — | — | **Deferred to D** |

### 5.2 Block-prefix and frame effects (C1)

Observed (P19): `f(x) { print("prefix"); k = x + 1; n ? n < k -> x | _ -> 0 }; f(2)` prints `prefix` **once**, then returns `2`. The block prefix runs before matching; `k` set by it is visible to a guard in the final case; the body then runs in the same prepared frame.

Required behavior (preserved for legacy identifier headers and inherited by any construct that uses the same body shapes):
- For a body that is a block ending in `IrCase`, **declaration-level preparation** runs the prefix exactly once per call, retains the prepared frame together with the selected match, and evaluates only the selected arm afterward.
- Prefix code is never part of declaration or key computation; flattening final arms, running guards before the prefix, re-running the prefix per arm, or recreating an empty body frame is a violation.
- Header frame is built once per call; for a pattern-headed clause it is the tuple pattern's bindings; match-local bindings shadow header bindings; guard sees header bindings; body sees match bindings.
- Fall-through and error handling are pinned in the RED baseline (no invented rollback of executed prefix effects).
- **Ordinary miss identity preserved (observed):** `f(x) = (0 -> x); f(1)` → `RuntimeError: No matching case for function f/1 with arguments [1]`. Reusing the R20 `TypeError` subclass for ordinary groups would be a regression; the text is pinned, the exception class is pinned too.

### 5.3 Optimizer retention (C2)

`interpreter.py:218` runs `optimize_program` on lowered IR before any declaration is evaluated. `optimizer.py` can rewrite an ordinary grouped `IrCase` body (the `pick(n, xs)` recursion over `(_, [])`, `(0, [x, .._])`, `(n, [_, ..rest])`) into the host-local `IrListTraversalLoop`, which does not retain the complete ordered arm sequence. Pre-flight requirement (mechanism chosen in GREEN design, observable fixed now):
- Logical keys, ordered arm records and dispatch order must not depend on whether the optimizer ran. **Original grouped-body arm keys, ordinals and necessary provenance MUST be captured before optimization, kept in a lossless original representation, or the rewrite declined (D8, §2.6 invariant 4); deriving them only from the optimized node is insufficient** (the rewrite keeps the empty/zero arms but not the recursive arm). Either (a) skip the rewrite for bodies of declarations that need retained structure until equivalence is proved, or (b) keep the original `IrCase` as a host-local field on the optimized node. Neither is serialized as portable IR; `IrListTraversalLoop` stays host-local.
- RED requires optimized-vs-unoptimized equivalence (same results, same duplicate decisions, same ambiguity/miss errors), a late declaration added after an optimized one, and retention of the existing collection-recursion regressions (`model-b-a-recursion-in-list`, `-in-map`, `test_model_b_optimizer_regression.py`).

### 5.4 Ownership and arity-keyed consumers (C5)

- `GeniaFunctionGroup` can no longer be only `dict[arity]`: distinct same-shape patterns need an ordered record list. The arity index, if kept, is a derived view for **legacy identifier-header records** only, keyed by required arity exactly as today (a legacy rest-parameter record stays at its required-arity key, which the `main` selector relies on — §2.5.1 M3). No inspection API may silently choose a representative of several clauses or miscount fixed/rest shapes.
- **Consumers to inspect (read):** `Env.define_function`, `builtins.py:3220` (`_format_function_shapes`, `_describe_function_group`), `interpreter.py:518` (main), `server_route_binding.py:267` (`sorted_arities() != [1]`), `http_annotation_binding.py:61,75` (`!= [0]`), `test_cli.py:189`, `lifecycle_binding.py:202`, `equality.py`/`values.py` identity and rendering.
- **Fixed+rest same-minimum hazard (C5/D3b):** `f(x)=…; f(x,..r)=…` both report required arity `[1]`, but the group is not an exact fixed one-argument handler. A distinct-arity-set rule would wrongly accept it. The per-consumer predicates and the approved conservative rule are in §2.5 (which also corrects revision 2's mistaken "varargs-accepting" claim: `@route` and HTTP annotations require `rest_param is None`).
- Ownership rule (design §4, D5): a declaration appends only to the group owned by the declaring scope's own binding of that name. Aliases, imported bindings, lambdas, builtins and host callables are not owners. Calls through aliases stay live (P1); an **immutable alias of a mutable ordinary callable does not freeze its accumulation** (observed `a =: f; f(x,y)=…; a(1,2)` → `3` on `main`). Declaration through an alias is rejected with `function-declaration-not-owner` (APPROVED, §2.3).

---

## 6. Observed baseline and compatibility assessment

### 6.1 Observed baseline (Python host @ `6d50a36`)

| # | Program | Today |
| --- | --- | --- |
| P1 | `f(x)=x; a=f; f(x,y)=x+y; a(1,2)` | `3` |
| P2 | `f(0)=1; f(n)=n; f(0)` | `model-b-not-implemented: declaration evaluation is not available` |
| P3 | `f(x)=1; f(y)=2` | `Duplicate function definition: f/1` |
| P4 | `f(a)=1; f(a,..r)=2` (also `f(x)=x; f(x,..r)=99`) | `Duplicate function definition: f/1` |
| P5 | `f(a,..r)="min1"; f(a,b,..s)="min2"; f(1,2)` | `"min2"` (**D1: becomes ambiguity error**) |
| P6 | same under `open` | `open-function-varargs-ambiguity: f/2 …` |
| P7 | same clauses, `f(1,2,3)` | `Ambiguous function resolution: f/3. Matching varargs: f/1+, f/2+` |
| P8 | `f(a)=1; f(1,2)` | `No matching function: f/2. Available: f/1` |
| P9 | `f(x)=x; f(none("r"))` | `none("r")` |
| P10 | `f(x)=x; a=f; a(x,y)=x+y; f(1,2)` | `3` (declares through alias) |
| P11 | module `lib` has `g(x)=x`; consumer `import lib; h = lib.g; h(x,y)=x+y; lib.g(1,2)` | `3` (cross-module append through alias) |
| P12 | entry `map(a,b,c)="mine"` | writes through to runtime scope R; `map(1,2,3)` → `"mine"`, `map(inc,[1,2])` → `[2,3]` |
| P13 | `open f(true)=1; f(1)=2`; `open f(1)=1; f(1.0)=2` | both `open-function-duplicate-clause` |
| P14 | `f(x)=x; open f(0)=1` | `open-function-redeclaration … already defined as an ordinary function` |
| P15 | `open f(0)=1; g(x)=x; f(n)=n` | `open-function-redeclaration … already declared open` |
| P16 | `open gcd(a,0)=a; gcd(a,b)=gcd(b,a%b); gcd(48,18)` | `6` |
| P17 | `f(x) ? x > 0 -> 1` | parse error "pattern/guard function headers cannot use ->" |
| P18 | `print(a,b,c)="mine"` | `Cannot define function print/3: name already bound to non-function value` |
| P19 | block-prefix program (§5.2) | prints `prefix` once, returns `2` |
| P20 | `f(x) = (0 -> x); f(1)` | `RuntimeError: No matching case for function f/1 with arguments [1]` |
| P21 | `((1) -> "a" \| _ -> "b")` over `1`, `1.0`, `true` | `a`, `a`, `b` (runtime matching, not key equality) |

Corpus (observed, scripted parse of repo `*.genia`): 183 files, 5 unparseable (not examined; **to verify**), 1,252 groups, 0 groups with ≥2 varargs clauses, 0 pattern-header clauses. Scope limit: top-level `.genia` only.

### 6.2 Does default-open change the meaning of previously valid programs? — yes, in exactly these ways

| ID | Change | Direction | Status |
| --- | --- | --- | --- |
| **B5 / D1 (P5)** | ordinary varargs with different minima, called at the larger minimum: result → ambiguity | valid → error | **APPROVED** (§2.1); migration note; oracle pinned |
| **B4 / D5 (P10, P11)** | declaring through a same-scope alias, or an imported binding, no longer appends | valid → error | **APPROVED** (§2.3): both rejected with `function-declaration-not-owner`; migration note pinned. P11 was an implicit cross-module modification. |
| B6 (P13) | explicit R20 `true`/`1` and `1`/`1.0` become distinct keys | error → valid (R20) | **APPROVED** (§2.2) |
| B1 | pattern/guard clauses execute | error → valid | new behavior |
| B2 | same required arity, distinct keys | error → valid | new behavior; legacy `Duplicate function definition: f/N` kept for identical keys of legacy-only clauses |
| B3 | fixed + varargs, same required arity | error → valid | per approved shape model |
| B8 | later clause shadowed by an earlier catch-all is silently unreachable | n/a | no warning invented; documented |
| B10 / D2 (P12) | entry write-through on prelude-owned names | **no change** | preserved; not retired in C |
| B11 | arity-keyed consumers on groups with pattern or fixed+rest records | none for legacy-only; new groups rejected by `@route`/HTTP/`@test` via their existing predicates and diagnostics; `main` is **not auto-selected** under the temporary boundary (§2.5.1); lifecycle and `help`/`doc`/`meta` unaffected | **APPROVED** (§2.5); `main` boundary DIRECTED (6326404613) |
| B12 | Core IR label | none | no bump (§13.2) |

### 6.3 Explicit-R20 compatibility matrix

| Surface | Slice C effect | Evidence (existing, unmodified unless stated) |
| --- | --- | --- |
| `open` + contiguous bare clauses (P16), grouped flattening, header-capture rejection, interface metadata (`@doc`/`@meta` only) | unchanged | `r20-*` shared specs; `tests/unit/test_r20_open_functions_*` |
| `open` after ordinary (P14); bare clause after ended run (P15) | unchanged | `tests/unit/test_r20_open_functions_diagnostics.py`, `spec/parse/parse-error-r20-open-redeclaration.yaml` (covered; no new duplicates) |
| duplicate-clause diagnostics | same category; key relation changes per §2.2 | C-KEY delta cases |
| `extend`/`use`, order independence, consumer non-transitivity, linked-view metadata | unchanged | all `r20-cross-module-*`, `error-r20-cross-module-*` |
| `use` over an ordinary function replaces it undiagnosed | unchanged (D owns the change) | characterization |
| automatic `none`/`some` over the shape stratum | unchanged for R20; ordinary pattern groups gain the same behavior | `r20-option-*`, C-OPT twins |
| tail calls | unchanged | `r20-open-*mutual-tail-call` |

---

## 7. Concurrency, reentrancy and writer atomicity (C6)

- **Publish atomically under the checked-owner boundary.** Validate the complete proposed declaration (key check, immutable/ownership check, inline-doc consistency) and publish clause, index and doc update as one step inside the existing `_BINDING_LOCK` critical section of `Env.define_function`. No partial clause/doc/index, no lost update.
- **Never run user code under that lock.** Matchers, guards, annotation expressions and bodies run outside it (Slice B rule: lock never held across user code). A guard or annotation that reenters evaluation and declares or rebinds must not deadlock or corrupt iteration.
- **Retain match/frame state through invocation.** A later declaration cannot retroactively change an already-selected clause's bindings.
- **No new portable scheduling semantics.** The contract grants no global ordering for concurrent calls. This revision **withdraws** revision 1's "dispatch snapshot / copy-on-write at dispatch start" as a *requirement*: it may be an implementation choice to avoid dictionary-iteration failure, but the RED plan asserts only (a) no iteration failure/crash, (b) no partial publication, (c) no bypass of immutable policy, (d) no deadlock. Stronger in-flight snapshot guarantees and rollback of executed effects are not claimed without approval.
- **Annotation failure (contract §5.2):** clause already installed stays callable; earlier attached metadata unchanged; collected metadata of the failed declaration does not attach; later annotations are not evaluated; effects of executed annotations persist.
- Meta-circular writers (`_meta_define`, `_meta_set`) route through the same checked path.
- Host-local tests use barriers and bounded joins, both writer orderings, failure recovery; no sleeps.

## 8. Seven-field portability analysis

1. **Portability zone.** Portable language semantics (shared R16) for local default-open ordinary groups and ordinary pattern/guard headers; plus Python-host-only implementation detail (record layout, lock, trampoline integration, optimizer interplay). `GENIA_STATE.md` authoritative only after GREEN.
2. **Core IR impact.** `IrFuncDef` (evaluation/ownership semantics; wire shape unchanged), `IrPatternFuncDef` (executable outside a group), `IrClosedFuncDef` (unchanged; still rejected), `IrAnnotation` (publication timing), `IrPat*` (key walker), `IrCase`/`IrBlock` (body preparation). Host-local `IrListTraversalLoop` is not portable and not serialized. No new nodes or fields; legacy `IrFuncDef` snapshots byte-stable; version label unchanged (`0.1.0`).
3. **Capability categories affected.** Required, never relaxed: `parser`, `ast_lowering`, `core_ir_eval`, `doc_help`. Optional: new `default_open_functions` (new behavior only); existing `open_functions`, `multi_file_eval`, `repl`, `refs`, `flow_phase_1`, `immutable_bindings` retain their original requirements on old-behavior tests. No `closed_functions` yet.
4. **Shared spec impact.** New `model-b-c-*` eval/error/cli cases; `spec/ir/model-b-a-*` untouched. Regression guards for already-working behavior keep their **original** applicability (ungated unless the original behavior needed a capability); only new behavior is gated.
5. **Python reference-host impact.** As §1.1/§8 cross-file list. Capability staging per §9.1: the Python adapter must not claim `default_open_functions` supported before the passing GREEN.
6. **Host adapter impact.** Python adapter: capability reporting only (no protocol change, no new operation). C++ adapter: `default_open_functions` unsupported + gap entry; no adapter change in this repository.
7. **Future host impact.** Node/Java/Rust/Go planned only. A host implements from the contract and shared cases without reading Python; the key encoding is the leakiest surface and is therefore specified by value (typed table in §2.2).

## 9. Host capability plan and evidence staging

### 9.1 Capability staging (C3) — C0 is implemented and merged (PR #1273); RED and GREEN are not authorized

Defect: `hosts/python/protocol_adapter.py::_python_claimed_capabilities` (line 38) claims `supported` for **every** manifest name except `shared_spec_runner`, and `tools/spec_runner/capabilities.py` derives the known names from the manifest's required/optional lists. Adding a new name to the manifest alone would therefore advertise execution that does not exist. Disclosure does not make a false claim accurate, and Slice B's provisional-claim precedent is acknowledged and **not repeated**.

**Status of C0 (revision 5): implemented, independently reviewed (PASS, #1273 `6333124626`), accepted (`6333148622`) and merged; the production override is empty and the advertised map is byte-for-byte the pre-C0 map. The paragraph below is the historical design-time status.** Integration owner: design-only conditional sign-off (comment 6322246286). Codex: **PASS for design** (comment 6324998154). Both are design statements. **No C0 code, manifest edit or adapter change is authorized or made.** C0 remains a separate prerequisite that needs its own authorization after the final-delta review.

**Capability-evidence terminology (corrected; use these terms exactly).**
- **External-host execution** (`python -m tools.spec_runner --host '<command>'`, `tools/spec_runner/runner.py::_run_via_host` → `host_executor.execute_spec_via_host`). A case whose `requires` are not all `supported` in the host's claimed capabilities (`capabilities.case_is_applicable` requires exactly `supported`) is reported **`unsupported` before the adapter is invoked** for that case. It is neither an executed failure nor a pass. It is *not* reported as "skipped".
- **A pytest skip is a distinct test-framework event** (for example a wrapper's `pytest.skip`). It must not be used as a synonym for `unsupported`, and the plan never converts a failing case into a skip, xfail or `unsupported`.
- **Unsupported cases are not passing conformance evidence.** A green exit code from an external-host run in which the new cases are all `unsupported` proves **no** new Slice C conformance. Reports give failed, passed, invalid and unsupported counts separately.
- **In-process path.** The default `python -m tools.spec_runner` (no `--host`; `runner.py::_run_in_process`) calls `executor.execute_spec` and `comparator.compare_spec` for every discovered case and **does not apply the external-host capability gate**. At RED it would therefore execute and *fail* the gated cases (U7). Evidence must name which path produced it.
- **Direct host-local RED runner.** A committed pytest harness that loads the **same YAML** through the existing loader, executes through the existing `execute_spec` / `hosts/python/adapter.run_case`, compares with the existing `compare_spec`, and fails with ordinary assertions on semantic differences. It auto-collects, selects all intended cases (including the ungated P5 tripwire and the ungated C-MAIN guards), retains actual errors and outputs, and never converts failures into skip, xfail or `unsupported`. Existing Slice A and R20 shared wrappers already use this pattern. **No second evaluator, expected-output store, protocol or certification system.**
- **Contract revision.** C0 changes no protocol, manifest-format or runner mechanism. This does **not** mean a `contract_revision` / contract SHA must stay frozen across commits: commit pins advance naturally, and "unchanged" refers to the mechanism only.

**Proposed mechanism (separately reviewable; not authorized).** A Python **claim-status override**, not another vocabulary registry (vocabulary remains the manifest):
1. **C0 (before RED).** A narrowly named constant `_VOCABULARY_ONLY_CAPABILITIES` (initially empty) in the adapter; `_python_claimed_capabilities` reports listed names `"unsupported"` (a valid declared status, `protocol.CAPABILITY_STATUSES`). With the set empty, the **advertised map is exactly unchanged** and no old applicability moves. `test_python_claimed_capabilities_covers_the_full_vocabulary` (`set(claimed) == known_capabilities()`) still holds and gains an assertion that vocabulary-only names are `unsupported`.
2. **RED commit.** Add `default_open_functions` to `spec/manifest.json` **and** to the override set together; add the C++ gap entry; add the gated cases. Under external-host execution the gated cases are reported `unsupported`, not run, and are not evidence. Old ungated and old-capability guards run normally and must pass.
3. **RED evidence.** The direct harness above (`tests/spec/test_model_b_slice_c_red.py`) fails with recorded messages. It is the committed failing-test evidence and the only place the external-host gate is bypassed.
4. **GREEN commit.** Remove the name from the override set in the commit whose gated cases pass (Python then reports `supported` truthfully). GREEN cites the failing-test (RED) SHA. If no staged names remain, delete the override; otherwise keep the small empty generic set with coverage. Convert the harness into an ordinary thin shared-case wrapper. No permanent C-specific machinery is required.

*Smaller alternative (recorded, not chosen):* omit the new Python claim entirely — absence also gates cases as `unsupported` and is protocol-compatible — at the cost of intentionally breaking the full-vocabulary advertising convention that the existing test pins. The override preserves that convention.

Properties the review checks (falsifiable): (i) `unsupported` is already a valid declared status; (ii) the external-host runner reports gated cases `unsupported`, never passed; (iii) the committed failing harness makes RED visible, so genuine failures are not hidden; (iv) names already in the vocabulary keep `supported` and old-case applicability is untouched, with an exact-unchanged map assertion for the empty prerequisite; (v) `set(claimed) == known_capabilities()` stays true; (vi) the flip to `supported` happens only in the commit whose gated cases pass; (vii) the C++ side is unaffected (the parity gate reads C++ evidence only). Guards for C0 when authorized: unchanged advertised map; staged known name `unsupported`; external-host `unsupported` without invocation; direct same-YAML comparator failure; unchanged old requirements; non-vacuous selected-case counts; GREEN `supported` with passing shared evidence.

### 9.2 Python
Claims `default_open_functions` = supported only at the GREEN head with all gated cases passing.

### 9.3 C++ (read-only here)
Not implemented. Add (RED commit) a `spec/known_host_gaps.json` entry for `default_open_functions`: `tracking_issue: m0smith/genia-2026#1269`, `affected_host: cpp`, exact case IDs, reason, removal condition. Facts: C++ lacks pattern-header parsing (genia-cpp#50) and `=:`; `multi_file_eval` is already a listed gap. **Pre-existing discrepancy, not a Model B gap:** reviewer-observed that the available C++ adapter binary returned OK/`1` for `open f(x)=1; f(y)=2; f(3)` instead of duplicate rejection (binary pinned to ancestor contract `6402e668`, provenance not certified). Track it distinctly under #1250 ownership; do not put it in the `default_open_functions` gap entry and do not count it as conformance. A genia-cpp child issue must be opened by the integration owner (this session cannot reach `genia-cpp`). Required capabilities are not eligible for optional-gap entries. UNSUPPORTED is never reported as PASS. Direct-IR twins are host-local (R16 `eval` accepts source only).

## 10. Security, diagnostics, MCP, documentation, rollback

- **Security/diagnostics.** (a) Closing P11 (cross-module append through an alias) is an ownership-boundary change; its diagnostic names the canonical module identity or `<entry>` only — no paths, addresses or captured values. (b) `No matching case … with arguments [...]` uses `format_debug`; RED asserts a protected (R10) sentinel does not appear in new pattern-group diagnostics. (c) D2 amplification (P12) is characterized, not widened. (d) The key walker rejects malformed structure deterministically; no `repr` fallback.
- **MCP language profile (C8 wording).** Affected, held until GREEN. After GREEN the profile's `idioms.clauses` must say: ordinary pattern/guard-headed and multi-clause functions execute locally in Python; **ordinary-base linking (`extend`/`use` of ordinary exports) and closed `f(...)=:` functions remain unavailable; explicit R20 `open`, `extend` and `use` remain implemented and unchanged.** Revision 1's phrase "`extend`/`use` … not available" was wrong and is withdrawn. Update STATE anchors/fragments (`state:open-functions` fragment "must carry the `open` keyword" stays true for explicit open interfaces), the `mcp_language_profile` registry, regenerate `apps/mcp/mcp.genia` via `tools/gen_mcp_language_profile.py`, run its check and `tests/doc` sync tests. `docs/ai/LLM_CONTRACT.md`'s sentence about literal first parameters needing `open` is revised then.
- **Documentation plan.** Companion §6. No authoritative document is changed by this PR. STATE/RULES/REPL/README describe the **local partial boundary**, never completed Model B.
- **Rollback/containment.** Changes are confined to the ordinary group record, key walker, body preparation and two evaluator branches; revert the implementation PR together with the manifest/gap/adapter-set edits and docs. C and D roll back together once linked views ship. A rejected declaration installs nothing; annotation failure leaves the installed clause (contract §5.2). Earlier effects are not rolled back.

## 11. Decision register (decisions precede GO)

| ID | Decision | Status | Where pinned |
| --- | --- | --- | --- |
| **D1** | Unified shape-stratum varargs dispatch; P5 valid→error; legacy ordinary ambiguity identity | **APPROVED** (comment 6321690337) | §2.1; C-DISP |
| **Numeric keys (D4)** | Distinct Boolean/integer/float tags; same-binary64 = duplicate; explicit-R20 acceptance change | **APPROVED** (comment 6321761534) | §2.2; C-KEY |
| **D5** | Only the owning declaration binding appends; same-scope and imported aliases rejected; calls stay live; immutable alias does not freeze; one category `function-declaration-not-owner` with distinct local/foreign messages | **APPROVED** (comment 6322649763); literal messages are RED oracles locked after baseline characterization | §2.3; C-OWN |
| **D3** | Preserve legacy duplicate/shape-miss/case-miss/ambiguity identities; normalized `open-function-duplicate-clause` for new pattern-header duplicates; ownership category | **APPROVED** (comment 6322649763); texts re-pinned byte-for-byte in RED baseline | §2.4; C-DISP, C-ERR |
| **D3b** | Legacy-only consumers unchanged; `@route`/HTTP/`@test` reject pattern-bearing or fixed+rest-mixed groups via their existing predicates; `main` follows the temporary boundary (§2.5.1); lifecycle has no signature gate; no representative clause; `help`/`doc`/`meta` keep working with deterministic new-group rendering | **APPROVED** (comment 6322649763); `main` clarified by 6326404613 | §2.5, §2.5.1; C-CONSUMER, C-MAIN |
| **D8** | Option A: one declaration-level key per legacy identifier-header declaration for local duplicate detection; original arm keys/ordinals/provenance MUST be retained or losslessly derivable; no fall-through; explicit R20 flattening unchanged | **APPROVED; VERIFIED as a contract interpretation** (Codex `6324998154`, integration `6325204788`); five mandatory invariants | §2.6; C-D8 |
| **D2** | Preserve entry/prelude write-through; do not retire in C | Resolved (integration + Codex); no new decision | C-OWN |
| **D6** | No Core IR version bump | Resolved by design §13.2 | — |
| **D7** | Provenance in C; frozen projections in D | Accepted (integration + Codex) | §4.3 |
| **C0** | Vocabulary-only capability staging | **Implemented and merged (PR #1273); independent review PASS; accepted.** Previously design-approved; terminology corrected in §9.1 | §9.1 |
| **U2 main** | Temporary compatibility boundary; legacy selector unchanged; mixed shapes are stop conditions | **DIRECTED** (comment 6326404613); #1271 owns the long-term lifecycle | §2.5.1; C-MAIN |

**Uncertainty register after revision 4.**
- **U1 — D8 / design §3.2:** **resolved** (Codex PASS as a contract interpretation, no amendment; mandatory invariants in §2.6).
- **U2 — `main`:** **dispositioned.** Temporary compatibility boundary (§2.5.1). Residual: SC-MAIN-1…5 (mixed shapes) are stop conditions with no manufactured expectation; the long-term behavior is #1271. Risk: a user can write a pattern-bearing `main` that silently never runs as the entry; documented, not diagnosed.
- **U3 — lifecycle:** **resolved.** `lifecycle_binding.py:199` has no signature gate; ordinary callable groups remain callable; no new binding-time rejection (§2.5).
- **U4 — literal diagnostic texts** for D5 and the new-group shape listing remain proposals until the RED baseline byte-characterizes the surrounding infrastructure.
- **U5 — file-mode span labels:** `_format_open_span` keeps the entry source label as given; in file mode that label is whatever name the CLI was given (existing R20 behavior). The ownership diagnostic deliberately renders no spans. Whether new duplicate diagnostics in file mode need the same property is for the RED baseline to characterize.
- **U6 — C0:** **resolved** (design PASS; implementation merged via #1273). The terminology corrections of §9.1 apply.
- **U7 — in-process runner at RED (resolved in revision 5 by the R1 matrix in `issue-1269-slice-c-red-authorization-package.md` §2: the in-process run and four in-process workflows are expected to FAIL on the RED head, the external host run exits non-zero only because of the ungated P5 tripwire, and the unmodified parity test fails at RED and must pass unchanged at GREEN; originally:** the default `python -m tools.spec_runner` path does not apply the external-host capability gate (§9.1), so gated `model-b-c-*` cases would be *executed* and *fail* there at RED. Whether that run is part of required CI at the RED commit must be recorded in the RED baseline; it is not hidden or converted to a skip.)

**Stop condition (design §11):** if a RED case cannot be written without a new semantic choice, stop and return to #1249.

## 12. Gate

- **Current gate (revision 5): NO-GO for RED until the integration owner issues a separate RED authorization with the R1–R5 package (`issue-1269-slice-c-red-authorization-package.md`) independently reviewed and decisions O-1–O-3 settled; G1 is a before-GREEN decision.** Historical revision-4 order of events: (1) Codex exact-head final-delta review of this revision (U2 boundary and stop conditions, D8 mandatory retention and oracles, C0 terminology, D3b consumer facts); (2) integration owner records separate GO/NO-GO decisions for **C0** and for **RED**.
- Implementer recommendation: with D8 verified, C0 design-approved and the U2 boundary documented, every RED oracle that does not depend on SC-MAIN-1…5 or U4 literal-text characterization is determinable. Recommendation, not approval; no gate is self-certified.
- Not started and not authorized (C0 itself is merged via #1273): RED, GREEN, manifest/adapter/spec edits, merge, parent closure, genia-cpp issue creation, and any work on #1271. Authoritative documents (`GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, MCP profile) remain unchanged and continue to describe only currently implemented behavior. When Slice C eventually passes GREEN, the companion plan §6 requires updates to `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, semantic facts, the MCP language profile and the affected host documentation. #1268 stays separate and non-blocking.
