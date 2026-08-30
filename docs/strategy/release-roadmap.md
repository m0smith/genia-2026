# Genia Release Roadmap

Status: Planning guide — non-authoritative. This is not a language contract.

This document orders upcoming Genia releases. It does not define implemented language behavior.
Planned items must not be documented as implemented behavior.

Implemented behavior remains defined by:

1. GENIA_STATE.md
2. GENIA_RULES.md
3. GENIA_REPL_README.md
4. README.md
5. spec/*

This roadmap exists to help LLM agents and maintainers keep planning, issue creation, and release sequencing aligned with the current product direction.

## Release Examples

Every implemented release listed below (R1 onward) must have a published
`docs/releases/<Rn>.md` page with one or more small, runnable examples for that
release's headline behavior — see `docs/releases/README.md`. This is maintained
during the doc phase of each change (`docs/process/05-doc.md` step 6a), not
created merely because a planned release is named and not retrofitted at release
close. A release is not "done" (✓ COMPLETE) until its page exists.

## Product North Star

Genia's first killer workflow is:

> Outcome-aware validated data pipelines.

Plain-language promise:

> messy records in → clear pipelines → validated shaped output / reports + useful diagnostics

New release work should strengthen this workflow unless explicitly approved as infrastructure or parking-lot work.

---

## Release R1 — Killer Workflow Foundation ✓ COMPLETE

Theme:

> Make Outcome-aware validated data pipelines feel real, useful, and demonstrable.

**Status: Complete.** The R1 foundation has been implemented and demonstrated.

R1 proved the core pipeline model end-to-end:

```text
messy records in → clear pipelines → Outcome-aware validation → clean records + diagnostics out
```

Delivered:

- Outcome value family: `some`, `none`, `err` with pipeline propagation
- Validation helpers: `validate_required`, `validate_field`, `validate_optional`, `validate_record`, `validate_each`
- `collect_validated` terminal helper for aggregating Outcome-aware pipeline results
- Flow / Seq / Sheet pieces supporting the data-pipeline story
- Diagnostic conventions for record/field failures
- Malformed record pipeline diagnostics (issue #398)
- End-to-end validated data pipeline demo (`examples/validated_pipeline_demo.genia`)
- Docs and tests tied to implemented behavior

Excluded from R1 (see R2, R6, or parking lot):

- general lifecycle system
- native unit test framework
- actors/concurrency expansion
- browser playground
- speculative value-template syntax
- CSV / JSONL record-parsing production helpers
- rich Sheet integration beyond minimal landing zone
- grouped diagnostic summaries and report helpers

---

## Release R2 — Native Test Kernel ✓ COMPLETE

Theme:

> Let Genia test Genia where Genia-level tests make sense.

R2 protects and exercises the R1 surface through native Genia tests.

Delivered:

- `genia test <file>` execution mode
- legacy `genia --test <file>` mode
- current `test(name, body)` registration path
- minimal assertions
- file-level test discovery through registered test units
- deterministic test result reporting
- selected shared CLI native-test outcomes
- one native validated-pipeline fixture

Excluded:

- arbitrary custom lifecycle definitions
- annotation-driven native test discovery
- setup/teardown annotations
- generalized module/test lifecycle hooks
- server/request/actor lifecycles
- parallel native test execution
- property testing
- snapshot testing
- full pytest migration
- changing shared semantic spec authority

Exit criteria:

- Genia-native tests cover part of the validated data pipeline surface.
- Python pytest remains responsible for host/runtime/parser/spec-runner internals.
- Native-test behavior is documented as Experimental, Python reference host only.

---

## Release R3 — Native Test Expansion Wave 1 ✓ COMPLETE

**Status: Complete.** R3 expanded native Genia test coverage over Genia-facing behavior.

Theme:

> Grow native test coverage over Genia-facing behavior without touching parser/IR/host internals.

Implemented annotation-driven test syntax (issue #458):

```genia
@test "basic math works"
test1() = assert_eq(1+1, 2)
```

R2 introduced the `test(name, body)` call form. R3 added `@test "description"` annotation-driven native test discovery: `@test` annotated zero-argument functions are discovered after legacy `test(name, body)` registrations and run through the same native test kernel. The annotation carries the human-readable description; the function name is the test identifier.

Delivered:

- `@test "description"` annotation-driven native test discovery (issue #458)
- native test coverage for validation helpers and `collect_validated`
- native test coverage for Outcome constructors and rendering behavior
- native test coverage for JSONL helper behavior in validated pipeline examples
- at least one pipeline example backed by a native test (`examples/r3_validated_pipeline_native_tests.genia`)
- native tests kept focused on Genia-facing behavior; parser/IR/host internals were not touched

Excludes:

- parser internals
- IR normalization
- host adapter behavior
- lifecycle generalization (see R4)
- pytest migration (see R5)
- setup/teardown, fixtures, parameterization, broad discovery, or multi-host claims

---

## Release R4 — Lifecycle Generalization ✓ COMPLETE

**Status: Complete.** R4 extracted the proven test lifecycle shape into a portable lifecycle contract while keeping observable lifecycle behavior narrow and test-backed.

Theme:

> Extract the proven test lifecycle shape into a portable lifecycle contract.

Primary outcomes:

- Lifecycle plans become portable Genia-level data/contracts.
- Annotation discovery is phase-driven and explicit.
- Execution modes can eventually use lifecycle plans without making import/load behavior spooky.

Delivered / included:

- lifecycle plan shape
- phase shape
- scope model
- cleanup rules
- failure rules
- annotation binding model
- deterministic source-order / reverse-source-order execution rules
- portable docs for execution-mode lifecycle proposals
- test lifecycle remains the first implemented consumer — the Python reference host native test path consumes the inert lifecycle contract as descriptive plan/scope data (issue #454); Experimental, no lifecycle runner / phase execution / setup/teardown / observable native-test behavior change
- annotations do not execute merely because they exist

Excludes:

- server mode implementation
- actor lifecycle implementation
- arbitrary plugin system
- YAML lifecycle runner unless separately approved
- broad runtime rewrites
- lifecycle behavior not exercised by tests
- unrelated data-pipeline hardening, now classified under R6 unless explicitly promoted

Exit criteria:

- Lifecycle is documented as a general model.
- Test lifecycle remains the first implemented consumer as an inert descriptor link.
- No annotations execute merely because they exist.

---

## Release R5 — Native Test Migration / Genia-Facing Coverage Wave 1 ✓ COMPLETE

**Status: Complete.** All ten R5 issues (#509-#518) are closed and the final truth audit (#518) passed with full regression green.

Theme:

> Move appropriate Genia-facing tests into Genia-native tests.

Primary outcomes:

- More prelude and language-facing behavior is tested in Genia.
- Python tests remain for Python host internals.
- The split between native tests and pytest is explicit.

Move candidates:

- Outcome helpers
- validation helpers
- Flow/Seq visible behavior
- Sheet helper behavior that is already implemented
- prelude-level utilities
- examples intended to be Genia-facing

Keep in pytest:

- parser internals
- IR normalization
- host adapter behavior
- CLI harness internals
- spec runner implementation
- Python-specific exceptions and plumbing

Current R5 issue set:

- **#509** — roadmap/R5 active-release alignment
- **#510** — native-test vs pytest boundary contract
- **#511** — audit pytest coverage for native-test migration candidates
- **#512** — migrate Outcome helper behavior to native tests
- **#513** — migrate validation helper behavior to native tests
- **#514** — migrate visible Flow/Seq behavior to native tests
- **#515** — migrate implemented Sheet helper behavior to native tests
- **#516** — add native coverage for Genia-facing examples
- **#517** — document native-test vs pytest guidance
- **#518** — final R5 native migration truth review

Existing R5-adjacent issues:

- **#369** — optional shared spec cleanup for removed slash named-access compatibility
- **#406** — tested validation quick-reference examples
- **#486** — optional focused validated-pipeline reporting example, if still useful

Exit criteria:

- Native test suite proves useful Genia-facing behavior without duplicating every pytest.
- Documentation explains what belongs in native tests vs pytest.
- Parser, IR, host, CLI harness, spec-runner, and Python internals remain protected by pytest/shared specs.
- No R6 data-hardening work is pulled into R5 unless explicitly promoted.

Agent guidance for R5:

- Current release focus is R5. When asked for new Genia work with no release specified, classify the work against R5 first.
- If the work is native-test migration or Genia-facing coverage, proceed through the normal phase pipeline.
- If the work is data-workflow hardening, classify it as R6 unless the user explicitly promotes it.
- R5 is not a bucket for CSV helpers, new Sheet APIs, diagnostic helper APIs, actors, browser work, or broad value-template implementation.

---

## Release R6 — Data Workflow Hardening ✓ COMPLETE

**Status: Complete.** All nine R6 issues are closed and `docs/releases/R6.md`
carries a runnable example for each landed issue that added user-facing
behavior.

Theme:

> Make validated pipelines feel production-useful.

This release picks up the data-workflow items deferred from R1. These items were deferred because R1 proved the core model; they are not required for that proof and belong to production-quality polish.

Current R6 issue set:

- **#543** — roadmap/R6 active-release alignment ✓ closed

Deferred R1 items now targeting R6:

- **#405** — post-R1 diagnostic-context hardening ✓ closed
- **#393** — diagnostic helper APIs for field/index-aware validation diagnostics ✓ closed
- **#394** — conditional / deferred until concrete need is proven — ✓ closed not-planned; `collect_validated` + `filter` already covers the partition use case, no repeated friction found
- **#390** — CSV support (record ingestion from CSV files) ✓ closed
- **#395** — Sheet landing zone improvements ✓ closed
- **#396** — depends on #395; schedule after Sheet landing zone lands ✓ closed
- **#363** — delivered; `row_get(row, column_name)` ergonomic row access ✓ closed
- **#364** — depends on Sheet landing zone; schedule after #395 — ✓ closed completed, no code change; `rows(sheet)` already satisfies the explicit row-Seq-adapter contract

Possible additional includes:

- richer diagnostics
- grouped summaries
- report helpers
- Sheet aggregation helpers
- schema/shape inspection helpers
- better command-line ergonomics
- clearer examples for real-world records
- possible file-search helper for CLI-native data workflow setup
- Option Record Pattern for APIs with many optional settings
- diagnostics for unknown or invalid options

Deferred candidates after the R1 demo proves the basic workflow:

- richer Sheet integration beyond the minimal R1 landing zone
- `validate_each/3` context merging, if R1 diagnostics reveal a concrete repeated need
- validation DSL exploration, only if plain helpers and value-template work prove insufficient

Excludes by default:

- actors
- browser-native runtime
- full static type system
- broad value-template implementation

Agent guidance for R6:

- R6 is complete. When asked for new Genia work with no release specified, do not default to classifying it against R6 — check whether it fits an active release (see current status above) or belongs in a new ticket/parking lot.
- Do not create tickets for R6's former "possible additional includes" or "deferred candidates" items without explicit user approval — they are brainstorm/parking-lot scope, not approved tickets, and are not automatically reopened by R6's closure.
- If a concrete gap in `rows(sheet)` (#364) or a proven repeated need for a `partition_validated`-style split (#394) surfaces later, file it as a focused follow-up issue with evidence, not a reopening of the closed R6 ticket.

---

## Release R7 — Web Serving Ergonomics ✓ COMPLETE

**Status: Complete.** Promoted from the parking lot as **explicitly approved infrastructure work** after R6 completed. This release does **not** strengthen the validated-data-pipeline killer workflow; it was scheduled deliberately as infrastructure.

Theme:

> Make the web / HTTP serving surface comfortable for a real browser client.

Context:

- Surfaced by exercising `serve_http` against a real browser client for an external consuming app. Historical idea capture: `docs/parking-lot/web-backend-cfm-app.md`.
- Verified current behavior remains defined by `GENIA_STATE.md`: handler-returned response headers reach the transport, `request("query")` is parsed, routing uses the query-stripped exact path, and the server is synchronous/blocking.
- Delivered by #526 and #527: composable response-header handling and automatic browser CORS preflight. Issue #530 stabilized the Python-host web capability boundary, published the runnable release example, and completed the release truth audit.

Approved architecture:

```genia
with_headers(headers, response) -> response
cors(policy, handler) -> handler
```

- `with_headers` is the single response-header composition mechanism.
- `cors` is a handler wrapper that decorates ordinary responses through `with_headers` and answers true browser preflight requests.
- Do not add header-taking overloads to `json` or `text`.
- Do not add a separate public `options(...)` route constructor for R7.
- R8's inert `@cors` annotation binds to the R7 `cors` wrapper; it must not create a second CORS mechanism.

Required issue path:

1. **#526 — E-1: response header composition with `with_headers`**
2. **#527 — E-2: CORS handler wrapper with automatic preflight**
3. **#530 — E-3: stabilize and audit the Python-host web capability**

Dependency order: **#526 → #527 → #530**.

Deferred from R7:

- **#528 — path-parameter routing:** closed not-planned; query parameters satisfy the demonstrated consumer. Reconsider only with concrete repeated friction.
- **#529 — concurrent serving:** closed not-planned; the consumer has no measured concurrency need. Reconsider only with load evidence.
- Both remain planning history and are not R7 completion work.

Excludes:

- a general web framework, middleware framework, or broad server-mode runtime
- `genia serve <file>` and lifecycle-activated web annotations (R8)
- browser-native runtime
- path parameters or concurrency without new evidence
- credentials/cookies policy, dynamic origin reflection, per-route CORS overrides, authentication, or authorization
- parser, lexer, Core IR, or unrelated host-adapter changes
- multi-host portability claims
- documenting planned behavior as implemented before it ships — `GENIA_STATE.md` remains authoritative

Exit criteria:

- A browser-shaped preflight followed by a JSON request succeeds through a real `serve_http` instance.
- Application handlers contain no manual `access-control-*` header construction.
- JSON content type and application status/body survive CORS response decoration.
- Genia-native tests cover the public value/wrapper behavior, while focused Python tests cover the HTTP transport boundary.
- Web behavior is pinned in `docs/host-interop/capabilities.md` with correct Python-host-only status.
- `docs/releases/R7.md` provides a runnable headline example.
- R8 binds to the landed R7 primitives without a second mechanism.
- No completed R5/R6 behavior is reopened or regressed.

Final R7 disposition:

- #526 and #527 completed the approved header-composition and CORS wrapper path.
- #528 and #529 closed not-planned; path parameters and concurrency remain deferred pending evidence.
- #530 pinned the Python-host-only capability and coverage boundary and verified the release exit criteria.
- R8 was explicitly activated after R7 completion; R7 remains closed.

---

## Release R8 — Server Execution Mode

**Status: Complete.** Explicitly approved infrastructure work delivered after R7. R8 implemented server execution mode as the second R4 lifecycle consumer without broadening it into a general web framework. It does **not** strengthen the validated-data-pipeline killer workflow. Design capture: `docs/parking-lot/server-execution-mode.md`.

Theme:

> A `serve` execution mode as the second consumer of the R4 lifecycle model.

Context:

- R4 delivered the lifecycle model + annotation binding model and named the **test lifecycle as the first consumer**. R8 adds the intended **second consumer: a server / request lifecycle** activated by a dedicated serve execution mode.
- This makes annotation-driven web config legitimate under the R4 rule that *annotations do not execute merely because they exist*: `@cors` / `@route` are inert descriptors the serve mode's lifecycle activates, exactly as `@test` is inert until `genia test` runs the test lifecycle.

Approved scope and tracking issues:

- a `serve` execution mode (`genia serve <file>`) alongside file / `-c` / `-p` / `test` modes
- a server lifecycle plan reusing the R4 contract — phases: startup (config + data + bind), per-request (route → handler → response, CORS applied here), shutdown (deterministic cleanup)
- inert annotations activated only by serve mode: `@server(...)` (config), `@route(method, path)` (handler discovery, same shape as `@test` discovery), `@cors(...)` (request-lifecycle cross-cutting)
- **bind-down principle:** annotations are sugar over existing primitives — `@route` → `route_request`, `@cors` → the R7 `cors` wrapper, `@server` → `serve_http`. No second mechanism (Core Surface Freeze).

Required issue path:

1. **#558 — E8-0: contract and execution-boundary reconciliation**
2. **#534 — E8-2: independently testable server lifecycle core**
3. **#535 / #536 / #537 — route, server-config, and CORS annotation bindings**
4. **#533 — E8-1: final `genia serve <file>` CLI integration**

Dependency order: **#558 → #534 → (#535, #536, #537) → #533**.

Excludes:

- a general application framework, plugin system, or DI container
- any annotation that executes outside a lifecycle (must stay consistent with R4)
- new language semantics or Core IR changes — serve mode is a host/runtime execution mode
- displacing R5 (native-test migration) or R6 (data-workflow hardening)
- documenting any of the above as implemented before it ships — `GENIA_STATE.md` remains authoritative

Exit criteria:

- `genia serve <file>` runs an annotation-declared REST service whose handlers never mention CORS, with preflight handled by the server lifecycle.
- The serve mode consumes the R4 lifecycle contract as its second implemented consumer; annotations remain inert descriptors bound by the lifecycle, not self-executing.
- R7 primitives are the sole mechanism the annotations bind to; no killer-workflow (R5/R6) work was displaced.

Agent guidance for R8:

- R8 is complete. Preserve its Python-reference-host-only boundary and its binding to the R7 primitives.
- Keep annotations inert and lifecycle-activated; do not introduce a self-executing annotation mechanism.

Final R8 disposition:

- #558, #534, #535, #536, #537, and #533 delivered the reconciled contract, lifecycle core, inert annotation bindings, and explicit `genia serve <file>` integration.
- #561 completed the non-blocking repository metadata and README release polish.
- `docs/releases/R8.md` provides the runnable headline example, and the release truth audit verified the exit criteria.
- R9 was explicitly activated after R8 completion; R8 remains closed.

---

## Release R9 — Value Templates & Representations

**Status: Complete.** E9-1 through E9-7 delivered the approved behavior, and
E9-8 completed the release truth audit. Implemented surfaces retain their
documented Experimental maturity.

Implemented foundation:

- E9-1 / issue #399: named reusable patterns are first-class callable Template values over the existing one-argument Outcome matcher contract.
- E9-2 / issue #570: ordered carrier facets and one-layer representation-aware matching reuse those Templates.
- E9-3 / issue #89: boolean refinement lifting and open ordinary-map shapes require listed fields, accept extras, and preserve the original map.
- E9-4 / issue #90: exact ordinary-map shapes require equal field sets and preserve ordinary map values without nominal Struct/layout behavior.
- E9-5 / issue #571: strict JSON decode/encode maps ordinary values through one outer `json` facet with normalized Outcomes and portable duplicate, number, Unicode, and nesting limits.
- E9-6 / issue #572: the closed JSON Schema structural subset compiles represented schema maps into ordinary callable Outcome Templates and rejects unsupported keywords explicitly.
- E9-7 / issue #573: an executable Outcome-aware pipeline proves composition of the JSON boundary, a JSON Schema-derived exact `Person` Template, representation-aware nested matching, and validated aggregation without adding semantics.

Theme:

> Give Genia a structural way to describe, refine, represent, and pattern-match values without introducing nominal type machinery.

R9 promotes the existing value-template design direction out of the parking lot
and unifies four related concepts:

- **Value** — what the data is.
- **Template** — the structural/refinement contract a value satisfies.
- **Representation** — semantically meaningful information about how a value is represented or carried across a boundary.
- **Pattern** — how Genia recognizes and destructures values, templates, and representations.

Delivered scope:

- value templates and structural compatibility without nominal wrapper hierarchies
- open and closed shapes, refinements, and template composition
- representation semantics, representation-aware pattern matching, and explicit preservation/propagation rules
- JSON as a representation of ordinary Genia maps, lists, and scalars, not a parallel JSON object model
- JSON Schema as a source of structural templates, initially limited to a useful structural subset; advanced or unsupported JSON Schema features remain outside R9 unless separately designed and approved
- JSON/schema matching as the proving boundary use case

The release model explains the following conceptual forms coherently:

```text
secret(x)
json(x)
json(Person(x))
```

Representations say how values are carried. Templates say what shape and
refinements values satisfy. Patterns may match both. `json(x)` and
`json(Person(x))` are implemented through named representation-aware Templates;
`secret(x)` remains a conceptual R10 use of the same carrier mechanism, not
implemented syntax or secret acquisition.

Excludes by default:

- a nominal type system or inheritance hierarchy
- a second JSON-specific value model
- a promise to implement every JSON Schema feature in R9
- silently promoting unrelated broad contract/refinement work beyond what this release needs

Exit criteria — met:

- Genia can explain `secret(x)`, `json(x)`, and `json(Person(x))` through one coherent representation/template/pattern model rather than unrelated special cases.
- JSON decoding yields ordinary values, the approved JSON Schema subset compiles
  ordinary Outcome Templates, and representation-aware matching composes with
  the existing matcher model.
- The executable R9 pipeline proves the boundary without nominal types,
  implicit coercion, broad contracts, or variants.
- Authoritative docs, specs/tests, roadmap, and composability matrix passed the
  E9-8 truth review.

Issue guidance:

- **#399** is the implemented E9-1 Template foundation.
- **#570** is the implemented E9-2 generic carrier and matching slice.
- **#89** is the implemented E9-3 refinement/open structural Template slice.
- **#90** is the implemented E9-4 exact/closed structural Template slice.
- **#571** is the implemented E9-5 JSON representation boundary.
- **#572** is the implemented E9-6 JSON Schema structural-subset compiler.
- **#573** is the implemented E9-7 composed JSON Template proving case.
- **#91** is later-release/follow-up contract work and is not an R9 blocker.
- **#92** is later-release/follow-up variant work and is not an R9 blocker.

---

## Release R10 — Configuration & Secrets ✓ COMPLETE

**Status: Complete. E10-1 through E10-8 delivered and audited.** Issue #586 approved the durable
R10 configuration/protected-value contract; issue #589 implemented the
Experimental provider/ordinary acquisition slice, issue #590 implemented
missing-only defaults plus explicit converter/Template composition, issue #591 implemented protected carrier acquisition/matching/transport, and issues #592 through #595 completed protected sinks, explicit declassification, cross-mode hardening, and the composed validated-pipeline proving case. Issue #596 completed the release truth audit and distillation. Follow-up behavior requires its own contract and phase gates.

Theme:

> Portable configuration acquisition and protected-value handling built on the R9 representation model.

R10 is the first major consumer of R9 representations. The earlier candidate
forms were:

```genia
model = @config("OPENAI_MODEL")
api_key = @secret("OPENAI_API_KEY")
```

Issue #586 rejected these forms because existing prefix annotations are binding
metadata, not expressions. The approved contract uses ordinary explicit calls
over an immutable provider snapshot, adds no syntax or Core IR node, and treats
the string argument as a configuration **key**, not the configured value.

Delivered scope:

- configuration lookup, source/precedence rules, missing values, and defaults
- conversion and validation at the host/environment boundary
- explicit acquisition across execution modes; annotation/config injection was rejected and remains deferred
- secret representation and representation-aware pattern matching
- secret-safe diagnostics, rendering, logging, output, and serialization policy
- explicit propagation rules for values derived from secrets

Matching or destructuring a secret must not implicitly declassify it. In the
conceptual pattern below, `x` remains protected:

```genia
value
  |> secret(x) -> ...
```

R10 uses the R9 representation model rather than an unrelated `Secret` class
hierarchy. The reserved protected facet cannot be constructed, matched, or
stripped through generic carrier operations; protected matching retains the
protected subject, sinks reject recursively, and explicit authority-gated
declassification is the only payload-revealing operation. See
`docs/design/r10-configuration-protected-value-contract.md`.

Exit criterion:

- Config and secret acquisition use the representation semantics established by R9, and ordinary matching, diagnostics, or rendering cannot accidentally expose secrets.

Issue guidance:

- **#585** is the completed R10 epic.
- **#586** is the completed E10-0 contract gate.
- **#589** is the implemented E10-1 provider/ordinary acquisition slice.
- **#590** is the implemented E10-2 defaults/conversion/Template-validation slice.
- **#591** is the implemented E10-3 protected-carrier/matching slice.
- **#592** is the implemented E10-4 protected rendering/sink-safety slice.
- **#593** is the implemented E10-5 explicit-declassification authority slice.
- **#594** is the implemented E10-6 cross-mode-hardening slice.
- **#595** is the implemented E10-7 composed validated-pipeline proving case.
- **#596** completed the E10-8 release truth audit and distillation.

Completion qualifications:

- Configuration/protected-value APIs remain Experimental.
- Shared conformance remains Partial and Python is the only implemented host.
- Completion does not claim absolute security, memory erasure, vault/rotation/authentication support, annotation injection, ambient providers, R11, or R12 behavior.

---

## Release R11 — AI Composition ✓ COMPLETE

**Status: Complete; E11-1 through E11-8 complete.** The Experimental
E11-1/E11-3 Python reference-host boundary provides text and R9-validated JSON
`model/4` over an explicit deterministic fixture and one explicit Google Gemini
direct-REST capability. E11-5/E11-6 provide the application-owned conversation
and validated-pipeline proofs, and E11-7 synchronizes runnable examples. Any
future or excluded material below remains unimplemented. See
`docs/design/r11-ai-composition-contract.md` for the approved boundary.

Theme:

> Make AI a natural participant in Genia's existing value, function, pipeline, Flow, and Outcome model.

Architectural rules:

- messages are values
- models are callables
- prompts are functions
- chains are pipelines
- tools are ordinary Genia functions plus contracts/metadata
- conversations are evolving state driven by a Flow of input events
- Outcome carries failure and absence

R11 must not create chain runtime classes, `Runnable` / `RunnableSequence`
equivalents, prompt or message class hierarchies, `AgentExecutor`-style
orchestration, or a second pipeline abstraction. One provider is sufficient to
prove ordinary model invocation. Credentials and configuration come through
R10, and structured model output uses R9 JSON/template/pattern machinery rather
than a separate AI validation system.

Conversation semantics do not own input acquisition:

```text
input producer -> Flow<UserInput> -> conversation evolution -> Flow<ConversationState>
```

Input producers may include terminal prompts, files and test fixtures, HTTP,
WebSockets, actor/message sources, generated input, or other Flow sources. The
same conversation implementation must work across them.

Current Genia implements `evolve(init, step)` as an unbounded Flow that emits
`init` and repeatedly applies `step(previous_value)`; it does not consume an
input Flow. Current `scan(step, initial_state, source)` is the closer existing
shape for evolving state from input events, with a step returning
`[next_state, output]`. A conceptual conversation therefore looks like:

```genia
chat_turn_step(state, input) =
  next_state = chat_turn(state, input)
  [next_state, next_state]

user_inputs
  |> scan(chat_turn_step, initial_chat)
```

This remains conceptual pseudocode because `chat_turn` is not a public helper;
the implemented application example defines its own step over `model/4` and
existing `scan`. An interactive terminal producer may use the current two-argument
`evolve(init, step)` shape to generate prompt events, but input production must
remain separate from conversation evolution.

`take_some_while` is not part of R11. The preferred eventual expression is
`take_while(some?)` if ordinary `take_while` semantics are designed to provide
the required bounded termination. `take_while` itself is not currently an
implemented Flow helper, so this remains a planned semantic gap rather than an
implemented example or a reason to invent a special-purpose helper.

R11 also demonstrates model use inside Genia's Outcome-aware validated
data-pipeline story through the implemented E11-6 proving case.

Exit criterion:

- Useful AI applications look like ordinary Genia composition, and conversation logic can consume different Flow-based input sources without changing the conversation implementation.

Approved sequence:

1. E11-1 — ordinary values, `model/4`, and deterministic fixture — **implemented (Experimental; Python fixture only)**
2. E11-2 — R9 structured output — **implemented (Experimental; Python fixture only)**
3. E11-3 — R10 boundary and one Python provider adapter — **implemented (Experimental; Python Gemini REST only)**
4. E11-4 — shared conformance and cross-mode hardening — **implemented (Experimental; Python fixture harness)**
5. E11-5 — Flow/`scan` conversation composition — **implemented (Experimental; application-owned ordinary state)**
6. E11-6 — Outcome-aware validated-pipeline proving case — **implemented (Experimental; deterministic fixture proof)**
7. E11-7 — release examples and truth sync — **implemented (documentation and runnable-example verification; no runtime behavior)**
8. E11-8 — final truth audit and distillation — **complete (no runtime behavior)**

The implemented Gemini adapter is one narrow provider proof, not a framework.
Streaming, model-call cancellation, automatic retry/fallback, tools/agents,
multimodal content, persistent memory, and general AI observability/evaluation
infrastructure are excluded. Retrieval, embeddings, grounding, and citations
remain R12. Later tickets require their own gates.

---

## Release R12 — Retrieval & Grounding ✓ COMPLETE

**Status: Complete; E12-1 through E12-9 complete.** E12-1 through E12-7 retain their Experimental implementation status. E12-8 is documentation/runnable-example verification and E12-9 is audit/distillation only.
Issue #641 approved the semantic boundary in
`docs/design/r12-retrieval-grounding-contract.md`. Each behavior slice still
requires its own complete phase workflow. This section is planning, not
implemented language behavior.

Theme:

> Complete production-quality RAG through general retrieval and grounding capabilities rather than a separate RAG framework.

R12 builds on R11. Its abstraction is **retrieval**, not `VectorDatabase`.

Approved contract scope:

- document and chunk values that preserve provenance
- chunking as ordinary Seq/Flow/library composition
- provider-neutral embedding capability
- a backend-neutral indexing/retrieval contract supporting replaceable vector, lexical, hybrid, SQL/pgvector, Databricks Vector Search, Elasticsearch, local-index, graph, and external-retrieval implementations
- reranking as ordinary composition
- grounded-context assembly with answer, sources, and evidence
- Outcome-aware failure handling

Conceptual composition:

```genia
documents
  |> chunk
  |> embed
  |> index

question
  |> embed
  |> retrieve
  |> rerank
  |> take(...)
  |> assemble_grounded_context
  |> model
  |> validate
  |> answer + sources + evidence
```

This is proposed composition, not implemented syntax or API. Retrieved chunks
must retain provenance rather than becoming anonymous strings too early. Genia
does not need to own or implement a vector database to complete R12.

Critical acceptance criterion:

- The embedding provider, retrieval backend, reranker, and generation model can each be replaced independently without restructuring the overall Genia application.

Replaceability is interface compatibility, not identical vectors, scores,
ordering, evidence, or answers across implementations. The approved sequence is:

1. E12-1 — document/chunk/provenance
2. E12-2 — unified corpus/query embedding fixture
3. E12-3 — indexing capability and opaque handle
4. E12-4 — retrieval capability and compatibility guards
5. E12-5 — provider reranking and provenance integrity
6. E12-6 — grounded context/answer composition with unchanged R11 `model/4`
7. E12-7 — R10 boundary, cross-mode conformance, and grounded proving case
8. E12-8 — release examples and implemented-truth synchronization — **implemented (documentation and runnable-example verification; no runtime behavior)**
9. E12-9 — release truth audit and distillation — **complete (no runtime behavior)**

E12-1 through E12-9 completed their per-ticket workflows in issues #643 through #651. The contract explicitly excludes a RAG/vector-store framework,
hidden query embedding, citation rendering semantics, retry/streaming, and
syntax/Core IR/lifecycle expansion.

---

## Release R13 — Configuration Resolution Ergonomics

**Status: Planned, not active.** This section records approved product direction,
not implemented language behavior. R13 refines the completed R10 configuration
surface without reopening R10 protected-value semantics.

Theme:

> Make configuration resolution concise, namespaced, and predictable while preserving explicit providers and protected-value safety.

R10 established the portable configuration/protected-value model. R13 addresses
the ergonomic friction that remains when real applications need several sources,
repeated common settings, multiple values with the same local name, and standard
host-backed provider patterns.

Candidate scope:

- concise composition of standard provider sources rather than verbose provider construction
- standard provider presets/adapters for common sources such as command-line options, environment snapshots, and `.env`-style files when host capability support is explicitly available
- deterministic provider precedence and fallback that remain visible in the configuration value/model
- namespaced or prefixed resolution so multiple settings such as `PORT` can coexist cleanly without global-name collisions
- dynamic resolution of provider prefixes/namespaces through ordinary values rather than one global ambient configuration namespace
- ergonomic ordinary-value and protected-secret lookup that reuses R10 conversion, Template validation, Outcome, and protected-carrier semantics
- clear separation between configuration key names, source/provider identity, namespaces/prefixes, and resolved values
- diagnostics that expose enough source/key context to be useful without exposing protected payloads

R13 must prefer library/value composition over new syntax. Candidate shorthand or
annotation forms are not approved merely by appearing in discussion; any public
surface must pass the Core Surface Freeze and the normal contract/design gates.

Architectural rules:

- R10 remains the semantic authority for providers, missing/default behavior,
  conversion/Template validation, protected carriers, sinks, and declassification
- R13 reduces call-site ceremony; it does not introduce a second configuration system
- standard providers must have deterministic precedence and explicit host/portable boundaries
- provider/source names and namespaces must be ordinary inspectable configuration metadata/values where safe, not hidden ambient state
- protected values remain protected through all new ergonomic resolution paths

Critical acceptance criterion:

- An application can define a small, readable configuration-resolution policy once and then resolve ordinary and protected values from multiple standard providers/namespaces without repeating provider plumbing or introducing ambiguous global names.

Explicit non-goals:

- changing R10 protected-secret semantics
- implicit global environment lookup as an uninspectable default
- dependency injection
- a new configuration annotation/macro system without a separately approved contract
- vault/rotation/authentication systems
- HTTP-specific configuration lookup; R14 consumes R13 rather than extending it ad hoc

---

## Release R14 — Composable HTTP Lifecycles

**Status: Planned, not active.** R14 is explicitly approved infrastructure work.
The release epic is **#619**. No R14 behavior is implemented merely because the
roadmap and issues exist.

Theme:

> Make lifecycle an execution-scope model that composes naturally, with inbound server requests and outbound HTTP operations as the first end-to-end proving case.

R14 extends the completed R4 lifecycle contract and R8 server lifecycle. A
lifecycle is an execution scope, not an application-wide mode. Long-lived parent
instances may own shorter-lived child lifecycle instances:

```text
execution
└── server
    └── request
        └── http-client
```

Core design rules:

- lifecycle definitions describe phases/scopes/policy
- lifecycle instances own active execution, resources, result/failure, and optional parent/children
- creating a child does not replace or mutate a global "current lifecycle"
- parent remains active while child work executes
- child completion returns control/result to the parent
- child failure does not implicitly terminate the parent
- child-owned resources finalize with the child; parent-owned resources remain parent-owned
- inherited context is readable according to contract but cannot be silently mutated by children
- annotations remain inert descriptors until an explicit lifecycle consumes/invokes them
- importing/loading an HTTP-annotated declaration performs no network IO

Outbound HTTP is the proving lifecycle consumer. One common HTTP operation model
must underlie method-specific ergonomics:

```text
HttpOperation {
  method
  base_url
  path
  headers
  query
  body
  response
}
```

The conceptual client lifecycle is:

```text
prepare
→ authorize
→ send
→ receive
→ decode
→ finalize
```

The lifecycle semantics belong to Genia. The Python reference host supplies only
the narrow outbound transport capability required to touch the network. Future
hosts must implement the same contract rather than redefining lifecycle/HTTP
behavior.

R14 may add declarative method annotations such as `@get` only after the common
operation and lifecycle model exist. Such annotations are metadata/operation
descriptors, not self-executing IO. Static policy belongs in descriptors;
dynamic request values remain ordinary Genia values.

R14 also integrates R10/R13 protected configuration with authorized HTTP
credential sinks. A protected API key may cross an explicitly authorized
transport header boundary without becoming an ordinary printable/serializable
value or requiring ad hoc application-level declassification.

Proving application:

- a Genia REST service accepts an array of canonical Bible references
- R13/R10 resolve a configured YouVersion base URL, Bible/version ID, and protected API credential
- an inbound R8 request creates one or more outbound HTTP client child lifecycle instances
- responses are decoded and returned as structured JSON
- automated tests use a controlled local upstream and fake credentials; CI does not depend on YouVersion or public network access
- the example proves composition only; it does not create Bible-specific language semantics or human-reference parsing

Approved R14 issue path:

1. **#620 — E14-0:** release contract and roadmap alignment
2. **#621 — E14-1:** lifecycle instance model and parent-child scope execution
3. **#622 — E14-2:** common HTTP operation representation contract
4. **#623 — E14-3:** Python host outbound HTTP transport capability
5. **#624 — E14-4:** outbound HTTP client lifecycle
6. **#625 — E14-5:** protected HTTP credential sinks
7. **#626 — E14-6:** declarative outbound HTTP annotations
8. **#627 — E14-7:** compose server request and outbound HTTP client lifecycles
9. **#628 — E14-8:** YouVersion Bible proxy proving application
10. **#629 — E14-9:** documentation sync and release example
11. **#630 — E14-10:** release truth audit and closure

Recommended dependency order:

```text
#620
  ↓
#621 + #622
  ↓
#623
  ↓
#624
  ↓
#625
  ↓
#626
  ↓
#627
  ↓
#628
  ↓
#629
  ↓
#630
```

Explicit non-goals:

- a general async/await model or scheduler
- actor supervision or distributed lifecycle execution
- WebSockets, SSE, or HTTP/2-specific semantics
- connection-pool configuration, retries, circuit breakers, or an auth framework
- dependency injection
- a second server/routing/CORS mechanism
- a second configuration, Template, representation, Outcome, validation, or error model
- self-executing annotations
- global mutable lifecycle state
- human-language Bible-reference parsing or YouVersion-specific language APIs

Critical acceptance criterion:

- A real Genia server request can execute protected/configured outbound HTTP as a child lifecycle, return the decoded result, correctly contain child failure/resource ownership, and leave the long-lived server lifecycle healthy.

---

## R8–R14 Sequence and Dependencies

The scheduling sequence is:

```text
R8  — Server Execution Mode
 |
 v
R9  — Value Templates & Representations
 |
 v
R10 — Configuration & Secrets ✓ COMPLETE
 |
 v
R11 — AI Composition
 |
 v
R12 — Retrieval & Grounding
 |
 v
R13 — Configuration Resolution Ergonomics
 |
 v
R14 — Composable HTTP Lifecycles
```

This ordering does not imply that every release is a strict technical dependency
of the next. The main semantic chain begins with R9: R10 consumes R9
representations; R11 consumes R9 structured values plus R10
configuration/secrets; R12 builds on R11 AI composition. R13 is a focused
post-R10 ergonomics release that preserves R10 semantics. R14 consumes R13's
configuration-resolution ergonomics and builds on the R4/R8 lifecycle/server
foundation while preserving R10 protected-value boundaries.

R8, R9, R10, R11, and R12 are complete. R11 and R12 APIs remain Experimental,
Python is the only implemented host, and shared/multi-host conformance remains
Partial. R13 and R14 remain planned.
R10/R11/R12 follow-ups require their own gates; R13 and R14
do as well.
Each later behavior slice requires its
own contract/design/test/implementation/documentation/audit gates; roadmap
placement is not implementation authority.

---

## Parking Lot / Later

These are valuable, but not part of the near roadmap unless explicitly promoted:

- actor system
  - includes actor lifecycle, supervision, and actor-oriented runtime expansion
  - keep out of R5 unless a narrow use case explicitly requires it
- browser playground runtime
  - useful as a future demo surface, not required for the first validated-data-pipeline release
- ants / simulation teaching demos
  - useful teaching material after the data-pipeline wedge is demonstrable
- value-template work outside the focused R9 structural/representation scope
  - R9 is complete; new Template work requires later-release or follow-up classification
- refinement / shape / contract / variant work beyond the subset required to prove R9
- validation DSL
  - do not create implementation tickets until helper-based validation proves insufficient
- multi-host implementation beyond contract scaffolding
- server mode
  - **Web ergonomics promoted to R7**, and the **serve execution mode promoted to R8** (Server Execution Mode — the second R4 lifecycle consumer, `@server`/`@route`/`@cors` bound to R7 primitives). Idea capture: `docs/parking-lot/web-backend-cfm-app.md` (R7) and `docs/parking-lot/server-execution-mode.md` (R8). Anything beyond those two remains parked.
- notebook mode
- parallel native test execution
- **#102** — broad scope; should be split into smaller targeted tickets or updated before use as a release tracker; do not use as a release blocker in its current form

---

## Post-R1 Issue Disposition

This section records the classification of R1-adjacent issues after R1 completion.

| Issue | Classification | Notes |
|---|---|---|
| #374 | **Closed / completed** | Delivered as part of R1. |
| #405 | R6 diagnostic-context hardening | Keep open; schedule in R6. |
| #393 | R6 diagnostics hardening | Keep open; schedule in R6. |
| #394 | Conditional / deferred | Keep open; promote when need is concrete. |
| #390 | R6 — CSV support | Keep open; schedule in R6. |
| #395 | R6 — Sheet landing zone | Keep open; schedule in R6. |
| #396 | R6 — after #395 | Keep open; depends on Sheet landing zone. |
| #363 | R6 — delivered | `row_get(row, column_name)` ergonomic row access shipped. |
| #364 | R6 — after Sheet landing zone | Keep open; schedule after #395. |
| #399 | R9 E9-1 — delivered | Minimal callable Template foundation implemented over Outcome matchers. |
| #87 / #89 / #90 | R9 — delivered | R9 epic, open-shape, and exact-shape work completed through the approved E9 sequence. |
| #91 / #92 | Later release / follow-up | Broad contracts and variants were not required by R9 and are not release blockers. |
| #102 | Needs split or update | Do not use as a broad release blocker; split first. |

If an issue listed above is already closed, do not reopen it.

Possible future generated-helper idea:

- record-derived `with_*` helper generation
  - possible future opt-in form: `@derive(quote(withers))`
  - generated helpers must be namespaced under the record/template
  - generated helpers must not create global `with_*` functions
