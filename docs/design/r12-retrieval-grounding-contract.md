# R12 Retrieval & Grounding Contract

Status: **Approved contract; E12-1 through E12-9 complete. Implemented APIs remain Experimental; E12-8 is documentation verification and E12-9 is audit/distillation only.**

This document fixes the semantic boundary for later R12 tickets. It does not
define current language behavior and must not be cited as implementation
authority. `GENIA_STATE.md` remains final authority.

## Purpose

R12 makes retrieval and grounding ordinary Genia composition. Documents,
chunks, embeddings, retrieved evidence, grounded context, and grounded answers
are closed ordinary values. Embedding, indexing, retrieval, and provider-backed
reranking are explicit Outcome-producing callables over opaque host
capabilities. Grounded content feeds the unchanged R11 `model/4` boundary.

R12 adds no RAG object model, vector-store ownership, provider registry, second
pipeline, autonomous executor, hidden memory, implicit configuration, syntax,
annotation, lifecycle behavior, or Core IR node.

## Public surface

The complete candidate R12 runtime surface is five ordinary functions:

```text
chunk(chunker, document) -> some([chunk, ...]) | err(reason, context)

embed(provider, config, credential, authority) -> callable_embedder
callable_embedder(embedding_input)
  -> some(embedded_chunk | query_embedding) | err(reason, context)

index(provider, config, credential, authority) -> callable_indexer
callable_indexer([embedded_chunk, ...])
  -> some(index_handle) | err(reason, context)

retrieve(provider, config, credential, authority) -> callable_retriever
callable_retriever(index_handle, query_embedding, k)
  -> some([retrieved_chunk, ...])
   | none("retrieval-no-results")
   | err(reason, context)

rerank(provider, config, credential, authority) -> callable_reranker
callable_reranker(query, [retrieved_chunk, ...])
  -> some([retrieved_chunk, ...]) | err(reason, context)
```

Constructors validate and capture arguments without declassification or a
provider attempt. The `provider` is one opaque concern-specific host
capability. The `credential` is exactly one R10 protected string secret. The
authority must match its configuration-provider identity and the exact purpose
`quote(embed_call)`, `quote(index_call)`, `quote(retrieve_call)`, or
`quote(rerank_call)`.

Exact closed configurations are:

```text
embed config    = {id: non_empty_string, space: non_empty_string,
                   timeout_ms: integer_in_1_through_300000}
index config    = {id: non_empty_string,
                   timeout_ms: integer_in_1_through_300000}
retrieve config = {id: non_empty_string,
                   timeout_ms: integer_in_1_through_300000}
rerank config   = {id: non_empty_string,
                   timeout_ms: integer_in_1_through_300000}
```

`space` is an application-supplied compatibility label for an embedding model,
version, and vector interpretation. It is not inferred from vector length and
does not expose provider identity. Replacing an embedder is contract-compatible
only when the application deliberately retains the same space because the new
embedder produces compatible vectors; otherwise the corpus must be re-embedded
and re-indexed under a new space.

The provider capability factory is host API, not a Genia function. Rejected
public APIs include `VectorStore`, `VectorDatabase`, `Retriever`, `Embedder`,
`Indexer`, `Reranker`, `RAGChain`, `RetrievalQA`, provider/backend classes,
provider registries, persistence APIs, method-style `similarity_search`,
retrieval-specific pipe operators, implicit query embedding, and a second
model/generation entry point.

Grounded-context and answer assembly are application/library functions over the
closed shapes below. They are not new provider boundaries or required builtins.

## Exact ordinary values

All maps below are closed. Missing or extra keys are invalid at the relevant
boundary. Lists preserve order. Integers exclude booleans. Numbers exclude
booleans and must be finite.

### Document, span, chunk, and provenance

```text
document = {
  id: non_empty_string,
  text: string,
  meta: json_represented_object
}

chunk_span = {
  offset: non_negative_integer,
  length: positive_integer
}

chunk_source = {
  doc_id: non_empty_string,
  offset: non_negative_integer,
  length: positive_integer
}

chunk = {
  text: non_empty_string,
  source: chunk_source,
  meta: json_represented_object
}
```

`json_represented_object` is an ordinary JSON object under exactly one outer R9
`json` representation. An empty represented object is the no-metadata value.
Metadata may contain only the existing R9 JSON domain.

Offsets and lengths count Unicode code points in `document.text`, not bytes.
For every chunk, `source.doc_id == document.id` and `chunk.text` equals exactly
`document.text[offset:offset+length]`. A span must lie wholly within the text.

The chunker callable contract is exact:

```text
chunker(document.text) -> [chunk_span, ...]
```

`chunk/2` validates the document, invokes `chunker` exactly once, validates the
returned list and every span, computes chunk text and `chunk_source`, and copies
the exact `document.meta` represented value to every chunk. The chunker cannot
set text, document identity, source, or metadata. R12 defines no automatic
metadata augmentation or merge. Applications that need enriched metadata must
construct a new valid document explicitly before chunking.

Returned span order is chunk order. Overlap and repeated spans are permitted;
reordering is not. An empty document can produce only an empty span list.
Any document may validly produce zero chunks, returning `some([])`.

Malformed document shape or a non-callable chunker is runtime misuse. A chunker
exception or non-list result is callback-contract runtime misuse. A malformed or
out-of-bounds span returns:

```text
err("chunk-invalid", {stage: quote(span), index: non_negative_integer})
```

No provider, credential, authority, or declassification participates in
`chunk/2`.

### Unified corpus/query embedding input

Queries never fabricate chunk provenance. The embedder accepts exactly one of:

```text
embedding_input =
  {kind: quote(chunk), chunk: chunk}
  | {kind: quote(query), text: non_empty_string}
```

The output variant corresponds to the input variant:

```text
embedding = {
  vector: [finite_number, ...],
  dims: positive_integer,
  space: non_empty_string
}

embedded_chunk = {chunk: chunk, embedding: embedding}
query_embedding = {text: non_empty_string, embedding: embedding}
```

The vector is non-empty, `dims` equals its exact length, and `space` equals the
constructor configuration's exact `space`. The returned `embedded_chunk.chunk`
or `query_embedding.text` must equal the input exactly. Provider responses
cannot replace either value.

### Index handle and retrieved chunk

An `index_handle` is opaque, host-produced, and source cannot construct,
inspect, compare, use as a key, serialize, or persist it. Diagnostic rendering
is the fixed non-sensitive string `<index-handle>`. Internally it retains:

- the exact retrieval-capability compatibility identity established by the
  indexing capability;
- the exact embedding `space` and `dims` of the indexed corpus.

Those fields are portable obligations but not source-visible data. A handle is
valid only with its matching retrieval capability. The indexing and retrieval
capabilities for one backend may be distinct objects, but the host must create
them with one exact shared compatibility identity.

```text
retrieved_chunk = {chunk: chunk, score: finite_number}
```

The list order, not score magnitude or direction, is the authoritative
best-first retrieval order. Ties retain provider order. Scores are opaque
backend-native relevance observations: R12 defines no range, direction,
normalization, threshold, or comparability across backends.

### Grounded context and answer

```text
grounded_context = {
  question: non_empty_string,
  content: r11_content,
  evidence: [retrieved_chunk, ...]
}

grounded_answer = {
  answer: r11_content,
  sources: [chunk_source, ...],
  evidence: [retrieved_chunk, ...]
}
```

Grounded-context assembly is pure data assembly and makes no embedding,
indexing, retrieval, reranking, model, or other provider attempt. Evidence
order is exact retrieval/reranking order. Grounded-answer assembly preserves
the exact evidence list from its context. `sources` is derived in evidence
order and removes later exact-equal `chunk_source` duplicates, retaining the
first occurrence.

`content` and `answer` reuse the exact R11 content variants. Final generation is
one unmodified R11 `model/4` invocation; a grounded answer can be assembled only
from its successful `some(response)` and the exact context that produced the
request.

R12 standardizes this provenance/evidence substrate only. Citation labels,
indices, spans in generated prose, citation validation, and citation rendering
are explicitly excluded. Applications may render citations from `sources` and
`evidence` with ordinary functions.

## Call semantics

Each provider-backed callable independently:

1. validates all closed inputs locally;
2. checks locally available vector, compatibility, handle, and bound rules;
3. translates ordinary values into private host adapter values;
4. immediately before its one attempt, declassifies the captured credential
   with the captured concern-specific authority;
5. makes exactly one synchronous attempt under the configured finite timeout;
6. normalizes the observation to an existing Outcome while discarding provider
   bodies, exception text, headers, request IDs, credentials, and provider
   identity.

Construction makes no attempt and no declassification audit event. Invocation
validation, compatibility, empty-input, authority, or declassification failure
makes no attempt. There is no retry, fallback, race, stream, background task,
queue, sleep, or cache. Invocations retain no history.

### Embedding

The embedder processes one input in one attempt. A malformed chunk in a valid
chunk input returns `chunk-invalid` before declassification. Invalid normalized
vector, dimensions, space, or replacement of input text/chunk returns
`embed-response-invalid`.

### Indexing

The indexer accepts a non-empty list of `embedded_chunk` values. Empty input is
runtime misuse and makes no attempt. Every vector must be valid, every chunk
valid, and all embeddings must have exact-equal `space` and `dims`. A mismatch
is a recoverable local error before declassification. One invocation creates
one handle through exactly one provider attempt; host-internal batching is not
portable behavior.

### Retrieval

`k` must be an integer in `1..1000`; otherwise invocation is runtime misuse.
The retriever validates the query embedding, checks handle/capability identity,
then checks exact `space` and `dims` compatibility before declassification.

A valid normalized empty provider result is
`none("retrieval-no-results")`. It is absence, not failure. A non-empty success
contains at most `k` retrieved chunks in provider best-first order. Each chunk
must be valid and each score finite. Retrieval cannot alter indexed chunk text,
source, or metadata; a backend result that cannot be traced to an exact indexed
chunk is invalid.

### Reranking

`rerank/4` always means provider-backed reranking with the full R10/R11-style
capability boundary. A pure local reranker is an ordinary application/library
function with any explicit name other than `rerank/4`; it needs no capability,
credential, authority, provider semantics, or new public runtime API.

For an empty valid input list, the provider-backed callable returns `some([])`
without declassification or an attempt. For non-empty input it makes one
attempt. A successful output must contain exactly the same multiset of exact
chunk values as the input, once per input occurrence. It may reorder entries
and replace each score with a finite reranker-native score. It may not add,
drop, duplicate, mutate, or replace a chunk or provenance. Output order is
authoritative and score values have no cross-reranker comparability guarantee.

## Outcomes and errors

Runtime misuse includes malformed top-level public shapes, extra/missing map
keys, invalid constructor config, non-callable values, invalid `k`, empty index
input, forged host capabilities/handles, protected ordinary request fields,
unsupported host values, authority mismatch, and callback contract violations.
It is not converted to an Outcome and makes no provider attempt when locally
detectable.

Recoverable results are exact:

| Observation | Result |
|---|---|
| valid embed/index/retrieve/rerank result | `some(result)` |
| valid empty retrieval result | `none("retrieval-no-results")` |
| malformed chunk at an R12 data boundary | `err("chunk-invalid", {stage})` |
| invalid embedding value/vector | `err("embedding-invalid", {stage})` |
| mixed index dimensions/spaces | `err("index-embedding-incompatible", {kind})` |
| handle/capability mismatch | `err("retrieve-capability-incompatible", {kind: quote(index_handle)})` |
| query/index dimension or space mismatch | `err("retrieve-embedding-incompatible", {kind})` |
| malformed reranker result | `err("rerank-response-invalid", {stage: quote(result)})` |
| concern timeout | `err("<concern>-timeout", {timeout_ms})` |
| concern rate limit | `err("<concern>-rate-limited", {retry_after_ms})` |
| provider rejection | `err("<concern>-rejected", {kind})` |
| transport/availability failure | `err("<concern>-transport-failure", {kind})` |
| malformed normalized provider response | `err("<concern>-response-invalid", {stage})` |

`<concern>` is exactly `embed`, `index`, `retrieve`, or `rerank`.

Exact contexts are:

- `chunk-invalid`: `{stage: quote(document) | quote(span) | quote(provider_response)}`;
  the `chunk/2` span form additionally includes `index` as stated above.
- `embedding-invalid`: `{stage: quote(vector) | quote(dims) | quote(space)}`.
- compatibility `{kind}`: `quote(dimension) | quote(space)` except the fixed
  index-handle kind shown in the table.
- timeout: `{timeout_ms: integer}`.
- rate limit: `{retry_after_ms: some(non_negative_integer)}` or
  `{retry_after_ms: none("<concern>-retry-after-unavailable")}`.
- rejection/transport `{kind}`: `quote(authentication) | quote(permission) |
  quote(policy) | quote(request) | quote(unavailable) | quote(other)`.
- response-invalid `{stage}`:
  - embed: `quote(provider_response) | quote(vector) | quote(dims) |
    quote(space) | quote(input_identity)`;
  - index: `quote(provider_response) | quote(index_handle)`;
  - retrieve: `quote(provider_response) | quote(result) | quote(chunk) |
    quote(score) | quote(limit) | quote(provenance)`;
  - rerank: `quote(provider_response) | quote(result)`.

Provider-completed no-result is absence only for retrieval. Embed, index, and
rerank empty/missing provider results are response-invalid. No error context or
runtime diagnostic retains provider bodies, exception strings, headers, request
IDs, credentials, config `id`, config `space`, or provider identity.

## R9, R10, and R11 composition

- R9 supplies the one outer `json` representation for metadata and existing
  `json_schema`/callable Templates for structural validators. R12 creates no
  second schema, nominal record type, or validator system.
- R10 supplies explicit `config_get`/`config_get_or`, `secret_get`, protected
  transport/redaction, exact concern-specific authority, just-in-time
  declassification, and audit. Credentials cannot be ambient, shared across
  concerns, or reused across purposes.
- R11 content/message/request/response shapes and `model/4` are unchanged.
  R12 adds no model variant, prompt runtime, chain executor, tool loop, or
  conversation abstraction.
- Existing Outcome propagation, ordinary functions, `|>`, list/Flow helpers,
  and application-owned `scan` remain the only composition mechanisms.

## Provider and portability boundary

| Concern | Portable contract | Opaque host capability | Python proof mechanics |
|---|---|---|---|
| chunking | exact document/span/chunk behavior | none | ordinary callable only |
| embedding | exact variants, vectors, space, Outcomes | explicit embed capability | deterministic fixture first |
| indexing | non-empty compatible corpus, opaque handle | explicit index capability | deterministic in-memory index |
| retrieval | handle/query compatibility, order, absence | explicit retrieve capability | paired in-memory retriever |
| reranking | exact evidence integrity and Outcomes | explicit provider rerank capability | deterministic fixture first |
| credentials | R10 protected value and purpose | R10 authority | just-in-time audit/declassification |
| generation | unchanged R11 values and `model/4` | existing model capability | existing fixture/provider proof |
| timeout | one synchronous finite attempt | adapter implementation | deadline and cleanup tests |

Opaque capabilities and handles are Python-only mechanics in the first proof.
SDK, HTTP, database, serialization, persistence, and storage objects remain
private. The local/in-memory backend must implement the same capability
protocol; it does not create a Genia-owned vector store or persistence model.
Any hosted backend is optional, requires separate justification, and cannot
delay the portable/offline proof or broaden the contract.

Replaceability means an application retains the same ordinary call sites and
value contract when swapping a compatible injected capability. It does not mean
different embedding models, indexes, retrievers, rerankers, or generation
models return identical vectors, scores, order, evidence, or answers.

## Deterministic test obligations

Before networking, later tickets must provide deterministic offline embed,
index, retrieve, and rerank capabilities with no network, clock, randomness,
environment, filesystem, sleep, or nondeterministic ordering. Exact inputs map
to configured observations. Instrumented attempt counts and audits remain host
test data, not language values.

Shared conformance must cover, as appropriate:

- eval: closed validation, successful variants, normalization, absence/errors,
  dimensions/space, provenance, and grounding shapes;
- flow: ordered/lazy composition and bounded downstream consumption without
  hidden attempts;
- error: exact misuse diagnostics and zero-attempt local guards;
- CLI: deterministic fixture stdout/stderr/exit behavior;
- parse and IR: regression proof that all calls and shapes use existing nodes.

Python tests must cover capability/handle opacity, paired compatibility,
attempt counts, zero retries, timeouts and cleanup, validation order, R10
declassification timing/audit, input/request disposal, provenance integrity,
and recursive leak scanning. Generated sentinel keys and payloads must be absent
from stdout, stderr, exceptions, Outcomes, diagnostics, rendering, reports,
provider observations, audits, buffers, resources, and test output.

The composability matrix records R12 relationships. E12-1 implements `chunk/2`,
E12-2 implements `embed/4`, E12-3 implements `index/4` plus its opaque handle,
E12-4 implements `retrieve/4`, E12-5 implements `rerank/4`, and E12-6 implements the ordinary application-owned grounded context/answer module without adding a Template/representation/matcher-family builtin. Their
classified executable coverage and `docs/releases/R12.md` examples describe
only landed boundaries; later planned examples must not appear as implemented.

## Reconciled release sequence

Each behavior issue runs its own complete phase workflow. Issue bodies must be
written from this contract rather than copied from the earlier proposal.

1. **E12-1 — document/chunk/provenance:** exact closed values, span-owned
   `chunk/2`, R9 metadata validation, deterministic local proof.
2. **E12-2 — unified corpus/query embedding fixture:** `embed/4`, both explicit
   input/output variants, vector/space validation, deterministic capability.
3. **E12-3 — indexing capability and opaque handle:** non-empty compatible
   inputs, paired backend marker, deterministic in-memory index.
4. **E12-4 — retrieval capability:** explicit query embedding, `k`,
   compatibility guards, best-first order, no-results absence.
5. **E12-5 — provider reranking and provenance integrity:** `rerank/4`, empty
   short path, exact evidence multiset; pure local reranking remains ordinary
   application/library code.
6. **E12-6 — grounded context/answer composition with R11:** provenance/evidence
   substrate, first-occurrence source deduplication, unchanged `model/4`, no
   standardized citation rendering.
7. **E12-7 — R10 boundary, cross-mode conformance, and proving case:**
   concern-specific credentials, timeout/cleanup/leak hardening, local backend
   replacement proof, shared categories, validated-pipeline grounded example.
8. **E12-8 — release examples and implemented-truth synchronization:** update
   canonical/public docs only for landed behavior and add executable R12 release
   examples; no runtime behavior.
9. **E12-9 — release truth audit and distillation (complete):** release-wide
   evidence, status reconciliation, and distillation; no runtime behavior.

## Non-goals

- LangChain/LlamaIndex reproduction, vector-database ownership, persistence,
  provider marketplace, or backend class hierarchy.
- Agents, planners, tools, autonomous/hidden loops, or persistent memory.
- Query rewriting/expansion, multi-hop/iterative retrieval, fusion, caching,
  cost accounting, or an observability/evaluation platform.
- Streaming, cancellation APIs, retry/backoff/jitter, fallback, racing,
  queueing, background tasks, or idempotency guarantees.
- Provider score normalization, identical replacement results, citation
  rendering/validation, or generated-prose citation semantics.
- Syntax, annotations, parser/AST/Core IR/lifecycle changes.

## Gate

Issue #641 approved this contract and stopped after the contract phase. Issues
#643 through #647 completed E12-1 through E12-5 through their own phase gates.
Issues #643 through #651 completed E12-1 through E12-9 through separate ticket
workflows. E12-8 is documentation/executable-example verification and E12-9 is
audit/distillation; neither adds runtime behavior. R12 is release-complete, but
excluded or later-release behavior remains unimplemented.
