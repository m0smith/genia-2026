# GENIA Change Pre-Flight: Python/C++ host parity CI gate

## Change identity

- **Change name:** Python/C++ host parity CI gate
- **Release / issue:** R26 infrastructure follow-up; issue to be assigned when the
  pre-flight is copied to GitHub (the local environment has no authenticated
  GitHub CLI session)
- **Proposed branch:** `ci/host-parity-gate`
- **Owner:** repository maintainer / implementation agent

## 1. Scope lock

**Includes:**

- Reuse the R16 generic subprocess runner to execute the canonical shared specs
  against both the Python protocol adapter and the production C++ adapter.
- Add one required, readable CI parity result.
- Record temporary host gaps explicitly and fail when the observed gap set
  differs from that record.
- Document the matching local command.

**Excludes:**

- Language, parser, Core IR, runtime, protocol, or capability semantics.
- A new conformance runner/evidence format, broad CI redesign, C++ source
  changes, or claims of Python/C++ feature parity.

## 2. Source of truth

- **Authoritative `GENIA_STATE.md` sections:** opening R16 and R24/R25 status;
  no semantic text changes are expected.
- **Relevant `GENIA_RULES.md` sections:** Host Integration Boundary and
  Portability Boundary.
- **Additional relevant docs/contracts:** `spec/manifest.json`,
  `docs/architecture/executable-semantic-conformance.md`,
  `docs/design/r16-multi-host-conformance-infrastructure-contract.md`, and
  `tools/spec_runner/README.md`.
- **Conflicts or ambiguities:** none. The existing Docker workflow proves C++
  conformance only when Docker-environment paths trigger it; it is not the
  repository's always-visible semantic parity gate.

## 3. Feature maturity

- [ ] Experimental
- [x] Partial
- [ ] Stable
- [ ] N/A — process/docs-only

**Required wording / impact:** the gate proves only applicable shared cases;
documented unsupported cases remain gaps, never passes.

## 4. Contract vs implementation

- **Portable contract:** unchanged; canonical shared YAML in `spec/`, selected
  by each case's existing `requires` capabilities.
- **Python today:** full-language reference adapter speaks R16 protocol.
- **C++ today:** bounded R24/R25 production host in `m0smith/genia-cpp` speaks
  the same protocol and explicitly reports unsupported capabilities/cases.
- **Not implemented:** capability surfaces the C++ adapter reports unsupported;
  those gaps will be checked against a repository-owned allowlist with reasons.

## 5. Test strategy

- **Core invariants:** both hosts use the same checkout, discovery, protocol,
  applicability, comparison, and evidence machinery; failures cannot be
  converted into gaps; gaps must be named and justified.
- **Expected behavior:** CI reports Python and C++ pass/fail plus the exact
  documented C++ unsupported case set.
- **Failure cases:** either host has fail/protocol-error/crash/timeout/invalid;
  either host's advertised capability-gap set changes without an intentional
  manifest update; malformed/missing evidence.
- **Shared approach:** execute the existing full shared spec inventory through
  `python -m tools.spec_runner --host ...` for each host.
- **Host-specific approach:** build `m0smith/genia-cpp` and invoke its adapter;
  no host-specific semantic test is added here.

## 6. Examples

- **Minimal example:** one parity command accepts Python and C++ adapter
  commands and prints an explicit result for each host.
- **Realistic example:** CI checks out and builds `genia-cpp`, then runs the
  parity command over the complete discovered shared suite.
- **Classification:** process/infrastructure only.

## 7. Complexity check

- [x] Adding necessary complexity
- [x] Revealing existing structure
- [ ] No implementation complexity — process/docs-only

**Justification:** a thin orchestrator and gap file are the minimum needed to
turn two independent runner invocations into one enforceable parity result.
Shell-only duplication or count-only checks would not identify gap drift.

## 8. Cross-file impact

**Likely surfaces:** `.github/workflows/ci.yml`, `tools/`, focused tests, one
machine-readable known-gap file, and local-run documentation.

**Drift risk:**

- [ ] Low
- [x] Medium
- [ ] High

**Synchronization:** no STATE/RULES/book/cheatsheet/spec semantic update;
README/spec-runner documentation only. CI and focused unit tests must agree on
the manifest/report contract.

## 9. Philosophy check

- **Preserves minimalism:** YES
- **Avoids hidden behavior:** YES
- **Keeps semantics out of host adapters:** YES
- **Aligns with pattern-matching-first design:** N/A
- **Strengthens the validated-pipeline priority or has an approved reason not
  to:** YES — it protects shared semantics, including pipeline specs, across
  production hosts.

## 10. Prompt plan

- [x] Pre-flight
- [ ] Contract
- [ ] Design
- [x] Failing tests
- [x] Implementation
- [x] Documentation
- [x] Audit
- [ ] Distillation

**Order / rationale:** commit this pre-flight before code. No language contract
or design phase is needed because R16 already defines the reused protocol,
runner, capability, and evidence architecture. Add focused failing tests, then
the thin orchestration/CI implementation, documentation, and audit. No
distillation is needed for this small infrastructure change.

## 11. Host Parity / Conformance

**Affected hosts:**

- [x] Python
- [x] C++
- [ ] Other / future

**Does this change portable semantics?** NO

- **Shared tests involved:** every discovered shared YAML case under `spec/`,
  with applicability determined by existing `requires` metadata and
  `spec/manifest.json` capabilities.
- **Host changes:** no evaluator/runtime change in either host; only both
  existing adapters are invoked by the new gate.
- **Cross-host verification:** required in the new CI job.
- **Known host gaps:** C++ unsupported cases and the Python protocol's
  fixture/debug-stdio exclusions are explicit in the checked gap manifest with
  reasons; neither is counted as a pass.
- **Can one host merge before the other?** NO for a portable semantic change;
  this change itself has no semantic implementation.

## 12. Final GO / NO-GO

**Ready to proceed?** GO

**Missing decisions/evidence/dependencies:** GitHub issue number is unavailable
in this unauthenticated environment. CI can check out `m0smith/genia-cpp`; local
end-to-end validation requires a neighboring C++ checkout and toolchain.

**Reviewer / decision date:** implementation agent, 2026-09-25.
