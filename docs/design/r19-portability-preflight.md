# R19 Unicode, Float, and Diagnostic Portability Pre-flight

Status: **Planning contract — non-authoritative.** `GENIA_STATE.md` remains final authority for implemented behavior.

R19 follows completed R18 Portable Value Equality. This pre-flight establishes the scope and implementation discipline for R19 before any runtime/spec behavior changes begin.

## 1. Scope lock

R19 includes only:

- portable Unicode/string semantics required by existing Genia surfaces
- canonical float display/debug rendering
- classification and normalization of portable diagnostic text/identity where shared conformance observes it
- shared evidence sufficient for an independent host to reproduce those surfaces

R19 does **not** include:

- new string syntax or broad new string APIs
- grapheme-cluster processing
- locale-sensitive formatting/collation
- new numeric types or approximate equality
- changes to R18 equality/key semantics
- redesign of error categories
- new host-adapter protocol outcome categories
- Open Functions / extensible pattern dispatch (R20)
- C++ host implementation (R21)

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
- `docs/analysis/r19-float-current-behavior-inventory.md`
- `docs/analysis/r19-diagnostic-contract-inventory.md`
- `docs/design/r21-cpp-host-preflight.md`

Current Python implementation is evidence, not semantic authority.

## 3. Feature maturity

Stage before implementation: **Planned contract hardening / not active**.

E19-0 may add analysis/design/process documentation only. It must not describe proposed rules as implemented Genia behavior.

## 4. Contract vs implementation

Portable contract to define:

- string/code-point model and UTF-8 boundary semantics
- canonical debug escaping
- canonical float rendering
- exact vs structured diagnostic portability boundaries

Python reference-host implementation currently:

- relies on Python `str` for code-point iteration/slicing
- encodes Python strings to UTF-8 for byte-length/boundary helpers
- uses Python `str(float)` / `repr(float)` for general float display/debug
- contains exact shared error stderr assertions while diagnostic identity metadata is mostly informational

Not implemented by E19-0:

- any new canonical formatter
- any Unicode runtime change
- any diagnostic centralization
- any new shared spec
- any R19 `GENIA_STATE.md` behavior claim

## 5. Core invariants to preserve

R19 MUST preserve:

- R17 ordered-map semantics
- R18 equality, legal-key, protection, and opaque/identity semantics
- R9 JSON representation boundaries unless separately affected and explicitly reconciled
- R10 protected-value non-leakage
- R16 host-adapter outcome taxonomy separation
- existing parser/Core IR syntax/shape unless a concrete approved portability requirement proves a change is necessary (none is expected)

Specific guardrails:

- Unicode normalization must not silently change equality semantics
- float rendering must not change numeric equality
- diagnostic interpolation must not leak protected payloads
- host/library exception wording must not become portable by accident

## 6. Inventory gate

E19-0 requires three inventories before contract approval:

- Unicode current behavior: complete enough to identify Python `str` dependencies and unresolved portable semantics
- float rendering current behavior: complete enough to identify `str`/`repr`/format-engine dependencies
- diagnostics: classification model plus a plan for a complete machine-generated exact-text inventory before message refactoring

The three inventory documents in `docs/analysis/` satisfy this planning gate. The diagnostic inventory intentionally defers generating every exact stderr row until the diagnostic implementation slice, because E19-0 must not mutate specs/runtime merely to enumerate them.

## 7. Test strategy after approval

R19 implementation must follow narrow failing-evidence slices.

Unicode evidence should cover:

- 1/2/3/4-byte UTF-8 code points
- code-point iteration/slicing
- combining sequences vs grapheme assumptions
- byte-boundary detection
- debug escaping
- explicit invalid UTF-8 decode behavior where an existing boundary exposes it

Float evidence should cover:

- ordinary finite values
- integral-looking floats
- precision-sensitive decimals
- exponent spelling/thresholds
- signed zero
- non-finite values if supported
- nested display/debug contexts

Diagnostic evidence should cover:

- representative exact portable messages
- parse/runtime/CLI boundary distinctions
- dynamic value interpolation through Genia rendering
- host exception normalization
- protected-value redaction

## 8. Expected work slices

Proposed sequencing after E19-0 approval:

- **E19-1 — Unicode portable contract implementation + shared evidence**
- **E19-2 — canonical float rendering implementation + shared evidence**
- **E19-3 — complete diagnostic assertion/source inventory and classification**
- **E19-4 — diagnostic portability normalization + representative shared evidence**
- **E19-5 — cross-surface hardening / host-default leak audit**
- **E19-6 — source-of-truth and release documentation sync**
- **E19-7 — skeptical release truth audit/distillation**

Exact issue numbering is not semantic truth and may be adjusted when tickets are created.

## 9. Complexity check

R19 should reveal and centralize existing semantics, not add a competing abstraction.

Acceptable complexity:

- small pure helpers for canonical Unicode/float rendering
- narrowly scoped diagnostic templates/identifiers where duplication/portability justify them
- shared conformance cases

Unacceptable complexity without a separate contract revision:

- full Unicode framework/ICU dependency requirement
- generalized internationalization system
- diagnostic object hierarchy
- public error-code API
- runtime-loaded message catalog

## 10. Cross-file impact after approval

Likely later implementation/doc surfaces:

- `src/genia/utf8.py`
- `src/genia/_format_engine.py`
- selected evaluator/builtin/parser/CLI diagnostic constructors
- `spec/eval/*`, `spec/error/*`, `spec/parse/*`, `spec/cli/*` as justified
- `GENIA_STATE.md`
- `GENIA_RULES.md` if invariant wording changes
- `GENIA_REPL_README.md` / `README.md` only where public behavior is documented
- host portability docs/capability evidence where necessary

E19-0 itself changes only analysis/design documentation.

## 11. Philosophy check

- preserves minimalism: **YES** — contracts existing behavior rather than adding broad APIs
- avoids hidden behavior: **YES** — removes host-default dependence
- keeps semantics out of host: **YES** — Python/C++ libraries implement, not define, the contract
- aligns with pattern/value/flow direction: **NEUTRAL/PRESERVES** — no competing paradigm introduced

## 12. Branching and change discipline

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

**GO for E19-0 planning artifacts.**

**NO-GO for R19 runtime/spec behavior changes until the R19 contract is explicitly approved.**

The governing rule is:

> R19 converts observed Python defaults into explicit Genia portability contracts; it does not give Python defaults permanent authority merely because they exist today.
