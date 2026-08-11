from __future__ import annotations

import pytest

from genia.utf8 import format_debug


def test_sheet_shape_columns_and_rows_are_deterministic(run):
    result = run(
        """
        people = sheet([
          [quote(name), ["Ann", "Bob", "Cara"]],
          [quote(age), [30, 22, 41]]
        ])
        [shape(people), columns(people), rows(people)]
        """
    )

    assert format_debug(result) == (
        '[[[rows, 3], [columns, 2]], [name, age], '
        '[[[name, "Ann"], [age, 30]], [[name, "Bob"], [age, 22]], [[name, "Cara"], [age, 41]]]]'
    )


def test_empty_sheet_has_zero_shape_and_empty_rows(run):
    result = run(
        """
        empty = sheet([])
        selected = empty |> select([])
        [shape(empty), columns(empty), rows(empty), shape(selected)]
        """
    )

    assert format_debug(result) == "[[[rows, 0], [columns, 0]], [], [], [[rows, 0], [columns, 0]]]"


def test_select_reorders_columns_and_preserves_original_sheet(run):
    result = run(
        """
        people = sheet([
          [quote(name), ["Ann", "Bob"]],
          [quote(age), [30, 22]],
          [quote(city), ["Provo", "Ogden"]]
        ])
        selected = people |> select([quote(age), quote(name)])
        [columns(selected), rows(selected), shape(people)]
        """
    )

    assert format_debug(result) == (
        '[[age, name], [[[age, 30], [name, "Ann"]], [[age, 22], [name, "Bob"]]], '
        '[[rows, 2], [columns, 3]]]'
    )


def test_where_filters_rows_and_preserves_original_sheet(run):
    result = run(
        """
        people = sheet([
          [quote(name), ["Ann", "Bob"]],
          [quote(age), [30, 22]]
        ])
        kept = people |> where((row) -> true)
        dropped = people |> where((row) -> false)
        [rows(kept), shape(dropped), shape(people)]
        """
    )

    assert format_debug(result) == (
        '[[[[name, "Ann"], [age, 30]], [[name, "Bob"], [age, 22]]], '
        '[[rows, 0], [columns, 2]], [[rows, 2], [columns, 2]]]'
    )


def test_derive_appends_column_stores_outcomes_and_preserves_original_sheet(run):
    result = run(
        """
        people = sheet([
          [quote(name), ["Ann", "Bob"]],
          [quote(age), [30, 22]]
        ])
        derived = people |> derive(quote(status), (row) -> some("ok"))
        [rows(derived), shape(people)]
        """
    )

    assert format_debug(result) == (
        '[[[[name, "Ann"], [age, 30], [status, some("ok")]], '
        '[[name, "Bob"], [age, 22], [status, some("ok")]]], [[rows, 2], [columns, 2]]]'
    )


def test_row_get_returns_paired_value_directly_and_via_where_derive(run):
    result = run(
        """
        people = sheet([
          [quote(name), ["Ann", "Bob", "Cara"]],
          [quote(age), [30, 22, 41]]
        ])
        older = people
          |> where((row) -> row_get(row, quote(age)) >= 30)
          |> derive(quote(age_next), (row) -> row_get(row, quote(age)) + 1)
        [row_get([[quote(age), 30]], quote(age)), rows(older)]
        """
    )

    assert format_debug(result) == (
        '[30, [[[name, "Ann"], [age, 30], [age_next, 31]], '
        '[[name, "Cara"], [age, 41], [age_next, 42]]]]'
    )


def test_row_get_matches_string_keyed_rows_from_collect_sheet(run):
    result = run(
        """
        report = collect_sheet([{name: "Ann", age: 30}])
        derived = report |> derive("age_next", (row) -> row_get(row, "age") + 1)
        rows(derived)
        """
    )

    assert format_debug(result) == '[[["name", "Ann"], ["age", 30], ["age_next", 31]]]'


def test_row_get_first_match_wins_on_duplicate_names(run):
    result = run(
        """
        row_get([[quote(age), 1], [quote(age), 2]], quote(age))
        """
    )

    assert format_debug(result) == "1"


def test_row_get_does_not_mutate_row_or_source_sheet(run):
    result = run(
        """
        people = sheet([[quote(age), [30]]])
        row = [[quote(age), 30]]
        value = row_get(row, quote(age))
        [value, row, rows(people)]
        """
    )

    assert format_debug(result) == '[30, [[age, 30]], [[[age, 30]]]]'


@pytest.mark.parametrize(
    ("source", "message"),
    [
        (
            """
            sheet([
              [quote(name), ["Ann", "Bob"]],
              [quote(age), [30]]
            ])
            """,
            "sheet expected all columns to have equal length",
        ),
        (
            """
            sheet([
              [quote(name), ["Ann"]],
              [quote(name), ["Bob"]]
            ])
            """,
            "sheet expected unique column names",
        ),
        (
            """
            people = sheet([[quote(name), ["Ann"]]])
            people |> select([quote(age)])
            """,
            "select could not find column age",
        ),
        (
            """
            people = sheet([[quote(name), ["Ann"]]])
            people |> derive(quote(name), (row) -> "Ada")
            """,
            "derive expected a new column name; name already exists",
        ),
        (
            'row_get("not-a-row", quote(age))',
            r"row_get expected a row \(list of \[name, value\] pairs\)",
        ),
        (
            "row_get([quote(age)], quote(age))",
            r"row_get expected a row \(list of \[name, value\] pairs\); malformed entry at index 0",
        ),
        (
            "row_get([[quote(age), 30]], quote(city))",
            "row_get could not find column city",
        ),
    ],
)
def test_sheet_errors_are_clear(run, source, message):
    with pytest.raises((RuntimeError, TypeError), match=message):
        run(source)


def test_collect_sheet_empty_input_has_zero_shape(run):
    result = run(
        """
        report = collect_sheet([])
        [shape(report), columns(report), rows(report)]
        """
    )

    assert format_debug(result) == "[[[rows, 0], [columns, 0]], [], []]"


def test_collect_sheet_builds_columns_from_first_record_order(run):
    result = run(
        """
        report = collect_sheet([
          {name: "Ann", age: 30},
          {name: "Bob", age: 22}
        ])
        [shape(report), columns(report), rows(report)]
        """
    )

    assert format_debug(result) == (
        '[[[rows, 2], [columns, 2]], ["name", "age"], '
        '[[["name", "Ann"], ["age", 30]], [["name", "Bob"], ["age", 22]]]]'
    )


def test_collect_sheet_ignores_later_record_key_order(run):
    result = run(
        """
        report = collect_sheet([
          {name: "Ann", age: 30},
          {age: 22, name: "Bob"}
        ])
        rows(report)
        """
    )

    assert format_debug(result) == (
        '[[["name", "Ann"], ["age", 30]], [["name", "Bob"], ["age", 22]]]'
    )


def test_collect_sheet_accepts_finite_flow_same_as_list(run):
    result = run(
        """
        next(n) = n + 1
        record(n) = (
          0 -> {name: "Ann", age: 30} |
          1 -> {name: "Bob", age: 22}
        )
        source = evolve(0, next) |> take(2) |> map(record)
        rows(collect_sheet(source))
        """
    )

    assert format_debug(result) == (
        '[[["name", "Ann"], ["age", 30]], [["name", "Bob"], ["age", 22]]]'
    )


def test_collect_sheet_stores_outcome_field_values_as_ordinary_cells(run):
    result = run(
        """
        report = collect_sheet([{name: "Ann", status: some("ok")}])
        rows(report)
        """
    )

    assert format_debug(result) == '[[["name", "Ann"], ["status", some("ok")]]]'


def test_collect_sheet_does_not_mutate_source_records(run):
    result = run(
        """
        records = [{name: "Ann"}, {name: "Bob"}]
        report = collect_sheet(records)
        [records, rows(report)]
        """
    )

    assert format_debug(result) == (
        '[[{name: "Ann"}, {name: "Bob"}], [[["name", "Ann"]], [["name", "Bob"]]]]'
    )


@pytest.mark.parametrize(
    ("source", "message"),
    [
        (
            'collect_sheet("not-a-seq")',
            r"collect_sheet expected a Seq-compatible value \(list or Flow\); received",
        ),
        (
            'collect_sheet([{name: "Ann"}, "not-a-map"])',
            "collect_sheet expected map records; received .* at index 1",
        ),
        (
            'collect_sheet([some({name: "Ann"})])',
            "collect_sheet expected map records; received .* at index 0",
        ),
        (
            'collect_sheet([{name: "Ann", age: 30}, {name: "Bob"}])',
            "collect_sheet expected column age at row 1",
        ),
        (
            'collect_sheet([{name: "Ann"}, {name: "Bob", age: 22}])',
            "collect_sheet expected only column.*found unexpected column age at row 1",
        ),
    ],
)
def test_collect_sheet_errors_are_clear(run, source, message):
    with pytest.raises((RuntimeError, TypeError), match=message):
        run(source)


def test_render_csv_empty_and_header_only_sheets(run):
    result = run(
        """
        [
          render_csv(sheet([])),
          render_csv(sheet([
            [quote(name), []],
            [quote(age), []]
          ]))
        ]
        """
    )

    assert result == ["", "name,age\n"]


def test_render_csv_preserves_sheet_order_and_escapes_csv_fields(run):
    result = run(
        '''
        report = sheet([
          [quote(name), ["Ann", "Bob"]],
          [quote(note), ["hello, world", "said \\"hi\\""]],
          [quote(detail), ["line1\\nline2", "  spaced  "]]
        ])
        render_csv(report)
        '''
    )

    assert result == (
        'name,note,detail\n'
        'Ann,"hello, world","line1\nline2"\n'
        'Bob,"said ""hi""",  spaced  \n'
    )


def test_render_csv_converts_supported_scalar_cells(run):
    result = run(
        """
        report = sheet([
          ["kind", [quote(ok)]],
          ["count", [7]],
          ["ratio", [1.5]],
          ["active", [true]],
          ["missing", [nil]]
        ])
        render_csv(report)
        """
    )

    assert result == "kind,count,ratio,active,missing\nok,7,1.5,true,\n"


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ('render_csv("not-a-sheet")', "render_csv expected a Sheet"),
        (
            'render_csv(sheet([[{name: "header"}, ["value"]]]))',
            "render_csv expected CSV scalar header at column 0; received map",
        ),
        (
            'render_csv(sheet([[quote(value), [[1, 2]]]]))',
            "render_csv expected CSV scalar cell at row 0, column 0; received list",
        ),
        (
            'render_csv(sheet([[quote(value), [some("ok")]]]))',
            "render_csv expected CSV scalar cell at row 0, column 0; received some\\(string\\)",
        ),
    ],
)
def test_render_csv_errors_are_clear(run, source, message):
    with pytest.raises((RuntimeError, TypeError), match=message):
        run(source)
