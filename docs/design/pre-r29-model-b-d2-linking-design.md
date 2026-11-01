# Model B D2: ordinary-base `extend` / `use` linking (D2a + D2b)

Status: **PROPOSED DESIGN — NOT IMPLEMENTED.** No D2 code, test, spec or
documentation change of implemented behavior exists. Phase: DESIGN for #1250,
authorized by the maintainer decisions in
[comment 6561255519](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6561255519)
(Q1, Q2, A, Q3, B, Q4). `GENIA_STATE.md` remains the only authority on implemented
behavior; until D2 GREEN is accepted, ordinary `extend`/`use` is rejected exactly as
STATE describes. Governing sources: the maintainer-approved
[Model B contract](pre-r29-default-open-and-immutable-binding-contract-DRAFT.md)
(§§2.1–2.3, 5.3–5.4), the [portable design](pre-r29-default-open-and-immutable-binding-design.md)
(§§5.1–5.4, 7–10, 13.4), the [D1 design](pre-r29-model-b-d1-completion-design.md), and the
[D2 preflight](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6560789663).
Baseline: `main@5f5fa28d727f52abb8608bb1c5f929343b9de456`.

## 1. Scope, decisions and phase map

**In scope:** link `extend` contributions and an explicit `use` selection onto an
exported, original-module-owned **ordinary** base interface G (a default-open
`GeniaFunctionGroup` that has a D1 completion witness); a frozen mixed-record view;
cross-unit validation; deterministic dispatch/diagnostics; atomic publication;
B1 three-channel view metadata; unchanged explicit-R20 `open` behavior except the
declared deltas (§8).
**Out of scope:** closed `=:` publication (Slice E), R29, any C++ parity claim, new
syntax, Core IR family/version, capability names or wire format, public snapshot API,
import-triggered activation, `#1250/#1251` closure, the seven historical timeouts.

| Decision | Design realization (section) |
|---|---|
| Q1 validation for **all** views incl. explicit `open` bases | one shared pure validator, activated for both base kinds in D2b (§5, §8 Δ2) |
| Q2 distinct normalized `open-function-*` identities | `open-function-cross-unit-duplicate-clause`, `open-function-shape-conflict` (§6) |
| A consistent view dispatch categories | existing `open-function-*` classes for every view regardless of record source (§6.3) |
| Q3 authority keyed by exact G; `(module,name)` diagnostics only | exact-G contribution store for ordinary targets; explicit R20 table unchanged (§3.3, §9) |
| B canonical contributor order by canonical module identity | single sort key and tiebreak (§4) |
| Q4 staging | D2a private machinery, no activation; D2b activation + metadata + conformance (§2) |

## 2. Slices and the exact activation boundary

**D2a — private link machinery (no public activation, no behavior claim).**
Adds, in a new private module and a small number of private seams: (a) the typed D1
completion lookup; (b) `FrozenOrdinaryBase`, a view-owned immutable base; (c) the pure
link validator and canonical unit ordering; (d) the mixed-record candidate adapter in
the shared dispatch engine; (e) awareness (`none`/`some`) for mixed strata; (f) the
single-lock publication method `Env.publish_view`; (g) the **inert** contribution-store
fields (`GeniaOpenContributionUnit.target`, `Env.ordinary_contributions`,
`ModuleValue._ordinary_contributions`), added in D2a so D2a tests can construct ordinary
units, but never populated by the evaluator until D2b. Nothing evaluates it from Genia
source: `IrOpenContribution` and `IrOpenUse` keep their current branches
(`evaluator.py`), so ordinary targets still raise `open-function-target-not-open`
and explicit `use` is byte-for-byte unchanged (including the call-time ambiguity
behavior that D2b later replaces). Evidence is host-local tests that construct modules
through the real loader, build contribution units directly, and drive the private
entry `link_view(...)`. D2a updates **no** STATE/RULES/README/REPL claim except one
accurate sentence in STATE §3 beside the D1 paragraph ("private link machinery exists
but is unreachable from source"), added only at D2a GREEN.

**D2b — activation boundary (the only behavior-changing slice).** Exactly two
evaluator edits, both inside the existing `IrOpenContribution` / `IrOpenUse` branches:
1. `extend`: if the target export is a `GeniaFunctionGroup` with a completion witness
   (§3.1) store the unit in the exact-G store (§3.3); every other non-`GeniaOpenFunction`
   target still raises the existing `open-function-target-not-open`.
2. `use`: route both base kinds through the §5 transaction (resolution → validation →
   view → checked write). Explicit bases gain Q1 validation and canonical unit order.
Plus: metadata channels (§7), shared R16 specs and the declared oracle changes (§8),
known-gap and documentation synchronization (§11). No D2b edit is permitted outside
these two branches, reflection (`builtins.py`), and the registered fields below.

Dependencies: D2b requires D2a GREEN and accepted. Each slice has its own RED commit
(before any production code), implementation, maintainability review, independent
behavioral audit and docs/truth synchronization.

## 3. Data and interface design

### 3.1 D1 projection lookup (D2a)
New private function in `ordinary_completion.py`:
`completion_for(module_value, value) -> _Projection | None` returns the projection whose
associated group `is` `value` (exact identity, scan of `ModuleValue._ordinary_completions`;
linear but bounded by exported ordinary callables). It never uses names, equality, hashing,
`repr` or user code. `None` means "no authority" (closed callable, lambda, builtin,
host callable, view, local alias of such, unfinished/failed origin, name collision).
A re-exporting module resolves through the origin witness D1 already stores in its own
tuple, so a lookup in either module reaches the same `_Projection`.

### 3.2 `FrozenOrdinaryBase` (D2a)
View-owned immutable base materialized once per `use` from one `_Projection`:
`group` (G, identity only), `interface_key = projection.provenance` (diagnostics only),
`name`, `module_id`, `clauses: tuple[GeniaFunction, ...]` (one `_Clause.materialize()`
copy per clause, owned by this view, never exposed to Genia code), `span` (first clause
span), and `projection` (for the three channels). Copies preserve closure and
Ref/Cell/runtime-literal identity (D1 contract). Invariant: for every record,
`copy.dispatch_key == clause.dispatch_key` (the cached D1 key is used for validation;
the copy's own key for dispatch; the equality is a tested invariant). Views from the
same base are observationally identical; they need not share objects.

### 3.3 Contribution ownership (D2b store, D2a-tested shape)
Ownership of clauses never moves: each `OpenClauseRecord` keeps its **contributing
module's** closure (`self.env` at `extend`), span and declaring module id; a view never
rebinds a record to base or consumer scope.
- **Explicit-open targets (historical R20, unchanged):** `Env.open_contributions[
  interface_key]` → `ModuleValue.contributions`. `interface_key=(module,name)` is
  identity-equivalent for explicit interfaces because redeclaration is rejected
  (`open-function-redeclaration`), so this keying is exact-G-equivalent there.
- **Ordinary targets (new):** `Env.ordinary_contributions: dict[int, unit]` keyed by
  `id(G)`, where the unit (`GeniaOpenContributionUnit`, new field
  `target: object | None = field(default=None, compare=False, repr=False)` so dataclass
  equality/repr never touch G) holds a strong reference to G so ids are never reused.
  The completed module copies the table onto a new private frozen field
  `ModuleValue._ordinary_contributions: tuple[unit, ...]` (not an export, not equality,
  not reflection; mirrors D1's `_ordinary_completions`). A unit is selected for base G
  iff `unit.target is G`.
- `(module, defining name)` = `G.owner` appears only in diagnostics/provenance. Aliases
  (`a = f` exported as `a`), re-exports and a different export spelling resolve to the
  same G and therefore the same unit. A different G that merely shares a spelling
  never matches. Repeated `extend` statements accumulate by building a **new** unit
  (existing mechanism); a unit is never mutated after construction and a view copies
  `tuple(unit.clauses)`.
- Same-unit duplicate keys keep failing at construction (`open-function-duplicate-clause`,
  unchanged). Failed contributor modules publish no `ModuleValue`, so their units are
  unreachable; a retry rebuilds a fresh unit against the cached completed base. A base
  that failed publishes no completion, so no contributor can have extended it.

### 3.4 Mixed-record view (D2a)
`GeniaLinkedOpenFunction.base` may now be a `GeniaOpenFunction` (explicit) **or** a
`FrozenOrdinaryBase`; every existing `isinstance(..., GeniaLinkedOpenFunction)` site is
unchanged. `units` is stored in canonical order (§4) as tuples. Unit records are
`OpenClauseRecord` (contributions, explicit base) or `GeniaFunction` (ordinary base).
The view exposes `interface_key`, `base`, `units` and nothing mutable.

### 3.5 Candidate adapter in the shared engine (D2a)
`_dispatch_open` keeps its algorithm (shape stratum over all units → first candidate per
unit → exactly one body → ambiguity if more than one unit has a candidate). Only the
per-unit candidate step and the invocation step gain a record-kind branch, gated on
`isinstance(r, GeniaFunction) and r.pattern is None` (identifier header). The unit's record
list handed to `_first_unit_match` is sliced at (and including) the first such record, so
records after it are unreachable exactly as in `_dispatch_once`:
- *candidate:* an identifier-header record always matches (no matcher, no guard) and
  ends that unit's scan, exactly as `GeniaFunctionGroup._dispatch_once` behaves today;
  its bindings are "none" (the trampoline binds the header frame).
- *invocation:* `TailCall(record, args)` (header frame constructed once by the
  trampoline, TCO preserved, no second trampoline, no body run during discovery).
- pattern-header `GeniaFunction` records already satisfy the `OpenClauseRecord` duck
  interface (`_run_pattern_record` reuses `_first_unit_match`/`_invoke_open_clause`) and
  take the unchanged path; matcher Outcome conversion (`PatternOutcomeError`) is unchanged.
- grouped `case` bodies of an identifier-header record are part of the **body**: an arm
  miss after selection is that body's own terminal evaluation error
  (`No matching case for function …`, `RuntimeError`), not a dispatch diagnostic, and
  never falls through to another unit. Arms therefore carry no link-time keys
  (D1's arm ordinals remain provenance only).
Consequence stated by the contract ("may"): an always-matching identifier-header base
clause makes a selected specialization of the same shape ambiguous at call time whenever
the specialization also matches the arguments.
View build eagerly reads every copy's `dispatch_key` (and every unit record's), so a
malformed key surfaces as a pre-publication error, never as a first-dispatch `TypeError`.

### 3.6 Awareness (D2a)
`_callable_explicitly_handles_none/some` already treat `GeniaLinkedOpenFunction` through
`_open_stratum_records`. For `GeniaFunction` records in that stratum use the existing
`_record_handles_none/some` helpers (which already cover identifier and pattern headers);
`OpenClauseRecord` keeps its current expression. Union over the stratum across all
units is unchanged. Group-only extras do **not** apply to views (register Δ6).

## 4. Canonical identity and ordering (Decision B)

- **Unit identity:** base unit label `'base'` (existing convention); contribution unit
  label = `declaring_module_id` = the canonical cached module name used as the
  `Env.load_module` cache key (STATE: "canonical cached module name"). Import alias,
  filesystem path, module-value address, `with` position and import order never
  participate.
- **Sort key:** ascending Python `str` order of `declaring_module_id` (Unicode
  code-point order; no case folding, locale or normalization). `'base'` is not a
  contributor key; the base unit is always first. Identical ids cannot reach the sort:
  selecting one module twice (through any aliases) fails earlier with the existing
  `open-function-duplicate-selection`. No further tiebreak exists or is needed.
- **Within a unit:** lexical ordinal (record list index).
- Order of consumers: validation scan, stored `units`, dispatch participation,
  `help` listing (matches today's `sorted(units, key=declaring_module_id)`), and all
  rendered unit lists in diagnostics (already sorted today).
- Guard/matcher effect order during candidate discovery follows this canonical order
  but is **not** a contract guarantee and no test may assert it (contract §2.3).

## 5. Atomic linking transaction (D2a machinery, D2b activation)

Phases of `use <local> from <alias>.<name> with c1, c2, …`:
1. **Precheck (unchanged):** `check_rebind_target(local)`; then resolve base
   module alias (non-module ⇒ `open-function-target-not-open`) and export.
2. **Base eligibility:** explicit `GeniaOpenFunction` ⇒ explicit path; else
   `GeniaFunctionGroup` with `completion_for(...) is not None` ⇒ ordinary path; else
   existing `open-function-target-not-open` (views, closed, lambda, builtin, host
   callable, uncompleted, non-function).
3. **Selection resolution in `with` order (unchanged diagnostics):** each alias must be
   a `ModuleValue` (else `open-function-incompatible-contribution`), have a unit for
   this base (explicit: by `interface_key`; ordinary: by exact G; else
   `open-function-incompatible-contribution`), and not repeat a module id
   (`open-function-duplicate-selection`). These errors keep their historical
   `with`-order dependence.
4. **Route, then validate, then one locked write.** `Env._entry_route(local)` (lock-free
   but able to read prelude declarations and raise `ValueError`) runs **before** any lock to
   find the home scope, exactly as `Env.set` does; a routed (runtime-owned) name uses the
   home scope's `publish_view` and then `_record_entry_declaration`. Steps a–c are pure
   reads of immutable data (cached keys, tuples, `_copy_syntax` copies) and need no lock; they
   run before the lock is taken. Only step d holds `_BINDING_LOCK` — **once, by the home
   scope, never nested, with no user code**:
   a. sort units canonically (§4);
   b. `plan_link(base_participant, units)` — pure; scans pairs `(i<j)` in canonical
      order, clause ordinals ascending in `i` then `j`; per clause pair checks equal
      `dispatch_key` first, then fixed-`n`/varargs-`m≤n`; the **first** conflict found
      raises its error; uses only cached keys (no walker rerun, no matcher/guard/body,
      no renderer, no callback);
   c. build the view (copies/tuples only);
   d. `Env._write_binding(local, view, assignable=True, …)` — the checked writer —
      called inside the single lock hold of `Env.publish_view(name, view)`.
   A test covers a runtime-owned (routed) name and a pruned name's `ValueError`.
5. **Failure:** every error in 2–4c occurs before the only mutation (4d). No binding,
   prior view, contribution table, completion cache or escaped value changes; a retry
   starts from identical state. An `ImmutableBindingError` raised by 4d (a race after
   the lock-free precheck) is also pre-publication. `use` still never evaluates a
   clause, matcher, guard or annotation.

`check_rebind_target` stays lock-free (it was never part of a lock hold); the design
does not claim atomicity between it and step 4, only that publication re-checks under
the lock.

## 6. Diagnostics, provenance and observable identities

### 6.1 New identities (frozen here; wording is a shared-spec oracle form)
Both subclass `OpenFunctionError(TypeError)` in `callable.py`; spans render through the
existing `_format_open_span(span, closure.module_identity())` (imported module ⇒
`module:line`; entry ⇒ source label; never a path or host repr).

**Unit rendering `U(unit)`** (new messages only; collision-free): the base unit is
`base[{module_id}]` (unquoted, bracketed), a contribution unit is `{module_id!r}` (quoted).
So a contributor module literally named `base` renders `'base'`, never `base[base]`.

`open-function-cross-unit-duplicate-clause` — two different participating units contain
clauses with equal `dispatch_key`:
```
open-function-cross-unit-duplicate-clause: {name} has an identical dispatch key in units {U1} and {U2} shape={shape!r} (first at {span1}, duplicate at {span2})
```
`U1` precedes `U2` canonically; `span1`/`span2` are those clauses' spans; `shape` is
`dispatch_key[0]` (e.g. `('fixed', 3)`). Payload attributes: `interface_key`,
`first_unit`, `second_unit`, `shape`, `first_span`, `duplicate_span`.

`open-function-shape-conflict` — a fixed-arity clause of arity `n` in one unit and a
varargs clause with minimum `m ≤ n` in a different unit, irrespective of pattern
disjointness:
```
open-function-shape-conflict: {name}: {d1} in unit {U1} (at {span1}) conflicts with {d2} in unit {U2} (at {span2}); a fixed-arity clause conflicts with a varargs clause of another unit whose minimum arity is not greater
```
where `U1` precedes `U2` canonically and `d` is `fixed/{n}` or `varargs/{m}+`. Payload:
`interface_key`, `first_unit`, `second_unit`, `first_shape`, `second_shape`,
`first_span`, `second_span`. Same-unit fixed+varargs, varargs-vs-varargs, and
different-shape fixed-vs-fixed never trigger it (the latter two remain runtime
`open-function-varargs-ambiguity` or non-overlapping).

Worked shape example (illustrative; the exact fixture and string are frozen in RED): base
`f(x) = x` (`base.genia:1`), contributor `ext` with `extend base.f(x, ..r) = 1` (`ext:2`) ⇒
`Error: open-function-shape-conflict: f: fixed/1 in unit base[base] (at base:1) conflicts with varargs/1+ in unit 'ext' (at ext:2); a fixed-arity clause conflicts with a varargs clause of another unit whose minimum arity is not greater`.

Example (the historical overlapping-unit spec, new oracle in D2b):
`Error: open-function-cross-unit-duplicate-clause: get has an identical dispatch key in units 'db_ext' and 'db_ext2' shape=('fixed', 3) (first at db_ext:2, duplicate at db_ext2:2)`
(exit 1, stdout empty), raised at the `use` line, before any call.

### 6.2 Error order (deterministic)
Pipeline order in §5 is the observable order: precheck → base/target → `with`-order
resolution errors (existing identities) → canonical-order link validation → publication.
A program with several faults reports the first in that order; the link-validation
stage reports the first conflict in the §5.4b scan order independently of `with` order.

### 6.3 Dispatch diagnostics for every view (Decision A)
All failures during view invocation use the existing R20 class family and **unchanged
text**, for ordinary-source and explicit-open records alike:
| Situation | Class / text |
|---|---|
| no eligible shape for the arity | `OpenFunctionNoMatchingFunctionError` — `No matching function: f/n. Available: …` |
| shape selected, no unit has a matching candidate | `OpenFunctionNoMatchingCaseError` — `No matching case for function f/n with arguments […]` |
| more than one distinct eligible varargs minimum | `OpenFunctionVarargsAmbiguityError` — `open-function-varargs-ambiguity: …` |
| more than one unit supplies a candidate | `OpenFunctionClauseAmbiguityError` — `open-function-clause-ambiguity: …` |
| selected body evaluation (incl. a body-level `case` arm miss) | the body's own error (unchanged) |
Plain (non-view) ordinary groups keep their legacy `TypeError("Ambiguous function
resolution …")` / `RuntimeError("No matching case …")` identities (guarded by
`test_model_b_slice_c_identity.py`). **Decision A resolution (made here, not deferred):** "consistent `open-function-*`
categories" is realized as one **class family with the existing, unchanged texts** for every
view. Rejected alternative: prefixing the no-match texts (`open-function-no-matching-…`)
would change the `No matching function/case` oracles of 9 R20/Model B shared specs that
exercise open interfaces (e.g. `error-r20-no-matching-case`, `model-b-c-d8-terminal-grouped-miss`,
`model-b-c-pat-fixed-miss-no-varargs-fallthrough`) plus 14 Python test modules, contradicting
"never silently alter historical oracles" for no behavioral benefit. Design acceptance on
#1250 is the approval; a maintainer veto before RED sends the design back with that delta list.
Because Δ2 rejects cross-unit fixed/varargs conflicts at `use`, the remaining runtime
varargs ambiguity arises only from distinct varargs minima (within a unit or across
units).

## 7. Metadata (D2b; B1 three channels) and R20 preservation

For a view whose base is a `FrozenOrdinaryBase`, with `P = base.projection`:
| Observation | Source |
|---|---|
| `meta(view)` | `P.binding_metadata` (channel 1) — frozen, read-only |
| `doc(view)` | `P.projected_doc` (channel 2) else existing `none("missing-doc")` |
| `help(view)` | `P.help_doc` + summary lines of `P.help_metadata` (channel 3) + clause provenance: base unit first (`base (module)` with each `_Clause.provenance` span), then contribution units in canonical order |
**Per-function precedence (verified against `builtins.py`).** `doc(name)` and `meta(name)` take a
string name and resolve it with `lookup_env.get(name)`; `help(x)` is value-based (`help("name")`
resolves the string then behaves as `help(value)`).
| Call | Explicit-open interface/view (unchanged) | Ordinary-base view (new) |
|---|---|---|
| `doc(name)` | binding `@doc` metadata first, then interface `@doc`, then interface docstring | `P.projected_doc` (channel 2) **instead of** binding metadata; else `none("missing-doc")` |
| `meta(name)` | interface metadata only (binding metadata ignored) | `P.binding_metadata` (channel 1) |
| `help(value)` | `_describe_open_function` | `P.help_doc` + `P.help_metadata` summary + provenance |
Implementation shape: after `lookup_env.get(name)` and **before** `get_metadata(name)` in
`_doc_in_scope`, test `isinstance(target, GeniaLinkedOpenFunction)` with a
`FrozenOrdinaryBase` base and return the channel; `_meta_in_scope` gains the same early
branch; `help` gains a branch beside the existing open-function branch. Aliases evaluate
to the same view object, so `g = f_view` propagates it and alias annotations never overlay.
**Help provenance text (frozen):** for ordinary-base views every clause line renders
`{ordinal}. {module}:{line}` via `_format_open_span(span, module_id)` (module identity from
the `_Clause.provenance`/closure), never `span.filename`. The existing explicit-open
`help` prints raw `span.filename:line`, which for imported modules is a resolved path;
that pre-existing behavior is unchanged here, is **not** normalized by D2 (separate
technical-debt note), and its text is therefore excluded from shared oracles.
Direct annotation on `use` stays
prohibited by the existing parser/annotation rule. Contributor metadata never reaches
the base projection. Later alias annotations on G, slot changes or further `use`s cannot
alter any projection (D1 `_Metadata` is read-only and captured once). The `help` header
for these views is `{name} (linked ordinary function view)` (exact new text);
explicit views keep `{name} (R20 open function)`.

**Explicit-open preservation:** explicit bases and views keep today's interface-owned
metadata, the lookup precedence in the table above, header, help
body and error identities; the only changes are the §8 deltas. This divergence between
ordinary-base and explicit-open view introspection is the contract's stated intentional
candidate compatibility divergence (§5.3), not an implicit rewrite.

## 8. Observable compatibility register (D2b unless stated)

| Δ | Change | Evidence / handling |
|---|---|---|
| 1 | Ordinary targets for `extend`/`use` become accepted | owner: D2b RED commit (one dedicated commit, old/new text in its message and on #1250). Spec guards: `model-b-c-own-extend-ordinary-rejected`, `model-b-c-own-use-ordinary-base-unchanged`, `model-b-d1-preserve-ordinary-extension-rejection`. Python tests: `tests/unit/test_model_b_slice_c_ownership.py::test_ordinary_group_is_not_an_extend_or_use_target_today` (asserts exit 1 / `open-function-target-not-open`) and the two hard-coded id lists in `tests/spec/test_model_b_slice_c_red.py` (~57–58, ~275–276). Docs: `GENIA_RULES.md` ~535–542 ("`extend`/`use` on an ordinary function stays `open-function-target-not-open`" and the "fixed and varargs are distinct shapes" sentence needs the cross-unit conflict qualification), `GENIA_REPL_README.md` lines ~21 and ~37, README lines ~35/~52/~967, STATE ~745–749 and ~1080+ |
| 2 | Cross-unit equal key (and Δ3 fixed/varargs) now fail at `use` for **all** views | corpus probe (read-only, 34 `multi_file_eval` specs, 11 build a view): exactly one conflict, `error-r20-cross-module-overlapping-unit-ambiguity` (`db_ext` vs `db_ext2`, `('fixed',3)`); its stderr changes from call-time `open-function-clause-ambiguity: get/3 matched clauses in more than one unit ['db_ext', 'db_ext2']` to the §6.1 string at the `use` line. The historical expected text is **not edited silently**: the RED commit changes it explicitly with the maintainer authorization reference and the old text preserved in the commit message and this register. Python test `test_two_contributions_with_overlapping_dispatch_key_are_ambiguous_not_prioritized` is replaced by a rejection test; a new case with *distinct overlapping* keys (e.g. `get("db", db, key)` vs `get("db", 1, key)`) keeps proving runtime `open-function-clause-ambiguity` |
| 3 | A program whose overlapping units were never called with the overlapping domain previously ran; it now fails at `use` | inherent in Q1; documented in STATE at D2b |
| 4 | Explicit views store/dispatch units in canonical order instead of `with` order | affects only unpromised guard/matcher effect order; `help` order unchanged; D2b full regression required |
| 5 | Ordinary-base view `doc`/`meta`/`help` use frozen channels and ignore alias overlays | new surface; explicit views unchanged |
| 6 | Views do not receive group-only behavior: name-based `none`/`some` awareness (`_NONE_AWARE_PUBLIC_FUNCTIONS`/`_SOME_AWARE_PUBLIC_FUNCTIONS`) and the Flow-fusion adapters for `map`/`filter`/`take`/`drop`; only stratum-union awareness applies | an exported ordinary function named like a public prelude function changes `none` propagation once viewed; D2b tests pin this (shared where expressible) and STATE states it |
| 7 | View dispatch (shared `_dispatch_open`) does not thread debug hooks/`internal_access` into pattern-header clause bodies (identifier-header bodies run through their record's own hooks) | same as explicit views today; documented, not claimed as parity with group dispatch |
No Core IR, capability, wire or syntax change; no existing identity string or text changes.

## 9. Acceptance matrices

### 9.1 D2a (host-local; no shared spec; no public surface)
Files (proposed): `tests/unit/test_model_b_d2a_link_*.py`. Real modules via the loader;
contribution units built directly; private `link_view`/`plan_link`/`Env.publish_view`.
| ID | Observation |
|---|---|
| D2a-01 | `completion_for`: direct export, `a=f` alias export, re-export via other module, B1 replaced-slot G ⇒ same `_Projection`; lambda, builtin, host callable, view, local alias of lambda, failed/unfinished origin ⇒ `None` |
| D2a-02 | `FrozenOrdinaryBase`: clause/key/provenance fidelity, `copy.dispatch_key == clause.dispatch_key`, closure/Ref/Cell identity shared, later group/slot/alias changes do not alter it, copies not shared with authoritative syntax |
| D2a-03 | `plan_link` equal-key detection: alpha-equivalent, base-vs-contrib, contrib-vs-contrib, `true` vs `1`/`1` vs `1.0` distinct (proved in this test, not assumed), nested guard/lambda shadow and free-name distinctions; no matcher/guard/body/renderer invoked (sentinel counters) |
| D2a-04 | fixed `n` vs varargs `m≤n` rejected for disjoint patterns; `m>n`, same-unit mix, varargs-vs-varargs accepted |
| D2a-05 | canonical order: shuffled `with` orders and import orders give identical view, identical error and identical conflict report; sort by module id; duplicate selection raised first |
| D2a-06 | mixed dispatch: identifier-header base + open-clause contributions; pattern-header base; catch-all-vs-specialization ambiguity; fixed over varargs; varargs minima ambiguity; Outcome/`none` argument awareness; matcher Outcome; header-frame capture; self/mutual TCO through the view (the test binds the view to a name via `Env.publish_view` and calls it by name); effectful guard evaluated once per candidate; body-level case miss is not a dispatch error |
| D2a-07 | atomicity: injected fault at each stage (resolution, sort, each scan step, view build) leaves binding table, prior view, tables and completion cache unchanged; retry succeeds; immutable-name collision raises through the checked writer without partial effect |
| D2a-08 | lock discipline: single hold, no re-entrant acquisition, builder performs no `Env.get`/renderer; two threads publishing the same name (barrier-synchronised) never expose a half-built view; load racing `publish_view` |
| D2a-09 | explicit-open bases through the same validator (Q1 machinery) with the legacy public path untouched: public `use` over explicit bases still produces call-time ambiguity |
| D2a-10 | non-activation: `extend base.f` / `use f from base` over an ordinary base still raise `open-function-target-not-open`; no export, equality or reflection exposes `_ordinary_*`/frozen objects; full existing regression unchanged |

### 9.2 D2b (shared R16 + Python-local)
New shared specs (proposed ids; `requires: [multi_file_eval, open_functions, default_open_functions]`, plus `doc_help` where marked):
`model-b-link-positive-extend-use`, `…-import-inert`, `…-authority-negatives` (set: view, lambda, builtin, local alias, unfinished-origin via cycle, non-export), `…-alias-and-reexport`, `…-b1-slot-replaced`, `…-duplicate-selection-two-aliases`, `…-order-independence`, `…-cross-unit-duplicate-key`, `…-key-true-vs-one`, `…-key-shadow-and-free-names`, `…-shape-conflict-disjoint`, `…-shape-same-unit-ok`, `…-overlap-ambiguity-distinct-keys`, `…-catchall-base-ambiguity`, `…-failed-use-leaves-view`, `…-frozen-nonretroactive`, `…-later-view-same-snapshot`, `…-consumer-midinit`, `…-header-capture-and-tco` (Python-only TCO), `…-outcome-awareness`, `…-meta-doc-help` (`doc_help`), `…-view-alias-no-overlay` (`doc_help`), `…-explicit-view-metadata-unchanged` (`doc_help`), `…-diagnostics-no-host-leak`.
Existing shared specs: all 34 `multi_file_eval` specs, R20 IR/parse specs byte-stable except the four register-Δ oracles.
Python-local: lock/thread/fault-injection carry-overs from D2a re-run through the public path; REPL `use` rebinding; entry-route name; full regression (both partitions) and focused R20/Model B/D1 suites.
Preflight matrix mapping: D2-01..05, 08, 10–12, 17–18, 20–21 ⇒ shared; D2-06/07 ⇒ shared + D2a-03/04; D2-09/15/16 ⇒ D2a-07/08 re-run; D2-13 ⇒ regression; D2-14 ⇒ existing + D2a-10; D2-19 ⇒ shared + D2a diagnostics checks.

## 10. Conformance requirements and host gaps
- Portable contract authority is the Model B contract; shared specs land before or with
  Python D2b (RED first, SHA recorded). Shared `lower` checks are unaffected (no IR change).
- C++ (`genia-cpp@fef41e5`, contract 6402e668): `multi_file_eval` and `doc_help`
  unsupported; `default_open_functions` undeclared. Every D2b shared case reports
  `UNSUPPORTED` (never `PASS`); zero failure classes is the required result. Before D2b
  merge update `spec/known_host_gaps.json` (#1269 entry `affected_tests` with the new ids;
  #1018 `multi_file_eval` unchanged) and `docs/host-interop/HOST_CAPABILITY_MATRIX.md`;
  record that the Q1 validation rule changes the R20 cross-module contract a future C++
  implementation must adopt. No parity claim; D2a changes no gap.
- Gap policy and owner: #1250, `@m0smith` until reassigned.

## 11. Documentation impact
| Doc | D2a | D2b |
|---|---|---|
| `GENIA_STATE.md` | one sentence at the D1 paragraph (private link machinery exists, unreachable) at GREEN | ordinary `extend`/`use`, validation, new identities, deltas, three-channel metadata, replace the "equal key in two units is not a build-time duplicate" and "linking unimplemented" statements |
| `GENIA_RULES.md` | none | §8.5 incl. lines ~535–542: extend/use for ordinary bases, validation and ordering rules; replace the "stays `open-function-target-not-open`" sentence |
| `GENIA_REPL_README.md` | none | lines ~21 and ~37 state cross-module linking is unimplemented; rewrite at D2b GREEN |
| `README.md` | none | feature/limitations wording (lines ~35, ~967) |
| `AGENTS.md` | none | none expected; verify at D2b |
| `docs/design/r20-open-functions-contract.md`, Model B contract header, portable design §5.3 pointer, `docs/book/03-functions.md`, host matrix, known gaps, MCP `semantic_facts.json` (only if the language profile projects these facts) | none | updated; each classified KEEP/EXTRACT/DELETE at the doc-distillation gate. This file: **KEEP** (design record, like D1) |
Maintained-code documentation (docs/contract/code-documentation.md) is required for every new/changed binding in each slice.

## 12. Complexity, risks and phase gate
Complexity: **necessary**. One dispatch engine is retained; the only new branching is
the identifier-header candidate/invoke branch and a base-kind union. Risks and controls:
(1) regression in explicit dispatch ⇒ branch gated on record kind, D2b full regression;
(2) Q1/Δ2–4 oracle changes ⇒ explicit register, maintainer-approved, no silent edit;
(3) stale-key divergence between D1 key and copy key ⇒ tested invariant D2a-02;
(4) lock misuse ⇒ pure builder, D2a-08; (5) id-keyed store ⇒ strong reference to G;
(6) per-`use` copy cost ⇒ O(clauses), accepted; (7) Decision A text mapping ⇒ resolved in §6.3 with a costed rejected alternative; (8) group-only behavior absent
from views ⇒ register Δ6/Δ7, pinned by tests.
Gate: this design authorizes **no** RED test, production code, E or R29. Next gate: D2a
RED (separate authorization) after design review acceptance.

## 13. File plan and final check (docs/process/02-design.md)

**New files:** D2a — `src/genia/function_linking.py` (private: `FrozenOrdinaryBase`, `plan_link`, canonical order, `link_view`; no Genia-visible name), `tests/unit/test_model_b_d2a_link_*.py`; D2b — shared specs listed in §9.2 under `spec/eval` / `spec/error` and `tests/unit/test_model_b_d2b_*.py`; this design file (KEEP).
**Modified (D2a):** `ordinary_completion.py` (`completion_for`), `callable.py` (`GeniaLinkedOpenFunction.base` union, `GeniaOpenContributionUnit.target`, candidate/invoke branch, awareness branch, two new error classes), `environment.py` (`publish_view`, `ordinary_contributions`), `values.py` (`_ordinary_contributions`), maintained-code docs. **Modified (D2b):** `evaluator.py` (two branches), `builtins.py` (reflection branches), `spec/known_host_gaps.json`, host matrix, the documents in §11, the Δ1 tests above. **Removed:** none.
**Final check:** contract not changed; no behavior added beyond the contract and the six maintainer decisions; every unresolved choice is either resolved above (Decision A, labels, precedence, routing) or listed as a risk; nothing here is described as implemented.
