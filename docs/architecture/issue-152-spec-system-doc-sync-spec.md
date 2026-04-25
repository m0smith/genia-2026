# Issue #152 — Spec-System Doc Sync: Spec

**Phase:** spec
**Branch:** issue-152-spec-system-doc-sync
**Issue:** #152 — Subtask for #116: Sync spec-system documentation with current shared spec reality
**Scope:** Documentation/spec sync only. No runtime behavior changes.

---

## Truth Baseline (from GENIA_STATE.md — final authority)

Before consulting any other source, these facts are authoritative:

- Active shared spec categories: `parse`, `ir`, `eval`, `cli`, `flow`, `error` — all six executable.
- `eval`, `ir`, `cli` have active, executable shared spec files.
- `flow` is active, first-wave coverage only.
- `error` is active, initial coverage only.
- `parse` is active, initial coverage only.
- The runner loads from `spec/parse/`, `spec/ir/`, `spec/eval/`, `spec/cli/`, `spec/flow/`, `spec/error/`.
- Scaffold-only directories (no executable cases): `spec/errors/`, `spec/flows/`, `spec/parser/`, `spec/pattern/`.
- No second host is implemented; Python is the only host and reference host.
- `tools/spec_runner/` is a real implemented runner, gated in CI.

---

## Drift Item 1: `GENIA_STATE.md` — Stale Limitations Bullets (lines 173–174)

### Location

`GENIA_STATE.md` — Section 1 `**Limitations:**` block, lines 173–174.

### Current stale text

```
- Shared semantic-spec case files exist under `spec/eval/`, `spec/ir/`, `spec/cli/`, `spec/flow/`, and `spec/error/` in this phase.
- The current shared semantic-spec runner does not yet execute parse categories as shared spec files.
```

### Why stale

Line 173 omits `spec/parse/` from the directory list. Line 174 directly contradicts lines 18–19, 54–55, and 154 of the same file, all of which confirm that parse is active and the runner executes parse cases.

### Required correction

Replace lines 173–174 with text that:
- Lists all six directories: `spec/eval/`, `spec/ir/`, `spec/cli/`, `spec/flow/`, `spec/error/`, and `spec/parse/`.
- States that the runner executes parse categories.
- Preserves the "initial coverage only" qualifier for parse.

### Required phrase (for test assertion)

`spec/parse/` must appear in the Limitations section of `GENIA_STATE.md` alongside the other five directories.

### Forbidden phrase (for test assertion)

`"The current shared semantic-spec runner does not yet execute parse categories as shared spec files."` must not appear anywhere in `GENIA_STATE.md`.

### Scope note

The two bullets at lines 171–172 (Python-only, no browser) are accurate and must not change.

---

## Drift Item 2: `docs/host-interop/HOST_INTEROP.md` — Stale Parse Coverage Claim

### Location

`docs/host-interop/HOST_INTEROP.md` line 102.

### Current stale text

```
- This runner does not yet provide implemented shared case coverage for parse.
```

### Why stale

Parse shared spec coverage is active. The runner calls the Python host parse adapter directly. `spec/parse/` contains executable YAML cases.

### Required correction

Remove line 102. The surrounding context describes the five other active categories (eval, cli, flow, error, ir) with their comparison fields. The correction must add parse to that list or replace line 102 with an accurate statement.

Accurate statement for parse comparison:
```
- parse: normalized AST (exact match for `kind: ok`) or error type exact + message substring (for `kind: error`)
```

### Required phrase (for test assertion)

`docs/host-interop/HOST_INTEROP.md` must contain a statement that the runner provides parse coverage (e.g., `parse: normalized AST` or similar) in the comparison-fields block.

### Forbidden phrase (for test assertion)

`"This runner does not yet provide implemented shared case coverage for parse."` must not appear in `docs/host-interop/HOST_INTEROP.md`.

### Scope note

Lines 103–104 (other hosts not implemented, portability note) are accurate and must not change.

---

## Drift Item 3: `docs/cheatsheet/quick-reference.md` — Stale Header Comment

### Location

`docs/cheatsheet/quick-reference.md` line 1.

### Current stale text

```
# Note: Examples in this cheatsheet are validated by the Semantic Spec System where covered. Currently, only the eval category is active for executable shared spec files; other categories are scaffold-only. See GENIA_STATE.md for authoritative status.
```

### Why stale

Six categories are now active (`eval`, `ir`, `cli`, `flow`, `error`, `parse`). Saying "only the eval category is active" and "other categories are scaffold-only" is factually false for five of the six categories.

### Required correction

Replace the stale note with one that:
- Does not claim only eval is active.
- Accurately states that multiple categories are now active.
- Retains the pointer to `GENIA_STATE.md` for authoritative status.
- Remains a single-line comment header (matching existing style).

Acceptable replacement (exact wording to be finalized in the docs phase):
```
# Note: Examples in this cheatsheet are validated by the Semantic Spec System where covered. Active categories: eval, ir, cli, flow, error, parse (coverage varies by category). See GENIA_STATE.md for authoritative status.
```

### Required phrase (for test assertion)

`docs/cheatsheet/quick-reference.md` line 1 must not contain `"only the eval category is active"`.

### Forbidden phrase (for test assertion)

- `"only the eval category is active for executable shared spec files"` must not appear in `docs/cheatsheet/quick-reference.md`.
- `"other categories are scaffold-only"` must not appear in `docs/cheatsheet/quick-reference.md`.

### Scope note

The rest of the file content is unaffected by this correction. This is a one-line header fix only.

---

## Drift Item 4: `docs/cheatsheet/unix-power-mode.md` — Stale Header Comment

### Location

`docs/cheatsheet/unix-power-mode.md` line 1.

### Current stale text

```
# Note: Examples in this cheatsheet are validated by the Semantic Spec System where covered. Currently, only the eval category is active for executable shared spec files; other categories are scaffold-only. See GENIA_STATE.md for authoritative status.
```

### Why stale

Same reason as Drift Item 3. Six categories are now active.

### Required correction

Same pattern as Drift Item 3. Replace with a note that does not claim only eval is active and does not call other categories scaffold-only.

### Required phrase (for test assertion)

`docs/cheatsheet/unix-power-mode.md` line 1 must not contain `"only the eval category is active"`.

### Forbidden phrase (for test assertion)

- `"only the eval category is active for executable shared spec files"` must not appear in `docs/cheatsheet/unix-power-mode.md`.
- `"other categories are scaffold-only"` must not appear in `docs/cheatsheet/unix-power-mode.md`.

### Scope note

Line 2 onward (Python-host-only CLI/Flow note) is accurate and must not change.

---

## Drift Item 5: `docs/architecture/spec-phase-1-design.md` — Superseded Design Artifact

### Location

`docs/architecture/spec-phase-1-design.md` — entire file.

### Current stale content (summary)

The file header reads: `**Status:** Design artifact — no implementation yet.`

The body:
- Uses `spec/errors/` (now `spec/error/`), `spec/flows/` (now `spec/flow/`), `spec/parser/` (now `spec/parse/`) — all wrong directory names.
- Marks IR (`spec/ir/`), parse (`spec/parser/`), and flow (`spec/flows/`) as "Phase 2+" deferred.
- States explicitly: "No generic `tools/spec_runner/` runner implementation — Python runs its own adapter in its own test suite." — the generic runner now exists at `tools/spec_runner/`.
- Marks `spec/errors/` as a Phase 1 category under the wrong name.

### Why stale

This is a pre-implementation design artifact. Implementation proceeded with different directory naming conventions and broader scope than this document planned. The document is entirely superseded by actual implementation.

### Required correction

The document must NOT be deleted — it is a historical design record. Instead, add a **superseded notice** at the very top of the file (before the existing title/status block) that:
- States the document is superseded.
- Names the correct current directory conventions.
- Points to `GENIA_STATE.md` as the authoritative source.
- Does not alter the original body text (preserves historical record).

Required superseded notice (exact wording to be finalized in docs phase):

```markdown
> **SUPERSEDED — 2026-04-24**
> This design artifact predates the current implementation. Directory names used here
> (`spec/errors/`, `spec/flows/`, `spec/parser/`) have been replaced by the implemented
> names (`spec/error/`, `spec/flow/`, `spec/parse/`). IR, parse, flow, and the
> `tools/spec_runner/` runner are all now implemented. See `GENIA_STATE.md` §0–§1 for
> the authoritative current state.
```

### Required phrase (for test assertion)

`docs/architecture/spec-phase-1-design.md` must contain the word `SUPERSEDED` near the top (within the first 10 lines after any leading whitespace).

### Forbidden phrase (for test assertion)

No assertion should guard against the body content — the old text must remain intact as the historical record. The superseded notice is the only required addition.

### Scope note

Do not rewrite or delete any section of the original body. Only prepend the superseded notice.

---

## Guard Assertions for `tests/test_semantic_doc_sync.py`

Each drift correction above requires a corresponding guard assertion. The following are the new test cases to add in the test phase:

### Guard 1 — GENIA_STATE.md parse directory present

```python
def test_genia_state_limitations_includes_parse_directory() -> None:
    state = read_text("GENIA_STATE.md")
    # The Limitations section must list spec/parse/ alongside the other directories
    assert "spec/parse/" in state
```

### Guard 2 — GENIA_STATE.md stale parse claim removed

```python
def test_genia_state_does_not_claim_parse_not_yet_executed() -> None:
    state = read_text("GENIA_STATE.md")
    assert "does not yet execute parse categories as shared spec files" not in state
```

### Guard 3 — HOST_INTEROP.md stale parse claim removed

```python
def test_host_interop_does_not_claim_no_parse_coverage() -> None:
    text = read_text("docs/host-interop/HOST_INTEROP.md")
    assert "does not yet provide implemented shared case coverage for parse" not in text
```

### Guard 4 — Cheatsheets do not claim only eval is active

```python
@pytest.mark.parametrize("relpath", [
    "docs/cheatsheet/quick-reference.md",
    "docs/cheatsheet/unix-power-mode.md",
])
def test_cheatsheets_do_not_claim_only_eval_is_active(relpath: str) -> None:
    text = read_text(relpath)
    assert "only the eval category is active for executable shared spec files" not in text
    assert "other categories are scaffold-only" not in text
```

### Guard 5 — spec-phase-1-design.md carries superseded notice

```python
def test_spec_phase_1_design_carries_superseded_notice() -> None:
    text = read_text("docs/architecture/spec-phase-1-design.md")
    # SUPERSEDED notice must appear near the top
    assert "SUPERSEDED" in text[:500]
```

---

## Scaffold Directory Invariant (Must Not Change)

The following directories are correctly labeled scaffold-only and must remain so. No correction targets them:

| Directory | README status | Action |
|---|---|---|
| `spec/errors/` | "scaffold-only in this phase" | No change |
| `spec/flows/` | "scaffold-only in this phase" | No change |
| `spec/parser/` | "scaffold-only in this phase" | No change |
| `spec/pattern/` | "scaffold-only in this phase" | No change |

Any test assertion added must NOT accidentally flag these scaffold-only READMEs. Assertions must target the specific stale phrases in non-scaffold files listed above.

---

## `docs/contract/semantic_facts.json` — No Change Required

The current facts file guards pipeline/option semantics, host status, CLI dispatch, and naming rules. Spec-system category status is not a protected semantic fact at the `semantic_facts.json` level — it is a documentation accuracy concern guarded by the test assertions above. No new fact entry is needed.

---

## Files Affected in Later Phases

| Phase | File | Action |
|---|---|---|
| test | `tests/test_semantic_doc_sync.py` | Add Guards 1–5 above as failing tests |
| docs | `GENIA_STATE.md` lines 173–174 | Replace stale bullets |
| docs | `docs/host-interop/HOST_INTEROP.md` line 102 | Replace stale claim |
| docs | `docs/cheatsheet/quick-reference.md` line 1 | Replace stale header comment |
| docs | `docs/cheatsheet/unix-power-mode.md` line 1 | Replace stale header comment |
| docs | `docs/architecture/spec-phase-1-design.md` | Prepend superseded notice |
| audit | all of the above | Verify no remaining stale spec-system claims |

**GENIA_STATE.md is the final authority for implemented behavior. All other docs/specs must align with this contract.**
