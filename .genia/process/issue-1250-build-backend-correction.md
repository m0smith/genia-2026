# #1250 / PR #1318 build-backend correction

PROPOSED_NOT_APPROVED. Author: Codex. Independent Claude re-review pending.

## Preflight and design

Starting head d83e1c8bd3a0d6246c3c7cd7d8ba6a9610e07456; existing branch
issue-1250-fresh-dependency-baseline; base relationship remains
issue-1250-acceptance-infrastructure@9f96c6d9369bc29b87d6f63a97b3f7ce89bb7e05.
User authorizes correction and local preparation tests, including a bounded real
provisioning integration. No activation, acceptance, CI, merge or closure.
Independent review: PR #1318 review 5819491580 / #1250 comment 6726564535.
Read latest AGENTS and material authority sections in STATE, RULES, REPL README,
README; existing process, infrastructure code/tests, prior proposal and ledger.

Scope: fix the missing build backend without changing pyproject or the proposed
runtime lock/freeze. Root cause confirmed in a fresh disposable baseline archive:
original helper command exits 1, ModuleNotFoundError: hatchling. The default
isolated fixture install left backend versions unrecorded. Installing those into
the target would conflict with strict freeze equality; fake-uv tests never
exercised this dependency boundary.

Chosen design: a minimal PEP 660 frontend for the existing hatchling.build
backend. Create a separate disposable venv; install exact direct-wheel URL/hash
build requirements with --no-deps --require-hashes --no-index --only-binary :all:.
Check the complete build distribution/version set and every applicable static
and dynamic backend requirement before invoking build_editable. Build no other
source distribution. Sync target locked dependencies with --no-install-project
--no-build; then actually install Genia's editable wheel with --no-deps --no-index.
As required of an editable frontend, record PEP 610 source URL/editable metadata
and update its RECORD. Target contains the real Genia metadata, console entry
point and source link, with no backend-only distributions. Compare unchanged
42-package normalized freeze, and recheck immutable lock and subject identity.
Retain exact build inputs, build freeze, built wheel digest and all command exits.

Alternative considered: uv's default isolated build with constraints still
performs an internal solve and exposes less direct build-env verification.
Build-free installation is unnecessary and is not selected. The project-wide
backend and build contract remain unchanged. No source-tree .pth shortcut or
project-install bypass. The separate build venv is cleaned after retained evidence.

Core invariants: unchanged runtime lock/freeze, separately pinned backend inputs,
complete build closure, real editable installation, shared inputs for both frozen
subjects, explicit closed approval gate, exception propagation with FAIL evidence.
Tests: new RED before implementation, backend absence/version/evidence corruption,
backend leaked to target, positive wrapper handoff/shared evidence, bounded real
baseline/candidate provisioning without executing acceptance tests.

Portability seven fields: Python-only infrastructure; C++ unaffected; portable
contract unchanged; Core IR unchanged; no capability change; shared semantic
specs inapplicable (host-local packaging tests); no host gap. Maturity process-only.
MCP language knowledge unaffected: no Genia syntax/runtime/API change. Four core
docs remain truthful unchanged. Minimal necessary packaging complexity; no new
language/adapter semantics. Supports authorized #1250/R29 prerequisite tooling.
Risks: custom editable frontend metadata/RECORD correctness, new backend version,
artifact availability, CPython 3.12.14 Linux x86_64 only; preserve explicit limits.
Rollback: revert correction commits, leaving prior draft blocked and all evidence
preserved. GO for correction only; independent approval/activation remains NO-GO.

## Execution evidence

Pending local implementation and bounded preparation validation. The old evidence
is immutable; corrected provenance will be additive and explicitly supersede only
the earlier installation claim, never historical failures or accepted evidence.
