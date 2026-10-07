# Checking maintained code documentation

The [policy](../contract/code-documentation.md) covers maintained first-party code
in both repositories. The [design](../design/code-documentation-enforcement.md)
explains declaration discovery and legacy debt. Coverage establishes presence;
reviewers must verify contract quality and truth.

## Run the checker

```sh
uv run python -m tools.code_documentation --base-ref origin/main
uv run python -m tools.code_documentation --inventory inventory.json
uv run pytest -q tests/unit/test_code_documentation.py
```

For the C++ checkout, run the canonical checker from genia-2026:

```sh
uv run python -m tools.code_documentation --root ../genia-cpp --base-ref origin/main
```

The target repository resolves its own base ref. C++ CI pins the checker provider
separately from the host's semantic contract revision; it changes neither build
nor runtime dependencies.

## Baseline and exemptions

`.github/code-documentation-baseline.json` records existing gaps by declaration
identity and source fingerprint. Document a binding, then remove its resolved
entry. New identities or changed fingerprints cannot be added against the PR
base. The explicit bootstrap flag refuses to overwrite an existing baseline;
initial rollout is compared against target-branch source to prevent hiding new
code in a first baseline.

`.github/code-documentation.json` records classifications and justified,
fingerprint-specific exemptions. New classifications/exemptions need a separately
reviewed policy change; routine remediation cannot silently broaden them.
A checker error or unsupported syntax is an explicit finding, not coverage credit.

Public prelude/builtin lint and generated-reference checks remain independent.
Generated-language-profile regions are regenerated from their governed source;
MCP remediation must preserve `tools/gen_mcp_language_profile.py --check`.

## Remediation order and completion

MCP source contracts are the first slice. Continue through Python host boundaries,
Python runtime and Genia libraries, C++ runtime/adapters, tooling/scripts/editor
extension/examples/fixtures, and tests/build configuration. Each slice updates
its baseline, runs focused validation, and receives prose-quality review.
The issue remains open while legacy debt remains; a passing gate means no new
unresolved debt, not that every existing function is documented.

The checker does not decide whether prose is exemplary, prove exception coverage,
or establish portability. In particular, existing C++ comments remain useful
contracts even without Doxygen syntax, and descriptive test names can explain
straightforward test behavior without redundant docstrings.

## Initial rollout status (#1101)

The initial inventory records 3,950 accepted legacy findings in genia-2026 and
379 in genia-cpp. Findings include module-purpose gaps, declaration-documentation
gaps and explicit parse/unsupported cases; these are not 4,329 independently
verified semantic defects. The baseline is an actionable debt inventory, not an
exemption or a claim that existing prose has passed quality review.

MCP source now has contracts for its named functions/pattern, plus the important
handwritten descriptor/profile values. Native protocol and host callbacks remain
unchanged. Python host-boundary remediation and the remaining subsystem slices
are still required before closing #1101. C++ rollout requires its separate PR
and the canonical checker provider commit to be available.
