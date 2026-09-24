# Unified Function Model — Semantic Contract (Issue #1010, F1)

Status: **PROPOSED — DRAFT FOR ARCHITECTURAL REVIEW. NOT APPROVED.**
`GENIA_STATE.md` remains final authority for implemented behavior. This
document defines a candidate semantic contract only. It does not change,
and must not be read as changing, any implemented Genia behavior. No
surface syntax is chosen here (see §0.3). No Core IR is redesigned here
(see §14, which records requirements only). Nothing in this document may be
cited as approved until issue #1010's F1 gate is explicitly passed by human
review, per the issue's own required process.

This document supersedes no existing contract. `docs/design/r20-open-
functions-contract.md` remains the authoritative description of currently
*implemented* R20 behavior until an approved follow-up contract and its own
design/failing-test/implementation/docs/audit phases replace it.

## 0. Scope and method

### 0.1 What this document is

A precise answer to issue #1010's 25 semantic questions, plus the
required critical-decision analysis (permission vs. composition-only
authority), plus the required-invariant mapping, for **one** Genia
Function model that covers what is implemented today as two runtime
species — ordinary named functions (`GeniaFunction`/`GeniaFunctionGroup`)
and R20 open interfaces (`GeniaOpenFunction`/`GeniaOpenContributionUnit`/
`GeniaLinkedOpenFunction`).

### 0.2 What this document is not

- Not a test file. No pytest code, no YAML spec cases.
- Not an implementation plan. No parser, lowering, or Core IR field names
  are fixed here beyond the semantic requirements §14 hands to a future F3.
- Not a syntax decision. `open`, `extend`, `use`, `extensible`, punctuation,
  and any other spelling are explicitly out of scope (issue #1010,
  "Surface syntax is out of scope"). Where this contract must refer to a
  spelling-independent concept that F2 will eventually spell, it uses the
  issue's own placeholder vocabulary (Function, Clause, ContributionUnit,
  FunctionView) and, where a permission property survives, an abstract
  "extensibility permission" property — never a candidate keyword.
- Not a release. Per `AGENTS.md`'s product-priority section and issue
  #1010's non-goals, this is R20-follow-up design work, not a new release
  number.

### 0.3 Relationship to the R20 contract

Every reference in this document to "current implementation" or "current
contract" means `docs/design/r20-open-functions-contract.md` plus
`GENIA_STATE.md` §4 (ordinary functions) and §4.7 (R20). Where this
contract proposes a change from that baseline, the change is called out
explicitly as **[CHANGE FROM R20]**; unmarked text preserves current R20
semantics verbatim, restated in unified vocabulary.

---

## 1. What is a Clause?

A **Clause** is the unit that a `case`-arm, a lambda body, an ordinary
grouped-function arm, and an R20-style pattern-headed clause already all
reduce to in the current implementation: one ordered tuple of

- an argument pattern (portable Core IR pattern: identifier bind, wildcard
  `_`, literal, tuple/list/map sub-pattern, `some(...)`/`err(...)`,
  named-pattern use, at most one trailing rest pattern for varargs);
- an optional guard expression over the pattern's bindings;
- a body expression/block;
- a callable shape derived from the pattern (fixed arity `n`, or varargs
  with minimum arity `m`) — never stored redundantly, always derived from
  the pattern, exactly as R20 already requires (R20 contract §10, note on
  arity derivation); and
- a provenance record: declaring Function-or-ContributionUnit, declaring
  module/source-unit identity, source span, and lexical ordinal within its
  owning ordered list.

This is not a new concept. It is the existing `IrCaseClause` family
generalized to be the *only* clause representation a Function is built
from — including what ordinary `IrFuncDef` currently represents as a
single-clause, single-arity `GeniaFunction`. **[CHANGE FROM R20]**: today,
an ordinary function's single clause is *not* a first-class provenance-
bearing record distinct from the `GeniaFunction` object itself; unifying
requires every ordinary function clause to carry the same provenance shape
an R20 clause already carries, even though ordinary functions do not
currently expose per-clause provenance in diagnostics.

A Clause is never independently callable. It only has meaning as a member
of a Function's ordered local clause list or a ContributionUnit's ordered
clause list.

## 2. What is a Function?

A **Function** is one identity-bearing value consisting of:

- a stable **origin identity** (§3);
- an **ordered list of local Clauses**, declared in the Function's own
  declaring module/source unit, in lexical declaration order;
- optional interface-level metadata (`@doc`, `@category`, `@since`,
  `@deprecated`, docstring) that belongs to the Function as a whole, never
  to an individual Clause; and
- (only if the permission model in §26 requires it) one extensibility
  permission property, decided once at declaration and immutable
  thereafter.

Every named, pattern-dispatched, top-level Genia function is a Function
under this model — there is exactly one Function species. **[CHANGE FROM
R20]**: this collapses `GeniaFunction`/`GeniaFunctionGroup` (ordinary) and
`GeniaOpenFunction` (R20 base) into one runtime concept. A Function called
directly (with no externally selected contributions) dispatches using only
its own local Clauses — this is the R20 contract's "one participating
unit" case generalized to be the *only* case for a Function that has no
FunctionView built over it, which is also exactly how every ordinary
function behaves today. Ordinary functions do not become "extensible" by
this unification unless the permission model in §26 says so; unifying the
*representation* does not by itself unify *authority*.

A Function is a value: it may be bound to a name, passed as an argument,
returned, stored in a data structure, and compared with `==` under R18
identity rules (§15). It is never itself a module, a namespace, or a
mutable registry.

**[CHANGE FROM CURRENT IMPLEMENTATION — confirmed defect,
execution-verified]**: the ordinary leading-string-literal docstring
convention (`GENIA_STATE.md`, "named function definitions may include an
optional leading docstring string literal after `=`") is not currently
wired for R20's declaration path at all, even though `GENIA_STATE.md`'s
own R20 known-limitations bullet ("interface metadata beyond the optional
docstring position is a follow-up") affirmatively implies the leading-
docstring position itself works for `open`. The F1 decision report's item
7 confirms by direct execution and AST inspection that it does not:
`_parse_open_clause_list` (`src/genia/parser.py`) has no docstring
detection equivalent to ordinary `FuncDef` parsing's explicit check, so a
leading string literal is parsed as the clause's entire body, the intended
remaining body text is silently split off into an orphaned, unrelated
top-level statement, and `IrOpenFuncDef`'s `docstring` field is hardcoded
`None` in every parser path — dead code for the current grammar. This
fails **silently** into a corrupted two-statement parse (surfacing later
as a confusing "Undefined name" error at the orphaned statement) rather
than the clean rejection R20's own audit fixup achieved for the related
`@doc`-prefix-annotation case. A Function's metadata model (this section)
must be implemented uniformly for every Function regardless of whether it
was declared with or without any permission property (§26); this is
recorded as a required parity fix, not a new design choice, since the
convention itself (§1's Clause/Function metadata split) is already
correctly specified — only one declaration path's parser support is
missing.

## 3. What is Function origin identity?

Function origin identity is the same portable key R20 already defines
(R20 contract §2.1), generalized to every Function, not only ones
declared with a permission marker:

> the pair (declaring module's canonical module identity, the exported
> binding name in that module)

- For the entry/in-memory program, the canonical module identity is the
  deterministic `"<entry>"` id already produced by `Env.module_identity()`
  (`src/genia/environment.py`).
- A filesystem path, import alias, object address, allocation order, cache
  insertion order, or host hash is never part of this key, for the same
  reason R20 already excludes them: none of those are stable across
  re-execution, host, or import spelling.
- Two lexical aliases of the same cached module export are the same
  Function identity. Two modules exporting the same name are two different
  Function identities, even if their clauses are textually identical.
- Re-evaluating the same source unit in a new execution creates a new
  runtime value identity, consistent with R18, while retaining the same
  diagnostic/provenance key — this is an unchanged restatement of R20
  contract §2.1's last paragraph, now asserted for every Function, not only
  currently-open ones.

**[CHANGE FROM R20]**: today an *ordinary* function has no portable origin
identity distinct from its Python object identity — `GeniaFunctionGroup`
carries a `name` but no `module_id`/interface-key pair, and two ordinary
functions of the same name in different modules are distinguished only by
which lexical/module binding resolves to which Python object, not by an
explicit key. Unification requires giving every Function this same
`(module_identity, name)` key, purely as an added provenance/identity
field — it changes no dispatch behavior for a Function that is never
targeted by a ContributionUnit.

## 4. What is a ContributionUnit?

A **ContributionUnit** is exactly what R20 already calls a "contribution
unit" (R20 contract §4.1), generalized to name any Function's origin
identity as its target, not only ones already marked open:

- one contributing module's **inert**, externally declared, ordered list
  of Clauses;
- an explicit **target Function origin identity** (§3) — the pair
  (target module's canonical identity, target exported name) resolved
  through the *contributing* module's own lexical/import bindings, never
  through the alias spelling used to reach it (R20 contract §4.1's
  existing "resolved to the cached ModuleValue" rule, restated
  identity-first);
- its own **ContributionUnit identity**: the pair (declaring module's
  canonical identity, target Function origin identity) — never the
  contributing module's import alias for the target, and never a Python
  object address or export-key string. **[CHANGE FROM CURRENT
  IMPLEMENTATION]**: §19 records that this is a genuine implementation
  drift fix, not a restatement — see §19 and the F1 decision report's
  verified-divergence findings for items 1 and 2.

A ContributionUnit:

- **cannot mutate** its target Function, the target's declaring module, a
  process registry, or any already-constructed FunctionView (R20 contract
  §4.1, unchanged);
- produces **no callable value by itself** — it is inert declaration only,
  never directly invocable (R20 contract §4.1, unchanged);
- is **not activated by ordinary `import`** of its declaring module — an
  importer that never explicitly selects the unit into a FunctionView is
  completely unaffected by its existence (R20 contract §4.1/§9, unchanged);
  and
- closes over its own declaring module's lexical environment, never the
  target Function's declaring module's private environment and never any
  consumer/importer's environment (R20 contract §2.2, unchanged, restated
  for every ContributionUnit rather than only R20-era ones); and
- is **inaccessible to an importer except through an explicit selection
  operation** — R20 contract §4.2 states this plainly ("Private/non-
  exported contribution metadata is inaccessible").
  **[CHANGE FROM CURRENT IMPLEMENTATION — confirmed defect,
  execution-verified]**: this guarantee does not currently hold. A
  ContributionUnit is stored as an ordinary top-level binding in its
  declaring module's environment (the same `__open_contribution__
  <alias>__<name>` key described in §19/§20), and `Env.load_module`
  (`src/genia/environment.py`) exports **every** top-level binding of a
  module (`exports = dict(module_env.values)`) with no export/private
  distinction anywhere in the codebase — `ModuleValue.get_export`
  (`src/genia/values.py`) is a plain dict lookup with no name-based
  filtering. The F1 decision report's item 4 confirms by direct execution
  that an ordinary importer can read the raw `GeniaOpenContributionUnit`
  host value directly by ordinary named access
  (`ext.__open_contribution__base__get`), with **no `use`-equivalent
  operation at all** — bypassing the entire selection mechanism this
  contract's §5 requires to be the *only* way a ContributionUnit's Clauses
  ever become reachable. This shares its root cause with §19/§20's
  non-contiguous-accumulation defect (the same fixed, alias-spelling-keyed,
  ordinary-binding storage mechanism) and must be closed by the same fix:
  ContributionUnit storage must be a distinct, non-exported (or otherwise
  structurally inaccessible-by-ordinary-name-access) mechanism, keyed by
  structural identity (§4's own identity definition above), not an ordinary
  module-level binding reachable by guessing or deriving its mangled name.

Whether declaring a ContributionUnit against a given target Function
requires that Function to have granted permission is the central open
question this contract resolves in §26 — a ContributionUnit's own inertness
is not, by itself, an answer to that question (see §26.1 for why).

## 5. What is a FunctionView?

A **FunctionView** is exactly what R20 already calls a "linked view" (R20
contract §4.2), generalized to be the *only* mechanism by which more than
one participating unit's Clauses ever become jointly dispatchable:

- an **immutable** composition of exactly one Function (the "base unit")
  plus zero or more explicitly selected ContributionUnits, each targeting
  that same Function's origin identity;
- constructed once, by one explicit, declarative, non-executable operation
  that a host resolves after the constructing module's imports and
  declarations are available and before any ordinary top-level expression
  in that module can call the view — so no partially linked or temporally
  mutating view is ever observable (R20 contract §4.2, unchanged);
- bound to a name **in the constructing module only** — a FunctionView is
  not inherited process-globally by importers of that module; if a
  consumer wants to re-export its FunctionView, it does so as its own
  ordinary exported binding, which does not change the original Function's
  origin identity or implicitly grant selection rights to unrelated
  modules (R20 contract §4.2, unchanged);
- keyed by ContributionUnit identity for duplicate-selection detection,
  including through two lexical aliases of one cached module (R20 contract
  §4.2, unchanged); and
- **a value with the same origin identity as its base Function** for every
  purpose except dispatch participation: `FunctionView.interface_key ==
  base.interface_key` (already true of `GeniaLinkedOpenFunction
  .interface_key` today) — a FunctionView is not a new, separate Function
  identity; it is one particular immutable *composition* over an existing
  Function's identity. **This identity equivalence is the property §13
  requires the dispatch/TCO trampoline to use, and its current absence is
  the confirmed cause of the mutual/cross-function TCO defect recorded in
  §13 and the F1 decision report's item 5.**

A FunctionView with zero selected ContributionUnits is semantically
identical to calling the base Function directly — this is required for
"calling a Function" and "calling a FunctionView with an empty selection"
to be the same operation, which is what makes ordinary functions (which
today never have any FunctionView built over them) a degenerate case of
this same model rather than a separate species.

## 6. Exact dispatch algorithm

Given a callable target `T` (a Function called directly, or a FunctionView)
and `n` supplied arguments, dispatch is exactly the algorithm R20 contract
§5 already specifies, generalized to `T`'s participating-unit list, which
is `[T]`'s own local Clauses alone when `T` is a bare Function, or `[base,
contribution_1, ..., contribution_k]` when `T` is a FunctionView:

1. **Shape stratum.** If any participating Clause has fixed arity `n`,
   only fixed-arity-`n` Clauses across all participating units continue to
   step 2. Otherwise, collect every eligible varargs Clause (minimum arity
   ≤ `n`) across all participating units. If more than one distinct
   eligible varargs minimum exists, fail with deterministic varargs-shape
   ambiguity — never silently choose the largest minimum. If none is
   eligible, fail with no-matching-function.
2. **Unit-local selection.** Independently within each participating unit
   (the base unit, or one selected ContributionUnit), test that unit's
   surviving Clauses in lexical declaration order using the existing
   pattern/guard engine. At most the first matching Clause in each unit
   becomes that unit's candidate.
3. **Across-unit selection.** Exactly one unit supplying a candidate
   dispatches to it. More than one unit supplying a candidate is a
   deterministic clause-ambiguity failure — there is no specificity
   ranking, and neither ContributionUnit selection order nor import order
   can break the tie (§21/§22).
4. **Pattern miss.** No unit supplying a candidate is the existing
   no-matching-case diagnostic family for this Function's identity and
   argument count.

This is identical to R20 contract §5 verbatim, with "interface" replaced by
"Function" and "linked view" by "FunctionView." A bare Function (no
FunctionView constructed over it — the ordinary-function common case today)
is the `k = 0` instance of this same algorithm: exactly one participating
unit, so step 3 can never produce ambiguity from contributions, and the
whole algorithm degenerates to "test local Clauses in lexical order, first
match wins" — which is observably the same as today's ordinary
`GeniaFunctionGroup` dispatch (§7 explains the one place today's ordinary
dispatch differs in *representation*, not *outcome*, from this
generalization).

## 7. Fixed arity and varargs interaction

Unchanged from R20 contract §5 note and current ordinary-function behavior
(`GENIA_STATE.md` §4, "exact fixed arity beats varargs"): fixed-arity
Clauses of the calling arity always take priority over every varargs
Clause, regardless of which unit (base or contribution) declares them.
Multiple eligible varargs minimums are always an ambiguity failure, never a
largest-wins resolution.

**[CHANGE FROM CURRENT IMPLEMENTATION — confirmed defect, execution-verified]**:
today's *ordinary* multi-clause dispatch (`invoke_callable`'s
`_resolve_target` / `GeniaFunctionGroup.__call__`, `src/genia/callable.py`)
does **not** actually implement this rule the way open dispatch
(`_dispatch_open`) does, even though both claim to. Ordinary functions
*can* declare more than one varargs clause (`g(..rest) = rest` and
`g(a, ..rest) = [a, ..rest]` both parse and coexist) — the earlier
assumption that the grammar forbids this is wrong. The actual divergence is
a **dispatch shortcut**: ordinary resolution is keyed by a
`dict[int, GeniaFunction]` indexed by each clause's own fixed-param count,
and it returns `functions.get(call_arity)` **immediately, with no
ambiguity check at all**, whenever the call arity exactly equals some
varargs clause's own fixed-param count — it only falls through to the
varargs-ambiguity check when no clause's fixed-param count exactly equals
the call arity. Open dispatch has no such shortcut and always computes
eligibility from every clause's minimum arity uniformly, exactly per
contract §5.1. Confirmed by direct execution: for the two clauses above,
`open g(...)` raises `open-function-varargs-ambiguity` at `g(1)` (arity 1
exactly matches the second clause's own fixed-param count, but the first
clause's minimum-0 shape is also eligible), while the *ordinary* version of
the identical two clauses raises "Ambiguous function resolution" only at
`g(1, 2, 3)` — `g()` and `g(1)` both silently succeed via the dict
shortcut, using whichever clause's fixed-param count happens to equal the
call arity, without ever considering that a lower-minimum varargs clause
also matches. This is a genuine, reproducible, previously undisclosed
divergence, not a hypothetical — `GENIA_STATE.md` §4.7's "preserves current
fixed-over-varargs precedence" claim holds only for the fixed-vs-varargs
question, not for this varargs-vs-varargs question. The unified model's
requirement is to pick one behavior for every Function regardless of
whether it has ever had a ContributionUnit declared against it; this
contract proposes the open/contract-§5.1 behavior (uniform minimum-based
eligibility, no fixed-param-count shortcut) as the unified rule, since it
is the one the approved R20 contract already specifies in writing, and
records the alternative (keep today's ordinary shortcut) as an open
question for human review, since narrowing today's *ordinary* behavior is
an observable tightening for any currently-passing ordinary-function
program that happens to rely on the shortcut's silent success — unlike the
duplicate-clause question in §20, this tightening is not proven
inobservable and must be decided by the reviewer, not assumed.

## 8. Grouped-header binder scoping

A Clause's pattern bindings are scoped to that Clause's own guard and body
only — never to a sibling Clause, never to the Function's or
ContributionUnit's other Clauses, and never to the declaring module's
outer lexical scope beyond ordinary closure-over-declaration-environment
rules (§10). This is unchanged from both ordinary case-clause pattern
binding and R20 contract §3.2/§7.1.

A single Clause's header may bind more than one name (tuple/list/map
sub-pattern, `some(...)`/`err(...)`, named-pattern use) exactly as the
existing lambda-parameter pattern grammar already allows outside R20;
every bound name is visible in that Clause's own guard and body,
first-occurrence order determines alpha-normalization for duplicate-key
detection (§11, unchanged from R20 contract §6), and nothing else changes.

Where a *grouped* multi-arm `case`-with-`|` body is written as one
surface-level Clause "header" over several dispatch arms (today's grouped
open-declaration sugar), each `|`-arm's own pattern is the actual Clause
header for binder-scoping purposes — the outer grouped header binds
nothing beyond what R20 already restricts it to (plain-identifier headers
only, per the current implementation's `src/genia/parser.py` grouped-body
restriction). This contract does not widen that restriction; §2.1's
grouped/repeated-equivalence requirement is preserved unchanged, and F1
takes no position on whether a future release should lift the
plain-identifier-header restriction for grouped bodies — that is
independent of unification and out of scope here.

## 9. Guard behavior

Unchanged from current pattern/guard semantics for both species: an
optional guard expression follows a Clause's pattern, evaluated only after
the pattern itself matches, over exactly that Clause's own pattern
bindings, using existing boolean-truthiness rules. A guard that raises, or
that evaluates to a non-boolean value, follows whatever existing
diagnostic path ordinary case-guard evaluation already uses — this
contract adds no new guard-failure semantics. A Clause whose guard is
absent always matches once its pattern matches. Guards participate in
unit-local first-match selection (§6 step 2) exactly like pattern matching
does; a guard never influences across-unit ambiguity resolution (§6 step
3) beyond determining whether that unit produces a candidate at all.

## 10. Lexical environment behavior

Each Clause closes over its **declaring unit's declaring module's lexical
environment at declaration time** — never the caller's environment, never
a consumer FunctionView's constructing module's environment, and never
(for a ContributionUnit's Clauses) the target Function's declaring
module's private environment. This is R20 contract §2.2 verbatim,
generalized: it already describes ordinary closures today and requires no
behavior change for ordinary functions, only the explicit statement that
it is the same rule R20-contributed Clauses already follow.

Constructing a FunctionView changes no Clause's closure. Selecting a
ContributionUnit into a FunctionView does not re-parent, does not copy,
and does not re-close any Clause's environment — it only adds that unit's
already-closed Clauses to the participating-unit list used by dispatch
(§6). This is why FunctionView construction is inert (§26's "no lifecycle
activation" requirement, restated).

## 11. Outcome propagation and `none` behavior

A Function or FunctionView participates in the existing automatic
`none`-short-circuit and Outcome (`some(...)`/`err(...)`) handling exactly
as any other callable value does today, via the existing
`_callable_explicitly_handles_none`/`_some`/`_normalize_absence` mechanism
in `src/genia/callable.py`. This contract requires that mechanism apply
**identically** regardless of whether the callable is a bare Function or a
FunctionView, and regardless of which participating unit's Clause a given
argument pattern would need to explicitly handle `some`/`err`/`none` to
opt out of short-circuiting. **Confirmed by execution (F1 decision
report's item 10): this already holds today.** Both implicit `none`
short-circuiting and explicit `some(...)`/`none(...)`/`err(...)` header
handling produce byte-identical results for equivalent ordinary and open
clause sets — the none-awareness detection helper is not special-cased per
callable kind anywhere in `src/genia/callable.py`/`src/genia/evaluator.py`.
The only asymmetry found is a **syntax-surface** one, not a semantic one:
ordinary top-level *repeated*-clause headers (as opposed to the *first*/
`open`-equivalent clause header, and as opposed to lambda or `case`-arm
patterns, both of which already accept the full pattern grammar) do not
accept a constructor sub-pattern like `err(r)` directly and require the
grouped case-body spelling instead for that shape, whereas an
`open`/repeated open clause header accepts it directly per §1's pattern
grammar. This is a pre-existing parser asymmetry in how much of the
pattern grammar different top-level clause-header positions accept, not an
Outcome/`none` propagation difference, and this contract takes no position
on whether a future release should widen ordinary repeated-clause headers
to accept the same grammar `open` clause headers already do — that is
independent of unification (unifying dispatch/runtime semantics does not
require unifying every existing surface-parsing entry point) and is
recorded here only so it is not confused with a semantic Outcome bug.

Within dispatch (§6), a Clause whose pattern/guard evaluation itself
produces an Outcome failure (`PatternOutcomeError` in the current
implementation) short-circuits the *entire* dispatch for that call — not
just that one unit's candidacy — exactly as R20's `_dispatch_open` already
implements (`except PatternOutcomeError as exc: return exc.outcome`). This
is unchanged and generalized to every Function/FunctionView call.

## 12. Tail-call optimization behavior

TCO must be defined **once**, over Function origin identity and FunctionView
composition, not per runtime species. This is the single most important
correctness requirement this contract adds, because it is where today's
two-species split is independently confirmed (not merely suspected) to
produce different observable behavior — see the F1 decision report's item
5 and this document's own architecture note below.

**Required unified rule:** a tail call from any Clause body (base,
contributed, or ordinary) to any Function or FunctionView must be resolved,
before a trampoline decides whether to loop or recurse, down to the
concrete Clause selected by dispatch — never left as "call this opaque
callable object and let it manage its own internal loop." The trampoline
that drives repeated tail calls must be **one flat loop keyed by dispatch
target**, so that:

- self-recursion (a Clause's tail call resolves back to the same Function
  or FunctionView origin identity, however it was reached — directly, via
  a re-imported alias, or via a different local binding to the identical
  FunctionView composition) never grows the host call stack; and
- mutual recursion between two different Function/FunctionView origin
  identities never grows the host call stack either, for exactly the same
  reason ordinary same-species mutual recursion already does not grow the
  stack today (§12.1).

**[CHANGE FROM CURRENT IMPLEMENTATION — confirmed defect, not a
hypothesis]**: direct reading of `src/genia/callable.py` during this F1
pass shows the *current* implementation already satisfies this rule for
ordinary functions, but **does not** satisfy it for R20 open
functions/linked views, and the failure mode is exactly what issue #1010's
known-evidence list predicts ("open-function mutual/cross-function tail
calls can lose documented TCO"):

- `eval_with_tco`'s single while-loop (`src/genia/callable.py` around line
  298) special-cases `isinstance(current_fn, GeniaFunction)` inline. Every
  other callable kind falls to `result = current_fn(*current_args)` —an
  ordinary **Python call**, not a loop iteration.
- `invoke_callable` (same file, around line 1129) resolves a tail call
  through a `GeniaFunctionGroup` all the way down to the concrete
  `GeniaFunction` clause *before* returning `TailCall(target, args)` — so
  every ordinary-function tail call, including mutual recursion between two
  different named ordinary functions, becomes a bare `GeniaFunction` target
  that `eval_with_tco`'s single loop handles without ever recursing into
  itself. This is why ordinary mutual TCO already works.
- `GeniaOpenFunction.__call__` and `GeniaLinkedOpenFunction.__call__` (same
  file, around lines 683 and 717) each run their **own private** while-loop
  that only avoids growing the stack when `result.fn is self` — literal
  Python object identity of the exact `GeniaOpenFunction`/
  `GeniaLinkedOpenFunction` instance, not Function origin identity. Any
  tail call whose target is a *different* Python object — a different
  open-function instance (true mutual recursion between two open
  interfaces), or even the *same* logical interface reached through a
  different FunctionView object, or a plain tail call back out to an
  ordinary `GeniaFunction` — falls through to `return
  eval_with_tco(result.fn, result.args)`, which is a **new, nested Python
  call**, not a loop continuation. Each such bounce consumes one Python
  stack frame, so unboundedly deep mutual/cross recursion through open
  functions/FunctionViews will overflow the host stack at a depth
  determined by the host's recursion limit — independently of how many
  iterations the *documented* contract promises are TCO-safe.
- `docs/analysis/r20-release-truth-audit.md` §3's TCO reproduction only
  exercises **self**-recursion of one open function calling itself
  (200,000 iterations, `result.fn is self` true on every bounce) — it never
  exercises mutual recursion between two open interfaces, so the audit's
  "TCO preserved through open dispatch" claim is true for the case it
  tested and does not generalize to the case issue #1010 flags.

This confirms, independently of the F1 decision report's separately-run
execution evidence, that **the current two-species split is not merely a
style difference — it already produces a real, reproducible correctness
gap**, and that gap is exactly the kind of thing a "second callable
namespace/runtime species" (which R20's own required invariants forbid,
and which issue #1010 explicitly says the unified model must not
recreate) tends to produce: a fast path was written once for the original
species and never revisited when the second species was added on top.
Unifying dispatch and TCO onto one Function/FunctionView model, with one
trampoline loop keyed by resolved dispatch target rather than by Python
`is`-identity of a wrapper object, is a **requirement** this contract
places on any future design (§14), not an optional nicety.

### 12.1 Why ordinary mutual TCO already works (baseline, unchanged)

For completeness: ordinary named-function mutual recursion already loops
flat today because `invoke_callable`'s `GeniaFunctionGroup` branch always
resolves the *specific arity's* `GeniaFunction` before constructing a
`TailCall`, and `eval_with_tco`'s loop special-cases exactly that concrete
type. The unified model's requirement is to give Functions/FunctionViews
the same property — resolve to the concrete selected Clause's execution
frame before handing back a `TailCall`, not to hand back "the callable
object, please call it and manage your own loop."

## 13. Recursion from a FunctionView

A tail or non-tail call from a Clause body to the name the FunctionView
itself is bound under resolves to **that exact FunctionView's own
participating-unit set** — dispatch re-runs the full algorithm (§6) over
`[base, contribution_1, ..., contribution_k]` on every recursive call, not
just over the base unit. This matches current `GeniaLinkedOpenFunction
.__call__`'s behavior (it dispatches through `self._dispatch_once`, which
uses `self.units` on every call) and is unchanged by this contract.

A recursive call from a **base Function's own Clause** to its own name
(not through any FunctionView) resolves to the base Function alone — it
never implicitly "sees" any FunctionView some other module happened to
construct over it, even if that FunctionView is, at the moment of the
recursive call, already fully constructed elsewhere in the running
program. A Function's own recursive self-reference is always base-only
unless that Function's own declaring module itself explicitly constructs
and calls through a FunctionView — this preserves R20's "no implicit
extension from ordinary import" invariant at the recursion boundary, not
only at first-call boundary.

## 14. Mutual recursion

Mutual recursion between two different Function/FunctionView origin
identities must use the same unified trampoline described in §12 — see
§12's required rule and confirmed current-implementation gap. Semantically
(independent of the TCO stack-growth question), mutual recursion between
two Functions/FunctionViews dispatches each call independently: Function A
calling Function B's FunctionView uses A's own participating units for A's
own dispatch and B's FunctionView's participating units for B's dispatch —
there is no shared or merged unit list between mutually recursive
Functions, and no ordering relationship between them beyond ordinary call
sequencing.

## 15. Aliases and Function identity

Two lexical aliases of the same cached module's export of the same name
are the **same** Function origin identity — this is unchanged from R20
contract §2.1 ("Two aliases of the same cached module export refer to the
same interface") generalized to every Function. `import base as b1` and
`import base as b2` in the same or different modules both resolve
`b1.f`/`b2.f` to one Function identity; `f(...)==f(...)` under R18 equality
reflects that shared identity, and a diagnostic naming that Function must
name it once, not once per alias spelling used to reach it.

**Empirically tested aliasing scenarios are correct today.** The F1
decision report's item 1 independently executed the most natural aliasing
scenarios this contract's §3 identity rule governs — two aliases of the
same base module in one *consuming* module (`import base as b1` /
`import base as b2`), selecting a contribution through either alias, and
the existing `test_alias_identity_two_aliases_of_the_same_module_are_one_
interface` / `test_duplicate_selection_through_two_aliases_of_one_cached_
module_is_rejected` regression tests — and found **no loss or
duplication** in any of them: `use`/selection resolves aliases through
ordinary lexical lookup to the one shared cached `ModuleValue`, exactly as
§3/R20 contract §2.1 require. That part of issue #1010's aliasing concern
is **not reproduced** against current `main`.

**[CHANGE FROM CURRENT IMPLEMENTATION — confirmed defect, narrower
scenario, found by direct code reading]**: a *different*, untested-by-
execution aliasing scenario still violates this contract's identity
requirement, and it shares its root cause with the confirmed §19/§20
non-contiguous-`extend` and leaked-binding defects. `IrOpenContribution`
evaluation (`src/genia/evaluator.py`, the `isinstance(node,
IrOpenContribution)` branch) computes its module-export storage key as
`f"__open_contribution__{node.target_module_alias}__{node.target_name}"` —
using the **contributing module's own alias spelling for the target**, not
the resolved target Function's origin identity. If a single *contributing*
module imports the same target module under two different local aliases
(`import base as b1`, `import base as b2`) and writes `extend b1.get(...)
= ...` and `extend b2.get(...) = ...` for what is structurally the *same*
target interface, the two `extend` blocks produce **two separate, non-
colliding export keys** (`__open_contribution__b1__get` and
`__open_contribution__b2__get`), both holding a `GeniaOpenContributionUnit`
whose `target_interface_key` is identical. `Evaluator
._find_open_contribution_unit` (`src/genia/evaluator.py`) then iterates
`module_value.exports.values()` and returns only the **first** match by
Python dict-iteration order — silently ignoring the other alias's
contributed Clauses, with no duplicate/redeclaration diagnostic, whenever a
consumer's `use` later selects that contributing module. This is a real,
code-confirmed instance of the same underlying defect §19/§20 describe
(export storage keyed by alias/import spelling rather than by the
structural identity §4 already requires); it was not the specific scenario
the F1 decision report's execution-based item 1 targeted, so it should be
read as a *distinct, narrower* confirmed finding, not as contradicting item
1's "not reproduced" verdict for the scenarios that report actually ran.
The unified model's requirement is unchanged either way: ContributionUnit
storage/lookup must be keyed by the same **structural**
`(declaring_module_identity, target_interface_key)` pair this contract
already defines in §4, never by any alias spelling, on either the
contributing or the consuming side — this is a correctness requirement for
any future implementation, not a new design choice.

## 16. Imports and Function identity

Ordinary `import` binds a module value and evaluates that module under
existing module rules; it never changes, creates, or removes a Function
identity, and it never, by itself, selects any ContributionUnit (§26). This
is unchanged from R20 contract §4.1 and ordinary import semantics.

## 17. Re-exports and Function identity

A module that re-exports a Function it imported (binds an ordinary local
name to an imported Function value and exports that local name) does not
create a new Function origin identity — the re-exported binding still
resolves, under §3's identity rule, to the *original* declaring module's
`(module_identity, name)` pair, because origin identity is a property of
the Function value itself (carried on the value, per §3), not of whichever
binding currently points at it. A re-exporting module may itself become
the target module alias other modules use to reach that Function, but
`extend`ing through the re-exporting module's alias must still resolve
`ContributionUnit`'s target key to the *original* Function's identity, not
to a fresh identity keyed off the re-exporting module — this is a direct
consequence of §3's rule that alias spelling and file path are never part
of the key, and requires no new mechanism beyond correctly applying §3.

## 18. Does wrapping create a new Function identity?

Yes, unconditionally, and this is unchanged by unification. Any operation
that produces a genuinely new callable value not returned unchanged by the
declaring module's own declaration operation — an ordinary lambda closing
over a Function, a partial-application helper, a decorator-style wrapper
function — produces a value with **no** Function origin identity under
§3's definition (it has no `(module_identity, name)` key derived from an
`open`/Function declaration; it is an ordinary closure value). Such a
wrapper cannot be the target of a ContributionUnit (§4 requires resolving
to an actual Function origin identity; wrapping does not preserve or
forward one), and calling it does not dispatch through §6's algorithm
unless the wrapper itself, internally, calls a Function/FunctionView.

## 19. How ContributionUnits are identified and ordered

- **Identity** (§4, restated): `(declaring module's canonical identity,
  target Function origin identity)`. Two ContributionUnits with the same
  identity, from the same declaring module, targeting the same Function,
  are the same unit — see §15 for the confirmed current-implementation gap
  that must be closed so lookup actually honors this.
- **Ordering within a unit**: lexical declaration order of its Clauses,
  exactly as a Function's own local Clauses are ordered (§2). Repeated
  `extend`-equivalent statements for the same target, in the same
  contributing module, accumulate into one unit's Clause list in source
  order — unchanged from R20 contract §3.1/§4.1.
- **Ordering across units in a FunctionView**: none. §6 step 3's
  across-unit ambiguity rule already establishes that no total order over
  participating units exists or is needed for correctness; any stable
  ordering used for diagnostics/introspection (§25) is for display only
  and must never be allowed to resolve an ambiguity (R20 contract §4.3,
  unchanged).

**Non-contiguous accumulation [gap requiring resolution]**: the current
implementation's parser only merges a contiguous run of top-level
`extend`-equivalent statements for the same target into one AST-level
unit (`src/genia/parser.py`'s `_merge_open_toplevel`, and the syntax/IR
design doc's explicit "Contiguity restriction," §4). When a later,
non-contiguous resumption occurs, the syntax/IR design document promises
"a rejected redeclaration-like error, not a silent second interface." The
F1 decision report's item 2 records that, for the **base** (`open`)
declaration case, the current implementation does deliver exactly that
promised rejection (`Evaluator`'s `IrOpenFuncDef` branch explicitly checks
`if node.name in self.env.values: raise OpenFunctionRedeclarationError`
before binding). For the **contribution** (`extend`) case, however, direct
reading of `Evaluator`'s `IrOpenContribution` branch
(`src/genia/evaluator.py`) shows no equivalent guard: it unconditionally
calls `self.env.set(export_name, unit, assignable=False)`, and
`Env.set` (`src/genia/environment.py`) unconditionally overwrites
`self.values[name]` with no prior-binding check at all. A second,
non-contiguous `IrOpenContribution` node for the same target therefore
**silently replaces** the first `GeniaOpenContributionUnit` value under the
same export key — the first run's Clauses are lost with **no diagnostic
whatsoever**, which is a strictly worse outcome than either the promised
rejection or a silent-second-interface outcome, because it is silent data
loss rather than a silent duplication. This is exactly the "non-contiguous
extend runs losing ContributionUnits" finding issue #1010 asks F1 to
verify, and it is independently confirmed by direct code reading (see the
F1 decision report for the accompanying execution-based reproduction). The
unified model's requirement is symmetric with the already-correct base
case: **every** non-contiguous resumption of Clause accumulation for the
same Function-or-ContributionUnit target, whether base or contribution,
must be a deterministic, diagnosed rejection — never silent loss and never
silent duplication.

## 20. Duplicate contributions

Two ContributionUnits with the same identity (§19) selected into the same
FunctionView is a deterministic duplicate-selection failure, including
through two lexical aliases of one cached contributing module — unchanged
from R20 contract §4.2. This requires §15/§19's identity-not-alias-spelling
fix to be reliable in the presence of the confirmed aliasing gap; until
that gap is closed, duplicate-selection detection can itself be unreliable
(if two alias-keyed exports of "the same" unit are visible under different
export names, a consumer selecting both could either double-count Clauses
or trip an unrelated incompatible-contribution error instead of the
intended duplicate-selection error — the F1 decision report records which
of these the current implementation actually does).

Two Clauses with the same structural, alpha-normalized, span-free dispatch
key **within the same unit** (base or one contribution) are a
build-time duplicate-clause failure, detected once when the unit is built,
never deferred to call time — unchanged from R20 contract §6, generalized
to every Function's base unit (today, an *ordinary* function has no
equivalent build-time structural duplicate check; `GeniaFunctionGroup
.add_clause` only rejects a second clause of the *same arity*, not a
second clause with an identical dispatch key at a *different* arity that
happens to be unreachable, nor identical guards — a narrower check than
R20's. Unification requires deciding whether ordinary functions gain R20's
stricter structural check, which this contract recommends as the unified
rule for consistency, recorded as an open question for human review in the
F1 decision report rather than silently assumed.).

The same dispatch key in **different** units is never a build-time
duplicate — separately authored guards/patterns may be intentionally
disjoint only at runtime; if both match one call, §6 step 3's across-unit
ambiguity rule applies. Unchanged from R20 contract §6.

## 21. Ambiguity determination

Ambiguity is determined **structurally and deterministically**, never by
import order, ContributionUnit selection order, or any specificity/priority
ranking:

- **varargs-shape ambiguity** (§6 step 1): more than one distinct eligible
  varargs minimum arity across all participating units.
- **clause ambiguity** (§6 step 3): more than one participating unit
  supplies a first-match candidate for the same call.

Both are unchanged from R20 contract §5, generalized to every
Function/FunctionView. Neither ambiguity check inspects which unit is the
base versus a contribution — the base unit participates exactly like any
other unit, so a foreign Clause overlapping a matching base Clause is
ambiguous by the same rule as two contributions overlapping each other
(R20 contract §5, "the base unit participates exactly like one unit,"
unchanged).

## 22. Can contribution selection order change successful dispatch?

No. This is a required invariant (§26), not merely current behavior. Per
§6, the participating-unit list's *order* is irrelevant to which unit
supplies a candidate (each unit is tested independently; ambiguity is
determined by *how many* units produce a candidate, not by which one is
listed first) and irrelevant to which Clause within a unit is selected
(unit-local order is fixed at declaration time by lexical Clause order,
never by selection order). Changing the order in which ContributionUnits
are named in a FunctionView-construction operation, or changing unrelated
import order, cannot change a successful dispatch's result — unchanged
from R20 contract §4.3, restated as a hard requirement for the unified
model (this is one of the required R20 invariants §26 maps explicitly).

## 23. Provenance preservation

Every Clause record retains, immutably, through export/aliasing/linking/
recursive calls: Function-or-ContributionUnit identity (§3/§4), base-versus-
contribution role, declaring module/source-unit identity, source span
(filename/source label, start/end line/column), fixed/varargs shape and
arity/minimum, and lexical ordinal within its owning unit — unchanged from
R20 contract §7.1, generalized to every Clause of every Function, not only
currently-open ones. Portable diagnostics render this using the semantic
module/source identity and normalized span; host object addresses,
exception text, unordered-map iteration artifacts, absolute path
accidents, and protected payloads must never appear (R20 contract §8,
unchanged).

Interface-level metadata (`@doc`, category, stability, deprecation)
belongs to the Function alone; a ContributionUnit's Clauses can never
supply, replace, merge, or erase it — unchanged from R20 contract §7.2.

## 24. Module boundaries and environment leakage

Two independent guarantees, both required, and the second is **currently
violated** per confirmed reading of the implementation:

1. **No module sees another module's private top-level bindings merely by
   being imported or by declaring/selecting a ContributionUnit against
   it.** A ContributionUnit's Clauses close over their own declaring
   module's environment (§10); constructing a FunctionView does not expose
   any participating unit's private environment to the constructing
   module or to any other participating unit. This part is unchanged from
   R20 contract §2.2/§4.2 and is not, per this session's reading, currently
   violated for R20-specific mechanisms.

2. **No loaded module sees the entry/in-memory program's own top-level
   bindings merely because a module was loaded from that program.**
   **[CHANGE FROM CURRENT IMPLEMENTATION — confirmed defect, pre-existing
   and not R20-specific]**: direct reading of `Env.load_module`
   (`src/genia/environment.py`) shows that a freshly loaded module's
   environment is constructed as `Env(root, rebind_parent=False)`, where
   `root = self.root()` is the **same** environment object the entry
   program's own top-level code runs directly against (`make_global_env()`
   in `src/genia/builtins.py` returns one `Env()` that both holds every
   builtin binding *and* is the exact environment `run_source` evaluates
   the entry program's top-level statements into — there is no separate
   child frame for the entry program). Because `Env.get` (`src/genia/
   environment.py`) walks the `parent` chain unconditionally on every
   lookup miss, and `rebind_parent=False` only prevents *assignment* from
   writing back into `root` (consistent with `GENIA_STATE.md` §4's
   documented "module top-level assignment does not rebind names in the
   importing root environment"), a **name lookup** inside a loaded
   module's top-level code that isn't found in that module's own
   `values` **does** fall through to the entry program's `root.values` —
   which includes every top-level name the entry program itself defines,
   not only builtins. This means an entry program can define a name and
   have every module it imports silently observe that name if the module
   itself never happens to shadow it — a real module-isolation leak,
   independent of R20, that the F1 decision report's item 8 records with
   an execution-based reproduction. The unified model's requirement is
   that a loaded module's environment chain must terminate at a shared
   **builtins-only** root, never at the entry program's own top-level
   frame; this requires separating "the builtins root" from "the entry
   program's top-level frame" as two distinct environments, which is a
   pre-existing module-system defect this contract surfaces but does not
   itself redesign (module-visibility redesign beyond what the permission
   analysis proves necessary is explicitly out of scope for issue #1010).

## 25. Diagnostics: base versus contributed clauses

Every diagnostic that names a specific Clause or unit (duplicate-clause,
clause-ambiguity, varargs-shape-ambiguity, no-matching-case) must be able
to state, using the provenance each Clause always carries (§23), whether
the implicated Clause(s) came from the base unit or from a named
ContributionUnit, and which declaring module produced a contribution —
unchanged from R20 contract §8's existing diagnostic identity list,
generalized so the same diagnostic identities (renamed only if a future F2
renames the underlying concept, never renamed by this contract) apply
uniformly whether the Function in question has ever had a ContributionUnit
declared against it or not. `help(Function-or-FunctionView)` lists the base
unit first, then each contribution unit ordered by declaring-module
identity (a stable, informational-only ordering — never a dispatch-order
implication, per §21), Clauses within a unit by lexical ordinal — unchanged
from R20 contract §7.3.

---

## 26. Critical architectural decision: permission vs. composition authority

Issue #1010 requires this question be answered explicitly, before any
surface syntax is chosen:

> Does a Function need to grant permission to be the target of an inert
> ContributionUnit when that contribution cannot affect the Function, its
> defining module, or ordinary importers unless a consumer explicitly
> constructs/selects a FunctionView containing it?

### 26.1 Why ContributionUnit inertness does not, by itself, answer this

It is tempting to reason: "a ContributionUnit can't do anything until a
consumer builds a FunctionView, and building a FunctionView is itself
explicit, so no permission is needed — composition IS the authority
boundary." This is Model B's argument, and it is *coherent*, but it is not
automatically implied by inertness alone. The reason it needs its own
analysis is that "cannot affect the Function" is a claim about **runtime
effects**, while permission is a question about **declaration-time
authority over meaning** — specifically:

- **API-surface commitment.** A Function's author may have written it
  as a closed, exhaustively-reasoned-about decision procedure (this is
  exactly what closed shapes and closed pattern matching mean elsewhere in
  Genia's core-surface-freeze philosophy — see `AGENTS.md`'s "Core Surface
  Freeze" section: closed matching is a deliberate design tool for
  reasoning about totality, not an accident). Even if no FunctionView is
  ever built, the mere fact that Clauses *can* be declared against a
  Function's identity from anywhere in the dependency graph is itself an
  API commitment the author did not necessarily make — it constrains what
  the author can assume about their own Function's identity being
  "closed" for reasoning purposes, and it is a commitment made the moment
  the Function is declared, not the moment a FunctionView is built.
- **Namespace/identity pollution, independent of runtime effect.**
  `open-function-target-not-open`-equivalent errors exist today
  specifically so that `extend`ing a name that was never meant to be
  extended fails immediately and loudly rather than silently succeeding
  and only mattering if someone later builds a view. Removing the
  permission bit removes this **fail-fast at the point of the mistaken
  `extend`**, pushing the earliest possible diagnostic from
  ContributionUnit-declaration time to FunctionView-construction time (in
  Model B) or making it never fail at all for a Function whose author
  never anticipated contribution.
- **This is not the same question as whether the mechanism is safe.**
  R20's required invariants (no global registry, no import-order effect,
  explicit composition) are about *safety of the mechanism once used*.
  The permission question is about *whether every Function's author
  implicitly opts into being a legal `extend` target merely by existing as
  an exported, pattern-dispatched Function* — a question about default
  authorial intent, not mechanism safety. A mechanism can be perfectly
  safe (Model B is) and still be judged to violate an author's reasonable
  expectation of closed-by-default semantics (which is Model A's
  argument).

### 26.2 Model A — Explicit permission

A Function must explicitly declare itself externally contributable at
Function-declaration time (surface spelling out of scope, per issue
#1010). Absent that declaration, `extend`-equivalent statements targeting
it fail immediately, at ContributionUnit-declaration time, with a
diagnostic naming the target Function as not contributable — this is
exactly today's R20 behavior, generalized: `open-function-target-not-open`
already fires today for *any* non-open target, including an ordinary
closed function.

**Arguments for:**
- Preserves closed-by-default reasoning for every ordinary Function,
  consistent with Genia's broader closed-by-default philosophy (closed
  shapes, closed pattern matching — `AGENTS.md` Core Surface Freeze;
  `docs/design/03-closed-shapes.md`).
- Fails fast, at the point of the mistake, rather than only at
  FunctionView-construction time or never.
- Matches current, audited (`docs/analysis/r20-release-truth-audit.md`),
  PASS-verdict R20 behavior exactly — zero behavior change for any
  currently-passing program, since every currently-open Function was
  already explicitly declared open and every ordinary Function was
  already correctly rejected as a target.
- Keeps "which Functions can ever be contributed to" a statically
  discoverable, per-Function property, useful for tooling/documentation
  generation (`tools/gen_function_docs.py`-style introspection) without
  needing to scan the whole dependency graph for every `extend` statement
  that might exist anywhere.

**Arguments against:**
- Requires every Function author to anticipate contribution in advance,
  which does not fit every legitimate extension scenario (a Function the
  original author never anticipated being extended, but whose owner later
  — possibly the same author, possibly a maintainer with write access to
  the declaring module — is happy to allow it, still requires editing and
  redeploying the *declaring* module merely to flip a permission bit,
  even though the actual new behavior lives entirely in the contributing
  module).
- Is, in a literal sense, "recreating `open` under another marker" if the
  unified model still requires a spelled-out permission property — exactly
  risk #2 in issue #1010's own "Risk of drift" section. This contract does
  not itself choose a spelling (§0.2), but Model A does commit F2 to
  choosing *some* spelling for this property, which is a real, disclosed
  cost of this model, not a free preservation of the status quo.
- Two Function "flavors" (permission-granted vs. not) still exist as a
  visible property of Function declarations, even though both flavors
  share one runtime species (§2) — this is a smaller version of the
  "second species" problem R20's invariants warn against, moved from the
  *runtime* layer (where R20 already has it today: `GeniaFunction` vs.
  `GeniaOpenFunction`) to the *declaration* layer (a boolean property on
  one unified Function type). It is a real reduction in complexity
  relative to today, but not a complete elimination of the two-flavor
  distinction issue #1010 asks F1 to seriously consider removing.

### 26.3 Model B — Composition is the authority boundary

Any otherwise-resolvable Function (any exported, pattern-dispatched
Function whose origin identity can be named) may be named as the target of
an inert ContributionUnit. This has no semantic effect on the Function, its
defining module, or ordinary importers unless and until a consumer
explicitly constructs a FunctionView selecting that unit — and only within
that consumer's own module (§5's "bound in the constructing module only").

**Arguments for:**
- Removes an entire category of declaration — no permission property, no
  spelling to choose, no "why do I need to mark this open just to let one
  downstream module optionally extend it" friction.
- Matches the issue's own instinct, stated plainly in the critical-decision
  question itself: since a ContributionUnit is already proven inert and a
  FunctionView is already proven to be consumer-local and explicit, the
  *composition* operation is arguably already doing all the authority work
  a permission bit would add — nothing observable changes for a Function's
  author or its ordinary importers unless *they themselves* write the
  `use`-equivalent statement.
- Is the more aggressive simplification consistent with "the unified
  Function model must not create a second callable namespace or runtime
  species merely to support contribution" (issue #1010's own closing
  requirement) — Model B removes not only the second runtime species (§2
  already does that under either model) but also the second declaration
  flavor.

**Arguments against:**
- Loses the fail-fast diagnostic at ContributionUnit-declaration time for
  a Function whose author genuinely never wanted it extended — the
  earliest a mistake surfaces is FunctionView-construction time (if the
  target Function's declaring module later, deliberately, adds a
  guard against being a target — but Model B by definition provides no
  such guard) or, in the fully permissive reading, never, because nothing
  ever rejects the `extend` itself.
- Weakens closed-by-default reasoning for *every* Function, including ones
  the author explicitly designed as closed and exhaustive — under Model B,
  "is this Function ever contributed to" becomes a whole-program question
  (did any module, anywhere, ever declare a ContributionUnit against it
  and did any module, anywhere, ever select it?), not a locally-answerable
  one, even though *dispatch* itself stays local to whichever module
  actually calls through a FunctionView. This does not weaken any R20
  invariant (no global registry, no import-order effect — Model B keeps
  both), but it does weaken a property this contract's own §26.1 argues is
  independently valuable: authorial closed-by-default commitment.
- A later audit/reviewer cannot distinguish, by reading only the
  Function's own declaration, "this Function is closed and no one has ever
  attempted to extend it" from "this Function is closed and someone,
  somewhere in the dependency graph, already has a ContributionUnit
  targeting it that merely hasn't been selected into any FunctionView
  yet" — both look identical from the declaring module. Model A's
  permission bit at least makes "contribution is possible in principle"
  locally visible even when no contribution has actually been written.

### 26.4 Model C — narrower alternative

This session found no independently-verified evidence (from the
implementation, from GENIA_STATE.md, from the R20 contract, or from any
recoverable investigation — see F0) that justifies a third model distinct
from A and B along a genuinely new axis. Two narrower variants were
considered and are recorded here as **not proposed**, with reasons:

- *Opt-out rather than opt-in* (every Function is contributable by default
  unless explicitly marked closed) was considered and rejected as a
  candidate: it inverts Model A's fail-fast benefit onto a "silent unless
  you remembered to close it" default, which is a strictly worse default
  than either A or B for a language whose stated philosophy elsewhere
  favors closed-by-default reasoning (`docs/design/03-closed-shapes.md`).
  It is not recommended as Model C; it is recorded only so the option is
  shown to have been considered rather than silently omitted.
- *Per-ContributionUnit acknowledgment* (the target Function stays
  permission-free, but each `extend` site must itself carry some
  acknowledgment that it targets a Function that did not ask for it) was
  considered and rejected as a candidate: it does not change the
  authority boundary at all (the ContributionUnit's own author already
  necessarily writes the `extend`-equivalent statement deliberately), it
  only adds ceremony to something already deliberate, and it does nothing
  §26.1's actual concerns (author's closed-by-default expectation,
  fail-fast timing) that Model A does not already do better.

No Model C is proposed. The decision in §26.5 is between A and B only.

### 26.5 Selected model and rationale

**This contract recommends Model A (explicit permission), as a proposal
for human review — not yet approved.**

Rationale, weighing §26.2/§26.3 against the required invariants (§27) and
against `AGENTS.md`'s core-surface-freeze philosophy:

1. **Zero behavior change for currently-passing programs.** Model A is,
   by construction, exactly what R20 already implements and what the
   PASS-verdict audit already verified end-to-end. Model B is a genuine
   *widening* of which Functions can be legally targeted (every ordinary
   Function becomes a legal target the instant unification ships, with no
   action from that Function's author), which is new externally-observable
   surface area that did not exist before, even though its *runtime*
   effect remains gated by explicit FunctionView construction. Given
   `AGENTS.md`'s repeated emphasis on minimal, non-speculative change and
   the rejection criteria in its Core Surface Freeze section ("adds syntax
   without increasing clarity" / "expands the surface area without
   strengthening the core model"), a model that requires no new default
   widening is the safer default to recommend, with Model B available as
   a deliberate, separately-justified future loosening if the project
   later decides the friction Model A imposes is not worth its benefit.
2. **Closed-by-default reasoning is a load-bearing Genia value, not
   incidental.** Genia already treats "closed" as a first-class, deliberate
   design choice distinct from "open" elsewhere in the value-template
   system (closed shapes vs. open shapes, `docs/design/02-open-shapes.md`
   / `docs/design/03-closed-shapes.md`). Extending that same
   closed-by-default posture to Functions — "a Function is closed to
   external contribution unless its author says otherwise" — is more
   consistent with the rest of the language's design vocabulary than
   introducing, for Functions specifically, an open-by-default posture
   that has no analogue anywhere else in the value-template/pattern
   system.
3. **The "recreates `open` under another marker" risk is real but
   acceptable, because the marker is now smaller and better-justified.**
   Issue #1010 itself distinguishes "treating a surface rename as the
   architecture fix" (bad) from "settling whether the permission bit is
   necessary and then choosing its spelling" (the actual required
   process). This contract's recommendation is not a surface rename — it
   is a considered judgment, made after weighing Model B seriously (§26.3
   gives Model B a real, non-strawman case), that the permission property
   is semantically load-bearing for reasons independent of mechanism
   safety (§26.1). F2 remains free to spell it however minimally the
   language's soft-keyword conventions prefer, including reusing existing
   vocabulary rather than inventing new words — that is explicitly F2's
   job, not this document's.
4. **This is a recommendation, not a foreclosed decision.** Human review
   at the F1 gate may weigh §26.2/§26.3 differently — in particular, a
   reviewer who judges "no behavior change" (point 1) as less important
   than "eliminate the declaration-layer species distinction entirely"
   (Model B's strongest argument) has a legitimate basis to select Model B
   instead. Both models satisfy every required invariant in §27; neither
   is disqualified by this analysis. The F1 decision report (companion
   document) restates this as an open decision for the reviewer, not a
   fait accompli.

---

## 27. Required invariant mapping (R20 invariants, preserved by construction)

| R20 invariant | How this contract preserves it |
|---|---|
| No global mutable dispatch registry | §2/§4/§5: Functions, ContributionUnits, and FunctionViews are values constructed once from Core IR at declaration/link time; no process-global table is introduced anywhere in this contract. |
| Contribution declarations are inert | §4, restated verbatim from R20 contract §4.1; §26.1 explains why inertness is necessary but not sufficient for the permission question, which §26 answers separately. |
| Ordinary import does not activate contributions | §16, unchanged from R20 contract §4.1. |
| Explicit composition controls participation | §5/§6: only an explicitly constructed FunctionView ever has more than one participating unit; a bare Function always dispatches over its own local Clauses alone. |
| Composed views are immutable | §5, unchanged from R20 contract §4.2. |
| Import order does not determine successful dispatch | §22, elevated from R20's description of current behavior to a required invariant of the unified model. |
| Contribution selection order does not determine successful dispatch | §22, same elevation. |
| Deterministic ambiguity detection | §21, unchanged algorithm, generalized to every Function/FunctionView. |
| Provenance survives composition | §23, unchanged from R20 contract §7.1, generalized to every Clause. |
| Module isolation | §24: guarantee (1) is preserved and, per this session's reading, not currently violated for R20 mechanisms specifically; guarantee (2) is a **confirmed pre-existing violation** this contract surfaces as a requirement for the unified model to close, not a new invariant it weakens. |
| Cross-host representability | §14 (Core IR requirements) carries forward R20 contract §10/§11's host-independence obligations unchanged, generalized to every Function/Clause/ContributionUnit/FunctionView. |
| No second callable namespace/runtime species | §2, the central unification move: one Function runtime species replaces `GeniaFunction`/`GeniaFunctionGroup`/`GeniaOpenFunction`/`GeniaLinkedOpenFunction`'s current four-type split with one Function type plus one FunctionView composition type (a FunctionView is not a second *Function* species — see §5's identity-equivalence requirement). Model A (§26.5) reintroduces exactly one boolean declaration-time property, not a second species; Model B reintroduces none. |

---

## 28. Semantic requirements for Core IR (not a redesign)

This contract does not choose Core IR node names, fields, or lowering
strategy (`AGENTS.md`: "Do not redesign Core IR yet"; issue #1010: "Do not
let current names such as `IrOpenFuncDef` force the semantic model"). It
records what a future F3 Core IR design must be able to represent, host-
independently, without a host-side table:

1. **Function origin identity** (§3): derivable structurally from
   declaring-module-tree membership plus exported binding name — no new
   identity-carrying field beyond what R20's existing IR nodes already
   avoid needing (R20 contract §10 note 3, generalized).
2. **Ordered Clauses** (§1/§2) for every Function, not only currently-open
   ones — meaning every ordinary function's single implicit clause (today
   represented by plain `IrFuncDef`) must be representable as one member
   of an ordered Clause list with the same provenance shape a
   currently-open Function's clauses already have, without requiring
   every ordinary function to carry R20's full mechanism weight if F3
   later decides a lighter-weight representation is possible for the
   common single-clause, non-contributable case. This contract takes no
   position on whether that means literally reusing `IrOpenFuncDef`'s
   shape for every function or introducing one shared "Function
   declaration" IR family that both the current `IrFuncDef` case and the
   current `IrOpenFuncDef` case lower to — that choice belongs to F3.
3. **ContributionUnit identity and provenance** (§4/§19): structural
   `(declaring_module_identity, target_interface_key)`, resolved through
   the contributing module's own import/lexical table at link time —
   never an alias-spelling-keyed storage mechanism (§15/§19's confirmed
   defect is specifically an *implementation* bug in how the current
   runtime keys contribution storage, not a flaw in R20's Core IR design
   itself; F3 must ensure whatever storage mechanism F5 implements keys by
   this structural identity, whether or not the Core IR node shape itself
   changes).
4. **FunctionView composition** (§5): one base Function reference plus an
   ordered-for-determinism-but-not-for-dispatch list of selected
   ContributionUnit references, with the identity-equivalence property
   §5 requires (`view.interface_key == base.interface_key`) representable
   without a host object address.
5. **Module references**: every module reference used to resolve a target
   (declaring module of a Function, declaring module of a
   ContributionUnit, target module alias resolution for both `extend`-
   equivalent and `use`-equivalent operations) must resolve through the
   same canonical module-identity mechanism `Env.load_module`/
   `module_identity()` already provides — no new module-identity
   mechanism is introduced.
6. **Deterministic dispatch information**: each Clause's derived
   fixed/varargs shape (§1, never stored redundantly — always derived from
   the pattern) and lexical ordinal (§1, the Clause's list-index position,
   never a separately stored field) — unchanged from R20 contract §10.
7. **Any permission property that survives F1** (§26): if Model A is
   approved, F3 must represent one boolean-or-equivalent property on a
   Function's declaration, immutable after declaration, with no
   inference from later foreign contribution (R20 contract §2.2's
   existing "openness must be declared, never inferred from a later
   foreign contribution" rule, generalized). If Model B is approved, F3
   introduces no such property at all, and every Function is uniformly a
   legal ContributionUnit target by construction.

No existing closed `IrFuncDef`-equivalent representation is required to
disappear merely because this contract exists; F3 is free to keep a
lighter-weight representation for the common non-contributable case, so
long as it is provably equivalent, for dispatch/TCO/Outcome purposes
(§6/§12/§11), to the general Function representation — the equivalence
requirement, not representational sameness, is what this contract actually
needs.

## 29. Multi-host boundary

This contract is host-independent by construction (§2 through §25 name no
Python-specific mechanism as semantically required). Per issue #1010's
instruction to inspect both the Python reference host and the current
documented C++ capability boundary:

- The Python reference host (`src/genia/*`) is the only host that
  currently implements R20's `open_functions` capability
  (`spec/manifest.json`; `docs/host-interop/HOST_CAPABILITY_MATRIX.md`),
  and it is also the host whose implementation this contract's §12/§15/§19/
  §24 findings were read directly against.
- `docs/releases/R24.md` and `docs/analysis/r24-release-truth-audit.md`
  (R24, the C++ minimal conforming host) do not claim `open_functions`
  support; R24's pinned evidence records it among the currently-
  unsupported-but-not-misreported capabilities. This contract does not
  require C++ to support any behavior it does not currently claim
  (issue #1010's explicit instruction), and nothing here changes that
  claim.
- Because this contract is a strict semantic generalization of the
  existing, already-host-independent R20 contract (no new host-specific
  mechanism is introduced anywhere above), a future conforming host that
  already implements R20's `open_functions` boundary requires no new
  capability vocabulary entry to also satisfy the unified model — the
  unification is a *representation* consolidation on the Python reference
  host's side, not a new observable capability surface. A host that
  implements only ordinary functions and not R20 continues to correctly
  report `open_functions` (or its unified-model successor capability name,
  an F3/F5 decision) as unsupported.

## 30. Explicit non-goals (carried forward from issue #1010 and R20)

- No surface syntax decision (§0.2).
- No Core IR redesign, only recorded requirements (§28).
- No implementation, parser, or lowering change of any kind.
- No new release number.
- No change to `extend`/`use`-equivalent high-level operation *shape*
  beyond what §4/§5/§19 already require to fix confirmed defects — this
  contract does not add a third top-level operation, a priority/specificity
  mechanism, wildcard selection, or protocol/trait/typeclass/method
  dispatch, consistent with R20 contract §12's existing non-goals list,
  carried forward unchanged.
- No Unicode identifier, annotation-system redesign, actor, or event
  semantics — issue #1010's scope exclusions apply unchanged.
- No broad module-visibility redesign beyond §24 guarantee (2)'s narrowly
  scoped requirement (shared builtins-only root distinct from the entry
  program's own top-level frame) — this contract does not otherwise touch
  module visibility, export rules, or privacy beyond what R20 already
  specifies.
