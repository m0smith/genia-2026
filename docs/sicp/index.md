# SICP with Genia

This section is a Head First–style, executable companion to SICP written against the real current Genia implementation.

If any chapter disagrees with implemented behavior, `GENIA_STATE.md` is the final authority.

## How To Use This Section

- read chapters in order if you want the full learning path
- jump by topic if you are filling a specific gap
- trust the `Reality Check` section in each chapter over wishful interpretation
- treat runnable `genia` blocks as executable truth, not decoration

## Published Chapters

### Part I — Building Abstractions with Procedures

- [01. Elements of Programming](01-elements-of-programming.md)
- [02. Procedures and Processes](02-procedures-and-processes.md)
- [03. Higher-Order Procedures](03-higher-order-procedures.md)

### Part II — Building Abstractions with Data

- [04. Data Structures](04-data-structures.md)
- [05. Pattern Matching](05-pattern-matching.md)
- [06. Symbolic Data](06-symbolic-data.md)
- [07. Generic Operations](07-generic-operations.md)

### Part III — Flow, Time, and State

- [08. Pipelines and Flow](08-pipelines-and-flow.md)
- [09. Absence and Option Semantics](09-absence-and-option-semantics.md)
- [10. State and Identity](10-state-and-identity.md)
- [11. Concurrency](11-concurrency.md)
- [12. Laziness and Streams](12-laziness-and-streams.md)

### Part IV — Metalinguistic Abstraction

- [13. Code as Data](13-code-as-data.md)
- [14. Evaluators](14-evaluators.md)
- [15. Language Variations](15-language-variations.md)

### Part V — Implementation and Runtime

- [16. Core IR](16-core-ir.md)
- [17. Tail Calls and Runtime](17-tail-calls-and-runtime.md)
- [18. Machines and Compilation](18-machines-and-compilation.md)

## Validation Contract

- runnable `genia` blocks are validated by `tests/test_sicp_code_blocks.py`
- every runnable block must be followed immediately by an expected-output block
- illustrative-only Genia snippets must use the approved marker `**Illustrative** — not runnable`
- each runnable block executes in a fresh environment, so examples must be self-contained

## Current Scope

### ✅ Published now

- the full chapter skeleton from `OUTLINE.md`
- runnable examples only for currently implemented Genia behavior
- explicit labeling where a SICP concept is only partial or still future work

### ⚠️ Partial

- several later chapters are intentionally short and status-heavy because the corresponding Genia surface is still partial or scaffolded

### ❌ Not included

- imaginary syntax
- alternative conditionals such as `if`
- Python-host-only behavior taught as if it were portable Genia law
