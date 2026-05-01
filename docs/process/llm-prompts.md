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

# TASK

<phase-specific task goes here>

---

# CONSTRAINTS

- Follow pre-flight / contract / design (as applicable)
- No scope expansion
- No unrelated changes
- Prefer minimal edits