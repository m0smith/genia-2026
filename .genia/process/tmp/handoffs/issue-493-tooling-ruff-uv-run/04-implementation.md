# === GENIA IMPLEMENTATION ===

CHANGE NAME: issue #493 tooling-ruff-uv-run
CHANGE SLUG: issue-493-tooling-ruff-uv-run
ISSUE: #493
BRANCH: feature/issue-493-tooling-ruff-uv-run

## Branch

Starting branch: feature/issue-493-tooling-ruff-uv-run
Working branch: feature/issue-493-tooling-ruff-uv-run
Branch status: Branch already existed; no branch creation was needed. The pre-existing untracked `ryan-holiday-book-club-list.md` file remained unstaged and untouched.

## Scope

What this phase changed: Added ruff to the existing project dev dependency group and changed CI linting from unmanaged `uvx ruff check .` to project-local `uv run ruff check .` after the existing `uv sync --dev` step.

What this phase did not change: No Genia language syntax, parser behavior, evaluator behavior, Core IR, prelude behavior, Flow behavior, Outcome behavior, Sheets behavior, module/import behavior, native test behavior, shared spec behavior, ruff rules, broad lint cleanup, or broad formatting changed.

## Inputs read

- AGENTS.md
- GENIA_STATE.md
- GENIA_RULES.md
- GENIA_REPL_README.md
- README.md
- 00-preflight.md
- 01-contract.md
- 02-design.md
- 03-test.md
- pyproject.toml
- CI workflow file inspected/changed:
  - .github/workflows/ci.yml

## Failing evidence addressed

Exact failing evidence from `03-test.md`:

```text
error: Failed to spawn: `ruff`
  Caused by: No such file or directory (os error 2)
```

This phase addressed that by making `ruff` a project-managed dev dependency and validating that `uv run ruff check .` now resolves and runs ruff successfully.

## Implementation summary

Dependency changes: Added `"ruff>=0.8.0"` to the existing `[dependency-groups] dev = [...]` list in `pyproject.toml`.

Lockfile changes: Ran `UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv lock`. The repo has a local `uv.lock`, but `.gitignore` intentionally ignores it. The command resolved successfully with network access and reported `Added ruff v0.15.18`; no tracked lockfile diff exists because `uv.lock` is not tracked in `HEAD`.

CI changes: Changed `.github/workflows/ci.yml` lint step from `uvx ruff check .` to `uv run ruff check .`. The workflow already runs `uv sync --dev` immediately before linting, so no additional sync step was needed.

Docs/process changes, if any: None outside this implementation handoff.

## Files changed

Expected production/tooling files:

- pyproject.toml
- .github/workflows/ci.yml

Expected handoff file:

- .genia/process/tmp/handoffs/issue-493-tooling-ruff-uv-run/04-implementation.md

Local ignored file touched by tooling but not committed:

- uv.lock

Unrelated pre-existing untracked file not touched:

- ryan-holiday-book-club-list.md

## Commands run

```bash
git branch --show-current
```

Observed result:

```text
feature/issue-493-tooling-ruff-uv-run
```

```bash
git status --short
```

Observed initial result:

```text
?? ryan-holiday-book-club-list.md
```

```bash
grep -n "ruff" pyproject.toml || true
```

Observed pre-edit result:

```text
47:[tool.ruff]
```

```bash
ls -l uv.lock
```

Observed result:

```text
-rw-r--r--@ 1 m0smith  staff  300895 Apr 28 12:40 uv.lock
```

```bash
sed -n '1,90p' pyproject.toml
```

Observed pre-edit result: dev dependencies contained `mkdocs`, `mkdocs-material`, `pytest`, `pytest-cov`, and `pytest-xdist`; no `ruff` entry was present.

```bash
sed -n '45,65p' .github/workflows/ci.yml
```

Observed pre-edit result:

```text
      - name: Sync dependencies
        run: uv sync --dev

      - name: Lint (ruff)
        run: uvx ruff check .
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv lock
```

Observed sandbox result:

```text
error: Request failed after 3 retries in 3.6s
  Caused by: Failed to fetch: `https://pypi.org/simple/pyyaml/`
  Caused by: error sending request for url (https://pypi.org/simple/pyyaml/)
  Caused by: client error (Connect)
  Caused by: dns error
  Caused by: failed to lookup address information: nodename nor servname provided, or not known
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv lock
```

Observed result with network access:

```text
Resolved 70 packages in 2.66s
Added ruff v0.15.18
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run ruff check .
```

Observed sandbox result:

```text
× Failed to build `genia @ file:///Users/m0smith/projects/genia-2026`
├─▶ Failed to resolve requirements from `build-system.requires`
├─▶ No solution found when resolving: `hatchling`
├─▶ Request failed after 3 retries in 9.0s
├─▶ Failed to fetch: `https://pypi.org/simple/hatchling/`
├─▶ error sending request for url (https://pypi.org/simple/hatchling/)
├─▶ client error (Connect)
├─▶ dns error
╰─▶ failed to lookup address information: nodename nor servname provided, or
    not known
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run ruff check .
```

Observed result with network access:

```text
All checks passed!
```

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q
```

Observed result:

```text
8 failed, 2605 passed in 414.86s (0:06:54)
```

The 8 failures were all local socket-bind failures:

```text
PermissionError: [Errno 1] Operation not permitted
```

Affected tests:

- tests/demo/test_ants_web_demo.py::test_ants_web_http_routes_serve_assets_and_state_updates
- tests/unit/test_http_web.py::test_serve_http_plain_text_response
- tests/unit/test_http_web.py::test_serve_http_json_response_and_request_body_parsing
- tests/unit/test_http_web.py::test_serve_http_request_map_includes_client_and_raw_text_body
- tests/unit/test_http_web.py::test_serve_http_json_body_parse_failure_stays_in_request_body_as_absence
- tests/unit/test_http_web.py::test_serve_http_route_request_returns_not_found_response
- tests/unit/test_http_web.py::test_serve_http_invalid_handler_result_returns_500
- tests/unit/test_http_web.py::test_http_service_example_runs_health_endpoint

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_http_web.py tests/demo/test_ants_web_demo.py::test_ants_web_http_routes_serve_assets_and_state_updates
```

Observed result with local socket binding allowed:

```text
8 passed in 1.46s
```

```bash
git diff --name-only
```

Observed result before handoff:

```text
.github/workflows/ci.yml
pyproject.toml
```

```bash
git status --short
```

Observed result before handoff:

```text
 M .github/workflows/ci.yml
 M pyproject.toml
?? ryan-holiday-book-club-list.md
```

```bash
git check-ignore -v uv.lock .genia/process/tmp/handoffs/issue-493-tooling-ruff-uv-run/04-implementation.md
```

Observed result:

```text
.gitignore:7:uv.lock	uv.lock
.gitignore:83:.genia/process/tmp/	.genia/process/tmp/handoffs/issue-493-tooling-ruff-uv-run/04-implementation.md
```

## Validation

Ruff validation: Passed with `UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run ruff check .` after network access allowed uv to build/sync the local environment and install the project-managed ruff dependency.

Pytest validation: Full `UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q` produced `2605 passed` and 8 socket-bind failures under the sandbox. The exact failing HTTP/socket subset passed with local socket binding allowed: `8 passed in 1.46s`.

Any limitations: Initial `uv lock` and `uv run ruff check .` attempts hit sandbox DNS/network limits. The full pytest run hit sandbox local socket binding limits for HTTP tests; the focused socket subset passed outside that limitation.

## Runtime/language impact

Confirm:

- no parser changes
- no evaluator changes
- no Core IR changes
- no runtime behavior changes
- no Genia semantic docs changed

## Follow-ups

None.

## Final verdict

Ready for Docs Sync?
YES
