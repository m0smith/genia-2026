# Issue #175 Spec — Fix quasiquote+unquote normalization in spec/ir shared runner

**Phase:** spec
**Branch:** `issue-175-quasiquote-unquote-ir-normalize`
**Issue:** #175 — Fix quasiquote+unquote normalization in spec/ir shared runner

This phase defines expected behavior only.
It does not add spec YAML files, failing tests, implementation, or documentation sync edits.

---

## 1. Source Of Truth

Final authority: `GENIA_STATE.md`

Supporting:
- `GENIA_RULES.md`
- `docs/architecture/core-ir-portability.md`
- `spec/ir/quote-expr.yaml` (canonical shape reference for quoted syntax normalization)

Relevant existing truths:
- Python is the only implemented host and is the reference host.
- `IrQuasiQuote`, `IrUnquote`, and `IrUnquoteSplicing` are already in the frozen minimal portable
  Core IR contract (`docs/architecture/core-ir-portability.md`).
- `_normalize_ir_node` in `hosts/python/ir_normalize.py` already handles top-level `IrUnquote` and
  `IrUnquoteSplicing` correctly (lines 106–115).
- `_normalize_quoted_syntax` in the same file handles: `String`, `Number`, `Boolean`, `Var`,
  `ListLiteral`, `MapLiteral`. It does not handle `Unquote` or `UnquoteSplicing` parser AST nodes.
- `IrQuasiQuote.expr` holds a raw parser AST `Node`, not lowered IR. This is why quasiquote bodies
  go through `_normalize_quoted_syntax` instead of `_normalize_ir_node`.
- The limitation is already documented in `docs/architecture/core-ir-portability.md` under
  "Known Normalization Limitations".
- Quasiquotation runtime behavior is implemented and tested in `tests/test_quasiquote.py`. This fix
  does not touch the evaluator.

---

## 2. Scope Decision

### Included in this spec

- Define the exact normalized shape for `IrQuasiQuote` bodies that contain `Unquote` parser AST nodes.
- Define the exact normalized shape for `IrQuasiQuote` bodies that contain `UnquoteSplicing` parser AST nodes.
- Scope the inner `expr` of `Unquote`/`UnquoteSplicing` to identifier expressions (`Var`) only.
  Anything broader requires its own issue.
- Confirm that inner `expr` is normalized via `_normalize_quoted_syntax` (not `_normalize_ir_node`).
- Confirm the `kind:` key convention for quoted syntax shape (not `node:`).

### Explicitly excluded from this spec

- Normalization of `unquote(expr)` where `expr` is a compound parser AST node (`Binary`, `Call`,
  `ListLiteral`, etc.). Only `Var` inner expressions are in scope for the cases defined here.
- Normalization of `unquote` inside map value positions (a separate gap, not in scope).
- Changes to the evaluator or quasiquote runtime behavior.
- Changes to `_normalize_ir_node` (top-level `IrUnquote`/`IrUnquoteSplicing` are already handled).
- New IR node types or parser AST extensions.
- Implementation, failing tests, or docs sync.

---

## 3. Normalized Shape Contract

### 3.1 Convention: `kind:` vs `node:`

All quoted syntax nodes (inside `IrQuote.expr` or `IrQuasiQuote.expr`) use `kind:` as their
discriminator key. Top-level IR nodes use `node:`. This is the existing convention established by
`quote-expr.yaml` and `_normalize_quoted_syntax`.

`Unquote` and `UnquoteSplicing` inside a quasiquote body are parser AST nodes — they must use
`kind:`, not `node:`.

### 3.2 `Unquote` in a quasiquote body

A parser AST `Unquote(expr)` node encountered during `_normalize_quoted_syntax` must normalize as:

```
{
  kind: Unquote,
  expr: <_normalize_quoted_syntax(expr)>
}
```

For `unquote(x)` where `x` is an identifier:

```
{kind: Unquote, expr: {kind: Var, name: x}}
```

### 3.3 `UnquoteSplicing` in a quasiquote body

A parser AST `UnquoteSplicing(expr)` node encountered during `_normalize_quoted_syntax` must
normalize as:

```
{
  kind: UnquoteSplicing,
  expr: <_normalize_quoted_syntax(expr)>
}
```

For `unquote_splicing(xs)` where `xs` is an identifier:

```
{kind: UnquoteSplicing, expr: {kind: Var, name: xs}}
```

### 3.4 Full top-level IR shape

`quasiquote([a, unquote(x)])` lowers to `IrQuasiQuote` (a top-level IR node) whose `expr` holds
the raw parser AST `ListLiteral([Var("a"), Unquote(Var("x"))])`. The portable normalized IR for
this program is:

```
node: IrExprStmt
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

`quasiquote([a, unquote_splicing(xs), b])` produces:

```
node: IrExprStmt
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

### 3.5 Recursive invariant

`_normalize_quoted_syntax` is the only normalization path for content inside a quasiquote body.
`Unquote.expr` and `UnquoteSplicing.expr` are also parser AST nodes and must therefore be
normalized with `_normalize_quoted_syntax`, not `_normalize_ir_node`.

This means any inner expression NOT already handled by `_normalize_quoted_syntax` (e.g., `Binary`,
`Call`) will still raise a `TypeError` from the existing fallback. That gap is out of scope for
this issue.

---

## 4. Observable Cases (to become YAML in the test phase)

These are not test code. They describe the contract. YAML files are written in the test phase.

### Case: quasiquote-unquote-var

```
name: quasiquote-unquote-var
category: ir
description: quasiquote body with unquote wrapping a variable normalizes as kind:Unquote
source: quasiquote([a, unquote(x)])
expected ir:
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

### Case: quasiquote-unquote-splicing-var

```
name: quasiquote-unquote-splicing-var
category: ir
description: quasiquote body with unquote_splicing wrapping a variable normalizes as kind:UnquoteSplicing
source: quasiquote([a, unquote_splicing(xs), b])
expected ir:
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

## 5. Cases NOT in scope

- `unquote(x + 1)` — `Binary` inside unquote body, not handled by `_normalize_quoted_syntax`.
- `unquote(f(x))` — `Call` inside unquote body, not handled by `_normalize_quoted_syntax`.
- `quasiquote({key: unquote(x)})` — `Unquote` inside a map value position.
- Nested quasiquote depth (e.g., `quasiquote([quasiquote([unquote(x)])])`).
- Runtime eval cases for quasiquote with unquote — already covered by `tests/test_quasiquote.py`.

---

## 6. Cross-phase notes

### For the design phase

- The fix is exactly two `isinstance` branches added to `_normalize_quoted_syntax` in
  `hosts/python/ir_normalize.py`.
- Each branch returns `{kind: "Unquote"/"UnquoteSplicing", expr: _normalize_quoted_syntax(node.expr)}`.
- No new helpers, no refactoring, no changes outside `_normalize_quoted_syntax`.
- The design document should confirm this is the complete change and describe where the branches
  sit relative to the existing `ListLiteral` branch (they are siblings, not nested).
- The design document should also confirm which docs will be updated: the Known Normalization
  Limitations entry in `docs/architecture/core-ir-portability.md` and the matching bullet in
  `GENIA_STATE.md`.

### For the test phase

Write these files (failing before implementation, passing after):
- `spec/ir/quasiquote-unquote-var.yaml`
- `spec/ir/quasiquote-unquote-splicing-var.yaml`

Confirm all 20 existing `spec/ir/` cases still pass with the new YAML present.
Confirm `tests/test_quasiquote.py` is unaffected (it does not touch the IR normalizer path).

### For the docs phase

In order:
1. `docs/architecture/core-ir-portability.md` — remove the Known Normalization Limitations entry
   for quasiquote+unquote.
2. `GENIA_STATE.md` — remove the matching limitation bullet from the IR stability section. Update
   the description of IR stability to reflect that quasiquote+unquote is now covered by shared
   spec cases.

---

## 7. Recommended next prompt (DESIGN phase)

```
You are working in the Genia repo on issue #175:
Fix quasiquote+unquote normalization in spec/ir shared runner

Spec is complete. Branch: issue-175-quasiquote-unquote-ir-normalize.
Spec doc: docs/architecture/issue-175-quasiquote-unquote-ir-normalize-spec.md

Design phase task:
1. Confirm current branch is issue-175-quasiquote-unquote-ir-normalize.
   Refuse to modify files on main.
2. Write a design document at docs/architecture/issue-175-quasiquote-unquote-ir-normalize-design.md
   describing exactly:
   - What two isinstance branches are added and where in _normalize_quoted_syntax
   - The exact return value of each branch
   - Why inner expr uses _normalize_quoted_syntax (not _normalize_ir_node)
   - Which docs change in the docs phase and exactly what is removed/updated
   - Confirmation that nothing else in the codebase changes
3. Do NOT implement. Do NOT write tests. Do NOT update behavior docs.
4. Commit with prefix: design(core-ir): quasiquote+unquote normalizer fix plan issue #175
```
