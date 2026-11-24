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
| `json_strict` hidden partial | `flow/json-representation-template-flow` | #1018 | R31 (follows Templates row) |

### C. Ungated shared cases unsupported on C++ (493; no capability flag)

| Family (case-id evidence) | ≈Cases | Proposed target | Notes |
|---|---:|---|---|
| Value templates/representations, refinement, named patterns, open/exact shapes, schema (`template-*`, `representation-*`, `exact-shape-*`, `open-shape-*`, `named-pattern-*`, `json-schema-*`, `error-template-*`) | ~95 | R31 for demonstrated Sheet prerequisites; remainder R32 | D-A |
| Validation/diagnostics/`collect_validated`/`validate_each`/`parse_csv` | ~60 | R31 for demonstrated Sheet prerequisites; remainder R32 | D-A |
| Format strings (`format-*`, `error-format-*`) | ~65 | R31 for demonstrated Sheet prerequisites; remainder R33 | D-A |
| Core stdlib and patterns: Option/Outcome patterns, `apply_raw`, `as_seq`, seq-compatible, map/pair helpers, glob/list patterns, quote/quasiquote/`delay`, unary ops, call spread, lambda varargs, imports, R18 equality, R19 Unicode, R21 parse errors, R22 exact-numeric errors, Model B CLI/eval cases | ~150 | R31 for demonstrated Sheet prerequisites; remainder R33 | D-A |
| Flow beyond phase 1: `tee`/`zip`/`merge`, `rules`/`refine`, Flow `reduce`/display, `rand` flows | ~12 | R32 (Flow) | `rand` simulation flows → R36 |
| Configuration resolution and protected values (`config-*`, `secret-*`, `protected-secret-*`, `r10-*`, `r13-*`, `r18-protected-*`) | ~30 | R32 | protected values/lifecycle per baseline |
| Lifecycle (`r14-*`) | 2 | R32 | |
| AI/retrieval cross-release (`model-fixture-*`, `r11-*`, `r12-*`, `chunk-*`) | ~20 | R34 | |
| CLI file-mode argv/`--`/`main(argv)` (`file_mode_*`) | 3 | R33 | |
| Native test runner CLI (`native_test_runner_*`) | 3 | R39 | |
| `pipe_mode_record_pipeline_collect_validated_boundary_error` | 1 | R31 (separate test-only change, #1018) | D-C: re-express with strict JSON |

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

## Dependency check and maintainer decisions

Dependencies checked: R31 Sheet parity depends on whichever template,
validation, prelude and core-library cases the `sheet_values` shared cases
actually exercise. R32 configuration snapshots depend on protected values;
outbound HTTP (R37) depends on protected values (R32) and `import`; serving
(R37) depends on annotations/`serve` (R33); R34 AI/retrieval depend on R32
protected values and the R31/R32 template rows. No dependency points backwards.

Maintainer decisions recorded on #1341 (2026-11-24):

- **D-A — R31 is not enlarged by ~370 cases.** R31 acceptance requires only
  C-family cases that the R31 pre-flight *demonstrates* are Sheet
  prerequisites. Remaining template/validation parity targets R32; remaining
  format-string and core-stdlib/pattern parity targets R33. Either target may
  move only by a later maintainer decision.
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
