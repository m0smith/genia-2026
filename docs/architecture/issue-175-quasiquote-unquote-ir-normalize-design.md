# Issue #175 Design — Fix quasiquote+unquote normalization in spec/ir shared runner

**Phase:** design
**Branch:** `issue-175-quasiquote-unquote-ir-normalize`
**Issue:** #175 — Fix quasiquote+unquote normalization in spec/ir shared runner
**Spec doc:** `docs/architecture/issue-175-quasiquote-unquote-ir-normalize-spec.md`

This phase describes the implementation plan only.
It does not add failing tests, implementation code, or documentation sync edits.

---

## 1. Design Summary

Two changes to `hosts/python/ir_normalize.py`:

1. Add `Unquote` and `UnquoteSplicing` to the import list (they are parser AST types currently not
   imported in this file).
2. Add two `isinstance` branches inside `_normalize_quoted_syntax` — one for `Unquote`, one for
   `UnquoteSplicing` — each delegating the inner `expr` back through `_normalize_quoted_syntax`.

No other files change in the implementation phase.

---

## 2. Scope Lock

### Included

- Import `Unquote` and `UnquoteSplicing` from `genia.interpreter` in
  `hosts/python/ir_normalize.py`.
- Two new `isinstance` branches in `_normalize_quoted_syntax`.

### Excluded

- No changes to `_normalize_ir_node` — top-level `IrUnquote` and `IrUnquoteSplicing` are already
  handled there and are correct.
- No changes to `src/genia/interpreter.py` — parser AST definitions and lowering are correct.
- No changes to any spec runner, evaluator, or test infrastructure.
- No new IR node types, no new parser AST types, no new language syntax.
- Tests — test phase only.
- Docs sync — docs phase only.
- Implementation code — implementation phase only.

---

## 3. Why the import is missing

`_normalize_quoted_syntax` was originally written to handle only the literal parser AST node types
that appear in plain `quote(...)` bodies: `Var`, `String`, `Number`, `Boolean`, `ListLiteral`,
`MapLiteral`. These are all imported. `Unquote` and `UnquoteSplicing` are parser AST types that
appear in `quasiquote(...)` bodies and were never needed by `_normalize_quoted_syntax` before,
so they were never added to the import.

`IrUnquote` and `IrUnquoteSplicing` (IR-level types) are already imported and already handled in
`_normalize_ir_node`, which is the correct path for top-level unquote nodes. The gap is
specifically in the quoted-syntax path.

---

## 4. Import change

### File: `hosts/python/ir_normalize.py`

The existing import block (lines 9–54) imports from `genia.interpreter`. `Unquote` and
`UnquoteSplicing` must be added to this block.

Current end of the import block (alphabetical order, excerpt):

```python
    IrUnquote,
    IrUnquoteSplicing,
    IrVar,
    ListLiteral,
    MapLiteral,
    Number,
    String,
    Var,
    assert_portable_core_ir,
)
```

Add `Unquote` and `UnquoteSplicing` in alphabetical order between `String` and `Var`:

```python
    IrUnquote,
    IrUnquoteSplicing,
    IrVar,
    ListLiteral,
    MapLiteral,
    Number,
    String,
    Unquote,
    UnquoteSplicing,
    Var,
    assert_portable_core_ir,
)
```

---

## 5. Branch placement in `_normalize_quoted_syntax`

### File: `hosts/python/ir_normalize.py`, function `_normalize_quoted_syntax` (line 295)

The function currently has these branches in order:
1. `String` → `{kind: Literal, value: ...}`
2. `Number` → `{kind: Literal, value: ...}`
3. `Boolean` → `{kind: Literal, value: ...}`
4. `Var` → `{kind: Var, name: ...}`
5. `ListLiteral` → `{kind: List, items: [...]}`
6. `MapLiteral` → `{kind: Map, items: [...]}`
7. `raise TypeError` (fallback)

The two new branches are added between `MapLiteral` (step 6) and the `raise TypeError` (step 7).

New branches:

```python
    if isinstance(expr, Unquote):
        return {
            "kind": "Unquote",
            "expr": _normalize_quoted_syntax(expr.expr),
        }
    if isinstance(expr, UnquoteSplicing):
        return {
            "kind": "UnquoteSplicing",
            "expr": _normalize_quoted_syntax(expr.expr),
        }
```

---

## 6. Why inner `expr` uses `_normalize_quoted_syntax`, not `_normalize_ir_node`

`IrQuasiQuote.expr` holds a raw parser AST `Node` — the quasiquote body is stored before lowering.
This is intentional and consistent with how `IrQuote.expr` is stored. All content inside a
quasiquote body is parser AST, so `_normalize_quoted_syntax` is the correct recursive path.

`Unquote.expr` inside a quasiquote body is also a parser AST `Node` (e.g., `Var("x")`). Calling
`_normalize_ir_node` on a parser AST node would be a type error. The recursion must stay inside
`_normalize_quoted_syntax`.

Contrast this with top-level `IrUnquote` (handled in `_normalize_ir_node`): that node's `expr`
field is an `IrNode` because it was lowered. The two paths are distinct and must not be conflated.

---

## 7. Normalized output

For `quasiquote([a, unquote(x)])`:

The parser produces `QuasiQuote(ListLiteral([Var("a"), Unquote(Var("x"))]))`. Lowering stores the
raw body: `IrQuasiQuote(ListLiteral([Var("a"), Unquote(Var("x"))]))`. Normalization calls
`_normalize_quoted_syntax(ListLiteral([Var("a"), Unquote(Var("x"))]))`, which:

1. Matches `ListLiteral` → recurses into items.
2. Item 0: `Var("a")` → `{kind: Var, name: a}`.
3. Item 1: `Unquote(Var("x"))` → new branch → `{kind: Unquote, expr: {kind: Var, name: x}}`.

Full normalized IR:

```yaml
- node: IrExprStmt
  expr:
    node: IrQuasiQuote
    expr:
      kind: List
      items:
        - kind: Var
          name: a
        - kind: Unquote
          expr:
            kind: Var
            name: x
```

For `quasiquote([a, unquote_splicing(xs), b])`:

Item at position 1: `UnquoteSplicing(Var("xs"))` → new branch →
`{kind: UnquoteSplicing, expr: {kind: Var, name: xs}}`.

Full normalized IR:

```yaml
- node: IrExprStmt
  expr:
    node: IrQuasiQuote
    expr:
      kind: List
      items:
        - kind: Var
          name: a
        - kind: UnquoteSplicing
          expr:
            kind: Var
            name: xs
        - kind: Var
          name: b
```

---

## 8. What does NOT change

| File | Status |
|---|---|
| `src/genia/interpreter.py` | Unchanged — parser AST and lowering are correct |
| `hosts/python/ir_normalize.py` `_normalize_ir_node` | Unchanged — already handles `IrUnquote`/`IrUnquoteSplicing` |
| `hosts/python/ir_normalize.py` `_normalize_pattern` | Unchanged |
| `hosts/python/ir_normalize.py` `_normalize_quoted_map_key` | Unchanged |
| `tests/test_quasiquote.py` | Unchanged — eval tests do not touch the normalizer |
| All existing `spec/ir/` YAML files | Unchanged — all 20 must continue passing |

---

## 9. Docs impacted in the docs phase (not this phase)

| File | Change |
|---|---|
| `docs/architecture/core-ir-portability.md` | Remove the Known Normalization Limitations entry for quasiquote+unquote (currently lines 93–95) |
| `GENIA_STATE.md` | Remove the matching limitation bullet from the IR stability description (§ 0 "IR stability remains Partial") |

No other docs change. The behavioral description of quasiquote in GENIA_STATE.md (§9.2.1) does not
need updating — the runtime semantics are unchanged.

---

## 10. Complexity check

- Lines changed in implementation: ~7 (2 import names + 2 × 4-line branch)
- New abstractions: 0
- New functions: 0
- New files: 0 (beyond the spec/test/docs artifacts of their own phases)
- Design decision to make: 0 (single correct approach, no tradeoffs)

---

## 11. Control flow for later phases

1. **Test phase** — add two failing `spec/ir/` YAML files; run spec runner to confirm both fail;
   commit with `test(core-ir): ...`
2. **Implementation phase** — apply the import addition and two branches; reference failing-test
   commit SHA; run all `spec/ir/` cases and `tests/test_quasiquote.py`; all must pass; commit
   with `fix(core-ir): ...`
3. **Docs phase** — remove limitation entries from `core-ir-portability.md` and `GENIA_STATE.md`;
   commit with `docs(core-ir): ...`
4. **Audit phase** — full suite, spec runner, doc-sync check; commit with `audit(core-ir): ...`

---

## 12. Recommended next prompt (TEST phase)

```
You are working in the Genia repo on issue #175:
Fix quasiquote+unquote normalization in spec/ir shared runner

Design is complete. Branch: issue-175-quasiquote-unquote-ir-normalize.
Design doc: docs/architecture/issue-175-quasiquote-unquote-ir-normalize-design.md
Spec doc:   docs/architecture/issue-175-quasiquote-unquote-ir-normalize-spec.md

Test phase task — write FAILING spec/ir YAML files only, no implementation:

1. Confirm current branch is issue-175-quasiquote-unquote-ir-normalize.
   Refuse to modify files on main.

2. Create spec/ir/quasiquote-unquote-var.yaml:
   source: quasiquote([a, unquote(x)])
   Expected IR: IrExprStmt > IrQuasiQuote > kind:List with items
     [{kind:Var, name:a}, {kind:Unquote, expr:{kind:Var, name:x}}]

3. Create spec/ir/quasiquote-unquote-splicing-var.yaml:
   source: quasiquote([a, unquote_splicing(xs), b])
   Expected IR: IrExprStmt > IrQuasiQuote > kind:List with items
     [{kind:Var, name:a}, {kind:UnquoteSplicing, expr:{kind:Var, name:xs}}, {kind:Var, name:b}]

4. Run the shared spec/ir runner against these two new cases only.
   Confirm both FAIL with the current code (TypeError from _normalize_quoted_syntax).
   Show the failure output.

5. Confirm all 20 existing spec/ir cases still pass (no regression from adding the new files).

6. Commit with prefix: test(core-ir): failing spec/ir cases for quasiquote+unquote issue #175

Do NOT implement the fix. Do NOT update ir_normalize.py. Do NOT update any docs.
Both new spec cases must be failing when committed.
```
