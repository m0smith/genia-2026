# D2b authorized TEST-ONLY oracle correction — review pending

> Historical phase evidence, superseded for current implementation/status claims.
> See [GENIA_STATE.md](../../../GENIA_STATE.md) for implemented behavior and the
> [independent cumulative review](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6773392957)
> for the current conditional-review disposition. Historical review/STOP wording
> below describes its recorded phase; it does not grant D2b acceptance or parity.

Authority: maintainer [6609232173](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6609232173),
following independent Claude Code reconciliation
[6609143905](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6609143905).
This corrects tests, not language behavior. **Fresh independent Claude Code review
of the corrected commit is required before RED acceptance or GREEN resumption.**

## Preflight delta / scope

Parent: accepted RED `b25b8f8c1904dc683f6634c4ef8c5f108d4f3eca`, production-identical
to D2a merge `c377b971b42682207d194aefb0e5182650d4ac10`. Partial implementation used
only as a comparison target: `1bbc63e4ef5d3a461542f6849d35aed33bfe9e17`.
No production, parser, IR, authority document, MCP profile, capability declaration
or skip change. No new design or semantics authorized. Original accepted RED logs,
results, C++ evidence and historical oracle archive remain byte-identical; the
original README is also preserved in `original_test_and_specs.json`.

Portability: existing ordinary callable/linking contract and source-module boundary;
same R16 shared cases and `multi_file_eval`, `open_functions`, `default_open_functions`
(plus `doc_help` for metadata). Python-only tests supplement private projection,
concurrency and TCO observations. C++ remains unsupported under existing claims;
original 32-UNSUPPORTED evidence is retained, not freshly recertified. No adapter,
protocol, capability vocabulary or Core IR change. All four authoritative documents
already forbid rename-on-use and retain unimplemented D2b boundaries; no truthful
MCP language-knowledge change is warranted by correcting tests alone.

## Seven authorized corrections / old and new expectations

Complete original and revised shared documents plus original host test text are
retained in `original_test_and_specs.json`. This table explains the changes;
the four earlier authorized historical transitions remain unchanged in
`../model_b_d2b_red/historical_oracles.json`.

| Item | Previous test / why incorrect | Authorized correction and retained coverage |
|---|---|---|
| 1 | Help expected `base:2`, discarding annotation-inclusive D1 span start. D1 copies spans verbatim; D2 section7 formats that span. | Require `  1. base:1` and absence of `base:2`. Two new cases discriminate annotation after a prefix (`base:2`, not head-line3) and unannotated head-line2 (not1). Three independent doc/meta/help channels remain asserted. |
| 2 | Qualified/renamed `use g from relay.h`, `use g from base.a`, renamed sequential views and `consumer.f` reinterpret a whole dotted IDENT and violate RULES no-renaming-on-use. | Use exported names `h`, `a`, `f`; preserve re-export/alias exact-G authority, B1 replaced slot99, sequential order results, view-not-target negative, immutable precheck, fault/retry and concurrency. A new literal `a.b` import-alias guard prevents dot splitting and asserts exact group identity. |
| 3 | `meta("f")/doc` and `meta("g")/doc` are division, not named map access; the prior README's attempted fix was wrong. | `map_get(meta("f"), "doc")` / corresponding `g`; preserve exact frozen channel and explicit-R20 overlay expectations. |
| 4 | Ownership stderr invented `function f/2`, unlike the existing ownership diagnostic (already wrong on original RED). | Exact `function 'f'` text, same error identity and owner module; authority is existing Slice C imported-alias oracle plus maintainer correction. |
| 5 | Typed clause keys were confused with literal matching: int1 and float1.0 keys differ, but both calls match the earlier int1 clause first. | `[7, 8, 9]` becomes `[7, 8, 8]`. All true/int/float declarations and calls remain, preserving duplicate-key discrimination and first-match behavior. |
| 6 | TCO fixture used unbound header names in an arm and `n-1` (one identifier), and renamed use. | Arm-bound `walk(k - 1, a + 1)`, base alias `walk=f`, legacy `use f`, publish the selected view to closure `walk`; still asserts exactly60000 steps. Frozen-view mutation keeps distinct old/new views and live999 while both snapshots return3. |
| 7 | Original counts and acceptance wording hid later assertions and misnamed passing controls. | Keep original evidence immutable, annotate historical README, record revised inventory/results and old/new values separately. No assertion deletion, skip, timeout increase or production patch. |

The design section5 notation is not a syntax extension: STATE/RULES and the
maintainer decision take precedence. Parser/IR and D1 spans remain untouched.

## Before / after verification

| Selection and implementation | PASS | FAIL | Meaning |
|---|---:|---:|---|
| Original53 on original RED |6|47|Retained original evidence; observed failure classification, not certification of masked assertions. |
| Original53 on partial1bbc63e4 |40|13|Fresh reproduction, `before-partial.json`; confirms independent reconciliation. |
| Revised original53 on RED |8|45|Two formerly invalid baseline tests now correctly pass as controls. |
| Revised original53 on partial |53|0|No production change. |
| Expanded56 on RED |8|48|Three added guards remain RED at missing activation/reflection seams. |
| Expanded56 on partial |56|0|Includes all three new guards and meaningful60000-step TCO. |

Eight RED passing controls: authority-builtin, authority-lambda, authority-nonfunction,
local-lambda-alias, non-export, ownership-declaration, explicit-view-metadata-unchanged,
and escaped-failed-origin negative. Corrected `view-not-target` is **not** a passing
RED control. Its rejection is reached only after ordinary activation succeeds.
The original6 controls did not include ownership or explicit-view metadata.

`results.json` maps each of56 names to original/revised RED/partial outcomes.
The 48 remaining RED failures are genuine missing activation/reflection/validation
seams. No remaining failure was observed in these56 selections on the partial
candidate. This does not certify production maintainability, full regression,
all concurrency schedules, cross-host conformance or GREEN acceptance.

## Commands, environment and evidence

Python3.12.14, existing uv project environment. Every pytest command uses uv,
explicit current-worktree `PYTHONPATH=src:.`, `--maxfail=19`, and default deadlines.
Selections are bounded: shared groups10/10/10/6, host16, transitioned Python4.
Maximum observed failures in one invocation15; no threshold crossing, errors or
skips. Expected RED exits are retained, not retried to overwrite failures.

`before-partial.json`, `revised-red.json` and `revised-partial.json` retain exact
commands, source HEADs, counts and per-case outcomes in compact form (see archive
policy below). Source HEAD identifies the production tree; corrected test-overlay
SHA256 values remain in inventory.json. The same overlay was used on both trees.

`reproduce.py` is retained as historical, nonportable sandbox tooling. Its hard-coded
/workspace paths and original uv environment are not a clean-checkout or CI recipe.
It delegated to existing pytest tests, without replacing R16 or transferring
production between implementations. The recorded comparisons used the TEST-ONLY
overlay on the original RED and partial1bbc63e4 production trees.

Preservation on **each** implementation (`preservation.json`):
- D1 completion/preparation, Slice C keys, private D2a core/dispatch/publication:
  **124 PASS /2 deliberately transitioned D2b selections deselected**.
- Existing R20 cross-module tests: **11 PASS /1 transitioned equal-key test
  deselected**; that transition is exercised in the four-test behavioral group.
- Slice C inventory + D2b owned-gap inventory: **7 PASS /143 semantic cases
  deselected**, an inventory-only check, not semantic coverage.

Fixture checks: **101 module sources parse/lower PASS** through existing parser,
lowerer and portable-IR assertion. Ruff check and format checks PASS for the two
test modules and evidence reproduction helper. Inventory checks confirm original53
plus3, no omitted names, preserved original archives and TEST-ONLY changed paths.
Initial helper lint and a wrong scratch import were corrected; their observations
and original helper are retained in `support_attempts.json`, not counted as test
results or hidden behind a pristine-green claim.

## Remaining gate

Review this exact corrected SHA independently with Claude Code. Check all seven
changes, old/new archives, no-renaming/dotted-alias meaning, snapshot identity,
metadata channels and60000-step TCO. No acceptance is claimed here. PR1313 remains
draft and unchanged by this separate correction branch; no production implementation
resumes, merge, issue closure, Slice E or R29 work is authorized by these results.


## Compact archive and history retention

See the [archive format and mandatory history-retention policy](../model_b_d2b_red/README.md#compact-archive-and-history-retention).
Per-case outcomes/diagnostics and exact run commands/return codes remain here;
raw logs and duplicated case records are replaced by hashes, original-commit
links and case-table indices. No outcome is reclassified. Do not squash away
historical evidence without independently verified durable tags or restored logs.
