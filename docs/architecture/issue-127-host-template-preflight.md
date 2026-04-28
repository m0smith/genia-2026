# Issue #127 Pre-Flight — Create template repo for new Genia hosts

**Phase:** preflight
**Branch:** `issue-127-host-template`
**Issue:** #127 — Create template repo for new Genia hosts (parent: #115)

---

## 1. Scope

**Includes:**
- A host template directory (in-repo) that new host implementers can copy and fill in
- Skeleton files: skeleton runtime stub, shared spec runner integration point, capability stubs, CI setup, and host README/onboarding guide
- An example walkthrough showing a host being brought up from the template
- An onboarding guide explaining the checklist a new host must complete

**Excludes:**
- Any change to `GENIA_STATE.md`, `GENIA_RULES.md`, or `GENIA_REPL_README.md`
- Any implementation of an actual new host (Node, Java, Rust, Go, C++)
- Changes to the Python reference host runtime (`src/genia/`)
- Changes to shared spec content under `spec/`
- Changes to the spec runner itself (`tools/spec_runner/`)
- Changes to `HOST_CAPABILITY_MATRIX.md` beyond what the template itself touches

---

## 2. Source of Truth Files

In authority order per AGENTS.md:

1. `GENIA_STATE.md` — final authority
2. `GENIA_RULES.md`
3. `GENIA_REPL_README.md`
4. `README.md`
5. `docs/host-interop/HOST_INTEROP.md`
6. `docs/host-interop/HOST_PORTING_GUIDE.md` — most directly relevant
7. `docs/host-interop/HOST_CAPABILITY_MATRIX.md`
8. `docs/host-interop/capabilities.md` — authoritative capability name/shape registry
9. `docs/architecture/core-ir-portability.md`
10. `hosts/python/` — reference adapter structure (template model)
11. `hosts/node/`, `hosts/go/`, `hosts/java/`, `hosts/rust/`, `hosts/cpp/` — existing scaffolded stubs

---

## 3. Current Behavior (from docs only)

- `HOST_PORTING_GUIDE.md` exists as a documentation checklist
- Existing scaffolded host directories contain only `AGENTS.md` and `README.md` with TODO placeholders
- No skeleton runtime, CI stub, capability stub files, or onboarding walkthrough exists
- `hosts/python/adapter.py` is the only working adapter structure with `run_case`, `exec_*.py` modules, and normalization code
- `HOST_PORTING_GUIDE.md` provides a checklist but no mechanical starting point

---

## 4. Desired Behavior (from issue only)

- A host template (in-repo template directory) making new host creation "mostly mechanical"
- Template includes: skeleton runtime, shared spec runner integration, capability stubs, CI setup, host README/onboarding guide
- An example showing how to bring up a new host from the template
- Goal: turn host creation into "a checklist instead of a free-form expedition"

---

## 5. Non-Goals

- Do NOT implement any actual host beyond stubs/skeletons
- Do NOT change language semantics, Core IR, or the shared spec contract
- Do NOT update `GENIA_STATE.md` with any new behavior
- Do NOT modify the spec runner or shared spec cases
- Do NOT replace `HOST_PORTING_GUIDE.md`
- Do NOT add `hosts/template/` as a row in `HOST_CAPABILITY_MATRIX.md`

---

## 6. Contract vs. Implementation Split

| Zone | What changes |
|---|---|
| Docs / Tests / Examples | New template files, onboarding guide, example walkthrough |
| Host Adapters | Template stubs modeled after `hosts/python/` — no behavior change to Python host |
| Language Contract | No changes |
| Core IR | No changes |

---

## 7. Test Strategy

- Structural presence tests: required files exist
- Content tests: required sections, status labels, cross-references
- No-invented-names test: all capability names derive from `capabilities.md`
- No-Implemented-rows test: template starts fully Not Implemented
- Pointer tests: `HOST_PORTING_GUIDE.md` and planned-host READMEs reference `hosts/template/`
- Regression guard: `HOST_CAPABILITY_MATRIX.md` has no Template row; `GENIA_STATE.md` anchor intact

---

## 8. Docs Impact

- `docs/host-interop/HOST_PORTING_GUIDE.md` — add pointer to `hosts/template/`
- `hosts/{node,go,java,rust,cpp}/README.md` — add pointer to `hosts/template/`
- `hosts/README.md` — add `hosts/template/` to Target Layout
- `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md` — no change

---

## 9. Cross-File Impact

| File / Directory | Impact |
|---|---|
| `hosts/template/` | New — all template content |
| `hosts/node/README.md` ... `hosts/cpp/README.md` | Pointer added |
| `docs/host-interop/HOST_PORTING_GUIDE.md` | Pointer added |
| `hosts/README.md` | Target Layout updated |
| `HOST_CAPABILITY_MATRIX.md` | No change |
| `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md` | No change |
| `spec/`, `src/genia/`, `tools/`, `hosts/python/` | No change |

---

## 10. Risk of Drift

| Risk | Severity | Mitigation |
|---|---|---|
| Template capability stubs use names not in contract | High | Names sourced only from `capabilities.md`; test enforces this |
| Template guide duplicates instead of referencing `HOST_PORTING_GUIDE.md` | Medium | Template references, does not duplicate |
| Template spec runner stub diverges from actual adapter contract | Medium | Sourced from `HOST_INTEROP.md §Host Adapter`; kept minimal |
| Template grows into an actual host claim | Medium | Status label `scaffolded, not implemented` enforced by test |

---

## 11. GO / NO-GO Decision

**GO**

- Scope bounded: new scaffold files only, no language behavior changes
- All authoritative sources consistent on what a host needs
- Model exists in `hosts/python/` — template is largely a de-content copy with TODO stubs
- No `GENIA_STATE.md` update required
- Risk of semantic drift low — deliverable is documentation and stubs, not runtime code
