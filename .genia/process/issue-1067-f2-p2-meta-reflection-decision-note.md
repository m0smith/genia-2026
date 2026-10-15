# Decision note: metacircular reflection (R10 / R34) — awaiting maintainer ruling

Parent #1067; tracker #1229; debt #1238. Status: **UNRESOLVED — merge blocker.** No
runtime behavior was changed for this item. Documentation is not approval; this note
asks for a ruling and does not make one.

## Question

Contract §16.2 makes `doc`/`meta`/`help` evaluation-bound over the evaluating frame.
§16.4 fixes the base of `empty_env()` at R and says state reaches an evaluation
explicitly through `define`/`extend`. Neither says what raw reflection (`doc`, `meta`,
`help` obtained by looking the name up inside a metacircular frame) does with a name
bound in that frame. `GeniaMetaEnv.lookup` (`src/genia/evaluator.py`) returns the raw
R-bound builtin, which resolves names against R only.

## Discriminating probe (run on this branch, `import genia`)

A documented entry function is `define`d into a fresh `empty_env()`:

```text
@doc "documented in entry"
documented(x) = x
e  = define(empty_env(), quote(f), documented)
e2 = define(e, quote(d), doc)          # `doc` read in the entry: an already-bound reflective value
```

| Expression | Observed | Reading |
|---|---|---|
| `eval(quote(f(1)), e)` | `1` | explicit `define` works for calls |
| `eval(quote(doc("f")), e)` | `none("missing-doc")` | raw `doc` cannot see the meta-frame binding `f` |
| `eval(quote(meta("f")), e)` | `none("missing-meta")` | same, for `meta` |
| `eval(quote(doc("documented")), e)` | `none("missing-doc")` | E-resident name not visible (correct, §16.4) |
| `eval(quote(d("documented")), e2)` | `"documented in entry"` | already-bound `doc` keeps its captured entry scope |
| `eval(quote(d("f")), e2)` | `none("missing-doc")` | …and still cannot see the meta-frame `f` |

The earlier pin (`doc` of integer `1`) cannot discriminate: it is `missing-doc` under
every candidate rule. A documented function (or any value with binding metadata)
distinguishes "name absent" from "name present in the meta frame".

Two distinct things must stay distinct under any ruling:

1. **Raw reflective callable** looked up by name inside the meta frame (`doc` as a free
   name in quoted code): today unbound from the meta frame.
2. **Already-bound reflective value** transferred through `define`: carries the scope
   where its identifier was evaluated (§16.2 "Callable passed to another unit"). This
   is existing ordinary-callable behavior; it is also how an explicit transfer reaches
   E names, and no option below changes it.

## Options

**A. Evaluation-bound reflection within the metacircular frame (recommended).**
`GeniaMetaEnv.lookup` scope-binds a raw reflective builtin to the meta frame using the
existing `Env.scope_bound` / `SCOPE_BINDER_ATTR` mechanism, exactly as the ordinary
evaluator does for identifier reads. Then `doc("f")`/`meta("f")` find explicitly
defined names; `empty_env()` still roots at R, no fallback is added, E stays invisible
unless explicitly passed, and no new syntax or Core IR node appears. Cost: one narrow
change in `GeniaMetaEnv.lookup`; STATE/book wording for eval and a discriminating test.
Rationale: it is the §16.2 rule applied to the one lookup path that §16.2 did not
enumerate, so reflection means the same thing in quoted code as in source.

**B. Separate metacircular reflection model.** Keep raw R-bound reflection in the meta
frame and document it as a deliberate exception. Requires its own approved rule,
precise boundary in STATE/book, and a discriminating pin that asserts the *exception*
(`doc("f")` stays `missing-doc` although `f` is defined). Cost: a second reflection
semantic that differs between quoted and unquoted code, which the core-surface
criteria ("reduce ambiguity", "no second way") disfavor.

I found no conflict in the approved contract that rules A out: §16.2 is broad
("evaluation-bound values over existing lexical capture"), §16.4 constrains only the
base environment, and neither grants reflection a fallback. B is a legitimate choice
only if the maintainer wants quoted code to see R-only reflection.

## Requested ruling

Choose A or B (or another rule) on #1238/#1067. On A: failing discriminating test
first (documented-function and metadata positive controls, plus the two controls above
for raw versus already-bound values), then the minimal `lookup` change, then STATE,
eval book chapter, composability-matrix row and cheatsheet review. On B: document the
boundary and pin the exception with the same positive control. Until then, the
existing behavior is unchanged and unapproved as a contract interpretation.
