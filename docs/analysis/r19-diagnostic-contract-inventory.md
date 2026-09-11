# R19 Diagnostic Contract Inventory

Status: **Planning analysis — non-authoritative.** `GENIA_STATE.md` remains final authority for implemented behavior.

This inventory classifies the diagnostic surfaces R19 must make portable enough for an independent host. It does not change any error message, runner field, spec, or runtime behavior.

## Current shared-spec facts

The active `error` shared-spec category currently asserts only normalized observable process behavior:

- `stdout` exact
- `stderr` exact
- `exit_code` exact

For current error cases, `stdout` is required to be empty, `stderr` is an exact string match, and `exit_code` is `1`.

The existing optional `notes` field may describe `error_phase`, `error_category`, and `message_source`, but those concepts are informational and are not machine-asserted structured fields.

Other categories have different contracts:

- parse specs compare normalized parse success exactly, while parse failures use error type plus message substring
- eval/CLI/flow cases compare normalized stdout/stderr/exit code at their observable boundary
- host-adapter protocol failures have their own normalized runner taxonomy from R16 and are not Genia program diagnostics

The result is an important R19 distinction: some exact text is already shared evidence, but not every Python exception/message string should automatically become permanent language text.

## Classification model

R19 should classify observed diagnostics into three groups.

### A — Exact portable diagnostic text

Use when wording is itself part of the user-visible language contract and independent hosts must emit the same bytes.

Examples include current shared `spec/error` cases unless R19 deliberately migrates a case to a structured contract while preserving an approved normalized message rendering.

Requirements:

- one deterministic template
- deterministic value rendering inside the message
- no host exception/library/OS wording
- byte-exact shared evidence

### B — Structured portable diagnostic identity with deterministic normalized rendering

Use when the important contract is phase/category/reason/parameters, while the host must still be able to produce a stable normalized message at shared boundaries.

Potential fields, if a later runner revision is approved:

- phase
- category/kind
- reason/code
- ordered parameters/context

E19-0 does **not** add these runner fields. This classification only preserves the option of making the semantic identity clearer than handwritten strings.

### C — Incidental host wording

Messages originating from Python, standard-library, OS, network, parser-library, or C++/STL internals are not portable merely because they can be observed somewhere in the reference host.

Such text must be normalized before entering an A/B portable boundary or remain host-local/non-conformance detail.

## Current inventory by surface

| Surface | Current assertion style | E19-0 classification direction | Notes |
|---|---|---|---|
| `spec/error/*.yaml` runtime/eval errors | exact stderr + exit 1 | A today; review each family before freezing permanently | Existing executable evidence already treats text as exact. |
| `spec/error` parse-origin cases | exact stderr through error execution path | A today, but reconcile with parse category | Avoid two contradictory contracts for the same parse failure. |
| `spec/parse` failures | type + message substring | B-like existing behavior | Exact full text is not currently required by parse specs. |
| eval cases expecting failure | stdout/stderr/exit code | A only where exact expected stderr exists | Do not infer untested Python wording as contract. |
| CLI misuse | normalized stdout/stderr/exit code | A or B depending existing shared case | Shell/OS parser wording must not leak. |
| Flow/Seq misuse | deterministic runtime messages in shared eval/error cases | A where asserted | Preserve function/type vocabulary while centralizing only if justified. |
| Template/validation misuse | many deterministic messages in error specs | A where asserted | Large family; inventory by template rather than one global rewrite. |
| R18 equality/map-key misuse | semantics approved by R18; exact diagnostic text intentionally deferred to R19 in places | R19 must decide A/B wording | Do not change key legality/equality semantics. |
| R10 protected-value boundaries | security-sensitive deterministic wording/redaction | A/B with non-leakage invariant | Diagnostic work must never expose protected payloads. |
| R14 HTTP/lifecycle host failures | already normalized into closed kinds at approved boundaries | B-style Outcome reason/context, not raw exception text | R19 must not collapse these into host strings. |
| R16 adapter protocol outcomes | structured runner taxonomy | outside Genia diagnostic redesign | `protocol_error`, `crash`, `timeout`, `unsupported` belong to runner protocol. |

## Existing error-spec families visible in the current tree

The current `spec/error` directory includes families covering at least:

- undefined names and assignment/pattern failures
- malformed pattern behavior
- wrong arity
- field/reason/skipped diagnostic helpers
- `collect_validated` misuse
- Template/validation misuse (`accumulate`, alternatives, and related R15 surfaces)
- additional release-specific deterministic misuse cases

E19-0 deliberately does not rewrite these files. The implementation slice should produce a machine-generated inventory of every exact expected `stderr` before changing any diagnostic construction.

## Required inventory fields for E19 implementation work

Before E19 diagnostic implementation begins, each exact diagnostic case should be tabulated with:

- spec file
- triggering source
- phase (`parse`, `eval`, `cli`, flow-stage, capability boundary, etc.)
- current exact stderr or substring expectation
- source function/module that constructs it
- whether dynamic values are interpolated
- how interpolated values are rendered (`display`, `debug_repr`, bespoke formatting)
- security/redaction implications
- proposed A/B/C classification
- portable diagnostic identifier/template if A/B

This table may be generated mechanically during E19-3 rather than hand-maintained forever.

## Diagnostic architecture constraints

The draft contract should preserve these invariants:

1. Host-native exception text does not define Genia diagnostics.
2. Exact portable messages use Genia-defined rendering for inserted values.
3. Protected/represented/authority values retain their existing redaction and non-leakage rules.
4. R16 adapter/protocol outcomes remain separate from evaluated-program diagnostics.
5. Parse diagnostics must not acquire a second contradictory contract merely because they can surface through `spec/error` and `spec/parse`.
6. Centralization is justified by portability, not by a desire to build a giant new error framework.
7. R19 may centralize stable templates in code; it does not require runtime loading of a data catalog.

## Recommended implementation strategy after contract approval

- first produce the complete mechanical exact-text inventory
- identify repeated templates and Python-derived text
- centralize only the stable repeated/portable templates
- normalize host-derived exceptions at the closest semantic boundary
- add representative cross-category drift guards
- preserve existing exact text unless the approved contract explicitly changes it

## Non-goals of this inventory

- no new error syntax
- no redesign of error categories
- no new structured runner fields in E19-0
- no mass rewrite of messages
- no localization/i18n
- no exposure of host exception internals
- no runtime/spec behavior change
