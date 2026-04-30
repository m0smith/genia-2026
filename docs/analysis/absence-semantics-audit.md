# Absence Semantics Audit

This document audits the current `nil` / Python `None` / `none(...)` behavior in the Genia codebase before any further absence-semantics redesign work.

It is intentionally descriptive.
It does not propose new syntax, automatic lifting, or a pipeline redesign.

Authority order for this audit:

1. `GENIA_STATE.md`
2. verified runtime behavior in `src/genia/interpreter.py`
3. current tests
4. documentation truthfulness updates made in this phase

---

## 1. Current behavior summary

### `nil`

- `nil` is still accepted as surface syntax.
- At runtime it normalizes immediately to `none("nil")`.
- Lowering reflects that normalization:
  - expression `nil` lowers to `IrOptionNone(IrLiteral("nil"), None)`
  - pattern `nil` lowers to `IrPatNone(IrPatLiteral("nil"), None)`
- Quoted `nil` also becomes the normalized absence value, not a separate runtime `nil` object.
- Pair-built lists and quoted lists still use `nil` as the teaching/source-level terminator spelling, but the runtime value is the normalized `none("nil")`.

Verified in:

- [interpreter.py](/Users/m0smith/projects/genia-2026/src/genia/interpreter.py)
- [test_option.py](/Users/m0smith/projects/genia-2026/tests/test_option.py)
- [test_pairs.py](/Users/m0smith/projects/genia-2026/tests/test_pairs.py)
- [test_quote_symbols.py](/Users/m0smith/projects/genia-2026/tests/test_quote_symbols.py)

### `none(...)`

- `none`, `none(reason)`, and `none(reason, context)` are one runtime absence family.
- `none` is shorthand for `none("nil")`.
- Runtime constructor validation is real today:
  - `reason` must be a string
  - `context` / metadata must be a `GeniaMap` when present
- `some(value)` is the explicit present-value constructor.
- Present normalized legacy `nil` values therefore appear as `some(none("nil"))`.

Verified in:

- [interpreter.py](/Users/m0smith/projects/genia-2026/src/genia/interpreter.py)
- [test_option.py](/Users/m0smith/projects/genia-2026/tests/test_option.py)
- [test_option_semantics.py](/Users/m0smith/projects/genia-2026/tests/test_option_semantics.py)

### Python `None`

- Python `None` is still used internally in several host/runtime code paths as a sentinel.
- At user-facing runtime boundaries it is usually normalized to `none("nil")` through `_normalize_nil(...)`, `_python_host_to_genia(...)`, or formatting helpers.
- Host interop converts any Genia `none(...)` to Python `None`, which discards reason/context metadata.
- Host interop converts Python `None` back to `none("nil")`.

This means the host bridge currently preserves “absence happened” but does not preserve structured absence metadata.

### Propagation in ordinary calls

- Ordinary function calls short-circuit on `none(...)` arguments.
- When any evaluated argument is `none(...)`, the call returns that same `none(...)` and does not evaluate the callee body.
- Exception: functions/builtins explicitly marked as none-aware still receive `none(...)` as plain data.
- This explicit-handling decision currently lives partly in Python via `_NONE_AWARE_PUBLIC_FUNCTIONS` and `_mark_handles_none(...)`.

### Propagation in pipelines

- `|>` is an explicit pipeline evaluation form.
- Pipelines short-circuit on `none(...)` stage input and return the same `none(...)`.
- If a stage returns `none(...)`, later stages do not execute and that same `none(...)` is returned.
- Pipelines do not auto-unwrap `some(...)`.
- Explicit Option helpers such as `flat_map_some(...)`, `map_some(...)`, and `then_*` are still required when the next stage expects the inner value of a `some(...)`.

### Pattern matching

- Pattern matching supports:
  - literal `none`
  - structured `none(reason)`
  - structured `none(reason, context)`
  - constructor `some(pattern)`
- `nil` is not a separate runtime match family anymore; it normalizes to `none("nil")`.
- Pattern-side `none(...)` reason parsing is currently looser than runtime construction in one specific way:
  - parser accepts literal/symbol-label reason patterns
  - runtime `make_none(...)` requires string reasons

### Current list / map / parsing / operator behavior

- Canonical list access helpers are already structured:
  - `first([]) -> none("empty-list")`
  - `last([]) -> none("empty-list")`
  - `nth(...) -> none("index-out-of-bounds", ...)`
- Canonical map helper `get(...)` returns `some(value)` or structured `none(...)`.
- Compatibility map access forms remain mixed-shape:
  - `map_get`, slash access, callable map lookup, and string projectors return raw value on success and `none(...)` on missing lookup.
- `parse_int(...)` returns `some(int)` or `none("parse-error", context)` for ordinary parse failure.
- Arithmetic/comparison type mismatches currently return structured `none("type-error", meta)` rather than raising.
- Many other wrong-type situations still raise Python-side exceptions mapped as Genia runtime errors, for example:
  - `car(1)` -> `TypeError`
  - `parse_int(42)` -> `TypeError`
  - spread of non-list -> `TypeError`

### REPL / printing / rendered representation

- `format_debug(...)` and `format_display(...)` both render raw Python `None` as `none("nil")`.
- Structured absence is rendered directly:
  - `none("missing-key", {key: "name"})`
  - `some(none("nil"))`
- CLI/file mode suppresses printing a final `none("nil")` result.
- Non-`nil` structured absence values still print in `-c` / file mode.
- REPL/harness-style result formatting is not identical to CLI/file mode:
  - test/documentation harnesses that print “any non-`None` result” will print `none("nil")`
  - `_main(...)` currently suppresses that specific result

---

## 2. Leak inventory

| File | Function / path | Current behavior | User-visible? | Classification | Recommended fix |
| --- | --- | --- | --- | --- | --- |
| [src/genia/interpreter.py](/Users/m0smith/projects/genia-2026/src/genia/interpreter.py) | `finish_none_expr(...)` | Parser accepts arbitrary expressions in `none(...)` reason position | Yes | Semantic inconsistency | Validate reason/meta shape earlier, or document clearly that shape validation is runtime-only |
| [src/genia/interpreter.py](/Users/m0smith/projects/genia-2026/src/genia/interpreter.py) | `make_none(...)` | Runtime requires string reason + map meta | Yes | Current law, but under-documented outside core docs | Keep central constructor; ensure all creation paths go through it |
| [src/genia/interpreter.py](/Users/m0smith/projects/genia-2026/src/genia/interpreter.py) | `_genia_to_python_host(...)` | Any `none(...)` becomes Python `None`, dropping reason/context | Yes | Host leak | Decide whether host bridge intentionally erases absence metadata or should preserve it through an explicit wrapper/protocol |
| [src/genia/interpreter.py](/Users/m0smith/projects/genia-2026/src/genia/interpreter.py) | `_python_host_to_genia(...)` | Python `None` becomes `none("nil")` | Yes | Host leak / lossy normalization | Keep for now, but document that Python `None` cannot round-trip structured absence |
| [src/genia/interpreter.py](/Users/m0smith/projects/genia-2026/src/genia/interpreter.py) | Host interop call path (`_wrap_python_host_callable`, pipeline into host exports) | `some(x)` is unwrapped by host conversion, unlike ordinary pipeline stages | Yes | Semantic inconsistency / host-specific behavior | Make this explicit in docs/spec or remove it in a dedicated follow-up; do not let it remain accidental |
| [src/genia/interpreter.py](/Users/m0smith/projects/genia-2026/src/genia/interpreter.py) | `invoke_callable(...)` + `_NONE_AWARE_PUBLIC_FUNCTIONS` | Absence propagation exceptions are partly controlled by a host-side allowlist | Yes | Host-defined language behavior | Shrink or replace with a narrower explicit marker strategy; keep the bridge small |
| [src/genia/interpreter.py](/Users/m0smith/projects/genia-2026/src/genia/interpreter.py) | `eval_program(...)`, `eval_tail(...)`, `eval_function_body(...)` | Internal empty-result paths still use raw Python `None` | Mostly no | Internal inconsistency | Leave as internal sentinel unless it leaks; normalize at public boundaries only |
| [src/genia/interpreter.py](/Users/m0smith/projects/genia-2026/src/genia/interpreter.py) | `log`, `print`, `run`, `sleep`, `flush`, `send`, `cell_send` | Return Python `None`, then rely on `_normalize_nil(...)` in call dispatch | Usually yes | Internal inconsistency with safe normalization | Acceptable in short term; centralize boundary normalization and avoid bypass paths |
| [src/genia/interpreter.py](/Users/m0smith/projects/genia-2026/src/genia/interpreter.py) | `_main(...)` vs `run_source(...)` / harnesses | CLI/file mode suppresses final `none("nil")`, while direct embedding and doc harnesses may still print it | Yes | User-visible host-boundary inconsistency | Pick one documented output policy per entrypoint and make harness docs/tests explicit |
| [src/genia/interpreter.py](/Users/m0smith/projects/genia-2026/src/genia/interpreter.py) | `GeniaMap.get(...)` / `map_get` / map call / string projector / slash access | Success shape is raw value, not `some(value)`; missing shape is `none(...)` | Yes | Public API inconsistency | Preserve for compatibility, but continue steering canonical docs/examples to `get(...)` |
| [src/genia/interpreter.py](/Users/m0smith/projects/genia-2026/src/genia/interpreter.py) | `eval_binary(...)` and `eval_unary(...)` | Operator type mismatches return `none("type-error", meta)` instead of raising | Yes | Semantic choice that differs from many other wrong-type failures | Decide whether operators stay absence-producing or move to hard errors; document one rule clearly before changing anything |
| [src/genia/utf8.py](/Users/m0smith/projects/genia-2026/src/genia/utf8.py) | `format_display(...)`, `format_debug(...)` | Raw Python `None` is rendered as `none("nil")`, hiding host leaks | Yes | Tooling-side normalization leak | Useful today, but it can mask accidental raw `None` at the runtime boundary |
| [src/genia/std/prelude/eval.genia](/Users/m0smith/projects/genia-2026/src/genia/std/prelude/eval.genia) and [src/genia/std/prelude/syntax.genia](/Users/m0smith/projects/genia-2026/src/genia/std/prelude/syntax.genia) | Metacircular/pair helpers still use `nil` as source-level terminator spelling | Yes | Intentional legacy surface | Keep until a dedicated pair/pair-list cleanup; do not confuse this with a separate runtime nil value |
| Current core docs | Earlier documentation implied `nil` was distinct from runtime `none` and used old `none(empty_list)` examples | Yes | Documentation drift | Keep `GENIA_STATE.md` and surviving core docs aligned with normalized `none("nil")` semantics |

### Notes on internal `return None`

Not every `return None` in the repo is a semantic bug.

Current broad categories:

- parser/matcher/no-match sentinels
- empty-program / empty-block internal result sentinels
- host builtins that rely on `_normalize_nil(...)`
- generic Python helpers outside the language runtime (debug protocol, file IO helpers, etc.)

The next patch should not mechanically replace every `None` with `OPTION_NONE`.
It should only normalize public/runtime boundaries and remove sentinel leaks that affect semantics.

---

## 3. Surface area matrix

| Category | Current behavior | Desired behavior for follow-up work | Migration risk | Fix layer |
| --- | --- | --- | --- | --- |
| List operations | Canonical helpers already use structured `some` / `none(...)`; pair-built list syntax still uses legacy `nil` spelling | Keep current canonical Option behavior; leave pair syntax alone unless a separate pair cleanup is planned | Low | Prelude first, host only if boundary leaks |
| Map/key lookup | `get` is canonical maybe-aware API; compatibility forms still return raw value or `none(...)` | Keep compatibility forms, but avoid expanding them; canonical docs/tests should keep moving toward `get` | Low | Prelude/docs |
| Parsing helpers | `parse_int` already returns `some(...)` / `none("parse-error", ctx)` | Keep shape; clarify constructor validation and pipeline examples | Low | Host runtime + docs |
| Arithmetic/type mismatch | Operators return `none("type-error", meta)` while many other wrong-type paths still raise exceptions | Choose and document a consistent boundary between ordinary absence and programmer/runtime errors | Medium | Host runtime semantics |
| Function argument passing | Calls short-circuit on `none(...)` unless allowlisted/marked none-aware | Replace broad host-side curation with the smallest explicit mechanism possible | High | Host runtime first |
| Pipeline stages | Pipelines short-circuit on `none(...)` and automatically lift ordinary stages over `some(x)` | Keep this stable per current constraints | Low | Host runtime/docs |
| Pattern matching | Runtime sees normalized absence family; parser still accepts looser `none(...)` reason shapes than runtime constructor allows | Align parse/lower/runtime validation story | Medium | Parser/lowering + docs |
| REPL/display/help text | Formatting hides raw Python `None` as `none("nil")`; CLI suppresses final `none("nil")` while some harnesses print it | Make output policy explicit per entrypoint and reduce accidental raw `None` masking | Medium | Host runtime + docs |
| Core IR / lowering / evaluator boundary | IR is already explicit for `some` / `none`; lowering normalizes `nil` to `IrOptionNone("nil")` | Preserve this as the portability boundary; do not bypass it | Low | Host runtime/core IR |
| Std/prelude wrappers vs host-backed helpers | Public absence-facing helpers mostly live in prelude; host bridge still decides some special none-aware behavior | Keep public semantics prelude-centered and shrink host-side curated exceptions | Medium | Prelude + minimal host support |
| Host interop | Host `None` erases structured absence metadata; `some(x)` unwraps at the bridge unlike ordinary pipelines | Make bridge semantics explicit and narrow; avoid accidental Python-only language law | High | Host bridge + host interop docs |

---

## 4. Minimal diff plan

### Phase 1: Constructor and boundary inventory locks

Files:

- [src/genia/interpreter.py](/Users/m0smith/projects/genia-2026/src/genia/interpreter.py)
- focused tests under [tests/test_option.py](/Users/m0smith/projects/genia-2026/tests/test_option.py), [tests/test_option_semantics.py](/Users/m0smith/projects/genia-2026/tests/test_option_semantics.py), and semantic cases under [tests/cases/option](/Users/m0smith/projects/genia-2026/tests/cases/option)

Why first:

- The next patch needs one authoritative list of public absence creation/normalization paths before changing behavior.

Expected test impact:

- Mostly characterization tests if any are added.

Doc impact:

- Minimal; likely no public wording changes yet beyond the audit.

Rollback risk:

- Low.

### Phase 2: Tighten `none(...)` construction rules at the front door

Files:

- [src/genia/interpreter.py](/Users/m0smith/projects/genia-2026/src/genia/interpreter.py)
- possibly [tests/test_ir.py](/Users/m0smith/projects/genia-2026/tests/test_ir.py)
- possibly parser-focused tests if construction validation moves earlier

Why before later phases:

- If the parser/lowering/runtime disagree about what `none(...)` is allowed to contain, every later cleanup becomes ambiguous.

Expected test impact:

- IR/lowering tests that still use symbolic reasons like `none(parse_failed, ...)` will need explicit decisions.

Doc impact:

- `GENIA_STATE.md`, `GENIA_RULES.md`, and the Option/pattern chapters should describe exactly where validation happens.

Rollback risk:

- Medium; parser-time validation is more disruptive than runtime-only validation.

### Phase 3: Reduce raw `None` at public runtime boundaries

Files:

- [src/genia/interpreter.py](/Users/m0smith/projects/genia-2026/src/genia/interpreter.py)
- [src/genia/utf8.py](/Users/m0smith/projects/genia-2026/src/genia/utf8.py)
- entrypoint/harness tests such as [tests/test_pipeline_operator.py](/Users/m0smith/projects/genia-2026/tests/test_pipeline_operator.py) and [tests/test_pairs.py](/Users/m0smith/projects/genia-2026/tests/test_pairs.py)

Why before host interop:

- The host bridge is easier to reason about once Genia-side public boundaries are no longer mixing raw Python `None` and normalized absence.

Expected test impact:

- CLI/file/REPL/documentation-harness result-printing tests may need alignment.

Doc impact:

- `GENIA_REPL_README.md` and other current core docs about visible output may need small clarifications.

Rollback risk:

- Medium; output behavior is user-visible.

### Phase 4: Decide and document the operator/type-error line

Files:

- [src/genia/interpreter.py](/Users/m0smith/projects/genia-2026/src/genia/interpreter.py)
- [GENIA_STATE.md](/Users/m0smith/projects/genia-2026/GENIA_STATE.md)
- [GENIA_RULES.md](/Users/m0smith/projects/genia-2026/GENIA_RULES.md)
- relevant tests under [tests/test_option_semantics.py](/Users/m0smith/projects/genia-2026/tests/test_option_semantics.py), [tests/test_option.py](/Users/m0smith/projects/genia-2026/tests/test_option.py), and operator tests

Why before broad API cleanup:

- Canonical absence semantics cannot be called “unified” while operators return structured absence but many comparable wrong-type cases still raise exceptions.

Expected test impact:

- Moderate.

Doc impact:

- Errors/functions chapters need to teach one clear rule.

Rollback risk:

- Medium to high, because this changes user-visible failure mode.

### Phase 5: Shrink host-curated none-awareness

Files:

- [src/genia/interpreter.py](/Users/m0smith/projects/genia-2026/src/genia/interpreter.py)
- relevant prelude modules such as [src/genia/std/prelude/option.genia](/Users/m0smith/projects/genia-2026/src/genia/std/prelude/option.genia), [src/genia/std/prelude/eval.genia](/Users/m0smith/projects/genia-2026/src/genia/std/prelude/eval.genia), [src/genia/std/prelude/syntax.genia](/Users/m0smith/projects/genia-2026/src/genia/std/prelude/syntax.genia)

Why after constructor/boundary cleanup:

- Once the runtime value shape is stable, the remaining question is who is allowed to treat `none(...)` as plain data versus propagated absence.

Expected test impact:

- Metacircular/syntax/helper tests will be sensitive here.

Doc impact:

- Mostly `GENIA_STATE.md` / `GENIA_RULES.md`; probably not much current-doc churn if the public surface stays the same.

Rollback risk:

- High if done too broadly.

### Phase 6: Revisit host interop absence semantics

Files:

- [src/genia/interpreter.py](/Users/m0smith/projects/genia-2026/src/genia/interpreter.py)
- [GENIA_STATE.md](/Users/m0smith/projects/genia-2026/GENIA_STATE.md)
- [GENIA_RULES.md](/Users/m0smith/projects/genia-2026/GENIA_RULES.md)
- [README.md](/Users/m0smith/projects/genia-2026/README.md)
- host bridge tests such as [tests/test_python_host_interop.py](/Users/m0smith/projects/genia-2026/tests/test_python_host_interop.py)

Why last:

- Host interop is the highest-risk place to accidentally let Python define Genia semantics.
- It is easier to pin down once core absence behavior is already internally coherent.

Expected test impact:

- High for host interop only.

Doc impact:

- Shared host docs and current core docs must be synchronized.

Rollback risk:

- High.

---

## Recommended next patch scope

The smallest safe next implementation prompt should focus on exactly two things:

1. constructor/validation coherence for `none(reason, meta?)`
2. public-boundary normalization of raw Python `None`

It should explicitly avoid, for now:

- redesigning `|>`
- changing Flow semantics
- reworking canonical `get` / `first` / `nth` behavior
- broad host interop redesign

That narrower next step will remove the highest-confidence leaks without stepping on the larger host-interop and operator-error decisions yet.

---

## Tiny preparatory fixes made in this audit phase

- Updated current core documentation so it no longer teaches `nil` as a separate runtime absence value and no longer uses the stale `none(empty_list)` example.
- Added this audit document only; no runtime semantics were changed in this phase.
