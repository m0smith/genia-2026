# Builtin detail record

> **Non-authoritative provenance record.** This file preserves, verbatim and unedited, text that was displaced
> from `GENIA_STATE.md` during the #1099 distillation. It is audit material, not part of the truth hierarchy:
> it does not define Genia behavior, and `GENIA_STATE.md` governs. Start with the release, design, and reference
> documents; open this file only to see the exact displaced wording.
>
> Baseline: `GENIA_STATE.md` at `d401f322c692e8c3620509854065692c2605c61a`. Scope: Pre-condensation text of builtin sections (R17-R19 portability, validation helpers, Option model, bridges, and others).
> Ledger: `docs/analysis/state-distillation-migration-map.json`.

## B085: baseline lines 1732-1733

Moved from GENIA_STATE.md@d401f322, lines 1732-1733 (ledger row B085, retained-condensed, sha256 6ddc6ddad8f3e352)

~~~~~markdown
## 6) Builtins (runtime)

~~~~~

## B086: baseline lines 1734-1750

Moved from GENIA_STATE.md@d401f322, lines 1734-1750 (ledger row B086, retained-condensed, sha256 5ba235df2c8c8bfa)

~~~~~markdown
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

~~~~~

## B089: baseline lines 1821-1849

Moved from GENIA_STATE.md@d401f322, lines 1821-1849 (ledger row B089, retained-condensed, sha256 7aa5ad87c192ebed)

~~~~~markdown
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

~~~~~

## B100: baseline lines 2019-2032

Moved from GENIA_STATE.md@d401f322, lines 2019-2032 (ledger row B100, retained-condensed, sha256 8037781fe10c1163)

~~~~~markdown
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
- `row_get(row, column_name)` — return the value paired with `column_name` in a row (**Experimental**, issue #363); see below
~~~~~

## B101: baseline lines 2033-2048

Moved from GENIA_STATE.md@d401f322, lines 2033-2048 (ledger row B101, retained-condensed, sha256 cddeb7483e685715)

~~~~~markdown
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
~~~~~

## B102: baseline lines 2049-2062

Moved from GENIA_STATE.md@d401f322, lines 2049-2062 (ledger row B102, retained-condensed, sha256 b1d159a0f4f68bc3)

~~~~~markdown
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
~~~~~

## B103: baseline lines 2063-2076

Moved from GENIA_STATE.md@d401f322, lines 2063-2076 (ledger row B103, retained-condensed, sha256 a7aba983f6ec0c29)

~~~~~markdown
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
~~~~~

## B104: baseline lines 2077-2090

Moved from GENIA_STATE.md@d401f322, lines 2077-2090 (ledger row B104, retained-condensed, sha256 6dd642af20af4cdc)

~~~~~markdown
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

~~~~~

## B105: baseline lines 2091-2105

Moved from GENIA_STATE.md@d401f322, lines 2091-2105 (ledger row B105, retained-condensed, sha256 0cfee0b808bbb29b)

~~~~~markdown
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

~~~~~

## B106: baseline lines 2106-2132

Moved from GENIA_STATE.md@d401f322, lines 2106-2132 (ledger row B106, retained-condensed, sha256 430835f8485b0d02)

~~~~~markdown
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
~~~~~

## B107: baseline lines 2133-2149

Moved from GENIA_STATE.md@d401f322, lines 2133-2149 (ledger row B107, retained-condensed, sha256 70f8ae1a74ecb84b)

~~~~~markdown
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
~~~~~

## B108: baseline lines 2150-2174

Moved from GENIA_STATE.md@d401f322, lines 2150-2174 (ledger row B108, retained-condensed, sha256 48d3d489879b2409)

~~~~~markdown
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
~~~~~

## B109: baseline lines 2175-2194

Moved from GENIA_STATE.md@d401f322, lines 2175-2194 (ledger row B109, retained-condensed, sha256 dcb84166a3f77eb2)

~~~~~markdown
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

~~~~~

## B110: baseline lines 2195-2219

Moved from GENIA_STATE.md@d401f322, lines 2195-2219 (ledger row B110, retained-condensed, sha256 172b25bdbffc0492)

~~~~~markdown
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
~~~~~

## B111: baseline lines 2220-2238

Moved from GENIA_STATE.md@d401f322, lines 2220-2238 (ledger row B111, retained-condensed, sha256 c1548ac1ebf7bf63)

~~~~~markdown
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
~~~~~

## B112: baseline lines 2239-2253

Moved from GENIA_STATE.md@d401f322, lines 2239-2253 (ledger row B112, retained-condensed, sha256 7346f1cf2a4a84f3)

~~~~~markdown
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
~~~~~

## B113: baseline lines 2254-2278

Moved from GENIA_STATE.md@d401f322, lines 2254-2278 (ledger row B113, retained-condensed, sha256 165a5a572d31ef4c)

~~~~~markdown
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

~~~~~

## B125: baseline lines 2508-2522

Moved from GENIA_STATE.md@d401f322, lines 2508-2522 (ledger row B125, retained-condensed, sha256 f8154c7d7201578a)

~~~~~markdown
### Integer arithmetic portability (Experimental, R17 complete through E17-3)

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

~~~~~

## B126: baseline lines 2523-2537

Moved from GENIA_STATE.md@d401f322, lines 2523-2537 (ledger row B126, retained-condensed, sha256 6875265ddf0a23f2)

~~~~~markdown
### Portable value equality (Experimental, R18 complete through E18-7)

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

~~~~~

## B127: baseline lines 2538-2557

Moved from GENIA_STATE.md@d401f322, lines 2538-2557 (ledger row B127, retained-condensed, sha256 f3b340f471c089d8)

~~~~~markdown
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
~~~~~

## B128: baseline lines 2558-2576

Moved from GENIA_STATE.md@d401f322, lines 2558-2576 (ledger row B128, retained-condensed, sha256 ed324b6729ecf8ae)

~~~~~markdown
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
~~~~~

## B129: baseline lines 2577-2599

Moved from GENIA_STATE.md@d401f322, lines 2577-2599 (ledger row B129, retained-condensed, sha256 a0e19239492a7434)

~~~~~markdown
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
~~~~~

## B130: baseline lines 2600-2616

Moved from GENIA_STATE.md@d401f322, lines 2600-2616 (ledger row B130, retained-condensed, sha256 1ba6c20b2600f8af)

~~~~~markdown
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

~~~~~

## B131: baseline lines 2617-2630

Moved from GENIA_STATE.md@d401f322, lines 2617-2630 (ledger row B131, retained-condensed, sha256 d19b50838b58f4ea)

~~~~~markdown
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
~~~~~

## B132: baseline lines 2631-2648

Moved from GENIA_STATE.md@d401f322, lines 2631-2648 (ledger row B132, retained-condensed, sha256 4a59c817fe5b2496)

~~~~~markdown
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

~~~~~

## B133: baseline lines 2649-2662

Moved from GENIA_STATE.md@d401f322, lines 2649-2662 (ledger row B133, retained-condensed, sha256 089048f816e512ca)

~~~~~markdown
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
~~~~~

## B134: baseline lines 2663-2677

Moved from GENIA_STATE.md@d401f322, lines 2663-2677 (ledger row B134, retained-condensed, sha256 91a9b71ec482d93e)

~~~~~markdown
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

~~~~~

## B135: baseline lines 2678-2692

Moved from GENIA_STATE.md@d401f322, lines 2678-2692 (ledger row B135, retained-condensed, sha256 a4836a17048e4711)

~~~~~markdown
### Unicode and diagnostic portability (Experimental, R19 complete — E19-1 through E19-6)

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
~~~~~

## B136: baseline lines 2693-2712

Moved from GENIA_STATE.md@d401f322, lines 2693-2712 (ledger row B136, retained-condensed, sha256 10ec06f2c31cf6b9)

~~~~~markdown
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
~~~~~

## B137: baseline lines 2713-2736

Moved from GENIA_STATE.md@d401f322, lines 2713-2736 (ledger row B137, retained-condensed, sha256 ee8eb9146e68aa66)

~~~~~markdown
- What R19 E19-1 did not do: no grapheme-cluster model, no
  normalization/collation, no locale-aware formatting, no Decimal/Rational/
  Float64 numeric-model change, no new public string API, no Core IR change.
- **E19-2 diagnostic inventory.** A complete mechanical inventory of all 146
  `spec/error` exact-stderr cases and the 4 genuine `spec/parse` failure
  cases now exists (`docs/analysis/r19-diagnostic-mechanical-inventory.md`),
  classifying each by semantic family, construction site, and A/B/C
  portability class. Analysis only — no behavior changed by E19-2 itself.
- **E19-3 diagnostic normalization.** The one confirmed host-`repr()` leak
  the inventory found is fixed: a "No matching case" runtime-dispatch
  failure (`src/genia/evaluator.py`) now renders its call arguments with
  Genia's own `format_debug` (joined as `"[" + ", ".join(...) + "]"`, Genia's
  list debug syntax) instead of Python `repr()` of the argument tuple. For
  example, calling an unmatched function with a string argument now reports
  `with arguments ["hello"]` (Genia double-quote debug escaping) rather than
  Python's `with arguments ('hello',)` (Python single-quote tuple repr). All
  other diagnostic families the inventory reviewed were already portable
  (in particular, the large "expected X, received Y" family already renders
  via `_runtime_type_name`, a Genia-authored type-name table, not Python
  `type()`/`repr`); a lower-severity `repr()`-based quoting of closed-grammar
  source tokens (format-spec strings, lexer/parser token text) was reviewed
  and deliberately left unchanged for this slice — see the inventory
  document Section 7 for that recorded decision.

~~~~~

## B138: baseline lines 2737-2758

Moved from GENIA_STATE.md@d401f322, lines 2737-2758 (ledger row B138, retained-condensed, sha256 b7e338e3a12ade9e)

~~~~~markdown
- **E19-4 cross-surface leak audit.** A deliberate sweep of `src/genia/*.py`
  beyond E19-1/E19-3's fixes found no further in-scope-fixable-now host-
  wording leak: `configuration.py`'s dotenv UTF-8 decode boundary and
  `gemini_rest.py`'s decode fallback were already fully compliant; two items
  (shell-pipeline subprocess stdout's `errors="replace"`, and the explicit
  `python.*` host-module bridge's exception wrapper) were reviewed and
  recorded as deliberate follow-up candidates rather than fixed, since both
  are host-interop-by-design surfaces outside R19's minimal-change scope;
  `str(exc)` values in a handful of `builtins.py` Outcome context maps
  (`read_file`, `write_file`, `zip_read`/`zip_write`, config-resource
  backends) were confirmed to be incidental class-C debugging detail never
  asserted by any shared spec, not part of the portable diagnostic contract.
  See `docs/analysis/r19-host-default-leak-audit.md` for the full sweep.
- **E19-6 skeptical release truth audit — PASS.** Re-derived every slice's
  claims from `main` as merged, re-ran full regression (4247 passed, the
  same 2 pre-existing unrelated root-environment `chmod(0)` failures) and
  `python -m tools.spec_runner` (674/674), verified the independent-host
  acceptance criterion by direct reproduction attempt from the contract and
  release doc alone, and confirmed no R17/R18/R9/R10/R16 regression and no
  exact-numeric-model behavior smuggled into R19. See
  `docs/analysis/r19-release-truth-audit.md`.

~~~~~

## B139: baseline lines 2759-2786

Moved from GENIA_STATE.md@d401f322, lines 2759-2786 (ledger row B139, retained-condensed, sha256 d096add1170d0c1b)

~~~~~markdown
R19 is **complete**. See `docs/design/r19-unicode-diagnostic-portability-contract.md`
for the approved contract; `docs/analysis/r19-diagnostic-mechanical-inventory.md`
for the full diagnostic inventory; `docs/analysis/r19-host-default-leak-audit.md`
for the cross-surface leak audit; `docs/analysis/r19-release-truth-audit.md`
for the closing skeptical audit; `docs/releases/R19.md` for the release
summary.

**R20 — Open Functions and Extensible Pattern Dispatch is complete
(E20-1 through E20-8).** Its approved contract
(`docs/design/r20-open-functions-contract.md`) and syntax/Core IR design
(`docs/design/r20-open-functions-syntax-ir-design.md`) are implemented as
described in section 4.7 above, with the E20-8 skeptical release audit
(`docs/analysis/r20-release-truth-audit.md`) verdict and full evidence
recorded there and in `docs/releases/R20.md`. See section 4.7 for the
implemented boundary. R21 (numeric source classification), R22 (exact
numeric runtime), and R23 (numeric representation and interchange) have
since completed; the C++ host is now numbered R24 and its pre-flight gate
(`docs/design/r24-cpp-host-preflight.md`) records a GO decision. E24-1
(`m0smith/genia-2026#955`) completed toolchain bootstrap: a real,
compiled C++ E16-1 adapter honestly declaring every capability
unsupported, with no Genia language behavior implemented. **E24-2 through
E24-8 are now complete.** The host genuinely parses source, lowers only to
approved portable Core IR, evaluates its deliberately bounded grammar, and
provides `-c`/file-mode CLI. The floor includes R17 integers/ordered maps,
R18 equality/key identity, R19-normalized adapter diagnostics, local R20 open
functions, and the selected R21-R23 Decimal/Rational/Float64 arithmetic,
comparison, rendering, format, and strict numeric JSON evidence.

~~~~~

## B140: baseline lines 2787-2799

Moved from GENIA_STATE.md@d401f322, lines 2787-2799 (ledger row B140, retained-condensed, sha256 80b2a5e795cfee86)

~~~~~markdown
The final capability declaration is: `parser`, `ast_lowering`,
`cli_command_mode`, `cli_file_mode`, and `open_functions` `supported`;
`core_ir_eval`, `prelude_autoload`, and `shared_spec_runner` `partial`; every
other capability at the pinned revision `unsupported`. The latter two partial
claims describe the bounded source-level prelude and deterministic external-host
runner participation actually evidenced by R24; they do not claim the full
Python prelude or feature parity. `core_ir_eval` intentionally remains partial.
Pinned evidence against Genia revision
`a2229cb9b079a379a5eeae76a618fe69a2bd6daa` is `total=755 passed=141
unsupported=614 failed=0 protocol_error=0 crash=0 timeout=0 invalid=0`.
Unsupported behavior is expected and explicitly deferred to R25+; see
`docs/releases/R24.md` and `docs/analysis/r24-release-truth-audit.md`.

~~~~~

## B141: baseline lines 2800-2864

Moved from GENIA_STATE.md@d401f322, lines 2800-2864 (ledger row B141, retained-condensed, sha256 b36abbddeb7ea7f7)

~~~~~markdown
### Host-backed persistent associative maps (Phase 1 bridge; ordering Experimental, R17 complete through E17-3)

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

~~~~~

## B142: baseline lines 2865-2908

Moved from GENIA_STATE.md@d401f322, lines 2865-2908 (ledger row B142, retained-condensed, sha256 6af0e90373e26fe8)

~~~~~markdown
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

~~~~~

## B143: baseline lines 2909-2932

Moved from GENIA_STATE.md@d401f322, lines 2909-2932 (ledger row B143, retained-condensed, sha256 4d1a4b5855fee7c5)

~~~~~markdown
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

~~~~~

## B144: baseline lines 2933-2958

Moved from GENIA_STATE.md@d401f322, lines 2933-2958 (ledger row B144, retained-condensed, sha256 c8d05c12329c8232)

~~~~~markdown
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

~~~~~

## B145: baseline lines 2959-2982

Moved from GENIA_STATE.md@d401f322, lines 2959-2982 (ledger row B145, retained-condensed, sha256 7a689ec7c54b9412)

~~~~~markdown
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

~~~~~

## B146: baseline lines 2983-3008

Moved from GENIA_STATE.md@d401f322, lines 2983-3008 (ledger row B146, retained-condensed, sha256 6ba25708a59dc372)

~~~~~markdown
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

~~~~~

## B147: baseline lines 3009-3029

Moved from GENIA_STATE.md@d401f322, lines 3009-3029 (ledger row B147, retained-condensed, sha256 fee9c699bfadecbb)

~~~~~markdown
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
~~~~~

## B148: baseline lines 3030-3047

Moved from GENIA_STATE.md@d401f322, lines 3030-3047 (ledger row B148, retained-condensed, sha256 94ef48f18885c692)

~~~~~markdown
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

~~~~~

## B149: baseline lines 3048-3061

Moved from GENIA_STATE.md@d401f322, lines 3048-3061 (ledger row B149, retained-condensed, sha256 d8afbfd91bc73ce5)

~~~~~markdown
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
~~~~~

## B150: baseline lines 3062-3075

Moved from GENIA_STATE.md@d401f322, lines 3062-3075 (ledger row B150, retained-condensed, sha256 547cbf11bcef8f12)

~~~~~markdown
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

~~~~~

## B151: baseline lines 3076-3092

Moved from GENIA_STATE.md@d401f322, lines 3076-3092 (ledger row B151, retained-condensed, sha256 7a16202d69887a14)

~~~~~markdown
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
~~~~~

## B152: baseline lines 3093-3110

Moved from GENIA_STATE.md@d401f322, lines 3093-3110 (ledger row B152, retained-condensed, sha256 5449698f6d48dbf3)

~~~~~markdown
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
~~~~~

## B153: baseline lines 3111-3125

Moved from GENIA_STATE.md@d401f322, lines 3111-3125 (ledger row B153, retained-condensed, sha256 7226498b7c0e2abb)

~~~~~markdown
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
~~~~~

## B154: baseline lines 3126-3139

Moved from GENIA_STATE.md@d401f322, lines 3126-3139 (ledger row B154, retained-condensed, sha256 87073192ffa27de2)

~~~~~markdown
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
~~~~~

## B155: baseline lines 3140-3165

Moved from GENIA_STATE.md@d401f322, lines 3140-3165 (ledger row B155, retained-condensed, sha256 34588b55f1574e75)

~~~~~markdown
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

~~~~~

## B156: baseline lines 3166-3185

Moved from GENIA_STATE.md@d401f322, lines 3166-3185 (ledger row B156, retained-condensed, sha256 4f4497074a8e31c8)

~~~~~markdown
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
~~~~~

## B157: baseline lines 3186-3199

Moved from GENIA_STATE.md@d401f322, lines 3186-3199 (ledger row B157, retained-condensed, sha256 afb1fb3c98f2c485)

~~~~~markdown
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

~~~~~

## B159: baseline lines 3225-3239

Moved from GENIA_STATE.md@d401f322, lines 3225-3239 (ledger row B159, retained-condensed, sha256 716f43313f84db33)

~~~~~markdown
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
~~~~~

## B160: baseline lines 3240-3254

Moved from GENIA_STATE.md@d401f322, lines 3240-3254 (ledger row B160, retained-condensed, sha256 35c75293fdbfc19c)

~~~~~markdown
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

~~~~~

## B161: baseline lines 3255-3268

Moved from GENIA_STATE.md@d401f322, lines 3255-3268 (ledger row B161, retained-condensed, sha256 31aa5b16e2aa81a1)

~~~~~markdown
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
- portable JSON-domain limits are: string object names, no duplicate object names, safe integers in `[-9007199254740991, 9007199254740991]` (Integer), fraction/exponent numbers accepted as exact Decimal only when `stable_json_decimal` holds (R23 E23-3, issue #915 -- section 9.34; parsed/emitted lexically, never through a host float), a Rational encodable only when its exact value has a finite base-10 Decimal equivalent that itself satisfies `stable_json_decimal` (never rounded, never decoded back to Rational -- R23 E23-4, issue #921 -- section 9.35), a finite Float64 encodable using its canonical shortest-roundtrip decimal spelling as a bare JSON number (NaN/infinity rejected; decode never produces Float64 -- same section), Unicode scalar strings/names, and at most 128 nested object/array containers
- `json_decode` rejects malformed/trailing JSON, invalid UTF-8, duplicate names, nonstandard/non-finite or out-of-range numbers, invalid Unicode scalars, and excessive nesting as `err(...)`; `json_encode` rejects unsupported values/keys/facets and the same number/Unicode/nesting violations as `err(...)`
- boundary Outcome contexts contain `kind: quote(json)`, `operation: quote(decode|encode)`, `status: quote(decoded|encoded|error)`, and `reason`; malformed syntax adds 1-based `line`/`column`, duplicates add `key`, and unsupported encoding adds `value_type`
~~~~~

## B162: baseline lines 3269-3289

Moved from GENIA_STATE.md@d401f322, lines 3269-3289 (ledger row B162, retained-condensed, sha256 35eb7a60690c8a34)

~~~~~markdown
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
- (R15 E15-1, issue #728) a compiled Template carries an inert `template_description(...)` description mirroring its compiled schema exactly; see the "Inert inspectable Template descriptions" subsection above
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
~~~~~

## B163: baseline lines 3290-3303

Moved from GENIA_STATE.md@d401f322, lines 3290-3303 (ledger row B163, retained-condensed, sha256 6b29d009405b90fb)

~~~~~markdown
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
~~~~~

## B164: baseline lines 3304-3305

Moved from GENIA_STATE.md@d401f322, lines 3304-3305 (ledger row B164, retained-condensed, sha256 b5d8222d979dcf1e)

~~~~~markdown
- this is a minimal host-backed bridge and is **not** the full flow system

~~~~~
