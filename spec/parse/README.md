# Parse Spec Suite

This directory holds the shared executable parse spec files for Genia.

**Status: active (initial coverage only)**

## What parse specs assert

Parse specs validate the parse boundary: the parser produces a deterministic, host-neutral normalized AST for valid inputs, and a deterministic error type plus message for invalid inputs.

Only stable, already-implemented syntax forms may appear in parse specs. Parse spec coverage expands only when new forms are explicitly added and tested.

## Spec format

Parse specs use the standard shared YAML envelope with `category: parse`.

`input` fields:
- `source` — the Genia source text to parse

`expected` fields:
- `parse` — a mapping with:
  - `kind: ok` plus `ast: {...}` for a successful parse (AST compared exactly)
  - `kind: error` plus `type: SyntaxError` and `message: "..."` for a parse failure (`message` matched as substring)

## Example

```yaml
name: parse-literal-number
category: parse
description: Number literal parses to a Literal node
input:
  source: "42"
expected:
  parse:
    kind: ok
    ast:
      kind: Literal
      value: 42
```

**GENIA_STATE.md is the final authority for implemented behavior. All other docs/specs must align with this contract.**
