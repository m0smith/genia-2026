# F2 P1-A characterization pre-flight — issue #1067

Baseline: `b3876890434182b4c18e0c512604aaf0678c86ef` (merged #1207).
Branch: `issue-1067-f2-p1-a-tests`. Owner: Codex for maintainer review.

## Scope and authority

Authorize only P1-A baseline tests for Python REPL `:env` and debugger globals/
locals, per the user request and PR #1207 comment `6132019249` on 2026-10-12.
Classification: unnumbered R20 follow-up, after R28 and before R29.
Authority: STATE §§0, 4, 7, 9; REPL README host-local commands; F2 P0 §§8/10
and merged P1 design §8. Characterize today's shared-root observations, including
module frames displaying entry/runtime globals. Do not activate approved future
D1/D2b/D3 behavior, change runtime code, add accessors, amend P0, merge, close
#1067, or begin P1-B/P2/P3/F3–F5.

## Maturity, boundary and portability (seven fields)

1. Maturity: N/A, test-only; no implemented semantic change.
2. Authority/boundary: Python host-local `:env` and debugger variable protocol;
   ordinary lexical functions/modules are setup, not new semantic authority.
3. Representation: existing scripted REPL text and debugger JSON events; no
   AST/Core IR/protocol schema or runtime value changes.
4. Shared evidence: Python tests are appropriate for colon commands/debugger
   inspection. Existing shared `repl`/module cases retain their authority;
   no new portable behavior needs a shared twin in this slice.
5. Applicability: existing `repl`/`debugger_stdio`/`multi_file_eval` vocabulary;
   no capability changes or conformance claims.
6. Hosts/evidence: Python only; C++ host-local command/debugger/module behavior
   is not claimed or changed. No new host gap or evidence format.
7. Truth synchronization/MCP: none; no behavior or user-facing example changes,
   so STATE/book/cheatsheets/registry/generated profile remain unchanged.

## Test plan and examples

Pin sorted REPL listing of runtime and user bindings, retained session state,
autoloaded functions, scripted prompt suppression and quit/EOF. Pin entry and
module named-function locals versus root globals through actual stdio debugger
sessions; inspect prelude function frames too. Fixtures are host-only tests.
Assertions distinguish current behavior from eventual isolated/unit-only views.
Run focused tests, appropriate lint, and both full regression partitions; report
environmental failures honestly. Characterization tests should pass on baseline;
do not manufacture failing semantics or add runtime code to make them pass.

## Complexity, impact and philosophy

Small test helpers exercise public host entry points; no scope architecture or
new parser machinery. Files: Python host-tool tests and this process record.
Drift risk: medium, because future phases must deliberately update baseline
expectations. Preserves minimalism, explicit boundaries and pattern-first
semantics; approved correctness infrastructure supports reliable composition.
No public function metadata changes or reference regeneration required.

## Phase and parity gate

Pre-flight → authorized TEST/characterization commit → focused test PR.
No implementation phase is authorized. Passing characterization tests are the
explicit P1-A exception to failing tests for new behavior; P1-B still requires
its own reviewed test/design gate. Existing design decisions are recorded in
the linked PR comment, not re-decided here. Python-only observations imply no
C++ parity. GO for P1-A only; reviewer: maintainer, decisions recorded
2026-10-12. Keep #1067 open.
