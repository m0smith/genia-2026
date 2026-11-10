# MCP stdio client acceptance (R28 E28-4)

Runs the official MCP TypeScript client SDK (`@modelcontextprotocol/client` 2.2.0, locked) against
the server configured in the repository-root `.mcp.json`, and prints one JSON report line.

    cd tools/mcp_acceptance && npm ci && GENIA_MCP_TEST_PYTHON="$(command -v python)" node acceptance.mjs

Requires Node 20+, `uv`, `git`, and POSIX. See `docs/mcp/stdio-development.md`.

Pytest supplies its active interpreter through `GENIA_MCP_TEST_PYTHON`. Both SDK
harnesses pass only `UV_PYTHON` and `UV_PYTHON_DOWNLOADS=never` beyond the SDK
client environment defaults, overriding a different repository-local version pin.
This is test-harness selection; the public `.mcp.json` command stays unchanged.
