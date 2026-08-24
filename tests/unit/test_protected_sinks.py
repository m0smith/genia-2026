import io

import pytest

from genia.builtins import make_global_env
from genia.host_bridge import _wrap_python_host_callable
from genia.interpreter import run_source
from genia.test_cli import format_test_suite_report
from genia.utf8 import format_debug, format_display
from genia.values import GeniaMap, GeniaOptionErr, GeniaOptionNone


PAYLOAD = "PROTECTED_PAYLOAD_SENTINEL_592"
KEY = "PROTECTED_KEY_SENTINEL_592"
PURPOSE = "PROTECTED_PURPOSE_SENTINEL_592"


def _env_with_protected(*, stdout=None, stderr=None):
    env = make_global_env(stdout_stream=stdout, stderr_stream=stderr)
    protected = run_source(
        "provider = config_provider([{kind: quote(values), values: {"
        f'{KEY}: "{PAYLOAD}"'
        "}}]) |> unwrap_or(none)\n"
        f'secret_get(provider, "{KEY}", quote({PURPOSE})) |> unwrap_or(none)',
        env,
    )
    env.set("protected_fixture", protected)
    return env, protected


def _assert_no_sentinel(text):
    rendered = str(text)
    assert PAYLOAD not in rendered
    assert KEY not in rendered
    assert PURPOSE not in rendered


def test_diagnostic_renderers_redact_nested_protected_leaves():
    env, protected = _env_with_protected()
    value = run_source(
        'sheet_value = sheet([["credential", [protected_fixture]]])\n'
        '[protected_fixture, {nested: some(protected_fixture)}, sheet_value]',
        env,
    )

    assert format_display(protected) == "<protected>"
    assert format_debug(protected) == "<protected>"
    for rendered in (format_display(value), format_debug(value)):
        assert "<protected>" in rendered
        _assert_no_sentinel(rendered)


@pytest.mark.parametrize(
    "source",
    [
        "print(protected_fixture)",
        "log({nested: [protected_fixture]})",
        "inspect(protected_fixture)",
        'trace("credential", protected_fixture)',
        "write(stdout, protected_fixture)",
        "writeln(stderr, {nested: protected_fixture})",
    ],
)
def test_output_sinks_reject_recursively_before_writing(source):
    stdout = io.StringIO()
    stderr = io.StringIO()
    env, _ = _env_with_protected(stdout=stdout, stderr=stderr)

    with pytest.raises(TypeError, match="protected-value") as excinfo:
        run_source(source, env)

    assert stdout.getvalue() == ""
    assert stderr.getvalue() == ""
    _assert_no_sentinel(excinfo.value)


def test_format_rejects_a_protected_resolved_replacement():
    env, _ = _env_with_protected()

    with pytest.raises(TypeError, match="protected-value") as excinfo:
        run_source('format("token={token}", {token: protected_fixture})', env)

    _assert_no_sentinel(excinfo.value)


def test_json_boundaries_reject_recursively_with_exact_encode_shape():
    env, _ = _env_with_protected()

    encoded = run_source("json_encode({nested: [protected_fixture]})", env)
    assert isinstance(encoded, GeniaOptionErr)
    assert str(encoded.reason) == "protected-value"
    assert list(encoded.context.items()) == [["operation", "json-encode"]]
    _assert_no_sentinel(format_debug(encoded))

    stringified = run_source("json_stringify({nested: protected_fixture})", env)
    assert isinstance(stringified, GeniaOptionNone)
    assert stringified.reason == "protected-value"
    _assert_no_sentinel(format_debug(stringified))


def test_sheet_csv_rejects_with_structural_position_only():
    env, _ = _env_with_protected()

    with pytest.raises(TypeError, match="protected-value.*row 0, column 0") as excinfo:
        run_source(
            'render_csv(sheet([["credential", [protected_fixture]]]))',
            env,
        )

    _assert_no_sentinel(excinfo.value)


def test_resource_write_rejects_before_creating_or_writing_file(tmp_path):
    target = tmp_path / "protected.txt"
    env, _ = _env_with_protected()
    env.set("target_path", str(target))

    result = run_source(
        'import resource as res\n'
        'res.write_text(res.resource_ref(target_path), protected_fixture)',
        env,
    )

    assert isinstance(result, GeniaOptionNone)
    assert result.reason == "protected-value"
    assert not target.exists()
    _assert_no_sentinel(format_debug(result))


def test_python_host_callable_is_not_invoked_for_nested_protected_argument():
    env, protected = _env_with_protected()
    calls = []
    wrapped = _wrap_python_host_callable(
        "fixture", "capture", lambda value: calls.append(value) or value
    )

    with pytest.raises(TypeError, match="protected-value") as excinfo:
        wrapped([GeniaMap().put("nested", protected)])

    assert calls == []
    _assert_no_sentinel(excinfo.value)


def test_native_test_report_redacts_protected_actual_and_expected_values():
    _, protected = _env_with_protected()
    suite = {
        "total": 1,
        "passed": 0,
        "failed": 1,
        "errored": 0,
        "results": [
            {
                "kind": "fail",
                "name": "protected assertion",
                "phase": "run",
                "reason": "assertion failed",
                "expected": protected,
                "actual": GeniaMap().put("nested", protected),
            }
        ],
    }

    report = format_test_suite_report(suite)

    assert report.count("<protected>") == 2
    _assert_no_sentinel(report)
