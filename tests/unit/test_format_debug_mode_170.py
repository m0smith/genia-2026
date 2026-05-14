import io

import pytest

from genia import make_global_env, run_source


def _env():
    stdout = io.StringIO()
    stderr = io.StringIO()
    return make_global_env(stdout_stream=stdout, stderr_stream=stderr), stdout, stderr


def test_format_debug_mode_distinguishes_display_and_debug_strings():
    env, _, _ = _env()
    result = run_source('format("display={x} debug={x:?}", {x: "hi"})', env)
    assert result == 'display=hi debug="hi"'


def test_format_debug_mode_uses_debug_repr_for_compound_values():
    env, _, _ = _env()
    result = run_source(
        'format("{x:?}", {x: {name: "Ada", scores: [1, some("ok"), none("missing-score")]}})',
        env,
    )
    assert result == '{name: "Ada", scores: [1, some("ok"), none("missing-score")]}'


def test_format_debug_mode_covers_primitives_options_and_format_values():
    env, _, _ = _env()
    result = run_source(
        'format("n={n:?} b={b:?} missing={missing:?} opt={opt:?} fmt={fmt:?}", '
        '{n: 42, b: true, missing: none, opt: some("Ada"), fmt: Format("{a}")})',
        env,
    )
    assert result == 'n=42 b=true missing=none("nil") opt=some("Ada") fmt=<format>'


def test_format_debug_mode_supports_positional_placeholders():
    env, _, _ = _env()
    result = run_source('format("{0} {0:?}", ["hi"])', env)
    assert result == 'hi "hi"'


def test_format_debug_mode_raw_string_and_format_value_are_equivalent():
    env, _, _ = _env()
    raw = run_source('format("{x:?}", {x: "hi"})', env)
    env2, _, _ = _env()
    via_format = run_source('format(Format("{x:?}"), {x: "hi"})', env2)
    assert raw == via_format == '"hi"'


def test_format_debug_mode_keeps_escaped_braces_behavior():
    env, _, _ = _env()
    result = run_source('format("{{x}} {x:?}", {x: "hi"})', env)
    assert result == '{x} "hi"'


def test_format_no_spec_still_uses_display_representation():
    env, _, _ = _env()
    result = run_source('format("{x}", {x: "hi"})', env)
    assert result == "hi"


@pytest.mark.parametrize("spec", ["debug", "!", "??", "?>10"])
def test_format_debug_like_unsupported_specs_still_raise(spec):
    env, _, _ = _env()
    with pytest.raises(ValueError, match="format-error: unsupported format spec"):
        run_source(f'format("{{x:{spec}}}", {{x: 1}})', env)


def test_format_debug_mode_missing_named_field_uses_existing_resolution_error():
    env, _, _ = _env()
    with pytest.raises(ValueError, match="format missing field: x"):
        run_source('format("{x:?}", {})', env)


def test_format_debug_mode_missing_positional_field_uses_existing_resolution_error():
    env, _, _ = _env()
    with pytest.raises(ValueError, match="format missing field: 1"):
        run_source('format("{1:?}", ["only zero"])', env)


def test_format_debug_mode_named_field_still_requires_map_values():
    env, _, _ = _env()
    with pytest.raises(TypeError, match="format expected a map for named placeholder: x"):
        run_source('format("{x:?}", [1])', env)


def test_format_debug_mode_positional_field_still_requires_list_values():
    env, _, _ = _env()
    with pytest.raises(TypeError, match="format expected a list for positional placeholder: 0"):
        run_source('format("{0:?}", {x: 1})', env)
