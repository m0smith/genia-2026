# Model B Slice E: closed-function publication (E1 + E2)

Status: **APPROVED DESIGN, iteration 3, with final semantic rulings reconciled for E1 RED. Nothing here is implemented.**
Python parses and lowers closed `f(pattern) =: expression` groups, and evaluation
still rejects them with `model-b-not-implemented`. `GENIA_STATE.md` remains the only
authority on implemented behavior. Phase record for
[#1250](https://github.com/m0smith/genia-2026/issues/1250), authorized as a docs-only
design by [comment 6803222025](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6803222025),
following the [Slice E preflight](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6802507721).
Source line numbers refer to `main` at `2c9bb7c4d54f532521f680590dfb1bee2a310dc4`.

Independent [iteration-3 review](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6810212238)
returned PASS WITH NON-BLOCKING FINDINGS for `af8480a`. The
[final semantic ruling](https://github.com/m0smith/genia-2026/issues/1249#issuecomment-6811083960)
approves the selections in §12; this reconciliation records those selections and
the allocation-wording follow-up, not a new algorithm or implemented behavior.
[E1 TEST authorization](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6811094929)
is bounded to private representation/use/rendering/capture RED. Lineage execution,
reservations and publication remain E2, including their host-local test inventory.

Governing sources: the maintainer-approved
[Model B contract](pre-r29-default-open-and-immutable-binding-contract-DRAFT.md)
(§§3, 4.1–4.3, 6.1), the [portable design](pre-r29-default-open-and-immutable-binding-design.md)
(§§6.2, 7–9), the Q-C1 ruling on
[#1249](https://github.com/m0smith/genia-2026/issues/1249#issuecomment-6803212555),
and the accepted [D2 linking design](pre-r29-model-b-d2-linking-design.md).

This design authorizes no RED test, production code, capability, C++ change or R29 work.

**Iteration 2** answers the independent review
[FAIL — DESIGN CORRECTIONS REQUIRED](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6808189269)
of iteration 1 (`426819a2735c76d8a6f7ba282a89b174a77bd8f7`).

| Finding | Correction | Where |
|---|---|---|
| F1 thread-only admission | Admission needs an open transaction window **and** an unbroken synchronous lineage; host execution boundaries cut the lineage | §6 |
| F2 commit not atomic | One linearization point; nothing visible is written before it; faults after it roll forward | §4.1–4.4 |
| F3 closedness and raw records | Sealed callable, guarded clause records, clause append rejected by value, consumer audit | §3.1–3.2, §7.3 |
| F4 `@test` versus the `test` metadata key | Names and keys separated; Alternative A subsequently approved | §5 |
| F5 declaration result and oracle | Exact output and full inventory list | §10.4 |
| F6 capability | Independent `closed_functions` capability subsequently approved; no host claim yet | §9 |
| F7 truth synchronization | Lands with E2, not after it | §11 |

**Iteration 3** answers the independent re-review
[FAIL — DESIGN CORRECTIONS REQUIRED](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6809101867)
of iteration 2 (`510d80ef3a4ae175aaee733f7a96d41874b592d7`). It changes only the
three concurrency points below. The F3–F7 resolutions are unchanged.

| Finding | Correction | Where |
|---|---|---|
| N1 immutable-name set staged outside the lock | The declaring scope's set is computed from its current value under the binding lock, before the linearization point; the self frame's set is fixed at construction | §4.1, §4.6 |
| N2 cleanup not idempotent | The count is replaced by a set of open transactions; cleanup is four ownership-conditional steps that can be repeated | §4.1, §4.6, §6.6 |
| N3 transaction cleared under a reader | The descriptor is assigned once and never cleared; the admission test reads only data that cannot change during the check | §3.1, §4.6, §6.2 |

## 1. Scope lock

**Includes (Python reference host):** one closed callable and one immutable defining
name per maximal consecutive same-name `=:` run; whole-group validation before any
annotation runs; a provisional callable usable only by the declaration's own
synchronous annotation calls; ordered annotation evaluation with one atomic
publication; the initializing, committed and failed states; failed values that can
be passed around but not used; error precedence; REPL submission boundaries;
exclusion from D2b linking.

**Excludes:** new syntax or `@closed`; changes to accepted D2b linking or R20
dispatch; a new Core IR node or version; a second dispatcher; rollback or
cancellation of external effects; server discovery of closed functions; C++
implementation or parity; R29.

**Approved semantic decisions and their historical alternatives** are in §12.
E1 RED does not authorize implementation or E2 RED.

## 2. Verified starting point

| Fact | Evidence |
|---|---|
| A closed run parses to one `ClosedFuncDef` and lowers to one `IrClosedFuncDef` whose `declarations` are `IrFuncDef` or `IrPatternFuncDef`, each with its own annotations | `parser.py:442-527`, `lowering.py:249-250`, `ir.py:336`; probe |
| Comments, blank lines and `;` do not end a run; another statement does | probe of 11 source variants |
| `=` and `=:` clauses of one name side by side are a parse error | `parser.py:520-521` |
| A closed form inside a block or lambda, a dotted name, or `->` is a parse error | probe |
| Evaluation rejects every closed group | `evaluator.py:1407-1414` |
| An ordinary declaration publishes its clause before its annotations run and returns the clause record | `evaluator.py:1659-1712` |
| `eval_annotations` evaluates in order, validates each value at once, returns a private map; `@meta` accepts any map | `evaluator.py:692-757` |
| Command mode prints a non-nil final value with `format_debug`, which uses `repr` for a function | `interpreter.py:337-341, 668-675`; `utf8.py:151`; probe: `-c 'f(x) = x'` prints `<function f/1>` |
| The shared `eval` runner executes a case through command mode (`-c`) | `hosts/python/exec_eval.py:25` |
| Native-test discovery selects on the binding-metadata key `test`, not on the annotation name | `test_cli.py:175-209`; probe: an ordinary function with `@meta({test: "…"})`, an alias with `@test("…")` and an alias with `@meta({test: "…"})` are all discovered and run (3 PASS) |
| `send_annotated` selects on the metadata key `http_annotation` of the function value and does not revalidate it | `http_annotation_binding.py:67-79` |
| `define_function` appends to an existing group when its `owner` equals the declaring module and name | `environment.py:704-715` |
| An annotated alias writes the merged map back to the group itself | `environment.py:750-752` |
| `serve_http` dispatches each request to its handler on the thread that called `serve_http` | `builtins.py:5498-5502, 5544-5548` (a `handle_request` loop in the calling thread) |
| Process and cell handlers run on their own threads | `values.py:609-648, 773-794` |
| There is no construct that catches a runtime error inside one program | no `try`-like builtin or prelude function |

Within one file or command a failed declaration ends the program. A failed callable
can therefore be used only later in a REPL session, or by another execution that
already holds it.

## 3. Representation (E1)

### 3.1 The closed callable

A closed callable is a new subclass `GeniaClosedFunction(GeniaFunctionGroup)` in
`callable.py`. Dispatch is the inherited stratum and first-match logic, so recursion,
tail calls, Outcome awareness and pattern/guard headers are the ordinary ones. No
second dispatcher exists.

Private fields: `_state` (`building`, `initializing`, `committed`, `failed`) and
`_txn` (its publication transaction descriptor, §6.1). `_txn` is assigned exactly
once, while the callable is `building` and unreachable, and is **never cleared or
replaced**. `_state` is the only field that changes after the callable can be
reached.

The callable is **sealed**:
- Only the private whole-group builder adds records, and only while the state is
  `building`. `add_clause` on a sealed closed callable raises
  `closed-function-not-extensible`.
- Its metadata is written exactly once, by the publication protocol (§4.1).
  `merge_metadata` on a closed callable raises, and the two writers that update a
  group through a binding leave a closed callable untouched (§7.3).

State changes are single stores, `building → initializing → committed | failed`.
The two stores to a terminal state are made under the binding lock and only when the
current state is `initializing`. `committed` and `failed` are therefore final.

| Alternative | Verdict |
|---|---|
| A state flag on `GeniaFunctionGroup` | Rejected. Every ordinary call would pay for a state check, and ordinary rendering would change. |
| A class unrelated to `GeniaFunctionGroup` | Rejected. `GeniaFunctionGroup` is referenced on 50 lines in 12 source files, including at least 21 `isinstance` checks that handle dispatch, awareness and reflection. A second class means a second dispatcher. |
| **Subclass** | Chosen. Ordinary groups are untouched. The subclass is not safe merely by passing `isinstance`; §7.2 and §7.3 list every site that needs a check. |

Class-name comparisons at `values.py:84` and `equality.py:128` fall through to their
`callable(value)` branch for the subclass: type name `function`, equality by identity.

### 3.2 Guarded clause records

Clause records of a closed callable are instances of a small subclass of
`GeniaFunction` that holds a reference to its closed callable. Its `__call__` runs
that callable's use check (§7.2) before anything else.

Reason: several host consumers take a record out of a group and call it later
(§7.3). A record that carries its callable keeps the state rule attached wherever
the record goes, so safety does not depend on every present and future consumer
remembering to check. Inside the trampoline a record is reached only through a
`TailCall` produced by an entry point that has already checked.

No evaluator or builtin path returns a clause record of a closed callable as a value.

### 3.3 Self frame

Each closed callable owns one private scope, the **self frame**:
`Env(parent=declaring scope)` that holds only the defining name. Its immutable-name
set contains that name from construction, while the frame is still private, and the
publication protocols never store to that set again. Every clause record uses the
self frame as its closure, and annotations are evaluated in it.

An **unshadowed** reference to the function's own name inside a clause body or an
annotation therefore means this exact callable, never a later declaration that
reuses the name (contract §4.2).

The self frame is a parent scope. It is consulted only after the scopes below it:
- A parameter or pattern binder with the function's own name, as in `f(f) =: f`,
  binds in the clause frame and shadows the self frame. It keeps ordinary parameter
  lookup and assignability.
- A body assignment to the function's name with no local binding of that name
  reaches the self frame and is rejected with the existing immutable-binding
  diagnostic. This is the nearest-binding rule of contract §3; it does not create a
  silent shadow.
- Assignments to any other name pass through the self frame to the declaring scope
  as before, because the self frame holds no other name.

While the callable is `initializing`, the self frame holds the name as a guarded
slot, not as an ordinary binding (§6.6). At a terminal state the slot becomes an
ordinary immutable binding to the same callable. After a failed publication the self
frame still names the failed callable, so a lambda that a clause body created and
that escaped reaches the old failed callable even after the name is reused.

The self frame inherits `module_identity()` and `unit_scope()`. Debugger and
inspection views gain one scope level; E1 pins what they show.

## 4. Lifecycle transaction (E2)

Evaluating one `IrClosedFuncDef` runs these steps on one thread. T0–T3 evaluate no
user code. Source and direct Core IR both enter at T0.

| Step | Action | Failure |
|---|---|---|
| T0 | `assert_portable_core_ir([node])` (existing) | existing `ValueError` |
| T1 | Name check in the declaring scope: not bound, not held by another transaction, not runtime-owned (`_check_declaration` rules, `environment.py:420-441`) | existing `ImmutableBindingError` texts |
| T2 | Annotation permission scan (§5.1) over every annotation name of every clause, in source order | `closed-function-annotation-not-permitted` |
| T3 | Build the callable, its records, its transaction descriptor and its self frame privately; add records in source order | existing duplicate-clause and conflicting-documentation errors |
| T4 | **Provisional publication** under the binding lock, in this order: P1 repeat T1; P2 add the transaction to the open-transaction set (§6.6); P3 set `initializing`; P4 insert the declaring-scope slot; P5 insert the self-frame slot | as T1 |
| T5 | Open the admission window (§6.2); evaluate annotations in group order in the self frame, folding each clause's map into one private map with `_merge_metadata_maps`; close the window in a `finally` | the annotation's own error |
| T6 | **Publish** (§4.1) | — |
| T7 | **Fail** (§4.2), on any exception leaving T4, T5 or the pre-commit part of T6, including `BaseException`; then re-raise it unchanged | — |

The whole group is validated before the first annotation runs, so an annotation on
clause 1 does not run when clause 3 is a duplicate. During T5 the callable already
has all of its clauses, so an annotation on clause 1 may call the function and reach
clause 2.

The state becomes `initializing` (P3) before any slot exists (P4, P5), so a reader
that finds a slot never sees a `building` callable. The transaction joins the open
set (P2) before any slot exists, which §4.6 relies on.

The binding lock (`_BINDING_LOCK`, `environment.py:37`) is held only inside T4, T6
and T7. It is never held while an annotation or a function body runs.

### 4.1 Publication protocol (T6)

**Before the lock.** The only value prepared outside the lock is the final metadata
map, which T5 already folded and which belongs to this transaction alone. Nothing
that is derived from shared scope data is computed outside the lock.

**Under one hold of the binding lock:**

| Step | Action | Visible to others? |
|---|---|---|
| C1 | Revalidate: the declaring scope's slot for the name still belongs to this transaction and the name is not bound | no |
| C2 | Store the final metadata map on the callable | no: every reader of a closed callable's metadata goes through the use check, which still sees `initializing` |
| C2b | Compute the declaring scope's new immutable-name set as **its current set plus the name**, into a local value | no |
| **C3** | **If the state is `initializing`, set `_state = committed`** — the linearization point | **yes, all at once** |
| C4 | Declaring scope: binding metadata, then the set computed at C2b, then the binding itself | already implied by C3 (see below) |
| C5 | Self frame: binding metadata, then the binding itself | same |
| C6 | Run the close routine K1–K4 | no change in what readers see |

**Close routine**, used by publication, failure and an aborted T4:

| Step | Action |
|---|---|
| K1 | Remove the declaring-scope slot for the name **if it belongs to this transaction** |
| K2 | Remove the self-frame slot for the name if it belongs to this transaction |
| K3 | Discard this transaction from the open-transaction set (no effect if absent) |
| K4 | Mark the transaction descriptor `closed` |

Every K step is a conditional store that does nothing when its work is already done,
and none touches anything that another transaction owns. The routine runs as "repeat
K1–K4 until the descriptor is `closed`". Progress needs no separate record: each
step's own condition is the record, and K4 is the single completion mark.

**Why C3 alone is the linearization point.** While a slot exists, every lookup of the
name and of its metadata, in the declaring scope or the self frame, is answered from
the slot (§6.6) and decided by **one read** of the callable's state. Every use of an
escaped reference is decided by the same single read (§7.2). The data a reader needs
after seeing `committed` (records, metadata) was stored before C3 and never changes.
So before C3 every observer sees an unpublished function, and from C3 on every
observer sees a fully published one. C4–C6 only move the answer from the slot into
the ordinary tables; they change no observable result.

C2b completes the immutable-set allocation before C3. Inserting metadata or a new
binding into a Python dictionary at C4/C5 can still allocate or resize storage;
those post-C3 faults follow roll-forward, not failure or rollback. The lock
is held continuously from C2b through C4, so no other writer can change the
declaring scope's set between the computation and the store (§4.6, N1).

A reader that started before T4 and skipped the slot path (§6.6, fast path) reads the
ordinary tables directly. It finds the binding absent until C4 writes it, and C4
writes the binding last, after its metadata. Both outcomes are consistent with a
lookup that took effect either before the declaration or after C3.

### 4.2 Failure protocol (T7)

The admission window is already closed (T5's `finally`). Under one hold of the
binding lock:

| Step | Action |
|---|---|
| F1 | If the state is `initializing`: **`_state = failed`** — the linearization point of failure |
| F2 | Self frame: bind the name to the failed callable (the name is already in that frame's immutable-name set) |
| F3 | Run the close routine K1–K4 |

Nothing is written to the declaring scope, its metadata or its immutable-name set.
The name is free for reuse. The private metadata map is dropped; it was never stored
on the callable or in any scope.

### 4.3 What each observer sees

| Observation | Before C3 / F1 | After C3 | After F1 |
|---|---|---|---|
| Call through an escaped reference, not admitted | `closed-function-not-yet-published` | ordinary call | `closed-function-failed-publication` |
| `doc`/`meta`/`help` through an escaped reference | `closed-function-not-yet-published` | final metadata | `closed-function-failed-publication` |
| Name lookup in the declaring scope, not admitted | as if not declared | the callable | as if not declared |
| Name lookup reaching the self frame, not admitted | `closed-function-not-yet-published` | the callable | the failed callable (a value; using it is rejected) |
| A write to the name in the declaring scope | rejected as immutable | rejected as immutable | allowed |

Assignment, passing, storing, comparing and rendering the value are allowed in every
column.

### 4.4 Faults inside the protocols

A fault is any exception raised by a protocol step itself, for example an
interrupt or an allocation failure. It is distinct from an annotation error.

| Fault at | Result |
|---|---|
| P1 or P2 (state still `building`) | Close routine. The callable was never reachable; it is discarded. |
| P3, P4 or P5 | T7. The state may already be `initializing`; F1 is conditional and the close routine removes whichever slots exist. |
| T5, or closing the window | T7. |
| C1, C2 or C2b | T7. The state is still `initializing`; nothing visible was written. An allocation failure at C2b is this case. |
| C3 | The handler reads the state. `committed`: roll forward. Otherwise: T7. |
| C4 or C5 | **Roll forward.** A `finally` inside the lock hold repeats C4 and C5, including dictionary insertions which may allocate despite the values already existing, then runs the close routine. The fault is then re-raised from the declaration statement. The function is published. |
| Between or after any of K1–K4 | The close routine is run again from K1. Steps already done do nothing (§4.6, N2). |
| F1 | The handler reads the state. Not yet `failed`: repeat F1. |
| F2 | Repeat F2, then the close routine. |

Consequences:
- **Committed never becomes failed.** F1 is conditional on `initializing`, and
  after C3 the only path is forward.
- **Every exit leaves a terminal state (or a discarded, never-reachable callable), no
  slot of this transaction, and this transaction absent from the open set.**
- **What is rolled back:** only the transaction's own private bookkeeping (its slots
  and its membership of the open set). Nothing visible is written before C3, so
  there is nothing visible to undo.
- **What is never rolled back:** effects of annotations (contract §4.2). They may
  already have been observed by other executions or outside the program, and the
  contract defines no cancellation.

Fault injection covers one fault at each step. Several simultaneous faults are not
covered and that limit is stated in the tests.

### 4.5 Metadata channels

Closed callables use the ordinary three observations: binding annotations (the
committed map), inline documentation (the group docstring, merged at T3), and help
(the existing `_describe_function_group`). Until C2 the private map is a local value
of the transaction.

### 4.6 Concurrency arguments (N1–N3)

Each argument names its invariant, replays the failure found in iteration 2, and
gives the corrected interleaving. Thread **O** owns closed function `f`.

#### N1 — immutable-name membership

**Ownership.** `Env._immutable` (`environment.py:129`). Its only existing writer is
`commit_immutable_declaration` (`environment.py:473`), which stores
`self._immutable | {name}` inside one hold of the binding lock. Step C2b and the
store in C4 are the only new writers.

**Invariant IM.** For every scope: the immutable-name set only grows, and every
store to it is "the current set plus one name", read and stored within one
uninterrupted hold of the binding lock.

**Old failure (iteration 2).**

| # | Thread O (`f`) | Thread W (`g =: 1`, same scope) | Set |
|---|---|---|---|
| 1 | stages `S ∪ {f}` outside the lock | | `S` |
| 2 | | lock; store `S ∪ {g}`; bind `g`; unlock | `S ∪ {g}` |
| 3 | lock; C1 passes; C4 stores the staged `S ∪ {f}` | | `S ∪ {f}` — **`g` lost** |

**Corrected.**

| # | Thread O (`f`) | Thread W (`g =: 1`) | Set |
|---|---|---|---|
| 1 | T5 ends; only the private metadata map is prepared | | `S` |
| 2 | | lock; store `S ∪ {g}`; bind `g`; unlock | `S ∪ {g}` |
| 3 | lock; C1; C2 | | `S ∪ {g}` |
| 4 | C2b reads the current set: local `N = S ∪ {g, f}` | any writer waits for the lock | `S ∪ {g}` |
| 5 | C3; C4 stores `N`; C5; C6; unlock | | `S ∪ {g, f}` |

If W runs after step 5 instead, it reads `S ∪ {f}` and stores `S ∪ {f, g}`. If W
arrives during steps 3–5 it waits for the lock and then does the same. In every
order both names stay in the set, so committing `f` cannot make `g` writable.

**Two closed publications** `f` and `h` in one scope are the same argument: each
runs C2b through C4 inside its own lock hold, so the second reads the set the first
stored.

**Allocation failure.** C2b is the only allocation that depends on shared data. It
runs before C3. If it fails, the state is still `initializing`, nothing visible was
written, and T7 runs: `f` is failed and unbound, and the set is untouched. No step
after C3 allocates an immutable set; dictionary insertion may allocate and uses
the post-C3 roll-forward protocol.

**Self frame.** Its set is built at T3, while the frame is private, and already
contains the name. C5 and F2 do not store to it. Any later immutable declaration
made in that frame goes through the existing writer and obeys IM.

**Effect on F2.** The linearization argument is unchanged. The claim "nothing derived
from shared data is computed outside the lock" replaces the staging paragraph.

#### N2 — cleanup accounting

**Ownership.** The per-scope slot tables and one module-level set of open
transactions in `environment.py`, all written only under the binding lock; the
`closed` mark on the descriptor.

**Invariant R1.** If any slot owned by transaction X exists, X is in the open set.

**Invariant R2.** Only X's own close routine removes X's slots or removes X from the
set, and within one pass it removes the slots (K1, K2) before the set entry (K3).

*R1 holds* because P2 adds X before P4 and P5 insert its slots, and because K3 runs
after K1 and K2 in every pass. On a repeated pass K1 and K2 run again first; they do
nothing only when X's slots are already gone. Discarding X never removes another
transaction. So **an empty set implies that no transaction has a live slot**, and
the fast path cannot be taken while another transaction still owns slots.

**Old failure (iteration 2).** A and B are open; the count is 4.

| # | Transaction A cleanup | Count | B's slots |
|---|---|---|---|
| 1 | removes its two slots; count 4 → 2 | 2 | live |
| 2 | one interrupt before cleanup is recognized as complete | 2 | live |
| 3 | the retry decrements again; 2 → 0 | **0** | live — **the fast path now skips them** |

**Corrected.** The set is `{A, B}`.

| # | Transaction A close routine | Open set | B's slots |
|---|---|---|---|
| 1 | K1, K2: remove A's own slots | `{A, B}` | live |
| 2 | K3: discard A | `{B}` | live |
| 3 | one interrupt before K4 | `{B}` | live |
| 4 | repeat: K1, K2 find no slot of A; K3 finds A absent; K4 marks `closed` | `{B}` | live |

The same holds for an interrupt after K1 (the repeat removes the second slot) or
after K2 (the repeat discards A). For an aborted T4 the routine removes whichever of
A's slots exist and discards A if it was added. In every case the set is non-empty
exactly while B is open, so B's declaring thread still finds B's slot, and a write to
B's name is still rejected.

**Why no general framework.** The whole mechanism is one set, two conditional
removals and one mark. Progress is read from the data itself: "is my slot still
there", "am I still in the set", "am I marked closed".

**Effect on F1 and F2.** Slot visibility, on which admission by name and the
linearization argument depend, now follows from R1 and R2 instead of a balanced
count. The fault rows for C6 and F3 are replaced by the K rows of §4.4.

#### N3 — state and descriptor

**Ownership.** `_state` and `_txn` on `GeniaClosedFunction` (`callable.py`), the
descriptor's `window_open` flag, and the use-check helper (§7.2).

**Invariant D1.** `_txn` is assigned once, at T3, before the callable can be reached
by any other execution, and is never cleared or reassigned. Whenever the state is
`initializing` or terminal, `_txn` is a valid descriptor.

**Invariant D2.** After P3, `_state` changes only by the conditional stores C3 and
F1, each under the binding lock and each only from `initializing`. A terminal state
never changes.

**Invariant D3.** The use check, and every slot lookup, reads `_state` exactly once
and decides from that value. Only when it read `initializing` does it read `_txn`,
and then it applies the two ordered tests of §6.2.

**Old failure (iteration 2).**

| # | Reader R (not the declaring thread) | Thread O |
|---|---|---|
| 1 | reads `_state`: `initializing` | |
| 2 | | commits or fails; **clears `_txn`** |
| 3 | reads `c._txn.window_open` — **dereferences nothing** | |

**Corrected.**

| # | Reader R (not the declaring thread) | Thread O |
|---|---|---|
| 1 | reads `_state` once: `initializing` | |
| 2 | | window already closed; C3 or F1; C4–C6 or F2–F3. `_txn` is untouched |
| 3 | reads `_txn`: the same valid descriptor (D1) | |
| 4 | test 1: is the descriptor on **R's own** stack above a barrier? No | |
| 5 | result: `closed-function-not-yet-published` | |

R's result is correct for the moment of its state read, which is before C3 or F1. A
later call by R reads the terminal state and behaves accordingly. Whether O commits
or fails makes no difference to steps 3–5.

**Why a reader that saw `initializing` can always finish.**
- *R is not in the lineage.* Test 1 reads only R's own thread-local stack, which no
  other thread writes. It is false and stays false. R never reaches test 2.
- *R is in the lineage.* Then R is the declaring thread, running inside T5. O is the
  same thread, so it cannot be in T6 or T7 at the same time: those start only after
  T5 has unwound, which is after R's call has returned. The state and `window_open`
  cannot change during R's check.

So no execution can read `initializing`, be admitted, and run a body after the
function was committed or failed by someone else.

**A slot lookup** follows the same rule. It keeps the slot it fetched in a local
value, reads the callable's state once, and decides. If K1 or K2 removes the slot
from the table meanwhile, the local value is still valid, and the outcome is one of
the two outcomes that §4.1 already shows to be consistent.

**No committed-to-failed transition.** D2: C3 and F1 are both conditional on
`initializing` and both under the lock, so whichever runs first is final, also when
a handler repeats one of them.

**What the descriptor keeps.** Lock-free readers use only its identity and
`window_open`. Fields that only the owner uses under the lock, such as the private
metadata map and the scope references, may be released by the owner after K4.

**No lock during user code.** The use check takes no lock at all. The binding lock is
still held only in T4, T6 and T7.

**Effect on F1 and F2.** The admission rule of §6.1 is unchanged in meaning; its test
order is now fixed and the thread comparison is dropped as redundant. The
linearization argument already relied on one read of the state; D1 removes the one
extra mutable field it had overlooked.

## 5. Annotations, metadata keys and discovery

### 5.1 Annotation names (Q-C1, approved) and where they are checked

| Annotation **name** on a closed clause | Result |
|---|---|
| `@doc`, `@meta`, `@since`, `@deprecated`, `@category` | Permitted (ruled). Existing validation applies at T5. |
| `@route`, `@get`, `@post`, `@server`, `@cors` | Rejected at T2 (ruled). |
| `@test` | Permitted by the final Q-C1b ruling; existing validation at T5 and guarded native discovery (§5.2). |
| Any other unsupported name | Rejected at T2 before any annotation effects, as approved by Q-C1b. Ordinary unknown-name timing stays unchanged (`evaluator.py:714-757`). |

T2 scans the annotation names of the whole group before any annotation expression is
evaluated. Names are static in Core IR (`IrAnnotation.name`), so the scan runs no
user code. The final ruling approves this pre-scan. It does not change the order of
contract §4.2: that order governs evaluation of permitted annotations and begins
after structural validation, of which "permitted metadata" is a listed part (§4.1).

The scan runs at evaluation, so a direct Core IR caller gets the same rejection as
source, and statements before the declaration still run.

**Names are not keys.** The ruling lists annotation names. It does not restrict the
keys of a map given to `@meta`, and this design bans no key. `@meta({test: "x"})`,
`@meta({route: …})` and `@meta({http_annotation: …})` are valid `@meta` uses on a
closed declaration. What a *consumer* of such a key does with a closed callable is a
separate question, answered in §5.2 and §5.3.

**Server discovery is unchanged.** The three walkers still reject an entry program
that contains any closed declaration (`server_route_binding.py:211-214`,
`server_config_binding.py:218-221`, `server_cors_binding.py:182-185`). They select by
annotation name in Core IR, so a `route` key inside `@meta` is not discovered.

### 5.2 Native-test discovery — Alternative A APPROVED (Q-C1b)

Iteration 1 recommended excluding `@test` and concluded that a closed function would
then never be discovered. The review showed that conclusion is false, and a probe
confirms it for ordinary functions today (§2): discovery reads the binding-metadata
key `test`, which can come from three sources.

| Source of the `test` key | Example |
|---|---|
| The `@test` annotation on the declaration | `@test("adds")` above `t() =: …` |
| A `test` key in `@meta` on the declaration | `@meta({test: "adds"})` above `t() =: …` |
| An annotated alias binding | `@test("adds")` above `u = t` |

Discovery then requires a function group with exactly arity 0 and one plain record,
and runs that record (`test_cli.py:184-205`, `test_kernel.py:106-111`).

**Alternative A — APPROVED: closed functions are discoverable tests.**
`@test` joins the permitted names. Discovery treats a committed closed callable like
an ordinary function with the same binding metadata, from any of the three sources,
with the existing description, arity and unique-name rules. Discovery runs the
callable's use check and schedules the **callable**, not a bare record, so the state
rules hold at run time.

**Historical Alternative B — NOT SELECTED: closed functions are never discovered.**
`@test` is rejected at T2. Discovery gets a type-aware rule: a binding whose value is
a closed callable and whose metadata has a `test` key produces the discovery error
`@test cannot select a closed function`. `@meta` keys stay unrestricted.

| | A | B |
|---|---|---|
| Fit with contract §4.1 ("preserve existing ordinary-compatible … annotations") | Follows it | An exception that must be justified |
| New rules | None in discovery; one more permitted name | One T2 rejection, one discovery rule, one new error text |
| The three sources behave alike | Yes | Yes, but only through the type-aware rule |
| Alias of a closed function with `@test` | A test, as for an ordinary alias | A discovery error on a binding that is not itself a closed declaration |
| Extends the approved five-name list | Yes, by `@test` | No |
| Evidence | Shared `cli` test-mode cases | Shared `cli` test-mode cases |

**Approved selection: Alternative A.** The final maintainer ruling explicitly
permits `@test` and discovery from all three sources. The alternatives above are
retained as design history; Alternative B is not an implementation option.

**Approved contract wording, Alternative A:**
> `@test` is permitted on a closed declaration under the validation that applies to
> ordinary functions. Native-test discovery treats a committed closed callable as it
> treats an ordinary function with the same binding metadata, whether that metadata
> came from `@test`, from a `test` key in `@meta`, or from an annotated alias
> binding. Discovery and execution go through the callable, so §4.2 applies; a
> callable that is not committed is never run as a test.

**Historical proposed wording, Alternative B (not selected):**
> `@test` is rejected on a closed declaration like the annotations rejected above.
> Native-test discovery never selects a closed callable: a binding whose value is a
> closed callable and whose metadata has a `test` key is reported as a discovery
> error, whether the key came from `@meta` or from an alias binding. The keys of an
> `@meta` map are not restricted.

Contract §4.3 now records the final ruling; this does not activate closed evaluation.

### 5.3 The `http_annotation` key — exclusion APPROVED (Q-C1b)

`send_annotated(fn)` reads the key `http_annotation` from the function value's
metadata. `@get` and `@post` are rejected by name, but `@meta({http_annotation: …})`
would put the same key on a closed callable.

- **Historical alternative, not selected:** `send_annotated` treats a committed closed callable like
  an ordinary function carrying that key.
- **Approved exclusion:** `send_annotated` rejects a closed callable with its existing
  `TypeError` text, whatever its metadata.

**Approved selection: excluded.** The final Q-C1b ruling explicitly decides the
consumer exclusion as well as annotation-name permission. The use check runs first;
no `@meta` key is banned.

## 6. Admission and provisional names

### 6.1 Rule

> While a closed callable is `initializing`, an invocation is **admitted** only if
> (1) its publication transaction's admission window is open, and (2) the invocation
> runs inside the synchronous call chain that the declaration's own annotation
> evaluation started, with no host execution boundary in between.
> Every other invocation, and every callable-specific introspection, is rejected
> with `closed-function-not-yet-published`.

Running on the declaring thread is necessary and not sufficient.

The **publication transaction** is described by a private host object, the
descriptor, created at T3. It is never a Genia value, so Genia code cannot obtain,
copy or forge it. It records the callable, the declaring scope, the self frame,
whether its window is open and whether it is closed. The callable's `_txn` field is
the only link from a value to its descriptor, and that link never changes (§3.1).
The descriptor does not need to record a thread: only the declaring thread ever
pushes it on a lineage stack, so being on a thread's stack already identifies that
thread.

### 6.2 Window and lineage

Each thread has a private **lineage stack**. It is thread-local host state and is
not stored in a `contextvars` variable.

| Event | Stack operation |
|---|---|
| T5 begins | set `window_open`; push the transaction |
| T5 ends, normally or by exception (`finally`) | pop the transaction; clear `window_open` |
| A host execution boundary begins running a callable (§6.3) | push a **barrier** |
| That boundary's callable returns or raises (`finally`) | pop the barrier |

An invocation of callable `c` whose state was read as `initializing` is admitted
when both of these hold, tested **in this order**:
1. `c._txn` is on the current thread's lineage stack **above the most recent
   barrier**;
2. `c._txn.window_open` is true.

Test 1 reads only the current thread's own stack. Test 2 is reached only by a thread
that has the descriptor on its stack, which is the declaring thread, and that is the
only thread that ever writes `window_open`. Neither value can be changed by another
thread while the check runs (§4.6, N3).

How the required properties follow:
- **Start and end of the window.** Authority exists only between the push at T5's
  start and the pop in its `finally`. Between T4 and T5, and between the end of T5
  and C3 or F1, nobody is admitted. No user code runs on the declaring thread in
  those gaps.
- **Entering and leaving the call chain.** The chain starts when the evaluator begins
  an annotation expression inside the window and ends when that expression returns
  or unwinds. Everything called in between is in the chain.
- **Recursion.** A recursive call is made inside the chain, so the transaction is
  still on the stack. Nothing is passed along.
- **Synchronous host bridges.** A builtin that calls its callback before returning
  neither pushes nor pops, so authority is unchanged. No builtin needs editing.
- **Unrelated callbacks on the same thread.** They are started by a host execution
  boundary, which pushes a barrier that hides every transaction below it.
- **Copied contexts.** The stack is not in a context, so copying a context copies no
  authority. Code run from a copied context is admitted exactly when the same code
  called directly would be.
- **New threads, tasks and processes.** A new thread starts with an empty stack. A
  task run by a scheduler starts behind a barrier. An operating-system process
  shares no values.
- **Nesting.** Several transactions can be on one stack. Each callable is checked
  against its own transaction only. A barrier hides all of them.
- **Revocation.** The pop in T5's `finally` runs before T6 or T7 starts.

A lazy value created during T5 and forced later is not special: by then the callable
is committed or failed.

### 6.3 Bridges and boundaries

A **bridge** runs a callable because the current call asked for it and before that
call returns: a callback argument, forcing a lazy value, pulling a Flow the caller
consumes, a lifecycle scope the caller runs, loading a module the caller imports.
A bridge needs no code.

A **boundary** runs a callable on behalf of a requester other than the current
synchronous call. It must push a barrier. The Python host has these today:

| Boundary | Location | Same thread as its caller? |
|---|---|---|
| `serve_http` request dispatch | `builtins.py:5499-5502` | **yes** |
| Native-test body execution | `test_kernel.py:106-111` | yes |
| Entry `main` dispatch | `interpreter.py:513-529` | yes |
| Process message handler | `values.py:794` | no |
| Cell update | `values.py:648` | no |

The last two are already excluded by their empty stacks; they push a barrier so the
rule is uniform. Any future task scheduler, timer, or debugger-initiated evaluation
is a boundary.

**Host-boundary invariant.** Every host site that runs a Genia callable is either a
bridge or a boundary, and every boundary pushes a barrier. A missed boundary would
admit a call it should refuse, so E1 includes an inventory test that fails when a
handler-dispatch or thread-start site exists without a classification (§10.1).

### 6.4 Examples

**Admitted: nested recursion.**
```genia
depth(0) =: 0
@meta({probe: depth(2)})
depth(n) =: 1 + depth(n - 1)
```
The annotation calls `depth(2)`, which calls `depth(1)`, which calls `depth(0)`. All
three run inside the chain the annotation started, on the declaring thread, with the
window open and no barrier. All are admitted. The same holds when the annotation
calls a module-scope helper that calls `depth` by name (§6.6).

**Rejected on the same thread: a request handler.**
An annotation, directly or through a helper, stores the provisional callable in a
Ref and calls `serve_http(handler)`. `handler` reads the Ref and calls the value
when an HTTP request arrives. The handler runs on the declaring thread while the
window is open, and iteration 1 would have admitted it. Here the request dispatch is
a boundary: the barrier hides the transaction, and the call is rejected with
`closed-function-not-yet-published`. The request was not started by the annotation's
call chain; it only happened to be served during it.

**Rejected: before and after the window.** A reference that reached another thread is
called between T4 and T5, or after T5 returned and before C3. In both gaps the
descriptor is on no thread's stack and `window_open` is false.

**Rejected: a copied context.** A context copied inside the window is run later, or
on another thread. Later, the window is closed. On another thread, the stack is
empty.

**Nested transactions.** An annotation of closed `a` causes a module to load, and the
module declares closed `b`. While `b`'s annotations run, the stack holds `a`'s and
`b`'s transactions. A call to `a` and a call to `b` are each admitted against their
own transaction. A boundary inside `b`'s annotation hides both. When `b`'s window
closes, only `a`'s authority remains.

### 6.5 Alternatives

| Alternative | Verdict |
|---|---|
| Declaring thread only (iteration 1) | Rejected. It admits the request handler above and both gaps around T5. |
| A `contextvars` token | Rejected. A context can be copied into a task that a same-thread scheduler runs inside the window. |
| A token passed through evaluator calls | Rejected. Host bridges call `fn(*args)` and would drop it, refusing legitimate calls. |
| Bridges opt in, everything else denied | Rejected. Every builtin that takes a callback would need marking, and a missed mark would refuse legitimate calls. |
| **Window plus thread-local lineage with barriers at boundaries** | Chosen. |

Portable statement: admission requires the declaration's transaction and an unbroken
synchronous lineage from its annotation evaluation. How a host represents lineage is
its own matter; a thread-local stack is the Python realization only.

### 6.6 Guarded name slots

A **slot** is an entry in a per-scope private table, `name → transaction`, with a
policy. T4 inserts two for the defining name; C6 or F3 removes them.

| Scope | Policy for a lookup that is not admitted |
|---|---|
| Declaring scope | **Fall through**: continue as if the name were not declared here. This serves the module-scope helper an annotation calls, and leaves all other code where it was before the declaration. |
| Self frame | **Strict**: raise `closed-function-not-yet-published`. Code that reaches the self frame is lexically inside the declaration or is a closure such code created. The name can only mean this function, so falling through to an outer binding of the same name would be wrong. |

"Admitted" is the §6.2 test, not thread identity. An escaped closure therefore cannot
obtain the provisional callable by name, through either scope.

**Lookup.** `Env.get` and `get_metadata` (`environment.py:476-487, 717-722`) consult
the slot at a scope's own level before that scope's ordinary table and before moving
to the parent. One read of the callable's state decides:

| State read | Declaring scope | Self frame |
|---|---|---|
| `initializing`, admitted | the callable (metadata: not yet published) | the callable |
| `initializing`, not admitted | fall through | `closed-function-not-yet-published` |
| `committed` | the callable and its final metadata | the callable and its final metadata |
| `failed` | fall through | the callable |

Lookup at the declaring scope's own level comes before its parent, so a module that
declares a closed function whose name also exists in the runtime scope resolves the
provisional callable for an admitted helper.

**Writes.** While a slot exists, its scope treats the name as its own immutable
binding for every writer on every thread. Each of these must honor it:
`check_assign_target` and `find_assign_target` (so the rejection precedes evaluation
of the right-hand side and a write is never redirected to an outer binding of the
same name), `_write_binding`, `set`, `assign`, `define_function`, `publish_view`,
`_check_declaration`, `merge_binding_metadata`, import-alias and `use` binding, and
autoload publication. Rejections use the existing immutable diagnostics. Only the
owning transaction's C4 and C5 write the name.

Every writer makes its final decision **under the binding lock**, where it sees the
slot table directly; it never relies on the lock-free "set is empty" test. The
existing lock-free pre-check that rejects an assignment before its right-hand side
runs (`check_assign_target`, `environment.py:392-410`) only affects timing: if it
ran just before P2 and saw nothing, the write itself is still rejected under the
lock and is never redirected.

**Fast path.** A process-wide **set of open transactions** is changed only under the
binding lock. A transaction is added at P2, before its first slot is inserted, and
discarded at K3, after its last slot is removed. Adding and discarding are
idempotent, and discarding one transaction cannot remove another. When the set is
empty, lookups take the current path unchanged; otherwise they consult slots. There
is no counter to drift (§4.6, N2). The set is an optimization, never a source of
authority: a reader that misses a slot because it read "empty" before P2 is, by
construction, not the declaring thread inside its window.

| Alternative | Verdict |
|---|---|
| Self frame only | Rejected. The module-scope helper case fails; the portable design (§6.2) names it. |
| Bind the name in the declaring scope at T4 | Rejected. Every execution could resolve it, and failure would have to delete a binding. |
| An ordinary binding in the self frame (iteration 1) | Rejected. An escaped closure resolved the provisional callable by name with no check. |
| **Guarded slots in both scopes** | Chosen. |

## 7. Use rules and error precedence (E1)

### 7.1 State table

| State | Invoke, admitted | Invoke, not admitted | `doc`/`meta`/`help`; `extend`/`use` target; `send_annotated`; discovery | Assign, pass, return, store, compare, render |
|---|---|---|---|---|
| initializing | ordinary call | `closed-function-not-yet-published` | `closed-function-not-yet-published` | allowed |
| committed | ordinary call | ordinary call | per that consumer's rules | allowed |
| failed | `closed-function-failed-publication` | same | same | allowed |

Introspection is refused during `initializing` for admitted callers as well. Contract
§4.2 requires this: only invocations are admitted.

### 7.2 Where the use check runs

One helper on the callable performs the check with one read of the state.

| Entry point | Location | Reason |
|---|---|---|
| `invoke_callable`, first statement | `callable.py:1552`, before `:1580` | `None`-argument propagation at 1580-1582 returns before dispatch. The contract requires the state error first. This also precedes the name-based Flow adapters, stratum selection and autoload. |
| `GeniaClosedFunction.__call__` | override | Every host site that calls a value directly: handlers, callbacks, `apply_raw` after its own argument check. The inherited fast path would call a record without `_dispatch_once`. |
| `GeniaClosedFunction._dispatch_once` | override | The trampoline calls it for a group reached through a `TailCall` (`callable.py:625`). |
| Guarded clause record `__call__` | §3.2 | Any consumer that extracted a record. |
| `_help_in_scope`, `_doc_in_scope`, `_meta_in_scope`, `_describe_function_group` | `builtins.py:3467, 3513, 3568, 3251` | After the name or value is resolved, before any metadata is read. |
| `extend` and `use` target resolution | `evaluator.py:1603`, `:1625`, right after `get_export` | Before the completion-witness lookup. |
| `resolve_http_annotation` | `http_annotation_binding.py:67` | Before it reads the value's metadata. |
| Native-test discovery | `test_cli.py:189` | Before it reads the group's shape. |

Arity selection, pattern matching, guards and bodies run after these points. The
Outcome-awareness helpers (`callable.py:1430, 1493`) only read clause structure and
authorize nothing.

**A bridge's own argument checks are not an invocation.** `apply_raw(f, "x")` fails
on its second argument before `f` is invoked (`builtins.py:4321-4325`); that order
stays.

**Storage is not invocation.** `spawn(failed)`, building a lazy Flow stage from a
failed callable, and registering it as a handler all succeed. The rejection happens
when the callback is actually run. A stage that is never pulled, or an empty Flow,
raises nothing.

**Pipelines.** `eval_pipeline` (`evaluator.py:1135-1150`) returns a `none` or `err`
stage value before the next stage is evaluated, so that stage is not invoked and
nothing is rejected (contract §4.2). A stage that is reached goes through
`invoke_callable`; its error is wrapped by the existing pipeline-stage text.

### 7.3 Closedness follows the value

Closedness belongs to the callable, not to a name. It holds when the value is
assigned to another name, stored in a Ref or Cell, exported or re-exported, passed to
a higher-order function, or bound again under its original spelling after a failed
publication.

**No clause is ever appended.** `define_function` (`environment.py:664-715`) checks,
after its existing immutable-name check and before its ownership check, whether the
existing value is a closed callable in any state. If so it raises
`closed-function-not-extensible`. The check does not look at `owner`. This closes
the case the review found: after a failed publication, `f = ref_get(saved)` followed
by an ordinary `f(x, y) = …` passed the ownership check, because the failed
callable's owner still equals the declaring module and name. The sealed `add_clause`
(§3.1) is the second line of defense.

For the committed defining name, the existing immutable-name check still fires first
with its existing text.

**No metadata is written through a binding.** `merge_binding_metadata`
(`environment.py:750-752`) and `define_function` (`:691, :713`) update a group's own
metadata when a binding is annotated. For a closed callable they update only the
binding's metadata. An annotated alias of a closed function has its own binding
metadata and leaves the callable unchanged.

**Consumers that reach inside a group:**

| Consumer | What it takes | Design |
|---|---|---|
| Native-test discovery (`test_cli.py:184-205`) and execution (`test_kernel.py:106-111`) | shape; one record, run later | Per §5.2. Use check at discovery; under Alternative A the callable is scheduled, not the record. |
| `send_annotated` (`http_annotation_binding.py:54-79`, `builtins.py:800`) | metadata, shape; invokes the value | Use check first; then per §5.3. |
| Route handler shape (`server_route_binding.py:262-271`) | shape | Not reachable for closed declarations (§5.1). |
| Entry `main` (`interpreter.py:513-529`) | records for arity 1 and 0, called directly | Per DQ-M. Use check first; the records are guarded. |
| List-traversal fast-path stability test (`evaluator.py:922-940`) | reads records, invokes nothing | No check needed. Closed clauses are not optimized, so it does not apply to them. |
| Help spans (`builtins.py:3228`) | reads spans | Behind help's use check. |
| D1 completion capture (`ordinary_completion.py:139-166`) | records and closures | Closed values are skipped (§8). |
| `invoke_callable` simple-group path | a record, as a `TailCall` | Behind the first-statement check. |

### 7.4 Transport and rendering

Assignment, argument passing, return, storage in a Ref, Cell or collection, closure
capture and equality need no check. Equality stays identity
(`equality.py:125-133`).

Rendering uses overridden `__repr__` and `__str__`, which every display path reaches
(`format_display` and `format_debug` fall back to `str`/`repr`; diagnostics that
embed a value use `repr`). Approved literals (DQ-L):

| State | Rendering |
|---|---|
| initializing, committed | `<closed-function NAME>`, for example `<closed-function f>` |
| failed | `<closed-function failed>` — no name |

No marker shows arity, clauses, metadata or closure content. Inside a list, map,
pair, Outcome, Ref or Cell the marker appears wherever a function value would, and
the existing opaque markers for protected and represented values are unchanged. A
protected value captured by a closed function's closure never appears in any
rendering or diagnostic of that function. Serialization boundaries such as JSON keep
their existing behavior for a function value; they are not callable use and raise no
lifecycle error.

## 8. Interaction with accepted D2b and other consumers

| Consumer | Design |
|---|---|
| D1 completion capture (`prepare_module_completions`, `ordinary_completion.py:139-166`) | Skip every closed value at the top of the loop, whether exported under its own name, an alias or a re-export. No completion witness is created for it. Ordinary originals and re-exports keep their witnesses. |
| `extend`/`use` naming a committed closed export | `completion_for` returns `None`; the existing `open-function-target-not-open`. A target that is not committed gets the state error first. |
| An ordinary clause declared onto a closed callable through any binding | `closed-function-not-extensible` (§7.3). |
| A later clause under the committed defining name | Existing immutable-binding rejections. |
| Entry `main` selection | DQ-M (§12). |
| Server discovery | Unchanged rejection (§5.1). |
| Optimizer | `optimize_program` rewrites only top-level `IrFuncDef` (`optimizer.py:64-70`). Closed clauses are not optimized in Slice E; behavior is the same without that fast path. |
| Name-based Flow adapters and prelude-name awareness | Apply to a closed callable as to an ordinary group of that name, after the use check. |

Combined D+E integration acceptance stays with
[#1251](https://github.com/m0smith/genia-2026/issues/1251). The link-target cases
are part of Slice E because they prove the capture exclusion.

## 9. Portability analysis (`docs/process/run-change.md`)

1. **Observable semantics.** Group boundary; validation before effects; ordered
   annotation effects; self-call during annotation; the state errors and their
   precedence; failed-value transport, equality and rendering; REPL name reuse;
   the declaration's value. Thread and boundary admission are observable only with
   process or server primitives. The thread-local stack is a host detail and is not
   portable semantics.
2. **Core IR and runtime boundary.** `IrClosedFuncDef` already carries the atomic
   group. No new node, field or version. Transaction, slots and lineage are private
   runtime state.
3. **Shared executable conformance.** §10.
4. **Capability applicability — APPROVED (DQ-C), not yet advertised.**
   The independently optional capability is **`closed_functions`**.
   - *Why.* `immutable_bindings` covers `name =: expr`; `default_open_functions`
     covers ordinary default-open clauses and pattern/guard headers. Neither implies
     closed publication. The Python host is the proof: it claims both today and
     rejects every closed declaration. Gating closed cases on those two would make a
     host that correctly implements both fail cases about a feature it never
     claimed.
   - *Boundary.* Evaluation of `IrClosedFuncDef`: group publication, the three
     states, the state errors, failed-value behavior, and the closed-specific
     rejections. Parsing and lowering of closed forms stay under the required
     `parser` and `ast_lowering`.
   - *Applicability.* Every closed case requires `closed_functions`, plus
     `default_open_functions` when it uses a pattern or guard header or ordinary
     clauses, `immutable_bindings` when it uses `name =: expr`, and `repl`, `refs`,
     `cell_primitives`, `process_primitives`, `multi_file_eval`, `open_functions` or
     `doc_help` only where used.
   - *Synchronization at E2, not now:* `spec/manifest.json` (the vocabulary; the
     runner and the parity gate derive theirs from it),
     `hosts/python/protocol_adapter.py` (the Python claim),
     `spec/known_host_gaps.json` (a new issue-backed C++ entry with its removal
     condition, which the parity gate requires for an optional capability a host
     does not support), `docs/host-interop/HOST_CAPABILITY_MATRIX.md`, the
     capability catalog `docs/host-interop/capabilities.md` (a description, not a
     second registry), and the independent literal capability-map size in
     `tests/unit/test_model_b_slice_c_capability_evidence.py:36` (36 today), which
     stays a literal and is updated deliberately. RED follows the Slice C staging
     precedent: the adapter advertises the capability as unsupported until GREEN.
   - *Alternative:* redefine `default_open_functions` to include closed publication.
     Rejected: it changes the meaning of a claim the Python host already makes and
     that existing evidence was collected against.
   - Capability gating is never used to hide a regression in ordinary behavior:
     no existing case gains this requirement except the one transition in §10.4.
5. **Host claims.** Python reference host only, and only at E2 GREEN. The bounded
   C++ host would not declare `closed_functions`, so every closed case reports
   unsupported, never pass. [genia-cpp#50](https://github.com/m0smith/genia-cpp/issues/50)
   (parser and lowering) remains open. No parity claim.
6. **Gap recording.** At E2: the `closed_functions` entry above, owner #1250,
   `@m0smith` until reassigned. The transitioned case also joins the
   `default_open_functions` entry (§10.4).
7. **Documentation and MCP.** Synchronized **in the E2 change itself** (§11):
   `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`,
   `docs/contract/semantic_facts.json`, the MCP idiom text in `apps/mcp/mcp.genia`
   with its golden file, the host capability matrix, the contract's status line and
   this document's status. Until E2 merges, all of them keep saying closed
   publication is not implemented.

## 10. RED evidence plan (inventory only; no test is written or changed here)

Proposed ids name observations; approved literals are recorded in §12.
`C` = the approved `closed_functions`. `D` = `default_open_functions`. No manifest
or runtime claim is changed during E1 TEST.

### 10.1 E1 — host-local only

E1 has no source activation, so nothing is observable through R16. This follows the
accepted D2a precedent. The current E1 TEST authorization covers private callable
construction, controlled lifecycle-state fixtures, guards, rendering, transport and
capture exclusion. It does not authorize transactions, windows, reservations,
`Env.get` changes or lineage behavior. The original E1-04 through E1-07 admission
rows below are retained as future E2 inventory, not current E1 commitments. E1-01
name/annotation validation and E1-12 live-slot checks likewise belong to E2; E1
can cover pure clause construction and lexical-frame shape without activation.

| Id | Observation |
|---|---|
| E1-01 | Whole-group build: duplicate key, conflicting inline documentation; with several simultaneous errors the order is name, annotation permission, clause structure; a sentinel proves no annotation, guard or body ran |
| E1-02 | Use check at each §7.2 entry point, for `initializing` not admitted and for `failed`: direct call, `invoke_callable`, tail call, `apply_raw`, matcher use, callback through a builtin, extracted record |
| E1-03 | Precedence: a failed callable called with `none`, with `err`, with the wrong arity and with a failing guard gives the state error each time; a sentinel proves nothing else ran |
| E1-04 | Admission: admitted inside an open window; refused before the window opens, after it closes, behind a barrier on the same thread, on a new thread, from a context copied inside the window and run after it or on another thread, and from a copied context run by a scheduler boundary on the same thread while the window is still open |
| E1-05 | Nested transactions on one stack: each callable admitted only against its own; a barrier hides both; closing the inner window leaves the outer |
| E1-06 | Bridges keep authority: an admitted call through a callback-taking builtin, a forced lazy value, a pulled Flow |
| E1-07 | Boundary inventory: every actual handler-dispatch and thread-start site in the host is classified, and each boundary is exercised at its real dispatch site to show that it pushes a barrier and pops it again, also when its callable raises |
| E1-08 | Introspection and link-target rejection in both non-committed states, including for an admitted caller |
| E1-09 | Sealing: `add_clause` and `merge_metadata` refused; a clause declared through an alias, through a re-export and through the restored original spelling after failure raises `closed-function-not-extensible`; an annotated alias leaves the callable's metadata unchanged |
| E1-10 | Transport through assignment, collection, Ref and Cell; identity equality; markers nested in list, map, pair and Outcome; no arity, metadata, source or protected sentinel in any rendering or diagnostic; JSON keeps its existing function behavior |
| E1-11 | Storage is not invocation: `spawn`, a lazy Flow stage and a registered handler accept a failed callable; the error appears only when it is run; an unpulled stage raises nothing |
| E1-12 | Self frame: unshadowed self-reference; a parameter and a pattern binder with the function's name shadow it and stay assignable; assignment to the name without a local binding is rejected; other names pass through; debugger scope listing; inherited module identity |
| E1-13 | D1 capture skips closed exports, aliases and re-exports; ordinary originals and re-exports keep their witnesses |
| E1-14 | Non-activation: every closed source form still raises `model-b-not-implemented`; the full existing regression is unchanged |

### 10.2 E2 — shared R16 cases

| Proposed id (`model-b-closed-…`) | Category | Requires | Observation |
|---|---|---|---|
| `single-clause`, `multi-clause-order` | eval | C | Dispatch as ordinary; the declaration's value prints as the committed marker |
| `pattern-guard-headers` | eval | C, D | Pattern and guard headers dispatch as ordinary |
| `self-recursion`, `deep-tail-call` | eval | C | Recursion; constant-stack tail call where the host supports it |
| `comments-blank-lines-one-group` | eval | C | One group |
| `parameter-shadows-own-name` | eval | C | `f(f) =: f` returns its argument |
| `mixed-operators` | error | C | Parse error; nothing runs |
| `duplicate-key-no-effects`, `conflicting-docstring` | error | C | Existing diagnostics; an annotation sentinel is not printed |
| `name-collision-existing`, `name-reserved-runtime`, `name-collision-import` | error | C (+`multi_file_eval`) | Rejected before any annotation effect |
| `validation-order` | error | C | With a name collision, a forbidden annotation and a duplicate key together, the name error is reported |
| `alias-mutable-name-immutable` | cli | C, `repl` | The alias rebinds; the defining name does not; both observed after the rejection |
| `second-group-after-statement`, `ordinary-clause-after-closed`, `repl-later-submission-clause` | cli | C, `repl` | Rejected; a later submission shows the first group still works |
| `alias-clause-rejected`, `restored-name-clause-rejected` | cli | C, `repl`, `refs` | `closed-function-not-extensible` through an alias and through the original spelling restored after a failed publication |
| `annotation-permitted-set` | eval | C, `doc_help` | The six permitted kinds, including `@test`, merged in order |
| `annotation-forbidden-route` (+ `get`, `post`, `server`, `cors`) | error | C | Rejected at T2; an earlier permitted annotation's sentinel is not printed |
| `annotation-meta-keys-allowed` | eval | C | `@meta` with `route` and other keys is accepted as data |
| `annotation-self-call`, `annotation-helper-self-call`, `annotation-recursion` | eval | C | The annotation calls the function directly, through a module-scope helper, and recursively |
| `annotation-reaches-later-clause` | eval | C | An annotation on clause 1 dispatches to clause 2 |
| `annotation-order-and-atomic-metadata` | eval | C, `doc_help` | Effects in group order; `meta` shows the merged map only after the declaration |
| `annotation-introspection-while-initializing` | error | C, `doc_help` | `doc`/`meta` of its own name inside an annotation: `closed-function-not-yet-published` |
| `annotation-effect-then-value-failure` | cli | C, `repl` | A permitted annotation's effect is visible; a later annotation's invalid value fails the declaration; the name is unbound and no metadata exists |
| `failed-escape-transport-ref`, `failed-escape-transport-cell` | cli | C, `repl`, `refs` / `cell_primitives` | The stored reference survives; renders as the failed marker, also nested; equal to itself only |
| `failed-call`, `failed-call-none`, `failed-call-err`, `failed-call-wrong-arity`, `failed-apply-raw`, `failed-higher-order`, `failed-matcher`, `failed-tail-call` | cli | C, `repl`, `refs` | `closed-function-failed-publication` each time |
| `failed-pipeline-upstream-none-skips`, `failed-flow-not-pulled` | cli | C, `repl`, `refs` (+`flow_phase_1`) | The stage is not invoked; no error |
| `failed-flow-pulled` | cli | C, `repl`, `refs`, `flow_phase_1` | The error appears at the pull |
| `failed-introspection` | cli | C, `repl`, `refs`, `doc_help` | `doc`/`meta`/`help` rejected |
| `failed-inner-lambda-self-reference` | cli | C, `repl`, `refs` | A lambda created by a clause body still reaches the failed callable after the name is reused |
| `repl-name-reuse-new-identity` | cli | C, `repl`, `refs` | The new declaration works; the old reference stays failed and unequal to the new one |
| `committed-export-not-link-target`, `reexported-closed-not-link-target` | error | C, `multi_file_eval`, `open_functions` | `open-function-target-not-open` |
| `committed-export-callable`, `ordinary-linking-unaffected` | eval | C, `multi_file_eval`, `open_functions`, D | A plain cross-module call works; D2b linking of an ordinary function in the same program is unchanged |
| `main-selection` | cli | C | Per DQ-M |
| test-mode and `send_annotated` cases | cli / error | C | Per the Q-C1b rulings (§5.2, §5.3) |
| `model-b-c-stage-closed-rejected` | eval | changes | **Authorized transition** (§10.4) |

Observations made *after* a rejection use the REPL, because a file or command stops
at the first error (§2).

### 10.3 E2 — host-local

| Id | Observation |
|---|---|
| E2-L1 | Barrier-synchronized second thread holding an escaped reference: refused during `initializing`; paused at each of C1, C2, C2b, C3, C4, C5 and K1–K4, it sees either the unpublished or the fully published function, never a mixture: for a call through the reference, for `doc`/`meta`/`help`, and for a name lookup and a metadata lookup made immediately afterwards in the declaring scope and through the self frame |
| E2-L2 | A fault injected at each of P1–P5, T5 (including `BaseException`), window close, C1, C2, C2b, C3, C4, C5, F1 and F2, and after each of K1, K2, K3 and K4 on both the publication and the failure path: the end result matches §4.4; afterwards there is a terminal state or a discarded callable, no slot of that transaction, the transaction absent from the open set, and either a complete binding with metadata or none at all; the name is reusable after failure |
| E2-L2a (allocation follow-up) | Inject a single allocation failure at each actual C4/C5 metadata/binding dictionary insertion, including dict growth, before and after the insertion takes effect. Retry inside the same lock hold. The state stays committed; binding, metadata and immutable membership complete; K1–K4 remove only the owner's reservations. This is a single-fault model, not a progress guarantee under persistent OOM. |
| E2-L3 | No execution observes `committed` and later `failed` |
| E2-L4 | Slots: an outer binding of the same name is resolved by non-admitted code and the provisional callable by admitted code; the self-frame slot refuses an escaped closure; a write to the name is rejected before its right-hand side runs and is never redirected to the outer binding; every writer listed in §6.6 is covered |
| E2-L5 | The request-handler example of §6.4 with a real `serve_http` dispatch on the declaring thread |
| E2-L6 | Nested transactions through a module load triggered by an annotation |
| E2-L7 | Source and direct Core IR agree, for valid groups and for malformed IR, multiple simultaneous errors and forbidden annotations |
| E2-L8 | The lookup fast path is structurally unchanged while no slot is open (not a timing test) |
| E2-L9 | The binding lock is not held while an annotation or a function body runs |
| E2-L10 (N1) | A hook pauses closed `f` after T5 and before it takes the lock. Another thread commits immutable `g` in the same scope. `f` resumes and commits. Both `f` and `g` reject assignment afterwards. Variants: two closed publications `f` and `h` interleaved at the same point, in both orders; `g` committed while `f` waits for the lock; an allocation failure injected at C2b leaves `f` failed and unbound, `g` still immutable, and the name `f` reusable |
| E2-L11 (N2) | Two live transactions A and B. One fault is injected in A's close routine after K1, after K2 and after K3 (before K4), on the publication path, the failure path and an aborted T4. After A exits: A has no slot and is not in the open set; B is in the open set with both slots; lookups do not take the fast path; B's admitted helper resolves B's provisional function and not an outer binding of the same name; a write to B's name is still rejected. Then B completes and the set is empty |
| E2-L12 (N3) | A hook pauses the use check on a non-declaring thread between its state read and its descriptor read, with the state read as `initializing`. The owner then reaches `committed`, and in a second run `failed`. The paused check resumes and returns `closed-function-not-yet-published`, with no other exception. A following call gives the terminal behavior. `_txn` is the same object before and after. The same pause is applied to a slot lookup after it has fetched the slot, in the declaring scope and in the self frame |

A shared twin of E2-L1 is not assumed. The portable process primitives (`spawn`,
`send`, `process_alive?`, `process_failed?`, `process_error`) have no deterministic
wait, and shared cases must not claim concurrency evidence they cannot prove.

### 10.4 The authorized oracle transition and its inventory

`spec/eval/model-b-c-stage-closed-rejected.yaml` has this source, which stays
unchanged:
```genia
print("before")
f(0) =: { print("child"); 0 }
```

| | Today | After the E2 transition (DQ-S and DQ-L approved) |
|---|---|---|
| stdout | `before` | `before` then `<closed-function f>` |
| stderr | `Error: model-b-not-implemented: declaration evaluation is not available` | empty |
| exit code | 1 | 0 |
| `requires` | none | `closed_functions`, `default_open_functions` (the clause has a pattern header) |

The second stdout line follows from the design: the declaration is the last
statement, its value is the committed callable, and command mode prints a non-nil
final value (§2). The body is not run, so `child` is not printed. No fixture change
is needed and no output-suppression rule is added. DQ-S and DQ-L approve this
result and marker. This oracle remains unchanged until the authorized E2 transition.

Every place that must change with it, in one dedicated commit that records the old
and new text:

| Location | Change |
|---|---|
| `spec/eval/model-b-c-stage-closed-rejected.yaml` | expected output, `requires`, notes |
| `tests/spec/test_model_b_slice_c_red.py` | move the id from `SLICE_C_GUARD_IDS` to `SLICE_C_GATED_IDS`; `SLICE_C_REQUIRES` entry; literal counts 53 → 52 guards, 84 → 85 gated, 90 → 91 all gated (lines 354-355, 359, 388); 137 red cases and 143 total unchanged |
| `tests/unit/test_model_b_slice_c_capability_evidence.py` | docstring "53 guards plus 90 gated" → "52 guards plus 91 gated" (line 9); `len(gated) == 90` → `91` (line 58); 143 unchanged (line 54) |
| `docs/host-interop/HOST_CAPABILITY_MATRIX.md` | "53 existing-behavior guards plus 90 gated cases" → 52 and 91 (lines 135-136) |
| `spec/known_host_gaps.json` | add the id to the `default_open_functions` entry, which the harness compares with the gated set |

The literal counts, the id sets and the loaded-spec count stay three independent
assertions. Host-local tests that assert `model-b-not-implemented` for closed forms
get the same explicit, recorded transition.

### 10.5 Rules for the RED commits

- A shared case must fail because the feature is missing, not because a helper or
  environment is missing.
- A case that needs an observation after a failure is a REPL or host-local case.
- Host-local constructor tests are the right tool for E1 internals. Deterministic
  barriers belong in host-local tests where shared primitives cannot express the
  ordering.
- No existing oracle changes except §10.4, and none in this phase.

### 10.6 Regressions to preserve

All D1/D2a/D2b suites, R20 open-function suites, Slice A/B/C inventories, annotation
and lexical-assignment suites, native-test and `send_annotated` suites, REPL
characterization, module isolation, Outcome, Flow and protected-value suites, and
both regression partitions.

## 11. Delivery

Lifecycle phases (RED, implementation, review, audit) apply inside each
code-bearing change. The table below is about **mergeable PR boundaries**.

| PR | Content | Truth documents | RED gate |
|---|---|---|---|
| **E1** | Sealed `GeniaClosedFunction`, guarded records, self-frame shape, whole-group builder, use check at every §7.2 point, markers, sealing in `define_function` and the metadata writers, capture exclusion. **No source activation** and no `Env` lookup change: closed source still raises `model-b-not-implemented`. | One accurate sentence in `GENIA_STATE.md` at E1 GREEN: private closed-function machinery exists and is unreachable from source (the D2a precedent). | §10.1 |
| **E2** | Lineage stack/barriers and annotation windows, transaction T0–T7, guarded slots and lookup, publication and failure protocols, source activation, shared specs, the §10.4 transition, the capability and gap entries, **and the full implemented-truth synchronization of §9 item 7**. | Updated in this PR, so `main` is never ahead of or behind its documents. | §10.2, §10.3 |
| **E3** | Independent integration audit, distillation, remaining follow-ups. | Corrections only if the audit finds drift. | none (verification) |

E1 can merge alone: nothing in it is reachable from source, and its additions to hot
paths (one type test at the top of `invoke_callable`) must be behavior-neutral for
existing programs. E1 exercises non-admitted initializing use and terminal states
through private host fixtures; active admission, lineage and slots remain E2.
An inability to express meaningful E1 RED without implementation scaffolding is a
blocker to report under the E1 TEST authorization, not permission to implement the
scaffolding or expand into E2. A half-defined state machine is not merged for the
sake of the split.

**Risks.**
1. A missed boundary admits a call it should refuse. Mitigation: the E1-07 inventory deferred to E2.
2. A missed use-check site. Mitigation: guarded records, E1-02, full regression.
3. `Env.get` is on the hottest path. Mitigation: the fast path taken while the open-transaction set is empty, E2-L8.
4. `GENIA_STATE.md` is at 42,845 of its 43,000-word limit. E2's synchronization must
   fit, or a distillation must precede it in the same change.
5. Free-threaded Python. The protocols rely on single stores and one lock, not on
   the GIL; E2-L1 should run on a free-threaded build where CI has one.
6. Fault injection covers single faults only (§4.4).

**Complexity: necessary.** One dispatcher. The new parts are two small subclasses,
one transaction object, one slot table, one thread-local stack and one check helper.

## 12. Approved decisions before RED

The final maintainer ruling approves Q-C1b and DQ-L/V/S/M/C below and confirms
DQ-I, which was already fixed by the contract. These are intended semantics, not
implemented claims. E1 TEST alone is authorized; implementation and E2 require
separate authorization.

| Id | Contract requirement | Approved choice | Compatibility effect | RED evidence |
|---|---|---|---|---|
| **Q-C1b** `@test`, `test` and `http_annotation` keys, alias discovery, other names | §4.3: six names permitted, five names and all other unsupported names rejected; ordinary-compatible annotations | (a) `@test`: **Alternative A**, closed functions are discoverable through any of the three sources (§5.2). (b) `send_annotated`: closed callables excluded (§5.3). (c) Other unsupported names: rejected at T2 with `closed-function-annotation-not-permitted`. (d) No `@meta` key is banned. | None for existing programs; closed evaluation is rejected today. (a) extends the previously approved name list by one. (c) differs from ordinary functions in timing. | `cli` test-mode cases for the three sources, wrong arity and a failed publication; `send_annotated` rejection; unknown-name and `@meta`-key cases |
| **DQ-L** literals | §4.2 fixes the two identities and a sanitized failed marker | `closed-function-not-yet-published: NAME is not yet published`; `closed-function-failed-publication: closed function failed publication`; `closed-function-annotation-not-permitted: @ANNOTATION is not permitted on closed function NAME`; `closed-function-not-extensible: cannot declare LABEL: NAME refers to a closed function`; markers per §7.4 | New texts only | Every error and rendering case in §10 |
| **DQ-V** validation order | §4.1: validate before exposing anything; order among competing errors unspecified | T0 well-formedness, then name, then annotation permission, then clause structure; parse errors precede all of them for source | None | `validation-order`, E1-01, E2-L7 |
| **DQ-S** declaration value | Contract §4.5 records the final ruling | The committed callable; never a clause record. The historical no-value alternative was not selected. | Determines the second stdout line of §10.4 and of every case that ends with a closed declaration | `single-clause`, §10.4 |
| **DQ-M** closed `main` | Contract §4.5 records the final ruling | A committed closed `main` is selected exactly as an ordinary one: only a simple identifier-header group, `main/1` before `main/0`, the same modes and existing varargs rules, never in the REPL; through the use check and guarded records | A closed `main` would otherwise be silently ignored | `main-selection`, plus a pattern-header closed `main` that is not selected |
| **DQ-I** introspection while initializing | **§4.2 requires rejection** | Rejected for every caller, admitted or not | — | `annotation-introspection-while-initializing`, E1-08 |
| **DQ-C** capability | §6.1 item 4: reuse the vocabulary, never mislabel supported behavior; conformance obligation: add a capability only for an independently claimable surface | Add optional `closed_functions` (§9 item 4) | A conformance-contract addition; no existing claim changes meaning | The `requires` of every §10.2 case; adapter staging test |

## 13. Process note, file plan and final check

**Branch name.** The original design PR #1320 uses `claude/brave-babbage-qb2zvm`. `docs/process/run-change.md`
and `scripts/check-genia-branch.sh` require `issue-<number>-<short-name>`, and this
branch fails that check. The original authoring session did not rename it. This is
an open process item, not an accepted exception: before
merge the maintainer either records an explicit exception or the commits are moved to
a compliant branch. The E1 TEST reconciliation uses the compliant
`issue-1250-slice-e1-red` branch with the original design ancestry preserved; it
does not modify or merge PR #1320 and grants no exception to that PR's branch.

**New:** this document (KEEP, design record). **Modified in this phase:** the Model B
contract (§4.3 and a status phrase) and one pointer line in the portable design.
**Removed:** none.

**Final check (docs/process/02-design.md):** the contract text records Q-C1 and the
final Q-C1b/DQ rulings. Every previously open choice is recorded with its
alternatives and approved selection in §12. The dictionary-allocation correction
retains the accepted roll-forward protocol. E1 TEST stage boundaries follow the
explicit authorization. Nothing here is described as implemented.
