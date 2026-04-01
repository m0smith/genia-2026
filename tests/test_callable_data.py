import pytest


def test_map_callable_lookup_and_default(run):
    src = '''
    person = { name: "Matthew", age: 42 }
    [person("name"), person("missing"), person("missing", "?")]
    '''
    assert run(src) == ["Matthew", None, "?"]


def test_string_projector_lookup_and_default(run):
    src = '''
    person = { name: "Matthew", age: 42 }
    ["name"(person), "missing"(person), "missing"(person, "?")]
    '''
    assert run(src) == ["Matthew", None, "?"]


def test_map_callable_wrong_arity_raises_clear_error(run):
    with pytest.raises(TypeError, match="map callable expected 1 or 2 args, got 0"):
        run("{}()")

    with pytest.raises(TypeError, match="map callable expected 1 or 2 args, got 3"):
        run('{}("a", "b", "c")')


def test_string_projector_wrong_arity_raises_clear_error(run):
    with pytest.raises(TypeError, match="string projector expected 1 or 2 args, got 0"):
        run('"name"()')

    with pytest.raises(TypeError, match="string projector expected 1 or 2 args, got 3"):
        run('"name"({}, "x", "y")')


def test_string_projector_requires_map_target(run):
    with pytest.raises(TypeError, match="string projector expected a map as first argument"):
        run('"name"(42)')


def test_ordinary_non_callable_values_still_fail_normally(run):
    with pytest.raises(TypeError):
        run("1(2)")


def test_ordinary_function_calls_still_work(run):
    src = """
    inc(x) = x + 1
    inc(4)
    """
    assert run(src) == 5
