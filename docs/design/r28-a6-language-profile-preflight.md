# GENIA Change Pre-Flight: `genia_language_profile` MCP tool

Status: **Pre-flight for contract amendment A6** (R28 follow-up; epic #700). Follows the R26+ gate
(`docs/process/run-change.md`, `.github/ISSUE_TEMPLATE/genia-change-preflight.md`). `GENIA_STATE.md` remains
final authority; nothing here is implemented until the later phases land.

## Change identity

- **Change name:** MCP language-profile tool (adapter affordance)
- **Release / issue:** R28 follow-up amendment A6; no issue number assigned in the request (record one before merge)
- **Proposed branch:** `claude/friendly-turing-uamx3h` (session-designated; the `issue-<n>-<name>` convention is not applied)
- **Owner:** repository owner

## 1. Scope lock

**Includes:** one new native-Genia MCP tool `genia_language_profile` (no arguments) returning a fixed,
deterministic description of Genia's control-flow model inside the existing `genia.mcp.v1` envelope; the fourth
position in `tools/list`; contract amendment A6; test, fixture and documentation updates for the four-tool surface.

**Excludes:** any Genia syntax or semantics (no if-expression, no loop syntax, no parser/evaluator change); source-specific
parse/run diagnostic hints; resources, prompts, Streamable HTTP, C++ MCP; any new host capability or Python MCP logic.

## 2. Source of truth

- `GENIA_STATE.md` section 5 (case expressions, patterns, "Conditionals": no dedicated conditional keyword), section 8
  (tail calls), section 6/20 `open` function clauses, section 9.49 (R28).
- `GENIA_RULES.md` tail-call rules; `docs/design/r28-genia-mcp-contract-threat-model.md` sections 2.1-2.3, 18.
- **Conflict found and resolved:** the requested example text `gcd(a, 0) = a` / `gcd(a, b) = gcd(b, a % b)` is **not
  valid Genia** (`Invalid function definition parameter token '0'`). A literal first-parameter clause requires the first
  clause to be declared `open` (`GENIA_STATE.md` open-function clauses; `README.md` gcd example). The profile therefore
  carries the `open` spelling, which evaluates to `6`; shipping the invalid text would make the tool misinform assistants.

## 3. Feature maturity

Adapter-level, same maturity as the rest of the R28 MCP server (Python reference host only, local stdio). Not a language
feature and not portable Genia behavior.

## 4. Contract vs implementation

- **Portable contract:** none; this is an MCP application contract (section 8 of the R28 contract).
- **Python implementation today:** the whole tool lives in `apps/mcp/mcp.genia`; the Python host gains no code.
- **C++ implementation today:** none; no C++ MCP exists. No shared-spec change (no portable observable behavior).
- **Not implemented:** source-specific hints, resources, prompts, HTTP.

## 5. Test strategy

Core invariants: the four tools in contract order; capabilities `tools` agrees with `tools/list`; exact closed descriptor;
no-argument policy (`{}`/omitted accepted, anything else `-32602`); profile flags (`if_expression=false`, `loops=false`,
`recursion=true`); profile `contract_revision` equals the launch revision; deterministic across calls, eras, and namespace
modes; every profile example is run through direct evaluation and must evaluate as documented; no resources/prompts.
Host-specific: launcher/wire tests only (they are Python-host tests of an adapter, labeled as such).

## 6. Examples

`gcd(48, 18)` -> `6`; `fact(5)` -> `120`. Classification: MCP adapter output; the Genia snippets are portable Genia.

## 7. Complexity check

Revealing existing structure (the language model already in STATE) through the existing tool mechanism; no new mechanism.

## 8. Cross-file impact

`apps/mcp/mcp.genia`; contract section 19; `tests/fixtures/r28_mcp_helpers.py` and the R28 unit tests that pin the tool
set; `GENIA_STATE.md` 9.x R28 section; `docs/mcp/*`, `docs/releases/R28.md`, `docs/ai/LLM_CONTRACT.md`, README/REPL README
only where their MCP summary becomes stale. Drift risk: **Medium** (the "exactly three tools" wording is widespread).
Historical acceptance evidence (VS Code run records) describes the three-tool surface of that revision and is not rewritten.

## 9. Philosophy check

Preserves minimalism YES; avoids hidden behavior YES (fixed constant, no host input); keeps semantics out of host adapters
YES (native Genia, no Python); pattern-matching-first YES (the tool documents it); supports the validated-pipeline priority
N/A (assistant-facing discovery aid, approved as an MCP adapter affordance by the request).

## 10. Prompt plan

Phases are committed separately on this branch in order: pre-flight + contract, failing tests, implementation, docs, audit
(focused R28 suite + doc sync). Distillation is not run.

## 11. Host Parity / Conformance

Affected hosts: Python (MCP adapter only). Changes portable semantics: **NO**. No spec manifest or known-host-gap change.
Can one host merge before the other: not applicable.

## 12. GO / NO-GO

**GO**, with the example-spelling deviation recorded in section 2.
