# Genia Shared Spec (Phase 1)

## Supported Categories (Phase 1)
- parse
- lower
- eval
- cli
- errors

## Case File Format
- Format: JSON
- Required fields: `id`, `category`, `expect`
- Optional fields: `source`, `stdin`, `argv`, `description`, `tags`
- Example:

```json
{
  "id": "simple-add",
  "category": "eval",
  "source": "1 + 2",
  "expect": { "result": 3 }
}
```

## How Cases Are Loaded
- Only manifest-driven loading is supported in phase 1.
- Add new cases by listing them in `spec/manifest.json`.
- Directory scanning is NOT supported.

## Shared vs Host-Local
- Shared: Case schema, normalized output, error object, assertion rules.
- Host-local: Python adapter code, normalization helpers, CLI wrappers, test integration.

## Limitations
- Only Python host is implemented.
- Multi-host and cross-runtime support is NOT present.
- Shared spec execution is partial/experimental.
- Flows, async, and advanced IR are out of scope.
