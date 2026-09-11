# R19 Unicode and Diagnostic Portability Pre-flight

Status: **Planning contract — non-authoritative.** `GENIA_STATE.md` remains final authority for implemented behavior.

R19 follows completed R18 Portable Value Equality. This pre-flight establishes the scope and implementation discipline for R19 before any runtime/spec behavior changes begin.

## 1. Scope lock

R19 includes only:

- portable Unicode/string semantics required by existing Genia surfaces
- classification and normalization of portable diagnostic text/identity where shared conformance observes it
- shared evidence sufficient for an independent host to reproduce those surfaces

R19 does **not** include:

- new string syntax or broad new string APIs
- grapheme-cluster processing
- locale-sensitive formatting/collation
- float/Decimal/Rational numeric-model redesign
- canonical Float64 rendering
- new numeric types or approximate equality
- changes to R18 equality/key semantics except as a later separately approved numeric release may supersede them
- redesign of error categories
- new host-adapter protocol outcome categories
- Open Functions / extensible pattern dispatch
- C++ host implementation

The former F1 float-rendering blocker is split out into a separate exact-numeric-model workstream. See `docs/design/exact-numeric-model-preflight.md`.

## 2. Source of truth

Authoritative implemented truth remains, in order:

1. `GENIA_STATE.md`
2. `GENIA_RULES.md`
3. `GENIA_REPL_README.md`
4. `README.md`
5. executable shared specs for covered behavior

Relevant planning/evidence inputs:

- `docs/strategy/roadmap/r16-r20.md`
- `docs/releases/R18.md`
- `docs/design/r18-portable-value-equality-contract.md`
- `docs/analysis/r19-unicode-current-behavior-inventory.md`
- `docs/analysis/r19-diagnostic-contract-inventory.md`
- `docs/analysis/r19-float-current-behavior-inventory.md` (historical/current-state evidence for the separate numeric workstream)
- `docs/design/exact-numeric-model-preflight.md`
- `docs/design/r21-cpp-host-preflight.md`

Current Python implementation is evidence, not semantic authority.

## 3. Feature maturity

Stage before implementation: **Planned contract hardening / not active**.

E19-0 may add analysis/design/process documentation only. It must not describe proposed rules as implemented Genia behavior.

## 4. Approved Unicode decisions

The following E19-0 decisions are approved for the R19 contract but are not implemented merely by this planning document.

### U1 — code-point slicing

Genia string slicing is by Unicode scalar/code-point index, not UTF-8 byte offset and not grapheme cluster.

Normalize slice bounds as follows:

- omitted start -> `0`
- omitted end -> code-point length
- negative indices count from the end
- after negative-index adjustment, bounds below `0` clamp to `0`
- bounds above length clamp to length
- if normalized start is greater than or equal to normalized end, the result is the empty string

### U2 — strict UTF-8 decode boundaries

Where an existing Genia/host boundary claims to decode UTF-8:

- valid input decodes to the exact Unicode scalar sequence
- malformed UTF-8 fails deterministically
- no implicit U+FFFD replacement is permitted
- raw host decoder exception text must not cross the portable boundary
- the boundary keeps its already-approved Outcome/diagnostic shape; R19 does not invent a new universal decode API

### U3 — deterministic debug escaping

Debug strings retain the short escapes:

- backslash -> `\\`
- double quote -> `\"`
- newline -> `\n`
- carriage return -> `\r`
- tab -> `\t`

Every other C0 control (`U+0000..U+001F`), DEL (`U+007F`), and C1 control (`U+0080..U+009F`) renders as lowercase `\uXXXX` hexadecimal. Other Unicode scalar values render literally.

## 5. Current implementation facts

Python reference-host implementation currently:

- relies on Python `str` for code-point iteration/slicing
- encodes Python strings to UTF-8 for byte-length/boundary helpers
- contains exact shared error stderr assertions while diagnostic identity metadata is mostly informational
- still uses Python binary floats and Python `str(float)` / `repr(float)` today; that fact is now input to the separate exact-numeric-model workstream rather than an R19 contract target

Not implemented by E19-0:

- any Unicode runtime change
- any diagnostic centralization
- any new shared spec
- any exact numeric model change
- any R19 `GENIA_STATE.md` behavior claim

## 6. Core invariants to preserve

R19 MUST preserve:

- R17 ordered-map semantics
- current R18 equality, legal-key, protection, and opaque/identity semantics
- R9 JSON representation boundaries
- R10 protected-value non-leakage
- R16 host-adapter outcome taxonomy separation
- existing parser/Core IR syntax/shape unless a concrete approved portability requirement proves a change is necessary

Specific guardrails:

- Unicode normalization must not silently change equality semantics
- diagnostic interpolation must not leak protected payloads
- host/library exception wording must not become portable by accident
- R19 must not pre-empt the separate exact Decimal/Rational/Float64 contract

## 7. Inventory gate

E19-0 produced three inventories:

- Unicode current behavior
- float rendering current behavior
- diagnostics current contract/assertion behavior

After the numeric split, the float inventory is retained as current-state evidence but is no longer an R19 implementation gate. Unicode and diagnostic inventories remain the R19 gate inputs.

## 8. Test strategy after approval

Unicode evidence should cover:

- 1/2/3/4-byte UTF-8 code points
- approved negative/out-of-range code-point slicing
- combining sequences vs grapheme assumptions
- byte-boundary detection
- approved debug escaping
- strict malformed UTF-8 behavior at existing decode boundaries

Diagnostic evidence should cover:

- representative exact portable messages
- parse/runtime/CLI boundary distinctions
- dynamic value interpolation through Genia rendering
- host exception normalization
- protected-value redaction

## 9. Expected work slices

Proposed sequencing after E19-0 approval:

- **E19-1 — Unicode portable semantics implementation + shared evidence**
- **E19-2 — complete diagnostic assertion/source inventory and classification**
- **E19-3 — diagnostic portability normalization + representative shared evidence**
- **E19-4 — cross-surface host-default leak audit**
- **E19-5 — source-of-truth and release documentation sync**
- **E19-6 — skeptical release truth audit/distillation**

Exact issue numbering is not semantic truth and may be adjusted when tickets are created.

## 10. Cross-file impact after approval

Likely later implementation/doc surfaces:

- `src/genia/utf8.py`
- selected evaluator/builtin/parser/CLI diagnostic constructors
- `spec/eval/*`, `spec/error/*`, `spec/parse/*`, `spec/cli/*` as justified
- `GENIA_STATE.md`
- `GENIA_RULES.md` if invariant wording changes
- `GENIA_REPL_README.md` / `README.md` only where public behavior is documented
- host portability docs/capability evidence where necessary

The separate numeric release will own `src/genia/_format_engine.py` changes that depend on Decimal/Rational/Float64 semantics.

## 11. Branching and change discipline

Work must occur on a dedicated branch, never directly on `main`.

Each implementation slice must:

1. read current authoritative docs first
2. state exact portable behavior targeted
3. add failing shared/unit evidence before implementation where practical
4. make the smallest runtime change
5. run related and broad regression suites
6. update docs only to implemented truth
7. complete a skeptical audit before release closure

## Final go/no-go

**GO for E19-0 planning artifacts with U1/U2/U3 approved.**

**NO-GO for R19 runtime/spec behavior changes until the narrowed Unicode + diagnostic contract is explicitly approved.**

**NO-GO for Decimal/Rational/Float64 implementation under R19; that work requires its own release gate.**
