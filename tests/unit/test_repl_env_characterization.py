"""Pin Python's host-local :env view before F2 splits entry/runtime scopes.

These colon-command observations are not the portable R26 REPL contract.
Runtime bindings intentionally remain listed during behavior-preserving P1.
"""

import io

import pytest

from genia.interpreter import repl


@pytest.mark.parametrize("ending", [":quit", None], ids=["quit", "eof"])
def test_env_lists_sorted_runtime_and_persistent_user_bindings_after_autoload(monkeypatch, ending):
    stdout = io.StringIO()
    stderr = io.StringIO()
    commands = iter([
        ":env",
        "entry_marker = 17",
        "entry_probe(parameter) = parameter + 1",
        ":env",
        "length([1, 2])",
        "entry_marker = 19",
        ":env",
        *([ending] if ending is not None else []),
    ])
    listings: list[str] = []
    previous_command = None
    output_start = 0

    def scripted_input(prompt=""):
        """Capture each completed :env response without replacing its rendering."""
        nonlocal previous_command, output_start
        assert prompt == ""
        if previous_command == ":env":
            listings.append(stdout.getvalue()[output_start:])
        output_start = len(stdout.getvalue())
        try:
            previous_command = next(commands)
        except StopIteration:
            raise EOFError from None
        return previous_command

    monkeypatch.setattr("builtins.input", scripted_input)
    monkeypatch.setattr("sys.stdin", io.StringIO())
    monkeypatch.setattr("sys.stdout", stdout)
    monkeypatch.setattr("sys.stderr", stderr)

    repl()

    assert stderr.getvalue() == ""
    assert "Genia prototype REPL" not in stdout.getvalue()
    assert len(listings) == 3
    bindings = []
    for listing in listings:
        rows = [line.split(" = ", 1) for line in listing.splitlines()]
        assert all(len(row) == 2 for row in rows)
        names = [name for name, _value in rows]
        assert names == sorted(names)
        assert len(names) == len(set(names))
        bindings.append(dict(rows))

    baseline, user, autoloaded = bindings
    for snapshot in bindings:
        assert {"stdout", "stderr", "argv", "doc", "meta", "help", "_write"} <= snapshot.keys()
        assert "parameter" not in snapshot
    assert "entry_marker" not in baseline
    assert "entry_probe" not in baseline
    assert "length" not in baseline
    assert "length" not in user
    assert user["entry_marker"] == "17"
    assert user["entry_probe"] == (
        "GeniaFunctionGroup(name='entry_probe', functions={1: <function entry_probe/1>}, "
        "docstring=None, metadata=<map 0>)"
    )
    assert autoloaded["entry_marker"] == "19"
    assert autoloaded["entry_probe"] == user["entry_probe"]
    assert "<function length/1>" in autoloaded["length"]
    assert baseline.keys() <= user.keys() <= autoloaded.keys()
