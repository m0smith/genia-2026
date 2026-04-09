# 🖥️ Genia Unix → Genia Cheatsheet

Translate common Unix commands into Genia pipelines.

Legend: 🟢 Value  🔵 Flow  🟣 Bridge  🔴 Sink

Validation: runnable rows include `[case: <id>]` markers in Notes and are executed by pytest.

---

## 📄 Basic I/O

| Unix          | Genia                | Notes                         |
| ------------- | -------------------- | ----------------------------- |
| `cat file`    | 🔵 `stdin \|> lines` | Genia assumes stdin as source |
| `echo "text"` | 🟢 `"text"`          | Value expression [case: unix-map-echo-text] |

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
| `awk '{sum += $5}'` | 🟣 `stdin \|> lines \|> map(split_whitespace) \|> map((r) -> nth(4, r) \|> flat_map_some(parse_int)) \|> keep_some \|> collect \|> sum` | Safe numeric sum [case: unix-map-awk-sum-5] |

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
| Sum column    | 🟣 `stdin \|> lines \|> map(split_whitespace) \|> map((r) -> nth(4, r) \|> flat_map_some(parse_int)) \|> keep_some \|> collect \|> sum` | Classic pattern [case: unix-map-pattern-sum-column]   |
| Count matches | 🟣 `stdin \|> lines \|> filter((l) -> contains(l, "error")) \|> collect \|> count`                                | Filter then count [case: unix-map-pattern-count-matches] |

---

## ⚠️ Key Differences from Unix

* Genia is **type-safe** (Option vs silent failure)
* Pipelines are **functional**, not string-based
* `none(...)` replaces missing/invalid data
* Flow is **lazy and single-use**
* `head` / `take` stop upstream pulling early
* Must explicitly end with 🔴 `run` or 🟣 `collect`

---

## 🚀 One-Liner

> Unix: text streams + tools
> Genia: typed streams + functions
