# R27 E27-3 — HTTP Server Contract Decision

Status: **Planning/analysis record. Non-authoritative.** This document changes no
Genia language or runtime behavior and implements nothing. `GENIA_STATE.md`
remains final authority for implemented behavior.

Tracking issue: [#1041](https://github.com/m0smith/genia-2026/issues/1041)
Preceded by: `docs/analysis/r27-contract-evidence-reconciliation.md` section 5,
E27-1 (#1035), E27-2 (#1038).

## 1) Decision

**Defer `http_server` out of R27.** It stays a documented C++ host gap. No C++
work, shared spec, or capability-vocabulary change starts under R27 for HTTP
serving. A later release may take it up only through its own contract-first gate
(section 5).

This is the default the R27 preflight recommended ("defer unless a small,
deterministic, capability-gated contract exists"). The question was whether
that condition is met. It is not.

## 2) Evidence

| # | Finding | Where it is recorded |
|---|---|---|
| 1 | The current surface is declared **Python-host-only**: a synchronous, blocking bridge that is "not part of the shared portable contract", with "portability to non-Python hosts" listed under Not Guaranteed. | `docs/host-interop/capabilities.md` (HTTP Serving); `docs/host-interop/HOST_CAPABILITY_MATRIX.md` |
| 2 | **No shared evidence exists.** There is no `spec/web` category and no `requires: [http_server]` case. Coverage is Genia-native wrapper tests plus focused Python transport tests. | `docs/host-interop/capabilities.md` ("Coverage boundary"); `spec/manifest.json` |
| 3 | **The E16-1 protocol cannot drive a server.** Its operation set is closed (`parse`, `lower`, `eval`, `cli`, `capabilities`); a case observes stdout, stderr and exit code after a process ends. `serve_http` blocks while listening (bounded only by `config.max_requests`), so no runner step can send it a request. | `tools/spec_runner/protocol.py`; `serve_http_fn` in `src/genia/builtins.py` |
| 4 | **`genia-cpp` lacks every prerequisite.** `import` is a hard-rejected keyword (`import web` is how the surface is reached), the tokenizer has no `@` annotation (`@route`/`@server`/`@cors` drive `genia serve`), there is no `serve` CLI mode, and there is no socket code. | `genia-cpp` `src/parser.hpp`, `src/adapter.hpp` |
| 5 | **Listener authority is not portably defined.** Bind address and port policy, listener ownership, and what a host may bind are host-authority questions the Genia contract has not answered. The execution-realization guardrail asks that network endpoints not be treated as local-call-equivalent. | `docs/architecture/execution-realization.md`; `GENIA_STATE.md` section 9.7 (server lifecycle is Python-host `genia serve`) |
| 6 | **Nothing in the current release plan needs it.** R28's optional Streamable HTTP is its own contract-first decision and does not depend on a C++ HTTP server. The killer workflow (validated data pipelines) is served by Flow and pipe mode, both now proven. | `docs/strategy/roadmap/r25-r29.md` |

Together, findings 3 and 4 mean a "small slice" is not available: proving even a
minimal server needs a new evidence mechanism (a client driver, port and lifecycle
coordination) plus module, annotation and CLI-mode prerequisites. R27's own
rules forbid adding a runner, protocol, evidence format or capability registry
"just to satisfy R27".

## 3) Options considered

- **Promote a minimal portable subset now** (for example only the pure
  `route_request`/`response`/`with_headers`/`cors` value helpers, without a
  listener). Rejected for R27: those helpers are ordinary Genia prelude code
  behind `import web`, so they depend on the module system, not on
  `http_server`; promoting them would not close `http_server` and would blur what
  the capability means. They belong with a future module/`import` slice.
- **Define a fixture-backed "virtual server" evidence path** (feed request maps
  to a handler in-process). Rejected: it exercises `route_request`, not a
  listener, and would claim `http_server` without a socket.
- **Implement a socket listener in C++ first.** Rejected: no contract, no
  evidence, unresolved authority.
- **Defer (chosen).** Zero behavior change, keeps the gap honest and tracked.

## 4) What changes

- `spec/known_host_gaps.json`: the `http_server` entry is kept (the C++ host still
  lacks the capability, so the parity gate must keep reporting `KNOWN_GAP`) but
  is re-tracked to #1041 with a deferred reason and a stricter removal condition.
- `docs/strategy/roadmap/cpp-host-gap-burndown.md`: `http_server` moves from the
  R27 delivery lane to "Later Release / Separate Gate".
- `docs/strategy/roadmap/r25-r29.md`: the R27 section records the deferral.
- No change to `GENIA_STATE.md`, the release title, capability vocabulary,
  shared specs, or `genia-cpp`. Retitling R27 is left to the E27-6 release truth
  sync so that title and completed scope are corrected once.

## 5) Preconditions for any future HTTP-server release

A separate contract-first gate must settle, with shared executable evidence:

1. the smallest portable request and response value shapes;
2. who owns and authorizes the listener, and what bind policy a host may apply;
3. an evidence mechanism that can drive a served request deterministically
   without ambient network access in ordinary test environments;
4. the `genia-cpp` prerequisites: module/`import` support, annotation parsing,
   and a `serve` CLI mode;
5. the interaction with the R8 lifecycle and R14 outbound-client composition
   already recorded in `GENIA_STATE.md` sections 9.7 and 9.17.

Removal of the `http_server` gap requires `genia-cpp` to declare it `supported`
with that evidence passing and the host parity gate reporting `PARITY_OK`.
