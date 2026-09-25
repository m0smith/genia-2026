---
name: GENIA Change Pre-Flight
about: Complete the required intake gate before eligible R26+ work begins
title: "[Pre-Flight] "
labels: "pre-flight"
assignees: ""
---

<!-- Complete every applicable field before implementation. Use "N/A" with a
short reason rather than deleting a field. If this pre-flight cannot be
completed, the change is not ready to implement. -->

# GENIA Change Pre-Flight

## Change identity

- **Change name:**
- **Release / issue:**
- **Proposed branch:**
- **Owner:**

## 1. Scope lock

**Includes:**
-

**Excludes:**
-

## 2. Source of truth

- **Authoritative `GENIA_STATE.md` section(s):**
- **Relevant `GENIA_RULES.md` section(s):**
- **Additional relevant docs/contracts:**
- **Conflicts or ambiguities to resolve before proceeding:**

## 3. Feature maturity

- [ ] Experimental
- [ ] Partial
- [ ] Stable
- [ ] N/A — process/docs-only

**Required documentation wording / maturity impact:**
-

## 4. Contract vs implementation

- **Portable contract:**
- **Python implementation today:**
- **C++ implementation today:**
- **Not implemented:**

## 5. Test strategy

- **Core invariants:**
- **Expected behavior:**
- **Failure cases:**
- **Shared spec/conformance approach:**
- **Host-specific test approach:**

## 6. Examples

- **Minimal example:**
- **Realistic example:**
- **Classification (portable / host-only / process-only):**

## 7. Complexity check

- [ ] Adding necessary complexity
- [ ] Revealing existing structure
- [ ] No implementation complexity — process/docs-only

**Justification and simpler alternatives considered:**
-

## 8. Cross-file impact

**Files or surfaces likely to change:**
-

**Drift risk:**
- [ ] Low
- [ ] Medium
- [ ] High

**Required synchronization (STATE, RULES, book, cheatsheets, specs, hosts, generated docs):**
-

## 9. Philosophy check

- **Preserves minimalism:** YES / NO / N/A
- **Avoids hidden behavior:** YES / NO / N/A
- **Keeps semantics out of host adapters:** YES / NO / N/A
- **Aligns with pattern-matching-first design:** YES / NO / N/A
- **Strengthens the Outcome-aware validated-data-pipeline priority, or has an approved reason not to:** YES / NO / N/A

**Notes:**
-

## 10. Prompt plan

<!-- Select only the phases this change requires; explain skipped phases. -->

- [ ] Pre-flight
- [ ] Contract
- [ ] Design
- [ ] Failing tests
- [ ] Implementation
- [ ] Documentation
- [ ] Audit
- [ ] Distillation

**Phase order, issue split, and skipped-phase rationale:**
-

## 11. Host Parity / Conformance

**Affected hosts:**
- [ ] Python
- [ ] C++
- [ ] Other / future

**Does this change portable semantics?** YES / NO

**If YES:**
- **Spec/conformance tests added or updated:**
- **Python implementation updated:**
- **C++ implementation updated:**
- **Cross-host behavior verified:**
- **Known host gaps documented:**

**Can one host merge before the other?** YES / NO

**If YES, temporary compatibility note:**
-

<!-- Portable semantic changes must land first as shared contract/conformance
changes. Python and C++ must then both implement the change, or the temporary
host gap must be explicit and documented before merge. -->

## 12. Final GO / NO-GO

**Ready to proceed?** GO / NO-GO

**Missing decisions, evidence, or dependencies:**
-

**Reviewer / decision date:**
-
