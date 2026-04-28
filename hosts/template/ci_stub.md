# CI Configuration Stub

CI setup is host-language-specific. This stub defines the required contract only.

See `docs/host-interop/HOST_PORTING_GUIDE.md` §Test Checklist for the full documentation requirement.

---

## Required CI Jobs

Every host must pass these two CI jobs on every push and pull request:

### 1. shared-spec-runner

Run the shared spec runner and assert exit code 0.

```
Command:  python -m tools.spec_runner
Assert:   exit code 0
Trigger:  on every push / PR
```

Do not merge a PR that fails the shared spec runner.

### 2. host-local-tests

Run the host-language test suite and assert exit code 0.

```
Command:  TODO (replace with the host-language test runner, e.g. `go test ./...`)
Assert:   exit code 0
Trigger:  on every push / PR
```

---

## Setup Steps

TODO: describe host-language environment setup for CI (e.g. install runtime version, install dependencies).

Example structure:

```
- name: Set up <language>
  uses: actions/setup-<language>@v...
  with:
    <language>-version: 'x.y.z'

- name: Install dependencies
  run: TODO
```

---

## Notes

- Do not claim a capability as `Implemented` until both CI jobs pass for that capability.
- Keep the shared spec runner job separate from the host-local job so failures are easy to diagnose.
- The shared spec runner requires Python — add a Python setup step even for non-Python hosts.
