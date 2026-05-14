import io

import pytest

from genia import make_global_env, run_source
from genia.utf8 import format_debug


def _env():
    stdout = io.StringIO()
    stderr = io.StringIO()
    return make_global_env(stdout_stream=stdout, stderr_stream=stderr), stdout, stderr


def test_tagged_format_formats_like_untagged_format():
    env, _, _ = _env()
    untagged = run_source('format(Format("{name}"), {name: "Ada"})', env)

    env2, _, _ = _env()
    tagged = run_source('format(Format("{name}", "person-card"), {name: "Ada"})', env2)

    assert untagged == tagged == "Ada"


def test_tagged_format_supports_positional_placeholders():
    env, _, _ = _env()
    result = run_source('format(Format("{0} {1}", "pair-line"), ["hello", "world"])', env)

    assert result == "hello world"


def test_tagged_format_preserves_escaped_braces_and_debug_specs():
    env, _, _ = _env()
    result = run_source(
        'format(Format("{{name}} {name:?}", "debug-line"), {name: "Ada"})',
        env,
    )

    assert result == '{name} "Ada"'


def test_format_tag_returns_none_for_untagged_format():
    env, _, _ = _env()
    result = run_source('format_tag(Format("{name}"))', env)

    assert format_debug(result) == 'none("missing-format-tag")'


def test_format_tag_returns_some_for_tagged_format():
    env, _, _ = _env()
    result = run_source('format_tag(Format("{name}", "person-card"))', env)

    assert format_debug(result) == 'some("person-card")'


def test_tagged_format_display_and_debug_remain_opaque():
    env, _, _ = _env()
    display = run_source('display(Format("{secret}", "person-card"))', env)

    env2, _, _ = _env()
    debug = run_source('debug_repr(Format("{secret}", "person-card"))', env2)

    assert display == "<format>"
    assert debug == "<format>"
    assert "person-card" not in display
    assert "person-card" not in debug
    assert "{secret}" not in display
    assert "{secret}" not in debug


def test_tagged_format_missing_named_field_uses_existing_error():
    env, _, _ = _env()
    with pytest.raises(ValueError, match="format missing field: name"):
        run_source('format(Format("{name}", "person-card"), {})', env)


def test_tagged_format_missing_positional_field_uses_existing_error():
    env, _, _ = _env()
    with pytest.raises(ValueError, match="format missing field: 1"):
        run_source('format(Format("{1}", "pair-line"), ["only zero"])', env)


def test_tagged_format_unsupported_spec_uses_existing_error():
    env, _, _ = _env()
    with pytest.raises(ValueError, match="format-error: unsupported format spec"):
        run_source('format(Format("{name:debug}", "person-card"), {name: "Ada"})', env)


def test_format_constructor_rejects_zero_arguments():
    env, _, _ = _env()
    with pytest.raises(TypeError, match="Format expected 1 or 2 args, got 0"):
        run_source("Format()", env)


def test_format_constructor_rejects_more_than_two_arguments():
    env, _, _ = _env()
    with pytest.raises(TypeError, match="Format expected 1 or 2 args, got 3"):
        run_source('Format("{name}", "person-card", "extra")', env)


def test_format_constructor_rejects_non_string_template():
    env, _, _ = _env()
    with pytest.raises(TypeError, match="Format expected template string, received int"):
        run_source("Format(123)", env)


def test_format_constructor_rejects_non_string_tag():
    env, _, _ = _env()
    with pytest.raises(TypeError, match="Format expected tag string, received int"):
        run_source('Format("{name}", 123)', env)


def test_format_constructor_rejects_empty_tag():
    env, _, _ = _env()
    with pytest.raises(TypeError, match="Format expected non-empty tag string"):
        run_source('Format("{name}", "")', env)


def test_format_tag_rejects_zero_arguments():
    env, _, _ = _env()
    with pytest.raises(TypeError, match="format_tag expected 1 arg, got 0"):
        run_source("format_tag()", env)


def test_format_tag_rejects_more_than_one_argument():
    env, _, _ = _env()
    with pytest.raises(TypeError, match="format_tag expected 1 arg, got 2"):
        run_source('format_tag(Format("{x}"), Format("{y}"))', env)


def test_format_tag_rejects_non_format_value():
    env, _, _ = _env()
    with pytest.raises(TypeError, match="format_tag expected a format value, received string"):
        run_source('format_tag("not-format")', env)
