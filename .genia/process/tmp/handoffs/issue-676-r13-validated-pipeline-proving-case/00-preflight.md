# Preflight — issue #676 R13 validated-pipeline proving case

## 0. Branch

- Required/current: `feature/issue-676-r13-validated-pipeline-proving-case`
- Base: `main`

## 1. Scope lock

Includes:
- One offline, executable, application-owned Outcome-aware validated-data-pipeline example.
- Deterministic conventional provider sources with distinct server, database, and third qualified `PORT` settings.
- Explicit conversion and existing callable Template validation.
- Existing `validate_each`/`collect_validated` clean values and structured diagnostics.
- One protected credential carried to an injected authorized boundary, with sentinel non-leakage and at-most-one declassification/attempt assertions.
- Executable example, shared eval/Flow/CLI observations where useful, native/Python coverage, and truthful implemented-state/release documentation.

Excludes:
- New configuration, validation, pipeline, diagnostic, model, HTTP, protection, or declassification APIs or semantics.
- Real credentials/networking, retries, repair, fallback, agents, or hidden lifecycle behavior.
- Transformation of successful Template payloads beyond existing semantics.

## 2. Source of truth

Authoritative: `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, `AGENTS.md`.

Additional relevant: issue #676; `docs/design/r13-configuration-resolution-contract.md`; `docs/strategy/r13-configuration-resolution-ergonomics.md`; `docs/strategy/killer-workflow.md`; `docs/strategy/release-roadmap.md`; existing R10/R11 proving cases and R13 E13-1–E13-5 tests.

Notes: E13-0 is approved and E13-1 through E13-5 are implemented. The approved R13 contract already requires this exact proving composition. No unresolved dependency remains.

## 3. Feature maturity

- Stage: Experimental.
- Wording: executable proof over Experimental R13 APIs; Python is the only implemented host and shared/multi-host conformance remains Partial.

### 3a. Portability analysis

- Portability zone: portable application-level ordinary value/callable composition, plus Python reference-host fixture verification at the authorized declassification boundary.
- Core IR impact: none.
- Capability categories affected: no new category; existing configuration environment/`.env` acquisition, protected declassification/audit, and injected ordinary host-call boundary are exercised.
- Shared spec impact: add source-visible eval/Flow/CLI observations using existing calls and values.
- Python reference host impact: add tests injecting deterministic environment/`.env` snapshots, one matching authority, audit observer, and outbound fixture; no runtime implementation change.
- Host adapter impact: none; existing injected callable and authority adapters are reused unchanged.
- Future host impact: future hosts can run the portable source-visible proving composition after implementing existing R10/R13 contracts; host-local authority injection remains host responsibility.

## 4. Contract vs implementation

- Portable contract: deterministic explicit provider/view/Outcome/Template/Flow composition; exact existing failure propagation; protected credential opacity and one authorized reveal/attempt maximum.
- Python implementation today: all constituent E13-1–E13-5 and R10 pipeline/protection behavior exists; this ticket supplies proving artifacts only.
- Not implemented: any new API, ambient provider, network transport, retry/fallback, schema system, or lifecycle injection.

## 5. Test strategy

- Core invariants: qualified `PORT` values never collide; conversion and Template failures remain exact Outcomes; valid/invalid records produce deterministic ordered clean output/diagnostics; credential is never rendered; only the matching injected boundary reveals once and attempts outbound once.
- Expected behavior: offline example returns stable safe observations; valid authorized dispatch returns an ordinary receipt.
- Failure cases: missing/malformed config, Template mismatch, provider failure, authority mismatch, and protected direct-host submission all prevent outbound effects and leak no sentinels.
- Approach: failing inventory/example tests first; shared spec runner coverage, native Genia test, focused Python-host boundary tests, then nearby and full regression.

## 6. Examples

- Minimal: three qualified views resolve distinct `PORT` strings from one explicit standard provider.
- Real: configured validation of mixed records produces clean records and diagnostics, then submits clean data with one declassified credential at an authorized injected fixture.

## 7. Complexity check

- Revealing structure.
- Justification: composition-only proof demonstrates the approved APIs together without new machinery.

## 8. Cross-file impact

- Likely: `examples/r13_validated_pipeline_proving_case.genia`, `tests/native/`, `tests/unit/`, `spec/{eval,flow,cli,error}/`, shared-spec test inventory, `GENIA_STATE.md`, `README.md`, `docs/releases/R13.md`, and release/strategy status wording.
- Drift risk: Medium, because implemented/gated release wording appears in several canonical docs.

## 9. Doc distillation check

- Creates process artifacts: yes; run distillation and mark handoffs safe to delete.
- Adds design/architecture docs: no.
- Doc drift risk: Medium.

## 10. Philosophy and killer workflow

- Preserves minimalism: YES.
- Avoids hidden behavior: YES.
- Keeps semantics out of host: YES.
- Aligns with pattern-matching-first: YES.
- Killer workflow: Yes. It directly proves deterministic configuration, Outcome-aware record validation, clean output, diagnostics, and protected outbound data in one application pipeline.

## 11. Prompt plan

Preflight → Contract → Design → Failing Test → Implementation → Docs → Audit → Distillation, with phase commits and no pause absent a concrete blocker.

## Final GO / NO-GO

GO. Dependencies and contract direction are resolved; no behavior decision is missing.
