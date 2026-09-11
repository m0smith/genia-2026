# E18-4 Reconcile Patterns, Assertions, and Equality-like Surfaces — Pre-flight

ISSUE: #794
PARENT: #789
BLOCKED BY: #790, #791, #792, #793 — all merged (PRs #805, #806, #807, #808)
STATUS: pre-flight

---

## 0. BRANCH

Branch slug: `reconcile-equality-surfaces`
Expected branch: `issue-794-reconcile-equality-surfaces`
Base: `main` @ `925a548`

---

## 1. INVENTORY (performed before scoping)

The relation itself is complete after #791–#793. This issue finds every remaining
place that answers a Genia *semantic sameness* question and routes it through the
one relation. The sweep covered `==`, `!=`, `__eq__`, `__hash__`, dataclass
equality assumptions, host set/dict membership used as equivalence, key freezing
and canonicalization, duplicate detection, assertions, and pattern merging.

### Confirmed divergences, each measured on this base

| # | Surface | Site | Measured divergence |
|---|---|---|---|
| 1 | `assert_eq` | `builtins.py` `assert_eq_fn`, host `!=` | `assert_eq(true, 1)` **passes**; `assert_eq(utf8_encode("hi"), utf8_encode("hi"))` **fails**; `assert_eq({"a": 1}, {"a": 1})` **fails** |
| 2 | literal patterns | `pattern_match.py` `IrPatLiteral`, host `==` | a `1` literal pattern **matches** `true` |
| 3 | duplicate bindings | `pattern_match.py` `_merge_bindings`, host `!=` | a repeated `x` clause reports `true` and `1` as **the same** |
| 4 | meta-circular evaluator | `builtins.py` `_meta_operator_eq` / `_meta_operator_ne`, host `==`/`!=` | `eval(quote(true == 1), empty_env())` → `true` while `true == 1` → `false`; `!=` diverges the same way |
| 5 | Sheet column-name identity | `sheet.py` `_freeze_column_name`, a second hand-rolled key relation | `sheet([[true, [1]], [1, [2]]])` is rejected as duplicate column names even though `true != 1` |

Findings 3 and 5 were handed here by #792's audit. Finding 4 is new to this
sweep and is the most important one found: it is an entire second equality
implementation for Genia's own meta-evaluator, reachable from ordinary source
through `empty_env()`/`eval`.

### Checked and deliberately **not** changed (implementation-local, not semantic)

- parser and lexer token-kind and tag comparisons
- enum-like control-flow string comparisons
- source positions and spans
- process, scope, and phase **names** (`lifecycle_runtime`, `lifecycle_scope`,
  `lifecycle_plan`, `lifecycle_binding`) — these compare declaration names, not
  Genia values
- `callable.py`'s duplicate function definition check (name/arity strings)
- host protocol and spec-runner fields
- `host_builtin_docs` registry names
- test-framework metadata

`lifecycle_plan.py` uses a host set of `GeniaSymbol` for duplicate phase names.
Symbols are equal exactly when their names are equal, and `GeniaSymbol` is a
frozen dataclass keyed on `name`, so host behavior and the canonical relation
already agree. No change needed; recorded so #797 does not re-flag it.

### Obligation from #792 discharged by this sweep

"Confirm no semantic site decides map sameness with host `==`." The sweep found
no site that compares two `GeniaMap` values with host `==` to answer a semantic
question. `contains_protected` and the declassification scanners walk maps via
`.items()` and use `isinstance`, never `==`. This is recorded as evidence rather
than as an absence of effort, and #797 re-checks it.

### Behavior change inherited from #793, to be pinned here

Retrieval index handles are identity-bearing under the approved contract, so
Genia-level `handle == handle` now returns a boolean by identity instead of
raising. `GeniaIndexHandle.__eq__` still raises, which continues to protect
internal host comparisons. This is contract-correct — the failure boundary says
equality of two well-formed values returns a boolean — but it is currently
unpinned by any test at the Genia level. This issue adds that coverage.

---

## 2. SCOPE LOCK

Includes: routing findings 1–5 through the canonical relation; pinning the index
handle behavior; shared and focused failing evidence first.

Excludes: new pattern syntax; open-function or extensible-dispatch semantics;
domain-specific equivalence predicates; changes to the relation itself; C++ host;
authoritative release truth (#796).

---

## 3. FEATURE MATURITY

Stage: [x] Partial (E18-4 slice; R18 completes at E18-6/E18-7)

---

## 3a. Portability Analysis

All seven fields resolved; no `TBD`.

1. **Portability zone** — *language semantics (portable contract)*. Literal
   pattern matching, duplicate binding consistency, native assertion success, and
   the meta-evaluator's operators are all host-independent behavior.

2. **Core IR impact** — `none`. No new or changed `Ir*` node family. `IrPatLiteral`
   and the pattern families keep their shape; only how the evaluator compares a
   literal to a candidate changes. No parser, AST, or lowering change, and no new
   pattern syntax.

3. **Capability categories affected** — `none`. Every routed site becomes *more*
   restricted, not less: the canonical relation invokes no user code, performs no
   IO, and consumes nothing.

4. **Shared spec impact** — new `spec/eval/` cases for literal patterns,
   duplicate bindings, `assert_eq`, meta-evaluator agreement, and Sheet column
   identity. No new spec category or envelope field.

5. **Python reference host impact** — `src/genia/builtins.py` (`assert_eq_fn`,
   `_meta_operator_eq`, `_meta_operator_ne`), `src/genia/pattern_match.py`
   (`IrPatLiteral`, `_merge_bindings`), `src/genia/sheet.py`
   (`_freeze_column_name`). No public function, builtin, or syntax added.

6. **Host adapter impact** — `none`.

7. **Future host impact** — this is the slice that makes "one relation" true
   rather than merely stated. A future host that implemented `==` correctly but
   left literal patterns or assertions on its own host equality would still be
   non-conforming, and the new shared cases detect exactly that.

---

## 4. TEST STRATEGY

Core invariant, asserted directly: for the same operands, every equality-like
surface agrees with public `==`.

The strongest form of this is a *cross-surface agreement* case — compare the same
operand pairs through `==`, a literal pattern, a duplicate binding, `assert_eq`,
and the meta-evaluator in one program, and require identical answers. That
catches a future surface drifting away from the relation, which per-surface tests
would not.

Baseline: `main` @ `925a548` — `-m "not loopback"` 2 failed / 4168 passed
(pre-existing root/`chmod 000` cases), `-m loopback` 26 passed, shared specs
660/660, `uv run ruff check .` clean.

---

## 5. COMPLEXITY CHECK

[x] Revealing structure — this removes four independent equality implementations
and one independent key relation, replacing them with calls to the existing one.

---

## 6. CROSS-FILE IMPACT

`src/genia/builtins.py`, `src/genia/pattern_match.py`, `src/genia/sheet.py`, new
specs and tests, `GENIA_STATE.md`.

Risk of drift: [x] High — pattern dispatch and native test semantics depend on
these paths, and `sheet.py` changes a rejection boundary.

---

## 7. DOC DISTILLATION CHECK

Creates process artifacts? YES. Adds `docs/design`/`docs/architecture` files? NO.
Doc drift risk: [x] Medium.

---

## 8. PHILOSOPHY CHECK

- preserves minimalism? YES — deletes duplicate mechanisms
- avoids hidden behavior? YES
- keeps semantics out of host? YES
- aligns with pattern-matching-first? YES — this is precisely the slice that
  makes pattern matching obey the language's own equality

---

## KILLER WORKFLOW ALIGNMENT

[x] Yes. Literal patterns, duplicate bindings, and `assert_eq` are the everyday
tools of record parsing, validation, and native tests. A literal `1` pattern
silently matching `true`, or `assert_eq` rejecting two equal byte values, are
direct correctness hazards for validated data pipelines.

---

## 9. PROMPT PLAN

Preflight → Contract → Design → Test (failing) → Implementation → Docs → Audit →
Distillation.

---

## FINAL GO / NO-GO

**YES.** All blockers merged.
