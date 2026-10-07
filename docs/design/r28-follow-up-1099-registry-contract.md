# Contract: governed MCP language-profile registry (#1099, PR A)

Status: **contract phase, 2026-10-07.** Approved direction:
`docs/design/r28-follow-up-1099-state-distillation-mcp-sync-preflight.md` (review
decision section). This contract defines behavior of the governance mechanism only. It
adds no Genia language semantics, parser/evaluator/Core IR/builtin/host-capability
behavior, MCP tool, transport, limit, or security boundary, and it changes no
`genia_language_profile` wire byte. `GENIA_STATE.md` remains final authority; the
registry is a guard and projection source, never a definition of the language.

## C1. Chain of authority

```text
GENIA_STATE.md            semantic authority (prose) + semantic anchor markers
      │  evidence: text fragments located by anchor
      ▼
docs/contract/semantic_facts.json   key `mcp_language_profile`
      │  structured facts: stable id -> anchors -> evidence
      ▼
tools/gen_mcp_language_profile.py   deterministic projection (+ --check)
      ▼
generated block in apps/mcp/mcp.genia  ->  genia_language_profile (wire, unchanged)
```

Rules: (1) a fact is identified by its stable semantic `id` and its anchors, never by
prose; (2) STATE fragments, executable probes, and machine-truth cross-checks are
*evidence*; (3) the registry cannot make a claim STATE does not make; (4) `mcp.genia`
contains no hand-maintained copy of any registry-governed claim.

## C2. Semantic anchors in `GENIA_STATE.md`

An anchor is one line `<!-- anchor: state:<name> -->` placed on the line immediately
after a `##` or `###` heading (blank lines allowed). `<name>` is lowercase
`[a-z0-9-]+`. The anchor's **span** is that heading through the line before the next
heading of the same or higher level (a `##` span includes its `###` children). Anchors
are unique, independent of heading numbers and titles, and must survive STATE
reorganization (they travel with their section). The initial set:
`state:host-status`, `state:browser`, `state:conformance`, `state:execution-model`,
`state:syntax-forms`, `state:open-functions`, `state:pattern-matching`,
`state:control-flow`, `state:tail-calls`, `state:mcp-macos`, `state:mcp-surface`,
`state:mcp-language-profile`.

## C3. Legacy section crosswalk

The A7 wire value `state_sections` stays byte-identical. The registry holds an anchor
table `state_anchors: {anchor: {legacy_section: "<number>"}}`. A fact's wire
`state_sections` is `[state_anchors[a].legacy_section for a in fact.anchors]`, in
order. While STATE is not reorganized, each `legacy_section` must equal the number of
the `##` heading enclosing the anchor; after a reorganization the legacy value is
frozen and the crosswalk is the only place that records the divergence.

## C4. Registry shape (`mcp_language_profile`)

Additive top-level key in `semantic_facts.json`; the 22 sentence facts are unchanged.

- `state_anchors` — the crosswalk of C3.
- `language` — governed A6 members: `control_flow`, `supported_forms`, `patterns`,
  `absent_forms`, `idioms`, each `{value, evidence}`. (`name`, `contract_revision`,
  and `examples` are adapter vocabulary or runtime data and are not governed here; the
  examples stay native and are proven by evaluation.)
- `discovery` — `{coverage, facts}` where each fact is `{id, scope, status, maturity,
  summary, anchors, evidence}` with exactly the A7 closed vocabularies (status in
  `implemented|partial|planned|scaffolded|unsupported`; maturity null or
  `Experimental|Partial|Stable`; `summary` at most 256 UTF-8 bytes; the discovery JSON at
  most 16,384 bytes). `summary` is MCP-owned phrasing of the anchored claim.
- `evidence` — a non-empty list of items: `{"kind": "state_text", "anchor", "fragment"}`
  (fragment must occur in the anchor's span; the anchor must lie within a cited anchor
  of the fact), `{"kind": "probe", "name"}` (a named executable probe), or
  `{"kind": "manifest", "name"}` (a named cross-check against `spec/manifest.json`).

Language-claim text fragments must be anchored in language sections
(`state:control-flow`, `state:pattern-matching`, `state:tail-calls`,
`state:open-functions`, `state:syntax-forms`), never only in an MCP section.

## C5. STATE statements required by this change

`state:control-flow` states, independent of any MCP section: no `if` expression or form
exists; no dedicated loop syntax (`while`, `for`) exists; repetition is expressed by
recursion, with tail calls optimized in tail position. These describe existing,
already-probed behavior only.

## C6. Projection and wire invariants

The generated block defines `LANGUAGE_CONTROL_FLOW`, `LANGUAGE_SUPPORTED_FORMS`,
`LANGUAGE_PATTERNS`, `LANGUAGE_ABSENT_FORMS`, `LANGUAGE_IDIOMS`, and
`LANGUAGE_DISCOVERY` between marker comments. Output of `genia_language_profile` is
byte-identical to the pre-change output in every era and namespace mode; the four-tool
surface and `genia_capabilities` are unchanged. `--check` fails if the block differs from
a fresh projection or any registry rule is violated.

## C7. Guard-file rule

`semantic_facts.json` keeps its role as a selective cross-document drift guard. Its
string facts stay at most 22 (a deliberate cap); the single non-string key is
`mcp_language_profile`. `docs/architecture/executable-semantic-conformance.md` states
that this key is a guarded projection source, not a second language definition.

## C8. Future-change rule

Every implemented semantic change answers: **does this change affect knowledge an MCP
client should know about Genia?** If no, record "none" with a reason. If yes, the same
change updates STATE, the registry entry (and evidence), regenerates `mcp.genia`, and
passes the profile tests. The pre-flight template, `docs/process/00-preflight.md`,
`05-doc.md`, `06-audit.md`, `run-change.md`, `AGENTS.md`, `docs/ai/LLM_CONTRACT.md`, and
`.github/copilot-instructions.md` carry this rule; a doc-sync test enforces it.

## C9. Non-goals

No change to STATE size or structure beyond anchors and the C5 statements (PR B). No
runtime JSON or Markdown reading by the MCP server. No new tool, resource, prompt,
host capability, or `spec/` change. No A8 wire amendment.
