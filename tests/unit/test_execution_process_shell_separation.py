"""FAILING-TEST PHASE — Group K: shell separation regression.

Proves `execution.process` does not become a portable wrapper around
`$(...)` (contract §16: "`execution.process != execution.shell` is a
contract invariant"; design §10/§22). Uses argv values containing
shell-significant characters and proves the child receives them literally,
as exact separate elements, with no shell interpreting them.

Also proves resolution has no portable PATH-lookup fallback: an unbound
symbol never silently resolves through a PATH search.

`execution.process` is NOT implemented yet; every test fails today with
`ModuleNotFoundError` -- the correct RED state for this phase.
"""

from __future__ import annotations

from tests.fixtures.process_fixtures import echo_argv_nul_joined


_SHELL_SIGNIFICANT_ARGS = ["*", "$HOME", ";", "|", ">", "a b c", "$(whoami)", "`id`", "&&"]


def _launch(argv: list[str], timeout_ms: int = 5000):
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    executable, *args = argv
    return module.launch_process(executable, args, timeout_ms)


def test_shell_significant_argv_elements_are_received_literally():
    """The fixture child echoes back exactly the argv elements it received,
    NUL-joined. If any layer invoked a shell, expanded `$HOME`/`*`, ran a
    command substitution, or split on `;`/`|`/`>` , the echoed elements
    would not exactly match what was requested.
    """
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    echo_argv = echo_argv_nul_joined()
    executable = echo_argv[0]
    fixed_args = echo_argv[1:]
    result = _launch([executable, *fixed_args, *_SHELL_SIGNIFICANT_ARGS])

    assert isinstance(result, module.ProcessTransportResult)
    received = result.stdout.decode("utf-8").split("\x00")
    # The echoed elements are everything after the fixture's own two -c
    # script arguments: exactly _SHELL_SIGNIFICANT_ARGS, unmodified.
    assert received == _SHELL_SIGNIFICANT_ARGS


def test_a_single_argv_element_with_embedded_spaces_is_not_split():
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    echo_argv = echo_argv_nul_joined()
    executable = echo_argv[0]
    fixed_args = echo_argv[1:]
    spaced_element = "this is one single argument"
    result = _launch([executable, *fixed_args, spaced_element, "second"])

    assert isinstance(result, module.ProcessTransportResult)
    received = result.stdout.decode("utf-8").split("\x00")
    assert received == [spaced_element, "second"]


def test_glob_characters_are_not_expanded():
    """`*` must reach the child as the literal one-character string `*`, not
    expanded against the filesystem (contract §7: "no ... glob expansion").
    """
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    echo_argv = echo_argv_nul_joined()
    executable = echo_argv[0]
    fixed_args = echo_argv[1:]
    result = _launch([executable, *fixed_args, "*"])

    assert isinstance(result, module.ProcessTransportResult)
    assert result.stdout == b"*"


def test_empty_string_argument_is_preserved_exactly():
    """Contract §7: "Empty strings ... are preserved exactly." An empty
    argv element is not the same as omitting it.
    """
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    echo_argv = echo_argv_nul_joined()
    executable = echo_argv[0]
    fixed_args = echo_argv[1:]
    result = _launch([executable, *fixed_args, "before", "", "after"])

    assert isinstance(result, module.ProcessTransportResult)
    received = result.stdout.decode("utf-8").split("\x00")
    assert received == ["before", "", "after"]


def test_shell_metacharacter_argv_element_cannot_perform_command_injection(tmp_path):
    """The strongest possible proof of "no shell invocation": a `shlex.quote`
    -aware `shell=True` implementation could still pass every literal-
    preservation test above while remaining a genuine shell invocation
    (`/bin/sh -c '<quoted argv>'`), violating contract §4/§16. This test
    instead proves the *absence of a shell-interpretable side effect*: an
    argv element that would create a marker file if a shell ever evaluated
    it (`; touch <marker> ;`) must both (a) be echoed back byte-for-byte and
    (b) never actually create that file, regardless of how the launcher
    constructs the child process.
    """
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    marker = tmp_path / "shell_injection_proof_978.marker"
    assert not marker.exists()

    injection_attempt = f"; touch {marker} ; echo pwned"
    echo_argv = echo_argv_nul_joined()
    executable = echo_argv[0]
    fixed_args = echo_argv[1:]

    result = _launch([executable, *fixed_args, injection_attempt])

    assert isinstance(result, module.ProcessTransportResult)
    assert result.stdout.decode("utf-8") == injection_attempt
    assert not marker.exists(), (
        "a marker file was created -- this argv element was evaluated by a "
        "shell (directly or via shlex-quoted shell=True), which is exactly "
        "what contract §4/§16 forbid even though character-preservation "
        "tests alone would not catch it"
    )


def test_no_portable_path_search_fallback_at_resolution():
    """An unbound symbol must never be "helpfully" resolved by searching the
    host PATH -- resolution is a private static dict lookup only (contract
    §6, design §5). This is exercised at the composition boundary since
    PATH search would be a *resolution*-layer shortcut, not a
    transport-layer one.
    """
    from tests.fixtures.execution_process_helpers import (
        make_capability,
        make_request,
        process_execution_module,
        refusing_launcher,
    )
    from genia.values import symbol

    module = process_execution_module()
    # "python3" (or similar) is very likely resolvable via PATH on the test
    # host -- if resolution ever fell back to PATH search, binding nothing
    # explicitly for this symbol but still succeeding would prove the leak.
    capability = make_capability(bindings={}, launcher=refusing_launcher())
    request = make_request(executable=symbol("python3"), args=[], timeout_ms=1000)

    result = module.perform_process_execution(capability, request)

    assert result.reason == "process-executable-unavailable"
