# Parse Fixture Schema (for shared contract)

Each parse fixture must be a YAML file with one of the following shapes:

## Valid parse case
```yaml
id: <unique-id>
source: <genia-source-string>
expect_ast:
  <normalized-contract-ast>
```

## Invalid parse case
```yaml
id: <unique-id>
source: <genia-source-string>
expect_error:
  type: <error-type>
  message: <error-message>
```

- Only contract-required fields are asserted.
- Do not snapshot full ASTs if a smaller contract projection suffices.
- Do not depend on host-local details or error formatting.