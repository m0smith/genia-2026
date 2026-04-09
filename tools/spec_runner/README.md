# Shared Spec Runner Contract

This directory defines the minimal contract future Genia hosts should implement to run shared spec cases.

This is a documentation scaffold in the current phase.
There is no generic multi-host runner implementation in the repo yet.

Browser playground note:

- browser runtime adapter docs are scaffolded under `docs/browser/`
- this does not add a second implemented host in the current phase
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
  - output: JSON representation of lowered Core IR
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

## Rules

- host-local transport details may vary
- JSON field naming should stay stable once shared fixtures depend on it
- host-local convenience wrappers must not replace the shared contract
- if the contract changes, update:
  - `spec/manifest.json`
  - `docs/host-interop/HOST_INTEROP.md`
  - `docs/host-interop/HOST_PORTING_GUIDE.md`
