import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug


def test_import_module_and_named_access_from_std_prelude(run):
    src = """
    import math
    [math/pi, math/inc(2)]
    """
    assert run(src) == [pytest.approx(3.141592653589793), 3]


def test_import_module_with_alias_binds_same_module_value(run):
    src = """
    import math
    import math as m
    [math == m, m/inc(2)]
    """
    assert run(src) == [True, 3]


def test_duplicate_imports_reuse_loaded_module_instance():
    env = make_global_env([])
    run_source("import math\nimport math", env)
    assert env.values["math"] is env.loaded_modules["math"]


def test_multiple_aliases_reference_same_loaded_module_instance():
    env = make_global_env([])
    run_source("import math as m1\nimport math as m2", env)
    assert env.values["m1"] is env.values["m2"]
    assert env.values["m1"] is env.loaded_modules["math"]


def test_module_missing_export_raises_clear_error(run):
    with pytest.raises(NameError, match="Module math has no export named missing"):
        run(
            """
            import math
            math/missing
            """
        )


def test_map_named_accessor_and_missing_returns_nil(run):
    src = """
    person = { name: "Matthew", age: 42 }
    [person/name, person/age, person/middle]
    """
    result = run(src)
    assert result[0:2] == ["Matthew", 42]
    assert format_debug(result[2]) == 'none("missing-key", {key: "middle"})'


def test_named_accessor_invalid_lhs_type_errors(run):
    with pytest.raises(TypeError, match="named accessor '/' is only supported for map and module values"):
        run("42/foo")


def test_named_accessor_invalid_rhs_forms_fail_clearly(run):
    with pytest.raises(TypeError, match="requires a bare identifier"):
        run('{name: "m"}/"name"')
    with pytest.raises(TypeError, match="requires a bare identifier"):
        run("{name: \"m\"}/((x) -> x)")


def test_slash_division_behavior_still_works(run):
    assert run("8 / 2") == 4
    assert run("8 / inc(2)") == 8 / 3


def test_map_callable_and_string_projector_regression(run):
    src = """
    person = { name: "Matthew", age: 42 }
    [person("name"), "name"(person)]
    """
    assert run(src) == ["Matthew", "Matthew"]


def test_file_based_module_resolution_relative_to_source(tmp_path):
    module_file = tmp_path / "local_math.genia"
    module_file.write_text(
        """
        pi = 3
        inc(x) = x + 1
        """,
        encoding="utf-8",
    )
    env = make_global_env([])
    result = run_source(
        """
        import local_math as m
        [m/pi, m/inc(2)]
        """,
        env,
        filename=str((tmp_path / "main.genia").resolve()),
    )
    assert result == [3, 3]


def test_duplicate_import_does_not_re_evaluate_module(tmp_path):
    module_file = tmp_path / "counter_mod.genia"
    module_file.write_text(
        """
        _ = ref_update(counter, (n) -> n + 1)
        value = 42
        """,
        encoding="utf-8",
    )
    env = make_global_env([])
    counter = env.get("ref")(0)
    env.set("counter", counter)
    result = run_source(
        """
        import counter_mod
        import counter_mod as c
        [counter_mod/value, c/value]
        """,
        env,
        filename=str((tmp_path / "main.genia").resolve()),
    )
    assert result == [42, 42]
    assert env.get("ref_get")(counter) == 1


def test_import_missing_module_raises_clear_error(run):
    with pytest.raises(FileNotFoundError, match="^Module not found: definitely_not_a_real_module$"):
        run("import definitely_not_a_real_module")


def test_import_module_with_syntax_error_surfaces_cleanly(tmp_path):
    module_file = tmp_path / "bad_syntax.genia"
    module_file.write_text("broken = (", encoding="utf-8")
    env = make_global_env([])
    with pytest.raises(SyntaxError):
        run_source(
            "import bad_syntax",
            env,
            filename=str((tmp_path / "main.genia").resolve()),
        )


def test_import_module_runtime_failure_is_propagated(tmp_path):
    module_file = tmp_path / "bad_eval.genia"
    module_file.write_text("boom = missing_name", encoding="utf-8")
    env = make_global_env([])
    with pytest.raises(NameError, match="Undefined name: missing_name"):
        run_source(
            "import bad_eval",
            env,
            filename=str((tmp_path / "main.genia").resolve()),
        )


def test_named_accessor_invalid_rhs_expression_fails_clearly(run):
    with pytest.raises(TypeError, match="requires a bare identifier"):
        run("{name: \"Alice\"}/(1 + 2)")
