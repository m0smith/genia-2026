# Codex Prompt — R15 E15-0

Work issue #726, **E15-0 — R15 contract, roadmap reconciliation, and capability inventory**, in `m0smith/genia-2026`.

Before doing anything, read the latest `AGENTS.md` completely and obey it. Then read the primary current-state documentation completely: `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, and `README.md`. Also read `docs/strategy/killer-workflow.md`, `docs/strategy/release-roadmap.md`, `docs/strategy/r15-validation-modeling.md`, `docs/strategy/r15-kickoff.md`, `docs/process/08-roadmap-ticketing.md`, relevant R9/R10/R13/R14 contract/design documents, and `docs/design/composability-matrix.md`.

`GENIA_STATE.md` is final authority for implemented behavior. Do not infer planned behavior into current truth.

Follow the repository process for issue #726. This is the R15 E15-0 preflight/contract gate only. Do not implement E15-1 or later runtime behavior.

Required work:

1. Inventory the exact currently implemented validation/modeling capabilities and boundaries inherited from R9, R10, R13, and R14.
2. Reconcile the roadmap so R14 remains complete and R15 is the active/current release, while clearly stating that no R15 runtime behavior is implemented yet.
3. Produce the required preflight and contract/design handoff artifacts for #726.
4. Lock the E15-0 decisions for:
   - inert inspectable Template descriptions and opaque arbitrary callable Templates;
   - explicit missing-only defaults and explicit normalization;
   - explicit accumulated deterministic path-aware diagnostics without changing ordinary pattern semantics;
   - protected-value non-leakage through diagnostics, descriptions, defaults, or schema;
   - bounded/no-over-pull lazy Flow behavior;
   - exact-or-fail Template → JSON Schema generation;
   - deterministic discriminator-directed structural alternatives without nominal variants;
   - validation-local, explicitly bounded recursive Template references without global/lifecycle/config ambient state.
5. Reconcile issue #92 conceptually: only structural discriminated validation belongs in R15; nominal variant identity, constructors, and exhaustiveness remain deferred.
6. Record the dependency/order for E15-1 through E15-9, but do not implement them.
7. Run the documentation/process validations required for this gate.
8. Stop after the E15-0 artifacts and validations are complete. The next authorized implementation step is E15-1 only after the required approval.

Keep project documentation up to date as part of the work. In particular, keep `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, `docs/strategy/release-roadmap.md`, release documentation/examples, and `docs/design/composability-matrix.md` synchronized whenever the process phase legitimately requires them. Do not update implemented-truth docs to claim planned R15 behavior before that behavior is implemented and tested.

At completion, report changed files, process artifacts, validation commands/results, commits, and the exact next authorization boundary.