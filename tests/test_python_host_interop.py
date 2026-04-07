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


def test_disallowed_python_host_module_is_rejected(run):
    with pytest.raises(PermissionError, match="^Host module not allowed: python.os$"):
        run("import python.os")
