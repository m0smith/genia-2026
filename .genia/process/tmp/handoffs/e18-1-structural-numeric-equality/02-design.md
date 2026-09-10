# E18-1 Structural and Exact Numeric Equality — Design

ISSUE: #791
PARENT: #789
STATUS: design

Translates `.genia/process/tmp/handoffs/e18-1-structural-numeric-equality/01-contract.md`
into implementation structure. It adds no behavior.

---

## 0. BRANCH CHECK

Branch `issue-791-structural-numeric-equality`; pre-flight and contract exist on it.

---

## 1. PURPOSE

Create the single semantic equality authority the whole release reuses, and move
the `==`/`!=` evaluator dispatch point onto it, without changing any behavior
that later slices own.

---

## 2. ARCHITECTURE

### 2.1 One module

New file `src/genia/equality.py`, exporting one internal operation:

```text
genia_equal(left, right) -> bool
```

There is no public Genia function. `src/genia/evaluator.py` is the only caller
added by this slice. Later slices add callers (`GeniaMap`, `pattern_match`,
`assert_eq`); none of them may reimplement the rules.

Import direction is `equality.py → values.py` (and `sheet.py`) only. `values.py`
must not import `equality.py` at module scope during E18-1, so the new module
cannot create an import cycle. #792 needs `GeniaMap` to consult the key
canonicalizer; that dependency is introduced there, using a function-local
import if required, and is explicitly out of scope here.

### 2.2 Explicit kind dispatch, no host-equality fallback

`genia_equal` dispatches over an explicit, ordered list of recognized Genia
semantic kinds. There is no terminal `return left == right`.

Ordering matters and is fixed:

1. **boolean check first.** In the Python reference host `bool` is a subclass of
   `int`. Testing `isinstance(x, bool)` before any numeric branch is what makes
   `true == 1` false. This ordering is a host-specific defence implementing a
   host-independent rule; the rule is in the contract, the defence is here.
2. **numeric** (int/float, including the exact bridge)
3. **string**, then **symbol** (distinct kinds, never cross-equal)
4. **deferred families** (§2.5) — recognized, but their semantics belong to
   #792/#793
5. **structural kinds** with explicit per-kind field comparison
6. **unclassified terminal** (§2.6)

### 2.3 Numeric comparator

```text
bool  vs bool   -> same truth value
bool  vs any    -> false
int   vs int    -> exact integer equality
float vs float  -> NaN -> false; otherwise mathematical equality
                   (0.0 == -0.0 and matching infinities fall out of this)
int   vs float  -> false unless the float is finite and integral and its exact
                   value equals the integer
```

The int↔float bridge must be exact. The implementation converts the **float** to
an exact rational/integer value and compares against the arbitrary-precision
integer. It must never convert the integer to a float, which would lose
precision for large R17 integers. Concretely: reject non-finite floats, reject
non-integral floats, then compare the float's exact integer value to the integer.

This is decided before generic kind comparison so no host subtype relationship
can collapse the boolean and numeric kinds.

### 2.4 Structural recursion

Each structural kind gets its own branch naming only its semantic fields. No
generic dataclass-field reflection: adding a Python field must not silently
change Genia equality.

| Kind | Compared fields |
|---|---|
| `str` | value |
| `GeniaSymbol` | `name` |
| `list` (Genia List) | length, then each element recursively |
| `GeniaPair` | `head`, `tail` recursively |
| `GeniaOptionSome` | `value`, `context` recursively |
| `GeniaOptionNone` | `reason`, `context` recursively |
| `GeniaOptionErr` | `reason`, `context` recursively |
| `GeniaRepresented` | `facet` (exact string identity), then `value` recursively |
| `GeniaRng` | `state` |
| `GeniaFormat` | `template`, `tag`, `pieces` (recursively; pieces may nest Formats) |
| `GeniaBytes` | `value` byte sequence |
| `GeniaZipEntry` | `name`, then `data` recursively |
| `GeniaSheet` | `row_count`, column count, then each column's name and values pairwise in order, recursively |
| `None` (host absence sentinel) | equal only to `None` |

Outcome constructors are compared by exact runtime constructor kind first, so
`some(x)` never equals `err(x)`.

Sheet columns are positional in the runtime representation and the contract
defines Sheets by *ordered* semantic columns, so comparison is positional, not
set-like.

`None` is included because the reference host still uses bare host `None` as an
internal absence value in places; classifying it explicitly keeps it out of the
unclassified terminal and preserves today's behavior exactly.

Note: the contract's "inert closed ordinary data descriptors" (for example
`http_operation`'s result) are represented in this host as ordinary `GeniaMap`
values, not as distinct classes. They therefore need no branch here; their
equality arrives with map equality in #792. This is recorded so #792 and the
#797 audit do not go looking for a missing descriptor branch.

### 2.5 Deferred families (transitional, removed by their owning issue)

These kinds are **recognized** and routed to one clearly named transitional
helper that preserves exactly today's behavior:

- `GeniaMap` → owned by **#792**
- `GeniaProtected`, `GeniaDeclassificationAuthority`, `GeniaConfigProvider`,
  `GeniaNamedPattern`, `ModuleValue`, `GeniaPythonHandle`, `GeniaRef`,
  `GeniaCell`, `GeniaProcess`, `GeniaSeq`, `GeniaFlow`, `GeniaOutputSink`,
  `GeniaStdinSource`, model/embed/index/retrieve/rerank providers and handles,
  callables and function groups, promises, meta-environments, and lifecycle
  values → owned by **#793**

The helper carries a comment naming the owning issue. Each owning issue deletes
the entries it takes over; after #793 the helper is gone. This is one mechanism
with explicitly deferred branches, not a second parallel equality mechanism, and
it is not a generic host fallback: only these named kinds reach it.

Rationale for deferring rather than implementing now: #791 must not
pre-implement #792/#793 semantics, and it must not regress behavior that those
issues will define. Preserving current behavior behind a named, issue-tagged
branch is the only option that satisfies both.

### 2.6 Unclassified terminal

An object matching no recognized kind is host leakage. It is compared by
**logical identity only** (`left is right`).

It is deliberately *not*:
- an error — the contract says this slice adds no new error surface, and turning
  previously-working comparisons into crashes would be a regression
- host `__eq__` — that is the exact fallback the contract and design forbid

Identity is the most conservative answer that never invents a semantic relation
and never becomes an oracle over a host object's contents. The #797 audit
verifies that no value reachable from Genia source lands here.

### 2.7 Evaluator integration

`src/genia/evaluator.py::eval_binary`, the existing
`if node.op in {"EQEQ", "NE"}` block, is the only changed site:

```text
EQEQ -> genia_equal(left, right)
NE   -> not genia_equal(left, right)
```

Both arms move together; see the pre-flight's `!=` scope note. No parser, AST,
lowering, optimizer, or Core IR change. The `IrBinary` node shape and its
`EQEQ`/`NE` op tags are untouched.

### 2.8 What is explicitly not touched

- `_freeze_map_key` and `GeniaMap` operations (#792)
- `GeniaProtected.__eq__` (#793 removes the payload oracle)
- `pattern_match.py` literal patterns and `_merge_bindings` (#794)
- `assert_eq` in `builtins.py` (#794)
- `hosts/python/*` adapters and the R16 protocol (#795 adds evidence only)

---

## 3. RECURSION AND PURITY

Recursion is ordinary structural recursion bounded by the host's recursion limit,
matching what host equality already did for nested Lists and dataclasses. The
contract states structural values are well-formed, so no cycle detection is
added; identity/deferred leaves terminate traversal before any runtime graph is
entered.

Purity is structural, not enforced at runtime: `genia_equal` reads fields and
calls itself. It never calls a value, never iterates a Seq/Flow, never reads a
Ref/Cell/Process, and performs no IO. `GeniaSeq`/`GeniaFlow`/`GeniaRef` are in
the deferred set precisely so recursion cannot reach their contents. Tests assert
purity observationally (an unconsumed Flow stays unconsumed).

---

## 4. FILE PLAN

New:
- `src/genia/equality.py`
- `spec/eval/r18-equality-*.yaml` (shared cases)
- `tests/unit/test_r18_structural_numeric_equality_791.py`

Modified:
- `src/genia/evaluator.py` (one dispatch block)
- existing tests only where they asserted accidental host coercion

Removed: none.

Temporary handoff artifacts under
`.genia/process/tmp/handoffs/e18-1-structural-numeric-equality/` are subject to
the normal Doc Distillation decision; they are not durable semantic truth.

---

## 5. TEST PLAN INPUT

Tests belong to the TEST phase; targets only.

Reachability finding (measured on this branch): NaN and both infinities **are**
reachable from ordinary Genia source through float overflow and subtraction —
e.g. a large float literal cubed yields `inf`, `0.0 - inf` yields `-inf`, and
`inf - inf` yields `nan`. Shared eval specs can therefore cover the whole numeric
matrix portably, with no host-only escape hatch and no new builtin.

Shared spec targets (`spec/eval/`): boolean/number separation, the int↔float
bridge including a large R17-precision integer, signed zero, infinities, NaN
non-reflexivity, symbol-vs-string kind separation, List/Pair/Outcome/represented
recursion, and `!=` as exact negation of `==`.

Focused pytest targets: kinds not conveniently constructed from source (RNG,
Format, bytes, ZIP entry, Sheet), the unclassified-terminal rule, purity
observations, and direct assertions on `genia_equal`.

Regression risks to watch: existing tests or examples that encode `true == 1`,
Python list-equality's identity shortcut making `[nan] == [nan]` true, and
dataclass equality on represented/Outcome values.

---

## 6. COMPLEXITY CHECK

- [ ] Minimal
- [x] Necessary
- [ ] Over-engineered

One module and one changed dispatch block, replacing an implicit host relation.
No registry, protocol, typeclass, or comparator plug-in is introduced — those are
explicit R18 non-goals.

---

## 7. FINAL CHECK

- matches the E18-1 contract exactly: YES
- no behavior added by design: YES
- no host-specific semantics promoted to contract: YES (the bool-first ordering
  is a host defence implementing a written host-independent rule)
- no parser/Core IR expansion: YES
- no public surface added: YES
- later-slice semantics untouched: YES
- R17 semantics preserved: YES

**GO for the E18-1 failing-test phase.**
