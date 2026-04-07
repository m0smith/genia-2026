# Python Host

Status:

- implemented
- current reference host/prototype

Current reality in this phase:

- the working Python host still lives at `src/genia/`
- the current runtime entrypoint is `src/genia/interpreter.py`
- the package script entrypoint is `genia = genia.interpreter:_main`
- `hosts/python/` is documentation scaffolding for the future monorepo layout, not the current source location

Rules:

- Python remains the semantic reference host until another host exists with matching shared spec coverage
- host-local convenience must not override shared semantics
- updates that change shared behavior must also update the shared docs/spec artifacts

Known commands:

- setup: `uv sync --dev`
- run REPL: `python3 -m genia.interpreter`
- run CLI entrypoint: `genia -c "1 + 2"`
- lint: `uvx ruff check .`
- tests: `uv run pytest -q -vv --maxfail=1`
- tests with coverage: `uv run pytest --cov=genia --cov-report=term-missing`
