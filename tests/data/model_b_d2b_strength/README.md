# Final D2b RED strength delta — independent review pending

> Historical phase evidence, superseded for current implementation/status claims.
> See [GENIA_STATE.md](../../../GENIA_STATE.md) for implemented behavior and the
> [independent cumulative review](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6773392957)
> for the current conditional-review disposition. Historical review/STOP wording
> below describes its recorded phase; it does not grant D2b acceptance or parity.

Base corrected RED: `69ac60aa5a769fb267558e8b8dbe91995aecfc04`.
Partial production comparison: `1bbc63e4ef5d3a461542f6849d35aed33bfe9e17`.
Authority: maintainer [6615005691](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6615005691),
following Claude review [6611014654](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6611014654).
The seven earlier corrections are independently verified; **final RED acceptance
still requires narrow independent Claude Code review of this additive delta**.

## Scope / preflight

Two logical guards only. No production, parser/IR, capability declaration,
authority-document, MCP profile, earlier oracle or baseline changes. Existing56
test definitions/outcomes and all historical archives are preserved. STATE/RULES
still define implemented behavior; this task makes no new D2b implementation claim.
The D2 section5 notation erratum remains a later verified GREEN docs-sync item.

Portable observations remain in existing shared R16 source-module specs. R1 uses
only `multi_file_eval` and `open_functions`; R2 also requires existing
`default_open_functions` and `doc_help`. No capability or runner is invented.
Owned C++ gaps add only the two IDs: R1 to multi-file #1018, R2 to default-open
#1269. Reasons, classifications and removal conditions remain unchanged.

## R1 — no accidental rename or dot splitting

`spec/error/error-r20-use-dotted-from-not-rename.yaml` uses the independently
verified explicit R20 fixture: `open f(0)=1`, contributor `extend base.f(1)=2`,
then `use walk from base.f with ext`. Its exact portable oracle is exit1,
empty stdout and `Error: Undefined name: base.f\n`. Trailing calls would return
`[1,2]` if an accidental rename succeeded. An ordinary base would mask the guard
at RED during contributor import; this explicit base avoids that problem.

One additive host-local twin first executes that same shared case with existing
R16 `load_spec/execute_spec/compare_spec`, then uses the exact reviewed fixture
to assert literal lookup failure and **no `walk` binding published**. This private
Env-table assertion supplements the portable shared observation; Python is not
its sole semantic authority. The existing positive literal `a.b` module-alias
test is unchanged and continues passing on partial GREEN.

## R2 — projected doc differs from binding metadata

`spec/eval/model-b-link-projected-doc-not-binding-meta.yaml` uses real modules:
`other` exports `v=1`; `base` defines annotated original `f`, inline `G-inline`,
alias `a=f`, then replaces slot `f` by `import other as f`; `ext` contributes
to `base.a`. Main selects `use a from base with ext` and observes
`[doc("a"), map_has?(meta("a"), "doc")] == ["G-inline", false]`.
The projected doc is the G-inline fallback; binding metadata has no doc, while
the independently captured help channel still originates from G. Reading doc
from binding metadata or replacing metadata with documented channels cannot
satisfy the deliberately unequal observations. This uses the existing shared
D2b pytest harness, with no added framework or source stub.

## Focused results and discrimination

| Selection | Original RED production | Unchanged partial GREEN |
|---|---:|---:|
| Original56 (preserved) |8 PASS /48 FAIL|56 PASS|
| New R1 |PASS|PASS|
| New R2 |FAIL: ordinary `base.a` target not open|PASS: `["G-inline", false]`|
| Final58 |**9 PASS /49 FAIL**|**58 PASS /0 FAIL**|

No errors/skips. Existing helper groups10/10/10/7 shared selections,17 host
selections and4 historical Python transitions; `--maxfail=19`, maximum15
expected failures in any invocation. The 60000-step TCO, concurrency, snapshots,
three-channel metadata and all historical compatibility transitions remain in
the unchanged56 cohort. `inventory.json` verifies all prior outcomes and host
test ASTs unchanged; the new total is exactly56+R1+R2.

| Mutant | Observed discrimination |
|---|---|
| M7 literal-first, split-at-dot fallback | New shared R1 fails all three expected stdout/stderr/exit comparisons on both implementations: mutant returns `[1,2]`, exit0. The host-local R1 twin also fails on both (`DID NOT RAISE`). |
| M2 doc reads binding-metadata channel instead of projected doc | New R2 on partial fails its stdout comparison: `[none("missing-doc", {name: "a"}), false]` instead of `["G-inline", false]`. It remains exit0 with empty stderr, so this is a channel discrimination, not a crash. |

M2 is not scored on RED: ordinary activation rejects before reflection, so a
failure there would not discriminate the channel. Every control output and
mutant mismatch is retained in the mutation JSONs. Expected mutant failures are
not hidden or counted as genuine implementation defects.

## Reproduction / environment

Python3.12.14, existing uv project environment with pytest9.2.0, explicit
current-worktree `PYTHONPATH=src:.`. Focused JSONs retain exact commands/node IDs,
source HEADs and per-case outcomes in compact form (see archive policy below). Source HEAD names the unchanged production tree;
test-overlay SHA256 values in `inventory.json` identify this final test content.
The historical comparisons overlaid the TEST-ONLY test/spec delta on a detached
partial1bbc worktree with the same bounded selections; no production was transferred
between the trees. The corrected-RED reproduction helper is nonportable sandbox tooling.

`mutation_probe.py red|partial` is historical, nonportable sandbox tooling with
hard-coded /workspace paths and original environment assumptions; it is not a
clean-checkout or CI recipe. It used existing R16 execution and comparison APIs.
It adds only an in-memory bootstrap to the existing interpreter subprocess,
using a10-second deadline. M7 intercepts `IrOpenUse` evaluation only when literal
lookup fails and splits the alias; M2 redirects the projection doc read to its
binding map. Neither mutation writes a source file or adds a host protocol,
capability, comparator or language implementation. The direct host-test M7
probe also injects the same wrapper in process memory. Full mutant code, actual
outputs and mismatches are retained; both production source trees stay unchanged.

The initial57-selection diagnostic (before adding the host-local publication
assertion) is retained separately. It had8 PASS/49 FAIL on RED and57 PASS on
partial; it is not the final58 inventory. Initial helper formatting and gap-file
insertion attempts are disclosed in `support-notes.json`. No fixture or oracle
was changed in response to a genuine production failure.

## Preservation / applicability / checks

On each production implementation with final overlays:
- D1/key/private D2a: **124 PASS /2 transitioned tests deselected**; transitions
  remain covered in the4-case behavioral group.
- R20 cross-module: **11 PASS /1 transitioned test deselected**, also covered.
- Existing Slice C/D2b inventory checks: **7 PASS /143 semantic cases deselected**,
  an inventory-only selection, not a semantic pass claim.

**120 module sources parse/lower/portable-IR PASS**: original101 D2b sources,
12 historical-transition sources,4 R2 sources and3 R1 sources. Ruff check and
format-check PASS on the affected test module, existing D2b harness and mutation
evidence helper. JSON gap-diff proof permits only the two owned test-ID additions.

Fresh capability-gated execution of both new specs against the existing clean
bounded C++ source1f338866 binary gives **2 UNSUPPORTED /0 PASS /0 actual failure
classes** at the normal10-second deadline. Binary hash and declared capabilities
are retained. This is truthful applicability evidence, not a new build, not
re-certification of the earlier fef41e58 source pin, and not C++ language parity.
Original accepted C++ evidence stays byte-identical.

## Stop / review handoff

After the separate TEST-ONLY commit, request Claude Code DELTA-ONLY review of
R1/R2, mutation discrimination, additive scope and preserved56/historical data.
Do not self-approve RED or infer GREEN acceptance from58 focused passes.
Production maintainability review, full regression/conformance/documentation
gates remain a later authorized GREEN phase. PRs1314/1313 remain draft/unmerged;
issue state and Slice E/R29 boundaries are unchanged.


## Compact archive and history retention

See the [archive format and mandatory history-retention policy](../model_b_d2b_red/README.md#compact-archive-and-history-retention).
Per-case outcomes/diagnostics and exact run commands/return codes remain here;
raw logs and duplicated case records are replaced by hashes, original-commit
links and case-table indices. No outcome is reclassified. Do not squash away
historical evidence without independently verified durable tags or restored logs.
