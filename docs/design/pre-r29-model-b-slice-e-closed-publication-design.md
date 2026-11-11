# Model B Slice E: closed-function publication (E1 + E2)

Status: **DESIGN PROPOSED — awaiting independent review. Nothing here is implemented.**
Python parses and lowers closed `f(pattern) =: expression` groups, and evaluation
still rejects them with `model-b-not-implemented`. `GENIA_STATE.md` remains the only
authority on implemented behavior. Phase record for
[#1250](https://github.com/m0smith/genia-2026/issues/1250), authorized as a docs-only
design by [comment 6803222025](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6803222025),
following the [Slice E preflight](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6802507721).
Source line numbers refer to `main` at `2c9bb7c4d54f532521f680590dfb1bee2a310dc4`.

Governing sources: the maintainer-approved
[Model B contract](pre-r29-default-open-and-immutable-binding-contract-DRAFT.md)
(§§3, 4.1–4.3, 6.1), the [portable design](pre-r29-default-open-and-immutable-binding-design.md)
(§§6.2, 7–9), the Q-C1 ruling on
[#1249](https://github.com/m0smith/genia-2026/issues/1249#issuecomment-6803212555),
and the accepted [D2 linking design](pre-r29-model-b-d2-linking-design.md).

This design authorizes no RED test, production code, capability, C++ change or R29 work.

## 1. Scope lock

**Includes (Python reference host):** one closed callable and one immutable defining
name per maximal consecutive same-name `=:` run; whole-group validation before any
annotation runs; a provisional callable visible only to the declaring execution;
ordered annotation evaluation with one atomic commit; the initializing, committed
and failed states; failed values that can be passed around but not used; error
precedence; REPL submission boundaries; exclusion from D2b linking.

**Excludes:** new syntax or `@closed`; changes to accepted D2b linking or R20
dispatch; a new Core IR node or version; rollback or cancellation of external
effects; server discovery of closed functions; C++ implementation or parity; R29.

**Decisions this design needs from the maintainer before RED** are collected in §12.

## 2. Verified starting point

| Fact | Evidence |
|---|---|
| A closed run parses to one `ClosedFuncDef` and lowers to one `IrClosedFuncDef` whose `declarations` are `IrFuncDef` or `IrPatternFuncDef`, each carrying its own annotations | `parser.py:442-527`, `lowering.py:249-250`, `ir.py:336`; probe: `@doc` on clause 1 and `@meta`, `@route` on clause 2 stay on their own clause |
| Comments, blank lines and `;` do not end a run; another statement does (two groups result) | probe of 11 source variants |
| `=` and `=:` clauses of one name side by side are a parse error | `parser.py:520-521`, `mixed-function-declaration-operators` |
| A closed form inside a block or lambda, a dotted name, or `->` is a parse error | probe |
| Parser state does not survive a submission; a trailing `=:` keeps the REPL reading | `parse_program` at `parser.py:233-242`; `interpreter.py:157-191` |
| Evaluation rejects every closed group | `evaluator.py:1407-1414` |
| An ordinary declaration publishes its clause before its annotations run | `evaluator.py:1659-1712` (`define_function` at 1702, annotations after) |
| An immutable `=:` bind publishes its value, then attaches metadata | `evaluator.py:1714-1735` |
| `eval_annotations` evaluates in order, validates each value at once, and returns a private map | `evaluator.py:692-757` |
| `commit_immutable_declaration` revalidates under the binding lock and accepts `metadata=` | `environment.py:453-474` |
| `GeniaFunctionGroup.add_clause` works on a group that is not bound anywhere | `callable.py:314-337` |
| D1 capture records every exported `GeniaFunctionGroup` whose `owner` is set | `ordinary_completion.py:148-151` |
| A function value renders through its Python `repr` | `utf8.py:66-113`; probe prints `GeniaFunctionGroup(name='f', functions={1: <function f/1>}, …, metadata=<map 2>)` |
| There is no construct that catches a runtime error inside one program | no `try`-like builtin or prelude function exists |
| The host starts processes and cells on their own OS threads and uses no `asyncio`, signal handlers or finalizers | `values.py:609,713,773`; grep of `src/genia` |

The last two rows shape the evidence plan: within one file or command, a failed
declaration ends the program, so a failed callable can only be used later in a
REPL session or from another thread.

## 3. Representation

### 3.1 `GeniaClosedFunction` (E1)

A closed callable is a new subclass `GeniaClosedFunction(GeniaFunctionGroup)` in
`callable.py`. It stores its clauses as ordinary `GeniaFunction` records and
dispatches through the inherited stratum and first-match logic, so recursion, tail
calls, Outcome awareness and pattern/guard headers are the ordinary ones.

It adds three private fields: `_state` (`initializing`, `committed` or `failed`),
`_owner_thread` (the declaring thread object, cleared when the state leaves
`initializing`), and `_closed_name`. It overrides `__call__`, `_dispatch_once`,
`__repr__` and `__str__`. `owner` stays `(module identity, defining name)`.

| Alternative | Verdict |
|---|---|
| A state flag on `GeniaFunctionGroup` | Rejected. Every ordinary call would pay for a state check, and the dataclass `repr` would have to change for ordinary groups. |
| A class unrelated to `GeniaFunctionGroup` | Rejected. `GeniaFunctionGroup` is referenced on 50 lines in 12 source files, including at least 21 `isinstance` checks that handle dispatch, awareness and reflection. A second class means a second dispatcher, which the contract forbids (§6.1 item 2). |
| **Subclass** | Chosen. Ordinary groups are untouched; every existing `isinstance` site keeps working. |

Class-name checks were audited: `values.py:84` and `equality.py:128` compare class
names, and both fall through to their `callable(value)` branch for the subclass.
The results are unchanged: runtime type name `function`, equality by identity.

### 3.2 Self frame (E1 shape, E2 use)

Each closed callable owns one private scope, the **self frame**:
`Env(parent=declaring scope)` holding only the defining name bound to the callable,
marked immutable. Every clause record uses the self frame as its closure.

A reference to the function's own name written inside a clause body therefore
always resolves to this exact callable. It never resolves to a later declaration
that reuses the name (contract §4.2). This also holds for a lambda created by a
clause body that outlives a failed publication: calling the name from that lambda
reaches the failed callable and is rejected.

Consequences that the implementation must handle:
- At commit, the committed metadata map is also stored on the self frame, so
  `doc`/`meta` called from inside a clause body see the same map as callers outside.
- An assignment to the defining name from a clause body hits the immutable binding
  in the self frame and is rejected with the existing immutable diagnostic.
- The self frame inherits `module_identity()` and `unit_scope()` from its parent, so
  provenance and module ownership are unchanged.
- Debugger and inspection views gain one scope level between a clause frame and its
  module. E1 pins what they show with a host-local test.

## 4. Lifecycle transaction (E2)

Evaluating one `IrClosedFuncDef` runs steps T0–T7 on the declaring thread. T0–T3
evaluate no user code. Source and direct Core IR both enter at T0.

| Step | Action | Failure |
|---|---|---|
| T0 | `assert_portable_core_ir([node])` (existing) | existing `ValueError` |
| T1 | Name check in the declaring scope: not already bound, not reserved by another transaction, not runtime-owned (the `_check_declaration` rules, `environment.py:420-441`) | existing `ImmutableBindingError` texts |
| T2 | Annotation permission scan (§5): every annotation name of every clause, in source order | `closed-function-annotation-not-permitted` |
| T3 | Build the callable and self frame privately; add each clause record in source order with `add_clause` | existing duplicate-clause and conflicting-documentation errors |
| T4 | **Provisional publication**, under the binding lock: repeat T1, reserve the name (§6), set `initializing` and the owner thread | as T1 |
| T5 | Evaluate annotations in group order (clause 1's in source order, then clause 2's, …) in the self frame; fold each clause's map into one private map with the existing `_merge_metadata_maps` | the annotation's own error |
| T6 | **Commit** in one lock hold (§4.1) | — |
| T7 | **Failure**: on any exception leaving T5 or T6, including `BaseException`: set `failed`, then withdraw the reservation, then re-raise the original exception unchanged | — |

If T1–T3 fail, nothing was published and no value can have escaped. The whole group
is validated before the first annotation runs, so an annotation on clause 1 does not
run when clause 3 is a duplicate. This is the contract's "explicitly different
atomic closed-publication rule": an ordinary declaration publishes clause by clause.

During T5 the callable already has all of its clauses, so an annotation on clause 1
may call the function and reach clause 2.

The statement value of a successful closed declaration is the committed callable.
An ordinary declaration returns its clause record (`evaluator.py:1712`); a closed
declaration must never hand out a bare record, because records carry no state guard.

### 4.1 Commit order

All inside one hold of `_BINDING_LOCK` (`environment.py:37`), in this order:
1. repeat the T1 name check;
2. store the final metadata map on the callable and on the self frame;
3. set the state to `committed` and clear the owner thread;
4. store the declaring scope's binding metadata;
5. mark the name immutable in the declaring scope;
6. bind the name to the callable;
7. remove the reservation.

`Env.get` reads without the lock. With this order, any reader that finds the binding
finds a committed callable with its metadata already in place. No reader can see a
bound name whose callable is still initializing.

Effects of annotations are never rolled back, on commit or on failure.

### 4.2 Metadata channels

Closed callables use the ordinary three observations unchanged: binding annotations
(the committed map), inline documentation (the group docstring, merged at T3), and
help (the existing `_describe_function_group`). Until commit, the private map exists
only as a local value: it is not on the callable, the self frame or any scope. A
failed callable therefore never carries partial metadata.

## 5. Annotation permission (Q-C1)

The Q-C1 ruling fixes the two lists. This design fixes where the check runs.

| Annotation on a closed clause | Result |
|---|---|
| `@doc`, `@meta`, `@since`, `@deprecated`, `@category` | Permitted. Existing per-annotation validation applies at T5. |
| `@route`, `@get`, `@post`, `@server`, `@cors` | Rejected at T2. |
| `@test` | **Undecided** (§12, Q-C1b). This design recommends rejection at T2. |
| Any other name | **Undecided** (§12, Q-C1b). This design recommends rejection at T2. |

**Validation point.** T2 scans the annotation names of the whole group before any
annotation expression is evaluated. Names are static in Core IR
(`IrAnnotation.name`), so the scan runs no user code. The ruling prefers this
pre-scan. It does not alter the §4.2 order of the contract: that order governs
evaluation of permitted annotations, and it starts only after structural validation,
of which "permitted metadata" is a listed part (contract §4.1).

The scan runs at evaluation, not at parse or lowering. A direct Core IR caller then
gets the same rejection as source, and statements before the declaration in the same
program still run, as they do for every other evaluation-time declaration error.

**Alternative considered:** reject a forbidden annotation only when evaluation
reaches it. Rejected, because earlier annotations would already have run and a
provisional callable could have escaped for a declaration that can never succeed.

**Server discovery is unchanged.** The three walkers still reject an entry program
that contains any closed declaration with `model-b-not-implemented: server discovery
is not available` (`server_route_binding.py:211-214`, `server_config_binding.py:218-221`,
`server_cors_binding.py:182-185`). No registration mechanism is added.

### 5.1 `@test`: inventory and recommendation

`genia test` evaluates the entry file, then `discover_annotated_test_units`
(`test_cli.py:175-209`) scans the entry scope's bindings. For each binding whose
metadata has a `test` key it requires a `GeniaFunctionGroup`, a non-empty string
description and exactly arity 0. It then takes the group's single plain record with
`single_plain_record()` and schedules that record as the test body. Imported modules
are not scanned. The legacy registrar `test(name, body)` is a separate path that
stores whatever value it is given.

**Recommendation: exclude `@test` from closed declarations in Slice E**, rejected at
T2 like the HTTP family.
1. Discovery executes a bare record, bypassing the callable. That is safe only
   because a bound closed callable is always committed. Supporting `@test` makes that
   invariant part of test-mode behavior.
2. Support adds test-mode CLI behavior to Slice E's RED and evidence, with no
   Model B semantics gained. A closed test function has no extension to prevent.
3. Exclusion is reversible. Allowing `@test` later is additive; removing it after
   release is a break.

**If the maintainer prefers support**, the cost is small in code (the subclass
already passes discovery's `isinstance`) and is mostly evidence: shared `cli`
test-mode cases for a passing closed test, a wrong-arity closed test, and a failed
closed publication that must not be discovered; plus documentation of the discovery
rule. The legacy registrar needs no decision: it calls its body as a value, so the
state guard applies.

## 6. Provisional name and admission (E2)

### 6.1 Admission rule

> While a closed callable is `initializing`, an invocation is **admitted** if and
> only if it runs on the declaring thread. Every other invocation, and every
> callable-specific introspection on any thread, is rejected with
> `closed-function-not-yet-published`.

The declaring thread is blocked inside T5 for the whole `initializing` period.
Everything that executes on that thread in that period is therefore inside the
dynamic extent of the declaration's annotation evaluation: the annotations, the
helpers they call, recursive calls, and lazy values they force. This is exactly the
contract's "synchronous invocations arising from its declaration-owned annotation
evaluation and their recursive calls". The rule needs no token passed through calls.

The host compares the thread **object** (`threading.current_thread() is owner`),
not the numeric id, so id reuse cannot admit another thread.

A process or cell handler runs on its own thread (`values.py:609`). It is never
admitted, even when it holds the callable, because admission is a property of the
executing thread and not of the value or of any inherited context.

| Alternative | Verdict |
|---|---|
| A `contextvars` token | Rejected. A context can be copied into another thread or task, which is the inheritance the portable design (§6.2) rules out. |
| A token threaded through evaluator calls | Rejected. Host bridges call `fn(*args)` directly and would drop it, so legitimate synchronous calls through a builtin would be refused. |
| **Declaring thread while `initializing`** | Chosen. Not inheritable, not forgeable from Genia code, no cost outside a transaction. |

Portable statement for other hosts: admission belongs to the host's unit of
synchronous execution. That is the OS thread here. A host that multiplexes tasks on
one thread must use the task.

A lazy value created during T5 and forced later is not special. By then the
callable is committed or failed, and the ordinary state rule applies.

### 6.2 Name reservation

The self frame makes the name visible to clause bodies and to the annotation
expressions themselves. It does not cover an annotation that calls a helper whose
closure is the module scope and which refers to the function by name. For that case
the declaring scope holds a **reservation** from T4 until T6 or T7.

- **Lookup.** `Env.get` (`environment.py:476-487`) resolves a reserved name to the
  provisional callable only when the current thread is admitted. For any other
  thread the reservation does not exist: the lookup continues to the parent scope
  and ends as it would have before the declaration.
- **Precedence.** The reservation is consulted at the declaring scope's own level,
  before the walk moves to the parent. A module may declare a closed function whose
  name also exists in the runtime scope, and the helper must find the provisional
  callable, not the runtime one.
- **Writes.** From T4 to T6 or T7 the declaring scope treats the reserved name as an
  immutable binding for every writer on every thread: assignment, ordinary
  declaration, import alias, `use`, another `=:`. Rejections use the existing
  immutable diagnostics.
- **Withdrawal.** T7 removes the reservation after marking the callable failed. The
  name is then free; nothing was bound, so there is nothing to roll back.
- **Cost.** `Env.get` is on every name lookup. The reservation table is consulted
  only while a process-wide count of open transactions is non-zero; otherwise the
  lookup path is the current one plus one integer test.

| Alternative | Verdict |
|---|---|
| Self frame only | Rejected. The module-scope helper case fails; the portable design (§6.2) names it explicitly. |
| Bind the name in the declaring scope at T4 and rely on the state guard | Rejected. Every thread could then resolve the name, but the contract makes it available "only" to the admitted execution. Failure would also have to delete a binding. |
| **Reservation with admitted lookup** | Chosen. |

Transactions may nest on one thread, for example when an annotation triggers a
module load that declares its own closed function. Each callable has its own owner
thread and each scope its own reservation table. A second closed declaration of a
name that is reserved in the same scope fails at T1.

## 7. Use rules and error precedence (E1)

### 7.1 State table

| State | Invoke, declaring thread | Invoke, other thread | `doc`/`meta`/`help`; `extend`/`use` target | Assign, pass, return, store, compare, render |
|---|---|---|---|---|
| initializing | ordinary call | `closed-function-not-yet-published` | `closed-function-not-yet-published` | allowed |
| committed | ordinary call | ordinary call | ordinary reflection; as a link target `open-function-target-not-open` | allowed |
| failed | `closed-function-failed-publication` | same | same | allowed |

Introspection is refused during `initializing` on the declaring thread too. The
contract admits invocations only; metadata does not exist yet.

### 7.2 Where the state is checked

One helper on the callable performs the check. It is called at exactly these points:

| Entry point | Location | Why here |
|---|---|---|
| `invoke_callable`, first statement | `callable.py:1552`, before `:1580` | `None`-argument propagation at 1580-1582 returns before any dispatch. The contract requires the state error first, so `failed(none)` is an error and not `none`. This also precedes the name-based Flow adapters, stratum selection and autoload. |
| `GeniaClosedFunction.__call__` | override | Every host bridge that calls a value directly lands here: process and cell handlers, `apply_raw` (`builtins.py:4321`), builtins that take callbacks. The inherited fast path for simple groups calls a record without passing `_dispatch_once`. |
| `GeniaClosedFunction._dispatch_once` | override | The trampoline calls this for a group reached through a `TailCall` (`callable.py:625`). |
| `_help_in_scope`, `_doc_in_scope`, `_meta_in_scope`, `_describe_function_group` | `builtins.py:3467, 3513, 3568, 3251` | After the name or value is resolved, before any metadata is read. |
| `extend` and `use` target resolution | `evaluator.py:1603` and `:1625`, right after `get_export` | Before the completion-witness lookup. |

Arity selection, pattern matching, guards and bodies all run after these points.
The Outcome-awareness helpers (`callable.py:1430, 1493`) only read clause structure
and are not guarded.

**Pipelines.** `eval_pipeline` (`evaluator.py:1135-1150`) returns a `none` or `err`
stage value before the next stage is evaluated. That stage is never invoked, so
nothing is rejected (contract §4.2, last sentence of the fourth paragraph). A stage
that is reached goes through `invoke_callable`; its state error is wrapped by the
existing pipeline-stage error text.

**Records.** Clause records have no guard. Two rules keep them unreachable for a
callable that is not committed:
1. No evaluator or builtin path returns a record of a closed callable as a value.
2. Host code that takes a record out of a group (`test_cli.py:196`,
   `http_annotation_binding.py:63`, `server_route_binding.py:270`,
   `interpreter.py:513-529`) reads the group from a **binding**, and only a
   committed closed callable is ever bound.

### 7.3 Transport and rendering

Assignment, argument passing, return, storage in a Ref or collection, closure
capture and equality need no check and get none. Equality stays identity
(`equality.py:125-133`). A failed callable is equal only to itself.

`spawn(failed)` succeeds, because creating a process does not invoke its handler
(`builtins.py:3759-3762`). The rejection happens on the worker when it first calls.

Rendering uses the overridden `__repr__`/`__str__`, which every display path reaches
(`format_display` and `format_debug` fall back to `str`/`repr`; diagnostics that
embed a value use `repr`). The markers show no arity, clause, metadata or closure
content. Proposed literals are in §12 (DQ-L).

## 8. Interaction with accepted D2b and other consumers

| Consumer | Design |
|---|---|
| D1 completion capture (`ordinary_completion.py:148-151`) | Skip `GeniaClosedFunction` explicitly. A closed export gets no completion witness. |
| `extend`/`use` on a committed closed export | `completion_for` returns `None`, so the existing `open-function-target-not-open` is raised. No new identity. |
| An ordinary clause declared through an alias of a closed callable (`a = f` then `a(0) = 1`) | `define_function` already raises `function-declaration-not-owner` because `owner` names the defining binding (`environment.py:705-712`). |
| A later clause under the defining name (`f(2) = 3` or a second `=:` group) | Existing immutable-binding rejections (`environment.py:386-390, 420-441`). |
| Entry `main` selection (`interpreter.py:513-529`) | A committed closed `main` is a simple group and is selected like an ordinary one. Recommended as ordinary-compatible; needs confirmation (§12, DQ-M). |
| Server discovery | Unchanged rejection (§5). |
| `genia test` discovery | Per Q-C1b. With exclusion, a closed function is never a discovered test. |
| Optimizer | `optimize_program` rewrites only top-level `IrFuncDef` (`optimizer.py:64-70`). Closed clauses are not optimized in Slice E; behavior is the same, only without that fast path. |
| Name-based Flow adapters and prelude-name awareness | Apply to a closed callable exactly as to an ordinary group of that name, after the state check. |

Combined D+E integration acceptance stays with
[#1251](https://github.com/m0smith/genia-2026/issues/1251). The link-target cases
above are part of Slice E because they prove the capture exclusion.

## 9. Portability analysis (`docs/process/run-change.md`)

1. **Observable semantics.** Group boundary; validation before effects; ordered
   annotation effects; self-call during annotation; the two state errors and their
   precedence; failed-value transport, equality and rendering; REPL name reuse.
   Thread admission is observable only with process primitives.
2. **Core IR and runtime boundary.** `IrClosedFuncDef` already carries the atomic
   group. No new node, field or version. State, reservation and admission are
   private runtime state.
3. **Shared executable conformance.** §10. The existing `ir` cases
   `model-b-a-closed`, `model-b-a-closed-run` and `model-b-a-closed-grouped` are
   unchanged.
4. **Capability applicability.** Reuse `immutable_bindings` and
   `default_open_functions`, adding `repl`, `refs`, `process_primitives` or
   `multi_file_eval` only on cases that use them. No new capability is proposed.
   Known limit: capabilities are claimed whole, so a host that later claims both
   prerequisites without closed publication would fail these cases. That event,
   not this slice, is the point at which a `closed_functions` capability should be
   proposed for approval.
5. **Host claims.** Python reference host only. The bounded C++ host declares
   neither prerequisite, so every closed case reports unsupported, never pass.
   [genia-cpp#50](https://github.com/m0smith/genia-cpp/issues/50) (parser and
   lowering) remains open. No parity claim.
6. **Gap recording.** At E2, add the new case ids to the `immutable_bindings`
   (#1261) and `default_open_functions` (#1269) entries of
   `spec/known_host_gaps.json` with their removal conditions. Owner: #1250,
   `@m0smith` until reassigned.
7. **Documentation and MCP.** After verified GREEN only: `GENIA_STATE.md`,
   `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`,
   `docs/contract/semantic_facts.json`, the MCP idiom text in `apps/mcp/mcp.genia`
   with its golden file, the host capability matrix, and this document's status.
   Until then every one of them keeps saying closed publication is not implemented.

## 10. RED evidence plan (inventory only; no test is written here)

Proposed ids name observations; literals are locked at RED against §12.
`I` = `immutable_bindings`, `D` = `default_open_functions`.

### 10.1 E1 — host-local only

E1 has no source activation, so nothing is observable through R16. This follows the
accepted D2a precedent (private machinery, host-local RED, no shared spec). Tests
construct `GeniaClosedFunction` values through the private constructor.

| Id | Observation |
|---|---|
| E1-01 | Whole-group build: duplicate key, conflicting inline documentation and the T1/T2/T3 order with multiple simultaneous errors; a sentinel proves no annotation, guard or body ran |
| E1-02 | Each §7.2 entry point rejects an `initializing` callable (other thread) and a `failed` one: direct call, `invoke_callable`, tail call, `apply_raw`, matcher use, callback through a builtin |
| E1-03 | Precedence: a failed callable called with `none`, with `err`, with the wrong arity, and with a failing guard gives the state error each time; sentinel proves nothing else ran |
| E1-04 | Introspection and link-target rejection in both non-committed states, including on the declaring thread |
| E1-05 | Transport: assignment, collection, Ref, closure, identity equality; markers contain no arity, metadata, source or protected sentinel |
| E1-06 | Self frame: lexical self-reference, immutable defining name, metadata mirror, debugger scope listing, inherited module identity |
| E1-07 | D1 capture skips a closed export; alias extension raises `function-declaration-not-owner` |
| E1-08 | Non-activation: every closed source form still raises `model-b-not-implemented`; full existing regression unchanged |

### 10.2 E2 — shared R16 cases

| Proposed id (`model-b-closed-…`) | Category | Requires | Observation |
|---|---|---|---|
| `single-clause`, `multi-clause-order`, `pattern-guard-headers` | eval | I, D | Dispatch as ordinary; declaration value renders as the committed marker |
| `self-recursion`, `deep-tail-call` | eval | I, D | Recursion; constant-stack tail call (Python only where depth requires it) |
| `comments-blank-lines-one-group` | eval | I, D | One group |
| `second-group-after-statement` | error | I, D | Second same-name group rejected; first still callable |
| `ordinary-clause-after-closed`, `closed-after-ordinary` | error | I, D | Existing immutable or collision diagnostics; no effect of the rejected clause |
| `mixed-operators` | error | I, D | Parse error; nothing runs |
| `duplicate-key-no-effects`, `conflicting-docstring` | error | I, D | Existing diagnostics; annotation sentinel not printed |
| `name-collision-import`, `name-reserved-runtime` | error | I, D (+`multi_file_eval`) | Rejected before any annotation effect |
| `alias-mutable-name-immutable` | eval/error | I, D | Alias rebinds; defining name does not |
| `alias-extension-rejected` | error | I, D | `function-declaration-not-owner` |
| `annotation-permitted-set` | eval | I, D | `doc`/`meta` after commit show all five permitted kinds merged in order |
| `annotation-forbidden-route` (+ `get`, `post`, `server`, `cors`) | error | I, D | Rejected at T2; an earlier permitted annotation's sentinel is not printed |
| `annotation-self-call`, `annotation-helper-self-call` | eval | I, D | Annotation calls the function directly and through a module-scope helper |
| `annotation-reaches-later-clause` | eval | I, D | Annotation on clause 1 dispatches to clause 2 |
| `annotation-order-and-atomic-metadata` | eval | I, D | Effects in group order; `meta` sees the merged map only after the declaration |
| `annotation-introspection-while-initializing` | error | I, D | `doc`/`meta` of own name inside an annotation: `closed-function-not-yet-published` |
| `annotation-failure-effects-persist` | cli | I, D, `repl` | Effect before the failure is visible; name unbound afterwards |
| `failed-escape-transport` | cli | I, D, `repl`, `refs` | Stored reference survives; renders as the failed marker; equal to itself only |
| `failed-call`, `failed-call-none`, `failed-call-err`, `failed-call-wrong-arity`, `failed-apply-raw`, `failed-higher-order` | cli | I, D, `repl`, `refs` | `closed-function-failed-publication` each time |
| `failed-pipeline-upstream-none-skips` | cli | I, D, `repl`, `refs` | Stage not invoked; result is the `none` |
| `failed-introspection` | cli | I, D, `repl`, `refs` | `doc`/`meta`/`help` rejected |
| `failed-inner-lambda-self-reference` | cli | I, D, `repl`, `refs` | Lambda created by a clause body still reaches the failed callable after name reuse |
| `repl-name-reuse-new-identity` | cli | I, D, `repl`, `refs` | New declaration works; old reference stays failed and unequal |
| `repl-later-submission-clause` | cli | I, D, `repl` | A clause in a later submission is rejected |
| `committed-export-not-link-target`, `committed-export-callable` | error/eval | I, D, `multi_file_eval`, `open_functions` | `open-function-target-not-open`; plain cross-module call works |
| `main-selection` | cli | I, D | Per DQ-M |
| `model-b-c-stage-closed-rejected` | eval | changes from none to I, D | **Authorized transition** (§10.4) |

Failed-callable cases use the REPL because no other mode lets a program continue
after the failing declaration (§2).

### 10.3 E2 — host-local

| Id | Observation |
|---|---|
| E2-L1 | Admission: a second thread holding the callable is rejected during `initializing`, synchronized with barriers, no timing assumptions |
| E2-L2 | A copied `contextvars` context and a freshly started thread are not admitted |
| E2-L3 | Reservation: a non-admitted thread resolves the outer binding or gets the ordinary undefined-name error; writers are rejected on all threads |
| E2-L4 | Commit atomicity: a concurrent reader never sees a bound name with a non-committed callable or without metadata |
| E2-L5 | Failure by `BaseException` and by an injected commit fault leaves `failed`, no binding, no reservation |
| E2-L6 | Nested transactions on one thread; a second declaration of a reserved name fails at T1 |
| E2-L7 | Source and direct Core IR give identical results for a representative subset |
| E2-L8 | No measurable change to `Env.get` outside a transaction (structural check on the fast path, not a timing test) |

A shared twin of E2-L1 is added only if the portable process primitives can express
a deterministic wait; they currently offer `spawn`, `send`, `process_alive?`,
`process_failed?` and `process_error`, which do not. This is not assumed.

### 10.4 Authorized oracle transition

`spec/eval/model-b-c-stage-closed-rejected.yaml` today expects stdout `before`,
stderr `Error: model-b-not-implemented: declaration evaluation is not available`
and exit 1, with no `requires`. At E2 RED it changes, in a dedicated commit that
records the old and new text, to: `before` printed, `child` not printed (the body is
not run by declaring it), no error, exit 0, and `requires` I and D. Its entry moves
from the guard list to the gated list in `tests/spec/test_model_b_slice_c_red.py`
(53/90 becomes 52/91, total 143 unchanged) and is added to the known-gap entry. Host-local
tests that assert `model-b-not-implemented` for closed forms get the same explicit
transition.

### 10.5 Regressions to preserve

All existing D1/D2a/D2b suites, R20 open-function suites, Slice A/B/C inventories,
annotation and lexical-assignment suites, REPL characterization, module isolation,
Outcome, Flow and protected-value suites, and both regression partitions.

## 11. Delivery

Two implementation PRs, each with its own RED commit first, then an integration PR.

| Slice | Content | Files | RED gate |
|---|---|---|---|
| **E1** | `GeniaClosedFunction`, self frame, whole-group builder, the use check at all §7.2 points, markers, capture exclusion. No source activation: closed source still raises `model-b-not-implemented`. | `callable.py`, `evaluator.py` (builder only), `builtins.py`, `ordinary_completion.py`, new host-local tests | §10.1 |
| **E2** | Transaction T0–T7, reservation and admitted lookup, commit and failure, source activation, the §10.4 transition, shared specs, known-gap entries. | `evaluator.py`, `environment.py`, `spec/`, `tests/`, `spec/known_host_gaps.json` | §10.2, §10.3 |
| **E3** | Truth synchronization (§9 item 7), independent behavioral audit, distillation. | documentation and MCP files only | none (verification) |

E1 is safe to merge alone because nothing in it is reachable from source. If the
maintainer prefers fewer PRs, E1 and E2 may be combined; E3 stays separate.

**Risks.** (1) `Env.get` is on the hottest path; the change must be a no-op outside
a transaction (E2-L8). (2) The self frame adds a scope level; debugger and
inspection output must be pinned (E1-06). (3) A guard point may be missed; E1-02
enumerates entry points and the full regression backstops it. (4) Capability
granularity (§9 item 4). (5) Free-threaded Python: admission uses thread identity
and commit uses one lock hold, so neither depends on the GIL; E2-L4 covers it.

**Complexity: necessary.** One dispatcher is kept. The new parts are one subclass,
one transaction function, one reservation table and one guard helper.

## 12. Decisions required before RED

| Id | Question | Recommendation |
|---|---|---|
| **Q-C1b** | Is `@test` permitted on closed declarations? Are annotation names outside the ten ruled ones rejected at T2? | Exclude `@test` (§5.1). Reject every name outside the five permitted ones at T2, with the same identity, so the permitted set is exhaustive. |
| **DQ-L** | Literal texts | Errors: `closed-function-not-yet-published: <name> is not yet published`; `closed-function-failed-publication: closed function failed publication`; `closed-function-annotation-not-permitted: @<annotation> is not permitted on closed function <name>`. Markers: `<closed-function <name>>` for initializing and committed; `<closed-function failed>` for failed, with no name, as the strict reading of "sanitized opaque marker". |
| **DQ-V** | Order of validation failures | T1 name, then T2 annotation permission, then T3 clause structure (§4). |
| **DQ-S** | Statement value of a closed declaration | The committed callable (§4). |
| **DQ-M** | Is a committed closed `main` selected as the entry function? | Yes, as for an ordinary simple group (§8). |
| **DQ-I** | Introspection of its own name by an annotation during `initializing` | Rejected (§7.1). |
| **DQ-C** | Capability | Reuse existing vocabulary; record the trigger for a future `closed_functions` capability (§9 item 4). |

Only Q-C1b concerns contract semantics. The others are design choices that become
observable and are therefore listed for explicit approval.

## 13. File plan and final check

**New:** this document (KEEP, design record). At E1/E2: host-local test modules and
shared specs listed in §10. **Modified now:** the Model B contract (§4.3 Q-C1
clarification and a stale status phrase) and one pointer line in the portable
design. **Removed:** none.

**Final check (docs/process/02-design.md):** the contract is changed only by the
recorded Q-C1 ruling; no behavior is added beyond the contract and that ruling;
every choice that the contract leaves open is either decided above with its
alternatives or listed in §12; nothing here is described as implemented.
