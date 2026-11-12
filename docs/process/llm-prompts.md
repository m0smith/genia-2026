# === GENIA LLM PROMPT WRAPPER ===

Follow docs/process/llm-system-prompt.md.

GENIA_STATE.md is final authority.

Run:
./scripts/check-genia-branch.sh

Rules:
- Do not work on main
- Do not proceed beyond the explicitly authorized phase **or bounded implementation slice**
- Do not expand scope
- Do not invent behavior

---

# PHASE

This prompt is for phase or approved bounded slice: <PHASE_OR_SLICE>  
Commit prefix(es): <PREFIX> (use distinct test/feat/docs prefixes and commits for bounded slices)

---

# SCOPE

Work ONLY on:
<explicit files or modules>

If additional files are required outside the authorized impact map → STOP and report.

---

# HANDOFF — GITHUB ISSUE COMMENTS (CANONICAL)

Task issue: <GitHub issue URL and number>
Phase: <phase-number>-<phase-name>

Before starting:
- Read the issue body, relevant preceding phase comments, and linked commits/PR evidence.
- Resolve the latest accepted iteration of each prerequisite phase. If a prerequisite is missing, blocked, or ambiguous, STOP and report. Do not assume a local file or agent memory is authoritative.
- Respect separate authorization for new semantic decisions and unapproved phases. A maintainer may explicitly approve a bounded implementation slice covering sequential RED, GREEN, docs and one independent final review.

Before reporting this authorized phase **or bounded slice** complete, publish and verify **one top-level comment on the task issue** with:
- heading `Phase <number> — <name> (iteration <n>)` or `Slice <name> — Consolidated Handoff (iteration <n>)`, agent/reviewer and UTC timestamp;
- PASS / PASS WITH NON-BLOCKING FINDINGS / FAIL / BLOCKED verdict and scope/decision;
- branch, exact commit/tree SHA and linked PR where applicable;
- separately committed RED test SHA and observed failure before implementation where applicable; GREEN SHA; test commands, observed results, failures, and evidence links (include host/version pins when relevant);
- blockers, accountable follow-ups, superseded comment URL if retrying, and authorized next action.

GitHub comments are an append-only phase/slice ledger. In an explicitly authorized bounded slice, one consolidated completion comment replaces intermediate microphase comments, but never replaces failing-test commits, recorded failures, an independent final review, or required external CI/release gates. Supersede prior handoffs by linking from a new comment, not silently overwriting old evidence. Never publish secrets, protected content or enormous raw logs; link appropriately accessible artifacts instead.

If posting or verifying the comment fails: report `HANDOFF NOT PUBLISHED — BLOCKED` and do not advance a gated phase. A temporary local draft is permitted for recovery, but **is not a completed handoff**. Repository files/commits remain authoritative for implemented behavior and test artifacts; issue comments are coordination evidence, not language-semantic authority.

---

# TASK

<phase-specific task goes here>

---

# CONSTRAINTS

- Follow pre-flight / contract / design (as applicable)
- No scope expansion
- No unrelated changes
- Prefer minimal edits

---

# MAINTAINABILITY REVIEW PHASE

For high-risk unsettled semantics, run the separately required maintainability review **after implementation and before docs**. For an explicitly authorized bounded implementation slice, combine maintainability and behavior/truth review into **one independent final review** using `docs/process/code-maintainability-review.md` and applicable audit criteria; do not self-review.

- Inspect the actual diff and neighboring call sites; do not accept implementer summaries as review evidence.
- Record reviewer independence, file/line findings, severity, dispositions, and a PASS / PASS WITH NON-BLOCKING FINDINGS / FAIL verdict in the change handoff.
- On FAIL, STOP and return to implementation for focused corrections and repeat review before continuing.
- For non-blocking findings, record accountable follow-up rather than silently dropping them.
- Keep final truth audit separate for high-risk semantic decisions and release acceptance. Approved bounded slices can use a combined independent review without dropping truth checks. Do not change implemented-language authority; maintain `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, and `README.md` when actual behavior changes.
