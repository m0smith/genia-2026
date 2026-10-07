# Maintained Code Documentation Enforcement

Design for #1101; implements the obligations in
[`code-documentation.md`](../contract/code-documentation.md).
This is development infrastructure, not Genia semantics.

## Architecture

One checker in `tools/code_documentation.py` inventories tracked first-party
files and discovers declarations using Python AST, the native Genia parser,
and pinned Tree-sitter grammars for C++, JavaScript/TypeScript, shell and the maintained Rust component. Existing Genia
style and public-surface checks remain independent and strict. Anonymous
callbacks are covered by their enclosing binding; named callback assignments
are inventoried when the grammar exposes them. Parser failures become explicit
findings rather than coverage credit.

Source files need a module purpose, substantial declarations need associated
documentation. For conservative mechanical enforcement, named production
functions/classes are required unless explicitly exempted. Descriptive test
functions may satisfy the test obligation through their names; test helpers
remain covered. Humans review semantic quality and surprising test setup.

The checker emits an inventory and findings with path, language, binding,
kind, source fingerprint and reason. Baseline records are temporary debt:
an exact finding identity and fingerprint can remain, but changed/new findings
fail. Resolved findings still listed in the baseline fail. Paths participate
in identity, so moves require deliberate review and never pass silently.
Baseline updates in pull requests may remove entries; additions or changed
fingerprints fail against the target-branch baseline. New/changed code must
be documented rather than automatically refreshed into the baseline.

## Classification and exemptions

Tracked files are the discovery boundary. First-party source, build and workflow
files are maintained. Third-party and generated/archive classifications are
explicit, reasoned records in the repository manifest. Generated regions in
mixed files remain visible; handwritten declarations stay covered.
Binding exemptions carry a reason and exact source fingerprint, invalidating
on change. The checker rejects unused exemptions. No underscore/internal-name
blanket exemption exists. Empty Python package markers need no invented purpose.

Module-purpose checks for build/workflow configuration establish presence of
explanatory comments; reviews remain responsible for consequential assumptions.
Unsupported executable file types must be surfaced in the inventory.

## Interfaces and repository distribution

CLI accepts `--root`, `--manifest`, `--baseline`, optional `--base-ref`, and
`--inventory`. An explicit `--write-baseline` is initial bootstrap only, never
a CI repair. JSON records use schema version 1 and sorted deterministic identities.
Errors exit nonzero; reports distinguish accepted legacy debt from new failures.

Each repository owns its manifest and baseline. C++ CI checks out the canonical
checker at an explicitly pinned genia-2026 revision and runs it against its own
checkout. Do not copy Python/Genia semantics into C++; this development checker
does not enter the C++ build or runtime path. Dependency pins belong to the
canonical development environment. Coordinate rollout before calling both gates
operational; an unmerged provider revision is explicitly pending review.

## File and verification plan

Add checker, dedicated host-tooling tests, manifests/baselines and focused CI.
Update policy links, agent instructions, core-doc process note, roadmap and
usage documentation in the documentation phase. Native MCP annotations are the
first remediation slice, verified by existing MCP tests and generator checks.

Checker fixtures cover missing/valid docs in every maintained source language,
parser errors, nested/helper coverage, annotations, baseline identity changes,
changed bindings, stale debt/exemptions, rename rejection and target-baseline
expansion. No shared Genia semantic evidence is introduced by this tooling.

## Rollout and limits

Initial bootstrap inventories existing gaps honestly. Source remediation reduces
the baseline in independent slices; baseline presence is not a quality verdict.
Full parent completion requires remediation/audit across maintained areas.
Mechanical presence checks cannot prove prose correctness, ownership claims or
the completeness of documented exception cases. Required review supplies that
part of the contract.
