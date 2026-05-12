import io

import pytest

from genia import make_global_env, run_source


def _env():
    stdout = io.StringIO()
    stderr = io.StringIO()
    return make_global_env(stdout_stream=stdout, stderr_stream=stderr), stdout, stderr


# --- Alignment: left ---

def test_format_field_align_left():
    env, _, _ = _env()
    result = run_source('format("{name:<5}", {name: "A"})', env)
    assert result == "A    "


def test_format_field_align_left_noop_when_text_already_wide():
    env, _, _ = _env()
    result = run_source('format("{name:<3}", {name: "hello"})', env)
    assert result == "hello"


# --- Alignment: right ---

def test_format_field_align_right():
    env, _, _ = _env()
    result = run_source('format("{name:>5}", {name: "A"})', env)
    assert result == "    A"


# --- Alignment: center ---

def test_format_field_align_center_even_padding():
    env, _, _ = _env()
    result = run_source('format("{name:^5}", {name: "A"})', env)
    assert result == "  A  "


def test_format_field_align_center_odd_padding_extra_space_on_right():
    env, _, _ = _env()
    result = run_source('format("{name:^4}", {name: "A"})', env)
    assert result == " A  "


# --- String precision ---

def test_format_field_string_precision_truncates():
    env, _, _ = _env()
    result = run_source('format("{name:.3}", {name: "Matthew"})', env)
    assert result == "Mat"


def test_format_field_string_precision_zero_returns_empty():
    env, _, _ = _env()
    result = run_source('format("{name:.0}", {name: "Matthew"})', env)
    assert result == ""


def test_format_field_string_precision_noop_when_shorter():
    env, _, _ = _env()
    result = run_source('format("{name:.10}", {name: "hi"})', env)
    assert result == "hi"


# --- Numeric precision ---

def test_format_field_numeric_precision_rounds_float():
    env, _, _ = _env()
    result = run_source('format("{n:.2}", {n: 0.875})', env)
    assert result == "0.88"


def test_format_field_numeric_precision_pads_integer():
    env, _, _ = _env()
    result = run_source('format("{n:.2}", {n: 5})', env)
    assert result == "5.00"


def test_format_field_numeric_precision_zero_no_decimal():
    env, _, _ = _env()
    result = run_source('format("{n:.0}", {n: 12.5})', env)
    assert result == "13"


def test_format_field_numeric_precision_zero_negative_tie():
    env, _, _ = _env()
    result = run_source('format("{n:.0}", {n: -12.5})', env)
    assert result == "-13"


# --- Zero padding ---

def test_format_field_zero_pad_basic():
    env, _, _ = _env()
    result = run_source('format("{n:03}", {n: 5})', env)
    assert result == "005"


def test_format_field_zero_pad_negative_keeps_sign_first():
    env, _, _ = _env()
    result = run_source('format("{n:03}", {n: -5})', env)
    assert result == "-05"


def test_format_field_zero_pad_noop_when_already_wide():
    env, _, _ = _env()
    result = run_source('format("{n:03}", {n: 1234})', env)
    assert result == "1234"


# --- Grouping ---

def test_format_field_grouping_integer():
    env, _, _ = _env()
    result = run_source('format("{n:,}", {n: 1000})', env)
    assert result == "1,000"


def test_format_field_grouping_large_integer():
    env, _, _ = _env()
    result = run_source('format("{n:,}", {n: 1234567})', env)
    assert result == "1,234,567"


def test_format_field_grouping_negative():
    env, _, _ = _env()
    result = run_source('format("{n:,}", {n: -1234567})', env)
    assert result == "-1,234,567"


def test_format_field_grouping_decimal():
    env, _, _ = _env()
    result = run_source('format("{n:,}", {n: 1234.5})', env)
    assert result == "1,234.5"


# --- Positional with spec ---

def test_format_field_positional_with_spec():
    env, _, _ = _env()
    result = run_source('format("{0:<5}", ["A"])', env)
    assert result == "A    "


# --- Format(...) parity ---

def test_format_field_format_value_parity_align():
    env, _, _ = _env()
    raw = run_source('format("{name:<5}", {name: "A"})', env)
    env2, _, _ = _env()
    via_format = run_source('format(Format("{name:<5}"), {name: "A"})', env2)
    assert raw == via_format


def test_format_field_format_value_parity_zero_pad():
    env, _, _ = _env()
    raw = run_source('format("{n:03}", {n: 5})', env)
    env2, _, _ = _env()
    via_format = run_source('format(Format("{n:03}"), {n: 5})', env2)
    assert raw == via_format


def test_format_field_format_value_parity_grouping():
    env, _, _ = _env()
    raw = run_source('format("{n:,}", {n: 1000})', env)
    env2, _, _ = _env()
    via_format = run_source('format(Format("{n:,}"), {n: 1000})', env2)
    assert raw == via_format


# --- Regression: existing no-spec behavior unchanged ---

def test_format_field_no_spec_regression_named():
    env, _, _ = _env()
    result = run_source('format("Hello {name}!", {name: "Alice"})', env)
    assert result == "Hello Alice!"


def test_format_field_no_spec_regression_positional():
    env, _, _ = _env()
    result = run_source('format("{0} {1}", ["hello", "world"])', env)
    assert result == "hello world"


def test_format_field_escaped_braces_with_spec_text():
    env, _, _ = _env()
    result = run_source('format("{{name:<5}}", {name: "A"})', env)
    assert result == "{name:<5}"


# --- Error: invalid or unsupported specs ---

def test_format_field_empty_spec_raises():
    env, _, _ = _env()
    with pytest.raises((ValueError, TypeError), match="format-error"):
        run_source('format("{name:}", {name: "A"})', env)


def test_format_field_bare_width_raises():
    env, _, _ = _env()
    with pytest.raises((ValueError, TypeError), match="format-error"):
        run_source('format("{name:10}", {name: "A"})', env)


def test_format_field_incomplete_align_raises():
    env, _, _ = _env()
    with pytest.raises((ValueError, TypeError), match="format-error"):
        run_source('format("{name:<}", {name: "A"})', env)


def test_format_field_combined_spec_raises():
    env, _, _ = _env()
    with pytest.raises((ValueError, TypeError), match="format-error"):
        run_source('format("{n:05.2}", {n: 3})', env)


def test_format_field_zero_pad_on_string_raises():
    env, _, _ = _env()
    with pytest.raises((ValueError, TypeError), match="format-error"):
        run_source('format("{name:03}", {name: "hello"})', env)


def test_format_field_grouping_on_string_raises():
    env, _, _ = _env()
    with pytest.raises((ValueError, TypeError), match="format-error"):
        run_source('format("{name:,}", {name: "hello"})', env)


def test_format_field_precision_on_list_raises():
    env, _, _ = _env()
    with pytest.raises((ValueError, TypeError), match="format-error"):
        run_source('format("{v:.2}", {v: [1, 2, 3]})', env)


def test_format_field_bool_rejected_as_non_numeric_for_zero_pad():
    env, _, _ = _env()
    with pytest.raises((ValueError, TypeError), match="format-error"):
        run_source('format("{n:03}", {n: true})', env)


def test_format_field_bool_rejected_as_non_numeric_for_grouping():
    env, _, _ = _env()
    with pytest.raises((ValueError, TypeError), match="format-error"):
        run_source('format("{n:,}", {n: true})', env)
