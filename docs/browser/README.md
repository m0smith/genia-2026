# Browser Playground Docs

This folder documents the planned browser playground architecture for Genia.

Current status:

- Implemented now: architecture and contract documentation only.
- V1 runtime plan: browser UI with the current Python reference host running on a backend service.
- Later plan: browser-native runtime using a JavaScript host or a Rust/WASM host behind the same adapter contract.

The browser playground work is a host-capability adaptation layer.
It is not a separate Genia dialect, and it does not change Genia language semantics.

Related shared host docs:

- docs/host-interop/HOST_INTEROP.md
- docs/host-interop/HOST_PORTING_GUIDE.md
- docs/host-interop/HOST_CAPABILITY_MATRIX.md
- docs/architecture/core-ir-portability.md
- spec/README.md
- spec/manifest.json
- tools/spec_runner/README.md

See also:

- docs/browser/PLAYGROUND_ARCHITECTURE.md
- docs/browser/RUNTIME_ADAPTER_CONTRACT.md
