# GENIA Change Pre-Flight: MCP maturity and known-gap discovery (#1086)

Status: **Completed pre-flight / design decision, 2026-10-06.** R28 follow-up,
not a new release or implemented MCP behavior. `GENIA_STATE.md` remains final
authority. The proposed output below is not returned by the current server.

## Change identity

- **Change name:** scoped maturity and known-gap discovery in the language profile
- **Release / issue:** R28 follow-up, #1086; classification parent #1085
- **Proposed branch:** `issue-1086-mcp-maturity-preflight`
- **Owner:** repository owner; agent-authored recommendation pending review

## 1. Scope lock

**Includes:** choose the discovery surface; define a bounded static candidate
shape; map its claims to STATE; specify subsequent phase gates and child issues.
This step produces one design document and focused verification only.

**Excludes:** new syntax, parser/evaluator/AST/Core IR changes, builtins, shared
semantic-spec changes, host protocol or capability changes, C++ MCP, MCP
resources/prompts/HTTP, authority, client-dependent output, provider/RAG work
(#1087), and runtime implementation in this step. No `genia_capabilities`
expansion, filesystem discovery, remote requests, live host probing, or new
capability registry.

## 2. Source of truth and prerequisite review

Read: `AGENTS.md`, `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`,
`README.md`, `docs/process/run-change.md`, `docs/process/08-roadmap-ticketing.md`,
`docs/strategy/killer-workflow.md`, `docs/strategy/release-roadmap.md`,
`docs/design/r28-a6-language-profile-preflight.md`, `docs/mcp/reference.md`,
`docs/releases/R28.md`, and amendment A6 in
`docs/design/r28-genia-mcp-contract-threat-model.md` section 19.

The requested `docs/design/r28-follow-up-1085-classification-preflight.md` is
absent on this checkout's main. It was read from parent branch commit
`8412a963239ea2f4fa9dd8900335e452edcc1cc8` (reported in #1085). It promotes #1086
only for a separate decision and leaves #1087 separate; it grants no runtime
implementation authority. This document does not require that branch's merge
and does not copy its roadmap edits.

**Authoritative sections:** STATE 0, 0.1, 1, 5, 8, 9.48–9.50; see the field
and row mappings below. Relevant RULES: 6 (patterns), 8 (resolution), 8.4 (Core
IR), 9.1 (tail calls), 10 (observable spec scope), 16 (conditional model), and
19 (Flow). Lower-priority sources supply context and evidence, never additional
implemented claims.

**Conflicts resolved for this decision:** STATE 0 retains R25-era C++ summaries
and an "Other hosts are not implemented" sentence under shared-contract
maturity, while its opening and later R26/R27 entries identify the bounded R27
production host. STATE 10 retains an acceptance-gate-open parenthetical; 9.49
records completion. Use the explicit later implemented entries for those
facts, not those obsolete summaries. Do not infer global language stability
from release completion, or lack of runtime Flow from partial shared coverage.
Broad historical-summary cleanup is separate from this decision.

## 3. Feature maturity

- [x] N/A — process/docs-only for this change
- [ ] Experimental
- [ ] Partial
- [ ] Stable

The candidate is an MCP adapter affordance on the Python reference host.
Implementation status and maturity are separate axes. A completed release can
contain Experimental behavior. An absent maturity label means unspecified,
not Stable. Planned/scaffolded entries are unavailable. The catalogue is
curated and non-exhaustive, not a language-wide maturity rating.

## 3a. Portability analysis

1. **Affected hosts:** none in this step; future MCP application output affects
   the Python reference-host deployment only, with no Python host-code change.
2. **Portable observable behavior:** none; static MCP discovery is an
   application contract, not portable Genia evaluation semantics.
3. **Authority and representation/boundary:** STATE owns each claim; amendment
   A6 owns the existing `genia.mcp.v1` envelope and `result.language` boundary.
4. **Shared executable evidence:** no new shared spec is applicable to MCP
   metadata. Existing R16 evidence remains the source for covered semantics;
   proposed wire assertions belong in the R28 adapter suite.
5. **Applicability vocabulary:** no `spec/manifest.json` capability addition or
   change; no second capability/profile registry for host conformance.
6. **Host claims and gaps:** no host support claim changes and no
   `spec/known_host_gaps.json` edits. C++ MCP remains unsupported; bounded C++
   language support is a different fact. No temporary parity exception needed.
7. **Truth synchronization:** after implementation and verification, update
   STATE 9.50, the application contract, MCP reference/matrix, release page,
   and affected summaries together; preserve historical acceptance evidence.

## 4. Contract vs implementation

- **Portable contract:** unchanged; facts restate STATE only.
- **Python implementation today:** A6 returns the eight documented language
  members: `name`, `contract_revision`, `control_flow`, `supported_forms`,
  `patterns`, `absent_forms`, `idioms`, `examples`. It has no maturity catalogue.
- **C++ implementation today:** bounded R27 production language host; no MCP.
- **Not implemented:** the extension described below, live gap discovery,
  source-specific hints, and any #1087 showcase.

### Surface decision

| Option | Decision | Reason |
|---|---|---|
| Extend `genia_language_profile` | **Selected** | Same assistant question and static no-argument boundary as A6; adds no tool or authority. |
| Separate MCP affordance/tool | Rejected for this slice | Duplicates discovery and revision identity; no independent input, lifecycle, or authority justifies a fifth tool. |
| Documentation-only | Rejected as the final solution | Docs remain authority, but do not answer structured discovery for a connected assistant. This step itself is documentation-only. |
| Deferred | Not selected for the bounded slice | #1085 promoted this decision and it supports truthful pipeline generation. Exhaustive inventories and live host introspection remain deferred. |

`genia_capabilities` continues to report server identity, advertised tools,
protocol, and governed execution policy. It does not need language maturity;
A6's separation remains sufficient.

### Candidate output (requires a later contract amendment)

Add only `language.discovery`, with exactly `{coverage, facts}`. `coverage` is
the literal `"curated_non_exhaustive"`. `facts` is a fixed ordered array of the
12 rows below, not a client query or a generated inventory. Every row has
exactly `{id, scope, status, maturity, summary, state_sections}`:

| Field | Candidate rule | Authority / rationale |
|---|---|---|
| `coverage` | Fixed disclaimer; omitted facts imply nothing | STATE 0/1 limit coverage claims; this selection policy is proposed adapter metadata. |
| `id` | Unique stable identifier from the table | Proposed adapter labels, not builtin or capability names. |
| `scope` | One of `language`, `shared_conformance`, `cpp_host`, `other_hosts`, `browser`, `mcp`, `mcp_windows`, `mcp_macos` | STATE 0/0.1 and 9.48–9.50 distinguish these boundaries. |
| `status` | `implemented`, `partial`, `planned`, `scaffolded`, or `unsupported` | STATE sections in each row; applies only to that row's scope. |
| `maturity` | `Experimental`, `Partial`, `Stable`, or JSON null | Copy an explicit STATE label only; no selected row warrants `Stable`. Null means no explicit rating, never unavailable. |
| `summary` | One fixed sentence, at most 256 UTF-8 bytes | Narrow restatement of the cited STATE entries, not new semantics. |
| `state_sections` | Nonempty ordered array of section identifiers, e.g. `["9.49", "9.50"]` | References `GENIA_STATE.md` in the same launch revision, not live URLs or roadmap authority. |

Candidate fact values and source mapping (summaries here are the proposed text):

| `id` | `scope` | `status` | `maturity` | `summary` | `state_sections` |
|---|---|---|---|---|---|
| `pattern_branching` | language | implemented | null | Branching uses pattern matching. | 5 |
| `tail_calls` | language | implemented | null | Tail calls are optimized. | 8 |
| `if_and_loops` | language | unsupported | null | There is no dedicated if expression or while/for loop syntax. | 5, 9.50 |
| `flow_shared_coverage` | shared_conformance | partial | Experimental | Flow runs in Python; shared executable coverage is limited to first-wave cases. | 0, 1 |
| `core_ir_stability` | shared_conformance | partial | Partial | Portable Core IR stability remains Partial. | 0 |
| `cpp_language_floor` | cpp_host | partial | null | C++ implements the bounded R27 production floor, not Python feature parity. | 0 |
| `other_language_hosts` | other_hosts | planned | null | Node.js, Java, Rust, and Go hosts are planned, not implemented. | 0 |
| `browser_runtime` | browser | scaffolded | null | Browser artifacts are documentation scaffolding; no runtime or playground is implemented. | 0.1 |
| `mcp_surface` | mcp | implemented | null | Python-host local stdio MCP exposes four tools after A6. | 9.49, 9.50 |
| `cpp_mcp` | mcp | unsupported | null | There is no C++ MCP implementation. | 9.49, 9.50 |
| `windows_mcp` | mcp_windows | unsupported | null | Windows MCP deployment is unsupported. | 9.49 |
| `macos_hardening` | mcp_macos | partial | null | macOS MCP runs are verified without an address-space bound or network namespace; the profile is not a security sandbox. | 9.48, 9.49 |

`partial` in the C++ and macOS rows describes a bounded support/hardening
surface, not an inferred maturity label or a partially implemented C++ MCP.
`unsupported` syntax is intentional absence, not a promised future feature.
`scaffolded` describes documentation existence only. MCP execution denial is
still described by `genia_capabilities.execution_profile`, not inferred from
language support. These rows are not permission to invoke denied capabilities.

Keep all A6 members, examples, revision semantics, tool order, argument policy,
and envelopes unchanged. Candidate discovery JSON must be at most **16,384
UTF-8 bytes**; this is a proposed static-fixture bound, not a new execution
limit. Only the existing launch `contract_revision` varies; no timestamp,
client input, environment, git fetch, filesystem read, host evidence scan, or
runtime probing enters the constant. Changes to claims require ordinary
review and updated pinning tests; the server never parses STATE at runtime.

## 5. Test strategy

**Current step:** run focused semantic-doc, overclaim, R28 ledger, and release
gate checks; review that only this proposed document changes.

**Future failing-test phase:** extend
`tests/unit/test_r28_mcp_language_profile.py` to pin the exact new member set,
closed nested schema, all 12 rows and their section mappings, enums/nulls,
unique IDs, order, summary byte bounds, and discovery byte bound. Preserve
omitted/empty argument acceptance and non-object/nonempty rejection; compare
bytes across repeated calls, protocol eras, namespace modes, and plain file
mode. Pin no fifth tool, capabilities shape unchanged, text/structured
envelope equality, no resources/prompts, no if/loops or C++ MCP claims.

Truth checks must verify cited STATE headings exist and representative claims
match their scoped authoritative entries, with a manual semantic review of
every row. Checking section existence alone cannot prove prose truth. Existing
A6 example execution tests remain required. Assert launch-revision agreement
with capabilities. These are Python-host MCP adapter checks, not a claim of
new shared conformance; no portable behavior changes or shared spec additions.

## 6. Examples

- **Minimal:** proposed `cpp_mcp` row says unsupported even though the
  `cpp_language_floor` row says partial production language support.
- **Realistic:** a pipeline assistant sees implemented pattern branching and
  tail calls, absent if/loop syntax, and partial shared Flow coverage without
  treating Python Flow as unavailable or enabling network authority.
- **Classification:** design-only MCP metadata illustrations; no new runnable
  Genia example or cheatsheet snippet is added.

## 7. Complexity check

- [x] Revealing existing structure
- [x] No implementation complexity in this process/docs-only step
- [ ] Adding necessary complexity

A single curated array expresses gaps and support without parallel positive
and negative catalogues. The fixed count and narrow fields avoid a new host
registry, capability query language, exhaustive release matrix, or framework.

## 8. Cross-file impact

**This step:** this document only. Drift risk: **Medium**, because static
claims duplicate selected STATE facts. No wording changes to STATE, RULES,
README, REPL README, AGENTS, MCP reference, or acceptance records are needed
to document a proposal rather than implemented behavior.

**After verified implementation:** STATE 9.50; contract amendment following A6;
`apps/mcp/mcp.genia`; profile tests and relevant closed-schema fixtures;
`docs/mcp/reference.md`, `docs/mcp/conformance-matrix.md`, and
`docs/releases/R28.md`. Review README, REPL README, AGENTS,
`docs/ai/LLM_CONTRACT.md`, RULES, MCP demo, relevant book and core/unix
cheatsheet pages and synchronize wording only where affected. Generated public
function docs are inapplicable (no prelude metadata change). Shared specs,
host-gap manifest, parser/evaluator/Core IR, and host protocol stay untouched.
The authentic R28 acceptance runs continue to describe their original three
tools; neither A6 nor this proposal has a new authentic client run recorded.

## 9. Philosophy check

- **Preserves minimalism:** YES — no new tool or language surface.
- **Avoids hidden behavior:** YES — static data, no input or acquisition.
- **Keeps semantics out of host adapters:** YES — claims come from STATE;
  candidate constants live in the native MCP application.
- **Aligns with pattern-matching-first design:** YES — preserves A6 guidance.
- **Strengthens the Outcome-aware validated-data-pipeline priority:** YES,
  indirectly, by preventing assistants from generating unavailable constructs
  and confusing language support with MCP authority. #1085 explicitly promotes
  this follow-up independently of the #1087 showcase.

## 10. Prompt plan and recommended child issues

This step completes **pre-flight, design selection, documentation, and focused
truth review** only. It does not amend A6, add failing tests, implement output,
or distill implemented-behavior docs. Those phases require subsequent prompts
and separate commits per `run-change.md`.

Recommend the following issue creation order (recommendations, not created):

1. **R28 follow-up: contract/design amendment for scoped profile discovery.**
   Depends on this decision; classification Follow-up. Lock the above candidate
   field/row inventory, status/maturity meanings, compatibility with A6's closed
   schema, static bound, source mapping, and acceptance obligations. Scope
   excludes language/host changes and #1087. Acceptance: approved application
   contract and final source review; no implementation claim. Medium drift risk.
2. **R28 follow-up: implement and verify the approved profile discovery extension.**
   Depends on the approved amendment; classification Follow-up. Commit failing
   adapter tests first; implementation commit must reference that SHA; then
   minimal native constants, documentation synchronization, focused audit, and
   distillation. Acceptance: closed deterministic bounded output, preserved
   arguments/eras/tools/policy, row-by-row STATE truth, and historical acceptance
   unchanged. Affected surfaces and tests are listed in sections 5 and 8.
   Medium drift risk; all exclusions of section 1 remain non-goals.

No separate tool, capabilities expansion, RAG implementation, or exhaustive
live gap-inventory issue is recommended for this slice.

## 11. Host Parity / Conformance

**Affected hosts:** none now; Python MCP deployment for the future extension.
**Changes portable semantics:** NO. **Shared evidence additions:** N/A.
**Python/C++ implementation updates:** none now; future native application
constant only. **Cross-host verification / temporary gaps:** N/A; no C++ MCP
claim is made. **Can one host merge before the other:** N/A for MCP-only data.

## 12. Final GO / NO-GO

**GO** for the selected `genia_language_profile` extension to proceed to a
separate contract/design amendment. **NO-GO for runtime implementation now:**
A6 currently closes the language member set; the new amendment must be
approved and failing tests committed before implementation. This is a process
dependency, not a deferred discovery decision. No language or runtime behavior
is implemented or approved by this document alone.

**Remaining dependencies:** owner review of this recommendation, approved
application amendment, final claim review, and failing-test SHA. No unresolved
surface choice remains. **Decision date:** 2026-10-06; agent recommendation,
not a claim of owner approval.

## Verification of this pre-flight

`uv run pytest -q tests/doc/test_semantic_doc_sync.py
tests/doc/test_r28_inventory_ledger.py tests/unit/test_no_overclaim_language.py
tests/unit/test_r28_release_gate.py`: **678 passed, 1 skipped**. The skip is the
release-gate test for a latest acceptance run that is not executed; run 3 is
executed, so that scenario is inapplicable. `git diff --check` passed. These
checks validate existing truth guardrails, not the proposed wire output; its
new tests belong to the subsequent failing-test phase.
