"""Minimal immutable Sheet runtime value."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .numeric_runtime import GeniaDecimal, GeniaRational
from .values import GeniaMap, GeniaSymbol, _is_nil_none, _runtime_type_name, symbol
from .configuration import contains_declassification_authority, contains_protected


def _sheet_error(message: str) -> TypeError:
    """Construct a TypeError marked to retain its diagnostic through pipeline handling.

    Return rather than raise it; callers supply already-safe diagnostic text.
    """
    exc = TypeError(message)
    setattr(exc, "_genia_preserve_pipeline_error", True)
    return exc


@dataclass(frozen=True)
class GeniaSheet:
    """Frozen Python container for ordered columns, tuple cell sequences and row count.

    LANGUAGE CONTRACT: Sheet transformations return new values without changing
    source rows/columns; stored values and their ordinary identity are preserved.
    PYTHON REFERENCE HOST: freezing is shallow. Cells/names remain references;
    direct host construction does not validate names, lengths or row_count.
    Callers must supply validated column tuples and a consistent nonnegative count.
    Use public construction helpers rather than treating this as a validating API.
    """
    columns: tuple[tuple[Any, tuple[Any, ...]], ...]
    row_count: int

    @property
    def column_names(self) -> tuple[Any, ...]:
        """Return a fresh tuple of exact column-name references in stored order."""
        return tuple(name for name, _ in self.columns)

    @property
    def column_count(self) -> int:
        """Return stored column count without validating cell lengths or row_count."""
        return len(self.columns)

    @property
    def name_to_values(self) -> dict[Any, tuple[Any, ...]]:
        """Build a fresh canonical-name dictionary sharing stored value tuples.

        Use Genia map-key identity, not host raw-name equality; canonicalization errors
        propagate. Valid Sheets have unique names; direct invalid storage is not repaired.
        """
        return {_freeze_column_name(name): values for name, values in self.columns}


def _display_column_name(name: Any) -> str:
    """Render symbols by name and strings verbatim for existing column diagnostics.

    Other values use repr; callers first validate names through the legal-key boundary.
    """
    if isinstance(name, GeniaSymbol):
        return name.name
    if isinstance(name, str):
        return name
    return repr(name)


_canonical_map_key = None


def _freeze_column_name(name: Any) -> Any:
    """Sheet column-name identity, owned by the canonical equality boundary.

    R18 (#794): two column names denote the same column exactly when they are
    Genia-equal, so this delegates to the same canonicalizer map keys use.
    Column-name identity and map-key identity ask the same question — do these
    two values denote the same slot? — and the contract requires both to be `==`.

    Before R18 this was a second, hand-rolled relation that returned raw host
    values for booleans, integers, floats and strings, which let a host container
    merge ``true`` with ``1`` and rejected such a Sheet as having duplicate
    column names. It also ended with an "anything hashable" fallback, which would
    reintroduce a host-defined relation.

    The protected check stays ahead of the delegation so Sheets keep their own
    message; the canonicalizer rejects protected values too, so the guarantee is
    not weakened either way.

    The import is function-local because ``equality`` imports this module; the
    resolved function is cached after the first call.
    """
    global _canonical_map_key
    if name.__class__.__name__ == "GeniaProtected":
        raise TypeError("protected values cannot be Sheet column names")
    if _canonical_map_key is None:
        from .equality import canonical_map_key

        _canonical_map_key = canonical_map_key
    try:
        return _canonical_map_key(name)
    except TypeError as exc:
        raise _sheet_error(f"sheet expected a legal column name: {exc}") from exc


def _ensure_sheet(value: Any, operation: str) -> GeniaSheet:
    """Return the same Sheet instance or raise marked operation-specific TypeError.

    Check host type only; do not revalidate direct-host column storage.
    """
    if not isinstance(value, GeniaSheet):
        raise _sheet_error(f"{operation} expected a Sheet")
    return value


def make_sheet(columns_value: Any) -> GeniaSheet:
    """Validate a list of [name, values] pairs and build a new ordered Sheet.

    Reject recursively detected declassification authority before shape validation.
    Names use legal Genia map-key identity and must be unique; values must be lists
    of equal length. Raise marked TypeError on malformed shape, duplicates or lengths;
    name-key failures follow _freeze_column_name, including protected-name rejection.
    Copy outer column/value lists into tuples while retaining exact name/cell references;
    protected cells remain opaque stored leaves. Empty columns yield zero rows/columns.
    No cell coercion, callback, IO or mutation of input containers occurs.
    """
    if contains_declassification_authority(columns_value):
        raise _sheet_error("declassification authority cannot be stored in a Sheet")
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
    """Return fresh [[rows symbol, row_count], [columns symbol, column_count]] lists.

    Require a Sheet; misuse raises marked TypeError without consuming or changing it.
    """
    sheet = _ensure_sheet(sheet_value, "shape")
    return [[symbol("rows"), sheet.row_count], [symbol("columns"), sheet.column_count]]


def sheet_columns(sheet_value: Any) -> list[Any]:
    """Return a fresh list of exact names in Sheet column order; non-Sheet raises TypeError."""
    sheet = _ensure_sheet(sheet_value, "columns")
    return list(sheet.column_names)


def sheet_rows(sheet_value: Any) -> list[list[list[Any]]]:
    """Materialize fresh ordered row lists containing fresh [name, cell] pairs.

    Require a Sheet; retain exact name/cell references and row/column order.
    Zero-column storage yields one empty row per retained row_count. No coercion or IO.
    """
    sheet = _ensure_sheet(sheet_value, "rows")
    return [
        [[name, values[index]] for name, values in sheet.columns]
        for index in range(sheet.row_count)
    ]


def row_get_value(row_value: Any, column_name: Any) -> Any:
    """Return the first Genia-equal named cell from a list of [name, value] pairs.

    Validate row type and target name, then entries only until the first match.
    A later malformed/duplicate entry after success is not inspected. Name
    canonicalization failures propagate; malformed visited entry or missing name
    raises Sheet TypeError with existing index/name diagnostic. Return exact cell
    without copying, unwrapping Outcomes or requiring a Sheet.
    """
    if not isinstance(row_value, list):
        raise _sheet_error("row_get expected a row (list of [name, value] pairs)")

    target = _freeze_column_name(column_name)
    for index, entry in enumerate(row_value):
        if not isinstance(entry, list) or len(entry) != 2:
            raise _sheet_error(
                "row_get expected a row (list of [name, value] pairs); "
                f"malformed entry at index {index}"
            )
        name, value = entry
        if _freeze_column_name(name) == target:
            return value

    raise _sheet_error(f"row_get could not find column {_display_column_name(column_name)}")


def sheet_select(names_value: Any, sheet_value: Any) -> GeniaSheet:
    """Build a Sheet sharing requested columns in requested name order.

    Require Sheet and list of unique legal names; canonical identity resolves each
    lookup and missing/duplicate names raise Sheet TypeError. Retain requested name
    references and original value tuples/count; selecting [] preserves row_count
    even though the new Sheet has zero columns. Source is not mutated.
    """
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
    """Eagerly filter rows in order using one invocation per row and a strict boolean.

    Require Sheet/callable predicate; invoke receives (predicate, [fresh row]).
    Non-bool result raises marked TypeError; callback failures propagate and no
    partial Sheet is returned, though callback effects are not rolled back.
    Return new column tuples with exact kept cells and original names/order.
    No rows means no callbacks; source storage is not mutated.
    """
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
    """Eagerly append one new legal-name column from one callback invocation per row.

    Require Sheet/callable and a name absent under Genia column identity, validating
    these before callbacks. invoke receives (function, [fresh row]); store returned
    values exactly, including Outcomes, without coercion or unwrapping. Existing
    column tuples/count are shared unchanged. Callback failures propagate with no
    partial Sheet; callback effects are not rolled back. No rows means no calls.
    This helper does not re-run make_sheet validation over callback results.
    """
    sheet = _ensure_sheet(sheet_value, "derive")
    if not callable(function):
        raise _sheet_error("derive expected a function")

    frozen_name = _freeze_column_name(name)
    if frozen_name in sheet.name_to_values:
        raise _sheet_error(f"derive expected a new column name; {_display_column_name(name)} already exists")

    derived_values = tuple(invoke(function, [row]) for row in sheet_rows(sheet))
    return GeniaSheet((*sheet.columns, (name, derived_values)), sheet.row_count)


def _csv_scalar_text(value: Any, location: str) -> str:
    """Render one CSV scalar, rejecting recursively detected protection first.

    Nil absence renders empty, strings retain content, symbols use names and booleans
    use true/false. Integer/host float/GeniaDecimal/GeniaRational use existing str
    rendering; this is report formatting, not a new numeric interchange boundary.
    Composite/non-nil Outcome/other values raise marked TypeError with supplied
    structural location and governed runtime type, excluding payload text. No IO.
    """
    if contains_protected(value):
        raise _sheet_error(f"protected-value: render-csv {location}")
    if _is_nil_none(value):
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, GeniaSymbol):
        return value.name
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float, GeniaDecimal, GeniaRational)):
        return str(value)
    raise _sheet_error(
        f"render_csv expected CSV scalar {location}; received {_runtime_type_name(value)}"
    )


def _escape_csv_field(text: str) -> str:
    """Quote fields containing comma, double quote, CR or LF and double embedded quotes.

    Caller supplies text; otherwise preserve every character, including whitespace.
    """
    if any(character in text for character in (",", '"', "\n", "\r")):
        return '"' + text.replace('"', '""') + '"'
    return text


def render_sheet_csv(sheet_value: Any) -> str:
    """Return CSV report text in stored column/row order without output or mutation.

    Require Sheet. Zero columns return empty text, regardless of row_count. Otherwise
    render one header plus every row, comma-separated with LF after every record.
    Use _csv_scalar_text/escaping, retaining whitespace and rejecting protected or
    unsupported headers/cells with zero-based structural locations. Raise TypeError
    without returning partial text; no output sink or implicit Outcome unwrapping.
    """
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
    """Build a Sheet from an already-materialized list of homogeneous GeniaMap records.

    Caller owns Seq validation/consumption and any boundary guards before this helper;
    this function neither consumes Flow nor delegates to make_sheet. Empty list
    yields zero rows/columns. First map key order/raw keys define columns; later maps
    must have the same key set, ignoring their order. Preserve cell references and
    Outcome field values without coercion/unwrapping; copy structural storage to tuples.
    Non-map item, missing key or extra key raises marked TypeError with index/name
    and no partial result. A top-level Outcome is not a map. No input mutation,
    column union/padding/defaults or independent authority scan occurs here.
    """
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
