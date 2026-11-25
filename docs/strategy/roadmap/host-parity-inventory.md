# Supported-Host Parity Inventory and Schedule (R30–R39)

Status: **Planning record — non-authoritative.** `GENIA_STATE.md` remains final
authority for implemented behavior. This file schedules parity work; it
implements nothing, approves no syntax, and adds no release. Policy:
[`multi-host-conformance-policy.md`](multi-host-conformance-policy.md).
Tracking issue: [#1341](https://github.com/m0smith/genia-2026/issues/1341).

## Evidence base (exact revisions)

| Item | Revision / value |
|---|---|
| `genia-2026` inventoried checkout | `794e6816f40e6ef5d7dc40f9c26a0905af547b82` (current `main` at inventory time) |
| `genia-cpp` inventoried checkout | `0a119f67d92cb08c2feaf975610722a2fa7555c8` (`main`, merge of genia-cpp#61) |
| `genia-cpp` pinned contract revision (CI/README) | `d005c89f852ee2d27682dade272eabfd158adf12` |
| Pinned evidence (`genia-cpp/evidence.json`) | total 1146: pass 335, unsupported 811, all failure classes 0, classification `current` |
| Current-main run (this inventory; local Release build, `tools.spec_runner --host`) | total 1162: pass 335, unsupported 827, all failure classes 0, classification `resolvable_ancestor` |

Supported hosts: Python reference host (`src/genia`) and `m0smith/genia-cpp`.
`spec/manifest.json` lists node/java/rust/go only as *planned* hosts and the
browser runtime adapter as *scaffolded*; they are out of this schedule until a
host exists.

**Verification limits (explicit unknowns).** Classification below is by shared
spec `requires:` tags plus case-id family for the 493 ungated unsupported
cases; individual case root causes were not each re-diagnosed. The inventory is
evidence-bounded, not exhaustive: Python-host behavior with *no* shared spec
(for example interactive REPL prompt/history, `serve` mode, MCP, the native
test runner, host-interop module allowlists) can only be inventoried from
`GENIA_STATE.md` and source, and no C++ evidence exists for it either way.
Python-side unsupported cases (Python declares every capability supported in
its evidence run) were not re-run here.

## Disparity categories

- **Missing behavior** — C++ returns `unsupported` for portable behavior.
- **Hidden partial** — capability declared `supported`/`partial`, but cases
  whose every `requires:` tag is satisfied remain unsupported (not visible in
  capability flags or `spec/known_host_gaps.json`).
- **Missing evidence** — behavior exists on Python but no shared spec can
  observe it on any host.
- **Implementation detail (not a gap)** — host-local freedom, e.g. REPL
  prompt/banner/history, build system, internal data structures.

## Inventory and release assignments

Owner for every C++ delivery row is the `genia-cpp` host lane under the named
release umbrella; tracking issue is the existing issue shown (no new tickets
created). "Removal condition" for every capability row is: `genia-cpp`
declares the capability `supported`, applicable shared cases pass, and the
host parity gate reports `PARITY_OK` (see `cpp-host-gap-burndown.md`).

### A. Registered capability gaps (`spec/known_host_gaps.json`)

| Capability | Current-main unsupported (cases whose only unmet tags include it) | Tracking | Target release |
|---|---|---|---|
| `immutable_bindings` | 24 sole + 8 combined | #1261 | R31 |
| `default_open_functions` | 78 sole + 54 combined | #1269 | R31 |
| `closed_functions` | 42 sole + 23 combined | #1250 | R31 |
| `multi_file_eval` | 18 sole + 55 combined | #1018 | R31 |
| `sheet_values` (not declared by C++ at all) | 35 | #1330 | R31 (D7: R30 Python-first; R31 Sheet parity commitment, #1340) |
| `resource_io` | 0 shared cases observed | #1018 | R32 |
| `configuration_environment_snapshot`, `configuration_dotenv_snapshot` | requires-gated config cases | #1018 | R32 |
| `debugger_stdio` | debugger cases + `cli/debug_stdio_suppression` | #1018 | R33 |
| `model_deterministic_fixture`, `model_gemini_rest` | AI cases | #1018 | R34 (separately gated workstream, D-D) |
| `embedding_/indexing_/retrieval_/reranking_deterministic_fixture` | retrieval cases | #1018 | R34 (separately gated workstream, D-D) |
| `allowlisted_host_interop` | interop cases | #1018 | R35 (allowlist contents are host-local; the capability is not) |
| `execution_process`, `shell_stage` | process/shell cases | #1018 | R36 |
| `http_server`, `http_outbound_transport` | 1 combined; no dedicated shared specs | #1041, #1043 | R37 |
| `json_compat` | 8 | #1024 | **Permanent host-local exception** (see register) |

### B. Capability-flag partials and required-capability gaps (not in the gap registry)

| Item | Evidence | Tracking | Target |
|---|---|---|---|
| `doc_help` (a *required* manifest capability) declared `unsupported` by C++ | 17 sole + 29 combined unsupported | #1018 | R33 |
| `prelude_autoload` `partial` | 7 combined unsupported | #1018 | R31 (prerequisite for core-library rows below) |
| `core_ir_eval` `partial`, `shared_spec_runner` `partial` | umbrella flags; resolved by rows in C | #1018 | closes when C rows close |
| `open_functions` hidden partial | 26 cases tagged only `open_functions` still unsupported: `extend`/`use` selection, mutual tail calls, Option-aware strata, varargs precedence, help provenance, grouped-header capture errors | #1018 | R31 (with default-open/closed functions) |
| `json_strict` hidden partial | `flow/json-representation-template-flow` | #1018 | R32 (with Templates), unless demonstrated to be an R31 prerequisite or separately approved earlier |

### C. Ungated shared cases unsupported on C++ (493; no capability flag)

Exact per-case assignment: [`host-parity-ungated-cases.json`](https://github.com/m0smith/genia-2026/blob/main/docs/strategy/roadmap/host-parity-ungated-cases.json)
(every case in exactly one family; ordered case-id rules, first match wins).
Under D-A, any case in these rows that the R31 pre-flight demonstrates to be an
actual Sheet prerequisite moves to R31; all others keep the target shown.

| Family (JSON key) | Cases | Target |
|---|---:|---|
| Templates, representations, refinement, named patterns, open/exact shapes, schema, validation, diagnostics, `collect_validated`, `parse_csv`, R9/R15 cross-mode (`template_validation`) | 199 | R32 |
| Format strings (`format`) | 73 | R33 |
| Core stdlib and patterns: Option/Outcome, `apply_raw`, `as_seq`, seq-compatible, map/pair helpers, glob/list patterns, quote/quasiquote/`delay`, unary ops, call spread, varargs, imports, annotated funcdef IR, R18 equality, R19 Unicode, R21 parse errors, R22 exact-numeric errors, Model B (`core`) | 137 | R33 |
| Configuration resolution and protected values, R10/R13 (`config_protected`) | 38 | R32 |
| AI/retrieval cross-release: model fixture, R11, R12, `chunk` (`ai_retrieval`) | 24 | R34 (separately gated workstream, D-D) |
| Flow beyond phase 1: `tee`/`zip`, `rules`/`refine`, Flow `reduce` (`flow_ext`) | 10 | R32 |
| CLI file-mode argv/`--`/`main(argv)`, debug-stdio suppression (`cli_argv`) | 4 | R33 |
| Native test runner CLI (`native_test`) | 3 | R39 |
| Lifecycle, R14 (`lifecycle`) | 2 | R32 |
| `rand` simulation flows (`simulation`) | 2 | R36 |
| `pipe_mode_record_pipeline_collect_validated_boundary_error` (`compat_pipe`) | 1 | D-C: separate test-only change re-expressing it with strict JSON (#1018) |
| **Total** | **493** | |

**Reconciliation of the 827 current-main unsupported cases:** 307 with at
least one unmet `requires:` tag (sections A/B; their sole/combined figures
count a case once per unmet tag) + 27 hidden partials whose tags are all
declared supported (26 `open_functions`, 1 `json_strict`) + 493 untagged
(this section) = 827.

### D. Python surfaces without shared evidence (missing evidence)

| Surface | Target | Note |
|---|---|---|
| Annotations (`@route`, `@cors`, …) and `serve` CLI mode | R33 (CLI/annotations); serving R37 | needs shared evidence route first |
| ZIP (`zip_entries`/`zip_read`/`zip_write`) | R35 | contract-first; no capability name yet (#1024) |
| Web helpers (R7 routing/CORS wrappers) | R37 | |
| Actors (Python-host-only per STATE) | R38 | |
| Native test runner and Genia MCP server (`apps/mcp/mcp.genia`) | R39 | |
| `read_file`/`write_file` legacy bare-name helpers | R32 (with `resource_io`) | D-B: no exception |
| Interactive REPL prompt/banner/history | not a gap | host-local by R26 contract |

## R30 incremental evidence

The earlier tables retain the inventoried baseline. The follow-up tested the
authoritative shared corpus at `45f77fe72adb679568b8cd913de106ce3498b30b`:

| C++ revision | PASS | UNSUPPORTED | FAIL |
|---|---:|---:|---:|
| Previous CI pin `0a119f67d92cb08c2feaf975610722a2fa7555c8` | 335 | 850 | 1 |
| Catalogue candidate `6c88ef858a25172281e908f891ac7fdfa6748df3` | 335 | 851 | 0 |

Both runs classified 1,186 cases. Every other failure-class count was zero.
Only `r30-map2-global-alias` changed classification. The pin returned
`Error: Undefined name: map2` on the unshadowed alias. The catalogue candidate
reports all 24 R30 cases unsupported, including that alias. The genuine
undefined-name control still passes. The CI pin is now `0c4dbb1c1ee290d41777bcf52c68e62a7a22e059`
([genia-cpp #62](https://github.com/m0smith/genia-cpp/pull/62)). The merge tree
matches the reviewed head `5d00e181f3eddc51f4e4e080631065b65bac29cd`.

| C++ gap | Owner lane | Track | Target | Removal condition |
|---|---|---|---|---|
| `sheet_values` (11 additional shared cases, 46 total) | genia-cpp Sheet | #1330 | R31 | C++ declares `sheet_values` supported, every affected case passes, and parity reports `PARITY_OK`. |
| Standalone `map2` (14 cases) | genia-cpp core stdlib | #1018 | R33 per D-A | Every case passes on C++ without a `map2` exclusion and parity reports `PARITY_OK`. |

Standalone `map2` cases have no `sheet_values` requirement. R31 can take
`map2` only if its pre-flight demonstrates an actual Sheet prerequisite.

### Sheet extraction and attachment

- `spec/error/r30-sheet-attach-not-sheet.yaml`
- `spec/error/r30-sheet-column-not-sheet.yaml`
- `spec/error/r30-sheet-duplicate.yaml`
- `spec/error/r30-sheet-long.yaml`
- `spec/error/r30-sheet-missing.yaml`
- `spec/error/r30-sheet-not-list.yaml`
- `spec/error/r30-sheet-reserved.yaml`
- `spec/error/r30-sheet-short.yaml`
- `spec/eval/r30-sheet-columns.yaml`
- `spec/eval/r30-sheet-empty-shapes.yaml`
- `spec/eval/r30-sheet-validated-report.yaml`

### Standalone List computation

- `spec/error/r30-map2-arity.yaml`
- `spec/error/r30-map2-callback-failure.yaml`
- `spec/error/r30-map2-callback-first.yaml`
- `spec/error/r30-map2-first-list.yaml`
- `spec/error/r30-map2-mismatch.yaml`
- `spec/error/r30-map2-noncallable.yaml`
- `spec/error/r30-map2-reserved.yaml`
- `spec/error/r30-map2-second-list.yaml`
- `spec/eval/r30-map2-callables.yaml`
- `spec/eval/r30-map2-closed.yaml`
- `spec/eval/r30-map2-global-alias.yaml`
- `spec/eval/r30-map2-outcomes.yaml`
- `spec/eval/r30-map2-results.yaml`
- `spec/eval/r30-map2-zip.yaml`

## Dependency check and maintainer decisions

Dependencies checked: R31 Sheet parity depends on whichever template,
validation, prelude and core-library cases the `sheet_values` shared cases
actually exercise. R32 configuration snapshots depend on protected values;
outbound HTTP (R37) depends on protected values (R32) and `import`; serving
(R37) depends on annotations/`serve` (R33); R34 AI/retrieval depend on R32
protected values and the R31/R32 template rows. No dependency points backwards.

Maintainer decisions recorded on #1341 (2026-11-24):

- **D-A — approved, committed targets** ([decision](https://github.com/m0smith/genia-2026/issues/1341#issuecomment-7139205101)).
  R30 is unchanged (Python-first Sheet shaped computation). R31 carries its
  existing parity commitments plus only section-C cases the R31 pre-flight
  *demonstrates* are actual Sheet prerequisites; it is not enlarged by the 409
  `template_validation`/`format`/`core` cases. Remaining template/validation
  parity is R32; remaining format-string, core-stdlib and pattern parity is
  R33. These targets change only by a later explicit maintainer decision.
- **D-B — `read_file`/`write_file`** parity is scheduled with R32 `resource_io`.
  No new permanent exception.
- **D-C — the pipe-mode case requiring `json_compat`** is re-expressed with
  portable strict JSON in a separate test-only change that preserves the
  original pipe-mode error contract (not part of this planning PR).
- **D-D — AI/retrieval parity keeps the R34 target** as a separately gated
  workstream; it does not expand R34's performance-optimization scope.
- **D-E — #1018 stays the tracking umbrella**; split only when a release
  pre-flight needs a separately actionable issue.

## Exception register

| Surface | Kind | Authorization | Scope / reason |
|---|---|---|---|
| `json_compat` (`json_parse`/`json_stringify`/`json_pretty`/`parse_jsonl_record`) | **Permanent host-specific feature** | `docs/design/r26-cpp-data-bridge-contract.md` §5, #1024; reaffirmed in #1341 | Legacy compatibility JSON API; strict JSON (`json_strict`) is the portable surface |
| REPL prompt/banner/history, build tooling, internal representations, host-interop allowlist contents, CI vendor mechanics | Host implementation freedom (not a feature exemption) | R26 REPL contract; R16 policy | Observable portable semantics still required |

Audit result: no other historical "Python-host-only" label (shell stage,
host interop, actors, HTTP, `read_file`/`write_file`, MCP) carries an explicit
permanent-exception authorization; each is scheduled above. None is grandfathered.
