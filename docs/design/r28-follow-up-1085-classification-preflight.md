# GENIA Change Pre-Flight: R28 Remaining MCP Follow-Up Classification

Status: **Classification / pre-flight for issue #1085.** This document records
the remaining work after R28 amendment A6 (`genia_language_profile`) and decides
what may proceed as implementation work later. It does not implement runtime,
MCP, language, host, or documentation-truth behavior.

`GENIA_STATE.md` remains final authority for implemented behavior.

## Change identity

- **Change name:** R28 remaining MCP follow-up classification
- **Release / issue:** R28 follow-up; issue #1085
- **Proposed branch:** `issue-1085-r28-follow-up-classification`
- **Owner:** repository owner

## 1. Scope lock

**Includes:**

- Classify the remaining items raised after R28/A6:
  - accidental SICP artifact handling;
  - language-profile maturity and known-gap discovery;
  - capability discovery shape;
  - misleading Genia code generation;
  - MCP-backed grounded-answering / RAG-style killer-workflow showcase;
  - process/pre-flight requirements for any promoted child work.
- Decide which items are already complete, which require child issues, and
  which must stay deferred or parked.
- Preserve the distinction between implemented R28/A6 behavior and future
  roadmap work.

**Excludes:**

- Adding or changing Genia syntax, parser behavior, evaluator behavior, Core IR,
  builtins, shared semantic specs, host protocol, or host capability claims.
- Adding MCP resources, prompts, Streamable HTTP, C++ MCP, a Genia MCP client,
  arbitrary filesystem/shell authority, or RAG/model/provider behavior.
- Treating any RAG/showcase or maturity-matrix idea as implemented behavior.
- Reintroducing SICP artifacts as Genia language authority or R28 source
  material.

## 2. Source of truth

- **Authoritative `GENIA_STATE.md` sections:**
  - section 0: current host, maturity, shared-spec, and limitation status;
  - section 5: case expressions and pattern matching;
  - section 8: tail-call optimization;
  - section 9.49: completed R28 MCP server;
  - section 9.50: R28 amendment A6, `genia_language_profile`.
- **Relevant `GENIA_RULES.md` sections:**
  - pattern-validity and function-resolution invariants;
  - tail-call and parser/evaluator invariants.
- **Additional relevant docs/contracts:**
  - `AGENTS.md`;
  - `README.md`;
  - `GENIA_REPL_README.md`;
  - `docs/process/run-change.md`;
  - `docs/process/08-roadmap-ticketing.md`;
  - `docs/strategy/killer-workflow.md`;
  - `docs/strategy/release-roadmap.md`;
  - `docs/strategy/roadmap/r25-r29.md`;
  - `docs/design/r28-a6-language-profile-preflight.md`;
  - `docs/design/r28-genia-mcp-contract-threat-model.md`;
  - `docs/mcp/reference.md`;
  - `docs/releases/R28.md`.
- **Conflicts or ambiguities to resolve before proceeding:**
  - "R28 follow-up" currently names several distinct things. This issue must
    split them before implementation work starts.
  - Historical R28 acceptance records saw the original three-tool surface and
    must not be rewritten as if `genia_language_profile` existed then.
  - SICP appears only as historical or external learning-material handling, not
    as an R28 or language-design source of truth.

## 3. Feature maturity

- [ ] Experimental
- [ ] Partial
- [ ] Stable
- [x] N/A -- process/docs-only

**Required documentation wording / maturity impact:**

This issue may say only that the remaining work has been classified. It must
not claim a maturity matrix, richer capability discovery, or RAG/showcase
behavior exists until separately approved child issues implement and verify it.

## 4. Contract vs implementation

- **Portable contract:** none. This classification does not alter portable
  Genia semantics or shared conformance.
- **Python implementation today:** unchanged. R28/A6 behavior remains the
  current implementation: `apps/mcp/mcp.genia` exposes `genia_language_profile`
  as static adapter text.
- **C++ implementation today:** unchanged. There is no C++ MCP.
- **Not implemented by this issue:**
  - structured maturity/known-gap output;
  - a richer `genia_capabilities` payload;
  - MCP-backed grounded-answering / RAG showcase;
  - source-specific code-generation hints;
  - any new MCP authority.

## 5. Classification

| Item | Classification | Decision |
|---|---|---|
| Archive/remove accidental SICP reference | No implementation work / truth-protection note | Keep SICP out of R28. Do not use `SICP-PDF.txt` or external SICP material as Genia authority. Existing repo text may continue to describe SICP validation only when a `docs/sicp` tree exists. |
| Existing `genia_language_profile` endpoint | Complete R28 follow-up (A6) | No child issue needed for the current A6 behavior. It already documents pattern matching, no `if`, no loops, recursion, TCO, idioms, and runnable examples. |
| Base profile on `GENIA_STATE.md` | Complete for A6 | Existing tests evaluate examples and docs point back to `GENIA_STATE.md`. Future additions must map each field to an authoritative section. |
| Structured maturity / known-gap discovery | Follow-up candidate | Tracked by #1086. Preferred first decision: extend `genia_language_profile` versus add a separate discovery affordance versus docs-only. |
| Improve `genia_capabilities` directly | Deferred unless justified by child pre-flight | A6 deliberately used a separate profile tool. Do not widen `genia_capabilities` in this issue. |
| Prevent misleading GCD / `if` code generation | Complete for the immediate problem | `genia_language_profile` includes the canonical `open gcd(a, 0)` pattern-matching example and absent forms. |
| MCP-backed grounded-answering / RAG killer-workflow showcase | Follow-up candidate, not R28 behavior | Tracked by #1087. It must stay within the MCP threat model and killer-workflow strategy. |

## 6. Test strategy

- **Core invariants:**
  - this issue changes classification only;
  - implemented-truth docs must not describe maturity/gap or showcase work as
    complete;
  - R28/A6 existing tests remain the evidence for current behavior.
- **Expected behavior:**
  - no runtime or protocol behavior changes;
  - any later implementation has its own focused failing tests.
- **Failure cases:**
  - docs imply future maturity/RAG behavior is implemented;
  - docs imply SICP is an R28 input or language authority;
  - a child implementation issue skips pre-flight.
- **Shared spec/conformance approach:** N/A for this classification issue.
- **Host-specific test approach:** existing focused tests remain sufficient for
  current A6 behavior. If a child issue changes MCP output, update the R28 MCP
  unit tests for that child issue.

## 7. Examples

- **Minimal example:** N/A; process-only classification.
- **Realistic example:** a future maturity child issue might add static fields
  such as implemented/partial/planned/unsupported surfaces, but this document
  does not approve their names or shape.
- **Classification:** process-only.

## 8. Complexity check

- [ ] Adding necessary complexity
- [ ] Revealing existing structure
- [x] No implementation complexity -- process/docs-only

**Justification and simpler alternatives considered:**

The simpler alternative is to treat #1085 as a broad implementation ticket. That
is rejected because it would mix assistant guidance, capability discovery,
SICP cleanup, and a possible RAG showcase into one change. Splitting preserves
the R26+ change process.

## 9. Cross-file impact

**Files or surfaces likely to change in this classification step:**

- `docs/design/r28-follow-up-1085-classification-preflight.md`
- `docs/strategy/roadmap/r25-r29.md`

**Drift risk:**

- [ ] Low
- [x] Medium
- [ ] High

**Required synchronization:**

No implemented-behavior synchronization is required for this classification
step. Any child issue that changes MCP output must update `GENIA_STATE.md`,
`docs/mcp/reference.md`, `docs/releases/R28.md`, `README.md`, and tests as
appropriate.

## 10. Philosophy check

- **Preserves minimalism:** YES
- **Avoids hidden behavior:** YES
- **Keeps semantics out of host adapters:** YES
- **Aligns with pattern-matching-first design:** YES
- **Strengthens the Outcome-aware validated-data-pipeline priority, or has an approved reason not to:** YES

**Notes:**

The classification protects the killer-workflow direction by keeping a possible
MCP-backed RAG showcase separate from the already-complete MCP adapter surface.

## 11. Prompt plan

- [x] Pre-flight
- [ ] Contract
- [ ] Design
- [ ] Failing tests
- [ ] Implementation
- [x] Documentation
- [x] Audit
- [ ] Distillation

**Phase order, issue split, and skipped-phase rationale:**

This issue completes classification/pre-flight only. Contract, design, failing
tests, implementation, full docs sync, and distillation are skipped here because
no behavior is changed. Child issues were created in this order:

1. #1086 -- maturity / known-gap discovery shape;
2. #1087 -- MCP-backed grounded-answering / RAG killer-workflow showcase.

Each child issue must run the normal pre-flight through audit path.

## 12. Host Parity / Conformance

**Affected hosts:**

- [ ] Python
- [ ] C++
- [ ] Other / future

**Does this change portable semantics?** NO

**If YES:** N/A.

**Can one host merge before the other?** N/A

**If YES, temporary compatibility note:** N/A.

## 13. Final GO / NO-GO

**Ready to proceed?** GO for classification and issue splitting; NO-GO for
implementation inside #1085.

**Missing decisions, evidence, or dependencies:**

- #1086 must decide whether maturity/gap discovery should be a
  `genia_language_profile` extension, a separate MCP affordance, or
  documentation-only.
- #1087 must decide whether the MCP-backed grounded-answering / RAG showcase is
  important enough to promote now or should remain roadmap guidance.

**Reviewer / decision date:**

- Repository owner, 2026-10-06.
