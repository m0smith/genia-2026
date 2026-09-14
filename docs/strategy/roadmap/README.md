# Roadmap File Layout

`docs/strategy/release-roadmap.md` is the canonical roadmap entrypoint.

Use the focused files in this directory for edits:

- `r15.md` — completed R15 detail
- `r16-r20.md` — completed portability foundations through Open Functions
- `r21-r24.md` — planned exact numeric decomposition and C++ minimal host
- `r25-r29.md` — planned C++ expansion, MCP, and Sheet record pipelines
- `r30-r32.md` — planned shaped data, relational, database, tooling, and performance releases R30–R34 (historical filename retained)
- `r35-r37.md` — planned portable storage/resource semantics, location-independent execution, and Genia-native conformance tooling
- `sequence.md` — cross-release ordering and dependencies
- `parking-lot.md` — deferred ideas and historical issue disposition

`archive/release-roadmap-pre-split.md` is the exact monolithic roadmap snapshot from main immediately after PR #738 merged. It exists only to preserve historical wording during and after the split. Do not edit it as the live roadmap and do not use it to override `GENIA_STATE.md` or the focused current roadmap files.
