# R21 Initial Execution Readiness after Issue #836

Status: **Planning — non-authoritative.** Candidate Genia contract revision:
`3fe03b8` (the #836 fixture implementation and portable cases are present in
its ancestry/current change). `GENIA_STATE.md` remains final authority.

## Verdict

**R21 readiness: NO-GO for semantic implementation. CONDITIONAL GO for
non-semantic repository/bootstrap preparation.**

R16, R17, R18, R19, and R20 are recorded complete by their authoritative
release/state documents. Issue #836 closes R20's cross-module shared-evidence
gap with eight dual-path portable cases. Two entry gates remain unsatisfied:

1. the exact-numeric-model documents are planning design and explicitly say
   NO-GO for implementation until a dedicated contract is approved and its
   remaining boundaries are resolved; and
2. `m0smith/genia-cpp` is not present in this workspace and the environment
   cannot access GitHub, so repository availability, bootstrap contents, and
   existing toolchain decisions could not be verified.

No C++ numeric or other semantic behavior may be inferred while those gates
remain open. Safe work is limited to creating/verifying repository metadata,
CI/toolchain scaffolding, and a runner invocation that initially reports cases
unsupported.

## Proposed minimal capability floor

The machine-readable proposal is
`docs/design/r21-minimal-capability-floor.json`. Capability claims are enabled
only after every named evidence case passes. Initial unsupported capabilities
include pipe mode, REPL, Flow, refs/cells, processes/actors, HTTP, providers,
resource IO, and distributed execution.

The first vertical slice is exactly three cases: `parse-literal-number`,
`unary-operators`, and `arithmetic-basic`. It proves parse, portable lowering,
eval, normalized response, and the generic runner without claiming a category.
It remains blocked because `arithmetic-basic` is numeric semantics and the
exact-numeric gate is incomplete. If bootstrap work begins earlier, it may wire
the protocol and produce the expected failing/unsupported evidence, but may not
implement the arithmetic result or advertise support.

## Ordered vertical increments

1. **Literal path:** the three cases above; parser/literal IR/evaluator/adapter;
   expected pre-implementation evidence is fail/unsupported; capability claims
   remain unchanged until all three pass. Authority: STATE/RULES, Core IR, R16,
   and the future approved exact-numeric contract.
2. **Collections/equality:** `pattern-list-exact`, `map-literal`,
   `map-put-replace-existing-key-preserves-order`, `r18-equality-kind-separation`, and
   `r18-map-key-equivalence-is-equality`; add list and insertion-ordered map
   values plus R18 equality/key rules.
3. **Calls/patterns/Outcomes:** `lambda-basic`, `case-patterns`,
   `pattern-literal-int`, `outcome-err-render`, and `outcome-pattern-err`;
   add callable frames, approved matching, and closed Outcome values.
4. **Pipelines/errors:** `pipeline-explicit`, `pipeline-call-shape-basic`, and
   `diagnostic-error-wrong-arity`; add ordered pipeline evaluation and R19
   normalized failure mapping.
5. **Minimal CLI:** `command_mode_basic`, then `file_mode_basic`; advertise
   `cli_command_mode` and later `cli_file_mode` only after their exact cases
   pass.
6. **R20 local:** all 9 parse, 5 IR, 4 original local eval, and 3 original local
   error cases.
7. **R20 cross-module:** the 8 #836 eval/error cases; implement the logical
   module fixture and existing R20 identity/linking semantics, then advertise
   `open_functions` only after all 29 R20 cases pass.

Every increment begins with pinned failing generic-runner evidence, changes only
the named C++ surface, and ends with normalized evidence. Later increments must
not be pulled into an earlier batch.

## Native primitive inventory

- **Portable Genia/prelude behavior:** shared prelude functions and public
  composition remain Genia source wherever feasible.
- **Required host-native primitives:** UTF-8/code-point string storage and
  iteration; arbitrary-precision integer operations (blocked pending numeric
  contract); ordered-map storage preserving R17 insertion order; evaluator
  allocation/call frames; each accepts/returns portable Genia values and maps
  misuse to contracted R19 diagnostics. These are prelude-internal/runtime, not
  new public functions.
- **Adapter-only:** JSON request decode/validation, normalized response encode,
  capability/revision advertisement, stdout isolation, timeout/process exit
  boundary, and logical fixture ingestion. Protocol errors never become Genia
  errors.
- **Deferred/unsupported:** every excluded capability listed above and all
  unapproved exact Decimal/Rational/Float64 behavior.

## Toolchain status

No existing C++ choices could be inspected. Proposed choices for explicit
review in `genia-cpp` are C++20, CMake, a locked dependency mechanism, Catch2,
clang-format, clang-tidy, a conforming JSON library, Boost.Multiprecision (or a
documented equivalent) for integers, ICU/utf8proc (or equivalent) for Unicode,
and vector-backed insertion order plus equality-aware lookup for maps. These
are implementation candidates only and define no Genia behavior.

## Ambiguities/blockers

- Exact-number source forms, JSON predicate, limits, Float64 NaN policy, and
  other items listed open by the numeric pre-flight require a separately
  approved upstream contract/spec issue. Slices 1 and 2 are blocked where they
  touch numbers.
- C++ repository/toolchain state must be inspected once accessible; do not
  replace existing documented choices without cause.
- Exact case existence/names in later increments must be machine-validated
  before execution; the JSON inventory deliberately pins only verified names.
