# Issue #127 Spec — Create Template for New Genia Hosts

**Phase:** spec
**Branch:** `issue-127-host-template`
**Issue:** #127 — Create template repo for new Genia hosts
**Scope:** Docs / scaffold only. No runtime behavior changes. No language semantics changes.

---

## 1. Source of Truth

Final authority: `GENIA_STATE.md`

Supporting (in authority order):
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
- `README.md`
- `docs/host-interop/HOST_INTEROP.md` — host adapter contract and `run_case` signature
- `docs/host-interop/HOST_PORTING_GUIDE.md` — porting checklist (template supplements, does not replace)
- `docs/host-interop/capabilities.md` — authoritative capability name/shape registry
- `docs/host-interop/HOST_CAPABILITY_MATRIX.md` — per-host capability status matrix
- `docs/architecture/core-ir-portability.md` — Core IR portability boundary
- `hosts/python/` — reference adapter structure (template is modeled after this)
- `hosts/node/README.md` — representative scaffolded host (current gap the template closes)

Relevant existing truths:
- Python is the only implemented host and is the reference host.
- `hosts/node/`, `hosts/go/`, `hosts/java/`, `hosts/rust/`, `hosts/cpp/` contain only `AGENTS.md` + `README.md` with TODO placeholders.
- `docs/host-interop/HOST_PORTING_GUIDE.md` exists as a checklist but provides no mechanical starting point.
- `hosts/python/adapter.py` exposes `run_case(spec: LoadedSpec) -> ActualResult` as the canonical spec runner integration entrypoint (per `HOST_INTEROP.md`).
- Capability names and portability status are authoritative in `capabilities.md`.

---

## 2. Scope

### Included

- A new directory `hosts/template/` containing the following required files (defined precisely below)
- An onboarding guide embedded in `hosts/template/README.md`
- A capability status stub in `hosts/template/CAPABILITY_STATUS.md`
- A spec runner integration stub in `hosts/template/adapter_stub.md`
- A CI stub in `hosts/template/ci_stub.md`
- An example walkthrough in `hosts/template/EXAMPLE.md`
- A pointer to the template in `docs/host-interop/HOST_PORTING_GUIDE.md`
- A pointer to the template in each existing planned-host README (`hosts/node/README.md`, `hosts/go/README.md`, `hosts/java/README.md`, `hosts/rust/README.md`, `hosts/cpp/README.md`)

### Explicitly Excluded

- No implementation of any actual host runtime
- No changes to `GENIA_STATE.md`
- No changes to `GENIA_RULES.md`, `GENIA_REPL_README.md`, or `README.md`
- No changes to `spec/`, `tools/spec_runner/`, or `src/genia/`
- No changes to `hosts/python/` (the reference host)
- No changes to `HOST_CAPABILITY_MATRIX.md` capability rows (template is not an implemented host)
- No new shared spec YAML cases
- No new language features, syntax, or Core IR changes

---

## 3. Behavior Definition

### What this change does

It creates `hosts/template/` as an in-repo starting point that makes new host creation mostly mechanical. A host implementer copies `hosts/template/` to their target host directory, follows the onboarding guide, and replaces `TODO` markers with working code.

The template does not implement runtime behavior. It provides:
- The required file structure
- The required section headings with `TODO` markers
- The spec runner integration contract documented as a stub
- The capability list as stubs sourced from `capabilities.md`
- A CI workflow skeleton
- A step-by-step example walkthrough

### Inputs

None at runtime. This is a static scaffold.

### Outputs

A directory `hosts/template/` containing the required files enumerated in §4.

### State changes

- `hosts/template/` is created (new directory)
- `docs/host-interop/HOST_PORTING_GUIDE.md` gains a pointer to `hosts/template/`
- Each planned-host README gains a pointer to `hosts/template/`
- `HOST_CAPABILITY_MATRIX.md` gains no new rows (template is not a host)

---

## 4. Required File Structure and Content Contract

### 4.1 `hosts/template/AGENTS.md`

Must contain:

- A `Status:` line with exactly the value `scaffolded, not implemented`
- A statement that agents must read `AGENTS.md`, `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, and `README.md` before working in any host directory
- A statement that this directory is a template and must not be treated as an implemented host
- A reference to `docs/host-interop/HOST_PORTING_GUIDE.md`

Must not contain:

- Claims that any capability is implemented
- Any runtime code

### 4.2 `hosts/template/README.md`

Required sections (each must be present by heading):

1. `# <Host Name> Host` — with a `TODO: replace <Host Name>` note
2. `## Status` — must contain `scaffolded, not implemented`
3. `## Goal` — with a `TODO` placeholder for the host's goal statement
4. `## Required Reading` — must enumerate the same reading list as `HOST_PORTING_GUIDE.md §Required Reading` verbatim
5. `## Minimal Host Requirements` — must reference `HOST_PORTING_GUIDE.md §Minimal Host Requirements` and enumerate the same items
6. `## Optional Capabilities` — must reference `HOST_PORTING_GUIDE.md §Optional Capabilities`
7. `## Setup` — with `TODO` placeholder
8. `## Build` — with `TODO` placeholder
9. `## Test` — must include: `python -m tools.spec_runner` as the shared spec runner invocation and a `TODO` for the host-local test command
10. `## Lint` — with `TODO` placeholder
11. `## Known commands` — summary table mirroring the format in `hosts/node/README.md`

Must reference `docs/host-interop/HOST_PORTING_GUIDE.md`.
Must reference `docs/host-interop/HOST_CAPABILITY_MATRIX.md`.
Must not claim any capability as implemented.

### 4.3 `hosts/template/CAPABILITY_STATUS.md`

This file is the per-host copy of the capability tracking table.

Must contain:

- A header noting that capability names are authoritative in `docs/host-interop/capabilities.md`
- A status table with one row per capability group from `capabilities.md`, using these exact columns:
  - `Capability` — name from `capabilities.md`
  - `Status` — must be `Not Implemented` for every row in the template
  - `Notes` — `TODO` placeholder for each row
- The complete set of capability group names drawn only from `capabilities.md` (no invented capability names)
- A footer: `Status must be updated as implementation progresses. Do not mark Implemented until code, tests, and spec coverage all exist.`

Must not claim any capability as `Implemented` or `Python-host-only`.

### 4.4 `hosts/template/adapter_stub.md`

This file documents the spec runner integration contract as a code-stub narrative.

Must contain:

1. A statement that `run_case(spec: LoadedSpec) -> ActualResult` is the required entrypoint (sourced from `HOST_INTEROP.md §Host Adapter and Spec Runner Model`)
2. The required input fields for `LoadedSpec`:
   - `category` (all)
   - `source` (all)
   - `stdin` (eval, flow, error, cli)
   - `file` (cli file mode)
   - `command` (cli command and pipe modes)
   - `argv` (cli)
   - `debug_stdio` (cli debug mode)
3. The required output fields for `ActualResult`:
   - `stdout`
   - `stderr`
   - `exit_code`
4. A `TODO` block for each spec category: `parse`, `ir`, `eval`, `cli`, `flow`, `error`
5. A reference to `HOST_INTEROP.md §Host Adapter and Spec Runner Model` as the authoritative contract
6. A note that the adapter must wire into `tools/spec_runner/executor.py::execute_spec`

Must not contain working runtime code.

### 4.5 `hosts/template/ci_stub.md`

This file is a CI configuration narrative stub.

Must contain:

1. A note that CI setup is host-language-specific and this stub describes the required contract only
2. Required CI job: run the shared spec runner (`python -m tools.spec_runner`) and assert exit code 0
3. Required CI job: run the host-local test suite with a `TODO` for the specific command
4. A `TODO` for the host-language setup steps
5. A reference to `docs/host-interop/HOST_PORTING_GUIDE.md §Test Checklist`

Must not contain a working GitHub Actions YAML workflow (CI setup is host-language-specific and cannot be templated as runnable YAML without a working runtime).

### 4.6 `hosts/template/EXAMPLE.md`

This file is a step-by-step walkthrough showing how to bring up a new host from the template.

Must contain:

1. `## Step 1 — Copy the template`: instruction to copy `hosts/template/` to `hosts/<new-host>/`
2. `## Step 2 — Update status and goal`: instruction to update `AGENTS.md`, `README.md` Status and Goal sections
3. `## Step 3 — Choose a target spec category`: instruction to pick one spec category (recommended: `eval`) and implement only what is needed to pass one case
4. `## Step 4 — Implement run_case for one category`: instruction referencing `adapter_stub.md` and showing the `LoadedSpec` → `ActualResult` contract
5. `## Step 5 — Run the shared spec runner`: instruction showing `python -m tools.spec_runner` and how to interpret a first pass/fail
6. `## Step 6 — Update CAPABILITY_STATUS.md`: instruction to mark capabilities as `Not Implemented` until code + tests + spec coverage all exist
7. `## Step 7 — Update HOST_CAPABILITY_MATRIX.md`: instruction to update only the row for the new host; no other rows may change
8. A closing note: "Do not update `GENIA_STATE.md` or shared docs unless the new host changes shared observable behavior."

Must demonstrate behavior only using already-implemented Genia features (no invented language features).
Must not claim to produce a working host — it demonstrates the process, not the result.

---

## 5. Invariants

These must always hold after the change lands. They drive the test phase.

1. `hosts/template/AGENTS.md` contains the string `scaffolded, not implemented`
2. `hosts/template/README.md` contains the string `scaffolded, not implemented`
3. `hosts/template/README.md` contains a reference to `HOST_PORTING_GUIDE.md`
4. `hosts/template/README.md` contains a reference to `HOST_CAPABILITY_MATRIX.md`
5. `hosts/template/CAPABILITY_STATUS.md` contains no `Implemented` status values
6. `hosts/template/CAPABILITY_STATUS.md` contains a reference to `capabilities.md`
7. Every capability name in `CAPABILITY_STATUS.md` exists in `capabilities.md` (no invented names)
8. `hosts/template/adapter_stub.md` contains the string `run_case`
9. `hosts/template/adapter_stub.md` references `HOST_INTEROP.md`
10. `hosts/template/EXAMPLE.md` contains references to `HOST_PORTING_GUIDE.md` and `HOST_CAPABILITY_MATRIX.md`
11. `docs/host-interop/HOST_PORTING_GUIDE.md` contains a reference to `hosts/template/`
12. Each of `hosts/node/README.md`, `hosts/go/README.md`, `hosts/java/README.md`, `hosts/rust/README.md`, `hosts/cpp/README.md` contains a reference to `hosts/template/`
13. `HOST_CAPABILITY_MATRIX.md` contains no `Template` row (template is not a host)
14. `GENIA_STATE.md` is unchanged

---

## 6. Failure Behavior

This is a scaffold change, not runtime behavior. Failures are structural:

- If a required file is missing from `hosts/template/`, the test (structural presence check) fails
- If a required section heading is missing from a required file, the test (content check) fails
- If `CAPABILITY_STATUS.md` contains an invented capability name not in `capabilities.md`, the test fails
- If any template file claims `Implemented` status, the test fails
- If `HOST_PORTING_GUIDE.md` does not reference `hosts/template/`, the test fails

No runtime errors are introduced.

---

## 7. Examples

### Minimal

After this change, a new host implementer can do:

```
cp -r hosts/template/ hosts/mylang/
# Follow hosts/mylang/EXAMPLE.md
```

And immediately have a correctly-structured host directory with all required sections and no broken invariants.

### Real: Verifying template structure

```bash
# Check required files exist
ls hosts/template/AGENTS.md
ls hosts/template/README.md
ls hosts/template/CAPABILITY_STATUS.md
ls hosts/template/adapter_stub.md
ls hosts/template/ci_stub.md
ls hosts/template/EXAMPLE.md
```

### Real: Running the structural invariant tests

```bash
pytest tests/test_host_template_structure.py -v
```

---

## 8. Non-Goals

- Does NOT implement any host runtime
- Does NOT add new language features or Core IR nodes
- Does NOT change shared spec cases
- Does NOT change `GENIA_STATE.md`
- Does NOT change the spec runner itself
- Does NOT create a working CI workflow (CI is language-specific)
- Does NOT replace `HOST_PORTING_GUIDE.md` (it supplements it)
- Does NOT add `hosts/template/` as a row in `HOST_CAPABILITY_MATRIX.md`

---

## 9. Implementation Boundary

This spec is host-neutral: all files in `hosts/template/` are Markdown documents or plain-text stubs. No runtime code is written. No Python, Node, Java, Rust, Go, or C++ code is added. The structural invariants are testable in Python via file presence and content checks without invoking any host runtime.

---

## 10. Doc Requirements

### `GENIA_STATE.md`

No update required. No new implemented behavior exists.

### `GENIA_RULES.md`

No update required. No language invariants change.

### `GENIA_REPL_README.md`

No update required. No runtime behavior changes.

### `README.md`

No update required. This is a scaffold change not visible to language users.

### `docs/host-interop/HOST_PORTING_GUIDE.md`

Update required: add a pointer to `hosts/template/` at the top of the guide.

### `docs/host-interop/HOST_CAPABILITY_MATRIX.md`

No new rows. No change to existing rows.

### Planned-host READMEs

Minor update required to each of: `hosts/node/README.md`, `hosts/go/README.md`, `hosts/java/README.md`, `hosts/rust/README.md`, `hosts/cpp/README.md` — add a pointer to `hosts/template/`.

---

## 11. Complexity Check

- [x] Minimal — six Markdown files, pointer updates to four existing docs
- [x] Necessary — closes the gap between "checklist exists" and "mechanical starting point exists"
- [ ] Overly complex — no; all content is direct transcription of existing authoritative docs into stub form

---

## 12. Final Check

- [x] No implementation details included
- [x] No scope expansion beyond pre-flight
- [x] Consistent with `GENIA_STATE.md` (no new implemented behavior claimed)
- [x] All invariants are precise and testable
- [x] All required file sections sourced only from existing authoritative docs
- [x] No invented capability names
- [x] Truth-hierarchy docs justified: `GENIA_STATE.md` unchanged, `GENIA_RULES.md` unchanged, `GENIA_REPL_README.md` unchanged, `README.md` unchanged, `HOST_PORTING_GUIDE.md` updated (pointer only), `HOST_CAPABILITY_MATRIX.md` unchanged
