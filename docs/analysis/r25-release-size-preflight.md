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

---

## 1) Executive finding

**R25 as currently worded is directionally reasonable but under-decomposed.**
Its stated non-goals (no language scheduler, no async/await, no supervision
tree, no distributed actors, no HTTP, no resource IO) already prevent the
worst-case scope creep. But its candidate scope still bundles **four
independent, differently-shaped host primitive families** — Ref, Cell,
Process, Actor — plus "threading/mailbox/failure/cleanup mapping" and
"deterministic stress/race/lifecycle tests" into what reads as a single
release-sized deliverable. This is structurally the same shape as the
pre-R24 Exact Numeric Model gate (issue #838/PR #839) that Genia's own
postmortem (`docs/analysis/exact-numeric-gate-postmortem.md`) found "too
large and too cross-cutting to be a safe release prerequisite," with the
explicit warning rule: *"If one implementation PR begins changing more than
one semantic subsystem plus its tests/documentation, stop and reassess the
slice boundary."*

R25 has one more latent problem the numeric gate did not: **zero existing
shared-spec (cross-host) evidence exists for any of Ref, Cell, Process, or
Actor today.** They are registered in `spec/manifest.json` as optional
capabilities (`refs`, `process_primitives`) but no shared spec case anywhere
requires them — `capabilities.md` explicitly documents this as "registered,
not yet conformance-proven," identical in shape to `execution_process`'s own
disclosed gap. This means R25 cannot simply "port to C++ and pass the shared
suite" the way R24's E24-1 through E24-3 slices did — the shared suite for
these primitives does not exist. Producing "evidence-based capability
claims" (R25's own candidate-scope wording) therefore requires first
deciding, and likely first building, the executable-conformance surface
these claims would rest on. That is a real prerequisite gap, not merely an
implementation detail.

**Verdict: RESTRUCTURE.** Keep the `R25` label and position in the sequence
(no renumbering of R26 onward, no touching the R37–R41 sequence), but
require R25 to ship as an explicit epic sequence (`E25-1` … `E25-N`,
mirroring R24's own `e24-issue-sequence.md` discipline) decided *before*
implementation begins, each epic independently mergeable, independently
audited, and scoped to one primitive family at a time. This is Phase 5
option **C**.

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

Inventory of every implemented area the wording could reasonably reach,
classified per the preflight's required taxonomy:

| Area | Implemented today? | State authority | Portable or host-local | Classification |
|---|---|---|---|---|
| Ref (blocking sync reference) | Yes — `GENIA_STATE.md` "### Refs" (~L2150); `GENIA_RULES.md` §10 | Python-host-only (`threading.Condition`) | Host-local; capability `refs`, no shared-spec cases | **Definitely R25** |
| Cell (async fail-stop mailbox-of-one) | Yes — `GENIA_STATE.md` "### Cell helpers" (~L2196) | Python-host-only, capability group "Refs/Cells" | Host-local, no shared-spec cases | **Definitely R25** |
| Process (`process.*`, FIFO mailbox, fail-stop, no restart) | Yes — `GENIA_STATE.md` "### Host-backed concurrency" (~L2170) | Python-host-only, capability `process_primitives` | Host-local, no shared-spec cases | **Definitely R25** |
| Actor (prelude layer over Cell) | Yes — `GENIA_STATE.md` "### Actor helpers" (~L2239) | Python-host-only, no dedicated capability name (rides on `refs`/`process_primitives`) | Host-local | **Definitely R25**, but is *last* in the natural build order (depends on Cell) |
| `execution.process` (external OS process) | Yes — `GENIA_STATE.md` §9.40 | Portable *contract*, Python-implemented only, zero shared-spec cases | Distinct capability `execution_process` | **Already implemented by R24-adjacent work; out of scope** — a different, unrelated capability from Genia's own `process.*`; R25 must not conflate the two |
| Promise (`delay`/`force`) | Yes — `GENIA_STATE.md` §4.3 | Portable, part of the core evaluator, not host-capability-gated | Not a concurrency primitive — pure delayed/memoized values | **Not R25** — no threading/mailbox/failure-mapping story exists or is needed; including it would blur "stateful runtime" into "the whole value model" |
| Flow (lazy pull-based single-use stream) | Yes — `GENIA_STATE.md` "### Flow runtime" | Portable core runtime behavior, `flow_phase_1` capability, active shared-spec coverage | Distinct from concurrency; synchronous finalization only, explicitly "no async cancellation or scheduler involvement" | **Not R25** — R24/R27 territory (R27 explicitly owns "lazy pull-based single-use Flow phase 1... over the C++ host") |
| Lifecycle scopes (R14) | Yes — `GENIA_STATE.md` §§9.8–9.20 | Portable, Experimental, Python-implemented | Synchronous only; explicit non-goal: "no ... concurrent peer/child execution is defined" | **Prerequisite constraint, not R25 scope** — R25 must not attempt to make lifecycle concurrent; that boundary is explicitly frozen |
| Concurrency scheduling/threading | Host OS threads only, `GENIA_RULES.md` §10: "concurrency remains host-backed (threads), not language-scheduled" | N/A | Host-local by design | **Definitely R25** (as *implementation mechanics*, not new language semantics) |
| Cancellation / failure propagation | No unified mechanism — each primitive (Ref/Cell/Process/Actor/Lifecycle/Flow) defines its own local fail-stop/finalization notion; Outcome (`some`/`none`/`err`) is a value-level result type, not a cancellation token | GENIA_STATE.md, multiple sections | N/A | **Already implemented (per-primitive); no new unifying mechanism should be invented in R25** |
| Restart/supervision | Cell/Actor: single-entity restart only. Process: explicitly none. Supervision trees/links/monitors: **do not exist anywhere in the repo** | GENIA_STATE.md ~L2311, capabilities.md, R14 non-goals | N/A | **Explicitly future actor/event work — must not be pulled into R25.** `R38 — Portable Actors, Messaging and Supervision` owns supervision, restart policy, `ActorRef`, and mailbox *capacity/backpressure* as portable Genia semantics |
| Message ordering / mailbox / backpressure | FIFO per-entity mailbox exists (Process/Cell/Actor); "no cross-actor ordering," "no backpressure" explicitly listed as not guaranteed | GENIA_STATE.md ~L2304-2317 | Host-local | **R25 may harden/prove host-local FIFO behavior; must not define portable mailbox-capacity or backpressure semantics — that is R38's** |
| Deterministic vs. nondeterministic behavior | No determinism guarantee exists across concurrent entities today; this is a documented, accepted property, not a defect | GENIA_STATE.md concurrency-invariants block | N/A | **R25 should prove the C++ host reproduces the same *documented* nondeterminism boundary, not eliminate it** |
| Thread/process identity leakage | Not documented as a concern anywhere | — | — | **Unclear contract gap** — worth one explicit line in R25's contract saying host thread/process identity must not leak into any Genia-observable value, matching the existing "opaque handle" pattern used elsewhere (e.g. config providers) |
| Host resource limits | No documented limits for Ref/Cell/Process/Actor (contrast with `execution.process`'s explicit 1MiB stdout/stderr caps and 1..300000ms timeout) | — | — | **Unclear contract gap** — if C++ needs different resource bounds (e.g., a fixed thread-pool vs. Python's unbounded daemon-thread-per-entity model), that is a new host-observable difference requiring an explicit contract decision, not an implementation detail |
| Interaction with Flow | None documented; Flow and these primitives are used independently in examples (e.g. `ants_actor.genia`) | — | — | **Not R25** — no existing contract to port |
| Interaction with future R37 events / R38 portable actors | R38's own scope (`docs/strategy/roadmap/r38.md`) explicitly claims `ActorRef` identity, message/envelope contract, mailbox capacity/backpressure, and supervision as *portable Genia semantics*, and does **not** list R25 as a foundation it builds on | roadmap | — | **Boundary risk, not R25 scope** — see §7 |

---

## 3) Portable semantic dependency map

**Portable semantic dependencies (frozen, reusable, must not be reopened):**

- **Identity/equality (R18):** Ref, Cell, Process, Actor, and Promise are all
  identity-bearing runtime values — compared only by entity identity, never
  structurally, and equality never forces/dereferences them
  (`GENIA_STATE.md` §9.6 "Portable value equality"). This is already settled
  and portable; R25 inherits it unchanged.
- **Outcome/failure (R9-era Outcome model):** each primitive's fail-stop
  state is already expressed as ordinary Outcome values (`cell_error`
  returns `some(error_string)`/`none`; `actor_call` on failure returns
  `none("actor-error")`). R25 should reuse this, not invent a second
  cancellation/error channel.
- **Core IR:** none of Ref/Cell/Process/Actor/Promise introduce or require a
  Core IR node — they are ordinary prelude-backed calls over host-backed
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
  further operations) (Cell, Process, Actor)
- restart machinery (Cell, Actor only — Process explicitly has none)
- reply/one-shot synchronization for blocking calls (`actor_call`'s
  `reply_to` ref)
- C++ ownership/lifetime strategy for these entities (who frees a Cell's
  worker thread, when, and how a dangling reference from Genia code is
  prevented or diagnosed)

Per `AGENTS.md`'s Future Execution-Realization Guardrail and
`docs/architecture/execution-realization.md` (both non-authoritative
direction, read directly): infrastructure/host-mechanism detail must never
become Core IR or shared language semantics. R25's job is squarely in the
"host implementation dependencies" column; it must not manufacture new
portable semantics for mailbox capacity, backpressure, or supervision along
the way — that is explicitly R38's territory (see §7).

**What can be implemented sequentially, independent of the whole surface:**

Genia's own Python implementation already demonstrates the natural
dependency order — Actor is *literally* "prelude-backed over cells"
(`GENIA_STATE.md` "### Actor helpers (Phase 1, prelude-backed over cells)"),
and Cell/Process share no code with each other. The natural, independently
provable build order for C++ is:

1. **Ref** — simplest: one condition variable, blocking get/set/update, no
   threads-of-its-own, no fail-stop.
2. **Cell** — adds an owned worker thread, an update queue, and the
   fail-stop state machine.
3. **Process** — a sibling of Cell (own worker thread + FIFO mailbox +
   fail-stop) but *without* restart — provable independently of Cell.
4. **Actor** — a thin protocol layer *on top of* Cell (effect-shape
   validation, `reply_to` handling) — cannot start before Cell lands, but
   requires no new primitive machinery of its own.

Each of these four is independently testable, independently mergeable, and
independently auditable — exactly the shape the numeric-gate postmortem
recommends ("multiple independently mergeable PRs against current `main`...
[each establishing] one narrow invariant").

---

## 4) Conformance/evidence map (Phase 3, reusing R16/`executable-semantic-conformance.md` — no second framework invented)

Applying the existing 7-part obligation
(`docs/architecture/executable-semantic-conformance.md`) to each candidate
R25 unit:

| Unit | Authority | Boundary | Executable proof today | Applicability (capability) | Host evidence needed | Truth sync | Ambiguity stop |
|---|---|---|---|---|---|---|---|
| Ref | `GENIA_STATE.md` "### Refs" prose | Capability/provider contract (opaque handle value), not Core IR | **None** — no shared-spec case exists | `refs` (registered, unused) | New host-local test coverage proving blocking/wake semantics under a real second thread (Python's own `tests/test_invariant_concurrency.py` Ref assertions are the closest existing template, but they are pytest, not shared-spec) | `docs/host-interop/capabilities.md`, `HOST_CAPABILITY_MATRIX.md`, `spec/manifest.json` only if/when shared cases are added | **Yes — stop here first.** Whether `refs`/`process_primitives`/an eventual `actor_primitives` should ever gain real shared-spec cases, or are intentionally permanent Python-host-only conveniences a second host may freely choose to skip, is not decided anywhere in the repo. R25 cannot honestly produce "evidence-based capability claims" without this decision. |
| Cell | `GENIA_STATE.md` "### Cell helpers" prose | Capability/provider contract | None | `refs`/`process_primitives` group (imprecise fit — no dedicated `cells` name) | Same gap as Ref, plus fail-stop/restart-specific determinism proof | Same docs | Same ambiguity stop; additionally, no capability name cleanly names "Cell" today — worth a naming decision before claiming support |
| Process | `GENIA_STATE.md` "### Host-backed concurrency" prose | Capability/provider contract | None | `process_primitives` | FIFO-ordering and permanent-fail-stop proof under real concurrent senders | Same docs | Same ambiguity stop |
| Actor | `GENIA_STATE.md` "### Actor helpers" prose | Capability/provider contract, layered over Cell | None | No dedicated name | Effect-shape validation, `actor_call` blocking-reply correctness, and the same fail-stop propagation-from-Cell proof | Same docs | Same ambiguity stop; also depends on Cell's own evidence model being settled first |

**Conclusion for this phase:** every single R25 candidate unit hits the same
"Ambiguity stop" at step 7 of the conformance framework — the applicability
and host-evidence questions cannot be answered honestly until the repo
decides what "evidence-based capability claims" means for a family of
primitives that has *never* had shared-spec coverage, even in the reference
Python host. This should be resolved as its own small, focused design step
(most naturally the first R25 epic's contract phase) rather than assumed
away.

---

## 5) Contract/evidence gaps found

1. **No shared-spec existence for Ref/Cell/Process/Actor in any host,
   including Python.** `spec/` has zero cases requiring `refs` or
   `process_primitives`, confirmed by direct grep. R25's candidate wording
   ("evidence-based capability claims") presupposes evidence infrastructure
   that does not exist yet, for any host.
2. **No capability name exists for Cell or Actor specifically** — only
   `refs` and `process_primitives` are registered; Cell and Actor ride
   informally under those or under no name at all.
3. **No documented resource-limit contract** for Ref/Cell/Process/Actor
   (contrast `execution.process`'s explicit byte/timeout caps). If C++'s
   natural implementation shape differs from Python's "unbounded daemon
   thread per entity" model, that is an undecided, currently-invisible
   contract question.
4. **R25's roadmap wording uses "mailbox"** in a way that is not clearly
   fenced off from R38's own claimed "mailbox capacity and backpressure are
   contract concerns" territory. R25's non-goals list supervision and
   distributed actors but does not explicitly disclaim ownership of mailbox
   *capacity/backpressure semantics* — an encroachment risk on a
   later-numbered, dependency-order-sensitive release.
5. **R25 sits inside `killer-workflow.md`'s explicit parking-lot list**
   ("actors / process-level concurrency," "lifecycle machinery" — "Unless
   explicitly approved, route proposals in these areas to parking lot").
   R24, R7, R8, and R14 all proceeded as *explicitly approved infrastructure
   work* outside the strict killer-workflow priority — R25 needs the same
   explicit-approval framing recorded somewhere, not silent inheritance from
   the roadmap's mere existence.
6. **Sequence diagram vs. dependency-chain discrepancy (found during
   sequencing review, not directly an R25 gap but relevant to "downstream
   impact through R41"):** `docs/strategy/roadmap/sequence.md`'s diagram
   chains R37→R38→R39→R41 directly and places **R40 — Configuration and
   Secret Hardening and Ergonomics outside the dependency chain entirely**,
   with an explicit note that "reservation number does not imply dependency
   on R14–R39 or R41." This is intentional per the document's own prose, not
   an error — but it means the "expected" R37→R38→R39→R40→R41 straight
   chain from this preflight's own brief is not what the roadmap actually
   specifies. No edit is proposed; this is flagged for awareness only, since
   it affects how a reader should interpret "downstream impact through R41."

---

## 6) R24 lessons applied to R25

From `docs/analysis/exact-numeric-gate-postmortem.md` and the R24 epic
history (`docs/strategy/roadmap/e24-issue-sequence.md`,
`docs/design/r24-cpp-host-preflight.md`, `docs/design/r24/*`):

- **Root cause of the pre-R24 failure:** "treating a multi-subsystem
  language change as a prerequisite gate instead of admitting that it was a
  sequence of releases." R25's candidate scope currently bundles four
  subsystems (Ref/Cell/Process/Actor) the same way the pre-R24 numeric gate
  bundled source-classification/runtime/rendering/JSON/formatting. The fix
  used there (splitting into R21/R22/R23) is the same fix this preflight
  recommends for R25 — but applied *before* any implementation branch opens,
  not after a failed one.
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
  numeric-kind burden was, even though the *subsystem count* (4) is similar.
- **Portability-obligation fan-out is lower for R25.** R24 had to satisfy
  mandatory portable obligations accumulated across R17–R23
  (`docs/design/r24/portability-obligation-map.md`). Ref/Cell/Process/Actor
  carry no such mandatory portable obligation — they are optional,
  Python-host-only capabilities today. This cuts against R25 being
  "R24-sized" in the numeric sense, but it does not remove the
  evidence-infrastructure gap identified in §5.
- **Diagnostic-normalization discipline still applies.** R24 needed a
  dedicated adversarial epic (E24-5) purely to prove no raw host exception
  text leaked. Any C++ fail-stop error string for Ref/Cell/Process/Actor
  needs the same discipline — this belongs inside each primitive's own
  epic, not as a separate release-ending sweep, since the surface is much
  smaller per primitive than R24's numeric diagnostic surface was.

**Net comparison:** R25 shares R24's *structural* risk (multiple semantic
subsystems bundled under one release name) but not its *magnitude* risk
(native-primitive complexity, mandatory cross-host obligation fan-out). The
correct response, per the postmortem's own "why this is better" reasoning,
is the same regardless of magnitude: decompose before starting, not after a
branch grows unreviewable.

---

## 7) Release-size assessment

Using the qualitative scale requested (small / medium / large /
release-threatening):

- **Ref alone:** small.
- **Cell alone:** small–medium (adds the fail-stop state machine and
  restart semantics).
- **Process alone:** small (sibling of Cell, simpler — no restart).
- **Actor alone:** small (thin protocol layer over an already-proven Cell).
- **Cross-cutting deterministic stress/race test harness + evidence-based
  capability declaration, across all four:** medium on its own, and it
  cannot start honestly until the §5 evidence-infrastructure gap is
  resolved.
- **R25 as currently worded, attempted as one undifferentiated release:**
  **large, trending toward release-threatening** — not because any one
  primitive is complex, but because of subsystem count (4 independent
  concurrency models), an unresolved evidence-infrastructure question that
  touches all four simultaneously, and a live boundary risk against R38's
  claimed mailbox/supervision territory. This is exactly the failure-mode
  checklist from Phase 4: "too many independent failure models" (Ref has
  none, Cell/Process/Actor each have their own distinct fail-stop shape),
  "too many host subsystems" (mutex+condvar, worker-thread+queue×2,
  reply-protocol), and "inability to audit one coherent claim at release
  end" (a single R25 audit would have to certify four unrelated concurrency
  models plus a not-yet-existing evidence model, all at once).
- **R25 decomposed into epics along the four-primitive natural build order
  (§3), with the evidence-infrastructure question resolved as its own first
  contract step:** each epic is small, and the release as a whole becomes
  medium — comparable to R24's own realized shape (8 small-to-medium
  epics), not release-threatening.

---

## 8) Recommended decomposition

**Outcome C — keep R25 as the umbrella release name and roadmap position,
define independently completable sub-releases (epics) beneath it.**
Renumbering R25 into R25a/R25b/R25c as separate numbered releases (Outcome
B) is not recommended: it would force downstream renumbering pressure on
R26 onward and the fixed R37–R41 sequence for no compensating benefit, since
R25's subsystems share one coherent umbrella claim ("the C++ host has a
provably equivalent stateful/concurrency primitive layer") even though they
should land as separate PRs.

Proposed epic sequence (mirroring `e24-issue-sequence.md`'s own discipline,
each independently mergeable and independently audited, no epic beginning
before its predecessor's audit passes):

- **E25-0 (contract):** Resolve the §5 evidence-infrastructure ambiguity
  stop. Decide and record whether Ref/Cell/Process/Actor ever gain real
  shared-spec cases (and if so, what a host-neutral fixture for
  thread/timing-observable behavior even looks like — this is genuinely
  hard, since these primitives are inherently host-thread-timing-dependent
  in a way eval/cli/flow cases are not), or whether "evidence-based
  capability claims" means something narrower (e.g., a documented host-local
  deterministic test suite plus explicit capability-matrix rows, without a
  cross-host shared-spec requirement). This decision gates every later
  epic's "host evidence" column.
- **E25-1:** C++ Ref — ownership/lifetime strategy, blocking get/set/update,
  no threads-of-its-own beyond the caller's, deterministic wake proof.
- **E25-2:** C++ Cell — worker thread + update queue + fail-stop state
  machine + restart, deterministic ordering and failure-preservation proof.
- **E25-3:** C++ Process — worker thread + FIFO mailbox + fail-stop (no
  restart), deterministic ordering proof.
- **E25-4:** C++ Actor — effect-shape validation and `actor_call`
  reply-blocking layered over the now-proven Cell, matching Python's
  documented effect shapes (`["ok", ...]`, `["reply", ...]`,
  `["stop", ...]`) exactly.
- **E25-5:** Cross-cutting deterministic stress/race hardening across all
  four, diagnostic-normalization audit (no raw C++/OS exception text
  crossing the Genia boundary), and capability-matrix/manifest truth sync
  per whatever E25-0 decided.
- **E25-6:** Release completion evidence and independent skeptical audit
  (matching R24's own E24-8 shape).

**Boundary tightening recommended for the roadmap text itself (not made in
this pass — see §13):** add one explicit line to R25's non-goals in
`docs/strategy/roadmap/r25-r29.md` disclaiming ownership of mailbox
*capacity and backpressure semantics*, since R38's own scope document
already claims that exact phrase as its contract concern.

---

## 9) Exact proposed release sequence

**No renumbering proposed.** The recommendation preserves the existing
numbering exactly:

```
R24 — C++ Minimal Conforming Host                         (in progress)
R25 — C++ Stateful Runtime and Concurrency                (umbrella; epics E25-0..E25-6 as above)
R26 — C++ REPL and Data Bridges                           (unchanged; independent of R25 per roadmap)
R27 — C++ Flow, Pipe Mode, and HTTP Serving               (unchanged; depends on R24 + any approved R25/R26 behavior)
...
R37 — Unified Events and Subscriptions                    (unchanged)
R38 — Portable Actors, Messaging and Supervision          (unchanged; does not list R25 as a foundation — confirmed)
R39 — Genia-Native Conformance Tooling                    (unchanged)
R40 — Configuration and Secret Hardening and Ergonomics   (unchanged; intentionally outside the R37→R41 dependency chain per sequence.md)
R41 — Portable Core IR Artifacts                          (unchanged)
```

This preserves numbering stability exactly as instructed and requires no
edits to `sequence.md`, `release-roadmap.md`, or `r25-r29.md`'s title/number
— only (optionally, and not made in this pass) an added non-goal sentence
inside R25's existing entry.

---

## 10) Smallest first post-R24 release

**E25-1 — C++ Ref: ownership/lifetime and blocking synchronization only.**

- **One headline semantic claim:** "The C++ host provides a Ref primitive
  whose blocking get/set/update behavior is observably equivalent to the
  Python reference host's documented behavior, under an explicit,
  documented C++ ownership/lifetime strategy."
- **Explicit prerequisites:** E25-0's evidence-model decision must be
  recorded first (even if the answer is "host-local test suite only, no
  shared-spec case yet").
- **Explicit exclusions:** no Cell, Process, or Actor; no restart semantics
  (Ref has none to begin with); no mailbox; no fail-stop; no new Core IR;
  no new manifest capability claim beyond what E25-0 authorizes; no
  attempt to make Lifecycle scopes concurrent.
- **Bounded capability/evidence surface:** exactly the `refs` capability
  group's `ref.create/get/set/update` operations, per
  `docs/host-interop/capabilities.md`'s existing "Group: Refs / Cells"
  definition — no new names invented.
- **Executable conformance target:** whatever E25-0 decides — at minimum, a
  deterministic host-local test proving a blocking `ref_get` call is
  unblocked by a concurrent `ref_set` from a second thread, with no timeout
  and no busy-wait, matching the documented "blocks the calling thread
  indefinitely... `ref_set` wakes all blocked waiters" contract.
- **Vertical proving case:** a small C++ program with two threads — one
  blocks on an unset Ref, the other sets it after a delay — producing the
  same observable value the Python reference host produces for the
  equivalent Genia program.
- **Clear completion criteria:** ownership/lifetime strategy documented;
  blocking/wake semantics proven deterministic under a thread sanitizer (no
  data races, no UB); no leaked host thread/handle identity into any
  Genia-observable value; independent audit passes.
- **Skeptical audit gate:** a fresh audit (not the implementer) confirms the
  above against `genia-cpp`'s actual merged code, following the same
  "audit runs against merged main, defects become small repair PRs" pattern
  the postmortem recommends.

A reviewer can verify this acceptance statement without saying "and also all
the rest of concurrency" — it says nothing about Cell, Process, Actor,
mailboxes, or evidence-model completeness beyond Ref itself.

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
- propose actor/event/supervision *language* semantics — that is R38's
  scope, explicitly out of reach here
- resolve the E25-0 evidence-model question itself — that is flagged as the
  first required follow-up (§13), not answered by this document

---

## 12) Risks / regret checks

- **Regret risk if R25 is kept as one undifferentiated release anyway:**
  repeats the pre-R24 numeric-gate failure mode at smaller absolute scale
  but identical structural shape — a single long-lived branch touching four
  unrelated concurrency models, with audit findings evaluated against an
  already-far-diverged branch.
- **Regret risk if R25 is split into separately *numbered* releases:**
  forces renumbering pressure on R26 onward and the fixed R37–R41 sequence
  for no real benefit, since the four primitives share one coherent
  umbrella completion claim and a natural dependency order (Ref→Cell→
  Process→Actor) that an umbrella-with-epics structure already expresses
  cleanly.
- **Regret risk if the E25-0 evidence-model question is skipped:** every
  later epic's "evidence-based capability claim" becomes an unfalsifiable
  assertion — exactly the outcome R16's conformance framework exists to
  prevent. This is the single highest-priority follow-up.
- **Regret risk if R25's non-goals are not tightened against R38:** a
  future R25 epic could accidentally define portable mailbox-capacity or
  backpressure semantics "for C++'s own good," which R38 would then have to
  either adopt as prior art it didn't choose or explicitly overrule —
  either way, wasted or contested work.
- **Regret risk if R25 proceeds without an explicit approval note** (the
  same kind R7/R8/R14 received) despite sitting inside
  `killer-workflow.md`'s named parking-lot categories: a future audit could
  reasonably ask why parking-lot-classified work shipped without the
  explicit-approval trail the process expects.

---

## 13) Required follow-up architecture/contracts

1. **E25-0 contract step (highest priority):** decide what "evidence-based
   capability claims" concretely means for Ref/Cell/Process/Actor, given
   zero existing shared-spec coverage in any host. This is a design
   question, not an implementation one, and should be resolved before any
   C++ code is written under the R25 name.
2. **Capability-naming decision:** whether Cell and Actor need their own
   `spec/manifest.json` capability names, or continue riding informally
   under `refs`/`process_primitives`.
3. **One added non-goal sentence in `docs/strategy/roadmap/r25-r29.md`**
   disclaiming R25 ownership of mailbox capacity/backpressure *semantics*,
   to pre-empt the R38 boundary risk identified in §5 and §7. (Not made in
   this pass, per the instruction to report before editing broadly —
   offered here as the exact, minimal, non-renumbering edit a maintainer
   could apply.)
4. **Resource-limit contract decision:** whether C++'s Ref/Cell/Process/Actor
   implementation may use a different threading/resource model than
   Python's "unbounded thread per entity," and if so, what observable
   contract (if any) constrains that difference.
5. **Explicit approval record** for R25 proceeding despite
   `killer-workflow.md`'s parking-lot classification of "actors /
   process-level concurrency" and "lifecycle machinery" — mirroring how R7,
   R8, and R14 recorded explicit approval as infrastructure work outside the
   strict killer-workflow priority.

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

**Yes, structurally — but the risk is preventable and the fix is cheap.**
R25 bundles four independent concurrency subsystems (Ref, Cell, Process,
Actor) under one release name, exactly the "multi-subsystem gate" shape
Genia's own postmortem already diagnosed as unsafe for the pre-R24 numeric
work. Unlike that numeric work, R25's individual subsystems are smaller
(standard-library threading primitives, not hand-built bignum/Decimal
machinery) and carry no mandatory cross-host portability obligation today —
so the *magnitude* of the risk is lower than R24's was. But the *shape* of
the risk — one release-sized audit trying to certify several unrelated
failure models at once, on top of an evidence-infrastructure question that
has never been answered for any of them — is the same shape, and R25's own
wording does not yet decompose it. Doing so now, before any implementation
branch opens (via the epic sequence in §8), converts a large,
trending-release-threatening bundle into a medium release built from four
small, independently auditable slices — the same correction R21/R22/R23
already proved works for exact numerics, and the same correction R24 was
itself decomposed into eight epics to apply.
