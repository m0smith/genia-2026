# R19 Unicode, Float, and Diagnostic Portability Contract

Status: **DRAFT FOR APPROVAL — non-authoritative, not implemented by this document.** `GENIA_STATE.md` remains final authority for implemented behavior.

R19 follows completed R17 Numeric and Ordered-Map Portability and R18 Portable Value Equality. Its purpose is to remove remaining Python-default dependencies from byte-observable string, float-rendering, and diagnostic surfaces before a second production host implements them.

## 1. Scope

R19 defines portable behavior for:

1. Genia string/code-point and UTF-8 boundary semantics already exposed by current surfaces.
2. Canonical float display/debug text.
3. The boundary between portable Genia diagnostics and host-local exception/error wording.
4. Shared conformance evidence sufficient for a non-Python host to implement those rules without consulting Python runtime behavior.

R19 does not add a new language syntax, new numeric type, new error hierarchy, grapheme-cluster model, locale-aware formatting, or C++ implementation.

## 2. Governing portability rule

> A conforming host must be able to reproduce contracted string operations, float rendering, and portable diagnostics from this written contract and shared evidence alone. Python `str`, `repr`, exception messages, and library defaults are implementation mechanisms, never semantic authority.

## 3. Unicode/string contract

### 3.1 String semantic unit

**Proposed rule:** A Genia string is an ordered sequence of Unicode scalar values. Public string iteration and code-point slicing operate on those scalar values, not UTF-8 bytes and not grapheme clusters.

Consequences:

- supplementary-plane characters are one string element/code point
- a user-perceived grapheme composed from multiple code points remains multiple elements
- UTF-8 encoding length is a separate byte-level property

No implicit Unicode normalization is performed by the string model. Canonically equivalent but differently encoded code-point sequences remain different values unless another separately approved operation explicitly normalizes them. This preserves R18 structural string equality.

### 3.2 UTF-8 encoding

At explicit string/byte boundaries, the portable encoding is UTF-8.

For a valid Genia string:

- UTF-8 byte length is the number of bytes in its UTF-8 encoding
- byte offset `0` and byte offset equal to byte length are valid boundaries
- an interior offset is a boundary iff it points to the first byte of a UTF-8 encoded scalar value
- offsets below zero or above byte length are not boundaries

A boundary query is observational only; it does not slice or decode data.

### 3.3 Code-point iteration and slicing

Iteration produces each Unicode scalar value in sequence order.

Slicing operates on code-point indices. The E19-1 implementation/spec slice MUST pin exact bound behavior before merge, including omitted bounds, negative indices, and out-of-range clamping/rejection. The preferred compatibility direction is to preserve the currently observed Python-reference behavior where it can be stated simply and host-independently, but this draft does not make Python slicing itself the contract.

**Approval blocker U1:** exact negative/out-of-range slice semantics must be filled in before this contract becomes authoritative.

### 3.4 Invalid UTF-8

Malformed UTF-8 can arise only at an explicit bytes-to-string or host input boundary; an already-constructed Genia string cannot contain an invalid Unicode scalar encoding.

R19 requires deterministic failure with no host decoder exception text leakage.

**Approval blocker U2:** identify the currently implemented public byte-to-string/host boundaries covered by R19 and pin their exact failure result/message. R19 must not invent a new public decode API merely to test invalid UTF-8.

### 3.5 String display/debug

Display of an ordinary string is its raw character sequence with no surrounding quotes.

Debug rendering surrounds the string with ASCII double quotes and uses deterministic Genia escaping.

The existing required escapes are:

- backslash -> `\\`
- double quote -> `\"`
- newline -> `\n`
- carriage return -> `\r`
- tab -> `\t`

All other printable Unicode scalar values are emitted literally unless E19-1 evidence establishes an additional required portable control-character escape.

**Approval blocker U3:** decide how remaining C0/C1/non-printing control scalars render in debug text rather than inheriting host terminal/repr behavior.

## 4. Float rendering contract

R18 owns numeric equality. R19 defines only text rendering.

### 4.1 Canonical finite rendering

**Proposed rule:** ordinary finite binary64 values render as one deterministic, locale-independent decimal representation that round-trips to the identical binary64 value and is canonical among equivalent decimal spellings.

A host may use any implementation algorithm/library that produces the exact contracted string. The contract MUST NOT require Python, C++ iostreams, `printf`, Ryu, Dragonbox, or another named implementation dependency.

### 4.2 Required visible distinctions

The canonical representation MUST preserve these current/intentional distinctions unless approval changes them explicitly:

- an integral-looking float remains visibly a float (`1.0`, not `1`)
- negative zero remains visibly negative (`-0.0`)
- exponent marker is lowercase `e`
- exponent includes an explicit sign when exponent notation is used
- rendering is locale-independent; decimal separator is `.` and no locale grouping is implicit

### 4.3 Non-finite values

If Genia continues to permit non-finite binary64 values, their display/debug spellings are portable and closed.

Proposed spellings:

- positive infinity: `inf`
- negative infinity: `-inf`
- NaN: `nan`

NaN payload/sign details are not exposed through ordinary rendering. This does not change R18's `NaN == NaN` behavior.

### 4.4 Display vs debug

**Proposed rule:** float display and debug rendering are identical. Containers and Outcome/debug structures therefore reuse the same canonical float atom text.

### 4.5 Exponent/canonicalization blocker

The contract must pin exact exponent selection and spelling before approval, including:

- when fixed form changes to exponent form
- exponent leading-zero policy
- trailing zero rules
- shortest representation tie/canonicalization rules

**Approval blocker F1:** E19-0 must not claim "shortest round trip" is sufficient for byte-exact conformance until these details are pinned. The E19-2 slice should construct a corpus from current/reference behavior and select a host-neutral rule before implementation.

### 4.6 Existing explicit format specs

R19's first float contract governs ordinary display/debug rendering. Existing explicit format-spec semantics (precision, zero-padding, grouping) remain as currently implemented unless their output depends on the canonical atom text.

E19-2 MUST audit those dependent paths and add evidence where ordinary canonical rendering changes their portability. R19 does not redesign the format mini-language.

## 5. Diagnostic portability contract

### 5.1 Diagnostic classes

Every observed failure belongs to one of these portability classes:

**A. Exact portable diagnostic text** — wording is part of the language contract and shared evidence compares exact normalized text.

**B. Portable diagnostic identity with normalized rendering** — phase/category/reason/parameters are semantic; a deterministic normalized text rendering may be used at CLI/shared boundaries.

**C. Host-local/incidental diagnostic detail** — host exception/library/OS wording is not Genia semantics and must not leak into an A/B boundary.

R19 does not require these letters to become public runtime values or runner fields.

### 5.2 Existing exact error specs

Current shared `spec/error` cases compare exact `stderr`. Until an approved E19 diagnostic slice changes a case deliberately, those existing exact expectations remain regression evidence.

R19 MUST NOT silently reword all errors as a cleanup exercise.

Before diagnostic implementation, E19-3 MUST generate the complete inventory mapping each exact assertion to:

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
- R18 equality, map-key equivalence, NaN key rules, identity/opaque/protected equality semantics
- R9 JSON-specific numeric/representation rules
- R10 protected-value sinks/declassification/non-leakage
- R16 adapter protocol outcome taxonomy

In particular:

- no Unicode normalization changes `==`
- no float rendering rule changes numeric equality
- no diagnostic improvement exposes protected payloads
- no runner crash/protocol outcome is reclassified as a Genia program diagnostic

## 7. Shared conformance evidence

After approval, R19 must add enough shared evidence that a non-Python host can implement the contract without reading Python source.

Minimum Unicode families:

- 1/2/3/4-byte UTF-8 representatives
- code-point iteration/slicing
- combining-sequence behavior
- UTF-8 byte length/boundaries
- exact debug escaping
- explicit malformed UTF-8 behavior for existing covered boundaries

Minimum float families:

- zero and negative zero
- integral-looking finite float
- ordinary fraction
- precision-sensitive round-trip values
- fixed/exponent boundary values
- large/small finite values
- non-finite values if supported
- nested display/debug rendering

Minimum diagnostic families:

- exact runtime misuse
- parse failure normalization
- CLI misuse
- dynamic-value interpolation
- protected redaction
- normalized host exception boundary representative

## 8. Expected implementation slices

Subject to issue creation/approval:

- E19-1 Unicode semantics/evidence
- E19-2 float canonical rendering/evidence
- E19-3 complete diagnostic assertion/source inventory
- E19-4 diagnostic portability normalization/evidence
- E19-5 cross-surface host-default leak audit
- E19-6 truth/docs/release sync
- E19-7 skeptical release audit/distillation

No slice may use a later slice as implicit authority.

## 9. Explicit non-goals

- grapheme clusters
- normalization/collation API
- locale-aware output
- new float type
- approximate equality
- total numeric ordering
- error-category redesign
- public diagnostic-code API
- localization
- Open Functions
- C++ host implementation

## 10. Contract approval checklist

This draft is not ready to become authoritative until:

- [ ] U1 exact code-point slice bounds/negative-index behavior is pinned
- [ ] U2 covered invalid-UTF-8 entry boundaries and failure semantics are identified
- [ ] U3 remaining control-character debug escaping is decided
- [ ] F1 canonical finite-float/exponent algorithm is byte-exactly specified
- [ ] diagnostic E19-3 mechanical inventory procedure is accepted
- [ ] R17/R18/R9/R10/R16 compatibility review passes
- [ ] proposed shared case families are sufficient for an independent host

## Critical acceptance criterion for completed R19

A non-Python host can reproduce contracted Unicode/string behavior, canonical float display/debug text, and portable diagnostic output from the approved written contract and shared evidence alone, byte-for-byte where the contract says text is exact, without using Python `str`, `repr`, exception strings, or Python implementation source as an undocumented specification.
