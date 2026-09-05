from __future__ import annotations

import subprocess
import sys


EXPECTED_LOOPBACK_TESTS = {
    "tests/demo/test_ants_web_demo.py::test_ants_web_http_routes_serve_assets_and_state_updates",
    "tests/unit/test_http_web.py::test_http_service_example_runs_health_endpoint",
    "tests/unit/test_http_web.py::test_serve_http_cors_preflight_then_json_request",
    "tests/unit/test_http_web.py::test_serve_http_emits_headers_composed_by_with_headers",
    "tests/unit/test_http_web.py::test_serve_http_invalid_handler_result_returns_500",
    "tests/unit/test_http_web.py::test_serve_http_json_body_parse_failure_stays_in_request_body_as_absence",
    "tests/unit/test_http_web.py::test_serve_http_json_response_and_request_body_parsing",
    "tests/unit/test_http_web.py::test_serve_http_plain_text_response",
    "tests/unit/test_http_web.py::test_serve_http_request_map_includes_client_and_raw_text_body",
    "tests/unit/test_http_web.py::test_serve_http_route_request_returns_not_found_response",
    "tests/unit/test_http_transport.py::test_send_http_request_returns_exact_status_headers_body_from_real_server",
    "tests/unit/test_http_transport.py::test_send_http_request_http_error_status_returns_ordinary_response_not_failure",
    "tests/unit/test_http_transport.py::test_send_http_request_does_not_follow_redirect",
    "tests/unit/test_http_transport.py::test_send_http_request_connect_refused_returns_connect_failure",
    "tests/unit/test_http_transport.py::test_send_http_request_timeout_against_slow_server_returns_timeout_failure",
}


def _run_pytest(*args: str) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def _collect(marker_expression: str | None = None) -> set[str]:
    args = ["--collect-only", "-q"]
    if marker_expression is not None:
        args.extend(["-m", marker_expression])
    output = _run_pytest(*args)
    return {line for line in output.splitlines() if line.startswith("tests/") and "::" in line}


def test_loopback_marker_is_registered():
    markers = _run_pytest("--markers")

    assert "@pytest.mark.loopback:" in markers
    assert "local loopback socket" in markers


def test_loopback_partition_has_exact_known_inventory():
    assert _collect("loopback") == EXPECTED_LOOPBACK_TESTS


def test_loopback_partitions_are_disjoint_and_complete():
    ordinary = _collect()
    sandbox_safe = _collect("not loopback")
    loopback = _collect("loopback")

    assert sandbox_safe.isdisjoint(loopback)
    assert sandbox_safe | loopback == ordinary
