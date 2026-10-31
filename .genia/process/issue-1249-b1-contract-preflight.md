# #1249 B1 contract-clarification preflight

Date: 2026-10-31 (America/Denver). Contract proposal only, not D1 implementation
or maintainer acceptance. Base main `def3860858e9bf066ffe5931d1cd820c51bd2e87`,
tree `380cdfb26fb976917f44ffbb0e45514b3c42807e`.

## Identity, scope and authority

- Change: original defining-binding metadata when an exported ordinary callable
  survives replacement of its defining name. Existing issue #1249, D1 owner #1250.
- Branch: `issue-1249-b1-binding-projection`; owner m0smith / authority maintainer.
- Includes policy comparison, precise proposed interpretation of Model B §5.3,
  positive/negative examples, focused independent review and reviewable contract PR.
- Excludes code, D1 RED, new public introspection, linking activation, E, R29,
  extension-authority expansion, capability/version changes and #1251 closure.
- Authority: current STATE §3/§4.7/module/reflection behavior; RULES §8.5.1;
  REPL/README Model B/module boundaries; AGENTS and token-efficient policy.
- Intended contract: approved Model B §§2.1–2.2/5.1–5.3; design §§5.1/5.3/6.1.
  Intake: #1249 comment6535928871 and #1250 comment6535922850. The D1 preflight
  remains NO-GO; this explicitly authorized contract task addresses its B1 decision.
- Maturity: Partial, proposed clarification of unimplemented D semantics. Existing
  Model B approval does not approve this new subsection or establish implementation.

## Seven-field portability analysis

1. **Zone:** host-neutral callable identity, lexical binding metadata, original
   successful module-completion projection; future D2 observable meaning.
2. **Core IR:** none. No new Ir* nodes/fields or version transition.
3. **Capabilities:** no change; future evidence uses existing multi_file_eval,
   default_open_functions, doc_help/open_functions where applicable. No internal
   snapshot capability and no downgrade of already-supported ordinary cases.
4. **Shared specs:** contract/examples only now; no test files. After acceptance,
   D1 needs internal projection RED plus shared public-preservation evidence;
   future D2 needs actual shared linking/introspection cases. Do not invent a
   snapshot API merely to expose internals through R16.
5. **Python:** existing mutable binding metadata and live aliases are inspected
   read-only. No implementation changed; no new ordinary linking claim.
6. **Adapters:** none; existing R16 protocol, comparator, deadline and taxonomy.
7. **Other hosts:** C++ Model B/module gaps and required parser/lowering #50 stay
   explicit; no new cross-host execution evidence or planned-host support claim.

## Current implementation versus prospective policy

Python A/B/C shipped; D ordinary linking and completion projections, and E closed
publication remain absent. C++ stays bounded and its older declared revision
means compatibility, not full-current conformance. No current behavior is changed.

Actual source evidence: environment.py `_write_binding` may replace/drop a named
metadata map; `assign` preserves/merges it; `merge_binding_metadata` updates the
current group's shared help map separately. builtins.py doc/meta/help implement
distinct binding/callable channels. Existing test_annotation_metadata.py contains
`test_rebinding_preserves_existing_metadata_and_new_annotations_override`; this
task reads it, does not rerun or claim new proof. Approved design defines binding
identity by lexical owner/name/policy, separately from callable/interface/view.

Compare: completion-time original lexical-slot metadata (smallest, but replacement
annotations may affect old callable's future projected doc); original-generation
metadata (isolation, but additional replacement/restoration/history rules); revoke
old alias eligibility (breaks alias/provenance contract); capture export alias map
(conflates channels and makes alias/export order meaningful). Proposed clarification
must make its choice explicit and remain pending maintainer acceptance.

## Validation, examples, complexity and risk

Expected validation: focused independent contract review of actual patch, precise
prospective examples (not executed D1 results), doc-sync/profile checks and strict
documentation build for changed contract/design. No runtime RED or repeated A/B/C
audits. All newly specified observations wait for subsequent authorized test phases.
No implementation-maintainability verdict is applicable to this contract-only diff.

Minimal example: `f(x)=x; a=f; g(x)=x+1; f=g` in a source module.
Realistic examples distinguish annotated replacement, import-alias reset, restoration
of the original callable, independent alias/shared-help annotations, and re-exports.
Classification: prospective portable contract cases, not current linking support.
Failure/negative cases retain no identity minting for lambdas/host values, no alias
append authority, no effects on completed projections and no import activation.

Complexity: reveal existing binding/callable distinction; no implementation scheme
chosen. Risk high: a tempting metadata-storage choice changes future doc/meta/target
observations. Material post-approval semantic changes require maintainer decision.
Likely files: approved-contract file (clearly delimited proposed subsection), a
design cross-reference and this process preflight; no production/test files.

## Documentation, MCP, philosophy and phase gate

STATE/RULES/REPL/README/AGENTS already accurately say D/E unimplemented; no edit is
justified to describe proposed B1 as shipped. MCP knowledge impact now: none;
do not change semantic registry/generated profile. After verified public behavior,
normal same-change truth/MCP synchronization applies. No new architecture or
generic binding-generation framework is authorized.

Minimalism YES; explicit behavior YES; semantics outside adapters YES; pattern-first
YES; indirect approved killer-workflow foundation for reusable pipeline callables.
Temporary handoffs stay ignored; durable process evidence stays under .genia/process
and GitHub, not a new docs/ report. Distill semantic text only into the existing
contract; preserve the old approved status and label the new proposal separately.

Current authorization: preflight → contract proposal → focused independent review
→ doc validation → publish proposed ruling and draft PR. No later design/TEST/code.
Host-first merge policy is not exercised: no host implementation or claims change.

**GO for a bounded proposed contract clarification and reviewable PR only.**
The semantic choice is not accepted by this preflight. D1 remains NO-GO until
explicit maintainer acceptance plus independent review, then a separate readiness
reassessment. No merge, issue closure, E or R29 authorization is implied.
