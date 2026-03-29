# Genia

Genia is a small, expressive, functional-first programming language designed to be:

* Simple to implement
* Easy to read and write
* Composable at every level
* Immediately useful for scripting and data transformation

Genia emphasizes a minimal core with powerful composition. Most functionality—including the standard library—is written in Genia itself.

---

## ✨ Core Ideas

* **Expression-oriented** — everything returns a value
* **Functional-first** — functions are the primary building block
* **Minimal syntax** — few rules, consistently applied
* **Pattern matching** — replaces most conditional logic
* **Composable by design** — small pieces combine naturally

---

## 🚀 Quick Example

```genia
fact(n) =
  0 -> 1 |
  n -> n * fact(n - 1)

fact(5)
```

---

## 🧠 Language Overview

### Values

Genia supports a small set of core types:

* Number
* String
* Boolean (`true`, `false`)
* Nil (`nil`)
* List
* Function

---

### Functions

Functions are first-class and defined using `=`:

```genia
square(x) = x * x
square(5)
```

Functions are **dispatched by name and arity**:

```genia
f(x) = x
f(x, y) = x + y
```

---

### Lambdas

Anonymous functions:

```genia
(x) -> x + 1
(x, y) -> x + y
```

Lambdas:

* are ordinary expressions
* can appear anywhere
* capture surrounding variables (closures)

---

### Pattern Matching

Pattern matching is central to control flow:

```genia
len(xs) =
  [] -> 0 |
  [_, ..rest] -> 1 + len(rest)
```

Rules:

* patterns match the full argument tuple
* first matching case wins
* duplicate bindings must agree

```genia
[x, x]   # matches only if both elements are equal
```

---

### List Patterns

Lists are first-class:

```genia
[1, 2, 3]
```

Pattern destructuring:

```genia
[x, y]
[x, ..rest]
```

Rules:

* `..rest` matches zero or more elements
* `..rest` must be the final element in the pattern

---

### Case Expressions

Case expressions define pattern-based behavior:

```genia
fact(n) =
  0 -> 1 |
  n -> n * fact(n - 1)
```

They are allowed only:

* as a function body
* as the final expression in a block

They are **not allowed**:

* as arbitrary subexpressions
* as function arguments
* inside list literals

---

### Blocks

Blocks group multiple expressions:

```genia
double(x) {
  log(x)
  x * 2
}
```

Rules:

* expressions are separated by newlines
* the last expression is returned
* a block may end with a case expression

---

## ⚙️ Host-backed Concurrency (Minimal)

Genia exposes a tiny process/mailbox substrate through builtins:

* `spawn(handler)` → creates a process handle
* `send(process, message)` → enqueues a message to that process mailbox
* `process_alive?(process)` → checks whether the host worker thread is alive

### Semantics

* **Process creation**: `spawn` starts a host-backed worker (Python thread) that runs forever and invokes `handler(msg)` for each received message.
* **Mailbox ordering**: for a single process, messages are handled in FIFO order (`send(p, a)` then `send(p, b)` means `a` is handled before `b`).
* **Serial processing per process**: each process handles one message at a time; no concurrent handler execution within the same process.
* **Host-backed concurrency**: this feature is implemented by the runtime host (not as a pure language-level scheduler).

### Runnable Examples

```genia
# 1) Basic process + send
inbox = ref([])
p = spawn((msg) -> ref_update(inbox, (xs) -> append(xs, [msg])))
send(p, "a")
send(p, "b")
send(p, "c")
ref_get(inbox)  # eventually ["a", "b", "c"]
```

```genia
# 2) Ref used with a process
total = ref(0)
acc = spawn((msg) -> ref_update(total, (n) -> n + msg))
send(acc, 10)
send(acc, 5)
ref_get(total)  # eventually 15
```

```genia
# 3) Simple counter agent (autoloaded from std/prelude/agent.genia)
counter = agent(0)
agent_send(counter, (n) -> n + 1)
agent_send(counter, (n) -> n + 1)
agent_get(counter)  # eventually 2
```

```genia
# 4) Logging/background worker pattern
append_logged(xs, msg) {
  log(msg)
  append(xs, [msg])
}

logs = ref([])
logger = spawn((msg) -> ref_update(logs, (xs) -> append_logged(xs, msg)))
send(logger, "boot")
send(logger, "request")
ref_get(logs)  # eventually ["boot", "request"]
```

```genia
# Observe liveness
p = spawn((msg) -> msg)
process_alive?(p)  # true
```

---

## 📚 Standard Library (Autoloaded)

Genia’s standard library is written in Genia and loaded on demand.

Examples:

```genia
count([1,2,3,4])  # → 4
sum([1,2,3,4])    # → 10
```

These functions are:

* **not loaded at startup**
* loaded automatically when first used

Autoload is keyed by:

```
(name, arity)
```

---

### Example: reduce

```genia
reduce(f, acc, xs) =
  (f, acc, []) -> acc |
  (f, acc, [x, ..rest]) -> reduce(f, f(acc, x), rest)
```

---

## 🔁 Evaluation Model

* Functions receive arguments as a tuple
* Patterns are checked top-to-bottom
* First match wins
* Guards (future) will refine matches
* All constructs return values

---

## ⚠️ Current Limitations (v0.2)

Genia intentionally keeps the core small. These are **not yet part of the language**:

* Modules / imports (autoload used instead)
* Static typing
* Exceptions
* Objects / classes
* Protocols
* Map/dictionary literals (planned)

---

## 🧰 VS Code Extension

A minimal VS Code extension lives at `vscode/genia-debugger` and now includes:

* `.genia` file recognition
* Syntax highlighting
* Basic editor language configuration (comments, brackets, indentation)
* Debugging support via the `genia` launch configuration

To run it in dev mode, see `vscode/genia-debugger/README.md`.

---

## 🧪 Running Tests

```bash
uv run pytest -q
```

---

## 🧱 Project Structure

```text
src/genia/
  interpreter.py

tests/
  test_*.py
  cases/

std/
  prelude/
    list.genia
    math.genia
```

---

## 🔮 Design Direction

Genia grows by layering:

* A minimal core language
* A Genia-written standard library
* Lazy loading via autoload
* Future modules and tooling

The goal is a language that stays small, but becomes powerful through composition.

---

## 🧭 Philosophy

Genia is built on a few core principles:

* Prefer fewer concepts used consistently
* Make behavior explicit and readable
* Keep parsing simple and predictable
* Let the standard library do the heavy lifting

---

## 🏁 Summary

Genia is:

* Small
* Functional
* Pattern-driven
* Composable
* Easy to implement

It achieves power not through complexity, but through a minimal set of well-chosen features.
