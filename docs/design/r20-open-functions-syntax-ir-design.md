# R20 Open Functions — Syntax and Core IR Design (E20-1)

Status: **DESIGN — approved for E20-2 onward implementation.** This document
chooses concrete surface syntax and Core IR under the semantic contract in
`docs/design/r20-open-functions-contract.md`. It does not itself change
runtime behavior; `GENIA_STATE.md` remains final authority for implemented
behavior until E20-7.

## 1. Design goals recap

Per the contract, E20-1 must resolve: repeated local clause syntax; grouped/
repeated equivalence; explicit open-interface declaration; explicit
cross-module contribution syntax; explicit selection/linking syntax; portable
interface identity; clause identity/provenance; contribution identity;
arity/varargs representation; visibility/linking representation; and exact
Core IR nodes/fields. The guiding rule is **smallest addition that reuses
existing machinery** — in particular the existing lambda-parameter pattern
parser (`Parser.parse_lambda_parameter_pattern`, used today for lambda
argument patterns) and the existing `IrCaseClause`/`IrPatTuple` pattern-match
machinery (`pattern_match.match_lambda_pattern`), which already implement
per-argument pattern matching with a trailing rest pattern. R20 adds no new
pattern engine.

## 2. Surface syntax

Three new top-level soft-keyword forms are added, following the repository's
existing precedent of soft top-level keywords (`import`, `as`, `pattern` are
already contextual identifiers, not reserved words; `open`, `extend`, `use`
join them the same way — recognized only in top-level statement position by
text, exactly like `try_parse_import_stmt` already recognizes `import`).

### 2.1 Local pattern clauses — `open` and repetition

```genia
open gcd(a, 0) = a
gcd(a, b) = gcd(b, a % b)

gcd(48, 18)
```

- The **first** clause of a new open interface must be introduced with the
  `open` keyword immediately before the function name: `open name(<pattern>,
  ...) = <body>`.
- Every **subsequent** top-level clause with the same name, in the same
  module, is a **repeated clause** and is written exactly like an ordinary
  function clause header (no keyword): `name(<pattern>, ...) = <body>`. It is
  recognized as belonging to the open interface only because that exact name
  was already declared `open` earlier in the same module's top-level clause
  run (see §2.4) — never inferred from pattern shape alone.
- `<pattern>` reuses the existing per-argument pattern grammar already used
  for lambda parameters (`Parser.parse_lambda_parameter_pattern`): identifier
  bind, wildcard `_`, literal, tuple/list/map pattern, `some(...)`/`err(...)`,
  named-pattern use, and a single final rest pattern (`..name`) for varargs.
  A clause whose patterns are all plain identifiers (no rest) is legal and
  behaves identically to an ordinary parameter list — this is how a fully
  var-headed clause still participates in one open interface.
- An optional guard may follow the closing `)`: `name(<pattern>, ...) ?
  <guard-expr> = <body>`, reusing the same `?` guard syntax already used by
  `case` clauses.
- Grouped repetition remains available and is fully equivalent: a single
  clause whose body is a `case`-with-`|` over the argument tuple (the
  existing `fact(n) = (0) -> 1 | (n) -> n * fact(n - 1)` shape) may itself be
  one clause of an `open` declaration:

  ```genia
  open gcd(a, b) = (a, 0) -> a | (a, b) -> gcd(b, a % b)
  ```

  Both spellings lower to the identical ordered `IrCaseClause` list (see §3);
  this is the required grouped/repeated equivalence.

### 2.2 Explicit cross-module contribution — `extend`

```genia
# base.genia
open get(store, key) = (MemoryStore(s), k) -> memory_get(s, k)

# db_ext.genia
import base
extend base.get(Database(db), key) = db_get(db, key)
```

- `extend <module-alias>.<name>(<pattern>, ...) = <body>` declares one clause
  of a **contribution unit** targeting the open interface exported as `<name>`
  by the module bound to `<module-alias>` in the *contributing* module's own
  import table. `<module-alias>` must already be bound by an `import` (or
  `import ... as`) statement earlier in the same module.
- Repeated `extend base.get(...)` statements for the same `(module-alias
  target, name)` pair in the same contributing module accumulate into one
  contribution unit, in source order, exactly like repeated `open` clauses.
- `extend` never mutates `base`, never requires `base` itself to know about
  the contributing module, and produces no callable value by itself — it is
  inert declaration only (§4.3).
- The alias is resolved to the *cached* `ModuleValue` at contribution-build
  time; because module loading is cached by canonical module name
  (`Env.load_module`), two different aliases bound to the same module resolve
  to the same target identity, and contribution-unit identity is (declaring
  module's canonical identity, target module's canonical identity, target
  name) — never the alias spelling or file path.

### 2.3 Explicit selection/linking — `use ... from ... with ...`

```genia
import base
import db_ext

use get from base with db_ext
```

- `use <name> from <base-alias> with <contrib-alias-1>, <contrib-alias-2>,
  ...` is a declarative top-level statement, evaluated once at module load
  like `import`, that:
  1. resolves `<base-alias>.<name>` to the target open interface (error if
     not open, not exported, or not found);
  2. resolves each `<contrib-alias>` to its module value and requires it to
     export exactly one contribution unit targeting that exact interface
     (error otherwise — incompatible-contribution);
  3. builds one immutable **linked view** consisting of the base unit plus
     the named contribution units, keyed by contribution-unit identity so a
     contribution named twice (directly or through two aliases of the same
     cached module) is a duplicate-selection error; and
  4. binds `<name>` in the *current* module only, as an ordinary lexical
     binding to that linked view.
- `use` never appears without an explicit contribution list; there is no
  wildcard "use all contributions" form (contract §4.2 forbids splatting).
- Plain `import db_ext` alone never changes what `base.get` or any bare
  `get` resolves to; only an explicit `use` creates a linked, contribution-
  extended callable, and only in the module that wrote the `use` statement.

### 2.4 Rejected forms

- A pattern-headed clause header (any non-identifier pattern item) for a name
  not already declared `open` in the same module is rejected with the
  existing "Invalid function definition parameter token" diagnostic — this
  is unchanged parser behavior, not a new one, and is exactly how the design
  keeps openness explicit without a new error path for the common case.
- `open` on a name already declared `open` earlier in the same module is
  `open-function-redeclaration`.
- `open` or a repeated open clause nested inside a block, function body, or
  any non-top-level position is rejected (`SyntaxError`): R20 does not
  support nested/local-scope open declarations (contract §3.1).
- `extend` targeting a name that is not `open` in the resolved module, or
  naming a module alias that was never imported, is rejected at parse/build
  time as `open-function-target-not-open` /
  `open-function-incompatible-contribution`.
- `use` naming a contribution alias that is a plain import with no matching
  contribution unit is `open-function-incompatible-contribution`.
- `use` naming the same contribution alias twice, or two aliases of the same
  cached module contributing to the same target, is
  `open-function-duplicate-selection`.
- Ordinary closed function definitions (plain identifier parameters, no
  `open`/`extend`/`use`) are completely unaffected; `IrFuncDef` is unchanged
  and no existing program is reinterpreted as open.

## 3. Core IR

Four new portable Core IR node types are added to
`PORTABLE_CORE_IR_NODE_TYPES` in `src/genia/ir.py`. No existing node type
changes shape. All four reuse the existing `IrCaseClause`/`IrPattern` family
verbatim — R20 adds no new pattern or guard representation.

```python
@dataclass
class IrOpenFuncDef(IrNode):
    """Open interface declaration: base unit's ordered clause list."""
    name: str
    clauses: list[IrCaseClause]       # each item's .pattern is an IrPatTuple
    docstring: str | None
    annotations: list[IrAnnotation] = field(default_factory=list)
    span: SourceSpan | None = None    # covers the declaring `open` clause


@dataclass
class IrOpenContribution(IrNode):
    """One contributing module's clause set targeting one open interface."""
    target_module_alias: str          # this module's own import alias
    target_name: str
    clauses: list[IrCaseClause]
    span: SourceSpan | None = None


@dataclass
class IrOpenUse(IrNode):
    """Explicit contribution selection producing one linked view."""
    local_name: str
    target_module_alias: str
    target_name: str
    contribution_module_aliases: list[str]
    span: SourceSpan | None = None
```

Notes:

- Each clause's fixed/varargs shape is derived, not stored redundantly: arity
  is `len(pattern.items)` (or the count preceding a trailing `IrPatRest`
  item), exactly as `match_lambda_pattern` already computes for lambdas.
  This avoids a second shape encoding that could drift from the pattern.
- Clause **lexical ordinal** within its unit is the list index — Core IR list
  order is the provenance ordinal, not a separately stored field, so no host
  side table is needed to recover it.
- **Declaring module identity** and **contribution-unit identity** are not
  stored as literal fields on the clause or unit node. They are structural:
  the declaring module is whichever module's IR tree contains the node (a
  property every host already tracks to run a module at all), and a
  contribution unit's identity is the pair (declaring module identity, target
  identity) recovered from `IrOpenContribution.target_module_alias` resolved
  through that module's own `IrImport` alias table at link time — exactly how
  `IrCall`/`IrVar` already resolve names through lexical/module lookup. This
  keeps the contract's "no host side table" requirement while adding zero new
  identity-carrying field.
- `IrOpenFuncDef.name` together with the declaring module's canonical module
  identity (the same identity `Env.load_module` already caches modules under)
  is the interface's portable key (contract §2.1). Import alias and file path
  never appear in this key.
- Grouped-vs-repeated equivalence is a **lowering** property, not a runtime
  property: both spellings produce the same `IrOpenFuncDef.clauses` list with
  each entry's own original span. A grouped clause using `|` still lowers each
  `|`-arm to its own `IrCaseClause` exactly as `IrCase` already does today, so
  a grouped clause simply contributes multiple `IrCaseClause` entries from one
  AST node while a repeated clause contributes one `IrCaseClause` entry per
  AST node; the merge into one `IrOpenFuncDef.clauses` list happens during AST
  lowering (§4), before any node becomes a separate top-level IR statement.
- `IrOpenUse` carries no clause data; it is a pure link instruction. It cannot
  execute a clause body and performs no evaluation beyond name resolution.

## 4. Lowering (AST → Core IR)

New AST nodes (`src/genia/ast_nodes.py`), mirroring the IR shapes 1:1:

```python
@dataclass
class OpenFuncDef(Node):
    name: str
    clauses: list[CaseClause]
    docstring: str | None
    span: SourceSpan | None = None

@dataclass
class OpenExtendDef(Node):
    target_module_alias: str
    target_name: str
    clauses: list[CaseClause]
    span: SourceSpan | None = None

@dataclass
class OpenUseDef(Node):
    local_name: str
    target_module_alias: str
    target_name: str
    contribution_module_aliases: list[str]
    span: SourceSpan | None = None
```

The parser itself performs the merge of repeated top-level clauses into one
AST node (tracking, per parse, the set of names already declared `open` and
the set of `(module_alias, name)` extend targets already opened in this
module) so that **lowering is a straight 1:1 map**, matching the existing
`lower_node` structure (`lower_program` stays `[lower_node(n) for n in
nodes]`; no AST-level grouping pass is added). This is the smallest change to
`lower_program`/`lower_node`: `OpenFuncDef` lowers to `IrOpenFuncDef` with
`clauses = [IrCaseClause(lower_pattern(c.pattern), lower(c.guard),
lower(c.result), span=c.span) for c in node.clauses]`, and the two other
nodes lower the same way as `IrOpenContribution`/`IrOpenUse`.

**Contiguity restriction (explicitly scoped-down for this release):** the
parser only merges clauses for one open interface (or one extend target) when
they form a contiguous run of top-level statements — i.e. once an `open`
clause is opened, every subsequent statement that is *not* another clause of
that same interface implicitly closes it for further un-annotated repetition;
writing a later bare `name(pattern...) = body` for a name that was open but
whose run was already closed is a rejected redeclaration-like error, not a
silent second interface. This is a deliberate minimality choice — the
contract requires deterministic grouping and does not require support for
clauses interleaved with unrelated statements. It matches every example in
the contract and roadmap, all of which write an open interface's clauses as
one contiguous run.

## 5. Runtime representation (informative — implemented in E20-3/E20-5)

Not part of the portable Core IR contract, but recorded here so E20-3/E20-5
implement exactly this and no more:

- `GeniaOpenFunction` — identity-bearing callable: `name`, declaring module
  id, ordered local `clauses` (pattern/guard/body/span/closure/ordinal).
  Called directly, it dispatches using only its own clauses as the single
  participating unit (contract §5 with exactly one unit).
- `GeniaOpenContributionUnit` — `target_interface_key`, declaring module id,
  ordered clauses/closure. Never callable by itself.
- `GeniaLinkedOpenFunction` — `base: GeniaOpenFunction`, `units: tuple[
  GeniaOpenContributionUnit, ...]` (immutable, selection order is not dispatch
  order). Implements the full contract §5 algorithm (shape stratum → per-unit
  first match → across-unit exactly-one-candidate). Duplicate detection
  (contract §6, structural dispatch-key over alpha-normalized pattern/guard
  with spans stripped) runs once when a unit (base or contribution) is built,
  not deferred to call time.

## 6. Compatibility with current grammar and Core IR

- No existing token, keyword, precedence, or production changes meaning.
  `open`, `extend`, `use` are recognized only as the first token of a fresh
  top-level statement, exactly where `import`/`pattern` already are, so
  `open`/`extend`/`use` remain ordinary identifiers everywhere else (call
  arguments, patterns, module member names, etc.).
- `IrFuncDef`, `IrCase`, `IrCaseClause`, `IrImport`, `IrLambda` and every
  other existing node are byte-for-byte unchanged.
- The four new node types are portable per §10 of the contract: no field
  requires a host dictionary, object address, or filesystem path; every
  identity is either structural (module-tree membership) or derived
  (list-index ordinal, pattern-derived arity).

## 7. Non-decisions carried forward

Consistent with the contract's non-goals: no priority/specificity annotation
syntax, no wildcard `use *`, no `extend` without a prior `import`, no
renaming on `use` (the linked view always binds under the interface's own
exported name), and no syntax for unloading/redeclaring/hot-swapping an open
interface.
