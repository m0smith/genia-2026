# 🖥️ Genia Unix → Genia Cheatsheet

Translate common Unix commands into Genia pipelines.

Legend: 🟢 Value  🔵 Flow  🟣 Bridge  🔴 Sink

Validation: runnable rows include `[case: <id>]` markers in Notes and are executed by pytest. Examples are classified as **Valid** if directly tested, **Likely valid** if not directly tested, **Illustrative** if not runnable, or **Invalid** if contradicted by implementation.

---

## 📄 Basic I/O

| Unix          | Genia                | Notes                         |
| ------------- | -------------------- | ----------------------------- |
| `cat file`    | 🔵 `stdin \|> lines` | Genia assumes stdin as source |
| `echo "text"` | 🟢 `"text"`          | Value expression [case: unix-map-echo-text] |

---

## ⌨️ Real-Time Input

| Use Case | Genia | Notes |
| -------- | ----- | ----- |
| keypress stream | 🔴 `stdin_keys \|> each(handle_input) \|> run` | Python-host-only; captures keypresses without waiting for newline; `stdin` line mode stays unchanged |

---

## 🔢 Counting

| Unix    | Genia                                                                 | Notes        |
| ------- | --------------------------------------------------------------------- | ------------ |
| `wc -l` | 🟣 `stdin \|> lines \|> collect \|> count`                            | Flow → Value [case: unix-map-wc-l] |
| `wc -w` | 🟣 `stdin \|> lines \|> map(split_whitespace) \|> map(count) \|> sum` | Word count   |

---

## 🔍 Filtering (grep)

| Unix            | Genia                                                                                       | Notes            |
| --------------- | ------------------------------------------------------------------------------------------- | ---------------- |
| `grep error`    | 🔴 `stdin \|> lines \|> filter((l) -> contains(l, "error")) \|> each(print) \|> run`        | Basic filter [case: unix-map-grep]     |
| `grep -i error` | 🔴 `stdin \|> lines \|> filter((l) -> contains(lower(l), "error")) \|> each(print) \|> run` | Case-insensitive [case: unix-map-grep-i] |

---

## ✂️ Columns (awk / cut)

| Unix                | Genia                                                                                                             | Notes            |
| ------------------- | ----------------------------------------------------------------------------------------------------------------- | ---------------- |
| `awk '{print $5}'`  | 🔴 `stdin \|> lines \|> map(split_whitespace) \|> map((r) -> nth(4, r)) \|> keep_some \|> each(print) \|> run`                  | 0-based index [case: unix-map-awk-print-5]    |
| `awk '{sum += $5}'` | 🟣 `stdin \|> lines \|> map(split_whitespace) \|> map((r) -> nth(4, r) \|> parse_int) \|> keep_some \|> collect \|> sum` | Safe numeric sum [case: unix-map-awk-sum-5] |

---

## 🔁 Transform

| Unix             | Genia                                                       | Notes     |
| ---------------- | ----------------------------------------------------------- | --------- |
| `tr 'a-z' 'A-Z'` | 🔴 `stdin \|> lines \|> map(upper) \|> each(print) \|> run` | Uppercase [case: unix-map-tr-upper] |

---

## 📍 Head / Tail

| Unix        | Genia                                                    | Notes                 |
| ----------- | -------------------------------------------------------- | --------------------- |
| `head -n 5` | 🔴 `stdin \|> lines \|> head(5) \|> each(print) \|> run` | Short-circuits [case: unix-map-head-5]        |

---

## 📊 Aggregation Patterns

| Pattern       | Genia                                                                                                             | Notes             |
| ------------- | ----------------------------------------------------------------------------------------------------------------- | ----------------- |
| Sum column    | 🟣 `stdin \|> lines \|> map(split_whitespace) \|> map((r) -> nth(4, r) \|> parse_int) \|> keep_some \|> collect \|> sum` | Classic pattern [case: unix-map-pattern-sum-column]   |
| Count matches | 🟣 `stdin \|> lines \|> filter((l) -> contains(l, "error")) \|> collect \|> count`                                | Filter then count [case: unix-map-pattern-count-matches] |

---

## ⏱️ evolve Simulation (Experimental)

| Use Case | Genia | Notes |
| ---- | ----- | ----- |
| Step simulation loop | 🟣 `evolve(5) \|> scan((state, _) -> [state + 1, state + 1], 0) \|> collect` | Experimental discrete-time progression [case: unix-map-evolve-simulation] |

---

## 🎮 Terminal Rendering (Simple Game Loop)

Use terminal helpers for lightweight frame rendering.

[case: unix-map-terminal-game-loop]
```genia
grid_for(n) = (
	0 -> ["XO", "OX"] |
	_ -> ["OX", "XO"]
)

loop(i, max) = (
	(i, max) ? i >= max -> none |
	(i, max) -> {
		clear_screen()
		move_cursor(1, 1)
		render_grid(grid_for(i))
		loop(i + 1, max)
	}
)

loop(0, 2)
```
Classification: **Valid** (directly tested)

Writes two frames using ANSI terminal control and returns `none("nil")`.

---

## 🧭 Debugging Failures

| Unix | Genia | Notes |
| ---- | ----- | ----- |
| `grep + context` | 🟢 `absence_meta(none("missing_key", { key: "user" }))` | Inspect structured absence metadata [case: unix-map-debug-absence-meta] |

---

## ⚠️ Key Differences from Unix

* Genia is **type-safe** (Option vs silent failure)
* Pipelines are **functional**, not string-based
* `none(...)` replaces missing/invalid data
* Flow is **lazy and single-use**
* `head` / `take` stop upstream pulling early
* Must explicitly end with 🔴 `run` or 🟣 `collect`

---

## 🐚 Shell Pipeline Stage (Python-host-only, experimental)

| Unix | Genia | Notes |
| ---- | ----- | ----- |
| `echo hello | tr a-z A-Z` | 🟢 `"hello" |> $(tr a-z A-Z)` | Shell stage in pipeline [case: unix-map-shell-upper] (**Valid**) |
| `echo hello | cat` | 🟢 `"hello" |> $(cat)` | Round-trip through shell [case: unix-map-shell-cat] (**Valid**) |

`$(command)` is only valid inside a pipeline. **Python-host-only**; not part of portable Core IR contract.

---

## �🚀 One-Liner

> Unix: text streams + tools
> Genia: typed streams + functions

---

## CLI Mode Reminder

- use `-p` for stage expressions that still produce a Flow (`stdin |> lines` and final `run` are injected)
- use `-c` or file mode when you want final collected values (for example sums)
- file/`-c` modes apply runtime `main` dispatch: `main(argv())` first, then `main()`
- when no `-c`/`-p` is selected, the first non-mode argument must be a source file path (`--` stops option parsing for dash-prefixed literals)
