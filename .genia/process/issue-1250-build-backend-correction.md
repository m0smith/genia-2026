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

## Implementation and exact build evidence

`build_backend.py` validates literal evidence/requirements digests and runtime
scope, creates the private build venv and installs direct wheels with no deps,
no index and required hashes. `editable_builder.py` checks the complete build
inventory and PEP 517 static / PEP 660 dynamic requirements, invokes the original
Hatchling backend, and records wheel hash and source. It implements frontend-owned
PEP 610 editable metadata plus its RECORD entry after uv installs the editable
wheel. No backend-only distribution is hidden or excluded from freeze: those
packages exist only in the separate venv, which is removed after retained logs.
`packaging`, `pathspec` and `pluggy` independently occur in the runtime lock;
their runtime entries still participate in exact equality.

`run.py` preserves the closed approval sentinel and every literal lock/freeze
check. It syncs locked runtime/dev wheels with --no-install-project --no-build,
then always installs the actual editable project, and freezes the exact target
interpreter with --no-config --quiet. --no-install-project is an intermediate
step, not a project-install bypass. A build/install failure propagates and
finalization cannot report PASS. Backend closure loading occurs before sync.

Build evidence: `tools/issue_1250/dependencies/proposed-build-2026-11-08/`.

- build-evidence.json SHA-256:
  `e1fae82b5e5358d7db86ede48903cda603eea0d26050de6827cf850e21a65404`
- build-requirements.txt SHA-256:
  `96a6b7b227b6d8603b786f7dfdb2a825a915fbe910b3b59674b29b4490baab18`
- evidence bundle manifest SHA-256:
  `737c244c9b7c7e3e0e464c75191d82badf89217b7ad51d6dd3276fe7ee759037`

| Build distribution | Version | Wheel SHA-256 |
|---|---|---|
| editables | 0.6 | `d70e4698078a1d033e7786d9c64e5be070d058a67c21417024d38a58ac20aa43` |
| hatchling | 1.33.0 | `415290b84f464d2884303fca8974d38e7b85579069fab02a15db0828fbb1446d` |
| packaging | 26.3 | `d7193f7c8e4e93f444fde0262bf90af30e16fa0ad0ad44cb553c87339b23cd1c` |
| pathspec | 1.1.1 | `a00ce642f577bf7f473932318056212bc4f8bfdf53128c78bbd5af0b9b20b189` |
| pluggy | 1.7.0 | `7dd7b0d8832ba3cb632c306926ded123429211b83641b35dc5c41ad2d34f9bec` |
| tomlkit | 0.15.2 | `05562412163a3037b94497385fb7f9204c637bc605af7a48199e41cf2272f437` |
| trove-classifiers | 2026.9.21.13 | `8b1ff4f9c191b1040b71c37f1e445ab99732911e3cd91de52838453a854d7a17` |

Selected explicitly from default-PyPI metadata; exact direct-wheel URLs and
requires-python/requires-dist fields retained. No build dependency solve or
second runtime lock generated. uv's "Resolved 7" line validates the seven exact
provided wheels; --no-deps prohibits transitive acquisition. There is no choice
of a new backend version during provisioning. On Python 3.12, hatchling's
conditional tomli requirement is inactive; tomlkit and other active static
requirements are pinned. Dynamic editables~=0.3 is satisfied by editables 0.6.
The manifest is PROPOSED_NOT_APPROVED; it confers no activation authority.

## Execution evidence

Additive raw records and `validation/validation.json` retain the initial cold
failure, committed RED, both intermediate correction failures and final result.
Earlier unpinned installation evidence, original runtime fixture/manifest,
historical registration and all 22 failure records remain byte-identical.

Committed RED: 888aacb3 (7 failed for missing backend interface; 2 passed;
1 opt-in integration not selected). The correction implementation cites that RED.

Final focused command (from repository root):

```sh
ISSUE1250_BUILD_INTEGRATION=1 \
ISSUE1250_BUILD_EVIDENCE=/workspace/1250-backend-preparation/evidence/final-integration \
UV_CACHE_DIR=/workspace/1250-backend-preparation/test-cache \
uv run --project /workspace/1250-proposed/subject --no-sync pytest -n 0 -q \
  tests/unit/test_issue_1250_acceptance_infrastructure.py \
  tests/unit/test_issue_1250_build_backend.py
```

**73 passed in 6.91s; zero skipped.** Integration uses two disposable local
clones at the registered baseline/candidate SHAs and separate initially absent
uv caches. It invokes only provision_locked, never main()/acceptance. Both
produce the same seven-package backend inventory and exact 42-entry target
freeze, unchanged lock SHA and clean subject status. Target Python imports Genia
from each subject's src, finds installed metadata and the console entry point;
PEP 610 metadata hash/size match installed RECORD. Temporary build venvs are gone.
The positive provision() handoff is tested with a test-scoped sentinel patch;
the checked-in sentinel remains None.

Both build wheels are recorded by SHA; their bytes include different source
paths and are not claimed equal:

- baseline: `db5388a162f4e7c7bb6fd9adc4911792b13036396d79382fb43dec071e9807d3`
- candidate: `ff38bbd543eefaaef3410e42b8617fd006894fb0f94c72e356523c4348fee4ee`

Other checks:

```sh
UV_CACHE_DIR=/workspace/1250-proposed/test-cache uv run --project /workspace/1250-proposed/subject --no-sync ruff check tools/issue_1250 tests/unit/test_issue_1250_acceptance_infrastructure.py tests/unit/test_issue_1250_build_backend.py
UV_CACHE_DIR=/workspace/1250-proposed/test-cache uv run --project /workspace/1250-proposed/subject --no-sync python -m tools.code_documentation --base-ref d83e1c8bd3a0d6246c3c7cd7d8ba6a9610e07456
python3 -m compileall -q tools/issue_1250
git diff --check
```

Ruff passed; documentation checker: 10199 records, 2793 legacy gaps,
1 classified exclusion, **0 errors**. Compileall and whitespace check passed.

Retained intermediate findings:
1. Runtime override guard initially rejected uv's internal recursion counter;
   allowlisted UV_RUN_RECURSION_DEPTH (not a dependency setting).
2. First successful build/install attempt exposed inherited VIRTUAL_ENV selecting
   the runner's environment during freeze. Strict comparison rejected it, never
   reported success. Explicit target --python fixes that boundary; --quiet keeps
   uv status text out of freeze without filtering any package lines.
3. A standalone corrected integration passed; the final combined run adds RECORD
   and missing-evidence/false-PASS assertions and includes every focused test.

## Limits and independent review gate

Supported/checked: CPython 3.12.14, uv 0.13.5, Linux x86_64. Helper enforces them,
uses --no-config and rejects UV_/PIP_ overrides except cache location and uv's
internal recursion counter. OS/interpreter build, wheel availability and pinned
backend behavior remain external inputs; no cross-platform or bit-identical
editable-wheel claim. No vulnerability/semantic audit of new backend releases.
Only packaging/import/metadata verified, never Genia acceptance or signal behavior.
Hosted Ubuntu/GCC and namespaces are untested. Original historical lock bytes and
unpinned backend versions remain unavailable.

Independent Claude should inspect the PEP 660 frontend, installed RECORD update,
complete closure checks, command flags, positive handoff, real retained evidence
and unchanged target freeze. Required maintainability/evidence review is pending;
no author PASS substitutes for it. Draft remains NOT APPROVED — DO NOT MERGE.
APPROVED_DEPENDENCIES remains None. No CI/acceptance dispatch, G0/G1/G2,
executor-A/#1316 investigation, merge or closure. Rollback by reverting correction
commits only; retain all additive failure evidence and original22 unchanged.


## Subsequent registration preparation

Independent review 5828336713 approved the correction at d3bf5b73 for the next
separately authorized gate only. [Registration preparation and hardening](issue-1250-registration-preparation.md)
subsequently adds the remaining negative tests, strict pre/post RECORD checks,
hash-required editable installation and mandatory future qualification. Its
registration metadata and wiring diff remain inactive; original correction
fixtures and their manifest stay immutable. Baseline/activation review remains
separate and pending. The local 73-test evidence above is historical; the new
preparation record reports its own exact tested source and 127-test result.
