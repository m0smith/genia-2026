"""Python-host B3–B6 behavioral reds on existing program construction paths.

§16.2 reflection observations are shared-spec candidates (doc_help,
multi_file_eval); this file observes host integration, not portable authority.
Module read denial (the removed temporary fallback, issue #1230) is Python-observed here; reflection/eval is P2-D.
No manually allocated child pretends to be a registered entry.
"""

import pytest

from genia import run_source
from genia.values import GeniaOptionNone
from tests.unit.f2_p2_support import load_program_module, program_env, separated_scopes


@pytest.mark.parametrize("kind", ["call", "top_level", "contribution"])
def test_B4_B_module_read_rejects_entry_binding(tmp_path, kind):
    """§4.2/5: a module free-name read of an entry binding is the ordinary NameError at every read site."""
    entry = program_env()
    run_source("entry_marker = 5", entry)
    with pytest.raises(NameError, match="^Undefined name: entry_marker$"):
        if kind == "contribution":
            (tmp_path / "base.genia").write_text('open dispatch("base", x) = x', encoding="utf-8")
            load_program_module(tmp_path, entry, 'import base\nextend base.dispatch("ext", x) = entry_marker', "extension")
            run_source('import base\nuse dispatch from base with extension\ndispatch("ext", 41)', entry, filename=str(tmp_path / "entry.genia"))
        else:
            module = load_program_module(tmp_path, entry, "probe() = entry_marker" if kind == "call" else "snapshot = entry_marker\nprobe() = snapshot")
            module.exports["probe"]()
    assert not entry.runtime_scope().loading_modules


def test_B4_B_host_get_never_resolves_entry_binding(tmp_path):
    """Host Env.get from a module scope never reaches an entry binding."""
    e = program_env()
    run_source("entry_marker = 17", e)
    module = load_program_module(tmp_path, e, "probe() = entry_marker")
    scope = module.exports["probe"].get(0).closure
    with pytest.raises(NameError, match="^Undefined name: entry_marker$"):
        scope.get("entry_marker")


@pytest.mark.parametrize("reflection", ["doc", "meta", "help"])
def test_B5_B_module_local_reflection_resolves_actual_owner(tmp_path, reflection):
    """§16.2/§7.1: P2-D binds reflection at identifier evaluation in actual M."""
    output = []
    e = program_env(output_handler=output.append)
    module = load_program_module(tmp_path, e, f'@doc "module documentation"\nown_helper(x) = x\nprobe() = {reflection}("own_helper")')
    result = module.exports["probe"]()
    if reflection == "doc":
        assert result == "module documentation"
    elif reflection == "meta":
        assert result is module.exports["own_helper"].metadata
    else:
        assert "module documentation" in "".join(output)


@pytest.mark.parametrize("reflection", ["doc", "meta", "help"])
def test_B5_B_module_reflection_never_falls_back_to_entry(tmp_path, reflection):
    """§16.2: module reflection never reaches entry metadata."""
    output = []
    e = program_env(output_handler=output.append)
    run_source('@doc "ENTRY_DOCUMENTATION_SENTINEL"\nentry_subject(x) = x', e)
    module = load_program_module(tmp_path, e, f'probe() = {reflection}("entry_subject")')
    result = module.exports["probe"]()
    if reflection == "help":
        assert "No public helper or runtime name found: entry_subject" in "".join(output)
        assert "ENTRY_DOCUMENTATION_SENTINEL" not in "".join(output)
    else:
        assert isinstance(result, GeniaOptionNone), "module reflection exposed E metadata"


@pytest.mark.parametrize("reflection", ["doc", "meta", "help"])
def test_B5_B_frame_parameter_takes_precedence(tmp_path, reflection):
    """§16.2 change 3: P2-D starts at frame; parameter value wins over R's map."""
    output = []
    e = program_env(output_handler=output.append)
    run_source('@doc "parameter documentation"\nlocal_subject(x) = x', e)
    module = load_program_module(tmp_path, e, f'probe(map) = {reflection}("map")')
    result = module.exports["probe"](e.get("local_subject"))
    if reflection == "doc":
        assert isinstance(result, GeniaOptionNone), "parameter has no binding @doc; do not use R map metadata"
    elif reflection == "meta":
        assert result.count() == 0, "parameter binding has no metadata; do not use R map metadata"
    else:
        assert "parameter documentation" in "".join(output)


@pytest.mark.parametrize("path", ["indirect", "alias", "transfer", "higher_order"])
def test_B5_B_module_evaluation_binding_survives_indirection(tmp_path, path):
    """§7.1/§16.2: P2-D carries M binding through map, aliases and returned values."""
    e = program_env()
    bodies = {
        "indirect": 'probe() = map(doc, ["own_helper"])',
        "alias": 'alias = doc\nprobe() = alias("own_helper")',
        "transfer": 'probe() = doc',
        "higher_order": 'apply_reflection(f) = f("own_helper")\nprobe() = apply_reflection(doc)',
    }
    module = load_program_module(tmp_path, e, '@doc "module documentation"\nown_helper(x) = x\n' + bodies[path])
    result = module.exports["probe"]()
    if path == "transfer":
        result = result("own_helper")
    assert result == (["module documentation"] if path == "indirect" else "module documentation")


@pytest.mark.parametrize("from_module", [False, True])
def test_B6_B_empty_env_does_not_implicitly_expose_entry(tmp_path, from_module):
    """§16.4: P2-D bases eval on R; define is the explicit migration path."""
    e = program_env()
    run_source("entry_f(x) = x + 1", e)
    expression = "eval(quote(entry_f(41)), empty_env())"
    if from_module:
        module = load_program_module(tmp_path, e, f"probe() = {expression}")
        evaluate = module.exports["probe"]
    else:
        def evaluate():
            """Execute the quoted expression through the real entry program path."""
            return run_source(expression, e)
    with pytest.raises(NameError, match="^Undefined name: entry_f$"):
        evaluate()


def test_B3_B_runtime_closure_cannot_read_entry_binding():
    """§16.1.3: P2-C removes shared-root leak through an actual host-built program."""
    e = program_env()
    r = e.runtime_scope()
    run_source("runtime_reader() = entry_marker", r)
    run_source("entry_marker = 17", e)
    with pytest.raises(NameError, match="^Undefined name: entry_marker$"):
        run_source("runtime_reader()", e)


def test_B6_A_explicit_define_and_runtime_names_keep_working(tmp_path):
    """§16.4: physical integration (A); P2-D changes only implicit E visibility."""
    s = separated_scopes(tmp_path)
    run_source("entry_f(x) = x + 1", s.entry)
    assert run_source("eval(quote(entry_f(41)), define(empty_env(), quote(entry_f), entry_f))", s.entry) == 42
    # P2-D test repair (reviewed): the metacircular evaluator supports neither lambda nor
    # list syntax, so P1 failed this line for a reason unrelated to scope. A runtime-owned
    # prelude function with a simple argument keeps the "runtime names remain available" intent.
    assert run_source("eval(quote(inc(41)), empty_env())", s.entry) == 42
    run_source("log = 5", s.entry)
    assert run_source("eval(quote(log), empty_env())", s.entry) == 5
    base = run_source("empty_env()", s.entry).env
    assert base.parent is s.runtime and base.parent is not s.entry


@pytest.mark.parametrize("case", ["module_reflection_owns_its_lookup", "frame_parameter_precedes_runtime_name"])
def test_B5_B_native_reflection_twin(case, capsys):
    """§16.2: P2-D native Genia observations use the actual host test runner."""
    from genia.test_cli import run_native_tests_from_file
    from tests.unit.f2_p2_support import ROOT

    result = run_native_tests_from_file(ROOT / "tests/native/f2_p2_b_reflection.genia")
    output = capsys.readouterr().out
    assert f"PASS {case}" in output, output
    assert result in (0, 1), output  # Individual status is independent of its sibling.


@pytest.mark.parametrize("path", ["entry", "entry_alias", "entry_indirect", "transfer_to_module", "user_rebound", "host_direct", "prelude"])
def test_B5_A_reflection_binding_identity_and_explicit_grants(tmp_path, path):
    """§7.1/§16.2: P2-D marking is value-based, preserving explicit grants/identity."""
    s = separated_scopes(tmp_path, prepare=lambda r: run_source("runtime_probe() = doc(\"entry_subject\")", r))
    run_source('@doc "entry documentation"\nentry_subject(x) = x', s.entry)
    s.load('probe(f) = f("entry_subject")', "grant_module")
    group = s.entry.get("entry_subject")
    if path == "entry":
        assert run_source('doc("entry_subject")', s.entry) == "entry documentation"
    elif path == "entry_alias":
        assert run_source('alias = doc\nalias("entry_subject")', s.entry) == "entry documentation"
    elif path == "entry_indirect":
        assert run_source('map(doc, ["entry_subject"])', s.entry) == ["entry documentation"]
    elif path == "transfer_to_module":
        assert run_source("grant_module.probe(doc)", s.entry) == "entry documentation"
    elif path == "user_rebound":
        assert run_source('doc = (name) -> "user doc"\nalias = doc\n[doc("entry_subject"), alias("entry_subject")]', s.entry) == ["user doc", "user doc"]
    elif path == "host_direct":
        public = s.runtime.get("doc")
        assert s.entry.get("doc") is public and s.module.get("doc") is public
        assert isinstance(public("entry_subject"), GeniaOptionNone)
    else:
        assert isinstance(run_source("runtime_probe()", s.entry), GeniaOptionNone)
    assert s.entry.get("entry_subject") is group


@pytest.mark.parametrize("operation", ["write", "export", "reflection", "runtime_owned", "local", "eval", "host_get"])
def test_B4_A_module_scope_operations_preserve_module_isolation(tmp_path, operation):
    """Writes, exports, reflection, runtime-owned reads, locals, eval and host get keep module scope isolated from E."""
    s = separated_scopes(tmp_path)
    run_source('@doc "entry docs"\nentry_subject(x) = x\nentry_marker = 17\nlog = 5', s.entry)
    source = {
        "write": "probe() = {entry_marker = 19\nentry_marker}",
        "export": "probe() = 41",
        "reflection": 'probe() = [doc("entry_subject"), meta("entry_subject")]',
        "runtime_owned": "probe() = log",
        "local": "probe(entry_marker) = entry_marker",
        "eval": "probe() = eval(quote(entry_marker), empty_env())",
        "host_get": "probe() = entry_marker",
    }[operation]
    module = s.load(source, "exclusion")
    scope = module.exports["probe"].get(1 if operation == "local" else 0).closure
    if operation == "write":
        assert module.exports["probe"]() == 19
        assert s.entry.get("entry_marker") == 17
    elif operation == "export":
        assert "entry_marker" not in module.exports and "log" not in module.exports
    elif operation == "reflection":
        assert all(isinstance(value, GeniaOptionNone) for value in module.exports["probe"]())
    elif operation == "runtime_owned":
        assert module.exports["probe"]() == 5
    elif operation == "local":
        assert module.exports["probe"](23) == 23
    else:
        with pytest.raises(NameError, match="^Undefined name: entry_marker$"):
            scope.get("entry_marker") if operation == "host_get" else module.exports["probe"]()


@pytest.mark.parametrize("name", ["doc", "meta", "help"])
def test_B5_A_scope_bound_callable_identity_is_stable(tmp_path, name):
    """§16.2/P1 design §6: P2-D caches evaluation-bound values per value and scope."""
    s = separated_scopes(tmp_path)
    first = run_source(name, s.entry)
    assert run_source(name, s.entry) is first
    assert run_source(f"alias = {name}\nalias", s.entry) is first
    module = s.load(f"stored = {name}\nprobe() = stored", "identity_module")
    other = module.exports["probe"]()
    assert other is module.exports["probe"]()
    assert other is not first
