# R14 Composable Lifecycle Contract

Status: **Approved contract. E14-1 (issue #621), E14-2 (issue #692), and
E14-3 (issue #693) are implemented against this document; E14-4 and later
slices remain not implemented.**

This document fixes the semantic boundary for R14 tickets. It is not itself
implemented-behavior documentation — see `GENIA_STATE.md` sections 9.8-9.10
for what E14-1 through E14-3 actually implement.
`GENIA_STATE.md` remains final authority for implemented behavior.

## Purpose

R14 turns the inert R4 lifecycle vocabulary and R8's one fixed server
lifecycle into one coherent, explicit execution-scope model that composes
vertically (parent/child scopes), horizontally (peer attachments on one
scope), and repeatedly (fresh element scopes over eager and lazy sources).
Outbound HTTP is one common inert operation and one client-scope consumer of
that model, proving the vertical/protected-credential story without adding a
second lifecycle system.

R14 adds no lifecycle runner over arbitrary R4 plan data, no global mutable
"current lifecycle," no lexical injection, no dependency injection, no
scheduler, and no second Outcome/Template/representation/configuration/HTTP/
error model. Flow/Seq/Outcome transformations, R9 representations, R10
protected values, and R13 provider/view behavior remain unchanged and
authoritative.

## Terms

- **LifecycleDefinition**: an inert, source-constructible closed map
  describing one attachable lifecycle concern: a name and two ordinary
  callables, `enter` and `exit`. It performs no work by existing; it is data
  until an explicit scope operation consumes it.
- **ExecutionScope**: one entered lifetime. Not source-constructible;
  obtained only as the opaque handle argument passed into `enter`, `exit`,
  and work callables during an explicit scope operation. A handle is valid
  only for the synchronous duration of the scope operation that produced it.
- **LifecycleInstance**: the internal pairing between one `LifecycleDefinition`
  and the one `ExecutionScope` that entered it. R14 keeps this concept
  distinct in this document so parent/child, peer, and repeated-element
  ownership rules stay precise, but it is not itself a separately
  constructible or inspectable source-visible value — reifying it as public
  API would duplicate the scope handle for no behavior a caller needs.
- **peer**: informal name for one `LifecycleDefinition` attached to one scope
  operation alongside zero or more other `LifecycleDefinition`s. Attachment
  order is not parentage.
- **root scope**: a scope created directly by `lifecycle_scope`, with no R14
  parent.
- **child scope**: a scope created by `lifecycle_child` from an active parent
  handle.
- **element scope**: one fresh scope created per consumed element by
  `lifecycle_repeat`.
- **context**: an ordinary Genia value exposed inward by one entered peer's
  `enter` result, or by a reserved element/config binding, readable through
  `lifecycle_context`. Context is distinct from lexical bindings: it is read
  only through the explicit scope handle, never injected into surrounding
  lexical scope.
- **primary failure**: the first entry, work, or unwind failure encountered
  for one scope operation. Exactly one failure is primary per `LifecycleResult`.
- **cleanup failure**: an `exit` failure that is not the primary failure. It
  never replaces or hides the primary failure.

## Public surface

The complete new R14 public surface is six ordinary functions plus one
closed result shape:

```text
lifecycle_scope(peers, work) -> LifecycleResult
lifecycle_child(scope_handle, peers, work) -> LifecycleResult
lifecycle_repeat(peers, source, element_work) -> [LifecycleResult, ...] | Flow<LifecycleResult>
lifecycle_context(scope_handle, name) -> some(context_value) | none("lifecycle-context-absent")
lifecycle_config(provider) -> LifecycleDefinition
web.http_send(operation, authority, timeout_ms) -> some(HttpResponse) | err(reason, context)
```

`peers` is an ordered list of `LifecycleDefinition` values:

```text
{name: symbol, enter: callable/1, exit: callable/2}

enter(scope_handle) -> some(context_value) | err(reason, context)
exit(scope_handle, primary_summary) -> some("nil") | err(reason, context)
```

`work` (for `lifecycle_scope`/`lifecycle_child`) and `element_work` (for
`lifecycle_repeat`) are ordinary one-argument callables receiving the scope
handle. Their return value is carried into the result verbatim as ordinary
data; it is never inspected for `some`/`none`/`err` by the executor. A work
callable that legitimately returns `err(...)` as its own application data is
not a lifecycle failure. The only way work causes a lifecycle failure is by
raising, exactly as R8 request handling treats an unhandled exception as the
request's primary failure rather than parsing handler return values for
failure sentinels.

Rejected public API shapes include a mutable/ambient "current scope" getter,
annotation-driven lifecycle discovery (`@setup`/`@teardown` or similar),
class-based lifecycle objects, a generic action-identifier registry/resolver
over R4 plan data, and any second `map`/`filter`/`scan` mechanism. `peers`,
`work`, and `provider` are always explicit ordinary arguments.

## LifecycleResult

Every scope operation (`lifecycle_scope`, `lifecycle_child`, and one
per-element application inside `lifecycle_repeat`) returns exactly this
closed map:

```text
{
  status: quote(ok) | quote(error),
  state: quote(completed) | quote(failed),
  scope: quote(root) | quote(child) | quote(element),
  phase: quote(enter) | quote(work) | quote(exit),
  peer: some(symbol) | none("lifecycle-no-peer"),
  result: some(ordinary_value) | none("lifecycle-no-result"),
  primary_failure: none("lifecycle-no-failure") | failure_value,
  cleanup_failures: [failure_value, ...]
}
```

`failure_value` is exactly:

```text
{
  peer: some(symbol) | none("lifecycle-no-peer"),
  phase: quote(enter) | quote(work) | quote(exit),
  reason: string,
  context: map
}
```

`status` is `quote(ok)` exactly when `primary_failure` is
`none("lifecycle-no-failure")`; `state` mirrors it as `quote(completed)` or
`quote(failed)`. `phase` names the phase that owns the primary failure on
failure, or `quote(exit)` as the terminal phase on success (the scope always
finishes by unwinding whatever it entered, even when nothing was attached).
`peer` names the peer that owned an enter/exit primary failure; it is
`none("lifecycle-no-peer")` for a work-phase primary failure (the work
callable's own body, not a peer) and for success. `result` carries the work
callable's return value on a completed or work-phase-failed scope; it is
`none("lifecycle-no-result")` when work never ran (an entry failure) or when
work raised (the exception is the failure, not a result). `cleanup_failures`
lists every `exit` failure that was not promoted to `primary_failure`, in
exit-call order (see below).

## Scope lifetime state machine

Every scope (root, child, or element) transitions:

```text
created -> entering -> active -> exiting -> completed   (success)
created -> entering -> exiting -> failed                (entry failure, if any peer already entered)
created -> entering -> failed                            (entry failure, nothing yet entered)
created -> entering -> active -> exiting -> failed        (work or exit failure)
```

A scope is **entered** the moment its first peer's `enter` returns `some`, or
immediately (no peers) when it reaches `active`. A scope handle is valid only
while its scope is `entering`, `active`, or `exiting`; `lifecycle_child` and
`lifecycle_context` called with a handle whose scope has already reached
`completed`/`failed` raise the existing-pattern runtime error used elsewhere
for a value used past its single valid lifetime (the same family as Flow's
"already consumed" error). This is the sole mechanism preventing lazy values
or callbacks from silently retaining expired scope/element context: retention
does not leak data, it fails loud on the next access attempt.

`lifecycle_child` may be called only while the parent handle's scope is
`active`, and only synchronously within that parent's own `work`/
`element_work` callable (the only place source code legitimately holds an
active handle). No R14 operation exists to create a child asynchronously,
store a handle for later reuse across calls, or resume a completed scope —
this is R14's entire cancellation/shutdown surface: there is none. A scope
ends only by its own work, child calls, and peers returning or raising
synchronously; R14 defines no external cancel/abort/signal API.

## Entry, work, and unwind algorithm

For one scope operation with peer list `[p0, p1, ..., pn]` and a work
callable:

1. **Enter phase.** For `i` from `0` to `n`, call `p_i.enter(scope_handle)`.
   - `some(context)`: `p_i` is now entered; its context becomes readable
     through `lifecycle_context(scope_handle, p_i.name)`; continue to `p_{i+1}`.
   - `err(reason, context)`: `p_i` is not entered. Stop entering later peers.
     Skip work entirely. Proceed to the unwind step below for peers
     `p_0..p_{i-1}` (already entered). The result's `primary_failure` is
     `{peer: some(p_i.name), phase: quote(enter), reason, context}`.
2. **Work phase** (only if every peer entered). Call `work(scope_handle)`.
   - Returns ordinarily: capture the return value as `result`; no failure yet.
   - Raises: the primary failure becomes
     `{peer: none("lifecycle-no-peer"), phase: quote(work), reason, context}`,
     normalized from the exception the same way R8 normalizes lifecycle
     exceptions (`reason`/`context` from the exception when it supplies them,
     otherwise a non-sensitive default).
3. **Unwind (exit) phase.** For every entered peer, in strict reverse
   attachment order, call `p_i.exit(scope_handle, primary_summary)`, where
   `primary_summary` is exactly `{status: quote(ok) | quote(error), phase,
   peer}` reflecting the outcome so far (never another peer's context or
   resources — only this narrow status summary is inward-visible during
   unwind).
   - `some("nil")`: no cleanup failure.
   - `err(reason, context)`: build `{peer: some(p_i.name), phase:
     quote(exit), reason, context}`.
     - If no primary failure exists yet (this is the first exit failure seen
       and enter/work fully succeeded), this failure becomes
       `primary_failure` instead of being appended to `cleanup_failures`.
     - Otherwise (a primary failure already exists, or an earlier exit
       failure in this same unwind was already promoted to primary),
       append it to `cleanup_failures` in exit-call order.
   Every entered peer's `exit` is attempted exactly once regardless of
   earlier exit failures; one peer's `exit` failing never skips another
   entered peer's `exit`.
4. Assemble the closed `LifecycleResult` from the outcome above.

This algorithm is identical for `lifecycle_scope` (`scope: quote(root)`),
`lifecycle_child` (`scope: quote(child)`), and one element application inside
`lifecycle_repeat` (`scope: quote(element)`); only the scope tag and the
element-only reserved context (below) differ.

### Partial-entry / failure matrix

| Peers attempted | Enter outcome | Work outcome | Exit calls made | `primary_failure` owner | `cleanup_failures` |
|---|---|---|---|---|---|
| `[A, B]`, both succeed | full | succeeds | `B.exit`, `A.exit` (reverse) | none (`status: ok`) | any exit failures among B, A |
| `[A, B]`, `B.enter` fails | partial (`A` entered) | skipped | `A.exit` only | `B` (enter) | `A.exit` failure, if any (never promoted — a primary already exists) |
| `[A, B]`, both enter, work raises | full | fails | `B.exit`, `A.exit` | work (no peer) | any exit failures among B, A |
| `[A, B]`, both enter, work succeeds, `B.exit` fails | full | succeeds | `B.exit` fails, `A.exit` runs | `B` (exit, promoted — first exit failure with no earlier primary) | `A.exit` failure only if it also fails |
| `[A, B]`, both enter, work succeeds, `A.exit` and `B.exit` both fail | full | succeeds | `B.exit` fails, `A.exit` fails | `B` (exit, promoted — first in reverse-call order) | `A.exit` failure |
| `[]` (no peers) | trivially full | runs | none | work's outcome only | `[]` |

Required default invariants (restated as this contract's exact algorithm
above): no global mutable current-scope switch exists anywhere in this
surface; a child's peers/work cannot read or mutate a sibling's or ancestor's
owned resources, only inward-readable context; child completion always
returns an ordinary `LifecycleResult` value to the caller and never
implicitly raises into the parent; child-owned resources are entered and
exited entirely inside the synchronous `lifecycle_child` call, so they cannot
outlive it; parent-owned resources are untouched by a child's unwind, since a
child's peer list is entirely separate data from the parent's.

## Vertical composition (parent/child)

`lifecycle_child(parent_handle, peers, work)` runs the algorithm above as a
new scope nested syntactically inside the parent's `work`. It is a plain
function call: the parent's `work` receives the parent handle, calls
`lifecycle_child` zero or more times (sequentially; R14 has no concurrent
child execution), and receives one ordinary `LifecycleResult` per call.

- **Result propagation is always explicit.** A child's `LifecycleResult` is
  ordinary data returned to the parent's `work`. Whether a failed child
  causes the parent's own work to fail is the parent `work` callable's
  choice — for example, by raising when `child_result.status ==
  quote(error)`, or by ignoring it and continuing (matching "child failure
  does not implicitly terminate the parent").
- **Context inheritance is read-only and inward-only.** Inside a child scope,
  `lifecycle_context(child_handle, name)` first checks the child's own
  entered peers (and, inside `lifecycle_repeat`, the element's reserved
  names), then its parent's exposed context, then that parent's parent, up
  to the root. A write is never possible through this accessor — only
  `enter` results and the reserved element/config names populate context.
- **Non-shadowing.** Attaching a peer (including the reserved `lifecycle_config`
  peer, named `quote(config)`) whose `name` collides with any name already
  exposed by an ancestor scope in the same chain is construction-time
  misuse. A child cannot rebind, shadow, or refresh an ancestor's exposed
  context or bound provider.
- **Ownership.** Because entry and unwind for one `lifecycle_child` call are
  fully synchronous and complete before the call returns, a child's peers
  can never hold a resource past that call, and a parent's peers/resources
  are never touched by a child's enter/exit at all (separate peer lists,
  separate `LifecycleInstance` pairings).

## Horizontal composition (peer attachment)

Peers on one scope operation are entered in attachment (list) order and
exited in strict reverse order — the middleware nesting the strategy
document requires:

```text
A.enter -> B.enter -> C.enter -> work -> C.exit -> B.exit -> A.exit
```

Attachment order is unrelated to parentage: peers on one scope are siblings,
none of them is the parent or child of another, and none of their `enter`
results are visible to a peer entered earlier in the same list (only to
peers entered *later* in the list, via `lifecycle_context`, and to `work`).
A peer's `enter` runs before any later peer's `enter`, so an earlier peer may
expose context a later peer's `enter` reads; a later peer's context is never
visible to an earlier peer.

A peer cannot mutate another peer's owned context, state, resources, or
configuration binding: `lifecycle_context` returns the exact value `enter`
produced with no copy-on-read mutation hook, and `exit` receives only the
scope-wide `primary_summary`, never another peer's raw context or resources.
Priority graphs, dependency resolution between peers, and concurrent peer
execution are outside R14; peer order is exactly the caller-supplied list
order, nothing else.

## Repeated element-scoped execution

```text
lifecycle_repeat(peers, source, element_work) -> [LifecycleResult, ...]   # source: List
lifecycle_repeat(peers, source, element_work) -> Flow<LifecycleResult>    # source: Flow
```

`lifecycle_repeat` distinguishes three lifetimes exactly as required:
the call itself has no lifecycle scope of its own (it is a pure dispatcher
over `source`'s existing List/Flow behavior); each consumed element gets one
fresh **element scope** running the full entry/work/unwind algorithm above
with `scope: quote(element)`; and any scope `element_work` creates via
`lifecycle_child` is a shorter nested lifetime under that element scope,
exactly as described in vertical composition.

Two reserved context names are populated automatically inside every element
scope, before any attached peer's `enter` runs, so peers may read them during
their own `enter`:

```text
lifecycle_context(element_handle, quote(element)) -> some(consumed_element)
lifecycle_context(element_handle, quote(index)) -> some(one_based_index)
```

`quote(index)` is the 1-based ordinal of this element among elements actually
pulled from `source` so far (the first consumed element is index `1`).
Attaching a peer literally named `quote(element)` or `quote(index)` to a
`lifecycle_repeat` peer list is construction-time misuse (reserved-name
collision, the same rule as ancestor non-shadowing above). These two names
are how a future ordinary lifecycle owns AWK-like `record`/`fields`/`nr`/`nf`
projections without `$0`/`$1`/`NR`/`NF` syntax: a peer or `element_work`
reads `quote(element)`/`quote(index)` through the same accessor as any other
context, then derives `record`, `fields`, `nr`, or `nf` as ordinary values
using existing Genia operations — R14 defines no such derived names itself.

**Eager (List) source.** Every element in `source` is processed, in order,
regardless of any individual element's `LifecycleResult` status — exactly
like `map` does not stop on an item an application later decides is invalid.
`lifecycle_repeat` never short-circuits a List source; the caller filters or
inspects `.status`/`.primary_failure` afterward using ordinary list
operations.

**Lazy (Flow) source.** `lifecycle_repeat` over a Flow returns a lazy,
single-use `Flow<LifecycleResult>` and performs no work until pulled,
preserving existing pull-based Flow laws. Pulling one item from the returned
Flow pulls **exactly one** item from `source` (no read-ahead, no buffering —
"no over-pull"), runs that element's complete entry/work/unwind algorithm
synchronously to completion, and yields its `LifecycleResult`. Because the
element scope is fully entered *and* unwound before its result is yielded,
bounded early termination of the returned Flow (the consumer simply stops
pulling, via `take`, a manual break, or downstream short-circuit) never
leaves an element scope partially entered: the most recently yielded
element's cleanup already ran before the consumer saw it. "Early-close
cleanup" therefore reduces to the existing Flow/source finalization rule for
`source` itself — R14 adds no new finalization mechanism, hook, or
capability.

**Filtering and Outcome values.** An `element_work` that returns `none(...)`
or `err(...)` as ordinary data is not treated specially by `lifecycle_repeat`
(per the general work-return rule): it is exactly `result: some(err(...))` (or
`some(none(...))`) on an otherwise `completed` `LifecycleResult`. Applications
compose existing `keep_some`/`map`/`filter` over the returned List/Flow of
`LifecycleResult` to select or report on individual elements; R14 introduces
no dedicated filtering primitive.

**Expired context.** As stated in the scope lifetime section, an
`element_handle` (and any context value obtained by copying, not reading
through it) becomes invalid the instant its element scope reaches
`completed`/`failed`. If `element_work` closes over the handle and a later,
independently-called function tries to read `lifecycle_context` on it after
that element's `LifecycleResult` was already yielded, that later call raises
the existing-pattern runtime error rather than silently returning stale or
leaked data. Element-local context that must outlive the element is copied
by `element_work` into an ordinary Genia value before returning; lifecycle
execution state is never application accumulator state — applications
continue to use ordinary values and `scan` for that.

## Lifecycle-owned configuration binding

```text
lifecycle_config(provider) -> LifecycleDefinition
```

`lifecycle_config(provider)` validates that `provider` is an existing,
already-constructed immutable R10/R13 provider value (the result of a
successful `config_provider`/`config_standard` call) and returns exactly one
`LifecycleDefinition` reserved under `name: quote(config)`:

```text
enter(scope_handle) -> some(provider)     # always succeeds; captures, does not acquire
exit(scope_handle, primary_summary) -> some("nil")   # always succeeds; nothing to release
```

Binding is attachment, not acquisition: `lifecycle_config` performs no
lookup, no source acquisition, no host capability call, and no provider
refresh. The bound provider is read, inward-only, by any peer or work in the
same scope or any descendant scope via
`lifecycle_context(handle, quote(config))`, then used exactly as an
explicitly hand-threaded provider would be: ordinary `config_view`/
`secret_view` construction, `config_get`/`secret_get`, existing Outcomes,
protected carriers, sinks, authority, and declassification are entirely
unchanged. R14 adds no bare configuration name, no ambient lookup, and no
`server.PORT`-style named access.

Because `quote(config)` is a reserved, non-shadowable peer name (see
vertical composition), at most one `lifecycle_config` peer may exist anywhere
in one root/child/element ancestry chain; a second attempt anywhere in that
chain — sibling scope trees may each bind their own — is construction-time
misuse. This is R14's entire configuration surface: it is one explicit,
immutable, non-refreshable binding, not dependency injection, not a service
container, and not a second provider implementation.

## HTTP operation representation

One inert, closed operation value underlies every supported method.
Construction and inspection perform no network IO.

```text
http_operation(method, base_url, path, headers, query, body)
  -> some(HttpOperation) | err("http-operation-invalid", {stage})
```

```text
HttpOperation {
  method: quote(get) | quote(post) | quote(put) | quote(patch) | quote(delete)
  base_url: string
  path: string
  headers: map<string, string | protected_secret_string>
  query: map<string, string>
  body: none("http-no-body")
      | {kind: quote(text), text: string}
      | {kind: quote(json), value: json_represented_value}
}
```

- **method**: exactly one of the five listed quoted symbols. Any other value
  is `err("http-operation-invalid", {stage: quote(method)})`. HEAD, OPTIONS,
  CONNECT, and TRACE are not in the approved R14 method set.
- **base_url**: `scheme "://" host [":" port]` where `scheme` is `"http"` or
  `"https"`, `host` is one or more ASCII letters/digits/`-`/`.`, and `port`
  (if present) is one or more ASCII digits. No userinfo, path, query, or
  fragment may appear in `base_url`; any of those, or an unsupported scheme,
  is `err("http-operation-invalid", {stage: quote(base_url)})`.
- **path**: must start with `/` and must not contain `?` or `#` (those
  belong to `query`). Path bytes are passed through exactly as supplied —
  R14 performs no percent-encoding, normalization, or trailing-slash
  handling on `path`; callers supply already-valid path segments.
- **headers**: keys are normalized to lowercase ASCII during construction.
  Two header entries whose lowercased names collide is construction-time
  misuse (no last-wins silent overwrite, unlike `with_headers`'s
  compositional merge — this is one-shot closed construction, not
  composition). A header value is either a plain string or exactly one R10
  protected `secret` value; any other shape is invalid. Query values may
  never be protected — a protected `query` entry is rejected at construction,
  so a credential must be carried in `headers`.
- **query**: plain string keys and values only. Serialized deterministically
  as `key=value` pairs sorted by key (map keys are already unique), each
  byte outside `ALPHA / DIGIT / "-" / "." / "_" / "~"` percent-encoded from
  its UTF-8 bytes, space encoded as `%20`, pairs joined by `&`, the whole
  thing prefixed with `?` only when `query` is non-empty.
- **body**: `none("http-no-body")`, or `{kind: quote(text), text}` encoded as
  UTF-8 bytes with an implicit `content-type: text/plain; charset=utf-8`
  unless `headers` already sets `content-type` explicitly, or
  `{kind: quote(json), value}` encoded through the existing `json_encode`
  capability with an implicit `content-type: application/json` unless
  `headers` overrides it. A `json_encode` failure surfaces as
  `err("http-operation-invalid", {stage: quote(body)})` from `http_operation`
  itself, before any child scope or transport attempt exists. Explicit
  headers always win over an implicit content-type; R14 never silently
  discards a caller-supplied header.
- Body presence is not restricted by `method` — an operation may carry a
  body regardless of method; that is an explicit application choice, not a
  portable prohibition.

`HttpOperation` is an ordinary closed map once constructed: it composes with
`display`, diagnostics, and any container operation exactly as any other map
containing a possibly-protected leaf, per R10's existing transport/derivation
and rendering/sink rules (see Protected HTTP sinks below). R14 adds no
`response` field to the constructed request value; the response is a
separate `HttpResponse` value returned by `web.http_send`, keeping the inert
request representation and the post-transport observation distinct.

## Outbound HTTP client lifecycle

```text
web.http_send(operation, authority, timeout_ms) -> some(HttpResponse) | err(reason, context)

HttpResponse {
  status: integer            # 100..599
  headers: map<string, string>
  body: <Bytes>               # existing opaque Bytes wrapper value
}
```

`web.http_send` is one ordinary, host-capability-backed function — not a
separate lifecycle primitive. The R14 "client lifecycle" is simply the
existing vertical-composition story applied to HTTP: an application calls
`web.http_send` from inside a `lifecycle_child`'s `work` (typically a child
of an R8 request scope), so a transport failure is contained by that child's
`LifecycleResult` exactly like any other child work failure — R14 adds no
second pipeline state machine or HTTP-specific scope kind. This composes the
five conceptual phases without new machinery: *prepare* is the already-inert
`operation` value plus the surrounding child scope's `enter`; *authorize* is
declassification inside `web.http_send`'s private host implementation,
described next; *send*/*receive* are the one synchronous host transport
attempt; *decode* is the caller's own explicit `utf8_decode`/`json_decode`
over `response.body`, not an automatic step; *finalize* is that child scope's
own `exit`, and the release of any host-local transport resource before
`web.http_send` returns (no connection, socket, or stream object ever
escapes to Genia code — nothing to keep alive between calls).

- **authority**: `none("nil")` when `operation.headers` carries no protected
  value, or `some(authority)` — an opaque R10 authority, exactly like R11's
  model-call credential argument — when it does. `authority`'s provider
  identity and purpose allowlist must match every protected header value's
  identity and the fixed purpose `quote(http_send)`; a missing or mismatched
  authority when a protected header is present is runtime misuse, exactly
  as for `declassify`, and no transport attempt is made.
- **timeout_ms**: required integer in `1..300000`, mirroring R11's model-call
  timeout contract. A configured deadline elapsing before the attempt
  completes is `err("http-timeout", {timeout_ms})`.
- Exactly one synchronous attempt is made per call: no automatic retry,
  redirect following, backoff, streaming, connection pooling, or
  cancellation handle. A 3xx/4xx/5xx response the host transport actually
  received is not a transport failure — it is an ordinary
  `some(HttpResponse)` with that `status`; only a failure to obtain any HTTP
  response at all is an `err`. Applications inspect `status` themselves;
  R14 defines no "expected status" or auto-throw-on-error behavior.
- Declassification of any protected header value happens inside
  `web.http_send`'s private host implementation immediately before the one
  transport attempt, using the existing `declassify(authority,
  protected_value)` operation — never earlier, never by application code.
  The existing R10 audit event fires on that declassification exactly as for
  any other use; no second audit mechanism is introduced.
- `response.body` is always an opaque `Bytes` value (existing `bytes.*`
  capability family), never auto-decoded, auto-parsed, or content-type
  sniffed. `response.headers` keys are lowercased; R14 does not define
  behavior for a host transport that reports the same header name twice
  beyond "the host-supplied normalized map wins," which is Python-host
  implementation detail, not portable contract.
- No redirect is ever followed automatically. No response body or total
  transfer size limit is imposed by the portable contract; a future
  Python-host capability may impose its own resource limits as host policy,
  not as a portable observation.

Recoverable failure reasons are exactly:

```text
err("http-timeout", {timeout_ms})
err("http-transport-failure", {kind: quote(connect) | quote(tls) | quote(dns) | quote(other)})
err("http-response-invalid", {stage: quote(status) | quote(headers) | quote(body)})
```

Runtime misuse covers a malformed `operation`/`authority`/`timeout_ms`
argument, a protected header present with no matching authority, and a
non-protected `authority` value. Diagnostics for all of the above never
include header/query/body content, the URL, or any declassified string.

## Protected HTTP sinks

R10 remains fully authoritative; R14 introduces no new protected-value
mechanism, only one new sink family (`http_operation`/`web.http_send`) and
one new declassification purpose (`quote(http_send)`), exactly the same
extension shape R11 used for `quote(model_call)`.

- A protected header value stays protected through `http_operation`
  construction, through storage inside the resulting `HttpOperation` map,
  and through any later inspection, `display`, diagnostic rendering, or
  JSON/CSV/Sheet/report serialization of that operation value — R10's
  existing recursive sink-scan rules apply to `HttpOperation` exactly as to
  any other ordinary map holding a protected leaf, with no special case.
- The only place a protected header's carried string is ever read is inside
  `web.http_send`'s private host implementation, at the single point
  immediately before the transport attempt, through the existing
  `declassify` boundary described above.
- `HttpResponse` values are always ordinary. Response headers/status/body
  bytes returned by a real upstream server can never carry R14/R10
  protection; this reuses R10's existing "JSON decode cannot produce
  protection" rule (extended to HTTP decode generally: a boundary that
  produces a value from external bytes never manufactures protection).
- Test failure output, native-assertion redaction, and diagnostic rendering
  for any of the above follow R10's existing `<protected>` redaction rules
  verbatim; R14 defines no separate redaction format.

## Failures and diagnostics

Recoverable lifecycle-core reasons are exactly the ones an `enter`/`exit`
callable itself chooses to return via `err(reason, context)` (application-
defined, not fixed by R14 — R14 fixes only the envelope: `peer`, `phase`,
`reason`, `context`) plus these R14-defined runtime-misuse identifiers used
at each construction/consumption boundary described above:
`lifecycle-scope-expired` (a handle used outside its scope's `entering`/
`active`/`exiting` window), reserved-name collision at construction
(`quote(config)`, `quote(element)`, `quote(index)`), and duplicate/ambiguous
header construction. Recoverable HTTP reasons are exactly `http-operation-invalid`,
`http-timeout`, `http-transport-failure`, and `http-response-invalid`, as
defined above. Diagnostics never include raw header/query/body content,
declassified credential text, provider identity/contents, or authority.

## Portability boundary

### Portable language obligations

- `LifecycleDefinition`/`ExecutionScope`/`LifecycleInstance` vocabulary
  separation; the six-function public surface; the closed `LifecycleResult`
  and scope-state-machine rules; the entry/work/unwind algorithm and its
  partial-entry/failure matrix; non-shadowing and inward-only context
  visibility, vertically and horizontally; the repeated-element reserved
  context names, eager/lazy source rules, and expired-handle behavior; the
  `lifecycle_config` binding, its reservation, and its non-acquisition
  semantics; the `HttpOperation` shape, construction grammar, and
  normalization rules; the `web.http_send` call contract, failure reasons,
  and protected-sink rules.
- All of the above compose with unchanged Flow/Seq laws, unchanged Outcomes,
  unchanged R9 representations, and unchanged R10/R13 provider/protected-value
  semantics.

### Host capabilities

- No host capability is added by #620. A later ticket (E14-6, roadmap #623)
  supplies exactly one narrow outbound HTTP transport capability that
  `web.http_send` calls after local validation and declassification; that
  capability accepts a fully-normalized request (method, absolute URL, byte
  headers, byte body) and returns normalized status/headers/bytes or a
  normalized transport failure, mirroring the existing `config.dotenv-snapshot`
  and `model.gemini-rest` capability documentation shape in
  `docs/host-interop/capabilities.md`.
- Future hosts must implement the same advertised transport boundary or
  report it unavailable (`err("http-transport-failure", {kind:
  quote(other)})` when no such capability is advertised); they may not
  redefine lifecycle or HTTP policy, add redirect-following, retry, or
  connection pooling as if it were portable, or weaken protected-sink
  behavior.

### Python reference host

No Python behavior is implemented by #620. A later ticket implements the
lifecycle core (`lifecycle_scope`, `lifecycle_child`, `lifecycle_repeat`,
`lifecycle_context`, `lifecycle_config`) as ordinary Python-reference-host
support over the algorithm above, and a separate later ticket implements
`http_operation`/`web.http_send` over the one narrow transport capability.
Python exception types, socket/connection objects, and any HTTP client
library used internally are not portable contract.

Core IR and parser impact: **none**. R14 introduces no syntax, annotation
expression form, AST node, or Core IR node; every operation above is an
ordinary call over ordinary closed values.

## Conformance obligations

Later R14 tickets must add, before implementation, failing coverage for:

- shared eval/error cases for the entry/work/unwind algorithm, including
  every row of the partial-entry/failure matrix, for `lifecycle_scope`,
  `lifecycle_child`, and one `lifecycle_repeat` element
- shared eval/flow cases proving List exhaustiveness, Flow one-pull-per-element
  laziness, no over-pull, early-stop cleanup completeness, and expired-handle
  misuse for both source kinds
- shared eval/error cases for non-shadowing (ancestor context, reserved
  `quote(config)`/`quote(element)`/`quote(index)` names) and for inward-only,
  read-only context visibility across peers and across parent/child
- focused Python tests plus shared eval/error cases for `lifecycle_config`
  binding visibility across descendants, non-acquisition, and non-refresh
- portable parser fixtures plus focused tests for every `HttpOperation`
  construction rule (method/base_url/path/headers/query/body), the query
  percent-encoding table, and implicit-vs-explicit content-type precedence
- focused Python loopback-transport tests plus shared eval/error cases for
  `web.http_send` timeout, transport-failure, response-invalid, and
  any-received-status-is-success behavior, with no live network dependency
- recursive protected-sink scans proving a protected header value never
  leaks through `HttpOperation` display/diagnostic/serialization paths, and
  that declassification happens exactly once, immediately pre-transmission
- parse/Core IR regression proving only existing ordinary call/value forms
  are used
- file, command, pipe, import, native-test, and serve-startup cross-mode
  observations proving import/load performs no lifecycle activation and no
  network IO

The repeated-record proving case (roadmap #695) must configure one
pipeline/session scope, fresh element scopes, at least two peer
`LifecycleDefinition`s per element (for example a record-context peer and a
diagnostics peer), deterministic enter/work/reverse-unwind order, the
reserved `quote(element)`/`quote(index)` context read into ordinary
`record`/`fields`/`nr`/`nf`-style values by application code (never new
syntax), no cross-element or post-scope context leakage, and correct cleanup
on both an individual element's work failure and bounded early Flow
termination. It adds no new API or semantics beyond this contract.

The HTTP vertical proving case (roadmap #628) must configure a YouVersion
base URL, Bible/version ID, and protected API credential entirely through
R13/R10 (via a `lifecycle_config`-bound provider), construct one
`http_operation`, call `web.http_send` from inside a `lifecycle_child` of an
R8 request scope, decode the returned `HttpResponse.body` explicitly, and
demonstrate that a contained client-child failure does not stop the R8
server. Automated tests use a controlled local upstream and fake credentials;
CI must not depend on YouVersion, public network availability, or a real
credential. The example proves composition only; it adds no Bible-specific
semantics or human-reference parser.

## Non-goals

R14 does not include:

- an AWK language mode or `$0`/`$1`/`NR`/`NF` syntax; the reserved
  `quote(element)`/`quote(index)` context names are read through the
  ordinary `lifecycle_context` accessor, never bound as lexical identifiers
- mutable lifecycle injection into lexical bindings, or a mutable/ambient
  "current scope" value
- lifecycle as a replacement for `map`, `filter`, `scan`, `refine`, or `rules`
- implicit context capture by lazy values (context access past scope
  validity always fails loud; see the scope lifetime state machine)
- a general arbitrary lifecycle-plan/action registry or resolver over R4
  plan data
- annotation-driven lifecycle discovery of any kind (no `@setup`, `@teardown`,
  or similar); all attachment is explicit `peers` list arguments
- async/await syntax, a scheduler, actor supervision, distributed execution,
  or concurrent peer/child execution
- concurrent server guarantees beyond R8's existing ones
- WebSockets, SSE, streaming request/response bodies, or HTTP/2-specific
  semantics
- connection-pool configuration, automatic retries, circuit breakers,
  cookies, redirect following, or a general auth framework
- dependency injection or a service container; `lifecycle_config` is one
  explicit, non-refreshable, non-shadowable binding of an already-constructed
  provider, nothing more
- a second server/routing/CORS or configuration system
- HEAD, OPTIONS, CONNECT, TRACE, or any method beyond the five listed
- `@get`/`@post`-style declarative HTTP annotations (planned no earlier than
  roadmap #626, over this same inert `HttpOperation`/`web.http_send`
  surface, and still inert descriptors, not self-executing IO)
- human-language Bible-reference parsing or YouVersion-specific language APIs
- a browser runtime or multi-host implementation

## Proving cases

### Minimal vertical/horizontal composition

```text
peers = [A, B]  # LifecycleDefinition values, ordinary application data
lifecycle_scope(peers, fn(scope) ->
  lifecycle_child(scope, [], fn(child) -> ordinary_work(child))
)
```

Expected shape: `A.enter -> B.enter -> (child scope entered and fully
unwound inside work) -> B.exit -> A.exit`, with the outer `LifecycleResult`
carrying the child's own `LifecycleResult` only if `work` chose to include it
in its return value.

### Repeated record proof (pressure test)

```text
peers = [record_context_peer, diagnostics_peer]
lifecycle_repeat(peers, records |> lines, fn(scope) ->
  record = lifecycle_context(scope, quote(element)) |> unwrap_or(none)
  nr     = lifecycle_context(scope, quote(index)) |> unwrap_or(none)
  process_record(record, nr)
)
```

Expected shape: one `LifecycleResult` per line, each with its own fully
entered-and-unwound `record_context`/`diagnostics` peers and no context
visible across elements.

### HTTP vertical proof (pressure test)

```text
provider = config_standard(overrides, argv()) |> unwrap_or(none)
config_peer = lifecycle_config(provider)
lifecycle_scope([config_peer], fn(root) ->
  lifecycle_child(root, [], fn(request) ->
    prov = lifecycle_context(request, quote(config)) |> unwrap_or(none)
    base = config_view(prov, "YOUVERSION_")("BASE_URL") |> unwrap_or(none)
    key  = secret_view(prov, "YOUVERSION_", quote(http_send))("API_KEY") |> unwrap_or(none)
    op = http_operation(quote(get), base, "/v1/bible", {authorization: key}, {}, none("http-no-body")) |> unwrap_or(none)
    lifecycle_child(request, [], fn(client) -> web.http_send(op, some(authority), 5000))
  )
)
```

Expected shape: the protected `key` value is never printed, logged, or
serialized anywhere along this chain; it is declassified exactly once,
inside `web.http_send`, immediately before the one transport attempt.

## Reconciled R14 sequence

Every behavior issue runs its own complete repository phase workflow;
issue numbering follows `docs/strategy/r14-composable-lifecycles.md` and
`docs/strategy/release-roadmap.md`. Later issues are created or reclassified
as "Current release: R14" only after this contract records explicit GO.

1. **#620 — E14-0 (this document):** composable lifecycle and HTTP contract.
2. **#621 — E14-1 (implemented):** lifecycle instance and parent/child
   execution scopes (`lifecycle_scope`, `lifecycle_child`,
   `lifecycle_context`, the state machine, and the entry/work/unwind
   algorithm, without HTTP). Peer-list mechanics are implemented as one
   general algorithm (shared, unchanged, by every later slice per this
   contract's own "Vertical composition" section); #692 owns proving
   broader multi-peer attachment/ordering breadth, not introducing peers
   for the first time.
3. **#692 — E14-2 (implemented):** peer lifecycle attachment and
   deterministic unwind (multi-peer `peers` lists, the partial-entry/failure
   matrix), proven at three-or-more-peer breadth over the same E14-1
   algorithm with no runtime-code change.
4. **#693 — E14-3 (implemented):** repeated element-scoped lifecycle
   execution (`lifecycle_repeat` over List and Flow, reserved
   element/index context), composed with no change to the E14-1/E14-2
   entry/work/unwind algorithm.
5. **#694 — E14-4:** lifecycle-owned configuration provider binding
   (`lifecycle_config`, reservation/non-shadowing, R10/R13 preservation).
6. **#622 — E14-5:** common HTTP operation representation (`http_operation`,
   `HttpOperation`, construction grammar, no IO).
7. **#623 — E14-6:** Python host outbound HTTP transport capability (the one
   narrow advertised capability `web.http_send` calls internally).
8. **#624 — E14-7:** outbound HTTP client lifecycle (`web.http_send` over
   E14-5 + E14-6, composed with E14-1's child scopes).
9. **#625 — E14-8:** protected HTTP credential sinks (the `quote(http_send)`
   purpose, declassification timing, and non-leakage proof over E10).
10. **#626 — E14-9:** declarative outbound HTTP annotations (inert method
    metadata over the E14-5/E14-7 surface; still no self-executing IO).
11. **#627 — E14-10:** server/request/outbound-client composition (nesting
    E14-7 client children under R8 request scopes via E14-1/E14-2).
12. **#695 — E14-11:** repeated record lifecycle proving case (over E14-3 +
    E14-2, no AWK syntax).
13. **#628 — E14-12:** YouVersion Bible proxy proving application (over
    E14-4 + E14-10, controlled upstream, no real network/credential in CI).
14. **#696 — E14-13:** cross-mode lifecycle and HTTP hardening (inertness,
    every failure matrix row, laziness, diagnostics, protection,
    capability-unavailable normalization, parse/Core IR regression).
15. **#629 — E14-14:** release examples and implemented-truth synchronization
    (documentation only; no runtime change).
16. **#630 — E14-15:** release truth audit and distillation (audit only; no
    runtime change).

Dependency shape (unchanged from the strategy document; recorded here for
convenience):

```text
#620
├── #621 → #692 → #693 → #695
│             └── #694
└── #622 → #623
          #621 + #622 + #623 → #624 → #625 → #626
          #692 + #624 + #626 → #627
          #694 + #627 → #628

#693 + #694 + #627 + #628 + #695 → #696 → #629 → #630
```

Each behavior issue commits failing tests before implementation and
references that commit from its implementation phase. E14-14 reconciles
implemented slices into runnable examples and documentation truth; docs never
lead behavior. E14-15 adds no behavior.

## Gate

**GO for E14-4 preflight only**, now that issue #693 has implemented and
tested E14-3 against this contract. This document itself authorizes no
further implementation, tests, later ticket creation, or implemented-behavior
documentation beyond what #621, #692, and #693 have already landed and
`GENIA_STATE.md` sections 9.8-9.10 record. Every later E14 ticket must name
#620/#621/#692/#693 and its own earlier dependencies, distinguish
portable semantics from Python reference-host capability work, and preserve
R4 vocabulary, R8 server behavior, Flow/Seq laws, R9 composition, R10
protected semantics, and R13 provider/view semantics exactly as this
document states them.
