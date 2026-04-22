# Shared Conformance Cases — Phase 1: Design Note

**Status:** Design artifact — no implementation yet.
**Date:** 2026-04-16
**Author:** Spec planning prompt

---

## 1. Scope Lock

Phase 1 covers the **smallest useful cross-host conformance surface** that can be executed today by the Python reference host against real shared case files under `spec/`.

### Included in phase 1

| Category | Directory | Boundary tested |
|---|---|---|
| eval | `spec/eval/` | Source → result value, with optional stdout |
| errors | `spec/errors/` | Source → normalized error category + message substring |
| cli | `spec/cli/` | Argv list + optional stdin → stdout + stderr + exit code |

### Explicitly excluded from phase 1

| Category | Why deferred |
|---|---|
| parser (AST snapshots) | AST shape is explicitly host-local per `docs/architecture/core-ir-portability.md`; normalizing a shared JSON AST contract is high cost, low value at one host |
| ir (Core IR snapshots) | Valuable but requires a stable Core IR JSON serialization contract; defer until a second host is closer |
| flows | Flow behavior is already covered under eval (source → result/stdout) without needing a distinct category contract; flow-specific cases can live in `spec/eval/` as ordinary eval cases with stdin |
| prelude-only behavior | Prelude helpers that produce plain values are covered by eval cases; helpers requiring Flow + stdin are covered via eval-with-stdin or cli cases |

### Rationale

- Eval cases are the highest-value surface: they lock observable language semantics at the result boundary.
- Error cases lock the normalized error contract that docs and users already depend on.
- CLI cases lock the three execution modes (file, `-c`, `-p`) at the process boundary.
- Parser AST and Core IR JSON shapes require serialization contracts that do not exist yet and are explicitly host-local; forcing them now would embed Pythonisms.

---

## 2. Goals

1. Make shared conformance real — at least one category has executable cases that the Python host runs in CI.
2. Let the Python reference host execute shared cases through a thin adapter, without a generic multi-host runner.
3. Create a case file contract that future hosts can adopt without inheriting Python-specific details.
4. Catch semantic drift at the eval, error, and CLI boundaries before a second host exists.
5. Validate the `spec/manifest.json` host test contract shape against real fixtures.

---

## 3. Non-Goals

- No second host implementation.
- No full cross-host matrix execution.
- No browser runtime adapter claims.
- No language redesign or new syntax.
- No capability-driver expansion (HTTP, shell stage, debugger).
- No generic `tools/spec_runner/` runner implementation — Python runs its own adapter in its own test suite.
- No AST or Core IR JSON serialization standard (deferred).

---

## 4. Phase-1 Categories

### 4.1 `spec/eval/`

**Why phase 1:** Eval is the core semantic boundary — source text in, result value + stdout out. Every Genia host must agree on this.

**Boundary validated:** `eval(source, stdin?, argv?) → { result, stdout, stderr?, error? }`

**Fixture kinds:**
- Literal evaluation (numbers, strings, booleans, lists, maps, none/some)
- Arithmetic and operator precedence
- Function definition and call
- Pattern matching (tuple, list, map, wildcard, rest, guard, option patterns)
- Pipeline evaluation (value-mode, Option propagation)
- Assignment and lexical scoping
- Autoloaded prelude helpers (pure-value subset)
- Cases with stdin input (flow collect, rules)
- Cases expecting `none(...)` / `some(...)` result values

**Out of scope within eval:**
- Host interop (`import python`) — host-local capability
- HTTP serving, debugger stdio, process/ref timing — host-local capabilities
- Shell stage `$(...)` — Python-host-only, experimental
- Non-deterministic output (timing, random seed) — not contractually stable

### 4.2 `spec/errors/`

**Why phase 1:** Docs, cheatsheets, and user-facing error messages already depend on stable error categories and message substrings. Locking these prevents drift.

**Boundary validated:** `eval(source) → normalized error { category, message_contains }` or `cli(args) → { exit_code, stderr_contains }`

**Fixture kinds:**
- Parse errors (bad rest position, invalid case placement, missing closing delimiter)
- Runtime errors (undefined name, no matching case, wrong arity, type errors)
- CLI mode errors (missing file path, ambiguous mode, pipe-mode rejections)

**Out of scope within errors:**
- Exact full error message matching (fragile; use substring/category matching)
- Source location line/column enforcement (optional metadata, not contractually required in phase 1)
- Stack trace format

### 4.3 `spec/cli/`

**Why phase 1:** All three CLI modes (file, `-c`, `-p`) are documented as required host capabilities. Locking their observable stdout/stderr/exit-code behavior prevents mode-semantic drift.

**Boundary validated:** `cli(args, stdin?) → { stdout, stderr, exit_code }`

**Fixture kinds:**
- `-c` with simple expression producing stdout via `print`
- `-c` with `main(argv())` dispatch
- `-p` with stdin lines through map/filter/each
- File mode with inline source (case references a `.genia` source file co-located in the spec directory)
- Exit code 0 on success, non-zero on error

**Out of scope within cli:**
- REPL behavior (interactive, hard to normalize)
- `--debug-stdio` mode (host-local transport)
- Broken-pipe behavior (OS-dependent)
- `argv()` edge cases beyond basic positional/option-like args

---

## 5. Case File Contract

### 5.1 File format

Each shared case is a single **JSON file** with extension `.case.json` placed under the appropriate `spec/<category>/` directory.

JSON is chosen because:
- every host can parse it without extra dependencies
- git-readable, hand-authorable
- stable once adopted
- mirrors the existing `tests/data/*_cases.json` pattern in the repo

### 5.2 Required fields

```json
{
  "id": "eval_literal_number",
  "category": "eval",
  "description": "Evaluating a number literal returns that number",
  "source": "42",
  "expected_result": "42"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | **yes** | Unique case identifier. Format: `<category>_<snake_case_name>`. Must be unique across the entire `spec/` tree. |
| `category` | string | **yes** | One of: `eval`, `errors`, `cli`. Must match the parent directory. |
| `description` | string | **yes** | Human-readable one-line description of what the case validates. |

One of the following input groups is required:

**For `eval` and `errors` cases:**

| Field | Type | Required | Description |
|---|---|---|---|
| `source` | string | **yes** | Genia source text to evaluate. Inline in the JSON value. Newlines as `\n`. |
| `source_file` | string | no | Relative path (from the `.case.json` file) to a `.genia` source file. Mutually exclusive with `source`. Use for multi-line programs where inline JSON is awkward. |
| `stdin` | string | no | Stdin text to provide. Newlines as `\n`. |
| `argv` | string[] | no | Argv strings to expose through `argv()`. |

**For `cli` cases:**

| Field | Type | Required | Description |
|---|---|---|---|
| `args` | string[] | **yes** | CLI argument list (as if passed to the `genia` command, excluding the binary name). |
| `stdin` | string | no | Stdin text to provide. |

### 5.3 Expected output fields

**For `eval` cases (success):**

| Field | Type | Required | Description |
|---|---|---|---|
| `expected_result` | string | **yes** | The display-string representation of the final Genia result value (see §6). |
| `expected_stdout` | string | no | Expected stdout text. If omitted, stdout is unchecked. |

**For `errors` cases:**

| Field | Type | Required | Description |
|---|---|---|---|
| `expected_error` | object | **yes** | Normalized error expectation (see §7). |

**For `cli` cases:**

| Field | Type | Required | Description |
|---|---|---|---|
| `expected_stdout` | string | yes (unless error) | Expected stdout text. |
| `expected_stderr` | string | no | Expected stderr text or substring. |
| `expected_exit_code` | integer | **yes** | Expected process exit code. |
| `expected_error` | object | no | If present, the case asserts an error condition. |

### 5.4 Optional metadata fields (all categories)

| Field | Type | Description |
|---|---|---|
| `tags` | string[] | Freeform tags for filtering (e.g. `["option", "pipeline", "pattern-matching"]`). |
| `since` | string | Language/spec version when the case was added (e.g. `"0.1.8"`). |
| `notes` | string | Implementation notes, not contractual. |

### 5.5 Case ID rules

- Format: `<category>_<descriptive_snake_case_name>`
- Must be unique across all `spec/` case files
- Must match the filename stem: `spec/eval/eval_literal_number.case.json` has id `eval_literal_number`
- No host-specific prefixes or suffixes

### 5.6 Source encoding

- `source` field: inline JSON string. Use `\n` for newlines, standard JSON escaping.
- `source_file` field: relative path from the case file to a `.genia` file in the same spec directory. The file must exist. Only one of `source` or `source_file` may be present.
- No base64, no external URL references.

### 5.7 Manifest registration

Phase 1 does **not** require per-case manifest registration in `spec/manifest.json`.

The manifest records the overall spec contract shape and host status. Individual cases are discovered by globbing `spec/<category>/*.case.json`. This keeps case addition low-friction.

A future phase may add a case index to the manifest if case counts grow large.

---

## 6. Normalized Output Contract

### 6.1 Result value rendering

The `expected_result` field uses the **display-string** representation of a Genia value — the same text Genia's `print` or REPL would emit.

| Value kind | Display format | Example |
|---|---|---|
| Number (integer) | Decimal digits, no trailing `.0` | `42` |
| Number (float) | Decimal with fractional part | `3.14` |
| String | Bare string content (no quotes) | `hello world` |
| Boolean | `true` or `false` | `true` |
| Symbol | Bare name | `x` |
| List | `[item1, item2, ...]` | `[1, 2, 3]` |
| Map | `{key1: value1, key2: value2}` | `{name: Alice, age: 30}` |
| `none` (bare) | `none` | `none` |
| `none(reason)` | `none(reason)` | `none(missing-key)` |
| `none(reason, ctx)` | `none(reason, {key: value})` | `none(missing-key, {key: name})` |
| `some(value)` | `some(value)` | `some(42)` |
| Pair | `(head . tail)` | `(1 . 2)` |
| Function | Not contractually specified | (cases should not assert function display) |
| Flow | Not contractually specified | (cases should not assert flow display) |
| Opaque handles | Not contractually specified | (not in shared scope) |

### 6.2 Map key ordering

Map display key order is **not contractually guaranteed** in phase 1. Cases that assert map results should either:
- use single-key maps, or
- use `expected_result_unordered_map: true` (optional field, signals the runner to compare map contents set-wise rather than string-wise)

### 6.3 Stdout / stderr

- `expected_stdout` and `expected_stderr` are plain text strings with `\n` for newlines.
- Trailing newline handling: the expected string is compared after stripping one trailing `\n` from both expected and actual, to tolerate host differences in final-newline emission. All other whitespace must match exactly.
- If the field is omitted, that stream is unchecked.

### 6.4 Exit code

- `expected_exit_code` is an integer.
- `0` = success.
- `1` = general error (parser, runtime, or CLI dispatch failure).
- Other codes are not specified in phase 1.

### 6.5 What is NOT in the shared output contract

- Internal Core IR JSON shape
- Parser AST JSON shape
- Debug-print formatting of host objects
- Stack trace text
- Timing or ordering of concurrent output
- Flow display text (opaque)
- Function display text (opaque)

---

## 7. Error Normalization Contract

### 7.1 Shared error object shape

```json
{
  "expected_error": {
    "category": "NameError",
    "message_contains": "Undefined name"
  }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `category` | string | **yes** | Python exception class name **or** a shared category alias (see below). Hosts must map to a shared namespace. |
| `message_contains` | string | **yes** | A substring that must appear in the error message text. |
| `message_exact` | string | no | If present, the full error message must match exactly. Use sparingly. |

### 7.2 Shared error category aliases

To avoid embedding Python exception class names as the permanent contract, phase 1 defines a small shared alias set. Hosts must map their native error types to these aliases. The Python host maps directly since these are already its exception names.

| Shared alias | Python mapping | When used |
|---|---|---|
| `SyntaxError` | `SyntaxError` | Parse-time and lowering-time syntax violations |
| `NameError` | `NameError` | Undefined name at eval time |
| `TypeError` | `TypeError` | Wrong type, wrong arity, ambiguous resolution, non-callable value |
| `ValueError` | `ValueError` | Invalid argument value (e.g. invalid JSON text) |
| `RuntimeError` | `RuntimeError` | General runtime failures not covered above |
| `FileNotFoundError` | `FileNotFoundError` | Missing module file, missing source file |
| `PermissionError` | `PermissionError` | Disallowed host module import |

Future hosts must map their native error representations to these shared aliases.

### 7.3 Parser errors vs runtime errors

- Parser errors use `category: "SyntaxError"`.
- Runtime errors use the appropriate alias from the table above.
- There is no structural difference in the case file shape; both use `expected_error`.

### 7.4 CLI error representation

For `cli` category cases asserting errors:
- `expected_exit_code` must be non-zero (typically `1`).
- `expected_stderr` may contain a substring check.
- `expected_error` is optional and provides structured category/message validation if the runner can capture the underlying exception before it becomes stderr text.

### 7.5 Source location

Source location (line, column) is **not required** in phase 1 error objects. It may be added as optional fields in a future phase:

```json
{
  "line": 3,
  "column": 5
}
```

### 7.6 Stability rule

Error `message_contains` substrings must be drawn from strings that already appear in the current test suite and are verified by CI. Do not invent new message text for the shared contract.

---

## 8. Category-Specific Expectations

### 8.1 `spec/eval/` assertion boundary

- **Assert:** `expected_result` matches the display-string of the evaluated result.
- **Assert (optional):** `expected_stdout` matches captured stdout.
- **Do NOT assert:** stderr content (eval cases are success cases; use `spec/errors/` for failures).
- **Do NOT assert:** internal IR shape, AST shape, or evaluation trace.

Runner pseudocode:
```
env = make_global_env(case.argv or [])
result = run_source(case.source, env, stdin=case.stdin)
assert display(result).strip() == case.expected_result.strip()
if case.expected_stdout:
    assert captured_stdout.strip() == case.expected_stdout.strip()
```

### 8.2 `spec/errors/` assertion boundary

- **Assert:** evaluating `source` raises an exception.
- **Assert:** the exception's category matches `expected_error.category`.
- **Assert:** `expected_error.message_contains` is a substring of the exception message.
- **Do NOT assert:** exact full message (unless `message_exact` is present).
- **Do NOT assert:** source location.

Runner pseudocode:
```
try:
    run_source(case.source, env)
    FAIL("expected error")
except Exception as e:
    assert type(e).__name__ == case.expected_error.category
    assert case.expected_error.message_contains in str(e)
```

### 8.3 `spec/cli/` assertion boundary

- **Assert:** `expected_stdout` matches captured stdout (after trailing-newline normalization).
- **Assert:** `expected_exit_code` matches the process exit code.
- **Assert (optional):** `expected_stderr` substring appears in captured stderr.
- **Assert (optional):** `expected_error` structured check if the runner captures the exception.

Runner approach: the Python adapter invokes the CLI entrypoint programmatically or as a subprocess with `case.args` and `case.stdin`.

### 8.4 Flows

Flow behavior is tested through `spec/eval/` cases that provide `stdin` and use `collect` to materialize results, or through `spec/cli/` cases that test `-p` mode. Flows do not need a separate spec category in phase 1.

---

## 9. What Remains Host-Local

The following are explicitly **not part of the shared spec contract** in phase 1:

| Item | Reason |
|---|---|
| Parser AST JSON shape | Host-local per `core-ir-portability.md` |
| Core IR JSON serialization | No shared serialization standard yet |
| Optimized post-lowering IR (e.g. `IrListTraversalLoop`) | Host-local optimization |
| `import python` / `import python.json` behavior | Python-host-only capability |
| Shell stage `$(...)` | Python-host-only, experimental |
| HTTP serving (`serve_http`) | Optional capability, no shared process-level test contract |
| Ref/Process timing behavior | Thread-sensitive, host-local |
| Debugger stdio adapter | Host-local transport |
| REPL interactive behavior | Hard to normalize |
| Stack trace format | Host-local |
| `help()` / `help("name")` display formatting | Host-local rendering |
| Function/Flow/opaque-handle display strings | Host-local |
| Map key iteration order | Not guaranteed |
| Broken-pipe OS behavior | OS-dependent |

---

## 10. Validation Rules

### 10.1 Case schema validation

Later implementation prompts must add a test that validates every `spec/<category>/*.case.json` file against the schema defined in §5. At minimum:
- required fields present
- `id` matches filename stem
- `category` matches parent directory name
- `id` is unique across all spec cases
- `source` and `source_file` are mutually exclusive
- `source_file` references must resolve to existing files

### 10.2 Deterministic fixture execution

- Every spec case must produce the same result on every run.
- Cases must not depend on timing, random seeds, network, or filesystem state outside the spec tree.
- Cases must not depend on mutable global state or prior case execution order.

### 10.3 Snapshot / update policy

- There is no snapshot-update mode in phase 1. Expected values are hand-authored in the case files and validated by CI.
- A future phase may add snapshot update tooling.

### 10.4 Anti-drift rules

- Every eval/error case's `source` must be valid current Genia syntax.
- Every `expected_result` must match the current Python host's actual output for that source.
- Every `message_contains` substring must appear in the current Python host's actual error message.
- If a language change modifies any of these, the shared case file must be updated in the same PR.

### 10.5 Adding new shared cases

When adding a new case:
1. Create `spec/<category>/<id>.case.json` following §5.
2. If using `source_file`, co-locate the `.genia` file in the same directory.
3. Run the spec test suite and verify the new case passes.
4. The case must exercise behavior that is implemented, stable, and verified by existing tests.
5. Do not add cases for behavior that is speculative, host-local, or not yet implemented.

---

## 11. Documentation Impact

When the phase-1 spec is implemented, later prompts **must** update:

| Document | What to update |
|---|---|
| `GENIA_STATE.md` §0 | Change spec/ description from "scaffold-level" to "phase-1 cases exist for eval, errors, cli" |
| `spec/README.md` | Update status from "directory scaffold only" per category; add link to this design note |
| `spec/manifest.json` | Add `spec_phase` or similar field recording that phase 1 is implemented; update `generic_spec_runner` status if the Python adapter exists |
| `spec/eval/README.md` | Update from "directory scaffold only" to document the eval case contract |
| `spec/errors/README.md` | Same |
| `spec/cli/README.md` | Same |
| `tools/spec_runner/README.md` | Document the Python adapter and how to run spec cases |
| `hosts/README.md` | Note that the Python host now validates shared spec cases |
| `docs/host-interop/HOST_CAPABILITY_MATRIX.md` | Update `shared spec runner support` row from "Scaffolded" to "Phase 1" for Python |
| `README.md` | Mention shared spec cases exist (brief) |
| shared portability docs | Update to reflect real spec execution when contract changes |

Documents that do **not** need updating (unless public user-facing examples change):
- `docs/cheatsheet/*`
- `GENIA_RULES.md` (semantics are not changing)
- `GENIA_REPL_README.md`
- `docs/style/*`

---

## 12. Open Questions

### 12.1 Must resolve now (before implementation)

| # | Question | Recommended resolution |
|---|---|---|
| Q1 | Should the Python adapter be a new test file (e.g. `tests/test_spec_cases.py`) or integrated into the existing `test_cases.py`? | **New file.** `test_cases.py` tests `tests/cases/` which is the host-local black-box suite. Spec cases live under `spec/` and have a different schema. Keep them separate. |
| Q2 | Should `spec/eval/` cases that need stdin be placed in `spec/eval/` or `spec/cli/`? | **`spec/eval/`** when the boundary under test is eval semantics (result value). `spec/cli/` when the boundary is process stdout/stderr/exit-code. Eval cases may provide `stdin`. |
| Q3 | How should multi-line Genia source be represented? | **Inline `\n`** in the `source` JSON string for short programs. Use `source_file` for longer programs (>~10 lines). |
| Q4 | Should the case file schema be documented as a JSON Schema file in the repo? | **Yes, but deferred to implementation prompt.** A minimal JSON Schema in `spec/case-schema.json` aids validation. |
| Q5 | Is the error category list in §7.2 sufficient? | **Yes for phase 1.** These cover all error types currently raised by the Python host for the fixture kinds in scope. Expand if new error types are needed. |

### 12.2 Explicitly deferred to later phases

| # | Question | Phase |
|---|---|---|
| D1 | Core IR JSON serialization standard for `spec/ir/` | Phase 2+ (when a second host approaches) |
| D2 | Parser AST normalization for `spec/parser/` | Phase 2+ |
| D3 | Generic multi-host spec runner in `tools/spec_runner/` | Phase 2+ (when a second host exists) |
| D4 | Snapshot update tooling | Phase 2+ |
| D5 | Flow-specific category (`spec/flows/`) separate from eval | Phase 2+ (if flow contract grows complex) |
| D6 | Capability-driver shared test contract (HTTP, debugger) | Phase 2+ |
| D7 | Per-case manifest index | Phase 2+ (if case count warrants it) |
| D8 | Source location in error normalization | Phase 2+ |

---

## 13. Recommended First Fixture Set

All cases below exercise behavior that is **already implemented, stable, and verified** by existing tests in `tests/cases/` or `tests/test_*.py`.

### 13.1 Eval cases (8 cases)

| Case ID | Source | Expected result | Notes |
|---|---|---|---|
| `eval_literal_number` | `42` | `42` | Basic literal |
| `eval_literal_string` | `"hello"` | `hello` | String display |
| `eval_arithmetic_precedence` | `1 + 2 * 3` | `7` | Mirrors `tests/cases/arithmetic_precedence` |
| `eval_list_literal` | `[1, 2, 3]` | `[1, 2, 3]` | List display |
| `eval_function_call` | `inc(x) -> x + 1\ninc(5)` | `6` | Named function |
| `eval_pattern_match_list` | `head([x, .._]) -> x\nhead([10, 20, 30])` | `10` | List pattern with rest |
| `eval_option_some` | `some(42)` | `some(42)` | Option some display |
| `eval_option_none_bare` | `none` | `none` | Bare none display |

### 13.2 Error cases (4 cases)

| Case ID | Source | Expected error category | message_contains |
|---|---|---|---|
| `errors_undefined_name` | `xyz` | `NameError` | `Undefined name` |
| `errors_bad_rest_position` | `f(xs) =\n  [..rest, x] -> x\nf([1,2,3])` | `SyntaxError` | `..rest must be the final item` |
| `errors_no_matching_case` | `f(0) -> "zero"\nf(1)` | `RuntimeError` | `No matching case` |
| `errors_wrong_arity` | `((x) -> x)(1, 2)` | `TypeError` | (arity message substring from current runtime) |

### 13.3 CLI cases (3 cases)

| Case ID | Args | Stdin | Expected stdout | Expected exit code |
|---|---|---|---|---|
| `cli_command_print` | `["-c", "print(42)"]` | — | `42` | `0` |
| `cli_command_argv` | `["-c", "argv()", "hello", "world"]` | — | `[hello, world]` | `0` |
| `cli_pipe_head` | `["-p", "head(1) \\|> each(print)"]` | `"a\nb\nc\n"` | `a` | `0` |

**Total: 15 cases.** This is deliberately small. It proves the machinery works end-to-end. More cases are added once the adapter and schema validation pass CI.

---

## 14. Acceptance Criteria

### Done means:

- [ ] `spec/eval/` contains at least 5 `.case.json` files following the §5 contract.
- [ ] `spec/errors/` contains at least 3 `.case.json` files following the §5 contract.
- [ ] `spec/cli/` contains at least 2 `.case.json` files following the §5 contract.
- [ ] A Python test adapter exists (e.g. `tests/test_spec_cases.py`) that discovers and executes all `spec/<category>/*.case.json` files.
- [ ] The adapter validates required fields and rejects malformed case files.
- [ ] All spec cases pass in the Python reference host's CI (`uv run pytest tests/test_spec_cases.py`).
- [ ] No spec case depends on host-local behavior, timing, randomness, or filesystem state outside `spec/`.
- [ ] `spec/README.md` is updated to reflect phase-1 status per category.
- [ ] `spec/manifest.json` is updated to record phase-1 status.
- [ ] `GENIA_STATE.md` §0 is updated to reflect that spec cases exist (not just scaffolding).
- [ ] `tools/spec_runner/README.md` is updated to document the Python test adapter.
- [ ] `docs/host-interop/HOST_CAPABILITY_MATRIX.md` Python row for `shared spec runner support` is updated.
- [ ] Category README files (`spec/eval/README.md`, `spec/errors/README.md`, `spec/cli/README.md`) are updated.
- [ ] All existing tests still pass (`uv run pytest`).

---

## 15. Prompt Handoff

Later implementation, test, and documentation prompts **must** follow these rules:

1. **Keep `AGENTS.md` requirements in force.** Every change to language behavior, syntax, runtime semantics, parser rules, or examples must also update `GENIA_STATE.md` and any relevant implementation-aligned docs/specs.

2. **Keep these documents synchronized as applicable:**
   - `GENIA_STATE.md`
   - `GENIA_RULES.md`
   - `README.md`
   - `GENIA_REPL_README.md`
   - implementation-aligned docs
   - `docs/host-interop/*`
   - `spec/*`
   - `tools/spec_runner/README.md`
   - `hosts/README.md`

3. **Do not document behavior that is not implemented and verified by tests.**

4. **Do not claim the generic shared spec runner is complete.** Phase 1 adds a Python-host test adapter only. The generic runner remains scaffolded.

5. **Do not introduce Python-specific behavior into the shared case files.** Cases must express portable Genia semantics only.

6. **Error `message_contains` values must be drawn from currently verified error messages**, not invented.

7. **`GENIA_STATE.md` is the final authority** if any docs disagree.

8. **Run the full test suite** (`uv run pytest`) after any change and before declaring done.

9. **This design note lives at `docs/architecture/spec-phase-1-design.md`** and serves as the canonical reference for the phase-1 spec contract. Implementation prompts should read it before making changes.
