# Genia MCP security and deployment limitations (R28)

Status: **Release candidate.** `GENIA_STATE.md` is the final authority. This page says what R28 actually
guarantees and what it does not. The Genia MCP server is a **local development tool for trusted stdio
clients**. Its execution profile is a **defense-in-depth profile**: **not a security sandbox and not
production multi-tenant isolation**. Do not expose it to untrusted callers.

## What R28 guarantees (each backed by a test; see the conformance matrix)

| Guarantee | How |
|---|---|
| Exactly three tools, no resources, no prompts, no HTTP, no listener | closed discovery, architecture and configuration tests (M:D1–D6, Z6) |
| A fresh, disposable worker per `genia_run` call; nothing carries over between calls | one process per call in its own process group, killed and reaped after every call (M:R10, X9, Y7) |
| A fixed minimal worker environment | only loader and encoding variables; no `PATH`, no `HOME`, no user variables (M:A3) |
| A private, empty working directory, removed after the worker is reaped | `genia-worker-*` temporary directory (M:X2, Y6) |
| Operating-system resource limits in the worker | no file writes (`RLIMIT_FSIZE` 0), no core dumps, CPU 10 s, 64 open files, 2 GiB address space (M:A21) |
| Bounded execution | fixed 5,000 ms deadline from worker readiness; kill and reap of the whole process group on timeout, cancellation, overflow, or any failure (M:T1–T8, X1–X10) |
| Bounded input and output in UTF-8 bytes | source 262,144; stdout, stderr and value 1,048,576 each; whole result 3,276,800; enforced incrementally (M:L1–L9) |
| A restricted Genia environment | a default-deny classification: only explicitly allowed bindings survive; a new binding is denied until classified, enforced by a drift test (M:A18) |
| Static policy over the **raw parser AST** | source that names a prohibited capability, an `import`, or a shell stage is `policy_denied` before anything runs (M:A1–A19) |
| Runtime stubs beneath policy | process creation, sockets, and module loading are stubbed inside the worker (M:A9, A10) |
| Protected values do not cross the boundary | a protected value in a result is `policy_denied`; sentinel tests found none in any response, error, or timing path (M:S1–S10) |
| Program output cannot corrupt or steer the protocol | output is data inside one response; a cancellation lookalike does not cancel (M:C-F) |
| One execution model for both protocol eras | the `2025-11-25` and `2026-07-28` paths dispatch into the same tool implementation, policy, worker, limits, and cancellation; the compat suite compares both eras' envelopes and repeats the authority, protected-value, timeout, cancel, and lifecycle rows (M:K10-K14) |
| Client capabilities grant no authority | `initialize` capabilities (roots, sampling, elicitation, tasks, extensions) are validated for shape and discarded; results are identical for empty and maximal capabilities and the server never sends a request or notification (M:K8) |
| Failures are fixed closed envelopes | no source, path, exception text, class name, or trace (M:F1–F9) |

## Operating-system isolation: best effort, never the contract

Where the host verifies it once at start-up, workers also run inside a user + network namespace
(`unshare --user --map-root-user --net`). This is **best effort** and is used only if verified. Hardened
hosts (some CI images, some containers) deny it; then workers run **without** it and **nothing claims
otherwise**: `genia_capabilities` never mentions an operating-system mechanism, and every security test
passes identically with the namespace granted and with it simulated as denied (M:N1–N3). The policy,
pruned environment, runtime stubs, and limits are the contract; the namespace is an extra layer.

## What R28 does not provide

- No filesystem namespace or mount isolation, **no seccomp**, **no cgroup** memory or CPU isolation, **no PID
  namespace**.
- No protection against defects in the Python interpreter, the Genia runtime, or the kernel.
- No isolation from other processes owned by the same user: the server and workers run as the user who
  starts them, and a local process of that user could signal or inspect them.
- No authentication and no network listener: the only client is the process that started the server
  over stdio. Streamable HTTP is deferred and not implemented.
- Not multi-tenant, not for untrusted callers, not a hosted service, no resource accounting across calls.
- The server executes the program a client submits: enabling the `genia` server in a client is a trust
  decision about that client and about this repository's `.mcp.json` (review it like any executable
  configuration; it contains no environment, secret, URL, or absolute path).

## Documented limitations

- **SIGKILL:** a host killed with SIGKILL cannot clean up; its worker ends itself within 8 seconds
  (an orphan backstop, not a second deadline) and an **empty private temporary directory may remain**.
- **Large pending input:** while more than 8 MiB of unread client input is pending, the server stops
  reading and cannot observe a cancellation (best effort).
- **A closed transport** may prevent any response from being delivered.
- **Rendering** of a very large value cannot be bounded incrementally; it is bounded by the deadline and
  the address-space limit and then checked.
- **Debug-rendered values:** `value.rendered` is canonical debug text and may show host text for callable
  values (a Python function representation with an address). It is not a serialization.
- **Strings:** UTF-16 surrogate `\u` escapes in program strings do not cross the JSON boundary unchanged.
- **No failure text:** a failed run returns only a fixed message. Parse failures give a character offset
  only.

- **Protocol revisions:** exactly `2026-07-28` and `2025-11-25` are served; older revisions that also use
  `initialize` are rejected, not negotiated down. VS Code behavior after `initialize` (the `initialized`
  notification, timing of `tools/list`, `ping`) rests on the SDK reference and the first authentic trace
  and is pending the owner's second run (ledger R28-H39).

## Deployment

Supported: run the server from a git clone on Linux as a stdio child of a trusted client on the same machine
(`docs/mcp/demo.md`). Not verified: macOS. Not supported: Windows. Prerequisites: `git`, and `uv` or
Python 3.10+. Nothing is installed or downloaded when the server starts. There is no published package, no
container image, and no registry entry; the supported distribution is the repository checkout.
