# E18-4 Reconcile Patterns, Assertions, and Equality-like Surfaces — Audit

ISSUE: #794
BRANCH: `issue-794-reconcile-equality-surfaces` (not `main`; matches change)

Audited skeptically. The implementer's inventory is not accepted as evidence that
the inventory was complete; it was re-run after the change.

---

## 1. SUMMARY

Status: **[x] PASS**

Every surface that answers a Genia semantic sameness question now delegates to
the one relation, and a post-change sweep found no remaining site. One contract
clause was found unsatisfiable during implementation and was amended with
justification rather than worked around.

---

## 2. INVENTORY RE-RUN AFTER THE CHANGE

The sweep was repeated on the modified tree rather than trusting the pre-flight.
Remaining `==`/`!=` between value-shaped operands:

- `equality.py` lines 187, 194, 255, 260, 323, 330 — the primitive comparisons
  *inside* the relation itself: int/int, float/float, string, symbol name, byte
  sequence. These are the relation's own leaves, not a second relation.
- `environment.py:167` and `builtins.py:1334` — comparing a requested **name**
  against a module/builtin name. Implementation-local string lookup.

No other site remains. `__eq__` definitions across `src/` are: none on
`GeniaProtected` (removed by #793), `__hash__ = None` guards, and
`GeniaIndexHandle`'s raising pair, which now only guards internal host
comparisons.

Both Sheet duplicate-detection sites (`make_sheet` and `select`) route through
`_freeze_column_name`, so both were fixed by the one delegation rather than
needing separate changes. Verified by reading both call sites.

Prelude helpers (`member?`, `find_opt`, `any?`, and the rest) are written in
Genia source, so their `==` is evaluated by the evaluator and is canonical by
construction. No prelude change was needed, and none was made.

---

## 3. CORE CHECKS

### Contract ↔ implementation

The governing rule is "every listed surface answers as `==` does". The decisive
evidence is the cross-surface agreement test, which runs the same operand pairs
through `==`, duplicate bindings, the meta-evaluator, and `!=` and asserts the
rows are identical — rather than asserting each surface's expected value
separately. A per-surface test suite would still pass if a surface drifted in a
way that happened to match its own expectations; this construction cannot.

Checked that each routing preserves its surrounding behavior:

- `assert_eq` keeps its `NativeTestFailure` shape, message, and
  `expected`/`actual` fields, so native-test CLI output is unchanged. Confirmed
  by the unchanged native-test suites in the full regression.
- literal-pattern mismatch still returns `None`, so clause selection is
  unchanged and a kind difference is a mismatch rather than an error. Tested
  directly with four mismatching kinds.
- `_merge_bindings` only reaches the comparison when a name repeats, so ordinary
  multi-name patterns are untouched.
- only the meta-evaluator's `==`/`!=` changed; `<`, `<=`, `>`, `>=` and the
  arithmetic operators are deliberately untouched, because R18 defines no
  ordering. Verified by reading the operator table.

### The amended contract clause

The contract originally said the legal column-name set is "not widened or
narrowed". Implementation showed that is unsatisfiable together with the
governing rule, so it was amended in the contract file with the reasoning, not
silently violated.

The amendment was challenged during audit on three grounds and survives each:

1. *Is this scope expansion?* No — it is a narrowing forced by the rule the issue
   exists to enforce, within a surface the issue already owns.
2. *Was documented behavior withdrawn?* No. `GENIA_STATE.md` and `GENIA_RULES.md`
   say only that column names must be unique; neither ever specified which value
   kinds are legal.
3. *Was the old behavior actually acceptable?* No. The removed fallback compared
   non-legal names by **host identity**, so two equal-content map column names
   were two distinct columns — itself a disagreement with `==`, and precisely the
   hidden host relation the contract forbids. Keeping it would have left a known
   violation in the release.

The one affected test was re-pointed rather than deleted: it still asserts a
clear rejection, now at Sheet construction.

### New rejection: NaN column names

Follows from reflexivity — a name that does not equal itself cannot denote a
stable column. Tested at top level and nested inside a List name.

### Performance

The routed sites include hot paths (literal patterns, binding merges). Full
regression wall time is 536s against a 533s baseline on `main`, so no meaningful
regression. Recorded because a correctness fix that halved throughput would still
be a problem.

### Protected-data non-interference preserved

`assert_eq` on protected carriers is verified indistinguishable between an
equal-payload pair and a different-payload pair. The Sheet protected column-name
rejection keeps its own message and discloses no payload — checked with a
sentinel.

---

## 4. FUTURE-HOST CHECK

Could a C++ implementer reproduce E18-4 from the written contract plus shared
specs? Yes, and this is the slice that makes the conformance suite able to
*detect* the most likely partial implementation: a host that implements `==`
correctly but leaves literal patterns, duplicate bindings, or assertions on its
own host equality. `r18-surface-agreement-across-equality-like-paths.yaml` fails
exactly that host, and states the failure as three explicit agreement booleans
rather than as a diff a reader must interpret.

The meta-circular evaluator is part of the prelude surface, so its operators are
portable behavior a future host must reproduce; its coverage is included for that
reason.

---

## 5. VALIDATION

- focused + shared 794 evidence: 29 passed
- Sheet suite: 34 passed
- full shared spec suite: `total=664 passed=664 failed=0 invalid=0`
- documentation tests: 205 passed
- `uv run ruff check .`: clean
- full regression `-m "not loopback"`: **2 failed / 4197 passed** — exactly the
  two pre-existing root/`chmod 000` cases, with no other fallout

---

## 6. VERDICT

**PASS.** One obligation remains open for #797: confirm no value reachable from
Genia source lands in the relation's unclassified identity terminal, and re-check
the standing constraint that a future structural value must not be callable.
