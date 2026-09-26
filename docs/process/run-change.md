# Running a Genia Change

Starting with R26, complete the
[GENIA Change Pre-Flight issue template](../../.github/ISSUE_TEMPLATE/genia-change-preflight.md)
before implementation for new release work, semantic or language changes,
runtime or host behavior changes, conformance/spec changes, and multi-file
changes. Small typo or documentation-only fixes may skip it only when they have
no semantic, host, conformance, or process impact. If the pre-flight cannot be
completed, the work is not ready to implement. This is a project process
control, not Genia runtime behavior, and does not apply retroactively to closed
releases through R25.

For work requiring pre-flight:

1. Create branch: `issue-<number>-<short-name>`
2. Run preflight prompt
   - Pre-flight must include a completed PORTABILITY ANALYSIS block (section 3a).
   - All seven portability fields must be answered before the contract phase begins.
   - Incomplete portability analysis is grounds for blocking the contract step.
   - If the change adds or changes portable observable behavior, complete the
     executable semantic conformance obligation from
     `docs/architecture/executable-semantic-conformance.md` before the contract
     phase:
     1. identify the portable authority and representation/boundary;
     2. identify the shared executable spec evidence (or explicitly justify why
        shared evidence is impossible without claiming unproved cross-host
        conformance);
     3. identify applicability using the existing `spec/manifest.json`
        capability vocabulary, adding a capability only for a genuinely new,
        independently claimable host surface;
     4. identify the host capability claim/evidence impact;
     5. identify implemented-truth documentation that must be synchronized
        after implementation and verification.
   - If an implementing host must inspect another host's implementation source
     to determine observable Genia semantics, stop. Clarify the authoritative
     contract and add or repair shared evidence before host implementation
     resumes.
   - This obligation reuses R16. Do not create a parallel runner, protocol,
     evidence format, capability registry/profile system, semantic manifest, or
     Core IR mechanism merely to satisfy this process gate.
   - Identify whether Python, C++, or both are affected. A semantic change must
     land first as shared contract/conformance work; then both hosts must
     implement it, or a temporary host gap must be documented before merge.
     Add or update shared spec/conformance tests wherever applicable.
   - Every temporary host gap recorded in `spec/known_host_gaps.json` must have
     a GitHub issue reference, short reason, affected host, affected tests or
     spec area, and removal condition. Do not add unowned skip-list entries.
3. Commit preflight
4. Run contract prompt
5. Commit contract
6. Run design prompt
7. Commit design
8. Run failing-test prompt
9. Commit failing tests
10. Run implementation prompt
11. Commit implementation
12. Run docs prompt
13. Commit docs
14. Run audit prompt
15. Commit audit or audit fixes
16. Run the Doc Distillation prompt
17. Commit the updated docs

Do not merge until audit passes.

## Full regression in socket-restricted environments

Run both partitions on the first attempt:

```
uv run pytest -n auto -q -m "not loopback"
uv run pytest -n auto -q -m loopback
```

The second command requires local loopback socket permission. The two commands
together are equivalent to ordinary full-suite selection; neither partition
alone is full regression. Do not automatically skip loopback tests when socket
permission is unavailable.
