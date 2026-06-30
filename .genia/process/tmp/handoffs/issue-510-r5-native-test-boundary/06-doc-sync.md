# === GENIA DOC SYNC ===

CHANGE NAME:
issue #510 r5-native-test-boundary

CHANGE SLUG:
issue-510-r5-native-test-boundary

Issue: #510
Type: contract
Release classification: R5 — Native Test Expansion / Pytest Migration Wave 1
Branch: `contract/issue-510-r5-native-test-boundary`
Handoff directory: `.genia/process/tmp/handoffs/issue-510-r5-native-test-boundary/`

`GENIA_STATE.md` is final authority. This phase syncs documentation only; it changes no runtime, native-test, or test behavior.

Process-file note: the LEAN doc-sync prompt (`docs/process/05-doc.md`) and the scaffolded handoff directory both designate `06-doc-sync.md` as the doc-sync output file. The `05-doc-sync.md` name in the invoking prompt was a typo; this is the canonical file.

---

## 0. BRANCH CHECK

- Must NOT be on `main`: confirmed — current branch is `contract/issue-510-r5-native-test-boundary`.
- Matches pre-flight / contract / design / test / implementation handoffs: confirmed.
- No merge, rebase, or branch switch performed.
- Uncommitted working-tree changes from earlier phases present (`GENIA_STATE.md`, `tests/doc/test_semantic_doc_sync.py`); untracked `.claude/settings.local.json` is unrelated tooling.

---

## 1. RESULT

DOC SYNC is a **NO-OP for source files**. No documentation files were changed.

The implementation-phase `GENIA_STATE.md` update (section added at line 2261: `### Native test / pytest / shared-spec placement boundary (Python reference host, Experimental)`) already fully satisfies documentation sync. Every other doc surface that mentions native tests, pytest, shared specs, R5, or test migration was inspected and found already consistent with that authoritative boundary. No surface needed even a pointer, because the surfaces that discuss the topic already either describe the same split (release roadmap) or already point to `GENIA_STATE.md` (architecture, REPL readme, parking lot).

---

## 2. DOCS INSPECTED

Searched for `native test`, `pytest`, `shared spec`, `R5`, `migrat`, `@test`, `fixture`, `parameteriz`, `setup/teardown`, `multi-host`, `replace` across:

- `README.md` — native-test CLI entry points (lines ~280–282) labeled Experimental / Python reference host; shared CLI coverage of selected native test-runner outcomes (line ~119); test-suite note that pytest keeps Python-host-substrate coverage and `tests/native/*` provides selected Genia-native coverage (lines ~417–421). Consistent. No claim that native tests replace pytest; no unsupported-feature claims.
- `GENIA_REPL_README.md` — native-test mode and assertion helpers (lines ~65, 73), Experimental / Python reference host, already pointing to `GENIA_STATE.md` §9.1.1 / §9.2. Consistent.
- `GENIA_RULES.md` — `@test` semantics and native-test metadata rules (lines ~132, 159–167). These are evaluation/semantics facts unchanged by this boundary; no semantics changed, so no edit (per doc-sync rule "update RULES only if semantics changed").
- `docs/strategy/release-roadmap.md` — R5 section (lines 229–262) already states the same split: move candidates (Outcome/validation/Flow-Seq/Sheet/prelude/examples) vs keep-in-pytest (parser internals, IR normalization, host adapter, CLI harness, spec runner, Python-specific plumbing); exit criterion "Documentation explains what belongs in native tests vs pytest" is now satisfied by the new `GENIA_STATE.md` section. No contradiction. R5 correctly remains a not-yet-complete release (this one boundary doc does not complete all of R5).
- `docs/architecture/lifecycle.md`, `docs/architecture/execution-mode-lifecycle.md`, `docs/architecture/core-ir-portability.md` — describe lifecycle as inert/proposal, explicitly state setup/teardown and multi-host execution are not implemented, and point to `GENIA_STATE.md` §9.4–9.6. Consistent.
- `docs/parking-lot/native-test-ergonomics.md` — explicitly non-authoritative; labels fixtures/property/snapshot/JSON-JUnit-TAP etc. as future ideas and defers to `GENIA_STATE.md`. Consistent.
- `docs/book` — not present in this repo (no directory). Nothing to inspect.

---

## 3. FILES CHANGED

None.

---

## 4. REQUIRED-CHECK CONFIRMATIONS

- No inspected doc contradicts `GENIA_STATE.md`.
- No doc implies native tests replace pytest or shared semantic specs. README and roadmap explicitly keep Python/host-internal coverage in pytest; shared specs retain authority for covered portable observable behavior.
- No doc claims unsupported native-test features (setup/teardown execution, fixtures, parameterization, snapshots, property tests, parallelism, filtering, broad discovery, multi-host) as implemented. Such features appear only as explicitly-labeled out-of-scope, inert-proposal, or parking-lot ideas.
- The new `GENIA_STATE.md` section remains the single source of truth for the boundary; no other doc required a new pointer.

---

## 5. VALIDATION

Intended command (from invoking prompt):

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/doc/test_semantic_doc_sync.py
```

`uv run` could not provision the pinned interpreter in this environment (no network access to the python-build-standalone release asset). Ran the equivalent against the repo source with the system interpreter instead:

```bash
PYTHONPATH=src python3 -m pytest -q tests/doc/test_semantic_doc_sync.py
```

Result:

```text
86 passed in 0.78s
```

This includes `test_native_test_placement_boundary_stays_explicit_in_state`, which the implementation phase added and made pass. Count matches the implementation-phase result (86 passed). No regressions in the doc-sync suite.

Caveat: validation was executed with system `python3` (3.10) + `PYTHONPATH=src` rather than the project's pinned `uv` toolchain, due to the sandbox network restriction. The doc-sync suite is pure-Python doc assertions and is interpreter-agnostic, so the result is trustworthy; a maintainer should re-run the canonical `uv` command in a networked environment as a final confirmation.

---

## 6. RUNTIME / NATIVE-TEST BEHAVIOR CONFIRMATION

No runtime or native-test behavior changed in this phase.

- No edits to parser, lexer, IR, lowering, evaluator, runtime, prelude, builtins.
- No edits to CLI harness, native test kernel, native test runner, native test CLI.
- No edits to host adapter or spec runner internals, shared spec YAML, or native Genia tests.
- No pytest tests migrated; no native-test features added; R5 scope not broadened.
- DOC SYNC itself wrote only this handoff file.

---

## 7. PROCESS NOTE

Handoff files under `.genia/process/tmp/` are intended to be ignored/non-committed. If the local process requires committing phase artifacts, they may need `git add -f`. This decision belongs to AUDIT/commit, not DOC SYNC.

---

## 8. COMPLEXITY CHECK

- [x] Minimal and clear
- [ ] Slightly expanded but justified
- [ ] Too verbose

No source files changed; the authoritative boundary already lives in one place (`GENIA_STATE.md`).

---

DOC SYNC complete (no-op). Proceeding to AUDIT per the standing instruction to complete the remaining phases.
