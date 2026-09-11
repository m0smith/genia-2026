# R19 Unicode and Diagnostic Portability Contract

Status: **APPROVED FOR IMPLEMENTATION — E19-0 complete; GO for E19-1.** `GENIA_STATE.md` remains final authority for implemented behavior. This contract approval does not by itself make any R19 behavior implemented.

R19 follows completed R17 Numeric and Ordered-Map Portability and R18 Portable Value Equality. Its purpose is to remove remaining Python-default dependencies from byte-observable string and diagnostic surfaces before a second production host implements them.

Numeric-model work formerly represented by blocker F1 is explicitly split out. See `docs/design/exact-numeric-model-preflight.md` and `docs/design/exact-numeric-model-resolved-decisions.md`.

## 1. Scope

R19 defines portable behavior for:

1. Genia string/code-point and UTF-8 boundary semantics already exposed by current surfaces.
2. Deterministic string debug escaping.
3. The boundary between portable Genia diagnostics and host-local exception/error wording.
4. Shared conformance evidence sufficient for a non-Python host to implement those rules without consulting Python runtime behavior.

R19 does not add a new language syntax, grapheme-cluster model, locale-aware formatting, Decimal/Rational/Float64 numeric model, new error hierarchy, or C++ implementation.

## 2. Governing portability rule

> A conforming host must be able to reproduce contracted string operations and portable diagnostics from this written contract and shared evidence alone. Python `str`, exception messages, and library defaults are implementation mechanisms, never semantic authority.

## 3. Unicode/string contract

### 3.1 String semantic unit

**Approved E19-0 rule:** A Genia string is an ordered sequence of Unicode scalar values. Public string iteration and code-point slicing operate on those scalar values, not UTF-8 bytes and not grapheme clusters.

Consequences:

- supplementary-plane characters are one string element/code point
- a user-perceived grapheme composed from multiple code points remains multiple elements
- UTF-8 encoding length is a separate byte-level property

No implicit Unicode normalization is performed by the string model. Canonically equivalent but differently encoded code-point sequences remain different values unless another separately approved operation explicitly normalizes them. This preserves current structural string equality.

### 3.2 UTF-8 encoding and boundaries

At explicit string/byte boundaries, the portable encoding is UTF-8.

For a valid Genia string:

- UTF-8 byte length is the number of bytes in its UTF-8 encoding
- byte offset `0` and byte offset equal to byte length are valid boundaries
- an interior offset is a boundary iff it points to the first byte of a UTF-8 encoded scalar value
- offsets below zero or above byte length are not boundaries

A boundary query is observational only; it does not slice or decode data.

### 3.3 Code-point iteration and slicing — U1 approved

Iteration produces each Unicode scalar value in sequence order.

Slicing operates on code-point indices with the following exact bound normalization:

- omitted start -> `0`
- omitted end -> code-point length
- a negative index counts backward from the end by adding the code-point length
- after negative adjustment, a bound below `0` clamps to `0`
- a bound above length clamps to length
- when normalized start is greater than or equal to normalized end, the result is the empty string

Examples for `"abcdef"`:

- `[1:4]` -> `"bcd"`
- `[-2:]` -> `"ef"`
- `[0:100]` -> `"abcdef"`
- `[100:200]` -> `""`
- `[4:2]` -> `""`

These rules are the portable contract; Python slicing is not semantic authority even where current behavior agrees.

### 3.4 Invalid UTF-8 — U2 approved

Malformed UTF-8 can arise only at an explicit bytes-to-string or host input boundary; an already-constructed Genia string cannot contain an invalid Unicode scalar encoding.

Where an existing boundary claims to decode UTF-8:

- valid input decodes to the exact Unicode scalar sequence
- malformed input fails deterministically
- implicit replacement with U+FFFD is forbidden
- raw host decoder exception wording is forbidden at the portable boundary
- the existing boundary-specific Outcome/diagnostic model remains authoritative unless separately changed through its own gate

R19 does not invent a universal public decode API merely to exercise malformed input.

### 3.5 String display/debug — U3 approved

Display of an ordinary string is its raw character sequence with no surrounding quotes.

Debug rendering surrounds the string with ASCII double quotes and uses deterministic Genia escaping.

Required short escapes:

- backslash -> `\\`
- double quote -> `\"`
- newline -> `\n`
- carriage return -> `\r`
- tab -> `\t`

Every other C0 control scalar (`U+0000..U+001F`), DEL (`U+007F`), and C1 control scalar (`U+0080..U+009F`) renders as `\uXXXX` using exactly four lowercase hexadecimal digits.

All other Unicode scalar values render literally.

This rule avoids dependence on host terminal behavior or host Unicode printability tables.

## 4. Numeric work split from R19

The original R19 draft contained blocker F1 for canonical finite binary-float rendering. That blocker is withdrawn from R19 rather than resolved here.

Reason: the preferred language direction now requires a separate semantic contract for an exact numeric family:

- arbitrary-precision Integer
- arbitrary-precision Decimal as the default fractional/decimal-literal model
- exact Rational values for non-terminating exact quotients
- explicit IEEE-754 Float64 for deliberate approximate/high-performance/interoperability use

That work affects parser/Core IR/arithmetic/division/equality/map keys/JSON/conversions/formatting and therefore requires its own release gate. R19 must not canonize current Python `float` behavior as the future default numeric model.

Current float behavior remains implemented truth until that later release actually changes it.

## 5. Diagnostic portability contract

### 5.1 Diagnostic classes

Every observed failure belongs to one of these portability classes:

**A. Exact portable diagnostic text** — wording is part of the language contract and shared evidence compares exact normalized text.

**B. Portable diagnostic identity with normalized rendering** — phase/category/reason/parameters are semantic; a deterministic normalized text rendering may be used at CLI/shared boundaries.

**C. Host-local/incidental diagnostic detail** — host exception/library/OS wording is not Genia semantics and must not leak into an A/B boundary.

R19 does not require these letters to become public runtime values or runner fields.

### 5.2 Existing exact error specs

Current shared `spec/error` cases compare exact `stderr`. Until an approved R19 diagnostic slice changes a case deliberately, those existing exact expectations remain regression evidence.

R19 MUST NOT silently reword all errors as a cleanup exercise.

Before diagnostic implementation, the diagnostic inventory slice MUST generate the complete mapping from exact assertions to:

- trigger/spec case
- phase
- semantic family
- construction site
- dynamic interpolations
- rendering function used for values
- proposed A/B/C classification

### 5.3 Parse diagnostic reconciliation

Current parse shared specs assert parse failure type plus a message substring, while some parse-origin errors may also surface through exact-stderr error cases.

R19 MUST reconcile those surfaces so one failure does not acquire contradictory portable contracts.

The parse semantic identity may remain type + stable message component while the error/CLI surface defines a deterministic fully rendered message, provided both derive from the same approved diagnostic meaning.

### 5.4 Host exception boundary

The following are never portable Genia diagnostic text unless a later explicit contract says otherwise:

- Python exception class/message text
- C++/STL exception wording
- compiler/runtime-specific type names
- OS/library error strings
- demangled/native symbol names

A host must normalize such failures before they cross an A/B portable boundary.

### 5.5 Diagnostic value rendering

When a portable diagnostic interpolates a Genia value, it MUST use an explicitly named Genia rendering rule (display/debug/safe diagnostic formatter), not host `str`/`repr`.

Protected/security-sensitive values retain existing redaction and non-leakage invariants. R19 cannot weaken R10/R18 protection semantics for better diagnostics.

Numeric diagnostic rendering that depends on the future Decimal/Rational/Float64 model must not be prematurely frozen by R19; current exact regression evidence remains until the numeric release deliberately changes that surface.

### 5.6 Centralization rule

R19 MAY centralize stable diagnostic templates/identifiers where inventory shows repeated or portability-sensitive construction.

It MUST NOT require:

- a runtime-loaded message catalog
- localization infrastructure
- a public diagnostic class hierarchy
- wholesale conversion of every internal exception into a new object system

The smallest portable mechanism that prevents host-default drift is preferred.

## 6. Cross-release invariants

R19 MUST preserve:

- R17 deterministic ordered-map behavior
- current R18 equality, map-key equivalence, identity/opaque/protected equality semantics
- R9 JSON-specific representation rules
- R10 protected-value sinks/declassification/non-leakage
- R16 adapter protocol outcome taxonomy

In particular:

- no Unicode normalization changes `==`
- no diagnostic improvement exposes protected payloads
- no runner crash/protocol outcome is reclassified as a Genia program diagnostic
- no R19 rule pre-empts the separately gated exact numeric model

## 7. Shared conformance evidence

After approval, R19 must add enough shared evidence that a non-Python host can implement the contract without reading Python source.

Minimum Unicode families:

- 1/2/3/4-byte UTF-8 representatives
- approved negative/out-of-range code-point slicing
- combining-sequence behavior
- UTF-8 byte length/boundaries
- exact approved debug escaping
- explicit malformed UTF-8 behavior for existing covered boundaries

Minimum diagnostic families:

- exact runtime misuse
- parse failure normalization
- CLI misuse
- dynamic-value interpolation
- protected redaction
- normalized host exception boundary representative

These families are approved as the minimum independent-host evidence set. Implementation slices may add narrower regression cases where needed, but may not weaken these families.

## 8. Expected implementation slices

Approved sequencing:

- E19-1 Unicode semantics/evidence
- E19-2 complete diagnostic assertion/source inventory
- E19-3 diagnostic portability normalization/evidence
- E19-4 cross-surface host-default leak audit
- E19-5 truth/docs/release sync
- E19-6 skeptical release audit/distillation

No slice may use a later slice as implicit authority.

## 9. Explicit non-goals

- grapheme clusters
- normalization/collation API
- locale-aware output
- Decimal/Rational/Float64 implementation
- approximate equality
- total numeric ordering
- error-category redesign
- public diagnostic-code API
- localization
- Open Functions
- C++ host implementation

## 10. Contract approval checklist

- [x] U1 exact code-point slice bounds/negative-index behavior is pinned
- [x] U2 invalid-UTF-8 decode rule is strict, deterministic, and boundary-preserving
- [x] U3 C0/DEL/C1 debug escaping is pinned
- [x] F1 is removed from R19 and assigned to a separate exact-numeric-model gate
- [x] diagnostic mechanical inventory procedure is accepted: E19-2 must mechanically map each exact/substring assertion to trigger, phase, semantic family, construction site, interpolation/rendering, security implications, and A/B/C classification before diagnostic normalization begins
- [x] R17/R18/R9/R10/R16 compatibility review passes: R19 preserves ordered-map semantics, equality/key behavior, JSON boundaries, protected-value non-leakage, and adapter-protocol outcome taxonomy; no conflicting semantic change is introduced
- [x] proposed shared case families are sufficient for the independent-host acceptance criterion: Unicode width/boundary/slicing/combining/escaping/malformed-input families plus runtime/parse/CLI/interpolation/redaction/host-exception diagnostic families establish the required portable observable surface

## Approval result

**E19-0 is approved and complete. GO for E19-1 — Unicode semantics/evidence.**

This approval authorizes only the ordered R19 implementation process above. It does not authorize Decimal/Rational/Float64 work under R19, does not make any R19 behavior implemented, and does not advance R20 or R21 prerequisites.

## Critical acceptance criterion for completed R19

A non-Python host can reproduce contracted Unicode/string behavior and portable diagnostic output from the approved written contract and shared evidence alone, byte-for-byte where the contract says text is exact, without using Python `str`, exception strings, or Python implementation source as an undocumented specification.
