# R27 Release-Size Preflight — C++ Flow, Pipe Mode, and HTTP Serving

Status: **Planning/architecture record. Non-authoritative.** This document
changes no Genia language or runtime behavior and implements nothing.
`GENIA_STATE.md` remains final authority for implemented behavior. Roadmap
documents remain planning authority for sequencing; this document evaluates
R27 size and release shape before any contract, design, test, implementation,
documentation, audit, or distillation phase starts.

Scope of this document: a skeptical preflight of the planned release
**R27 — C++ Flow, Pipe Mode, and HTTP Serving**. It asks whether R27 is one
coherent release or a thematic bundle that should be decomposed before
implementation begins. It is preflight/architecture work only. It includes no
R27 implementation, no `genia-cpp` changes, no capability additions or
renames, no shared-spec edits, and no host-gap manifest edits.

Baseline: R26 is complete. The bounded C++ production host supports the R24
minimal floor, R25 Ref/Cell/local Process capabilities, and R26 scripted REPL,
Bytes/UTF-8, and strict JSON data bridges. Python remains the full-language
reference host; C++ is not feature parity.

---

## 1) Executive finding

**R27 as named is useful, but too broad to implement as one undifferentiated
change.** It is four capability tracks with different dependencies and risk:

| Track | Portable contract today | Shared evidence today | Main risk |
|---|---|---|---|
| **Flow phase 1** | Implemented in Python and documented as partial | Existing `spec/flow/*` cases, mostly not C++-passing today | Runtime pull/finalization semantics |
| **CLI pipe mode** | Implemented in Python CLI contract | Existing `spec/cli/*` pipe cases | Depends on Flow behavior and stdin/stdout discipline |
| **HTTP server** | Python-host-only / Experimental surfaces exist | No C++-passing shared HTTP-server capability evidence | Promoting host-local behavior too quickly |
| **HTTP outbound transport** | Python-host-only / Experimental surfaces exist | No C++-passing shared outbound HTTP capability evidence | Authority, protected sinks, and lifecycle interaction |

Semantic verdict: **DECOMPOSE BEFORE IMPLEMENTATION.**

Recommended release shape:

- Keep the R27 number and title for now; do not renumber R28-R41.
- Start R27 with **E27-0 contract/evidence reconciliation** over the four
  tracks.
- Deliver **Flow phase 1** and **CLI pipe mode** as the first coherent lane.
- Treat **HTTP server** and **HTTP outbound transport** as separately gated
  lanes that may remain deferred if their contracts are not small enough to
  prove without broadening R27.
- Do not let C++ implementation details define observable Genia semantics.
- Do not claim C++ support for any optional capability until shared evidence
  proves it and the host parity gate reports it honestly.

This is a decomposition recommendation only. The actual R27 issue split still
requires the normal R26+ change pre-flight issue.

---

## 2) Why this simplifies future work

R27 sits directly between the completed C++ host arc and the planned MCP and
Sheet pipeline releases. Flow and pipe mode are enabling infrastructure for
the killer workflow:

```text
messy records in -> clear pipelines -> validated shaped output / reports + useful diagnostics
```

If Flow and pipe mode are proven cleanly in C++, later R28/R29 work can rely on
a smaller, evidence-backed portable substrate. If R27 also tries to promote
HTTP serving and outbound transport in the same implementation lane, the
release risks mixing:

- lazy runtime semantics;
- CLI observation rules;
- server lifecycle behavior;
- external IO authority;
- protected-value sink behavior;
- host capability declarations;
- cross-host evidence bookkeeping.

That combination is exactly the kind of bundle that makes later release audits
expensive. Separate lanes keep each failure model visible.

---

## 3) Candidate R27 lane split

### E27-0 — Contract and Evidence Reconciliation

Purpose: decide the exact implemented-truth boundary before any host work.

Required outputs:

- identify the authoritative `GENIA_STATE.md`, `GENIA_RULES.md`, and
  `GENIA_REPL_README.md` sections for Flow, pipe mode, HTTP server, and HTTP
  outbound behavior;
- inventory existing `spec/flow/*` and `spec/cli/*` coverage relevant to C++;
- identify whether HTTP behavior has any existing shared-spec route or needs a
  new capability-gated route;
- decide whether `flow_phase_1`, `cli_pipe_mode`, `http_server`, and
  `http_outbound_transport` remain the right capability names;
- map every temporary C++ unsupported area to an issue-backed known-gap entry
  or to an explicit R27 lane.

Exit criteria:

- every lane has a contract/evidence path or is deferred;
- no lane requires copying Python implementation details as semantics;
- the host parity gate can distinguish genuine gaps from stale gaps.

### E27-1 — C++ Flow Phase 1

Purpose: implement the smallest shared Flow surface that C++ can prove.

Candidate scope:

- lazy pull-based, single-use Flow values;
- deterministic observable output for already-covered first-wave Flow cases;
- bounded-demand behavior for `take`, `drop`, `map`, `filter`, `scan`, `reduce`,
  `each`, `collect`, and current first-wave compositions only where shared
  evidence already exists or is deliberately added;
- finalization/early-close behavior required by the current shared Flow cases.

Explicit non-goals:

- async Flow;
- multi-port Flow;
- distributed sources;
- browser/runtime integration;
- Sheet-specific record semantics;
- actor/event/subscription machinery.

### E27-2 — C++ CLI Pipe Mode

Purpose: make `genia -p` portable for the already-contracted pipe-mode surface.

Dependency: E27-1 or an explicitly smaller Flow subset that still satisfies the
pipe-mode shared cases.

Candidate scope:

- stdin `lines` source;
- automatic consumption of the final Flow;
- rejection of explicit unbound `stdin` and explicit unbound `run`;
- deterministic stdout/stderr/exit-code observations for shared pipe cases;
- no `main` dispatch in pipe mode.

Explicit non-goals:

- shell tokenization;
- `$1`/`ARGV`-style features;
- shell pipeline `$(...)`;
- richer streaming IO or filesystem authority.

### E27-3 — HTTP Server Contract Decision

Purpose: decide whether HTTP serving belongs in R27 implementation or is
deferred.

Contract questions:

- Is any HTTP server behavior portable, or is the current behavior
  Python-host-only infrastructure?
- What is the smallest observable contract: route matching, request shape,
  response shape, status/header/body normalization, lifecycle interaction, or
  something narrower?
- Can shared evidence run deterministically without opening broad socket
  authority in ordinary test environments?
- Does the contract depend on R8 server-execution behavior in a way C++ can
  prove without becoming a second web framework?

Recommended default: **defer unless E27-0 proves a small, deterministic,
capability-gated contract.**

### E27-4 — HTTP Outbound Transport Contract Decision

Purpose: decide whether outbound HTTP belongs in R27 implementation or is
deferred.

Contract questions:

- What authority creates or supplies the outbound transport capability?
- How are protected headers and protected request values rejected or
  declassified?
- Which failure taxonomy is portable across hosts?
- Can a deterministic fixture prove behavior without real networking?
- Does the transport depend on lifecycle/configuration behavior outside the
  bounded C++ host floor?

Recommended default: **defer unless E27-0 proves a narrow fixture-backed
contract that preserves R10 protected-value guarantees.**

### E27-5 — Cross-Cutting Hardening

Purpose: prove the completed R27 lanes together.

Candidate scope:

- cross-mode CLI behavior for file, command, REPL, and pipe where applicable;
- Flow finalization and failure cleanup;
- known-host-gap freshness;
- no protected-value leakage through pipe or HTTP surfaces;
- no drift between Python reference evidence and bounded C++ evidence.

### E27-6 — Release Truth Sync and Audit

Purpose: close the release honestly.

Required outputs:

- update `GENIA_STATE.md` for only the behavior actually implemented;
- update `README.md`, `GENIA_REPL_README.md`, host-interop docs, roadmap text,
  and `docs/releases/R27.md` only as supported by evidence;
- record final Python and C++ evidence counts;
- run the host parity gate;
- complete skeptical release truth audit and doc distillation.

---

## 4) Recommended first implementation lane

The first implementation lane should be:

```text
E27-0 contract/evidence reconciliation
-> E27-1 Flow phase 1
-> E27-2 CLI pipe mode
-> E27-5 hardening for those lanes
-> E27-6 release truth sync/audit, if HTTP is deferred
```

Reason: Flow and pipe mode are tightly coupled and directly support the
validated-data-pipeline north star. They also unlock later Sheet record
pipeline work more directly than HTTP does.

HTTP serving and outbound transport should remain R27 candidates only if the
first contract gate demonstrates they are small, deterministic, and
capability-gated. Otherwise, they should be split out without disturbing the
R28 MCP issue set or later release numbering.

---

## 5) Prompt handoff guidance

Future CODEX/Claude prompts for R27 should include:

- read `AGENTS.md`, `GENIA_STATE.md`, `GENIA_RULES.md`,
  `GENIA_REPL_README.md`, `README.md`, `docs/strategy/killer-workflow.md`,
  `docs/strategy/release-roadmap.md`, `docs/strategy/roadmap/r25-r29.md`,
  and this file before acting;
- do not implement R27 from roadmap text alone;
- complete the R26+ pre-flight issue template before contract work;
- keep documentation synchronized with implemented truth;
- do not add a new runner, protocol, evidence format, capability registry, or
  Core IR mechanism just to satisfy R27;
- if portable observable behavior changes, add or update shared executable
  spec evidence first;
- if C++ cannot support a portable capability in the same merge window, record
  an issue-backed known host gap with affected tests and a removal condition.

---

## 6) Final recommendation

Proceed to an R27 pre-flight issue, but keep implementation parked until
E27-0 answers the contract/evidence questions.

Default decomposition:

1. Flow phase 1 and CLI pipe mode are the primary R27 delivery lane.
2. HTTP server and outbound HTTP are R27 candidates, not assumed completion
   requirements.
3. If HTTP cannot be proven narrowly, defer it to a later contract-first
   release without renumbering R28-R41.
