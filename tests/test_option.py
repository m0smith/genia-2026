import pytest


def test_some_value(run):
    result = run("some(2)")
    assert run("is_some?(some(2))") is True
    assert run("unwrap_or(0, some(2))") == 2
    assert "some(2" in repr(result)


def test_none_value(run):
    assert run("none") == run("none")
    assert run("is_none?(none)") is True




def test_get_none_target_returns_none(run):
    assert run('is_none?(get?("a", none))') is True


def test_get_some_map_target_unwraps_and_queries(run):
    assert run('unwrap_or(0, get?("a", some({a: 3})))') == 3


def test_callable_map_and_string_projector_behavior_unchanged(run):
    src = '[{a:nil}("a"), {a:nil}("b"), {a:nil}("b", 7), "a"({a:nil}), "b"({a:nil}), "b"({a:nil}, 7)]'
    assert run(src) == [None, None, 7, None, None, 7]


def test_get_present_key_returns_some(run):
    assert run('is_some?(get?("a", {a: 1}))') is True
    assert run('unwrap_or(0, get?("a", {a: 1}))') == 1


def test_get_missing_key_returns_none(run):
    assert run('is_none?(get?("b", {a: 1}))') is True
    assert run('unwrap_or(9, get?("b", {a: 1}))') == 9


def test_get_nested_pipeline_success(run):
    src = '\n'.join([
        'record = some({ profile: { name: "Genia" } })',
        'record |> get?("profile") |> get?("name") |> unwrap_or("?")',
    ])
    assert run(src) == "Genia"


def test_get_nested_pipeline_missing(run):
    src = '\n'.join([
        'record = some({ profile: {} })',
        'record |> get?("profile") |> get?("name") |> unwrap_or("?")',
    ])
    assert run(src) == "?"


def test_get_preserves_present_nil_vs_missing(run):
    src = '[is_some?(get?("a", {a:nil})), is_none?(get?("b", {a:nil})), unwrap_or("d", get?("a", {a:nil}))]'
    assert run(src) == [True, True, None]


def test_unwrap_or_some_and_none(run):
    assert run('unwrap_or(5, some(2))') == 2
    assert run('unwrap_or(5, none)') == 5


def test_option_predicates(run):
    assert run('is_some?(some(1))') is True
    assert run('is_some?(none)') is False
    assert run('is_none?(none)') is True
    assert run('is_none?(some(1))') is False


def test_get_unsupported_target_type_error(run):
    with pytest.raises(TypeError, match="get\\? expected a map, some\\(map\\), or none target"):
        run('get?("a", 42)')



def test_get_some_non_map_target_type_error(run):
    with pytest.raises(TypeError, match=r"get\? expected a map, some\(map\), or none target"):
        run('get?("a", some(42))')


def test_option_values_work_with_pattern_matching(run):
    src = '\n'.join([
        'status(opt) =',
        '  none -> "missing" |',
        '  x ? is_some?(x) -> unwrap_or("?", x)',
        '[status(get?("name", {name: "Genia"})), status(none)]',
    ])
    assert run(src) == ["Genia", "missing"]

def test_unwrap_or_requires_option(run):
    with pytest.raises(TypeError, match="unwrap_or expected an option value"):
        run('unwrap_or(0, 42)')
