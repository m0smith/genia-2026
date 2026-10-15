"""Python-only B1/B2/B3 accessor reds (§16.1, §16.6; green-making P2-C).

All cases are A-class: physical registered E is the missing approved mechanism.
Collisions deliberately retain P1 compatibility, including A1 prelude hijacks.
"""

import re

import pytest

from genia import make_global_env, run_source
from genia.environment import Env
from tests.unit.f2_p2_support import register_entry, separated_scopes


@pytest.mark.parametrize("check", ["distinct", "parent", "registration", "runtime", "entry_frame", "module_frame", "disjoint", "autoloads", "identity", "inspection"])
def test_B1_A_registered_scope_invariant(tmp_path, check):
    """§16.6.1: each ownership invariant needs P2-C registration, not plain Env(R)."""
    s = separated_scopes(tmp_path)
    r, e, m = s.runtime, s.entry, s.module
    checks = {
        "distinct": e is not r and m is not e and m is not r,
        "parent": e.parent is r and e.rebind_parent and m.parent is r,
        "registration": all(scope.entry_scope() is e for scope in (r, e, m, Env(m))),
        "runtime": all(scope.runtime_scope() is r for scope in (r, e, m, Env(e))),
        "entry_frame": Env(e).unit_scope() is e,
        "module_frame": Env(m).unit_scope() is m,
        "disjoint": not (set(r.values) & set(e.values)),
        "autoloads": e.autoloads == {} and bool(r.autoloads),
        "identity": e.module_identity() == "<entry>" and m.module_identity() == "scope_probe",
        "inspection": Env(e).inspection_globals_scope() is e and Env(m).inspection_globals_scope() is m,
    }
    assert checks[check], f"§16.6.1 missing invariant: {check}"


def test_B1_A_second_registration_rejected():
    """§16.6.1: P2-C must reject a second E without replacing the first."""
    r = make_global_env([])
    e = register_entry(r)
    with pytest.raises((ValueError, RuntimeError)):
        r.create_entry_scope()
    assert r.entry_scope() is e


@pytest.mark.parametrize("origin", ["runtime", "entry", "module"])
def test_B1_A_entry_host_class_routes_from_any_scope(tmp_path, origin):
    """§16.6.1: P2-C routes entry-only injections to E from any supplied owner."""
    s = separated_scopes(tmp_path)
    getattr(s, origin).set_host("fixture_marker", 17, visibility="entry-only")
    assert s.entry.values["fixture_marker"] == 17
    assert "fixture_marker" not in s.runtime.values and "fixture_marker" not in s.module.values


@pytest.mark.parametrize("installation", ["public", "internal", "autoload", "owned_entry"])
def test_B1_A_late_runtime_install_and_owned_entry_injection_rejected(tmp_path, installation):
    """§16.1.6: P2-C freezes host work before registration; no authority expansion."""
    s = separated_scopes(tmp_path)
    with pytest.raises((ValueError, RuntimeError)):
        if installation == "public":
            s.entry.set_host("late_public", object(), visibility="runtime-public")
        elif installation == "internal":
            s.module.set_host_internal("late_internal", object(), visibility="runtime-public")
        elif installation == "autoload":
            s.entry.register_host_autoload("late_load", 0, "unused.genia", visibility="runtime-public")
        else:
            s.entry.set_host("map_acc", object(), visibility="entry-only")
    assert "late_public" not in s.runtime.values
    assert "late_internal" not in s.runtime.internal_values
    assert ("late_load", 0) not in s.runtime.autoloads


@pytest.mark.parametrize("name,params,body,call,result", [
    ("first", "x", "x", "first(41)", 41),
    ("map", "f, xs", "xs", "map((x) -> x, [41])", [41]),
    ("map_acc", "f, xs, acc", "acc", "map_acc((x) -> x, [], [41])", [41]),
])
@pytest.mark.parametrize("loaded", [False, True])
def test_B2_A_duplicate_collisions_keep_single_root_diagnostic(tmp_path, name, params, body, call, result, loaded):
    """§16.1.2/8 row 1 + A1: P2-C routes registered/unregistered declarations to R."""
    s = separated_scopes(tmp_path)
    arity = len(params.split(","))
    source = f"{name}({params}) = {body}"
    if loaded:
        run_source("length([1])", s.entry)
        group = s.runtime.get(name)
        with pytest.raises(TypeError, match="^" + re.escape(f"Duplicate function definition: {name}/{arity}") + "$"):
            run_source(source, s.entry)
        assert s.runtime.get(name) is group
    else:
        run_source(source, s.entry)
        assert run_source(call, s.entry) == result
        assert name in s.runtime.values and name not in s.entry.values
        with pytest.raises(TypeError, match="^" + re.escape(f"Duplicate function definition: {name}/{arity}") + "$"):
            run_source("length([1])", s.entry)
        assert not s.runtime.loading_files


@pytest.mark.parametrize("name,source,call,expected", [
    ("rows", "rows() = 71", '[rows(), rows(sheet([["a", [1]]]))]', [71, [[["a", 1]]]]),
    ("first", "first(x,y) = y", "[first([3]) |> unwrap_or(0), first(1,42)]", [3, 42]),
])
def test_B2_A_distinct_arities_merge_in_runtime(tmp_path, name, source, call, expected):
    """§16.1.6 row 2: P2-C merges the existing whole group, without P3 shadowing."""
    s = separated_scopes(tmp_path)
    group = s.runtime.get(name)
    old_arm = group.get(1)
    run_source(source, s.entry)
    assert run_source(call, s.entry) == expected
    assert s.runtime.get(name) is group and group.get(1) is old_arm
    assert name not in s.entry.values


@pytest.mark.parametrize("name,loaded", [("log", True), ("first", True), ("first", False), ("map_acc", False)])
def test_B2_A_assignment_write_through_loaded_and_unloaded(tmp_path, name, loaded):
    """§16.1.2 rows 3/4: P2-C keeps assignment/later-load behavior from P1."""
    s = separated_scopes(tmp_path)
    if loaded:
        s.runtime.get(name)
    baseline = make_global_env([])
    if loaded:
        baseline.get(name)
    run_source(f"{name} = 5", baseline)
    run_source(f"{name} = 5", s.entry)
    assert s.runtime.values[name] == 5 and name not in s.entry.values
    if not loaded:
        with pytest.raises(Exception) as old:
            run_source("length([1])", baseline)
        with pytest.raises(type(old.value)) as new:
            run_source("length([1])", s.entry)
        assert str(new.value) == str(old.value)


def test_B2_A_host_owned_write_through_and_entry_only_name(tmp_path):
    """§16.1.1/2: P2-C includes runtime host keys, while fresh names reside in E."""
    s = separated_scopes(tmp_path, prepare=lambda r: r.set_host("host_marker", 17, visibility="runtime-public"))
    run_source("host_marker = 19\nentry_marker = 23", s.entry)
    assert s.runtime.values["host_marker"] == 19
    assert s.entry.values["entry_marker"] == 23
    assert "entry_marker" not in s.runtime.values and "host_marker" not in s.entry.values


@pytest.mark.parametrize("name,source", [("first", "first(x) = x"), ("map_acc", "map_acc(f,xs,acc) = acc")])
def test_B2_A_prelude_hijack_is_pinned_for_P3_retirement(tmp_path, name, source):
    """§16.8 A1(c): P2-C preserves the measured hijack; P3 must change it deliberately."""
    s = separated_scopes(tmp_path)
    run_source(source, s.entry)
    with pytest.raises(TypeError, match=f"Duplicate function definition: {name}/"):
        run_source("map((x) -> x + 1, [41])", s.entry)


def test_B3_A_runtime_closure_cannot_read_or_write_entry_only(tmp_path):
    """§16.1.3/8(b): P2-C separates R closures and E; fallback never serves R."""
    s = separated_scopes(tmp_path, prepare=lambda r: run_source("read_entry() = zzz\nwrite_entry() = {zzz = 19\nzzz}", r))
    run_source("zzz = 17", s.entry)
    with pytest.raises(NameError, match="^Undefined name: zzz$"):
        run_source("read_entry()", s.entry)
    assert run_source("write_entry()", s.entry) == 19
    assert s.entry.get("zzz") == 17
    assert "zzz" not in s.runtime.values


def test_B3_A_runtime_owned_entry_declaration_remains_visible_to_R(tmp_path):
    """§16.1.7/A1: P2-C preserves the compatibility exception instead of P3 rules."""
    s = separated_scopes(tmp_path, prepare=lambda r: run_source("read_log() = log", r))
    run_source("log = 5", s.entry)
    assert run_source("read_log()", s.entry) == 5
    assert "log" not in s.entry.values


def test_B2_A_manifest_ownership_survives_pruning_without_conveying_authority(tmp_path):
    """§16.1.1/6/§16.7: P2-C keeps prelude ownership, while a pruned builtin loses it."""
    from hosts.python.mcp_worker_profile import prune_environment

    s = separated_scopes(tmp_path, prune=prune_environment)
    with pytest.raises((ValueError, RuntimeError)):
        s.entry.set_host("read_file", object(), visibility="entry-only")
    marker = object()
    s.entry.set_host("secret_get", marker, visibility="entry-only")
    assert s.entry.values["secret_get"] is marker and "secret_get" not in s.runtime.values
    assert "read_file" not in s.runtime.values


@pytest.mark.parametrize("form", ["pattern", "import", "open", "use", "metadata"])
def test_B2_A_all_entry_binding_forms_route_runtime_owned_names(tmp_path, form):
    """§16.1.2: P2-C routes patterns/imports/open/use/metadata, not just function defs."""
    s = separated_scopes(tmp_path)
    (tmp_path / "binding_base.genia").write_text('open map_acc("base", x) = x\nprobe() = 41', encoding="utf-8")
    (tmp_path / "binding_extension.genia").write_text('import binding_base\nextend binding_base.map_acc("ext", x) = x', encoding="utf-8")
    source = {
        "pattern": "pattern map_acc(value) = some(value)",
        "import": "import binding_base as map_acc",
        "open": 'open map_acc("entry", x) = x',
        "use": "import binding_base\nimport binding_extension\nuse map_acc from binding_base with binding_extension",
        "metadata": '@doc "owned docs"\nmap_acc(x) = x',
    }[form]
    run_source(source, s.entry, filename=str(tmp_path / "entry.genia"))
    assert "map_acc" in s.runtime.values and "map_acc" not in s.entry.values
    assert s.entry.get("map_acc") is s.runtime.get("map_acc")
    if form == "metadata":
        assert s.runtime.get_metadata("map_acc").get("doc") == "owned docs"
    if form == "use":
        assert run_source('map_acc("base", 41)', s.entry) == 41


def test_B1_A_registration_must_be_owned_by_runtime():
    """§16.6.1: P2-C registration is an operation on R, never a lexical child."""
    r = make_global_env([])
    child = Env(r)
    if not callable(getattr(child, "create_entry_scope", None)):
        register_entry(r)  # Emit the prescribed missing-API marker on P1.
    with pytest.raises((ValueError, RuntimeError)):
        child.create_entry_scope()
    assert r.entry_scope() is r, "invalid registration changed the runtime entry owner"
