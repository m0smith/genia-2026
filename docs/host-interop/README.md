# Host Interop Docs

Architecture planning distinguishes the capability registry, host support,
program authority, and semantic surface. See
[`../architecture/host-capability-taxonomy.md`](../architecture/host-capability-taxonomy.md)
and the not-implemented
[`../architecture/external-process-execution.md`](../architecture/external-process-execution.md)
record.

This folder holds the shared portability contract for Genia's future multi-host work.

> **Terminology — two distinct concerns, do not conflate them:**
>
> - **Host interop** (this folder): the *multi-host portability* contract. The
>   same Genia program must produce the same observable semantics on any
>   conforming host implementation (Python today; Node, Java, Rust, Go, C++
>   planned). Success means "runs identically on host X and host Y." It is
>   defined by Core IR + the shared `spec/` suite + `GENIA_RULES.md`, and proven
>   through the generic conformance runner (`tools/spec_runner --host`).
>
> - **FFI** (a *separate* concern): calling host-language code *from* Genia —
>   e.g. the allowlisted `import python` / `import python.json` bridge. FFI is
>   how a program reaches *into* the host it happens to run on, so a program that
>   uses it is host-specific by construction. FFI therefore always carries a
>   portability label (today: **Python-host-only**, allowlisted) and is **not**
>   part of the portability contract above. Its authoritative contract lives in
>   `GENIA_STATE.md` §4.1 (currently titled "Python host interop layer" — the
>   FFI layer) and is summarized in `HOST_INTEROP.md` under "Host FFI Bridge".
>
> The two pull in opposite directions on purpose: host interop makes programs
> host-independent; FFI lets a program depend on a specific host. Keep the terms
> separate in docs and analysis.

Current status in this phase:

- Python is the full-language reference host; C++ is the bounded R24 production host.
- The files in this folder define shared guidance and scaffolding for future hosts.
- They do not imply that Node.js, Java, Rust, or Go hosts already exist, or that
  C++ implements behavior beyond its declared R24 floor.

Start here:

- `capabilities.md` for the formal per-capability contract (name, Genia surface, input, output, errors, portability status)
- `HOST_INTEROP.md` for the cross-host semantic contract
- `HOST_PORTING_GUIDE.md` for the practical checklist when adding a host
- `HOST_CAPABILITY_MATRIX.md` for current/planned host capability status

For architecture background, also read:

- `docs/architecture/core-ir-portability.md`
- `spec/README.md`
- `tools/spec_runner/README.md`
