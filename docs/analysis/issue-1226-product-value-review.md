# Issue #1226 — Product-Value Review and Dogfooding Assessment

Status: **Non-authoritative review.** Date: 2026-10-20. Reviewed `main` at `979302c`.
Implemented behavior is defined by `GENIA_STATE.md`; roadmap material is planning only. This review changes no language, runtime, MCP, CI, or agent-instruction behavior and creates no tickets.

Goal under test: *Genia should be something a capable engineer or agent, free to choose any language, deliberately chooses because it makes a task easier, clearer, safer, or more maintainable.* The goal is not to maximize the share of tooling rewritten in Genia.

## 0. Method and limits

- Read: `AGENTS.md`, `docs/strategy/{killer-workflow,release-roadmap,human-ai-shared-programming}.md`, `docs/strategy/roadmap/r39.md`, `docs/process/08-roadmap-ticketing.md`, `docs/ai/LLM_CONTRACT.md`, relevant `GENIA_STATE.md` sections (validation helpers, JSONL/CSV, `collect_validated`), the MCP `genia_language_profile` output, issue #1226 (body and all 9 comments), and #1224.
- Executed: five small programs through the MCP `genia_run` tool (restricted Python-reference-host worker; source only, no files/stdin/network). They are quoted in the Appendix.
- **Not done, so not claimed:** no Python head-to-head was run; the CLI (file/stdin mode) was not exercised because shell access to the repo environment was restricted in this session; PRs cited in #1226 comments were not re-opened (their claims are used as reported, and flagged as such); PR #1262's current state was not checked; no subagents were used. The "challenge the pro-Genia case" and "is this really a discovery gap?" passes in §B and §D were done by the author of this review and are weaker than independent review. An independent reviewer should re-check the Appendix and §D before the owner decides.
- No effort, token, or productivity numbers appear because none were measured.

## A. Executive verdict

**The pilot is not ready for an ADOPT/REVISE/DO-NOT-ADOPT decision on the prospective trial, but it is ready for a REVISE decision on the practice as designed.**

- Independent prospective sample: **2 completed task families, 1 incomplete**, not 5. The nine comments reduce to: (1) F2/P2-C test-ownership helper (#1067); (2) the Model B family — #1250/PR #1260 (Slice A, three comments) and #1261/PR #1262 (Slice B, two comments), one effort; (3) genia-cpp #51, which its own comment says is incomplete and executed nothing. The five retrospective PRs are a separate baseline and are mostly CI/documentation tooling by one team.
- What it demonstrated: (a) agents recurrently fail to *find* existing Genia constructs (four separate notes, four different symptoms, §D); (b) a few narrow policy/invariant fragments are expressible and behave as the Python oracle does (retrospective: 31 scoped comparisons; Slice A tally); (c) most agent-written support code is host work where Python/Bash/Git/native tooling is correct (the large majority of inspected units were classified D or E; no exact count is claimed); (d) one attempted replacement was not equivalent (float rounding, `1.234` vs `1.235`).
- What it did not demonstrate: any measured reduction in total effort; any case where an agent *voluntarily preferred* Genia; any realistic task where Genia was clearly the better tool.
- What this review adds: a verified end-to-end slice of the killer workflow (Appendix) shows a credible advantage for *validating messy records with accumulated diagnostics*, with specific discoverability and diagnostic frictions. It is one workload, one author, no comparison run — evidence of feasibility, not of preference.

## B. Genia usefulness assessment

**Where Genia is credibly good today (Python reference host):**
- Messy line records → `parse_jsonl_record`/`parse_csv_row` → `validate_record`/`validate_each` → `collect_validated` yields `{clean, diagnostics}` with no exceptions, no hand-written error list, and three distinct outcomes (valid / skipped blank / error) as ordinary values. Multi-field failures accumulate per record with `field`, `expected`, `actual`. See the Appendix.
- Small pure invariants over shaped records (partition checks, status/ID legality, classification tables, histograms) are short pattern-matching/fold code (retrospective O1–O4; Slice A tally). They match Python results on tested inputs.

**Where usability is limited:**
- *Discovery.* The cheatsheet (`docs/cheatsheet/`) has no recursion or `open` multi-clause section (searched: no match for "recurs" or `open name(`); the language profile does cover it, so the information exists but not where a task-driven agent looks first.
- *Self-correction through MCP.* `genia_run` returns the same fixed message (`Genia source failed during evaluation`) for every runtime error. I got it for `is_number(1)`, `type_of(1)`, and an undefined name alike (Appendix). This is by design (`docs/mcp/reference.md:74`), but it means an agent cannot repair a typo through the tool; the CLI is the fallback (two prior observers did this).
- *Name collisions.* Binding `input = [...]` returned `policy_denied: source requests a capability unavailable in the MCP v1 profile`, because `input` is a host builtin. Accurate but unhelpful to someone who just chose a natural variable name.
- *Provenance in diagnostics.* A record-validation failure carries only field diagnostics plus `index`; the original line text from the parse stage is not in the aggregate (visible in §2 output). Mapping back to the source row needs a caller-added `row` field. Treated as E (one observation).
- *Host reach.* Files, processes, YAML, hashing, regex, parsers, Git, CI APIs: Python/Bash retain clear advantages (retrospective O7/O8; Model B Slice A/B notes). Exit status for gate-style programs: a returned `err(...)` exits 0 (R39 already owns this).
- *Portability.* Everything verified here ran on the Python host only. Compatibility JSON helpers (`json_parse`, `parse_jsonl_record`) are Python-host-only per `GENIA_STATE.md`; no C++ claim is made.

**Honest comparison:** For a one-off record check an engineer fluent in Python with `pydantic`/`jsonschema` is not slower, and Python has files, packaging, and ecosystem. Genia's candidate edge is *default-accumulating, exception-free, inspectable failure values* and a small uniform pipeline model. That edge is real only if (i) the first-time user can find the constructs and (ii) diagnostics can be tied to source rows. Neither is yet shown by measurement.

## C. Evidence matrix

| Claim | Evidence | Strength |
|---|---|---|
| Independent prospective sample is 2 (+1 incomplete) | #1226 comments 6174357364 (F2/P2-C), 6277213915 / 6278247481 / 6277767827 (#1261, PR #1262), 6277265426 / 6277294207 (#1250, PR #1260), 6277996708 (genia-cpp #51, "incomplete") | High (read directly) |
| Retrospective found narrow A fragments, no B, one non-equivalence | #1226 comment 6171967040 §"Verified alternatives"; appendix harness; author-run, partly auditor-reviewed | Medium (not re-run here) |
| Timing formatter replacement not equivalent | same comment: `format("{n:.3}", {n: 1.2345})` → `"1.235"` vs Python `1.234` | Medium (reported, not re-run) |
| End-to-end validated JSONL pipeline works on the Python host | Appendix, run 1 | High (run here, output captured), narrow |
| Report aggregation (tally/total/filter) works | Appendix, run 2 | High, narrow |
| MCP runtime errors are uniformly opaque | §2 runs 3–4; `docs/mcp/reference.md:74`; `apps/mcp/mcp.genia:836` | High |
| `input` name triggers policy denial | §2 run 5 | High (single probe) |
| Cheatsheet lacks recursion/`open` guidance | grep of `docs/cheatsheet/` here; Slice B comment 6277213915 | Medium-high |
| Language profile does state `open` for multi-clause | `genia_language_profile` output (`idioms.clauses`, `examples.factorial`) | High |
| Spec-runner lacks a case-name filter | Slice A and Slice B comments (one agent, one family) | Low-medium (count is 1 family) |
| Gate exit-status and host-parity policy already planned | `docs/strategy/roadmap/r39.md` lines 31–41 | High |
| Python Counter shorter than Genia fold for histogram | comment 6277294207 | Medium (author statement) |

## D. Adoption barriers

| Barrier | Area | Demonstrated by | Note |
|---|---|---|---|
| Can't find multi-clause/`open` form; guessed wrong 3× | 5 Documentation/discoverability | Slice B | Not language design |
| `starts_with` argument order, `first` returns Option, no regex; 5 attempts | 5 / 2 | F2/P2-C (3-row sample only) | Mostly discovery; "no regex" is a stdlib question with E evidence |
| `walk/4` fallback `_` mistake; raw `map_get` vs `get` with Option | 5 | Retrospective; Slice A | Pattern-arity and Option contracts are learned, not defects |
| Opaque `runtime_error` in MCP | 4 Tooling | This review | Deliberate; trade-off needs an owner decision |
| Builtin-name collision → generic policy denial | 4 / 5 | This review | Single probe |
| Diagnostics lack source-row provenance | 2 / 1 | This review | E |
| No exit-status mapping for gate programs | 3 Host | Retrospective O5 | Owned by R39 |
| Spec-runner has no case filter; 5-minute full suite | 4 (non-Genia tooling) | Model B family | Not a Genia gap |
| Files/processes/AST/hash/YAML/Git/CI are host work | 7 Positioning / 3 | Retrospective O7/O8; Model B | Continue external tool |
| Cross-host portability of data helpers | 6 / 3 | Compatibility JSON is Python-only | Use strict `json_decode` only after checking its wrapper |
| No measured effort comparison | 8 Evidence gap | All | Unmeasured costs: authoring time, review time, tokens, adoption friction for a human unfamiliar with Genia |

Reclassifications:
- F2/P2-C fragment: **B → A (discoverability) with E for "no regex".** Five attempts on argument order and Option returns are documented behavior; the three-row sample cannot support an ergonomics claim.
- Slice B "wrong clause syntax ×3": **E → A (discoverability).** Cheatsheet gap confirmed here; profile already contains it.
- Retrospective O5 (exit status): **C → C owned by existing R39; not a new gap.**
- Model B spec-runner subset selection: **D/tooling note → Investigate further (tooling, not Genia).**
- Slice A tally: stays A for the fold; **D** for any replacement, since the Python expression is shorter and sits inside host-bound work.
- Model B family: three-plus comments count as **one** task family. genia-cpp #51: **not counted.**

## E. Top opportunities (ranked)

Roadmap placement uses existing homes only. None changes R29 scope. None is a ticket; the owner decides.

| # | Opportunity | Disposition | Benefit | Evidence | Difficulty | Placement |
|---|---|---|---|---|---|---|
| 1 | **Agent-first discovery fixes, documentation/profile only:** cheatsheet section for multi-clause `open` recursion; a short "common builtin names and Option-returning functions" table; profile facts for known traps (reserved builtin names such as `input`, tuple-pattern arity, `get` vs `map_get`). | Use Genia now (docs) | Cuts repeated first-attempt failures reported in four separate notes | Medium-high (four distinct symptoms, though all from one operator's agents; one confirmed by direct inspection) | Low | R33 Developer Experience, or an unnumbered docs task; no semantics. Must be verified against `GENIA_STATE.md` and run |
| 2 | **Killer-workflow flagship comparison (see §H),** then publish the verified example as onboarding material if it holds | Use Genia now / Investigate | Tests the central value claim against a fair Python baseline | Low today (one slice, no comparison) | Medium | Existing killer-workflow priority; cross-cutting experiment, not a release |
| 3 | **R39 host-parity policy shadow slice** with negative fixtures and dual-run | Improve existing (already planned) | Best-evidenced reusable policy candidate; includes gate exit-status decision | Medium (retrospective O1) | Planned | R39 as written; no change |
| 4 | **MCP self-correction:** decide whether `genia_run` may return a bounded, non-leaking error class or identifier for evaluation errors; also whether builtin-name collisions can say which name | Investigate further | Lets an agent repair code through the sanctioned tool | Low-medium (one session, three errors) | Design/security trade-off | R28 follow-up or R33 preflight; must respect the existing deliberately fixed message |
| 5 | **Spec-runner case-name filter** | Continue external tool (small tooling item) | Saves minutes per Model B-style task; unrelated to language | Low-medium (one family) | Low | Existing spec-runner owner (R16/R39 tooling); not a Genia ticket |

Not ranked, deliberately: source-row provenance in validation diagnostics (E; include in the §H experiment before any proposal); regex/hash/YAML builtins (rejected by the retrospective; no new evidence).

## F. Negative findings

- Timing formatter replacement failed equivalence (float binary vs decimal half-up). Keep Python.
- Concurrency/process orchestration, Git/CI queries, AST/Tree-sitter, hashing, archive building, native instrumentation, race-injection tests, perf harnesses (`perf_counter`), bulk text edits, YAML fixture generation: all D or E. None was a Genia failure.
- Python threading hooks used for deterministic race tests (Model B) have no Genia analogue and should not.
- Retrospective baseline-ratchet and matrix-invariant fragments matched Python but benefit is low; replacing a tiny embedded function costs more than it saves.
- A returned `err(...)` exiting 0 is a host-edge design question, not an API to add in isolation (per R39).
- The pilot itself produced a `genia-cpp` #51 comment that executed nothing and an F2 fragment tried on three rows; neither is evidence of fit.
- Not pursued: new syntax, new builtins for regex/hashing, a Genia-native Git or CI layer.

## G. Dogfooding process recommendation: **REVISE**

Answers to the review questions:
- *Actionable insights?* Yes, but about discovery and false-gap prevention, not about missing features.
- *Revealed unknown capabilities?* Yes: `validate_*`/`collect_validated`, `parse_jsonl_record`, and Option/`get` contracts were repeatedly unfamiliar.
- *Overhead justified?* Retrospective: no, as a per-task practice (3 collectors + coordinator + auditor). Prospective notes: reported as "a few minutes", but unmeasured.
- *Incentivized unnatural substitutions?* Mild signs: F2 and Slice A fragments were tried partly because the pilot asked. Both honestly ended D/E.
- *Duplicates/noise?* Yes: one task family produced five comments; one incomplete task produced a sixth.
- *Optional, sampled, periodic, standardized?* Optional and sampled by **task family**, not by comment; periodic aggregation by a coordinator.

Proposed revision (needs owner approval; this review edits no instruction file):
1. Count independent *task families*; one note per PR/family.
2. Record notes only when the task contained validation, transformation, reporting or diagnostics over structured data; otherwise "none" is optional.
3. Add one field to the template: **discovery friction** (what was guessed, how many attempts, where the answer was finally found). It was the most valuable signal in the pilot.
4. Keep "tested vs hypothetical" and "review cost: not recorded" as is.
5. Stop at 5 independent families or 60 days, whichever comes first; then aggregate once.
Expand only if discovery fixes (§E-1) demonstrably cut guess counts, or if ≥2 independent A/B findings recur. Stop if later notes keep returning D/E with no new discovery signal. Do not add a CI or agent gate.

## H. Next product experiment

**Same workload, three independent authors, pre-registered criteria.** Workload: CI test-result quality report from JSONL.

- Inputs (public, synthetic): a ≥12-record corpus including valid, blank, malformed JSON, missing field, wrong value, negative duration, duplicate suite, Unicode suite name, extra fields, and a record that is valid JSON but not an object. Expected clean list, diagnostics and report written *before* any implementation.
- Task: read from a file/stdin via CLI, produce clean records, diagnostics with source line numbers, a status tally, total duration, and failing suite names; then a requirement change (add a rule: durations over 10 minutes are errors) and a defect-injection review.
- Conditions: Genia (CLI mode, using only the MCP profile and documented sources), Python stdlib, and Python with a validation library. At least three fresh-agent runs per condition plus one human reviewer reading outputs.
- Measures: pass/fail on the expected-output corpus; tool calls and attempts to first valid run; hallucinated names; diagnostic usefulness (rubric: identifies row, field, expected, actual); change-request correctness; reviewer's ability to find the injected defect; secondary: line count. Report failures. No effort or token savings unless the same measurements were recorded under all conditions.
- Success for Genia means "equal correctness with fewer silent failure modes or clearer diagnostics at comparable attempts," not "shorter code." A loss is a valid, useful result.

## I. Issue #1226 disposition

**Revise acceptance criteria and keep open.** The criteria that require 5–10 heterogeneous tasks are unmet (2 independent completed families, 1 incomplete) and should not be satisfied by splitting slices. Revised criteria: five independent task *families* or 60 days; template gains a discovery-friction field; aggregation once with explicit independence counts; a Genia-vs-Python comparison (§H) is accepted as a substitute for further passive observation if the owner prefers. Closure is not the objective; the evidence supports the REVISE verdict already recorded on #1226 and adds the discovery-first emphasis.

---

## Appendix — verified runs (MCP `genia_run`, Python reference host, 2026-10-20)

Run 1: validated JSONL pipeline. Source (exact):

```genia
is_status(s) = any?((x) -> x == s, ["pass", "fail", "skip"])
non_empty(s) = s != ""
non_neg(n) = n >= 0
check(rec) = validate_record(rec, {
  suite: (r) -> validate_field("suite", non_empty, "non-empty", r),
  status: (r) -> validate_field("status", is_status, "pass|fail|skip", r),
  ms: (r) -> validate_field("ms", non_neg, "non-negative", r)
})
raw = [
  "{\"suite\":\"parser\",\"status\":\"pass\",\"ms\":120}",
  "{\"suite\":\"\",\"status\":\"pass\",\"ms\":5}",
  "{\"suite\":\"cli\",\"status\":\"flaky\",\"ms\":-3}",
  "not json",
  "",
  "{\"suite\":\"io\",\"ms\":900}",
  "{\"suite\":\"io\",\"status\":\"fail\",\"ms\":900}"
]
collect_validated(validate_each(map(parse_jsonl_record, raw), check))
```

Observed: `clean` held records 0 and 6; `diagnostics` held index 1 (`suite` invalid), index 2 (`status` and `ms` invalid, both reported), index 3 (`invalid_jsonl_record`, line text and column), index 4 (`skipped`, `blank_line`), index 5 (`status` missing). Failure diagnostics for validation carried `field`/`expected`/`actual` but not the original line.

Run 2: report aggregation over clean records (`reduce` with `map_put`/`get`/`unwrap_or`, `filter`, `map`) gave `{by_status: {pass: 2, fail: 1}, total_ms: 1025, failing: ["io"]}`.

Run 3–4: `is_number(1)`, `type_of(1)`, and an undefined name each returned `runtime_error` / `Genia source failed during evaluation`.

Run 5: `input = [1]` returned `policy_denied` / `source requests a capability unavailable in the MCP v1 profile`; renaming to `raw` ran.

Not tested: behavior of `validate_field` with a non-numeric value under `>=`; CLI file/stdin mode; any cross-host run; any Python equivalent.
