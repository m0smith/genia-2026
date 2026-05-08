# Note: Examples in this cheatsheet are validated by the Semantic Spec System where covered. Active categories: eval, ir, cli, flow, error, parse (coverage varies by category). See GENIA_STATE.md for authoritative status.

# Genia CLI Cheatsheet: Unix Power Mode

Only includes currently implemented Genia CLI and Flow behavior. All shell pipeline stage features described below are implemented only in the Python reference host, not in the portable language contract.

Validation: runnable snippets include `[case: <id>]` markers and are executed by pytest. Examples are classified as **Valid** if directly tested, **Likely valid** if not directly tested, **Illustrative** if not runnable, or **Invalid** if contradicted by implementation.

## Core CLI Shapes

| Mode | Command | Notes |
| --- | --- | --- |
| command mode | `genia -c 'source'` | run full source expression/program |
| pipe mode | `genia -p 'stage_expr'` | runs the stage expression over `stdin |> lines`, then consumes the final Flow automatically |
| file mode | `genia path/to/file.genia` | run file source |
| REPL mode | `genia` | interactive loop |

Use `-c` for value-producing pipelines such as sums.
Use `-p` for flow-stage pipelines ending in effects.
In file/`-c` mode, runtime dispatch is `main(argv())` first, then `main()`.
When no `-c` or `-p` is selected, the first non-mode argument must be a source file path.
Use `--` to stop option parsing when a literal arg/path starts with `-`.
In `-p`, stage helpers still receive a Flow, so per-row work should go through `map(...)`, `filter(...)`, `each(...)`, `keep_some(...)`, or `keep_some_else(...)`.

For file-based terminal demos, keep controls as ordinary trailing args parsed by `main(argv())`.
For example, `examples/ants_terminal.genia` accepts `--seed`, `--ants`, `--steps`, `--delay`, `--size`, and `--mode pure|actor`; it is a blocking text UI, not a `stdin_keys` pause/step loop.

## Reliable Pipeline Building Blocks

| Goal | Building blocks |
| --- | --- |
| row source | `stdin |> lines` |
| flow transform | `map`, `filter`, `head`, `keep_some_else` |
| side effects | `each(print)`, `each(log)` |
| materialize | `collect` |
| maybe-safe parse | `parse_int`, `flat_map_some`, `unwrap_or` |
| numeric aggregate | `keep_some(...) |> collect |> sum` or `map((x) -> unwrap_or(...)) |> collect |> sum` |

Flow rules:
- Flow stays lazy and single-use.
- `head` / `take` stop upstream pulling as soon as they have enough items.
- `collect` and `run` are the explicit Flow → Value / Flow → effect boundaries.
- `map` and `filter` are polymorphic: they work on both lists and flows.
- Pipe mode is only for stage expressions that still produce a Flow.
- Raw values stay values, flows stay flows, only explicit bridges cross.
- See `docs/cheatsheet/piepline-flow-vs-value.md` for the full classification matrix.

## Working Commands

### Print stdin rows

[case: unix-power-print-stdin-rows]
```bash
cat file.txt | genia -p 'each(print)'
```
Classification: **Valid** (directly tested)

### Keep first 5 rows

[case: unix-power-head-5]
```bash
cat file.txt | genia -p 'head(5) |> each(print)'
```
Classification: **Valid** (directly tested)

### Count rows

[case: unix-power-count-rows]
```bash
cat file.txt | genia -c 'stdin |> lines |> collect |> count'
```
Classification: **Valid** (directly tested)

### Grep-style filter

[case: unix-power-grep]
```bash
cat file.txt | genia -p 'filter((l) -> contains(l, "error")) |> each(print)'
```
Classification: **Valid** (directly tested)

### Case-insensitive grep-style filter

[case: unix-power-grep-i]
```bash
cat file.txt | genia -p 'filter((l) -> contains(lower(l), "error")) |> each(print)'
```
Classification: **Valid** (directly tested)

### Uppercase all rows

[case: unix-power-upper]
```bash
cat file.txt | genia -p 'map(upper) |> each(print)'
```
Classification: **Valid** (directly tested)

### Sum the 5th column (AWK-style)

[case: unix-power-sum-5th]
```bash
ls -l | genia -c '
  stdin
    |> lines
    |> map(fields)
    |> keep_some_else((row) -> row |> nth(5) |> parse_int, log)
    |> collect
    |> sum
'
```
Classification: **Valid** (directly tested)

Notes:
- `fields(row)` keeps the original row at index `0`.
- `nth(5, row)` targets the fifth whitespace field.
- `keep_some_else` keeps good parsed ints and sends bad rows to `log`.
- `sum` sees only plain numbers after the explicit keep/drop step.

## Canonical daily tasks

- line filtering: `genia -p 'filter((l) -> contains(l, "error")) |> each(print)'` (tested by case id `unix-power-grep`)
- trim blank lines: `genia -p 'map(trim) |> filter((line) -> line != "") |> each(print)'` (covered in CLI regression tests)
- extract a field: `genia -p 'map(split_whitespace) |> map((r) -> nth(4, r)) |> keep_some |> each(print)'` (tested by case id `unix-map-awk-print-5`)
- parse/filter/sum: `genia -c 'stdin |> lines |> map(fields) |> keep_some_else((row) -> row |> nth(5) |> parse_int, log) |> collect |> sum'` (tested by case id `unix-power-sum-5th`)
- command/file mode with `main(argv())`: `genia -c 'main(args) = args' --pretty input.txt` and `genia script.genia --pretty input.txt` (covered by CLI regression tests)

## Common Pitfalls

| Pitfall | Bad | Good |
| --- | --- | --- |
| wrong `nth` arity | `nth(5)` | `nth(5, row)` |
| forcing explicit Option helpers when plain stage lifting already works | `row |> nth(5) |> flat_map_some(parse_int)` | `row |> nth(5) |> parse_int` |
| wrong helper for dead rows | `keep_some(parse_int)` when you need dead-letter logging | `keep_some_else(parse_int, log)` |
| summing raw Option values | `map(parse_int) |> collect |> sum` | `keep_some(parse_int) |> collect |> sum` |
| using a reducer directly in `-p` | `genia -p 'sum'` | `genia -c 'stdin |> lines |> ... |> collect |> sum'` |
| forgetting flow sink | `stdin |> lines` | `stdin |> lines |> each(print) |> run` (or use `-p`) |
| reusing a consumed flow | bind once, then `collect` and `run` it again | materialize with `collect` if you need reusable data |

When dead-row handling is not needed, `keep_some(parse_int)` is a concise keep-only option stage.

## Dead-Letter Pattern

[case: unix-power-dead-letter-pattern]
```genia
rows
  |> lines
  |> keep_some_else(parse_int, log)
  |> collect
```
Classification: **Valid** (directly tested)

`parse_int` returns `some(int)` or `none(...)`.
`keep_some_else` unwraps `some(...)` into the main flow and routes `none(...)` items to `log`.
Use `absence_meta(opt)` when dead-letter handlers need structured reason/context inspection.

# � Shell Pipeline Stage (Python-host-only)


> **Python-host-only** — `$(command)` executes a host shell command inside a pipeline. This is not part of the portable language contract; it is only available in the Python reference host.

| Pattern | Genia | Notes |
| --- | --- | --- |
| Pipe string to shell | `"hello" \|> $(tr a-z A-Z)` | stdout captured as string |
| Shell in flow pipeline | `stdin \|> lines \|> collect \|> join("\n") \|> $(sort)` | Materializes first |
| Empty shell output | `"x" \|> $(tr -d x)` | Returns `none("empty-shell-output")` |
| Non-zero exit | `"hello" \|> $(false)` | RuntimeError |

<!-- [case: unix-power-shell-upper] -->
```bash
genia -c '"hello" |> $(tr a-z A-Z)'
```

Classification: **Valid** (directly tested)

[case: unix-power-shell-cat]
```bash
genia -c '"hello world" |> $(cat)'
```

Classification: **Valid** (directly tested)

Expected result: the string is uppercased by the host `tr` command (first example), or round-trips through `cat` unchanged (second example).

Limitations:

* Python-host-only; not part of portable Core IR or portable language contract
* `$(...)` is only valid inside a pipeline
* Non-zero exit raises `RuntimeError`

# �🚀 One-Liner to Remember

> “Treat stdin like a stream, pipe it through small functions, and only run when you’re ready.”

---

# 🔥 What This Unlocks

With just this cheatsheet, Genia can already replace:

* `awk`
* `cut`
* `grep`
* `wc`
* parts of `sed`
* host shell commands via `$(...)` (Python-host-only)

…and do it in a way that’s:

* safer (Option)
* composable (pipelines)
* readable (left → right)
