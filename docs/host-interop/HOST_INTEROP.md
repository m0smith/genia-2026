# Genia Host Interop Contract

This document defines the shared portability contract for Genia hosts.


**LANGUAGE CONTRACT**
- The shared host contract currently covers these spec categories: parse, ir, eval, cli, flow, error.
- The contract requires host-neutral observable behavior; the current implemented shared semantic-spec suite applies executable comparison for `eval`, `ir`, `cli`, `flow`, and initial `error` behavior in the Python reference host.

**PYTHON REFERENCE HOST**
- Python is the only implemented host and is the reference host today.
- The Python host adapter implements the shared host contract for these spec categories:
  - parse
  - ir
  - eval
  - cli
  - flow
  - error
- Other hosts are not implemented yet.

Future hosts may differ internally, but must preserve the same observable Genia semantics at the source/Core IR/runtime boundary.

## Status Terms

- **Implemented host**: runnable host code exists in this repository with tests.
- **Reference host**: the implemented host used as the current semantic baseline.
- **Scaffolded surface**: docs, manifests, placeholders, or layout exist, but no runnable host implementation exists there yet.
- **Planned host**: intended future host work only.
- **Contract**: the observable semantics that all hosts must preserve, defined by Core IR + spec + `GENIA_RULES.md`.


Current status:

- Python is the only implemented reference host.
- The Python host adapter in `hosts/python/` implements the shared host contract for the categories above, using the core runtime in `src/genia/`.
- Node.js, Java, Rust, Go, and C++ are planned hosts only.
- `spec/` and `tools/spec_runner/` now include an implemented shared semantic-spec runner plus active `eval`, `ir`, `cli`, `flow`, initial `error`, and initial `parse` case files.
- executable shared semantic-spec coverage is currently active for `eval`, `ir`, `cli`, `flow`, initial `error`, and initial `parse`.

## Authority Order

When multi-host artifacts disagree, use this order:

1. `GENIA_STATE.md`
2. `GENIA_RULES.md`
3. `GENIA_REPL_README.md`
4. shared spec artifacts under `spec/`
5. `docs/host-interop/*`
6. `docs/architecture/core-ir-portability.md`
7. `README.md` and relevant core reference docs

Notes:

- `GENIA_STATE.md` remains the final authority for current implemented behavior.
- The shared spec suite is the authoritative cross-host conformance target as it grows.
- Hosts must not treat host-local convenience as stronger than the shared docs/spec contract.



## Phase 2 Strictness, Normalization, and Error Contract

**The Python reference host is the current conformance baseline in this phase.**

- In the current implemented shared semantic-spec suite:
  - eval comparison is limited to normalized `stdout`, normalized `stderr`, and `exit_code`
  - cli comparison is limited to normalized `stdout`, normalized `stderr`, and `exit_code`
  - flow comparison is limited to normalized `stdout`, normalized `stderr`, and `exit_code`
  - error comparison is limited to normalized observable `stdout`, normalized observable `stderr`, and `exit_code`
  - IR comparison is limited to normalized portable Core IR output
- Error shared specs in this phase assert only the observable runner surface:
  - `stdout`
  - `stderr`
  - `exit_code`
- Current error shared cases require:
  - `stdout` exactly `""`
  - `stderr` exact match
  - `exit_code` exactly `1`
- Error phase/category/message remain contract concepts, but they are not structured runner fields in this phase.
- Malformed, missing, or unsupported cases fail validation with explicit normalized errors; nothing is silently skipped.
- Output ordering and structure are deterministic and stable.
- Only the minimal portable Core IR node families are used in lowering and output (see `docs/architecture/core-ir-portability.md`).
- CLI and flow behaviors are strictly validated for output, error, and exit code normalization.
- GENIA_STATE.md is the final authority for implemented behavior; all specs and docs must align with it.

---


## Host Adapter and Spec Runner Model

The Python host adapter exposes a single `run_case(spec: LoadedSpec) -> ActualResult` entrypoint in `hosts/python/adapter.py`. The shared spec runner routes all category execution through this entrypoint via `tools/spec_runner/executor.py::execute_spec`.

**Input contract** — `run_case` accepts a `LoadedSpec`-compatible value with these execution fields:

| Field | Present for |
|-------|-------------|
| `category` | all |
| `source` | all |
| `stdin` | eval, flow, error, cli |
| `file` | cli (file mode) |
| `command` | cli (command and pipe modes) |
| `argv` | cli |
| `debug_stdio` | cli |

The adapter must not inspect `expected_*` fields and must not mutate the input.

**Output contract** — `run_case` returns an `ActualResult`-compatible value with fields per category:

| Category | Fields returned |
|----------|----------------|
| eval, flow, error | `stdout`, `stderr`, `exit_code` |
| cli | `stdout`, `stderr`, `exit_code` (trailing newlines stripped) |
| ir | `ir` (normalized portable Core IR) |
| parse | `parse` (`{kind: "ok", ast: ...}` or `{kind: "error", type: ..., message: ...}`) |

**Normalization rules:**
- All text fields: line endings normalized (`\r\n` → `\n`, `\r` → `\n`)
- CLI only: trailing newlines stripped from `stdout` and `stderr` after line-ending normalization
- eval, flow, error: trailing newlines are preserved (not stripped)
- Unsupported categories raise an error immediately; no result is returned

In the current implemented shared semantic-spec system, the shared runner executes `eval`, `ir`, `cli`, `flow`, initial `error`, and initial `parse` cases.

The shared spec runner loads YAML eval, cli, flow, error, IR, and parse cases, executes them against the Python reference host, and compares:

- eval: normalized `stdout`, normalized `stderr`, and `exit_code`
- cli: normalized `stdout`, normalized `stderr`, and `exit_code`
- flow: normalized `stdout`, normalized `stderr`, and `exit_code`
- error: normalized `stdout`, normalized `stderr`, and `exit_code`
- ir: normalized portable Core IR output
- parse: normalized AST (exact match for `kind: ok`) or error type exact + message substring (for `kind: error`)

- Error specs reuse eval execution; there is no separate error execution path in the runner.
- Error `notes` are informational only and are not machine-asserted.
- Parse specs call the Python host parse adapter directly; no subprocess is invoked.

Other hosts are not implemented yet. "Portable" means: any future host must pass the same contract and normalization rules, but only Python is enforced today.


## Normalization Concept

Normalization means all observable outputs (values, errors, IR, CLI, flow) are converted to canonical, host-neutral forms. No Python-specific details are allowed in normalized outputs. Only the minimal portable Core IR node families are used in the contract. Error objects are normalized with required fields and strict category separation.


## Not Implemented

- No other hosts are implemented yet.
- No browser runtime or playground is implemented; browser artifacts are documentation only.
- No generic multi-host runner exists; all conformance is validated against the Python reference host.


## Shell Pipeline Stage (Python-Host-Only)

`$(command)` is an experimental pipeline stage that executes a host shell command. It is Python-host-only and not part of the portable Core IR contract. Other hosts must reject it unless they implement the same capability.

## Portable Runtime Value Taxonomy

Hosts may use different internal representations, but they must preserve the same runtime value families and observable behaviors.

### Core values

- Number
- String
- Boolean
- `nil`
- Symbol
- Pair
- List
- Map
- Option family: `none`, `none(reason)`, `none(reason, context)`, `some(value)`
- Promise

### Function and module values

- named/lambda function values
- module namespace values
  - current Python host also includes allowlisted host-backed module namespace values (`python`, `python.json`)

### Runtime capability values

- `stdin`, `stdout`, `stderr`
- raw CLI args via `argv()`
- Flow values
- Ref values
- Process handle values
- MetaEnv values used by the metacircular layer
- Bytes wrapper values
- Zip entry wrapper values
- HTTP serving bridge capability
- Python host handle values
- debugger stdio bridge capabilities

Contract:

- hosts may format/debug-print these differently internally
- host-only metadata must not change Genia-level semantics
- capability values remain capability-oriented, not portable plain data

## Normalized Error Model

Hosts may raise native exceptions/errors internally.
The shared contract is the observable error category and message behavior.

The cross-host error model should normalize at least:

- phase:
  - `parse`
  - `lower`
  - `eval`
  - `cli`
  - `io`
- category:
  - `SyntaxError`
  - `TypeError`
  - `NameError`
  - `RuntimeError`
  - `FileNotFoundError`
- message:
  - preserve shared wording/prefixes that user code and tests rely on
  - examples include:
    - `Ambiguous function resolution`
    - `Flow has already been consumed`
    - `invalid-rules-result: ...`
- optional source location:
  - filename
  - line/column when available

Hosts may attach additional native debugging details, but shared tests should assert only the normalized contract. In the current executable `spec/error/` phase, that asserted surface is limited to `stdout`, `stderr`, and `exit_code`; structured phase/category/source-location fields are not machine-asserted yet.

## Capability Registry Model

Hosts should treat host services as a small named capability registry rather than as language semantics.

Examples:

- stdin/stdout/stderr
- raw argv access
- time/sleep
- randomness
- process/mailbox substrate
- ref synchronization substrate
- bytes/json/zip bridges
- synchronous HTTP serving bridge
- debugger stdio bridge

Rules:

- capability names and observable behavior must stay aligned with shared docs/specs
- pure user-facing transformation logic should prefer prelude/Genia code
- adding a public capability or changing capability semantics requires:
  - `GENIA_STATE.md`
  - relevant core docs/specs
  - `docs/host-interop/HOST_CAPABILITY_MATRIX.md`
  - `spec/manifest.json`

## Allowlisted Host Interop Bridge

Current host interop is a narrow capability bridge, not a second semantic runtime.

Current Python-host contract:

- host interop reuses ordinary `import` plus slash export access
- current allowlisted modules are `python` and `python.json`
- host exports participate in the same call and pipeline model as ordinary Genia callables
- boundary normalization preserves shared Genia semantics:
  - host `None` -> Genia `none`
  - Genia `some(x)` crossing to the host -> converted `x`
  - host exceptions remain explicit errors
- current normalized bridge example:
  - `python.json/loads("{")` raises `ValueError("python.json/loads invalid JSON: ...")`

Important boundary rule:

- Option-aware pipelines continue across the host bridge
- Flow does not implicitly cross the host bridge
- if a host export receives a Flow where it expects an ordinary host value, that remains a type error in the current model

## HTTP Serving Contract (Phase 1)

Current Python-host contract:

- `import web` exposes `web/serve_http(config, handler)` as the minimal host primitive wrapper
- the host bridge owns socket/protocol integration only
- the language boundary uses ordinary Genia maps for both requests and responses
- current request map fields are:
  - `method`
  - `path`
  - `query`
  - `headers`
  - `body`
  - `raw_body`
  - `client`
- current response map fields are:
  - `status`
  - `headers`
  - `body`
- current phase-1 routing/user-visible semantics live primarily in prelude helpers such as:
  - `get`
  - `post`
  - `route_request`
  - `json`
  - `text`
  - `ok_text`
- current limitations:
  - synchronous/blocking only
  - exact-path routing only
  - no middleware
  - no path params
  - no streaming request/response bodies
  - no websockets
  - no async support
- current invalid handler return behavior is normalized to a `500 internal server error` response rather than a large host exception surface

## Flow Contract

Flow semantics are shared language/runtime semantics, even if hosts implement them differently.

Current contract:

- Flow is a runtime value family
- flows are lazy, pull-based, source-bound, and single-use
- `|>` lowers to an explicit Core IR pipeline node with one source plus ordered stages
- consuming the same flow twice raises `RuntimeError("Flow has already been consumed")`
- `take` performs early termination without over-pulling
- the public Flow helper surface is prelude-backed:
  - `lines`
  - `rules`
  - `each`
  - `collect`
  - `run`

Current split to preserve across hosts:

- host/runtime kernel:
  - lazy pull loop
  - single-use enforcement
  - stdin/runtime integration
  - sink/materialization boundaries
- prelude/user-facing layer:
  - stage helpers where feasible
  - `rules(..fns)` orchestration/defaulting/contract glue where feasible

## CLI Contract

CLI behavior is part of the cross-host contract, not an incidental Python detail.

Current required modes:

- file mode: `genia path/to/file.genia`
- command mode: `genia -c "source"`
- pipe mode: `genia -p "stage_expr"` / `genia --pipe "stage_expr"`
- REPL mode: `genia`

Current shared behavior:

- trailing host args are visible as `argv()`
- pipe mode wraps:
  - `stdin |> lines |> <stage_expr> |> run`
- pipe mode rejects explicit `stdin` and explicit `run`
- file/command mode apply the current `main/1` then `main/0` entrypoint convention
- debugger stdio mode is part of the documented host contract for hosts that implement it

## Prelude and Shared Stdlib Contract

Public stdlib behavior should prefer shared Genia/prelude implementation whenever feasible.

That means:

- hosts keep runtime primitives and capability bridges small
- public helper semantics should prefer prelude wrappers and prelude composition logic
- `help("name")` and public discovery should prefer prelude docstrings/autoload metadata over host-local curated registries

Current repository note:

- `src/genia/std/prelude/` is the single canonical stdlib/prelude source tree in this repository
- the Python host loads those bundled files via package resources from the `genia.std` package layout


## Shared Spec Contract

The shared spec suite under `spec/` is the authoritative cross-host validation layer within its implemented scope. The current implemented shared case coverage is `eval` plus `ir` in the Python reference host. Host-local tests are valuable, but do not override shared spec results. Other hosts are not implemented yet.


## Documentation Rule

All documentation must reflect the actual, implemented reality. Do not document planned host behavior as implemented. GENIA_STATE.md is the final authority.
