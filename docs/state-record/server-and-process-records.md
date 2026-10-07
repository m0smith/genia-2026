# Server and process record

> **Non-authoritative provenance record.** This file preserves, verbatim and unedited, text that was displaced
> from `GENIA_STATE.md` during the #1099 distillation. It is audit material, not part of the truth hierarchy:
> it does not define Genia behavior, and `GENIA_STATE.md` governs. Start with the release, design, and reference
> documents; open this file only to see the exact displaced wording.
>
> Baseline: `GENIA_STATE.md` at `d401f322c692e8c3620509854065692c2605c61a`. Scope: Pre-condensation text of the CORS wrapper, 9.7 R8 server execution contract, and 9.40 external process execution.
> Ledger: `docs/analysis/state-distillation-migration-map.json`.

## B090: baseline lines 1850-1865

Moved from GENIA_STATE.md@d401f322, lines 1850-1865 (ledger row B090, retained-condensed, sha256 e95b4e99887f6379)

~~~~~markdown
### CORS handler wrapper (**Partial**, issue #527)

Implemented and verified in the Python reference host:

- public Python-reference-host web-module call shape: `cors(policy, handler) -> handler`
- `policy` is a closed Option Record Pattern with optional fields `origin`, `methods`, and `headers`; omitted fields use these defaults:
  - `origin: "*"`
  - `methods: ["GET", "POST", "OPTIONS"]`
  - `headers: ["content-type"]`
- `origin` must be a non-empty string; `methods` and `headers` must be non-empty lists whose entries are non-empty strings
- policy strings are preserved exactly; no trimming, case normalization, duplicate removal, origin reflection, allowlist matching, HTTP token validation, or request-policy negotiation is introduced
- methods and headers serialize in list order with `", "` between entries
- every decorated response contains:
  - `access-control-allow-origin: <origin>`
  - `access-control-allow-methods: <serialized methods>`
  - `access-control-allow-headers: <serialized headers>`
~~~~~

## B091: baseline lines 1866-1881

Moved from GENIA_STATE.md@d401f322, lines 1866-1881 (ledger row B091, retained-condensed, sha256 ce2182985a8a1fdb)

~~~~~markdown
- a request is a true CORS preflight only when its `method` field is exactly `"OPTIONS"` and its lowercased `headers` map contains both `origin` and `access-control-request-method`; header values are not otherwise interpreted
- a true preflight does not invoke the wrapped handler and returns `response(204, cors_headers, none)`; the response is bodyless at the HTTP transport
- an `OPTIONS` request missing either required preflight header is ordinary and delegates to the wrapped handler
- every other request invokes the wrapped handler exactly once, then decorates its returned response solely through `with_headers(cors_headers, response)`; `with_headers` therefore owns response validation, lowercase normalization, collision precedence, preservation, and non-mutation behavior
- configured CORS headers override case-insensitive collisions in an ordinary handler response; unrelated headers, status, body, and additional response fields are preserved
- the policy map, policy lists, request map, handler response, and existing response headers are not mutated
- validation occurs when `cors(policy, handler)` is called, before the returned handler exists; validation order is: policy map, unknown fields in map iteration order, `origin`, `methods`, method entries in list order, `headers`, header entries in list order, handler callable
- malformed inputs raise `TypeError` with these exact messages:
  - `cors expected policy to be a map`
  - `cors unexpected policy field <field>` where `<field>` uses debug rendering
  - `cors expected policy.origin to be a non-empty string`
  - `cors expected policy.methods to be a non-empty list`
  - `cors expected policy.methods item at index <index> to be a non-empty string`
  - `cors expected policy.headers to be a non-empty list`
  - `cors expected policy.headers item at index <index> to be a non-empty string`
  - `cors expected handler to be callable`
~~~~~

## B092: baseline lines 1882-1895

Moved from GENIA_STATE.md@d401f322, lines 1882-1895 (ledger row B092, retained-condensed, sha256 a792093f635d7d06)

~~~~~markdown
- entry indexes are zero-based
- request-shape or wrapped-handler failures retain existing callable and response behavior; `cors` does not return an Outcome or translate failures
- this adds no header-map-only CORS API, public `options(...)` route, `json`/`text` overload, credentials policy, origin reflection/allowlist, per-route override, general middleware chain, parser syntax, Core IR node, shared spec, or cross-host portability claim
- `print(...)` writes to `stdout`
- `log(...)` writes to `stderr`
- `input()` remains interactive-only and does not consume the flow/stdin source path
- broken pipe on `stdout` output is treated as normal downstream termination in CLI/file/command execution (no Python traceback)
- flow-driven stdout writes use the same quiet broken-pipe path, so Unix pipelines can stop downstream early without noisy Python tracebacks
- broken pipe on `stderr` is handled best-effort and does not trigger recursive noisy failures
- on Windows console streams, `clear_screen` and `move_cursor` try to enable virtual terminal processing before writing ANSI control codes

Representation System entry points (#185, implemented):

- `display(value)` and `debug_repr(value)` are the first concrete public surface of the planned Representation System.
~~~~~

## B093: baseline lines 1896-1921

Moved from GENIA_STATE.md@d401f322, lines 1896-1921 (ledger row B093, retained-condensed, sha256 03603e0971529d68)

~~~~~markdown
- They are entry points into that system, not independent formatting utilities.
- Representation renders values as strings for output and debugging.
- Representation does not change value identity.
- Representation is separate from value templates; value templates describe or constrain values, while representation formats describe output strings.
- `display(value)` returns a string containing the user-facing display representation of `value`.
- `debug_repr(value)` returns a string containing the debug representation of `value`.
- `display(value)` and `debug_repr(value)` render Outcome values directly, including `none(...)`; ordinary none propagation must not bypass these representation entry points. This is representation behavior only and does not change Outcome identity, direct-call none propagation for other functions, or pipeline propagation.
- `format(template_or_format, values)` is a public prelude-backed helper for building strings from a small placeholder template.
- `format(template_or_format, values)` returns a string and does not write output.
- `format(template_or_format, values)` does not mutate the input template, `Format` value, or values map/list.
- The first argument to `format` is either a raw string template or a `Format` value (see below).
- `format` supports:
  - named placeholders such as `{name}`, looked up in a map by string key
  - field-path placeholders (**Experimental**, #290): `{user.name}`, `{user.address.city}` — dot-separated named segments resolved left-to-right through nested map-like values; each segment must match `[A-Za-z_][A-Za-z0-9_]*`; field paths are lookup-only and not general template expressions
  - positional placeholders such as `{0}`, looked up in a list by zero-based index
  - escaped braces `{{` and `}}`
  - debug placeholders (**Partial**, #170): `{name:?}` and `{0:?}` render the resolved value with the same debug representation as `debug_repr(value)`
  - field format specs (**Experimental**, #169): a limited set of display specifiers after `:` inside a placeholder:
    - `<N` — left-align in width N using spaces
    - `>N` — right-align in width N using spaces
    - `^N` — center-align in width N using spaces; odd padding adds the extra space on the right
    - `.N` — truncate string value to first N characters; or format numeric value to exactly N decimal places (ties away from zero)
    - `0N` — zero-pad numeric output to width N; negative values keep the sign before the zeros
    - `,` — comma-group numeric output (integer portion only, ASCII commas, no localization)
  - `bool` values are not numeric for spec purposes; numeric specs (`0N`, `,`) applied to bools fail deterministically
  - combined specs, bare width specs (e.g. `{n:10}`), debug spec combinations (e.g. `{x:?>10}`), and any spec not listed above are unsupported and fail with a `format-error:` prefixed error
~~~~~

## B094: baseline lines 1922-1944

Moved from GENIA_STATE.md@d401f322, lines 1922-1944 (ledger row B094, retained-condensed, sha256 8ce044753791f1d9)

~~~~~markdown
- Field-path placeholder resolution (#290): a missing top-level or nested segment fails with `format missing field: <path>`; a non-map intermediate fails with `format expected a map while resolving placeholder path: <path>`; invalid path syntax (empty segment, leading/trailing/double dot, slash-separated paths, brackets, calls) fails with `format invalid placeholder`; slash (`/`) is not a field-path separator and must not be used in field-path placeholders.
- Placeholder replacements use the same user-facing display representation as `display(value)`, except where the exact debug spec `?` or another listed field spec applies.
- Missing fields and invalid placeholders raise deterministic errors.
- `format` does not support interpolation string syntax, localization, tag-based format selection, custom formatter protocols, list indexing in field paths, optional chaining, filters, or spec combinations beyond the listed subset.
- `Format(template)` and `Format(template, tag)` are first-class Representation System constructors (**Experimental**, #168, #292):
  - `Format(template)` accepts a string template and returns an untagged first-class `Format` value.
  - `Format(template, tag)` accepts a string template and a non-empty string tag and returns a tagged first-class `Format` value.
  - `Format` is for output representation and does not affect value identity.
  - `Format` is separate from value templates.
  - A `Format` value is representation-only: it is not a Value Template and does not participate in shape/refinement/contract/variant semantics.
  - The tag is representation metadata attached to the `Format` value only. It does not affect placeholder parsing, placeholder resolution, field-spec rendering, debug field specs, or the identity of values being formatted.
  - `format(Format(template), values)` and `format(Format(template, tag), values)` produce the same result as `format(template, values)` for the same template and values.
  - A `Format` value can be assigned to a name, passed as an argument, stored in a list or map, and returned from a function.
  - `display(Format(...))` returns `<format>`; the wrapped template and tag are not exposed.
  - `debug_repr(Format(...))` returns `<format>`; the wrapped template and tag are not exposed.
  - `Format()` fails with `TypeError: Format expected 1 or 2 args, got 0`.
  - `Format(template, tag, extra)` fails with `TypeError: Format expected 1 or 2 args, got 3`.
  - `Format(non_string)` fails with `TypeError: Format expected template string, received <type>`.
  - `Format(template, non_string_tag)` fails with `TypeError: Format expected tag string, received <type>`.
  - `Format(template, "")` fails with `TypeError: Format expected non-empty tag string`.
  - `format(non_string_non_format, values)` fails with `TypeError: format expected a string template or Format value, received <type>`.
  - No parser syntax such as `Format "..."` is introduced; `Format("...")` and `Format("...", "tag")` are the only accepted call forms.
  - `Format` is Experimental. The wrapped template, tag, display/debug text, and constructor surface may change before stabilization.
~~~~~

## B095: baseline lines 1945-1966

Moved from GENIA_STATE.md@d401f322, lines 1945-1966 (ledger row B095, retained-condensed, sha256 1747f89adcc4fad8)

~~~~~markdown
- `format_template(fmt)` is a public Representation System helper (**Experimental**, #294):
  - `format_template(fmt)` returns the original source template string supplied to `Format(...)`.
  - Accepted: a `Format` value created by `Format(template)`.
  - Rejected: raw strings, numbers, lists, maps, booleans, flow values, and any other non-Format value.
  - `format_template(fmt)` returns the template string exactly: no normalization, no unescaping, no placeholder parsing.
  - `format_template("{a}")` fails with `TypeError: format_template expected a format, received string`.
  - `format_template(non_format)` fails with `TypeError: format_template expected a format, received <type>`.
  - `display(Format(...))` and `debug_repr(Format(...))` remain opaque; `format_template` is the only approved way to recover the source template string.
  - `format_template` does not expose compiled template internals, placeholder metadata, or parsed template structure.
  - `format_template` does not apply to composed `Format` values created by `format_compose(...)`. Calling `format_template` on a composed format fails with `TypeError: format_template expected an atomic Format value`.
  - `format_template` is not explicitly none-aware; ordinary none propagation applies in pipelines.
  - `format_template` is Experimental. The accessor name and behavior may change before stabilization.
- `format_tag(fmt)` is a public Representation System helper (**Experimental**, #292):
  - `format_tag(fmt)` returns `some(tag)` for a tagged `Format` value created with `Format(template, tag)`.
  - `format_tag(fmt)` returns `none("missing-format-tag")` for an untagged `Format` value created with `Format(template)`.
  - Accepted: a `Format` value created by `Format(template)` or `Format(template, tag)`.
  - Rejected: raw strings, numbers, lists, maps, booleans, flow values, and any other non-Format value.
  - `format_tag()` fails with `TypeError: format_tag expected 1 arg, got 0`.
  - `format_tag(fmt, extra)` fails with `TypeError: format_tag expected 1 arg, got 2`.
  - `format_tag(non_format)` fails with `TypeError: format_tag expected a format value, received <type>`.
  - `format_tag` does not expose the template, alter rendering, or cause tag-based format dispatch.
  - `format_tag` is Experimental. The helper name and behavior may change before stabilization.
~~~~~

## B096: baseline lines 1967-1983

Moved from GENIA_STATE.md@d401f322, lines 1967-1983 (ledger row B096, retained-condensed, sha256 48f2b4cef124ecfb)

~~~~~markdown
- `format_compose(parts)` is a public Representation System helper (**Experimental**, #293):
  - `format_compose(parts)` accepts a list of format pieces and returns a new `Format` value.
  - Each piece in `parts` must be either a raw string template or a `Format` value (including another composed `Format`).
  - Rendering a composed `Format` with `format(composed_fmt, values)` renders each piece in order with the same `values` map and concatenates the resulting strings.
  - Empty composition is valid: `format(format_compose([]), {})` returns `""`.
  - Nested composition is valid: composed `Format` values may be used as pieces in later composition.
  - Repeated placeholders are allowed and read the same value from the input map.
  - All placeholders in a composed `Format` share the same input namespace; there is no per-piece namespace.
  - Composition adds no separators, whitespace, or newlines; separators must be explicit pieces.
  - `format_compose(parts)` is pure: it does not mutate `parts`, any piece, or any values map.
  - `display(format_compose(...))` and `debug_repr(format_compose(...))` return `<format>`.
  - `format_template` does not apply to composed `Format` values; calling it on a composed format fails with a deterministic `TypeError`.
  - `format_compose(non_list)` fails with `TypeError: format_compose expected list of format pieces, received <type>`.
  - `format_compose([..., invalid, ...])` fails with `TypeError: format_compose expected string or Format at index <n>, received <type>` (zero-based index).
  - Missing placeholder behavior during rendering is unchanged: existing missing-placeholder errors apply.
  - `format_compose` does not add parser syntax, Core IR behavior, control flow, expression evaluation, localization, debug mode, tagged dispatch, field paths, or Value Template behavior.
  - `format_compose` is Experimental. The helper name and behavior may change before stabilization.
~~~~~

## B097: baseline lines 1984-1997

Moved from GENIA_STATE.md@d401f322, lines 1984-1997 (ledger row B097, retained-condensed, sha256 c6ae869089040627)

~~~~~markdown
- These helpers do not write to `stdout` or `stderr`.
- These helpers do not mutate runtime state.
- These helpers do not change `print`, `log`, `write`, `writeln`, REPL result display, CLI final-result rendering, or pipeline semantics.
- `print(value)`, `log(value)`, `write(sink, value)`, and `writeln(sink, value)` remain output operations; `display(value)` and `debug_repr(value)` return ordinary strings.
- For ordinary runtime data, the minimal implemented representation behavior is:
  - strings: `display("x")` returns `x`; `debug_repr("x")` returns `"x"` with debug escaping
  - numbers: both return ordinary numeric text
  - booleans: both return `true` or `false`
  - `none`: both return `none("nil")`
  - `none(reason)` and `none(reason, context)`: both preserve structured absence syntax and context metadata
  - `some(value)`: both preserve the `some(...)` wrapper and recursively represent the inner value
  - lists: both return bracketed list syntax and recursively represent items
  - maps: both return brace map syntax and recursively represent keys and values
  - pairs / quoted syntax data: both preserve the existing pair-shaped representation syntax
~~~~~

## B098: baseline lines 1998-2012

Moved from GENIA_STATE.md@d401f322, lines 1998-2012 (ledger row B098, retained-condensed, sha256 46d14d21ebecb4f2)

~~~~~markdown
- Wrong arity fails through the ordinary callable arity/type-error path.
- Examples:
  - `display("hello")` evaluates to the string `hello`
  - `debug_repr("hello")` evaluates to the string `"hello"`
  - `format("display={x} debug={x:?}", {x: "hello"})` evaluates to the string `display=hello debug="hello"`
  - `display(none("missing-key", {key: "name"}))` evaluates to the string `none("missing-key", {key: name})`
  - `debug_repr([some("x"), false])` evaluates to the string `[some("x"), false]`
  - `format_template(Format("{a} {b}"))` evaluates to the string `{a} {b}`
  - `format_template(Format("{{escaped}}"))` evaluates to the string `{{escaped}}`
  - `format_tag(Format("{name}", "person-card"))` evaluates to `some("person-card")`
  - `format_tag(Format("{name}"))` evaluates to `none("missing-format-tag")`
  - `format(Format("{name}", "person-card"), {name: "Ada"})` evaluates to the string `Ada`
  - `format(format_compose(["Hello, ", Format("{name}"), "!"]), {name: "Matt"})` evaluates to the string `Hello, Matt!`
  - `format(format_compose([]), {})` evaluates to the string `""`
  - `format(format_compose(["{x}", " / ", "{x}"]), {x: "go"})` evaluates to the string `go / go`
~~~~~

## B099: baseline lines 2013-2018

Moved from GENIA_STATE.md@d401f322, lines 2013-2018 (ledger row B099, retained-condensed, sha256 d1dff099c2d372de)

~~~~~markdown
- Runtime capability values and function-like values may have host-specific opaque debug/display text in this phase unless a later contract explicitly stabilizes them.
- #185 does not define the full Representation System.
- #166 owns the broader representation model, including naming boundaries beyond `display` and `debug_repr`, extension points, user-defined representations, registry/strategy behavior, and cross-host treatment of opaque runtime values.
- #185 must not introduce alternate public representation terms such as `render`, `view`, or `repr`.
- If #166 later changes the canonical public names, #185 behavior must migrate through the alias-safe rename process: introduce alias, migrate usage incrementally, update tests, then remove the old name in a later phase.

~~~~~

## B179: baseline lines 3768-3781

Moved from GENIA_STATE.md@d401f322, lines 3768-3781 (ledger row B179, retained-condensed, sha256 39480321063cfb22)

~~~~~markdown
## 9.7) R8 server execution contract

Status: Implemented. The independently callable lifecycle core (issue #534), inert route/server/CORS annotation bindings (issues #535-#537), and explicit CLI/live HTTP integration (issue #533) are implemented as Experimental Python-reference-host-only behavior. The descriptor and lifecycle-result shapes are host-independent; execution remains Python-reference-host-only in R8. Defined in issue #558.

LANGUAGE CONTRACT (PARTIALLY IMPLEMENTED):

- `genia serve <file>` is the only server-lifecycle activation boundary. Loading, importing, parsing, evaluating, or discovering a file in any other execution mode must not bind a listener, run a route handler, apply CORS, or enter server cleanup.
- Serve mode loads and evaluates exactly one entry file without ordinary `main/0` or `main/1` dispatch. An evaluation failure is a startup failure and prevents listener activation.
- R8 uses the existing prefix-annotation grammar, AST, and Core IR. Each server annotation takes one ordinary map expression on the annotation line; no call-like annotation syntax is added.
- Server annotations store inert descriptor maps under metadata keys `server`, `route`, and `cors`. `@server`, `@route`, and `@cors` metadata attachment are implemented. Descriptor value expressions are evaluated after their target binding exists, using the existing top-to-bottom annotation evaluation rule. An invalid implemented descriptor fails metadata attachment deterministically in every execution mode; a valid descriptor has no behavioral effect outside serve mode.
- `@server config` is valid only on a top-level simple-name assignment. Exactly one `@server` descriptor is required in the serve entry file. Its closed map accepts only optional `host`, `port`, and `max_requests` fields and uses the exact validation/default behavior of `serve_http`: `host` defaults to `"127.0.0.1"`, `port` defaults to `8000`, and `max_requests` remains optional. The annotated assignment is the server descriptor owner; its ordinary bound value is not server configuration and is not otherwise consumed by the lifecycle.
- `@cors policy` is valid only on the same assignment that owns `@server`. At most one `@cors` descriptor is allowed. Its closed map accepts only optional `origin`, `methods`, and `headers` fields and uses the exact validation, defaults, and response behavior of `cors(policy, handler)`.
- `@route descriptor` is valid only on a top-level named function. Its closed map has exactly `method` and `path` string fields. Both strings must be non-empty and `path` must start with `/`. The annotated binding must expose exactly one fixed one-argument callable arm; zero-argument, multi-argument, varargs, non-callable, or ambiguous bindings are invalid route handlers.
- Annotation names may occur at most once on one declaration. Repeating `@server`, `@cors`, or `@route` on the same target is an error rather than last-wins metadata. Annotated rebinding that would replace one of these descriptor keys is also an error. These rules do not change the existing merge behavior of other annotations.
~~~~~

## B180: baseline lines 3782-3795

Moved from GENIA_STATE.md@d401f322, lines 3782-3795 (ledger row B180, retained-condensed, sha256 46789050bc4642cb)

~~~~~markdown
- Serve discovery considers only declarations owned by the evaluated entry file. Imported modules may contain valid inert server annotation metadata, but their descriptors are not activated or merged into the entry file's server lifecycle.
- Discovery occurs after successful entry-file evaluation. Candidates are examined in source order, with declaration name as the deterministic tie-breaker. The one server descriptor is selected first, optional CORS second, and routes last. Route order passed to `route_request` is source order.
- Two routes conflict only when their normalized discovery keys are the exact pair `(method, path)`; R8 performs no method/path normalization. Every member of a conflicting pair is rejected, and diagnostics list occurrences in source order. Different methods on the same path are allowed.
- Descriptor failures are reported in this deterministic order: entry-file evaluation; `@server` cardinality/target/payload; `@cors` cardinality/target/payload; then each `@route` target/payload/arity in source order; then route conflicts in route source order. All descriptor diagnostics available from one completed discovery pass are returned together; listener activation does not occur when any diagnostic exists.
- The dedicated server lifecycle has three ordered phases and two scopes: `startup` in server scope, repeated `request` in request scope, and `shutdown` in server scope. It is one focused lifecycle consumer, not a generalized lifecycle runner or action registry.
- Startup validates/discovers descriptors, constructs exact route values from discovered handlers, passes them to `route_request`, optionally wraps the result once with `cors`, then activates the existing `serve_http` boundary with the server config. No parallel routing, CORS, header, or transport mechanism is permitted.
- Each accepted request enters one request scope. The handler produced by `route_request` receives the unchanged request map, selects one exact route, invokes that handler exactly once, and returns its response. When configured, the single application-wide `cors` wrapper owns preflight and response decoration. A request failure does not retry a handler.
- Server scope becomes entered before listener activation is attempted. Listener ownership begins only after activation returns an owned listener/server handle. Request scope becomes entered immediately before request routing and ends after a response or request failure. Shutdown is attempted exactly once for an owned listener after normal completion or any later primary failure; no cleanup is attempted for a listener that was never owned.
- Lifecycle state transitions are deterministic: `created -> starting -> serving -> stopping -> stopped` on success. A failure transitions from the current state to `stopping` when owned cleanup remains, then to `failed`; without owned cleanup it transitions directly to `failed`. Requests are accepted only in `serving`.
- The independently testable lifecycle core accepts validated/discovered descriptor data plus injected activate, request, and close operations. It does not parse CLI arguments or require a live socket. Final CLI integration may call this core; the core must not call CLI dispatch.
- The lifecycle core returns one deterministic result map with keys `status`, `state`, `phase`, `scope`, `server`, `primary_failure`, and `cleanup_failures`. `status` is `"ok"` or `"error"`; `state` is `"stopped"` or `"failed"`; `phase` is the terminal phase (`"shutdown"` on success or the phase owning the primary failure); `scope` is `"server"` or `"request"`; `server` is the existing `serve_http` result on success and `none` on error; `primary_failure` is `none` on success and otherwise the first failure; `cleanup_failures` is a source-ordered list and is empty on success.
- The first non-cleanup failure is always the primary failure. Cleanup never replaces or hides it. If no earlier failure exists, the first shutdown/close failure is primary and later cleanup failures remain in `cleanup_failures`. Startup failure skips request processing; request failure skips later requests; shutdown still gets its contracted opportunity for owned resources.
- Diagnostics and result failures must identify execution mode `serve`, phase, scope, reason, and source location when available. User-facing rendering may add context, but it must preserve the deterministic primary/cleanup distinction.

~~~~~

## B181: baseline lines 3796-3809

Moved from GENIA_STATE.md@d401f322, lines 3796-3809 (ledger row B181, retained-condensed, sha256 8ea1a9ed4274a57b)

~~~~~markdown
PYTHON REFERENCE HOST (IMPLEMENTED LIFECYCLE CORE):

- `src/genia/server_lifecycle.py` implements the dedicated, independently callable lifecycle core. `server_lifecycle_plan()` returns inert plan data for the exact `startup -> request -> shutdown` phases and `server` / `request` scopes; `validate_server_lifecycle()` validates that static descriptor through the existing lifecycle-plan normalizer without executing lifecycle work.
- `run_server_lifecycle(application, requests, activate=..., request=..., close=...)` is the only implemented #534 activation seam. It accepts already validated/discovered application data, a finite ordered request source, and injected Python operations, so it is callable without CLI parsing or live sockets.
- Successful activation establishes listener ownership; requests run in order without retry; request failure skips later requests; an owned listener receives exactly one close opportunity. Activation failure creates no ownership and performs no close. The first non-cleanup failure remains primary, and close failures are preserved in `cleanup_failures` without replacing it.
- The core returns the seven-key lifecycle result map defined above. Injected-operation exceptions are normalized to failure maps containing `mode`, `phase`, `scope`, `reason`, and `source_location` when the exception provides one.
- This is one fixed lifecycle consumer, not a lifecycle-plan runner: phase action identifiers remain inert and there is no action registry or resolver.
- Validated by `tests/unit/test_server_lifecycle.py` (9 tests), Python reference host only.

PYTHON REFERENCE HOST (IMPLEMENTED ROUTE ANNOTATION BINDING):

- The evaluator accepts `@route {method: ..., path: ...}` only on a top-level named function, validates the exact closed descriptor map, and stores it as inert `route` binding metadata. The parser, AST grammar, and Core IR are unchanged.
- Repeated `@route` on one declaration and annotated replacement of existing canonical `route` metadata fail deterministically. An initial `@meta` entry named `route` remains ordinary metadata and is not a canonical route candidate; existing merge behavior for other annotations remains unchanged.
- `src/genia/server_route_binding.py` discovers only annotated `IrFuncDef` declarations from the supplied evaluated entry-file IR list and environment. It preserves source order with declaration name as tie-breaker, requires exactly one fixed one-argument function arm, aggregates descriptor diagnostics before exact `(method, path)` conflict diagnostics, and rejects every conflict member.
~~~~~

## B182: baseline lines 3810-3823

Moved from GENIA_STATE.md@d401f322, lines 3810-3823 (ledger row B182, retained-condensed, sha256 8999386afdbad319)

~~~~~markdown
- A diagnostic-free result assembles existing generic R7 route values in source order and passes them once to the existing `route_request` operation through injected call boundaries. Discovery and assembly do not start a listener or execute a route handler.
- Validated by `tests/unit/test_server_route_binding.py` and focused annotation metadata tests. This is Experimental Python-reference-host internal support; there is no public route-discovery prelude API.

PYTHON REFERENCE HOST (IMPLEMENTED SERVER-CONFIG ANNOTATION BINDING):

- The evaluator accepts `@server {host: ..., port: ..., max_requests: ...}` only on a top-level assignment, validates and normalizes the closed descriptor, and stores it as inert `server` binding metadata. The parser, AST grammar, and Core IR are unchanged.
- Omitted `host` and `port` normalize to the existing `serve_http` defaults `"127.0.0.1"` and `8000`. `port` must be an integer in `[0, 65535]`; optional `max_requests` must be a positive integer when present, while explicit runtime absence is treated as omitted. Input maps are not mutated.
- Repeated `@server` on one declaration and annotated replacement of existing `server` metadata fail deterministically. An initial `@meta` entry named `server` remains ordinary metadata and is not a canonical server candidate; existing merge behavior for other annotations remains unchanged.
- `src/genia/server_config_binding.py` discovers only annotated `IrAssign` declarations from the supplied evaluated entry-file IR list and environment. It preserves source order with declaration name as tie-breaker, requires exactly one valid entry-file descriptor, ignores imported declarations, and returns deterministic descriptor/cardinality diagnostics without starting a listener.
- A diagnostic-free result passes the normalized configuration and unchanged handler once to an injected operation with the existing `serve_http(config, handler)` shape. Diagnostics prevent that operation from being called. This bind-down is independently testable and does not implement CLI dispatch or live lifecycle-to-HTTP composition.
- Validated by `tests/unit/test_server_config_binding.py`. This is Experimental Python-reference-host internal support; there is no public server-config discovery or binding prelude API.

PYTHON REFERENCE HOST (IMPLEMENTED CORS ANNOTATION BINDING):

~~~~~

## B183: baseline lines 3824-3838

Moved from GENIA_STATE.md@d401f322, lines 3824-3838 (ledger row B183, retained-condensed, sha256 9fe89409faa4ffb6)

~~~~~markdown
- The evaluator accepts `@cors {origin: ..., methods: ..., headers: ...}` only on a top-level assignment, validates the closed descriptor through the same policy validator used by R7 `cors`, and stores the original validated map as inert `cors` binding metadata. The parser, AST grammar, and Core IR are unchanged.
- Repeated `@cors` on one declaration and annotated replacement of existing `cors` metadata fail deterministically. An initial `@meta` entry named `cors` remains ordinary metadata and is not a canonical CORS candidate; existing merge behavior for other annotations remains unchanged.
- `src/genia/server_cors_binding.py` discovers only annotated `IrAssign` declarations from the supplied evaluated entry-file IR list and environment. It preserves source order with declaration name as tie-breaker, accepts descriptor absence, requires any descriptor to share the selected `@server` owner, ignores imported declarations, and returns deterministic payload/cardinality/ownership diagnostics without starting a listener.
- A diagnostic-free result with no CORS descriptor returns the unchanged assembled handler without calling a wrapper. One accepted descriptor passes its policy and the unchanged handler exactly once to an injected operation with the existing `cors(policy, handler)` shape. Diagnostics prevent that operation from being called. R7 `cors` and `with_headers` remain the sole owners of preflight and response-header behavior.
- The shared internal policy validator in `src/genia/cors_policy.py` preserves the existing R7 validation order, defaults, and messages; it prevents a duplicate annotation-specific policy contract.
- Validated by `tests/unit/test_server_cors_binding.py` plus existing R7 CORS tests. This is Experimental Python-reference-host internal support; there is no public CORS-discovery or server-binding prelude API.

PYTHON REFERENCE HOST (IMPLEMENTED CLI INTEGRATION):

- Python remains the only R8 server execution host because `serve_http`, `route_request`, `cors`, and `with_headers` are Python-reference-host capabilities.
- `genia serve <file>` accepts exactly one existing entry-file path, evaluates it once without `main` dispatch, performs entry-file descriptor discovery, and prevents activation when diagnostics exist.
- A valid application assembles source-ordered routes through `route_request`, applies optional application CORS once through `cors`, and activates `serve_http` through the dedicated lifecycle coordinator. Finite `max_requests` completion exits `0` without printing the lifecycle result; startup or lifecycle failure emits a Genia-facing `serve <phase>/<scope>` diagnostic and exits `1`.
- Missing files, extra operands, and conflicting serve command shapes are CLI usage errors and exit `2` before evaluation or activation.
- Future hosts may consume the host-independent inert descriptor and lifecycle-result shapes, but R8 adds no shared host-adapter capability and makes no multi-host server guarantee.

~~~~~

## B184: baseline lines 3839-3843

Moved from GENIA_STATE.md@d401f322, lines 3839-3843 (ledger row B184, retained-condensed, sha256 1016ef423e72fae9)

~~~~~markdown
Explicit limitations:

- `@route`, `@server`, and `@cors` metadata remain inert outside explicit `genia serve <file>` activation.
- No generalized lifecycle runner, middleware system, plugin system, dependency injection, path parameters, concurrent serving, streaming, WebSockets, authentication, authorization, credential policy, per-route CORS, graceful signal protocol, parser/Core IR change, or second web mechanism is defined.

~~~~~

## B283: baseline lines 6138-6152

Moved from GENIA_STATE.md@d401f322, lines 6138-6152 (ledger row B283, retained-condensed, sha256 5f4b4206579154ea)

~~~~~markdown
## 9.40) External direct process execution (`execution.process`)

Status: Implemented (Python reference host). Implements the approved
cross-cutting contract `execution.process(capability, request) ->
some(ProcessResult) | err(reason, context)`
(`docs/design/execution-process-contract.md`, PR #977) per the approved
implementation design (`docs/design/execution-process-design.md`, PR #978).
This capability has no release number (it specializes the existing
host-capability taxonomy and R14 ownership/finalization patterns rather
than opening a new numbered release) and is distinct from the unrelated,
already-implemented `process.*` logical process/mailbox family (`spawn`,
`send`, `process_alive?`): `execution.process` is external direct
executable execution; `process.*` is Genia's own in-process concurrency
primitive.

~~~~~

## B284: baseline lines 6153-6171

Moved from GENIA_STATE.md@d401f322, lines 6153-6171 (ledger row B284, retained-condensed, sha256 91c3edc75198916e)

~~~~~markdown
LANGUAGE CONTRACT:

- `import execution` then `execution.process(capability, request)` is an
  ordinary two-argument call. `capability` must be an opaque, host-created
  process-execution capability; pure Genia source cannot construct,
  compare, serialize, or meaningfully render one, and there is no ambient
  capability, global `host` object, or `host.supports(...)` operation —
  the capability must be supplied explicitly, exactly as R11's model
  provider or R14's outbound-HTTP transport already require.
- `request` is exactly the closed map `{executable: symbol, args: [string,
  ...], timeout_ms: integer}`. `executable` is a provider-bound symbolic
  identity (e.g. `quote(candidate_host)`), never an OS path, command
  string, or portable promise to search `PATH`. `args` elements become
  exact, separate child argv elements after `executable` — no shell is
  ever invoked, and no quoting, splitting, glob expansion, variable
  interpolation, or command substitution occurs at any layer. `timeout_ms`
  is a plain Integer in `1..300000`; a Python-style `bool` (or any other
  non-Integer numeric domain, including Decimal/Rational) is rejected as
  misuse, not silently accepted or coerced.
~~~~~

## B285: baseline lines 6172-6188

Moved from GENIA_STATE.md@d401f322, lines 6172-6188 (ledger row B285, retained-condensed, sha256 ea792d06aa63e81e)

~~~~~markdown
- A malformed capability, request shape, `executable`, `args`, `timeout_ms`,
  or any request value that recursively contains a protected leaf
  (reusing the existing R10 `contains_protected`/`reject_protected`
  machinery — no new taint mechanism) is runtime misuse, raised before any
  resolution or provider effect. V1 defines no process declassification
  sink and no authority argument: this differs from the R14 protected-HTTP-header
  sink model, where a matching authority does authorize revealing a
  protected value immediately before the one transport attempt.
- A completed child attempt is always `some({exit_code, stdout, stderr})`
  — including a nonzero `exit_code`. A program's nonzero exit status is
  the program's own ordinary result data, never an `execution.process`
  failure; nothing in this capability's normalization can turn a
  completed nonzero exit into `err(...)`. `stdout`/`stderr` are opaque
  `Bytes` values (never implicitly decoded to text, never line-ending
  normalized); each channel has an independent fixed maximum of exactly
  `1,048,576` bytes — a channel of exactly that size succeeds, one more
  byte is overflow.
~~~~~

## B286: baseline lines 6189-6207

Moved from GENIA_STATE.md@d401f322, lines 6189-6207 (ledger row B286, retained-condensed, sha256 a28343d9ffd6d2d9)

~~~~~markdown
- Recoverable failures are exactly the closed taxonomy:
  `err("process-executable-unavailable", {executable})` (unbound symbol),
  `err("process-unauthorized", {operation: quote(execute), executable})`
  (bound symbol, capability policy denies it),
  `err("process-launch-failure", {executable})` (resolution succeeded, the
  bound target could not be started),
  `err("process-timeout", {timeout_ms})` (the deadline elapsed; the owned
  child is terminated and reaped before this is returned),
  `err("process-output-limit", {limit_bytes: 1048576})` (either channel
  exceeded its independent bound; all partial output is discarded, never
  included), and `err("process-provider-failure", {operation:
  quote(execute)})` (any other host condition, including an unexpected
  exception from the capability's own launcher). No raw Python exception
  text, exception type name, errno description, native executable path,
  or process identifier ever crosses into a returned context, a
  diagnostic, or a rendered value. `process-unsupported` is reserved
  taxonomy this operation never emits itself — that reason belongs
  entirely to the deferred, not-yet-implemented capability-provisioning
  boundary (see Explicit limitations).
~~~~~

## B287: baseline lines 6208-6222

Moved from GENIA_STATE.md@d401f322, lines 6208-6222 (ledger row B287, retained-condensed, sha256 2eef63baf347e389)

~~~~~markdown
- Adds no syntax, no `IrProcess`/`IrSpawnExternal`/`IrHostCall`/shell-AST
  Core IR node, and no Flow/Seq change: `execution.process(...)` lowers
  through the existing ordinary-call/map/list/quote node families exactly
  like any other dotted module call.

PYTHON REFERENCE HOST:

- `src/genia/process_capability.py` (new): `GeniaProcessCapability` is an
  opaque `__slots__`-based value (symbol -> native-target bindings, an
  authorization predicate, and a launcher callable), mirroring
  `GeniaModelProvider`'s shape. The private factory
  `create_process_capability(bindings, authorized, launcher)` is
  consumed only by privileged host-side code — there is no Genia-callable
  constructor, matching R11's model-provider/R14's declassification-authority
  precedent of privileged-host-only minting.
~~~~~

## B288: baseline lines 6223-6239

Moved from GENIA_STATE.md@d401f322, lines 6223-6239 (ledger row B288, retained-condensed, sha256 ce81a53c08a65f73)

~~~~~markdown
- `src/genia/process_transport.py` (new): `launch_process(executable, args,
  timeout_ms, spawn_hook=None) -> ProcessTransportResult |
  ProcessTransportFailure` is the narrow launcher:
  `subprocess.Popen(argv, shell=False, ...)` with `stdin=DEVNULL`; two
  dedicated reader threads drain `stdout`/`stderr` concurrently, each
  incrementally counting bytes and stopping the instant the running total
  exceeds `1,048,576` (never buffering past that bound plus one read
  chunk); timeout uses a monotonic-clock deadline polled at a short fixed
  interval, never `subprocess.run(..., timeout=...)`'s own raised
  `TimeoutExpired`. Cleanup (`Popen.kill()`, which sends `SIGKILL` on
  POSIX — unblockable, so a child that installs a `SIGTERM` handler still
  dies) plus reap is unconditional and idempotent on every failure path
  (launch failure, timeout, either channel's overflow, or an unexpected
  host error), so no owned child survives the attempt. Nonzero exit
  becomes `ProcessTransportResult` unconditionally; `subprocess.run(...,
  check=True)`/`check_call`/`check_output` are not used anywhere in this
  module, by design.
~~~~~

## B289: baseline lines 6240-6253

Moved from GENIA_STATE.md@d401f322, lines 6240-6253 (ledger row B289, retained-condensed, sha256 7ec33a54fa4685b0)

~~~~~markdown
- `src/genia/process_execution.py` (new): `perform_process_execution(capability,
  request)` is the validation/normalization boundary — exact closed-request
  validation in field order (`executable`, `args`, `timeout_ms`), the
  existing `reject_protected(request, "execution.process")` call before
  any resolution or launch, symbol resolution against the capability
  (`is_bound`/`is_authorized`/`target_for`), and failure-taxonomy
  normalization. No native target string or raw exception ever appears in
  a value this function returns.
- `src/genia/std/prelude/execution.genia` (new): `process(capability,
  request) = _execution_process(capability, request)`, resolved through
  the existing packaged-prelude-module import mechanism (`import
  execution`) exactly like `import web`/`import resource` — no new
  module-loading mechanism. `src/genia/builtins.py` registers the private
  raw builtin `_execution_process`, mirroring `_http_send`.
~~~~~

## B290: baseline lines 6254-6273

Moved from GENIA_STATE.md@d401f322, lines 6254-6273 (ledger row B290, retained-condensed, sha256 c478cd3989d6723e)

~~~~~markdown
- Validated by 115 tests across 13 files under
  `tests/unit/test_execution_process_*.py`: exact capability/request
  misuse validation including boolean-as-`timeout_ms` rejection; recursive
  protected-value rejection with sentinel-non-leak proof; unavailable vs.
  unauthorized vs. launch-failure kept observably distinct; nonzero exit
  (`1`, `2`, `17`, `127`, `255`) always `some(ProcessResult)`, with an
  explicit guard against `subprocess.CalledProcessError`-style semantics;
  byte-exact capture including non-UTF-8 payloads; concurrent stdout/stderr
  draining sized past a 64 KiB OS pipe buffer so a naive sequential reader
  would deadlock; exact-at-limit and one-byte-over independent output
  bounds, plus an endless-writer fixture proving incremental (not
  buffer-then-check) enforcement; timeout against a fixture that ignores
  `SIGTERM`; PID-liveness-checked no-leaked-child proof across every
  terminal path; failure-context non-leak proof using recognizable
  sentinel strings; a real command-injection-style proof (a
  shell-significant argv element that would create a marker file if any
  shell ever evaluated it); and a Core IR regression confirming
  `execution.process(...)` lowers to the same node-family shape as any
  other dotted call.

~~~~~

## B291: baseline lines 6274-6303

Moved from GENIA_STATE.md@d401f322, lines 6274-6303 (ledger row B291, retained-condensed, sha256 2d5e8ecacffc004e)

~~~~~markdown
Explicit limitations (deferred, not implemented):

- No source-level capability provisioning/bootstrap API — the contract
  intentionally defers this; only privileged host-side Python code (a
  test harness, a future host bootstrap) can call
  `create_process_capability`. No file, command, pipe, import, REPL, test,
  or server mode provisions a usable capability implicitly.
- No protected argv/environment sink, no user-specified environment, no
  cwd, no child stdin beyond immediate EOF, no streaming output, no TTY,
  no signals/general cancellation, no process handles, no supervision, no
  retries, and no remote execution — all explicitly out of scope for this
  slice.
- **Portable contract, single-host implementation, no multi-host
  conformance evidence yet.** `execution.process` has a portable semantic
  contract that any future host must satisfy identically, and the Python
  reference host currently implements that contract — this does **not**
  mean another host currently implements it. `execution.process` is
  registered as `execution_process` in `spec/manifest.json`'s
  `optional_capabilities` (the Python host self-declares it `supported`,
  matching the existing `shell_stage`/`debugger_stdio`/`process_primitives`
  name-only-registration precedent), but no shared-spec case declares
  `requires: [execution_process]` yet, because no host-neutral fixture/
  provisioning mechanism exists to let a portable case inject a capability
  into the sandboxed `eval` category — so that `supported` self-declaration
  is not yet exercised or falsified by any actual conformance test. Runtime
  implementation and R16 capability *advertisement* are not conformance
  *evidence*; a natural future consumer of the missing fixture mechanism is
  R37 Genia-native conformance tooling, which the roadmap already names as
  a concrete future consumer of this primitive — see
  `docs/host-interop/capabilities.md`.
~~~~~

## B292: baseline lines 6304-6307

Moved from GENIA_STATE.md@d401f322, lines 6304-6307 (ledger row B292, retained-condensed, sha256 43cfb7f97576323d)

~~~~~markdown
- No new Core IR, R35 portable storage/location semantics, or R36
  location-independent execution behavior is implemented or implied by
  this capability.

~~~~~
