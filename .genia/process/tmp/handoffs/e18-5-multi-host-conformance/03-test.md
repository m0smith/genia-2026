# E18-5 Multi-host Equality Conformance Hardening — Evidence Phase

ISSUE: #795
STATUS: evidence added; **no source change required**

---

## Inverted proof obligation

This ticket asserts behavior that already exists, so "prove it fails first" does
not apply. The obligation instead is to show each case is **meaningful** — that
it distinguishes the current implementation from a plausible wrong one — and that
it passes on the base commit without any source change.

| Case | Wrong implementation it detects |
|---|---|
| `r18-conformance-represented-and-pair-structure` | a host that unwraps a represented value before comparing, ignores facet identity or layer order, or models a Pair as a two-element List |
| `r18-conformance-sheet-structural-equality` | a host that compares Sheets by runtime identity, treats columns as an unordered set, or skips the int/float bridge inside cells |
| `r18-conformance-protected-in-containers-and-patterns` | a host that implements carrier identity in `==` but leaves duplicate pattern bindings on host equality — exactly the partial implementation #794 found in this host |
| `r18-conformance-cross-family-summary` | any single broken family, named by a single failing index |

All four pass on the base commit. Measured before writing each expectation, so
the expected values are recorded behavior rather than guesses.

---

## Protocol-path evidence

`tests/spec/test_r18_conformance_protocol_evidence_795.py` → **3 passed**.

- `test_r18_cases_exist_and_span_the_expected_families` — guards against the
  suite silently shrinking, and names one required case per family.
- `test_every_r18_case_passes_in_process` — all R18 cases pass in-process.
- `test_every_r18_case_passes_through_the_generic_host_protocol` — all R18 cases
  pass through the R16 subprocess protocol, and **zero** resolve to
  `unsupported`, `protocol_error`, `crash`, or `timeout`.

The last assertion is the substance of the ticket. A run in which every R18 case
was declined would produce the same aggregate pass count as one in which they
were skipped; separating "executed and correct" from "not executed" is what makes
the conformance claim honest.

The R18 case list is derived by filename prefix, so a case added by a later
ticket is covered automatically and cannot be omitted from the claim.

---

## Full suite

`uv run python -m tools.spec_runner` → `total=668 passed=668 failed=0 invalid=0`.

Protocol parity count updated 664 → 668; `unsupported` stays 18, confirming none
of the four new cases needs an unexpressible fixture.

---

## Defects found

**None.** No source file changed under this ticket. The contract's defect rule
("fix the smallest necessary implementation defect and document why") was not
triggered, which is itself a meaningful result: E18-1 through E18-4 hold up
under independent, transport-level verification across every source-reachable
family.

---

## Unrelated pre-existing failures

Baseline on `main` @ `bd24214`: `-m "not loopback"` 2 failed / 4197 passed,
`-m loopback` 26 passed, shared specs 664/664, `ruff` clean.
