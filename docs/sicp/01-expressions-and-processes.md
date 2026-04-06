# 1. Expressions and Processes

You are not here to admire syntax.

You are here to make a machine do something precise.

Good news: Genia is very honest about that.

Bad news: Genia is very honest about that.

If you ask for nonsense, it tends to hand you nonsense right back.

That turns out to be useful.

## Chapter Status

✅ Implemented in this chapter:

- `Number`, `String`, `Boolean`, `nil`
- arithmetic and comparison
- function definition and application
- pattern matching as the only conditional model
- blocks
- lexical assignment
- closures
- proper tail calls

⚠️ Partial in this chapter:

- we mention lists briefly, but list-processing gets its own chapter
- we mention code-as-data briefly, but `quote`, `quasiquote`, and metacircular evaluation come later

❌ Future or not in this chapter:

- `if`
- `switch`
- macro systems
- automatic laziness

## 1.1 Computation Is "Evaluate This"

🤔 Think About It

What does this do?

```genia
1 + 2 * 3
```

Stop.

Actually guess.

No fake guessing.

The answer is:

```text
7
```

💡 Aha!

Genia is expression-oriented.

That means the language is mostly built from things that produce values.

Not "do this statement, then maybe something happens later."

More like:

```text
expression in
value out
```

Like a vending machine, except the snack is math.

🧠 Your Brain on Genia

You might be thinking:

"Okay, sure, arithmetic. Every language can do arithmetic."

Yes.

But here is the important part:

Genia keeps pushing that same idea upward.
Functions produce values.
Blocks produce values.
Pattern matches produce values.

That consistency is the whole game.

🧪 Try This

Run each of these and predict the result before you do:

```genia
[40 + 2, 10 - 3 * 2, (10 - 3) * 2, 5 % 2]
```

```text
[42, 4, 14, 1]
```

⚠️ Common Trap

This:

```genia
1 + 2 * 3
```

```text
7
```

is not the same as:

```genia
(1 + 2) * 3
```

```text
9
```

If your brain says "eh, same ingredients," your brain is being a chaos goblin.

🧩 Puzzle

What does this return?

```genia
1 + 2 + 3 * 4
```

```text
15
```

Write the answer down before you move on.

## 1.2 Names Let You Stop Repeating Yourself

🤔 Think About It

If you need "square something" more than once, do you really want to keep retyping `x * x` forever like a cursed spreadsheet?

No.

Use a function.

```genia
square(x) = x * x

square(12)
```

Result:

```text
144
```

💡 Aha!

A function gives a name to a process.

You hand it values.
It gives you back a value.

That means you can build bigger computations out of smaller ones.

```genia
square(x) = x * x

sum_of_squares(a, b) = square(a) + square(b)

sum_of_squares(3, 4)
```

That returns:

```text
25
```

🔁 Let's Rewrite That

These two ideas are equivalent in spirit:

```genia
3 * 3
```

```text
9
```

and:

```genia
square(x) = x * x

square(3)
```

```text
9
```

The second one is nicer because it says what you mean.

That matters once programs stop fitting inside your head all at once.

🧠 Your Brain on Genia

You may feel a tiny urge to ask:

"Where are the `return` statements?"

There aren't any here.

The function body is an expression.
The value of that expression is the result.

🧪 Try This

Predict these before running them:

```genia
square(x) = x * x

sum_of_squares(a, b) = square(a) + square(b)

[square(5), sum_of_squares(2, 5), square(square(2))]
```

```text
[25, 29, 16]
```

⚠️ Common Trap

This `square = x * x` is not a function definition.

It tries to assign the value of `x * x`, but `x` is not bound there.

Use:

**Example only — not runnable**
```genia
square(x) = x * x
```

instead.

Failure case:

```genia
square = x * x
```

```text
Error: Undefined name: x
```

## 1.3 No `if`. Pattern Matching Does the Branching.

Wait.

No `if`?

Correct.

Genia is not being difficult.

It is being specific.

🤔 Think About It

How would you write absolute value without `if`?

Here is one honest answer:

```genia
abs(n) =
  (n) ? n < 0 -> -n |
  _ -> n

[abs(-3), abs(0), abs(7)]
```

Result:

```text
[3, 0, 7]
```

💡 Aha!

Pattern matching is Genia's conditional model.

That means branching happens by asking:

- what shape did I get?
- what value did I get?
- does a guard succeed?

Not by reaching for separate `if` syntax.

Here is the same idea with structure instead of just numbers:

**Example only — not runnable**
```genia
head(xs) =
  [x, .._] -> x
```

That says:

"If the list starts with `x`, return `x`."

ASCII Picture

```text
[10, 20, 30]
 ^
 x
```

🧠 Your Brain on Genia

This is usually the moment when people think:

"Wait, is pattern matching a special fancy thing for weird cases?"

No.

It is the normal thing.

The weird thing is languages that make you switch mental models every five minutes.

🧪 Try This

What do you expect?

```genia
describe(xs) =
  [] -> "empty" |
  [x] -> "one" |
  [x, y, .._] -> "many"

[describe([]), describe([1]), describe([1, 2, 3])]
```

```text
["empty", "one", "many"]
```

⚠️ Common Trap

Do not write imaginary syntax from some other language:

```text
if n < 0 then -n else n
```

That is not Genia.

Use a case body or pattern-based function clauses instead.

Failure case:

```genia
head(xs) =
  [x, .._] -> x

head([])
```

```text
Error: No matching case for function head/1 with arguments ([],)
```

🧩 Puzzle

Write a function `sign(n)` that returns:

- `-1` for negative numbers
- `0` for zero
- `1` for positive numbers

Use pattern matching plus guards.

## 1.4 Blocks Let You Build a Process Step by Step

🤔 Think About It

What if the computation is easier to explain in stages?

Use a block.

```genia
{
  x = 10
  x = x + 5
  x
}
```

Result:

```text
15
```

💡 Aha!

A block evaluates expressions in order and returns the last one.

That gives you a local workspace.

Not a pile of statements.

A workspace made out of expressions.

Like this:

```text
step 1: x = 10
step 2: x = x + 5
step 3: result is x
```

🧠 Your Brain on Genia

You might be thinking:

"Hold on. Didn't you say Genia is immutable by default? Why can `x` change?"

Great question.

Data values are still ordinary values.

But lexical names can be rebound within scope.

That means:

- lists do not become secretly mutable
- maps do not become secretly mutable
- names can point at a new value later in the same scope

🧪 Try This

Predict the result:

```genia
{
  total = 3
  total = total * 4
  total = total - 1
  total
}
```

```text
11
```

🔁 Let's Rewrite That

Sometimes a block makes a process easier to read:

**Example only — not runnable**
```genia
hypotenuse(a, b) = {
  aa = a * a
  bb = b * b
  aa + bb
}
```

It is still just value computation.

⚠️ Common Trap

A block returns its last expression.

So this returns `20`, not `10`:

```genia
{
  x = 10
  20
}
```

```text
20
```

If the last expression is wrong, the result is wrong.

## 1.5 Closures Remember Their Lexical World

🤔 Think About It

Can a function remember something from the place where it was created?

Yes.

Watch this:

```genia
make_counter() = {
  n = 0
  () -> {
    n = n + 1
    n
  }
}

c = make_counter()
[c(), c(), c()]
```

Result:

```text
[1, 2, 3]
```

Pause.

That is a big deal.

💡 Aha!

The inner function closes over the lexical binding `n`.

Not a copy of the source text.

Not a magical global variable.

The actual lexical environment.

That is why each call can see the updated value.

ASCII Picture

```text
make_counter()
  creates n = 0
  creates function ----+
                       |
call function <--------+
  update n
  return n
```

🧠 Your Brain on Genia

This is usually where people say:

"So... is that a ref?"

No.

Refs are explicit capability values in Genia.

This is lexical rebinding inside a closure.

Different tool.

Same "wow, it remembered" feeling.

🧪 Try This

Predict this before running it:

```genia
make_counter() = {
  n = 0
  () -> {
    n = n + 1
    n
  }
}

a = make_counter()
b = make_counter()
[a(), a(), b(), a(), b()]
```

```text
[1, 2, 1, 3, 2]
```

If your answer is `[1, 2, 1, 3, 2]`, you are thinking like the language now.

⚠️ Common Trap

Do not assume every closure shares the same state.

Each call to `make_counter()` creates a fresh lexical environment.

That is why `a` and `b` do not stomp on each other.

## 1.6 Processes: Recursive Does Not Mean "Doomed"

🤔 Think About It

What does this compute?

```genia
sum_to(n, acc) =
  (n, acc) ? n == 0 -> acc |
  (n, acc) -> sum_to(n - 1, acc + n)

sum_to(10, 0)
```

Result:

```text
55
```

💡 Aha!

This is a recursive process, but it is in tail position.

That matters because Genia guarantees proper tail calls.

So the process can run in constant stack space.

In plain English:

```text
old step finishes
new step takes over
stack does not keep growing forever
```

That is not "maybe the compiler is smart today."

It is part of the language behavior.

🔁 Let's Rewrite That

This version:

**Example only — not runnable**
```genia
sum_to(n, acc) =
  (n, acc) ? n == 0 -> acc |
  (n, acc) -> sum_to(n - 1, acc + n)
```

describes an iterative process.

This version:

**Example only — not runnable**
```genia
sum_to_slow(n) =
  (n) ? n == 0 -> 0 |
  (n) -> n + sum_to_slow(n - 1)
```

still works for small inputs, but it is not tail-recursive.

That means it still consumes stack.

🧠 Your Brain on Genia

Many people learn recursion as:

"Call yourself and hope nothing catches fire."

That is not the right lesson.

The real lesson is:

"What process does this description create?"

Tail-recursive descriptions can create iterative processes.

Mini challenge:

What does this return?

```genia
fact(n, acc) =
  (n, acc) ? n == 0 -> acc |
  (n, acc) -> fact(n - 1, acc * n)

fact(5, 1)
```

```text
120
```

🧩 Puzzle

Rewrite factorial in a tail-recursive style:

**Conceptual example — not directly runnable**

```text
fact(n, acc) = ...
```

Then predict:

```genia
fact(n, acc) =
  (n, acc) ? n == 0 -> acc |
  (n, acc) -> fact(n - 1, acc * n)

fact(5, 1)
```

```text
120
```

## 1.7 Tiny Teaser: Programs Can Become Data

You do not need this to survive chapter 1.

But it is too fun not to mention.

🤔 Think About It

What should this return?

```genia
quote(1 + 2)
```

Not `3`.

It returns:

```text
(app + 1 2)
```

💡 Aha!

Genia can treat code as data.

Later, that becomes the doorway to evaluators, symbolic computation, and stream tricks that make your brain sit up and point.

For now, just remember:

```text
normal evaluation:
  1 + 2  -> 3

quoted evaluation:
  quote(1 + 2) -> (app + 1 2)
```

⚠️ Common Trap

`quote(...)` does not evaluate its argument.

That is the point.

## What You Should Now Feel In Your Bones

- computation in Genia is built from expressions
- functions name processes
- pattern matching is the only branching model
- blocks let you evaluate in sequence and return a value
- lexical assignment rebinds names in scope
- closures remember their lexical environment
- tail recursion can describe iterative processes

If some of that still feels slippery, good.

Slippery means your brain is still rewiring itself.

## End-of-Chapter Playground

Try each one without looking up the answer first.

```genia
square(x) = x * x
square(9)
```

```text
81
```

```genia
abs(n) =
  (n) ? n < 0 -> -n |
  _ -> n

abs(-42)
```

```text
42
```

```genia
{
  x = 3
  x = x + 4
  x * 2
}
```

```text
14
```

```genia
sum_to(n, acc) =
  (n, acc) ? n == 0 -> acc |
  (n, acc) -> sum_to(n - 1, acc + n)

sum_to(100, 0)
```

```text
5050
```

```genia
quote(square(5))
```

```text
(app square 5)
```

If you can explain why each result is what it is, you are not just reading anymore.

You are driving.

## Solutions

Here are the answers to the chapter puzzles and playground.

### Arithmetic Warm-Up Puzzle

```text
1 + 2 + 3 * 4 -> 15
```

### Sign Puzzle

One valid answer:

```genia
sign(n) =
  (n) ? n < 0 -> -1 |
  (n) ? n == 0 -> 0 |
  _ -> 1

[sign(-2), sign(0), sign(9)]
```

```text
[-1, 0, 1]
```

### Tail-Recursive Factorial Puzzle

```genia
fact(n, acc) =
  (n, acc) ? n == 0 -> acc |
  (n, acc) -> fact(n - 1, acc * n)

fact(5, 1)
```

```text
120
```

### Playground Answers

```text
square(9) -> 81
abs(-42) -> 42
{ x = 3 x = x + 4 x * 2 } -> 14
sum_to(100, 0) -> 5050
quote(square(5)) -> (app square 5)
```
