# R19 Diagnostic Mechanical Inventory (E19-2)

Status: **Mechanical inventory complete.** This document is the durable
artifact required by `docs/design/r19-unicode-diagnostic-portability-contract.md`
Section 5.2/9 before any diagnostic wording may be normalized (E19-3). It maps
every existing exact-stderr `spec/error/*` case and the `spec/parse/*`
type+message assertions to trigger, phase, semantic family, construction
site, interpolation/rendering, security implications, and a proposed A/B/C
classification. No diagnostic wording is changed by this document or by
E19-2; that is E19-3's job.

See also `docs/analysis/r19-diagnostic-contract-inventory.md` (E19-0's
narrative analysis input to this inventory).

## 1. Scope and method

- Enumerated all 146 `spec/error/*.yaml` cases (`category: error`) — every
  case's `expected.stderr` (or, for the five cases with `exit_code: 0` and no
  stderr, the structured-Outcome shape instead) plus `expected.exit_code`.
- Enumerated `spec/parse/*.yaml` — of 24 files, 4 are genuine parse-failure
  assertions (`parse-error-unclosed-paren`, `parse-error-named-pattern-declaration-arity`,
  `parse-error-named-pattern-use-arity`, `parse-dot-named-access-trailing-dot-error`);
  the rest assert successful parses (out of scope for diagnostic inventory).
- Grouped every error case into one of 17 semantic families by message shape
  (script-assisted, hand-reviewed), then traced each family's construction
  site(s) in `src/genia/*.py` via targeted grep, and inspected each site's
  interpolation/rendering approach.
- Classification key (contract Section 5.1): **A** = exact portable text is
  itself the contract; **B** = portable identity (phase/category/reason/params)
  with deterministic normalized rendering; **C** = host-local/incidental,
  must never leak into an A/B boundary.

## 2. Construction-site and rendering findings (families, in case-count order)

All CLI-surfaced exceptions are wrapped uniformly as `Error: {message}\n` by
the CLI's top-level exception handler (`src/genia/cli.py` — the `Error: `
prefix plus the exception's own `str(exc)`). Per-family findings below
describe the `{message}` construction, not this shared wrapper (which is
itself class B: a stable, deterministic template — "Error: " + message; the
CLI does not use Python's own exception-formatting/traceback machinery for
this path).

### type-check ("expected X, received Y") — 57 cases, the largest family

Construction sites: dozens of call sites across `src/genia/builtins.py`,
`src/genia/_format_engine.py`, and `src/genia/std/prelude/*.genia` helper
wrappers, all following the pattern
`f"{fn} expected {expectation}, received {_runtime_type_name(value)}"`.
`_runtime_type_name` (`src/genia/values.py`) is a **Genia-authored, portable
type-name table** (`"int"`, `"string"`, `"map"`, `"list"`, `"bool"`, `"flow"`,
`"named-pattern"`, `"some(int)"`, etc.) — **not** Python's `type(value).__name__`
and not `repr`/`str` of the value itself. **No host leak.** Proposed
classification: **B** (portable identity — function name + expectation +
portable type-name — with a deterministic, already-stable rendering; the
literal text is what shared evidence currently pins exactly, i.e. it
functions as A-in-practice today, but its *meaning* is a B-shaped template
so it is safe to keep exact without further inventory work).

### format-template — 28 cases

Construction sites: `src/genia/_format_engine.py` (`format-error: ...`
messages) and `src/genia/builtins.py` `format`/`format_compose` family
(`format invalid placeholder`, `format missing field: ...`). Several
`format-error` messages interpolate the raw format-spec substring with
Python `!r}` (e.g. `f"format-error: invalid format spec {spec!r}"` at
`src/genia/_format_engine.py:179,195,198,203,208,221`). `spec` here is a
short ASCII format-spec token drawn from the Genia source text itself (e.g.
`'<'`, `'03'`), not an arbitrary Genia runtime value, but Python `repr()`'s
quoting convention (single quotes, Python escape rules) is still host
formatting, not Genia's own debug-escaping rule (U3, double quotes). Flagged
as a **candidate C-adjacent leak** for E19-3 to assess: low severity (input
is always a narrow ASCII spec-grammar token, not user data), but not
authored by a Genia-defined renderer. Classification: **B**, with the `!r}`
call flagged as a normalization candidate (replace with an explicit `'…'`
literal wrap, since the value space is a closed ASCII grammar and quoting
style should be pinned by contract rather than incidentally inherited from
Python).

### arity/dispatch — 6 cases

`"No matching function: {name}/{arity}. Available: {name}/{available}"` —
construction site: `src/genia/evaluator.py` function-dispatch failure path.
Purely portable integers/names, no interpolated runtime value. **A** (exact
text is itself stable and portable).

### pattern-match-miss — 3 cases

`f"No matching case for function {fn_name}/{len(args)} with arguments {args!r}"`
and `f"No matching case for arguments {args!r}"` — construction site:
`src/genia/evaluator.py:860,862,1369`. **Confirmed real host leak**: `args`
is a Python tuple of actual Genia runtime argument values, and `{args!r}`
invokes **Python's own `repr()`** on that tuple — not `format_debug`. For a
string argument this renders with Python single-quote repr conventions
(`'x'`) instead of Genia's U3 double-quote debug escaping (`"x"`), and for
any future value whose Python `repr` differs from its Genia debug rendering
(e.g. floats, opaque wrapper types) the two diverge further. This is the
**highest-priority finding** of this inventory for E19-3. All three existing
cases (`error-lambda-pattern-miss`, `error-pattern-guard-all-fail`,
`error-pattern-miss`) currently pin the Python-`repr()`-shaped exact text
(e.g. `with arguments (99,)`), so fixing this is a **deliberate, approved
exact-text change** under contract Section 5.2, not a silent rewording — it
must be called out explicitly in E19-3's PR body. Proposed classification:
**B**, rendered via `format_debug` per value once fixed (not `repr`).

### template/matcher — 9 cases, protected-value — 4 cases, map-key-legality — 4 cases, representation — 1 case, sheet/csv — 5 cases, validated-pipeline — 2 cases, config — 1 case, model/provider — 2 cases, import — 2 cases, glob-pattern — 1 case, eval-core — 2 cases, assert-surface — 1 case, other — 18 cases

All remaining families were hand-reviewed for host-wording/interpolation
risk. None found a second `!r`/`str()`/`repr()`-on-a-runtime-value leak
beyond the two already noted above. Representative construction sites:
`src/genia/builtins.py` (template/matcher, protected-value, representation,
sheet/csv, config, model/provider, validated-pipeline, glob-pattern),
`src/genia/evaluator.py` (eval-core: `Undefined name: ...`,
`Assignment target must be a simple name`), the module-import path (import:
`Module not found: ...`, `Host module not allowed: ...`),
`src/genia/equality.py`/`src/genia/values.py` (map-key-legality: NaN/
unsupported-key messages — these are R18-approved exact text and out of
scope for R19 to reword), `src/genia/builtins.py` (assert-surface:
`assert_eq failed`). Proposed classification for all of these: **A**
(static/template text with no dynamic Genia-value interpolation risk beyond
already-portable type names or user-supplied field/column names, which are
themselves plain Genia strings passed through unmodified — not re-rendered
by any host formatter).

### The five `exit_code: 0` structured-failure cases

`error-config-args-malformed`, `error-r13-standard-source-failure`,
`r11-flow-conversation-model-failure`, `r11-validated-pipeline-structured-failure`,
`r13-validated-pipeline-config-failure` assert a structured Outcome
(`none(...)`/`err(...)`) on stdout rather than a stderr exception. These are
R11/R13 host-adapter/provider-boundary Outcomes, not the CLI exact-stderr
surface; they are R16-taxonomy-adjacent (host-adapter outcome, not a Genia
program exception) and out of scope for R19's diagnostic A/B/C work — noted
here only so the inventory is visibly complete over all 146 cases, not
silently skipped.

## 3. Parse vs. error/CLI diagnostic-surface reconciliation (contract Section 5.3)

`spec/parse/*.yaml` asserts parser/lexer `SyntaxError` identity as
**type + message substring**, executed at the parse phase before evaluation
begins. Four genuine parse-failure cases exist today:
`parse-error-unclosed-paren`, `parse-error-named-pattern-declaration-arity`,
`parse-error-named-pattern-use-arity`, `parse-dot-named-access-trailing-dot-error`.

Separately, one `spec/error/*` case — `error-parse-bad-rest-pattern`
(`Error: ..rest must be the final item in a list pattern`) — is *also*
parser-originated (a `SyntaxError` raised by `src/genia/parser.py`) but is
asserted through the CLI exact-stderr surface instead of the parse-phase
type+substring surface, because its trigger source is invoked through the
CLI path in that spec case rather than the parser harness directly.

**Reconciliation finding**: both surfaces already derive from the *same*
underlying `SyntaxError` object and its `str(exc)` message — there is no
contradiction today (the CLI surface is simply "parse phase's own message,
now also wrapped by `Error: ` and asserted exactly" rather than a
differently-worded restatement). The semantic identity (type = `SyntaxError`,
message = the parser's own text) is single-sourced. **No reconciliation
work is required for E19-3** beyond documenting this: parse identity remains
type + stable message text; the CLI/error surface's "deterministic fully
rendered message" is that same text plus the shared `Error: ` wrapper, not a
second independent wording. The `parser.py`/`lexer.py` `{...!r}` findings
noted under "format-template" above recur here too (e.g.
`src/genia/parser.py:133,205,216,314,325,400,427,431,743,897,954,1004`, and
`src/genia/lexer.py:184,232,249,294` all use `{token_text!r}` /
`{ch!r}`-style Python repr on **source-text tokens**, not Genia runtime
values) — same low-severity "Python quoting convention on a closed
lexical-grammar string" pattern as the format-spec case, flagged for E19-3
to assess uniformly across both families rather than fixed piecemeal.

## 4. Security / redaction review

Grepped all 146 exact-stderr messages for protected/secret-adjacent content:
the four `protected-value` family cases (`error-r10-cross-mode-protected-print`,
`error-represent-reserved-secret`, `error-representation-match-reserved-secret`,
`error-strip-representation-reserved-secret`) are the only ones that mention
protection at all, and all four assert **non-disclosure** text (e.g.
`protected-value: print`, `cannot use reserved protected facet "secret"`) —
none interpolate a payload, carrier identity, or redacted value. No case in
the full 146 interpolates a protected/declassified value. This matches the
R10 non-leakage invariant and requires no E19-3 change.

## 5. Summary for E19-3

Two concrete, minimal, approved-scope fixes are identified for E19-3:

1. **`evaluator.py` pattern-match-miss `{args!r}`** (lines 860, 862, 1369) —
   replace Python `repr()` of the runtime argument tuple with Genia
   `format_debug` rendering of each argument, joined the same way. Requires
   deliberately updating three existing exact-stderr cases
   (`error-lambda-pattern-miss`, `error-pattern-guard-all-fail`,
   `error-pattern-miss`) — call this out explicitly in the E19-3 PR per
   contract Section 5.2.
2. **`{...!r}` on closed-grammar source tokens** in `_format_engine.py`
   (format-spec strings) and `parser.py`/`lexer.py` (lexer token text) —
   lower-severity, same host-quoting-convention issue; E19-3 should decide
   whether to normalize these to an explicit Genia-authored quoting rule or
   accept them as out-of-scope host-adjacent formatting of source-grammar
   tokens (not runtime values), and record that decision.

No other family shows a host-wording leak, a protected-value interpolation
risk, or a parse/error contradiction. The remaining ~140 cases are
classified **A** (stable literal templates, safe to keep as exact-text
regression evidence) or **B** (the type-check family, whose rendering
already uses `_runtime_type_name`, a portable Genia-authored table).

## 6. Full per-case listing

Total spec/error cases: 146

### family: arity/dispatch (6 cases)

- `collect-validated-wrong-arity-two` — `Error: No matching function: collect_validated/2. Available: collect_validated/1`
- `collect-validated-wrong-arity-zero` — `Error: No matching function: collect_validated/0. Available: collect_validated/1`
- `diagnostic-error-wrong-arity` — `Error: No matching function: diagnostic_error/3. Available: diagnostic_error/4`
- `diagnostic-field-wrong-arity` — `Error: No matching function: diagnostic_field/0. Available: diagnostic_field/1`
- `diagnostic-reason-wrong-arity` — `Error: No matching function: diagnostic_reason/2. Available: diagnostic_reason/1`
- `diagnostic-skipped-wrong-arity` — `Error: No matching function: diagnostic_skipped/5. Available: diagnostic_skipped/4`

### family: assert-surface (1 case)

- `r18-surface-assert-eq-rejects-cross-kind` — `Error: assert_eq failed`

### family: config (1 case)

- `error-config-provider-invalid-values` — `Error: config_provider expected valid string keys and string values at source index 0`

### family: eval-core (2 cases)

- `error-eval-assignment-target` — `Error: Assignment target must be a simple name`
- `error-eval-undefined-name` — `Error: Undefined name: undefined_name`

### family: format-template (28 cases)

- `error-format-compose-missing-placeholder` — `Error: format missing field: missing`
- `error-format-debug-composed-spec` — `Error: format-error: unsupported format spec '?>10'`
- `error-format-field-bare-width` — `Error: format-error: unsupported format spec '10'`
- `error-format-field-bool-zero-pad` — `Error: format-error: format spec '03' requires numeric value`
- `error-format-field-combined-spec` — `Error: format-error: unsupported format spec '05.2'`
- `error-format-field-empty-spec` — `Error: format-error: invalid format spec ''`
- `error-format-field-grouping-non-numeric` — `Error: format-error: format spec ',' requires numeric value`
- `error-format-field-incomplete-align` — `Error: format-error: invalid format spec '<'`
- `error-format-field-path-invalid-double-dot` — `Error: format invalid placeholder`
- `error-format-field-path-invalid-index` — `Error: format invalid placeholder`
- `error-format-field-path-invalid-leading-dot` — `Error: format invalid placeholder`
- `error-format-field-path-invalid-trailing-dot` — `Error: format invalid placeholder`
- `error-format-field-path-missing-nested` — `Error: format missing field: user.name`
- `error-format-field-path-missing-top-level` — `Error: format missing field: user.name`
- `error-format-field-path-mixed-slash-dot` — `Error: format invalid placeholder`
- `error-format-field-path-non-map-intermediate` — `Error: format expected a map while resolving placeholder path: user.name`
- `error-format-field-path-slash-nested` — `Error: format invalid placeholder`
- `error-format-field-path-slash-separator` — `Error: format invalid placeholder`
- `error-format-field-precision-non-string-non-numeric` — `Error: format-error: format spec '.2' requires string or numeric value`
- `error-format-field-zero-pad-non-numeric` — `Error: format-error: format spec '03' requires numeric value`
- `error-format-invalid-placeholder-empty` — `Error: format invalid placeholder`
- `error-format-invalid-placeholder-whitespace` — `Error: format invalid placeholder`
- `error-format-missing-named-field` — `Error: format missing field: name`
- `error-format-missing-positional-field` — `Error: format missing field: 1`
- `error-format-named-non-map` — `Error: format expected a map for named placeholder: name`
- `error-format-positional-non-list` — `Error: format expected a list for positional placeholder: 0`
- `error-format-unmatched-left-brace` — `Error: format invalid placeholder`
- `error-format-unmatched-right-brace` — `Error: format invalid placeholder`

### family: glob-pattern (1 case)

- `error-pattern-glob-malformed` — `Error: Invalid glob pattern: unterminated character class`

### family: import (2 cases)

- `error-import-disallowed-host` — `Error: Host module not allowed: python.os`
- `error-import-missing-module` — `Error: Module not found: definitely_not_a_real_module_xyz`

### family: map-key-legality (4 cases)

- `error-represented-unsupported-map-key` — `Error: map key type is not supported: GeniaMap`
- `r18-map-key-nan-rejected-on-lookup` — `Error: map key must equal itself; NaN is not a legal map key`
- `r18-map-key-nan-rejected` — `Error: map key must equal itself; NaN is not a legal map key`
- `r18-map-key-nested-nan-rejected` — `Error: map key must equal itself; NaN is not a legal map key`

### family: model/provider (2 cases)

- `error-model-empty-messages` — `Error: model request expected a non-empty messages list`
- `error-r12-grounded-provider-failure` — `Error: embed expected query text to be a non-empty string`

### family: other (18 cases)

- `error-chunk-callback-non-list` — `Error: chunk chunker must return a list`
- `error-config-args-malformed` — `(no stderr / structured-outcome case)`
- `error-named-pattern-non-outcome-return` — `Error: named pattern Positive returned non-Outcome value`
- `error-named-pattern-ordinary-function` — `Error: Positive is not a named pattern`
- `error-named-pattern-unknown` — `Error: unknown named pattern Missing`
- `error-outcome-err-invalid-arity` — `Error: err(...) expects 1 or 2 arguments`
- `error-outcome-err-missing-reason` — `Error: err(...) expects 1 or 2 arguments`
- `error-outcome-some-invalid-arity` — `Error: some(...) expects 1 or 2 arguments`
- `error-outcome-some-zero-arg` — `Error: some(...) expects 1 or 2 arguments`
- `error-parse-bad-rest-pattern` — `Error: ..rest must be the final item in a list pattern`
- `error-r13-standard-source-failure` — `(no stderr / structured-outcome case)`
- `error-refinement-match-predicate-result` — `Error: refinement_match predicate must return bool, received int`
- `error-sheet-derive-duplicate-column` — `Error: derive expected a new column name; age already exists`
- `error-sheet-select-missing-column` — `Error: select could not find column city`
- `error-template-direct-call-non-outcome` — `Error: named pattern Bad returned non-Outcome value`
- `r11-flow-conversation-model-failure` — `(no stderr / structured-outcome case)`
- `r11-validated-pipeline-structured-failure` — `(no stderr / structured-outcome case)`
- `r13-validated-pipeline-config-failure` — `(no stderr / structured-outcome case)`

### family: pattern-match-miss (3 cases)

- `error-lambda-pattern-miss` — `Error: No matching case for arguments ([1],)`
- `error-pattern-guard-all-fail` — `Error: No matching case for function classify/1 with arguments (10,)`
- `error-pattern-miss` — `Error: No matching case for function f/1 with arguments (99,)`

### family: protected-value (4 cases)

- `error-r10-cross-mode-protected-print` — `Error: protected-value: print`
- `error-represent-reserved-secret` — `Error: represent cannot use reserved protected facet "secret"`
- `error-representation-match-reserved-secret` — `Error: representation_match cannot use reserved protected facet "secret"`
- `error-strip-representation-reserved-secret` — `Error: strip_representation cannot use reserved protected facet "secret"`

### family: representation (1 case)

- `error-represent-empty-facet` — `Error: represent expected a non-empty facet string`

### family: sheet/csv (5 cases)

- `error-collect-sheet-missing-column` — `Error: collect_sheet expected column age at row 1`
- `error-render-csv-not-sheet` — `Error: render_csv expected a Sheet`
- `error-row-get-missing-column` — `Error: row_get could not find column city`
- `error-row-get-not-row` — `Error: row_get expected a row (list of [name, value] pairs)`
- `error-sheet-unequal-column-lengths` — `Error: sheet expected all columns to have equal length`

### family: template/matcher (9 cases)

- `error-exact-shape-field-template-result` — `Error: exact_shape_match field age Template must return Outcome, received bool`
- `error-open-shape-field-template-result` — `Error: open_shape_match field age Template must return Outcome, received bool`
- `error-recursive-template-builder-return-type` — `Error: recursive_template builder must return a Template, received int`
- `error-template-at-assert-err` — `Error: @! assertion failed: matcher returned err: not-a-number`
- `error-template-at-assert-non-outcome-return` — `Error: matcher used with @! must return Outcome, received bool`
- `error-template-at-assert-none` — `Error: @! assertion failed: matcher returned none: not-positive`
- `error-template-at-check-non-outcome-return` — `Error: matcher used with @? must return Outcome, received bool`
- `error-template-compose-left-non-outcome-return` — `Error: matcher composed with & must return Outcome, received bool`
- `error-template-compose-right-non-outcome-return` — `Error: matcher composed with & must return Outcome, received bool`

### family: type-check (expected X, received Y) (57 cases)

- `collect-validated-non-outcome-item-error` — `Error: collect_validated expected Outcome items, received int at index 1`
- `collect-validated-non-seq-source-error` — `Error: collect_validated expected a Seq-compatible value (list or Flow); received int.`
- `diagnostic-field-non-map-error` — `Error: map_get expected a map as first argument, received string`
- `diagnostic-reason-non-map-error` — `Error: map_get expected a map as first argument, received int`
- `error-accumulate-non-callable` — `Error: accumulate expected callable Template, received int`
- `error-accumulate-opaque-template` — `Error: accumulate expected inspectable Template, received opaque Template`
- `error-alternatives-branch-template-type` — `Error: alternatives branch circle expected Template function, received int`
- `error-alternatives-branches-type` — `Error: alternatives expected branches Templates map, received int`
- `error-alternatives-discriminator-field-type` — `Error: alternatives expected non-empty discriminator field string, received int`
- `error-collect-sheet-not-seq` — `Error: collect_sheet expected a Seq-compatible value (list or Flow); received string.`
- `error-config-get-invalid-key` — `Error: config_get expected a non-empty configuration key string without NUL, received string`
- `error-config-get-or-default-noncallable` — `Error: pipeline stage expected a callable value, received int`
- `error-config-view-invalid-prefix` — `Error: config_view expected a prefix string without NUL, received string`
- `error-default-field-template-type` — `Error: default_field expected Template function, received int`
- `error-exact-shape-field-name` — `Error: exact_shape_match expected string field name, received int`
- `error-exact-shape-field-template-type` — `Error: exact_shape_match field age expected Template function, received int`
- `error-exact-shape-field-type` — `Error: exact_shape field name expected Template function, received int`
- `error-exact-shape-spec-type` — `Error: exact_shape_match expected field Templates map, received list`
- `error-format-compose-invalid-piece` — `Error: format_compose expected string or Format at index 1, received int`
- `error-format-compose-non-list` — `Error: format_compose expected list of format pieces, received int`
- `error-format-compose-string-argument` — `Error: format_compose expected list of format pieces, received string`
- `error-format-first-class-constructor-non-string` — `Error: Format expected template string, received int`
- `error-format-first-class-non-string-non-format` — `Error: format expected a string template or Format value, received int`
- `error-format-non-string-template` — `Error: format expected a string template or Format value, received int`
- `error-format-template-number-input` — `Error: format_template expected a format, received int`
- `error-format-template-string-input` — `Error: format_template expected a format, received string`
- `error-json-decode-input-type` — `Error: json_decode expected string or bytes, received int`
- `error-json-schema-input` — `Error: json_schema expected json-represented schema, received map`
- `error-json-schema-root-type` — `Error: json_schema expected represented schema map, received list`
- `error-json-schema-wrong-facet` — `Error: json_schema expected outer json representation, received csv`
- `error-model-structured-template` — `Error: model expected output template function, received int`
- `error-open-shape-field-name` — `Error: open_shape_match expected string field name, received int`
- `error-open-shape-field-template-type` — `Error: open_shape_match field age expected Template function, received int`
- `error-open-shape-field-type` — `Error: open_shape field name expected Template function, received int`
- `error-open-shape-spec-type` — `Error: open_shape_match expected field Templates map, received list`
- `error-recursive-template-builder-type` — `Error: recursive_template expected callable builder, received int`
- `error-recursive-template-max-depth-too-large` — `Error: recursive_template expected a positive integer max_depth of at most 100, received int`
- `error-recursive-template-name-type` — `Error: recursive_template expected non-empty reference name string, received int`
- `error-refinement-match-predicate-type` — `Error: refinement_match expected predicate function, received int`
- `error-refinement-predicate-type` — `Error: refinement expected predicate function, received int`
- `error-render-csv-unsupported-cell` — `Error: render_csv expected CSV scalar cell at row 0, column 0; received list`
- `error-representation-match-facet-type` — `Error: representation_match expected a non-empty facet string, received int`
- `error-secret-view-invalid-logical-name` — `Error: secret_view expected a non-empty logical name string without NUL, received string`
- `error-strip-representation-unrepresented` — `Error: strip_representation expected represented value, received int`
- `error-strip-representation-wrong-outer` — `Error: strip_representation expected outer facet inner, received outer`
- `error-template-at-assert-non-callable` — `Error: @! expected matcher function, received int`
- `error-template-at-check-non-callable` — `Error: @? expected matcher function, received int`
- `error-template-compose-left-non-callable` — `Error: & expected matcher function on left, received int`
- `error-template-compose-right-non-callable` — `Error: & expected matcher function on right, received int`
- `error-template-description-non-callable` — `Error: template_description expected callable Template, received int`
- `error-template-schema-non-callable` — `Error: template_schema expected callable Template, received int`
- `parse-csv-row-invalid-header-error` — `Error: parse_csv_row expected header at index 1 to be string, received int`
- `parse-csv-row-non-list-headers-error` — `Error: parse_csv_row expected headers to be a list, received string`
- `parse-csv-row-non-string-line-error` — `Error: parse_csv_row expected line to be string, received int`
- `parse-jsonl-record-non-string-error` — `Error: parse_jsonl_record expected a string, received int`
- `validate-each-rejects-non-list-source` — `Error: validate_each expected a list or Flow source, received map`
- `validate-each-rejects-non-outcome-validator-result` — `Error: validate_each expected validator to return an Outcome, received int at index 0`

### family: validated-pipeline (2 cases)

- `error-validated-pipeline-predicate-non-callable` — `Error: validate_field expected predicate to be callable`
- `validate-each-rejects-non-callable-validator` — `Error: validate_each expected validator to be callable`
