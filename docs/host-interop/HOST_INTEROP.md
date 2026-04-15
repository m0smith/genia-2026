# Genia Host Interop Contract

This document defines the shared portability contract for Genia hosts.

Python is the current reference host.
Python is the only implemented host today.
Future hosts may differ internally, but they must preserve the same observable Genia semantics at the source/Core IR/runtime boundary.

## Status Terms

- **Implemented host**: runnable host code exists in this repository with tests.
- **Reference host**: the implemented host used as the current semantic baseline.
- **Scaffolded surface**: docs, manifests, placeholders, or layout exist, but no runnable host implementation exists there yet.
- **Planned host**: intended future host work only.

Current status:

- Python is the only implemented reference host.
- The live Python source remains in `src/genia/`, with tests under `tests/` and prelude sources under `src/genia/std/prelude/`.
- `hosts/python/` is a scaffolded future-layout directory, not the live source location.
- Node.js, Java, Rust, Go, and C++ are planned hosts only.
- `spec/` and `tools/spec_runner/` define shared contract scaffolding; they are not a generic multi-host runner implementation yet.

## Authority Order

When multi-host artifacts disagree, use this order:

1. `GENIA_STATE.md`
2. `GENIA_RULES.md`
3. `GENIA_REPL_README.md`
4. shared spec artifacts under `spec/`
5. `docs/host-interop/*`
6. `docs/architecture/core-ir-portability.md`
7. `README.md` and the teaching material under `docs/book/`

Notes:

- `GENIA_STATE.md` remains the final authority for current implemented behavior.
- The shared spec suite is the authoritative cross-host conformance target as it grows.
- Hosts must not treat host-local convenience as stronger than the shared docs/spec contract.

## End-to-End Pipeline

Every host must preserve this model:

1. Source text
2. Lex/parse into a surface AST
3. Lower the surface AST into Genia Core IR
4. Evaluate Core IR against a runtime environment plus host capabilities
5. Produce:
   - a Genia result value
   - stdout/stderr side effects where applicable
   - CLI exit behavior where applicable
   - capability-level effects for Flow, Ref, Process, Bytes/ZIP, debugger stdio, and related runtime bridges

Hosts may use different parser implementations, IR data structures, or execution engines internally.
They must still preserve the same lowered Core IR meaning and the same observable runtime/CLI behavior.

## Core IR Boundary

Core IR is the portability boundary for Genia semantics in this phase.

The frozen minimal Core IR contract is documented in:

- `docs/architecture/core-ir-portability.md`

That means:

- surface parsing may vary internally by host
- AST node classes may vary internally by host
- Core IR meaning must not vary by host
- evaluation behavior after lowering must stay semantically aligned across hosts

Portable host work should therefore ask:

- does this preserve lowering into the same Core IR meaning?
- does this preserve the same runtime result/effect behavior?
- would the shared spec suite observe the same outcome?

Boundary rule:

- minimal lowered Core IR must contain only portable `Ir*` node families in the frozen contract
- host-local post-lowering optimized nodes are allowed only after host-local optimization passes
- host-local optimized nodes must preserve observable Genia semantics and must not be treated as shared contract nodes

## Browser Playground Adapter Scaffold

Browser playground architecture/contract docs exist as scaffolding under:

- `docs/browser/README.md`
- `docs/browser/PLAYGROUND_ARCHITECTURE.md`
- `docs/browser/RUNTIME_ADAPTER_CONTRACT.md`

Current truth:

- these docs do not mean a browser host is implemented
- Python remains the only implemented host
- V1 playground runtime is planned as backend Python execution
- browser-native runtime (JavaScript host or Rust/WASM host) is planned later

Interop rule:

- browser adapter transport may vary by host/runtime placement
- Genia source/Core IR/runtime semantics must remain aligned with shared docs/spec artifacts

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

Hosts may attach additional native debugging details, but shared tests should assert only the normalized contract.

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
  - relevant `docs/book/*`
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

## Shared Spec Rule

The shared spec suite under `spec/` is the authoritative cross-host validation layer.

For Core IR specifically:

- lowering-facing shared checks should validate the minimal portable Core IR boundary
- host-local optimized IR checks may exist as host-local tests, but they do not redefine the shared portable IR contract

Hosts should eventually be able to run the same categories of cases for:

- parse snapshots
- IR snapshots
- eval behavior
- stdout/stderr/exit-code behavior
- CLI behavior
- Flow behavior
- error normalization behavior
- prelude behavior

Host-local tests are valuable, but they do not override shared spec results.

## Documentation Rule

Semantic changes are not complete until the shared docs and learning materials are updated.

At minimum, changes to language/runtime/public behavior must update:

- `GENIA_STATE.md`
- relevant `docs/book/*`
- relevant `docs/host-interop/*`
- `spec/manifest.json` when the shared host contract changes
- `HOST_CAPABILITY_MATRIX.md` when capability coverage changes

Do not document planned host behavior as implemented.
