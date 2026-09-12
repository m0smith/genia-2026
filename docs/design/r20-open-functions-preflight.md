# R20 Open Functions and Extensible Pattern Dispatch Pre-flight

Status: **E20-0 CONTRACT GATE COMPLETE — implementation-ready semantics; NO-GO for behavior until a separate syntax/design slice and failing shared tests.** `GENIA_STATE.md` remains final authority for implemented behavior. This document records inventory and readiness only.

## 1. Scope and source-of-truth review

This pre-flight was produced after reviewing the current `AGENTS.md`,
`GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`,
`docs/strategy/killer-workflow.md`, `docs/strategy/release-roadmap.md`, and
`docs/strategy/roadmap/r16-r20.md`.

R20 is limited to one portable semantic change: a named, lexically visible open
function can own ordered local pattern clauses and can receive explicitly
selected, immutable cross-module clause contributions. It does not add a
protocol/typeclass system, dynamic registration, method syntax, `==`
overloading, lifecycle behavior, or a C++ host.

The feature supports the killer workflow only where independently owned value
representations need one explicit validation/transformation dispatch point. It
must continue to use Genia patterns, ordinary calls, values, modules, and
Outcomes rather than introduce a competing object or method model.

## 2. Current behavior inventory

The facts in this section describe the repository before R20 implementation.
They are evidence, not authority for proposed R20 behavior.

### 2.1 Named function groups and arity resolution

- `Env.define_function` creates one `GeniaFunctionGroup` for a name and adds
  later definitions in the same environment to that mutable group.
- A group is currently keyed by minimum/fixed arity (`dict[int,
  GeniaFunction]`), so it can contain only one function value at a given arity.
  A second definition at that arity raises `Duplicate function definition:
  <name>/<arity>` before argument-pattern dispatch is relevant.
- A name already bound to a non-group rejects a named function definition.
- Call resolution selects an exact fixed/minimum-arity entry first. Only when
  that entry is absent does it consider varargs entries whose minimum arity is
  satisfied. More than one eligible varargs entry is ambiguous; the current
  implementation does not select the largest minimum arity.
- `GeniaFunctionGroup` is a mutable Python reference-host representation. R18
  nevertheless contracts functions and groups as identity-bearing values; two
  equal-looking groups are not structurally equal.

### 2.2 Existing pattern dispatch

- A named function definition has ordinary parameter names and one body. A
  body may be an `IrCase`; its clauses match the complete argument tuple.
- Grouped case clauses are tested in lexical source order. The first pattern
  match whose optional guard is truthy runs; there is no specificity ranking.
- A miss produces the normalized `No matching case for function
  <name>/<arity> with arguments <Genia-debug-list>` diagnostic.
- Pattern semantics already cover wildcard, binding, literal, tuple, list/map,
  final rest, Option, glob, named-pattern/Template composition, duplicate
  bindings, and guards. R20 has no authority to change those semantics.
- Automatic `none(...)` handling inspects grouped case patterns. R20 must not
  bypass that callable boundary when clauses are represented differently.

### 2.3 Bindings, modules, imports, and exports

- Lookup is lexical. Assignment may rebind a nearest assignable binding, while
  module evaluation uses a child environment with `rebind_parent=False`.
- `import mod` and `import mod as alias` bind exactly one cached `ModuleValue`;
  they do not splat exports into the importer.
- A file module currently exports a snapshot of every top-level binding in its
  module environment. There is no public/private declaration syntax or explicit
  export list. An underscore is not a language-level privacy rule.
- Module named access is narrow `module.name` access. A missing export is an
  error. Import aliases do not change module-value identity.
- Module cache identity currently uses the requested module name. Resolution
  has requester-relative, base-directory, and packaged-stdlib paths. R20 must
  not turn host filesystem paths or Python object addresses into portable open
  function identity.
- Loading evaluates module top-level code once, so arbitrary existing top-level
  expressions can have effects. The narrower invariant relevant to R20 is that
  declaring, importing, or selecting open-function contribution metadata must
  itself add no lifecycle activation, acquisition, network IO, or process IO.
  R20 does not retroactively make all module programs pure.
- Autoload is a separate root-binding mechanism, not module import, and must not
  implicitly activate or aggregate R20 contributions.

### 2.4 Core IR

- `IrFuncDef` carries name, parameter names, optional rest name, docstring,
  body, annotations, and one source span. It does not encode openness, a
  pattern-headed declaration, stable module identity, contribution target, or
  per-clause provenance.
- `IrCase`/`IrCaseClause` already encode ordered pattern, optional guard, and
  result records. Existing grouped pattern dispatch therefore has a portable
  representation, but repeated same-arity definitions cannot survive current
  evaluation as one clause set.
- `IrImport` carries module name, alias, and span. It has no contribution-use
  semantics.
- Core IR, not parser AST or `GeniaFunctionGroup`, is the portability boundary.
  Any R20 Core IR extension must be normalized by the shared IR adapter and
  rejected if a host cannot represent its required semantic fields.

### 2.5 Diagnostics and provenance

- Function definitions and clauses currently carry source spans, but a group
  retains no explicit declaring-module identity or contribution relationship.
- Duplicate arity, non-function rebinding, conflicting docstrings, no matching
  arity, varargs ambiguity, and case miss are existing diagnostic families.
- R19 requires portable diagnostics to use Genia rendering rather than host
  `repr`, and forbids raw host/library exception text at portable boundaries.
  R20 diagnostics must preserve protected-value redaction.
- Current varargs ambiguity candidate text is sorted by minimum arity, but two
  same-arity pattern candidates cannot currently reach callable dispatch.

### 2.6 Metadata and help

- A group has one merged metadata map and one canonical legacy docstring.
  Identical docstrings across arities are accepted; conflicting docstrings fail.
- `help(name)` renders group shapes, the earliest source span, one effective
  docstring, and selected group metadata. It does not enumerate clauses or
  module provenance.
- `doc(name)` and `meta(name)` address a lexical name. Public prelude functions
  and host functions use existing canonical metadata registries/generation.
- R20 must retain one interface-level documentation contract while making
  per-clause provenance inspectable. A contribution cannot replace interface
  documentation or annotations merely by adding a clause.

### 2.7 Shared conformance

- Shared categories are `parse`, `ir`, `eval`, `error`, `cli`, and `flow`.
  Parse normalization compares host-neutral AST snapshots; IR normalization
  compares portable Core IR; error cases compare exact stderr; eval cases
  compare normalized results/stdout/stderr.
- Existing shared coverage includes functions, case/pattern behavior, imports,
  Core IR definitions, and diagnostics, but no explicit open interface,
  repeated pattern-headed same-arity clauses, contribution selection,
  contribution provenance, or cross-module ambiguity case.
- R16 requires capability advertisement and prevents unsupported cases from
  counting as passes. R20 needs a distinct capability requirement so an older
  host cannot silently claim these cases.

## 3. Gaps that block implementation without a contract

1. Current arity-keyed storage conflates a callable shape with a single body.
2. Source order is meaningful inside one grouped case, but import order cannot
   be allowed to become cross-module overload order.
3. A string name is insufficient identity: unrelated modules may export the
   same spelling, and aliases must not create new interfaces.
4. Ordinary imports have no explicit contribution-selection operation.
5. Existing metadata is group-wide and cannot explain which module supplied a
   matching or ambiguous clause.
6. Syntactic equality is not a safe duplicate definition until binder names,
   source spans, and guard structure are normalized.
7. Existing Core IR cannot distinguish an open declaration, contribution, and
   explicit selection without host-local side tables.

The companion contract resolves these semantic gaps without selecting concrete
surface spelling.

## 4. Readiness and required slice order

The implementation-ready contract is
`docs/design/r20-open-functions-contract.md`. Work must proceed in separate
phases:

1. **E20-1 syntax and Core IR design** — choose the smallest unambiguous surface
   spelling and exact normalized node names/fields consistent with the contract.
2. **E20-2 failing shared parse/IR tests** — commit before parser/lowering work.
3. **E20-3 local open-clause implementation** — repeated/grouped equivalence,
   duplicates, arity strata, TCO/Option behavior.
4. **E20-4 failing shared module/error tests** — commit before contribution
   linking implementation.
5. **E20-5 explicit contribution implementation** — immutable lexical views,
   provenance, visibility, deterministic ambiguity.
6. **E20-6 metadata/help and cross-mode hardening** — provenance introspection,
   inertness, redaction, autoload and lifecycle non-regression.
7. **E20-7 implemented-truth synchronization** — only now update
   `GENIA_STATE.md`, affected book/cheatsheet/reference surfaces, and roadmap.
8. **E20-8 skeptical release audit/distillation**.

### 4.1 Required shared evidence for later TEST phases

This pre-flight, rather than the semantic contract, owns the future test plan.
Before R20 is called implemented, shared evidence must include:

- **parse:** the eventually approved grouped/repeated/open/contribution/use
  forms and rejection of nested declarations, implicit targets, and contribution
  metadata replacement;
- **IR:** grouped/repeated semantic equivalence with distinct clause spans,
  fixed/varargs shapes, explicit target and contribution identities, explicit
  use, and unchanged ordinary closed functions/imports;
- **eval/module:** local first-match behavior, grouped/repeated equivalence,
  fixed-over-varargs behavior, varargs ambiguity, disjoint contributions,
  base/contribution and contribution/contribution overlap, alias/cache identity,
  ordinary-import non-selection, import/selection permutations, lexical
  visibility, and consumer non-transitivity;
- **error/help/inertness:** exact portable duplicate/incompatible/selection/
  ambiguity/miss diagnostics, stable help provenance, protected redaction, no
  clause-body or R20-added effect during declaration/import/selection, and
  applicable execution-mode parity; and
- **Flow regression:** an open linked view remains an ordinary callable without
  changing pipeline or Option/Outcome propagation.

The R16 protocol must advertise a dedicated R20 capability. Parse, IR, eval,
error, and applicable CLI evidence are required for an R20 conformance claim;
unsupported cases remain visible and do not count as passes.

## 5. Go/no-go

**GO** for E20-1 syntax/Core IR design against the companion contract.

**NO-GO** for parser, runtime, module, help, shared-spec, or implemented-truth
changes in this contract phase. In particular, the motivating spelling in the
roadmap is illustrative and remains unapproved.

