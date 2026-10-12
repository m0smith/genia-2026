"""Python host orchestration must select entry owners through the P1 seam."""

from types import SimpleNamespace

from genia.builtins import make_global_env
from genia.interpreter import _resolve_program_result, run_source
from genia.test_cli import discover_test_units, make_test_env


def test_main_selection_uses_entry_owner_and_entry_argv():
    entry = make_global_env(cli_args=["kept"])
    run_source("main(args) = args", entry)
    outer = make_global_env(cli_args=["wrong"])
    outer.entry_scope = lambda: entry
    assert _resolve_program_result(71, outer) == ["kept"]


def test_native_discovery_uses_entry_values_metadata_and_registrar():
    entry, registered = make_test_env()
    run_source('@test "entry annotation"\nentry_test() = true\ntest("legacy", () -> true)', entry)
    outer = make_global_env()
    outer.entry_scope = lambda: entry
    units = discover_test_units(outer)
    assert [unit.name for unit in units] == ["legacy", "entry_test"]
    assert units[0] is registered[0]


def test_serve_discovery_receives_entry_owner(tmp_path, monkeypatch):
    import genia.interpreter as interpreter
    import genia.server_config_binding as config
    import genia.server_route_binding as routes

    program = tmp_path / "empty.genia"
    program.write_text("17", encoding="utf-8")
    outer = make_global_env()
    entry = make_global_env()
    outer.entry_scope = lambda: entry
    monkeypatch.setattr(interpreter, "make_global_env", lambda: outer)
    seen = []

    def discover(_nodes, env, **_kwargs):
        seen.append(env)
        return SimpleNamespace(binding=None, diagnostics=[])

    monkeypatch.setattr(config, "discover_entry_file_server_config_binding", discover)
    monkeypatch.setattr(routes, "discover_entry_file_route_bindings", discover)
    assert interpreter._run_serve_file(str(program)) == 1
    assert seen == [entry, entry]
