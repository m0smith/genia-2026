# C++ Host AGENTS — Pointer

**No C++ implementation exists in this repository.** The planned production
C++ host repository is [`m0smith/genia-cpp`](https://github.com/m0smith/genia-cpp)
(bootstrapped as a repository shell only in R16 E16-6, issue #763; the real
C++ implementation is R20, entirely in that repository).

If you are working on the C++ host, use `m0smith/genia-cpp`'s own
`AGENTS.md`, not this file. That repository's rules require it to:

- read the `genia-2026` docs it consumes as authoritative and never fork
  or redefine them: `GENIA_STATE.md`, `GENIA_RULES.md`,
  `GENIA_REPL_README.md`, `docs/host-interop/*`, `spec/manifest.json`,
  `docs/architecture/core-ir-portability.md`
- declare an exact pinned `genia-2026` contract revision and E16-1
  adapter-protocol version, and update that declaration deliberately, not
  silently
- stop and clarify the contract upstream in `genia-2026` rather than
  guessing at ambiguous portable behavior from Python implementation
  details

This directory (`hosts/cpp/` in `genia-2026`) is retained only as a
pointer so no duplicate, authoritative-looking C++ implementation exists
in two repositories at once. See `hosts/cpp/README.md` and
`docs/design/r16-multi-host-conformance-infrastructure-contract.md`.
