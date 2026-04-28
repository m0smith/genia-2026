from pathlib import Path

from genia import make_global_env, run_source


def _load_example(path: str):
    env = make_global_env([])
    source_path = Path(path)
    source = source_path.read_text(encoding="utf-8")
    run_source(source, env, filename=str(source_path.resolve()))
    return env


def _run(env, source: str):
    return run_source(source, env, filename="<rest-example-test>")


def test_rest_todo_service_create_and_list():
    env = _load_example("examples/rest_todo_service.genia")

    created = _run(
        env,
        """
        handler = app()
        request = {
          method: "POST",
          path: "/todos/create",
          query: {},
          headers: {"content-type": "application/json"},
          body: {title: "Ship docs"},
          raw_body: ""
        }
        handler(request)
        """,
    )
    listed = _run(
        env,
        """
        handler = app()
        request = {
          method: "GET",
          path: "/todos",
          query: {},
          headers: {},
          body: none,
          raw_body: ""
        }
        handler(request)
        """,
    )

    assert created.get("status") == 200
    assert created.get("headers").get("content-type") == "application/json; charset=utf-8"
    assert created.get("body") == '{\n  "done": false,\n  "id": 1,\n  "title": "Ship docs"\n}'
    assert listed.get("status") == 200
    assert listed.get("headers").get("content-type") == "application/json; charset=utf-8"
    assert listed.get("body") == '{\n  "count": 1,\n  "items": [\n    {\n      "done": false,\n      "id": 1,\n      "title": "Ship docs"\n    }\n  ]\n}'


def test_rest_webhook_service_ingests_and_lists_events():
    env = _load_example("examples/rest_webhook_service.genia")

    created = _run(
        env,
        """
        handler = app()
        request = {
          method: "POST",
          path: "/webhooks/events",
          query: {},
          headers: {"x-signature": "sig_test"},
          body: {type: "invoice.paid", data: {customer: "cus_123"}},
          raw_body: ""
        }
        handler(request)
        """,
    )
    listed = _run(
        env,
        """
        handler = app()
        request = {
          method: "GET",
          path: "/webhooks/events",
          query: {},
          headers: {},
          body: none,
          raw_body: ""
        }
        handler(request)
        """,
    )

    assert created.get("status") == 200
    assert created.get("headers").get("content-type") == "application/json; charset=utf-8"
    assert created.get("body") == '{\n  "accepted": true,\n  "received": {\n    "data": {\n      "customer": "cus_123"\n    },\n    "event_type": "invoice.paid",\n    "signature": "sig_test"\n  },\n  "total": 1\n}'
    assert listed.get("status") == 200
    assert listed.get("headers").get("content-type") == "application/json; charset=utf-8"
    assert listed.get("body") == '{\n  "items": [\n    {\n      "data": {\n        "customer": "cus_123"\n      },\n      "event_type": "invoice.paid",\n      "signature": "sig_test"\n    }\n  ],\n  "total": 1\n}'


def test_rest_metrics_service_tracks_and_summarizes():
    env = _load_example("examples/rest_metrics_service.genia")

    created = _run(
        env,
        """
        handler = app()
        request = {
          method: "POST",
          path: "/metrics/track",
          query: {},
          headers: {"content-type": "application/json"},
          body: {name: "signups", value: 3},
          raw_body: ""
        }
        handler(request)
        """,
    )
    listed = _run(
        env,
        """
        handler = app()
        request = {
          method: "GET",
          path: "/metrics/summary",
          query: {},
          headers: {},
          body: none,
          raw_body: ""
        }
        handler(request)
        """,
    )

    assert created.get("status") == 200
    assert created.get("headers").get("content-type") == "application/json; charset=utf-8"
    assert created.get("body") == '{\n  "summary": {\n    "count": 1,\n    "total": 3\n  },\n  "tracked": "signups"\n}'
    assert listed.get("status") == 200
    assert listed.get("headers").get("content-type") == "application/json; charset=utf-8"
    assert listed.get("body") == '{\n  "metrics": {\n    "signups": {\n      "count": 1,\n      "total": 3\n    }\n  }\n}'


def test_rest_feature_flags_updates_and_queries():
    env = _load_example("examples/rest_feature_flags.genia")

    updated = _run(
        env,
        """
        handler = app()
        request = {
          method: "POST",
          path: "/flags/set",
          query: {},
          headers: {"content-type": "application/json"},
          body: {flag: "release_banner", enabled: true},
          raw_body: ""
        }
        handler(request)
        """,
    )
    queried = _run(
        env,
        """
        handler = app()
        request = {
          method: "GET",
          path: "/flags",
          query: {user: "guest"},
          headers: {},
          body: none,
          raw_body: ""
        }
        handler(request)
        """,
    )

    assert updated.get("status") == 200
    assert updated.get("headers").get("content-type") == "application/json; charset=utf-8"
    assert updated.get("body") == '{\n  "flag": "release_banner",\n  "rule": {\n    "enabled": true,\n    "users": []\n  }\n}'
    assert queried.get("status") == 200
    assert queried.get("headers").get("content-type") == "application/json; charset=utf-8"
    assert queried.get("body") == '{\n  "enabled": [\n    "beta_search",\n    "release_banner"\n  ],\n  "user": "guest"\n}'


def test_rest_shortener_service_creates_and_resolves():
    env = _load_example("examples/rest_shortener_service.genia")

    created = _run(
        env,
        """
        handler = app()
        request = {
          method: "POST",
          path: "/links",
          query: {},
          headers: {"content-type": "application/json"},
          body: {code: "docs", url: "https://genia.dev/docs"},
          raw_body: ""
        }
        handler(request)
        """,
    )
    resolved = _run(
        env,
        """
        handler = app()
        request = {
          method: "GET",
          path: "/resolve",
          query: {code: "docs"},
          headers: {},
          body: none,
          raw_body: ""
        }
        handler(request)
        """,
    )

    assert created.get("status") == 200
    assert created.get("headers").get("content-type") == "application/json; charset=utf-8"
    assert created.get("body") == '{\n  "code": "docs",\n  "url": "https://genia.dev/docs"\n}'
    assert resolved.get("status") == 200
    assert resolved.get("headers").get("content-type") == "application/json; charset=utf-8"
    assert resolved.get("body") == '{\n  "code": "docs",\n  "url": "https://genia.dev/docs"\n}'
