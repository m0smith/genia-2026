# Agent test-environment preflight (Claude Code #1250 findings)

This is **tooling/environment guidance**, not a Genia semantic contract or permission to relax required tests. Source: [Claude's reproduced diagnosis and accepted local verification](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6559570664), after [D1 PR #1307](https://github.com/m0smith/genia-2026/pull/1307). Preserve all prior failed outcomes; a corrected environment produces a **new** run, not a reclassification of the old one.

## Before running tests in a fresh checkout/worktree

1. Read current `AGENTS.md` and the four authority documents, plus applicable process gates.
2. Check that the checkout has the right Python/uv environment, writable cache and permitted sockets. In this repository `uv.lock` is gitignored, and `uv run --no-sync` does **not** generate it. Where required, run `uv sync` **first** in the correct checkout. Record the resolved environment; do not silently update dependency specifications or treat a generated local lockfile as tracked source.
3. Confirm that `$HOME` and **`$HOME/.cache/uv` are writable to the test subprocess**, not merely to the coordinator process. Some R28 MCP tests launch with a deliberately minimal sanitized environment that preserves HOME/PATH but strips `UV_CACHE_DIR`; setting `UV_CACHE_DIR` in the parent does **not** fix those child launches. Provision a writable HOME/cache in the actual worker environment.
4. Confirm the needed loopback/socket permissions. A sandbox that denies `socket()` with EPERM cannot be used as proof of a runtime regression. Do not silently skip loopback tests; use the required separate loopback partition in a capable environment.
5. Bound simultaneous workers/builds to the real machine quota. Record test SHA, host pin, worker count, deadlines and environment. Preserve any STOP rule and evidence. Never bypass a stopped run by hiding failures.

## Failure triage before modifying Genia code

- **MCP subprocess closes stdout early:** inspect subprocess stderr and `uv` exit status; distinguish failed server startup from protocol/runtime behavior. Check writable `$HOME/.cache/uv` first.
- **Missing `uv.lock`:** determine whether the fresh worktree was initialized with `uv sync` before `--no-sync`; inspect the actual child environment.
- **`socket(): Operation not permitted`:** identify sandbox/network permissions before attributing to Genia. Do not weaken security restrictions globally; use a properly permissioned, isolated test worker.
- Reproduce each cause in a focused bounded diagnostic and record the original as FAIL, not PASS. Diagnose unclassified failures independently. Resume full gates only as the established process allows.

## OpenClaw and multi-agent integration

OpenClaw, when configured, should run this **read-only environment preflight** for each spawned Claude Code/Codex worker/worktree before dispatching expensive tests. A coordinator's own cache/permissions are not evidence that child processes inherit them.

A useful handoff record contains: task/issue, repository and exact commit/tree, worktree, HOME/cache writability, lockfile/uv sync status, Python/uv versions, socket/loopback availability, worker quota, tool permission boundary, and evidence/decision links. It must not copy credentials, protected values or unnecessary logs into prompts.

On a failed environment preflight, route to a **bounded setup repair** instead of starting the full test matrix. Do not make OpenClaw mandatory or grant it authority to change source, merge, close issues or override acceptance gates. For security, provision an isolated writable HOME for the worker, not a privileged host-wide workaround.

## Provenance and scope

Claude's #1250 investigation classified **22 earlier R28 MCP failures**: 20 read-only uv cache errors, one missing `uv.lock`, one socket EPERM. In a corrected environment, focused tests **116 PASS**, D1 tests **82 PASS**, full non-loopback **7,826 PASS / 60 SKIP**, loopback **31 PASS**, Ruff PASS. The original blocked run remains retained. This does **not** explain the separate seven historical Python timeouts under #1251.

This guidance does not claim that current OpenClaw installations automatically perform preflight, or that D1/D2/E or C++ functionality has expanded.
