# E18-5 Multi-host Equality Conformance Hardening — Audit

ISSUE: #795
BRANCH: `issue-795-multi-host-equality-conformance` (not `main`; matches change)

Audited skeptically, with the specific skepticism this ticket invites: an
evidence-only ticket can look successful while proving nothing.

---

## 1. SUMMARY

Status: **[x] PASS**

R18 now has 24 shared cases spanning every equality family reachable from Genia
source, verified both in-process and through the R16 generic host protocol, with
zero cases declined. No source file changed, and no defect was found.

---

## 2. THE SKEPTICAL QUESTION FOR AN EVIDENCE TICKET

*Could this ticket pass while proving nothing?* Three ways, each checked:

### (a) Cases that pass vacuously

A case asserting only things any implementation satisfies adds nothing. Each new
case was therefore justified against a **named wrong implementation** it detects,
recorded in the evidence handoff: unwrapping a represented value, modelling a
Pair as a List, comparing Sheets by identity, treating columns as unordered, and
— the one this host actually had before #794 — implementing carrier identity in
`==` while leaving pattern bindings on host equality.

The protected case goes further: it asserts the *agreement* of an equal-payload
pair with its different-payload twin, so it cannot be satisfied by a host that
merely returns plausible-looking individual answers.

### (b) Cases silently not executed

This is the failure mode the issue explicitly warns about, and it is the reason
the protocol test asserts `declined == []` rather than only a pass count. A run
that skipped every R18 case would produce an identical aggregate. Verified that
all 24 cases resolve to `pass` through the subprocess protocol, with zero
`unsupported`, `protocol_error`, `crash`, or `timeout`.

Cross-checked independently: the full-suite `unsupported` count stayed at 18
across the 664 → 668 growth, confirming none of the four new cases fell into the
unexpressible-fixture bucket.

### (c) The suite silently shrinking later

Guarded by `test_r18_cases_exist_and_span_the_expected_families`, which asserts a
minimum count and names one required case per family. Deleting a case now fails a
test rather than quietly narrowing the conformance claim.

The R18 case list is derived by filename prefix, so a case added by a later
ticket joins the protocol-path claim automatically — the coverage cannot drift
open in either direction.

---

## 3. CORE CHECKS

### No semantics were added

Verified by diff: the only non-test, non-spec change is the protocol parity case
count. `src/` is untouched. This satisfies the ticket's central constraint, and
the fact that no defect surfaced is a real result — E18-1 through E18-4 hold up
under transport-level verification.

### Expected values are measured, not guessed

Each new case's expected output was measured from the running implementation
before being written into the YAML. Challenged as circular — "does that not just
assert whatever the code does?" — and resolved: circularity is broken by (a)
above, since each case was independently justified against a wrong
implementation it must reject. Measuring prevents a typo'd expectation from being
mistaken for a semantic finding.

### The opaque-token absence

Re-confirmed as required rather than missing. R18 exposes no way to mint or
observe a token from Genia source, so a shared case would have to introduce the
public token surface the approved contract excludes. This is now stated in the
pre-flight, the contract, the cross-family case's own notes, and the doc handoff,
so #796 and #797 cannot mistake it for a gap.

### Capability handling

The four new cases declare no `requires:`, so they belong to the base
required-capability set every conforming host implements by definition. No
capability, spec category, envelope field, or protocol change was made.
`spec/manifest.json` is untouched.

---

## 4. FUTURE-HOST CHECK

Could a C++ implementer determine conformance from the contract plus these cases?
Yes, for every source-reachable family, and the cross-family summary case gives
them a single first test whose failing index names the broken family.

The three partial implementations most likely in practice are each detected:
reusing host `==` (boolean/number separation), reusing a host hash map's key
rules (key equivalence, NaN rejection), and implementing `==` while leaving
patterns and assertions on host equality (surface agreement, protected through
patterns).

---

## 5. VALIDATION

- `tests/spec/test_r18_conformance_protocol_evidence_795.py`: 3 passed
- full shared spec suite: `total=668 passed=668 failed=0 invalid=0`
- documentation tests: 205 passed
- `uv run ruff check .`: clean
- full regression `-m "not loopback"`: **2 failed / 4200 passed** — exactly the
  two pre-existing root/`chmod 000` cases

---

## 6. VERDICT

**PASS.** Obligations still open for #797: confirm no source-reachable value
lands in the relation's unclassified identity terminal, and re-check the standing
constraint that a future structural Genia value must not be callable.
