# GENIA — Specification Examples (v0.2)

This section provides concrete examples of Genia programs and their behavior.
All examples are valid Genia code and reflect the current language semantics.

---

# 1. Arithmetic and Expressions

```genia
1 + 2 * 3
```

Result:

```text
7
```

---

# 2. Function Definition and Call

```genia
square(x) = x * x

square(5)
```

Result:

```text
25
```

---

# 3. Multiple Arity Functions

```genia
f(x) = x
f(x, y) = x + y

f(3)
f(3, 4)
```

Results:

```text
3
7
```

---

# 4. Recursive Functions

```genia
fact(n) =
  0 -> 1 |
  n -> n * fact(n - 1)

fact(5)
```

Result:

```text
120
```

---

# 5. List Processing

## 5.1 Length

```genia
len(xs) =
  [] -> 0 |
  [_, ..rest] -> 1 + len(rest)

len([10, 20, 30])
```

Result:

```text
3
```

---

## 5.2 Head and Tail

```genia
head(xs) =
  [x, .._] -> x

tail(xs) =
  [_, ..rest] -> rest

head([5, 6, 7])
tail([5, 6, 7])
```

Results:

```text
5
[6, 7]
```

---

# 6. Pattern Matching

## 6.1 Tuple Matching

```genia
add(x, y) =
  (0, y) -> y |
  (x, 0) -> x |
  (x, y) -> x + y

add(0, 5)
add(3, 0)
add(2, 3)
```

Results:

```text
5
3
5
```

---

## 6.2 Duplicate Binding

```genia
same(xs) =
  [x, x] -> true |
  _ -> false

same([1, 1])
same([1, 2])
```

Results:

```text
true
false
```

---

## 6.3 Nested Patterns

```genia
nested(xs) =
  [[x, x], y] -> true |
  _ -> false

nested([[3, 3], 9])
nested([[3, 4], 9])
```

Results:

```text
true
false
```

---

# 7. Lambdas

## 7.1 Basic Lambda

```genia
(x) -> x + 1
```

(returns a function)

---

## 7.2 Lambda Application

```genia
apply2(f, a, b) = f(a, b)

apply2((x, y) -> x * y, 6, 7)
```

Result:

```text
42
```

---

## 7.3 Closure

```genia
makeAdder(n, x) =
  ((y) -> y + n)(x)

makeAdder(10, 7)
```

Result:

```text
17
```

---

# 8. Host-backed Concurrency and Agents

## 8.1 Basic Process + Send

```genia
inbox = ref([])
p = spawn((msg) -> ref_update(inbox, (xs) -> append(xs, [msg])))
send(p, "a")
send(p, "b")
send(p, "c")
ref_get(inbox)
```

Result (after mailbox drains):

```text
["a", "b", "c"]
```

## 8.2 Ref Used with a Process

```genia
total = ref(0)
p = spawn((msg) -> ref_update(total, (n) -> n + msg))
send(p, 10)
send(p, 5)
ref_get(total)
```

Result (after mailbox drains):

```text
15
```

## 8.3 Simple Counter Agent

```genia
counter = agent(0)
agent_send(counter, (n) -> n + 1)
agent_send(counter, (n) -> n + 1)
agent_send(counter, (n) -> n + 1)
agent_get(counter)
```

Result (after mailbox drains):

```text
3
```

## 8.4 Logging / Background Worker Pattern

```genia
append_logged(xs, msg) {
  log(msg)
  append(xs, [msg])
}

logs = ref([])
logger = spawn((msg) -> ref_update(logs, (xs) -> append_logged(xs, msg)))
send(logger, "boot")
send(logger, "request")
send(logger, "done")
ref_get(logs)
```

Result (after mailbox drains):

```text
["boot", "request", "done"]
```

## 8.5 Process Liveness

```genia
p = spawn((msg) -> msg)
process_alive?(p)
```

Result:

```text
true
```

---

# 9. Blocks

```genia
double(x) {
  log(x)
  x * 2
}

double(5)
```

Result:

```text
10
```

(Side effect: logs `5`)

---

# 10. Case Expressions in Blocks

```genia
classify(n) {
  log(n)
  0 -> "zero" |
  n -> "nonzero"
}

classify(0)
classify(5)
```

Results:

```text
"zero"
"nonzero"
```

---

# 10. Top-Level Assignment

```genia
add(x, y) = x + y

a = 10
b = add(a, 5)
b
```

Result:

```text
15
```

---

# 11. Higher-Order Functions

## 11.1 Reduce

```genia
reduce(f, acc, xs) =
  (f, acc, []) -> acc |
  (f, acc, [x, ..rest]) -> reduce(f, f(acc, x), rest)

reduce((acc, x) -> acc + x, 0, [1, 2, 3, 4])
```

Result:

```text
10
```

---

## 11.2 Count

```genia
count(xs) = reduce((acc, _) -> acc + 1, 0, xs)

count([1, 2, 3, 4])
```

Result:

```text
4
```

---

## 11.3 Sum

```genia
sum(xs) = reduce((acc, x) -> acc + x, 0, xs)

sum([1, 2, 3, 4])
```

Result:

```text
10
```

---

# 12. Autoload Behavior

```genia
count([1,2,3])
```

Behavior:

* `count` is not defined initially
* runtime loads `std/prelude/list.genia`
* function becomes available
* call is retried

Result:

```text
3
```

---

# 13. Errors

## 13.1 No Matching Case

```genia
f(xs) =
  [] -> 0

f([1])
```

Error:

```text
No matching case
```

---

## 13.2 Undefined Name

```genia
mystery
```

Error:

```text
Undefined name: mystery
```

---

## 13.3 Invalid Pattern

```genia
f(xs) =
  [..rest, x] -> x
```

Error:

```text
..rest must be the final item in a list pattern
```

---

## 13.4 Arity Mismatch

```genia
f(x) = x

f(1, 2)
```

Error:

```text
No matching function: f/2
```

---

## 13.5 Runtime Recursion

```genia
loop() = loop()

loop()
```

Error:

```text
maximum recursion depth exceeded
```

---

# 🏁 Summary

These examples demonstrate:

* Function definition and recursion
* Pattern matching (including nested and duplicate bindings)
* List destructuring with rest patterns
* Lambda functions and closures
* Processes, refs, and agents for host-backed concurrency
* Blocks and evaluation order
* Higher-order functions
* Autoloaded standard library
* Error behavior

They serve both as documentation and as executable regression tests.
