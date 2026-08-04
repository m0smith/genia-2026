import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug


def _run(src: str):
    return run_source(src, make_global_env([]))


def test_parse_csv_row_returns_string_fields_and_success_context():
    src = r'''
    describe(result) =
      some(fields, ctx) -> [fields, display(ctx.kind), display(ctx.status), display(ctx.reason), ctx.line, ctx.field_count] |
      _ -> [quote(unexpected)]

    describe(parse_csv_row("Ada,37,engineer"))
    '''

    assert _run(src) == [["Ada", "37", "engineer"], "csv_row", "parsed", "parsed", "Ada,37,engineer", 3]


def test_parse_csv_row_supports_quotes_empty_fields_and_preserves_whitespace():
    src = r'''
    describe(result) =
      some(fields, ctx) -> [fields, ctx.line, ctx.field_count] |
      _ -> [quote(unexpected)]

    [
      describe(parse_csv_row("\"Ada, Lovelace\",\"said \"\"hi\"\"\",")),
      describe(parse_csv_row(" a ,, c "))
    ]
    '''

    assert _run(src) == [
        [["Ada, Lovelace", 'said "hi"', ""], '"Ada, Lovelace","said ""hi""",', 3],
        [[" a ", "", " c "], " a ,, c ", 3],
    ]


def test_parse_csv_row_blank_line_returns_structured_absence():
    src = r'''
    describe(result) =
      none(reason, ctx) -> [reason, display(ctx.kind), display(ctx.status), display(ctx.reason), ctx.line] |
      _ -> [quote(unexpected)]

    [describe(parse_csv_row("")), describe(parse_csv_row("   "))]
    '''

    assert _run(src) == [
        ["blank_line", "csv_row", "skipped", "blank_line", ""],
        ["blank_line", "csv_row", "skipped", "blank_line", "   "],
    ]


def test_parse_csv_row_malformed_returns_recoverable_error():
    src = r'''
    describe(result) =
      err(reason, ctx) -> [display(reason), display(ctx.kind), display(ctx.status), display(ctx.reason), ctx.line, ctx.message] |
      _ -> [quote(unexpected)]

    describe(parse_csv_row("\"unterminated"))
    '''

    result = _run(src)
    assert result[:5] == ["invalid_csv_row", "csv_row", "error", "invalid_csv_row", '"unterminated']
    assert isinstance(result[5], str)
    assert result[5]


def test_parse_csv_row_headers_return_record_and_context():
    src = r'''
    describe(result) =
      some(record, ctx) -> [record.name, record.age, display(ctx.kind), display(ctx.status), display(ctx.reason), ctx.line, ctx.field_count, ctx.header_count] |
      _ -> [quote(unexpected)]

    describe(parse_csv_row(["name", "age"], "Ada,37"))
    '''

    assert _run(src) == ["Ada", "37", "csv_row", "parsed", "parsed", "Ada,37", 2, 2]


def test_parse_csv_row_header_mismatch_is_recoverable_error():
    src = r'''
    describe(result) =
      err(reason, ctx) -> [display(reason), display(ctx.kind), display(ctx.status), display(ctx.reason), ctx.line, ctx.field_count, ctx.header_count] |
      _ -> [quote(unexpected)]

    describe(parse_csv_row(["name", "age"], "Ada,37,extra"))
    '''

    assert _run(src) == ["csv_header_mismatch", "csv_row", "error", "csv_header_mismatch", "Ada,37,extra", 3, 2]


def test_parse_csv_row_composes_with_collect_validated():
    src = r'''
    result = collect_validated(
      validate_each(
        [
          parse_csv_row(["name", "age"], "Ada,37"),
          parse_csv_row(["name", "age"], "   "),
          parse_csv_row(["name", "age"], "\"unterminated")
        ],
        (record) -> some(record)
      )
    )

    first = unwrap_or({}, result.clean |> nth(0))
    skipped = unwrap_or({}, result.diagnostics |> nth(0))
    failed = unwrap_or({}, result.diagnostics |> nth(1))
    skipped_ctx = unwrap_or({}, skipped.context)
    failed_ctx = unwrap_or({}, failed.context)
    [
      first.name,
      first.age,
      display(skipped.kind),
      display(skipped.reason),
      skipped_ctx.line,
      display(failed.kind),
      display(failed.reason),
      failed_ctx.line
    ]
    '''

    assert _run(src) == [
        "Ada",
        "37",
        "skipped",
        "blank_line",
        "   ",
        "error",
        "invalid_csv_row",
        '"unterminated',
    ]


def test_parse_csv_row_non_string_line_is_runtime_misuse():
    with pytest.raises(TypeError, match="parse_csv_row expected line to be string, received int"):
        _run("parse_csv_row(42)")


def test_parse_csv_row_non_list_headers_is_runtime_misuse():
    with pytest.raises(TypeError, match="parse_csv_row expected headers to be a list, received string"):
        _run('parse_csv_row("name,age", "Ada,37")')


def test_parse_csv_row_invalid_header_item_is_runtime_misuse():
    with pytest.raises(TypeError, match="parse_csv_row expected header at index 1 to be string, received int"):
        _run('parse_csv_row(["name", 7], "Ada,37")')


def test_parse_csv_row_empty_header_is_runtime_misuse():
    with pytest.raises(ValueError, match="parse_csv_row expected header at index 1 to be non-empty"):
        _run('parse_csv_row(["name", ""], "Ada,37")')


def test_parse_csv_row_duplicate_header_is_runtime_misuse():
    with pytest.raises(ValueError, match="parse_csv_row duplicate header: name"):
        _run('parse_csv_row(["name", "name"], "Ada,Ada")')
