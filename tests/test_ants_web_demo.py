import json
import socket
import threading
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from genia import make_global_env, run_source


SOURCE_PATH = Path("examples/ants_web.genia")
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")
FILENAME = str(SOURCE_PATH.resolve())


def run_web(src_suffix: str):
    return run_source(SOURCE + "\n" + src_suffix, make_global_env(), filename=FILENAME)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _start_server(source: str, env, *, filename: str):
    outcome: dict[str, object] = {}

    def target() -> None:
        try:
            outcome["result"] = run_source(source, env, filename=filename)
        except BaseException as exc:  # pragma: no cover - surfaced by assertions
            outcome["error"] = exc

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    return thread, outcome


def _request(method: str, url: str, *, body: str | None = None, headers: dict[str, str] | None = None):
    encoded_body = None if body is None else body.encode("utf-8")
    last_error = None

    for _ in range(60):
        try:
            request = Request(url, data=encoded_body, method=method, headers={} if headers is None else headers)
            with urlopen(request, timeout=2) as response:
                return response.status, response.headers, response.read().decode("utf-8")
        except HTTPError as exc:
            return exc.code, exc.headers, exc.read().decode("utf-8")
        except URLError as exc:
            last_error = exc
            time.sleep(0.02)

    raise last_error  # type: ignore[misc]


def _finish_server(thread: threading.Thread, outcome: dict[str, object]):
    thread.join(timeout=3)
    assert not thread.is_alive(), "server thread did not stop"
    if "error" in outcome:
        raise outcome["error"]  # type: ignore[misc]
    return outcome["result"]


def test_ants_web_snapshot_is_json_friendly_and_uses_ants_logic():
    result = run_web(
        """
        state = reset_state({seed: 7, ants: 3, size: 8, delay: 0, mode: "pure"})
        json_stringify(snapshot_state(state))
        """
    )
    snapshot = json.loads(result)

    assert snapshot["tick"] == 0
    assert snapshot["seed"] == 7
    assert snapshot["mode"] == "pure"
    assert snapshot["width"] == 8
    assert snapshot["height"] == 8
    assert len(snapshot["ants"]) == 3
    assert snapshot["nest"]["center"] == {"x": 4, "y": 4}
    assert snapshot["food"]
    assert snapshot["pheromones"] == []
    assert snapshot["delivered"] == 0
    assert snapshot["remaining_food"] == 24
    assert snapshot["stats"]["ants"] == 3


def test_ants_web_reset_and_step_are_seeded_and_deterministic():
    program = """
    reset_state({seed: 9, ants: 4, size: 8, delay: 0, mode: "pure"})
    first = step_handler({})/body |> json_parse
    reset_state({seed: 9, ants: 4, size: 8, delay: 0, mode: "pure"})
    second = step_handler({})/body |> json_parse
    [first/tick, first/ants, second/tick, second/ants, json_stringify(first) == json_stringify(second)]
    """

    result = run_web(program)

    assert result[0] == 1
    assert result[2] == 1
    assert result[4] is True


def test_ants_web_actor_mode_endpoint_uses_actor_session():
    result = run_web(
        """
        req = {body: {seed: 11, ants: 2, size: 8, delay: 0, mode: "actor"}}
        reset = reset_handler(req)/body |> json_parse
        stepped = step_handler({})/body |> json_parse
        [reset/mode, reset/stats/ants, stepped/mode, stepped/tick, stepped/stats/ants]
        """
    )

    assert result == ["actor", 2, "actor", 1, 2]


def test_ants_web_static_assets_are_small_browser_ui():
    result = run_web(
        """
        [
          contains(html_page(), "<canvas"),
          contains(app_js(), "fetch(\\"/state\\")"),
          contains(app_js(), "fetch(path"),
          contains(style_css(), "grid-template-columns")
        ]
        """
    )

    assert result == [True, True, True, True]


def test_ants_web_http_routes_serve_assets_and_state_updates():
    port = _free_port()
    env = make_global_env([])
    source = SOURCE + f'\nmain(["--port", "{port}", "--max-requests", "4"])\n'

    thread, outcome = _start_server(source, env, filename=FILENAME)

    status, headers, body = _request("GET", f"http://127.0.0.1:{port}/")
    assert status == 200
    assert headers["Content-Type"] == "text/html; charset=utf-8"
    assert "<canvas" in body

    status, headers, body = _request("GET", f"http://127.0.0.1:{port}/state")
    initial = json.loads(body)
    assert status == 200
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    assert initial["tick"] == 0

    status, headers, body = _request(
        "POST",
        f"http://127.0.0.1:{port}/reset",
        body='{"seed":5,"ants":2,"size":8,"delay":0,"mode":"pure"}',
        headers={"Content-Type": "application/json"},
    )
    reset = json.loads(body)
    assert status == 200
    assert reset["seed"] == 5
    assert reset["stats"]["ants"] == 2
    assert reset["width"] == 8

    status, headers, body = _request("POST", f"http://127.0.0.1:{port}/step", body="{}")
    stepped = json.loads(body)
    result = _finish_server(thread, outcome)

    assert status == 200
    assert stepped["tick"] == 1
    assert result.get("handled_requests") == 4
