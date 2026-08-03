# Server Execution Mode (second lifecycle consumer)

Status: **Parking lot / non-authoritative**

This note captures future ideas only. It does not define implemented Genia behavior.
If this conflicts with `GENIA_STATE.md`, `GENIA_STATE.md` wins.

Alignment note: server/web work is **not** part of Genia's current killer workflow
(Outcome-aware validated data pipelines). "server mode" is listed under Parking Lot in
`docs/strategy/release-roadmap.md`, and R4 explicitly **excluded** server-mode
implementation. This note is promoted to a **planned** release (R8) only as explicitly
approved infrastructure; it must not displace R5/R6.

## Why this exists

R4 delivered a portable lifecycle model (lifecycle plan / phase / scope / cleanup / failure
rules, plus an **annotation binding model** and "portable docs for execution-mode lifecycle
proposals"), and named the **test lifecycle as the first implemented consumer**. The clear
next step the model was built for is a **second consumer: a server / request lifecycle**,
activated by a dedicated *serve* execution mode.

This also resolves an open design tension for web ergonomics (R7). A behavioral `@cors`
"decorator" looks like it violates the R4 rule that *"annotations do not execute merely
because they exist."* It does not — under a serve execution mode the annotation is an inert
descriptor that the **mode's lifecycle** activates, exactly as `@test` is inert until
`genia test` runs the test lifecycle. The execution mode is what makes annotation-driven
web config legitimate.

## Ideas to preserve

- **A `serve` execution mode.** `genia serve <file>` alongside the existing file, `-c`
  command, `-p` pipe, and `test` modes. It owns the server lifecycle; it does not define new
  language semantics or Core IR.
- **A server lifecycle plan (three phases), reusing the R4 lifecycle contract:**
  - *startup* — read `@server` config, load data/state, bind the port
  - *per-request* — route match → handler → response, with cross-cutting hooks (CORS) applied
    in this phase
  - *shutdown* — deterministic cleanup / close, per R4 cleanup + failure rules
- **Inert annotation surface, activated only by the serve mode:**
  - `@server(port, host, ...)` — server configuration descriptor
  - `@route(method, path)` — handler discovery, the same phase-driven discovery shape as
    `@test` (zero-arg / request-arg functions discovered and bound; no manual registration)
  - `@cors(origin, methods, headers)` — request-lifecycle cross-cutting descriptor that
    injects CORS headers and answers `OPTIONS` preflight
- **Bind-down principle (Core Surface Freeze):** annotations are *sugar* that bind to
  existing runtime primitives — `@route` → `route_request`, `@cors` → the R7 `web.cors(...)`
  wrapper, `@server` → `serve_http`. No second mechanism is introduced; the declarative
  surface compiles to the functional one.
- **Relationship to R7:** R7 delivers the functional web primitives and ergonomics (the
  `cors` wrapper, preflight-aware routing). R8 adds the declarative execution-mode layer on
  top of them. **R8 depends on R7.**

## What this should not become

- A general application framework, plugin system, or DI container.
- A behavioral annotation system where annotations execute outside a lifecycle (this must stay
  consistent with R4: annotations do not execute merely because they exist).
- A new language dialect or Core IR change — serve mode is a host/runtime execution mode, not
  language semantics.
- A reason to pull work into R5 (native-test migration) or R6 (data-workflow hardening).
- Anything documented as implemented before it ships — `GENIA_STATE.md` stays authoritative.

## Related areas

- `docs/strategy/release-roadmap.md` — Release R7 (web ergonomics) and Release R8 (this)
- `docs/parking-lot/web-backend-cfm-app.md` — the R7 web-ergonomics gaps this builds on
- R4 lifecycle model + annotation binding model (the contract this reuses)
- `src/genia/std/prelude/web.genia`, `src/genia/builtins.py` — current web primitives
- `src/genia/interpreter.py` — CLI / execution-mode entry point
- test lifecycle / `@test` discovery — the precedent for `@route` discovery

## Promotion status

**Promoted to Release R8 — Server Execution Mode** (see `docs/strategy/release-roadmap.md`)
as explicitly approved infrastructure work, staged **after R7**. This note remains the
idea-capture source; per the parking-lot process it should be superseded by a pre-flight
artifact and tracking issues before implementation. R8 must not displace killer-workflow
(R5/R6) work, and depends on R7 landing first.
