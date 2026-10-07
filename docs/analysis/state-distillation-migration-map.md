# GENIA_STATE.md distillation: migration ledger and dry-run (#1099 PR B, phase 4a)

Status: **phase 4a review artifact, 2026-10-07.** Non-authoritative planning/audit record;
`GENIA_STATE.md` is final authority. **No STATE content has moved.** This phase only
measures, classifies, and proposes. Baseline: `GENIA_STATE.md` at `d401f322` (the merge of
PR A / #1100), 6,960 lines, 72,919 words.

Machine-readable sources (guarded by `tests/doc/test_state_migration_map.py`):
`docs/analysis/state-distillation-migration-map.json` (the ledger),
`docs/analysis/state-distillation-baseline-identifiers.json` (3,151 distinct backtick
identifiers), and `tools/state_inventory.py` (inventory generator).

## 1. Method

- **Partition.** Every baseline line belongs to exactly one of 322 rows: one row per
  short section, or contiguous sub-blocks (split at top-level bullets/paragraphs, merged
  to at least 14 lines) for the 35 sections longer than 70 lines. The guard proves rows
  are contiguous and non-overlapping and, while STATE is still the baseline, that they
  match the live file.
- **Dispositions** (exactly one per row): `retained` (unchanged), `retained-condensed`
  (stays in STATE, narrative removed, behavior claims kept), `moved` (leaves STATE; STATE
  keeps at most a digest), `redundant`, `obsolete`. This dry run assigns no whole row to
  `redundant`: the identifier-overlap figures recorded per row are weak evidence (generic
  identifiers match README/AGENTS), so redundancy is not claimed from them. `obsolete` is
  recorded for two individual *statements* with evidence (section 6), not whole rows.
- **Verbatim records, not deletion.** Every `moved` and `retained-condensed` row names a
  destination under a new `docs/state-record/` directory (ten files, section 3). In phase
  4b each such row is copied **byte-for-byte** into its record under a provenance line
  (`Moved from GENIA_STATE.md@d401f322, lines a-b`) before STATE is touched. Condensing in
  4c is then reviewable as "claims kept" against the preserved full text, and git history
  is no longer the only place old text lives. Records are marked non-authoritative.
- **No unexplained bucket.** There is no "deleted" disposition; a row with no disposition,
  or a moved/condensed row with no destination, fails the guard.

## 2. Roll-up by region

| Region | Baseline lines | Words | Est. retained lines | Est. words |
|---|---:|---:|---:|---:|
| Title | 4 | 20 | 4 | 20 |
| 0, 0.1, 1 (conformance): hosts and conformance | 349 | 4,463 | 206 | 2,490 |
| 0.2–0.4: doc tooling | 92 | 737 | 0 | 0 |
| 1 (execution model), 2 (value categories), 3 (syntax) | 675 | 11,725 | 482 | 6,750 |
| 4.x functions, interop, open functions | 421 | 3,035 | 394 | 2,826 |
| 5 patterns | 190 | 3,634 | 174 | 3,088 |
| 6 builtins | 1,640 | 16,838 | 1,413 | 14,128 |
| 7–9 stdlib, TCO, debug, native-test boundaries | 158 | 1,731 | 158 | 1,731 |
| 9.1–9.6 native test + lifecycle shapes | 238 | 3,183 | 142 | 1,898 |
| 9.7 R8 server contract | 76 | 2,131 | 50 | 1,383 |
| 9.8–9.20 R14 lifecycle/HTTP | 1,016 | 8,016 | 0 | 0 |
| 9.21–9.37 R21–R23 numerics | 1,041 | 7,605 | 0 | 0 |
| 9.38–9.39 provider proofs | 237 | 1,754 | 0 | 0 |
| 9.40 external process | 170 | 1,228 | 118 | 854 |
| 9.41–9.51 R28 MCP | 565 | 5,625 | 136 | 1,443 |
| 10 not implemented | 10 | 106 | 10 | 106 |
| 11 demos | 78 | 1,088 | 0 | 0 |
| **Rows total** | **6,960** | **72,919** | **3,287** | **36,717** |

Dispositions: 67 `retained` rows (1,453 lines), 129 `retained-condensed` (2,640 lines),
126 `moved` (2,867 lines). Retained-row estimates use a mechanical rule recorded in the
JSON: ticket/issue-dense rows (four or more `E##-#`/`#NNN` tags) keep 30–60% of their lines
depending on group; other rows keep 60–100%.

**New STATE text (digests, to be written in 4c):** D1 navigation index and authority
statement (45 lines); D2 host matrix and conformance-protocol digest (40); D3 R14
lifecycle/HTTP digest (150); D4 R21/R22 exact-numeric digest (110); D5 R23 rendering/JSON
digest (80); D6 provider-proof digest (25); D7 R28 MCP lifecycle digest (45); D8
tooling/examples pointers (10). Total 505 lines.

## 3. Verbatim-record destinations (`docs/state-record/`)

| Record | Rows | Lines | Words | Source |
|---|---:|---:|---:|---|
| `hosts-and-conformance.md` | 12 | 264 | 3,589 | section 0 R16/R26/R27 chronology, section 1 conformance detail |
| `tooling-and-examples.md` | 9 | 170 | 1,825 | 0.2–0.4 doc tooling, 11 demos |
| `capability-records.md` | 24 | 480 | 10,434 | runtime capability values (R10–R14 tickets), 4.7 R20, ticket-tagged pattern/Template blocks |
| `builtin-records.md` | 56 | 1,081 | 11,437 | condensed builtin sections (R17–R19 portability, validation helpers, Option model, bridges, etc.) |
| `server-and-process-records.md` | 26 | 415 | 5,705 | CORS wrapper, 9.7 R8 server, 9.40 process |
| `native-test-and-lifecycle-shape-records.md` | 7 | 238 | 3,183 | 9.1–9.6 |
| `r14-lifecycle-http-records.md` | 54 | 1,016 | 8,016 | 9.8–9.20 |
| `numeric-r21-r23-records.md` | 37 | 1,041 | 7,605 | 9.21–9.37 |
| `provider-proof-records.md` | 7 | 237 | 1,754 | 9.38–9.39 |
| `r28-mcp-records.md` | 23 | 565 | 5,625 | 9.41–9.47 history, condensed 9.48–9.51 |

Each record is linked from the matching `docs/releases/R*.md` page (R10–R14, R17–R23,
R26–R28 as applicable) and from STATE digest D1. Open question Q1 asks whether to append
into the release pages instead.

## 4. Dry-run size model and the target

Model total = rows 3,287 + digests 505 = **3,792 lines (-45.5%)** and about **41,800 words
(-42.7%)**.

The pre-flight proposed an acceptance ceiling of ≤3,000 lines / ≤35,000 words. **The
dry run does not support that ceiling** under a semantics-preserving model: even with all
R14/R21–R23/provider/R28 narrative moved, the remaining core language, value model, and
builtin contracts total about 3,300 lines. The largest remaining mass is section 6
(1,413 est. lines, 14,128 words) and the pure language core (title, execution model, value
categories, syntax, functions, patterns, 7–9: about 1,200 lines).

Recommendation (Q2): **ratify a ceiling of ≤3,900 lines and ≤43,000 words** (about -44%
lines, -41% words) as the PR B acceptance bound, with structural bounds unchanged (zero
`E##-#` headings, `#NNN` references ≤60, no pass/total-count phrases, no pinned evidence
commit hashes). A **stretch** of ≤3,300 lines is reachable only by cutting section 6 to
about 900 lines, i.e. leaving per-builtin examples to the generated function reference
(`docs/reference/`) for prelude functions that already carry `@doc`; that is a semantic-
detail decision and is not assumed here.

## 5. Proposed outline of the distilled STATE

Section numbers listed are retained as legacy identifiers where they exist today (the MCP
wire's legacy `state_sections` values and ~150 inbound references depend on 0, 0.1, 1, 5, 8,
9.48, 9.49, 9.50); **anchors, not numbers, are the identities**.

0. Authority, scope, and navigation (`state:host-status` retained; D1 index with pointers to every record, release page, and contract)
0.1 Browser/playground status (`state:browser`)
1. Hosts, portability, and shared conformance (digest D2 + retained limitations; `state:conformance`); Execution model (`state:execution-model`) — duplicate heading number `1` stays until 4c, then the second is renumbered with a crosswalk row
2. Runtime value categories (retained; ticket narrative condensed)
3. Syntax and expression forms (`state:syntax-forms`); shell stage
4. Functions and dispatch; 4.1 interop; 4.1 symbols (duplicate number resolved in 4c); 4.2–4.6; 4.7 open functions (`state:open-functions`)
5. Case expressions and pattern matching (`state:pattern-matching`, `state:control-flow`)
6. Builtins (condensed contracts; ticket/issue narrative removed)
7. Autoloaded stdlib; 8. Tail calls (`state:tail-calls`); 9. Debug/runtime tooling and native-test boundaries
9.1–9.6 Native test and lifecycle data shapes (condensed)
9.7 R8 server execution contract (heading and pinned subheadings frozen)
9.8–9.20 → **one digest**: lifecycle and outbound HTTP (D3), legacy numbers listed in the crosswalk
9.21–9.37 → **two digests**: exact numerics R21/R22 (D4) and rendering/JSON R23 (D5)
9.38–9.39 → one digest (D6)
9.40 External direct process execution (condensed)
9.41–9.47 → digest (D7); **9.48, 9.49, 9.50 retained as headings** with their anchors (`state:mcp-macos`, `state:mcp-surface`, `state:mcp-language-profile`); the 12-row table in 9.50 becomes a pointer to the registry in 4c; 9.51 condensed
10. Explicitly not implemented (current)
11. Retired: pointer to the examples record

## 6. Superseded statements (recorded evidence, removed in 4c)

1. Section 0 "Explicit limitations", first bullet (baseline line 75): "`m0smith/genia-cpp`
   is the R25-complete second production host for the bounded floor recorded above" is
   superseded by the section 0 opening statement (line 10: C++ is the bounded R27
   production host), semantic fact `host_status`, and `spec/manifest.json` `host_status`.
2. Section 10 (baseline line 6592): the E28-3 "acceptance-gate-open" parenthetical is
   superseded by section 9.49 (R28 completion with authentic acceptance).

The original text of both remains in `hosts-and-conformance.md` and `server-and-process-records.md`
respectively until reviewers confirm the removal.

## 7. Test-pinned content

An automated scan (string constants of at least 18 characters in the 28 test modules that
read STATE, matched against STATE text) marks **82 rows** as pinned by 17 test modules
(listed in the JSON per row). **17 `moved` rows are pinned** (R14 headings/phrases used by
`test_r8_server_contract_sync.py` and `test_semantic_doc_sync.py`, the 9.25 heading, the
MCP tool-set sentence, `test_r28_release_gate.py`'s 9.44 heading). Each carries a
`pin_action`: keep the pinned sentence in the digest, or retarget the test to the
destination record in the same PR. The scan is approximate and is re-run in 4b.

## 8. Gates for 4b/4c (restated, now concrete)

1. **Partition gate** (done in 4a): `tests/doc/test_state_migration_map.py`.
2. **Verbatim gate (4b):** every `moved`/`retained-condensed` row appears byte-identical,
   contiguous, in its record, with a provenance line.
3. **Identifier gate:** every one of the 3,151 baseline identifiers appears in distilled
   STATE or in a record; the unexplained set must be empty and is printed on failure.
4. **Pin gate:** every pinned string still appears in STATE, or its test is retargeted and
   the change recorded in the ledger.
5. **Anchor/wire gate:** the 12 anchors resolve; the registry crosswalk legacy numbers stay
   valid; `gen_mcp_language_profile.py --check` and the golden snapshot still pass.
6. **Link gate:** each `GENIA_STATE.md ... section N` reference resolves via a retained
   heading or a crosswalk row.
7. **Scope gate:** the PR touches no file under `src/`, `hosts/`, `spec/`, or
   `apps/mcp/mcp.genia`.
8. **Size gate** (after ratification): lines/words and the structural bounds in section 4.

## 9. Decisions requested

- **Q1.** Verbatim records in a new `docs/state-record/` directory (recommended: lossless,
  navigable, keeps release pages short) versus appending into `docs/releases/R*.md`.
- **Q2.** Ratify the revised bound (≤3,900 lines / ≤43,000 words) in place of ≤3,000/≤35,000,
  and whether to pursue the section 6 stretch.
- **Q3.** Approve removal of the two superseded statements in section 6.
- **Q4.** For the 17 pinned `moved` rows: prefer keeping the pinned sentence in the digest
  (recommended) or retargeting the test.
- **Q5.** Approve digests D1–D8 as the only new STATE text.

## 10. Not done in 4a

No STATE edit, no record file, no test retargeting, no heading renumbering, no change to
`apps/mcp/mcp.genia` or the registry. Phase 4b begins only after this ledger is approved.
