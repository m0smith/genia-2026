# Independent behavioral/documentation truth audit handoff

Historical pre-audit handoff. The independent verdict at `c14fa139` is now
**PASS WITH NON-BLOCKING FINDINGS**, superseding the earlier FAIL; see
`07-audit.md` and `08-distillation.md` for the final decision and closeout.
Earlier pinned counts below remain historical observations.

PR: https://github.com/m0smith/genia-2026/pull/1260 . Branch: `issue-1250-slice-a`.
Issue #1250 remains open. Scope is Slice A only. This document prepares an
independent audit; Codex has not performed or certified that audit.

## Authority and exact review target

Read latest `AGENTS.md`, then `GENIA_STATE.md`, `GENIA_RULES.md`,
`GENIA_REPL_README.md`, `README.md`; approved #1255 contract (merge
`a4730906a37450ae15aa2b595c69a1e9aa061e67`); merged #1259 design (base
`d85a56fa66d3369806ab9951b7572c79db98eba3`); `docs/process/run-change.md` and
`docs/process/code-maintainability-review.md`. Contract/design describe future
B–E behavior, not current execution support.

Original implemented/reviewed head: `45a1def273810132d1cb9fd0dea13f9c9de002d1`.
Original phase SHAs and implementation/RED evidence are preserved in
`.genia/process/issue-1250-slice-a-claude-handoff.md` and its referenced artifacts.
All eight closeout SHAs, RED results, owners and N1–N9 dispositions are in
`maintainability-closeout.md` beside this file. Last source/truth-doc target:
`08a92c010ccef8b95fd67022622d41356bd1a749`. Later commits in this handoff series
contain process evidence only. Audit the exact PR head containing the handoff,
not merely the earlier Claude range. Resolve the final artifact commit SHA from
PR/git history; a document cannot contain its own eventual commit SHA.

## What changed and what must remain true

- N1 restores the historical parser treatment of ordinary dotted target tokens:
  literal binding names, not property writes. Ordinary function `=`, arrow and
  block spellings retain their lowering. New dotted `=:` and pattern/guard
  targets still reject; no new R20 grammar or Model B execution is introduced.
- N2 makes direct entry-file route/config/CORS discovery preflight the entire
  input list before reading values or metadata. All three new declaration
  families reject even without annotations. The evaluator separately rejects
  each new declaration before its children; earlier ordinary source effects may
  already exist. No submission rollback is implied.
- N3 tests the conservative Slice A walker already in place. Collection-nested
  calls count, inert quote does not, and an extra recursive arm prevents the
  nth rewrite from discarding its list/map result. Canonical nth remains eligible.
- New nodes remain explicit portable carriers; legacy `IrFuncDef` normalization
  and existing context omission remain unchanged. No wire/protocol/Core IR
  version, capability vocabulary or optional-capability claims changed.
- The four root documents and relevant book reference explain historical target
  compatibility. STATE records direct discovery and optimizer eligibility.
  STATE condensation preserves its ratified word budget and the exact existing
  MCP evidence fragment. Registry/profile/golden and generated references are
  checked without unnecessary rewrites.

## Independent scrutiny requested

Inspect the entire actual diff from `d85a56fa` plus the correction delta from
`45a1def2`, adjacent consumers and current shared evidence. Do not infer truth
from a green summary. In particular check ordinary binding-name behavior versus
named access, all declaration target restrictions, annotations and group
ownership, malformed direct IR and recursive child traversal, wire stability,
REPL grouping/completeness, effect timing, native/server discovery, and optimizer
result preservation.

Compare each implemented claim in the four roots, book, portable IR document,
host matrix, semantic-fact registry, generated MCP profile and references with
source/tests. Do not treat accepted syntax as executable Model B. B–E immutable
write policy, default-open dispatch, cross-module linking and closed publication
remain unsupported. Existing ordinary and explicit R20 behavior must remain.

## C++ limitation and reporting decision

Read `.genia/process/issue-1250-slice-a-cpp-evidence.md` in full. Initial evidence
used source `87204407543f2b175c6b185bdc7e625edeb19251`, contract revision
`9ab0d3a323c9add045d47db1f476aead96af1e77`: 2 PASS / 27 UNSUPPORTED.
Closeout uses the unmodified available source checkout
`bb7c7474001f18e2e27fd94b7be9e9b725ba3473` and an existing binary advertising
`6402e668ae85a1e7efe94b3ac3d51f233b730ca4`: 5 PASS / 33 UNSUPPORTED across
38 selected cases. Exact paths, binary hash and ownership/removal conditions are
in that ledger. No C++ implementation or full current-pinned conformance is
claimed. Both advertised revisions are ancestors, not the current audit target;
the binary's advertised contract pin does not independently certify its source
build provenance. UNSUPPORTED is never PASS, including negative diagnostics.

N9 reporting uses the existing evidence ledger and durable host matrix because
`spec/known_host_gaps.json` permits optional-capability gaps only. Required parser
and lowering obligations stay required and unmet cases remain visible. A green
optional-capability host-parity workflow does not manufacture required-syntax
parity. #1250 owns the C++ implementation boundary until affected cases pass at
a current contract pin.

## Remaining risks and boundaries

N4 centralized/reflective validation debt, N5 prelude/documentation consumer
readiness, N6 diagnostic quality, N7 unused helpers and N8 transitional timing
are accepted, scoped #1250 dependencies with named implementation/integration
owners and completion conditions in the maintainability closeout. This handoff
does not silently clear them. Do not adopt Model B declarations in shipped
prelude code before the N5 inventory/documentation obligations are resolved.

Use `verification.md` beside this file for exact commands, outcomes, old failed
runs, post-fix reruns, CI commit scope and unsupported cases. Local runs use
Python 3.12; CI uses Python 3.14. Full regression means both partitions, not a
focused suite or an isolated flaky-test rerun. Preserve distinctions among a
completed failed run, a corrected affected rerun, skipped tests and pending CI.

Do not merge PR #1260, close #1250, start Slice B, or substitute this implementer
handoff for the required independent audit and later distillation gates.


## Final verification limits to carry into the audit

R16: 869/869; focused: 258 pass; final docs: 518 pass / 35 skip; final permitted
serial loopback: 31 pass. All six CI workflows passed at frozen source/truth-doc
head `08a92c01` (fast non-loopback 6958 pass / 63 skip; loopback 31 pass; R16
869/869). The local full non-loopback selection completed with 7026 pass /
63 skip / 22 fail: one corrected old STATE-size snapshot plus 21 MCP host
failures. A bounded permitted/cache-configured rerun recovered 20 of the 21;
the two-launch cleanup assertion still observes an unreaped zombie adopted by
PID 1 (`tail`). The identical case passed in CI. Preserve this local reaping
risk under #1250 / R28-H37 with m0smith as integration owner; do not ignore
zombies, relax assertions, or call the local full run a PASS. Raw evidence and
the diagnostic's unchanged assertion are in the packet. Audit readiness here
means the evidence is assembled for an independent reviewer, not that the
review has passed or these limitations have disappeared.
