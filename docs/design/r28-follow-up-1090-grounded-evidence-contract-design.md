# contract/design: R28 MCP grounded-evidence example (#1090)

Status: **Approved contract/design candidate for issue #1090, 2026-10-06.**
This document fixes the contract and design for one future executable example
only. It implements nothing: no runtime, MCP, language, host, test, example, or
implemented-behavior documentation changes land here.

`GENIA_STATE.md` remains final authority for implemented behavior.

## 1. Scope lock

**Includes:**

- Define the output contract for one future `examples/mcp/` grounded-evidence
  example run through the unchanged `genia_run` tool.
- Decide the machine-readable output channel, evidence package shape, ordinary
  selection step, chunking policy, duplicate-id handling, diagnostics, and
  non-claims.
- Preserve the R28 MCP threat model and the R12 provenance/Outcome vocabulary
  without adding an MCP tool, resource, field, authority, provider, builtin, or
  language construct.

**Excludes:** implementation of the example; tests; docs that claim implemented
behavior; provider-backed embedding, indexing, retrieval, reranking, or model
generation under MCP; `import`; private underscore-prefixed host functions;
filesystem, network, environment, shell, secret, config, stdin, or MCP-root
authority; parser/evaluator/Core IR changes; C++ or portable-host claims.

## 2. Source of truth

- `GENIA_STATE.md`: final authority for implemented behavior, host maturity,
  R12 retrieval/grounding, and R28 MCP.
- `GENIA_RULES.md`: Outcome, function resolution, protection, and no-hidden-
  authority invariants.
- `docs/design/r28-follow-up-1087-grounded-showcase-preflight.md`: parent
  pre-flight and scope decision.
- `docs/design/r28-genia-mcp-contract-threat-model.md`: unchanged R28 security
  boundary.
- `docs/design/r12-retrieval-grounding-contract.md`: chunk/provenance shapes and
  the distinction between ordinary pure composition and provider-backed
  retrieval.
- `docs/mcp/demo.md` and `examples/mcp/validated_records.genia`: existing MCP
  demo pattern for self-contained examples and channel separation.

## 3. Decision summary

| Question | Decision |
|---|---|
| Output channel | Emit exactly one strict JSON object to `stdout` via `json_encode`. Clients consume `stdout`, not `value.rendered`, for machine-readable evidence. |
| Final value | The final expression may return the same ordinary package for human/debug rendering, but tests must not parse `value.rendered` as the contract. |
| Selection | Include one deterministic ordinary lexical selection step named and documented as application code, **not** R12 `retrieve/4`, semantic retrieval, reranking, or ranking quality. |
| Chunking | Use `chunk/2` with an inline deterministic chunker. Offsets and lengths are Unicode code points, inherited from `chunk/2`. |
| Metadata | Preserve R12 represented metadata inside `chunk/2`; emit only JSON-domain metadata copied from the original validated input in the stdout package. |
| Duplicate ids | Keep the first valid document for a non-empty id; later valid documents with the same id are excluded and reported with indexed diagnostics. |
| Diagnostics | Return indexed JSON diagnostics in the package; malformed records and data-level failures do not become MCP protocol failures. |
| Maturity | Host-only Python MCP example, Experimental R12 `chunk/2`; not portable semantics and not implemented by this issue. |

## 4. External contract

The future example is submitted as the `source` string of one unchanged
`genia_run` call. The source contains the program plus the client-supplied
question and candidate documents as literals. The R28 envelope remains unchanged.

Successful execution returns the ordinary R28 `completed` result with:

- `exit_code: 0`;
- `stderr: ""` unless the future example deliberately documents data-level
  warnings there;
- `stdout`: exactly one strict JSON object plus the newline produced by
  `print`/`writeln`;
- `value.rendered`: debug/human rendering only.

The JSON object emitted on `stdout` has this closed shape:

```json
{
  "version": 1,
  "status": "ok",
  "question": "string",
  "selection": {
    "method": "exact_term_overlap",
    "claim": "ordinary_example_selection_not_r12_retrieve"
  },
  "evidence": [
    {
      "doc_id": "string",
      "doc_index": 0,
      "chunk_index": 0,
      "text": "string",
      "source": {
        "doc_id": "string",
        "offset": 0,
        "length": 1
      },
      "meta": {},
      "score": 1,
      "matched_terms": ["string"]
    }
  ],
  "sources": [
    {
      "doc_id": "string",
      "doc_index": 0,
      "meta": {},
      "evidence_indices": [0]
    }
  ],
  "diagnostics": [
    {
      "index": 1,
      "doc_id": "string",
      "stage": "validation",
      "reason": "duplicate_doc_id",
      "message": "duplicate document id",
      "context": {
        "first_index": 0
      }
    }
  ]
}
```

All emitted values must be strict JSON-domain values: strings, numbers, booleans,
null, arrays, and objects. The stdout contract must not emit Genia symbols,
Outcome constructors, represented values, protected values, opaque handles, or
debug-rendered fragments such as `<represented>`.

`status` is `"ok"` when the program produced a package, including packages with
empty evidence or validation diagnostics. A future implementation may use
`"error"` only for data-level input failure that the example handles inside the
JSON package; it must not invent a new MCP error kind.

## 5. Input model

The example input is ordinary literal data inside the submitted source:

```text
question = "..."
documents = [
  {id: "doc-a", text: "...", meta: {title: "...", url: "..."}}
]
```

Accepted document literals are closed maps with exactly:

- `id`: non-empty string;
- `text`: string;
- `meta`: JSON-domain object.

`meta` is client-asserted data. It may help the client render sources, but Genia
does not verify the document's origin, URL, title, freshness, ownership, or
authority. The future example must construct the R12 `document.meta` represented
JSON object needed by `chunk/2` from this ordinary metadata, while retaining the
ordinary metadata for stdout JSON output.

## 6. Validation and duplicate policy

The program validates every candidate document before chunking. Invalid records
produce indexed diagnostics and do not produce evidence. Diagnostics are stable
ordinary JSON objects, not raw `collect_validated` debug output.

Closed diagnostic fields:

| Field | Meaning |
|---|---|
| `index` | Zero-based index in the original `documents` list. |
| `doc_id` | The supplied id when present and a string; otherwise `null`. |
| `stage` | One of `validation`, `deduplication`, `chunking`, or `selection`. |
| `reason` | Stable reason string. |
| `message` | Short human-readable message. |
| `context` | JSON object with reason-specific non-sensitive details. |

Initial reason strings for the example:

| Reason | Stage | Meaning |
|---|---|---|
| `invalid_document` | `validation` | Record is not the required closed shape. |
| `empty_doc_id` | `validation` | `id` is empty. |
| `invalid_meta` | `validation` | `meta` is not a JSON-domain object. |
| `duplicate_doc_id` | `deduplication` | A valid earlier document already used this id. |
| `chunk_failed` | `chunking` | `chunk/2` returned an `err(...)` for this valid document. |
| `no_chunks` | `chunking` | A valid document produced zero chunks. |
| `no_matching_evidence` | `selection` | Selection found no chunk with positive overlap. |

Duplicate handling is first-valid-wins. The first valid document with an id may
produce chunks. Later valid documents with the same id are excluded before
chunking and receive `duplicate_doc_id` diagnostics with
`context.first_index`.

## 7. Chunking design

The future example uses `chunk/2` because that is the implemented R12 public
surface reachable under `genia_run`. The chunker is defined inline in the
program. It is deterministic and application-owned; it is not a new builtin.

The implementation phase should choose the smallest chunker that is easy to
test through MCP. Acceptable chunkers include:

- a fixed-span chunker for the checked-in example literals;
- a paragraph or line chunker if it can compute valid code-point spans using
  implemented public functions.

Whichever shape child issue C implements, these invariants are mandatory:

- spans are `{offset, length}` only;
- offsets and lengths are Unicode code points, not bytes;
- `chunk/2` owns text slicing, source construction, metadata preservation, and
  span validation;
- zero chunks are valid data and produce a `no_chunks` diagnostic;
- chunk failures are surfaced as diagnostics, not silently discarded.

## 8. Selection design

The example includes a small pure selection pass so the package demonstrates a
grounded-evidence workflow rather than dumping every chunk. It is ordinary
application code and must be named without using `retrieve`, `rerank`, `rank`,
`semantic`, `embedding`, or `vector`.

The selected method is `exact_term_overlap`:

- normalize the question and chunk text with the same implemented string
  helpers available to the example;
- derive query terms from the question;
- assign each chunk an integer `score` equal to the count of distinct query
  terms present in the chunk text;
- keep chunks with `score > 0`;
- sort by descending `score`, then original document index, then original chunk
  index.

This is not R12 retrieval. It is not semantic retrieval, vector search,
reranking, ranking quality, citation validation, answer generation, or evidence
authenticity. The future docs and tests must use that wording or an equally
explicit equivalent.

## 9. Evidence and source derivation

Each evidence item is built from a valid chunk plus the retained ordinary input
metadata:

- `doc_id` and `source.doc_id` are identical;
- `text` equals the exact chunk text produced by `chunk/2`;
- `source.offset` and `source.length` are copied from the chunk source;
- `meta` is the original ordinary JSON-domain metadata for that document;
- `score` and `matched_terms` come only from the example selection pass.

`sources` is derived from evidence order. It uses first occurrence by `doc_id`,
not by URL/title metadata, because ids are the only provenance keys controlled by
the example. `evidence_indices` are zero-based indices into the emitted
`evidence` array.

## 10. Non-claims

The future example and docs must not claim or imply:

- a new MCP tool, resource, field, prompt, transport, authority, or error kind;
- provider-backed `embed/4`, `index/4`, `retrieve/4`, `rerank/4`, or `model/4`
  under MCP;
- RAG, semantic retrieval, vector search, reranking quality, citation validation,
  or answer generation by Genia;
- verified source authenticity, URL freshness, ownership, or trust;
- portability to C++ or another host;
- implemented behavior before child issues B through E land.

## 11. Child issue gates

- **#1091 failing tests:** add focused failing tests for stdout JSON shape,
  invalid-document diagnostics, duplicate-id handling, deterministic selection,
  Unicode code-point provenance, no `<represented>` in stdout, and denial of
  forbidden names.
- **#1092 implementation:** add exactly one self-contained
  `examples/mcp/` program using only public facilities allowed by R28
  `genia_run`; no runtime change.
- **#1093 docs sync:** document the example only after tests and implementation
  pass. Keep it labeled host-only, Experimental, ordinary selection, not RAG.
- **#1094 skeptical audit:** verify no private host functions, imports, denied
  authorities, widened MCP surface, stale implemented-behavior claims, or
  overclaiming phrases slipped in.

Do not proceed to implementation from this document without the failing-test
phase.

## 12. Stop conditions

Return to NO-GO if implementation requires any of:

- new builtin, provider, import path, MCP tool, MCP resource, MCP field, or MCP
  error kind;
- parser, evaluator, Core IR, shared-spec, or host-adapter behavior change;
- private underscore-prefixed host function;
- filesystem, shell, Git, network, environment, config, secret, stdin, or MCP-root
  authority;
- parsing `value.rendered` as a machine contract;
- claiming C++ or portable-host behavior.
