# Issue #838 — Exact Numeric Model Contract Review

Verdict: **PASS**

Status: contract-review evidence only. No runtime behavior is implemented by this review; `GENIA_STATE.md` remains final authority.

Reviewed contract: `docs/design/exact-numeric-model-contract.md` at the issue #838 branch.

## Skeptical review

- **Independent-host implementability:** PASS. Integer/Decimal/Rational/Float64 values, source classification, arithmetic, division/remainder, comparisons, conversion, Core IR, rendering, JSON, formatting, and resource-failure boundaries are stated without Python implementation dependence.
- **Host-library leakage:** PASS. The contract explicitly rejects Python `float`, Decimal-context defaults, C++ casts, host JSON parser behavior, formatter defaults, locale, and library exception text as semantic authority.
- **Conversion determinism:** PASS. exact→Float64 uses IEEE-754 round-to-nearest/ties-to-even with overflow failure; finite Float64→exact reconstructs the exact represented dyadic value as Decimal.
- **Equality/key coherence:** PASS. R18's single equality/key relation remains authoritative; exact-family equality is mathematical, the finite Float64 bridge uses the exact represented value, booleans remain distinct, and NaN remains non-reflexive/illegal as a map key.
- **JSON reproducibility:** PASS. The Decimal acceptance predicate is defined in terms of deterministic binary64 rounding plus a deterministic canonical shortest-round-trip decimal and exact Decimal reparse; encoding never rounds an exact value merely to make it fit JSON.
- **Rendering:** PASS. Decimal/Rational rendering follows the previously resolved host-neutral rules; Float64 is explicitly constructor-shaped so display does not masquerade as an exact Decimal source literal.
- **Resource limits:** PASS. The mathematical domain is not narrowed to a host threshold; resource exhaustion is explicitly distinct from numeric overflow and normalized without implementation text.
- **Approximation boundary:** PASS. Float64 is explicit, mixed arithmetic is rejected, and transcendental approximation cannot silently fall back to hardware float.
- **Core IR:** PASS. The frozen node family remains unchanged; numeric literal portability is carried by tagged `IrLiteral.value` payloads.

## Deferred-but-not-blocking items

- direct Float64 raw-bit/NaN/infinity source construction is intentionally out of scope
- actual transcendental APIs are intentionally out of scope
- fixed host resource thresholds are intentionally not portable semantics

These are explicit non-goals rather than unresolved contract ambiguity.

## Gate result

The contract is **implementation-ready and approved** for the issue #838 phase sequence. Implementation remains NO-GO until the separately committed syntax/Core-IR design and failing TEST phase are present.
