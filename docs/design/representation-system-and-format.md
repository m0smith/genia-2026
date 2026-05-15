# Representation System and Format

Status: Current Python reference host behavior unless marked Experimental.

This page documents the implemented Representation System surface for display/debug strings and format templates. `GENIA_STATE.md` remains the final authority.

## Purpose

Representation renders values as strings for output and debugging.

Representation answers:

> How should this value be shown?

It is not a type system, data model, localization layer, or interpolation syntax.

## Core Rule

Representation does not change value identity.

Calling `display(value)`, `debug_repr(value)`, or `format(template_or_format, values)` does not change the value being represented, its runtime category, structure, or value-template compatibility.

## Representation vs Value Templates

Value templates describe or constrain values.

Formats describe output strings.

`Format` values are not refinements, open shapes, closed shapes, contracts, variants, or template composition for value matching.

## Display and Debug Representation

- `display(value)` returns a user-facing representation string without writing output.
- `debug_repr(value)` returns a debug representation string without writing output.

Output operations such as `print`, `log`, `write`, and `writeln` remain separate.

## format(...)

`format(template_or_format, values)` returns a string and writes nothing.

The first argument may be:

- a raw string template
- a `Format` value

Supported placeholder forms:

- Named placeholders use map values: `{name}`
- Positional placeholders use list values: `{0}`
- Debug placeholders use debug representation: `{name:?}`, `{0:?}`
- Escaped braces use `{{` and `}}`

Plain placeholders use display rendering. Debug placeholders use the same debug rendering as `debug_repr(value)`.

`format(...)` is side-effect-free at the language surface: it does not write output and does not mutate the template, `Format` value, or values map/list.

## Format Values

`Format(template)` constructs an untagged first-class representation value from a string template. Experimental.

`Format(template, tag)` constructs a tagged first-class representation value. Experimental.

Related helpers are Experimental:

- `format_template(fmt)` returns the original source template string from an atomic `Format` value.
- `format_tag(fmt)` returns `some(tag)` for a tagged `Format` and `none("missing-format-tag")` for an untagged `Format`.
- `format_compose(parts)` creates a composed `Format` from ordered raw string templates and/or `Format` values.

Tags are metadata only. They do not affect rendering, display/debug output, or value identity.

`Format` values display and debug as opaque representation values: `<format>`.

## Examples

Named placeholder:

```genia
format("Hello {name}!", {name: "Alice"})
```

Result:

```text
"Hello Alice!"
```

Classification: Valid, covered by `spec/eval/format-named-basic.yaml`.

Positional placeholder:

```genia
format("Item {0} costs {1}", ["apple", "5"])
```

Result:

```text
"Item apple costs 5"
```

Classification: Valid, covered by `spec/eval/format-positional-basic.yaml`.

Escaped braces:

```genia
format("{{key}} = {0}", ["value"])
```

Result:

```text
"{key} = value"
```

Classification: Valid, covered by `spec/eval/format-escaped-braces-mixed.yaml`.

Tic-tac-toe board row:

```genia
format("{0} | {1} | {2}", ["X", "O", "X"])
```

Result:

```text
"X | O | X"
```

Classification: Valid, covered by `spec/eval/format-tic-tac-toe-row.yaml`.

Missing named field:

```genia
format("Hello {name}!", {greeting: "Hi"})
```

Expected stderr:

```text
Error: format missing field: name
```

Expected exit code:

```text
1
```

Classification: Valid, covered by `spec/error/error-format-missing-named-field.yaml`.

## Non-goals

Not implemented:

- Localization
- Locale-aware formatting
- Interpolation syntax
- Tagged formats as stable behavior
- `Format` as a value-template mechanism
- Static typing or protocol behavior for `Format`
- Implicit template application
- Arbitrary formatter functions inside placeholders
- User-defined placeholder renderers
- Compile-time format validation
