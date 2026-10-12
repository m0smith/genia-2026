# Bounded C++ numeric host status

`GENIA_STATE.md` remains final authority. This is implementation-status evidence,
not a new numeric contract: C++ support is **not full R22/R23 parity**. R22/R23
release completion records describe the Python reference host at those releases;
the later R24 floor and R26 strict JSON bridge implement the bounded subset below.
Historical `docs/state-record/` provenance is unchanged.

## Inspected revisions and applicability

- Genia checkout: `7eb99da46ea059400d68b0e1768dbb00f812579e`.
- C++ checkout: `bb7c7474001f18e2e27fd94b7be9e9b725ba3473`.
- C++ declared Genia pin: `6402e668ae85a1e7efe94b3ac3d51f233b730ca4`; protocol `1`.
- `core_ir_eval`, `prelude_autoload` and `shared_spec_runner` remain `partial`.
  `json_strict` is `supported`; `json_compat` remains unsupported by contract.
  There is no separate numeric capability claim.

The existing R16 loader/executor/comparator, with the adapter's capability
response, observed **24 pass / 5 unsupported / 0 failure-class outcomes** across
all 29 `r22-*`/`r23-*` shared cases in this Genia checkout. This is compatibility
with the inspected checkout, **not pinned conformance** for the older declared
pin. Each pass proves that case, not every numeric surface. JSON cases require
`json_strict`; the other listed numeric cases have no `requires` gate.

| Implemented subset | Concrete shared evidence (case names under `spec/`) |
| --- | --- |
| Rational construction; exact-family promotion, division and floor remainder | `r22-rational-construction`, `r22-exact-arithmetic-promotion-lattice`, `r22-exact-division-required-proofs`, `r22-exact-floor-remainder` |
| Explicit Float64 conversion, binary64 arithmetic and mixed-domain rejection | `r22-float64-exact-round-trip`, `r22-float64-arithmetic`, `r22-mixed-exact-float64-rejected` |
| Mathematical comparison and cross-kind numeric map-key identity | `r22-exact-family-equality`, `r22-exact-family-and-float64-ordering`, `r22-numeric-map-key-cross-kind` |
| Selected quoted numeric evaluation and literal patterns | `r22-cross-surface-quoted-and-pattern` (not general metacircular evaluation) |
| Canonical numeral atoms and numeric field precision | `r23-format-align-rational-canonical-atom`, `r23-format-precision-decimal-half-up`, `r23-format-precision-rational-exact-ratio`, `r23-format-precision-float64-exact-dyadic` |
| Strict numeric JSON stability, terminating Rational and finite Float64 | Six `r23-json-*` eval cases, each gated by `json_strict` |
| Normalized Float64 zero-divisor and exact-to-Float64 overflow diagnostics | `r22-float64-division-by-zero-rejected`, `r22-float64-remainder-by-zero-rejected`, `r22-float64-magnitude-overflow-rejected` |

C++ `tests/test_engine.cpp` additionally exercises conversion tie boundaries,
signed zero, NaN/infinity ordering/key rejection, canonical rendering and strict
JSON. The numeric/equality selection used during source-contract remediation
(#1187's evidence on #1101, C++ PR #49) passed 71 native cases / 293 assertions;
that host-local evidence is not a substitute for shared conformance. Implementing
headers are `arithmetic.hpp`, `equality.hpp`, `float64.hpp`, `render.hpp`,
`format.hpp` and the strict JSON codec in `json_numeric.hpp`.

## Retained gaps

- Decimal exponents are C++ `int64_t`; no arbitrary-precision exponent parity is
  claimed. Exact helpers do not implement Python's private `numeric-resource-limit`
  guard. Large exponents can require substantial work/allocation; the Python
  safeguard must not be attributed to this C++ realization.
- Shared cases `r22-exact-division-by-zero-rejected`,
  `r22-exact-remainder-by-zero-rejected`, `r22-exact-nan-rejected`,
  `r22-rational-non-integer-argument-rejected` and
  `r22-rational-zero-denominator-rejected` remain **unsupported**. Internal
  absence/rejection is not proof of the required diagnostic.
- Full prelude, first-class `Format` Values, configuration/protected values,
  Template/Sheet/retrieval numeric cross-surfaces and general metacircular
  evaluation are outside this numeric claim. Compatibility JSON (`json_compat`)
  remains Python-host-only; strict JSON does not establish those capabilities.
- The bounded claim and its gaps do not reopen R22/R23 completion or promote
  `core_ir_eval`. Future implementation requires its own contract-first gate;
  use the [C++ host gap planning surface](../strategy/roadmap/cpp-host-gap-burndown.md).

The four core docs and the governed MCP `cpp_language_floor` fact already describe
C++ as bounded rather than Python parity. Correcting obsolete numeric-only absence
wording adds no MCP fact, registry member, tool or language behavior.
