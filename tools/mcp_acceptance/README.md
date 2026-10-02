# MCP stdio client acceptance (R28 E28-4)

Runs the official MCP TypeScript client SDK (`@modelcontextprotocol/client` 2.2.0, locked) against
the server configured in the repository-root `.mcp.json`, and prints one JSON report line.

    cd tools/mcp_acceptance && npm ci && node acceptance.mjs

Requires Node 20+, `uv`, `git`, and POSIX. See `docs/mcp/stdio-development.md`.
