"""Python-only F2/P2-E temporary fallback tests (contract 11, 16.3; issues #1067, #1229, #1230).

Adversarial coverage beyond the P2-B B4 cases: eligibility boundaries, strict mode,
legacy roots, pruning, protected values, closures and higher-order reads. Python host
internals only; the fallback is a temporary Python-host mechanism, never portable
language behavior and never claimed for any other host.
"""

import io

import pytest

from genia import make_global_env, run_source
from hosts.python.mcp_worker_profile import prune_environment
from tests.unit.f2_p2_support import load_program_module, separated_scopes

PROTECTED = 'protected_value = secret_get(config_provider([{kind: quote(values), values: {KEY: "P2_E_PROTECTED_SENTINEL"}}]) |> unwrap_or(none), "KEY", quote(use)) |> unwrap_or(none)'


@pytest.fixture(autouse=True)
def default_fallback_mode(monkeypatch):
    """These tests exercise the default (non-strict) mode unless a case sets the switch."""
    monkeypatch.delenv("GENIA_STRICT_MODULE_SCOPE", raising=False)


def test_only_module_identifier_reads_of_entry_resident_names_fall_back(tmp_path, capsys):
    """Entry code, prelude code and unknown names get no fallback and record no event."""
    s = separated_scopes(tmp_path, prepare=lambda r: run_source("prelude_reader() = entry_marker", r))
    run_source("entry_marker = 17\nlog = 5", s.entry)
    module = s.load("runtime_owned() = log\nunknown() = never_defined\nentry_ok() = 1", "eligibility")
    assert run_source("entry_marker", s.entry) == 17
    assert module.exports["runtime_owned"]() == 5
    with pytest.raises(NameError, match="^Undefined name: entry_marker$"):
        run_source("prelude_reader()", s.entry)
    with pytest.raises(NameError, match="^Undefined name: never_defined$"):
        module.exports["unknown"]()
    assert s.runtime.fallback_events == set()
    assert capsys.readouterr().err == ""


def test_event_pairs_are_module_identity_and_name_with_single_value_free_warning(tmp_path, capsys):
    """The event set holds exactly the distinct pairs; one warning per pair, to the runtime stderr sink."""
    s = separated_scopes(tmp_path)
    run_source('entry_a = "VALUE_SENTINEL_A"\nentry_b = 1', s.entry)
    module = s.load("one() = [entry_a, entry_a]\ntwo() = entry_b", "pair_module")
    module.exports["one"]()
    module.exports["two"]()
    module.exports["two"]()
    assert s.runtime.fallback_events == {("pair_module", "entry_a"), ("pair_module", "entry_b")}
    err = capsys.readouterr().err
    lines = err.strip().splitlines()
    assert len(lines) == 2 and all(line.count("TEMPORARY COMPATIBILITY FALLBACK") == 1 and "#1230" in line for line in lines)
    assert "VALUE_SENTINEL_A" not in err and str(tmp_path) not in err


def test_strict_mode_denies_with_ordinary_name_error_and_records_nothing(tmp_path, monkeypatch, capsys):
    """Strict mode raises the ordinary NameError and leaves no event or warning."""
    monkeypatch.setenv("GENIA_STRICT_MODULE_SCOPE", "1")
    s = separated_scopes(tmp_path)
    run_source("entry_marker = 17", s.entry)
    module = s.load("probe() = entry_marker", "strict_module")
    assert s.runtime.strict_module_scope is True
    with pytest.raises(NameError) as failure:
        module.exports["probe"]()
    assert str(failure.value) == "Undefined name: entry_marker" and type(failure.value) is NameError
    assert s.runtime.fallback_events == set() and capsys.readouterr().err == ""


@pytest.mark.parametrize("value,expected", [("1", True), ("0", False), ("true", False), ("", False)])
def test_strict_switch_accepts_only_exact_one(monkeypatch, value, expected):
    """The switch is exactly GENIA_STRICT_MODULE_SCOPE=1; any other spelling stays non-strict."""
    monkeypatch.setenv("GENIA_STRICT_MODULE_SCOPE", value)
    assert make_global_env([]).strict_module_scope is expected


def test_caller_created_single_root_has_no_fallback_and_no_events(capsys):
    """A root with no registered entry never uses the fallback: module reads of root names are ordinary."""
    root = make_global_env([])
    run_source("shared_name = 3", root)
    assert root.fallback_events == set()
    assert root.runtime_scope()._entry is None and capsys.readouterr().err == ""


def test_lambda_and_closure_ownership_decide_eligibility(tmp_path):
    """A module lambda reading an entry name is an eligible module read; an entry closure given to a module is not."""
    s = separated_scopes(tmp_path)
    run_source("entry_marker = 7\nentry_closure() = entry_marker", s.entry)
    module = s.load("via_lambda() = map((x) -> x + entry_marker, [1])\ncall(f) = f()", "closure_module")
    assert module.exports["via_lambda"]() == [8]
    assert s.runtime.fallback_events == {("closure_module", "entry_marker")}
    s.runtime.fallback_events.clear()
    assert run_source("closure_module.call(entry_closure)", s.entry) == 7
    assert s.runtime.fallback_events == set()


def test_fallback_never_reaches_denied_capabilities_after_pruning(tmp_path):
    """Pruned builtin/autoload capabilities stay undefined for modules; no entry binding is conjured."""
    s = separated_scopes(tmp_path, prune=prune_environment)
    module = s.load("a() = secret_get\nb() = read_file\nc() = http_operation", "pruned_module")
    for name in ("a", "b", "c"):
        with pytest.raises(NameError, match="^Undefined name: "):
            module.exports[name]()
    assert s.runtime.fallback_events == set()


def test_entry_own_value_named_like_a_denied_capability_is_not_the_capability(tmp_path):
    """An entry program's own value with a denied builtin's name is returned as that value, never as the capability."""
    s = separated_scopes(tmp_path, prune=prune_environment)
    run_source("secret_get = 5", s.entry)
    module = s.load("probe() = secret_get", "lookalike_module")
    assert module.exports["probe"]() == 5
    assert "secret_get" not in s.runtime.values and callable(s.runtime.values.get("secret_get")) is False


def test_protected_values_stay_protected_and_never_enter_warnings(tmp_path, capsys):
    """The fallback returns the same protected carrier (as the shared root did); rendering and warnings leak nothing."""
    s = separated_scopes(tmp_path)
    run_source(PROTECTED, s.entry)
    module = s.load("probe() = protected_value\nshown() = display(protected_value)", "protected_module")
    carrier = module.exports["probe"]()
    assert carrier is s.entry.get("protected_value")
    assert "P2_E_PROTECTED_SENTINEL" not in str(module.exports["shown"]())
    err = capsys.readouterr().err
    assert "P2_E_PROTECTED_SENTINEL" not in err and "protected_value" in err
    assert all("P2_E_PROTECTED_SENTINEL" not in repr(pair) for pair in s.runtime.fallback_events)


def test_inspection_and_host_lookup_never_trigger_the_fallback(tmp_path):
    """REPL/debugger inspection views, binding_owner and host get are not identifier evaluation."""
    s = separated_scopes(tmp_path)
    run_source("entry_marker = 17", s.entry)
    module = s.load("probe() = entry_marker", "inspect_module")
    scope = module.exports["probe"].get(0).closure
    assert "entry_marker" not in scope.inspection_bindings() and scope.binding_owner("entry_marker") is None
    with pytest.raises(NameError):
        scope.get("entry_marker")
    assert s.runtime.fallback_events == set()


def test_warning_uses_the_runtime_stderr_sink_when_configured(tmp_path):
    """A host-supplied stderr stream receives the warning, not the process stream."""
    from genia.test_cli import make_test_env

    stream = io.StringIO()
    entry, _ = make_test_env(stderr_stream=stream)
    run_source("entry_marker = 1", entry)
    module = load_program_module(tmp_path, entry, "probe() = entry_marker", "sink_module")
    module.exports["probe"]()
    assert "TEMPORARY COMPATIBILITY FALLBACK" in stream.getvalue()


def test_a_failing_warning_stream_never_changes_the_program_result(tmp_path):
    """A closed or broken stderr stream is ignored; the fallback still returns the entry value."""

    class BrokenStream(io.StringIO):
        """A stream whose writes fail the way a closed pipe does."""

        def write(self, text):
            """Fail every write."""
            raise OSError("closed")

    from genia.test_cli import make_test_env

    entry, _ = make_test_env(stderr_stream=BrokenStream())
    run_source("entry_marker = 41", entry)
    module = load_program_module(tmp_path, entry, "probe() = entry_marker", "broken_stream_module")
    assert module.exports["probe"]() == 41
    assert entry.runtime_scope().fallback_events == {("broken_stream_module", "entry_marker")}
