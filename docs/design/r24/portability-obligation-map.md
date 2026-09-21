# R17–R23 portability obligation map for the C++ host

Status: **Planning contract — non-authoritative.** See
`docs/design/r24-cpp-host-preflight.md` section 6 (item 6 of the R24
pre-flight task). Maps each portability release to what `genia-cpp` must
implement, on what authority, and when.

| Release | Obligation | Authoritative source | Applicable shared evidence | Bootstrap, later slice, or completion gate |
|---|---|---|---|---|
| R17 | Exact arbitrary-precision Integer arithmetic; deterministic insertion-ordered maps | `docs/design/r17-numeric-ordered-map-portability-contract.md`; `GENIA_STATE.md` §4 (R17) | `spec/eval/arithmetic-basic.yaml`, `integer-arithmetic-large-magnitude-no-overflow.yaml`, `spec/eval/map-*.yaml` | Bootstrap (integer arithmetic + one ordered-map case are in `docs/design/r24/bootstrap-cases.json`); full map-behavior surface is a later slice |
| R18 | Structural/identity/opaque-token value equality; map-key identity and "legal key" rules | `docs/releases/R18.md`; `GENIA_STATE.md` §4 (R18) | `spec/eval/r18-equality-*.yaml`, `r18-map-*.yaml` | Bootstrap (two representative cases in `bootstrap-cases.json`); the full `r18-*` family (13 cases per the spec inventory) is a later slice before completion |
| R19 | Unicode decode/code-point handling; portable diagnostic normalization (no STL/OS/compiler text leakage) | `docs/releases/R19.md`; `GENIA_STATE.md` §4 (R19) | `spec/error/*.yaml` (160 files); no dedicated Unicode-literal suite exists yet, so Unicode string handling is exercised indirectly through string-literal/error cases in the bootstrap suite | Bootstrap includes one error/diagnostic case; the diagnostic-normalization *boundary itself* (native-primitive-inventory.md's diagnostic row) is a completion-gate requirement, not deferrable, since it protects every other category from leaking implementation text |
| R20 | Local grouped/repeated open-function clauses; cross-module open-function contribution/selection | `docs/design/r20-open-functions-contract.md`; `GENIA_STATE.md` §4.7 | `spec/eval/r20-*.yaml` (9), `spec/ir/r20-*.yaml` (5), `spec/error/error-r20-*.yaml` (6) | Bootstrap includes two representative cases (`open_functions_r20` category); this is an **R24 entry prerequisite AND a completion-gate requirement** — capability-floor.json marks `open_functions` mandatory for R24 completion even though the generic manifest treats it as optional |
| R21 | Numeric source classification; tagged portable `IrLiteral` numeric payloads (no runtime arithmetic at this layer) | `docs/releases/R21.md`; `docs/analysis/r21-release-truth-audit.md` | `spec/parse/parse-r21-*.yaml` | Bootstrap literal cases exercise the parser/IR path; full classification coverage is a later slice |
| R22 | Exact Decimal/Rational runtime values, Float64 explicit boxing, exact-family arithmetic/division/comparison, numeric misuse/resource-limit diagnostics | `docs/releases/R22.md`; `docs/analysis/r22-release-truth-audit.md` | `spec/eval/r22-*.yaml` (6 files: promotion lattice, division proofs, ordering, equality, floor-remainder, mixed-domain rejection) | Later slice — not in the initial 19-case bootstrap (arithmetic-basic covers plain Integer only); required before R24 completion since exact numerics are a stated non-goal-exception (R24 must implement, not merely stub, exact numeric runtime) |
| R23 | Canonical numeric rendering/formatting; strict JSON boundary for exact/Float64 numerics | `docs/releases/R23.md`; `docs/analysis/r23-release-truth-audit.md`; `docs/design/r23-numeric-representation-interchange-contract.md` | `spec/eval/r23-format-*.yaml` (4), `spec/error/error-r23-format-*.yaml` (1), `spec/eval/r23-json-*.yaml` (6) — added by issue #954 to close the gap this row previously flagged, each derived exclusively from the contract sections and `tests/unit/test_r23_*.py` cases cited in its own `notes:` field, verified directly against the reference host before being added | Completion gate — the open-evidence-gap flag is **resolved by issue #954**: E23-2 format-spec numeric integration for Decimal/Rational, E23-4 Rational/Float64 JSON boundary policy, and Decimal/Rational JSON encode-side behavior (mirroring the existing decode-side case) now have dedicated shared evidence; R24/E24-7 may build against it directly instead of R22 evidence alone |

## Ambiguity-stop note

No behavior in this map was derived from Python implementation internals;
every "authoritative source" column cites a genia-2026 contract, release
doc, or audit trail. If a future E24 slice finds a case whose expected
behavior is not traceable to one of these documents or to `spec/*.yaml`,
that slice must invoke the ambiguity-stop rule (pre-flight section 9)
rather than infer behavior from `src/genia/` (Python) source.
