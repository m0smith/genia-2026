# R24 native primitive inventory

Status: **Planning contract — non-authoritative.** Applies to `m0smith/genia-cpp`. See `docs/design/r24-cpp-host-preflight.md` section 4.

This is the initial inventory of things `genia-cpp` must implement in
native C++ rather than reuse from a shared Genia/prelude source, because
they sit below the portable Core IR boundary (process/runtime/transport
concerns) or because no portable prelude implementation exists to port
(bignum kernels). It does not authorize any *public Genia behavior* to be
implemented natively that duplicates prelude semantics — prelude functions
(list/map helpers, `first`, `nth`, formatting, etc.) must be interpreted
from the same shared Genia source every other host uses, not reimplemented
in C++.

| Primitive | Why host-native | Portable input contract | Portable output contract | Misuse/error behavior | Visibility | Authoritative source |
|---|---|---|---|---|---|---|
| E16-1 adapter transport (stdin/stdout JSON request-response loop) | Below Core IR; a process boundary, not Genia semantics | One JSON object per E16-1 request schema (`tools/spec_runner/protocol.py`) | One JSON object per E16-1 response schema | Malformed/unreadable request -> `protocol_error` outcome per the runner's taxonomy, never a crash | Adapter-only | `docs/design/r16-multi-host-conformance-infrastructure-contract.md` |
| Capabilities declaration | Below Core IR; reports what this binary implements, is not itself Genia behavior | `capabilities` operation (`case_id: __capabilities__`) | Every name in `spec/manifest.json`'s required/optional vocabulary declared `supported`/`partial`/`unsupported`, plus `contract_revision` and protocol version | Declaring an unknown capability name aborts the run before any case executes (E16-3 rule) | Adapter-only | `docs/design/r16-multi-host-conformance-infrastructure-contract.md`; `docs/design/r24/capability-floor.json` |
| Arbitrary-precision Integer arithmetic kernel | No portable prelude implementation exists to port; must be built once as an in-house bignum (magnitude + sign, base-appropriate digit vector) so its exact overflow-free, deterministic behavior matches R17's contract bit-for-bit, not merely "close enough" via a third-party library's own rounding/limit choices | Two arbitrary-precision integers plus an operator (`+ - * / floor-div rem cmp`) | Exact arbitrary-precision integer result, or the R17/R22 misuse diagnostic (e.g. division by zero) | Division by zero, or any operation exceeding a documented resource limit, normalizes to the same portable diagnostic shape R19/R22 define — never an STL/library exception string | Prelude-internal (backs the `Integer`/exact-family runtime value; never called directly by user Genia code) | `docs/design/r17-numeric-ordered-map-portability-contract.md`; R22/R23 numeric contracts |
| Decimal/Rational runtime representation | Same reasoning as Integer: R21-R23 define exact coefficient/exponent and numerator/denominator semantics that a generic decimal/rational C++ library is not guaranteed to preserve exactly | R21's tagged `IrLiteral` numeric payload, or a runtime exact-family value | Canonical Decimal/Rational runtime value per R22/R23 rendering rules | Malformed source classification is a parser diagnostic, not a runtime exception; runtime misuse follows R22 §8 | Prelude-internal | R21/R22/R23 numeric contracts |
| Float64 boxing/conversion | IEEE 754 binary64 is a native machine type; genia-cpp must box it as an explicit tagged value rather than silently aliasing it with exact numerics (R22's mixed-domain-rejection rule) | A `float64(...)` conversion call or Float64 literal payload | Explicit Float64-tagged runtime value; ordering/equality per R22 `r22-exact-family-and-float64-ordering`/`r22-exact-family-equality` | Mixed exact/Float64 arithmetic without explicit conversion is rejected per R22, not silently coerced | Prelude-internal | R22 numeric contract |
| UTF-8 decode/code-point iteration | Below Core IR; C++ has no built-in Unicode-aware string type, so decoding UTF-8 into the code-point sequence R19 requires must be native | Raw UTF-8 byte sequence from source/stdin/argv | R19 portable string/code-point value | Invalid UTF-8 normalizes to the R19 diagnostic contract, never a raw decode-library exception | Adapter/runtime-internal | `docs/host-interop` Unicode references; R19 release contract |
| Diagnostic/error normalization boundary | Below Core IR; translates internal C++ failure modes (parse errors, native-primitive misuse, uncaught exceptions) into the portable diagnostic shape | Internal C++ exception/error state | R19-conformant portable diagnostic (`reason`, message, no STL/OS/compiler text) | Every native failure path funnels through this boundary before crossing into shared conformance evidence — see pre-flight section 5 | Adapter-internal | R19 release contract; pre-flight section 5 |
| CLI argv/exit-code/file-read primitives (`-c`, file mode) | Below Core IR; process argv, `sys.exit`-equivalent, and file I/O are OS-level concerns | CLI invocation shape defined by `spec/cli/*.yaml` (`cli_command_mode`, `cli_file_mode`) | stdout/stderr/exit-code triple exactly as the case's `expected` block specifies | Missing file / bad argv normalizes to the same diagnostic contract as any other runtime error | Adapter-only | `spec/cli/*.yaml`; HOST_INTEROP.md |

## Explicitly NOT native

- List/map prelude helpers (`first`, `nth`, `map`, `items`, `keys`, `values`, etc.) — interpreted from the shared Genia prelude source, same as every other host.
- Pattern/case dispatch and open-function selection logic — this is Core IR evaluator behavior (R20 contract), not a native primitive; only the underlying comparison/equality primitives it calls down into (Integer/Decimal equality, structural equality) are native.
- Formatting/rendering of user-facing values — driven by the shared format-spec contract (R23); native code supplies the underlying numeric-to-digit-string kernel only, not the format-spec interpretation itself.

## Process for adding a primitive later

Adding any native primitive not listed here requires, before it is used in
shared conformance evidence: (1) a written justification here explaining
why no portable prelude source can supply the behavior, (2) the same five
columns as the table above, and (3) passing evidence for the shared cases
that exercise it. See pre-flight section 3 ("written justification and
shared conformance evidence proving equivalence").
