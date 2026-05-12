import io

import pytest

from genia import make_global_env, run_source


def _env():
    stdout = io.StringIO()
    stderr = io.StringIO()
    return make_global_env(stdout_stream=stdout, stderr_stream=stderr), stdout, stderr


# --- Happy path: construction and use ---

def test_format_value_named_formats_correctly():
    env, _, _ = _env()
    result = run_source('BoardRow = Format("{a} {b} {c}")\nformat(BoardRow, {a: "X", b: "O", c: " "})', env)
    assert result == "X O  "


def test_format_value_inline_formats_correctly():
    env, _, _ = _env()
    result = run_source('format(Format("{a} {b} {c}"), {a: "X", b: "O", c: " "})', env)
    assert result == "X O  "


def test_format_value_matches_raw_string_output():
    env, _, _ = _env()
    raw = run_source('format("{a} {b} {c}", {a: "X", b: "O", c: " "})', env)
    env2, _, _ = _env()
    via_format = run_source('format(Format("{a} {b} {c}"), {a: "X", b: "O", c: " "})', env2)
    assert raw == via_format


def test_format_value_is_first_class_assignable():
    env, _, _ = _env()
    result = run_source('f = Format("{x}")\nformat(f, {x: "hello"})', env)
    assert result == "hello"


def test_format_value_empty_template():
    env, _, _ = _env()
    result = run_source('format(Format(""), {})', env)
    assert result == ""


def test_format_value_no_placeholders():
    env, _, _ = _env()
    result = run_source('format(Format("hello world"), {})', env)
    assert result == "hello world"


def test_format_value_positional_placeholders():
    env, _, _ = _env()
    result = run_source('format(Format("{0} {1}"), ["hello", "world"])', env)
    assert result == "hello world"


# --- Display and debug rendering ---

def test_format_value_display_returns_format_tag():
    env, _, _ = _env()
    result = run_source('display(Format("{a}"))', env)
    assert result == "<format>"


def test_format_value_debug_repr_returns_format_tag():
    env, _, _ = _env()
    result = run_source('debug_repr(Format("{a}"))', env)
    assert result == "<format>"


def test_format_value_display_does_not_expose_template():
    env, _, _ = _env()
    result = run_source('display(Format("{secret_key}"))', env)
    assert "{secret_key}" not in result


# --- Error cases ---

def test_format_constructor_rejects_non_string():
    env, _, _ = _env()
    with pytest.raises(TypeError, match="Format expected a string template"):
        run_source("Format(123)", env)


def test_format_rejects_non_string_non_format_first_arg():
    env, _, _ = _env()
    with pytest.raises(TypeError, match="format expected a string template or Format value"):
        run_source("format(123, {})", env)


def test_format_constructor_rejects_list():
    env, _, _ = _env()
    with pytest.raises(TypeError, match="Format expected a string template"):
        run_source('Format(["a", "b"])', env)


# --- Backward compatibility ---

def test_raw_string_format_unchanged():
    env, _, _ = _env()
    result = run_source('format("Hello {name}!", {name: "Alice"})', env)
    assert result == "Hello Alice!"
