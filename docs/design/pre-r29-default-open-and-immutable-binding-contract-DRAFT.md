# #1249 — Default-open function interfaces and immutable bindings: proposed semantic contract

**Status: MAINTAINER-APPROVED SEMANTIC CONTRACT (2026-10-16) — PARTIALLY IMPLEMENTED (Python reference host: immutable bindings and ordinary default-open execution; closed functions and cross-module linking are not implemented).** Maintainer explicitly approved the consolidated Model B semantics in conversation on 2026-10-16. Independent Codex focused semantic review of revision `5060d52` returned **PASS** (no new blocker in that focused diff). The subsequent consolidation was checked for preservation of the reviewed semantic decisions; neither the focused PASS nor approval constitutes implementation or host parity evidence. `GENIA_STATE.md` remains the source of truth for what Genia currently implements.

**Scope:** New default function openness, additive cross-module contribution coherence, `=:` immutable lexical bindings, `f(...)=:` closed function definitions, compatibility and portability boundaries. Applies prospectively after #1250/#1251 implementation, tests, documentation synchronization, and audit. Existing R20 behavior is unchanged until then.

**Evidence and history:** merged pre-flight `docs/analysis/pre-r29-function-immutability-preflight-DRAFT.md`; implemented R20 and `docs/design/r20-open-functions-contract.md`; incremental review/correction commits `de68abba`, `3151ff6`, `3fa80b3`, `b8262d5`, `f578efa`, `3abbb59`, `5060d52`. Git history preserves the full successive drafts. The final PASS was a **focused contract review**, with read-only Python baseline probes, not a runtime implementation, full regression, C++ parity certification, or maintainer approval.

## 1. Design principles

1. **Model B is the selected direction:** module-owned ordinary named functions are extensible by default. No `@closed` syntax.
2. Extension contributions are **additive**: never replace an existing clause record or mutate an already-selected view. Exact duplicate keys are invalid; distinct overlaps may cause deterministic ambiguity rather than implicit priority.
3. Importing contributions never activates them; a consumer must explicitly select them with `use`.
4. Immutable **binding** is distinct from deep immutability of referenced Ref/Cell values and from callable **closedness**.
5. Preserve existing ordinary syntax and behavior wherever possible, including noncontiguous declarations, aliases, documentation, and annotation failure timing. Maintain compatibility with explicit R20 `open` behavior as a distinct historical source form.
6. Keep portable behavior host-independent and keep unimplemented syntax out of `GENIA_STATE.md` and user-facing language profiles until verified.

## 2. Function openness and contribution authority

### 2.1 Default-open ordinary functions

A **module-owned ordinary named** `f(pattern) = expression` function defines an open interface by default, including when exported. Its owner need not write `open` or authorize an outside contributor. Existing explicit `open f(...)` remains accepted with its historical R20 syntax and metadata constraints.

Default openness does **not** automatically grant module/export interface identity to lambda values, builtins, host-callable values, local factory instances, or arbitrary callable aliases. Cross-module `extend` targets only exported, module-owned declared open interfaces. Re-exported base interface aliases retain the original interface provenance. An already linked view is not a new `extend`/`use` target merely because it is exported.

`extend alias.f(pattern) = expression` declares an **inert contribution unit** in its contributing module. A consumer's `use f from base with contributor` constructs an **immutable linked view** of the selected base and contribution units. Mere `import` of either module does not activate contributions. Imported base and all selected contributor modules must finish initialization successfully before linking; the consuming module may still be executing its top-level statements.

### 2.2 Ordinary base-unit accumulation and aliases

For ordinary-source functions, compatible declarations of the same module-owned function, **including noncontiguous arity clauses**, append to the *same base unit* as execution reaches them. They remain source-ordered; the first matching clause *within that unit* wins according to currently accepted ordinary behavior. A clause is not visible before its declaration executes.

An alias bound by `a = f` refers to the same identity-bearing ordinary callable interface while base-unit declarations accumulate; it **sees subsequently declared arities**, consistent with today's ordinary function-group behavior. For example, `f(x)=x; a=f; f(x,y)=x+y; a(1,2)` yields `3`; an interleaving unrelated statement does not seal the ordinary base unit. A call before the later arity is installed must not see that future clause.

A completed imported module exports its completed base unit. Consumer-local `use` views freeze the selected clause set; later unrelated imports, contribution declarations, or modifications of an ordinary base unit during another context do not retroactively add clauses to an existing linked view.

Existing ordinary grouped-case bodies, header variable captures, `=`/`->`/block function spellings, inline documentation, `@category`/`@route`/`@test` and other currently accepted metadata must remain compatible. Do **not** blindly lower all ordinary functions via the current R20 `IrOpenFuncDef` path with its different header-capture and annotation restrictions.

Named nested declarations such as `make(k) = { f(x) = x+k; f }` remain **unsupported** as in the verified baseline. Existing lexical lambda factories remain supported; each invocation's captured callable value is distinct and cannot be externally extended as a module-owned interface. Nested `f(...)=:` definitions are not implicitly introduced by this proposal.

### 2.3 Duplicate keys, overlapping patterns and arity-shape coherence

- **Syntactic duplicate relation.** A dispatch key is a host-neutral representation of a clause's patterns, guards and arity shape with typed literal tags (`true` and `1` are distinct) and scope-aware alpha normalization. Free identifiers participate as syntactic references; the key does not prove equal captured runtime values or semantic matcher equivalence. Neither guard nor matcher nor clause body executes when keys are computed.
- **Validation boundary.** Reject duplicates within each declaration/contribution unit at construction. On `use`, validate all selected units *atomically before publication*; reject equal keys across different participating units, including base-vs-contribution, with both source provenances. The inert contribution may still exist before its selection. Selection order cannot turn a duplicate into a winner.
- **Cross-unit fixed/varargs conflict.** Reject a linked view if a fixed-arity clause of arity `n` in one unit conflicts with a varargs clause in another participating unit whose minimum arity `m <= n`. This conservative rejection prevents existing R20 shape-stratum selection from silently suppressing previously matching varargs behavior; it may reject disjoint patterns. Within-unit R20 shape precedence is preserved.
- **Other overlaps.** Distinct structurally keyed patterns with compatible shapes may overlap. At invocation, after the existing shape selection, take the first matching clause of each participating unit. If multiple participating units match, produce normalized deterministic ambiguity, **not** specificity-based priority, import-order priority, override, or last-writer wins. A catch-all base may therefore make a selected specialization ambiguous.
- **Guarantee boundary.** Clause records are never silently replaced. This is *not* full observational noninterference: matcher/guard side effects and failures may occur during candidate discovery, and R20 Option-aware propagation may be affected by selected clauses. Determinism describes candidate choice and normalized diagnostics after successful matching, not arbitrary guard-effect order.

## 3. Immutable lexical binding: `name =: initializer`

- A valid `name =: initializer` declares a **new immutable binding** in its current lexical declaration scope, initialized exactly once. It does not freeze or overwrite an already-existing binding in that same scope, including a parameter/import name. Same-scope duplicate declaration fails.
- Ordinary `name = value` continues nearest-binding resolution and rejects writing to an immutable resolved binding; it does not silently create a shadow. An **explicit nested** `name =:` may shadow a non-reserved outer user binding without modifying it.
- Every language-visible binding writer obeys immutability: `=`, `use`, import aliases, named declarations, annotations, autoload/prelude publication, and other binding-producing operations. Where a target is known invalid before evaluating its initializer, reject **before** initializer execution and its effects.
- **Runtime-owned names:** an entry-scope `=:` declaration of a name owned or reserved by the runtime/prelude (including an unloaded reserved prelude name) deterministically fails before initializer evaluation. Thus `print =: 7` is rejected; neither runtime-scope rebinding nor entry-scope shadowing occurs. Existing `=` runtime-owned entry write-through semantics remain as specified by implemented STATE; this draft does not change #1229/#1230 scope behavior. The set of reserved names must be faithfully represented by the host/portable language boundary and cannot depend on whether a lazy prelude name happened to load.
- Function parameters retain existing assignability by default. Binding immutability is **shallow**; mutating a referenced Ref, Cell, or authorized capability does not reassign the binding itself.

## 4. Closed function definitions: `f(pattern) =: expression`

### 4.1 Group boundary and identity

A maximal consecutive run of same-name `=:` clauses (ignoring comments and blank lines) creates **one closed callable and one immutable defining name**. A different statement, or a completed REPL submission, ends the run. Mixing `=` and `=:` in a run, adding later same-scope clauses, rebinding its defining name, or extending the callable via an alias is invalid. Callable closedness follows the value through aliases; immutable name ownership applies to the defining binding, not arbitrary alias bindings.

Validate the group's structure (shapes, duplicate keys, mixing, declaration collision, permitted metadata) before exposing any completed binding. Preserve existing ordinary-compatible clause bodies, recursion/TCO, annotations and documentation where accepted, except for the explicitly different atomic closed-publication rule below.

### 4.2 Provisional publication for self-referential annotations

After successful structural validation, a provisional closed callable becomes available by its own name **only to synchronous invocations arising from its declaration-owned annotation evaluation and their recursive calls**. It captures its own self-identity and does not resolve recursion against a later same-named declaration. While it is **initializing**, external process/task invocations and callable-specific introspection fail with `closed-function-not-yet-published`; ordinary value transport is allowed.

On successful ordered dynamic annotation validation, commit the callable and immutable binding. On annotation failure, permanently mark the provisional callable **failed** before withdrawing its provisional defining name; no completed binding or partial declaration metadata is published. Effects already performed, including writes storing a reference to the provisional callable, are *not* rolled back.

An escaped failed callable is a **transportable opaque value**. Ordinary assignment, argument passing, closure capture, return, collection storage, equality under existing callable-identity rules, and generic safe rendering are allowed and never revive it. Generic rendering exposes only a sanitized opaque failed-callable marker, not source, captured values, partial metadata or protected content.

**Actual callable use**—direct, higher-order, trampoline/indirect invocation, `extend`/`use` targeting/linking, or callable-specific `doc`/`meta`/`help` inspection—rejects with normalized `closed-function-failed-publication`. On an *actual invocation*, this target-state rejection precedes target-specific `none`/`err` propagation, arity selection, pattern matching, guard or body evaluation. Thus invoking an escaped failed callable with `none` errors; an upstream Outcome/Flow stage that already skips invocation remains skipped.

Synchronous declaration-owned calls complete before the annotation transaction commits or fails. Other in-flight invocations are never admitted while initializing; no cancellation semantics or rollback of arbitrary external effects is implied. A later permitted REPL name reuse creates a **new identity** and cannot redirect or resurrect escaped failed callables.

## 5. Ordinary metadata ownership, failure and linked-view projection

### 5.1 Ordinary function metadata and lookup

Preserve **three distinct channels** of existing ordinary function metadata:

1. **Binding annotations:** `@doc`/`@meta` and allowed annotations merge onto the *named declaring binding* across later clauses. On successful list evaluation, newer keys overwrite equal older keys, with unmentioned keys retained. An unannotated alias receives no copy of binding-owned annotations; an annotated alias has its own binding metadata.
2. **Callable inline documentation:** ordinary inline docstrings belong to the shared callable group, remain visible through unannotated aliases when there is no effective binding `@doc`, and retain existing consistency checks before installation of a conflicting clause.
3. **Shared effective help:** `help(name)` observes the ordinary callable group's shared help-facing metadata and its legacy inline-documentation fallback, which can be altered by an alias's annotation without altering another binding's `doc`/`meta`.

For ordinary callables, `doc(name)` first uses the named binding's `@doc`, then callable inline documentation, else existing missing-doc behavior. `meta(name)` returns the binding-owned map for that name (or `{}` for an unannotated alias). `help(name)` uses the shared callable help-facing channel, **which need not equal `doc(name)`**.

Historical explicit R20 `open` declarations retain their existing *interface-owned* metadata and syntax/annotation restrictions. The default-open ordinary-source path preserves legacy ordinary metadata observations instead of inheriting the historical explicit-`open` metadata route merely because it became extensible.

### 5.2 Ordinary annotation publication

For an ordinary-source function declaration, structurally validate and **install the clause first**. Then **evaluate and validate each annotation individually in source order**, retaining existing preliminary checks and stopping at the **first failure without evaluating later annotations**. Accumulate validated metadata privately; **attach it only if the entire annotation list succeeds**, as one declaration-level commit.

If an annotation fails, the newly installed clause remains callable and earlier successfully attached metadata remains unchanged; none of the failed declaration's collected metadata attaches. Effects of *already executed* annotation expressions persist. A conflicting inline docstring fails before installing the new clause. This deliberately differs from the closed `=:` atomic-publication rule.

### 5.3 Linked-view metadata: event, content and lookup

At **successful completion of base-module initialization**, freeze an immutable exported base-interface projection with **three separate observations**:

1. the original *defining binding's successfully accumulated annotation map* (not metadata attached solely to aliases);
2. the defining binding's *effective* `doc` value at that moment, using binding `@doc` first and legacy inline fallback second; and
3. the callable's *effective help documentation and summary metadata* at that moment, with shared help-metadata documentation taking precedence and **legacy inline documentation as its own fallback**, *independent of* channel 2's defining-binding `doc`.

A linked view of a default-open ordinary base uses channel 1 for `meta(view)`, channel 2 for `doc(view)`, and channel 3 plus selected clause provenance for `help(view)`. Views linked later from the same completed base use the same frozen snapshot. Later alias annotations cannot change existing or future linked views' frozen metadata. Contributor metadata never overwrites the base projection.

**No new view-binding override:** annotating a local assignment/alias of a linked view may create ordinary local binding annotations, but these do **not** overlay or replace linked-view `doc`/`meta`/`help` introspection; linked-view callable projection takes precedence for that lookup and propagates through ordinary view aliases. Direct annotation on `use` remains prohibited. This is an **intentional candidate compatibility divergence** from asymmetric lookup observed in the current Python R20 implementation, not an implicit rewriting of historical explicit-`open` views; those keep their approved R20 interface projection.

For example, where the defining binding has `@doc "canonical"`, the callable inline documentation is `"inline"`, and an alias adds only shared help category metadata, `doc(view)` remains `"canonical"` while `help(view)` renders `"inline"`. The frozen help fallback is not incorrectly derived from the defining-binding `doc`.

## 6. Compatibility, portability and process gates

### 6.1 Portability analysis

1. **Observable boundary:** source parsing, module/entry lexical ownership, ordinary clause publication, callable dispatch, metadata and linked-view snapshots, closed/provisional lifecycle, diagnostics and REPL behavior.
2. **Core IR:** preserve host-neutral expression of immutable declarations, local/function/interface identity, atomic group boundaries, unit provenance, provisional callable states and metadata channels. Concrete version-safe carrier design follows *after contract approval*; no opportunistic breaking IR rewrite or second dispatcher.
3. **Shared conformance:** after approval, #1250 must create failing shared R16 executable cases for the observables in this contract and document the red-test commit before implementation. Contracts contain semantic rules, not embedded test suites.
4. **Capability applicability:** reuse the existing R16 runner, manifest protocol and capability selection; never label already-supported ordinary function behavior unsupported to mask regression.
5. **Host truth:** Python reference-host support and C++ host support are separately evidenced. Unsupported C++ cross-module/TCO surfaces remain accurately classified, with issue-backed gaps and removal conditions rather than invented parity.
6. **Gap handling:** no unowned porting gaps and no host-dependent semantics; exact direct-Core-IR vs source agreement for the surfaces each host claims to support.
7. **Documentation synchronization:** after verified implementation, #1251 updates `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, shared spec/host documentation, `docs/contract/semantic_facts.json` and generated MCP language-profile projection, examples and release evidence. Draft status must remain unmistakable until then.

### 6.2 Approval and independence

- The maintainer **explicitly approved the consolidated Model B contract on 2026-10-16**, including conservative fixed/varargs cross-unit rejection, runtime-reserved-name rejection for `=:`, legacy metadata compatibility/frozen linked-view introspection, and failed provisional-callable invalidation. Any material post-approval semantic change requires another contract decision.
- Independent Codex review yielded a **focused PASS on `5060d52`** after preceding REVISE cycles. A subsequent structural semantic-preservation check compared consolidation to the reviewed candidate; no additional independent Codex equivalence verdict or runtime/host conformance is claimed.
- With #1249 contract approval recorded, #1250 may proceed **only in phase order**: portable design → committed failing shared R16 specs/evidence → bounded host implementations → maintainability review; no code changes are authorized directly by this contract PR.
- #1251 follows verified implementation: truth-doc/MCP profile sync → skeptic audit → distillation. Do not treat the roadmap placement, open PR or green CI as semantic implementation approval.
- #1229/#1230 own independent module-scope/compatibility closeout. PR #1254 merged the fallback removal; do not restore removed behavior or silently close those gates. R29 language-facing implementation remains separately gated.
- No runtime code, shared specs, protected registry, authoritative implemented-language docs, C++ host claims or unrelated issues are altered by this contract-only PR.

**Contract disposition: APPROVED MODEL B SEMANTIC CONTRACT — FOCUSED REVIEW PASS; NOT IMPLEMENTED.**
