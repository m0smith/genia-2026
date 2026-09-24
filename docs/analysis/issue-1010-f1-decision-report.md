# Issue #1010 — F0/F1 Decision Report

Status: **PROPOSED — FOR ARCHITECTURAL REVIEW. NOT APPROVED.** This report
summarizes F0/F1 work for issue #1010 (R20 follow-up: unify Function
semantics and settle extensibility declaration). It is a process/decision
document, not a language contract; the actual semantic proposal lives in
`docs/design/issue-1010-unified-function-model-contract.md`, and it too
remains unapproved. `GENIA_STATE.md` remains final authority for
implemented behavior — nothing in this report changes it.

## 1. F0 outcome

Both prior investigations named by issue #1010 ("Unified Function Model —
Contract Gate Report" and "Natural-Language Neutrality in Genia Syntax —
Architecture Investigation") were searched for exhaustively (full-text repo
search, `git log --all`, GitHub issue/PR search) and **not found** anywhere
in this repository's history or accessible GitHub state. Per issue
#1010's own instruction, neither was reconstructed from memory. See
`docs/analysis/investigation-recovery-note-issue-1010.md` for the full
search record. F1 below relies entirely on independently verified
evidence: the approved R20 contract/design/state documents and fresh
reproductions against the current interpreter, not on either missing
report's authority.

## 2. Current-model findings

The current implementation is a genuine two-species split, not a stylistic
difference:

- **Ordinary functions** (`GeniaFunction`/`GeniaFunctionGroup`,
  `src/genia/callable.py`) have no portable origin identity, dispatch via
  a `dict[int, GeniaFunction]` keyed by fixed-param count with an
  exact-arity shortcut, and share one flat `eval_with_tco` trampoline that
  correctly inlines mutual recursion between any two ordinary functions
  because `invoke_callable` always resolves a tail call down to a concrete
  `GeniaFunction` before returning a `TailCall`.
- **R20 open functions** (`GeniaOpenFunction`/`GeniaOpenContributionUnit`/
  `GeniaLinkedOpenFunction`) have a portable `(module_identity, name)`
  origin identity, dispatch via the stricter, contract-specified uniform
  minimum-based algorithm (`_dispatch_open`), and each run their **own
  private** trampoline loop that only avoids growing the Python stack for
  literal self-identical (`is self`) tail calls — never for calls to a
  different Function/FunctionView object, even one that is semantically
  "the same interface."

Both species reuse the same underlying pattern-match engine
(`match_lambda_pattern`) and the same none-awareness/Outcome machinery, so
runtime pattern/guard/Outcome behavior is close to unified already; the
real divergences are in **dispatch bookkeeping** (varargs-shortcut vs.
uniform), **identity/provenance** (absent vs. present), **TCO** (flat
shared trampoline vs. two-tier self-only trampoline), and **declaration-
time parser support** (docstrings, contiguity guards) that was built once
for ordinary functions and never fully re-built for open functions.

## 3. Verified divergences (issue #1010's ten known-evidence items)

Full reproductions, exact output, and file:line evidence for every item are
in `docs/analysis/issue-1010-r20-bug-verification-evidence.md`. Summary:

| # | Claim | Classification |
|---|---|---|
| 1 | Contribution units lost through aliasing | **NOT REPRODUCED** for the tested scenarios (dual alias on the consuming/`use` side; existing regression tests). A narrower, untested scenario (dual alias on the *contributing* side extending the same target) is a confirmed instance of item 2/4's root cause, found by code reading — see contract §15. |
| 2 | Non-contiguous `extend` runs lose contribution units | **CONFIRMED CONTRACT VIOLATION.** Silent data loss (not even an error), worse than the design doc's own promised rejection. |
| 3 | Alias rebinding loses contribution units | **NOT REPRODUCED.** Rebinding before `use` is correctly rejected (incompatible-contribution); rebinding after `use` correctly has no effect on the already-linked, immutable view. |
| 4 | Internal contribution bindings leak through exports | **CONFIRMED CONTRACT VIOLATION.** A raw `GeniaOpenContributionUnit` is directly readable via ordinary named access, bypassing `use` entirely. Same root cause as item 2. |
| 5 | Mutual/cross-function TCO failures | **CONFIRMED CONTRACT VIOLATION — most serious finding.** Self-recursion is fine (matches the R20 audit's claim); mutual recursion between two open interfaces overflows the Python stack at the same low iteration count where the equivalent, already-passing ordinary-function test proves constant stack space. The audit's PASS verdict rested on a TCO reproduction that only exercised self-recursion. |
| 6 | Grouped-header binders dropped | **INTENTIONAL DIFFERENCE** for non-trivial headers (cleanly rejected, as documented). **CONTRACT UNCLEAR / undocumented edge case**: a plain-identifier header's own binder names are unavailable inside a grouped arm that uses different names for the same position — a faithful, loud-failing (not silent) consequence of the documented flattening mechanism, not a distinct bug. |
| 7 | Open-function docstrings parse incorrectly | **CONFIRMED CONTRACT VIOLATION.** The ordinary leading-string-literal docstring convention was never wired for `open`; a docstring silently becomes the clause body and the real body is silently split into an orphaned, broken statement. `docstring` field is dead code. |
| 8 | Module environments see entry-program bindings | **CONFIRMED IMPLEMENTATION DRIFT** (general module-isolation defect, pre-existing, not R20-specific — but R20's own `extend`/`use` alias resolution inherits the same leak surface). |
| 9 | Ordinary/open fixed+varargs differences | **CONFIRMED IMPLEMENTATION DRIFT.** Fixed-over-varargs precedence itself is fine; a varargs-vs-varargs disambiguation shortcut exists only in ordinary dispatch, causing the two to diverge for identical clause sets at the same call arity. |
| 10 | Ordinary/open Outcome/`none` differences | **NOT REPRODUCED** as a semantic difference — runtime behavior is byte-identical. An unrelated parser-surface asymmetry (ordinary repeated-clause headers accept a narrower pattern grammar than `open` headers) was found and is not itself an Outcome bug. |

**Net:** 5 of 10 items are confirmed genuine, previously-undisclosed
defects (2, 4, 5, 7 as outright contract violations against the approved
R20 design; 8 and 9 as drift from documented/audited claims); item 1 adds
one narrower confirmed variant by code reading; items 3 and 10 are fully
cleared. None of these findings requires any implementation action in this
phase — they are carried forward as required-fix material for F3/F5, and
as evidence that unification is not merely cosmetic (§5 below).

## 4. Proposed Function/dispatch/identity/recursion model (summary)

Full detail in `docs/design/issue-1010-unified-function-model-contract.md`
§1–§25. In brief:

- **One Function species** replaces the current four runtime types: a
  Function is an origin-identity-bearing value with an ordered local
  Clause list; a FunctionView is an immutable composition of one Function
  plus explicitly selected ContributionUnits, sharing the base Function's
  origin identity for every purpose except dispatch participation.
- **One dispatch algorithm** (R20 contract §5, generalized): shape
  stratum → unit-local first match → across-unit exactly-one-candidate.
  A bare Function is the zero-ContributionUnit degenerate case of the same
  algorithm.
- **One identity model**: `(declaring module canonical identity, exported
  name)`, generalized from R20 to every Function, with the confirmed
  alias-spelling-keyed storage bug (items 2/4/1-narrow) named as a
  required correctness fix, not a design change — the *rule* is already
  right in the R20 contract; the *storage mechanism* violates it.
- **One TCO trampoline requirement**: a single flat loop keyed by resolved
  dispatch target, not by wrapper-object Python identity — the confirmed
  fix for item 5, and the contract's single most important new
  requirement, since it is the one place today's two-species split
  produces a real correctness gap rather than a documentation gap.
- **FunctionView recursion**: a call through a FunctionView's own bound
  name re-dispatches over that exact FunctionView's full participating-unit
  set on every call, including recursively; a Function's own internal
  self-reference (not through any FunctionView) is always base-only,
  preserving "no implicit extension from ordinary import" at the recursion
  boundary as well as the first-call boundary.

## 5. Permission/extensibility analysis and selected model

Full analysis in contract §26. In brief: ContributionUnit inertness alone
does not answer the permission question, because the question is about
declaration-time authorial commitment (closed-by-default reasoning,
fail-fast diagnostics) rather than runtime-effect safety, which R20's
existing invariants already guarantee under either model.

- **Model A (explicit permission)** — matches current, audited R20
  behavior exactly; preserves closed-by-default reasoning consistent with
  Genia's existing closed-shapes philosophy; fails fast at
  ContributionUnit-declaration time; costs one boolean declaration-time
  property (not a second runtime species) and commits F2 to spelling it.
- **Model B (composition is the authority boundary)** — removes that
  property entirely; matches the issue's own framing of "nothing happens
  until a consumer selects it"; loses the fail-fast diagnostic and weakens
  closed-by-default reasoning for every ordinary Function the instant
  unification ships, since every Function becomes a legal target with no
  action from its author.
- **Model C** — no independently justified narrower alternative was found;
  two candidates (opt-out-by-default, per-site acknowledgment) were
  considered and rejected as strictly worse than A or B.

**This report recommends Model A**, primarily because it is the only
option with zero behavior change for currently-passing programs and
because closed-by-default is a load-bearing value elsewhere in Genia's
design vocabulary (closed shapes/patterns) — but this is a genuine,
contestable judgment call for the human reviewer, not a foreclosed
conclusion; §26.5 of the contract states the case for Model B fairly and
notes a reviewer could reasonably choose it instead. Both models satisfy
every required R20 invariant (§27 of the contract).

## 6. R20 invariant mapping

See contract §27 for the full table. Every required invariant (no global
registry, contribution inertness, no implicit activation, explicit
composition, immutable views, import/selection-order independence,
deterministic ambiguity, provenance survival, cross-host representability,
no second runtime species) is preserved by construction under either
permission model. **Module isolation** is the one invariant with a
confirmed pre-existing gap (item 8) that this contract surfaces as a
requirement rather than a new weakening — R20 mechanisms themselves do not
add to that gap.

## 7. Unresolved questions for human review

1. **Model A vs. Model B** (§5 above / contract §26) — the central
   decision this report cannot make unilaterally.
2. **Varargs-vs-varargs disambiguation** (contract §7): should the unified
   rule tighten ordinary dispatch to the stricter, already-contractual
   open-function behavior (this report's proposal), or loosen open
   dispatch to match ordinary's existing shortcut? Tightening ordinary
   dispatch is an observable behavior change for any currently-passing
   ordinary-function program relying on the shortcut's silent success —
   unlike the duplicate-clause question below, this is not proven
   inobservable.
3. **Duplicate-clause structural checking** (contract §20): should ordinary
   functions gain R20's stricter build-time structural duplicate-key
   check (currently only rejects same-arity duplicates), or should open
   functions' check be loosened? This report recommends adopting R20's
   stricter check as the unified rule but flags it as an open question
   for review since it is a new class of accepted-today program that
   could start failing.
4. **Whether F3 keeps a lightweight representation for the common
   non-contributable, single-clause case** (contract §28 item 2) or gives
   every Function the full Clause-list/provenance shape uniformly — an
   implementation-cost question this document explicitly leaves to F3.
5. **Grouped-header binder-discard edge case** (contract §8 / item 6): this
   report classifies it as a faithful, non-silent consequence of the
   documented design rather than a bug requiring a fix, but a reviewer may
   want it explicitly documented as a known edge case regardless of what
   F1 decides about permission/dispatch.

## 8. Semantic requirements handed to F2/F3

- F2 (surface syntax) receives: one Function/Clause/ContributionUnit/
  FunctionView vocabulary with no runtime-species distinction to spell
  around; if Model A is approved, exactly one permission property to spell
  (contract §26.5 point 3 — explicitly not a mandate to reuse `open`
  verbatim, nor a mandate to invent a new word; that choice is F2's own,
  per issue #1010's scope exclusion "Do not automatically replace `open`
  with `extensible`"); `extend`/`use`-equivalent operation *shapes* are
  unchanged in this contract (only their underlying storage/lookup
  correctness, per §5/§19/§20, is required to be fixed).
- F3 (Core IR/runtime design) receives: contract §28's seven requirements
  (origin identity, ordered Clauses for every Function, structurally-keyed
  ContributionUnit identity, FunctionView composition with identity
  equivalence, unified module-reference resolution, derived-not-stored
  dispatch shape/ordinal, and the optional permission property) plus this
  report's §7 open questions to resolve before or during design, plus the
  §3 verified-divergence list as required-fix material (items 2, 4, 5, 7,
  8, 9, and the narrow item-1 variant) that F3's design must show how it
  closes, and F4's failing specs must cover.
- F4 (failing specs) receives, in addition to issue #1010's own listed
  minimum coverage: an explicit non-contiguous-`extend`-rejection case
  (item 2), an explicit contribution-privacy case asserting a
  ContributionUnit is *not* reachable by ordinary named access (item 4), an
  explicit mutual/cross-Function-identity TCO case at the same iteration
  count the existing ordinary-function TCO test already proves (item 5,
  mirroring `tests/unit/test_tco.py::test_mutual_tail_recursion_uses_
  constant_python_stack`), an open-function docstring case (item 7), and a
  varargs-vs-varargs parity case exercising the exact two-clause shape
  this report reproduced (item 9).

## 9. Is F1 ready for human approval?

**No — not as a final decision, but yes as a complete draft ready for
review.** Every element issue #1010 requires from F1 is present in
`docs/design/issue-1010-unified-function-model-contract.md`: all 25
semantic questions are answered, the critical permission/composition
question is analyzed with a stated recommendation (not a dodge), every
required R20 invariant is mapped, and Core IR/multi-host requirements are
recorded without redesigning either. What remains is explicitly a human
decision, not missing analysis: §7 above lists exactly the open questions
(chiefly Model A vs. B) that this report cannot resolve on its own
authority, consistent with issue #1010's requirement that the gate be
"approved through the repository process," not self-certified.

## 10. Issue #1010 progress against its acceptance criteria

Using the checklist from the issue body:

- [x] *A reviewed Unified Function Model contract defines Function,
  Clause, identity, ContributionUnit, FunctionView, dispatch, recursion,
  and composition.* — Drafted and complete; **not yet reviewed/approved**
  (the "reviewed" qualifier is the gating word — this is the draft
  awaiting that review).
- [ ] *The explicit-permission question is answered with documented
  rationale.* — **Analyzed with a recommendation** (Model A), not yet
  decided by human review. Partially supported: the analysis exists;
  the decision does not yet.
- [ ] *Final surface syntax is chosen only after that semantic decision.*
  — **Correctly not started**, per F1's own gate (F2 has not begun).
- [ ] *The chosen model does not rely on implicit extension, global
  mutation, or import order.* — **Not yet applicable**: no model has been
  chosen (approved) yet; both candidate models satisfy this criterion by
  construction (§6/contract §27), so it is expected to pass once a model
  is selected.
- [ ] *Ordinary and contributed functions share the intended
  dispatch/call semantics.* — **Designed, not implemented.** The contract
  specifies this; §3's findings show the *current* implementation does
  not yet fully achieve it (items 5, 9 especially) — this criterion is
  satisfied by the design, gated on F5 implementation.
- [x] *The known drift/bug findings are verified and dispositioned.* —
  Complete: all ten items classified in §3 above, with full evidence in
  `docs/analysis/issue-1010-r20-bug-verification-evidence.md`.
- [ ] *Core IR migration/design is explicitly defined and semantic rather
  than spelling-driven.* — **Requirements recorded (contract §28),
  migration/design itself not started** — that is F3's job, explicitly out
  of scope for F1.
- [ ] *Required failing specs/tests are identified before
  implementation.* — **Categories identified** (§8 above), **no test/spec
  files written** — correct for this phase; F4 has not begun.
- [ ] *Implementation is split into independently reviewable slices.* —
  **Not started** — F5 has not begun.
- [ ] *Applicable multi-host/C++ consequences are defined.* — **Defined**
  (contract §29): no new C++ claim required, unification does not expand
  the observable capability surface.
- [ ] *When implementation lands, authoritative docs/specs/semantic facts
  are synchronized.* — **Not applicable yet** — no implementation has
  landed; this is an F6 obligation for a future phase.
- [ ] *A skeptical truth audit passes before the follow-up is considered
  complete.* — **Not applicable yet** — F7 has not begun.

**Overall: F0 is complete. F1 is drafted and complete pending human
approval; it is not yet "passed" in the issue's own gating sense, since
that requires the review this report explicitly defers to.** No
acceptance criterion beyond the two directly satisfied above (contract
existence; bug findings verified/dispositioned) can honestly be marked
done, because every later criterion is explicitly gated on human approval
of this F1 material. Issue #1010 is **not closed** and this session does
not close it, per its own explicit instruction.

## 11. What this phase changed in the repository

Added only (no existing file modified, no implementation/test/spec/doc-
truth file touched):

- `docs/analysis/investigation-recovery-note-issue-1010.md` (F0)
- `docs/analysis/issue-1010-r20-bug-verification-evidence.md` (F1 raw
  evidence)
- `docs/design/issue-1010-unified-function-model-contract.md` (F1 contract
  draft)
- `docs/analysis/issue-1010-f1-decision-report.md` (this report)

None of these are committed or pushed per the task's explicit instruction
to stop after F0/F1 and return results for review.
