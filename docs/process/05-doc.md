# === GENIA DOC SYNC PROMPT (LEAN) ===

Follow docs/process/llm-system-prompt.md.

CHANGE NAME: <short name>
CHANGE SLUG: <short-kebab-name>

GENIA_STATE.md is final authority.

---

# HANDOFF

Read:
- .genia/process/tmp/handoffs/<change-slug>/00-preflight.md
- .genia/process/tmp/handoffs/<change-slug>/01-contract.md
- .genia/process/tmp/handoffs/<change-slug>/02-design.md
- .genia/process/tmp/handoffs/<change-slug>/04-implementation.md

If any are missing → STOP and report.

Write output to:
.genia/process/tmp/handoffs/<change-slug>/06-doc-sync.md

This file must be created.

---

0. BRANCH CHECK

- Must NOT be on main
- Must match pre-flight branch
- If mismatch → STOP

---

Sync docs for <CHANGE NAME>.

Goal:
Make documentation match the actual implemented and tested behavior.

Rules:
- Document only what is implemented and verified by tests
- Do not add future behavior
- Do not expand scope
- Keep updates minimal and local
- Examples must match real syntax/output

---

1. SCOPE

Update ONLY for:
- contract-defined behavior
- implemented code
- verified test results

Do NOT:
- document unimplemented features
- “clean up everything” outside scope

---

2. FILES TO UPDATE

Core:
- GENIA_STATE.md (authoritative)
- GENIA_RULES.md (only if semantics changed)
- GENIA_REPL_README.md (if affected)
- README.md (if user-facing changes)

Supporting (if needed):
- docs/design/*
- docs/cheatsheet/*
- docs/host-interop/*
- docs/releases/* (see step 6a — required when this change lands or extends the active release's headline behavior)
- examples/*

---

3. UPDATE PLAN

For each file:
- sections impacted
- what must change
- minimal wording updates

Preserve structure and tone.

---

4. GENIA_STATE.md (CRITICAL)

Ensure it:
- reflects exact behavior
- marks maturity (Experimental / Partial / Stable)
- lists limitations honestly
- does NOT overstate capabilities

---

5. RULES / SEMANTICS

Update GENIA_RULES.md only if:
- evaluation behavior changed
- pattern/matching semantics changed

Keep minimal and precise.

---

6. EXAMPLES

Ensure:
- examples run (if applicable)
- outputs match real behavior
- no reliance on unimplemented features

Update or add minimal examples if needed.

---

6a. RELEASE EXAMPLE PAGE (`docs/releases/<Rn>.md`)

If this change delivers, extends, or meaningfully changes the active
release's headline behavior (the theme/primary-outcomes in
`docs/strategy/release-roadmap.md`):

- Add or update one small, copy-pasteable, runnable example on
  `docs/releases/<Rn>.md` for the active release (create the file from
  the existing releases if it doesn't exist yet; add it to `mkdocs.yml`
  nav and `docs/releases/README.md`'s release list).
- The example must actually run: paste-and-run it yourself (`genia ...` /
  `genia test ...` / whatever the feature's entry point is) and copy the
  real output into the page. Do not hand-write expected output.
- Keep it minimal — the smallest snippet that demonstrates the behavior,
  not a comprehensive tour.
- If the change is internal/infra with no new example-worthy behavior,
  state that explicitly in this phase's output instead of skipping
  silently.

This step is part of what "done" means for a release-facing change, not
optional polish.

---

7. CONSISTENCY CHECK

Verify alignment across:
- GENIA_STATE.md
- GENIA_RULES.md
- GENIA_REPL_README.md
- README.md
- examples
- docs/releases/<Rn>.md (if step 6a applied)

No contradictions.

---

8. TRUTH CHECK

Docs must:
- reflect real behavior
- clearly state limitations
- avoid exaggeration

---

9. COMPLEXITY CHECK

Mark one:

[ ] Minimal and clear  
[ ] Slightly expanded but justified  
[ ] Too verbose  

Explain only if not minimal.

---

OUTPUT:

1. Summary of doc changes  
2. Files updated  
3. Key wording changes  
4. Risks or ambiguities  

No redesign. No speculation. Only truth.