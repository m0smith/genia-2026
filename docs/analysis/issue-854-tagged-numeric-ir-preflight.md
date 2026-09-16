# Issue #854 Preflight — E21-2 Tagged Portable Numeric IrLiteral Payloads

Status: process artifact for issue #854 (E21-2). Not a source-of-truth
document; `GENIA_STATE.md` remains final authority. Records the preflight
review required by `docs/process/run-change.md` before the contract phase.

## Scope

Implement only §4 of
`docs/design/r21-numeric-source-portable-representation-contract.md`, consuming
the E21-1 (#853) classification already merged to `main`:

- lower Integer/Decimal source through the existing `IrLiteral` node
- Integer payload `{kind: "integer", digits: <canonical unsigned decimal text>}`
- Decimal payload `{kind: "decimal", coefficient: <canonical text>, exponent: <canonical text>}`
- preserve unary minus outside the literal payload
- preserve `/` as ordinary `IrBinary(op=SLASH)` (unaffected — no numeric-specific handling exists there)
- update normalized IR adapters/fixtures only as required for the tagged payload
- failing shared IR cases before implementation

Out of scope: new `IrDecimal`/`IrRational`/`IrFloat64` node, evaluator/runtime
Decimal materialization or arithmetic (R22), equality/map-key changes (R22),
rendering/formatting/JSON (R23), C++ work (R24).

## PORTABILITY ANALYSIS (required, all seven fields)

1. **What portable boundary does this change touch?**
   The Core IR boundary itself: `lowering.py`'s `Number -> IrLiteral`
   construction, and every normalized-IR consumer (`hosts/python/
   ir_normalize.py`, the R16 subprocess protocol IR path, `spec/ir/*`
   fixtures). This is the layer `docs/architecture/core-ir-portability.md`
   freezes as the shared contract.

2. **Does this change alter the minimal portable Core IR node family?**
   No. `IrLiteral` already exists in the frozen node family
   (`docs/architecture/core-ir-portability.md`); only its `value` payload
   shape changes for numeric literals, from a bare Python `int`/`float` to
   a small tagged dict of canonical strings. String/bool/nil `IrLiteral`
   payloads are unaffected. No new node class is introduced.

3. **Does this change require a host-native binary float at any point?**
   No. The tagged payload is built directly from E21-1's
   `classify_numeric_literal` output (already string/int-only,
   `float()`-free) via the `Number` AST node's `digits`/`coefficient`/
   `exponent` fields populated in #853. Lowering only re-packages those
   already-canonical strings into a dict; it performs no numeric
   conversion of its own.

4. **Does this change require another host implementation to consult
   Python-specific behavior to reproduce it?**
   No. The payload shape is fully specified in contract §4.1/§4.2 in
   host-independent terms (tag + canonical base-10 strings). An
   independent host can build the identical payload from its own lexer's
   digit/fraction/exponent parts using the same canonicalization rule.

5. **Does this change affect R16/R17/R18/R19/R20?**
   It changes what R16's shared IR evidence and subprocess-protocol IR
   normalization observe for numeric literals (the payload shape), which
   is an intentional, contract-authorized change to the portable IR
   surface, not a behavior regression in R16's machinery itself. R17
   Integer arithmetic, R18 equality/map-key, R19 diagnostics, and R20 open
   functions are otherwise unaffected — none of their own IR node
   families or evaluator behavior changes.

6. **Is any part of this change host-local-only rather than portable?**
   No — the tagged payload itself is the portable representation being
   defined. Python-specific details (how `IrLiteral.value` is stored as a
   `dict` object in the reference host's dataclass) are ordinary
   host-local representation of the portable JSON-serializable shape,
   consistent with how every other `IrLiteral` payload already works.

7. **What new portable evidence must exist for another host to reproduce
   this behavior without reading Python source?**
   New `spec/ir/*` cases showing the exact tagged `IrLiteral` payload for
   representative Integer/Decimal forms, huge Integers, equivalent Decimal
   spellings, and unary-negative lowering — verified identical through
   both the in-process path and the R16 subprocess protocol adapter.

## Evaluator compatibility note

The evaluator currently reads `IrLiteral.value` directly as the runtime
number (`int`/`float`) for numeric literals (see `evaluator.py`'s
`IrLiteral` handling). Changing `IrLiteral.value` to a tagged dict for
numeric literals would break evaluation unless the evaluator is taught to
unwrap the tag back to a runtime number. Since R21 explicitly excludes
runtime Decimal materialization (R22 owns it) but must not regress existing
Integer/Decimal *evaluation* (arithmetic, display, etc., which is currently
implemented and must keep working), this ticket's minimal compatibility
shim is: the evaluator's numeric `IrLiteral` handling unwraps the tagged
payload back into the exact same `int`/`float` it already produces today
(no new runtime type, no new semantics — pure reconstruction from the
canonical strings, e.g. `int(digits)` for Integer and
`float(f"{coefficient}e{exponent}")` for Decimal, which is mathematically
identical to the previous direct float() of the source spelling since it
reconstructs the same value modulo binary64 rounding, which the source
`float()` call already performed identically). This is compatibility
strictly required by the source/Core-IR boundary change (a change
E21-2 itself makes to the previously-untagged payload), not a new R22
runtime feature — no new Decimal/Rational/Float64 value kind, arithmetic
rule, or conversion semantic is added; the observable evaluated value for
every existing program is unchanged bit-for-bit.

## Conclusion

Preflight is complete. Proceeding to contract reconciliation; §4 already
specifies this ticket's payload shapes with no contradiction found.
