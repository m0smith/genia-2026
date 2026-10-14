# F2/P2-G evidence — documentation, audit and merge readiness (issue #1067, tracker #1229)

Phase: docs/audit. Branch `issue-1067-f2-p2-g-closeout`, stacked on `issue-1067-f2-p2-f-integration` (`91d454cd`).
Nothing merged; fallback not removed; no P3/R29 work.

## Final-tree validation (P2-G head, this tree)
| Run | Result |
|---|---|
| non-loopback, default | 6945 passed, 54 skipped, 0 failed |
| non-loopback, `GENIA_STRICT_MODULE_SCOPE=1` | 6945 passed, 54 skipped, 0 failed |
| loopback | 31 passed |
| shared specs (`tools.spec_runner`) | 825/825 passed |
| `tests/doc`, ruff, code-documentation check | pass (0 errors; one P2-F probe docstring gap fixed) |
Skip count differs from the P2-F log (60 vs 54) in this environment; no failure either way.
Trial merge of the whole stack into `origin/main` `1261ae27` (`git merge-tree`): no conflicts.

## Host parity (real run)
C++ host `m0smith/genia-cpp` `bb7c7474`: 825 total / 263 passed / 562 unsupported / 0 failure-class.
Python protocol host: 807 passed / 18 unsupported. `host_parity_gate` OK. The three new `f2-*` specs are
UNSUPPORTED on C++ (undeclared `multi_file_eval`/`doc_help`); the existing known gap #1018 covers
`multi_file_eval`. No new known-gap record was needed because the gate passed; C++ module isolation is P3/C++ work.

## N1 (attempt-record) resolution
`entry_declared_runtime_owned` is an attempt record: a failed `first(x)=x` or `open log(x)=x` can list the
existing runtime binding in the entry inspection view (REPL `:env`, debugger entry globals). Documented in
STATE; pinned by `tests/unit/test_f2_p2_g_closeout.py`. No API or behavior change. Recording after success is
a follow-up on #1238 and must flip that test.

## Closure recommendations (not executed)
- #1220, #1221: recommend closing only after the stack lands on `main`; evidence is in P2-C…P2-F records.
- #1230: stays open as an R29 planning gate (amendment A2); no first-on-main date is recorded.
  Measurement: 32 reads / 12 tests / 13 distinct pairs.
- #1238: stays open; N1 follow-up added; other dispositions as in the P2-F evidence.
- #1067/#1229: stay open; F2/P2 is not marked complete.

## Merge plan (maintainer executes; do not self-merge)
1. #1235 into `main`. 2. Retarget #1239 to `main`, merge. 3. Retarget #1240, merge. 4. Retarget #1241, merge.
5. Retarget #1242, merge. 6. Retarget the P2-G PR, merge. After each merge, re-run required checks
(ci.yml including the strict steps, host-parity, code-documentation). No conflicts expected against `1261ae27`;
re-check with a fresh trial merge if `main` advances.

## Maintainability review (#1233)
Source/test-logic change in P2-G: one test file only (guards, no production code). Determination in
`issue-1067-f2-p2-g-maintainability-review.md`.
