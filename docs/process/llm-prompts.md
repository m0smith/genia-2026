# === GENIA LLM PROMPT WRAPPER ===

Follow docs/process/llm-system-prompt.md.

GENIA_STATE.md is final authority.

Run:
./scripts/check-genia-branch.sh

Rules:
- Do not work on main
- Do not proceed beyond this phase
- Do not expand scope
- Do not invent behavior

---

# PHASE

This prompt is for phase: <PHASE>  
Commit prefix: <PREFIX>

---

# SCOPE

Work ONLY on:
<explicit files or modules>

If additional files are required → STOP and report.

---

# HANDOFF

Change slug: <change-slug>

Read prior handoffs:
- .genia/process/tmp/handoffs/<change-slug>/00-preflight.md
- .genia/process/tmp/handoffs/<change-slug>/01-contract.md
- .genia/process/tmp/handoffs/<change-slug>/02-design.md

Write this phase handoff to:
.genia/process/tmp/handoffs/<change-slug>/<phase-number>-<phase-name>.md

If required handoffs are missing → STOP and report.

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

For a code-bearing change, run a separate phase **after implementation and before docs** using `docs/process/code-maintainability-review.md`.

- Inspect the actual diff and neighboring call sites; do not accept implementer summaries as review evidence.
- Record reviewer independence, file/line findings, severity, dispositions, and a PASS / PASS WITH NON-BLOCKING FINDINGS / FAIL verdict in the change handoff.
- On FAIL, STOP and return to implementation for focused corrections and repeat review before continuing.
- For non-blocking findings, record accountable follow-up rather than silently dropping them.
- Keep final truth audit separate. Do not change implemented-language authority; maintain `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, and `README.md` when actual behavior changes.
