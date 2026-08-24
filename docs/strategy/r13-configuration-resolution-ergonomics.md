# R13 — Configuration Resolution Ergonomics

Status: **Planned, not active.** This document records proposed release direction only. It does not define implemented language behavior. `GENIA_STATE.md` remains final authority.

## Theme

> Make R10 configuration and secrets comfortable for real applications without weakening explicit provider, Outcome, snapshot, or protected-value semantics.

R13 is an ergonomics layer over the completed R10 contract. It must not reopen or replace R10 semantics.

## Problem

R10 deliberately chose explicit provider construction and ordinary acquisition calls. That keeps behavior truthful, but repeated calls such as `config_get(provider, "DB_PORT")` and `secret_get(provider, "OPENAI_API_KEY", quote(openai))` are too verbose for normal application code.

R13 should reduce ceremony without introducing ambient bare-name lookup, hidden environment fallback, or a second configuration model.

## Candidate scope

### Standard configuration sources

Provide standard source constructors for common application configuration inputs:

- command-line options
- `.env`
- process environment
- literal/test values

The exact public API names are design work, not approved syntax.

### Conventional provider

Provide a deterministic standard-provider composition for the common application case.

Candidate precedence:

```text
command-line options
  > .env
  > process environment
```

Provider construction must preserve R10 snapshot semantics: acquisition happens when the provider is constructed, precedence is deterministic, and later source mutation is not observed by that provider.

The first pass should not recursively search parent directories or discover arbitrary config files. A missing conventional `.env` may be treated as absence if the contract explicitly approves that behavior; malformed discovered input must not be silently ignored.

### Qualified configuration views

Allow concise logical namespaces over an existing provider so repeated physical key prefixes do not infect application code.

Candidate application shape:

```genia
provider = config_standard()
server = config("SERVER_")
database = config("DB_")
openai = secrets("OPENAI_", quote(openai))

server.PORT
database.PORT
openai.API_KEY
```

The exact names above are candidates only.

The intended semantics are:

```text
provider = where values come from
resolver/view = how logical names map to physical keys
qualified prefix = which logical domain is selected
name = the requested setting
```

This allows multiple values named `PORT` to coexist naturally:

```genia
server.PORT
database.PORT
redis.PORT
metrics.PORT
```

### Lifecycle/application binding

A normal application lifecycle may bind one conventional provider so application code can construct concise config/secret views without manually threading the provider through every use site.

This must remain explicit lifecycle/application wiring, not ambient bare-name lookup.

## Core semantic guardrails

- Ordinary identifier resolution remains lexical.
- Dynamic resolution happens only through an explicit qualified prefix/value.
- The provider owns source precedence and snapshot behavior.
- A resolver/view owns logical-name-to-key mapping only; it must not create a competing precedence mechanism.
- Config lookup preserves existing R10 Outcome behavior.
- Secret lookup preserves existing R10 protected-value behavior.
- Protected values remain protected until explicit authorized declassification.
- No implicit process-environment fallback inside ordinary identifier lookup.
- No second acquisition API that bypasses `config_provider`, `config_get`, or `secret_get` semantics.
- No new `$`, `${...}`, `$${...}`, `@config`, or `@secret` syntax unless later evidence proves syntax is necessary and it passes the normal semantic gates.
- Prefer zero new syntax if existing qualified access can express the model cleanly.

## Standard-provider boundaries

R13 should distinguish clearly between:

```text
Source constructor
  describes/captures one source

Provider
  owns ordered precedence and immutable snapshot behavior

Qualified config/secret view
  maps logical names onto physical keys

Lifecycle/application wiring
  supplies the conventional provider to the running application
```

These responsibilities must not blur together.

## Candidate source helpers

Possible public helpers to evaluate during design:

```genia
config_values(values)
config_cli()
config_dotenv(path)
config_env()
config_standard()
```

These names are not approved API. The design phase should prefer the smallest surface that removes repeated ceremony.

## CLI source considerations

A command-line config source should normalize ordinary options into the same configuration key space used by other sources, so CLI, `.env`, environment, and test values are not separate programming models.

Example candidate mapping:

```text
--port 8080     -> PORT=8080
--db-port 5432  -> DB_PORT=5432
```

Exact option grammar, collision handling, unknown-option behavior, and interaction with existing Genia CLI arguments require contract work before implementation.

## `.env` considerations

The first pass should stay deliberately narrow:

- one explicitly known/conventional `.env` path
- deterministic parsing
- no upward-directory treasure hunt
- no automatic `.env.local`, `.env.production`, profile cascade, or framework-specific discovery unless separately approved
- malformed input must have deterministic failure semantics

## Secrets

Qualified secret views must be only an ergonomic wrapper over R10 protected acquisition.

For example, a candidate expression such as:

```genia
openai.API_KEY
```

must still yield the R10 protected Outcome result corresponding to the mapped physical key. It must not expose the carried string or weaken sink/declassification rules.

## Non-goals

R13 does not initially include:

- dynamic scoping of bare identifiers
- generic dependency-injection framework
- arbitrary filesystem configuration discovery
- YAML/TOML/JSON config files
- remote vault/secret-store integration
- secret rotation
- authentication/authorization systems
- a generic user-programmable resolver framework unless the config use case proves it necessary
- changing R10 protected-carrier, sink, authority, or declassification semantics
- reopening R10 completion

## Dependencies

- R9 — Value Templates & Representations: complete
- R10 — Configuration & Secrets: complete
- R4 lifecycle concepts may be reused for application/provider binding, but R13 must not introduce hidden lifecycle acquisition

R13 is sequenced after R12 in the roadmap, but its semantic dependency is primarily R10. R11 and R12 are not required to define the configuration ergonomics contract unless later design reveals a concrete interaction.

## Exit criterion

A normal Genia application can use command-line options, `.env`, and process-environment configuration through one deterministic provider setup and refer to domain-qualified configuration and secret names concisely, including multiple cleanly separated `PORT` values, while preserving R10 Outcome, snapshot, precedence, protection, sink, and explicit-declassification rules.

## Required process

Before implementation, R13 must proceed through the repository phase discipline:

1. contract
2. design
3. failing tests
4. implementation
5. documentation
6. audit
7. distillation

Any implementation work must keep `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, relevant book/cheatsheet documentation, host capability documentation, shared specs, and the composability matrix truthful and current as required by `AGENTS.md`.
