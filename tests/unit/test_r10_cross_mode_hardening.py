import io

import pytest

import genia.interpreter as interpreter_module
from genia.builtins import make_global_env
from genia.configuration import create_declassification_authority
from genia.interpreter import run_source
from genia.test_cli import make_test_env, run_native_tests_from_file
from genia.values import GeniaMap, GeniaOptionSome, symbol


KEY = "R10_CROSS_MODE_KEY_SENTINEL_594"
PAYLOAD = "R10_CROSS_MODE_PAYLOAD_SENTINEL_594"
PURPOSE = "fixture_use"


def _assert_sentinels_absent(value):
    rendered = str(value)
    assert KEY not in rendered
    assert PAYLOAD not in rendered


def _literal_provider(env):
    result = run_source(
        'config_provider([{kind: quote(values), values: {'
        f'{KEY}: "{PAYLOAD}"'
        "}}])",
        env,
    )
    assert isinstance(result, GeniaOptionSome)
    return result.value


def test_imports_and_inert_annotations_do_not_acquire_configuration(tmp_path):
    module = tmp_path / "fixture_module.genia"
    module.write_text('value = "ordinary"\n', encoding="utf-8")
    calls = []
    env = make_global_env(environment_snapshot_provider=lambda: calls.append(True) or {KEY: PAYLOAD})

    result = run_source(
        f'''
        import fixture_module
        @meta {{configuration_key: "{KEY}"}}
        annotated = fixture_module.value
        annotated
        ''',
        env,
        filename=str((tmp_path / "entry.genia").resolve()),
    )

    assert result == "ordinary"
    assert calls == []


def test_explicit_import_acquisition_uses_the_shared_snapshot_capability_once(tmp_path):
    module = tmp_path / "fixture_module.genia"
    module.write_text(
        "provider = config_provider([{kind: quote(environment)}]) |> unwrap_or(none)\n"
        f'value = config_get(provider, "{KEY}")\n',
        encoding="utf-8",
    )
    calls = []
    env = make_global_env(environment_snapshot_provider=lambda: calls.append(True) or {KEY: PAYLOAD})

    result = run_source(
        "import fixture_module\nfixture_module.value",
        env,
        filename=str((tmp_path / "entry.genia").resolve()),
    )

    assert isinstance(result, GeniaOptionSome)
    assert result.value == PAYLOAD
    assert calls == [True]


def test_native_test_harness_accepts_explicit_provider_and_authority_fixtures(tmp_path):
    fixture_env = make_global_env(environment_snapshot_provider=None)
    provider = _literal_provider(fixture_env)
    authority = create_declassification_authority(
        provider,
        [symbol(PURPOSE)],
        lambda _event: None,
    )
    program = tmp_path / "fixture_test.genia"
    program.write_text(
        f'''
        @test "explicit fixture authority"
        verify_fixture() = assert_eq(
          declassify(authority_fixture, secret_get(provider_fixture, "{KEY}", quote({PURPOSE})) |> unwrap_or(none)),
          "{PAYLOAD}"
        )
        ''',
        encoding="utf-8",
    )
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = run_native_tests_from_file(
        str(program),
        fixture_bindings={
            "provider_fixture": provider,
            "authority_fixture": authority,
        },
        environment_snapshot_provider=None,
        stdout_stream=stdout,
        stderr_stream=stderr,
    )

    assert exit_code == 0
    assert "passed=1" in stdout.getvalue()
    assert stderr.getvalue() == ""
    _assert_sentinels_absent(stdout.getvalue())
    _assert_sentinels_absent(stderr.getvalue())


def test_native_test_fixture_authority_mismatch_is_redacted():
    fixture_env = make_global_env(environment_snapshot_provider=None)
    provider = _literal_provider(fixture_env)
    other_provider = _literal_provider(make_global_env(environment_snapshot_provider=None))
    authority = create_declassification_authority(
        other_provider,
        [symbol(PURPOSE)],
        lambda _event: None,
    )
    env, _ = make_test_env(
        fixture_bindings={
            "provider_fixture": provider,
            "authority_fixture": authority,
        },
        environment_snapshot_provider=None,
    )

    with pytest.raises(TypeError) as excinfo:
        run_source(
            f'declassify(authority_fixture, secret_get(provider_fixture, "{KEY}", quote({PURPOSE})) |> unwrap_or(none))',
            env,
        )

    _assert_sentinels_absent(excinfo.value)


def test_serve_explicit_snapshot_precedes_activation_and_is_not_refreshed(tmp_path, monkeypatch):
    program = tmp_path / "server.genia"
    program.write_text(
        f'''
        import web
        provider = config_provider([{{kind: quote(environment)}}]) |> unwrap_or(none)
        configured = config_get(provider, "{KEY}") |> unwrap_or("missing")

        @server {{host: "127.0.0.1", port: 0, max_requests: 1}}
        server_owner = none

        @route {{method: "GET", path: "/"}}
        home(request) = web.ok_text(configured)
        ''',
        encoding="utf-8",
    )
    events = []
    original_make_global_env = make_global_env

    def make_env(*args, **kwargs):
        return original_make_global_env(
            *args,
            **kwargs,
            environment_snapshot_provider=lambda: events.append("snapshot") or {KEY: PAYLOAD},
        )

    def activate(_config, handler, _serve_http):
        events.append("activate")
        response = handler(GeniaMap().put("method", "GET").put("path", "/"))
        events.append(response.get("body"))
        return {"handled_requests": 1}

    monkeypatch.setattr(interpreter_module, "make_global_env", make_env)
    monkeypatch.setattr(interpreter_module, "_activate_serve_application", activate)

    assert interpreter_module._run_serve_file(str(program)) == 0
    assert events == ["snapshot", "activate", PAYLOAD]
