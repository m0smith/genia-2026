"""Narrow host parse capability for the native Genia MCP server (R28 E28-2, issue #703).

`parse_source(source)` reaches the existing normalized parse surface
(`hosts/python/parse_adapter.parse_and_normalize`, unchanged) because Genia source
cannot call the parser itself (ledger R28-H17). It returns closed JSON text that
`mcp.genia` decodes and validates natively:

- {"status": "parsed", "ast": <unchanged normalized AST>}
- {"status": "syntax_error", "offset": <int or null>}
- {"status": "internal_error"}

It never evaluates source, reads files, or resolves imports, and no exception text,
class name, or source fragment crosses back. It contains no MCP protocol, tool, or
envelope logic.
"""

from __future__ import annotations

import json
import re

from hosts.python.parse_adapter import parse_and_normalize

_TRAILING_OFFSET = re.compile(r" at (\d+)$")
_INTERNAL_ERROR = '{"status": "internal_error"}'


def parse_source(source: str) -> str:
    try:
        parsed = parse_and_normalize(source)
        if parsed.get("kind") == "ok":
            reply = {"status": "parsed", "ast": parsed["ast"]}
        elif parsed.get("type") == "SyntaxError":
            match = _TRAILING_OFFSET.search(str(parsed.get("message", "")))
            reply = {"status": "syntax_error", "offset": int(match.group(1)) if match else None}
        else:
            return _INTERNAL_ERROR
        return json.dumps(reply, ensure_ascii=False, allow_nan=False)
    except Exception:
        return _INTERNAL_ERROR
