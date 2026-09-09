# C++ Host — Pointer

**Status: pointer/scaffold only. No C++ implementation lives in this repository.**

As of R16 E16-6 (issue #763), the planned production C++ host lives in a
separate repository: **[`m0smith/genia-cpp`](https://github.com/m0smith/genia-cpp)**.
This directory is retained only so no duplicate, authoritative-looking C++
implementation ever exists in two repositories at once.

`genia-2026` remains the sole authority for the Genia language contract,
Core IR portability boundary, shared specs (`spec/`), the generic
conformance runner (`tools/spec_runner`), and the E16-1 host-adapter
protocol (`tools/spec_runner/protocol.py`). `m0smith/genia-cpp` consumes
that contract; it does not define it. See
`docs/design/r16-multi-host-conformance-infrastructure-contract.md` and
`docs/strategy/roadmap/multi-host-conformance-policy.md`.

R16 bootstraps `m0smith/genia-cpp` as a repository shell only (its own
`README.md`/`AGENTS.md`, a pinned `genia-2026` contract revision + E16-1
protocol version declaration, and a minimal protocol-participation
placeholder) — **no real C++ interpreter is implemented in R16**. The real
C++ lexer/parser/evaluator bring-up is R20 (`docs/strategy/roadmap/
r16-r20.md`), and happens entirely in `m0smith/genia-cpp`, not here.

## What used to be here

Before E16-6, this directory was an empty template-derived placeholder
(`README.md`/`AGENTS.md` copied from `hosts/template/`, stating "planned,
no host implementation exists yet"). No C++ code, build tooling, or test
scaffolding was ever added here. Nothing behavioral changed by this
transition — only where the *future* implementation belongs.

## For a future Node.js/Java/Rust/Go host

The same repository-boundary model applies: a production host for any of
`hosts/node/`, `hosts/java/`, `hosts/rust/`, `hosts/go/` belongs in its own
dedicated repository once real implementation begins, following the same
pattern `m0smith/genia-cpp` establishes. Those directories remain
unchanged placeholders until that decision is made for each host.
