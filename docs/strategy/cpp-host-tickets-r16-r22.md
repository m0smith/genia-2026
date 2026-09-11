# Ticket-Ready Drafts: R16–R22 (C++ Host Porting Readiness)

Status: **Superseded — not adopted, kept for historical drafting evidence
only.** The current, approved R16 numbering and scope is
`docs/strategy/roadmap/r16-r20.md` (epic #756) and its E16-0 contract,
`docs/design/r16-multi-host-conformance-infrastructure-contract.md` (issue
#757). That numbering no longer matches this draft one-to-one: current R16
is the broader Multi-Host Conformance Infrastructure release described
there (not "spec-runner protocol only"), current R20 is Open Functions and
Extensible Pattern Dispatch (a language feature, not C++ bring-up), and
current R21 is the first C++ host release, absorbing what this draft called
R19. The technical reasoning below (subprocess protocol need, C++ bring-up
ordering) informed the current contract and is preserved as history; do not
treat any release number or ticket text below as active.

Original status: **Proposal drafts — not filed as GitHub issues.** Written in the exact shape `docs/process/08-roadmap-ticketing.md` requires for a ticket, ready to paste into GitHub issues by whoever has push access. Source plan: `docs/strategy/cpp-host-release-plan-r16-r22.md`. Per that doc and `docs/process/08-roadmap-ticketing.md`, nothing here is authoritative or committed — these still need approval before filing, let alone implementation.

Ticket ordering follows the required dependency order: contract/spec clarification → failing tests/specs → minimal implementation → docs sync → audit/truth review → migration/follow-up. R16–R18 are contract/infrastructure; R19–R22 are implementation.

---

## Ticket: R16 — Multi-Host Spec Runner Protocol

**Release target:** R16 (new, proposed)
**Roadmap alignment:** Required infrastructure — blocking prerequisite for any second host (C++ or otherwise); not part of the current or next feature release.

**Problem statement:** `tools/spec_runner` only drives `hosts/python/adapter.py` in-process. `GENIA_STATE.md` states plainly that no generic multi-host runner exists and all conformance is validated against the Python reference host only. Without a subprocess-based (or equivalent) adapter protocol, a second host has no way to prove conformance against the shared `spec/` suite except ad hoc, one-off comparison scripts — which don't scale and don't get maintained.

**Scope includes:**
- Define a subprocess adapter protocol: spec case in, normalized result out (e.g. one JSON envelope over stdin/stdout, or a documented small CLI contract per category).
- Add a `--host <path-or-command>` (or equivalent) mode to `tools/spec_runner` that speaks this protocol against an external process, alongside the existing in-process Python path.
- Document the protocol in `tools/spec_runner/README.md`, cross-referenced from `docs/host-interop/HOST_PORTING_GUIDE.md`.
- Wire the existing Python host through the new protocol as its own conformance check, proving the protocol works before any second-host code exists.

**Scope excludes:**
- Any second host implementation (C++, Node, Java, Rust, Go).
- Expanding spec category coverage (flow/error/parse phase stays as-is).
- Any change to Core IR or language semantics.

**Affected docs/tests/specs:** `tools/spec_runner/README.md`, `docs/host-interop/HOST_PORTING_GUIDE.md`, `spec/manifest.json` (if the host contract shape changes), no changes to `spec/*/*.yaml` case content.

**Acceptance criteria:** The Python host's existing conformance is provably unchanged when run through the new subprocess protocol path (same pass/fail counts as the in-process path); protocol is documented well enough that a from-scratch implementer could write a conforming adapter without reading `tools/spec_runner`'s source.

**Non-goals:** Building a "universal" host SDK/library — just the wire protocol and one runner-side implementation of it.

**Risk of drift:** Low — this is infrastructure with no observable-behavior surface; the main risk is under-specifying the protocol and having to revise it once a real second host (R19) starts using it.

**Required process phases:** contract/spec clarification (protocol design) → minimal implementation → docs sync.

---

## Ticket: R17 — Numeric & Ordered-Container Portability Contract

**Release target:** R17 (new, proposed)
**Roadmap alignment:** Required infrastructure, depends on R16.

**Problem statement:** Genia integers are Python's arbitrary-precision ints; nothing in `GENIA_RULES.md`/`GENIA_STATE.md` states general integer overflow behavior outside the JSON boundary (which caps at `±9007199254740991`, a JSON-specific limit, not a general integer contract). Map insertion-order preservation is implied by `map_items`/`map_keys`/`map_values` behavior and by Python dict semantics, but never stated as a general portable runtime guarantee. A second host has no documented target to implement against for either.

**Scope includes:**
- Document explicit integer semantics in `GENIA_STATE.md`/`GENIA_RULES.md`: arbitrary-precision requirement, or an explicit fixed-width-plus-overflow-behavior decision if arbitrary precision turns out not to be required generally.
- Document an explicit, general map-ordering contract (not just the JSON-boundary-adjacent implications already documented).
- Add `spec/eval` and/or `spec/ir` cases exercising large-integer arithmetic beyond JSON-boundary limits, and map insertion-order preservation across mutation-adjacent operations, executable against the Python reference host via the R16 protocol.

**Scope excludes:**
- Any second-host implementation work.
- Changing the existing JSON-boundary integer limits.

**Affected docs/tests/specs:** `GENIA_STATE.md`, `GENIA_RULES.md`, `docs/architecture/core-ir-portability.md` (if either contract touches lowering-level representation), new `spec/eval`/`spec/ir` cases.

**Acceptance criteria:** New spec cases pass against the Python reference host via R16's protocol; the integer and map-ordering contracts are stated precisely enough that a from-scratch C++ implementation could be reviewed for conformance without asking the Python source what it "really" does.

**Non-goals:** Deciding what data structure or library a future C++ host uses (ordered-map library choice, bignum library choice) — that's an R19 implementation decision, this ticket only fixes the observable contract.

**Risk of drift:** Medium — if the arbitrary-precision-integer contract is written loosely, a C++ host in R19 could pick a fixed-width representation that passes today's spec cases but silently diverges on inputs the spec doesn't yet cover.

**Required process phases:** contract/spec clarification → failing tests/specs → docs sync.

---

## Ticket: R18 — String/Unicode, Float Formatting & Error-Text Portability Contract

**Release target:** R18 (new, proposed)
**Roadmap alignment:** Required infrastructure, depends on R16.

**Problem statement:** `src/genia/utf8.py`'s codepoint iteration, byte-boundary checks, and slicing assume Python's code-point-indexed `str`, with no host-neutral contract written down. Float display formatting (Python's shortest-round-trip repr) has no documented target a C++ host's `printf`/`iostream`-based formatting could conform to. Error message text asserted byte-for-byte in `spec/error`/`spec/eval` exists only as hand-formatted Python strings, with no shared, language-neutral source of truth.

**Scope includes:**
- Document exact codepoint/UTF-8 boundary/slice semantics as a portable contract.
- Document an exact float display-formatting spec (which rounding/precision rule, e.g. shortest round-trip vs. fixed rules) with spec coverage for edge cases (very large/small magnitudes, exact zero, negative zero if applicable).
- Inventory error message templates for categories already asserted in `spec/error`/`spec/eval`; where feasible, extract them into a shared, language-neutral source (data file or generation step) both a Python and future C++ host can read from, rather than two independently hand-maintained string sets.
- Expand `spec/parse`, `spec/eval`, `spec/error` coverage for non-ASCII codepoint boundaries and float formatting edge cases.

**Scope excludes:**
- Any second-host implementation work.
- Redesigning error categories or structure — text-content portability only, within the existing strict error normalization from Phase 2.

**Affected docs/tests/specs:** `src/genia/utf8.py` (contract extraction, not necessarily code change), `GENIA_STATE.md`/`GENIA_RULES.md`, new/expanded `spec/parse`/`spec/eval`/`spec/error` cases.

**Acceptance criteria:** Float formatting and codepoint-boundary contracts are precise enough to implement from the doc alone; error-message extraction (if pursued) doesn't change any currently-asserted `stdout`/`stderr` spec expectations.

**Non-goals:** Choosing the C++ host's Unicode library (ICU vs. hand-rolled) — that's an R19 decision.

**Risk of drift:** Medium-high — this is the largest surface area of "currently Python-only incidental behavior" in the whole plan; under-scoping it risks R19 discovering contract gaps mid-implementation.

**Required process phases:** contract/spec clarification → failing tests/specs → docs sync.

---

## Ticket: R19 — C++ Host Bring-up: Minimal Host

**Release target:** R19 (new, proposed)
**Roadmap alignment:** Depends on R16, R17, R18. First release that writes actual C++ code.

**Problem statement:** `hosts/cpp/` exists only as a template-derived scaffold (`README.md`/`AGENTS.md`, both "planned, no implementation yet"). No C++ code exists. `docs/host-interop/HOST_CAPABILITY_MATRIX.md`'s C++ column is "Not Implemented" across every row.

**Scope includes:**
- C++ lexer/parser for current documented surface syntax.
- Lowering into the minimal portable Core IR node/pattern families frozen in `docs/architecture/core-ir-portability.md`.
- Core IR evaluator covering non-capability-backed runtime semantics (literals, options, binary/unary ops, pipelines, case/pattern matching, lambdas, function defs).
- Integer and ordered-map representation chosen per R17's contract.
- CLI file mode, `-c` command mode, raw `argv()` access.
- Prelude autoload/loading (the prelude itself needs no porting — only the loader).
- `help(name)` support for documented public helpers.
- Build system/tooling selection (CMake + package manager) with real, non-TODO setup/build/test/lint commands in `hosts/cpp/README.md`.
- Passes `spec/parse`, `spec/ir`, `spec/eval` shared cases via the R16 multi-host runner protocol.
- `hosts/template/CAPABILITY_STATUS.md` copied into `hosts/cpp/` and kept truthful as capabilities land.
- `docs/host-interop/HOST_CAPABILITY_MATRIX.md` C++ column updated only for what's actually implemented and spec-passing.

**Scope excludes:** Pipe mode, REPL, Flow, HTTP serving, refs, processes, bytes/json/zip bridge, debugger stdio (all deferred to R20/R21/R22); anything requiring the memory/concurrency model designed in R20.

**Affected docs/tests/specs:** New `hosts/cpp/` source tree; `hosts/cpp/README.md`, `hosts/cpp/AGENTS.md`, `hosts/cpp/CAPABILITY_STATUS.md`; `docs/host-interop/HOST_CAPABILITY_MATRIX.md`.

**Acceptance criteria:** `spec/parse`/`spec/ir`/`spec/eval` pass against the C++ host through the R16 runner at parity with the Python host's results on the same cases; capability matrix and status doc reflect exactly what's implemented, nothing more.

**Non-goals:** Any capability requiring I/O, concurrency, or network access.

**Risk of drift:** High if R17/R18 contracts are incomplete — this is where every gap in those tickets gets discovered the hard way, mid-implementation.

**Required process phases:** minimal implementation → docs sync → audit/truth review.

---

## Ticket: R20 — C++ Host: Memory & Concurrency Model for Refs, Cells, and Processes

**Release target:** R20 (new, proposed)
**Roadmap alignment:** Depends on R19.

**Problem statement:** Python's refs/cells/processes ride on refcounting+cycle GC plus threading, and Python's GIL serializes much of what looks like concurrent behavior. C++ gets none of this for free. Deciding this ad hoc while implementing individual `spec/eval` ref/cell/process cases risks an inconsistent, retrofitted design.

**Scope includes:**
- Explicit ownership/lifetime model decision for Genia values in the C++ host (candidates: `shared_ptr` with a cycle-breaking strategy for closures/cells, arena/region allocation, tracing GC), documented as a host-local design decision per `HOST_PORTING_GUIDE.md`'s "internals may differ" allowance.
- Concurrency primitive mapping (`std::thread`/mutex/condvar or equivalent) preserving `src/genia/lifecycle_scope.py`/`lifecycle_plan.py` semantics (the R4/R8/R14 lifecycle contracts) without redefining them.
- A race/stress test pass specifically probing for behavior Python's GIL masked but true parallelism could expose.
- `refs` and `cell`/`process` primitives implemented in C++, passing relevant `spec/eval` cases.

**Scope excludes:** HTTP serving, bytes/json/zip bridge (R21/R22); any change to the lifecycle contract itself — this release implements it, doesn't redesign it.

**Affected docs/tests/specs:** `hosts/cpp/` source tree; `hosts/cpp/AGENTS.md` (document the chosen memory model as host-local); `docs/host-interop/HOST_CAPABILITY_MATRIX.md`.

**Acceptance criteria:** `refs`/`cell`/`process` spec cases pass; stress-test suite specifically targeting concurrent access patterns exists and passes reproducibly (not flaky).

**Non-goals:** General-purpose garbage collector benchmarking or optimization — correctness and lifecycle-contract preservation only.

**Risk of drift:** High — this is the single largest design-freedom area of the whole plan; a rushed decision here is expensive to unwind after R21/R22 build on top of it.

**Required process phases:** contract/spec clarification (memory model design note) → minimal implementation → docs sync → audit/truth review.

---

## Ticket: R21 — C++ Host: CLI Pipe Mode, REPL, and Bytes/JSON/Zip Bridge

**Release target:** R21 (new, proposed)
**Roadmap alignment:** Depends on R19; benefits from but does not strictly require R20.

**Problem statement:** Rounding out optional capabilities that don't require R20's concurrency model, so C++ host capability parity can progress without waiting on the largest design item.

**Scope includes:**
- `-p`/`--pipe` CLI mode.
- REPL.
- Bytes/json/zip bridge, using C++ libraries chosen to match already-spec'd limits (duplicate-key rejection, 128-container nesting cap, safe-integer range) rather than a generic library's default behavior.
- Expanded `spec/cli` coverage exercised against the C++ host via the R16 runner.
- Capability matrix and `CAPABILITY_STATUS.md` updated.

**Scope excludes:** Flow, HTTP serving (R22); debugger stdio (parking lot unless separately prioritized).

**Affected docs/tests/specs:** `hosts/cpp/` source tree; `docs/host-interop/HOST_CAPABILITY_MATRIX.md`; `spec/cli`.

**Acceptance criteria:** `spec/cli` pipe-mode cases pass at parity with Python host; JSON/zip bridge enforces the same limits as the Python host on malformed input (verified with cases the Python host currently rejects).

**Non-goals:** Performance tuning of the bridge implementations.

**Risk of drift:** Medium — library-default behavior for JSON/zip parsing is the main trap; needs explicit verification against Genia's stricter limits, not just "does it parse valid JSON."

**Required process phases:** minimal implementation → docs sync.

---

## Ticket: R22 — C++ Host: Flow Runtime & HTTP Serving Parity

**Release target:** R22 (new, proposed)
**Roadmap alignment:** Depends on R19, R20, R21. Closes capability parity for this plan.

**Problem statement:** The two largest remaining capability surfaces — Flow and HTTP serving — are the last gap between the C++ host and the Python reference host's capability matrix.

**Scope includes:**
- Flow phase 1 runtime (lazy, pull-based, single-use) in C++, passing first-wave `spec/flow` cases.
- Synchronous blocking HTTP serving bridge preserving request/response map shapes, exact-path routing, and CORS preflight behavior documented in `capabilities.md`.
- Full `docs/host-interop/HOST_CAPABILITY_MATRIX.md` C++ row review — every capability marked `Implemented` only where code, tests, and spec coverage all exist.
- Final audit pass comparing C++ and Python hosts on the full active shared spec suite.

**Scope excludes:** Python-host-only capabilities not yet promoted to shared/portable status (deterministic model fixture, Gemini REST adapter, deterministic embedding fixture, allowlisted host interop, resource-io beyond `fs`) — these stay Python-host-only until a separate roadmap decision promotes them.

**Affected docs/tests/specs:** `hosts/cpp/` source tree; `docs/host-interop/HOST_CAPABILITY_MATRIX.md`; `spec/flow`.

**Acceptance criteria:** First-wave `spec/flow` cases and HTTP serving cases pass at parity with the Python host; capability matrix accurately reflects final state; full active shared spec suite (all six categories) passes on both hosts via the R16 runner.

**Non-goals:** Promoting any Python-host-only capability to shared status — that's a separate future roadmap decision, not implied by C++ reaching parity on the currently-shared capabilities.

**Risk of drift:** Medium — mostly integration risk (does everything built in R19–R21 actually compose correctly) rather than new design risk.

**Required process phases:** minimal implementation → docs sync → audit/truth review → migration/follow-up (capability-promotion decisions, if any, become their own future tickets).
