# R20 Open Functions and Extensible Pattern Dispatch Contract

Status: **IMPLEMENTATION-READY CONTRACT — E20-0 complete; behavior not yet implemented.** `GENIA_STATE.md` remains final authority for implemented behavior. This contract defines the required semantics but deliberately does not approve surface syntax.

## 1. Purpose and boundary

R20 adds one concept: an **open function interface** is an identity-bearing,
ordinary callable whose immutable clause set may be assembled from ordered
local clauses and explicitly selected cross-module contributions.

R20 reuses existing patterns, guards, calls, lexical bindings, modules,
metadata, diagnostics, and Core IR. It does not add methods, implicit protocol
conformance, type-directed lookup, global registries, runtime mutation, or
user-overloadable equality.

Terms used below:

- **interface** — the declaring open function and its identity
- **clause** — one argument-pattern, optional guard, body, callable shape, and
  provenance record
- **base unit** — the interface-declaring module's local clauses
- **contribution unit** — one module's explicitly declared clauses targeting
  one interface
- **linked view** — the immutable callable visible in one lexical module after
  an explicit set of contribution units is selected

## 2. Interface identity

### 2.1 Stable key

Each open interface has one opaque semantic identity created by its declaration.
Its portable key is the pair:

1. the declaring module's canonical module identity, and
2. the exported binding name in that module.

For an entry/in-memory program, the runner supplies a deterministic source-unit
identity in the normalized input. A filesystem path, import alias, object
address, allocation order, cache insertion order, or host hash is never the
portable key.

Two aliases of the same cached module export refer to the same interface.
Two modules exporting the same name declare different interfaces. Re-evaluating
the same source unit in a new execution creates a new runtime callable identity,
consistent with R18, while retaining the same diagnostic/provenance key.

Interface values and linked views remain identity-bearing under `==`. Clause
contents are not structural callable equality, and R20 cannot overload `==`.

### 2.2 Declaration and closure ownership

Exactly one module/source unit owns an interface declaration. Base clauses close
over that declaration's lexical environment. A contribution clause closes over
its own declaring module environment, not the importer's environment and not the
base module's private lexical environment.

A declaration cannot replace an existing non-function binding, convert a closed
ordinary function implicitly, or redeclare an interface key in the same module.
Whether an ordinary grouped function can be explicitly declared open using the
chosen E20-1 surface is a syntax question; semantically, openness must be
declared, never inferred from a later foreign contribution.

## 3. Local clause accumulation

### 3.1 One canonical clause model

Grouped clauses and repeated local clause declarations lower to the same ordered
clause records. Equivalent records therefore have identical dispatch,
diagnostics, metadata, TCO, and Option/Outcome behavior.

Within one base or contribution unit, lexical declaration order is the clause
order. Repeated local clauses extend only the same interface/unit in the same
module-level lexical binding. They never search a parent environment for a
same-spelled open interface and never mutate an imported module value.

Nested/local-scope open declarations and extensions are outside R20. E20-1 must
reject rather than invent semantics for them.

### 3.2 Compatible clauses

A clause is compatible with an interface when:

- its target identity is exact;
- it is a named, pattern-dispatched clause rather than a value rebinding;
- its fixed or varargs shape is well formed under existing parameter/rest rules;
- its pattern and guard use existing portable pattern/IR forms; and
- it does not attempt to set or replace interface-owned metadata.

Different fixed arities and different varargs minimum arities may coexist.
Multiple clauses may share a callable shape when their dispatch keys are not
duplicates.

## 4. Explicit cross-module contributions and visibility

### 4.1 Declaration is not selection

A contribution declaration names an exact imported open interface identity and
creates inert contribution metadata plus clause closures in the contributing
module. It does not mutate the target interface, the target module, a process
registry, or any already-created linked view.

An ordinary import only binds its module value and evaluates that module under
the existing module rules. It does **not** select any contribution exported by
that module. A consumer must perform a separate, explicit contribution-use
operation naming the target interface and contribution module/unit. E20-1 owns
the concrete spelling for declaration and use.

### 4.2 Linked lexical view

Contribution use is a declarative link operation, not an executable expression.
A host resolves the complete selected set for a module after its imports and
declarations are available and before any ordinary top-level expression in that
module can call the view. Thus source placement cannot expose a partially linked
or temporally mutating view. The operation creates the target name's linked view
in the current module only. The selected set is immutable after linking and is
not inherited process-globally by importers of that consumer. If a consumer
wants to export its linked view, it does so as its own ordinary exported
binding; this does not change the original interface identity or silently pass
selection to unrelated modules.

Selection requires the target interface to be visible by ordinary lexical or
module binding rules and the contribution unit to be an exported member of the
named module value. Private/non-exported contribution metadata is inaccessible.
R20 adds no wildcard import or export splatting.

Selecting the same contribution unit for the same target more than once is a
duplicate-selection error, including selection through two aliases of one
cached module. Selecting a unit for a different interface, a closed function,
or a non-function is an incompatible-contribution error.

### 4.3 Import-order independence

The semantic selected set is a set keyed by contribution provenance, not a list
ordered by import evaluation. Changing the order of unrelated ordinary imports
or explicit selections cannot change a successful dispatch result.

Within a single contribution unit, source clause order remains meaningful.
Across units, no total dispatch order exists. Sorting provenance is permitted
only for stable introspection and diagnostics; it must not break a match tie.

## 5. Dispatch

Given arguments of count `n`, dispatch is exactly:

1. **Shape stratum.** If any fixed-arity clause has arity `n`, only fixed
   clauses of arity `n` participate. Otherwise collect every varargs shape whose
   minimum arity is at most `n`. If more than one distinct varargs minimum is
   eligible, fail with varargs-shape ambiguity; do not choose the largest
   minimum. If none is eligible, fail with no-matching-function.
2. **Unit-local selection.** In each participating unit independently, test
   clauses of the selected shape in lexical source order using existing pattern
   and guard semantics. At most the first matching clause in each unit becomes
   that unit's candidate.
3. **Across-unit selection.** If exactly one unit supplies a candidate, invoke
   it. If more than one unit supplies a candidate, fail with clause ambiguity.
   There is no specificity ranking and provenance sort order cannot select one.
4. **Pattern miss.** If no unit supplies a candidate, fail with the existing
   no-matching-case semantic family for the interface and argument count.

The base unit participates exactly like one unit. Consequently, a foreign
clause overlapping a matching base clause is ambiguous; extensions are safe by
construction only when their accepted argument domains do not overlap, or when
the contract later adds an explicit priority mechanism in a separate release.

This algorithm preserves current fixed-over-varargs behavior and current
first-match grouped-case behavior without making cross-module import order a
hidden priority rule.

## 6. Duplicate clauses

Every clause has a **dispatch key** consisting of:

- fixed versus varargs shape and its arity/minimum;
- the portable Core IR pattern with spans removed and bound variables
  alpha-normalized by first binding occurrence; and
- the optional guard's portable Core IR with spans removed and references to
  pattern bindings alpha-normalized consistently.

Two clauses in the same unit with the same dispatch key are duplicates,
regardless of body text, metadata, binder spelling, or source form (grouped
versus repeated). Duplicate detection happens when the unit is built, before
the interface can be called. It is not deferred until values happen to match.

The same dispatch key in different units is not reported as a declaration-time
duplicate because separately authored guards/patterns can be intentionally
disjoint only at runtime; if both match one call, the across-unit ambiguity rule
applies. This avoids pretending that arbitrary guard overlap is statically
decidable.

## 7. Provenance, metadata, and help

### 7.1 Required clause provenance

Every clause record retains:

- interface portable key;
- base or contribution role;
- declaring module/source-unit identity;
- contribution-unit identity when applicable;
- source span (filename/source label, start and end line/column);
- fixed/varargs shape and arity/minimum; and
- lexical ordinal within its unit.

Portable diagnostics use the semantic module/source identity and normalized
span. Host paths may be shown only as separately classified host-local detail.
Provenance is immutable and survives export, aliasing, linking, and calls. R20
preserves it for later unload/reload design but defines no unload/reload action.

### 7.2 Interface metadata ownership

`@doc`, category, stability, deprecation, and other interface metadata belong to
the single interface declaration. Repeated base clauses may repeat identical
legacy doc text under the existing canonical-doc rule; conflicts fail.
Contribution clauses cannot supply, replace, merge, or erase interface-level
metadata. Clause-local annotations unsupported by the E20-1 design are rejected,
not silently promoted to interface metadata.

### 7.3 Introspection contract

`help(interface-or-linked-view)` must retain the interface name, callable shapes,
effective interface documentation, and declaration location. It must additionally
list every participating unit and clause provenance in deterministic order:
base first; contribution units ordered by portable provenance key; clauses within
each unit by lexical ordinal. This display order is informational only.

`doc(name)` continues to return interface documentation. `meta(name)` continues
to return interface metadata; clause provenance is not smuggled into that
user-authored metadata map. E20-1 must choose one explicit introspection shape or
extend `help` only; it must not expose mutable host runtime objects. The required
provenance data above must remain available to portable help/diagnostics either
way.

## 8. Deterministic diagnostic identities

R20 requires these portable semantic diagnostic identities and parameters:

- `open-function-redeclaration(interface_key)`
- `open-function-target-not-open(target)`
- `open-function-duplicate-clause(interface_key, unit_key, shape,
  first_span, duplicate_span)`
- `open-function-duplicate-selection(interface_key, unit_key)`
- `open-function-incompatible-contribution(expected_interface_key,
  actual_target)`
- `open-function-varargs-ambiguity(interface_key, call_arity, shapes,
  provenances)`
- `open-function-clause-ambiguity(interface_key, call_arity,
  candidate_provenances)`
- existing `no-matching-function` and `no-matching-case` families where the
  dispatch algorithm specifies them

Lists of shapes and provenance are sorted by the portable provenance ordering;
argument values use Genia safe debug rendering. Raw host object identities,
exception text, unordered-map iteration, absolute path accidents, and protected
payloads must not appear. E20's failing error specs must pin the exact CLI text
before runtime implementation; the identities and parameter order above are
already contractual.

## 9. Inertness and effects

Open declaration, contribution declaration, contribution selection, module
caching, metadata inspection, and help discovery perform no lifecycle
activation, resource acquisition, networking, process IO, configuration/secret
lookup, provider call, or arbitrary clause invocation.

This is an R20-mechanism guarantee, not a claim that evaluating arbitrary module
top-level expressions is effect-free. Existing explicit top-level code keeps its
existing behavior. A clause body executes only after successful call dispatch.
Pattern/guard evaluation retains existing semantics and cannot be run merely to
link a view.

Autoload lookup cannot discover or activate contribution units. Native-test
discovery, file/command/pipe modes, import mode, and serve entry evaluation must
observe the same explicit selection and immutable linked-view rules.

## 10. Portable Core IR requirements

E20-1 may choose node names, but normalized portable Core IR must represent,
without host side tables:

1. an open-interface declaration and its exported binding name;
2. each clause's fixed/varargs shape, argument pattern, optional guard, body,
   annotations allowed by this contract, and full source span;
3. base versus contribution role and the explicit contribution target;
4. a contribution-unit identity local to its declaring module; and
5. an explicit contribution-use operation naming target and unit.

Grouped and repeated local syntax must normalize to semantically identical
ordered clause records. Parser-only aggregation that loses original per-clause
spans is forbidden. Runtime-only mutation of `GeniaFunctionGroup` with no Core
IR representation is non-conforming.

Existing closed `IrFuncDef` remains valid and unchanged for ordinary functions.
R20 must not reinterpret every existing named function as open. Hosts must
reject malformed R20 IR deterministically: duplicate unit identity, target-key
mismatch, missing clause provenance, unsupported pattern/guard node, or use of a
contribution without an open target.

## 11. Host-independent conformance obligations

A conforming implementation must expose the same normalized parser/Core IR
meaning, dispatch results, diagnostic identities and parameters, module
visibility, provenance, help information, and inertness guarantees defined by
this contract. The implementation may not rely on Python dictionaries, object
identity formatting, filesystem-path accidents, import evaluation order, or a
host-specific overload algorithm to fill a semantic gap.

The R16 adapter capability model must distinguish hosts that implement this
entire boundary from hosts that do not. Unsupported R20 operations cannot be
reported as successful conformance. The pre-flight document owns the later
shared-evidence plan; this contract contains semantic obligations only.

## 12. Explicit non-goals

- approving `open`, `extend`, `use`, or any other concrete spelling in E20-0
- implicit extension from ordinary import
- process-global or dynamically mutable dispatch tables
- extension priority, pattern specificity, best-match ranking, or fallback
  annotations
- protocols, traits, typeclasses, multimethod objects, methods, or nominal
  receiver dispatch
- extending closed ordinary functions or named patterns/Templates implicitly
- overloading `==`, map-key equality, or pattern equality
- private/export declaration redesign beyond requiring contributions to cross an
  existing module export boundary
- unloading, reload replacement, hot code swap, or version negotiation
- C++ implementation

## 13. Acceptance criterion

R20 is complete only when a non-Python host can implement the Core IR and shared
cases from this contract alone and demonstrate that:

- grouped and repeated equivalent local clauses dispatch identically;
- fixed/varargs precedence and ambiguity are deterministic;
- separately authored modules contribute only through explicit selection;
- ordinary import and unrelated import order cannot alter dispatch;
- overlapping successful units fail rather than acquire hidden priority;
- duplicates and incompatible targets fail with stable provenance;
- visibility remains lexical/module-scoped and linked views immutable;
- declaration/linking/import are inert with respect to R20-added effects; and
- help and errors expose host-independent provenance without leaking protected
  or host-local details.

## 14. Approval result

The semantic gate is resolved. **GO for the separate E20-1 syntax and exact Core
IR design phase. NO-GO for implementation or implemented-truth documentation in
this phase.**
