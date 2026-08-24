# Composability Matrix

> **Status: PROPOSED / EXPLORATORY**
> This design aid records implemented foundations alongside explicit
> later-release constraints. The Status column identifies each row. It does not
> define implemented behavior; `GENIA_STATE.md` is final authority.

## Current foundation

| Concept | Composes with | Relationship | Status |
|---|---|---|---|
| ordinary values | functions and pipelines | functions consume/produce values; pipelines pass stage results | Implemented |
| ordinary values | patterns | patterns recognize and destructure values | Implemented |
| Outcome | constructor patterns | `some`, `none`, and `err` distinguish success, absence, and recoverable failure | Implemented |
| named matcher | nested pattern | `Name(inner)` applies one Outcome matcher, then matches its success payload | Implemented, Experimental |
| template | named matcher and Outcome | a Template is an ordinary one-argument Outcome matcher; named Templates are first-class callable values | Implemented, Experimental |
| template | `@?` / `@!` / `&` | named Templates reuse existing original-subject and short-circuit semantics | Implemented, Experimental |
| refinement template | boolean predicate | `refinement_match` lifts true to `some(original)` and false to ordinary mismatch | Implemented, Experimental |
| open template | ordinary map and field Templates | `open_shape_match` requires listed fields, accepts extras, preserves the original map, and propagates nested Outcome failures | Implemented, Experimental |
| exact template | ordinary map and field Templates | `exact_shape_match` requires an equal key set, preserves the original map, and propagates nested Outcome failures | Implemented, Experimental |
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

## R9 relationships

These rows summarize the implemented R9 boundaries and the explicitly marked
future-secret constraint from `r9-value-template-representation-contract.md`.

| Concept | Composes with | Required relationship | Status |
|---|---|---|---|
| representation facet | ordinary value | `represent` adds one explicit ordered carrier layer; no parallel JSON/secret value hierarchy | Implemented generic carrier, Experimental |
| representation pattern | nested pattern/template | `representation_match` consumes one explicit outer facet through a named Template, then matches the carried value | Implemented generic matching, Experimental |
| represented value | List/map/pipeline/Seq/Flow | transport preserves the value; derivation does not propagate facets implicitly | Implemented generic carrier rule, Experimental |
| representation facet | equality/keys | exact ordered facets participate in equality and existing key suitability | Implemented generic carrier rule, Experimental |
| representation facet | explicit strip/declassification | `strip_representation` removes one outer generic facet; protected `secret` uses only `declassify` with exact host-injected provider/purpose authority and audit | Generic strip and E10-5 declassification implemented, Experimental |
| JSON | representation facet | `json_decode` returns an ordinary Genia root with one outer `json` facet; `json_encode` consumes that layer or a supported ordinary value | Implemented E9-5, Experimental |
| JSON Schema subset | template | `json_schema` compiles the closed structural subset into ordinary callable Outcome Templates and rejects unsupported keywords | Implemented E9-6, Experimental |
| `json` representation | structural template | `Json(person)` consumes one outer facet and the JSON Schema-derived `Person(person)` Template validates the carried ordinary value in an Outcome-aware pipeline | Implemented E9-7 proving case, Experimental |
| `secret` | representation facet | E10-3 implements one reserved protected outer carrier created only by secret acquisition; generic `represent`, `representation_match`, and `strip_representation` reject it | R10 E10-3 implemented, Experimental |
| `secret` | named Template / pattern | `protected_match` returns the exact protected subject, so `Secret(x)` binds protected `x` and reuses existing named-pattern, `@?`, `@!`, and `&` rules without implicit declassification | R10 E10-3 implemented, Experimental |
| configuration provider | Outcome / Template | explicit immutable lookup returns exact-string `some(...)` or missing `none(...)`; `config_get_or` lazily supplies only missing values, explicit converters return existing Outcomes, and callable Templates validate converted successes without a second schema or error model | R10 E10-1/E10-2 implemented, Experimental |
| protected value | List/map/pipeline/Seq/Flow/Sheet | E10-3 transport preserves exact protected leaves and containers do not gain hidden taint; E10-4 diagnostic rendering redacts recursively and existing output/serialization sinks reject before effects | Transport and sinks implemented, Experimental |
| rendering | representation facet | separate concerns; generic facets render opaquely, while the protected policy renders `<protected>` diagnostically and rejects output/serialization sinks | Generic opacity and protected policy implemented, Experimental |
| protected value | explicit declassification | only an opaque host-injected matching authority may remove the protected layer; generic `strip_representation` rejects it | R10 E10-5 implemented, Experimental |
| configuration/protection | execution modes | ordinary eval, file, command, pipe, import, native-test, and serve-entry paths preserve explicit values; modes and annotations add no ambient acquisition, and serve snapshots precede activation without request refresh | R10 E10-6 implemented, Experimental; serve mechanics Python-host-only |
| configuration/protection | validated record pipeline / authorized boundary | the E10-7 proving case composes explicit converter/Template Outcomes, exact protected matching, `validate_each`/`collect_validated`, and declassification immediately in an injected authorized fixture call; it adds no helper or alternate framework | R10 E10-7 proving case implemented, Experimental; authority/host fixture Python-host-only |

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

The matrix was reviewed during E9-8 and must be reviewed whenever a later
release changes one of these composition boundaries.

## R11 planned relationships

These rows constrain later R11 work. They are approved planning boundaries,
not implemented behavior; see `r11-ai-composition-contract.md`.

| Concept | Composes with | Required relationship | Status |
|---|---|---|---|
| model | ordinary callable / Outcome | `model/4` returns one ordinary callable; each call makes at most one synchronous provider attempt and returns an existing Outcome | Planned; not implemented |
| prompt and chain | function / pipeline | prompts build ordinary request values and chains use ordinary functions and `|>`; no second chain runtime or executor | Planned; not implemented |
| structured model output | R9 JSON / Template | strict `json_decode` plus an explicit callable Template validates one represented JSON result; no AI schema/repair system | Planned; not implemented |
| model credential | R10 protected value / authority | explicit `secret_get(..., quote(model_call))` stays protected until declassification immediately before one authorized adapter attempt | Planned; not implemented |
| conversation | external list/Flow / `scan` | an application step evolves exact ordinary state from external events; input acquisition, termination, and cancellation are not hidden in a conversation runtime | Planned; not implemented |

## Keeping this matrix in sync

`tests/doc/test_composability_matrix_sync.py` automatically re-derives the
full Template/representation/matcher family (every `*_match` helper, plus
`represent`, `strip_representation`, `json_decode`, `json_encode`, and
`json_schema`) from `src/genia/builtins.py` and
`src/genia/std/prelude/*.genia`, and fails if any member is missing from this
matrix, missing from `GENIA_STATE.md`, or if this matrix still mentions a
family-shaped name that no longer exists in code. See AGENTS.md's
"Composability Matrix Sync Rule" for what to do when it fails — the test
only guards names, not the accuracy of the composition described for each
one.
