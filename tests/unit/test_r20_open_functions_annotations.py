"""R20 contract section 7.2.1 (issue #1067): interface metadata annotations on
an open declaration. Python-host evidence by design: it checks which programs
are rejected and the diagnostic category/context (the annotation and interface
named), never exact wording, plus ownership behaviors that need real module
files. Portable acceptance behavior is in the shared specs
`r20-open-doc-annotation-*`, `r20-open-meta-annotation-*`,
`r20-cross-module-view-reports-base-metadata`, and `r20-open-annotated-declaration`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from genia.builtins import make_global_env
from genia.interpreter import run_source


def _write(tmp_path: Path, name: str, text: str) -> Path:
    """Write `<name>.genia` under `tmp_path` and return its path."""
    path = tmp_path / f"{name}.genia"
    path.write_text(text, encoding="utf-8")
    return path


def _run(source: str, tmp_path: Path | None = None):
    """Run `source` as an entry program (beside module files when `tmp_path` is given)."""
    filename = str(tmp_path / "main.genia") if tmp_path is not None else "<memory>"
    return run_source(source, make_global_env(), filename=filename)


def test_unsupported_annotations_on_an_open_declaration_are_rejected_naming_the_annotation():
    for name, value in (("since", '"1"'), ("category", '"x"'), ("deprecated", '"x"'), ("test", '"t"')):
        with pytest.raises(SyntaxError) as raised:
            _run(f"@{name} {value}\nopen f(0) = 1\n")
        assert name in str(raised.value)


def test_duplicate_doc_or_meta_is_an_error_naming_annotation_and_interface():
    with pytest.raises(SyntaxError) as doc_error:
        _run('@doc "a"\n@doc "b"\nopen f(0) = 1\n')
    assert "doc" in str(doc_error.value) and "f" in str(doc_error.value)
    with pytest.raises(SyntaxError) as meta_error:
        _run('@meta {a: 1}\n@meta {b: 2}\nopen g(0) = 1\n')
    assert "meta" in str(meta_error.value) and "g" in str(meta_error.value)


def test_annotation_on_a_repeated_clause_is_rejected_and_the_interface_keeps_its_metadata():
    with pytest.raises(SyntaxError):
        _run('@doc "owner"\nopen f(0) = 1\n@doc "replacement"\nf(1) = 2\n')


def test_annotation_on_extend_or_use_is_still_rejected(tmp_path):
    _write(tmp_path, "base", 'open get("mem", s, k) = "m"\n')
    _write(tmp_path, "ext", 'import base\n@doc "nope"\nextend base.get("db", d, k) = "d"\n')
    with pytest.raises(SyntaxError):
        _run("import base\nimport ext\n1\n", tmp_path)
    _write(tmp_path, "ext", 'import base\nextend base.get("db", d, k) = "d"\n')
    with pytest.raises(SyntaxError):
        _run('import base\nimport ext\n@doc "nope"\nuse get from base with ext\n', tmp_path)


def test_a_failing_annotation_value_leaves_the_interface_undeclared():
    env = make_global_env()
    with pytest.raises(TypeError):
        run_source('@doc 5\nopen f(0) = 1\n', env)
    with pytest.raises(NameError):
        env.get("f")


def test_help_shows_the_interface_documentation_and_metadata_lines(capsys):
    _run('@doc "Counts things."\n@meta {category: "demo"}\nopen f(0) = 1\nhelp("f")\n')
    out = capsys.readouterr().out
    assert "Counts things." in out
    assert "Category: demo" in out


def test_a_view_in_another_module_reports_the_base_metadata_and_not_its_own(tmp_path):
    _write(tmp_path, "base", '@doc "Base doc."\nopen get("mem", s, k) = "m"\n')
    _write(tmp_path, "ext", 'import base\nextend base.get("db", d, k) = "d"\n')
    _write(
        tmp_path,
        "consumer",
        'import base\nimport ext\nuse get from base with ext\nowner = doc("get")\n',
    )
    result = _run('import consumer\nconsumer.owner\n', tmp_path)
    assert result == "Base doc."
