# R11 AI Composition Contract

Status: **Approved contract; E11-1/E11-2 implemented as Experimental, later slices planned.**

This document fixes the semantic boundary for R11 tickets. E11-1/E11-2 now implement
the text and R9-validated JSON `model/4` deterministic-fixture subset. This design document must
not be cited as the authority for current language behavior.
`GENIA_STATE.md` remains final authority for implemented behavior.

## Purpose

R11 permits one model call to participate in Genia as an ordinary callable,
Outcome-producing pipeline stage. Messages and observations remain ordinary
values, prompts remain functions, chains remain pipelines, and conversation
state evolves from external input through existing `scan` behavior.

R11 adds no AI object hierarchy, second pipeline, autonomous executor, hidden
memory, implicit configuration, syntax, annotation, lifecycle, or Core IR node.

## Terms

- **Provider capability**: an opaque host-injected value implementing one
  provider protocol. Source cannot construct, inspect, compare, render,
  serialize, or persist it.
- **Model configuration**: the closed ordinary map `{id, timeout_ms}`.
- **Model**: the ordinary callable returned by `model(...)`. Calling it once
  performs at most one provider attempt and returns an Outcome.
- **Message**, **request**, **response**, **usage**, **conversation input**, and
  **conversation state**: exact ordinary values defined below, never classes.
- **Structured output**: provider text decoded through R9 `json_decode`, kept
  under one outer `json` representation, and checked by an explicit Template.
- **Provider attempt**: the single adapter operation after local validation and
  successful R10 declassification.

## Public surface

The complete new R11 public surface is one ordinary function:

```text
model(provider, config, credential, authority) -> callable_model
callable_model(request) -> some(response) | none("model-no-response") | err(reason, context)
```

`model(...)` validates and captures four explicit arguments without network
access:

- `provider` is an opaque model-provider capability supplied at an explicit
  host/application boundary;
- `config` is exactly `{id: string, timeout_ms: integer}`, where `id` is
  non-empty and `timeout_ms` is in `1..300000`;
- `credential` is exactly one R10 protected `secret` carrying a string;
- `authority` is an opaque R10 authority matching the credential's R10
  configuration-provider identity and purpose `quote(model_call)`.

Malformed arguments and extra/missing config keys are construction-time runtime
misuse. A wrong protected purpose or authority/credential identity mismatch is
runtime misuse at invocation-time declassification, before a provider attempt.
Validation reveals no protected data. Construction does not declassify,
contact a provider, or record a declassification audit event.

The provider capability factory is host API, not another Genia public
function. The Python proof supplies one provider-specific capability and one
deterministic fixture capability through a harness/application boundary. There
is no provider registry, name dispatch, general outbound HTTP function,
ambient provider, or implicit configuration read.

Rejected public APIs include `Message`, `Prompt`, `Chain`, `Response`, `Tool`,
`Agent`, `AgentExecutor`, `Runnable`, `RunnableSequence`, provider classes,
`chat(...)`, `complete(...)`, `generate(...)`, and AI-specific pipe operators.

## Exact ordinary value shapes

All maps in this section are closed: missing or extra keys are runtime misuse
at an R11 boundary. Lists preserve source order.

### Content and messages

Content has exactly one of these shapes:

```text
{kind: quote(text), text: string}
{kind: quote(json), value: json_represented_value}
```

`json_represented_value` is an ordinary JSON-domain value under exactly one
outer R9 `json` representation. A content map cannot contain both `text` and
`value`. Image, audio, binary, file, URL, multipart, and provider-specific
content are excluded.

A message is exactly:

```text
{role: quote(system) | quote(user) | quote(assistant), content: content}
```

Messages may occur in any order. An empty message list is runtime misuse.
Tool/developer roles and provider-specific roles are excluded.

### Output requirement and request

An output requirement is exactly:

```text
{kind: quote(text)}
{kind: quote(json), schema: json_represented_schema, template: callable_template}
```

For JSON output, `schema` is exactly one outer `json`-represented schema value
accepted by R9 `json_schema`, and `template` is an ordinary one-argument
Outcome Template applied locally. It is normally the Template compiled from
that schema, but R11 neither requires nor claims callable identity metadata;
the supplied Template is the exact local validation contract. Both are explicit
because R9 Templates have no implemented introspection metadata from which an
adapter can reconstruct a provider schema.

A request is exactly:

```text
{messages: [message, ...], output: output_requirement}
```

Temperature, sampling, seeds, token limits, stop strings, metadata, user IDs,
provider options, tools, and per-call timeout overrides are excluded. Provider
defaults are adapter policy and are not portable semantics except through the
normalized response/error observations below.

### Usage and response

Usage is exactly:

```text
{input_tokens: non_negative_integer, output_tokens: non_negative_integer, total_tokens: non_negative_integer}
```

`total_tokens` equals the other two fields' sum. Unreported usage becomes
`none("model-usage-unavailable")`; malformed or inconsistent reported usage is
`err("model-response-invalid", {stage: quote(usage)})`.

A response is exactly:

```text
{
  message: {role: quote(assistant), content: content},
  finish_reason: quote(stop) | quote(length) | quote(filtered) | quote(other),
  usage: some(usage) | none("model-usage-unavailable")
}
```

Provider finish reasons normalize into this set; provider-specific reason text
is discarded. Text requests succeed with text content. JSON requests decode
returned text through `json_decode` and succeed with JSON content retaining one
outer `json` facet. A wrong content variant cannot be a successful response.

### Tools

No tool declaration, request, result, role, or invocation shape is retained in
R11. Tools are unnecessary for the exit criterion and deferred unless a later
contract demonstrates an ordinary-function need. R11 has no hidden tool loop,
planner, memory manager, or agent executor.

If later promoted, tools must remain ordinary functions plus ordinary metadata,
and model output must remain inert until source explicitly invokes a selected
function. This is a constraint, not a planned API.

## Call semantics

Calling a model:

1. Validates the closed request, messages, content, output requirement, schema,
   and Template callability without declassification or a provider call.
2. Translates ordinary request values through the provider adapter; SDK/wire
   objects stay host-local.
3. Immediately before the one provider attempt, invokes existing R10
   declassification with the captured authority and credential.
4. Makes exactly one synchronous attempt with the finite configured timeout.
   No retry, fallback, race, stream, or background task starts.
5. Normalizes the provider observation to an Outcome without retaining provider
   bodies, exception text, headers, request IDs, credential/key text, or
   provider identity.
6. For JSON output, decodes through R9 `json_decode`, then applies the supplied
   Template to the carried ordinary value while retaining the represented value
   in the successful response.

The model returns only after a response or failure. Invocations are independent.
The callable stores only explicit fixed configuration/capabilities; it has no
history, cache, memory, usage accumulator, retry state, or planner state.

Prompts are ordinary request-building functions. Chains use ordinary functions
and `|>`. R11 adds no prompt syntax or chain registry/execution API.

## Outcomes and errors

The complete recoverable result set is:

| Observation | Result |
|---|---|
| normalized valid response | `some(response)` |
| provider completed without a usable candidate | `none("model-no-response")` |
| configured deadline elapsed | `err("model-timeout", {timeout_ms})` |
| provider rate limit | `err("model-rate-limited", {retry_after_ms})` |
| provider rejected a valid request | `err("model-rejected", {kind})` |
| connection/provider availability failure | `err("model-transport-failure", {kind})` |
| malformed response/normalization failure | `err("model-response-invalid", {stage})` |
| JSON decode or Template did not succeed | `err("model-structured-output-invalid", {stage, outcome})` |

Context shapes are exact:

- `{timeout_ms: integer}` repeats the configured non-sensitive timeout.
- `{retry_after_ms: some(non_negative_integer)}` or
  `{retry_after_ms: none("model-retry-after-unavailable")}`.
- `{kind: quote(authentication) | quote(permission) | quote(policy) |
  quote(request) | quote(unavailable) | quote(other)}`.
- `{stage: quote(message) | quote(finish_reason) | quote(usage) |
  quote(provider_response)}` for `model-response-invalid`.
- `{stage: quote(json_decode) | quote(template), outcome: none(...) | err(...)}`
  for structured failure. Template mismatch remains the nested `none`; decode
  or Template error remains the nested `err`.

Runtime misuse covers malformed public values, non-callable Templates, invalid
config, forged/mismatched capabilities, protected request fields, unsupported
host values, and callback contract violations. It occurs before an attempt when
locally detectable and is not converted into a model Outcome.

Failures end that invocation. Automatic retry, backoff, jitter, failover,
queueing, and rate-limit sleeping do not occur. R11 adds no retry helper and
makes no idempotency guarantee.

## R9 structured-output composition

R11 creates no AI schema or validator:

- schemas use one outer R9 `json` representation;
- compilation uses existing `json_schema`;
- response decoding uses existing `json_decode`;
- compatibility uses the explicit callable Template;
- existing `some`, `none`, `err`, JSON number, Unicode, duplicate-name,
  nesting, and unsupported-keyword rules remain unchanged.

No coercion, repair, second parse, prose extraction, Markdown-fence stripping,
or automatic reprompt occurs. Invalid structured output is one normalized
error from one attempt.

## R10 protected-credential composition

Model identity/timeout are explicitly acquired as ordinary values, normally
through `config_get`/`config_get_or` and existing converters/Templates. The
credential is explicitly acquired through `secret_get` with purpose
`quote(model_call)`. There is no environment lookup, default credential,
provider discovery, annotation injection, or ambient configuration.

The model captures the protected value and matching authority, never the
declassified string. Each invocation declassifies only after validation and
immediately before its one authorized attempt. Existing R10 audit behavior
records the attempt without key or payload.

On validation, authority, or declassification failure, no provider is called.
R10 recursive redaction/rejection applies to every path. The ordinary credential
may exist only in a private host adapter request immediately before transmission;
that request is never ordinary Genia data, logged, returned, retried, or retained.

R11 does not broaden `declassify`, weaken protected host-call rejection, add
arbitrary reveal callbacks, or claim memory erasure.

## Provider and host boundary

| Concern | Portable contract | Host/Python proof |
|---|---|---|
| provider selection | explicit opaque capability | harness injects one capability |
| identity/timeout | exact config map | adapter maps to provider protocol |
| request/response | exact shapes/normalization | SDK/HTTP objects remain private |
| credential | R10 protected value/authority | just-in-time declassification |
| execution | one synchronous finite attempt | Python deadline/cleanup |
| errors | exact Outcomes | provider details removed |
| testing | deterministic fixture observations | no network or sleeping |

The release proof implements one Python provider-specific adapter. Its SDK,
endpoint, headers, wire JSON, authentication convention, request IDs, and error
types are not Genia semantics. It may use host HTTP internally, but R11 exposes
no general networking capability and changes no current HTTP/server behavior.

Model-provider capabilities differ from R10 configuration providers: one
performs a model protocol attempt; the other snapshots key/value sources.
Neither is ambient or substitutes for the other.

## Streaming, cancellation, timeout, retry, and rate limits

| Concern | R11 decision |
|---|---|
| synchronous call | included; one call returns one Outcome |
| streaming | excluded; no token/event Flow or partial response |
| cancellation | excluded at model-call level; no handle/token/API |
| timeout | required config, `1..300000` ms; normalized timeout error |
| retry/backoff | excluded; zero automatic retries |
| rate limit | normalized error; optional delay is data only |
| fallback/racing | excluded |

External Flow termination prevents future calls but does not cancel an already
running synchronous call.

## Conversation and Flow

Conversation owns state evolution, not input acquisition. Terminal, fixture,
file, HTTP, actor/message, generated, or future producers may feed the same
logic only by producing exact events through a list or Flow. R11 changes none
of those producers.

Conversation input is exactly:

```text
{kind: quote(message), message: {role: quote(user), content: content}}
{kind: quote(stop), reason: string}
```

Conversation state is exactly:

```text
{
  messages: [message, ...],
  turn: non_negative_integer,
  status: quote(active) | quote(stopped) | quote(failed),
  last: none("conversation-not-started")
      | none("conversation-stopped", {reason: string})
      | some(response)
      | none("model-no-response")
      | err(model_reason, model_context)
}
```

Initial state is exactly:

```text
{messages: [], turn: 0, status: quote(active), last: none("conversation-not-started")}
```

An application-defined `conversation_step(model, prompt, state, input)` uses
the ordinary `prompt(messages) -> request` function and returns
`[next_state, next_state]` for existing `scan`:

- active + message: append the user message, pass all ordered messages to
  `prompt`, call the model with that request, increment `turn` once, set `last`,
  and append the assistant message only on `some(response)`;
- success keeps status active; model `none`/`err` sets status failed;
- active + stop sets status stopped and `conversation-stopped` without a model
  call or turn increment;
- stopped/failed + later input returns `[state, state]` unchanged and makes no
  call.

Composition is `scan(step, initial_state, source)`. List input returns list;
Flow input returns lazy single-use Flow. Each consumed input emits one state in
order; `scan` does not emit the initial state before the first input.

Termination is external source completion, existing downstream bounded
finalization, or a terminal state making later inputs inert. R11 adds no
`take_while`, `take_some_while`, hidden loop, terminal prompt, cancellation, or
conversation runtime. Producers own blocking/read behavior.

## Deterministic testing and portability

A deterministic fixture capability is mandatory before provider networking:

- injected by the harness; zero network, clock, randomness, environment,
  filesystem, or sleep access;
- returns a configured response/failure for each exact request;
- attempt count and declassification audit are host-test instrumentation only;
- deterministic matching/output order;
- shared by eval, flow, error, and CLI observations.

Future shared specs cover:

- eval: validation, minimal invocation, normalization, absence/errors, R9 output;
- flow: source-independent state sequences, laziness, terminal no-call behavior;
- error: malformed shapes/capabilities/protected request fields and diagnostics;
- CLI: stdout/stderr/exit using injected fixtures;
- parse/IR: regression proof using existing ordinary forms/nodes only.

Python tests cover opaque capabilities, adapter mapping, timeout cleanup, one
attempt/zero retries, error translation, declassification timing/audit, request
disposal, and recursive leak scanning.

Generated sentinel credentials and keys live only in the host test harness.
Captured stdout, stderr, exceptions, Outcomes, diagnostics, rendering, reports,
provider requests/responses, audit events, resources, HTTP buffers, and test
output must each exclude both sentinels.

The composability matrix gains planned model/function/pipeline, R9 output, R10
credential, and Flow conversation rows. This contract adds no family builtin.

## Core and portability decisions

| Area | Decision |
|---|---|
| syntax/annotations | none |
| parser/AST/Core IR | existing nodes only |
| values | ordinary closed values and Outcomes |
| public functions | only `model/4`; returned model is callable |
| provider | explicit opaque capability; no class/registry/global |
| prompt/chain | ordinary functions and pipelines |
| structured output | R9 JSON/schema/Template |
| credential | R10 protection/declassification/audit |
| conversation | application function over existing `scan` |
| tools | deferred; no shape/executor |
| lifecycle | none; existing annotation behavior unchanged |
| Python-only | handles, adapter, SDK/HTTP/deadline mechanics |

Future hosts may vary internal libraries/storage but must preserve exact shapes,
one-attempt synchronous Outcomes, timeout/no-retry rules, R9/R10 composition,
and deterministic fixture behavior. No non-Python host is claimed.

## Proving cases

### Minimal invocation

```text
explicit capability/config/protected credential/authority
  -> model(...)
  -> closed text request
  -> some(closed text response)
```

### Structured output

```text
json schema -> json_schema -> Person Template
  -> one fixture response -> json_decode -> Person
  -> some(response retaining one json facet)
```

### Flow conversation

```text
fixture/list/Flow producer
  -> scan(conversation_step(model), initial_state)
  -> identical ordered states for identical inputs
```

### Validated pipeline

```text
messy JSONL -> parse/validate_each -> prompt -> model -> R9 validation
  -> collect_validated -> clean shaped values + normalized diagnostics
```

The proof includes malformed input, model absence/failure, and invalid
structured output without leaking fixture key/credential.

## R11/R12 boundary and non-goals

R11 includes only text/JSON invocation, normalized ordinary values, R9/R10
composition, source-independent `scan` conversation composition, and the
validated-pipeline proof.

R11 excludes retrieval, documents/chunks/provenance, embeddings, vector/lexical
indexes, search, reranking, grounding, evidence, citations, vector stores, and
RAG. Those remain R12 planning.

R11 also excludes tools, agents, streaming, cancellation, retry/backoff/fallback,
batching, multimodal content, fine-tuning, model discovery, cost accounting,
caching, persistent memory, and general AI observability/evaluation systems.

## Reconciled R11 sequence

Issue #607 recorded the contract GO; each later issue still requires its own
phase gates.

1. **E11-1 — ordinary values, `model/4`, deterministic fixture (implemented):**
   validators, callable behavior, one-attempt Outcomes, no network.
2. **E11-2 — R9 structured output (implemented):** schema/Template request,
   strict decode, response/failure normalization.
3. **E11-3 — R10 boundary and one Python provider adapter:** explicit
   capability, purpose, just-in-time declassification, timeout, mapping, audit,
   and leak scans.
4. **E11-4 — conformance/cross-mode hardening:** eval/flow/error/CLI plus
   parse/IR regression and import/test/serve non-ambient proof.
5. **E11-5 — Flow conversation:** list/Flow equivalence, terminal behavior,
   source independence.
6. **E11-6 — validated-pipeline proving case.**
7. **E11-7 — release examples and truth sync:** implemented-behavior docs and
   `docs/releases/R11.md` runnable examples.
8. **E11-8 — final truth audit and distillation.**

Each behavior issue runs its own phase workflow. Failing tests precede
implementation. E11-7 reconciles implemented slices; docs never lead behavior.

## Gate

Issue #607 recorded explicit approval; issues #611/#612 delivered E11-1/E11-2. Later
behavior slices still require their own tickets and phase gates; this document
does not authorize E11-3 or later implementation.
