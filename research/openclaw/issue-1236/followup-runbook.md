# Execute #1236 follow-up evidence case on Benjamin

This is an **external read-only research task**, not implementation, contract approval, or a test of Genia semantics. Evidence commit: `7475646d44fee58bc98294ba78e22727eaab63f1`. Do not check out or modify this research branch in the active R29 checkout: use `git show` to copy the case.

From `~/projects/genia-2026`:

```bash
git fetch origin research/openclaw-1236-isolated-20261120
git show origin/research/openclaw-1236-isolated-20261120:research/openclaw/issue-1236/followup-case.json > /tmp/genia-openclaw-controller/cases/issue-1236-followup.json
```

Then:

```bash
cd /tmp/genia-openclaw-controller
python3 -m unittest -v
python3 genia_workflow.py \
  --case cases/issue-1236-followup.json \
  --sha 7475646d44fee58bc98294ba78e22727eaab63f1 \
  --output-dir runs/issue-1236-followup
cat runs/issue-1236-followup/report.md
```

The follow-up case pins 10 source assertions across 6 files. Review `followup-evidence.md` for the already verified manual inventory. Compare OpenClaw's new claims with that evidence and flag unsupported requirements rather than accepting all of a model's design speculation.

The reviewer is optional because it was expensive and prone to false objections in the previous run. If needed later:

```bash
python3 genia_workflow.py \
  --case cases/issue-1236-followup.json \
  --sha 7475646d44fee58bc98294ba78e22727eaab63f1 \
  --review \
  --output-dir runs/issue-1236-followup-reviewed
```

Never merge this branch into `main` or modify R29 as part of the experiment. The actual live follow-up output is not yet part of this branch; source notes are explicitly distinct from execution logs.
