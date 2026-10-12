"""R20 contract section 8 (issue #1067, F1-F): diagnostics carry accurate
context. Python-host evidence by design: it asserts the diagnostic identity and
the context a message must name (module identity instead of a filesystem path,
available shapes, the actual existing binding), never exact English wording,
because wording is host-local. Real parser -> lowering -> evaluator path via
`genia.interpreter.run_source`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from genia.builtins import make_global_env
from genia.callable import (
    OpenFunctionDuplicateClauseError,
    OpenFunctionNoMatchingFunctionError,
    OpenFunctionRedeclarationError,
)
from genia.interpreter import run_source


def _write(tmp_path: Path, name: str, text: str) -> Path:
    """Write `<name>.genia` under `tmp_path` and return its path."""
    path = tmp_path / f"{name}.genia"
    path.write_text(text, encoding="utf-8")
    return path


def _run(tmp_path: Path, source: str):
    """Run `source` as the entry program `main.genia` beside the module files in `tmp_path`.

    Imports resolve relative to that file; the program's value is returned and
    any Genia error propagates."""
    return run_source(source, make_global_env(), filename=str(tmp_path / "main.genia"))


def test_duplicate_clause_in_an_imported_module_names_the_module_not_its_path(tmp_path):
    _write(tmp_path, "base", 'open get("mem", store, key) = "mem"\n')
    _write(
        tmp_path,
        "ext",
        'import base\nextend base.get("db", d, k) = "one"\nextend base.get("db", e, j) = "two"\n',
    )
    with pytest.raises(OpenFunctionDuplicateClauseError) as raised:
        _run(tmp_path, "import base\nimport ext\n1\n")
    message = str(raised.value)
    assert str(tmp_path) not in message
    assert "ext:2" in message and "ext:3" in message


def test_duplicate_clause_in_the_entry_program_keeps_its_source_label():
    with pytest.raises(OpenFunctionDuplicateClauseError) as raised:
        run_source("open f(0) = 1\nf(0) = 2\n", make_global_env(), filename="<command>")
    assert "<command>:1" in str(raised.value) and "<command>:2" in str(raised.value)


def test_arity_miss_names_available_shapes_like_an_ordinary_function():
    with pytest.raises(OpenFunctionNoMatchingFunctionError) as raised:
        run_source("open f(0) = 1\nf(a, b) = 2\nf(x, y, z, ..r) = 3\n\nf()\n", make_global_env())
    # f() has no clause of arity 0: Available lists fixed shapes then varargs.
    message = str(raised.value)
    assert message.startswith("No matching function: f/0")
    assert "Available:" in message
    assert "f/1" in message and "f/2" in message and "f/3+" in message


def test_ordinary_function_then_open_says_ordinary_function_not_already_open():
    with pytest.raises(OpenFunctionRedeclarationError) as raised:
        run_source("f(n) = 1\nopen f(0) = 2\n", make_global_env())
    message = str(raised.value)
    assert message.startswith("open-function-redeclaration:")
    assert "already declared open" not in message
    assert "ordinary function" in message


def test_non_function_binding_then_open_says_non_function_value():
    with pytest.raises(OpenFunctionRedeclarationError) as raised:
        run_source("f = 1\nopen f(0) = 2\n", make_global_env())
    message = str(raised.value)
    assert message.startswith("open-function-redeclaration:")
    assert "already declared open" not in message
    assert "non-function" in message


def test_open_then_open_in_one_module_still_says_already_declared_open():
    with pytest.raises(SyntaxError, match="open-function-redeclaration"):
        run_source("open f(0) = 1\nopen f(1) = 2\n", make_global_env())


def test_ordinary_definition_over_a_linked_view_names_the_open_view(tmp_path):
    _write(tmp_path, "base", 'open get("mem", store, key) = "mem"\n')
    _write(tmp_path, "ext", 'import base\nextend base.get("db", d, k) = "db"\n')
    with pytest.raises(TypeError) as raised:
        _run(tmp_path, "import base\nimport ext\nuse get from base with ext\nget(n) = 99\n")
    message = str(raised.value)
    assert "open" in message
    assert "non-function value" not in message


def test_use_over_an_ordinary_function_replaces_it_unchanged(tmp_path):
    """Compatibility decision (contract 4.2): not diagnosed, current behavior kept."""
    _write(tmp_path, "base", 'open get("mem", store, key) = "mem"\n')
    _write(tmp_path, "ext", 'import base\nextend base.get("db", d, k) = "db"\n')
    result = _run(
        tmp_path,
        'import base\nimport ext\nget(n) = 99\nuse get from base with ext\nget("db", 1, 2)\n',
    )
    assert result == "db"
