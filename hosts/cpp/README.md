# C++ Host — Pointer

**Status: pointer/scaffold only. No C++ implementation lives in this repository.**

As of R16 E16-6 (issue #763), the planned production C++ host lives in a separate repository: **[`m0smith/genia-cpp`](https://github.com/m0smith/genia-cpp)**. This directory is retained only so no duplicate, authoritative-looking C++ implementation ever exists in two repositories at once.

`genia-2026` remains the sole authority for the Genia language contract, Core IR portability boundary, shared specs (`spec/`), the generic conformance runner (`tools/spec_runner`), and the E16-1 host-adapter protocol (`tools/spec_runner/protocol.py`). `m0smith/genia-cpp` consumes that contract; it does not define it.

R16 bootstrapped `m0smith/genia-cpp` as a repository shell only. No real C++ interpreter is implemented in R16. The real C++ host implementation begins in **R24 — C++ Minimal Conforming Host**, after R21–R23 exact numeric releases complete, and happens entirely in `m0smith/genia-cpp`, not here. See `docs/strategy/roadmap/r21-r24.md`.

## What used to be here

Before E16-6, this directory was an empty template-derived placeholder based on `hosts/template/`. No C++ code, build tooling, or test scaffolding was added here. Nothing behavioral changed by that transition; only where the future implementation belongs.

## For a future Node.js/Java/Rust/Go host

The same repository-boundary model applies: a substantial production host belongs in its own dedicated repository once real implementation begins. In-repository planned-host scaffolds still use `hosts/template/`; once a substantial host moves to its own repository, its in-repository directory becomes a pointer/scaffold so semantic authority stays in `genia-2026`.
