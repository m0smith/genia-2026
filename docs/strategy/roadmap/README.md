# Roadmap File Layout

`docs/strategy/release-roadmap.md` is the canonical roadmap entrypoint.

Use the focused files in this directory for edits:

- `r15.md` — active R15 detail
- `r16-r19.md` — planned portability infrastructure and minimal C++ host work
- `r20-r23.md` — planned C++ expansion and Sheet record pipeline work
- `sequence.md` — cross-release ordering and dependencies
- `parking-lot.md` — deferred ideas and historical issue disposition

`archive/release-roadmap-pre-split.md` is the exact monolithic roadmap snapshot from main immediately after PR #738 merged. It exists only to preserve historical wording during and after the split. Do not edit it as the live roadmap and do not use it to override `GENIA_STATE.md` or the focused current roadmap files.
