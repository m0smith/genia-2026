# Model B D1: ordinary module-completion projections

Status: **DESIGN ONLY — not implemented.** Bounded #1250 D1; no ordinary linking,
closed publication or new public observation. The [accepted B1 contract](pre-r29-default-open-and-immutable-binding-contract-DRAFT.md#54-b1-defining-name-replacement-before-completion-accepted)
and its §§2.1–2.2/5.1–5.3 govern intended behavior. STATE remains final implemented
authority. This document refines the [portable design](pre-r29-default-open-and-immutable-binding-design.md#53-completion-and-atomic-linking),
not its dispatch or extension-authority contract.

## 1. Purpose and scope

Prepare one private, completed projection of each directly exported original
module-declared ordinary callable. Preserve live groups while independently owning
the completed clause/provenance structure and three B1 metadata observations.
Capture after successful original source-module initialization, before cache
publication. Re-exports reuse original projections.

Exclude ordinary extend/use acceptance, view dispatch or coherence checks, E,
public snapshot reflection, new syntax/Core IR/wire/capability versions, generic
binding-generation history, whole-module immutability and module-loader redesign.
No annotation, matcher, guard, body or lifecycle runs merely to capture a projection.

## 2. Placement and file plan

The existing loader remains responsible for resolution, loading sentinels,
isolated module execution, exports and completed caching. Projection construction
is a private preparation step in that existing completion path, not a new loader.

| Later implementation location | Responsibility |
|---|---|
| `src/genia/environment.py` | Completion transaction and original local-slot metadata capture using existing writer synchronization. |
| `src/genia/values.py` | Backward-compatible private projection association on ModuleValue, excluded from repr/equality/export access; default empty for existing constructors/host modules. |
| New `src/genia/ordinary_completion.py` | Private record ownership, pure bounded metadata extraction and projection preparation; dependency direction toward existing IR/value types, no evaluator or linker import. |
| `src/genia/callable.py` | Read existing group/record ownership and retained grouped bodies; no changes to invocation, identity, clause append, dispatcher or trampoline. Add a narrow read helper only if required to avoid representation duplication. |
| Existing reflection helper surface | Share pure metadata-doc/summary selection with builtins if needed; do not call public doc/meta/help or change their precedence. |

No removed files. Parser, lowering schema, adapters, capability manifest and
conformance protocol require no implementation changes. Changes to existing writers
must be limited to making the specified capture coherent, not new write policy.

## 3. Ownership and internal interfaces

Names below are private implementation choices, not language APIs or serialized IR.

**CompletionProjection** owns: original callable identity reference; canonical
original module/name provenance; ordered completed clause descriptors; defining-slot
annotation-map value; projected-doc presence/text; effective-help presence/text and
summary metadata. Missing documentation is represented as absence, not rendered
text or a fabricated docstring. Source locations remain data, not formatted help.

**CompletedClause** owns: declaration ordinal and original arm ordinals/provenance;
shape and existing pure structural key; original header/body relationship and
retained grouped-case structure; source spans; lexical closure reference and
required invocation settings. Body/guard/header remain the existing IR vocabulary.
Do not flatten ordinary grouped bodies into independent candidates. The retained
case inside IrListTraversalLoop supplies original arms; cache/index order is never
semantic clause order.

**Read-only ownership discipline:** copy ordered containers and detach all mutable
record/IR syntax containers from live groups. The projection privately owns these
detached existing-IR trees and exposes no reference that can mutate them. Any later
execution-record materialization must return a fresh copy of syntax containers,
not lend the authoritative owned tree. Shape/key/provenance descriptors and public
read-only container access use immutable tuples/records. Host-local tests may probe
private state, but production callers receive no mutation capability. A frozen
outer dataclass or tuple of live GeniaFunction records alone is insufficient.

Use an explicit structural copy of known record/IR fields, not generic deepcopy,
pickle, user conversion, repr, or a second IR serializer. Preserve every legitimate
existing ordinary body, including host-only nodes such as shell stages; do not run
portable-IR rejection or add new source restrictions during module completion.
Copies preserve lexical Env/Ref/Cell/capability/callable identity and language-value
semantics. They do not deep-copy closures, execute lazy values or freeze referenced
resources. Syntax list containers are distinct from language payload values.

Metadata uses the existing persistent Genia value semantics. Own any host map/list
containers serving as projection structure; do not borrow a mutable binding-table
dict or group help map as authority. Preserve referenced language payloads shallowly.
Do not create a general immutable-value codec or change ordinary GeniaMap behavior.

**Association:** ModuleValue carries a private immutable tuple of `(callable,
projection)` associations, compared by callable identity (`is` in Python), not
callable equality/hash or `(module,name)` alone. The tuple retains strong references
for its module lifetime and is excluded from language equality/render/export access.
Original identities with equal diagnostic provenance never share snapshots. No
global registry or field installed on a live callable is needed.

Private preparation interface: successful module Env + detached export selection
and contribution table → fully prepared ModuleValue with its completion associations,
or exception. A read-only lookup by exact callable identity returns its existing
projection or absence, never synthesizes one from an alias. No source-visible API.

## 4. Accepted B1 extraction

For each directly exported ordinary group G originally declared in this module,
select its original local defining slot by G's owner provenance. Do not search
parents, use an alias binding map, follow the current slot value, or recover a
historical generation. A missing slot/map means an empty annotation map.

| Channel | Capture at original successful completion |
|---|---|
| Binding metadata | Slot's successfully attached map, independently of what value occupies the slot now. |
| Projected doc | String doc in that map; otherwise G's own inline doc; otherwise absence. Never ordinary doc lookup on replacement H. |
| Shared help | G's own effective help doc and summary metadata, with G-inline fallback independently of binding doc. Store facts, not rendered Markdown/help output. |

Before completion, a replacement's annotations in the original slot may change
G's projected binding doc. They do not thereby change G's shared help. An annotated
alias of G may change G's shared help but does not become its defining map.
Import reset clears the slot map; restoring G uses the current map with no metadata
resurrection. These are accepted B1 consequences, not additional design choices.

After completion, changes to slot maps, alias annotations, group records or shared
help leave the owned projection unchanged; existing ordinary calls/reflection
continue to see their separately specified live objects. Never substitute the
replacement callable's inline docs or freeze the live group.

## 5. Original identity, aliases and re-exports

Scan direct export values only, deduplicating exact ordinary callable identities.
An eligible original group requires actual declaration provenance and original
source-module ownership; an arbitrary host-created group, lambda, builtin or
collection containing a callable does not acquire interface authority.

For an imported/re-exported ordinary G, locate its original completed module in
this execution's existing completed cache, then its exact-identity association.
Reuse that same immutable projection reference; do not use re-export module's
slot maps, recapture live metadata or key a projection solely by an export alias.
An existing exact-identity association, established when G was directly exported
by its successfully completed original module, is the completion witness for a
re-export. Owner text or the presence of a same-named completed module is not that
witness. If no such association exists, preserve G as a normal ordinary export
without a projection; do not reject the module or manufacture interface eligibility.
This includes values escaped through Ref/Cell from a failed origin, an origin that
never directly exported G, and an old G after a retry cached a distinct G2 with
the same diagnostic provenance. Later re-export does not repair missing original
completion. Internal invariant tests must detect loss of associations that were
actually established, without imposing new validity errors on these legal values.

Repeated import returns the already completed ModuleValue and projection. Failed
origin initialization has no completed association; escaped ordinary values are
not invalidated and no E-style failed-callable lifecycle is introduced. A retry's
new original callable is a different identity, even with equal module/name text.
Host-module fast paths retain empty associations and existing loading behavior.

## 6. Completion transaction and error flow

The existing module name remains the canonical cache/sentinel key. Preserve its
current import resolution, cycle diagnostics and loader semantics; introduce no
waiting scheduler, fairness guarantee, retry policy or automatic cycle recovery.

1. Existing cache lookup/loading admission and source resolution remain in place.
2. Execute the module with the existing isolated Env and loading sentinel. No
   projection is published during user initialization or annotation evaluation.
3. On successful source execution, enter a single coherent completion critical
   section coordinated with the existing binding writer lock. Capture exports,
   contributions, original slot maps, group records and help facts from the same
   boundary. All operations there are pure bounded structural/data operations:
   no matcher/guard/body, autoload, renderer or locking public writer re-entry.
4. Prepare detached projection structures and ModuleValue privately; resolve
   re-export associations from already completed origins. All fallible preparation
   finishes before publishing any completed entry. Do not attach tentative
   projections to escaped groups or a process-wide registry.
5. Publish the fully prepared ModuleValue at the one existing completed-cache
   assignment. Release the completion critical section before any later user work.
   A cache hit therefore sees both normal exports and full private associations.
6. Existing finally removes only this attempt's loading sentinel. An exception
   before publication leaves no completed entry/projection for this attempt.

Python realization uses the existing non-reentrant binding lock for the coherent
capture/preparation/publication interval. Do not call methods that acquire it again.
Ordinary declaration/metadata writer mutations must stay under that same lock.
Lazy structural-key caches may be read/computed purely; their optimization state
is not authoritative snapshot data. No correctness argument relies on the GIL.
The private copy may scale with declared syntax; never hold the lock across user
evaluation. Do not add an optimistic retry loop that could repeat user work.

Cache-hit reads, loading admission and sentinel removal use short sections of
the same lock, so readers synchronize with the single publication. Source/path
resolution and source execution stay outside it; recheck cache/loading admission
after resolution before reserving the loading name. A loading name retains the
existing cycle/error path, not waiting. Cleanup removes only the sentinel owned
by this attempt. Host-module publication follows the same visibility boundary
without ordinary projections. These are synchronization details, not a new
successful-import result, automatic retry or general concurrent-loader guarantee.

This is atomic visibility of one module's completion, not a transaction over the
module's IO or other completed dependencies. On failure, keep already performed
effects and successfully completed dependency caches; discard only private candidate
state and this module's unpublished entry. A later explicit import follows existing
retry behavior and creates fresh attempt state. Snapshot/preparation OS/allocation
or internal errors propagate through existing host normalization; no new public
error category, validity restriction, rollback or automatic retry is introduced.

Concurrency preserves existing behavior when an import sees a loading sentinel,
including its existing cycle/error path; it does not wait for another loader.
The implementation must synchronize completion reads with publication without
putting source execution inside a global lock or promising thread-safe concurrent
module evaluation beyond the existing loader contract. Tests must deterministically
observe old/loading versus fully completed state, not assume timing or the GIL.

## 7. Acceptance matrix and later TEST inputs

These are design obligations, not new tests or executed D1 evidence.

| ID / original preflight | Acceptance | Evidence boundary |
|---|---|---|
| A1 / D1-01 | Success captures once before cache publication; a cache hit shares the original association. No visible half-built projection. | Internal loader/barrier tests; existing public import cache observations. |
| A2 / D1-02 | Live list/record/header/body/guard or returned execution-copy mutation cannot change owned syntax/key/order/provenance. Closure and Ref/Cell identities stay shared; grouped arms retain original order/pairing, including optimized retained cases. | Host-local structural/mutation/direct-IR tests; existing source/optimizer preservation specs. |
| A3 / D1-03 | Canonical binding-doc differs correctly from inline-help fallback; absent doc and all three maps remain independent. No renderer/autoload effects during extraction. | Internal construction assertions plus shared expressible metadata preservation. |
| A4 / D1-04 | Multiple aliases deduplicate G; re-export reuses original projection despite alias help mutation. An escaped failed-origin or never-directly-exported G has no projection and remains an ordinary valid export, even when a retry cached G2 with equal owner text. No recapture or inferred eligibility. | Internal identity assertions; existing alias/import specs; future D2 observable view tests remain separate. |
| A5 / D1-05 | Replacement preserves slot map; new replacement annotations affect G binding doc; H-inline never substitutes; import clears, restore does not resurrect; alias map affects only its allowed channel; equal owner text does not merge identities. | Internal B1 RED and direct-IR/source preservation; future shared linking/introspection RED. |
| A6 / D1-06 | Failure at each pre-publication preparation boundary leaves no local completed entry or leaked projection. Sentinel clears; prior effects/dependency caches remain; explicit retry uses fresh identities. No E-style invalidation. | Host-local failure injection and cache inspection, public failure/retry observations where expressible. |
| A7 / D1-07 | Self/mutual cycles retain existing errors; host fast paths unchanged; ordinary live aliases, reflection, immutable writers, metadata failure timing, module isolation and explicit-R20 semantics preserved. Ordinary extend/use still rejected. | Existing R16 module/ordinary/R20 specs and legitimate host internals. |
| A8 / D1-08 | All actual failures retained; exact SHA/tree and RED-before-code; no capability/adapter/IR changes; maintained code documentation and independent maintainability/truth reviews before merge. | Later implementation lifecycle, not design verification. |

Use the named preservation families in the original D1 preflight, especially
model-b-c-meta-three-channel-trio, meta-alias-no-copy, binding-doc-merge,
own-import-inert, own-extend-ordinary-rejected, own-use-ordinary-base-unchanged,
and existing R20 alias/view metadata and module-cache/cycle cases. Retain each
case's current requires; no blanket gating of old ordinary behavior.

No legal R16 source request exposes a private projection before linking. Internal
RED is therefore essential but cannot establish portable D2 conformance. Add shared
twins for new public preservation observations where expressible. Future D2 still
needs shared observable frozen-view/linking RED, atomic cross-unit validation and
all authority checks; D1 introduces none of those behaviors or evidence claims.

## 8. Portability and documentation

Portability zone is the accepted host-neutral completion contract; Python storage
and synchronization are a private realization. Core IR impact none; adapter impact
none; no capability claims change. Existing default_open_functions, multi_file_eval,
doc_help/open_functions and concern-specific requirements apply only to actual
shared cases. C++ remains bounded with owned runtime gaps and required syntax
genia-cpp#50; Python internal success is not C++ parity or a waiver. Other hosts
remain planned. Preserve source/direct-IR meaning, not Python class names as a
new portable wire contract.

STATE/RULES/REPL/README/AGENTS correctly describe A/B/C and absent linking/closed
publication; no current behavior changed by this design. Do not advertise D1 as
shipped. Future verified internal implementation should synchronize existing
architecture/code documentation while retaining the public unimplemented boundary.
No MCP language-knowledge impact until a verified public fact changes: no registry
or generated profile edit now. Use existing strict doc/profile checks for this
design; do not repeat A/B/C implementation audits.

## 9. Complexity and phase gate

Necessary complexity: one private module-owned association and an explicit ownership
copy boundary. Avoid global registries, a new binding-generation model, alternate
dispatch, generic immutable-IR serialization or changes to all module exports.
Acceptance requires checking actual copier/record fields and writer locking in the
later implementation diff, not trusting an outer frozen declaration.

This design is ready for focused independent review. After design acceptance and
an explicit next prompt, perform TEST ONLY: committed meaningful D1 RED and scoped
public-preservation cases, with exact base/environment and host applicability.
Implementation is a subsequent separately authorized phase citing that RED commit.
No code/RED, D2, E, #1251 closure or R29 is authorized by this document.
