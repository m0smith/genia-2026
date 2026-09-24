# R25 Release Truth Audit

Verdict: **PASS — release candidate ready for ordered merge.** R25 is not
declared merged-complete until the dependency chain in `docs/releases/R25.md`
lands; no PR was self-merged.

## Evidence reviewed

- Authority/evidence revision:
  `9ab0d3a323c9add045d47db1f476aead96af1e77`
- C++ completion/audit revision:
  `a0b70792a201903b5fb4c8515b0df723b1e1f74b`
- Protocol version `1`
- `762 total / 149 pass / 613 unsupported`
- `fail=0`, `protocol_error=0`, `crash=0`, `timeout=0`, `invalid=0`
- exact supported gates: `refs`, `cell_primitives`, `process_primitives`

## Skeptical result

The audit did not merely confirm the initial result. It found that the first
six shared cases failed to observe the contracted `none("nil")` return from
`cell_send` and `send`, while C++ returned placeholders. The defect was fixed
in C++ and a seventh host-neutral shared case was added; both Python and C++
pass it. Counts and release truth were then regenerated from the repaired
authority revision.

No Actor or ActorRef implementation, supervision, distribution, placement,
scheduler/fairness contract, timing threshold, thread identity, native
exception detail, alternate runner/protocol/evidence system, or R26 behavior
was found. Host-local sanitizer/stress results are described only as
implementation validation; portable claims remain tied to shared evidence.

The repository has no `docs/book/` tree, so there was no existing book surface
to update. Current-state, REPL, root README, capability registry/matrix, host
interop, roadmap, semantic-fact guardrail, release page, and MkDocs navigation
were all synchronized and validated.

## Conclusion

R25's bounded claims are supported and the candidate can merge only in the
recorded dependency order. Actor remains assigned to R38.
