# Investigation Recovery Note — Issue #1010 (F0)

Status: **NON-AUTHORITATIVE. Investigative only. Does not define implemented
behavior.** `GENIA_STATE.md` remains final authority for all implemented
Genia behavior. Nothing in this note may be cited as language truth.

## Purpose

Issue #1010 (R20 follow-up: unify Function semantics and settle
extensibility declaration) asks F0 to recover and preserve, under
`docs/analysis/`, the full text of two prior investigations referenced by
the issue:

1. "Unified Function Model — Contract Gate Report"
2. "Natural-Language Neutrality in Genia Syntax — Architecture Investigation"

Both are cited in issue #1010 as prior work whose *findings* seeded the
issue's working semantic model (`Pattern -> Clause -> Function`,
`ContributionUnit`, `FunctionView`) and its "do not invent punctuation
merely to avoid English" framing. Issue #1010 explicitly requires that
these documents be treated as evidence, not language truth, even if
recovered in full.

## What was searched

This session searched the following locations for the complete text of
either report, in the `m0smith/genia-2026` repository, before starting any
other F0/F1 work:

- Full-text search of `docs/` for `unified function model`,
  `natural-language neutrality` / `natural language neutrality`, and
  related filename patterns (`*unified-function*`, `*neutrality*`) — no
  matches.
- `git log --all` (every local branch and ref) for commits whose message or
  added file paths mention either title — no matches.
- GitHub issue/PR search (`search_issues`) across
  `repo:m0smith/genia-2026` for `"Unified Function Model"` and
  `"Natural-Language Neutrality"` — zero results for both queries.
- The current issue #1010 body and its comment thread — the issue
  summarizes and quotes conclusions attributed to both investigations (the
  working semantic model in the issue body, and the note that "Genia's
  grammar is already structurally small and mostly uses contextual/soft
  keywords" / "we should not invent punctuation merely to avoid English"),
  but does not attach or link either report's full text.

No copy of either report — complete, partial, or as a distinct committed
file — was found anywhere in this repository's git history, working tree,
or GitHub issue/PR history accessible to this session.

## Disposition

Per issue #1010's own instruction: *"If a complete report cannot be
recovered, do not reconstruct it from memory. Record that limitation and
continue using independently verified evidence."*

This session does not reconstruct either report from memory or inference.
The only evidence this session treats as authoritative for F1 is:

- the approved R20 contract and design documents
  (`docs/design/r20-open-functions-contract.md`,
  `docs/design/r20-open-functions-syntax-ir-design.md`);
- `GENIA_STATE.md` section 4.7 (implemented R20 truth) and section 4
  (ordinary function/dispatch truth);
- direct reading of the current implementation
  (`src/genia/callable.py`, `src/genia/evaluator.py`,
  `src/genia/parser.py`, `src/genia/lowering.py`,
  `src/genia/environment.py`, `src/genia/ast_nodes.py`, `src/genia/ir.py`);
  and
- independent, freshly-run reproductions against the current interpreter
  (`uv run python -m genia.interpreter <file>.genia`) performed during this
  F0/F1 pass, recorded in the companion verification evidence referenced by
  the F1 decision report.

The working semantic model quoted in issue #1010's body
(`Pattern -> Clause -> Function` / `ContributionUnit` / `FunctionView`) is
carried forward as a **hypothesis to test**, exactly as the issue frames
it, not as a conclusion either recovered report already reached and proved.
Any claim in the F1 contract or decision report that happens to echo a
theme attributed to one of the two missing investigations (for example,
"do not invent punctuation to avoid English") is independently justified in
this session's own F1 materials from `AGENTS.md`'s core-surface-freeze
rules and the issue's own explicit surface-syntax-out-of-scope instruction
— not from the unrecovered report's authority.

## If either report resurfaces later

Should a complete copy of either investigation be located later (for
example, in an external chat log, a different fork, or a contributor's
local files), it should be added under `docs/analysis/` as its own
clearly-labeled non-authoritative artifact (investigative, non-authoritative,
does not define implemented behavior — same labeling as this note) rather
than merged into this note or into any authoritative document.
