# GENIA Change Pre-Flight: STATE distillation and structural MCP language-knowledge synchronization (#1099)

Status: **Pre-flight only, 2026-10-07.** Decision: **GO WITH CONDITIONS** (section 12).
Nothing in this document is implemented. `GENIA_STATE.md` remains final authority;
this file is a design record, not a language contract. No runtime, MCP, STATE, or
test file was changed to produce it. Measurements were taken against
`origin/main` at `f75c166`.

## Change identity

- **Change name:** distill `GENIA_STATE.md`; synchronize MCP language knowledge structurally
- **Release / issue:** R28 follow-up governance/hardening, #1099 (siblings: #1085 classification, #1086 A7 discovery, #1087 grounded example)
- **Proposed branch:** `issue-1099-state-distillation-mcp-sync` (this pre-flight was produced on `claude/issue-1099-preflight-pm2cgg`)
- **Owner:** repository owner

## Review decision (2026-10-07): GO to PR A with one amendment

The owner approved C1–C7, Option 1 (extend `semantic_facts.json`), and the two-PR
sequence (PR A: sync architecture; PR B: STATE distillation), and directed **stopping
after PR A** for review before any STATE surgery. One amendment **supersedes** earlier
text in this document where they conflict:

1. **Semantic anchors replace section numbers as identities.** Section numbers are not
   the long-term stable identifiers (this supersedes "section numbers are stable
   identifiers" in Part B/Part H and condition C3's renumbering/duplicate-number plan).
   PR A introduces semantic anchor IDs (`state:control-flow`, `state:pattern-matching`,
   `state:tail-calls`, `state:host-status`, `state:mcp-surface`, ...) placed in STATE
   independently of presentation numbering. The registry points at anchors. The legacy
   wire values (`"5"`, `"9.50"`, ...) are kept for R28 byte-compatibility through an
   explicit anchor-to-legacy-section crosswalk, so PR B may reorganize STATE freely.
   Duplicate heading numbers (`1`, `4.1`) are no longer an identity problem because
   anchors disambiguate them; renumbering is deferred to PR B.
2. **Three layers: semantic anchor → structured fact → evidence.** The fact's identity
   is its stable semantic ID plus its anchor, not its prose. Evidence is one or more
   verification mechanisms: a STATE text fragment that shows STATE explicitly states
   the fact, an executable probe, or a machine-truth cross-check. This supersedes
   "pins must be verbatim STATE text" as the identity rule; text fragments are
   verification, so wording improvements re-pin a fragment without changing the fact.
3. **C4 is mandatory in PR A.** STATE states, independently of the MCP sections, that
   there is no `if` form, no dedicated loop syntax, and that repetition is recursion
   with tail-call optimization.

PR A implementation record: `docs/design/r28-follow-up-1099-registry-contract.md`
(contract) and `docs/design/r28-follow-up-1099-registry-design.md` (design).

## Summary of findings

1. **STATE is 6,932 lines / 72,424 words / 572 KB, but the bloat is concentrated.**
   Sections 9.7–9.51 (per-ticket release/proof narratives, including a few current
   contracts) are 3,092 lines (44.6%); section 6 (builtins) is 1,640 lines (23.7%);
   section 2 (value categories) is 540 lines (7.8%). Sections 0–0.4 mix current host
   status with R16 chronology, test counts, and documentation-tooling process. The
   syntax, dispatch, pattern, and value-model core (sections 2–5, 7–10) is about
   1,440 lines (21%).
2. **`semantic_facts.json` is a selective drift guard, not a definition, and its
   schema cannot express the MCP projection as-is.** It is a flat map of 22
   sentence-valued keys, frozen by an exact-key-set test and a `<= 22` cap. It has no
   status, scope, maturity, or STATE-anchor fields. It can be extended additively.
3. **`genia_language_profile` holds the same facts in at least five places** (the
   native constants in `apps/mcp/mcp.genia`, the pasted wire oracle in
   `tests/unit/test_r28_mcp_language_profile.py`, the STATE 9.50 table, contract
   section 20 summaries, and the #1086 pre-flight). Only the STATE-fragment pins and
   the executable probes link it back to STATE.
4. **Current STATE evidence for the profile is partly circular and positionally
   fragile.** The `if_and_loops` fact pins `if_expression: false` / `loops: false`,
   which appear in STATE only at line 6844, inside section 9.50, which is the
   profile's own restatement. Section 5 says only "no dedicated conditional keyword
   exists" and no section states that loops are absent. Sections are looked up by
   number via `dict(re.findall(...))`, and STATE has duplicate numbers (`## 1)` twice,
   `## 4.1)` twice), so the last duplicate silently wins. `flow_shared_coverage`
   cites `["0","1"]` and passes only because the fragments happen to sit in section 0.
5. **Renumbering STATE is a wire-contract and link hazard.** The profile emits
   `state_sections` identifiers (`"5"`, `"9.50"`, ...) as exact-pinned wire values
   (A7), and 153 `GENIA_STATE.md ... section N` references exist across docs. The
   distillation must treat section numbers as stable identifiers.
6. **The MCP server cannot consume the registry at runtime without changing its
   boundary.** `mcp.genia` is a native program that works in plain file mode with no
   host capability (a tested property), and the issue forbids host/transport/security
   change and Markdown scraping. The projection must be **generated at build time**
   into `mcp.genia` with a `--check` gate (precedent: `tools/gen_function_docs.py --check`).

## 1. Scope lock

**Includes (eventual implementation):**
- structured MCP-fact governance by extending `docs/contract/semantic_facts.json` additively
- a generator + drift gate that projects it into the native `genia_language_profile` constants
- STATE-pin, executable-probe, and golden-wire tests
- a future-change rule in the pre-flight template, `AGENTS.md`, and `docs/process/*`
- distillation of `GENIA_STATE.md` with a machine-checked migration ledger
- synchronization of affected docs (section 8)

**Excludes:** new Genia syntax/semantics; any parser, evaluator, Core IR, builtin, or
host-capability change; any change to MCP tools, transport, limits, security boundary,
resources, prompts, or the four-tool surface; runtime Markdown scraping; any change to
host capability claims (unless a claim is proven incorrect, then separately); C++ MCP;
new authentic client acceptance runs; deleting STATE content without a recorded destination.

## 2. Source of truth

- **Authoritative `GENIA_STATE.md` sections:** 0, 0.1, 1, 5, 8, 9.48–9.50 (the profile's current anchors); 4.7 (open-clause rule); 2/3 (value and syntax forms).
- **Relevant `GENIA_RULES.md`:** 6 (patterns), 8 (resolution), 9.1 (tail calls), 16 (conditional model), 10 (observable spec scope).
- **Additional docs/contracts:** `docs/contract/semantic_facts.json`, `tests/doc/test_semantic_doc_sync.py`, `docs/design/r28-genia-mcp-contract-threat-model.md` (A6 s19, A7 s20), `docs/mcp/*`, `docs/releases/R28.md`, `docs/architecture/executable-semantic-conformance.md`, `docs/process/run-change.md`, `docs/process/00-preflight.md`, `.github/ISSUE_TEMPLATE/genia-change-preflight.md`, `spec/manifest.json` (`host_status`), `spec/known_host_gaps.json`.
- **Conflicts to resolve before proceeding:**
  1. `docs/architecture/executable-semantic-conformance.md` states that `semantic_facts.json` is a "selective cross-document drift guard", "not a second language definition", and that no new semantic manifest is justified. Extending it is consistent only if entries stay pinned guards. That document's wording must be amended in the same change (condition C2).
  2. STATE section 0 still carries R25-era C++ summaries and a "Other hosts are not implemented" line beside later R26/R27 truth (already recorded in the #1086 pre-flight). Distillation resolves this by retaining only the current statement; it must not silently pick a side without a recorded decision (migration map row).
  3. Duplicate section numbers (`1`, `4.1`) must be disambiguated before any anchor policy is enforceable.

## 3. Feature maturity

- [x] N/A — process/docs/governance only. The MCP surface keeps its existing classification (Python reference host adapter; Experimental discovery scope per A7). No language/runtime maturity changes.

**Required wording impact:** none for language maturity. Docs must say the registry is a guard/projection source and that STATE remains authority.

### 3a. Portability analysis

- **Portability zone:** process/documentation plus a Python-reference-host MCP adapter application; not portable language behavior.
- **Core IR impact:** none.
- **Capability categories affected:** none (no `spec/manifest.json` capability added or changed).
- **Shared spec impact:** none; MCP metadata is an application contract. Existing R16 evidence is untouched.
- **Python reference host impact:** none to `hosts/python/*` or `src/genia/*`. `apps/mcp/mcp.genia` changes only by replacing hand-written constants with a generated block of identical output.
- **Host adapter impact:** none.
- **Future host impact:** none. `m0smith/genia-cpp` references STATE by file name only (no section numbers; checked), so STATE restructuring needs no change there. No `spec/known_host_gaps.json` edit.

## 4. Contract vs implementation

- **Portable contract:** unchanged.
- **Python implementation today:** `genia_language_profile` returns static constants from `apps/mcp/mcp.genia` (lines ~265–390 plus `language_value`/`profile_envelope`).
- **C++ implementation today:** bounded R27 language host; no MCP.
- **Not implemented / not to be implemented here:** runtime consumption of any JSON by the MCP server; C++ MCP; live discovery.

## Part A — Measuring `GENIA_STATE.md`

Totals at `f75c166`: **6,932 lines, 72,424 words, 572,275 bytes**; 77 `##` and 38 `###`
headings; 31 commits touch it. It contains about 266 `#NNN` issue references, 426
`E##-#` ticket tags, 59 pass/total-count phrases, and 3,142 distinct backtick
identifiers (a usable preservation inventory, see Part H).

| Region | Lines | Words | % lines | Character |
|---|---:|---:|---:|---|
| Title | 4 | 20 | 0.1 | keep |
| 0, 0.1 Multi-host, browser status | 268 | 3,096 | 3.9 | **mixed**: current host matrix + R16 E16-1..7 chronology, evidence counts (e.g. 641/623/18), `host_parity_gate`/#883 dedup narrative |
| 0.2–0.4 doc publishing, `@doc` linter, style-sync tests | 92 | 737 | 1.3 | tooling/process, not language state |
| 1 Shared conformance (first `## 1)`) + 1 Execution model | 114 | 1,768 | 1.6 | current model + conformance narrative |
| 2 Runtime value categories | 540 | 10,272 | 7.8 | **current semantics**, but 133 `E##-#` tags and 54 issue refs |
| 3, 4, 4.1–4.6, 7, 8, 9 (syntax, dispatch, interop, stdlib, TCO, debug) | 539 | 4,742 | 7.8 | current semantics |
| 4.7 Open functions (R20) | 135 | 1,048 | 1.9 | current semantics (the profile's `open` rule depends on it) |
| 5 Case expressions and patterns | 183 | 3,564 | 2.6 | current semantics; **the profile's primary authority** |
| 6 Builtins | 1,640 | 16,838 | 23.7 | reference catalogue; current truth, high prose density, repeated release qualifiers |
| 9.1–9.6 native-test and lifecycle data shapes | 238 | 3,183 | 3.4 | current Experimental surface |
| 9.7 R8 server execution contract | 76 | 2,131 | 1.1 | current contract (a test asserts this exact heading) |
| 9.8–9.20 R14 lifecycle/HTTP, ticket by ticket | 1,016 | 8,016 | 14.7 | per-ticket narrative over a contract that exists in `docs/design/r14-composable-lifecycle-contract.md` |
| 9.21–9.31 R21/R22 numerics, ticket by ticket | 516 | 3,785 | 7.4 | ditto (`r21-*`, `r22-exact-numeric-runtime-contract.md`) |
| 9.32–9.37 R23 numeric rendering/JSON | 525 | 3,820 | 7.6 | ditto (`r23-*` contract, `analysis/r23-release-truth-audit.md`) |
| 9.38–9.39 Provider P8/P9 proofs | 237 | 1,754 | 3.4 | proof narrative; `p8-*`, `p9-*` design docs exist |
| 9.40 External process execution | 170 | 1,228 | 2.5 | current surface; `execution-process-contract.md` exists |
| 9.41–9.51 R28 MCP (E28-1..6, A5, A6, A7, #1087) | 552 | 5,536 | 8.0 | current MCP contract interleaved with phase history |
| 10 Not implemented; 11 Demos | 88 | 1,194 | 1.3 | 10 keep; 11 is an example catalogue |

Reading: about **21% of lines are core language semantics** (sections 2–5, 7–10) and
**24% are the builtin catalogue** (section 6, current truth); **about 45% is
release/proof narrative** (9.7–9.51, of which 9.7, 9.40, and the current MCP contract
must be kept as digests); the remainder is host chronology and tooling. Section 6
needs care: it is current truth, and the composability-matrix sync test derives the
Template/representation family from code and requires every name in STATE.

**Where detail can move without losing discoverability** (all destinations exist):
`docs/releases/R*.md` (release narrative and evidence), `docs/design/r*-contract.md`
(contracts), `docs/analysis/*release-truth-audit.md` (audit narrative),
`docs/host-interop/*` and `docs/architecture/executable-semantic-conformance.md`
(R16/host mechanics), `docs/style/doc-style.md` + `docs/process/*` (linter/publishing
tooling), `docs/mcp/*` (MCP wire detail), `docs/reference/` (generated prelude
reference, for prelude functions already carrying `@doc`).

## Part B — Responsibility and shape of the distilled STATE

**Responsibility statement (proposed):**

> `GENIA_STATE.md` is the final authority for what Genia **is now**: the implemented
> syntax and semantics, the value model, language/runtime invariants, execution modes,
> host support and the portable/host-specific split, maturity classifications, current
> limitations, and — for every topic whose detail lives elsewhere — the pointer to the
> governed document that owns that detail. It records no release chronology, issue-by-issue
> implementation history, historical test counts, or audit narrative. A statement that
> is not here is not part of the language.

**Moves out of STATE:** release/epic/ticket chronology; per-ticket "E##-# adds ..."
paragraphs; pass/total evidence counts and pinned commit hashes; audit verdicts;
documentation-publishing and linter tooling; example-demo catalogues; duplicated
restatements of MCP wire constants.

**Stays in STATE:** every currently implemented behavior claim (syntax, semantics,
errors, invariants, builtin contracts), maturity labels, host/portability labels,
limitations, and the authority/navigation index.

**Proposed outline** (section numbers are stable identifiers, see section 8 / Part H):

0. Authority, scope, and navigation index (replaces the introduction; pointers to RULES, REPL README, specs, releases)
0.1 Hosts and portability: host matrix (Python full; C++ bounded production host; Node/Java/Rust/Go planned; browser scaffolding), shared-conformance categories, maturity vocabulary — *retains numbers 0, 0.1, 1(conformance)*
1. Execution model (retains number 1; the conformance subsection gets a distinct number, see C3)
2. Runtime value categories
3. Syntax and expression forms (adds the explicit "no `if`, no loop syntax; repetition is recursion" statement — see Part D)
4. Functions and dispatch (4.1 interop, 4.2–4.6, 4.7 open functions)
5. Case expressions and pattern matching
6. Builtins (condensed contract-per-name; per-release qualifiers removed)
7. Autoloaded stdlib; 8. Tail calls; 9. Debug/runtime tooling
9.x Subsystem contracts, **current-state digests only**, one per subsystem, original numbers kept where the content stays (9.1–9.7 native test/lifecycle/R8, 9.40 process, 9.48–9.50 MCP); retired numbers are listed in a crosswalk
10. Explicitly not implemented (current)
11. (retired; pointer to the examples catalogue)

**Measurable target** (derived from the table above, not preset). A planning model
that keeps all language/runtime semantics and condenses per-ticket narratives yields
about 2,500 lines (host sections ~60; value categories ~300; core ~400; open functions
~90; patterns ~150; builtins ~700; native-test/lifecycle ~120; R8 ~60; R14/R21/R22/R23
digests ~350; P8/P9 ~30; process ~70; MCP ~110). The proposed acceptance ceiling,
which leaves headroom over that model:

- **lines ≤ 3,000 (≥ 57% reduction); words ≤ 35,000 (≥ 52%)**; stretch ~2,500 lines
- **zero** headings containing `E\d+-\d+`; `#NNN` references ≤ 60, each a pointer to an owning document, never narrative
- no pass/total-count phrases; no pinned evidence commit hashes
- no section other than 6 over 250 lines
- all 3,142 current backtick identifiers accounted for (Part H), including the test-pinned strings (Part I)

The numbers are a proposal to ratify (condition C6) after the migration ledger is drafted
and a dry run confirms the model; the ceiling is enforced by a test only once ratified.

## Part C — Audit of the semantic-fact system

- **Content:** `docs/contract/semantic_facts.json`, 24 lines, 22 keys, every value a sentence. Groups: Option pipeline semantics (5), CLI/pipe/main (4), Flow (2), `host_status`, `naming_rule`, `annotation_builtins`, two path-separator facts, two native-test facts, R11/R12/R13 composition boundaries, and `r18_equality_relation`.
- **What it synchronizes:** README, `GENIA_REPL_README.md`, cheatsheets, `hosts/README.md`, `spec/README.md`, `docs/browser/README.md`, `apps/playground/README.md`, `docs/host-interop/HOST_INTEROP.md`, and the R11/R12/R13 release-truth tests. STATE is checked by hard-coded assertions in the test file, not by registry values (only `FACTS["direct_call_option_behavior"]` is checked against RULES).
- **Authoritative or guardrail:** guardrail/projection. `AGENTS.md` calls these "cross-doc semantic guardrails"; `executable-semantic-conformance.md` says they are not a second language definition. STATE is the authority; the JSON is derived by humans and checked by substring tests.
- **Drift detection:** `normalize()` (whitespace/case) substring containment of fact text in documents, a frozen key-set test, a `<= 22` cap, a few forbidden-phrase checks, and executable runtime probes (pipeline lifting, `main` dispatch, pipe mode, annotations). It detects drift only for the facts it holds and only in the documents listed per test.
- **Schema fit for MCP facts:** not as-is. MCP facts need `id`, `scope`, `status`, `maturity` (nullable, closed enum), a wire `summary` (≤ 256 bytes), ordered STATE anchors, and verbatim pins; the current schema is `key -> sentence`. Three consumers of the file read it by key (`test_semantic_doc_sync.py` and the R11/R12/R13 truth-sync tests), so an **additive reserved key** (no change to existing entries) has the smallest blast radius: one key-set/cap test edit.
- **What must change to support the profile:** add the projection metadata and pins (section 6), a cap rule that distinguishes the 22 sentence facts from the projection key, a generator, and tests. Some MCP-visible claims overlap existing facts (`host_status` already protects the C++ floor, Python/C++ split, and planned-host wording); the projection references them by key (`fact_refs`) instead of restating them.

## Part D — Provenance of `genia_language_profile` (as of `f75c166`)

| Profile member | Origin today | Duplicated in | Protection today | STATE-change failure mode |
|---|---|---|---|---|
| `name`, tool schema, envelope | native constants | contract s19, `reference.md` | wire tests | none (adapter shape) |
| `contract_revision` | runtime launch argument | n/a | test vs `genia_capabilities` | n/a — **runtime-derived** |
| `control_flow` (pattern matching, no `if`, no loops, recursion, TCO) | hand-written `LANGUAGE_CONTROL_FLOW` | STATE 9.50 prose, test, contract s19, `reference.md`, `LLM_CONTRACT.md` | executable probes (absent forms are absent; constant-stack tail recursion) | a semantic change that breaks a probe fails; a prose-only STATE edit is invisible |
| `supported_forms`, `absent_forms`, `patterns` | hand-written lists | STATE 9.50, test, contract | partial probes (`absent_forms`); form/pattern lists have **no STATE pin** | stale silently if a form/pattern is added |
| `idioms` (branching, repetition, `open` rule) | hand-written strings | STATE 9.50 | `open` rule proved by evaluating both spellings | prose drift invisible |
| `examples` (`gcd`, `factorial`) | hand-written programs | STATE 9.50, `reference.md`, `LLM_CONTRACT.md` | **evaluated** (6, 120) | caught by behavior |
| `discovery.facts[12]` — language (3) | hand-written maps | STATE 9.50 table, test oracle, contract s20, #1086 pre-flight | STATE-fragment pins; `if_and_loops` pin is **circular** (sits in 9.50) | pin fails only if the pinned fragment is reworded |
| `discovery.facts` — shared conformance (2), C++/other hosts (2), browser (1) | hand-written | same | STATE-fragment pins in sections 0/0.1/1 | fails on rewording of pinned fragments (and on renumbering); could pass on the wrong duplicate section (`1`) |
| `discovery.facts` — MCP/Windows/macOS (4) | hand-written | same | STATE-fragment pins in 9.48–9.50 | same |
| `discovery.coverage`, bounds (16,384 B / 256 B) | hand-written | contract s20 | shape test | n/a |

**If STATE changes and the profile does not:** a behavioral change that contradicts an
executable probe fails a test. A change to a pinned STATE fragment fails the pin test
(which then requires a human to re-read the fact). Everything else — a new pattern kind,
a new syntax form, a changed maturity label whose wording is not pinned, a prose-only
semantic edit — leaves the profile stale and green. That residual gap is the defect to close.

## Part E — Synchronization architectures

| Criterion | **1. Extend `semantic_facts.json`** (additive projection key) | 2. Separate `language_profile.json` | 3. Generate from another governed artifact (`spec/manifest.json`, `known_host_gaps.json`, capability docs) | 4. Alternatives |
|---|---|---|---|---|
| Semantic authority | STATE; JSON stays a pinned guard if entries carry verbatim STATE pins | STATE nominally; a new file invites "profile JSON is the truth" | manifest is machine truth for host claims only; no prose/maturity labels | (a) runtime Markdown parse: rejected by issue; (b) runtime JSON read by `mcp.genia`: needs a file-read capability, changes security boundary, breaks plain-file mode; (c) hand copy + equality test: leaves two maintained copies, fails the "generated from" criterion |
| Duplication | one registry; projection references flat facts by key | adds a second registry beside the 22 guard facts; overlap with `host_status` | covers ~4 of 12 facts; counts are volatile | (c) 2 hand copies |
| Maintainability | one file, one generator, one pin-test family | cleaner schema, separate caps; two files to review | spread over several files | — |
| MCP runtime simplicity | unchanged (generated constants) | unchanged | unchanged | (b) adds runtime I/O |
| Testability | pins + probes + `--check` + golden wire | same | strong where applicable | — |
| Failure modes | mixes string facts and one object (cap/guard-doc friction) | creates the "second authority" the issue forbids unless pins are equally strict | derivation of prose summaries impossible | — |
| Migration effort | small: one test edit + new key + generator | slightly larger (new file, new loader) | n/a as a sole source | — |
| Contributor ergonomics | one place to look; template field points to it | two places | many places | — |

**Option 3 is useful as a cross-check only:** `spec/manifest.json`'s `host_status`
(implemented/planned/scaffolded hosts, browser adapter) can validate the host/browser
facts (`other_language_hosts`, `browser_runtime`, `cpp_language_floor`) mechanically, and
`spec/known_host_gaps.json` can cross-check `cpp_mcp`-adjacent claims. It cannot supply
summaries or maturity labels, and counts change too often to belong in a static profile.

**Recommendation: Option 1** — extend `semantic_facts.json` additively, generate the profile
constants from it, and keep Option 2 as a documented contingency. This satisfies the issue's
stated preference and has the fewest independently maintained semantic representations
(STATE prose + one registry; every other representation is generated or derived in tests).
**Tripwire for Option 2:** if maintainers decide, at the contract phase, that a nested object
in `semantic_facts.json` contradicts its "selective guard" charter beyond what a wording
amendment can reconcile, use `docs/contract/mcp_language_profile.json` with the identical
schema, pin tests, and generator. Placement is the only difference; the invariant is unchanged.

## Recommended architecture — the synchronization chain

```text
GENIA_STATE.md                      semantic authority (prose; explicit sentences for every pinned claim)
      │
      │  verbatim-pin tests: each projection entry's pins must occur in the cited STATE section
      │  (anchors resolved by stable ID, never by dict-of-last-duplicate)
      ▼
docs/contract/semantic_facts.json   GUARD + PROJECTION SOURCE (not authority)
  ├─ 22 existing sentence facts (unchanged)  ──► existing doc-sync tests (retained)
  └─ mcp_language_profile (new, additive)    ──► tools/gen_mcp_language_profile.py
        { id, scope, status, maturity, summary≤256B,
          anchors[], pins[], fact_refs[], guard: state_pin | executable_probe }
                                                  │ generates (with --check)
                                                  ▼
                                      generated block in apps/mcp/mcp.genia
                                                  │
                                                  ▼
                                      genia_language_profile (wire, byte-stable)
                                                  ▲
        executable probes (absent forms, TCO, `open` rule, examples) ─┤
        golden wire snapshot (reviewable diff when the wire changes) ─┤
        four-tool acceptance (unchanged) ─────────────────────────────┘
```

Details to settle in the contract phase (non-binding sketch):
- **Entry shape:** `id`, `scope`, `status` (existing closed enum), `maturity` (null or `Experimental|Partial|Stable`), `summary` (wire text, MCP-owned phrasing), `anchors` (ordered strings), `pins` (verbatim STATE fragments that justify the claim), optional `fact_refs` (keys of existing sentence facts), and the A6 members (`control_flow`, `supported_forms`, `absent_forms`, `patterns`, `idioms`) as guarded data. Example programs stay native/evaluated; they are adapter vocabulary proven by execution, not facts.
- **Zero wire change by default:** summaries, ids, section strings, ordering, and sorted encoding stay byte-identical, so the A7 contract and four-tool acceptance remain valid. A wire change (for example re-pointed `state_sections`) would need an explicit amendment (A8) and is avoided by keeping stable section identifiers.
- **Why `pins` rather than copying summaries into STATE:** summaries are MCP-owned phrasing; the pins bind the underlying STATE claim. Reworded pins fail loudly; unrelated editorial edits do not.
- **Generator, not runtime read:** `mcp.genia` keeps working in plain file mode with no host capability; the generated region is delimited by markers, and `--check` fails on a hand edit or a stale block.

## Future semantic-change workflow

Every implemented semantic change must answer: **"Does this change affect knowledge an MCP client should know about Genia?"**

- **If no:** record `MCP language-knowledge impact: none` with a one-line reason.
- **If yes:** the same change updates STATE (pinned sentence), the registry entry, regenerates `mcp.genia`, updates the golden wire snapshot, and the four-tool/profile tests pass.

Where the rule lives (each is a documented process surface; update only these):
1. `.github/ISSUE_TEMPLATE/genia-change-preflight.md` section 8: new required field "MCP language-knowledge impact (none / registry ids touched)". (Section 8 already holds "Required synchronization".)
2. `docs/process/00-preflight.md` section 8 (cross-file impact) mirrors the field; `docs/process/05-doc.md` and `06-audit.md` gain one checklist line each.
3. `AGENTS.md` "Required Workflow for Any Change": add a step after "update any other affected core docs", and one sentence in the R26+ pre-flight gate.
4. `docs/process/run-change.md`: one bullet in the pre-flight requirements.
5. `docs/ai/LLM_CONTRACT.md` and `.github/copilot-instructions.md`: one pointer line each (they are already required by a test to cite `semantic_facts.json`).

**Distinguishing meaningful from editorial STATE changes** (a "any STATE diff requires a profile change" rule is rejected):
- *Pins:* only the verbatim fragments a projection entry pins can fail on a STATE edit, so editorial changes elsewhere cannot cause false failures; a pinned fragment's rewording fails once and is resolved by confirming the claim (re-pin) or changing the registry.
- *Probes:* executable claims are bound to behavior, not wording.
- *Classification coverage (candidate, decide in contract phase):* a test that derives a form/pattern inventory from the parser or `spec/` and requires each item to be either profiled or explicitly listed as "not MCP-relevant", analogous to `test_composability_matrix_sync.py`. This is the only mechanism that catches a brand-new syntax form with no existing pin; feasibility must be confirmed against the actual AST/kind vocabulary before it is committed to.
- *Honest limit:* an MCP-relevant claim that is neither pinned, probed, nor derived can still be missed; the template field and review are the backstop for that remainder.

## 5. Test strategy

**Retain unchanged:** `tests/doc/test_semantic_doc_sync.py` (all existing tests; only the key-set/cap test is edited), the R11/R12/R13 release-truth sync tests, `tests/doc/test_composability_matrix_sync.py`, `tests/doc/test_r8_server_contract_sync.py`, `tests/unit/test_docs_truth_model.py`/`test_no_overclaim_language.py`, `tests/unit/test_r28_mcp_*.py` (skeleton, parse, run, compat, architecture, conformance surface/matrix, language profile), `tests/unit/test_r28_release_gate.py`, `tests/doc/test_r28_inventory_ledger.py`, and the Node acceptance in `tools/mcp_acceptance/` (four-tool `acceptance.mjs`, `negotiation.mjs`).

**Add / change:**

| # | Requirement | Test (deterministic, structural) |
|---|---|---|
| 1 | Governed facts and MCP output agree | `test_profile_wire_equals_registry_projection`: invoke the profile (existing helper) and assert it equals the projection computed from the registry by an independent in-test function; assert generated block == committed block (`gen_mcp_language_profile.py --check` as a pytest) |
| 2 | Removing/changing a fact without its projection fails | mutation tests: copy the registry to a temp path, drop/alter one entry or pin, assert `--check` and the pin test fail; assert any `mcp.genia` edit inside the generated markers fails `--check` |
| 3 | Editorial STATE changes cause no false failures | test that mutates STATE text *outside* pinned fragments (whitespace, reordering of unrelated sections, retired narrative) and asserts the pin/anchor tests still pass; anchors resolve by stable ID so renumbered-but-mapped sections still resolve |
| 4 | Profile still produces the intended assistant-facing result | retain `test_r28_mcp_language_profile.py` assertions on `control_flow`, forms, patterns, idioms, examples (evaluate to 6/120), absent forms, tail recursion; add a **golden wire snapshot** (`tests/data/mcp_language_profile.golden.json`) so a wire change appears as a reviewable diff |
| 5 | Four-tool MCP acceptance remains valid | unchanged `tools/mcp_acceptance/*`, `test_r28_mcp_*` suites, matrix rows D1, D5, D6, D9, D10 |
| 6 | Semantic documentation sync still passes | full `tests/doc/` including the edited key-set test |
| 7 | STATE distillation does not change runtime behavior | distillation PR touches no file under `src/`, `hosts/`, `apps/`, `spec/` (diff-scope check in the audit) and the full regression plus shared spec runner results are identical before/after; registry/generator PR leaves `mcp.genia` output byte-identical (golden) |
| 8 | Pins resolve unambiguously | `test_state_anchors_are_unique_and_stable`: every anchor ID occurs exactly once (this fails today for `1` and `4.1` and closes the duplicate-last-wins hazard); every cited anchor exists; pins are found *within the cited anchor*, not anywhere in STATE |
| 9 | Pins are not circular | each language-claim pin must occur in a language section (3/4/5/8), never only in the MCP sections |
| 10 | Workflow rule exists | doc-sync test asserting the pre-flight template, `00-preflight.md`, `AGENTS.md`, and `run-change.md` contain the MCP-impact field/step (mirrors the existing killer-workflow checks) |
| 11 | Cross-check against machine truth | host/browser facts validated against `spec/manifest.json` `host_status`; distinct from authority |
| 12 | Migration completeness | Part H gates |

The existing `test_discovery_claims_have_scoped_state_authority` and the pasted
`DISCOVERY_FACTS` oracle are **replaced** by registry-driven tests in the same PR as the
registry (the pasted oracle currently duplicates 12 rows by design as an "independent wire
oracle"; its role moves to the golden snapshot plus shape/enum/size assertions). That
substitution must be a reviewed, explicit change, not a silent deletion.

## 6. Examples

- **Minimal (registry entry sketch, not binding):**
  `{ "id": "tail_calls", "scope": "language", "status": "implemented", "maturity": null,
  "summary": "Tail calls are optimized.", "anchors": ["8"],
  "pins": ["proper tail-call optimization is implemented via trampoline evaluation"],
  "guard": ["state_pin", "executable_probe:tail_recursion_constant_stack"] }`
- **Realistic:** a future change that adds a loop-like form. The probe `absent_forms` fails, the STATE section 3 sentence "no loop syntax exists" is edited and its pin fails, both forcing the registry entry, regenerated `mcp.genia`, and golden snapshot into the same change.
- **Classification:** process-only / MCP-adapter-only (Python reference host); not portable language behavior.

## 7. Complexity check

- [ ] Adding necessary complexity
- [x] Revealing existing structure

**Justification:** the facts and the STATE links already exist; this removes four hand
copies and replaces them with one registry plus a generator. The only new machinery is
a small generator and pin tests, following the existing `gen_function_docs.py --check`
pattern. **Simpler alternatives considered:** hand copy + equality test (simplest, but the
profile would still maintain an independent hand-copied inventory, contrary to the issue);
runtime JSON read (rejected on boundary grounds); documentation-only rule (does not
detect drift).

## Part H — Migration safety for the STATE reduction

Risk: information disappears while the tests stay green (STATE is asserted by about 11
test modules with a bounded set of strings; the vast remainder is unguarded).

**Method.**
1. **Freeze a baseline:** record the pre-distillation commit SHA; generate a **section inventory** (every `##`/`###` heading with its line range, word count, backtick-identifier set, issue/ticket refs).
2. **Migration ledger** (`docs/analysis/state-distillation-migration-map.md`, with a guard test in the style of `test_r28_inventory_ledger.py`): one row per heading in the baseline. Each row has exactly one disposition:
   - `retained` (in distilled STATE; heading and identifiers preserved or condensed with named kept claims);
   - `moved-existing` (verbatim into a named existing document, with its new heading/anchor);
   - `moved-new` (verbatim into a new supporting document, which must be linked from the owning release/design page);
   - `redundant` (names the governed source that already states it, with a locator and evidence);
   - `obsolete` (with evidence that it was superseded, such as the later entry that replaced it, or a deleted feature).
   There is **no** "deleted" bucket; any row without a disposition fails the guard.
3. **Verbatim relocation:** moved blocks are copied unchanged under a line `Moved from GENIA_STATE.md@<sha>, section <id>`, so review is a diff of identical text; condensing happens only in STATE and each condensed section lists its kept claims in the ledger.
4. **Preservation gates (automated):**
   - *identifier inventory diff:* every one of the 3,142 baseline backtick identifiers (and all quoted error/diagnostic strings) must appear in distilled STATE or in a ledger-named destination; the unexplained set must be empty and is printed on failure;
   - *assertion inventory:* the exact strings asserted against STATE by the ~11 test modules still appear in STATE (or the test is deliberately retargeted in the same PR, with the move recorded);
   - *builtin inventory:* every builtin/prelude name in code remains in STATE (existing composability sync test) and in the ledger;
   - *link integrity:* each of the 153 `GENIA_STATE.md ... section N` references resolves, via retained numbers or the crosswalk; each retired number maps to a destination.
5. **Review of the map:** the ledger is committed in Phase 4a before any content moves; a reviewer signs the dispositions table (not the diff) first; the move PR is then reviewable mechanically. Sections touching live tests (9.7, 9.48–9.50) are marked "frozen" and reviewed individually.
6. **Dry run first:** produce the ledger and inventory diff on a scratch branch to confirm the size model before ratifying the target (condition C6).

**Stable identifiers.** Retain existing numbers where the content stays; never reuse a
retired number; resolve the two duplicates by renumbering the later occurrences only after
adding crosswalk entries (condition C3). Add explicit anchors so pins resolve by ID.

## Part I — Test-pinned STATE strings (must survive distillation)

Verified pinned in STATE (non-exhaustive; the Phase 4a inventory generates the complete list): the equality-relation sentences; pipeline Option contract sentences; `stdin` bridge-only sentences; `main(argv())` dispatch and pipe-mode wording; naming-rule wording; dot field-path/named-access wording; capability-registry pointer (`capabilities.md`); `spec/parse/` listing; native-test placement boundary section (heading text and support-boundary sentences); the literal heading `## 9.7) R8 server execution contract`; the A7 evidence fragments listed in `test_discovery_claims_have_scoped_state_authority`; fragments pinned by R11/R12/R13 audit tests and the composability-matrix sync (builtin names). Any of these that the distillation condenses must be retargeted in the same PR with the change recorded in the ledger.

## 8. Cross-file impact

**Likely changed (by phase):**

| File | Why | Phase |
|---|---|---|
| `docs/contract/semantic_facts.json` | additive `mcp_language_profile` key | 1 |
| `tests/doc/test_semantic_doc_sync.py` | key-set/cap rule for the new key; STATE-pin and anchor tests; workflow-field test | 1–3 |
| `tools/gen_mcp_language_profile.py` (new) | build-time projection with `--check` | 2 |
| `apps/mcp/mcp.genia` | generated block replaces hand constants; output byte-identical | 2 |
| `tests/unit/test_r28_mcp_language_profile.py` | replace pasted oracle/pin test with registry-driven tests; keep probes | 2–3 |
| `tests/data/mcp_language_profile.golden.json` (new) | wire snapshot | 2 |
| `GENIA_STATE.md` | Phase 1: add explicit no-`if`/no-loop/recursion language sentences and stable anchors; Phase 4: distillation | 1, 4 |
| `docs/analysis/state-distillation-migration-map.md` (new), destination docs (`docs/releases/R*.md`, `docs/design/r*-contract.md`, `docs/host-interop/*`, `docs/style/doc-style.md`, `docs/process/*`) | migration ledger and relocated content | 4 |
| `docs/architecture/executable-semantic-conformance.md` | amend "selective drift guard" wording to cover the projection key (C2) | 1 |
| `.github/ISSUE_TEMPLATE/genia-change-preflight.md`, `docs/process/00-preflight.md`, `05-doc.md`, `06-audit.md`, `docs/process/run-change.md`, `AGENTS.md`, `docs/ai/LLM_CONTRACT.md`, `.github/copilot-instructions.md` | future-change rule | 3 |
| `docs/mcp/reference.md`, `docs/mcp/conformance-matrix.md`, `docs/design/r28-genia-mcp-contract-threat-model.md` (A7 s20 pointer), `docs/releases/R28.md` | state that the profile is generated from the registry; replace duplicated tables with pointers; no wire change | 5 |
| `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md` | only if the distillation or workflow changes a statement they hold; `README.md`/REPL README carry protected semantic facts (tests above) and cross-references to STATE section numbers, so they are re-verified, not rewritten | 5 |
| `docs/mcp/stdio-development.md`, `docs/mcp/demo.md`, `tools/mcp_acceptance/*` | no change expected (four-tool surface and acceptance remain valid) | n/a |

Not changing: `hosts/python/*`, `src/genia/*`, `spec/*`, `docs/host-interop/*` claims, `m0smith/genia-cpp`.

**Drift risk:** High (STATE is the most widely cross-referenced file in the repo).

## 9. Philosophy check

- **Preserves minimalism:** YES (fewer representations)
- **Avoids hidden behavior:** YES (generated block is explicit, checked)
- **Keeps semantics out of host adapters:** YES (no host change; the adapter text remains a projection)
- **Aligns with pattern-matching-first design:** N/A (documentation governance); the profile's own claim about pattern matching becomes pinned
- **Strengthens Outcome-aware validated pipelines, or has an approved reason not to:** Indirect: assistants generating Genia source through MCP get current idioms (the profile exists to stop `if`/loop output), and #1087's grounded example depends on the same facts. Otherwise governance work under the R28 follow-up umbrella.

## Part J — Risks

| Risk | Mitigation |
|---|---|
| Accidental semantic loss during distillation | ledger with no unexplained bucket; verbatim relocation; identifier and assertion inventory gates; dry run |
| A second authority is created | pins must be verbatim STATE text; projection key stays inside the guard file; docs amended to say "guard/projection source"; tripwire to Option 2 keeps the same rules; STATE edit sequence in Phase 1 puts every claim into STATE first |
| Circular synchronization (STATE restating the profile, profile pinning STATE) | language-claim pins must be in language sections (test 9); STATE 9.50 stops restating constants and points to the registry |
| Brittle documentation tests | pins are limited to curated verbatim fragments; anchors resolve by ID; mutation tests prove editorial edits do not fail |
| Stale MCP guidance | generator `--check`, golden snapshot, probes, template field, plus the optional classification-coverage test; residual gap acknowledged |
| Historical evidence becomes undiscoverable | ledger rows name destinations; release pages link the moved blocks; crosswalk for retired numbers; moved text carries a provenance line |
| Scope creep into language/runtime | the distillation PR is diff-scoped to docs/tests/tools; audit asserts no `src/`, `hosts/`, `spec/` change; Phase 1 STATE additions describe existing, already-probed behavior only |
| Wire change by accident | zero-wire-change default; byte-identical golden; any intentional change requires amendment A8 |
| Renumbering breaks 153 inbound references and test heading regexes | stable-ID policy, crosswalk, link-integrity gate, heading-regex tests retargeted explicitly |
| Large single PR | two PRs (A: Phases 1–3; B: Phases 4–6) recommended |

## 10. Prompt plan

- [x] Pre-flight (this document)
- [x] Contract (short, approval-gated: registry projection schema, anchor/ID policy, workflow rule, whether A8 is needed; "contract defines behavior only", so no tests)
- [x] Design (generator design, ledger format, target ratification)
- [x] Failing tests (Phases 1–3 tests first; migration guard tests before content moves)
- [x] Implementation
- [x] Documentation
- [x] Audit
- [x] Distillation (the STATE distillation itself is Phase 4; the closing Doc Distillation prompt then re-checks the supporting docs)

**Phase order, issue split:** recommend two PRs under #1099 — **A (sync architecture, Phases 1–3)** then **B (STATE distillation, Phases 4–6)** — because A makes B safer (anchors, pins, and the registry exist first). Child issues are not created by this pre-flight; splitting is a reviewer decision.

## Implementation phases

1. **Structured governance (PR A).** Add stable anchors/ID policy and disambiguate duplicate section numbers in STATE (crosswalk); add explicit language-section sentences for no `if`, no loop syntax, repetition-by-recursion so MCP claims are not circular; add the registry projection key with pins; amend `executable-semantic-conformance.md` wording; edit the key-set/cap test. Wire unchanged.
2. **Prove the projection.** Generator + `--check`; replace hand constants in `mcp.genia` with the generated block; golden wire snapshot; byte-identical output proven; registry-driven profile tests replace the pasted oracle.
3. **Drift gates and workflow.** Pin/anchor/mutation/editorial-immunity tests; classification-coverage test if feasible; template, `00-preflight`, `05-doc`, `06-audit`, `run-change`, `AGENTS.md`, `LLM_CONTRACT.md`, `copilot-instructions.md` rule plus its doc-sync test. *(End of PR A.)*
4. **STATE distillation (PR B), in sub-steps.** 4a: baseline inventory + migration ledger + guard tests committed with no content moved; ledger reviewed. 4b: verbatim relocation to destination docs. 4c: condense STATE to the ratified target; retarget pinned tests explicitly; crosswalk.
5. **Synchronize supporting docs.** `docs/mcp/*`, R28 release page, threat-model A7 pointer, `README.md`/`GENIA_REPL_README.md`/`GENIA_RULES.md` only where affected; replace duplicated tables with pointers.
6. **Audit and distillation.** Full regression in both partitions, doc tests, `gen_mcp_language_profile.py --check`, four-tool acceptance, identifier/assertion/link gates, diff-scope check (no `src/`/`hosts/`/`spec/` change), size target report.

## 11. Host Parity / Conformance

- **Affected hosts:** none (Python host code untouched; C++ untouched; no future-host impact).
- **Does this change portable semantics?** NO.
- **Can one host merge before the other?** N/A.
- No shared spec/conformance change, no `spec/known_host_gaps.json` change.

## 12. Final GO / NO-GO

**Decision: GO WITH CONDITIONS.**

Conditions to satisfy before or during the contract phase:
- **C1.** Reviewer approves Option 1 (additive registry key + generated block) or selects the Option 2 contingency; confirms the zero-wire-change default.
- **C2.** The wording of `docs/architecture/executable-semantic-conformance.md` and the `semantic_facts.json` guard tests is amended in the same change so the registry is explicitly a guard/projection source, not a definition.
- **C3.** Stable section-ID and crosswalk policy accepted; duplicate numbers `1` and `4.1` resolved first.
- **C4.** Phase 1 adds the language-section statements (no `if`, no loop syntax, recursion for repetition) before any MCP pin may cite them; STATE 9.50 stops being evidence for language claims.
- **C5.** The migration ledger is committed and approved (4a) before any content moves; the identifier/assertion/link gates are in place.
- **C6.** The size target in Part B is ratified after the dry run; until then it is a proposal.
- **C7.** A reviewer decides whether the classification-coverage test (derive form/pattern inventory from code) is in scope after a feasibility check in the contract phase.

**Missing decisions/evidence:** C1–C7 above; feasibility of C7; the exact owner of each moved section (the ledger).

**Reviewer / decision date:** pending review.

## Pre-flight verification record

Tests run on this branch before writing this file (read-only baseline):
`uv run pytest -q tests/doc/test_semantic_doc_sync.py tests/unit/test_r28_mcp_language_profile.py tests/unit/test_r28_mcp_architecture.py tests/unit/test_r28_mcp_conformance_matrix.py` — **153 passed**. Measurements in Part A were computed directly from `GENIA_STATE.md` (line/word/byte counts, heading ranges, reference counts, backtick inventory). The full regression and MCP acceptance were not re-run; this change adds only documentation.

**STOP.** This document makes no implementation change. Implementation awaits review of the decision and conditions above.
