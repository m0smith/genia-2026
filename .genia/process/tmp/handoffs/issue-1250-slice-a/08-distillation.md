# Slice A post-audit distillation and merge gate

PR #1260; branch `issue-1250-slice-a`; integration owner m0smith.
Distillation/verification: Codex. This is not an independent audit.

## Inputs, authority and exact commits

Read latest AGENTS first, the four roots in authority order, approved contract
#1255 (`a4730906a37450ae15aa2b595c69a1e9aa061e67`), merged design #1259
(`d85a56fa66d3369806ab9951b7572c79db98eba3`), run-change and distillation instructions.
The existing differently named phase handoffs supply the numbered template's
inputs: `issue-1250-slice-a-preflight.md` (00), approved contract/design documents
(01/02), `issue-1250-slice-a-red.md` (03),
`issue-1250-slice-a-implementation.md` (04), and
`issue-1250-slice-a-claude-handoff.md` plus `maintainability-closeout.md` and
`verification.md` (06 and correction evidence). `07-audit.md` records the actual
independent re-review; no absent audit or phase is invented from test success.

- Audited implementation/spec/documentation head:
  `c14fa139c64eee49cfdaf601f90bac34185454de`.
- Independent Claude decision: [comment 6272838043](https://github.com/m0smith/genia-2026/pull/1260#issuecomment-6272838043),
  **PASS WITH NON-BLOCKING FINDINGS**, superseding FAIL comment 6271452465.
- Canonical distillation and completed C++ observations:
  `fa0baa59cc124c7f4838cd13a5ba45fe8b2a09b2`.
- This handoff's enclosing commit is evidence-only. Its final SHA and exact-head
  CI run links are recorded in PR #1260's closeout description after pushing;
  the document cannot contain its own eventual commit SHA.

## Durable extraction and destinations

- `docs/releases/R28.md`: concise A7–A11 amendment history, including #1086,
  #1119 and #1084 decisions, anchors, fact counts and A11's absence-handling
  wording correction. A7's original catalogue already exists in the state record.
- `docs/state-record/r28-mcp-records.md`: the displaced 365-word STATE paragraph
  from the approved-design base, preserved verbatim under its own provenance
  heading. It is historical and non-authoritative, including then-rejected
  syntax wording; current STATE governs. No handoff/phase narrative moved to docs.
- `HOST_CAPABILITY_MATRIX.md`: honest 43-case observations and dedicated
  [genia-cpp #50](https://github.com/m0smith/genia-cpp/issues/50) ownership under
  #1250, preserving required capabilities and current-pin removal conditions.
- Existing C++ process ledger and raw appendix: actual outcomes, reasons,
  capability response, spec hashes, binary hash and source/pin limitations.

The four roots remain synchronized and unchanged by distillation. STATE is
exactly 43,000 words; its budget and semantic anchors are unchanged. No runtime,
syntax, Core IR, manifest/spec/test, capability or protocol change occurs here.
MCP language-knowledge impact: none; history relocation and host-gap tracking
do not change the currently verified language facts or assistant profile.
The semantic-fact registry and generated profile therefore require no rewrite.
This is the already-authorized post-audit phase of the existing preflight,
not a new semantic or host implementation project.

## Verification of the distillation tree

Commands used `UV_CACHE_DIR=/workspace/.cache/uv uv run --no-sync` in the existing
locked project environment. Build output stayed outside source-scanning paths.

| Check | Result |
|---|---|
| `python -m tools.spec_runner` | 874 passed / 0 failed / 0 invalid |
| `pytest -n auto -q tests/doc tests/unit/test_doc_style_sync.py tests/unit/test_cheatsheet_*.py` | 519 passed / 35 skipped |
| Supplemental selection adding all of `tests/spec`, including slow subprocess-protocol conformance | 812 passed / 35 skipped |
| Final STATE distillation, semantic-fact and anchor/registry tests | 244 passed / 34 skipped |
| `python -m tools.code_documentation --base-ref origin/main` | 9572 records / 2803 legacy gaps / 1 classified exclusion / 0 errors |
| `gen_mcp_language_profile.py --check`; `gen_function_docs.py --check` | Passed; profile/reference current |
| `lint_doc.py --scan-dir src/genia/std/prelude --require-coverage` | 24 files / 286 docstrings / 0 errors / 0 warnings |
| `ruff check .` | Passed |
| Fresh `stage_docs_for_mkdocs.py`, then `mkdocs build --strict` | Passed; all three new link anchors exist in generated output |
| Historical preservation/provenance checks | Exact displaced text retained; 43 unique ledger paths equal actual observations; all spec/binary hashes match; both advertised pins are ancestors; C++ checkout clean |
| Diff and authority checks | `git diff --check` passed; no changes since audited head in roots, registry/profile, src, hosts, spec or tests |

The correct prelude lint command above replaced an initial invocation lacking
`--scan-dir`; no checker was changed to resolve that invocation error.
Completed validation logs are attached in `distillation-evidence.zip` with SHA-256
checksums. The supplemental selection completed successfully before the evidence
cut; its result above includes the existing slow full-corpus Python subprocess
protocol assertion (856 PASS / 18 known host-only UNSUPPORTED / no failure classes). These are scoped runs, not a full local regression PASS. Earlier full
partition failures and bounded reruns remain in `verification.md` and the older
`audit-evidence.zip`; no failed run or assertion was erased or waived.

## Completed C++ evidence and remaining gap

All 43 selected cases were actually rerun, including the five newly added
`IrPatErr`/`IrPatNamed` IR cases. Result: **5 PASS / 38 UNSUPPORTED / 0 failure-class
outcomes**; the five added cases each returned explicit adapter UNSUPPORTED.
They require advertised-supported `ast_lowering`, so those requests reached the
adapter rather than being filtered by capability selection. Existing R16 APIs
and the unchanged 10-second timeout were used.

Available clean C++ source: `bb7c7474001f18e2e27fd94b7be9e9b725ba3473`.
Existing binary SHA-256:
`609d9807e5753574bd6e518ea4cad77c782b824ee45f9d154788e2853daf2df3`.
Advertised pin: `6402e668ae85a1e7efe94b3ac3d51f233b730ca4`; initial historical
ledger used `9ab0d3a323c9add045d47db1f476aead96af1e77`. Both are ancestors,
not current-head conformance evidence. The binary was not rebuilt; independent
source-build provenance is not certified. No full C++ suite or parity is claimed.
Required parser/lowering obligations stay required and unmet cases visible;
the optional-only gap registry is not broadened.

## Outstanding owners and dependencies (non-blocking for bounded Slice A)

| Finding/dependency | Owner, scope and completion condition |
|---|---|
| N4 validator/walker architecture | Codex implementation owner; m0smith integration, #1250. Separately design explicit per-node/child ownership before refactoring; retain malformed-IR, wire and traversal evidence. Decide sequencing before Slice B. |
| N5 prelude/documentation AST inventory | Codex / consumer implementer and documentation-gate owner, #1250 Slice B. Resolve before shipped Model B prelude declarations or immutable reserved-name enforcement rely on these consumers; no baseline masking. |
| N6 stray-question-mark diagnostics | Codex, #1250 parser follow-up. Pin negative shared cases and review correction before widening grammar; no syntax broadening here. |
| N7 unused parser helpers | Codex, separately scoped #1250 cleanup. Caller inventory, focused regressions and review must establish safe deletion. |
| N8 transitional rejection timing | Codex, #1250 Slice B design. Earlier ordinary effects persist; unsupported declaration children do not run. Decide and verify approved writer/publication timing before replacing rejection; no rollback promise. |
| N9 / required C++ gap | m0smith integration / C++ implementer, genia-cpp #50 under #1250. Remove only after bounded implementation and passing affected shared cases at a reproducible current pin. |
| MCP zombie-reaping discrepancy | m0smith integration, R28-H37 / #1250. Local PID 1 `tail` did not reap; independent environment and audited-head CI passed. Retain evidence, diagnose on comparable base/head environments, and keep cleanup assertions unchanged. |
| Later B–E / #1251 integration | Codex implementation / m0smith integration under #1250. Separate approved phases and prerequisite planning after Slice A merge; immutable execution, default-open dispatch, linking and closed publication remain unimplemented. #1250 stays open. |

## Final merge gate and cleanup

All six repository workflows must succeed on this handoff's exact final head:
CI (including fast non-loopback, loopback, shared specs and MCP acceptance), Docs,
Code documentation, LLM instruction validation, Host parity and Docker. Prior
`c14fa139` green runs are audit evidence only and cannot substitute for final-head
checks. PR-only deploy may be skipped. Exact final conclusions/run IDs and the
merge recommendation are recorded in the PR description after completion.
No merge, issue closure or Slice B start is performed by this distillation.

Complexity: minimal durable additions plus the specifically requested historical
archive and real outcome appendix. Phase logs, attempts, review sequencing and
environment diagnostics stay process evidence; none defines language semantics.
The handoff directory is safe to delete from a future working tree after merge:
durable facts are in canonical docs, deferred work remains owned in #1250 / C++
#50 and the PR closeout, and exact evidence remains retrievable from commit
history. It is retained/committed now at the user's explicit closeout request;
do not treat it as authority or a new reason to broaden this PR.
