# R19 Float Rendering Current-Behavior Inventory

Status: **Planning analysis — non-authoritative.** `GENIA_STATE.md` remains final authority for implemented behavior.

This inventory records current Python reference-host float rendering behavior that R19 must replace with an explicit portable contract. It does not change runtime behavior.

## Current implementation facts

General rendering is in `src/genia/utf8.py`:

- `format_display(value)` has no explicit float branch; floats fall through to Python `str(value)`.
- `format_debug(value)` has no explicit float branch; floats fall through to Python `repr(value)`.
- On current Python, `str(float)` and `repr(float)` generally use Python's shortest-round-trip-style decimal rendering, but that is a Python implementation/library contract, not yet a Genia contract.

The format engine adds more numeric rendering behavior:

- numeric precision formatting builds `Decimal(repr(value))` and rounds with `ROUND_HALF_UP` to the requested decimal places.
- zero-padding starts from `format_display(value)`.
- grouping starts from `format_display(value)` and then groups the integer part.

Therefore a future host cannot reproduce current output reliably by choosing arbitrary `printf`, iostream, `to_chars`, or library defaults.

## Inventory matrix

| Surface | Python reference-host behavior today | Portable status before R19 | R19 contract question |
|---|---|---|---|
| Ordinary float display | Python `str(float)` | implicit host behavior | Define one canonical finite-float rendering algorithm. |
| Float debug rendering | Python `repr(float)` | implicit host behavior | Decide whether debug equals display for floats or has a distinct contract. |
| Integral-looking float | Python emits decimal point for examples such as `1.0` | implicit | Preserve or deliberately change; must be exact. |
| Negative zero | Python preserves `-0.0` in `str`/`repr` | implicit | Specify sign preservation. |
| Exponent marker | Python uses lowercase `e` | implicit | Specify exact marker/case. |
| Exponent sign/digits | Python formatting rules | implicit | Specify exact canonical spelling. |
| Switch to exponent notation | Python threshold/algorithm | implicit | Choose algorithm, not a host default. |
| NaN | Python usually emits `nan` | implicit | Define exact spelling and whether payload/sign details are ignored. |
| Positive infinity | Python usually emits `inf` | implicit | Define exact spelling. |
| Negative infinity | Python usually emits `-inf` | implicit | Define exact spelling. |
| Precision spec | `Decimal(repr(value))`, decimal quantize, ROUND_HALF_UP | implementation behavior | Decide whether this exact semantic belongs in R19 portability or remains existing format-engine contract to be separately evidenced. |
| Zero padding | based on ordinary display text | transitively host-dependent | Becomes portable once ordinary rendering is portable. |
| Grouping | based on ordinary display text | transitively host-dependent | Becomes portable once ordinary rendering is portable. |

## Relationship to R18

R18 already owns equality semantics. R19 must not reopen them.

In particular:

- exact cross-kind numeric equality remains R18 behavior
- booleans remain distinct from numbers
- signed zero equality remains whatever R18 approved; R19 only defines visible rendering
- `NaN == NaN` remains false under R18; R19 only chooses deterministic text
- legal map-key behavior remains R18 territory

The representation contract must therefore preserve observability without changing equality.

## Recommended contract direction

The R19 draft should require a canonical algorithm with these properties, subject to approval:

1. finite floats render to a deterministic decimal string that round-trips to the same IEEE-754 binary64 value
2. among round-tripping representations, use a shortest/canonical representation rule independent of host libraries
3. integral-looking floats retain a visible float distinction (for example `1.0`, not `1`) unless the contract explicitly chooses otherwise
4. negative zero renders distinctly as `-0.0`
5. exponent spelling is fixed and locale-independent
6. non-finite spellings are fixed and locale-independent
7. display and debug rendering for floats are identical unless a concrete portability need justifies divergence

The contract may name an algorithmic property rather than mandate a particular library implementation. A C++ host may use `to_chars`, Ryu, Dragonbox, or another mechanism only if it produces the contracted output.

## Required future shared evidence

Candidate cases:

- `0.0`
- `-0.0`
- `1.0`
- ordinary fraction such as `1.5`
- a binary precision-sensitive value such as `0.1`
- values around exponent-switch boundaries chosen by the approved algorithm
- very small finite value
- very large finite value
- minimum/maximum normal/subnormal representatives where practical
- `inf`, `-inf`, `nan` if Genia continues to support them as float values
- nested list/map rendering containing the same floats
- debug and display equivalence/difference as approved

## Implementation-impact locations for later slices

At minimum, later implementation work must review:

- `src/genia/utf8.py` (`format_display`, `format_debug`)
- `src/genia/_format_engine.py` (`_format_numeric_precision`, zero padding, grouping)
- tests/specs that assert rendered numeric text
- adapter/result normalization paths that surface final values

R19 should avoid replacing every numeric formatter at once. Ordinary canonical rendering should be established first; dependent formatting should then be checked for compatibility.

## Non-goals of this inventory

- no equality changes
- no approximate-comparison API
- no locale-aware formatting
- no arbitrary-precision decimal type
- no C++ library selection
- no runtime changes
