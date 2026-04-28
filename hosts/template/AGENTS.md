# Host Template — Agent Guide

Status: scaffolded, not implemented

This directory is a **template**. Copy it to `hosts/<new-host>/` and replace all `TODO` markers with host-specific content. Do not treat this directory as an implemented host.

---

## Required Reading

Before working in any host directory, read these in order:

1. `AGENTS.md` (repo root)
2. `GENIA_STATE.md` (**final authority**)
3. `GENIA_RULES.md`
4. `GENIA_REPL_README.md`
5. `README.md`
6. `docs/host-interop/HOST_INTEROP.md`
7. `docs/architecture/core-ir-portability.md`
8. `spec/README.md`
9. `spec/manifest.json`
10. `tools/spec_runner/README.md`
11. Relevant core docs/specs for the capability area you are touching

See `docs/host-interop/HOST_PORTING_GUIDE.md` for the complete porting checklist.

---

## Rules

- Do not claim any capability as `Implemented` until code, tests, and shared spec coverage all exist.
- Do not redefine language behavior — shared docs/specs are authoritative.
- Do not update `GENIA_STATE.md` unless the new host changes shared observable behavior.
- Shared spec tests and shared docs win over host-local convenience.
