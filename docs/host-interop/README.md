# Host Interop Docs

This folder holds the shared portability contract for Genia's future multi-host work.

Current status in this phase:

- Python is the only implemented host.
- The files in this folder define shared guidance and scaffolding for future hosts.
- They do not imply that Node.js, Java, Rust, Go, or C++ hosts already exist.

Start here:

- `HOST_INTEROP.md` for the cross-host semantic contract
- `HOST_PORTING_GUIDE.md` for the practical checklist when adding a host
- `HOST_CAPABILITY_MATRIX.md` for current/planned host capability status

For architecture background, also read:

- `docs/architecture/core-ir-portability.md`
- `spec/README.md`
- `tools/spec_runner/README.md`
