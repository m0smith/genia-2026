"""Narrow host parse capability for the native Genia MCP server (R28 E28-2, issue #703).

`parse_source(source)` reaches the existing normalized parse surface
(`hosts/python/parse_adapter.parse_and_normalize`, unchanged) because Genia source
cannot call the parser itself (ledger R28-H17). It returns text of exactly one shape:

- parsed: `{"status": "parsed"}` + "\n" + the unchanged normalized AST serialized
  losslessly (exact integers, never rounded or stringified; no raw newline). The AST
  is opaque transport data for `mcp.genia` and is deliberately not routed through the
  R9 portable-JSON range (ledger R28-H22, contract Clarification A3);
- syntax error: `{"offset": <int or null>, "status": "syntax_error"}` (no AST);
- `{"status": "internal_error"}`.

It never evaluates source, reads files, or resolves imports, and no exception text,
class name, or source fragment crosses back. It contains no MCP protocol, tool, or
envelope logic.
"""


from __future__ import annotations

import json
import re

from hosts.python.parse_adapter import parse_and_normalize

_TRAILING_OFFSET = re.compile(r" at (\d+)$")
_PARSED_HEADER = '{"status": "parsed"}'
_INTERNAL_ERROR = '{"status": "internal_error"}'


def parse_source(source: str) -> str:
    try:
        parsed = parse_and_normalize(source)
        if parsed.get("kind") == "ok":
            ast_text = json.dumps(
                parsed["ast"],
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ": "),
            )
            return _PARSED_HEADER + "\n" + ast_text
        elif parsed.get("type") == "SyntaxError":
            match = _TRAILING_OFFSET.search(str(parsed.get("message", "")))
            reply = {"status": "syntax_error", "offset": int(match.group(1)) if match else None}
        else:
            return _INTERNAL_ERROR
        return json.dumps(reply, ensure_ascii=False, allow_nan=False, sort_keys=True)
    except Exception:
        return _INTERNAL_ERROR
