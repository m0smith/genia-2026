# Provider Composition Architecture Track

Status: **Architecture/preflight track — non-authoritative, not a numbered release, and not implementation authority.**

`GENIA_STATE.md` remains final authority for implemented behavior.

This file exists only to make the provider-composition investigation discoverable from the roadmap area while the architecture is evaluated methodically.

The evidence baseline and ordered work ledger live at:

- [`../../analysis/provider-composition-stage0.md`](../../analysis/provider-composition-stage0.md)

Current conclusion:

> Genia already has substantial audited provider architecture in R11, R12, R14, R16, and R18. The open work is to determine whether and how to generalize that foundation into whole-program requires/provides semantics, owned/borrowed resources, one canonical cross-language provider boundary, and coherent provider-vs-execution failure layering.

WIT/WebAssembly Component Model is a comparison and interoperability target, not the semantic authority for this work.

## Current work order

The Stage 0 ledger defines P0 through P9. Work starts with P0 and must proceed through explicit architecture decisions before any implementation tickets are created.

The track is relevant to planned R32, R35, R36, and R37, but this file does not change their numbering or scope. If the preflight later justifies promotion, the normal roadmap/ticketing process must decide whether the result becomes a dedicated release, a prerequisite slice of an existing release, infrastructure, or remains parked.
