# Issue #152 — Spec-System Doc Sync: Design

**Phase:** design
**Branch:** issue-152-spec-system-doc-sync
**Issue:** #152 — Subtask for #116: Sync spec-system documentation with current shared spec reality
**Scope:** Documentation/spec sync only. No runtime behavior changes.

---

## Change Order

All changes in this issue are documentation corrections. The pipeline follows AGENTS.md discipline:

1. **test** — add five failing guard assertions to `tests/test_semantic_doc_sync.py`
2. **docs** — make the five documentation corrections; all five guards become passing
3. **audit** — verify no remaining stale spec-system claims; confirm full pytest + spec runner pass

No implementation phase (this issue has no runtime behavior changes).

---

## Phase: test

### File: `tests/test_semantic_doc_sync.py`

Append five new test functions after the last existing test (`test_runtime_pipe_mode_matches_documented_wrapper`).

These tests must **fail before** the docs phase edits and **pass after**.

#### Exact additions

```python
def test_genia_state_limitations_includes_parse_directory() -> None:
    state = read_text("GENIA_STATE.md")
    assert "spec/parse/" in state, (
        "GENIA_STATE.md Limitations section must list spec/parse/ alongside the other five directories"
    )


def test_genia_state_does_not_claim_parse_not_yet_executed() -> None:
    state = read_text("GENIA_STATE.md")
    assert "does not yet execute parse categories as shared spec files" not in state, (
        "GENIA_STATE.md must not claim the runner does not yet execute parse — parse is active"
    )


def test_host_interop_does_not_claim_no_parse_coverage() -> None:
    text = read_text("docs/host-interop/HOST_INTEROP.md")
    assert "does not yet provide implemented shared case coverage for parse" not in text, (
        "HOST_INTEROP.md must not claim no parse coverage — parse is active"
    )


@pytest.mark.parametrize("relpath", [
    "docs/cheatsheet/quick-reference.md",
    "docs/cheatsheet/unix-power-mode.md",
])
def test_cheatsheets_do_not_claim_only_eval_is_active(relpath: str) -> None:
    text = read_text(relpath)
    assert "only the eval category is active for executable shared spec files" not in text, (
        f"{relpath} must not claim only eval is active — six categories are now active"
    )
    assert "other categories are scaffold-only" not in text, (
        f"{relpath} must not claim other categories are scaffold-only — five others are active"
    )


def test_spec_phase_1_design_carries_superseded_notice() -> None:
    text = read_text("docs/architecture/spec-phase-1-design.md")
    assert "SUPERSEDED" in text[:500], (
        "spec-phase-1-design.md must carry a SUPERSEDED notice within the first 500 characters"
    )
```

#### Placement

Append directly after the last line of the file (after `assert captured.out == "a\n"`). No other changes to `tests/test_semantic_doc_sync.py`.

---

## Phase: docs

Five edits across six files. Order does not matter for correctness; apply all five before committing.

---

### Edit 1 — `GENIA_STATE.md` lines 173–174

**Current text (exact):**
```
- Shared semantic-spec case files exist under `spec/eval/`, `spec/ir/`, `spec/cli/`, `spec/flow/`, and `spec/error/` in this phase.
- The current shared semantic-spec runner does not yet execute parse categories as shared spec files.
```

**Replacement text (exact):**
```
- Shared semantic-spec case files exist under `spec/eval/`, `spec/ir/`, `spec/cli/`, `spec/flow/`, `spec/error/`, and `spec/parse/` in this phase.
- Parse shared semantic-spec coverage is initial only; coverage expands only when new forms are explicitly added and tested.
```

**Why:** Line 173 omits `spec/parse/`. Line 174 directly contradicts the authoritative lines 18–19 and 154 of the same file. The replacement bullet restates the accurate initial-coverage qualifier from the authoritative section.

**Invariant check:** Lines 170–172 and 176 must remain unchanged.

---

### Edit 2 — `docs/host-interop/HOST_INTEROP.md`

**Current text (lines 88–102, exact change target):**

Lines 90–92:
```
The Python host adapter exposes a single `run_case(case: SpecCase) -> SpecResult` entrypoint. In the current implemented shared semantic-spec system, the shared runner executes `eval`, `ir`, `cli`, `flow`, and initial `error` cases.

The shared spec runner loads YAML eval, cli, flow, error, and IR cases, executes them against the Python reference host, and compares:
```

Lines 94–102:
```
- eval: normalized `stdout`, normalized `stderr`, and `exit_code`
- cli: normalized `stdout`, normalized `stderr`, and `exit_code`
- flow: normalized `stdout`, normalized `stderr`, and `exit_code`
- error: normalized `stdout`, normalized `stderr`, and `exit_code`
- ir: normalized portable Core IR output

- Error specs reuse eval execution; there is no separate error execution path in the runner.
- Error `notes` are informational only and are not machine-asserted.
- This runner does not yet provide implemented shared case coverage for parse.
```

**Replacement text (lines 90–102):**

Replace lines 90–92 with:
```
The Python host adapter exposes a single `run_case(case: SpecCase) -> SpecResult` entrypoint. In the current implemented shared semantic-spec system, the shared runner executes `eval`, `ir`, `cli`, `flow`, initial `error`, and initial `parse` cases.

The shared spec runner loads YAML eval, cli, flow, error, IR, and parse cases, executes them against the Python reference host, and compares:
```

Replace lines 94–102 with:
```
- eval: normalized `stdout`, normalized `stderr`, and `exit_code`
- cli: normalized `stdout`, normalized `stderr`, and `exit_code`
- flow: normalized `stdout`, normalized `stderr`, and `exit_code`
- error: normalized `stdout`, normalized `stderr`, and `exit_code`
- ir: normalized portable Core IR output
- parse: normalized AST (exact match for `kind: ok`) or error type exact + message substring (for `kind: error`)

- Error specs reuse eval execution; there is no separate error execution path in the runner.
- Error `notes` are informational only and are not machine-asserted.
- Parse specs call the Python host parse adapter directly; no subprocess is invoked.
```

**Why:** Adds parse to the runner description, the case-list, and the comparison-fields list. Removes the false "does not yet" claim. Replaces it with an accurate parse execution note.

**Invariant check:** Lines 103–104 (other hosts not implemented, portability note) must remain unchanged.

---

### Edit 3 — `docs/cheatsheet/quick-reference.md` line 1

**Current text (exact):**
```
# Note: Examples in this cheatsheet are validated by the Semantic Spec System where covered. Currently, only the eval category is active for executable shared spec files; other categories are scaffold-only. See GENIA_STATE.md for authoritative status.
```

**Replacement text (exact):**
```
# Note: Examples in this cheatsheet are validated by the Semantic Spec System where covered. Active categories: eval, ir, cli, flow, error, parse (coverage varies by category). See GENIA_STATE.md for authoritative status.
```

**Why:** Six categories are now active. The old claim that only eval is active and others are scaffold-only is false for five of six categories.

**Invariant check:** Line 2 onward must remain unchanged.

---

### Edit 4 — `docs/cheatsheet/unix-power-mode.md` line 1

**Current text (exact):**
```
# Note: Examples in this cheatsheet are validated by the Semantic Spec System where covered. Currently, only the eval category is active for executable shared spec files; other categories are scaffold-only. See GENIA_STATE.md for authoritative status.
```

**Replacement text (exact):**
```
# Note: Examples in this cheatsheet are validated by the Semantic Spec System where covered. Active categories: eval, ir, cli, flow, error, parse (coverage varies by category). See GENIA_STATE.md for authoritative status.
```

**Why:** Same reason as Edit 3.

**Invariant check:** Line 2 onward (Python-host-only CLI/Flow disclaimer) must remain unchanged.

---

### Edit 5 — `docs/architecture/spec-phase-1-design.md`

**Current text (lines 1–7, exact):**
```
# Shared Conformance Cases — Phase 1: Design Note

**Status:** Design artifact — no implementation yet.
**Date:** 2026-04-16
**Author:** Spec planning prompt

---
```

**Replacement text (lines 1–7):**

Prepend the superseded notice block before the existing title, then keep all existing content unchanged:

```
> **SUPERSEDED — 2026-04-25**
> This design artifact predates the current implementation. Directory names used here
> (`spec/errors/`, `spec/flows/`, `spec/parser/`) have been replaced by the implemented
> names (`spec/error/`, `spec/flow/`, `spec/parse/`). IR, parse, flow, and the
> `tools/spec_runner/` runner are all now implemented. See `GENIA_STATE.md` §0–§1 for
> the authoritative current state.

# Shared Conformance Cases — Phase 1: Design Note

**Status:** Design artifact — no implementation yet.
**Date:** 2026-04-16
**Author:** Spec planning prompt

---
```

**Why:** Preserves the full historical record while making the superseded status immediately visible. Does not alter any body content.

**Invariant check:** Every line after the `---` separator must remain byte-for-byte identical to the current file.

---

## Commit Message for test Phase

```
test(docs): add failing guards for spec-system doc accuracy issue #152
```

## Commit Message for docs Phase

```
docs(spec): fix stale spec-system documentation issue #152
```

---

## Verification Checklist (for audit phase)

After the docs phase commit, verify:

- [ ] `uv run pytest tests/test_semantic_doc_sync.py` — all five new guards pass
- [ ] `uv run pytest -q --maxfail=1` — full suite passes
- [ ] `uv run python -m tools.spec_runner` — spec runner passes
- [ ] `grep "does not yet execute parse" GENIA_STATE.md` — no output
- [ ] `grep "does not yet provide implemented shared case coverage for parse" docs/host-interop/HOST_INTEROP.md` — no output
- [ ] `grep "only the eval category is active" docs/cheatsheet/quick-reference.md docs/cheatsheet/unix-power-mode.md` — no output
- [ ] `head -3 docs/architecture/spec-phase-1-design.md` — shows SUPERSEDED
- [ ] `spec/errors/README.md`, `spec/flows/README.md`, `spec/parser/README.md`, `spec/pattern/README.md` — unchanged (scaffold-only labels intact)

---

**GENIA_STATE.md is the final authority for implemented behavior. All other docs/specs must align with this contract.**
