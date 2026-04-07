import pytest


def test_import_python_root_module_and_call_basic_host_functions(run):
    src = """
    import python
    [[1, 2, 3] |> python/len, 42 |> python/str]
    """
    assert run(src) == [3, "42"]


def test_import_python_json_module_and_convert_host_data(run):
    src = """
    import python.json as pyjson
    obj = pyjson/loads("{\\"name\\": \\"Ada\\", \\"nums\\": [1, 2]}")
    [unwrap_or("?", obj |> get("name")), unwrap_or(-1, obj |> get("nums") |> nth(1))]
    """
    assert run(src) == ["Ada", 2]


def test_host_none_maps_to_genia_none_and_short_circuits_pipeline(run):
    src = """
    import python.json as pyjson
    unwrap_or("fallback", "null" |> pyjson/loads)
    """
    assert run(src) == "fallback"


def test_host_none_short_circuits_later_pipeline_stage(run):
    src = """
    import python.json as pyjson
    seen = ref(0)
    bump(x) = {
      ref_update(seen, (n) -> n + 1)
      x + 1
    }

    result = "null" |> pyjson/loads |> bump
    [none?(result), ref_get(seen)]
    """
    assert run(src) == [True, 0]


def test_some_input_unwraps_before_host_stage_and_host_none_stays_plain_none(run):
    src = """
    import python.json as pyjson
    none?(some("null") |> pyjson/loads)
    """
    assert run(src) is True


def test_python_json_loads_invalid_json_raises_normalized_value_error(run):
    src = """
    import python.json as pyjson
    "{" |> pyjson/loads
    """
    with pytest.raises(ValueError, match=r"^python\.json/loads invalid JSON:"):
        run(src)


def test_genia_map_converts_to_host_json_string(run):
    src = """
    import python.json as pyjson
    pyjson/dumps({ name: "Ada", age: 3 })
    """
    assert run(src) == '{"age": 3, "name": "Ada"}'


def test_file_pipeline_can_open_and_read_via_python_host_module(run, tmp_path):
    path = tmp_path / "demo.txt"
    path.write_text("hello from host interop", encoding="utf-8")
    src = f'''
    import python
    "{path}" |> python/open |> python/read
    '''
    assert run(src) == "hello from host interop"


def test_root_python_module_exposes_json_submodule(run):
    src = """
    import python
    unwrap_or("fallback", "null" |> python/json/loads)
    """
    assert run(src) == "fallback"


def test_host_and_user_defined_pipeline_stages_compose_without_special_cases(run):
    src = """
    import python
    inc(x) = x + 1
    [1, 2, 3] |> python/len |> inc
    """
    assert run(src) == 4


def test_flow_values_remain_distinct_from_host_value_calls(run):
    src = """
    import python
    stdin |> lines |> python/len
    """
    with pytest.raises(TypeError, match="python interop cannot convert flow to a host value"):
        run(src)


def test_disallowed_python_host_module_is_rejected(run):
    with pytest.raises(PermissionError, match="^Host module not allowed: python.os$"):
        run("import python.os")
