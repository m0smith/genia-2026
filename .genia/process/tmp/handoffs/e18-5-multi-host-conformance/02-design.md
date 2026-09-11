# E18-5 Multi-host Equality Conformance Hardening — Design

ISSUE: #795
STATUS: design

Translates the E18-5 contract into structure. Adds no behavior.

---

## 1. NEW SHARED CASES — filling the §3 gaps only

Four cases, each chosen because a plausible host implementation gets it wrong and
nothing currently detects that:

### `r18-conformance-represented-and-pair-structure.yaml`

Represented-value equality (facet identity plus carried value, ordered layers)
and Pair equality, including Pair-vs-List kind separation.

*Why a host gets this wrong:* the obvious implementation compares a represented
value to its carried value, or represents a Pair as a two-element list.

### `r18-conformance-sheet-structural-equality.yaml`

Sheet equality by ordered semantic columns and cell values, with the cell-level
int/float bridge and column order mattering.

*Why a host gets this wrong:* comparing Sheets by identity, or treating columns
as an unordered set.

### `r18-conformance-protected-in-containers-and-patterns.yaml`

Protected carriers as map values and through duplicate pattern bindings, using
the equal-payload / different-payload pair construction so the case fails any
host whose pattern surface can distinguish them.

*Why a host gets this wrong:* implementing carrier identity in `==` but leaving
pattern binding on host equality — precisely the partial implementation #794
found in this host.

### `r18-conformance-cross-family-summary.yaml`

One case comparing a representative value of every source-reachable family
against itself and against a near-miss, in a single program.

*Why:* it is the case a host implementer runs first. A single failing index
localizes the broken family immediately, instead of requiring a hunt across
twenty files.

All four declare no `requires:`, so they are always applicable.

---

## 2. PROTOCOL-PATH EVIDENCE

A new test in `tests/spec/` runs the full suite through the Python host's
subprocess protocol adapter (the same adapter `test_python_protocol_adapter_parity_762.py`
uses) and asserts, specifically for the R18 cases:

1. every R18 case resolves to `pass`
2. **zero** R18 cases resolve to `unsupported`, `protocol_error`, `crash`,
   `timeout`, or `invalid`

Point 2 is the substance. Asserting only an aggregate pass count would be
satisfied by a run that skipped every R18 case, which is the failure mode the
contract names.

The test derives the R18 case list from the spec directory by filename prefix
rather than hard-coding it, so a future R18 case is covered automatically and
cannot be silently omitted from the conformance claim.

---

## 3. EXPECTED SOURCE CHANGES: NONE

The behavior is already implemented. The only non-test file expected to change is
the protocol parity case count.

If a new case fails, the contract's rule applies: fix the smallest necessary
implementation defect and document why. That outcome must be recorded explicitly
in the test-phase handoff, not folded silently into the diff.

---

## 4. FILE PLAN

New: four `spec/eval/r18-conformance-*.yaml`;
`tests/spec/test_r18_conformance_protocol_evidence_795.py`;
shared-spec wiring.

Modified: `tests/spec/test_python_protocol_adapter_parity_762.py` (case count).

---

## 5. TEST PLAN INPUT

Because this ticket asserts existing behavior, the usual "prove it fails first"
step is inverted: the evidence that these cases are *meaningful* is that each one
distinguishes the current implementation from a plausible wrong one. The
test-phase handoff records, per case, which wrong implementation it detects, and
confirms each passes on the base commit.

---

## 6. COMPLEXITY CHECK

- [x] Minimal

Four cases and one test. No new mechanism.

---

## 7. FINAL CHECK

- matches contract exactly: YES
- no behavior added: YES
- no new capability, category, or protocol change: YES
- opaque-token absence preserved deliberately: YES

**GO for the E18-5 evidence phase.**
