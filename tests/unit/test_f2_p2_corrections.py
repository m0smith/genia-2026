"""Python-only F2/P2 pre-merge correction regressions (issue #1067, tracker #1229, debt #1238, retirement #1230).

Covers Python-host internals only: the entry-declaration record on `Env`. None of this is portable
language behavior, so there is no shared-spec twin.

- R01: `entry_declared_runtime_owned` records successful declarations only.

The R15/R16 fallback event-accounting cases were removed with the temporary compatibility fallback (#1230).
"""

import pytest

from genia import make_program_env, run_source
from tests.unit.f2_p2_support import separated_scopes


def _program_with_list_prelude():
    """Return a program environment whose list prelude is loaded, so `first` and `length` are bound runtime names.

    Failure cases below need an existing runtime-owned binding to collide with.
    """
    entry = make_program_env([])
    run_source("length([1])", entry)  # loads the list prelude so `first` is a bound runtime name
    return entry


# ---------------------------------------------------------------- R01 -------------------------


@pytest.mark.parametrize(
    "source,error,name",
    [
        ("first(x) = x", TypeError, "first"),
        ("open log(x) = x", Exception, "log"),
    ],
)
def test_r01_failed_declaration_of_existing_runtime_name_is_not_recorded(source, error, name):
    entry = _program_with_list_prelude()
    runtime = entry.runtime_scope()
    before = runtime.values[name]
    with pytest.raises(error):
        run_source(source, entry)
    assert name not in entry.entry_declared_runtime_owned
    assert name not in entry.inspection_bindings()
    assert entry.binding_owner(name) is None
    assert runtime.values[name] is before


def test_r01_failed_assignment_and_failed_function_clause_are_not_recorded(tmp_path):
    def prepare(runtime):
        """Pre-registration host setup: a non-assignable and an ordinary non-function runtime binding."""
        runtime.set("fixed_value", 1, assignable=False)
        runtime.set("plain_value", 2)

    s = separated_scopes(tmp_path, prepare=prepare)
    entry = s.entry
    with pytest.raises(NameError):
        run_source("fixed_value = 5", entry)
    with pytest.raises(TypeError):
        run_source("plain_value(x) = x", entry)
    assert entry.entry_declared_runtime_owned == set()
    assert "fixed_value" not in entry.inspection_bindings()
    assert "plain_value" not in entry.inspection_bindings()
    assert s.runtime.values["fixed_value"] == 1 and s.runtime.values["plain_value"] == 2


def test_r01_failed_declaration_retains_its_original_error_text():
    entry = _program_with_list_prelude()
    with pytest.raises(TypeError) as first:
        run_source("first(x) = x", entry)
    again = _program_with_list_prelude()
    with pytest.raises(TypeError) as second:
        run_source("first(x) = x", again)
    assert str(first.value) == str(second.value) != ""


@pytest.mark.parametrize(
    "source,name",
    [
        ("first = 1", "first"),
        ("first(a, b, c, d, e) = 1", "first"),
        ("open_probe_free = 1\nmap_acc(a, b, c, d) = 1", "map_acc"),
    ],
)
def test_r01_successful_declaration_is_recorded_and_visible(source, name):
    entry = _program_with_list_prelude()
    run_source(source, entry)
    assert name in entry.entry_declared_runtime_owned
    assert name in entry.inspection_bindings()
    assert entry.binding_owner(name) is entry.runtime_scope()


def test_r01_nested_successful_declaration_survives_a_later_failed_one():
    entry = _program_with_list_prelude()
    with pytest.raises(TypeError):
        run_source("map_acc(a, b, c, d) = 1\nfirst(x) = x", entry)
    assert "map_acc" in entry.entry_declared_runtime_owned
    assert "first" not in entry.entry_declared_runtime_owned


@pytest.mark.parametrize("source", ["read_file = 1", "read_file(x) = x", "open read_file(x) = x"])
def test_r01_mcp_denied_name_cannot_be_declared_restored_or_recorded(tmp_path, source):
    from hosts.python.mcp_worker_profile import prune_environment

    s = separated_scopes(tmp_path, prune=prune_environment)
    assert "read_file" not in s.runtime.values
    with pytest.raises(ValueError, match="restricted execution"):
        run_source(source, s.entry)
    assert "read_file" not in s.runtime.values and "read_file" not in s.entry.values
    assert "read_file" not in s.entry.entry_declared_runtime_owned
    assert "read_file" not in s.entry.inspection_bindings()


def test_r01_annotation_error_after_a_successful_binding_leaves_the_binding_and_its_record():
    """Declarations are not transactional: annotation processing runs after the bind, so the record stays."""
    entry = _program_with_list_prelude()
    with pytest.raises(TypeError):
        run_source("@doc 1\nfirst(a, b, c, d, e) = 1", entry)
    assert "first" in entry.entry_declared_runtime_owned
    assert entry.runtime_scope().get("first").get(5) is not None
