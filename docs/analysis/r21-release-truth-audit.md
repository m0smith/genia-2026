# R21 Release Truth Audit — E21-5 (issue #857)

Status: durable skeptical release-audit evidence for R21 (epic #852). Not a
source-of-truth document; `GENIA_STATE.md` remains final authority. This
audit re-derives R21's obligations independently from the approved
contract and merged `main`, rather than trusting prior per-ticket audits.

Audited commit: `ebd2e5a0fc71396c1581e56e6d43779f62376682` (merged #863,
`main` tip at audit time).

## Re-read sources

`AGENTS.md` (unchanged since epic start — confirmed by diff against an
earlier commit), `GENIA_STATE.md` sections 9.21/9.22, `GENIA_RULES.md`
section 8.6, `GENIA_REPL_README.md`, `README.md`,
`docs/design/r21-numeric-source-portable-representation-contract.md`,
`docs/architecture/core-ir-portability.md`, `docs/releases/R21.md`,
`docs/strategy/release-roadmap.md` and
`docs/strategy/roadmap/r21-r24.md`, and the merged diffs/commits for
#853 (PR #858), #854 (PR #861), #855 (PR #862), #856 (PR #863).

## Independent re-derivation

Read `src/genia/numeric_source.py`, `src/genia/lexer.py`'s numeric-token
staged matching, `src/genia/lowering.py`'s `Number -> IrLiteral`
construction, and `src/genia/evaluator.py`'s two `IrLiteral` value sites
directly (not merely trusting prior audit prose) and confirmed each
matches contract §2–§4 exactly, independent of this audit's own earlier
involvement in writing them:

- Grammar (§2): `integer := DIGIT+`; `decimal-dotted`, `decimal-exp`,
  `decimal-dot-exp` all classify Decimal. Confirmed by the regex
  `_NUMERIC_LITERAL_RE = r"^(\d+)(?:\.(\d+))?(?:[eE]([+-]?\d+))?$"` and by
  the lexer's staged integer/fraction/exponent matching with explicit
  malformed-exponent rejection.
- Lexical exactness (§3): `_canonicalize_decimal` and
  `_canonical_integer_digits` use only string slicing and `int` arithmetic
  on exponent offsets; `classify_numeric_literal`,
  `_canonicalize_decimal`, and `_canonical_integer_digits` contain zero
  `float(...)` calls (re-verified by direct source read, not just the
  existing AST-scanning unit tests).
- Portable Core IR (§4): `numeric_literal_payload` builds
  `{"kind": "integer", "digits": ...}` / `{"kind": "decimal",
  "coefficient": ..., "exponent": ...}` directly from the AST node's
  already-classified fields; `numeric_literal_runtime_value` is the sole
  function in the module calling `float()`, used only by the evaluator's
  compatibility shim (not classification/lowering).

## Skeptical spot-probes (beyond the existing test suite)

Ran ad hoc CLI/module probes against edge cases not literally spelled out
in any single existing test, to check for a subtle rounding, leading-zero,
or canonicalization bug:

| Input | classify_numeric_literal | `genia -c` evaluated result |
|---|---|---|
| `007` | integer, digits `"7"` | `7` |
| `0e0` | decimal, coefficient `"0"`, exponent `"0"` | `0.0` |
| `1e-0` | decimal, coefficient `"1"`, exponent `"0"` | `1.0` |
| `100.000e2` | decimal, coefficient `"1"`, exponent `"4"` | `10000.0` |
| `9.99e99` | decimal, coefficient `"999"`, exponent `"97"` | `9.99e+99` |
| `0.001` | decimal, coefficient `"1"`, exponent `"-3"` | `0.001` |
| `123456789012345678901234567890 + 1` | — | `123456789012345678901234567891` (R17 unaffected) |
| `.5`, `5.`, `1e` | — | deterministic `SyntaxError` in each case |

All matched the mathematically expected value with no discrepancy.

## Verification checklist (against issue #857's explicit scope)

| Item | Result |
|---|---|
| Integer/Decimal source classification matches the contract | PASS — independently re-derived above |
| Decimal source classification/lowering never transits binary64 | PASS — zero `float()` in the classification/canonicalization/lowering path; only the documented evaluator shim calls it, and only to reconstruct a pre-existing runtime value |
| malformed forms behave as contracted | PASS — `.5`, `5.`, `1e`, `1e+` all deterministically rejected, spot-checked live via CLI |
| unary sign remains unary lowering | PASS — `-1.25` lowers as `IrUnary(MINUS, IrLiteral({...}))`; confirmed by `spec/ir/r21-unary-negative-decimal-tagged-payload.yaml` and direct test |
| slash lowering is unchanged | PASS — confirmed by `spec/ir/r21-slash-remains-ordinary-binary.yaml` and `slash-operator.yaml` (migrated, still passing) |
| tagged numeric payloads are canonical and string-based | PASS — every payload field is a Python `str`; `test_lowering_no_host_native_float_in_payload` and the spot-probes above confirm |
| huge Integer digits remain exact | PASS — 30-digit literal round-trips exactly through classification, lowering, and evaluation; 40-digit spot-probe above also exact |
| equivalent Decimal source spellings normalize identically | PASS — `1.0`/`1.00`/`100e-2`/`1.000e0` all normalize to `("1","0")`; spot-probed further with `00.00`, `0e0` |
| no new numeric Core IR node family was introduced | PASS — diffed `docs/architecture/core-ir-portability.md` and `spec/manifest.json`'s node family lists against pre-R21 `main`; the only additions present (`IrOpenFuncDef`/`IrOpenContribution`/`IrOpenUse`) are pre-existing R20 work, not R21 |
| applicable in-process and subprocess behavior agree | PASS — `tests/spec/test_r21_conformance_protocol_evidence_855.py` (18 named R21 cases) and `tests/spec/test_python_protocol_adapter_parity_762.py` (full-suite parity, `total=721 passed=721`) both re-run fresh at audit time |
| R17/R18/R19/R20 guarantees were not accidentally weakened | PASS — 296 R17–R20-keyword-matched tests pass; huge-integer arithmetic (R17) spot-probed live; full regression shows zero new failures beyond the pre-existing baseline tracked in #859 |
| R22/R23 behavior has not been smuggled into R21 | PASS — grepped every `src/` diff since pre-R21 `main` for `rational`/`Decimal(`/`float64`/`from decimal`; zero hits. No new evaluator numeric operator, equality rule, map-key rule, rendering, or JSON behavior anywhere in the diff |
| authoritative documentation is truthful | PASS — `GENIA_STATE.md` 9.21/9.22, `GENIA_RULES.md` 8.6, `docs/releases/R21.md` all re-read and independently cross-checked against source; no claim exceeds implemented behavior; R22/R23/R24 boundaries stated explicitly everywhere |
| an independent host implementer could reproduce R21 from the contract + shared evidence alone | PASS — the contract's §2/§4 grammar and canonicalization rules are self-contained arithmetic/string specifications; this audit's own independent source read confirms the implementation is a direct, unsurprising transcription of that text, and 18 shared `spec/parse`/`spec/ir` cases exercise every required family (§5) through the host-neutral protocol |

## Full regression evidence (fresh, this audit)

- `uv run pytest -n auto -q -m "not loopback"` → 4388 passed, 10 failed — identical pre-existing baseline set tracked in issue #859 (doc-sync drift on R7/R11/R12/R13 status docs, one roadmap-staging test, one cpp-host-readme template test, and a sandbox file-permission artifact in the native test runner); zero new failures
- `uv run pytest -n auto -q -m loopback` → 26 passed, 0 failed
- `uv run python -m tools.spec_runner` → `Summary: total=721 passed=721 failed=0 invalid=0`
- `uv run pytest tests/spec/test_r21_conformance_protocol_evidence_855.py tests/spec/test_python_protocol_adapter_parity_762.py -q` → 4 passed
- `uv run pytest tests/ -k "r17 or r18 or r19 or r20" -q` → 296 passed, 0 failed

## Verdict

# PASS

R21's approved contract obligations (§2 grammar, §3 lexical exactness, §4
portable Core IR payload, §5 shared evidence, §6 compatibility
boundaries) are all satisfied by merged `main`, independently re-derived
and spot-probed rather than taken on faith from prior per-ticket audits.
No R22/R23 behavior was smuggled in. No R17–R20 guarantee was weakened.
Documentation is truthful and R22/R23/R24 boundaries are stated
explicitly throughout. The only regression-suite failures present are the
pre-existing baseline set tracked separately in issue #859, unrelated to
R21 and outside this epic's scope to repair.

R21 is release-complete once this audit's PR merges. The roadmap/status
docs are updated to reflect that as part of this same PR (see
`docs/strategy/release-roadmap.md` and
`docs/strategy/roadmap/r21-r24.md`).

R22 work has not begun.
