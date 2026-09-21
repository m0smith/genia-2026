# E24 implementation issue sequence

Status: Planned roadmap detail — non-authoritative. Produced under
`docs/process/08-roadmap-ticketing.md` after the R24 pre-flight
(`docs/design/r24-cpp-host-preflight.md`) recorded GO on 2026-09-19.

This sequence targets the first genuine end-to-end C++ Genia execution as
early as possible (E24-2), then widens capability coverage in small
evidence-backed slices, rather than building disconnected parser/evaluator
subsystems for many tickets before any vertical proof exists. All work
happens in `m0smith/genia-cpp`; `genia-2026` is touched only to add
missing shared evidence if a slice finds a genuine gap (see E24-7).

Ordering follows `docs/process/08-roadmap-ticketing.md`: contract/pre-flight
(done) -> failing shared/conformance evidence -> smallest vertical
implementation -> capability declaration only after passing evidence ->
docs sync -> audit.

## E24-1 — Toolchain bootstrap and honest E16-1 adapter skeleton

- **Release target / roadmap alignment:** R24, first slice.
- **Problem statement:** `m0smith/genia-cpp` has no build system and its
  only adapter is a Python placeholder (`bootstrap/protocol_adapter_stub.py`)
  with no C++ code at all. Before any Genia semantics are implemented,
  the repository needs a real C++ toolchain and a real (still
  fully-unsupported) C++ E16-1 adapter binary to build on.
- **Includes:** CMake project skeleton per `docs/design/r24/dependency-toolchain-policy.md`; vendored/pinned Catch2, nlohmann/json; `clang-format`/`clang-tidy` configs; a C++ binary that reads one E16-1 JSON request from stdin and writes one response to stdout, correctly answering `capabilities` with every `spec/manifest.json` capability `unsupported` and every other operation `unsupported`; deletion of `bootstrap/protocol_adapter_stub.py` once the C++ binary replaces it (per `genia-cpp/AGENTS.md`'s existing instruction).
- **Excludes:** any parsing, lowering, or evaluation of Genia source; any capability declared as `supported`.
- **Affected docs/tests/specs:** `genia-cpp/README.md`, `genia-cpp/AGENTS.md` (pin table, build/test/lint commands); no `genia-2026` spec changes.
- **Acceptance criteria:** `python -m tools.spec_runner --host '<built binary>' --evidence evidence.json` run from a `genia-2026` checkout at the pinned revision produces deterministic evidence with 0 supported capabilities and every applicable case `unsupported`, 0 `fail`/`crash`/`protocol_error`.
- **Non-goals:** implementing any Genia behavior.
- **Drift risk:** low; scope is mechanically bounded by "still says unsupported to everything."
- **Required phases:** contract (done) -> minimal implementation -> docs sync.
- **Prerequisites:** R24 pre-flight GO.
- **Capability/case evidence targeted:** none claimed `supported`; full unsupported run against all applicable cases as a smoke test.

## E24-2 — First vertical slice: integer literals, arithmetic, `-c` mode

- **Release target / roadmap alignment:** R24, first semantic slice.
- **Problem statement:** Prove the entire mandatory path (`source -> parser -> portable Core IR -> evaluator -> normalized adapter result`) end to end on the smallest possible surface before any wider feature work.
- **Includes:** a parser for integer literals and `+ - * /`-style binary expressions; lowering to the approved `IrLiteral`/`IrBinary` Core IR nodes only; an evaluator for exact Integer arithmetic (using the native bignum kernel from `docs/design/r24/native-primitive-inventory.md`); `-c` command-mode CLI wiring; declaring `parser`, `ast_lowering`, `core_ir_eval` (partial), and `cli_command_mode` in the capabilities response once evidence passes.
- **Excludes:** lists, maps, lambdas, pattern matching, Decimal/Rational/Float64, file mode, open functions.
- **Affected docs/tests/specs:** none in `genia-2026` (uses existing cases); `genia-cpp` capability-status doc gains its first `supported` entries.
- **Acceptance criteria:** the `literals`, `exact_integer_arithmetic`, and `cli_command_mode` categories of `docs/design/r24/bootstrap-cases.json` (4 cases; see `m0smith/genia-2026#963` -- the `literals` category was corrected from 2 to 1 case, dropping a case that required out-of-scope pattern dispatch and string literals) pass with 0 fail via `tools/spec_runner --host`; capabilities response matches actual behavior exactly.
- **Non-goals:** any capability beyond the three named above.
- **Drift risk:** low-medium; the temptation is to "also handle lists while I'm in the evaluator" — explicitly excluded.
- **Required phases:** failing spec evidence (run bootstrap cases against E24-1's binary, confirm they fail/unsupported) -> minimal implementation -> capability declaration -> docs sync.
- **Prerequisites:** E24-1.
- **Capability/case evidence targeted:** `docs/design/r24/bootstrap-cases.json` categories `literals`, `exact_integer_arithmetic`, `cli_command_mode` (4 cases; see `m0smith/genia-2026#963`).

## E24-3 — Lists, ordered maps, equality/legal-key behavior, file mode

- **Release target / roadmap alignment:** R24.
- **Problem statement:** Widen the working vertical slice to cover R17/R18's portable data-structure and equality contracts, and add the second CLI entry point.
- **Includes:** list literal/construction Core IR + evaluator support; the in-house insertion-ordered map (per dependency policy); structural/identity equality per R18; file-mode CLI wiring; native UTF-8 decode for string literals used in these cases.
- **Excludes:** lambdas, pattern matching beyond what these cases already require, Decimal/Rational/Float64, open functions.
- **Affected docs/tests/specs:** none in `genia-2026`.
- **Acceptance criteria:** `list_construction_and_use`, `ordered_map_behavior`, `equality_and_legal_key_behavior`, `cli_file_mode` categories of `bootstrap-cases.json` (7 cases; two were replaced by `m0smith/genia-2026#968` with narrower substitutes that don't require E24-4-scope pattern dispatch/recursion) pass with 0 fail.
- **Non-goals:** widening equality/map coverage beyond these pinned cases in this ticket.
- **Drift risk:** medium — map/equality code is where "just special-case this Python behavior" temptation is highest; ambiguity-stop rule applies if any case's expected behavior isn't traceable to R17/R18 docs.
- **Required phases:** failing evidence -> minimal implementation -> capability declaration -> docs sync.
- **Prerequisites:** E24-2.
- **Capability/case evidence targeted:** `bootstrap-cases.json` categories `list_construction_and_use`, `ordered_map_behavior`, `equality_and_legal_key_behavior`, `cli_file_mode` (7 cases).

## E24-4 — Outcome values, lambdas, pattern/case dispatch, pipelines

- **Release target / roadmap alignment:** R24.
- **Problem statement:** Complete `core_ir_eval` coverage for the bootstrap floor's remaining control-flow/value categories.
- **Includes:** Outcome value representation and rendering; lambda/closure evaluation; pattern/case dispatch (non-open-function, local `case` only); pipeline (`|>`) composition; the deterministic runtime/error diagnostic case, wired through the diagnostic-normalization boundary.
- **Excludes:** open functions/`extend`/cross-module dispatch (E24-6); exact numeric runtime beyond plain Integer (E24-7).
- **Affected docs/tests/specs:** none in `genia-2026`.
- **Acceptance criteria:** `outcome_values`, `lambda_function_call`, `pattern_case_dispatch`, `pipeline_composition`, `deterministic_runtime_error_behavior` categories of `bootstrap-cases.json` (7 cases) pass with 0 fail.
- **Non-goals:** open-function dispatch semantics.
- **Drift risk:** medium — closures/pattern dispatch are where a C++-only shortcut IR is most tempting; must still lower only to approved Core IR nodes.
- **Required phases:** failing evidence -> minimal implementation -> capability declaration -> docs sync.
- **Prerequisites:** E24-3.
- **Capability/case evidence targeted:** `bootstrap-cases.json` categories `outcome_values`, `lambda_function_call`, `pattern_case_dispatch`, `pipeline_composition`, `deterministic_runtime_error_behavior` (7 cases).

## E24-5 — Diagnostic normalization boundary audit

- **Release target / roadmap alignment:** R24.
- **Problem statement:** E24-2 through E24-4 each route failures through the diagnostic boundary informally; this ticket is a dedicated, adversarial pass proving no STL/compiler/OS text can leak, before the surface grows further (R20, R21-R23).
- **Includes:** a fuzz/adversarial test pass feeding malformed input, resource-limit-triggering input, and forced internal exceptions at every layer (parser, lowering, evaluator, native primitives) and asserting every resulting adapter response matches the R19 portable diagnostic schema with no forbidden text (see pre-flight section 5's forbidden list).
- **Excludes:** any new user-visible feature.
- **Affected docs/tests/specs:** `genia-cpp` test suite only.
- **Acceptance criteria:** zero forbidden-text leaks across the adversarial test matrix; all existing bootstrap cases still pass (regression check).
- **Non-goals:** new Genia semantics.
- **Drift risk:** low.
- **Required phases:** minimal implementation (hardening) -> docs sync.
- **Prerequisites:** E24-4.
- **Capability/case evidence targeted:** re-run of all bootstrap-cases.json cases so far, plus new internal-only adversarial tests (not shared specs).

## E24-6 — R20 open functions / extensible pattern dispatch

- **Release target / roadmap alignment:** R24 (mandatory-for-completion capability per `docs/design/r24/capability-floor.json`).
- **Problem statement:** `open_functions` is an entry prerequisite and a completion-gate requirement, but not yet implemented in `genia-cpp`.
- **Includes:** local grouped/repeated open-function clauses; declaring `open_functions` `partial` (see acceptance-criteria annotation below for why not `supported`). Cross-module `open`/`extend`/`use` contribution and selection describes R20 the language contract, not this ticket's achievable `genia-cpp` scope — see `m0smith/genia-2026#971`.
- **Excludes:** any dispatch specificity/priority ranking (explicitly out of scope per R20 contract itself); cross-module `extend`/`use` evidence (requires `multi_file_eval`, explicitly out of R24 scope per `docs/design/r24/capability-floor.json` — see `#971`).
- **Affected docs/tests/specs:** none in `genia-2026`.
- **Acceptance criteria:** `open_functions_r20` category of `bootstrap-cases.json` (2 cases; the cross-module case was replaced by `m0smith/genia-2026#971` with the repeated-clause sibling of the grouped-clause case, since the original required `multi_file_eval`) passes; capability declared `partial` (not `supported` — no in-scope evidence proves cross-module dispatch) only after passing.
- **Non-goals:** anything R20's own contract lists as non-goals.
- **Drift risk:** medium — cross-module selection ambiguity handling must match R20's contract exactly (ambiguity is by design, not a bug to "fix"); moot for this ticket's actual (local-only) scope, relevant again once `multi_file_eval` enters R24 scope.
- **Required phases:** failing evidence -> minimal implementation -> capability declaration -> docs sync.
- **Prerequisites:** E24-4.
- **Capability/case evidence targeted:** `bootstrap-cases.json` category `open_functions_r20` (2 cases, both single-file/local as of `#971`); wider `spec/eval/r20-*.yaml`/`spec/ir/r20-*.yaml`/`spec/error/error-r20-*.yaml` families — including every `r20-cross-module-*.yaml` case, all of which require `multi_file_eval` — remain future follow-up evidence, gated on a roadmap-level decision to bring `multi_file_eval` into R24 scope, before `open_functions` can ever be declared fully (not partially) supported.

## E24-7 — Exact numeric runtime and interchange (R21-R23), including the R23 evidence gap

- **Release target / roadmap alignment:** R24.
- **Problem statement:** `docs/design/r24/portability-obligation-map.md` flags that no R23-specific (canonical rendering/JSON-boundary) shared eval cases were identified in the current spec inventory beyond the R22 numeric family. This ticket has a mandatory first phase to resolve that gap in `genia-2026` (contract/spec clarification — find or add the missing shared cases) before `genia-cpp` implementation proceeds, per the ambiguity-stop rule.
- **Includes:** Phase A (`genia-2026`): confirm whether R23-specific shared cases exist under a name not yet found, and if genuinely absent, open the gap as its own small `genia-2026` ticket to add them (this ticket does not silently invent them). Phase B (`genia-cpp`): Decimal/Rational runtime values, Float64 explicit boxing and mixed-domain rejection, exact-family arithmetic/division/comparison, canonical numeric rendering and JSON boundary.
- **Excludes:** any numeric syntax/semantics not already approved by R21-R23.
- **Affected docs/tests/specs:** possibly a new `genia-2026` spec addition (Phase A), gated through the normal spec-change process, not this ticket's `genia-cpp` implementation work.
- **Acceptance criteria:** `spec/eval/r22-*.yaml` (6 cases) plus whatever R23-specific cases Phase A resolves, all pass with 0 fail.
- **Non-goals:** transcendentals, ambient precision, new numeric syntax (all explicitly excluded by R21-R23 themselves).
- **Drift risk:** high if Phase A is skipped — implementing R23 rendering "by inference" from R22 evidence alone is exactly the ambiguity-stop rule's concern.
- **Required phases:** contract/spec clarification (Phase A) -> failing evidence -> minimal implementation -> capability declaration -> docs sync.
- **Prerequisites:** E24-4.
- **Capability/case evidence targeted:** `spec/eval/r22-*.yaml` (6 cases) plus Phase A's resolved R23 cases.

## E24-8 — R24 completion evidence, capability declaration, docs sync, audit

- **Release target / roadmap alignment:** R24 completion.
- **Problem statement:** Consolidate all prior slices into the completion evidence pre-flight section 12 requires, and run the skeptical audit before any claim that R24 is complete.
- **Includes:** full deterministic evidence run against the complete declared capability floor (`docs/design/r24/capability-floor.json`'s `generic_manifest_required_capabilities_claimed_at_r24_floor` plus `open_functions`); explicit unsupported-reason documentation for everything outside that floor; `GENIA_STATE.md`/`genia-cpp` README/AGENTS.md sync recording R24 completion; an independent skeptical release-truth audit modeled on R21/R22/R23's audit process, checking specifically for the defect classes this pre-flight and its skeptical-audit section named (stale numbering, capability claims without cases, diagnostic leakage, Core IR shortcuts, native primitives duplicating prelude behavior).
- **Excludes:** any new feature work; R25+ scope.
- **Affected docs/tests/specs:** `GENIA_STATE.md`, `genia-cpp/README.md`, `genia-cpp/AGENTS.md`, `docs/releases/R24.md` (new).
- **Acceptance criteria:** zero failed applicable cases across the full declared floor; audit records PASS or documents repairs the same way R23's did.
- **Non-goals:** none beyond scope exclusions above.
- **Drift risk:** low if E24-1 through E24-7 stayed disciplined; this ticket is a checkpoint, not new implementation.
- **Required phases:** docs sync -> audit.
- **Prerequisites:** E24-1 through E24-7.
- **Capability/case evidence targeted:** the full bootstrap suite plus every case added in E24-6/E24-7's follow-up evidence.

## Parking lot

None proposed at this time — every item above ties directly to the pinned
R24 minimal capability floor. Broader capabilities (pipe mode, REPL, Flow,
storage/HTTP, provider interop) remain in the roadmap's own parking lot
(`docs/strategy/roadmap/parking-lot.md`) and are out of scope for R24 per
the pre-flight's non-goals.
