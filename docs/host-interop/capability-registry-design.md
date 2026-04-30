# Design: Host Capability Registry Contract
# Issue #118 — Design Phase

**Branch:** docs/host-capability-registry-contract
**Spec:** docs/host-interop/capability-registry-spec.md
**Authority:** GENIA_STATE.md is the final authority for all behavioral claims.

No code here. No implementation. No scope expansion.

---

## 1. PURPOSE

Translate the capability registry spec into a concrete file layout, document format, test additions, and implementation order. The design answers two deferred questions from the spec: document format and validation layer.

---

## 2. SCOPE LOCK

Follows spec exactly. No new behavior added.

**Design resolves two spec-deferred decisions:**

| Decision | Resolution | Rationale |
|---|---|---|
| Document format | Markdown with per-capability bullet-list template | Consistent with existing host-interop docs; human-readable; machine-checkable by string matching |
| Validation layer | Lightweight string-based doc-sync tests added to `tests/test_semantic_doc_sync.py` | Matches existing test pattern; no schema format needed; minimal scope |

No YAML schema file, no Python validation registry, no new test framework. Those are deferred.

---

## 3. ARCHITECTURE OVERVIEW

This change is entirely in the **Docs / Tests** zone (AGENTS.md four-zone model). It does not cross into Language Contract, Core IR, or Host Adapters.

```
docs/host-interop/capabilities.md        ← new: primary deliverable
tests/test_semantic_doc_sync.py          ← modified: adds invariant checks
docs/host-interop/HOST_CAPABILITY_MATRIX.md  ← modified: adds reference
docs/host-interop/README.md              ← modified: adds to start-here list
GENIA_STATE.md §0                        ← modified: records registry exists
```

No files in `src/genia/`, `hosts/python/`, or `spec/` change.

---

## 4. FILE / MODULE CHANGES

### New files

**`docs/host-interop/capabilities.md`**
- The primary deliverable.
- Contains the maturity notice, portability vocabulary table, and all 29 capability entries across 7 groups.
- Authoritative reference for capability names, input/output shapes, error behavior, and portability status.

### Modified files

**`tests/test_semantic_doc_sync.py`**
- Add one new test function: `test_capability_registry_invariants`.
- Checks all 12 spec invariants by string matching against `docs/host-interop/capabilities.md`.
- Follows the existing pattern: `read_text(relpath)` + `assert "..." in text`.

**`docs/host-interop/HOST_CAPABILITY_MATRIX.md`**
- Add one sentence in the opening section referencing `capabilities.md` as the per-capability contract source.
- No row changes in this phase; the matrix rows already reflect the correct status.

**`docs/host-interop/README.md`**
- Add `capabilities.md` as the first entry in the "Start here" list with description: "formal per-capability contract reference (name, input, output, errors, portability status)".

**`GENIA_STATE.md` §0**
- Add one bullet point under "Implemented today": formal capability registry contract documented at `docs/host-interop/capabilities.md`.
- Must be in the multi-host status section because that is where Python-host-only vs language contract status is tracked.

### Removed files

None.

---

## 5. DATA SHAPES

### Capability entry template (markdown)

Each capability entry in `capabilities.md` uses this exact layout:

```
#### `<name>`

- **name:** `<dotted-name>`
- **genia_surface:** `<surface>` [, `<surface>`, ...]
- **input:** <Genia type description — no Python types>
- **output:** <Genia type description — no Python types>
- **errors:**
  - `<ErrorCategory>` — <trigger condition and normalized message prefix>
  - (or: none defined)
- **portability:** `<language contract | Python-host-only | not implemented>`
- **notes:** <optional short clarification> (omit line if empty)
```

Rules enforced by this template:
- `name` always uses backtick quoting
- `portability` always uses one of the three spec-defined terms in backticks
- `errors` section always present, even if value is "none defined"
- `notes` line omitted entirely when there is nothing to say (not written as empty or "N/A")

### Document structure

```
# Host Capability Registry Contract

<maturity notice>

## Portability Status Terms

<vocabulary table>

## Capability Groups

### Group: I/O Substrate

#### `io.stdout`
...

#### `io.stderr`
...

#### `io.stdin`
...

### Group: Time / Sleep

#### `time.sleep`
...

### Group: Randomness

#### `random.rng`
...

[remaining groups in §5 of spec order]
```

Section heading format for groups: `### Group: <Group Name>`
Section heading format for entries: `#### \`<name>\``

This structure lets the doc-sync test verify capability presence with simple `assert "\`io.stdout\`" in text`.

---

## 6. TEST DESIGN (for test phase)

### Function: `test_capability_registry_invariants`

Location: `tests/test_semantic_doc_sync.py`

The test reads `docs/host-interop/capabilities.md` once and asserts all 12 invariants from the spec.

**Invariant checks mapped to assertions:**

| Invariant | Assertion type |
|---|---|
| 1. All 29 capability names present | `assert "\`<name>\`" in text` for each name |
| 2. All entries have required fields | `assert "- **portability:**" in text` (count ≥ 29); similar for other required fields |
| 3. Portability values are only the three allowed terms | `assert "portability: \`language contract\`" or "portability: \`Python-host-only\`" or "portability: \`not implemented\`" — no other portability value appears |
| 4. No Python class names | `assert "src/genia/" not in text`; `assert "interpreter.py" not in text` |
| 5. No unimplemented behaviors described as current | checked via prohibited phrasings |
| 6. No non-Python host claims implementation | `assert "Node.js: Implemented" not in text` (etc.) — this is weaker; primary guard is Invariant 3 + status terms |
| 7. language contract entries in HOST_CAPABILITY_MATRIX as Implemented | separate assertion on HOST_CAPABILITY_MATRIX.md |
| 8. Python-host-only entries in HOST_CAPABILITY_MATRIX as Python-host-only | separate assertion on HOST_CAPABILITY_MATRIX.md |
| 9. No prohibited phrasings | `assert "will be implemented" not in text`, etc. |
| 10. No future-tense phrases in contracts | `assert "coming soon" not in text`; "planned" not in contract field lines |
| 11. Structured absence distinguished from error raises | presence of `none("json-parse-error"` in json.parse entry and absence of "raises" in the same entry |
| 12. No language semantics in doc | `assert "Core IR" not in text`; `assert "IrPipeline" not in text` |

**Failing state before implementation phase:** The test will fail immediately at the file read because `docs/host-interop/capabilities.md` does not exist yet.

### Existing tests: no regression expected

No existing test assertions change. The new function is additive.

---

## 7. IMPLEMENTATION ORDER (TDD)

Phase ordering matters. The test phase must produce failing tests before the implementation phase writes the document.

**Test phase commit (tests fail — capabilities.md does not exist):**
1. Add `test_capability_registry_invariants` to `tests/test_semantic_doc_sync.py`.

**Implementation phase commits (tests pass):**
1. Write `docs/host-interop/capabilities.md` (all 29 capability entries).
2. Update `docs/host-interop/README.md` (add capabilities.md to start-here list).
3. Update `docs/host-interop/HOST_CAPABILITY_MATRIX.md` (add cross-reference).
4. Update `GENIA_STATE.md` §0 (add registry bullet point).

All four implementation changes may land in one commit because they are jointly required to satisfy all 12 invariants. If the test phase verifies invariants 7 and 8 against HOST_CAPABILITY_MATRIX.md, that file must also be in place before the test can pass.

---

## 8. ERROR HANDLING DESIGN

No runtime error handling is introduced. This is a docs-only change.

For the doc-sync test:
- If `capabilities.md` is missing → `FileNotFoundError` from `Path.read_text` → test fails with clear path message.
- If an invariant string is absent → `AssertionError` with the failing assertion visible in pytest output.
- No try/except needed; pytest handles both.

---

## 9. INTEGRATION POINTS

| System | Interaction |
|---|---|
| `tests/test_semantic_doc_sync.py` | New function added; existing functions untouched |
| `docs/host-interop/HOST_CAPABILITY_MATRIX.md` | Cross-reference sentence added; rows unchanged |
| `docs/host-interop/README.md` | One list entry added |
| `GENIA_STATE.md §0` | One bullet point added under "Implemented today" |
| `src/genia/`, `hosts/python/`, `spec/` | No changes |
| CI (pytest -q) | New test runs; must pass before merge |

---

## 10. DOC IMPACT

**`GENIA_STATE.md` §0 addition (exact required wording):**

```
- A formal host capability registry contract is documented at
  `docs/host-interop/capabilities.md`. It is the authoritative reference
  for capability names, Genia surface, input/output shapes, normalized error
  behavior, and portability status for each host capability.
```

**`docs/host-interop/README.md` addition (exact required wording):**

```
- `capabilities.md` for the formal per-capability contract
  (name, Genia surface, input, output, errors, portability status)
```

This entry goes before the existing `HOST_INTEROP.md` entry so it is the first reference.

**`docs/host-interop/HOST_CAPABILITY_MATRIX.md` addition (exact required wording):**

In the opening section, after the status legend, before the browser playground note:

```
For the formal per-capability contract (input shapes, output shapes,
normalized error behavior, and portability status), see
`docs/host-interop/capabilities.md`.
```

---

## 11. CONSTRAINTS

Must:
- Follow existing markdown conventions in `docs/host-interop/`
- Follow existing test patterns in `test_semantic_doc_sync.py` (string matching, `read_text`, `normalize`)
- Use only Genia type names in capability contracts (no Python types)
- Keep capabilities.md truthful: all claims grounded in GENIA_STATE.md

Must not:
- Add a YAML schema file
- Add a Python validation registry or dataclass
- Modify any runtime file
- Add shared spec YAML cases
- Describe future hosts as implemented
- Change any existing test assertion

---

## 12. COMPLEXITY CHECK

[x] Minimal
[x] Necessary

The primary deliverable (capabilities.md) is a single markdown document. The test addition is one function using existing patterns. Three small edits to existing docs. This is the minimum that satisfies all 12 spec invariants with a verifiable artifact.

The validation layer stays at its simplest possible form: string-based doc-sync assertions. No schema, no reflection, no runtime hooks. This matches the "keep it tiny" directive from the pre-flight.

---

## 13. FINAL CHECK

- [x] Matches spec exactly — all 29 capabilities covered; all 12 invariants mapped to concrete test assertions
- [x] No new behavior introduced — docs-only change; no runtime modifications
- [x] Structure is clear and implementable — template defined, file locations defined, exact wording for related-file updates defined
- [x] TDD order preserved — test phase commits failing test before implementation phase writes capabilities.md
- [x] Existing tests not broken — new function is additive only
- [x] Validation layer is minimal — string matching in existing test file; no schema format
- [x] Ready for test phase — `test_capability_registry_invariants` definition is fully specified above
