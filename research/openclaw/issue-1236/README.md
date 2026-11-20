# OpenClaw research spike for issue #1236

Status: **READ-ONLY RESEARCH PACKET — NOT AN ACCEPTED CONTRACT OR IMPLEMENTATION**.

Issue: https://github.com/m0smith/genia-2026/issues/1236

## Isolation

- Branch: `research/openclaw-1236-isolated-20261120` (not `main`).
- Base and evidence commit: `7475646d44fee58bc98294ba78e22727eaab63f1`.
- Work here must not modify R29/#1328, #1251, source semantics, shared specs, or authoritative root docs.
- No PR, merge, issue closure, implementation, or acceptance authorization from this spike.
- Follow `AGENTS.md`; implemented language authority remains `GENIA_STATE.md`, then `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`.
- Case uses nine exact-line assertions from four files, and it is *not* a repository-wide audit.

## Run on Benjamin (Ubuntu WSL)

Use the already tested local v0.9 controller in `/tmp/genia-openclaw-controller`. From an existing checkout of the Genia repo, run:

```bash
git fetch origin research/openclaw-1236-isolated-20261120
git show origin/research/openclaw-1236-isolated-20261120:research/openclaw/issue-1236/case.json > /tmp/genia-openclaw-controller/cases/issue-1236.json

cd /tmp/genia-openclaw-controller
python3 -m unittest -v
python3 genia_workflow.py \
  --case cases/issue-1236.json \
  --sha 7475646d44fee58bc98294ba78e22727eaab63f1 \
  --output-dir runs/issue-1236-research
cat runs/issue-1236-research/report.md
```

If the first run is useful, reviewer mode is optional and expensive; run it only for substantive disputed claims:

```bash
python3 genia_workflow.py \
  --case cases/issue-1236.json \
  --sha 7475646d44fee58bc98294ba78e22727eaab63f1 \
  --review \
  --output-dir runs/issue-1236-review
```

## Acceptance for this research spike

1. Deterministic evidence pinning passes; no agent retrieval or execution claims.
2. Describe the exact currently implemented `|>` data-application behavior, not the desired callable-stage composition.
3. Separate confirmed source facts from proposed alternatives, unsupported interpretation, and gaps.
4. Report consequences for Flow demand, terminal consumption, Outcome propagation, error indexing, Core IR, and C++ honestly as questions unless established.
5. Produce a short pre-flight research report on this isolated branch **after a live run**. Do not merge or treat a model verdict as semantic approval.

The file `case.json` is an external v0.9 controller input copied into the branch for repeatability; the Genia repo does not run this automatically.
