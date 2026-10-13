# F2 P1 execution authorization and evidence

Baseline: `9f0170d`; B red gate: `3695cb7862aed8438bd2dd88f6e61b03a0841804`.
The 2026-10-12 user execution handoff authorizes B–H TEST, implementation,
documentation, audit/distillation and focused PR publication without repeated
phase approval. Earlier pre-flight stop statements are historical. No self-merge,
auto-merge, issue closure, P2/P3 or F3–F5 work is authorized.

Design/contract: merged #1207, F2 P0 and #1211's four reviewed accessors.
This is the existing unnumbered R20 infrastructure follow-up before R29, not a
new release. Keep root as entry, module parentage/lookup unchanged, root-bound
reflection and debugger globals compatibility; never add an entry child/fallback.
Use explicit references for unit ownership, explicit host classes for injection,
and existing R10 trust/protection rules. Overlapping interpreter/builtins edits
are serialized; independent workers use isolated worktrees with named owners.

Portability analysis: (1) STATE remains implemented authority; (2) Python Env
and host-consumer/injection APIs, existing lexical runtime representation;
(3) Python internal tests plus retained R16 shared observable evidence;
(4) existing capability vocabulary, no new capability; (5) Python only, C++
bounded claims unchanged; (6) no new host gap/protocol/evidence format;
(7) STATE documents only verified host internals, relevant architecture notes
updated, book/cheatsheets reviewed for unchanged language examples, MCP facts
unchanged because no new language knowledge. New API red commits precede
implementation; behavior-preserving consumers retain characterization guards.

Verification: focused suites per slice; generated-reference/profile/documentation
and semantic-sync gates; integrated shared conformance and both full pytest
partitions at H. Compare failures with pristine main; preserve original outcomes
when reporting retries. Audit and evidence outside docs. P1 is prepared for
review only until required PRs are merged and integrated main is audited.

## P1-B

22 red cases at `3695cb7` become green with explicit inherited unit ownership;
runtime/entry/inspection remain root. Focused accessor + existing P1-A/module/
debugger/IO suite: 84 passed. No lookup/assignment algorithm or consumer changes.
