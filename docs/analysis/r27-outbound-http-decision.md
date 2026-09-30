# R27 E27-4 — Outbound HTTP Transport Contract Decision

Status: **Planning/analysis record. Non-authoritative.** This document changes no
Genia language or runtime behavior and implements nothing. `GENIA_STATE.md`
remains final authority for implemented behavior.

Tracking issue: [#1043](https://github.com/m0smith/genia-2026/issues/1043)
Preceded by: `docs/analysis/r27-contract-evidence-reconciliation.md` section 6,
E27-1 (#1035), E27-2 (#1038), E27-3 (#1041, `r27-http-server-decision.md`).

## 1) Decision

**Defer `http_outbound_transport` out of R27.** It stays a documented C++ host
gap. No C++ work, shared spec, or capability-vocabulary change starts under R27
for outbound HTTP. With E27-3, this leaves no HTTP work in R27.

The R27 preflight's default was to defer "unless a narrow fixture-backed
contract exists that preserves R10 protected-value guarantees". The question was
whether that condition is met. It is not.

## 2) Evidence

| # | Finding | Where it is recorded |
|---|---|---|
| 1 | The capability has **no Genia surface of its own**: `http.transport` is a private Python-host capability consumed only by `web.http_send` and, through it, `web.send_annotated`. A portable claim would be about `import web` + `http_operation` + `web.http_send`, not about a transport. | `GENIA_STATE.md` 9.13, 9.14, 9.16; `docs/host-interop/capabilities.md` (HTTP Outbound Transport) |
| 2 | **Authority is host-minted.** `web.http_send`'s `authority` is an opaque R10 declassification authority; minting one is "a privileged host-side operation, never a pure-Genia one". A shared case that sends a protected header therefore needs a host-supplied authority, which the E16-1 protocol has no channel for. | `spec/cli/r14-youversion-bible-proxy-proving-case.yaml` (notes); `GENIA_STATE.md` 9.14 |
| 3 | **No shared case reaches the network.** The one shared case near this surface stops before the outbound round trip and says it is exercised only by a Python unit test. No `requires: [http_outbound_transport]` case exists, and no other spec uses `http_send` or `http_operation`. | `spec/cli/r14-youversion-bible-proxy-proving-case.yaml`; `grep` over `spec/` |
| 4 | **Fixtures are not expressible over the generic protocol.** Python's transport tests inject a fake transport in-process and use a real loopback server. The runner allowlists one fixture (`r25_concurrency`). Of the 23 of 772 shared cases that declare fixtures, 6 use it; the other 17 (13 `r11_model`, 4 `r12_grounded`) are excluded. A deterministic transport fixture would need a new fixture-and-authority mechanism in the runner. | `tools/spec_runner/host_executor.py` (`build_host_request`); measured with `discover_specs()` |
| 5 | **`genia-cpp` lacks every prerequisite:** no `import`, no R10 protected values or declassification, no R14 lifecycle scopes, no R13 configuration views, no `http_operation`, no sockets. Those names appear in the C++ host only in its known-unimplemented-globals list. | `genia-cpp` `src/genia2026_known_globals.hpp`, `src/parser.hpp`, `src/evaluator.hpp` |
| 6 | **The failure taxonomy is specified but unproven off-Python.** The closed `timeout`/`connect`/`tls`/`dns`/`other` kinds and the `err("http-timeout" \| "http-transport-failure")` mapping are defined, but their classification is Python `OSError`/`ssl` behavior. No cross-host evidence shows another stack maps identically. | `GENIA_STATE.md` 9.13, 9.14 |

Findings 2 and 4 together are decisive: even a fixture-backed proof needs
runner-level authority and fixture plumbing that does not exist, and R27's rules
forbid adding a runner, protocol, evidence format or capability registry "just to
satisfy R27". Finding 5 means the C++ side would be a multi-release stack
(protected values, lifecycle scopes, modules) before the transport itself.

## 3) Options considered

- **Promote only the pure pieces** (`http_operation` construction, query
  encoding). Rejected for R27: they are ordinary Genia code behind
  `import web` and R10/R14 machinery, so they belong with the module,
  protected-value and lifecycle slices, not with a transport claim.
- **Unauthenticated-only fixture subset** (no protected header, so no authority).
  Rejected: it would still need a new transport-fixture mechanism in the runner
  and would leave the R10 protected-sink guarantee, the reason this surface is
  sensitive, unproven while declaring the capability supported.
- **Implement a C++ transport first.** Rejected: no contract, no evidence, no
  authority model, and no prerequisites.
- **Defer (chosen).** Zero behavior change; keeps the gap honest and tracked.

## 4) What changes

- `spec/known_host_gaps.json`: the `http_outbound_transport` entry is kept (the
  C++ host still lacks the capability, so the parity gate must keep reporting
  `KNOWN_GAP`) but is re-tracked to #1043 with a deferred reason and a stricter
  removal condition.
- `docs/strategy/roadmap/cpp-host-gap-burndown.md`: the entry moves from the R27
  delivery lane to "Later Release / Separate Gate".
- `docs/strategy/roadmap/r25-r29.md`: the R27 section records the deferral.
- No change to `GENIA_STATE.md`, the release title, capability vocabulary, shared
  specs, or `genia-cpp`. Retitling R27 stays with the E27-6 release truth sync.

## 5) Preconditions for any future outbound-HTTP release

A separate contract-first gate must settle, with shared executable evidence:

1. how a host obtains or is granted transport and declassification authority
   under the shared protocol, without pure-Genia code minting it;
2. a deterministic transport-fixture mechanism the runner can drive, with no
   ambient network access in ordinary test environments;
3. the `genia-cpp` prerequisites: module/`import` support, R10 protected values
   and declassification, R14 lifecycle scopes, and R13 configuration views;
4. cross-host evidence that the closed failure kinds classify identically.

Removal of the `http_outbound_transport` gap requires `genia-cpp` to declare it
`supported` with that evidence passing and the host parity gate reporting
`PARITY_OK`.
