"""
Failing tests for issue #298 format-refactor.

These tests define the interface for the extracted format engine helpers:
  - parse_format_template: parses a template string into TemplateLiteral / TemplatePlaceholder parts
  - resolve_format_placeholder: resolves a field name from a Genia value
  - render_format_value: renders a Genia value to its display string

All imports fail with ModuleNotFoundError until src/genia/_format_engine.py is created.
"""

import pytest

from genia._format_engine import (  # type: ignore[import-not-found]
    TemplateLiteral,
    TemplatePlaceholder,
    parse_format_template,
    render_format_value,
    resolve_format_placeholder,
)
from genia.values import GeniaMap


# ---------------------------------------------------------------------------
# parse_format_template — structural parsing
# ---------------------------------------------------------------------------


def test_parse_literal_only():
    parts = parse_format_template("hello world")
    assert parts == [TemplateLiteral("hello world")]


def test_parse_single_named_placeholder():
    parts = parse_format_template("{name}")
    assert parts == [TemplatePlaceholder("name", None)]


def test_parse_mixed_literal_and_placeholder():
    parts = parse_format_template("Hello {name}!")
    assert parts == [
        TemplateLiteral("Hello "),
        TemplatePlaceholder("name", None),
        TemplateLiteral("!"),
    ]


def test_parse_multiple_placeholders():
    parts = parse_format_template("{first} {last}")
    assert parts == [
        TemplatePlaceholder("first", None),
        TemplateLiteral(" "),
        TemplatePlaceholder("last", None),
    ]


def test_parse_positional_placeholder():
    parts = parse_format_template("{0} {1}")
    assert parts == [
        TemplatePlaceholder("0", None),
        TemplateLiteral(" "),
        TemplatePlaceholder("1", None),
    ]


def test_parse_placeholder_with_spec():
    parts = parse_format_template("{name:<5}")
    assert parts == [TemplatePlaceholder("name", "<5")]


def test_parse_empty_template():
    assert parse_format_template("") == []


def test_parse_escaped_left_brace():
    parts = parse_format_template("{{")
    assert parts == [TemplateLiteral("{")]


def test_parse_escaped_right_brace():
    parts = parse_format_template("}}")
    assert parts == [TemplateLiteral("}")]


def test_parse_escaped_braces_mixed():
    parts = parse_format_template("{{{name}}}")
    assert parts == [
        TemplateLiteral("{"),
        TemplatePlaceholder("name", None),
        TemplateLiteral("}"),
    ]


def test_parse_unmatched_left_brace_raises():
    with pytest.raises(ValueError):
        parse_format_template("{unclosed")


def test_parse_unmatched_right_brace_raises():
    with pytest.raises(ValueError):
        parse_format_template("bad}")


def test_parse_empty_placeholder_raises():
    with pytest.raises(ValueError):
        parse_format_template("{}")


# ---------------------------------------------------------------------------
# resolve_format_placeholder — field resolution
# ---------------------------------------------------------------------------


def test_resolve_named_field_from_map():
    m = GeniaMap().put("name", "Alice")
    assert resolve_format_placeholder(m, "name") == "Alice"


def test_resolve_named_field_integer_value():
    m = GeniaMap().put("age", 30)
    assert resolve_format_placeholder(m, "age") == 30


def test_resolve_positional_field_from_list():
    assert resolve_format_placeholder(["a", "b", "c"], "0") == "a"
    assert resolve_format_placeholder(["a", "b", "c"], "2") == "c"


def test_resolve_missing_named_field_raises():
    m = GeniaMap()
    with pytest.raises((ValueError, TypeError)):
        resolve_format_placeholder(m, "missing")


def test_resolve_missing_positional_field_raises():
    with pytest.raises((ValueError, TypeError)):
        resolve_format_placeholder(["a"], "5")


def test_resolve_named_requires_map_raises():
    with pytest.raises(TypeError):
        resolve_format_placeholder(["a", "b"], "name")


def test_resolve_positional_requires_list_raises():
    m = GeniaMap().put("0", "val")
    with pytest.raises(TypeError):
        resolve_format_placeholder(m, "0")


# ---------------------------------------------------------------------------
# render_format_value — value-to-string rendering
# ---------------------------------------------------------------------------


def test_render_string_returns_as_is():
    assert render_format_value("hello") == "hello"


def test_render_integer():
    assert render_format_value(42) == "42"


def test_render_float():
    assert render_format_value(3.14) == "3.14"


def test_render_bool_true():
    assert render_format_value(True) == "true"


def test_render_bool_false():
    assert render_format_value(False) == "false"


def test_render_empty_string():
    assert render_format_value("") == ""
