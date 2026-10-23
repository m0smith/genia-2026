# Error Message Format — Cross-Language Comparison and Recommendation (DRAFT)

Status: **DRAFT / non-authoritative.** Nothing here is implemented. `GENIA_STATE.md` remains final authority. This note is input to a future contract; it changes no behavior.

## 1. Problem

Genia errors are currently one free-text line on stderr (`Error: Undefined name: x`, exit code 1). Host exceptions (`TypeError`, `PatternMatchError`, ...) are the only structure, and those are Python-host mechanisms (R19 §2: host exception wording is never semantic authority). The shared error specs already name three contract concepts that are not machine fields: `error_phase`, `error_category`, `message_source` (`spec/error/README.md`).

Goal: one definition that is (a) pleasant for humans, (b) parseable by machines, (c) feeds logs, metrics and traces without per-consumer scraping, and (d) portable across hosts.

## 2. What the best systems do

| System | Strength worth stealing | Weakness / cost |
|---|---|---|
| **Rust (rustc, `--error-format=json`)** | Stable code (`E0425`) + `--explain`; primary/secondary labelled spans; `help`/`note` children; one diagnostic model rendered as human text *or* JSON | Numeric codes are opaque; JSON schema is compiler-internal |
| **Elm** | Best human text: plain-language, shows the source, suggests a fix; also emits JSON | No stable codes; prose is the only identity |
| **TypeScript / Roslyn (C#)** | `TSxxxx` / `CSxxxx` code + category + message *template* with numbered args, localizable | Numeric registry needs central curation |
| **Clang/GCC → SARIF** | OASIS SARIF 2.1: `ruleId`, `level`, `message`, `locations`, `relatedLocations`, `fixes`; consumed by GitHub code scanning | Heavy for runtime errors; built for static analysis |
| **LSP `Diagnostic`** | Small, widely implemented: `range`, `severity`, `code`, `codeDescription`, `source`, `message`, `relatedInformation`, `tags`, `data` | Editor-oriented; no cause chain |
| **Go** | Errors are values; `%w` wrapping + `errors.Is/As` give a cause *chain*; `log/slog` attaches typed key/values | Messages are strings; no standard code or location |
| **Python** | Exception chaining (`__cause__`/`__context__`), PEP 678 `add_note`, column-caret tracebacks, `ExceptionGroup` for multiple errors | Type name is the only identity; traceback is text |
| **Java/.NET** | Cause chain + typed exceptions; structured logging (Logback/ECS, Serilog message templates) | Stack-trace text dominates; high-cardinality messages leak into metrics |
| **Erlang/Elixir** | `{error, Reason}` tagged data, not text; `Logger` metadata; reason atoms are stable and matchable | Convention only; no mandated shape |
| **PostgreSQL** | 5-char `SQLSTATE` (class = first 2 chars) + severity + `message` + `detail` + `hint` + `position` | Code space is fixed and coarse |
| **gRPC `google.rpc.Status`** | Coarse canonical `code` + `message` + typed `details[]`; `ErrorInfo{reason, domain, metadata}` is the machine identity; `LocalizedMessage`, `RetryInfo`, `Help` | Verbose; two-level code scheme confuses people |
| **RFC 9457 Problem Details** | `type` (URI, doubles as docs link), `title`, `status`, `detail`, `instance`, plus extension members | HTTP-shaped; no span/cause |
| **OpenTelemetry semantic conventions** | `error.type` (**low cardinality** — the only error attribute meant for metric labels), `exception.type/message/stacktrace` on span events/logs, span status `ERROR` | Defines *emission*, not the error's own shape |
| **Elastic Common Schema** | `error.code`, `error.id`, `error.message`, `error.type`, `error.stack_trace` flat names for log pipelines | Overlaps OTel; pick one mapping |

### Cross-cutting lessons

1. **Identity must be separate from prose.** Every system that supports tooling well has a stable code (Rust, TS, Roslyn, SQLSTATE, gRPC `reason`, OTel `error.type`). Systems that rely on message text (Elm, Go, Python) force consumers to regex.
2. **Message = template + parameters, not a pre-formatted string.** Roslyn, Serilog and gRPC `LocalizedMessage` keep arguments separate. This makes grouping (fingerprints), redaction, and localization possible, and keeps metrics clean.
3. **One model, many renderers.** Rust and Elm prove human and JSON output can come from the same object. Never maintain a second hand-built JSON path.
4. **Cardinality discipline.** Only `code`/`category`/`phase`/`severity` may be metric labels. Message, parameters, paths and values belong in logs/traces only (OTel rule; the usual cause of runaway metric bills).
5. **Causes and related locations are first-class** (Go `%w`, Python chaining, LSP `relatedInformation`, SARIF `relatedLocations`) — a flat string loses the "caused by" story.
6. **Location is a span, not a string** (`file, line, col, end_line, end_col`), optional for runtime errors that have no source.
7. **Help is data** (`help`, `hint`, `fixes`) — separate from the message so terse renderers can drop it.
8. **Versioned schema.** JSON output needs a `schema`/`version` field before anyone parses it.

## 3. Genia-specific constraints

- **Portability (R19):** the portable contract is `code` + `params`; message text is rendered from a catalog. A second host must reproduce the code and params, not Python wording.
- **Existing byte contract:** `spec/error/*.yaml` asserts exact stderr `Error: <message>\n`, exit 1. The default human rendering must stay byte-identical unless a spec change is approved.
- **Already-structured diagnostics:** `err(reason, context?)` and `diagnostic_*` already produce maps with `field`, `status`, `reason`, `context`, `path`, `kind`. The new shape should be a superset projection of these, not a rival.
- **Protected values (R10):** configuration secrets must never appear in `params` or rendered text; the params model needs a redaction rule.
- **Observable surface:** CLI/error contracts are limited to `stdout`, `stderr`, `exit_code` (STATE). JSON must be opt-in so that default stays unchanged.

## 4. Recommended architecture

### 4.1 The Diagnostic record (single source of truth)

A Genia map (so it is a plain value, matchable, and host-neutral):

```
{
  schema:   "genia.diagnostic/1",
  code:     "eval.undefined_name",       # stable, namespaced <phase>.<slug>; never reused
  phase:    "parse" | "eval" | "runtime" | "host" | "io" | "config",
  category: "NameError",                 # coarse class, bounded set (metric-safe)
  severity: "error" | "warning",
  message:  "Undefined name: x",         # rendered from catalog template + params
  params:   {name: "x"},                 # typed, redactable; template args
  span:     {file, line, col, end_line, end_col},   # optional
  cause:    <Diagnostic> | none,         # chain, Go/Python style
  related:  [{span, message}],           # secondary labels, LSP/SARIF style
  help:     "Did you mean `y`?" | none,
  retryable: false                       # optional; gRPC RetryInfo analogue
}
```

Code form: **dotted lowercase slug** (`eval.undefined_name`) rather than `E0425`. Readable in logs, greppable, matchable in Genia, safe as an OTel `error.type` value, and equivalent to gRPC `ErrorInfo.reason`. A registry file (`docs/contract/error_codes.json`, guarded like `semantic_facts.json`) maps code → category, template, default severity, docs anchor. Codes are append-only; retiring one leaves a tombstone.

### 4.2 Renderers (all derived from §4.1)

| Renderer | Output | Notes |
|---|---|---|
| **human** (default) | `Error: <message>` | Byte-compatible with current specs. Optional `--verbose`/TTY adds `--> file:line:col`, source snippet, `help:`, `caused by:` |
| **json** (`--error-format=json`) | One JSON object per line on stderr, exactly the §4.1 record | Rust-style; versioned via `schema` |
| **log** | level from severity; message; flattened attributes (`error.code`, `error.type`, params as `genia.error.param.*`) | slog/ECS-like |
| **otel** | span event `exception` with `exception.type=category`, `exception.message`, `exception.stacktrace`; attribute `error.type=code`; span status ERROR | Follows OTel semantic conventions |
| **metric** | counter `genia.errors{code, phase, severity}` | Labels **only** those three; never message/params |
| **lsp/sarif** (later) | Project `span`, `code`, `severity`, `related` | Cheap once the record exists |

### 4.3 Grouping / fingerprint

`fingerprint = hash(code, phase, cause.code?)` — message and params deliberately excluded (Sentry/OTel practice).

### 4.4 Mapping examples from today's specs

| Today's stderr | `code` | `category` |
|---|---|---|
| `Undefined name: undefined_name` | `eval.undefined_name` | `NameError` |
| `No matching case for function f/1 ...` | `eval.no_matching_case` | `PatternMatchError` |
| `Assignment target must be a simple name` | `parse.invalid_assignment_target` | `SyntaxError` |
| `Module not found: m` | `module.not_found` | `FileNotFoundError` |
| `Module import cycle detected ...` | `module.import_cycle` | `RuntimeError` |

## 5. Alternatives considered

- **Numeric codes (E0425 / SQLSTATE):** compact but opaque and need central allocation; slugs give the same stability with self-documentation. Can add an alias column later.
- **RFC 9457 as the core shape:** right for the future HTTP/`serve` surface (`type`/`title`/`detail`), but lacks span/cause; treat it as a *projection* of §4.1, not the base.
- **SARIF as the core shape:** too heavy for runtime errors; offer as an export.
- **Free-form `context` maps only (status quo for `err`):** flexible, but no identity or grouping.

## 6. Adoption path (follows repo workflow: contract → spec → implementation → STATE)

1. **Contract:** this note → approved `docs/design/error-diagnostic-contract.md` (record, code grammar, redaction, renderers). Decide open questions below.
2. **Registry + catalog:** `docs/contract/error_codes.json`; doc-sync test that every code used by a spec exists.
3. **Spec:** extend `spec/error/*.yaml` so `notes` become asserted fields (`code`, `phase`, `category`); add `--error-format=json` cases. Default stderr cases stay unchanged.
4. **Python host:** attach `code` + `params` at raise sites (start with the six existing error specs); renderer module owns all formatting; `_emit_error` becomes the single funnel.
5. **Observability adapters:** log/OTel/metric renderers behind opt-in config; no new default output.
6. **STATE/RULES sync** when behavior lands.

## 7. Open questions for the owner

1. Slug codes (`eval.undefined_name`) vs numeric (`GE0101`) vs both?
2. Should `err(reason, context)` Outcome values be convertible to Diagnostics (e.g. `diagnostic_of(err)`), or stay separate?
3. Is JSON error output wanted only on the CLI, or also in `serve`/MCP responses (RFC 9457 projection)?
4. Is localization in scope, or just template/params separation for now?
5. Should warnings exist (new severity) or is everything `error` in this phase?
