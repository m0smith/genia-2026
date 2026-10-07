# R14 lifecycle and outbound HTTP record

> **Non-authoritative provenance record.** This file preserves, verbatim and unedited, text that was displaced
> from `GENIA_STATE.md` during the #1099 distillation. It is audit material, not part of the truth hierarchy:
> it does not define Genia behavior, and `GENIA_STATE.md` governs. Start with the release, design, and reference
> documents; open this file only to see the exact displaced wording.
>
> Baseline: `GENIA_STATE.md` at `d401f322c692e8c3620509854065692c2605c61a`. Scope: Sections 9.8-9.20, ticket by ticket.
> Ledger: `docs/analysis/state-distillation-migration-map.json`.

## B185: baseline lines 3844-3876

Moved from GENIA_STATE.md@d401f322, lines 3844-3876 (ledger row B185, moved, sha256 fd895fd02314b6cc)

~~~~~markdown
## 9.8) R14 E14-1 lifecycle instance and parent/child execution scopes

Status: Implemented. The vertical-composition instance/scope core (issue #621) is implemented as Experimental, portable, Python-reference-host-only behavior. It is the first implemented slice of the approved R14 contract (`docs/design/r14-composable-lifecycle-contract.md`, approved by issue #620). Horizontal peer-attachment breadth is proven by issue #692 over this same core — see section 9.9. `lifecycle_repeat`/element scopes are implemented by issue #693 — see section 9.10. Provider binding is implemented by issue #694 — see section 9.11. HTTP remains #622-#628 — not implemented yet.

LANGUAGE CONTRACT:

- Three ordinary functions are implemented: `lifecycle_scope(peers, work)`, `lifecycle_child(scope_handle, peers, work)`, and `lifecycle_context(scope_handle, name)`. `lifecycle_repeat`, `lifecycle_config`, and `web.http_send` are not implemented by this issue.
- A peer (`LifecycleDefinition`) is an ordinary closed map `{name: symbol, enter: callable/1, exit: callable/2}`. Any other shape, a non-symbol or empty-string `name`, or a duplicate name within one peer list is construction-time misuse (`TypeError`) raised before any `enter` call.
- `enter(scope_handle)` must return `some(context_value)` or `err(reason, context)`; any other return is misuse. A successful `enter` makes its peer "entered" and exposes `context_value` through `lifecycle_context` under that peer's name, readable by later peers in the same list and by `work`, but never by an earlier peer in the same list.
- Peers on one scope operation enter in list (attachment) order and unwind (`exit`) in strict reverse order. `exit(scope_handle, primary_summary)` receives only the narrow `{status: quote(ok)|quote(error), phase, peer}` summary — never another peer's context or resources — and must return `some("nil")` or `err(reason, context)`.
- `work(scope_handle)` runs only if every peer entered. Its return value is carried into the result's `result` field verbatim and is never inspected for `some`/`none`/`err`; the only way `work` produces a lifecycle failure is by raising, normalized the same way R8 normalizes lifecycle exceptions (`reason` from `str(exception)`, non-sensitive empty `context`).
- Every scope operation returns exactly one closed `LifecycleResult`: `{status: quote(ok)|quote(error), state: quote(completed)|quote(failed), scope: quote(root)|quote(child), phase: quote(enter)|quote(work)|quote(exit), peer: some(symbol)|none("lifecycle-no-peer"), result: some(value)|none("lifecycle-no-result"), primary_failure: none("lifecycle-no-failure")|failure_value, cleanup_failures: [failure_value, ...]}`, where `failure_value` is `{peer, phase, reason: string, context: map}`.
- Exactly one failure is primary per `LifecycleResult`: the first entry, work, or unwind failure encountered. The first exit failure encountered with no primary failure yet is promoted to `primary_failure`; every later exit failure in the same unwind is appended to `cleanup_failures` in exit-call order. Every entered peer's `exit` is attempted exactly once regardless of earlier exit failures.
- `result` carries `work`'s return value whenever `work` executed without raising, independent of any later exit failure; it is `none("lifecycle-no-result")` only when `work` never ran (an entry failure) or `work` raised.
- Scope lifetime is `created -> entering -> active -> exiting -> completed` on success, `created -> entering -> failed` when the very first peer's `enter` fails (nothing yet entered, so no unwind), `created -> entering -> exiting -> failed` when a later peer's `enter` fails (unwinds only the already-entered peers), and `created -> entering -> active -> exiting -> failed` on a work or exit failure.
- A scope handle is valid only while its scope is `entering`/`active`/`exiting`. Any later use by `lifecycle_context` or `lifecycle_child` raises `RuntimeError("lifecycle-scope-expired")` — the same single-valid-lifetime family as an already-consumed Flow. This is the entire cancellation/shutdown surface: there is no external cancel/abort/signal API.
- `lifecycle_child(scope_handle, peers, work)` runs a new scope as a plain nested function call from inside the parent's own `work`; it requires the parent handle to be `active` (not merely alive) and raises a distinct `RuntimeError` (not the scope-expired identifier) otherwise, since a handle mid-`entering`/`exiting` is alive but in the wrong phase for child creation. A child's `LifecycleResult` is ordinary data returned to the parent's `work` — it is never implicitly raised into the parent, so a failed child never implicitly fails the parent. A child's peers/resources are entirely separate from the parent's; child entry and unwind complete synchronously inside the one `lifecycle_child` call, so a child can never outlive it, and a parent's own resources are untouched by a child's unwind.
- `lifecycle_context(scope_handle, name)` is inward-only and read-only: it checks the calling scope's own entered-peer context first, then walks each ancestor scope up to the root, returning the first match as `some(value)` or `none("lifecycle-context-absent")` if none expose that name. There is no write accessor and no way to mutate an ancestor's or peer's exposed context through this call.
- Non-shadowing is enforced at peer-list construction, before any `enter` runs: a peer name colliding with any name already exposed by an ancestor scope in the same chain is `TypeError` misuse. (This is the same mechanism later reserved names such as `quote(config)`/`quote(element)`/`quote(index)` will reuse in #693/#694; no reserved names exist yet in this issue.)
- No global mutable "current lifecycle" or "current scope" exists anywhere in this surface. No annotation, parser, AST, or Core IR change was made; every operation is an ordinary call over ordinary closed map/callable values, registered exactly like `config_view`/`secret_view`.

PYTHON REFERENCE HOST:

- `src/genia/lifecycle_runtime.py` implements the algorithm above. `GeniaLifecycleScope` is an internal, non-source-constructible handle (`kind`, `parent`, `lifetime`, `context`); it is never a public value category and is only ever the argument passed into one scope operation's own `enter`/`exit`/`work` callables.
- `run_lifecycle_scope(peers, work, invoke)`, `run_lifecycle_child(parent_handle, peers, work, invoke)`, and `lookup_lifecycle_context(handle, name)` take an injected `invoke: Callable[[Any, list], Any]` for calling caller-supplied Genia callables, mirroring `server_lifecycle.run_server_lifecycle`'s injected-operation style; `src/genia/builtins.py` wires this to the existing `_invoke_raw_from_builtin` evaluator path (the same one already used for `where`/`derive`/`config_get_or`'s default).
- Registered as `lifecycle_scope`/`lifecycle_child`/`lifecycle_context` in `src/genia/builtins.py`; documented in `src/genia/host_builtin_docs.py`.
- Validated by `tests/unit/test_lifecycle_runtime.py` (24 tests) exercising the module directly with a trivial injected invoker, Python reference host only. No host capability is introduced; shared/multi-host conformance remains Partial.

Explicit limitations:

- No `lifecycle_repeat`, `lifecycle_config`, HTTP operation/client, element scopes, reserved element/index/config context names, or provider binding is implemented. Peer-attachment breadth (multiple `LifecycleDefinition`s on one scope) is now proven at three-or-more peers by issue #692 — see section 9.9.
- No generalized lifecycle-plan/action-identifier runner, dependency injection, scheduler, actor supervision, or concurrent peer/child execution is defined.

~~~~~

## B186: baseline lines 3877-3900

Moved from GENIA_STATE.md@d401f322, lines 3877-3900 (ledger row B186, moved, sha256 e493122aa1f08049)

~~~~~markdown
## 9.9) R14 E14-2 peer lifecycle attachment and deterministic unwind

Status: Proven. Issue #692 adds no new public function, value shape, or runtime behavior. It extends `tests/unit/test_lifecycle_runtime.py` with nine focused tests proving the E14-1 entry/work/unwind algorithm (section 9.8, `src/genia/lifecycle_runtime.py`) at three-or-more-peer breadth, exactly matching the horizontal-composition contract approved by issue #620 (`docs/design/r14-composable-lifecycle-contract.md`). `src/genia/lifecycle_runtime.py`, `src/genia/builtins.py`, and `src/genia/host_builtin_docs.py` are unchanged from E14-1: `_run_scope`'s enter/work/unwind loops already iterate a plain Python list of arbitrary length with no hardcoded peer count.

LANGUAGE CONTRACT (already true of `lifecycle_scope`/`lifecycle_child` as documented in section 9.8; this section records what #692 additionally proves at breadth):

- The peer list is not limited to one or two entries: any number of `LifecycleDefinition` peers enter in list order and unwind, in strict reverse, only the peers that actually entered.
- Entry failure at any position in a longer peer list unwinds exactly the already-entered prefix in reverse, and never attempts a peer positioned after the one that failed.
- Exactly one `primary_failure` is recorded across an arbitrarily long unwind: the first exit failure encountered in reverse-call order is promoted, every later exit failure (including one that occurs after a peer whose own exit succeeded) is appended to `cleanup_failures` in exit-call order, and every entered peer's `exit` still runs exactly once.
- Context visibility stays inward/later-only at any peer-list length: a peer's exposed context is invisible to every earlier peer in the same list and visible to every later peer and to `work`.
- `exit`'s `primary_summary` argument carries only `{status, phase, peer}` for every peer regardless of list length — no peer's `exit` callable ever receives another peer's exposed context or resources.
- A peer that reads another peer's exposed context and derives a locally modified value (via `GeniaMap.put`, which is persistent and returns a new map rather than mutating in place) cannot cause that derived value to appear under the original peer's own name — peer isolation holds structurally, not merely by the absence of a write API.
- Attachment order and parent/child ownership remain independent relationships at any peer-list length: a multi-peer child scope's own attachment/unwind order is unaffected by how many ancestor scopes or ancestor peers exist above it.

PYTHON REFERENCE HOST:

- No change to `src/genia/lifecycle_runtime.py`, `src/genia/builtins.py`, or `src/genia/host_builtin_docs.py`.
- Validated by nine additional tests in `tests/unit/test_lifecycle_runtime.py` (34 tests total in that file, at the time of E14-2; 43 after E14-3's own additions — see section 9.10), Python reference host only. No host capability is introduced; shared/multi-host conformance remains Partial.

Explicit limitations:

- No HTTP operation/client is implemented (see issues #622-#628). `lifecycle_repeat` and element scopes are implemented by issue #693 — see section 9.10. `lifecycle_config`/provider binding is implemented by issue #694 — see section 9.11.
- No generalized lifecycle-plan/action-identifier runner, dependency injection, scheduler, actor supervision, or concurrent peer/child execution is defined.

~~~~~

## B187: baseline lines 3901-3916

Moved from GENIA_STATE.md@d401f322, lines 3901-3916 (ledger row B187, moved, sha256 b3a35b858501824b)

~~~~~markdown
## 9.10) R14 E14-3 repeated element-scoped lifecycle execution

Status: Implemented. Issue #693 adds one new ordinary function,
`lifecycle_repeat(peers, source, element_work)`, composing the unchanged
E14-1/E14-2 entry/work/unwind algorithm (sections 9.8-9.9) with the
existing Flow/Seq lazy-pull/finalization machinery, per the approved R14
contract's "Repeated element-scoped execution" section
(`docs/design/r14-composable-lifecycle-contract.md`).

LANGUAGE CONTRACT:

- `lifecycle_repeat(peers, source, element_work)` accepts `source` as
  either an ordinary `list` (eager) or a `Flow` (lazy), and returns
  `[LifecycleResult, ...]` or `Flow<LifecycleResult>` respectively; any
  other `source` shape raises the existing "expected a Seq-compatible
  value (list or Flow)" `TypeError` before any element scope is touched.
~~~~~

## B188: baseline lines 3917-3931

Moved from GENIA_STATE.md@d401f322, lines 3917-3931 (ledger row B188, moved, sha256 3d75a19bcb08ee92)

~~~~~markdown
- Each consumed element gets one fresh **element scope**
  (`scope: quote(element)`) running the exact same entry/work/unwind
  algorithm as `lifecycle_scope`/`lifecycle_child`, with no R14 parent —
  `lifecycle_repeat` itself has no lifecycle scope of its own.
- Two reserved context names are populated in every element scope before
  any attached peer's own `enter` runs, readable through the existing
  `lifecycle_context(scope_handle, name)` accessor by any peer or by
  `element_work`: `quote(element)` (the consumed element value) and
  `quote(index)` (its 1-based ordinal among elements actually pulled from
  `source` so far — the pull order, not source position).
- A peer literally named `element` or `index` is construction-time misuse,
  rejected with a `TypeError` before any `enter` runs — the same
  non-shadowing mechanism `lifecycle_scope`/`lifecycle_child` already use
  for ancestor context, now also checking a scope's own pre-seeded
  reserved context.
~~~~~

## B189: baseline lines 3932-3948

Moved from GENIA_STATE.md@d401f322, lines 3932-3948 (ledger row B189, moved, sha256 c50d7aee8c4487a7)

~~~~~markdown
- **Eager (`list`) source:** every element is processed, in order,
  regardless of any individual element's `LifecycleResult` status —
  `lifecycle_repeat` never short-circuits a `list` source, exactly like
  `map` processing every item.
- **Lazy (`Flow`) source:** `lifecycle_repeat` over a `Flow` returns a
  lazy, single-use `Flow<LifecycleResult>` and performs no work until
  pulled. Pulling one item from the returned Flow pulls exactly one item
  from `source` (no over-pull, no read-ahead), runs that element's
  complete entry/work/unwind algorithm synchronously, and yields its
  `LifecycleResult`. Because each element scope is fully entered and
  unwound *before* its result is yielded, bounded early termination
  (`take`, a manual break, downstream short-circuit) never leaves an
  element scope partially entered — the most recently yielded element's
  cleanup already ran. Early-close cleanup is exactly the existing Flow
  `close_on_early_termination` + upstream-`close()` finalization rule
  already used by `map`/`filter`/`take`; no new finalization mechanism is
  introduced.
~~~~~

## B190: baseline lines 3949-3962

Moved from GENIA_STATE.md@d401f322, lines 3949-3962 (ledger row B190, moved, sha256 65afc7a564a51012)

~~~~~markdown
- `element_work` returning `none(...)`/`err(...)` as ordinary data is not
  treated specially: per the general work-return rule (section 9.8), it is
  exactly `result: some(none(...))`/`result: some(err(...))` on an
  otherwise `completed` `LifecycleResult`. There is no dedicated filtering
  primitive.
- An element scope's handle becomes invalid (raising the existing
  `RuntimeError("lifecycle-scope-expired")` on later `lifecycle_context`/
  `lifecycle_child` use) the instant its own `LifecycleResult` is produced
  — the same single-valid-lifetime mechanism sections 9.8-9.9 already
  document, with no new expiry concept.
- Any scope `element_work` creates via `lifecycle_child` is a shorter
  nested lifetime under that element scope, exactly like existing vertical
  composition — this required no change, since `lifecycle_child` only
  checks that its parent handle's scope is `active`, not its `kind`.
~~~~~

## B191: baseline lines 3963-3981

Moved from GENIA_STATE.md@d401f322, lines 3963-3981 (ledger row B191, moved, sha256 017ec5427d5ad276)

~~~~~markdown
- No cross-element context leakage: each element scope is an independent
  `_run_scope` call with no parent, so nothing exposed in one element's
  scope is ever visible from another element's scope.

PYTHON REFERENCE HOST:

- `src/genia/lifecycle_runtime.py`: `run_lifecycle_element(peers, element,
  index, work, invoke)` runs one element scope via the existing `_run_scope`,
  now taking an optional `preset_context` keyword that seeds `scope.context`
  before peer validation/entry (used only by this function; root/child
  scopes never pass it, so their behavior is unchanged — confirmed by the
  existing 34 E14-1/E14-2 tests staying green). This module still has zero
  `list`/`Flow`/iteration knowledge.
- `src/genia/builtins.py`: `lifecycle_repeat_fn` dispatches `isinstance(source,
  list)` (eager, a plain list comprehension over `enumerate(source, start=1)`)
  vs. `isinstance(source, GeniaFlow)` (lazy, a generator wrapped in
  `GeniaFlow`, reusing the exact `try/finally` + `_finalize_iterable(items,
  primary_error=...)` idiom already used by `map`/`filter`/`take`).
  Registered as `lifecycle_repeat`, documented in `host_builtin_docs.py`.
~~~~~

## B192: baseline lines 3982-3995

Moved from GENIA_STATE.md@d401f322, lines 3982-3995 (ledger row B192, moved, sha256 1e7b82bc47feecf1)

~~~~~markdown
- Validated by 9 additional tests in `tests/unit/test_lifecycle_runtime.py`
  (43 tests total in that file, Flow-free, exercising
  `run_lifecycle_element` directly) and 15 tests in the new
  `tests/unit/test_lifecycle_repeat.py` (through real Genia source via
  `run_source`, covering eager/lazy dispatch, no-over-pull, close-once-on-
  early-stop, and deterministic two-peer-per-element ordering for both
  source kinds), Python reference host only. No host capability is
  introduced; shared/multi-host conformance remains Partial.

Explicit limitations:

- No HTTP operation/client is implemented (see issues #622-#628).
  `lifecycle_config`/provider binding is implemented by issue #694 — see
  section 9.11.
~~~~~

## B193: baseline lines 3996-4004

Moved from GENIA_STATE.md@d401f322, lines 3996-4004 (ledger row B193, moved, sha256 fe9703ff6c92a7f3)

~~~~~markdown
- No AWK syntax, `$0`/`$1`/`NR`/`NF` binding, or record-shape derivation —
  `quote(element)`/`quote(index)` are read through the ordinary
  `lifecycle_context` accessor only; a future record-oriented lifecycle
  derives `record`/`fields`/`nr`/`nf` as ordinary values from these, not as
  new syntax (see issue #695).
- No generalized lifecycle-plan/action-identifier runner, dependency
  injection, scheduler, actor supervision, or concurrent element
  processing is defined.

~~~~~

## B194: baseline lines 4005-4024

Moved from GENIA_STATE.md@d401f322, lines 4005-4024 (ledger row B194, moved, sha256 9a22734d4499bae2)

~~~~~markdown
## 9.11) R14 E14-4 lifecycle-owned configuration provider binding

Status: Implemented. Issue #694 adds one new ordinary function,
`lifecycle_config(provider) -> LifecycleDefinition`, a pure factory
composing the *unmodified* E14-1/E14-2/E14-3 peer machinery (sections
9.8-9.10) with the existing R10/R13 `GeniaConfigProvider` type, per the
approved R14 contract's "Lifecycle-owned configuration binding" section
(`docs/design/r14-composable-lifecycle-contract.md`). This promotes
candidate C-1 from `docs/parking-lot/post-r13-configuration-followups.md`
(the R13 lifecycle/provider-binding gap deliberately deferred at the time).

LANGUAGE CONTRACT:

- `lifecycle_config(provider)` validates that `provider` is an existing,
  already-constructed `GeniaConfigProvider` value — the unwrapped result
  of a successful `config_provider`/`config_standard` call — and returns
  exactly one closed peer map `{name: quote(config), enter: callable/1,
  exit: callable/2}`. Any other argument shape (a plain map, a string,
  `none`, an un-unwrapped `some(provider)`, an `err(...)`) raises
  `TypeError` before any scope/peer machinery runs.
~~~~~

## B195: baseline lines 4025-4038

Moved from GENIA_STATE.md@d401f322, lines 4025-4038 (ledger row B195, moved, sha256 7a73a6a4c7ac9629)

~~~~~markdown
- `enter(scope_handle)` always returns `some(provider)`: it captures the
  exact provider reference and performs no lookup, no source acquisition,
  no host capability call, and no provider refresh — binding is
  attachment, not acquisition.
- `exit(scope_handle, primary_summary)` always returns `some("nil")`:
  there is nothing to release.
- The bound provider is read, inward-only, by any peer or `work`/
  `element_work` in the same scope or any descendant scope, through the
  unchanged `lifecycle_context(handle, quote(config))` accessor — no new
  accessor is introduced. The value returned is the exact provider object
  (not a copy), so `config_view`/`secret_view` construction,
  `config_get`/`secret_get`, existing Outcomes, protected carriers, sinks,
  authority, and declassification behave exactly as an explicitly
  hand-threaded provider would.
~~~~~

## B196: baseline lines 4039-4052

Moved from GENIA_STATE.md@d401f322, lines 4039-4052 (ledger row B196, moved, sha256 e84c92e702525508)

~~~~~markdown
- `quote(config)` is a reserved, non-shadowable peer name: at most one
  `lifecycle_config` peer may exist anywhere in one root/child/element
  ancestry chain. A second attempt anywhere in that chain is
  construction-time misuse. This is enforced entirely by the *already-
  implemented, unmodified* `_validate_peers` duplicate-peer-name-in-one-list
  check and ancestor-non-shadowing check (sections 9.8-9.9) — because
  `lifecycle_config` always hardcodes `name: quote(config)`, no new
  reserved-name mechanism was needed. Sibling scope trees (not
  ancestor-related) may each bind their own provider independently.
  Element scopes have no R14 parent (section 9.10), so a provider bound at
  an outer scope is not automatically inherited into `lifecycle_repeat`'s
  per-element scopes; an application wanting every element to see a
  provider attaches `lifecycle_config(provider)` inside the same `peers`
  list passed to `lifecycle_repeat`.
~~~~~

## B197: baseline lines 4053-4068

Moved from GENIA_STATE.md@d401f322, lines 4053-4068 (ledger row B197, moved, sha256 612a02878a6470e0)

~~~~~markdown
- A missing binding (`lifecycle_context` on `quote(config)` with no
  `lifecycle_config` peer anywhere in the chain) returns the existing
  generic `none("lifecycle-context-absent")` — no new failure reason.
- No bare configuration name, ambient lookup, or `server.PORT`-style named
  access is introduced. This is R14's entire configuration surface: one
  explicit, immutable, non-refreshable binding — not dependency injection,
  not a service container, and not a second provider implementation.

PYTHON REFERENCE HOST:

- `src/genia/builtins.py`: `lifecycle_config_fn` validates
  `isinstance(provider, GeniaConfigProvider)` and constructs the peer map
  with trivial Python-closure `enter`/`exit` (no genia source involved in
  their construction). Registered as `lifecycle_config`, documented in
  `host_builtin_docs.py`. **No change to `src/genia/lifecycle_runtime.py`
  or `src/genia/configuration.py`.**
~~~~~

## B198: baseline lines 4069-4082

Moved from GENIA_STATE.md@d401f322, lines 4069-4082 (ledger row B198, moved, sha256 28f29750cfab58d0)

~~~~~markdown
- Validated by 9 additional tests in `tests/unit/test_lifecycle_runtime.py`
  (53 tests total in that file — peer shape, non-provider rejection, exact-
  object context identity, grandchild visibility, duplicate/shadowing
  rejection in both a shared list and across parent/child, sibling
  scope-tree independence, element-scope binding, missing-binding absence,
  and N-peer composition, all via the trivial injected invoker) and 4 tests
  in the new `tests/unit/test_lifecycle_config.py` (through real Genia
  source via `run_source`: `config_view`/`secret_view` parity with a
  hand-threaded provider, protected-secret redaction under `display`/
  `debug_repr`, an end-to-end bind-then-read-from-child-scope proof, and
  rejection of an unwrapped `some(provider)` argument), Python reference
  host only. No host capability is introduced; shared/multi-host
  conformance remains Partial.

~~~~~

## B199: baseline lines 4083-4093

Moved from GENIA_STATE.md@d401f322, lines 4083-4093 (ledger row B199, moved, sha256 ba155da15e11e190)

~~~~~markdown
Explicit limitations:

- No HTTP client/transport is implemented (see issues #623-#628). The
  common `HttpOperation` representation is implemented by issue #622 —
  see section 9.12.
- No provider refresh, mutation, service container, or dependency-injection
  framework is defined — `lifecycle_config` is one explicit, immutable
  binding, nothing more.
- No change to `config_view`, `secret_view`, `config_standard`,
  `config_provider`, or any R10/R13 lookup/protection semantic.

~~~~~

## B200: baseline lines 4094-4110

Moved from GENIA_STATE.md@d401f322, lines 4094-4110 (ledger row B200, moved, sha256 cd14fc872e322329)

~~~~~markdown
## 9.12) R14 E14-5 common HTTP operation representation

Status: Implemented. Issue #622 adds one new ordinary function,
`http_operation(method, base_url, path, headers, query, body) ->
some(HttpOperation) | err("http-operation-invalid", {stage})`, per the
approved R14 contract's "HTTP operation representation" section
(`docs/design/r14-composable-lifecycle-contract.md`). Construction
performs **zero network IO** of any kind — this is the first R14-HTTP
ticket, and it adds no host capability at all (that arrives in #623).

LANGUAGE CONTRACT:

- `method`, `base_url`, `path`, `headers`, `query`, and `body` are
  validated in that declared order; the first invalid field stops
  validation immediately and produces
  `err("http-operation-invalid", {stage: quote(<field>)})` — no partial or
  multi-error result is ever returned.
~~~~~

## B201: baseline lines 4111-4126

Moved from GENIA_STATE.md@d401f322, lines 4111-4126 (ledger row B201, moved, sha256 f39fe90f4b063fc1)

~~~~~markdown
- `method` must be exactly one of `quote(get)`, `quote(post)`,
  `quote(put)`, `quote(patch)`, or `quote(delete)`. `HEAD`, `OPTIONS`,
  `CONNECT`, and `TRACE` are not in the approved R14 method set.
- `base_url` must match `scheme://host[:port]` exactly, `scheme` in
  `{http, https}`, `host` one-or-more ASCII letters/digits/`-`/`.`, `port`
  (if present) one-or-more ASCII digits; any userinfo, path, query, or
  fragment, or an unsupported scheme, is invalid.
- `path` must start with `/` and must not contain `?` or `#`. Path bytes
  pass through exactly as supplied — no percent-encoding, normalization,
  or trailing-slash handling.
- `headers` keys are normalized to lowercase ASCII; two entries whose
  lowercased names collide is construction-time misuse (not last-wins). A
  header value is a plain string or exactly one R10 `GeniaProtected`
  value — any other shape is invalid. (Purpose restriction to
  `quote(http_send)` is #625's declassification-time concern, not
  construction.)
~~~~~

## B202: baseline lines 4127-4140

Moved from GENIA_STATE.md@d401f322, lines 4127-4140 (ledger row B202, moved, sha256 b06119fb4c7e793a)

~~~~~markdown
- `query` accepts plain string keys and values only — a `GeniaProtected`
  value in `query` is rejected at construction; a credential must be
  carried in `headers`. Query keys are **not** lowercased.
- `body` is `none(...)` (any reason; normalized to
  `none("http-no-body")` in the result), `{kind: quote(text), text:
  string}`, or `{kind: quote(json), value}`. A `json`-kind body's `value`
  is passed through the existing `json_encode` capability purely to fail
  fast — a `json_encode` failure (including a protected leaf inside
  `value`, which `json_encode` already rejects) surfaces as this
  function's own `err(..., {stage: quote(body)})`, before any later
  ticket's child scope or transport exists. The constructed `body` field
  keeps its original `{kind, text|value}` descriptor shape — `http_operation`
  does not store pre-encoded bytes; actual wire encoding is `web.http_send`'s
  job (#624).
~~~~~

## B203: baseline lines 4141-4155

Moved from GENIA_STATE.md@d401f322, lines 4141-4155 (ledger row B203, moved, sha256 55d7f89d9bf4301e)

~~~~~markdown
- An implicit `content-type` header (`text/plain; charset=utf-8` for
  `text`, `application/json` for `json`) is added to the result's
  `headers` only when `body` validates successfully and `headers` does
  not already set `content-type` (case-insensitively) — an explicit
  caller-supplied header always wins; R14 never silently discards it.
  A `none` body adds no implicit content-type.
- The constructed `HttpOperation` is an ordinary closed `GeniaMap` with
  keys `method, base_url, path, headers, query, body` — no new value
  class. It composes with `display`, diagnostics, and any container
  operation exactly like any other map holding a possibly-protected leaf,
  per R10's existing recursive sink-scan rules — no special-casing was
  needed. `HttpOperation` carries no `response` field.

PYTHON REFERENCE HOST:

~~~~~

## B204: baseline lines 4156-4170

Moved from GENIA_STATE.md@d401f322, lines 4156-4170 (ledger row B204, moved, sha256 bf4001ce4addf88a)

~~~~~markdown
- `src/genia/http_operation.py` (new): `construct_http_operation(method,
  base_url, path, headers, query, body, json_encode)` implements the
  algorithm above. `json_encode` is an injected dependency (the same
  style `run_lifecycle_scope` already uses for `invoke`), so this module
  has no closure dependency on `builtins.py` and no `list`/`Flow`/
  lifecycle knowledge.
- `src/genia/builtins.py`: `http_operation_fn` delegates to
  `construct_http_operation(..., json_encode_fn)`. Registered as
  `http_operation`, documented in `host_builtin_docs.py` under a new
  "HTTP" category. Set `__genia_handles_none__ = True` (the same opt-out
  `json_encode`/`json_decode`/`display` already use) so that passing
  `none(...)` as the `body` argument reaches the function body instead of
  short-circuiting the whole call via Genia's general none-propagation
  convention — required precisely because the contract's own `body`
  shape includes `none("http-no-body")`.
~~~~~

## B205: baseline lines 4171-4186

Moved from GENIA_STATE.md@d401f322, lines 4171-4186 (ledger row B205, moved, sha256 f4adb4b15a71c8b5)

~~~~~markdown
- Validated by 55 tests in the new `tests/unit/test_http_operation.py`:
  every method; every `base_url`/`path` validation rule; header
  lowercasing/collision/protected-value handling; query shape and
  protected-value rejection; every `body` shape and implicit-vs-explicit
  content-type precedence; a `json`-body-with-protected-leaf rejection;
  declared-order first-failure determinism; and one R10 redaction
  regression proof (a protected header built from a real `secret_get`
  call never appears in `display`/`debug_repr` output), Python reference
  host only. No host capability is introduced; shared/multi-host
  conformance remains Partial.

Explicit limitations:

- No host transport, outbound client lifecycle, protected HTTP credential
  sink purpose, or declarative HTTP annotations are implemented (see
  issues #623-#628).
~~~~~

## B206: baseline lines 4187-4193

Moved from GENIA_STATE.md@d401f322, lines 4187-4193 (ledger row B206, moved, sha256 bb06207d3e5632d1)

~~~~~markdown
- No percent-encoding or URL serialization of `query` is performed by
  `http_operation` itself — the query percent-encoding table is portable
  contract text for `web.http_send` (#624) to obey when it builds the
  real URL.
- No new schema/Template/validation framework — reuses existing Outcome,
  `GeniaMap`, `GeniaProtected`, and `json_encode` conventions verbatim.

~~~~~

## B207: baseline lines 4194-4263

Moved from GENIA_STATE.md@d401f322, lines 4194-4263 (ledger row B207, moved, sha256 c2594d83dde21800)

~~~~~markdown
## 9.13) R14 E14-6 outbound HTTP transport capability

Status: Implemented. Issue #623 adds one narrow Python-host outbound HTTP
transport capability per the approved R14 contract's "Portability
boundary" section (`docs/design/r14-composable-lifecycle-contract.md`).
This ticket adds **no Genia-visible surface**: the capability is not a
builtin, has no `import` entry, and is consumed privately by a later
ticket (`web.http_send`, E14-7, #624), exactly like
`create_gemini_rest_model_provider`/`_default_transport` in
`src/genia/gemini_rest.py` have no `builtins.py` registration of their
own. This section therefore has no LANGUAGE CONTRACT block.

PYTHON REFERENCE HOST:

- `src/genia/http_transport.py` (new): `send_http_request(request,
  transport=None) -> HttpTransportResponse | HttpTransportFailure` makes
  exactly one synchronous transport attempt via an injectable
  `HttpTransport = Callable[[HttpTransportRequest], HttpTransportResponse]`,
  defaulting to `_default_transport` (a `urllib.request`-based opener
  built with a no-redirect handler, mirroring `gemini_rest.py`'s own
  `_NoRedirect`/`_default_transport` pattern but generic over method/URL
  instead of one fixed Gemini endpoint).
- `HttpTransportRequest` is a private frozen dataclass:
  `method, url, headers, body: bytes, timeout_seconds`. `HttpTransportResponse`
  is `status, headers, body: bytes`. `HttpTransportFailure` is a single
  closed field `kind: str`, one of `timeout`, `connect`, `tls`, `dns`, or
  `other`. No Genia value (`GeniaMap`, `GeniaOptionErr`, `GeniaProtected`,
  etc.) appears anywhere in this module.
- Any status the wrapped server actually returns (including 4xx/5xx)
  normalizes to an ordinary `HttpTransportResponse` via `urllib.error.HTTPError`
  treated as a received response, not a failure — matching `http_operation`'s
  own contract framing that transport-layer success is independent of
  status code. No redirect is ever followed.
- Every other exception raised by the selected transport is caught once at
  `send_http_request`'s own boundary and classified by `_classify`, which
  never re-raises and never retains the original exception's message,
  type name, or traceback: `TimeoutError`/`socket.timeout` maps to
  `timeout`; `ssl.SSLError` (including `SSLCertVerificationError`) maps to
  `tls`; `socket.gaierror` maps to `dns`; `ConnectionRefusedError` and any
  other `OSError` map to `connect`; anything else maps to `other`; a
  `urllib.error.URLError` is classified recursively from its own
  `.reason`.
- Validated by 13 tests in the new `tests/unit/test_http_transport.py`: 5
  real-loopback tests (a Python `http.server` fixture as the server, this
  capability as the client, marked `@pytest.mark.loopback`) proving exact
  method/URL/header/body round-trip, an HTTP-error-status response
  returned as ordinary (not failure), redirect non-following, real
  connect-refused classification, and a real short-timeout classification
  against a server that accepts but never responds; 8 injected-fake-
  transport tests (no real socket) proving dns/tls/timeout/connect/other
  classification including the recursive `URLError.reason` unwrap, and
  byte-exact non-UTF-8/empty body pass-through. The five new loopback test
  IDs are registered in `tests/doc/test_loopback_pytest_partition.py`'s
  exact inventory. No host capability existed for generic outbound
  HTTP before this ticket (only the fixed-endpoint Gemini adapter and the
  inbound R7/R8 server existed); shared/multi-host conformance remains
  Partial.

Explicit limitations:

- No `web.http_send`, outbound client lifecycle composition, or Genia
  builtin/prelude surface (see #624).
- No retries, redirect following, connection pooling, streaming API,
  OAuth, cookies, or async IO — one synchronous attempt only, per the
  approved contract's non-goals.
- No portable failure-reason vocabulary (`http-timeout`/
  `http-transport-failure`/`http-response-invalid`) is constructed by this
  ticket — this capability returns only a closed `kind`; mapping that into
  R14's `err(...)` shapes is #624's composition, not owned here.

~~~~~

## B208: baseline lines 4264-4285

Moved from GENIA_STATE.md@d401f322, lines 4264-4285 (ledger row B208, moved, sha256 974f69f51a32411b)

~~~~~markdown
## 9.14) R14 E14-7 outbound HTTP client lifecycle

Status: Implemented. Issue #624 adds `web.http_send(operation, authority,
timeout_ms) -> some(HttpResponse) | err(reason, context)` per the approved
R14 contract's "Outbound HTTP client lifecycle" section
(`docs/design/r14-composable-lifecycle-contract.md`). It composes four
already-implemented, unchanged mechanisms — the E14-1 lifecycle core, the
`HttpOperation` representation (#622), the host transport capability
(#623), and R10's `declassify` boundary — adding no new lifecycle
primitive, protected-value mechanism, or host transport mechanics.

LANGUAGE CONTRACT:

- `web.http_send(operation, authority, timeout_ms)` executes one
  `LifecycleInstance` internally per call: *prepare* (the already-inert
  `operation` value), *authorize* (declassifying any protected header via
  the existing `declassify(authority, protected_value)`, immediately
  before the one transport attempt), *send*/*receive* (exactly one
  synchronous host transport attempt), *decode* (left entirely to the
  caller's own explicit `utf8_decode`/`json_decode` over `response.body`
  — never automatic), and *finalize* (the internal scope's own `exit`,
  plus the transport's own already-guaranteed resource release).
~~~~~

## B209: baseline lines 4286-4301

Moved from GENIA_STATE.md@d401f322, lines 4286-4301 (ledger row B209, moved, sha256 3886bf14ccc90ed0)

~~~~~markdown
- `authority` is `none(...)` when `operation.headers` carries no
  protected value, or `some(authority)` — an opaque R10
  `GeniaDeclassificationAuthority` — when it does; a `GeniaProtected`
  header value with a missing (`none`) or identity/purpose-mismatched
  authority is runtime misuse (a raised error), exactly as `declassify`
  itself already enforces — `web.http_send` adds no new matching logic,
  it only calls the existing `declassify` once per protected header. A
  malformed `operation`/`authority`/`timeout_ms` argument is likewise
  runtime misuse, raised before any transport attempt is made.
- `timeout_ms` is a required plain integer in `1..300000`, mirroring
  R11's model-call `timeout_ms` contract exactly.
- Any status the transport actually receives (100..599) normalizes to an
  ordinary `some({status, headers, body})` — never a failure; only a
  failure to obtain any response at all is `err(...)`. `headers` keys are
  lowercased; `body` is always an opaque `GeniaBytes` value, never
  auto-decoded or auto-parsed.
~~~~~

## B210: baseline lines 4302-4325

Moved from GENIA_STATE.md@d401f322, lines 4302-4325 (ledger row B210, moved, sha256 f6b8e9746a660d80)

~~~~~markdown
- Recoverable failures are exactly `err("http-timeout", {timeout_ms})`
  (from `HttpTransportFailure(kind="timeout")`) and
  `err("http-transport-failure", {kind: quote(connect)|quote(tls)|
  quote(dns)|quote(other)})` (from every other `HttpTransportFailure`
  kind). `err("http-response-invalid", {stage})` is contract-reserved
  vocabulary this ticket never constructs: #623's transport response is
  always structurally well-formed by construction (an `int` status, a
  `dict[str,str]` headers map, `bytes` body), and #624 performs no
  automatic decode/validation of `response.body` that could discover an
  "invalid" observation — decode is explicitly the caller's own later
  step.
- The query string is assembled deterministically from `operation.query`:
  entries sorted by key, each `key=value` pair with every byte outside
  `ALPHA/DIGIT/-._~` percent-encoded from its UTF-8 bytes (space becomes
  `%20`), pairs joined by `&`, the whole thing prefixed with `?` only
  when `query` is non-empty — the exact table the E14-0 contract reserved
  for this ticket. `operation.body`'s `{kind: quote(text), text}` encodes
  as UTF-8 bytes; `{kind: quote(json), value}` encodes through the same
  `json_encode` capability #622 already used once to fail fast at
  construction time (called again here to obtain the actual bytes, since
  `http_operation` does not persist pre-encoded bytes); `none(...)`
  encodes as zero bytes. `operation.headers`' implicit-vs-explicit
  content-type precedence was already resolved by `http_operation` (#622)
  and is not revisited here.
~~~~~

## B211: baseline lines 4326-4354

Moved from GENIA_STATE.md@d401f322, lines 4326-4354 (ledger row B211, moved, sha256 7963a77e07f03972)

~~~~~markdown
- `web.http_send` has no scope-handle argument and creates no
  ambient/global lifecycle: its internal `LifecycleInstance` has no
  caller-visible parent (there is nothing in the fixed 3-argument
  signature to attach to as a literal parent-linked child); "one HTTP
  operation executes as one child lifecycle instance" is satisfied by
  running exactly one complete entry/work/unwind cycle per call, with
  containment of any resulting failure coming from the ordinary
  Outcome-returning-value composition already used when `web.http_send`
  is called from inside another scope's `work` (the shape #627 proves) —
  R14 adds no second pipeline state machine or HTTP-specific scope kind.

PYTHON REFERENCE HOST:

- `src/genia/http_client.py` (new): `perform_http_send(operation,
  authority, timeout_ms, json_encode, invoke, transport=None)` implements
  the algorithm above. `json_encode`/`invoke` are injected dependencies
  (the same style `construct_http_operation`/`run_lifecycle_scope`
  already use); `declassify` and `send_http_request` are imported
  directly, since both are standalone functions with no `builtins.py`
  closure dependency. All misuse validation (operation/authority/
  timeout_ms shape, protected-header declassification) runs *before* any
  internal lifecycle scope opens, so a raised `TypeError` propagates
  directly to the caller rather than being silently normalized into an
  ordinary `LifecycleResult` by the scope machinery's own
  exception-to-`primary_failure` handling — only the one transport
  attempt (a genuinely recoverable failure mode) runs inside the internal
  `run_lifecycle_scope` call, in a single reserved peer whose `enter`
  performs the send/receive and whose `work` reads the captured result
  back via the existing `lifecycle_context` accessor.
~~~~~

## B212: baseline lines 4355-4369

Moved from GENIA_STATE.md@d401f322, lines 4355-4369 (ledger row B212, moved, sha256 d6af5ac9e82c1783)

~~~~~markdown
- `src/genia/builtins.py`: `http_send_fn` delegates to `perform_http_send`
  and is registered as the private `_http_send` (mirroring
  `_serve_http`/`_with_headers`/`_cors`'s existing
  underscore-prefixed-builtin pattern; no `host_builtin_docs.py`
  `_PUBLIC_DOCS` entry, matching those three). Set
  `__genia_handles_none__ = True` — required because a legitimate
  `none("nil")` `authority` argument is the *common* case (any call with
  no protected header), not an edge case, so without this marker Genia's
  general none-propagation convention would silently short-circuit every
  such call into `none("nil")` instead of performing the request (the
  same bug class #622 caught with `json_encode`/`http_operation`).
  `src/genia/std/prelude/web.genia` adds the public
  `http_send(operation, authority, timeout_ms) = _http_send(...)` wrapper
  with its own `@doc` block, exactly mirroring `serve_http`/
  `with_headers`/`cors`.
~~~~~

## B213: baseline lines 4370-4388

Moved from GENIA_STATE.md@d401f322, lines 4370-4388 (ledger row B213, moved, sha256 5a6c23cefdbe8e9f)

~~~~~markdown
- Validated by 26 tests in the new `tests/unit/test_http_send.py`: any
  received status returns an ordinary response (never a failure); exactly
  one transport call per `http_send` invocation; all 5
  `HttpTransportFailure` kinds mapped to the correct reason; malformed
  `operation`/`authority`/`timeout_ms` raise (not normalized); a
  protected header with a missing or mismatched authority raises via the
  existing `declassify`; a protected header with a matching authority is
  declassified, reaches the fake transport as its plain string, and never
  appears in the returned response or any string rendering of it; exact
  query percent-encoding (reserved characters, space, `/`, `&`); exact
  `text`/`json`/`none` body encoding; response header keys lowercased;
  response body is `GeniaBytes` not a plain string; and one real
  `run_source` + real-loopback-server end-to-end test (registered in
  `tests/doc/test_loopback_pytest_partition.py`'s exact inventory). No
  change to `lifecycle_runtime.py`, `http_operation.py`,
  `http_transport.py`, or `configuration.py`. No new host capability is
  introduced (#624 only consumes #623's existing one); shared/multi-host
  conformance remains Partial.

~~~~~

## B214: baseline lines 4389-4400

Moved from GENIA_STATE.md@d401f322, lines 4389-4400 (ledger row B214, moved, sha256 975de8eeb4cedac5)

~~~~~markdown
Explicit limitations:

- No `@get`/`@post` verb annotations, inbound server/request integration,
  or YouVersion-specific behavior (see #625-#628).
- No retries, circuit breakers, redirect-following beyond "none",
  connection pooling, or streaming client API — one synchronous attempt
  only, per the approved contract's non-goals.
- Constructing a `GeniaDeclassificationAuthority` from ordinary Genia
  source is not possible — exactly like R11's `model` credential/
  authority, it is always an opaque, externally host-injected value; this
  is unchanged by #624 and is not a gap this ticket needs to close.

~~~~~

## B215: baseline lines 4401-4419

Moved from GENIA_STATE.md@d401f322, lines 4401-4419 (ledger row B215, moved, sha256 32595a93fcb82cbb)

~~~~~markdown
## 9.15) R14 E14-8 protected HTTP credential sinks

Status: Implemented, with **zero runtime-code change**. Issue #625
proves, at comprehensive regression breadth, the contract-approved
"Protected HTTP sinks" section (`docs/design/r14-composable-lifecycle-contract.md`)
that #622 and #624 already implement correctly. This is the same
"already-correct mechanism, proven not built" shape as E14-2 (#692) and
E14-4 (#694).

LANGUAGE CONTRACT (proven, not newly introduced):

- A protected header value placed in `http_operation`'s `headers` field
  stays protected through construction, storage inside the resulting
  `HttpOperation` map, and any later `display`, `debug_repr`, or
  `json_encode` attempt (which fails closed with
  `err("protected-value", {operation: "json-encode"})`, recursively
  detecting the nested protected leaf) — R10's existing recursive
  sink-scan rules apply exactly as to any other map holding a protected
  leaf, with no special case for `HttpOperation`.
~~~~~

## B216: baseline lines 4420-4433

Moved from GENIA_STATE.md@d401f322, lines 4420-4433 (ledger row B216, moved, sha256 14f078fbc8974147)

~~~~~markdown
- Generic representation-family operations — `represent`,
  `representation_match`, `strip_representation` — reject the reserved
  `secret` facet identically whether the protected value under test is a
  bare one or one specifically carried inside an `HttpOperation`'s
  `headers` field; the raised diagnostic text contains no trace of the
  protected value's identity, purpose, or payload.
- The only place a protected header's carried string is ever read is
  inside `web.http_send`'s private host implementation
  (`_resolve_headers` in `src/genia/http_client.py`), immediately before
  the one transport attempt, through the existing `declassify(authority,
  protected_value)`; this is `web.http_send`'s new sink family and the
  new `quote(http_send)` declassification purpose convention, exactly the
  extension shape R11 used for `quote(model_call)` — R10 gains no new
  protected-value mechanism.
~~~~~

## B217: baseline lines 4434-4448

Moved from GENIA_STATE.md@d401f322, lines 4434-4448 (ledger row B217, moved, sha256 be3a5cfa370c24f4)

~~~~~markdown
- A missing (`none`) authority, a mismatched-identity authority, or a
  mismatched-purpose authority, each with a protected header present,
  fails deterministically (a raised `TypeError`, matching `declassify`'s
  own existing behavior) with no protected payload, key, or purpose
  appearing in the raised diagnostic text — proven for all three cases,
  not just the one #624 already exercised.
- `HttpResponse` values are always ordinary: response status/headers/body
  are built entirely from primitive `str`/`int`/`bytes` values returned
  by the host transport, so they structurally cannot carry R10/R14
  protection — this reuses R10's existing "a boundary that produces a
  value from external bytes never manufactures protection" rule, proven
  directly rather than only reasoned about.

PYTHON REFERENCE HOST:

~~~~~

## B218: baseline lines 4449-4467

Moved from GENIA_STATE.md@d401f322, lines 4449-4467 (ledger row B218, moved, sha256 ae8a0cc42c583d83)

~~~~~markdown
- No change to `src/genia/http_client.py`, `http_transport.py`,
  `http_operation.py`, `configuration.py`, or `values.py` — confirmed via
  `git diff origin/main..HEAD` showing only a new test file.
- Validated by 7 tests in the new `tests/unit/test_http_protected_sinks.py`:
  display/debug_repr/failed-json_encode sentinel-free survival of a
  real-`secret_get`-constructed protected header inside an
  `HttpOperation`; generic representation-family rejection of the same
  header-carried protected value; one full real round trip (`secret_get`
  → `http_operation` → `perform_http_send` with a matching authority)
  proving the plain credential reaches only the fake transport and
  appears in no returned value, operation rendering, or audit event;
  three parametrized unauthorized-placement failure cases (mismatched
  purpose, mismatched provider, missing authority), each swept for
  sentinel leakage in the raised diagnostic; and one structural
  confirmation that an ordinary `HttpResponse` never carries a
  `<protected>` marker. All sentinel constants follow this codebase's
  established synthetic-naming convention (never realistic-looking
  secret text), matching `tests/unit/test_declassification.py`'s and
  `tests/unit/test_protected_configuration.py`'s existing discipline.
~~~~~

## B219: baseline lines 4468-4482

Moved from GENIA_STATE.md@d401f322, lines 4468-4482 (ledger row B219, moved, sha256 001f02798cb299b7)

~~~~~markdown
- `GENIA_RULES.md`'s sink-invariant enumeration gains one new sentence
  distinguishing this **authorized** outbound-HTTP-header sink (accepts a
  protected value, reveals it only through `declassify` at one point)
  from the pre-existing **rejecting** sinks already listed there (output,
  JSON encoding, Sheet/CSV rendering, resource writes, the R7 server's
  own inbound `http-response` guard) — the same authorized-sink shape
  R11's `model` credential argument already uses.

Explicit limitations:

- No vault, key rotation, encryption-at-rest, OAuth, or cookie/session
  policy — out of scope per the issue's own non-goals.
- No broad information-flow/taint tracking; no change making all HTTP
  headers secret-aware by default — only `headers` (never `query`, which
  #622 already rejects protected values in outright).
~~~~~

## B220: baseline lines 4483-4485

Moved from GENIA_STATE.md@d401f322, lines 4483-4485 (ledger row B220, moved, sha256 6498e408535004b4)

~~~~~markdown
- No change to R10 protected semantics outside this narrow, already-landed
  integration.

~~~~~

## B221: baseline lines 4486-4500

Moved from GENIA_STATE.md@d401f322, lines 4486-4500 (ledger row B221, moved, sha256 f5bba8a496da2eec)

~~~~~markdown
## 9.16) R14 E14-9 declarative outbound HTTP annotations

Status: Implemented. Issue #626 adds `@get {path}` and `@post {path}`
inert descriptive annotations and `web.send_annotated(fn, base_url,
authority, timeout_ms)`, the sole function that binds annotation metadata
to the existing `HttpOperation`/`web.http_send` surface. Unlike every
other R14 ticket, the approved E14-0 contract does not specify this
feature's exact shape — it is explicitly listed under the contract's own
"Non-goals" as "planned no earlier than roadmap #626... still inert
descriptors, not self-executing IO" — so this section records design
decisions #626 itself made, following the existing `@route` annotation's
established shape as closely as possible, not a pre-locked contract.

LANGUAGE CONTRACT:

~~~~~

## B222: baseline lines 4501-4516

Moved from GENIA_STATE.md@d401f322, lines 4501-4516 (ledger row B222, moved, sha256 4f98d4d760ccd777)

~~~~~markdown
- `@get {path: string}` / `@post {path: string}` are valid only on a
  top-level named function with a fixed zero-argument arm; any other
  target (assignment, named pattern, wrong arity) is a deterministic
  diagnostic. `path` must be a non-empty string starting with `/`; any
  other descriptor shape (missing/extra keys, wrong type) is a
  deterministic diagnostic. `method` is never a descriptor field — it is
  implied by the annotation's own name, matching how `web.genia`'s
  existing `get`/`post` prelude functions already derive method from
  function name.
- `@get` and `@post` share one cardinality slot per declaration: at most
  one of either may appear, combined — a function cannot coherently be
  both a GET and a POST operation. Repeating either, or annotating both
  on one declaration, is a deterministic diagnostic. Annotated rebinding
  that would replace existing `http_annotation` metadata is also a
  deterministic diagnostic — mirrors `@route`'s exact
  rebinding/replacement rules.
~~~~~

## B223: baseline lines 4517-4540

Moved from GENIA_STATE.md@d401f322, lines 4517-4540 (ledger row B223, moved, sha256 ae0e90219111ce5d)

~~~~~markdown
- Annotating a function **never changes how it is called** — this is the
  same invariant every existing annotation (`@route`, `@server`, `@cors`)
  already upholds. Calling an annotated function with ordinary Genia call
  syntax never performs network IO; only the separate, explicit
  `web.send_annotated(fn, base_url, authority, timeout_ms)` call does.
  Loading, importing, or evaluating a declaration carrying `@get`/`@post`
  performs zero network IO, exactly like every other annotation.
- `web.send_annotated` reads the annotated function's `{verb, path}`
  descriptor, calls the function with no arguments to obtain its dynamic
  `{headers, query, body}` map (any other return shape is deterministic
  misuse), builds the operation via the unchanged
  `http_operation(verb, base_url, path, headers, query, body)`, and calls
  the unchanged `web.http_send(operation, authority, timeout_ms)` —
  composing exactly these two already-implemented functions. No new
  transport or lifecycle mechanism exists; `base_url`/`authority`/
  `timeout_ms` are ordinary call-time arguments, never annotation-static,
  matching how neither `@server`'s host/port nor R11's `model` config are
  annotation-static either. Each call to `send_annotated` creates a
  fresh, independent lifecycle instance (a fresh `send_http_request`
  attempt every time — no caching, no shared state across calls). An
  `http_operation` construction failure (a malformed dynamic `query`/
  `body`) propagates unchanged as `err("http-operation-invalid",
  {stage})`.

~~~~~

## B224: baseline lines 4541-4554

Moved from GENIA_STATE.md@d401f322, lines 4541-4554 (ledger row B224, moved, sha256 375c88c4b4241fef)

~~~~~markdown
PYTHON REFERENCE HOST:

- `src/genia/evaluator.py`: two new dispatch branches in
  `eval_annotations` (mirroring `@route`'s exact placement), a
  duplicate-cardinality check treating `get`/`post` as one shared group,
  two new rebinding/replacement guard methods
  (`_reject_http_annotation_metadata_rebinding`/`_replacement`) called at
  every declaration-processing site `@route`'s own guards are already
  called at, and an updated unsupported-annotation whitelist message.
  This is the first R14 ticket to touch this shared, sensitive dispatch
  file; the full existing `@route`/`@server`/`@cors` test suites
  (`test_server_route_binding.py`, `test_server_config_binding.py`,
  `test_server_cors_binding.py`, 53 tests) were re-run and confirmed
  unaffected.
~~~~~

## B225: baseline lines 4555-4574

Moved from GENIA_STATE.md@d401f322, lines 4555-4574 (ledger row B225, moved, sha256 78bb146655de86b1)

~~~~~markdown
- `src/genia/http_annotation_binding.py` (new):
  `validate_http_annotation_descriptor(verb_name, value)` (mirrors
  `validate_route_descriptor`'s exact structure/error style),
  `resolve_http_annotation(fn)` (reads the descriptor directly off the
  `GeniaFunctionGroup` value's own `.metadata` attribute — confirmed via
  `environment.py`'s `merge_binding_metadata` that a function group's
  metadata is stored both in the environment's binding-metadata table
  and directly on the function-group object itself, so no whole-file
  discovery pass or name-based lookup is needed, unlike `@route`'s own
  `server_route_binding.py` discovery module), and
  `perform_send_annotated(fn, base_url, authority, timeout_ms,
  json_encode, invoke, transport=None)` implementing the composition
  above.
- `src/genia/builtins.py`: `send_annotated_fn` delegates to
  `perform_send_annotated`, registered as the private `_send_annotated`
  (mirroring `_http_send`), with `__genia_handles_none__ = True` for the
  same reason as `_http_send` (a legitimate `none("nil")` `authority`
  argument is the common case). `src/genia/std/prelude/web.genia` adds
  the public `send_annotated(fn, base_url, authority, timeout_ms)`
  wrapper with its own `@doc` block.
~~~~~

## B226: baseline lines 4575-4588

Moved from GENIA_STATE.md@d401f322, lines 4575-4588 (ledger row B226, moved, sha256 d9ff717ae28708ad)

~~~~~markdown
- Validated by 21 tests: 13 in the new `tests/unit/test_http_annotations.py`
  (evaluator-level attachment/validation/rebinding, and structural proof
  that mere evaluation and direct ordinary calling never perform IO) and
  8 in the new `tests/unit/test_http_send_annotated.py`
  (`perform_send_annotated`'s own composition behavior via an injected
  fake transport, matching #624's own testing style). No change to
  `http_operation.py`, `http_transport.py`, `http_client.py`'s
  `perform_http_send`, or `configuration.py`. No new host capability.

Explicit limitations:

- No verb beyond `get`/`post` — the only two the contract's own
  non-goals sentence names; put/patch/delete/head/options annotations
  remain unimplemented.
~~~~~

## B227: baseline lines 4589-4594

Moved from GENIA_STATE.md@d401f322, lines 4589-4594 (ledger row B227, moved, sha256 6a1618df2bf4d005)

~~~~~markdown
- No server `@route` replacement, middleware/auth/retry DSL, macro,
  compile-time transform, or general annotation framework.
- No change to R10 protected semantics, the E14-1 lifecycle core, or the
  E14-5/E14-7 `HttpOperation`/`web.http_send` surface — this ticket only
  adds a new way to construct calls into that unchanged surface.

~~~~~

## B228: baseline lines 4595-4609

Moved from GENIA_STATE.md@d401f322, lines 4595-4609 (ledger row B228, moved, sha256 7c742373fcecf973)

~~~~~markdown
## 9.17) R14 E14-10 server/request/outbound-client composition

Status: Implemented, with **zero runtime-code change**. Issue #627
proves the central R14 record-pipeline-adjacent claim: an inbound R8
server request can create one or more outbound HTTP client lifecycle
instances while the server remains active and resource/failure ownership
stays correct. Direct code reading confirms `src/genia/server_lifecycle.py`
(R8) has zero dependency on `src/genia/lifecycle_runtime.py` (R14's E14-1
core) — they are, and remain, architecturally separate. Composition is
possible because an R8 route handler is an ordinary one-argument
function and `web.http_send`/`web.send_annotated` (E14-7/E14-9) impose no
caller-context precondition; this section records the proof, not a new
mechanism, mirroring E14-2 (#692) and E14-8 (#625)'s own established
"proven, not built" shape.

~~~~~

## B229: baseline lines 4610-4623

Moved from GENIA_STATE.md@d401f322, lines 4610-4623 (ledger row B229, moved, sha256 51c85b05cf9ecab4)

~~~~~markdown
LANGUAGE CONTRACT (proven, not newly introduced):

- A route handler registered through the existing `web.route_request`
  may call `web.http_send` or `web.send_annotated` any number of times
  during its own invocation; each call independently runs its own
  complete E14-1 entry/work/unwind cycle and finalizes its own
  transport-level resources, entirely independent of the R8 request
  scope's own lifetime.
- A transport failure from an outbound call (e.g. connection refused)
  normalizes to the existing `err("http-transport-failure", {kind})`
  Outcome exactly as it would from any other caller; the handler
  receives it as ordinary data and decides how to respond — it never
  implicitly terminates the request or the server. The server continues
  accepting and completing further requests afterward.
~~~~~

## B230: baseline lines 4624-4639

Moved from GENIA_STATE.md@d401f322, lines 4624-4639 (ledger row B230, moved, sha256 efdc8b202b269b76)

~~~~~markdown
- One request handler may make multiple sequential outbound calls; each
  is entirely independent (no shared transport state, no caching).
- The server's own listener remains owned exclusively by the existing
  R8 server scope; an outbound call's own transport resources are never
  visible to, and cannot affect, that ownership.
- No second server, routing, or CORS mechanism is introduced; existing
  R7/R8 `route_request`/`with_headers`/`cors`/`serve_http` behavior is
  entirely unchanged.

PYTHON REFERENCE HOST:

- No change to `server_lifecycle.py`, `lifecycle_runtime.py`,
  `http_client.py`, `http_transport.py`, `http_operation.py`,
  `http_annotation_binding.py`, or any R7/R8 routing/CORS module —
  confirmed via `git diff origin/main..HEAD` showing only a new test
  file and documentation.
~~~~~

## B231: baseline lines 4640-4654

Moved from GENIA_STATE.md@d401f322, lines 4640-4654 (ledger row B231, moved, sha256 03ce8080b0135bdf)

~~~~~markdown
- Validated by 4 real-loopback tests in the new
  `tests/unit/test_http_server_client_composition.py` (a real R8 server
  under test, driven by real inbound HTTP requests, whose route handler
  calls out to a second real local downstream fixture server): a
  successful outbound call with the server completing two successive
  requests; a failing outbound call (real connect-refused) contained by
  the handler with the server still completing both requests; one
  handler making two sequential outbound calls in a single request; and
  the same success shape composed through `web.send_annotated` instead
  of direct `http_operation`/`web.http_send`. The existing R7/R8
  regression suite (`test_server_lifecycle.py`,
  `test_server_route_binding.py`, `test_server_config_binding.py`,
  `test_server_cors_binding.py`, `test_http_web.py`, 82 tests) was
  re-confirmed unaffected.

~~~~~

## B232: baseline lines 4655-4665

Moved from GENIA_STATE.md@d401f322, lines 4655-4665 (ledger row B232, moved, sha256 971c4168beacaa8d)

~~~~~markdown
Explicit limitations:

- No concurrent-serving guarantee beyond R8's existing one; no
  distributed tracing, request cancellation API beyond the approved
  contract, retries, circuit breakers, or new inbound HTTP syntax.
- No protected-credential-specific integration case is proven here
  beyond what #625 already established generically — a credentialed
  outbound call from a route handler composes the same way as any other
  `web.http_send` call, with no additional server-specific behavior.
- No domain-specific proving application (that is #628's job).

~~~~~

## B233: baseline lines 4666-4724

Moved from GENIA_STATE.md@d401f322, lines 4666-4724 (ledger row B233, moved, sha256 c8320511e9f21b94)

~~~~~markdown
## 9.18) R14 E14-11 repeated record lifecycle proving case

Status: Implemented, with **zero runtime-code change**. Issue #695 proves
the record-pipeline-adjacent claim from
`docs/design/r14-composable-lifecycle-contract.md`'s "Repeated record proof
(pressure test)" section: `lifecycle_scope` (E14-1), `lifecycle_repeat`
(E14-3), and `lifecycle_context` (E14-1) already compose into a repeated
record-processing pipeline with no new API, syntax, or lifecycle primitive.

LANGUAGE CONTRACT (proven, not newly introduced):

- One outer pipeline/session `lifecycle_scope` wraps a `lifecycle_repeat`
  call; each consumed element gets its own fresh element scope with at
  least two peer `LifecycleDefinition`s (a `record_context` peer and a
  `diagnostics` peer), entered and reverse-unwound deterministically per
  the existing E14-1/E14-3 algorithm.
- `record`/`fields`/`nr`/`nf`-style values are derived by application code
  reading the reserved `quote(element)`/`quote(index)` context through the
  existing `lifecycle_context` accessor — no `$0`/`$1`/`NR`/`NF` syntax and
  no new AWK-mode primitive is introduced (per this contract's explicit
  non-goal).
- An eager `List` source never short-circuits: a data-level malformed
  record (a field-count mismatch, surfaced as ordinary `err(...)` data
  returned by `element_work`, per the existing "not treated specially"
  work-return rule) and a genuine element work-phase exception (a
  non-string element) are each recovered from independently, with every
  later element still processed and no cross-element context leakage.
- A lazy `Flow` source composes with the existing `take` bound: each
  yielded element's scope is fully entered and unwound before the next
  pull (the existing close-before-next-pull guarantee), and bounded early
  termination never leaves a scope partially entered.
- Survived (successfully classified) records are captured as ordinary
  values by filtering/mapping each element's `LifecycleResult.result`,
  using only existing `filter`/`map` list operations — no dedicated
  filtering primitive is introduced.

PYTHON REFERENCE HOST:

- No change to `lifecycle_runtime.py`, `builtins.py`, or any other runtime
  module — confirmed via `git diff origin/main..HEAD --stat -- src/genia/`
  showing no production-code changes.
- New example `examples/r14_repeated_record_lifecycle_proving_case.genia`
  runnable directly via `genia examples/r14_repeated_record_lifecycle_proving_case.genia`.
- Validated by 10 tests in the new
  `tests/unit/test_r14_repeated_record_lifecycle_proving_case_695.py`
  (loading the example through real Genia source via `run_source`) and the
  new `spec/cli/r14-repeated-record-lifecycle-proving-case.yaml` end-to-end
  CLI fixture (confirmed via `python -m tools.spec_runner`, 586/586
  passing). The existing `test_lifecycle_runtime.py`/`test_lifecycle_repeat.py`
  regression suites remain unaffected.

Explicit limitations:

- No AWK language mode, `$0`/`$1`/`NR`/`NF` syntax, or record-shape
  derivation beyond ordinary `lifecycle_context` reads.
- No new `map`/`filter`/`scan`/`rules` API; the example composes only
  existing list/Flow operations.
- No HTTP behavior (that is #628's job).

~~~~~

## B234: baseline lines 4725-4740

Moved from GENIA_STATE.md@d401f322, lines 4725-4740 (ledger row B234, moved, sha256 18d079300671b4e7)

~~~~~markdown
## 9.19) R14 E14-12 YouVersion Bible proxy proving application

Status: Implemented, with **zero runtime-code change**. Issue #628 proves
the contract's "HTTP vertical proving case" section: `config_view`/
`secret_view` (R13), `http_operation`/`web.http_send` (R14 E14-5/E14-7,
#622/#624), the protected HTTP header sink (E14-8, #625), and
`web.serve_http`/`web.route_request` (R8) already compose into a
complete end-to-end proving application with no new mechanism.

LANGUAGE CONTRACT (proven, not newly introduced):

- Base URL, Bible/version ID, and API credential resolve entirely through
  the landed R13/R10 configuration model — `config_view(provider,
  "YOUVERSION_")` for the ordinary values, `secret_view(provider,
  "YOUVERSION_", quote(bible_proxy_outbound))` for the protected
  credential — with no new configuration mechanism.
~~~~~

## B235: baseline lines 4741-4762

Moved from GENIA_STATE.md@d401f322, lines 4741-4762 (ledger row B235, moved, sha256 595ac21bd48adc29)

~~~~~markdown
- One `http_operation` per canonical passage reference carries the
  credential in a protected header; the credential is declassified only
  immediately inside `web.http_send`'s existing transport boundary,
  exactly as E14-8 already proved generically.
- An R8 `POST /passages` route handler is an ordinary function that
  dispatches one `web.http_send` call per reference — outbound child
  HTTP lifecycle instances created from an inbound request, exactly the
  composition E14-10 (#627) already proved architecturally correct.
- An upstream non-2xx response or transport failure (including
  connect-refused) classifies to a deterministic per-reference
  `{status: "error", reason, ...}` value in the structured JSON
  response; it is ordinary data, never a lifecycle failure, and never
  stops the server from completing further requests.
- **Minting a declassification authority is a privileged host-side
  operation, never a pure-Genia one** — no `make_global_env` parameter
  or Genia builtin constructs one (confirmed by direct code reading, the
  same boundary R13's own proving case already established; see
  `docs/releases/R13.md`). A plain `genia` CLI run of the example
  therefore only resolves configuration and shows the credential stays
  protected; the full outbound round trip is exercised entirely by a
  Python-host test that injects a real authority.

~~~~~

## B236: baseline lines 4763-4787

Moved from GENIA_STATE.md@d401f322, lines 4763-4787 (ledger row B236, moved, sha256 d95e22e25f546586)

~~~~~markdown
PYTHON REFERENCE HOST:

- No change to `src/genia/http_client.py`, `http_operation.py`,
  `configuration.py`, `server_lifecycle.py`, or any other runtime module
  — confirmed via `git diff origin/main..HEAD --stat -- src/genia/`
  showing no production-code changes.
- New example
  `examples/r14_youversion_bible_proxy_proving_case.genia`, runnable
  directly via `genia examples/r14_youversion_bible_proxy_proving_case.genia`.
- Validated by 7 tests in the new
  `tests/unit/test_r14_youversion_bible_proxy_proving_case_628.py`: the
  CLI-demo configuration path; a real R8 server plus a local mock-upstream
  `ThreadingHTTPServer` fixture proving a multi-reference request
  produces a structured response via real outbound calls, with the mock
  upstream receiving the declassified credential header; an upstream
  5xx and a connect-refused upstream each producing a deterministic
  per-reference error without killing the server; the protected
  credential never appearing in any response body or audit record; and
  a structural check that no real credential or network dependency
  exists in source. Four of these are `@pytest.mark.loopback`,
  registered in `tests/doc/test_loopback_pytest_partition.py`'s
  maintained inventory. The new
  `spec/cli/r14-youversion-bible-proxy-proving-case.yaml` fixture is
  confirmed via `python -m tools.spec_runner` (587/587 passing).

~~~~~

## B237: baseline lines 4788-4800

Moved from GENIA_STATE.md@d401f322, lines 4788-4800 (ledger row B237, moved, sha256 a9aba938d03168fc)

~~~~~markdown
Explicit limitations:

- No human-language Bible-reference parsing; references are opaque
  caller-supplied strings.
- No Bible search, verse indexing, caching, theology/domain
  abstractions, or YouVersion-specific language APIs.
- No real YouVersion credential or public network dependency anywhere in
  automated tests; the fake credential
  (`FAKE_YOUVERSION_KEY_SENTINEL_628`) is an explicit synthetic
  sentinel, never a value resembling a real API key.
- No retries, auth framework, or capability beyond what R14 already
  implements.

~~~~~

## B238: baseline lines 4801-4859

Moved from GENIA_STATE.md@d401f322, lines 4801-4859 (ledger row B238, moved, sha256 7bd3f4b53b2688fd)

~~~~~markdown
## 9.20) R14 E14-13 cross-mode lifecycle and HTTP hardening

Status: Implemented, with **zero runtime-code change**. Issue #696
proves, at combined cross-cutting breadth, that E14-1 through E14-12
already satisfy the contract's full combined boundary — the same
"conformance proof only" shape as R13's E13-5 (#675).

LANGUAGE CONTRACT (proven, not newly introduced):

- Importing or discovering (native-test mode) a module that defines,
  but never invokes, `http_operation`/`@get`/`@post`/lifecycle
  functions performs zero outbound transport calls.
- An `@get`/`@post` annotation's own registration at server startup
  never self-executes; only an explicit `web.send_annotated` call
  inside a request handler performs IO — proven against a real R8
  server and a real local downstream fixture.
- A protected credential and ordinary lifecycle-context data survive
  `display`/`debug_repr` rendering together in one comprehensive value
  with no sentinel leak.
- A work-phase primary failure survives a combined multi-peer,
  multi-exit-failure matrix (3 peers, 2 independent exit failures): the
  primary failure stays the work failure, and both exit failures land
  in `cleanup_failures` in exit-call (reverse-entry) order.
- `take(n)` over `lifecycle_repeat` with a protected value threaded
  through each element scope pulls exactly `n` elements, closing each
  scope before the next pull, with no cross-element leak.
- A raising transport's raw Python exception text never reaches the
  normalized `err("http-transport-failure", {kind})` Outcome — only the
  closed `{kind}` shape crosses the boundary.
- One request making both a successful and a failed outbound call,
  followed by a second successful request against the same server,
  proves combined server/request/outbound-client resilience with no
  external network.
- Every R14 call form (`lifecycle_scope`/`child`/`repeat`/`context`/
  `config`, `http_operation`, `web.http_send`/`send_annotated`,
  `@get`/`@post`) still parses using only ordinary existing call/
  annotation/map/list grammar — no new parser/AST/Core IR node.

PYTHON REFERENCE HOST:

- No change to any `src/genia/` module — confirmed via `git diff
  origin/main..HEAD --stat -- src/genia/` showing no production-code
  changes.
- Validated by 10 tests in the new
  `tests/unit/test_r14_cross_mode_hardening_696.py`, two of which are
  `@pytest.mark.loopback` (registered in
  `tests/doc/test_loopback_pytest_partition.py`'s maintained
  inventory). The full non-loopback regression suite, the full
  loopback suite, `python -m tools.spec_runner`, and `tests/doc`
  (including R8/R10/R13/Flow/annotation coverage) all remain green.

Explicit limitations:

- No new public helper, syntax, annotation, or parser/AST/Core IR node.
- No retries, resilience framework, async, concurrency, or scheduler
  behavior.
- No feature redesign; this is conformance proof only, matching R13's
  E13-5 precedent.

~~~~~
