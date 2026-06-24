# === GENIA DOC SYNC ===

CHANGE NAME: issue #493 tooling-ruff-uv-run
CHANGE SLUG: issue-493-tooling-ruff-uv-run
ISSUE: #493
TYPE: feature
BRANCH: feature/issue-493-tooling-ruff-uv-run

Doc Sync output file:
`.genia/process/tmp/handoffs/issue-493-tooling-ruff-uv-run/06-doc-sync.md`

Starting branch: feature/issue-493-tooling-ruff-uv-run
Working branch: feature/issue-493-tooling-ruff-uv-run
Branch already existed or newly created: already existed

---

## 0. SUMMARY

Docs Sync was expected to be a near no-op but was NOT. A repo-wide search for
`ruff`/`uvx` references found two durable host docs that the Implementation
phase did not catch (the implementation only touched `.github/workflows/ci.yml`).
Both used the ephemeral `uvx ruff check .` form, which the Contract/Design
phases require to be the project-managed `uv run ruff check .` form.

Both were corrected in this phase.

---

## 1. FULL REFERENCE SWEEP

Search command (excluding handoffs, `.venv`, site-packages):

```bash
grep -RIn "ruff\|uvx" . --include="*.md" --include="*.yml" --include="*.yaml" \
  --include="*.toml" --include="*.cfg" --include="*.ini" \
  | grep -v ".genia/process/tmp/handoffs" | grep -v "/.venv/" | grep -v "site-packages"
```

All ruff/uvx references in tracked, durable files:

| File | Reference | State after this phase |
|------|-----------|------------------------|
| `pyproject.toml:18` | `"ruff>=0.8.0"` (dev dep) | correct — added in Implementation |
| `pyproject.toml:48` | `[tool.ruff]` config | unchanged baseline — correct |
| `.github/workflows/ci.yml:58` | `uv run ruff check .` | correct — fixed in Implementation |
| `hosts/python/README.md:38` | `uvx ruff check .` → `uv run ruff check .` | **fixed in Doc Sync** |
| `hosts/python/AGENTS.md:20` | `uvx ruff check .` → `uv run ruff check .` | **fixed in Doc Sync** |

No `ruff`/lint references exist in top-level `README.md`, top-level `AGENTS.md`,
`docs/process/*`, or `docs/ai/LLM_CONTRACT.md`.

---

## 2. CHANGES MADE IN THIS PHASE

`hosts/python/README.md` — under "Known commands":

```diff
- - lint: `uvx ruff check .`
+ - lint: `uv run ruff check .`
```

`hosts/python/AGENTS.md` — under "Known local commands":

```diff
- - lint: `uvx ruff check .`
+ - lint: `uv run ruff check .`
```

Both are single-line command corrections inside existing command-reference
lists. No prose, policy, tutorial, or philosophy content was added. No language
or runtime docs were touched.

---

## 3. CONTRACT COMPLIANCE

- Command spelling now consistent: every documented ruff invocation in the repo
  uses `uv run ruff check .`. No bare `ruff` or `uvx ruff` remains as a
  documented workflow.
- No overclaiming wording introduced (ruff is not described as validating Genia
  semantics, replacing pytest/specs, or guaranteeing correctness).
- No durable language/runtime docs changed (`GENIA_STATE.md`, `GENIA_RULES.md`,
  `GENIA_REPL_README.md`, `docs/book/*`, `docs/architecture/*`, `spec/*`
  untouched).
- Existing `[tool.ruff]` config preserved.

---

## 4. NOTES / FOLLOW-UPS

- The Implementation handoff (`04-implementation.md`) claimed
  `ryan-holiday-book-club-list.md` was "left untouched and unstaged." That file
  no longer exists in the working tree (not committed, not ignored). Out of
  issue scope, but the implementation report is now inaccurate on that point.
- Implementation missed the two `hosts/python/` references because its search
  scope was narrower than the full repo. Recommend the Audit phase re-run the
  full sweep above to confirm no stragglers.
- No other follow-ups.

---

## 5. VERDICT

Docs Sync complete. Two durable host-doc references corrected to the
project-managed `uv run ruff check .` form. Ready for Audit phase.
