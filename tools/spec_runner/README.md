# Shared Spec Runner Contract

This directory defines the minimal contract future Genia hosts should implement to run shared spec cases.

This is a documentation scaffold in the current phase.
There is no generic multi-host runner implementation in the repo yet.

Browser playground note:

- browser runtime adapter docs are scaffolded under `docs/browser/`
- this does not add a second implemented host in the current phase
- `spec/manifest.json` records no implemented browser runtime adapter hosts in this phase
- if adapter contract expectations change, update `spec/manifest.json` and relevant `docs/host-interop/*` docs in the same change

## Minimal Host Runner Interface

Each host should eventually expose a small interface equivalent to:

- `parse(source) -> AST JSON`
- `lower(source) -> IR JSON`
- `eval(source, stdin?, argv?) -> result JSON`
- `cli(args, stdin?) -> stdout/stderr/exit_code JSON`

Suggested normalized shapes:

- `parse(source)`:
  - input: source string
  - output: JSON representation of the host's parsed AST shape
- `lower(source)`:
  - input: source string
  - output: JSON representation of lowered minimal portable Core IR
  - optional host-local extension output may include a separate optimized IR payload, but it must not replace the minimal portable Core IR payload
- `eval(source, stdin?, argv?)`:
  - input:
    - source string
    - optional stdin string
    - optional argv string list
  - output:
    - result value JSON
    - stdout string
    - stderr string
    - normalized error object when evaluation fails
    - when a host implements allowlisted host interop, the same eval contract should expose normalized bridge behavior too:
      - host `None` returning as Genia `none`
      - explicit normalized host errors rather than silent success conversion
- `cli(args, stdin?)`:
  - input:
    - argv-like argument list
    - optional stdin string
  - output:
    - stdout string
    - stderr string
    - integer exit code
    - normalized error object when applicable

  Optional capability note:

  - hosts that implement optional capability bridges such as HTTP serving may validate those behaviors through host-local orchestration around `eval(...)` / `cli(...)` until a shared capability-driver contract is added


## Phase 2 Strictness, Normalization, and Error Contract

**The Python reference host enforces strict, deterministic, and unambiguous conformance as of Phase 2.**

- All observable outputs (runtime, CLI, errors) must be strictly normalized to canonical forms; no host-local or Python-specific leakage is allowed.
- Error objects must include required fields: category, message, and span (when applicable). Categories are strictly separated (parse/runtime/CLI).
- Malformed, missing, or unsupported cases must fail validation with explicit normalized errors; nothing is silently skipped.
- Output ordering and structure must be deterministic and stable.
- Only the minimal portable Core IR node families are used in lowering and output (see `docs/architecture/core-ir-portability.md`).
- CLI and flow behaviors must be strictly validated for output, error, and exit code normalization.
- GENIA_STATE.md is the final authority for implemented behavior; all specs and docs must align with it.

---

- host-local transport details may vary
- JSON field naming should stay stable once shared fixtures depend on it
- host-local convenience wrappers must not replace the shared contract
- host-local optimized IR must be surfaced as host-local/optional metadata, not as the shared minimal Core IR payload
- if the contract changes, update:
  - `spec/manifest.json`
  - `docs/host-interop/HOST_INTEROP.md`
  - `docs/host-interop/HOST_PORTING_GUIDE.md`
