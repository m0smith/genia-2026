# R22 Release Truth Audit — E22-11 (issue #897)

Status: durable skeptical release-audit evidence for R22 (epic #886). Not a
source-of-truth document; `GENIA_STATE.md` remains final authority. This
audit re-derives R22's obligations independently from the approved
contract and merged `main`, rather than trusting prior per-ticket audits
or this session's own earlier implementation prose.

Audited commit: `3ec522b4054c52f85bfd97ab07a825fb6ed2a73d` (merged #907,
`main` tip at audit time; includes E22-1 through E22-10, PRs #898–#907).

## Re-read sources

`AGENTS.md`; `GENIA_STATE.md` sections 9.21–9.31; `GENIA_RULES.md`
sections 8.6–8.7; `GENIA_REPL_README.md`; `README.md`;
`docs/ai/LLM_CONTRACT.md`; `docs/design/r22-exact-numeric-runtime-contract.md`
(the approved contract, re-read in full); `docs/design/r21-numeric-source-portable-representation-contract.md`
and `docs/releases/R21.md` (R21 dependency); `docs/analysis/exact-numeric-gate-postmortem.md`;
`docs/releases/R22.md`; `docs/strategy/release-roadmap.md`,
`docs/strategy/roadmap/r21-r24.md`, `docs/strategy/roadmap/sequence.md`;
every merged R22 issue (#887–#896) and PR (#898–#907) via their diffs and
descriptions; the source files implementing R22 directly
(`src/genia/numeric_runtime.py`, `src/genia/equality.py`'s numeric
sections, `src/genia/evaluator.py`'s binary-operator dispatch, `src/genia/builtins.py`'s
`rational`/`float64`/`exact`/`syntax_self_evaluating_fn` registrations,
`src/genia/sheet.py`, `src/genia/retrieval.py`); shared evidence
(`spec/eval/r22-*.yaml`, `spec/error/r22-*.yaml`,
`tests/spec/test_python_protocol_adapter_parity_762.py`).

## Independent re-derivation

Read the implementation directly rather than trusting prior per-slice
audit prose, cross-checking every line against the corresponding contract
section:

- **Decimal (§2)**: `GeniaDecimal.__init__` canonicalizes
  `coefficient * 10**exponent` via `_canonicalize` — zero collapses to
  `(0, 0)`, trailing base-10 zeros are stripped with the count folded into
  the exponent, sign lives in the coefficient, and there is no
  negative-zero identity. `make_decimal_from_payload` builds a
  `GeniaDecimal` directly from R21's already-canonical string
  coefficient/exponent — confirmed zero `float()` calls anywhere in the
  Decimal construction path.
- **Rational (§3)**: `rational_from_integers` divides by `_gcd`
  (always-positive gcd via `abs()`), forces the denominator positive by
  negating the numerator when needed, and collapses a reduced denominator
  of `1` to a plain Integer rather than a `GeniaRational` instance —
  confirmed no code path can ever construct a `GeniaRational` with
  denominator `1` or a non-reduced pair.
- **Exact arithmetic (§6)**: `_decimal_binop`/`_decimal_mul` handle
  Integer/Decimal-only `+`/`-`/`*` via a common power-of-ten denominator;
  `_rational_binop`/`_rational_mul` handle any pairing involving a
  `GeniaRational` via `_to_exact_fraction` cross-multiplication. Verified
  the promotion table cell-by-cell against §6's table: Decimal participates
  and retains Decimal kind even for an integral result (no auto-collapse to
  Integer); Rational is the top of the lattice, so `GeniaDecimal.__add__`
  etc. explicitly return `NotImplemented` for a `GeniaRational` right
  operand and let Python's reflected-method protocol route to
  `GeniaRational`'s own arithmetic.
- **Exact division (§7)**: `exact_divide` cross-multiplies to a reduced
  `(numerator, denominator)`, then dispatches by operand kind exactly per
  the table: any `GeniaRational` operand → `rational_from_integers`; pure
  `int`/`int` → Integer when `denominator == 1`, else
  `rational_from_integers` (**never** Decimal, confirmed by direct source
  read — there is no code path from the pure-int branch into
  `_decimal_from_reduced_fraction`); a `GeniaDecimal` operand (no
  Rational) → `_decimal_from_reduced_fraction` when
  `_terminates_in_base10(denominator)` (denominator has only 2/5 prime
  factors after reduction), else `rational_from_integers`. Division by
  exact zero raises `ZeroDivisionError` before any of this dispatch runs.
- **Exact remainder (§8)**: `exact_remainder` computes
  `floor_quotient = quotient_numerator // quotient_denominator` after
  forcing `quotient_denominator` positive (negating both if needed) — since
  Python's `//` on two ints is floor division and the denominator is now
  always positive, this is floor division regardless of the sign of either
  original operand, then returns `left - floor_quotient * right` using the
  already-verified exact-family `-`/`*` operators. Spot-probed empirically
  (not just read): `(-7) % 3 = 2`, `7 % (-3) = -2`, `(-7) % (-3) = -1`,
  `(-7.5) % 2 = 0.5` — all match Python's own floor-remainder semantics
  extended to the exact domain, confirming negative-operand correctness.
- **Float64 (§4/§5)**: no dedicated wrapper — a bare Python `float` already
  is one IEEE-754 binary64 value. `to_float64` converts an exact value via
  `numerator / denominator` on arbitrary-precision Python ints, which
  CPython specifies to be correctly rounded (round-to-nearest,
  ties-to-even); confirmed this is the same `_to_exact_fraction` helper
  `exact_divide` uses, not a `float()`-of-text path, and that
  `OverflowError` from Python's own true-division-of-huge-ints is
  re-raised with this project's own message rather than silently producing
  infinity. `exact()` uses `float.as_integer_ratio()` (CPython-guaranteed
  exact, power-of-two denominator), scales by the matching power of five
  to reach a power-of-ten denominator, and constructs the `GeniaDecimal`
  directly — confirmed exact by construction, not an approximation;
  spot-probed the contract's own worked example
  (`exact(float64(0.1))` → `0.1000000000000000055511151231257827021181583404541015625`)
  and it matches exactly. NaN/±infinity are conversion failures in both
  directions (`to_float64` never receives them as exact-family input by
  construction; `exact()` explicitly raises for them).
- **Mixed-domain rejection (§9)**: `is_mixed_exact_and_float64` is checked
  first, before any other dispatch, in every one of `evaluator.py`'s
  `PLUS`/`MINUS`/`STAR`/`SLASH`/`PERCENT` cases (confirmed by direct read
  of all five `match` arms) — mixed arithmetic can never reach Python's
  native operator dispatch at all, so there is no path by which
  `GeniaDecimal`'s own dunder methods (which separately also reject float,
  as a redundant safety net) could be bypassed.
- **Comparison/equality (§10)**: `numeric_order`/`_magnitude_kind` in
  `numeric_runtime.py` and `_numeric_equal` in `equality.py` both decompose
  every operand — exact values to their own exact fraction, a finite
  Float64 to its own exact fraction via `as_integer_ratio()` — before any
  comparison; neither ever converts an exact operand to `float` first.
  Confirmed NaN is unordered (`numeric_order` returns `None` when either
  side is `("nan",)`) and unequal to everything including itself
  (`_numeric_equal`'s float/float branch explicitly checks
  `math.isnan(left) or math.isnan(right)` before falling back to `==`).
  Booleans are excluded from every one of these numeric paths
  (`_magnitude_kind`, `_exact_is_zero`, `_to_exact_fraction`,
  `_is_exact_numeric_kind` all check `isinstance(value, bool)` first and
  reject/exclude it), matching contract §1's "booleans are not numbers"
  for every surface R22 itself owns.
- **R18 single relation (§10, §14)**: read `equality.py` in full — there is
  exactly one `genia_equal` function and one `canonical_map_key` function;
  `_numeric_equal` is a private helper `genia_equal` calls, not a second
  public relation. `canonical_map_key` buckets Integer and an
  integral-valued Decimal/Rational/float into the same `("num", ...)` key,
  and buckets every non-integral exact/Float64 value into a shared
  `("num-fraction", numerator, denominator)` key after reducing
  `GeniaDecimal`'s (not-always-reduced) fraction form — confirmed an equal
  legal numeric key produces an identical internal identity regardless of
  which of Integer/Decimal/Rational/Float64 it came from. NaN raises
  `TypeError` at `canonical_map_key` before any bucket is reached — spot-
  probed live (`map_put(map_new(), __r18_conformance_test_only_nan, 1)`
  raises `"map key must equal itself; NaN is not a legal map key"`).
- **Resource limits (§11)**: `NumericResourceLimitError` is its own
  exception class, never `OverflowError` (reserved for `float64`'s
  genuine binary64 magnitude overflow) or `TypeError` — confirmed by
  direct read of `_check_resource_limit`, `GeniaDecimal.__init__`, and
  `rational_from_integers`, plus the existing
  `test_resource_limit_is_not_reported_as_type_error_or_overflow` test.
  The bound is checked via cheap `bit_length()` on raw input before any
  expensive canonicalization, pre-empting the raw Python
  `sys.set_int_max_str_digits` leak that predated this slice (E22-8's own
  finding). The seam (`_numeric_resource_limit_test_seam`) is a private
  Python context manager, not a Genia builtin — confirmed unreachable from
  Genia source by direct grep of every `env.set`/`register_autoload` call
  in `builtins.py` (no match) and by the existing
  `test_resource_limit_seam_not_reachable_from_genia_source` test.
- **Error boundary (§13)**: every misuse family listed in §13 (exact/
  Float64 division/remainder by zero, invalid `rational`/`float64`/`exact`
  arguments, mixed exact/Float64 arithmetic, `numeric-resource-limit`) has
  its own focused test in `tests/unit/test_r22_misuse_resource_limits_894.py`
  asserting the exact message string with no `Traceback`/`.py` substring —
  re-ran this file fresh (18 passed) rather than trusting the prior slice's
  report of it.

## R21 boundary: confirmed not reopened

Diffed every R22-cycle commit (`2d789ab`, R21's own completion commit,
through the audited tip) against `src/genia/lexer.py`, `src/genia/parser.py`,
`src/genia/numeric_source.py`, `docs/design/r21-numeric-source-portable-representation-contract.md`,
and `docs/architecture/core-ir-portability.md`:

- `lexer.py`/`parser.py`: the only change in the entire R22 cycle is a
  `from __future__ import annotations` line added to each file (4 lines
  total) — no grammar, tokenization, or new syntax change of any kind.
  This directly disproves any new numeric literal syntax (no Rational
  literal, no Float64 suffix, no raw-bit syntax) was introduced.
- `numeric_source.py`: the only change (in E22-1's own commit, `b759c46`)
  is `numeric_literal_runtime_value`'s return type, retiring the R21-era
  evaluator compatibility shim that returned a host `float` for Decimal
  source, in favor of constructing a genuine `GeniaDecimal` — this is
  exactly the transition R21's own release page anticipated ("R22 will
  define actual Decimal/Rational runtime values ... over the Core IR
  boundary this release freezes"), not a reopening of R21's classification/
  lowering logic (§2–§4 of the R21 contract, which govern lexical
  classification and the tagged `IrLiteral` payload shape, both untouched).
- R21's own contract and architecture docs: zero diff.

## R23 boundary: confirmed no leak

- `json_encode` (`builtins.py`) has no case for `GeniaDecimal`/
  `GeniaRational` in `_strict_json_from_runtime` and falls through to a
  clean, structured `unsupported_json_value` diagnostic — re-verified by
  direct source read; no JSON numeric transport policy decision (lexical
  JSON Decimal decode, `stable_json_decimal`, Rational/Float64 JSON rules)
  was implemented.
- Every `__repr__`/`__str__` on `GeniaDecimal`/`GeniaRational` is
  explicitly commented `# pending R23 canonical spelling` and exists only
  so values can be printed without crashing during development — not
  offered anywhere as canonical display truth. `docs/releases/R22.md` and
  `GENIA_STATE.md` both classify display/JSON policy as pending R23, never
  claiming it as delivered.
- No C++ host work: this audit's source tree is `genia-2026`; no commit in
  the R22 cycle touches `m0smith/genia-cpp` (out of this repository's
  scope entirely, and no R22 issue/PR references it).

## Cross-surface conformance (E22-9's own scope, independently re-checked)

Re-read `quote_node`/`quasiquote_node`'s `qq()` in `evaluator.py` and
`syntax_self_evaluating_fn` in `builtins.py` directly (not merely trusting
E22-9's PR description): both now route a `Number` AST node through
`numeric_literal_runtime_value(numeric_literal_payload(node))`, matching
ordinary evaluation exactly, and the metacircular self-evaluating
predicate recognizes `GeniaDecimal`/`GeniaRational` alongside `bool`/`int`/
`float`/`str`. `pattern_match.py`'s `IrPatLiteral` case dispatches through
`genia_equal`, confirmed by direct read (`return {} if
genia_equal(pattern.value, arg) else None`). `optimizer.py` performs no
arithmetic constant folding of any kind — its only numeric-literal-aware
logic (`_is_integer_literal_one`) is scoped to tail-recursion-to-loop
detection and already calls `numeric_literal_runtime_value` on the tagged
payload. `sheet.py`'s `_csv_scalar_text` and `retrieval.py`'s
`_is_finite_score` both accept `GeniaRational` alongside `GeniaDecimal`.

## Shared evidence: fresh run at the audited commit

Re-ran every regression partition fresh against the audited commit
(`3ec522b`), rather than reusing E22-10's own pre-merge numbers:

```
uv run pytest -n auto -q -m "not loopback"   # 4456 passed
uv run pytest -n auto -q -m loopback         # 26 passed
uv run python -m tools.spec_runner           # Summary: total=740 passed=740 failed=0 invalid=0
uv run pytest tests/spec/test_python_protocol_adapter_parity_762.py  # 1 passed
```

The subprocess protocol parity suite proves the in-process and generic
subprocess-protocol paths agree on every applicable case (the same
`total=740 passed=722` assertion E22-9 established, still current).

## Skeptical spot-probes (beyond the existing test suite)

Ran ad hoc probes against edge cases and a boundary the existing test
suite does not literally spell out, specifically to hunt for a subtle sign,
rounding, or boundary bug that per-slice unit tests (written by the same
author as the implementation) might share a blind spot with:

| Probe | Result |
|---|---|
| `(-7) % 3` | `2` |
| `7 % (-3)` | `-2` |
| `(-7) % (-3)` | `-1` |
| `(-7.5) % 2` | `0.5` (Decimal/Integer floor remainder) |
| `float64(-7) % float64(3)` | `2.0` |
| `float64(1) / float64(3)` | `0.3333333333333333` |
| `float64(rational(1, 3))` | `0.3333333333333333` (agrees with the direct float64/float64 division above) |
| `exact(float64(0.1))` | `0.1000000000000000055511151231257827021181583404541015625` (matches contract §5's own worked example exactly) |
| `map_put(map_new(), NaN, 1)` | raises `"map key must equal itself; NaN is not a legal map key"` |
| `1 + float64(2)` | `none("type-error", {source: "+", left: "int", right: "float"})` |

All match the mathematically/contractually expected result.

## One observation: not a contract violation, not R22's to fix

`true + 1` evaluates to `2` (plain Python `bool`-as-`int` arithmetic
fallthrough in the evaluator's native `+`/`-`/`*` dispatch, since `PLUS`/
`MINUS`/`STAR` — unlike `SLASH`/`PERCENT`, which explicitly gate on
`is_exact_numeric` — fall through to a bare `left + right` when neither
operand is Float64). This is **not** a new R22 defect: diffed
`evaluator.py`'s `PLUS` case against the pre-R22 commit (`90fac29`) and
confirmed byte-for-byte identical `try: return left + right / except
TypeError: ...` logic, unchanged by any R22 slice. Contract §1's "booleans
are not numbers" is satisfied by every surface R22 itself owns and was
asked to own — `is_exact_numeric`, `_exact_is_zero`, `_to_exact_fraction`,
`_magnitude_kind`, and `canonical_map_key` all explicitly exclude `bool`
from the exact family, confirmed above. General boolean/`+`/`-`/`*`
interoperation is a pre-existing, pre-R22 language design question (dating
to R1) outside this contract's scope (§6 defines the Integer/Decimal/
Rational lattice, not general operand-type policing for `+`/`-`/`*`) and is
not filed as an R22 repair issue; a future release may address it on its
own terms if desired.

## Verification checklist (all 21 audit-specific risks from the R22 orchestration brief)

| # | Risk | Result |
|---|---|---|
| 1 | Decimal never transits binary64 | PASS — zero `float()` calls in `GeniaDecimal` construction/canonicalization; `make_decimal_from_payload` builds directly from R21's string payload |
| 2 | Rational normalization deterministic | PASS — `rational_from_integers` always gcd-reduces, forces positive denominator, collapses denominator-1 to Integer; no non-canonical `GeniaRational` construction path exists |
| 3 | Exact arithmetic exact | PASS — fraction-based `_decimal_binop`/`_rational_binop`/`_rational_mul` over arbitrary-precision ints, no float anywhere |
| 4 | Exact division domain selection correct | PASS — `exact_divide` dispatch matches contract §7's table cell-by-cell, confirmed by direct read; pure Integer/Integer never becomes Decimal |
| 5 | Floor remainder correct including negative operands | PASS — verified by code read and live spot-probes across all four sign combinations |
| 6 | Float64 explicit, not in exact lattice | PASS — `is_exact_numeric` excludes `float`; §6/§7 promotion tables never include Float64 |
| 7 | `float64` round-nearest-ties-even | PASS — reuses CPython's correctly-rounded `int/int` true division; `OverflowError` re-raised cleanly rather than silent infinity |
| 8 | `exact(Float64)` exact | PASS — `as_integer_ratio()`-based reconstruction, confirmed exact by construction; contract's own worked example reproduced exactly |
| 9 | Mixed arithmetic rejected | PASS — `is_mixed_exact_and_float64` checked first in every evaluator arithmetic case, before any native dispatch |
| 10 | Comparison bridge never rounds exact operand | PASS — both sides decomposed to exact fractions before comparison; float side uses `as_integer_ratio()`, never rounds the exact side to float |
| 11 | R18 equality/key is one relation | PASS — exactly one `genia_equal`/`canonical_map_key` pair; `_numeric_equal` is a private helper, not a second public relation |
| 12 | NaN key behavior correct | PASS — `canonical_map_key` raises `TypeError` for NaN before any bucket; live-probed |
| 13 | No raw host exceptions escape | PASS — every misuse family has an authored, tested message with no `Traceback`/`.py` substring; E22-8's specific fix for the `sys.set_int_max_str_digits` leak confirmed still in place |
| 14 | Resource limits don't masquerade as overflow | PASS — `NumericResourceLimitError` is its own exception class, distinct from `OverflowError`/`TypeError`, confirmed by direct read and existing test |
| 15 | R21 not reopened | PASS — lexer/parser diff since R21's completion commit is 4 lines of `from __future__ import annotations`; `numeric_source.py`'s one change is the anticipated evaluator-shim retirement; R21's own contract/architecture docs have zero diff |
| 16 | R23 policy did not leak in | PASS — `json_encode` still rejects Decimal/Rational cleanly; every Decimal/Rational `__repr__` is explicitly marked pending-R23; docs consistently classify display/JSON as pending |
| 17 | No new numeric literal syntax | PASS — same 4-line lexer/parser diff as risk 15; `rational(...)` is an ordinary function call, not new syntax |
| 18 | No C++ work appeared | PASS — no commit in the R22 cycle touches `m0smith/genia-cpp`; out of this repository's scope |
| 19 | Metacircular/quoted/pattern/optimizer paths correct | PASS — E22-9's fixes independently re-read and confirmed still in place; optimizer performs no arithmetic folding at all |
| 20 | Shared in-process/subprocess evidence agrees | PASS — fresh run at the audited commit: 740/740 spec runner, subprocess protocol parity suite passed |
| 21 | Docs describe only merged truth | PASS — `docs/releases/R22.md`'s examples independently re-run against the audited commit and match verbatim; roadmap docs (`release-roadmap.md`, `r21-r24.md`, `sequence.md`) describe R22 as "in progress" (E22-1 through E22-10 merged, E22-11 pending), not COMPLETE |

## Verdict

**PASS.**

Every one of the 21 audit-specific risks holds under independent
re-derivation from the approved contract and direct source/test evidence,
not merely by trusting prior per-slice audit prose. Full regression (both
partitions), the shared spec suite, and the subprocess protocol parity
suite are all green at the audited commit. R21 was not reopened. No R23
policy, new numeric literal syntax, or C++ host work leaked in. The one
observation recorded above (`true + 1` boolean-arithmetic fallthrough) is
confirmed pre-existing and outside this contract's scope, not a defect
this audit treats as blocking.

Per issue #897's acceptance criteria, this PASS is required before:

- Epic #886 (R22) can be closed.
- Roadmap status can be updated to **R22 COMPLETE** — via a narrow
  follow-up docs change, not bundled into this audit's own PR.
- R23 (Numeric Representation and Interchange) can begin, remaining
  planned and not implemented as of this audit.
