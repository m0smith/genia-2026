# #1269 / #1250 — Model B Slice C RED authorization package (R1–R5, G1 recorded; revision 6 reconciliation in §R6)

**Revision 6 (documentation only) adds §R6 below and supersedes the sections it names; see §R6.0 for the decision register of what remains PROPOSED.** **Status: DOCUMENTATION ONLY. No failing test, spec, manifest, adapter, known-gap, production or implemented-truth file is added or changed by this package. RED is NOT started and NOT authorized by this document. GREEN is NOT authorized. G1 is recorded, NOT approved.**

| Item | Value |
| --- | --- |
| Tracking issue | [#1269](https://github.com/m0smith/genia-2026/issues/1269) (child of [#1250](https://github.com/m0smith/genia-2026/issues/1250)) |
| Package base | `main` at `79c073b4…` (`79c073b`, merge of #1272; includes merged C0 = PR #1273) |
| Accepted pre-flight | PR #1270, revision 4 `585f6aa229a55bbd3e3110c975dcaaa94a61e93e`; this package is revision 5 of the same branch (revision 6 = §R6, starting from `a0dce7c9ec8ddebf8c695c5d46495ef20e167031`) (companion edits in `issue-1269-slice-c-preflight.md` and `issue-1269-slice-c-red-test-plan.md`) |
| Authority | `GENIA_STATE.md` (final); contract #1255 / design #1259; integration authorization [6327837022](https://github.com/m0smith/genia-2026/pull/1270#issuecomment-6327837022); C0 acceptance [#1273 6333148622](https://github.com/m0smith/genia-2026/pull/1273#issuecomment-6333148622); independent reviews [6327597044](https://github.com/m0smith/genia-2026/pull/1270#issuecomment-6327597044) and [#1273 6333124626](https://github.com/m0smith/genia-2026/pull/1273#issuecomment-6333124626) |
| Not this package | C++ work, #1271 / #1272 Application Lifecycle, RED/GREEN code, `GENIA_STATE.md` / `GENIA_RULES.md` / `GENIA_REPL_README.md` / `README.md` / semantic-facts / MCP-profile edits |

**Evidence labels (used throughout):** **exec** = executed in this session against the stated head, output observed; **rehearsal** = executed in a throw-away worktree (never committed) to observe *capability and runner mechanics only* — it is **not** a RED result and uses no Slice C case; **read** = from source or docs; **inferred** = reasoned, not run. **No Slice C RED case exists yet, so no RED outcome below is observed; every RED/GREEN expectation is `inferred`** (with the mechanism it relies on labelled exec/rehearsal/read).

Implemented behavior = what `GENIA_STATE.md` records on `main`. Approved future behavior = contract/design/maintainer decisions D1, D3, D3b, D4 (numeric keys), D5, D8 in the pre-flight. Inferred = the outcome tables here. Unresolved = §8.

---

## R6. Revision 6 — RED-readiness reconciliation (documentation only; supersedes the sections named in §R6.0)

**Status of this section: DOCUMENTATION ONLY. RED is NOT authorized. GREEN is NOT authorized. Nothing here is a maintainer decision unless §R6.0 says "APPROVED"; every other item is a PROPOSAL awaiting the integration owner.** Revision 6 starts from the reviewed head `a0dce7c9ec8ddebf8c695c5d46495ef20e167031` (PR head and `origin/main` re-fetched before editing: head unchanged, `main` still `79c073b556ad16343051d545d7928248a6d0f6b0`). It reconciles three inputs: the independent revision-5 readiness review ([Codex, 6346831556](https://github.com/m0smith/genia-2026/pull/1270#issuecomment-6346831556)), the C++ compatibility investigation ([report 6346857756](https://github.com/m0smith/genia-2026/issues/1269#issuecomment-6346857756), [case appendix 6346894165](https://github.com/m0smith/genia-2026/issues/1269#issuecomment-6346894165)) and the [integration reconciliation (6346933756)](https://github.com/m0smith/genia-2026/pull/1270#issuecomment-6346933756).

Evidence labels are those of the head of this file. Additional label: **twin** = the same clauses written with the explicit-`open` spelling (implemented R20 behavior), executed on the Python host to observe dispatch, ordering and renderer text where the default-open behavior is by contract the same; it is never used where `open` semantics differ (noncontiguous clauses, header capture, numeric/Boolean keys).

### R6.0 What changed, what is superseded, and the decision register

| Codex finding / task item | Disposition in revision 6 | Where |
| --- | --- | --- |
| 1 (High) O-1 applicability | Decision card with three options; **recommendation C (authority-anchored)** — PROPOSED, not approved | §R6.1 |
| 2 (High) executable oracles and C++ ledger | Every shared case now carries source, category, requires, stdout/stderr/exit, baseline, RED outcome, oracle status and C++ row; **N = 116** (was 127); persistence-dependent and REPL-transcript cases moved to host-local with stated justification | §R6.2 and the test plan §R6 |
| 3 (High) GA continuity | GA-13…GA-23 added; GA-1…GA-12 retained (GA-4 and GA-6 sharpened) | §R6.4 |
| 4 (Medium) C0 phase tests | Whole-set `monkeypatch` defect fixed by unioning the production override; exact RED and GREEN edits listed | §R6.5 |
| 5 (Medium) O-3 | Draft amendment text for design §3.4 and §13.5 — PROPOSED | §R6.6 |
| 6 (Medium) R1 workflow triggers / totals | Recomputed totals; workflow descriptions corrected (docs/LLM/code-documentation on every PR; regression scheduled/manual; canary and smoke on infra branches/manual) | §R6.3 |
| O-4 / O-5 / O-6 | O-4 stays excluded; O-5 program replaced (verified diagnostic); the 13 L rows split 11 error + 2 REPL observations | §R6.7 |
| G1 | Six reserved IDs (SC-MAIN-3 has two declaration orders); future totals corrected | §R6.8 |

**Sections of this document superseded in part (the older text is retained for history and rationale only):** §2.3/§2.4 and the path-matrix counts (replaced by §R6.3); §3.3 inventory and §3.5 (replaced by the test plan §R6 inventory — the older rows listed 127 ids, several without executable sources); §4 GA table (extended by §R6.4); §5.3/§5.5 (O-3 now has draft amendment text, §R6.6); §6.3 (replaced by §R6.5); §7 (reserved ids and totals replaced by §R6.8); §8.1 (replaced by the register below). Where an older sentence conflicts with §R6, §R6 governs this documentation set; neither governs `GENIA_STATE.md`.

#### Decision register (what remains proposed)

| ID | Decision needed | Status | Revision-6 recommendation | Needed before |
| --- | --- | --- | --- | --- |
| **R6-D1** | O-1 applicability policy (A uniform-ungated old syntax / B gate all changed outcomes / C authority-anchored) | **PROPOSED** | C | locking `requires` for 4 cases (+P5 rationale) |
| **R6-D2** | Portable status of ordinary grouped-body header capture (`hdr-grouped-body-captures-header`) | **PROPOSED** (authority found: contract §2.2, design §13.4; absent from STATE) | required portable behavior; keep shared and ungated; record a separate C++ defect (CPP-D1) | merge of the final head (not RED) |
| **R6-D3** | Placement of the five Python-specific-wording legacy cases (legacy duplicate ×3, non-function declaration ×2) | **PROPOSED** | host-local (existing unit tests already pin the wording); promote to shared only if the maintainer declares the wording portable | RED |
| **R6-D4** | Shared pinning of the R20 `open` diagnostics `own-explicit-open-alias-unchanged` and `d8-r20-flattening-unchanged`, with the pre-existing C++ R20 differences (CPP-D2) tracked separately and not hidden | **PROPOSED** | keep shared with `open_functions` (R20 contract requires pinned CLI text); ledger records C++ latent differences | merge of the final head |
| **R6-D5** | Tag the metadata-channel cases with the existing required capability `doc_help` (design §7 table; 11 existing specs do the same) | **PROPOSED** | yes | RED |
| **R6-D6** | Persistence-dependent observations and REPL transcripts are host-local (one-shot evaluation stops at the first failure; REPL echoes host function representations) | **PROPOSED** | yes | RED |
| **R6-D7** | O-3 design amendment (§R6.6) | **PROPOSED**; needs explicit approval, then align both design clauses | approve | locking file-mode duplicate oracles |
| **R6-D8** | Literal ownership / foreign-alias texts (candidate texts from pre-flight D3) | **PROPOSED**; texts cannot be observed on the current runtime | approve text or the message shape | RED baseline lock |
| **R6-D9** | Active-`unquote` half of the key counterexample has no pinned program | **OPEN**; excluded from the inventory; the quoted-names-are-data half is included | supply a program or accept the exclusion | RED (only for that half) |
| **R6-D10** | `key-repeated-binders-distinct` (O-4) | **EXCLUDED** — no approved non-linear-pattern semantics | keep excluded | n/a |
| **R6-D11** | C++ defects CPP-D1…CPP-D4 (§R6.2): who files them in `genia-cpp`, and the merge precondition (fix + pin bump, or an explicit maintainer ruling) | **OPEN** | file; precondition = zero C++ failure classes at the final head | merge |
| **R6-D12** | G1 `main` selector invariant and the six reserved ids | **PENDING** (before GREEN) | as recorded in §7/§R6.8 | GREEN |
| **R6-D13** | Separate TEST-ONLY RED authorization naming exact ids and expected outcomes | **NOT GIVEN** | issue after independent verification of revision 6 | RED |

APPROVED items already on record are unchanged: D1, numeric keys, D3, D3b, D5, D8, C0, the U2 boundary direction. Revision 6 reopens none of them; R6-D1 concerns only the *applicability* of already-approved outcomes.

### R6.1 O-1 decision card — applicability of changed outcomes of previously accepted syntax

**Question.** P5 (`disp-p5-varargs-minima-ambiguity`) changes an ungated ordinary program and is ungated; the D5 alias/ownership rejections also change programs written in old syntax but were gated by `default_open_functions`. Are those two treatments consistent?

**Exact programs, today, and approved future outcome** (all "today" outputs executed on `main@79c073b`; "future" is the approved decision, not observable):

| # | Program (exact source in the test plan) | Today (observed) | Approved future | Class of change |
| --- | --- | --- | --- | --- |
| 1 | P5: `f(a, ..r)`, `f(a, b, ..s)`, `f(1, 2)` | `"min2"` | `Ambiguous function resolution: f/2. Matching varargs: f/1+, f/2+` (D1) | valid → error |
| 2 | `f(x)=x; a=f; a(x, y)=x+y` | accepted; installs `a/2` into `f`'s group (`<function a/2>`; later `a(1,2)` = 3) | `function-declaration-not-owner` (D5) | valid → error |
| 3 | same plus `@doc (print("annotation-ran"))` before the declaration | prints `annotation-ran`, accepted | rejected **before** the annotation runs (D5/C6) | valid → error, effect-order change |
| 4 | `h = lib.g; h(x, y) = x + y` (module `lib` owns `g/1`) | accepted; appends to `lib.g` | `function-declaration-not-owner` naming module `lib` (D5) | valid → error |
| 5 | `f(x)=x; a=f; a(x, ..r)=x` | error `Duplicate function definition: a/1` | `function-declaration-not-owner … a/1+` (D5; ownership check first) | **error → different error** (no accepted program changes) |

**What the authorities say about the *old* outcome** (targeted searches; not exhaustive):

| Old behavior | `GENIA_STATE.md` | `GENIA_RULES.md` / `README.md` | Shared spec | Model B contract/design |
| --- | --- | --- | --- | --- |
| Highest-minimum varargs silently wins (#1) | line 809: "if multiple varargs candidates match and neither is more specific, runtime raises `TypeError("Ambiguous function resolution")`" — *specificity is never defined* | RULES 204–205: "fixed-arity match is preferred over varargs match; varargs ambiguity must raise `TypeError("Ambiguous function resolution")`"; README 796–797 | none for ordinary varargs resolution (`r20-varargs-over-fixed-precedence` covers fixed-over-varargs only) | design §2.1 baseline; D1 approved |
| Declaration through a same-scope or imported alias appends (#2–#5) | no statement (only *import* aliases appear) | none | none | contract §2.2 documents **calls** through aliases (`a(1,2)` → `3`), not declarations; D5 approved rejection |

So the **new** outcome of #1 (ambiguity raises) is already stated by RULES/STATE text and the shared R20 shape-stratum behavior; the **new** outcomes of #2–#5 are first established by the approved Model B contract (D5) and exist nowhere in the implemented documents. The **old** outcomes of #2–#5 are not documented portable behavior; the old outcome of #1 is documented only up to an undefined word ("more specific").

**Authority for applicability** (both must be honored): contract §6.1(4) — "reuse the existing R16 runner, manifest protocol and capability selection; never label already-supported ordinary function behavior unsupported to mask regression"; design §13.3 — Model B capabilities start as `unsupported` in C++ with "exact #1250-owned entries in `spec/known_host_gaps.json`, including affected cases"; and "an unsupported C++ negative diagnostic is not PASS".

| | **Option A** — preserve ungated old-program applicability | **Option B** — gate every changed outcome | **Option C** — authority-anchored (recommended) |
| --- | --- | --- | --- |
| Rule | Any case whose program uses old syntax keeps the old (empty) `requires`, plus concern-specific capabilities | Any changed outcome requires `default_open_functions` (P5 included) | A case is ungated iff its **expected outcome is already stated** by STATE/RULES/README, a shared spec, or implemented R20 text; if the outcome is first established by the Model B contract, it requires `default_open_functions`. Unchanged-outcome guards always keep their original applicability |
| P5 | ungated | gated | ungated (RULES 205 + STATE 809 already state the ambiguity rule) |
| #2 `own-local-alias-rejected` | ungated | gated | gated |
| #3 `own-alias-annotation-not-evaluated` | ungated (no refs needed; stdout observation) | gated | gated |
| #4 `own-imported-alias-rejected` | ungated, `multi_file_eval` only | gated | gated (`multi_file_eval` kept) |
| #5 `own-local-alias-varargs` | ungated | gated | gated |
| Pattern-header variant `own-local-alias-pattern-clause` | gated (new syntax) | gated | gated |
| Shared N / G / ungated RED / gated | 116 / 43 / 5 / 68 | 116 / 43 / 0 / 73 | 116 / 43 / 1 / 72 |
| In-process RED (total / pass / fail) | 1017 / 944 / 73 | 1017 / 944 / 73 | 1017 / 944 / 73 |
| External Python RED (pass / fail / unsupported), exit | 926 / 5 / 86, exit 1 | 926 / 0 / 91, exit 0 for that step | 926 / 1 / 90, exit 1 |
| GREEN in-process / external | 1017 / 1017; 999 pass + 18 unsupported | same | same |
| C++ rows for the cases that move | 4 more applicable-by-form cases: 3 `UNSUPPORTED` (observed form: ends in a declaration, varargs, annotations) with one **latent FAIL** (C++ rebinds: `a(x,y)=x+y; a(1,2)` → `3`, observed); 1 capability-gated | no change | no change |
| Host-local companion required? | yes — every changed outcome (#1–#5) gets a before/after test | yes | yes (HL-23) |
| Weakness | forces the shared D5 outcomes onto hosts that, by design §13.3, begin `unsupported`; adds a documented C++ defect for behavior that was never portable | treats the RULES-stated P5 rule like a Model B invention, contradicting contract §6.1(4) for already-stated behavior; weakens the external-run RED signal (the unmodified `unsupported == 18` test, in-process runner and pytest harness still fail) | depends on reading "more specific" as *not* defining the old P5 outcome; a maintainer who disagrees gets Option A or B by changing one row |

**Recommendation: Option C**, as a *policy stated before looking at any host's result* ("a changed outcome is ungated exactly when the outcome is already portable text"), applied identically to the five rows above. It is **not** adopted by this document. The CI consequence (C++ shows no new observed failure under any option) is recorded as a consequence, not a reason. If the maintainer prefers uniform treatment of old-syntax programs, choose A; if the maintainer rules that RULES 205 does not state the P5 outcome, choose B. Whichever is chosen, the host-local before/after companion (HL-23) is required for #1–#5, and the unchanged-outcome guards (`own-alias-call-live`, `open-alias-sees-later-arity`, …) stay ungated.

**Revision-5 correction:** Codex listed seven cases for Option A. Three of them (`own-local-alias-state-after-rejection`, `own-local-alias-owner-still-extendable`, `own-imported-alias-owner-unchanged`) need an observation *after* the rejection, which a one-shot evaluation cannot make; they are host-local in revision 6, so Option A affects four shared cases, not seven. `own-local-alias-varargs` is error → different error (row 5), not valid → error.

### R6.2 O-2 — C++ placement and the revised compatibility ledger

**Observed baseline** (`genia-cpp@44456baea06b4bb7bdf727e39939dd7150261ee6`, also current C++ `main` and the `host-parity.yml` pin; built with the documented CMake commands, `ctest` 3/3; existing shared specs 268 pass / 633 unsupported / 0 failing classes; parity gate `OK` with the Python evidence). The investigation's disposable 52-probe run (1 pass / 2 fail / 49 unsupported) used 36 package-pinned programs and 16 investigator-authored programs; revision 6 replaced every authored program by a specified one and **re-ran the final sources**. Nothing about C++ source or protocol was changed. `unsupported` is never counted as PASS; the gate fails only on failure classes, so a *wrong answer* on an applicable case is the only thing that can break `host-parity.yml`, and no known-gap mechanism can record it (gaps are capability-scoped; an entry for a capability C++ declares supported is a `STALE_GAP`).

**Per-case determination of the eight cases flagged by the investigation** (plus the case revision-6 execution added):

| Case | Intended assertion | Authority | Class | Placement (PROPOSED) | Shared twin | C++ evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `hdr-grouped-body-captures-header` | grouped-body arms see the header parameters | contract §2.2 ("header variable captures … must remain compatible"); design §13.4 ("header frame … acts as parent environment for … function bodies"); not stated in STATE | **required portable behavior** | keep shared, ungated (R6-D2); host-local Python regression stays in the C-HDR family | none needed | **FAIL** (observed): `Undefined name: x` → **CPP-D1**; merge precondition, not a RED precondition |
| `main-repl-never-selects` | REPL activation never auto-runs `main` | structural fact about `_resolve_program_result` (HL-9); the transcript prints a host function representation | **incorrect/nonrepresentative probe** (`<function main/0>` appears in no authority; C++ prints nothing for a block-bodied declaration and `unsupported` for others) | host-local (HL-20) | none (every REPL definition echoes a host value) | FAIL on the probe source; not applicable once host-local |
| `key-legacy-dup-id`, `key-rest-binders-legacy-duplicate`, `d8-legacy-identical-header-dup` | legacy duplicate rejection unchanged | design §13.4 "preserve legacy ordinary error identities"; wording appears only in Python unit tests (`test_f2_p2_*`) and design/analysis docs — not STATE/RULES/README/spec | **Python-host-specific wording**; the rejection itself is **unspecified as portable** (R6-D3) | host-local (HL-21, existing tests already pin the text; companions added after the refactor) | none expressible without pinning the wording | latent difference (observed with a trailing call): C++ replaces the earlier definition (`f(1)` → `2`) → **CPP-D4** if the rejection is declared portable |
| `own-lambda-nonfunction-unchanged`, `own-builtin-nonfunction-unchanged` | declaring a function over a non-function binding keeps its existing diagnostic | R20 contract ("a declaration cannot replace an existing non-function binding"); wording unspecified in STATE | **unspecified** (R6-D3) | host-local (HL-22) | none | latent difference: C++ rebinds (`g(1,2)` → `1`) → CPP-D4 |
| `own-explicit-open-alias-unchanged` (O-5 replacement) | declaring through an alias of an open interface keeps its diagnostic naming the open interface/view | implemented R20 contract ("says that the name holds an open interface view, not a non-function value"); the contract requires pinned CLI text | **required portable R20 behavior** | shared, `open_functions` (R6-D4) | none | UNSUPPORTED as specified (ends in a declaration); latent: with a trailing expression C++ accepts silently (observed) → **CPP-D2** |
| `d8-r20-flattening-unchanged` | explicit-open grouped arms still flatten for duplicate detection | STATE (R20 grouped flattening); `error-r20-local-duplicate-clause` | **required portable R20 behavior** | shared, `open_functions` | none | UNSUPPORTED as specified; latent: C++ returns `1` (no duplicate error; the pre-existing R20 discrepancy design §13.3 says to track separately) → CPP-D2 |
| `meta-inline-doc-shared-via-alias`, `meta-conflicting-inline-doc-before-install` (new in revision 6; the authored probes never exercised inline docs) | inline docstrings (`f(x) = "d" body`) merge/conflict | contract §5.1; design §7 table row for metadata channels lists `doc_help` | **required** metadata-channel behavior | shared; tagged `doc_help` (R6-D5), exactly as 11 existing specs are | none | UNSUPPORTED via the existing `doc_help` gate; the same programs without the gate give `Undefined name: x` → **CPP-D3** (parse defect) |

**Candidate separate C++ defects (to be filed by the maintainer in `genia-cpp`; this repository cannot):** CPP-D1 header capture in ordinary grouped bodies; CPP-D2 R20 explicit-open differences (alias-of-open accepted; redeclaration after an intervening definition accepted; flattened-arm duplicate not detected; `open f(x)=1; f(y)=2; f(3)` returns `1` per the independent review); CPP-D3 inline-docstring definitions mis-parse as an application; CPP-D4 (conditional on R6-D3) legacy duplicate and non-function rebinding replace instead of rejecting. None is hidden behind a capability or counted as conformance.

**Shared → host-local moves (14) and replacements** (every move has a justification above or below and a shared observable twin where one exists):

| Moved case | Why one-shot shared evaluation cannot express it | Host-local item | Shared twin |
| --- | --- | --- | --- |
| `open-persistent-env` | needs successive submissions; REPL echoes host function values (observed `GeniaFunctionGroup(name='f', …)`) | HL-15 | `open-noncontiguous-arities`, `open-pattern-after-plain` |
| `own-local-alias-state-after-rejection`, `own-local-alias-owner-still-extendable` | observation after the rejection | HL-16 | `own-local-alias-rejected` |
| `own-imported-alias-owner-unchanged` | observation after the rejection | HL-17 | `own-imported-alias-rejected` |
| `ann-old-metadata-retained`, `ann-installed-clause-visible-via-alias` | observation after a failed annotation | HL-18 | `ann-later-annotation-suppressed`, `ann-prior-effects-persist` |
| `ann-repl-recovery`, `mode-repl-failed-declaration-leaves-group` | REPL transcript; annotation and target must share one submission (observed: `@doc 7; f(x, y) = x + y` raises the `@doc` error and installs the clause; separate lines fail framing) | HL-19 | one-shot error cases above |
| `main-repl-never-selects` | see table above | HL-20 | none |
| `key-legacy-dup-id`, `key-rest-binders-legacy-duplicate`, `d8-legacy-identical-header-dup` | wording | HL-21 | none |
| `own-lambda-nonfunction-unchanged`, `own-builtin-nonfunction-unchanged` | wording | HL-22 | none |

Replacements: `key-named-matcher` → `key-named-matcher-distinct` + `key-named-matcher-same-dup`; `key-quote-unquote` → `key-quote-names-are-data` (active-unquote half open, R6-D9); `mode-file-command-import-equivalence` → `mode-file-pattern-program`, `mode-command-pattern-program`, `mode-import-pattern-program` (a single case cannot run three modes); `own-explicit-open-unchanged` → `own-explicit-open-alias-unchanged`. Excluded: `key-repeated-binders-distinct`. Reconciliation to the revision-5 count: 127 − 9 (moved, absent from the list) − 5 (moved after re-sourcing) + 1 + 2 (splits) = **116**; the 14 moved + 1 excluded + 4 renamed/split ids are listed one-by-one in the test plan §R6.

**Revised C++ compatibility ledger — summary** ([inferred] where marked; the final sources were executed, the real RED YAML does not exist):

| Group | Count | C++ outcome |
| --- | --- | --- |
| Shared cases | 116 | |
| — applicable (no unmet capability) and sent to the adapter: 28 guards + P5 | 29 | **2 PASS** (`optim-collection-recursion`, `opt-plain-identity-none`), **1 FAIL** (`hdr-grouped-body-captures-header`), 26 UNSUPPORTED (observed) |
| — gated before invocation by an *existing* capability: `immutable_bindings` 4, `multi_file_eval` 3, `doc_help` 8 | 15 | UNSUPPORTED (observed; existing gaps/required-capability claims) |
| — gated by `default_open_functions` (Option C) | 72 | UNSUPPORTED (inferred: undeclared capability; mechanism observed for `immutable_bindings`) |
| Projected C++ external RED totals (inferred) | 1017 | 270 pass / **1 fail** / 746 unsupported → `EVIDENCE FAILURE` until CPP-D1 is fixed, or until the maintainer re-places that case (then 270 / 0 / 746 on 1016) |

Remaining uncertainty: the 26 applicable `UNSUPPORTED` rows are "unsupported as specified" (the program ends in a declaration or uses constructs C++ lacks); extending a source can turn some of them into FAILs, as the table above shows for six cases, and only the programs named in the table above were extended and re-run; the remaining applicable programs were not extended. The real RED sources must be re-run through the pinned adapter (GA-22). The adapter's reason text is generic, so causes are attributed by micro-probes.

### R6.3 R1 — recomputed arithmetic (Option C; projections are inferred, not executed)

| Quantity | Value |
| --- | --- |
| Shared cases N | **116** |
| Ungated guards (G) | **43** (of which 28 are C++-applicable; 15 carry an existing capability that C++ lacks) |
| Ungated RED tripwires | **1** (P5) |
| New-capability-gated RED cases | **72** |
| Host-local items | **24** (14 existing HL-1…HL-14 + 10 new HL-15…HL-24) covering the 14 moved case ids |
| Blocked / excluded | 1 excluded (`key-repeated-binders-distinct`), 1 half-open (active `unquote`), 6 reserved G1 ids |
| C++-applicable cases | 29 (2 pass, 1 fail, 26 unsupported — observed) |
| In-process RED (total / pass / fail) | 1017 / 944 / 73, exit 1 |
| External Python RED (total / pass / fail / unsupported) | 1017 / 926 / 1 / 90, exit 1 |
| In-process GREEN | 1017 / 1017 / 0 |
| External Python GREEN | 1017 / 999 / 0 / 18, exit 0 |
| After G1 approval (+6 gated ids) | in-process GREEN 1023 pass; external GREEN 1005 pass + 18 unsupported |

The 18 is the existing, unmodified parity guard (`unsupported == 18`). At RED the external run reports 90 unsupported (18 + 72) and the parity test would fail with 90 — but that test is `slow`/`full_conformance`, excluded from the ordinary PR selection and run by the scheduled/manual `regression.yml`.

**Workflow behavior at the RED head** (corrected; "when run at that commit"):

| Workflow | Triggers | Behavior at RED |
| --- | --- | --- |
| `ci.yml` Fast tests | every PR, push to `main`, manual | `pytest … -m "not slow and not loopback" --maxfail=1 -n auto` fails on the first failing RED test (xdist makes the stop approximate); the loopback step and the `tools.spec_runner` step are then not run (earlier step failed) |
| `docs.yml`, `validate-llm-instructions.yml`, `code-documentation.yml` | every PR | run normally; expected green absent unrelated change (they are not path-filtered) |
| `host-parity.yml` | PRs/pushes touching `spec/**`, `src/genia/**`, `hosts/**`, `tools/spec_runner/**` — **triggered by the RED commit** | the Python-evidence step exits 1 only if an ungated case fails (P5 under Options A/C; none under B); a failing step stops the job before C++ evidence and the gate |
| `docker-dev-environment.yml` | PRs touching `docker/**`, `README.md`, … | not triggered by RED; **GREEN's `README.md` edit triggers it** |
| `regression.yml` | scheduled and manual only | when run at the RED head: compatibility job fails like `ci.yml`; the full-conformance parity job fails at `unsupported == 90` (inferred) |
| `github-hosted-runner-canary.yml`, `self-hosted-runner-smoke.yml` | their `infra/*` branches and manual dispatch | when run at the RED head, the `tools.spec_runner` step exits 1 |

The in-process runner does not apply the capability gate and executes gated cases; the external runner reports them `unsupported` before invocation, and `unsupported` never changes its exit status.

### R6.4 R3 — additional anti-false-GREEN requirements (GA-1…GA-12 are retained)

| ID | Requirement |
| --- | --- |
| **GA-13** | Exact bidirectional case-id equality: the loader's `model-b-c-*` names equal the literal list; no duplicate names; spec file stems equal names; **zero invalid loader entries** across the whole `spec/` tree; `len` equals the recorded N. A missing or extra file fails. |
| **GA-14** | **Exact `requires` per id**, pinned as a literal id → tuple table (not "subset of the old vocabulary"): replacing one old capability by another, or adding/removing `default_open_functions`, fails. Table equals the §R6 inventory at RED and at GREEN. |
| **GA-15** | **Oracle continuity from the committed RED SHA.** At GREEN, `git diff <RED_SHA>..HEAD` over `spec/**/model-b-c-*`, sibling `.genia` inputs, `tools/spec_runner/**`, `tests/spec/test_python_protocol_adapter_parity_762.py` and the harness constants must be empty, or each hunk must be listed as an explicit reviewed amendment in the GREEN note. Ordinary diff/review; no second expected-output store. |
| **GA-16** | **Per-id real-adapter pass** (sharpens GA-4): for every `model-b-c-*` id, `execute_spec_via_host(spec, <real adapter command>, host_capabilities=_python_claimed_capabilities()).kind == "pass"`. The evidence JSON has only aggregate counts and cannot satisfy this. Runs in the ordinary selection (≈1 process per case). |
| **GA-17** | **Inclusion in ordinary selection:** an assertion plus a recorded command that `pytest --collect-only -q -m "not slow and not loopback" tests/spec/test_model_b_slice_c_red.py` collects exactly the expected parametrized ids; no inherited `slow`/`loopback`/`full_conformance` marker (module, class, conftest, `pytest.ini`). |
| **GA-18** | At GREEN the in-process runner passes every applicable case: `python -m tools.spec_runner` → `total == 901 + N`, `failed == 0`, `invalid == 0`. |
| **GA-19** | The override is phase-exact: `_VOCABULARY_ONLY_CAPABILITIES == frozenset({"default_open_functions"})` at RED and `== frozenset()` at GREEN (§R6.5); GREEN removes the name in the same commit that makes the gated cases pass. |
| **GA-20** | The existing parity guard is unmodified and passes at GREEN: `unsupported == 18`, `passed == total − 18` (GA-5 retained verbatim). |
| **GA-21** | No skip/xfail substitution: AST scan of the harness **and** conftest/`pytest.ini` markers for `skip`, `skipif`, `xfail`, `importorskip`, `pytest.skip(`; plus the recorded run shows `0 skipped, 0 xfailed` for the file. |
| **GA-22** | **C++ case ledger on the exact RED YAML** through the workflow-pinned adapter, recorded per id as PASS / FAIL / UNSUPPORTED with reason class, and `fail = protocol_error = crash = timeout = invalid = 0` before the final head can merge; never infer pass from a `host_parity_gate` `OK`. |
| **GA-23** | Literal-lock procedure: each `PROPOSED`/`L` oracle is locked in the RED commit from the byte-characterized baseline **only where the baseline can emit it**; for text the current runtime cannot emit (ownership diagnostics) the approved candidate text is entered and any later difference is an explicit amendment, not a rebaseline. |

GREEN is the conjunction of GA-2, GA-3, GA-5/20, GA-6/18 and GA-16, **plus** the other items above; the shorter conjunction in §4 is not a permission to omit them.

### R6.5 R5 — corrected C0 phase-guard transition (tests are NOT edited here)

**Defect.** Several C0 tests call `monkeypatch.setattr(adapter, "_VOCABULARY_ONLY_CAPABILITIES", frozenset({"refs"}))`, replacing the **whole** set. At RED the production set contains `default_open_functions`; replacing it drops that name, so the adapter reports it **supported** and `dict(RED_MAP, refs="unsupported")` no longer matches (reproduced by the independent reviewer).

**Fix.** Stage by *union with the production value read at test time*, and compare against a phase-exact expected map; keep `PRE_C0_CAPABILITY_MAP` as frozen history.

| Test (current name) | RED edit | GREEN edit |
| --- | --- | --- |
| module constants | keep `PRE_C0_CAPABILITY_MAP` unchanged; add `RED_CAPABILITY_MAP = {**PRE_C0_CAPABILITY_MAP, "default_open_functions": "unsupported"}` and `PHASE_OVERRIDE = frozenset({"default_open_functions"})`, `PHASE_MAP = RED_CAPABILITY_MAP` | add `GREEN_CAPABILITY_MAP = {**PRE_C0_CAPABILITY_MAP, "default_open_functions": "supported"}`; `PHASE_OVERRIDE = frozenset()`, `PHASE_MAP = GREEN_CAPABILITY_MAP`; `RED_CAPABILITY_MAP` retained as history |
| new helper | `_stage(monkeypatch, *names)` → `setattr(adapter, "_VOCABULARY_ONLY_CAPABILITIES", adapter._VOCABULARY_ONLY_CAPABILITIES \| frozenset(names))` | unchanged |
| `test_override_is_empty_and_immutable_in_production` | rename `test_override_matches_the_phase_and_is_immutable`; assert `== PHASE_OVERRIDE` and `isinstance(..., frozenset)` | assert `== frozenset()` via `PHASE_OVERRIDE` |
| `test_empty_override_capability_map_equals_pre_c0_baseline_exactly` | assert `_python_claimed_capabilities() == PHASE_MAP` **and** `{k: v for k, v in claimed.items() if k != "default_open_functions"} == PRE_C0_CAPABILITY_MAP` (35 historical names unchanged) | same two assertions with the supported map |
| `test_default_open_functions_is_not_in_the_vocabulary_or_the_override` | invert: in `known_capabilities()` (manifest has it, optional, **not** required), in the override, claimed `unsupported` | in the vocabulary, **not** in the override, claimed `supported` |
| `test_staged_known_capability_is_reported_unsupported_and_others_unchanged` | `_stage(…, "refs")`; expected `dict(PHASE_MAP, refs="unsupported")` | same expression |
| `test_staging_overrides_the_partial_status_too` | `_stage(…, "shared_spec_runner")` | same |
| `test_staging_an_unknown_name_is_rejected_not_added` | `_stage(…, "not-a-real-capability")` → `ValueError` | same |
| `test_staged_capability_case_is_unsupported_without_invoking_the_host` | `_stage(…, "refs")`; **add** a twin witness for a spec requiring `default_open_functions` using the *production* map: `unsupported`, marker file absent | the same spec is **applicable** (`case_is_applicable` true) and the witness is replaced by GA-16 |
| `test_ungated_case_is_not_affected_by_staging`, `test_empty_override_leaves_existing_r20_capability_gating_unchanged`, `test_claimed_names_equal_known_vocabulary_with_and_without_staging` | `_stage` for the staged variants; assertions unchanged | unchanged |

Preserved without weakening: unknown-name fail-closed, complete vocabulary (`set(claimed) == known_capabilities()` — now 36 names), statuses ⊆ `CAPABILITY_STATUSES`, `partial` precedence, existing `open_functions`/`multi_file_eval` claims, the no-invocation witness, and the unmodified parity guard. The four tests the independent rehearsal showed failing at RED are exactly the rows above that change at RED; transitional pattern-rejection tests (`test_model_b_slice_a.py::test_transitional_rejection`, `test_model_b_slice_b.py::test_closed_and_pattern_declarations_remain_not_implemented`, the two MCP-profile probes) change **at GREEN only**, closed-group rejection stays.

### R6.6 O-3 — PROPOSED amendment to the Model B design (not applied; explicit approval requested)

Observed (independent review, repeated here): relative and absolute file invocations both render the **resolved absolute entry path** in the existing R20 duplicate renderer (`… first at /<abs>/dup.genia:1, duplicate at /<abs>/dup.genia:2`); command mode renders `<command>:1/2`. Design §3.4 ("Render canonical imported module names or the existing entry label, never filesystem paths, object addresses or captured values") and §13.5 ("without leaking host-only absolute paths, captured values or protected data") therefore overstate the property for duplicate-clause diagnostics. A claim that the existing renderer is path-free would be false.

**Proposed replacement for the quoted sentence in design §3.4:**

> Diagnostics keep source provenance as follows. **Duplicate-clause source-location diagnostics** reuse the existing R20 renderer: imported-module clauses render the canonical module identity; entry clauses render the existing entry label, which is `<command>` in command mode and the host-resolved entry path in file mode. **Ownership and foreign-alias diagnostics** (`function-declaration-not-owner`) are path- and span-free and name only the declared name, the owning binding and, for a foreign owner, the canonical module identity or `<entry>`. **No diagnostic** renders host object addresses, captured values or protected (R10) values, or host-specific output representations of function values. Span-free direct IR has deterministic unknown-location diagnostics and never fabricates locations.

**Proposed replacement for the §13.5 sentence "Preserve file/entry diagnostic provenance without leaking host-only absolute paths, captured values or protected data":**

> Preserve file/entry diagnostic provenance exactly as the existing R20 renderer produces it (the resolved entry path appears in file-mode duplicate-clause diagnostics and is the one sanctioned location-bearing surface); new ownership and foreign-alias diagnostics carry no path or span; no diagnostic leaks host addresses, captured values or protected data.

Consequences if approved: shared exact duplicate oracles use command mode (`<command>:N`); the file-mode path format is pinned only host-locally (HL-12, `str(Path(file).resolve())`); ownership texts stay path-free (HL-11). Record the approval on #1269, then align both design clauses; until then no file-mode duplicate oracle is locked.

### R6.7 O-4, O-5, O-6

- **O-4.** `key-repeated-binders-distinct` stays excluded; nothing in STATE, the contract or the design defines non-linear (repeated-binder) pattern semantics, and none is inferred from Python's duplicate-parameter handling.
- **O-5.** `own-explicit-open-unchanged` is replaced by **`own-explicit-open-alias-unchanged`**: `open f(x) = x` / `a = f` / `a(x, y) = x + y`, category `error`, `requires: [open_functions]`. Observed: stdout empty, exit 1, stderr exactly `Error: Cannot define function a/2: name is bound to an open function interface or linked view, which an ordinary definition cannot replace` + newline (the same observation the independent review reported). The previous program (`open f(0)=1; g(x)=x; f(n)=n`) triggers `open-function-redeclaration`, a different rule. Placement: the R20 contract requires such diagnostics to name the open interface/view and to be pinned as CLI text, so the case is **shared**; C++ accepts the program when it is extended with a trailing expression (CPP-D2), and is `UNSUPPORTED` as specified.
- **O-6.** The 13 `L` rows are **11 error observations and 2 successful REPL observations**. The two REPL rows (`open-persistent-env`, `main-repl-never-selects`) are host-local (HL-15, HL-20) because REPL echoes host function representations. The 11 error rows, with source, category, expected text and status in the test plan §R6: `key-same-binary64-dup`, `key-spelling-dup`, `key-alpha-equivalent-dup`, `key-guard-alpha-dup`, `disp-duplicate-pattern-header` (renderer text observed on the explicit-open twin; byte-locked at RED), `disp-no-matching-function-new-group` (twin-observed), `main-explicit-call-miss` (twin-observed), and the ownership family `own-local-alias-rejected`, `own-local-alias-pattern-clause`, `own-local-alias-varargs`, `own-imported-alias-rejected` (**candidate text only**: the current runtime cannot emit the new category, so no "observation" is claimed; the texts are the pre-flight D3 proposals and need approval, R6-D8). Conventions: eval/error stdout/stderr are compared exactly and end in `\n`; CLI stdout/stderr are normalized by the runner (CRLF → LF, trailing newlines stripped); source locations are `<command>:N` in shared oracles (N = 1-based line in the submitted source); no file path appears in any shared oracle.

### R6.8 G1 — corrected (recorded, **not approved, not implemented**)

Recommended conservative invariant (unchanged): the existing CLI entry selector invokes `main` automatically only when the **whole** function group contains legacy identifier-header records with no two records sharing a required-arity key; otherwise it silently keeps the source-result fallback without executing any record, matcher, guard or body and without a new diagnostic. Eligible groups keep `main/1` → `main/0` → source-result behavior; explicit calls dispatch normally. Shape SC-MAIN-3 has **two declaration orders**, so there are **six** cases, not five (all `requires: [default_open_functions]`, file/command CLI shape, stdout `top` / `42` with no `main` output; programs proposed only — they cannot run before GREEN):

`model-b-c-main-g1-mixed-main0-plus-pattern`, `model-b-c-main-g1-mixed-main1-plus-pattern`, `model-b-c-main-g1-main1-plus-pattern-arity1-legacy-first`, `model-b-c-main-g1-main1-plus-pattern-arity1-pattern-first`, `model-b-c-main-g1-fixed-plus-rest-same-minimum`, `model-b-c-main-g1-legacy-rest-plus-pattern-arity1`.

If approved: N becomes 122; in-process GREEN 1023; external GREEN 1005 pass + 18 unsupported. They do not change the RED set. G1 stays a before-GREEN decision; #1271/#1272 are untouched.

### R6.9 Outstanding blockers after revision 6

1. R6-D1…R6-D9, R6-D11 (register above), then independent verification at the new exact head.
2. A separate TEST-ONLY RED authorization naming exact ids and expected outcomes (R6-D13); intentional RED failures must be recorded per id without weakening any guard.
3. Filing CPP-D1…CPP-D4 and fixing CPP-D1 (and the R20 differences, if their cases stay shared) before the final head can merge.
4. G1 before GREEN.

### R6.10 Validation (revision 6; exec unless noted)

Run in a clean worktree of the revision-6 tree with `PYTHONPATH=<worktree>:<worktree>/src` and the repository `.venv`:

| Check | Result |
| --- | --- |
| `pytest -p no:cacheprovider -q tests/doc -n 4` | 397 passed, 35 skipped |
| `pytest -q tests/doc/test_semantic_doc_sync.py tests/doc/test_state_anchors_and_registry_sync.py tests/doc/test_portability_contract_sync.py` | 244 passed, 34 skipped |
| `python tools/validate_llm_instructions.py` | LLM instruction validation passed |
| `python -m mkdocs build --strict` | exit 0 |
| `python tools/gen_mcp_language_profile.py --check` | exit 0 |
| `pytest -q tests/unit/test_python_protocol_adapter_c0_capability_staging_1269.py tests/unit/test_host_parity_gate.py` (unchanged tests, baseline sanity) | 39 passed |
| `git diff --check` | clean |

Evidence behind the inventory (not committed; reproducible with the repository's own helpers): every shared source in the test plan §R6 was sent to the Python protocol adapter with the capability gate bypassed to record the baseline, every explicit-open twin was run the same way, and every applicable source was sent to the pinned C++ adapter through `execute_spec_via_host`-equivalent code. Consistency checks that passed: all 43 guards produce their expected value today; all 73 non-guard rows (1 tripwire + 72 gated) differ from it today; every twin-derived expected value equals the twin's output. **Limitations:** no RED YAML exists, so GA-13…GA-23 are plans, not results; the 72 gated rows' C++ status is inferred; the full test suite, the full external runs, the loopback partition and the workflows were not re-run for this documentation-only change (revision-5 baselines stand: in-process 901/901, external 883 pass + 18 unsupported); `genia-cpp` GitHub issues could not be searched from this session, so CPP-D1…CPP-D4 are candidate defects, not filed issues.

---

## 0. What was refreshed and verified (revision 5; history)

- `origin/main` is `79c073b`. The commits since the pre-flight base (`6d50a36`) are: C0 (#1273: `0e63dc1`, plus the maintainer's two documentation-gate repair commits `e9246ed`/`ac7c270`/`2ccd8c8`) and #1271/#1272 (application-lifecycle contract/design **drafts** and a pre-flight under `docs/design/*-DRAFT.md` and `.genia/process/`). **exec:** `git diff --stat 6d50a36 origin/main` touches no `src/`, `spec/`, `tools/spec_runner`, root authority file or Slice C document. No intervening change to the Slice C plan or implementation. #1271/#1272 stay out of Slice C.
- **C0 mechanism verified on merged `main` (read):** `hosts/python/protocol_adapter.py` defines `_VOCABULARY_ONLY_CAPABILITIES: frozenset[str] = frozenset()`; `_python_claimed_capabilities` raises `ValueError` for names outside `known_capabilities()` and reports staged names `unsupported` ahead of the `partial`/`supported` branches. The 11 C0 tests (`tests/unit/test_python_protocol_adapter_c0_capability_staging_1269.py`) pass (exec, §2.2). The independent C0 review (#1273 `6333124626`) is PASS; the integration owner accepted and merged.
- The accepted pre-flight architecture (D1, numeric keys, D3, D3b, D5, D8, U2 boundary, C-MAIN, C0 design) is **not reopened**. This package adds R1–R5 detail, records G1, and corrects directly relevant stale facts (§8.4).

---

## 1. R-conditions at a glance

| Condition | Disposition in this package | Section |
| --- | --- | --- |
| R1 command / CI matrix | Done: 12 execution paths, observed baselines (exec), inferred RED/GREEN counts derived from an exact case-ID set, capability-mechanics **rehearsal** | §2 |
| R2 exact non-slow harness and case set | Done: harness specified; **127 shared case IDs** (51 G, 1 ungated R, 75 gated RG) plus host-local inventory; oracle status per case (D 73 / A 41 / L 13) and one blocked case (B) reserved, not created | §3 |
| R3 anti-false-GREEN | Done: assertions GA-1…GA-12, RED→GREEN capability sequence | §4 |
| R4 diagnostic paths | Done per the directed disposition; grounded command-/file-mode examples (exec); one **design-text clarification required before RED** (§5.5) | §5 |
| R5 manifest / docs sync | Done: manifest edit, override timing, test impact (rehearsal), intentional phase-guard changes, GREEN removal | §6 |
| G1 | **Recorded only; pending maintainer approval before GREEN**; GREEN tests identified | §7 |
| Unresolved | O-1 … O-6 (gating consistency of the D5 breaking changes, ungated cases vs the C++ evidence path, R4 design text, plan source defects, one blocked oracle, one wrong program) | §8 |

---

## 2. R1 — RED/GREEN execution matrix **[counts and workflow rows superseded by §R6.3]**

### 2.1 Observed baselines (exec; `main@79c073b`, clean, `.venv` from `uv sync`)

| # | Path | Exact command | Observed baseline |
| --- | --- | --- | --- |
| E1 | In-process shared runner (`ci.yml`, `regression.yml`, canary, self-hosted smoke use this) | `uv run python -m tools.spec_runner` | `Summary: total=901 passed=901 failed=0 invalid=0`, exit 0 |
| E2 | External Python protocol adapter | `uv run python -m tools.spec_runner --verbose --host-jobs 8 --host "<venv>/bin/python -m hosts.python.protocol_adapter" --host-timeout 30 --evidence py_evidence.json` | `total=901 passed=883 failed=0 unsupported=18 protocol_error=0 crash=0 timeout=0 invalid=0`, exit 0; evidence `counts` `{pass 883, fail 0, unsupported 18, protocol_error 0, crash 0, timeout 0, invalid 0}`, 35 capabilities |
| E3 | Existing Python protocol parity test (`regression.yml` job *Full Python protocol conformance*) | `uv run pytest -q -m full_conformance tests/spec/test_python_protocol_adapter_parity_762.py` | `1 passed in 527.73s`, exit 0 (asserts `unsupported == 18`, `passed == total − 18`, all failure classes 0, exit 0) |
| E4 | Host parity gate (Python side, C++ unavailable) | `uv run python -m tools.spec_runner.host_parity_gate --python-evidence py_evidence.json --cpp-unavailable-reason "no genia-cpp checkout in this session" --known-gaps spec/known_host_gaps.json` | `C++ PARITY NOT EVALUATED …`, `OK`, exit 0. **Limit:** the C++ comparison (`docker`/`genia-cpp` build in `host-parity.yml`) was not run here |
| E5 | Focused suites | `uv run pytest -q -p no:cacheprovider tests/spec/test_r20_open_functions_shared_specs.py tests/unit/test_python_protocol_adapter_762.py tests/unit/test_python_protocol_adapter_c0_capability_staging_1269.py tests/unit/test_spec_runner_capabilities.py tests/unit/test_host_parity_gate.py tests/unit/test_model_b_slice_a.py tests/unit/test_model_b_slice_b.py tests/unit/test_model_b_optimizer_regression.py` | `216 passed` |
| E6 | `tests/doc` | `uv run pytest -q -p no:cacheprovider tests/doc -n 4` | `397 passed, 35 skipped`, exit 0 |

The Slice B-era "874 passed" figure in the plan is stale; **901** is the measured count.

### 2.2 Runner semantics this matrix relies on (read, with exec corroboration)

- **In-process** (`runner.py::_run_in_process` → `executor.execute_spec` → `comparator.compare_spec`): `requires` is validated by the loader but **never consulted**; the buckets are `passed / failed / invalid` only; exit 1 iff `failed` or `invalid` is non-zero. **Rehearsal:** with `default_open_functions` staged `unsupported`, a gated throw-away case was *executed* and reported `FAIL` (`total=903 passed=901 failed=2 invalid=0`, exit 1). So the in-process run cannot report a gated case `unsupported`, and a RED head fails it.
- **External host** (`_run_via_host` → `host_executor.execute_spec_via_host`): a case whose `requires` are not all `supported` in the host's claimed map is `unsupported` **before the adapter is invoked for that case** (the `capabilities` request itself is still made once). Exit is non-zero iff `failed`, `protocol_error`, `crash`, `timeout` or `invalid` is non-zero; **`unsupported` never affects the exit code**.
- **Pytest** `-m "not slow and not loopback"` (the required `ci.yml` / `regression.yml` selection) collects every test not marked `slow`/`loopback`. `full_conformance`-marked tests are `slow` and excluded from that selection (`pytest.ini`), and are run by the dedicated `regression.yml` job.

### 2.3 Expected counts, derived from the exact case set in §3 (inferred)

Let `N=127` new shared cases = 51 **G** (pass today) + 1 **R** (ungated P5 tripwire; fails today) + 75 **RG** (gated by `default_open_functions`; fail today). Existing suite: 901.

| Path | Baseline (exec) | RED expectation (inferred) | GREEN expectation (inferred) |
| --- | --- | --- | --- |
| In-process runner | 901 / 0 / 0, exit 0 | `total=1028 passed=952 failed=76 invalid=0`, **exit 1** (76 = P5 + 75 gated, all executed because the gate is not applied) | `total=1028 passed=1028 failed=0 invalid=0`, exit 0 |
| External Python host | `passed=883 unsupported=18`, others 0 | `total=1028 passed=934 failed=1 unsupported=93 protocol_error=0 crash=0 timeout=0 invalid=0`, **exit 1** (the single failure is the ungated P5 case; 93 = 18 + 75 gated, all `unsupported` before invocation, **not** passes) | `total=1028 passed=1010 failed=0 unsupported=18 …`, exit 0 |
| `test_python_protocol_adapter_parity_762.py` (**unmodified**) | passes (`unsupported == 18`) | **fails**: `counts["unsupported"] == 18` (actual 93), then `failed == 0` (1) and `exit_code == 0` (1) would also fail. Expected and honest; the assertion must **not** be edited to 93 | passes, unchanged: `unsupported == 18`, `passed == total − 18` |

Why P5 is ungated and why that matters: with every Slice C gated case `unsupported`, an external run would otherwise exit **0** with 75 more unsupported cases and no failure — a false green. The ungated P5 tripwire (it changes ungated ordinary behavior) is the one case that makes the external run non-zero at RED, and the unchanged `unsupported == 18` assertion is the permanent guard that no gated case may stay `unsupported` at GREEN. (But see O-2 for the C++ consequence of ungated cases.)

### 2.4 Full path matrix

| # | Path | Command (exact) | Baseline | RED expectation | GREEN expectation | Exit | Evidence | Guard against false GREEN |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P1 | Direct RED harness | `uv run pytest -q tests/spec/test_model_b_slice_c_red.py` | file absent; analogous R20 wrapper passes (E5) | 127 parametrized + structural tests: **76 fail** (P5 + 75 gated, with `compare_spec` messages retained), 51 G pass, structural tests pass | all pass; harness becomes the thin wrapper | RED 1 → GREEN 0 | harness absent now → inferred; mechanism exec (E5) | exact ID-set equality; static no-skip/xfail/slow guard (§4 GA-8); RG cases assert `requires` contains the capability |
| P2 | Default in-process runner | E1 command | 901/0/0 | `1028/952/76/0`, exit 1 | `1028/1028/0/0`, exit 0 | 1 → 0 | mechanism rehearsal; counts inferred | cannot hide: no gate applied |
| P3 | External Python adapter | E2 command | `883 pass / 0 fail / 18 unsupported` | `934 / 1 / 93 / 0…`, exit 1 | `1010 / 0 / 18 / 0…`, exit 0 | 1 → 0 | mechanism rehearsal; counts inferred | P5 ungated; GA-4 requires gated IDs `pass` not `unsupported` |
| P4 | Existing parity test | E3 command | pass | **fails** (3 assertions, see §2.3) | passes unchanged | fail → pass | read + arithmetic; mechanism exec (E2) | assertion unmodified |
| P5a | Host parity gate unit tests | `uv run pytest -q tests/unit/test_host_parity_gate.py` | pass | pass unchanged (fabricated evidence; no real C++ build) | pass unchanged | 0 | exec (E5) | — |
| P5b | Host parity gate CLI (`host-parity.yml`) | E4 command, plus C++ evidence in CI | `OK` (Python side) | the workflow's *Generate Python reference-host evidence* step exits 1 (P5) before the gate; if evidence were fed to the gate, `fail ≥ 1` is an `EVIDENCE FAILURE`. With the C++ entry present, `default_open_functions` is `KNOWN_GAP` (not `UNDOCUMENTED_GAP`); **see O-2 for ungated new cases on the C++ side** | gate `OK`; `default_open_functions` stays `KNOWN_GAP` (C++ undeclared, entry present — not `STALE_GAP`) | 1 → 0 | rehearsal for Python side; C++ side inferred | gap entry `affected_tests` must equal the gated ID set exactly (GA-9) |
| W1 | `ci.yml` *Fast tests (py3.14)* | `ruff check .`; `pytest -q -vv --maxfail=1 --cov=genia -m "not slow and not loopback" -n auto`; `… -m "not slow and loopback"`; `python -m tools.spec_runner` | green | red: the first pytest step fails (P1 is non-slow and collected); remaining steps skipped by `--maxfail`/step failure; the `tools.spec_runner` step would also exit 1 | green | 1 → 0 | source (workflow) + inferred | the harness is not slow/xfail/skip |
| W2 | `regression.yml` *Compatibility (py matrix)* | same two pytest selections + `python -m tools.spec_runner` | green | red (same as W1) | green | 1 → 0 | source + inferred | — |
| W3 | `regression.yml` *Slow tests (sections)* | `pytest -q -v -m "slow and not full_conformance" tests/<section>/` | green | unchanged (harness is not `slow`) | unchanged | 0 | source | — |
| W4 | `regression.yml` *Full Python protocol conformance* | `pytest -q -v -m full_conformance tests/spec/test_python_protocol_adapter_parity_762.py` | green | red (= P4) | green | 1 → 0 | source + inferred | unmodified assertion |
| W5 | `github-hosted-runner-canary.yml` | `tools/validate_llm_instructions.py`; `python -m tools.spec_runner`; `pytest -q tests/unit/test_cheatsheet_*.py` | green | the semantic-specs step exits 1 | green | 1 → 0 | source + inferred | — |
| W6 | `self-hosted-runner-smoke.yml` | `python3 -m tools.spec_runner` (plus toolchain checks) | green | exits 1 | green | 1 → 0 | source + inferred | — |
| W7 | `host-parity.yml` (path-triggered by `spec/**`, `hosts/**`, `tools/spec_runner/**`, `src/genia/**`) | Python evidence (`--host-jobs 8`), C++ evidence, `host_parity_gate` | green | red at the Python evidence step (P5) | green | 1 → 0 | source + inferred | see P5b / O-2 |
| W8 | `code-documentation.yml` | `python -m tools.code_documentation [--base-ref <base>] --inventory …`; `pytest -q tests/unit/test_code_documentation.py` | green | **new or changed bindings in the harness and adapter must be documented in the same commit** (C0 needed two repair commits for this); do not add baseline entries | same | — | read (C0 history) | follows `docs/contract/code-documentation.md` |
| W9 | `docs.yml` (mkdocs `--strict`), `validate-llm-instructions.yml`, `docker-dev-environment.yml` | as workflows | green | not triggered by RED (no `docs/`, `README.md` or `docker/` change). **GREEN's documentation edits do trigger them** (`README.md` triggers the docker/C++ conformance job) | green | — | source | — |

*Requirement placed on RED authorization:* RED is a red head by definition — W1, W2, W4, W5, W6 and W7 are **expected** to fail on the RED commit and must not be "fixed" by editing the harness, the parity test, the runner, counts, or by marking anything `slow`/`xfail`/`skip`/`unsupported`. The RED evidence note must record the measured counts against the table in §2.3.

### 2.5 Capability-mechanics rehearsal (exec; throw-away worktree, **not** RED)

To observe the mechanics in §2.2 without writing any Slice C case, a scratch worktree of `main@79c073b` was given: `default_open_functions` appended to `optional_capabilities`, the name added to the override, a C++ gap entry, and **two throw-away eval cases** (one with `requires: [default_open_functions]`, one ungated), each expecting impossible output. Nothing was committed or pushed.

| Rehearsal run (scratch worktree of `main@79c073b`, never committed) | Command | Observed |
| --- | --- | --- |
| In-process runner | `python -m tools.spec_runner` | `total=903 passed=901 failed=2 invalid=0`, exit 1 — **both** throw-away cases were *executed* and reported `FAIL` (the gated one too: the in-process path does not apply the capability gate) |
| External Python host | `python -m tools.spec_runner --verbose --host-jobs 8 --host "<venv>/bin/python -m hosts.python.protocol_adapter" --host-timeout 30 --evidence reh_evidence.json` | `total=903 passed=883 failed=1 unsupported=19 protocol_error=0 crash=0 timeout=0 invalid=0`, exit 1; the gated case printed `UNSUPPORTED` (0.000 s, adapter never invoked for it); the ungated case printed `FAIL`; evidence `capabilities["default_open_functions"] == "unsupported"` (36 names), `counts.unsupported == 19`, `applicable_cases == 903` |
| Host parity gate on that evidence | `python -m tools.spec_runner.host_parity_gate --python-evidence reh_evidence.json --cpp-unavailable-reason rehearsal --known-gaps spec/known_host_gaps.json` | `EVIDENCE FAILURE: python evidence has fail=1 (must be 0)`, `FAIL`, exit 1 |
| `check_parity` with fabricated C++ evidence (name undeclared by C++) | direct call | with the gap entry: `KNOWN_GAP`; without it: `UNDOCUMENTED_GAP`, `ok == False` |
| `tests/doc` with manifest + override + gap edits | `pytest -q tests/doc -n 4` | `397 passed, 35 skipped` — unchanged from baseline |
| Capability / adapter / Slice A·B unit suites with the same edits | `pytest -q tests/unit/test_python_protocol_adapter_762.py tests/unit/test_python_protocol_adapter_c0_capability_staging_1269.py tests/unit/test_spec_runner_capabilities.py tests/unit/test_host_parity_gate.py tests/unit/test_model_b_slice_a.py tests/unit/test_model_b_slice_b.py` | `4 failed, 147 passed` — the four failures are exactly four C0 phase-guard tests (§6.3); nothing else moved |

This confirms, by execution, the +1 `unsupported` / +1 `failed` arithmetic that §2.3 scales to 75 / 1, that an ungated failing case is what makes the external run exit non-zero, and that only the C0 phase guards (not `tests/doc`, not the parity gate unit tests) break on the manifest + override edit.

---

## 3. R2 — exact RED harness and case set **[inventory superseded by the test plan §R6; harness design retained]**

### 3.1 Harness specification (design only; not implemented here)

File `tests/spec/test_model_b_slice_c_red.py`. It reuses only existing machinery: `tools.spec_runner.loader.discover_specs/load_spec`, `tools.spec_runner.executor.execute_spec`, `tools.spec_runner.comparator.compare_spec` (the pattern of `tests/spec/test_r20_open_functions_shared_specs.py`). It creates no runner, comparator, evaluator, protocol or expected-output store.

1. **Selection.** Constants `SLICE_C_CASE_IDS` (the 127 IDs of §3.3, literal), `SLICE_C_GATED_IDS` (75), `SLICE_C_UNGATED_RED_IDS = ("model-b-c-disp-p5-varargs-minima-ambiguity",)`. `test_case_id_set_is_exact` loads all specs, selects names starting `model-b-c-`, and asserts **set equality in both directions** and `len == 127` (non-vacuous; a missing or extra file fails).
2. **Applicability checks.** `test_gated_cases_require_the_capability` — every ID in `SLICE_C_GATED_IDS` has `default_open_functions` in `spec.requires`, and no other `model-b-c-` ID has it. `test_guard_cases_keep_original_requires` — every G case's `requires` ⊆ the pre-existing capability vocabulary (never the new name). `test_p5_tripwire_is_ungated`.
3. **Per-case test.** `@pytest.mark.parametrize("spec", specs, ids=name)`: `actual = execute_spec(spec)`; `failures = compare_spec(spec, actual)`; `assert not failures, <expected/actual retained>`. Ordinary assertions only. It executes **every** selected case, including gated ones — this is the one place the external-host gate is bypassed, which is what makes RED visible.
4. **Markers.** None of `slow`, `xfail`, `skip`, `skipif`, `loopback`. Runs under the ordinary required selection (`-m "not slow and not loopback"`); `tests/spec` is already collected by W1/W2.
5. **Genuine RED.** Against the current implementation the 75 RG cases and P5 fail; the 51 G cases pass. This split is an **inferred** expectation for the RED author to *prove* by running the harness and recording `selected / passed / failed / invalid / unsupported(=0)` and each failure message. A G case that fails today, or an RG/R case that passes today, is a stop condition (the oracle or the classification is wrong), not something to adjust.
6. **Ungated C-MAIN guards.** `main-legacy-*`, `main-no-qualifying`, `main-command-mode` (and `main-repl-never-selects` with `requires: repl`) are G cases in the set; they pass today (exec) and must pass through every refactor.
7. **No hiding through capability staging.** The harness never consults capability claims; staging only affects the external-host path.
8. **Host-local tests** (§3.4) live in `tests/unit/test_model_b_slice_c_*.py`, run in the required selection, and say in their module docstrings that they cover Python internals (per AGENTS "Portable-behavior test placement").

### 3.2 Oracle status legend

- **D** — derived: the expected result follows from an approved decision/contract text *and* (where a current-behavior fact is cited) was observed in this session.
- **A** — author-at-RED: the observation and its expected outcome follow from an approved rule, but the accepted plan does not pin the source text (or a dependent API). The RED author writes the source, byte-characterizes the baseline, and **stops** (SC) if the result contradicts the stated outcome. Not an invented oracle: no expected value is changed without a recorded amendment.
- **L** — literal-lock: the outcome class and shape are derived, but the exact diagnostic string is locked only after byte-characterization at the RED baseline (maintainer directive, U4). Where an `open` twin already produces the renderer text (exec), the expected string is shown.
- **B** — blocked: the oracle cannot be derived from accepted sources. Listed for traceability, **not created** in RED until resolved.

"exec" in the Baseline column means the program was run through the existing in-process adapter (`hosts.python.adapter.run_case`, the path the shared runner uses) or the CLI on `main@79c073b`; `model-b-not-implemented: …` abbreviates `model-b-not-implemented: declaration evaluation is not available` (exec, same text for every pattern-bearing declaration).

### 3.3 Exact case-ID inventory (shared R16 YAML, `spec/{eval,error,cli}/model-b-c-*.yaml`)

Kinds: **G** passes today, original applicability, must stay green · **R** ungated, fails today · **RG** fails today, `requires` includes `default_open_functions`. 128 rows listed, 127 created (one **B** reserved).


#### C-OPEN

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `open-noncontiguous-arities` | G | - | exec: `[1, 3]` | `[1, 3]` | D |
| `open-alias-sees-later-arity` | G | - | exec: `3` | `3` | D |
| `open-immutable-alias-stays-live` | G | immutable_bindings | exec: `3` | `3` | D |
| `open-call-before-later-clause` | G | - | exec: `No matching function: f/2. Available: f/1` | same (byte-identical) | D |
| `open-pattern-after-plain` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `[0, 1]` (earlier catch-all wins) | D |
| `open-noncontiguous-pattern` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | stdout `a` then `["a", "b"]` (`f(0)="a"; g(y)=y; print(f(0)); f(1)="b"; [f(0), f(1)]`) | D |
| `open-lambda-factory-distinct` | G | - | exec (corrected source, see §2 note): `[2, 3, true, false]` | `[2, 3, true, false]` for `mk(k) { g = (x) -> x + k; g }` | D |
| `open-persistent-env` | RG | default_open_functions, repl | REPL transcript fails (no clause install) | group grows across submissions; `f(0, 5)` → `5` | L |

#### C-PAT

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `pat-literal-base-case` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `120` | D |
| `pat-guard-selects` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `["pos", "other"]` | D |
| `pat-guard-sees-header-binding` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `[3, 6]` | D |
| `pat-match-local-shadows-outer` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `1` | D |
| `pat-list-rest` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `[2, 3]` | D |
| `pat-map` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `5` | D |
| `pat-some` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `3` | D |
| `pat-err` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `"bad"` | D |
| `pat-wildcard` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `1` | D |
| `pat-first-match-wins` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `1` | D |
| `pat-fixed-miss-no-varargs-fallthrough` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `Error: No matching case for function f/1 with arguments [5]`, exit 1 | D |
| `pat-fixed-miss-two-args-varargs` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `2` | D |
| `pat-named-matcher` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | named pattern (`pattern Name(value) = body`, STATE §3) used as a header; result per matcher | A |
| `pat-string-body-is-body` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `f("a")` → body string; `doc` observation not derivable yet | A |

#### C-KEY

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `key-true-vs-one` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `[1, 2]` | D |
| `key-one-vs-one-point-zero` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `[10, 10]` | D |
| `key-same-binary64-dup` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)` (renderer reproduced by the executed `open` twin) | L |
| `key-spelling-dup` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)` (renderer reproduced by the executed `open` twin) | L |
| `key-alpha-equivalent-dup` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)` (renderer reproduced by the executed `open` twin) | L |
| `key-guard-alpha-dup` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)` (renderer reproduced by the executed `open` twin) | L |
| `key-guard-differs-ok` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `[1, 2]` | D |
| `key-free-name-syntactic` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `limit = 1; cap = 1`, guards `x > limit` / `x > cap` → both install; `f(5)` → first | D |
| `key-lambda-shadow-dup` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | duplicate error (text as above) | A |
| `key-lambda-shadow-outer-slot-distinct` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | both install (inner binder shadowing an outer pattern binder is not collapsed with one referencing the outer slot) | A |
| `key-quote-unquote` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | quoted names are data; active unquote participates | A |
| `key-repeated-binders-distinct` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `f(x, x)` vs `f(a, b)` — **repeated-binder (non-linear) pattern semantics are not specified in the accepted plan or contract** | B |
| `key-rest-binders-legacy-duplicate` | G | - | exec: `Duplicate function definition: f/1` for `f(x, ..r)=1; f(y, ..s)=2` | unchanged legacy duplicate (both plain identifier headers) | D |
| `key-named-matcher` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | distinct matcher references distinct; same reference duplicate | A |
| `key-no-effects` | RG | default_open_functions, refs | `model-b-not-implemented: declaration evaluation is not available` | rejected duplicate runs no guard/matcher/body; `Ref` log empty (`ref`/`ref_update`/`ref_get` exist: exec) | A |
| `key-legacy-dup-id` | G | - | exec: `Duplicate function definition: f/1` | unchanged | D |
| `key-r20-delta-true-one` | RG | open_functions, default_open_functions | exec: `open-function-duplicate-clause … ('fixed', 1) …` (P13) | `[1, 2]` (approved R20 acceptance change) | D |
| `key-r20-delta-one-float` | RG | open_functions, default_open_functions | exec: duplicate error (P13) | `open f(1)=1; f(1.0)=2; f(1.0)` → `1` | D |

#### C-DISP

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `disp-p5-varargs-minima-ambiguity` | R | - | exec: `"min2"` (wrong) | `Error: Ambiguous function resolution: f/2. Matching varargs: f/1+, f/2+`, exit 1 | D |
| `disp-p5-migration-fixed-clause` | RG | default_open_functions | exec: `Duplicate function definition: f/2` | `"exact2"` | D |
| `disp-p5-migration-drop-lower` | G | - | exec: `"min2"` | `"min2"` | D |
| `disp-p7-same-arity-ambiguity` | G | - | exec: `Ambiguous function resolution: f/3. Matching varargs: f/1+, f/2+` | unchanged | D |
| `disp-fixed-over-varargs` | G | - | exec: `["exact", "varargs"]` | unchanged | D |
| `disp-fixed-and-varargs-same-arity` | RG | default_open_functions | exec: `Duplicate function definition: f/1` (P4) | `[1, 2]` | D |
| `disp-no-matching-function` | G | - | exec: `No matching function: f/2. Available: f/1` | byte-identical | D |
| `disp-no-matching-function-new-group` | RG | default_open_functions | exec: `Duplicate function definition: f/1` | `Error: No matching function: f/0. Available: f/1, f/2, f/1+` (executed `open` twin yields this exact text) | L |
| `disp-duplicate-pattern-header` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | duplicate error (renderer text as C-KEY; executed twin) | L |
| `disp-case-miss-identity` | G | - | exec: `No matching case for function f/1 with arguments [1]` | unchanged | D |
| `disp-case-miss-pattern-group` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `Error: No matching case for function f/1 with arguments [5]` | D |
| `disp-no-clause-ambiguity-single-unit` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | overlapping pattern/guard clauses: first match, never `open-function-clause-ambiguity` | A |

#### C-HDR

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `hdr-block-prefix-once` | G | - | exec: `prefix` / `2` | unchanged | D |
| `hdr-block-prefix-miss` | G | - | exec: stdout `prefix`; `No matching case for function f/1 with arguments [2]` | unchanged | D |
| `hdr-block-prefix-multi-call` | G | - | exec: `prefix` / `prefix` / `[1, 2]` | unchanged | D |
| `hdr-grouped-body-captures-header` | G | - | exec: `[0, 10]` | unchanged | D |
| `hdr-guard-evaluated-once` | RG | default_open_functions, refs | `model-b-not-implemented: declaration evaluation is not available` | counter `1` after one call | A |
| `hdr-guard-order` | RG | default_open_functions, refs | `model-b-not-implemented: declaration evaluation is not available` | `[2, ["a", "b"]]` for three effect-logging guards | D |
| `hdr-guard-error` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | guard error propagates; later guards not run; no partial binding | A |
| `hdr-matcher-outcome` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | named matcher returning `none`/`err` follows existing pattern-outcome behavior | A |
| `hdr-recursion-tco` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | constant-stack twin of `r20-open-ordinary-mutual-tail-call` | A |

#### C-OPTIM

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `optim-collection-recursion` | G | - | exec: `6` | `6` | D |
| `optim-late-declaration` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | optimized declaration then later different-shape clause: both visible | A |

#### C-OPT

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `opt-none-pattern-in-group-dispatches` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | twin of `r20-option-none-pattern-in-stratum-dispatches` | A |
| `opt-other-arity-clause-not-aware` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | twin of `r20-option-other-arity-clause-not-aware` | A |
| `opt-delegation-to-aware-callee` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | twin of `r20-option-delegation-to-aware-callee` | A |
| `opt-err-pipeline-value-short-circuits` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | twin of `r20-option-err-pipeline-value-short-circuits` | A |
| `opt-plain-identity-none` | G | - | exec: `none("r")` | `none("r")` | D |
| `opt-pipe-lift` | G | - | not yet executed | existing `|>` lift behavior unchanged | A |

#### C-OWN

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `own-alias-call-live` | G | - | exec: `3` | `3` | D |
| `own-immutable-alias-live` | G | immutable_bindings | exec: `3` | `3` | D |
| `own-local-alias-rejected` | RG | default_open_functions | exec: installs, prints `<function a/2>` (P10) | `Error: function-declaration-not-owner: cannot declare a/2: 'a' refers to function 'f' declared by another binding in this scope` | L |
| `own-local-alias-state-after-rejection` | RG | default_open_functions | exec: group grows | `f(1)`→`1`, `a(1)`→`1`, `f(1, 2)`→`No matching function: f/2. Available: f/1` | D |
| `own-local-alias-owner-still-extendable` | RG | default_open_functions | n/a | after rejection `f(x, y) = x + y; a(1, 2)` → `3` | D |
| `own-local-alias-pattern-clause` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `… cannot declare a/2: …` same category | L |
| `own-local-alias-varargs` | RG | default_open_functions | exec: `Duplicate function definition: a/1` (appends to `f`) | `… cannot declare a/1+: …`; **ownership check must precede the duplicate check** | L |
| `own-alias-annotation-not-evaluated` | RG | default_open_functions, refs | exec: annotation would run | rejection first; effect log empty | A |
| `own-imported-alias-rejected` | RG | default_open_functions, multi_file_eval | P11 (Slice-C plan): installs, `3` | `function-declaration-not-owner: cannot declare h/2: 'h' refers to function 'g' owned by module 'lib'` | L |
| `own-imported-alias-owner-unchanged` | RG | default_open_functions, multi_file_eval | P11 | `lib.g(1, 2)` → `No matching function: g/2. Available: g/1`; `lib.g(1)` → `1` | D |
| `own-lambda-nonfunction-unchanged` | G | - | exec: `Cannot define function g/2: name already bound to non-function value` | unchanged | D |
| `own-builtin-nonfunction-unchanged` | G | - | exec: `Cannot define function p/2: name already bound to non-function value` | unchanged | D |
| `own-explicit-open-unchanged` | G | open_functions | exec (probe `open f(0)=1; g(x)=x; f(n)=n`): `open-function-redeclaration: 'f' is already declared open in module '<entry>'` | unchanged; the plan's quoted text (`Cannot define function … open function interface or linked view`) is **not** what this probe produces — program selection needs characterization | A |
| `own-import-inert` | G | multi_file_eval | not yet executed | import never changes dispatch elsewhere | A |
| `own-extend-ordinary-rejected` | G | multi_file_eval, open_functions | not yet executed | `open-function-target-not-open` unchanged | A |
| `own-use-ordinary-base-unchanged` | G | multi_file_eval, open_functions | not yet executed | current behavior characterized, unchanged | A |
| `own-two-modules-independent` | RG | default_open_functions, multi_file_eval | `model-b-not-implemented: declaration evaluation is not available` | independent groups | A |
| `own-entry-prelude-name` | G | - | exec: `["mine", [2, 3]]` (P12) | unchanged characterization | D |

#### C-D8

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `d8-forward-collision` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `["zero", "other"]` | D |
| `d8-reverse-collision` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `["clause", 5]` | D |
| `d8-terminal-grouped-miss` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `No matching case for function f/1 with arguments [9]` | D |
| `d8-earlier-pattern-miss-continues` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `No matching case for function f/1 with arguments [5]` | D |
| `d8-legacy-identical-header-dup` | G | - | exec: `Duplicate function definition: describe/1` | unchanged | D |
| `d8-grouped-decl-one-key` | G | - | exec: `["z", 6, 3]` | unchanged | D |
| `d8-prefix-and-capture` | G | - | not yet executed (composition of executed `hdr-*` cases) | prefix once per call, header capture preserved | A |
| `d8-r20-flattening-unchanged` | G | open_functions | exec: `open-function-duplicate-clause …` | unchanged (Option A not applied to `open`) | D |

#### C-IMM

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `imm-rebind-as-function` | G | immutable_bindings | exec: `Cannot rebind immutable binding: x` | unchanged | D |
| `imm-rebind-as-pattern-function` | RG | immutable_bindings, default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `Error: Cannot rebind immutable binding: x`; nothing installed | D |
| `imm-declare-after-function` | G | immutable_bindings | exec: `Cannot declare immutable binding f: name is already bound in this scope` | unchanged | D |

#### C-META

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `meta-binding-doc-merge` | G | - | partially executed (`meta-doc-merge` probe printed `d1`); remainder not yet executed | contract §5.1 observation (see plan) | A |
| `meta-newer-key-overwrites` | G | - | partially executed (`meta-doc-merge` probe printed `d1`); remainder not yet executed | contract §5.1 observation (see plan) | A |
| `meta-alias-no-copy` | G | - | partially executed (`meta-doc-merge` probe printed `d1`); remainder not yet executed | contract §5.1 observation (see plan) | A |
| `meta-inline-doc-shared-via-alias` | G | - | partially executed (`meta-doc-merge` probe printed `d1`); remainder not yet executed | contract §5.1 observation (see plan) | A |
| `meta-conflicting-inline-doc-before-install` | G | - | partially executed (`meta-doc-merge` probe printed `d1`); remainder not yet executed | contract §5.1 observation (see plan) | A |
| `meta-three-channel-trio` | G | - | partially executed (`meta-doc-merge` probe printed `d1`); remainder not yet executed | contract §5.1 observation (see plan) | A |
| `meta-pattern-clause-annotations` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | pattern clauses accept annotations legal on legacy clauses | A |

#### C-ANN

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `ann-later-annotation-suppressed` | G | refs | `@doc 7` → exec: `@doc annotation expected a string, received int`; rest not yet executed | contract §5.2 observation | A |
| `ann-old-metadata-retained` | G | - | `@doc 7` → exec: `@doc annotation expected a string, received int`; rest not yet executed | contract §5.2 observation | A |
| `ann-installed-clause-visible-via-alias` | G | - | `@doc 7` → exec: `@doc annotation expected a string, received int`; rest not yet executed | contract §5.2 observation | A |
| `ann-prior-effects-persist` | G | refs | `@doc 7` → exec: `@doc annotation expected a string, received int`; rest not yet executed | contract §5.2 observation | A |
| `ann-pattern-clause-variants` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | same observations for pattern clauses | A |
| `ann-repl-recovery` | RG | default_open_functions, repl | `model-b-not-implemented: declaration evaluation is not available` | failure leaves session usable; group unchanged except installed clause | A |

#### C-MODE

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `mode-file-command-import-equivalence` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | file / `-c` / import / piped equivalents give identical program results | A |
| `mode-repl-failed-declaration-leaves-group` | RG | default_open_functions, repl | `model-b-not-implemented: declaration evaluation is not available` | duplicate/immutable/ownership failure leaves group unchanged and the name usable | A |

#### C-STAGE

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `stage-closed-rejected` | G | - | exec: stdout `before`, `model-b-not-implemented: declaration evaluation is not available` | unchanged; `child` never printed | D |

#### C-MAIN

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `main-legacy-main1-preferred` | G | - | exec: `top` / `main1` / `11` | unchanged | D |
| `main-legacy-main0-fallback` | G | - | exec: `top` / `main0` / `10` | unchanged | D |
| `main-legacy-rest-main-selected` | G | - | exec: `top` / `mainrest` / `12` | unchanged | D |
| `main-no-qualifying` | G | - | exec: `top` / `42` | unchanged | D |
| `main-command-mode` | G | - | exec: `top` / `cmdmain` / `["x", "y"]` | unchanged | D |
| `main-repl-never-selects` | G | repl | not yet executed | transcript framing characterized from existing `model-b-b-repl-*` cases | L |
| `main-pattern-not-selected` | RG | default_open_functions | exec: `model-b-not-implemented: declaration evaluation is not available` | `top` / `42`; no `pattern-main` | D |
| `main-pattern-guard-not-evaluated` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `top` / `42`; no `guard-ran`, no `body` | D |
| `main-wildcard-not-selected` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `top` / `42`; no `wild` | D |
| `main-multi-pattern-group-not-selected` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `top` / `42`; no `A`, no `B` | D |
| `main-pattern-command-mode` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | source result only; no body output | D |
| `main-explicit-call-dispatches` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `pattern-main` (exactly once) / `1` / `42` | D |
| `main-explicit-call-miss` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `No matching case for function main/1 with arguments …`; argument rendering to be byte-characterized | L |
| `main-test-mode-unchanged` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `@test` runs; pattern-bearing `main` produces no output | A |


**Reserved, not created (G1-dependent):** `model-b-c-main-g1-mixed-*` (five IDs, §7) — absent from the RED set until the maintainer approves G1.

**Existing specs cited, not duplicated or edited:** `error-r20-local-duplicate-clause`, `error-r20-varargs-ambiguity`, all `r20-*`, `f2-*`, `model-b-a-*`, `model-b-b-*`, `file_mode_main_argv`, `pipe_mode_bypass_main`, and the Slice A `parse-error-mixed-function-declaration-operators` pin (the plan's `stage-mixed-operators` case is therefore **not** added; exec shows `Error: mixed-function-declaration-operators`).

### 3.4 Host-local inventory (`tests/unit/test_model_b_slice_c_*.py`; not counted in the 127)

| ID | Test subject | Oracle source | Status |
| --- | --- | --- | --- |
| HL-1 | group record API: ordered records, legacy-only arity index consistency, owner/provenance | design §3; pre-flight §5.4 | D |
| HL-2 | pure key walker against the §2.2 table; no `repr`/host-equality fallback; malformed structure rejected | pre-flight §2.2 | D |
| HL-3 | writer atomicity/reentrancy: barriers, bounded joins, both orderings; user code never under `_BINDING_LOCK` | pre-flight §7 | D |
| HL-4 | consumer predicate table (route / HTTP / `@test` / lifecycle / `help`·`doc`·`meta`) + grep-level "no `get(n)` on multi-record group without cardinality check" | pre-flight §2.5 | D |
| HL-5 | autoload/prelude twin of `test_autoload_resolution_matches_non_autoload` with pattern clauses; P12 | pre-flight §5.4 | A |
| HL-6 | exception-class identity: `TypeError` legacy duplicate / `OpenFunctionDuplicateClauseError` / shape-miss `TypeError` / case-miss `RuntimeError` / ambiguity `TypeError` / `FunctionDeclarationNotOwnerError` | pre-flight §2.4 | D |
| HL-7 | source ↔ direct-IR equivalence for every source-expressible RG/R case | design | A |
| HL-8 | optimizer on/off equivalence; D8 arm retention (`optim-keys-retained`, `d8-arms-retained-not-checked`) | pre-flight §2.6 invariant 4 | D |
| HL-9 | C-MAIN structural: `_resolve_program_result` reached only from the `command`/`file` branches; no pattern/guard evaluation in it; no new `main` error category (read: `interpreter.py:513-528`, `:671`, `:687`) | pre-flight §2.5.1 | D |
| HL-10 | `Env.define_function` owner checks via module-identity/name provenance, not `callable(value)`; ordinary groups not accepted by `IrOpenContribution`/`IrOpenUse` target checks | pre-flight §2.3 | D |
| HL-11 | **R4 diagnostic safety:** ownership / foreign-alias messages contain no filesystem path, `0x…` address, source span or captured/protected value; module rendered by canonical identity or `<entry>`; protected R10 sentinel absent from case-miss / duplicate / ownership diagnostics | §5.3 | D |
| HL-12 | **R4 file-mode label characterization:** a duplicate involving a pattern clause, run through the CLI on a `tmp_path` file, renders the existing entry label (the host-resolved path, §5.2) — asserted as `str(Path(file).resolve())`, not a literal | §5.2 | D |
| HL-13 | capability evidence: exact RED capability map (a *new* constant, §6.2); every `SLICE_C_GATED_IDS` spec through `execute_spec_via_host` with a witness host that records invocations → all `unsupported`, zero invocations; non-vacuous counts | R3 | D |
| HL-14 | `immutable`-interaction: `_meta_define` cannot append to an immutable-owned name | pre-flight §6 | A |

### 3.5 Cases whose expected result cannot yet be derived unambiguously (flagged, no oracle invented)

1. **`key-repeated-binders-distinct` (B).** Whether `f(x, x)` is a legal non-linear header and how it compares with `f(a, b)` is not specified in the pre-flight, contract or design. Needs a maintainer/contract answer (or a documented existing-pattern-semantics characterization) before the case is created.
2. **`own-explicit-open-unchanged` (A).** The plan quotes `Cannot define function … open function interface or linked view`; the probe `open f(0)=1; g(x)=x; f(n)=n` yields `open-function-redeclaration: 'f' is already declared open in module '<entry>'` instead (exec). The program that triggers the quoted diagnostic must be identified from the existing R20 specs.
3. **All **L** cases** — exact strings locked at the RED baseline.
4. **Source defects in the accepted plan** (corrected here, §8.4): the lambda-factory program and the migration/new-group programs.
5. **`pat-string-body-is-body`, `pat-named-matcher`, `key-named-matcher`, `hdr-matcher-outcome`** — the `doc(...)` observation for an undocumented pattern group and the named-pattern body forms are not characterized; **A** until the RED author characterizes them on legacy twins.

Stop rule (unchanged): if writing any A/L case needs a semantic choice, stop and return to #1249; never replace the stated outcome silently.

---

## 4. R3 — GREEN anti-false-positive gate **[extended by §R6.4]**

Required for GREEN acceptance; every item is an automated assertion or a recorded command unless marked *checklist*.

| ID | Assertion | Type |
| --- | --- | --- |
| GA-1 | `default_open_functions` is in `spec/manifest.json["optional_capabilities"]` and **not** in `required_capabilities`; it was added only in the RED commit (before it, the C0 absence test holds; after, this) | static test |
| GA-2 | `hosts.python.protocol_adapter._VOCABULARY_ONLY_CAPABILITIES` does not contain `default_open_functions`; at GREEN it is `frozenset()` (or deleted with the mechanism covered, per the plan) | static test |
| GA-3 | `_python_claimed_capabilities()` **equals the literal** `GREEN_CAPABILITY_MAP` = the 35-entry C0 map plus `"default_open_functions": "supported"` (36 entries). Written as an explicit literal, never generated from code | test |
| GA-4 | For every ID in `SLICE_C_GATED_IDS`, `execute_spec_via_host(spec, <real adapter command>, host_capabilities=_python_claimed_capabilities())` returns `kind == "pass"` — **not** `unsupported`. The P5 case also returns `pass`. An aggregate asserts the set of kinds is exactly `{"pass"}` over all 127 | test (non-slow if run in the harness's sibling; may reuse the external run) |
| GA-5 | `tests/spec/test_python_protocol_adapter_parity_762.py` passes **unmodified** (`unsupported == 18`, `passed == total − 18`, zero failure classes, exit 0), because the applicability contract is unchanged | existing test |
| GA-6 | `python -m tools.spec_runner` exits 0 with `failed=0 invalid=0` and `total == 1028` | recorded command (W1–W6) |
| GA-7 | The harness is converted to a thin wrapper over the same ID set; no skip/xfail introduced | test |
| GA-8 | Static guard: `tests/spec/test_model_b_slice_c_red.py` (and its GREEN successor) contains no `skip`, `skipif`, `xfail`, `slow`, or conditional import-skip; present from the RED commit | static test |
| GA-9 | The `default_open_functions` entry in `spec/known_host_gaps.json` lists `affected_tests` equal to the gated ID set derived from the YAML `requires` (not typed twice by hand); present from RED, still true at GREEN | test |
| GA-10 | The Python evidence JSON from the external run shows `capabilities["default_open_functions"] == "supported"` **and** `counts.unsupported == 18` (supported is meaningful only with PASS evidence, never with a count of unsupported cases) | recorded command |
| GA-11 | `host_parity_gate` reports `default_open_functions` as `KNOWN_GAP` (C++ still undeclared) — not `UNDOCUMENTED_GAP` and not `STALE_GAP` | recorded command (CI) |
| GA-12 | The **C0 phase guards are updated deliberately** (§6.3), never regenerated or weakened; the original `PRE_C0_CAPABILITY_MAP` literal is kept as history | review checklist |

**An external runner that exits 0 because gated cases were classified `unsupported` is not GREEN.** GREEN is the conjunction GA-2 ∧ GA-3 ∧ GA-4 ∧ GA-5 ∧ GA-6.

### 4.1 Capability vocabulary / override sequence

| State | `spec/manifest.json` | `_VOCABULARY_ONLY_CAPABILITIES` | Python-advertised map | External-host gated cases | In-process gated cases | Known gap (C++) |
| --- | --- | --- | --- | --- | --- | --- |
| **Now** (`main@79c073b`) | name absent | `frozenset()` | 35 names (34 supported, `shared_spec_runner` partial) | n/a | n/a | none |
| **RED commit** | name appended to `optional_capabilities` | `frozenset({"default_open_functions"})` | 36 names, new one `unsupported` | `unsupported` before invocation | executed → fail | entry added: `m0smith/genia-2026#1269`, `affected_host: cpp`, `affected_tests` = 75 gated IDs |
| **GREEN commit** | unchanged | name **removed** (set empty again, or mechanism deleted) | 36 names, new one `supported` | `pass` | pass | entry unchanged |

The manifest edit and the override edit must be in the **same commit**: manifest-first would make the Python adapter advertise `supported` (the default branch) — a false claim; override-first would raise `ValueError` (unknown name); gated YAML without the name makes the loader reject `requires` (`invalid`). (Reasoning: read — `_python_claimed_capabilities`, `capabilities.validate_case_requirements`.)

---

## 5. R4 — diagnostic-path compatibility (directed disposition applied) **[§5.5 amendment text now drafted in §R6.6]**

**Disposition (directed):** preserve the existing R20 duplicate-diagnostic renderer for pattern-clause duplicates, **including its established file-mode source-location format**. Apply stricter path redaction only to newly defined ownership / foreign-alias errors and specifically designated sanitized surfaces. No blanket ban on file paths across all new diagnostics.

### 5.1 Separation of diagnostic classes

| Class | Renderer / category | Path policy | Source |
| --- | --- | --- | --- |
| Existing R20 duplicate-clause rendering (`open …`) | `OpenFunctionDuplicateClauseError`, `callable.py::_format_open_span` | entry clauses render `<label>:<line>`; imported-module clauses render `<module-identity>:<line>` | exec, read |
| **New** pattern-duplicate messages (ordinary groups) | **reuse** the same class and renderer unchanged | identical to the existing renderer (command mode `<command>:N`; file mode the entry label as given) | pre-flight §2.4 D3 |
| Ownership / foreign-alias (`function-declaration-not-owner`) | new `FunctionDeclarationNotOwnerError` | **no** path, address, span or captured/protected value; canonical module identity or `<entry>` only | D5; design §3 |
| Case-miss / shape-miss | existing `RuntimeError` case-miss; `TypeError` shape-miss (`OpenFunctionNoMatchingFunctionError` rendering for new groups) | no spans at all; arguments via `format_debug` (protected values masked) | exec |
| Host-generated / protected-value diagnostics | unchanged; R10 sentinels never appear | existing protections | pre-flight §10 |

### 5.2 Grounded examples (exec, `main@79c073b`, `open` twin of the pattern-duplicate because the ordinary form does not execute yet)

| Mode | Program | Observed stderr |
| --- | --- | --- |
| command mode (`genia -c`) and shared `eval`/`error` category | `open f([a,b])=1` / `f([c,d])=2` | `Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)` |
| file mode, invoked as `genia dup.genia` (relative) | same text in `dup.genia` | `… (first at /<absolute>/dup.genia:1, duplicate at /<absolute>/dup.genia:2)` — **the host-resolved absolute path, even for a relative or subdirectory argument** (`sub/dup.genia` also resolves to `/<absolute>/sub/dup.genia`) |
| file mode, invoked with an absolute path | same | identical absolute path |
| legacy-only duplicate, either mode | `f(x)=1` / `f(y)=2` | `Error: Duplicate function definition: f/1` (no span) |
| shape miss | `f(x)=1` / `f(1,2)` | `Error: No matching function: f/2. Available: f/1` |
| case miss | `f(x) = (0 -> x)` / `f(1)` | `Error: No matching case for function f/1 with arguments [1]` |
| new-group shape miss (`open` twin) | `open f(x)=1; f(x,y)=2; f(x,..r)=3; f()` | `Error: No matching function: f/0. Available: f/1, f/2, f/1+` |

### 5.3 Oracle placement that follows

1. **Shared YAML (`eval`/`error`) duplicate oracles use the `<command>` label.** The comparator compares stderr **exactly** (`comparator.py`), and a file-mode path is machine-dependent, so a shared file-mode duplicate oracle with an exact string is not expressible and is **not created**. (Existing precedent: `error-r20-local-duplicate-clause`.)
2. **File-mode behavior is pinned host-locally (HL-12)** by asserting the label equals `str(Path(file).resolve())` — preserving, not redacting, the existing renderer.
3. **Ownership / foreign-alias diagnostics** keep the stricter rule (HL-11): canonical module identity or `<entry>` only; shared cases `own-local-alias-*` / `own-imported-alias-*` use exact strings with no span.
4. The plan's blanket C-ERR sentence ("no filesystem path … in any new diagnostic") is **narrowed** accordingly in the revised RED plan.

### 5.4 Ownership-versus-duplicate ordering (found while grounding)

`f(x) = x; a = f; a(x, ..r) = x` currently fails with `Duplicate function definition: a/1` (the declaration appends to `f`'s group, exec). After D5 the ownership check must run **before** any duplicate check, otherwise the case would surface the legacy duplicate message instead of `function-declaration-not-owner` (`own-local-alias-varargs`, L).

### 5.5 Amendment required before RED (not made here)

The design (#1259) §3 says diagnostics "render canonical imported module names or the existing entry label, never filesystem paths", and §13.5 says "without leaking host-only absolute paths". The **existing entry label in file mode is the host-resolved absolute path** (exec above). The two statements conflict for file-mode pattern-duplicate diagnostics. The directed disposition resolves it by preserving the renderer; the design/contract text needs a **one-line maintainer-approved clarification** (e.g. "for diagnostics produced by the existing R20 duplicate renderer the entry label is the host's entry label, which in file mode is the resolved entry path; the 'never filesystem paths' rule applies to ownership/foreign-alias and other designated sanitized diagnostics") recorded as a decision on #1269 (no design-document edit is made in this phase). RED duplicate oracles for file mode must not be locked until that sentence is confirmed.

---

## 6. R5 — manifest, documentation and phase-guard synchronization **[§6.3 superseded by §R6.5]**

### 6.1 Manifest edit the RED phase must make (not made here)

`spec/manifest.json` has `required_capabilities` (8 names) and `optional_capabilities` (27 names; last entry `immutable_bindings`). Both are flat string arrays; no per-capability schema. The RED commit appends exactly one string, `"default_open_functions"`, to **`optional_capabilities`** (never `required_capabilities`: required capabilities are not relaxed and are ineligible for gap entries). `known_capabilities()` then returns 36 names. Because `host_parity_gate.optional_capabilities()` iterates the optional list, C++ (which does not declare it) needs the known-gap entry in the same commit or the parity gate reports `UNDOCUMENTED_GAP`.

### 6.2 What changes in RED, and what must not

| Artifact | RED | GREEN |
| --- | --- | --- |
| `spec/manifest.json` | + `default_open_functions` (optional) | unchanged |
| `hosts/python/protocol_adapter.py` | override becomes `frozenset({"default_open_functions"})` | override emptied/removed |
| `spec/known_host_gaps.json` | + C++ entry (`tracking_issue: m0smith/genia-2026#1269`, `affected_host: cpp`, exact gated IDs, reason, removal condition) | unchanged |
| `spec/{eval,error,cli}/model-b-c-*.yaml` + sibling `.genia` | + 127 cases | unchanged |
| `tests/spec/test_model_b_slice_c_red.py`, `tests/unit/test_model_b_slice_c_*.py` | added (failing) | thin wrapper; host-local tests green |
| C0 phase-guard tests | updated deliberately (§6.3) | updated deliberately |
| Existing parity/capability/R20/F2/Slice A·B tests, existing specs | **unchanged** | unchanged except §6.4 |
| `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, `docs/book`, cheatsheets, `docs/ai/LLM_CONTRACT.md`, semantic facts, MCP profile, host-capability docs, roadmap | **unchanged** (nothing is implemented) | updated to verified behavior only |

### 6.3 C0 phase guards that change intentionally (`tests/unit/test_python_protocol_adapter_c0_capability_staging_1269.py`)

- RED: `test_override_is_empty_and_immutable_in_production` → asserts `frozenset({"default_open_functions"})`; `test_empty_override_capability_map_equals_pre_c0_baseline_exactly` → keep `PRE_C0_CAPABILITY_MAP` as a historical literal and add `RED_CAPABILITY_MAP = PRE_C0_CAPABILITY_MAP + {"default_open_functions": "unsupported"}`, asserting equality with it; `test_default_open_functions_is_not_in_the_vocabulary_or_the_override` → inverted (name **is** in the vocabulary and in the override); `test_staged_known_capability_is_reported_unsupported_and_others_unchanged` → its expected dict is rebuilt from the RED map (rehearsal: it fails otherwise because the advertised map gains a 36th name). These are the **four** C0 tests the rehearsal showed failing; the remaining seven (unknown-name rejection, `shared_spec_runner` precedence, external-host no-invocation, ungated unaffected, R20 gating unchanged, full-vocabulary and status checks) passed unchanged.
- GREEN: override empty again; `GREEN_CAPABILITY_MAP = PRE_C0_CAPABILITY_MAP + {"default_open_functions": "supported"}` (GA-3).
- Every other test in that file (unknown-name rejection, external-host no-invocation, ungated unaffected, R20 gating unchanged) is retained as written.

### 6.4 Documentation and phase-guard tests

- **`tests/doc` must be rerun after the manifest edit** (R5, and every subsequent edit). **Rehearsal:** `397 passed, 35 skipped` after adding the name to the manifest (together with the override and a gap entry) in the scratch worktree — no documentation test depends on the new name. Re-run on the real RED commit and record the count.
- Tests that look at the manifest/capability lists: `tests/doc/test_portability_contract_sync.py::test_manifest_capabilities_cover_capability_matrix` checks matrix rows → manifest (one direction), so **adding a manifest name without a matrix row passes at RED**; at GREEN, adding the `default_open_functions` row to `docs/host-interop/HOST_CAPABILITY_MATRIX.md` requires adding its display name to that test's `display_to_key` mapping — an intentional, additive edit. `docs/host-interop/capabilities.md` is a separate runtime-capability registry and is not manifest-driven.
- **Phase guards that must change at GREEN, not RED** (they assert pattern headers are not executable today; they pass until GREEN):
  - `tests/unit/test_model_b_slice_a.py::test_transitional_rejection` — parameters `f([x]) = x` and `f(x) ? true = x` (the `f(x) =: x` parameter stays: closed groups remain unimplemented);
  - `tests/unit/test_model_b_slice_b.py::test_closed_and_pattern_declarations_remain_not_implemented` — the `f([x]) = x` half;
  - `tests/unit/test_r28_mcp_language_profile.py` (≈ line 208) and `tests/unit/test_r28_mcp_language_registry.py` (≈ line 184) — the un-`open`ed `gcd` pattern-clause rejection probes;
  - `tests/unit/test_model_b_slice_b.py` ≈ lines 306/313 — **inspect at GREEN** (closed/annotated discovery rejection; may stay);
  - `GENIA_STATE.md` ≈ lines 744 and 3626, `docs/contract/semantic_facts.json` ≈ lines 255 and 448, `tests/data/mcp_language_profile.golden.json`, `docs/host-interop/HOST_CAPABILITY_MATRIX.md` ≈ line 93, `docs/architecture/core-ir-portability.md` ≈ line 219, `docs/book/03-functions.md`, `docs/cheatsheet/core.md`, `docs/cheatsheet/unix-power-mode.md`, `docs/ai/LLM_CONTRACT.md` (the "literal first parameter needs `open`" sentence) — all synchronized with *verified* behavior only, with `tools/gen_mcp_language_profile.py --check`, `tests/doc/test_semantic_doc_sync.py`, `tests/doc/test_state_anchors_and_registry_sync.py`, cheatsheet/SICP/doc-style sidecar tests as AGENTS requires.
  - Retained unchanged: closed `f(...) =: body` still rejects with `model-b-not-implemented` (`stage-closed-rejected`, `test_native_discovery_explicitly_rejects_closed_test`, `test_transitional_rejection_precedes_body_effects`).
- **How GREEN removes the staged claim:** the same commit that makes the 75 gated cases pass removes the name from the override; GA-2…GA-5 then prove `supported` is true.

---

## 7. G1 — recorded, **pending maintainer approval before GREEN** (not implemented, not approved) **[reserved ids corrected in §R6.8]**

**Proposed conservative invariant** (integration comment 6327837022 §4, Codex 6327597044 §3):

> The existing CLI entry selector may invoke `main` automatically only when the entire function group contains legacy identifier-header records and no two records share the same required-arity key. Otherwise it silently preserves source-result fallback without executing a selected record, matcher, guard or body.

Where the group is eligible, the legacy `main/1`-then-`main/0` convention is unchanged (M1–M5, exec). Explicit calls to `main` continue through ordinary function dispatch. No new diagnostic.

**Why it matters (read):** `_resolve_program_result` looks up `main_group.get(1)` then `get(0)` and invokes the record directly (it does not go through dispatch). Mixed groups first become user-constructible at GREEN (at base they fail to construct: pattern headers give `model-b-not-implemented`; fixed+rest same minimum gives `Duplicate function definition`). Without G1 the selector would pick a representative record — forbidden by rule 5.

**Concrete GREEN tests once approved** (shared cases, `requires: default_open_functions`; CLI-shaped with sibling `.genia`; each asserts top-level output + source result and **no** `main` output). Programs `print("top")` … `42`, argv chosen so that a pattern record would match if (wrongly) selected:

| ID (reserved) | Group | Expected under G1 |
| --- | --- | --- |
| `model-b-c-main-g1-mixed-main0-plus-pattern` (SC-MAIN-1) | legacy `main()` + pattern record of another arity | `top` / `42`; nothing selected |
| `model-b-c-main-g1-mixed-main1-plus-pattern` (SC-MAIN-2) | legacy `main/1` + pattern record of another arity | `top` / `42` |
| `model-b-c-main-g1-main1-plus-pattern-arity1` (SC-MAIN-3, both declaration orders: two IDs) | legacy `main/1` and a pattern arity-1 record | `top` / `42`; the legacy body does **not** run even though it would match |
| `model-b-c-main-g1-fixed-plus-rest-same-minimum` (SC-MAIN-4) | `main(a)` + `main(a, ..r)` | `top` / `42`; no representative pick |
| `model-b-c-main-g1-legacy-rest-plus-pattern-arity1` (SC-MAIN-5) | legacy `main(a, ..r)` + pattern arity-1 record | `top` / `42` |
| host-local `HL-9b` | selector never reads a lossy/derived index to choose among records; a pure legacy group with unique required-arity keys still selects `main/1` then `main/0` | structural |

Two reading divergences G1 closes: (G) whole-group vs (S) legacy-only-index selection, and the declaration-order dependence in SC-MAIN-3/5. G1 as recorded takes reading (G). **Until the maintainer confirms G1 (and, if (S) is preferred instead, states the per-arity and ordering rules), no GREEN may be accepted and no G1 case is created.** #1271 / #1272 (host-selected application lifecycle) own any eventual new `main` behavior and are not part of Slice C.

---

## 8. Unresolved items and corrections **[§8.1 superseded by the §R6.0 register]**

### 8.1 Open decisions for the integration owner (do not block this package; block RED authorization where marked)

- **O-1 — gating consistency of the D5 breaking changes (blocks locking `requires` for the `own-*-rejected` cases).** P5 is ungated because it changes ungated ordinary behavior. P10/P11 (alias / imported-binding declaration → `function-declaration-not-owner`) are the same kind of valid→error change on ungated programs (exec: `a(x, y) = x + y` through an alias still succeeds today), yet the pre-flight plan gates them. Choose one rule: *breaking changes to ungated behavior are ungated* (then `own-local-alias-rejected` family are `R`, affecting the O-2 C++ question and the counts: ungated R +N, gated −N) or *gated by `default_open_functions`* (then the P5 rationale needs restating). The counts in §2.3 assume the plan as written (gated).
- **O-2 — ungated new cases and the C++ evidence path (blocks RED).** Every ungated new case (51 G + P5 = 52) is *applicable* to the C++ host, and known-gap entries are capability-scoped. If the pinned C++ adapter fails any of them (P5 is a prime candidate; some G diagnostics are Python text), `host-parity.yml` gets a non-zero failure-class count with no gap mechanism to document it, and RED cannot be merged without a policy decision. This session cannot build `genia-cpp`. **Pre-RED action requested of the integration owner:** run the pinned C++ adapter against the 52 ungated candidates (or authorize `add_repo` of `m0smith/genia-cpp` read access for a build), then decide for each failing ungated case: re-gate by a pre-existing capability it genuinely needs, treat as a separately tracked pre-existing C++ discrepancy (as the plan already does for the R20 duplicate-clause discrepancy), or drop from the shared set (host-local only). The list of the 52 is §3.3 (all rows with `requires` not containing `default_open_functions`).
- **O-3 — R4 design-text clarification (blocks locking file-mode duplicate oracles; §5.5).**
- **O-4 — B case `key-repeated-binders-distinct` (does not block the rest; §3.5).**
- **O-5 — `own-explicit-open-unchanged` program selection (§3.5).**
- **O-6 — U4 literal strings (13 L cases)** are byte-locked at the RED baseline, as already directed.

### 8.2 Contract conflicts found

- Design §3 / §13.5 "never filesystem paths" vs the existing file-mode entry label (R4, §5.5).
- Plan C-ERR sentence "no filesystem path in any new diagnostic" — narrowed (§5.3).

### 8.3 What was *not* verified here

The C++ side (no `genia-cpp` checkout/build): `host-parity.yml` C++ evidence and `docker-dev-environment.yml` C++ conformance were not run. The 128-case inventory has not been run as YAML; its Baseline column for **exec** rows was run through the in-process adapter on the stated program text, and the RED/GREEN columns are inferred. No full-suite pytest run was made (only the suites listed in §2.1); the loopback partition was not run.

### 8.4 Stale or incorrect facts corrected in the plan (verified)

1. RED plan header said "(revision 3)" while the body was revision 4; now revision 5.
2. "Slice B recorded 874 passed" → measured **901**.
3. C0 "design-approved, NOT implementation-authorized" → implemented, independently reviewed and merged (#1273).
4. `model-b-c-open-lambda-factory-distinct` source `mk(k) = (x) -> x + k` is a **grouped-body arm** (exec: `mk(1)` evaluates the arm and returns `2`), not a lambda factory; corrected source is `mk(k) { g = (x) -> x + k; g }` with oracle `[2, 3, true, false]` (exec).
5. `model-b-c-disp-p5-migration-fixed-clause` baseline is `Duplicate function definition: f/2` (not "valid today"); `model-b-c-disp-no-matching-function-new-group` baseline is `Duplicate function definition: f/1` (fixed+rest same minimum, P4), not `model-b-not-implemented`.
6. The pre-flight said C0 "NOT authorized"; the later authorization (6327837022) governs.

---

## 9. Gate checklist

- [x] Sources: `AGENTS.md`, `docs/process/run-change.md`, both Slice C process documents, issue #1269 and the cited PR comments were read in full. `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, `docs/ai/LLM_CONTRACT.md`, the strategy documents and contract #1255 / design #1259 were consulted **by targeted search for the specific claims cited here**, not re-read line by line (stated, not hidden; the pre-flight revision 4 and its two independent reviews already carry the line-by-line reads).
- [x] `main` refreshed; C0 mechanism verified on merged `main`.
- [x] R1 matrix with exec baselines; RED/GREEN counts derived from the exact ID set; unsupported never counted as success.
- [x] R2 harness specification and 127 exact IDs with oracle status; blocked/ambiguous cases flagged.
- [x] R3 assertions GA-1…GA-12 and the vocabulary/override sequence.
- [x] R4 disposition applied; command- and file-mode examples (exec); design-text clarification identified.
- [x] R5 manifest edit specified, `tests/doc` rerun results recorded, intentional phase-guard changes listed.
- [x] G1 recorded, **explicitly pending**.
- [ ] Independent review of this package (requested).
- [ ] Integration-owner decisions: O-1, O-2, O-3 (before RED); G1 (before GREEN).
- [ ] Separate RED authorization — **not given by this document**.

## 10. Evidence index

Pre-flight and RED plan (this branch); #1270 comments 6327597044 (Codex final-delta), 6327837022 (integration gate); #1273 comments 6332339182, 6333124626, 6333148622, 6340512475, 6340735417; `tools/spec_runner/{runner,host_executor,capabilities,comparator,host_parity_gate}.py`; `hosts/python/protocol_adapter.py`; `src/genia/interpreter.py:513-528`; `.github/workflows/{ci,regression,github-hosted-runner-canary,self-hosted-runner-smoke,host-parity,docker-dev-environment,code-documentation,docs,validate-llm-instructions}.yml`; `pytest.ini`; `spec/manifest.json`; `spec/known_host_gaps.json`; scratch characterization of the exec programs (not committed): 82 program texts run through `hosts.python.adapter.run_case`, 6 CLI programs, 4 file-mode/command-mode diagnostic probes.
