import io

import pytest

from genia import make_global_env, run_source


def _env():
    stdout = io.StringIO()
    stderr = io.StringIO()
    return make_global_env(stdout_stream=stdout, stderr_stream=stderr), stdout, stderr


def test_display_returns_display_representation_string_without_output():
    env, stdout, stderr = _env()

    assert run_source('display("hello")', env) == "hello"
    assert run_source('display([1, "x", true, none("missing-key", {key: "name"}), some("ok")])', env) == (
        '[1, x, true, none("missing-key", {key: name}), some(ok)]'
    )
    assert run_source('display({name: "Genia", count: 2})', env) == "{name: Genia, count: 2}"
    assert stdout.getvalue() == ""
    assert stderr.getvalue() == ""


def test_debug_repr_returns_debug_representation_string_without_output():
    env, stdout, stderr = _env()

    assert run_source('debug_repr("line\\n\\t\\"q\\"")', env) == r'"line\n\t\"q\""'
    assert run_source('debug_repr([some("x"), false])', env) == '[some("x"), false]'
    assert run_source('debug_repr({key: "value"})', env) == '{key: "value"}'
    assert stdout.getvalue() == ""
    assert stderr.getvalue() == ""


def test_representation_entrypoints_do_not_change_output_operations():
    env, stdout, stderr = _env()

    assert run_source('print(display("hi"))', env) == "hi"
    assert run_source('writeln(stdout, debug_repr("hi"))', env) == '"hi"'
    assert stdout.getvalue() == 'hi\n"hi"\n'
    assert stderr.getvalue() == ""


def test_representation_entrypoints_follow_ordinary_arity_errors():
    env, _stdout, _stderr = _env()

    with pytest.raises(TypeError):
        run_source("display()", env)

    with pytest.raises(TypeError):
        run_source('debug_repr("a", "b")', env)
