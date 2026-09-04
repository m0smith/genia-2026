# Genia — Current Language State (Main Branch)

This file describes what is **actually implemented now** in the Python runtime.

## 0) Multi-host status


Implemented today:

- **Python is the only implemented host and is the reference host.**
- Shared semantic-spec contract categories are:
  - parse
  - ir
  - eval
  - cli
  - flow
  - error
- The implemented shared Semantic Spec System currently executes **eval**, **ir**, **cli**, **flow**, **error**, and **parse** cases.
- The current shared spec runner compares normalized:
  - eval `stdout`
  - eval `stderr`
  - eval `exit_code`
  - cli `stdout`
  - cli `stderr`
  - cli `exit_code`
  - flow `stdout`
  - flow `stderr`
  - flow `exit_code`
  - error `stdout`
  - error `stderr`
  - error `exit_code`
  - IR portable normalized output
  - parse normalized AST (exact match for `kind: ok`) or parse error type + message substring (for `kind: error`)
- The working Python implementation lives in:
  - `src/genia/`
  - `tests/`
  - `src/genia/std/prelude/`
  - `hosts/python/` (adapter, normalization, and category execution modules)
- Multi-host documentation/spec scaffolding exists in:
  - `docs/host-interop/`
  - `docs/architecture/core-ir-portability.md`
  - `spec/`
  - `tools/spec_runner/README.md`
  - `hosts/`
- A formal host capability registry contract is documented at `docs/host-interop/capabilities.md`. It is the authoritative reference for capability names, Genia surface, input/output shapes, normalized error behavior, and portability status for each host capability.

Scaffolded or planned, not implemented as hosts:

- Node.js, Java, Rust, Go, C++: planned only, not implemented
- `hosts/python/` is now the adapter location, but the core runtime remains in `src/genia/`
- No generic multi-host runner exists; all conformance is validated against the Python reference host

**Maturity:**

- Shared host contract is **Partial**: the contract categories above are documented, and executable shared spec coverage is implemented for `eval`, `ir`, `cli`, first-wave `flow`, initial `error`, and initial `parse` behavior in the Python reference host. Other hosts are not implemented.
- Semantic Spec System is **Experimental**: the file format, runner, and initial case inventory exist for `eval`, `ir`, `cli`, first-wave `flow`, initial `error`, and initial `parse` behavior in this phase.
- Flow behavior is implemented in Python, and shared semantic-spec coverage for flow is now **active but partial**. Current flow shared coverage is limited to first-wave cases proving lazy pull-based observable behavior through early termination, single-use enforcement, deterministic outputs, `evolve(init, f)` progression, `refine(..steps)` behavior, `rules(..fns)` compatibility behavior, `step_*` / `rule_*` equivalence, the `rules()` identity stage, selected rule result defaulting/no-effect behavior, focused Flow `map` / `filter` / `scan` coverage, selected Seq-compatible `each` / `collect` / `run` / `reduce` terminal behavior, and a resource lifecycle case (`seq-finalization-drop-take`) proving Flow-aware `drop |> take |> collect` composition with bounded pulling and correct output. Advanced Flow behavior is not covered by shared semantic specs in this phase.
- IR stability remains **Partial**: the minimal portable Core IR contract is documented with field-level lowering invariants (bare `none` reason=null, `none()` reason wrapped as `IrQuote`, canonical `lhs.name` -> `IrBinary(op=SLASH, named_access=true)` for narrow named access (ordinary slash/division lowers as `IrBinary(op=SLASH)` without `named_access`; legacy `lhs/name` compatibility removed); neither form is general field-path lookup, `IrAssign` placement in `IrBlock.exprs`, optional fields), the Python runtime guards that boundary, and shared semantic-spec case coverage now validates the full portable node family in the Python reference host, including `quasiquote` bodies with `unquote` and `unquote_splicing` in list context.

**Explicit limitations:**

- Only Python is implemented; all other hosts are planned or scaffolded only.
- No browser runtime or playground is implemented; browser artifacts are documentation only.
- No generic multi-host runner exists; all conformance is validated against the Python reference host.
- Shared semantic-spec case files currently exist under `spec/eval/`, `spec/ir/`, `spec/cli/`, `spec/flow/`, `spec/error/`, and `spec/parse/` in this phase.
- Parse shared semantic-spec coverage is limited to initial cases for stable, already-implemented syntax forms; parse spec coverage expands only when new forms are explicitly added and tested.
- Flow is implemented as a lazy, pull-based, single-use runtime value; async, multi-port, and advanced flow features are not present.
- Flow orchestration supports both `refine(..steps)` (preferred) and `rules(..fns)` (compatibility); both are available and behave identically.
- Step/rule helpers are available as both `step_*` (preferred) and `rule_*` (compatibility) names.
- Flow shared semantic-spec coverage is limited to first-wave observable cases only; advanced Flow behavior remains uncovered in shared specs.
- CLI contract covers file, command, pipe, and REPL modes as described; no shell tokenization, `$1`/`$2`/`ARGV`-style, or advanced CLI features exist.
- The current shared semantic-spec runner asserts `stdout`, `stderr`, and `exit_code` for eval cases.
- The current shared semantic-spec runner asserts `stdout`, `stderr`, and `exit_code` for CLI cases.
- The current shared semantic-spec runner asserts `stdout`, `stderr`, and `exit_code` for error cases.
- The current shared semantic-spec runner compares normalized portable Core IR output for IR cases.
- The current shared semantic-spec runner compares normalized parse output for parse cases: exact AST for `kind: ok`, type and message substring for `kind: error`.
- Only the minimal portable Core IR node families are used in the contract; host-local optimized nodes (e.g., `IrListTraversalLoop`) are excluded.

**GENIA_STATE.md is the final authority for implemented behavior. All other docs/specs must align with this contract.**

## 0.1) Browser playground status

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
- Coverage is still partial and experimental; see below for category status.

PYTHON REFERENCE HOST:

- Python is the only implemented host and is the reference host.
- All conformance is validated against the Python reference host.
- The current shared spec runner executes eval cases (`spec/eval/`), comparing normalized `stdout`, `stderr`, and `exit_code`. Eval shared coverage includes list-side Seq-compatible `collect`, `run`, lazy `each`, item-preserving `each |> collect`, the existing `seq-compatible-list-transform-chain` fixture, list-side `scan` (accepting list input and returning list), Seq-compatible non-list/non-Flow diagnostics for `each`, `collect`, `run`, `map`, `filter`, `take`, `drop`, and `scan`.
- The current shared spec runner executes CLI cases (`spec/cli/`) through the Python host adapter, comparing normalized `stdout`, `stderr`, and `exit_code`.
- The current shared spec runner executes Flow cases (`spec/flow/`) through command-source execution in the Python host adapter, comparing normalized `stdout`, `stderr`, and `exit_code`. Flow shared coverage includes first-wave cases proving lazy pull-based observable behavior through early termination, single-use enforcement, deterministic outputs, `evolve(init, f)` progression, `refine(..steps)`, `rules(..fns)`, `step_*` / `rule_*` equivalence, `rules()` identity, selected rule result defaulting/no-effect behavior, deterministic `keep_some(...)` option-filtering behavior, focused core stdlib Flow coverage for direct `map`, `filter`, and `scan` over Flow inputs, including composed `map`/`filter` and bounded `evolve |> scan |> take |> collect` cases; Seq-compatible terminal coverage for `each` preserving items, `each(print) |> run`, `collect` materialization, and `reduce` accumulation over Flow; and a resource lifecycle case (`seq-finalization-drop-take`) proving Flow-aware `drop |> take |> collect` composition with bounded pulling and correct output.
- The current shared spec runner executes error cases (`spec/error/`) through the same eval execution path used by eval cases, comparing exact normalized `stdout`, exact normalized `stderr`, and exact `exit_code`.
- CLI shared spec coverage proves deterministic non-interactive file mode, `-c` command mode, `-p` pipe mode behavior, and selected native `--test` mode outcomes. Current shared CLI coverage includes basic file execution, file-mode `main(argv())` dispatch, trailing `argv()` exposure, command-mode final-value execution, valid pipe-mode Flow-stage usage, explicit `stdin` / `run` rejection, current pipe-mode guidance for bare per-item stages, bare reducers, and non-Flow final results, plus selected native test-runner passing, runtime-erroring, and discovery-error suite outcomes. REPL mode is not included in shared executable spec coverage.
- The observable CLI shared-spec contract is limited to `stdout`, `stderr`, and `exit_code`.
- The observable error shared-spec contract in this phase is limited to `stdout`, `stderr`, and `exit_code`.
- Eval shared spec cases are loaded from YAML files under `spec/eval/`; each case provides source text plus optional stdin text and is executed independently.
- Error shared spec cases are loaded from YAML files under `spec/error/`; each case provides source text plus optional stdin text, requires `stdout: ""`, exact `stderr`, and `exit_code: 1`, and may include informational `notes` that are not machine-asserted.
- Shared spec YAML loading prefers `PyYAML`; when `PyYAML` is unavailable, the runner can fall back to a Ruby YAML bridge in the current implementation.
- The current eval shared case inventory covers deterministic command-source eval output for:
  - final rendered expression results
  - direct `stdout` output
  - direct `stderr` output
  - combined `stdout`/`stderr` output separation
  - stdin-fed eval cases whose compared surface remains `stdout`, `stderr`, and `exit_code`
  - direct Option rendering for deterministic final-result output (`some(...)`, `none(...)`)
  - pipeline Option propagation for deterministic final-result output (`some(...)` lift and `none(...)` short-circuit)
  - deterministic pattern matching output for currently implemented pattern families (first-match behavior, literals, wildcard/variable binding, list/tuple/map, option, guard, glob, and named reusable pattern forms)
  - deterministic eval failures with exact `stderr` and `exit_code`, including Flow/value boundary errors: `each` given a list, `first` given a Flow, `reduce` given a non-Seq-compatible value (int, string)
  - focused core stdlib list/absence helper behavior: `map` over lists (basic and empty), `filter` over lists (basic, no-match, and Option-element callbacks), `first` (some and empty-list), `last` (some and empty-list), `nth` (in-range and out-of-bounds)
  - selected validation helper behavior: optional field present/absent/invalid outcomes, required field present success, and simple nested validation path success/missing diagnostics (Partial; Python reference host only)
  - `collect_validated/1` behavior: empty source, all-clean, mixed `some`/`none`/`err`, `some` context ignored on clean path, bare `none`, `err` without context, and Flow-compatible source (Experimental; initial coverage only)
  - selected `validate_each/2` behavior: empty list, `some(...)` preservation, and mixed `some(...)` / `none(...)` / `err(...)` preservation (Experimental; initial coverage only)
  - `validate_each/2` output feeding `collect_validated` directly: shared eval coverage proves mixed Outcome results from validation helpers aggregate into clean values plus skipped/error diagnostics. Experimental; initial coverage only.
- Eval normalization is limited to line-ending normalization for `stdout` and `stderr` (`\r\n` and `\r` normalize to `\n`).
- Eval comparison is otherwise exact: `stdout`, `stderr`, and `exit_code` must match exactly after that line-ending normalization.
- Error normalization is limited to the same line-ending normalization used for eval `stdout` and `stderr` (`\r\n` and `\r` normalize to `\n`).
- Error comparison is otherwise exact in this phase: `stdout` must be `""`, `stderr` must match exactly after that line-ending normalization, and `exit_code` must be `1`.
- The current shared spec runner also executes IR cases (`spec/ir/`), comparing normalized portable Core IR output before host-local optimization.
- Error shared coverage is active but initial only: the current inventory proves a narrow normalized error surface (including deterministic pattern miss, guard-all-fail, malformed-glob, named-pattern error cases, and selected `validate_each/2` misuse diagnostics: non-list/non-Flow source, non-callable validator, and non-Outcome validator result) and does not machine-assert structured phase/category/message fields.
- The current shared spec runner executes Parse cases (`spec/parse/`) by calling the Python host parse adapter directly; for `kind: ok` cases the normalized AST is compared exactly; for `kind: error` cases the error type is compared exactly and the message is matched as a substring.
- The current shared spec runner accepts `-v` / `--verbose`, printing each spec name before execution starts and then a single timing line (`<name>\t<elapsed>s`) after each spec completes.
- Parse shared coverage is active but initial only: the current inventory covers stable, already-implemented syntax forms, and now includes named pattern declaration (`pattern Name(value) = body`) and named pattern use in case arms (`Name(inner_pattern)`), including error cases for invalid declaration and use arity. Parse spec coverage expands only when new forms are explicitly added and tested.
- Uncovered or partial categories are not guaranteed and may differ in future implementations.

**Summary:**
- `eval`, `ir`, `cli`, first-wave `flow`, initial `error`, and initial `parse` are active for executable shared spec files.
- `GENIA_STATE.md` is the final authority for implemented behavior. All other docs/specs must align with this contract.

**Host implementation location:**
- The working Python implementation lives in `src/genia/`, `tests/`, and `src/genia/std/prelude/`.
- `hosts/python/` is the active host adapter layer; it is not the core runtime source location (that remains `src/genia/`).
- `hosts/python/adapter.py::run_case(spec: LoadedSpec) -> ActualResult` is the canonical adapter entrypoint, wired to the shared spec runner via `tools/spec_runner/executor.py::execute_spec`. All spec categories route through `run_case`.

**Planned/Scaffolded:**
- Node.js, Java, Rust, Go, C++: planned only, not implemented
- No generic multi-host runner exists; all conformance is validated against the Python reference host

**Limitations:**
- Only Python is implemented; all other hosts are planned or scaffolded only.
- No browser runtime or playground is implemented; browser artifacts are documentation only.
- Shared semantic-spec case files exist under `spec/eval/`, `spec/ir/`, `spec/cli/`, `spec/flow/`, `spec/error/`, and `spec/parse/` in this phase.
- Parse shared semantic-spec coverage is initial only; coverage expands only when new forms are explicitly added and tested.

**GENIA_STATE.md is the final authority for implemented behavior. All other docs/specs must align with this contract.**

---

## 0.2) Repository documentation publishing workflow
Implemented today:

- repository docs are staged into a temporary MkDocs input tree by `tools/stage_docs_for_mkdocs.py`
- the published docs site uses MkDocs with the Material theme
- published sections include:
  - `README.md` as the homepage
  - `GENIA_STATE.md`
  - `GENIA_RULES.md`
  - `GENIA_REPL_README.md`
  - `docs/cheatsheet/*`
  - public-facing host interop docs under `docs/host-interop/`
  - per-release runnable examples under `docs/releases/` (see `docs/releases/README.md`)
  - `docs/strategy/release-roadmap.md`, staged individually as `strategy/release-roadmap.md` with a top-level Roadmap navigation entry; it remains non-authoritative planning guidance and no other `docs/strategy/*` file is published
- GitHub Actions docs workflow behavior is:
  - on pull requests: stage, validate, and build docs without deployment
  - on pushes to `main`: stage, validate, build, and deploy to GitHub Pages
  - after a successful Pages deployment, publish the generated Function Reference mirror to the GitHub Wiki only when the optional `WIKI_TOKEN` repository secret is configured
  - when `WIKI_TOKEN` is absent, skip all Wiki-specific setup and publishing steps without failing the Pages deployment
- docs validation in this phase includes:
  - strict MkDocs builds
  - semantic doc sync tests for protected cross-doc semantic facts
    - the protected facts surface is intentionally small and lives in `docs/contract/semantic_facts.json`
    - validation covers both public docs and LLM-instruction surfaces
  - cheatsheet validation tests
  - core documentation truthfulness and synchronization tests

Clarifications:

- the staging tree is a build artifact only; source-of-truth docs remain in their existing repository locations
- source annotations and the host documentation registry consumed by `tools/gen_function_docs.py` remain authoritative for both `docs/reference/**` and the generated Wiki mirror; generated pages must not be edited by hand
- the docs workflow is repository tooling, not part of the Genia language/runtime semantics

## 0.3) `@doc` linter (`tools/lint_doc.py`)

Implemented today:

- deterministic linter for `@doc` content strings
- located at `tools/lint_doc.py`; tests at `tests/test_lint_doc.py`
- accepts a raw `@doc` text string via the `lint_doc()` API or CLI
- returns structured `LintFinding` values with `rule_id`, `severity`, `message`, and optional `line`
- CLI modes:
  - inline: `python tools/lint_doc.py "doc string"`
  - file: `python tools/lint_doc.py --file path.genia`
- directory scan: `python tools/lint_doc.py --scan-dir dir/`
  - all modes support `--json` for machine-readable output
- `--require-coverage` derives the public surface from registered prelude autoloads
  plus the canonical non-internal Python-host builtin registry
- DOC008 requires canonical documentation for every derived public binding;
  DOC009 requires its category; registry entries with `stability: "internal"`
  are excluded
- file/scan modes extract binding names and include them in output
- `--scan-dir` prints a summary (files scanned, doc count, error/warning counts) to stderr

Implemented lint rules (phase 1):

| Rule | ID | Severity | Description |
|---|---|---|---|
| Summary required | DOC001 | error | Every `@doc` must have a non-empty first line |
| Summary shape | DOC002 | warning | Summary should end with `.`/`!`/`?` and avoid boilerplate prefixes |
| Allowed sections | DOC003 | error | Only `## Arguments`, `## Returns`, `## Errors`, `## Notes`, `## Examples` |
| No HTML | DOC004 | error | Raw HTML tags forbidden outside fences |
| No tables | DOC005 | error | Pipe-table markdown forbidden outside fences |
| Behavior mention | DOC006 | warning | `none(`, `flow`, `lazy` should appear in prose, not only in fences |
| Fence sanity | DOC007 | error | Fences must be balanced; `## Examples` fences allow only `genia`, `text`, or empty lang |

Not implemented yet:

- semantic NLP scoring or readability metrics
- public/private marker enforcement (no such marker exists in the language yet)
- cross-reference validation between `@doc` content and function signatures

## 0.4) `@doc` style synchronization tests (`tests/test_doc_style_sync.py`)

Implemented today:

- style guide structure test: validates `docs/style/doc-style.md` has required sections, good/bad examples, and well-formed genia fences
- cheatsheet sync test: validates `docs/cheatsheet/core.md` and `docs/cheatsheet/quick-reference.md` have `@doc Quick Reference` sections with case markers linking back to the style guide
- linter-style guide alignment test: validates that the linter's `ALLOWED_SECTION_HEADERS`, `DISCOURAGED_PREFIXES`, and disallowed Markdown match the style guide
- prelude doc lint sweep: scans all `src/genia/std/prelude/*.genia` files for `@doc` strings and runs the linter over them

Not implemented yet:

- CI-gate enforcement (tests exist but are not yet wired into a required CI check)
- runnable example execution within the style guide itself (cheatsheet sidecar tests cover runnable examples separately)

Clarifications:

- these are repository tooling tests, not part of the Genia language/runtime semantics
- the linter is repository tooling, not part of the Genia language/runtime semantics
- rules are intentionally conservative and deterministic

## 1) Execution model

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

- Document chunking with exact provenance (Experimental, R12 E12-1, issue #643)
  - `chunk(chunker, document)` is an ordinary portable call over existing values, callables, R9 representation, and Outcomes; it adds no capability, syntax, annotation, parser/AST/Core IR/lifecycle behavior, or second pipeline
  - `document` is the exact closed map `{id: nonempty string, text: string, meta: json_represented_object}`; metadata is an ordinary existing R9 JSON-domain map beneath exactly one outer `json` representation
  - `chunker` is invoked exactly once with `document.text` and must return a list of exact closed `{offset, length}` maps; offsets are nonnegative integers, lengths are positive integers, and booleans are not integers
  - offsets and lengths count Unicode code points; each span must lie wholly within the original text, returned order is preserved, and overlapping/repeated spans are allowed
  - `chunk/2` alone constructs exact closed chunks `{text, source, meta}` from the original document; source is `{doc_id, offset, length}`, text is the exact original slice, and every chunk retains the exact represented metadata value without merge, augmentation, unwrap, or rewrap
  - valid empty span lists return `some([])`, including for nonempty documents; an empty document can produce only an empty valid span list
  - the first malformed or out-of-bounds span returns `err("chunk-invalid", {stage: quote(span), index})`; malformed document/non-callable chunker and callback exception/non-list result are runtime misuse
  - shared eval/error/Flow specs plus Python tests cover closed validation, exact construction, Unicode slicing, ordering/overlap/repetition, zero results, metadata identity, callback count, and misuse; existing parse/Core IR coverage confirms an ordinary call
  - LANGUAGE CONTRACT: the closed values, one-call callback boundary, code-point slicing, exact provenance, metadata preservation, and Outcome/misuse behavior above are the implemented portable E12-1 boundary
  - PYTHON REFERENCE HOST: the portable boundary is implemented locally with no host capability or provider attempt; shared/multi-host conformance remains Partial and no non-Python host is implemented
  - indexing, retrieval, and provider-backed reranking are implemented separately by E12-3/E12-4/E12-5; grounding, model changes, and citation rendering remain later R12 work

- Unified corpus/query embedding fixture (Experimental, R12 E12-2, issue #644)
  - `embed(provider, config, credential, authority)` validates and captures one explicit opaque embed capability, exact closed `{id, space, timeout_ms}` config, one R10 protected credential, and one declassification authority, then returns an ordinary one-argument callable without declassification, audit, or provider attempt
  - config `id` and `space` are nonempty strings; `timeout_ms` is an integer in `1..300000` excluding booleans; missing/extra keys are runtime misuse
  - the callable accepts exactly `{kind: quote(chunk), chunk}` or `{kind: quote(query), text}`; query text is nonempty, a chunk is the exact E12-1 closed value, and protected ordinary input fields are runtime misuse
  - malformed nested chunk input returns `err("chunk-invalid", {stage: quote(document)})` before declassification or attempt; other locally detectable invalid inputs are runtime misuse and likewise make no attempt
  - a valid invocation declassifies the protected string credential just in time through the exact R10 `quote(embed_call)` authority and makes one synchronous deterministic fixture attempt under the configured finite timeout; there is no retry, fallback, batching contract, stream, cache, background work, clock, randomness, environment, filesystem, sleep, or network dependency
  - success is exactly `some({chunk: exact_input_chunk, embedding})` or `some({text: exact_input_text, embedding})` according to the input variant; queries never fabricate provenance and provider output cannot replace application-owned chunk/text identity
  - `embedding` is exactly `{vector, dims, space}`; vector is a nonempty list of finite numbers excluding booleans, dims is a positive integer excluding booleans equal to exact vector length, and space exactly equals the constructor config space
  - invalid successful provider values normalize to `err("embed-response-invalid", {stage})` with stage `provider_response|vector|dims|space|input_identity`; approved timeout/rate-limit/rejection/transport errors retain the exact R12 contexts, and provider exceptions normalize once to non-sensitive `embed-transport-failure/{kind: quote(other)}`
  - no result or diagnostic retains credentials, config id/space, provider identity, bodies, exception text, headers, or request identifiers; the fixture capability renders as `<embed-provider>` and is never ambient or source-constructible
  - LANGUAGE CONTRACT: the exact ordinary input/output variants, identity, vector/dimension/space validation, Outcome normalization, local-validation ordering, and one-attempt/no-retry boundary are portable E12-2 obligations
  - PYTHON REFERENCE HOST: one explicitly injected opaque deterministic offline fixture proves the boundary and attempt/audit instrumentation; shared/multi-host conformance remains Partial and no non-Python host or network embedding adapter is implemented
  - indexing, explicit retrieval, and provider-backed reranking are implemented separately by E12-3/E12-4/E12-5; grounding/model invocation, persistence/vector databases, implicit query embedding, and provider registries remain unimplemented R12 work

- Indexing capability and opaque handle (Experimental, R12 E12-3, issue #645)
  - `index(provider, config, credential, authority)` validates and captures one explicit opaque index capability, exact closed `{id, timeout_ms}` config, one R10 protected credential, and one authority, then returns an ordinary one-argument callable without declassification, audit, or attempt
  - the callable requires a nonempty list of exact E12 embedded chunks; empty input is runtime misuse, malformed chunks/embeddings fail locally, and all vectors must have exact-equal positive `dims` and nonempty `space`
  - mixed dimensions return `err("index-embedding-incompatible", {kind: quote(dimension)})`; mixed spaces return the same reason with `quote(space)`; validation and compatibility checks precede declassification and make zero attempts
  - a valid invocation declassifies the protected string just in time through exact R10 `quote(index_call)` authority and makes one synchronous deterministic fixture attempt with no retry, fallback, stream, cache, background work, networking, or portable batching behavior
  - success returns only `some(index_handle)`; the host-produced handle retains private compatibility identity plus corpus space/dims, renders exactly `<index-handle>`, and cannot be source-constructed, inspected, compared, hashed/keyed, copied, serialized, or persisted
  - approved timeout/rate-limit/rejection/transport observations retain exact R12 contexts; malformed observations normalize to non-sensitive `index-response-invalid`, and provider exceptions normalize once to `index-transport-failure/{kind: quote(other)}`
  - LANGUAGE CONTRACT: exact config/input validation, compatibility ordering, one-attempt Outcome normalization, fixed opacity/rendering, and private compatibility obligations are portable E12-3 behavior
  - PYTHON REFERENCE HOST: one explicitly injected deterministic offline in-memory fixture proves the capability/handle boundary; shared/multi-host conformance remains Partial and no non-Python host, network index adapter, or public storage object is implemented
  - retrieval and provider-backed reranking are implemented separately by E12-4/E12-5; grounding/model invocation, persistence/vector databases, public handle inspection, and provider registries remain unimplemented R12 work

- Retrieval capability and compatibility guards (Experimental, R12 E12-4, issue #646)
  - `retrieve(provider, config, credential, authority)` validates and captures one explicit opaque retrieval capability, exact closed `{id, timeout_ms}` config, one R10 protected credential, and one authority, then returns an ordinary three-argument callable without declassification, audit, or attempt
  - the callable requires one host-produced E12-3 index handle, one exact explicit E12-2 query embedding, and non-boolean integer `k` in `1..1000`; malformed top-level values are runtime misuse and query embedding is never implicit
  - local compatibility checks run in exact handle/capability identity, embedding space, then embedding dimension order; mismatches return `retrieve-capability-incompatible/{kind: quote(index_handle)}` or `retrieve-embedding-incompatible/{kind: quote(space)|quote(dimension)}` before declassification and make zero attempts
  - a valid invocation declassifies the protected string just in time through exact R10 `quote(retrieve_call)` authority and makes one synchronous deterministic fixture attempt with no retry, fallback, stream, cache, background work, networking, or hidden query embedding
  - nonempty success returns `some([retrieved_chunk, ...])` with at most `k` exact indexed chunks, finite opaque backend-native scores, and provider best-first order; valid empty success returns exact `none("retrieval-no-results")`
  - result validation rejects malformed/over-limit/non-finite/untraceable observations with exact non-sensitive `retrieve-response-invalid` stages; approved timeout/rate-limit/rejection/transport observations retain exact R12 contexts and provider exceptions normalize once to `retrieve-transport-failure/{kind: quote(other)}`
  - the paired index/retrieve capabilities share one private compatibility identity; the opaque handle privately retains corpus space/dims, backend reference, and exact indexed chunk occurrences needed for provenance validation, none of which becomes source-visible
  - LANGUAGE CONTRACT: exact config/input/`k` validation, identity-space-dimension ordering, one-attempt Outcome normalization, ordered bounded evidence, exact indexed provenance, empty-result absence, and private compatibility obligations are portable E12-4 behavior
  - PYTHON REFERENCE HOST: one explicitly paired deterministic offline in-memory fixture proves capability/handle compatibility, attempts, audits, and provenance; shared/multi-host conformance remains Partial and no non-Python host, network retrieval adapter, vector database, or public storage API is implemented
  - provider-backed reranking is implemented separately by E12-5; grounding/model invocation, persistence/vector databases, implicit query embedding, provider registries, score normalization/thresholds, and citation rendering remain unimplemented R12 work

- Provider reranking and provenance integrity (Experimental, R12 E12-5, issue #647)
  - `rerank(provider, config, credential, authority)` validates and captures one explicit opaque rerank capability, exact closed `{id, timeout_ms}` config, one R10 protected credential, and one authority, then returns an ordinary two-argument callable without declassification, audit, or attempt
  - the callable requires a nonempty query string and a list of exact E12 retrieved chunks; malformed/protected input is runtime misuse and local validation precedes declassification
  - valid empty evidence returns `some([])` with zero declassification/audit/attempt; nonempty evidence declassifies just in time through exact `quote(rerank_call)` authority and makes one synchronous deterministic fixture attempt without retry, fallback, stream, cache, background work, or networking
  - success may reorder occurrences and replace scores with finite reranker-native numbers only; it preserves the exact multiset of exact chunk values, including repeated occurrences, and therefore cannot add, drop, duplicate, replace, or mutate text/source/represented metadata provenance
  - malformed/non-preserving success returns exact non-sensitive `rerank-response-invalid/{stage: quote(result)}`; malformed observations use `quote(provider_response)`, approved rerank timeout/rate-limit/rejection/transport contexts pass through, and provider exceptions normalize once to `rerank-transport-failure/{kind: quote(other)}`
  - LANGUAGE CONTRACT: exact config/input validation, inert construction/empty short path, one-attempt Outcome normalization, finite-score replacement, authoritative output order, and exact evidence-multiset/provenance preservation are portable E12-5 obligations
  - PYTHON REFERENCE HOST: one explicitly injected deterministic offline fixture proves attempts, audits, duplicate-aware integrity, and non-leakage; shared/multi-host conformance remains Partial and no non-Python host or network rerank adapter is implemented
  - pure local rerankers remain ordinary application/library functions under other explicit names; score normalization/comparability, grounding/model invocation, citation rendering, persistence/vector databases, and provider registries remain unimplemented

- Grounded context and answer composition (Experimental, R12 E12-6, issue #648)
  - the importable `examples/r12_grounded_context_answer.genia` module defines application-owned `assemble_grounded_context/3`, `assemble_grounded_answer/2`, `grounded_request/1`, and `generate_grounded_answer/2`; these are ordinary composition functions, not new public builtins or provider boundaries
  - grounded context is the exact closed `{question, content, evidence}` shape with a nonempty unprotected question, exact R11 text/JSON content, and a list of exact finite-scored E12 retrieved chunks; assembly validates locally and makes zero provider/model attempts
  - grounded answer is the exact closed `{answer, sources, evidence}` shape; it is assembled only from an exact successful R11 `some(response)`, retains the exact context evidence list/order, and takes answer content only from `response.message.content`
  - `sources` traverses evidence in order and retains the first occurrence of each exact-equal closed `{doc_id, offset, length}` source; later exact duplicates are removed, while different spans from the same document remain distinct
  - `none(...)` and `err(...)` model Outcomes propagate unchanged and produce no grounded answer; the application-owned generation wrapper validates the exact context, constructs one existing R11 text request, and invokes its supplied unchanged model callable once
  - LANGUAGE CONTRACT: exact closed shapes, local validation, zero-attempt assembly, exact evidence preservation, ordered first-occurrence source deduplication, successful-Outcome-only answer assembly, and unchanged R11 `model/4` composition are portable E12-6 obligations
  - PYTHON REFERENCE HOST: private validation bridges and deterministic tests prove the ordinary application module; shared/multi-host conformance remains Partial and no non-Python host grounding proof is implemented
  - R12 standardizes provenance/evidence substrate only; citation labels, numbering, generated-prose citation spans/validation/rendering, prompt runtime, RAG framework objects, agents/tools/memory, and retry remain unimplemented

- R12 cross-mode hardening and grounded proving case (Experimental, R12 E12-7, issue #649)
  - existing E12-1 through E12-6 and unchanged R11 `model/4` boundaries are proved through explicit deterministic shared eval/Flow/error/CLI fixtures plus existing parse/Core IR forms; E12-7 adds no public function, provider semantic, syntax, or Core IR node
  - `embed_call`, `index_call`, `retrieve_call`, `rerank_call`, and `model_call` use distinct protected credentials and exact matching R10 authorities; constructors remain inert, local checks precede just-in-time declassification, and each consumed valid stage makes at most one synchronous attempt without retry, fallback, sleep, queue, race, or background work
  - bounded downstream Flow consumption is demand-driven and makes no attempt for unconsumed items; deterministic fixtures use no network, clock, randomness, environment, filesystem, or sleep
  - paired in-memory index/retrieve compatibility remains private; compatible injected capabilities keep the same ordinary call/value contracts without promising identical vectors, scores, evidence order, or answers
  - recursive tests scan results, Outcomes, rendering, audits, provider observations, buffers, resources, stdout/stderr, and test output for credential/payload sentinels
  - `examples/r12_cross_mode_grounded_proving.genia` explicitly composes validation/diagnostics, chunking, corpus/query embedding, indexing, retrieval, provider reranking, grounded context, one unchanged R11 model call, and grounded answer while retaining exact provenance
  - LANGUAGE CONTRACT: E12-7 adds cross-mode conformance evidence and an ordinary composition proof for existing R10/R11/R12 obligations only; it adds no new behavior
  - PYTHON REFERENCE HOST: the explicit offline fixture runner and instrumentation are host proof mechanics, not portable APIs; shared/multi-host conformance remains Partial and no non-Python host is implemented

- R12 release examples and implemented-truth synchronization (Experimental, R12 E12-8, issue #650)
  - E12-8 adds no runtime behavior: `docs/releases/R12.md` and focused documentation tests synchronize runnable chunking and complete grounded-composition examples with the implemented E12-1 through E12-7 boundary
  - the synchronized public account keeps ordinary values/callables/Outcomes, exact provenance, explicit query embedding, opaque index/retrieval compatibility, backend-native scores, unchanged R11 `model/4`, Python-host-only proof mechanics, and excluded citation rendering distinct
  - LANGUAGE CONTRACT: E12-8 is documentation and executable-example verification only; the implemented portable behavior remains exactly E12-1 through E12-6, while E12-7 remains conformance/proving evidence without new semantics
  - E12-9 adds no runtime behavior: its release-wide truth audit verifies the approved boundary, focused/shared/native/documentation/full-suite evidence, protected-provider exclusions, and canonical release status
  - R12 is release-complete through E12-9 while its APIs remain Experimental, shared/multi-host conformance remains Partial, and Python remains the only implemented host

- AI model invocation, Flow conversation composition, validated-pipeline proof, release-example truth sync, and release truth audit (Experimental, R11 E11-1 through E11-8, issues #611-#618)
  - `model(provider, config, credential, authority)` is the sole public AI entry point and returns an ordinary one-argument callable
  - E11-3 adds one explicit Python-host-only Google Gemini Developer API adapter using direct `v1beta models.generateContent` REST; the deterministic fixture remains the portable-observation test path
  - `provider` is an opaque host-injected model-provider capability; ordinary source has no constructor and execution modes inject no ambient provider, credential, or authority
  - `config` is the closed map `{id: nonempty string, timeout_ms: integer 1..300000}`
  - a request is the closed map `{messages, output}` with a nonempty message list, closed text messages using `system|user|assistant` roles, and `{kind: quote(text)}` output
  - E11-2 also accepts the closed output requirement `{kind: quote(json), schema, template}`: `schema` has exactly one outer R9 `json` representation and must be accepted by existing `json_schema`; `template` is an explicit callable one-argument Outcome Template
  - construction validates its inputs without declassification, audit, or provider attempt; invocation validates the complete request before declassification or attempt
  - a valid invocation declassifies the R10 protected string credential at the authorized boundary, records the existing R10 audit, and makes exactly one synchronous provider attempt; there is no implicit retry
  - the Gemini host adapter maps `config.id` to the percent-encoded model path, `config.timeout_ms` to the one standard-library HTTPS attempt, and the declassified credential only to `x-goog-api-key`; it refuses redirects and exposes no provider factory to source, ambient binding, SDK dependency, general HTTP API, discovery, retry, or fallback
  - Gemini user/assistant messages map to `user`/`model` contents, system text maps in relative order to `systemInstruction.parts`, and structured output sends the existing represented schema as `responseJsonSchema` with `application/json`
  - success is `some({message, finish_reason, usage})`; the response is closed, its message is assistant text, finish reason is `stop|length|filtered|other`, and usage is exact nonnegative token counts or `none("model-usage-unavailable")`
  - structured success processes the single provider assistant text through existing `json_decode`, invokes the explicit Template once on the decoded carried ordinary value, ignores the Template success payload, and returns assistant content `{kind: quote(json), value: represented_value}` retaining exactly one outer `json` facet
  - decode or Template `none(...)`/`err(...)` becomes exactly `err("model-structured-output-invalid", {stage: quote(json_decode)|quote(template), outcome: original_outcome})`; a non-Outcome Template result is runtime callback misuse
  - there is no repair, trimming, prose/fence extraction, coercion, second parse, reprompt, partial acceptance, or retry
  - absence is exactly `none("model-no-response")`; normalized failures use `model-timeout`, `model-rate-limited`, `model-rejected`, `model-transport-failure`, or `model-response-invalid` with the closed contexts defined in `GENIA_RULES.md`
  - malformed provider observations become `err("model-response-invalid", {stage: quote(provider_response)})` (or the precise response stage); Gemini HTTP/transport failures normalize to the existing timeout/rate-limit/rejected/transport Outcomes without retaining raw bodies, headers other than parsed retry delay, request IDs, exception text, keys, or credentials
  - shared eval/error/Flow/CLI specs opt into the Python fixture explicitly with `fixtures: [r11_model]`; CLI fixture routing is private shared-spec harness behavior for command/file/pipe observations, while ordinary eval, file, command, pipe, import, native-test, and serve execution gain no fixture bindings
  - parse and Core IR shared specs retain the existing ordinary `Call`/`IrCall` shapes; E11-4 adds no syntax, node, execution mode, flag, annotation, lifecycle consumer, ambient capability, or retry/tool/streaming surface
  - E11-5 implements conversation as application-owned ordinary state evolution through existing `scan(step, initial_state, source)`: input is exactly `{kind: quote(message), message: {role: quote(user), content}}` or `{kind: quote(stop), reason: string}`; initial state is exactly `{messages: [], turn: 0, status: quote(active), last: none("conversation-not-started")}`
  - the application-defined step returns `[next_state, next_state]`; an active message appends the user message, calls an ordinary prompt over the full ordered history, calls the model once, increments `turn`, records the exact Outcome, and appends one assistant message only for `some(response)`; `none`/`err` sets failed status without an assistant append
  - active stop preserves history/turn, records stopped status plus `none("conversation-stopped", {reason})`, and makes no model call; stopped/failed states return unchanged for later input with no call
  - list input returns an eager state list and Flow input returns a lazy single-use Flow with equivalent consumed states; `scan` emits no initial state, and source completion or existing downstream bounds terminate consumption without a new Flow helper
  - `examples/r11_flow_conversation.genia` is the executable application composition proof; it uses existing `apply_raw` only to deliberately dispatch model Outcomes as data rather than triggering ordinary Option short-circuiting
  - conversation owns neither input acquisition nor model/provider configuration and adds no runtime object, hidden memory, retry/reprompt/tool loop, streaming, cancellation, `take_while`, syntax, annotation, or Core IR node
  - `examples/r11_validated_pipeline_proving_case.genia` is the executable E11-6 proof: mixed JSONL uses existing parsing and record validation before an ordinary structured model stage; R9 `json_schema`/represented output, explicit R10 protected credentials, and existing `validate_each`/`collect_validated` produce clean represented values plus ordered diagnostics
  - the deterministic proof attempts the model only for parse/validation successes, at most once per invocation; no-response, normalized provider failures, invalid structured output, Template mismatch, and protected-boundary failure use existing Outcomes/errors without retry, repair, reprompt, fallback, or sensitive leakage
  - E11-6 adds no helper, schema/validation system, provider behavior, syntax, annotation, or Core IR node; its shared CLI/eval/Flow/error cases and native/Python tests are conformance/proving artifacts over existing behavior
  - E11-7 adds no runtime behavior: `docs/releases/R11.md` and focused documentation tests synchronize runnable text, structured-output, Flow-conversation, and validated-pipeline examples with the implemented boundary and keep maturity, portability, and exclusions explicit
  - E11-8 adds no runtime behavior: its release-wide truth audit verifies the approved boundary, focused/shared/native/documentation/full-suite evidence, sensitive-data exclusions, and canonical release status; R11 is release-complete while its APIs remain Experimental, Python remains the only implemented host, and shared/multi-host conformance remains Partial
  - LANGUAGE CONTRACT: the ordinary closed value shapes, callable behavior, validation ordering, one-attempt rule, R9 structured composition, normalized Outcomes, explicit cross-mode boundary, application-owned list/Flow `scan` composition, and Outcome-aware validated-pipeline composition are the implemented R11 E11-1 through E11-8 portable boundary; E11-7 is documentation/executable-example verification and E11-8 is audit/distillation only
  - PYTHON REFERENCE HOST: the offline deterministic fixture and one explicitly constructed Gemini REST capability are implemented; automated adapter tests inject a fake transport and perform no network access; shared/multi-host conformance remains Partial

- Configuration provider, protected acquisition/sinks, explicit declassification, cross-mode hardening, and composed validated-pipeline proving case (Experimental, issues #589-#595)
  - R10 E10-1 through E10-8 are release-complete; completion records the delivered and audited scope, while the APIs remain Experimental and shared/multi-host conformance remains Partial
  - `config_provider(sources)` constructs an explicit opaque immutable provider snapshot and returns `some(provider)` or a normalized `err(...)`
  - supported descriptors are `{kind: quote(values), values: map}` and capability-backed `{kind: quote(environment)}`
  - source order is highest to lowest precedence; the first source containing a key wins
  - all descriptors and literal string keys/values are validated before any host-backed snapshot is acquired
  - `config_get(provider, key)` returns `some(exact_string)`, including `some("")`, or context-free `none("config-missing")`
  - `config_get_or(provider, key, default)` preserves found values including empty; only `none("config-missing")` invokes the zero-argument default, exactly once
  - an ordinary default result is wrapped in `some(...)`; a default `some(...)`, `none(...)`, or `err(...)` is preserved without nesting
  - default callability/arity is checked only if missing selects the default branch; other lookup Outcomes bypass the default unchanged
  - conversion remains an explicit ordinary Outcome-returning callable, and validation reuses existing callable Templates through ordinary Outcome-aware pipelines
  - `secret_get(provider, key, purpose)` protects found exact strings, including empty, in one reserved outer `secret` carrier; purpose is a non-empty symbol
  - `secret_get_or(provider, key, purpose, default)` uses the same missing-only, exactly-once default rule; ordinary/`some` successes are protected once and `none`/`err` are preserved
  - `protected_match("secret", value)` returns `some(value)` containing the exact protected subject; ordinary/non-secret values return `none("representation-mismatch")`
  - generic `represent`, `representation_match`, and `strip_representation` reject the reserved `secret` facet
  - protected equality includes provider identity, purpose, and carried-value equality without exposing them; protected values are not map keys
  - calls, returns, containers, pipelines, Seq, Flow, Sheet cells, refs, and process messages transport exact protected leaves; containers gain no hidden taint and unsupported ordinary derivation returns existing type failure
  - diagnostic rendering recursively substitutes `<protected>`; Format replacements, output sinks, JSON, Sheet CSV, resource writes, HTTP responses, and ordinary host conversion reject protected leaves before effects
  - `json_encode` returns `err("protected-value", {operation: "json-encode"})`; resource rejection writes zero payload bytes
  - `declassify(authority, protected_value)` is the sole payload-revealing operation; a host-injected opaque authority must match the exact provider identity and allow the protected purpose
  - successful declassification removes exactly one protected layer, returns an ordinary untainted value, and records a host-local non-sensitive audit event; mismatches reveal nothing and audit failure fails closed
  - authority displays as `<declassification-authority>`, cannot be copied or used as a map key, and is rejected by output/format/serialization/Sheet/resource/HTTP/process/ordinary-host boundaries
  - valid keys are non-empty strings without NUL; normalized diagnostics never include the key, source contents, raw value, or host exception detail
  - providers display/debug as `<config-provider>`, compare by identity, are not map keys, and are rejected by ordinary host conversion and JSON serialization
  - construction copies every source once; later literal/environment mutation is invisible and lookup performs no host access
  - ordinary eval, file, command, pipe, import, native-test, and serve-entry evaluation preserve these explicit provider/protection semantics; modes create no ambient provider or authority
  - imports acquire only when evaluated module code explicitly constructs and uses a provider; existing annotations do not acquire or inject configuration
  - the Python native-test harness accepts explicit fixture bindings and environment-capability/output test seams; it constructs no fixture provider or authority implicitly
  - serve entry evaluation and any explicit provider snapshot complete before listener activation; requests do not refresh configuration automatically
  - `examples/r10_validated_pipeline_proving_case.genia` is the executable E10-7 composition proof: explicit ordinary configuration flows through `parse_int` and callable Templates, protected acquisition/matching remains opaque, and existing `validate_each`/`collect_validated` produce clean records plus diagnostics
  - shared CLI and native Genia coverage prove the source-visible composition; Python reference-host tests inject the matching authority and fixture host callable, prove declassification immediately at that boundary, and cover mismatch, protected-sink, provider-failure, audit, and sentinel non-leak behavior
  - no ambient provider, implicit environment fallback, refresh, implicit conversion/coercion, new validation system, annotation injection, parser, or Core IR change is implemented
  - LANGUAGE CONTRACT: explicit ordering, immutable snapshot semantics, literal sources, lookup Outcomes, opacity, and normalized failures are portable
  - PYTHON REFERENCE HOST: `{kind: quote(environment)}` snapshots `os.environ` during construction; a host may report the capability unavailable rather than substitute another source

- Qualified configuration and secret views (Experimental, issue #671)
  - R13 E13-1 adds `config_view(provider, prefix)` and `secret_view(provider, prefix, purpose)` as ordinary constructors returning one-argument callables
  - construction validates and captures the existing R10 provider and exact string prefix; secret views also validate and capture one existing non-empty R10 purpose symbol
  - an empty prefix is valid; a prefix containing NUL is runtime misuse; construction performs no lookup, source acquisition, refresh, conversion, validation, protection, declassification, audit, or host operation
  - each returned callable requires one non-empty logical-name string without NUL, forms the physical key by exact `prefix + logical_name` concatenation, and performs exactly one existing R10 lookup
  - `config_view` returns the exact `config_get` Outcome; `secret_view` returns the exact `secret_get` Outcome and preserves provider identity, purpose, protected carrier, sinks, authority, audit, and declassification behavior
  - views add no caching, fallback, precedence, defaulting, conversion, Template validation, ambient lookup, named access, syntax, annotation, parser/AST/Core IR node, lifecycle binding, or host capability
  - normalized misuse does not include the prefix, logical name, physical key, provider identity, purpose, source content/value, or protected payload
  - E13-1 itself adds no conventional provider composition; E13-4 supplies that composition, E13-5 verifies the complete implemented boundary across relevant modes, and E13-6 proves its validated-pipeline composition; release-completion slices remain unimplemented
  - LANGUAGE CONTRACT: construction/callability, validation, exact concatenation, and exact one-call R10 delegation are portable ordinary-call behavior
  - PYTHON REFERENCE HOST: the two constructors use the existing callable and R10 provider implementation; no new host capability is introduced and shared/multi-host conformance remains Partial

- Explicit CLI configuration source (Experimental, issue #672)
  - R13 E13-2 adds `config_args(args)` as an ordinary one-argument callable over an explicit plain list of strings, normally `argv()`; it never reads process arguments or interpreter mode flags itself
  - before the first standalone `--`, input is exact long-option/value pairs; names use ASCII letter-led alphanumeric segments separated by single hyphens, and values are the next exact strings, including empty or option-looking strings
  - standalone `--` terminates configuration parsing and every later string is ignored; empty and terminator-only input produce an empty values map
  - names normalize by replacing hyphens with underscores and uppercasing ASCII letters; unknown valid names are accepted, while repeated or normalization-colliding keys fail atomically
  - success is `some({kind: quote(values), values: normalized_map})`, using the existing R10 literal source descriptor shape and fresh snapshot data
  - malformed string-list data returns exactly `err("config-source-invalid", {source_kind: quote(arguments), stage: quote(parse)})`; no option spelling, argument index, value, or partial map is exposed
  - a non-list input or any non-string list member is runtime misuse; short/grouped options, flags without values, `--name=value`, underscores, non-ASCII names, and positionals before `--` are not accepted
  - E13-2 adds no schema, boolean encoding, conversion, provider construction, host acquisition capability, syntax, annotation, parser/AST/Core IR node, named access, lifecycle binding, or ambient lookup
  - LANGUAGE CONTRACT: explicit-input grammar, normalization, collision handling, descriptor/Outcome shapes, atomic failure, and snapshot behavior are portable pure ordinary-call behavior
  - PYTHON REFERENCE HOST: the ordinary callable is registered over existing runtime values; raw process arguments remain available only through the unchanged explicit `argv()` boundary and shared/multi-host conformance remains Partial

- Narrow `.env` configuration source (Experimental, issue #673)
  - R13 E13-3 adds `{kind: quote(dotenv), path, required}` as an R10-compatible descriptor; `path` is a non-empty NUL-free string and `required` is boolean, with descriptor misuse rejected before any host acquisition
  - provider construction validates every descriptor first, then reads each `.env` path at most once in source-list order and copies parsed exact strings into the existing immutable provider snapshot; lookup never reads or refreshes the file
  - optional absence contributes an empty source at its fixed index; required absence and host read failure return `config-provider-failure`, unavailable capability returns `config-source-unavailable`, and invalid UTF-8/grammar returns `config-source-invalid`
  - `.env` failure context contains only `source_index`, `source_kind: quote(dotenv)`, and `stage: quote(acquire|decode|parse)`; paths, keys, values, content, partial providers, and raw host details do not escape
  - UTF-8 accepts one leading BOM, LF/CRLF, a final unterminated line, blank/full-comment lines, ASCII space/tab around entries, ASCII identifier keys, exact duplicate rejection, and unquoted/single-quoted/double-quoted values with only `\\`, `\"`, `\n`, `\r`, and `\t` double-quote escapes
  - empty values are present exact strings; interpolation, expansion, command substitution, multiline values, `export`, continuation, discovery, profiles/cascades, other formats, and watch/refresh are not implemented
  - existing source precedence and R10 `config_get`/`secret_get` Outcomes, protected carriers, sinks, authority, audit, and declassification remain unchanged
  - E13-3 adds no `config_standard`, conventional precedence helper, public parser, syntax, annotation, parser/AST/Core IR node, named access, lifecycle binding, or ambient lookup
  - LANGUAGE CONTRACT: descriptor validation, grammar, normalized Outcomes, fixed indices, acquisition ordering, and immutable snapshot behavior are portable
  - PYTHON REFERENCE HOST: `config.dotenv-snapshot` reads bytes from exactly the supplied path during provider construction; future hosts may report capability unavailable, and shared/multi-host conformance remains Partial

- Conventional configuration provider composition (Experimental, issue #674)
  - R13 E13-4 adds ordinary `config_standard(overrides, args)` and `config_standard(overrides, args, dotenv_path)` calls
  - the two-argument form selects optional `.env`; the three-argument form requires the exact supplied non-empty NUL-free path
  - construction normalizes explicit arguments, then delegates to the existing provider with fixed sources: overrides at index 0, arguments at 1, environment at 2, and `.env` at 3
  - fixed precedence is overrides > arguments > environment > `.env`; empty or optionally absent sources retain their indices
  - invalid explicit types/values are runtime misuse before acquisition; malformed argument syntax returns its exact non-sensitive `config-source-invalid` Outcome before environment or filesystem acquisition
  - the result is the exact existing provider Outcome; construction is atomic, snapshots once, and preserves unchanged ordinary/secret views and every R10 protected boundary
  - E13-4 adds no provider model, capability, ambient lookup/refresh, defaults source, schema/conversion, syntax, annotation, parser/AST/Core IR node, named access, or lifecycle binding
  - LANGUAGE CONTRACT: arities, validation ordering, fixed source order/indices, precedence, optional/required path policy, exact Outcomes, atomicity, and snapshot behavior are portable
  - PYTHON REFERENCE HOST: composition reuses the existing environment and `.env` snapshot capabilities; Python remains the only implemented host and shared/multi-host conformance remains Partial

- R13 cross-mode, diagnostic, and protected-boundary hardening (Experimental, issue #675)
  - E13-5 adds conformance proof only; it adds no public helper, value, error shape, source, capability, syntax, annotation, parser/AST/Core IR node, or execution-mode behavior
  - shared eval/error/CLI cases verify explicit standard-provider construction, exact existing Outcomes, non-sensitive malformed-argument failure, command-mode behavior, and existing ordinary parse/Core IR call forms
  - Python reference-host tests verify standard sources snapshot once before view use, imports acquire only through explicit module construction, serve snapshots precede activation and requests do not refresh, and malformed explicit data prevents later host acquisition
  - credentials acquired through standard composition and `secret_view` retain exact R10 provider identity, purpose, carrier, matching authority, audit-before-return, redaction, and protected-sink behavior; successful host-local audits retain their existing non-sensitive purpose field but no protected payload or raw host detail
  - focused sentinel scans cover normalized Outcomes, misuse diagnostics, protected rendering, and host audit observations; the existing R10 recursive sink/report/resource/HTTP/ordinary-host suites remain the protection authority and pass unchanged
  - file, command, pipe, import, native-test, and serve-entry behavior remains explicit and non-ambient; the E13-5 additions do not create a provider or authority fixture visible to ordinary source
  - Python remains the only implemented host and shared/multi-host conformance remains Partial; E13-7/E13-8 release-close slices add no runtime behavior

- R13 Outcome-aware validated-pipeline proving case (Experimental, issue #676)
  - `examples/r13_validated_pipeline_proving_case.genia` is the executable E13-6 application composition proof: one conventional provider feeds distinct server, database, and metrics qualified `PORT` views through explicit `parse_int` conversion and a callable Template, while existing `validate_each`/`collect_validated` produce clean records plus ordered structured diagnostics
  - deterministic overrides, explicit arguments, environment acquisition, and one explicit `.env` snapshot exercise the existing fixed standard-provider boundary; provider construction remains atomic and snapshot-based, identically named logical settings remain unambiguous through prefixes, and missing/malformed/Template-mismatched configuration preserves existing Outcomes
  - one protected credential remains opaque in public results and is declassified at most once only as an argument to an injected authorized outbound fixture; a matching authority produces one audit event and one outbound attempt, while provider/purpose mismatch, direct protected submission, and provider failure produce no outbound attempt and leak no key, payload, source value, or raw host detail
  - shared CLI/eval/Flow/error cases, one native Genia test, and focused Python reference-host tests prove the source-visible composition, normalized failure, sentinel non-leakage, and exact protected boundary offline
  - E13-6 adds no public helper, provider/source model, validation or diagnostic behavior, protected/declassification rule, network behavior, retry/fallback, syntax, annotation, parser/AST/Core IR node, ambient lookup, or lifecycle injection
  - LANGUAGE CONTRACT: explicit qualified lookup, Outcome propagation, callable Template validation, record collection, and protected transport compose using the already implemented R10/R13 portable ordinary-call boundary
  - PYTHON REFERENCE HOST: tests inject deterministic snapshot capabilities, one matching or mismatching authority, a non-sensitive audit observer, and an outbound fixture; Python remains the only implemented host and shared/multi-host conformance remains Partial

- R13 release examples, implemented-truth synchronization, and release audit (Experimental, R13 E13-7/E13-8, issues #677/#678)
  - E13-7 adds no runtime behavior: `docs/releases/R13.md` and focused documentation tests synchronize runnable qualified-view and complete validated-pipeline examples with the implemented E13-1 through E13-6 boundary
  - the synchronized public account keeps ordinary explicit providers, callables, Outcomes, immutable snapshots, fixed source precedence, explicit conversion/callable Template validation, R10 protected transport, and Python-host-only acquisition/test mechanics distinct
  - LANGUAGE CONTRACT: E13-7 is documentation and executable-example verification only; implemented portable behavior remains exactly E13-1 through E13-4, while E13-5/E13-6 remain conformance and application-composition proof without new semantics
  - E13-8 adds no runtime behavior: its release-wide truth audit verifies the approved boundary, focused/shared/native/documentation/full-suite evidence, protected-value exclusions, and canonical release status
  - R13 is release-complete through E13-8 while its APIs remain Experimental, shared/multi-host conformance remains Partial, and Python remains the only implemented host

- R14 lifecycle instance and parent/child execution scopes (Experimental, issue #621)
  - R14 E14-1 adds `lifecycle_scope(peers, work)`, `lifecycle_child(scope_handle, peers, work)`, and `lifecycle_context(scope_handle, name)` as the first implemented slice of the approved E14-0 composable-lifecycle contract (`docs/design/r14-composable-lifecycle-contract.md`)
  - a peer is an ordinary closed map `{name: symbol, enter: callable/1, exit: callable/2}`; peers on one scope operation enter in list order and unwind in strict reverse order, every entered peer's `exit` runs exactly once regardless of earlier exit failures, and the first non-cleanup failure is always the scope's one `primary_failure` while every later exit failure is preserved in `cleanup_failures`
  - `work`'s return value is carried into the closed `LifecycleResult` verbatim and is never inspected for `some`/`none`/`err`; the only way `work` produces a lifecycle failure is by raising, normalized exactly like R8 lifecycle exceptions
  - `lifecycle_child` may be called only synchronously from an active parent scope's own `work`; a child's result/failure is ordinary data returned to the parent and never implicitly raised into it, and a child's peers/resources are entirely separate from the parent's
  - `lifecycle_context` is inward-only and read-only: it checks the calling scope's own entered-peer context, then each ancestor scope in turn, and never exposes a later-attached peer's context to an earlier one; a peer name colliding with any name already exposed by an ancestor scope is rejected before any `enter` runs
  - a scope handle is valid only while its scope is `entering`/`active`/`exiting`; any later use (or `lifecycle_child` on a handle that is not `active`) raises a runtime-misuse `RuntimeError`, the same family as an already-consumed Flow
  - E14-1 adds no `lifecycle_repeat`, `lifecycle_config`, HTTP operation/client, peer-attachment ordering syntax, parser/AST/Core IR change, or ambient/global current-scope state; those remain later R14 tickets (#692-#630)
  - LANGUAGE CONTRACT: the six required default invariants (no global mutable current-scope switch; contained child failure; explicit child result/failure propagation; child-owned resource finalization inside one synchronous call; untouched parent-owned resources; inward-only non-shadowed context) are implemented exactly as locked by the E14-0 contract
  - PYTHON REFERENCE HOST: implemented in `src/genia/lifecycle_runtime.py` as ordinary calls over `values.py` types with no new host capability; validated by `tests/unit/test_lifecycle_runtime.py` (24 tests), Python reference host only; shared/multi-host conformance remains Partial

- Stdout / Stderr
  - `stdout` and `stderr` are first-class host-backed output sink values
  - they are opaque runtime capability values (`<stdout>`, `<stderr>`)
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

- literals: number, string (single/double quoted + triple-quoted multiline), boolean, `nil`, `none`
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

## 5) Case expressions and pattern matching

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
- Template metadata, positional/labeled shapes, and nominal Structs are not implemented by the Template/shape slices; the separate Experimental JSON Schema boundary below compiles only its locked structural subset

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

- implemented via pattern matching in function definitions and case expressions; lambdas may also pattern-match their single parameter arm
- no dedicated conditional keyword exists
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

### Response header composition (**Partial**, issue #526)

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

### CORS handler wrapper (**Partial**, issue #527)

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
- Field-path placeholder resolution (#290): a missing top-level or nested segment fails with `format missing field: <path>`; a non-map intermediate fails with `format expected a map while resolving placeholder path: <path>`; invalid path syntax (empty segment, leading/trailing/double dot, slash-separated paths, brackets, calls) fails with `format invalid placeholder`; slash (`/`) is not a field-path separator and must not be used in field-path placeholders.
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
- Examples:
  - `display("hello")` evaluates to the string `hello`
  - `debug_repr("hello")` evaluates to the string `"hello"`
  - `format("display={x} debug={x:?}", {x: "hello"})` evaluates to the string `display=hello debug="hello"`
  - `display(none("missing-key", {key: "name"}))` evaluates to the string `none("missing-key", {key: name})`
  - `debug_repr([some("x"), false])` evaluates to the string `[some("x"), false]`
  - `format_template(Format("{a} {b}"))` evaluates to the string `{a} {b}`
  - `format_template(Format("{{escaped}}"))` evaluates to the string `{{escaped}}`
  - `format_tag(Format("{name}", "person-card"))` evaluates to `some("person-card")`
  - `format_tag(Format("{name}"))` evaluates to `none("missing-format-tag")`
  - `format(Format("{name}", "person-card"), {name: "Ada"})` evaluates to the string `Ada`
  - `format(format_compose(["Hello, ", Format("{name}"), "!"]), {name: "Matt"})` evaluates to the string `Hello, Matt!`
  - `format(format_compose([]), {})` evaluates to the string `""`
  - `format(format_compose(["{x}", " / ", "{x}"]), {x: "go"})` evaluates to the string `go / go`
- Runtime capability values and function-like values may have host-specific opaque debug/display text in this phase unless a later contract explicitly stabilizes them.
- #185 does not define the full Representation System.
- #166 owns the broader representation model, including naming boundaries beyond `display` and `debug_repr`, extension points, user-defined representations, registry/strategy behavior, and cross-host treatment of opaque runtime values.
- #185 must not introduce alternate public representation terms such as `render`, `view`, or `repr`.
- If #166 later changes the canonical public names, #185 behavior must migrate through the alias-safe rename process: introduce alias, migrate usage incrementally, update tests, then remove the old name in a later phase.

### Sheet builtins (Experimental)

Sheet public helpers are registered directly as arity-specific `GeniaFunctionGroup` builtins in the global environment (not autoloaded). This allows coexistence with user-defined functions at other arities (for example, user-defined `rows/0` may coexist with `rows(sheet)`).

Public helpers:

- `sheet(columns)` — construct a Sheet from a list of `[name, values]` column pairs; column values must be lists; column names must be unique; all columns must have equal length
- `shape(sheet)` — return `[[rows, n], [columns, n]]`
- `columns(sheet)` — return column names in deterministic order
- `select(names, sheet)` — return a new Sheet with requested columns in requested order; rejects duplicate or missing names
- `where(predicate, sheet)` — return a new Sheet of rows where predicate returns `true`; predicate receives each row as a list of `[name, value]` pairs; predicate must return boolean
- `derive(name, function, sheet)` — return a new Sheet with a new column appended; row function receives each row as a list of `[name, value]` pairs; rejects existing column names
- `rows(sheet)` — return a list of rows, each row as a list of `[name, value]` pairs
- `row_get(row, column_name)` — return the value paired with `column_name` in a row (**Experimental**, issue #363); see below
- `collect_sheet(records)` — terminal, explicit conversion of a finite Seq-compatible source (list or Flow) of homogeneous map records into an immutable Sheet (**Experimental**, issue #395); see below
- `render_csv(sheet)` — return deterministic CSV report text for a Sheet (**Experimental**, issue #396); see below

All Sheet operations return new Sheet values. Existing Sheet values are never mutated.

`row_get(row, column_name)` (**Experimental**, issue #363):

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

`collect_sheet(records)` (**Experimental**, issue #395):

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

`render_csv(sheet)` (**Experimental**, issue #396):

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

### Host-backed persistent associative maps (Phase 1 bridge)

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
- `map_new` returns an empty map
- `map_put` and `map_remove` are persistent (return a new map, do not mutate input map)
- `map_get` returns stored value or `none("missing-key", {key: key})` when key is missing
- `map_has?` returns `true`/`false`
- `map_count` returns entry count
- `map_items` returns a list of `[key, value]` pairs in insertion order
- `map_item_key` extracts the key from a `[key, value]` pair produced by `map_items`
- `map_item_value` extracts the value from a `[key, value]` pair produced by `map_items`
- `map_keys` returns a list of all keys in insertion order
- `map_values` returns a list of all values in insertion order
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
- list keys are supported by stable structural key-freezing in runtime
- tuple keys are supported by the same runtime key-freezing strategy (runtime-level interop values)
- invalid map arguments and unsupported key types raise clear `TypeError`

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

### Field/index validation diagnostic helpers (**Experimental**, issue #393 contract)

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

### validate_record helper (**Experimental**, issue #391)

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

### collect_validated helper (**Experimental**, issue #383)

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
- does not create Sheets itself; pass `clean` to `collect_sheet(records)` (Experimental, issue #395) for an explicit, separate conversion to Sheet — `collect_validated` and `collect_sheet` remain two distinct terminal steps, not merged
- does not change Outcome semantics, pipeline short-circuit behavior, `keep_some`, or existing validation helpers
- `collect_validated` is terminal: it consumes the entire finite source to produce complete output; infinite Flow sources must be bounded before calling `collect_validated`
- error shared specs cover wrong arity (0 args, 2 args), non-Seq source, and non-Outcome item cases
- eval shared specs cover empty source, all clean, mixed `some`/`none`/`err`, `some` context ignored, bare `none`, `err` without context, and Flow-compatible source

### validate_each helper (**Experimental**, issue #392, issue #415, issue #416)

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
- portable JSON-domain limits are: string object names, no duplicate object names, safe integers in `[-9007199254740991, 9007199254740991]`, finite binary64 fractional/exponent numbers, Unicode scalar strings/names, and at most 128 nested object/array containers
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
- `parse_csv_row` (**Experimental**, issue #390) parses one CSV row string and returns an Outcome with stable context metadata:
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

LANGUAGE CONTRACT:
- Native test kernel core provides normalized pass/fail/error result dictionaries and suite dictionaries.
- It normalizes `TestUnit` execution into one of three stable result kinds: `pass`, `fail`, or `error`.
- It aggregates suite results and maps suite results to kernel-level exit codes.
- `TestResult` is distinct from Outcome (`some`/`none`/`err`); there is no automatic mapping between them.
- Exit code `0` means all executed tests passed or the suite was empty; exit code `1` means at least one test failed or errored.
- Native test metadata keys and values must be strings. Non-string metadata is reported as a deterministic discovery error before test body execution. Diagnostics use deterministic Genia runtime type names and include existing `TestUnit.location` when available.

PYTHON REFERENCE HOST:
- Implemented as `src/genia/test_kernel.py` in the Python reference host.
- Provides: `NativeTestFailure`, `TestUnit`, `run_test_unit`, `run_test_suite`, `aggregate_results`, `suite_exit_code`.
- `TestUnit` is a frozen dataclass with `name` (required non-empty string), `body` (required callable), and optional `location` and `metadata`. When `metadata` is present, all keys and values must be strings; non-string metadata is a discovery error.
- `run_test_unit(test_unit)` validates metadata before executing the body, catches `NativeTestFailure` as a `fail` result, and catches other exceptions as `error` results. Non-string metadata keys are reported as discovery errors with reason `invalid native test metadata key: expected string, received <type>`; non-string metadata values are reported as discovery errors with reason `invalid native test metadata value for key '<key>': expected string, received <type>`. Diagnostics use Genia runtime type names; existing `TestUnit.location` is appended when available. Invalid metadata must not cause the test body to execute.
- `run_test_suite(test_units)` runs each unit in given order and aggregates results via `aggregate_results`.
- Normalized `TestResult` dictionaries contain stable keys: `kind`, `name`, `phase`, `reason`, `expected`, `actual`, `stdout`, `stderr`, `diagnostics`.
- `stdout` and `stderr` are stable empty strings in this phase; capture is not implemented.
- `TestSuiteResult` dictionaries contain: `total`, `passed`, `failed`, `errored`, `results`.
- `results` preserves input order exactly.
- Validated by `tests/unit/test_native_test_kernel.py` (10 tests, Python reference host only).

Not implemented in this phase:
- `skip` result kind
- `duration` field
- shared spec-runner integration
- host adapter for Genia runtime callables
- parser/lexer/evaluator/Core IR changes
- broad assertion framework, lifecycle hooks, lifecycle annotations (such as `@setup`/`@teardown`), or fixtures; only the minimal helpers `assert_true` and `assert_eq` are implemented; `@test` annotation discovery is handled by the CLI/test-mode layer, not the kernel
- stdout/stderr capture (fields are present but always empty strings)
- multi-host test execution

## 9.1.1) Native test assertion helpers (Python reference host, Experimental)

PYTHON REFERENCE HOST:
- The Python reference host provides minimal native-test assertion helpers: `assert_true(value)` and `assert_eq(actual, expected)`.
- Implemented as builtins registered directly in the global environment via `src/genia/builtins.py`.
- This is not a full assertion framework. This is the minimal native-test helper surface.

`assert_true(value)`:
- passes when `value` is truthy according to current runtime truthiness
- returns `none` on success
- prints nothing on success
- raises `NativeTestFailure` on assertion failure
- inside native test mode, a failing `assert_true` is reported as a test `FAIL` outcome, not an `ERROR` outcome

`assert_eq(actual, expected)`:
- passes when `actual` equals `expected` according to current Genia equality behavior
- compares Outcome values directly, including `none(...)`
- returns `none` on success
- prints nothing on success
- preserves useful actual/expected diagnostics on failure
- raises `NativeTestFailure` on assertion failure
- inside native test mode, a failing `assert_eq` is reported as a test `FAIL` outcome, not an `ERROR` outcome

Assertion failure behavior:
- Inside native test mode, failing helpers are reported as test FAIL outcomes rather than evaluation ERROR outcomes.
- Incorrect helper arity remains an evaluation ERROR.
- Later tests in the same suite continue running after an assertion failure.

Not implemented in this phase:
- `assert_false`, `assert_ne`, `assert_raises`, custom assertion messages, snapshot testing, property testing, soft assertions, or matcher DSLs
- cross-host implementation; Python is the only implemented host
- assertion lifecycle hooks, grouping, or count tracking

A Genia-native fixture now covers the R1 validated pipeline path. Validated by `tests/unit/test_r1_validated_pipeline_native_tests.py` (1 test, Python reference host only); the fixture is `tests/native/r1_validated_pipeline.genia`. Validated pipeline behavior is covered by a native test fixture using `parse_jsonl_record`, `validate_each`, `validate_record`, `collect_validated`, and `assert_eq`.

A Genia-native fixture now covers selected Outcome constructor, representation, predicate, and structured absence inspection behavior. Validated by `tests/unit/test_outcome_native_tests.py` (7 tests, Python reference host only); the fixture is `tests/native/outcome_rendering.genia`. The fixture uses `@test` annotated zero-argument functions and `assert_eq` to cover selected current behavior for `some(...)`, `none(...)`, `err(...)`, `display(...)`, `debug_repr(...)`, `some?`, `none?`, `absence_reason`, `absence_context`, and `absence_meta`. This is selected native coverage only; it does not change Outcome semantics or native-test report semantics.

A Genia-native fixture covers selected validation-helper behavior for the R3 validated-pipeline surface, including required/field/optional/record validation, `validate_each` Outcome-boundary behavior, and `collect_validated` aggregation. Validated by `tests/unit/test_r3_validation_helpers_native_tests.py` (1 test, Python reference host only); the fixture is `tests/native/r3_validation_helpers.genia`. This is selected native coverage only and does not change validation, Outcome, Flow, or native-test semantics.

A Genia-native fixture covers selected Flow/Seq visible behavior, including direct Flow `map`, `filter`, and `scan` results, list-side `collect` reuse, and list-side `run` terminal behavior returning `none`. Validated by `tests/unit/test_flow_seq_native_tests.py` (1 test, Python reference host only); the fixture is `tests/native/flow_seq_behavior.genia`. This is selected native coverage only and does not change Flow, Seq, assertion, or native-test semantics.

A runnable native-test example file is now available for the R3 validated-pipeline surface. The example is `examples/r3_validated_pipeline_native_tests.genia`, validated by `tests/unit/test_r3_validated_pipeline_native_test_examples.py` (1 test, Python reference host only). It covers Outcome-boundary preservation through `validate_each` (upstream `some(...)`, `none(...)`, and `err(...)` items pass through without invoking the validator), direct `validate_each(...) |> collect_validated(...)` composition, and a JSONL-style pipeline demonstrating clean/diagnostic observability. The example uses existing `test(name, body)` native-test authoring, existing validation helpers, and existing Outcome semantics only. This is selected native coverage only; it does not imply complete validated-pipeline coverage, advanced Flow behavior beyond what is already stated above, or new language/runtime/CLI/lifecycle behavior.

## 9.2) Native test CLI (Python reference host, Experimental)

Status: Experimental, Python reference host.

`genia --test <file>` runs native test units registered through the test-mode-only `test(name, body)` helper and `@test` annotated zero-argument functions discovered after evaluation, and reports the existing normalized native test runner outcomes. The CLI prints suite counts before and after per-result lines, reports `PASS`, `FAIL`, and `ERROR` results, and exits `0` when no failures/errors occur, `1` when failures or normalized test errors occur, and `2` for invalid CLI invocation.

`genia test <file>` routes through `src/genia/test_cli.py::run_native_tests_from_file`, sharing the same report format as `genia --test <file>`. It validates and parses the file, discovers test units through the existing test-mode-only `test(name, body)` registration path and appends `@test` annotated zero-argument functions discovered after evaluation, runs the discovered units through the native test kernel, prints a summary line (`total=<t> passed=<p> failed=<f> errored=<e>`) before and after per-result lines, and exits `0` when all discovered tests pass, `1` when any test fails/errors, and `2` for invalid CLI invocation.

Native tests may be authored with the legacy `test(name, body)` call form. Native tests may also be authored as `@test "description"` annotated zero-argument functions. The `@test "description"` annotation carries the human-readable description; the function name is the test identifier. Annotated native tests are discovered only in native test mode. `@test` marks functions for discovery; it does not execute by itself. Annotated tests use the same native test kernel as legacy tests. Assertion failures are `FAIL`; unexpected runtime exceptions are `ERROR`; malformed annotated declarations are discovery `ERROR`: empty `@test` description, `@test` on a non-function binding, and `@test` on a parameterized function are each reported with distinct discovery error reasons; a malformed annotated declaration keeps its own discovery error reason and is not overridden by duplicate-name detection. Duplicate native-test names among valid annotated and explicit units are discovery errors; the discovery reason begins with `duplicate native test name: <name>` followed by deterministic `occurrence N: <location>` lines for each conflicting definition, where location is derived from existing `TestUnit.location` metadata when available or `<unknown>` when not. Lifecycle hooks are not implemented. Setup/teardown, fixtures, parameterized tests, filtering, parallel native tests, and broad lifecycle semantics are not implemented.

PYTHON REFERENCE HOST:
- Implemented as `src/genia/test_cli.py` in the Python reference host.
- The `genia test <file>` entry point is implemented as `src/genia/test_cli.py::run_native_tests_from_file` and routed by `src/genia/interpreter.py`.
- Test mode registers a test-mode-only `test(name, body)` helper that appends `TestUnit` values to a private list; malformed units are normalized as discovery errors by the existing kernel.
- `--test` is mutually exclusive with `-c`/`--command`, `-p`/`--pipe`, and `--debug-stdio`.
- Invalid combinations such as `--debug-stdio --test` are rejected with exit code `2`.
- Report format: a summary line `total=<t> passed=<p> failed=<f> errored=<e>` appears both before and after per-result lines.
- Per-result lines: `PASS <name>`, `FAIL <name> phase=<phase> reason=<reason>` (with `expected=<expected> actual=<actual>` when present), `ERROR <name-or-unnamed> phase=<phase> reason=<reason>`.
- Validated by `tests/unit/test_native_test_cli.py` (17 tests) and `tests/unit/test_interpreter_test_mode.py` (20 tests), Python reference host only.

`@test "description"` annotation-driven native test discovery is implemented; annotated zero-argument functions are discovered after legacy `test(name, body)` registrations and run through the same native test kernel. Duplicate test names across explicit and annotated tests are discovery errors. This does not add setup/teardown lifecycle hooks, `@setup` or `@teardown` annotations, filtering, parallel execution, JSON/JUnit/TAP output, or multi-host test execution.

## 9.3) Lifecycle plan data-shape support (Python reference host, Experimental)

Status: Experimental, Python reference host only. Implemented in issue #449; root policy validation extended in issue #451.

LANGUAGE CONTRACT:
- A lifecycle plan is ordinary data: a map with a required `name` identifier and a required `phases` list of phase maps.
- A lifecycle phase is a map with a required `name` identifier and a required `action` identifier. Optional fields are `scope` (portable scope label), `always` (boolean), `description` (string), and `metadata` (map).
- Phase order is list order; no implicit ordering or reordering is added.
- `action` is a portable identifier (a quoted symbol), not a callable or host hook; it does not execute by existing in a plan.
- `always`, if present, must be a boolean; it normalizes to `false` when absent.
- Optional root policy maps are supported for portable data validation only: `cleanup`, `failure_policy`, and `result_policy`.
- Root policy maps normalize contract-safe defaults and reject unsupported, unsafe, or nonportable policy values. Cleanup validation preserves cleanup eligibility for entered scopes, rejects cleanup for unentered scopes, keeps cleanup failures observable, and permits only supported cleanup ordering labels. Failure policy validation preserves primary failures and cleanup failures and rejects policies that overwrite or swallow cleanup failures. Result policy validation fixes `failure_order` to the deterministic `observed_order` label and validates the observability include flags (`include_phase`, `include_scope`, `include_role`, `include_source_location`) as booleans, preserving each explicit accepted value in the normalized output and defaulting omitted flags to `true`.
- A valid plan must not contain duplicate phase `name` values within one plan.
- Lifecycle plans are inert data: constructing, importing, or validating a plan does not execute lifecycle behavior.

PYTHON REFERENCE HOST:
- `validate_lifecycle_plan(value) -> None` validates the shape without executing lifecycle behavior; raises `ValueError` with a deterministic path-based diagnostic on invalid input.
- `normalize_lifecycle_plan(value) -> GeniaMap` validates and returns a normalized plan map with `always` defaulted to `false` on phases where absent; raises `ValueError` on invalid input.
- Identifier fields (`name`, `action`, `scope`) must be `GeniaSymbol` values (produced by `quote(...)` in Genia surface code).
- Callable values as `action` fields are rejected as nonportable behavior.
- Implemented in `src/genia/lifecycle_plan.py`.
- Validated by `tests/unit/test_lifecycle_plan.py` (35 tests), Python reference host only.

Explicit limitations:
- No lifecycle runner behavior is implemented.
- No phase execution is implemented.
- No cleanup execution behavior is implemented.
- No action resolution or registry is implemented.
- No execution-mode lifecycle dispatch is implemented.
- No annotation-driven phase discovery (`@setup`, `@teardown`) is implemented.
- No module, server, actor, notebook, or browser lifecycle support is implemented.
- No portable multi-host lifecycle runner behavior is implemented.
- This is Python reference-host internal utility code; no public Genia prelude API was added in this phase.

## 9.4) Lifecycle scope tree data-shape support (Python reference host, Experimental)

Status: Experimental, Python reference host only. Implemented in issue #450.

LANGUAGE CONTRACT:
- A lifecycle scope tree is ordinary data: a map with a required `scopes` list of scope maps.
- Each scope is a map with a required `name` identifier, a required `parent` (either `none` for the root scope or `some(identifier)` for non-root scopes), and a required `children` list of identifiers.
- The first-pass R4 scope vocabulary is exactly four names: `execution`, `suite`, `module`, `test`.
- The canonical first-pass hierarchy is `execution -> suite -> module -> test`.
- Canonical parent/child relationships are deterministic:
  - `execution`: parent `none`, children `[suite]`
  - `suite`: parent `some(execution)`, children `[module]`
  - `module`: parent `some(suite)`, children `[test]`
  - `test`: parent `some(module)`, children `[]`
- Duplicate scope names are rejected.
- Unsupported scope names (including server, actor, plugin, request, browser, notebook) are rejected.
- Optional `description` (string) and `metadata` (map) fields are preserved as inert data and are not executed.
- Lifecycle scope tree data is inert: constructing, importing, or validating a scope tree does not execute lifecycle behavior.

PYTHON REFERENCE HOST:
- `validate_lifecycle_scope_tree(value) -> None` validates the shape without executing lifecycle behavior; raises `ValueError` with a deterministic path-based diagnostic on invalid input.
- `normalize_lifecycle_scope_tree(value) -> GeniaMap` validates and returns a normalized scope tree map; raises `ValueError` on invalid input.
- Identifier fields (`name`, `parent` inner value, and `children` entries) must be `GeniaSymbol` values (produced by `quote(...)` in Genia surface code).
- Input order of scope records is preserved by normalization; no implicit reordering occurs.
- Callable values stored in optional `metadata` fields are not invoked during validation or normalization.
- Implemented in `src/genia/lifecycle_scope.py`.
- Validated by `tests/unit/test_lifecycle_scope.py` (13 tests), Python reference host only.

Explicit limitations:
- No lifecycle runner behavior is implemented.
- No lifecycle phase execution is implemented.
- No setup/teardown behavior is implemented.
- No annotation discovery or annotation execution is implemented.
- No cleanup execution behavior is implemented.
- No execution-mode lifecycle dispatch is implemented.
- No server, actor, plugin, browser, notebook, HTTP, command, file, pipe, REPL, source, or flow lifecycle scopes are implemented.
- No changes were made to parser, lexer, Core IR, evaluator, prelude, CLI, native test runner, runtime execution paths, or shared semantic specs.
- This is Python reference-host internal utility code; no public Genia prelude API was added in this phase.

## 9.5) Lifecycle annotation binding helper (Python reference host, Experimental)

Status: Experimental, Python reference host only. Implemented in issue #452; ordering-rule contract hardened in issue #453.

LANGUAGE CONTRACT:
- Lifecycle annotation binding treats annotations as candidate markers for lifecycle phases; annotations do not execute themselves.
- A lifecycle annotation binding selects candidates by annotation name, exact metadata filters, participant kind, and deterministic ordering.
- Supported first-pass ordering labels are `source_order`, `reverse_source_order`, and `stable_name_order`.
- Omitted annotation binding ordering defaults to `source_order`.
- Ordering metadata is normalized and preserved in the binding result data. Ordering metadata is inert: it does not execute annotated declarations, introduce lifecycle phase execution, introduce setup/teardown behavior, or introduce dependency or priority ordering.
- Invalid ordering values fail validation with a deterministic diagnostic. Unsupported ordering labels and non-string ordering values are both rejected; the diagnostic names the `binding.ordering` field, and for non-string values it names the runtime type. Ordering validation does not invoke participant or ordering values.
- Required bindings report a deterministic diagnostic when no participants match; optional bindings may produce an empty participant list without diagnostics.
- Selecting the same declaration more than once for one binding produces a deterministic diagnostic and includes that declaration at most once.
- Binding results are discovery data only. Selecting a participant does not invoke it, activate a phase, execute setup/teardown behavior, or change ordinary evaluation.

PYTHON REFERENCE HOST:
- Implemented as `src/genia/lifecycle_binding.py`.
- Provides internal dataclasses and `discover_lifecycle_participants(...)` for phase-owned annotation binding discovery.
- The helper supports annotation-name matching, exact metadata filtering, callable participant validation, deterministic ordering, duplicate diagnostics, required-binding diagnostics, and binding results without executing participant values.
- `LifecycleAnnotationBinding.ordering` defaults to `source_order` when omitted. Ordering values are validated through a centralized `_validate_ordering(...)` check that rejects non-string values and unsupported labels with deterministic `binding.ordering` diagnostics; the ordering value is preserved in the normalized binding result data.
- Validated by `tests/unit/test_lifecycle_binding.py` (17 tests), Python reference host only.

Explicit limitations:
- No lifecycle runner behavior is implemented.
- No lifecycle phase execution is implemented.
- No setup/teardown behavior is implemented.
- No `@setup` or `@teardown` annotations are implemented.
- No parser, lexer, Core IR, evaluator, CLI, native test behavior, prelude, public builtin, runtime execution path, or shared semantic spec behavior changed.
- No public Genia lifecycle annotation binding API was added.
- Native test discovery remains owned by the existing native test CLI/test-mode layer; it was not refactored to use this helper in this phase.

## 9.6) Native test lifecycle contract consumer (Python reference host, Experimental)

Status: Experimental, Python reference host only, internal/inert lifecycle contract consumer. Implemented in issue #454.

The Python reference host native test path is the first implemented consumer of the inert R4 lifecycle contract. It describes and validates the existing native test lifecycle shape as inert lifecycle plan/scope data. Observable native-test behavior is unchanged.

LANGUAGE CONTRACT:
- The native test path is described as an inert lifecycle plan with the phase shape `discover -> run -> report`.
- The native test path is described as an inert lifecycle scope tree with the canonical hierarchy `execution -> suite -> module -> test`.
- The descriptor is internal/inert data: constructing or validating it does not execute lifecycle behavior and does not change native-test behavior.
- Descriptor validation is silent during native test execution; it produces no user-visible output unless the static internal descriptor is malformed.

PYTHON REFERENCE HOST:
- Implemented in `src/genia/native_test_lifecycle.py` with:
  - `native_test_lifecycle_plan()` — returns inert lifecycle plan data for the native test path.
  - `native_test_lifecycle_scope_tree()` — returns inert lifecycle scope-tree data for the native test path.
  - `validate_native_test_lifecycle()` — validates and returns normalized plan/scope data using the existing lifecycle helpers (`normalize_lifecycle_plan`, `normalize_lifecycle_scope_tree`).
- The descriptor reuses the existing inert lifecycle plan/scope validators (sections 9.3 and 9.4); it does not duplicate or loosen validation logic.
- Dependency direction is `native_test_lifecycle.py -> lifecycle_plan.py / lifecycle_scope.py`; the lifecycle helpers do not depend on native-test modules.
- `validate_native_test_lifecycle()` is integrated into `src/genia/test_cli.py` on the native test file execution path as a silent, behavior-neutral validation call.
- Validated by `tests/unit/test_native_test_lifecycle_consumer.py` (9 tests), Python reference host only.

Explicit limitations:
- No lifecycle runner is implemented.
- No lifecycle phase execution is implemented.
- No setup execution is implemented.
- No teardown execution is implemented.
- No `@setup` or `@teardown` annotations are implemented.
- No generalized annotation execution is implemented.
- No lifecycle action registry or action resolution is implemented.
- No public Genia prelude lifecycle API was added.
- No parser, lexer, Core IR, or evaluator semantic changes were made.
- Native-test discovery is not routed through lifecycle binding; `@test` discovery is unchanged and `discover_lifecycle_participants(...)` is not used.
- No execution-mode lifecycle dispatch is implemented.
- The native-test consumer adds no server, actor, plugin, YAML, browser, notebook, or data-workflow lifecycle. The separate focused R8 server lifecycle core is described in section 9.7; no multi-host lifecycle is implemented.
- No changes to native-test CLI output or native-test exit codes were made.

## 9.7) R8 server execution contract

Status: Implemented. The independently callable lifecycle core (issue #534), inert route/server/CORS annotation bindings (issues #535-#537), and explicit CLI/live HTTP integration (issue #533) are implemented as Experimental Python-reference-host-only behavior. The descriptor and lifecycle-result shapes are host-independent; execution remains Python-reference-host-only in R8. Defined in issue #558.

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

- `src/genia/server_lifecycle.py` implements the dedicated, independently callable lifecycle core. `server_lifecycle_plan()` returns inert plan data for the exact `startup -> request -> shutdown` phases and `server` / `request` scopes; `validate_server_lifecycle()` validates that static descriptor through the existing lifecycle-plan normalizer without executing lifecycle work.
- `run_server_lifecycle(application, requests, activate=..., request=..., close=...)` is the only implemented #534 activation seam. It accepts already validated/discovered application data, a finite ordered request source, and injected Python operations, so it is callable without CLI parsing or live sockets.
- Successful activation establishes listener ownership; requests run in order without retry; request failure skips later requests; an owned listener receives exactly one close opportunity. Activation failure creates no ownership and performs no close. The first non-cleanup failure remains primary, and close failures are preserved in `cleanup_failures` without replacing it.
- The core returns the seven-key lifecycle result map defined above. Injected-operation exceptions are normalized to failure maps containing `mode`, `phase`, `scope`, `reason`, and `source_location` when the exception provides one.
- This is one fixed lifecycle consumer, not a lifecycle-plan runner: phase action identifiers remain inert and there is no action registry or resolver.
- Validated by `tests/unit/test_server_lifecycle.py` (9 tests), Python reference host only.

PYTHON REFERENCE HOST (IMPLEMENTED ROUTE ANNOTATION BINDING):

- The evaluator accepts `@route {method: ..., path: ...}` only on a top-level named function, validates the exact closed descriptor map, and stores it as inert `route` binding metadata. The parser, AST grammar, and Core IR are unchanged.
- Repeated `@route` on one declaration and annotated replacement of existing canonical `route` metadata fail deterministically. An initial `@meta` entry named `route` remains ordinary metadata and is not a canonical route candidate; existing merge behavior for other annotations remains unchanged.
- `src/genia/server_route_binding.py` discovers only annotated `IrFuncDef` declarations from the supplied evaluated entry-file IR list and environment. It preserves source order with declaration name as tie-breaker, requires exactly one fixed one-argument function arm, aggregates descriptor diagnostics before exact `(method, path)` conflict diagnostics, and rejects every conflict member.
- A diagnostic-free result assembles existing generic R7 route values in source order and passes them once to the existing `route_request` operation through injected call boundaries. Discovery and assembly do not start a listener or execute a route handler.
- Validated by `tests/unit/test_server_route_binding.py` and focused annotation metadata tests. This is Experimental Python-reference-host internal support; there is no public route-discovery prelude API.

PYTHON REFERENCE HOST (IMPLEMENTED SERVER-CONFIG ANNOTATION BINDING):

- The evaluator accepts `@server {host: ..., port: ..., max_requests: ...}` only on a top-level assignment, validates and normalizes the closed descriptor, and stores it as inert `server` binding metadata. The parser, AST grammar, and Core IR are unchanged.
- Omitted `host` and `port` normalize to the existing `serve_http` defaults `"127.0.0.1"` and `8000`. `port` must be an integer in `[0, 65535]`; optional `max_requests` must be a positive integer when present, while explicit runtime absence is treated as omitted. Input maps are not mutated.
- Repeated `@server` on one declaration and annotated replacement of existing `server` metadata fail deterministically. An initial `@meta` entry named `server` remains ordinary metadata and is not a canonical server candidate; existing merge behavior for other annotations remains unchanged.
- `src/genia/server_config_binding.py` discovers only annotated `IrAssign` declarations from the supplied evaluated entry-file IR list and environment. It preserves source order with declaration name as tie-breaker, requires exactly one valid entry-file descriptor, ignores imported declarations, and returns deterministic descriptor/cardinality diagnostics without starting a listener.
- A diagnostic-free result passes the normalized configuration and unchanged handler once to an injected operation with the existing `serve_http(config, handler)` shape. Diagnostics prevent that operation from being called. This bind-down is independently testable and does not implement CLI dispatch or live lifecycle-to-HTTP composition.
- Validated by `tests/unit/test_server_config_binding.py`. This is Experimental Python-reference-host internal support; there is no public server-config discovery or binding prelude API.

PYTHON REFERENCE HOST (IMPLEMENTED CORS ANNOTATION BINDING):

- The evaluator accepts `@cors {origin: ..., methods: ..., headers: ...}` only on a top-level assignment, validates the closed descriptor through the same policy validator used by R7 `cors`, and stores the original validated map as inert `cors` binding metadata. The parser, AST grammar, and Core IR are unchanged.
- Repeated `@cors` on one declaration and annotated replacement of existing `cors` metadata fail deterministically. An initial `@meta` entry named `cors` remains ordinary metadata and is not a canonical CORS candidate; existing merge behavior for other annotations remains unchanged.
- `src/genia/server_cors_binding.py` discovers only annotated `IrAssign` declarations from the supplied evaluated entry-file IR list and environment. It preserves source order with declaration name as tie-breaker, accepts descriptor absence, requires any descriptor to share the selected `@server` owner, ignores imported declarations, and returns deterministic payload/cardinality/ownership diagnostics without starting a listener.
- A diagnostic-free result with no CORS descriptor returns the unchanged assembled handler without calling a wrapper. One accepted descriptor passes its policy and the unchanged handler exactly once to an injected operation with the existing `cors(policy, handler)` shape. Diagnostics prevent that operation from being called. R7 `cors` and `with_headers` remain the sole owners of preflight and response-header behavior.
- The shared internal policy validator in `src/genia/cors_policy.py` preserves the existing R7 validation order, defaults, and messages; it prevents a duplicate annotation-specific policy contract.
- Validated by `tests/unit/test_server_cors_binding.py` plus existing R7 CORS tests. This is Experimental Python-reference-host internal support; there is no public CORS-discovery or server-binding prelude API.

PYTHON REFERENCE HOST (IMPLEMENTED CLI INTEGRATION):

- Python remains the only R8 server execution host because `serve_http`, `route_request`, `cors`, and `with_headers` are Python-reference-host capabilities.
- `genia serve <file>` accepts exactly one existing entry-file path, evaluates it once without `main` dispatch, performs entry-file descriptor discovery, and prevents activation when diagnostics exist.
- A valid application assembles source-ordered routes through `route_request`, applies optional application CORS once through `cors`, and activates `serve_http` through the dedicated lifecycle coordinator. Finite `max_requests` completion exits `0` without printing the lifecycle result; startup or lifecycle failure emits a Genia-facing `serve <phase>/<scope>` diagnostic and exits `1`.
- Missing files, extra operands, and conflicting serve command shapes are CLI usage errors and exit `2` before evaluation or activation.
- Future hosts may consume the host-independent inert descriptor and lifecycle-result shapes, but R8 adds no shared host-adapter capability and makes no multi-host server guarantee.

Explicit limitations:

- `@route`, `@server`, and `@cors` metadata remain inert outside explicit `genia serve <file>` activation.
- No generalized lifecycle runner, middleware system, plugin system, dependency injection, path parameters, concurrent serving, streaming, WebSockets, authentication, authorization, credential policy, per-route CORS, graceful signal protocol, parser/Core IR change, or second web mechanism is defined.

## 9.8) R14 E14-1 lifecycle instance and parent/child execution scopes

Status: Implemented. The vertical-composition instance/scope core (issue #621) is implemented as Experimental, portable, Python-reference-host-only behavior. It is the first implemented slice of the approved R14 contract (`docs/design/r14-composable-lifecycle-contract.md`, approved by issue #620). Horizontal peer-attachment breadth remains #692, `lifecycle_repeat`/element scopes remain #693, provider binding remains #694, and HTTP remains #622-#628 — none of that is implemented yet.

LANGUAGE CONTRACT:

- Three ordinary functions are implemented: `lifecycle_scope(peers, work)`, `lifecycle_child(scope_handle, peers, work)`, and `lifecycle_context(scope_handle, name)`. `lifecycle_repeat`, `lifecycle_config`, and `web.http_send` are not implemented by this issue.
- A peer (`LifecycleDefinition`) is an ordinary closed map `{name: symbol, enter: callable/1, exit: callable/2}`. Any other shape, a non-symbol or empty-string `name`, or a duplicate name within one peer list is construction-time misuse (`TypeError`) raised before any `enter` call.
- `enter(scope_handle)` must return `some(context_value)` or `err(reason, context)`; any other return is misuse. A successful `enter` makes its peer "entered" and exposes `context_value` through `lifecycle_context` under that peer's name, readable by later peers in the same list and by `work`, but never by an earlier peer in the same list.
- Peers on one scope operation enter in list (attachment) order and unwind (`exit`) in strict reverse order. `exit(scope_handle, primary_summary)` receives only the narrow `{status: quote(ok)|quote(error), phase, peer}` summary — never another peer's context or resources — and must return `some("nil")` or `err(reason, context)`.
- `work(scope_handle)` runs only if every peer entered. Its return value is carried into the result's `result` field verbatim and is never inspected for `some`/`none`/`err`; the only way `work` produces a lifecycle failure is by raising, normalized the same way R8 normalizes lifecycle exceptions (`reason` from `str(exception)`, non-sensitive empty `context`).
- Every scope operation returns exactly one closed `LifecycleResult`: `{status: quote(ok)|quote(error), state: quote(completed)|quote(failed), scope: quote(root)|quote(child), phase: quote(enter)|quote(work)|quote(exit), peer: some(symbol)|none("lifecycle-no-peer"), result: some(value)|none("lifecycle-no-result"), primary_failure: none("lifecycle-no-failure")|failure_value, cleanup_failures: [failure_value, ...]}`, where `failure_value` is `{peer, phase, reason: string, context: map}`.
- Exactly one failure is primary per `LifecycleResult`: the first entry, work, or unwind failure encountered. The first exit failure encountered with no primary failure yet is promoted to `primary_failure`; every later exit failure in the same unwind is appended to `cleanup_failures` in exit-call order. Every entered peer's `exit` is attempted exactly once regardless of earlier exit failures.
- `result` carries `work`'s return value whenever `work` executed without raising, independent of any later exit failure; it is `none("lifecycle-no-result")` only when `work` never ran (an entry failure) or `work` raised.
- Scope lifetime is `created -> entering -> active -> exiting -> completed` on success, `created -> entering -> failed` when the very first peer's `enter` fails (nothing yet entered, so no unwind), `created -> entering -> exiting -> failed` when a later peer's `enter` fails (unwinds only the already-entered peers), and `created -> entering -> active -> exiting -> failed` on a work or exit failure.
- A scope handle is valid only while its scope is `entering`/`active`/`exiting`. Any later use by `lifecycle_context` or `lifecycle_child` raises `RuntimeError("lifecycle-scope-expired")` — the same single-valid-lifetime family as an already-consumed Flow. This is the entire cancellation/shutdown surface: there is no external cancel/abort/signal API.
- `lifecycle_child(scope_handle, peers, work)` runs a new scope as a plain nested function call from inside the parent's own `work`; it requires the parent handle to be `active` (not merely alive) and raises a distinct `RuntimeError` (not the scope-expired identifier) otherwise, since a handle mid-`entering`/`exiting` is alive but in the wrong phase for child creation. A child's `LifecycleResult` is ordinary data returned to the parent's `work` — it is never implicitly raised into the parent, so a failed child never implicitly fails the parent. A child's peers/resources are entirely separate from the parent's; child entry and unwind complete synchronously inside the one `lifecycle_child` call, so a child can never outlive it, and a parent's own resources are untouched by a child's unwind.
- `lifecycle_context(scope_handle, name)` is inward-only and read-only: it checks the calling scope's own entered-peer context first, then walks each ancestor scope up to the root, returning the first match as `some(value)` or `none("lifecycle-context-absent")` if none expose that name. There is no write accessor and no way to mutate an ancestor's or peer's exposed context through this call.
- Non-shadowing is enforced at peer-list construction, before any `enter` runs: a peer name colliding with any name already exposed by an ancestor scope in the same chain is `TypeError` misuse. (This is the same mechanism later reserved names such as `quote(config)`/`quote(element)`/`quote(index)` will reuse in #693/#694; no reserved names exist yet in this issue.)
- No global mutable "current lifecycle" or "current scope" exists anywhere in this surface. No annotation, parser, AST, or Core IR change was made; every operation is an ordinary call over ordinary closed map/callable values, registered exactly like `config_view`/`secret_view`.

PYTHON REFERENCE HOST:

- `src/genia/lifecycle_runtime.py` implements the algorithm above. `GeniaLifecycleScope` is an internal, non-source-constructible handle (`kind`, `parent`, `lifetime`, `context`); it is never a public value category and is only ever the argument passed into one scope operation's own `enter`/`exit`/`work` callables.
- `run_lifecycle_scope(peers, work, invoke)`, `run_lifecycle_child(parent_handle, peers, work, invoke)`, and `lookup_lifecycle_context(handle, name)` take an injected `invoke: Callable[[Any, list], Any]` for calling caller-supplied Genia callables, mirroring `server_lifecycle.run_server_lifecycle`'s injected-operation style; `src/genia/builtins.py` wires this to the existing `_invoke_raw_from_builtin` evaluator path (the same one already used for `where`/`derive`/`config_get_or`'s default).
- Registered as `lifecycle_scope`/`lifecycle_child`/`lifecycle_context` in `src/genia/builtins.py`; documented in `src/genia/host_builtin_docs.py`.
- Validated by `tests/unit/test_lifecycle_runtime.py` (24 tests) exercising the module directly with a trivial injected invoker, Python reference host only. No host capability is introduced; shared/multi-host conformance remains Partial.

Explicit limitations:

- No `lifecycle_repeat`, `lifecycle_config`, HTTP operation/client, peer-attachment breadth beyond what one shared algorithm already proves, element scopes, reserved element/index/config context names, or provider binding is implemented.
- No generalized lifecycle-plan/action-identifier runner, dependency injection, scheduler, actor supervision, or concurrent peer/child execution is defined.

## 10) Explicitly not implemented (current)

- general unrestricted host interop / FFI layer
- general member access syntax
- index syntax
- generalized flow runtime semantics beyond the current phase (async scheduling, advanced backpressure/cancellation, configurable multi-port stages)
- full Flow system (stages/sinks/backpressure/multi-port pipelines)
- language-level scheduler/selective receive/timeouts (concurrency remains host-primitive based)

## 11) Example demos shipped in-repo

Per-release curated runnable examples (one or more small examples per
release for its headline behavior) are published at `docs/releases/` —
see `docs/releases/README.md`.

- `examples/tic-tac-toe.genia`: canonical Format + Seq-compatible style example — two-player console tic-tac-toe using `Format`/`format(...)` for board rendering and list-side sequence helpers for data-driven winner detection
- `examples/ants.genia`: canonical pure deterministic ants colony simulation demo with optional CLI seed for reproducible runs
- `examples/ants_terminal.genia`: blocking terminal developer UI over the same colony simulation with CLI-configurable seed, ant count, step count, delay, world size, and pure/actor mode selection
- `examples/ants_actor.genia`: actor/coordinator version of the ants simulation — same colony rules, different execution structure
- `examples/ants_web.genia`: browser visualization over the same ants simulation using the current blocking HTTP helper, JSON endpoints, and a Canvas renderer in plain browser JavaScript
- `examples/validated_pipeline_demo.genia`: experimental first demo milestone for the Outcome-aware validated data pipeline direction — a file-mode demo covered by shared CLI spec `spec/cli/validated-data-pipeline-demo.yaml`; reads JSONL records from `examples/data/validated_pipeline_demo.jsonl`, validates each record using existing `parse_jsonl_record`, `validate_each`, `validate_record`, and `collect_validated` helpers, and emits clean records plus diagnostics; demonstrates the intended Outcome-aware validated data pipeline direction; does not add new helper/runtime semantics; Experimental
- `examples/r3_validated_pipeline_native_tests.genia`: R3 native-test example for the validated-pipeline surface — runnable through the native test runner (`genia test examples/r3_validated_pipeline_native_tests.genia`); covers Outcome-boundary preservation through `validate_each`, direct `validate_each(...) |> collect_validated(...)` composition, and a JSONL-style pipeline with clean/diagnostic observability; uses existing `test(name, body)` native-test syntax and existing validation/Outcome helpers; validated by `tests/unit/test_r3_validated_pipeline_native_test_examples.py`; this is selected native coverage only, not complete validated-pipeline coverage; Experimental

`examples/ants.genia` intentionally uses only currently implemented features:

- ordinary persistent maps/lists for explicit world, cell, and ant state
- world-owned active food/pheromone position lists plus food/pheromone totals for compact evaporation and summary calculation
- explicit seeded randomness via `rng(seed)` plus `rand_int(rng_state, n)` for reproducible weighted movement choice
- world-owned RNG threading through `step(world) -> world2`
- recursive stepping over ants and simulation ticks
- `sleep` for blocking frame delay
- text rendering via `print`

Implemented colony behavior in this phase:

- nest/home region tracking
- food pickup with decremented food quantity
- return-to-nest delivery with delivered-food counting
- pheromone deposit on return paths
- pheromone evaporation each evolve
- direction-aware candidate moves with weighted seeded choice

It is intentionally pure and explicit. It is **not** actor-based, does **not** add a scheduler, and does **not** introduce hidden mutable runtime state or new language syntax.
This is the canonical simulation teaching pattern in this phase: ordinary world value, deterministic `step(world) -> world2`, seeded RNG threaded through the world, and rendering from snapshots in outer shells.

`examples/ants_terminal.genia` intentionally stays within the same current runtime surface:

- imports and renders the same pure colony simulation helpers from `examples/ants.genia`
- sequential multi-ant stepping with the same nest/food/pheromone/weighted-movement semantics as the tested ants helpers
- terminal rendering via `clear_screen()`, `move_cursor(x, y)`, and `render_grid(grid)`
- CLI configuration via `main(argv())` plus `cli_parse`
- explicit seeded randomness via `rng(seed)` plus `rand_int(rng_state, n)` for reproducible setup and movement
- visible text UI for development/teaching:
  - deterministic rendering priority: carrying ant `H`, ant `a`, nest `N`, food `*`, pheromone heat `#`/`+`/`:`, empty `.`
  - stats panel with mode, seed, evolve, remaining steps, ant/carrying counts, delivered food, remaining food, pheromone total, active trail count, and delay
  - CLI flags: `--seed`, `--ants`, `--steps`, `--delay`, `--size`, and `--mode pure|actor`
- pure mode steps the imported pure `ants.step(world)` model
- actor mode uses a coordinator actor session from `examples/ants_actor.genia` so the same terminal UI can compare the actor/coordinator execution structure

It is still a blocking terminal demo. It does **not** use `stdin_keys`, does **not** introduce a real-time event loop, does **not** provide pause/step/quit key controls, and does **not** add new language/runtime features. Same seed plus same config gives the same progression for a given mode.

`examples/ants_actor.genia` demonstrates actor-based concurrency using the same colony rules from `examples/ants.genia`:

- coordinator actor owns the authoritative world state
- ant workers request sense data via `actor_call` and submit move intents back to the coordinator
- explicit coordinator-driven evolve loop for deterministic reproducibility
- reusable actor session helpers for the terminal UI: `actor_session`, `actor_session_world`, `actor_session_step`, and `actor_session_stop`
- imports and reuses the pure scoring/movement logic from `ants.genia` via `import ants`
- per-ant RNG splitting via `rng(seed)` / `rand_int` for seeded randomness
- string-tagged messages: `["sense", ant_id]`, `["move_intent", ant_id, move]`, `["evolve"]`, `["snapshot"]`, `["stop"]`

It is a teaching architecture layer — same colony behavior, different execution structure. It does **not** add new language syntax, does **not** introduce a scheduler, and does **not** require selective receive or timeouts.

`examples/ants_web.genia` is an application/demo layer over the existing HTTP surface:

- serves `GET /`, `GET /app.js`, and `GET /style.css` as static browser assets
- serves `GET /state` as a JSON-friendly snapshot with evolve, seed, mode, world size, ant positions/carrying status, nest cells, food cells, pheromone cells, delivered food, remaining food, and small stats
- accepts `POST /reset` with JSON config (`seed`, `ants`, `size`, `delay`, `mode`) and `POST /step` to advance one evolve
- keeps one explicit server-memory session in a `ref`
- pure mode reuses `ants_terminal.start_session` over the pure `ants.step(world)` model
- actor mode reuses the coordinator session from `examples/ants_actor.genia`
- the browser uses Canvas drawing and client-side repeated `/step` calls for run/pause controls

It is a viewer over the current simulation/session logic. It does **not** implement browser-native Genia execution, a browser playground runtime, WebSockets, SSE, a generalized event loop, or a new server framework. Terminal ants remains the developer UI.
