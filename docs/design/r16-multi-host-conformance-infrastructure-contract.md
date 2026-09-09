# R16 Multi-Host Conformance Infrastructure Contract

Status: **Approved contract. E16-0 (issue #757) complete. E16-1 (issue #758)
complete** — the versioned host-adapter protocol and outcome taxonomy are
implemented as a standalone module (`tools/spec_runner/protocol.py`),
proven only against a deterministic fixture adapter; not yet wired into
`tools/spec_runner`. E16-2 (issue #759) through E16-8 (issue #765) are not
started. This document locks wire-level
protocol and ownership decisions only; it adds no runtime behavior, no
subprocess protocol implementation, no Core IR change, and no second host.
`GENIA_STATE.md` remains final authority for implemented behavior.

Issue: #757
Parent epic: #756

`GENIA_STATE.md` remains final authority. This contract constrains later R16
slices only. It does not make any R16 behavior current merely because the
roadmap, issues, or this file exist. As of this contract, **no generic
multi-host runner exists; all conformance is validated against the Python
reference host**, exactly as `GENIA_STATE.md` §0 already states.

## Purpose

The shared conformance runner (`tools/spec_runner`) currently drives the
Python reference host in-process only. A second, independently versioned
host repository has no generic way to prove conformance against the
authoritative `genia-2026` contract without a one-off shim. R16 replaces
that single-host assumption with one versioned, capability-aware subprocess
adapter protocol and one evidence model, while Python remains the semantic
reference host and `genia-2026` remains the sole authority for language and
Core IR semantics.

E16-0 exists because several wire-level and ownership decisions were left
intentionally unspecified in `docs/strategy/roadmap/r16-r20.md` and
`docs/strategy/roadmap/multi-host-conformance-policy.md`. This document
settles them so the protocol cannot accidentally encode Python
implementation details or blur semantic authority between repositories.

## Existing capability inventory (current truth, before R16)

This section is the exact-state inventory required by issue #757. It
restates, without changing, what `GENIA_STATE.md` §0, `docs/host-interop/*`,
`spec/manifest.json`, and `tools/spec_runner` already document as
implemented today.

- **Python is the only implemented host and the reference host.** No other
  host (Node.js, Java, Rust, Go, C++) is implemented; all are planned or
  scaffolded only (`hosts/node`, `hosts/java`, `hosts/rust`, `hosts/go`,
  `hosts/cpp` contain only placeholder `README.md`/`AGENTS.md` files copied
  from `hosts/template/`).
- **No generic multi-host runner exists.** `tools/spec_runner/executor.py::
  execute_spec` calls `hosts/python/adapter.py::run_case(spec) ->
  ActualResult` in-process. There is no subprocess boundary, no `--host`
  selection flag, and no host-agnostic invocation path.
- **Shared spec categories:** `parse`, `ir`, `eval`, `cli`, `flow`, `error`.
  All six are active with executable YAML case files under `spec/eval/`,
  `spec/ir/`, `spec/cli/`, `spec/flow/`, `spec/error/`, `spec/parse/`. `flow`
  and `error` cases execute through the same code path as `eval`
  (`hosts/python/exec_flow.py` and the `category in ("eval", "error")`
  branch of `run_case` both call `hosts/python/exec_eval.py::
  run_eval_subprocess`); `parse` calls the parse adapter directly with no
  subprocess; `ir` calls the parser/lowering pipeline directly with no
  subprocess; `cli` and `eval` each spawn one Python interpreter subprocess
  per case today, already isolating the evaluated program's stdout/stderr
  from the calling process via `subprocess.run(capture_output=True)`.
- **`spec/manifest.json`'s `host_test_contract`** already documents the
  logical shape R16 must generalize into a wire protocol:
  - `parse`: input `source string` -> output `AST JSON`
  - `lower`: input `source string` -> output `normalized minimal portable
    Core IR JSON` (plus an optional host-local optimized IR payload)
  - `eval`: input `source string`, optional `stdin`, optional `argv` ->
    output JSON with `result`, `stdout`, `stderr`, normalized error data
  - `cli`: input `argv` list plus optional `stdin` -> output JSON with
    `stdout`, `stderr`, `exit_code`, normalized error data
  - `spec/manifest.json`'s own `host_status.generic_spec_runner` field is
    already recorded as `"scaffolded"` — contract-level intent only, no
    implementation.
- **Capability vocabulary already exists but is not wired to the runner.**
  `spec/manifest.json` lists `required_capabilities` and
  `optional_capabilities`; `docs/host-interop/capabilities.md` gives each a
  formal per-capability contract (name, Genia surface, input/output,
  errors, portability status). Nothing today advertises these from a host
  process or filters spec cases by them.
- **`docs/host-interop/HOST_INTEROP.md`** already defines the authority
  order, the normalized error model, the Flow/CLI/capability-registry
  contracts, and the Phase 2 strictness/normalization rules that any new
  protocol must preserve unchanged; R16 does not revise any of that.
- **`hosts/cpp/`** is scaffold-only: `README.md`/`AGENTS.md` state "planned,
  no host implementation exists yet" and defer to `hosts/template/`. No
  `m0smith/genia-cpp` repository exists yet.
- **Two earlier, non-adopted proposal drafts** —
  `docs/strategy/cpp-host-tickets-r16-r22.md` and
  `docs/strategy/cpp-host-release-plan-r16-r22.md` — sketched a different
  R16–R22 numbering (old R16 = spec-runner protocol only; old R19 = C++
  minimal host; etc.) before the current `docs/strategy/roadmap/r16-r20.md`
  and epic #756 existed. They already carried a
  "Proposal — non-authoritative, not adopted" status line. See "Stale
  planning docs" below; their technical reasoning is folded into this
  contract and the current roadmap, not deleted.

## Global invariants

Every later R16 slice (E16-1 through E16-8) must preserve all of the
following, drawn directly from `docs/strategy/roadmap/r16-r20.md` and
`docs/strategy/roadmap/multi-host-conformance-policy.md`:

1. **No second semantic authority.** `genia-2026` alone owns the language
   contract, Core IR portability boundary, shared specs, the generic
   runner, and the wire protocol definition. An external host repository
   implements Genia; it never defines Genia.
2. **No Python-shaped protocol.** The wire protocol must be expressible by
   a host that has never read Python source; it may not encode Python
   process/module/exception conventions as if they were part of the
   contract.
3. **`unsupported` is never `pass`.** Unexecuted, silently skipped,
   malformed, crashed, or protocol-invalid cases are never reported as
   conformance passes.
4. **Deterministic six-state reporting.** Every executed case resolves to
   exactly one of `PASS`, `FAIL`, `UNSUPPORTED`, `PROTOCOL ERROR`,
   `CRASH`, `TIMEOUT`.
5. **Pinned conformance ≠ current-main compatibility.** These are two
   distinct, separately reported questions; a host may be correctly
   pinned-conforming while visibly behind current `main`.
6. **Capability sets need not match across hosts.** Synchronization means
   identical observable behavior for every capability a host claims, not
   forced support for every Python-host-only surface.
7. **No Core IR or language-semantics change.** R16 is infrastructure only.
8. **No distributed-execution semantics.** Multi-host conformance (do
   different hosts preserve the same observable semantics?) stays
   independent of distributed execution (can one computation span
   processes/machines?); R16 must not smuggle in the latter.
9. **Drift handling stays contract-first.** A host disagreeing with shared
   evidence fixes itself against the authoritative contract/spec, or the
   ambiguity is clarified in `genia-2026` first; a host must never resolve
   an ambiguity by reading another host's implementation.

## Protocol contract

This section is organized by the E16-1 through E16-8 slices it authorizes,
matching the epic's approved issue order.

### E16-1 — Versioned adapter protocol + failure taxonomy (issue #758)

**Transport.** One host-adapter process invocation per spec case. The
runner spawns a configured adapter command, writes exactly one JSON request
object to its stdin, and reads exactly one JSON response object from its
stdout, subject to a runner-configured timeout. The protocol is
stateless and per-invocation; it does not require a long-lived daemon
process. This generalizes, rather than replaces, the isolation the Python
adapter already performs today (`subprocess.run(capture_output=True)` in
`hosts/python/exec_eval.py`/`exec_cli.py`).

**Adapter operations.** Exactly the four operations already implied by
`spec/manifest.json`'s `host_test_contract`, plus one capability-discovery
operation added by E16-3:

- `parse`
- `lower` (the `ir` spec category)
- `eval` (also used for the `flow` and `error` spec categories, matching
  today's in-process routing)
- `cli`
- `capabilities` (E16-3; request `input: {}`)

No operation beyond this set exists in R16. `tools/spec_runner` never
assumes host-specific operations.

**Request envelope** (UTF-8 JSON, one object, written to the adapter
process's stdin):

```json
{
  "protocol_version": "1",
  "case_id": "<opaque string, echoed back unchanged>",
  "operation": "parse | lower | eval | cli | capabilities",
  "input": { "...": "operation-specific, see below" }
}
```

Operation-specific `input`, matching `host_test_contract` exactly:

| Operation | `input` shape |
|---|---|
| `parse` | `{"source": "<string>"}` |
| `lower` | `{"source": "<string>"}` |
| `eval` | `{"source": "<string>", "stdin": "<string> or null", "argv": ["<string>", ...] or null}` |
| `cli` | `{"argv": ["<string>", ...], "stdin": "<string> or null"}` |
| `capabilities` | `{}` |

CLI mode selection (file/command/pipe/test) is expressed purely through
`argv` content, exactly as the real CLI already accepts it (e.g. a bare
path for file mode, `["-c", "<command>"]` for command mode, `["-p",
"<command>"]` with a non-null `stdin` for pipe mode, `["--test",
"<name>"]` for test mode). The protocol adds no genia-2026-specific
dispatch vocabulary beyond real CLI argv.

**Response envelope** (UTF-8 JSON, one object and nothing else, written to
the adapter process's stdout):

```json
{
  "protocol_version": "1",
  "case_id": "<same string echoed back>",
  "operation": "<same operation echoed back>",
  "status": "ok | unsupported",
  "result": { "...": "present and non-null only when status == ok" },
  "unsupported_reason": "<string, present and non-null only when status == unsupported>"
}
```

`status` has exactly two adapter-reportable values: `ok` and `unsupported`.
An adapter can never claim `protocol_error`, `crash`, or `timeout` about
itself — those three states are always inferred by the runner from
process-level and JSON-validity facts, never self-reported, so a
misbehaving or dishonest adapter cannot manufacture a more favorable
outcome than the runner independently observes.

Operation-specific `result` (only when `status == "ok"`), matching
`host_test_contract` and the current Python adapter's `ActualResult`
fields exactly:

| Operation | `result` shape |
|---|---|
| `parse` | `{"kind": "ok", "ast": {...}}` or `{"kind": "error", "type": "<string>", "message": "<string>"}` |
| `lower` | `{"ir": {...normalized portable Core IR...}}` |
| `eval` | `{"stdout": "<string>", "stderr": "<string>", "exit_code": <integer>}` |
| `cli` | `{"stdout": "<string>", "stderr": "<string>", "exit_code": <integer>}` |
| `capabilities` | see E16-3 |

**stdout/stderr channel ownership (the roadmap's explicitly named risk).**

- The adapter process's own stdout is reserved exclusively for the single
  JSON response object. It must print nothing else there — no logging, no
  banners, no partial writes.
- The adapter process's own stderr is reserved for adapter-internal
  diagnostics only. The runner never reads it for conformance comparison,
  and it never contributes to `result.stderr`.
- For `eval` and `cli`, the evaluated Genia program's own stdout/stderr
  must never reach the adapter's inherited stdout/stderr directly. The
  adapter is responsible for capturing that output itself (e.g. by running
  the program as its own internally piped child process, exactly as
  `hosts/python/exec_eval.py`/`exec_cli.py` already do) and returning it as
  the `result.stdout`/`result.stderr` string fields inside its JSON
  response. This is an explicit requirement, not an implementation detail
  left to each host: a host that lets the evaluated program's output leak
  onto the adapter's own stdout produces a `PROTOCOL ERROR` (invalid
  envelope), never a false pass or fail.

**Protocol versioning.** `protocol_version` is a small string (`"1"` for
this contract). The runner declares the exact set of versions it accepts
for a given invocation (initially exactly `{"1"}`). A response whose
`protocol_version` is outside that set is a `PROTOCOL ERROR`, never
silently coerced or treated as compatible. A future `"2"` is additive-only
unless a later contract explicitly approves a breaking change; no version
negotiation handshake is designed in R16 beyond exact-match acceptance.

**Echo requirement.** The adapter must echo back the exact `case_id` and
`operation` it received. A mismatch is a `PROTOCOL ERROR`. This exists so
a future concurrent/batched runner (not designed in R16, but not
precluded) can detect a host answering the wrong request.

**Runner-derived outcome taxonomy.** The six states from
`multi-host-conformance-policy.md`, computed entirely by the runner:

| State | Condition |
|---|---|
| `TIMEOUT` | Adapter process exceeds the runner's configured timeout; the runner kills it. |
| `CRASH` | Adapter process exits nonzero, or is terminated by a signal, within the timeout. |
| `PROTOCOL ERROR` | Process exits 0 within the timeout, but stdout is not exactly one well-formed JSON value, or that value fails envelope validation (missing/extra top-level keys, unsupported `protocol_version`, mismatched `case_id`/`operation`, `status` outside `{ok, unsupported}`, or a `result`/`unsupported_reason` shape that does not match the operation's contract). |
| `UNSUPPORTED` | Envelope is valid and `status == "unsupported"`. Never scored as pass or fail. |
| `PASS` | Envelope is valid, `status == "ok"`, and `result` matches the spec case's `expected` value under that category's existing normalized comparison rules (unchanged from today's `tools/spec_runner/comparator.py`/`parse_comparator.py` behavior). |
| `FAIL` | Envelope is valid, `status == "ok"`, and `result` does not match `expected`. |

The exact timeout duration/default and the exact JSON-schema validation
mechanics are E16-1/E16-2 implementation-design decisions; this contract
fixes only the six-state derivation rule above, not a number.

### E16-2 — Generic external-host `spec_runner` path (issue #759)

- `tools/spec_runner` gains a host-selection mechanism (a `--host <command>`
  flag or equivalent) that, when given, executes every applicable case by
  spawning `<command>` per case per the E16-1 protocol, instead of
  importing `hosts/python/adapter.py`. Omitting it preserves today's
  in-process default with no behavior change.
- `tools/spec_runner` must contain no host-specific implementation
  knowledge (no C++, Node, Java, Rust, or Go awareness); it only knows the
  generic protocol from E16-1 and the capability/requirement rules from
  E16-3.
- Case selection against a given host is capability-filtered per E16-3
  before the `eval`/`cli`/`parse`/`lower` operation is ever invoked for
  that case; a case a host cannot claim is `UNSUPPORTED`, not silently
  dropped from the run's totals.

### E16-3 — Capability advertisement + per-case requirements (issue #760)

- The `capabilities` operation's `result` (only when `status == "ok"`,
  which is required — `capabilities` itself is not an operation a
  conforming adapter may mark `unsupported`):

  ```json
  {
    "capabilities": {"<capability_name>": "supported | partial | unsupported", "...": "..."},
    "operations": ["parse", "lower", "eval", "cli"],
    "contract_revision": "<string, see E16-4>",
    "protocol_version": "1"
  }
  ```

  `<capability_name>` values must come from the single shared vocabulary
  `genia-2026` already owns (`spec/manifest.json`'s `required_capabilities`/
  `optional_capabilities`, formalized per-capability in
  `docs/host-interop/capabilities.md`). A host never invents a capability
  name; an unrecognized name in a `capabilities` response is a
  `PROTOCOL ERROR`. `operations` lists the subset of `{parse, lower, eval,
  cli}` the adapter implements at all (independent of which specific
  capabilities it claims within eval/cli behavior).
- Each shared spec case may declare an optional `requires: [capability_name,
  ...]` field (absent or empty means "base required-capability set only,"
  matching today's implicit behavior). A case whose `requires` includes a
  name the host's `capabilities` response does not mark `supported` is
  `UNSUPPORTED` for that host and is never sent through its normal
  operation. Whether a `partial` claim can ever satisfy `requires` is an
  E16-3 implementation-design decision left open here; until E16-3 decides
  otherwise, only `supported` satisfies `requires`.
- Hosts are never required to claim identical capability sets. A host's
  `UNSUPPORTED` count for capabilities it never claims is expected and is
  not treated as a regression, per the policy doc's capability-aware
  synchronization rule.

### E16-4 — Contract revision pinning + current-main drift (issue #761)

- `contract_revision` (in the `capabilities` response) is the exact
  `genia-2026` identifier — a git commit SHA in the default design; an
  exact released tag is an E16-4 implementation option, not excluded here —
  that the host's adapter build declares itself validated against.
- Two distinct evidence runs are always kept separate, never merged into
  one number:
  - **Pinned conformance**: the host is run against `spec/` and
    `tools/spec_runner` exactly as they existed at its declared
    `contract_revision`. This is the certification claim.
  - **Current-main compatibility**: the same host binary is run against
    `spec/`/`tools/spec_runner` at current `main` HEAD and reported
    separately, explicitly labeled as a forward-drift signal, never as
    conformance.
- A host may be correctly pinned-conforming while failing current-main
  compatibility; that is an expected, honestly reported state, not an
  error condition to suppress or reconcile.
- The exact checkout/CI mechanics for running a pinned revision are an
  E16-4/E16-7 implementation-design decision; this contract fixes only that
  the two questions remain distinguishable end to end, from declared
  revision through to the evidence report.

### E16-5 — Python reference host through the subprocess protocol (issue #762)

- `hosts/python/` gains a small adapter-process entrypoint implementing
  exactly the E16-1 protocol by wrapping the existing
  `hosts/python/adapter.py::run_case` and `hosts/python/exec_*.py` category
  executors. It translates the existing in-process contract to the wire
  protocol; it must not reimplement or alter Python-side semantics.
- Acceptance bar: parity. Every case that currently passes via the
  in-process path must produce an identical `PASS`/`FAIL`/`UNSUPPORTED`
  result via the new subprocess path, with an identical `result` payload
  (modulo the new envelope wrapper). Any observed difference is a
  protocol or adapter bug to fix; it is never a reason to relax either
  path's behavior.
- The existing in-process call path
  (`tools/spec_runner/executor.py::execute_spec` importing
  `hosts/python/adapter.py` directly) may be retained after E16-5 only as
  an explicitly labeled transition/developer-optimization path, per
  `roadmap/r16-r20.md`. It must never become a second, silently diverging
  semantic authority once the subprocess path is proven.

### E16-6 — External-host boundary + `genia-cpp` bootstrap (issue #763)

- `genia-2026` remains sole authority for: the Genia language contract,
  the Core IR portability boundary, shared specs (`spec/`), the generic
  runner (`tools/spec_runner`), the E16-1 wire protocol and capability
  vocabulary, and the Python reference host.
- External host repositories (starting with `m0smith/genia-cpp`) own their
  own build/dependency/test/lint toolchain, their adapter-process
  implementation (any internal representation/language choice), their own
  CI orchestration, and their own declared `contract_revision`/capability
  claims. They consume but never fork or redefine `GENIA_STATE.md`,
  `GENIA_RULES.md`, `GENIA_REPL_README.md`, Core IR, shared specs, or the
  E16-1 protocol.
- R16's `genia-cpp` bootstrap creates only the repository shell (its own
  `AGENTS.md`/`README.md` naming `genia-2026` as authoritative, a minimal
  adapter-process scaffold) with **no real C++ interpreter**. "Bootstrap"
  is explicitly not "implementation," matching epic #756's non-goals.
- Existing `hosts/cpp/` in `genia-2026` transitions, no earlier than
  E16-6, to a pointer/scaffold location (its `README.md`/`AGENTS.md`
  updated to name `m0smith/genia-cpp` as the canonical implementation
  location), so no duplicate authoritative-looking C++ implementation ever
  exists in two repositories at once. This contract fixes the rule; E16-6
  executes the transition. E16-0 makes no change to `hosts/cpp/` itself.

### E16-7 — Evidence reporting + external-host CI (issue #764)

- Per host, per run, the host-mode `tools/spec_runner` path publishes one
  evidence report (exact serialization format — JSON matching the
  response-envelope style is the natural default — is an E16-7
  implementation-design decision) recording at minimum, per
  `multi-host-conformance-policy.md`: `contract_revision`,
  `protocol_version`, claimed `capabilities`, applicable case count, and
  `PASS`/`FAIL`/`UNSUPPORTED`/`PROTOCOL ERROR`/`CRASH`/`TIMEOUT` counts,
  reported separately for the pinned-conformance and current-main-
  compatibility runs defined in E16-4.
- External-host CI (in `genia-cpp` or any later host repository) is
  expected to pin and test its declared `genia-2026` revision through this
  same generic runner path. The exact cross-repository CI vendor/checkout
  mechanics remain an E16-7 implementation-design decision, not fixed here.

### E16-8 — Docs, release evidence, skeptical audit, distillation (issue #765)

Standard closing-slice shape, matching the pattern already used to close
R14 (E14-15) and R15 (E15-9): documentation sync across `GENIA_STATE.md`,
`docs/host-interop/*`, `docs/host-interop/HOST_CAPABILITY_MATRIX.md`, and
`spec/manifest.json`; a runnable release example/page under
`docs/releases/`; full regression plus `tools/spec_runner` plus
`mkdocs build --strict` evidence; and a skeptical release-truth audit
recording a PASS verdict before R16 closes. This contract records no
additional decision for E16-8 beyond that shape.

## What remains host-local vs. authoritative in `genia-2026`

**Authoritative in `genia-2026` (this repository):**

- the Genia language contract and Core IR portability boundary
- shared spec cases (`spec/*`) and the capability name vocabulary
  (`spec/manifest.json`, `docs/host-interop/capabilities.md`)
- the generic runner (`tools/spec_runner`) and its comparison/evidence logic
- the E16-1 wire protocol definition itself (envelope shape, operation
  set, taxonomy, versioning rule)
- the Python reference host, as the current semantic baseline

**Host-local (each external host repository's own concern):**

- the adapter-process implementation language and internal representation
- build, dependency, test, and lint toolchain choices
- adapter-level stderr logging/diagnostics (never read by the runner)
- CI orchestration mechanics beyond "pin and test a declared revision
  through the generic protocol"
- any capability it chooses not to claim

## Stale planning docs

`docs/strategy/cpp-host-tickets-r16-r22.md` and
`docs/strategy/cpp-host-release-plan-r16-r22.md` proposed an earlier,
non-adopted R16–R22 sequence (old R16 = spec-runner protocol only; R17 =
numeric contract; R18 = Unicode/float contract; R19 = C++ minimal host; R20
= memory/concurrency; R21 = pipe/REPL/bridge; R22 = Flow/HTTP parity) before
the current `docs/strategy/roadmap/r16-r20.md` (R16 = this broader
Multi-Host Conformance Infrastructure release; R17 = numeric/map contract;
R18 = Unicode/float/diagnostic contract; R19 = Open Functions — a language
feature, not C++ bring-up; R20 = C++ Minimal Conforming Host) and epic #756
existed. The two numbering schemes no longer align one-to-one (R19 changed
meaning entirely; the old plan's R19–R22 C++-bring-up phases collapse
toward the new R20).

Both files already carried a "Proposal — non-authoritative, not adopted"
status line, so no reader could have mistaken them for current truth even
before this contract. As part of this change they are marked **Superseded**
with a pointer to this contract and to `roadmap/r16-r20.md`, and are
otherwise left intact as historical drafting evidence — their technical
substance (subprocess protocol need, numeric/Unicode/error-text contract
gaps, C++ bring-up ordering) is preserved and, where still accurate, is
folded into this contract and the current roadmap rather than deleted.

## Portability posture

R16 semantics are intended to be host-independent from the moment E16-1
lands. The following are portable observations once implemented:

- the request/response envelope shape and field names
- the operation set (`parse`, `lower`, `eval`, `cli`, `capabilities`)
- stdout/stderr channel ownership
- the six-state outcome taxonomy and which party (adapter vs. runner) may
  report which states
- protocol-version exact-match acceptance
- the capability vocabulary and `requires`/`capabilities` matching rule
- the pinned-conformance vs. current-main-compatibility distinction
- the evidence report's required fields

Internal adapter representation, build tooling, and CI vendor choice remain
host-local, per `docs/host-interop/HOST_PORTING_GUIDE.md`'s existing
"different internals are fine, different observable semantics are not"
rule.

## Expected issue sequence

The approved dependency order after E16-0 is:

1. **#757 — E16-0:** contract, current-state inventory, protocol decisions (this document)
2. **#758 — E16-1:** versioned adapter protocol + failure taxonomy
3. **#759 — E16-2:** generic external-host `spec_runner` path
4. **#760 — E16-3:** capability advertisement + per-case requirements
5. **#761 — E16-4:** contract revision pinning + current-main drift
6. **#762 — E16-5:** Python reference host through subprocess protocol
7. **#763 — E16-6:** external-host boundary + `genia-cpp` bootstrap
8. **#764 — E16-7:** evidence reporting + external-host CI
9. **#765 — E16-8:** docs, release evidence, skeptical audit, distillation

```text
#757 -> #758 -> #759 -> #760 -> #761 -> #762 -> #763 -> #764 -> #765
```

Each issue runs its own repository process (preflight/contract/design/
test/implementation/docs/audit as applicable). An earlier issue merging
does not waive a later issue's gates.

## Non-goals

R16 explicitly excludes, per epic #756 and `roadmap/r16-r20.md`:

- a second production interpreter/runtime
- the real C++ host implementation
- any change to Core IR or Genia language semantics
- claiming an unsupported or unexecuted case passed
- expanding the meaning of current spec categories merely to build the
  runner
- requiring every host to support identical capability sets
- distributed-execution semantics (see
  `docs/architecture/execution-realization.md`, parked)
- R17/R18/R19 numeric/Unicode/open-function contract work

## Documentation rule

E16-0 updates strategy/roadmap/design documentation to record R16 as the
active release and to constrain planned protocol behavior. It must **not**
update `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, or
`README.md` to claim any new R16 runtime behavior, because none exists yet.

As each later slice lands, that issue is responsible for updating every
implemented-truth surface legitimately affected by its tested
implementation, including `GENIA_STATE.md` §0, `docs/host-interop/*`, and
`spec/manifest.json`.

## E16-0 authorization boundary

If #757 is reviewed and approved, the next authorized work item is **#758 /
E16-1 preflight only**.

No E16-2+ implementation is authorized merely because those issues exist.

## E16-1 completion note (issue #758)

E16-1 is complete: `tools/spec_runner/protocol.py` implements exactly the
request/response envelope, stdout/stderr channel-ownership rule, protocol
versioning, and outcome taxonomy fixed above for the `parse`, `lower`,
`eval`, and `cli` operations, proven end-to-end by
`tests/unit/test_spec_runner_protocol.py` against the deterministic
`tools/spec_runner/fixtures/protocol_fixture_adapter.py`. No behavior
beyond this contract was added; the module is not yet consulted by
`tools/spec_runner`'s case execution. The next authorized work item is
**#759 / E16-2 preflight only**.
