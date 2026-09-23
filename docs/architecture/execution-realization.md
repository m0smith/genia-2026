# Logical Computation and Execution Realization

Status: **Architectural direction — non-authoritative and not implemented.**

This document records constraints for future Genia design. It does not define
current language behavior. `GENIA_STATE.md` remains final authority.

Capability **provisioning** is a separate concern: it combines declared host
support with policy to supply authority to a program. It must not be conflated
with execution realization. See [Host Capability Taxonomy](host-capability-taxonomy.md)
and the planned [External Process Execution Architecture](external-process-execution.md).

## Principle

Genia is intended to describe the logical computation of a system independently
from the physical realization used to execute that computation.

A Genia program should describe:

- values and transformations
- Flow / Seq processing
- pattern and Outcome semantics
- explicit capabilities
- lifecycle relationships
- logical sources, sinks, and work boundaries when such abstractions exist

A physical realization may later decide:

- in-process vs multi-process execution
- local vs remote placement
- scheduling and worker count
- in-memory vs durable transport
- queue or broker implementation
- infrastructure provider
- deployment mechanism

The long-term design objective is:

> A computation that is valid locally should not require its business logic to be
> rewritten merely because its physical execution is later distributed.

This is a design objective, not a promise that every local value or operation can
be transparently distributed.

## Three Layers

Future designs should keep these concerns separate:

1. **Logical computation**
   - what the Genia program means
2. **Execution realization**
   - where and under what execution topology that computation runs
3. **Infrastructure realization**
   - which processes, queues, brokers, machines, clouds, provisioning systems,
     or other physical mechanisms provide the required capabilities

Dependencies should flow downward:

```text
logical Genia computation
        |
        v
execution realization
        |
        v
host / transport / infrastructure capabilities
```

Infrastructure details must not become the definition of Genia semantics.

## Composition as Inspectable Structure

Logical composition should remain distinct from execution realization.

Ordinary Genia pipelines must stay lightweight and preserve their existing value,
Flow/Seq, Outcome, and lifecycle semantics. Future designs may additionally need
an **inspectable representation of composition** when tooling, placement,
parallelism, tracing, actors, or distributed execution require reasoning about
the work before it runs.

The architectural direction is:

```text
pipeline / ordinary composition
        |
        v
logical composition structure, when explicitly materialized
        |
        v
execution realization
```

This does **not** mean every `|>` expression becomes a heavyweight workflow
graph or runtime object. Materialization must be explicit or otherwise narrowly
defined by a future contract.

Future composition participants should satisfy small semantic contracts rather
than inherit from a host-language base class. A participant may be an ordinary
callable, Flow/Seq transformation, validation step, model operation, future
execution unit, or future actor-facing stage when its contract permits.

Sequential composition and future fan-out/fan-in should preserve existing Genia
abstractions:

- `|>` remains the canonical pipeline syntax; do not introduce a second pipe
  merely to model executable graphs.
- ordinary maps/lists remain ordinary values; appearing after a pipeline stage
  must not implicitly make a map mean parallel execution.
- fan-out or parallel composition, if promoted, must be explicit and must define
  result ordering, failure/Outcome behavior, bounded demand, cancellation,
  lifecycle ownership, and placement requirements.
- Flow/Seq remains the ordered-stream abstraction rather than being replaced by
  a graph-stream type.
- Outcome remains the value-level presence/absence/failure model rather than
  being replaced by graph-specific result wrappers.
- R14 lifecycle remains the surrounding resource/cleanup model rather than
  callbacks or tracing hooks becoming a second lifecycle system.
- provider placement or transport must not change the logical business
  transformation merely because a stage runs locally, in another process, on a
  worker, or through a future actor provider.
- Core IR/shared contracts remain the portability boundary; Python/C++/future
  hosts must not invent different composition semantics.

The motivating lesson from systems that model executable chains as reusable
objects is not operator overloading. It is that **computation can be represented
as composable structure so execution policy can vary independently**.

That structure may later support inspection and tooling questions such as:

- what stages exist and in what dependency order?
- what values/templates each stage consumes or produces?
- where Outcomes, capabilities, effects, or lifecycle scopes appear?
- which independent branches may run concurrently?
- which stages require order or bounded demand?
- which work may cross a process/provider boundary?
- which actor/event/execution adapters participate without changing the logical
  computation?

Any such introspection remains future work until explicitly contracted.

## Semantic Transparency, Not Infrastructure Transparency

Genia must not pretend unlike systems are identical.

A local List, an in-memory work queue, AWS SQS, Kafka, and another transport may
all be usable for related purposes, but they do not inherently have identical
semantics.

Relevant differences can include:

- ordering
- replayability
- durability
- acknowledgment
- delivery cardinality
- duplicate delivery
- partitioning
- backpressure
- retry behavior
- latency
- failure modes

Future abstractions must describe the semantic guarantees required by the
program rather than hiding these differences behind one misleading universal
interface.

A realization is valid only when it can satisfy the semantics required by the
logical computation.

## Placement May Be Hidden; Failure Semantics Must Not Be

Future Genia execution may hide physical placement where useful.

It must not hide semantic differences caused by distribution.

In particular, distributed execution may introduce:

- retries
- duplicate work
- partial failure
- unavailable workers
- network partitions
- delayed delivery
- reordered independent work

These conditions must remain observable where they affect program correctness.

Genia must not adopt the fiction that a remote operation is merely a local call
executing somewhere else.

## Portable Values and Host-Local Values

Future distributed execution will require a distinction between values that can
cross an execution boundary and values that are meaningful only inside one host
or process.

Designs should therefore avoid assuming that arbitrary host objects, resource
handles, closures, streams, open files, connections, or other opaque runtime
objects can be moved between realizations.

Do not add such a distinction to the language until concrete work requires it,
but do not design new abstractions in ways that make the distinction impossible.

## Effects and Distribution

Pure value transformations are naturally portable.

External effects are not.

Any future distributed execution model must explicitly address operations such
as:

- network writes
- database updates
- filesystem changes
- message publication
- external API calls

At-least-once execution, retries, and uncertain completion can make these effects
observable more than once.

Genia must not imply exactly-once effects merely because local execution appears
to execute once.

## Local Development

A future execution realization may allow the same logical program to run using
local substitutes for remote capabilities.

Examples might include:

```text
development realization
  source -> local collection or local queue
  workers -> local process
  storage -> local implementation

production realization
  source -> durable broker
  workers -> distributed processes
  storage -> remote durable implementation
```

Such substitutions must preserve the semantic contract claimed by the
realization.

A local test realization may eventually emulate distributed behaviors such as
duplicate delivery, retries, failure, or reordering where those behaviors are
part of the production contract.

## Infrastructure Tools

Genia must not require a particular infrastructure provisioning system.

An execution realization might eventually be materialized through:

- Ansible
- Terraform
- Kubernetes
- cloud-native deployment APIs
- another provisioning system

Those are infrastructure mechanisms, not Genia language semantics.

The dependency direction should remain:

```text
Genia declares requirements
deployment tooling realizes requirements
```

not:

```text
deployment tooling defines Genia semantics
```

## Relationship to Host Portability

Host portability and execution realization are separate concerns.

Host portability asks:

> Can Python, C++, or another host execute the same Genia semantics?

Execution realization asks:

> Can one logical Genia computation be placed and transported differently while
> preserving its required semantics?

A host may support Genia without supporting distributed execution.

A distributed realization may involve one host or several conforming hosts.

Do not conflate the two concepts.

## Current Design Guardrails

Until distributed execution is explicitly promoted into a release:

- do not add distributed execution semantics
- do not add queue/broker syntax
- do not promise transparent remoting
- do not make AWS, Kafka, Ansible, Kubernetes, or another platform part of the
  language contract
- do not make Flow require network distribution
- do not make Flow assume all sources live in memory
- do not make lifecycle assume all scopes live in one process unless that is
  genuinely required by the implemented contract
- keep host capabilities explicit and narrow
- keep portable Core IR free of infrastructure-specific concepts
- keep logical operations independent of provisioning details where practical

When forced to choose between two otherwise equivalent designs, prefer the one
that preserves these separations without adding current complexity.

## Promotion Rule

This architecture direction must remain dormant until a concrete use case proves
the need for implementation.

Before promotion, require a design that explicitly answers:

1. Which semantic source/work/transport contract is needed?
2. Which guarantees are required: ordering, durability, delivery cardinality,
   acknowledgement, replay, partitioning, or others?
3. Which values may cross the execution boundary?
4. How are effects and retries handled?
5. What failures become observable?
6. How is the same logical computation exercised locally?
7. What remains host-neutral?
8. What remains infrastructure-specific?

Only after those questions are answered should implementation work be scheduled.
