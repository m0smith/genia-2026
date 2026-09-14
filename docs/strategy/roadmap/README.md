# Roadmap File Layout

`docs/strategy/release-roadmap.md` is the canonical roadmap entrypoint.

Use the focused files in this directory for edits:

- `r15.md` — completed R15 detail
- `r16-r20.md` — completed R16-R20 portability/open-function foundations
- `r21-r24.md` — R21-R23 exact-numeric releases plus R24 C++ Minimal Conforming Host
- `r25-r29.md` — R25-R27 C++ expansion, R28 Genia MCP Server, and R29 Sheet Record Pipelines
- `r30-r32.md` — R30-R34 shaped-data, relational, database-boundary, tooling, and performance work; historical filename retained for link stability
- `r35-r37.md` — portable storage/resource semantics, location-independent Genia execution, and Genia-native conformance tooling
- `sequence.md` — cross-release ordering and dependencies
- `parking-lot.md` — deferred ideas and historical issue disposition

`archive/release-roadmap-pre-split.md` is the exact monolithic roadmap snapshot from main immediately after PR #738 merged. It exists only to preserve historical wording during and after the split. Do not edit it as the live roadmap and do not use it to override `GENIA_STATE.md` or the focused current roadmap files.
