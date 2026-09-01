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
| configuration provider | Outcome / Template | explicit immutable lookup returns exact-string `some(...)` or missing `none(...)`; `config_get_or` lazily supplies only missing values; R13 `config_view`/`secret_view` qualify exact logical names through one unchanged lookup without adding defaults or validation; `config_args` purely normalizes explicit string arguments into the existing literal source descriptor, while an explicit `.env` descriptor snapshots exact strings through the same provider before existing converters and callable Templates compose with lookup Outcomes | R10 E10-1/E10-2 and R13 E13-1/E13-3 implemented, Experimental |
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

## R11 relationships

These rows record the release-complete E11-1 through E11-8 foundation; E11-8 is
audit/distillation only. See `r11-ai-composition-contract.md`.

| Concept | Composes with | Required relationship | Status |
|---|---|---|---|
| model | ordinary callable / Outcome | `model/4` returns one ordinary callable; after local validation and authorized credential declassification, each call makes exactly one synchronous fixture or Gemini REST attempt and returns an existing Outcome; explicit shared eval/error/Flow/CLI fixture observations preserve that relationship without ambient bindings | E11-1 through E11-4 implemented, Experimental; providers Python-host-only |
| prompt and chain | function / pipeline | prompts build ordinary request values and chains use ordinary functions and `|>`; no second chain runtime or executor | Planned; not implemented |
| structured model output | R9 JSON / Template | a closed request carries one R9 JSON schema plus an explicit callable Template; strict `json_decode` validates the single provider text observation, the Template checks its carried ordinary value once, and success retains the original represented value; no AI schema/repair/retry system | E11-2 implemented, Experimental; fixture Python-host-only |
| model credential | R10 protected value / authority | explicit `secret_get(..., quote(model_call))` stays protected until declassification immediately before one authorized adapter attempt; the Gemini adapter places the revealed string only in its private API-key header | E11-3 implemented, Experimental; Gemini adapter Python-host-only |
| conversation | external list/Flow / `scan` | an application step evolves exact ordinary state from external events; list and Flow produce equivalent consumed states, terminal states make later events inert, and input acquisition, termination, and cancellation are not hidden in a conversation runtime | E11-5 implemented, Experimental; no new builtin |
| model structured Outcome | JSONL validation / `collect_validated` | only parse/validation successes invoke the ordinary model stage; R9 represented successes become clean values and existing normalized failures become diagnostics without retry, repair, or a second collection framework | E11-6 proving case implemented, Experimental; fixture Python-host-only |
| R11 public examples | callable / R9 / R10 / Outcome / `scan` | executable text, structured-output, conversation, and validated-pipeline examples verify the existing composition boundaries without adding a helper or alternate framework | E11-7 documentation verification implemented; no runtime behavior |

## R12 relationships

These rows record the release-complete R12 boundary. E12-1 through E12-8 are
implemented as Experimental; E12-8 is documentation verification only and
E12-9 is audit/distillation only. See
`r12-retrieval-grounding-contract.md`.

| Concept | Composes with | Required relationship | Status |
|---|---|---|---|
| document/chunk provenance | R9 JSON representation / ordinary callable | closed ordinary values retain the exact represented metadata value; `chunk/2` invokes one ordinary span chunker exactly once, then owns Unicode-code-point source slicing and provenance rather than trusting chunker-produced text; it adds no new Template or representation semantics | E12-1 implemented, Experimental |
| embedding input | ordinary variant values / Outcome | explicit chunk and query variants share one `embed/4` callable without fabricating query provenance or hiding embedding in retrieval; exact input identity is retained across the opaque provider boundary | E12-2 implemented, Experimental; deterministic fixture Python-host-only |
| embedding | R10 protected value / index/retrieve compatibility | finite vectors carry exact dimensions and application-owned compatibility space; indexing validates exact corpus dimensions/space and retrieval checks exact query/index space/dimensions before their authorized attempts; compatibility does not claim equal results across providers | E12-2 through E12-4 implemented, Experimental |
| indexing | R10 protected value / Outcome / opaque host capability | `index/4` accepts a nonempty compatible embedded corpus, keeps the credential protected until one `quote(index_call)` attempt, and returns only an opaque non-comparable/non-serializable handle rather than exposing backend storage | E12-3 implemented, Experimental; deterministic fixture Python-host-only |
| index/retrieve | opaque host capabilities / ordinary callables / Outcome | the index handle privately retains paired capability identity, space, dimensions, backend reference, and indexed provenance; `retrieve/4` checks identity then space then dimensions before one authorized attempt and returns provider-ordered exact indexed evidence or no-results absence | E12-3/E12-4 implemented, Experimental; deterministic fixtures Python-host-only |
| provider reranking | retrieved evidence / R10 authority / Outcome | `rerank/4` keeps the credential protected through empty/local validation, makes one authorized attempt only for nonempty evidence, and may reorder occurrences and replace finite scores while preserving the exact duplicate-aware chunk/provenance multiset; pure local rerankers remain ordinary differently named functions | E12-5 implemented, Experimental; deterministic fixture Python-host-only |
| grounded context/answer | R11 content / Outcome / `model/4` | the importable application module validates exact closed context/answer values, retains the exact ordered evidence list, derives first-occurrence exact-equal sources, propagates non-success Outcomes, and invokes one supplied unchanged model callable; citation rendering remains application-owned | E12-6 implemented, Experimental; private validation proof Python-host-only |
| complete grounded composition | R10 authorities / Flow / validation diagnostics / E12 evidence / R11 `model/4` | explicit ordinary stages keep each provider concern separately authorized, make attempts only under demand, preserve exact provenance into the grounded answer, and gate later provider/model work on existing successful Outcomes; compatible replacement preserves call/value contracts rather than identical results | E12-7 proving case implemented, Experimental; deterministic fixtures Python-host-only |
| R12 public examples | ordinary values / callables / Outcomes / R9 / R10 / R11 / Flow | executable chunking and complete grounded examples verify the existing composition boundaries while keeping backend-native scores distinct from citation rendering and adding no helper or alternate framework | E12-8 documentation verification implemented; no runtime behavior |

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
