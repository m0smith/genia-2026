# Token-efficient agent workflow (pilot)

This policy reduces avoidable AI-token and review effort. It is **subordinate** to `AGENTS.md`, `GENIA_STATE.md`, the established pre-flight/change process, and all required semantic, host, conformance, independent-review, and release gates. It authorizes **no** skipped required phase, weak oracle, reclassified failure, undocumented behavior, or unsupported host claim.

## 1. Select the smallest sufficient work scope

- **Low risk:** isolated typo/prose changes without semantic, host, process, or conformance impact. Use a short prompt, inspect the diff, run relevant doc checks; follow existing documentation-only pre-flight exceptions where applicable.
- **Medium risk:** bounded implementation, tooling, or fixture updates. Follow the full applicable process; use one implementer and focused independent review required by that process.
- **High risk:** language/runtime/host behavior, cross-host contracts, security/protected data, Core IR, or release acceptance. Preserve complete pre-flight, contract, design, RED/GREEN, maintainability, docs, independent audit, distillation, and shared/host conformance obligations.

**Risk tier changes the amount of redundant investigation, not the required quality gates.** Promote the tier if scope or evidence changes.

## 2. Read with purpose

At the beginning of each task, consult the latest `AGENTS.md` and the four authority documents (`GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`) in the required precedence order. First inspect their navigation, relevant headings, anchors and rules; read the sections material to the change in full. Read the full document when needed to resolve a conflict or to satisfy an explicitly required full-document review. Never assume previously quoted excerpts are current. Treat issue summaries, generated references and agent handoffs as navigation, **not** semantic authority.

## 3. Reuse verified evidence without laundering it

- Link exact issue, commit/tree, command, environment, host pin, result and reviewer evidence instead of pasting large logs or repeating settled investigations.
- Begin with changed paths and affected cases; run additional focused regressions as justified.
- Complete **all full-suite, cross-host, CI, portability and release gates when the existing process requires them**, regardless of the incremental checks.
- Evidence is valid only for its recorded SHA, tree, host version and execution envelope. If the candidate changes, identify what must be rerun; do not call earlier green runs exact-head proof.
- Retain red runs, unsupported cases, timeouts and known gaps. Do not retry-to-green, silently reduce required coverage or raise deadlines to manufacture a pass.

## 4. Minimize agent and prompt overhead

- Prefer concise prompts naming the issue, objective, exact candidate, changed scope, mandatory instructions and stop condition. Link existing acceptance criteria rather than restating them.
- Default to **one implementer**. Add independent reviewers only to satisfy the project's process or when risk and uncertainty justify them; independence is never replaced by an implementer's self-report.
- Parallel agents only for non-overlapping worktrees and clearly separable tasks. Do not launch several agents to restate the same review.
- Store comprehensive findings, test artifacts and provenance in the relevant GitHub issue/PR. Return a short decision summary: outcome, actual blockers, evidence link and next action. Logs remain accessible, not suppressed.
- Prefer a lower-cost model for mechanical, well-bounded work when supported; use deeper reasoning for semantic uncertainty, architecture, root-cause analysis and independent skeptical audits. Model choice never relaxes acceptance criteria.

## 5. Optional OpenClaw coordination (experimental)

OpenClaw may coordinate Codex, Claude Code or other agents for Genia tasks, but **it is not installed, connected, proven or required by this policy**. Use the established standalone agent process when orchestration is unavailable or less efficient. OpenClaw must read and respect the same repository guidance; a coordinator is not a new semantic authority or approval gate.

When OpenClaw is available:

- **Single issue intake:** resolve the issue, current candidate SHA, relevant sections, scope/risk tier, acceptance gates and existing evidence once. Give each worker a small task-specific context and link the exact GitHub source; do not forward entire historical transcripts or repeated large documents by default.
- **Explicit delegation:** default to one implementer. Route independent review to a separate agent/session when mandated; make independence, branch/worktree isolation and reviewer scope explicit. Prefer sequential handoffs to redundant simultaneous agents.
- **Bounded concurrency:** cap simultaneous sessions and expensive builds to the machine's measured resource envelope. Avoid contention-induced timeouts; do not alter the conformance deadline or change results to green. Each worker records failures and exact run provenance.
- **Durable handoff:** every issue-tracked phase publishes its structured, append-only handoff to the task GitHub issue as specified by `docs/process/llm-prompts.md`; the coordinator maintains a compact pointer to the latest valid issue comment (decision, commit/tree, host pins, test evidence links, blockers, owner, next step). A failed comment publication blocks advancing that phase. Local tmp files, OpenClaw memory, and session summaries are convenience caches only. GitHub comments coordinate phase decisions; committed repository files remain semantic and executable truth.
- **Costs and limits:** account for coordinator tokens, each delegated session, cached/context tokens where provided, and repeated tool/test calls. Separate subscription-backed usage from API-billed usage where observable. Do not promise savings until a measured comparison shows them.
- **Safety and authority:** use minimum necessary tool permissions; separate read-only review from code-writing and GitHub mutation; preserve explicit approvals and PR/CI gates. Do not delegate secrets or protected inputs unnecessarily. A coordinator must not merge, close an issue or authorize R29 merely because all workers report success.

**Pilot gate:** first run a small, reversible coordination trial on a bounded nonsemantic task and compare completion quality, token usage and operator effort against the standalone workflow. Do not introduce a mandatory OpenClaw step or replace existing CI until the integration is actually working and reviewed.

## 6. Measure rather than assume savings

For the next **five substantial eligible tasks** after this policy is adopted, when token/usage figures are accessible, record issue/PR, task tier, model(s), input/output/cached tokens, agent count, repeated full-run count, and whether required checks passed. If token figures are unavailable, say **not measured**, not zero or estimated. Summarize at the fifth task: cost/usage per accepted change, regressions, review quality and any added delays. Compare with a grounded historical baseline only when available.

The proposed **40–60% token reduction is a hypothesis, not achieved savings or a target that outranks correctness**. Publish an ADOPT / REVISE / RETIRE assessment in a follow-up issue or PR; avoid turning this pilot into a permanent new gate without an explicit decision. This usage pilot is independent of the temporary #1226 Genia-dogfooding observations.

## 7. Prompt template

> Follow current AGENTS.md and authority documents. Work on [issue] at [exact ref]. Goal: [one measurable outcome]. Use the existing change gates and smallest justified evidence delta; preserve required full acceptance checks and all failed results. Publish detailed evidence on the issue/PR. Return decision, blockers and next action. Keep authority documentation up to date for verified shipped behavior.
