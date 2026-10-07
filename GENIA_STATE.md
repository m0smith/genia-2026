# Genia — Current Language State (Main Branch)

This file describes what is **actually implemented now** in the Python runtime.

## Authority, scope, and navigation

`GENIA_STATE.md` is the **final authority for implemented Genia behavior**: what exists now, its syntax and semantics, runtime
invariants, execution modes, host support and the portable/host-specific split, maturity classifications, and current limitations.
If it is not here, it is not part of the language. It records no release chronology, issue-by-issue history, test counts, or audit
narrative; those live in the documents below. Source-of-truth order (`AGENTS.md`): this file, `GENIA_RULES.md`, `GENIA_REPL_README.md`,
`README.md`, `spec/*`, `docs/host-interop/*`, `docs/architecture/*`, implementation, `docs/process/run-change.md`.

Where detail lives:

| Topic | Document |
|---|---|
| Release scope, evidence, examples | `docs/releases/R*.md` (index: `docs/releases/README.md`) |
| Approved contracts and designs | `docs/design/` (for example `r14-composable-lifecycle-contract.md`, `r22-exact-numeric-runtime-contract.md`) |
| Release truth audits | `docs/analysis/` |
| Host capability contract and matrix | `docs/host-interop/` (`capabilities.md` is the capability registry) |
| Portable Core IR boundary | `docs/architecture/core-ir-portability.md` |
| Shared executable conformance | `spec/`, `tools/spec_runner/README.md` |
| MCP server | `docs/mcp/`, `docs/design/r28-genia-mcp-contract-threat-model.md` |
| Generated function reference | `docs/reference/` |
| Semantic guard facts and the MCP language-profile registry | `docs/contract/semantic_facts.json` (a guard and projection source, never authority) |
| Exact text displaced from this file (provenance only) | `docs/state-record/README.md` |

Retired section numbers are mapped to their current location in `docs/state-record/crosswalk.md`. Stable semantic anchors (`<!-- anchor: state:... -->`) identify sections independently of heading numbers; the MCP language-profile
registry and its tests refer to them. Section numbers are legacy identifiers and may be cross-referenced by other documents.
`docs/state-record/` is a non-authoritative provenance layer: it never defines behavior and is not part of the truth hierarchy.

## 0) Multi-host status
<!-- anchor: state:host-status -->

Implemented today:

- **Python is the full-language reference host; C++ is the bounded R27 production host.**
- Shared semantic-spec contract categories are:
  - parse
  - ir
  - eval
  - cli
  - flow
  - error

- The implemented shared Semantic Spec System executes **parse**, **ir**, **eval**, **cli**, **flow**, and **error** cases. The runner
  compares normalized `stdout`, `stderr`, and `exit_code` for eval, cli, flow, and error cases; portable normalized Core IR output for
  IR cases; and, for parse cases, the normalized AST (exact match for `kind: ok`) or error type plus message substring (`kind: error`).

- The working Python implementation lives in `src/genia/` (core runtime), `src/genia/std/prelude/`, `tests/`, and `hosts/python/` (adapter,
  normalization, and category execution modules). Multi-host documentation and spec scaffolding live in `docs/host-interop/`,
  `docs/architecture/core-ir-portability.md`, `spec/`, `tools/spec_runner/README.md`, and `hosts/`.
- The formal host capability registry contract is `docs/host-interop/capabilities.md`: the authoritative reference for capability names,
  Genia surface, input/output shapes, normalized error behavior, and portability status.
- **Multi-host conformance infrastructure (R16, complete).** Contract: `docs/design/r16-multi-host-conformance-infrastructure-contract.md`;
  policy: `docs/strategy/roadmap/multi-host-conformance-policy.md`; release page `docs/releases/R16.md`.
  - A versioned subprocess host-adapter protocol (`tools/spec_runner/protocol.py`) carries `parse`/`lower`/`eval`/`cli` requests and
    responses; evaluated-program output travels only inside `result` fields. An adapter can self-report only `ok` or `unsupported`;
    `protocol_error`, `crash`, and `timeout` are always derived by the runner from process and JSON facts.
  - `python -m tools.spec_runner --host '<command>'` runs applicable cases through that protocol. The in-process default path (no
    `--host`) is a developer-optimization path, not the conformance definition.
  - A mandatory `capabilities` operation and an optional per-case `requires:` field gate cases: a case requiring a capability the host
    does not declare exactly `supported` is reported `unsupported` without invoking the adapter, never silently skipped or counted as
    passing. Multi-file cases require `multi_file_eval` (the optional `eval.input.modules` shape); unknown input fields are invalid.
  - `tools/spec_runner/revision.py` classifies a host's declared `contract_revision` against local git history only: an exact match is
    `current` (pinned-conformance evidence), a real older commit is `resolvable_ancestor` (current-main compatibility only), and an
    unresolvable declaration stops the run with exit code 1.
  - `tools/spec_runner/evidence.py` and `--evidence <path>` emit one deterministic per-host JSON evidence document (revision, protocol
    version, capabilities, applicable-case count, full outcome taxonomy); identical runs give byte-identical evidence.
  - `tools/spec_runner/host_parity_gate.py` with `spec/known_host_gaps.json` is a CI/process gate (`.github/workflows/host-parity.yml`)
    over those evidence documents at `spec/manifest.json` optional-capability granularity: a capability the C++ host does not declare
    `supported` needs a matching entry with a GitHub issue, affected host, affected tests or spec area, reason, and removal condition; a
    stale entry for a now-supported capability fails; any nonzero `fail`/`protocol_error`/`crash`/`timeout`/`invalid` count fails. It adds
    no protocol, evidence format, or capability registry.
  - The Python reference host is itself proven through the same protocol (`hosts/python/protocol_adapter.py`), with the full-suite proof
    kept in `tests/spec/test_python_protocol_adapter_parity_762.py` (`full_conformance`, run nightly or by dispatch). Test-suite
    organization changes there alter no case discovery, protocol behavior, or semantic coverage.
  - [`m0smith/genia-cpp`](https://github.com/m0smith/genia-cpp) is the first external production host (bounded floor, see the C++ host
    entry below); `hosts/cpp/` here is a pointer to that repository (`hosts/cpp/README.md`).

Scaffolded or planned, not implemented as hosts:

- Node.js, Java, Rust, Go: planned only, not implemented.
- `hosts/python/` is the adapter location, but the core runtime remains in `src/genia/`.
- No second production host implements the full language. `m0smith/genia-cpp` is the bounded R27 production host (see below); other
  external-host proofs are Python-reference-host evidence or non-semantic protocol fixtures.

**Maturity:**

- Shared host contract is **Partial**: executable shared spec coverage exists for `eval`, `ir`, `cli`, first-wave `flow`, initial `error`,
  and initial `parse` behavior in the Python reference host and, for the bounded C++ floor, as recorded in the C++ host entry below.
- Semantic Spec System is **Experimental**: the file format, runner, and initial case inventory exist for those categories.
- Flow behavior is implemented in Python, and shared semantic-spec coverage for flow is **active but partial**: first-wave cases cover
  lazy pull-based behavior through early termination, single-use enforcement, deterministic output, `evolve(init, f)`, `refine(..steps)`,
  `rules(..fns)` compatibility, `step_*`/`rule_*` equivalence, selected rule defaulting, `map`/`filter`/`scan`, Seq-compatible `each`/
  `collect`/`run`/`reduce` terminals, and bounded `drop |> take |> collect` finalization. Advanced Flow behavior is not covered by shared specs.
- IR stability remains **Partial**: the minimal portable Core IR contract is documented with field-level lowering invariants (bare `none`
  lowers with `reason=null`; `none()` reason wrapped as `IrQuote`; canonical `lhs.name` lowers to `IrBinary(op=SLASH, named_access=true)`
  for narrow named access, never general field-path lookup, while ordinary division lowers as `IrBinary(op=SLASH)` without
  `named_access`; legacy `lhs/name` compatibility is removed; `IrAssign` appears directly in `IrBlock.exprs`), the Python runtime guards
  that boundary, and shared cases validate the full portable node family, including `quasiquote` with `unquote`/`unquote_splicing`.

**Explicit limitations:**

- No browser runtime or playground is implemented; browser artifacts are documentation only.
- Shared semantic-spec case files exist under `spec/eval/`, `spec/ir/`, `spec/cli/`, `spec/flow/`, `spec/error/`, and `spec/parse/`. Parse
  coverage is limited to stable, already-implemented syntax forms and expands only when new forms are explicitly added and tested.
- Flow is a lazy, pull-based, single-use runtime value; async, multi-port, and advanced Flow features are not present. Flow orchestration
  supports `refine(..steps)` (preferred) and `rules(..fns)` (compatibility), identically; step/rule helpers exist as `step_*` (preferred)
  and `rule_*` (compatibility). Flow shared-spec coverage is first-wave only.
- The CLI contract covers file, command, pipe, and REPL modes as described; no shell tokenization, `$1`/`$2`/`ARGV`-style, or advanced CLI
  features exist.
- **R26-1 REPL portability contract:** the portable `repl` boundary (`docs/design/r26-cpp-repl-contract.md`) is no-argument mode selection,
  persistent successful bindings across complete submissions, multiline submission (Python's completeness heuristic is not standardized),
  canonical debug-result echo (including `none("nil")`) to `stdout`, normalized diagnostics to `stderr` with session recovery, successful
  EOF termination, and no implicit `main` dispatch. Banner/prompt text, terminal editing/history, signals, colon commands, and cross-stream
  timing stay host-local; `repl()` writes no banner or prompts to `stdout` when `stdin` is not an interactive tty. Shared evidence is three
  capability-gated `cli` cases declaring `requires: [repl]`.

- **C++ host (`m0smith/genia-cpp`), current state.** The bounded production floor is parser, AST lowering, command/file CLI, local open
  functions, Ref/Cell/local Process, a scripted REPL, Bytes/UTF-8 and strict JSON data bridges, Flow phase 1, and `genia -p` pipe mode, each
  declared `supported` only for the shared cases carrying the matching `requires:` capability. It is not Python feature parity; pinned
  evidence and gaps live in `docs/releases/R24.md` through `R27.md`, `spec/known_host_gaps.json`, and the host parity gate.
  - **Scripted REPL:** one environment retained across complete submissions, normalized failure reporting, recovery; interactive
    prompt/banner/history stays host-local.
  - **Data bridge contract** (`docs/design/r26-cpp-data-bridge-contract.md`): `bytes_utf8` (`utf8_decode` for well-formed UTF-8 only; `<bytes N>`
    display) and `json_strict` (full grammar, nesting bounded at exactly 128 containers for decode and encode, duplicate-key rejection with the
    key in context, a leading BOM not accepted as whitespace, sorted-key 2-space-indented encode, exactly one outer `json` layer). Compatibility JSON
    (`json_parse`/`json_stringify`/`json_pretty`/`parse_jsonl_record`, capability `json_compat`) is **not portable** and stays Python-host-only;
    ZIP is out of R26. `spec/manifest.json` declares `bytes_utf8`, `json_strict`, and `json_compat`.
  - **Flow phase 1 and pipe mode** (`flow_phase_1`, `cli_pipe_mode`): lazy single-use Flow with `lines`, `evolve`, `map`/`filter`/`take`/`drop`/
    `scan`/`keep_some`/`each`, and `collect`/`run`/`reduce`. C++ limits: no trailing script arguments after `-p <expr>`; `argv()` only in pipe
    mode; `upper`/`trim`/`parse_int` decide ASCII input only; `tee`/`merge`/`zip`, `rules`/`refine`, list-form `scan`, Flow display, and a
    pipeline inside call arguments are unsupported; config/model/Template/JSON cross-release Flow and pipe cases stay Python-host-only.
  - The HTTP server and outbound HTTP are not part of the C++ floor; both remain Python-host-only with tracked C++ gaps.
- **Python reference-host repairs recorded for the data bridge:** decoding or computing a Decimal whose `10 ** exponent` expansion would exceed the
  numeric resource bound raises `NumericResourceLimitError` before expansion; the portable type-name table names a bare symbol `"symbol"`;
  `json_parse`, `parse_jsonl_record`, `json_stringify`, and `json_encode` normalize `RecursionError` from deep nesting to their existing
  diagnostic shapes (`none("json-parse-error", ...)`, `err("invalid_jsonl_record", ...)`, `none("json-stringify-error", ...)`,
  `err("json_nesting_too_deep", ...)`). These changed no value mapping, limit, or Outcome shape for well-behaved input.

- The current shared semantic-spec runner asserts `stdout`, `stderr`, and `exit_code` for eval cases.
- The current shared semantic-spec runner asserts `stdout`, `stderr`, and `exit_code` for CLI cases.
- The current shared semantic-spec runner asserts `stdout`, `stderr`, and `exit_code` for error cases.
- The current shared semantic-spec runner compares normalized portable Core IR output for IR cases.
- The current shared semantic-spec runner compares normalized parse output for parse cases: exact AST for `kind: ok`, type and message substring for `kind: error`.
- Only the minimal portable Core IR node families are used in the contract; host-local optimized nodes (e.g., `IrListTraversalLoop`) are excluded.

**GENIA_STATE.md is the final authority for implemented behavior. All other docs/specs must align with this contract.**
## 0.1) Browser playground status
<!-- anchor: state:browser -->

Implemented today:

- browser playground architecture and runtime-adapter documentation scaffolding exists under:
  - `docs/browser/README.md`
  - `docs/browser/PLAYGROUND_ARCHITECTURE.md`
  - `docs/browser/RUNTIME_ADAPTER_CONTRACT.md`
- app scaffold documentation exists under:
  - `apps/playground/README.md`

Planned, not implemented yet:

- V1 browser playground app that runs Genia via a backend service using the current Python reference host
- browser-native runtime backend for the playground using either:
  - a JavaScript host, or
  - a Rust/WASM host

Clarifications:

- no browser playground application runtime is implemented in this repository yet
- browser work in this phase is architecture/contract scaffolding only
- browser execution is planned to use the Python reference host on a backend service in the current V1 direction
- browser execution remains a host-capability adaptation concern and does not define a new Genia dialect
- `examples/ants_web.genia` is a browser-viewer demo served by the current host-backed HTTP helper; it is not a browser-native Genia runtime or playground
## 1) Shared Conformance — Semantic Spec System
<!-- anchor: state:conformance -->

LANGUAGE CONTRACT:

- The Semantic Spec System defines observable behavior for the following categories:
  - parse (**active**, executable shared spec files; initial coverage only)
  - ir (**active**, executable shared spec files)
  - eval (**active**, executable shared spec files)
  - cli (**active**, executable shared spec files)
  - flow (**active**, executable shared spec files; first-wave coverage only)
  - error (**active**, executable shared spec files; initial coverage only)
- `eval`, `ir`, `cli`, first-wave `flow`, initial `error`, and initial `parse` behavior are implemented as executable shared spec files in the Python reference host.
- The spec is authoritative for covered categories; uncovered behavior is not guaranteed.

- Coverage is partial and experimental. The spec is authoritative for covered categories; uncovered behavior is not guaranteed and may differ in future hosts.
- Eval shared cases (`spec/eval/`) cover deterministic command-source output: final rendered results, `stdout`/`stderr` separation, stdin-fed cases,
  Option rendering and pipeline lifting/short-circuit, pattern-matching families (first-match, literals, wildcard/variable binding, list/tuple/map,
  option, guard, glob, named reusable patterns), list/Seq-compatible helper behavior, selected validation helpers (`collect_validated/1`,
  `validate_each/2`, optional/required field and nested-path diagnostics, Experimental, initial coverage only), and deterministic failures with exact
  `stderr` and `exit_code` (including Flow/value boundary errors such as `each` given a list, `first` given a Flow, `reduce` given a non-Seq value).
- Flow cases (`spec/flow/`) run through command-source execution in the Python host adapter; the first-wave inventory is summarized in section 0.

- Error cases (`spec/error/`) run through the eval execution path and require `stdout: ""`, exact `stderr`, and `exit_code: 1`; informational `notes`
  are not machine-asserted. Error coverage is initial: pattern miss, guard-all-fail, malformed-glob, named-pattern errors, and selected `validate_each/2`
  misuse; structured phase/category fields are not machine-asserted.
- CLI cases (`spec/cli/`) prove deterministic non-interactive file mode, `-c` command mode, `-p` pipe mode, `main(argv())` dispatch, trailing `argv()`,
  explicit `stdin`/`run` rejection, pipe-mode guidance diagnostics, selected native `--test` outcomes, and three `requires: [repl]` REPL cases; every
  other REPL scenario is uncovered. The observable CLI and error contracts are limited to `stdout`, `stderr`, and `exit_code`.
- Parse cases (`spec/parse/`) call the Python host parse adapter directly (exact AST for `kind: ok`; error type exact and message substring for
  `kind: error`); IR cases (`spec/ir/`) compare normalized portable Core IR before host-local optimization (host-local nodes such as
  `IrListTraversalLoop` are excluded).

- Normalization is limited to line endings for `stdout` and `stderr` (`\r\n` and `\r` become `\n`); comparison is otherwise exact (error cases:
  `stdout` must be `""`, `exit_code` must be `1`). YAML loading prefers `PyYAML` and can fall back to a Ruby YAML bridge. The runner accepts
  `-v`/`--verbose` (spec name before execution, then `<name>\t<elapsed>s`).
- Uncovered or partial categories are not guaranteed and may differ in future implementations.

**Host implementation location:** the working Python implementation lives in `src/genia/`, `tests/`, and `src/genia/std/prelude/`; `hosts/python/` is the
host adapter layer (not the core runtime). `hosts/python/adapter.py::run_case(spec: LoadedSpec) -> ActualResult` is the canonical adapter entrypoint,
wired through `tools/spec_runner/executor.py::execute_spec`; all spec categories route through it.

**GENIA_STATE.md is the final authority for implemented behavior. All other docs/specs must align with this contract.**

---

## 0.2) Repository documentation tooling (pointer)

Documentation tooling is repository process, not Genia language or runtime semantics. Docs are staged for MkDocs (Material theme) by
`tools/stage_docs_for_mkdocs.py` and published by the GitHub Actions docs workflow (pull requests stage, validate, and build; pushes to
`main` also deploy to GitHub Pages, and publish the generated Function Reference mirror to the Wiki only when the optional `WIKI_TOKEN`
secret is configured). Source annotations and the host documentation registry consumed by `tools/gen_function_docs.py` remain authoritative
for `docs/reference/**` and the Wiki mirror; generated pages are never edited by hand. `tools/lint_doc.py` is a deterministic `@doc` linter
(rules DOC001-DOC009; `--require-coverage` requires canonical documentation and a category for every public binding) and
`tests/test_doc_style_sync.py` keeps `docs/style/doc-style.md`, the cheatsheets, and the linter constants aligned. The governing style
guide is `docs/style/doc-style.md`; the displaced detailed text is in `docs/state-record/tooling-and-examples.md`.

## 1) Execution model
<!-- anchor: state:execution-model -->

- programs are expression sequences
- parser AST stays close to surface syntax, then lowers into a tiny Core IR before evaluation
- Core IR is the current portability boundary
  - lowering keeps pipelines explicit as ordered stage sequences rather than nested calls
  - lowering keeps Option constructors explicit as `IrOptionSome(...)` / `IrOptionNone(...)`
  - the minimal Core IR contract is explicitly frozen in `docs/architecture/core-ir-portability.md`
  - lowered portable IR is validated before host-local optimization in the Python reference host
- the current Python host may apply small post-lowering optimization rewrites such as `IrListTraversalLoop`
  - those optimized nodes are Python-host implementation details, not the minimal shared Core IR contract
- assignment is supported at top level and in lexical scopes (`name = expr`)
- blocks evaluate expressions in order and return the last value
- no statement/declaration split at runtime level
- CLI entry points support three execution modes:
  - file mode: `genia path/to/file.genia`
  - command mode: `genia -c "expr_or_program_source"`
  - pipe mode: `genia -p "stage_expr"` / `genia --pipe "stage_expr"`
  - REPL mode: `genia` (no file/command arguments)
- when no `-c`/`-p` mode is selected, the first non-mode argument must be a source file path (option-like tokens are treated as malformed mode/arg combinations unless passed after `--`)
- in file/command/pipe mode, trailing host CLI arguments are exposed to programs as `argv()` (list of strings)
  - command mode accepts both bare positionals (`a`) and option-like args (`--pretty`) as trailing args
- pipe mode runs the provided stage expression over `stdin |> lines`, then consumes the final Flow automatically
  - pipe mode expects a single stage expression, not a full standalone program
  - explicit unbound `stdin` and explicit unbound `run` are rejected in pipe mode with a clear error
  - per-item functions used as bare stages (e.g. `parse_int`) are diagnosed with targeted suggestions (`map(parse_int)` or `keep_some(parse_int)`)
  - reducers used as bare stages (e.g. `sum`) are diagnosed with `collect |> sum` or `-c/--command` guidance
  - non-flow final results (e.g. from `collect`) are reported with `-c/--command` guidance
  - `collect_validated` record-pipeline aggregate results have a targeted diagnostic that names the original stage expression and suggests `-c/--command` mode or explicit print-with-empty-Flow
  - broken pipe on stdout exits cleanly with no traceback or stderr noise
- after file/command source evaluation, runtime entrypoint convention is:
  - if `main/1` exists, call `main(argv())`
  - else if `main/0` exists, call `main()`
  - else keep existing result behavior (no implicit call)
  - pipe mode bypasses the `main` convention and runs the wrapped flow directly
## 2) Implemented runtime value categories

This is the current runtime value model in `main`. It is intentionally descriptive, not a new static type system.
### Core values

- Number
- Promise
- Symbol
- String
- Boolean
- Pair
- Outcome — `none`, `some(value)`, `some(value, context)`, `err(reason, context?)`
  - `none` is shorthand for `none("nil")`
  - legacy surface `nil` also normalizes to `none("nil")`
  - `some(value, context)` — successful presence with optional context metadata (Experimental)
  - `err(reason, context?)` — recoverable value-level failure; not a runtime error (Experimental)
- List
- Map
  - map literals and `map_*` builtins produce the same runtime map value family
  - map values are persistent and opaque at runtime (`<map N>`)
- Sheet — immutable, columnar, named-column value (**Experimental**)
- Validation helper results are ordinary Outcome values over ordinary map records:
  - `field` may be a flat field name or a simple dot-joined nested field path such as `"patient.name"` or `"patient.address.zip"`; this is validation-helper lookup and diagnostic metadata only, not a general field-path language feature
  - `validate_required(field, record)` returns `some(record)` when `record` has `field`, otherwise `err("missing required field", {row: ...?, field: field, reason: "missing required field"})`
  - `validate_field(field, predicate, expected, record)` returns `some(record)` when the field exists and `predicate(value) == true`, otherwise a recoverable diagnostic `err(...)`; non-callable predicates remain runtime errors
  - `validate_optional(field, record)` and `validate_optional(field, record, validator)` validate optional record fields (**Experimental**):
    - missing field returns `none({field: field, reason: quote(missing_optional_field)})`
    - present field with no validator returns `some(value, {field: field})`
    - present field with validator: `some(...)` results are preserved unchanged; `err(...)` results keep their meaning, and a `field` entry in an error context is prefixed to the full nested path when applicable; `none(...)` result is normalized to `err(quote(optional_field_validator_returned_none), {field: field, validator_result: result})`
    - non-map record, non-callable validator, and validator returning non-Outcome are runtime errors
- `validate_record(record, validators)` and `validate_record(record, validators, context)` compose field validators over one record and return a record-level Outcome (**Experimental**):
  - `record` must be a map-like Genia value; non-map input is a runtime misuse error
  - `validators` must be a map-like value whose keys are field paths and whose values are validator callables; each callable receives the original `record` and must return an Outcome
  - non-map `validators`, non-callable validator values, and non-Outcome validator returns are runtime misuse errors
  - validators execute in deterministic Genia map iteration order; all validators run even when earlier ones return `err(...)`
  - `some(value)` field results contribute the validated field value to the `clean_record` under the validator map key
  - `none(...)` field results are successful absence and do not contribute a value to `clean_record`
  - `err(...)` field results are aggregated into record-level diagnostics; each diagnostic includes `field`, `status: quote(error)`, `reason`, and `context`
  - if no validators return `err(...)`, returns `some(clean_record, record_context?)` where `clean_record` contains only present validated values
  - if one or more validators return `err(...)`, returns `err(quote(record_validation_failed), record_context_with_diagnostics)`
  - optional caller-provided `context` is preserved in the record-level Outcome
  - does not mutate the original record; does not add a schema DSL, Sheet behavior, Flow collector, or value-template integration
- `validate_each(source, validator)` applies a callable validator to each item in a list or Flow source and returns one Outcome per item (**Experimental**, issue #392, issue #415, issue #416):
  - `source` must be a list or a Flow; non-list/non-Flow input is a runtime `TypeError`
  - `validator` must be callable; non-callable validators raise a runtime `TypeError`
  - classifies each source item before invoking the validator:
    - upstream `err(...)` items are preserved unchanged; the validator is not called
    - upstream `none(...)` items are preserved unchanged; the validator is not called
    - upstream `some(payload)` items: the validator is called with the unwrapped `payload`; the validator result is returned as the item output
    - plain records and values: the validator is called with the item directly; validator runtime errors propagate unchanged
  - every validator result must be an Outcome; non-Outcome validator results raise `TypeError("validate_each expected validator to return an Outcome, received <type> at index <n>")`
  - list input returns a list of Outcome values in source order; output length equals input length
  - Flow input returns a lazy derived Flow of Outcome values; validation happens during consumption; single-use and finalization behavior follow existing Flow semantics
  - does not aggregate; aggregation remains the job of `collect_validated`
  - `validate_each/3`, Sheet behavior, and validation DSL are not implemented in this phase
- `collect_validated(results)` is an explicit terminal helper for Outcome-aware validated pipelines (**Experimental**):
  - accepts a list or Flow (Seq-compatible source)
  - every item must be an Outcome; non-Outcome items raise a runtime `TypeError`
  - `some(value)` and `some(value, context)` append `value` to `clean`; `some` context is ignored in this first version
  - `none(...)` appends a diagnostic with `kind: quote(skipped)`
  - `err(...)` appends a diagnostic with `kind: quote(error)`
  - diagnostics have `index` (zero-based source position), `kind` (symbol), `reason`, and `context` (`some(ctx)` when present or `none("nil")` when absent)
  - result shape: `{clean: [...], diagnostics: [...]}`
  - does not create Sheets
  - does not change Outcome semantics or pipeline short-circuit behavior
  - does not change `keep_some` or existing validation helpers
### Function / module values

- Function
  - named functions are first-class values
  - lambdas evaluate to ordinary callable runtime values
- Module
  - `import mod` / `import mod as alias` bind module namespace values
  - module values are distinct from maps and are accessed with narrow dot named access (`mod.name`)
  - current Python host interop reuses this same module value model:
    - `import python`
    - `import python.json as pyjson`
### Callable values / callable behaviors

- Function values are callable in the ordinary way
- Map values also have callable lookup behavior
  - `m(key)` -> stored value or `none("missing-key", {key: key})`
  - `m(key, default)` -> stored value when key exists, otherwise `default`
  - other arities → `TypeError("map callable expected 1 or 2 args, got N")`
- String values can act as callable map projectors
  - `"key"(m)` -> map lookup behavior (`value` or `none("missing-key", {key: key})`)
  - `"key"(m, default)` -> stored value when key exists, otherwise `default`
  - other arities → `TypeError("string projector expected 1 or 2 args, got N")`
  - non-map first argument → `TypeError("string projector expected a map-like target as first argument")`
- This callable layer is behavior-based, not a single unified nominal type
  - maps stay maps even when callable
  - strings stay strings even when used as projectors

### Runtime capability values

Current-state summary of the Experimental R10-R14 runtime capabilities (ticket-by-ticket text is preserved verbatim, as non-authoritative
provenance, in `docs/state-record/capability-records.md`). Release pages: `docs/releases/R10.md` to `R14.md`; contracts:
`docs/design/r10-configuration-protected-value-contract.md`, `r11-ai-composition-contract.md`, `r12-retrieval-grounding-contract.md`,
`r13-configuration-resolution-contract.md`, `r14-composable-lifecycle-contract.md`. All are ordinary callables over ordinary values and
Outcomes with no new syntax, annotation, parser/AST/Core IR node, or ambient capability; execution modes (eval, file, command, pipe, import,
native-test, serve) inject no ambient provider, credential, or authority. LANGUAGE CONTRACT: the closed value shapes, validation ordering,
one-attempt rule, and normalized Outcomes below are portable obligations. PYTHON REFERENCE HOST: implemented with explicit host-injected
opaque capabilities and deterministic offline fixtures; shared/multi-host conformance remains Partial and Python is the only host.

- **Release status.** R10 is release-complete. R11 E11-1 through E11-8 are complete. R12 is release-complete through E12-9. R13 is release-complete through E13-8.
  R14 is complete (section 9.8). Their APIs remain Experimental, shared/multi-host conformance remains Partial, and Python is the only implemented host for them.
- **R10 configuration and protected values.**
  - `config_provider(sources)` builds an explicit opaque immutable snapshot and returns `some(provider)` or a normalized `err(...)`.
    Descriptors are `{kind: quote(values), values: map}` and capability-backed `{kind: quote(environment)}`; the first source containing a key
    wins (highest to lowest precedence); all descriptors and literal strings are validated before any host snapshot is acquired. Construction
    copies every source once, so later mutation is invisible and lookup performs no host access. Providers display as `<config-provider>`,
    compare by identity, and are not map keys. `{kind: quote(environment)}` snapshots `os.environ` on the Python host; a host may report it unavailable.
  - `config_get(provider, key)` returns `some(exact_string)` (including `some("")`) or context-free `none("config-missing")`;
    `config_get_or(provider, key, default)` invokes the zero-argument `default` exactly once, only for `none("config-missing")`: an ordinary
    result is wrapped in `some(...)`, a default `some`/`none`/`err` is preserved unnested, and callability is checked only when the default is selected.
    Valid keys are non-empty strings without NUL; normalized diagnostics never include the key, source content, raw value, or host detail.
  - `secret_get(provider, key, purpose)` protects a found string (including empty) in one reserved outer `secret` carrier; `purpose` is a non-empty
    symbol. `secret_get_or(...)` follows the same missing-only, exactly-once rule and protects ordinary/`some` successes once while preserving `none`/`err`.
    `protected_match("secret", value)` returns `some(value)` holding the exact protected subject (otherwise `none("representation-mismatch")`);
    generic `represent`, `representation_match`, and `strip_representation` reject the reserved `secret` facet.
  - Protected equality observes carrier identity only: a carrier equals itself and its aliases, independently acquired carriers are unequal even with
    equal payloads, and protected values are not map keys. Calls, returns, containers, pipelines, Seq, Flow, Sheet cells, refs, and process messages
    transport protected leaves exactly, with no hidden taint. Diagnostic rendering recursively substitutes `<protected>`; Format replacements, output
    sinks, JSON, Sheet CSV, resource writes, HTTP responses, and ordinary host conversion reject protected leaves before any effect
    (`json_encode` returns `err("protected-value", {operation: "json-encode"})`; a rejected resource write writes zero payload bytes).
  - `declassify(authority, protected_value)` is the sole payload-revealing operation. The authority is a host-injected opaque value that must match the exact
    provider identity and allow the protected purpose (it displays as `<declassification-authority>`, cannot be copied or used as a map key, and is rejected by
    every sink above); success removes exactly one protected layer, returns an ordinary value, and records a host-local non-sensitive audit event; a mismatch
    reveals nothing and an audit failure fails closed. Serve-entry evaluation and any explicit provider snapshot complete before listener activation; requests do not refresh configuration.
- **R13 configuration ergonomics.**
  - `config_view(provider, prefix)` and `secret_view(provider, prefix, purpose)` return one-argument callables; construction validates and captures the provider,
    prefix (empty allowed; NUL is misuse), and (secret) purpose, performing no lookup or host operation. Each call takes a non-empty NUL-free logical name,
    forms the key by exact `prefix + name`, and performs one existing lookup, returning the exact `config_get`/`secret_get` Outcome. No caching, fallback, named access, or ambient lookup.
  - `config_args(args)` takes an explicit list of strings (normally `argv()`). Before the first standalone `--` it parses exact long-option/value pairs (names are
    letter-led ASCII alphanumeric segments joined by single hyphens; values are the next string, even if empty or option-looking); later strings are ignored. Names normalize
    hyphen to underscore and uppercase; repeated or colliding keys fail atomically. Success is `some({kind: quote(values), values})`; malformed data is exactly
    `err("config-source-invalid", {source_kind: quote(arguments), stage: quote(parse)})`; a non-list or non-string member is misuse. Short/grouped options, `--name=value`, and positionals before `--` are not accepted.
  - A `{kind: quote(dotenv), path, required}` descriptor (non-empty NUL-free `path`, boolean `required`) is read at most once, in source order, during provider construction; lookup never re-reads.
    Optional absence contributes an empty source at its index; required absence or read failure is `config-provider-failure`, an unavailable capability `config-source-unavailable`, bad UTF-8 or grammar
    `config-source-invalid`, with context only `{source_index, source_kind: quote(dotenv), stage: quote(acquire|decode|parse)}`. Accepted grammar: one leading BOM, LF/CRLF, a final unterminated line,
    blank and comment lines, ASCII space/tab around entries, ASCII identifier keys, exact-duplicate rejection, and unquoted/single-quoted/double-quoted values with only `\\`, `\"`, `\n`, `\r`, `\t` escapes;
    no interpolation, `export`, multiline values, or refresh.
  - `config_standard(overrides, args)` (optional `.env`) and `config_standard(overrides, args, dotenv_path)` (required exact path) normalize `args`, then build the fixed source list: overrides (index 0) > arguments (1) >
    environment (2) > `.env` (3), keeping indices for empty or absent sources. Invalid explicit types are misuse before acquisition; malformed argument syntax returns its `config-source-invalid` Outcome before any host acquisition; the result is the exact provider Outcome, atomic and snapshotted once.
- **R11 AI model invocation.**
  - `model(provider, config, credential, authority)` is the sole public AI entry point and returns an ordinary one-argument callable. `provider` is an opaque host-injected capability with no source constructor;
    `config` is exactly `{id: nonempty string, timeout_ms: integer 1..300000}`; `credential` is one R10 protected string; construction validates only and performs no declassification, audit, or attempt.
  - A request is the closed map `{messages, output}`: a non-empty list of closed text messages with role `system|user|assistant`, and `output` either `{kind: quote(text)}` or `{kind: quote(json), schema, template}` where
    `schema` carries exactly one outer R9 `json` representation accepted by `json_schema` and `template` is a callable one-argument Outcome Template. Invocation validates the whole request before declassifying; a valid invocation
    declassifies the credential at the authorized boundary, records the R10 audit, and makes exactly one synchronous provider attempt (no implicit retry, fallback, repair, reprompt, streaming, or tool loop).
  - Success is `some({message, finish_reason, usage})`: assistant text, `finish_reason` in `stop|length|filtered|other`, and `usage` of exact non-negative token counts or `none("model-usage-unavailable")`. Structured success decodes the
    one assistant text with `json_decode`, calls the Template once on the decoded value (its success payload is ignored), and returns content `{kind: quote(json), value}` retaining one outer `json` facet; a decode or Template
    `none`/`err` becomes `err("model-structured-output-invalid", {stage: quote(json_decode)|quote(template), outcome})` and a non-Outcome Template result is runtime misuse.
  - Absence is `none("model-no-response")`; normalized failures are `model-timeout`, `model-rate-limited`, `model-rejected`, `model-transport-failure`, and `model-response-invalid` (malformed observations use
    `{stage: quote(provider_response)}` or the precise stage), with contexts defined in `GENIA_RULES.md`; no raw bodies, headers, request ids, exception text, keys, or credentials are retained.
  - The Python host provides an offline deterministic fixture (shared specs opt in with `fixtures: [r11_model]`) and one explicit Google Gemini Developer API adapter over `v1beta models.generateContent` REST: `config.id` is the
    percent-encoded model path, `timeout_ms` the single standard-library HTTPS attempt, the declassified credential goes only to `x-goog-api-key`, redirects are refused, there is no SDK, general HTTP API, or provider factory visible to source.
  - Conversation is application-owned `scan(step, initial_state, source)` composition (`examples/r11_flow_conversation.genia`): input is `{kind: quote(message), message: {role: quote(user), content}}` or `{kind: quote(stop), reason}`;
    state is `{messages, turn, status, last}` starting from `{messages: [], turn: 0, status: quote(active), last: none("conversation-not-started")}`. An active message calls an ordinary prompt over the full history and the model once,
    increments `turn`, records the exact Outcome, and appends an assistant message only for `some(response)`; `none`/`err` sets failed status; a stop records `none("conversation-stopped", {reason})` with no call; stopped and failed states
    return unchanged. A list source gives an eager list of states, a Flow source a lazy single-use Flow. `apply_raw` deliberately dispatches model Outcomes as data. The executable validated-pipeline proof is `examples/r11_validated_pipeline_proving_case.genia`.
- **R12 retrieval and grounding (provenance substrate only).**
  - `chunk(chunker, document)`: `document` is the closed map `{id: nonempty string, text, meta: json_represented_object}`; `chunker` is called exactly once with `document.text` and returns a list of closed `{offset, length}` maps (non-negative
    integer offsets, positive integer lengths, booleans excluded) counted in Unicode code points, each wholly inside the text, order preserved, overlap and repetition allowed. Success is `some([chunk, ...])` with chunks `{text, source: {doc_id, offset, length}, meta}` (exact original slice, exact
    represented metadata); an empty span list is `some([])`; the first bad span is `err("chunk-invalid", {stage: quote(span), index})`; a malformed document, non-callable chunker, callback exception, or non-list result is runtime misuse.
  - `embed(provider, config, credential, authority)`, `index(...)`, `retrieve(...)`, and `rerank(...)` each validate and capture one opaque capability, a closed config (`embed`: `{id, space, timeout_ms}`; others `{id, timeout_ms}`), one protected credential, and one authority, and return an ordinary
    callable without declassification, audit, or attempt. Each valid invocation validates locally first, declassifies just in time through its exact purpose (`quote(embed_call)`, `quote(index_call)`, `quote(retrieve_call)`, `quote(rerank_call)`), and makes one synchronous deterministic attempt (no retry, fallback, batching, stream, cache, clock, randomness, or network).
    Provider exceptions normalize once to `<stage>-transport-failure/{kind: quote(other)}`; timeout, rate-limit, and rejection observations keep their exact R12 contexts; malformed observations are non-sensitive `<stage>-response-invalid` with a `stage` field. No result retains credentials, provider identity, bodies, or exception text; capabilities render as opaque `<...-provider>`.
  - **Embed:** the callable takes `{kind: quote(chunk), chunk}` or `{kind: quote(query), text}` (non-empty query text) and returns `some({chunk, embedding})` or `some({text, embedding})` with `embedding = {vector, dims, space}` (non-empty finite numbers, `dims` equal to the vector length, `space` equal to the config space); a malformed nested chunk is
    `err("chunk-invalid", {stage: quote(document)})` before declassification; response stages are `provider_response|vector|dims|space|input_identity`.
  - **Index:** takes a non-empty list of embedded chunks with equal positive `dims` and non-empty `space`; mixed dimensions or spaces return `err("index-embedding-incompatible", {kind: quote(dimension)|quote(space)})` before any attempt. Success is only `some(index_handle)`, an opaque `<index-handle>` that retains private compatibility identity, space/dims, and indexed chunks
    and cannot be constructed, inspected, compared, keyed, copied, serialized, or persisted from source.
  - **Retrieve:** takes one index handle, one explicit query embedding (never implicit), and integer `k` in `1..1000`; compatibility checks run in the order capability identity, space, dimension and return `retrieve-capability-incompatible/{kind: quote(index_handle)}` or `retrieve-embedding-incompatible/{kind: quote(space)|quote(dimension)}` before declassification. Non-empty success is `some([retrieved_chunk, ...])` (at most `k`, finite backend-native
    scores, provider best-first order, exact indexed provenance); an empty result is exactly `none("retrieval-no-results")`.
  - **Rerank:** takes a non-empty query string and a list of retrieved chunks; empty evidence returns `some([])` with no declassification or attempt. Success may reorder and replace scores with finite reranker-native numbers only and must preserve the exact multiset of chunk values (repeats included); otherwise `err("rerank-response-invalid", {stage: quote(result)})`.
  - **Grounded composition** is application-owned (`examples/r12_grounded_context_answer.genia`, ordinary functions, not builtins): a grounded context is the closed `{question, content, evidence}`, a grounded answer the closed `{answer, sources, evidence}` built only from an exact successful R11 `some(response)` (answer text from `response.message.content`), `sources` being the
    first occurrence of each exact-equal `{doc_id, offset, length}` in evidence order; `none`/`err` model Outcomes propagate unchanged. Citation labels, numbering, prompt runtime, RAG framework objects, persistence, and provider registries are not implemented. Cross-mode proofs: `examples/r12_cross_mode_grounded_proving.genia`.
- **R14 lifecycle and outbound HTTP** capabilities (`lifecycle_*`, `http_operation`, `web.http_send`, `web.send_annotated`) are summarized in section 9.8.

- MetaEnv
  - `empty_env()` returns a host-backed metacircular environment value (`<meta-env>`)
  - metacircular environments support lexical lookup/definition/rebinding for the phase-1 evaluator layer
- Flow
  - Flow is a real runtime value family (`<flow ...>`)
  - Flow runtime (Phase 1) is implemented
  - flows are lazy, pull-based, source-bound, and single-use
- Ref
  - refs are synchronized host-backed runtime cells
  - `ref_get` / `ref_update` may block until a value is present
- Process
  - `spawn` returns a host-backed process handle value
- Bytes
  - `utf8_encode` and ZIP helpers produce opaque bytes wrapper values
  - Bytes is not a legal map key; rejection is the exact clean diagnostic
    `bytes cannot be a map key`, never a raw host class name (R26-2
    `bytes_utf8` contract, `docs/design/r26-cpp-data-bridge-contract.md`
    section 2)
- ZipEntry
  - `zip_entries` returns opaque zip entry wrapper values
- HTTP serving
  - `import web` exposes module exports such as `web.serve_http(config, handler)` for the host-backed blocking HTTP capability
  - requests and responses are represented as ordinary Genia maps at the language boundary
- Python host handles
  - `python.open` returns opaque Python file-handle values (`<python file>`)
  - these are capability-style values intended only for passing back to allowlisted Python host exports
### Current consistency notes

- Maybe/absence behavior is now unified around one explicit family:
  - present value: `some(value)`
  - absence value: `none(reason, meta?)`
  - plain `none` and legacy `nil` both normalize to `none("nil")`
  - compatibility aliases remain where naming migration was staged (`get?`, `first_opt`, `nth_opt`)
  - canonical maybe-aware access/search APIs use structured absence directly (`get`, `first`, `last`, `nth`, string `find`, `find_opt`, `parse_int`)
  - lookup surfaces such as `map_get`, dot access, callable map/string lookup, and `cli_option` now also return structured `none(...)` on missing results
- structured `none(...)` metadata is still absence metadata, not a separate control-flow family.
- absence metadata is inspectable through:
  - `absence_reason(none(...))` -> `some(reason)`
  - `absence_context(none(...))` -> `some(context)` when present, otherwise `none("nil")`
  - `absence_meta(none(...))` -> `some({reason: ..., context: ...?})`
- Outcome extends the current `some` / `none` model with `err(...)` for recoverable failure (Experimental):
  - `some(value, context)` — present value with optional context metadata; context is preserved through pipeline lifting
  - `err(reason, context?)` — recoverable value-level failure; not a runtime error; renders to stdout with exit_code 0
  - `err(...)` is not absence: `none?(err(...))` returns `false`; existing absence helpers do not treat `err(...)` as `none(...)`
  - constructor arity: `some` accepts 1 or 2 args; `err` requires exactly 1 or 2 args; invalid arity is a runtime error
- `some(pattern)`, `none(...)`, and `err(...)` constructor patterns are implemented in pattern matching.
  - context-aware forms `some(value, ctx)`, `none(reason, ctx)`, `err(reason, ctx)` bind only when context is present
- ordinary function calls short-circuit on `none(...)` arguments unless the callee explicitly handles absence.
  - lambda expressions whose body delegates to a known Option-aware function (for example `(o) -> unwrap_or(0, o)`) are recognized as absence-aware and bypass short-circuiting
- list higher-order functions (`reduce`, `map`, `filter`) are pure prelude implementations using `apply_raw` for callback invocation; `none(...)` list elements are delivered to the callback without short-circuit
  - `reduce` accepts both list and Flow (Seq-compatible) as its third argument; `none(...)` as initial accumulator is not short-circuited
  - this means `map((o) -> unwrap_or(0, o), [none("a"), some(2)])` correctly returns `[0, 2]` instead of propagating `none`
  - `filter((o) -> some?(o), [some(1), none("x"), some(3)])` correctly returns `[some(1), some(3)]`
- pipelines short-circuit on `none(...)` and `err(...)`, and automatically lift ordinary stages over `some(...)`.
  - non-Option stage results are wrapped back into `some(...)`
  - Option stage results (`some(...)` / `none(...)`) are preserved as-is
  - `err(...)` short-circuits value-transforming stages and propagates unchanged; `err(...)` is not converted to `none(...)`
  - `some(value, context)` context metadata is preserved through ordinary pipeline lifting
  - explicitly Option-aware stages (for example `unwrap_or`, `map_some`, `flat_map_some`, and `then_*`) still receive Option values directly
- Pipeline + Option invariants are locked by black-box tests under `tests/cases/option/invariant_*.genia`:
  - raw values stay raw through all stages (no implicit Option promotion)
  - `some(x)` auto-lifts through ordinary stages; Option-returning stages are preserved as-is
  - `none(...)` short-circuits absolutely — all remaining stages skipped, including Option-aware ones
  - `none(...)` reason and context metadata preserved exactly through short-circuit
  - recovery must wrap the whole pipeline: `unwrap_or(default, expr |> stages)`, not `expr |> stages |> unwrap_or(default)`
- Flow vs Value invariants are locked by black-box tests under `tests/cases/flow/invariant_*.genia`:
  - lists through value-only stages stay lists (no implicit flow promotion)
  - flows through flow-only stages stay flows (must `collect` to see a list)
  - Option composes orthogonally: per-item Options use `keep_some` in flows; pipeline-level `some`/`none` propagation works the same in both worlds
- `Seq` is a semantic compatibility category for ordered value production.
  - Seq is not a public runtime value, type constructor, syntax form, helper, or Core IR node.
  - In this phase, the implemented Seq-compatible public values are lists and Flow.
  - Lists are eager and reusable.
  - Flow is lazy, pull-based, source-bound, and single-use.
  - Iterators and generators are host implementation details, not portable Genia values.
  - The Python reference host uses an internal `GeniaSeq` helper to model ordered-source consumption lifecycle; this does not create a public Seq surface.
  - Seq compatibility does not change pipeline call shape or Option-aware pipeline behavior.
  - Explicit bridges such as `lines` and Flow-side `collect` / `run` still define Value<->Flow crossings.
  - `stdin` is a host-backed input capability, not a Seq-compatible public value; it must be adapted through `lines(stdin)` before participating in Flow-style ordered processing.
  - Direct use of `stdin` as a source to `each`, `collect`, or `run` fails with a Genia-facing diagnostic naming list or Flow as the accepted values and pointing to `stdin |> lines`.
  - `each`, `collect`, and `run` accept Seq-compatible public values:
    - `each(f, list)` returns a lazy tap-style Flow stage; when consumed, it calls `f(item)` for each item in order, ignores callback results, and emits the original items unchanged.
    - `each(f, Flow)` remains a lazy tap-style Flow stage that emits original items unchanged.
    - `collect(list)` returns the same ordered list values; `collect(Flow)` materializes emitted Flow items into a list.
    - `run(list)` traverses the list without printing and returns `nil`; `run(Flow)` consumes the Flow to completion and returns `nil`.
    - non-list/non-Flow inputs fail with a Seq-compatible diagnostic naming list or Flow as the accepted public values.
  - `map`, `filter`, `take`, `drop`, and `scan` also accept Seq-compatible public values; non-list/non-Flow inputs fail with a Seq-compatible diagnostic naming list or Flow as the accepted values. `scan(list)` returns list; `scan(Flow)` returns Flow.
  - The Python reference host implements `_seq_transform(initial_state, step, source)` as an internal kernel primitive for shared list/Flow transformation mechanics; it is not an ordinary user-callable Genia name and does not create a public Seq surface.
  - `_seq_transform` accepts list or Flow sources and returns the same source kind: list in -> list out, Flow in -> Flow out.
  - `_seq_transform` calls `step(state, item)` for each processed item; the step must return a map with optional `state`, `emit`, and `halt` fields.
  - Missing `state` keeps the current state, missing `emit` emits `[]`, and missing `halt` means `false`.
  - `emit` must be a list of zero, one, or many output values; `halt: true` emits the current step's values and then stops the whole transform without pulling later source items.
  - Invalid `_seq_transform` step results raise runtime errors prefixed with `invalid-seq-transform-result:`.
  - PYTHON REFERENCE HOST: adjacent Flow `map` / `filter` stages may be represented by an internal fused Flow object that composes callbacks over one upstream source. This is an implementation optimization only; it adds no public Seq value, no fusion API, no new syntax, no Core IR node, no runtime flags, and no observable `trace` / display label change.
  - PYTHON REFERENCE HOST: `_ensure_seq_compatible(name, source)` is an internal kernel primitive that validates a value is a Seq-compatible source and returns it unchanged; it accepts list and GeniaFlow only, raises a Seq-compatible TypeError for all other values, and does not consume or pull from a Flow during validation. It is registered via `env.set_internal` and is not accessible from ordinary Genia user code.
  - `as_seq(value)` is a public explicit adapter that converts supported values into Seq-compatible ordered sources; it does not introduce a public Seq runtime type or constructor.
    - `as_seq(list)` returns the list value unchanged; list reusability is preserved.
    - `as_seq(string)` returns a list of one-character strings in iteration order; strings remain atomic unless passed to `as_seq`.
    - `as_seq("")` returns an empty list.
    - Unsupported inputs (e.g., number, boolean, map) fail with `TypeError: as_seq expected a list or string, received <type>.`
    - Flow input is not supported in this phase; Flow remains Seq-compatible through existing `each`, `collect`, `run`, `map`, `filter`, `scan`, `reduce` without `as_seq`.
    - `as_seq` does not make strings implicitly Seq-compatible; `collect("abc")` and similar remain invalid.
    - `as_seq` does not introduce a `Char` type; each emitted element is a one-character Genia string value.
  - Maturity: Partial; list and Flow behavior is implemented, while Seq remains semantic terminology rather than a separate public surface. `as_seq` for list and string input is implemented and tested.
- pipeline debugging helpers are implemented as prelude-level identity stages:
  - `inspect(value)` logs and returns `value` unchanged
  - `trace(label, value)` logs `label` plus `value` and returns `value` unchanged
  - `tap(fn, value)` runs `fn(value)` for side effects and returns `value` unchanged
  - these helpers do not force Flow materialization by themselves; they preserve explicit/lazy Flow boundaries unless user-provided side-effect callbacks consume a Flow value
- public Map/Ref/Process/IO helper names are also prelude-backed wrappers over host-backed runtime primitives, so `help("name")` and higher-order use follow the user-facing stdlib surface rather than raw host bindings.
- public validation helper names `validate_required`, `validate_field`, `validate_optional`, `validate_record`, `validate_each`, `diagnostic_error`, `diagnostic_skipped`, `diagnostic_reason`, and `diagnostic_field` are prelude-backed wrappers over small host-backed checks/constructors; record validation helpers return Outcome values for user-data problems, diagnostic constructors return ordinary maps, and programmer misuse remains a runtime error.
- `collect_validated` is a host-backed terminal builtin (Experimental) registered directly in the global environment; it consumes a Seq-compatible source of Outcome items and returns `{clean: [...], diagnostics: [...]}`; it does not alter Outcome semantics, pipeline short-circuit behavior, Sheet semantics, or existing validation helpers.
- public Web helper names `serve_http`, `get`, `post`, `route_request`, `response`, `with_headers`, `cors`, `json`, `text`, `ok`, `ok_text`, `bad_request`, and `not_found` are also thin prelude wrappers in this phase; the underlying HTTP transport integration remains host-backed
- public Flow helper names `lines`, `evolve` (experimental), `tee`, `merge`, `zip`, `scan`, `keep_some`, `keep_some_else`, `rules`, `each`, `collect`, and `run` are also thin prelude wrappers in this phase; the underlying Flow behavior remains host-backed and the related underscore kernels are internal to trusted prelude/runtime code
- limited Python host interop is implemented in this phase:
  - it uses the existing module/import model rather than new syntax
  - supported host modules are currently allowlisted: `python`, `python.json`
  - unsupported host module names fail clearly instead of falling through to arbitrary host import
- `help()` now serves as a small public-surface overview that points users toward registered autoloaded prelude families rather than a hand-maintained API inventory
- naming discipline for current APIs:
  - new `?`-suffixed APIs are boolean-returning
  - maybe-returning APIs should use Option values without `?`
  - `get?` remains as the current compatibility exception
- Callable behavior currently crosses nominal value boundaries:
  - functions are callable as functions
  - maps are callable as lookup values
  - strings are callable as map projectors
- Flow, stdout/stderr, MetaEnv, Ref, and Process handles are runtime capability values, not plain data in quite the same sense as numbers, lists, or maps.
- lexical assignment currently does not protect builtin/root names from rebinding inside the same root environment; that is real current behavior.
- The current model is implemented and tested as one integrated design in this phase:
  - Core IR carries explicit pipeline and Option nodes
  - pipeline evaluation owns automatic Option propagation
  - Flow remains an explicit runtime value family rather than an implicit pipeline mode
  - host interop is a narrow capability bridge layered onto the same call/pipeline semantics
- This is still not a full static type/protocol system; the coherence is semantic rather than nominal.
### Sheet values (Experimental)

**LANGUAGE CONTRACT:**

A Sheet is an immutable, columnar, named-column value. It is distinct from Flow, Seq, and ordinary lists.

A Sheet has:
- zero or more named columns
- deterministic column order
- columns represented as ordered sequences of values
- all columns aligned by row index
- a deterministic row count
- immutable update semantics; all operations return new Sheets

A Sheet is not:
- a lazy or streaming value
- a reactive or formula-driven spreadsheet
- a Seq-compatible source in this phase
- a replacement for Flow or lists

**PYTHON REFERENCE HOST:**

Implemented as `GeniaSheet` — a frozen dataclass with tuple-backed column storage. Column names may be any hashable Genia value (symbols are the intended default). Column order is deterministic from construction order.

**Maturity:** Experimental — minimal immutable columnar core only.

**Explicit limitations:**
- No reactive cells, formula plans, joins, grouping, sorting, or spreadsheet UI semantics.
- `some(...)`, `none(...)`, and `err(...)` are stored as ordinary cell values; no automatic Outcome propagation across columns.
- `derive` rejects an existing column name.
- `where` predicates must return a boolean; non-boolean predicate results fail clearly.
- Construction requires lists as column values; other Seq-compatible values are not accepted in this phase.
- Sheets are not Seq-compatible sources in this phase.
## 3) Implemented syntax and expression forms
<!-- anchor: state:syntax-forms -->

- literals: number, string (single/double quoted + triple-quoted multiline), boolean, `nil`, `none`
  - numeric source classification (R21 E21-1, see section 9.21): `DIGIT+` classifies as Integer source; `DIGIT+ "." DIGIT+`, `DIGIT+` exponent, and `DIGIT+ "." DIGIT+` exponent (`e`/`E`, optional sign, `DIGIT+`) all classify as Decimal source; `.5` and `5.` are not numeric literals; a malformed exponent (`1e`, `1e+`) is a deterministic `SyntaxError`
- quote special form: `quote(expr)`
- quasiquote special form: `quasiquote(expr)`
- delay special form: `delay(expr)`
- variables
- function calls
- unary operators: `-`, `!`
- binary operators: `+ - * / % < <= > >= == != && ||`
- pipeline operator: `|>`
- matcher check operator: `value @? matcher` — applies `matcher(value)`; returns `some(value)` when matcher succeeds, preserves `none(...)` and `err(...)` unchanged; never returns boolean — Experimental
- matcher assert operator: `value @! matcher` — applies `matcher(value)`; returns the original `value` when matcher succeeds; raises a runtime error on `none` or `err`, preserving the `err` reason in the diagnostic — Experimental
- matcher composition operator: `matcher_a & matcher_b` — creates a composed matcher that applies `matcher_a` first; short-circuits on `none` or `err`; if `matcher_a` succeeds, applies `matcher_b` to the original subject; returns `some(subject)` when both matchers succeed — Experimental
- block expressions: `{ ... }`
- list literals: `[a, b, c]`
- map literals: `{ key: value }` with identifier/string keys (`name: 1` sugar for `"name": 1`)
- module import: `import mod`, `import mod as alias`
  - imports are cached by module name in `loaded_modules` (repeat imports/aliases reuse the same module value instance)
  - dotted host module names are supported through ordinary identifiers (for example `import python.json as pyjson`)
  - module resolution order for user modules: (1) requester-relative — `<requester-dir>/<mod>.genia` when the importing source has a known filesystem path; (2) BASE_DIR-relative — `<BASE_DIR>/<mod>.genia`; (3) packaged stdlib — bundled `std/prelude/<mod>.genia`; (4) `FileNotFoundError("Module not found: <mod>")`
  - requester-relative resolution is skipped when the importing source filename is `<memory>` or `<command>`; when the filename is `<pipe>`, resolution proceeds from the current working directory
  - import cycle detection raises `RuntimeError("Module import cycle detected while loading <mod>")`; the cycling module is not committed to the cache
- list spread in literals: `[..xs]`, `[1, ..xs, 2]`
- call spread: `f(..xs)`
- lambdas: `(x) -> x + 1`
- lambda parameter position accepts existing Genia patterns as a single-arm match, such as `([a, b]) -> a + b`, `({name}) -> name`, and `(some(x)) -> x`
- varargs lambdas: `(..xs) -> xs`, `(a, ..rest) -> rest`
- prefix annotations are now a usable binding-metadata surface: `@name value`
  - one or more consecutive annotations attach to the next top-level function definition or simple-name assignment
  - parsed annotations produce explicit AST nodes (`Annotation`, `AnnotatedNode`)
  - metadata attachment to bindings is implemented for `@doc`, `@meta`, `@since`, `@deprecated`, and `@category`
  - no macro behavior or compile-time transform behavior is implemented

Pipeline (Phase 2) evaluation model:

- `|>` is a dedicated pipeline stage form in Core IR/runtime in this phase
- Core IR shape is explicit:
  - `x |> f |> g` lowers to one pipeline node with a source plus ordered stages
  - pipelines are not represented as nested call nodes
- ordinary call shape is preserved:
  - `x |> f` calls `f(x)`
  - `x |> f(y)` calls `f(y, x)` (left value appended as the last argument)
  - `x |> expr` calls `expr(x)` when `expr` is valid in ordinary call-callee position
  - example: `record |> "name"` behaves like `"name"(record)`
- left associative: `a |> f |> g`
- newline-separated pipeline formatting is accepted:
  - `x`
    `|> f`
    `|> g`
  - `x |> `
    `f |> g`
- automatic Outcome propagation is part of pipeline evaluation:
  - if a stage input is `none(...)`, the remaining stages do not execute and the same `none(...)` is returned
  - if a stage input is `err(...)`, the remaining stages do not execute and the same `err(...)` is returned; `err(...)` is not converted to `none(...)`
  - if a stage input is `some(x)` and the stage is not explicitly Option-aware, the stage receives `x`
  - when a lifted stage returns non-Option `y`, the pipeline continues with `some(y)`
  - when a lifted stage returns `some(...)` or `none(...)`, that Outcome result is preserved
  - when a lifted stage lifts `some(x, context)`, context metadata is preserved in the resulting `some(result, context)`
  - if a stage result is `none(...)`, the remaining stages do not execute and the same `none(...)` is returned
- pipeline failure diagnostics now include:
  - 1-based stage index
  - stage rendering when available
  - stage source span when available
  - pipeline mode classification (`Value mode`, `Flow mode`, or `Explicit bridge mode`)
  - received runtime type names (Option values display as `some(inner_type)` recursively)
  - when the pipeline input is `some(x)`, errors distinguish the auto-unwrapped value from the original: "pipeline value was some(int) (auto-unwrapped)" vs "stage received int"
- pipeline-visible function modes are interpreted as:
  - Value -> Value
  - Flow -> Flow
  - explicit Value <-> Flow bridge
- recovery/defaulting wraps the whole pipeline result rather than living as a later pipeline stage:
  - `unwrap_or("unknown", record |> get("user") |> get("name"))`
  - `unwrap_or(0, fields(row) |> nth(5) |> parse_int)`
- Flow remains explicit:
  - Flow values still come only from explicit bridge/stage functions such as `lines`
  - Value↔Flow conversion is not implicit
### Shell pipeline stage (`$(...)`, Python-host-only, implemented)

- `$(command)` is a pipeline stage that executes `command` via the host shell
- the pipeline value is converted to stdin bytes: strings→UTF-8, lists/flows→newline-joined display, numbers/bools→display
- stdout is captured as a UTF-8 string; a single trailing `\n` is stripped
- empty stdout returns `none("empty-shell-output")`
- non-zero exit code raises `RuntimeError("shell stage: command failed (exit <code>): <command>")`
- Option propagation: `none(...)` short-circuits (command not executed); `some(x)` unwraps, result re-wrapped
- `$(...)` outside a pipeline raises `SyntaxError`
- **Implemented and supported on Python host only.**
- **Not part of portable Core IR or shared multi-host contract.**
- Distinct from, and not superseded by, `execution.process` (section 9.40):
  `$(...)` remains nonportable host-shell text execution with no argv
  structure of its own; `execution.process` is structured direct
  execution (an exact argv, no shell, no PATH search) under a portable
  contract currently implemented by Python. Neither wraps or replaces the
  other.
## 4) Functions and dispatch

- named functions are first-class values
- multiple definitions by arity shape are allowed
- varargs named functions are supported (`f(a, ..rest) = ...`)
- named functions may use either `=` or `->` for single-expression bodies, or `{ ... }` for block bodies
- lambda single-expression bodies may start on the next line after the `->` token
- bindings may carry metadata maps discoverable through `meta("name")`
- doc lookup is available through `doc("name")`
- lexical assignment uses the same `name = expr` surface syntax
  - if `name` already exists in the reachable lexical environment chain, assignment updates the nearest existing binding
  - otherwise assignment creates `name` in the current scope
  - blocks create lexical scopes
  - function parameters are ordinary assignable lexical bindings
  - closures capture lexical environments, so rebinding is visible across calls to the same closure
  - assignment is limited to simple names in this phase
  - invalid targets such as `(a + b) = 3` raise `SyntaxError("Assignment target must be a simple name")`
  - module evaluation uses its own module environment, so module top-level assignment does not rebind names in the importing root environment
- named function definitions may include an optional leading docstring string literal after `=`
  - example:
    ```genia
    inc(x) = """
    # inc

    Increment by one.
    """ x + 1
    ```
  - docstrings are metadata, not runtime body expressions
  - function bodies may still use the ordinary parenthesized case-expression style after a docstring
    - example:
      ```genia
      sign(n) = """
      # sign
      """ (
        0 -> 0 |
        _ -> 1
      )
      ```
  - for multi-clause named functions: zero docstrings = undocumented; one docstring total = valid; repeated identical docstrings = valid; conflicting docstrings raise a clear `TypeError`
- prefix annotations now attach metadata to bindings in this phase
  - supported built-in annotations are:
    - `@doc "text"` -> stores `{"doc": "text"}`
    - `@meta { ... }` -> merges map entries into binding metadata
    - `@since "0.4"` -> stores `{"since": "0.4"}`
    - `@deprecated "message"` -> stores `{"deprecated": "message"}`
    - `@category "name"` -> stores `{"category": "name"}`
    - `@test "description"` -> stores `{"test": "description"}`; marks the annotated zero-argument function for native test discovery in native test mode
    - `@route {method: ..., path: ...}` -> stores validated inert Experimental R8 route metadata on a top-level named function
    - `@server {host: ..., port: ..., max_requests: ...}` -> stores normalized inert Experimental R8 server configuration metadata on a top-level assignment
  - annotation metadata attaches to the binding name for top-level functions and top-level assignments
  - unannotated rebinding preserves existing metadata on that binding
  - annotated rebinding merges new metadata over existing metadata, with the last annotation winning for duplicate keys
  - `doc("name")` returns the current doc string or `none("missing-doc", {name: ...})`; `@doc` metadata takes priority over legacy inline docstrings
  - `meta("name")` returns the metadata map or `none("missing-meta", {name: ...})` for undefined names
  - `help("name")` prefers `@doc` metadata text over legacy function docstrings and also shows selected metadata fields such as category/since/deprecated
  - no macros, compile-time transforms, or annotation-driven evaluator rewrites are implemented
  - `@test` annotations are discovered by the native test runner; `@test` does not execute by itself and does not affect language evaluation behavior outside native test mode; see section 9.2
- resolution behavior:
  - exact fixed arity beats varargs
  - if multiple varargs candidates match and neither is more specific, runtime raises `TypeError("Ambiguous function resolution")`
- named accessor (phase 1):
  - `lhs.name` is the canonical narrow named-access form; it is not general field-path lookup
  - legacy `lhs/name` compatibility has been removed
  - supported LHS runtime kinds: module values, map values
  - map missing key => `none("missing-key", {key: "name"})`
  - module missing export => clear error
  - non-identifier RHS (for example `lhs/(1 + 2)`) raises a clear `TypeError`
  - this does not add general member/index access
## 4.1) Python host interop layer (implemented, allowlisted)

- Genia currently exposes a minimal Python-only host interop layer through the existing module system.
- supported host imports in this phase:
  - `import python`
  - `import python.json`
  - `import python.json as alias`
- current allowlisted `python` exports:
  - `python.open`
  - `python.read`
  - `python.write`
  - `python.close`
  - `python.read_text`
  - `python.write_text`
  - `python.len`
  - `python.str`
- current allowlisted `python.json` exports:
  - `loads`
  - `dumps`
- host exports participate in ordinary calls and pipeline stages without special pipeline rules.
- boundary conversion rules:
  - Genia string/number/bool -> Python scalar
  - Genia list -> Python list recursively
  - Genia map -> Python dict recursively
  - Genia `some(x)` -> converted host value for `x`
  - Genia `none(...)` -> Python `None`
  - Python `None` -> Genia `none("nil")`
  - Python list/tuple -> Genia list recursively
  - Python dict -> Genia map recursively
- host file objects cross the boundary only as opaque Python handle values.
- current safety limits:
  - no arbitrary host import
  - no general member access syntax
  - no unrestricted Python eval/exec surface
  - disallowed host modules raise `PermissionError("Host module not allowed: <name>")`
- current error behavior:
  - host exceptions remain explicit errors unless the host result is actually `None`
  - `None` maps to Genia `none("nil")` and therefore participates in ordinary call/pipeline absence propagation
  - invalid JSON through `python.json/loads` raises `ValueError("python.json/loads invalid JSON: ...")`
- callable data (phase 1):
  - maps are callable lookup values:
    - `m(key)` returns stored value or `none("missing-key", {key: key})`
    - `m(key, default)` returns stored value when key exists, otherwise `default`
    - arity other than 1 or 2 raises `TypeError`
  - strings are callable map projectors:
    - `"key"(m)` returns `map_get(m, "key")` behavior (`value` or `none("missing-key", {key: key})`)
    - `"key"(m, default)` returns stored value when key exists, otherwise `default`
    - first argument must be map-like (runtime map value); non-map targets raise clear `TypeError`
    - arity other than 1 or 2 raises `TypeError`
## 4.1) Symbols and quote

- Symbol is a real runtime value family
  - symbols are distinct from strings
  - symbols print as bare names (`x`, not `"x"`)
  - symbols compare by value/name
  - symbols are valid stable map keys
- `quote(expr)` is implemented as a special form
  - it does not evaluate `expr`
  - it converts syntax to runtime data
- current quote conversion rules:
  - identifier -> symbol
  - number / string / boolean / `nil` / `none` -> corresponding literal runtime value
  - list literal -> pair chain ending in `nil`
  - map literal -> runtime map with quoted keys and values
  - unary / binary / call forms -> tagged application pair chain `(app <operator> <arg1> ...)`
  - quoted identifier map keys become symbols; quoted string map keys stay strings
- there is no quote sugar (`'x`) in this phase
- `quasiquote(expr)` is implemented as a special form
  - it constructs the same runtime data shapes as `quote(expr)`
  - `unquote(expr)` evaluates `expr` and inserts the result at the nearest active quasiquote depth
  - nested `quasiquote(...)` forms are depth-sensitive; inner `unquote(...)` applies only to the nearest surrounding quasiquote
  - `unquote_splicing(expr)` is implemented only for quasiquoted list literal contexts
  - current `unquote_splicing` input families are:
    - ordinary list values
    - `nil`
    - nil-terminated pair chains
  - `unquote(...)` and `unquote_splicing(...)` outside quasiquote raise clear runtime errors
  - `quasiquote(unquote_splicing(...))` is invalid because splicing requires a quasiquoted list context
 - current quoted representation also supports these evaluator-facing tagged forms:
   - assignment -> `(assign <name-symbol> <value-expr>)`
   - lambda -> `(lambda <params-structure> <body-expr>)`
   - block -> `(block <expr1> <expr2> ...)`
   - match/case -> `(match (clause <pattern> <result>) ...)` or `(match (clause <pattern> <guard> <result>) ...)`
   - application -> `(app <operator> <operand1> <operand2> ...)`
 - ordinary quoted list/pair data remain plain pair/list data and are distinct from tagged quoted applications
## 4.2) Pairs

- Pair is a real immutable runtime value family
  - `cons(x, y)` creates a pair
  - `car(pair)` returns the head field
  - `cdr(pair)` returns the tail field
  - `pair?(x)` reports whether a value is a pair
  - `null?(x)` reports whether a value is the normalized empty-pair terminator (`none("nil")`, including legacy `nil`)
- pair equality is structural
- lists can be represented as pair chains ending in `nil`
- ordinary list literals remain separate List values in this phase
## 4.3) Promises

- Promise is a real runtime value family
  - `delay(expr)` is a special form that does not evaluate `expr` immediately
  - `delay(expr)` captures the lexical environment in the same way closures do
  - `force(value)` forces promise values and returns non-promise values unchanged
  - forcing is memoized after the first successful evaluation
  - if forcing raises, the promise remains unforced and a later `force(...)` retries evaluation
  - promises are ordinary delayed values and are separate from Flow
  - promises are reusable and memoized; flows are source-bound, single-use, and pipeline-oriented
## 4.4) Streams (stdlib)

- Streams are implemented as a stdlib/prelude layer, not as a runtime value family
  - a stream node is `cons(head, delay(tail_expr))`
  - in prelude practice, stream construction is exposed as `stream_cons(head, tail_fn)`
  - the tail is forced explicitly with `stream_tail(s)` / `force(cdr(s))`
- current public stream helpers are:
  - `stream_cons(head, tail_fn)`
  - `stream_head(s)`
  - `stream_tail(s)`
  - `stream_map(f, s)`
  - `stream_take(n, s)`
  - `stream_filter(pred, s)`
- `stream_take` materializes the requested prefix as an ordinary list
- streams are distinct from Flow:
  - streams are pure data built from Pair + Promise
  - Flow is the runtime pipeline/IO model and remains separate
## 4.5) Programs-as-data helper layer (stdlib)

- Genia now ships a minimal metacircular expression helper layer in `src/genia/std/prelude/syntax.genia`
- these helpers operate on the same quoted/quasiquoted data representation produced by `quote(expr)` and `quasiquote(expr)`
- the host-backed substrate in this phase is intentionally small:
  - parser/lowering/quote/quasiquote runtime representation
  - symbol/self-evaluating runtime shape detection
  - metacircular pattern-lowering support used by the evaluator
- most user-facing quoted-form predicates, selectors, and branch/match structural helpers now live in prelude/Genia code
- current public helpers are:
  - predicates:
    - `self_evaluating?`
    - `symbol_expr?`
    - `tagged_list?`
    - `quoted_expr?`
    - `quasiquoted_expr?`
    - `assignment_expr?`
    - `lambda_expr?`
    - `application_expr?`
    - `block_expr?`
    - `match_expr?`
  - selectors:
    - `text_of_quotation`
    - `assignment_name`
    - `assignment_value`
    - `lambda_params`
    - `lambda_body`
    - `operator`
    - `operands`
    - `block_expressions`
  - match selectors:
    - `match_branches`
    - `branch_pattern`
    - `branch_has_guard?`
    - `branch_guard`
    - `branch_body`
- current supported expression families in the helper layer are:
  - self-evaluating literals
  - symbol/variable expressions
  - quote / quasiquote forms
  - assignments
  - lambdas
  - applications
  - blocks
  - match/case expressions
- quoted source applications are now represented and detected with the stable `(app ...)` tag
- `operands(expr)` returns the operand tail of `(app ...)` as a pair-chain sequence of operand expressions
- `match_branches(expr)` returns the branch tail of `(match ...)` as a pair-chain sequence of quoted branches
- `branch_guard(branch)` raises a clear `TypeError` when used on an unguarded branch
## 4.6) Metacircular evaluator (stdlib)

- Genia now ships a minimal metacircular evaluator layer in `src/genia/std/prelude/eval.genia`
- the host-backed substrate in this phase remains:
  - metacircular environment values and lexical mutation support
  - metacircular pattern lowering/matching support
  - ordinary evaluator/runtime substrate and `apply` fallback machinery
- evaluator dispatch and most user-facing semantic glue live in prelude/Genia code
- current public evaluator/environment names are:
  - `empty_env`
  - `lookup`
  - `define`
  - `set`
  - `extend`
  - `eval`
  - `apply` (extended in `src/genia/std/prelude/fn.genia` to handle metacircular compound procedures as well as ordinary callables)
- `eval(expr, env)` currently supports these quoted expression families:
  - self-evaluating literals
  - symbol/variable expressions
  - quoted expressions
  - assignments
  - lambdas
  - match/case expressions
  - applications
  - blocks
- metacircular environments follow current lexical scoping rules:
  - `define` binds in the current frame
  - `set` rebinds the nearest existing lexical name or defines in the current frame when missing
  - `extend` creates a child lexical environment for lambda application
  - closures capture the defining metacircular environment
- metacircular compound procedures are represented as tagged pair data:
  - `(compound <params> <body> <env>)`
- metacircular matcher procedures are represented as tagged pair data:
  - `(matcher <match-expr> <env>)`
- current evaluator limitations:
  - `eval` is only defined for the supported expression families above
  - unsupported quoted forms raise a clear runtime error instead of silently expanding evaluator coverage
## 4.7) R20 open functions and extensible pattern dispatch (Experimental, R20 complete)
<!-- anchor: state:open-functions -->

R20 adds one concept: an **open function interface** is an identity-bearing
ordinary callable whose immutable clause set is assembled from ordered local
clauses and explicitly selected cross-module contributions. See
`docs/design/r20-open-functions-contract.md` (approved semantics) and
`docs/design/r20-open-functions-syntax-ir-design.md` (approved syntax and
Core IR).

- **Local declaration and repeated clauses.**
  - `open name(<pattern>, ...) = <body>` declares a new open interface; the
    first clause of an interface must carry the `open` keyword.
  - Every subsequent bare `name(<pattern>, ...) = <body>` in the same module,
    for a name already declared `open`, is a repeated clause appended to that
    interface, in source order. `open`/repeated clauses must form one
    contiguous run of top-level statements — a later bare
    `name(<pattern>...) = body` for a name whose run already ended does not
    silently reopen it.
  - `<pattern>` reuses the existing lambda-parameter pattern grammar
    verbatim: identifier bind, wildcard `_`, literal, tuple/list/map
    sub-pattern, `some(...)`/`err(...)`, named-pattern use, and one final
    `..rest` for varargs. An optional `? guard` may follow the closing `)`.
  - A single clause whose body is a grouped `(pat) -> body | (pat) -> body`
    case-with-pipe over a plain-identifier header is flattened at parse time
    into one clause per arm, so grouped and repeated local clause syntax
    normalize to an identical ordered clause list (contract §3.1).
  - Example (the release's required acceptance case):
    ```genia
    open gcd(a, 0) = a
    gcd(a, b) = gcd(b, a % b)

    gcd(48, 18)
    ```
    evaluates to `6`, identically to the grouped spelling
    `open gcd(a, b) = (a, 0) -> a | (a, b) -> gcd(b, a % b)`.
- **Dispatch algorithm** (contract §5): given `n` arguments, if any
  participating clause has a fixed shape of arity `n`, only fixed clauses of
  arity `n` participate; otherwise every eligible varargs clause (minimum
  arity ≤ `n`) participates, and more than one distinct eligible minimum is a
  deterministic `open-function-varargs-ambiguity` failure (the largest
  minimum is never chosen). Within each participating unit (the base, or one
  selected contribution), clauses are tested in lexical order and at most one
  becomes that unit's candidate. If exactly one unit supplies a candidate it
  runs; more than one candidate is a deterministic `open-function-clause-
  ambiguity` failure — there is no specificity ranking and contribution
  selection/import order can never break a tie. Existing fixed-over-varargs
  precedence, first-match order, guards, named patterns, and automatic
  Outcome/`none` propagation are preserved by reusing the existing pattern
  engine (`match_lambda_pattern`) unchanged.
- **Duplicate clauses.** Two clauses in the same unit with the same
  structural, alpha-normalized, span-free dispatch key are
  `open-function-duplicate-clause`, detected once when the unit is built
  (module load time), never deferred to call time. The same dispatch key in
  two different units is not a build-time duplicate; if both match one call,
  the across-unit ambiguity rule applies.
- **Explicit cross-module contribution.**
  - `extend <module-alias>.<name>(<pattern>, ...) = <body>` (in a
    contributing module that has already `import`ed `<module-alias>`)
    declares one clause of that module's contribution unit targeting the
    open interface exported as `<name>` by `<module-alias>`. Repeated
    `extend` statements for the same target in the same module accumulate
    into one contribution unit, in source order.
  - `use <name> from <base-alias> with <contrib-alias-1>, <contrib-alias-2>,
    ...` is a declarative, once-evaluated top-level statement (like
    `import`) that resolves `<base-alias>.<name>`, resolves each named
    contribution module's exported contribution unit for that exact
    interface, and binds `<name>` in the *current* module to the resulting
    immutable linked view. There is no wildcard/implicit selection.
  - Ordinary `import` alone never selects a contribution: importing a
    contribution-bearing module without an explicit `use` leaves the base
    interface (and any other module's already-linked view) completely
    unaffected.
  - Interface/contribution identity is the pair (canonical cached module
    name, exported name) — the same identity `Env.load_module` already
    caches modules under. Import alias, file path, and host object address
    are never part of this identity, so two aliases of the same cached
    module are one interface/contribution, duplicate selection through two
    such aliases is a deterministic `open-function-duplicate-selection`
    failure, and reordering unrelated imports or the `with` list cannot
    change a successful dispatch result.
  - Selecting a module with no matching contribution unit, or a closed
    function/non-function, is `open-function-incompatible-contribution`.
  - Declaration, import, and `use` perform no lifecycle activation, resource
    acquisition, network/process IO, or clause-body execution; a clause body
    runs only after a successful call dispatches to it.
- **Provenance and introspection.** `help(interface-or-linked-view)` lists
  the interface name, its declaration span, effective documentation (or "No
  documentation available."), and every participating unit's clauses in
  deterministic order — the base unit first (labelled by its declaring
  module identity), then each contribution unit ordered by its declaring
  module identity, clauses within a unit by lexical ordinal. `doc(name)`
  returns the interface's own docstring; contribution clauses cannot supply,
  replace, or erase interface-level documentation. No host object address or
  Python-specific representation is exposed.
- **Diagnostics.** `open-function-redeclaration`,
  `open-function-target-not-open`, `open-function-duplicate-clause`,
  `open-function-duplicate-selection`,
  `open-function-incompatible-contribution`,
  `open-function-varargs-ambiguity`, and `open-function-clause-ambiguity` are
  raised as `TypeError` subclasses (`src/genia/callable.py`) with the
  parameters the contract requires; a pattern/shape miss reuses the existing
  `No matching function` / `No matching case` diagnostic families. Span
  rendering in these messages is a plain `filename:line` string, not a raw
  host object repr.
- **Core IR.** Three new portable node types —
  `IrOpenFuncDef(name, clauses, docstring, annotations)`,
  `IrOpenContribution(target_module_alias, target_name, clauses)`, and
  `IrOpenUse(local_name, target_module_alias, target_name,
  contribution_module_aliases)` — reuse the existing `IrCaseClause`/
  `IrPatTuple`/`IrPatRest` pattern representation verbatim; no new pattern or
  guard node was added. See
  `docs/architecture/core-ir-portability.md`.
- **Host capability.** A dedicated `open_functions` capability
  (`spec/manifest.json` optional capability;
  `docs/host-interop/HOST_CAPABILITY_MATRIX.md`) is `Implemented` for Python;
  every R20 shared spec case requires `open_functions` so an
  older/non-conforming host reports these cases unsupported rather than
  silently passing them.
- **Known limitations of this Experimental slice** (see
  `docs/analysis/r20-release-truth-audit.md` for the full accounting):
  - a grouped case-with-pipe body is auto-flattened only when the header
    pattern is plain identifiers and the body is exactly one `CaseExpr` (or
    a one-expression `{ }` block containing one); other combinations of a
    non-trivial header with a case body are rejected rather than given
    ad hoc semantics;
  - `@doc`/`@meta`-style annotation attachment is not wired for `open`/
    `extend` declarations in this slice — interface metadata beyond the
    optional docstring position is a follow-up;
  - cross-module contribution/linking behavior retains Python-host real-file
    unit evidence and has eight portable shared eval/error cases using #836's
    logical multi-file fixture; those cases additionally require the R16
    `multi_file_eval` transport capability, independently of R20 semantics;
  - debug-hook wiring (`debug_hooks`/`debug_mode` propagation used by the
    Python debug adapter) is not threaded through open-function dispatch.
## 5) Case expressions and pattern matching
<!-- anchor: state:pattern-matching -->

Case arms support:

```genia
pattern -> result
pattern ? guard -> result
```

Implemented pattern types:

- literal patterns
- glob string patterns (`glob"..."`) for whole-string matching
- option constructor patterns (`some(pattern)`)
- variable binding
- wildcard `_`
- tuple patterns
- list patterns
- map patterns (partial-by-default key matching)
- rest pattern `..name` / `.._` (list patterns only; final position only)
- duplicate binding semantics (same name must match equal value)
- multiline list pattern formatting is accepted (newlines inside `[...]` pattern shapes)
- named reusable patterns (`Name(inner_pattern)`) — **Experimental**

Resolution order: arms of a case expression and clauses of a function are tried in source order, and the first matching arm or clause is selected.

Map pattern semantics:
- key forms:
  - explicit: `{ name: n }`, `{ "name": n }`
  - shorthand binding: `{ name }` (identifier keys only; sugar for `{ name: name }`)
  - mixed forms are supported (`{ name, age: years }`)
- trailing commas are accepted (`{ name, age: years, }`)
- patterns are partial by default:
  - `{ name }` matches any map containing key `"name"`
  - multiple entries require all listed keys to be present
- missing keys fail the match
- duplicate binding names follow normal duplicate-binding equality semantics

Lambda pattern semantics:

- lambda parameter patterns use the same implemented pattern families as function clauses and case arms
- lambdas remain single-arm; multi-arm lambda syntax is not implemented
- when a lambda parameter pattern does not match, the runtime raises the existing pattern-miss style error for the received argument tuple

Glob pattern semantics (Phase 1):

- valid in any pattern position accepted by function clauses, case arms, or lambda parameter patterns
- matches only string values (non-string values fail to match)
- whole-string matching only (no substring mode)
- supported metacharacters:
  - `*` (zero or more chars)
  - `?` (exactly one char)
  - character classes: `[abc]`, `[a-z]`, `[!abc]`
- supported escaping inside glob text:
  - `\*`, `\?`, `\[`, `\]`, `\\`
- malformed character classes raise deterministic syntax errors

Named reusable pattern semantics (Experimental):

- a named pattern is declared at top level with `pattern Name(value) = body`; exactly one matcher parameter is required
- the body evaluates to an Outcome value; non-Outcome bodies are a runtime error
- `Name(inner_pattern)` in pattern position invokes the named matcher with the candidate value and then matches `inner_pattern` against the matcher's returned payload
- `some(payload, context?)` — match succeeds; `inner_pattern` is matched against `payload`
- `none(reason, context?)` — pattern misses; later case arms are tried normally
- `err(reason, context?)` — recoverable matcher failure; does NOT fall through as a miss; surfaces as the dispatch result
- non-Outcome return from the matcher is a runtime error
- `some`, `none`, and `err` in pattern position remain built-in Outcome constructor patterns unaffected by named pattern resolution
- using a name that is bound to an ordinary function (not a named pattern) in pattern position is a runtime error
- using an unknown name in named-pattern position is a runtime error
- only one nested pattern argument is supported; `Name()` and `Name(a, b)` are parse errors
- named patterns are valid wherever ordinary patterns are valid (function case arms, list patterns, map patterns, tuple patterns)
- named pattern declarations do not introduce a separate namespace; `Name` is bound in the normal lexical environment
- recursive named patterns are not supported in this phase

Template semantics (Experimental):

- a Template is an ordinary one-argument Outcome matcher; it is not a distinct runtime category, namespace, or nominal type
- a value declared by `pattern Name(value) = body` is directly callable and may be stored, passed, returned, imported, and used by higher-order functions like any other callable value
- direct Template calls return the matcher Outcome unchanged, including a transformed `some(...)` payload and any reason/context
- direct Template calls require an Outcome result; a non-Outcome result raises `named pattern <Name> returned non-Outcome value`
- `@?`, `@!`, `&`, and `Name(inner_pattern)` retain their implemented original-subject, short-circuit, and payload-matching behavior
- `refinement_match(predicate, value)` lifts an existing one-argument boolean predicate into a Template result: `true` returns `some(value)` and `false` returns `none("refinement-mismatch")`; a non-callable predicate or non-boolean result is runtime misuse
- `open_shape_match(fields, value)` treats an ordinary map of string field names to callable Templates as an open structural specification; a matching ordinary map must contain every listed field, may contain extras, and returns the original complete map in `some`
- open-shape field specifications and checks run in specification insertion order; missing fields return `none("open-shape-missing-field", {field: name})`, non-map subjects return `none("open-shape-mismatch")`, and a nested Template `none` or `err` is propagated unchanged
- `exact_shape_match(fields, value)` uses the same specification protocol but requires the candidate map's key set to equal the specification key set; non-map, missing, and extra candidates return `none("exact-shape-mismatch")`, `none("exact-shape-missing-field", {field: name})`, and `none("exact-shape-extra-field", {field: name})` respectively
- exact-shape specifications are validated first; missing fields are checked in specification insertion order, then extras in candidate insertion order, then field Templates in specification order
- nested Template `some(payload)` establishes compatibility only; structural matching does not transform the field or subject, while nested `none`/`err` propagates unchanged
- refinement/open/exact helpers compose through existing direct calls, `Name(inner_pattern)`, `@?`, `@!`, and `&`; they add no syntax, nominal identity, or runtime shape category
- positional/labeled shapes and nominal Structs are not implemented by the Template/shape slices; the separate Experimental JSON Schema boundary below compiles only its locked structural subset

Inert inspectable Template descriptions (Experimental):

- `refinement(predicate)` returns a curried one-argument Template whose behavior is identical to `refinement_match(predicate, value)`; `open_shape(fields)` and `exact_shape(fields)` are the curried equivalents of `open_shape_match`/`exact_shape_match`. Each builder validates its argument eagerly at construction time, using the same validation as its two-argument counterpart, and requires zero additional matching logic — the returned Template simply delegates to the existing two-argument helper.
- `template_description(template)` requires a callable Template and returns `some(description)` when `template` was produced by `refinement`, `open_shape`, `exact_shape`, or `json_schema`; every other callable Template — arbitrary one-argument callables and named patterns declared with `pattern Name(value) = ...`, even when the body directly calls `refinement_match`/`open_shape_match`/`exact_shape_match` — remains fully valid but opaque and returns `none("opaque-template")`. A non-callable argument raises a clear `TypeError`.
- description shapes are ordinary Genia data built only from maps, symbols, strings, booleans, and lists:
  - `refinement` -> `{kind: quote(refinement)}`; the predicate is never introspected, executed during inspection, or exposed
  - `open_shape`/`exact_shape` -> `{kind: quote(open_shape)|quote(exact_shape), fields: {name: field_description, ...}}`, where `fields` preserves the builder's field-map insertion order and each entry is either that field Template's own description or the symbol `quote(opaque)` when the field Template itself has none
  - a `json_schema`-compiled Template additionally carries a description mirroring its already-compiled internal schema: scalar node -> `{kind: quote(json_schema_scalar), type: quote(<type>)}`; object node -> `{kind: quote(json_schema_object), properties: {name: description, ...}, required: [names...], additional: bool}` with `properties` in schema-declaration order; array node -> `{kind: quote(json_schema_array), items: description}`
- descriptions are immutable and inert: they do not participate in equality, hashing, callable identity, pattern identity, matching, dispatch, or original-subject semantics (`@?`, `@!`, `&`, and `Name(inner)` behave identically whether or not a Template has a description). Two Templates built from equal specifications are two distinct callables with equal-shaped descriptions, never the same Template.
- construction and inspection are effect-free: no user-data validation runs, no predicate/refinement callable is executed, and no config/lifecycle lookup, filesystem/network IO, or import-time activation occurs.
- no protected or represented payload can appear inside a description; nested field/property entries contribute only their own description shape or the `quote(opaque)` marker, never a captured closure or field value.

Explicit missing-only field defaults (Experimental):

- `default_field(default, template)` wraps a field Template with an explicit default for use as a field entry inside `open_shape(fields)` / `exact_shape(fields)` (the E15-1 curried builders); `template` must be Template-callable or it raises `TypeError("default_field expected Template function, received <type>")`.
- when the wrapped field's key is present in the candidate map, `default_field` has no effect: the present value is validated by `template` exactly as an ordinary field entry, and a present invalid value fails normally — it never falls back to the default.
- when the wrapped field's key is absent, the shape validates `default` through `template` (not the missing candidate value); a passing default is inserted into the result under that field name, while a failing default's mismatch/error propagates unchanged as that field's own Outcome rather than being reported as a missing-field mismatch.
- on overall success: if no defaults were actually applied, `open_shape`/`exact_shape` return the exact original subject unchanged (identity-preserved, not merely equal); if one or more defaults were applied, they return a new map equal to the subject plus every inserted default field, in specification order.
- `open_shape_match`/`exact_shape_match` (the R9-era two-argument matcher primitives used inside `pattern Name(value) = ...` bodies) are completely unmodified by E15-2 and know nothing about `default_field`; only the E15-1 curried `open_shape`/`exact_shape` builders recognize it.
- `template_description` on a `default_field`-wrapped Template is `{kind: quote(field_default), has_default: true, template: inner_description_or_quote(opaque)}`; the literal default value is never copied into the description, so a protected or represented default stays opaque there exactly as it does everywhere else.
- a default filled inside a nested structural Template establishes that nested value's own compatibility only; it does not transform the *outer* field, consistent with the existing R9 invariant that a nested Template's success payload never replaces the enclosing subject. For example, with `Address = exact_shape({city: default_field("Unknown", ...)})` and `Person = exact_shape({..., address: Address})`, `Person({..., address: {}})` keeps `address: {}` in its own result even though `Address({})` independently succeeds as `some({city: "Unknown"})`; only defaults declared directly in a shape's own field map are reflected in that shape's own returned value.
- explicit normalization needs no new builtin: `record |> normalize_fn |> Shape` is already ordinary explicit pipeline composition, where `normalize_fn` is any ordinary one-argument function and `Shape` validates its result exactly as any other value; Template matching itself performs no coercion.
- construction and matching remain effect-free; no ambient config/lifecycle/IO occurs.

Accumulated path-aware validation diagnostics (Experimental):

- `accumulate(template, value)` validates `value` against an inspectable Template, collecting every independent field/index failure in one call instead of short-circuiting on the first mismatch; `template` must be Template-callable, and (after unwrapping one outer `default_field`, if present) must carry a `template_description` or it raises `TypeError("accumulate expected inspectable Template, received opaque Template")`.
- deep recursion is supported only for the `open_shape`/`exact_shape` family (including nested shapes and `default_field`-wrapped fields, which reuse their exact real default-insertion semantics); a bare `refinement` Template, or any other inspectable-but-non-shape Template such as a `json_schema`-compiled one, is treated as one leaf check rather than recursed into.
- `exact_shape`'s own contracted phase order is replicated for diagnostics: missing-without-default fields in specification order, then extra fields in candidate order, then per-field validation in specification order, depth-first; `open_shape`'s single interleaved per-field pass is replicated as-is.
- each diagnostic entry is `{path: [field_name_or_index, ...], kind: quote(mismatch)|quote(error), reason: <reason>}`; `path` segments are built only from the Template's own specification/traversal (field names as strings), never from candidate data; `kind` is `quote(mismatch)` for an underlying `none(...)` observation and `quote(error)` for `err(...)`; `reason` is exactly the underlying Outcome's own `reason` value and never its `context`, so an arbitrary leaf Template's context can never leak a protected or represented payload into a diagnostic.
- zero diagnostics: `accumulate` returns the exact result of directly invoking `template(value)` — it never reimplements or diverges from the real success path (including default insertion). One or more diagnostics: `err(quote(accumulated-validation-failed), {diagnostics: [...]})` in the deterministic order above.
- `accumulate` never touches Flow or Seq itself; it operates on one already-materialized value, so composing it inside an ordinary `map` stage over a lazy Flow preserves existing bounded-demand, no-over-pull, single-use Flow semantics with zero new Flow-specific code.
- `accumulate` does not change `open_shape_match`/`exact_shape_match`/`refinement_match`/`open_shape`/`exact_shape`/`refinement`/`default_field`/`json_schema` direct-call behavior, named-pattern dispatch, `@?`/`@!`/`&`, or case-arm/first-match semantics; it is a separate, explicitly-invoked operation that only reads their existing private structural attributes.
Faithful Template to JSON Schema generation (Experimental):

- `template_schema(template)` generates a JSON Schema for `template` through pure inspection over its own `template_description` data; it never invokes `template`, never invokes any nested field Template, never executes a callable refinement predicate, and touches no runtime value at all. `template` must be Template-callable or it raises `TypeError("template_schema expected callable Template, received <type>")`.
- faithfully convertible: a `json_schema`-compiled Template's own description converts back to the equivalent schema map directly (it already is schema-shaped); `open_shape`/`exact_shape` convert to `{type: "object", properties: {...}, required: [every field name, specification order], additionalProperties: <true for open_shape, false for exact_shape>}` only when every field recursively converts.
- deterministically unsupported, never approximated: an opaque field or top-level Template (no description at all); a bare `refinement` field or top-level Template (its predicate is never introspected, so it has no derivable JSON type); a `default_field`-wrapped field or top-level Template (JSON Schema's `default` keyword is an annotation, not an insertion transform, so missing-only default semantics cannot be represented faithfully — the same conclusion E15-2 already reached).
- failure is `err(quote(unsupported-template), {path: [field_name_or_index, ...], kind: quote(opaque)|quote(refinement)|quote(default_field)|quote(unsupported_kind)})`, `path` pointing at the exact unsupported node; success is `some(represent("json", schema_map), {kind: quote(template_schema), operation: quote(generate), status: quote(generated), reason: quote(generated)})`.
- round-trip claim is limited to the tested subset: compiling a schema with `json_schema`, reversing it with `template_schema`, and recompiling the result with `json_schema` produces a Template with identical accept/reject behavior over the tested representative values — not object identity, not preservation of non-schema metadata.
- `template_schema` does not change `json_schema`/`open_shape`/`exact_shape`/`refinement`/`default_field`/`accumulate`/`template_description` direct-call behavior; it is a separate, explicitly-invoked, pure-inspection operation.

Structural discriminated alternatives (Experimental):

- `alternatives(discriminator_field, branches)` is a curried Template builder (same family as `refinement`/`open_shape`/`exact_shape`) selecting exactly one branch by reading an explicit string discriminator field, then validating only that branch against the full original value; ordinary map/value payloads only, no nominal variant object is ever constructed. `discriminator_field` must be a non-empty ordinary string; `branches` must be a map whose keys are non-empty ordinary strings and whose values are Template-callable, or construction raises a clear `TypeError`.
- direct-call resolution order: a non-map subject returns `none("alternative-mismatch")`; a subject missing `discriminator_field` returns `none("alternative-missing-discriminator", {field: discriminator_field})`; a present discriminator value that is not an ordinary string (a symbol counts as not-a-string here) returns `none("alternative-invalid-discriminator", {field: discriminator_field})`; a string not present among `branches`' keys returns `none("alternative-unknown-discriminator", {field: discriminator_field, value: <the discriminator string>})`; otherwise the resolved branch Template is invoked on the full unmodified subject and its Outcome is returned unchanged.
- exactly one branch is ever validated; a branch's own mismatch/error surfaces unchanged and no other branch is ever attempted — there is no try-every-branch-and-pick-a-success semantics and no discriminator inference from payload shape.
- `alternatives` does not strip the discriminator field before branch validation; a branch built with `exact_shape` must declare the discriminator field itself if it wants a fully closed shape, while a branch built with `open_shape` tolerates it as an allowed extra, exactly like any other nested-shape composition.
- `template_description` -> `some({kind: quote(alternatives), discriminator: discriminator_field, branches: {tag: branch_description_or_quote(opaque), ...}})`, `branches` in the builder's own map insertion order.
- `accumulate` recurses depth-first into exactly the resolved branch at the same path (the branch validates the whole subject, not a sub-field); discriminator-resolution failures produce one diagnostic at `path + [discriminator_field]` with reason `accumulate-not-a-map`/`alternative-missing-discriminator`/`alternative-invalid-discriminator`/`alternative-unknown-discriminator` as applicable.
- `template_schema` returns `err(quote(unsupported-template), {path: [...], kind: quote(alternatives)})` for every `alternatives` Template — E15-4's closed schema-keyword subset has no discriminated-union primitive, and this slice does not extend it.
- composes with named patterns, `@?`, `@!`, `&`, and `Name(inner)` exactly like any other Template, since `alternatives` produces an ordinary Template built the same way as `refinement`/`open_shape`/`exact_shape`; no pattern-dispatch code was added or changed.
- issue #92 disposition: only structural discriminator-directed validation is absorbed here. Nominal variant identity, constructor objects/syntax, sealed/closed nominal hierarchies, and exhaustiveness checking remain explicitly deferred beyond R15 and are not implemented.

Bounded named recursive Template references (Experimental):

- `recursive_template(name, build_fn, max_depth)` builds a self-recursive Template through one explicit named reference; `name` must be a non-empty ordinary string, `build_fn` must be Template-callable, and `max_depth` must be a positive integer no greater than 100, or construction raises a clear `TypeError`. Validation of a self-reference reachable through `alternatives`/`open_shape`/`exact_shape` composition (the documented idiom, and the only shape every example uses) runs on an explicit Python-list stack rather than the Python call stack: `alternatives` dispatch is a pure tail substitution and each shape field's descent pushes one frame that is popped again before the next field is considered, so frames never accumulate along the self-reference spine. This keeps the explicit depth bound's own Python stack usage independent of `max_depth` and of how deep a validated value actually is — the bound fires correctly at any documented `max_depth` (verified to a logical depth of 10,000, ten times Python's own default recursion limit) and `RecursionError` never crosses the boundary for this idiom. A self-reference invoked from behind a fully opaque (non-inspectable) wrapper Template still falls back to ordinary Python recursion for that unusual case only, remaining correctly bounded but without the O(1)-stack guarantee.
- construction calls `build_fn(ref)` exactly once with an ordinary one-argument callable `ref`: `ref(name)` (matching the declared `name`) returns a self-reference Template; `ref(other_name)` returns a Template that always fails with `err("recursive-template-unresolved-reference", {name: other_name})` without inspecting its argument. `ref`'s own argument must be an ordinary string, and `build_fn`'s return value must itself be Template-callable, or construction raises a clear `TypeError`.
- reference resolution is entirely closed over the one `name`/`build_fn`/`max_depth` triple supplied at construction; no mutable global registry, configuration, or lifecycle context ever participates. Depth is tracked per `recursive_template` instance with a dedicated `contextvars.ContextVar` created fresh inside each call — never shared across instances or exposed to Genia code — reset to `0` on every top-level call and incremented/restored around each self-reference invocation.
- a self-reference invocation whose current depth has reached `max_depth` returns `err("recursive-template-depth-exceeded", {limit: max_depth})` immediately, without ever invoking the wrapped structure on that value; validated subjects are walked as ordinary tree-shaped data only — arbitrary cyclic runtime object graphs and unrestricted mutual recursion (multiple names referring to each other) are out of scope and not promised.
- `template_description(t)` -> `{kind: quote(recursive_template), name, max_depth, template: <the built structure's own description, or quote(opaque)>}`.
- `accumulate` and `template_schema` both treat any `recursive_template`-built Template as **one leaf check at every level** — a deliberate, documented boundary rather than a gap: it avoids introducing a second, independently bounded recursive traversal inside the diagnostics accumulator or the schema generator. Direct-call validation is unaffected and still performs real bounded recursive traversal. `template_schema` therefore always returns `err(quote(unsupported-template), {path: [...], kind: quote(recursive_template)})` for a `recursive_template` Template in this slice; a faithful `$ref`-based JSON Schema mapping is an explicit non-goal here, not an approximation.
- composes with named patterns, `@?`, `@!`, `&`, and `Name(inner)` automatically, since `recursive_template` produces an ordinary Template; no pattern-dispatch code was added or changed.
- example: `Tree = recursive_template("tree", (ref) -> alternatives("kind", {leaf: exact_shape({kind: refinement((x) -> x == "leaf")}), node: exact_shape({kind: refinement((x) -> x == "node"), left: ref("tree"), right: ref("tree")})}), 5)`; `Tree({kind: "node", left: {kind: "leaf"}, right: {kind: "leaf"}})` is `some(...)` with the original value unchanged; a chain of `node`s nested `5` levels deep returns `err("recursive-template-depth-exceeded", {limit: 5})` at the point the bound is reached.

Carrier representation semantics (Experimental):

- `represent(facet, value)` attaches one explicit outer carrier facet; `facet` must be a non-empty string
- carrier facets are ordered nested layers around ordinary Genia values, not nominal JSON/secret classes or an unordered tag set; duplicate layers are valid
- `representation_match(facet, value)` returns `some(carried)` only for the exact outer facet and otherwise returns `none("representation-mismatch")`
- an existing named Template can define a representation-aware pattern with `pattern Name(value) = representation_match("facet", value)`; `Name(inner)` then uses ordinary named-pattern payload matching and may nest with other patterns
- `strip_representation(facet, value)` explicitly removes exactly one matching outer layer; an ordinary value or different outer facet is runtime misuse
- represented values compare by exact facet plus ordinary carried-value equality; represented and unrepresented values are unequal; supported map keys retain ordinary carried-value key restrictions
- assignment, calls, returns, collection storage, pipelines, Seq, Flow, and Sheet cells transport represented values unchanged; operations deriving new values do not copy facets implicitly
- `display` and `debug_repr` render every generic represented value as `<represented>`, exposing neither facet nor payload
- no facet registry, implicit propagation/coercion, protected `secret` behavior, declassification, parser syntax, or Core IR node is implemented by the generic carrier slice; the separate Experimental JSON boundary below now uses this carrier

Case placement rules (enforced):

- allowed in function body
- allowed as final expression in block
- rejected in ordinary subexpressions / call args / non-final block positions
### Conditionals
<!-- anchor: state:control-flow -->

- implemented via pattern matching in function definitions and case expressions; lambdas may also pattern-match their single parameter arm
- no dedicated conditional keyword exists
- no `if` expression or `if` form exists; branching uses pattern matching
- no dedicated loop syntax (`while`, `for`) exists
- repetition is expressed by recursion; tail calls are optimized in tail position (see tail-call behavior)
- `decide` has been removed from the language
## 6) Builtins (runtime)
### Configuration acquisition (Experimental)

- `config_args(args)` — pure normalization of explicit raw program strings into an existing R10 literal values-source descriptor Outcome
- `config_provider(sources)` — explicit immutable provider construction over ordered quoted-kind descriptors
- `config_standard(overrides, args[, dotenv_path])` — conventional four-source provider composition with fixed precedence and snapshot timing
- `config_get(provider, key)` — exact raw-string lookup through an explicit provider
- `config_get_or(provider, key, default)` — missing-only lazy defaulting; found/empty values bypass the zero-argument default, and selected defaults run exactly once
- `config_view(provider, prefix)` — inert qualified ordinary lookup callable using exact prefix/name concatenation and one existing `config_get`
- `secret_get(provider, key, purpose)` — exact lookup whose success is one protected `secret` carrier
- `secret_get_or(provider, key, purpose, default)` — missing-only lazy defaulting whose ordinary/`some` success is protected once
- `secret_view(provider, prefix, purpose)` — inert qualified secret lookup callable using one existing `secret_get` with unchanged protection
- `protected_match("secret", value)` — matches only protected values and returns the exact protected subject
- default ordinary values are lifted into `some(...)`, while default Outcomes remain unchanged; explicit converter Outcomes and callable Template validation compose through existing pipeline rules
- generic carrier construction, matching, and stripping reject the reserved `secret` facet; protected values compare without exposing payloads, are not map keys, and transport as exact leaves without container taint
- `declassify(authority, protected_value)` reveals only with an exact host-injected provider/purpose-scoped authority and records a non-sensitive audit event
- this E10-1/E10-7 surface adds ordinary calls, enforcement, cross-mode conformance, and an executable composition proof at existing boundaries only; annotation injection and syntax/Core IR changes are not implemented
### Lifecycle (Experimental)

- `lifecycle_scope(peers, work)` — runs a fresh root execution scope through the entry/work/unwind algorithm; `peers` is an ordered list of `{name: symbol, enter: callable/1, exit: callable/2}` closed maps
- `lifecycle_child(scope_handle, peers, work)` — runs a child execution scope nested under an active parent handle; callable only synchronously from that parent's own `work`
- `lifecycle_context(scope_handle, name)` — inward-only, read-only lookup of context exposed by an entered peer on the calling scope or any ancestor scope; `some(value)` or `none("lifecycle-context-absent")`
- see GENIA_STATE.md section 9.8 for the full entry/work/unwind algorithm, scope lifetime state machine, and failure-matrix contract
### Core I/O and utilities

- direct runtime names: `log`, `print`, `display`, `debug_repr`, `input`, `stdin`, `stdin_keys`, `stdout`, `stderr`, `help`
- `display` and `debug_repr` are the first concrete public entry points of the planned Representation System (#166); they are implemented as minimal Representation System surface area and are not standalone utility terminology
- public sink helpers are thin prelude wrappers in `src/genia/std/prelude/io.genia`:
  - `write`
  - `writeln`
  - `flush`
  - `clear_screen`
  - `move_cursor`
  - `render_grid`
- public web helpers are thin prelude wrappers in `src/genia/std/prelude/web.genia`:
  - `serve_http`
  - `get`
  - `post`
  - `route_request`
  - `response`
  - `with_headers`
  - `cors`
  - `json`
  - `text`
  - `ok`
  - `ok_text`
  - `bad_request`
  - `not_found`
- `argv` (returns raw trailing CLI args as a list of strings)
- constants in global env: `pi`, `e`, `true`, `false`, legacy alias `nil`
- pair builtins: `cons`, `car`, `cdr`, `pair?`, `null?`

Output sink semantics:

- `write`, `writeln`, and `flush` are the canonical public sink helper names and carry Markdown docstrings for `help(...)`
- the underlying sink behavior remains host-backed and unchanged in this phase
- `write(sink, value)` writes display-formatted output without a trailing newline and returns `value`
- `writeln(sink, value)` writes display-formatted output with a trailing newline and returns `value`
- `flush(sink)` flushes the sink and returns `none("nil")`
- `clear_screen()` writes ANSI clear/home control codes to `stdout`, flushes, and returns `none("nil")`
- `move_cursor(x, y)` writes an ANSI cursor-position control code to `stdout` and returns `none("nil")`
  - `x` is terminal column, `y` is terminal row
  - both coordinates must be positive integers
- `render_grid(grid)` writes a text grid to `stdout` and returns `grid`
  - `grid` must be a list
  - each row must be either a string or a list of displayable values
- `web.serve_http(config, handler)` runs a synchronous blocking HTTP server and returns `{host, port, handled_requests}` after the server stops
  - this is a public Python-reference-host surface in the current phase, not a shared cross-host contract category
  - `config.host` defaults to `"127.0.0.1"`
  - `config.port` defaults to `8000`
  - optional `config.max_requests` stops the server after a fixed number of handled requests
  - request maps currently include:
    - `method`
    - `path`
    - `query` (string-keyed map; repeated query keys keep the last value)
    - `headers` (lowercased string-keyed map)
    - `body` (parsed JSON when content type starts with `application/json`, otherwise decoded text)
    - `raw_body` (decoded text body)
    - `client` (`{host, port}`)
  - response maps currently use:
    - `status` (integer)
    - `headers` (string-keyed map)
    - `body` (string, bytes, or `none`)
  - invalid handler return values or response-shape errors produce a `500 internal server error` response in this phase
  - the ants browser viewer uses this same HTTP surface with static HTML/CSS/JS responses, JSON state snapshots, and POST endpoints for reset/step; it does not add WebSockets, SSE, or a richer server runtime
### Response header composition (**Partial**)

Implemented and verified in the Python reference host:

- public Python-reference-host web-module call shape: `with_headers(headers, response) -> response`
- `headers` is first and `response` is last so `response |> with_headers(headers)` is the canonical pipeline form
- `headers` and `response` must be maps; `response` must contain `status`, `headers`, and `body`, and `response.headers` must be a map
- every existing and supplied header name and value must be a string; empty strings are accepted and no trimming or HTTP token/value validation is introduced
- every output header name is normalized with the existing `lower` string operation; header-name collisions are therefore case-insensitive
- entries are processed in map iteration order, so the later case-insensitive spelling within one input header map wins; supplied entries are processed after existing entries, so supplied headers always win collisions with existing headers
- the result is a new response map with a new normalized header map; every non-`headers` response entry, including `status`, `body`, and any additional entry, is preserved unchanged
- the input response, its existing header map, and the supplied header map are not mutated
- validation order is: supplied `headers` map; `response` map; required `status`, `headers`, and `body` response fields; `response.headers` map; existing header entries; supplied header entries
- malformed inputs raise `TypeError` with these exact messages:
  - `with_headers expected headers to be a map`
  - `with_headers expected response to be a map`
  - `with_headers expected response.status field`
  - `with_headers expected response.headers field`
  - `with_headers expected response.body field`
  - `with_headers expected response.headers to be a map`
  - `with_headers expected response header name at index <index> to be a string`
  - `with_headers expected response header value at index <index> to be a string`
  - `with_headers expected supplied header name at index <index> to be a string`
  - `with_headers expected supplied header value at index <index> to be a string`
- header-entry indexes are zero-based map-iteration indexes
- `status`, `body`, and additional response entries are preserved without validation or coercion; transport response-shape validation remains the responsibility of the existing HTTP bridge
- this adds no `json`/`text` overload, CORS policy, automatic preflight handling, `OPTIONS` route, middleware framework, parser syntax, Core IR node, shared-spec category, or cross-host portability claim
- the existing `serve_http`, routing, response-constructor, `json`, and `text` behavior is otherwise unchanged
### CORS handler wrapper (**Partial**)

Implemented and verified in the Python reference host:

- public Python-reference-host web-module call shape: `cors(policy, handler) -> handler`
- `policy` is a closed Option Record Pattern with optional fields `origin`, `methods`, and `headers`; omitted fields use these defaults:
  - `origin: "*"`
  - `methods: ["GET", "POST", "OPTIONS"]`
  - `headers: ["content-type"]`
- `origin` must be a non-empty string; `methods` and `headers` must be non-empty lists whose entries are non-empty strings
- policy strings are preserved exactly; no trimming, case normalization, duplicate removal, origin reflection, allowlist matching, HTTP token validation, or request-policy negotiation is introduced
- methods and headers serialize in list order with `", "` between entries
- every decorated response contains:
  - `access-control-allow-origin: <origin>`
  - `access-control-allow-methods: <serialized methods>`
  - `access-control-allow-headers: <serialized headers>`
- a request is a true CORS preflight only when its `method` field is exactly `"OPTIONS"` and its lowercased `headers` map contains both `origin` and `access-control-request-method`; header values are not otherwise interpreted
- a true preflight does not invoke the wrapped handler and returns `response(204, cors_headers, none)`; the response is bodyless at the HTTP transport
- an `OPTIONS` request missing either required preflight header is ordinary and delegates to the wrapped handler
- every other request invokes the wrapped handler exactly once, then decorates its returned response solely through `with_headers(cors_headers, response)`; `with_headers` therefore owns response validation, lowercase normalization, collision precedence, preservation, and non-mutation behavior
- configured CORS headers override case-insensitive collisions in an ordinary handler response; unrelated headers, status, body, and additional response fields are preserved
- the policy map, policy lists, request map, handler response, and existing response headers are not mutated
- validation occurs when `cors(policy, handler)` is called, before the returned handler exists; validation order is: policy map, unknown fields in map iteration order, `origin`, `methods`, method entries in list order, `headers`, header entries in list order, handler callable
- malformed inputs raise `TypeError` with these exact messages:
  - `cors expected policy to be a map`
  - `cors unexpected policy field <field>` where `<field>` uses debug rendering
  - `cors expected policy.origin to be a non-empty string`
  - `cors expected policy.methods to be a non-empty list`
  - `cors expected policy.methods item at index <index> to be a non-empty string`
  - `cors expected policy.headers to be a non-empty list`
  - `cors expected policy.headers item at index <index> to be a non-empty string`
  - `cors expected handler to be callable`
- entry indexes are zero-based
- request-shape or wrapped-handler failures retain existing callable and response behavior; `cors` does not return an Outcome or translate failures
- this adds no header-map-only CORS API, public `options(...)` route, `json`/`text` overload, credentials policy, origin reflection/allowlist, per-route override, general middleware chain, parser syntax, Core IR node, shared spec, or cross-host portability claim
- `print(...)` writes to `stdout`
- `log(...)` writes to `stderr`
- `input()` remains interactive-only and does not consume the flow/stdin source path
- broken pipe on `stdout` output is treated as normal downstream termination in CLI/file/command execution (no Python traceback)
- flow-driven stdout writes use the same quiet broken-pipe path, so Unix pipelines can stop downstream early without noisy Python tracebacks
- broken pipe on `stderr` is handled best-effort and does not trigger recursive noisy failures
- on Windows console streams, `clear_screen` and `move_cursor` try to enable virtual terminal processing before writing ANSI control codes

Representation System entry points (#185, implemented):

- `display(value)` and `debug_repr(value)` are the first concrete public surface of the planned Representation System.
- They are entry points into that system, not independent formatting utilities.
- Representation renders values as strings for output and debugging.
- Representation does not change value identity.
- Representation is separate from value templates; value templates describe or constrain values, while representation formats describe output strings.
- `display(value)` returns a string containing the user-facing display representation of `value`.
- `debug_repr(value)` returns a string containing the debug representation of `value`.
- `display(value)` and `debug_repr(value)` render Outcome values directly, including `none(...)`; ordinary none propagation must not bypass these representation entry points. This is representation behavior only and does not change Outcome identity, direct-call none propagation for other functions, or pipeline propagation.
- `format(template_or_format, values)` is a public prelude-backed helper for building strings from a small placeholder template.
- `format(template_or_format, values)` returns a string and does not write output.
- `format(template_or_format, values)` does not mutate the input template, `Format` value, or values map/list.
- The first argument to `format` is either a raw string template or a `Format` value (see below).
- `format` supports:
  - named placeholders such as `{name}`, looked up in a map by string key
  - field-path placeholders (**Experimental**, #290): `{user.name}`, `{user.address.city}` — dot-separated named segments resolved left-to-right through nested map-like values; each segment must match `[A-Za-z_][A-Za-z0-9_]*`; field paths are lookup-only and not general template expressions
  - positional placeholders such as `{0}`, looked up in a list by zero-based index
  - escaped braces `{{` and `}}`
  - debug placeholders (**Partial**, #170): `{name:?}` and `{0:?}` render the resolved value with the same debug representation as `debug_repr(value)`
  - field format specs (**Experimental**, #169): a limited set of display specifiers after `:` inside a placeholder:
    - `<N` — left-align in width N using spaces
    - `>N` — right-align in width N using spaces
    - `^N` — center-align in width N using spaces; odd padding adds the extra space on the right
    - `.N` — truncate string value to first N characters; or format numeric value to exactly N decimal places (ties away from zero)
    - `0N` — zero-pad numeric output to width N; negative values keep the sign before the zeros
    - `,` — comma-group numeric output (integer portion only, ASCII commas, no localization)
  - `bool` values are not numeric for spec purposes; numeric specs (`0N`, `,`) applied to bools fail deterministically
  - combined specs, bare width specs (e.g. `{n:10}`), debug spec combinations (e.g. `{x:?>10}`), and any spec not listed above are unsupported and fail with a `format-error:` prefixed error
- Field-path placeholder resolution: a missing top-level or nested segment fails with `format missing field: <path>`; a non-map intermediate fails with `format expected a map while resolving placeholder path: <path>`; invalid path syntax (empty segment, leading/trailing/double dot, slash-separated paths, brackets, calls) fails with `format invalid placeholder`; slash (`/`) is not a field-path separator and must not be used in field-path placeholders.
- Placeholder replacements use the same user-facing display representation as `display(value)`, except where the exact debug spec `?` or another listed field spec applies.
- Missing fields and invalid placeholders raise deterministic errors.
- `format` does not support interpolation string syntax, localization, tag-based format selection, custom formatter protocols, list indexing in field paths, optional chaining, filters, or spec combinations beyond the listed subset.
- `Format(template)` and `Format(template, tag)` are first-class Representation System constructors (**Experimental**, #168, #292):
  - `Format(template)` accepts a string template and returns an untagged first-class `Format` value.
  - `Format(template, tag)` accepts a string template and a non-empty string tag and returns a tagged first-class `Format` value.
  - `Format` is for output representation and does not affect value identity.
  - `Format` is separate from value templates.
  - A `Format` value is representation-only: it is not a Value Template and does not participate in shape/refinement/contract/variant semantics.
  - The tag is representation metadata attached to the `Format` value only. It does not affect placeholder parsing, placeholder resolution, field-spec rendering, debug field specs, or the identity of values being formatted.
  - `format(Format(template), values)` and `format(Format(template, tag), values)` produce the same result as `format(template, values)` for the same template and values.
  - A `Format` value can be assigned to a name, passed as an argument, stored in a list or map, and returned from a function.
  - `display(Format(...))` returns `<format>`; the wrapped template and tag are not exposed.
  - `debug_repr(Format(...))` returns `<format>`; the wrapped template and tag are not exposed.
  - `Format()` fails with `TypeError: Format expected 1 or 2 args, got 0`.
  - `Format(template, tag, extra)` fails with `TypeError: Format expected 1 or 2 args, got 3`.
  - `Format(non_string)` fails with `TypeError: Format expected template string, received <type>`.
  - `Format(template, non_string_tag)` fails with `TypeError: Format expected tag string, received <type>`.
  - `Format(template, "")` fails with `TypeError: Format expected non-empty tag string`.
  - `format(non_string_non_format, values)` fails with `TypeError: format expected a string template or Format value, received <type>`.
  - No parser syntax such as `Format "..."` is introduced; `Format("...")` and `Format("...", "tag")` are the only accepted call forms.
  - `Format` is Experimental. The wrapped template, tag, display/debug text, and constructor surface may change before stabilization.
- `format_template(fmt)` is a public Representation System helper (**Experimental**, #294):
  - `format_template(fmt)` returns the original source template string supplied to `Format(...)`.
  - Accepted: a `Format` value created by `Format(template)`.
  - Rejected: raw strings, numbers, lists, maps, booleans, flow values, and any other non-Format value.
  - `format_template(fmt)` returns the template string exactly: no normalization, no unescaping, no placeholder parsing.
  - `format_template("{a}")` fails with `TypeError: format_template expected a format, received string`.
  - `format_template(non_format)` fails with `TypeError: format_template expected a format, received <type>`.
  - `display(Format(...))` and `debug_repr(Format(...))` remain opaque; `format_template` is the only approved way to recover the source template string.
  - `format_template` does not expose compiled template internals, placeholder metadata, or parsed template structure.
  - `format_template` does not apply to composed `Format` values created by `format_compose(...)`. Calling `format_template` on a composed format fails with `TypeError: format_template expected an atomic Format value`.
  - `format_template` is not explicitly none-aware; ordinary none propagation applies in pipelines.
  - `format_template` is Experimental. The accessor name and behavior may change before stabilization.
- `format_tag(fmt)` is a public Representation System helper (**Experimental**, #292):
  - `format_tag(fmt)` returns `some(tag)` for a tagged `Format` value created with `Format(template, tag)`.
  - `format_tag(fmt)` returns `none("missing-format-tag")` for an untagged `Format` value created with `Format(template)`.
  - Accepted: a `Format` value created by `Format(template)` or `Format(template, tag)`.
  - Rejected: raw strings, numbers, lists, maps, booleans, flow values, and any other non-Format value.
  - `format_tag()` fails with `TypeError: format_tag expected 1 arg, got 0`.
  - `format_tag(fmt, extra)` fails with `TypeError: format_tag expected 1 arg, got 2`.
  - `format_tag(non_format)` fails with `TypeError: format_tag expected a format value, received <type>`.
  - `format_tag` does not expose the template, alter rendering, or cause tag-based format dispatch.
  - `format_tag` is Experimental. The helper name and behavior may change before stabilization.
- `format_compose(parts)` is a public Representation System helper (**Experimental**, #293):
  - `format_compose(parts)` accepts a list of format pieces and returns a new `Format` value.
  - Each piece in `parts` must be either a raw string template or a `Format` value (including another composed `Format`).
  - Rendering a composed `Format` with `format(composed_fmt, values)` renders each piece in order with the same `values` map and concatenates the resulting strings.
  - Empty composition is valid: `format(format_compose([]), {})` returns `""`.
  - Nested composition is valid: composed `Format` values may be used as pieces in later composition.
  - Repeated placeholders are allowed and read the same value from the input map.
  - All placeholders in a composed `Format` share the same input namespace; there is no per-piece namespace.
  - Composition adds no separators, whitespace, or newlines; separators must be explicit pieces.
  - `format_compose(parts)` is pure: it does not mutate `parts`, any piece, or any values map.
  - `display(format_compose(...))` and `debug_repr(format_compose(...))` return `<format>`.
  - `format_template` does not apply to composed `Format` values; calling it on a composed format fails with a deterministic `TypeError`.
  - `format_compose(non_list)` fails with `TypeError: format_compose expected list of format pieces, received <type>`.
  - `format_compose([..., invalid, ...])` fails with `TypeError: format_compose expected string or Format at index <n>, received <type>` (zero-based index).
  - Missing placeholder behavior during rendering is unchanged: existing missing-placeholder errors apply.
  - `format_compose` does not add parser syntax, Core IR behavior, control flow, expression evaluation, localization, debug mode, tagged dispatch, field paths, or Value Template behavior.
  - `format_compose` is Experimental. The helper name and behavior may change before stabilization.
- These helpers do not write to `stdout` or `stderr`.
- These helpers do not mutate runtime state.
- These helpers do not change `print`, `log`, `write`, `writeln`, REPL result display, CLI final-result rendering, or pipeline semantics.
- `print(value)`, `log(value)`, `write(sink, value)`, and `writeln(sink, value)` remain output operations; `display(value)` and `debug_repr(value)` return ordinary strings.
- For ordinary runtime data, the minimal implemented representation behavior is:
  - strings: `display("x")` returns `x`; `debug_repr("x")` returns `"x"` with debug escaping
  - numbers: both return ordinary numeric text
  - booleans: both return `true` or `false`
  - `none`: both return `none("nil")`
  - `none(reason)` and `none(reason, context)`: both preserve structured absence syntax and context metadata
  - `some(value)`: both preserve the `some(...)` wrapper and recursively represent the inner value
  - lists: both return bracketed list syntax and recursively represent items
  - maps: both return brace map syntax and recursively represent keys and values
  - pairs / quoted syntax data: both preserve the existing pair-shaped representation syntax
- Wrong arity fails through the ordinary callable arity/type-error path.
- Runtime capability values and function-like values may have host-specific opaque debug/display text in this phase unless a later contract explicitly stabilizes them.
### Sheet builtins (Experimental)

Sheet public helpers are registered directly as arity-specific `GeniaFunctionGroup` builtins in the global environment (not autoloaded). This allows coexistence with user-defined functions at other arities (for example, user-defined `rows/0` may coexist with `rows(sheet)`).

Public helpers:

- `sheet(columns)` — construct a Sheet from a list of `[name, values]` column pairs; column values must be lists; column names must be unique; all columns must have equal length. Column-name uniqueness uses Genia equality (R18 E18-4), and the legal column-name family is the same as the legal map-key family; see "Portable value equality" above
- `shape(sheet)` — return `[[rows, n], [columns, n]]`
- `columns(sheet)` — return column names in deterministic order
- `select(names, sheet)` — return a new Sheet with requested columns in requested order; rejects duplicate or missing names
- `where(predicate, sheet)` — return a new Sheet of rows where predicate returns `true`; predicate receives each row as a list of `[name, value]` pairs; predicate must return boolean
- `derive(name, function, sheet)` — return a new Sheet with a new column appended; row function receives each row as a list of `[name, value]` pairs; rejects existing column names
- `rows(sheet)` — return a list of rows, each row as a list of `[name, value]` pairs
- `row_get(row, column_name)` — return the value paired with `column_name` in a row (**Experimental**); see below
- `collect_sheet(records)` — terminal, explicit conversion of a finite Seq-compatible source (list or Flow) of homogeneous map records into an immutable Sheet (**Experimental**); see below
- `render_csv(sheet)` — return deterministic CSV report text for a Sheet (**Experimental**); see below

All Sheet operations return new Sheet values. Existing Sheet values are never mutated.

`row_get(row, column_name)` (**Experimental**):

- takes any row value shaped like the existing `where`/`derive`/`rows` row contract: a `list` of two-item `[name, value]` pairs
- does not take a Sheet; it reads a single already-extracted row, which is why `where` and `derive` row functions can call it directly on the row argument they receive
- returns the value paired with `column_name`, matched using the same column-name identity rules as `sheet`/`select` (`GeniaSymbol`, string, number, boolean, nil, tuple, and list names compare by value; other name types must be hashable)
- performs a first-match linear scan; a row with duplicate names for a requested column returns the first matching pair's value and is not itself flagged as an error — well-formed rows produced by `rows`, `where`, and `derive` never contain duplicate names, so this case only arises from hand-built rows, which is out of scope
- pure and read-only: never mutates the row, its source Sheet, or any cell value
- errors (all `TypeError`, opting out of generic pipeline error wrapping):
  - row is not a `list`: `"row_get expected a row (list of [name, value] pairs)"`
  - a row entry is not a two-item `list`: `"row_get expected a row (list of [name, value] pairs); malformed entry at index <n>"`
  - `column_name` absent from the row: `"row_get could not find column <name>"`
- introduces no new syntax; `row_get(row, quote(age))` is an ordinary function call using the existing pair-list row representation, not a new access form

`collect_sheet(records)` (**Experimental**):

- consumes a finite `list` or `GeniaFlow` of `GeniaMap` records, the same Seq-compatible source types accepted by `collect` and `collect_validated`
- empty input returns the same zero-row/zero-column Sheet as `sheet([])`
- for non-empty input, the first record's map entry order becomes the Sheet's column order; column names are the record's raw keys, unchanged and uncoerced (map-literal keys such as `{name: "Ann"}` are plain strings, not symbols, so resulting column names render as strings, unlike `sheet()`'s symbol-keyed columns)
- every later record must have exactly the first record's key set (order-independent); values are copied as ordinary cell values with no coercion, and Outcome values (`some`/`none`/`err`) stored as a field are kept as plain cell values, not unwrapped
- it does **not** process Outcome items itself: a bare `some(...)`/`none(...)`/`err(...)` passed as a top-level record item is rejected as "not a map," matching `collect_validated`'s separate, explicit aggregation step — use `collect_validated` first and pass its `clean` list into `collect_sheet`
- errors (all `TypeError`, opting out of generic pipeline error wrapping):
  - non-Seq-compatible source: `"collect_sheet expected a Seq-compatible value (list or Flow); received <type>."`
  - non-map item at index `<n>`: `"collect_sheet expected map records; received <type> at index <n>"`
  - later record missing a first-row column: `"collect_sheet expected column <name> at row <n>"`
  - later record with an extra column: `"collect_sheet expected only column(s) from the first record; found unexpected column <name> at row <n>"`
- no column union, padding, default values, dropped fields, schema parameter, or type coercion

`render_csv(sheet)` (**Experimental**):

- accepts only a Sheet and performs no I/O; compose the returned string with existing `write` or `writeln` when output is required
- emits headers in Sheet column order and data records in Sheet row order
- converts string contents unchanged, symbols to their names, integers/floats to display text, booleans to `true`/`false`, and nil to an empty field; other headers/cells, including non-nil Outcome values and composite values, are runtime misuse errors
- separates fields with `,` and records with `\n`; fields containing comma, double quote, newline, or carriage return are double-quoted and embedded double quotes are doubled; other content, including whitespace, is preserved
- a zero-column Sheet renders as `""`; a Sheet with columns always includes a header and ends every record, including the final record, with `\n`
- preserves Sheet immutability and does not make Sheets Seq-compatible or implicitly unwrap Outcome values
- errors (all `TypeError`, opting out of generic pipeline error wrapping):
  - non-Sheet input: `"render_csv expected a Sheet"`
  - unsupported header: `"render_csv expected CSV scalar header at column <n>; received <type>"`
  - unsupported cell: `"render_csv expected CSV scalar cell at row <r>, column <c>; received <type>"`
- row/column error indexes are zero-based; failure returns no partial string and performs no output

Construction example:

```genia
people = sheet([
  [quote(name), ["Ann", "Bob", "Cara"]],
  [quote(age), [30, 22, 41]]
])
shape(people)
```

Returns `[[rows, 3], [columns, 2]]`.
Error behavior:

- non-Sheet value passed to a Sheet-only operation: `TypeError`
- unequal column lengths at construction: `TypeError` with column name
- duplicate column names at construction or in `select`: `TypeError`
- missing column in `select`: `TypeError` naming the column
- non-boolean predicate result in `where`: `TypeError`
- existing column name in `derive`: `TypeError` naming the column
- Sheet errors opt out of generic pipeline error wrapping (`_genia_preserve_pipeline_error = True`)

Implementation files:
- `src/genia/sheet.py` — `GeniaSheet` runtime value and pure helper functions
- `src/genia/builtins.py` — builtin registration
- `src/genia/utf8.py` — deterministic Sheet rendering
### Flow runtime (Phase 1)

- `stdin` is a lazy source value when used in pipelines (`stdin |> lines`)
  - `stdin |> lines` reads incrementally from the underlying source
  - `stdin()` still materializes and caches the full remaining input as a list for compatibility
- `stdin_keys` is a lazy real-time keypress Flow source (`stdin_keys |> ...`)
  - emits one keypress item at a time without waiting for newline in interactive terminal mode
  - remains single-use like other Flow values
  - in non-interactive stdin contexts, falls back to character-by-character input reads
  - existing `stdin |> lines` behavior is unchanged
- public flow helpers are thin prelude wrappers in `src/genia/std/prelude/flow.genia`:
  - `lines`
  - `evolve` (experimental)
  - `tee`
  - `merge`
  - `zip`
  - `scan`
  - `keep_some_else`
  - `rules`
  - `refine`
  - `each`
  - `collect`
  - `run`
  - `rule_*` compatibility constructors
  - `step_*` preferred constructors
  - `rules` orchestration, defaulting, and contract validation now primarily live in prelude/Genia code
  - the host rules kernel consumes normalized rule output from prelude and does not provide rule-result defaults itself
- Flow-adjacent helper extraction boundary:
  - pure helpers that operate on ordinary Genia values and return ordinary Genia values may live in prelude
  - stage composition wrappers, curried/immediate dispatch glue, and rule/refine result defaulting are prelude responsibilities when they do not create, consume, or schedule Flow values
  - validation of rule/refine result maps may live in prelude when it only checks ordinary Genia value shape and preserves the current `invalid-rules-result:` diagnostic surface
  - extraction to prelude is a no-behavior-change relocation only; it must not introduce new Flow semantics, new implicit Flow/Value conversion, or new host responsibilities
  - host execution responsibilities remain in the Python Flow kernel and host adapters
- `_seq_transform(initial_state, step, source)` is the current Python reference-host internal kernel primitive for shared ordered-source transformation over list and Flow sources:
  - `source` must be a list or Flow; other values raise `TypeError("_seq_transform expected list or flow as third argument, received <type>")`
  - list sources are traversed eagerly and return a list
  - Flow sources return a lazy, pull-based, single-use Flow and do not consume upstream until downstream pulls
  - `step(state, item)` must return a map with optional `state`, `emit`, and `halt` fields
  - omitted `state` keeps the current state; omitted `emit` defaults to `[]`; omitted `halt` defaults to `false`
  - `emit` must be a list; its values are emitted in list order
  - `halt: true` stops the whole transform after emitting the current result and does not pull later source items
  - invalid step result shape, non-list `emit`, and non-boolean `halt` raise runtime errors prefixed with `invalid-seq-transform-result:`
  - `_seq_transform` is available only to trusted prelude/runtime code and Python reference-host tests; ordinary Genia user code must use public helpers such as `map`, `filter`, `take`, `scan`, `each`, `collect`, `run`, and `evolve`
  - `_seq_transform` introduces no syntax, no Core IR node, no public Seq value/type/helper, and no implicit list/Flow conversion
- `_ensure_seq_compatible(name, source)` is the Python reference-host internal boundary primitive for validating Seq-compatible source values:
  - accepts list → returns the list unchanged
  - accepts GeniaFlow → returns the Flow unchanged without pulling any items
  - rejects all other values → raises `TypeError` via the Seq-compatible diagnostic: `"<name> expected a Seq-compatible value (list or Flow); received <type>."`
  - for direct `stdin` capability values, the diagnostic appends: `" Use stdin |> lines to adapt stdin into a Flow."`
  - `_ensure_seq_compatible` is available only to trusted prelude/runtime code; ordinary Genia user code cannot call it
  - it introduces no public Seq surface, no Core IR node, no new syntax, and no implicit list/Flow conversion
- PYTHON REFERENCE HOST: adjacent Flow `map` / `filter` stages may be fused into one internal Flow wrapper before downstream consumption:
  - fusion applies only to Flow inputs and only to adjacent `map` / `filter` stages in this phase
  - list-side `map` / `filter` behavior remains eager and reusable, with no list fusion in this phase
  - non-fusable Flow stages and consumers (`take`, `drop`, `scan`, `each`, `collect`, `run`, rules/refine helpers, and option-routing helpers) continue to consume a normal Flow-compatible value
  - the fused wrapper is internal Python host machinery, not a public runtime value or portable Core IR contract
  - observable behavior must remain unchanged: item order, callback order, side-effect order, laziness, bounded pulling, upstream close behavior, single-use enforcement, errors, stdout/stderr/exit code, and Flow display labels
- flow transforms:
  - `lines(flow_or_source)`
  - `evolve(init, f)` (experimental unbounded progression flow; emits `init` first, then repeatedly emits `f(previous_value)`)
  - `tee(flow)` returns `[left_flow, right_flow]`
  - `merge(flow1, flow2)` and `merge(pair)` where `pair` is a two-element list such as the result of `tee(flow)`
  - `zip(flow1, flow2)` and `zip(pair)` where `pair` is a two-element list such as the result of `tee(flow)`
  - `scan(step, initial_state, source)` / `source |> scan(step, initial_state)` — accepts list or Flow; returns list for list input, Flow for Flow input
  - `keep_some_else(stage, dead_handler, flow)` / `flow |> keep_some_else(stage, dead_handler)`
  - `map(f, flow)` / `filter(pred, flow)` when second arg is a flow
  - `take(n, flow)` when second arg is a flow
  - `rules(..fns, flow)` / `flow |> rules(..fns)` as a stateful rule-driven transform
  - `head(flow)` and `head(n, flow)` via stdlib aliases over `take`
- Seq-compatible sinks/materialization:
  - `each(f, source)` for list or Flow (lazy tap-style Flow stage; emits original items unchanged when consumed)
  - `collect(source)` for list or Flow (returns list)
  - `run(source)` for list or Flow (consume/traverse to completion; returns `nil`)
- stdlib rule/refine helper constructors (autoloaded from `src/genia/std/prelude/flow.genia`):
  - `rule_skip()`
  - `rule_emit(x)`
  - `rule_emit_many(xs)`
  - `rule_set(record)`
  - `rule_ctx(ctx)`
  - `rule_halt()`
  - `rule_step(record, ctx, out)`
  - `step_skip()`
  - `step_emit(x)`
  - `step_emit_many(xs)`
  - `step_set(record)`
  - `step_ctx(ctx)`
  - `step_halt()`
  - `step_step(record, ctx, out)`
Flow semantics:

- lazy, pull-based, source-bound, single-use
- consuming a flow twice raises `RuntimeError("Flow has already been consumed")`
- `tee` returns a two-element list of branch flows and keeps one shared upstream flow, buffering only as needed when branch consumption rates diverge
- `merge` preserves input ordering (`flow1` items, then `flow2` items)
- `zip` emits lockstep `[left, right]` pairs and stops when either input flow is exhausted
- `take` performs early termination (stops upstream pulling as soon as limit is reached, without over-pulling one extra item)
- `evolve(init, f)` provides deterministic discrete step progression for simulation-style pipelines while preserving the same explicit/lazy/single-use Flow contract; integer stepping is expressed with a step function such as `inc(n) -> n + 1`, `evolve(0, inc)`, and `take(n)` for bounded sequences
- short-circuiting flow consumers such as `take`, `head`, and downstream broken-pipe termination stop generator-backed upstream work promptly
- `scan` is a per-Seq stateful transform where `step(state, item)` must return `[next_state, output]`; accepts list or Flow input; `scan(list)` returns list, `scan(Flow)` returns Flow
- `scan` keeps state internal to the operator while emitting one output item per input item
- invalid flow-source misuse fails with clear Genia-facing runtime errors instead of leaked Python iterator errors
- Seq/Flow resource lifecycle (Partial):
  - a closeable source is a Seq-compatible source backed by a resource that requires cleanup when consumption ends
  - closeable sources are finalized (resource released) on: normal exhaustion, early termination, and error interruption
  - finalization is synchronous and source-local; no async cancellation or scheduler involvement
  - finalization is idempotent: further finalization requests after the first are no-ops
  - `take(n)` stops pulling after n values and finalizes any closeable upstream; `take(0)` does not pull any item values but still finalizes if the source was acquired
  - `drop(n)` pulls and discards exactly n values, then passes remaining values downstream without over-pulling
  - `drop(n) |> take(m)` pulls exactly n+m values total, then finalizes any closeable upstream
  - terminal consumers (`collect`, `run`) finalize closeable upstream on normal exhaustion or error interruption
  - finalization-error behavior: if a primary user or source error is already propagating, finalization errors are suppressed; if no primary error exists, finalization errors surface
  - list sources are never finalized; lists have no resource lifecycle
  - PYTHON REFERENCE HOST: finalization is implemented via the iterable `.close()` protocol (generator close); the `close_on_early_termination` flag on internal `GeniaSeq`/`GeniaFlow` objects controls whether cleanup is attempted; these internals are not public Genia surfaces
- host-backed Flow kernel remains intentionally small in this phase:
  - flow value creation and single-consumption enforcement
  - lazy pull-based iteration over upstream sources
  - source-bound stdin integration
  - sink/materialization boundaries such as `each`, `collect`, and `run`
  - host pull-loop integration, early-close behavior, and generator/resource cleanup
  - Flow-producing and Flow-consuming primitive boundaries used by prelude wrappers
- Flow vs Value classification model:
  - the one rule: raw values stay values, flows stay flows, only explicit bridges cross the boundary
  - Value functions (list in, value out): `sum`, `first`, `last`, `nth`, `reverse`
  - Flow functions (flow in, flow out): `keep_some`, `keep_some_else`, `rules`, `tee`, `merge`, `zip`, `head`
  - Polymorphic functions (work on both lists and flows, same-kind return): `map`, `filter`, `take`, `drop`, `scan`
  - Seq-compatible helpers (list or Flow): `each`, `collect`, `run`, `reduce`, `count`
  - Explicit adapter (value → Seq-compatible): `as_seq` (list or string → list; does not produce Flow)
  - Bridge: source (value → flow): `lines`, `evolve`, `stdin_keys`
  - Bridge: materialize (flow → value): `collect`
  - Bridge: consume (flow → effect): `run`
  - Option behavior (`some`/`none` auto-lifting in pipelines) composes with the Flow vs Value distinction but does not erase it
  - this classification is documented in `docs/cheatsheet/piepline-flow-vs-value.md` and this file
- `rules` semantics:
  - each rule is called as `(record, ctx)`
  - running `ctx` starts as `{}` for the first input item and persists across later items
  - `none`, `none(reason)`, and `none(reason, context)` mean no effect
  - `some(result)` expects a map result with optional fields:
    - `emit` (default `[]`)
    - `record` (default current record unchanged)
    - `ctx` (default current ctx unchanged)
    - `halt` (default `false`)
  - emitted values become downstream flow items in rule order
  - `halt: true` stops later rules for the current input item only
  - `rules()` is the identity stage
  - contract violations raise `RuntimeError` messages prefixed with `invalid-rules-result:`
  - rule orchestration, defaulting of omitted fields, and most contract checking are implemented in `src/genia/std/prelude/flow.genia` in this phase
  - the host rules kernel expects the prelude layer to pass normalized rule output with `emit` and `ctx` fields already present
- `keep_some_else` semantics:
  - it is an explicit Flow-stage helper for Option-returning per-item stages
  - for each input item `x`, it evaluates `stage(x)`
  - `stage(x)` receives the original raw input item, not `some(x)`
  - `some(v)` emits `v` on the main output flow
  - `none(...)` emits nothing on the main flow for that item and calls `dead_handler(x)` with the original input item
  - if `stage(x)` does not return `some(...)` or `none(...)`, it raises a clear user-facing error
  - this helper is local dead-letter routing only; it does not change global `|>` semantics or create a second live output flow
- `keep_some` semantics:
  - `keep_some(flow)` expects upstream Option items
  - `keep_some(stage, flow)` applies an Option-returning stage per item
  - `some(v)` is unwrapped to `v` inside this helper
  - `none(...)` is dropped inside this helper
- explicit CLI pipe mode is implemented:
  - `genia -p "<stage_expr>"` / `genia --pipe "<stage_expr>"`
  - runs `<stage_expr>` over `stdin |> lines`, then consumes the final Flow automatically
  - no `pipe(...)` helper function exists in this phase
  - pipe mode expects one stage expression, not a full program
  - explicit `stdin` is rejected because pipe mode provides it automatically
  - explicit `run` is rejected because pipe mode runs the final flow automatically
  - if the stage expression does not produce a flow for the automatic final `run`, pipe mode reports a clear user-facing error
  - `collect_validated` record-pipeline aggregate results have a targeted diagnostic that names the original stage expression and suggests `-c/--command` mode or explicit print-with-empty-Flow as alternatives (Python reference host)
  - if a pipe-mode stage helper receives the whole Flow when it expected per-item values, pipe mode reports clear guidance to use Flow stages such as `map(...)`, `filter(...)`, `each(...)`, `keep_some(...)`, or to switch to `-c` / `--command` for reducers such as `sum`
  - common `some(...)` pipeline mismatches in pipe mode keep the original type error but use Genia-facing stage rendering (for example `some(1)`) instead of leaking internal IR node names
### CLI argument helpers (prelude-backed over raw argv + tiny host validation primitives)

- `cli_parse(args) -> [opts, positionals]`
- `cli_parse(args, spec) -> [opts, positionals]`
- `cli_flag?(opts, name) -> bool`
- `cli_option(opts, name) -> value | none("missing-key", {key: name})`
- `cli_option_or(opts, name, default) -> value`

Behavior:

- `argv()` remains the raw host-backed CLI primitive and returns list-first data intended for normal pattern matching
- public CLI helper names are thin prelude wrappers in `src/genia/std/prelude/cli.genia`
- `cli_parse` returns a persistent map (`opts`) and remaining positional args list
- default parsing:
  - `--name` => boolean `true` unless followed by a non-option token (then `--name value`)
  - `--name=value` => string value
  - `-abc` => grouped short boolean flags
  - `-o value` => short option value when next token is non-option
  - `--` terminates option parsing
  - repeated keys are deterministic last-one-wins (`map_put` replacement semantics)
- `cli_parse(args, spec)` supports a minimal map-based spec:
  - `flags`: list of names forced to boolean behavior
  - `options`: list of names forced to value-taking behavior
  - `aliases`: map of alias name -> canonical name (string keys/values)
- grouped short options with spec raise clear `ValueError` for ambiguous mixes
- host-side CLI support is intentionally small in this phase:
  - raw `argv()`
  - spec normalization/validation
  - token-to-char decomposition
  - deterministic CLI-specific error raising
- the actual option-parsing walk now lives in prelude/Genia code
### Program entrypoint convention (runtime, no syntax)

- `main` is a runtime convention, not parser syntax
- in file mode and `-c` command mode, `main/1` is preferred over `main/0`
- arity coercion is not performed by the entrypoint selector:
  - only exact `main/1` or exact `main/0` are auto-invoked
  - if neither exists, no entrypoint call is attempted
### Refs

R25 portability status: the observable Ref behavior in this section is the
approved portable contract for the ordinary opaque `refs` capability. The
Python reference host and bounded C++ host implement it and pass the applicable
R16 shared evidence. Lock/condition-variable type,
host thread identity, fairness, wake latency, and thread count are realization
details, not portable semantics. See
`docs/design/r25-stateful-runtime-concurrency-contract.md`.

- public ref helpers are thin prelude wrappers in `src/genia/std/prelude/ref.genia`
  - `ref([initial])`
  - `ref_get(ref)`
  - `ref_set(ref, value)`
  - `ref_is_set(ref)`
  - `ref_update(ref, updater)`
  - these wrappers are the canonical user-facing API surface and carry Markdown docstrings for `help(...)`
  - the underlying ref behavior remains host-backed and unchanged in this phase

Behavior:

- refs are synchronized host objects backed by a Python `threading.Condition`
- `ref_get` / `ref_update` on an unset ref **block the calling thread indefinitely** until another thread calls `ref_set`
- there is no timeout — a ref that is never set will block forever
- `ref_update` holds the internal lock while calling the updater function, so the updater should be fast and must not re-enter the same ref
- `ref_set` wakes all blocked `ref_get` / `ref_update` waiters
- reads and writes are serialized through a single condition variable per ref
### Host-backed concurrency

R25 portability status: the local Process/mailbox observations in this section
are the approved portable contract for `process_primitives`. The Python
reference host and bounded C++ host implement them and pass applicable R16
shared evidence. Actor behavior remains Python-host-only
and is excluded from R25; portable actors belong to R38.

- public process helpers are thin prelude wrappers in `src/genia/std/prelude/process.genia`
  - `spawn(handler)`
  - `send(process, message)`
  - `process_alive?(process)`
  - `process_failed?(process)`
  - `process_error(process)`
  - these wrappers are the canonical user-facing API surface and carry Markdown docstrings for `help(...)`
  - the underlying process behavior remains host-backed and unchanged in this phase

Behavior:

- each process has FIFO mailbox (backed by Python `queue.Queue`)
- one handler invocation at a time per process
- implemented with host daemon threads
- if the handler throws an exception on any message:
  - the process enters fail-stop state
  - the error is cached as a string
  - the worker thread exits
  - future `send` calls raise `RuntimeError`
  - `process_failed?` returns `true`
  - `process_error` returns `some(error_string)`
- there is no restart mechanism for processes (use cells/actors for restartable workers)
- there is no graceful shutdown — the daemon thread runs until it fails or the program exits
### Cell helpers (Phase 1, runtime-backed fail-stop)

R25 portability status: the Cell observations in this section are the approved
portable contract for the independently claimable `cell_primitives`
capability. The Python reference host and bounded C++ host implement them and
pass applicable R16 shared evidence. Cell's specific
restart is not a general supervision policy and creates no Actor precedent.

- public prelude helpers:
  - `cell(initial)`
  - `cell_with_state(state_ref)`
  - `cell_send(cell, update_fn)`
  - `cell_get(cell)`
  - `cell_state(cell)`
  - `cell_failed?(cell)`
  - `cell_error(cell)`
  - `restart_cell(cell, new_state)`
  - `cell_status(cell)`
  - `cell_alive?(cell)`
  - `cell_stop(cell)`

Behavior:

- cells process queued updates asynchronously and serialize them one at a time
- successful updates replace cell state in order
- failed updates do not change state
- on update failure:
  - the cell caches an error string
  - `cell_status(cell)` becomes `"failed"`
  - `cell_failed?(cell)` becomes `true`
  - `cell_error(cell)` returns `some(error_string)`
  - later queued updates are discarded
  - future `cell_send` and `cell_get` raise `RuntimeError`
- `cell_state(cell)` is an alias for `cell_get(cell)`
- `restart_cell(cell, new_state)`:
  - replaces state with `new_state`
  - clears cached failure/error and stopped state
  - marks the cell ready again
  - relaunches the worker thread if it has exited (e.g. after `cell_stop`)
  - discards queued pre-restart updates in this phase
- nested `cell_send` calls made during an update are staged and are committed only if that update succeeds
- `cell_stop(cell)` gracefully stops the cell:
  - queued updates already in the mailbox are processed before the worker exits
  - `cell_status(cell)` becomes `"stopped"` immediately
  - `cell_send` raises `RuntimeError` after stop
  - `cell_get` still returns the last state
  - calling `cell_stop` on a stopped or failed cell is a no-op
  - `cell_alive?` returns `false` after the worker exits
### Actor helpers (Phase 1, prelude-backed over cells)

- public prelude helpers in `src/genia/std/prelude/actor.genia`:
  - `actor(initial_state, handler)`
  - `actor_send(actor, msg)`
  - `actor_call(actor, msg)`
  - `actor_alive?(actor)`
  - `actor_stop(actor)`
  - `actor_restart(actor, new_state)`
  - `actor_state(actor)`
  - `actor_failed?(actor)`
  - `actor_error(actor)`
  - `actor_status(actor)`
- host-backed helpers:
  - `_actor_validate_effect` validates the handler effect shape for fire-and-forget sends
  - `_actor_call_update` handles handler invocation, effect validation, reply delivery, and error recovery for synchronous calls
Behavior:

- `actor(initial_state, handler)` creates an actor backed by a cell
  - this is a public Python-reference-host surface in the current phase, not a shared cross-host contract category
  - the handler shape is `handler(state, msg, ctx) -> effect`
  - the actor is represented as a map with internal `_cell` and `_handler` keys
- supported effect shapes:
  - `["ok", new_state]` — update state only
  - `["reply", new_state, response]` — update state and deliver a response value
  - `["stop", reason, new_state]` — commit final state and stop the actor
- invalid handler return shapes (not matching any supported effect) mark the actor as failed with a clear error showing the received value and expected shapes
- `actor_send(actor, msg)` enqueues the message for asynchronous processing
  - the handler is called with `(current_state, msg, {})` inside a cell update
  - the handler may return `["ok", new_state]`, `["reply", new_state, response]`, or `["stop", reason, new_state]`
  - for `actor_send`, any response value from a `["reply", ...]` effect is discarded
  - for `["stop", ...]`, the final state is committed and the actor stops after the current message
  - messages are processed one at a time in FIFO order
- `actor_call(actor, msg)` sends a message and blocks until the handler replies
  - a one-shot ref is created and passed in `ctx` as `reply_to`
  - the handler is called with `(current_state, msg, {reply_to: <ref>})`
  - for `["reply", new_state, response]`: the caller receives `response`
  - for `["ok", new_state]`: the caller receives `new_state` as the reply
  - for `["stop", reason, new_state]`: the caller receives `none("actor-stopped")`
  - if the handler throws, the caller receives `none("actor-error")` and the actor enters failed state
  - the same handler works correctly with both `actor_send` and `actor_call`
- `actor_alive?(actor)` reports whether the backing cell worker thread is alive
- `actor_stop(actor)` gracefully stops the actor:
  - queued messages already in the mailbox are processed before the worker exits
  - after stop, `actor_send` and `actor_call` raise `RuntimeError`
  - `cell_get` on the backing cell still returns the last state
  - `actor_alive?` returns `false` after the worker exits
  - calling `actor_stop` on a stopped or failed actor is a no-op
- `actor_restart(actor, new_state)` restarts a failed or stopped actor:
  - resets state to `new_state` and clears failure/stopped status
  - relaunches the worker thread if it has exited (e.g. after `actor_stop`)
  - the handler is preserved
  - returns the actor reference
- `actor_state(actor)` reads the current state without sending a message
  - equivalent to `cell_get` on the backing cell
  - raises `RuntimeError` if the actor has failed
- `actor_failed?(actor)` returns `true` if the actor has failed
- `actor_error(actor)` returns `none` when healthy, or `some(error_string)` when failed
- `actor_status(actor)` returns `"ready"`, `"failed"`, or `"stopped"`
- failure semantics are inherited from the backing cell:
  - handler exceptions or invalid effect shapes mark the actor as failed
  - subsequent `actor_send` raises `RuntimeError` after failure
  - `actor_call` on a failing handler returns `none("actor-error")` instead of blocking
- actors are a thin convenience layer; internal cell state is accessible through the actor map for advanced use in this phase
- Concurrency invariants are locked by `tests/test_invariant_concurrency.py`:
  - Ref: `ref_set` visible to all threads; `ref_update` serialized; `ref_get` blocks until set
  - Process: FIFO message ordering; serialized handler execution; permanent fail-stop on exception
  - Cell: FIFO update ordering; failure preserves last good state; `restart_cell` clears failure and discards stale; nested `cell_send` rolls back on failure
  - Actor: message ordering (via cell); `actor_call` blocks until reply; `["stop", ...]` rejects subsequent sends; invalid effect marks failed
  - Not guaranteed: no cross-actor ordering, no timeout on `ref_get`, no deterministic scheduling, no supervision, no selective receive, no backpressure

Not implemented yet:

- selective receive
- timeouts in message receive
- deterministic scheduling
- supervision / links / monitors
- actor-specific syntax
### Integer arithmetic portability (Experimental, R17 complete)

- Genia integers exclude booleans and have arbitrary-precision integer semantics.
- For two integer operands, `+`, `-`, `*`, `%`, `<`, `<=`, `>`, and `>=`
  produce the mathematically exact integer result or relational result regardless
  of magnitude. Unary `-` likewise produces the mathematically exact integer.
- These integer operations do not overflow, wrap, saturate, or truncate because
  of a host's fixed-width integer representation. A host must not silently
  narrow Genia integers to a fixed-width host integer.
- This contract is independent of the existing R9 JSON safe-integer boundary.
  The JSON-domain restriction remains exactly `[-9007199254740991,
  9007199254740991]` at `json_encode`/`json_decode`; it does not bound ordinary
  Genia integer arithmetic.
- `/` and float-producing numeric behavior are outside R17 and are unchanged.
### Portable value equality (Experimental, R18 complete)

Genia has one semantic equality relation. `==` denotes it, `!=` is exactly its
logical negation, and it is not user-overloadable: no Genia function, Template,
matcher, or provider can supply, replace, or intercept it. E18-1 adds no public
function, builtin, operator, or syntax.

In the Python reference host the relation is
`src/genia/equality.py::genia_equal`, and the evaluator's `==`/`!=` dispatch is
routed through it. The relation dispatches over an explicit list of Genia
semantic kinds; it does not fall back to host-language equality for unrecognized
objects, so a host default cannot define Genia behavior.

Landed by E18-1:
- Values of different semantic kinds are unequal, and kind difference produces
  `false` rather than an error. The integer/float bridge below is the only
  cross-kind exception.
- Booleans are a distinct semantic kind and never compare equal to numbers:
  `true == 1` and `false == 0` are both `false`. This holds even though the
  reference host represents booleans as integers.
- Equal integers are equal. An integer equals a float exactly when the float is
  finite, integral, and denotes the same mathematical integer; the comparison is
  exact and does not convert an arbitrary-precision integer to a host float.
  R17 integer semantics are unchanged.
- `0.0 == -0.0` is `true`; matching infinities are equal; opposite infinities are
  not; NaN is unequal to everything including itself, and that non-reflexivity
  propagates through structural containers.
- Structural values compare recursively by named semantic contents, not by
  runtime allocation identity: strings, symbols, Lists, Pairs, `some`/`none`/`err`
  Outcomes, represented values, RNG states, Format values, byte values,
  ZIP entries, and Sheets. Two independently constructed byte values with the
  same bytes are equal. Outcome constructors are never equal across kinds.
  Represented values compare by facet plus carried value, and representation
  layers remain ordered.
- Equality is pure: it performs no IO, acquires nothing, invokes no user code or
  Template, consumes no Seq or Flow, dereferences no Ref, inspects no
  Cell/Process/provider state, and mutates neither operand.

Landed by E18-2 (maps and map keys):

- Map equality is equality of mappings, not of insertion history. Two maps are
  equal when they hold the same number of mappings and every mapping in one has
  a Genia-equal key in the other with a Genia-equal mapped value. Equal-content
  maps are therefore equal even when their R17 iteration orders differ.
- Mapped values use the full relation, so any Genia value may be a map value. A
  map holding NaN as a value is consequently not reflexive; R18 requires
  reflexivity of legal map *keys*, not of every Genia value.
- For legal keys, map key identity is exactly `==`. One relation governs lookup,
  presence, insertion, replacement, removal, and map-literal duplicate-key
  detection. Equal legal keys are interchangeable in all of them; unequal legal
  keys are never collapsed by host container coercion. In particular `true` and
  `1` are different keys, `false` and `0` are different keys, `1` and `1.0` are
  one key, and `0.0` and `-0.0` are one key.
- The legal public key families are exactly: booleans, integers, non-NaN floats
  including infinities, strings, symbols, and recursively legal Pairs, Lists, and
  represented values. No other family is keyable.
- Every legal key satisfies `k == k`. NaN is therefore not a legal key, and
  neither is any otherwise-legal structural key containing NaN at any depth.
  Illegal keys are rejected deterministically on every map operation, not only on
  insertion, and a rejection never discloses a protected payload or an internal
  canonical key form.
- R17 map order semantics are unchanged. Order is a separate observable from
  equality.

Landed by E18-3 (the three families that are never compared by contents):

- **Identity-bearing runtime values** compare only by logical runtime entity
  identity. Equivalent visible state or configuration never implies equality, and
  comparison never dereferences, invokes, advances, or inspects the entity behind
  the value — it reads no Ref contents, no Cell or Process state, no Seq or Flow
  elements, no provider configuration, no module exports, and no closure
  environment. The family covers functions and function groups, host and native
  callables, named pattern and Template matcher values, model callables and
  providers, retrieval index handles, modules, Refs, Cells, Processes, Seq and
  Flow values, promises, meta-environments, configuration providers,
  declassification authorities, host and IO handles, and lifecycle values.
- **Protected carriers** compare by carrier identity only, as described in the
  configuration/secrets section above. The relation may reveal that two names
  refer to the same carrier; it must never reveal whether two independently
  acquired carriers hold equal payloads. That non-interference holds through
  `==`, `!=`, recursive structural comparison at any depth, Lists, Pairs,
  Outcomes, maps, keys, rendering, and rejection diagnostics.
- **Opaque semantic tokens** are a contract/design family with **no implemented
  source-level feature**. R18 adds no token value, token-domain declaration,
  minting API, or syntax, and implements no storage or `Revision`; no token can be
  created or observed from Genia source. What exists is the internal rule that a
  token is equal to another exactly when its hidden domain, provenance, and
  semantic identities are all equal, compared as data with no issuer contact and
  no token-supplied comparator. The family is closed to comparator extension and
  open to domain extension, so a future built-in or user-defined token domain can
  participate without making `==` overloadable. Opaque tokens are not legal map
  keys.
These three families are terminal: structural comparison stops when it reaches
one, and none of them are legal map keys.

Landed by E18-4 (every equality-like surface uses the one relation):

For the same two operands, all of the following answer exactly as `==` does:

- `==` and `!=`
- a literal pattern tested against a candidate — a `1` literal matches `1.0` but
  not `true`, and a kind difference is a mismatch, never an error
- a repeated pattern binding — a clause shaped like `f(x, x)` accepts `(1, 1.0)`
  and rejects `(true, 1)`
- `assert_eq(actual, expected)`, which succeeds exactly when `actual == expected`
  and otherwise fails through its existing failure path unchanged
- the meta-circular evaluator's `==` and `!=`, so an expression evaluated through
  `eval` agrees with the same expression evaluated directly
- map lookup, presence, insertion, replacement, removal, and duplicate-key
  detection, for legal keys
- Sheet column-name identity, for legal column names
- recursive List, Pair, Outcome, and represented-value comparison, and map
  equality

No surface consults host-language equality or a host container's key rules to
answer a semantic sameness question.

Sheet column names use the same legal family and the same identity relation as
map keys: booleans, integers, non-NaN floats, strings, symbols, and recursively
legal Pairs, Lists, and represented values. Names that are not Genia-equal are
distinct columns, so `true` and `1` are two columns rather than a duplicate.
Values outside that family — including maps and Outcomes — are rejected at Sheet
construction, and protected values remain rejected with their existing message.
R18 ships 24 shared cases under `spec/eval/` and `spec/error/` covering every
equality family reachable from Genia source, verified both in-process and through
the R16 generic host protocol with zero cases reported `unsupported`.

**What R18 did not do.** Each of these is a plausible misreading of a release
called "Portable Value Equality", so each is stated explicitly:

- Python remains the reference and only production host; **no C++ host was
  implemented**.
- **No user-overloadable `==`.** No function, Template, matcher, provider, token,
  or future open-function mechanism can supply, replace, extend, or intercept the
  relation. Programs may define ordinary predicates for approximate or
  domain-specific equivalence; those can never redefine `==`, literal-pattern
  equality, duplicate-binding consistency, or map-key identity.
- **No token-domain syntax, minting API, or token value.** Opaque semantic tokens
  have no source-level surface: none can be created or observed from Genia
  source. Their equality rule and future extensibility are a contract/design
  property, not an implemented feature.
- **No storage `Revision`.** A `Revision` is a motivating future example of the
  opaque-token family, not something R18 builds.
- **Map iteration order is unchanged** and remains the R17 contract, distinct
  from map equality.
- No approximate equality, ordering, public hashing API, or deep-diff
  diagnostics; no new public function, builtin, operator, syntax, capability, or
  Core IR node. R18 changed evaluator and runtime semantics only.

See `docs/releases/R18.md` for the release summary and
`docs/design/r18-portable-value-equality-contract.md` for the approved contract.
### Unicode and diagnostic portability (Experimental, R19 complete)

- **U1 — code-point semantics.** Genia strings are sequences of Unicode
  scalar values. `src/genia/utf8.py`'s internal `utf8_codepoints` iterates
  scalar values (never grapheme clusters, never UTF-8 bytes), and
  `utf8_safe_slice_by_codepoint(s, start, end)` slices by code-point index
  with exact bound normalization: an omitted start is `0`, an omitted end is
  the code-point length, a negative index counts from the end, a bound below
  `0` after adjustment clamps to `0`, a bound above length clamps to length,
  and a normalized `start >= end` yields the empty string. A combining
  sequence such as `"e" + U+0301` is two code points, not one grapheme — no
  implicit normalization is performed and canonically equivalent but
  differently encoded sequences remain distinct values, so this never
  changes `==` (R18 unaffected). These helpers are internal today; no new
  public string-indexing syntax or slicing builtin was added by E19-1.
- **U2 — strict UTF-8 boundaries.** `utf8_byte_length(s)` and
  `utf8_is_boundary(s, offset)` (`src/genia/utf8.py`) report UTF-8 byte
  length and whether a byte offset is a valid scalar boundary (`0` and the
  byte length are always boundaries; an interior offset is a boundary only
  at the first byte of an encoded scalar). The public `utf8_decode(bytes)`
  builtin (`src/genia/builtins.py`) decodes strict UTF-8: on malformed input
  it raises deterministically with the message
  `utf8_decode invalid UTF-8 at byte offset N`, where `N` is the byte offset
  of the first invalid byte — a portable integer fact, not host-specific
  decoder wording. No implicit U+FFFD replacement occurs and no raw
  Python/host decoder exception text crosses this boundary.
- **U3 — deterministic debug escaping.** `format_debug` on a string
  (`src/genia/utf8.py`) surrounds it with ASCII double quotes and escapes
  `\` -> `\\`, `"` -> `\"`, newline -> `\n`, carriage return -> `\r`, tab ->
  `\t`; every other C0 control (`U+0000..U+001F`), DEL (`U+007F`), and every
  C1 control (`U+0080..U+009F`) renders as lowercase `\uXXXX` (exactly four
  hex digits); every other Unicode scalar value renders literally.
  `format_display` on a string remains the raw character content with no
  surrounding quotes. Neither rule depends on host terminal behavior,
  locale, or a Unicode printability table.

- **Diagnostic portability (E19-2 through E19-4).** A mechanical inventory of the exact-stderr `spec/error` and `spec/parse` failure cases (`docs/analysis/r19-diagnostic-mechanical-inventory.md`) classified each by semantic
  family and portability class. The one confirmed host-`repr()` leak was fixed: a "No matching case" runtime-dispatch failure renders its call arguments with Genia's own `format_debug` as a list, for example
  `with arguments ["hello"]` rather than a Python tuple repr. The large "expected X, received Y" family already renders through `_runtime_type_name`, a Genia-authored type-name table. A cross-surface leak audit
  (`docs/analysis/r19-host-default-leak-audit.md`) found no further fixable leak; recorded, deliberately unchanged items are shell-pipeline stdout decoding with `errors="replace"`, the explicit `python.*` bridge's exception
  wrapper, and incidental `str(exc)` detail in some `builtins.py` Outcome contexts (`read_file`, `write_file`, `zip_read`/`zip_write`, config-resource backends), which is never part of the portable diagnostic contract.
- R19 adds no grapheme-cluster model, normalization or collation, locale-aware formatting, numeric-model change, new public string API, or Core IR change. R19 is **complete**
  (`docs/design/r19-unicode-diagnostic-portability-contract.md`, `docs/analysis/r19-release-truth-audit.md`, `docs/releases/R19.md`).

### Host-backed persistent associative maps (Phase 1 bridge; ordering Experimental, R17 complete)

- public map helpers are exposed from `src/genia/std/prelude/map.genia`
  - `map_new()`
  - `map_get(map, key)`
  - `map_put(map, key, value)`
  - `map_has?(map, key)`
  - `map_remove(map, key)`
  - `map_count(map)`
  - `map_items(map)`
  - `map_item_key(item)`
  - `map_item_value(item)`
  - `map_keys(map)`
  - `map_values(map)`
  - `pairs(xs, ys)`
  - these helper names are the canonical user-facing API surface and carry Markdown docstrings for `help(...)`
  - the underlying persistent map runtime remains host-backed and unchanged in this phase

Behavior:

- map values are opaque runtime values (`<map N>`) and do not expose host methods
- module imports produce opaque module namespace values (`<module name>`)
- `map_new` returns an empty map with an empty key order
- `map_put` and `map_remove` are persistent (return a new map, do not mutate input map)
- a newly associated key is appended to the end of the current key order
- `map_put(map, existing_key, new_value)` replaces the value without changing
  that key's position
- `map_remove` removes a present key while preserving the relative order of the
  remaining keys; removing a missing key leaves the ordering unchanged
- re-inserting a key after removal appends that key at the current end
- map literals associate entries from left to right; when a literal repeats a
  key, the last value wins while the key retains the position established by
  its first association
- `map_get` returns stored value or `none("missing-key", {key: key})` when key is missing
- `map_has?` returns `true`/`false`
- `map_count` returns entry count
- `map_items` returns a list of `[key, value]` pairs in the deterministic map order above
- `map_item_key` extracts the key from a `[key, value]` pair produced by `map_items`
- `map_item_value` extracts the value from a `[key, value]` pair produced by `map_items`
- `map_keys` returns all keys in the deterministic map order above
- `map_values` returns the corresponding values in that same order
- portable map order is distinct from map equality, map pattern matching, and
  `json_encode`'s sorted object-member-name output; R17 changes none of those
- map patterns continue to match structurally by content rather than order
- map equality and the map-key relation were resolved by R18 E18-2; see
  "Portable value equality" above. Two maps with equal mappings compare equal
  even when their iteration orders differ, and none of the order rules in this
  section changed
- `pairs(xs, ys)` zips two lists into a list of two-element list pairs:
  - pair order follows input order
  - each output item is `[x, y]`, not a tuple or Pair value
  - the result length is bounded by the shorter input list
  - `pairs([], ys)` returns `[]`
  - `pairs(xs, [])` returns `[]`
  - `pairs([], [])` returns `[]`
  - first-argument non-list values raise `TypeError("pairs expected a list as first argument, received <type>")`
  - second-argument non-list values raise `TypeError("pairs expected a list as second argument, received <type>")`
  - no implicit list coercion, Flow consumption, map traversal, padding, default fill value, or option wrapping is performed
- list keys are supported by recursive structural key canonicalization in runtime
- host tuple keys remain a runtime-level interop accommodation handled by the same
  canonicalization; they are not a public Genia key family
- invalid map arguments and unsupported key types raise clear `TypeError`
- the legal public key families and the key relation itself are defined by R18
  E18-2; see "Portable value equality" above
### Record validation helpers (Phase 1 minimal Outcome-aware data pipeline surface)

- public validation helpers are exposed from `src/genia/std/prelude/validation.genia`
  - `validate_required(field, record)`
  - `validate_optional(field, record)`
  - `validate_optional(field, record, validator)`
  - `validate_field(field, predicate, expected, record)`
  - `validate_record(record, validators)` (**Experimental**)
  - `validate_record(record, validators, context)` (**Experimental**)
  - `validate_each(source, validator)` (**Experimental**)
  - `diagnostic_error(index, field, reason, context)` (**Experimental**)
  - `diagnostic_skipped(index, field, reason, context)` (**Experimental**)
  - `diagnostic_reason(diagnostic)` (**Experimental**)
  - `diagnostic_field(diagnostic)` (**Experimental**)
  - the helpers operate on one map record or list of records at a time; no schema DSL, Sheet behavior, or report helper is introduced in this phase
  - the helpers use existing Outcome values: valid records return `some(record)` or `some(clean_record, context?)`, and recoverable user-data problems return `err(reason, context)`

Behavior:

- `validate_required(field, record)`:
  - requires `record` to be a map
  - returns `some(record)` when `record` contains `field`
  - returns `err("missing required field", context)` when `field` is absent
- `validate_field(field, predicate, expected, record)`:
  - requires `predicate` to be callable; non-callable predicates raise `TypeError("validate_field expected predicate to be callable")`
  - requires `record` to be a map
  - returns `err("missing required field", context)` when `field` is absent
  - calls `predicate(value)` with raw callback invocation when the field is present
  - returns `some(record)` only when the predicate result is exactly `true`
  - returns `err("invalid field", context)` when the predicate result is not exactly `true`
- missing-field diagnostic context includes `row` when the record has a `row` field, plus `field` and `reason`
- invalid-field diagnostic context includes `row` when present, plus `field`, `expected`, `actual`, and `reason`
- simple nested field paths are supported for validation helper lookup and diagnostic metadata by passing a dot-joined string field such as `"patient.name"` or `"patient.address.zip"`; diagnostics keep that full path in `field`
- this nested validation path support does not add general field-path syntax, wildcards, recursive descent, list index paths, or a public path value type
- runtime/programmer misuse remains a runtime error; it is not converted into a recoverable row diagnostic
- validation diagnostic context is **Experimental** and stable only per the producing helper/result layer; there is no universal validation diagnostic context shape:
  - `validate_required` and the missing-field branch of `validate_field` stably expose `field` and `reason`, plus `row` only when the input record contains a `row` field
  - the invalid-field branch of `validate_field` stably exposes `field`, `expected`, `actual`, and `reason`, plus `row` only when the input record contains a `row` field
  - `field` is the caller-supplied flat or supported dot-joined field path; `row`, `expected`, and `actual` preserve the corresponding Genia values without coercion
  - map entry order and rendered diagnostic formatting are representation details, not additional validation-context semantics
- `validate_optional` keeps its currently documented Outcome shapes, but issue #405 does not establish one shared stable context schema across its absence, success, nested-validator error, and validator-returned-`none(...)` branches; fields beyond each branch's existing behavior remain branch-specific
- shared specs currently cover selected validation helper behavior only: valid-record, required-field present/missing, optional-field present/absent/invalid, simple nested validation path success/missing diagnostics, invalid-field, non-callable-predicate misuse cases, selected `validate_each/2` behavior (empty list, `some(...)` preservation, and mixed `some(...)` / `none(...)` / `err(...)` preservation), and selected `validate_each/2` misuse diagnostics (non-list/non-Flow source, non-callable validator, and non-Outcome validator result)
- multi-record splitting/collection, summary reports, Sheet integration, and broader path semantics are not implemented by these helpers
### Field/index validation diagnostic helpers (**Experimental** contract)

Implemented in the Python reference host:

- public names: `diagnostic_error/4`, `diagnostic_skipped/4`, `diagnostic_reason/1`, and `diagnostic_field/1`
- `diagnostic_error(index, field, reason, context)` returns exactly `{index: index, field: field, kind: quote(error), reason: reason, context: context}`
- `diagnostic_skipped(index, field, reason, context)` returns exactly `{index: index, field: field, kind: quote(skipped), reason: reason, context: context}`
- constructor arguments are ordinary Genia values and are preserved without validation, coercion, or context wrapping; only `kind` is supplied by the constructor
- `diagnostic_reason(diagnostic)` requires a map and returns its `reason` value using existing map lookup semantics
- `diagnostic_field(diagnostic)` requires a map and returns its `field` value using existing map lookup semantics
- an accessor given a non-map is a runtime misuse error; an absent requested key returns `none("missing-key", {key: <key>})`
- standard callable arity handling rejects any arity other than the public arities above
- the helpers produce and inspect ordinary immutable maps; they perform no I/O and mutate no value
- this helper-specific five-key shape does not replace or normalize producer-specific validation context, `validate_record` field diagnostics, or `collect_validated` aggregate diagnostics
- `collect_validated` does not automatically consume, create, or transform these helper maps
- no universal validation diagnostic schema, reporter framework, logging framework, Sheet behavior, Flow behavior, Outcome change, parser syntax, or Core IR change is introduced

PYTHON REFERENCE HOST:

- public wrappers live in `src/genia/std/prelude/validation.genia`
- two narrow option-aware constructor primitives in `src/genia/builtins.py` preserve `none(...)` arguments instead of applying ordinary none-propagation
- accessors reuse existing `map_get` behavior
- shared eval/error specs cover exact constructor/accessor output, missing keys, non-map misuse, and public arities; Genia-native validation tests cover constructor value preservation and accessor behavior
### validate_record helper (**Experimental**)

- public names: `validate_record/2` and `validate_record/3`
- exposed as prelude-backed wrappers over host-backed `_validate_record` in `src/genia/builtins.py`; public surface lives in `src/genia/std/prelude/validation.genia`
- `validate_record(record, validators)` and `validate_record(record, validators, context)` compose field validators over one map record and return one record-level Outcome
- `record` must be a Genia map; non-map input is a runtime misuse error
- `validators` must be a Genia map whose keys are field path strings and whose values are callable validators
  - non-map `validators` is a runtime misuse error
  - non-callable validator values are a runtime misuse error
  - each validator callable receives the original `record` and must return an Outcome
  - validator returning a non-Outcome value is a runtime misuse error
- validators execute in deterministic Genia map iteration order; all validators run even when earlier validators return `err(...)` so that all field diagnostics can be collected
- field-level Outcome interpretation:
  - `some(value)` or `some(value, context)` — the validated field value is added to `clean_record` under the validator map key
  - `none(...)` — successful absence; the field is not added to `clean_record` and does not cause record failure
  - `err(reason, context?)` — field-level validation failure; appended as a diagnostic
- field-error diagnostic shape: `{field: <key>, status: quote(error), reason: <field reason>, context: <some(ctx) or none("nil")>}`
  - the stable field-diagnostic keys are `field`, `status`, `reason`, and `context`
  - `field` is the validator-map key, `status` is `quote(error)`, `reason` preserves the field `err(...)` reason, and `context` preserves the field `err(...)` context or is `none("nil")` when absent
- record-level Outcome:
  - no `err(...)` from any validator: `some(clean_record, record_context?)` where `clean_record` contains only present validated values
  - one or more `err(...)` results: `err(quote(record_validation_failed), record_context_with_diagnostics)`
- optional third argument `context` is preserved in the record-level Outcome for both success and failure
- on failure, `diagnostics` is the stable record-level key added to the supplied record context (or to a new context map); other caller-supplied context keys are preserved and are not validation-defined fields
- does not mutate the input record; does not add a schema DSL, Sheet behavior, Flow collector, value-template integration, or new path syntax
### collect_validated helper (**Experimental**)

- public name: `collect_validated/1`
- registered as a host-backed builtin in `src/genia/builtins.py`
- accepts a Seq-compatible source: list or Flow
  - non-list/non-Flow input raises a runtime error
- every item produced by the source must be an Outcome value; non-Outcome items raise `TypeError("collect_validated expected Outcome items, received <type> at index <n>")`
- `some(value)` and `some(value, context)` append `value` to the `clean` list; the `some` context is ignored in this first version
- `none(...)` appends a diagnostic with `kind: quote(skipped)`
- `err(...)` appends a diagnostic with `kind: quote(error)`
- diagnostic shape:
  ```
  {index: n, kind: quote(skipped) | quote(error), reason: reason, context: some(ctx) | none("nil")}
  ```
  - `index` is the zero-based source item position
  - `context` is `some(ctx)` when the Outcome carried a context, or `none("nil")` when absent
- the stable aggregate-diagnostic keys are `index`, `kind`, `reason`, and `context`; there is no guarantee that nested `context` maps share one schema across producers
- result shape: `{clean: [...], diagnostics: [...]}`
- does not create Sheets itself; pass `clean` to `collect_sheet(records)` (Experimental) for an explicit, separate conversion to Sheet — `collect_validated` and `collect_sheet` remain two distinct terminal steps, not merged
- does not change Outcome semantics, pipeline short-circuit behavior, `keep_some`, or existing validation helpers
- `collect_validated` is terminal: it consumes the entire finite source to produce complete output; infinite Flow sources must be bounded before calling `collect_validated`
- error shared specs cover wrong arity (0 args, 2 args), non-Seq source, and non-Outcome item cases
- eval shared specs cover empty source, all clean, mixed `some`/`none`/`err`, `some` context ignored, bare `none`, `err` without context, and Flow-compatible source
### validate_each helper (**Experimental**)

- public name: `validate_each/2`
- exposed as a prelude-backed wrapper over host-backed `_validate_each` in `src/genia/builtins.py`; public surface lives in `src/genia/std/prelude/validation.genia`
- `validate_each/2` accepts list and Flow sources. List input returns a list of Outcome values. Flow input returns a lazy Flow of Outcome values. The validator must return an Outcome for each item. validate_each does not aggregate; collect_validated remains the aggregation helper. validate_each/3 is not implemented.
- `source` must be a list or Flow; non-list/non-Flow input is a runtime `TypeError`
- `validator` must be callable; non-callable validators raise `TypeError`
- classifies each source item before invoking the validator:
  - upstream `err(...)` items are preserved unchanged; the validator is not called
  - upstream `none(...)` items are preserved unchanged; the validator is not called
  - upstream `some(payload)` items: the validator is called with the unwrapped `payload`; the validator result is returned as the item output
  - plain records and values: the validator is called with the item directly; validator runtime errors propagate unchanged
- every validator result must be an Outcome (`some(...)`, `none(...)`, or `err(...)`); non-Outcome results raise `TypeError("validate_each expected validator to return an Outcome, received <type> at index <n>")`
- list input returns a list of Outcome values in source order with output length equal to input length
- Flow input returns a lazy derived Flow of Outcome values; validation happens during consumption; single-use and finalization behavior follow existing Flow semantics
- does not aggregate diagnostics; aggregation remains the job of `collect_validated`
- composes with `validate_record` as the per-item validator; composes with `collect_validated` as the terminal aggregator
- `validate_each/3`, Sheet behavior, and context merging are not implemented in this phase

PYTHON REFERENCE HOST:

- implemented in `src/genia/builtins.py` alongside other validation helpers
- list items are validated using the existing raw callable invocation path
- Flow items are validated lazily during Flow consumption using the existing Flow stage pattern
- Outcome detection uses a local `_is_validation_outcome` helper; `collect_validated` applies equivalent inline Outcome checks
### Primitive Option model (Phase 3 canonical access surface on runtime-backed values)

- option values:
  - `none`
  - `none(reason)`
  - `none(reason, context)`
  - `some(value)`
- public option helpers are thin prelude wrappers in `src/genia/std/prelude/option.genia`
  - these wrappers are the canonical user-facing API surface and carry Markdown docstrings for `help(...)`
  - the underlying runtime behavior remains host-backed and unchanged in this phase
  - `none` remains a runtime literal/value, not a prelude wrapper
- option/query helpers:
  - `get(key, target)`
  - `get?(key, target)`
  - `unwrap_or(default, opt)`
  - `is_some?(opt)` / `some?(opt)`
  - `is_none?(opt)` / `none?(opt)`
  - `or_else(opt, fallback)`
  - `or_else_with(opt, thunk)`
  - `absence_reason(opt)`
  - `absence_context(opt)`
- maybe-flow helpers:
  - `map_some(f, opt)`
  - `flat_map_some(f, opt)`
  - `then_get(key, target)`
  - `then_first(target)`
  - `then_nth(index, target)`
  - `then_find(needle, target)`
- option-returning stdlib helpers:
  - `first(list)`
  - `first_opt(list)` (compatibility alias)
  - `last(list)`
  - `find(string, needle)`
  - `find_opt(predicate, list)`
  - `nth(index, list)`
  - `nth_opt(index, list)` (compatibility alias)
  - `parse_int(string)`
  - `parse_int(string, base)`
Absence semantics:

- `some(value)` means present.
- `none`, `none(reason)`, and `none(reason, context)` are one absence family.
- `none` is shorthand for `none("nil")`.
- legacy surface `nil` also evaluates to `none("nil")`; there is no separate runtime nil value.
- `reason` must be a string.
- `context` / metadata must be a map when present.
- reason/context metadata does not create a new success/failure category.
- absence is not the same as a runtime error.
- helpers treat all `none...` forms as absence.
- `parse_int` uses `none("parse-error", context)` for invalid integer text instead of raising for ordinary parse failure
- ordinary function calls short-circuit on `none(...)` arguments unless the callee explicitly handles absence
- list higher-order functions (`reduce`, `map`, `filter`) are pure prelude implementations using `apply_raw`; `none(...)` list elements are delivered to the callback without short-circuit; `reduce` additionally accepts Flow as Seq-compatible input and does not short-circuit on `none(...)` as initial accumulator
- a present key whose stored value is legacy `nil` now appears as `some(none("nil"))`

`get?` semantics:

- `get(key, target)` is the canonical maybe-aware lookup helper in this phase
- `get?(key, target)` remains as a compatibility alias with the same runtime behavior
- `get?(key, none) -> none`
- `get?(key, none(reason)) -> none(reason)`
- `get?(key, none(reason, context)) -> none(reason, context)`
- `get?(key, some(map)) -> get?(key, map)`
- `get?(key, map) -> some(value)` when key exists (including `value = none("nil")`)
- `get?(key, map) -> none("missing-key", { key: key })` when key is missing
- unsupported target types raise clear `TypeError`
Maybe-flow helper semantics:

- they remain useful for:
  - explicit Option values outside pipeline position
  - higher-order composition
  - places where wrap-vs-flat-map behavior is the actual intent
  - pipeline stages that need the inner value of `some(...)`
- `map_some(f, some(x)) -> some(f(x))`
- `map_some(f, none(...)) -> none(...)` unchanged
- `map_some(f, some(x))` calls `f(x)` with the inner raw value only at that explicit helper boundary
- `flat_map_some(f, some(x)) -> f(x)` and requires `f(x)` to be an Option value
- `flat_map_some(f, none(...)) -> none(...)` unchanged
- `flat_map_some(f, some(x))` calls `f(x)` with the inner raw value only at that explicit helper boundary
- `then_get(key, target)` is a thin maybe-aware chaining helper:
  - `then_get(key, map) -> get(key, map)`
  - `then_get(key, some(map)) -> get(key, map)`
  - `then_get(key, none(...)) -> none(...)` unchanged
- `then_first(target)` is a thin maybe-aware chaining helper over raw list / `some(list)` / `none(...)`
- `then_nth(index, target)` is a thin maybe-aware chaining helper over raw list / `some(list)` / `none(...)`
- `then_find(needle, target)` is a thin maybe-aware chaining helper over raw string / `some(string)` / `none(...)`
- `or_else_with(opt, thunk)` is recovery/defaulting:
  - returns wrapped value for `some(value)`
  - calls `thunk()` only for `none...`
- `or_else(opt, fallback)` and `or_else_with(opt, thunk)` are direct recovery helpers over explicit Option values
- these helpers preserve structured absence reason/context during propagation unless they are explicitly recovery/defaulting helpers

Developer-facing rendering and introspection:

- REPL result display and debug-oriented formatting preserve structured absence syntax directly:
  - `none("nil")`
  - `none("empty-list")`
  - `none("index-out-of-bounds", {index: 8, length: 2})`
  - `none("missing-key", {key: "name"})`
  - `some(3)`
  - `some(none("nil"))`
- structured absence context is rendered structurally in debug/display output; it is no longer collapsed to `<map N>` in these tooling-facing paths
- `some?` / `none?` are the short predicate names; `is_some?` / `is_none?` remain supported aliases with the same runtime behavior
- `absence_reason(opt)` and `absence_context(opt)` are the canonical inspection helpers for structured absence metadata
- because plain `none` normalizes to `none("nil")`, `absence_reason(none)` returns `some("nil")`
- `absence_context(none)` returns `none("nil")`
- public evaluator result boundaries normalize raw host `None` to `none("nil")`, including empty top-level program results returned through `run_source(...)`
- both `none` and legacy `nil` render as `none("nil")`

Pipeline note:

- pipelines are now Option-aware directly
- canonical safe-chaining style is now:
  - `record |> get("user") |> get("address") |> get("zip")`
  - `data |> get("items") |> then_nth(0) |> then_get("name")`
  - `data |> get("users") |> then_first() |> then_get("email")`
- canonical recovery wraps the pipeline result:
  - `unwrap_or("unknown", record |> get("user") |> get("name"))`
  - `unwrap_or(0, fields(row) |> nth(5) |> parse_int)`
- pipelines now lift ordinary stages over `some(...)`; use `map_some` / `flat_map_some` when you need explicit wrap-vs-flat-map control
- reducers remain explicit:
  - `sum(xs)` expects a plain list of numbers
  - `sum` rejects raw Option items with a clear error instead of relying on accidental arithmetic with `some(...)` / `none(...)`
  - flow/value parse pipelines should therefore use `keep_some(...)`, `keep_some_else(...)`, or per-item `unwrap_or(...)` before `collect |> sum`
  - value-mode parse pipelines can now also use `map(parse_int) |> map((o) -> unwrap_or(0, o)) |> sum` because `map` uses `apply_raw` semantics to deliver `none(...)` elements to the callback
- explicit helpers such as `map_some`, `flat_map_some`, and `then_*` remain available for direct Option values and higher-order/non-pipeline composition

Structured absence currently used in canonical access/search helpers:

- `first([]) -> none("empty-list")`
- `last([]) -> none("empty-list")`
- `find(string, needle) -> none("not-found", { needle: needle })` when missing
- `find_opt(pred, xs) -> none("no-match")` when no element matches
- `nth(i, xs) -> none("index-out-of-bounds", { index: i, length: n })` when out of range
- `map_get(map, key) -> none("missing-key", {key: key})` when key is missing
- `cli_option(opts, name) -> none("missing-key", {key: name})` when the option is absent

Absence migration status:

| API | Status | Present result | Missing result | Notes |
| --- | --- | --- | --- | --- |
| `get` | canonical | `some(value)` | `none("missing-key", { key: key })` | preferred map lookup |
| `get?` | compatibility alias | `some(value)` | `none("missing-key", { key: key })` | retained naming exception |
| `first` | canonical | `some(value)` | `none("empty-list")` | list head access |
| `first_opt` | compatibility alias | `some(value)` | `none("empty-list")` | alias for `first` |
| `last` | canonical | `some(value)` | `none("empty-list")` | list tail access |
| `nth` | canonical | `some(value)` | `none("index-out-of-bounds", { ... })` | zero-based list indexing |
| `nth_opt` | compatibility alias | `some(value)` | `none("index-out-of-bounds", { ... })` | alias for `nth` |
| `find` | canonical string search | `some(index)` | `none("not-found", { needle: needle })` | string search only |
| `find_opt` | canonical predicate-search helper | `some(value)` | `none("no-match")` | list predicate search |
| `map_get` | compatibility surface | raw value | `none("missing-key", { key: key })` | use `get` in new code |
| callable map lookup `m(key)` | compatibility surface | raw value | `none("missing-key", { key: key })` | use `get` in new code |
| string projector lookup `"key"(m)` | compatibility surface | raw value | `none("missing-key", { key: key })` | use `get` in new code |
| map dot access `m.name` | canonical narrow named access | raw value | `none("missing-key", { key: key })` | narrow map/module access only; prefer `get("name", m)` for maybe-aware lookup |
| `cli_option` | canonical CLI lookup | raw value | `none("missing-key", { key: name })` | use `cli_option_or` for defaults |
Compatibility note:

- legacy `nil` surface syntax remains accepted, but it normalizes immediately to `none("nil")`
- existing callable-data map/string-projector behavior is unchanged:
  - `m(key)`, `m(key, default)`
  - `"key"(m)`, `"key"(m, default)`
- compatibility aliases retained in this phase:
  - `get?` for `get`
  - `first_opt` for `first`
  - `nth_opt` for `nth`
- docs and new examples should prefer canonical APIs:
  - `get`
  - `first`
  - `last`
  - `nth`
  - string `find`
  - `find_opt`
  - direct Option-aware pipelines such as `record |> get("user") |> get("name")`
  - explicit chaining helpers such as `then_first`, `then_nth`, and `flat_map_some(...)` when the next stage expects the inner value of `some(...)`
  - outer recovery with `unwrap_or(...)` / `or_else(...)`
- new naming rule in current docs/runtime surface:
  - new `?`-suffixed APIs are boolean-returning
  - maybe-returning APIs should use Option values without `?`
  - `get?` remains the existing compatibility exception; `get` is the canonical maybe-aware name in this phase

Pattern matching note:

- `none` matches as a literal pattern
- `none(reason)` matches structured absence by reason
- `none(reason, context)` matches structured absence by reason and context
- `some(pattern)` destructures option values in function clauses and case arms
- `some(...)` pattern form requires exactly one inner pattern
- in `none(reason)` and `none(reason, context)` patterns, the reason slot matches the quoted/literal reason value
### String helpers

- `byte_length`, `is_empty`, `concat`
- `contains`, `starts_with`, `ends_with`, `find`
- `split`, `split_whitespace`, `join`
- `trim`, `trim_start`, `trim_end`
- `lower`, `upper`, `parse_int`
- public string helpers are thin prelude wrappers in `src/genia/std/prelude/string.genia`
  - these wrappers are the canonical user-facing API surface and carry Markdown docstrings for `help(...)`
  - the underlying runtime behavior remains host-backed and unchanged in this phase

`parse_int` behavior:

- `parse_int(string)` returns `some(int)` or `none("parse-error", context)`
- `parse_int(string, base)` does the same with explicit base `2..36`
- surrounding whitespace is ignored
- leading `+` / `-` is supported
- invalid integer text returns structured absence
- non-string input raises clear `TypeError`
- invalid base type raises clear `TypeError`
- out-of-range base raises clear `ValueError`
- non-string input raises clear `TypeError`
- invalid base type raises clear `TypeError`
- out-of-range base raises clear `ValueError`
### Bytes / JSON / ZIP bridge builtins (Phase 1, host-backed)

- `utf8_decode(bytes) -> string`
- `utf8_encode(string) -> bytes`
- internal JSON/CSV bridge primitives: `_json_parse(string) -> value|none`, `_json_stringify(value) -> string|none`, `_parse_jsonl_record(line) -> some(record, context)|none("blank_line", context)|err(reason, context)`, `_parse_csv_row(line) -> some(fields, context)|none("blank_line", context)|err(reason, context)`, `_parse_csv_row(headers, line) -> some(record, context)|none("blank_line", context)|err(reason, context)`
- public JSON helpers from `src/genia/std/prelude/json.genia`:
  - `json_decode(string_or_bytes) -> some(json_represented_value, context) | err(reason, context)` (**Experimental**, portable R9 boundary)
  - `json_encode(value) -> some(json_text, context) | err(reason, context)` (**Experimental**, portable R9 boundary)
  - `json_schema(json_represented_schema) -> some(template, context) | err(reason, context)` (**Experimental**, portable R9 structural-subset compiler)
  - `json_parse(string) -> value | none("json-parse-error", context)`
  - `json_stringify(value) -> string | none("json-stringify-error", context)`
  - `json_pretty(value) -> string | none(...)` (compatibility alias)
  - `parse_jsonl_record(line) -> some(parsed_record, context) | none("blank_line", context) | err(reason, context)` (**Experimental**)
  - `parse_csv_row(line) -> some(fields, context) | none("blank_line", context) | err(reason, context)` (**Experimental**)
  - `parse_csv_row(headers, line) -> some(record, context) | none("blank_line", context) | err(reason, context)` (**Experimental**)
- internal file/zip bridge primitives: `_read_file(path)`, `_write_file(path, text)`, `_zip_read(path)`, `_zip_write(path, items)`
- public file/zip helpers from `src/genia/std/prelude/file.genia`:
  - `read_file(path) -> string | none(...)`
  - `write_file(path, string) -> path | none(...)`
  - `zip_read(path) -> flow | none(...)`
  - `zip_write(path, flow_or_list) -> path | none(...)`
  - `zip_write(path)` stage form returns a pipeline stage `(items) -> zip_write(path, items)`
- `zip_entries(path) -> list of zip entries`
- `zip_write(entries, path) -> path` (also accepts `(path, entries)` for pipeline ergonomics)
- `entry_name(entry) -> string`
- `entry_bytes(entry) -> bytes`
- `set_entry_bytes(entry, new_bytes) -> entry`
- `update_entry_bytes(entry, f) -> entry`
- `entry_json(entry) -> bool`
Behavior:

- bytes are opaque runtime wrappers (`<bytes N>`)
- zip entries are opaque runtime wrappers (`<zip-entry ...>`) containing entry name + bytes payload
- `zip_entries` currently returns a strict list (Phase 1) and preserves entry order
- JSON objects from `json_parse` are represented as persistent runtime map values (`map_*` bridge type)
- `json_stringify`/`json_pretty` emit deterministic pretty JSON with 2-space indentation and sorted object keys
- JSON parse/stringify failures return structured `none(...)` metadata rather than raising parse/stringify exceptions
- `json_decode` and `json_encode` are the Experimental portable R9 JSON representation boundary; legacy `json_parse`, `json_stringify`, `json_pretty`, and `parse_jsonl_record` retain their compatibility behavior
- successful `json_decode` returns `some(represent("json", root), context)`, where `root` is an ordinary map/list/string/number/boolean/`nil` value and nested values have no implicit representation facets; string input and strict UTF-8 bytes input are accepted, while any other input type is runtime misuse
- successful `json_encode` returns deterministic two-space-indented JSON with sorted object member names and preserved list order; it accepts one outer `json`-represented supported value or a supported ordinary value, consuming only that optional outer layer
- portable JSON-domain limits are: string object names, no duplicate object names, safe integers in `[-9007199254740991, 9007199254740991]` (Integer), fraction/exponent numbers accepted as exact Decimal only when `stable_json_decimal` holds (R23 E23-3 -- section 9.34; parsed/emitted lexically, never through a host float), a Rational encodable only when its exact value has a finite base-10 Decimal equivalent that itself satisfies `stable_json_decimal` (never rounded, never decoded back to Rational -- R23 E23-4 -- section 9.35), a finite Float64 encodable using its canonical shortest-roundtrip decimal spelling as a bare JSON number (NaN/infinity rejected; decode never produces Float64 -- same section), Unicode scalar strings/names, and at most 128 nested object/array containers
- `json_decode` rejects malformed/trailing JSON, invalid UTF-8, duplicate names, nonstandard/non-finite or out-of-range numbers, invalid Unicode scalars, and excessive nesting as `err(...)`; `json_encode` rejects unsupported values/keys/facets and the same number/Unicode/nesting violations as `err(...)`
- boundary Outcome contexts contain `kind: quote(json)`, `operation: quote(decode|encode)`, `status: quote(decoded|encoded|error)`, and `reason`; malformed syntax adds 1-based `line`/`column`, duplicates add `key`, and unsupported encoding adds `value_type`
- portable error reasons are `invalid_json`, `invalid_json_utf8`, `duplicate_json_key`, `json_number_out_of_range`, `invalid_json_unicode`, `json_nesting_too_deep`, and `unsupported_json_value`; host exception text is not portable
- JSON decoding/serialization may be host-backed, but value mapping, facet placement, limits, deterministic output, Outcomes, and matching observations are portable; no parser/Core IR node or parallel JSON runtime value model is added
- `json_schema` accepts exactly one outer `json`-represented schema map and compiles it into an ordinary one-argument Outcome Template; unrepresented input, another outer facet, or a represented non-map root is runtime misuse
- every schema node requires one string `type`: `object`, `array`, `string`, `number`, `integer`, `boolean`, or `null`; the only other supported keywords are `properties`, `required`, `items`, and boolean `additionalProperties`
- object `properties` default to `{}`, `required` defaults to `[]`, and `additionalProperties` defaults to `true`; required names must be unique and declared in `properties`; optional declared properties are checked only when present
- array schemas require one schema-valued `items`; object-only keywords on other types, array-only keywords on other types, malformed supported-keyword values, unsupported type names, and every unlisted keyword fail compilation rather than being ignored
- successful compilation returns `some(template, {kind: quote(json_schema), operation: quote(compile), status: quote(compiled), reason: quote(compiled)})`; unsupported keywords return `err(quote(unsupported_json_schema_keyword), context)`, while malformed subset schemas return `err(quote(invalid_json_schema), context)` with deterministic `schema_path` and detail fields
- a compiled Template returns `some(original_subject)` on success; type, missing-required-property, and forbidden-additional-property mismatches return `none("json-schema-type-mismatch"|"json-schema-required-property"|"json-schema-additional-property", context)` at the first deterministic subject path
- object matching checks type, required names in `required` order, forbidden extras in candidate insertion order, then present properties in specification order; array matching checks items by increasing index; nested success payloads never transform the subject
- JSON Schema `number` accepts finite integers/floats except booleans, `integer` accepts integers except booleans, `string` excludes symbols, and `null` matches Genia `nil`; compilation/matching adds no syntax, Core IR node, schema-specific runtime hierarchy, coercion, defaults, references, recursion, acquisition, or standards-completeness claim
- (R15 E15-1) a compiled Template carries an inert `template_description(...)` description mirroring its compiled schema exactly; see the "Inert inspectable Template descriptions" subsection above
- the executable R9 composed proving case is `examples/r9_composed_json_template_pipeline.genia`: it decodes a JSON Schema-derived exact `Person` Template, decodes represented JSON records, consumes the outer `json` facet through an existing named Template, validates the carried ordinary value with `Person`, and aggregates valid records plus mismatch/boundary diagnostics with `validate_each` and `collect_validated`; this composition adds no behavior beyond the independently specified boundaries above
- `parse_jsonl_record(line)` (**Experimental**) parses one JSONL string line and returns an Outcome with stable context metadata:
  - every recoverable Outcome context includes the exact original input string as `line: <original_line>`
  - valid JSON object: `some(parsed_record, {kind: quote(jsonl_record), status: quote(parsed), reason: quote(parsed), line: <original_line>})`
  - blank or whitespace-only line: `none("blank_line", {kind: quote(jsonl_record), status: quote(skipped), reason: quote(blank_line), line: <original_line>})`
  - malformed JSON: `err(quote(invalid_jsonl_record), {kind: quote(jsonl_record), status: quote(error), reason: quote(invalid_jsonl_record), message: "...", line: <original_line>, column: <col>})` where `column` is the 1-based column position from the JSON parse error
  - valid JSON that is not an object: `err(quote(jsonl_record_not_object), {kind: quote(jsonl_record), status: quote(error), reason: quote(jsonl_record_not_object), value_type: <type_symbol>, line: <original_line>})` where `value_type` is a symbol describing the actual JSON value type (`list`, `string`, `number`, `bool`, `null`)
  - non-string input is a runtime/type misuse error, not a recoverable Outcome
  - `parse_jsonl_record` does not change `json_parse` behavior; it is an additive helper
  - shared semantic spec coverage is active for this helper (see `spec/eval/parse-jsonl-record-*.yaml` and `spec/error/parse-jsonl-record-non-string-error.yaml`)
- `parse_csv_row` (**Experimental**) parses one CSV row string and returns an Outcome with stable context metadata:
  - supported row subset: comma delimiter, double-quote quoting, quoted commas, doubled quotes inside quoted fields, empty fields, no automatic trimming
  - unsupported: multiline quoted fields, alternate delimiters, alternate quote characters, escape options, comments, dialect options, automatic type inference, file-level CSV reading, and Sheet conversion
  - every recoverable Outcome context includes the exact original input string as `line: <original_line>`
  - `parse_csv_row(line)` valid non-blank row: `some(fields, {kind: quote(csv_row), status: quote(parsed), reason: quote(parsed), line: <original_line>, field_count: <n>})` where `fields` is a list of strings
  - `parse_csv_row(headers, line)` valid non-blank row: `some(record, {kind: quote(csv_row), status: quote(parsed), reason: quote(parsed), line: <original_line>, field_count: <n>, header_count: <n>})` where `headers` is a list of unique non-empty strings and `record` maps each header to the parsed field string at the same position
  - blank or whitespace-only line: `none("blank_line", {kind: quote(csv_row), status: quote(skipped), reason: quote(blank_line), line: <original_line>})`
  - malformed row data: `err(quote(invalid_csv_row), {kind: quote(csv_row), status: quote(error), reason: quote(invalid_csv_row), message: "...", line: <original_line>})`
  - header/field count mismatch: `err(quote(csv_header_mismatch), {kind: quote(csv_row), status: quote(error), reason: quote(csv_header_mismatch), line: <original_line>, field_count: <field_count>, header_count: <header_count>})`
  - non-string line input, non-list headers input, non-string header items, empty header names, and duplicate header names are runtime/type misuse errors, not recoverable Outcomes
  - shared semantic spec coverage is active for this helper (see `spec/eval/parse-csv-row-*.yaml` and `spec/error/parse-csv-row-*.yaml`)
- `zip_read` is lazy and returns Flow items shaped as `[filename, bytes]`
- `zip_write` consumes a Flow (or list) of `[filename, bytes|string]` items
- file/zip parse/write/read failures return structured `none(...)` metadata for the new prelude API surface
- this is a minimal host-backed bridge and is **not** the full flow system
### Resource IO bridge (Phase 1, host-backed)

Maturity: **Experimental** — `fs` backend only; no object store, no streaming, no browser-native backend.

Module: `import resource` or `import resource as res` — accessed via dot syntax (`res.read_text(ref)`, etc.).

**`ResourceRef`** — plain Genia map `{uri: string, backend: string}`. Constructed by `resource_ref(path)`, which is a pure Genia function (no bridge call). The `uri` is stored verbatim with no normalization.

**`ResourceMeta`** — plain Genia map with keys `exists` (boolean, always present), `size` (integer, present only when file exists), `backend` (string, always present).

Public surface from `src/genia/std/prelude/resource.genia`:
- `resource_ref(path) -> {uri: path, backend: "fs"}` — pure Genia map constructor
- `discover(root_ref) -> Flow[ResourceRef] | none(...)` — lazy recursive file walk; yields one ResourceRef per file (no directories); existence check is eager (before Flow is returned)
- `read_text(ref) -> string | none(...)`
- `read_bytes(ref) -> bytes | none(...)`
- `write_text(ref, text) -> ref | none(...)` — returns the input ref on success
- `write_bytes(ref, bytes) -> ref | none(...)` — returns the input ref on success
- `delete(ref) -> none("nil") | none(...)` — always returns `none("nil")` on success (no meaningful return value)
- `copy(from_ref, to_ref) -> to_ref | none(...)` — returns the destination ref on success
- `resource_meta(ref) -> ResourceMeta | none(...)`
- `resource_capabilities() -> map` — pure constant; no IO; `supports_discover`, `supports_delete`, `supports_copy`, `supports_meta`, `supports_bytes` are all `true`

Locked `none(...)` reason strings — no other reason strings are used for resource operations:
- `"resource-not-found"` — file or directory does not exist
- `"resource-read-error"` — OSError during read
- `"resource-write-error"` — OSError during write
- `"resource-delete-error"` — OSError during delete (FileNotFoundError → `none("nil")`, not this)
- `"resource-copy-error"` — OSError during copy
- `"resource-meta-error"` — OSError during stat
- `"resource-unsupported"` — backend is not `"fs"`
- `"resource-malformed-ref"` — ref is not a valid ResourceRef (not a map, missing `uri`, missing `backend`)

Behavior notes:
- `delete` on a non-existent file returns `none("nil")` (idempotent — file is already gone)
- None propagation: if any argument to a resource function is `none(...)`, Genia's standard none-propagation short-circuits before the bridge runs
- `discover` on a non-existent root returns `none("resource-not-found")` eagerly (not a lazy error inside the Flow)
- Does not deprecate `read_file`/`write_file`: those remain Python-host-only bare-name helpers
### Simulation primitives (Phase 2)

- public prelude-backed randomness helpers:
  - `rng(seed)`
  - `rand()`
  - `rand(rng_state)`
  - `rand_int(n)`
  - `rand_int(rng_state, n)`
  - `rand_flow(seed)` (experimental)
  - `rand_int_flow(seed, n)` (experimental)
- `sleep(ms)`

Behavior:

- `rng(seed)` returns an opaque explicit RNG value; seed must be a non-negative integer
- `rand()` returns a float in `[0, 1)` using host RNG convenience randomness
- `rand(rng_state)` returns `[next_rng_state, float]` using a deterministic explicit RNG sequence
- `rand_int(n)` returns an integer in `[0, n)` using host RNG convenience randomness
- `rand_int(rng_state, n)` returns `[next_rng_state, int]` using the same deterministic explicit RNG sequence; the integer is always in `[0, n)`
- the explicit seeded RNG uses a simple 32-bit LCG so the same seed yields the same sequence on the current Python host
- `rand_int(...)` raises clear `TypeError` for non-integer `n` and `ValueError` for `n <= 0` in both convenience and seeded forms
- `sleep(ms)` blocks current execution for `ms` milliseconds; raises clear `TypeError` for non-numeric values and `ValueError` for negative values
- `rand_flow(seed)` returns a lazy, pull-based, single-use Flow emitting floats in `[0, 1)`; same seed yields the same sequence across runs on the Python reference host; seed must be a non-negative integer; raises `TypeError` for non-integer seed and `ValueError` for negative seed; the Flow is unbounded and must be bounded with `take` or similar before `collect` or `run`
- `rand_int_flow(seed, n)` returns a lazy, pull-based, single-use Flow emitting integers in `[0, n)`; same seed and `n` yield the same sequence across runs on the Python reference host; seed must be a non-negative integer and `n` a positive integer; invalid seed raises through `rng(seed)` at call time; invalid `n` raises through `rand_int(rng_state, n)` when the Flow is pulled; the Flow is unbounded and must be bounded before `collect` or `run`
- both `rand_flow` and `rand_int_flow` are pure Genia prelude wrappers composed from `evolve`, `drop`, `map`, and existing seeded RNG helpers; no new Python kernel primitives
- LANGUAGE CONTRACT: `rand_flow` and `rand_int_flow` expose a deterministic bounded lazy sequence contract; cross-host output reproducibility is not guaranteed in this phase
- PYTHON REFERENCE HOST: determinism is provided by the existing 32-bit LCG via `rng`/`rand`/`rand_int`; internal RNG state is not exposed as a Genia-visible value during Flow consumption
## 7) Autoloaded stdlib

Autoload is keyed by `(name, arity)` and currently registers functions from bundled stdlib sources:

- `src/genia/std/prelude/list.genia`
- `src/genia/std/prelude/fn.genia`
- `src/genia/std/prelude/flow.genia`
- `src/genia/std/prelude/map.genia`
- `src/genia/std/prelude/ref.genia`
- `src/genia/std/prelude/process.genia`
- `src/genia/std/prelude/io.genia`
- `src/genia/std/prelude/random.genia`
- `src/genia/std/prelude/option.genia`
- `src/genia/std/prelude/string.genia`
- `src/genia/std/prelude/json.genia`
- `src/genia/std/prelude/file.genia`
- `src/genia/std/prelude/math.genia`
- `src/genia/std/prelude/awk.genia`
- `src/genia/std/prelude/cell.genia`
- `src/genia/std/prelude/actor.genia`

Loading behavior:

- bundled stdlib `.genia` files are loaded via package resources
- this works in both local repo execution and installed-package/tool execution
- custom absolute filesystem autoload paths still work
- file-relative module imports still resolve from the requesting source file's directory first
- autoload can be triggered both by calls and by plain name lookup for function values
  - this means autoloaded functions can be passed to higher-order helpers such as `apply`, `compose`, `map_some`, and `flat_map_some`
  - `help("name")` also triggers autoload for registered public helpers and prints a short missing-name note when no public helper or runtime name exists
- autoload loading is a separate path from user module imports:
  - autoloads are keyed by `(name, arity)` and triggered lazily on first name lookup miss
  - loaded exports bind directly into the root environment; no module value is created
  - autoload deduplication uses a separate file-key set, independent of the module import cache (`loaded_modules`)
  - autoload cycle detection raises `RuntimeError("Autoload cycle detected while loading <key>")`
  - autoloads are not accessible through module named access (`mod.name`) and do not appear in the module cache

Notable autoloaded functions include:

- list: `list`, `first`, `rest`, `empty?`, `nil?`, `append`, `length`, `reverse`, `reduce`, `map`, `filter`, `count`, `any?`, `nth`, `take`, `drop`, `range`
  - `reduce`, `map`, and `filter` are pure prelude implementations using `apply_raw` for callback invocation; `none(...)` list elements are delivered to the callback without short-circuit; `reduce` additionally accepts Flow as Seq-compatible input and does not short-circuit on `none(...)` as initial accumulator; `count` (built on `reduce`) also accepts Flow
- canonical list/search helpers: `first`, `last`, `nth`, string `find`, `find_opt`
- compatibility aliases: `first_opt`, `nth_opt`
- fn: `apply`, `apply_raw`, `compose`
  - `apply_raw(f, args)` — language-contract host primitive; calls `f` with list `args` as positional arguments, bypassing the automatic `none(...)` short-circuit for arguments delivered to `f`; `apply_raw` itself is subject to normal none-propagation on its own two arguments (`apply_raw(f, none("x"))` short-circuits before `apply_raw` runs); `args` must be a list or `TypeError` is raised; return value of `f` is returned as-is with no coercion; exceptions inside `f` propagate unchanged; registered directly in the env (not autoloaded)
- cli: `cli_parse`, `cli_flag?`, `cli_option`, `cli_option_or`
- map: `map_new`, `map_get`, `map_put`, `map_has?`, `map_remove`, `map_count`, `map_items`, `map_item_key`, `map_item_value`, `map_keys`, `map_values`, `pairs`
- validation: `validate_required`, `validate_field`, `validate_optional`, `validate_record`, `validate_each`, `diagnostic_error`, `diagnostic_skipped`, `diagnostic_reason`, `diagnostic_field` (Experimental); `collect_validated` (host-backed builtin, Experimental)
- ref: `ref`, `ref_get`, `ref_set`, `ref_is_set`, `ref_update`
- process: `spawn`, `send`, `process_alive?`
- io: `write`, `writeln`, `flush`, `clear_screen`, `move_cursor`, `render_grid`
- randomness: `rng`, `rand`, `rand_int`, `rand_flow`, `rand_int_flow`
- flow: `lines`, `tee`, `merge`, `zip`, `scan`, `rules`, `refine`, `each`, `collect`, `run`, `rule_*`, `step_*`
- option: `some`, `none?`, `some?`, `get`, `get?`, `map_some`, `flat_map_some`, `then_get`, `then_first`, `then_nth`, `then_find`, `or_else`, `or_else_with`, `unwrap_or`, `absence_reason`, `absence_context`, `is_some?`, `is_none?`
- string: `byte_length`, `is_empty`, `concat`, `contains`, `starts_with`, `ends_with`, `find`, `split`, `split_whitespace`, `join`, `trim`, `trim_start`, `trim_end`, `lower`, `upper`, `parse_int`
- syntax: `self_evaluating?`, `symbol_expr?`, `tagged_list?`, `quoted_expr?`, `quasiquoted_expr?`, `assignment_expr?`, `lambda_expr?`, `application_expr?`, `block_expr?`, `match_expr?`, `text_of_quotation`, `assignment_name`, `assignment_value`, `lambda_params`, `lambda_body`, `operator`, `operands`, `block_expressions`, `match_branches`, `branch_pattern`, `branch_has_guard?`, `branch_guard`, `branch_body`
- metacircular evaluator: `empty_env`, `lookup`, `define`, `set`, `extend`, `eval`
- math: `inc`, `dec`, `mod`, `abs`, `min`, `max`, `sum`
- awk: `fields`, `awkify`, `awk_filter`, `awk_map`, `awk_count`
- cell: `cell`, `cell_with_state`, `cell_send`, `cell_get`, `cell_state`, `cell_failed?`, `cell_error`, `restart_cell`, `cell_status`, `cell_alive?`, `cell_stop`
- actor: `actor`, `actor_send`, `actor_call`, `actor_alive?`, `actor_stop`, `actor_restart`, `actor_state`, `actor_failed?`, `actor_error`, `actor_status`
- prelude public functions now carry Markdown docstrings intended for `help(...)` teaching output
## 8) Tail calls and optimization behavior
<!-- anchor: state:tail-calls -->

Callable dispatch semantics (arity resolution, none-propagation detection, closure capture, TCO trampoline, invocation dispatch via `invoke_callable`) live in `src/genia/callable.py`; expression evaluation and pipeline dispatch (eval_call, eval_pipeline_stage) live in `src/genia/evaluator.py`; builtin registration and Python host interop bridge live in `src/genia/builtins.py` and `src/genia/host_bridge.py` respectively; `src/genia/interpreter.py` is the CLI/REPL orchestration facade (REPL loop, CLI arg parsing, run_source orchestration, pipe-mode validation, debug-stdio adapter) and re-exports the following symbols for backward compatibility with code written before the #210 module-split series: `make_global_env` (builtins); `Evaluator`, `GeniaPromise`, `GeniaMetaEnv` (evaluator); `GeniaFunction`, `GeniaFunctionGroup`, `TailCall`, `eval_with_tco`, `DebugHooks` (callable); `GeniaFlow`, `GeniaOptionNone`, `GeniaOptionSome`, `OPTION_NONE`, `truthy` (values); `lex`, `SourceSpan` (lexer); `Parser` (parser); `lower_program` (lowering); `optimize_program` (optimizer); `Assign`, `Block`, `ExprStmt`, `Lambda`, `ListPattern`, `MapPattern`, `Node`, `NoneOption`, `RestPattern`, `SomePattern`, `TuplePattern`, `Var` (ast_nodes); `_load_source_from_path` (host_bridge). All other symbols are imported for internal orchestration use only and are not part of the compat surface.

Implemented tail-call/runtime behavior:

- proper tail-call optimization is implemented via trampoline evaluation
- function calls in tail position execute in constant stack space
- self tail recursion is implemented
- mutual tail recursion is implemented
- tail position currently includes:
  - the direct result of a function body
  - the selected branch result of a case expression
  - the final expression in a block
  - the final pipeline stage after `|>` lowering

Other implemented optimizations:

- specialized nth-style list traversal rewrite to `IrListTraversalLoop` for a narrow recognized recursion shape

Core IR shape currently includes:

- program items: expression statement, assignment, named function definition, import, annotation
- expressions: literal, explicit Option some/none, variable, call, pipeline, unary, binary, lambda, block, list, map, spread, case, quote, quasiquote, delay
- patterns: wildcard, variable, literal, tuple, list, map, final rest, option some/none, glob
- function docstrings are carried as metadata on named-function definitions (not runtime expressions)
- Python may add specialized optimized execution nodes after lowering for narrow cases such as `IrListTraversalLoop`
  - these optimized nodes are not the minimal Core IR portability contract
## 9) Debug/runtime tooling

- parser/IR nodes carry source spans (filename + line/column ranges)
- `run_debug_stdio(...)` exposes debugger protocol endpoints used by the VS Code extension
- `help(name)` displays named-function metadata when available:
  - function signature header (`name/shape`, shapes include `+` for varargs)
  - source location (`Defined at file:line`) when available
  - Markdown-aware docstring rendering (headings, bullet lists, inline code, fenced code blocks, paragraph spacing)
  - docstring normalization (trim outer blank lines, dedent indentation, optional triple-quote wrapper stripping, collapse excessive blank lines)
  - undocumented fallback message (`No documentation available.`)
- `help()` with no arguments prints a small overview centered on the public prelude-backed stdlib surface and calls out the intentionally small host bridge
  - the overview keeps only a small host-written scaffold; public family names are grouped from registered prelude autoloads
  - all autoloaded prelude families (including Actor) are discovered dynamically from the autoload registry
  - `@doc` metadata is the primary source of truth for help content; legacy inline docstrings serve as fallback only
- public Python-host callables have one canonical registry in
  `src/genia/host_builtin_docs.py`; environment construction attaches its `doc`,
  `category`, and `stability` metadata through the existing binding path
- `help("name")` and `doc("name")` expose that canonical metadata for registered
  public host callables; internal bridges carry `stability: "internal"` in the
  registry and are excluded from public coverage and generated reference output
- `tools/gen_function_docs.py` generates the deterministic union of documented
  prelude autoloads and registered public Python-host callables; generated pages
  are outputs rather than a second documentation source
- `help("missing")` prints a short missing-name note instead of raising an undefined-name traceback
### Native test layer boundaries (Python reference host, Experimental)

The current native test stack uses four layers:

- **Kernel** (`src/genia/test_kernel.py`): executes already-formed `TestUnit` values and normalizes their outcomes. The kernel distinguishes passing tests, assertion/native-test failures (`NativeTestFailure`), unexpected runtime errors, and malformed/discovery-invalid test units. The kernel does not discover tests, load files, format CLI output, or own process exit codes.
- **Runner** (`src/genia/native_test_runner.py`): provides file/suite-level test execution helpers by invoking the kernel and aggregating results. The runner does not define assertion semantics or change language runtime behavior.
- **CLI/test-mode layer** (`src/genia/test_cli.py`): selects the `--test` entry point and handles `genia test <file>` through `run_native_tests_from_file`, loads/evaluates the file in test mode, registers tests through the `test(name, body)` mechanism, appends `@test` annotated zero-argument functions discovered by `discover_test_units(env)` after evaluation, validates unique test names among duplicate-eligible units (units already carrying a discovery error are excluded from duplicate-name validation; duplicate names among valid units are discovery errors; the discovery reason begins with `duplicate native test name: <name>` followed by deterministic `occurrence N: <location>` lines for each conflicting definition, where location is derived from existing `TestUnit.location` metadata when available or `<unknown>` when not), formats output via `format_test_suite_report`, and returns process exit codes via `suite_exit_code`. The CLI layer does not own kernel outcome normalization or provide broad discovery or lifecycle support.
- **Assertion helpers** (`src/genia/builtins.py`): `assert_true` and `assert_eq` make passing assertions return `none` (the implemented success value) and make failing assertions raise `NativeTestFailure`, which the kernel reports as a `fail` result rather than an unexpected `error`.

Current native test behavior distinguishes:

- `pass`: the test unit body completes without raising;
- `fail`: the test unit body raises `NativeTestFailure` (phase `"evaluation"`);
- `error`: an unexpected exception occurs during execution (phase `"evaluation"`);
- discovery error: the test unit has an invalid name or non-callable body (phase `"discovery"`).

Current native test support is not a complete test framework; lifecycle hooks, `@setup`/`@teardown` annotations, setup/teardown, fixtures, parameterized tests, broad directory discovery, and multi-host conformance are out of scope in this phase.
### Native test / pytest / shared-spec placement boundary (Python reference host, Experimental)

Native test support remains Experimental and backed by the Python reference host in this phase. Native tests complement pytest and shared semantic specs. Native tests do not replace pytest or shared semantic specs.

Genia-native tests belong to Genia-facing behavior that can be expressed and verified in Genia source from the user's perspective. Appropriate native-test coverage includes Outcome helpers, validation helpers, Flow/Seq visible behavior, Sheet helpers, user-facing examples, and similar prelude/source-level behavior.

Python pytest remains the home for parser, lexer, AST, Core IR, host/runtime internals, host adapter behavior, CLI harness internals, spec runner internals, Python-specific exception/normalization behavior, and native-test stack internals such as the kernel, CLI/test-mode layer, discovery validation, duplicate-name machinery, and inert lifecycle descriptor validation.

Shared semantic specs remain authoritative for portable observable CLI/eval/flow/error/parse/IR behavior where covered. Covered portable observable behavior must stay in shared specs and must not be moved into native tests as a replacement.

Unsupported native-test features remain unsupported in this phase:

- setup/teardown execution and setup/teardown are not implemented
- fixtures are not implemented
- parameterized tests are not implemented
- snapshots are not implemented
- property tests are not implemented
- parallelism is not implemented
- filtering is not implemented
- broad discovery is not implemented
- multi-host execution is not implemented

## 9.1) Native test kernel core (Python reference host, Experimental)

Pre-condensation text of sections 9.1-9.6 is preserved verbatim, as non-authoritative provenance, in
`docs/state-record/native-test-and-lifecycle-shape-records.md`.

LANGUAGE CONTRACT:
- The kernel normalizes `TestUnit` execution into one of three stable result kinds, `pass`, `fail`, or `error`, aggregates suite results, and maps them to
  kernel exit codes. `TestResult` is distinct from Outcome (`some`/`none`/`err`); there is no automatic mapping.
- Exit code `0` means all executed tests passed or the suite was empty; `1` means at least one test failed or errored.
- Native test metadata keys and values must be strings; non-string metadata is a deterministic discovery error reported before the test body runs, using Genia
  runtime type names and the existing `TestUnit.location` when available.

PYTHON REFERENCE HOST:
- `src/genia/test_kernel.py` provides `NativeTestFailure`, `TestUnit` (frozen: required non-empty `name`, required callable `body`, optional `location` and string-only
  `metadata`), `run_test_unit`, `run_test_suite`, `aggregate_results`, and `suite_exit_code`. `run_test_unit` validates metadata first, maps `NativeTestFailure` to `fail`
  and any other exception to `error`; discovery errors read `invalid native test metadata key: expected string, received <type>` or `invalid native test metadata value for key '<key>': expected string, received <type>`.
- A normalized `TestResult` has the stable keys `kind`, `name`, `phase`, `reason`, `expected`, `actual`, `stdout`, `stderr`, `diagnostics` (`stdout`/`stderr` are always empty strings; capture is not
  implemented). A `TestSuiteResult` has `total`, `passed`, `failed`, `errored`, and `results` in input order.

Not implemented: a `skip` result kind, a `duration` field, shared spec-runner integration, a host adapter for Genia callables, a broad assertion framework, lifecycle hooks or `@setup`/`@teardown`, fixtures,
stdout/stderr capture, and multi-host test execution. `@test` discovery belongs to the CLI/test-mode layer, not the kernel.

## 9.1.1) Native test assertion helpers (Python reference host, Experimental)

PYTHON REFERENCE HOST: the minimal helper surface is two builtins, `assert_true(value)` and `assert_eq(actual, expected)`.
- `assert_true` passes when `value` is truthy under current runtime truthiness; `assert_eq` passes exactly when `actual == expected` under the one Genia equality relation (R18; Outcome values compare directly,
  including `none(...)`). Both return `none` and print nothing on success, and raise `NativeTestFailure` (with useful actual/expected diagnostics for `assert_eq`) on failure.
- In native test mode a failing helper is a test `FAIL`, not an `ERROR`; wrong arity remains an evaluation `ERROR`; later tests in the suite still run.
- Selected current behavior is covered by Genia-native fixtures under `tests/native/` (validated pipeline, Outcome rendering and absence inspection, validation helpers, Flow/Seq) and by the runnable example
  `examples/r3_validated_pipeline_native_tests.genia`; these add no semantics.

Not implemented: `assert_false`, `assert_ne`, `assert_raises`, custom assertion messages, snapshot or property testing, soft assertions, matcher DSLs, assertion lifecycle hooks, grouping or count tracking, and
cross-host assertion support beyond the bounded C++ host.

## 9.2) Native test CLI (Python reference host, Experimental)

`genia --test <file>` and `genia test <file>` (`src/genia/test_cli.py::run_native_tests_from_file`) validate and parse the file, discover test units, run them through the native test kernel, and report. Discovery
uses the test-mode-only `test(name, body)` helper and `@test "description"` annotated zero-argument functions discovered after evaluation (after legacy registrations). The annotation carries the human-readable
description, the function name is the identifier, `@test` only marks functions for discovery (it does not execute them), discovery happens only in native test mode, and annotated tests use the same kernel.
Duplicate names across explicit and annotated tests are discovery errors; malformed units are normalized discovery errors. `@test "description"` annotation-driven native test discovery is implemented; setup/teardown lifecycle hooks,
`@setup`/`@teardown`, filtering, parallel execution, JSON/JUnit/TAP output, and multi-host test execution are not.

- The report prints a summary line `total=<t> passed=<p> failed=<f> errored=<e>` before and after the per-result lines `PASS <name>`, `FAIL <name> phase=<phase> reason=<reason>` (with `expected=<expected>
  actual=<actual>` when present), and `ERROR <name-or-unnamed> phase=<phase> reason=<reason>`.
- Exit code `0` when no failures or errors occur, `1` for failures or normalized test errors, `2` for invalid CLI invocation. `--test` is mutually exclusive with `-c`/`--command`, `-p`/`--pipe`, and `--debug-stdio`
  (for example `--debug-stdio --test` exits `2`).

## 9.3) Lifecycle plan data-shape support (Python reference host, Experimental)

Python reference host only; inert data validation, no lifecycle execution.

LANGUAGE CONTRACT:
- A lifecycle plan is ordinary data: a map with a required `name` identifier and a required `phases` list of phase maps. A phase is a map with required `name` and `action` identifiers and optional `scope` (portable
  scope label), `always` (boolean, normalized to `false` when absent), `description` (string), and `metadata` (map). Phase order is list order; duplicate phase names in one plan are invalid.
- `action` is a portable identifier (a quoted symbol), not a callable or host hook, and does not execute by existing in a plan.
- Optional root policy maps `cleanup`, `failure_policy`, and `result_policy` are validated as portable data: defaults normalize contract-safely and unsupported, unsafe, or nonportable values are rejected (cleanup keeps
  eligibility for entered scopes and rejects unentered ones, keeps cleanup failures observable, and permits only supported ordering labels; failure policy preserves primary and cleanup failures and rejects overwrite or
  swallow; result policy fixes `failure_order`).
- Constructing, importing, or validating a plan never executes lifecycle behavior.

PYTHON REFERENCE HOST: `src/genia/lifecycle_plan.py` provides `validate_lifecycle_plan` (raises `ValueError` with a deterministic path-based diagnostic) and `normalize_lifecycle_plan`; identifier fields must be
`GeniaSymbol` values (`quote(...)`) and callable `action` values are rejected. It is internal utility code with no public prelude API.

No lifecycle runner behavior is implemented. Also not implemented: phase or cleanup execution, action resolution or registry, execution-mode dispatch, annotation-driven phase discovery, and module/server/actor/notebook/browser lifecycle support.

## 9.4) Lifecycle scope tree data-shape support (Python reference host, Experimental)

Python reference host only; inert data validation, no lifecycle execution.

LANGUAGE CONTRACT:
- A lifecycle scope tree is ordinary data: a map with a required `scopes` list of scope maps, each with a required `name` identifier, a required `parent` (`none` for the root, otherwise `some(identifier)`), and a
  required `children` list of identifiers. Optional `description` (string) and `metadata` (map) are preserved as inert data.
- The scope vocabulary is exactly `execution`, `suite`, `module`, `test`, with the canonical hierarchy `execution -> suite -> module -> test`: `execution` has parent `none` and children `[suite]`; `suite`
  `some(execution)` and `[module]`; `module` `some(suite)` and `[test]`; `test` `some(module)` and `[]`. Duplicate scope names and unsupported names (server, actor, plugin, request, browser, notebook) are rejected.
- Constructing, importing, or validating a scope tree never executes lifecycle behavior.

PYTHON REFERENCE HOST: `src/genia/lifecycle_scope.py` provides `validate_lifecycle_scope_tree` and `normalize_lifecycle_scope_tree` (input order preserved; identifier fields must be `GeniaSymbol`; callables in
`metadata` are never invoked); invalid input raises `ValueError` with a deterministic path-based diagnostic. Internal utility code, no public prelude API.

No lifecycle runner behavior is implemented. No setup/teardown behavior is implemented. Also not implemented: phase execution, annotation discovery or execution, cleanup execution, execution-mode dispatch, and non-test scopes (server, actor, plugin, browser, notebook,
HTTP, command, file, pipe, REPL, source, flow).

## 9.5) Lifecycle annotation binding helper (Python reference host, Experimental)

Python reference host only; discovery data only, no execution.

LANGUAGE CONTRACT:
- Annotations are candidate markers for lifecycle phases and never execute themselves. A binding selects candidates by annotation name, exact metadata filters, participant kind, and deterministic ordering;
  results are discovery data only (selecting a participant does not invoke it, activate a phase, or change evaluation).
- Ordering labels are `source_order` (the default when omitted), `reverse_source_order`, and `stable_name_order`; the value is normalized and preserved in the result and is inert (no dependency or priority
  ordering). A non-string or unsupported ordering fails with a deterministic diagnostic naming `binding.ordering` (and, for non-strings, the runtime type); validation never invokes participants or ordering values.
- A required binding with no matching participants reports a deterministic diagnostic; an optional one yields an empty list. Selecting the same declaration more than once is a deterministic diagnostic and the
  declaration is included at most once.

PYTHON REFERENCE HOST: `src/genia/lifecycle_binding.py` provides internal dataclasses and `discover_lifecycle_participants(...)` (name matching, metadata filtering, callable participant validation, ordering via a centralized
`_validate_ordering(...)`, duplicate and required-binding diagnostics). No public Genia API was added; native test discovery does not use it.

Not implemented: lifecycle runner, phase, setup, or teardown execution, `@setup`/`@teardown`, and any public binding API.

## 9.6) Native test lifecycle contract consumer (Python reference host, Experimental)

Python reference host only; internal and inert. The native test path is the first consumer of the inert lifecycle contract: it is described and validated as inert lifecycle plan and scope data, and observable native-test behavior
(CLI output and exit codes) is unchanged.

LANGUAGE CONTRACT:
- The native test path is described as the inert lifecycle plan with phase shape `discover -> run -> report` and the inert scope tree `execution -> suite -> module -> test`. The descriptor is internal data: constructing or
  validating it executes nothing and changes no native-test behavior; validation is silent during native test execution unless the static descriptor is malformed.

PYTHON REFERENCE HOST: `src/genia/native_test_lifecycle.py` provides `native_test_lifecycle_plan()`, `native_test_lifecycle_scope_tree()`, and `validate_native_test_lifecycle()`, reusing the existing plan and scope
validators of sections 9.3 and 9.4 (dependency direction `native_test_lifecycle.py -> lifecycle_plan.py / lifecycle_scope.py`); `validate_native_test_lifecycle()` is called silently from `src/genia/test_cli.py`.

Not implemented: lifecycle runner, phase, setup, or teardown execution, `@setup`/`@teardown`, generalized annotation execution, an action registry, a public lifecycle prelude API, execution-mode dispatch, routing
`@test` discovery through lifecycle binding, and multi-host lifecycle. The separate focused R8 server lifecycle core is described in section 9.7; the executable R14 lifecycle runtime is section 9.8.

## 9.7) R8 server execution contract

Status: Implemented. The independently callable lifecycle core, inert route/server/CORS annotation bindings (issues #535-#537), and explicit CLI/live HTTP integration are implemented as Experimental Python-reference-host-only behavior. The descriptor and lifecycle-result shapes are host-independent; execution remains Python-reference-host-only in R8. Defined in issue #558.

LANGUAGE CONTRACT (PARTIALLY IMPLEMENTED):

- `genia serve <file>` is the only server-lifecycle activation boundary. Loading, importing, parsing, evaluating, or discovering a file in any other execution mode must not bind a listener, run a route handler, apply CORS, or enter server cleanup.
- Serve mode loads and evaluates exactly one entry file without ordinary `main/0` or `main/1` dispatch. An evaluation failure is a startup failure and prevents listener activation.
- R8 uses the existing prefix-annotation grammar, AST, and Core IR. Each server annotation takes one ordinary map expression on the annotation line; no call-like annotation syntax is added.
- Server annotations store inert descriptor maps under metadata keys `server`, `route`, and `cors`. `@server`, `@route`, and `@cors` metadata attachment are implemented. Descriptor value expressions are evaluated after their target binding exists, using the existing top-to-bottom annotation evaluation rule. An invalid implemented descriptor fails metadata attachment deterministically in every execution mode; a valid descriptor has no behavioral effect outside serve mode.
- `@server config` is valid only on a top-level simple-name assignment. Exactly one `@server` descriptor is required in the serve entry file. Its closed map accepts only optional `host`, `port`, and `max_requests` fields and uses the exact validation/default behavior of `serve_http`: `host` defaults to `"127.0.0.1"`, `port` defaults to `8000`, and `max_requests` remains optional. The annotated assignment is the server descriptor owner; its ordinary bound value is not server configuration and is not otherwise consumed by the lifecycle.
- `@cors policy` is valid only on the same assignment that owns `@server`. At most one `@cors` descriptor is allowed. Its closed map accepts only optional `origin`, `methods`, and `headers` fields and uses the exact validation, defaults, and response behavior of `cors(policy, handler)`.
- `@route descriptor` is valid only on a top-level named function. Its closed map has exactly `method` and `path` string fields. Both strings must be non-empty and `path` must start with `/`. The annotated binding must expose exactly one fixed one-argument callable arm; zero-argument, multi-argument, varargs, non-callable, or ambiguous bindings are invalid route handlers.
- Annotation names may occur at most once on one declaration. Repeating `@server`, `@cors`, or `@route` on the same target is an error rather than last-wins metadata. Annotated rebinding that would replace one of these descriptor keys is also an error. These rules do not change the existing merge behavior of other annotations.
- Serve discovery considers only declarations owned by the evaluated entry file. Imported modules may contain valid inert server annotation metadata, but their descriptors are not activated or merged into the entry file's server lifecycle.
- Discovery occurs after successful entry-file evaluation. Candidates are examined in source order, with declaration name as the deterministic tie-breaker. The one server descriptor is selected first, optional CORS second, and routes last. Route order passed to `route_request` is source order.
- Two routes conflict only when their normalized discovery keys are the exact pair `(method, path)`; R8 performs no method/path normalization. Every member of a conflicting pair is rejected, and diagnostics list occurrences in source order. Different methods on the same path are allowed.
- Descriptor failures are reported in this deterministic order: entry-file evaluation; `@server` cardinality/target/payload; `@cors` cardinality/target/payload; then each `@route` target/payload/arity in source order; then route conflicts in route source order. All descriptor diagnostics available from one completed discovery pass are returned together; listener activation does not occur when any diagnostic exists.
- The dedicated server lifecycle has three ordered phases and two scopes: `startup` in server scope, repeated `request` in request scope, and `shutdown` in server scope. It is one focused lifecycle consumer, not a generalized lifecycle runner or action registry.
- Startup validates/discovers descriptors, constructs exact route values from discovered handlers, passes them to `route_request`, optionally wraps the result once with `cors`, then activates the existing `serve_http` boundary with the server config. No parallel routing, CORS, header, or transport mechanism is permitted.
- Each accepted request enters one request scope. The handler produced by `route_request` receives the unchanged request map, selects one exact route, invokes that handler exactly once, and returns its response. When configured, the single application-wide `cors` wrapper owns preflight and response decoration. A request failure does not retry a handler.
- Server scope becomes entered before listener activation is attempted. Listener ownership begins only after activation returns an owned listener/server handle. Request scope becomes entered immediately before request routing and ends after a response or request failure. Shutdown is attempted exactly once for an owned listener after normal completion or any later primary failure; no cleanup is attempted for a listener that was never owned.
- Lifecycle state transitions are deterministic: `created -> starting -> serving -> stopping -> stopped` on success. A failure transitions from the current state to `stopping` when owned cleanup remains, then to `failed`; without owned cleanup it transitions directly to `failed`. Requests are accepted only in `serving`.
- The independently testable lifecycle core accepts validated/discovered descriptor data plus injected activate, request, and close operations. It does not parse CLI arguments or require a live socket. Final CLI integration may call this core; the core must not call CLI dispatch.
- The lifecycle core returns one deterministic result map with keys `status`, `state`, `phase`, `scope`, `server`, `primary_failure`, and `cleanup_failures`. `status` is `"ok"` or `"error"`; `state` is `"stopped"` or `"failed"`; `phase` is the terminal phase (`"shutdown"` on success or the phase owning the primary failure); `scope` is `"server"` or `"request"`; `server` is the existing `serve_http` result on success and `none` on error; `primary_failure` is `none` on success and otherwise the first failure; `cleanup_failures` is a source-ordered list and is empty on success.
- The first non-cleanup failure is always the primary failure. Cleanup never replaces or hides it. If no earlier failure exists, the first shutdown/close failure is primary and later cleanup failures remain in `cleanup_failures`. Startup failure skips request processing; request failure skips later requests; shutdown still gets its contracted opportunity for owned resources.
- Diagnostics and result failures must identify execution mode `serve`, phase, scope, reason, and source location when available. User-facing rendering may add context, but it must preserve the deterministic primary/cleanup distinction.

PYTHON REFERENCE HOST (IMPLEMENTED LIFECYCLE CORE):

- `src/genia/server_lifecycle.py` is the dedicated, independently callable lifecycle core: `server_lifecycle_plan()` returns inert plan data for `startup -> request -> shutdown` over `server`/`request` scopes,
  `validate_server_lifecycle()` validates it through the lifecycle-plan normalizer without executing work, and `run_server_lifecycle(application, requests, activate=..., request=..., close=...)` is the only activation seam
  (validated descriptor data, a finite ordered request source, injected operations; no CLI parsing or live socket needed). Successful activation establishes ownership; requests run in order without retry; a request
  failure skips later requests; an owned listener gets exactly one close; an activation failure creates no ownership and no close. Injected-operation exceptions normalize to failure maps with `mode`, `phase`, `scope`,
  `reason`, and `source_location` when available. It is one fixed consumer, not a lifecycle-plan runner (action identifiers stay inert; no registry or resolver).

PYTHON REFERENCE HOST (IMPLEMENTED ROUTE ANNOTATION BINDING):

- The evaluator accepts `@route {method: ..., path: ...}` only on a top-level named function, validates the closed descriptor, and stores it as inert `route` metadata; parser, AST, and Core IR are unchanged. Repeated `@route`
  and annotated replacement of existing canonical `route` metadata fail deterministically; an initial `@meta` entry named `route` stays ordinary metadata.
- `src/genia/server_route_binding.py` discovers annotated `IrFuncDef` declarations of the evaluated entry file (source order, name as tie-breaker), requires exactly one fixed one-argument arm, aggregates descriptor diagnostics
  before exact `(method, path)` conflict diagnostics (rejecting every conflicting member), and, when diagnostic-free, assembles generic R7 route values in source order and passes them once to `route_request` without starting a
  listener or running a handler. No public route-discovery prelude API.

PYTHON REFERENCE HOST (IMPLEMENTED SERVER-CONFIG ANNOTATION BINDING):

- `@server {host: ..., port: ..., max_requests: ...}` is accepted only on a top-level assignment and stored as inert `server` metadata after normalization: `host` defaults to `"127.0.0.1"`, `port` to `8000` (an integer in `[0, 65535]`),
  optional `max_requests` is a positive integer (explicit runtime absence is treated as omitted); input maps are not mutated. Repeated `@server` and annotated replacement of `server` metadata fail deterministically; `@meta`-named
  `server` stays ordinary.
- `src/genia/server_config_binding.py` discovers annotated `IrAssign` declarations of the entry file, requires exactly one valid descriptor, ignores imported declarations, and returns descriptor/cardinality diagnostics without
  starting a listener; a diagnostic-free result passes the normalized configuration and the unchanged handler once to an injected `serve_http(config, handler)`-shaped operation. No public server-config binding API.

PYTHON REFERENCE HOST (IMPLEMENTED CORS ANNOTATION BINDING):

- `@cors {origin: ..., methods: ..., headers: ...}` is accepted only on a top-level assignment, validated by the same policy validator as R7 `cors` (`src/genia/cors_policy.py`, preserving order, defaults, and messages), and
  stored as inert `cors` metadata; repeated `@cors` and annotated replacement fail deterministically; `@meta`-named `cors` stays ordinary.
- `src/genia/server_cors_binding.py` discovers annotated `IrAssign` declarations (source order), accepts absence, requires any descriptor to share the selected `@server` owner, ignores imported declarations, and returns
  payload/cardinality/ownership diagnostics. With no descriptor the assembled handler is returned unchanged; one descriptor passes its policy and the unchanged handler once to a `cors(policy, handler)`-shaped operation. R7
  `cors` and `with_headers` remain the sole owners of preflight and response-header behavior. No public CORS-discovery API.

PYTHON REFERENCE HOST (IMPLEMENTED CLI INTEGRATION):

- Python remains the only R8 server execution host because `serve_http`, `route_request`, `cors`, and `with_headers` are Python-reference-host capabilities.
- `genia serve <file>` accepts exactly one existing entry-file path, evaluates it once without `main` dispatch, discovers entry-file descriptors, and prevents activation when diagnostics exist. A valid application assembles
  source-ordered routes through `route_request`, applies optional application CORS once through `cors`, and activates `serve_http` through the lifecycle coordinator. Finite `max_requests` completion exits `0` without printing the
  lifecycle result; a startup or lifecycle failure prints a `serve <phase>/<scope>` diagnostic and exits `1`; missing files, extra operands, and conflicting serve command shapes exit `2` before evaluation or activation.
- Future hosts may consume the host-independent descriptor and lifecycle-result shapes, but R8 adds no shared host-adapter capability and no multi-host server guarantee.

Explicit limitations:

- `@route`, `@server`, and `@cors` metadata remain inert outside explicit `genia serve <file>` activation.
- No generalized lifecycle runner, middleware system, plugin system, dependency injection, path parameters, concurrent serving, streaming, WebSockets, authentication, authorization, credential policy, per-route CORS, graceful signal protocol, parser/Core IR change, or second web mechanism is defined.

## 9.8) R14 lifecycle and outbound HTTP (digest; Experimental, Python reference host only)

Current-state digest of former sections 9.8-9.20 (ticket-by-ticket text is preserved verbatim, as non-authoritative
provenance, in `docs/state-record/r14-lifecycle-http-records.md`). Approved contract:
`docs/design/r14-composable-lifecycle-contract.md`; release page: `docs/releases/R14.md`. R14 is complete. All behavior
below is ordinary functions over ordinary values: no new syntax, parser, AST, or Core IR node, and no ambient or global
"current lifecycle". Shared/multi-host conformance for this surface is Partial; no C++ implementation exists.

LANGUAGE CONTRACT (Experimental; portable behavior, implemented on the Python reference host only):

- **Lifecycle scopes.** `lifecycle_scope(peers, work)`, `lifecycle_child(scope_handle, peers, work)`, and
  `lifecycle_context(scope_handle, name)` run entry/work/unwind.
  - A peer is a closed map `{name: symbol, enter: callable/1, exit: callable/2}`. Any other shape, a non-symbol or empty
    `name`, or a duplicate name in one peer list is construction-time misuse (`TypeError`) raised before any `enter`.
  - `enter(scope_handle)` returns `some(context_value)` or `err(reason, context)`; any other return is misuse. A
    successful `enter` exposes its context under the peer's name to later peers and to `work`, never to earlier peers.
  - Peers enter in list order and unwind in strict reverse order, and only already-entered peers unwind.
    `exit(scope_handle, primary_summary)` receives only `{status: quote(ok)|quote(error), phase, peer}` and returns
    `some("nil")` or `err(...)`.
  - `work(scope_handle)` runs only if every peer entered. Its return value is carried verbatim in `result` and is never
    inspected for `some`/`none`/`err`; `work` fails a scope only by raising.
  - Every scope returns exactly one closed `LifecycleResult` (`status`, `state`, `scope`, `phase`, `peer`, `result`,
    `primary_failure`, `cleanup_failures`). Exactly one failure is primary: the first entry, work, or exit failure; later
    exit failures are appended to `cleanup_failures` in exit-call order, and every entered peer's `exit` still runs.
    `result` is `none("lifecycle-no-result")` only when `work` never ran or raised.
  - A scope handle is valid only while its scope is entering/active/exiting; later use raises
    `RuntimeError("lifecycle-scope-expired")`. `lifecycle_child` requires an `active` parent and runs as a plain nested
    call from the parent's `work`.
  - `lifecycle_context` is inward-only and read-only: own scope first, then each ancestor to the root, returning
    `some(value)` or `none("lifecycle-context-absent")`. A peer name that collides with a name exposed by an ancestor is
    construction-time misuse. Attachment order is independent of parent/child ownership.
- **Repeated element scopes.** `lifecycle_repeat(peers, source, element_work)` takes a list (eager, never short-circuits)
  or a Flow (lazy, single-use, no over-pull, one source item per pulled result) and returns a list of `LifecycleResult` or
  a Flow of them; any other source raises the Seq-compatibility `TypeError`. Each element gets a fresh scope
  (`scope: quote(element)`, no parent) whose reserved context `quote(element)` and `quote(index)` (1-based pull order) is
  readable through `lifecycle_context` before any peer's `enter`. Peers named `element` or `index` are misuse. Early Flow
  termination never leaves an element scope partially entered; cleanup is the existing Flow finalization rule. There is no
  AWK syntax and no cross-element leakage; `none(...)`/`err(...)` from `element_work` is ordinary `result` data.
- **Configuration binding.** `lifecycle_config(provider)` accepts an already-constructed R10/R13 provider (the unwrapped
  result of `config_provider`/`config_standard`; a plain map, `some(provider)`, `none`, or `err` raises `TypeError`) and
  returns one peer named `quote(config)`. `enter` captures the exact provider reference (no lookup, acquisition, or refresh)
  and `exit` returns `some("nil")`. At most one `quote(config)` peer may exist along one root/child/element chain; element
  scopes do not inherit an outer binding automatically. A missing binding yields the generic
  `none("lifecycle-context-absent")`.
- **HTTP operation.** `http_operation(method, base_url, path, headers, query, body)` returns `some(HttpOperation)` or
  `err("http-operation-invalid", {stage})` for the first invalid field in declared order, with zero network IO.
  - `method` is `quote(get|post|put|patch|delete)`; `base_url` is exactly `scheme://host[:port]` with `http`/`https`;
    `path` starts with `/` and contains no `?` or `#`, passed through unmodified.
  - Header keys lowercase; a lowercase-name collision is misuse. A header value is a plain string or one R10 protected
    value. `query` takes plain string keys and values only (a protected value is rejected; keys keep their case).
  - `body` is `none(...)` (normalized to `none("http-no-body")`), `{kind: quote(text), text}`, or `{kind: quote(json),
    value}`; a JSON body that `json_encode` rejects (including a protected leaf) is `err(..., {stage: quote(body)})`.
    An implicit `content-type` is added only for a valid body when the caller set none; an explicit one always wins.
  - An `HttpOperation` is an ordinary closed map `{method, base_url, path, headers, query, body}` with no response field.
- **Outbound call.** `web.http_send(operation, authority, timeout_ms)` returns `some({status, headers, body})` or
  `err(reason, context)`.
  - `authority` is `none(...)` when no header is protected, otherwise `some(<opaque R10 declassification authority>)`;
    `timeout_ms` is an integer in 1..300000. Malformed arguments, or a protected header with a missing or mismatched
    authority, raise before any transport attempt.
  - Exactly one synchronous attempt: no retry, redirect, pooling, or streaming. Any received status (100..599) is an ordinary
    `some(...)`; response header keys are lowercase and `body` is opaque bytes, never auto-decoded.
  - Failures are exactly `err("http-timeout", {timeout_ms})` and `err("http-transport-failure", {kind})` with `kind` in
    `connect|tls|dns|other`. `http-response-invalid` is reserved vocabulary that is never constructed.
  - The query string is sorted by key, percent-encodes every byte outside `ALPHA/DIGIT/-._~` (space is `%20`), joined with `&`
    and prefixed with `?` only when non-empty. Text bodies are UTF-8; JSON bodies use `json_encode`.
  - Each call runs one complete internal entry/work/unwind cycle with no caller-visible parent; the declassified header value
    is revealed only immediately before the transport attempt, through `declassify` with purpose `quote(http_send)`.
- **Protected credentials.** A protected header stays opaque through construction, storage in an `HttpOperation`, `display`,
  `debug_repr`, and `json_encode` (which fails closed with `err("protected-value", {operation: "json-encode"})`); generic
  representation operations reject it. Responses are always ordinary values. A declassification authority is host-injected and
  cannot be constructed from Genia source.
- **Declarative annotations.** `@get {path: string}` and `@post {path: string}` are inert descriptors valid only on a
  top-level named function with a fixed zero-argument arm; `path` is a non-empty string starting with `/`. They share one
  cardinality slot per declaration, and rebinding that would replace existing metadata is a deterministic diagnostic. Calling,
  loading, or importing an annotated function never performs IO. `web.send_annotated(fn, base_url, authority, timeout_ms)`
  calls `fn` with no arguments for its `{headers, query, body}` map, builds the operation with `http_operation`, and calls
  `web.http_send`; construction failures propagate as `err("http-operation-invalid", {stage})`. Only `get` and `post` exist.
- **Composition.** An R8 route handler may call `web.http_send`/`web.send_annotated` any number of times; each call is
  independent of the request scope, a failed outbound call is ordinary `err(...)` data, and the server keeps serving. The R8
  server lifecycle and the R14 lifecycle runtime remain separate. A repeated-record pipeline composes
  `lifecycle_scope` + `lifecycle_repeat` + `lifecycle_context` with ordinary `filter`/`map`; the shipped proving examples
  are `examples/r14_repeated_record_lifecycle_proving_case.genia` and the YouVersion Bible proxy case.

PYTHON REFERENCE HOST:

- Implemented in `src/genia/lifecycle_runtime.py`, `http_operation.py`, `http_transport.py`, `http_client.py`, and
  `http_annotation_binding.py`; `web.http_send` and `web.send_annotated` are prelude wrappers over private builtins. The
  transport capability is private (no builtin or import entry) and classifies every failure to a closed `kind` without
  retaining raw exception text.
- Import, native-test discovery, and serve-mode annotation registration never perform lifecycle or network activation.

Explicit limitations: no retries, circuit breakers, redirects, pooling, streaming client, cookies/OAuth, dependency
injection, scheduler, concurrent peer or element execution, HTTP methods beyond the five above, annotation verbs beyond
`get`/`post`, AWK syntax, or C++ implementation.

## 9.21) R21/R22 exact numeric model (digest; Experimental)

Current-state digest of former sections 9.21-9.31 (ticket-by-ticket text is preserved verbatim, as non-authoritative
provenance, in `docs/state-record/numeric-r21-r23-records.md`). Contracts: `docs/design/r21-numeric-source-portable-representation-contract.md`
and `docs/design/r22-exact-numeric-runtime-contract.md`; release pages `docs/releases/R21.md` and `R22.md`. Python reference
host only; no C++ implementation. Rendering and JSON of these values are in section 9.32.

LANGUAGE CONTRACT:

- **Numeric source classification (R21).** Source literals classify lexically with no host binary float: `DIGIT+` is Integer;
  `DIGIT+ "." DIGIT+`, `DIGIT+` with an exponent (`e`/`E`, optional sign, `DIGIT+`), and the dotted-exponent form are Decimal.
  `.5` and `5.` are rejected; a malformed exponent (`1e`, `1e+`) is a deterministic `SyntaxError`. A Decimal literal is
  canonicalized as `(coefficient, exponent)` with value = coefficient x 10^exponent (zero is `(0, 0)`, trailing base-10 zeros
  stripped). The `Number` AST node carries `source_kind`, `digits` or `coefficient`/`exponent`.
- **Portable literal payload (R21).** Expression-position numeric source lowers through the existing `IrLiteral` with a tagged
  payload: `{"kind": "integer", "digits": "<canonical text>"}` or `{"kind": "decimal", "coefficient": "<text>", "exponent":
  "<text>"}` (all strings; equivalent spellings such as `1.0`, `1.00`, `100e-2` give the identical payload). Source sign stays
  outside the payload (`-1.25` is `IrUnary(MINUS, ...)`); `/` stays ordinary `IrBinary(op=SLASH)`; `IrPatLiteral` is unchanged;
  no new Core IR node.
- **Value kinds (R22).** Integer is a Python `int` (unbounded, R17). **Decimal** (`GeniaDecimal`) is an exact
  coefficient x 10^exponent over arbitrary-precision integers, canonicalized as above with no negative-zero identity; Decimal kind
  is retained even for an integral value (`1.0` stays Decimal). **Rational** (`GeniaRational`) is an exact reduced ratio of
  Integers; `rational(n, d)` requires Integer arguments and a nonzero denominator (otherwise deterministic misuse), reduces by
  gcd, carries sign on the numerator, and collapses a denominator of 1 to Integer (`rational(2, 2)` is Integer `1`). There is no
  Rational literal syntax. **Float64** is the host IEEE-754 binary64 value; there is no public NaN/infinity/raw-bit constructor.
- **Exact family arithmetic.** `+`, `-`, `*`, unary `-` use the promotion lattice Integer < Decimal < Rational, computed exactly
  (never via host float). A Decimal operand keeps Decimal kind; any Rational operand gives Rational (collapsing to Integer when
  the denominator is 1). `/`: Integer/Integer is Integer when evenly divisible, otherwise **Rational** (never Decimal: `1 / 2` is
  `1/2`); with a Decimal operand and no Rational it is Decimal when the reduced quotient terminates in base 10, otherwise
  Rational; any Rational operand gives Rational. `%` is floor remainder (`left - floor(left/right) * right`) with the `+ - *`
  result-kind rule. Division or remainder by exact zero raises `ZeroDivisionError` with the host-independent text
  `"exact division by zero"` / `"exact remainder by zero"`.
- **Float64 and conversions.** `float64(value)` accepts Integer/Decimal/Rational (correctly rounded, ties-to-even) or Float64
  (unchanged); exact magnitude beyond the largest finite binary64 raises `OverflowError`; exact zero gives positive zero.
  `exact(value)` leaves exact kinds unchanged and converts a finite Float64 to the Decimal of its exact binary value
  (`exact(float64(0.1))` is `0.1000000000000000055511151231257827021181583404541015625`); `+0.0`/`-0.0` give Decimal zero; NaN and
  infinities fail with `ValueError`. Float64-with-Float64 arithmetic is native binary64; division or remainder by Float64 zero
  raises `ZeroDivisionError` (`"float64 division by zero"` / `"float64 remainder by zero"`).
- **Mixed-domain rejection.** Arithmetic mixing an exact kind (including plain Integer) with Float64 is rejected in both operand
  orders for all five binary operators, returning the existing `none("type-error", ...)`; the caller picks a domain with
  `float64(...)` or `exact(...)` first. Comparison is unaffected.
- **Comparison, equality, map keys.** One uniform exact relation (R18): `1 == 1.0`, `1.0 == 1.00`, `1 == rational(2, 2)` hold, and
  `< <= > >=` order exact kinds mathematically. A finite Float64 compares by its exact represented value (the exact operand is
  never rounded); `+0.0`/`-0.0` equal exact zero; NaN is unequal to everything including itself and every ordered comparison with
  it is `false`; infinities order as extended reals. Map keys: any non-integral Decimal, Rational, or float collides with an equal
  value of any of those kinds in one `("num-fraction", n, d)` bucket (lowest terms), integral values of any kind share the integer
  bucket, NaN is an illegal key, and infinities keep distinct-by-sign buckets.
- **Misuse and limits.** Every numeric misuse family (zero division, invalid `rational`/`float64`/`exact` arguments, mixed-domain
  arithmetic, illegal NaN key) fails with deterministic, host-independent diagnostics and no raw host exception text. A
  Decimal coefficient/exponent or Rational numerator/denominator beyond a private bound (default 14,000 bits) raises the
  deterministic `numeric-resource-limit` error before any expensive work; the bound does not apply to plain Integer arithmetic,
  which stays unbounded, and its value is a host/test detail, not Genia semantics.
- **Cross-surface recognition.** Quoted and quasiquoted numeric literals materialize the same runtime kind as ordinary evaluation;
  `self_evaluating?`/metacircular `eval` treats Decimal and Rational as self-evaluating; Sheets CSV rendering, format-spec
  numerics, shell-stage stdin materialization, JSON Schema `"number"` matching, and R12 finite-score validation recognize Decimal
  and Rational.

Explicit limitations: no Rational literal syntax, Float64 suffix or raw-bit syntax, public NaN construction, arbitrary-precision
JSON transport, locale-sensitive formatting, or C++ implementation.

## 9.32) R23 numeric rendering and JSON interchange (digest; Experimental)

Current-state digest of former sections 9.32-9.37 (ticket-by-ticket text is preserved verbatim, as non-authoritative
provenance, in `docs/state-record/numeric-r21-r23-records.md`). Contract:
`docs/design/r23-numeric-representation-interchange-contract.md`; audit: `docs/analysis/r23-release-truth-audit.md`; release
page `docs/releases/R23.md`. R23 is complete. Python reference host only; no C++ implementation. It changes no R22
arithmetic, equality, or comparison.

LANGUAGE CONTRACT:

- **Canonical rendering.** `display` and `debug_repr` render numbers identically:
  - Integer: its decimal text.
  - Decimal: fixed notation when the adjusted exponent (`digits + exponent - 1`) is in `-6..20`, otherwise scientific (one digit
    before `.`, lowercase `e`, explicit `+`/`-` exponent sign, no needless exponent zeros); no insignificant trailing fractional
    zeros; an integral value keeps a `.0` suffix (`500.0`).
  - Rational: `<numerator>/<denominator>` with no spaces.
  - Float64: `float64(<shortest-roundtrip-decimal>)`, rendered with the Decimal rule; signed zero is `float64(0.0)` /
    `float64(-0.0)`; non-finite values are `float64(nan)`, `float64(inf)`, `float64(-inf)`. The REPL/CLI final-value echo uses
    the same rendering.
- **Field format specs.** Alignment and width (`<n`, `>n`, `^n`) operate on the canonical text. Precision `.n` rounds half-up
  from each kind's exact value (Decimal coefficient/exponent, Rational numerator/denominator by integer division, Float64 exact
  binary value via its integer ratio, so `2.675` rounds `2.67` at 2 places); NaN and infinity raise a normalized
  `format-error` requiring a finite value. Zero-padding (`0n`) and grouping (`,`) apply only to canonical text that is a plain
  numeral; a Rational atom, a `float64(...)` atom, or scientific Decimal text raises the existing `format-error` diagnostic.
  Format specs never change a value's kind.
- **Strict JSON (`json_decode`/`json_encode`).**
  - Integer is bounded to the R9 safe interval (+/-(2^53-1)).
  - A JSON fraction or exponent token decodes lexically to an exact Decimal (never through host float); it must satisfy
    `stable_json_decimal` (the value survives conversion to binary64 and back to its shortest-roundtrip decimal as the same
    canonical Decimal), otherwise decode fails with reason `json_number_out_of_range`. `NaN`/`Infinity` are invalid JSON.
  - Encode emits a stable Decimal as its exact canonical spelling as a raw JSON number and rejects an unstable one with
    `json_number_out_of_range`; it never rounds or degrades to a string.
  - A Rational encodes only when its reduced denominator has no prime factors other than 2 and 5 and the equivalent Decimal is
    stable: a non-terminating Rational fails with `unsupported_json_value`, an unstable terminating one with
    `json_number_out_of_range`. Decode never constructs a Rational (a decoded Rational form is an equal Decimal under R18).
  - A finite Float64 encodes using the same canonical digits as rendering with the `float64(...)` wrapper removed; NaN and
    infinities fail with `json_number_out_of_range`. Decode never produces Float64.
  - Every failure uses the existing structured boundary outcome with a fixed reason plus a structured `cause` context field; no
    raw exception text and no new reason symbols.
- **Compatibility JSON (`json_parse`, `json_stringify`, `json_pretty`, `parse_jsonl_record`).** Fraction and exponent tokens
  decode through the same lexical parser to exact Decimal, never host float, but without the `stable_json_decimal` gate
  (legacy tolerance: failures stay `none(...)` only for outright parse or type failures). `json_stringify` accepts Decimal,
  terminating Rational, and finite Float64 and always emits exact canonical decimal text without the stability gate; a
  non-terminating Rational or a non-finite Float64 fails with the existing `none("json-stringify-error", ...)` shape.
  `json_stringify(json_parse(text))` round-trips decimal numbers. The `none(...)` versus `err(...)` difference between the
  compatibility and strict surfaces is an approved, unchanged difference.
- **Diagnostics.** Numeric and JSON failure paths in these surfaces carry portable type names (for example `"rational"`,
  `"decimal"`, `"float64"`) and no raw Python class or exception text.

Explicit limitations: no arbitrary-precision JSON-number transport, no new JSON dialect, no locale-sensitive formatting, no new
general formatting language, no Rational literal syntax, and no C++ implementation.

## 9.38) Provider-composition proofs P8 and P9 (digest; evidence only)

Current-state digest of former sections 9.38-9.39 (verbatim provenance text in
`docs/state-record/provider-proof-records.md`). Designs: `docs/design/p8-alternate-provider-substitution-proof-design.md`,
`docs/design/p9-genia-wit-interoperability-mapping.md`, `docs/design/p9-wit-toolchain-build.md`; ledger:
`docs/analysis/provider-composition-stage0.md`. These are architecture-exploration proofs, not a numbered release. They add no
Genia syntax, builtin, factory, or Core IR node and change no `src/genia/retrieval.py` behavior; `retrieve/4`'s public
contract, error vocabulary, and Outcome shape (R12) are unchanged. Python reference host only.

- **P8 (alternate-provider substitution).** Two independent realizations of the retrieve provider, both installed through the
  unmodified `create_fixture_retrieve_provider`, give the same Genia-source `retrieve(...)` call a contract-conformant Outcome:
  a fixed-order list-backed handler and `hosts/python/r12_retrieve_cosine_fixture.py` (id-keyed backend, deterministic cosine
  ranking). Binding is explicit only; providers never cross-invoke; both pass the identity/space/dims compatibility guards;
  Outcome shape is identical while content (order, score) may differ; provider-internal objects never appear in rendered
  output; a raising handler normalizes to `err("retrieve-transport-failure", {kind: other})`; Integer, Decimal, Rational, and
  Float64 scores survive exactly; a non-finite score is `retrieve-response-invalid` (`stage: score`).
- **P9 (Genia <-> WIT mapping).** A real compiled, validated WIT component (`wit/genia-retrieve/world.wit`, package
  `genia:retrieve@0.1.0`) maps Integer, Decimal, and Rational as structural records (never a fixed-width WIT integer or `f64`), a
  three-case outcome variant (never `result<T, E>`), an ordered-map adapter, and an `index-ref` record. The Python-host-only
  `hosts/python/wit_retrieve_adapter.py` (never reachable from Genia source) calls the component through a pinned `wasmtime`
  command-line process and round-trips numerics with no precision loss, ordered maps with R17/R18 key identity, and all three
  Outcome cases as distinct constructors. Protected carriers and non-finite floats are rejected before any component call; an
  invalid invocation is a normalized `WitComponentFaultError`, distinct from an ordinary `err("retrieve-rejected")` Outcome.

Explicit limitations: not a provider registry, binding-plan, or R36 execution-envelope proof; `index-ref` is a record, not a
WIT resource or borrow; the ordered-map adapter is exercised only against a narrow Integer/String value variant; no claim is
made for `embed/4`, `index/4`, or `rerank/4`; the `wasmtime` toolchain pin was a release candidate when built.

## 9.40) External direct process execution (`execution.process`)

Status: Implemented (Python reference host). Contract `docs/design/execution-process-contract.md`; design `docs/design/execution-process-design.md`; detailed pre-condensation text in
`docs/state-record/server-and-process-records.md`. `execution.process(capability, request) -> some(ProcessResult) | err(reason, context)` has no release number (it specializes the host-capability taxonomy and R14
ownership/finalization patterns) and is distinct from the in-process `process.*` mailbox family (`spawn`, `send`, `process_alive?`): this is external direct executable execution.

LANGUAGE CONTRACT:

- `import execution` then `execution.process(capability, request)` is an ordinary two-argument call. `capability` is an opaque, host-created process-execution capability that pure Genia source cannot construct, compare,
  serialize, or render; there is no ambient capability or `host.supports(...)`; it must be supplied explicitly (as for R11's model provider or R14's HTTP transport).
- `request` is exactly the closed map `{executable: symbol, args: [string, ...], timeout_ms: integer}`. `executable` is a provider-bound symbolic identity (for example `quote(candidate_host)`), never an OS path, command
  string, or promise to search `PATH`. Each `args` element becomes one exact child argv element: no shell is invoked and no quoting, splitting, glob expansion, interpolation, or command substitution occurs. `timeout_ms` is a
  plain Integer in `1..300000`; a boolean or any other numeric domain is rejected as misuse.
- A malformed capability or request, or any request value that recursively contains a protected leaf (existing R10 `contains_protected`/`reject_protected`), is runtime misuse raised before any resolution or provider effect. Version
  1 has no process declassification sink and no authority argument (unlike the R14 protected-HTTP-header sink).
- A completed child attempt is always `some({exit_code, stdout, stderr})`, including a nonzero `exit_code`: a program's nonzero exit is ordinary result data, never an `execution.process` failure. `stdout`/`stderr` are opaque
  `Bytes` (never decoded or line-ending normalized); each channel has an independent maximum of exactly `1,048,576` bytes (exactly that size succeeds; one more byte overflows).
- Recoverable failures are exactly: `err("process-executable-unavailable", {executable})` (unbound symbol), `err("process-unauthorized", {operation: quote(execute), executable})` (bound but denied),
  `err("process-launch-failure", {executable})`, `err("process-timeout", {timeout_ms})` (the owned child is terminated and reaped first), `err("process-output-limit", {limit_bytes: 1048576})` (either channel; all partial
  output discarded), and `err("process-provider-failure", {operation: quote(execute)})` (any other host condition). No raw exception text or type name, errno description, native path, or process id crosses into a context,
  diagnostic, or rendering. `process-unsupported` is reserved taxonomy this operation never emits (it belongs to the deferred capability-provisioning boundary).
- Adds no syntax, no new Core IR node, and no Flow/Seq change: it lowers as an ordinary dotted module call.

PYTHON REFERENCE HOST:

- `src/genia/process_capability.py`: `GeniaProcessCapability` (opaque; symbol-to-native-target bindings, an authorization predicate, a launcher), minted only by privileged host code through
  `create_process_capability(bindings, authorized, launcher)`; there is no Genia-callable constructor.
- `src/genia/process_transport.py`: `launch_process(...)` uses `subprocess.Popen(argv, shell=False)` with `stdin=DEVNULL`, two reader threads that drain stdout/stderr concurrently and stop incrementally once a channel exceeds
  `1,048,576` bytes, a monotonic-clock deadline, and unconditional idempotent `kill()` plus reap on every failure path, so no owned child survives; a nonzero exit is always a result.
- `src/genia/process_execution.py`: `perform_process_execution(capability, request)` validates the closed request in field order, calls `reject_protected(request, "execution.process")` before any launch, resolves the symbol,
  and normalizes the failure taxonomy; `src/genia/std/prelude/execution.genia` exposes `process(...)` over the private builtin `_execution_process`.

Explicit limitations (deferred): no source-level capability provisioning (only privileged host code can call `create_process_capability`; no file, command, pipe, import, REPL, test, or server mode provisions one implicitly);
no protected argv/environment sink, user environment, cwd, child stdin beyond EOF, streaming output, TTY, signals, process handles, supervision, retries, or remote execution; no new Core IR, R35 storage, or R36
location-independent execution. The portable contract has a single-host implementation: `execution_process` is registered in `spec/manifest.json` `optional_capabilities` (the Python host self-declares `supported`), but
no shared-spec case declares `requires: [execution_process]` yet (no host-neutral fixture mechanism exists), so that declaration is advertisement, not conformance evidence (`docs/host-interop/capabilities.md`).

## 9.41) R28 native Genia MCP server (digest; Experimental, Python reference host only)

Current-state digest of former sections 9.41-9.47 (phase history is preserved verbatim, as non-authoritative provenance, in
`docs/state-record/r28-mcp-records.md`). Contract: `docs/design/r28-genia-mcp-contract-threat-model.md` (with amendments A1-A7);
reference: `docs/mcp/reference.md`; conformance: `docs/mcp/conformance-matrix.md`; release page `docs/releases/R28.md`; the
completion and acceptance record is section 9.49. LANGUAGE CONTRACT: none. The behavior below is the application contract of
`apps/mcp/mcp.genia`, an ordinary Genia program with no new syntax, builtin, Core IR node, or language semantics. There is no C++
MCP implementation and no cross-host parity claim.

APPLICATION BEHAVIOR (local stdio only; no HTTP transport):

- **Launch.** `genia apps/mcp/mcp.genia <contract_revision>` takes exactly one argument, 40 lowercase hexadecimal characters;
  anything else writes one fixed diagnostic to stderr, nothing to stdout, and exits nonzero without echoing the value. The
  checked-in `.mcp.json` registers one stdio server `genia` that runs `hosts/python/mcp_launch.py` (identity plumbing only:
  resolves `git rev-parse HEAD`, fixes the environment allowlist, supplies host capabilities). Its guide is
  `docs/mcp/stdio-development.md`; `scripts/genia-mcp` starts the same launcher.
- **Framing.** One JSON-RPC message per stdin line (split on `\n` only), one response per request on exactly one stdout line;
  empty lines are ignored; a well-formed notification gets no response; the server exits at stdin EOF. Native Genia owns
  decoding, validation, dispatch, result and error construction, JSON encoding, framing, and stdout.
- **Protocol eras.** Exactly two are served, selected per request: a request whose `params._meta` carries
  `io.modelcontextprotocol/protocolVersion` is `2026-07-28` (stateless: no `initialize`, no session; `_meta` requires that
  version string and a `clientCapabilities` object; results carry `_meta["io.modelcontextprotocol/serverInfo"]`
  `{name: "genia-mcp", version: <contract_revision>}`, and discover/list results carry `ttlMs: 0`, `cacheScope: "public"`);
  every other request is `2025-11-25` (amendment A5). In `2025-11-25`, `initialize` needs object params with string
  `protocolVersion`, object `capabilities`, and object `clientInfo` (string `name` and `version`); only `2025-11-25` succeeds
  (`{protocolVersion, capabilities: {tools: {}}, serverInfo}`), any other version is `-32602` with `data.supported` and
  `data.requested` (never negotiated down), a second `initialize` is `-32600`. One process-local state bit (new/initialized)
  gates `tools/list` and `tools/call` (`-32602` before `initialize`); `ping` is `{}` always; `notifications/initialized` is
  accepted silently. Compat results omit `resultType`, `ttlMs`, `cacheScope`, and `_meta`; everything else is identical across
  eras. Client capabilities (`roots`, `sampling`, `elicitation`, `tasks`, `extensions`) are shape-checked and discarded; the
  server never sends a request or notification.
- **Methods and protocol errors.** `server/discover` (capabilities exactly `{tools: {}}`), `tools/list` (no pagination; any
  `cursor` is `-32602`), `tools/call`. Fixed messages never echo caller text: unparseable JSON `-32700` (invalid Unicode too);
  invalid JSON-RPC object, including a non-string/non-integer `id` `-32600`; unknown method (resources, prompts, completion,
  logging, tasks, roots, sampling, elicitation, an `initialize` carrying the `2026-07-28` `_meta`) `-32601`; missing or malformed
  `_meta`, bad `tools/call` params, unknown tool, or unexpected arguments `-32602`; unsupported version `-32022` with
  `data.supported = ["2026-07-28"]`.
- **Tools.** Exactly four, in this order: `genia_capabilities`, `genia_parse`, `genia_run`, `genia_language_profile` (section
  9.50). `genia_parse` and `genia_run` are advertised only when the launcher provisions them; plain file mode lists
  `genia_capabilities` and `genia_language_profile`. Results are `CallToolResult` with one text item and `structuredContent` equal to
  the envelope `{schema_version: "genia.mcp.v1", status, result, error}`; `genia_capabilities` takes no arguments and reports
  `server`, `mcp`, `genia`, `tools`, and the governed `execution_profile` (`portable_mcp_implementation` is `false`).
- **`genia_parse`.** Input exactly one string `source` (any other shape is `-32602`); over 262,144 UTF-8 bytes is an `input_limit`
  envelope; parsing never evaluates. Success is `{kind: "parsed", ast}` with the existing normalized parse surface, transported
  losslessly (integer literals outside the R9 range remain exact JSON number tokens; a client decoding JSON numbers as
  IEEE-754 doubles can lose precision). A syntax failure is `parse_error` (phase `parse`, character offset only); other host
  failures are a fixed `internal_error`; a result over 3,276,800 bytes is `result_limit`. The AST is intentionally coarse.
- **`genia_run`.** Input exactly one string `source`, same input limit. Success is `{kind: "completed", value: {rendered},
  stdout, stderr, exit_code: 0}` where `rendered` is the canonical debug rendering and stdout/stderr are captured separately;
  the source is evaluated as command source (`run_source`) and `main` is **not** dispatched. Failures carry no partial data and
  fixed messages: `parse_error`, `policy_denied`, `runtime_error` (no diagnostic text), `timeout` (5,000 ms), `cancelled`,
  `result_limit` (a channel or rendered value over 1,048,576 bytes, or the whole result over 3,276,800 bytes), `internal_error`.
  A `notifications/cancelled` whose `requestId` equals the active request terminates and reaps the worker (matched in native
  Genia); a cancel for another id or after completion is ignored.
- **Execution policy (defense in depth, not a security sandbox, not production multi-tenant isolation).** Each call runs in a
  fresh worker process: static policy over the raw parser AST rejects every `import`, shell stage `$(...)`, and any reference to
  an authority-bearing name (file, zip, resource, HTTP, server, process, configuration, secret, declassification, model,
  retrieval, `input`, `stdin_keys`), conservatively including user definitions reusing those names; the environment is pruned by a
  default-deny classification with runtime stubs for process creation and sockets; `argv()` is empty and `stdin` is immediate
  EOF; a protected-value carrier in the result is `policy_denied`. The worker has its own process group, a minimal environment, a
  private empty working directory, process limits (`FSIZE` 0, `CORE` 0, `CPU` 10 s, `NOFILE` 64, `AS` 2 GiB where the platform
  allows), a monotonic 5,000 ms deadline that starts when the worker reports readiness, and forceful kill-and-reap on timeout,
  cancellation, overflow, or failure. A user+network namespace is used only when verified once at host start and is never
  claimed otherwise. Not provided: filesystem namespaces, seccomp, cgroup limits, a PID namespace, or protection against
  interpreter or kernel defects. The host unwinds on SIGTERM/SIGHUP, reaping the worker and its directory.
- **Clients and evidence.** The official TypeScript client SDK is exercised in CI (`tools/mcp_acceptance/`); the authentic VS Code +
  GitHub Copilot acceptance record is section 9.49. Clients that send `initialize` work through the `2025-11-25` era. Streamable
  HTTP is deferred. Known limitations are recorded in the living ledger `docs/analysis/r28-host-dependency-inventory.md`.

## 10) Explicitly not implemented (current)

- general unrestricted host interop / FFI layer
- general member access syntax
- index syntax
- generalized flow runtime semantics beyond the current phase (async scheduling, advanced backpressure/cancellation, configurable multi-port stages)
- full Flow system (stages/sinks/backpressure/multi-port pipelines)
- language-level scheduler/selective receive/timeouts (concurrency remains host-primitive based)
- MCP resources/prompts, HTTP MCP transports, and any C++ MCP implementation (the R28 MCP server is complete: four tools over local stdio on the Python reference host; see sections 9.41-9.50)

## 11) Example demos shipped in-repo

Curated runnable examples are published per release in `docs/releases/` (see `docs/releases/README.md`); the repository `examples/` directory
holds the programs (for example `ants*.genia`, `tic-tac-toe.genia`, `validated_pipeline_demo.genia`, `ollama_chat.genia`, and the R10-R14
proving cases and `examples/mcp/`). Examples describe only currently implemented behavior; the displaced catalogue text is in
`docs/state-record/tooling-and-examples.md`.

## 9.48) R28 macOS portability of the governed `genia_run` profile
<!-- anchor: state:mcp-macos -->

Current state (history in `docs/state-record/r28-mcp-records.md`; ledger R28-H47/H48; pre-flight `docs/design/r28-e28-6-macos-execution-preflight.md`). No Genia syntax, builtin, Core IR node, MCP tool, resource, prompt,
protocol, authority, limit, parse behavior, or envelope changed.

- **Worker limits are platform-aware.** `hosts/python/mcp_worker.py` `apply_limits()` applies `RLIMIT_FSIZE` 0, `CORE` 0, `CPU` 10 s, `NOFILE` 64 on every platform, and `RLIMIT_AS` 2 GiB on every platform; any failure is
  `internal_error` (the worker never runs without them). The one exception: on Darwin a rejected `RLIMIT_AS` is tolerated (the kernel rejects an address-space bound below the process's current virtual size). Linux is
  unchanged; there is one execution model and the same envelopes on every platform.
- **macOS has a weaker resource bound and no namespace.** There is no address-space bound on macOS, so memory is bounded only by the 5,000 ms deadline and the 10 s CPU limit; there is no network namespace (Linux-only);
  network, file, process, and import denial rests on the static policy, the pruned environment, and the runtime stubs. No namespace or sandbox is claimed on macOS.
- **Verification.** macOS governed execution is owner-verified (full R28/MCP suite and authentic VS Code run 3, section 9.49); `tests/unit/test_r28_mcp_portability.py` covers simulated Darwin rejection, fail-closed rules, and
  diagnostic hygiene; lifecycle helpers use `/proc` on Linux and `ps`/`lsof` elsewhere; Linux-only namespace tests skip on macOS. A development-only worker diagnostic (`GENIA_MCP_WORKER_DIAG=1`) writes to the worker's own
  stderr, is never forwarded, and never appears on the wire.

## 9.49) R28 completion: authentic VS Code + GitHub Copilot acceptance
<!-- anchor: state:mcp-surface -->

R28 (Genia MCP Server) is **Complete**: contract section 12.2 is satisfied by an authentic VS Code + GitHub Copilot run. Evidence record: `docs/mcp/acceptance/vscode-copilot-evidence.md`; release page:
`docs/releases/R28.md`. This section adds no Genia syntax, builtin, Core IR node, MCP tool, resource, prompt, transport, protocol, authority, limit, or envelope.

- **Run 3 (PASS)**, macOS, VS Code 1.138.0, Copilot Chat 0.66.0: VS Code started the repository-configured `genia` server (`.mcp.json`, `initialize` for `2025-11-25`)
  and reported `Discovered 3 tools`; `genia_capabilities` reported protocol `2025-11-25`, transport `stdio`, the three tools, profile `source-only-isolated-v1`, timeout 5000 ms, and every authority flag `false`;
  the broken canonical demo gave `parse_error` at character offset 171 through `genia_parse`; the corrected demo parsed and, through Copilot Agent, `genia_run` returned `ok`/`completed`, exit code 0, with value, stdout, and
  stderr separate; no `mcp_launch`, `mcp_host`, or `mcp_worker` process remained after the server stopped. That no resources or prompts were visible rests on the advertised `capabilities: {tools: {}}`, automated `-32601`
  results, and VS Code's report of exactly three tools, not a separate UI inspection. History: run 1 failed at `initialize` (fixed by amendment A5), run 2 failed at `genia_run` on macOS (fixed by section 9.48); the release
  gate (`tests/unit/test_r28_release_gate.py`) reads the latest run (executed, complete, `PASS`, on an allowed negotiation path).
- **Agent guidance (contract 12.3):** `docs/ai/LLM_CONTRACT.md` and `.github/copilot-instructions.md` direct Genia development agents to prefer the Genia MCP server for parsing and running source where an MCP client is
  available; they add no language semantics and do not make MCP a prerequisite. Post-R28 follow-up candidates stay open in the ledger (`docs/analysis/r28-host-dependency-inventory.md`) and the parking lot, not ticketed.
- **Supported platforms and limits:** Python reference host only; local stdio only; exactly four tools (the fourth, `genia_language_profile`, is section 9.50; the acceptance runs saw three); no resources, prompts,
  Streamable HTTP, or C++ MCP; Linux (CI) and macOS (owner-run, not in CI) verified, Windows unsupported; macOS has no address-space bound and no network namespace; the execution profile is a defense-in-depth profile,
  not a security sandbox.

## 9.50) R28 `genia_language_profile` (MCP adapter affordance; amendments A6 and A7)
<!-- anchor: state:mcp-language-profile -->

Contract: section 19 (A6) and section 20 (A7) of `docs/design/r28-genia-mcp-contract-threat-model.md`; pre-flights `docs/design/r28-a6-language-profile-preflight.md` and
`r28-follow-up-1086-maturity-gap-preflight.md`. The tool adds no Genia syntax, parser or evaluator behavior, builtin, Core IR node, host capability, resource, prompt, transport, limit, or authority, and no Python host code: it is
native Genia in `apps/mcp/mcp.genia`. It is an adapter affordance for assistants, not language behavior; this file and `GENIA_RULES.md` remain the language authority. Python reference host only; no C++ MCP.

LANGUAGE CONTRACT: none. The MCP wire behavior below is the application contract of `apps/mcp/mcp.genia`.

PYTHON REFERENCE HOST (MCP adapter):

- The advertised surface is exactly four tools, in this order: `genia_capabilities`, `genia_parse`, `genia_run`, `genia_language_profile`. `genia_language_profile` needs no host capability, so plain file mode advertises
  `genia_capabilities` and `genia_language_profile` and the launcher advertises all four; `genia_capabilities.tools` reports the advertised set. No resources, prompts, pagination, or other protocol surface is added.
- It takes no arguments (`arguments` omitted or `{}`; any other value is `-32602`), has the same input schema as `genia_capabilities`, and returns the normal `CallToolResult` with `structuredContent` and one text item holding
  the same `genia.mcp.v1` envelope (`result = {language: {...}}`).
- `language` is a fixed constant except `contract_revision` (the launch revision `genia_capabilities` reports): `name`, `control_flow`, `supported_forms`, `absent_forms`, `patterns`, `idioms`, `examples` (`gcd`, `factorial`; they
  evaluate to `6` and `120` under direct command-source evaluation, verified by tests), and (A7) `discovery`. A literal-first-parameter multi-clause function needs its first clause declared `open`
  (`open gcd(a, 0) = a`; the same text without `open` is rejected), and the profile states that rule in `idioms.clauses`. Output is byte-identical across calls, protocol eras, and namespace modes; JSON member order is the
  encoder's sorted order.
- **Provenance.** Each claim restates implemented behavior documented in the language sections of this file (control flow in `state:control-flow`, patterns in `state:pattern-matching`, tail calls in `state:tail-calls`, open
  clauses in `state:open-functions`). The governed members and the discovery catalogue are generated into a delimited block of `apps/mcp/mcp.genia` from the `mcp_language_profile` registry in
  `docs/contract/semantic_facts.json`, a guarded projection source: this file stays the authority, and each registry fact carries semantic anchors (`<!-- anchor: state:... -->` markers in this file) and evidence (STATE
  text, executable probes, or manifest cross-checks). The server never reads the registry at runtime; `state_sections` values keep their legacy section numbers through the registry's anchor crosswalk.
- **Discovery (A7).** `language.discovery` is exactly `{coverage, facts}`: `coverage` is `"curated_non_exhaustive"` and `facts` is a fixed ordered catalogue of 12 scoped facts, each exactly `{id, scope, status, maturity,
  summary, state_sections}`. Status is `implemented|partial|planned|scaffolded|unsupported` within the row's scope; maturity copies an explicit STATE rating or is JSON null (null means unspecified, not Stable and not
  unavailable). The facts are `pattern_branching`, `tail_calls`, `if_and_loops`, `flow_shared_coverage`, `core_ir_stability`, `cpp_language_floor`, `other_language_hosts`, `browser_runtime`, `mcp_surface`, `cpp_mcp`,
  `windows_mcp`, and `macos_hardening`; their ids, scopes, statuses, maturity labels, summaries, and anchors are defined only in the registry (and projected into amendment A7, section 20). Partial C++ support is the bounded
  R27 language floor, not C++ MCP; partial Flow shared coverage does not mean missing Python Flow behavior; browser scaffolding is documentation only; macOS hardening is bounded as in section 9.48 and no security sandbox
  is claimed. The catalogue grants no execution authority, is not an exhaustive inventory, performs no live discovery, is at most 16,384 UTF-8 bytes with summaries at most 256 bytes (static output bounds, not runtime
  limits), and is identical in plain file mode.
- **Evidence:** `tests/unit/test_r28_mcp_language_profile.py`, `tests/unit/test_r28_mcp_language_registry.py`, `tests/doc/test_state_anchors_and_registry_sync.py`, and the golden wire snapshot
  `tests/data/mcp_language_profile.golden.json`; matrix rows D1, D5, D6, D9, D10 in `docs/mcp/conformance-matrix.md`. The authentic client acceptance runs (1-3) predate A6 and A7 and describe the three-tool surface; no new
  authentic client run is claimed. Not done: source-specific parse or run diagnostic hints.

## 9.51) R28 MCP grounded-evidence example

LANGUAGE CONTRACT: unchanged. This is one checked-in example program and tests, not a new Genia feature.

PYTHON REFERENCE HOST (MCP example): `examples/mcp/grounded_evidence.genia` runs through the existing `genia_run` tool. It validates client-supplied document literals, chunks valid documents with Experimental R12 `chunk/2`,
and prints one strict JSON evidence package on stdout (the question, retained validated input documents, selected evidence with exact `chunk/2` source spans, first-occurrence sources, indexed diagnostics, and a selection
descriptor whose claim is `ordinary_example_selection_not_r12_retrieve`). It uses only ordinary Genia plus existing public helpers and adds no MCP tool, resource, prompt, transport, authority, builtin, parser/evaluator
behavior, Core IR node, provider, or host capability; no C++ MCP or cross-host parity is claimed.

The selection step is a deterministic example-local exact-term overlap over the checked-in source literals. It is not R12 `retrieve/4`, semantic retrieval, embedding, reranking, RAG, citation validation, answer generation,
or evidence authenticity; answer generation remains outside Genia with the MCP client. Document ids and metadata are client-asserted labels; the example preserves supplied spans and diagnostics but does not verify
origin or trust. Evidence: `tests/unit/test_r28_mcp_grounded_evidence_example.py`.


## Development documentation infrastructure

The maintained-code documentation policy and native-language coverage checker
are development infrastructure, not language semantics or host capabilities.
See `docs/contract/code-documentation.md` and `docs/process/code-documentation.md`.
Existing source-documentation debt is tracked separately from semantic host gaps.
