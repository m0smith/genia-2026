# R25 Release-Size Preflight — C++ Stateful Runtime and Concurrency

Status: **Planning/architecture record. Non-authoritative.** This document
changes no Genia language or runtime behavior and implements nothing.
`GENIA_STATE.md` remains final authority for implemented behavior. Roadmap
documents remain planning authority for sequencing; this document evaluates
them but does not replace them.

Scope of this document: a skeptical preflight of the currently-planned
release **R25 — C++ Stateful Runtime and Concurrency**, asking whether it is
correctly sized to begin implementation as one release, or whether it should
be decomposed. This is preflight/architecture work only — no R25
implementation, no `genia-cpp` changes, no capability additions, no roadmap
renumbering.

R24 (C++ Minimal Conforming Host) is confirmed **still in progress** as of
this preflight: `GENIA_STATE.md` §0 records E24-1 through E24-3 complete,
E24-4 through E24-8 remaining, entirely in the separate `m0smith/genia-cpp`
repository, which this preflight does not read or modify.

**Revision note:** this version incorporates a maintainer review pass. The
main substantive correction from that review: **Actor is removed from R25
entirely** and explicitly deferred to R38. The reasoning, in the reviewer's
own words, is preserved here because it is the central architectural
argument of this document: implementing today's Python actor convenience
layer in C++ under R25 would let a host-implementation artifact quietly
become the portable actor contract by precedent —

```text
Python actor behavior
        ↓
C++ copies it in R25
        ↓
R38 later asks:
"What should portable Genia actors actually mean?"
```

— which reverses the architecture direction the roadmap's own R37–R41
sequencing (settled by PR #994) just established: **R38 — Portable Actors,
Messaging and Supervision** owns actor identity, messaging, supervision,
lifecycle, Flow/event interaction, placement, and provider realization as
portable Genia semantics; hosts implement that contract afterward. R25 may
build infrastructure R38 later reuses, but must not make today's
Python-host-only actor layer portable by default.

---

## 1) Executive finding

**R25 as originally worded was directionally reasonable but
under-decomposed, and included one boundary error: Actor.** Its stated
non-goals (no language scheduler, no async/await, no supervision tree, no
distributed actors, no HTTP, no resource IO) already prevent the worst-case
scope creep. But its candidate scope still bundled independent host
primitive families — Ref, Cell, Process, and (incorrectly) Actor — plus
"threading/mailbox/failure/cleanup mapping" and "deterministic stress/race/
lifecycle tests" into what read as a single release-sized deliverable, and
risked pre-empting R38's own actor-semantics decision by implementing
today's Python actor convenience layer in C++ first. This is structurally
similar to the pre-R24 Exact Numeric Model gate (issue #838/PR #839) that
Genia's own postmortem (`docs/analysis/exact-numeric-gate-postmortem.md`)
found "too large and too cross-cutting to be a safe release prerequisite,"
with the explicit warning rule: *"If one implementation PR begins changing
more than one semantic subsystem plus its tests/documentation, stop and
reassess the slice boundary."*

R25 also has a problem the numeric gate did not: **zero existing shared-spec
(cross-host) evidence exists for Ref, Cell, or Process today.** They are
registered in `spec/manifest.json` as optional capabilities (`refs`,
`process_primitives`; Cell has no independent name) but no shared spec case
anywhere requires them — `capabilities.md` explicitly documents this as
"registered, not yet conformance-proven," identical in shape to
`execution_process`'s own disclosed gap. R25 cannot honestly produce
"evidence-based capability claims" (its own candidate-scope wording) without
first defining what host-neutral, deterministic, timing-independent
executable evidence for these primitives even looks like — and per the
review, that evidence must be **causal/observational, not timing-based**
(e.g., "a consumer blocked on an unset Ref eventually observes exactly the
value a producer establishes," not "the wake happens within 50ms"), so that
the R16 runner can prove it without becoming a scheduler-fairness test.

**Verdict: RESTRUCTURE.** Keep the `R25` label and position in the sequence
(no renumbering of R26 onward, no touching the R37–R41 sequence). Require
R25 to ship as an explicit epic sequence (`E25-0` … `E25-5`) decided *before*
implementation begins, each epic independently mergeable, independently
audited, scoped to one primitive family at a time, **excluding Actor
entirely**, and require that no portable C++ capability claim for Ref/Cell/
Process be made until host-neutral executable evidence exists for that
exact semantic surface — host-local unit tests prove implementation
mechanics, not cross-host semantics, and must not be treated as a
substitute. This is Phase 5 option **C**.

R25 is explicitly **approved multi-host portability infrastructure**, not a
killer-workflow feature expansion — see §7a for why that resolves the
`killer-workflow.md` parking-lot observation rather than blocking on it.

---

## 2) Current R25 scope inventory

Per `docs/strategy/roadmap/r25-r29.md` (verbatim, gathered via subagent):

> "Candidate scope retains the prior plan: C++ ownership/lifetime strategy;
> portability promotion for refs/cells/process observations;
> threading/mailbox/failure/cleanup mapping; deterministic stress/race/
> lifecycle tests; evidence-based capability claims."
>
> "Explicit non-goals: language scheduler, async/await, supervision tree,
> distributed actors, HTTP, or resource IO."

Note the roadmap's own candidate-scope wording already says "refs/cells/
process observations" — it does not name Actor. Actor's presence in this
preflight's initial draft came from over-reading "concurrency" in the
release title, not from the roadmap text itself. This revision corrects
that misreading.

Inventory of every implemented area the wording could reasonably reach,
classified per the preflight's required taxonomy:

| Area | Implemented today? | State authority | Portable or host-local | Classification |
|---|---|---|---|---|
| Ref (blocking sync reference) | Yes — `GENIA_STATE.md` "### Refs" (~L2150); `GENIA_RULES.md` §10 | Python-host-only (`threading.Condition`) | Host-local; capability `refs`, no shared-spec cases | **Definitely R25** |
| Cell (async fail-stop mailbox-of-one) | Yes — `GENIA_STATE.md` "### Cell helpers" (~L2196) | Python-host-only, capability group "Refs/Cells" | Host-local, no shared-spec cases, no independent capability name | **Definitely R25** |
| Process (`process.*`, FIFO mailbox, fail-stop, no restart) | Yes — `GENIA_STATE.md` "### Host-backed concurrency" (~L2170) | Python-host-only, capability `process_primitives` | Host-local, no shared-spec cases | **Definitely R25** |
| Actor (prelude layer over Cell) | Yes — `GENIA_STATE.md` "### Actor helpers" (~L2239) | Python-host-only, explicitly "not a shared cross-host contract category," no dedicated capability name | Host-local | **Excluded from R25 — deferred to R38.** Actor is Genia's own message-handling/effect-shape *convenience layer*, and R38 is the release that must decide what portable actor semantics (identity, messaging, supervision, lifecycle, placement) actually mean before any host — Python or C++ — gets to claim a "portable actor." Porting today's Python actor shape into C++ under R25 would let host implementation precede and bias that R38 decision. |
| `execution.process` (external OS process) | Yes — `GENIA_STATE.md` §9.40 | Portable *contract*, Python-implemented only, zero shared-spec cases | Distinct capability `execution_process` | **Already implemented by R24-adjacent work; out of scope** — a different, unrelated capability from Genia's own `process.*`; R25 must not conflate the two |
| Promise (`delay`/`force`) | Yes — `GENIA_STATE.md` §4.3 | Portable, part of the core evaluator, not host-capability-gated | Not a concurrency primitive — pure delayed/memoized values | **Not R25** — no threading/mailbox/failure-mapping story exists or is needed; including it would blur "stateful runtime" into "the whole value model" |
| Flow (lazy pull-based single-use stream) | Yes — `GENIA_STATE.md` "### Flow runtime" | Portable core runtime behavior, `flow_phase_1` capability, active shared-spec coverage | Distinct from concurrency; synchronous finalization only, explicitly "no async cancellation or scheduler involvement" | **Not R25** — R24/R27 territory (R27 explicitly owns "lazy pull-based single-use Flow phase 1... over the C++ host") |
| Lifecycle scopes (R14) | Yes — `GENIA_STATE.md` §§9.8–9.20 | Portable, Experimental, Python-implemented | Synchronous only; explicit non-goal: "no ... concurrent peer/child execution is defined" | **Prerequisite constraint, not R25 scope** — R25 must not attempt to make lifecycle concurrent; that boundary is explicitly frozen |
| Concurrency scheduling/threading | Host OS threads only, `GENIA_RULES.md` §10: "concurrency remains host-backed (threads), not language-scheduled" | N/A | Host-local by design | **Definitely R25** (as *implementation mechanics*, not new language semantics — see §7b on which parts are and are not portable) |
| Cancellation / failure propagation | No unified mechanism — each primitive (Ref/Cell/Process/Lifecycle/Flow) defines its own local fail-stop/finalization notion; Outcome (`some`/`none`/`err`) is a value-level result type, not a cancellation token | GENIA_STATE.md, multiple sections | N/A | **Already implemented (per-primitive); no new unifying mechanism should be invented in R25** |
| Restart/supervision | Cell: single-entity restart only. Process: explicitly none. Supervision trees/links/monitors: **do not exist anywhere in the repo** | GENIA_STATE.md ~L2311, capabilities.md, R14 non-goals | N/A | **Explicitly future actor/event work — must not be pulled into R25.** `R38 — Portable Actors, Messaging and Supervision` owns supervision, restart *policy*, `ActorRef`, and mailbox *capacity/backpressure* as portable Genia semantics |
| Message ordering / mailbox / backpressure | FIFO per-entity mailbox exists (Process/Cell); "no cross-actor ordering," "no backpressure" explicitly listed as not guaranteed | GENIA_STATE.md ~L2304-2317 | Host-local | **R25 may harden/prove the existing local-process FIFO behavior that is already authoritative today; it must not define portable mailbox-*capacity* or *backpressure* semantics — that is R38's** |
| Deterministic vs. nondeterministic behavior | No determinism guarantee exists across concurrent entities today; this is a documented, accepted property, not a defect | GENIA_STATE.md concurrency-invariants block | N/A | **R25 should prove the C++ host reproduces the same *documented* nondeterminism boundary, not eliminate it** |
| Thread/process identity leakage | Not documented as a concern anywhere | — | — | **Unclear contract gap** — worth one explicit line in R25's contract saying host thread/process identity must not leak into any Genia-observable value, matching the existing "opaque handle" pattern used elsewhere (e.g. config providers) |
| Host resource limits | No documented limits for Ref/Cell/Process (contrast with `execution.process`'s explicit 1MiB stdout/stderr caps and 1..300000ms timeout) | — | — | **Contract gap requiring an explicit non-portability statement — see §7b** |
| Interaction with Flow | None documented; Flow and these primitives are used independently in examples (e.g. `ants_actor.genia`, itself now out of scope for this exercise since it demonstrates Actor) | — | — | **Not R25** — no existing contract to port |
| Interaction with future R37 events / R38 portable actors | R38's own scope (`docs/strategy/roadmap/r38.md`) explicitly claims `ActorRef` identity, message/envelope contract, mailbox capacity/backpressure, and supervision as *portable Genia semantics*, and does **not** list R25 as a foundation it builds on | roadmap | — | **Boundary now resolved by excluding Actor from R25 — see §7** |

---

## 3) Portable semantic dependency map

**Portable semantic dependencies (frozen, reusable, must not be reopened):**

- **Identity/equality (R18):** Ref, Cell, Process, and Promise are all
  identity-bearing runtime values — compared only by entity identity, never
  structurally, and equality never forces/dereferences them
  (`GENIA_STATE.md` §9.6 "Portable value equality"). This is already settled
  and portable; R25 inherits it unchanged.
- **Outcome/failure (R9-era Outcome model):** each primitive's fail-stop
  state is already expressed as ordinary Outcome values (`cell_error`
  returns `some(error_string)`/`none`). R25 should reuse this, not invent a
  second cancellation/error channel.
- **Core IR:** none of Ref/Cell/Process/Promise introduce or require a Core
  IR node — they are ordinary prelude-backed calls over host-backed
  capability values. R25 must not add one.
- **Lifecycle ownership (R14):** frozen at "synchronous, single-threaded
  scopes only; no concurrent peer/child execution is defined." R25 must
  treat this as an upstream constraint, not a dependency to extend.
- **Message/state semantics:** FIFO-per-entity ordering and fail-stop are
  already the documented portable *intent* (they are Python-host-only today,
  but the intended shape — one mailbox, one handler thread, permanent
  failure on unhandled exception — is stable prose in `GENIA_STATE.md` and
  `capabilities.md`). This is the actual "authoritative behavior" R25 must
  reproduce in C++, prior to any question of shared-spec proof.

**Host implementation dependencies (C++-side mechanics, not Genia semantics):**

- mutex / condition-variable machinery (Ref)
- a per-entity worker thread + bounded/unbounded queue (Cell, Process)
- fail-stop state machine (cached error string, permanent rejection of
  further operations) (Cell, Process)
- restart machinery (Cell only — Process explicitly has none)
- C++ ownership/lifetime strategy for these entities (who frees a Cell's
  worker thread, when, and how a dangling reference from Genia code is
  prevented or diagnosed)

Per `AGENTS.md`'s Future Execution-Realization Guardrail and
`docs/architecture/execution-realization.md` (both non-authoritative
direction, read directly): infrastructure/host-mechanism detail must never
become Core IR or shared language semantics. R25's job is squarely in the
"host implementation dependencies" column; it must not manufacture new
portable semantics for mailbox capacity, backpressure, or supervision along
the way — that is explicitly R38's territory.

**What can be implemented sequentially, independent of the whole surface:**

Ref, Cell, and Process are independently testable, independently mergeable,
and independently auditable. The natural build order is:

1. **Ref** — simplest: one condition variable, blocking get/set/update, no
   threads-of-its-own, no fail-stop.
2. **Cell** — its own semantic unit, *not* a trivial wrapper over Process:
   it adds last-good-state preservation on failure, fail-stop status,
   restart, stale-queue discard on restart, staged/rolled-back nested sends
   during an in-flight update, and graceful drain-on-stop. This is a
   materially richer contract than Ref and deserves its own epic
   immediately after Ref.
3. **Process** — a sibling of Cell (own worker thread + FIFO mailbox +
   fail-stop) but *without* restart, last-good-state preservation, or
   nested-send staging — provable independently of Cell, and simpler than
   it despite introducing the mailbox concept, because it carries none of
   Cell's recovery machinery.

(Actor, which in Python is a thin protocol layer over Cell, is intentionally
excluded — see the revision note above and §7.)

What matters more than the exact second/third ordering is that Ref, Cell,
and Process each land as their own epic — never combined into one
"concurrency" ticket — exactly the shape the numeric-gate postmortem
recommends ("multiple independently mergeable PRs against current `main`...
[each establishing] one narrow invariant").

---

## 4) Conformance/evidence map (Phase 3, reusing R16/`executable-semantic-conformance.md` — no second framework invented)

Applying the existing 7-part obligation
(`docs/architecture/executable-semantic-conformance.md`) to each candidate
R25 unit:

| Unit | Authority | Boundary | Executable proof today | Applicability (capability) | Host evidence needed | Truth sync | Ambiguity stop |
|---|---|---|---|---|---|---|---|
| Ref | `GENIA_STATE.md` "### Refs" prose | Capability/provider contract (opaque handle value), not Core IR | **None** — no shared-spec case exists | `refs` (registered, unused) | A deterministic, causal (not timing-based) shared case: unset Ref → consumer blocks on `ref_get` → producer sets a value → consumer's eventual observation equals exactly that value. Provable through the existing R16 protocol using an ordering/causality assertion, not a wall-clock assertion. | `docs/host-interop/capabilities.md`, `HOST_CAPABILITY_MATRIX.md`, `spec/manifest.json` once such a case is designed and lands | **Yes — stop here first (E25-0).** Whether the R16 runner/protocol as it exists today can express a causal-ordering assertion (vs. its current stdout/stderr/exit_code/AST-equality comparisons) is not yet decided. This is a genuine protocol-design question, not just a missing test file. |
| Cell | `GENIA_STATE.md` "### Cell helpers" prose | Capability/provider contract | None | No independent capability name today; needs one (or an agreed sub-scope of `refs`) per §13 | Same causal-evidence question as Ref, plus: fail-stop preserves last good state; restart discards stale queued updates; nested sends during an update commit only if that update succeeds. Each is independently expressible as "send sequence in → observed final state out," not a timing assertion. | Same docs | Same E25-0 ambiguity stop, resolved once for Ref and then reused, not re-litigated, for Cell |
| Process | `GENIA_STATE.md` "### Host-backed concurrency" prose | Capability/provider contract | None | `process_primitives` | "send A; send B; handler records observations; observable result is exactly `[A, B]`" — again causal/ordering, not timing. Plus fail-stop permanence: after one failing message, all later `send` calls are rejected. | Same docs | Same E25-0 ambiguity stop |

**Actor is intentionally absent from this table.** Its conformance
questions (what is an `ActorRef`, what does portable actor messaging mean,
what supervision/restart policy is authoritative) are R38's to answer, not
R25's.

**Conclusion for this phase:** Ref, Cell, and Process each hit the same
"Ambiguity stop" at step 7 of the conformance framework, but it is one
underlying protocol-design question, not three: **can the existing R16
shared-spec runner express causal/observational assertions about
concurrent, multi-thread-visible behavior**, as opposed to its current
"compare final stdout/stderr/exit_code/AST" comparisons? Resolving this once
in E25-0 unblocks Ref, Cell, and Process alike.

---

## 5) Contract/evidence gaps found

1. **No shared-spec existence for Ref/Cell/Process in any host, including
   Python.** `spec/` has zero cases requiring `refs` or `process_primitives`,
   confirmed by direct grep. R25's candidate wording ("evidence-based
   capability claims") presupposes evidence infrastructure that does not
   exist yet, for any host, and that infrastructure must express causal
   observations, not timing.
2. **No capability name exists for Cell specifically** — it rides
   informally under the "Refs/Cells" capability grouping in
   `capabilities.md` without its own `spec/manifest.json` entry.
3. **No documented resource-limit contract** for Ref/Cell/Process (contrast
   `execution.process`'s explicit byte/timeout caps). Per the review, the
   correct resolution is not to invent new limits, but to state plainly
   which properties are contract and which are Python's own realization
   choice — see §7b.
4. **R25's roadmap wording uses "mailbox"** in a way that must be fenced off
   from R38's own claimed "mailbox capacity and backpressure are contract
   concerns" territory. R25 may hardened-prove only whatever minimal
   local-process FIFO behavior is *already authoritative today*
   (`GENIA_STATE.md`'s existing "FIFO mailbox... one handler invocation at a
   time" prose); it must not define capacity, backpressure, or any new
   portable mailbox semantic.
5. **R25 sits inside `killer-workflow.md`'s explicit parking-lot list**
   ("actors / process-level concurrency," "lifecycle machinery" — "Unless
   explicitly approved, route proposals in these areas to parking lot").
   Per the maintainer review, this is not treated as a blocker: R25 is
   explicitly approved multi-host portability infrastructure (the same
   category R7, R8, and R24 itself occupy), not a killer-workflow feature
   expansion, and does not need to re-litigate whether concurrency belongs
   in the product every time another host is built. This rationale should
   be recorded explicitly in R25's own contract text (see §13), not merely
   inferred from precedent.
6. **Sequence diagram vs. dependency-chain discrepancy (found during
   sequencing review, not directly an R25 gap but relevant to "downstream
   impact through R41"):** `docs/strategy/roadmap/sequence.md`'s diagram
   chains R37→R38→R39→R41 directly and places **R40 — Configuration and
   Secret Hardening and Ergonomics outside the dependency chain entirely**,
   with an explicit note that "reservation number does not imply dependency
   on R14–R39 or R41." This is intentional per the document's own prose, not
   an error — but it means the "expected" R37→R38→R39→R40→R41 straight
   chain from this preflight's own brief is not what the roadmap actually
   specifies. No edit is proposed; this is flagged for awareness only.

---

## 6) R24 lessons applied to R25

From `docs/analysis/exact-numeric-gate-postmortem.md` and the R24 epic
history (`docs/strategy/roadmap/e24-issue-sequence.md`,
`docs/design/r24-cpp-host-preflight.md`, `docs/design/r24/*`):

- **Root cause of the pre-R24 failure:** "treating a multi-subsystem
  language change as a prerequisite gate instead of admitting that it was a
  sequence of releases." R25's candidate scope, before this revision,
  bundled Ref/Cell/Process/Actor the same way the pre-R24 numeric gate
  bundled source-classification/runtime/rendering/JSON/formatting; removing
  Actor and epic-splitting the rest applies the same fix R21/R22/R23 already
  proved — but applied *before* any implementation branch opens, not after
  a failed one.
- **R24 itself, even correctly pre-decomposed into 8 epics, still produced
  roughly one repair commit per landed epic** (bootstrap-cases.json fixed
  three separate times across E24-3/E24-6 alone). This is not evidence that
  epic decomposition fails — it is evidence that evidence-based ticketing
  inherently produces correction cycles, and that a release attempted as one
  undifferentiated gate would have multiplied that churn across
  unrelated subsystems simultaneously, which is strictly worse.
- **Native-primitive burden is comparatively lower for R25 than it was for
  R24's numeric work.** R24 had to hand-implement bignum, Decimal, Rational,
  and UTF-8 machinery in-house per `docs/design/r24/native-primitive-inventory.md`
  and `dependency-toolchain-policy.md` (no third-party library reuse
  allowed). R25's primitives — mutex, condition variable, worker thread,
  FIFO queue — are squarely inside the C++ standard library
  (`<thread>`, `<mutex>`, `<condition_variable>`, `<queue>`), so the
  *implementation* burden per subsystem should be smaller than R24's per
  numeric-kind burden was, and removing Actor further reduces subsystem
  count from four to three.
- **Portability-obligation fan-out is lower for R25.** R24 had to satisfy
  mandatory portable obligations accumulated across R17–R23
  (`docs/design/r24/portability-obligation-map.md`). Ref/Cell/Process carry
  no such mandatory portable obligation — they are optional, Python-host-only
  capabilities today. This cuts against R25 being "R24-sized" in the
  numeric sense, but it does not remove the evidence-infrastructure gap
  identified in §5.
- **Diagnostic-normalization discipline still applies.** R24 needed a
  dedicated adversarial epic (E24-5) purely to prove no raw host exception
  text leaked. Any C++ fail-stop error string for Ref/Cell/Process needs the
  same discipline — this belongs inside the cross-cutting hardening epic
  (E25-4 below), since the surface is much smaller per primitive than R24's
  numeric diagnostic surface was.

**Net comparison:** R25, once Actor is removed, shares R24's *structural*
risk (multiple semantic subsystems bundled under one release name) at
smaller subsystem count (three, not four) and lower *magnitude* risk
(native-primitive complexity, mandatory cross-host obligation fan-out). The
correct response, per the postmortem's own "why this is better" reasoning,
is the same regardless of magnitude: decompose before starting, not after a
branch grows unreviewable.

---

## 7) Release-size assessment

Using the qualitative scale requested (small / medium / large /
release-threatening):

- **Ref alone:** small.
- **Cell alone:** small–medium (adds the fail-stop state machine, restart,
  stale-queue discard, and nested-send staging — a materially richer
  contract than Ref).
- **Process alone:** small (simpler than Cell despite introducing the
  mailbox concept — no restart, no last-good-state recovery, no nested-send
  staging).
- **Cross-cutting deterministic stress/race test harness + evidence-based
  capability declaration, across Ref/Cell/Process:** medium on its own, and
  it cannot start honestly until the §5 evidence-infrastructure gap
  (E25-0) is resolved.
- **R25 as originally worded, with Actor included and attempted as one
  undifferentiated release:** large, trending toward release-threatening —
  four independent concurrency models, an unresolved evidence-infrastructure
  question touching all of them, and a live boundary risk against R38's
  claimed actor/mailbox/supervision territory.
- **R25 with Actor removed and decomposed into epics along the Ref→Cell→
  Process build order (§3), with the evidence-infrastructure question
  resolved as its own first contract step:** each epic is small, and the
  release as a whole becomes **medium** — smaller than R24's own realized
  shape (8 epics across four numeric kinds plus a full diagnostic sweep),
  not release-threatening.

### 7a) Why the killer-workflow parking-lot observation does not block R25

`killer-workflow.md` names "actors / process-level concurrency" and
"lifecycle machinery" as categories to park "unless explicitly approved."
R25 is not an unapproved feature request drifting in from that parking lot —
it is a **numbered, roadmap-sequenced portability-infrastructure release**
supporting the multi-host strategy, in the same category R7 (web-serving
ergonomics), R8 (server-execution-mode infrastructure), and R24 itself
already occupy: each of those shipped as "explicitly approved infrastructure
work" distinct from the killer-workflow's own feature priority, and each
recorded that distinction in its own contract rather than leaving it
implicit. R25 should do the same (see §13) rather than being treated as a
standing risk to re-litigate at every check-in.

### 7b) What is contract vs. what is host realization (resource limits)

Python's current implementation realizes Ref/Cell/Process as one OS thread
per entity with unbounded creation. That realization choice must not become
portable Genia semantics merely because Python happens to implement it that
way — a C++ (or future Rust/Java/event-loop-based) host should remain free
to use a thread pool, a fiber scheduler, or any other internal mechanism.

**Contract (must hold in any conforming host):**

- FIFO ordering per mailbox
- serialized handler execution (one update/message in flight at a time per
  entity)
- blocking `ref_get`/`ref_update` observation of an unset Ref until set
- fail-stop permanence (once failed, an entity permanently rejects further
  operations)
- the specific, already-documented stop/restart observations (Cell:
  last-good-state preserved, stale queue discarded, restart clears failure;
  Process: no restart, by design)

**Not contract (Python's own realization choice, not portable semantics):**

- one OS thread per Process/Cell specifically
- any particular scheduling fairness or wake latency
- host thread/process identity being observable from Genia code
- unbounded thread creation as a required implementation strategy

This distinction — semantic behavior above, realization below — is the same
principle `docs/architecture/execution-realization.md` already states for
the language generally, and it is the specific form R25 must give it for
Ref/Cell/Process. It also directly feeds R36/R38, which will need the same
discipline for portable actor placement and realization.

---

## 8) Recommended decomposition

**Outcome C — keep R25 as the umbrella release name and roadmap position,
define independently completable sub-releases (epics) beneath it, and
exclude Actor entirely.** Renumbering R25 into R25a/R25b/R25c as separate
numbered releases (Outcome B) is not recommended: it would force downstream
renumbering pressure on R26 onward and the fixed R37–R41 sequence for no
compensating benefit, since Ref/Cell/Process share one coherent umbrella
claim ("the C++ host has a provably equivalent stateful/concurrency
primitive layer, excluding actors") and a natural dependency order that an
umbrella-with-epics structure already expresses cleanly.

Revised proposed epic sequence:

| Epic | Scope |
|---|---|
| **E25-0** | Portable state/concurrency contract + evidence model: resolve whether/how the R16 runner can express causal/observational (not timing-based) assertions for concurrent behavior; record the contract-vs-realization split from §7b; explicitly exclude Actor with a pointer to R38. |
| **E25-1** | Ref contract/evidence + C++ Ref |
| **E25-2** | Cell contract/evidence + C++ Cell |
| **E25-3** | Local Process/mailbox contract/evidence + C++ Process |
| **E25-4** | Cross-cutting ownership, race, cleanup, diagnostic, and resource hardening (the E24-5-style adversarial sweep, sized to three primitives instead of a full numeric family) |
| **E25-5** | Release truth sync + skeptical audit |

No epic may claim a portable capability for its primitive until E25-0's
evidence model has actually produced executable proof for that primitive —
a host-local unit-test suite, however thorough, proves implementation
mechanics, not cross-host semantics, and must not be substituted for that
proof. If a specific observation genuinely cannot be expressed through the
R16 runner, E25-0 (or the epic that discovers the gap) must say so
explicitly and narrow that primitive's portability claim accordingly, rather
than quietly declaring "supported."

**R25's contract must state explicitly (tightened non-goals):**

- Actors are excluded from R25. Portable actor semantics and any C++ actor
  realization belong to R38.
- No actor contract, no supervision, no restart *policy* generalization
  beyond Cell's already-documented single-entity restart.
- No mailbox capacity or backpressure semantics beyond whatever minimal
  local-process FIFO behavior is already authoritative today.
- No distributed messaging, no events/pub-sub (R37's territory), no
  placement (R36/R38's territory).
- No language scheduler, async/await, HTTP, or resource IO (already in the
  roadmap's existing non-goals; preserved unchanged).
- R25 is explicitly approved multi-host portability infrastructure,
  recorded as such in its own contract text, resolving the
  `killer-workflow.md` parking-lot question rather than leaving it open per
  §7a.

---

## 9) Exact proposed release sequence

**No renumbering proposed.** The recommendation preserves the existing
numbering exactly:

```
R24 — C++ Minimal Conforming Host                         (in progress)
R25 — C++ Stateful Runtime and Concurrency                (umbrella; epics E25-0..E25-5 as above; Actor excluded)
R26 — C++ REPL and Data Bridges                           (unchanged; independent of R25 per roadmap)
R27 — C++ Flow, Pipe Mode, and HTTP Serving               (unchanged; depends on R24 + any approved R25/R26 behavior)
...
R37 — Unified Events and Subscriptions                    (unchanged)
R38 — Portable Actors, Messaging and Supervision          (unchanged; now explicitly the sole owner of actor semantics/realization)
R39 — Genia-Native Conformance Tooling                    (unchanged)
R40 — Configuration and Secret Hardening and Ergonomics   (unchanged; intentionally outside the R37→R41 dependency chain per sequence.md)
R41 — Portable Core IR Artifacts                          (unchanged)
```

This preserves numbering stability exactly as instructed and requires no
edits to `sequence.md`, `release-roadmap.md`, or `r25-r29.md`'s title/number
— only (optionally, and not made in this pass) the non-goal tightening
described in §8 and §13 inside R25's existing entry.

---

## 10) Smallest first post-R24 release

**E25-1 — C++ Ref: ownership/lifetime and blocking synchronization only.**

- **One headline semantic claim:** "The C++ host provides a Ref primitive
  whose blocking get/set/update behavior is observably equivalent to the
  Python reference host's documented behavior, under an explicit,
  documented C++ ownership/lifetime strategy."
- **Explicit prerequisites:** E25-0's evidence-model decision must be
  recorded first, specifically resolving whether/how the R16 runner can
  express a causal-ordering assertion (blocked-consumer eventually observes
  producer's value) rather than a timing assertion.
- **Explicit exclusions:** no Cell, Process, or Actor; no restart semantics
  (Ref has none to begin with); no mailbox; no fail-stop; no new Core IR;
  no new manifest capability claim beyond what E25-0 authorizes; no attempt
  to make Lifecycle scopes concurrent; no claim about thread-per-entity
  realization being required (§7b).
- **Bounded capability/evidence surface:** exactly the `refs` capability
  group's `ref.create/get/set/update` operations, per
  `docs/host-interop/capabilities.md`'s existing "Group: Refs / Cells"
  definition — no new names invented.
- **Executable conformance target:** a deterministic, causal (not
  timing-based) proof that a blocking `ref_get` call is unblocked by a
  concurrent `ref_set` from a second thread and observes exactly that set
  value, matching the documented "blocks the calling thread
  indefinitely... `ref_set` wakes all blocked waiters" contract.
- **Vertical proving case:** a small C++ program with two threads — one
  blocks on an unset Ref, the other sets it after a delay — producing the
  same observable value the Python reference host produces for the
  equivalent Genia program, verified by outcome/ordering, not by timing.
- **Clear completion criteria:** ownership/lifetime strategy documented;
  blocking/wake semantics proven deterministic under a thread sanitizer (no
  data races, no UB); no leaked host thread/handle identity into any
  Genia-observable value; independent audit passes.
- **Skeptical audit gate:** a fresh audit (not the implementer) confirms the
  above against `genia-cpp`'s actual merged code, following the same
  "audit runs against merged main, defects become small repair PRs" pattern
  the postmortem recommends.

A reviewer can verify this acceptance statement without saying "and also all
the rest of concurrency" — it says nothing about Cell, Process, mailboxes,
Actor, or evidence-model completeness beyond Ref itself.

---

## 11) Explicit non-goals (of this preflight, and inherited into R25 planning)

This preflight does not, and R25 planning built on it must not:

- implement any R25 behavior in `genia-cpp` or anywhere else
- modify `m0smith/genia-cpp` in any way
- begin R26 or R27 implementation
- change Genia runtime behavior, `GENIA_STATE.md`, or any implemented-truth
  document
- change parser/AST/Core IR behavior
- add, remove, or rename any `spec/manifest.json` capability
- write implementation tests or specs
- create R25 implementation tickets (the epic sequence in §8 is a
  recommendation for future ticketing, not tickets themselves)
- merge anything or touch R24's ongoing work in any repository
- implement, design, or propose Actor semantics in C++ under R25 — that is
  R38's scope, explicitly out of reach here
- propose actor/event/supervision *language* semantics generally — R38's
  scope
- resolve the E25-0 evidence-model question itself — that is flagged as the
  first required follow-up (§13), not answered by this document

---

## 12) Risks / regret checks

- **Regret risk if R25 is kept as one undifferentiated release anyway
  (including Actor):** repeats the pre-R24 numeric-gate failure mode and
  additionally biases R38's actor-semantics decision with a C++
  implementation of today's Python convenience layer that no one has yet
  decided should be portable.
- **Regret risk if R25 is split into separately *numbered* releases:**
  forces renumbering pressure on R26 onward and the fixed R37–R41 sequence
  for no real benefit, since Ref/Cell/Process share one coherent umbrella
  completion claim and a natural dependency order that an umbrella-with-epics
  structure already expresses cleanly.
- **Regret risk if the E25-0 evidence-model question is skipped, or answered
  by falling back to "host-local tests count as conformance":** every later
  epic's "evidence-based capability claim" becomes an unfalsifiable
  assertion — exactly the outcome R16's conformance framework exists to
  prevent, and exactly the fallback the maintainer review explicitly warns
  against. Host-local tests prove correctness of implementation mechanics;
  they do not prove cross-host semantics.
- **Regret risk if R25's non-goals are not tightened against R38:** a future
  R25 epic could accidentally define portable mailbox-capacity or
  backpressure semantics, or ship a C++ Actor, "for C++'s own good," which
  R38 would then have to either adopt as unwanted prior art or explicitly
  overrule — either way, wasted or contested work. Removing Actor from R25
  entirely closes the largest version of this risk; the remaining
  mailbox-capacity/backpressure line item in §8's tightened non-goals closes
  the rest.
- **Regret risk if Python's thread-per-entity realization is silently
  treated as contract:** a future host (C++ or otherwise) could be forced
  into an unnecessarily heavyweight implementation, or a genuine behavioral
  difference could be mistaken for nonconformance. §7b's contract/realization
  split exists specifically to prevent this.
- **Regret risk if R25 proceeds without recording its own
  explicitly-approved-infrastructure rationale:** a future audit could
  reasonably ask why parking-lot-classified work shipped without the same
  explicit-approval trail R7/R8/R14 recorded. §7a resolves this in
  reasoning; §13 asks that it also be recorded in R25's contract text.

---

## 13) Required follow-up architecture/contracts

1. **E25-0 contract step (highest priority):** define deterministic,
   host-neutral, *causal/observational* (not timing-based) executable
   evidence for Ref/Cell/Process behavior, and determine what the existing
   R16 shared-spec runner needs (if anything) to express such assertions.
   This is a design question, not an implementation one, and must be
   resolved before any C++ code is written under the R25 name. No portable
   capability claim for any of these primitives may be made until this
   evidence exists for that exact primitive.
2. **Capability-naming decision:** whether Cell needs its own
   `spec/manifest.json` capability name, or continues riding informally
   under the "Refs/Cells" grouping.
3. **One added set of non-goal sentences in
   `docs/strategy/roadmap/r25-r29.md`** stating: Actors are excluded from
   R25 and belong to R38; no supervision or restart-policy generalization;
   no mailbox capacity/backpressure semantics beyond today's authoritative
   local-process FIFO behavior; no distributed messaging, pub-sub, or
   placement. (Not made in this pass, per the instruction to report before
   editing broadly — offered here as the exact, minimal, non-renumbering
   edit a maintainer could apply.)
4. **Resource-limit contract decision, framed per §7b:** record explicitly
   which Ref/Cell/Process properties are contract (FIFO ordering, serialized
   handler execution, blocking-until-set observation, fail-stop permanence,
   the documented stop/restart behaviors) and which are Python's own
   realization choice (thread-per-entity, scheduling fairness, wake latency,
   thread identity, unbounded thread creation) that a C++ host is free to
   implement differently.
5. **Explicit approval rationale recorded in R25's own contract text** (not
   just this preflight) stating that R25 is approved multi-host portability
   infrastructure, analogous to R7/R8/R14, and does not require re-litigating
   whether concurrency belongs in the product despite
   `killer-workflow.md`'s parking-lot classification of "actors /
   process-level concurrency" and "lifecycle machinery."

---

## 14) Stop gate

This preflight stops here. No R25 implementation has been started, no
`genia-cpp` repository has been read or modified, no R26/R27 work has begun,
no Genia runtime/parser/Core IR behavior has changed, no capability has been
added, no implementation tickets have been created, nothing has been merged,
and no interference with the ongoing R24 work has occurred. `GENIA_STATE.md`
is unchanged, matching the instruction that no behavior is being
implemented.

---

## Answering the central question directly

**Would beginning the current R25 as written risk repeating R24's
oversized-release problem?**

**Yes, structurally, and it also risked a second, distinct error — but both
are preventable and the fix is cheap.** R25 as originally worded bundled
four independent concurrency subsystems (Ref, Cell, Process, and Actor)
under one release name, exactly the "multi-subsystem gate" shape Genia's own
postmortem already diagnosed as unsafe for the pre-R24 numeric work. Beyond
that sizing risk, including Actor specifically risked a second, sharper
error: letting a C++ port of today's Python-host-only actor convenience
layer become the de facto portable actor contract before R38 — the release
the roadmap's own R37–R41 sequencing designated for exactly that decision —
ever gets to make it. Removing Actor from R25 entirely, and decomposing the
remaining Ref/Cell/Process work into small, independently auditable epics
gated on a first evidence-model contract step (E25-0), converts what would
have been a large, trending-release-threatening, boundary-violating bundle
into a medium release built from three small, independently auditable
slices — the same correction R21/R22/R23 already proved works for exact
numerics, the same correction R24 was itself decomposed into eight epics to
apply, and, on the Actor question specifically, the correction that keeps
R38's own architectural decision from being made by implementation
precedent instead of by design.
