import pytest

from genia import make_global_env, run_source


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
    assert run(src) == ["Matthew", 42, None]


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
