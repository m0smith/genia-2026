
# Shared Spec Runner

The shared spec runner loads shared spec cases, executes them against the Python reference host, and compares normalized observable outputs.

**Python is the only implemented host today.**

## Runner Scope (Current Phase)

- **Active categories:** `eval`, `ir`, `cli`, `flow`, `error`, `parse` (executable shared spec files)
- YAML spec files are loaded from `spec/eval/`, `spec/ir/`, `spec/cli/`, `spec/flow/`, `spec/error/`, and `spec/parse/`
- The loader uses one shared top-level envelope for active executable categories: `name`, `id`, `category`, `description`, `input`, `expected`, and `notes`
- Comparison fields:
  - eval: `stdout`, `stderr`, `exit_code`
  - cli: `stdout`, `stderr`, `exit_code`
  - flow: `stdout`, `stderr`, `exit_code`
  - error: `stdout`, `stderr`, `exit_code`
  - ir: normalized portable Core IR
  - parse: normalized AST (exact match for `kind: ok`) or error type + message substring (for `kind: error`)

Browser execution is planned to use the Python reference host on a backend service in the current playground direction; this does not add a second implemented host today.

## Dependencies

- Preferred: `PyYAML` in the active Python environment.
- Fallback: if `PyYAML` is unavailable, the loader can use a Ruby runtime with `YAML` support to parse shared spec files.

## How to run the spec suite

```bash
python -m tools.spec_runner
```

```bash
python -m tools.spec_runner --verbose
```

Verbose mode prints each spec name before execution starts, then prints a timing line after execution in the form `<spec-name>\t<elapsed>s`.

## How it works

- Cases are loaded from `spec/eval/*.yaml`, `spec/cli/*.yaml`, `spec/ir/*.yaml`, `spec/flow/*.yaml`, `spec/error/*.yaml`, and `spec/parse/*.yaml`
- Each case is executed independently against the Python reference host via `execute_spec` in `tools/spec_runner/executor.py`, which delegates to `hosts/python/adapter.py::run_case`
- CLI cases are executed through the Python host adapter
- Flow cases are executed through command-source execution in the Python host adapter; the runner does not route Flow cases through CLI pipe mode
- Error cases reuse the eval execution path; there is no separate error subprocess or error-specific execution path
- Parse cases call the Python host parse adapter directly (`parse_and_normalize`); no subprocess is invoked
- CLI file mode uses `input.file`; command mode uses `input.command` with empty `input.stdin`; pipe mode uses `input.command` as `-p <command>` when `input.stdin` is non-empty, with that stdin passed directly as subprocess input; native test mode uses `input.test`
- The runner does not construct shell pipelines for CLI specs
- Eval, CLI, and Flow cases normalize `stdout`/`stderr` line endings before comparison
- Error cases use the same line-ending normalization as eval before comparison
- The current CLI suite covers deterministic non-interactive file, command, pipe, and selected native test-mode cases, including file-mode `main(argv())` dispatch, command-mode final-value execution, valid pipe-mode Flow-stage usage, current pipe-mode guidance/error cases for explicit `stdin`, explicit `run`, bare per-item stages, bare reducers, non-Flow final results, and selected native test-runner passing, runtime-erroring, and discovery-error suite outcomes. REPL is not covered by shared executable specs
- The current Flow suite covers first-wave observable contract cases only: lazy pull-based observable behavior through early termination, single-use enforcement, deterministic outputs, `evolve(init, f)` progression, `refine(..steps)`, `rules(..fns)`, `step_*` / `rule_*` equivalence, `rules()` identity, selected rule result defaulting/no-effect behavior, error propagation via invalid-reducer-on-flow diagnostic, focused Flow `map` / `filter` / `scan` behavior, and selected Seq-compatible terminal behavior
- The current Error suite covers initial normalized observable contract cases only: `stdout`, `stderr`, and `exit_code`, with `stdout` expected to be `""`, `stderr` matched exactly, and `exit_code` expected to be `1`
- IR cases normalize portable Core IR before comparison and fail if host-local optimized IR appears in the shared IR path
- Failures are reported per spec with expected vs actual fields
- `notes` is informational only and is not read by the runner; phase/category/message remain contract concepts, not structured runner fields in this phase

**Example failure output:**

```
FAIL eval arithmetic-basic (/path/to/spec/eval/arithmetic-basic.yaml)
  field: stdout
    expected: '42\n'
    actual:   '41\n'
```

**Normalization:**
- For eval, the runner normalizes line endings for `stdout`/`stderr` to `\n`; trailing newlines remain significant.
- For flow, the runner normalizes line endings for `stdout`/`stderr` to `\n`; trailing newlines remain significant.
- For cli, the runner normalizes line endings for `stdout`/`stderr` to `\n` and strips trailing newlines before comparison.
- For error, the runner normalizes line endings for `stdout`/`stderr` to `\n`; trailing newlines remain significant.
- Internal whitespace is not trimmed or collapsed. Stderr is not otherwise normalized.
- For eval, cli, flow, and error, the compared surface remains only `stdout`, `stderr`, and `exit_code`
- For IR, the runner compares normalized host-neutral portable Core IR output
- For IR, execution flow is `source -> parse -> lower -> normalize -> compare`
- For parse, the runner compares the normalized parse result: exact AST match for `kind: ok`; type exact + message substring for `kind: error`
- It does not trim meaningful whitespace

**GENIA_STATE.md is the final authority for implemented behavior. All other docs/specs must align with this contract.**

## E16-1 host-adapter protocol module (issue #758)

`tools/spec_runner/protocol.py` implements the versioned subprocess
host-adapter protocol approved by the R16 E16-0 contract
(`docs/design/r16-multi-host-conformance-infrastructure-contract.md`):

- a JSON request envelope (`protocol_version`, `case_id`, `operation`,
  `input`) for the `parse`, `lower`, `eval`, and `cli` operations
- a JSON response envelope (`protocol_version`, `case_id`, `operation`,
  `status`, `result`, `unsupported_reason`) that an adapter process writes,
  and nothing else, to its own stdout
- `run_adapter_request` spawns exactly one adapter process per request,
  writes the request to its stdin, and classifies the result
- the deterministic outcome taxonomy: an adapter can only ever self-report
  `ok` or `unsupported`; `protocol_error` (malformed/invalid envelope),
  `crash` (nonzero exit), and `timeout` (exceeded the caller's timeout) are
  always derived by the runner from process-level and JSON-validity facts,
  never self-reported by the adapter

**Status: implemented as a standalone module, proven only against the
deterministic fixture adapter in this phase.** It is not yet wired into
`tools/spec_runner`'s case execution (`execute_spec`/`main` still call the
Python adapter in-process, exactly as before) — that generic external-host
execution path is E16-2 (issue #759). This module adds no new adapter
operation beyond the four existing ones; `capabilities` is added by E16-3
(issue #760).

`tools/spec_runner/fixtures/protocol_fixture_adapter.py` is a deterministic,
non-semantic fixture used only to prove protocol mechanics and every outcome
in the taxonomy end-to-end (see `tests/unit/test_spec_runner_protocol.py`).
It is not a Genia host and must not be treated as one.

## E16-2 generic external-host execution path (issue #759)

`python -m tools.spec_runner --host '<command>'` runs every applicable
discovered case through an external adapter command speaking the E16-1
protocol instead of the in-process Python adapter. Pass the full adapter
command as one shell-quoted string, e.g.:

```bash
python -m tools.spec_runner --host 'python3 -m my_host.adapter' --host-timeout 10
```

- `tools/spec_runner/host_executor.py::execute_spec_via_host` maps each
  `LoadedSpec` onto an E16-1 request (`ir` category -> `lower` operation;
  `flow`/`error` categories -> `eval` operation, matching the existing
  in-process routing) and classifies the result into `pass`, `fail`,
  `unsupported`, `protocol_error`, `crash`, or `timeout`.
- A case that requires an injected Python-host-only test fixture or the
  `--debug-stdio` CLI mode is reported `unsupported` locally, without
  invoking the adapter: neither is expressible over the generic protocol
  yet. This is a minimal, explicitly labeled interim rule; explicit
  capability-aware selection is E16-3 (issue #760).
- The host-mode summary line names every outcome explicitly (`Summary:
  total=... passed=... failed=... unsupported=... protocol_error=...
  crash=... timeout=... invalid=...`) so none of them can be silently
  folded into `passed` or omitted. The run exits nonzero if `failed`,
  `protocol_error`, `crash`, `timeout`, or `invalid` is nonzero;
  `unsupported` alone does not fail the run.
- Running the full real `spec/` suite through the deterministic fixture
  adapter (not a Genia host) is a proof of the runner path only: it
  produces `passed=0` (the fixture never reproduces real Genia semantics)
  with zero `protocol_error`/`crash`/`timeout` and `unsupported` limited to
  exactly the fixture/debug-stdio-bearing cases, proving the generic
  transport, taxonomy, and CLI plumbing work across every category without
  any host-specific knowledge in the runner.
- **Without `--host`, behavior is unchanged**: `tools.spec_runner.runner.main`
  still calls the Python adapter in-process by default, exactly as before
  E16-2. Replacing that default path is E16-5 (issue #762).

## E16-7 conformance evidence reporting (issue #764)

`python -m tools.spec_runner --host '<command>' --evidence <path>` writes
one deterministic JSON evidence document to `<path>` after the run
completes:

```json
{
  "protocol_version": "1",
  "contract_revision": {"declared": "<sha>", "checkout": "<sha>", "classification": "current"},
  "capabilities": {"parser": "supported", "...": "..."},
  "capability_operations": ["parse", "lower", "eval", "cli"],
  "total_cases": 641,
  "applicable_cases": 641,
  "counts": {"pass": 623, "fail": 0, "unsupported": 18, "protocol_error": 0, "crash": 0, "timeout": 0, "invalid": 0}
}
```

- `tools/spec_runner/evidence.py::build_evidence` is a pure function of
  the capabilities response, the E16-4 revision classification, and the
  final counts; `encode_evidence` serializes with `sort_keys=True`, so
  identical inputs produce byte-identical evidence across repeated runs.
- Every discovered case resolves to exactly one of `pass`/`fail`/
  `unsupported`/`protocol_error`/`crash`/`timeout`/`invalid`; `build_evidence`
  raises rather than publish a document whose counts do not sum to
  `total_cases`. No capability or category can be summarized as passing
  merely because it was unsupported or unexecuted.
- No evidence is written when the run stops before any case executes
  (capabilities fetch failure, malformed capability declaration, or an
  unresolvable declared revision) — there is nothing honest to publish yet.
- See `docs/strategy/roadmap/multi-host-conformance-policy.md`'s "Evidence
  model and CI expectations" section for what external-host CI is expected
  to do with this: pin a revision, run the generic protocol, publish the
  artifact, fail the job on the runner's exit code (never on `unsupported`
  alone), and separately run a non-blocking current-`main` drift check.

## E16-3 host capability advertisement and per-case requirements (issue #760)

`--host` mode now begins every run with exactly one `capabilities` request
to the adapter (`tools/spec_runner/protocol.py::fetch_capabilities`,
sentinel `case_id` `__capabilities__`). The response must declare, per
capability name, whether it is `supported`, `partial`, or `unsupported`;
every claimed name must come from the vocabulary `genia-2026` already owns
(`spec/manifest.json`'s `required_capabilities`/`optional_capabilities`,
formalized in `docs/host-interop/capabilities.md`) — an unknown name is
rejected as a malformed declaration (`tools/spec_runner/capabilities.py::
validate_capability_claims`) and the whole run stops with one deterministic
error before any case is executed, since case selection cannot be trusted
without it.

- A spec case may declare an optional top-level `requires:` list of
  capability names in its YAML file. A case with no `requires` belongs to
  the base required-capability set every conforming host implements by
  definition and is always applicable. A case with `requires` is applicable
  only when the host declares every listed capability exactly `supported`
  (`partial` and undeclared capabilities do not satisfy `requires` in this
  phase). An unmet requirement is reported `unsupported` — the adapter is
  never even invoked for that case's own operation.
- `requires` naming an unknown capability is a spec-loading error (the case
  becomes `INVALID`, matching every other malformed-spec path already in
  `tools/spec_runner/loader.py`).
- Hosts are never required to declare identical capability sets; a host's
  `unsupported` count for capabilities it never claims is expected, not a
  regression.
- Shape correctness of `contract_revision`/`protocol_version` (non-empty
  string, supported version) is validated at the wire level by
  `tools/spec_runner/protocol.py`.

## E16-4 contract revision pinning and current-main compatibility (issue #761)

`--host` mode classifies the host's declared `contract_revision` against
the revision this checkout is actually at right now
(`tools/spec_runner/revision.py::check_revision`), using local git history
only -- it never fetches from a remote and never rewrites the host's
declared claim.

- If the declared revision **is** the revision currently checked out, the
  run prints `Revision: pinned conformance for <sha>` and this run's
  pass/fail evidence is honest pinned-conformance evidence for that exact
  revision.
- If the declared revision resolves locally but differs from the one
  checked out (a real, known, older commit), the run prints `Revision:
  current-main compatibility only -- host declared <sha>, this checkout is
  at <sha>` and proceeds; the same pass/fail evidence is now honestly
  labeled a current-main-compatibility check, not pinned conformance for
  the declared revision. This is expected, not an error: a host can be
  correctly conforming to its declared revision while visibly behind
  current `main`.
- If the declared revision resolves to no commit this local history has,
  the run prints `UNRESOLVABLE host-declared contract_revision` and stops
  with exit code 1 **before any case is executed** -- neither pinned nor
  current-main evidence can be honestly attributed to an unresolvable
  claim.
- Genuinely re-running the suite pinned at an *older* revision's own
  `spec/` snapshot (rather than just labeling a live run against the
  current tree) is an external-host-CI concern: that CI pins its own
  `genia-2026` checkout at the declared revision. This runner only
  classifies what one local run against the currently checked-out tree can
  honestly claim; see E16-7 (issue #764) for the evidence/CI contract.

## E16-5 Python reference host through the subprocess protocol (issue #762)

`hosts/python/protocol_adapter.py` exposes the Python reference host as an
E16-1 protocol-speaking subprocess command, wrapping the existing
in-process adapter (`hosts/python/adapter.py::run_case`) with no change to
Python evaluation semantics -- only transport translation, exactly like
`hosts/python/adapter.py` already does for the in-process path:

```bash
python -m tools.spec_runner --host 'python -m hosts.python.protocol_adapter'
```

- Declares every capability in `spec/manifest.json`'s vocabulary as
  `supported`, except `shared_spec_runner` which it declares `partial`
  (matching its documented status in
  `docs/host-interop/HOST_CAPABILITY_MATRIX.md`).
- Proven at full scale in `tests/spec/
  test_python_protocol_adapter_parity_762.py` (marked `slow`): running the
  entire real `spec/` suite through this subprocess path produces the
  identical outcome as the in-process default path for every currently
  applicable case (`641 total, 623 passed, 0 failed, 18 unsupported
  (fixture/debug-stdio cases not yet expressible over the protocol, same
  as E16-2), 0 protocol_error/crash/timeout`) -- real Genia evaluation
  through two full subprocess hops per `eval`/`cli` case, not the
  deterministic fixture.
- `tests/unit/test_python_protocol_adapter_762.py` proves transport
  isolation directly: a program that prints non-JSON text to its own
  stdout during evaluation never corrupts the adapter's envelope; that
  output arrives only inside `result.stdout`.
- **The in-process default path (`tools.spec_runner.executor.execute_spec`
  importing `hosts/python/adapter.py` directly, used when `--host` is
  omitted) is retained unchanged** as the existing developer-optimization
  path -- it is not deleted, and it is not the conformance definition. The
  subprocess protocol path above is what any host, Python included, is
  actually held to.
- No Python-private semantic shortcut exists in the generic runner: this
  adapter uses only the same public `run_case` entrypoint, `LoadedSpec`-
  shaped translation, and E16-1 envelope every other host must speak.
