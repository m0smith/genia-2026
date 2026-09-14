# Issue #853 Preflight — E21-1 Numeric Source Classification

Status: process artifact for issue #853 (E21-1). Not a source-of-truth document;
`GENIA_STATE.md` remains final authority. This file records the preflight
review required by `docs/process/run-change.md` before the contract phase.

## Scope

Implement only the source-classification portion of
`docs/design/r21-numeric-source-portable-representation-contract.md` (§2, §3):

- classify `DIGIT+` as Integer source
- classify dotted, exponent-only, and dotted-exponent forms as Decimal source
- reject leading-dot (`.5`) and trailing-dot (`5.`) forms
- reject malformed exponents deterministically
- preserve existing unary sign lowering (sign is not part of the numeric token)
- add lexical/base-10 classification+normalization machinery with zero host
  binary-float construction, ready for E21-2 to consume when building the
  tagged `IrLiteral` payload
- add failing shared `spec/parse/*` cases and focused lexer/parser unit tests
  before implementation

Out of scope (explicitly deferred): `IrLiteral` tagged payload wiring (E21-2),
evaluator/runtime Decimal values or arithmetic (R22), equality/map-key changes
(R22), rendering/formatting/JSON (R23), C++ host work (R24).

## PORTABILITY ANALYSIS (required, all seven fields)

1. **What portable boundary does this change touch?**
   The lexer/parser surface syntax layer and the AST layer that sits above
   Core IR. It does not yet touch the Core IR node family or `IrLiteral`
   payload shape — that boundary is intentionally deferred to E21-2. This
   ticket only prepares classification data that the AST layer carries.

2. **Does this change alter the minimal portable Core IR node family?**
   No. `docs/architecture/core-ir-portability.md`'s frozen node list is
   unchanged. Lowering (`lowering.py`) is not modified in this ticket; the
   existing `IrLiteral(node.value, ...)` call path continues to run
   unchanged, so numeric literals lower exactly as they do today.

3. **Does this change require a host-native binary float at any point in the
   new classification/normalization code path?**
   No. The new `classify_numeric_literal` function operates purely on the
   lexical text via string slicing, `str.lstrip`/`str.rstrip`, and integer
   arithmetic on exponent offsets. It never calls `float(...)`. The existing,
   separate `Number.value` field (used only by the current evaluator/AST
   compatibility path, unrelated to the new classification machinery)
   continues to call `float(text)` for decimal literals exactly as it does
   on current `main` — this is pre-existing R21-unrelated runtime behavior
   that this ticket does not change and R22 owns migrating away from.

4. **Does this change require another host implementation (Node/Java/Rust/
   Go/C++) to consult Python-specific behavior to reproduce it?**
   No. The classification grammar (§2 of the R21 contract) and the
   canonicalization rule (§4.2, prepared here for E21-2's later use) are
   both specified in host-independent lexical/arithmetic terms reproducible
   from the contract text alone.

5. **Does this change affect R16 multi-host conformance infrastructure, R17
   arbitrary-precision Integer, R18 equality/map-key, R19 diagnostics, or R20
   open functions?**
   No behavioral change to any of those. New `spec/parse/*` cases are pure
   additions exercised through the existing shared spec/conformance paths;
   they do not modify R17/R18/R19/R20 machinery.

6. **Is any part of this change host-local-only (Python reference host
   convenience) rather than portable?**
   The specific mechanism of raising `SyntaxError` with Python exception
   text is host-local (as it already is for all other parse errors in this
   codebase); the *fact* that malformed exponents/leading-or-trailing-dot
   forms are rejected, and the classification result itself, are portable
   and specified by the contract.

7. **What new portable evidence must exist for another host to reproduce this
   behavior without reading Python source?**
   New `spec/parse/*` YAML cases (parse-only, no IR yet since tagged
   `IrLiteral` payloads are E21-2) covering: integer classification,
   dotted/exponent-only/dotted-exponent Decimal classification, equivalent
   Decimal spellings, malformed exponent rejection, and rejected leading/
   trailing-dot forms.

## Conclusion

Preflight is complete. Proceeding to the contract-reconciliation phase next;
the approved R21 contract already covers this ticket's scope with no
contradiction found.
