import pytest

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


def test_parse_jsonl_record_success_context_includes_exact_original_line():
    src = r'''
    line = "{\"id\":1,\"name\":\"Ada\"}"
    describe(result) =
      some(record, ctx) -> [record.id, record.name, display(ctx.kind), display(ctx.status), display(ctx.reason), ctx.line] |
      _ -> [quote(unexpected)]

    describe(parse_jsonl_record(line))
    '''
    assert _run(src) == [1, "Ada", "jsonl_record", "parsed", "parsed", '{"id":1,"name":"Ada"}']


def test_parse_jsonl_record_success_context_preserves_surrounding_whitespace():
    src = r'''
    line = "  {\"id\":1}  "
    describe(result) =
      some(record, ctx) -> [record.id, display(ctx.kind), display(ctx.status), display(ctx.reason), ctx.line] |
      _ -> [quote(unexpected)]

    describe(parse_jsonl_record(line))
    '''
    assert _run(src) == [1, "jsonl_record", "parsed", "parsed", '  {"id":1}  ']


def test_parse_jsonl_record_blank_context_includes_exact_original_line():
    src = r'''
    describe(result) =
      none(reason, ctx) -> [reason, display(ctx.kind), display(ctx.status), display(ctx.reason), ctx.line] |
      _ -> [quote(unexpected)]

    [
      describe(parse_jsonl_record("")),
      describe(parse_jsonl_record("   "))
    ]
    '''
    assert _run(src) == [
        ["blank_line", "jsonl_record", "skipped", "blank_line", ""],
        ["blank_line", "jsonl_record", "skipped", "blank_line", "   "],
    ]


def test_parse_jsonl_record_invalid_json_context_includes_exact_original_line():
    src = r'''
    line = "{bad json}"
    describe(result) =
      err(reason, ctx) -> [display(reason), display(ctx.kind), display(ctx.status), display(ctx.reason), ctx.line] |
      _ -> [quote(unexpected)]

    describe(parse_jsonl_record(line))
    '''
    assert _run(src) == [
        "invalid_jsonl_record",
        "jsonl_record",
        "error",
        "invalid_jsonl_record",
        "{bad json}",
    ]


def test_malformed_jsonl_context_survives_validate_each_and_collection():
    src = r'''
    result = collect_validated(
      validate_each(
        [parse_jsonl_record("{\"id\":")],
        (record) -> some(record)
      )
    )

    diagnostic = unwrap_or({}, result.diagnostics |> nth(0))
    ctx = unwrap_or({}, diagnostic.context)
    [
      display(diagnostic.kind),
      display(diagnostic.reason),
      ctx.line,
      ctx.message,
      unwrap_or(-1, ctx |> get("column"))
    ]
    '''
    assert _run(src) == [
        "error",
        "invalid_jsonl_record",
        '{"id":',
        "Expecting value",
        7,
    ]


def test_parse_jsonl_record_non_object_context_includes_exact_original_line():
    src = r'''
    line = "[1,2,3]"
    describe(result) =
      err(reason, ctx) -> [display(reason), display(ctx.kind), display(ctx.status), display(ctx.reason), display(ctx.value_type), ctx.line] |
      _ -> [quote(unexpected)]

    describe(parse_jsonl_record(line))
    '''
    assert _run(src) == [
        "jsonl_record_not_object",
        "jsonl_record",
        "error",
        "jsonl_record_not_object",
        "list",
        "[1,2,3]",
    ]


def test_parse_jsonl_record_non_string_input_remains_runtime_type_misuse():
    with pytest.raises(TypeError, match="parse_jsonl_record expected a string, received int"):
        _run("parse_jsonl_record(42)")
