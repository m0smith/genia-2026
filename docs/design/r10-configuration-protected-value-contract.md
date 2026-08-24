# R10 Configuration and Protected-Value Contract

Status: **Approved R10 contract; E10-1 through E10-4 provider/default/protected-carrier/sink-safety slices implemented; later slices not implemented.**

`GENIA_STATE.md` remains final authority for implemented behavior. The E10-1
provider/ordinary acquisition, E10-2 defaults/conversion-validation, E10-3 protected-carrier/matching, and E10-4 protected-sink subsets
are available; later sections remain contracted but unavailable until their own
tickets implement and verify them.

## Purpose

R10 adds deterministic configuration acquisition and protected secret handling
without adding a second value, matcher, validation, pipeline, or error model.
Configuration composes through ordinary calls, Outcomes, callable Templates,
and explicit host capabilities. Secrets reuse the R9 carrier abstraction with
a reserved protected policy that generic carrier operations cannot bypass.

## Terms

- **Configuration key**: a non-empty string with no NUL character, used only to
  select an entry. It is not a value, binding name, annotation, or field path.
- **Configuration source**: one immutable set of string-keyed raw entries made
  available to a provider snapshot.
- **Configuration provider**: an opaque capability value holding an ordered,
  immutable snapshot of zero or more sources.
- **Acquired raw value**: the exact string stored for a key, including `""`.
- **Default**: a zero-argument callable evaluated only after a lookup reports
  missing. It is not evaluated for an empty, found, or failed lookup.
- **Conversion**: an ordinary callable from an acquired/default value to an
  Outcome. It may parse or otherwise transform; implicit coercion is forbidden.
- **Template validation**: an ordinary callable Template applied to the
  conversion success value. Existing Outcome behavior remains unchanged.
- **Protected secret representation**: exactly one reserved outer `secret`
  carrier facet created by secret acquisition. Its carried value is ordinary
  data but is not observable without explicit declassification authority.
- **Protected matching**: matching the outer protected facet while returning
  the original protected value as the match payload.
- **Protection propagation**: the finite operation-family rules below; it is
  not transitive taint tracking.
- **Declassification**: `declassify(authority, protected)`, the only portable
  operation that returns a protected payload as an ordinary value.
- **Injection**: lifecycle-owned binding of already-acquired values. It is not
  retained in the first implementation sequence.

Configuration key names are treated as sensitive operational metadata. A
program may deliberately use a key string as ordinary data, but normalized
acquisition diagnostics never include it.

## Public surface

The approved surface consists of ordinary callable operations:

```text
config_provider(sources) -> some(provider) | err(reason, context)
config_get(provider, key) -> some(raw_string) | none("config-missing") | err(reason, context)
config_get_or(provider, key, default) -> some(raw_or_default) | err(reason, context)
secret_get(provider, key, purpose) -> some(secret_protected_string) | none("config-missing") | err(reason, context)
secret_get_or(provider, key, purpose, default) -> some(secret_protected_value) | err(reason, context)
protected_match(facet, value) -> some(original_protected_value) | none("representation-mismatch")
declassify(authority, protected_value) -> ordinary_carried_value
```

`config_provider` is the portable constructor over explicit source descriptor
values. Creating host-backed source snapshots requires a host capability. A
host injects declassification authority; source text cannot construct, copy,
serialize, compare, or inspect authority values.

The candidate expression forms `@config("key")` and `@secret("key")` are
rejected. Existing prefix annotations attach inert metadata to top-level
bindings and are not expressions. Reusing them would create an implicit
evaluation/acquisition path and conflict with lifecycle activation. R10 adds no
annotation, parser, AST, lowering, evaluator special form, or Core IR node.

`@server`, `@route`, `@cors`, `@test`, and other annotations are unchanged.
Ordinary evaluation and imports perform no configuration lookup unless code
explicitly calls the operations above. `meta` exposes no provider, key, value,
protection, or authority metadata.

## Sources, snapshots, and precedence

The first release supports exactly these source descriptors:

| Source | Descriptor | Portable meaning | Python reference host |
|---|---|---|---|
| literal values | `{kind: quote(values), values: map}` | snapshot of explicit string keys and string values | supported |
| process environment | `{kind: quote(environment)}` | snapshot supplied by an advertised host capability | snapshot of the process environment |

`sources` is an explicit list ordered from highest to lowest precedence. The
first source containing the key wins. No ambient source, implicit environment
fallback, command-line source, file source, working-directory search, module
source, or remote provider exists in the first release.

Provider construction validates all descriptors before acquiring any
host-backed snapshot. A provider is immutable. Every successful provider
construction captures one snapshot; later source mutation is invisible.
Repeated lookup of the same key returns the same result. A new snapshot requires
a new provider. Imports share only a provider explicitly passed or bound by the
program; module loading neither constructs nor refreshes one.

Literal source keys and environment snapshot names must satisfy the key
contract. Literal values and environment entries must be strings. Duplicate
keys inside a descriptor are impossible under ordinary map identity rules.
Cross-source duplicates are resolved solely by list order.

## Acquisition, defaults, conversion, and validation

| Situation | Result |
|---|---|
| key found with non-empty text | `some(exact_text)` |
| key found with `""` | `some("")` |
| key absent from every source | `none("config-missing")` |
| unsupported/unavailable source capability | `err("config-source-unavailable", {source_index})` |
| provider acquisition failure | `err("config-provider-failure", {source_index})` |
| malformed provider/source/key argument | runtime misuse; diagnostic omits key text and values |

Provider validation or acquisition failure makes `config_provider` return
`err`, with no partial provider. Ordinary Outcome propagation therefore prevents
lookup and default evaluation. Source access is complete during snapshot
construction; lookup itself has no external side effect.

`config_get_or` first performs `config_get`. On `some`, it preserves that
Outcome. On missing, it calls `default()` exactly once and wraps the returned
ordinary value in `some`; if the default returns an Outcome, that Outcome is
preserved rather than nested. On provider error it does not call the default.
A non-callable default or a non-zero-argument default is runtime misuse.

`secret_get` has the same lookup rules but requires a non-empty purpose symbol
and wraps the acquired string plus that opaque purpose in exactly one protected
`secret` layer before returning `some`. `secret_get_or` protects the default
success value in the same way. A default returning `none` or `err` is preserved
and not protected. A default success already containing any protected value is
runtime misuse; duplicate protection is not introduced.

Conversion and validation add no API. Programs compose existing Outcome-aware
pipeline behavior with an ordinary converter and callable Template:

```text
config_get(provider, "PORT") |> parse_port |> Port
```

The converter must return an Outcome. Its `none` or `err` is preserved. The
Template receives only the converter's `some` payload and returns its existing
Outcome unchanged. Defaults occur before conversion. Neither acquisition nor
validation silently trims, parses, coerces, or substitutes empty text.

Secret conversion is deliberately not part of the first acquisition surface:
secret source strings remain protected strings until an authorized boundary.
This avoids executing ordinary user conversion over an exposed payload.

## Protected carrier semantics

`secret` is a reserved facet policy over the R9 carrier abstraction, not a
nominal class or a generic facet registry.

- Generic `represent("secret", value)` is runtime misuse.
- Generic `representation_match("secret", value)` is runtime misuse even for a
  protected value.
- Generic `strip_representation("secret", value)` is runtime misuse.
- `protected_match("secret", value)` returns `some(value)` with the exact
  original protected value, not the carried payload.
- `protected_match` with any facet other than `"secret"` is runtime misuse.
- An ordinary value or non-secret represented value returns
  `none("representation-mismatch")`.
- Secret acquisition creates exactly one outer protected layer. Nested or
  duplicate protected layers are invalid public states.
- A protected value is unequal to ordinary and generic represented values.
- Equality between two protected values is permitted and follows carried-value
  equality without exposing either payload. Protected values are not valid map
  keys.

A named Template may define the conceptual secret pattern without new syntax:

```genia
pattern Secret(value) = protected_match("secret", value)
```

`Secret(x)` binds `x` to the protected value. `Secret(inner)` applies `inner`
to that protected value, so an ordinary inner literal, map, list, or scalar
pattern cannot inspect the carried payload. `@?`, `@!`, and `&` retain their
existing original-subject rules. Matching never grants declassification
authority.

## Transport and derivation

The rule is value-local: a protected leaf stays protected when transported.
A container holding protected leaves is not itself implicitly marked, but every
recursive sink scan treats the whole attempted sink operation as protected.

| Operation family | Rule |
|---|---|
| assignment, arguments, return, import/export binding | preserve the exact protected value |
| list/map/tuple/Outcome construction and projection | preserve protected leaves; do not protect the container or sibling values |
| pipeline, Seq, Flow, Sheet, ref, process/message transport | preserve protected leaves unchanged |
| identity, selection, reordering, `map`, `filter`, `reduce`, `scan` | transport is allowed; invoking an ordinary callback with a protected leaf is rejected before callback execution unless that callback only performs approved protected operations |
| protected equality and `protected_match` | return an ordinary boolean/Outcome; do not reveal or copy the payload |
| string concatenation, interpolation, Format, arithmetic, ordering, hashing, map-key freezing | reject when a protected operand is encountered |
| ordinary Template/validation predicate | may receive the protected value as opaque input; protected matching/equality may be used, payload inspection is rejected |
| diagnostic/Outcome reason or context construction | may transport protected leaves, but later rendering/serialization rejects the entire sink operation |
| JSON decode | cannot produce protection |
| JSON encode, CSV/Sheet/report rendering | reject recursively when any protected leaf is present |
| resource/file writes and HTTP response construction | reject recursively when any protected leaf is present |
| host calls | reject recursively unless the call is the explicit declassification-authorized boundary |
| host return values | never gain protection implicitly |

This is bounded propagation, not hidden taint. An operation either transports
the same protected leaf, returns a non-sensitive observation explicitly listed
above, or rejects. No derived ordinary string/number/container is implicitly
marked protected.

## Rendering and sink safety

Recursive protected-value detection applies through lists, maps, tuples,
Outcomes (payload, reason, context, metadata), Sheets, and any other traversable
ordinary runtime container. Opaque host handles are not inspected and may not
contain protected values through ordinary host conversion.

| Observation/sink | Required behavior |
|---|---|
| `display`, `debug_repr`, REPL final value, CLI final value | render exactly `<protected>` for a protected value; nested renderers substitute `<protected>` at each protected leaf |
| runtime exception and normalized diagnostic rendering | redact each protected leaf as `<protected>`; never include carried value, configuration key, provider contents, or authority |
| `Format` / `format` | reject the formatting operation if any resolved replacement is protected |
| `print`, `log`, `inspect`, `trace`, stdout, stderr | reject before writing anything if the submitted value recursively contains protection |
| native assertions and test reports | redact protected actual/expected/context values as `<protected>`; test bodies cannot print/log them |
| JSON encoding | return `err("protected-value", {operation: "json-encode"})` |
| CSV/Sheet/report rendering | fail with a normalized protected-value diagnostic identifying only operation and structural row/column/path position |
| resource/file write | return the boundary's existing recoverable failure shape with normalized reason `protected-value`; write zero payload bytes |
| HTTP response | reject response construction/serialization before headers or body are committed |
| ordinary host interop conversion | reject before calling the host function |

Rendering/redaction is only a diagnostic safety net. It is not authorization and
does not make outputting a protected value successful. Sink operations reject
where specified even though error rendering is redacted.

## Declassification

`declassify(authority, protected_value)` is the sole portable payload-revealing
operation.

- `authority` is an opaque, non-serializable host capability value injected at
  an explicit application boundary. Genia source cannot construct or derive it.
- Authority is scoped to one provider identity and an allowlist of purpose
  symbols supplied by the host. A protected value carries the provider identity
  and the purpose passed to `secret_get` opaquely; neither renders or serializes.
- The two-argument declassification operation accepts only an authority whose
  provider identity and purpose allowlist match the protected value.
- Success removes exactly one protected layer and returns the ordinary carried
  value. The runtime records a host-local audit event containing provider
  identity, purpose, source location when available, and success/failure, but no
  key or payload.
- Missing, mismatched, forged, or ordinary authority is runtime misuse and
  reveals nothing. Declassifying a non-protected value is runtime misuse.
- Authority cannot be stored in JSON, Sheets, resources, process messages, or
  ordinary host data; those operations reject it.

After successful declassification, the returned ordinary value has no hidden
taint. Preventing a program with legitimate authority from subsequently using
or exposing that ordinary value is explicitly not guaranteed. Applications
should declassify immediately at the narrow host call that needs the credential.

## Execution modes and lifecycle

- Ordinary evaluation, file/command/pipe mode, native tests, imports, and server
  lifecycle code use the same explicit provider values and portable semantics.
- Tests use literal fixture sources and fixture authorities supplied by the test
  harness. Real environment values and credentials never appear in test source,
  expected output, snapshots, or failure messages.
- CLI modes do not construct an ambient provider. A future CLI integration may
  explicitly create and pass one under its own ticket.
- Server startup may explicitly construct a provider before listener activation
  in a later ticket; request handling does not refresh it. Existing server
  annotations do not acquire or inject configuration.
- Injection and `@config`/`@secret` annotations are omitted from E10-1 through
  E10-7. A later follow-up requires separate evidence and contract work.

## Errors and diagnostics

Recoverable acquisition reasons are exactly:

- `config-missing`
- `config-source-unavailable`
- `config-provider-failure`

Protected boundary failures use normalized reason `protected-value` when the
existing boundary returns an Outcome. Runtime misuse remains the existing
language error category. Diagnostics may include only stable operation,
source-index, and structural path/row/column fields relevant to the failure.
They must not include the configuration key, raw/default/protected value,
provider contents/identity, authority, host environment, or exception text that
contains any of those values.

## Portability boundary

Portable language semantics:

- key validity, explicit ordered sources, first-source precedence, snapshot and
  repeat-lookup behavior, missing/present-empty/default behavior, Outcome and
  Template composition, protected carrier/matching/transport/derivation rules,
  sink behavior, authority checks, normalized errors, and no new syntax/Core IR.

Host capabilities:

- capturing a source snapshot, advertising supported source kinds, supplying
  declassification authority, recording audit events, and performing the
  authorized external operation after explicit declassification.

Python reference host:

- supports literal and process-environment snapshots; copies environment entries
  at provider construction; uses opaque provider/authority handles; emits the
  required host-local audit event. Python object/class/storage choices are not
  portable contract.

Legitimate host variation:

- whether the environment source capability is available, how source access is
  internally secured, and where non-sensitive audit events are stored. A host
  may reject an unavailable source but may not silently substitute another.

Core IR and parser impact: **none**. Existing call, list, map, function,
Outcome, pipeline, and named-pattern forms are sufficient.

## Future conformance strategy

Shared specs must cover:

- eval: source precedence, missing versus empty, lazy defaults, provider
  construction errors, conversion/Template Outcomes, protected match/equality, generic
  construct/match/strip rejection, recursive rendering/redaction and sink errors;
- flow: exact protected-leaf transport and callback rejection;
- error: normalized misuse/sink diagnostics with sentinel key/payload absence;
- CLI: stdout/stderr/exit behavior with fixture providers and no sentinel leak;
- parse and IR: ordinary-call surface plus regression proof that no annotation
  expression or new node exists.

Python tests must cover environment snapshot timing/mutation, unavailable source
capabilities, opaque handle conversion, audit events, resources, HTTP pre-commit
rejection, native-test reports, and recursive leak scanning.

Fixture secrets use unmistakable generated sentinel strings held only in the
test harness. Every captured stdout, stderr, exception, Outcome rendering,
report, serialized value, resource buffer, HTTP response, and audit record is
asserted not to contain the sentinel or fixture key.

## Proving cases

Minimal configuration:

```genia
provider = config_provider([{kind: quote(values), values: {PORT: "8080"}}]) |> unwrap_or(none)
config_get(provider, "PORT") |> parse_port |> Port
```

Expected result: `some(8080)` using existing Outcome/Template composition.

Minimal secret:

```genia
credential = secret_get(provider, "API_TOKEN", quote(outbound_api))
credential |> Secret(token) -> [display(token), representation_match("secret", token)]
```

The match binds a protected `token`; display yields `<protected>`, and generic
matching raises non-revealing misuse. Printing, logging, JSON encoding, or
generic stripping cannot expose the fixture payload.

Real pipeline:

```text
explicit provider snapshot
  -> ordinary endpoint acquisition + Template validation
  -> protected credential acquisition + Secret pattern
  -> validated records through existing Outcome pipeline
  -> credential declassified only with injected matching authority immediately
     before the authorized outbound host call
  -> clean records and normalized diagnostics with no key or payload
```

## Decision table

| Area | Decision |
|---|---|
| acquisition | explicit ordinary calls over an explicit immutable provider |
| precedence | source list order, highest first; no ambient fallback |
| defaults | zero-argument callable, missing-only, exactly once, before conversion |
| conversion | explicit Outcome callable; no coercion |
| validation | existing callable Templates and Outcomes |
| protected representation | reserved outer `secret` policy over R9 carrier |
| matching | `protected_match` returns the original protected subject |
| generic carrier operations | cannot construct, match, or strip `secret` |
| transport | exact protected leaves preserved |
| derivation | only enumerated observation/transport; other protected operands reject |
| sinks | recursive redaction for diagnostics; output/serialization sinks reject |
| declassification | only `declassify` with matching opaque host authority |
| errors | normalized non-sensitive reasons/context |
| annotations | rejected; existing annotations/lifecycles unchanged |
| parser/Core IR | no change |
| portability | semantics portable; snapshots/authority/audit are capabilities |

## Reconciled R10 sequence

1. **E10-1 — provider and ordinary acquisition (implemented, Experimental):**
   literal/environment snapshots, explicit precedence, missing/empty/provider
   errors, no defaults or secrets.
2. **E10-2 — defaults, conversion, and validation (implemented, Experimental):**
   lazy `config_get_or` plus proven composition with existing converters,
   Outcomes, and Templates.
3. **E10-3 — protected carrier and matching (implemented, Experimental):** `secret_get`, `secret_get_or`,
   reserved facet restrictions, equality/key rules, `protected_match`, transport.
4. **E10-4 — protected sinks:** rendering/redaction and recursive rejection for
   formatting, output, diagnostics, tests, JSON, reports, resources, HTTP, host.
5. **E10-5 — explicit declassification:** opaque scoped authority, exact checks,
   audit record, and narrow authorized-host-boundary proof.
6. **E10-6 — cross-mode hardening:** CLI/import/test/server snapshot boundaries;
   no annotation injection.
7. **E10-7 — composed validated-pipeline proving case.**
8. **E10-8 — release truth audit and distillation.**

Each behavior ticket performs its own repository phase workflow. E10-6's former
annotation/injection scope is replaced by cross-mode hardening. Injection is a
later follow-up, not an R10 exit requirement.

## Non-goals

- New syntax, annotation semantics, Core IR, nominal secret/config classes,
  implicit global lookup, schema/validation/error/pipeline alternatives, hidden
  taint, arbitrary callback-scoped reveal, memory-erasure guarantees, vaults,
  encryption, rotation, authentication/authorization, or multi-host delivery.

## Gate

**E10-1 through E10-4 implemented through issues #589-#592.** This contract does
not activate E10-5 or any later slice; each still requires its own ticket and
phase gates.
