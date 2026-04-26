# Issue #162 — Value-vs-Flow Classification (Deferred Slice) Audit

**Phase:** audit
**Branch:** issue-162-value-flow-classification
**Issue:** #162 — Stdlib Phase 1 Normalization (deferred slice: value-vs-Flow classification)

---

## Verification Checklist

| Check | Result |
|---|---|
| `uv run python -m tools.spec_runner` — 95 specs pass, 0 invalid | PASS |
| `uv run pytest -q` — 1404 tests pass | PASS |
| All 4 new spec YAML files present and well-formed | PASS |
| All 4 spec names registered in `test_spec_ir_runner_blackbox.py` | PASS |
| `GENIA_STATE.md` classification model present (lines 991–1000) | PASS |
| `GENIA_STATE.md` eval coverage description updated (line 147) | PASS |
| `GENIA_STATE.md` flow coverage description updated (line 130) | PASS |
| No interpreter changes (`src/genia/interpreter.py` unchanged) | PASS |
| No prelude changes (`src/genia/std/prelude/` unchanged) | PASS |
| Branch scope clean: only docs, specs, tests, and phase artifacts changed | PASS |

---

## Phase Trail

| Commit | Phase | Description |
|---|---|---|
| `199f2da` | preflight | Inventory all public prelude functions; identify four misuse-risk zones |
| `d94531e` | spec | Add four boundary-error YAML spec cases; record map/filter hybrid finding |
| `e4288dd` | design | Confirm no-op implementation; plan test + docs changes only |
| `b484617` | test | Register four spec names in blackbox discovery assertions |
| `a9d3f68` | feat (no-op impl) | Confirm all four errors already enforced; zero interpreter changes |
| `182e8da` | docs | Update GENIA_STATE.md spec coverage descriptions |

---

## Scope Invariants Confirmed

- No runtime behavior was changed.
- No prelude function semantics were changed.
- No new language features were introduced.
- `GENIA_STATE.md` classification model (lines 991–1000) was already accurate before this slice; no rewrites required.
- `docs/cheatsheet/piepline-flow-vs-value.md` was already accurate; no changes needed.
- All four new spec cases test existing error behavior — no new behavior was added to make them pass.

---

## Key Finding (recorded for history)

`map` and `filter` are **intentionally hybrid**: when called with a `GeniaFlow`
as the second argument, a special interpreter override at `interpreter.py:4652–4684`
short-circuits Genia body resolution and returns a new `GeniaFlow` directly.
This is correct and by design — no boundary error spec was added for
`map(f, flow)` or `filter(f, flow)`.

---

## Files Changed

| File | Change |
|---|---|
| `spec/eval/each-on-list-type-error.yaml` | new — `each` given a list → `each expected a flow, received list` |
| `spec/eval/reduce-on-flow-type-error.yaml` | new — `reduce` given a Flow → `reduce expected a list as third argument, received flow` |
| `spec/eval/first-on-flow-type-error.yaml` | new — `first` given a Flow → `No matching case for function first/1` |
| `spec/flow/count-as-pipe-stage-type-error.yaml` | new — `count` as pipe stage → pipe-mode stage error |
| `tests/test_spec_ir_runner_blackbox.py` | +4 names in discovery assertions |
| `GENIA_STATE.md` | 2-line update to spec coverage descriptions |
| `docs/architecture/issue-162-value-flow-classification-{preflight,spec,design,impl,audit}.md` | phase artifacts |

---

## Verdict

**PASS**

All four boundary error cases were already enforced by existing runtime guards.
The slice correctly documents this surface with shared specs and updates
GENIA_STATE.md. No scope drift. No stale claims introduced.
