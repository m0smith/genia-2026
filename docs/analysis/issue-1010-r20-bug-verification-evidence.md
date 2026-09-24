# R20 Open Functions — Issue #1010 Independent Verification

Status: **NON-AUTHORITATIVE. Investigative evidence only. Does not define
implemented behavior.** `GENIA_STATE.md` remains final authority. This
document is raw verification evidence gathered for issue #1010's F1 gate
(independently executed reproductions of the ten known-evidence claims in
the issue body), preserved here for review. Its findings are synthesized
and classified against the proposed contract in
`docs/design/issue-1010-unified-function-model-contract.md` and the
companion `docs/analysis/issue-1010-f1-decision-report.md`; read those for
the reviewable conclusions. Every reproduction below was executed against
the current interpreter on this branch (based on `main`) — nothing here was
guessed or reconstructed from memory.

Repo: /home/user/genia-2026, branch claude/gracious-johnson-2r0sif (based on main).
All reproductions actually executed via `uv run python -m genia.interpreter <file>.genia`
or via a small driver script calling `genia.builtins.make_global_env()` +
`genia.interpreter.run_source()` for multi-file cases (mirroring
`tests/unit/test_r20_open_functions_cross_module.py`'s own technique).

---

# Item 1: Contribution units lost through aliasing
Classification: NOT REPRODUCED

Repro (multi-file, driver: make_global_env + run_source, files in one tmp dir):
```
# base.genia
open get("mem", key) = "mem:" + key

# ext.genia
import base
extend base.get("db", key) = "db:" + key

# main.genia (two aliases of base in ONE module)
import base as b1
import base as b2
import ext

use get from b1 with ext

[get("mem", "k1"), get("db", "k2"), b1.get("mem", "k3"), b2.get("mem", "k4"), b1 == b2]
```
Observed: `RESULT: ['mem:k1', 'db:k2', 'mem:k3', 'mem:k4', True]`

Also tried `use get from b2 with ext` (opposite alias) in place of `b1` — identical
correct result `['mem:k1', 'db:k2']`.

Evidence: `src/genia/environment.py` `load_module` (lines 226-262) caches modules by
canonical `module_name` string in `root.loaded_modules`, and `Env.get`/`self.env.get(alias)`
just resolves whichever local variable name the alias was bound to, which always points at
the same cached `ModuleValue` object regardless of alias spelling. `src/genia/evaluator.py`
`IrOpenUse` handling (lines 1528-1550) resolves `base_module = self.env.get(node.target_module_alias)`
and finds the export by name on that shared `ModuleValue`, so alias identity never enters
contribution-unit lookup. Matches contract §2.1/§4.2 ("Two aliases of the same cached module
export refer to the same interface... duplicate selection through two aliases of one cached
module is a deterministic error") and `GENIA_STATE.md` lines ~1245-1330 (identity = pair of
canonical module name + export name).

Notes: Aliasing works correctly both for the *base* interface and (per the existing
`test_alias_identity_two_aliases_of_the_same_module_are_one_interface` and
`test_duplicate_selection_through_two_aliases_of_one_cached_module_is_rejected` tests) for
*contribution* modules. No loss or duplication observed in any alias combination tried.

---

# Item 2: Non-contiguous `extend` runs lose contribution units
Classification: CONFIRMED CONTRACT VIOLATION

Repro:
```
# base.genia
open get("mem", key) = "mem:" + key

# ext.genia  (two non-contiguous extend blocks for the SAME target)
import base
extend base.get("db", key) = "db:" + key

value = 1

extend base.get("cache", key) = "cache:" + key

# main.genia
import base
import ext

use get from base with ext

[get("mem", "k1"), get("db", "k2"), get("cache", "k3")]
```
Observed:
```
genia.callable.OpenFunctionNoMatchingCaseError: No matching case for function get/2
with arguments ["db", "k2"]
```
Isolated confirmation that `ext.genia` alone loads without ANY error/diagnostic
(`run_source` on ext.genia directly returns `<open contribution <entry> -> get>`,
i.e. it silently succeeds), and that `get("cache", "k3")` (the *second*, post-interruption
extend block) dispatches fine as `'cache:k3'`, while `get("db", "k2")` (the *first*,
pre-interruption extend block) is gone entirely — not merged, not rejected, just dropped.

Evidence:
- Docs requirement: `docs/design/r20-open-functions-syntax-ir-design.md:265-276`
  ("**Contiguity restriction**... the parser only merges clauses for one open interface
  (or one extend target) when they form a contiguous run of top-level statements...
  writing a later bare `name(pattern...) = body` for a name... whose run was already closed
  is a rejected redeclaration-like error, not a silent second interface.") This section
  explicitly covers "or one extend target", so `extend` is in scope.
- Actual implementation: `src/genia/evaluator.py:1513-1527` (`IrOpenContribution` handling)
  builds a **fixed, non-unique export key**:
  `export_name = f"__open_contribution__{node.target_module_alias}__{node.target_name}"`
  and does `self.env.set(export_name, unit, assignable=False)`. Every `extend base.get(...)`
  block in the same module — contiguous or not — writes to this *same* dict key.
  `Env.set` (`src/genia/environment.py:78-95`) is an unconditional overwrite:
  `self.values[name] = value` with **no duplicate/redeclaration check at all**. So a second,
  non-contiguous `extend base.get(...)` block silently clobbers the first
  `GeniaOpenContributionUnit` object; only the last one is ever visible under that export
  name, and `use ... with ext` only ever finds the last one via
  `_find_open_contribution_unit` (`src/genia/evaluator.py:1270-1279`), which just scans
  `module_value.exports.values()` for a `GeniaOpenContributionUnit` with a matching
  `target_interface_key` — there is exactly one such export left to find.
- Contrast: the equivalent *local* `open`/repeated-clause interleaving case IS correctly
  rejected — `open f(0) = "zero"` / unrelated statement / `f(1) = "one"` raises
  `open-function-redeclaration: 'f' is already declared open...` at parse time
  (parser tracks `self._open_names`, `src/genia/parser.py:616-628`). So the contiguity
  guard exists and works for local `open` clauses but was never implemented for `extend`
  contribution clauses.

Notes: This is a genuine silent-data-loss bug, worse than the "silent second interface"
the design doc warns against — it is silent *replacement*, so the first contribution unit's
clauses vanish with zero diagnostic. `GENIA_STATE.md` (section 4.7) only explicitly restates
the contiguity requirement for local `open`/repeated clauses; for `extend` it says "Repeated
`extend` statements for the same target in the same module accumulate into one contribution
unit, in source order" without repeating the contiguity caveat verbatim — but the design doc
it references states the restriction covers `extend` targets too, so this is a genuine
drift from the approved design, not merely an ambiguous doc gap.

---

# Item 3: Alias rebinding loses contribution units
Classification: NOT REPRODUCED

Repro A (rebind alias to a DIFFERENT module before `use`):
```
import base as b
import other   # other.genia declares its own open get("mem", key) = ...
import ext     # extend base.get("db", key) = ...

b = other

use get from b with ext
```
Observed: `OpenFunctionIncompatibleContributionError: open-function-incompatible-contribution:
expected a contribution targeting ('other', 'get'), got 'ext'` — correctly rejected, because
`use` resolves `self.env.get(node.target_module_alias)` at the moment it executes (ordinary
lexical/mutable-binding semantics), and `ext`'s contribution genuinely targets `base.get`,
not `other.get`. Deterministic, not silent.

Repro B (rebind alias AFTER `use` has already linked):
```
import base as b
import ext
use get from b with ext
result1 = get("db", "k1")
b = 42
result1
```
Observed: `RESULT: 'db:k1'` — the already-linked view is unaffected by the later rebinding,
confirming immutability of the linked view per contract §4.2 ("The selected set is immutable
after linking").

Evidence: `src/genia/evaluator.py:1528-1550` (`IrOpenUse`) resolves `target_module_alias`
and every `contribution_module_aliases` entry via `self.env.get(...)` once, at the moment the
`use` statement executes, and stores the resulting `GeniaLinkedOpenFunction` as an ordinary
immutable value bound to `node.local_name`; nothing about it re-reads the alias later.

Notes: Rebinding an alias is ordinary Genia mutable-variable behavior (R20 adds nothing
here); behavior observed is exactly what the contract requires (declarative, once-evaluated,
immutable-after-linking). No loss or misattribution found in either direction tested.

---

# Item 4: Internal contribution bindings leak through exports
Classification: CONFIRMED CONTRACT VIOLATION

Repro:
```
# base.genia
open get("mem", key) = "mem:" + key

# ext.genia
import base
extend base.get("db", key) = "db:" + key

# main.genia
import base
import ext

ext.__open_contribution__base__get
```
Observed: `RESULT: <open contribution ext -> get>` — the importer can directly read the
internal `GeniaOpenContributionUnit` object as an ordinary named member of `ext`, with no
`use` statement at all.

Evidence:
- Contract requirement: `docs/design/r20-open-functions-contract.md` §4.1 ("An ordinary
  import only binds its module value and evaluates that module under the existing module
  rules. It does **not** select any contribution exported by that module. A consumer must
  perform a separate, explicit contribution-use operation...") and §4.2 ("Private/non-exported
  contribution metadata is inaccessible.").
- Implementation: `src/genia/evaluator.py:1513-1527` binds the contribution unit via
  `self.env.set(export_name, unit, assignable=False)` where `export_name =
  f"__open_contribution__{node.target_module_alias}__{node.target_name}"` — an ordinary
  module-level binding. `src/genia/environment.py:257` (`load_module`) does
  `exports = dict(module_env.values)`, i.e. it exports **every** top-level binding in the
  module's environment, with no export/private distinction anywhere in the codebase (there
  is no leading-underscore-means-private convention enforced at the `ModuleValue`/`get_export`
  layer — `ModuleValue.get_export`, `src/genia/values.py:459-462`, does a plain dict lookup).
  So the "internal" dunder-prefixed name is fully name-mangled-looking but not actually
  hidden: it is a regular exported member, reachable by ordinary attribute access
  (`ext.__open_contribution__base__get`) exactly like any user-defined top-level binding.

Notes: The `use` statement's own gating (checking `isinstance(target, GeniaOpenContributionUnit)`
with a matching `target_interface_key`) is a legitimate additional check, but it does not
prevent the underlying object from being visible through ordinary member access, so the
contract's "inaccessible" guarantee for private contribution metadata does not hold in this
implementation. This also means a Genia program can introspect/pattern-match/pass around the
raw `GeniaOpenContributionUnit` host object outside of any sanctioned R20 operation, and — combined
with item 2 — the same fixed export-name key is exactly the mechanism that silently drops
non-contiguous contribution clauses.

---

# Item 5: Mutual/cross-function TCO failures for open functions
Classification: CONFIRMED CONTRACT VIOLATION

Repro (self-recursion, single open interface — sanity baseline matching the audit):
```genia
open count(n, 0) = n
count(n, k) = count(n + 1, k - 1)

count(0, 200000)
```
Observed: `200000` — no stack overflow. Matches the audit's own claim; self-recursion TCO works.

Repro (mutual recursion between TWO SEPARATE open interfaces, low recursion limit,
mirroring `tests/unit/test_tco.py::test_mutual_tail_recursion_uses_constant_python_stack`
exactly, but with `open`):
```genia
open even(0) = true
even(n) = odd(n - 1)

open odd(0) = false
odd(n) = even(n - 1)

even(1000)
```
run under `sys.setrecursionlimit(300)` (identical harness/limit to the passing ordinary-function
test in `tests/unit/test_tco.py`).

Observed:
```
RecursionError: maximum recursion depth exceeded
```
(traceback bottoms out inside `genia.equality._numeric_equal`, called from ordinary pattern
matching deep inside nested Python call frames — i.e. genuine Python-stack growth, not a
Genia-level error.)

For comparison, the **existing, already-passing** ordinary-function equivalent
(`tests/unit/test_tco.py::test_mutual_tail_recursion_uses_constant_python_stack`, lines 36-46)
runs the *same shape* of mutual recursion (`even`/`odd`, 1000 iterations, recursion limit 300)
and returns `True` with **zero** Python stack growth.

Also reproduced directly via the CLI at higher iteration count:
```genia
open is_even(0) = true
is_even(n) = is_odd(n - 1)

open is_odd(0) = false
is_odd(n) = is_even(n - 1)

is_even(400000)
```
Observed: `Error: maximum recursion depth exceeded`.

Evidence:
- Contract requirement: `GENIA_STATE.md` section 4.7 ("Existing fixed-over-varargs
  precedence, first-match order, guards, named patterns, and automatic Outcome/`none`
  propagation are preserved by reusing the existing pattern engine
  (`match_lambda_pattern`) unchanged" — the surrounding prose and the audit both claim
  full reuse of the *existing TCO machinery*), and `docs/analysis/r20-release-truth-audit.md`
  §3/§5 explicitly claims "TCO preserved through open dispatch (no stack overflow)" and "the
  fact `invoke_callable`'s existing dispatch order... required zero changes;
  `GeniaOpenFunction`/`GeniaLinkedOpenFunction` fall through to the existing generic-callable
  branch unmodified" — presented as evidence TCO is fully preserved, but the audit's own
  reproduction (§3) only exercises **self**-recursion, never cross-function/mutual recursion.
- Root cause in implementation: `src/genia/callable.py`:
  - `GeniaOpenFunction.__call__` (lines 683-692) and `GeniaLinkedOpenFunction.__call__`
    (lines 717-726) each implement their **own private trampoline loop**, but the loop only
    flattens the *self*-recursive case: `if result.fn is self: current_args = result.args;
    continue`. Any other `TailCall` target — including another `GeniaOpenFunction` — falls to
    `return eval_with_tco(result.fn, result.args)`.
  - `eval_with_tco` (lines 298-340) is the *shared, flat* trampoline used by ordinary
    `GeniaFunction`s: its own `while True` loop natively handles a `GeniaFunction` tail-calling
    another `GeniaFunction` without any nested Python call, because both live inside the same
    `if isinstance(current_fn, GeniaFunction): ...` branch of the *same* loop iteration.
  - But `GeniaOpenFunction`/`GeniaLinkedOpenFunction` are **not** `GeniaFunction` instances, so
    when `eval_with_tco`'s loop reaches one, it falls to the generic `else: result =
    current_fn(*current_args)` branch (line 334) — a literal, un-trampolined Python call into
    that object's own `__call__`. When two different open functions tail-call each other
    repeatedly, each hand-off is: `A.__call__` loop -> `eval_with_tco(B, ...)` (new Python
    frame) -> `B(*args)` i.e. `B.__call__` (new Python frame) -> ... -> `eval_with_tco(A, ...)`
    (new Python frame) -> `A(*args)` (new Python frame) -> ... This nests two new Python
    stack frames per mutual round-trip with no bound, unlike ordinary `GeniaFunction`
    mutual recursion which stays inside one flat `while True` loop forever.

Notes: This is the strongest, most clear-cut confirmed bug of the ten. It directly
contradicts both `GENIA_STATE.md`'s and the audit's TCO-preservation claims for the
cross-function case; the audit's own limitation is that it tested only self-recursion
("The truth audit only tested single-function self-recursion" — exactly as issue #1010
suspected). A `use`-linked view tail-calling a *different* linked view (or its own base)
would hit the identical failure mode for the same reason.

---

# Item 6: Grouped-header binders dropped
Classification: INTENTIONAL DIFFERENCE (documented limitation) for the header-rejection
half; CONTRACT UNCLEAR (undocumented but defensible edge behavior) for the
binder-discard-on-flattening half.

Repro A (non-plain-identifier header + grouped case body):
```genia
open f({x, y}) = ({x: 0, y: 0}) -> 999 | ({x, y}) -> x + y

f({x: 1, y: 2})
```
Observed: clean parse-time rejection —
`Error: open clause with a grouped case body requires plain identifier parameters
(dispatch belongs in the case arms) at 5`
— matches `GENIA_STATE.md`'s documented limitation exactly ("a grouped case-with-pipe body
is auto-flattened only when the header pattern is plain identifiers... other combinations...
are rejected rather than given ad hoc semantics") and the audit's claim that this fixup
(commit `4179793`) avoids a "raw-repr-leaking fallback". Confirmed: this *is* a clean
rejection, not a crash or silent misbehavior.

Repro B (plain-identifier header, but arm patterns use DIFFERENT names than the header):
```genia
open f(a, b) = (x, 0) -> a | (x, y) -> a + b + x + y

[f(10, 0), f(10, 5)]
```
Observed: `Error: Undefined name: a` (at call time, inside the flattened `(x, 0) -> a` arm).

Evidence: `src/genia/parser.py:601-611` (`_parse_open_clause_list`): when the header is
"trivial" (plain identifiers, checked by `_open_header_is_trivial`, lines 553-565) and the
body is a grouped case expression, the flattening is:
```python
return [CaseClause(arm.pattern, arm.guard, arm.result, span=arm.span) for arm in case_expr.clauses]
```
i.e. **only** each arm's own `pattern`/`guard`/`result` survive; the header's own binder names
(`a`, `b`) are discarded entirely and never merged into the arm's scope. This is exactly what
makes the required equivalence example work (`open gcd(a, b) = (a, 0) -> a | (a, b) ->
gcd(b, a % b)` — the arms happen to *reuse* the header's own names `a`/`b`, so nothing is lost
in that specific case), but it means a header binder is silently unavailable in any arm whose
own pattern uses a different name for the same position.

Notes: This is not the "silently wrong binding" issue item 6 worried about — it fails loudly
with a normal `Undefined name` runtime error, and matches the literal, documented flattening
mechanism ("flattened at parse time into one clause per arm, so grouped and repeated local
clause syntax normalize to an identical ordered clause list", `GENIA_STATE.md` section 4.7).
It is undocumented as its own edge case, but it is a natural and honestly-implemented
consequence of the documented design, not a distinct bug.

---

# Item 7: Open-function docstrings parse incorrectly
Classification: CONFIRMED CONTRACT VIOLATION

Repro (ordinary-function docstring convention, `GENIA_STATE.md:978-987`, applied to `open`):
```genia
open f(x) = "Doc for f." x + 1

f(1)
```
Observed: `Error: Undefined name: x`

AST-level confirmation (parsed directly via `genia.parser.Parser`/`genia.lexer.lex`):
```
OpenFuncDef(name='f', clauses=[CaseClause(pattern=TuplePattern(items=[Var('x')]),
  guard=None, result=String(value='Doc for f.'), ...)], docstring=None, ...)
ExprStmt(expr=Binary(left=Var(name='x'), op='PLUS', right=Number(value=1)))
ExprStmt(expr=Call(fn=Var(name='f'), args=[Number(value=1)]))
```
i.e. the parser (a) treats the leading string literal as the **entire clause body** (not a
docstring at all — the clause's actual return value is just the string), (b) silently splits
the remainder (` x + 1`) off into a **separate, orphaned top-level statement** with no
statement separator required, referencing `x`, which is unbound at module scope — hence the
runtime "Undefined name: x" when the program executes that orphaned statement (before `f(1)`
is even called), and (c) hardcodes `docstring=None` on the `OpenFuncDef` node regardless.

Evidence:
- Documented convention: `GENIA_STATE.md:978-987` ("named function definitions may include
  an optional leading docstring string literal after `=`... function bodies may still use the
  ordinary parenthesized case-expression style after a docstring") and `GENIA_STATE.md:1350`
  ("`IrOpenFuncDef(name, clauses, docstring, annotations)`" — implying `open` funcdefs carry a
  meaningful `docstring` field, consistent with this convention being available to them; the
  only disclosed gap is "`@doc`/`@meta`-style annotation attachment is not wired... interface
  metadata beyond the optional docstring position is a follow-up" (`GENIA_STATE.md`, R20
  known-limitations bullet) — this phrasing ("beyond the optional docstring position")
  affirmatively implies the leading-docstring-literal position itself *does* work for `open`.
- Root cause: ordinary `FuncDef` parsing (`src/genia/parser.py:409-417`, inside
  `try_parse_bindable_toplevel`) explicitly special-cases this: `if self.at("STRING"): ...
  if self.at_expr_start(): docstring = candidate ... body = parse_function_body_after_intro(...)`.
  `_parse_open_clause_list` (`src/genia/parser.py:567-614`), used for `open`/repeated/`extend`
  clauses, has **no equivalent check** — it goes straight from `self.eat("ASSIGN")` to
  `body = self.parse_function_body_after_intro(fixed_arity)` (lines 591-593), so a leading
  string literal is parsed as an ordinary expression and immediately becomes the whole clause
  body. `_parse_open_pattern_clause` (`src/genia/parser.py:616-628`) then hardcodes
  `OpenFuncDef(name, clauses, None, span=span)` — the `docstring` constructor argument is
  always `None`, confirming the field is dead code for the current grammar (there is no
  parser path that ever produces a non-`None` value for it).

Notes: The `@doc "..." open f(0)=1` prefix-annotation case (which the audit's fixup commit
`4179793` addressed) IS now a clean rejection ("Prefix annotations are not supported on
open/extend/use declarations in this release") — reproduced and confirmed working as claimed.
But the *other*, pre-existing Genia docstring convention (inline leading string literal) was
never wired for `open` at all, and unlike the annotation case it fails **silently** into a
corrupted two-statement parse rather than a clean rejection — this is the "raw-repr-leaking
fallback"-style problem the audit's fixup was supposed to eliminate, just via a different code
path the audit did not test.

---

# Item 8: Module environments see entry-program bindings
Classification: CONFIRMED IMPLEMENTATION DRIFT

Repro:
```genia
# mod.genia
uses_entry_var() = entry_only_var + 1

# main.genia (the CLI entry file)
entry_only_var = 100
import mod

mod.uses_entry_var()
```
Observed: `RESULT: 101` — `mod.genia` never defines `entry_only_var`, yet it resolves to the
entry program's own top-level binding.

Evidence: `src/genia/environment.py`:
- `Env.root()` (lines 59-63) walks `self.parent` up to the topmost environment.
- `load_module` (lines 226-262): `module_env = Env(root, rebind_parent=False)` — every loaded
  module's environment is created with **the calling program's own root environment as its
  lexical parent**. For a program run via the CLI/`run_source` entry point, that root *is*
  the same environment the entry file's own top-level statements were evaluated into (the one
  `make_global_env()` returned), so `entry_only_var = 100` at entry scope becomes visible via
  ordinary parent-chain lookup (`Env.get`, lines 65-...) inside every subsequently imported
  module, regardless of which module requested the import or how deep the import graph is.

This is a general module-isolation defect, not specific to R20 — R20 code does not touch this
path — but the task explicitly asked it be checked because R20's own module/contribution
machinery depends on the module-scoping model being sound. `GENIA_STATE.md:977` only makes a
one-directional isolation claim ("module evaluation uses its own module environment, so module
top-level assignment does not rebind names in the importing root environment"); it does not
explicitly claim the reverse (that a module cannot *read* entry-only names), but "uses its own
module environment" plainly implies isolation, and the observed behavior — a module's result
silently depending on unrelated global state defined only in whatever program happens to import
it — contradicts the ordinary expectation of a "module environment" and is not disclosed
anywhere as intended behavior.

Notes: This also means R20's `use`/`extend` resolution, which walks `self.env.get(alias)` and
relies on lexical scoping being sound, inherits this same leak surface (e.g. an entry program
could accidentally shadow an imported module's alias name and have that leak into every module
it transitively imports), though no R20-specific exploit of this was constructed here.

---

# Item 9: Ordinary/open fixed+varargs differences
Classification: CONFIRMED IMPLEMENTATION DRIFT (a genuine, reproducible divergence — not
about fixed-over-varargs precedence itself, which is preserved, but about a varargs-vs-varargs
disambiguation shortcut that only ordinary functions have)

Repro (open):
```genia
open g(..rest) = rest
g(a, ..rest) = [a, ..rest]

[g(), g(1), g(1, 2, 3)]
```
Observed: `Error: open-function-varargs-ambiguity: g/1 matches more than one varargs shape
[('varargs', 0), ('varargs', 1)] contributed by ['base']` — fails on the **second** list
element, `g(1)` (i.e. `g()` alone succeeds first).

Repro (ordinary, identical clause shapes):
```genia
g(..rest) = rest
g(a, ..rest) = [a, ..rest]

[g(), g(1), g(1, 2, 3)]
```
Observed: `Error: Ambiguous function resolution: g/3. Matching varargs: g/0+, g/1+` — fails
only on the **third** element, `g(1, 2, 3)`; `g()` and `g(1)` both succeed silently.

Evidence: `src/genia/callable.py`:
- Ordinary dispatch (`invoke_callable`, `_resolve_target`, lines ~1129-1150): `functions:
  dict[int, GeniaFunction]` is keyed by each clause's **fixed-param count** (its `arity`).
  `_resolve_target` first tries `exact = functions.get(call_arity)` and returns it
  **immediately, with no ambiguity check at all**, whenever the call arity exactly equals some
  varargs clause's own fixed-param count — even though a different, lower-minimum varargs
  clause would also structurally match. Only when `call_arity` matches **no** clause's exact
  fixed-param count does it fall through to the `vararg_matches` list-and-ambiguity check
  (lines ~1129-1148).
- Open dispatch (`_dispatch_open`, lines 596-641): computes `varargs_eligible` uniformly from
  every clause whose `minimum <= n` (no special-case for `n` equal to a clause's *own*
  fixed-param count) and raises `OpenFunctionVarargsAmbiguityError` whenever `len(minimums) >
  1`, exactly per contract §5.1 ("If more than one distinct varargs minimum is eligible, fail
  with varargs-shape ambiguity; do not choose the largest minimum").
- Net effect: at call arity `n=1` here, open correctly (per contract §5.1, read literally)
  treats `{0, 1}` as two eligible minimums and rejects; ordinary silently short-circuits to
  the `arity==1` clause via its dict-exact-match shortcut and never even computes the
  ambiguity. `GENIA_STATE.md` section 4.7 claims dispatch "preserves current fixed-over-varargs
  precedence"; that specific claim (fixed clauses beating varargs) does hold, but ordinary and
  open genuinely disagree on varargs-vs-varargs resolution for this shape, which is a
  different, undocumented divergence.

Notes: This is a real, reproducible difference, not a hypothetical — both are internally
"correct" relative to their own separately-implemented algorithms, but they diverge in output
for the exact same clause set at the exact same call arity, contradicting the general
"identical dispatch" framing used throughout `GENIA_STATE.md` section 4.7 and the design doc.

---

# Item 10: Ordinary/open Outcome/`none` differences
Classification: NOT REPRODUCED for runtime Outcome/none semantics (identical); a related but
distinct PARSER-surface asymmetry was found and is reported separately (not itself an Outcome
semantic bug).

Repro (implicit `none` short-circuit):
```genia
open f(x) = x + 1     # vs ordinary  f(x) = x + 1
f(none("missing"))
```
Observed: identical for both — `none("missing")`.

Repro (explicit `some`/`none`/`err` handling, open):
```genia
open handle(some(x)) = x + 1
handle(none(r)) = "missing:" + r
handle(err(r)) = "error:" + r

[handle(some(5)), handle(none("nope")), handle(err("bad"))]
```
Observed: `[6, "missing:nope", "error:bad"]` — correct.

Repro (the literal ordinary-function equivalent, same header shape):
```genia
handle(some(x)) = x + 1
handle(none(r)) = "missing:" + r
handle(err(r)) = "error:" + r
```
Observed: `Error: Expected RPAREN, got LPAREN at 10` — **parse failure**. Ordinary top-level
repeated-clause headers do not accept constructor sub-patterns like `err(r)` directly (even
though a bare literal like `0` works fine, as in the `gcd` example). The semantically
equivalent ordinary form requires the case-body style instead:
```genia
handle(x) = (some(v)) -> v + 1 | (none(r)) -> "missing:" + r | (err(r)) -> "error:" + r
```
which, once used, produces the identical `[6, "missing:nope", "error:bad"]` result.

Evidence: `_parse_open_clause_list` (`src/genia/parser.py:567-579`) parses the header via
`self.parse_lambda_parameter_pattern()` — the **full** existing pattern grammar (same one
lambdas and case arms use), matching `GENIA_STATE.md` section 4.7's own text ("`<pattern>`
reuses the existing lambda-parameter pattern grammar verbatim... `some(...)`/`err(...)`").
Ordinary top-level repeated `FuncDef` clause headers go through a different, more restricted
parameter-list parser (`try_parse_function_header`, not shown in full here) that does not
accept constructor-application sub-patterns directly in a **repeated-clause** header position,
requiring the case-body form instead for that shape.

Notes: Once past parsing, runtime Outcome/`none` propagation is byte-for-byte identical between
open and ordinary functions (both go through the same `match_lambda_pattern`,
`_callable_explicitly_handles_none`/`_normalize_absence` machinery in
`src/genia/callable.py`/`src/genia/evaluator.py`, and open functions are not special-cased
anywhere in that code). The only real difference found is a **syntax-surface** asymmetry (open
clause headers accept a strictly larger pattern grammar directly at top level than ordinary
repeated clauses do) — which is exactly what the contract intends for `open`
("reuses the existing lambda-parameter pattern grammar verbatim") and is not itself a
contract violation; it is simply an asymmetry between `open` and pre-existing ordinary
top-level repeated-clause syntax that is easy to mistake for an Outcome-handling difference
until you spell the ordinary equivalent correctly.

---

# Summary

| Item | Classification |
|---|---|
| 1. Contribution units lost through aliasing | NOT REPRODUCED |
| 2. Non-contiguous `extend` runs lose contribution units | CONFIRMED CONTRACT VIOLATION |
| 3. Alias rebinding loses contribution units | NOT REPRODUCED |
| 4. Internal contribution bindings leak through exports | CONFIRMED CONTRACT VIOLATION |
| 5. Mutual/cross-function TCO failures for open functions | CONFIRMED CONTRACT VIOLATION |
| 6. Grouped-header binders dropped | INTENTIONAL DIFFERENCE / CONTRACT UNCLEAR (edge case) |
| 7. Open-function docstrings parse incorrectly | CONFIRMED CONTRACT VIOLATION |
| 8. Module environments see entry-program bindings | CONFIRMED IMPLEMENTATION DRIFT |
| 9. Ordinary/open fixed+varargs differences | CONFIRMED IMPLEMENTATION DRIFT |
| 10. Ordinary/open Outcome/`none` differences | NOT REPRODUCED (runtime semantics identical; unrelated parser-surface asymmetry found) |

Five of the ten items reproduce genuine, previously undisclosed problems (items 2, 4, 5, 7 as
outright contract violations; item 8 and 9 as implementation drift). Item 5 (mutual-recursion
TCO) is the most serious: the release-truth audit's PASS verdict rests on a TCO reproduction
that only exercises self-recursion, and mutual recursion between two open interfaces overflows
the Python stack at the same iteration counts where the equivalent ordinary-function case is
already proven (by an existing, passing test) to run in constant stack space. Items 2 and 4
share a root cause (the fixed, non-unique `__open_contribution__<alias>__<name>` export key
with no duplicate/privacy guard), so a single implementation fix addresses both.
