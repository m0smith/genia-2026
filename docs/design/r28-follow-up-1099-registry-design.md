# Design: registry projection, generator, and drift gates (#1099, PR A)

Status: **design phase, 2026-10-07.** Implements
`docs/design/r28-follow-up-1099-registry-contract.md`. Design only.

## D1. Files

| File | Role |
|---|---|
| `docs/contract/semantic_facts.json` | add `mcp_language_profile` (contract C4) |
| `GENIA_STATE.md` | anchor markers (C2) and the `state:control-flow` statements (C5) |
| `tools/state_anchors.py` (new) | `parse_anchors(text)` -> span per anchor, enclosing `##` number, duplicate detection; reusable by PR B |
| `tools/gen_mcp_language_profile.py` (new) | `load_registry`, `validate`, `render_block`, `wire_projection`, `--check`/default write |
| `apps/mcp/mcp.genia` | hand constants replaced by the generated block (examples stay hand-written) |
| `tests/data/mcp_language_profile.golden.json` | wire snapshot captured from the pre-change implementation |
| `tests/doc/test_state_anchors_and_registry_sync.py` (new) | STATE-only checks: anchors, evidence text, crosswalk, workflow rule |
| `tests/unit/test_r28_mcp_language_registry.py` (new) | generator, projection vs live wire, probes, mutation tests, golden |
| `tests/unit/test_r28_mcp_language_profile.py` | replace the pasted `DISCOVERY_FACTS` oracle and the STATE-pin test with golden/registry-driven checks; keep all behavior tests |
| `tests/doc/test_semantic_doc_sync.py` | key-set/cap rule for the new key (C7) |

## D2. Generator

Pure Python, deterministic, stdlib only. `render_block` emits Genia map/list literals
(unquoted map keys, double-quoted strings, `nil`, `true`/`false`); it rejects any string
containing `"`, `\`, or a control character so no escaping rules are needed. The block
sits between `# >>> BEGIN GENERATED ... <<<` and `# <<< END GENERATED <<<` comment lines
in `mcp.genia`. `--check` compares the committed block with a fresh render and runs
`validate`; the default mode rewrites the block. `wire_projection(registry)` returns the
Python dict the wire must equal (excluding `name`, `contract_revision`, `examples`).

## D3. Validation rules (`validate`)

Closed vocabularies for status/maturity; unique fact ids; 12 facts in the committed
order; summary <= 256 bytes; discovery JSON <= 16,384 bytes; every fact has evidence;
every anchor cited exists in `state_anchors`; evidence anchors lie within a cited
anchor; probe and manifest names are non-empty strings. STATE-dependent checks
(fragments in span, crosswalk numbers, unique anchors) live in the doc test.

## D4. Probes and manifest checks

A probe is a named function in `tests/unit/test_r28_mcp_language_registry.py`, evaluated
with the Python reference host: `absent_forms_are_absent`,
`tail_recursion_constant_stack`, `pattern_dispatch_evaluates`, `pattern_kinds_evaluate`,
`supported_forms_evaluate`, `open_clause_rule`. A test asserts the set of probe names
referenced by the registry equals the set implemented, and runs each. Manifest checks
(`other_hosts_planned_not_implemented`, `browser_scaffolded`, `cpp_host_implemented`)
read `spec/manifest.json` `host_status` and `browser_runtime_adapter` as cross-checks of
host/browser facts; they are verification, not a source of the claim text.

## D5. Gates

1. `--check` as a pytest: committed block == fresh render; validate passes.
2. Wire == `wire_projection(registry)` and == golden snapshot (plain-file and launcher
   modes, both eras via existing helpers).
3. Mutation tests: a copy of the registry with a dropped/changed fact or evidence fails
   validate/`--check`; a hand edit inside the generated markers fails `--check`.
4. Editorial immunity: appending unrelated text and reordering other sections of a copy
   of STATE does not break anchor/evidence checks; removing an anchor marker or a
   pinned fragment does.
5. Crosswalk: each anchor's `legacy_section` equals its enclosing `##` number now.
6. Workflow rule present in the listed process documents.

## D6. Phasing in this branch

contract (done) -> design (this) -> failing tests (golden, new tests; they fail because
the registry, anchors, generator, and rule do not exist) -> implementation (registry,
anchors, generator, generated block) -> docs (STATE 9.50, MCP docs, conformance wording,
workflow rule) -> audit.
