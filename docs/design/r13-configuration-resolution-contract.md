# R13 Configuration Resolution Contract

Status: **APPROVED / EXPERIMENTAL — E13-0 contract; E13-1 through E13-4 implemented.**
Later R13 behavior in this document is not implemented merely because this contract exists.
`GENIA_STATE.md` remains final authority for implemented behavior.

## Purpose

R13 adds an ordinary value/callable ergonomics layer over the completed R10
configuration provider. It defines qualified lookup views, explicit program
argument normalization, one narrow `.env` source, and one conventional provider
composition without changing R10 lookup, Outcome, snapshot, protected-value,
sink, authority, audit, or declassification semantics.

## Public surface

The approved future surface is:

```text
config_view(provider, prefix) -> callable(logical_name)
secret_view(provider, prefix, purpose) -> callable(logical_name)

config_args(args) -> some(values_source_descriptor)
                   | err("config-source-invalid", context)

config_standard(overrides, args) -> some(provider) | err(reason, context)
config_standard(overrides, args, dotenv_path) -> some(provider) | err(reason, context)
```

The `.env` source descriptor is:

```text
{kind: quote(dotenv), path: path, required: boolean}
```

`config_args` returns the existing literal descriptor shape:

```text
{kind: quote(values), values: normalized_map}
```

inside `some(...)`. R13 adds no wrapper around explicit override maps.

All operations are ordinary calls and values. Views are ordinary one-argument
callables. No new syntax, annotation, parser form, AST node, Core IR node,
named-access protocol, provider kind, or lifecycle binding is introduced.

## Qualified views

### Construction

`config_view(provider, prefix)` requires an R10 provider and a string prefix.
`secret_view(provider, prefix, purpose)` additionally requires the same
non-empty purpose symbol accepted by `secret_get`.

An empty prefix is valid. A prefix containing NUL is runtime misuse. Construction
validates only its arguments and captures them. It performs no lookup, source
acquisition, provider refresh, default evaluation, conversion, validation,
protection, declassification, or host operation.

The returned callable accepts exactly one logical name. The logical name must be
a non-empty string containing no NUL. Invalid arity, provider, prefix, purpose,
or logical name is runtime misuse with a non-sensitive diagnostic.

### Calls

For a valid call, the physical key is exact string concatenation:

```text
physical_key = prefix + logical_name
```

No trimming, case conversion, separator insertion, normalization, parsing, or
fallback occurs.

- A `config_view` call invokes `config_get(captured_provider, physical_key)`
  exactly once and returns its exact Outcome.
- A `secret_view` call invokes
  `secret_get(captured_provider, physical_key, captured_purpose)` exactly once
  and returns its exact Outcome.

Views do not cache. Repeated calls repeat the R10 lookup over the same immutable
provider snapshot. They add no defaulting, precedence, conversion, Template
validation, or error translation. Secret results retain the exact provider
identity, purpose, protected carrier, sink behavior, and authority rules owned
by R10.

## Explicit program-argument source

### Input and result

`config_args(args)` consumes an explicit plain list of strings, normally the
result of `argv()`. It accepts raw program arguments, not the result of
`cli_parse`. It never reads `argv()` itself and never sees or reinterprets Genia
interpreter mode flags. It snapshots its input during the call and returns a
literal values descriptor suitable for `config_provider`.

A non-list input or a list containing a non-string is runtime misuse. A
syntactically malformed string list is recoverable source data failure:

```text
err("config-source-invalid", {
  source_kind: quote(arguments),
  stage: quote(parse)
})
```

No argument index, option spelling, or value is included in the Outcome or
rendered diagnostic.

### Grammar

Before the first standalone `--`, every token must participate in a long option
pair:

```text
option = "--" name
pair   = option value
name   = segment ("-" segment)*
segment = ASCII_ALPHA (ASCII_ALPHA | ASCII_DIGIT)*
```

Names are ASCII only and case-sensitive as input. A value is the next exact
string token. It may be empty and may begin with `-`; only a token in option
position is parsed as an option. `--name=value`, bare `--name`, short options,
grouped short options, empty segments, underscores, non-ASCII letters, and
positional tokens before the terminator are malformed.

A standalone `--` ends configuration parsing. All later tokens are ignored
exactly, including option-like tokens. The terminator is not data and requires
no following token. An empty argument list and a list containing only `--`
produce an empty values map.

### Normalization and collisions

Each accepted name is normalized by replacing `-` with `_` and converting ASCII
letters to uppercase. Values are preserved exactly.

```text
--port 8080        -> PORT = "8080"
--db-port 5432     -> DB_PORT = "5432"
--Db-Port primary  -> DB_PORT = "primary"
```

Every normalized key must satisfy the R10 key contract. A normalized key may
occur only once. Repeated spellings and distinct spellings that normalize to the
same key are both `config-source-invalid`; no first-wins or last-wins value is
returned. Unknown but syntactically valid names are accepted because R13 owns no
configuration schema.

Flags without values are invalid. R13 does not invent a boolean encoding inside
R10's string-only source model.

## `.env` source

### Descriptor and acquisition

`{kind: quote(dotenv), path, required}` is an R10-compatible host-backed source
descriptor. `path` must be a non-empty string containing no NUL and `required`
must be a boolean. Invalid descriptor fields are runtime misuse during provider
validation, before any host-backed source is acquired.

Provider construction validates every descriptor first, then acquires sources
in source-list order under the R10 all-or-nothing rule. A `.env` source is read
at most once during construction. Successful content is parsed and copied into
the immutable provider snapshot. Lookup never reads the file. Later file
creation, deletion, or mutation is invisible.

If `required` is `false`, a path that is absent at acquisition contributes an
empty source at its fixed list position. If `required` is `true`, absence is:

```text
err("config-provider-failure", {
  source_index: index,
  source_kind: quote(dotenv),
  stage: quote(acquire)
})
```

An unavailable filesystem capability is always
`err("config-source-unavailable", context)`, whether the source is optional or
required. Permission, I/O, or other host read failure is
`err("config-provider-failure", context)`. Invalid UTF-8 or grammar is
`err("config-source-invalid", context)`. Those contexts contain only
`source_index`, `source_kind: quote(dotenv)`, and respectively
`stage: quote(acquire)`, `quote(decode)`, or `quote(parse)`.

Malformed or unreadable input is never treated as absence, and every failure
returns no partial provider.

### Encoding and lines

Content is UTF-8. One leading UTF-8 BOM is accepted and removed. A BOM anywhere
else is ordinary content and therefore invalid unless permitted in a quoted
value. Invalid UTF-8 is a decode-stage source failure.

The parser accepts LF and CRLF line endings. A final line need not end in a line
break. A bare CR is invalid. Blank lines and lines whose first non-horizontal-
whitespace character is `#` are ignored. Horizontal whitespace means ASCII
space or tab only.

### Entries

An entry is:

```text
hws* key hws* "=" hws* value hws*
key = (ASCII_ALPHA | "_") (ASCII_ALPHA | ASCII_DIGIT | "_")*
```

Keys are preserved exactly and must also satisfy the R10 key contract. Duplicate
keys are `config-source-invalid`; no first-wins or last-wins snapshot is
produced.

Values have exactly three forms:

- **unquoted:** zero or more characters other than CR, LF, `#`, single quote,
  double quote, or backslash. Leading horizontal whitespace after `=` and
  trailing horizontal whitespace are not part of the value. An unquoted `#`
  begins an inline comment and must either be the first value character or be
  preceded by horizontal whitespace. Otherwise the line is invalid.
- **single quoted:** characters between `'` and the next `'`. Every character is
  literal; backslash has no escape meaning. The value may contain `#`, spaces,
  tabs, `=`, and double quotes, but not CR, LF, or a single quote. After the
  closing quote, only horizontal whitespace and an optional `#` comment may
  appear.
- **double quoted:** characters between `"` and the next unescaped `"`.
  The only escapes are `\\`, `\"`, `\n`, `\r`, and `\t`, producing backslash,
  double quote, LF, CR, and tab respectively. Any other escape is invalid.
  Literal CR or LF is invalid. After the closing quote, only horizontal
  whitespace and an optional `#` comment may appear.

Empty unquoted, `''`, and `""` values all produce the exact empty string.
There is no interpolation, variable expansion, command substitution, multiline
value, `export` prefix, continuation, Unicode normalization, or escape handling
outside double quotes.

## Conventional provider

### Arguments and source order

`config_standard(overrides, args)` uses the conventional path `.env` with
`required: false`. `config_standard(overrides, args, dotenv_path)` uses the
supplied path with `required: true`.

`overrides` must be a map whose keys and values satisfy the R10 literal-source
contract. `args` has the exact `config_args` input contract. `dotenv_path` has
the exact `.env` path contract. Invalid argument types or literal entries are
runtime misuse before any acquisition.

The helper first normalizes `args`. On `config-source-invalid`, it returns that
Outcome without acquiring environment or filesystem state. Otherwise it is
exactly reducible to:

```text
config_provider([
  {kind: quote(values), values: overrides},
  normalized_argument_descriptor,
  {kind: quote(environment)},
  {kind: quote(dotenv), path: selected_path, required: selected_required}
])
```

All four descriptors are always present in those fixed zero-based positions:

| source index | source |
|---:|---|
| 0 | explicit overrides |
| 1 | normalized program arguments |
| 2 | process environment snapshot |
| 3 | `.env` snapshot |

Empty overrides, empty argument entries, and an absent optional `.env` remain
empty sources at their positions. Source indices never collapse or renumber.
Precedence is therefore exactly overrides > arguments > environment > `.env`.
Application defaults remain explicit downstream `config_get_or` behavior and
are not a provider source.

The result is the exact `config_provider` success or failure Outcome. Calling
`config_standard` is the acquisition event. It validates before host
acquisition, produces no partial provider, snapshots all inputs and host-backed
sources once, and performs no later refresh.

Because program arguments are supplied as an ordinary list, R13 introduces no
separate CLI acquisition capability and no CLI-capability-unavailable result.
The existing host boundary that supplies `argv()` remains unchanged. The
environment and filesystem capabilities may independently be unavailable; an
unavailable required conventional source is never silently omitted.

## Failures and diagnostics

R13 adds one recoverable source reason:

```text
config-source-invalid
```

It denotes malformed external source data: explicit argument syntax, `.env`
UTF-8, or `.env` grammar. R10 reasons retain their exact meanings:

- `config-source-unavailable` — an advertised host source capability is unavailable
- `config-provider-failure` — required absence or host acquisition failure
- `config-missing` — a valid provider contains no requested physical key
- `protected-value` — an existing protected boundary rejects a secret

Runtime misuse covers invalid callable arity/type, provider, prefix, logical
name, purpose, descriptor shape, path argument, override map, or argument-list
element type. It occurs before the affected lookup or acquisition.

Recoverable contexts may contain only the applicable stable fields:
`source_index`, `source_kind`, and `stage`. `source_kind` and `stage` are quoted
symbols. A diagnostic or Outcome must never contain an option name, argument
index, prefix, logical name, physical key, configuration key, filesystem path,
source content, source value, raw host failure, provider identity, purpose,
authority, or protected payload.

## Portability boundary

### Portable language obligations

- view construction/callability, validation, exact concatenation, and one R10
  delegation per call
- argument grammar, normalization, collision rules, descriptor result, and
  `config-source-invalid`
- `.env` descriptor shape, encoding/grammar obligations, missing policy,
  normalized Outcomes, and immutable snapshot behavior
- conventional arities, fixed source order/indices, validation order,
  precedence, and exact R10 provider result
- unchanged R10 Outcomes, protected values, sinks, authority, audit,
  declassification, execution-mode behavior, and no syntax/Core IR impact

### Host capabilities

- `config.environment-snapshot` remains the existing advertised capability
- `config.dotenv-snapshot` acquires bytes for exactly the explicit descriptor
  path and distinguishes absence, unavailability, and host read failure
- the host supplies raw program arguments only through the existing explicit
  `argv()` boundary; `config_args` itself is portable pure normalization

### Python reference host

A future Python slice may implement `config.dotenv-snapshot` using its filesystem
and the existing environment snapshot capability. Python paths, exception
classes/messages, object types, file APIs, and storage choices are not portable
contract. No R13 host capability is implemented by E13-0.

Future hosts either provide equivalent advertised snapshot capabilities or
return the normalized unavailable Outcome. They may not silently substitute a
different source or parsing policy.

Core IR and parser impact: **none**.

## Conformance obligations

Later R13 tickets must add, before implementation, failing coverage for:

- shared eval/error cases for view mapping, exact Outcomes, misuse, and secret
  preservation
- shared eval/CLI/error cases for every argument grammar, terminator,
  normalization, repeat, and collision rule
- portable parser fixtures plus focused Python filesystem tests for every
  `.env` production, UTF-8/BOM/line ending case, missing/unavailable/read/
  decode/parse failure, and post-snapshot mutation
- conventional pairwise precedence, fixed indices, optional absence,
  acquisition order, failure atomicity, and later-mutation invisibility
- file, command, pipe, import, native-test, and serve-startup cross-mode
  observations where applicable
- diagnostic and recursive sink scans proving that generated sentinel names,
  paths, values, raw host details, and protected payloads never escape
- parse/Core IR regression proving that only existing ordinary forms are used

The E13-6 proving case must configure a real Outcome-aware validated-data
pipeline with distinct server, database, and another qualified `PORT`; explicit
conversion and callable Template validation; clean diagnostics; and one
protected credential revealed at most once only at an injected authorized
boundary. It adds no new API or semantics.

## Examples

Proposed minimal view behavior:

```genia
provider = config_provider([
  {kind: quote(values), values: {SERVER_PORT: "8080"}}
]) |> unwrap_or(none)
server = config_view(provider, "SERVER_")
server("PORT")
```

Expected future result: `some("8080")`.

Implemented conventional composition:

```genia
provider = config_standard(
  {REPORT_FORMAT: "json"},
  argv()
) |> unwrap_or(none)

server = config_view(provider, "SERVER_")
database = config_view(provider, "DB_")
openai = secret_view(provider, "OPENAI_", quote(openai))

server("PORT")
database("PORT")
openai("API_KEY")
```

Classification: proposed R13 contract examples, not currently runnable R13
behavior.

## Non-goals

- ambient or dynamic bare-name lookup
- `server.PORT` or broader named access
- annotations, syntax, AST, Core IR, lifecycle binding, provider injection, or
  dependency injection
- a second provider implementation or user-programmable resolver protocol
- configuration schemas, unknown-option validation, boolean flags, short or
  grouped options, implicit conversion, or coercion
- `.env` discovery, parent traversal, `.env.local`, profiles, cascades,
  interpolation, expansion, command substitution, multiline values, or watch/
  refresh behavior
- YAML, TOML, JSON configuration files, remote stores, vaults, rotation,
  authentication, or authorization
- changes to R10 protected carriers, sinks, authority, audit, declassification,
  or completion status
- HTTP-specific configuration behavior

## Release gate

This contract is implementation-ready for the scoped R13 sequence only after
explicit approval.

**E13-1 (#671), E13-2 (#672), and E13-3 (#673) are implemented through their separate phase
workflows.** Their delivered behavior is authoritative only where recorded in
`GENIA_STATE.md`.

**NO-GO for E13-4 through E13-8 until their declared dependencies and
per-ticket phase gates are satisfied.**
