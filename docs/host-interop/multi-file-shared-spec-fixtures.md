# Portable Multi-File Shared-Spec Fixtures

Status: **Implemented conformance-infrastructure contract.** This format
transports existing module semantics; it does not define them. `GENIA_STATE.md`
remains final authority.

## Case input

Eval and error cases use either the existing single-file form:

```yaml
input:
  source: "1 + 1"
```

or a multi-file form:

```yaml
input:
  modules:
    entry: main.genia
    files:
      - path: base.genia
        source: |
          open get("mem", store, key) = key
      - path: main.genia
        source: |
          import base
          base.get("mem", 0, "k")
```

`source` and `modules` are mutually exclusive. A normalized case still has one
entry source: the exact `source` belonging to `modules.entry`. Existing
single-file inputs normalize exactly as before and carry no module fixture.

## Normalization and identity

- `modules` has exactly `entry` and `files`.
- `entry` and every file `path` are non-empty portable logical paths using `/`.
- A logical path is relative, has a `.genia` suffix, and contains only non-empty
  components other than `.` or `..`. Backslashes, absolute paths, drive-like
  prefixes, NUL, and empty components are rejected.
- Each file has exactly `path` and string `source`; paths are unique.
- `entry` names exactly one file.
- File order is normalized lexicographically by logical path. This stabilizes
  transport and cannot determine import or contribution-selection order, which
  remains established by Genia source.
- Logical file identity is the normalized path. Module names continue to follow
  the existing module contract; the fixture adds no alternate naming rule.

Malformed fixtures are shared-spec load errors. They are not Genia evaluation
diagnostics and never reach a host.

## Adapter request

The R16 `eval` request retains `source`, `stdin`, and `argv`. A multi-file case
also carries the normalized fixture verbatim:

```json
{"source":"<entry source>","stdin":null,"argv":null,"modules":{"entry":"main.genia","files":[{"path":"base.genia","source":"..."},{"path":"main.genia","source":"..."}]}}
```

The fixture contains no host path. An adapter may use a virtual module source,
a sandbox, or private temporary storage, but that realization and its paths are
not observable fixture semantics. The entry executes with its logical identity
so relative module resolution has the same language meaning in every host.

The fixture is available only to eval/error shared cases in this slice. Every
R20 multi-file case declares `requires: [open_functions]`; normal R16 capability
gating reports it `unsupported` without invocation when that capability is not
declared `supported`.
