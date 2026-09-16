# Issue #854 Design — E21-2 Tagged Portable Numeric IrLiteral Payloads

Status: process design artifact for issue #854. Implements only §4 of
`docs/design/r21-numeric-source-portable-representation-contract.md`.

## `lowering.py`

Change the `Number -> IrLiteral` construction:

```python
if isinstance(node, Number):
    return IrLiteral(numeric_literal_payload(node), span=node.span)
```

`numeric_literal_payload(node: Number) -> dict` (new function in
`src/genia/numeric_source.py`) builds:

- Integer: `{"kind": "integer", "digits": node.digits}`
- Decimal: `{"kind": "decimal", "coefficient": node.coefficient, "exponent": node.exponent}`

directly from the E21-1 classification fields already populated on every
`Number` node — no re-parsing, no `float()`.

## `evaluator.py` compatibility shim

New `numeric_literal_runtime_value(payload: dict) -> int | float` in
`src/genia/numeric_source.py`:

- Integer: `int(payload["digits"])`
- Decimal: `float(f"{payload['coefficient']}e{payload['exponent']}")`

This exactly reconstructs the value the evaluator already produced from
`float(tok.text)`/`int(tok.text)` before this ticket (same source digits,
same binary64 rounding via the same stdlib `float()` call — only the
spelling fed to `float()` changes from the original source text to the
canonical `coefficient` + `e` + `exponent` form, which denotes the same
mathematical value and therefore rounds to the same binary64 result).

`IrLiteral` evaluation (`evaluator.py` around line 1314) and
`_render_pipeline_stage` (around line 936) call this helper when
`isinstance(node.value, dict)` before using the result, leaving non-numeric
`IrLiteral` payloads (string/bool/nil) completely untouched.

## `optimizer.py`

The one existing numeric-payload-sensitive check
(`n_arg.right.value == 1` recognizing `n - 1` in a tail-recursion pattern)
is updated to `numeric_literal_equals(n_arg.right.value, 1)`, a tiny
new/shared predicate that handles both the legacy bare-number shape (for
robustness, though none remains after this ticket) and the new tagged
dict shape.

## `hosts/python/ir_normalize.py`

No code change: `_normalize_ir_node` already serializes `node.value`
whatever its shape is (previously a scalar, now sometimes a dict for
numeric literals); JSON/dict comparison in the shared spec-runner
comparator already supports nested dict equality.

## Fixture migration

Every existing `spec/ir/*.yaml` case whose expected IR contains a numeric
`IrLiteral` (`value: <int>`, no decimal cases exist yet) is updated to the
tagged shape, e.g.:

```yaml
node: IrLiteral
value:
  kind: integer
  digits: "1"
```

This is the "update normalized IR adapters/fixtures only as required for
the tagged portable representation" work issue #854 explicitly scopes in.
No fixture's *program source* changes, only the expected IR payload shape
for numeric literals it already exercised.

## New evidence

`spec/ir/*` cases (failing before implementation) for: Integer payload
shape, Decimal payload shape (dotted/exponent/dot-exponent), huge Integer
exact digits, equivalent Decimal spelling normalization, unary-negative
lowering (unary minus wrapping the positive tagged literal), and `/`
staying ordinary `IrBinary(op=SLASH)`.
