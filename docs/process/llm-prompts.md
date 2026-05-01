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