# Issue #856 Audit — E21-4 R21 Documentation and Release-Example Truth Sync

Status: durable audit evidence for issue #856 (E21-4). Not a
source-of-truth document; `GENIA_STATE.md` remains final authority.

## Acceptance criteria verification

| Criterion | Result |
|---|---|
| every R21 claim is directly supported by merged code/shared evidence | PASS — `docs/releases/R21.md` cites only #853/#854/#855's already-merged, already-audited behavior; no forward-looking claim |
| no doc claims runtime Decimal arithmetic, Rational, explicit Float64, rendering, or JSON behavior not yet implemented | PASS — `docs/releases/R21.md`'s "What's next" section explicitly attributes those to R22/R23; the evaluator-compatibility-shim paragraph explicitly labels itself "documented compatibility work, not new R22 runtime semantics" |
| release page exists and examples are verified at the level supported by R21 | PASS — `docs/releases/R21.md` created; `tests/unit/test_r21_release_doc_examples_856.py` (7 tests) verifies every quoted example |
| source-of-truth precedence remains intact | PASS — every new/edited doc defers to `GENIA_STATE.md` explicitly |
| docs build/integrity checks pass | PASS — `uv run pytest tests/doc/ -q` shows only the pre-existing baseline failures tracked in #859 (7 of the 10; the other 3 are non-`tests/doc` native-test-runner/host-template files not exercised by this check) |
| no runtime behavior changes occur in this issue | PASS — `git diff main...HEAD -- src/` is empty |

## Regression evidence

- `uv run pytest tests/unit/test_r21_release_doc_examples_856.py -q` → 7 passed
- `uv run pytest tests/doc/ -q` → 206 passed, 7 failed (identical pre-existing baseline subset tracked in #859; zero new)
- `uv run python -m tools.spec_runner` → `Summary: total=721 passed=721 failed=0 invalid=0` (unchanged from #855 — no spec touched)
- `uv run pytest -n auto -q -m "not loopback"` → 4386 passed, 10 failed (identical pre-existing baseline set tracked in #859, zero new)

## Scope boundary check

- `git diff main...HEAD -- src/` → empty. No parser/lowering/evaluator/optimizer file touched.
- `git diff main...HEAD -- spec/` → empty. No spec case added or modified.
- Every doc edit is either (a) a new/updated section directly summarizing already-merged, already-audited #853/#854/#855 behavior, or (b) a status/index correction (roadmap "Planned" → "In Progress", missing R21 nav/index entries) that does not touch R19/R20's separately-tracked pre-existing gaps.

## Verdict

**PASS.** `docs/releases/R21.md` and every touched primary/roadmap doc
describe only implemented, merged, audited R21 behavior; R22/R23/R24
boundaries are stated explicitly rather than implied; no runtime code
changed; docs/regression evidence is fresh and shows no new failures.

## Doc Distillation

`docs/releases/R21.md` follows the established R19/R20 release-page
structure (status line, scope, syntax/behavior summary with small
examples, explicit non-goals, "what's next") rather than inventing a new
shape. `GENIA_RULES.md` section 8.6 is one concise bullet list, cross-
referencing `GENIA_STATE.md` rather than duplicating its prose. No further
trimming needed. Process artifacts remain under `docs/analysis/` as
durable history, matching #853/#854/#855's precedent.
