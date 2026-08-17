import importlib
from collections.abc import Callable

from genia.lifecycle_plan import normalize_lifecycle_plan
from genia.values import GeniaMap, OPTION_NONE, symbol


RESULT_KEYS = [
    "status",
    "state",
    "phase",
    "scope",
    "server",
    "primary_failure",
    "cleanup_failures",
]


def _module():
    return importlib.import_module("genia.server_lifecycle")


def _keys(record):
    return [key for key, _value in record.items()]


def _failure_values(failure):
    return {
        "mode": failure.get("mode"),
        "phase": failure.get("phase"),
        "scope": failure.get("scope"),
        "reason": failure.get("reason"),
    }


def test_server_lifecycle_plan_is_inert_and_uses_exact_phases_and_scopes():
    lifecycle = _module()
    calls = []

    plan = lifecycle.server_lifecycle_plan()
    normalized = normalize_lifecycle_plan(plan)

    assert [phase.get("name") for phase in normalized.get("phases")] == [
        symbol("startup"),
        symbol("request"),
        symbol("shutdown"),
    ]
    assert [phase.get("scope") for phase in normalized.get("phases")] == [
        symbol("server"),
        symbol("request"),
        symbol("server"),
    ]
    assert normalized.get("phases")[-1].get("always") is True
    assert all(
        not isinstance(phase.get("action"), Callable)
        for phase in normalized.get("phases")
    )
    assert lifecycle.validate_server_lifecycle().has("plan")
    assert calls == []


def test_success_processes_requests_in_order_closes_once_and_returns_exact_result():
    lifecycle = _module()
    handle = object()
    calls = []

    def activate(application):
        calls.append(("activate", application))
        return handle

    def request(owned, value):
        calls.append(("request", owned, value))
        return f"response:{value}"

    def close(owned):
        calls.append(("close", owned))
        return {"host": "127.0.0.1", "port": 8000, "handled_requests": 2}

    result = lifecycle.run_server_lifecycle(
        {"config": "validated"},
        ["first", "second"],
        activate=activate,
        request=request,
        close=close,
    )

    assert calls == [
        ("activate", {"config": "validated"}),
        ("request", handle, "first"),
        ("request", handle, "second"),
        ("close", handle),
    ]
    assert _keys(result) == RESULT_KEYS
    assert result.get("status") == "ok"
    assert result.get("state") == "stopped"
    assert result.get("phase") == "shutdown"
    assert result.get("scope") == "server"
    assert result.get("server") == {
        "host": "127.0.0.1",
        "port": 8000,
        "handled_requests": 2,
    }
    assert result.get("primary_failure") == OPTION_NONE
    assert result.get("cleanup_failures") == []


def test_success_with_no_requests_still_owns_and_closes_listener_once():
    lifecycle = _module()
    handle = object()
    calls = []

    result = lifecycle.run_server_lifecycle(
        "application",
        [],
        activate=lambda application: calls.append(("activate", application)) or handle,
        request=lambda owned, value: calls.append(("request", owned, value)),
        close=lambda owned: calls.append(("close", owned)) or "server-result",
    )

    assert calls == [("activate", "application"), ("close", handle)]
    assert result.get("status") == "ok"
    assert result.get("server") == "server-result"


def test_startup_failure_skips_requests_and_does_not_close_unowned_listener():
    lifecycle = _module()
    calls = []

    def activate(application):
        calls.append(("activate", application))
        raise RuntimeError("bind failed")

    result = lifecycle.run_server_lifecycle(
        "application",
        ["request"],
        activate=activate,
        request=lambda *_args: calls.append(("request",)),
        close=lambda *_args: calls.append(("close",)),
    )

    assert calls == [("activate", "application")]
    assert result.get("status") == "error"
    assert result.get("state") == "failed"
    assert result.get("phase") == "startup"
    assert result.get("scope") == "server"
    assert result.get("server") == OPTION_NONE
    assert _failure_values(result.get("primary_failure")) == {
        "mode": "serve",
        "phase": "startup",
        "scope": "server",
        "reason": "bind failed",
    }
    assert result.get("cleanup_failures") == []


def test_request_failure_skips_later_requests_and_still_closes_owned_listener():
    lifecycle = _module()
    handle = object()
    calls = []

    def request(owned, value):
        calls.append(("request", owned, value))
        if value == "bad":
            raise ValueError("handler failed")

    result = lifecycle.run_server_lifecycle(
        "application",
        ["first", "bad", "skipped"],
        activate=lambda application: calls.append(("activate", application)) or handle,
        request=request,
        close=lambda owned: calls.append(("close", owned)) or "ignored-on-error",
    )

    assert calls == [
        ("activate", "application"),
        ("request", handle, "first"),
        ("request", handle, "bad"),
        ("close", handle),
    ]
    assert result.get("phase") == "request"
    assert result.get("scope") == "request"
    assert result.get("server") == OPTION_NONE
    assert result.get("primary_failure").get("reason") == "handler failed"
    assert result.get("cleanup_failures") == []


def test_shutdown_failure_is_primary_when_no_earlier_failure_exists():
    lifecycle = _module()
    handle = object()
    close_calls = []

    def close(owned):
        close_calls.append(owned)
        raise RuntimeError("close failed")

    result = lifecycle.run_server_lifecycle(
        "application",
        [],
        activate=lambda _application: handle,
        request=lambda *_args: None,
        close=close,
    )

    assert close_calls == [handle]
    assert result.get("phase") == "shutdown"
    assert result.get("scope") == "server"
    assert result.get("primary_failure").get("reason") == "close failed"
    cleanup_failures = result.get("cleanup_failures")
    assert len(cleanup_failures) == 1
    assert cleanup_failures[0].get("reason") == "close failed"


def test_shutdown_failure_does_not_replace_request_primary_failure():
    lifecycle = _module()
    handle = object()

    def fail_request(_owned, _value):
        raise RuntimeError("request failed first")

    def fail_close(_owned):
        raise RuntimeError("cleanup failed second")

    result = lifecycle.run_server_lifecycle(
        "application",
        ["request"],
        activate=lambda _application: handle,
        request=fail_request,
        close=fail_close,
    )

    assert result.get("phase") == "request"
    assert result.get("scope") == "request"
    assert result.get("primary_failure").get("reason") == "request failed first"
    cleanup_failures = result.get("cleanup_failures")
    assert len(cleanup_failures) == 1
    assert cleanup_failures[0].get("reason") == "cleanup failed second"


def test_failure_preserves_available_source_location():
    lifecycle = _module()

    error = RuntimeError("located failure")
    error.source_location = "app.genia:12"

    def activate(_application):
        raise error

    result = lifecycle.run_server_lifecycle(
        "application",
        [],
        activate=activate,
        request=lambda *_args: None,
        close=lambda *_args: None,
    )

    assert result.get("primary_failure").get("source_location") == "app.genia:12"


def test_module_does_not_expose_generalized_lifecycle_runner_api():
    lifecycle = _module()

    assert not hasattr(lifecycle, "run_lifecycle_phase")
    assert not hasattr(lifecycle, "execute_lifecycle_plan")
    assert not hasattr(lifecycle, "resolve_lifecycle_action")
