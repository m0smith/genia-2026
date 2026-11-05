# R1–R5 documentation handoff

Codex, 2026-11-05 UTC. Documentation-only synchronization after corrected code and
host evidence `2da6d870bed443059eeb56f45709fd23a30b9ccd`, following TEST-ONLY RED
`9b87b220a5a9168f22087cecae748faa8a6def34`. Exact documentation SHA is the containing
commit and is published on #1285, avoiding a self-hash cycle.

Verified prior handoffs:
- [RED](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6658357008)
- [Implementation/host verification and separate disclosed self-review](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6658657164)

Updated non-authoritative design, recipe, acceptance checklist and gap G4. They
identify the prior Claude PASS-WITH-REVISIONS, corrected candidate and pending
independent delta gate. The recipe names uv --no-cache and explicit tmpfs or
same-future-RUN removal of cache/receipt/dedicated TMPDIR, including empty project
coordination locks. Target acceptance remains unchecked; host-only corrections
are separately recorded. No source/lock/pin/test/implementation bytes changed in
this documentation phase. No language or MCP knowledge impact.

The independent behavioral/documentation truth audit remains pending with the
requested Claude Code delta review. Codex inspected the actual committed source
diff/call sites in a distinct self-review: PASS WITH NON-BLOCKING FINDINGS, not
independent acceptance. R6/R7 debt is explicitly maintainer-owned on #1285.

`verification.json` records exact document hashes, existing local-link checks and
bash -n for fenced shell examples. It also verifies unchanged authoritative docs
and byte-identical strict OCI section. No shell recipe was executed. Changed-file
whitespace passes. The earlier raw RED log whitespace, setup failures, first
A/B failure and initial doc-lint error remain preserved with their original phase.

STOP before image/container construction/run/export, private benchmark work,
CI dispatch, merge, issue closure or R29. $0 incremental spending; usage/effort not
measured. Venue-neutral G3, G1 signed OS/Git/Tini closure, official CPython3.12.15
acceptance and strict two-independent-build OCI equality remain open.
