import io

import pytest

from genia import make_global_env, run_source


def _env():
    stdout = io.StringIO()
    stderr = io.StringIO()
    return make_global_env(stdout_stream=stdout, stderr_stream=stderr), stdout, stderr


def test_format_compose_empty_renders_empty_string():
    env, _, _ = _env()
    result = run_source("Empty = format_compose([])\nformat(Empty, {})", env)
    assert result == ""


def test_format_compose_raw_string_parts_render_in_order():
    env, _, _ = _env()
    result = run_source(
        'Greeting = format_compose(["Hello ", "{name}", "!"])\n'
        'format(Greeting, {name: "Ada"})',
        env,
    )
    assert result == "Hello Ada!"


def test_format_compose_accepts_first_class_format_parts():
    env, _, _ = _env()
    result = run_source(
        'Name = Format("{name}")\n'
        'Location = Format("{city}")\n'
        'Line = format_compose([Name, " - ", Location])\n'
        'format(Line, {name: "Matt", city: "Bountiful"})',
        env,
    )
    assert result == "Matt - Bountiful"


def test_format_compose_nested_formats_render_recursively():
    env, _, _ = _env()
    result = run_source(
        'Cell = Format("{value}")\n'
        'PaddedCell = format_compose(["[", Cell, "]"])\n'
        'Row = format_compose([PaddedCell, " ", PaddedCell])\n'
        'format(Row, {value: "X"})',
        env,
    )
    assert result == "[X] [X]"


def test_format_compose_repeated_placeholders_share_values_map():
    env, _, _ = _env()
    result = run_source(
        'Pair = format_compose(["{x}", " / ", Format("{x}")])\n'
        'format(Pair, {x: "A"})',
        env,
    )
    assert result == "A / A"


def test_format_compose_returns_format_value_for_display():
    env, _, _ = _env()
    result = run_source('display(format_compose(["{x}"]))', env)
    assert result == "<format>"


def test_format_compose_does_not_render_during_composition():
    env, _, _ = _env()
    result = run_source('Later = format_compose([Format("{missing}")])\ndisplay(Later)', env)
    assert result == "<format>"


def test_format_compose_non_list_rejected():
    env, _, _ = _env()
    with pytest.raises(TypeError, match="format_compose expected list of format pieces, received int"):
        run_source("format_compose(42)", env)


def test_format_compose_string_argument_rejected_as_non_list():
    env, _, _ = _env()
    with pytest.raises(TypeError, match="format_compose expected list of format pieces, received string"):
        run_source('format_compose("{x}")', env)


def test_format_compose_invalid_piece_reports_index_and_type():
    env, _, _ = _env()
    with pytest.raises(TypeError, match="format_compose expected string or Format at index 1, received int"):
        run_source('format_compose([Format("{x}"), 42])', env)


def test_format_compose_missing_placeholder_uses_existing_format_error():
    env, _, _ = _env()
    with pytest.raises(ValueError, match="format missing field: missing"):
        run_source('F = format_compose([Format("{missing}")])\nformat(F, {})', env)
