#!/usr/bin/env python3
"""Build docs/state-record/ from the GENIA_STATE.md distillation ledger (#1099 PR B, phase 4b).

Each ledger row whose disposition is `moved` or `retained-condensed` is copied **verbatim**
from the baseline STATE (read from git history at the ledger's baseline SHA) into its record
file, under a provenance line. The records are non-authoritative audit/provenance material;
`GENIA_STATE.md` governs.

  python tools/state_records.py --write    # (re)generate docs/state-record/*.md
  python tools/state_records.py --check    # fail if a committed record differs from a fresh build
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "docs" / "analysis" / "state-distillation-migration-map.json"
FENCE = "~~~~~"

RECORDS = {
    "docs/state-record/hosts-and-conformance.md": ("Hosts and conformance record", "R16 protocol chronology, R26/R27 C++ host entries, and shared-conformance detail displaced from STATE sections 0 and 1."),
    "docs/state-record/tooling-and-examples.md": ("Tooling and examples record", "Documentation-publishing and `@doc` tooling sections (0.2-0.4) and the example-demo catalogue (section 11)."),
    "docs/state-record/capability-records.md": ("Capability and feature record", "Per-ticket runtime-capability narratives (R10-R14), R20 open-function narrative, and ticket-tagged pattern/Template blocks."),
    "docs/state-record/builtin-records.md": ("Builtin detail record", "Pre-condensation text of builtin sections (R17-R19 portability, validation helpers, Option model, bridges, and others)."),
    "docs/state-record/native-test-and-lifecycle-shape-records.md": ("Native test and lifecycle data-shape record", "Pre-condensation text of STATE sections 9.1-9.6."),
    "docs/state-record/server-and-process-records.md": ("Server and process record", "Pre-condensation text of the CORS wrapper, 9.7 R8 server execution contract, and 9.40 external process execution."),
    "docs/state-record/r14-lifecycle-http-records.md": ("R14 lifecycle and outbound HTTP record", "Sections 9.8-9.20, ticket by ticket."),
    "docs/state-record/numeric-r21-r23-records.md": ("R21-R23 numeric record", "Sections 9.21-9.37, ticket by ticket."),
    "docs/state-record/provider-proof-records.md": ("Provider-composition proof record", "Sections 9.38-9.39 (P8 and P9 proofs)."),
    "docs/state-record/r28-mcp-records.md": ("R28 MCP record", "Sections 9.41-9.47 history and the pre-condensation text of 9.48-9.51."),
}


def load_ledger() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def baseline_lines(ledger: dict) -> list[str]:
    sha = ledger["baseline"]["sha"]
    raw = subprocess.check_output(["git", "show", f"{sha}:GENIA_STATE.md"], cwd=REPO)
    return raw.decode("utf-8").split("\n")


def row_text(lines: list[str], row: dict) -> str:
    return "\n".join(lines[row["start"] - 1 : row["end"]])


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def provenance(ledger: dict, row: dict) -> str:
    sha = ledger["baseline"]["sha"][:8]
    return f"Moved from GENIA_STATE.md@{sha}, lines {row['start']}-{row['end']} (ledger row {row['id']}, {row['disposition']}, sha256 {row['sha256'][:16]})"


def build(ledger: dict, lines: list[str]) -> dict[str, str]:
    out: dict[str, list[str]] = {}
    for path, (title, scope) in RECORDS.items():
        out[path] = [
            f"# {title}",
            "",
            "> **Non-authoritative provenance record.** This file preserves, verbatim and unedited, text that was displaced",
            "> from `GENIA_STATE.md` during the #1099 distillation. It is audit material, not part of the truth hierarchy:",
            "> it does not define Genia behavior, and `GENIA_STATE.md` governs. Start with the release, design, and reference",
            "> documents; open this file only to see the exact displaced wording.",
            ">",
            f"> Baseline: `GENIA_STATE.md` at `{ledger['baseline']['sha']}`. Scope: {scope}",
            "> Ledger: `docs/analysis/state-distillation-migration-map.json`.",
            "",
        ]
    for row in ledger["rows"]:
        if not row["archive"]:
            continue
        text = row_text(lines, row)
        assert digest(text) == row["sha256"], row["id"]
        assert FENCE not in text
        out[row["archive"]] += [f"## {row['id']}: baseline lines {row['start']}-{row['end']}", "", provenance(ledger, row), "", f"{FENCE}markdown", text, FENCE, ""]
    return {path: "\n".join(parts).rstrip("\n") + "\n" for path, parts in out.items()}


def main(argv: list[str]) -> int:
    ledger = load_ledger()
    built = build(ledger, baseline_lines(ledger))
    if "--write" in argv:
        for path, content in built.items():
            target = REPO / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        return 0
    bad = [p for p, c in built.items() if not (REPO / p).is_file() or (REPO / p).read_text(encoding="utf-8") != c]
    for p in bad:
        print(f"state_records: {p} differs from a fresh build", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
