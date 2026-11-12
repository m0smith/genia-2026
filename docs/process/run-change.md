# Running a Genia Change

Starting with R26, complete the
[GENIA Change Pre-Flight issue template](../../.github/ISSUE_TEMPLATE/genia-change-preflight.md)
before implementation for new release work, semantic or language changes,
runtime or host behavior changes, conformance/spec changes, and multi-file
changes. Small typo or documentation-only fixes may skip it only when they have
no semantic, host, conformance, or process impact. If the pre-flight cannot be
completed, the work is not ready to implement. This is a project process
control, not Genia runtime behavior, and does not apply retroactively to closed
releases through R25.

## Risk-based gates

Classify the **semantic decision** separately from **execution of an already approved contract**. New language semantics, Core IR, cross-host observable behavior, concurrency, protected data and security boundaries remain high-risk even when the patch is small. An approved high-risk contract may be implemented as a medium-risk bounded slice. Promote the tier and STOP for new semantic decisions, scope growth, unforeseen failures or unapproved host gaps.

- **High risk (unsettled contract):** issue branch and R26+ pre-flight with all seven portability fields; separate contract/design acceptance; executable semantic conformance when applicable; independently reviewable failing tests and implementation; docs sync, independent audit and all host/CI/release gates. Do not combine a new semantic decision with execution.
- **Medium risk (approved bounded slice):** one explicit maintainer authorization may cover sequential committed RED, observed failure, GREEN implementation citing RED SHA, focused docs/checks and one independent final review. Preserve independently auditable test and implementation commits. One consolidated, verified top-level issue comment records exact candidate SHA/tree, RED/GREEN evidence, tests, docs, portability and reviewer verdict; no interim approvals or microphase handoffs are needed inside that authorized slice. FAIL blocks merge and requires corrective work with fresh review.
- **Low risk (nonsemantic):** concise prompt, targeted checks and normal PR review; issue handoff only when issue-tracked. Promote immediately if behavior or conformance impact appears.

High-risk pre-flight obligations remain: Python/C++ applicability; shared semantic authority and tests through the existing manifest/capability system; issue-backed host gaps and removal conditions; the MCP language-knowledge impact (does the change affect what an MCP client should know about Genia via `genia_language_profile`? If yes, the same change updates STATE, the `mcp_language_profile` registry in `docs/contract/semantic_facts.json` and the generated block in `apps/mcp/mcp.genia` via `tools/gen_mcp_language_profile.py`; if no, record why); truthful implemented-state docs; and applicable shared conformance. Do not add a parallel runner, registry, capability vocabulary or host-specific semantic authority. Review the pre-flight template and executable semantic conformance guide before such work.

Before each authorized phase/slice, read relevant GitHub issue decisions, accepted handoffs and exact commit evidence. Keep RED observations and failed evidence; a consolidated handoff is not a license to overwrite history. External CI, full regression, host parity and release gates apply whenever otherwise required. The independent reviewer must inspect the actual diff and not be the implementation author. Comments do not supersede GENIA_STATE.md, contract/spec or commits.

**Transition:** This policy is prospective after issue #1321's process PR merges. #1250 RED-C/GREEN-C still needs an explicit issue-specific authorization. No implicit merge, issue closure or R29 authorization.

## Full regression in socket-restricted environments

Run both partitions on the first attempt:

```
uv run pytest -n auto -q -m "not loopback"
uv run pytest -n auto -q -m loopback
```

The second command requires local loopback socket permission. The two commands
together are equivalent to ordinary full-suite selection; neither partition
alone is full regression. Do not automatically skip loopback tests when socket
permission is unavailable.

## Resource envelope for external-host verification

Record CPU quota, available memory and competing work when investigating a
request timeout. Schedule compilation, documentation builds and semantic host
verification sequentially in a resource-limited workspace. Choose and record
`--host-jobs` for that envelope (for example, `--host-jobs 2` under a two-CPU
quota); concurrency does not change case discovery, expected results, the
default 10-second request deadline or outcome classification. A finite green
run does not prove determinism or explain an earlier timeout. Retain failures,
label diagnostic versus acceptance runs and do not repeat failures to replace
their outcomes with PASS.
