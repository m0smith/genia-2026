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
    ],
)
def test_sheet_errors_are_clear(run, source, message):
    with pytest.raises((RuntimeError, TypeError), match=message):
        run(source)
