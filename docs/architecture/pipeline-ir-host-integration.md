# Pipeline / Core IR / Host Interop integration

## Old model

- pipelines started as call-rewriting sugar
- Option-aware chaining depended heavily on helper functions such as `then_get` and `map_some`
- host interop risked looking like a separate convenience layer instead of part of one shared semantic model

## Integrated model

- `|>` lowers into explicit Core IR as `IrPipeline(source, stages)`
- pipeline evaluation owns automatic Option propagation:
  - `some(x)` unwraps to `x` for the next stage
  - `none(...)` short-circuits the rest of the pipeline unchanged
- Flow is still explicit:
  - Flow values use the same pipeline syntax
  - Value↔Flow crossing still happens only through explicit Flow helpers
- host interop is a narrow capability bridge:
  - host exports are ordinary callable/module exports
  - host `None` becomes Genia `none`
  - host exceptions remain explicit errors

## Where semantics live

- parser/lowering:
  - preserve explicit pipeline structure and explicit Option constructors in Core IR
- Core IR:
  - is the portability boundary for the shared meaning of pipelines and Option values
- evaluator/runtime:
  - executes pipeline stages
  - enforces automatic Option propagation
  - keeps Flow runtime mechanics explicit and host-backed
- prelude:
  - provides the public helper surface and composition helpers
  - keeps helper-heavy Option code available where explicit Option manipulation is still the right tool
- host bridge:
  - handles capability access and boundary conversion
  - does not redefine pipeline or Option semantics

## Write code like this now

```genia
unwrap_or("unknown", record |> get("user") |> get("name"))
```

```genia
import python.json as pyjson
unwrap_or("fallback", "null" |> pyjson/loads)
```

## Portability boundary

- future hosts must preserve the same Core IR meaning
- future hosts may implement different internal runtimes
- future hosts must not let host-local convenience redefine:
  - pipeline stage behavior
  - Option propagation
  - Flow boundaries
  - host-bridge absence/error normalization
