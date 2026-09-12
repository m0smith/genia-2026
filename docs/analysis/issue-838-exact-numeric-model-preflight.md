# Issue #838 — Exact Numeric Model Gate Pre-flight

Status: **Pre-flight complete.** Analysis only; no language behavior is changed by this document. `GENIA_STATE.md` remains final authority for implemented behavior.

Starting revision: `bf169a481bdf86d038d0908bdcea429197758e46`.

## Purpose

Close the separately gated Exact Numeric Model prerequisite before R21 C++ semantic implementation begins. The gate exists to prevent the Python reference host's current binary-float choices from becoming de facto multi-host Genia semantics.

## Mechanical current-state inventory

At the starting revision:

- `src/genia/lexer.py` recognizes `NUMBER` as `\d+(?:\.\d+)?`; exponent forms are not numeric tokens and leading/trailing-dot forms are not numeric literals.
- `src/genia/parser.py` constructs `Number(float(tok.text))` for dotted number tokens in expression, pattern, and `none`-reason pattern positions; undotted tokens use Python `int`.
- `src/genia/ast_nodes.py` models `Number.value` as `int | float`.
- portable `IrLiteral.value` is currently `Any`; current numeric lowering/normalization therefore carries host-native integer/float values rather than a tagged host-neutral numeric payload.
- ordinary `/` already lowers as `IrBinary(op=SLASH)` and the portable node family already contains the required `IrLiteral`, `IrUnary`, `IrBinary`, and `IrCall` families; no new Core IR node family is needed.
- R17 already requires arbitrary-precision Integer semantics and deterministic ordered-map behavior.
- R18 already requires one non-user-overloadable equality/key relation, booleans distinct from numbers, exact integer/current-float bridging, signed-zero equality, and NaN non-reflexivity/key exclusion. The exact-numeric model must supersede only the current binary-float assumptions, not the equality architecture.
- R9 retains a deliberately narrower generic JSON interoperability boundary: safe integers only for Integer JSON numbers and finite binary64-oriented fractional behavior. The exact-numeric model must preserve the interoperability intent while replacing host-float parsing/rounding authority.
- R19 owns Unicode and diagnostic portability only and explicitly defers Decimal/Rational/Float64 semantics and rendering.
- `docs/design/exact-numeric-model-preflight.md` and `docs/design/exact-numeric-model-resolved-decisions.md` already settle the exact-family lattice, exact division direction, canonical Decimal/Rational normalization and rendering direction, tagged numeric Core IR direction, explicit exact↔Float64 crossing, and explicit immutable precision-context direction. They remain planning documents until the dedicated contract is approved.

## Current accidental Python assumptions to remove or quarantine

1. Dotted source numbers become Python `float` during parsing.
2. Current equality contains Python `int`/`float` bridge logic rather than a general exact-family/Float64 mathematical relation.
3. JSON decode currently has a strict host-float conversion path for fractional tokens.
4. Current float rendering/formatting tests exercise Python float values directly.
5. Numeric portable IR snapshots can inherit host-native JSON serialization choices.

These are implementation facts to inventory, not semantic authority.

## Remaining contract decisions and pre-flight recommendations

The following choices are recommended for the contract phase because they minimize syntax and host dependence while preserving the already-resolved direction:

- **Source classification:** undotted, non-exponent numeric tokens are Integer; `digits '.' digits`, `digits exponent`, and `digits '.' digits exponent` are Decimal. Exponent marker is `e` or `E` with optional `+`/`-` and at least one exponent digit. Leading-dot and trailing-dot forms remain invalid numeric literals.
- **Float64 surface:** no Float64 literal suffix in the first gate. `float64(value)` is an ordinary explicit conversion call. This avoids direct NaN payload/sign literal semantics in the first release.
- **Rational surface:** exact `/` is the ordinary source of Rational values; `rational(n, d)` is an ordinary explicit constructor call. No Rational literal syntax.
- **Exact conversion:** `exact(value)` is an ordinary explicit conversion call for Float64 → exact Decimal; exact inputs may return their existing exact value unchanged.
- **Generic JSON Decimal predicate:** accept an exact Decimal only when it is stable through the retained binary64 interoperability boundary: round the exact value to finite IEEE-754 binary64 using round-to-nearest/ties-to-even, render that binary64 with the unique shortest decimal that round-trips to the same binary64, parse that decimal text exactly, and require mathematical equality with the original Decimal. This accepts common values such as Decimal `0.1` while rejecting Decimal spellings whose additional significant information would be lost by a binary64-oriented consumer. Integer safe-range rules remain unchanged and independent.
- **Formatting:** canonical display/debug is part of the numeric contract. Existing format-spec rounding remains presentation only; it must never mutate or reclassify the numeric value. Detailed new formatting syntax is out of scope unless required to preserve existing format behavior.
- **Resource exhaustion:** arbitrary precision defines valid values, not infinite resources. Hosts may impose resource limits; resource exhaustion is a host/resource failure normalized without library/OS detail and is not numeric-domain overflow. Shared conformance must avoid machine-capacity thresholds.
- **NaN payload/sign:** direct NaN literal/raw-bit construction is deferred. Float64 NaN remains semantically non-reflexive when obtained through an approved host boundary, but payload/sign are not Genia identity in this gate.
- **Transcendentals:** precision-context semantics are ratified, but actual transcendental APIs/functions remain out of this gate unless an existing public surface requires migration.

## PORTABILITY ANALYSIS

1. **Semantic owner:** `genia-2026` owns the numeric language/runtime/Core-IR contract. External hosts, including `genia-cpp`, consume that contract and must not define numeric behavior.
2. **Core IR impact:** existing portable node families remain frozen. Numeric `IrLiteral.value` changes from host-native numeric payloads to tagged semantic payloads; `/` remains `IrBinary(SLASH)` and constructors/conversions remain ordinary `IrCall`.
3. **Host boundary:** every host must parse numeric source lexically, materialize the same Integer/Decimal/Rational/Float64 mathematical values, normalize the same tagged Core IR, and expose the same conversions/equality/JSON/rendering behavior without consulting Python implementation details.
4. **Determinism:** Decimal coefficient/exponent normalization, Rational reduction, exact promotion/division, exact↔Float64 conversion, equality/key equivalence, canonical rendering, and JSON acceptance must be mathematically specified and host-independent.
5. **Unsupported behavior:** core Integer/Decimal/Rational/Float64 semantics required by the exact-numeric gate are not optional capabilities. Later transcendental/host-specialized approximate math may be capability-gated separately; unsupported behavior must never masquerade as a pass.
6. **Failure normalization:** division by zero, invalid conversion, mixed exact/Float64 arithmetic, JSON-domain rejection, malformed construction, and resource failures require stable Genia diagnostic identity/text where contracted. Raw Python/C++/decimal-library/OS wording must not cross portable boundaries.
7. **Non-portable assumptions excluded:** Python `float`, Python `Decimal` context defaults, Python `Fraction` representation, C++ `double` casts, Boost/GMP/MPFR defaults, host JSON parsers, host numeric formatter text, locale, machine word width, and implementation-specific resource thresholds do not define Genia semantics.

## Gate recommendation

**GO for the dedicated contract phase.**

**NO-GO for parser/runtime/Core-IR/shared-spec implementation until the contract is explicitly approved and a separate syntax/Core-IR design plus committed failing TEST phase exist.**
