from pathlib import Path

import pytest

from genia import make_global_env, run_source


def test_exact_fixed_arity_preferred_over_varargs(run):
    src = '''
    pick(a, b) = "exact"
    pick(a, ..rest) = "varargs"
    pick(1, 2)
    '''
    assert run(src) == "exact"


def test_varargs_used_when_no_exact_arity_exists(run):
    src = '''
    pick(a, b) = "exact2"
    pick(a, ..rest) = "varargs"
    pick(1, 2, 3)
    '''
    assert run(src) == "varargs"


def test_ambiguous_varargs_resolution_raises(run):
    with pytest.raises(TypeError, match="Ambiguous function resolution"):
        run(
            '''
            pick(a, ..rest) = "prefix1"
            pick(a, b, ..rest) = "prefix2"
            pick(1, 2, 3)
            '''
        )


def test_autoload_resolution_matches_non_autoload(tmp_path: Path):
    src = '''
    pick(a, b) = "exact"
    pick(a, ..rest) = "varargs"
    pick(1, 2)
    '''
    assert run_source(src, make_global_env([])) == "exact"

    prelude_file = tmp_path / "std" / "prelude" / "pick.genia"
    prelude_file.parent.mkdir(parents=True)
    prelude_file.write_text(
        "pick(a, b) = \"exact\"\n"
        "pick(a, ..rest) = \"varargs\"\n",
        encoding="utf-8",
    )

    env = make_global_env([])
    env.register_autoload("pick", 2, str(prelude_file.resolve()))
    env.register_autoload("pick", 1, str(prelude_file.resolve()))

    assert run_source("pick(1, 2)", env) == "exact"
    assert run_source("pick(1, 2, 3)", env) == "varargs"


def test_autoload_ambiguous_matches_non_autoload(tmp_path: Path):
    with pytest.raises(TypeError, match="Ambiguous function resolution"):
        run_source(
            '''
            pick(a, ..rest) = "prefix1"
            pick(a, b, ..rest) = "prefix2"
            pick(1, 2, 3)
            ''',
            make_global_env([]),
        )

    prelude_file = tmp_path / "std" / "prelude" / "ambiguous.genia"
    prelude_file.parent.mkdir(parents=True)
    prelude_file.write_text(
        "pick(a, ..rest) = \"prefix1\"\n"
        "pick(a, b, ..rest) = \"prefix2\"\n",
        encoding="utf-8",
    )

    env = make_global_env([])
    env.register_autoload("pick", 1, str(prelude_file.resolve()))

    with pytest.raises(TypeError, match="Ambiguous function resolution"):
        run_source("pick(1, 2, 3)", env)
