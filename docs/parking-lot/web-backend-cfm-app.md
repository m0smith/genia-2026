# Web Backend Ergonomics (driven by a real consuming app)

Status: **Parking lot / non-authoritative**

This note captures future ideas only. It does not define implemented Genia behavior.
If this conflicts with `GENIA_STATE.md`, `GENIA_STATE.md` wins.

Alignment note: web/server work is **not** part of Genia's current killer workflow
(Outcome-aware validated data pipelines). "server mode" is already listed under
Parking Lot in `docs/strategy/release-roadmap.md`. These ideas stay parked unless
explicitly promoted.

## Why this exists

A real external application (a Come Follow Me / family-history verse-lookup widget,
built outside this repo) is being prototyped with a Genia backend serving JSON over
HTTP to a browser frontend. Exercising the current `web` prelude against a real
browser client surfaced a small, concrete set of ergonomic gaps worth preserving
before they are forgotten. This is captured as future-idea input, not as a request
to build web features into the current release.

## Verified current behavior (2026-07-28, Python reference host)

Confirmed working by running a throwaway one-endpoint service and calling it:

- `serve_http` dispatches all methods (GET/POST/PUT/DELETE/PATCH/OPTIONS/HEAD) to
  the handler and emits the handler's returned headers map verbatim.
- Arbitrary response headers work — a handler returning `access-control-*` headers
  produced a correct CORS response on a real GET.
- `request("query")` is a parsed map of the query string; routing matches on the
  query-stripped `path`, so `?ref=John+3:16` reads cleanly without extra work.

These are already-implemented behaviors; see `GENIA_STATE.md` and the `web` prelude
for the authoritative surface. This note does not redefine them.

## Ideas to preserve

- **CORS preflight support.** A browser preflight (`OPTIONS /path`) currently finds
  no route and returns 404, because the `web` router exposes only `get`/`post`
  constructors and `route_matches?` matches on method. A future `options(path, handler)`
  route constructor (or preflight-aware routing) would let handlers answer preflight
  requests. Only "non-simple" requests (custom headers, JSON-content-type POST bodies,
  PUT/DELETE) trigger preflight; simple GETs are unaffected.
- **A `cors(...)` header helper.** Building the `access-control-*` map by hand on
  every response is repetitive. A small helper that produces the CORS headers, plus a
  way to merge extra headers into `json(...)` / `text(...)` (which currently hardcode
  their headers), would remove the boilerplate.
- **Optional path-parameter routing.** `route_matches?` is exact-path only. Segment
  binding (e.g. `/verse/:book/:chapter/:verse`) would be a convenience; query-string
  style already covers the lookup case, so this is low priority.
- **Optional concurrency.** `serve_http` is single-threaded synchronous (one request
  at a time via a `handle_request` loop). An opt-in threaded/multi-request mode would
  matter only if a consumer needs concurrent load; it is not needed for low-traffic
  demos.
- **Stabilizing the web surface.** The `web` prelude / HTTP host capability is
  Python-host-only and outside the shared semantic-spec categories (parse/ir/eval/cli/
  flow/error). If a real app is to depend on it durably, consider adding it to the host
  capability registry and/or a spec category so behavior is pinned. Until then,
  consumers should pin to a specific Genia version/commit.

## What this should not become

- A general web framework or a new "server mode" release ahead of the data-pipeline
  killer workflow.
- Any change to `GENIA_STATE.md` or authoritative docs describing these as implemented.
- A reason to pull web work into R5 (native-test migration) or R6 (data-workflow
  hardening).
- Path-param routing or a validation DSL built speculatively before a consumer needs it.

## Related areas

- `src/genia/std/prelude/web.genia` — current web surface
- `src/genia/builtins.py` — `serve_http` / request-map / response handling (Python host)
- `docs/host-interop/capabilities.md` — host capability registry (candidate home if stabilized)
- `docs/strategy/release-roadmap.md` — "server mode" parking-lot entry
- `examples/rest_todo_service.genia` — existing REST example used as the spike skeleton
- `docs/parking-lot/server-execution-mode.md` — R8 follow-on: a `serve` execution mode + `@server`/`@route`/`@cors` annotations that bind down to the R7 primitives defined here

## Promotion status

**Promoted to Release R7 — Web Serving Ergonomics** (see `docs/strategy/release-roadmap.md`)
as explicitly approved infrastructure work. This note remains the idea-capture source;
per the parking-lot process it should be superseded by a pre-flight artifact and tracking
issues before implementation begins. R7 must not displace killer-workflow (R5/R6) work.

Original promotion trigger (now satisfied): a consuming app concretely needs the
preflight/CORS ergonomics, and the work has been explicitly approved as infrastructure.
