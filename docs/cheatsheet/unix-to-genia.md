# 🖥️ Genia Unix → Genia Cheatsheet

Translate common Unix commands into Genia pipelines.

Legend: 🟢 Value  🔵 Flow  🟣 Bridge  🔴 Sink

---

## 📄 Basic I/O

| Unix          | Genia                | Notes                         |
| ------------- | -------------------- | ----------------------------- |
| `cat file`    | 🔵 `stdin \|> lines` | Genia assumes stdin as source |
| `echo "text"` | 🟢 `"text"`          | Value expression              |

---

## 🔢 Counting

| Unix    | Genia                                                                 | Notes        |
| ------- | --------------------------------------------------------------------- | ------------ |
| `wc -l` | 🟣 `stdin \|> lines \|> collect \|> count`                            | Flow → Value |
| `wc -w` | 🟣 `stdin \|> lines \|> map(split_whitespace) \|> map(count) \|> sum` | Word count   |

---

## 🔍 Filtering (grep)

| Unix            | Genia                                                                                       | Notes            |
| --------------- | ------------------------------------------------------------------------------------------- | ---------------- |
| `grep error`    | 🔴 `stdin \|> lines \|> filter((l) -> contains(l, "error")) \|> each(print) \|> run`        | Basic filter     |
| `grep -i error` | 🔴 `stdin \|> lines \|> filter((l) -> contains(lower(l), "error")) \|> each(print) \|> run` | Case-insensitive |

---

## ✂️ Columns (awk / cut)

| Unix                | Genia                                                                                                             | Notes            |
| ------------------- | ----------------------------------------------------------------------------------------------------------------- | ---------------- |
| `awk '{print $5}'`  | 🔴 `stdin \|> lines \|> map(split_whitespace) \|> map((r) -> nth(r, 4)) \|> each(print) \|> run`                  | 0-based index    |
| `awk '{sum += $5}'` | 🟣 `stdin \|> lines \|> map(split_whitespace) \|> map((r) -> nth(r, 4)) \|> map(parse_int) \|> keep_some \|> sum` | Safe numeric sum |

---

## 🔁 Transform

| Unix             | Genia                                                       | Notes     |
| ---------------- | ----------------------------------------------------------- | --------- |
| `tr 'a-z' 'A-Z'` | 🔴 `stdin \|> lines \|> map(upper) \|> each(print) \|> run` | Uppercase |

---

## 📍 Head / Tail

| Unix        | Genia                                                    | Notes                 |
| ----------- | -------------------------------------------------------- | --------------------- |
| `head -n 5` | 🔴 `stdin \|> lines \|> head(5) \|> each(print) \|> run` | Short-circuits        |
| `tail -n 5` | 🔴 `stdin \|> lines \|> tail(5) \|> each(print) \|> run` | May require buffering |

---

## 🔀 Sort / Unique

| Unix   | Genia                                                   | Notes                 |
| ------ | ------------------------------------------------------- | --------------------- |
| `sort` | 🟣 `stdin \|> lines \|> collect \|> sort`               | Requires Value        |
| `uniq` | 🔴 `stdin \|> lines \|> unique \|> each(print) \|> run` | Assumes helper exists |

---

## 📊 Aggregation Patterns

| Pattern       | Genia                                                                                                             | Notes             |
| ------------- | ----------------------------------------------------------------------------------------------------------------- | ----------------- |
| Sum column    | 🟣 `stdin \|> lines \|> map(split_whitespace) \|> map((r) -> nth(r, 4)) \|> map(parse_int) \|> keep_some \|> sum` | Classic pattern   |
| Count matches | 🟣 `stdin \|> lines \|> filter((l) -> contains(l, "error")) \|> collect \|> count`                                | Filter then count |

---

## ⚠️ Key Differences from Unix

* Genia is **type-safe** (Option vs silent failure)
* Pipelines are **functional**, not string-based
* `none(...)` replaces missing/invalid data
* Flow is **lazy and single-use**
* Must explicitly end with 🔴 `run` or 🟣 `collect`

---

## 🚀 One-Liner

> Unix: text streams + tools
> Genia: typed streams + functions
