import genia.interpreter as interpreter_module


def test_serve_file_assembles_entry_descriptors_and_activates_once(tmp_path, monkeypatch):
    program = tmp_path / "server.genia"
    program.write_text(
        '''
import web

@server {host: "127.0.0.1", port: 0, max_requests: 1}
server_owner = none

@cors {origin: "*", methods: ["GET"], headers: []}
@server {host: "127.0.0.1", port: 0, max_requests: 1}
invalid_duplicate_owner = none

@route {method: "GET", path: "/"}
home(request) = web/ok_text("ok")
''',
        encoding="utf-8",
    )
    activations = []

    monkeypatch.setattr(
        interpreter_module,
        "_activate_serve_application",
        lambda config, handler: activations.append((config, handler)) or {"handled_requests": 0},
        raising=False,
    )

    exit_code = interpreter_module._run_serve_file(str(program))

    assert exit_code == 1
    assert activations == []


def test_serve_file_does_not_dispatch_main_and_returns_success(tmp_path, monkeypatch):
    program = tmp_path / "server.genia"
    program.write_text(
        '''
import web

@server {host: "127.0.0.1", port: 0, max_requests: 1}
server_owner = none

@route {method: "GET", path: "/"}
home(request) = web/ok_text("ok")

main() = error("serve dispatched main")
''',
        encoding="utf-8",
    )
    calls = []

    monkeypatch.setattr(
        interpreter_module,
        "_activate_serve_application",
        lambda config, handler, _serve_http: calls.append((config, handler)) or {"handled_requests": 0},
        raising=False,
    )

    assert interpreter_module._run_serve_file(str(program)) == 0
    assert len(calls) == 1
    assert calls[0][0].get("host") == "127.0.0.1"
    assert calls[0][0].get("port") == 0
    assert calls[0][0].get("max_requests") == 1


def test_serve_file_reports_missing_server_without_activation(tmp_path, monkeypatch, capsys):
    program = tmp_path / "server.genia"
    program.write_text("main() = 1", encoding="utf-8")
    calls = []
    monkeypatch.setattr(
        interpreter_module,
        "_activate_serve_application",
        lambda *_args: calls.append("activate"),
        raising=False,
    )

    assert interpreter_module._run_serve_file(str(program)) == 1
    assert calls == []
    error = capsys.readouterr().err
    assert "serve startup/server" in error
    assert "required @server descriptor not found in entry file" in error
