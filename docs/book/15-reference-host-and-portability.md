# Chapter 15: Reference Host and Portability

Genia currently has one implemented host: Python.

This repository now also includes shared portability scaffolding so future hosts can stay aligned with the same language semantics instead of inventing host-local behavior.

Current shared portability artifacts:

- `docs/host-interop/HOST_INTEROP.md`
- `docs/host-interop/HOST_PORTING_GUIDE.md`
- `docs/host-interop/HOST_CAPABILITY_MATRIX.md`
- `docs/architecture/core-ir-portability.md`
- `spec/README.md`
- `spec/manifest.json`
- `tools/spec_runner/README.md`
- `hosts/README.md`

These files do **not** mean that a Node.js, Java, Rust, Go, or C++ host is already implemented.
They define the shared contract and repository layout for future work.

Browser playground status in this phase:

- architecture and adapter-contract docs are scaffolded under `docs/browser/`
- V1 browser execution is planned to use the Python reference host on a backend service
- browser-native execution (JavaScript host or Rust/WASM host) is planned later behind the same adapter boundary
- this does not add a second implemented host today

## Minimal example

Today the Python reference host is still the real executable host:

```bash
python3 -m genia.interpreter -c '1 + 2'
```

Expected result:

- evaluates with the current Python host
- uses the same Core IR lowering/runtime semantics described in `GENIA_STATE.md`

## Edge case example

The shared host contract includes current CLI pipe behavior, not just expression evaluation:

```bash
printf 'a\nb\n' | genia -p 'head(1) |> each(print)'
```

Expected result:

- prints only `a`

Future hosts that implement pipe mode should preserve that same documented behavior.

## Failure case example

The pipe-mode wrapper contract is part of the shared host contract:

```bash
genia -p 'head(1) |> each(print) |> run'
```

Expected behavior:

- clear failure because pipe mode already injects `run`

This matters for portability because future hosts must preserve the documented CLI contract, not reinterpret it.

## ✅ Implemented

- Python reference host
- shared host-interop docs
- shared spec manifest/scaffolding
- placeholder host directories with status notes and local agent guidance

## ⚠️ Partial

- repository layout is transitional:
  - the working Python host still lives at the repo root rather than `hosts/python/`
- shared spec runner support is documented, but not implemented as generic tooling yet
- capability coverage for future hosts is planned and tracked, not implemented

## ❌ Not implemented

- Node.js host
- Java host
- Rust host
- Go host
- C++ host
- direct/native Genia host
- generic multi-host spec runner implementation

## The Rule Going Forward

Future hosts may use different internal parsers, runtimes, or execution strategies.

They must still preserve:

- shared Core IR meaning
- shared runtime semantics
- shared CLI behavior
- shared public prelude behavior
- shared documentation and spec truth
