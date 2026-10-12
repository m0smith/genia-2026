"""Issue #1205 (child of #1067): prelude functions must not overwrite the
caller's top-level bindings.

Python-host evidence by design: the actor, `cli_parse`, `rules`, and `web`
prelude surfaces exist only on the Python reference host, so there is no shared
spec to write. The behavior itself is Genia-facing and lives in the native test
file `tests/native/prelude_local_binding_isolation.genia`; this module runs that
file once through the native test runner and reports each native test as its
own pytest case, so a regression names the function that clobbered a binding.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from genia.test_cli import run_native_tests_from_file

FIXTURE = Path("tests/native/prelude_local_binding_isolation.genia")

EXPECTED_TESTS = [
    "actor_send_leaves_h_and_c",
    "actor_call_leaves_h_c_and_reply",
    "cli_long_option_with_value_leaves_body_parts_and_canonical",
    "cli_long_flag_leaves_body_parts_and_canonical",
    "cli_short_flag_leaves_body_chars_and_canonical",
    "cli_short_flag_group_leaves_chars_option_chars_and_canonical",
    "cli_short_option_with_inline_value_leaves_canonical_and_inline_value",
    "rules_with_an_immediate_flow_leaves_flow_and_fns",
    "rules_applying_some_leaves_emitted_halted_next_ctx_and_next_record",
    "web_route_request_leaves_handler",
]


@pytest.fixture(scope="module")
def native_results():
    import contextlib
    import io

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        exit_code = run_native_tests_from_file(FIXTURE)
    outcomes: dict[str, str] = {}
    for line in buffer.getvalue().splitlines():
        for status in ("PASS", "FAIL", "ERROR"):
            if line.startswith(status + " "):
                outcomes[line[len(status) + 1 :].split()[0]] = status
    return exit_code, outcomes, buffer.getvalue()


def test_every_expected_native_test_was_discovered(native_results):
    _exit_code, outcomes, output = native_results
    assert sorted(outcomes) == sorted(EXPECTED_TESTS), output


@pytest.mark.parametrize("test_name", EXPECTED_TESTS)
def test_prelude_function_leaves_user_bindings_unchanged(native_results, test_name):
    _exit_code, outcomes, output = native_results
    assert outcomes.get(test_name) == "PASS", output


def test_native_run_reports_success(native_results):
    exit_code, _outcomes, output = native_results
    assert exit_code == 0, output
