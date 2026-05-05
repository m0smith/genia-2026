"""Structural tests for #218: interpreter.py final cleanup and facade audit.

Pre-flight reference: issue #218 pre-flight report (2026-05-05).

Section 1: Dead re-export removal — FAIL before implementation.
  interpreter.py must not contain symbols that have canonical source modules
  and are not consumed from interpreter.py by any external caller.

Section 2: debug_controller.py import isolation — FAIL before implementation.
  debug_controller.py must import from canonical source modules, not from
  interpreter.py, which it used as a re-export hub.

Section 3: Module docstring accuracy — FAIL before implementation.
  The module docstring must describe the current facade role, not the
  pre-split monolithic behavior.

Section 4: Backward-compat regression guards — PASS before and after.
  Symbols that external callers (tests, __init__.py) currently import from
  genia.interpreter must remain accessible after the cleanup.
"""

import inspect


# ---------------------------------------------------------------------------
# 1. Dead re-export removal — FAIL before implementation
# ---------------------------------------------------------------------------


def _interp_source() -> str:
    import genia.interpreter
    return inspect.getsource(genia.interpreter)


def test_interpreter_does_not_contain_lower_node():
    """lower_node has no external callers via interpreter; must be removed."""
    assert "lower_node" not in _interp_source(), (
        "lower_node is a dead re-export in interpreter.py; remove it"
    )


def test_interpreter_does_not_contain_lower_pattern():
    """lower_pattern has no external callers via interpreter; must be removed."""
    assert "lower_pattern" not in _interp_source(), (
        "lower_pattern is a dead re-export in interpreter.py; remove it"
    )


def test_interpreter_does_not_contain_host_local_ir_constants():
    """IR type-set constants have no external callers via interpreter; must be removed."""
    source = _interp_source()
    dead = [
        "HOST_LOCAL_POST_LOWERING_IR_NODE_TYPES",
        "PORTABLE_CORE_IR_NODE_TYPES",
        "iter_ir_nodes",
    ]
    for name in dead:
        assert name not in source, (
            f"{name} is a dead re-export in interpreter.py; remove it"
        )


def test_interpreter_does_not_contain_irpat_symbols():
    """IrPat* pattern IR nodes have no external callers via interpreter; must be removed."""
    source = _interp_source()
    dead = [
        "IrPatBind",
        "IrPatGlob",
        "IrPatList",
        "IrPatLiteral",
        "IrPatMap",
        "IrPatNone",
        "IrPatRest",
        "IrPatSome",
        "IrPatTuple",
        "IrPatWildcard",
        "IrPattern",
    ]
    for name in dead:
        assert name not in source, (
            f"{name} is a dead re-export in interpreter.py; remove it"
        )


def test_interpreter_does_not_contain_dead_values_exports():
    """GeniaBytes, GeniaRef, GeniaZipEntry have no external callers via interpreter."""
    source = _interp_source()
    dead = ["GeniaBytes", "GeniaRef", "GeniaZipEntry"]
    for name in dead:
        assert name not in source, (
            f"{name} is a dead re-export in interpreter.py; remove it"
        )


def test_interpreter_does_not_contain_dead_host_bridge_exports():
    """host_bridge symbols with no external callers via interpreter must be removed."""
    source = _interp_source()
    dead = [
        "BASE_DIR",
        "_resolve_packaged_module",
        "_build_python_host_module",
        "_genia_to_python_host",
        "_python_host_to_genia",
    ]
    for name in dead:
        assert name not in source, (
            f"{name} is a dead re-export in interpreter.py; remove it"
        )


# ---------------------------------------------------------------------------
# 2. debug_controller.py import isolation — FAIL before implementation
# ---------------------------------------------------------------------------


def test_debug_controller_does_not_import_from_interpreter():
    """debug_controller.py must import from canonical source modules, not interpreter."""
    import genia.debug_controller
    source = inspect.getsource(genia.debug_controller)
    assert "interpreter" not in source, (
        "debug_controller.py must not import from interpreter.py; "
        "import DebugHooks from callable, Env from environment, "
        "GeniaRef from values, SourceSpan from lexer directly"
    )


# ---------------------------------------------------------------------------
# 3. Module docstring accuracy — FAIL before implementation
# ---------------------------------------------------------------------------


def test_interpreter_docstring_describes_facade_not_monolith():
    """The module docstring must not describe pre-split monolithic behavior."""
    import genia.interpreter
    doc = genia.interpreter.__doc__ or ""
    stale_markers = [
        "Implemented subset:",
        "builtins: log",
        "arithmetic: +",
        "function definitions: name",
    ]
    for marker in stale_markers:
        assert marker not in doc, (
            f"interpreter.py docstring still contains stale pre-split text: {marker!r}; "
            "update it to describe the current facade role"
        )


# ---------------------------------------------------------------------------
# 4. Backward-compat regression guards — PASS before and after
# ---------------------------------------------------------------------------

# Public entry points defined in interpreter.py itself


def test_run_source_accessible_from_interpreter():
    from genia.interpreter import run_source  # noqa: F401


def test_main_accessible_from_interpreter():
    from genia.interpreter import _main  # noqa: F401


def test_repl_accessible_from_interpreter():
    from genia.interpreter import repl  # noqa: F401


def test_run_debug_stdio_accessible_from_interpreter():
    from genia.interpreter import run_debug_stdio  # noqa: F401


# make_global_env — from genia.builtins


def test_make_global_env_accessible_from_interpreter():
    from genia.interpreter import make_global_env  # noqa: F401


# genia.evaluator compat surface


def test_evaluator_accessible_from_interpreter():
    from genia.interpreter import Evaluator  # noqa: F401


def test_genia_promise_accessible_from_interpreter():
    from genia.interpreter import GeniaPromise  # noqa: F401


def test_genia_meta_env_accessible_from_interpreter():
    from genia.interpreter import GeniaMetaEnv  # noqa: F401


# genia.callable compat surface


def test_genia_function_accessible_from_interpreter():
    from genia.interpreter import GeniaFunction  # noqa: F401


def test_genia_function_group_accessible_from_interpreter():
    from genia.interpreter import GeniaFunctionGroup  # noqa: F401


def test_tail_call_accessible_from_interpreter():
    from genia.interpreter import TailCall  # noqa: F401


def test_eval_with_tco_accessible_from_interpreter():
    from genia.interpreter import eval_with_tco  # noqa: F401


def test_debug_hooks_accessible_from_interpreter():
    from genia.interpreter import DebugHooks  # noqa: F401


# genia.values compat surface


def test_genia_flow_accessible_from_interpreter():
    from genia.interpreter import GeniaFlow  # noqa: F401


def test_genia_option_none_accessible_from_interpreter():
    from genia.interpreter import GeniaOptionNone  # noqa: F401


def test_genia_option_some_accessible_from_interpreter():
    from genia.interpreter import GeniaOptionSome  # noqa: F401


def test_option_none_accessible_from_interpreter():
    from genia.interpreter import OPTION_NONE  # noqa: F401


def test_truthy_accessible_from_interpreter():
    from genia.interpreter import truthy  # noqa: F401


# genia.lexer / genia.parser compat surface


def test_lex_accessible_from_interpreter():
    from genia.interpreter import lex  # noqa: F401


def test_source_span_accessible_from_interpreter():
    from genia.interpreter import SourceSpan  # noqa: F401


def test_parser_accessible_from_interpreter():
    from genia.interpreter import Parser  # noqa: F401


# genia.lowering / genia.optimizer compat surface


def test_lower_program_accessible_from_interpreter():
    from genia.interpreter import lower_program  # noqa: F401


def test_optimize_program_accessible_from_interpreter():
    from genia.interpreter import optimize_program  # noqa: F401


# genia.ast_nodes compat surface


def test_assign_accessible_from_interpreter():
    from genia.interpreter import Assign  # noqa: F401


def test_var_accessible_from_interpreter():
    from genia.interpreter import Var  # noqa: F401


# genia.host_bridge compat surface (live — test_packaging_resources.py uses it)


def test_load_source_from_path_accessible_from_interpreter():
    from genia.interpreter import _load_source_from_path  # noqa: F401
