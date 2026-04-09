# SICP with Genia

This section adapts SICP-style ideas to current Genia as executable learning artifacts.

If any SICP chapter disagrees with implemented behavior, `GENIA_STATE.md` remains the final authority.

## Status

✅ Published today:

- [01 Expressions and Processes](01-expressions-and-processes.md)

⚠️ Partial:

- only the opening SICP chapter is published in this phase
- coverage is intentionally incomplete and should expand only when chapters are implementation-truthful

❌ Not published yet:

- later SICP chapters beyond chapter 1

## Validation

- runnable `genia` blocks in SICP chapters are validated by `tests/test_sicp_code_blocks.py`
- illustrative-only `genia` blocks must be marked exactly as described in `docs/sicp/AGENTS.MD`
- the published docs site stages `docs/sicp/` without moving the source files
