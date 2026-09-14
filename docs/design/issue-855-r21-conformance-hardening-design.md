# Issue #855 Design — E21-3 R21 Cross-Surface Conformance and Compatibility Hardening

Status: process design artifact for issue #855.

## New test: `tests/spec/test_r21_conformance_protocol_evidence_855.py`

Mirrors `tests/spec/test_r18_conformance_protocol_evidence_795.py`'s
pattern exactly:

- `r21_specs()` discovers every spec whose `name` contains `"r21"`
  (substring, not prefix, since parse cases are named `parse-r21-...`/
  `parse-error-r21-...` and IR cases are named `r21-...`) across both the
  `parse` and `ir` categories — the two categories this ticket's shared
  evidence actually lives in per the R21 contract §5.
- `test_r21_cases_exist_and_span_the_expected_families()`: guards the
  count and names a representative case from each family (Integer,
  Decimal dotted/exponent/dot-exponent, equivalent spellings, huge
  Integer, malformed exponent, leading/trailing-dot rejection, unary
  negative, slash) so the suite cannot silently shrink.
- `test_every_r21_case_passes_in_process()`: executes every R21 spec via
  `execute_spec`/`compare_spec` directly.
- `test_every_r21_case_passes_through_the_generic_host_protocol()`:
  executes every R21 spec via `execute_spec_via_host` against
  `hosts.python.protocol_adapter`; any outcome other than `pass`
  (including `unsupported`) is a failure of the conformance claim,
  exactly like the R18 precedent.

## No implementation phase

The preflight audit sweep found zero remaining defect: #854 already
correctly threads the tagged payload through every `IrLiteral`/`float()`
consumer that exists in the codebase (evaluator, optimizer, lowering,
`ir_normalize.py`, `parse_adapter.py`, `protocol_adapter.py`,
`exec_eval.py`, and every `tools/spec_runner/*.py` module). There is
therefore no compatibility repair to make, and no `spec/manifest.json`
capability/version change is truthful (R21 adds no new capability, and
`core_ir_version` has no reader anywhere in the repository to justify a
bump). This is recorded as an explicit no-op implementation phase per
`docs/process/run-change.md`'s guidance to preserve the process boundary
with a named empty-phase commit rather than skip it silently.

## Evidence

`uv run pytest tests/spec/test_r21_conformance_protocol_evidence_855.py`,
plus a full regression re-run, confirm no regression and that the new
durable evidence file passes end to end.
