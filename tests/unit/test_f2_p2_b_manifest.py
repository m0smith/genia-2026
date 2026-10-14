"""Python-only B2/B8 source and ownership gates (§16.1.1, §16.6.2, A3).

The manifest proof parses actual top-level prelude declarations; it never
derives ownership from the autoload registry alone. P2-C makes these green.
"""

import ast
from collections import Counter

import pytest

from genia import make_global_env, run_source
from genia.ast_nodes import AnnotatedNode, Assign, FuncDef, NamedPatternDef
from genia.interpreter import Parser, lex
from tests.unit.f2_p2_support import ROOT, register_entry


def prelude_declarations(runtime):
    """Parse every autoload target, returning declared names and explicit paths.

    Parsing is inert. An annotated declaration is unwrapped, and assignments
    count alongside functions/patterns. Import-only packaged modules are excluded.
    """
    names = set()
    paths = set(runtime.autoloads.values())
    for logical in paths:
        path = ROOT / "src/genia" / logical
        source = path.read_text(encoding="utf-8")
        for node in Parser(lex(source), source=source, filename=str(path)).parse_program():
            while isinstance(node, AnnotatedNode):
                node = node.target
            if isinstance(node, (Assign, FuncDef, NamedPatternDef)):
                names.add(node.name)
    return names, paths


def test_B2_A_every_prelude_declaration_routes_to_runtime_without_eager_load():
    """§16.1.1/8(c): P2-C manifest drift gate includes assignments + unregistered helpers.

    The test observes routing, leaving the manifest's storage/API to design.
    Autoload-registration-only routing fails on map_acc and the other helpers.
    """
    r = make_global_env([])
    names, paths = prelude_declarations(r)
    registered = {name for name, _arity in r.autoloads}
    assert registered <= names
    assert "map_acc" in names - registered
    assert "pi" in names  # An assignment, not just function definitions.
    assert not any(path.endswith(("web.genia", "resource.genia", "execution.genia")) for path in paths)
    assert not r.loaded_files
    e = register_entry(r)
    assert not r.loaded_files, "construction must not evaluate prelude sources"
    missing = []
    for name in sorted(names - set(r.values)):
        run_source(f"{name} = 17", e)
        if r.values.get(name) != 17 or name in e.values:
            missing.append(name)
    assert not missing, "§16.1.1 manifest missed top-level declarations: " + ", ".join(missing)
    assert not r.loaded_files


PROGRAM_SITES = [
    ("src/genia/interpreter.py", "repl", 0),
    ("src/genia/interpreter.py", "run_debug_stdio", 0),
    ("src/genia/interpreter.py", "_run_serve_file", 0),
    ("src/genia/interpreter.py", "_run_execution_mode", 0),
    ("src/genia/interpreter.py", "_run_execution_mode", 1),
    ("src/genia/interpreter.py", "_run_execution_mode", 2),
    ("src/genia/test_cli.py", "make_test_env", 0),
    ("hosts/python/exec_model_fixture.py", "_build_env", 0),
    ("hosts/python/exec_r12_grounded_fixture.py", "_build_env", 0),
    ("hosts/python/exec_r25_concurrency_fixture.py", "_build_env", 0),
    ("hosts/python/exec_ollama_chat.py", "main", 0),
    ("hosts/python/mcp_worker.py", "execute_source", 0),
    ("hosts/python/mcp_host.py", "main", 0),
]


@pytest.mark.parametrize("path,function,index", PROGRAM_SITES)
def test_B8_B_program_constructor_guard_no_raw_runtime_factory(path, function, index):
    """§16.6.2/A3: P2-C routes all 13 constructors through one R/E construction helper.

    An unused raw construction is also a host-work ordering risk. Both run_source
    and direct Evaluator.eval_program paths (native runner) require registered E;
    the behavioral host matrix separately observes the execution result.
    """
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    owner = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == function)
    raw = [node for node in ast.walk(owner) if isinstance(node, ast.Call) and (
        isinstance(node.func, ast.Name) and node.func.id == "make_global_env"
        or isinstance(node.func, ast.Attribute) and node.func.attr == "make_global_env"
    )]
    assert len(raw) <= index, f"§16.6.2 {path}:{function} site {index}: raw R constructor before program evaluation"


def test_B8_B_program_evaluator_paths_have_registered_entry_guard():
    """§16.6.2/3: P2-C must protect direct native Evaluator.eval_program too."""
    from genia.native_test_runner import identify_tests

    source = '@test "entry"\nentry_test() = true'
    declarations = Parser(lex(source), source=source).parse_program()
    units = identify_tests(declarations)
    closure = units[0].body.closure
    assert closure is closure.entry_scope() and closure is not closure.runtime_scope()


def test_B8_B_31_site_inventory_classifies_all_raw_program_constructors():
    """A3: P2-C replaces 13 program calls; the other 18 calls remain classified.

    Counts are baseline evidence, not a demand to preserve implementation line
    numbers or allocate entry scopes for frames/tools. New constructor sites
    require an explicit disposition instead of silently joining the inventory.
    """
    program = Counter((path, function) for path, function, _ in PROGRAM_SITES)
    tree_calls = []
    for directory in ("src", "hosts", "tools"):
        for path in sorted((ROOT / directory).rglob("*.py")):
            relative = str(path.relative_to(ROOT))
            tree = ast.parse(path.read_text(encoding="utf-8"))
            parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
                if name not in ("Env", "make_global_env"):
                    continue
                owner = parents.get(node)
                while owner is not None and not isinstance(owner, ast.FunctionDef):
                    owner = parents.get(owner)
                function = owner.name if owner else "<module>"
                tree_calls.append((relative, function, name))
    approved = Counter({
        ("src/genia/builtins.py", "make_global_env", "Env"): 1,
        ("src/genia/builtins.py", "_make_meta_env", "Env"): 1,
        ("src/genia/builtins.py", "meta_match_pattern_env_fn", "Env"): 1,
        ("src/genia/environment.py", "load_module", "Env"): 1,
        ("src/genia/callable.py", "eval_with_tco", "Env"): 1,
        ("src/genia/callable.py", "_first_unit_match", "Env"): 1,
        ("src/genia/callable.py", "_invoke_open_clause", "Env"): 1,
        ("src/genia/evaluator.py", "extend", "Env"): 2,
        ("src/genia/evaluator.py", "eval_list_traversal_loop", "Env"): 2,
        ("src/genia/evaluator.py", "eval_case_expr", "Env"): 1,
        ("src/genia/evaluator.py", "eval_tail", "Env"): 1,
        ("src/genia/evaluator.py", "_eval_impl", "Env"): 1,
        ("src/genia/evaluator.py", "fn", "Env"): 1,
        ("tools/gen_function_docs.py", "collect", "make_global_env"): 1,
        ("tools/lint_doc.py", "_runtime_public_names", "make_global_env"): 1,
        ("tools/lint_doc.py", "_runtime_public_prelude_names", "make_global_env"): 1,
    })
    assert sum(approved.values()) == 18
    actual = Counter(tree_calls)
    unknown = actual - approved
    # One new construction helper may own a raw R factory when its body also
    # calls the approved registration operation. A second helper is a defect.
    helpers = []
    for path, function, name in list(unknown):
        if name != "make_global_env" or (path, function) in program:
            continue
        tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
        owner = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == function)
        if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "create_entry_scope" for n in ast.walk(owner)):
            helpers.append((path, function, name))
            del unknown[(path, function, name)]
    assert len(helpers) <= 1, "§16.6.2 requires one construction helper"
    assert not unknown, "A3 unclassified ownership/construction paths: " + repr(dict(unknown))
    assert not (approved - actual), "A3 non-program disposition changed; review inventory"
    unchanged = Counter((path, function) for path, function, name in tree_calls if name == "make_global_env" and (path, function) in program)
    assert not unchanged, "A3 un-migrated program constructors: " + repr(dict(unchanged))
    # The approved 18 non-program baseline sites are documented in the evidence
    # with their exact owner functions; do not demand all 31 allocate E.
