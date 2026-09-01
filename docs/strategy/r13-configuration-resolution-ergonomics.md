# R13 — Configuration Resolution Ergonomics

Status: **Active release; E13-0 approved and E13-1 through E13-3 implemented.** This
document records approved release direction only. It does not define implemented
language behavior. `GENIA_STATE.md` remains final authority.

## Theme

> Make R10 configuration and secrets comfortable for real applications without
> weakening explicit provider, Outcome, snapshot, or protected-value semantics.

R13 is an ergonomics layer over the completed R10 contract. It must not reopen
or replace R10 semantics.

## Problem

R10 deliberately chose explicit immutable provider construction and ordinary
acquisition calls. That keeps behavior truthful, but repeated calls such as
`config_get(provider, "SERVER_PORT")` and
`secret_get(provider, "OPENAI_API_KEY", quote(openai))` are cumbersome when an
application has several logical configuration domains and standard host-backed
sources.

R13 should let an application define its source policy once and create concise,
qualified lookup values without introducing ambient bare-name lookup, hidden
environment fallback, a second configuration model, or new syntax.

## Approved release boundary

R13 is limited to four concerns:

1. ordinary qualified configuration and secret views over one explicit R10 provider
2. explicit adaptation of program command-line arguments into the R10 string key/value source model
3. one narrow deterministic `.env`-style source capability
4. one conventional provider composition using an explicit documented source order

Every public operation must be an ordinary callable/value composition. R13 adds
no annotation, parser form, AST node, Core IR node, field-access protocol, or
lifecycle execution behavior.

## Qualified configuration views

A view captures an existing provider plus a physical key prefix. A secret view
also captures one explicit R10 purpose. Calling a view with a logical name maps
that name to one physical key and delegates to the existing R10 lookup.

Candidate application shape:

```genia
provider = config_standard(...) |> unwrap_or(none)

server = config_view(provider, "SERVER_")
database = config_view(provider, "DB_")
openai = secret_view(provider, "OPENAI_", quote(openai))

server("PORT")
database("PORT")
openai("API_KEY")
```

The exact public names remain contract/design decisions. The call shape is the
approved direction because current Genia dot access is deliberately limited to
maps and modules. R13 must not broaden `lhs.name`, manufacture an enumerable
provider map, or introduce a privileged member-resolution protocol merely to
support candidate `server.PORT` syntax.

The intended separation is:

```text
provider
  owns immutable source snapshots and precedence

view
  captures provider + prefix (+ secret purpose)

logical name
  is supplied explicitly when the view is called

physical key
  is prefix + logical name and is passed to R10 lookup
```

The first design should prefer prelude-level closures over a new runtime value
category when existing closure capture can preserve the exact provider, prefix,
and purpose.

### View invariants

- view construction performs no lookup, declassification, source acquisition, or provider refresh
- each view call performs exactly one existing R10 lookup
- an ordinary view returns the exact `config_get` Outcome
- a secret view returns the exact `secret_get` Outcome and never reveals the carried value
- the view adds no defaulting, conversion, validation, caching, precedence, or fallback behavior
- conversion and Template validation remain explicit downstream composition
- the contract must decide whether empty prefixes are valid and must require a non-empty logical name containing no NUL
- normalized failures must not expose the prefix, logical name, physical key, source contents, or protected payload

## Standard sources and precedence

The conventional provider should compose these sources from highest to lowest precedence:

```text
explicit launch/test overrides, when supplied
  > program command-line options
  > process environment snapshot
  > one .env-style file
```

The process environment intentionally precedes `.env` so deployment-provided
values are not replaced by a local file. Application defaults remain lazy and
explicit through `config_get_or`; they are not another implicit provider source.

Provider construction must preserve R10 snapshot semantics: validation and
source acquisition finish during provider construction, the first source
containing a physical key wins, later source mutation is invisible, and a new
snapshot requires a new provider.

Literal/test values already have an R10 descriptor. R13 should not add a wrapper
whose only purpose is to rename that existing map shape unless design evidence
shows it materially improves the conventional-provider boundary.

## Command-line source boundary

The command-line adapter consumes explicit program arguments, normally the
existing `argv()` value. It must not inspect or reinterpret Genia interpreter
mode flags.

Candidate normalization:

```text
--port 8080     -> PORT=8080
--db-port 5432  -> DB_PORT=5432
```

E13-0 must lock:

- whether the adapter accepts raw `argv()` or an existing `cli_parse` result
- long-option grammar and whether short/grouped options are excluded
- flag-without-value behavior under R10's string-only source contract
- hyphen/case normalization
- repeated-option and normalized-key collision behavior
- positional and `--` terminator behavior
- malformed option Outcome/runtime-misuse classification

Unknown-option validation requires a separately supplied schema and is not part
of R13. Without such a schema, every syntactically valid option is data.

## `.env` source boundary

The first pass supports one explicit or conventional path only. E13-0 must lock
one complete grammar, including:

- UTF-8 and optional BOM behavior
- blank lines and full-line comments
- key grammar
- whitespace around keys, `=`, and values
- quoted value and escape behavior
- inline-comment behavior
- duplicate-key behavior
- final-line-without-newline behavior
- missing-file behavior
- malformed-input and host-read failure normalization

The initial release excludes recursive parent-directory discovery,
`.env.local`, profile cascades, environment-name selection, interpolation,
variable expansion, command substitution, and framework-specific discovery.
A malformed file must never be treated as an absent file.

The `.env` snapshot is a host capability. The portable contract owns descriptor
shape, parsing obligations, precedence, normalized Outcomes, and snapshot
behavior; the Python reference host owns filesystem acquisition. Capability
documentation must label that boundary explicitly.

## Conventional provider boundary

The conventional provider is one explicit construction operation. Calling it is
the acquisition event; later lookup is not ambient acquisition. Its result must
retain the existing `config_provider` success/failure model rather than throwing
away source validation or acquisition Outcomes.

The contract must decide:

- exact argument shape, including explicit overrides and `.env` path policy
- whether a missing conventional `.env` is absence while an explicitly requested path is failure
- whether CLI or filesystem capabilities being unavailable are source absence or `config-source-unavailable`
- how source indices remain deterministic after optional-source handling

The conventional helper must be reducible to the same ordered immutable source
model as `config_provider`; it is not a competing provider implementation.

## Core semantic guardrails

- ordinary identifier resolution remains lexical
- current map/module-only named access remains unchanged
- dynamic configuration resolution happens only through an explicitly created and explicitly called view
- the provider remains explicit in view construction
- the provider alone owns source precedence and immutable snapshots
- views own logical-name-to-physical-key mapping only
- ordinary lookup preserves exact R10 Outcome behavior
- secret lookup preserves exact R10 provider identity, purpose, protected carrier, matching, sink, audit, and declassification behavior
- no lookup implicitly reads process state, arguments, or files after provider construction
- no new `$`, `${...}`, `$${...}`, `@config`, or `@secret` syntax
- no configuration key, prefix, logical name, physical key, source value, host failure detail, or protected payload appears in normalized diagnostics
- source kind/index/stage may be reported only where the approved R10/R13 contract classifies it as non-sensitive

## Lifecycle boundary

R13 does not bind providers through a lifecycle, annotation, global slot, hidden
root binding, or dependency-injection mechanism. Applications explicitly pass a
provider once when constructing their views.

R14 may consume completed R13 provider/view values when it contracts application
and request lifecycle wiring. That later release must not retroactively change
R13 lookup, snapshot, or protection semantics.

## Killer-workflow alignment

R13 indirectly strengthens Outcome-aware validated data pipelines:

- CLI/environment/`.env` inputs enter one deterministic string source model
- configuration acquisition continues to return Outcomes
- conversion and validation continue through existing converters and callable Templates
- protected credentials can reach authorized pipeline boundaries without appearing in records, diagnostics, reports, or sinks
- the proving case must configure one real validated-data-pipeline application, not a standalone configuration toy

## Non-goals

R13 does not include:

- dynamic or ambient scoping of bare identifiers
- `server.PORT` or another extension to named/member access
- lifecycle-owned provider injection
- dependency injection or service containers
- a generic user-programmable resolver protocol
- arbitrary filesystem discovery
- YAML, TOML, or JSON configuration files
- `.env` interpolation, expansion, profiles, or cascades
- remote vault or secret-store integration
- secret rotation
- authentication or authorization
- configuration schemas or unknown-option validation
- implicit conversion or coercion
- changing R10 protected carriers, sinks, authority, audit, or declassification
- HTTP-specific configuration lookup
- reopening R10 completion

## Portability posture

- **Portability zone:** mixed portable semantics and advertised host capabilities
- **Core IR impact:** none; all proposed source-visible behavior is ordinary calls, values, closures, maps, strings, symbols, and Outcomes
- **Capability categories:** existing configuration snapshot capability plus proposed explicit CLI adaptation and `.env` file snapshot capability
- **Shared spec impact:** portable view mapping/Outcome behavior and deterministic source composition should receive eval/error/CLI coverage; host filesystem acquisition needs focused Python-host tests
- **Python reference host impact:** CLI normalization, `.env` acquisition/parser, conventional composition, and capability documentation
- **Host adapter impact:** advertise unsupported host capabilities honestly and normalize portable observations without Python-specific paths or exceptions
- **Future host impact:** future hosts implement the same snapshot, precedence, parsing, and Outcome contract or report the capability unavailable

This posture is planning guidance. The mandatory E13-0 pre-flight portability
analysis must complete every field again against its final locked scope.

## Release sequence

Every behavior issue runs its own complete repository phase workflow. The
release epic is #608.

1. **#670 — E13-0: configuration-resolution ergonomics contract — complete**
   - Lock view call shapes, CLI normalization, `.env` grammar, standard-provider arguments/precedence, diagnostics, capability boundaries, and exclusions.
   - Contract only; no tests or implementation.
2. **#671 — E13-1: qualified configuration and secret views — implemented**
   - Implement the smallest ordinary closure/value surface over unchanged `config_get` and `secret_get` behavior.
3. **#672 — E13-2: explicit CLI configuration source — implemented**
   - Normalize explicit program arguments into one immutable R10-compatible string source.
4. **#673 — E13-3: narrow `.env` source capability — implemented**
   - Implement the contracted grammar, exact missing/malformed distinction, and immutable host-backed snapshot.
5. **#674 — E13-4: conventional provider composition**
   - Compose overrides, CLI, process environment, and `.env` in the approved order without a second provider model.
6. **#675 — E13-5: cross-mode, diagnostic, and protected-boundary hardening**
   - Prove snapshot timing, non-refresh, non-leakage, capability-unavailable behavior, and unchanged syntax/Core IR across relevant modes.
7. **#676 — E13-6: Outcome-aware validated-pipeline proving case**
   - Compose multiple qualified `PORT` values, conversion/Template validation, clean diagnostics, and one protected credential at an authorized boundary.
8. **#677 — E13-7: release examples and implemented-truth synchronization**
   - Documentation and runnable-example verification only; no runtime behavior.
9. **#678 — E13-8: release truth audit and distillation**
   - Audit the complete approved boundary and remove process artifacts; no runtime behavior.

## Ticket acceptance baseline

Every R13 ticket must:

- classify itself as **Current release: R13** after E13-0 is approved; E13-0 is **Next release / contract gate** until that approval
- name its dependency on E13-0 and any earlier behavior slice
- include explicit scope and non-goals from this document
- identify portable contract versus Python-host capability work
- preserve R10 exact-string, precedence, snapshot, Outcome, protected-value, sink, and declassification behavior
- name affected shared specs, focused tests, capability docs, core docs, cheatsheets/book pages, release docs, and composability-matrix review
- complete pre-flight, contract, design, failing test, implementation, documentation, audit, and distillation phases as applicable
- avoid claiming planned behavior in `GENIA_STATE.md` or user-facing docs before implementation and verification

## Dependencies and gate

- R9 — Value Templates & Representations: complete
- R10 — Configuration & Secrets: complete and the semantic authority for R13
- R11/R12: complete but not semantic dependencies of the R13 contract
- R4/R8 lifecycle concepts: not consumed by R13; lifecycle binding remains R14

**GO for E13-0 pre-flight only.** Implementation remains blocked until E13-0
completes pre-flight and an explicit approved contract. The attached legacy
pre-flight template is not current; use `docs/process/00-preflight.md`, including
its mandatory portability analysis and full phase discipline.

## Exit criterion

A normal Genia application can explicitly construct one deterministic snapshot
from program arguments, process environment, one `.env`-style file, and optional
explicit overrides; create concise ordinary and secret views for multiple
logical domains; resolve multiple cleanly separated settings such as `PORT`;
and feed ordinary values through existing Outcome conversion/Template validation
while protected values retain every R10 safety boundary.
