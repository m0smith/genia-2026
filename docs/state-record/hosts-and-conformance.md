# Hosts and conformance record

> **Non-authoritative provenance record.** This file preserves, verbatim and unedited, text that was displaced
> from `GENIA_STATE.md` during the #1099 distillation. It is audit material, not part of the truth hierarchy:
> it does not define Genia behavior, and `GENIA_STATE.md` governs. Start with the release, design, and reference
> documents; open this file only to see the exact displaced wording.
>
> Baseline: `GENIA_STATE.md` at `d401f322c692e8c3620509854065692c2605c61a`. Scope: R16 protocol chronology, R26/R27 C++ host entries, and shared-conformance detail displaced from STATE sections 0 and 1.
> Ledger: `docs/analysis/state-distillation-migration-map.json`.

## B003: baseline lines 19-34

Moved from GENIA_STATE.md@d401f322, lines 19-34 (ledger row B003, retained-condensed, sha256 409f91f0e782552f)

~~~~~markdown
- The implemented shared Semantic Spec System currently executes **eval**, **ir**, **cli**, **flow**, **error**, and **parse** cases.
- The current shared spec runner compares normalized:
  - eval `stdout`
  - eval `stderr`
  - eval `exit_code`
  - cli `stdout`
  - cli `stderr`
  - cli `exit_code`
  - flow `stdout`
  - flow `stderr`
  - flow `exit_code`
  - error `stdout`
  - error `stderr`
  - error `exit_code`
  - IR portable normalized output
  - parse normalized AST (exact match for `kind: ok`) or parse error type + message substring (for `kind: error`)
~~~~~

## B004: baseline lines 35-58

Moved from GENIA_STATE.md@d401f322, lines 35-58 (ledger row B004, moved, sha256 55901d7c9378dae1)

~~~~~markdown
- The working Python implementation lives in:
  - `src/genia/`
  - `tests/`
  - `src/genia/std/prelude/`
  - `hosts/python/` (adapter, normalization, and category execution modules)
- Multi-host documentation/spec scaffolding exists in:
  - `docs/host-interop/`
  - `docs/architecture/core-ir-portability.md`
  - `spec/`
  - `tools/spec_runner/README.md`
  - `hosts/`
- A formal host capability registry contract is documented at `docs/host-interop/capabilities.md`. It is the authoritative reference for capability names, Genia surface, input/output shapes, normalized error behavior, and portability status for each host capability.
- **R16 — Multi-Host Conformance Infrastructure is complete through E16-7** (epic #756; contract at `docs/design/r16-multi-host-conformance-infrastructure-contract.md`). A generic, versioned subprocess host-adapter protocol exists:
  - `tools/spec_runner/protocol.py` (E16-1, issue #758): the JSON request/response envelope for `parse`/`lower`/`eval`/`cli`, stdout/stderr channel separation (evaluated-program output travels only inside `result` fields, never the adapter's own transport stream), and the deterministic outcome taxonomy — an adapter can only ever self-report `ok` or `unsupported`; `protocol_error`/`crash`/`timeout` are always derived by the runner from process/JSON facts, never adapter-reported.
  - `python -m tools.spec_runner --host '<command>'` (E16-2, issue #759): runs applicable discovered cases through that protocol instead of the in-process Python adapter. **The in-process default path (used when `--host` is omitted) is unchanged** and remains available as a developer-optimization path, not the conformance definition.
  - a mandatory `capabilities` protocol operation plus an optional per-case `requires:` field (E16-3, issue #760): `--host` mode fetches and validates a host's capability declaration once per run; a case requiring a capability the host does not declare exactly `supported` is reported `unsupported` without invoking the adapter for it — never silently skipped or counted as passing. Issue #836 adds the capability-gated optional protocol-v1 `eval.input.modules` shape: multi-file cases require `multi_file_eval`, applicability is resolved before request construction, and a v1 host that does not opt in never receives that field. Unknown operation-input fields otherwise remain invalid.
  - `tools/spec_runner/revision.py` (E16-4, issue #761): classifies a host's declared `contract_revision` against this checkout's actual revision using local git history only (never a remote fetch, never rewriting the host's claim) — an exact match is honest pinned-conformance evidence (`current`); a real older commit is current-main-compatibility-only evidence (`resolvable_ancestor`); an unresolvable declaration stops the run with exit code 1 before any case executes.
  - `hosts/python/protocol_adapter.py` (E16-5, issue #762): the Python reference host itself, proven through this same subprocess protocol at full scale — 641 total, 623 passed, 0 failed, 18 unsupported, 0 protocol_error/crash/timeout, identical to the in-process path for every applicable case.
    CI keeps this authoritative full-suite proof in `tests/spec/test_python_protocol_adapter_parity_762.py`, marked `full_conformance`, and runs it nightly or by manual dispatch on canonical Python 3.14 in the dedicated regression `full-conformance` job. Ordinary slow spec-runner pytest coverage runs in the same regression workflow on canonical Python 3.14 with `full_conformance` excluded; supported-version compatibility is established separately by the regression compatibility matrix. This is test organization only and does not change case discovery, protocol behavior, or semantic coverage.
    Issue #883 further deduplicates semantic-spec execution within `tests/spec/`: `test_spec_ir_runner_blackbox.py` and `test_cli_shared_spec_runner.py` previously replayed most of the shared corpus (parametrized over nearly every eval/ir/cli/flow/error fixture) purely to prove runner wiring; they now execute a small representative sample per category instead, and the expensive `command_mode_collect_sum` CLI fixture is kept unique to a single pytest file. The full corpus is still proven once per supported Python version by `python -m tools.spec_runner` in the regression compatibility matrix, and once on Python 3.14 in routine CI; no shared case, expected result, or discovery assertion changed. This is test organization only.
  - [`m0smith/genia-cpp`](https://github.com/m0smith/genia-cpp) (R25): the first external production host, implementing the deliberately bounded R24 parser -> portable Core IR -> evaluator floor plus R25 Ref, Cell, and local Process capabilities with pinned R16 evidence. It is not feature-parity with Python; `hosts/cpp/` here remains a pointer to that repository (see `hosts/cpp/README.md`).
  - `tools/spec_runner/evidence.py` and `--evidence <path>` (E16-7, issue #764): one deterministic per-host JSON evidence document (contract revision, protocol version, capabilities, applicable-case count, full outcome taxonomy), a pure function of its inputs so identical runs produce byte-identical evidence. Proven against both the Python reference host (623 pass / 18 unsupported / 0 else, revision `current`) and the `genia-cpp` bootstrap placeholder (641 unsupported / 0 else, revision `resolvable_ancestor`). See `docs/strategy/roadmap/multi-host-conformance-policy.md`'s "Evidence model and CI expectations" for the external-host CI contract this defines.
  - `tools/spec_runner/host_parity_gate.py` and `spec/known_host_gaps.json` (pre-flight issue #1018, the first use of the R26+ Change Pre-Flight process): a CI/process-only gate over the existing E16-7 evidence documents. It compares a Python evidence document against a C++ evidence document at the `spec/manifest.json` optional-capability granularity: a capability the C++ host does not declare `supported` must have a matching, reasoned, issue-backed entry in `spec/known_host_gaps.json` or the gate fails as an undocumented gap; each manifest entry must include a GitHub issue reference, affected host, affected tests or spec area, short reason, and removal condition; a manifest entry whose capability the host now declares `supported` also fails, as a stale/closed gap that must be removed from the manifest; and a nonzero `fail`/`protocol_error`/`crash`/`timeout`/`invalid` count in either evidence document always fails the gate regardless of gap bookkeeping. It adds no new protocol, evidence format, or capability registry. `.github/workflows/host-parity.yml` runs it in CI whenever `spec/**`, `src/genia/**`, `hosts/**`, or `tools/spec_runner/**` change, reusing the same Docker dev image, `genia-cpp` checkout, and build/run steps already proven by `.github/workflows/docker-dev-environment.yml` (which remains scoped to proving the development image only, per `docs/architecture/development-container.md`).

~~~~~

## B005: baseline lines 59-72

Moved from GENIA_STATE.md@d401f322, lines 59-72 (ledger row B005, retained-condensed, sha256 04f3d1fa101ca766)

~~~~~markdown
Scaffolded or planned, not implemented as hosts:

- Node.js, Java, Rust, Go: planned only, not implemented.
- C++: R25 is complete through its reviewed PR stack in `m0smith/genia-cpp`. In addition to the bounded R24 floor, it supports the independently gated portable `refs`, `cell_primitives`, and local `process_primitives` contracts. Final E25-5 evidence is `762 total / 149 pass / 613 unsupported`, with every failure-class count zero; the exact E25-5 contract revision and C++ evidence commit are recorded in `docs/releases/R25.md`. Actor remains unsupported and belongs to R38. C++ is a genuine second host, not Python feature parity.
- `hosts/python/` is the adapter location, but the core runtime remains in `src/genia/`.
- **A generic multi-host runner now exists** (`tools/spec_runner --host`, R16 E16-1 through E16-7, above). No second production host implements the full language. `m0smith/genia-cpp` is the R25-complete second host for a deliberately bounded, evidence-backed subset; other external-host proofs remain either Python-reference-host evidence or non-semantic protocol fixtures.

**Maturity:**

- Shared host contract is **Partial**: the contract categories above are documented, and executable shared spec coverage is implemented for `eval`, `ir`, `cli`, first-wave `flow`, initial `error`, and initial `parse` behavior in the Python reference host. Other hosts are not implemented.
- Semantic Spec System is **Experimental**: the file format, runner, and initial case inventory exist for `eval`, `ir`, `cli`, first-wave `flow`, initial `error`, and initial `parse` behavior in this phase.
- Flow behavior is implemented in Python, and shared semantic-spec coverage for flow is now **active but partial**. Current flow shared coverage is limited to first-wave cases proving lazy pull-based observable behavior through early termination, single-use enforcement, deterministic outputs, `evolve(init, f)` progression, `refine(..steps)` behavior, `rules(..fns)` compatibility behavior, `step_*` / `rule_*` equivalence, the `rules()` identity stage, selected rule result defaulting/no-effect behavior, focused Flow `map` / `filter` / `scan` coverage, selected Seq-compatible `each` / `collect` / `run` / `reduce` terminal behavior, and a resource lifecycle case (`seq-finalization-drop-take`) proving Flow-aware `drop |> take |> collect` composition with bounded pulling and correct output. Advanced Flow behavior is not covered by shared semantic specs in this phase.
- IR stability remains **Partial**: the minimal portable Core IR contract is documented with field-level lowering invariants (bare `none` reason=null, `none()` reason wrapped as `IrQuote`, canonical `lhs.name` -> `IrBinary(op=SLASH, named_access=true)` for narrow named access (ordinary slash/division lowers as `IrBinary(op=SLASH)` without `named_access`; legacy `lhs/name` compatibility removed); neither form is general field-path lookup, `IrAssign` placement in `IrBlock.exprs`, optional fields), the Python runtime guards that boundary, and shared semantic-spec case coverage now validates the full portable node family in the Python reference host, including `quasiquote` bodies with `unquote` and `unquote_splicing` in list context.

~~~~~

## B006: baseline lines 73-107

Moved from GENIA_STATE.md@d401f322, lines 73-107 (ledger row B006, retained-condensed, sha256 79609a3b25f7e2cc)

~~~~~markdown
**Explicit limitations:**

- Python is the full-language production host; `m0smith/genia-cpp` is the R25-complete second production host for the bounded floor recorded above. All other hosts (Node.js, Java, Rust, Go) are planned or scaffolded only.
- No browser runtime or playground is implemented; browser artifacts are documentation only.
- A generic multi-host runner exists (`tools/spec_runner --host`, R16 E16-1 through E16-7); `m0smith/genia-cpp` supplies the completed R24 external-host evidence while Python remains the full-language reference.
- Shared semantic-spec case files currently exist under `spec/eval/`, `spec/ir/`, `spec/cli/`, `spec/flow/`, `spec/error/`, and `spec/parse/` in this phase.
- Parse shared semantic-spec coverage is limited to initial cases for stable, already-implemented syntax forms; parse spec coverage expands only when new forms are explicitly added and tested.
- Flow is implemented as a lazy, pull-based, single-use runtime value; async, multi-port, and advanced flow features are not present.
- Flow orchestration supports both `refine(..steps)` (preferred) and `rules(..fns)` (compatibility); both are available and behave identically.
- Step/rule helpers are available as both `step_*` (preferred) and `rule_*` (compatibility) names.
- Flow shared semantic-spec coverage is limited to first-wave observable cases only; advanced Flow behavior remains uncovered in shared specs.
- CLI contract covers file, command, pipe, and REPL modes as described; no shell tokenization, `$1`/`$2`/`ARGV`-style, or advanced CLI features exist.
- **R26-1 REPL portability contract (issue #1023):** the smallest portable
  `repl` boundary is now approved in
  `docs/design/r26-cpp-repl-contract.md`. It covers no-argument mode
  selection, persistent successful bindings across complete submissions,
  multiline submission without standardizing Python's completeness
  heuristic, canonical debug-result echo (including `none("nil")`) to
  `stdout`, normalized diagnostics to `stderr` with session recovery,
  successful EOF termination, and no implicit `main` dispatch. Banner/prompt
  text, terminal editing/history, signals, Python colon commands, and
  cross-stream timing remain host-local. Shared executable REPL evidence now
  exists (three capability-gated `cli` cases declaring `requires: [repl]`:
  `repl_persistent_binding_basic`, `repl_failed_submission_diagnostic`,
  `repl_none_result_rendering`) and passes against the Python reference host.
  At the time this contract was approved, C++ still declared `repl`
  unsupported with the known-gap entry pending this evidence and a
  `PARITY_OK` host-parity result; both are now satisfied -- see the
  following "R26-1 C++ scripted REPL" entry for the completed state. This
  contract itself adds no C++ implementation or Python/C++ feature-parity
  claim. Making that evidence honestly comparable required one
  narrow Python reference-host fix: `repl()` no longer writes its banner or
  `>>> `/`... ` prompts to `stdout` when `stdin` is not an interactive tty,
  since section 3 already documented them as host-local, non-portable
  cosmetics that must not appear in the portable observation.
~~~~~

## B007: baseline lines 108-151

Moved from GENIA_STATE.md@d401f322, lines 108-151 (ledger row B007, retained-condensed, sha256 630262bcdbacb72c)

~~~~~markdown
- **R26-1 C++ scripted REPL (issue #1023, `genia-cpp`):** the C++ adapter
  retains one environment across complete submissions, renders each result,
  reports normalized submission failures, and continues after a failure.
  All three `requires: [repl]` shared CLI cases pass. The pinned C++ evidence
  is `772 total / 149 pass / 623 unsupported` with zero failure classes;
  the host parity gate reports `repl` as `PARITY_OK` after removing its
  stale known-gap entry. Interactive prompt/banner/history behavior remains
  host-local. Strict JSON is tracked separately by #1024.
- **R26-2 reference-host defect repairs (issue #1024):** `docs/analysis/r26-release-size-preflight.md`'s
  preflight probing found genuine Python reference-host defects in the
  bytes/JSON boundary that a future C++ host must not inherit; three are
  now repaired:
  - `GeniaDecimal._as_fraction()` (used by `stable_json_decimal`, and
    therefore by `json_decode`/`json_encode` on every fraction/exponent
    number) now rejects an exponent whose `10 ** exponent` expansion would
    exceed the existing private numeric resource-limit bound before
    attempting that expansion, raising the same
    `NumericResourceLimitError` R22 already uses for this failure class.
    Previously, a small-magnitude exponent (e.g. from decoding
    `"1e999999999"`) passed the constructor's own bit-length check but
    still expanded to an astronomically large integer, an unbounded
    resource-exhaustion hang reachable from ordinary Genia source.
  - `_runtime_type_name` (the portable type-name table every diagnostic
    boundary uses) now has an explicit `GeniaSymbol` branch returning
    `"symbol"`. Previously, a bare symbol is not a `str` subclass and has
    no explicit branch, so it fell through to Python's own
    `type(value).__name__`, and `json_encode(quote(a))` leaked the raw
    class name `"GeniaSymbol"` as `value_type` -- the same leak class the
    E23-6 diagnostics sweep already repaired for other unsupported kinds,
    just never exercised with a symbol value.
  - `json_parse`, `parse_jsonl_record`, `json_stringify`, and `json_encode`
    now normalize `RecursionError` from deeply nested input into their
    existing clean, deterministic diagnostic shape (`none("json-parse-error", ...)`,
    `err("invalid_jsonl_record", ...)`, `none("json-stringify-error", ...)`,
    and `err("json_nesting_too_deep", ...)` respectively), matching strict
    `json_decode`'s existing `RecursionError` handling. Previously, deep
    nesting (or, for encode/stringify, a deeply nested protected-value
    check that ran before any try block) raised a raw uncaught Python
    `RecursionError` with the literal message "maximum recursion depth
    exceeded" straight through the boundary.
  These are diagnostics-cleanliness and resource-safety repairs only -- no
  JSON value mapping, limit, or Outcome shape changed for any input that
  was already well-behaved. See `tests/unit/test_r22_misuse_resource_limits_894.py`
  and `tests/unit/test_r23_e23_6_diagnostics_sweep.py`.
~~~~~

## B008: baseline lines 152-178

Moved from GENIA_STATE.md@d401f322, lines 152-178 (ledger row B008, retained-condensed, sha256 92e35be9b590c089)

~~~~~markdown
- **R26-2 E26-0 data bridge contract (issue #1024):** the portable
  `bytes_utf8`/`json_strict` boundary is approved in
  `docs/design/r26-cpp-data-bridge-contract.md`. It restates and pins
  already-implemented behavior only (key-sort basis, escape set, layout,
  BOM rejection, `line`/`column` semantics, error precedence, the
  `value_type` vocabulary, and the numeric/nesting resource bounds) -- no
  JSON/Bytes value mapping, limit, or Outcome shape changes. It inherits
  R24/E24-7's numeric codec path and R9 facet carrier rather than
  re-deriving them, decides compatibility JSON
  (`json_parse`/`json_stringify`/`json_pretty`, plus `parse_jsonl_record`)
  is **not portable** and remains Python-host-only, narrows the malformed-
  `utf8_decode` portable claim to well-formed input only (Genia source
  cannot construct arbitrary malformed bytes today), and removes ZIP from
  R26 entirely (deferred, contract-first, roadmap home TBD).
  `spec/manifest.json` now declares `bytes_utf8`, `json_strict`, and
  `json_compat` in place of the retired `bytes_json_zip` bundle; every
  previously-ungated JSON/Bytes/compatibility-JSON shared case is
  retro-gated with the matching `requires:` tag, and the missing coverage
  this contract identified (nesting 128/129 boundary for decode and
  encode, lone-vs-paired surrogate handling, duplicate-key `key` context,
  BOM rejection, key-sort basis, escape-set/layout rules) is added as new
  `spec/eval/*.yaml` cases, all passing against the Python reference host
  (`spec/known_host_gaps.json` tracks `bytes_utf8`/`json_strict` as
  issue-backed C++ gaps and `json_compat` as a permanent-by-design
  Python-host-only classification). C++ implementation had not started
  as of this gating; see the following entry for `bytes_utf8`'s
  completion.
~~~~~

## B009: baseline lines 179-192

Moved from GENIA_STATE.md@d401f322, lines 179-192 (ledger row B009, retained-condensed, sha256 ea2bd439f014d693)

~~~~~markdown
- **R26-2 C++ `bytes_utf8` (issue #1024, `genia-cpp`):** `genia-cpp`
  implements `utf8_decode` for well-formed UTF-8 input (an in-house RFC
  3629 validator, `src/utf8.hpp` -- no ICU, per the R24 dependency policy;
  malformed input or a non-Bytes argument stays honestly `unsupported`,
  never guessed at) and `<bytes N>` display rendering (`src/render.hpp`,
  matching `GeniaBytes.__repr__` verbatim), closing the sole
  `requires: [bytes_utf8]` shared case,
  `spec/eval/r19-unicode-utf8-encode-decode-roundtrip.yaml`. `genia-cpp`
  now declares `bytes_utf8` supported and `tools/spec_runner/host_parity_gate.py`
  reports it `PARITY_OK`; its `spec/known_host_gaps.json` entry has been
  removed. Bytes-value structural equality was already required R18
  baseline conformance, ungated by this capability. `json_strict` and
  `json_compat` remain unimplemented by `genia-cpp` and are unaffected by
  this change.
~~~~~

## B010: baseline lines 193-215

Moved from GENIA_STATE.md@d401f322, lines 193-215 (ledger row B010, retained-condensed, sha256 3787b40a4947e613)

~~~~~markdown
- **R26-2 C++ `json_strict` (issue #1024, `genia-cpp` PR #33):** `genia-cpp`
  widens R24's E24-7 scalar-numeric-only `json_decode`/`json_encode` slice
  to the full contract grammar -- objects, arrays, strings (with `\uXXXX`
  surrogate-pair combination and Unicode-scalar validation), booleans,
  `null` (decoding to `none("nil")`), nesting bounded at exactly 128
  containers for both decode and encode, duplicate-object-key rejection
  with the key in context, a leading BOM correctly not accepted as
  insignificant whitespace, and deterministic sorted-key/2-space-indented
  encode layout -- reusing E24-7's numeric codec unchanged (no second
  numeric parser). `json_decode`/`json_encode` accept exactly one outer
  `json`-represented layer, and a non-String/Bytes `json_decode` argument
  raises the exact contract-required `TypeError`. `genia-cpp` now declares
  `json_strict` supported; `spec/known_host_gaps.json`'s entry has been
  removed. Pinned C++ evidence: `772 total / 178 pass / 594 unsupported`
  with every failure-class count zero; every `requires: [json_strict]`
  shared case passes except `spec/flow/json-representation-template-flow.yaml`,
  which needs Template/Flow features (`pattern`, `refinement_match`,
  `open_shape_match`, `validate_each`, `collect`) genuinely outside this
  bounded host's floor and stays honestly `unsupported`.
  `tools/spec_runner/host_parity_gate.py` reports `json_strict`
  `PARITY_OK`. `json_compat` remains unimplemented by `genia-cpp`
  (permanent, by contract) and is unaffected by this change. This closes
  R26-2 and, with R26-1's completed scripted REPL, completes R26.
~~~~~

## B011: baseline lines 216-235

Moved from GENIA_STATE.md@d401f322, lines 216-235 (ledger row B011, retained-condensed, sha256 620ce2464354cd32)

~~~~~markdown
- **R27 C++ Flow phase 1 and pipe mode (issues #1035, #1038, #1047, #1049;
  `genia-cpp` PRs #34, #35, #36):** `genia-cpp` implements the portable Flow
  runtime kernel -- lazy, pull-based, single-use Flow with `stdin`/list `lines`,
  `evolve`, `map`/`filter`/`take`/`drop`/`scan`/`keep_some`/`each`, and
  `collect`/`run`/`reduce` -- and `genia -p '<stage expr>'` pipe mode, and declares
  `flow_phase_1` and `cli_pipe_mode` supported. The claim is exactly the shared
  cases that carry `requires: [flow_phase_1]` (37) or `requires: [cli_pipe_mode]`
  (16); all 53 pass. Pinned C++ evidence: `793 total / 257 pass / 536 unsupported`
  with every failure-class count zero (Python: `793 total / 775 pass / 18
  unsupported`). `tools/spec_runner/host_parity_gate.py` reports both capabilities
  `PARITY_OK` and their `spec/known_host_gaps.json` entries are removed. C++
  limits: no trailing script arguments after `-p <expr>`; `argv()` only in pipe
  mode; `upper`/`trim`/`parse_int` decide ASCII input only; `tee`/`merge`/`zip`,
  `rules`/`refine`, list-form `scan`, Flow display, and a pipeline inside call
  arguments are unsupported; the config/model/Template/JSON cross-release Flow and
  pipe cases stay Python-host-only. The HTTP server (#1041) and outbound HTTP
  (#1043) were decided **not** part of R27: both remain Python-host-only with
  tracked C++ gaps. This adds no language behavior; Python semantics are
  unchanged. See `docs/releases/R27.md` and
  `docs/analysis/r27-release-truth-audit.md`.
~~~~~

## B015: baseline lines 289-302

Moved from GENIA_STATE.md@d401f322, lines 289-302 (ledger row B015, retained-condensed, sha256 74aab7dae845884f)

~~~~~markdown
- Coverage is still partial and experimental; see below for category status.

PYTHON REFERENCE HOST:

- Python is the full-language reference host; C++ implements the bounded R27 floor.
- All conformance is validated against the Python reference host.
- The current shared spec runner executes eval cases (`spec/eval/`), comparing normalized `stdout`, `stderr`, and `exit_code`. Eval shared coverage includes list-side Seq-compatible `collect`, `run`, lazy `each`, item-preserving `each |> collect`, the existing `seq-compatible-list-transform-chain` fixture, list-side `scan` (accepting list input and returning list), Seq-compatible non-list/non-Flow diagnostics for `each`, `collect`, `run`, `map`, `filter`, `take`, `drop`, and `scan`.
- The current shared spec runner executes CLI cases (`spec/cli/`) through the Python host adapter, comparing normalized `stdout`, `stderr`, and `exit_code`.
- The current shared spec runner executes Flow cases (`spec/flow/`) through command-source execution in the Python host adapter, comparing normalized `stdout`, `stderr`, and `exit_code`. Flow shared coverage includes first-wave cases proving lazy pull-based observable behavior through early termination, single-use enforcement, deterministic outputs, `evolve(init, f)` progression, `refine(..steps)`, `rules(..fns)`, `step_*` / `rule_*` equivalence, `rules()` identity, selected rule result defaulting/no-effect behavior, deterministic `keep_some(...)` option-filtering behavior, focused core stdlib Flow coverage for direct `map`, `filter`, and `scan` over Flow inputs, including composed `map`/`filter` and bounded `evolve |> scan |> take |> collect` cases; Seq-compatible terminal coverage for `each` preserving items, `each(print) |> run`, `collect` materialization, and `reduce` accumulation over Flow; and a resource lifecycle case (`seq-finalization-drop-take`) proving Flow-aware `drop |> take |> collect` composition with bounded pulling and correct output.
- The current shared spec runner executes error cases (`spec/error/`) through the same eval execution path used by eval cases, comparing exact normalized `stdout`, exact normalized `stderr`, and exact `exit_code`.
- CLI shared spec coverage proves deterministic non-interactive file mode, `-c` command mode, `-p` pipe mode behavior, and selected native `--test` mode outcomes. Current shared CLI coverage includes basic file execution, file-mode `main(argv())` dispatch, trailing `argv()` exposure, command-mode final-value execution, valid pipe-mode Flow-stage usage, explicit `stdin` / `run` rejection, current pipe-mode guidance for bare per-item stages, bare reducers, and non-Flow final results, plus selected native test-runner passing, runtime-erroring, and discovery-error suite outcomes. REPL mode is covered only by the three capability-gated `requires: [repl]` cases described above (issue #1023); every other REPL scenario remains uncovered by shared executable specs.
- The observable CLI shared-spec contract is limited to `stdout`, `stderr`, and `exit_code`.
- The observable error shared-spec contract in this phase is limited to `stdout`, `stderr`, and `exit_code`.
- Eval shared spec cases are loaded from YAML files under `spec/eval/`; each case provides source text plus optional stdin text and is executed independently.
~~~~~

## B016: baseline lines 303-319

Moved from GENIA_STATE.md@d401f322, lines 303-319 (ledger row B016, retained-condensed, sha256 2f242f285b264a9c)

~~~~~markdown
- Error shared spec cases are loaded from YAML files under `spec/error/`; each case provides source text plus optional stdin text, requires `stdout: ""`, exact `stderr`, and `exit_code: 1`, and may include informational `notes` that are not machine-asserted.
- Shared spec YAML loading prefers `PyYAML`; when `PyYAML` is unavailable, the runner can fall back to a Ruby YAML bridge in the current implementation.
- The current eval shared case inventory covers deterministic command-source eval output for:
  - final rendered expression results
  - direct `stdout` output
  - direct `stderr` output
  - combined `stdout`/`stderr` output separation
  - stdin-fed eval cases whose compared surface remains `stdout`, `stderr`, and `exit_code`
  - direct Option rendering for deterministic final-result output (`some(...)`, `none(...)`)
  - pipeline Option propagation for deterministic final-result output (`some(...)` lift and `none(...)` short-circuit)
  - deterministic pattern matching output for currently implemented pattern families (first-match behavior, literals, wildcard/variable binding, list/tuple/map, option, guard, glob, and named reusable pattern forms)
  - deterministic eval failures with exact `stderr` and `exit_code`, including Flow/value boundary errors: `each` given a list, `first` given a Flow, `reduce` given a non-Seq-compatible value (int, string)
  - focused core stdlib list/absence helper behavior: `map` over lists (basic and empty), `filter` over lists (basic, no-match, and Option-element callbacks), `first` (some and empty-list), `last` (some and empty-list), `nth` (in-range and out-of-bounds)
  - selected validation helper behavior: optional field present/absent/invalid outcomes, required field present success, and simple nested validation path success/missing diagnostics (Partial; Python reference host only)
  - `collect_validated/1` behavior: empty source, all-clean, mixed `some`/`none`/`err`, `some` context ignored on clean path, bare `none`, `err` without context, and Flow-compatible source (Experimental; initial coverage only)
  - selected `validate_each/2` behavior: empty list, `some(...)` preservation, and mixed `some(...)` / `none(...)` / `err(...)` preservation (Experimental; initial coverage only)
  - `validate_each/2` output feeding `collect_validated` directly: shared eval coverage proves mixed Outcome results from validation helpers aggregate into clean values plus skipped/error diagnostics. Experimental; initial coverage only.
~~~~~

## B017: baseline lines 320-334

Moved from GENIA_STATE.md@d401f322, lines 320-334 (ledger row B017, retained-condensed, sha256 e3937f66dde010ee)

~~~~~markdown
- Eval normalization is limited to line-ending normalization for `stdout` and `stderr` (`\r\n` and `\r` normalize to `\n`).
- Eval comparison is otherwise exact: `stdout`, `stderr`, and `exit_code` must match exactly after that line-ending normalization.
- Error normalization is limited to the same line-ending normalization used for eval `stdout` and `stderr` (`\r\n` and `\r` normalize to `\n`).
- Error comparison is otherwise exact in this phase: `stdout` must be `""`, `stderr` must match exactly after that line-ending normalization, and `exit_code` must be `1`.
- The current shared spec runner also executes IR cases (`spec/ir/`), comparing normalized portable Core IR output before host-local optimization.
- Error shared coverage is active but initial only: the current inventory proves a narrow normalized error surface (including deterministic pattern miss, guard-all-fail, malformed-glob, named-pattern error cases, and selected `validate_each/2` misuse diagnostics: non-list/non-Flow source, non-callable validator, and non-Outcome validator result) and does not machine-assert structured phase/category/message fields.
- The current shared spec runner executes Parse cases (`spec/parse/`) by calling the Python host parse adapter directly; for `kind: ok` cases the normalized AST is compared exactly; for `kind: error` cases the error type is compared exactly and the message is matched as a substring.
- The current shared spec runner accepts `-v` / `--verbose`, printing each spec name before execution starts and then a single timing line (`<name>\t<elapsed>s`) after each spec completes.
- Parse shared coverage is active but initial only: the current inventory covers stable, already-implemented syntax forms, and now includes named pattern declaration (`pattern Name(value) = body`) and named pattern use in case arms (`Name(inner_pattern)`), including error cases for invalid declaration and use arity. Parse spec coverage expands only when new forms are explicitly added and tested.
- Uncovered or partial categories are not guaranteed and may differ in future implementations.

**Summary:**
- `eval`, `ir`, `cli`, first-wave `flow`, initial `error`, and initial `parse` are active for executable shared spec files.
- `GENIA_STATE.md` is the final authority for implemented behavior. All other docs/specs must align with this contract.

~~~~~

## B018: baseline lines 335-349

Moved from GENIA_STATE.md@d401f322, lines 335-349 (ledger row B018, retained-condensed, sha256 85df40300b1f3c3f)

~~~~~markdown
**Host implementation location:**
- The working Python implementation lives in `src/genia/`, `tests/`, and `src/genia/std/prelude/`.
- `hosts/python/` is the active host adapter layer; it is not the core runtime source location (that remains `src/genia/`).
- `hosts/python/adapter.py::run_case(spec: LoadedSpec) -> ActualResult` is the canonical adapter entrypoint, wired to the shared spec runner via `tools/spec_runner/executor.py::execute_spec`. All spec categories route through `run_case`.

**Planned/Scaffolded:**
- Node.js, Java, Rust, Go: planned only, not implemented; C++ is the bounded R27 production host in `m0smith/genia-cpp`
- A generic multi-host runner exists (`tools/spec_runner --host`, R16 E16-1 through E16-7; see §0 above), with pinned evidence for the bounded C++ R24 host

**Limitations:**
- Only Python is implemented; all other hosts are planned or scaffolded only.
- No browser runtime or playground is implemented; browser artifacts are documentation only.
- Shared semantic-spec case files exist under `spec/eval/`, `spec/ir/`, `spec/cli/`, `spec/flow/`, `spec/error/`, and `spec/parse/` in this phase.
- Parse shared semantic-spec coverage is initial only; coverage expands only when new forms are explicitly added and tested.

~~~~~
