# Python Host AGENTS

Use the root `AGENTS.md` first.

Additional host-local rules:

- root shared docs remain authoritative:
  - `GENIA_STATE.md`
  - `GENIA_RULES.md`
  - `GENIA_REPL_README.md`
  - `docs/host-interop/*`
  - `spec/manifest.json`
- Python is the current reference host, so accidental semantic drift here is especially risky
- host-local convenience must not override shared semantics
- keep `src/genia/std/prelude/` and `std/prelude/` synchronized when changing shared prelude files

Known local commands:

- setup: `uv sync --dev`
- lint: `uvx ruff check .`
- tests: `uv run pytest -q -vv --maxfail=1`
- coverage: `uv run pytest --cov=genia --cov-report=term-missing`
- run REPL: `python3 -m genia.interpreter`

If a change affects shared semantics, also update:

- `docs/host-interop/HOST_CAPABILITY_MATRIX.md`
- `spec/manifest.json` when the shared host contract changes
- relevant `docs/book/*`
