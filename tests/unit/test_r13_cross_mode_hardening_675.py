import io
from pathlib import Path

import pytest

import genia.interpreter as interpreter_module
from genia.builtins import make_global_env
from genia.configuration import create_declassification_authority
from genia.interpreter import run_source
from genia.utf8 import format_debug, format_display
from genia.values import GeniaMap, GeniaOptionErr, GeniaOptionSome, GeniaProtected, symbol


ROOT = Path(__file__).resolve().parents[2]
SHARED_CASES = (
    ROOT / "spec/eval/r13-cross-mode-explicit-standard.yaml",
    ROOT / "spec/error/error-r13-standard-source-failure.yaml",
    ROOT / "spec/cli/r13-cross-mode-command.yaml",
    ROOT / "spec/cli/r13-cross-mode-file.yaml",
    ROOT / "spec/cli/r13-cross-mode-pipe.yaml",
    ROOT / "spec/parse/parse-r13-existing-call-forms.yaml",
    ROOT / "spec/ir/r13-existing-call-ir.yaml",
)
SENTINELS = (
    "PREFIX_SENTINEL_675",
    "LOGICAL_SENTINEL_675",
    "PHYSICAL_KEY_SENTINEL_675",
    "PATH_SENTINEL_675",
    "SOURCE_VALUE_SENTINEL_675",
    "RAW_HOST_SENTINEL_675",
    "PROTECTED_PAYLOAD_SENTINEL_675",
    "PURPOSE_SENTINEL_675",
)


def _assert_sentinels_absent(*observations):
    rendered = "\n".join(str(value) for value in observations)
    assert all(sentinel not in rendered for sentinel in SENTINELS)


def test_e13_5_shared_conformance_inventory_exists():
    assert all(path.is_file() for path in SHARED_CASES)


def test_standard_snapshot_is_constructed_once_then_views_and_authorized_use_do_not_refresh():
    events = []
    environment_values = {
        "SERVER_PORT": "8080",
        "OPENAI_TOKEN": SENTINELS[6],
    }

    def environment():
        events.append("environment")
        return environment_values

    def dotenv(path):
        events.append(("dotenv", path))
        return b"DB_PORT=5432"

    env = make_global_env(
        environment_snapshot_provider=environment,
        dotenv_snapshot_provider=dotenv,
    )
    provider = env.get("config_standard")(GeniaMap(), []).value
    purpose = symbol(SENTINELS[7])
    protected = env.get("secret_view")(provider, "OPENAI_", purpose)("TOKEN").value
    audits = []
    authority = create_declassification_authority(
        provider,
        [purpose],
        lambda event: events.append("audit") or audits.append(event),
    )

    environment_values["SERVER_PORT"] = "9999"
    assert env.get("config_view")(provider, "SERVER_")("PORT").value == "8080"
    assert env.get("config_view")(provider, "DB_")("PORT").value == "5432"
    assert isinstance(protected, GeniaProtected)
    assert format_display(protected) == "<protected>"
    assert env.get("declassify")(authority, protected) == SENTINELS[6]
    assert events == ["environment", ("dotenv", ".env"), "audit"]
    assert len(audits) == 1
    assert audits[0]["purpose"] == SENTINELS[7]
    _assert_sentinels_absent(format_debug(protected))
    audit_text = str(audits)
    assert SENTINELS[6] not in audit_text
    assert SENTINELS[5] not in audit_text


def test_standard_failures_are_exact_effect_free_and_sentinel_free():
    calls = []
    env = make_global_env(
        environment_snapshot_provider=lambda: calls.append("environment") or {},
        dotenv_snapshot_provider=lambda path: (_ for _ in ()).throw(
            PermissionError(SENTINELS[5])
        ),
    )

    malformed = env.get("config_standard")(
        GeniaMap(), ["--bad_name", SENTINELS[4]], SENTINELS[3]
    )
    assert isinstance(malformed, GeniaOptionErr)
    assert malformed.reason == "config-source-invalid"
    assert calls == []
    _assert_sentinels_absent(format_debug(malformed))

    failed = env.get("config_standard")(GeniaMap(), [], SENTINELS[3])
    assert isinstance(failed, GeniaOptionErr)
    assert failed.reason == "config-provider-failure"
    assert failed.context.items() == [
        ["source_index", 3],
        ["source_kind", symbol("dotenv")],
        ["stage", symbol("acquire")],
    ]
    assert calls == ["environment"]
    _assert_sentinels_absent(format_debug(failed))


def test_import_without_construction_is_inert_and_explicit_module_standard_snapshots_once(tmp_path):
    inert = tmp_path / "inert.genia"
    inert.write_text('value = "ordinary"\n', encoding="utf-8")
    explicit = tmp_path / "explicit.genia"
    explicit.write_text(
        'provider = config_standard({}, []) |> unwrap_or(none)\n'
        'port = config_view(provider, "SERVER_")("PORT")\n',
        encoding="utf-8",
    )
    calls = []
    env = make_global_env(
        environment_snapshot_provider=lambda: calls.append("environment")
        or {"SERVER_PORT": "8080"},
        dotenv_snapshot_provider=lambda path: calls.append(("dotenv", path)) or b"",
    )

    assert run_source(
        "import inert\ninert.value", env, filename=str(tmp_path / "entry.genia")
    ) == "ordinary"
    assert calls == []
    result = run_source(
        "import explicit\nexplicit.port", env, filename=str(tmp_path / "entry.genia")
    )
    assert isinstance(result, GeniaOptionSome) and result.value == "8080"
    assert calls == ["environment", ("dotenv", ".env")]


def test_native_test_requires_explicit_standard_construction_and_snapshots_once(tmp_path):
    program = tmp_path / "configuration_native_tests.genia"
    program.write_text(
        '''
provider = config_standard({}, []) |> unwrap_or(none)
server = config_view(provider, "SERVER_")

@test "explicit standard provider"
explicit_standard() = assert_eq(server("PORT"), some("8080"))
''',
        encoding="utf-8",
    )
    calls = []
    stdout = io.StringIO()
    stderr = io.StringIO()

    from genia.test_cli import run_native_tests_from_file

    exit_code = run_native_tests_from_file(
        str(program),
        environment_snapshot_provider=lambda: calls.append("environment")
        or {"SERVER_PORT": "8080"},
        dotenv_snapshot_provider=lambda path: calls.append(("dotenv", path)) or b"",
        stdout_stream=stdout,
        stderr_stream=stderr,
    )

    assert exit_code == 0
    assert calls == ["environment", ("dotenv", ".env")]
    assert "passed=1" in stdout.getvalue()
    assert stderr.getvalue() == ""


def test_serve_standard_snapshot_precedes_activation_and_request_does_not_refresh(
    tmp_path, monkeypatch
):
    program = tmp_path / "server.genia"
    program.write_text(
        '''
import web
provider = config_standard({}, []) |> unwrap_or(none)
configured = config_view(provider, "SERVER_")("PORT") |> unwrap_or("missing")

@server {host: "127.0.0.1", port: 0, max_requests: 1}
server_owner = none

@route {method: "GET", path: "/"}
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
            environment_snapshot_provider=lambda: events.append("environment")
            or {"SERVER_PORT": "8080"},
            dotenv_snapshot_provider=lambda path: events.append(("dotenv", path)) or b"",
        )

    def activate(_config, handler, _serve_http):
        events.append("activate")
        response = handler(GeniaMap().put("method", "GET").put("path", "/"))
        events.append(response.get("body"))
        return {"handled_requests": 1}

    monkeypatch.setattr(interpreter_module, "make_global_env", make_env)
    monkeypatch.setattr(interpreter_module, "_activate_serve_application", activate)

    assert interpreter_module._run_serve_file(str(program)) == 0
    assert events == ["environment", ("dotenv", ".env"), "activate", "8080"]


def test_view_misuse_diagnostic_does_not_reveal_captured_or_requested_names():
    provider = run_source(
        'config_provider([{kind: quote(values), values: {}}]) |> unwrap_or(none)',
        make_global_env([]),
    )
    view = make_global_env([]).get("config_view")(provider, SENTINELS[0])

    with pytest.raises(TypeError) as excinfo:
        view(SENTINELS[1] + "\0")

    _assert_sentinels_absent(excinfo.value)
