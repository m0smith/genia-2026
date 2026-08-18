# Composability Matrix

> **Status: PROPOSED / EXPLORATORY**
> This design aid mixes implemented foundations with planned R9 relationships.
> The Status column identifies each row. It does not define implemented
> behavior; `GENIA_STATE.md` is final authority.

## Current foundation

| Concept | Composes with | Relationship | Status |
|---|---|---|---|
| ordinary values | functions and pipelines | functions consume/produce values; pipelines pass stage results | Implemented |
| ordinary values | patterns | patterns recognize and destructure values | Implemented |
| Outcome | constructor patterns | `some`, `none`, and `err` distinguish success, absence, and recoverable failure | Implemented |
| named matcher | nested pattern | `Name(inner)` applies one Outcome matcher, then matches its success payload | Implemented, Experimental |
| template | named matcher and Outcome | a Template is an ordinary one-argument Outcome matcher; named Templates are first-class callable values | Implemented, Experimental |
| template | `@?` / `@!` / `&` | named Templates reuse existing original-subject and short-circuit semantics | Implemented, Experimental |
| matcher | `@?` / `@!` | check/assert while retaining the original subject on success | Implemented, Experimental |
| matcher | matcher | `&` composes left-to-right over the original subject | Implemented, Experimental |
| List | Seq-compatible helpers | list transforms return lists; terminal helpers consume lists | Implemented |
| Flow | Seq-compatible helpers | transforms remain lazy; terminal helpers consume the single-use Flow | Implemented |
| validation helpers | Outcome | validators return Outcomes; misuse remains a runtime error | Implemented, Experimental |
| `validate_each` | `collect_validated` | per-item Outcomes feed clean/diagnostic aggregation | Implemented, Experimental |
| validated records | Sheet/report output | clean ordinary map records require explicit `collect_sheet`; CSV rendering is explicit | Implemented, Experimental |
| annotations | native tests | inert `@test` metadata is consumed only by test mode | Implemented, Experimental |
| annotations | serve mode | inert server descriptors are consumed only by explicit R8 serve mode | Implemented, Experimental/Python-host-only |
| lifecycle descriptors | test/serve consumers | consumers activate their explicit lifecycle; annotations do not self-execute | Implemented foundation |
| rendering | output | `display`, `debug_repr`, `Format`, and `format` produce strings; sinks perform I/O | Implemented; some Format parts Experimental |

## Approved R9 relationships

These rows are design constraints from
`r9-value-template-representation-contract.md`, not implemented behavior.

| Concept | Composes with | Required relationship | Status |
|---|---|---|---|
| open/exact template | ordinary map/list | structural compatibility without nominal conversion or layout promises | Approved R9 design; not implemented |
| representation facet | ordinary value | explicit ordered carrier layer; no parallel JSON/secret value hierarchy | Approved R9 design; not implemented |
| representation pattern | nested pattern/template | consume one explicit outer facet, then match the carried value | Approved R9 design; not implemented |
| represented value | List/map/pipeline/Seq/Flow | transport preserves the value; derivation does not propagate facets implicitly | Approved R9 design; not implemented |
| representation facet | equality/keys | exact ordered facets participate in equality and key suitability | Approved R9 design; not implemented |
| representation facet | explicit strip/declassification | remove one outer facet explicitly; protected facets may require authorization | Approved R9 design; not implemented |
| JSON | representation facet | decode to ordinary Genia values with one outer `json` facet | Planned E9-5; not implemented |
| JSON Schema subset | template | produce ordinary structural/refinement templates; reject unsupported features | Planned E9-6; not implemented |
| `json` representation | structural template | conceptual `json(Person(x))` proves boundary plus structure composition | Planned E9-7; not implemented |
| future `secret` | representation facet | reuse the carrier abstraction while retaining protection during matching | R10 constraint; not implemented |
| rendering | representation facet | separate concerns; rendering policy may hide protected payloads | Approved boundary; facet behavior not implemented |

## Isolation rules

| Concern | Must not become | Reason |
|---|---|---|
| template | a second matcher, validation, or nominal type system | Outcome matchers are the single compatibility model |
| representation facet | implicit coercion, unordered tags, or host wrapper identity | semantics must be explicit, ordered, and portable |
| derivation | automatic facet/taint propagation | preservation or replacement must be operation-specific and testable |
| pattern match | implicit declassification | protected values must remain protected without authorized stripping |
| rendering/Format | carrier representation | output strings and boundary metadata are different concerns |
| JSON | a parallel object/value hierarchy | decoded data remains ordinary Genia maps, lists, scalars, and `nil` |
| JSON Schema | silent best-effort interpretation | unsupported features must fail clearly |
| annotation | self-executing behavior | lifecycle consumers activate inert metadata explicitly |
| execution mode | new language semantics | modes select host/runtime execution behavior |
| Sheet | implicit Seq or Outcome conversion | conversions and aggregation remain explicit |

The matrix must be reviewed again during E9-8 and whenever a later release
changes one of these composition boundaries.
