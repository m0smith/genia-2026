# R28 follow-up #1087 grounded evidence example audit

Status: PASS

Scope:

- Parent: #1087, narrow tested executable grounded-evidence example.
- Children: #1091 failing tests, #1092 implementation, #1093 docs sync, #1094 skeptical audit.
- Base: #1097 / #1090 contract-design merge `02dbae81`.

## Phase evidence

| Phase | Evidence |
| --- | --- |
| Tests | `fd1b435e` adds `tests/unit/test_r28_mcp_grounded_evidence_example.py`. |
| Implementation | `d89cbc8f` adds `examples/mcp/grounded_evidence.genia` and references the failing-test commit. |
| Docs | `d1b97147` updates `docs/mcp/demo.md`, `docs/strategy/roadmap/r25-r29.md`, `docs/releases/R28.md`, and `GENIA_STATE.md`. |
| Audit | This document records the #1094 verification result. |

## Claim check

The example remains a narrow executable example, not a new MCP tool, provider,
builtin, import path, authority, language feature, or R12 retrieval surface.

Verified claims:

- The example runs through existing `genia_run` policy and emits a JSON evidence
  package on stdout.
- The final Genia value is debug-only; machine-readable output uses explicit
  `json_encode` stdout.
- Selection is ordinary example code labelled
  `ordinary_example_selection_not_r12_retrieve`.
- Document ids and metadata are client-asserted and are not verified by Genia.
- Invalid records, duplicate ids, empty input, zero-width chunks, and no-match
  cases are represented as deterministic diagnostics.
- Source spans are codepoint offsets, including the `café` case.

## Static checks

The example was scanned for denied authority and private/runtime-only helpers.
No `import`, private underscore helper, process, shell, file, env, argv, stdin,
socket, HTTP, config, or secret authority appears in
`examples/mcp/grounded_evidence.genia`.

An overclaim scan found only existing historical text or explicit non-claims,
including the expected `not RAG`, `no C++ MCP`, and R12 discussion text. No new
unsupported claim was found in the files changed for this work.

## Regression

Focused checks:

```text
699 passed, 1 skipped
```

Command:

```text
UV_CACHE_DIR=/tmp/uv-cache uv run pytest \
  tests/unit/test_r28_mcp_grounded_evidence_example.py \
  tests/unit/test_r28_mcp_demo.py \
  tests/doc/test_roadmap_split.py \
  tests/doc/test_semantic_doc_sync.py \
  tests/unit/test_r28_release_gate.py \
  tests/unit/test_no_overclaim_language.py -q
```

Full non-loopback regression, outside the restricted sandbox:

```text
6161 passed, 25 skipped
```

Command:

```text
UV_CACHE_DIR=/tmp/uv-cache uv run pytest -n auto -q -m "not loopback"
```

Loopback regression, outside the restricted sandbox:

```text
31 passed
```

Command:

```text
UV_CACHE_DIR=/tmp/uv-cache uv run pytest -n auto -q -m loopback
```

The same non-loopback suite was also attempted inside the restricted workspace
sandbox and failed with process-tree and worker-lifecycle visibility failures.
The same loopback suite failed inside the sandbox with local socket
`PermissionError`. Both partitions passed once rerun with the OS capabilities
those tests require.

## Conclusion

PASS for #1094. The branch implements #1087 through the requested phase split
without changing runtime behavior, MCP tool surface, language semantics, or
historical acceptance evidence.
