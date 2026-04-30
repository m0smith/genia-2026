from genia import make_global_env, run_source


def _run(src: str):
    return run_source(src, make_global_env([]))


def test_json_parse_valid_object_list_and_primitives():
    src = r'''
    parsed = json_parse("{\"name\":\"genia\",\"enabled\":true,\"n\":7,\"items\":[1,2,3]}")
    [
      unwrap_or("?", parsed |> get("name")),
      unwrap_or(false, parsed |> get("enabled")),
      unwrap_or(0, parsed |> get("n")),
      unwrap_or([], parsed |> get("items"))
    ]
    '''
    assert _run(src) == ["genia", True, 7, [1, 2, 3]]


def test_json_parse_invalid_returns_none_with_structured_context():
    src = r'''
    parsed = json_parse("{\"x\":")
    [
      none?(parsed),
      unwrap_or("?", absence_reason(parsed)),
      unwrap_or("?", absence_context(parsed) |> then_get("source")),
      unwrap_or(-1, absence_context(parsed) |> then_get("line")),
      unwrap_or(-1, absence_context(parsed) |> then_get("column"))
    ]
    '''
    result = _run(src)
    assert result[0] is True
    assert result[1] == "json-parse-error"
    assert result[2] == "json_parse"
    assert result[3] == 1
    assert result[4] > 0


def test_json_parse_nested_structures_integrate_with_map_semantics():
    src = r'''
    parsed = json_parse("{\"outer\":{\"inner\":{\"n\":3}},\"rows\":[{\"id\":1},{\"id\":2}]}")
    [
      unwrap_or(0, parsed |> get("outer") |> then_get("inner") |> then_get("n")),
      unwrap_or(0, parsed |> get("rows") |> then_nth(1) |> then_get("id"))
    ]
    '''
    assert _run(src) == [3, 2]


def test_json_stringify_renders_deterministic_pretty_json():
    src = r'''
    json_stringify({ b: 2, a: 1 })
    '''
    assert _run(src) == '{\n  "a": 1,\n  "b": 2\n}'
