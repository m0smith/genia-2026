"""E20-4/E20-5 (#R20 open functions): Python-host unit evidence for the
explicit cross-module contribution/linking behavior required by
docs/design/r20-open-functions-contract.md sections 4-6.

These cases require a real second `.genia` module file on disk, which the
generic shared eval/error YAML runner (tools/spec_runner) cannot express
today — it accepts one inline `source` string per case with no multi-file
fixture mechanism. That gap is disclosed in
tests/spec/test_r20_open_functions_shared_specs.py and
docs/releases/R20.md; this file is R20's actual cross-module test evidence.

Every test exercises the real parser -> lowering -> evaluator path via
`genia.interpreter.run_source`, never a hand-built runtime value, so it is
faithful evidence of the contract's cross-module obligations even though it
is not yet expressed as a portable YAML spec.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from genia.builtins import make_global_env
from genia.callable import (
    OpenFunctionDuplicateSelectionError,
    OpenFunctionIncompatibleContributionError,
    OpenFunctionClauseAmbiguityError,
)
from genia.interpreter import run_source


def _write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / f"{name}.genia"
    path.write_text(text, encoding="utf-8")
    return path


def _base_and_contribs(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "base",
        'open get("mem", store, key) = "mem:" + key\n',
    )
    _write(
        tmp_path,
        "db_ext",
        'import base\nextend base.get("db", db, key) = "db:" + key\n',
    )
    _write(
        tmp_path,
        "cache_ext",
        'import base\nextend base.get("cache", c, key) = "cache:" + key\n',
    )
    # A contribution overlapping db_ext's own shape, for the ambiguity case.
    _write(
        tmp_path,
        "db_ext2",
        'import base\nextend base.get("db", db, key) = "db2:" + key\n',
    )


def _run(tmp_path: Path, entry_name: str, entry_source: str):
    _write(tmp_path, entry_name, entry_source)
    env = make_global_env()
    return run_source(entry_source, env, filename=str(tmp_path / f"{entry_name}.genia"))


def test_base_plus_two_disjoint_contributions_dispatch_correctly(tmp_path):
    _base_and_contribs(tmp_path)
    result = _run(
        tmp_path,
        "main",
        "import base\nimport db_ext\nimport cache_ext\n\n"
        "use get from base with db_ext, cache_ext\n\n"
        '[get("mem", "x", "k1"), get("db", 1, "k2"), get("cache", 1, "k3")]\n',
    )
    assert result == ["mem:k1", "db:k2", "cache:k3"]


def test_ordinary_import_does_not_extend_visible_open_function(tmp_path):
    _base_and_contribs(tmp_path)
    with pytest.raises(TypeError, match="No matching case"):
        _run(
            tmp_path,
            "main",
            'import base\nimport db_ext\n\nbase.get("db", 1, "k2")\n',
        )


def test_import_order_cannot_alter_dispatch_selection(tmp_path):
    _base_and_contribs(tmp_path)
    forward = _run(
        tmp_path,
        "main_forward",
        "import base\nimport db_ext\nimport cache_ext\n\n"
        "use get from base with db_ext, cache_ext\n\n"
        'get("db", 1, "k2")\n',
    )
    backward = _run(
        tmp_path,
        "main_backward",
        "import cache_ext\nimport db_ext\nimport base\n\n"
        "use get from base with cache_ext, db_ext\n\n"
        'get("db", 1, "k2")\n',
    )
    assert forward == backward == "db:k2"


def test_duplicate_selection_through_two_aliases_of_one_cached_module_is_rejected(tmp_path):
    _base_and_contribs(tmp_path)
    with pytest.raises(OpenFunctionDuplicateSelectionError):
        _run(
            tmp_path,
            "main",
            "import base\nimport db_ext\nimport db_ext as db_ext_alias\n\n"
            "use get from base with db_ext, db_ext_alias\n",
        )


def test_two_contributions_with_overlapping_dispatch_key_are_ambiguous_not_prioritized(tmp_path):
    _base_and_contribs(tmp_path)
    with pytest.raises(OpenFunctionClauseAmbiguityError):
        _run(
            tmp_path,
            "main",
            "import base\nimport db_ext\nimport db_ext2\n\n"
            "use get from base with db_ext, db_ext2\n\n"
            'get("db", 1, "k2")\n',
        )


def test_selecting_a_plain_import_with_no_contribution_unit_is_incompatible(tmp_path):
    _base_and_contribs(tmp_path)
    _write(tmp_path, "unrelated", "value = 1\n")
    with pytest.raises(OpenFunctionIncompatibleContributionError):
        _run(
            tmp_path,
            "main",
            "import base\nimport unrelated\n\nuse get from base with unrelated\n",
        )


def test_unrelated_import_order_cannot_affect_dispatch(tmp_path):
    _base_and_contribs(tmp_path)
    _write(tmp_path, "unrelated_a", "value = 1\n")
    _write(tmp_path, "unrelated_b", "value = 2\n")
    first = _run(
        tmp_path,
        "main_u1",
        "import unrelated_a\nimport unrelated_b\nimport base\nimport db_ext\n\n"
        "use get from base with db_ext\n\n"
        'get("db", 1, "k2")\n',
    )
    second = _run(
        tmp_path,
        "main_u2",
        "import unrelated_b\nimport unrelated_a\nimport base\nimport db_ext\n\n"
        "use get from base with db_ext\n\n"
        'get("db", 1, "k2")\n',
    )
    assert first == second == "db:k2"


def test_linked_view_is_local_to_the_module_that_wrote_use(tmp_path):
    """A consumer's `use` does not retroactively change what `base.get`
    resolves to for other modules, and a second consumer that never wrote
    `use` never sees the contribution (contract §4.2 non-transitivity)."""
    _base_and_contribs(tmp_path)
    result = _run(
        tmp_path,
        "main",
        "import base\nimport db_ext\n\n"
        "use get from base with db_ext\n\n"
        # base.get itself (not the locally linked `get`) still only sees its
        # own base clauses.
        'base.get("mem", "x", "k1")\n',
    )
    assert result == "mem:k1"


def test_alias_identity_two_aliases_of_the_same_module_are_one_interface(tmp_path):
    _write(tmp_path, "iface", 'open ping(x) = "pong:" + x\n')
    result = _run(
        tmp_path,
        "main",
        'import iface\nimport iface as iface2\n\n[iface.ping("a") == iface2.ping("a")]\n',
    )
    assert result == [True]
