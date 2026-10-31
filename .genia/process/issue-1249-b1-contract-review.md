# B1 proposed contract decision and focused review

2026-10-31 (America/Denver). Existing #1249; D1 #1250. Base main
`def3860858e9bf066ffe5931d1cd820c51bd2e87`.
Preflight `3ffa28e5`; proposed contract/design
`00f92661da8f0a61e8c7ad90e7b281c745e4e032`, tree
`c82b06a07c4933943c7451420a4088a66a331e44`.

## Compared policies / recommendation

| Policy | Compatibility, identity and future D2 consequence | Disposition |
|---|---|---|
| P1: original lexical-slot metadata at successful original completion | Keeps existing lexical binding/callable distinction; no history of replacements. Original G retains alias eligibility/provenance; replacement annotations in its defining slot can affect projected binding doc before completion. Shared help and inline fallback remain G's. | Recommend as the smallest coherent explicit choice. The surprising doc consequence must be accepted, not hidden as implementation detail. |
| P2: original callable-generation metadata | Isolates old G from annotations on a replacement value, but requires new ownership/history rules: when a generation ends, what is retained, and what restoring G or reusing a name means. These rules are not settled by the approved contract. | Viable only with a larger separately approved semantic decision; not the minimal B1 clarification. |
| P3: revoke eligibility unless original spelling still names G | Avoids capture questions by making saved/exported aliases lose interface eligibility because another binding changed. | Reject: conflicts with retained alias/provenance direction and changes extension eligibility. |
| P4: snapshot export/re-export alias metadata | Different aliases can carry different maps; selection of one would conflate channels and make export spelling/order significant. | Reject: contradicts original defining-binding projection and re-export rules. |

No current runtime behavior is changed by this recommendation. Future D2 still
needs all original authority/completion/selection/coherence checks. No alias grants
authority to append clauses, and no callable inherits identity from a spelling.
P1's precise prospective examples and no-resurrection/import/shared-help rules
are in proposed contract §5.4, not new tests or shipped-language claims.

## Focused independent contract review

Reviewer: `/root/acceptance_review`, separate agent; authored none of the patch,
ran no tests and made no edits/branches/publication. Reviewed actual base-to-head
patch and relevant existing source/contract at exact contract head `00f92661`.

**PASS, no blocking findings.** Verified retained original G identity/provenance;
completion-time map from original local slot; projected-doc fallback only to G's
inline, never replacement-value doc lookup; independent G shared help; explicit
replacement/import/restoration/annotation consequences; no authority/identity
minting by spelling. Examples agree with inspected ordinary writer behavior.

P2 requires generation-history semantics; P3 conflicts with alias provenance;
P4 conflates channels. P1 is the smallest coherent recommendation with its tradeoff
disclosed. Approval exception banner and design cross-reference correctly retain
pending maintainer acceptance and D1 NO-GO. PASS means coherent proposal, **not**
approval of the semantic choice, implementation, merge, D1 advancement or R29.

This is coordinator transmission of attributable independent agent review, not
author self-approval or a separate GitHub maintainer's approval.

## Validation and exact limits

Existing documentation checks only, using the existing project venv via
`UV_PROJECT_ENVIRONMENT=/workspace/genia-2026/.venv`, writable
`UV_CACHE_DIR=/workspace/.cache/uv`, this checkout's src on PYTHONPATH:

```
uv run --no-sync pytest -q tests/doc/test_semantic_doc_sync.py tests/doc/test_state_anchors_and_registry_sync.py tests/doc/test_portability_contract_sync.py
uv run --no-sync python tools/gen_mcp_language_profile.py --check
uv run --no-sync python tools/stage_docs_for_mkdocs.py
uv run --no-sync mkdocs build --strict
git diff --check
```

Results at `00f92661`: **244 PASS / 34 existing skips** in0.64s; profile check,
staging and strict documentation build PASS (6.94s); whitespace PASS.
Runtime/host/spec/test files, five root authority/instruction files, guarded
registry and generated MCP profile are unchanged. Raw local check logs retained
at `/workspace/work/1249-b1-evidence/`; these are documentation verification, not
D1 RED/GREEN, a full implementation audit, host-conformance rerun or causal
explanation of the preserved seven historical timeouts.

This final evidence file is process-only; it does not modify the independently
reviewed contract/design content. No repeated full Slice C audit or new tests.

## Contract gate / next action

**GO to publish P1 as a proposed ruling in a focused reviewable PR; acceptance is
pending. D1 remains NO-GO.** Maintainer should explicitly accept/reject the
completion-time-slot policy, including replacement-annotation consequences.
Only after acceptance may the D1 preflight be reassessed against that ruling.
No D1 readiness reassessment, design/RED/code, E, issue closure or R29 in this task.

Existing STATE/RULES/REPL/README/AGENTS correctly describe A/B/C and absent D/E;
there is no justification to describe this proposal as shipped or change the
language profile. No implementation-maintainability verdict is applicable.

Efficiency: one coordinator and one read-only independent reviewer; focused
existing doc checks only. Token usage, savings and review time not measured.
