# Issue #855 Audit — E21-3 R21 Cross-Surface Conformance and Compatibility Hardening

Status: durable audit evidence for issue #855 (E21-3). Not a
source-of-truth document; `GENIA_STATE.md` remains final authority.

## Acceptance criteria verification

| Criterion | Result |
|---|---|
| all R21 source/IR obligations have shared host-neutral evidence | PASS — 18 named `spec/parse/*`/`spec/ir/*` cases from #853/#854, explicitly enumerated and guarded by `test_r21_cases_exist_and_span_the_expected_families` |
| applicable in-process and subprocess cases agree | PASS — `test_every_r21_case_passes_in_process` and `test_every_r21_case_passes_through_the_generic_host_protocol` both pass; no case is `unsupported`/`crash`/`timeout`/`protocol_error` |
| no parse/lowering/normalization path introduces host binary floating point for Decimal source | PASS — reconfirmed by the preflight audit sweep (no new code this ticket; #853/#854's own `float()`-isolation tests still pass) |
| existing single-file/shared-spec behavior outside R21 remains green | PASS — `uv run python -m tools.spec_runner` → `total=721 passed=721 failed=0 invalid=0`; full regression below |
| every compatibility change can be explained solely from the R21 contract | PASS vacuously — the preflight audit sweep found zero compatibility defect requiring a change; nothing was changed that isn't already covered by #853/#854's own audits |
| no R22/R23 semantic behavior is introduced | PASS — zero production code touched by this ticket |

## Preflight audit sweep (repeated at audit time for currency)

Re-ran the grep sweep from the preflight against the current branch tip:
every `IrLiteral` construction/consumption site and every `float(` call
reachable from numeric-literal handling across `src/genia/*.py`,
`hosts/python/*.py`, and `tools/spec_runner/*.py` is unchanged from #854's
already-audited state. No new site was introduced or missed.

## Explicit no-op phase decisions

- **Implementation phase**: no code change. The preflight/design docs
  record why (zero defect found); this audit reconfirms it by re-running
  the sweep and the full regression suite with zero new failures.
- **Documentation phase**: no `GENIA_STATE.md`/`GENIA_RULES.md`/
  `GENIA_REPL_README.md`/`README.md` change. No implemented behavior
  changed, so there is nothing new to truthfully describe; #853's and
  #854's documentation already fully describes the landed boundary this
  ticket proves. Manufacturing a doc edit here would violate the "avoid
  absolute claims without evidence" / no-churn guidance.
- **`spec/manifest.json`**: no change. R21 adds no new capability;
  `core_ir_version` has no reader anywhere in the repository to justify a
  bump (preflight finding, reconfirmed).

## Regression evidence

- `uv run pytest tests/spec/test_r21_conformance_protocol_evidence_855.py -q` → 3 passed
- `uv run python -m tools.spec_runner` → `Summary: total=721 passed=721 failed=0 invalid=0`
- `uv run pytest -n auto -q -m "not loopback"` → 4377 passed, 10 failed; identical pre-existing baseline set tracked in issue #859 (same count and identity as #853/#854's audits — zero new failures)
- `uv run pytest -n auto -q -m loopback` → 26 passed, 0 failed

## Verdict

**PASS.** The audit found the R21 source/Core-IR boundary already fully
compatible across every existing consumer, with no defect requiring
repair inside or outside the R21 boundary. The hard stop rule was never
triggered — no R22/R23 dependency was uncovered. This ticket's durable
contribution is the new `tests/spec/test_r21_conformance_protocol_evidence_855.py`
proving in-process/subprocess agreement specifically and durably, closing
the gap between an incidental aggregate pass count and an explicit,
named conformance claim.

## Doc Distillation

No documentation was added or changed by this ticket (see "Explicit no-op
phase decisions" above), so there is nothing to distill. Process artifacts
(preflight/contract/design) remain under `docs/analysis/` and
`docs/design/` as durable history, matching #853/#854's precedent.
