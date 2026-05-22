# Ada Language Ideas

Status: Parking lot / non-authoritative

This note captures future ideas only. It does not define implemented Genia behavior.
If this conflicts with `GENIA_STATE.md`, `GENIA_STATE.md` wins.

## Why this is parked

Ada has useful correctness and boundary-design ideas, but most of them should not become active Genia scope until they directly support the first killer workflow: Outcome-aware validated data pipelines.

Near-term Genia work should stay focused on:

```text
messy records in → clear pipelines → validated shaped output / reports + useful diagnostics
```

Ada-inspired ideas are most relevant when they strengthen validation, contracts, value templates, opaque resource boundaries, or later lifecycle/concurrency work.

## Ideas worth revisiting

### 1. Subtypes and predicates → refinement templates

Ada-style constrained subtypes and predicates map well to Genia refinement templates.

Potential Genia direction:

```text
Natural      = n where n >= 0
PortNumber   = n where n >= 1 and n <= 65535
NonEmptyText = s where length(s) > 0
IsoDateText  = s where matches(s, "\\d{4}-\\d{2}-\\d{2}")
```

Why it matters:

- strengthens value-template roadmap
- supports record validation
- makes field constraints explicit
- can produce better diagnostics for messy data

Parking-lot caution:

- do not add new syntax until the refinement-template contract is approved
- avoid implying static guarantees before they exist

### 2. Preconditions, postconditions, and invariants → runtime contracts first

Ada/SPARK-style contracts are useful as a discipline model.

Potential Genia direction:

```text
validate_record(patient_contract, row)
normalize_age :: ValidAge -> ValidAge
```

Useful staged path:

1. runtime contracts
2. contract-aware diagnostics
3. lightweight static checks
4. optional proof/verification experiments much later

Why it matters:

- strengthens boundary guarantees
- supports validation-heavy pipeline workflows
- improves diagnostics

Parking-lot caution:

- do not introduce a heavy static type system prematurely
- contracts should compose with Outcome rather than replace it

### 3. Package spec/body split → module public contracts

Ada's split between public package specs and private implementation suggests a future Genia module direction:

```text
module interface = public contract
module body      = implementation
```

Potential Genia direction:

```text
import db          -> module definition / namespace
init(db, config)   -> module instance
start(instance)    -> lifecycle activation
stop(instance)     -> lifecycle cleanup
```

Why it matters:

- clarifies public module boundaries
- supports module instances later
- prevents implementation details from leaking

Parking-lot caution:

- do not overload current import behavior
- do not make import run lifecycle hooks

### 4. Private types → opaque resource values

Ada private types suggest a future model for opaque Genia values whose representation is hidden.

Candidate opaque values:

```text
FileHandle
HttpServer
DbConnection
FlowSource
ModuleInstance
ActorRef
```

Why it matters:

- protects host-backed resources
- supports lifecycle safety
- keeps multi-host behavior cleaner

Parking-lot caution:

- avoid turning ordinary maps into pseudo-objects
- keep resource semantics explicit and testable

### 5. Range-constrained numerics → better field validation

Ada's constrained numeric ranges fit Genia's data-validation story.

Potential Genia direction:

```text
Percent  = n where n >= 0 and n <= 100
ValidAge = n where n >= 0 and n <= 130
LabValue = n where n >= 0
```

Why it matters:

- excellent fit for validated records and Sheet columns
- gives useful per-field diagnostics
- supports contracts and refinements without broad type-system expansion

### 6. Tasking and protected objects → actors/cells later

Ada tasking and protected objects are useful as conceptual inspiration for future Genia concurrency.

Potential Genia mapping:

```text
cell  = serialized protected state
actor = active message-driven process with private state
```

Why it matters:

- reinforces a clean distinction between active processes and protected state
- may inform future actor and lifecycle design

Parking-lot caution:

- not part of the first killer workflow
- do not copy Ada task syntax
- do not promise scheduler semantics before the runtime supports them

### 7. Restrictions/profiles → capability and purity profiles

Ada restriction profiles suggest future Genia profiles for constrained execution contexts.

Potential Genia direction:

```text
profile(data_pipeline)
profile(pure_formula)
profile(portable_core)
profile(no_host_io)
```

Useful future constraints:

```text
No host IO
No mutation
No random
No clock
No hidden resource access
```

Why it matters:

- useful for Sheet formula plans
- useful for portable-core validation
- may support future optimization and auditability

Parking-lot caution:

- do not introduce profiles until there is a concrete use case
- avoid pragma/aspect sprawl

## Ideas not to borrow directly

Do not copy Ada's:

- verbose syntax
- heavy declaration ceremony
- broad pragma/aspect culture
- complex access/pointer model
- full tasking model early
- exception-heavy control flow
- generic package complexity

## Priority if promoted later

If these ideas are promoted into active work, likely order:

1. Refinement templates for validated data
2. Runtime contracts and diagnostics
3. Opaque resource values for host-backed resources
4. Module public contracts and module instances
5. Capability/purity profiles for Sheets/formula plans
6. Protected-state and actor lessons for future concurrency
7. Optional proof/static-analysis experiments

## Promotion trigger

Promote an Ada-inspired idea only when it clearly supports one of these:

- Outcome-aware record validation
- clearer diagnostics
- value-template contracts/refinements/shapes
- safer host-backed resources
- Sheet formula purity or shape validation
- explicit lifecycle or actor work that has already been approved

Until then, keep these ideas parked.
