# GENIA Change Pre-Flight: MCP-backed grounded-answering showcase (#1087)

Status: **Completed pre-flight / design decision for issue #1087, 2026-10-06.**
This document decides whether and in what shape a showcase belongs near R28. It
implements nothing: no runtime, MCP, language, host, example, or test behavior
changes here. The showcase is **planning guidance, not implemented behavior**,
until child issues land their own contract, failing tests, implementation, docs
sync, and audit.

`GENIA_STATE.md` remains final authority for implemented behavior.

## Change identity

- **Change name:** MCP-backed grounded-answering / killer-workflow showcase decision
- **Release / issue:** R28 follow-up, #1087; classification parent #1085
- **Proposed branch:** `issue-1087-mcp-grounded-showcase-preflight`
- **Owner:** repository owner

## Decision summary

| Question | Decision |
|---|---|
| GO / NO-GO | **GO for a narrow tested executable example** (child issues only). **NO-GO** for anything that adds MCP authority, a provider, a builtin, or language surface. |
| Classification | **Tested executable example** (option 3). It is *delivered through* the existing `genia_run` tool and may be linked from `docs/mcp/demo.md`, but it is not a new MCP demo surface, not docs-only, not a later release, and not parking-lot. |
| Why not docs-only | The repository rule is that documented examples must be test-verifiable. A prose-only "showcase" would claim behavior with no executable evidence. |
| Why not a new MCP demo | R28's four tools are closed; a demo that needs anything beyond `genia_run` would widen the contract. |
| Why not later / parking | Every ingredient is already implemented and reachable under the unchanged policy (verified below). Cost is one example plus tests; no release placement is needed. |
| What it is *not* | Not the full R12 retrieval pipeline. The provider-backed stages cannot run under MCP, and the showcase must say so. |

## 1. Scope lock

**Includes:**

- Decide GO/NO-GO and classify the showcase shape.
- Define exactly what data crosses into Genia, what Genia computes, what the MCP
  client sees, and what stays outside Genia.
- Define the child-issue split and per-child gates.

**Excludes:** a Genia MCP client; autonomous agent orchestration; filesystem,
shell, Git, network, workspace, or MCP-root authority; new syntax, parser,
evaluator, Core IR, or shared-spec behavior; `rag_chat`; any new public grounding
builtin; Ollama/Groq/RAG providers for `model/4`; MCP resources, prompts, HTTP
transport, or C++ MCP; any change to the R28 threat model or execution profile;
and any statement that the showcase is implemented.

## 2. Source of truth

- **`GENIA_STATE.md`:** section 9.49 (R28 complete), 9.50 (A6/A7 profile and
  discovery), and the R12 retrieval/grounding sections. Also section 0 for host
  and maturity status.
- **`GENIA_RULES.md`:** Outcome and function-resolution invariants apply unchanged.
- **Additional:** `AGENTS.md`; `docs/process/run-change.md`;
  `docs/strategy/killer-workflow.md`; `docs/strategy/roadmap/r25-r29.md`;
  `docs/design/r28-follow-up-1085-classification-preflight.md`;
  `docs/design/r28-genia-mcp-contract-threat-model.md` (sections 4, 6, 13);
  `docs/releases/R28.md`; `docs/mcp/reference.md`; `docs/mcp/demo.md`;
  `docs/design/r12-retrieval-grounding-contract.md`.
- **Conflicts resolved:** the roadmap says R28 "should consider" a showcase in
  which "MCP-supplied context ... enter[s] Genia through an explicit governed
  boundary" and Genia runs a "retrieval/grounding pipeline ... before any LLM
  call". The R28 contract provisions **no** embedding, retrieval, reranking, or
  model provider, and no input channel other than the `source` string. So the
  roadmap wording is only partly realizable; this pre-flight narrows it (section 4)
  rather than widening R28.

## 3. Evidence: what is reachable under `genia_run` today

Checked against the Python reference host over the real `scripts/genia-mcp` stdio
server (not by reading code alone):

| Capability | Under `genia_run` | Evidence |
|---|---|---|
| `chunk/2` (ordinary, no provider) with a user-supplied chunker | **Runs.** Returns `some([{text, source: {doc_id, offset, length}, meta: <represented>}])`. | Ran a one-document program; `status: ok`. |
| Pure grounded-context assembly | A private underscore host function runs, but it is **not** public surface. The public `assemble_grounded_*` functions live in `examples/r12_grounded_context_answer.genia` and need `import`. | `import` is `policy_denied` (threat model section 4). |
| `embed`, `index`, `retrieve`, `rerank`, `model` | **Denied** (`policy_denied`, rows A17/A18 in `tests/unit/test_r28_mcp_conformance_security.py`). | Contract section 4: no provider provisioned. |
| `import`, file, env, config, secrets, network, process, stdin | **Denied.** | Same. |
| `json_encode` / `json_decode` | Run. | Ran both. |
| `value.rendered` for a chunk's `meta` | Renders as `<represented>`, not the metadata content. | Observed. |

Consequences that bind the design:

1. The showcase **cannot** run provider-backed retrieval, embedding, reranking, or
   generation under MCP. Claiming otherwise would contradict the R28 threat model.
2. The showcase **cannot** `import` the repository's R12 grounded-context example
   module; any helper must be defined inline in the one program. It must not
   depend on underscore-prefixed private host functions, which are not public
   surface.
3. Machine-readable evidence cannot rely on `value.rendered` alone (it is debug
   text, "not a portable serialization", and hides `meta`). The contract child must
   decide a shaped output channel (for example `json_encode` to stdout) and test it.

## 4. The showcase boundary

### What enters Genia (exactly)

One thing: the `source` string of a single `genia_run` call, at most 262,144 UTF-8
bytes, authored by the MCP client. The client embeds, as ordinary Genia literals:

- the user question;
- zero or more candidate documents, each `{id, text, meta}`, already read and
  selected by the client;
- optionally the small program text itself.

Nothing else crosses: no stdin (EOF), no argv (`[]`), no files, environment,
configuration, secrets, network, MCP roots, MCP resources, or tool-output
side channels. Document `id`/`meta` are **client-asserted labels**; Genia can show
that an evidence span is the exact code-point slice of the supplied text, but
cannot verify the document's real-world origin. Documents are untrusted data.

### What Genia computes (all ordinary, pure, deterministic, Python-host today)

1. **Validate** documents and the question with the existing
   `validate_each` / `collect_validated` / `validate_record` family. Invalid
   documents become structured, indexed diagnostics, not a crash and not silent
   drops (same pattern as `docs/mcp/demo.md`).
2. **Chunk** valid documents with the ordinary `chunk/2` and an application-supplied
   deterministic chunker, preserving exact code-point offsets, `doc_id`, and
   represented metadata.
3. *(Child contract decides; recommended minimal.)* **Select** evidence with an
   ordinary pure function (for example exact-term overlap with a stable
   document-order tie-break). This is application code. It must be labelled as
   **not** R12 `retrieve/4`, not semantic retrieval, and not ranking quality.
4. **Shape** a grounded evidence package: the question, ordered evidence chunks
   with provenance, first-occurrence-deduplicated `sources`, and the validation
   diagnostics. This reuses the R12 shapes by convention; it adds no builtin.

### What the MCP client sees

The ordinary R28 envelope from `genia_run`: `value.rendered`, `stdout`, `stderr`,
`exit_code: 0`, or one of the closed error kinds. No new field, tool, or error kind.

### What remains outside Genia

- Reading, fetching, selecting, and trusting documents (the client's job).
- **Embedding, vector indexing, retrieval, reranking.** Not available under MCP.
- **Answer generation.** There is no Genia `model/4` call; the MCP client's own
  model reads the returned evidence package and writes the answer.
- **Citation rendering and validation** (R12 excludes it).
- Provenance *authenticity*, persistence, multi-turn memory, and orchestration.
- Any authority: files, shell, Git, network, workspace, MCP roots/resources.

### Preserved properties

- Outcome-aware diagnostics stay visible and indexed; a failed record never aborts
  the package and never vanishes.
- Source provenance is exact (`doc_id`, code-point `offset`, `length`) and
  survives into the output.
- Threat model unchanged: fresh disposable worker per call, 5000 ms deadline,
  size limits, static policy, no widened authority. A prompt-injection string
  inside a document is inert data in Genia and is only text to the client.

## 5. Feature maturity

- [ ] Experimental
- [ ] Partial
- [ ] Stable
- [x] N/A -- process/docs-only (this step)

Child issues must describe the example as using **Experimental** R12 `chunk/2`
plus ordinary functions on the **Python reference host only**. It is not a
retrieval-augmented-generation feature.

## 3a. Portability analysis

- **Portability zone:** process-only for this step. A future example is
  host-only, because it runs through the Python-only MCP.
- **Core IR impact:** none.
- **Capability categories affected:** none changed. No capability is added,
  provisioned, or widened. The existing MCP execution profile is unchanged.
- **Shared spec impact:** none. A future example is not portable semantics and
  must not add shared-spec cases or capability claims.
- **Python reference host impact:** none now. A future example is run by the
  existing `genia_run`; no runtime code changes.
- **Host adapter impact:** none. `apps/mcp/mcp.genia` and the host boundary are
  unchanged.
- **Future host impact:** none claimed. There is no C++ MCP; the example must not
  imply cross-host parity.

## 6. Contract vs implementation

- **Portable contract:** none added.
- **Python implementation today:** `chunk/2`, validation helpers, `json_encode`,
  and `genia_run` exist and are unchanged. The showcase program does not exist.
- **C++ implementation today:** none for MCP.
- **Not implemented by this issue:** the example program, its tests, any
  `docs/mcp/demo.md` section, any retrieval/embedding/model call under MCP.

## 7. Test strategy (for child issues, not this step)

- **Core invariants:** the program uses only reachable, public ordinary
  facilities; output is byte-identical across runs; every evidence span equals
  `text[offset:offset+length]` in code points; invalid documents yield indexed
  diagnostics.
- **Expected behavior:** valid documents appear in evidence with provenance;
  invalid ones appear only in diagnostics.
- **Failure cases:** empty corpus; zero-chunk document; duplicate document ids;
  non-ASCII text (code points vs bytes); oversize input (`input_limit`); a document
  containing text that resembles protocol messages or instructions (stays data).
- **Shared spec approach:** N/A; the example is host-only and not portable.
- **Host-specific approach:** run the checked-in program both through the CLI and
  through the real MCP `genia_run` path (extending the pattern in
  `tests/unit/test_r28_mcp_demo.py`), and assert the example avoids denied
  authorities and private underscore functions.

## 8. Examples

- **Minimal:** one valid and one invalid document, one question, one chunk each.
- **Realistic:** four documents with one malformed and one that yields no chunk,
  mirroring `examples/mcp/validated_records.genia`.
- **Classification:** host-only (Python reference host via MCP). Not portable.

## 9. Complexity check

- [ ] Adding necessary complexity
- [x] Revealing existing structure
- [ ] No implementation complexity

**Justification:** the showcase composes existing facilities and adds none. The
simpler alternative, docs-only prose, was rejected because it would assert behavior
without executable evidence. The richer alternative, an R12-style provider-backed
RAG demo over MCP, was rejected because it requires provisioning providers and
credentials, which R28 deliberately denies.

## 10. Cross-file impact

Likely files for **this step:** this document and `docs/strategy/roadmap/r25-r29.md`
(pointer and decision only).

Likely files for **child issues:** `examples/mcp/` (one program), a focused unit
test, `docs/mcp/demo.md`, and later `GENIA_STATE.md` / `docs/releases/R28.md` only
once an example is implemented and verified.

**Drift risk:**

- [ ] Low
- [x] Medium
- [ ] High

**Required synchronization now:** none to `GENIA_STATE.md`, `docs/mcp/reference.md`,
`docs/releases/R28.md`, or `README.md`; nothing implemented changed. Do not edit
them in this step.

## 11. Philosophy check

- **Preserves minimalism:** YES. No new surface.
- **Avoids hidden behavior:** YES. Boundary and non-claims are explicit.
- **Keeps semantics out of host adapters:** YES.
- **Aligns with pattern-matching-first design:** YES.
- **Strengthens the Outcome-aware validated-data-pipeline priority:** YES. It is
  the same messy-records-in, validated-shaped-output-plus-diagnostics workflow,
  extended with exact provenance.

**Core Surface Freeze check:** reinforces value templates (R12 chunk/provenance
shapes) and canonical patterns (pipeline, Outcome); reduces ambiguity by stating
which stages are provider-backed and unavailable; introduces no second way to
express an existing concept.

## 12. Prompt plan and child-issue split

- [x] Pre-flight
- [ ] Contract
- [ ] Design
- [ ] Failing tests
- [ ] Implementation
- [x] Documentation (pointer only)
- [ ] Audit
- [ ] Distillation

This issue stops at pre-flight. Contract, design, tests, implementation, docs
sync, and audit are **not** performed here and a later phase must not begin
without being asked. The decision is **split into child issues**; they are
*recommended* below and have **not** been created.

| Child | Phase | Deliverable | Gate |
|---|---|---|---|
| A | Contract + design | Exact input shape, program shape, output channel (rendered value vs `json_encode` on stdout), selection function decision, diagnostics shape, and exact non-claims. | Must state `meta` handling given `<represented>` rendering; must reject private-function dependence. |
| B | Failing tests | Tests in section 7, committed failing before the program exists. | Must run through real MCP `genia_run`. |
| C | Implementation | One `examples/mcp/` program; no runtime change. | Must reference the failing-test commit SHA; any need for runtime change stops the work and returns to pre-flight. |
| D | Docs sync | `docs/mcp/demo.md` section, roadmap status, and `GENIA_STATE.md` / release note only if verified. | Must label Python-host-only, Experimental, and not RAG/generation. |
| E | Audit | Skeptical truth review incl. overclaim and authority scan. | PASS required before merge. |

**Stop conditions (return to NO-GO):** any child needs a new builtin, provider,
import path, MCP tool/field/resource, authority, parser/evaluator/Core IR change,
or reliance on a private host function.

## 13. Host parity / conformance

- **Affected hosts:** none changed (Python MCP only; no C++ MCP).
- **Does this change portable semantics?** NO.
- **Can one host merge before the other?** N/A.
- **Temporary compatibility note:** N/A. No `spec/known_host_gaps.json` entry is
  required.

## 14. Final GO / NO-GO

**GO** for the narrow tested executable example described in sections 4 and 12,
delivered through unchanged `genia_run`, and only via the child issues above.

**NO-GO** for: provider-backed retrieval, embedding, reranking, or generation under
MCP; any Genia MCP client or agent orchestration; any new authority, builtin,
syntax, or Core IR; `rag_chat`; and any documentation stating the showcase exists.

**Missing decisions (owned by child A):** output channel; whether selection is
included; chunker policy; duplicate-id handling.

**Reviewer / decision date:** repository owner to confirm; recorded 2026-10-06.
