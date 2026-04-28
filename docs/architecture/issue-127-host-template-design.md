# Issue #127 Design — Create Template for New Genia Hosts

**Phase:** design
**Branch:** `issue-127-host-template`
**Issue:** #127 — Create template repo for new Genia hosts
**Spec:** `docs/architecture/issue-127-host-template-spec.md`
**Scope:** Docs / scaffold only. No runtime behavior changes.

---

## 1. Purpose

Translate the approved spec into an exact file map. Six new template files, one new test file, six modified files (one process doc + five planned-host READMEs). No runtime files. No `GENIA_STATE.md` changes.

---

## 2. Scope Lock

Follows spec §2 exactly.

**New files:**
- `hosts/template/AGENTS.md`
- `hosts/template/README.md`
- `hosts/template/CAPABILITY_STATUS.md`
- `hosts/template/adapter_stub.md`
- `hosts/template/ci_stub.md`
- `hosts/template/EXAMPLE.md`
- `tests/test_host_template_structure.py`

**Modified files:**
- `docs/host-interop/HOST_PORTING_GUIDE.md` — pointer to `hosts/template/`
- `hosts/node/README.md` — pointer to `hosts/template/`
- `hosts/go/README.md` — pointer to `hosts/template/`
- `hosts/java/README.md` — pointer to `hosts/template/`
- `hosts/rust/README.md` — pointer to `hosts/template/`
- `hosts/cpp/README.md` — pointer to `hosts/template/`

**Unchanged:**
- `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`
- `HOST_CAPABILITY_MATRIX.md` (no new rows)
- `spec/`, `src/genia/`, `tools/`, `hosts/python/`

---

## 3. Architecture Overview

All deliverables are Markdown documents. There is no runtime component. The test file uses only `pathlib.Path` to verify file presence and string content — it imports no Genia runtime modules. The template directory sits alongside existing planned-host directories (`hosts/node/`, etc.) and does not require changes to any build, import, or packaging configuration.

Dependency chain:
```
hosts/template/CAPABILITY_STATUS.md  ← sources names from docs/host-interop/capabilities.md
hosts/template/adapter_stub.md        ← sources contract from docs/host-interop/HOST_INTEROP.md
hosts/template/README.md              ← references HOST_PORTING_GUIDE.md, HOST_CAPABILITY_MATRIX.md
hosts/template/EXAMPLE.md             ← references HOST_PORTING_GUIDE.md, HOST_CAPABILITY_MATRIX.md
tests/test_host_template_structure.py ← asserts 14 invariants from spec §5
```

---

## 4. File / Module Changes

### New files

| File | Zone | Content source |
|---|---|---|
| `hosts/template/AGENTS.md` | Host Adapters | Pattern: `hosts/node/AGENTS.md` |
| `hosts/template/README.md` | Docs | Pattern: `hosts/node/README.md`; required sections per spec §4.2 |
| `hosts/template/CAPABILITY_STATUS.md` | Docs | Capability names sourced from `capabilities.md` |
| `hosts/template/adapter_stub.md` | Docs | Contract sourced from `HOST_INTEROP.md §Host Adapter and Spec Runner Model` |
| `hosts/template/ci_stub.md` | Docs | Contract sourced from `HOST_PORTING_GUIDE.md §Test Checklist` |
| `hosts/template/EXAMPLE.md` | Docs | 7-step walkthrough per spec §4.6 |
| `tests/test_host_template_structure.py` | Tests | 14 invariants from spec §5 |

### Modified files

| File | Change |
|---|---|
| `docs/host-interop/HOST_PORTING_GUIDE.md` | Insert "See `hosts/template/`" pointer after the opening paragraph |
| `hosts/node/README.md` | Append "## Template" section with pointer |
| `hosts/go/README.md` | Append "## Template" section with pointer |
| `hosts/java/README.md` | Append "## Template" section with pointer |
| `hosts/rust/README.md` | Append "## Template" section with pointer |
| `hosts/cpp/README.md` | Append "## Template" section with pointer |

---

## 5. Data Shapes

### 5.1 `hosts/template/AGENTS.md`

Structure mirrors `hosts/node/AGENTS.md`. Required content:

```
Status: scaffolded, not implemented

[agent discipline block — same required-reading list as HOST_PORTING_GUIDE.md §Required Reading]

This directory is a template. Copy it to hosts/<new-host>/ and replace TODO markers.
Do not treat this directory as an implemented host.

See docs/host-interop/HOST_PORTING_GUIDE.md for the porting checklist.
```

### 5.2 `hosts/template/README.md`

Eleven required headings (per spec §4.2). Content template:

```
# <Host Name> Host
TODO: replace <Host Name> with the target host language.

## Status
scaffolded, not implemented

## Goal
TODO: describe the host's goal.

## Required Reading
[verbatim list from HOST_PORTING_GUIDE.md §Required Reading]

## Minimal Host Requirements
See docs/host-interop/HOST_PORTING_GUIDE.md §Minimal Host Requirements.
[verbatim items]

## Optional Capabilities
See docs/host-interop/HOST_PORTING_GUIDE.md §Optional Capabilities.

## Setup
TODO

## Build
TODO

## Test
Host-local:  TODO
Shared spec: python -m tools.spec_runner

## Lint
TODO

## Known commands
| Task  | Command |
|-------|---------|
| setup | TODO    |
| build | TODO    |
| test  | TODO    |
| lint  | TODO    |
```

References required (per spec §4.2):
- `docs/host-interop/HOST_PORTING_GUIDE.md`
- `docs/host-interop/HOST_CAPABILITY_MATRIX.md`

### 5.3 `hosts/template/CAPABILITY_STATUS.md`

Header note: capability names are authoritative in `docs/host-interop/capabilities.md`.

Table columns: `Capability | Status | Notes`

Capability rows are drawn from `capabilities.md` capability group entries only. Every Status cell must be `Not Implemented`. Every Notes cell is `TODO`.

Footer: `Status must be updated as implementation progresses. Do not mark Implemented until code, tests, and spec coverage all exist.`

Capability names to include (sourced from `capabilities.md`; do not invent names):
- `io.stdout`
- `io.stderr`
- `io.stdin`
- `time.sleep`
- `random.rng`, `random.rand`, `random.rand_int`
- `process.spawn`, `process.send`, `process.alive`
- `ref.ref`, `ref.get`, `ref.set`, `ref.update`
- `http.serve`
- `bytes.utf8_encode`, `bytes.utf8_decode`
- `json.parse`, `json.stringify`
- `zip.entries`, `zip.write`
- `cli.argv`, `cli.parse`
- `flow.lines`, `flow.each`, `flow.collect`, `flow.run`
- `debug.stdio`
- `host_interop.python`, `host_interop.python_json`

> **Implementation note:** Verify this list exhaustively against `capabilities.md` during implementation — do not copy the list above without checking it matches `capabilities.md` exactly. The design names the sourcing rule; the implementation must execute it.

### 5.4 `hosts/template/adapter_stub.md`

Content structure (per spec §4.4):

```
# Spec Runner Integration Stub

Authoritative contract: docs/host-interop/HOST_INTEROP.md §Host Adapter and Spec Runner Model
Wiring point: tools/spec_runner/executor.py::execute_spec

## Required entrypoint

run_case(spec: LoadedSpec) -> ActualResult

## LoadedSpec input fields

| Field       | Present for                    |
|-------------|--------------------------------|
| category    | all                            |
| source      | all                            |
| stdin       | eval, flow, error, cli         |
| file        | cli (file mode)                |
| command     | cli (command and pipe modes)   |
| argv        | cli                            |
| debug_stdio | cli (debug mode)               |

## ActualResult output fields

| Field     | Type   |
|-----------|--------|
| stdout    | string |
| stderr    | string |
| exit_code | int    |

## Category stubs

### parse
TODO: implement parse execution — call host parser, compare normalized AST

### ir
TODO: implement IR execution — call host lowering, compare normalized Core IR output

### eval
TODO: implement eval execution — run source, capture stdout/stderr/exit_code

### cli
TODO: implement CLI execution — run as CLI process, capture stdout/stderr/exit_code

### flow
TODO: implement flow execution — run flow-source program, capture stdout/stderr/exit_code

### error
TODO: implement error execution — run source, assert stdout="", match stderr, exit_code=1
```

### 5.5 `hosts/template/ci_stub.md`

Content structure (per spec §4.5):

```
# CI Configuration Stub

CI setup is host-language-specific. This stub defines the required contract only.
See docs/host-interop/HOST_PORTING_GUIDE.md §Test Checklist.

## Required CI jobs

### shared-spec-runner
Command: python -m tools.spec_runner
Assert: exit code 0
Trigger: on every push / PR

### host-local-tests
Command: TODO (host-language test runner)
Assert: exit code 0
Trigger: on every push / PR

## Setup steps
TODO: describe host-language environment setup (e.g., install runtime, dependencies)

## Notes
- Do not merge a PR that fails the shared spec runner.
- Do not claim a capability as Implemented until both CI jobs pass for that capability.
```

### 5.6 `hosts/template/EXAMPLE.md`

Seven sections per spec §4.6. Structure:

```
# Example: Bringing Up a New Host from the Template

## Step 1 — Copy the template
cp -r hosts/template/ hosts/<new-host>/

## Step 2 — Update status and goal
[instruction: edit AGENTS.md Status line, README.md Goal section]

## Step 3 — Choose a target spec category
[instruction: start with eval; explains why]

## Step 4 — Implement run_case for one category
[instruction: refer to adapter_stub.md; shows LoadedSpec -> ActualResult shape]

## Step 5 — Run the shared spec runner
python -m tools.spec_runner
[instruction: explains pass/fail interpretation]

## Step 6 — Update CAPABILITY_STATUS.md
[instruction: mark capabilities as Not Implemented until code+tests+spec all exist]

## Step 7 — Update HOST_CAPABILITY_MATRIX.md
[instruction: update only the new-host row; no other rows change]

Note: Do not update GENIA_STATE.md or shared docs unless the new host changes shared observable behavior.
```

### 5.7 Pointer text for `HOST_PORTING_GUIDE.md`

Insert after the opening paragraph ("Python is the current reference host. / New hosts should align with Python's implemented semantics, not redefine them."):

```markdown
A ready-to-copy host template lives at `hosts/template/`. Copy it and follow `hosts/template/EXAMPLE.md` as your starting point.
```

### 5.8 Pointer text for planned-host READMEs

Append to each of `hosts/node/README.md`, `hosts/go/README.md`, `hosts/java/README.md`, `hosts/rust/README.md`, `hosts/cpp/README.md`:

```markdown
## Template

Use the host template as a starting point:

- Copy `hosts/template/` to this directory to get the required file structure
- Follow `hosts/template/EXAMPLE.md` for step-by-step bringup guidance
```

---

## 6. Function / Interface Design

### `tests/test_host_template_structure.py`

No runtime imports. Uses only `pathlib.Path`.

**Helper:** `read(path: Path) -> str` — reads file as UTF-8 text.

**Test functions** (one per invariant group; names match the invariant numbers from spec §5):

| Test name | Invariants covered |
|---|---|
| `test_template_required_files_exist` | Files for all 6 required template files are present |
| `test_agents_md_status_label` | Inv 1: contains `scaffolded, not implemented` |
| `test_readme_status_label` | Inv 2: contains `scaffolded, not implemented` |
| `test_readme_references_porting_guide` | Inv 3: contains reference to `HOST_PORTING_GUIDE.md` |
| `test_readme_references_capability_matrix` | Inv 4: contains reference to `HOST_CAPABILITY_MATRIX.md` |
| `test_capability_status_no_implemented_rows` | Inv 5: no `Implemented` status values |
| `test_capability_status_references_capabilities_md` | Inv 6: contains reference to `capabilities.md` |
| `test_capability_status_no_invented_names` | Inv 7: all capability names appear in `capabilities.md` |
| `test_adapter_stub_contains_run_case` | Inv 8: contains `run_case` |
| `test_adapter_stub_references_host_interop` | Inv 9: contains reference to `HOST_INTEROP.md` |
| `test_example_references_required_docs` | Inv 10: contains references to `HOST_PORTING_GUIDE.md` and `HOST_CAPABILITY_MATRIX.md` |
| `test_porting_guide_references_template` | Inv 11: `HOST_PORTING_GUIDE.md` contains `hosts/template/` |
| `test_planned_host_readmes_reference_template` | Inv 12: all five planned-host READMEs contain `hosts/template/` |
| `test_capability_matrix_has_no_template_row` | Inv 13: `HOST_CAPABILITY_MATRIX.md` has no `Template` row |
| `test_genia_state_unchanged_marker` | Inv 14: verifies `GENIA_STATE.md` still contains key unchanged marker string |

For invariant 7 (`test_capability_status_no_invented_names`): the test reads `capabilities.md` to build a set of valid capability names, then asserts every name in `CAPABILITY_STATUS.md`'s table rows is a member of that set. The extraction is done via line scanning (no YAML/JSON parser needed — `capabilities.md` uses `**name:**` markers).

---

## 7. Control Flow

**Implementation order** (to satisfy TDD constraint — tests must be committed failing before template files exist):

1. Commit `tests/test_host_template_structure.py` with all 14 tests → all fail (no `hosts/template/` yet)
2. Create `hosts/template/` directory and all 6 files → tests pass
3. Apply pointer edits to 6 modified files → remaining invariant tests (11, 12) pass
4. Run full test suite to confirm no regressions

**Key decision point:** Invariant 7 requires parsing capability names from `capabilities.md`. The extraction rule is: lines matching `^\- \*\*name:\*\* `` capture the name value. If `capabilities.md` format changes, this test must be updated. The test must not hard-code a name list — it must derive from the file.

---

## 8. Error Handling Design

No runtime errors are introduced. Test failures are the only failure mode:

- **Missing file:** `FileNotFoundError` from `Path.read_text()` — naturally surfaces as test failure
- **Missing string:** `assert "..." in text` — standard pytest assertion failure
- **Invented capability name:** assertion failure in `test_capability_status_no_invented_names`
- **Stale pointer in planned-host README:** assertion failure in `test_planned_host_readmes_reference_template`

No error recovery is needed — test failures are the correct signal.

---

## 9. Integration Points

- **Test runner:** `pytest tests/test_host_template_structure.py` — no dependencies beyond `pathlib` and `pytest`
- **Spec runner:** not involved (no new YAML spec cases)
- **`GENIA_STATE.md` / `GENIA_RULES.md`:** not touched
- **`HOST_CAPABILITY_MATRIX.md`:** read by test (invariant 13) but not modified
- **`capabilities.md`:** read by test (invariant 7) to build valid name set; not modified
- **`docs/contract/semantic_facts.json`:** not touched

---

## 10. Test Design Input

Tests live in: `tests/test_host_template_structure.py`

**What is tested:** Structural presence and content invariants only. No runtime behavior.

**Key invariants (from spec §5):**

| # | Invariant | Test approach |
|---|---|---|
| 1 | `AGENTS.md` contains `scaffolded, not implemented` | `assert "scaffolded, not implemented" in read(AGENTS_MD)` |
| 2 | `README.md` contains `scaffolded, not implemented` | same pattern |
| 3 | `README.md` references `HOST_PORTING_GUIDE.md` | `assert "HOST_PORTING_GUIDE.md" in read(README)` |
| 4 | `README.md` references `HOST_CAPABILITY_MATRIX.md` | `assert "HOST_CAPABILITY_MATRIX.md" in read(README)` |
| 5 | `CAPABILITY_STATUS.md` has no `Implemented` rows | parse table rows, assert no `Implemented` cell |
| 6 | `CAPABILITY_STATUS.md` references `capabilities.md` | `assert "capabilities.md" in read(CAP_STATUS)` |
| 7 | All capability names in `CAPABILITY_STATUS.md` exist in `capabilities.md` | extract names from both files; assert subset |
| 8 | `adapter_stub.md` contains `run_case` | string check |
| 9 | `adapter_stub.md` references `HOST_INTEROP.md` | string check |
| 10 | `EXAMPLE.md` references both guide docs | two string checks |
| 11 | `HOST_PORTING_GUIDE.md` references `hosts/template/` | string check |
| 12 | All five planned-host READMEs reference `hosts/template/` | loop over five paths |
| 13 | `HOST_CAPABILITY_MATRIX.md` has no `Template` row | string check for `\| Template` |
| 14 | `GENIA_STATE.md` unchanged | assert known stable anchor string still present |

**Edge cases:**
- Invariant 7: `capabilities.md` uses `**name:** \`name.value\`` format; extraction must strip backticks and surrounding whitespace
- Invariant 5: "Implemented" must not match `Not Implemented` — use exact column value check, not substring of whole line

---

## 11. Doc Impact

| Doc | Change | Justification |
|---|---|---|
| `GENIA_STATE.md` | None | No implemented behavior changes |
| `GENIA_RULES.md` | None | No language invariant changes |
| `GENIA_REPL_README.md` | None | No runtime behavior changes |
| `README.md` | None | Template is internal tooling, not user-visible language surface |
| `HOST_PORTING_GUIDE.md` | Add pointer to `hosts/template/` | Spec §8 requires it; makes porting guide actionable |
| `HOST_CAPABILITY_MATRIX.md` | None | Template is not a host; no new row |
| Planned-host READMEs (5 files) | Add `## Template` pointer section | Spec §2 requires it; direct future implementers to template |

---

## 12. Constraints

Must:
- Follow existing test patterns from `tests/test_portability_contract_sync.py` and `tests/test_host_boundary_labels.py` (file reads via `pathlib.Path`, `assert "..." in text` checks)
- Keep test file import-free from Genia runtime modules
- Keep template files Markdown-only
- Source all capability names from `capabilities.md` — no hardcoded lists in template files

Must NOT:
- Add `hosts/template/` as a row in `HOST_CAPABILITY_MATRIX.md`
- Update `GENIA_STATE.md`
- Introduce any Python code in template files
- Change the spec runner, shared spec YAML, or `src/genia/`

---

## 13. Complexity Check

- [x] Minimal — 7 new files (6 Markdown + 1 test), 6 pointer-only edits
- [x] Necessary — closes the documented gap between checklist and mechanical starting point
- [ ] Over-engineered — no; every file maps directly to a spec §4 requirement

---

## 14. Final Check

- [x] Matches spec exactly (all 6 required files, all 14 invariants, all 6 modified files)
- [x] No new behavior introduced
- [x] File list is complete and unambiguous
- [x] Test design is precise enough to write failing tests before implementation
- [x] Implementation order is clear: tests first (all fail), then template files, then pointer edits
- [x] All truth-hierarchy docs justified: `GENIA_STATE.md` unchanged, `GENIA_RULES.md` unchanged, `GENIA_REPL_README.md` unchanged, `README.md` unchanged, `HOST_PORTING_GUIDE.md` pointer only, `HOST_CAPABILITY_MATRIX.md` unchanged
