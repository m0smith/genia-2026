
# Genia CLI Cheatsheet: Unix Power Mode

Only includes currently implemented Genia CLI and Flow behavior.

Validation: runnable snippets include `[case: <id>]` markers and are executed by pytest.

## Core CLI Shapes

| Mode | Command | Notes |
| --- | --- | --- |
| command mode | `genia -c 'source'` | run full source expression/program |
| pipe mode | `genia -p 'stage_expr'` | wraps as `stdin |> lines |> <stage_expr> |> run` |
| file mode | `genia path/to/file.genia` | run file source |

Use `-c` for value-producing pipelines such as sums.
Use `-p` for flow-stage pipelines ending in effects.

## Reliable Pipeline Building Blocks

| Goal | Building blocks |
| --- | --- |
| row source | `stdin |> lines` |
| flow transform | `map`, `filter`, `head`, `keep_some_else` |
| side effects | `each(print)`, `each(log)` |
| materialize | `collect` |
| maybe-safe parse | `parse_int`, `flat_map_some`, `unwrap_or` |
| numeric aggregate | `keep_some(...) |> collect |> sum` or `map((x) -> unwrap_or(...)) |> collect |> sum` |

## Working Commands

### Print stdin rows

[case: unix-power-print-stdin-rows]
```bash
cat file.txt | genia -p 'each(print)'
```

### Keep first 5 rows

[case: unix-power-head-5]
```bash
cat file.txt | genia -p 'head(5) |> each(print)'
```

### Count rows

[case: unix-power-count-rows]
```bash
cat file.txt | genia -c 'stdin |> lines |> collect |> count'
```

### Grep-style filter

[case: unix-power-grep]
```bash
cat file.txt | genia -p 'filter((l) -> contains(l, "error")) |> each(print)'
```

### Case-insensitive grep-style filter

[case: unix-power-grep-i]
```bash
cat file.txt | genia -p 'filter((l) -> contains(lower(l), "error")) |> each(print)'
```

### Uppercase all rows

[case: unix-power-upper]
```bash
cat file.txt | genia -p 'map(upper) |> each(print)'
```

### Sum the 5th column (AWK-style)

[case: unix-power-sum-5th]
```bash
ls -l | genia -c '
  stdin
    |> lines
    |> map(fields)
    |> keep_some_else((row) -> row |> nth(5) |> flat_map_some(parse_int), log)
    |> collect
    |> sum
'
```

Notes:
- `fields(row)` keeps the original row at index `0`.
- `nth(5, row)` targets the fifth whitespace field.
- `keep_some_else` keeps good parsed ints and sends bad rows to `log`.
- `sum` sees only plain numbers after the explicit keep/drop step.

## Common Pitfalls

| Pitfall | Bad | Good |
| --- | --- | --- |
| wrong `nth` arity | `nth(5)` | `nth(5, row)` |
| assuming some auto-unwrap | `row |> nth(5) |> parse_int` | `row |> nth(5) |> flat_map_some(parse_int)` |
| wrong helper for dead rows | `keep_some(parse_int)` when you need dead-letter logging | `keep_some_else(parse_int, log)` |
| summing raw Option values | `map(parse_int) |> collect |> sum` | `keep_some(parse_int) |> collect |> sum` |
| forgetting flow sink | `stdin |> lines` | `stdin |> lines |> each(print) |> run` (or use `-p`) |

When dead-row handling is not needed, `keep_some(parse_int)` is a concise keep-only option stage.

## Dead-Letter Pattern

[case: unix-power-dead-letter-pattern]
```genia
rows
  |> lines
  |> keep_some_else(parse_int, log)
  |> collect
```

`parse_int` returns `some(int)` or `none(...)`.
`keep_some_else` unwraps `some(...)` into the main flow and routes `none(...)` items to `log`.

# 🚀 One-Liner to Remember

> “Treat stdin like a stream, pipe it through small functions, and only run when you’re ready.”

---

# 🔥 What This Unlocks

With just this cheatsheet, Genia can already replace:

* `awk`
* `cut`
* `grep`
* `wc`
* parts of `sed`

…and do it in a way that’s:

* safer (Option)
* composable (pipelines)
* readable (left → right)

