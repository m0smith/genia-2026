# Issue #1269 — Slice C, C0 capability-staging evidence

Process evidence only (not implemented-truth documentation). Parent #1250 (Model B);
Slice C #1269; pre-flight accepted on PR #1270 (`585f6aa`), integration authorization
[#1270 comment 6327837022](https://github.com/m0smith/genia-2026/pull/1270#issuecomment-6327837022).
Base: `main@6d50a36d23cc4b894f0456ee502deb5d7796e99b`.

## What C0 is

A prerequisite mechanism: `hosts/python/protocol_adapter.py::_VOCABULARY_ONLY_CAPABILITIES`
lets the Python protocol adapter advertise a capability that is already in the
`spec/manifest.json` vocabulary as `unsupported` (an existing protocol status). The
external-host gate (`case_is_applicable`) then reports requiring cases `unsupported`
without invoking the adapter.

**The override is empty in production.** No capability is staged, no capability is
added to the manifest, `default_open_functions` does not exist, and no default-open
behavior is implemented. C0 is not RED and not GREEN. Unknown names in the override raise
`ValueError`; they are never added to the vocabulary.

## Evidence (all on this branch; exact commands)

Baseline taken from an unmodified `origin/main@6d50a36` worktree.

| Check | Command | Result |
|---|---|---|
| Pre-C0 map captured | `uv run python -c "...; _python_claimed_capabilities()"` on base | 35 names: 34 `supported`, `shared_spec_runner` `partial`; embedded verbatim in the C0 test |
| Focused unit tests | `uv run pytest tests/unit/test_python_protocol_adapter_c0_capability_staging_1269.py tests/unit/test_python_protocol_adapter_762.py tests/unit/test_spec_runner_capabilities.py tests/unit/test_host_parity_gate.py -q` | 78 passed (67 baseline + 11 new) |
| External-host parity (unmodified) | `uv run pytest tests/spec/test_python_protocol_adapter_parity_762.py -q` | 1 passed (`unsupported == 18`) |
| In-process runner | `uv run python -m tools.spec_runner` | base and C0: `total=901 passed=901 failed=0 invalid=0` |
| External Python host | `uv run python -m tools.spec_runner --host "<venv python> -m hosts.python.protocol_adapter" --host-timeout 30` | base and C0: `total=901 passed=883 failed=0 unsupported=18 protocol_error=0 crash=0 timeout=0 invalid=0`; per-case output identical |
| Docs | `uv run pytest tests/doc -q -n auto` | 397 passed, 35 skipped |
| Whitespace | `git diff --check` | clean |

R20 capabilities `open_functions` and `multi_file_eval` remain `supported`; applicability
is asserted unchanged.

## Scope and exclusions

No shared-spec YAML, `spec/manifest.json`, runner/comparator, known-gap policy, protocol
or wire schema, `model-b-not-implemented` behavior, interpreter/parser/evaluator/
optimizer/Core IR/dispatcher, or implemented-truth documentation (`GENIA_STATE.md`,
`GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, semantic facts, MCP profile)
changed. MCP language-knowledge impact: none — C0 changes no Genia language knowledge.
Python affected (adapter advertisement only); C++ unaffected.

Independent implementation review is required before C0 is accepted. A passing C0 does
not authorize RED; RED remains subject to the separate decision and conditions R1–R5.
