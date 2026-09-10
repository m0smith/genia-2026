# E18-1 Structural and Exact Numeric Equality — Pre-flight

ISSUE: #791
PARENT: #789
BLOCKED BY: #790 (E18-0 gate — merged as PR #805)
STATUS: pre-flight

---

## 0. BRANCH

Branch required: YES
Branch type: issue-scoped (repository R18 convention)
Branch slug: `structural-numeric-equality`
Expected branch: `issue-791-structural-numeric-equality`
Base branch: `main` @ `5c00e76`

Rules honored: no work on `main`; branch created before contract; one branch per change.

---

## 1. SCOPE LOCK

### Includes

- one canonical internal Genia equality boundary (`src/genia/equality.py`) owning semantic-kind dispatch
- structural equality for the E18-1 subset of the approved R18 structural family:
  booleans, integers, floats, strings, symbols, Lists, Pairs, `some`/`none`/`err`
  Outcomes, represented values, RNG state values, Format values, byte values,
  ZIP-entry values, Sheets, and inert closed data descriptors
- exact numeric equality matrix approved by E18-0 (bool/int/float separation,
  exact int↔float bridge, signed zero, infinities, NaN)
- routing evaluator `EQEQ`/`NE` through that one boundary
- shared failing eval specs plus focused pytest evidence before implementation

### Excludes

- map structural equality, legal-key relation, key canonicalization — #792
- identity-bearing, opaque-token, and protected-carrier semantics — #793
- `assert_eq`, literal patterns, duplicate bindings, and the wider equality-like
  inventory — #794
- multi-host conformance evidence — #795
- authoritative documentation/release truth sync — #796
- token minting/domain syntax, storage/`Revision`, C++ host, public hash API,
  approximate equality, ordering, user-overloadable `==`

### `!=` note (scope boundary clarification)

The approved R18 contract states `a != b` is *exactly* the logical negation of
`a == b`. In the Python reference host both operators are decided at a single
evaluator dispatch point (`eval_binary`, `node.op in {"EQEQ","NE"}`). Splitting
that one point across two issues would land a state on `main` in which `==` and
`!=` disagree about the same operands, which the contract forbids as an
invariant rather than as a later reconciliation task. E18-1 therefore routes
both arms of that single dispatch point. #794 retains ownership of the *rest* of
the equality-like inventory (`assert_eq`, literal patterns, duplicate bindings,
Pair/Outcome/representation consumers) and of the shared `!=` conformance
evidence across the whole inventory. This is a scope clarification, not an
expansion: no behavior outside the approved R18 numeric/structural matrix is
introduced.

---

## 2. SOURCE OF TRUTH

Authoritative:
- `GENIA_STATE.md` (final authority for currently implemented behavior)
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
- `README.md`
- `AGENTS.md`

Additional relevant:
- `docs/design/r18-portable-value-equality-contract.md` (approved R18 contract; defines
  behavior to implement during R18, not behavior already implemented)
- `.genia/process/tmp/handoffs/r18-portable-value-equality/02-design.md` (E18-0 design)
- `docs/process/run-change.md`, `docs/process/extensions/portability-analysis.md`
- `spec/README.md`, `tools/spec_runner/README.md`
- `docs/strategy/roadmap/r16-r20.md`

Notes: the R18 contract document is explicitly a design aid below
`GENIA_STATE.md`. Nothing in this issue may describe R18 behavior as implemented
release truth; that wording lands in #796.

---

## 3. FEATURE MATURITY

Stage: [x] Partial (E18-1 slice of R18; later slices complete the relation)

Doc wording: no authoritative-doc wording changes land in this issue beyond
what is required to avoid a directly contradictory statement. Release truth is
#796.

---

## 3a. Portability Analysis

Per `docs/process/extensions/portability-analysis.md`. All seven fields resolved; no `TBD`.

1. **Portability zone** — *language semantics (portable contract)*. Genia value
   equality is a host-independent semantic relation. Every conforming host must
   reproduce the approved matrix. The Python reference host's current reliance
   on Python `==` is host leakage being removed, not contract.

2. **Core IR impact** — `none`. No new or changed `Ir*` node family. `IrBinary`
   with `op` `EQEQ`/`NE` already exists and is unchanged in shape; only the
   evaluator's interpretation of that existing node changes. No parser, AST, or
   lowering change.

3. **Capability categories affected** — `none`. Equality is pure: it performs no
   IO, network, configuration/secret acquisition, provider or issuer calls, and
   consumes no Flow/Seq. No required or optional capability in
   `spec/manifest.json` is added, removed, or altered.

4. **Shared spec impact** — new executable shared cases under `spec/eval/`
   (`r18-*.yaml`) covering the structural subset and the exact numeric matrix.
   No new spec category, envelope field, or runner behavior. `spec/manifest.json`
   category/capability data is unchanged.

5. **Python reference host impact** — new internal module `src/genia/equality.py`;
   `src/genia/evaluator.py` `eval_binary` routes `EQEQ`/`NE` through it. No
   public Genia function, builtin, or `import` entry is added. Behavior changes
   observably only where current Python coercive equality contradicted the
   approved contract (notably `true == 1` and `false == 0` becoming `false`).

6. **Host adapter impact** — `none`. `hosts/python/adapter.py` and
   `hosts/python/protocol_adapter.py` are unchanged; the R16 generic host
   protocol surface is untouched. Adapters observe the new behavior only through
   ordinary program execution.

7. **Future host impact** — positive and required. A future host (including the
   scaffolded `hosts/cpp`) implements the written contract matrix plus the shared
   `spec/eval/r18-*.yaml` cases without reading Python source. The explicit
   semantic-kind whitelist and the ban on host-equality fallback exist precisely
   so a non-Python host is not forced to reproduce Python's `bool`-subclass-of-`int`
   accident or Python dict key coercion. No C++ implementation is added here.

---

## 4. CONTRACT vs IMPLEMENTATION

Portable contract (approved by E18-0, implemented by this slice):
- one equality relation; `==` non-overloadable; `!=` its negation
- structural values compare recursively by named semantic contents
- booleans are a distinct kind and never numerically equal to `1`/`0`
- exact int↔float bridge with no lossy coercion
- `0.0 == -0.0`; matching infinities equal; opposite infinities unequal; `NaN != NaN`
- different semantic kinds are unequal (no error)

Python implementation today (to be replaced):
- `eval_binary` returns raw `left == right` / `left != right`
- `bool` is a Python `int` subclass, so `true == 1` currently yields `true`
- `GeniaMap` defines no `__eq__`, so equal-content maps currently compare `false`
- `GeniaProtected.__eq__` compares payloads (a protected-payload oracle)
- dataclass-generated `__eq__` decides structural and identity kinds alike

Not implemented by this slice:
- map equality/key relation (#792), identity/token/protected families (#793),
  wider equality-like surfaces (#794)
- during E18-1 those families reach an explicitly named, comment-marked
  transitional branch that preserves today's behavior and is removed by its
  owning issue. This is one mechanism with deferred branches, not a second,
  parallel equality mechanism, and no permanent generic host fallback.

---

## 5. TEST STRATEGY

Core invariants:
- `==` and `!=` are exact negations for every covered operand pair
- the approved numeric matrix holds exactly
- structural recursion compares named semantic fields only
- kind separation produces `false`, never an error
- equality is pure (no IO, no user code, no Flow/Seq consumption)

Expected behavior: the approved E18-0 matrix, verbatim.

Failure cases: no new error surface is introduced by this slice. Kind mismatch
is `false`.

Test approach:
- shared executable specs `spec/eval/r18-*.yaml` (portable evidence, host-neutral)
- focused pytest over the internal boundary for kinds not conveniently reachable
  from source (RNG, Format, bytes, ZIP entry, Sheet, represented)
- failing evidence committed before implementation, with recorded proof that each
  new case fails for the intended semantic reason

Baseline (measured on `main` @ `5c00e76`, so later "unrelated" claims are provable):
`uv run pytest -n auto -q -m "not loopback"` → 2 failed, 3997 passed. Both
failures are `tests/unit/test_native_test_runner.py` unreadable-file cases that
fail because this environment runs as root and `chmod 000` does not restrict
root. They pre-date this branch.
`uv run pytest -n auto -q -m loopback` → 26 passed.

---

## 6. EXAMPLES

Minimal:
```genia
1 == 1.0      # true
true == 1     # false
0.0 == -0.0   # true
```

Real:
```genia
some([1, 2]) == some([1, 2.0])   # true
quote(x) == "x"                  # false
err("bad") == some("bad")        # false
```

---

## 7. COMPLEXITY CHECK

[ ] Adding complexity
[x] Revealing structure

Justification: the language already claims one equality relation. Today that
claim is implemented by delegating to a host language whose equality rules
differ from the contract. Centralizing the relation removes hidden host behavior
rather than adding a new concept, and it adds no public surface.

---

## 8. CROSS-FILE IMPACT

Files likely to change:
- `src/genia/equality.py` (new)
- `src/genia/evaluator.py` (`eval_binary` EQEQ/NE dispatch only)
- `spec/eval/r18-*.yaml` (new shared cases)
- `tests/unit/test_r18_structural_numeric_equality_791.py` (new)
- existing tests only where they encoded accidental Python coercion as expected
  Genia behavior

Risk of drift: [x] Medium — the relation is broad, but the slice adds no public
surface and authoritative wording is deferred to #796.

---

## 9. DOC DISTILLATION CHECK

Creates process artifacts? [x] YES → Doc Distillation runs in this issue for its
own handoff artifacts; release-wide distillation is #797.

Adds `docs/design` or `docs/architecture` files? [x] NO — the durable R18 design
record `docs/design/r18-portable-value-equality-contract.md` already exists from
E18-0 and is not duplicated.

Doc drift risk: [x] Low for this slice (authoritative sync is #796), provided no
source-of-truth document is left directly contradicting landed behavior.

---

## 10. PHILOSOPHY CHECK

- preserves minimalism? YES — one relation, no new public surface
- avoids hidden behavior? YES — this is the removal of hidden host behavior
- keeps semantics out of host? YES — that is the entire purpose
- aligns with pattern-matching-first? YES — literal patterns and duplicate
  bindings become consistent with `==` (evidence lands in #794)

---

## KILLER WORKFLOW ALIGNMENT

[x] Indirectly

Validated data pipelines compare, deduplicate, key, assert, and pattern-match
values constantly. An equality relation that silently follows the host language
makes validation and diagnostics unreliable across hosts. This slice improves
validation and record-processing correctness without adding pipeline surface.

Reference: `docs/strategy/killer-workflow.md`.

---

## 11. PROMPT PLAN

Preflight → Contract → Design → Test (failing) → Implementation → Docs → Audit →
Distillation.

---

## FINAL GO / NO-GO

Ready to proceed? **YES**

Missing: nothing. #790 is merged (PR #805), which records the E18-0 GO for the
E18-1 failing-test phase.
