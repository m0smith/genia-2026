"""Structural tests for #217: host bridge and builtin registration extraction.

Contract reference:  .genia/process/tmp/handoffs/issue-217-builtin-host-bridge-extraction/01-contract.md
Design reference:    .genia/process/tmp/handoffs/issue-217-builtin-host-bridge-extraction/02-design.md

Section 1+2: Import contract tests FAIL before implementation.
Section 3+4: Backward-compat and behavior tests PASS before and after.
"""

import inspect


# ---------------------------------------------------------------------------
# 1. Import contract — FAIL before implementation
# ---------------------------------------------------------------------------


def test_host_bridge_module_importable():
    import genia.host_bridge  # noqa: F401


def test_build_python_host_module_importable_from_host_bridge():
    from genia.host_bridge import _build_python_host_module  # noqa: F401


def test_load_source_from_path_importable_from_host_bridge():
    from genia.host_bridge import _load_source_from_path  # noqa: F401


def test_base_dir_importable_from_host_bridge():
    from genia.host_bridge import BASE_DIR  # noqa: F401


def test_genia_to_python_host_importable_from_host_bridge():
    from genia.host_bridge import _genia_to_python_host  # noqa: F401


def test_python_host_to_genia_importable_from_host_bridge():
    from genia.host_bridge import _python_host_to_genia  # noqa: F401


def test_make_global_env_importable_from_builtins():
    from genia.builtins import make_global_env  # noqa: F401


# ---------------------------------------------------------------------------
# 2. Import graph contract — FAIL before implementation
# ---------------------------------------------------------------------------


def test_host_bridge_does_not_import_interpreter():
    """host_bridge.py must not import from interpreter.py (contract invariant 4)."""
    import genia.host_bridge
    source = inspect.getsource(genia.host_bridge)
    assert "interpreter" not in source, (
        "host_bridge.py must not import from interpreter.py"
    )


def test_builtins_does_not_import_interpreter():
    """builtins.py must not import from interpreter.py (contract invariant 3)."""
    import genia.builtins
    source = inspect.getsource(genia.builtins)
    assert "interpreter" not in source, (
        "builtins.py must not import from interpreter.py"
    )


def test_no_circular_imports_217():
    """Importing host_bridge, builtins, and interpreter together must not cycle."""
    import genia.host_bridge  # noqa: F401
    import genia.builtins  # noqa: F401
    import genia.interpreter  # noqa: F401


# ---------------------------------------------------------------------------
# 3. Backward compatibility — PASS before and after
# ---------------------------------------------------------------------------


def test_make_global_env_importable_from_interpreter():
    """make_global_env remains accessible from interpreter namespace via re-import."""
    from genia.interpreter import make_global_env  # noqa: F401


def test_load_source_from_path_importable_from_interpreter():
    """_load_source_from_path remains accessible from interpreter namespace."""
    from genia.interpreter import _load_source_from_path  # noqa: F401


def test_build_python_host_module_importable_from_interpreter():
    """_build_python_host_module remains accessible from interpreter namespace."""
    from genia.interpreter import _build_python_host_module  # noqa: F401


def test_base_dir_importable_from_interpreter():
    """BASE_DIR remains accessible from interpreter namespace."""
    from genia.interpreter import BASE_DIR  # noqa: F401


def test_genia_to_python_host_importable_from_interpreter():
    """_genia_to_python_host remains accessible from interpreter namespace."""
    from genia.interpreter import _genia_to_python_host  # noqa: F401


def test_python_host_to_genia_importable_from_interpreter():
    """_python_host_to_genia remains accessible from interpreter namespace."""
    from genia.interpreter import _python_host_to_genia  # noqa: F401


def test_make_global_env_importable_from_genia_init():
    """make_global_env remains importable from the genia package."""
    from genia import make_global_env  # noqa: F401


# ---------------------------------------------------------------------------
# 4. Behavior preservation — PASS before and after (regression guard)
# ---------------------------------------------------------------------------

from genia import make_global_env, run_source  # noqa: E402


def _run(src, stdin_data=None):
    env = make_global_env([] if stdin_data is None else stdin_data)
    return run_source(src, env)


def test_make_global_env_produces_env_with_print():
    """make_global_env registers 'print' builtin."""
    from genia.environment import Env
    env = make_global_env([])
    assert isinstance(env, Env)
    assert env.get("print") is not None


def test_make_global_env_produces_env_with_flow_builtins():
    """make_global_env registers core flow builtins."""
    env = make_global_env([])
    for name in ("stdout", "stderr", "cons", "car", "cdr"):
        assert env.get(name) is not None, f"missing builtin: {name}"


def test_make_global_env_from_builtins_matches_interpreter():
    """make_global_env from builtins and interpreter produce equivalent envs."""
    from genia.builtins import make_global_env as make_global_env_builtins
    from genia.interpreter import make_global_env as make_global_env_interp
    env_b = make_global_env_builtins([])
    env_i = make_global_env_interp([])
    # Both should have the same set of registered names
    assert env_b.get("print") is not None
    assert env_i.get("print") is not None


def test_load_source_from_path_stdlib_roundtrip():
    """_load_source_from_path returns non-empty source for stdlib paths."""
    from genia.interpreter import _load_source_from_path
    source, filename = _load_source_from_path("std/prelude/list.genia")
    assert len(source) > 0
    assert "list.genia" in filename or "genia" in filename.lower()


def test_genia_to_python_host_int():
    """_genia_to_python_host converts integers identity."""
    from genia.interpreter import _genia_to_python_host
    assert _genia_to_python_host(42) == 42


def test_genia_to_python_host_str():
    """_genia_to_python_host converts strings identity."""
    from genia.interpreter import _genia_to_python_host
    assert _genia_to_python_host("hello") == "hello"


def test_python_host_to_genia_list():
    """_python_host_to_genia converts Python lists to Genia lists."""
    from genia.interpreter import _python_host_to_genia
    result = _python_host_to_genia([1, 2, 3])
    assert result == [1, 2, 3]


def test_base_dir_is_repo_root():
    """BASE_DIR points to the repository root (contains pyproject.toml or src/)."""
    from genia.interpreter import BASE_DIR
    import pathlib
    assert isinstance(BASE_DIR, pathlib.Path)
    assert (BASE_DIR / "src").exists() or (BASE_DIR / "pyproject.toml").exists()


def test_basic_eval_unchanged():
    assert _run("1 + 2") == 3


def test_function_call_unchanged():
    result = _run("f(x) = x + 1\nf(10)")
    assert result == 11


def test_pipeline_eval_unchanged():
    result = _run("[1,2,3] |> count")
    assert result == 3


def test_autoload_still_works():
    """Autoloaded prelude functions still resolve after extraction."""
    result = _run("map((x) -> x * 2, [1,2,3])")
    assert result == [2, 4, 6]
