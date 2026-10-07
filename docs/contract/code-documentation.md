# Maintained Code Documentation Contract

Status: Proposed policy contract for issue #1101; requires review before enforcement.
Scope: maintained first-party code in m0smith/genia-2026 and m0smith/genia-cpp.

## Authority and purpose

This contract defines documentation obligations, not Genia language behavior.
GENIA_STATE.md remains final authority, followed by GENIA_RULES.md,
GENIA_REPL_README.md and README.md under AGENTS.md. Source documentation must
describe implemented behavior and verified boundaries. It must not turn design
intent, another host's implementation, or roadmap placement into a semantic claim.

The existing Genia @doc style guide remains authoritative for annotation format.
This policy extends maintained-code scope without weakening the existing strict
public-prelude and host-builtin requirements.

A reader must be able to understand a substantial binding's caller contract
without reconstructing it by tracing its callees. Annotation presence alone
does not establish documentation quality.

## Maintained scope

The policy covers applications, runtime, libraries/prelude, host adapters,
tooling, scripts, editor extensions, maintained examples and fixtures, tests,
and executable build/CI configuration in both repositories.

Each maintained module/file must have discoverable documentation of its purpose
and important boundaries. A short header suffices where the role is simple.
Executable configuration must explain consequential assumptions and unusual
steps; function documentation rules apply only when it actually defines functions.

Generated code must identify its generator or governed source and the supported
update path. Generated binding documentation belongs in that source/generator.
Mixed files retain coverage for their handwritten regions. Vendored third-party
code and immutable historical archives are excluded from first-party binding
coverage, with provenance and classification recorded. Maintained first-party
code cannot become exempt merely by being moved into an archive/vendor directory.

## Binding obligations

Document public/exported APIs and entry points, including their supported use
and caller-visible failures. Document substantial internal functions, methods,
classes/types, and callbacks regardless of visibility or name.

A binding is substantial when understanding its contract requires knowledge of
one or more of these concerns:

- validation, normalization, nontrivial branching or composition;
- absence, failure, exception, diagnostic or recovery behavior;
- external IO, mutation, authority, or other side effects;
- protocol/data representation, host boundary or compatibility behavior;
- laziness, demand, cancellation, lifetime, ownership, or concurrency;
- a domain invariant or surprising precondition/result.

Size alone is not the criterion. A one-line host callback can be substantial.
Internal names, underscore prefixes and internal metadata do not automatically
exempt substantial behavior.

A short, obvious pure helper may use concise documentation. Omitting its binding
documentation requires an explicit exemption explaining why its name/signature
and local context expose its full contract. Existing stricter public-surface
rules take precedence over this allowance. Exemptions identify the binding and
reason, remain reviewable, and are reconsidered when its behavior changes.
Exemptions cannot cover whole maintained subsystems or serve as undocumented debt.

## Required content

Documentation begins with a concrete behavioral summary. Include the following
when relevant:

- input meaning, accepted forms, units and important preconditions;
- return/result shape, ordering, absence and ownership;
- failures, exceptions, diagnostics and invalid-input behavior;
- side effects and the resources or authority used;
- lazy/single-use behavior, bounded demand and termination;
- mutation, state transitions, lifetime and concurrency guarantees;
- host-only scope, unsupported boundaries and compatibility differences.

Omit sections that add no information. Avoid restating the name, signature or
body. Document surprising implementation rationale beside the relevant code;
keep the caller contract at the binding. Shared context/data contracts may be
documented once with discoverable references rather than copied into every helper.

Examples are required when an important call shape or boundary would otherwise
remain ambiguous. Any runnable example must use implemented syntax and have
appropriate existing or added executable verification during its change phase.
Documentation must not claim security, portability or coverage beyond evidence.

## Native documentation forms

| Maintained code | Contract form |
|---|---|
| Genia | Attached @doc using docs/style/doc-style.md; existing public @category requirements remain |
| Python | Module/class/function/method docstrings; adjacent comments for implementation rationale |
| C++ | Declaration-associated documentation comments; public contract at declaration, internal contract at definition where appropriate |
| TypeScript/JavaScript | Declaration-associated JSDoc/TSDoc-compatible comments |
| Shell/other scripts | Header and function-associated comments covering inputs, output, exit status and side effects where relevant |
| Build/CI configuration | Purpose/boundary comments for consequential non-obvious configuration and steps |

Ordinary existing C++ comments may already satisfy the quality requirement.
Any mechanical convention selected during design must support deliberate
migration without claiming that absence of Doxygen markers means absence of prose.
This contract does not require installing a documentation publishing framework.

## Tests and fixtures

Tests must make their asserted behavior/invariant discoverable through descriptive
names and, where necessary, concise documentation. Explain non-obvious setup,
host dependence, unusual fixtures, timing/resource assumptions and boundaries
of evidence. Test helpers and fixtures with substantial behavior follow the
binding obligations. Clear trivial tests need no redundant per-test docstring.
Do not annotate every assertion or duplicate executable expectations in prose.

Portable semantic authority remains in the governed contracts/shared specs.
Python-host tests and native tests retain their existing scope and labels.

## Coverage, legacy debt and change obligations

New maintained code must meet this policy. Changes to a required binding must
bring that binding's documentation into compliance in the same change, even if
its gap was previously baselined. Unrelated legacy debt can remain tracked.

Existing gaps must be inventoried with stable binding identities, subsystem,
reason and disposition. A baseline represents temporary debt, not an exemption.
CI must reject newly introduced gaps and stale baseline entries. Removing one
gap cannot offset introducing a different gap. Moves/renames must not hide debt
or exempt changed behavior; identity/matching mechanics belong to design.

Existing strict prelude/builtin checks must continue independently and cannot
be relaxed into the legacy baseline. All maintained languages must have an
explicit enforcement approach before cross-repository rollout is called complete.
Unsupported checker cases must be reported and tracked, not silently treated as
documented.

Generated/vendor/archive classifications and exemptions must remain reviewable.
A baseline change cannot redefine maintained scope without review.

Mechanical checks establish coverage and format, not semantic correctness.
Review must check usefulness, accuracy and consistency with authority and tests.
A superficial summary is a documentation defect even when a checker accepts it.

## Synchronization and phase boundaries

Contributor and agent guidance must require this policy and retain the existing
source-of-truth order. Documentation and implementation change together when a
binding's behavior changes. Keep the four core docs up to date as appropriate;
source-doc cleanup must not invent language changes.

Evaluate MCP language-knowledge impact for each change. This policy itself changes
no genia_language_profile fact or MCP surface. Preserve generated profile regions
and their generator checks during later MCP remediation.

Enforcement design, checker fixtures, implementation, source remediation and CI
rollout are subsequent gated work. This contract defines their required outcomes;
it contains no test implementation or checker architecture.

Initial policy/enforcement is required infrastructure after R28 and before new
R29 implementation, coordinated with the unnumbered R20 follow-up. Existing-code
remediation proceeds in bounded slices alongside roadmap work. The entire legacy
backlog does not block R29. Parent #1101 stays open until maintained areas meet
the policy or have justified explicit exemptions and the rollout has been audited.

## Non-goals

No language syntax, runtime semantics, Core IR, protocol, capability or host-parity
change. No bulk refactor, universal verbosity quota, automatic exemption for
internal code, hand edits of generated/vendor code, or second semantic authority.
