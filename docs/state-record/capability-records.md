# Capability and feature record

> **Non-authoritative provenance record.** This file preserves, verbatim and unedited, text that was displaced
> from `GENIA_STATE.md` during the #1099 distillation. It is audit material, not part of the truth hierarchy:
> it does not define Genia behavior, and `GENIA_STATE.md` governs. Start with the release, design, and reference
> documents; open this file only to see the exact displaced wording.
>
> Baseline: `GENIA_STATE.md` at `d401f322c692e8c3620509854065692c2605c61a`. Scope: Per-ticket runtime-capability narratives (R10-R14), R20 open-function narrative, and ticket-tagged pattern/Template blocks.
> Ledger: `docs/analysis/state-distillation-migration-map.json`.

## B028: baseline lines 579-593

Moved from GENIA_STATE.md@d401f322, lines 579-593 (ledger row B028, retained-condensed, sha256 329cd5200fbe058a)

~~~~~markdown
### Runtime capability values

- Document chunking with exact provenance (Experimental, R12 E12-1, issue #643)
  - `chunk(chunker, document)` is an ordinary portable call over existing values, callables, R9 representation, and Outcomes; it adds no capability, syntax, annotation, parser/AST/Core IR/lifecycle behavior, or second pipeline
  - `document` is the exact closed map `{id: nonempty string, text: string, meta: json_represented_object}`; metadata is an ordinary existing R9 JSON-domain map beneath exactly one outer `json` representation
  - `chunker` is invoked exactly once with `document.text` and must return a list of exact closed `{offset, length}` maps; offsets are nonnegative integers, lengths are positive integers, and booleans are not integers
  - offsets and lengths count Unicode code points; each span must lie wholly within the original text, returned order is preserved, and overlapping/repeated spans are allowed
  - `chunk/2` alone constructs exact closed chunks `{text, source, meta}` from the original document; source is `{doc_id, offset, length}`, text is the exact original slice, and every chunk retains the exact represented metadata value without merge, augmentation, unwrap, or rewrap
  - valid empty span lists return `some([])`, including for nonempty documents; an empty document can produce only an empty valid span list
  - the first malformed or out-of-bounds span returns `err("chunk-invalid", {stage: quote(span), index})`; malformed document/non-callable chunker and callback exception/non-list result are runtime misuse
  - shared eval/error/Flow specs plus Python tests cover closed validation, exact construction, Unicode slicing, ordering/overlap/repetition, zero results, metadata identity, callback count, and misuse; existing parse/Core IR coverage confirms an ordinary call
  - LANGUAGE CONTRACT: the closed values, one-call callback boundary, code-point slicing, exact provenance, metadata preservation, and Outcome/misuse behavior above are the implemented portable E12-1 boundary
  - PYTHON REFERENCE HOST: the portable boundary is implemented locally with no host capability or provider attempt; shared/multi-host conformance remains Partial and no non-Python host is implemented
  - indexing, retrieval, and provider-backed reranking are implemented separately by E12-3/E12-4/E12-5; grounding, model changes, and citation rendering remain later R12 work

~~~~~

## B029: baseline lines 594-607

Moved from GENIA_STATE.md@d401f322, lines 594-607 (ledger row B029, retained-condensed, sha256 11442b53e5771309)

~~~~~markdown
- Unified corpus/query embedding fixture (Experimental, R12 E12-2, issue #644)
  - `embed(provider, config, credential, authority)` validates and captures one explicit opaque embed capability, exact closed `{id, space, timeout_ms}` config, one R10 protected credential, and one declassification authority, then returns an ordinary one-argument callable without declassification, audit, or provider attempt
  - config `id` and `space` are nonempty strings; `timeout_ms` is an integer in `1..300000` excluding booleans; missing/extra keys are runtime misuse
  - the callable accepts exactly `{kind: quote(chunk), chunk}` or `{kind: quote(query), text}`; query text is nonempty, a chunk is the exact E12-1 closed value, and protected ordinary input fields are runtime misuse
  - malformed nested chunk input returns `err("chunk-invalid", {stage: quote(document)})` before declassification or attempt; other locally detectable invalid inputs are runtime misuse and likewise make no attempt
  - a valid invocation declassifies the protected string credential just in time through the exact R10 `quote(embed_call)` authority and makes one synchronous deterministic fixture attempt under the configured finite timeout; there is no retry, fallback, batching contract, stream, cache, background work, clock, randomness, environment, filesystem, sleep, or network dependency
  - success is exactly `some({chunk: exact_input_chunk, embedding})` or `some({text: exact_input_text, embedding})` according to the input variant; queries never fabricate provenance and provider output cannot replace application-owned chunk/text identity
  - `embedding` is exactly `{vector, dims, space}`; vector is a nonempty list of finite numbers excluding booleans, dims is a positive integer excluding booleans equal to exact vector length, and space exactly equals the constructor config space
  - invalid successful provider values normalize to `err("embed-response-invalid", {stage})` with stage `provider_response|vector|dims|space|input_identity`; approved timeout/rate-limit/rejection/transport errors retain the exact R12 contexts, and provider exceptions normalize once to non-sensitive `embed-transport-failure/{kind: quote(other)}`
  - no result or diagnostic retains credentials, config id/space, provider identity, bodies, exception text, headers, or request identifiers; the fixture capability renders as `<embed-provider>` and is never ambient or source-constructible
  - LANGUAGE CONTRACT: the exact ordinary input/output variants, identity, vector/dimension/space validation, Outcome normalization, local-validation ordering, and one-attempt/no-retry boundary are portable E12-2 obligations
  - PYTHON REFERENCE HOST: one explicitly injected opaque deterministic offline fixture proves the boundary and attempt/audit instrumentation; shared/multi-host conformance remains Partial and no non-Python host or network embedding adapter is implemented
  - indexing, explicit retrieval, and provider-backed reranking are implemented separately by E12-3/E12-4/E12-5; grounding/model invocation, persistence/vector databases, implicit query embedding, and provider registries remain unimplemented R12 work

~~~~~

## B030: baseline lines 608-630

Moved from GENIA_STATE.md@d401f322, lines 608-630 (ledger row B030, retained-condensed, sha256 1faa965c40af2a95)

~~~~~markdown
- Indexing capability and opaque handle (Experimental, R12 E12-3, issue #645)
  - `index(provider, config, credential, authority)` validates and captures one explicit opaque index capability, exact closed `{id, timeout_ms}` config, one R10 protected credential, and one authority, then returns an ordinary one-argument callable without declassification, audit, or attempt
  - the callable requires a nonempty list of exact E12 embedded chunks; empty input is runtime misuse, malformed chunks/embeddings fail locally, and all vectors must have exact-equal positive `dims` and nonempty `space`
  - mixed dimensions return `err("index-embedding-incompatible", {kind: quote(dimension)})`; mixed spaces return the same reason with `quote(space)`; validation and compatibility checks precede declassification and make zero attempts
  - a valid invocation declassifies the protected string just in time through exact R10 `quote(index_call)` authority and makes one synchronous deterministic fixture attempt with no retry, fallback, stream, cache, background work, networking, or portable batching behavior
  - success returns only `some(index_handle)`; the host-produced handle retains private compatibility identity plus corpus space/dims, renders exactly `<index-handle>`, and cannot be source-constructed, inspected, compared, hashed/keyed, copied, serialized, or persisted
  - approved timeout/rate-limit/rejection/transport observations retain exact R12 contexts; malformed observations normalize to non-sensitive `index-response-invalid`, and provider exceptions normalize once to `index-transport-failure/{kind: quote(other)}`
  - LANGUAGE CONTRACT: exact config/input validation, compatibility ordering, one-attempt Outcome normalization, fixed opacity/rendering, and private compatibility obligations are portable E12-3 behavior
  - PYTHON REFERENCE HOST: one explicitly injected deterministic offline in-memory fixture proves the capability/handle boundary; shared/multi-host conformance remains Partial and no non-Python host, network index adapter, or public storage object is implemented
  - retrieval and provider-backed reranking are implemented separately by E12-4/E12-5; grounding/model invocation, persistence/vector databases, public handle inspection, and provider registries remain unimplemented R12 work

- Retrieval capability and compatibility guards (Experimental, R12 E12-4, issue #646)
  - `retrieve(provider, config, credential, authority)` validates and captures one explicit opaque retrieval capability, exact closed `{id, timeout_ms}` config, one R10 protected credential, and one authority, then returns an ordinary three-argument callable without declassification, audit, or attempt
  - the callable requires one host-produced E12-3 index handle, one exact explicit E12-2 query embedding, and non-boolean integer `k` in `1..1000`; malformed top-level values are runtime misuse and query embedding is never implicit
  - local compatibility checks run in exact handle/capability identity, embedding space, then embedding dimension order; mismatches return `retrieve-capability-incompatible/{kind: quote(index_handle)}` or `retrieve-embedding-incompatible/{kind: quote(space)|quote(dimension)}` before declassification and make zero attempts
  - a valid invocation declassifies the protected string just in time through exact R10 `quote(retrieve_call)` authority and makes one synchronous deterministic fixture attempt with no retry, fallback, stream, cache, background work, networking, or hidden query embedding
  - nonempty success returns `some([retrieved_chunk, ...])` with at most `k` exact indexed chunks, finite opaque backend-native scores, and provider best-first order; valid empty success returns exact `none("retrieval-no-results")`
  - result validation rejects malformed/over-limit/non-finite/untraceable observations with exact non-sensitive `retrieve-response-invalid` stages; approved timeout/rate-limit/rejection/transport observations retain exact R12 contexts and provider exceptions normalize once to `retrieve-transport-failure/{kind: quote(other)}`
  - the paired index/retrieve capabilities share one private compatibility identity; the opaque handle privately retains corpus space/dims, backend reference, and exact indexed chunk occurrences needed for provenance validation, none of which becomes source-visible
  - LANGUAGE CONTRACT: exact config/input/`k` validation, identity-space-dimension ordering, one-attempt Outcome normalization, ordered bounded evidence, exact indexed provenance, empty-result absence, and private compatibility obligations are portable E12-4 behavior
  - PYTHON REFERENCE HOST: one explicitly paired deterministic offline in-memory fixture proves capability/handle compatibility, attempts, audits, and provenance; shared/multi-host conformance remains Partial and no non-Python host, network retrieval adapter, vector database, or public storage API is implemented
  - provider-backed reranking is implemented separately by E12-5; grounding/model invocation, persistence/vector databases, implicit query embedding, provider registries, score normalization/thresholds, and citation rendering remain unimplemented R12 work

~~~~~

## B031: baseline lines 631-650

Moved from GENIA_STATE.md@d401f322, lines 631-650 (ledger row B031, retained-condensed, sha256 a15fc33c01786a34)

~~~~~markdown
- Provider reranking and provenance integrity (Experimental, R12 E12-5, issue #647)
  - `rerank(provider, config, credential, authority)` validates and captures one explicit opaque rerank capability, exact closed `{id, timeout_ms}` config, one R10 protected credential, and one authority, then returns an ordinary two-argument callable without declassification, audit, or attempt
  - the callable requires a nonempty query string and a list of exact E12 retrieved chunks; malformed/protected input is runtime misuse and local validation precedes declassification
  - valid empty evidence returns `some([])` with zero declassification/audit/attempt; nonempty evidence declassifies just in time through exact `quote(rerank_call)` authority and makes one synchronous deterministic fixture attempt without retry, fallback, stream, cache, background work, or networking
  - success may reorder occurrences and replace scores with finite reranker-native numbers only; it preserves the exact multiset of exact chunk values, including repeated occurrences, and therefore cannot add, drop, duplicate, replace, or mutate text/source/represented metadata provenance
  - malformed/non-preserving success returns exact non-sensitive `rerank-response-invalid/{stage: quote(result)}`; malformed observations use `quote(provider_response)`, approved rerank timeout/rate-limit/rejection/transport contexts pass through, and provider exceptions normalize once to `rerank-transport-failure/{kind: quote(other)}`
  - LANGUAGE CONTRACT: exact config/input validation, inert construction/empty short path, one-attempt Outcome normalization, finite-score replacement, authoritative output order, and exact evidence-multiset/provenance preservation are portable E12-5 obligations
  - PYTHON REFERENCE HOST: one explicitly injected deterministic offline fixture proves attempts, audits, duplicate-aware integrity, and non-leakage; shared/multi-host conformance remains Partial and no non-Python host or network rerank adapter is implemented
  - pure local rerankers remain ordinary application/library functions under other explicit names; score normalization/comparability, grounding/model invocation, citation rendering, persistence/vector databases, and provider registries remain unimplemented

- Grounded context and answer composition (Experimental, R12 E12-6, issue #648)
  - the importable `examples/r12_grounded_context_answer.genia` module defines application-owned `assemble_grounded_context/3`, `assemble_grounded_answer/2`, `grounded_request/1`, and `generate_grounded_answer/2`; these are ordinary composition functions, not new public builtins or provider boundaries
  - grounded context is the exact closed `{question, content, evidence}` shape with a nonempty unprotected question, exact R11 text/JSON content, and a list of exact finite-scored E12 retrieved chunks; assembly validates locally and makes zero provider/model attempts
  - grounded answer is the exact closed `{answer, sources, evidence}` shape; it is assembled only from an exact successful R11 `some(response)`, retains the exact context evidence list/order, and takes answer content only from `response.message.content`
  - `sources` traverses evidence in order and retains the first occurrence of each exact-equal closed `{doc_id, offset, length}` source; later exact duplicates are removed, while different spans from the same document remain distinct
  - `none(...)` and `err(...)` model Outcomes propagate unchanged and produce no grounded answer; the application-owned generation wrapper validates the exact context, constructs one existing R11 text request, and invokes its supplied unchanged model callable once
  - LANGUAGE CONTRACT: exact closed shapes, local validation, zero-attempt assembly, exact evidence preservation, ordered first-occurrence source deduplication, successful-Outcome-only answer assembly, and unchanged R11 `model/4` composition are portable E12-6 obligations
  - PYTHON REFERENCE HOST: private validation bridges and deterministic tests prove the ordinary application module; shared/multi-host conformance remains Partial and no non-Python host grounding proof is implemented
  - R12 standardizes provenance/evidence substrate only; citation labels, numbering, generated-prose citation spans/validation/rendering, prompt runtime, RAG framework objects, agents/tools/memory, and retry remain unimplemented

~~~~~

## B032: baseline lines 651-667

Moved from GENIA_STATE.md@d401f322, lines 651-667 (ledger row B032, retained-condensed, sha256 6caec68a1363597d)

~~~~~markdown
- R12 cross-mode hardening and grounded proving case (Experimental, R12 E12-7, issue #649)
  - existing E12-1 through E12-6 and unchanged R11 `model/4` boundaries are proved through explicit deterministic shared eval/Flow/error/CLI fixtures plus existing parse/Core IR forms; E12-7 adds no public function, provider semantic, syntax, or Core IR node
  - `embed_call`, `index_call`, `retrieve_call`, `rerank_call`, and `model_call` use distinct protected credentials and exact matching R10 authorities; constructors remain inert, local checks precede just-in-time declassification, and each consumed valid stage makes at most one synchronous attempt without retry, fallback, sleep, queue, race, or background work
  - bounded downstream Flow consumption is demand-driven and makes no attempt for unconsumed items; deterministic fixtures use no network, clock, randomness, environment, filesystem, or sleep
  - paired in-memory index/retrieve compatibility remains private; compatible injected capabilities keep the same ordinary call/value contracts without promising identical vectors, scores, evidence order, or answers
  - recursive tests scan results, Outcomes, rendering, audits, provider observations, buffers, resources, stdout/stderr, and test output for credential/payload sentinels
  - `examples/r12_cross_mode_grounded_proving.genia` explicitly composes validation/diagnostics, chunking, corpus/query embedding, indexing, retrieval, provider reranking, grounded context, one unchanged R11 model call, and grounded answer while retaining exact provenance
  - LANGUAGE CONTRACT: E12-7 adds cross-mode conformance evidence and an ordinary composition proof for existing R10/R11/R12 obligations only; it adds no new behavior
  - PYTHON REFERENCE HOST: the explicit offline fixture runner and instrumentation are host proof mechanics, not portable APIs; shared/multi-host conformance remains Partial and no non-Python host is implemented

- R12 release examples and implemented-truth synchronization (Experimental, R12 E12-8, issue #650)
  - E12-8 adds no runtime behavior: `docs/releases/R12.md` and focused documentation tests synchronize runnable chunking and complete grounded-composition examples with the implemented E12-1 through E12-7 boundary
  - the synchronized public account keeps ordinary values/callables/Outcomes, exact provenance, explicit query embedding, opaque index/retrieval compatibility, backend-native scores, unchanged R11 `model/4`, Python-host-only proof mechanics, and excluded citation rendering distinct
  - LANGUAGE CONTRACT: E12-8 is documentation and executable-example verification only; the implemented portable behavior remains exactly E12-1 through E12-6, while E12-7 remains conformance/proving evidence without new semantics
  - E12-9 adds no runtime behavior: its release-wide truth audit verifies the approved boundary, focused/shared/native/documentation/full-suite evidence, protected-provider exclusions, and canonical release status
  - R12 is release-complete through E12-9 while its APIs remain Experimental, shared/multi-host conformance remains Partial, and Python remains the only implemented host

~~~~~

## B033: baseline lines 668-700

Moved from GENIA_STATE.md@d401f322, lines 668-700 (ledger row B033, retained-condensed, sha256 466ca8c1fe9f8109)

~~~~~markdown
- AI model invocation, Flow conversation composition, validated-pipeline proof, release-example truth sync, and release truth audit (Experimental, R11 E11-1 through E11-8, issues #611-#618)
  - `model(provider, config, credential, authority)` is the sole public AI entry point and returns an ordinary one-argument callable
  - E11-3 adds one explicit Python-host-only Google Gemini Developer API adapter using direct `v1beta models.generateContent` REST; the deterministic fixture remains the portable-observation test path
  - `provider` is an opaque host-injected model-provider capability; ordinary source has no constructor and execution modes inject no ambient provider, credential, or authority
  - `config` is the closed map `{id: nonempty string, timeout_ms: integer 1..300000}`
  - a request is the closed map `{messages, output}` with a nonempty message list, closed text messages using `system|user|assistant` roles, and `{kind: quote(text)}` output
  - E11-2 also accepts the closed output requirement `{kind: quote(json), schema, template}`: `schema` has exactly one outer R9 `json` representation and must be accepted by existing `json_schema`; `template` is an explicit callable one-argument Outcome Template
  - construction validates its inputs without declassification, audit, or provider attempt; invocation validates the complete request before declassification or attempt
  - a valid invocation declassifies the R10 protected string credential at the authorized boundary, records the existing R10 audit, and makes exactly one synchronous provider attempt; there is no implicit retry
  - the Gemini host adapter maps `config.id` to the percent-encoded model path, `config.timeout_ms` to the one standard-library HTTPS attempt, and the declassified credential only to `x-goog-api-key`; it refuses redirects and exposes no provider factory to source, ambient binding, SDK dependency, general HTTP API, discovery, retry, or fallback
  - Gemini user/assistant messages map to `user`/`model` contents, system text maps in relative order to `systemInstruction.parts`, and structured output sends the existing represented schema as `responseJsonSchema` with `application/json`
  - success is `some({message, finish_reason, usage})`; the response is closed, its message is assistant text, finish reason is `stop|length|filtered|other`, and usage is exact nonnegative token counts or `none("model-usage-unavailable")`
  - structured success processes the single provider assistant text through existing `json_decode`, invokes the explicit Template once on the decoded carried ordinary value, ignores the Template success payload, and returns assistant content `{kind: quote(json), value: represented_value}` retaining exactly one outer `json` facet
  - decode or Template `none(...)`/`err(...)` becomes exactly `err("model-structured-output-invalid", {stage: quote(json_decode)|quote(template), outcome: original_outcome})`; a non-Outcome Template result is runtime callback misuse
  - there is no repair, trimming, prose/fence extraction, coercion, second parse, reprompt, partial acceptance, or retry
  - absence is exactly `none("model-no-response")`; normalized failures use `model-timeout`, `model-rate-limited`, `model-rejected`, `model-transport-failure`, or `model-response-invalid` with the closed contexts defined in `GENIA_RULES.md`
  - malformed provider observations become `err("model-response-invalid", {stage: quote(provider_response)})` (or the precise response stage); Gemini HTTP/transport failures normalize to the existing timeout/rate-limit/rejected/transport Outcomes without retaining raw bodies, headers other than parsed retry delay, request IDs, exception text, keys, or credentials
  - shared eval/error/Flow/CLI specs opt into the Python fixture explicitly with `fixtures: [r11_model]`; CLI fixture routing is private shared-spec harness behavior for command/file/pipe observations, while ordinary eval, file, command, pipe, import, native-test, and serve execution gain no fixture bindings
  - parse and Core IR shared specs retain the existing ordinary `Call`/`IrCall` shapes; E11-4 adds no syntax, node, execution mode, flag, annotation, lifecycle consumer, ambient capability, or retry/tool/streaming surface
  - E11-5 implements conversation as application-owned ordinary state evolution through existing `scan(step, initial_state, source)`: input is exactly `{kind: quote(message), message: {role: quote(user), content}}` or `{kind: quote(stop), reason: string}`; initial state is exactly `{messages: [], turn: 0, status: quote(active), last: none("conversation-not-started")}`
  - the application-defined step returns `[next_state, next_state]`; an active message appends the user message, calls an ordinary prompt over the full ordered history, calls the model once, increments `turn`, records the exact Outcome, and appends one assistant message only for `some(response)`; `none`/`err` sets failed status without an assistant append
  - active stop preserves history/turn, records stopped status plus `none("conversation-stopped", {reason})`, and makes no model call; stopped/failed states return unchanged for later input with no call
  - list input returns an eager state list and Flow input returns a lazy single-use Flow with equivalent consumed states; `scan` emits no initial state, and source completion or existing downstream bounds terminate consumption without a new Flow helper
  - `examples/r11_flow_conversation.genia` is the executable application composition proof; it uses existing `apply_raw` only to deliberately dispatch model Outcomes as data rather than triggering ordinary Option short-circuiting
  - conversation owns neither input acquisition nor model/provider configuration and adds no runtime object, hidden memory, retry/reprompt/tool loop, streaming, cancellation, `take_while`, syntax, annotation, or Core IR node
  - `examples/r11_validated_pipeline_proving_case.genia` is the executable E11-6 proof: mixed JSONL uses existing parsing and record validation before an ordinary structured model stage; R9 `json_schema`/represented output, explicit R10 protected credentials, and existing `validate_each`/`collect_validated` produce clean represented values plus ordered diagnostics
  - the deterministic proof attempts the model only for parse/validation successes, at most once per invocation; no-response, normalized provider failures, invalid structured output, Template mismatch, and protected-boundary failure use existing Outcomes/errors without retry, repair, reprompt, fallback, or sensitive leakage
  - E11-6 adds no helper, schema/validation system, provider behavior, syntax, annotation, or Core IR node; its shared CLI/eval/Flow/error cases and native/Python tests are conformance/proving artifacts over existing behavior
  - E11-7 adds no runtime behavior: `docs/releases/R11.md` and focused documentation tests synchronize runnable text, structured-output, Flow-conversation, and validated-pipeline examples with the implemented boundary and keep maturity, portability, and exclusions explicit
  - E11-8 adds no runtime behavior: its release-wide truth audit verifies the approved boundary, focused/shared/native/documentation/full-suite evidence, sensitive-data exclusions, and canonical release status; R11 is release-complete while its APIs remain Experimental, Python remains the only implemented host, and shared/multi-host conformance remains Partial
  - LANGUAGE CONTRACT: the ordinary closed value shapes, callable behavior, validation ordering, one-attempt rule, R9 structured composition, normalized Outcomes, explicit cross-mode boundary, application-owned list/Flow `scan` composition, and Outcome-aware validated-pipeline composition are the implemented R11 E11-1 through E11-8 portable boundary; E11-7 is documentation/executable-example verification and E11-8 is audit/distillation only
  - PYTHON REFERENCE HOST: the offline deterministic fixture and one explicitly constructed Gemini REST capability are implemented; automated adapter tests inject a fake transport and perform no network access; shared/multi-host conformance remains Partial

~~~~~

## B034: baseline lines 701-735

Moved from GENIA_STATE.md@d401f322, lines 701-735 (ledger row B034, retained-condensed, sha256 007b78b5d74582d5)

~~~~~markdown
- Configuration provider, protected acquisition/sinks, explicit declassification, cross-mode hardening, and composed validated-pipeline proving case (Experimental, issues #589-#595)
  - R10 E10-1 through E10-8 are release-complete; completion records the delivered and audited scope, while the APIs remain Experimental and shared/multi-host conformance remains Partial
  - `config_provider(sources)` constructs an explicit opaque immutable provider snapshot and returns `some(provider)` or a normalized `err(...)`
  - supported descriptors are `{kind: quote(values), values: map}` and capability-backed `{kind: quote(environment)}`
  - source order is highest to lowest precedence; the first source containing a key wins
  - all descriptors and literal string keys/values are validated before any host-backed snapshot is acquired
  - `config_get(provider, key)` returns `some(exact_string)`, including `some("")`, or context-free `none("config-missing")`
  - `config_get_or(provider, key, default)` preserves found values including empty; only `none("config-missing")` invokes the zero-argument default, exactly once
  - an ordinary default result is wrapped in `some(...)`; a default `some(...)`, `none(...)`, or `err(...)` is preserved without nesting
  - default callability/arity is checked only if missing selects the default branch; other lookup Outcomes bypass the default unchanged
  - conversion remains an explicit ordinary Outcome-returning callable, and validation reuses existing callable Templates through ordinary Outcome-aware pipelines
  - `secret_get(provider, key, purpose)` protects found exact strings, including empty, in one reserved outer `secret` carrier; purpose is a non-empty symbol
  - `secret_get_or(provider, key, purpose, default)` uses the same missing-only, exactly-once default rule; ordinary/`some` successes are protected once and `none`/`err` are preserved
  - `protected_match("secret", value)` returns `some(value)` containing the exact protected subject; ordinary/non-secret values return `none("representation-mismatch")`
  - generic `represent`, `representation_match`, and `strip_representation` reject the reserved `secret` facet
  - protected equality observes carrier identity only (R18 E18-3): a carrier equals itself and any alias of the same carrier, while independently acquired carriers are unequal even when they share a provider and purpose and carry equal payloads. Ordinary equality never compares protected payloads, so it cannot be used to test whether two secrets match; payload comparison requires explicit authorized declassification first. Protected values are not map keys
  - calls, returns, containers, pipelines, Seq, Flow, Sheet cells, refs, and process messages transport exact protected leaves; containers gain no hidden taint and unsupported ordinary derivation returns existing type failure
  - diagnostic rendering recursively substitutes `<protected>`; Format replacements, output sinks, JSON, Sheet CSV, resource writes, HTTP responses, and ordinary host conversion reject protected leaves before effects
  - `json_encode` returns `err("protected-value", {operation: "json-encode"})`; resource rejection writes zero payload bytes
  - `declassify(authority, protected_value)` is the sole payload-revealing operation; a host-injected opaque authority must match the exact provider identity and allow the protected purpose
  - successful declassification removes exactly one protected layer, returns an ordinary untainted value, and records a host-local non-sensitive audit event; mismatches reveal nothing and audit failure fails closed
  - authority displays as `<declassification-authority>`, cannot be copied or used as a map key, and is rejected by output/format/serialization/Sheet/resource/HTTP/process/ordinary-host boundaries
  - valid keys are non-empty strings without NUL; normalized diagnostics never include the key, source contents, raw value, or host exception detail
  - providers display/debug as `<config-provider>`, compare by identity, are not map keys, and are rejected by ordinary host conversion and JSON serialization
  - construction copies every source once; later literal/environment mutation is invisible and lookup performs no host access
  - ordinary eval, file, command, pipe, import, native-test, and serve-entry evaluation preserve these explicit provider/protection semantics; modes create no ambient provider or authority
  - imports acquire only when evaluated module code explicitly constructs and uses a provider; existing annotations do not acquire or inject configuration
  - the Python native-test harness accepts explicit fixture bindings and environment-capability/output test seams; it constructs no fixture provider or authority implicitly
  - serve entry evaluation and any explicit provider snapshot complete before listener activation; requests do not refresh configuration automatically
  - `examples/r10_validated_pipeline_proving_case.genia` is the executable E10-7 composition proof: explicit ordinary configuration flows through `parse_int` and callable Templates, protected acquisition/matching remains opaque, and existing `validate_each`/`collect_validated` produce clean records plus diagnostics
  - shared CLI and native Genia coverage prove the source-visible composition; Python reference-host tests inject the matching authority and fixture host callable, prove declassification immediately at that boundary, and cover mismatch, protected-sink, provider-failure, audit, and sentinel non-leak behavior
  - no ambient provider, implicit environment fallback, refresh, implicit conversion/coercion, new validation system, annotation injection, parser, or Core IR change is implemented
  - LANGUAGE CONTRACT: explicit ordering, immutable snapshot semantics, literal sources, lookup Outcomes, opacity, and normalized failures are portable
  - PYTHON REFERENCE HOST: `{kind: quote(environment)}` snapshots `os.environ` during construction; a host may report the capability unavailable rather than substitute another source

~~~~~

## B035: baseline lines 736-759

Moved from GENIA_STATE.md@d401f322, lines 736-759 (ledger row B035, retained-condensed, sha256 0911f0b2c0fd4859)

~~~~~markdown
- Qualified configuration and secret views (Experimental, issue #671)
  - R13 E13-1 adds `config_view(provider, prefix)` and `secret_view(provider, prefix, purpose)` as ordinary constructors returning one-argument callables
  - construction validates and captures the existing R10 provider and exact string prefix; secret views also validate and capture one existing non-empty R10 purpose symbol
  - an empty prefix is valid; a prefix containing NUL is runtime misuse; construction performs no lookup, source acquisition, refresh, conversion, validation, protection, declassification, audit, or host operation
  - each returned callable requires one non-empty logical-name string without NUL, forms the physical key by exact `prefix + logical_name` concatenation, and performs exactly one existing R10 lookup
  - `config_view` returns the exact `config_get` Outcome; `secret_view` returns the exact `secret_get` Outcome and preserves provider identity, purpose, protected carrier, sinks, authority, audit, and declassification behavior
  - views add no caching, fallback, precedence, defaulting, conversion, Template validation, ambient lookup, named access, syntax, annotation, parser/AST/Core IR node, lifecycle binding, or host capability
  - normalized misuse does not include the prefix, logical name, physical key, provider identity, purpose, source content/value, or protected payload
  - E13-1 itself adds no conventional provider composition; E13-4 supplies that composition, E13-5 verifies the complete implemented boundary across relevant modes, and E13-6 proves its validated-pipeline composition; release-completion slices remain unimplemented
  - LANGUAGE CONTRACT: construction/callability, validation, exact concatenation, and exact one-call R10 delegation are portable ordinary-call behavior
  - PYTHON REFERENCE HOST: the two constructors use the existing callable and R10 provider implementation; no new host capability is introduced and shared/multi-host conformance remains Partial

- Explicit CLI configuration source (Experimental, issue #672)
  - R13 E13-2 adds `config_args(args)` as an ordinary one-argument callable over an explicit plain list of strings, normally `argv()`; it never reads process arguments or interpreter mode flags itself
  - before the first standalone `--`, input is exact long-option/value pairs; names use ASCII letter-led alphanumeric segments separated by single hyphens, and values are the next exact strings, including empty or option-looking strings
  - standalone `--` terminates configuration parsing and every later string is ignored; empty and terminator-only input produce an empty values map
  - names normalize by replacing hyphens with underscores and uppercasing ASCII letters; unknown valid names are accepted, while repeated or normalization-colliding keys fail atomically
  - success is `some({kind: quote(values), values: normalized_map})`, using the existing R10 literal source descriptor shape and fresh snapshot data
  - malformed string-list data returns exactly `err("config-source-invalid", {source_kind: quote(arguments), stage: quote(parse)})`; no option spelling, argument index, value, or partial map is exposed
  - a non-list input or any non-string list member is runtime misuse; short/grouped options, flags without values, `--name=value`, underscores, non-ASCII names, and positionals before `--` are not accepted
  - E13-2 adds no schema, boolean encoding, conversion, provider construction, host acquisition capability, syntax, annotation, parser/AST/Core IR node, named access, lifecycle binding, or ambient lookup
  - LANGUAGE CONTRACT: explicit-input grammar, normalization, collision handling, descriptor/Outcome shapes, atomic failure, and snapshot behavior are portable pure ordinary-call behavior
  - PYTHON REFERENCE HOST: the ordinary callable is registered over existing runtime values; raw process arguments remain available only through the unchanged explicit `argv()` boundary and shared/multi-host conformance remains Partial

~~~~~

## B036: baseline lines 760-782

Moved from GENIA_STATE.md@d401f322, lines 760-782 (ledger row B036, retained-condensed, sha256 9c9ca5842a609bfe)

~~~~~markdown
- Narrow `.env` configuration source (Experimental, issue #673)
  - R13 E13-3 adds `{kind: quote(dotenv), path, required}` as an R10-compatible descriptor; `path` is a non-empty NUL-free string and `required` is boolean, with descriptor misuse rejected before any host acquisition
  - provider construction validates every descriptor first, then reads each `.env` path at most once in source-list order and copies parsed exact strings into the existing immutable provider snapshot; lookup never reads or refreshes the file
  - optional absence contributes an empty source at its fixed index; required absence and host read failure return `config-provider-failure`, unavailable capability returns `config-source-unavailable`, and invalid UTF-8/grammar returns `config-source-invalid`
  - `.env` failure context contains only `source_index`, `source_kind: quote(dotenv)`, and `stage: quote(acquire|decode|parse)`; paths, keys, values, content, partial providers, and raw host details do not escape
  - UTF-8 accepts one leading BOM, LF/CRLF, a final unterminated line, blank/full-comment lines, ASCII space/tab around entries, ASCII identifier keys, exact duplicate rejection, and unquoted/single-quoted/double-quoted values with only `\\`, `\"`, `\n`, `\r`, and `\t` double-quote escapes
  - empty values are present exact strings; interpolation, expansion, command substitution, multiline values, `export`, continuation, discovery, profiles/cascades, other formats, and watch/refresh are not implemented
  - existing source precedence and R10 `config_get`/`secret_get` Outcomes, protected carriers, sinks, authority, audit, and declassification remain unchanged
  - E13-3 adds no `config_standard`, conventional precedence helper, public parser, syntax, annotation, parser/AST/Core IR node, named access, lifecycle binding, or ambient lookup
  - LANGUAGE CONTRACT: descriptor validation, grammar, normalized Outcomes, fixed indices, acquisition ordering, and immutable snapshot behavior are portable
  - PYTHON REFERENCE HOST: `config.dotenv-snapshot` reads bytes from exactly the supplied path during provider construction; future hosts may report capability unavailable, and shared/multi-host conformance remains Partial

- Conventional configuration provider composition (Experimental, issue #674)
  - R13 E13-4 adds ordinary `config_standard(overrides, args)` and `config_standard(overrides, args, dotenv_path)` calls
  - the two-argument form selects optional `.env`; the three-argument form requires the exact supplied non-empty NUL-free path
  - construction normalizes explicit arguments, then delegates to the existing provider with fixed sources: overrides at index 0, arguments at 1, environment at 2, and `.env` at 3
  - fixed precedence is overrides > arguments > environment > `.env`; empty or optionally absent sources retain their indices
  - invalid explicit types/values are runtime misuse before acquisition; malformed argument syntax returns its exact non-sensitive `config-source-invalid` Outcome before environment or filesystem acquisition
  - the result is the exact existing provider Outcome; construction is atomic, snapshots once, and preserves unchanged ordinary/secret views and every R10 protected boundary
  - E13-4 adds no provider model, capability, ambient lookup/refresh, defaults source, schema/conversion, syntax, annotation, parser/AST/Core IR node, named access, or lifecycle binding
  - LANGUAGE CONTRACT: arities, validation ordering, fixed source order/indices, precedence, optional/required path policy, exact Outcomes, atomicity, and snapshot behavior are portable
  - PYTHON REFERENCE HOST: composition reuses the existing environment and `.env` snapshot capabilities; Python remains the only implemented host and shared/multi-host conformance remains Partial

~~~~~

## B037: baseline lines 783-800

Moved from GENIA_STATE.md@d401f322, lines 783-800 (ledger row B037, retained-condensed, sha256 165b89172d348c83)

~~~~~markdown
- R13 cross-mode, diagnostic, and protected-boundary hardening (Experimental, issue #675)
  - E13-5 adds conformance proof only; it adds no public helper, value, error shape, source, capability, syntax, annotation, parser/AST/Core IR node, or execution-mode behavior
  - shared eval/error/CLI cases verify explicit standard-provider construction, exact existing Outcomes, non-sensitive malformed-argument failure, command-mode behavior, and existing ordinary parse/Core IR call forms
  - Python reference-host tests verify standard sources snapshot once before view use, imports acquire only through explicit module construction, serve snapshots precede activation and requests do not refresh, and malformed explicit data prevents later host acquisition
  - credentials acquired through standard composition and `secret_view` retain exact R10 provider identity, purpose, carrier, matching authority, audit-before-return, redaction, and protected-sink behavior; successful host-local audits retain their existing non-sensitive purpose field but no protected payload or raw host detail
  - focused sentinel scans cover normalized Outcomes, misuse diagnostics, protected rendering, and host audit observations; the existing R10 recursive sink/report/resource/HTTP/ordinary-host suites remain the protection authority and pass unchanged
  - file, command, pipe, import, native-test, and serve-entry behavior remains explicit and non-ambient; the E13-5 additions do not create a provider or authority fixture visible to ordinary source
  - Python remains the only implemented host and shared/multi-host conformance remains Partial; E13-7/E13-8 release-close slices add no runtime behavior

- R13 Outcome-aware validated-pipeline proving case (Experimental, issue #676)
  - `examples/r13_validated_pipeline_proving_case.genia` is the executable E13-6 application composition proof: one conventional provider feeds distinct server, database, and metrics qualified `PORT` views through explicit `parse_int` conversion and a callable Template, while existing `validate_each`/`collect_validated` produce clean records plus ordered structured diagnostics
  - deterministic overrides, explicit arguments, environment acquisition, and one explicit `.env` snapshot exercise the existing fixed standard-provider boundary; provider construction remains atomic and snapshot-based, identically named logical settings remain unambiguous through prefixes, and missing/malformed/Template-mismatched configuration preserves existing Outcomes
  - one protected credential remains opaque in public results and is declassified at most once only as an argument to an injected authorized outbound fixture; a matching authority produces one audit event and one outbound attempt, while provider/purpose mismatch, direct protected submission, and provider failure produce no outbound attempt and leak no key, payload, source value, or raw host detail
  - shared CLI/eval/Flow/error cases, one native Genia test, and focused Python reference-host tests prove the source-visible composition, normalized failure, sentinel non-leakage, and exact protected boundary offline
  - E13-6 adds no public helper, provider/source model, validation or diagnostic behavior, protected/declassification rule, network behavior, retry/fallback, syntax, annotation, parser/AST/Core IR node, ambient lookup, or lifecycle injection
  - LANGUAGE CONTRACT: explicit qualified lookup, Outcome propagation, callable Template validation, record collection, and protected transport compose using the already implemented R10/R13 portable ordinary-call boundary
  - PYTHON REFERENCE HOST: tests inject deterministic snapshot capabilities, one matching or mismatching authority, a non-sensitive audit observer, and an outbound fixture; Python remains the only implemented host and shared/multi-host conformance remains Partial

~~~~~

## B038: baseline lines 801-821

Moved from GENIA_STATE.md@d401f322, lines 801-821 (ledger row B038, retained-condensed, sha256 58efa58cd9a509ec)

~~~~~markdown
- R13 release examples, implemented-truth synchronization, and release audit (Experimental, R13 E13-7/E13-8, issues #677/#678)
  - E13-7 adds no runtime behavior: `docs/releases/R13.md` and focused documentation tests synchronize runnable qualified-view and complete validated-pipeline examples with the implemented E13-1 through E13-6 boundary
  - the synchronized public account keeps ordinary explicit providers, callables, Outcomes, immutable snapshots, fixed source precedence, explicit conversion/callable Template validation, R10 protected transport, and Python-host-only acquisition/test mechanics distinct
  - LANGUAGE CONTRACT: E13-7 is documentation and executable-example verification only; implemented portable behavior remains exactly E13-1 through E13-4, while E13-5/E13-6 remain conformance and application-composition proof without new semantics
  - E13-8 adds no runtime behavior: its release-wide truth audit verifies the approved boundary, focused/shared/native/documentation/full-suite evidence, protected-value exclusions, and canonical release status
  - R13 is release-complete through E13-8 while its APIs remain Experimental, shared/multi-host conformance remains Partial, and Python remains the only implemented host

- R14 lifecycle instance, parent/child execution scopes, peer attachment breadth, repeated element scopes, and configuration provider binding (Experimental, issues #621, #692, #693, #694)
  - R14 E14-1 adds `lifecycle_scope(peers, work)`, `lifecycle_child(scope_handle, peers, work)`, and `lifecycle_context(scope_handle, name)` as the first implemented slice of the approved E14-0 composable-lifecycle contract (`docs/design/r14-composable-lifecycle-contract.md`)
  - a peer is an ordinary closed map `{name: symbol, enter: callable/1, exit: callable/2}`; peers on one scope operation enter in list order and unwind in strict reverse order, every entered peer's `exit` runs exactly once regardless of earlier exit failures, and the first non-cleanup failure is always the scope's one `primary_failure` while every later exit failure is preserved in `cleanup_failures`
  - `work`'s return value is carried into the closed `LifecycleResult` verbatim and is never inspected for `some`/`none`/`err`; the only way `work` produces a lifecycle failure is by raising, normalized exactly like R8 lifecycle exceptions
  - `lifecycle_child` may be called only synchronously from an active parent scope's own `work`; a child's result/failure is ordinary data returned to the parent and never implicitly raised into it, and a child's peers/resources are entirely separate from the parent's
  - `lifecycle_context` is inward-only and read-only: it checks the calling scope's own entered-peer context, then each ancestor scope in turn, and never exposes a later-attached peer's context to an earlier one; a peer name colliding with any name already exposed by an ancestor scope is rejected before any `enter` runs
  - a scope handle is valid only while its scope is `entering`/`active`/`exiting`; any later use (or `lifecycle_child` on a handle that is not `active`) raises a runtime-misuse `RuntimeError`, the same family as an already-consumed Flow
  - R14 E14-2 (issue #692) proves the same entry/work/unwind algorithm at three-or-more-peer breadth: deterministic enter/reverse-unwind order, entry failure at any position unwinding only the already-entered prefix, multiple exit failures promoting the first encountered and appending the rest in exit-call order, later-only context visibility, an `exit` `primary_summary` that never carries another peer's context, and attachment order proven independent of ancestor depth — see section 9.9. E14-2 adds no new public function or runtime behavior; `src/genia/lifecycle_runtime.py` is unchanged from E14-1
  - R14 E14-3 (issue #693) adds `lifecycle_repeat(peers, source, element_work)`: a fresh "element" scope per consumed `list` (eager, exhaustive) or `Flow` (lazy, single-use, no-over-pull) element, running the same unchanged entry/work/unwind algorithm with two reserved context names — `quote(element)` (the consumed value) and `quote(index)`, its 1-based pull ordinal — populated before any attached peer's own `enter` runs. A peer literally named `element` or `index` is rejected before any `enter`, by the same non-shadowing mechanism as ancestor context. Early Flow termination reduces to the existing Flow/source `close_on_early_termination` finalization rule — no new finalization mechanism — because each yielded `LifecycleResult` reflects an element scope already fully entered and unwound before it is yielded. See section 9.10
  - R14 E14-4 (issue #694) adds `lifecycle_config(provider) -> LifecycleDefinition`: a pure factory validating `provider` is an already-constructed `GeniaConfigProvider` and returning one ordinary peer reserved under `name: quote(config)`, whose `enter` always returns `some(provider)` (capture, no acquisition) and whose `exit` always returns `some("nil")` (nothing to release). The bound provider is read inward-only via the unchanged `lifecycle_context(handle, quote(config))`, then used exactly as an explicitly hand-threaded provider would be — `config_view`/`secret_view`/`config_get`/`secret_get`, Outcomes, protected carriers, sinks, authority, and declassification are entirely unchanged. At most one `lifecycle_config` peer may exist anywhere in one root/child/element ancestry chain — enforced entirely by the *existing*, unmodified duplicate-peer-name and ancestor-non-shadowing checks, since `lifecycle_config` always hardcodes the reserved name; sibling scope trees may each bind their own. `src/genia/lifecycle_runtime.py` and `src/genia/configuration.py` are unchanged. See section 9.11
  - E14-1/E14-2/E14-3/E14-4 add no HTTP operation/client, peer-attachment ordering syntax, parser/AST/Core IR change, or ambient/global current-scope state; those remain later R14 tickets (#622-#630)
  - LANGUAGE CONTRACT: the six required default invariants (no global mutable current-scope switch; contained child failure; explicit child result/failure propagation; child-owned resource finalization inside one synchronous call; untouched parent-owned resources; inward-only non-shadowed context) are implemented exactly as locked by the E14-0 contract
  - PYTHON REFERENCE HOST: implemented in `src/genia/lifecycle_runtime.py` as ordinary calls over `values.py` types with no new host capability; validated by `tests/unit/test_lifecycle_runtime.py` (53 tests), `tests/unit/test_lifecycle_repeat.py` (15 tests), and `tests/unit/test_lifecycle_config.py` (4 tests), Python reference host only; shared/multi-host conformance remains Partial

~~~~~

## B039: baseline lines 822-837

Moved from GENIA_STATE.md@d401f322, lines 822-837 (ledger row B039, retained-condensed, sha256 99f4e8e2a68dca51)

~~~~~markdown
- R14 common HTTP operation representation (Experimental, issue #622)
  - `http_operation(method, base_url, path, headers, query, body) -> some(HttpOperation) | err("http-operation-invalid", {stage})` validates all six fields in declared order with zero network IO; the first invalid field stops validation and reports its own `stage` symbol
  - `method` is one of the five approved symbols; `base_url` is exactly `scheme://host[:port]`; `path` starts with `/` and passes through byte-for-byte; `headers` keys are lowercased with case-insensitive collision as construction-time misuse and values a plain string or one `GeniaProtected`; `query` accepts plain string keys/values only, rejecting any protected value; `body` is `none(...)` (normalized to `none("http-no-body")`), `{kind: quote(text), text}`, or `{kind: quote(json), value}` (validated via the existing `json_encode` capability, purely to fail fast)
  - an implicit `content-type` header is added only when `body` validates and `headers` doesn't already set one; an explicit header always wins
  - `HttpOperation` is an ordinary closed `GeniaMap` with no `response` field; it composes with `display`/diagnostics/any container operation exactly like any other map holding a possibly-protected leaf, per R10's existing recursive sink-scan rules — no special-casing needed
  - this is the first R14-HTTP ticket and adds no host capability at all — `web.http_send`, the outbound transport, and protected credential sinks remain later tickets (#623-#628)
  - LANGUAGE CONTRACT and PYTHON REFERENCE HOST: see section 9.12

- R14 outbound HTTP client, protected sinks, annotations, and composition (Experimental, issues #623, #624, #625, #626, #627)
  - R14 E14-6 (issue #623) adds one narrow Python-host outbound HTTP transport capability (one synchronous `urllib.request` attempt, closed `{timeout, connect, tls, dns, other}` failure kind) with no Genia-visible surface of its own — no builtin, no `import` entry; see section 9.13
  - R14 E14-7 (issue #624) adds `web.http_send(operation, authority, timeout_ms) -> some(HttpResponse) | err(reason, context)`, composing the unchanged E14-1 lifecycle core, E14-5's `HttpOperation`, and E14-6's transport into the first outbound HTTP call reachable from Genia source; any received status is an ordinary successful response, never a raised error; see section 9.14
  - R14 E14-8 (issue #625, zero runtime-code change) proves the protected-HTTP-credential-sink contract already implemented by E14-5/E14-7 at comprehensive regression breadth: a protected header value stays opaque through construction/storage/`display`/`debug_repr`/`json_encode`/generic representation operations, and is declassified only immediately before the one transport attempt via the existing `declassify`; see section 9.15
  - R14 E14-9 (issue #626) adds `@get {path}`/`@post {path}` inert declarative annotations plus `web.send_annotated(fn, base_url, authority, timeout_ms)`, the sole function binding them to the unchanged `http_operation`/`web.http_send` surface — annotating a function never changes how it is called; this contract left the exact shape unspecified, so #626 designed it itself following `@route`'s established precedent; see section 9.16
  - R14 E14-10 (issue #627, zero runtime-code change) proves an R8 route handler (an ordinary function) can call `web.http_send`/`web.send_annotated` any number of times per request while the server stays active — `server_lifecycle.py` and `lifecycle_runtime.py` remain architecturally separate, confirmed by direct code reading; see section 9.17
  - E14-6/E14-7/E14-8/E14-9/E14-10 add no new lifecycle primitive, protected-value mechanism, second server/routing/CORS mechanism, or parser/AST/Core IR node

~~~~~

## B040: baseline lines 838-851

Moved from GENIA_STATE.md@d401f322, lines 838-851 (ledger row B040, retained-condensed, sha256 e690a87791d9abaf)

~~~~~markdown
- R14 repeated record lifecycle and YouVersion Bible proxy proving cases, and combined cross-mode hardening (Experimental, issues #695, #628, #696)
  - R14 E14-11 (issue #695, zero runtime-code change) proves that `lifecycle_scope`/`lifecycle_repeat`/`lifecycle_context` already compose into a repeated record-processing pipeline: an outer pipeline/session scope, two peer `LifecycleDefinition`s per element, `record`/`fields`/`nr`/`nf`-style values derived from the reserved `element`/`index` context as ordinary data (no AWK syntax), no cross-element leakage, and correct cleanup on both a data-level `err(...)` record and a genuine element work-phase exception; see section 9.18
  - R14 E14-12 (issue #628, zero runtime-code change) proves `config_view`/`secret_view` (R13/R10), `http_operation`/`web.http_send`, the protected HTTP header sink, and `web.serve_http`/`web.route_request` (R8) already compose into a complete YouVersion Bible proxy proving application, with no real network/credential dependency in automated tests; minting a declassification authority remains a privileged host-side operation never reachable from pure Genia source; see section 9.19
  - R14 E14-13 (issue #696, zero runtime-code change) proves the combined cross-cutting hardening gate over all of E14-1 through E14-12: import/native-test-discovery inertness, serve-mode annotation non-self-execution, sentinel-free rendering across protected values and lifecycle context together, a combined multi-peer/multi-exit-failure matrix, bounded Flow termination with no leak, Python-exception normalization at the transport boundary, combined server/request/outbound-client resilience, and a parse-only regression confirming no new parser/AST/Core IR node; see section 9.20
  - E14-11/E14-12/E14-13 add no new public helper, syntax, annotation, transport mechanism, or lifecycle primitive; each is proof over already-implemented E14-1 through E14-10 mechanism

- R14 release examples, implemented-truth synchronization, and release audit (Experimental, R14 E14-14/E14-15, issues #629/#630)
  - E14-14 adds no runtime behavior: it reconciled `GENIA_STATE.md`, `GENIA_RULES.md`, `README.md`, `GENIA_REPL_README.md`, `docs/host-interop/capabilities.md`, `docs/cheatsheet/quick-reference.md`, `docs/releases/R14.md`, `docs/design/composability-matrix.md`, and `docs/strategy/release-roadmap.md` with the fully-landed E14-1 through E14-13 boundary, correcting stale claims found in `docs/host-interop/capabilities.md` ("genia serve...remain unavailable") and filling gaps in `GENIA_RULES.md` (no `@get`/`@post` entries) and `README.md`/`GENIA_REPL_README.md` (no R14 mention beyond E14-1)
  - E14-15 adds no runtime behavior: its release-wide skeptical audit re-verified the approved E14-0 contract against every implemented slice, re-ran the full R7/R8/R10/R13 regression suites plus the complete non-loopback suite (3800 passed, the same 2 pre-existing unrelated root-sandbox `chmod(0)` failures present since before R14 began), `python -m tools.spec_runner` (587/587), `mkdocs build --strict` (clean), and both proving examples live against their exact CLI spec fixtures byte-for-byte, confirming zero regression and zero drift beyond documentation gaps already fixed by E14-14/this audit's own distillation
  - R14 is release-complete through E14-15 while its APIs remain Experimental, shared/multi-host conformance remains Partial, and Python remains the only implemented host

- Stdout / Stderr
  - `stdout` and `stderr` are first-class host-backed output sink values
  - they are opaque runtime capability values (`<stdout>`, `<stderr>`)
~~~~~

## B065: baseline lines 1406-1441

Moved from GENIA_STATE.md@d401f322, lines 1406-1441 (ledger row B065, retained-condensed, sha256 68ea9985abb83df3)

~~~~~markdown
## 4.7) R20 open functions and extensible pattern dispatch (Experimental, R20 complete through E20-8)
<!-- anchor: state:open-functions -->

R20 adds one concept: an **open function interface** is an identity-bearing
ordinary callable whose immutable clause set is assembled from ordered local
clauses and explicitly selected cross-module contributions. See
`docs/design/r20-open-functions-contract.md` (approved semantics) and
`docs/design/r20-open-functions-syntax-ir-design.md` (approved syntax and
Core IR).

- **Local declaration and repeated clauses.**
  - `open name(<pattern>, ...) = <body>` declares a new open interface; the
    first clause of an interface must carry the `open` keyword.
  - Every subsequent bare `name(<pattern>, ...) = <body>` in the same module,
    for a name already declared `open`, is a repeated clause appended to that
    interface, in source order. `open`/repeated clauses must form one
    contiguous run of top-level statements — a later bare
    `name(<pattern>...) = body` for a name whose run already ended does not
    silently reopen it.
  - `<pattern>` reuses the existing lambda-parameter pattern grammar
    verbatim: identifier bind, wildcard `_`, literal, tuple/list/map
    sub-pattern, `some(...)`/`err(...)`, named-pattern use, and one final
    `..rest` for varargs. An optional `? guard` may follow the closing `)`.
  - A single clause whose body is a grouped `(pat) -> body | (pat) -> body`
    case-with-pipe over a plain-identifier header is flattened at parse time
    into one clause per arm, so grouped and repeated local clause syntax
    normalize to an identical ordered clause list (contract §3.1).
  - Example (the release's required acceptance case):
    ```genia
    open gcd(a, 0) = a
    gcd(a, b) = gcd(b, a % b)

    gcd(48, 18)
    ```
    evaluates to `6`, identically to the grouped spelling
    `open gcd(a, b) = (a, 0) -> a | (a, b) -> gcd(b, a % b)`.
~~~~~

## B066: baseline lines 1442-1455

Moved from GENIA_STATE.md@d401f322, lines 1442-1455 (ledger row B066, retained-condensed, sha256 afa0c7c261acaeeb)

~~~~~markdown
- **Dispatch algorithm** (contract §5): given `n` arguments, if any
  participating clause has a fixed shape of arity `n`, only fixed clauses of
  arity `n` participate; otherwise every eligible varargs clause (minimum
  arity ≤ `n`) participates, and more than one distinct eligible minimum is a
  deterministic `open-function-varargs-ambiguity` failure (the largest
  minimum is never chosen). Within each participating unit (the base, or one
  selected contribution), clauses are tested in lexical order and at most one
  becomes that unit's candidate. If exactly one unit supplies a candidate it
  runs; more than one candidate is a deterministic `open-function-clause-
  ambiguity` failure — there is no specificity ranking and contribution
  selection/import order can never break a tie. Existing fixed-over-varargs
  precedence, first-match order, guards, named patterns, and automatic
  Outcome/`none` propagation are preserved by reusing the existing pattern
  engine (`match_lambda_pattern`) unchanged.
~~~~~

## B067: baseline lines 1456-1491

Moved from GENIA_STATE.md@d401f322, lines 1456-1491 (ledger row B067, retained-condensed, sha256 3fdf398fca507860)

~~~~~markdown
- **Duplicate clauses.** Two clauses in the same unit with the same
  structural, alpha-normalized, span-free dispatch key are
  `open-function-duplicate-clause`, detected once when the unit is built
  (module load time), never deferred to call time. The same dispatch key in
  two different units is not a build-time duplicate; if both match one call,
  the across-unit ambiguity rule applies.
- **Explicit cross-module contribution.**
  - `extend <module-alias>.<name>(<pattern>, ...) = <body>` (in a
    contributing module that has already `import`ed `<module-alias>`)
    declares one clause of that module's contribution unit targeting the
    open interface exported as `<name>` by `<module-alias>`. Repeated
    `extend` statements for the same target in the same module accumulate
    into one contribution unit, in source order.
  - `use <name> from <base-alias> with <contrib-alias-1>, <contrib-alias-2>,
    ...` is a declarative, once-evaluated top-level statement (like
    `import`) that resolves `<base-alias>.<name>`, resolves each named
    contribution module's exported contribution unit for that exact
    interface, and binds `<name>` in the *current* module to the resulting
    immutable linked view. There is no wildcard/implicit selection.
  - Ordinary `import` alone never selects a contribution: importing a
    contribution-bearing module without an explicit `use` leaves the base
    interface (and any other module's already-linked view) completely
    unaffected.
  - Interface/contribution identity is the pair (canonical cached module
    name, exported name) — the same identity `Env.load_module` already
    caches modules under. Import alias, file path, and host object address
    are never part of this identity, so two aliases of the same cached
    module are one interface/contribution, duplicate selection through two
    such aliases is a deterministic `open-function-duplicate-selection`
    failure, and reordering unrelated imports or the `with` list cannot
    change a successful dispatch result.
  - Selecting a module with no matching contribution unit, or a closed
    function/non-function, is `open-function-incompatible-contribution`.
  - Declaration, import, and `use` perform no lifecycle activation, resource
    acquisition, network/process IO, or clause-body execution; a clause body
    runs only after a successful call dispatches to it.
~~~~~

## B068: baseline lines 1492-1510

Moved from GENIA_STATE.md@d401f322, lines 1492-1510 (ledger row B068, retained-condensed, sha256 6c4eee84389b0a33)

~~~~~markdown
- **Provenance and introspection.** `help(interface-or-linked-view)` lists
  the interface name, its declaration span, effective documentation (or "No
  documentation available."), and every participating unit's clauses in
  deterministic order — the base unit first (labelled by its declaring
  module identity), then each contribution unit ordered by its declaring
  module identity, clauses within a unit by lexical ordinal. `doc(name)`
  returns the interface's own docstring; contribution clauses cannot supply,
  replace, or erase interface-level documentation. No host object address or
  Python-specific representation is exposed.
- **Diagnostics.** `open-function-redeclaration`,
  `open-function-target-not-open`, `open-function-duplicate-clause`,
  `open-function-duplicate-selection`,
  `open-function-incompatible-contribution`,
  `open-function-varargs-ambiguity`, and `open-function-clause-ambiguity` are
  raised as `TypeError` subclasses (`src/genia/callable.py`) with the
  parameters the contract requires; a pattern/shape miss reuses the existing
  `No matching function` / `No matching case` diagnostic families. Span
  rendering in these messages is a plain `filename:line` string, not a raw
  host object repr.
~~~~~

## B069: baseline lines 1511-1524

Moved from GENIA_STATE.md@d401f322, lines 1511-1524 (ledger row B069, retained-condensed, sha256 25f3b56e71a08137)

~~~~~markdown
- **Core IR.** Three new portable node types —
  `IrOpenFuncDef(name, clauses, docstring, annotations)`,
  `IrOpenContribution(target_module_alias, target_name, clauses)`, and
  `IrOpenUse(local_name, target_module_alias, target_name,
  contribution_module_aliases)` — reuse the existing `IrCaseClause`/
  `IrPatTuple`/`IrPatRest` pattern representation verbatim; no new pattern or
  guard node was added. See
  `docs/architecture/core-ir-portability.md`.
- **Host capability.** A dedicated `open_functions` capability
  (`spec/manifest.json` optional capability;
  `docs/host-interop/HOST_CAPABILITY_MATRIX.md`) is `Implemented` for Python;
  every R20 shared spec case requires `open_functions` so an
  older/non-conforming host reports these cases unsupported rather than
  silently passing them.
~~~~~

## B070: baseline lines 1525-1541

Moved from GENIA_STATE.md@d401f322, lines 1525-1541 (ledger row B070, retained-condensed, sha256 29bb245821026bc5)

~~~~~markdown
- **Known limitations of this Experimental slice** (see
  `docs/analysis/r20-release-truth-audit.md` for the full accounting):
  - a grouped case-with-pipe body is auto-flattened only when the header
    pattern is plain identifiers and the body is exactly one `CaseExpr` (or
    a one-expression `{ }` block containing one); other combinations of a
    non-trivial header with a case body are rejected rather than given
    ad hoc semantics;
  - `@doc`/`@meta`-style annotation attachment is not wired for `open`/
    `extend` declarations in this slice — interface metadata beyond the
    optional docstring position is a follow-up;
  - cross-module contribution/linking behavior retains Python-host real-file
    unit evidence and has eight portable shared eval/error cases using #836's
    logical multi-file fixture; those cases additionally require the R16
    `multi_file_eval` transport capability, independently of R20 semantics;
  - debug-hook wiring (`debug_hooks`/`debug_mode` propagation used by the
    Python debug adapter) is not threaded through open-function dispatch.

~~~~~

## B077: baseline lines 1627-1641

Moved from GENIA_STATE.md@d401f322, lines 1627-1641 (ledger row B077, retained-condensed, sha256 cd954ce99f4e7dde)

~~~~~markdown
- open-shape field specifications and checks run in specification insertion order; missing fields return `none("open-shape-missing-field", {field: name})`, non-map subjects return `none("open-shape-mismatch")`, and a nested Template `none` or `err` is propagated unchanged
- `exact_shape_match(fields, value)` uses the same specification protocol but requires the candidate map's key set to equal the specification key set; non-map, missing, and extra candidates return `none("exact-shape-mismatch")`, `none("exact-shape-missing-field", {field: name})`, and `none("exact-shape-extra-field", {field: name})` respectively
- exact-shape specifications are validated first; missing fields are checked in specification insertion order, then extras in candidate insertion order, then field Templates in specification order
- nested Template `some(payload)` establishes compatibility only; structural matching does not transform the field or subject, while nested `none`/`err` propagates unchanged
- refinement/open/exact helpers compose through existing direct calls, `Name(inner_pattern)`, `@?`, `@!`, and `&`; they add no syntax, nominal identity, or runtime shape category
- positional/labeled shapes and nominal Structs are not implemented by the Template/shape slices; the separate Experimental JSON Schema boundary below compiles only its locked structural subset

Inert inspectable Template descriptions (Experimental, R15 E15-1, issue #728):

- `refinement(predicate)` returns a curried one-argument Template whose behavior is identical to `refinement_match(predicate, value)`; `open_shape(fields)` and `exact_shape(fields)` are the curried equivalents of `open_shape_match`/`exact_shape_match`. Each builder validates its argument eagerly at construction time, using the same validation as its two-argument counterpart, and requires zero additional matching logic — the returned Template simply delegates to the existing two-argument helper.
- `template_description(template)` requires a callable Template and returns `some(description)` when `template` was produced by `refinement`, `open_shape`, `exact_shape`, or `json_schema`; every other callable Template — arbitrary one-argument callables and named patterns declared with `pattern Name(value) = ...`, even when the body directly calls `refinement_match`/`open_shape_match`/`exact_shape_match` — remains fully valid but opaque and returns `none("opaque-template")`. A non-callable argument raises a clear `TypeError`.
- description shapes are ordinary Genia data built only from maps, symbols, strings, booleans, and lists:
  - `refinement` -> `{kind: quote(refinement)}`; the predicate is never introspected, executed during inspection, or exposed
  - `open_shape`/`exact_shape` -> `{kind: quote(open_shape)|quote(exact_shape), fields: {name: field_description, ...}}`, where `fields` preserves the builder's field-map insertion order and each entry is either that field Template's own description or the symbol `quote(opaque)` when the field Template itself has none
  - a `json_schema`-compiled Template additionally carries a description mirroring its already-compiled internal schema: scalar node -> `{kind: quote(json_schema_scalar), type: quote(<type>)}`; object node -> `{kind: quote(json_schema_object), properties: {name: description, ...}, required: [names...], additional: bool}` with `properties` in schema-declaration order; array node -> `{kind: quote(json_schema_array), items: description}`
~~~~~

## B078: baseline lines 1642-1655

Moved from GENIA_STATE.md@d401f322, lines 1642-1655 (ledger row B078, retained-condensed, sha256 6085b95c188b7da7)

~~~~~markdown
- descriptions are immutable and inert: they do not participate in equality, hashing, callable identity, pattern identity, matching, dispatch, or original-subject semantics (`@?`, `@!`, `&`, and `Name(inner)` behave identically whether or not a Template has a description). Two Templates built from equal specifications are two distinct callables with equal-shaped descriptions, never the same Template.
- construction and inspection are effect-free: no user-data validation runs, no predicate/refinement callable is executed, and no config/lifecycle lookup, filesystem/network IO, or import-time activation occurs.
- no protected or represented payload can appear inside a description; nested field/property entries contribute only their own description shape or the `quote(opaque)` marker, never a captured closure or field value.
- example: `Person = exact_shape({name: refinement((x) -> x != ""), age: refinement((x) -> x >= 0)})`; `template_description(Person)` is `some({kind: quote(exact_shape), fields: {name: {kind: quote(refinement)}, age: {kind: quote(refinement)}}})`; `Person({name: "Ada", age: 3})` is unchanged from `exact_shape_match`'s own behavior: `some({name: "Ada", age: 3})`.

Explicit missing-only field defaults (Experimental, R15 E15-2, issue #729):

- `default_field(default, template)` wraps a field Template with an explicit default for use as a field entry inside `open_shape(fields)` / `exact_shape(fields)` (the E15-1 curried builders); `template` must be Template-callable or it raises `TypeError("default_field expected Template function, received <type>")`.
- when the wrapped field's key is present in the candidate map, `default_field` has no effect: the present value is validated by `template` exactly as an ordinary field entry, and a present invalid value fails normally — it never falls back to the default.
- when the wrapped field's key is absent, the shape validates `default` through `template` (not the missing candidate value); a passing default is inserted into the result under that field name, while a failing default's mismatch/error propagates unchanged as that field's own Outcome rather than being reported as a missing-field mismatch.
- on overall success: if no defaults were actually applied, `open_shape`/`exact_shape` return the exact original subject unchanged (identity-preserved, not merely equal); if one or more defaults were applied, they return a new map equal to the subject plus every inserted default field, in specification order.
- `open_shape_match`/`exact_shape_match` (the R9-era two-argument matcher primitives used inside `pattern Name(value) = ...` bodies) are completely unmodified by E15-2 and know nothing about `default_field`; only the E15-1 curried `open_shape`/`exact_shape` builders recognize it.
- `template_description` on a `default_field`-wrapped Template is `{kind: quote(field_default), has_default: true, template: inner_description_or_quote(opaque)}`; the literal default value is never copied into the description, so a protected or represented default stays opaque there exactly as it does everywhere else.
- a default filled inside a nested structural Template establishes that nested value's own compatibility only; it does not transform the *outer* field, consistent with the existing R9 invariant that a nested Template's success payload never replaces the enclosing subject. For example, with `Address = exact_shape({city: default_field("Unknown", ...)})` and `Person = exact_shape({..., address: Address})`, `Person({..., address: {}})` keeps `address: {}` in its own result even though `Address({})` independently succeeds as `some({city: "Unknown"})`; only defaults declared directly in a shape's own field map are reflected in that shape's own returned value.
~~~~~

## B079: baseline lines 1656-1669

Moved from GENIA_STATE.md@d401f322, lines 1656-1669 (ledger row B079, retained-condensed, sha256 586f8cd0e0858893)

~~~~~markdown
- explicit normalization needs no new builtin: `record |> normalize_fn |> Shape` is already ordinary explicit pipeline composition, where `normalize_fn` is any ordinary one-argument function and `Shape` validates its result exactly as any other value; Template matching itself performs no coercion.
- construction and matching remain effect-free; no ambient config/lifecycle/IO occurs.

Accumulated path-aware validation diagnostics (Experimental, R15 E15-3, issue #730):

- `accumulate(template, value)` validates `value` against an inspectable Template, collecting every independent field/index failure in one call instead of short-circuiting on the first mismatch; `template` must be Template-callable, and (after unwrapping one outer `default_field`, if present) must carry a `template_description` or it raises `TypeError("accumulate expected inspectable Template, received opaque Template")`.
- deep recursion is supported only for the `open_shape`/`exact_shape` family (including nested shapes and `default_field`-wrapped fields, which reuse their exact real default-insertion semantics); a bare `refinement` Template, or any other inspectable-but-non-shape Template such as a `json_schema`-compiled one, is treated as one leaf check rather than recursed into.
- `exact_shape`'s own contracted phase order is replicated for diagnostics: missing-without-default fields in specification order, then extra fields in candidate order, then per-field validation in specification order, depth-first; `open_shape`'s single interleaved per-field pass is replicated as-is.
- each diagnostic entry is `{path: [field_name_or_index, ...], kind: quote(mismatch)|quote(error), reason: <reason>}`; `path` segments are built only from the Template's own specification/traversal (field names as strings), never from candidate data; `kind` is `quote(mismatch)` for an underlying `none(...)` observation and `quote(error)` for `err(...)`; `reason` is exactly the underlying Outcome's own `reason` value and never its `context`, so an arbitrary leaf Template's context can never leak a protected or represented payload into a diagnostic.
- zero diagnostics: `accumulate` returns the exact result of directly invoking `template(value)` — it never reimplements or diverges from the real success path (including default insertion). One or more diagnostics: `err(quote(accumulated-validation-failed), {diagnostics: [...]})` in the deterministic order above.
- `accumulate` never touches Flow or Seq itself; it operates on one already-materialized value, so composing it inside an ordinary `map` stage over a lazy Flow preserves existing bounded-demand, no-over-pull, single-use Flow semantics with zero new Flow-specific code.
- `accumulate` does not change `open_shape_match`/`exact_shape_match`/`refinement_match`/`open_shape`/`exact_shape`/`refinement`/`default_field`/`json_schema` direct-call behavior, named-pattern dispatch, `@?`/`@!`/`&`, or case-arm/first-match semantics; it is a separate, explicitly-invoked operation that only reads their existing private structural attributes.
- example: `Person = exact_shape({name: refinement((x) -> x != ""), age: refinement((x) -> x >= 0)})`; `accumulate(Person, {name: "", age: -1})` is `err(quote(accumulated-validation-failed), {diagnostics: [{path: ["name"], kind: quote(mismatch), reason: "refinement-mismatch"}, {path: ["age"], kind: quote(mismatch), reason: "refinement-mismatch"}]})`.

~~~~~

## B080: baseline lines 1670-1683

Moved from GENIA_STATE.md@d401f322, lines 1670-1683 (ledger row B080, retained-condensed, sha256 eaa9f998f856a348)

~~~~~markdown
Faithful Template to JSON Schema generation (Experimental, R15 E15-4, issue #731):

- `template_schema(template)` generates a JSON Schema for `template` through pure inspection over its own `template_description` data; it never invokes `template`, never invokes any nested field Template, never executes a callable refinement predicate, and touches no runtime value at all. `template` must be Template-callable or it raises `TypeError("template_schema expected callable Template, received <type>")`.
- faithfully convertible: a `json_schema`-compiled Template's own description converts back to the equivalent schema map directly (it already is schema-shaped); `open_shape`/`exact_shape` convert to `{type: "object", properties: {...}, required: [every field name, specification order], additionalProperties: <true for open_shape, false for exact_shape>}` only when every field recursively converts.
- deterministically unsupported, never approximated: an opaque field or top-level Template (no description at all); a bare `refinement` field or top-level Template (its predicate is never introspected, so it has no derivable JSON type); a `default_field`-wrapped field or top-level Template (JSON Schema's `default` keyword is an annotation, not an insertion transform, so missing-only default semantics cannot be represented faithfully — the same conclusion E15-2 already reached).
- failure is `err(quote(unsupported-template), {path: [field_name_or_index, ...], kind: quote(opaque)|quote(refinement)|quote(default_field)|quote(unsupported_kind)})`, `path` pointing at the exact unsupported node; success is `some(represent("json", schema_map), {kind: quote(template_schema), operation: quote(generate), status: quote(generated), reason: quote(generated)})`.
- round-trip claim is limited to the tested subset: compiling a schema with `json_schema`, reversing it with `template_schema`, and recompiling the result with `json_schema` produces a Template with identical accept/reject behavior over the tested representative values — not object identity, not preservation of non-schema metadata.
- `template_schema` does not change `json_schema`/`open_shape`/`exact_shape`/`refinement`/`default_field`/`accumulate`/`template_description` direct-call behavior; it is a separate, explicitly-invoked, pure-inspection operation.
- example: `Person = exact_shape({name: NameTemplate})` where `NameTemplate` is `json_schema`-derived from `{type: "string"}`; `template_schema(Person)` is `some(represent("json", {type: "object", properties: {name: {type: "string"}}, required: ["name"], additionalProperties: false}), context)`. `Person = exact_shape({name: refinement((x) -> x != "")})`; `template_schema(Person)` is `err(quote(unsupported-template), {path: ["name"], kind: quote(refinement)})`.

Structural discriminated alternatives (Experimental, R15 E15-5, issue #732):

- `alternatives(discriminator_field, branches)` is a curried Template builder (same family as `refinement`/`open_shape`/`exact_shape`) selecting exactly one branch by reading an explicit string discriminator field, then validating only that branch against the full original value; ordinary map/value payloads only, no nominal variant object is ever constructed. `discriminator_field` must be a non-empty ordinary string; `branches` must be a map whose keys are non-empty ordinary strings and whose values are Template-callable, or construction raises a clear `TypeError`.
- direct-call resolution order: a non-map subject returns `none("alternative-mismatch")`; a subject missing `discriminator_field` returns `none("alternative-missing-discriminator", {field: discriminator_field})`; a present discriminator value that is not an ordinary string (a symbol counts as not-a-string here) returns `none("alternative-invalid-discriminator", {field: discriminator_field})`; a string not present among `branches`' keys returns `none("alternative-unknown-discriminator", {field: discriminator_field, value: <the discriminator string>})`; otherwise the resolved branch Template is invoked on the full unmodified subject and its Outcome is returned unchanged.
~~~~~

## B081: baseline lines 1684-1697

Moved from GENIA_STATE.md@d401f322, lines 1684-1697 (ledger row B081, retained-condensed, sha256 de98f4a4bdecc822)

~~~~~markdown
- exactly one branch is ever validated; a branch's own mismatch/error surfaces unchanged and no other branch is ever attempted — there is no try-every-branch-and-pick-a-success semantics and no discriminator inference from payload shape.
- `alternatives` does not strip the discriminator field before branch validation; a branch built with `exact_shape` must declare the discriminator field itself if it wants a fully closed shape, while a branch built with `open_shape` tolerates it as an allowed extra, exactly like any other nested-shape composition.
- `template_description` -> `some({kind: quote(alternatives), discriminator: discriminator_field, branches: {tag: branch_description_or_quote(opaque), ...}})`, `branches` in the builder's own map insertion order.
- `accumulate` recurses depth-first into exactly the resolved branch at the same path (the branch validates the whole subject, not a sub-field); discriminator-resolution failures produce one diagnostic at `path + [discriminator_field]` with reason `accumulate-not-a-map`/`alternative-missing-discriminator`/`alternative-invalid-discriminator`/`alternative-unknown-discriminator` as applicable.
- `template_schema` returns `err(quote(unsupported-template), {path: [...], kind: quote(alternatives)})` for every `alternatives` Template — E15-4's closed schema-keyword subset has no discriminated-union primitive, and this slice does not extend it.
- composes with named patterns, `@?`, `@!`, `&`, and `Name(inner)` exactly like any other Template, since `alternatives` produces an ordinary Template built the same way as `refinement`/`open_shape`/`exact_shape`; no pattern-dispatch code was added or changed.
- issue #92 disposition: only structural discriminator-directed validation is absorbed here. Nominal variant identity, constructor objects/syntax, sealed/closed nominal hierarchies, and exhaustiveness checking remain explicitly deferred beyond R15 and are not implemented.
- example: `Circle = open_shape({radius: refinement((x) -> x > 0)})`; `Shape = alternatives("kind", {circle: Circle})`; `Shape({kind: "circle", radius: 5})` is `some({kind: "circle", radius: 5})`; `Shape({kind: "triangle"})` is `none("alternative-unknown-discriminator", {field: "kind", value: "triangle"})`.

Bounded named recursive Template references (Experimental, R15 E15-6, issue #733):

- `recursive_template(name, build_fn, max_depth)` builds a self-recursive Template through one explicit named reference; `name` must be a non-empty ordinary string, `build_fn` must be Template-callable, and `max_depth` must be a positive integer no greater than 100, or construction raises a clear `TypeError`. Validation of a self-reference reachable through `alternatives`/`open_shape`/`exact_shape` composition (the documented idiom, and the only shape every example uses) runs on an explicit Python-list stack rather than the Python call stack: `alternatives` dispatch is a pure tail substitution and each shape field's descent pushes one frame that is popped again before the next field is considered, so frames never accumulate along the self-reference spine. This keeps the explicit depth bound's own Python stack usage independent of `max_depth` and of how deep a validated value actually is — the bound fires correctly at any documented `max_depth` (verified to a logical depth of 10,000, ten times Python's own default recursion limit) and `RecursionError` never crosses the boundary for this idiom. A self-reference invoked from behind a fully opaque (non-inspectable) wrapper Template still falls back to ordinary Python recursion for that unusual case only, remaining correctly bounded but without the O(1)-stack guarantee.
- construction calls `build_fn(ref)` exactly once with an ordinary one-argument callable `ref`: `ref(name)` (matching the declared `name`) returns a self-reference Template; `ref(other_name)` returns a Template that always fails with `err("recursive-template-unresolved-reference", {name: other_name})` without inspecting its argument. `ref`'s own argument must be an ordinary string, and `build_fn`'s return value must itself be Template-callable, or construction raises a clear `TypeError`.
- reference resolution is entirely closed over the one `name`/`build_fn`/`max_depth` triple supplied at construction; no mutable global registry, configuration, or lifecycle context ever participates. Depth is tracked per `recursive_template` instance with a dedicated `contextvars.ContextVar` created fresh inside each call — never shared across instances or exposed to Genia code — reset to `0` on every top-level call and incremented/restored around each self-reference invocation.
~~~~~
