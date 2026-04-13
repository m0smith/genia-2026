# Genia

Genia is a small, functional-first, expression-oriented language prototype.

This repository currently provides:

- a parser + evaluator (`src/genia/interpreter.py`)
- a tiny Core IR + AST→IR lowering pass used before evaluation
  - pipelines lower to an explicit ordered-stage IR node rather than nested calls
  - Option constructors lower explicitly as `some(...)` / `none(...)` IR values
- a REPL and file runner (`python3 -m genia.interpreter`)
- host-backed concurrency primitives with public prelude-backed process helpers (`spawn`, `send`, `process_alive?`)
- host-backed refs with public prelude-backed helpers (`ref`, `ref_get`, `ref_set`, `ref_update`)
- raw host-backed `argv()` plus prelude-backed CLI parsing helpers (`cli_parse`, `cli_flag?`, `cli_option`, `cli_option_or`)
- a minimal allowlisted Python host-interop layer via ordinary module imports (`import python`, `import python.json as pyjson`)
- simulation primitives (`rand`, `rand_int`, `sleep`)
- terminal helpers and input sources (`clear_screen`, `move_cursor`, `render_grid`, `stdin_keys`)
- a minimal host-backed HTTP serving foundation with prelude helpers (`serve_http`, `get`, `post`, `route_request`, `ok_text`, `json`)
- autoloaded prelude libraries (flow helpers, lists, map/ref/process/io helpers, option/string helpers, math helpers, awk helpers, fn helpers, evaluator helpers, cells)
  - flow helpers now include stateful `scan(step, initial_state)` for running totals, buffering, and windowing
  - bundled `.genia` prelude sources are loaded from package resources, so installed `genia` tools can use the same stdlib as repo execution
  - autoloaded function names can also be referenced as higher-order function values, not only called directly
- debug-stdio adapter support for editor integration
- runnable demos under `examples/` (including `tic-tac-toe.genia`, `ants.genia`, `ants_terminal.genia`, and `http_service.genia`)
- proper tail-call optimization for calls in tail position
- multi-host scaffolding docs/manifests under `docs/host-interop/`, `docs/architecture/`, `spec/`, `tools/spec_runner/`, and `hosts/`

## Quick start

```bash
python3 -m genia.interpreter
```

Run a program:

```bash
python3 -m genia.interpreter path/to/program.genia
```

Small annotation example:

```genia
@doc "Adds one"
inc(x) -> x + 1

meta("inc")
```

Result:

```genia
{doc: "Adds one"}
```

## Documentation & Metadata

Genia annotations are runtime metadata for top-level bindings, not macros.

The canonical `@doc` formatting guide lives in `docs/style/doc-style.md`.

Supported built-ins in this phase:

- `@doc "text"`
- `@meta { ... }`
- `@since "0.4"`
- `@deprecated "message"`
- `@category "name"`

Useful lookup helpers:

```genia
@doc "Adds one"
@category "math"
@since "0.4"
inc(x) -> x + 1

[doc("inc"), meta("inc")]
```

Style note:

- keep `@doc` concise and source-friendly
- use the Markdown subset defined in `docs/style/doc-style.md`

Pass raw trailing CLI args into the running program:

```bash
python3 -m genia.interpreter path/to/program.genia --pretty input.txt
```

Run inline source from the command line:

```bash
genia -c "[1,2,3] |> count"
```

Run a pipeline stage expression:

```bash
printf 'a\nb\n' | genia -p 'head(1) |> each(print)'
```

Pipe-mode mental model:

- `genia -p 'stage_expr'` behaves like `stdin |> lines |> <stage_expr> |> run`
- write one stage expression, not a full program
- do not write explicit `stdin` or explicit `run`
- ordinary stages lift over `some(x)` automatically, and lifted non-Option results are wrapped back into `some(...)`
- use explicit helpers such as `flat_map_some(...)`, `map_some(...)`, or `then_*` when you want direct Option-aware control
- raw values stay raw values, and `none(...)` skips the remaining stages
- reducers such as `sum` expect plain numbers after explicit filtering or recovery
- pipeline debug helpers are available as identity stages:
  - `inspect(value)` logs the current value and returns it unchanged
  - `trace(label, value)` logs a label plus value and returns value unchanged
  - `tap(fn, value)` runs `fn(value)` for side effects and returns value unchanged

Unix-style examples:

```bash
printf '  alpha  \n\n beta\n' | genia -p 'map(trim) |> filter((line) -> line != "") |> each(print)'
printf '10\noops\n20\n' | genia -p 'map((row) -> unwrap_or("bad", row |> parse_int |> flat_map_some((n) -> some(n + 1)))) |> each(print)'
printf '1\n2\n3\n4\n' | genia -c 'stdin |> lines |> scan((state, x) -> [state + x, state + x], 0) |> collect'
printf 'a b c d 5 x\n1 2 3 4 6 y\nshort\n' | genia -c 'stdin |> lines |> rules((r, _) -> split_whitespace(r) |> nth(4) |> parse_int |> flat_map_some(rule_emit)) |> collect |> sum'
printf '1\n2\n3\n' | genia -c 'stdin |> lines |> map(parse_int) |> keep_some |> collect |> trace("after parse") |> sum'
```

- use `-p` for stage expressions that still produce a flow
- use `-c` or a script when you want a final collected value such as `sum`

## CLI behavior contract

- mode selection:
  - `genia path/to/file.genia [args ...]` -> file mode
  - `genia -c 'source' [args ...]` -> command mode
  - `genia -p 'stage_expr' [args ...]` -> pipe mode
  - `genia` -> REPL mode

### Choose `-p` vs `-c`

| Goal | Use | Why |
| --- | --- | --- |
| Stream stdin rows through Flow stages and perform side effects | `-p` | `-p` injects `stdin |> lines` and final `run` |
| Produce a final value (for example `count`, `sum`, map/list result) | `-c` or file mode | you control full program shape and final materialization |
| Reuse file-based program logic with `main(argv())` dispatch | file mode | file mode supports trailing args and runtime `main` convention |
| Quick one-off expression/program from shell | `-c` | inline source without creating a file |

- mode boundaries:
  - file/command mode evaluate source, then dispatch `main(argv())` if `main/1` exists, else `main()` if `main/0` exists, else preserve the evaluated result
  - pipe mode never dispatches `main`; it always runs `stdin |> lines |> <stage_expr> |> run`
  - pipe mode rejects explicit `stdin` and explicit `run` in unbound stage usage
- args and errors:
  - trailing CLI args are available through `argv()` in file/command/pipe modes
  - option-like trailing args are preserved as plain strings (for example `--pretty`)
  - when no `-c` or `-p` mode is selected, the first non-mode argument must be a file path
  - use `--` to stop option parsing when a literal arg/path starts with `-`

## Canonical CLI tasks

```bash
# 1) line filtering
printf 'ok\nerror one\nwarn\nerror two\n' | genia -p 'filter((l) -> contains(l, "error")) |> each(print)'

# 2) trimming blank lines
printf '  alpha  \n\n beta\n' | genia -p 'map(trim) |> filter((line) -> line != "") |> each(print)'

# 3) extracting a field
printf 'a b c d five\n1 2 3 4 six\n' | genia -p 'map(split_whitespace) |> map((r) -> nth(4, r)) |> keep_some |> each(print)'

# 4) parse/filter/sum pipeline
printf 'a b c d 5 x\n1 2 3 4 6 y\nshort\n' | genia -c 'stdin |> lines |> rules((r, _) -> split_whitespace(r) |> nth(4) |> parse_int |> flat_map_some(rule_emit)) |> collect |> sum'
```

```bash
# 5) command mode with main(argv()) dispatch
genia -c 'main(args) = args' --pretty input.txt
```

```genia
# 5b) file mode with main(argv()) dispatch
main(args) = args
```

```bash
genia script.genia --pretty input.txt
```

Run the ants demos:

```bash
python3 -m genia.interpreter examples/ants.genia
python3 -m genia.interpreter examples/ants_terminal.genia --ants 10
```

Run the HTTP service demo:

```bash
python3 -m genia.interpreter examples/http_service.genia --port 8080
```

The demo serves:

- `GET /health` -> plain-text `ok`
- `GET /info` -> JSON service metadata

`examples/ants_terminal.genia` uses the current terminal helper surface (`clear_screen`, `move_cursor`, `render_grid`) plus ordinary CLI args. It is still a blocking text demo, not a `stdin_keys`-driven real-time game loop.

## Build a Game in Genia

`examples/zip_json_puzzle.genia` shows how to build a small puzzle game around Genia’s JSON, ZIP, and pipeline helpers.

The game reads a puzzle archive, lets the player provide a transformation pipeline, and validates the transformed JSON against the expected result stored in the puzzle metadata.

Run the briefing for a puzzle zip:

```bash
python3 -m genia.interpreter examples/zip_json_puzzle.genia puzzle.zip
```

Play it with a pipeline:

```bash
python3 -m genia.interpreter examples/zip_json_puzzle.genia puzzle.zip --pipeline 'pick:rows,field:label,trim_each,drop_empty,upper_each'
```

Trace each stage and write a result archive:

```bash
python3 -m genia.interpreter examples/zip_json_puzzle.genia puzzle.zip --pipeline 'pick:rows,field:label,trim_each,drop_empty,upper_each' --trace --out solved.zip
```

The example uses:

- `zip_read` to load `puzzle.json` and the input payload from the archive
- `json_parse` / `json_stringify` to move between zip bytes and puzzle data
- named stage application to build a player-defined pipeline
- `trace` to debug puzzle loading and each pipeline stage
- `zip_write` to emit `summary.txt`, `actual.json`, and `expected.json` when `--out` is provided

Puzzle format and stage vocabulary are documented in `examples/zip_json_puzzle.md`.

Run tests:

```bash
pytest -q
```

Test suite note:

- `tests/cases/` holds reusable black-box language-semantic cases
- pytest files keep host/runtime-substrate coverage that is still specific to the Python reference host

## Documentation

Published documentation is deployed with GitHub Pages from the `main` branch at:

- `https://m0smith.github.io/genia-2026/`

The published site includes the repo homepage, current state/rules/runtime references, the book, the cheatsheets, host-interop docs, and a top-level `SICP with Genia` section sourced from `docs/sicp/`.

To preview locally:

```bash
uv sync --dev
uv run python tools/stage_docs_for_mkdocs.py
uv run mkdocs serve --strict
```

To validate the published-learning-doc surfaces locally:

```bash
uv run pytest -q tests/test_cheatsheet_*.py tests/test_sicp_code_blocks.py tests/test_book_chapter_status_sections.py
uv run mkdocs build --strict
```

The MkDocs build uses a temporary staged docs tree so the repo’s source-of-truth markdown can stay where it already lives, including the SICP chapter sources under `docs/sicp/`.

LLM instruction sync note:

- shared cross-tool LLM guidance lives in `docs/ai/LLM_CONTRACT.md`
- tool-specific instruction files should stay thin and point back to `GENIA_STATE.md`, `GENIA_RULES.md`, and `AGENTS.md`
- CI validates that these instruction files stay synchronized

## Core IR Layer

Genia lowers parsed source into a small host-neutral Core IR before evaluation.

This IR is meant to be:

- simple enough for future hosts to consume
- explicit about semantic structure
- separate from execution strategy

The frozen minimal portable Core IR node/pattern families are documented in `docs/architecture/core-ir-portability.md`.

Small schematic example:

```text
source: 3 |> inc |> double
ast:    Binary(Binary(Number(3), PIPE_FWD, Var("inc")), PIPE_FWD, Var("double"))
ir:     IrPipeline(source=IrLiteral(3), stages=[IrVar("inc"), IrVar("double")])
```

Option constructors are also explicit in the lowered IR:

```text
some(1)                  -> IrOptionSome(IrLiteral(1))
none("parse-error", ctx) -> IrOptionNone(IrLiteral("parse-error"), <lowered ctx>)
```

The current Python host may still apply small post-lowering optimizations such as `IrListTraversalLoop`, but those optimized nodes are not the minimal portability contract.

Boundary validation note:

- lowered programs are validated against the minimal portable Core IR contract before host-local optimization in the current Python reference host

## Multi-Host Direction

Python is the only implemented host today, and it remains the current reference host.

The repo now also includes shared portability scaffolding for future hosts:

- host interop contract docs: `docs/host-interop/`
- Core IR portability note: `docs/architecture/core-ir-portability.md`
- shared spec scaffold + manifest: `spec/`
- host layout/migration notes: `hosts/`

Alignment rule:

- future hosts may differ internally
- they must preserve shared semantics, Core IR lowering meaning, and shared CLI/runtime behavior
- Core IR plus the shared spec infrastructure are the intended portability/alignment mechanisms
- planned hosts are not treated as implemented until code, tests, and capability status exist

Current host status:

| Host | Status |
| --- | --- |
| Python | Implemented reference host |
| Node.js / Java / Rust / Go / C++ | Planned / scaffolded only |

## Browser playground architecture

Browser playground architecture docs are now scaffolded under:

- docs/browser/README.md
- docs/browser/PLAYGROUND_ARCHITECTURE.md
- docs/browser/RUNTIME_ADAPTER_CONTRACT.md

Truthful status:

- implemented now: documentation and architecture/contract scaffolding only
- planned V1 runtime path: browser UI backed by the current Python reference host on a backend service
- planned later: browser-native runtime via a JavaScript host or Rust/WASM host behind the same runtime adapter boundary

Related shared portability docs:

- docs/host-interop/HOST_INTEROP.md
- docs/host-interop/HOST_PORTING_GUIDE.md
- docs/host-interop/HOST_CAPABILITY_MATRIX.md
- docs/architecture/core-ir-portability.md
- spec/README.md
- spec/manifest.json
- tools/spec_runner/README.md

## Language snapshot (implemented)

### Runtime value categories

- Core values: Number, Symbol, String, Boolean, Pair, `none` / `none(reason)` / `none(reason, context)` / `some(value)`, List, Map
  - `none` is shorthand for `none("nil")`
  - legacy surface `nil` also normalizes to `none("nil")`
- Function / module values: Function, Module
- Callable behaviors:
  - functions/lambdas are callable values
  - maps are callable lookup values
  - strings can act as callable map projectors
- Runtime capability values:
  - `stdout`
  - `stderr`
  - MetaEnv
  - Flow (runtime Phase 1 is implemented)
  - Ref
  - Process handle
  - Bytes wrapper
  - Zip entry wrapper

Current consistency note:

- absence semantics are now unified around `some(value)` and structured `none(reason, meta?)`
- plain `none` and legacy `nil` both evaluate to `none("nil")`
- canonical access/search APIs use the absence family directly:
  - `get`
  - `first`
  - `last`
  - `nth`
  - string `find`
  - list predicate-search helper `find_opt`
  - `parse_int`
- compatibility lookup surfaces such as `map_get`, callable map/string lookup, slash access, and `cli_option` now also return structured `none(...)` on missing results
- compatibility aliases retained:
  - `get?`
  - `first_opt`
  - `nth_opt`
- preferred modern absence style in new code:
  - `get`, `first`, `last`, `nth`, string `find`, `find_opt`
- direct pipelines short-circuit on `none(...)`, but they preserve explicit `some(...)`
- helpers such as `map_some`, `flat_map_some`, `then_get`, `then_first`, `then_nth`, and `then_find` remain useful for explicit Option values and higher-order code
- public String, Map, Ref, Process, and sink helper names are prelude-backed wrappers over host-backed runtime primitives
- the public Option helper surface remains help-visible through prelude/autoload metadata, while canonical `some(...)` / `none(...)` constructor forms also lower explicitly in Core IR
- public Flow helper names `lines`, `rules`, `each`, `collect`, and `run` are also prelude-backed; the host keeps the lazy Flow kernel while `rules` orchestration/defaulting mostly live in prelude
- Flow reuse and invalid flow-source failures are surfaced as clear Genia-facing runtime errors rather than raw Python iterator errors
- `help()` now points users toward the public prelude-backed stdlib surface, while raw host-backed runtime names remain intentionally generic
- REPL/debug output now renders structured absence with visible context metadata, for example `none("missing-key", {key: "name"})`
- `some(pattern)`, `none(reason)`, and `none(reason, context)` are supported in pattern matching for Option values
- new `?`-suffixed APIs are boolean-returning; `get?` remains the current compatibility exception and `get` is the preferred maybe-aware lookup name
- Flow, MetaEnv, Ref, and Process handles are runtime values, but they are not plain data in the same sense as numbers/lists/maps

### Programs as Data

Genia has a minimal `quote(expr)` special form for syntax-as-data.

```genia
quote(x)
quote([a, b, c])
quote(1 + 2)
```

- `quote(x)` returns a symbol distinct from the string `"x"`
- `quote([a, b, c])` returns a pair chain of symbols ending in `nil`
- `quote(1 + 2)` returns `(app + 1 2)`, not `3`
- quoted source applications use `(app operator operand1 operand2 ...)`
- there is no `'x` shorthand in this phase

### Pairs and Lists

Genia also has immutable pairs for SICP-style data.

```genia
cons(1, 2)
cons(1, cons(2, nil))
```

- `car` and `cdr` access pair fields
- `pair?(x)` checks for pairs
- `null?(x)` checks for `nil`
- pair-built lists end in `nil`
- ordinary list literals remain separate list values in this phase

### Functions and lambdas

```genia
square(x) = x * x
inc = (x) -> x + 1
list = (..xs) -> xs
```

- functions are dispatched by name + arity shape (fixed arity preferred over varargs)
- varargs supported in named functions and lambdas via `..rest`
- `delay(expr)` creates a delayed promise value; `force(x)` forces promises and returns non-promises unchanged
- `quasiquote(expr)` constructs quoted data with selective evaluation via `unquote(...)`
  - `unquote_splicing(...)` is supported in quasiquoted list contexts
- quoted/quasiquoted data can now be inspected with the syntax helper prelude
  - `self_evaluating?`, `symbol_expr?`, `quoted_expr?`, `assignment_expr?`, `lambda_expr?`, `application_expr?`, `block_expr?`, `match_expr?`
  - selectors include `text_of_quotation`, `assignment_name`, `assignment_value`, `lambda_params`, `lambda_body`, `operator`, `operands`, `block_expressions`, `match_branches`, `branch_pattern`, `branch_has_guard?`, `branch_guard`, `branch_body`
  - parser/quote substrate stays host-backed, while most user-facing structural selectors now live in `src/genia/std/prelude/syntax.genia`
- Genia also now includes a minimal phase-1 metacircular evaluator over quoted expressions
  - environment helpers: `empty_env`, `lookup`, `define`, `set`, `extend`
  - evaluator entry: `eval(expr, env)`
  - `apply(proc, args)` still applies ordinary callables and now also applies metacircular compound procedures and metacircular matcher procedures
  - metacircular env/runtime substrate stays host-backed, while dispatch/helper glue live in `src/genia/std/prelude/eval.genia`
- named functions may include optional docstring metadata:
  - example:
    ```genia
    inc(x) = """
    # inc

    Increment by one.
    """ x + 1
    ```
  - `help(name)` renders docstrings with lightweight Markdown-aware formatting
  - official style guide: `docs/style/doc-style.md`
- closures are supported
- `name = expr` also works as lexical assignment in blocks
  - it rebinds the nearest existing lexical name when present
  - otherwise it defines a name in the current scope
  - function parameters are assignable
  - assignment is limited to simple names in this phase
- calls in tail position are guaranteed to run in constant stack space
- promises are separate from Flow
  - promises are memoized delayed ordinary values
  - Flow remains the single-use pipeline/runtime stream model
- stdlib streams are implemented on top of pairs + promises
  - `stream_cons`, `stream_head`, `stream_tail`, `stream_map`, `stream_take`, `stream_filter`
  - streams are pure delayed data and remain separate from Flow

### Pattern matching

```genia
head(xs) =
  [x, .._] -> x
```

Supported pattern forms:

- literals (`0`, `"ok"`, `true`, legacy `nil`)
- option patterns (`none`, `some(pattern)`)
- glob string patterns (`glob"..."`) for whole-string string matching
- variable bindings
- wildcard `_`
- tuple patterns (`(a, b)`)
- list patterns (`[x, ..rest]`)
- map patterns (`{name}`, `{name: n}`, `{"name": n}`; partial by default)
- map pattern shorthand is identifier-only (`{"name"}` shorthand is invalid; use `{"name": n}`)
- guards (`pattern ? condition -> result`)
- duplicate bindings (`[x, x]` only matches equal values)

### Conditionals in Genia

- Genia does **not** use `if` or `switch`
- all conditional logic is expressed with function-based pattern matching
- pattern matching is the only branching mechanism

### Case placement rules

Case expressions are valid only:

- as a function body
- as the final expression in a block

### Lists and spread

```genia
[1, ..[2, 3], 4]
add(..[20, 22])
```

- list literal spread is implemented
- function call argument spread is implemented

### Map literals

```genia
person = { name: "Matthew", age: 42 }
point = { "x": 10, "y": 20 }
empty = {}
```

- identifier keys in literals are sugar for string keys
- trailing commas are supported
- duplicate keys are deterministic last-one-wins


### Modules (Phase 1)

```genia
import math
import math as m

[math/pi, m/inc(2)]
```

- `import mod` binds a module value to `mod`
- `import mod as alias` binds the same module value to `alias`
- module imports are cached by module name (`loaded_modules`) so duplicate imports are not re-evaluated
- module exports are accessed with narrow slash access (`mod/name`)
- modules are immutable runtime namespace values (distinct from maps)

### Python host interop (Phase 1, allowlisted)

Genia currently reuses the existing module system for a minimal Python-only host bridge.
There is no new member-access syntax for this.

```genia
import python
import python.json as pyjson
```

- supported host modules in this phase:
  - `python`
  - `python.json`
- supported root exports:
  - `python/open`, `python/read`, `python/write`, `python/close`
  - `python/read_text`, `python/write_text`
  - `python/len`, `python/str`
  - nested `python/json/loads`, `python/json/dumps`
- host imports are allowlisted; `import python.os` is rejected
- host functions participate in ordinary calls and Option-aware pipelines
- host `None` maps to Genia `none`
- host exceptions remain explicit errors rather than turning into success values

Working examples:

```genia
import python
"file.txt" |> python/open |> python/read
```

```genia
import python.json as pyjson
unwrap_or("fallback", "null" |> pyjson/loads)
```

```genia
import python
[1, 2, 3] |> python/len
```

Failure example:

```genia
import python.json as pyjson
"{" |> pyjson/loads
```

- raises `ValueError("python.json/loads invalid JSON: ...")`

### Named slash access (`/`)

```genia
person = { name: "Matthew", age: 42 }
[person/name, person/age, person/middle]
```

- map named access returns the value when present
- missing map keys return `none("missing-key", {key: "middle"})`
- module named access returns exported bindings
- missing module exports raise a clear error
- `/` access is narrow: only `lhs/name` (bare identifier RHS), not general member/index access
- map slash access is still supported for compatibility, but new code should prefer canonical maybe-aware lookup:

```genia
get("name", person)
```

### Pipeline operator (Phase 2)

```genia
[1, 2, 3] |> map(inc)
```

- `|>` now evaluates as an Option-aware pipeline stage operator
- AST lowering preserves pipelines explicitly in Core IR as `IrPipeline(source, stages)` rather than nested calls
- ordinary stage call shape is preserved:
  - `x |> f` calls `f(x)`
  - `x |> f(y)` calls `f(y, x)` (append piped value as final argument)
- left-associative chaining is supported (`a |> f |> g`)
- multiline formatting around `|>` is supported:
  ```genia
  value
    |> f
    |> g
  ```
- Option propagation is built into pipeline evaluation:
  - if a stage input is `none(...)`, remaining stages do not execute and the same `none(...)` is returned
  - if a stage input is `some(x)` and the stage is not explicitly Option-aware, the stage receives `x`
  - when that lifted stage returns a non-Option value `y`, the pipeline wraps it back into `some(y)`
  - when that lifted stage returns `some(...)` or `none(...)`, that Option result is preserved as-is
- pipeline-visible function modes are now interpreted as:
  - Value -> Value
  - Flow -> Flow
  - explicit Value <-> Flow bridge
- recovery/defaulting should wrap the whole pipeline result:
  - `unwrap_or("unknown", record |> get("user") |> get("name"))`
  - `unwrap_or(0, fields(row) |> nth(5) |> parse_int)`
- reducers stay explicit:
  - `sum` expects plain numbers, so filter/recover Option values before `collect |> sum`
- Flow is still explicit:
  - Flow values move through pipelines only when explicit bridge/stage functions such as `lines`, `collect`, and `run` are used
  - there is no implicit Value↔Flow conversion

### Flow runtime (Phase 1)

```genia
stdin |> lines |> take(2) |> each(print) |> run
```

- `stdin |> lines` creates a lazy, pull-based, single-use Flow
- Flow is a runtime value produced/consumed by flow builtins; it is not a separate syntax category
- public flow helpers from `src/genia/std/prelude/flow.genia`: `lines`, `keep_some_else`, `rules`, `each`, `collect`, `run`
- the host Flow kernel stays intentionally small:
  - lazy pull/consume and single-use enforcement
  - source-bound stdin integration
  - sink/materialization boundaries
- reusable pipeline stages are ordinary functions of shape `(flow) -> flow`
- `keep_some_else(stage, dead_handler)` is an explicit dead-letter Flow stage for Option-returning item transforms:
  - `stage` receives the original raw item
  - `some(v)` continues on the main flow as `v`
  - `none(...)` drops that item from the main flow and calls `dead_handler(original_item)`
  - ordinary `|>` semantics stay unchanged outside this helper
- `keep_some(flow)` / `keep_some(stage, flow)` are the keep-only forms:
  - they unwrap `some(v)` to `v`
  - they drop `none(...)`
- `rules(..fns)` is a stateful rule-driven stage over any incoming Flow:
  - each rule runs as `(record, ctx)`
  - `ctx` starts as `{}` and persists across items
  - `rules()` is the identity stage
  - orchestration, defaulting, and most contract validation now live in prelude/Genia code
- `take` stops upstream pulling as soon as the limit is satisfied
- `take` / `head` and quiet broken-pipe termination stop generator-backed upstream work promptly
- `collect(flow)` materializes reusable data, while `run(flow)` drives effects to completion
- `stdin()` remains separate and returns a cached list of full stdin lines for non-stream use
- `-p` / `--pipe` wrap a stage expression as `stdin |> lines |> <stage_expr> |> run` for ergonomic Unix pipeline use
- `-p` expects a stage expression only; omit explicit `stdin` and `run`
- no `pipe(...)` helper function exists in this phase

### Output sinks (Phase 1)

```genia
write(stdout, "a")
writeln(stderr, "oops")
flush(stdout)
```

- `stdout` and `stderr` are first-class host-backed sink values
- public helpers from `src/genia/std/prelude/io.genia`: `write`, `writeln`, `flush`
- `write(sink, value)` writes display-formatted output with no newline
- `writeln(sink, value)` writes display-formatted output with a trailing newline
- `flush(sink)` flushes a sink and returns `none("nil")`
- `print(...)` writes to `stdout`, and `log(...)` writes to `stderr`
- `input()` remains independent of `stdin`
- broken pipe on `stdout` output in Unix pipelines is treated as normal downstream termination
- flow-driven stdout writes use the same quiet broken-pipe path

### Concurrency and cells

```genia
counter = cell(0)
cell_send(counter, (n) -> n + 1)
cell_get(counter)
```

- public helpers from `src/genia/std/prelude/process.genia`: `spawn`, `send`, `process_alive?`
- `spawn(handler)` creates a host-thread worker with FIFO mailbox
- `send(process, message)` enqueues messages
- `process_alive?(process)` reports worker liveness
- prelude provides `cell`, `cell_with_state`, `cell_send`, `cell_get`, `cell_state`, `cell_failed?`, `cell_error`, `restart_cell`, `cell_status`, `cell_alive?`
- cells are fail-stop:
  - failed updates preserve last successful state
  - failed cells cache an error string and reject future `cell_send` / `cell_get`
  - `restart_cell(cell, new_state)` clears failure and discards queued pre-restart updates in this phase

## Builtins

### Core

- direct runtime names: `log`, `print`, `input`, `stdin`, `stdout`, `stderr`, `help`
- public flow helpers from `src/genia/std/prelude/flow.genia`: `lines`, `rules`, `each`, `collect`, `run`
- public sink helpers from `src/genia/std/prelude/io.genia`: `write`, `writeln`, `flush`
- special form: `quote(expr)`
- pair builtins: `cons`, `car`, `cdr`, `pair?`, `null?`
- `help(name)` prints named-function/prelude metadata when available (`name/shape`, source if available, rendered docstring, or undocumented fallback)
- `help()` prints a compact overview of the public prelude-backed stdlib families and canonical helpers, with representative family samples derived from autoload registrations
- `help("name")` can autoload registered prelude helpers before rendering their docstrings
- `help("name")` for raw host-backed names prints a generic bridge note rather than a separate host-specific doc registry
- stdlib prelude helpers include Markdown docstrings for learn-by-inspection via `help("name")`
- constants: `pi`, `e`, `true`, `false`, legacy alias `nil`
- option runtime + public helpers:
  - `none` remains a runtime literal/value
  - public helpers from `src/genia/std/prelude/option.genia`: `some`, `get`, `get?`, `map_some`, `flat_map_some`, `then_get`, `then_first`, `then_nth`, `then_find`, `unwrap_or`, `is_some?`, `is_none?`, `some?`, `none?`, `or_else`, `or_else_with`, `absence_reason`, `absence_context`
- canonical maybe-returning list/search helpers: `first`, `last`, `nth`, `find` (string search), `find_opt` (predicate search)
- compatibility aliases: `first_opt`, `nth_opt`
- canonical pipeline style now prefers direct absence-aware stages such as `get`, plus explicit chaining helpers like `then_first`, `then_nth`, `then_find`, and `flat_map_some(...)` when the next stage needs the inner value of `some(...)`
- explicit helpers such as `map_some`, `flat_map_some`, `then_get`, `then_first`, `then_nth`, and `then_find` remain useful for direct Option values, higher-order code, and non-pipeline composition
- flow runtime (Phase 1): `lines`, `keep_some_else`, flow-aware `map`/`filter`, `take`, `rules`, `each`, `collect`, `run`, plus prelude `head` aliases and rule helper constructors `rule_skip`, `rule_emit`, `rule_emit_many`, `rule_set`, `rule_ctx`, `rule_halt`, `rule_step`

### CLI args / options (runtime layer)

- `argv()` is the raw host-backed CLI primitive and exposes trailing CLI args as a plain list of strings
- public CLI helpers now live in `src/genia/std/prelude/cli.genia`
- `cli_parse(args)` and `cli_parse(args, spec)` return `[opts_map, positionals]`
- `cli_flag?(opts, name)`, `cli_option(opts, name)`, `cli_option_or(opts, name, default)` help read options cleanly
- host-side CLI support is intentionally small: raw `argv()`, spec normalization/validation, token character decomposition, and deterministic CLI-specific error raising
- no `$1`/`$2` syntax is added; positional arguments are list-pattern friendly

## CLI Programs (`main` Entrypoint Convention)

In file mode (`genia path/to/program.genia`) and command mode (`genia -c "..."`), Genia checks for `main` after top-level evaluation:

1. `main/1` → called as `main(argv())`
2. else `main/0` → called as `main()`
3. else → no implicit entrypoint call

`main` is a runtime convention, not syntax.

Pipe mode (`genia -p "..."` / `genia --pipe "..."`) is separate:

1. it wraps the provided stage expression as `stdin |> lines |> <stage_expr> |> run`
2. it does not apply the `main` convention
3. it rejects explicit `stdin` and explicit `run` inside the provided stage expression

Example (`main/1` + list pattern matching):

```genia
main(args) =
  [] -> print("usage") |
  ["hello", name] -> print("Hello " + name) |
  _ -> print("unknown command")
```

Example (`main/0`):

```genia
main() = print("Hello world")
```

### Refs

- public helpers from `src/genia/std/prelude/ref.genia`: `ref`, `ref_get`, `ref_set`, `ref_is_set`, `ref_update`

### Strings

- public helpers from `src/genia/std/prelude/string.genia`: `byte_length`, `is_empty`, `concat`, `contains`, `starts_with`, `ends_with`
- `find`, `split`, `split_whitespace`, `join`
- `trim`, `trim_start`, `trim_end`, `lower`, `upper`
- `parse_int`
- these remain thin wrappers over the same host-backed string runtime behavior

Examples:

```genia
parse_int("42")
parse_int("ff", 16)
```

- returns `some(int)` on success
- returns `none("parse-error", context)` for invalid integer text
- base 10 by default
- explicit base supported in `2..36`
- surrounding whitespace is ignored

### Pipeline migration note

Old helper-heavy style:

```genia
record |> get("user") |> then_get("name") |> or_else("unknown")
```

New canonical style:

```genia
unwrap_or("unknown", record |> get("user") |> get("name"))
```

Old parse pipeline:

```genia
nth(5, fields(row)) |> map_some(parse_int) |> unwrap_or(0)
```

New canonical style:

```genia
unwrap_or(0, fields(row) |> nth(5) |> parse_int)
```

Short design note: [docs/architecture/pipeline-option-redesign.md](docs/architecture/pipeline-option-redesign.md)
Integration note: [docs/architecture/pipeline-ir-host-integration.md](docs/architecture/pipeline-ir-host-integration.md)
- non-string input and invalid bases still raise explicit errors

### Concurrency

- public helpers from `src/genia/std/prelude/process.genia`: `spawn`, `send`, `process_alive?`

### Simulation primitives (Phase 2)

- `rand()` returns a float in `[0, 1)`
- `rand_int(n)` returns an integer in `[0, n)` for positive integer `n`
- `sleep(ms)` blocks for `ms` milliseconds
- intentionally simple: no scheduler, no async/await, no event loop

### Bytes / JSON / ZIP bridge builtins (Phase 1)

- `utf8_encode(string) -> bytes`
- `utf8_decode(bytes) -> string`
- `json_parse(string) -> value | none("json-parse-error", context)`
- `json_stringify(value) -> string | none("json-stringify-error", context)`
- `json_pretty(value) -> string | none(...)` (compatibility alias for `json_stringify`)
- `read_file(path) -> string | none(...)`
- `write_file(path, string) -> path | none(...)`
- `zip_read(path) -> flow | none(...)`
- `zip_write(path, flow_or_list) -> path | none(...)`
- `zip_write(path) -> stage` (pipeline stage form)
- `zip_entries(path) -> list of zip entries`
- `zip_write(entries, path) -> path` (also accepts `(path, entries)` for pipeline style)
- `entry_name(entry)`, `entry_bytes(entry)`, `set_entry_bytes(entry, bytes)`, `update_entry_bytes(entry, f)`, `entry_json(entry)`

This is a minimal host-backed bridge for pipeline-first archive transforms; it is **not** the full Flow runtime system.

Example archive rewrite pipeline (list-based in this phase):

```genia
rewrite_entry(entry) =
  entry ? entry_json(entry) ->
    update_entry_bytes(entry, compose(utf8_encode, json_pretty, json_parse, utf8_decode)) |
  _ -> entry

rewrite_zip(in_path, out_path) =
  zip_entries(in_path)
    |> map(rewrite_entry)
    |> zip_write(out_path)
```

Flow-native zip pipeline example:

```genia
rewrite_item(item) =
  ([name, content]) ? ends_with(name, ".json") -> [name, json_parse(utf8_decode(content)) |> json_stringify |> utf8_encode] |
  ([name, content]) -> [name, content]

zip_read("in.zip")
  |> map(rewrite_item)
  |> zip_write("out.zip")
```

File API example:

```genia
text = read_file("input.json")
result = text |> json_parse |> json_stringify
write_file("output.json", unwrap_or("{}", result))
```

### Phase 1 persistent associative maps

- public helpers from `src/genia/std/prelude/map.genia`: `map_new`, `map_get`, `map_put`, `map_has?`, `map_remove`, `map_count`
- implemented as an opaque host-backed runtime wrapper (no map syntax added)
- persistent semantics from Genia perspective (`map_put`/`map_remove` return new map values)

## Autoloaded stdlib highlights

- list helpers: `list`, `first`, `rest`, `append`, `length`, `reverse`, `reduce`, `map`, `filter`, `nth`, `take`, `drop`, `range`, ...
- canonical maybe-returning list/search helpers: `first`, `last`, `nth`, `find` (string search), `find_opt` (predicate search)
- compatibility aliases: `first_opt`, `nth_opt`
- fn helpers: `apply`, `compose`
- map helpers: `map_new`, `map_get`, `map_put`, `map_has?`, `map_remove`, `map_count`
- ref helpers: `ref`, `ref_get`, `ref_set`, `ref_is_set`, `ref_update`
- process helpers: `spawn`, `send`, `process_alive?`
- sink helpers: `write`, `writeln`, `flush`
- math helpers: `inc`, `dec`, `mod`, `abs`, `min`, `max`, `sum`
- awk-ish helpers: `awkify`, `awk_filter`, `awk_map`, `awk_count`, `fields`
- cells: `cell`, `cell_with_state`, `cell_send`, `cell_get`, `cell_state`, `cell_failed?`, `cell_error`, `restart_cell`, `cell_status`, `cell_alive?`

## Not implemented yet

- quote sugar (`'x`)
- macros
- general unrestricted host interop / FFI
- general member access / indexing syntax
- full flow system beyond Phase 1 (async scheduling, multi-port stages, richer cancellation/backpressure controls)
- full Flow system (stages/sinks/backpressure/multi-port pipelines)
- language-level scheduler/event loop for simulations

For stricter implementation details and invariants, see:

- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
