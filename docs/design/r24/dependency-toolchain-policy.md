# R24 C++ dependency/toolchain policy

Status: **Planning contract — non-authoritative.** Applies to
`m0smith/genia-cpp`. See `docs/design/r24-cpp-host-preflight.md` section 7.
Mirror this table into `m0smith/genia-cpp/AGENTS.md` and `README.md`.

Guiding rule: libraries implement approved Genia semantics; they never
define them. Prefer boring, mature, portable dependencies. Keep the
initial footprint small. Do not introduce a large hosted CI matrix —
local/self-hosted/pinned conformance evidence (an evidence JSON file
committed or attached to a PR) is acceptable and is what R16's evidence
model already expects from external hosts.

| Concern | Decision | Rationale |
|---|---|---|
| Build system | CMake (minimum version pinned once toolchain work starts) | Ubiquitous, no bespoke build DSL to maintain, works with every CI runner and every IDE the eventual contributors are likely to use |
| C++ language version | C++20 | Modern enough for `std::variant`/`std::span`/concepts to model tagged Core IR values cleanly, old enough to have universal compiler support; C++23 is not yet universally available on stable distro toolchains |
| Compiler support policy | GCC (latest two major versions) and Clang (latest two major versions) on Linux; no MSVC commitment at R24 | Matches genia-2026's own CI posture of not chasing every platform; MSVC support is a later-release decision, not an R24 blocker |
| Package/dependency management | Vendored/header-only or git-submodule pinned dependencies only; no package manager (no Conan/vcpkg) at R24 | Minimal host has only three real third-party needs (JSON, test framework, formatting) — a package manager is infrastructure the minimal host doesn't need yet and would itself need dependency-policy review |
| Test framework | Catch2 (single header, BSD-2, widely used) | Boring, mature, no build-system integration burden beyond one header |
| Formatting | `clang-format`, pinned config committed to the repo | Deterministic, no bikeshedding, works with every editor |
| Lint/static analysis | `clang-tidy`, pinned config, run in the local/self-hosted conformance job (not a separate hosted matrix entry) | Catches the exact defect classes the pre-flight worries about (uncaught exceptions crossing the diagnostic boundary, implicit narrowing) before they reach conformance evidence |
| JSON protocol handling | `nlohmann/json` (header-only, permissive license), used ONLY at the E16-1 adapter boundary | It implements the *transport* envelope (see native-primitive-inventory.md's adapter-transport row), never a Genia-visible data structure; Genia's own ordered-map/JSON-interchange semantics (R23) are implemented natively, not delegated to this library |
| Arbitrary-precision Integer representation | In-house bignum (sign + `std::vector<uint32_t>` magnitude, base 2^32 limbs) | R17/R22 require exact, deterministic, resource-limited behavior; a general-purpose bignum library's own limits/rounding are an unaudited dependency on someone else's semantics, which the pre-flight's "libraries implement semantics, don't define them" rule specifically warns against for this exact case |
| Decimal representation | In-house coefficient (bignum) + exponent pair, matching R21's tagged `IrLiteral` payload shape and R23's canonical rendering rules | Same reasoning as Integer — no third-party decimal library is contracted to match Genia's canonical rendering/rounding rules |
| Rational representation | In-house numerator/denominator pair over the Integer bignum, kept in R22's canonical reduced form | Same reasoning; built on the same in-house Integer kernel rather than a second bignum implementation |
| Explicit Float64 handling | Native `double`, boxed in a tagged runtime-value variant so it is never silently interchangeable with exact numerics (R22) | IEEE 754 binary64 is exactly what R22's Float64 contract specifies; no library needed, only correct tagging/boxing discipline |
| Unicode strategy | In-house UTF-8 decode/code-point iteration (no ICU); Genia strings are stored as validated UTF-8 byte buffers with code-point-aware iterators | R19's portable string contract is narrow enough (decode, iterate, diagnostic-safe substrings) that ICU's much larger surface (locale-aware casing/collation, etc.) is unneeded weight and risks pulling in behavior beyond what R19 actually contracts |
| Ordered-map representation | In-house insertion-ordered map: `std::vector<std::pair<Key,Value>>` plus a hash index from key to vector position, matching R17's insertion-order-preserving contract exactly | `std::map`/`unordered_map` do not preserve insertion order; a purpose-built structure keeps the ordering guarantee explicit and auditable rather than relying on a library detail |
| Diagnostic/error representation | In-house struct mirroring the R19 portable diagnostic schema (reason code, message, no free-form C++ type/exception text); C++ exceptions used only internally and always caught/normalized before crossing the adapter boundary | Matches pre-flight section 5's diagnostic-normalization boundary directly; no library dependency needed |
| CI/conformance invocation | Local/self-hosted job runs `cmake --build` + `ctest` (unit tests) + `python -m tools.spec_runner --host '<built adapter binary>' --evidence evidence.json` (conformance), with the evidence JSON attached to the PR; no large hosted matrix | Matches R16's evidence model, which already treats a deterministic evidence file as the unit of proof regardless of where it ran; avoids introducing hosted-CI cost/complexity this pre-flight was not asked to justify |

## Non-goals of this policy

- This policy does not choose a package manager for later, larger releases — that is a future decision if/when the dependency surface grows past what vendoring can reasonably handle.
- This policy does not authorize using any of these libraries to *decide* observable Genia behavior (e.g., using `nlohmann/json`'s own number parsing for anything Genia-visible) — every row above is scoped to where the dependency sits relative to the Core IR / diagnostic boundary.
