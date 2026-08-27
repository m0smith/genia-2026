# Genia — Compiler & Language Invariants (Current)

These are implementation invariants that contributors should preserve.

## 1) Expression vs case grammar separation

- Case syntax (`->`, `?`, `|`) is not a normal infix-expression system.
- Parser must only parse case arms in explicit case contexts.

## 2) Case placement (hard constraint)

Case expressions are valid only:

- as full function bodies
- as the final expression in a block

Parser must reject case syntax in subexpressions, call arguments, list elements, and non-final block positions.

## 3) One case expression per block

- A block may include zero or more ordinary expressions.
- If a case expression appears, it must be the final expression.

## 4) Full tuple match model

Pattern matching always targets the full argument tuple.

- `f(x)` still matches a one-item tuple target.
- Multi-arg functions are tuple-pattern sugar, not a separate mechanism.
- Lambda parameter patterns also match the full argument tuple, but lambdas remain single-arm.

## 5) Arrow disambiguation by parse context

`->` means:

- lambda arrow in expression parsing
- case arm mapping in case parsing

Do not resolve this via precedence hacks.

## 6) Pattern validity rules

Supported patterns:

- literal
- glob string pattern (`glob"..."`)
- Outcome constructor pattern (`some(pattern)`, `none(...)`, `err(reason)`, context-aware forms)
- variable binding
- wildcard `_`
- tuple pattern
- list pattern with optional rest
- map pattern (string-keyed entries; partial-by-default)
- named reusable pattern (`Name(inner_pattern)`) — Experimental

Required constraints:

- list rest pattern (`..name` / `.._`) is valid only in final list-pattern position
- map pattern shorthand is valid only for identifier keys (`{name}`), not string keys (`{"name"}` requires `:`)
- parser ignores newlines between list-pattern delimiters and items
- duplicate names in a pattern require equality at match time
- lambda parameter position may use existing pattern forms; it must not introduce multi-arm lambda syntax
- glob patterns match only string values and must match the entire string
- glob pattern syntax supports only:
  - `*`, `?`, `[abc]`, `[a-z]`, `[!abc]`
  - escapes: `\*`, `\?`, `\[`, `\]`, `\\`
- malformed glob classes must raise deterministic syntax errors

## 6.1) Named reusable pattern invariants (Experimental)

- `pattern Name(value) = body` declares a named pattern at top level with exactly one matcher parameter
- `pattern Name() = body` and `pattern Name(a, b) = body` must fail at parse time (arity error)
- `Name(inner_pattern)` in pattern position is the use form; only one nested pattern argument is supported
- `Name()` and `Name(a, b)` in pattern position must fail at parse time (use arity error)
- `some`, `none`, and `err` in pattern position remain built-in Outcome constructor patterns; named pattern resolution does not apply to them
- the matcher body must return one of `some(...)`, `none(...)`, or `err(...)`; any other return value is a runtime error
- `some(payload, context?)` means match success; the pattern engine continues matching `inner_pattern` against `payload`
- `none(reason, context?)` means pattern miss; dispatch tries the next arm
- `err(reason, context?)` must NOT be treated as a miss; it surfaces as the dispatch result without trying later arms
- a name bound to an ordinary function used in named-pattern position must fail with a deterministic runtime error
- an unknown name used in named-pattern position must fail with a deterministic runtime error
- named pattern declarations bind `Name` in the normal lexical environment; no separate pattern namespace is introduced
- named patterns are valid in the same pattern positions as other implemented pattern forms
- recursive named pattern definitions are not supported in this phase

## 6.2) Template invariants (Experimental)

- a Template is an ordinary callable value accepting one subject and returning an Outcome; it does not create a separate runtime category or namespace
- a named reusable pattern value is directly callable and may be stored, passed, returned, imported, and used by higher-order functions
- direct calls return `some(...)`, `none(...)`, or `err(...)` unchanged; in particular, a transformed `some(payload)` remains observable
- direct calls returning a non-Outcome must fail with `named pattern <Name> returned non-Outcome value`
- ordinary call arity rules apply to direct Template calls
- matcher operators keep their section 9.7 behavior: `@?` and `@!` retain the original subject on success, and `&` applies both matchers to the original subject
- named-pattern use keeps section 6.1 behavior and matches its nested pattern against the `some(...)` payload
- `refinement_match(predicate, value)` returns `some(value)` only when its callable predicate returns `true`; `false` returns `none("refinement-mismatch")`, and a non-boolean predicate result is misuse
- `open_shape_match(fields, value)` requires an ordinary string-keyed map of callable Templates; declared fields are required, extras are allowed and preserved, and success returns the original complete map
- open-shape specification validation and field matching follow specification insertion order; non-map and missing-field mismatches are `none`, while nested Template `none`/`err` values propagate unchanged
- `exact_shape_match(fields, value)` uses the same field-Template specification but requires equal candidate/specification key sets; it returns distinct `none` mismatches for non-map, first missing, and first extra fields
- exact matching validates the specification first, checks missing fields in specification order, checks extras in candidate order, and only then invokes field Templates in specification order; equal key sets match regardless of insertion order
- a nested field Template success payload establishes compatibility but never transforms the subject
- open and exact structural helpers are distinct: open allows extras, exact rejects them; neither adds nominal identity, copying, layout, or positional/labeled shapes
- `json_schema(schema)` requires one outer `json`-represented schema map and returns an Outcome containing an ordinary callable Template; the supported vocabulary is closed to required `type`, plus type-appropriate `properties`, `required`, `items`, and boolean `additionalProperties`
- compiled schema Templates preserve the original subject on success; object checks run required names, forbidden extras, then present declared properties in their defined orders, and array checks run by increasing index
- unsupported schema keywords and malformed supported-keyword shapes are deterministic compile-time `err` Outcomes; schema compiler input-shape/facet violations are runtime misuse, and unsupported keywords are never ignored
- no implicit Template application, metadata behavior, structural declaration syntax, nominal shape category, or representation behavior is introduced

## 6.3) Carrier representation invariants (Experimental)

- `represent(facet, value)` requires a non-empty string and adds exactly one outer facet without mutating the carried value
- facets are ordered nested layers; order and duplicate layers participate in equality
- represented values are unequal to their unrepresented carried values
- a represented map key is supported only when its carried value is supported by ordinary map-key rules; its frozen key remains distinct from the carried key
- `representation_match(facet, value)` returns `some(carried)` for the exact outer facet and `none("representation-mismatch")` for an ordinary value or another outer facet; it never searches inner layers
- a named Template returning `representation_match(...)` composes through existing `Name(inner)`, `@?`, `@!`, and `&` rules; nested pattern matching consumes only the explicitly matched layer
- `strip_representation(facet, value)` removes one exact outer layer; non-represented input and wrong outer facets are runtime misuse
- assignment, argument passing, return, collection/Sheet storage, pipeline transport, and Seq/Flow transport preserve the represented value unchanged
- operations deriving new values do not copy carrier facets unless their own separately approved contract says so
- generic represented values render as `<represented>` for both display and debug; facet names and carried payloads are not exposed
- carrier representation is distinct from the existing rendering/Format system and introduces no JSON, secret protection/declassification, new syntax, or Core IR node

## 7) Spread semantics

- list literal spread requires list value at runtime
- call argument spread requires list value at runtime
- spreading non-list values must raise `TypeError`

## 8) Function resolution invariants

- fixed-arity match is preferred over varargs match
- varargs ambiguity must raise `TypeError("Ambiguous function resolution")`
- named-function groups may carry one canonical docstring:
  - no docstrings => undocumented
  - one docstring total => valid
  - repeated identical docstrings => valid
  - conflicting docstrings => clear `TypeError`

## 8.1) Named function docstring parse invariant

- parser may treat a string literal as function docstring metadata only for named function definitions after `=`
- supported docstring string literals include ordinary quoted strings and triple-quoted multiline strings
- the docstring is metadata, not a runtime expression
- after docstring metadata, the function body may be either a normal expression or the same parenthesized case-expression form accepted for ordinary function bodies
- lambdas do not support docstrings
- docstring text is interpreted as Markdown for `help(...)` display with lightweight formatting only (no full Markdown engine)

## 8.1.1) Prefix annotation parse invariant

- prefix annotation syntax is:
  - `@name value`
  - `@name "string"`
  - `@name """multiline string"""`
- annotation values are parsed as ordinary expressions in this phase
- one or more consecutive top-level prefix annotation lines attach to the next bindable top-level form only
- currently supported annotation targets are:
  - named function definitions
  - top-level simple-name assignments
- annotations not followed by one of those bindable forms must raise a parse error
- parser must not silently drop parsed annotations
- parsed annotations are represented explicitly in the AST as:
  - `Annotation(name, value)`
  - `AnnotatedNode(annotations, target)`
- annotation metadata behavior is currently implemented only for:
  - `@doc`
  - `@meta`
  - `@since`
  - `@deprecated`
  - `@category`
  - `@test`
  - `@route` (Experimental, inert R8 descriptor metadata)
  - `@server` (Experimental, inert R8 server-configuration metadata)
- no annotation introduces macros, compile-time transforms, or syntax rewriting in this phase

## 8.1.2) Prefix annotation runtime semantics

- annotations attach to the binding name, not to an anonymous raw value detached from that binding
- annotated targets still evaluate normally first; annotation metadata is attached after the binding is created or updated
- `@doc`:
  - evaluates its value expression after the target binding exists
  - the resulting value must be a string
  - stores metadata under key `"doc"`
- `@meta`:
  - evaluates its value expression after the target binding exists
  - the resulting value must be a map
  - merges all map entries into the binding metadata
- `@since`:
  - evaluates its value expression after the target binding exists
  - the resulting value must be a string
  - stores metadata under key `"since"`
- `@deprecated`:
  - evaluates its value expression after the target binding exists
  - the resulting value must be a string
  - stores metadata under key `"deprecated"`
- `@category`:
  - evaluates its value expression after the target binding exists
  - the resulting value must be a string
  - stores metadata under key `"category"`
- `@test`:
  - evaluates its value expression after the target binding exists
  - the resulting value must be a string
  - stores metadata under key `"test"`
  - marks the annotated zero-argument function for native test discovery in native test mode
  - has no effect on language evaluation behavior outside native test mode
  - annotated functions with one or more parameters are a discovery error, not an evaluation error
  - duplicate native-test names across `@test` annotated functions and explicit `test(name, body)` registrations are discovery errors in native test mode
- `@route`:
  - evaluates its value expression after the target binding exists
  - is valid only on a top-level named function
  - requires the exact closed descriptor map and handler shape defined in section 25
  - stores the validated map under metadata key `route`
  - remains inert; evaluation and discovery do not start a listener or invoke the handler
  - may not repeat on one declaration or replace existing `route` metadata through annotated rebinding
- `@server`:
  - evaluates its value expression after the target assignment exists
  - requires a top-level simple-name assignment target
  - validates and normalizes the closed optional `host`, `port`, and `max_requests` configuration map recorded in `GENIA_STATE.md` section 9.7
  - attaches inert metadata under the canonical `server` key; the assignment value is not configuration
  - may not repeat on one declaration or replace existing `server` metadata through annotated rebinding
- `@cors`:
  - evaluates its value expression after the target assignment exists
  - requires a top-level simple-name assignment target and the closed optional `origin`, `methods`, and `headers` policy recorded in `GENIA_STATE.md` section 9.7
  - attaches inert metadata under the canonical `cors` key and must share the selected entry-file `@server` owner
  - uses the existing R7 `cors` policy validation/default contract and may not repeat on one declaration or replace existing `cors` metadata through annotated rebinding
- native test metadata keys and values must be strings; non-string metadata keys or values in a `TestUnit` are discovery errors reported before test body execution; diagnostics use Genia runtime type names; existing `TestUnit.location` is appended to diagnostic text when available
- multiple annotations merge from top to bottom
- last annotation wins for duplicate metadata keys, except annotated rebinding cannot replace an existing canonical R8 descriptor key such as `route`, `server`, or `cors`
- rebinding without annotations preserves existing binding metadata
- rebinding with annotations merges new metadata over existing metadata for that binding
- `doc("name")` returns the current doc string for a bound name or `none("missing-doc", {name: ...})`
- `meta("name")` returns the current metadata map for a bound name
- annotations not in the supported list above must fail clearly at runtime
- annotation metadata is ordinary runtime metadata only in this phase:
  - no macros
  - no compile-time transforms
  - no evaluator special forms beyond metadata attachment


## 8.2) Module import + module value invariants (phase 1)

- supported import forms are exactly:
  - `import mod`
  - `import mod as alias`
- imports bind only the module value in the current environment (no export splatting)
- module values are runtime namespace values distinct from maps
- module resolution is:
  - file-based for ordinary modules
  - allowlisted host-backed for the current Python host namespace (`python`, `python.json`)
- module loads are cached by module name (`loaded_modules`); duplicate imports/aliases must reuse the same module value instance
- top-level named assignments/functions from the module file are exported
- missing module files must raise a deterministic `FileNotFoundError("Module not found: <name>")`
- disallowed host module names must raise a deterministic `PermissionError("Host module not allowed: <name>")`
- module resolution order for user modules:
  - (1) requester-relative — `<requester-dir>/<mod>.genia` when the importing source has a known filesystem path
  - (2) BASE_DIR-relative — `<BASE_DIR>/<mod>.genia`
  - (3) packaged stdlib — bundled `std/prelude/<mod>.genia`
  - (4) raise `FileNotFoundError("Module not found: <mod>")`
- requester-relative resolution is skipped when the importing source filename is `<memory>` or `<command>`; when the filename is `<pipe>`, resolution proceeds from the current working directory
- import cycle detection must raise `RuntimeError("Module import cycle detected while loading <mod>")`; the cycling module must not be committed to the cache

## 8.2.1) Python host interop invariants (phase 1)

- Python host interop reuses the existing module system and narrow dot export access.
- There is no additional member-access syntax for host interop in this phase.
- supported host modules are currently allowlisted:
  - `python`
  - `python.json`
- current Python root host exports are:
  - `open`
  - `read`
  - `write`
  - `close`
  - `read_text`
  - `write_text`
  - `len`
  - `str`
  - nested `json` submodule
- current `python.json` exports are:
  - `loads`
  - `dumps`
- host module exports participate in ordinary calls and pipelines through the existing callable model.
- boundary conversion rules in this phase are:
  - Genia string/number/bool -> Python scalar
  - Genia list -> Python list (recursive)
  - Genia map -> Python dict (recursive)
  - Genia `some(x)` -> converted host value for `x`
  - Genia `none(...)` -> Python `None`
  - Python `None` -> Genia `none("nil")`
  - Python list/tuple -> Genia list (recursive)
  - Python dict -> Genia map (recursive)
- host resource results that cannot be represented as plain Genia data may appear as opaque Python handle values.
- host exceptions must not be silently converted to success values.
  - ordinary host failures currently propagate as explicit Python-host errors
  - host `None` results are the only automatic none-mapping path in this phase
- current normalized bridge example:
  - `python.json/loads` raises `ValueError("python.json/loads invalid JSON: ...")` for invalid JSON text
- pipeline interaction at the bridge still uses ordinary pipeline semantics:
  - `some(x) |> python.len` passes `x` into the host export through ordinary host-boundary conversion
  - `none(...) |> python.len` skips the host export and preserves the same `none(...)`
  - Flow does not implicitly cross the bridge; passing a Flow to a host value export remains a type error unless an explicit Flow stage has already materialized ordinary values
- unrestricted host import, arbitrary attribute access, and arbitrary code execution are not part of this phase.

## 8.2.2) Autoload loading path invariants

- autoload loading is a separate loading path from user module imports
- autoloads are keyed by `(name, arity)` and triggered lazily on first name lookup miss in the root environment
- loaded exports bind directly into the root environment; no module value is created and no module cache entry is written
- autoload deduplication uses a separate file-key set, independent of the `loaded_modules` cache
- autoload cycle detection must raise `RuntimeError("Autoload cycle detected while loading <key>")`
- autoloads are stdlib-internal infrastructure; they are not accessible through module named access (`mod.name`) and are not part of the user-facing module system

## 8.3) Assignment invariants

- `name = expr` defines or rebinds a lexical name.
- If `name` already exists in the reachable lexical environment chain, assignment updates the nearest existing binding.
- Otherwise assignment creates `name` in the current scope.
- Function parameters are ordinary assignable lexical bindings.
- Closures observe rebinding through captured lexical environments.
- Assignment is limited to simple names in this phase.
- Invalid targets such as `(a + b) = 3` must raise `SyntaxError("Assignment target must be a simple name")`.
- Module evaluation keeps its own module environment boundary, so module top-level assignment must not rebind names in the importing root environment.
- Builtin/root names are not protected from rebinding inside the same root environment in the current implementation.

## 8.3.1) Named function definition surface forms

- named function definitions currently accept:
  - `name(args) = expr`
  - `name(args) -> expr`
  - `name(args) { ... }`
- only the `=` form may carry named-function docstring metadata in this phase

## 8.4) Core IR portability invariants

- Core IR is the semantic portability boundary, while parser AST shape is host-local.
- The frozen minimal portable Core IR contract is documented in `docs/architecture/core-ir-portability.md`.
- AST->IR lowering output must stay inside the frozen portable `Ir*` node families.
- Host-local post-lowering optimized nodes (for example `IrListTraversalLoop`) are allowed only after host-local optimization passes and are not part of the minimal shared Core IR contract.
- Dot is the canonical named-access separator: `lhs.name` lowers as `IrBinary(op=SLASH, named_access=true)`. `named_access=true` is part of the portable Core IR contract and is emitted in normalized shared IR. Ordinary slash/division lowers as `IrBinary(op=SLASH)` without `named_access`. This is narrow named access, not general field-path lookup, and hosts must not introduce a separate access node. Legacy `lhs/name` compatibility has been removed.
- `none(reason, ctx)` lowers as `IrOptionNone`; the reason argument is wrapped in `IrQuote` (not evaluated) — bare `none` produces `reason=null`.
- `IrAssign` appears directly in `IrBlock.exprs`; it is not wrapped in `IrExprStmt`.

## 9) Operator model

Implemented operators are limited to:

- unary: `-`, `!`
- binary: `+ - * / % < <= > >= == != && ||`
- pipeline: `|>`
- named accessor form: canonical `lhs.name` (RHS bare identifier only)
- matcher operators (Experimental): `@?`, `@!`, `&` — see section 9.7

Pipeline invariant:

- `|>` is a dedicated pipeline evaluation form in this phase
- AST lowering keeps pipelines explicit in Core IR as one source plus an ordered stage list
  - pipelines are not lowered into nested ordinary call nodes
- ordinary call shape is preserved:
  - `x |> f` calls `f(x)`
  - `x |> f(y)` calls `f(y, x)` (append source value as final arg)
  - `x |> expr` calls `expr(x)` when `expr` is valid in ordinary call-callee position
  - example: `record |> "name"` behaves like `"name"(record)`
- chaining is left-associative
- newlines may appear immediately before `|>` and immediately after `|>` in ordinary expression parsing
- Option propagation is part of pipeline evaluation:
  - if a stage input is `none(...)`, the remaining stages do not execute and that same `none(...)` is returned
  - if a stage input is `some(x)` and the stage is not explicitly Option-aware, the stage receives `x`
- when that lifted stage returns a non-Option value `y`, the pipeline wraps it back as `some(y)`
- when that lifted stage returns `some(...)` or `none(...)`, that Option result is used as-is


## 9.7) Matcher operator invariants (Experimental)

These operators apply Outcome matcher functions. A matcher function is a callable value that accepts one argument and returns an Outcome (`some(...)`, `none(...)`, or `err(...)`).

### `@?` invariants

- `value @? matcher` calls `matcher(value)`; if result is `some(...)` → returns `some(value)` (original subject); if result is `none(...)` or `err(...)` → returns it unchanged
- `@?` must not coerce the Outcome to boolean
- `@?` must not expose the matcher's success payload; the original subject is the success value
- `@?` must not raise merely because the matcher returned `none(...)` or `err(...)`
- right operand not callable → runtime error
- matcher returns non-Outcome → runtime error

### `@!` invariants

- `value @! matcher` calls `matcher(value)`
- if result is `some(...)` → evaluates to `value` (original subject); matcher success payload is not exposed
- if result is `none(...)` → runtime error (`@! assertion failed: matcher returned none`)
- if result is `err(reason[, ctx])` → runtime error preserving reason (`@! assertion failed: matcher returned err: <reason>`)
- right operand not callable → runtime error
- matcher returns non-Outcome → runtime error

### `&` matcher composition invariants

- `matcher_a & matcher_b` evaluates to a new callable matcher function
- the composed matcher applies `matcher_a` first; if that succeeds, applies `matcher_b` to the original subject (not the matcher payload)
- if `matcher_a(value)` returns `none(...)` → return that `none(...)` without calling `matcher_b`
- if `matcher_a(value)` returns `err(...)` → return that `err(...)` without calling `matcher_b`
- if `matcher_a(value)` returns `some(...)` → call `matcher_b(value)` (original subject); if result is `some(...)` → return `some(value)`; propagate `none(...)` or `err(...)` unchanged
- composition is left-to-right and deterministic
- context merging across composed success is not implemented in this phase
- either operand not callable → runtime error at composition time
- either matcher returns non-Outcome at invocation time → runtime error
- `&` for matcher composition is distinct from `&&` (boolean and); non-matcher operands are a runtime error


## 10) Observable Spec Contract (Current Implemented Scope)

- Shared semantic-spec cases define observable behavior only for categories and scope implemented and recorded in `GENIA_STATE.md` (currently: `eval`, `ir`, `cli`, first-wave `flow`, initial `error`, and initial `parse` are active; focused core stdlib list/Flow coverage for `map`, `filter`, `first`, `last`, and `nth` is included in the eval and flow categories)
- Current shared eval and cli cases assert:
  - `stdout`
  - `stderr`
  - `exit_code`
- Current shared cli cases cover deterministic non-interactive file, command, and pipe modes; REPL is not covered by shared executable specs
- Current shared ir cases compare normalized portable Core IR
- Determinism in the current shared semantic-spec scope means:
  - eval and cli asserted outputs must match exactly after newline normalization
  - the runner must not trim or reinterpret meaningful whitespace
- Expanding shared semantic-spec coverage beyond that scope requires implementation plus `GENIA_STATE.md` updates first
- Flow remains explicit:
  - pipeline evaluation does not create implicit Value→Flow conversions
  - flow values still come from explicit bridge/stage functions such as `lines`, `evolve`, `collect`, and `run`
  - tail position propagates through the final pipeline stage


Slash accessor invariants (phase 1):

- `lhs.name` is canonical narrow named access, not general member access or field-path lookup
- legacy `lhs/name` compatibility has been removed
- only module values and map values are valid LHS kinds
- for maps: missing key returns `none("missing-key", {key: <name>})`
- for modules: missing export raises a clear error
- non-identifier RHS forms are invalid for named access
- arithmetic division `/` remains available and unchanged for ordinary arithmetic contexts

No additional member/index/flow operators should be introduced without explicitly updating state/rules docs and tests.

## 9.1) Tail-call guarantee

- Genia guarantees proper tail-call optimization for function calls in tail position.
- A tail-position call must execute in constant stack space.
- Current runtime implementation uses an explicit trampoline in the evaluator rather than relying on Python recursion.
- Tail position currently includes:
  - the direct result of a function body
  - the result expression of a selected case arm
  - the final expression in a block
  - the final pipeline stage after `|>` lowering
- Non-tail calls are unchanged and may still consume Python stack space.

## 9.2) Symbols and quote

### Explicit configuration acquisition (Experimental)

- `config_provider`, `config_get`, `config_get_or`, `secret_get`, `secret_get_or`, and `protected_match` are ordinary calls; they add no syntax, annotation behavior, or Core IR node.
- source descriptor kinds must be explicit symbols produced with `quote(values)` or `quote(environment)`; no global `values` or `environment` binding is introduced.
- `sources` must be an explicit list ordered highest to lowest precedence; the first snapshot containing the key wins.
- provider construction must validate every descriptor and every literal key/value before acquiring any host-backed snapshot.
- literal and host-backed sources must be copied during construction; providers are immutable and lookup must not access or refresh host state.
- configuration keys must be non-empty strings containing no NUL; acquired values are exact strings and empty is present.
- found returns `some(exact_string)`; absent returns `none("config-missing")` without context.
- `config_get_or` returns a found `some(...)` unchanged, including `some("")`; only `none("config-missing")` invokes its zero-argument default, exactly once.
- an ordinary default result is wrapped once in `some(...)`; a default Outcome is preserved unchanged. Non-callable or wrong-arity defaults are runtime misuse only when missing selects the default branch.
- conversion is explicit through an ordinary Outcome-returning callable; validation uses existing callable Templates and existing Outcome-aware pipeline propagation.
- `secret_get(provider, key, purpose)` requires a non-empty purpose symbol and protects a found exact string, including empty, in exactly one reserved `secret` carrier.
- `secret_get_or(provider, key, purpose, default)` invokes the default exactly once only for missing; ordinary/`some` successes are protected once, `none`/`err` are preserved, and a success already containing protection is runtime misuse.
- `protected_match("secret", value)` returns `some(value)` with the exact protected subject; ordinary/non-secret values return `none("representation-mismatch")`; other facets are runtime misuse.
- generic `represent`, `representation_match`, and `strip_representation` must reject the reserved `secret` facet.
- protected equality uses provider identity, purpose, and carried-value equality without revealing them; protected values must not be map keys.
- transport preserves exact protected leaves without tainting containers; unsupported ordinary derivation uses existing type failure.
- diagnostic renderers recursively substitute exactly `<protected>`; this redaction does not authorize output.
- Format replacements, output sinks, JSON encoding, Sheet CSV rendering, resource writes, HTTP responses, and ordinary host conversion must reject recursively before effects; `json_encode` returns `err("protected-value", {operation: "json-encode"})`.
- `declassify(authority, protected_value)` is the sole reveal operation; authority must be host-injected, match provider identity, and allow the protected purpose.
- successful declassification removes one protected layer, audits before returning, and yields an ordinary value without hidden taint; failed matching reveals nothing.
- declassification authority is opaque, noncopyable, nonserializable, and rejected from ordinary output, storage, process, and host-data boundaries.
- unavailable environment capability returns `err("config-source-unavailable", {source_index})`; acquisition failure returns `err("config-provider-failure", {source_index})`.
- normalized acquisition failures and runtime misuse must not include the key, source contents, raw value, or raw host failure.
- providers are opaque identity values: display/debug is `<config-provider>` and ordinary map-key, host-conversion, and serialization boundaries reject them.
- execution modes must not construct an ambient provider or authority; file, command, pipe, import, native-test, and serve-entry evaluation preserve the same explicit values and Outcomes as ordinary evaluation.
- imports acquire configuration only when evaluated module code explicitly constructs and uses a provider; annotations do not acquire or inject configuration.
- serve startup must finish entry evaluation and explicit snapshot construction before listener activation; request handling performs no automatic refresh.
- there is no ambient lookup or implicit environment fallback. Implicit conversion/coercion, new Template/validation semantics, and annotation injection remain unimplemented.

### AI model invocation, Flow conversation, and validated-pipeline composition (Experimental R11 E11-1 through E11-8)

- `model(provider, config, credential, authority)` is an ordinary call and returns an ordinary one-argument callable; it adds no syntax, annotation behavior, AST form, or Core IR node.
- `provider` must be an opaque host-injected model-provider capability, `credential` must be protected, and `authority` must be a declassification authority. `config` must be exactly `{id, timeout_ms}`, with a nonempty string id and an integer timeout in `1..300000`.
- Calling the model requires exactly `{messages, output}`. Messages must be a nonempty list of exact `{role, content}` maps; roles are `system`, `user`, or `assistant`, and request content is exactly `{kind: quote(text), text: string}`. Output is exactly `{kind: quote(text)}` or `{kind: quote(json), schema, template}`.
- Structured `schema` must have one outer R9 `json` representation and be accepted by existing `json_schema`; `template` must be an explicit callable one-argument Outcome Template. Both are validated before declassification or an attempt.
- Request validation, including recursive protected-value rejection, occurs before declassification, audit, or provider attempt. Construction performs none of those effects.
- After validation, the protected credential is declassified with the supplied authority and must reveal a string. The provider is then attempted synchronously exactly once. No retry, fallback, queue, or timeout executor is implied.
- Accepted success is `some` of exact `{message, finish_reason, usage}`: assistant message; finish reason `stop|length|filtered|other`; and either `some({input_tokens, output_tokens, total_tokens})` with nonnegative integers whose total is the sum, or context-free `none("model-usage-unavailable")`. Text output keeps text content. JSON output strictly decodes the single provider text through existing `json_decode`, applies the Template once to the carried ordinary value, and retains the original represented value as `{kind: quote(json), value}`; a Template success payload does not transform it.
- Accepted absence is context-free `none("model-no-response")`.
- Accepted errors are exact: `model-timeout` with `{timeout_ms}` equal to config; `model-rate-limited` with `{retry_after_ms: some(nonnegative integer)|none("model-retry-after-unavailable")}`; `model-rejected` or `model-transport-failure` with `{kind: authentication|permission|policy|request|unavailable|other}`; `model-response-invalid` with `{stage: message|finish_reason|usage|provider_response}`; and `model-structured-output-invalid` with `{stage: json_decode|template, outcome: original none|err}`.
- A structured Template returning a non-Outcome is runtime callback misuse. Structured processing performs no repair, extraction, coercion, second parse, reprompt, partial acceptance, or retry.
- Malformed observations normalize to response-invalid; provider exceptions normalize to transport-failure/other and their text must not escape.
- E11-3 also permits one explicitly host-constructed Python Gemini REST capability. It uses direct standard-library `v1beta models.generateContent`, sends the declassified credential only as `x-goog-api-key`, refuses redirects, and makes one attempt with the configured timeout; provider wire details are not portable semantics.
- Automated Gemini adapter tests use an injected fake transport. No provider SDK, ambient binding, source-visible factory, general HTTP API, provider discovery, retry/fallback, tools, agents, streaming, conversation runtime, or retrieval is implemented.
- Shared eval, error, Flow, and CLI cases may explicitly select the private deterministic `r11_model` test fixture. That harness selection is not a CLI flag or runtime binding; ordinary command, file, pipe, import, native-test, and serve execution remain without ambient model capabilities.
- E11-5 conversation state is an exact ordinary map with ordered `messages`, nonnegative `turn`, `active|stopped|failed` status, and the exact last Outcome. Input is an exact ordinary user-message or stop map supplied by an external list or Flow.
- An application step over active message input appends the user message, invokes `prompt(messages)` and the model once, increments the turn, preserves the exact model Outcome, and appends one assistant message only for `some(response)`. Existing `apply_raw` is required when application code intentionally dispatches a `none` Outcome as data instead of allowing ordinary Option short-circuiting.
- Active stop and all later stopped/failed inputs make no model call. Stop preserves turn/history and records `none("conversation-stopped", {reason})`; terminal states remain unchanged.
- Existing `scan` is the sole composition mechanism: list and Flow inputs produce equivalent consumed state sequences, Flow remains lazy/single-use, and the initial state is not emitted. No conversation runtime, input producer, hidden memory, retry/reprompt/tool loop, or new Flow termination helper is added.
- E11-6 composes existing JSONL parsing and record validation before the ordinary model stage, so malformed/blank/invalid records create existing diagnostics and make no model attempt. Structured successes retain one R9 `json` representation and existing `collect_validated` separates them from existing normalized diagnostics.
- The proving case uses explicit ordinary model configuration and explicitly injected R10 protected credential/authority/provider values. At most one attempt occurs for each valid invocation; normalized failure, invalid structured output, Template mismatch, and protected-boundary failure add no retry, repair, reprompt, fallback, or new error/diagnostic shape.
- E11-7 changes no semantics; it verifies runnable public examples and synchronizes the implemented E11-1 through E11-6 behavior, maturity, portability, and exclusions.
- E11-8 changes no semantics; it completes the release truth audit and distillation. R11 is release-complete, while these APIs remain Experimental, Python remains the only implemented host, and shared/multi-host conformance remains Partial.

### Document chunking and exact provenance (Experimental R12 E12-1)

- `chunk(chunker, document)` is an ordinary two-argument call and adds no syntax, annotation, AST/Core IR node, capability, or pipeline rule.
- `document` must be exactly `{id, text, meta}`: nonempty string id, string text, and one outer `json` representation carrying an existing R9 JSON-domain ordinary object. Missing/extra keys or malformed fields are runtime misuse.
- `chunker` must be callable. After document and callability validation it is invoked exactly once with `document.text`; an exception propagates as callback misuse and a non-list result is callback-contract misuse.
- Every returned list item must be exactly `{offset, length}`. Both values are integers excluding booleans; offset is nonnegative, length is positive, and `offset + length` may not exceed the original text's Unicode-code-point length.
- The first malformed or out-of-bounds span returns `err("chunk-invalid", {stage: quote(span), index})` with its zero-based list index; no partial success list is returned.
- Successful chunks preserve span order and are exactly `{text, source, meta}`. Text is the original code-point slice, source is exactly `{doc_id: document.id, offset, length}`, and meta is the exact represented document value without unwrap, copy, merge, augmentation, or rewrap.
- Overlapping and repeated spans are valid. Any valid document may return zero chunks as `some([])`; no positive-length span is valid for empty text.
- The chunker cannot provide text, document identity, source, or metadata. No provider call, credential, authority, declassification, embedding, indexing, retrieval, reranking, grounding, or citation behavior participates.

### Unified corpus/query embedding (Experimental R12 E12-2)

- `embed(provider, config, credential, authority)` returns an ordinary one-argument callable. Construction validates and captures values but performs no declassification, audit, or provider attempt.
- Config is exactly `{id, space, timeout_ms}` with nonempty string id/space and a non-boolean integer timeout in `1..300000`.
- Input is exactly `{kind: quote(chunk), chunk}` or `{kind: quote(query), text}`. Query text is nonempty; chunk is the exact E12-1 value. Queries never fabricate chunk provenance.
- Locally invalid public shapes and protected ordinary input fields are runtime misuse and make no attempt. A malformed nested chunk returns `err("chunk-invalid", {stage: quote(document)})` before declassification or attempt.
- A valid call declassifies the captured protected string immediately before one synchronous attempt through the exact matching R10 `quote(embed_call)` authority. There is no retry, fallback, hidden batching, stream, cache, or background work.
- Success corresponds exactly to input kind and preserves the exact original chunk/text. Embeddings are exactly `{vector, dims, space}` with a nonempty finite-number vector excluding booleans, positive non-boolean dims equal to vector length, and exact configured space.
- Malformed provider success/observations normalize to exact non-sensitive `embed-response-invalid` stages; approved embed timeout/rate-limit/rejection/transport errors use the R12 contract contexts. Provider exceptions become one `embed-transport-failure` with `kind: quote(other)`.
- The deterministic Python fixture is explicit, opaque, offline, non-ambient, and source cannot construct it. No network embed adapter, retrieval, reranking, grounding, implicit query embedding, persistence, or provider registry is implemented; indexing is the separate E12-3 boundary below.

### Indexing capability and opaque handle (Experimental R12 E12-3)

- `index(provider, config, credential, authority)` returns an ordinary one-argument callable. Construction validates exact `{id, timeout_ms}` config and captured capability/protected credential/authority without declassification, audit, or attempt.
- Invocation requires a nonempty list of exact embedded chunks. Every vector must be valid, and all embeddings must share exact `dims` and `space`; mixed values return exact `index-embedding-incompatible` errors before declassification.
- A valid call declassifies immediately before one synchronous attempt through exact matching R10 `quote(index_call)` authority. There is no retry, fallback, exposed batching, stream, cache, or background work.
- Success is only `some(index_handle)`. The opaque host-produced handle renders `<index-handle>` and cannot be constructed, inspected, compared, keyed, copied, serialized, or persisted by source.
- Provider errors normalize to the exact R12 index families without provider bodies or identities. The deterministic Python fixture is offline, explicit, non-ambient, and introduces no vector database or public storage API.
- Retrieval, `k`, reranking, grounding, persistence, networking, provider registry, and source-visible compatibility identity remain unimplemented.

- symbols are runtime values distinct from strings
- `quote(expr)` is a special form, not an ordinary function call
- `quote(expr)` must not evaluate `expr`
- `quote(expr)` currently converts syntax to data with these core rules:
  - identifier -> symbol
  - number / string / boolean / `nil` / `none` -> corresponding literal runtime value
  - list literal -> pair chain ending in `nil`
  - map literal -> map of quoted keys and quoted values
  - unary / binary / call forms -> tagged application pair chain `(app <operator> <arg1> ...)`
- quoted identifier map keys remain symbols; quoted string map keys remain strings
- symbol values print as bare names and are stable map keys
- there is no `'x` quote sugar in this phase

## 9.2.1) Quasiquotation

- `quasiquote(expr)` is a special form that constructs the same runtime data shapes as `quote(expr)`.
- `quasiquote(expr)` must not eagerly evaluate ordinary subexpressions.
- `unquote(expr)` evaluates `expr` and inserts the result at the nearest active quasiquote depth.
- Nested quasiquote depth is significant:
  - nested `quasiquote(...)` increases depth
  - `unquote(...)` only activates at the nearest surrounding quasiquote
- `unquote_splicing(expr)` is implemented only in quasiquoted list literal contexts.
- `unquote_splicing(expr)` currently accepts:
  - ordinary list values
  - `nil`
  - nil-terminated pair chains
- invalid splice values must raise clear `TypeError`
- `unquote(...)` and `unquote_splicing(...)` outside quasiquote must raise clear runtime errors
- `quasiquote(unquote_splicing(...))` is invalid because splicing requires a quasiquoted list context

## 9.2.2) Programs-as-data helpers

- Genia provides a small stdlib helper layer for inspecting quoted expressions.
- These helpers operate on the same runtime data representation produced by `quote(expr)` and `quasiquote(expr)`.
- the host-backed substrate in this phase remains intentionally small:
  - parser/lowering/quote representation
  - symbol/self-evaluating runtime shape detection
  - metacircular pattern-lowering support used by evaluator internals
- language-visible selectors, structural helpers, and branch/match glue over quoted forms should prefer prelude/Genia code.
- Current stabilized quoted tags are:
  - `(quote <expr>)`
  - `(quasiquote <expr>)`
  - `(app <operator> <operand1> <operand2> ...)`
  - `(assign <name-symbol> <value-expr>)`
  - `(lambda <params-structure> <body-expr>)`
  - `(block <expr1> <expr2> ...)`
  - `(match (clause <pattern> <result>) ...)`
  - `(match (clause <pattern> <guard> <result>) ...)`
- Current helper surface includes:
  - predicates: `self_evaluating?`, `symbol_expr?`, `tagged_list?`, `quoted_expr?`, `quasiquoted_expr?`, `assignment_expr?`, `lambda_expr?`, `application_expr?`, `block_expr?`, `match_expr?`
  - selectors: `text_of_quotation`, `assignment_name`, `assignment_value`, `lambda_params`, `lambda_body`, `operator`, `operands`, `block_expressions`
  - match selectors: `match_branches`, `branch_pattern`, `branch_has_guard?`, `branch_guard`, `branch_body`
- Selectors must raise clear `TypeError` when used on the wrong expression kind.
- Application expressions are represented explicitly as `(app ...)`.
- Ordinary quoted pair/list data remain plain pair/list data and must not be classified as applications.
- `operands(expr)` returns the operand tail of the tagged application as a pair-chain sequence.
- `match_branches(expr)` returns the branch tail of `(match ...)` as a pair-chain sequence.
- `branch_guard(branch)` raises a clear `TypeError` when the branch is not guarded.

## 9.2.3) Metacircular evaluation

- Genia provides a minimal phase-1 metacircular evaluator over quoted expressions.
- evaluator dispatch and helper glue are exposed through prelude in this phase, while host code keeps the metacircular environment/runtime substrate.
- Public evaluator/environment names are:
  - `empty_env`
  - `lookup`
  - `define`
  - `set`
  - `extend`
  - `eval`
  - `apply`
- `eval(expr, env)` currently supports only:
  - self-evaluating literals
  - symbol expressions
  - quoted expressions
  - assignment expressions
  - lambda expressions
  - match/case expressions
  - application expressions
  - block expressions
- `eval(expr, env)` must follow current lexical scoping rules through metacircular environments:
  - `define` binds in the current frame
  - `set` rebinds the nearest existing lexical name or creates in the current frame when missing
  - `extend` creates a child lexical environment
  - closures capture the defining environment
- metacircular compound procedures are represented as tagged pair data:
  - `(compound <params> <body> <env>)`
- metacircular matcher procedures are represented as tagged pair data:
  - `(matcher <match-expr> <env>)`
- `apply(proc, args)` must preserve current ordinary callable behavior and additionally apply metacircular compound procedures and metacircular matcher procedures.
- current limitations:
  - the evaluator is only defined for the supported expression families above
  - unsupported quoted forms must fail clearly instead of pretending broader evaluator coverage

## 9.3) Pairs

- pairs are immutable two-field runtime values created with `cons`
- `car` returns the head field
- `cdr` returns the tail field
- `pair?(x)` reports whether a value is a pair
- `null?(x)` reports whether a value is the normalized empty-pair terminator (`none("nil")`, including legacy `nil`)
- pair equality is structural
- lists built from pairs are chains of pairs ending in `nil`
- ordinary list literals remain list values in this phase; they do not lower to pairs

## 9.4) Promises

- `delay(expr)` is a special form, not an ordinary function call.
- `delay(expr)` must not evaluate `expr` eagerly.
- `delay(expr)` creates a promise value that captures the current lexical environment in the same way closures do.
- `force(value)` forces a promise once and memoizes the successful result.
- `force(value)` returns non-promise values unchanged.
- If promise forcing raises, the promise remains unforced and later `force(...)` calls retry evaluation.
- Promises are ordinary delayed values and are separate from Flow.
- Promise forcing is explicit only; no automatic forcing is introduced in this phase.

## 9.5) Streams

- Streams are a stdlib abstraction, not a runtime value family.
- A stream node is built from Pair + Promise:
  - `cons(head, delay(tail_expr))`
  - prelude construction is exposed as `stream_cons(head, tail_fn)`
- Stream tails are forced explicitly with `stream_tail(s)` / `force(cdr(s))`.
- Current public stream helpers are `stream_cons`, `stream_head`, `stream_tail`, `stream_map`, `stream_take`, and `stream_filter`.
- `stream_take(n, s)` materializes the first `n` items as an ordinary list.
- Streams remain distinct from Flow:
  - streams are pure delayed data
  - Flow is the runtime pipeline/IO model

## 9.6) Option / absence semantics

This section is the complete contract for how absence values behave in Genia.

### 9.6.1) Outcome forms

The Outcome value family has three forms:

- `some(value)` / `some(value, context)` — a present value with optional context metadata
- `none(reason)` / `none(reason, context)` — a structured absence
  - bare `none` and legacy `nil` both normalize to `none("nil")`
  - `reason` is always a string
  - `context` is an optional map of metadata about the absence
  - metadata inspection helpers are:
    - `absence_reason(none(...))` -> `some(reason)`
    - `absence_context(none(...))` -> `some(context)` when present, otherwise `none("nil")`
    - `absence_meta(none(...))` -> `some({reason: ..., context: ...?})`
- `err(reason)` / `err(reason, context)` — a recoverable value-level failure (Experimental)
  - `err(...)` is not a runtime error; it is a normal Genia value
  - `err(...)` is not absence; `none?(err(...))` returns `false`
  - existing absence helpers do not treat `err(...)` as `none(...)`

### 9.6.2) Outcome propagation in pipelines (invariants)

- if a stage input is `none(...)`, the stage does not execute and the same `none(...)` is returned
- if a stage input is `err(...)`, the stage does not execute and the same `err(...)` is returned; `err(...)` is never automatically converted to `none(...)`
- if a stage input is `some(x)` and the stage is not explicitly Option-aware, the stage is invoked with `x`
- lifted stage results follow this rule:
  - non-Option result `y` becomes `some(y)`
  - Option/Outcome results (`some(...)` / `none(...)`) are propagated unchanged
- when lifting `some(x, context)`, context metadata is preserved in the result: `some(result, context)`
- if a stage produces a `none(...)` result, remaining stages do not execute
- structured none metadata (reason string + context map) passes through every skipped stage unchanged
### 9.6.3) Structured-none metadata invariant

Agents and implementations must preserve structured none metadata:

- `none("missing-key", { key: "user" }) |> f` → `none("missing-key", { key: "user" })` (not `none("missing-key")`)
- every stage skip must return the exact same `none(...)` value, not a new one

### 9.6.4) None-awareness: when a function receives none

- ordinary functions short-circuit on `none(...)` arguments (the call does not execute)
- a function explicitly handles absence when:
  - it is in `_NONE_AWARE_PUBLIC_FUNCTIONS`, or
  - at least one pattern arm matches `none(...)` or `none(reason, ctx)`, or
  - it is registered with `__genia_handles_none__ = True`
- handlers such as `some?`, `none?`, `unwrap_or`, `or_else`, `map_some`, `flat_map_some`, and all `then_*` helpers are explicitly none-aware

### 9.6.4.1) Explicit raw invocation: `apply_raw`

`apply_raw(f, args)` is a language-contract host primitive that calls `f` with the elements of list `args` as positional arguments without triggering the automatic `none(...)` short-circuit.

- `f` may be any Genia callable (named function, lambda, builtin)
- `args` must be a Genia list; a non-list second argument raises `TypeError`
- none values in `args` are delivered to `f` unchanged — the body executes
- exceptions raised inside `f` propagate through `apply_raw` unchanged
- the return value of `f` is returned as-is; no coercion or wrapping is applied
- `apply_raw` itself is subject to ordinary none-propagation: `apply_raw(f, none("x"))` short-circuits before `apply_raw` runs because `none("x")` is a direct argument to `apply_raw`
- use case: implementing higher-order functions (`reduce`, `map`, `filter`) that must deliver `none(...)` list elements to their callback

### 9.6.6) Debugging structured absence

Use structured none metadata directly instead of exceptions.

Examples:

- parse failure with reason-only metadata:
  - `none("parse_error")`
  - `absence_meta(none("parse_error"))` -> `some({reason: "parse_error"})`
- missing key with context metadata:
  - `none("missing_key", { key: "user" })`
  - `absence_meta(none("missing_key", { key: "user" }))` -> `some({reason: "missing_key", context: {key: "user"}})`
- pipeline propagation keeps metadata unchanged:
  - `none("index_out_of_bounds", { index: 9, length: 2 }) |> parse_int`
  - result is the same `none("index_out_of_bounds", { index: 9, length: 2 })`

### 9.6.5) Applying functions to Option-wrapped values

In direct calls, `some(x)` is still a normal value and is passed explicitly.
In pipelines, ordinary stages lift over `some(x)` automatically unless they are explicitly Option-aware.
Use explicit helpers when you want exact wrap/flat-map control regardless of stage detection:

| Goal | Helper |
|---|---|
| Apply plain `f` to inner value | `map_some(f, opt)` |
| Chain an Option-returning `f` | `flat_map_some(f, opt)` |
| Get a key from a map-or-Option | `then_get(key, target)` |
| Get first element of a list-or-Option | `then_first(target)` |
| Get nth element of a list-or-Option | `then_nth(index, target)` |
| Find substring in a string-or-Option | `then_find(needle, target)` |
| Recover with a default at pipeline end | `unwrap_or(default, opt)` |
| Recover with a fallback value | `or_else(opt, fallback)` |
| Recover with a lazy thunk | `or_else_with(opt, thunk)` |

Canonical pipeline patterns:

```
some("42") |> parse_int
```

Result: `some(42)` (stage receives `"42"`, result is already Option so it is preserved).

```
some(4) |> ((x) -> x + 1)
```

Result: `some(5)` (lifted stage result wraps back into `some(...)`).

```
some(4) |> unwrap_or(0)
```

Result: `4` (explicitly Option-aware stage receives the Option directly).

### 9.6.6) Some-lifting safety invariant

Automatic lifting applies only to pipeline stages that are not explicitly Option-aware.
Stages that explicitly handle Option values keep receiving Option values unchanged.
This protects helper-based and pattern-based Option handling from silent semantic drift.

## 10) Ref + concurrency runtime guarantees

- refs are synchronized host objects
- public ref helper names are exposed through thin prelude wrappers in `src/genia/std/prelude/ref.genia`
- public process helper names are exposed through thin prelude wrappers in `src/genia/std/prelude/process.genia`
- those wrappers are the canonical user-facing API surface for `help(...)` and higher-order use
- underlying ref/process behavior remains host-backed in this phase; wrappering does not change semantics
- process mailbox handling is FIFO per process
- one handler invocation at a time per process
- concurrency remains host-backed (threads), not language-scheduled
- cell helpers are runtime-backed in this phase and expose these public names:
  - `cell(initial)` / `cell_with_state(ref_value)`
  - `cell_send(cell, update)`
  - `cell_get(cell)` / `cell_state(cell)`
  - `cell_failed?(cell)` / `cell_error(cell)`
  - `restart_cell(cell, new_state)`
  - `cell_status(cell)` / `cell_alive?(cell)`
- cell invariants:
  - updates are asynchronous and serialized one at a time
  - last successful state is preserved
  - failed updates must not change state
  - failed updates mark the cell failed and cache an error string
  - failed cells reject future `cell_send` and `cell_get` with `RuntimeError`
  - queued updates after a failure are discarded
  - `restart_cell` clears failure, installs new state, and discards queued pre-restart updates in this phase
  - nested `cell_send` calls issued during an update are staged and are committed only if that update succeeds

## 11) Host-backed persistent map invariants

- persistent map runtime is shared by both map builtins and map literal/pattern syntax
- public map helper names are exposed through `src/genia/std/prelude/map.genia`
- those helper names are the canonical user-facing API surface for `help(...)` and higher-order use
- underlying persistent map runtime remains host-backed in this phase; helper exposure does not change semantics
- required builtins: `map_new`, `map_get`, `map_put`, `map_has?`, `map_remove`, `map_count`
- map values are opaque runtime wrappers, not exposed host objects
- `map_put` / `map_remove` must return new map values (no mutation of prior values)
- unsupported map input types and unsupported key types must raise clear `TypeError`
- `pairs(xs, ys)` is a public stdlib helper whose observable contract is independent of the persistent map runtime:
  - it accepts two list values
  - it returns a list of two-element list values `[x, y]`
  - it preserves input order
  - it stops at the shorter input
  - it returns `[]` when either input list is empty
  - first-argument non-list values must raise `TypeError("pairs expected a list as first argument, received <type>")`
  - second-argument non-list values must raise `TypeError("pairs expected a list as second argument, received <type>")`
  - it must not return host tuples, Pair values, Flow values, padded rows, or Option wrappers

## 11.1) Callable-data invariants (phase 1)

- ordinary call syntax may target map values and string values in these exact forms only:
  - `m(key)` / `m(key, default)` where `m` is a map value
  - `"key"(m)` / `"key"(m, default)` where first arg is a map value
- map-call and string-projector-call arity is restricted to 1 or 2; other arities raise clear `TypeError`
- missing map keys return `none("missing-key", {key: key})` unless an explicit default is provided in arity-2 form
- string projector with non-map target raises clear `TypeError`
- this does not add parser syntax, call operators, or user-defined callable-data protocols

## 11.2) Option invariants (phase 3 canonical access)

- primitive option values are:
  - `none`
  - `none(reason)`
  - `none(reason, context)`
  - `some(value)`
- public option helper names are exposed through thin prelude wrappers in `src/genia/std/prelude/option.genia`
- those wrappers are the canonical user-facing API surface for `help(...)` and higher-order use
- underlying option behavior remains host-backed in this phase; wrappering does not change semantics
- all `none...` forms belong to one absence family; reason/context are metadata, not a separate result kind
- `none` is shorthand for `none("nil")`
- legacy surface `nil` also evaluates to `none("nil")`; it is not a separate runtime absence value
- `reason` must be a string
- `context` must be a map when present
- key presence, not value truthiness, determines `some(...)` vs `none...`
  - key mapped to legacy `nil` still returns `some(none("nil"))`
- `get(key, target)` is the canonical maybe-aware lookup helper in this phase
- `get?(key, target)` is defined exactly as:
  - `get?(key, none) -> none`
  - `get?(key, none(reason)) -> none(reason)`
  - `get?(key, none(reason, context)) -> none(reason, context)`
  - `get?(key, some(map)) -> get?(key, map)`
  - `get?(key, map) -> some(value)` when key exists
  - `get?(key, map) -> none("missing-key", { key: key })` when key is missing
- `get(key, target)` has the same runtime behavior as `get?(key, target)`
- canonical list access helpers:
  - `first(list) -> some(value)` or `none("empty-list")`
  - `last(list) -> some(value)` or `none("empty-list")`
  - `nth(index, list) -> some(value)` or `none("index-out-of-bounds", { index: i, length: n })`
- canonical string search helper:
  - `find(string, needle) -> some(index)` or `none("not-found", { needle: needle })`
- canonical integer parsing helper:
  - `parse_int(string) -> some(int)` or `none("parse-error", context)`
  - `parse_int(string, base) -> some(int)` or `none("parse-error", context)`
- `find_opt(predicate, list)` is the canonical maybe-aware predicate-search helper for lists in this phase
- ordinary function calls propagate structured absence directly:
  - if any evaluated argument is `none(...)`, the call returns that same `none(...)`
  - the callee body is not evaluated unless the callee explicitly handles absence
- pattern matching supports:
  - literal `none`
  - structured none patterns `none(reason)` and `none(reason, context)`
  - constructor destructuring for `some(...)` with one inner pattern or `some(value, context)` context-aware form
  - `err(reason)` and `err(reason, context)` constructor patterns (Experimental)
  - context-aware patterns match only Outcome values that carry context
- in `none(reason)` and `none(reason, context)` patterns, the reason position matches the reason value directly; the context position uses normal pattern matching rules
- in `err(reason)` and `err(reason, context)` patterns, the reason position binds as a pattern variable
- `unwrap_or(default, opt)` accepts option values only
- `is_some?(opt)` / `some?(opt)` and `is_none?(opt)` / `none?(opt)` report option shape
- `or_else(opt, fallback)` returns the wrapped value for `some(value)` and the fallback for any `none...` form
- `or_else_with(opt, thunk)` returns the wrapped value for `some(value)` and calls `thunk()` only for `none...`
- `absence_reason(opt)` returns `some(reason)` for any `none...` value
  - because plain `none` normalizes to `none("nil")`, `absence_reason(none)` returns `some("nil")`
- `absence_context(opt)` returns `some(context)` only when context metadata is present
- `some?` / `none?` and `is_some?` / `is_none?` have the same runtime truth values; the shorter `some?` / `none?` names are preferred in docs/examples
- `map_some(f, opt)`:
  - returns `some(f(value))` for `some(value)`
  - returns the original `none...` unchanged for any absence value
- `flat_map_some(f, opt)`:
  - returns `f(value)` for `some(value)`
  - requires `f(value)` to be an Option value
  - returns the original `none...` unchanged for any absence value
- direct pipelines propagate `none(...)` automatically and lift ordinary stages over `some(...)`
- those helpers remain distinct for explicit wrap/flat-map control, higher-order use, and non-pipeline composition
- `then_get(key, target)` is a thin maybe-aware chaining helper over `get`
- `then_first(target)` is a thin maybe-aware chaining helper over `first`
- `then_nth(index, target)` is a thin maybe-aware chaining helper over `nth`
- `then_find(needle, target)` is a thin maybe-aware chaining helper over string `find`
- propagation helpers preserve the original structured `none(...)` unchanged unless they are explicit recovery/defaulting helpers
- expected absence remains data, not an exception
- runtime failures are not silently converted into `none(...)`
- new `?`-suffixed APIs must be boolean-returning
- maybe-returning APIs should prefer Option values and should not use `?`
- compatibility aliases retained in this phase:
  - `get?` for `get`
  - `first_opt` for `first`
  - `nth_opt` for `nth`
- compatibility aliases are expected to preserve the same outward behavior as their canonical target
- migration status labels used in docs:
  - `canonical`: preferred public API for new code
  - `compatibility alias`: thin wrapper/alias kept for migration stability
  - `compatibility surface`: behavior still supported but is no longer the preferred teaching path when a clearer helper exists
- book/readme/repl examples should prefer canonical maybe-aware access and direct absence-aware pipelines over helper-heavy chaining and compatibility lookup surfaces
- `get?` remains the current compatibility exception to that naming rule; `get` is preferred for new maybe-aware code
- pipeline behavior is now Option-aware directly
- canonical safe-chaining is therefore direct:
  - `record |> get("user") |> get("address") |> get("zip")`
  - `data |> get("items") |> then_nth(0) |> then_get("name")`
  - the first structured `none(...)` is preserved unchanged until an explicit recovery/defaulting helper wraps the final pipeline result
- explicit helpers such as `map_some`, `flat_map_some`, and `then_*` remain useful for direct Option values, higher-order code, and non-pipeline composition
- compatibility lookup surfaces now also return structured `none(...)` for missing results
- developer-facing presentation is separate from semantics:
  - REPL/debug output should preserve structured absence syntax and context metadata visibly
  - clearer rendering does not change evaluation behavior, matching rules, or error behavior

## 11.3) String builtin invariants

- public string helper names are exposed through thin prelude wrappers in `src/genia/std/prelude/string.genia`
- those wrappers are the canonical user-facing API surface for `help(...)` and higher-order use
- underlying string behavior remains host-backed in this phase; wrappering does not change semantics
- `find(string, needle)` returns:
  - `some(index)` when the substring exists
- `none("not-found", { needle: needle })` when the substring is missing
- `parse_int(string)` returns `some(int)` or `none("parse-error", context)`
- `parse_int(string, base)` does the same with explicit base in `2..36`
- `parse_int` ignores surrounding whitespace and supports leading `+` / `-`
- invalid integer text must return `none("parse-error", context)`
- non-string input must raise clear `TypeError`
- invalid base type must raise clear `TypeError`
- out-of-range base must raise clear `ValueError`

## 12) Error behavior

- unmatched function/case dispatch should raise deterministic runtime errors
- invalid grammar forms should fail during parse with syntax errors
- type-invalid builtins (e.g., non-list spread) should raise clear `TypeError`
- value-invalid builtins should raise clear `ValueError` where appropriate (e.g., `rand_int(0)`, `sleep(-1)`, invalid parse bases)

## 13) Simulation primitive builtins

- supported public randomness surface:
  - `rng(seed)`
  - `rand()`
  - `rand(rng_state)`
  - `rand_int(n)`
  - `rand_int(rng_state, n)`
  - `rand_flow(seed)` (experimental)
  - `rand_int_flow(seed, n)` (experimental)
- `sleep(ms)` remains a host-backed blocking builtin
- `rng(seed)` requires a non-negative integer seed and returns an explicit RNG state value
- `rand()` returns a host-RNG float in `[0, 1)` for convenience use
- `rand(rng_state)` returns `[next_rng_state, float]` deterministically from the explicit RNG state
- `rand_int(n)` requires a positive integer `n`, returns an integer in `[0, n)` for convenience use
- `rand_int(rng_state, n)` requires a valid RNG state and positive integer `n`, returns `[next_rng_state, int]` with the integer in `[0, n)`
- explicit seeded randomness is state-threaded and deterministic; the same seed must yield the same sequence
- the current Python host uses a simple fixed 32-bit LCG for the explicit seeded RNG
- `rand_flow(seed)` returns a lazy single-use Flow of floats in `[0, 1)`; seed must be a non-negative integer; raises `TypeError` for non-integer seed, `ValueError` for negative seed; Flow is unbounded
- `rand_int_flow(seed, n)` returns a lazy single-use Flow of integers in `[0, n)`; seed must be a non-negative integer and `n` a positive integer; invalid seed raises through `rng(seed)` at call time; invalid `n` raises through `rand_int(rng_state, n)` when the Flow is pulled; Flow is unbounded
- both `rand_flow` and `rand_int_flow` are pure Genia prelude wrappers; they obey the standard single-use Flow contract
- these are intentionally small runtime primitives only: no scheduler, no async/await, no event loop, no new syntax

## 14) Bytes / JSON / ZIP bridge invariants (host-backed only)

- bytes are runtime wrapper values (not string/list aliases)
- zip entries are runtime wrapper values with name + bytes payload
- required builtins:
  - `utf8_decode`, `utf8_encode`
  - internal JSON bridge primitives: `_json_parse`, `_json_stringify`
  - internal portable JSON boundary primitives: `_json_decode`, `_json_encode`, `_json_schema`
  - `zip_entries`, `zip_write`
  - `entry_name`, `entry_bytes`, `set_entry_bytes`, `update_entry_bytes`, `entry_json`
- public JSON helpers are prelude-backed wrappers in `src/genia/std/prelude/json.genia`:
  - `json_decode(string_or_bytes)` returns `some(represent("json", ordinary_value), context)` or a normalized `err(reason, context)` (**Experimental**)
  - `json_encode(value)` returns `some(deterministic_json_text, context)` or a normalized `err(reason, context)` (**Experimental**)
  - `json_schema(json_represented_schema)` returns `some(template, context)` or a normalized schema `err(reason, context)` (**Experimental**)
  - `json_parse(string)`
  - `json_stringify(value)`
  - `json_pretty(value)` compatibility alias for `json_stringify(value)`
- `zip_entries(path)` returns an eager list in this phase (not lazy flow semantics)
- `zip_write` preserves the order of entries it receives
- `json_parse` returns runtime map values for JSON objects
- JSON parse/stringify failures return structured `none(...)` values:
  - parse failures: `none("json-parse-error", context)`
  - stringify failures: `none("json-stringify-error", context)`
- the portable JSON boundary rejects duplicate object names, integers outside the exact interoperable range `[-9007199254740991, 9007199254740991]`, non-finite/overflow binary64 numbers, non-scalar Unicode, invalid UTF-8 byte input, and nesting beyond 128 containers
- `json_encode` supports ordinary JSON-domain values or exactly one outer `json` representation; it sorts object names, preserves list order, uses two-space indentation, and never silently strips another facet or coerces an unsupported value
- portable JSON data failures are `err`; `json_decode` input types other than string/bytes are runtime misuse; legacy JSON helpers remain unchanged
- this bridge does not introduce a generalized Flow system

## 15) Documentation + tests as contract

When changing syntax/semantics/runtime behavior, update together:

- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
- `README.md` for user-visible behavior
- corresponding tests under `tests/`

## 16) Conditional model invariant

- Genia has no conditional keyword (`if` or `switch`)
- branching is expressed only through pattern matching

## 17) CLI args + parsing invariants (runtime-only, list-first)

- raw process args are exposed via `argv()` as a list of strings (no `$1`/`$2` syntax)
- public CLI helper names are exposed through thin prelude wrappers in `src/genia/std/prelude/cli.genia`
- those wrappers are the canonical user-facing API surface for `help(...)` and higher-order use
- underlying host support is intentionally narrow in this phase:
  - raw `argv()`
  - spec normalization/validation
  - token character decomposition
  - deterministic CLI-specific error raising
- CLI parsing remains runtime/library behavior, not parser syntax
- `cli_parse` returns `[opts_map, positionals_list]` where `opts_map` is persistent (`map_put` semantics, last write wins)
- `cli_parse(args, spec)` accepts minimal map spec keys only:
  - `flags` (list of strings)
  - `options` (list of strings)
  - `aliases` (map of string->string)
- invalid CLI arg/spec/value types raise clear deterministic `TypeError`; ambiguous grouped short-option-with-value specs raise deterministic `ValueError`

## 18) Program entrypoint invariant (runtime convention only)

- `main` is not a keyword and introduces no parser syntax
- automatic entrypoint execution applies only in file mode and `-c` command mode
- entrypoint resolution order is exact arity:
  - prefer exact `main/1` and call it with `argv()`
  - else use exact `main/0`
  - else do nothing
- no partial matching/coercion is performed by the entrypoint selector

## 19) Flow runtime invariants (phase 1)

- pipeline operator semantics are Option-aware, but Flow remains explicit and runtime-level
- `stdin` may be used as a source value in pipelines; `input()` remains interactive-only
- public flow helper names are exposed through thin prelude wrappers in `src/genia/std/prelude/flow.genia`
- those wrappers are the canonical user-facing API surface for `help(...)` and higher-order use
- the host Flow kernel remains intentionally small in this phase:
  - lazy pull-based consumption
  - single-use enforcement
  - source-bound stdin/runtime integration
  - sink/materialization boundaries
- language-visible `rules` orchestration, defaulting, and most contract validation now live in prelude/Genia code
- the host rules kernel consumes normalized rule output from prelude and must not provide user-visible rule-result defaults itself
- phase-1 flow builtins:
  - sources/transforms: `lines`, `evolve(init, f)`, `map`, `filter`, `take`, `rules`
  - stdlib aliases over `take`: `head(flow)`, `head(n, flow)`
  - Seq-compatible sinks/materialization: `each`, `run`, `collect`, `reduce`, `count` accept list or Flow; non-list/non-Flow inputs fail with a Seq-compatible diagnostic
  - Seq-compatible transforms: `map`, `filter`, `take`, `drop` accept list or Flow and produce Seq-compatible diagnostics for invalid inputs; `scan` accepts list or Flow (`scan(list)` returns list, `scan(Flow)` returns Flow)
- flows are single-use:
  - first consumption succeeds
  - second consumption must raise `RuntimeError("Flow has already been consumed")`
- `take(n, flow)` must stop upstream pulling immediately after producing `n` items
- `evolve(init, f)` must emit `init` first and then call `f(previous_value)` only when downstream pulls later items
- `stdin |> lines` must remain lazy; binding the source must not force a full stdin read up front
- reaching EOF or a `take`/`head` limit is normal completion (not an error)

## 19.1) Seq compatibility invariants

- Seq is a semantic compatibility category for ordered value production, not a public runtime value, type constructor, syntax form, helper, or Core IR node.
- In this phase, only lists and Flow are Seq-compatible public values.
- Lists are eager and reusable.
- Flow is lazy, pull-based, source-bound, and single-use.
- Iterators and generators are host implementation details, not portable Genia values.
- Python reference-host internal lifecycle helpers for Seq-compatible sources must not create a public Seq surface.
- Seq compatibility does not change pipeline call shape.
- Seq compatibility does not change Option-aware pipeline behavior.
- No implicit list-to-Flow conversion is introduced.
- No implicit Flow-to-list conversion is introduced.
- Matching a Flow as a list requires explicit materialization first.
- `each(fn, source)` accepts list or Flow and returns a lazy Flow stage that applies effects only when consumed.
- `collect(source)` accepts list or Flow and returns a list.
- `run(source)` accepts list or Flow and returns `nil` without printing by itself.
- `reduce(f, acc, source)` accepts list or Flow and returns the final accumulator after folding all items left-to-right; `none(...)` as initial accumulator is not short-circuited; consuming a Flow with `reduce` constitutes single-use consumption.
- `count(source)` accepts list or Flow and returns the number of items; built on `reduce`.
- `_seq_reduce(f, acc, source)` is a Python reference-host internal kernel primitive; called from `reduce`'s catch-all prelude arm; handles both list and Flow; raises Seq-compatible diagnostic for non-list/non-Flow input.
- `_seq_transform(initial_state, step, source)` is a Python reference-host internal kernel primitive over Seq-compatible public sources:
  - `source` must be a list or Flow
  - list sources return lists; Flow sources return Flows
  - `step` is called as `step(state, item)`
  - `step` must return a map with optional `state`, `emit`, and `halt`
  - omitted `state` keeps the current state; omitted `emit` defaults to `[]`; omitted `halt` defaults to `false`
  - `emit` must be a list and emits zero, one, or many values in order
  - `halt: true` emits the current result and stops the whole transform without pulling later source items
  - invalid result shape, invalid `emit`, and invalid `halt` raise runtime errors prefixed with `invalid-seq-transform-result:`
- `_seq_transform` must not introduce syntax, a Core IR node, a public Seq value/type/helper, implicit list-to-Flow conversion, or implicit Flow-to-list conversion.
- `_seq_transform`, `_seq_reduce`, and related underscore sequence kernels must not be ordinary user-callable Genia names; public code uses prelude helpers such as `map`, `filter`, `take`, `scan`, `each`, `collect`, `run`, `reduce`, `count`, `evolve`, and `as_seq`.
- `as_seq(value)` is the only public explicit adapter for converting values into Seq-compatible ordered sources; strings remain atomic and are not implicitly Seq-compatible; `as_seq` does not introduce a `Char` type, scalar auto-lifting, or a public Seq runtime value beyond itself.

## `rules(..fns)`

`rules(..fns)` is a Flow-stage function that applies rule functions to each incoming flow item.

It is a library/runtime abstraction, not special syntax.

### Rule shape

Each rule must be a function with the shape:

```genia
(record, ctx) -> none(...) | some(result)
```

Plain `none` is also valid and means the same no-effect result as `none(reason)` / `none(reason, context)`.

Where `result` is a map that may contain:

* `emit`: a list of values to emit to the output flow
* `record`: a replacement current record for subsequent rules on the same input item
* `ctx`: a replacement running context carried to later rules and later input items
* `halt`: when true, stop evaluating remaining rules for the current input item

### Defaults

If a matching rule returns `some(result)` and a field is missing:

* `emit` defaults to `[]`
* `record` defaults to the current record unchanged
* `ctx` defaults to the current ctx unchanged
* `halt` defaults to `false`

### Evaluation semantics

The running `ctx` starts as `{}` before the first input item.

For each input item:

1. Initialize `record` to the current input item
2. Reuse the current running `ctx`
3. Evaluate rules from left to right
4. If a rule returns `none(...)` (including plain `none`), it has no effect
5. If a rule returns `some(result)`:

   * append `result.emit` to the output stream
   * replace `record` if `result.record` is present
   * replace `ctx` if `result.ctx` is present
   * stop evaluating later rules for this item if `result.halt` is true
6. After the last applicable rule, continue to the next input item using the final `ctx`

### Output semantics

A single input item may produce:

* zero output values
* one output value
* many output values

`rules(..fns)` may therefore filter, transform, expand, or suppress items.

### Identity case

`rules()` with zero rules acts as an identity flow stage.

### Errors

It is a runtime error if:

* a rule does not return `none(...)` or `some(...)`
* a matching rule returns `some(result)` where `result` is not a map-like structure
* `emit` is present but is not a list
* `halt` is present but is not a boolean

Rule-contract violations raise runtime errors prefixed with `invalid-rules-result:` so tooling can detect them reliably.

### Notes

* `rules(..fns)` works on any incoming flow, not only `stdin`
* `rules(..fns)` does not change the semantics of `|>`
* `record` is the current item being transformed
* `ctx` is persistent rule-processing state across items
* in this phase, the host runtime keeps the lazy Flow kernel while `src/genia/std/prelude/flow.genia` handles most user-visible rule semantics
* the host rules kernel expects normalized prelude output with `emit` and `ctx` already present

## `keep_some_else(stage, dead_handler[, flow])`

`keep_some_else(...)` is an explicit Flow-stage helper for Option-returning stages.

It is a library/runtime abstraction, not special syntax.

### Evaluation semantics

For each incoming flow item `x`:

1. Evaluate `stage(x)`
2. If the result is `some(v)`:
   * emit `v` on the main output flow
3. If the result is `none(...)`:
   * emit nothing on the main output flow for that item
   * call `dead_handler(x)` with the original input item
4. If the result is not an Option:
   * raise a clear user-facing error

### Notes

* this helper is explicit local dead-letter routing
* it does not change the semantics of `|>`
* ordinary pipelines still preserve `none(...)` short-circuit and metadata
* `dead_handler` is a handler call, not a second live flow output in this phase
* `none`, `none(reason)`, and `none(reason, meta)` are all treated as dead-letter results

## 20) Output sink invariants (host-backed phase 1)

- `display` and `debug_repr` are the first concrete public entry points of the planned Representation System (#166)
- these names must be treated as Representation System surface area, not standalone utility helpers
- `display(value)` and `debug_repr(value)` return strings and must not write to `stdout` or `stderr`
- `display(value)` and `debug_repr(value)` must render Outcome values directly, including `none(...)`; ordinary none propagation must not bypass these representation entry points
- output operations remain separate:
  - `print(...)` writes to `stdout`
  - `log(...)` writes to `stderr`
  - `write(sink, value)` and `writeln(sink, value)` write to explicit sinks
- #185 must not define the full Representation System
- #166 owns the broader representation model, naming boundaries beyond `display` / `debug_repr`, extension points, user-defined representations, registry/strategy behavior, and cross-host handling of opaque runtime values
- #185 must not introduce alternate public representation terminology such as `render`, `view`, or `repr`
- if #166 later changes the canonical names, #185 behavior must migrate through the alias-safe rename sequence: introduce alias, migrate usage incrementally, update tests, then remove the old name later

- `stdout` and `stderr` are runtime capability values, not parser syntax
- public sink helper names are exposed through thin prelude wrappers in `src/genia/std/prelude/io.genia`
- those wrappers are the canonical user-facing API surface for `help(...)` and higher-order use
- underlying sink behavior remains host-backed in this phase; wrappering does not change semantics
- required output builtins:
  - `write(sink, value)`
  - `writeln(sink, value)`
  - `flush(sink)`
- `print(...)` writes to `stdout`
- `log(...)` writes to `stderr`
- `input()` remains independent from `stdin` / Flow source behavior
- broken pipe on `stdout` output in CLI/file/command execution is normal downstream termination and must not surface as a Python traceback
- broken pipe on `stderr` should be handled best-effort without recursive noisy failures

## 21) Pipe command mode invariants (runtime-only)

- `-p` / `--pipe` are CLI-only runtime flags, not parser syntax
- pipe mode runs the provided source over `stdin |> lines`, then consumes the final Flow automatically
- the provided source must be a single stage expression
- explicit `stdin` and explicit `run` in pipe mode are rejected with a clear error
- pipe mode diagnostics should stay Genia-facing rather than exposing internal IR/runtime node names
- if a user gives a value helper or reducer where a Flow stage is expected, the error should point toward Flow stages such as `map(...)`, `filter(...)`, `each(...)`, `keep_some(...)`, or toward `-c` / file mode for final value reducers such as `sum` / `count`
- ordinary `-c` command mode remains unchanged and evaluates exactly what the user wrote
- pipe mode bypasses the `main` convention; file mode and `-c` mode keep existing `main/1` then `main/0` behavior
- pipeline operator semantics are unchanged; this does not add a new operator or runtime meaning for `|>`

## 22) Sheet invariants (Experimental)

- A `GeniaSheet` is an immutable, columnar, named-column runtime value.
- `sheet(columns)` accepts a list of `[name, values]` two-item pairs; column values must be lists; column names must be unique; all columns must have equal length.
- `shape`, `columns`, `select`, `where`, `derive`, and `rows` must reject non-Sheet values with a clear `TypeError`.
- `select(names, sheet)` returns a new Sheet with requested columns in requested order; duplicate or missing names must fail clearly; input Sheet is never mutated.
- `where(predicate, sheet)` returns a new Sheet containing rows where predicate returns `true`; predicate receives each row as a list of `[name, value]` pairs; non-boolean predicate results must fail clearly.
- `derive(name, function, sheet)` returns a new Sheet with a new column appended; an existing column name must fail clearly; the row function receives each row as a list of `[name, value]` pairs.
- `row_get(row, column_name)` (Experimental, issue #363) returns the value paired with `column_name` in a row — a plain `list` of `[name, value]` pairs, not a Sheet. It uses the same column-name identity rules as `sheet`/`select`, performs a first-match scan, never mutates its input, and must reject a non-`list` row, a malformed row entry, or a missing column with a clear `TypeError`. It introduces no new syntax and does not change the `where`/`derive`/`rows` row representation.
- All Sheet operations return new `GeniaSheet` values; tuple-backed canonical column storage must not be mutated.
- `some(...)`, `none(...)`, and `err(...)` values are stored as ordinary cell values; no implicit Outcome propagation is introduced across columns or rows.
- Sheet errors must set `_genia_preserve_pipeline_error = True` to opt out of generic pipeline error wrapping.
- Sheets are not Seq-compatible sources and must not be passed to `each`, `collect`, `run`, `map`, `filter`, or `reduce` without explicit conversion in this phase.
- `collect_sheet(records)` (Experimental, issue #395) is the one explicit Seq-to-Sheet conversion: it accepts a finite list or Flow of map records, uses the first record's key order as column order, and requires every later record's key set to exactly match the first record's — no union, padding, or dropped fields. Non-map items and shape mismatches must fail clearly with the offending row index. It does not read or unwrap Outcome values; a bare `some`/`none`/`err` item is rejected as a non-map record.
- `render_csv(sheet)` (Experimental, issue #396) is a pure Sheet-to-string operation: header order must match Sheet column order, data order must match Sheet row order, and comma/quote/newline/carriage-return fields must use deterministic CSV quoting with doubled embedded quotes. A zero-column Sheet returns an empty string; every record of a non-zero-column Sheet ends with `\n`.
- `render_csv` accepts string, symbol, integer, float, boolean, and nil headers/cells only. It must reject composite values and non-nil Outcome values with a clear zero-based location error, must not mutate the Sheet, perform I/O, make Sheet Seq-compatible, or unwrap Outcomes.
- No new syntax, parser changes, or Core IR nodes are introduced by Sheet.

## 23) Web response-header composition invariants (Python-host-only, Partial)

- `web.with_headers(headers, response)` is the single public response-header composition operation; response is last for pipeline use.
- It requires map inputs, a response containing `status`, `headers`, and `body`, a map-valued `response.headers`, and string header names and values.
- It returns a new response and a new header map; inputs are not mutated and all non-header response entries are preserved.
- Output header names are lowercase. Collisions are case-insensitive, later entries within one map win, and supplied headers win existing response headers.
- Programmer misuse raises the deterministic `TypeError` behavior recorded in `GENIA_STATE.md`; it does not return an Outcome.
- It performs no I/O and adds no CORS, preflight, route, middleware, parser, Core IR, shared-spec, or cross-host behavior.

## 24) CORS handler-wrapper invariants (Python-host-only, Partial)

- `web.cors(policy, handler)` is the single public CORS operation and returns a handler; there is no header-map-only CORS API or public `options(...)` route.
- The closed policy has optional `origin`, `methods`, and `headers` fields with the exact defaults and validation behavior recorded in `GENIA_STATE.md`.
- True preflight requires method `OPTIONS` plus `origin` and `access-control-request-method` request headers; it returns a bodyless `204` response without invoking the wrapped handler.
- Other requests, including incomplete `OPTIONS` requests, invoke the wrapped handler exactly once.
- Ordinary responses receive configured CORS headers solely through `with_headers`; configured CORS values win collisions while application status, body, unrelated headers, and additional fields are preserved.
- Inputs are not mutated. Programmer misuse raises deterministic `TypeError`; no Outcome, middleware framework, parser/Core IR/shared-spec behavior, or cross-host claim is introduced.

## 25) R8 server execution invariants

- Only explicit `genia serve <file>` activation may enter the dedicated server lifecycle. Load, import, parse, evaluation, and discovery remain inert in every other mode.
- `@server`, `@route`, and `@cors` each take one ordinary map expression through the existing prefix-annotation grammar. No parser or Core IR extension is permitted.
- Exactly one `@server` is required on a top-level assignment. At most one `@cors` may appear, on that same assignment. `@route` is valid only on a top-level named function exposing exactly one fixed request argument.
- Server config binds exactly to `serve_http`; route descriptors bind in source order exactly to `route_request`; application CORS binds exactly once to `cors`, whose header behavior remains owned by `with_headers`. R8 must not duplicate or loosen those operations.
- Discovery is entry-file-only and occurs after successful evaluation. Descriptor diagnostics precede conflicts; route conflicts use exact `(method, path)` equality and are reported in source order. Any discovery diagnostic prevents listener activation.
- The dedicated phase order is `startup -> request* -> shutdown`. Server and request scopes have explicit entry and ownership boundaries; an owned listener receives exactly one cleanup opportunity after normal completion or failure.
- The first non-cleanup failure remains primary. Cleanup failures never replace or hide it. Startup failure skips requests, request failure skips later requests, and owned cleanup still runs.
- The lifecycle core must be callable without CLI parsing or live sockets and must return the deterministic result shape defined in `GENIA_STATE.md` section 9.7.
- Descriptor and result data shapes are host-independent. R8 execution is Python-reference-host-only and adds no shared host-adapter capability or cross-host server guarantee.
- The dedicated lifecycle core and inert `@route`, `@server`, and `@cors` metadata/discovery/binding are implemented in the Python reference host, together with explicit `genia serve <file>` activation. Serve mode evaluates exactly one entry file without ordinary `main` dispatch and keeps the descriptors inert in every other mode.
