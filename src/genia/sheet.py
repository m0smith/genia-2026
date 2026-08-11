"""Minimal immutable Sheet runtime value."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .values import GeniaMap, GeniaSymbol, _is_nil_none, _runtime_type_name, symbol


def _sheet_error(message: str) -> TypeError:
    exc = TypeError(message)
    setattr(exc, "_genia_preserve_pipeline_error", True)
    return exc


@dataclass(frozen=True)
class GeniaSheet:
    columns: tuple[tuple[Any, tuple[Any, ...]], ...]
    row_count: int

    @property
    def column_names(self) -> tuple[Any, ...]:
        return tuple(name for name, _ in self.columns)

    @property
    def column_count(self) -> int:
        return len(self.columns)

    @property
    def name_to_values(self) -> dict[Any, tuple[Any, ...]]:
        return {_freeze_column_name(name): values for name, values in self.columns}


def _display_column_name(name: Any) -> str:
    if isinstance(name, GeniaSymbol):
        return name.name
    if isinstance(name, str):
        return name
    return repr(name)


def _freeze_column_name(name: Any) -> Any:
    if name is None or isinstance(name, (bool, int, float, str)):
        return name
    if isinstance(name, GeniaSymbol):
        return ("symbol", name.name)
    if isinstance(name, tuple):
        return ("tuple", tuple(_freeze_column_name(item) for item in name))
    if isinstance(name, list):
        return ("list", tuple(_freeze_column_name(item) for item in name))
    try:
        hash(name)
    except TypeError as exc:
        raise _sheet_error("sheet expected column names to be hashable values") from exc
    return name


def _ensure_sheet(value: Any, operation: str) -> GeniaSheet:
    if not isinstance(value, GeniaSheet):
        raise _sheet_error(f"{operation} expected a Sheet")
    return value


def make_sheet(columns_value: Any) -> GeniaSheet:
    if not isinstance(columns_value, list):
        raise _sheet_error("sheet expected a list of [name, values] column pairs")

    columns: list[tuple[Any, tuple[Any, ...]]] = []
    seen: set[Any] = set()
    expected_length: int | None = None

    for entry in columns_value:
        if not isinstance(entry, list) or len(entry) != 2:
            raise _sheet_error("sheet expected a list of [name, values] column pairs")

        name, values = entry
        frozen_name = _freeze_column_name(name)
        if frozen_name in seen:
            raise _sheet_error("sheet expected unique column names")
        seen.add(frozen_name)

        if not isinstance(values, list):
            raise _sheet_error("sheet expected column values to be lists")

        column_values = tuple(values)
        if expected_length is None:
            expected_length = len(column_values)
        elif len(column_values) != expected_length:
            raise _sheet_error("sheet expected all columns to have equal length")

        columns.append((name, column_values))

    return GeniaSheet(tuple(columns), 0 if expected_length is None else expected_length)


def sheet_shape(sheet_value: Any) -> list[list[Any]]:
    sheet = _ensure_sheet(sheet_value, "shape")
    return [[symbol("rows"), sheet.row_count], [symbol("columns"), sheet.column_count]]


def sheet_columns(sheet_value: Any) -> list[Any]:
    sheet = _ensure_sheet(sheet_value, "columns")
    return list(sheet.column_names)


def sheet_rows(sheet_value: Any) -> list[list[list[Any]]]:
    sheet = _ensure_sheet(sheet_value, "rows")
    return [
        [[name, values[index]] for name, values in sheet.columns]
        for index in range(sheet.row_count)
    ]


def sheet_select(names_value: Any, sheet_value: Any) -> GeniaSheet:
    sheet = _ensure_sheet(sheet_value, "select")
    if not isinstance(names_value, list):
        raise _sheet_error("select expected a list of column names")

    source = sheet.name_to_values
    seen: set[Any] = set()
    selected: list[tuple[Any, tuple[Any, ...]]] = []
    for name in names_value:
        frozen_name = _freeze_column_name(name)
        if frozen_name in seen:
            raise _sheet_error("select expected unique column names")
        seen.add(frozen_name)
        if frozen_name not in source:
            raise _sheet_error(f"select could not find column {_display_column_name(name)}")
        selected.append((name, source[frozen_name]))

    return GeniaSheet(tuple(selected), sheet.row_count)


def sheet_where(predicate: Any, sheet_value: Any, invoke: Callable[[Any, list[Any]], Any]) -> GeniaSheet:
    sheet = _ensure_sheet(sheet_value, "where")
    if not callable(predicate):
        raise _sheet_error("where expected a function")

    kept_indexes: list[int] = []
    row_values = sheet_rows(sheet)
    for index, row in enumerate(row_values):
        result = invoke(predicate, [row])
        if not isinstance(result, bool):
            raise _sheet_error("where expected predicate to return boolean")
        if result:
            kept_indexes.append(index)

    filtered = tuple(
        (name, tuple(values[index] for index in kept_indexes))
        for name, values in sheet.columns
    )
    return GeniaSheet(filtered, len(kept_indexes))


def sheet_derive(name: Any, function: Any, sheet_value: Any, invoke: Callable[[Any, list[Any]], Any]) -> GeniaSheet:
    sheet = _ensure_sheet(sheet_value, "derive")
    if not callable(function):
        raise _sheet_error("derive expected a function")

    frozen_name = _freeze_column_name(name)
    if frozen_name in sheet.name_to_values:
        raise _sheet_error(f"derive expected a new column name; {_display_column_name(name)} already exists")

    derived_values = tuple(invoke(function, [row]) for row in sheet_rows(sheet))
    return GeniaSheet((*sheet.columns, (name, derived_values)), sheet.row_count)


def _csv_scalar_text(value: Any, location: str) -> str:
    if _is_nil_none(value):
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, GeniaSymbol):
        return value.name
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    raise _sheet_error(
        f"render_csv expected CSV scalar {location}; received {_runtime_type_name(value)}"
    )


def _escape_csv_field(text: str) -> str:
    if any(character in text for character in (",", '"', "\n", "\r")):
        return '"' + text.replace('"', '""') + '"'
    return text


def render_sheet_csv(sheet_value: Any) -> str:
    sheet = _ensure_sheet(sheet_value, "render_csv")
    if sheet.column_count == 0:
        return ""

    records = [
        ",".join(
            _escape_csv_field(_csv_scalar_text(name, f"header at column {column_index}"))
            for column_index, (name, _) in enumerate(sheet.columns)
        )
    ]
    for row_index in range(sheet.row_count):
        records.append(
            ",".join(
                _escape_csv_field(
                    _csv_scalar_text(
                        values[row_index],
                        f"cell at row {row_index}, column {column_index}",
                    )
                )
                for column_index, (_, values) in enumerate(sheet.columns)
            )
        )
    return "\n".join(records) + "\n"


def collect_sheet_records(records: list[Any]) -> GeniaSheet:
    if not records:
        return GeniaSheet((), 0)

    first = records[0]
    if not isinstance(first, GeniaMap):
        raise _sheet_error(
            f"collect_sheet expected map records; received {_runtime_type_name(first)} at index 0"
        )

    schema = [raw_key for raw_key, _ in first.items()]
    columns: list[list[Any]] = [[value] for _, value in first.items()]

    for index, record in enumerate(records[1:], start=1):
        if not isinstance(record, GeniaMap):
            raise _sheet_error(
                f"collect_sheet expected map records; received {_runtime_type_name(record)} at index {index}"
            )

        for name in schema:
            if not record.has(name):
                raise _sheet_error(
                    f"collect_sheet expected column {_display_column_name(name)} at row {index}"
                )

        if record.count() != len(schema):
            extra_name = next(raw_key for raw_key, _ in record.items() if not first.has(raw_key))
            raise _sheet_error(
                "collect_sheet expected only column(s) from the first record; "
                f"found unexpected column {_display_column_name(extra_name)} at row {index}"
            )

        for column, name in zip(columns, schema):
            column.append(record.get(name))

    return GeniaSheet(tuple((name, tuple(values)) for name, values in zip(schema, columns)), len(records))
