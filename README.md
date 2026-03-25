# Genia (uv project layout)

This is a uv-based project layout for the current Genia interpreter.

## Layout

- `src/genia/interpreter.py` — the interpreter
- `src/genia/__init__.py` — package exports
- `tests/` — pytest regression suite

## First-time setup

```bash
uv sync --dev
```

This creates `.venv` and installs the dev dependency group. uv projects are managed from `pyproject.toml`, and project commands like `uv sync` and `uv run` create and use the project's environment and lockfile. Official uv docs also recommend `uv run` rather than isolated tool mode for project tools like pytest. citeturn947534search2turn947534search5turn947534search4

## Run tests

```bash
uv run pytest
```

or

```bash
uv run pytest -q
uv run pytest -x
uv run pytest tests/test_higher_order.py -q
```

## Add dependencies

```bash
uv add some-package
uv add --dev pytest
```

uv documents project dependency management through `pyproject.toml`, including `uv add` and `uv remove`. citeturn947534search9

## If starting from scratch next time

A packaged project can be created with `uv init --package`, and uv supports library/app templates plus a standard project structure around `pyproject.toml`. citeturn947534search0turn947534search6turn947534search2
