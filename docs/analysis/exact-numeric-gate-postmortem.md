# Exact Numeric Gate Decomposition Postmortem

Status: planning/process record. This document changes no Genia language or runtime behavior. `GENIA_STATE.md` remains final authority for implemented behavior.

Related work: issue #838, PR #839, repair issues #840-#844, planning issue #845.

## Decision

PR #839 will not be merged as the implementation vehicle for the Exact Numeric Model.

The semantic exploration remains valuable evidence, but the branch became too large and too cross-cutting to be a safe release prerequisite. Exact numeric work is therefore decomposed into numbered releases before the C++ host begins:

- R21 — Numeric Source and Portable Representation
- R22 — Exact Numeric Runtime
- R23 — Numeric Representation and Interchange
- R24 — C++ Minimal Conforming Host

Later planned releases shift by three release numbers.

## What happened

Issue #838 was opened as a separately gated prerequisite for the C++ host rather than as a numbered release. Its approved contract covered, in one gate, source numeric classification, portable Core IR payloads, Decimal/Rational/Float64 runtime values, exact arithmetic, conversions, equality and map keys, canonical rendering, JSON boundaries, formatting, diagnostics, compatibility hardening, documentation, and final audit.

PR #839 consequently accumulated dozens of commits and broad changes across parser/lexer, Core IR fixtures, evaluator, equality, formatting, JSON, retrieval, Sheets, compatibility callers, shared specs, unit tests, and authoritative documentation.

The closing audit sequence then demonstrated the integration risk directly. The first skeptical audit found multiple semantic blockers. Repair issues #840-#842 addressed those. A later fresh audit found an additional metacircular quoted-pattern regression that prior tests had not exposed, requiring #844 before the gate could be re-audited.

The work showed that the design is feasible. It also showed that the chosen delivery unit was too large.

## Root cause

The planning mistake was treating a multi-subsystem language change as a prerequisite gate instead of admitting that it was a sequence of releases.

The normal phase discipline was followed inside the branch, but the branch itself remained long-lived. Contract, design, failing tests, implementation slices, compatibility repairs, documentation, and repeated audits accumulated before integration with `main`.

That created an integration cliff: later audit findings were evaluated against a branch that had already changed many unrelated semantic surfaces.

## Process correction

A release is a planning milestone, not necessarily one branch or one PR.

Future releases SHOULD be delivered as multiple independently mergeable PRs against current `main`. Each implementation PR should establish one narrow invariant plus its directly related tests and truthful documentation. After it passes its local gate, it should merge before the next slice begins.

Warning rule:

> If one implementation PR begins changing more than one semantic subsystem plus its tests/documentation, stop and reassess the slice boundary.

Compatibility/hardening work discovered after a semantic slice should be a separate PR rather than silently widening the original implementation slice.

A skeptical release audit should run against merged `main`. A defect found by that audit becomes a small repair issue/PR, followed by a fresh audit. The audit should not repair substantive behavior inline.

## What is retained from #839

Retain as design and test evidence:

- resolved numeric semantic decisions
- edge cases and regression reproducers
- source/Core-IR design conclusions
- arithmetic/equality/JSON/rendering policy decisions
- audit findings, especially cases missed by the initial test inventory

Do not mechanically cherry-pick the implementation branch into the new releases. New implementation work is re-derived from current `main` and the approved semantic decisions.

## What is not changed by this decision

- R17 arbitrary-precision Integer and ordered-map portability remains authoritative.
- R18 equality/key architecture remains authoritative.
- R19 Unicode/diagnostic portability remains authoritative.
- R20 open-function behavior remains authoritative.
- The approved Exact Numeric Model semantic decisions are not reversed merely because their implementation delivery is repartitioned.
- `GENIA_STATE.md` remains unchanged until behavior is independently implemented, tested, merged, documented, and audited through the new releases.

## Release ownership

Detailed semantic ownership is recorded in `docs/design/exact-numeric-release-ownership.md`.

The key split is:

- R21 owns what numeric source text means at parse/lowering/Core-IR boundaries.
- R22 owns numeric runtime kinds, arithmetic, conversions, comparison/equality integration, and numeric misuse/resource rules.
- R23 owns display/debug rendering, generic and compatibility JSON boundaries, and numeric format presentation.
- R24 consumes the completed R21-R23 portable contracts; C++ does not define or repair those semantics itself.

## Why this is better

This decomposition gives reviewers smaller diffs, makes regressions attributable to a specific semantic slice, lets `main` continuously absorb proven work, and allows the first independent host to consume contracts that have already survived integration rather than a giant prerequisite branch.
