# Unified Events and Subscriptions — Design Survey

Status: Architecture survey and roadmap input — non-authoritative. `GENIA_STATE.md` remains final authority for implemented behavior.

## Question

Genia has several domains that need to expose facts over time: state changes, Flow execution, lifecycle scope/element activity, execution handles, resource watches, actors/messages, logging/metrics/debugging, and future distributed transports. The design question is whether these should grow separate callback/watch/listener APIs or share one small semantic model.

This survey recommends one shared **event/subscription semantic spine**, while preserving the distinction between events, state, Flow, lifecycle, actors, and durable messaging.

## Existing Genia constraints

The design must reuse rather than replace existing foundations:

- R14 already owns deterministic lifecycle scope entry/unwind and repeated per-element scopes.
- Flow is the existing sequence-over-time abstraction and is lazy, pull-based, and single-use today.
- Outcome remains the ordinary success/absence/failure boundary; events must not create a second error system.
- Import/load remains inert. Merely defining or importing an event source must not activate listeners, processes, network IO, or lifecycle scopes.
- Portable application semantics must not branch on host/provider identity.
- Future Store/Execution providers must keep transport mechanics and credentials below portable boundaries.
- Event observation must not silently alter the behavior of the observed operation.

## Survey

### Erlang/OTP

OTP's `gen_event` uses an event-manager process with dynamically installed handlers. Handlers have explicit initialization/termination and can be supervised. A failing handler can be removed without failing the other handlers. This is strong evidence for explicit subscription lifetime and failure isolation, but Genia should not copy a central event-manager process as the universal abstraction: it would introduce a second concurrency/control model beside Flow, lifecycle, and future actors.

Useful lesson: **subscription lifetime and subscriber failure are first-class semantics**.

### Reactive Streams / JDK Flow

Reactive Streams deliberately standardizes a minimal Publisher/Subscriber/Subscription protocol around asynchronous streams and non-blocking backpressure. A subscription carries demand and cancellation; completion and error are terminal signals. This is the strongest model for Genia's pressure problem because it makes bounded demand part of the contract instead of an implementation detail.

Useful lesson: **a subscriber must not imply unbounded buffering; demand, cancellation, completion, and failure belong in the stream contract**.

### Clojure core.async

`mult` and `pub` demonstrate explicit fan-out and topic partitioning over channels. Their default fan-out is synchronous: a slow tap/subscriber can hold up subsequent distribution unless buffering/windowing is chosen. Items with no matching subscribers can be dropped.

Useful lesson: **fan-out policy and slow-subscriber policy are observable semantics and cannot be hand-waved**. Genia should not silently inherit "slowest subscriber wins" or "drop when nobody listens."

### ReactiveX

ReactiveX distinguishes hot observables, which may emit independently of subscription, from cold observables, which begin per subscription. This distinction is essential for state-change notifications and external event sources: a live watch and a replayable/history-backed source are not the same thing.

Useful lesson: **live versus replayable/history-backed subscription must be explicit**.

### Kafka

Kafka separates publish durability from consume/process delivery guarantees, provides ordering within a partition rather than universal total ordering, and uses consumer groups to distinguish broadcast from load-balanced consumption.

Useful lesson: **ordering scope, durability, replay, acknowledgement, and fan-out/load-balancing are separate dimensions**. Genia must not use a single word such as "subscribe" to imply all of them.

### AWS SQS and Lambda

SQS makes an especially useful counterpoint to Kafka. Receiving a message does not mean the work is complete: delivery has a visibility interval, successful processing normally leads to deletion, and failure or timeout can make the message available for redelivery. Lambda event-source mappings add another realization: AWS owns the poller and invokes bounded batches of work rather than exposing the queue consumer loop directly to application code.

Useful lesson: **the semantic fact and one consumer's delivery of that fact are different things**. Receipt handles, visibility/deadline state, acknowledgement/deletion, retry/redelivery, batch identity, and dead-letter behavior belong to delivery/provider semantics rather than the portable Event value. Execution placement is also separate: the same logical subscription may be consumed by an in-process Flow worker, a Genia execution worker, or a Lambda-style provider-managed worker without redefining the event payload.

### DOM EventTarget

DOM EventTarget is intentionally simple: subscribe by string event type and invoke listeners. Its simplicity is attractive for UI/event callbacks, but stringly typed event names and callback-driven control do not fit Genia's pattern/value orientation or Flow composition.

Useful lesson: **keep registration simple, but prefer ordinary values plus pattern matching over a parallel string-topic type system**.

## Proposed Genia model

The smallest coherent model is:

```text
Event        = an immutable ordinary Genia value describing a fact
Delivery     = one provider/source delivery of an event, when delivery semantics exist
EventSource  = an explicit value/capability that can produce events
Subscription = the owned relationship between one source and one consumer
EventStream  = Flow<Event> for the simple/live baseline
Lifecycle    = owns acquisition and release of subscription resources
```

The central candidate invariant is:

> **A subscription is observed as a Flow of ordinary event values.**

Candidate conceptual surface, deliberately not syntax-approved:

```genia
events = subscribe(source, pattern)
events
  |> filter(...)
  |> map(...)
  |> take(100)
```

`subscribe` should not create a second EventStream collection type if existing Flow can carry the semantics. The contract must first determine whether today's pull-only Flow can represent live event demand directly or whether a provider adapter needs a bounded bridge beneath Flow.

The contract must also settle an **Event versus Delivery** boundary before durable providers are designed. `Event` is the portable semantic fact. `Delivery` is a candidate provider-facing/portable-capability value for one consumer's receipt of that fact when acknowledgement, progress, lease/visibility, replay position, or redelivery semantics exist. The simple local baseline should remain `Flow<Event>` unless the contract proves that a delivery wrapper is necessary there; durable providers must not contaminate every ordinary event with Kafka offsets, SQS receipt handles, or equivalent transport metadata.

## Event shape

Events should be ordinary immutable Genia values. A small common envelope may be useful, but domain payloads should remain domain-owned rather than forcing one giant universal record.

Candidate conceptual examples:

```text
state_changed
flow_element_started
flow_element_completed
flow_element_failed
flow_completed
flow_failed
scope_entered
scope_exited
resource_changed
execution_started
execution_finished
actor_started
message_received
message_sent
```

Patterns should select event values using Genia's existing pattern machinery where possible. Do not create a string-topic DSL merely to reproduce functionality already available through values and patterns.

## Boundaries that must remain distinct

### State is not an event log

State answers "what is true now." An event answers "what happened." A state API may expose current state and separately expose a live change subscription. R39 must not require event sourcing.

### Flow is not Event

Flow is a sequence abstraction. Event is a semantic fact. A Flow may carry events, but ordinary Flow elements do not become events merely by flowing.

### Events are observation, not hidden control flow

Instrumentation subscribers must not change the source operation's semantic result merely because they exist. Control flow remains explicit through ordinary calls, Flow, Outcome, lifecycle, open dispatch, and future actor/execution contracts.

### Event is not Delivery

An Event describes what happened. A Delivery describes how a particular consumer received that event. Kafka partition/offset/progress and SQS receipt-handle/visibility/delete semantics are delivery concerns, not universal event fields. R39 should preserve this distinction so local events remain simple while durable providers can expose stronger capabilities honestly.

This is a contract question, not approved syntax. A future durable source might conceptually expose a delivery-bearing Flow while a simple live source remains `Flow<Event>`. The design must avoid both extremes: forcing delivery machinery onto every event, or hiding acknowledgement/progress so thoroughly that reliable processing becomes impossible to express.

### Pub/sub is not durable messaging by default

A local live subscription, a broker-backed durable stream, an actor mailbox, and a replayable event log have different guarantees. R39 should define a portable baseline and explicit capability/option dimensions rather than pretending these transports are interchangeable.

## Lifecycle integration

Subscriptions that acquire resources should be lifecycle-owned. The intended invariant is:

> Entering the owning scope may acquire the subscription; leaving, failing, or cancelling the scope releases it deterministically.

R14's per-element scopes also provide a natural instrumentation boundary for optional element-level events. This must be observational: emitting or consuming instrumentation events must not mutate lexical state or alter element-scope parentage/unwind rules.

## Delivery semantic matrix to settle in contract

| Dimension | Baseline direction |
|---|---|
| Event value | ordinary immutable Genia value |
| Selection | existing pattern/value machinery where sufficient |
| Consumption | Flow of events |
| Subscription lifetime | explicit; lifecycle-owned when resources are acquired |
| Backpressure | bounded/demand-aware; no implicit unbounded queue |
| Cancellation | explicit and deterministic at the portable boundary |
| Completion/failure | aligned with Flow terminal semantics; no per-element Outcome wrapping solely for transport |
| Ordering | only within an explicitly documented source/order domain; no global total-order promise |
| Live vs replay | explicit; portable baseline should not imply replay |
| Durability | explicit provider capability; not implied by EventSource |
| Acknowledgement | only where a durable provider contract requires it; belongs to Delivery/provider semantics, not Event |
| Fan-out | explicit broadcast vs competing-consumer semantics; do not conflate them |
| Subscriber failure | must not silently corrupt the publisher or unrelated subscribers |
| No subscribers | contract must say whether events are dropped, retained by a durable source, or source-specific |
| Delivery metadata | provider/source-specific progress/lease/receipt metadata must not pollute the portable Event value |
| Execution realization | consumption may be in-process, Genia-execution-backed, or provider-managed (for example Lambda-style); placement must not redefine Event semantics |
| Distribution | same portable event values/subscription shape where guarantees are compatible; provider mechanics stay below boundary |
| Import behavior | inert; no subscription or IO on import/load |

## Recommended portable baseline

The first contract should be intentionally smaller than Kafka, NATS, or an actor system:

1. ordinary immutable event values;
2. explicit EventSource;
3. explicit subscription producing a Flow;
4. explicit cancellation/cleanup tied to lifecycle ownership;
5. bounded demand/backpressure behavior;
6. source-scoped ordering only;
7. live-only baseline with no durability/replay promise;
8. observer failure isolation;
9. no ambient global event bus;
10. no implicit retry, acknowledgement, persistence, distributed broker, or event-sourcing semantics.

Durable/replayable providers can later add capabilities without changing application-level event values. If a provider cannot preserve the portable baseline, incompatibility must be explicit rather than approximated silently.

## Provider realization sketches

These are architecture checks, not R39 implementation commitments.

- **Kafka:** topic/partition records can become ordinary Event payloads; consumer-group membership, partition assignment, offset/progress, replay position, and acknowledgement/commit behavior remain subscription/delivery capabilities. Genia must not silently invent a consumer group or promise global ordering.
- **SQS:** message payloads can become ordinary Event payloads; receipt handles, visibility/deadline, deletion acknowledgement, redelivery, batching, and dead-letter behavior remain delivery/provider concerns.
- **SQS → Lambda-style execution:** the provider may own polling and invoke bounded batches. Genia's application-level transformation/validation logic should remain transport-independent where practical; execution placement and batch invocation belong below the event value boundary and should reuse R36 execution concepts when that release exists.
- **Local source:** remains the proving baseline and should not pay for durable-delivery machinery it does not need.

A useful scale-up target is therefore: the same Genia record-processing logic can begin over a local Flow, later consume events from Kafka or SQS, and potentially run under provider-managed execution such as Lambda without rewriting domain transformations merely to accommodate transport identity. This is an architectural direction, not a claim of current portability or implementation.

## Why not a global event bus?

A global bus is convenient initially but conflicts with Genia's explicit authority/lifecycle direction. It hides ownership, makes import-time activation tempting, makes tests order-sensitive, and makes distributed realization ambiguous. Explicit sources compose better with R10/R13 authority, R14 lifecycle ownership, R35 Store authority, and R36 Execution placement.

## Relationship to future actors

Actors should be able to expose lifecycle/monitoring/message-observation events through the same event spine, but actor mailboxes are not merely subscriptions. Actor identity, supervision, request/reply, mailbox semantics, and failure propagation remain actor-system concerns.

R39 should therefore precede or inform actor-system promotion, without absorbing the actor system itself.

## Roadmap recommendation

Promote this architecture as **R39 — Unified Events and Subscriptions**.

R39 can be designed after the already-complete R14 lifecycle foundation and current Flow semantics. Its first portable/local contract does not need R35/R36 to exist, but later resource watches and distributed event providers should reuse R35/R36 rather than inventing transport-specific identities or placement rules.

Suggested gated slices:

- **E39-0 — Contract:** event/delivery/source/subscription identities, lifetime, demand, terminal behavior, ordering scope, live/replay boundary, acknowledgement/progress boundary, failure isolation, and non-goals.
- **E39-1 — Ordinary event values and local source:** no network, broker, actor, or persistence.
- **E39-2 — Flow subscription bridge:** prove bounded demand, cancellation, no over-pull, and terminal behavior.
- **E39-3 — Lifecycle ownership:** deterministic acquire/release and failure cleanup using R14.
- **E39-4 — State-change proving case:** current-state read remains separate from change observation.
- **E39-5 — Flow/lifecycle instrumentation proving case:** observational only; no semantic change when no subscriber exists.
- **E39-6 — Cross-cutting hardening:** subscriber failure isolation, multiple subscribers, no-subscriber behavior, protected-value non-leakage, import inertness, cross-mode checks.
- **E39-7 — Provider-readiness proof:** document capability dimensions and semantic mappings for at least Kafka and SQS, including provider-managed SQS→Lambda-style consumption, without implementing a broker/cloud adapter.
- **E39-8 — Documentation/truth audit and distillation.**

## Explicit non-goals for R39

- actor system or mailbox semantics;
- event sourcing;
- durable event log;
- Kafka/NATS/SQS implementation or Lambda runtime integration;
- exactly-once processing claims;
- global total ordering;
- implicit retries;
- distributed consensus;
- replacing Flow with a reactive-streams API;
- a second lifecycle system;
- ambient global event bus;
- string-topic DSL when ordinary patterns suffice;
- automatic state mutation from event observation.

## Regret checks

Before contract approval, reject a design if it:

- requires every Flow item to become an Event;
- makes state reconstructable only through event replay;
- permits unbounded buffering by default;
- makes one slow subscriber silently stall unrelated subscribers without an explicit policy;
- lets subscriber failure alter publisher results by default;
- activates subscriptions during import;
- encodes provider/broker identity into portable application logic;
- puts Kafka offsets, SQS receipt handles, visibility leases, or equivalent provider delivery metadata into the universal Event shape;
- conflates receiving an Event with successfully acknowledging/completing its Delivery;
- promises ordering, replay, durability, or exactly-once semantics that a local and distributed provider cannot both prove;
- duplicates R14 lifecycle ownership, Flow transformations, Outcome failure semantics, or R20 pattern dispatch.

## Sources surveyed

External systems were used only as design evidence; they do not define Genia behavior. Genia behavior remains governed by the repository source-of-truth hierarchy.
