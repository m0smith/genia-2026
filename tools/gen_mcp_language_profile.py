#!/usr/bin/env python3
"""Project the governed MCP language-profile registry into apps/mcp/mcp.genia (#1099).

The registry is the ``mcp_language_profile`` key of ``docs/contract/semantic_facts.json``. It is a
guarded projection source: ``GENIA_STATE.md`` stays the semantic authority (each fact carries
semantic anchors and evidence), and the MCP language-profile tool stays native Genia with no runtime
file or Markdown reading. This tool renders the governed constants into a delimited block.

  python tools/gen_mcp_language_profile.py           # rewrite the generated block
  python tools/gen_mcp_language_profile.py --check   # fail if the block or registry is stale/invalid

The tool is pure: stdlib only, deterministic, and adds no Genia semantics.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FACTS_PATH = REPO / "docs" / "contract" / "semantic_facts.json"
SERVER_PATH = REPO / "apps" / "mcp" / "mcp.genia"
REGISTRY_KEY = "mcp_language_profile"

BEGIN = "# >>> BEGIN GENERATED: mcp_language_profile (docs/contract/semantic_facts.json) >>>"
END = "# <<< END GENERATED: mcp_language_profile <<<"

STATUSES = ("implemented", "partial", "planned", "scaffolded", "unsupported")
MATURITIES = (None, "Experimental", "Partial", "Stable")
SCOPES_FACT_KEYS = ("id", "scope", "status", "maturity", "summary", "anchors", "evidence")
LANGUAGE_MEMBERS = ("control_flow", "supported_forms", "patterns", "absent_forms", "idioms")
CONSTANTS = {
    "control_flow": "LANGUAGE_CONTROL_FLOW",
    "supported_forms": "LANGUAGE_SUPPORTED_FORMS",
    "patterns": "LANGUAGE_PATTERNS",
    "absent_forms": "LANGUAGE_ABSENT_FORMS",
    "idioms": "LANGUAGE_IDIOMS",
}
DISCOVERY_FACT_COUNT = 15
SUMMARY_MAX_BYTES = 256
DISCOVERY_MAX_BYTES = 16384
EVIDENCE_KINDS = ("state_text", "probe", "manifest")


def load_registry(path: Path | None = None) -> dict:
    data = json.loads((path or FACTS_PATH).read_text(encoding="utf-8"))
    return data[REGISTRY_KEY]


# --- validation --------------------------------------------------------------------------------


def _covered(anchor: str, cited: set[str], anchors: dict) -> bool:
    """True when `anchor` is cited or lies (via the crosswalk's `within`) inside a cited anchor."""
    seen: set[str] = set()
    while anchor and anchor not in seen:
        if anchor in cited:
            return True
        seen.add(anchor)
        anchor = anchors.get(anchor, {}).get("within")
    return False


def _evidence_problems(owner: str, evidence, cited_anchors, anchors) -> list[str]:
    problems: list[str] = []
    if not isinstance(evidence, list) or not evidence:
        return [f"{owner}: evidence must be a non-empty list"]
    for item in evidence:
        kind = item.get("kind") if isinstance(item, dict) else None
        if kind not in EVIDENCE_KINDS:
            problems.append(f"{owner}: unknown evidence kind {kind!r}")
        elif kind == "state_text":
            if item.get("anchor") not in anchors:
                problems.append(f"{owner}: evidence anchor {item.get('anchor')!r} is not in state_anchors")
            elif cited_anchors is not None and not _covered(item["anchor"], cited_anchors, anchors):
                problems.append(f"{owner}: evidence anchor {item['anchor']!r} is outside every cited anchor")
            if not isinstance(item.get("fragment"), str) or not item["fragment"].strip():
                problems.append(f"{owner}: state_text evidence needs a non-empty fragment")
        elif not isinstance(item.get("name"), str) or not item["name"]:
            problems.append(f"{owner}: {kind} evidence needs a name")
    return problems


def validate(registry: dict) -> list[str]:
    problems: list[str] = []
    anchors = registry.get("state_anchors", {})
    for name, row in anchors.items():
        if not name.startswith("state:") or not isinstance(row.get("legacy_section"), str):
            problems.append(f"state_anchors[{name!r}] needs a string legacy_section")
        if "within" in row and row["within"] not in anchors:
            problems.append(f"state_anchors[{name!r}].within names an unknown anchor")
    language = registry.get("language", {})
    if tuple(language) != LANGUAGE_MEMBERS:
        problems.append(f"language members must be exactly {LANGUAGE_MEMBERS}")
    for member, body in language.items():
        if set(body) != {"value", "evidence"}:
            problems.append(f"language.{member} must have exactly value and evidence")
            continue
        problems += _evidence_problems(f"language.{member}", body["evidence"], None, anchors)
    discovery = registry.get("discovery", {})
    if discovery.get("coverage") != "curated_non_exhaustive":
        problems.append("discovery.coverage must be 'curated_non_exhaustive'")
    facts = discovery.get("facts", [])
    if len(facts) != DISCOVERY_FACT_COUNT:
        problems.append(f"discovery must hold exactly {DISCOVERY_FACT_COUNT} facts, found {len(facts)}")
    ids = [fact.get("id") for fact in facts]
    if len(set(ids)) != len(ids):
        problems.append("discovery fact ids must be unique")
    for fact in facts:
        fid = fact.get("id")
        if tuple(fact) != SCOPES_FACT_KEYS:
            problems.append(f"{fid}: fact keys must be exactly {SCOPES_FACT_KEYS} in order")
            continue
        if fact["status"] not in STATUSES:
            problems.append(f"{fid}: status {fact['status']!r} is not in the closed set")
        if fact["maturity"] not in MATURITIES:
            problems.append(f"{fid}: maturity {fact['maturity']!r} is not in the closed set")
        size = len(fact["summary"].encode("utf-8"))
        if not 0 < size <= SUMMARY_MAX_BYTES:
            problems.append(f"{fid}: summary must be 1..{SUMMARY_MAX_BYTES} UTF-8 bytes")
        cited = fact["anchors"]
        if not cited or any(a not in anchors for a in cited):
            problems.append(f"{fid}: every cited anchor must be in state_anchors")
        problems += _evidence_problems(fid, fact["evidence"], set(cited), anchors)
    if not problems and len(json.dumps(wire_projection(registry)["discovery"], ensure_ascii=False).encode("utf-8")) > DISCOVERY_MAX_BYTES:
        problems.append(f"discovery JSON exceeds {DISCOVERY_MAX_BYTES} bytes")
    return problems


def referenced_probes(registry: dict) -> set[str]:
    return _referenced(registry, "probe")


def referenced_manifest_checks(registry: dict) -> set[str]:
    return _referenced(registry, "manifest")


def _referenced(registry: dict, kind: str) -> set[str]:
    items = [i for body in registry["language"].values() for i in body["evidence"]]
    items += [i for fact in registry["discovery"]["facts"] for i in fact["evidence"]]
    return {i["name"] for i in items if i["kind"] == kind}


# --- projection --------------------------------------------------------------------------------


def wire_projection(registry: dict) -> dict:
    """The language members the wire must carry (excludes name, contract_revision, examples)."""
    table = registry["state_anchors"]
    out = {member: registry["language"][member]["value"] for member in LANGUAGE_MEMBERS}
    out["discovery"] = {
        "coverage": registry["discovery"]["coverage"],
        "facts": [
            {
                "id": fact["id"],
                "scope": fact["scope"],
                "status": fact["status"],
                "maturity": fact["maturity"],
                "summary": fact["summary"],
                "state_sections": [table[a]["legacy_section"] for a in fact["anchors"]],
            }
            for fact in registry["discovery"]["facts"]
        ],
    }
    return out


def _string(value: str) -> str:
    if any(ch in value for ch in '"\\') or any(ord(ch) < 32 for ch in value):
        raise ValueError(f"string needs escaping the generator does not support: {value!r}")
    return f'"{value}"'


def _render(value, indent: int) -> str:
    pad = "  " * indent
    if value is None:
        return "nil"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return _string(value)
    if isinstance(value, list):
        if all(isinstance(v, str) for v in value):
            return "[" + ", ".join(_string(v) for v in value) + "]"
        inner = ",\n".join(f"{pad}  {_render(v, indent + 1)}" for v in value)
        return "[\n" + inner + f"\n{pad}]"
    if isinstance(value, dict):
        inner = ",\n".join(f"{pad}  {key}: {_render(v, indent + 1)}" for key, v in value.items())
        return "{\n" + inner + f"\n{pad}}}"
    raise TypeError(f"unsupported value {value!r}")


def render_block(registry: dict) -> str:
    projection = wire_projection(registry)
    lines = [
        BEGIN,
        "# Generated from the governed registry; GENIA_STATE.md governs. Do not edit by hand:",
        "# run `python tools/gen_mcp_language_profile.py` and commit the result.",
        "",
    ]
    for member in LANGUAGE_MEMBERS:
        lines.append(f"{CONSTANTS[member]} = {_render(projection[member], 0)}")
        lines.append("")
    lines.append("# A7: static curated facts; nil encodes as JSON null. No live discovery.")
    lines.append(f"LANGUAGE_DISCOVERY = {_render(projection['discovery'], 0)}")
    lines.append(END)
    return "\n".join(lines)


def splice(server_text: str, block: str) -> str:
    start = server_text.index(BEGIN)
    end = server_text.index(END, start) + len(END)
    return server_text[:start] + block + server_text[end:]


def check(registry: dict | None = None, server_text: str | None = None) -> list[str]:
    registry = registry if registry is not None else load_registry()
    server_text = server_text if server_text is not None else SERVER_PATH.read_text(encoding="utf-8")
    problems = validate(registry)
    if server_text.count(BEGIN) != 1 or server_text.count(END) != 1 or server_text.index(BEGIN) > server_text.index(END):
        return problems + ["mcp.genia must contain exactly one BEGIN/END generated block in order"]
    if problems:
        return problems
    if splice(server_text, render_block(registry)) != server_text:
        problems.append("generated block in apps/mcp/mcp.genia is stale: run tools/gen_mcp_language_profile.py")
    return problems


def main(argv: list[str]) -> int:
    registry = load_registry()
    server_text = SERVER_PATH.read_text(encoding="utf-8")
    if "--check" in argv:
        problems = check(registry, server_text)
        for problem in problems:
            print(f"gen_mcp_language_profile: {problem}", file=sys.stderr)
        return 1 if problems else 0
    problems = validate(registry)
    if problems:
        for problem in problems:
            print(f"gen_mcp_language_profile: {problem}", file=sys.stderr)
        return 1
    SERVER_PATH.write_text(splice(server_text, render_block(registry)), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
