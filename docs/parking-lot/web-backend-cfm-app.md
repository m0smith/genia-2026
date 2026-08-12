# Web Backend Ergonomics (driven by a real consuming app)

Status: **Historical idea capture / non-authoritative — promoted to R7**

This note records the consumer evidence that motivated R7. It does not define implemented Genia behavior.
If this conflicts with `GENIA_STATE.md`, `GENIA_STATE.md` wins.

Current approved planning lives in:

- `docs/strategy/release-roadmap.md`
- R7 epic #525
- required issues #526, #527, and #530

## Why this exists

A real external application (a Come Follow Me / family-history verse-lookup widget,
built outside this repo) is being prototyped with a Genia backend serving JSON over
HTTP to a browser frontend. Exercising the current `web` prelude against a real
browser client surfaced a small, concrete set of ergonomic gaps.

This document preserves that evidence. It is no longer the active design source.

## Verified current behavior (2026-07-28, Python reference host)

Confirmed working by running a throwaway one-endpoint service and calling it:

- `serve_http` dispatches HTTP requests to the handler and emits the handler's returned headers map.
- Arbitrary response headers work; a handler returning `access-control-*` headers produced a correct CORS response on a real GET.
- `request("query")` is a parsed map of the query string; routing matches on the query-stripped path.

These are implemented facts only to the extent stated by `GENIA_STATE.md` and the current runtime. This note does not redefine them.

## Gaps surfaced by the consumer

- No composable way exists to add headers to an already-built `json(...)` or `text(...)` response.
- A browser preflight request cannot be handled automatically without manual routing and header construction.
- The Python-host web capability is outside the shared semantic-spec categories and is not yet pinned as a durable host capability.
- Exact-path routing and synchronous serving were observed, but the consumer did not demonstrate that path parameters or concurrency were required.

## Promoted R7 disposition

R7 approved one response-value primitive and one handler wrapper:

```genia
with_headers(headers, response) -> response
cors(policy, handler) -> handler
```

- #526 owns the sole response-header composition operation.
- #527 owns the CORS handler wrapper, ordinary-response decoration, and true preflight handling.
- #530 owns capability stabilization, release documentation, and the final truth audit.
- A public `options(...)` route constructor is not part of the approved R7 design.
- Header-taking `json`/`text` overloads are not part of the approved R7 design.
- #528 path parameters and #529 concurrent serving were closed not-planned until concrete evidence justifies new focused work.

Nothing in this section is implemented merely because it is planned here.

## What this must not become

- A general web or middleware framework.
- A source of implemented-behavior claims ahead of `GENIA_STATE.md`.
- A reason to add path parameters or concurrency speculatively.
- A second CORS or response-header mechanism.
- A substitute for R8's separately planned lifecycle-bound serve mode.

## Related areas

- `src/genia/std/prelude/web.genia` — current implemented web surface
- `src/genia/builtins.py` — current Python-host transport integration
- `docs/host-interop/capabilities.md` — stabilization target in #530
- `docs/strategy/release-roadmap.md` — active R7 plan
- R7 epic #525 — release checklist
- `docs/parking-lot/server-execution-mode.md` — R8 follow-on
- R8 #537 — future inert `@cors` binding to the R7 wrapper

## Promotion status

**Promoted to Release R7 — Web Serving Ergonomics.**

The original promotion trigger is satisfied: a real browser consumer needs preflight/CORS ergonomics and the infrastructure work has been explicitly approved. The active issue dependency is:

```text
#526 with_headers → #527 cors wrapper → #530 stabilization/audit → R7 complete
```
