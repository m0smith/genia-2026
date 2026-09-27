# R26-2 — C++ Bytes/UTF-8 and Strict JSON Data Bridge Contract (E26-0)

Status: **Approved contract; not implemented by the C++ host.** Issue #1024
defines this focused portability slice under the completed R26 pre-flight
(#1015) and the R26-2 scope decision (issue comment on #1024, adopting
`docs/analysis/r26-release-size-preflight.md`'s architecture analysis).
`GENIA_STATE.md` remains final authority for implemented behavior.

## 1. Purpose and scope

This contract defines the portable data-bridge boundary a C++ host must
satisfy before claiming the (to-be-split) `bytes_json_zip` capability family
for **Bytes/UTF-8 and strict JSON only**. It does not cover:

- **ZIP** (`zip_entries`/`zip_read`/`zip_write`/`entry_*`) — removed from R26
  entirely per the scope decision on #1024. Zero shared evidence exists, the
  public surface splits across eager and Flow-based access, raw filesystem
  authority is unreconciled with R35, and the DEFLATE dependency question is
  unreviewed. Deferred to a later, contract-first placement.
- **Compatibility JSON** (`json_parse`/`json_stringify`/`json_pretty`) and
  **`parse_jsonl_record`** — decided **not portable** by this contract (see
  section 5). They remain Python-host-only.
- **`json_schema`** — depends on the Template runtime, which no C++ release
  through R27 schedules.
- REPL (#1023), Flow, pipe mode, HTTP, resource I/O, shell-stage, external
  process execution, AI/retrieval/config/provider gaps.

`bytes_utf8` and `json_strict` are independently claimable capabilities. A
host may claim one without the other (`json_strict`'s Bytes-input path is the
one place it consumes `bytes_utf8`; that dependency is explicit, not implicit
capability coupling).

## 2. Portable observations — Bytes/UTF-8 (`bytes_utf8`)

A host declaring `bytes_utf8: supported` must provide:

1. **Bytes value.** Opaque, not a map key (map-key rejection is a
   deterministic misuse diagnostic, never a Python `TypeError`/`ValueError`
   class name). Two independently constructed byte values with the same
   bytes are equal (R18).
2. **`utf8_encode(string) -> bytes`.** Total for any Genia string (Genia
   strings are already-validated Unicode scalar sequences; no encode failure
   exists for well-formed input).
3. **`utf8_decode(bytes) -> string`, well-formed input.** Round-trips
   `utf8_encode`. Already covered by `spec/eval/r19-unicode-utf8-encode-decode-roundtrip.yaml`.
4. **`utf8_decode(bytes) -> string`, malformed input.** Deterministic misuse
   failure, never U+FFFD replacement, never raw host decoder text. The exact
   byte-offset semantics for overlong encodings, surrogate-encoded bytes
   (`ED A0..`), out-of-range (`> U+10FFFF`), and truncated sequences are
   **not separately pinned by this contract** — this is the one item
   deferred to section 6's evidence-route decision, since Genia source has
   no way to construct arbitrary malformed bytes to prove it today.
5. **Display.** `<bytes N>` where `N` is the exact byte count (not a
   character count, not a capacity).

Host-local: internal buffer representation, allocation strategy, whether the
same in-house UTF-8 validator source decoding already requires is reused for
`utf8_decode` (recommended, not required).

## 3. Portable observations — strict JSON (`json_strict`)

A host declaring `json_strict: supported` must provide `json_decode`/
`json_encode` matching every pinned detail below. This section makes no
change to already-documented R9/R23 behavior; it pins the details the
architecture doc found undocumented and inherits R24/E24-7's numeric path
unchanged (section 4).

### 3.1 Value mapping and facets (unchanged, restated for completeness)

- `json_decode(string_or_bytes) -> some(represent("json", root), context) | err(reason, context)`.
  `root` is an ordinary map/list/string/number/boolean/`nil` value; nested
  values carry no implicit representation facet.
- `json_encode(value) -> some(json_text, context) | err(reason, context)`.
  Accepts one outer `json`-represented supported value or a supported
  ordinary value, consuming only that optional outer layer.
- Objects decode to persistent ordered map values; encode preserves list
  order and sorts object member names (section 3.4).

### 3.2 Limits

- Safe integers: `[-9007199254740991, 9007199254740991]`.
- Nesting: at most 128 nested object/array containers (decode and encode).
- No duplicate object member names (decode).
- Unicode: strings/names must be valid Unicode scalar sequences (no lone
  surrogates U+D800-U+DFFF).
- Numeric stability: a fraction/exponent number decodes to an exact
  `GeniaDecimal` only when `stable_json_decimal` holds; a `GeniaRational`
  encodes only when its exact terminating-Decimal equivalent is itself
  `stable_json_decimal`; a finite Float64 encodes via its canonical
  shortest-roundtrip decimal spelling; NaN/Infinity are rejected in both
  directions. This is the E24-7 numeric path — see section 4.
- **Decode exponent/digit resource bound.** A JSON number token whose
  lexical magnitude would require expanding an astronomically large exact
  value (in practice: an exponent whose `10 ** exponent` expansion would
  exceed the numeric runtime's private resource-limit bound) fails
  deterministically as a `NumericResourceLimitError`
  (`"numeric-resource-limit"`), the same program-terminating diagnostic
  every other exact-numeric resource-limit failure already uses (R22
  contract section 11) — **not** a recoverable `err(json_number_out_of_range, ...)`
  Outcome, and not a hang. This was a genuine defect prior to this
  contract (see section 7, item 1) and is now repaired in the reference
  host (`GeniaDecimal._as_fraction`).
- **Nesting resource bound.** Nesting deeper than 128 is a strict-decode
  `err(json_nesting_too_deep, ...)` Outcome as already documented. Deep
  nesting anywhere in the compatibility surface (out of portable scope,
  see section 5) or in `json_stringify`/`json_encode`'s own traversal is a
  clean, deterministic diagnostic and never a raw Python `RecursionError`
  (repaired, section 7 item 3).

### 3.3 Key-sort basis

Object member names are sorted by Unicode code point order (not UTF-16 code
unit order, not locale-sensitive collation). Confirmed by direct probing:
encoding a map with keys `{"b", "a", "Z", "z", "A"}` produces the order
`"A", "Z", "a", "b", "z"` — plain code-point ordering, uppercase ASCII before
lowercase ASCII.

### 3.4 Escape set

`json_encode` escapes only: `"`, `\`, and control characters below U+0020
(as `\uXXXX`, e.g. `\u0001`; `\t`/`\n`/`\r`/etc. use their short escapes).
It does **not** escape: `/`, DEL (U+007F), U+2028, U+2029, or any non-ASCII
Unicode scalar (non-ASCII text is emitted directly, not `\uXXXX`-escaped).
Confirmed by direct probing.

### 3.5 Layout

- 2-space indentation; one member/element per line for a non-empty
  object/array.
- Key separator: `": "` (colon, one space). Item separator: `,` followed by
  a newline (no trailing comma).
- Empty object: `{}`. Empty array: `[]`. Neither contains internal
  whitespace or a newline.
- No trailing newline at the end of the encoded document.

### 3.6 BOM handling

A leading U+FEFF (byte-order mark) is **not** stripped and is **not**
accepted as insignificant whitespace; a document beginning with U+FEFF is
`err(invalid_json, ...)`. Confirmed by direct probing.

### 3.7 `line`/`column` semantics

`line` and `column` are 1-based. `column` is a **code-point** column within
`line` (not a byte offset, not a UTF-16 code-unit offset) — this is exactly
what Python's JSON scanner already computes and is now the pinned portable
semantics, not merely an implementation artifact. Existing shared cases
already assert specific `line`/`column` values against this exact
computation; no case is retroactively invalidated by pinning it.

### 3.8 Error precedence

When more than one condition applies to the same input (for example, a
duplicate key whose value is also out of numeric range), the first
condition encountered during the single left-to-right/depth-first scan wins
— there is no independent severity ranking between reasons. This matches
existing scanner-hook order (`object_pairs_hook`/`parse_int`/`parse_float`
fire as each token is scanned, before the container that holds them is
fully built) and requires no implementation change.

### 3.9 `value_type` vocabulary

`value_type` in an `unsupported_json_value` context is one of the exact
names `_runtime_type_name` already returns: `none`, `some(...)`, `err`,
`bool`, `int`, `decimal`, `rational`, `float`, `symbol`, `string`, `list`,
`map`, `named-pattern`, `flow`, `rng`, `ref`, `process`, `sink`, `bytes`,
`zip_entry`, `python_handle`, `pair`, `stdin`, `format`, `represented`,
`protected`, `declassification-authority`, `config-provider`,
`model-provider`, `index-handle`, `function`, `meta_env`, `promise`, or
`map-key` (used specifically for a non-string/symbol object key, not a
top-level value). This vocabulary is not closed to future additions as new
runtime value kinds are added, but it must always be a name from this
table, never a raw Python class name. The `GeniaSymbol` class-name leak
this section closes is repaired (section 7, item 2).

### 3.10 Reasons and context

Unchanged from current documented behavior: `invalid_json`,
`invalid_json_utf8`, `duplicate_json_key`, `json_number_out_of_range`,
`invalid_json_unicode`, `json_nesting_too_deep`, `unsupported_json_value`.
Context carries `kind: quote(json)`, `operation: quote(decode|encode)`,
`status`, `reason`, plus `line`/`column` (malformed syntax),
`key` (duplicate), `value_type` (unsupported encoding), and `cause`
(further distinguishing `json_number_out_of_range`'s several underlying
causes: `integer_out_of_range`, `decimal_unstable`, `rational_unstable`,
`float_non_finite`, `non_finite_constant`).

## 4. Inheritance from R24/E24-7 (not re-derived)

R26-2 **inherits, and must not re-derive or replace**, the numeric codec
path R24's E24-3/E24-7 already established in the bounded C++ host:

- the Bytes value, structural equality, and `utf8_encode` for well-formed
  input (E24-3);
- the scalar-numeric slice of `json_encode`/`json_decode`: R23 canonical
  numeric text, the `stable_json_decimal` check, Rational termination,
  Float64 finite spelling, lexical fraction→Decimal decode (E24-7);
- the R9 `represent`/`representation_match("json")` facet carrier needed to
  observe them.

R26-2 widens the codec **around** that numeric path (objects, arrays,
strings, Unicode, limits, Bytes input, layout, diagnostics) using the same
`parse_int`/`parse_float`/`object_pairs_hook` composition already
implemented on the Python side. A C++ implementation must reuse whatever its
own equivalent hook points are; it must not maintain two independent numeric
parsers.

## 5. Compatibility JSON portability decision

**Decided: not portable. Remains Python-host-only.**

`json_parse`, `json_stringify`, `json_pretty`, and `parse_jsonl_record` stay
outside the `json_strict`/`bytes_utf8` capability boundary and outside any
future C++ host-parity obligation, for these reasons:

- Their failure shape is `none(reason, context)` (or, for `parse_jsonl_record`,
  `err(...)`), not the `err(reason, context)` shape strict JSON uses, and the
  `message` field has historically carried Python's own exception text
  (`exc.msg`) — a durable Python-host-only property, not a portability gap
  this contract closes.
- They are deliberately permissive (accept `NaN`/`Infinity`, never enforce
  `stable_json_decimal`) by design (R23 contract section 6, "graceful legacy
  tolerance") — a different contract shape than strict JSON, not a stricter
  or laxer version of the same one.
- `parse_jsonl_record` is the most killer-workflow-relevant surface here, but
  promoting it independently of `json_parse`/`json_stringify` would still
  need its own dedicated contract (it already returns Outcomes with
  reasonably clean context, unlike the other three) — deferred as a
  separate, explicitly-approved future ticket, not decided by omission here.
- This keeps the C++ host's obligation bounded to the actually-well-specified
  strict boundary, consistent with the "no Python/C++ feature parity" rule.

**Consequence:** every currently-ungated shared spec case exercising
`json_parse`/`json_stringify`/`json_pretty`/`parse_jsonl_record`/`json_schema`
must be retro-gated with an appropriate `requires:` capability (a
`json_compat` capability for the first three, distinct from `json_strict`)
so a future C++ host is never silently on the hook for them merely because
they currently have no `requires:` tag. This retro-gating is **implementation
work for the next E26 slice**, not performed by this contract document.

## 6. Malformed-UTF-8 evidence route decision

**Decided: explicitly narrow the portable claim to well-formed
`utf8_decode` input for shared executable evidence; malformed-input
behavior is proven host-locally only, for now.**

Genia source has no way to construct arbitrary invalid-UTF-8 bytes today (no
portable byte-construction function, no `resource_io`-gated fixture file
mechanism approved for this purpose). Two routes exist to close this later:

- a portable byte-construction function (new language surface, needs its own
  separately-approved contract — out of scope here); or
- a `resource_io`-gated fixture file containing known-malformed bytes read
  through the existing resource bridge (also needs its own approval, since
  `resource_io` itself remains a separate gap).

Until one of those is separately approved, `bytes_utf8` capability claims
rest on well-formed-input shared evidence plus host-local malformed-input
tests. This is an explicit, honest narrowing, not a silent gap: any doc
claiming `bytes_utf8: supported` must say so.

## 7. Reference-host defect status

Three defects the preflight found are **repaired** (see `GENIA_STATE.md`'s
R26-2 entry and the referenced test files):

1. Unbounded `json_decode`/`json_encode` resource-exhaustion hang via
   `GeniaDecimal._as_fraction()` — repaired.
2. `_runtime_type_name`'s `GeniaSymbol` → raw class-name leak — repaired.
3. Uncaught `RecursionError` leaks in `json_parse`, `parse_jsonl_record`,
   `json_stringify`, `json_encode` — repaired.

Two items the preflight raised are **not** defects requiring a fix, per the
decisions above:

- Compatibility `json_parse("NaN")`/`"Infinity"` producing non-finite
  Float64 values is expected, permissive compat-JSON behavior (section 5),
  not a leak.
- Compatibility JSON's lone-surrogate/Python-`exc.msg`-in-context behavior is
  inherent to its Python-host-only, not-portable status (section 5); it is
  not repaired because it is not in the portable contract to begin with.

## 8. Host-local mechanics

Not part of `bytes_utf8`/`json_strict` conformance: internal Bytes buffer
representation, whether a host reuses one UTF-8 validator for both source
decoding and `utf8_decode`, native JSON parser/lexer implementation
strategy (a C++ host may not delegate JSON-visible behavior to
`nlohmann/json` or any third-party library per the existing dependency
policy — `docs/design/r24/dependency-toolchain-policy.md` limits it to the
E16-1 adapter transport only), and allocation/performance characteristics.

## 9. Evidence boundary

Shared executable evidence for `bytes_utf8` and `json_strict` uses the
existing `eval` category (ordinary function calls, no new CLI shape needed —
unlike REPL, no protocol/loader change is required here). Every case
exercising a `json_strict`-only construct not already covered by the
inherited E24-7 numeric cases needs `requires: [json_strict]`, and every
`bytes_utf8`-only case needs `requires: [bytes_utf8]`, once those
capabilities exist in `spec/manifest.json`. Adding those capability names,
retro-gating the existing ungated cases, and adding the missing coverage
this contract identifies (nesting 128/129 boundary cases, lone/paired
surrogate cases, `invalid_json_utf8`, duplicate-key `key` context, BOM
rejection, layout/escape-set cases) is the next E26 implementation slice,
not this contract.

## 10. Exclusions

This contract adds no syntax, parser form, Core IR node, evaluator
behavior, new builtin, prelude function, Flow behavior, pipe behavior, ZIP
behavior, or C++ implementation. It does not claim Python/C++ feature
parity. It changes no already-documented portable JSON/Bytes semantics —
every pin in section 3 restates existing, already-implemented Python
behavior; nothing here is new runtime behavior.

Implementation (capability vocabulary addition, retro-gating, missing
shared cases, then C++ implementation) is separate follow-up work.
