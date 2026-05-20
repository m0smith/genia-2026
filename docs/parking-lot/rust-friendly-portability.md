# Rust-Friendly Portability and Safety Ideas

Status: **Parking lot / non-authoritative**

This note captures future ideas only. It does not define implemented Genia behavior.
If this conflicts with `GENIA_STATE.md`, `GENIA_STATE.md` wins.

## Why this exists

Rust-oriented users are likely to value:

- explicit semantics
- predictable resource behavior
- strong host boundaries
- portable contracts
- performance discipline
- trustworthy tooling

Genia should not copy Rust syntax or become Rust-like for its own sake. The useful goal is to make Genia's contracts explicit enough that a future Rust host can implement them without inventing behavior.

## Ideas to preserve

### Host capability boundary

Future host work should keep a clear split between:

```text
Genia semantics
Host capability adapter
OS/runtime effect
```

Candidate capability families:

- file access
- stdin/stdout/stderr
- process exit code bridge
- clock/time
- randomness
- HTTP serving
- host-backed Flow/Seq sources
- parser/evaluator entry points while Python remains the reference host

### Resource ownership vocabulary

Genia may eventually need precise language for:

- owned source
- borrowed source
- reusable Seq
- single-use Seq
- consumed Flow
- finalized resource

This should support Seq/Flow behavior without importing Rust borrow-checker syntax.

### Outcome boundary discipline

Keep this distinction sharp:

```text
some(value)          success with presence
none(context?)       success with absence
err(reason, ctx?)    recoverable failure
runtime error        misuse / contract violation / broken invariant
```

### Zero-copy / view semantics

Future value-template and Sheet work should clarify when operations:

- copy data
- create validated views
- share columns
- materialize derived results
- preserve laziness

### Future Rust/WASM host roadmap

A future Rust path might be staged as:

```text
1. Rust host consumes portable Core IR subset.
2. Rust host passes small shared eval/IR specs.
3. Rust host adds embedded/runtime adapter surface.
4. Rust/WASM host supports browser playground experiments.
5. Performance-sensitive Seq/Sheet operations move behind portable contracts.
```

## Non-goals for now

Do not add merely for Rust appeal:

- borrow-checker syntax
- lifetimes
- `unsafe` blocks
- Rust trait syntax
- static type system
- Rust host implementation
- performance promises without benchmarks

## Promotion trigger

Promote this note into a pre-flight only when one of these becomes active work:

- host capability contract hardening
- Rust host adapter spike
- Rust/WASM playground runtime
- resource lifecycle contract for Seq/Flow
- zero-copy/view semantics for Sheets or value templates
