# Provider Composition Architecture Track

Status: **Architecture/preflight track — non-authoritative, not a numbered release, and not implementation authority.**

`GENIA_STATE.md` remains final authority for implemented behavior.

This file exists only to make the provider-composition investigation discoverable from the roadmap area while the architecture is evaluated methodically.

The evidence baseline and ordered work ledger live at:

- [`../../analysis/provider-composition-stage0.md`](../../analysis/provider-composition-stage0.md)

The P0/P1/P2/P5/P6/P7 architecture decision records live at:

- [`../../analysis/provider-composition-preflight.md`](../../analysis/provider-composition-preflight.md)

Current conclusion:

> Genia already has substantial audited provider architecture in R11, R12, R14, R16, and R18. The P0/P1/P2/P5/P6/P7 architecture pass found: no new whole-program requires/provides concept is justified (ordinary explicit arguments suffice); the smallest viable resource model is scope-owned with no distinct "borrowed" state, pending validation by R35/R36; interface identity is a nominal name plus exact revision, with SemVer treated only as a non-authoritative human suggestion; same-process provider calls stay ordinary Outcome-only, with R36's planned `ExecutionResult` remaining the sole outer execution envelope; and explicit provider composition needs no binding table or new construct — ordinary explicit values/factories are sufficient. Overall verdict: **small generalization**, not a new component subsystem. P3/P4/P8/P9 remain open.

WIT/WebAssembly Component Model is a comparison and interoperability target, not the semantic authority for this work.

## Current work order

The Stage 0 ledger defines P0 through P9. P0, P1, P2, P5, P6, and P7 are
resolved (P2 partially, pending R35/R36 validation) per the preflight
document above. P3 and P4 remain blocked on R22/R23 for their numeric
portion. P8 and P9 remain open, with P8's scope sharpened by the
preflight's synthesis section.

The track is relevant to planned R32, R35, R36, and R37, but this file does not change their numbering or scope. No new numbered provider-composition release is recommended: the architecture pass found no new runtime/language machinery that would warrant one. R24–R31 are not blocked by this track. R32's Database contract freeze, and R35/R36's own provider/resource contracts, should consume the preflight's P2/P5/P6/P7 models rather than inventing independent ones.
