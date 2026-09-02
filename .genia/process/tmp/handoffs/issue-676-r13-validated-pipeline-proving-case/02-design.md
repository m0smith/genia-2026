# Design — issue #676 R13 validated-pipeline proving case

## 1. Purpose

Organize the contract as executable proving artifacts over existing runtime behavior; no runtime component changes.

## 2. Scope lock

Include the explicit standard-provider/view/conversion/Template/validated-record/protected-boundary composition and its shared/native/Python observations. Exclude new semantics, helpers, adapters, capabilities, and network behavior.

## 3. Architecture

`examples/r13_validated_pipeline_proving_case.genia` is the single source-visible application composition. It defines callable Template patterns for valid ports, qualified lookup helpers, existing record validation/collection, and an explicit success-pattern dispatcher to an injected boundary.

Portable shared specs execute focused slices of that ordinary source in eval, Flow, error, and CLI modes. A native Genia test imports/repeats source-visible invariants. Python tests load the example into a deterministic environment with injected environment and `.env` snapshot providers, then inject an R10 authority/audit observer and wrapped outbound fixture for host-boundary assertions.

No production file under `src/` changes.

## 4. File plan

New:
- `examples/r13_validated_pipeline_proving_case.genia`: runnable application proof.
- `examples/r13_validated_pipeline_proving_case.env`: deterministic lowest-precedence fixture without secrets.
- `tests/native/r13_validated_pipeline_proving_case.genia`: native source-visible proof.
- `tests/unit/test_r13_validated_pipeline_proving_case_676.py`: example, failure, snapshot, sentinel, authority, audit, and attempt-count proof.
- Focused YAML under `spec/eval`, `spec/flow`, `spec/error`, and `spec/cli`, plus one shared-spec inventory test.

Modified in later doc phase:
- `GENIA_STATE.md`, `README.md`, `docs/releases/R13.md`, `docs/strategy/release-roadmap.md`, `docs/strategy/r13-configuration-resolution-ergonomics.md`, and relevant release-index/status wording.

Removed: none.

## 5. Data/interface design

Provider source fixture values deliberately span precedence:
- overrides: server port and protected credential;
- explicit arguments: database port;
- injected environment: metrics port;
- explicit `.env`: a lower-precedence supporting ordinary value.

The example exposes ordinary functions for a qualified port Outcome, record validation/collection, protected credential acquisition, and authorized dispatch. Their inputs/outputs are existing provider, list/map, Outcome, protected, authority, and callable values only.

Top-level result is a map of safe, deterministic observations. The outbound fixture receives ordinary validated ports, the declassified credential, and clean records; it returns its ordinary receipt.

## 6. Control/error flow

Provider construction completes before any view use. Each qualified port helper performs one view lookup, then `parse_int`, then its callable Template. Records pass through existing `validate_each` and `collect_validated`.

Dispatch pattern-matches the exact existing Outcome shapes. Only the all-success arm evaluates `declassify` as part of the single outbound call. Every `none`/`err` arm propagates the exact reason/Outcome without invoking the boundary. Host authority/audit failures retain existing R10 fail-closed behavior.

## 7. Test plan input

- Concrete top-level outputs for three distinct `PORT` values, clean records, ordered diagnostics, and protected observations.
- Missing, malformed, and out-of-range values preserve exact Outcomes.
- Shared eval/Flow/CLI/error execution uses only existing syntax/Core IR.
- Native test proves source-visible composition.
- Deterministic host sources acquire once; later mutation does not refresh.
- Matching authority produces exactly one audit and outbound attempt.
- Provider/purpose mismatch, protected direct submission, provider failure, and malformed args produce zero outbound attempts.
- Generated sentinels are absent from safe observations, diagnostics, errors, and sanitized audit data.

## 8. Documentation impact

Record E13-6 as implemented proving/conformance behavior in `GENIA_STATE.md`; update user-facing R13 sections and release status. `GENIA_RULES.md` and `GENIA_REPL_README.md` need no semantic update. Review book (not present), cheatsheets, host docs, and composability matrix; no change is expected because no callable/semantic/composition boundary changes.

## 9. Complexity

Minimal. The design adds only composition fixtures and evidence around existing behavior.

## 10. Final check

Matches the contract, adds no host-specific language assumption, and is ready for failing-test authoring.
