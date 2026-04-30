# Composability Matrix

> **Status: PROPOSED / EXPLORATORY**
> This document is a design note only.
> It does not describe implemented behavior.
> See `GENIA_STATE.md` for actual behavior.

---

## Core Concept Matrix

| Concept | Composes With | How |
|---|---|---|
| file/source | module | contributes fragments |
| file/source | annotation | contains annotated declarations |
| file/source | execution mode | selected as input source |
| module | module | imports / re-exports |
| module | annotation | stores annotated definitions |
| module | lifecycle | provides hook scope |
| annotation | lifecycle | selects phase participants |
| lifecycle | execution mode | mode chooses lifecycle |
| unit test | annotation | consumes `@test`, setup/teardown |
| unit test | lifecycle | runs test phases |
| execution mode | file/source | chooses command / file / pipe / stdin |
| execution mode | module | loads / runs module context |

---

## Language Feature Matrix

| Feature | Composes With | Notes |
|---|---|---|
| values | patterns | patterns inspect and destructure values |
| values | functions | functions consume and produce values |
| values | modules | top-level values are module exports |
| functions | pipelines | functions are pipeline stages |
| functions | modules | definitions live in modules |
| functions | annotations | `@doc`, `@category`, etc. attach to named functions |
| functions | patterns | function heads are pattern-matched |
| functions | lifecycle | lifecycle phases call selected functions |
| patterns | values | patterns match against runtime values |
| patterns | functions | function heads can pattern-match |
| patterns | templates | templates define reusable structural patterns |
| flows | functions | `map` / `filter` / `each` consume functions as stages |
| flows | execution modes | `-p` binds stdin as a Flow |
| flows | lifecycle | `rows` mode runs begin / row / end phases over a Flow |
| rows mode | lifecycle | rows is an execution shape with ordered begin/row/end phases |
| refs/cells | actors | cells provide state substrate for actors |
| actors | messages | messages are plain Genia values |
| actors | modules | actor definitions live in modules |
| templates | contracts | contracts use templates to define boundary shapes |
| templates | patterns | templates express structural pattern constraints |
| modules | templates | modules export templates |
| modules | tests | test modules verify exported behavior |
| modules | annotations | annotations on module-level bindings are module metadata |
| annotations | unit test | `@test` (proposed) marks test cases for the test runner |
| annotations | lifecycle | annotations select participants for lifecycle phases |
| contracts | functions | contracts declare function input/output expectations |
| contracts | templates | contracts use templates for shape constraints |
| contracts | modules | contracts describe module boundaries |
| execution modes | lifecycle | each mode may invoke a different lifecycle |
| execution modes | file/source | each mode selects a source form |
| unit test | execution mode | test runner is a dedicated execution mode |

---

## Isolation Rules

| Feature | Must NOT compose with | Reason |
|---|---|---|
| annotation | execution logic | annotations are metadata only; no behavioral side-effects |
| execution mode | lifecycle phases | mode selects a lifecycle; it does not define phase logic |
| file/source | module scope | a file contributes code; it does not own the namespace |
| unit test | language syntax extension | tests are consumers, not language authors |
| lifecycle | source loading | lifecycle runs selected code; it does not resolve files |
| module | file loading strategy | the host loads files; a module is a runtime namespace |
