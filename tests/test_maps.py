import pytest


def test_map_new_creates_empty_map(run):
    assert run("map_count(map_new())") == 0


def test_map_get_missing_returns_nil(run):
    assert run('map_get(map_new(), "missing")') is None


def test_map_put_returns_new_map_without_mutating_original(run):
    src = '''
    m0 = map_new()
    m1 = map_put(m0, "k", 10)
    [map_count(m0), map_count(m1), map_get(m0, "k"), map_get(m1, "k")]
    '''
    assert run(src) == [0, 1, None, 10]


def test_map_remove_returns_new_map_without_mutating_original(run):
    src = '''
    m0 = map_put(map_new(), "k", 10)
    m1 = map_remove(m0, "k")
    [map_has?(m0, "k"), map_has?(m1, "k"), map_count(m0), map_count(m1)]
    '''
    assert run(src) == [True, False, 1, 0]


def test_map_has_works_for_present_and_absent_keys(run):
    src = '''
    m = map_put(map_new(), "present", 1)
    [map_has?(m, "present"), map_has?(m, "absent")]
    '''
    assert run(src) == [True, False]


def test_map_count_tracks_entries(run):
    src = '''
    m0 = map_new()
    m1 = map_put(m0, "a", 1)
    m2 = map_put(m1, "b", 2)
    m3 = map_put(m2, "a", 3)
    [map_count(m0), map_count(m1), map_count(m2), map_count(m3)]
    '''
    assert run(src) == [0, 1, 2, 2]


def test_map_list_and_tuple_keys_follow_stable_value_semantics(run):
    src = '''
    m0 = map_new()
    m1 = map_put(m0, [1, 2], "list")
    [map_get(m1, [1, 2]), map_has?(m1, [1, 2]), map_has?(m1, [2, 1])]
    '''
    assert run(src) == ["list", True, False]


def test_map_tuple_keys_runtime_behavior():
    from genia import make_global_env, run_source

    env = make_global_env([])
    map_value = run_source("map_new()", env)
    env.set("m", map_value)
    env.set("k", ("tuple", 1))
    run_source('m2 = map_put(m, k, "value")', env)
    assert run_source("map_get(m2, k)", env) == "value"
    assert run_source("map_has?(m2, k)", env) is True


def test_map_invalid_types_raise_clear_type_errors(run):
    with pytest.raises(TypeError, match="map_get expected a map as first argument"):
        run('map_get(1, "k")')

    with pytest.raises(TypeError, match="map_put expected a map as first argument"):
        run('map_put(1, "k", 2)')

    with pytest.raises(TypeError, match="map_remove expected a map as first argument"):
        run('map_remove(1, "k")')

    with pytest.raises(TypeError, match="map_has\\? expected a map as first argument"):
        run('map_has?(1, "k")')

    with pytest.raises(TypeError, match="map_count expected a map as first argument"):
        run("map_count(1)")

    with pytest.raises(TypeError, match="map key type is not supported"):
        run("map_put(map_new(), ref(1), 2)")

    with pytest.raises(TypeError, match="map_new expected 0 args, got 1"):
        run("map_new(1)")
