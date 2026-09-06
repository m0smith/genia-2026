# Proposed Releases R16–R22: C++ Host Porting Readiness

Status: **Proposal — non-authoritative, not adopted.** This is a draft sequencing exercise, styled to match `docs/strategy/release-roadmap.md`. Per `docs/process/08-roadmap-ticketing.md`, nothing here becomes real work until it goes through roadmap ticketing and is explicitly approved; no release below should be treated as implemented or committed. R15 (Validated Value Modeling) is drafted but not yet merged into the main roadmap file at review time, so this plan starts at R16 to avoid colliding with it — renumber if R15 lands differently.

Source: `docs/analysis/cpp-host-porting-readiness.md` (this project), which reviewed `hosts/cpp/`, `docs/host-interop/*`, `docs/architecture/core-ir-portability.md`, and `spec/` against what a real C++ implementation would need beyond the current generic porting checklist.

Sequencing follows the dependency order `docs/process/08-roadmap-ticketing.md` requires: contract/spec clarification → failing tests/specs → minimal implementation → docs sync → audit/truth review → migration/follow-up. Each release is small enough to ticket independently. R16–R18 are host-agnostic infrastructure/contract work that benefits every planned host (Node, Java, Rust, Go — all currently scaffolded placeholders), not just C++; R19–R22 are C++-specific bring-up.

---

## Release R16 — Multi-Host Spec Runner

Theme:

> Give any second host a way to prove conformance without hand-rolled comparison scripts.

This is the load-bearing prerequisite. `tools/spec_runner` currently drives `hosts/python/adapter.py` in-process only; `GENIA_STATE.md` states plainly that no generic multi-host runner exists. Nothing else in this plan is verifiable without it.

Deliverables:

- a defined subprocess adapter protocol (spec case in, normalized result out — e.g. one JSON envelope over stdin/stdout, or a small documented CLI contract) that `tools/spec_runner` can drive against *any* host binary, not just the in-process Python adapter
- `tools/spec_runner` gains a `--host <path-or-command>` (or equivalent) mode that speaks this protocol, alongside the existing in-process Python path
- protocol documented in `tools/spec_runner/README.md` and cross-referenced from `docs/host-interop/HOST_PORTING_GUIDE.md`
- the existing Python host wired through the new protocol as its own conformance check (proves the protocol works before any C++ code exists)
- `spec/manifest.json` updated if the host contract changes

Excluded:

- any second host implementation
- expanding spec category coverage (flow/error/parse remain at current phase)
- changing Core IR or language semantics

---

## Release R17 — Numeric & Ordered-Container Portability Contract

Theme:

> Stop letting "whatever Python does" stand in for a numeric and container contract other hosts can actually implement.

Deliverables:

- explicit integer semantics documented in `GENIA_STATE.md`/`GENIA_RULES.md`: arbitrary-precision requirement (not just the JSON-boundary safe-integer range that's already spec'd), or an explicit fixed-width + overflow-behavior decision if arbitrary precision is not required generally
- explicit map ordering contract stated as a general runtime guarantee (today it's implied by `map_items`/`map_keys`/`map_values` behavior and by Python dict semantics, not stated as a portable requirement)
- new `spec/eval/` and/or `spec/ir/` cases exercising large-integer arithmetic (beyond JSON-boundary limits) and map insertion-order preservation across mutation-adjacent operations, executable against the Python reference host
- `docs/host-interop/capabilities.md` / `core-ir-portability.md` updated if either contract touches those documents

Excluded:

- any C++ implementation work
- changing existing JSON-boundary limits

Depends on: R16 (so the new spec cases are runnable in a form future hosts can execute, not just Python-internal pytest).

---

## Release R18 — String/Unicode, Float Formatting & Error-Text Portability Contract

Theme:

> Make the three things spec cases already assert byte-for-byte (`stdout`, `stderr`, codepoint behavior) into contracts a non-Python host can actually reproduce.

Deliverables:

- exact codepoint/UTF-8 boundary/slice semantics currently implicit in `src/genia/utf8.py` written up as a portable contract (not "whatever Python `str` does internally")
- exact float display-formatting spec (shortest round-trip vs fixed rules) documented and given explicit spec coverage, since Python repr and C++ default formatting diverge
- error message templates for the categories already asserted in `spec/error`/`spec/eval` inventoried and, where feasible, extracted into a shared, language-neutral source (data file or generation step) both a future Python and C++ host can read from, instead of two hand-maintained string sets that will drift
- new/expanded `spec/parse`, `spec/eval`, and `spec/error` cases covering non-ASCII codepoint boundaries and float formatting edge cases (very large/small magnitudes, exact zero, negative zero if applicable)

Excluded:

- any C++ implementation work
- redesigning error categories/structure (only text-content portability, per existing strict error normalization from Phase 2)

Depends on: R16.

---

## Release R19 — C++ Host Bring-up: Minimal Host

Theme:

> Stand up the smallest C++ host that can pass capability-light shared specs.

This is the first release that actually writes C++ code, using `hosts/cpp/` (already scaffolded) and following `hosts/template/EXAMPLE.md`.

Deliverables:

- C++ lexer/parser for current documented surface syntax
- lowering into the minimal portable Core IR node/pattern families frozen in `docs/architecture/core-ir-portability.md`
- Core IR evaluator covering current runtime semantics for non-capability-backed values (literals, options, binary/unary ops, pipelines, case/pattern matching, lambdas, function defs)
- integer representation chosen per R17's contract (bignum library or documented fixed-width decision) and ordered-map representation chosen per R17's contract
- CLI file mode and `-c` command mode, raw `argv()` access
- prelude autoload/loading (the prelude itself is already portable Genia source — no Genia-side work needed, only the loader)
- `help(name)` support for documented public helpers
- build system and tooling selected (CMake + package manager), with real (non-TODO) setup/build/test/lint commands filled into `hosts/cpp/README.md`
- passes `spec/parse`, `spec/ir`, and `spec/eval` shared cases via the R16 multi-host runner protocol
- `hosts/template/CAPABILITY_STATUS.md` copied into `hosts/cpp/` and kept truthful as capabilities land
- `docs/host-interop/HOST_CAPABILITY_MATRIX.md` C++ column updated only for what's actually implemented and spec-passing

Excluded:

- pipe mode, REPL, Flow, HTTP serving, refs, processes, bytes/json/zip bridge, debugger stdio (all deferred to later releases)
- any capability requiring the memory/concurrency model from R20

Depends on: R16, R17, R18.

---

## Release R20 — C++ Host: Memory & Concurrency Model for Refs, Cells, and Processes

Theme:

> Give the C++ host an explicit lifetime and concurrency model before adding any stateful capability.

Python's refs/cells/processes ride on refcounting+cycle GC plus threading, and Python's GIL serializes a lot of what looks like concurrent behavior. C++ gets none of that for free, so this needs a dedicated release rather than being decided ad hoc while implementing `spec/eval` cases for refs.

Deliverables:

- explicit ownership/lifetime model for Genia values (candidates: `shared_ptr` with a cycle-breaking strategy for closures/cells, arena/region allocation, or a tracing GC) documented as a C++ host-local design decision (not a portable semantics change — this is exactly the kind of "internals may differ" case `HOST_PORTING_GUIDE.md` already allows)
- concurrency primitive mapping (`std::thread`/mutex/condvar or equivalent) that preserves the lifecycle semantics in `src/genia/lifecycle_scope.py`/`lifecycle_plan.py` (R4/R8/R14 contracts) without redefining them
- a race/stress test pass specifically probing for behavior that Python's GIL masked but true parallelism could expose (concurrent cell/process access patterns)
- `refs` and `cell`/`process` primitives implemented in C++, passing relevant `spec/eval` cases

Excluded:

- HTTP serving, bytes/json/zip bridge (later)
- any change to the lifecycle contract itself — this release implements it, doesn't redesign it

Depends on: R19.

---

## Release R21 — C++ Host: CLI Pipe Mode, REPL, and Bytes/JSON/Zip Bridge

Theme:

> Round out the optional capabilities that don't require the R20 concurrency model.

Deliverables:

- `-p`/`--pipe` CLI mode
- REPL
- bytes/json/zip bridge, using C++ libraries chosen specifically to match the already-spec'd limits (duplicate-key rejection, 128-container nesting cap, safe-integer range) rather than a generic library's default behavior
- expanded `spec/cli` coverage exercised against the C++ host via the R16 runner
- capability matrix and `CAPABILITY_STATUS.md` updated

Excluded:

- Flow, HTTP serving (still deferred — both benefit from R20's concurrency model being battle-tested first)
- debugger stdio (parking lot unless separately prioritized)

Depends on: R19; benefits from but does not strictly require R20.

---

## Release R22 — C++ Host: Flow Runtime & HTTP Serving Parity

Theme:

> Reach capability parity with the Python reference host on the two remaining large surfaces.

Deliverables:

- Flow phase 1 runtime (lazy, pull-based, single-use) in C++, passing first-wave `spec/flow` cases
- synchronous blocking HTTP serving bridge preserving the request/response map shapes, exact-path routing, and CORS preflight behavior documented in `capabilities.md`
- full `docs/host-interop/HOST_CAPABILITY_MATRIX.md` C++ row review — every capability marked `Implemented` only where code, tests, and spec coverage all exist, consistent with the repo's existing truth-telling rule
- final audit pass (per the ticketing doc's "audit/truth review" phase) comparing C++ and Python hosts on the full active shared spec suite

Excluded:

- Python-host-only capabilities not yet promoted to shared/portable status (deterministic model fixture, Gemini REST adapter, deterministic embedding fixture, allowlisted host interop, resource-io beyond `fs`) — these stay Python-host-only until a separate roadmap decision promotes them to the shared contract

Depends on: R19, R20, R21.

---

## Summary Table

| Release | Focus | New C++ code? | Depends on |
|---|---|---|---|
| R16 | Multi-host spec runner protocol | No | — |
| R17 | Numeric & ordered-map contract | No | R16 |
| R18 | Unicode/float/error-text contract | No | R16 |
| R19 | Minimal C++ host (parse/ir/eval/CLI) | Yes | R16, R17, R18 |
| R20 | Memory & concurrency model | Yes | R19 |
| R21 | Pipe mode, REPL, bytes/json/zip | Yes | R19 (R20 optional) |
| R22 | Flow & HTTP serving parity | Yes | R19, R20, R21 |

This mirrors the existing roadmap's own dependency style (see R14's placement after R4/R8). R16–R18 are deliberately host-agnostic so the same contract work isn't repeated when Node/Java/Rust/Go bring-up is eventually proposed.
